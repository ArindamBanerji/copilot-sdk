from __future__ import annotations

import pytest

from copilot_sdk.graph import InMemoryGraphStore


def test_memory_write_decision_returns_id_and_stores_fields():
    store = InMemoryGraphStore()

    decision_id = store.write_decision(
        "invoice-1",
        "alpha",
        "approve",
        0.82,
        {"amount": 0.2},
        metadata={"source": "unit", "created_at": 10.0},
    )

    decision = store.get_decision(decision_id)
    assert decision["decision_id"] == decision_id
    assert decision["entity_id"] == "invoice-1"
    assert decision["category"] == "alpha"
    assert decision["recommended_action"] == "approve"
    assert decision["confidence"] == 0.82
    assert decision["factors"] == {"amount": 0.2}
    assert decision["metadata"]["source"] == "unit"


def test_memory_write_outcome_links_to_decision():
    store = InMemoryGraphStore()
    decision_id = store.write_decision("entity", "alpha", "approve", 0.8, {"risk": 0.1})

    store.write_outcome(decision_id, "approve", True, metadata={"verified_at": 20.0})

    verified = store.get_verified_decisions()
    assert len(verified) == 1
    assert verified[0]["decision_id"] == decision_id
    assert verified[0]["actual_action"] == "approve"
    assert verified[0]["is_correct"] is True
    assert verified[0]["verified_at"] == 20.0


def test_memory_write_outcome_missing_decision_raises():
    store = InMemoryGraphStore()

    with pytest.raises(KeyError):
        store.write_outcome("missing", "approve", True)


def test_memory_counts_empty_and_after_outcomes():
    store = InMemoryGraphStore()
    assert store.count_verified() == 0
    assert store.count_correct() == 0

    first = store.write_decision("e-1", "alpha", "approve", 0.8, {})
    second = store.write_decision("e-2", "alpha", "review", 0.7, {})
    store.write_outcome(first, "approve", True)
    store.write_outcome(second, "approve", False)

    assert store.count_verified() == 2
    assert store.count_correct() == 1


def test_memory_get_decision_missing_returns_none():
    assert InMemoryGraphStore().get_decision("missing") is None


def test_memory_get_decisions_all_category_and_limit():
    store = InMemoryGraphStore()
    store.write_decision("e-1", "alpha", "approve", 0.8, {}, metadata={"created_at": 1.0})
    store.write_decision("e-2", "beta", "review", 0.7, {}, metadata={"created_at": 2.0})
    store.write_decision("e-3", "alpha", "approve", 0.9, {}, metadata={"created_at": 3.0})

    assert [d["entity_id"] for d in store.get_decisions()] == ["e-1", "e-2", "e-3"]
    assert [d["entity_id"] for d in store.get_decisions(category="alpha")] == ["e-1", "e-3"]
    assert [d["entity_id"] for d in store.get_decisions(limit=2)] == ["e-1", "e-2"]


def test_memory_get_all_decisions():
    store = InMemoryGraphStore()
    store.write_decision("e-1", "alpha", "approve", 0.8, {})

    assert len(store.get_all_decisions()) == 1


def test_memory_reset_clears_and_close_noop():
    store = InMemoryGraphStore()
    decision_id = store.write_decision("e-1", "alpha", "approve", 0.8, {})
    store.write_outcome(decision_id, "approve", True)

    store.reset()
    store.close()

    assert store.get_all_decisions() == []
    assert store.count_verified() == 0
