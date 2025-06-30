import json
import os
import io
import sys
import uuid
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import date
from app import create_app, db
from app.models import User, AthleteProfile, AthleteMedia, AthleteStat
from app.models.oauth import UserOAuthAccount
from app.services.media_service import MediaService


@pytest.fixture
def app_instance(tmp_path, monkeypatch):
    monkeypatch.setattr(MediaService, 'BASE_DIR', str(tmp_path))
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


def create_athlete():
    user = User(username=str(uuid.uuid4()), email=f'{uuid.uuid4()}@example.com', first_name='F', last_name='L')
    user.save()
    athlete = AthleteProfile(user_id=user.user_id, date_of_birth=date.fromisoformat('2000-01-01'))
    athlete.save()
    return athlete


def test_upload_and_delete_media(client, app_instance, auth_headers):
    athlete = create_athlete()

    data = {
        'file': (io.BytesIO(b'content'), 'test.txt'),
        'media_type': 'docs'
    }
    resp = client.post(
        f'/api/athletes/{athlete.athlete_id}/media',
        data=data,
        headers=auth_headers,
        content_type='multipart/form-data'
    )
    assert resp.status_code == 201
    media = json.loads(resp.data)

    with app_instance.app_context():
        record = AthleteMedia.query.get(media['media_id'])
        assert record is not None
        assert os.path.exists(record.file_path)

    resp = client.get(f'/api/athletes/{athlete.athlete_id}/media')
    assert resp.status_code == 200
    items = json.loads(resp.data)
    assert len(items) == 1

    resp = client.delete(f"/api/media/{media['media_id']}", headers=auth_headers)
    assert resp.status_code == 204

    with app_instance.app_context():
        assert AthleteMedia.query.get(media['media_id']) is None
        assert not os.path.exists(record.file_path)


def test_upload_media_missing_file(client, auth_headers):
    athlete = create_athlete()
    resp = client.post(f'/api/athletes/{athlete.athlete_id}/media', data={}, headers=auth_headers)
    assert resp.status_code == 400


def test_stats_crud(client, app_instance, auth_headers):
    athlete = create_athlete()

    payload = {'name': 'goals', 'value': '10', 'stat_type': 'season', 'season': '2023'}
    resp = client.post(
        f'/api/athletes/{athlete.athlete_id}/stats',
        json=payload,
        headers=auth_headers
    )
    assert resp.status_code == 200
    stat = json.loads(resp.data)

    with app_instance.app_context():
        record = AthleteStat.query.get(stat['stat_id'])
        assert record is not None
        assert record.value == '10'

    resp = client.get(f'/api/athletes/{athlete.athlete_id}/stats')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) == 1

    payload['value'] = '12'
    resp = client.post(
        f'/api/athletes/{athlete.athlete_id}/stats',
        json=payload,
        headers=auth_headers
    )
    assert resp.status_code == 200
    updated = json.loads(resp.data)
    assert updated['value'] == '12'

    resp = client.delete(f"/api/stats/{updated['stat_id']}", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get(f'/api/athletes/{athlete.athlete_id}/stats')
    assert json.loads(resp.data) == []


def test_add_stat_missing_name(client, auth_headers):
    athlete = create_athlete()
    resp = client.post(
        f'/api/athletes/{athlete.athlete_id}/stats',
        json={},
        headers=auth_headers
    )
    assert resp.status_code == 400
