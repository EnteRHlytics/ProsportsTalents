import os
from dotenv import load_dotenv
import logging

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """Base configuration with validation"""
    
    # Required configurations
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        logger.warning("SECRET_KEY not set, using development key")
        SECRET_KEY = 'dev-secret-key-change-in-production'
    
    # Database configuration with fallback
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://app_user:app_secure_pass123!@localhost:5432/sport_agency_dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Connection pool settings for performance
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,  # Verify connections before using
        'max_overflow': 20
    }
    
    # OAuth Configuration with validation
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
    AZURE_CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')
    AZURE_CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET')
    AZURE_TENANT_ID = os.environ.get('AZURE_TENANT_ID')
    
    # External sports APIs with validation
    NBA_API_BASE_URL = os.environ.get("NBA_API_BASE_URL", "https://api.balldontlie.io/v1")
    NBA_API_TOKEN = os.environ.get("NBA_API_TOKEN") or os.environ.get("BALLDONTLIE_API_TOKEN")
    NFL_API_BASE_URL = os.environ.get("NFL_API_BASE_URL", "https://api.balldontlie.io/nfl/v1")
    NFL_API_TOKEN = os.environ.get("NFL_API_TOKEN") or os.environ.get("BALLDONTLIE_API_TOKEN")
    MLB_API_BASE_URL = os.environ.get("MLB_API_BASE_URL", "https://statsapi.mlb.com/api/v1")
    NHL_API_BASE_URL = os.environ.get("NHL_API_BASE_URL", "https://statsapi.web.nhl.com/api/v1")
    
    # Application settings
    CLIENT_SATISFACTION_PERCENT = float(os.environ.get('CLIENT_SATISFACTION_PERCENT', '98.7'))
    TOP_RANKINGS_FILE = os.environ.get('TOP_RANKINGS_FILE')
    ENABLE_SCHEDULER = os.environ.get('ENABLE_SCHEDULER', 'false').lower() == 'true'
    
    # Security settings
    SESSION_COOKIE_SECURE = True  # HTTPS only in production
    SESSION_COOKIE_HTTPONLY = True  # Prevent XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    
    # File upload settings
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    UPLOAD_FOLDER = os.path.join(basedir, 'storage')
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx'}
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    
    @classmethod
    def validate_config(cls):
        """Validate critical configuration"""
        errors = []
        
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            errors.append("Using default SECRET_KEY - not secure for production")
        
        if not cls.SQLALCHEMY_DATABASE_URI:
            errors.append("Database URI not configured")
        
        # Check OAuth configuration completeness
        if cls.GOOGLE_CLIENT_ID and not cls.GOOGLE_CLIENT_SECRET:
            errors.append("Google OAuth partially configured - missing CLIENT_SECRET")
        
        if cls.GITHUB_CLIENT_ID and not cls.GITHUB_CLIENT_SECRET:
            errors.append("GitHub OAuth partially configured - missing CLIENT_SECRET")
        
        if cls.AZURE_CLIENT_ID and not (cls.AZURE_CLIENT_SECRET and cls.AZURE_TENANT_ID):
            errors.append("Azure OAuth partially configured - missing CLIENT_SECRET or TENANT_ID")
        
        # Check API tokens for dependent services
        if not (cls.NBA_API_TOKEN or cls.NFL_API_TOKEN):
            logger.warning("No BallDontLie API token configured - NBA/NFL features will be limited")
        
        return errors

class DevelopmentConfig(Config):
    DEBUG = True
    # Development-specific settings
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    
class ProductionConfig(Config):
    DEBUG = False
    # Production-specific settings
    SESSION_COOKIE_SECURE = True
    
    @classmethod
    def validate_config(cls):
        """Additional production validations"""
        errors = super().validate_config()
        
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            errors.append("CRITICAL: Production requires a secure SECRET_KEY")
        
        if 'sqlite' in cls.SQLALCHEMY_DATABASE_URI.lower():
            errors.append("WARNING: SQLite not recommended for production")
        
        return errors

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    SESSION_COOKIE_SECURE = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}