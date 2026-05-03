"""Multi-factor weighted ranking algorithm.

This module provides a pure-Python implementation of the athlete ranking
algorithm.  It is intentionally decoupled from Flask/SQLAlchemy so it can be
unit tested with synthetic data.  The :func:`compute_rankings` function takes
a list of athlete records (plain dictionaries) plus a weight dictionary and
returns a ranked list with a per-component score breakdown.

Design (per requirements 3.1.4 - "Comparative Analysis"):

Five independent component scores are computed in the [0, 100] range:

* ``performance``       - core production from ``season_stats`` /
                          ``athlete_stats`` (per-sport key stat, scaled).
* ``efficiency``        - advanced ratio metrics (e.g. NBA TS%, MLB OPS,
                          NHL +/-, NFL passer rating).  Falls back to a
                          50.0 neutral score when the underlying stats are
                          unavailable.
* ``durability``        - games played / season availability.
* ``fan_perception``    - real signal when available
                          (Wikipedia pageviews + Reddit mentions, see
                          :mod:`app.services.fan_perception_service`).
                          Falls back to a flat 50.0 baseline with a small
                          bump for ``is_featured`` / verified athletes
                          when no real data is available.
* ``market_value``      - real signal when available (agency-supplied
                          ``salary_usd`` + ``endorsements_usd`` +
                          ``contract_end_date``, see
                          :mod:`app.services.market_value_service`).
                          Falls back to ``overall_rating * experience_curve``
                          when those columns are blank.

Wave-3 update
~~~~~~~~~~~~~
``build_athlete_record`` now attempts to pre-compute real fan-perception
and market-value scores from the ORM athlete and stores them in the
record under the ``fan_perception_real`` and ``market_value_real`` keys.
The ``_fan_perception_score`` / ``_market_value_score`` helpers consume
those keys when present, otherwise they apply the legacy heuristics.
The ranking *formula* and *weights* are unchanged - only the inputs to
those two components.

The final score is the weighted sum of the components, and weights default
to ``{performance: 0.4, efficiency: 0.2, durability: 0.2,
fan_perception: 0.1, market_value: 0.1}``.  Weights are auto-normalised so
the caller does not have to make them sum to exactly 1.0.

The module exposes:

* :data:`DEFAULT_WEIGHTS` - the default weights dict.
* :data:`COMPONENT_KEYS` - tuple of valid component names.
* :data:`SPORT_PERFORMANCE_STATS` - per-sport (stat_name, scaling_max) used
  for the performance component.
* :data:`SPORT_EFFICIENCY_STATS` - per-sport (stat_name, scaling_max) used
  for the efficiency component.
* :func:`normalise_weights` - normalise a partial / unbalanced weights dict.
* :func:`compute_rankings` - main entry point.
* :func:`build_athlete_record` - helper that converts an ORM
  ``AthleteProfile`` into the plain-dict shape the algorithm expects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

COMPONENT_KEYS = (
    "performance",
    "efficiency",
    "durability",
    "fan_perception",
    "market_value",
)

DEFAULT_WEIGHTS: dict[str, float] = {
    "performance": 0.4,
    "efficiency": 0.2,
    "durability": 0.2,
    "fan_perception": 0.1,
    "market_value": 0.1,
}

# Per-sport "primary" stat used for the performance component.  The second
# element is a rough maximum used to scale the value to 0-100 - it is a
# heuristic anchor, not a hard cap.
SPORT_PERFORMANCE_STATS: dict[str, Sequence] = {
    "NBA": ("PointsPerGame", 35.0),
    "NFL": ("PassingYards", 5000.0),
    "MLB": ("BattingAverage", 0.350),
    "NHL": ("Points", 120.0),
    "SOC": ("Goals", 50.0),
}

# Per-sport advanced/efficiency stat (with rough maximum for scaling).
SPORT_EFFICIENCY_STATS: dict[str, Sequence] = {
    "NBA": ("TrueShootingPct", 0.700),
    "NFL": ("PasserRating", 130.0),
    "MLB": ("OPS", 1.100),
    "NHL": ("PlusMinus", 50.0),
    "SOC": ("Assists", 25.0),
}

# Approximate season length used for the durability calculation.
SPORT_GAMES_PER_SEASON: dict[str, int] = {
    "NBA": 82,
    "NFL": 17,
    "MLB": 162,
    "NHL": 82,
    "SOC": 38,
}

GAMES_PLAYED_KEYS = ("GamesPlayed", "Games", "GP")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_float(value: Any) -> float | None:
    """Best-effort coercion to ``float``, returning ``None`` on failure."""
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


def _scale(value: float | None, max_val: float) -> float | None:
    """Scale ``value`` to a 0-100 range using ``max_val`` as the anchor."""
    if value is None or max_val in (None, 0):
        return None
    return _clamp((value / max_val) * 100.0)


def _lookup_stat(stats: Iterable[Mapping[str, Any]], names: Sequence[str]) -> float | None:
    """Return the most-recent numeric value for any of ``names`` in ``stats``.

    ``stats`` items are expected to be mappings with at least ``name`` and
    ``value`` keys; an optional ``season`` key is used to choose the most
    recent record when multiple matches exist.
    """
    candidates = []
    for stat in stats or []:
        sname = stat.get("name") if isinstance(stat, Mapping) else getattr(stat, "name", None)
        if sname in names:
            candidates.append(stat)
    if not candidates:
        return None

    def _season(s):
        if isinstance(s, Mapping):
            return s.get("season") or ""
        return getattr(s, "season", "") or ""

    candidates.sort(key=_season, reverse=True)
    chosen = candidates[0]
    raw = chosen.get("value") if isinstance(chosen, Mapping) else getattr(chosen, "value", None)
    return _to_float(raw)


# ---------------------------------------------------------------------------
# Weight normalisation
# ---------------------------------------------------------------------------


def normalise_weights(weights: Mapping[str, Any] | None) -> dict[str, float]:
    """Return a dict of valid component weights summing to 1.0.

    * Unknown keys are dropped.
    * Missing keys default to 0.
    * Negative values are clamped to 0.
    * If the total is 0 (or no weights supplied) the defaults are used.
    """
    if not weights:
        return dict(DEFAULT_WEIGHTS)

    cleaned: dict[str, float] = {}
    for key in COMPONENT_KEYS:
        raw = weights.get(key)
        val = _to_float(raw)
        if val is None or val < 0:
            val = 0.0
        cleaned[key] = val

    total = sum(cleaned.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)

    return {k: v / total for k, v in cleaned.items()}


# ---------------------------------------------------------------------------
# Component score calculations
# ---------------------------------------------------------------------------


def _performance_score(record: Mapping[str, Any]) -> float:
    sport = record.get("sport_code")
    spec = SPORT_PERFORMANCE_STATS.get(sport)
    if not spec:
        # No mapped stat for this sport - fall back to overall_rating scaled.
        rating = _to_float(record.get("overall_rating"))
        if rating is None:
            return 0.0
        # overall_rating is 0-99.99 so it doubles as a 0-100 score.
        return _clamp(rating)

    stat_name, max_val = spec
    value = _lookup_stat(record.get("stats") or [], (stat_name,))
    scaled = _scale(value, max_val)
    if scaled is not None:
        return scaled
    # No matching stat - fall back to overall_rating.
    rating = _to_float(record.get("overall_rating"))
    if rating is None:
        return 0.0
    return _clamp(rating)


def _efficiency_score(record: Mapping[str, Any]) -> float:
    sport = record.get("sport_code")
    spec = SPORT_EFFICIENCY_STATS.get(sport)
    if not spec:
        return 50.0  # neutral baseline
    stat_name, max_val = spec
    value = _lookup_stat(record.get("stats") or [], (stat_name,))
    scaled = _scale(value, max_val)
    return scaled if scaled is not None else 50.0


def _durability_score(record: Mapping[str, Any]) -> float:
    sport = record.get("sport_code")
    season_len = SPORT_GAMES_PER_SEASON.get(sport, 82)
    games = _lookup_stat(record.get("stats") or [], GAMES_PLAYED_KEYS)
    if games is None:
        # No games-played stat - assume an average availability.
        return 50.0
    return _clamp((games / season_len) * 100.0)


def _fan_perception_score(record: Mapping[str, Any]) -> float:
    """Real signal when ``fan_perception_real`` is set, else fallback heuristic.

    The ORM adapter (:func:`build_athlete_record`) calls
    :func:`app.services.fan_perception_service.compute_fan_perception_score`
    and stores the result under ``fan_perception_real``.  When that real
    score is missing or ``None`` we apply the legacy ``50 + 20*featured +
    10*verified`` heuristic so dict-only callers and offline tests still
    work.
    """
    real = _to_float(record.get("fan_perception_real"))
    if real is not None:
        return _clamp(real)

    base = 50.0
    if record.get("is_featured"):
        base += 20.0
    if record.get("is_verified"):
        base += 10.0
    return _clamp(base)


def _market_value_score(record: Mapping[str, Any]) -> float:
    """Real signal when ``market_value_real`` is set, else fallback heuristic.

    The ORM adapter calls
    :func:`app.services.market_value_service.compute_market_value_score`
    and stores the result under ``market_value_real``.  Missing data
    falls back to ``overall_rating * experience_curve``.
    """
    real = _to_float(record.get("market_value_real"))
    if real is not None:
        return _clamp(real)

    rating = _to_float(record.get("overall_rating")) or 0.0
    years = _to_float(record.get("years_professional")) or 0.0
    # Experience curve: peaks around 8 years.
    exp_factor = 1.0 - abs(years - 8.0) / 16.0
    exp_factor = max(0.4, min(1.0, exp_factor))
    return _clamp(rating * exp_factor)


def _compute_components(record: Mapping[str, Any]) -> dict[str, float]:
    return {
        "performance": round(_performance_score(record), 2),
        "efficiency": round(_efficiency_score(record), 2),
        "durability": round(_durability_score(record), 2),
        "fan_perception": round(_fan_perception_score(record), 2),
        "market_value": round(_market_value_score(record), 2),
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def compute_rankings(
    athletes: Iterable[Mapping[str, Any]],
    weights: Mapping[str, Any] | None = None,
    *,
    sport: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Return a ranked list of athletes.

    Parameters
    ----------
    athletes:
        Iterable of dict-like records.  Each record should expose:
        ``athlete_id``, ``name``, ``sport_code``, ``overall_rating``
        (optional), ``years_professional`` (optional), ``is_featured``,
        ``is_verified``, and ``stats`` - an iterable of ``{name, value,
        season}`` dicts.
    weights:
        Optional mapping of component name -> weight.  Auto-normalised.
    sport:
        Optional sport code filter (e.g. ``"NBA"``).
    limit:
        Optional maximum number of athletes to return.

    Returns
    -------
    list of dict, each with keys ``athlete_id``, ``name``, ``sport``,
    ``score`` (0-100), ``components`` (per-component breakdown), and
    ``rank`` (1-based).
    """
    norm_weights = normalise_weights(weights)
    rows: list[dict[str, Any]] = []
    for record in athletes:
        if sport and record.get("sport_code") != sport:
            continue
        components = _compute_components(record)
        score = sum(components[k] * norm_weights[k] for k in COMPONENT_KEYS)
        rows.append({
            "athlete_id": record.get("athlete_id"),
            "name": record.get("name"),
            "sport": record.get("sport_code"),
            "score": round(score, 2),
            "components": components,
        })

    rows.sort(key=lambda r: r["score"], reverse=True)
    for idx, row in enumerate(rows, start=1):
        row["rank"] = idx

    if limit is not None and limit > 0:
        rows = rows[:limit]
    return rows


# ---------------------------------------------------------------------------
# ORM adapter
# ---------------------------------------------------------------------------


def build_athlete_record(athlete) -> dict[str, Any]:
    """Convert an :class:`AthleteProfile` ORM row to the algorithm's input.

    The function is tolerant of missing relationships and stat collections.

    Wave-3: also calls the real fan-perception and market-value services
    and stores their results under ``fan_perception_real`` /
    ``market_value_real`` so the component scorers can use real data
    instead of the legacy placeholders.  Service failures degrade
    silently to the legacy heuristic.
    """
    name = None
    user = getattr(athlete, "user", None)
    if user is not None:
        full = getattr(user, "full_name", None)
        if full:
            name = full
    if not name:
        name = getattr(athlete, "athlete_id", None)

    sport = getattr(athlete, "primary_sport", None)
    sport_code = getattr(sport, "code", None) if sport is not None else None

    stats: list[dict[str, Any]] = []
    raw_stats = getattr(athlete, "stats", None) or []
    for s in raw_stats:
        stats.append({
            "name": getattr(s, "name", None),
            "value": getattr(s, "value", None),
            "season": getattr(s, "season", None),
        })

    # Wave-3: pull real signals when available.  Both services already
    # return ``None`` on missing data / upstream failure, but we wrap them
    # in ``try/except`` for total isolation - a bug in either must never
    # crash the ranking pipeline.
    fan_real: Optional[float] = None
    market_real: Optional[float] = None
    try:
        from app.services.fan_perception_service import (
            compute_fan_perception_score,
        )
        fan_real = compute_fan_perception_score(athlete)
    except Exception:  # pragma: no cover - defensive
        fan_real = None
    try:
        from app.services.market_value_service import (
            compute_market_value_score,
        )
        market_real = compute_market_value_score(athlete)
    except Exception:  # pragma: no cover - defensive
        market_real = None

    return {
        "athlete_id": getattr(athlete, "athlete_id", None),
        "name": name,
        "sport_code": sport_code,
        "overall_rating": getattr(athlete, "overall_rating", None),
        "years_professional": getattr(athlete, "years_professional", None),
        "is_featured": bool(getattr(athlete, "is_featured", False)),
        "is_verified": bool(getattr(athlete, "is_verified", False)),
        "stats": stats,
        "fan_perception_real": fan_real,
        "market_value_real": market_real,
    }
