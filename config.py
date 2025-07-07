import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://app_user:app_secure_pass123!@localhost:5432/sport_agency_dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
    AZURE_CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')
    AZURE_CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET')
    AZURE_TENANT_ID = os.environ.get('AZURE_TENANT_ID')
    NBA_API_BASE_URL = os.environ.get("NBA_API_BASE_URL") or "https://www.balldontlie.io/api/v1"
    NBA_API_TOKEN = os.environ.get("NBA_API_TOKEN")
    NFL_API_BASE_URL = os.environ.get("NFL_API_BASE_URL") or "https://api.nfl.com/v1"
    NHL_API_BASE_URL = os.environ.get("NHL_API_BASE_URL") or "https://statsapi.web.nhl.com/api/v1"
    CLIENT_SATISFACTION_PERCENT = float(os.environ.get('CLIENT_SATISFACTION_PERCENT', '98.7'))
    TOP_RANKINGS_FILE = os.environ.get('TOP_RANKINGS_FILE')
    ENABLE_SCHEDULER = os.environ.get('ENABLE_SCHEDULER', 'false').lower() == 'true'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
