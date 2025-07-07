import os
import sys
import time
from datetime import date

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, AthleteProfile, AthleteStat


@pytest.fixture
def app_instance(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path / "perf.db"}')
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_athlete_stats_query_speed(app_instance):
    with app_instance.app_context():
        user = User(username='perf', email='perf@example.com', first_name='P', last_name='T')
        user.save()
        athlete = AthleteProfile(user_id=user.user_id, date_of_birth=date.fromisoformat('2000-01-01'))
        athlete.save()

        # populate multiple seasons
        for season in ['2023', '2024']:
            for i in range(500):
                stat = AthleteStat(
                    athlete_id=athlete.athlete_id,
                    name='points',
                    value=str(i),
                    season=season,
                )
                db.session.add(stat)
        db.session.commit()

        start = time.perf_counter()
        stats = AthleteStat.query.filter_by(athlete_id=athlete.athlete_id, season='2024').all()
        duration = time.perf_counter() - start

        assert len(stats) == 500
        assert duration < 0.1
