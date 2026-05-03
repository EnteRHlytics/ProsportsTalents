"""Fan-perception score service.

This module replaces the heuristic 50 + (20 if featured) + (10 if verified)
placeholder in :mod:`app.services.ranking_service` with a score derived
from real, free, public, ToS-friendly data sources:

* **Wikipedia REST API - per-article pageviews** (no auth, no key).
  Endpoint::

      https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/
      en.wikipedia/all-access/all-agents/<article>/daily/<start>/<end>

  Total views over the window is a reasonable popularity proxy.  More
  views = more public interest.

* **Reddit search** (no auth needed for read-only at low rates) ::

      https://www.reddit.com/search.json?q=<query>&sort=hot&t=month

  We count returned children as a "mentions in the last month" proxy.  A
  ``User-Agent`` header is sent and we keep call volume low (one call per
  athlete per day, executed by the nightly scheduler job).

Both raw signals are squashed with ``log10(1+x)``, normalised against
high-end reference points, capped at 100, and combined::

    score = 0.6 * wiki_subscore + 0.4 * reddit_subscore

Results are cached in :class:`app.models.FanPerceptionScore` with a
1-day TTL so ranking calls do not hit upstream APIs on every request.

Graceful degradation
--------------------
* If both upstream calls fail and there is no cached row,
  :func:`compute_fan_perception_score` returns ``None`` so the ranking
  service can fall back to its existing heuristic.
* If only one source is reachable, the available sub-score is returned
  weighted up by the missing source's weight (so a Wiki-only result is
  not penalised by a missing-Reddit zero).

The HTTP clients are class-based so tests can swap in mocks; both raw
fetches are wrapped in broad ``try/except`` blocks because no upstream
guarantees uptime.
"""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timedelta
from typing import Any

import requests

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: TTL for cached :class:`FanPerceptionScore` rows.  Older rows are
#: considered stale and will be refreshed on the next call.
CACHE_TTL = timedelta(days=1)

#: Reference for Wikipedia views in a 30-day window.  Top-tier athletes
#: (LeBron James, Tom Brady, Lionel Messi) routinely pull ~1M+ views/month
#: on en.wikipedia.  ``log10(1 + 1_000_000) ~= 6``, so we anchor the log
#: scale at 6 = 100.
_WIKI_LOG_REFERENCE = 6.0  # log10(1 + 1M)

#: Reference for Reddit mention counts.  The search.json endpoint returns
#: at most ~25 children per page; a hot athlete trends around that ceiling
#: in any given month, so ``log10(1 + 25) ~= 1.41`` ~ 100.
_REDDIT_LOG_REFERENCE = math.log10(1 + 100.0)

#: Component weights inside the composite score.
_WIKI_WEIGHT = 0.6
_REDDIT_WEIGHT = 0.4

#: Polite User-Agent (Wikipedia and Reddit both ask clients to identify
#: themselves and reject generic ``python-requests`` UAs in some cases).
_USER_AGENT = (
    "ProsportsTalents/1.0 (https://prosportstalents.example.com; "
    "ranking-data-pipeline) python-requests"
)

_WIKI_BASE = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "en.wikipedia/all-access/all-agents"
)
_REDDIT_SEARCH = "https://www.reddit.com/search.json"


# ---------------------------------------------------------------------------
# Wikipedia
# ---------------------------------------------------------------------------


class WikipediaPageviewsClient:
    """Thin wrapper around the Wikipedia per-article pageviews API."""

    def __init__(self, session: requests.Session | None = None,
                 timeout: float = 10.0):
        self._session = session or requests.Session()
        self._timeout = timeout

    @staticmethod
    def _format_article(title: str) -> str:
        # Wikipedia URLs use underscores instead of spaces.
        return title.strip().replace(" ", "_")

    def get_views(self, article_title: str, days: int = 30) -> int | None:
        """Return total daily pageviews for ``article_title`` over ``days``.

        Returns ``None`` if the upstream call fails or the article does
        not exist.  Never raises - upstream failures are logged and
        swallowed so the ranking pipeline can continue.
        """
        if not article_title:
            return None
        try:
            end = datetime.utcnow().date() - timedelta(days=1)
            start = end - timedelta(days=max(days, 1) - 1)
            url = (
                f"{_WIKI_BASE}/{self._format_article(article_title)}"
                f"/daily/{start:%Y%m%d}/{end:%Y%m%d}"
            )
            resp = self._session.get(
                url,
                headers={"User-Agent": _USER_AGENT},
                timeout=self._timeout,
            )
            if resp.status_code != 200:
                logger.info(
                    "Wikipedia pageviews returned %s for %s",
                    resp.status_code, article_title,
                )
                return None
            payload = resp.json() or {}
            items = payload.get("items") or []
            total = 0
            for item in items:
                v = item.get("views")
                if isinstance(v, (int, float)):
                    total += int(v)
            return total
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "Wikipedia pageviews fetch failed for %s: %s",
                article_title, exc,
            )
            return None


# ---------------------------------------------------------------------------
# Reddit
# ---------------------------------------------------------------------------


class RedditMentionsClient:
    """Read-only Reddit search using the public ``search.json`` endpoint."""

    def __init__(self, session: requests.Session | None = None,
                 timeout: float = 10.0):
        self._session = session or requests.Session()
        self._timeout = timeout

    def get_mention_count(self, query: str, period: str = "month") -> int | None:
        """Return the number of Reddit posts matching ``query`` in ``period``.

        ``period`` is one of ``hour|day|week|month|year|all``.  Returns
        ``None`` if the upstream call fails.
        """
        if not query:
            return None
        try:
            params = {
                "q": query,
                "sort": "hot",
                "t": period,
                "limit": 100,
            }
            resp = self._session.get(
                _REDDIT_SEARCH,
                params=params,
                headers={"User-Agent": _USER_AGENT},
                timeout=self._timeout,
            )
            if resp.status_code != 200:
                logger.info(
                    "Reddit search returned %s for %s",
                    resp.status_code, query,
                )
                return None
            payload = resp.json() or {}
            data = payload.get("data") or {}
            children = data.get("children") or []
            return len(children)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "Reddit mentions fetch failed for %s: %s", query, exc,
            )
            return None


# ---------------------------------------------------------------------------
# Scoring math (pure functions, easy to unit test)
# ---------------------------------------------------------------------------


def _wiki_subscore(views: int | None) -> float | None:
    """Log-scale Wikipedia views into a 0-100 sub-score."""
    if views is None or views < 0:
        return None
    return _clamp(math.log10(1 + views) / _WIKI_LOG_REFERENCE * 100.0)


def _reddit_subscore(mentions: int | None) -> float | None:
    """Log-scale Reddit mentions into a 0-100 sub-score."""
    if mentions is None or mentions < 0:
        return None
    return _clamp(math.log10(1 + mentions) / _REDDIT_LOG_REFERENCE * 100.0)


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def combine_subscores(
    wiki: float | None, reddit: float | None
) -> float | None:
    """Combine the two sub-scores into a 0-100 composite.

    * Both ``None`` -> ``None`` (let the caller fall back).
    * One ``None`` -> the available sub-score (re-normalised so it is not
      penalised by the missing weight).
    * Both available -> 0.6 * wiki + 0.4 * reddit.
    """
    if wiki is None and reddit is None:
        return None
    if wiki is None:
        return round(_clamp(reddit), 2)
    if reddit is None:
        return round(_clamp(wiki), 2)
    return round(
        _clamp(_WIKI_WEIGHT * wiki + _REDDIT_WEIGHT * reddit),
        2,
    )


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


class FanPerceptionResult:
    """Lightweight return container - independent of the ORM."""

    __slots__ = ("breakdown", "computed_at", "score")

    def __init__(self, score: float, breakdown: dict[str, Any],
                 computed_at: datetime):
        self.score = score
        self.breakdown = breakdown
        self.computed_at = computed_at


def _athlete_query_name(athlete: Any) -> str | None:
    """Best-effort extraction of a search string from an athlete object."""
    user = getattr(athlete, "user", None)
    if user is not None:
        full = getattr(user, "full_name", None)
        if full:
            return full
        first = getattr(user, "first_name", None)
        last = getattr(user, "last_name", None)
        if first or last:
            return f"{first or ''} {last or ''}".strip()
    return getattr(athlete, "name", None)


def _is_fresh(row, now: datetime | None = None) -> bool:
    if row is None or row.computed_at is None:
        return False
    now = now or datetime.utcnow()
    return now - row.computed_at < CACHE_TTL


def _load_cached(athlete_id: str):
    """Look up the cache row for ``athlete_id``.  Never raises."""
    try:
        from app.models import FanPerceptionScore
        return FanPerceptionScore.query.filter_by(athlete_id=athlete_id).first()
    except Exception as exc:  # pragma: no cover - DB unavailable in some tests
        logger.debug("FanPerceptionScore lookup failed: %s", exc)
        return None


def _save_cached(athlete_id: str, score: float, breakdown: dict[str, Any],
                 computed_at: datetime) -> None:
    """Insert or update the cached row for ``athlete_id``.  Never raises."""
    try:
        from app import db
        from app.models import FanPerceptionScore

        row = FanPerceptionScore.query.filter_by(athlete_id=athlete_id).first()
        breakdown_json = json.dumps(breakdown, sort_keys=True, default=str)
        if row is None:
            row = FanPerceptionScore(
                athlete_id=athlete_id,
                score=score,
                source_breakdown=breakdown_json,
                computed_at=computed_at,
            )
            db.session.add(row)
        else:
            row.score = score
            row.source_breakdown = breakdown_json
            row.computed_at = computed_at
        db.session.commit()
    except Exception as exc:  # pragma: no cover - DB unavailable in some tests
        logger.warning("FanPerceptionScore save failed: %s", exc)
        try:
            from app import db
            db.session.rollback()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def compute_fan_perception_score(
    athlete: Any,
    *,
    wiki_client: WikipediaPageviewsClient | None = None,
    reddit_client: RedditMentionsClient | None = None,
    use_cache: bool = True,
    persist: bool = True,
) -> float | None:
    """Return a 0-100 fan-perception score for ``athlete``.

    Parameters
    ----------
    athlete:
        ORM ``AthleteProfile`` (must expose ``athlete_id`` and either
        ``user.full_name`` or ``name``).
    wiki_client / reddit_client:
        Optional pre-built clients; mainly for tests to inject mocks.
    use_cache:
        When ``True`` (default), a fresh cache row short-circuits the
        upstream calls.  Pass ``False`` from the nightly job to force a
        refresh.
    persist:
        When ``True`` (default), the result is written to the cache.

    Returns
    -------
    float | None
        ``None`` when no signal could be retrieved AND no cache row
        exists.  Callers must treat ``None`` as "fall back to placeholder".
    """
    athlete_id = getattr(athlete, "athlete_id", None)
    if athlete_id is None:
        return None

    if use_cache:
        cached = _load_cached(athlete_id)
        if _is_fresh(cached):
            try:
                return float(cached.score)
            except (TypeError, ValueError):
                pass

    name = _athlete_query_name(athlete)
    if not name:
        # Without a query string we cannot fetch upstream signals; fall
        # back to a stale cache row if present, else None.
        cached = _load_cached(athlete_id)
        if cached is not None:
            try:
                return float(cached.score)
            except (TypeError, ValueError):
                return None
        return None

    wiki = wiki_client or WikipediaPageviewsClient()
    reddit = reddit_client or RedditMentionsClient()

    views = wiki.get_views(name, days=30)
    mentions = reddit.get_mention_count(name, period="month")

    wiki_score = _wiki_subscore(views)
    reddit_score = _reddit_subscore(mentions)
    combined = combine_subscores(wiki_score, reddit_score)

    if combined is None:
        # All upstream calls failed; serve stale cache if available.
        cached = _load_cached(athlete_id)
        if cached is not None:
            try:
                return float(cached.score)
            except (TypeError, ValueError):
                return None
        return None

    breakdown = {
        "wikipedia": {"views_30d": views, "subscore": wiki_score},
        "reddit": {"mentions_month": mentions, "subscore": reddit_score},
        "weights": {"wikipedia": _WIKI_WEIGHT, "reddit": _REDDIT_WEIGHT},
    }
    if persist:
        _save_cached(athlete_id, combined, breakdown, datetime.utcnow())
    return combined


__all__ = [
    "CACHE_TTL",
    "FanPerceptionResult",
    "RedditMentionsClient",
    "WikipediaPageviewsClient",
    "combine_subscores",
    "compute_fan_perception_score",
]
