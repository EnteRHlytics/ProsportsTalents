from functools import wraps
from flask import request, jsonify
from marshmallow import Schema, fields, ValidationError

def validate_params(required_params):
    """Decorator to validate request parameters"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Check for required parameters
            for param in required_params:
                if param not in request.args and param not in request.json:
                    return jsonify({'error': f'Missing required parameter: {param}'}), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

def validate_json(schema):
    """Decorator to validate JSON request body against a schema"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Validate request JSON
                if not request.is_json:
                    return jsonify({'error': 'Request must be JSON'}), 400
                
                # Validate against schema
                schema.load(request.json)
                
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