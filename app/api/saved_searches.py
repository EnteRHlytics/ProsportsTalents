"""CRUD endpoints for per-user saved searches.

Each saved search persists the JSON params used by the
``/api/athletes/search`` endpoint, so users can quickly re-run a
common query (e.g. "available NBA point guards under 25").
"""

from functools import wraps

from flask import request, abort, current_app
from flask_login import current_user
from flask_restx import Resource

from app.api import api
from app import db
from app.models.saved_search import SavedSearch
from app.models.oauth import UserOAuthAccount


def _resolve_current_user():
    """Return the active user for the request, or None.

    Looks first at Flask-Login's session-based ``current_user``, then
    falls back to a Bearer access token in the ``Authorization``
    header. Resolved each time it is called so concurrent test
    clients (which can share a single app context) do not see each
    other's identities.
    """
    if current_user and current_user.is_authenticated:
        return current_user._get_current_object()

    auth = request.headers.get('Authorization', '')
    if auth.lower().startswith('bearer '):
        token = auth.split(' ', 1)[1].strip()
        account = UserOAuthAccount.query.filter_by(access_token=token).first()
        if account and account.user and account.user.is_active:
            return account.user

    return None


def _require_user(fn):
    """Decorator: 401 unless a session or token user can be resolved."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if _resolve_current_user() is None:
            abort(401)
        return fn(*args, **kwargs)

    return wrapper


def _get_owned_or_404(search_id):
    """Return a SavedSearch owned by the resolved user or raise 404."""
    user = _resolve_current_user()
    search = SavedSearch.query.filter_by(id=search_id).first()
    if search is None or user is None or search.user_id != user.user_id:
        abort(404, 'Saved search not found')
    return search


def _validate_payload(data, *, require_name=True):
    """Return (name, params) from a request payload, or abort 400."""
    if not isinstance(data, dict):
        abort(400, 'Request body must be a JSON object')

    name = data.get('name')
    params = data.get('params')

    if require_name:
        if not isinstance(name, str) or not name.strip():
            abort(400, 'Field "name" is required')
        name = name.strip()
    elif name is not None:
        if not isinstance(name, str) or not name.strip():
            abort(400, 'Field "name" must be a non-empty string')
        name = name.strip()

    if params is None:
        params = {} if require_name else None
    elif not isinstance(params, dict):
        abort(400, 'Field "params" must be a JSON object')

    return name, params


@api.route('/saved-searches')
class SavedSearchList(Resource):
    """List or create the current user's saved searches."""

    @api.doc(description='List saved searches for the current user')
    @_require_user
    def get(self):
        user = _resolve_current_user()
        searches = (
            SavedSearch.query
            .filter_by(user_id=user.user_id)
            .order_by(SavedSearch.updated_at.desc())
            .all()
        )
        return [s.to_dict() for s in searches], 200

    @api.doc(description='Create a saved search', params={
        'name': 'Display name for the saved search',
        'params': 'JSON object of search parameters',
    })
    @_require_user
    def post(self):
        user = _resolve_current_user()
        data = request.get_json(silent=True) or {}
        name, params = _validate_payload(data, require_name=True)

        existing = SavedSearch.query.filter_by(
            user_id=user.user_id, name=name
        ).first()
        if existing is not None:
            abort(409, 'A saved search with that name already exists')

        search = SavedSearch(
            user_id=user.user_id,
            name=name,
            params_json=params or {},
        )
        db.session.add(search)
        db.session.commit()
        current_app.logger.info(
            'Created saved search %s for user %s', search.id, user.user_id
        )
        return search.to_dict(), 201


@api.route('/saved-searches/<string:search_id>')
@api.param('search_id', 'Saved search identifier')
class SavedSearchResource(Resource):
    """Retrieve, update or delete a single saved search."""

    @api.doc(description='Get a saved search by id')
    @_require_user
    def get(self, search_id):
        search = _get_owned_or_404(search_id)
        return search.to_dict(), 200

    @api.doc(description='Update a saved search')
    @_require_user
    def put(self, search_id):
        search = _get_owned_or_404(search_id)
        data = request.get_json(silent=True) or {}
        name, params = _validate_payload(data, require_name=False)

        if name is not None and name != search.name:
            collision = (
                SavedSearch.query
                .filter(SavedSearch.user_id == search.user_id)
                .filter(SavedSearch.name == name)
                .filter(SavedSearch.id != search.id)
                .first()
            )
            if collision is not None:
                abort(409, 'A saved search with that name already exists')
            search.name = name

        if params is not None:
            search.params_json = params

        db.session.commit()
        current_app.logger.info('Updated saved search %s', search.id)
        return search.to_dict(), 200

    @api.doc(description='Delete a saved search')
    @_require_user
    def delete(self, search_id):
        search = _get_owned_or_404(search_id)
        db.session.delete(search)
        db.session.commit()
        current_app.logger.info('Deleted saved search %s', search.id)
        return '', 204
