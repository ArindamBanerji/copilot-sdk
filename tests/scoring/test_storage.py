from __future__ import annotations

import sqlite3

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


def test_decision_store_get_centroid_checkpoints_metadata(store):
    centroids = np.ones((2, 2), dtype=float)

    store.save_centroids(
        centroids,
        iks=2.5,
        decision_id="decision-1",
        category="alpha",
        metadata={"source": "unit"},
    )

    checkpoints = store.get_centroid_checkpoints(limit=1)
    assert checkpoints[0]["decision_id"] == "decision-1"
    assert checkpoints[0]["category"] == "alpha"
    assert checkpoints[0]["iks"] == 2.5
    assert checkpoints[0]["metadata"] == {"source": "unit"}
    np.testing.assert_allclose(checkpoints[0]["centroids"], centroids)


def test_decision_store_save_generates_checkpoint_time(store):
    store.save_centroids(np.ones((1, 1)), decision_id="decision-1", category="alpha")

    checkpoint = store.get_centroid_checkpoints(limit=1)[0]

    assert checkpoint["checkpoint_time"].endswith("Z")
    assert checkpoint["decision_time_start"] is None
    assert checkpoint["decision_time_end"] is None


def test_decision_store_save_with_bitemporal_stores_fields(store):
    centroids = np.ones((1, 1))

    store.save_centroids(
        centroids,
        decision_id="decision-1",
        category="alpha",
        decision_time_start="2026-05-01T00:00:00Z",
        decision_time_end="2026-05-01T01:00:00Z",
        checkpoint_time="2026-05-01T02:00:00Z",
    )

    checkpoint = store.get_centroid_checkpoints(limit=1)[0]
    assert checkpoint["decision_time_start"] == "2026-05-01T00:00:00Z"
    assert checkpoint["decision_time_end"] == "2026-05-01T01:00:00Z"
    assert checkpoint["checkpoint_time"] == "2026-05-01T02:00:00Z"


def test_decision_store_checkpoint_time_filter(store):
    store.save_centroids(
        np.ones((1, 1)),
        decision_id="old",
        category="alpha",
        checkpoint_time="2026-05-01T00:00:00Z",
    )
    store.save_centroids(
        np.ones((1, 1)),
        decision_id="new",
        category="alpha",
        checkpoint_time="2026-05-02T00:00:00Z",
    )

    checkpoints = store.get_centroid_checkpoints(
        checkpoint_time_start="2026-05-01T12:00:00Z",
    )

    assert [checkpoint["decision_id"] for checkpoint in checkpoints] == ["new"]


def test_decision_store_decision_time_filter(store):
    store.save_centroids(
        np.ones((1, 1)),
        decision_id="outside",
        category="alpha",
        decision_time_start="2026-05-01T00:00:00Z",
        decision_time_end="2026-05-03T00:00:00Z",
    )
    store.save_centroids(
        np.ones((1, 1)),
        decision_id="inside",
        category="alpha",
        decision_time_start="2026-05-02T00:00:00Z",
        decision_time_end="2026-05-02T12:00:00Z",
    )

    checkpoints = store.get_centroid_checkpoints(
        decision_time_start="2026-05-01T12:00:00Z",
        decision_time_end="2026-05-02T18:00:00Z",
    )

    assert [checkpoint["decision_id"] for checkpoint in checkpoints] == ["inside"]


def test_decision_store_temporal_filters_exclude_null(store):
    store.save_centroids(np.ones((1, 1)), decision_id="null-range", category="alpha")
    store.save_centroids(
        np.ones((1, 1)),
        decision_id="with-range",
        category="alpha",
        decision_time_start="2026-05-02T00:00:00Z",
        decision_time_end="2026-05-02T12:00:00Z",
    )

    checkpoints = store.get_centroid_checkpoints(
        decision_time_start="2026-05-01T00:00:00Z",
    )

    assert [checkpoint["decision_id"] for checkpoint in checkpoints] == ["with-range"]


def test_decision_store_category_filter(store):
    store.save_centroids(np.ones((1, 1)), decision_id="alpha-1", category="alpha")
    store.save_centroids(np.ones((1, 1)), decision_id="beta-1", category="beta")

    checkpoints = store.get_centroid_checkpoints(category="beta")

    assert [checkpoint["decision_id"] for checkpoint in checkpoints] == ["beta-1"]


def test_decision_store_migration_adds_bitemporal_columns(tmp_path):
    db_path = tmp_path / "old.sqlite"
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(
            """
            CREATE TABLE decisions (
                decision_id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                category TEXT NOT NULL,
                category_index INTEGER NOT NULL,
                factors_json TEXT NOT NULL,
                factor_vector_json TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                recommended_index INTEGER NOT NULL,
                confidence REAL NOT NULL,
                probabilities_json TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE outcomes (
                decision_id TEXT PRIMARY KEY REFERENCES decisions(decision_id),
                actual_action TEXT NOT NULL,
                actual_index INTEGER NOT NULL,
                is_correct INTEGER NOT NULL,
                verified_at REAL NOT NULL
            );
            CREATE TABLE centroid_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                centroids_json TEXT NOT NULL,
                decisions_count INTEGER NOT NULL,
                iks REAL NOT NULL,
                created_at REAL NOT NULL
            );
            """
        )
        connection.commit()
    finally:
        connection.close()

    migrated = DecisionStore(db_path)
    try:
        columns = {
            row["name"]
            for row in migrated.connection.execute("PRAGMA table_info(centroid_checkpoints)")
        }
        indexes = {
            row["name"]
            for row in migrated.connection.execute("PRAGMA index_list(centroid_checkpoints)")
        }
    finally:
        migrated.close()

    assert {"decision_time_start", "decision_time_end", "checkpoint_time"} <= columns
    assert {
        "idx_cc_checkpoint_time",
        "idx_cc_decision_time",
        "idx_cc_category",
    } <= indexes


def test_decision_store_migration_idempotent(tmp_path):
    db_path = tmp_path / "graph.sqlite"
    store = DecisionStore(db_path)
    try:
        store._ensure_centroid_columns()
        store._ensure_centroid_columns()
        store.connection.commit()
    finally:
        store.close()


def test_decision_store_get_centroid_checkpoints_limit(store):
    for index in range(3):
        store.save_centroids(
            np.full((1, 1), float(index)),
            decision_id=f"decision-{index}",
            category="alpha",
        )

    checkpoints = store.get_centroid_checkpoints(limit=2)

    assert [checkpoint["decision_id"] for checkpoint in checkpoints] == [
        "decision-1",
        "decision-2",
    ]


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
