"""Multi-factor athlete ranking API.

Endpoints
---------

* ``GET    /api/rankings/top``         - Ranked leaderboard using either a
                                        user preset (if logged in and a
                                        default exists) or the global default
                                        weights.
* ``GET    /api/rankings/calculate``   - Ad-hoc ranking with custom weights
                                        passed via query string.
* ``POST   /api/rankings/calculate``   - Same, but with weights in the JSON
                                        body (preferred for richer payloads).
* ``GET    /api/rankings/presets``     - List the current user's saved
                                        weight presets.
* ``POST   /api/rankings/presets``     - Create a preset.
* ``DELETE /api/rankings/presets/<id>``- Delete a preset.

The actual scoring logic lives in :mod:`app.services.ranking_service` and is
documented there.
"""

from __future__ import annotations

import json
import logging
import os

from flask import current_app, jsonify, request
from flask_login import current_user
from flask_restx import Resource
from sqlalchemy.orm import joinedload

from app import db
from app.api import api
from app.models import AthleteProfile, Sport
from app.services.ranking_service import (
    COMPONENT_KEYS,
    DEFAULT_WEIGHTS,
    build_athlete_record,
    compute_rankings,
    normalise_weights,
)

logger = logging.getLogger(__name__)

_DEFAULT_LIMIT = 10
_MAX_LIMIT = 100


# ---------------------------------------------------------------------------
# Backwards-compat helpers used by templates / older callers.
#
# The pre-merge rankings module exposed `_dynamic_rankings` and
# `_load_rankings`; `app/main/routes.py` and the dashboard template still
# import them. We re-implement them on top of the new multi-factor algorithm
# so the imports don't break.
# ---------------------------------------------------------------------------


_DEFAULT_RANKINGS_FALLBACK = [
    {"id": None, "name": "LeBron James", "score": 98.5},
    {"id": None, "name": "Connor McDavid", "score": 97.8},
    {"id": None, "name": "Mike Trout", "score": 96.2},
    {"id": None, "name": "Aaron Donald", "score": 95.7},
    {"id": None, "name": "Stephen Curry", "score": 94.9},
    {"id": None, "name": "Giannis Antetokounmpo", "score": 94.0},
    {"id": None, "name": "Patrick Mahomes", "score": 93.5},
    {"id": None, "name": "Sidney Crosby", "score": 92.8},
    {"id": None, "name": "Shohei Ohtani", "score": 92.2},
    {"id": None, "name": "Lionel Messi", "score": 91.7},
]


def _load_rankings():
    """Load static rankings from a configured JSON file or return defaults.

    Kept for backwards compatibility with templates / pages that fall back to
    a static list when no athletes exist yet.
    """
    try:
        path = current_app.config.get("TOP_RANKINGS_FILE")
    except Exception:
        path = None
    if path and os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
                # Normalise: ensure each entry has at least name / score / id keys.
                for entry in data:
                    entry.setdefault("id", None)
                    entry.setdefault("score", 0)
                return data
        except Exception:
            try:
                current_app.logger.exception(
                    "Failed to load rankings file %s", path
                )
            except Exception:
                pass
    return list(_DEFAULT_RANKINGS_FALLBACK)


def _dynamic_rankings(limit=5, sport_code=None):
    """Compute rankings for athletes using the multi-factor algorithm.

    Returns a list of dicts shaped like::

        {"id": <athlete_id>, "name": <full name>, "score": <0-100 float>}

    or ``None`` when there are no athletes in the database (so callers can
    fall back to :func:`_load_rankings`).
    """
    try:
        records = _records_for(sport_code=sport_code)
    except Exception:
        # If the DB / models are unavailable fall back to None so callers
        # use the static defaults.
        return None
    if not records:
        return None

    ranked = compute_rankings(
        records, weights=DEFAULT_WEIGHTS, sport=sport_code, limit=limit
    )
    out = []
    for row in ranked:
        out.append({
            "id": row.get("athlete_id"),
            "name": row.get("name"),
            "score": row.get("score"),
        })
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_limit(raw, default=_DEFAULT_LIMIT):
    try:
        value = int(raw) if raw is not None else default
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return min(value, _MAX_LIMIT)


def _parse_weights_qs(raw):
    """Parse a weights querystring like ``performance=0.5,efficiency=0.2``.

    Also accepts a JSON blob.  Returns ``None`` when nothing parseable is
    supplied.
    """
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
        except ValueError:
            return None
        return data if isinstance(data, dict) else None
    parsed = {}
    for chunk in raw.split(","):
        if "=" not in chunk:
            continue
        key, _, value = chunk.partition("=")
        key = key.strip()
        try:
            parsed[key] = float(value.strip())
        except (TypeError, ValueError):
            continue
    return parsed or None


def _resolve_sport_id(sport_code):
    if not sport_code:
        return None
    sport = Sport.query.filter_by(code=sport_code).first()
    return sport.sport_id if sport else None


def _load_athletes(sport_code=None):
    query = (
        AthleteProfile.query.options(joinedload(AthleteProfile.user))
        .options(joinedload(AthleteProfile.primary_sport))
        .options(joinedload(AthleteProfile.stats))
        .filter_by(is_deleted=False)
    )
    if sport_code:
        sport = Sport.query.filter_by(code=sport_code).first()
        if not sport:
            return []
        query = query.filter(AthleteProfile.primary_sport_id == sport.sport_id)
    return query.all()


def _records_for(sport_code=None):
    return [build_athlete_record(a) for a in _load_athletes(sport_code)]


def _user_default_preset(sport_code=None):
    """Return the active user's default preset for the sport (if any)."""
    if not getattr(current_user, "is_authenticated", False):
        return None
    try:
        from app.models.ranking_preset import RankingPreset
    except ImportError:
        return None
    query = RankingPreset.query.filter_by(
        user_id=current_user.user_id, is_default=True
    )
    if sport_code:
        sport_id = _resolve_sport_id(sport_code)
        if sport_id is not None:
            preset = query.filter_by(sport_id=sport_id).first()
            if preset:
                return preset
        # Fall back to a sport-agnostic default.
        return query.filter_by(sport_id=None).first()
    return query.first()


# ---------------------------------------------------------------------------
# /api/rankings/top
# ---------------------------------------------------------------------------


@api.route("/rankings/top")
class TopRankings(Resource):
    """Leaderboard using default or user-preferred weights."""

    @api.doc(
        description=(
            "Return the top ranked athletes using the multi-factor algorithm."
        ),
        params={
            "sport": "Sport code (e.g. NBA, NFL).  Optional.",
            "limit": (
                "Maximum number of results to return (default 10, max 100)."
            ),
        },
    )
    def get(self):
        sport = request.args.get("sport")
        limit = _parse_limit(request.args.get("limit"))
        records = _records_for(sport_code=sport)

        preset = _user_default_preset(sport)
        weights = preset.weights if preset is not None else DEFAULT_WEIGHTS

        ranked = compute_rankings(
            records, weights=weights, sport=sport, limit=limit
        )
        # Backwards-compatible shape: existing clients expect ``id``/``name``/
        # ``score``.  We keep those keys and add the richer fields.
        for row in ranked:
            row["id"] = row["athlete_id"]
        return jsonify(ranked)


# ---------------------------------------------------------------------------
# /api/rankings/calculate
# ---------------------------------------------------------------------------


@api.route("/rankings/calculate")
class CalculateRankings(Resource):
    """Ad-hoc rankings with custom weights."""

    @api.doc(
        description=(
            "Compute rankings with arbitrary weights without saving anything."
        ),
        params={
            "sport": "Sport code.",
            "limit": "Maximum number of results to return.",
            "weights": (
                "Either a comma-separated key=value list or a JSON object."
            ),
        },
    )
    def get(self):
        sport = request.args.get("sport")
        limit = _parse_limit(request.args.get("limit"))
        weights = _parse_weights_qs(request.args.get("weights"))
        return self._respond(sport=sport, limit=limit, weights=weights)

    def post(self):
        payload = request.get_json(silent=True) or {}
        sport = payload.get("sport") or request.args.get("sport")
        limit = _parse_limit(payload.get("limit") or request.args.get("limit"))
        weights = payload.get("weights")
        if isinstance(weights, str):
            weights = _parse_weights_qs(weights)
        return self._respond(sport=sport, limit=limit, weights=weights)

    @staticmethod
    def _respond(sport=None, limit=_DEFAULT_LIMIT, weights=None):
        normalised = normalise_weights(weights)
        records = _records_for(sport_code=sport)
        ranked = compute_rankings(
            records, weights=normalised, sport=sport, limit=limit
        )
        for row in ranked:
            row["id"] = row["athlete_id"]
        return jsonify({
            "weights": normalised,
            "components": list(COMPONENT_KEYS),
            "results": ranked,
        })


# ---------------------------------------------------------------------------
# /api/rankings/presets
# ---------------------------------------------------------------------------


def _require_login():
    if not getattr(current_user, "is_authenticated", False):
        return jsonify({"error": "Authentication required"}), 401
    return None


def _get_preset_model():
    """Lazily import the model so the API still works when the migration
    hasn't been applied yet (degrades to 503 instead of crashing)."""
    try:
        from app.models.ranking_preset import RankingPreset
        return RankingPreset
    except ImportError:  # pragma: no cover - defensive
        return None


@api.route("/rankings/presets")
class RankingPresetList(Resource):
    """List or create the current user's ranking presets."""

    @api.doc(description="List the current user's saved ranking presets.")
    def get(self):
        gate = _require_login()
        if gate is not None:
            return gate
        RankingPreset = _get_preset_model()
        if RankingPreset is None:
            return jsonify({"error": "Ranking presets not available"}), 503

        presets = (
            RankingPreset.query.filter_by(user_id=current_user.user_id)
            .order_by(RankingPreset.created_at.desc())
            .all()
        )
        return jsonify([p.to_dict() for p in presets])

    @api.doc(
        description="Create a ranking preset.",
        params={
            "name": "Preset name (required).",
            "sport": "Sport code (optional).",
            "weights": "Weights object (required).",
            "is_default": "Mark this preset as the default for the sport.",
        },
    )
    def post(self):
        gate = _require_login()
        if gate is not None:
            return gate
        RankingPreset = _get_preset_model()
        if RankingPreset is None:
            return jsonify({"error": "Ranking presets not available"}), 503

        payload = request.get_json(silent=True) or {}
        name = (payload.get("name") or "").strip()
        if not name:
            return jsonify({"error": "name is required"}), 400
        weights = payload.get("weights")
        if not isinstance(weights, dict) or not weights:
            return jsonify({"error": "weights object is required"}), 400

        # Reject completely invalid weight payloads up front.
        if all(k not in weights for k in COMPONENT_KEYS):
            return jsonify({"error": "weights must contain at least one known component"}), 400

        sport_id = _resolve_sport_id(payload.get("sport"))
        is_default = bool(payload.get("is_default"))

        preset = RankingPreset(
            user_id=current_user.user_id,
            sport_id=sport_id,
            name=name,
            is_default=is_default,
        )
        preset.weights = normalise_weights(weights)

        if is_default:
            # Only one default per (user, sport).
            RankingPreset.query.filter_by(
                user_id=current_user.user_id, sport_id=sport_id, is_default=True
            ).update({"is_default": False})

        try:
            db.session.add(preset)
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception("Failed to save ranking preset")
            return jsonify({"error": "Could not save preset"}), 400
        return jsonify(preset.to_dict()), 201


@api.route("/rankings/presets/<string:preset_id>")
@api.param("preset_id", "Ranking preset identifier")
class RankingPresetResource(Resource):
    """Fetch / update / delete a single preset."""

    @api.doc(description="Fetch a single preset.")
    def get(self, preset_id):
        gate = _require_login()
        if gate is not None:
            return gate
        RankingPreset = _get_preset_model()
        if RankingPreset is None:
            return jsonify({"error": "Ranking presets not available"}), 503
        preset = RankingPreset.query.filter_by(
            id=preset_id, user_id=current_user.user_id
        ).first()
        if not preset:
            return jsonify({"error": "Preset not found"}), 404
        return jsonify(preset.to_dict())

    @api.doc(description="Delete a preset.")
    def delete(self, preset_id):
        gate = _require_login()
        if gate is not None:
            return gate
        RankingPreset = _get_preset_model()
        if RankingPreset is None:
            return jsonify({"error": "Ranking presets not available"}), 503
        preset = RankingPreset.query.filter_by(
            id=preset_id, user_id=current_user.user_id
        ).first()
        if not preset:
            return jsonify({"error": "Preset not found"}), 404
        try:
            db.session.delete(preset)
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception("Failed to delete ranking preset %s", preset_id)
            return jsonify({"error": "Could not delete preset"}), 400
        return ("", 204)
