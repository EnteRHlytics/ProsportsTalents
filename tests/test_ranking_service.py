"""Unit tests for the multi-factor ranking algorithm.

These tests exercise :mod:`app.services.ranking_service` with synthetic
records.  The module is pure-Python and does not require a database or a
Flask app.  We import it directly from its file location so the tests run
even when other agents' modules elsewhere in the package are not yet
present at merge time.
"""

import importlib.util
import os
import sys

import pytest

_SERVICE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "..", "app", "services", "ranking_service.py"
    )
)


def _load_service():
    """Load the ranking_service module without going through ``app/__init__``."""
    if "ranking_service" in sys.modules:
        return sys.modules["ranking_service"]
    spec = importlib.util.spec_from_file_location("ranking_service", _SERVICE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["ranking_service"] = module
    spec.loader.exec_module(module)
    return module


rs = _load_service()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _athlete(
    aid,
    name,
    sport_code,
    *,
    overall_rating=70,
    years_professional=5,
    is_featured=False,
    is_verified=False,
    stats=None,
):
    return {
        "athlete_id": aid,
        "name": name,
        "sport_code": sport_code,
        "overall_rating": overall_rating,
        "years_professional": years_professional,
        "is_featured": is_featured,
        "is_verified": is_verified,
        "stats": stats or [],
    }


def _stat(name, value, season="2024"):
    return {"name": name, "value": value, "season": season}


# ---------------------------------------------------------------------------
# normalise_weights
# ---------------------------------------------------------------------------


def test_default_weights_sum_to_one():
    total = sum(rs.DEFAULT_WEIGHTS.values())
    assert pytest.approx(total, abs=1e-9) == 1.0


def test_normalise_weights_returns_defaults_when_empty():
    assert rs.normalise_weights(None) == rs.DEFAULT_WEIGHTS
    assert rs.normalise_weights({}) == rs.DEFAULT_WEIGHTS


def test_normalise_weights_rescales_partial_weights():
    weights = rs.normalise_weights({"performance": 2, "efficiency": 1, "durability": 1})
    assert pytest.approx(sum(weights.values()), abs=1e-9) == 1.0
    assert pytest.approx(weights["performance"], abs=1e-9) == 0.5
    assert pytest.approx(weights["efficiency"], abs=1e-9) == 0.25
    assert pytest.approx(weights["durability"], abs=1e-9) == 0.25
    assert weights["fan_perception"] == 0.0
    assert weights["market_value"] == 0.0


def test_normalise_weights_drops_unknown_and_clamps_negative():
    weights = rs.normalise_weights({
        "performance": 1,
        "efficiency": -5,
        "bogus": 99,
    })
    assert pytest.approx(sum(weights.values()), abs=1e-9) == 1.0
    assert weights["performance"] == 1.0
    assert weights["efficiency"] == 0.0
    assert "bogus" not in weights


def test_normalise_weights_zero_total_falls_back_to_defaults():
    assert rs.normalise_weights({"performance": 0}) == rs.DEFAULT_WEIGHTS


# ---------------------------------------------------------------------------
# Component scoring
# ---------------------------------------------------------------------------


def test_compute_rankings_orders_by_score_descending():
    athletes = [
        _athlete("a", "Alpha", "NBA", stats=[
            _stat("PointsPerGame", "30"),
            _stat("TrueShootingPct", "0.62"),
            _stat("GamesPlayed", "78"),
        ]),
        _athlete("b", "Bravo", "NBA", stats=[
            _stat("PointsPerGame", "12"),
            _stat("TrueShootingPct", "0.48"),
            _stat("GamesPlayed", "40"),
        ]),
        _athlete("c", "Charlie", "NBA", stats=[
            _stat("PointsPerGame", "22"),
            _stat("TrueShootingPct", "0.55"),
            _stat("GamesPlayed", "70"),
        ]),
    ]
    result = rs.compute_rankings(athletes)
    assert [r["name"] for r in result] == ["Alpha", "Charlie", "Bravo"]
    assert result[0]["rank"] == 1
    assert result[1]["rank"] == 2
    assert result[2]["rank"] == 3
    assert result[0]["score"] >= result[1]["score"] >= result[2]["score"]


def test_compute_rankings_returns_component_breakdown():
    athletes = [
        _athlete("a", "Alpha", "NBA", stats=[
            _stat("PointsPerGame", "35"),
            _stat("TrueShootingPct", "0.70"),
            _stat("GamesPlayed", "82"),
        ]),
    ]
    result = rs.compute_rankings(athletes)
    assert len(result) == 1
    components = result[0]["components"]
    assert set(components) == set(rs.COMPONENT_KEYS)
    # Maxed-out NBA stats should produce ~100 in performance / efficiency /
    # durability.
    assert components["performance"] == pytest.approx(100.0, abs=0.01)
    assert components["efficiency"] == pytest.approx(100.0, abs=0.01)
    assert components["durability"] == pytest.approx(100.0, abs=0.01)


def test_components_clamped_to_0_100():
    """Even absurd inputs must produce in-range component scores."""
    athletes = [
        _athlete("a", "Mega", "NBA", stats=[
            _stat("PointsPerGame", "999"),
            _stat("TrueShootingPct", "5.0"),
            _stat("GamesPlayed", "9999"),
        ]),
        _athlete("b", "Negative", "NBA", overall_rating=-50, stats=[]),
    ]
    result = rs.compute_rankings(athletes)
    for row in result:
        for k, v in row["components"].items():
            assert 0.0 <= v <= 100.0, f"{row['name']}.{k} = {v} out of range"
        assert 0.0 <= row["score"] <= 100.0


def test_weights_change_ranking_order():
    """Different weight presets pick different leaders."""
    big_scorer = _athlete("a", "Big Scorer", "NBA", stats=[
        _stat("PointsPerGame", "30"),
        _stat("TrueShootingPct", "0.50"),
        _stat("GamesPlayed", "40"),  # low durability
    ])
    iron_man = _athlete("b", "Iron Man", "NBA", stats=[
        _stat("PointsPerGame", "12"),
        _stat("TrueShootingPct", "0.55"),
        _stat("GamesPlayed", "82"),  # full season
    ])

    perf_first = rs.compute_rankings(
        [big_scorer, iron_man],
        weights={"performance": 1.0},
    )
    durability_first = rs.compute_rankings(
        [big_scorer, iron_man],
        weights={"durability": 1.0},
    )
    assert perf_first[0]["name"] == "Big Scorer"
    assert durability_first[0]["name"] == "Iron Man"


def test_compute_rankings_filters_by_sport():
    athletes = [
        _athlete("a", "NBAer", "NBA", stats=[_stat("PointsPerGame", "20")]),
        _athlete("b", "Hockey", "NHL", stats=[_stat("Points", "60")]),
        _athlete("c", "Footballer", "NFL", stats=[_stat("PassingYards", "4000")]),
    ]
    nba_only = rs.compute_rankings(athletes, sport="NBA")
    assert len(nba_only) == 1
    assert nba_only[0]["sport"] == "NBA"


def test_compute_rankings_respects_limit():
    athletes = [
        _athlete(str(i), f"P{i}", "NBA", stats=[_stat("PointsPerGame", str(i))])
        for i in range(1, 11)
    ]
    top3 = rs.compute_rankings(athletes, limit=3)
    assert len(top3) == 3
    # Ranks are still 1..3
    assert [r["rank"] for r in top3] == [1, 2, 3]


def test_missing_stats_fall_back_gracefully():
    athletes = [
        _athlete("a", "NoStats", "NBA", overall_rating=80, stats=[]),
    ]
    result = rs.compute_rankings(athletes)
    row = result[0]
    # Performance falls back to overall_rating; efficiency/durability use
    # their neutral defaults.
    assert row["components"]["performance"] == pytest.approx(80.0, abs=0.01)
    assert row["components"]["efficiency"] == 50.0
    assert row["components"]["durability"] == 50.0


def test_unknown_sport_uses_overall_rating():
    athletes = [
        _athlete("a", "Crickett", "CRI", overall_rating=88, stats=[]),
    ]
    result = rs.compute_rankings(athletes)
    assert result[0]["components"]["performance"] == pytest.approx(88.0, abs=0.01)


def test_featured_athlete_gets_higher_fan_perception():
    plain = _athlete("a", "Plain", "NBA")
    star = _athlete("b", "Star", "NBA", is_featured=True, is_verified=True)
    plain_score = rs._fan_perception_score(plain)
    star_score = rs._fan_perception_score(star)
    assert star_score > plain_score


def test_uses_most_recent_season_when_multiple_records():
    athletes = [
        _athlete("a", "Trend", "NBA", stats=[
            _stat("PointsPerGame", "10", season="2022"),
            _stat("PointsPerGame", "30", season="2024"),
            _stat("PointsPerGame", "20", season="2023"),
        ]),
    ]
    result = rs.compute_rankings(athletes)
    # Performance should reflect 30 PPG (i.e. ~85.7), not 10 or 20.
    assert result[0]["components"]["performance"] == pytest.approx(
        round(30 / 35.0 * 100.0, 2), abs=0.01
    )


def test_weighted_sum_matches_components():
    """The headline ``score`` is the weighted sum of the components."""
    athletes = [
        _athlete("a", "Alpha", "NBA", stats=[
            _stat("PointsPerGame", "20"),
            _stat("TrueShootingPct", "0.55"),
            _stat("GamesPlayed", "60"),
        ]),
    ]
    weights = {
        "performance": 0.5,
        "efficiency": 0.2,
        "durability": 0.2,
        "fan_perception": 0.05,
        "market_value": 0.05,
    }
    result = rs.compute_rankings(athletes, weights=weights)
    row = result[0]
    expected = sum(
        row["components"][k] * weights[k] for k in rs.COMPONENT_KEYS
    )
    assert row["score"] == pytest.approx(round(expected, 2), abs=0.01)
