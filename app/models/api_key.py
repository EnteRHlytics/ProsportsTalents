"""ApiKey model stub.

NOTE (Agent5): ``app/models/__init__.py`` imports ``ApiKey``; the full
implementation belongs to the API/keys agent. This minimal model exists so
the application can boot and unrelated tests can run, and so
``app.utils.security.require_api_key`` has a model to query against.
It should be overwritten by the owning agent's real implementation.
"""

from datetime import datetime
import uuid

from app import db


class ApiKey(db.Model):
    __tablename__ = 'api_keys'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=True)
    name = db.Column(db.String(100))
    key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    last_used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
