import json
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import date
from app import create_app, db
from app.models import User, AthleteProfile
from app.models.oauth import UserOAuthAccount

@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


@pytest.fixture
def auth_headers(app_instance):
    with app_instance.app_context():
        user = User(username='authuser', email='auth@example.com', first_name='A', last_name='User')
        user.save()
        oauth = UserOAuthAccount(
            user_id=user.user_id,
            provider_name='test',
            provider_user_id='123',
            access_token='testtoken'
        )
        db.session.add(oauth)
        db.session.commit()
    return {'Authorization': 'Bearer testtoken'}


def test_get_athlete(client):
    user = User(username='u1', email='u1@example.com', first_name='U', last_name='One')
    user.save()
    athlete = AthleteProfile(user_id=user.user_id, date_of_birth=date.fromisoformat('2000-01-01'))
    athlete.save()

    resp = client.get(f'/api/athletes/{athlete.athlete_id}')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['athlete_id'] == athlete.athlete_id
    assert data['user']['full_name'] == user.full_name


def test_create_athlete_missing_field(client, auth_headers):
    resp = client.post('/api/athletes', json={}, headers=auth_headers)
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert 'error' in data or 'message' in data


def test_404_returns_json(client):
    resp = client.get('/api/athletes/nonexistent')
    assert resp.status_code == 404
    data = json.loads(resp.data)
    assert 'error' in data or 'message' in data



def test_create_athlete_requires_auth(client):
    resp = client.post('/api/athletes', json={})
    assert resp.status_code == 401

def _create_athlete():
    user = User(username='u_skill', email='skill@example.com', first_name='S', last_name='Kill')
    user.save()
    athlete = AthleteProfile(user_id=user.user_id, date_of_birth=date.fromisoformat('2000-01-01'))
    athlete.save()
    return athlete


def test_skill_crud(client):
    athlete = _create_athlete()

    resp = client.post(
        f'/api/athletes/{athlete.athlete_id}/skills',
        json={'name': 'Speed', 'level': 5}
    )
    assert resp.status_code == 201
    skill = json.loads(resp.data)

    resp = client.get(f'/api/athletes/{athlete.athlete_id}/skills')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) == 1

    resp = client.put(f"/api/skills/{skill['skill_id']}", json={'level': 7})
    assert resp.status_code == 200
    updated = json.loads(resp.data)
    assert updated['level'] == 7

    resp = client.delete(f"/api/skills/{skill['skill_id']}")
    assert resp.status_code == 204

    resp = client.get(f'/api/athletes/{athlete.athlete_id}/skills')
    data = json.loads(resp.data)
    assert data == []


def test_create_skill_missing_name(client):
    athlete = _create_athlete()
    resp = client.post(f'/api/athletes/{athlete.athlete_id}/skills', json={})
    assert resp.status_code == 400
