import os
import sys
from datetime import date
from unittest.mock import patch
import requests

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import NFLTeam, AthleteProfile
from app.services import nfl_service


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
    with app_instance.app_context():
        yield


def test_sync_teams(app_ctx):
    sample = {
        'teams': [
            {
                'id': 1,
                'name': 'Patriots',
                'abbreviation': 'NE',
                'city': 'New England',
                'conference': 'AFC',
                'division': 'East',
            }
        ]
    }
    client = nfl_service.NFLAPIClient()
    with patch.object(client, '_get', return_value=sample):
        teams = nfl_service.sync_teams(client)
    assert NFLTeam.query.count() == 1
    assert teams[0]['id'] == 1


def test_sync_player_stats(app_ctx):
    athlete = AthleteProfile(user_id='u1', date_of_birth=date.fromisoformat('2000-01-01'))
    setattr(athlete, 'nfl_player_id', 12)
    db.session.add(athlete)
    db.session.commit()

    offense = {'passingYards': 4000}
    defense = {'tackles': 80}

    client = nfl_service.NFLAPIClient()
    with patch.object(client, 'get_player_stats', side_effect=[offense, defense]):
        nfl_service.sync_player_stats(client, athlete, season=2024)

    stats = {s.name: s for s in athlete.stats}
    assert stats['PassingYards'].value == '4000'
    assert stats['Tackles'].value == '80'


def test_get_handles_request_errors(monkeypatch):
    client = nfl_service.NFLAPIClient()

    def fail(*args, **kwargs):
        raise requests.RequestException("boom")

    monkeypatch.setattr(nfl_service, "request_with_retry", fail)
    data = client._get("/bad")
    assert data == {}


def test_get_handles_bad_json(monkeypatch):
    client = nfl_service.NFLAPIClient()

    class BadResp:
        def json(self):
            raise ValueError("bad")

    monkeypatch.setattr(nfl_service, "request_with_retry", lambda *a, **k: BadResp())
    data = client._get("/bad-json")
    assert data == {}
