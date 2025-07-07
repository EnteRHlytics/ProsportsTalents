import os
import sys
import uuid
from datetime import date

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import (
    User,
    AthleteProfile,
    Sport,
    Position,
    Team,
    SeasonStat,
    NBAGame,
)


@pytest.fixture
def app_instance(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path / "constraints.db"}')
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _create_athlete():
    sport = Sport(name='Basketball', code='NBA')
    db.session.add(sport)
    db.session.commit()
    position = Position(sport_id=sport.sport_id, name='Guard', code='G')
    db.session.add(position)
    db.session.commit()
    user = User(
        username=str(uuid.uuid4()),
        email=f'{uuid.uuid4()}@example.com',
        first_name='F',
        last_name='L',
    )
    user.save()
    athlete = AthleteProfile(
        user_id=user.user_id,
        primary_sport_id=sport.sport_id,
        primary_position_id=position.position_id,
        date_of_birth=date.fromisoformat('2000-01-01'),
    )
    athlete.save()
    team = Team(team_id=1, sport_id=sport.sport_id, name='Lakers', abbreviation='LAL', city='LA')
    db.session.add(team)
    db.session.commit()
    return athlete, sport, team


def test_season_stats_unique_constraint(app_instance):
    with app_instance.app_context():
        athlete, sport, team = _create_athlete()
        s1 = SeasonStat(
            athlete_id=athlete.athlete_id,
            sport_id=sport.sport_id,
            team_id=team.team_id,
            season='2024',
            name='Points',
            value='100',
        )
        db.session.add(s1)
        db.session.commit()
        s2 = SeasonStat(
            athlete_id=athlete.athlete_id,
            sport_id=sport.sport_id,
            team_id=team.team_id,
            season='2024',
            name='Points',
            value='120',
        )
        db.session.add(s2)
        with pytest.raises(Exception):
            db.session.commit()


def test_game_score_check_constraint(app_instance):
    with app_instance.app_context():
        athlete, sport, team = _create_athlete()
        game = NBAGame(
            game_id=1,
            date=date.fromisoformat('2024-01-01'),
            season=2024,
            home_team_id=team.team_id,
            visitor_team_id=team.team_id,
            home_team_score=-1,
            visitor_team_score=90,
        )
        db.session.add(game)
        with pytest.raises(Exception):
            db.session.commit()

