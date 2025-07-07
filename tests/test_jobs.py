import os
import pytest
from unittest.mock import patch

from app import create_app, db
from app.models import SyncLog
from app import jobs

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


def test_nightly_sync_logs_success(app_ctx, monkeypatch):
    monkeypatch.setattr(jobs.nba_service, 'NBAAPIClient', lambda: None)
    monkeypatch.setattr(jobs.nba_service, 'sync_teams', lambda client: None)
    monkeypatch.setattr(jobs.nba_service, 'sync_games', lambda *a, **k: None)
    monkeypatch.setattr(jobs.nhl_service, 'NHLAPIClient', lambda: None)
    monkeypatch.setattr(jobs.nhl_service, 'sync_teams', lambda client: None)
    monkeypatch.setattr(jobs.nhl_service, 'sync_games', lambda *a, **k: None)

    jobs.nightly_sync_games()
    log = SyncLog.query.filter_by(job_name='nightly_sync_games').first()
    assert log and log.success

def test_nightly_sync_logs_failure(app_ctx, monkeypatch):
    def raise_err(*args, **kwargs):
        raise RuntimeError('fail')
    monkeypatch.setattr(jobs.nba_service, 'NBAAPIClient', lambda: None)
    monkeypatch.setattr(jobs.nba_service, 'sync_teams', raise_err)

    jobs.nightly_sync_games()
    log = SyncLog.query.filter_by(job_name='nightly_sync_games').order_by(SyncLog.log_id.desc()).first()
    assert log and not log.success
