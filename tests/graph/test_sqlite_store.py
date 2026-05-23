from __future__ import annotations

import sqlite3
import threading

import numpy as np

from copilot_sdk.graph import SQLiteGraphStore


def _write(store: SQLiteGraphStore, domain: str, index: int, category: str = "alpha") -> str:
    return store.write_decision(
        domain,
        category,
        "approve",
        0.82,
        {"amount": float(index), "risk": 0.3},
        metadata={
            "decision_id": f"{domain}-{index}",
            "entity_id": f"entity-{index}",
            "created_at": float(index),
            "category_index": 2,
            "recommended_index": 1,
        },
    )


def _columns(db_path, table: str) -> set[str]:
    connection = sqlite3.connect(db_path)
    try:
        return {
            row[1]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
    finally:
        connection.close()


def test_sqlite_write_decision_returns_id_and_persists(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")

    decision_id = store.write_decision(
        "mock",
        "alpha",
        "approve",
        0.82,
        {"amount": 0.2, "risk": 0.3},
        metadata={"entity_id": "invoice-1", "created_at": 10.0, "category_index": 2, "recommended_index": 1},
    )

    decision = store.get_decision(decision_id)
    assert decision["decision_id"] == decision_id
    assert decision["domain"] == "mock"
    assert decision["entity_id"] == "invoice-1"
    assert decision["category"] == "alpha"
    assert decision["recommended_action"] == "approve"
    assert decision["confidence"] == 0.82
    assert decision["factors"]["amount"] == 0.2
    assert decision["category_index"] == 2
    assert decision["recommended_index"] == 1


def test_sqlite_write_outcomes_and_counts(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    first = _write(store, "mock", 1)
    second = _write(store, "mock", 2, category="beta")

    store.write_outcome(first, "approve", True, metadata={"actual_index": 0, "verified_at": 20.0})
    store.write_outcome(second, "approve", False, metadata={"actual_index": 1, "verified_at": 21.0})

    assert store.count_verified("mock") == 2
    assert store.count_correct("mock") == 1
    verified = store.get_verified_decisions("mock")
    assert set(decision["decision_id"] for decision in verified) == {first, second}
    by_id = {d["decision_id"]: d for d in verified}
    assert by_id[first]["actual_action"] == "approve"
    assert by_id[first]["is_correct"] is True


def test_sqlite_get_decision_missing_returns_none(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")

    assert store.get_decision("missing") is None


def test_sqlite_get_decisions_by_category_and_limit(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    _write(store, "mock", 1, category="alpha")
    _write(store, "mock", 2, category="beta")
    _write(store, "mock", 3, category="alpha")

    assert [d["entity_id"] for d in store.get_decisions("mock")] == ["entity-1", "entity-2", "entity-3"]
    assert [d["entity_id"] for d in store.get_decisions("mock", category="alpha")] == ["entity-1", "entity-3"]
    assert [d["entity_id"] for d in store.get_decisions("mock", limit=2)] == ["entity-1", "entity-2"]


def test_domain_isolation_same_file(tmp_path):
    db_path = tmp_path / "graph.sqlite"
    store = SQLiteGraphStore(db_path)
    first = _write(store, "alpha-domain", 1)
    second = _write(store, "beta-domain", 2)
    store.write_outcome(first, "approve", True)
    store.write_outcome(second, "approve", False)

    assert [d["decision_id"] for d in store.get_all_decisions("alpha-domain")] == [first]
    assert [d["decision_id"] for d in store.get_all_decisions("beta-domain")] == [second]
    assert store.count_verified("alpha-domain") == 1
    assert store.count_correct("alpha-domain") == 1
    assert store.count_correct("beta-domain") == 0


def test_count_decisions(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    _write(store, "mock", 1)
    _write(store, "mock", 2)
    _write(store, "other", 3)

    assert store.count_decisions("mock") == 2
    assert store.count_decisions("other") == 1


def test_sqlite_save_centroids_persists(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")

    store.save_centroids(
        "mock",
        "alpha",
        [[0.1, 0.2]],
        metadata={"iks": 4.5, "source": "unit"},
        decision_id="decision-1",
    )

    checkpoints = store.get_centroid_checkpoints("mock")
    assert len(checkpoints) == 1
    assert checkpoints[0]["domain"] == "mock"
    assert checkpoints[0]["decision_id"] == "decision-1"
    assert checkpoints[0]["category"] == "alpha"
    np.testing.assert_allclose(checkpoints[0]["centroids"], np.array([[0.1, 0.2]]))
    assert checkpoints[0]["iks"] == 4.5
    assert checkpoints[0]["metadata"] == {"iks": 4.5, "source": "unit"}


def test_load_latest_centroids_filters_domain(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    alpha = np.zeros((2, 2), dtype=float)
    beta = np.ones((2, 2), dtype=float)
    store.save_centroids("alpha", "cat", alpha)
    store.save_centroids("beta", "cat", beta)

    np.testing.assert_allclose(store.load_latest_centroids("alpha"), alpha)
    np.testing.assert_allclose(store.load_latest_centroids("beta"), beta)


def test_sqlite_save_without_bitemporal_works(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")

    store.save_centroids("mock", "alpha", [[0.1]], decision_id="decision-1")

    checkpoint = store.get_centroid_checkpoints("mock")[0]
    assert checkpoint["decision_time_start"] is None
    assert checkpoint["decision_time_end"] is None
    assert checkpoint["checkpoint_time"].endswith("Z")


def test_sqlite_checkpoint_time_filter(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    store.save_centroids("mock", "alpha", [[0.1]], decision_id="old", checkpoint_time="2026-05-01T00:00:00Z")
    store.save_centroids("mock", "alpha", [[0.2]], decision_id="new", checkpoint_time="2026-05-02T00:00:00Z")

    checkpoints = store.get_centroid_checkpoints(
        "mock",
        checkpoint_time_start="2026-05-01T12:00:00Z",
    )

    assert [checkpoint["decision_id"] for checkpoint in checkpoints] == ["new"]


def test_sqlite_decision_time_filter(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    store.save_centroids(
        "mock",
        "alpha",
        [[0.1]],
        decision_id="outside",
        decision_time_start="2026-05-01T00:00:00Z",
        decision_time_end="2026-05-03T00:00:00Z",
    )
    store.save_centroids(
        "mock",
        "alpha",
        [[0.2]],
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


def test_sqlite_centroid_checkpoints_limit(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    for index in range(4):
        store.save_centroids("mock", "alpha", [[float(index)]], decision_id=f"decision-{index}")

    checkpoints = store.get_centroid_checkpoints("mock", limit=2)

    assert [checkpoint["decision_id"] for checkpoint in checkpoints] == [
        "decision-2",
        "decision-3",
    ]


def test_wal_enabled_for_file_db(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")

    mode = store.connection.execute("PRAGMA journal_mode").fetchone()[0]

    assert mode.lower() == "wal"


def test_wal_skipped_for_memory():
    store = SQLiteGraphStore(":memory:")

    mode = store.connection.execute("PRAGMA journal_mode").fetchone()[0]

    assert mode.lower() == "memory"


def test_archive_table_created(tmp_path):
    db_path = tmp_path / "graph.sqlite"
    SQLiteGraphStore(db_path)

    assert "domain" in _columns(db_path, "decisions_archive")


def test_archive_moves_oldest(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    ids = [_write(store, "mock", index) for index in range(4)]
    for decision_id in ids:
        store.write_outcome(decision_id, "approve", True)

    assert store.archive_old_decisions("mock", keep_recent=2) == 2

    assert [d["decision_id"] for d in store.get_all_decisions("mock")] == ids[2:]
    assert store.count_archived("mock") == 2
    assert store.count_verified("mock") == 2


def test_archive_preserves_recent(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    ids = [_write(store, "mock", index) for index in range(3)]

    store.archive_old_decisions("mock", keep_recent=1)

    assert [d["decision_id"] for d in store.get_all_decisions("mock")] == [ids[-1]]


def test_archive_noop_under_limit(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    _write(store, "mock", 1)

    assert store.archive_old_decisions("mock", keep_recent=10) == 0
    assert store.count_archived("mock") == 0


def test_get_evolution_events(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    store.save_evolution_event("mock", "variant_created", "coverage_gap", "variant-1", metadata={"x": 1})
    store.save_evolution_event("other", "variant_created", "coverage_gap", "variant-2")

    events = store.get_evolution_events("mock")

    assert len(events) == 1
    assert events[0]["domain"] == "mock"
    assert events[0]["metadata"] == {"x": 1}


def test_domain_migration_true_legacy_decisions_without_domain(tmp_path):
    db_path = tmp_path / "old.sqlite"
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(
            """
            CREATE TABLE decisions (
                decision_id TEXT PRIMARY KEY,
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
            INSERT INTO decisions (
                decision_id, category, category_index, factors_json, factor_vector_json,
                recommended_action, recommended_index, confidence, probabilities_json, created_at
            ) VALUES (
                'legacy-1', 'alpha', 0, '{"risk": 0.4}', '[0.4]', 'approve', 0, 0.8, '[1.0]', 1.0
            );
            INSERT INTO outcomes (
                decision_id, actual_action, actual_index, is_correct, verified_at
            ) VALUES ('legacy-1', 'approve', 0, 1, 2.0);
            """
        )
        connection.commit()
    finally:
        connection.close()

    store = SQLiteGraphStore(db_path, domain="legacy")

    assert "domain" in _columns(db_path, "decisions")
    assert "domain" in _columns(db_path, "outcomes")
    assert "domain" in _columns(db_path, "centroid_checkpoints")
    assert {"decision_time_start", "decision_time_end", "checkpoint_time"} <= _columns(db_path, "centroid_checkpoints")
    row = store.connection.execute(
        "SELECT domain FROM decisions WHERE decision_id = 'legacy-1'"
    ).fetchone()
    assert row["domain"] == "legacy"
    assert store.count_decisions("legacy") == 1
    assert store.count_verified("legacy") == 1


def test_sqlite_concurrent_writes(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")

    def write(index: int) -> None:
        decision_id = _write(store, "mock", index)
        store.write_outcome(decision_id, "approve", True)

    threads = [threading.Thread(target=write, args=(index,)) for index in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert store.count_verified("mock") == 5
    assert store.count_correct("mock") == 5


def test_sqlite_close_safe(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")

    assert store.close() is None
