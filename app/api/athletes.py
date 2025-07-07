from flask import request, jsonify, current_app
from app.utils.validators import validate_params
from datetime import date
from functools import lru_cache
from sqlalchemy import or_

from flask_restx import Resource
from app.api import api
from app import db
from app.models import AthleteProfile, User, Sport, Position, AthleteStat

# Simple in-memory cache for search results
_SEARCH_CACHE_SIZE = 128


def _cache_key(args):
    key_parts = [f"{k}={v}" for k, v in sorted(args.items())]
    return '&'.join(key_parts)


@lru_cache(maxsize=_SEARCH_CACHE_SIZE)
def _cached_search(key):
    """Perform the actual database search using a cache key."""
    params = dict(item.split('=', 1) for item in key.split('&') if '=' in item)
    q = params.get('q', '')
    sport = params.get('sport')
    position = params.get('position')
    team = params.get('team')
    min_age = int(params['min_age']) if 'min_age' in params else None
    max_age = int(params['max_age']) if 'max_age' in params else None
    min_height = int(params['min_height']) if 'min_height' in params else None
    max_height = int(params['max_height']) if 'max_height' in params else None
    min_weight = float(params['min_weight']) if 'min_weight' in params else None
    max_weight = float(params['max_weight']) if 'max_weight' in params else None
    filter_tab = params.get('filter')
    limit = 50

    query = (
        AthleteProfile.query.filter_by(is_deleted=False)
        .join(User)
        .outerjoin(Sport)
        .outerjoin(Position)
    )

    if filter_tab:
        tab = filter_tab.lower()
        if tab in {'nba', 'nfl', 'mlb', 'nhl'}:
            query = query.filter(Sport.code == tab.upper())
        elif tab == 'available':
            if hasattr(AthleteProfile, 'contract_active'):
                query = query.filter(AthleteProfile.contract_active.is_(False))
        elif tab == 'top':
            limit = 10

    if sport:
        if sport.isdigit():
            query = query.filter(AthleteProfile.primary_sport_id == int(sport))
        else:
            query = query.filter(Sport.code.ilike(sport))

    if position:
        if position.isdigit():
            query = query.filter(
                AthleteProfile.primary_position_id == int(position)
            )
        else:
            pattern = f"%{position}%"
            query = query.filter(
                or_(Position.code.ilike(position), Position.name.ilike(pattern))
            )

    if team:
        query = query.filter(AthleteProfile.current_team.ilike(f"%{team}%"))

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                Position.name.ilike(pattern),
                AthleteProfile.current_team.ilike(pattern),
            )
        )

    today = date.today()
    if min_age is not None:
        cutoff = today.replace(year=today.year - min_age)
        query = query.filter(AthleteProfile.date_of_birth <= cutoff)
    if max_age is not None:
        cutoff = today.replace(year=today.year - max_age)
        query = query.filter(AthleteProfile.date_of_birth >= cutoff)

    if min_height is not None:
        query = query.filter(AthleteProfile.height_cm >= min_height)
    if max_height is not None:
        query = query.filter(AthleteProfile.height_cm <= max_height)

    if min_weight is not None:
        query = query.filter(AthleteProfile.weight_kg >= min_weight)
    if max_weight is not None:
        query = query.filter(AthleteProfile.weight_kg <= max_weight)

    results = (
        query.order_by(AthleteProfile.overall_rating.desc())
        .limit(limit)
        .all()
    )

    return [ath.to_dict() for ath in results]


@api.route('/athletes/search')
class AthleteSearch(Resource):
    """Search athletes with optional filters."""

    @api.doc(params={
        'q': 'Free text search',
        'sport': 'Sport code or id',
        'position': 'Position code or id',
        'team': 'Current team name',
        'min_age': 'Minimum age',
        'max_age': 'Maximum age',
        'min_height': 'Minimum height (cm)',
        'max_height': 'Maximum height (cm)',
        'min_weight': 'Minimum weight (kg)',
        'max_weight': 'Maximum weight (kg)',
        'filter': 'Filter tab selection (nba, nfl, mlb, nhl, available, top)',
    }, description="Search athletes with optional filters")
    @validate_params([])
    def get(self):
        args = request.args.to_dict(flat=True)
        key = _cache_key(args)
        results = _cached_search(key)

        if current_app:
            current_app.logger.info('search query: %s', key)

        return jsonify({'results': results, 'count': len(results)})


def _format_stat_value(value):
    """Return a formatted string for numeric stats."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    if 0 < num < 1:
        return f"{num:.3f}".lstrip("0")
    return f"{num:.1f}" if num % 1 else str(int(num))


def _collect_featured_stats(athlete, year):
    """Gather three key stats for display based on the athlete's sport."""
    sport = athlete.primary_sport.code if athlete.primary_sport else None
    mapping = {}
    if sport == "NBA":
        mapping = {
            "PPG": "PointsPerGame",
            "RPG": "ReboundsPerGame",
            "APG": "AssistsPerGame",
        }
    elif sport == "NFL":
        mapping = {
            "PassingYards": "PassingYards",
            "Touchdowns": "Touchdowns",
            "QBRating": "QBRating",
        }
    elif sport == "MLB":
        mapping = {
            "AVG": "BattingAverage",
            "HR": "HomeRuns",
            "RBI": "RunsBattedIn",
        }
    elif sport == "NHL":
        mapping = {"Goals": "Goals", "Assists": "Assists", "Points": "Points"}

    stats = []
    for label, name in mapping.items():
        stat = AthleteStat.query.filter_by(
            athlete_id=athlete.athlete_id, name=name, season=str(year)
        ).first()
        value = stat.value if stat else "N/A"
        stats.append({"label": label, "value": _format_stat_value(value)})
    return stats


@api.route('/athletes/featured')
class FeaturedAthletes(Resource):
    """Return manually curated featured athletes."""

    @validate_params([])
    def get(self):
        limit = request.args.get('limit', 6, type=int)
        athletes = (
            AthleteProfile.query.filter_by(is_deleted=False, is_featured=True)
            .join(User)
            .outerjoin(Sport)
            .outerjoin(Position)
            .order_by(AthleteProfile.overall_rating.desc())
            .limit(limit)
            .all()
        )
        year = date.today().year
        featured = []
        for ath in athletes:
            name = ath.user.full_name if ath.user else ath.athlete_id
            initials = "".join([n[0] for n in name.split()][:2]).upper()
            featured.append(
                {
                    "name": name,
                    "position": ath.primary_position.code if ath.primary_position else None,
                    "team": ath.current_team or "N/A",
                    "sport": ath.primary_sport.code if ath.primary_sport else None,
                    "profile_image_url": ath.profile_image_url,
                    "initials": initials,
                    "stats": _collect_featured_stats(ath, year),
                }
            )
        return jsonify(featured)
