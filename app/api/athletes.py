from flask import request, jsonify, current_app
from app.utils.validators import validate_params
from datetime import date
from functools import lru_cache
from sqlalchemy import or_

from flask_restx import Resource
from app.api import api
from app import db
from app.models import AthleteProfile, User, Sport, Position

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

    query = (
        AthleteProfile.query.filter_by(is_deleted=False)
        .join(User)
        .outerjoin(Sport)
        .outerjoin(Position)
    )

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
        .limit(50)
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
    }, description="Search athletes with optional filters")
    @validate_params([])
    def get(self):
        args = request.args.to_dict(flat=True)
        key = _cache_key(args)
        results = _cached_search(key)

        if current_app:
            current_app.logger.info('search query: %s', key)

        return jsonify({'results': results, 'count': len(results)})
