"""Unit tests for :mod:`app.services.fan_perception_service`.

All upstream HTTP calls are mocked with the ``responses`` library so the
suite never touches Wikipedia or Reddit.  The cache layer is monkey-
patched onto in-memory dicts so we do not need a Flask app or a database
to exercise the public API.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
import responses

_SERVICE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "app",
        "services",
        "fan_perception_service.py",
    )
)


def _load_service():
    """Load the fan-perception service without importing the whole app."""
    if "fan_perception_service" in sys.modules:
        return sys.modules["fan_perception_service"]
    spec = importlib.util.spec_from_file_location(
        "fan_perception_service", _SERVICE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    # Register *before* exec so dataclass / typing introspection works.
    sys.modules["fan_perception_service"] = module
    spec.loader.exec_module(module)
    return module


fps = _load_service()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _athlete(name="LeBron James", aid="ath-1"):
    user = SimpleNamespace(full_name=name, first_name=None, last_name=None)
    return SimpleNamespace(athlete_id=aid, user=user, name=name)


@pytest.fixture
def in_memory_cache(monkeypatch):
    """Replace the DB-backed cache with an in-memory dict."""
    store = {}

    def _load(athlete_id):
        return store.get(athlete_id)

    def _save(athlete_id, score, breakdown, computed_at):
        store[athlete_id] = SimpleNamespace(
            athlete_id=athlete_id,
            score=score,
            source_breakdown=json.dumps(breakdown, default=str),
            computed_at=computed_at,
        )

    monkeypatch.setattr(fps, "_load_cached", _load)
    monkeypatch.setattr(fps, "_save_cached", _save)
    return store


# ---------------------------------------------------------------------------
# Pure scoring math
# ---------------------------------------------------------------------------


def test_wiki_subscore_zero_for_no_views():
    assert fps._wiki_subscore(0) == 0.0


def test_wiki_subscore_one_million_pegs_to_100():
    # log10(1+1_000_000) / 6 * 100 == 100
    assert fps._wiki_subscore(1_000_000) == pytest.approx(100.0, abs=0.01)


def test_wiki_subscore_clamps_at_top():
    assert fps._wiki_subscore(10**12) == 100.0


def test_wiki_subscore_none_for_invalid():
    assert fps._wiki_subscore(None) is None
    assert fps._wiki_subscore(-5) is None


def test_reddit_subscore_zero_for_no_mentions():
    assert fps._reddit_subscore(0) == 0.0


def test_reddit_subscore_one_hundred_pegs_to_100():
    assert fps._reddit_subscore(100) == pytest.approx(100.0, abs=0.01)


def test_combine_returns_none_when_both_none():
    assert fps.combine_subscores(None, None) is None


def test_combine_uses_only_wiki_when_reddit_missing():
    assert fps.combine_subscores(80.0, None) == 80.0


def test_combine_uses_only_reddit_when_wiki_missing():
    assert fps.combine_subscores(None, 60.0) == 60.0


def test_combine_weighted_when_both_present():
    # 0.6 * 80 + 0.4 * 60 = 48 + 24 = 72
    assert fps.combine_subscores(80.0, 60.0) == 72.0


def test_combine_clamps_to_range():
    # Even crazy inputs should stay within [0, 100]
    assert 0.0 <= fps.combine_subscores(200.0, -50.0) <= 100.0


# ---------------------------------------------------------------------------
# WikipediaPageviewsClient
# ---------------------------------------------------------------------------


@responses.activate
def test_wikipedia_client_sums_daily_views():
    payload = {
        "items": [
            {"views": 100},
            {"views": 200},
            {"views": 300},
        ]
    }
    # Match any wikimedia URL - only one call is expected.
    responses.add(
        responses.GET,
        url=responses.matchers.re.compile(
            r"https://wikimedia\.org/api/rest_v1/metrics/.*"
        ),
        json=payload,
        status=200,
    )
    client = fps.WikipediaPageviewsClient()
    assert client.get_views("LeBron James", days=3) == 600


@responses.activate
def test_wikipedia_client_returns_none_on_404():
    responses.add(
        responses.GET,
        url=responses.matchers.re.compile(
            r"https://wikimedia\.org/api/rest_v1/metrics/.*"
        ),
        status=404,
    )
    assert fps.WikipediaPageviewsClient().get_views("Nonexistent") is None


@responses.activate
def test_wikipedia_client_returns_none_on_network_error():
    responses.add(
        responses.GET,
        url=responses.matchers.re.compile(
            r"https://wikimedia\.org/api/rest_v1/metrics/.*"
        ),
        body=ConnectionError("simulated network error"),
    )
    assert fps.WikipediaPageviewsClient().get_views("LeBron") is None


def test_wikipedia_client_returns_none_for_blank_title():
    assert fps.WikipediaPageviewsClient().get_views("") is None


# ---------------------------------------------------------------------------
# RedditMentionsClient
# ---------------------------------------------------------------------------


@responses.activate
def test_reddit_client_counts_children():
    payload = {
        "data": {
            "children": [
                {"data": {"title": "post 1"}},
                {"data": {"title": "post 2"}},
                {"data": {"title": "post 3"}},
            ]
        }
    }
    responses.add(
        responses.GET,
        url="https://www.reddit.com/search.json",
        json=payload,
        status=200,
    )
    assert fps.RedditMentionsClient().get_mention_count("LeBron") == 3


@responses.activate
def test_reddit_client_returns_none_on_500():
    responses.add(
        responses.GET,
        url="https://www.reddit.com/search.json",
        status=500,
    )
    assert fps.RedditMentionsClient().get_mention_count("LeBron") is None


def test_reddit_client_returns_none_for_blank_query():
    assert fps.RedditMentionsClient().get_mention_count("") is None


# ---------------------------------------------------------------------------
# compute_fan_perception_score (integration: math + cache + clients)
# ---------------------------------------------------------------------------


class _FakeWiki:
    def __init__(self, value):
        self.calls = 0
        self._value = value

    def get_views(self, name, days=30):
        self.calls += 1
        return self._value


class _FakeReddit:
    def __init__(self, value):
        self.calls = 0
        self._value = value

    def get_mention_count(self, name, period="month"):
        self.calls += 1
        return self._value


def test_compute_returns_combined_score(in_memory_cache):
    a = _athlete()
    score = fps.compute_fan_perception_score(
        a,
        wiki_client=_FakeWiki(1_000_000),
        reddit_client=_FakeReddit(100),
    )
    # Both maxed -> ~100
    assert score == pytest.approx(100.0, abs=0.01)


def test_compute_returns_none_when_both_sources_fail(in_memory_cache):
    a = _athlete()
    score = fps.compute_fan_perception_score(
        a,
        wiki_client=_FakeWiki(None),
        reddit_client=_FakeReddit(None),
    )
    assert score is None


def test_compute_uses_only_wiki_when_reddit_unavailable(in_memory_cache):
    a = _athlete()
    score = fps.compute_fan_perception_score(
        a,
        wiki_client=_FakeWiki(1_000_000),
        reddit_client=_FakeReddit(None),
    )
    # Wiki maxes, reddit missing -> wiki sub-score (100)
    assert score == pytest.approx(100.0, abs=0.01)


def test_compute_writes_to_cache(in_memory_cache):
    a = _athlete()
    fps.compute_fan_perception_score(
        a,
        wiki_client=_FakeWiki(1000),
        reddit_client=_FakeReddit(10),
    )
    assert "ath-1" in in_memory_cache
    cached = in_memory_cache["ath-1"]
    assert 0.0 <= float(cached.score) <= 100.0
    breakdown = json.loads(cached.source_breakdown)
    assert "wikipedia" in breakdown
    assert "reddit" in breakdown


def test_compute_hits_cache_when_fresh(in_memory_cache):
    a = _athlete()
    in_memory_cache["ath-1"] = SimpleNamespace(
        athlete_id="ath-1",
        score=42.0,
        source_breakdown="{}",
        computed_at=datetime.utcnow(),
    )
    wiki = _FakeWiki(1000)
    reddit = _FakeReddit(10)
    score = fps.compute_fan_perception_score(
        a, wiki_client=wiki, reddit_client=reddit
    )
    assert score == 42.0
    # Cache hit means no upstream calls.
    assert wiki.calls == 0
    assert reddit.calls == 0


def test_compute_misses_cache_when_stale(in_memory_cache):
    a = _athlete()
    in_memory_cache["ath-1"] = SimpleNamespace(
        athlete_id="ath-1",
        score=42.0,
        source_breakdown="{}",
        computed_at=datetime.utcnow() - timedelta(days=2),
    )
    wiki = _FakeWiki(1_000_000)
    reddit = _FakeReddit(100)
    score = fps.compute_fan_perception_score(
        a, wiki_client=wiki, reddit_client=reddit
    )
    assert score == pytest.approx(100.0, abs=0.01)
    assert wiki.calls == 1
    assert reddit.calls == 1


def test_compute_falls_back_to_stale_cache_on_upstream_failure(in_memory_cache):
    a = _athlete()
    in_memory_cache["ath-1"] = SimpleNamespace(
        athlete_id="ath-1",
        score=42.0,
        source_breakdown="{}",
        computed_at=datetime.utcnow() - timedelta(days=10),
    )
    score = fps.compute_fan_perception_score(
        a,
        wiki_client=_FakeWiki(None),
        reddit_client=_FakeReddit(None),
    )
    assert score == 42.0


def test_compute_use_cache_false_forces_refresh(in_memory_cache):
    a = _athlete()
    in_memory_cache["ath-1"] = SimpleNamespace(
        athlete_id="ath-1",
        score=42.0,
        source_breakdown="{}",
        computed_at=datetime.utcnow(),
    )
    wiki = _FakeWiki(1_000_000)
    reddit = _FakeReddit(100)
    score = fps.compute_fan_perception_score(
        a,
        wiki_client=wiki, reddit_client=reddit,
        use_cache=False,
    )
    assert wiki.calls == 1
    assert reddit.calls == 1
    assert score == pytest.approx(100.0, abs=0.01)


def test_compute_returns_none_when_no_athlete_id(in_memory_cache):
    a = SimpleNamespace(athlete_id=None, user=None, name="x")
    assert fps.compute_fan_perception_score(
        a,
        wiki_client=_FakeWiki(1000),
        reddit_client=_FakeReddit(10),
    ) is None


def test_compute_returns_none_when_no_query_name(in_memory_cache):
    a = SimpleNamespace(athlete_id="ath-2", user=None, name=None)
    assert fps.compute_fan_perception_score(
        a,
        wiki_client=_FakeWiki(1000),
        reddit_client=_FakeReddit(10),
    ) is None


def test_persist_false_does_not_write_cache(in_memory_cache):
    a = _athlete()
    fps.compute_fan_perception_score(
        a,
        wiki_client=_FakeWiki(1000),
        reddit_client=_FakeReddit(10),
        persist=False,
    )
    assert "ath-1" not in in_memory_cache
