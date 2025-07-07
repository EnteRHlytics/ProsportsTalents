import os
import sys
import uuid
import json
from datetime import date
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import (
    User,
    AthleteProfile,
    AthleteStat,
    NBATeam,
    NBAGame,
    Sport,
    Position,
)


@pytest.fixture
def app_instance(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path / "test.db"}')
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def create_athlete():
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
        last_name='L'
    )
    user.save()
    athlete = AthleteProfile(
        user_id=user.user_id,
        primary_sport_id=sport.sport_id,
        primary_position_id=position.position_id,
        date_of_birth=date.fromisoformat('2000-01-01'),
        current_team='Lakers'
    )
    athlete.save()
    return athlete


def test_stats_summary(client, app_instance):
    with app_instance.app_context():
        athlete = create_athlete()
        s1 = AthleteStat(athlete_id=athlete.athlete_id, name='Points', value='20', season='2022')
        s2 = AthleteStat(athlete_id=athlete.athlete_id, name='Points', value='25', season='2023')
        db.session.add_all([s1, s2])
        db.session.commit()

    resp = client.get(f'/api/athletes/{athlete.athlete_id}/stats/summary')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['2022']['Points'] == '20'
    assert data['2023']['Points'] == '25'


def test_game_log(client, app_instance):
    with app_instance.app_context():
        athlete = create_athlete()
        team1 = NBATeam(team_id=1, abbreviation='LAL', city='Los Angeles', conference='West', division='Pacific', full_name='Los Angeles Lakers', name='Lakers')
        team2 = NBATeam(team_id=2, abbreviation='MIA', city='Miami', conference='East', division='East', full_name='Miami Heat', name='Heat')
        db.session.add_all([team1, team2])
        db.session.commit()
        g1 = NBAGame(game_id=1, date=date.fromisoformat('2024-01-03'), season=2024, home_team_id=1, visitor_team_id=2, home_team_score=100, visitor_team_score=90)
        g2 = NBAGame(game_id=2, date=date.fromisoformat('2024-01-05'), season=2024, home_team_id=2, visitor_team_id=1, home_team_score=95, visitor_team_score=99)
        g3 = NBAGame(game_id=3, date=date.fromisoformat('2024-01-07'), season=2024, home_team_id=1, visitor_team_id=2, home_team_score=110, visitor_team_score=105)
        db.session.add_all([g1, g2, g3])
        db.session.commit()

    resp = client.get(f'/api/athletes/{athlete.athlete_id}/game-log')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) == 3
    assert data[0]['game_id'] == 3
