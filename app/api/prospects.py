"""REST endpoints for the prospect scouting domain.

A ``Prospect`` is a pre-pro athlete the agency is scouting (HS, college,
G-League, MiLB, etc.). These endpoints replace the Wave-1 stub.

Endpoints (mounted under the ``api`` blueprint):

- ``GET    /api/prospects``                 - search/list (q, sport, league, draft_year, paging)
- ``POST   /api/prospects``                 - create (auth required)
- ``GET    /api/prospects/<id>``            - detail
- ``PUT    /api/prospects/<id>``            - update (auth required)
- ``DELETE /api/prospects/<id>``            - soft-delete (auth required)
- ``GET    /api/prospects/<id>/stats``      - list stats
- ``POST   /api/prospects/<id>/stats``      - upsert stat (auth required)
"""

from datetime import date, datetime
import logging

from flask import abort, current_app, jsonify, request
from flask_restx import Resource
from sqlalchemy import or_

from app import db
from app.api import api
from app.models import (
    MinorLeagueTeam,
    Position,
    Prospect,
    ProspectLeague,
    ProspectStat,
    Sport,
)
from app.utils.auth import login_or_token_required


logger = logging.getLogger(__name__)


# ----- helpers ------------------------------------------------------------

def _parse_date(value):
    """Accept ISO date strings (yyyy-mm-dd) or already-parsed dates."""
    if value is None or value == '':
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        abort(400, 'Invalid date_of_birth; expected YYYY-MM-DD')


def _coerce_int(value, field_name, *, low=None, high=None):
    if value is None or value == '':
        return None
    try:
        ivalue = int(value)
    except (ValueError, TypeError):
        abort(400, f'Invalid {field_name}; expected integer')
    if low is not None and ivalue < low:
        abort(400, f'{field_name} must be >= {low}')
    if high is not None and ivalue > high:
        abort(400, f'{field_name} must be <= {high}')
    return ivalue


def _coerce_float(value, field_name):
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        abort(400, f'Invalid {field_name}; expected number')


def _resolve_sport_filter(query, sport):
    """Apply a sport filter that accepts numeric id or sport code."""
    sport = str(sport).strip()
    if not sport:
        return query
    if sport.isdigit():
        return query.filter(Prospect.primary_sport_id == int(sport))
    sport_row = Sport.query.filter(Sport.code.ilike(sport)).first()
    if sport_row is None:
        return query.filter(False)
    return query.filter(Prospect.primary_sport_id == sport_row.sport_id)


def _resolve_league_filter(query, league):
    """Apply a league filter that accepts uuid or league code."""
    league = str(league).strip()
    if not league:
        return query
    league_row = ProspectLeague.query.filter(
        or_(
            ProspectLeague.code.ilike(league),
            ProspectLeague.prospect_league_id == league,
        )
    ).first()
    if league_row is None:
        return query.filter(False)
    return query.filter(Prospect.prospect_league_id == league_row.prospect_league_id)


def _serialise_prospect(prospect: Prospect) -> dict:
    return prospect.to_dict()


# ----- /api/prospects -----------------------------------------------------

@api.route('/prospects')
class ProspectList(Resource):
    """List or create prospects."""

    @api.doc(
        description='List/search prospects',
        params={
            'q': 'Free text search (name, school)',
            'sport': 'Sport code (NBA) or numeric id',
            'league': 'Prospect league code (NCAA_BB_D1) or uuid',
            'draft_year': 'Draft eligible year (e.g. 2026)',
            'page': 'Page number (default 1)',
            'per_page': 'Items per page (default 25, max 100)',
        },
    )
    def get(self):
        params = request.args
        page = max(1, params.get('page', 1, type=int) or 1)
        per_page = min(max(1, params.get('per_page', 25, type=int) or 25), 100)

        query = Prospect.query.filter(Prospect.is_deleted.is_(False))

        q = (params.get('q') or '').strip()
        if q:
            pattern = f'%{q}%'
            query = query.filter(
                or_(
                    Prospect.first_name.ilike(pattern),
                    Prospect.last_name.ilike(pattern),
                    Prospect.school.ilike(pattern),
                )
            )

        sport = params.get('sport')
        if sport:
            query = _resolve_sport_filter(query, sport)

        league = params.get('league')
        if league:
            query = _resolve_league_filter(query, league)

        draft_year = params.get('draft_year')
        if draft_year:
            try:
                query = query.filter(
                    Prospect.draft_eligible_year == int(draft_year)
                )
            except (ValueError, TypeError):
                abort(400, 'Invalid draft_year; expected integer')

        query = query.order_by(
            Prospect.scout_grade.desc().nullslast(),
            Prospect.last_name.asc(),
            Prospect.first_name.asc(),
        )

        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            'items': [_serialise_prospect(p) for p in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
        }, 200

    @api.doc(description='Create a prospect')
    @login_or_token_required
    def post(self):
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            abort(400, 'Request body must be a JSON object')

        first_name = (data.get('first_name') or '').strip()
        last_name = (data.get('last_name') or '').strip()
        if not first_name or not last_name:
            abort(400, 'first_name and last_name are required')

        prospect = Prospect(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=_parse_date(data.get('date_of_birth')),
            height_cm=_coerce_int(
                data.get('height_cm'), 'height_cm', low=100, high=250
            ),
            weight_kg=_coerce_float(data.get('weight_kg'), 'weight_kg'),
            primary_sport_id=_coerce_int(
                data.get('primary_sport_id'), 'primary_sport_id'
            ),
            primary_position_id=_coerce_int(
                data.get('primary_position_id'), 'primary_position_id'
            ),
            current_team_id=data.get('current_team_id') or None,
            prospect_league_id=data.get('prospect_league_id') or None,
            school=data.get('school'),
            draft_eligible_year=_coerce_int(
                data.get('draft_eligible_year'), 'draft_eligible_year'
            ),
            scout_grade=_coerce_int(
                data.get('scout_grade'), 'scout_grade', low=0, high=100
            ),
            scout_notes=data.get('scout_notes'),
            bio=data.get('bio'),
            external_id=data.get('external_id'),
        )

        db.session.add(prospect)
        db.session.commit()
        logger.info('Created prospect %s', prospect.prospect_id)
        return _serialise_prospect(prospect), 201


@api.route('/prospects/<string:prospect_id>')
@api.param('prospect_id', 'Prospect identifier')
class ProspectResource(Resource):
    """Retrieve, update or soft-delete a prospect."""

    @api.doc(description='Get a prospect by id')
    def get(self, prospect_id):
        prospect = Prospect.query.filter_by(
            prospect_id=prospect_id, is_deleted=False
        ).first_or_404()
        return _serialise_prospect(prospect), 200

    @api.doc(description='Update a prospect')
    @login_or_token_required
    def put(self, prospect_id):
        prospect = Prospect.query.filter_by(
            prospect_id=prospect_id, is_deleted=False
        ).first_or_404()
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            abort(400, 'Request body must be a JSON object')

        simple_fields = (
            'first_name', 'last_name', 'school', 'scout_notes',
            'bio', 'external_id',
        )
        for field in simple_fields:
            if field in data:
                value = data[field]
                if field in ('first_name', 'last_name'):
                    if not value or not str(value).strip():
                        abort(400, f'{field} cannot be empty')
                    value = str(value).strip()
                setattr(prospect, field, value)

        if 'date_of_birth' in data:
            prospect.date_of_birth = _parse_date(data['date_of_birth'])

        if 'height_cm' in data:
            prospect.height_cm = _coerce_int(
                data['height_cm'], 'height_cm', low=100, high=250
            )

        if 'weight_kg' in data:
            prospect.weight_kg = _coerce_float(data['weight_kg'], 'weight_kg')

        if 'primary_sport_id' in data:
            prospect.primary_sport_id = _coerce_int(
                data['primary_sport_id'], 'primary_sport_id'
            )

        if 'primary_position_id' in data:
            prospect.primary_position_id = _coerce_int(
                data['primary_position_id'], 'primary_position_id'
            )

        if 'current_team_id' in data:
            prospect.current_team_id = data['current_team_id'] or None

        if 'prospect_league_id' in data:
            prospect.prospect_league_id = data['prospect_league_id'] or None

        if 'draft_eligible_year' in data:
            prospect.draft_eligible_year = _coerce_int(
                data['draft_eligible_year'], 'draft_eligible_year'
            )

        if 'scout_grade' in data:
            prospect.scout_grade = _coerce_int(
                data['scout_grade'], 'scout_grade', low=0, high=100
            )

        db.session.commit()
        logger.info('Updated prospect %s', prospect.prospect_id)
        return _serialise_prospect(prospect), 200

    @api.doc(description='Soft-delete a prospect')
    @login_or_token_required
    def delete(self, prospect_id):
        prospect = Prospect.query.filter_by(
            prospect_id=prospect_id, is_deleted=False
        ).first_or_404()
        prospect.is_deleted = True
        db.session.commit()
        logger.info('Soft-deleted prospect %s', prospect.prospect_id)
        return '', 204


@api.route('/prospects/<string:prospect_id>/stats')
@api.param('prospect_id', 'Prospect identifier')
class ProspectStats(Resource):
    """List or upsert stats for a prospect."""

    @api.doc(
        description='List stats for a prospect',
        params={
            'season': 'Filter to a specific season',
        },
    )
    def get(self, prospect_id):
        Prospect.query.filter_by(
            prospect_id=prospect_id, is_deleted=False
        ).first_or_404()
        query = ProspectStat.query.filter_by(prospect_id=prospect_id)
        season = request.args.get('season')
        if season:
            query = query.filter_by(season=season)
        stats = query.order_by(
            ProspectStat.season.desc(), ProspectStat.name.asc()
        ).all()
        return [s.to_dict() for s in stats], 200

    @api.doc(description='Upsert a stat for a prospect (unique on season+name)')
    @login_or_token_required
    def post(self, prospect_id):
        Prospect.query.filter_by(
            prospect_id=prospect_id, is_deleted=False
        ).first_or_404()
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            abort(400, 'Request body must be a JSON object')

        season = (data.get('season') or '').strip()
        name = (data.get('name') or '').strip()
        if not season or not name:
            abort(400, 'season and name are required')

        stat = ProspectStat.query.filter_by(
            prospect_id=prospect_id, season=season, name=name
        ).first()
        if stat is None:
            stat = ProspectStat(
                prospect_id=prospect_id,
                season=season,
                name=name,
                value=data.get('value'),
                stat_type=data.get('stat_type'),
                source=data.get('source'),
            )
            db.session.add(stat)
            status = 201
        else:
            stat.value = data.get('value', stat.value)
            if 'stat_type' in data:
                stat.stat_type = data.get('stat_type')
            if 'source' in data:
                stat.source = data.get('source')
            status = 200

        db.session.commit()
        logger.info(
            'Upserted prospect stat %s/%s/%s', prospect_id, season, name
        )
        return stat.to_dict(), status
