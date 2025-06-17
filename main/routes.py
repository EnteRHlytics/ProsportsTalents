from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.main import bp

@bp.route('/')
def index():
    """Home page."""
    return render_template('main/index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard."""
    return render_template('main/dashboard.html')