from __future__ import annotations

import threading

from copilot_sdk.graph import SQLiteGraphStore
from copilot_sdk.scoring.storage import DecisionStore


def test_sqlite_write_decision_returns_id_and_persists(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")

    decision_id = store.write_decision(
        "invoice-1",
        "alpha",
        "approve",
        0.82,
        {"amount": 0.2, "risk": 0.3},
        metadata={"created_at": 10.0, "category_index": 2, "recommended_index": 1},
    )

    decision = store.get_decision(decision_id)
    assert decision["decision_id"] == decision_id
    assert decision["entity_id"] == "invoice-1"
    assert decision["category"] == "alpha"
    assert decision["recommended_action"] == "approve"
    assert decision["confidence"] == 0.82
    assert decision["factors"]["amount"] == 0.2
    assert decision["category_index"] == 2
    assert decision["recommended_index"] == 1


def test_sqlite_write_outcomes_and_counts(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    first = store.write_decision("e-1", "alpha", "approve", 0.8, {"x": 1.0})
    second = store.write_decision("e-2", "beta", "review", 0.7, {"x": 0.0})

    store.write_outcome(first, "approve", True, metadata={"actual_index": 0, "verified_at": 20.0})
    store.write_outcome(second, "approve", False, metadata={"actual_index": 1, "verified_at": 21.0})

    assert store.count_verified() == 2
    assert store.count_correct() == 1
    verified = store.get_verified_decisions()
    assert [decision["decision_id"] for decision in verified] == [first, second]
    assert verified[0]["actual_action"] == "approve"
    assert verified[0]["is_correct"] is True


def test_sqlite_get_decision_missing_returns_none(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")

    assert store.get_decision("missing") is None


def test_sqlite_get_decisions_by_category_and_limit(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    store.write_decision("e-1", "alpha", "approve", 0.8, {"x": 1.0}, metadata={"created_at": 1.0})
    store.write_decision("e-2", "beta", "review", 0.7, {"x": 2.0}, metadata={"created_at": 2.0})
    store.write_decision("e-3", "alpha", "approve", 0.9, {"x": 3.0}, metadata={"created_at": 3.0})

    assert [d["entity_id"] for d in store.get_decisions()] == ["e-1", "e-2", "e-3"]
    assert [d["entity_id"] for d in store.get_decisions(category="alpha")] == ["e-1", "e-3"]
    assert [d["entity_id"] for d in store.get_decisions(limit=2)] == ["e-1", "e-2"]


def test_sqlite_get_all_decisions(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    store.write_decision("e-1", "alpha", "approve", 0.8, {"x": 1.0})

    assert len(store.get_all_decisions()) == 1


def test_sqlite_matches_raw_decision_store(tmp_path):
    db_path = tmp_path / "graph.sqlite"
    graph = SQLiteGraphStore(db_path, domain="mock")
    decision_id = graph.write_decision(
        "e-1",
        "alpha",
        "approve",
        0.8,
        {"x": 1.0},
        metadata={"category_index": 3, "recommended_index": 4, "created_at": 10.0},
    )
    graph.write_outcome(decision_id, "approve", True, metadata={"actual_index": 4})

    raw = DecisionStore(db_path)
    try:
        decision = raw.get_decision(decision_id)
        assert decision["domain"] == "mock"
        assert decision["category"] == "alpha"
        assert decision["category_index"] == 3
        assert decision["recommended_index"] == 4
        assert raw.count_verified() == graph.count_verified()
        assert raw.count_correct() == graph.count_correct()
    finally:
        raw.close()


def test_sqlite_concurrent_writes(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")

    def write(index: int) -> None:
        decision_id = store.write_decision(
            f"e-{index}",
            "alpha",
            "approve",
            0.8,
            {"x": float(index)},
            metadata={"created_at": float(index)},
        )
        store.write_outcome(decision_id, "approve", True)

    threads = [threading.Thread(target=write, args=(index,)) for index in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert store.count_verified() == 5
    assert store.count_correct() == 5


def test_sqlite_close_safe(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")

    assert store.close() is None
