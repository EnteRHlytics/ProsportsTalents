"""Market-value score service.

Replaces the ``overall_rating * experience_curve`` placeholder in
:mod:`app.services.ranking_service` with a score derived from real,
agency-supplied data:

* ``athlete.salary_usd``        - current annual salary (agency input)
* ``athlete.endorsements_usd``  - annual endorsement / sponsorship income
* ``athlete.contract_end_date`` - contract expiry, used to derive a
                                  "years remaining" multiplier (longer
                                  contracts -> higher market value).
* ``athlete.years_professional`` - feeds an experience curve that peaks
                                   around year 8 of a career.

We deliberately *avoid* scraping Spotrac / OvertheCap / Capfriendly -
their ToS prohibit scraping.  The Forbes "World's Highest-Paid Athletes"
list is public but only covers the very top ~50 names per year and does
not have a per-athlete API; the agency's manual entry covers the rest of
the roster.

Scoring
-------
1. ``compensation_score`` = log10(1 + salary + endorsements) normalised
   against a per-sport reference cap.  This produces a 0-100 sub-score
   that does not let outlier salaries blow up the scale.

2. ``contract_score`` = ``min(years_remaining / 5, 1.0) * 100``.  Five
   years remaining = 100; expired contract = 0.

3. ``experience_score`` = inverted-V centred at year 8, returning 100 at
   the peak and 40 at year 0 / year 16+.

The three sub-scores are combined::

    score = 0.6 * compensation + 0.25 * contract + 0.15 * experience

If both ``salary_usd`` and ``endorsements_usd`` are missing,
``compute_market_value_score`` returns ``None`` and the ranking
service falls back to the existing placeholder.

All maths are pure-Python (no DB, no network) so the module is
trivially unit-testable.

Per-sport reference points
--------------------------
``salary + endorsements`` is normalised against::

    NBA = 140_000_000   # 2024-25 salary cap
    NFL = 255_000_000   # 2024-25 salary cap
    NHL = 88_000_000    # 2024-25 upper limit
    MLB = 40_000_000    # no cap; reference top-of-market AAV

These caps are public knowledge (league press releases, Wikipedia).  We
do not pull them at runtime - the figures are stable on a year-over-year
basis and the absolute scale does not need to be perfect for *relative*
ranking.
"""

from __future__ import annotations

import logging
import math
from datetime import date
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Per-sport reference compensation (USD).  These figures are league-wide
# salary caps / top-of-market AAVs - public knowledge, not sourced from a
# scraping target.
# ---------------------------------------------------------------------------
SPORT_COMPENSATION_REFERENCE: Dict[str, float] = {
    "NBA": 140_000_000.0,
    "NFL": 255_000_000.0,
    "NHL": 88_000_000.0,
    "MLB": 40_000_000.0,
    "SOC": 50_000_000.0,
}
DEFAULT_COMPENSATION_REFERENCE = 50_000_000.0

#: Component weights inside the composite score.
_COMP_WEIGHT = 0.60
_CONTRACT_WEIGHT = 0.25
_EXPERIENCE_WEIGHT = 0.15

#: Years of contract remaining that pegs the contract sub-score at 100.
_CONTRACT_REFERENCE_YEARS = 5.0


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _years_remaining(contract_end: Optional[date],
                     today: Optional[date] = None) -> Optional[float]:
    if contract_end is None:
        return None
    today = today or date.today()
    delta_days = (contract_end - today).days
    if delta_days <= 0:
        return 0.0
    return delta_days / 365.25


# ---------------------------------------------------------------------------
# Sub-scores
# ---------------------------------------------------------------------------


def compensation_subscore(
    salary_usd: Optional[float],
    endorsements_usd: Optional[float],
    sport_code: Optional[str],
) -> Optional[float]:
    """Return a 0-100 sub-score from total compensation.

    Returns ``None`` when both inputs are missing.
    """
    salary = _to_float(salary_usd)
    endorse = _to_float(endorsements_usd)
    if salary is None and endorse is None:
        return None
    total = (salary or 0.0) + (endorse or 0.0)
    if total <= 0:
        return 0.0
    reference = SPORT_COMPENSATION_REFERENCE.get(
        sport_code, DEFAULT_COMPENSATION_REFERENCE
    )
    # Log-scale so the very top earners do not eclipse everyone else.
    return _clamp(
        math.log10(1 + total) / math.log10(1 + reference) * 100.0
    )


def contract_subscore(years_remaining: Optional[float]) -> float:
    """Return a 0-100 sub-score from years remaining on contract.

    Missing data -> a neutral 50.0 baseline (we do not penalise athletes
    whose contracts simply have not been entered yet).
    """
    if years_remaining is None:
        return 50.0
    return _clamp(years_remaining / _CONTRACT_REFERENCE_YEARS * 100.0)


def experience_subscore(years_professional: Optional[float]) -> float:
    """Inverted-V experience curve peaking at year 8.

    * years 0 / 16+ -> 40.0
    * year 8        -> 100.0
    * Missing       -> 50.0 (neutral)
    """
    yrs = _to_float(years_professional)
    if yrs is None:
        return 50.0
    factor = 1.0 - abs(yrs - 8.0) / 16.0
    factor = max(0.4, min(1.0, factor))
    return _clamp(factor * 100.0)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def compute_market_value_score(
    athlete: Any,
    *,
    today: Optional[date] = None,
) -> Optional[float]:
    """Compute the 0-100 market-value score for ``athlete``.

    Returns ``None`` when neither salary nor endorsements are available
    (i.e. there is no agency-supplied signal at all).  In that case the
    ranking service falls back to its existing heuristic.
    """
    sport = None
    primary_sport = getattr(athlete, "primary_sport", None)
    if primary_sport is not None:
        sport = getattr(primary_sport, "code", None)
    if sport is None:
        sport = getattr(athlete, "sport_code", None)

    comp = compensation_subscore(
        getattr(athlete, "salary_usd", None),
        getattr(athlete, "endorsements_usd", None),
        sport,
    )
    if comp is None:
        # No agency-supplied signal -> defer to placeholder.
        return None

    yrs_remaining = _years_remaining(
        getattr(athlete, "contract_end_date", None), today=today
    )
    contract = contract_subscore(yrs_remaining)
    experience = experience_subscore(getattr(athlete, "years_professional", None))

    score = (
        _COMP_WEIGHT * comp
        + _CONTRACT_WEIGHT * contract
        + _EXPERIENCE_WEIGHT * experience
    )
    return round(_clamp(score), 2)


def market_value_breakdown(
    athlete: Any, *, today: Optional[date] = None
) -> Dict[str, Any]:
    """Return the per-sub-score breakdown - useful for admin UIs / tests."""
    sport = None
    primary_sport = getattr(athlete, "primary_sport", None)
    if primary_sport is not None:
        sport = getattr(primary_sport, "code", None)
    if sport is None:
        sport = getattr(athlete, "sport_code", None)

    salary = getattr(athlete, "salary_usd", None)
    endorse = getattr(athlete, "endorsements_usd", None)
    yrs_remaining = _years_remaining(
        getattr(athlete, "contract_end_date", None), today=today
    )
    yrs_pro = getattr(athlete, "years_professional", None)

    return {
        "sport": sport,
        "salary_usd": _to_float(salary),
        "endorsements_usd": _to_float(endorse),
        "compensation": compensation_subscore(salary, endorse, sport),
        "years_remaining": yrs_remaining,
        "contract": contract_subscore(yrs_remaining),
        "years_professional": _to_float(yrs_pro),
        "experience": experience_subscore(yrs_pro),
        "weights": {
            "compensation": _COMP_WEIGHT,
            "contract": _CONTRACT_WEIGHT,
            "experience": _EXPERIENCE_WEIGHT,
        },
    }


__all__ = [
    "SPORT_COMPENSATION_REFERENCE",
    "compensation_subscore",
    "contract_subscore",
    "experience_subscore",
    "compute_market_value_score",
    "market_value_breakdown",
]
