import os
import sys
from datetime import date
from unittest.mock import patch
import requests

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import MLBTeam, AthleteProfile
from app.services import mlb_service


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
                'name': 'Yankees',
                'abbreviation': 'NYY',
                'locationName': 'New York',
                'league': {'name': 'AL'},
                'division': {'name': 'East'},
            }
        ]
    }
    client = mlb_service.MLBAPIClient()
    with patch.object(client, '_get', return_value=sample):
        teams = mlb_service.sync_teams(client)
    assert MLBTeam.query.count() == 1
    assert teams[0]['id'] == 1


def test_sync_player_stats(app_ctx):
    athlete = AthleteProfile(user_id='u1', date_of_birth=date.fromisoformat('2000-01-01'))
    setattr(athlete, 'mlb_player_id', 99)
    db.session.add(athlete)
    db.session.commit()

    hitting = {'avg': '.300'}
    pitching = {'era': '3.20'}
    fielding = {'fielding': '0.990'}

    client = mlb_service.MLBAPIClient()
    with patch.object(client, 'get_player_stats', side_effect=[hitting, pitching, fielding]):
        mlb_service.sync_player_stats(client, athlete, season=2024)

    stats = {s.name: s for s in athlete.stats}
    assert stats['BattingAverage'].value == '.300'
    assert stats['EarnedRunAverage'].value == '3.20'
    assert stats['FieldingPercentage'].value == '0.990'


def test_get_handles_request_errors(monkeypatch):
    client = mlb_service.MLBAPIClient()

    def fail(*args, **kwargs):
        raise requests.RequestException("boom")

    monkeypatch.setattr(mlb_service, "request_with_retry", fail)
    data = client._get("/bad")
    assert data == {}


def test_get_handles_bad_json(monkeypatch):
    client = mlb_service.MLBAPIClient()

    class BadResp:
        def json(self):
            raise ValueError("bad")

    monkeypatch.setattr(mlb_service, "request_with_retry", lambda *a, **k: BadResp())
    data = client._get("/bad-json")
    assert data == {}
