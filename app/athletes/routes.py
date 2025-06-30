from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required

from app import db
from app.models import AthleteProfile, User
from app.athletes import bp
from app.athletes.forms import AthleteForm

@bp.route('/')
@login_required
def index():
    athletes = AthleteProfile.query.filter_by(is_deleted=False).all()
    return render_template('athletes/list.html', athletes=athletes)

@bp.route('/<athlete_id>')
@login_required
def detail(athlete_id):
    athlete = (
        AthleteProfile.query.filter_by(athlete_id=athlete_id, is_deleted=False)
        .first_or_404()
    )
    return render_template('athletes/detail.html', athlete=athlete)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    form = AthleteForm()
    if form.validate_on_submit():
        user = User(first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    username=form.first_name.data.lower(),
                    email=f"{form.first_name.data.lower()}@example.com")
        db.session.add(user)
        db.session.flush()
        athlete = AthleteProfile(user_id=user.user_id,
                                 date_of_birth=form.date_of_birth.data,
                                 nationality=form.nationality.data)
        db.session.add(athlete)
        db.session.commit()
        flash('Athlete created.', 'success')
        return redirect(url_for('athletes.detail', athlete_id=athlete.athlete_id))
    return render_template('athletes/form.html', form=form)

@bp.route('/<athlete_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(athlete_id):
    athlete = (
        AthleteProfile.query.filter_by(athlete_id=athlete_id, is_deleted=False)
        .first_or_404()
    )
    form = AthleteForm(obj=athlete.user)
    if form.validate_on_submit():
        athlete.user.first_name = form.first_name.data
        athlete.user.last_name = form.last_name.data
        athlete.date_of_birth = form.date_of_birth.data
        athlete.nationality = form.nationality.data
        db.session.commit()
        flash('Athlete updated.', 'success')
        return redirect(url_for('athletes.detail', athlete_id=athlete_id))
    return render_template('athletes/form.html', form=form)
