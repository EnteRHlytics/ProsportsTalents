from app import db
from datetime import datetime

class Sport(db.Model):
    __tablename__ = 'sports'
    
    sport_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)  # NBA, NFL, MLB, NHL
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    positions = db.relationship('Position', back_populates='sport', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Sport {self.name}>'

class Position(db.Model):
    __tablename__ = 'positions'
    
    position_id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(db.Integer, db.ForeignKey('sports.sport_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sport = db.relationship('Sport', back_populates='positions')
    
    # Unique constraint per sport
    __table_args__ = (
        db.UniqueConstraint('sport_id', 'code', name='uq_sport_position_code'),
    )
    
    def __repr__(self):
        return f'<Position {self.sport.name}:{self.name}>'