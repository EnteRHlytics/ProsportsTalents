"""Cache manager stub.

Minimal no-op cache so the application boots in environments without a Redis
backend (unit tests, local dev). ``app/utils/__init__.py`` and ``app/__init__.py``
import ``cache_manager``/``cached`` from this module — when a real cache
implementation lands, replace this stub.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any


class _NoOpCacheManager:
    """No-op cache manager so the application can boot without Redis."""

    def __init__(self) -> None:
        self.redis_client = None
        self.app = None

    def init_app(self, app) -> None:
        self.app = app

    def get(self, key: str) -> Any | None:
        return None

    def set(self, key: str, value: Any, timeout: int | None = None) -> bool:
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
