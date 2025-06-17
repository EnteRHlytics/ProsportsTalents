from app import db
from app.models.base import BaseModel
from enum import Enum
import uuid

class AthleteStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    RETIRED = 'retired'
    SUSPENDED = 'suspended'

class AthleteProfile(BaseModel):
    __tablename__ = 'athlete_profiles'
    
    athlete_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, unique=True)
    primary_sport_id = db.Column(db.Integer, db.ForeignKey('sports.sport_id'))
    primary_position_id = db.Column(db.Integer, db.ForeignKey('positions.position_id'))
    
    # Physical attributes
    height_cm = db.Column(db.Integer)
    weight_kg = db.Column(db.Numeric(5, 2))
    
    # Personal information
    date_of_birth = db.Column(db.Date, nullable=False)
    nationality = db.Column(db.String(3))  # ISO 3166-1 alpha-3
    birthplace_city = db.Column(db.String(100))
    birthplace_country = db.Column(db.String(3))
    
    # Career information
    career_status = db.Column(db.Enum(AthleteStatus), default=AthleteStatus.ACTIVE)
    professional_debut_date = db.Column(db.Date)
    years_professional = db.Column(db.Integer)
    current_team = db.Column(db.String(100))
    jersey_number = db.Column(db.String(5))
    
    # Profile information
    bio = db.Column(db.Text)
    profile_image_url = db.Column(db.String(500))
    is_verified = db.Column(db.Boolean, default=False)
    verification_date = db.Column(db.DateTime)
    
    # Search and ranking
    search_vector = db.Column(db.Text)  # For full-text search
    overall_rating = db.Column(db.Numeric(4, 2))  # 0.00 to 99.99
    
    # Relationships
    user = db.relationship('User', back_populates='athlete_profile')
    primary_sport = db.relationship('Sport', back_populates='athletes')
    primary_position = db.relationship('Position')
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('height_cm BETWEEN 100 AND 250', name='ck_height_reasonable'),
        db.CheckConstraint('weight_kg BETWEEN 30 AND 200', name='ck_weight_reasonable'),
        db.CheckConstraint('overall_rating BETWEEN 0 AND 99.99', name='ck_rating_range'),
        db.Index('idx_athletes_sport_position', 'primary_sport_id', 'primary_position_id'),
        db.Index('idx_athletes_status_verified', 'career_status', 'is_verified'),
        db.Index('idx_athletes_search', 'search_vector'),  # For full-text search
    )
    
    @property
    def age(self):
        """Calculate current age."""
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def __repr__(self):
        return f'<AthleteProfile {self.user.full_name}>'