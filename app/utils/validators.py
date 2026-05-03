from functools import wraps

from flask import jsonify, request
from marshmallow import Schema, ValidationError, fields


def validate_params(required_params):
    """Decorator to validate request parameters.

    ``required_params`` may be a list/tuple of required parameter names. The
    parameters may come from ``request.args``, ``request.json`` (when JSON
    body), or ``request.form``.
    """
    required_params = list(required_params or [])

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            json_body = None
            if request.is_json:
                try:
                    json_body = request.get_json(silent=True)
                except Exception:
                    json_body = None
            json_body = json_body or {}
            for param in required_params:
                if (
                    param not in request.args
                    and param not in json_body
                    and param not in request.form
                ):
                    return jsonify({'error': f'Missing required parameter: {param}'}), 400
            return f(*args, **kwargs)

        return wrapper

    return decorator


def validate_json(schema):
    """Decorator to validate JSON request body.

    ``schema`` may be either:

    - A list/tuple of required field names (lightweight validation).
    - A Marshmallow ``Schema`` instance (full schema validation).
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400

            data = request.get_json(silent=True) or {}

            # Lightweight required-field validation when given a list.
            if isinstance(schema, (list, tuple, set)):
                missing = [k for k in schema if k not in data]
                if missing:
                    return (
                        jsonify({
                            'error': 'Missing required fields',
                            'missing': missing,
                        }),
                        400,
                    )
                return f(*args, **kwargs)

            # Marshmallow schema validation.
            try:
                schema.load(data)
            except ValidationError as e:
                return jsonify({'error': 'Validation error', 'messages': e.messages}), 400

            return f(*args, **kwargs)

        return wrapper

    return decorator

# Common validation schemas
class PaginationSchema(Schema):
    """Schema for pagination parameters"""
    page = fields.Integer(load_default=1, validate=lambda x: x >= 1)
    per_page = fields.Integer(load_default=50, validate=lambda x: 1 <= x <= 100)

class SearchSchema(Schema):
    """Schema for search parameters"""
    q = fields.String(load_default='')
    sport = fields.String(load_default=None, allow_none=True)
    position = fields.String(load_default=None, allow_none=True)
    team = fields.String(load_default=None, allow_none=True)
    min_age = fields.Integer(load_default=None, allow_none=True, validate=lambda x: x is None or x >= 0)
    max_age = fields.Integer(load_default=None, allow_none=True, validate=lambda x: x is None or x >= 0)
    min_height = fields.Integer(load_default=None, allow_none=True, validate=lambda x: x is None or x >= 0)
    max_height = fields.Integer(load_default=None, allow_none=True, validate=lambda x: x is None or x >= 0)
    min_weight = fields.Float(load_default=None, allow_none=True, validate=lambda x: x is None or x >= 0)
    max_weight = fields.Float(load_default=None, allow_none=True, validate=lambda x: x is None or x >= 0)
    filter = fields.String(load_default=None, allow_none=True)
    page = fields.Integer(load_default=1, validate=lambda x: x >= 1)
    per_page = fields.Integer(load_default=50, validate=lambda x: 1 <= x <= 100)
