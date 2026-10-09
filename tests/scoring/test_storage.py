from __future__ import annotations

import sqlite3
from datetime import datetime

import numpy as np
import pytest

from tests.graph_store_test_helpers import make_memory_store


def save_sample_decision(store, decision_id="d-1", category="alpha", created_at=1000.0):
    store.write_decision(
        "mock",
        category=category,
        action="approve",
        confidence=0.75,
        factors={"amount": 0.2, "risk": 0.4, "history": 0.6},
        metadata={
            "decision_id": decision_id,
            "category_index": {"alpha": 0, "beta": 1, "gamma": 2}[category],
            "factor_vector": [0.2, 0.4, 0.6],
            "recommended_index": 0,
            "probabilities": [0.75, 0.25],
            "created_at": created_at,
        },
    )


def test_save_get_decision_roundtrip(store):
    save_sample_decision(store)

    decision = store.get_decision("d-1", domain="mock")

    assert decision["decision_id"] == "d-1"
    assert decision["domain"] == "mock"
    assert decision["category"] == "alpha"
    assert {key: decision["factors"][key] for key in ("amount", "risk", "history")} == {
        "amount": 0.2,
        "risk": 0.4,
        "history": 0.6,
    }
    assert decision["factor_vector"] == [0.2, 0.4, 0.6]
    assert decision["probabilities"] == [0.75, 0.25]


def test_save_outcome_and_counts(store):
    save_sample_decision(store, "d-1")
    save_sample_decision(store, "d-2")

    store.write_outcome(
        decision_id="d-1",
        actual_action="approve",
        is_correct=True,
        metadata={"actual_index": 0, "verified_at": 2000.0},
        domain="mock",
    )
    store.write_outcome(
        decision_id="d-2",
        actual_action="review",
        is_correct=False,
        metadata={"actual_index": 1, "verified_at": 2001.0},
        domain="mock",
    )

    assert store.count_verified("mock") == 2
    assert store.count_correct("mock") == 1


def test_get_verified_decisions_joins_only_outcomes(store):
    save_sample_decision(store, "verified")
    save_sample_decision(store, "unverified")
    store.write_outcome(
        decision_id="verified",
        actual_action="approve",
        is_correct=True,
        metadata={"actual_index": 0},
        domain="mock",
    )

    verified = store.get_verified_decisions("mock")

    assert [d["decision_id"] for d in verified] == ["verified"]
    assert verified[0]["is_correct"] is True
    assert verified[0]["actual_action"] == "approve"


def test_save_load_latest_centroids(store):
    first = np.zeros((3, 2, 3), dtype=float)
    latest = np.ones((3, 2, 3), dtype=float)

    store.save_centroids("mock", "", first, metadata={"iks": 1.5}, created_at=1.0)
    store.save_centroids("mock", "", latest, metadata={"iks": 7.5}, created_at=2.0)

    np.testing.assert_allclose(store.load_latest_centroids("mock"), latest)
    checkpoints = store.get_centroid_checkpoints("mock")
    assert checkpoints[0]["iks"] == 7.5


def test_decision_store_get_centroid_checkpoints_metadata(store):
    centroids = np.ones((2, 2), dtype=float)

    store.save_centroids(
        "mock",
        "alpha",
        centroids,
        decision_id="decision-1",
        metadata={"iks": 2.5, "source": "unit"},
    )

    checkpoints = store.get_centroid_checkpoints("mock", limit=1)
    assert checkpoints[0]["decision_id"] == "decision-1"
    assert checkpoints[0]["category"] == "alpha"
    assert checkpoints[0]["iks"] == 2.5
    assert checkpoints[0]["metadata"] == {"iks": 2.5, "source": "unit"}
    np.testing.assert_allclose(checkpoints[0]["centroids"], centroids)


def test_decision_store_save_generates_checkpoint_time(store):
    store.save_centroids("mock", "alpha", np.ones((1, 1)), decision_id="decision-1")

    checkpoint = store.get_centroid_checkpoints("mock", limit=1)[0]

    assert isinstance(checkpoint["checkpoint_time"], str)
    datetime.fromisoformat(checkpoint["checkpoint_time"].replace("Z", "+00:00"))
    assert checkpoint["decision_time_start"] is None
    assert checkpoint["decision_time_end"] is None


def test_decision_store_save_with_bitemporal_stores_fields(store):
    centroids = np.ones((1, 1))

    store.save_centroids(
        "mock",
        "alpha",
        centroids,
        decision_id="decision-1",
        decision_time_start="2026-05-01T00:00:00Z",
        decision_time_end="2026-05-01T01:00:00Z",
        checkpoint_time="2026-05-01T02:00:00Z",
    )

    checkpoint = store.get_centroid_checkpoints("mock", limit=1)[0]
    assert checkpoint["decision_time_start"] == "2026-05-01T00:00:00Z"
    assert checkpoint["decision_time_end"] == "2026-05-01T01:00:00Z"
    assert checkpoint["checkpoint_time"] == "2026-05-01T02:00:00Z"


def test_decision_store_checkpoint_time_filter(store):
    store.save_centroids(
        "mock",
        "alpha",
        np.ones((1, 1)),
        decision_id="old",
        checkpoint_time="2026-05-01T00:00:00Z",
    )
    store.save_centroids(
        "mock",
        "alpha",
        np.ones((1, 1)),
        decision_id="new",
        checkpoint_time="2026-05-02T00:00:00Z",
    )

    checkpoints = store.get_centroid_checkpoints(
        "mock",
        checkpoint_time_start="2026-05-01T12:00:00Z",
    )

    assert [checkpoint["decision_id"] for checkpoint in checkpoints] == ["new"]


def test_decision_store_decision_time_filter(store):
    store.save_centroids(
        "mock",
        "alpha",
        np.ones((1, 1)),
        decision_id="outside",
        decision_time_start="2026-05-01T00:00:00Z",
        decision_time_end="2026-05-03T00:00:00Z",
    )
    store.save_centroids(
        "mock",
        "alpha",
        np.ones((1, 1)),
        decision_id="inside",
        decision_time_start="2026-05-02T00:00:00Z",
        decision_time_end="2026-05-02T12:00:00Z",
    )

    checkpoints = store.get_centroid_checkpoints(
        "mock",
        decision_time_start="2026-05-01T12:00:00Z",
        decision_time_end="2026-05-02T18:00:00Z",
    )

    assert [checkpoint["decision_id"] for checkpoint in checkpoints] == ["inside"]


def test_decision_store_temporal_filters_exclude_null(store):
    store.save_centroids("mock", "alpha", np.ones((1, 1)), decision_id="null-range")
    store.save_centroids(
        "mock",
        "alpha",
        np.ones((1, 1)),
        decision_id="with-range",
        decision_time_start="2026-05-02T00:00:00Z",
        decision_time_end="2026-05-02T12:00:00Z",
    )

    checkpoints = store.get_centroid_checkpoints(
        "mock",
        decision_time_start="2026-05-01T00:00:00Z",
    )

    assert [checkpoint["decision_id"] for checkpoint in checkpoints] == ["with-range"]


def test_decision_store_category_filter(store):
    store.save_centroids("mock", "alpha", np.ones((1, 1)), decision_id="alpha-1")
    store.save_centroids("mock", "beta", np.ones((1, 1)), decision_id="beta-1")

    checkpoints = store.get_centroid_checkpoints("mock", category="beta")

    assert [checkpoint["decision_id"] for checkpoint in checkpoints] == ["beta-1"]






def test_decision_store_get_centroid_checkpoints_limit(store):
    for index in range(3):
        store.save_centroids(
            "mock",
            "alpha",
            np.full((1, 1), float(index)),
            decision_id=f"decision-{index}",
            created_at=float(index + 1),
        )

    checkpoints = store.get_centroid_checkpoints("mock", limit=2)

    assert [checkpoint["decision_id"] for checkpoint in checkpoints] == [
        "decision-1",
        "decision-2",
    ]


def test_empty_latest_centroids_returns_none(store):
    assert store.load_latest_centroids("mock") is None


def test_get_missing_decision_raises_key_error(store):
    assert store.get_decision("missing", domain="mock") is None


def test_count_categories_with_n(store):
    for index in range(3):
        save_sample_decision(store, f"alpha-{index}", category="alpha", created_at=1000.0 + index)
        store.write_outcome(
            decision_id=f"alpha-{index}",
            actual_action="approve",
            is_correct=True,
            metadata={"actual_index": 0},
            domain="mock",
        )
    for index in range(2):
        save_sample_decision(store, f"beta-{index}", category="beta", created_at=1100.0 + index)
        store.write_outcome(
            decision_id=f"beta-{index}",
            actual_action="review",
            is_correct=False,
            metadata={"actual_index": 1},
            domain="mock",
        )

    assert store.count_categories_with_n("mock", 3) == 1
    assert store.count_categories_with_n("mock", 2) == 2



