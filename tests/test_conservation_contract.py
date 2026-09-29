"""WP-0 conservation provider contract tests."""

import time

import pytest

from copilot_sdk.evolution import (
    CachedAsyncProvider,
    ConservationSafety,
    ScorerBackedProvider,
    evaluate_conservation_safety,
)


def test_scorer_backed_provider_returns_state() -> None:
    class Scorer:
        def get_conservation_state(self):
            return {"status": "GREEN", "verified_count": 4, "correct_count": 3}

    state = ScorerBackedProvider(Scorer(), "purchasing").get_state()

    assert state["status"] == "GREEN"
    assert state["domain"] == "purchasing"
    assert state["verified_count"] == 4
    assert state["source"] == "scorer"
    assert state["overallSafe"] is True


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


def test_provider_normalization_is_fail_closed_for_non_green() -> None:
    provider = ScorerBackedProvider(
        type("Scorer", (), {"get_conservation_state": lambda self: {"status": "CALIBRATING"}})(),
        "trading",
    )
    state = provider.get_state()
    assert state["status"] == "CALIBRATING"
    assert state["overallSafe"] is False
    assert {"domain", "source", "observed_at"} <= set(state)


@pytest.mark.parametrize(
    ("status", "available", "learning", "promotion"),
    [
        ("GREEN", True, True, True),
        ("VERIFIED", True, True, True),
        ("ACTIVE", True, True, True),
        ("PRESEED", True, True, False),
        ("COLD_START", True, True, False),
        ("BOOTSTRAP", True, True, False),
        ("AMBER", True, False, False),
        ("RED", True, False, False),
        ("CALIBRATING", True, False, False),
        ("UNKNOWN", False, False, False),
        ("CONSERVATION_UNAVAILABLE", False, False, False),
    ],
)
def test_operation_aware_conservation_decision_table(
    status: str,
    available: bool,
    learning: bool,
    promotion: bool,
) -> None:
    decision = evaluate_conservation_safety(status.lower())

    assert decision.status == status
    assert decision.available is available
    assert decision.learning_allowed is learning
    assert decision.promotion_allowed is promotion


def test_conservation_decision_precedence_and_compatibility() -> None:
    assert evaluate_conservation_safety(
        {"status": "RED", "overallSafe": True}
    ).promotion_allowed is False
    assert evaluate_conservation_safety({"overallSafe": True}).status == "GREEN"
    assert evaluate_conservation_safety({"overall_safe": False}).status == "RED"


def test_conservation_decision_is_total_and_identity_preserving() -> None:
    malformed_values: list[object] = [None, "", {}, [], 42, {"status": object()}]
    assert all(
        evaluate_conservation_safety(value).available is False
        for value in malformed_values
    )
    decision = ConservationSafety("GREEN", True, True, True, "conservation_safe")
    assert evaluate_conservation_safety(decision) is decision
