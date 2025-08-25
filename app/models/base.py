from app import db
from datetime import datetime
from sqlalchemy import event
from flask import current_app

class BaseModel(db.Model):
    """Enhanced base model with audit logging and soft delete"""
    __abstract__ = True
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    
    def save(self, commit=True):
        """Save the current instance with error handling"""
        try:
            db.session.add(self)
            if commit:
                db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving {self.__class__.__name__}: {e}")
            raise
    
    def delete(self, soft=True):
        """Delete the current instance (soft delete by default)"""
        try:
            if soft and hasattr(self, 'is_deleted'):
                self.is_deleted = True
                db.session.commit()
            else:
                db.session.delete(self)
                db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting {self.__class__.__name__}: {e}")
            raise
    
    def to_dict(self, include_relationships=False):
        """Convert model to dictionary with relationship handling"""
        try:
            data = {}
            
            # Include columns
            for column in self.__table__.columns:
                value = getattr(self, column.name)
                # Handle datetime serialization
                if isinstance(value, datetime):
                    value = value.isoformat()
                data[column.name] = value
            
            # Optionally include relationships
            if include_relationships:
                for relationship in self.__mapper__.relationships:
                    try:
                        related = getattr(self, relationship.key)
                        if related:
                            if relationship.uselist:
                                # Handle collections
                                data[relationship.key] = [
                                    item.to_dict() if hasattr(item, 'to_dict') else str(item)
                                    for item in related
                                ]
                            else:
                                # Handle single relationships
                                data[relationship.key] = (
                                    related.to_dict() if hasattr(related, 'to_dict') else str(related)
                                )
                    except Exception as e:
                        current_app.logger.warning(f"Error serializing relationship {relationship.key}: {e}")
                        data[relationship.key] = None
            
            return data
        except Exception as e:
            current_app.logger.error(f"Error converting {self.__class__.__name__} to dict: {e}")
            return {}
    
    @classmethod
    def bulk_insert(cls, records):
        """Bulk insert records for performance"""
        try:
            db.session.bulk_insert_mappings(cls, records)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Bulk insert error for {cls.__name__}: {e}")
            raise
    
    @classmethod
    def bulk_update(cls, records):
        """Bulk update records for performance"""
        try:
            db.session.bulk_update_mappings(cls, records)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Bulk update error for {cls.__name__}: {e}")
            raise

# Audit logging for models
def setup_audit_logging():
    """Setup audit logging for database changes"""
    
    @event.listens_for(BaseModel, 'before_insert', propagate=True)
    def receive_before_insert(mapper, connection, target):
        """Log before insert"""
        if current_app:
            current_app.logger.debug(f"Inserting {target.__class__.__name__}: {target.to_dict()}")
    
    @event.listens_for(BaseModel, 'before_update', propagate=True)
    def receive_before_update(mapper, connection, target):
        """Log before update"""
        if current_app:
            current_app.logger.debug(f"Updating {target.__class__.__name__}: {target.to_dict()}")
    
    @event.listens_for(BaseModel, 'before_delete', propagate=True)
    def receive_before_delete(mapper, connection, target):
        """Log before delete"""
        if current_app:
            current_app.logger.info(f"Deleting {target.__class__.__name__}: {target.to_dict()}")