"""Persisted cache of computed fan-perception scores.

The :mod:`app.services.fan_perception_service` module fetches raw signals
from Wikipedia and Reddit and combines them into a 0-100 score.  Those
upstream calls are rate-limited and slow, so we cache the result in this
table.  The nightly scheduler job
:func:`app.jobs.nightly_refresh_fan_perception` refreshes every athlete's
row daily; ranking calculations read directly from the cache.
"""

from app import db
from app.models.base import BaseModel


class FanPerceptionScore(BaseModel):
    """Cached fan-perception score for an athlete.

    Attributes
    ----------
    id:
        Synthetic primary key.
    athlete_id:
        FK back to ``athlete_profiles``.  Unique - one cached score per
        athlete.
    score:
        Combined 0-100 score (Wikipedia views + Reddit mentions).
    source_breakdown:
        JSON-encoded string with the per-source raw values and sub-scores
        used to compute ``score``.  Useful for debugging and admin UIs.
    computed_at:
        Timestamp at which the upstream calls completed and ``score`` was
        produced.  Compare against ``CACHE_TTL`` to decide if a refresh is
        needed.
    """

    __tablename__ = 'fan_perception_scores'

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(
        db.String(36),
        db.ForeignKey('athlete_profiles.athlete_id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )
    score = db.Column(db.Numeric(5, 2), nullable=False)
    source_breakdown = db.Column(db.Text)
    computed_at = db.Column(db.DateTime, nullable=False)

    athlete = db.relationship('AthleteProfile', backref='fan_perception_score')

    __table_args__ = (
        db.Index('ix_fan_perception_scores_athlete_id', 'athlete_id'),
        db.Index('ix_fan_perception_scores_computed_at', 'computed_at'),
    )

    def __repr__(self):
        return f'<FanPerceptionScore athlete={self.athlete_id} score={self.score}>'
