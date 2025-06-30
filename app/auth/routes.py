from flask import render_template, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, current_user
from app.auth import bp
from app import db, oauth
from app.models.user import User
from app.models.role import Role
from app.models.oauth import UserOAuthAccount
from datetime import datetime
import requests

@bp.route('/login')
def login():
    """Display login page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('auth/login.html')

@bp.route('/login/<provider>')
def oauth_login(provider):
    """Initiate OAuth login"""
    if provider not in ['google', 'github', 'azure']:
        flash('Invalid provider', 'error')
        return redirect(url_for('auth.login'))
    
    if not hasattr(oauth, provider):
        flash(f'{provider.title()} OAuth not configured', 'error')
        return redirect(url_for('auth.login'))
    
    oauth_client = getattr(oauth, provider)
    redirect_uri = url_for('auth.oauth_callback', provider=provider, _external=True)
    return oauth_client.authorize_redirect(redirect_uri)

@bp.route('/callback/<provider>')
def oauth_callback(provider):
    """Handle OAuth callback"""
    try:
        oauth_client = getattr(oauth, provider)
        token = oauth_client.authorize_access_token()
        
        # Get user info
        user_info = get_user_info_from_provider(provider, token)
        
        if not user_info or not user_info.get('email'):
            flash('Could not get user information', 'error')
            return redirect(url_for('auth.login'))
        
        # Find or create user
        user = find_or_create_oauth_user(user_info, provider, token)
        
        if user and user.is_active:
            # Update login info
            user.last_login = datetime.utcnow()
            user.login_count = (user.login_count or 0) + 1
            db.session.commit()
            
            # Login user and store token for API access
            login_user(user, remember=True)
            session['auth_token'] = token.get('access_token', '')
            flash(f'Successfully logged in with {provider.title()}!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Account not active', 'error')
            
    except Exception as e:
        current_app.logger.error(f"OAuth error: {str(e)}")
        flash('Authentication failed', 'error')
    
    return redirect(url_for('auth.login'))

def get_user_info_from_provider(provider, token):
    """Get user info from OAuth provider"""
    try:
        if provider == 'google':
            resp = oauth.google.get('https://www.googleapis.com/oauth2/v2/userinfo', token=token)
            user_data = resp.json()
            return {
                'email': user_data.get('email'),
                'first_name': user_data.get('given_name', ''),
                'last_name': user_data.get('family_name', ''),
                'provider_user_id': str(user_data.get('id')),
                'email_verified': user_data.get('verified_email', False)
            }
        
        elif provider == 'github':
            # Get user profile
            user_resp = oauth.github.get('user', token=token)
            user_data = user_resp.json()
            
            # Get emails
            emails_resp = oauth.github.get('user/emails', token=token)
            emails = emails_resp.json()
            
            primary_email = next((e['email'] for e in emails if e['primary']), None)
            email_verified = next((e['verified'] for e in emails if e['primary']), False)
            
            # Split name
            full_name = user_data.get('name', '').split(' ', 1)
            first_name = full_name[0] if full_name else ''
            last_name = full_name[1] if len(full_name) > 1 else ''
            
            return {
                'email': primary_email,
                'first_name': first_name,
                'last_name': last_name,
                'provider_user_id': str(user_data.get('id')),
                'email_verified': email_verified
            }
        
        elif provider == 'azure':
            resp = oauth.azure.get('https://graph.microsoft.com/v1.0/me', token=token)
            user_data = resp.json()
            
            return {
                'email': user_data.get('mail') or user_data.get('userPrincipalName'),
                'first_name': user_data.get('givenName', ''),
                'last_name': user_data.get('surname', ''),
                'provider_user_id': user_data.get('id'),
                'email_verified': True
            }
    
    except Exception as e:
        current_app.logger.error(f"Error getting user info: {str(e)}")
        return None

def find_or_create_oauth_user(user_info, provider, token):
    """Find or create user from OAuth"""
    email = user_info['email']
    provider_user_id = user_info['provider_user_id']
    
    # Check for existing OAuth account
    oauth_account = UserOAuthAccount.query.filter_by(
        provider_name=provider,
        provider_user_id=provider_user_id
    ).first()
    
    if oauth_account:
        # Update token
        oauth_account.access_token = token.get('access_token', '')
        oauth_account.provider_data = user_info
        db.session.commit()
        return oauth_account.user
    
    # Check for existing user by email
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Create new user
        username = generate_username(email, user_info['first_name'], user_info['last_name'])
        
        user = User(
            username=username,
            email=email,
            first_name=user_info['first_name'],
            last_name=user_info['last_name'],
            email_verified=user_info.get('email_verified', False),
            is_active=True
        )
        
        # Assign default role
        default_role = Role.query.filter_by(name='viewer').first()
        if default_role:
            user.roles.append(default_role)
        
        db.session.add(user)
        db.session.flush()
    
    # Create OAuth account
    oauth_account = UserOAuthAccount(
        user_id=user.user_id,
        provider_name=provider,
        provider_user_id=provider_user_id,
        access_token=token.get('access_token', ''),
        provider_data=user_info
    )
    
    db.session.add(oauth_account)
    db.session.commit()
    
    return user

def generate_username(email, first_name, last_name):
    """Generate unique username"""
    base = email.split('@')[0]
    username = base
    counter = 1
    
    while User.query.filter_by(username=username).first():
        if counter == 1:
            username = f"{first_name.lower()}.{last_name.lower()}"
        else:
            username = f"{base}{counter}"
        counter += 1
    
    return username[:50]

@bp.route('/logout')
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))