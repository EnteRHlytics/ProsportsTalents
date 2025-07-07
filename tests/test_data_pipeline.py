import os
import sys
import uuid
from datetime import date

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db, jobs
from app.models import (
    NBATeam,
    NBAGame,
    NHLTeam,
    NHLGame,
    AthleteProfile,
    AthleteStat,
    Sport,
    User,
    SyncLog,
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
def app_ctx(app_instance):
    with app_instance.app_context():
        yield


def test_nightly_sync_full_cycle(app_ctx, monkeypatch):
    class DummyNBA:
        def get_teams(self):
            return [
                {
                    'id': 1,
                    'abbreviation': 'LAL',
                    'city': 'Los Angeles',
                    'conference': 'West',
                    'division': 'Pacific',
                    'full_name': 'Los Angeles Lakers',
                    'name': 'Lakers',
                },
                {
                    'id': 2,
                    'abbreviation': 'MIA',
                    'city': 'Miami',
                    'conference': 'East',
                    'division': 'East',
                    'full_name': 'Miami Heat',
                    'name': 'Heat',
                },
            ]

        def get_games(self, team_id, season=None):
            if team_id == 1:
                return [
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
            return [
                {
                    'id': 11,
                    'date': '2024-01-02T00:00:00Z',
                    'season': 2024,
                    'home_team': {'id': 2},
                    'visitor_team': {'id': 1},
                    'home_team_score': 90,
                    'visitor_team_score': 95,
                }
            ]

    class DummyNHL:
        def get_teams(self):
            return [
                {
                    'id': 1,
                    'name': 'Devils',
                    'abbreviation': 'NJD',
                    'locationName': 'New Jersey',
                    'division': {'name': 'Metro'},
                    'conference': {'name': 'East'},
                },
                {
                    'id': 2,
                    'name': 'Rangers',
                    'abbreviation': 'NYR',
                    'locationName': 'New York',
                    'division': {'name': 'Metro'},
                    'conference': {'name': 'East'},
                },
            ]

        def get_games(self, team_id, season=None):
            if team_id == 1:
                return [
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
            return [
                {
                    'gamePk': 100,
                    'gameDate': '2024-01-02T00:00:00Z',
                    'season': '20242025',
                    'teams': {
                        'home': {'team': {'id': 2}, 'score': 2},
                        'away': {'team': {'id': 1}, 'score': 1},
                    },
                }
            ]

    monkeypatch.setattr(jobs.nba_service, 'NBAAPIClient', lambda: DummyNBA())
    monkeypatch.setattr(jobs.nhl_service, 'NHLAPIClient', lambda: DummyNHL())

    jobs.nightly_sync_games()

    assert NBATeam.query.count() == 2
    assert NBAGame.query.count() == 2
    assert NHLTeam.query.count() == 2
    assert NHLGame.query.count() == 2
    log = SyncLog.query.filter_by(job_name='nightly_sync_games').first()
    assert log and log.success


def test_weekly_stats_sync_full_cycle(app_ctx, monkeypatch):
    # create sports
    nba = Sport(name='Basketball', code='NBA')
    nfl = Sport(name='Football', code='NFL')
    mlb = Sport(name='Baseball', code='MLB')
    nhl = Sport(name='Hockey', code='NHL')
    db.session.add_all([nba, nfl, mlb, nhl])
    db.session.commit()

    def make_athlete(sport, attr, pid):
        user = User(
            username=str(uuid.uuid4()),
            email=f'{uuid.uuid4()}@example.com',
            first_name='F',
            last_name='L',
        )
        user.save()
        athlete = AthleteProfile(
            user_id=user.user_id,
            primary_sport_id=sport.sport_id,
            date_of_birth=date.fromisoformat('2000-01-01'),
        )
        setattr(athlete, attr, pid)
        athlete.save()
        return athlete

    a_nba = make_athlete(nba, 'nba_player_id', 23)
    a_nfl = make_athlete(nfl, 'nfl_player_id', 12)
    a_mlb = make_athlete(mlb, 'mlb_player_id', 99)
    a_nhl = make_athlete(nhl, 'nhl_player_id', 88)

    class NBAClient:
        def get_player_season_avg(self, *a, **k):
            return {'season': 2024, 'pts': 20, 'reb': 5, 'ast': 7}

    class NFLClient:
        def get_player_stats(self, pid, season=None, group='offense'):
            if group == 'offense':
                return {'passingYards': 3000}
            return {'tackles': 40}

    class MLBClient:
        def get_player_stats(self, pid, season=None, group='hitting'):
            if group == 'hitting':
                return {'avg': '.300'}
            if group == 'pitching':
                return {'era': '3.10'}
            return {'fielding': '0.990'}

    class NHLClient:
        def get_player_stats(self, *a, **k):
            return {'goals': 30, 'assists': 40, 'points': 70}

    monkeypatch.setattr(jobs.nba_service, 'NBAAPIClient', lambda: NBAClient())
    monkeypatch.setattr(jobs.nfl_service, 'NFLAPIClient', lambda: NFLClient())
    monkeypatch.setattr(jobs.mlb_service, 'MLBAPIClient', lambda: MLBClient())
    monkeypatch.setattr(jobs.nhl_service, 'NHLAPIClient', lambda: NHLClient())

    jobs.weekly_sync_player_stats()

    assert AthleteStat.query.filter_by(athlete_id=a_nba.athlete_id).count() == 3
    assert AthleteStat.query.filter_by(athlete_id=a_nfl.athlete_id).count() >= 2
    assert AthleteStat.query.filter_by(athlete_id=a_mlb.athlete_id).count() >= 3
    assert AthleteStat.query.filter_by(athlete_id=a_nhl.athlete_id).count() >= 3
    log = SyncLog.query.filter_by(job_name='weekly_sync_player_stats').first()
    assert log and log.success
