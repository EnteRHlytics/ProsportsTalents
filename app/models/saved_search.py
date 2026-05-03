import uuid

from app import db
from app.models.base import BaseModel


class SavedSearch(BaseModel):
    """A user-defined, reusable athlete search query.

    Stores the search/filter parameters as a JSON blob so the same
    UI can hydrate filters from a saved search and re-issue the
    request against ``/api/athletes/search``.
    """

    __tablename__ = 'saved_searches'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(120), nullable=False)
    params_json = db.Column(db.JSON, nullable=False, default=dict)

    # Relationship — note: the reverse side is intentionally NOT
    # added to the User model in this branch to avoid editing a
    # merge-hotspot file. See MERGE_NOTES.md for the diff to apply.
    user = db.relationship(
        'User',
        backref=db.backref('saved_searches', cascade='all, delete-orphan', lazy='dynamic'),
    )

    __table_args__ = (
        db.Index('idx_saved_searches_user', 'user_id'),
        db.UniqueConstraint('user_id', 'name', name='uq_saved_search_user_name'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'params': self.params_json or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):  # pragma: no cover
        return f'<SavedSearch {self.name!r} user={self.user_id}>'
