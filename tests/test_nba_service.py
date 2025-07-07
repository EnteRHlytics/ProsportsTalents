import os
import sys
from datetime import date
from unittest.mock import patch
import requests

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import NBATeam, NBAGame
from app.services import nba_service


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
        'data': [
            {
                'id': 1,
                'abbreviation': 'LAL',
                'city': 'Los Angeles',
                'conference': 'West',
                'division': 'Pacific',
                'full_name': 'Los Angeles Lakers',
                'name': 'Lakers',
            }
        ]
    }
    client = nba_service.NBAAPIClient()
    with patch.object(client, '_get', return_value=sample):
        teams = nba_service.sync_teams(client)
    assert NBATeam.query.count() == 1
    assert teams[0]['id'] == 1


def test_sync_games(app_ctx):
    # create teams to satisfy FKs
    team1 = NBATeam(team_id=1, name='Lakers')
    team2 = NBATeam(team_id=2, name='Heat')
    db.session.add_all([team1, team2])
    db.session.commit()

    sample_games = {
        'data': [
            {
                'id': 10,
                'date': '2024-01-01T00:00:00Z',
                'season': 2024,
                'home_team': {'id': 1},
                'visitor_team': {'id': 2},
                'home_team_score': 100,
                'visitor_team_score': 90,
            }
        ]
    }
    client = nba_service.NBAAPIClient()
    with patch.object(client, '_get', return_value=sample_games):
        games = nba_service.sync_games(client, team_id=1, season=2024)
    assert NBAGame.query.count() == 1
    assert games[0]['id'] == 10


def test_get_handles_request_errors(monkeypatch):
    client = nba_service.NBAAPIClient()
    def fail(*args, **kwargs):
        raise requests.RequestException("boom")
    monkeypatch.setattr(nba_service, "request_with_retry", fail)
    data = client._get("/bad")
    assert data == {}

def test_get_handles_bad_json(monkeypatch):
    client = nba_service.NBAAPIClient()

    class BadResp:
        def json(self):
            raise ValueError("bad")

    def fake(*args, **kwargs):
        return BadResp()

    monkeypatch.setattr(nba_service, "request_with_retry", fake)
    data = client._get("/bad-json")
    assert data == {}
