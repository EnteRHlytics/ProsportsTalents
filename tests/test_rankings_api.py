import json
import os
import sys
import uuid
from datetime import date

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import AthleteProfile, AthleteStat, Sport, User


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


def _create_sport(code):
    sport = Sport.query.filter_by(code=code).first()
    if not sport:
        sport = Sport(name=code, code=code)
        db.session.add(sport)
        db.session.commit()
    return sport


def _create_athlete(sport_code, stat_value, *, extra_stats=None):
    sport = _create_sport(sport_code)

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
        "NFL": "PassingYards",
        "MLB": "BattingAverage",
    }[sport_code]

    db.session.add(AthleteStat(
        athlete_id=athlete.athlete_id,
        name=stat_name,
        value=str(stat_value),
        season="2024",
    ))
    for s in extra_stats or []:
        db.session.add(AthleteStat(
            athlete_id=athlete.athlete_id,
            name=s["name"],
            value=str(s["value"]),
            season=s.get("season", "2024"),
        ))
    db.session.commit()
    return athlete


def _create_user():
    user = User(
        username=str(uuid.uuid4()),
        email=f"{uuid.uuid4()}@example.com",
        first_name="Tester",
        last_name="User",
    )
    user.save()
    return user


# ---------------------------------------------------------------------------
# /api/rankings/top
# ---------------------------------------------------------------------------


def test_top_rankings_dynamic(client, app_instance):
    """The leaderboard returns the current athletes ordered by score."""
    with app_instance.app_context():
        a1 = _create_athlete("NBA", 30)
        _create_athlete("NBA", 20)
        _create_athlete("NHL", 50)
        top_name = a1.user.full_name

    resp = client.get("/api/rankings/top")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) == 3
    assert data[0]["name"] == top_name
    assert data[0]["id"]
    scores = [r["score"] for r in data]
    assert scores == sorted(scores, reverse=True)


def test_top_rankings_includes_components_and_rank(client, app_instance):
    with app_instance.app_context():
        _create_athlete("NBA", 28)

    resp = client.get("/api/rankings/top")
    assert resp.status_code == 200
    rows = json.loads(resp.data)
    assert rows
    row = rows[0]
    assert row["rank"] == 1
    assert "components" in row
    expected = {"performance", "efficiency", "durability", "fan_perception", "market_value"}
    assert expected.issubset(row["components"].keys())


def test_top_rankings_filters_by_sport(client, app_instance):
    with app_instance.app_context():
        _create_athlete("NBA", 25)
        _create_athlete("NBA", 15)
        _create_athlete("NHL", 70)

    resp = client.get("/api/rankings/top?sport=NHL")
    assert resp.status_code == 200
    rows = json.loads(resp.data)
    assert len(rows) == 1
    assert rows[0]["sport"] == "NHL"


def test_top_rankings_respects_limit(client, app_instance):
    with app_instance.app_context():
        for v in (10, 20, 30, 25, 5):
            _create_athlete("NBA", v)

    resp = client.get("/api/rankings/top?limit=2")
    assert resp.status_code == 200
    rows = json.loads(resp.data)
    assert len(rows) == 2


def test_top_rankings_empty_database(client):
    resp = client.get("/api/rankings/top")
    assert resp.status_code == 200
    assert json.loads(resp.data) == []


# ---------------------------------------------------------------------------
# /api/rankings/calculate
# ---------------------------------------------------------------------------


def test_calculate_rankings_with_query_weights(client, app_instance):
    with app_instance.app_context():
        # Two NBA athletes: scorer and iron-man.
        scorer = _create_athlete("NBA", 30, extra_stats=[
            {"name": "GamesPlayed", "value": 30},
        ])
        iron = _create_athlete("NBA", 12, extra_stats=[
            {"name": "GamesPlayed", "value": 82},
        ])
        scorer_name = scorer.user.full_name
        iron_name = iron.user.full_name

    perf = client.get("/api/rankings/calculate?weights=performance%3D1.0")
    assert perf.status_code == 200
    perf_body = json.loads(perf.data)
    assert perf_body["weights"]["performance"] == pytest.approx(1.0, abs=1e-6)
    assert perf_body["results"][0]["name"] == scorer_name

    dur = client.get("/api/rankings/calculate?weights=durability%3D1.0")
    dur_body = json.loads(dur.data)
    assert dur_body["results"][0]["name"] == iron_name


def test_calculate_rankings_post_with_json_body(client, app_instance):
    with app_instance.app_context():
        _create_athlete("NBA", 28)

    resp = client.post(
        "/api/rankings/calculate",
        json={
            "sport": "NBA",
            "limit": 5,
            "weights": {"performance": 0.8, "efficiency": 0.2},
        },
    )
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert pytest.approx(sum(body["weights"].values()), abs=1e-6) == 1.0
    assert body["weights"]["performance"] == pytest.approx(0.8, abs=1e-6)
    assert body["results"]


# ---------------------------------------------------------------------------
# /api/rankings/presets (auth-gated)
# ---------------------------------------------------------------------------


def _login(client, app_instance, user):
    """Manually set the Flask-Login session cookie."""
    with client.session_transaction() as sess:
        sess["_user_id"] = user.user_id
        sess["_fresh"] = True


def test_presets_requires_login(client):
    resp = client.get("/api/rankings/presets")
    assert resp.status_code == 401


def test_create_and_list_presets(client, app_instance):
    with app_instance.app_context():
        user = _create_user()
        _create_sport("NBA")

    _login(client, app_instance, user)

    create = client.post(
        "/api/rankings/presets",
        json={
            "name": "Scoring focus",
            "sport": "NBA",
            "weights": {"performance": 0.7, "efficiency": 0.3},
            "is_default": True,
        },
    )
    assert create.status_code == 201
    body = json.loads(create.data)
    assert body["name"] == "Scoring focus"
    assert body["is_default"] is True
    assert pytest.approx(sum(body["weights"].values()), abs=1e-6) == 1.0
    preset_id = body["id"]

    listed = client.get("/api/rankings/presets")
    assert listed.status_code == 200
    rows = json.loads(listed.data)
    assert any(r["id"] == preset_id for r in rows)


def test_create_preset_validates_payload(client, app_instance):
    with app_instance.app_context():
        user = _create_user()
    _login(client, app_instance, user)

    no_name = client.post(
        "/api/rankings/presets",
        json={"weights": {"performance": 1}},
    )
    assert no_name.status_code == 400

    no_weights = client.post(
        "/api/rankings/presets",
        json={"name": "X"},
    )
    assert no_weights.status_code == 400


def test_delete_preset(client, app_instance):
    with app_instance.app_context():
        user = _create_user()
    _login(client, app_instance, user)

    create = client.post(
        "/api/rankings/presets",
        json={"name": "Tmp", "weights": {"performance": 1}},
    )
    assert create.status_code == 201
    preset_id = json.loads(create.data)["id"]

    delete = client.delete(f"/api/rankings/presets/{preset_id}")
    assert delete.status_code == 204

    listed = client.get("/api/rankings/presets")
    rows = json.loads(listed.data)
    assert all(r["id"] != preset_id for r in rows)


def test_default_preset_is_used_for_top_rankings(client, app_instance):
    """When a user has a default preset, /top uses those weights."""
    with app_instance.app_context():
        user = _create_user()
        scorer = _create_athlete("NBA", 30, extra_stats=[
            {"name": "GamesPlayed", "value": 30},
        ])
        iron = _create_athlete("NBA", 12, extra_stats=[
            {"name": "GamesPlayed", "value": 82},
        ])
        iron_name = iron.user.full_name

    _login(client, app_instance, user)

    # Save a durability-only default preset for NBA.
    preset_resp = client.post(
        "/api/rankings/presets",
        json={
            "name": "Iron Man",
            "sport": "NBA",
            "weights": {"durability": 1.0},
            "is_default": True,
        },
    )
    assert preset_resp.status_code == 201

    top = client.get("/api/rankings/top?sport=NBA")
    assert top.status_code == 200
    rows = json.loads(top.data)
    assert rows[0]["name"] == iron_name
