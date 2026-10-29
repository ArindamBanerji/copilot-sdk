from __future__ import annotations

from typing import Any

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from scripts.preseed_trading_scenarios import (
    DECISION_COUNT,
    generate_scenario,
    seed_scenario,
    verify_scenario,
)


def _accuracy(scenario: str) -> float:
    rows = generate_scenario(scenario)
    return sum(1 for row in rows if row.is_correct) / len(rows)


def _snapshot(store: InMemoryGraphStore) -> list[dict[str, Any]]:
    rows = store.get_verified_decisions("trading", chronological=True)
    return [
        {
            "decision_id": row["decision_id"],
            "category": row["category"],
            "recommended_action": row["recommended_action"],
            "actual_action": row["actual_action"],
            "is_correct": row["is_correct"],
            "factor_vector": row["factor_vector"],
            "confidence": row["confidence"],
            "created_at": row["created_at"],
            "metadata": row["metadata"],
        }
        for row in rows
    ]


def test_healthy_scenario_accuracy() -> None:
    store = InMemoryGraphStore(domain="trading")
    summary = seed_scenario(store, "healthy")

    assert 0.73 <= _accuracy("healthy") <= 0.77
    assert 0.73 <= summary.accuracy <= 0.77
    assert summary.iks_estimate >= 70.0
    verify_scenario(store, summary)


def test_degraded_scenario_accuracy() -> None:
    store = InMemoryGraphStore(domain="trading")
    summary = seed_scenario(store, "degraded")

    assert 0.43 <= _accuracy("degraded") <= 0.50
    assert 0.43 <= summary.accuracy <= 0.50
    degraded = {row.category: row.accuracy for row in summary.categories}
    assert 0.38 <= degraded["scalp_intraday"] <= 0.42
    assert 0.38 <= degraded["income_strategy"] <= 0.42
    verify_scenario(store, summary)


def test_reset_clears_previous_trading_decisions_only() -> None:
    store = InMemoryGraphStore(domain="trading")
    old_id = store.write_decision(
        "trading",
        "trend_following",
        "strong_execution",
        0.8,
        {"signal_alignment": 0.5},
        metadata={"decision_id": "old-trading", "created_at": 10.0},
    )
    purchasing_id = store.write_decision(
        "purchasing",
        "staples",
        "order_as_planned",
        0.8,
        {"expected_demand": 0.5},
        metadata={"decision_id": "keep-purchasing", "created_at": 10.0},
    )

    summary = seed_scenario(store, "healthy", reset=True)

    assert summary.archived == 1
    assert store.get_decision(old_id, "trading") is None
    assert store.count_decisions("trading") == DECISION_COUNT
    assert store.get_decision(purchasing_id, "purchasing") is not None
    assert store.count_decisions("purchasing") == 1


def test_scenario_is_deterministic() -> None:
    first = InMemoryGraphStore(domain="trading")
    second = InMemoryGraphStore(domain="trading")

    first_summary = seed_scenario(first, "degraded")
    second_summary = seed_scenario(second, "degraded")

    assert first_summary == second_summary
    assert _snapshot(first) == _snapshot(second)
