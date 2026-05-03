"""Export endpoints — PDF and Excel exports for athletes, search, rankings.

Lives in its own Flask-RESTX namespace (``exports``) so it can be
registered alongside the other namespaces without colliding with route
declarations elsewhere. See ``MERGE_NOTES_EXPORTS.md`` for the wiring
required in :mod:`app.api.__init__`.
"""

from __future__ import annotations

import json
import os
import traceback
from urllib.parse import quote

from flask import Response, current_app, jsonify, request, send_file
from flask_restx import Namespace, Resource

from app import db
from app.models import AthleteProfile, Position, Sport, User
from app.services.excel_export import (
    athlete_profile_xlsx,
    rankings_xlsx,
    search_results_xlsx,
)
from app.services.pdf_export import (
    athlete_profile_pdf,
    rankings_pdf,
    search_results_pdf,
)
from app.utils.auth import login_or_token_required

# Public namespace — registered with the main Api in app/api/__init__.py.
ns = Namespace("exports", description="PDF and Excel export endpoints")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PDF_MIME = "application/pdf"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _send(buf, *, mimetype: str, filename: str) -> Response:
    """Return a Flask response with attachment headers."""
    buf.seek(0)
    resp = send_file(
        buf,
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename,
    )
    # Mirror the download_name into Content-Disposition explicitly so older
    # clients that ignore Flask's defaults still receive a sane filename.
    quoted = quote(filename)
    resp.headers["Content-Disposition"] = (
        f"attachment; filename=\"{filename}\"; filename*=UTF-8''{quoted}"
    )
    return resp


def _safe_filename(name: str, suffix: str) -> str:
    """Build a filesystem-friendly filename like ``LeBron_James.pdf``."""
    base = "".join(
        c if c.isalnum() or c in ("-", "_") else "_" for c in (name or "athlete")
    ).strip("_") or "athlete"
    return f"{base}.{suffix}"


def _search_athletes_for_export(params: dict, max_results: int = 500):
    """Replicate the filter logic of ``/api/athletes/search`` without paging."""
    from datetime import date

    from sqlalchemy import and_, func, or_

    query = (
        AthleteProfile.query
        .filter_by(is_deleted=False)
        .join(User)
        .outerjoin(Sport)
        .outerjoin(Position)
        .options(
            db.joinedload(AthleteProfile.user),
            db.joinedload(AthleteProfile.primary_sport),
            db.joinedload(AthleteProfile.primary_position),
        )
    )

    filters = []
    q = (params.get("q") or "").strip()
    if q:
        pattern = f"%{q}%"
        filters.append(or_(
            User.first_name.ilike(pattern),
            User.last_name.ilike(pattern),
            func.concat(User.first_name, " ", User.last_name).ilike(pattern),
            Position.name.ilike(pattern),
            AthleteProfile.current_team.ilike(pattern),
        ))

    sport = params.get("sport")
    if sport:
        if str(sport).isdigit():
            filters.append(AthleteProfile.primary_sport_id == int(sport))
        else:
            filters.append(Sport.code.ilike(sport))

    position = params.get("position")
    if position:
        if str(position).isdigit():
            filters.append(AthleteProfile.primary_position_id == int(position))
        else:
            filters.append(or_(
                Position.code.ilike(position),
                Position.name.ilike(f"%{position}%"),
            ))

    team = params.get("team")
    if team:
        filters.append(AthleteProfile.current_team.ilike(f"%{team}%"))

    today = date.today()
    if params.get("min_age"):
        try:
            ma = int(params["min_age"])
            filters.append(AthleteProfile.date_of_birth <= today.replace(year=today.year - ma))
        except ValueError:
            pass
    if params.get("max_age"):
        try:
            xa = int(params["max_age"])
            filters.append(AthleteProfile.date_of_birth >= today.replace(year=today.year - xa))
        except ValueError:
            pass

    if filters:
        query = query.filter(and_(*filters))

    query = query.order_by(
        AthleteProfile.overall_rating.desc().nullslast(),
        User.last_name,
        User.first_name,
    )
    return query.limit(max_results).all()


def _filters_summary(params: dict) -> dict:
    """Extract a presentable subset of the search params for display."""
    keys = ["q", "sport", "position", "team", "min_age", "max_age",
            "min_height", "max_height", "min_weight", "max_weight", "filter"]
    return {k: params.get(k) for k in keys if params.get(k) not in (None, "")}


def _load_rankings_for(sport: str, preset_id: str | None):
    """Build the ranking list + weights for the rankings export.

    Falls back to a configured rankings file or the default static list when
    no athlete data is available, matching the behavior of
    :mod:`app.api.rankings`.
    """
    from sqlalchemy.orm import joinedload

    weights = _resolve_preset_weights(preset_id)

    # Try dynamic rankings first
    athletes = (
        AthleteProfile.query
        .options(joinedload(AthleteProfile.user))
        .options(joinedload(AthleteProfile.primary_sport))
        .filter_by(is_deleted=False)
    )
    if sport:
        athletes = athletes.join(Sport).filter(Sport.code.ilike(sport))
    athletes = athletes.all()

    if athletes:
        rows = []
        for ath in athletes:
            rows.append({
                "id": ath.athlete_id,
                "name": ath.user.full_name if ath.user else ath.athlete_id,
                "team": ath.current_team or "Free Agent",
                "score": float(ath.overall_rating) if ath.overall_rating is not None else 0.0,
            })
        rows.sort(key=lambda r: r["score"], reverse=True)
        for i, r in enumerate(rows, start=1):
            r["rank"] = i
        return rows, weights

    # Fallback: static rankings file or hard-coded default
    path = current_app.config.get("TOP_RANKINGS_FILE")
    if path and os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
                for i, r in enumerate(data, start=1):
                    r.setdefault("rank", i)
                return data, weights
        except Exception:
            current_app.logger.exception("Failed to load rankings file %s", path)

    # Default placeholder list (mirrors app/api/rankings.py)
    default = [
        {"name": "LeBron James", "score": 98.5},
        {"name": "Connor McDavid", "score": 97.8},
        {"name": "Mike Trout", "score": 96.2},
        {"name": "Aaron Donald", "score": 95.7},
        {"name": "Stephen Curry", "score": 94.9},
    ]
    for i, r in enumerate(default, start=1):
        r["rank"] = i
    return default, weights


def _resolve_preset_weights(preset_id: str | None) -> dict:
    """Return weights for the ranking algorithm.

    Until the Phase-4 ranking service ships, we surface a small descriptive
    map so the export shows *something* meaningful in the weights column.
    """
    if not preset_id:
        return {"OverallRating": 1.0}
    presets = {
        "balanced": {"Offense": 0.4, "Defense": 0.3, "Durability": 0.2, "Intangibles": 0.1},
        "offense": {"Offense": 0.7, "Defense": 0.2, "Durability": 0.05, "Intangibles": 0.05},
        "defense": {"Offense": 0.2, "Defense": 0.7, "Durability": 0.05, "Intangibles": 0.05},
    }
    return presets.get(preset_id, {"Preset": preset_id})


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@ns.route("/athletes/<string:athlete_id>.pdf")
@ns.param("athlete_id", "Athlete identifier")
class AthleteProfilePDF(Resource):
    @ns.doc(description="Export an athlete profile as PDF")
    @login_or_token_required
    def get(self, athlete_id: str):
        try:
            buf = athlete_profile_pdf(athlete_id)
        except ValueError:
            return jsonify({"error": "Athlete not found"}), 404
        except Exception as e:
            current_app.logger.error(
                "PDF export failed for %s: %s\n%s",
                athlete_id, e, traceback.format_exc(),
            )
            return jsonify({"error": "Export failed"}), 500
        athlete = AthleteProfile.query.filter_by(athlete_id=athlete_id).first()
        name = athlete.user.full_name if athlete and athlete.user else athlete_id
        return _send(buf, mimetype=PDF_MIME, filename=_safe_filename(name, "pdf"))


@ns.route("/athletes/<string:athlete_id>.xlsx")
@ns.param("athlete_id", "Athlete identifier")
class AthleteProfileXLSX(Resource):
    @ns.doc(description="Export an athlete profile as Excel")
    @login_or_token_required
    def get(self, athlete_id: str):
        try:
            buf = athlete_profile_xlsx(athlete_id)
        except ValueError:
            return jsonify({"error": "Athlete not found"}), 404
        except Exception as e:
            current_app.logger.error(
                "XLSX export failed for %s: %s\n%s",
                athlete_id, e, traceback.format_exc(),
            )
            return jsonify({"error": "Export failed"}), 500
        athlete = AthleteProfile.query.filter_by(athlete_id=athlete_id).first()
        name = athlete.user.full_name if athlete and athlete.user else athlete_id
        return _send(buf, mimetype=XLSX_MIME, filename=_safe_filename(name, "xlsx"))


@ns.route("/search.pdf")
class SearchExportPDF(Resource):
    @ns.doc(description="Export search results as PDF")
    @login_or_token_required
    def get(self):
        params = request.args.to_dict()
        try:
            athletes = _search_athletes_for_export(params)
            buf = search_results_pdf(athletes, _filters_summary(params))
        except Exception as e:
            current_app.logger.error("Search PDF export failed: %s", e)
            return jsonify({"error": "Export failed"}), 500
        return _send(buf, mimetype=PDF_MIME, filename="athlete_search_results.pdf")


@ns.route("/search.xlsx")
class SearchExportXLSX(Resource):
    @ns.doc(description="Export search results as Excel")
    @login_or_token_required
    def get(self):
        params = request.args.to_dict()
        try:
            athletes = _search_athletes_for_export(params)
            buf = search_results_xlsx(athletes, _filters_summary(params))
        except Exception as e:
            current_app.logger.error("Search XLSX export failed: %s", e)
            return jsonify({"error": "Export failed"}), 500
        return _send(buf, mimetype=XLSX_MIME, filename="athlete_search_results.xlsx")


@ns.route("/rankings.pdf")
class RankingsExportPDF(Resource):
    @ns.doc(description="Export rankings as PDF")
    @login_or_token_required
    def get(self):
        sport = request.args.get("sport") or ""
        preset_id = request.args.get("preset_id")
        try:
            rows, weights = _load_rankings_for(sport, preset_id)
            buf = rankings_pdf(rows, sport=sport or None, weights=weights)
        except Exception as e:
            current_app.logger.error("Rankings PDF export failed: %s", e)
            return jsonify({"error": "Export failed"}), 500
        sport_token = (sport or "all").lower()
        return _send(
            buf,
            mimetype=PDF_MIME,
            filename=f"rankings_{sport_token}.pdf",
        )


@ns.route("/rankings.xlsx")
class RankingsExportXLSX(Resource):
    @ns.doc(description="Export rankings as Excel")
    @login_or_token_required
    def get(self):
        sport = request.args.get("sport") or ""
        preset_id = request.args.get("preset_id")
        try:
            rows, weights = _load_rankings_for(sport, preset_id)
            buf = rankings_xlsx(rows, sport=sport or None, weights=weights)
        except Exception as e:
            current_app.logger.error("Rankings XLSX export failed: %s", e)
            return jsonify({"error": "Export failed"}), 500
        sport_token = (sport or "all").lower()
        return _send(
            buf,
            mimetype=XLSX_MIME,
            filename=f"rankings_{sport_token}.xlsx",
        )
