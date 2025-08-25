from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from werkzeug.exceptions import HTTPException
import logging
from logging.handlers import RotatingFileHandler
import os

from config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
oauth = OAuth()
def _limiter_key():
    # Prefer API key prefix for fair limiting; fallback to IP
    try:
        from flask import request
        api_key = request.headers.get('X-API-Key')
        if api_key:
            # Use only a prefix to avoid storing secrets in Redis logs
            return f"api:{api_key[:12]}"
    except Exception:
        pass
    return get_remote_address()

limiter = Limiter(key_func=_limiter_key)

# Import cache manager after defining db
from app.utils.cache import cache_manager

def create_app(config_name='development'):
    """Application factory with enhanced error handling and middleware"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Validate configuration
    config_errors = app.config.get('validate_config', lambda: [])()
    if config_errors:
        for error in config_errors:
            app.logger.warning(f"Configuration issue: {error}")
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    oauth.init_app(app)
    limiter.init_app(app)
    cache_manager.init_app(app)
    
    # Configure CORS for API endpoints
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.session_protection = 'strong'  # Enhanced session security
    
    # Configure OAuth providers
    configure_oauth(app)
    
    # Setup logging
    setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Initialize scheduler if enabled
    if app.config.get('ENABLE_SCHEDULER'):
        from app.scheduler import init_scheduler
        init_scheduler(app)
    
    # User loader with error handling
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        try:
            return User.query.get(user_id)
        except Exception as e:
            app.logger.error(f"Error loading user {user_id}: {e}")
            return None
    
    # Request logging middleware
    @app.before_request
    def log_request():
        """Log incoming requests for debugging"""
        if app.config.get('DEBUG'):
            app.logger.debug(f"Request: {request.method} {request.path}")
    
    # Performance monitoring
    @app.after_request
    def after_request(response):
        """Add security headers and log response"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        if app.config.get('DEBUG'):
            app.logger.debug(f"Response: {response.status_code}")
        
        return response
    
    return app

def configure_oauth(app):
    """Configure OAuth providers with error handling"""
    
    # Google OAuth
    if app.config.get('GOOGLE_CLIENT_ID'):
        try:
            oauth.register(
                name='google',
                client_id=app.config.get('GOOGLE_CLIENT_ID'),
                client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
                server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                client_kwargs={'scope': 'openid email profile'}
            )
            app.logger.info("Google OAuth configured successfully")
        except Exception as e:
            app.logger.error(f"Failed to configure Google OAuth: {e}")
    
    # GitHub OAuth
    if app.config.get('GITHUB_CLIENT_ID'):
        try:
            oauth.register(
                name='github',
                client_id=app.config.get('GITHUB_CLIENT_ID'),
                client_secret=app.config.get('GITHUB_CLIENT_SECRET'),
                access_token_url='https://github.com/login/oauth/access_token',
                authorize_url='https://github.com/login/oauth/authorize',
                api_base_url='https://api.github.com/',
                client_kwargs={'scope': 'user:email'}
            )
            app.logger.info("GitHub OAuth configured successfully")
        except Exception as e:
            app.logger.error(f"Failed to configure GitHub OAuth: {e}")
    
    # Azure OAuth
    if app.config.get('AZURE_CLIENT_ID') and app.config.get('AZURE_TENANT_ID'):
        try:
            oauth.register(
                name='azure',
                client_id=app.config.get('AZURE_CLIENT_ID'),
                client_secret=app.config.get('AZURE_CLIENT_SECRET'),
                server_metadata_url=f'https://login.microsoftonline.com/{app.config.get("AZURE_TENANT_ID")}/v2.0/.well-known/openid-configuration',
                client_kwargs={'scope': 'openid email profile'}
            )
            app.logger.info("Azure OAuth configured successfully")
        except Exception as e:
            app.logger.error(f"Failed to configure Azure OAuth: {e}")

def register_blueprints(app):
    """Register all blueprints with error handling"""
    blueprint_configs = [
        ('app.main', 'main', None),
        ('app.auth', 'auth', '/auth'),
        ('app.athletes', 'athletes', None),
        ('app.api', 'api', None),
    ]
    
    for module_name, bp_name, url_prefix in blueprint_configs:
        try:
            module = __import__(module_name, fromlist=['bp'])
            blueprint = getattr(module, 'bp')
            if url_prefix:
                app.register_blueprint(blueprint, url_prefix=url_prefix)
            else:
                app.register_blueprint(blueprint)
            app.logger.info(f"Registered blueprint: {bp_name}")
        except Exception as e:
            app.logger.error(f"Failed to register blueprint {bp_name}: {e}")

def register_error_handlers(app):
    """Register comprehensive error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        db.session.rollback()
        app.logger.error(f"Internal error: {error}")
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handle HTTP exceptions"""
        if request.path.startswith('/api/'):
            return jsonify({'error': e.description}), e.code
        return e
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors"""
        app.logger.error(f"Unexpected error: {error}", exc_info=True)
        db.session.rollback()
        if request.path.startswith('/api/'):
            return jsonify({'error': 'An unexpected error occurred'}), 500
        return render_template('errors/500.html'), 500

def setup_logging(app):
    """Setup comprehensive logging"""
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Setup rotating file handler
        file_handler = RotatingFileHandler(
            'logs/sport_agency.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Sport Agency startup')