from flask import render_template, request, current_app, redirect, url_for, flash
from flask_login import current_user
from sqlalchemy import func
from datetime import datetime, timedelta, date
from app import db
from app.models import AthleteProfile, AthleteStat, AthleteMedia, User, Sport, Position
from app.services.media_service import MediaService
from app.api.rankings import _dynamic_rankings, _load_rankings
from app.utils.auth import oauth_session_required
from app.main import bp


def _format_stat_value(value):
    """Return a formatted string for numeric stats."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    if 0 < num < 1:
        return f"{num:.3f}".lstrip("0")
    return f"{num:.1f}" if num % 1 else str(int(num))


def _collect_featured_stats(athlete, year):
    """Gather three key stats for display based on the athlete's sport."""
    sport = athlete.primary_sport.code if athlete.primary_sport else None
    mapping = {}
    if sport == "NBA":
        mapping = {
            "PPG": "PointsPerGame",
            "RPG": "ReboundsPerGame",
            "APG": "AssistsPerGame",
        }
    elif sport == "NFL":
        mapping = {
            "PassingYards": "PassingYards",
            "Touchdowns": "Touchdowns",
            "QBRating": "QBRating",
        }
    elif sport == "MLB":
        mapping = {
            "AVG": "BattingAverage",
            "HR": "HomeRuns",
            "RBI": "RunsBattedIn",
        }
    elif sport == "NHL":
        mapping = {"Goals": "Goals", "Assists": "Assists", "Points": "Points"}

    stats = []
    for label, name in mapping.items():
        stat = AthleteStat.query.filter_by(
            athlete_id=athlete.athlete_id, name=name, season=str(year)
        ).first()
        value = stat.value if stat else "N/A"
        stats.append({"label": label, "value": _format_stat_value(value)})
    return stats

@bp.route('/')
def index():
    """Home page"""
    user_name = current_user.full_name if current_user.is_authenticated else None
    search_query = request.args.get('q', '')
    active_filter = request.args.get('filter', '')
    return render_template(
        'main/index.html',
        user_name=user_name,
        search_query=search_query,
        active_filter=active_filter,
    )

@bp.route('/dashboard')
@oauth_session_required
def dashboard():
    """User dashboard"""
    user_name = current_user.full_name
    total_athletes = (
        db.session.query(func.count(AthleteProfile.athlete_id))
        .filter(AthleteProfile.is_deleted.is_(False))
        .scalar()
        or 0
    )
    active_contracts = (
        db.session.query(func.count(AthleteProfile.athlete_id))
        .filter(
            AthleteProfile.is_deleted.is_(False),
            AthleteProfile.contract_active.is_(True),
        )
        .scalar()
        or 0
    )
    new_this_week = (
        db.session.query(func.count(AthleteProfile.athlete_id))
        .filter(
            AthleteProfile.is_deleted.is_(False),
            AthleteProfile.created_at >= datetime.utcnow() - timedelta(days=7),
        )
        .scalar()
        or 0
    )

    year = date.today().year
    featured_profiles = (
        AthleteProfile.query.filter_by(is_deleted=False, is_featured=True)
        .join(User)
        .outerjoin(Sport)
        .outerjoin(Position)
        .order_by(AthleteProfile.overall_rating.desc())
        .limit(4)
        .all()
    )
    featured_athletes = []
    for ath in featured_profiles:
        name = ath.user.full_name if ath.user else ath.athlete_id
        initials = "".join([n[0] for n in name.split()][:2]).upper()
        featured_athletes.append(
            {
                "name": name,
                "position": ath.primary_position.code if ath.primary_position else None,
                "team": ath.current_team or "N/A",
                "sport": ath.primary_sport.code if ath.primary_sport else None,
                "profile_image_url": ath.profile_image_url,
                "initials": initials,
                "stats": _collect_featured_stats(ath, year),
            }
        )

    raw_satisfaction = current_app.config.get('CLIENT_SATISFACTION_PERCENT', 98.7)
    try:
        satisfaction_value = float(raw_satisfaction)
    except (TypeError, ValueError):
        satisfaction_value = 0.0
    if satisfaction_value <= 1.0:
        satisfaction_value *= 100
    client_satisfaction = f"{satisfaction_value:.1f}"

    rankings = _dynamic_rankings(limit=5)
    if rankings is None:
        rankings = _load_rankings()[:5]

    return render_template(
        'main/dashboard.html',
        user_name=user_name,
        total_athletes=total_athletes,
        active_contracts=active_contracts,
        new_this_week=new_this_week,
        client_satisfaction=client_satisfaction,
        featured_athletes=featured_athletes,
        top_rankings=rankings,
    )


@bp.route('/analytics')
@oauth_session_required
def analytics():
    """Analytics page placeholder."""
    return render_template('main/analytics.html')


@bp.route('/media/upload', methods=['GET', 'POST'])
@oauth_session_required
def upload_media():
    """Upload media for an athlete."""
    athletes = (
        AthleteProfile.query.filter_by(is_deleted=False)
        .join(User)
        .order_by(User.last_name)
        .all()
    )
    if request.method == 'POST':
        athlete_id = request.form.get('athlete_id')
        file = request.files.get('file')
        if not athlete_id or not file:
            flash('Select an athlete and choose a file.', 'error')
        else:
            media_type = request.form.get('media_type', 'other')
            path, _ = MediaService.save_file(file, athlete_id, media_type)
            media = AthleteMedia(
                athlete_id=athlete_id,
                media_type=media_type,
                file_path=path,
                original_filename=file.filename,
            )
            db.session.add(media)
            db.session.commit()
            flash('Media uploaded successfully.', 'success')
            return redirect(url_for('athletes.detail', athlete_id=athlete_id))
    return render_template('main/upload_media.html', athletes=athletes)


@bp.route('/rankings')
def rankings():
    """Display the full rankings placeholder page."""
    # NOTE: This is a temporary page until the comprehensive
    # ranking algorithm is implemented in Phase 4.
    from app.api.rankings import _dynamic_rankings, _load_rankings

    rankings = _dynamic_rankings(limit=10)
    if rankings is None:
        rankings = _load_rankings()

    return render_template('main/rankings.html', top_rankings=rankings)
