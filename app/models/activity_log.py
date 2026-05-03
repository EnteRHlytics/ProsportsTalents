"""ActivityLog model.

Records mutating HTTP requests (POST/PUT/PATCH/DELETE) for audit purposes,
per section 3.2 (User Management -> Activity Tracking) of the Web Application
Requirements Document.

Fields
------
- ``user_id``        FK to ``users.user_id`` (nullable; anonymous calls allowed)
- ``method``         HTTP method
- ``path``           Request path (without query string)
- ``status_code``    Response status code (filled by audit middleware)
- ``ip``             Client IP address (best-effort, considers X-Forwarded-For)
- ``user_agent``     ``User-Agent`` header
- ``target_resource_id``  Trailing path segment if it looks like an id
- ``created_at``     UTC timestamp, indexed for time-range queries
"""

from datetime import datetime
import uuid

from app import db


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    method = db.Column(db.String(10), nullable=False)
    path = db.Column(db.String(2048), nullable=False)
    status_code = db.Column(db.Integer, nullable=True)
    ip = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    target_resource_id = db.Column(db.String(255), nullable=True, index=True)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    __table_args__ = (
        db.Index('idx_activity_user_created', 'user_id', 'created_at'),
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'method': self.method,
            'path': self.path,
            'status_code': self.status_code,
            'ip': self.ip,
            'user_agent': self.user_agent,
            'target_resource_id': self.target_resource_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f'<ActivityLog {self.method} {self.path} '
            f'user={self.user_id} status={self.status_code}>'
        )
