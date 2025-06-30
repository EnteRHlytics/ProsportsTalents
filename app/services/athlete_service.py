from app import db
from app.models import AthleteProfile
from app.utils.pagination import paginate_query


def create_athlete(data):
    """Create a new athlete profile from provided data."""
    athlete = AthleteProfile(
        user_id=data.get('user_id'),
        primary_sport_id=data.get('primary_sport_id'),
        primary_position_id=data.get('primary_position_id'),
        date_of_birth=data.get('date_of_birth'),
    )
    db.session.add(athlete)
    db.session.commit()
    return athlete


def get_athlete(athlete_id):
    """Retrieve an athlete profile by id or raise 404."""
    return (
        AthleteProfile.query.filter_by(athlete_id=athlete_id, is_deleted=False)
        .first_or_404()
    )


def update_athlete(athlete_id, data):
    """Update an existing athlete profile."""
    athlete = (
        AthleteProfile.query.filter_by(athlete_id=athlete_id, is_deleted=False)
        .first_or_404()
    )
    for field in ['primary_sport_id', 'primary_position_id', 'bio']:
        if field in data:
            setattr(athlete, field, data[field])
    db.session.commit()
    return athlete


def delete_athlete(athlete_id):
    """Soft delete an athlete profile."""
    athlete = (
        AthleteProfile.query.filter_by(athlete_id=athlete_id, is_deleted=False)
        .first_or_404()
    )
    athlete.is_deleted = True
    db.session.commit()
    return True


def list_athletes(page=1, per_page=10):
    """Return a pagination object of non-deleted athletes."""
    query = AthleteProfile.query.filter_by(is_deleted=False)
    return paginate_query(query, page=page, per_page=per_page)
