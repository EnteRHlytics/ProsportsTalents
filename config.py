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

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}