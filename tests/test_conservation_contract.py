"""WP-0 conservation provider contract tests."""

import time

from copilot_sdk.evolution import CachedAsyncProvider, ScorerBackedProvider


def test_scorer_backed_provider_returns_state() -> None:
    class Scorer:
        def get_conservation_state(self):
            return {"status": "GREEN", "verified_count": 4, "correct_count": 3}

    state = ScorerBackedProvider(Scorer(), "purchasing").get_state()

    assert state["status"] == "GREEN"
    assert state["domain"] == "purchasing"
    assert state["verified_count"] == 4
    assert state["source"] == "scorer"


def test_scorer_backed_provider_fails_to_unknown() -> None:
    class BrokenScorer:
        def get_conservation_state(self):
            raise RuntimeError("graph unavailable")

    state = ScorerBackedProvider(BrokenScorer(), "dataops").get_state()

    assert state["status"] == "UNKNOWN"
    assert state["domain"] == "dataops"


def test_cached_async_provider_freshness() -> None:
    snapshots = iter(
        [
            {"status": "GREEN"},
            {"status": "AMBER"},
        ]
    )
    provider = CachedAsyncProvider(lambda: next(snapshots), freshness_ttl=0.1)

    first = provider.get_state()
    assert first["status"] == "GREEN"
    time.sleep(0.2)
    second = provider.get_state()
    assert second["status"] == "AMBER"
    assert first["observed_at"] != second["observed_at"]


def test_cached_async_provider_stale_unknown() -> None:
    def broken_snapshot():
        raise RuntimeError("health monitor unavailable")

    state = CachedAsyncProvider(broken_snapshot, freshness_ttl=0.0).get_state()

    assert state["status"] == "UNKNOWN"
    assert state["reason"] == "stale_or_error"
