import json
import os
import sys
import uuid
from datetime import date
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, AthleteProfile, AthleteStat, Sport


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
def client(app_instance):
    return app_instance.test_client()


def _create_athlete(sport_code, stat_value):
    sport = Sport.query.filter_by(code=sport_code).first()
    if not sport:
        sport = Sport(name=sport_code, code=sport_code)
        db.session.add(sport)
        db.session.commit()

    user = User(
        username=str(uuid.uuid4()),
        email=f"{uuid.uuid4()}@example.com",
        first_name="F",
        last_name="L",
    )
    user.save()

    athlete = AthleteProfile(
        user_id=user.user_id,
        primary_sport_id=sport.sport_id,
        date_of_birth=date.fromisoformat("2000-01-01"),
    )
    athlete.save()

    stat_name = {
        "NBA": "PointsPerGame",
        "NHL": "Points",
    }[sport_code]

    stat = AthleteStat(
        athlete_id=athlete.athlete_id,
        name=stat_name,
        value=str(stat_value),
        season="2024",
    )
    db.session.add(stat)
    db.session.commit()
    return athlete


def test_top_rankings_dynamic(client, app_instance):
    with app_instance.app_context():
        a1 = _create_athlete("NBA", 30)
        a2 = _create_athlete("NBA", 20)
        a3 = _create_athlete("NHL", 50)
        top_name = a1.user.full_name

    resp = client.get("/api/rankings/top")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) == 3
    assert data[0]["name"] == top_name
    assert data[0]["id"]
    scores = [r["score"] for r in data]
    assert scores == sorted(scores, reverse=True)
