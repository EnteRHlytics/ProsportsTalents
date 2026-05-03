"""API key model.

A user-issued API key is identified by:
- ``key_hash``: a sha256 hex digest of the raw secret. Only the hash is stored.
- ``key_prefix``: first 12 chars of the raw secret, for display only.

Raw secrets are only known at creation time. Callers must capture the
returned key value immediately - the server cannot reproduce it later.

Wave-1 supplied a minimal stub. This module replaces it with the
production schema.
"""

from __future__ import annotations

import hashlib
import secrets as _secrets
import uuid
from datetime import datetime
from typing import Optional, Tuple

from app import db
from app.models.base import BaseModel


def _hash_key(raw: str) -> str:
    """Return a stable sha256 hex digest of ``raw``."""
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


class ApiKey(BaseModel):
    __tablename__ = 'api_keys'

    api_key_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=True,
        index=True,
    )
    name = db.Column(db.String(120), nullable=False)
    key_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    key_prefix = db.Column(db.String(16), nullable=False, index=True)
    scopes = db.Column(db.JSON, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_used_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship(
        'User', backref=db.backref('api_keys', cascade='all, delete-orphan', lazy='dynamic')
    )

    # ----- helpers -----

    @staticmethod
    def hash_key(raw: str) -> str:
        return _hash_key(raw)

    @classmethod
    def generate(
        cls,
        *,
        user_id: Optional[str],
        name: str,
        scopes: Optional[list] = None,
        expires_at: Optional[datetime] = None,
    ) -> Tuple['ApiKey', str]:
        """Create (but don't persist) an ApiKey + the raw key.

        Returns ``(api_key, raw_key)``. Caller is responsible for adding to
        the session and committing.
        """
        raw = _secrets.token_urlsafe(32)
        record = cls(
            user_id=user_id,
            name=name,
            key_hash=_hash_key(raw),
            key_prefix=raw[:12],
            scopes=scopes,
            is_active=True,
            expires_at=expires_at,
        )
        return record, raw

    @classmethod
    def find_by_raw_key(cls, raw: str) -> Optional['ApiKey']:
        """Look up an active, non-expired key by raw value."""
        if not raw:
            return None
        candidate = cls.query.filter_by(key_hash=_hash_key(raw)).first()
        if candidate is None or not candidate.is_active:
            return None
        if candidate.expires_at is not None and candidate.expires_at < datetime.utcnow():
            return None
        return candidate

    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at < datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            'api_key_id': self.api_key_id,
            'user_id': self.user_id,
            'name': self.name,
            'key_prefix': self.key_prefix,
            'scopes': self.scopes,
            'is_active': bool(self.is_active),
            'last_used_at': (
                self.last_used_at.isoformat() if self.last_used_at else None
            ),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f'<ApiKey {self.name} prefix={self.key_prefix}>'
