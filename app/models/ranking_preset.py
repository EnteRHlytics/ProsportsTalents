"""Ranking weight preset model.

Each preset captures a user-customised set of weights for the multi-factor
ranking algorithm.  A user may have several presets per sport (e.g.
"Scoring focus", "Two-way", "Durability") and pick one as their default.
"""

import json
import uuid

from app import db
from app.models.base import BaseModel


class RankingPreset(BaseModel):
    """User-saved weight configuration for the ranking algorithm."""

    __tablename__ = "ranking_presets"

    id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    sport_id = db.Column(
        db.Integer,
        db.ForeignKey("sports.sport_id", ondelete="SET NULL"),
        nullable=True,
    )
    name = db.Column(db.String(100), nullable=False)
    weights_json = db.Column(db.Text, nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    user = db.relationship("User")
    sport = db.relationship("Sport")

    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "sport_id", "name", name="uq_ranking_preset_name"
        ),
        db.Index("idx_ranking_presets_user", "user_id"),
        db.Index("idx_ranking_presets_user_sport", "user_id", "sport_id"),
    )

    # ------------------------------------------------------------------ helpers
    @property
    def weights(self):
        """Return the parsed weights dict (empty if invalid JSON)."""
        if not self.weights_json:
            return {}
        try:
            data = json.loads(self.weights_json)
        except (TypeError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    @weights.setter
    def weights(self, value):
        self.weights_json = json.dumps(dict(value or {}))

    def to_dict(self, include_relationships=False):
        data = super().to_dict(include_relationships=False)
        data["weights"] = self.weights
        # weights_json is an implementation detail; expose parsed form only.
        data.pop("weights_json", None)
        if self.sport is not None:
            data["sport_code"] = self.sport.code
        return data

    def __repr__(self):
        return f"<RankingPreset {self.id} {self.name!r}>"
