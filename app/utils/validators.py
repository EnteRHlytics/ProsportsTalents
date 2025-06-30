from functools import wraps
from flask import request, abort


def validate_json(required_fields):
    """Ensure a JSON payload with required fields is present."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                abort(400, description="Invalid or missing JSON payload")
            data = request.get_json() or {}
            missing = [f for f in required_fields if f not in data]
            if missing:
                abort(400, description="Missing fields: " + ", ".join(missing))
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def validate_params(required_params):
    """Ensure request args contain required query parameters."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            missing = [p for p in required_params if p not in request.args]
            if missing:
                abort(400, description="Missing parameters: " + ", ".join(missing))
            return fn(*args, **kwargs)

        return wrapper

    return decorator
