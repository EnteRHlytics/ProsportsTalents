import json
from datetime import date

import pytest

from app import create_app, db
from app.models import User, AthleteProfile, Sport, Position, AthleteStat


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


def test_featured_format(client, app_instance):
    with app_instance.app_context():
        sport = Sport(name='Baseball', code='MLB')
        db.session.add(sport)
        db.session.commit()
        position = Position(sport_id=sport.sport_id, name='Pitcher', code='P')
        db.session.add(position)
        db.session.commit()
        user = User(username='u1', email='u1@example.com', first_name='Test', last_name='User')
        user.save()
        athlete = AthleteProfile(
            user_id=user.user_id,
            primary_sport_id=sport.sport_id,
            primary_position_id=position.position_id,
            current_team='Yankees',
            date_of_birth=date.fromisoformat('2000-01-01'),
            is_featured=True,
        )
        athlete.save()
        year = date.today().year
        db.session.add_all([
            AthleteStat(athlete_id=athlete.athlete_id, name='BattingAverage', value='0.283', season=str(year)),
            AthleteStat(athlete_id=athlete.athlete_id, name='HomeRuns', value='20', season=str(year)),
            AthleteStat(athlete_id=athlete.athlete_id, name='RunsBattedIn', value='85', season=str(year)),
        ])
        db.session.commit()

    resp = client.get('/api/athletes/featured')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) == 1
    item = data[0]
    assert item['name'] == user.full_name
    assert item['position'] == 'P'
    assert item['team'] == 'Yankees'
    assert item['sport'] == 'MLB'
    assert len(item['stats']) == 3
    assert item['stats'][0]['label'] == 'AVG'
    assert item['stats'][0]['value'] == '.283'
