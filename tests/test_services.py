import os
import io
import sys
import uuid
from datetime import date
import pytest
from werkzeug.datastructures import FileStorage

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, AthleteProfile
from app.services import athlete_service
from app.services.media_service import MediaService

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
def app_ctx(app_instance):
    """Provide an application context for service functions."""
    with app_instance.app_context():
        yield


def create_user():
    user = User(username=str(uuid.uuid4()), email=f'test@example.com', first_name='T', last_name='User')
    user.save()
    return user


def test_athlete_crud(app_ctx):
    user = create_user()
    data = {
        'user_id': user.user_id,
        'primary_sport_id': None,
        'primary_position_id': None,
        'date_of_birth': date.fromisoformat('2000-01-01')
    }
    athlete = athlete_service.create_athlete(data)
    assert athlete.user_id == user.user_id

    fetched = athlete_service.get_athlete(athlete.athlete_id)
    assert fetched.athlete_id == athlete.athlete_id

    updated = athlete_service.update_athlete(athlete.athlete_id, {'bio': 'New Bio'})
    assert updated.bio == 'New Bio'

    athlete_service.delete_athlete(athlete.athlete_id)
    assert AthleteProfile.query.get(athlete.athlete_id).is_deleted

    page = athlete_service.list_athletes()
    assert athlete not in page.items


def test_athlete_errors(app_ctx):
    bad_id = 'non-existent-id'
    with pytest.raises(Exception):
        athlete_service.get_athlete(bad_id)
    with pytest.raises(Exception):
        athlete_service.update_athlete(bad_id, {'bio': 'x'})
    with pytest.raises(Exception):
        athlete_service.delete_athlete(bad_id)


def test_media_service_file_ops(tmp_path, monkeypatch):
    monkeypatch.setattr(MediaService, 'BASE_DIR', str(tmp_path))
    data = io.BytesIO(b'content')
    fs = FileStorage(stream=data, filename='test.txt')
    path, fname = MediaService.save_file(fs, 'ath1', 'docs')
    assert os.path.exists(path)
    assert fname in path
    MediaService.delete_file(path)
    assert not os.path.exists(path)
    MediaService.delete_file(path)  # should not raise
