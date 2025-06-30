from app import db
from app.models.base import BaseModel
import uuid

class AthleteMedia(BaseModel):
    __tablename__ = 'athlete_media'

    media_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    athlete_id = db.Column(db.String(36), db.ForeignKey('athlete_profiles.athlete_id', ondelete='CASCADE'), nullable=False)
    media_type = db.Column(db.String(20))
    file_path = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))

    athlete = db.relationship('AthleteProfile', backref='media')

    __table_args__ = (
        db.Index('idx_media_athlete', 'athlete_id'),
    )

    def __repr__(self):
        return f'<AthleteMedia {self.media_id}>'
