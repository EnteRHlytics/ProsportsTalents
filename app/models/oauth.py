from app import db
from datetime import datetime
import uuid

class UserOAuthAccount(db.Model):
    __tablename__ = 'user_oauth_accounts'
    
    account_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    provider_name = db.Column(db.String(50), nullable=False)  # 'google', 'github', 'azure'
    provider_user_id = db.Column(db.String(255), nullable=False)
    access_token = db.Column(db.Text)  # In production, encrypt this
    refresh_token = db.Column(db.Text)  # In production, encrypt this
    provider_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='oauth_accounts')
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('provider_name', 'provider_user_id', name='uq_provider_user'),
    )
    
    def __repr__(self):
        return f'<UserOAuthAccount {self.user_id}:{self.provider_name}>'