from functools import wraps
from flask import request, abort, session, redirect, url_for, flash
from flask_login import current_user, login_user
from app.models.oauth import UserOAuthAccount


def login_or_token_required(fn):
    """Allow access if session is authenticated or a valid bearer token is provided."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Session based
        if current_user.is_authenticated:
            return fn(*args, **kwargs)

        # Token based
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.lower().startswith('bearer '):
            token = auth_header.split(' ', 1)[1]
            account = UserOAuthAccount.query.filter_by(access_token=token).first()
            if account and account.user and account.user.is_active:
                login_user(account.user, remember=False)
                return fn(*args, **kwargs)

        abort(401)

    return wrapper


def oauth_session_required(fn):
    """Require an authenticated user with an OAuth session token."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not session.get('auth_token'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return fn(*args, **kwargs)

    return wrapper

