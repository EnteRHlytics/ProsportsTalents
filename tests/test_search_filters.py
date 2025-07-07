import uuid
import json
from datetime import date
import pytest

from app import create_app, db
from app.models import User, AthleteProfile, Sport

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


def create_athlete(code, rating=50, contract=True):
    sport = Sport.query.filter_by(code=code).first()
    if not sport:
        sport = Sport(name=code, code=code)
        db.session.add(sport)
        db.session.commit()
    user = User(username=str(uuid.uuid4()), email=f'{uuid.uuid4()}@ex.com', first_name='F', last_name='L')
    user.save()
    athlete = AthleteProfile(
        user_id=user.user_id,
        primary_sport_id=sport.sport_id,
        date_of_birth=date.fromisoformat('2000-01-01'),
        overall_rating=rating,
        contract_active=contract,
    )
    athlete.save()
    return athlete


def test_filter_league(client, app_instance):
    with app_instance.app_context():
        a_nba = create_athlete('NBA')
        create_athlete('NFL')

    resp = client.get('/api/athletes/search?filter=nba')
    data = json.loads(resp.data)
    assert resp.status_code == 200
    assert data['count'] == 1
    assert data['results'][0]['athlete_id'] == a_nba.athlete_id


def test_filter_available(client, app_instance):
    with app_instance.app_context():
        create_athlete('NBA', contract=True)
        a_free = create_athlete('NBA', contract=False)

    resp = client.get('/api/athletes/search?filter=available')
    data = json.loads(resp.data)
    assert resp.status_code == 200
    assert data['count'] == 1
    assert data['results'][0]['athlete_id'] == a_free.athlete_id


def test_filter_top_limit(client, app_instance):
    with app_instance.app_context():
        for i in range(15):
            create_athlete('NBA', rating=99 - i)

    resp = client.get('/api/athletes/search?filter=top')
    data = json.loads(resp.data)
    assert resp.status_code == 200
    assert data['count'] == 10


def test_filter_and_search_combined(client, app_instance):
    """Filter tab should work together with text search."""
    with app_instance.app_context():
        a_nba = create_athlete('NBA')
        create_athlete('NFL')

    resp = client.get('/api/athletes/search?filter=nba&q=F')
    data = json.loads(resp.data)

    assert resp.status_code == 200
    assert data['count'] == 1
    assert data['results'][0]['athlete_id'] == a_nba.athlete_id

