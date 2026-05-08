from __future__ import annotations

import numpy as np
import pytest

from copilot_sdk.scoring.storage import DecisionStore


def save_sample_decision(store, decision_id="d-1", category="alpha", created_at=1000.0):
    store.save_decision(
        decision_id=decision_id,
        domain="mock",
        category=category,
        category_index={"alpha": 0, "beta": 1, "gamma": 2}[category],
        factors={"amount": 0.2, "risk": 0.4, "history": 0.6},
        factor_vector=[0.2, 0.4, 0.6],
        recommended_action="approve",
        recommended_index=0,
        confidence=0.75,
        probabilities=[0.75, 0.25],
        created_at=created_at,
    )


def test_save_get_decision_roundtrip(store):
    save_sample_decision(store)

    decision = store.get_decision("d-1")

    assert decision["decision_id"] == "d-1"
    assert decision["domain"] == "mock"
    assert decision["category"] == "alpha"
    assert decision["factors"] == {"amount": 0.2, "risk": 0.4, "history": 0.6}
    assert decision["factor_vector"] == [0.2, 0.4, 0.6]
    assert decision["probabilities"] == [0.75, 0.25]


def test_save_outcome_and_counts(store):
    save_sample_decision(store, "d-1")
    save_sample_decision(store, "d-2")

    store.save_outcome(
        decision_id="d-1",
        actual_action="approve",
        actual_index=0,
        is_correct=True,
        verified_at=2000.0,
    )
    store.save_outcome(
        decision_id="d-2",
        actual_action="review",
        actual_index=1,
        is_correct=False,
        verified_at=2001.0,
    )

    assert store.count_verified() == 2
    assert store.count_correct() == 1


def test_get_verified_decisions_joins_only_outcomes(store):
    save_sample_decision(store, "verified")
    save_sample_decision(store, "unverified")
    store.save_outcome(
        decision_id="verified",
        actual_action="approve",
        actual_index=0,
        is_correct=True,
    )

    verified = store.get_verified_decisions()

    assert [d["decision_id"] for d in verified] == ["verified"]
    assert verified[0]["is_correct"] is True
    assert verified[0]["actual_action"] == "approve"


def test_save_load_latest_centroids(store):
    first = np.zeros((3, 2, 3), dtype=float)
    latest = np.ones((3, 2, 3), dtype=float)

    store.save_centroids(first, iks=1.5)
    store.save_centroids(latest, iks=7.5)

    np.testing.assert_allclose(store.load_latest_centroids(), latest)
    checkpoints = store.get_centroid_checkpoints()
    assert checkpoints[-1]["iks"] == 7.5


def test_empty_latest_centroids_returns_none(store):
    assert store.load_latest_centroids() is None


def test_get_missing_decision_raises_key_error(store):
    with pytest.raises(KeyError):
        store.get_decision("missing")


def test_count_categories_with_n(store):
    for index in range(3):
        save_sample_decision(store, f"alpha-{index}", category="alpha", created_at=1000.0 + index)
        store.save_outcome(
            decision_id=f"alpha-{index}",
            actual_action="approve",
            actual_index=0,
            is_correct=True,
        )
    for index in range(2):
        save_sample_decision(store, f"beta-{index}", category="beta", created_at=1100.0 + index)
        store.save_outcome(
            decision_id=f"beta-{index}",
            actual_action="review",
            actual_index=1,
            is_correct=False,
        )

    assert store.count_categories_with_n(3) == 1
    assert store.count_categories_with_n(2) == 2


def test_decisions_persist_across_store_reopen(temp_db):
    store = DecisionStore(temp_db)
    save_sample_decision(store, "persisted")
    store.close()

    reopened = DecisionStore(temp_db)
    try:
        assert reopened.get_decision("persisted")["decision_id"] == "persisted"
    finally:
        reopened.close()
