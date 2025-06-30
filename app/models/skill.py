from app import db
from app.models.base import BaseModel
import uuid

class AthleteSkill(BaseModel):
    __tablename__ = 'athlete_skills'

    skill_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    athlete_id = db.Column(db.String(36), db.ForeignKey('athlete_profiles.athlete_id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer)

    athlete = db.relationship('AthleteProfile', back_populates='skills')

    __table_args__ = (
        db.Index('idx_skills_athlete', 'athlete_id'),
    )

    def __repr__(self):
        return f'<AthleteSkill {self.name}>'
