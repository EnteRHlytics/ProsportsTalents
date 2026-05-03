"""Audit middleware: log mutating HTTP requests to the ActivityLog table.

Registers a Flask ``after_request`` hook that:

- Only fires for ``POST``, ``PUT``, ``PATCH`` and ``DELETE`` requests.
- Resolves the authenticated user via ``flask_login.current_user`` when
  available; falls back to ``None`` for anonymous calls.
- Captures IP (honoring ``X-Forwarded-For`` if present), user agent, status
  code, and a best-effort ``target_resource_id`` extracted from the trailing
  path segment when it looks like an id (uuid, int, or short alnum slug).
- Failures inside the audit hook are logged but never block the response.

Skips:
- Static asset routes
- ``/api/swagger`` swagger docs noise
- HEAD/OPTIONS/GET (read-only) requests
"""

from __future__ import annotations

import logging
import re
import uuid

from flask import Flask, Response, request

logger = logging.getLogger(__name__)

_MUTATING_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
_SKIP_PREFIXES = ('/static/', '/api/swagger', '/api/swaggerui')

# Heuristics for "looks like a resource id"
_UUID_RE = re.compile(
    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
)
_INT_RE = re.compile(r'^\d+$')
_SLUG_RE = re.compile(r'^[A-Za-z0-9_-]{6,64}$')


def _looks_like_id(segment: str) -> bool:
    if not segment:
        return False
    if _UUID_RE.match(segment):
        return True
    if _INT_RE.match(segment):
        return True
    # Restrict slugs to those containing at least one digit OR a dash, to
    # avoid matching plain words like "athletes".
    if _SLUG_RE.match(segment) and (any(c.isdigit() for c in segment) or '-' in segment):
        return True
    return False


def extract_target_resource_id(path: str) -> str | None:
    """Best-effort extraction of a resource id from a URL path.

    - Strips a trailing 'sub-action' segment that is clearly not an id
      (e.g. ``/api/athletes/<id>/media`` -> returns ``<id>``).
    - Returns ``None`` when nothing looks like an id.
    """
    if not path:
        return None
    parts = [p for p in path.split('/') if p]
    if not parts:
        return None

    # Walk segments right-to-left; first id-shaped segment wins.
    for segment in reversed(parts):
        if _looks_like_id(segment):
            return segment
    return None


def _client_ip() -> str | None:
    fwd = request.headers.get('X-Forwarded-For')
    if fwd:
        # First entry is original client
        return fwd.split(',')[0].strip()
    return request.remote_addr


def _current_user_id() -> str | None:
    try:
        from flask_login import current_user
        if getattr(current_user, 'is_authenticated', False):
            uid = getattr(current_user, 'user_id', None) or current_user.get_id()
            return str(uid) if uid else None
    except Exception:
        return None
    return None


def _record(response: Response, app: Flask) -> None:
    from app import db
    from app.models.activity_log import ActivityLog

    user_agent = request.headers.get('User-Agent', '')
    if user_agent and len(user_agent) > 512:
        user_agent = user_agent[:512]

    log = ActivityLog(
        id=str(uuid.uuid4()),
        user_id=_current_user_id(),
        method=request.method,
        path=request.path[:2048],
        status_code=response.status_code,
        ip=_client_ip(),
        user_agent=user_agent or None,
        target_resource_id=extract_target_resource_id(request.path),
    )
    try:
        db.session.add(log)
        db.session.commit()
    except Exception as exc:
        # Don't let audit failures bubble up
        try:
            db.session.rollback()
        except Exception:
            pass
        app.logger.warning('ActivityLog write failed: %s', exc)


def register_audit_middleware(app: Flask) -> None:
    """Attach the audit ``after_request`` hook to ``app``."""

    @app.after_request
    def _audit_after_request(response: Response):  # pragma: no cover - exercised via tests
        try:
            if request.method not in _MUTATING_METHODS:
                return response
            path = request.path or ''
            if any(path.startswith(p) for p in _SKIP_PREFIXES):
                return response
            _record(response, app)
        except Exception as exc:
            # Final guard - never break the response
            app.logger.warning('Audit middleware error: %s', exc)
        return response
