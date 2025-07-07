import threading
import time

class RateLimiter:
    """Simple rate limiter enforcing a minimum interval between requests."""

    def __init__(self, min_interval: float = 1.0):
        self.min_interval = float(min_interval)
        self._lock = threading.Lock()
        self._last_time = 0.0

    def wait(self) -> None:
        """Block until it is OK to perform the next request."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self._last_time = time.monotonic()
