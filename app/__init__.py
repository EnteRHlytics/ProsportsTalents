from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
oauth = OAuth()

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    oauth.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Configure OAuth providers
    configure_oauth(app)
    
    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.athletes import bp as athletes_bp
    app.register_blueprint(athletes_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp)

    if app.config.get('ENABLE_SCHEDULER'):
        from .scheduler import init_scheduler
        init_scheduler(app)
    
    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(user_id)

    return app

def configure_oauth(app):
    """Configure OAuth providers"""
    
    # Google OAuth
    if app.config.get('GOOGLE_CLIENT_ID'):
        oauth.register(
            name='google',
            client_id=app.config.get('GOOGLE_CLIENT_ID'),
            client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'}
        )
    
    # GitHub OAuth
    if app.config.get('GITHUB_CLIENT_ID'):
        oauth.register(
            name='github',
            client_id=app.config.get('GITHUB_CLIENT_ID'),
            client_secret=app.config.get('GITHUB_CLIENT_SECRET'),
            access_token_url='https://github.com/login/oauth/access_token',
            authorize_url='https://github.com/login/oauth/authorize',
            api_base_url='https://api.github.com/',
            client_kwargs={'scope': 'user:email'}
        )
    
    # Azure OAuth
    if app.config.get('AZURE_CLIENT_ID') and app.config.get('AZURE_TENANT_ID'):
        oauth.register(
            name='azure',
            client_id=app.config.get('AZURE_CLIENT_ID'),
            client_secret=app.config.get('AZURE_CLIENT_SECRET'),
            server_metadata_url=f'https://login.microsoftonline.com/{app.config.get("AZURE_TENANT_ID")}/v2.0/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'}
        )
