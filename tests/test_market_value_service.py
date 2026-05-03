"""Pure-Python unit tests for :mod:`app.services.market_value_service`.

The service has no DB or network dependencies, so we import it directly
from disk to avoid pulling in the entire ``app`` package at collection
time (which can be flaky on partial-merge branches).
"""

from __future__ import annotations

import importlib.util
import os
import sys
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

_SERVICE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "app",
        "services",
        "market_value_service.py",
    )
)


def _load_service():
    if "market_value_service" in sys.modules:
        return sys.modules["market_value_service"]
    spec = importlib.util.spec_from_file_location(
        "market_value_service", _SERVICE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["market_value_service"] = module
    spec.loader.exec_module(module)
    return module


mvs = _load_service()


def _athlete(*, salary_usd=None, endorsements_usd=None,
             contract_end_date=None, years_professional=None,
             sport_code="NBA"):
    primary_sport = SimpleNamespace(code=sport_code)
    return SimpleNamespace(
        salary_usd=salary_usd,
        endorsements_usd=endorsements_usd,
        contract_end_date=contract_end_date,
        years_professional=years_professional,
        primary_sport=primary_sport,
    )


# ---------------------------------------------------------------------------
# compensation_subscore
# ---------------------------------------------------------------------------


def test_compensation_subscore_returns_none_when_both_missing():
    assert mvs.compensation_subscore(None, None, "NBA") is None


def test_compensation_subscore_zero_when_total_zero():
    assert mvs.compensation_subscore(0, 0, "NBA") == 0.0


def test_compensation_subscore_in_range():
    score = mvs.compensation_subscore(20_000_000, 5_000_000, "NBA")
    assert 0.0 <= score <= 100.0


def test_compensation_subscore_clamped_at_top():
    score = mvs.compensation_subscore(1_000_000_000, 0, "NBA")
    assert score == 100.0


def test_compensation_subscore_per_sport_normalisation():
    # Same compensation should give different scores per sport because
    # NFL has a much larger reference cap than MLB.
    nba = mvs.compensation_subscore(50_000_000, 0, "NBA")
    nfl = mvs.compensation_subscore(50_000_000, 0, "NFL")
    mlb = mvs.compensation_subscore(50_000_000, 0, "MLB")
    assert mlb > nba > nfl


def test_compensation_subscore_unknown_sport_uses_default():
    assert mvs.compensation_subscore(10_000_000, 0, "XYZ") is not None


def test_compensation_subscore_handles_only_endorsements():
    assert mvs.compensation_subscore(None, 1_000_000, "NBA") is not None


# ---------------------------------------------------------------------------
# contract_subscore
# ---------------------------------------------------------------------------


def test_contract_subscore_missing_is_neutral():
    assert mvs.contract_subscore(None) == 50.0


def test_contract_subscore_zero_years():
    assert mvs.contract_subscore(0.0) == 0.0


def test_contract_subscore_five_years_pegs_to_100():
    assert mvs.contract_subscore(5.0) == 100.0


def test_contract_subscore_clamped_at_top():
    assert mvs.contract_subscore(20.0) == 100.0


# ---------------------------------------------------------------------------
# experience_subscore
# ---------------------------------------------------------------------------


def test_experience_subscore_peaks_at_year_8():
    peak = mvs.experience_subscore(8)
    rookie = mvs.experience_subscore(0)
    long_veteran = mvs.experience_subscore(24)  # 8 + 16
    missing = mvs.experience_subscore(None)
    assert peak == 100.0
    # year 0 -> factor=0.5 -> 50, year 24 -> floor (40)
    assert rookie == pytest.approx(50.0, abs=0.01)
    assert long_veteran == pytest.approx(40.0, abs=0.01)
    assert missing == 50.0
    # peak strictly higher than the rookie/long-veteran tails
    assert peak > rookie > long_veteran


def test_experience_subscore_clamps_to_floor():
    assert mvs.experience_subscore(100) == pytest.approx(40.0, abs=0.01)


# ---------------------------------------------------------------------------
# compute_market_value_score
# ---------------------------------------------------------------------------


def test_compute_returns_none_when_no_compensation_signal():
    a = _athlete(salary_usd=None, endorsements_usd=None)
    assert mvs.compute_market_value_score(a) is None


def test_compute_with_full_data_returns_in_range_score():
    a = _athlete(
        salary_usd=20_000_000,
        endorsements_usd=10_000_000,
        contract_end_date=date.today() + timedelta(days=365 * 3),
        years_professional=8,
    )
    score = mvs.compute_market_value_score(a)
    assert score is not None
    assert 0.0 <= score <= 100.0


def test_compute_higher_compensation_yields_higher_score():
    cheap = _athlete(salary_usd=1_000_000, endorsements_usd=0,
                     years_professional=8)
    rich = _athlete(salary_usd=40_000_000, endorsements_usd=0,
                    years_professional=8)
    assert mvs.compute_market_value_score(rich) > \
        mvs.compute_market_value_score(cheap)


def test_compute_longer_contract_increases_score():
    base = dict(salary_usd=10_000_000, endorsements_usd=0,
                years_professional=8)
    short = _athlete(
        contract_end_date=date.today() + timedelta(days=180),
        **base,
    )
    long_ = _athlete(
        contract_end_date=date.today() + timedelta(days=365 * 5),
        **base,
    )
    assert mvs.compute_market_value_score(long_) > \
        mvs.compute_market_value_score(short)


def test_compute_uses_sport_code_when_no_primary_sport():
    a = SimpleNamespace(
        salary_usd=10_000_000,
        endorsements_usd=0,
        contract_end_date=None,
        years_professional=5,
        sport_code="MLB",
        primary_sport=None,
    )
    score = mvs.compute_market_value_score(a)
    assert score is not None and 0.0 <= score <= 100.0


def test_compute_market_value_score_endorsements_only():
    a = _athlete(
        salary_usd=None,
        endorsements_usd=2_000_000,
        years_professional=10,
    )
    # With only endorsements, compensation is still computable so the
    # function must NOT return None.
    assert mvs.compute_market_value_score(a) is not None


def test_breakdown_includes_all_subscores():
    a = _athlete(salary_usd=10_000_000, endorsements_usd=2_000_000,
                 years_professional=8)
    bd = mvs.market_value_breakdown(a)
    assert bd["sport"] == "NBA"
    assert bd["compensation"] is not None
    assert bd["contract"] == 50.0  # No contract_end_date => neutral
    assert bd["experience"] == 100.0
    assert "weights" in bd


def test_per_sport_reference_points_match_brief():
    """The brief specifies per-sport reference compensations."""
    refs = mvs.SPORT_COMPENSATION_REFERENCE
    assert refs["NBA"] == 140_000_000
    assert refs["NFL"] == 255_000_000
    assert refs["NHL"] == 88_000_000
    assert refs["MLB"] == 40_000_000
