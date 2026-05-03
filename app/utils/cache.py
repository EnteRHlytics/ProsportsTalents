"""Minimal cache utilities.

This is a lightweight no-op stub used so the application can boot in
environments without a Redis backend (e.g. unit tests). The full
implementation may be provided elsewhere; if it exists, it should
override these definitions before they are used.
"""

from functools import wraps


class CacheManager:
    """Very small cache manager facade.

    Provides the surface area used elsewhere in the app
    (``init_app`` and an optional ``redis_client``) without
    requiring an actual cache backend.
    """

    def __init__(self):
        self.redis_client = None
        self.app = None

    def init_app(self, app):
        self.app = app

    def get(self, key):
        return None

    def set(self, key, value, timeout=None):
        return False

    def delete(self, key):
        return False


cache_manager = CacheManager()


def cached(timeout=60, key_prefix=""):
    """Decorator stub that simply calls the wrapped function.

    Mirrors the call signature of common Flask cache decorators so
    existing call sites work without requiring a real cache backend.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        return wrapper

    return decorator
