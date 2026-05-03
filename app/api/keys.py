"""User-facing API key management endpoints.

Endpoints (mounted under the ``api`` blueprint):

- ``GET    /api/keys``       - list current user's keys (no key body)
- ``POST   /api/keys``       - create a key (raw key returned ONCE)
- ``DELETE /api/keys/<id>``  - revoke a key (soft via is_active=False)

The raw secret is only returned at creation time; the database stores
only the sha256 hash plus the first-12-character display prefix.
"""

import logging
from datetime import datetime
from functools import wraps

from flask import abort, request
from flask_login import current_user
from flask_restx import Resource

from app import db
from app.api import api
from app.models import ApiKey
from app.models.oauth import UserOAuthAccount

logger = logging.getLogger(__name__)


def _resolve_current_user():
    """Resolve the active user via session or Bearer token."""
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
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if _resolve_current_user() is None:
            abort(401)
        return fn(*args, **kwargs)
    return wrapper


def _parse_expires_at(value):
    if not value:
        return None
    try:
        if isinstance(value, datetime):
            return value
        # Allow ISO 8601 with optional 'Z'
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except (ValueError, TypeError):
        abort(400, 'Invalid expires_at; expected ISO 8601 datetime')


@api.route('/keys')
class ApiKeyList(Resource):
    """List or create the current user's API keys."""

    @api.doc(description="List the current user's API keys")
    @_require_user
    def get(self):
        user = _resolve_current_user()
        keys = (
            ApiKey.query.filter_by(user_id=user.user_id)
            .order_by(ApiKey.created_at.desc())
            .all()
        )
        return [k.to_dict() for k in keys], 200

    @api.doc(
        description='Create a new API key. Returns the raw key ONCE.',
        params={
            'name': 'Display name for the key',
            'scopes': 'JSON array of scope strings (optional)',
            'expires_at': 'Optional ISO 8601 expiry timestamp',
        },
    )
    @_require_user
    def post(self):
        user = _resolve_current_user()
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            abort(400, 'Request body must be a JSON object')

        name = (data.get('name') or '').strip()
        if not name:
            abort(400, 'Field "name" is required')

        scopes = data.get('scopes')
        if scopes is not None and not isinstance(scopes, list):
            abort(400, 'Field "scopes" must be a JSON array')

        expires_at = _parse_expires_at(data.get('expires_at'))

        record, raw_key = ApiKey.generate(
            user_id=user.user_id,
            name=name,
            scopes=scopes,
            expires_at=expires_at,
        )
        db.session.add(record)
        db.session.commit()
        logger.info('Created API key %s for user %s', record.api_key_id, user.user_id)

        return {
            'api_key_id': record.api_key_id,
            'name': record.name,
            'key': raw_key,  # only returned ONCE
            'key_prefix': record.key_prefix,
            'scopes': record.scopes,
            'expires_at': (
                record.expires_at.isoformat() if record.expires_at else None
            ),
            'created_at': (
                record.created_at.isoformat() if record.created_at else None
            ),
        }, 201


@api.route('/keys/<string:api_key_id>')
@api.param('api_key_id', 'API key identifier')
class ApiKeyResource(Resource):
    """Revoke an API key."""

    @api.doc(description='Revoke (soft-delete) an API key')
    @_require_user
    def delete(self, api_key_id):
        user = _resolve_current_user()
        record = ApiKey.query.filter_by(api_key_id=api_key_id).first()
        if record is None or record.user_id != user.user_id:
            abort(404, 'API key not found')
        record.is_active = False
        db.session.commit()
        logger.info('Revoked API key %s for user %s', api_key_id, user.user_id)
        return '', 204
