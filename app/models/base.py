from app import db
from datetime import datetime
import uuid

class BaseModel(db.Model):
    __abstract__ = True
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def save(self):
        """Save the current instance."""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete the current instance."""
        db.session.delete(self)
        db.session.commit()
        return True
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}