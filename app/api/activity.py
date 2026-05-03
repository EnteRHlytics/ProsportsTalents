"""Activity log read endpoint.

GET ``/api/activity`` - admin-only listing of recent ActivityLog entries.

Query params
------------
- ``user_id``  (optional)  Filter by user id
- ``limit``    (optional, default 50, max 500)
- ``since``    (optional)  ISO-8601 timestamp; only entries on or after
                            this time are returned.

Returns 401 if unauthenticated, 403 if not admin, 400 on bad params.
"""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user

from app.models.activity_log import ActivityLog

# Standalone blueprint - registered separately under /api/activity so it
# does not collide with the Flask-RESTX api blueprint (which already owns
# the ``/api`` prefix). NOTE: registration is documented in
# MERGE_NOTES_HARDENING.md.
bp = Blueprint('activity', __name__, url_prefix='/api/activity')


def _is_admin(user) -> bool:
    if not getattr(user, 'is_authenticated', False):
        return False
    has_role = getattr(user, 'has_role', None)
    if callable(has_role):
        try:
            if has_role('admin'):
                return True
        except Exception:
            pass
    # Fallback: walk roles relationship
    roles = getattr(user, 'roles', None) or []
    return any(getattr(r, 'name', None) == 'admin' for r in roles)


def _parse_since(raw: str | None) -> datetime | None:
    if not raw:
        return None
    candidate = raw.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        abort(400, 'Invalid `since` parameter; expected ISO-8601 timestamp')


@bp.get('')
@bp.get('/')
def list_activity():
    """List recent activity entries. Admin-only."""
    if not getattr(current_user, 'is_authenticated', False):
        abort(401)
    if not _is_admin(current_user):
        abort(403)

    user_id = request.args.get('user_id') or None
    limit_raw = request.args.get('limit', default='50')
    try:
        limit = int(limit_raw)
    except (TypeError, ValueError):
        abort(400, 'Invalid `limit` parameter; expected integer')
    limit = max(1, min(limit, 500))

    since = _parse_since(request.args.get('since'))

    query = ActivityLog.query
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    if since:
        query = query.filter(ActivityLog.created_at >= since)

    rows = (
        query.order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )

    return jsonify({
        'items': [r.to_dict() for r in rows],
        'count': len(rows),
        'limit': limit,
    })
