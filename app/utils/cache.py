"""Cache manager stub.

NOTE (Agent5): This is a minimal stub required because ``app/utils/__init__.py``
and ``app/__init__.py`` import ``cache_manager``/``cached`` from this module,
but the actual cache implementation appears to belong to another agent.

If a richer caching layer is supplied later, this stub can be replaced.
The stub is import-safe and provides a no-op ``init_app`` plus a passthrough
``cached`` decorator so the application boots and tests can run.
"""

from functools import wraps
from typing import Any, Callable, Optional


class _NoOpCacheManager:
    """No-op cache manager so the application can boot without Redis."""

    def __init__(self) -> None:
        self.redis_client = None
        self.app = None

    def init_app(self, app) -> None:  # noqa: D401 - simple proxy
        """Attach to the Flask app. No backend is configured."""
        self.app = app

    # Minimal interface other call sites may rely on
    def get(self, key: str) -> Optional[Any]:
        return None

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        return False

    def delete(self, key: str) -> bool:
        return False

    def clear(self) -> bool:
        return False


cache_manager = _NoOpCacheManager()


def cached(timeout: int = 300, key_prefix: str = "") -> Callable:
    """No-op caching decorator. Calls the wrapped function every time."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        return wrapper

    return decorator
