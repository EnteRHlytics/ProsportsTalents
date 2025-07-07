from datetime import date

import pytest

from app import create_app, db, jobs
from app.models import Sport, User, AthleteProfile, AthleteStat, NBATeam, SyncLog


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


def test_historical_backfill(app_ctx, monkeypatch):
    # Setup minimal sport and athlete
    sport = Sport(name='Basketball', code='NBA')
    db.session.add(sport)
    db.session.commit()

    user = User(username='u1', email='u1@example.com', first_name='f', last_name='l')
    user.save()
    athlete = AthleteProfile(
        user_id=user.user_id,
        primary_sport_id=sport.sport_id,
        date_of_birth=date.fromisoformat('2000-01-01'),
    )
    athlete.nba_player_id = 23
    athlete.save()

    # Create team so sync_games loop has an entry
    team = NBATeam(team_id=1, name='Lakers')
    db.session.add(team)
    db.session.commit()

    # Dummy services
    class DummyNBA:
        def get_teams(self):
            return []

        def get_games(self, team_id, season=None):
            return []

        def get_player_season_avg(self, player_id, season=None):
            return {'season': season, 'pts': 10, 'reb': 3, 'ast': 4}

    monkeypatch.setattr(jobs.nba_service, 'NBAAPIClient', lambda: DummyNBA())
    monkeypatch.setattr(jobs.nba_service, 'sync_teams', lambda client: None)
    monkeypatch.setattr(jobs.nba_service, 'sync_games', lambda *a, **k: None)

    jobs.historical_backfill_stats(seasons=[2023, 2024])

    stats = AthleteStat.query.filter_by(athlete_id=athlete.athlete_id).all()
    seasons = sorted([s.season for s in stats])
    assert seasons == ['2023', '2024']
    log = SyncLog.query.filter_by(job_name='historical_backfill_stats').first()
    assert log and log.success
