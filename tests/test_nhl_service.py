import os
import sys
from datetime import date
from unittest.mock import patch
import requests

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import NHLTeam, NHLGame, AthleteProfile
from app.services import nhl_service


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
                'name': 'Devils',
                'abbreviation': 'NJD',
                'locationName': 'New Jersey',
                'division': {'name': 'Metro'},
                'conference': {'name': 'East'},
            }
        ]
    }
    client = nhl_service.NHLAPIClient()
    with patch.object(client, '_get', return_value=sample):
        teams = nhl_service.sync_teams(client)
    assert NHLTeam.query.count() == 1
    assert teams[0]['id'] == 1


def test_sync_standings(app_ctx):
    team = NHLTeam(team_id=1, name='Devils')
    db.session.add(team)
    db.session.commit()
    records = {
        'records': [
            {
                'teamRecords': [
                    {
                        'team': {'id': 1},
                        'leagueRecord': {'wins': 10, 'losses': 5, 'ot': 2},
                        'points': 22,
                    }
                ]
            }
        ]
    }
    client = nhl_service.NHLAPIClient()
    with patch.object(client, '_get', return_value=records):
        nhl_service.sync_standings(client)
    team = NHLTeam.query.get(1)
    assert team.wins == 10
    assert team.points == 22


def test_sync_games(app_ctx):
    home = NHLTeam(team_id=1, name='Devils')
    away = NHLTeam(team_id=2, name='Rangers')
    db.session.add_all([home, away])
    db.session.commit()
    games_data = {
        'dates': [
            {
                'games': [
                    {
                        'gamePk': 99,
                        'gameDate': '2024-01-01T00:00:00Z',
                        'season': '20242025',
                        'teams': {
                            'home': {'team': {'id': 1}, 'score': 3},
                            'away': {'team': {'id': 2}, 'score': 2},
                        },
                    }
                ]
            }
        ]
    }
    client = nhl_service.NHLAPIClient()
    with patch.object(client, '_get', return_value=games_data):
        games = nhl_service.sync_games(client, team_id=1, season='20242025')
    assert NHLGame.query.count() == 1
    assert games[0]['gamePk'] == 99


def test_sync_player_stats(app_ctx):
    athlete = AthleteProfile(user_id='u1', date_of_birth=date.fromisoformat('2000-01-01'))
    setattr(athlete, 'nhl_player_id', 88)
    db.session.add(athlete)
    db.session.commit()

    stats = {'goals': 30, 'assists': 40, 'points': 70}
    client = nhl_service.NHLAPIClient()
    with patch.object(client, 'get_player_stats', return_value=stats):
        nhl_service.sync_player_stats(client, athlete, season='20242025')

    stored = {s.name: s for s in athlete.stats}
    assert stored['Goals'].value == '30'
    assert stored['Assists'].value == '40'
    assert stored['Points'].value == '70'



def test_get_handles_request_errors(monkeypatch):
    client = nhl_service.NHLAPIClient()

    def fail(*args, **kwargs):
        raise requests.RequestException("boom")

    monkeypatch.setattr(nhl_service, "request_with_retry", fail)
    data = client._get("/bad")
    assert data == {}


def test_get_handles_bad_json(monkeypatch):
    client = nhl_service.NHLAPIClient()

    class BadResp:
        def json(self):
            raise ValueError("bad")

    monkeypatch.setattr(nhl_service, "request_with_retry", lambda *a, **k: BadResp())
    data = client._get("/bad-json")
    assert data == {}
