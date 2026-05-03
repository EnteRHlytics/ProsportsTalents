"""API key / token security helpers stub.

Minimal stub required because ``app/api/routes.py`` imports
``require_api_key`` from this module. Validates an ``X-API-Key`` header
against the ``ApiKey`` model when the table exists, otherwise lets the
request through (so it does not break local/dev work).
"""

from functools import wraps
from typing import Callable

from flask import abort, request


def require_api_key(fn: Callable) -> Callable:
    """Best-effort API key validator."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        try:
            from app.models import ApiKey  # type: ignore
        except Exception:
            return fn(*args, **kwargs)

        if not api_key:
            try:
                count = ApiKey.query.limit(1).count()
            except Exception:
                return fn(*args, **kwargs)
            if count == 0:
                return fn(*args, **kwargs)
            abort(401, "API key required")

        try:
            record = ApiKey.query.filter_by(key=api_key).first()
        except Exception:
            return fn(*args, **kwargs)
        if not record or not getattr(record, "is_active", True):
            abort(401, "Invalid API key")
        return fn(*args, **kwargs)

    return wrapper
