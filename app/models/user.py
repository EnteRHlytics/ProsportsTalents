from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email_verified = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(255))
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = db.relationship('Role', secondary='user_roles', back_populates='users')
    oauth_accounts = db.relationship('UserOAuthAccount', back_populates='user', cascade='all, delete-orphan')
    
    def get_id(self):
        """Required by Flask-Login"""
        return self.user_id
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role_name):
        """Check if user has specific role"""
        return any(role.name == role_name for role in self.roles)
    
    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.username}>'