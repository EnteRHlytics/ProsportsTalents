from flask import jsonify, current_app
from flask_restx import Resource
import json
import os
from sqlalchemy.orm import joinedload

from app.api import api
from app.models import AthleteProfile, AthleteStat


_DEFAULT_RANKINGS = [
    {"name": "LeBron James", "score": 98.5},
    {"name": "Connor McDavid", "score": 97.8},
    {"name": "Mike Trout", "score": 96.2},
    {"name": "Aaron Donald", "score": 95.7},
    {"name": "Stephen Curry", "score": 94.9},
    {"name": "Giannis Antetokounmpo", "score": 94.0},
    {"name": "Patrick Mahomes", "score": 93.5},
    {"name": "Sidney Crosby", "score": 92.8},
    {"name": "Shohei Ohtani", "score": 92.2},
    {"name": "Lionel Messi", "score": 91.7},
]


def _load_rankings():
    """Load rankings from file if configured, otherwise return defaults."""
    path = current_app.config.get("TOP_RANKINGS_FILE")
    if path and os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            current_app.logger.exception("Failed to load rankings file %s", path)
    return _DEFAULT_RANKINGS


_SPORT_STAT = {
    "NBA": "PointsPerGame",
    "NFL": "PassingYards",
    "MLB": "BattingAverage",
    "NHL": "Points",
    "SOC": "Goals",
}

# Rough maximum values used to scale a stat to 0-100. These heuristics are only
# for the placeholder algorithm and will be replaced in Phase 4.
_STAT_MAX = {
    "PointsPerGame": 35,
    "PassingYards": 5000,
    "BattingAverage": 0.35,
    "Points": 120,
    "Goals": 60,
}


def _calculate_simple_score(athlete):
    """Return a naive 0-100 score using one key stat per sport.

    This function is a **temporary stand-in** until the real multi-metric
    ranking algorithm arrives in Phase 4. It looks up a single stat for the
    athlete (e.g. NBA points per game) and scales it using a rough maximum
    value.
    """

    base = float(athlete.overall_rating or 0)
    sport_code = athlete.primary_sport.code if athlete.primary_sport else None
    stat_name = _SPORT_STAT.get(sport_code)
    if not stat_name:
        return base

    stat = (
        AthleteStat.query.filter_by(athlete_id=athlete.athlete_id, name=stat_name)
        .order_by(AthleteStat.season.desc())
        .first()
    )
    if not stat:
        return base
    try:
        value = float(stat.value)
    except (TypeError, ValueError):
        return base

    max_val = _STAT_MAX.get(stat_name) or 1
    score = (value / max_val) * 100
    return round(min(score, 100), 1)


def _dynamic_rankings(limit=5):
    """Compute rankings for athletes using the simple scoring formula."""

    athletes = (
        AthleteProfile.query.options(joinedload(AthleteProfile.user))
        .options(joinedload(AthleteProfile.primary_sport))
        .filter_by(is_deleted=False)
        .all()
    )
    if not athletes:
        return None

    ranked = []
    for ath in athletes:
        name = ath.user.full_name if ath.user else ath.athlete_id
        ranked.append({
            "id": ath.athlete_id,
            "name": name,
            "score": _calculate_simple_score(ath),
        })

    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked[:limit]


@api.route('/rankings/top')
class TopRankings(Resource):
    """Return the top 5 athlete rankings using a temporary formula."""

    def get(self):
        rankings = _dynamic_rankings()
        if rankings is None:
            rankings = _load_rankings()
        return jsonify(rankings)
