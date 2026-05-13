from __future__ import annotations

import json
import sqlite3

from copilot_sdk.graph import GraphStore, InMemoryGraphStore, SQLiteGraphStore


def _sqlite_events(db_path):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT event_type, rule_name, variant_id, metadata, timestamp
            FROM evolution_events
            ORDER BY id ASC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def test_graph_store_protocol_includes_save_evolution_event():
    assert hasattr(GraphStore, "save_evolution_event")
    assert isinstance(InMemoryGraphStore(), GraphStore)


def test_in_memory_graph_store_save_evolution_event():
    store = InMemoryGraphStore()

    store.save_evolution_event(
        "variant_created",
        "coverage_gap",
        "variant-1",
        metadata={"source": "unit", "score": 0.7},
    )

    assert store._evolution_events == [
        {
            "event_type": "variant_created",
            "rule_name": "coverage_gap",
            "variant_id": "variant-1",
            "metadata": {"source": "unit", "score": 0.7},
            "timestamp": store._evolution_events[0]["timestamp"],
        }
    ]
    assert store._evolution_events[0]["timestamp"]


def test_in_memory_reset_clears_evolution_events():
    store = InMemoryGraphStore()
    store.save_evolution_event("variant_created", "coverage_gap", "variant-1")

    store.reset()

    assert store._evolution_events == []


def test_sqlite_graph_store_save_evolution_event(tmp_path):
    db_path = tmp_path / "graph.sqlite"
    store = SQLiteGraphStore(db_path)

    store.save_evolution_event(
        "variant_created",
        "coverage_gap",
        "variant-1",
        metadata={"trigger": "low_accuracy"},
    )

    events = _sqlite_events(db_path)
    assert events[0]["event_type"] == "variant_created"
    assert events[0]["rule_name"] == "coverage_gap"
    assert events[0]["variant_id"] == "variant-1"
    assert json.loads(events[0]["metadata"]) == {"trigger": "low_accuracy"}
    assert events[0]["timestamp"]


def test_sqlite_graph_store_evolution_table_created(tmp_path):
    db_path = tmp_path / "graph.sqlite"
    store = SQLiteGraphStore(db_path)

    store.save_evolution_event("shadow_started", "coverage_gap", "variant-1")

    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'evolution_events'"
        ).fetchone()
        assert row is not None
    finally:
        connection.close()


def test_evolution_event_metadata_persisted(tmp_path):
    db_path = tmp_path / "graph.sqlite"
    store = SQLiteGraphStore(db_path)
    metadata = {"nested": {"approved": True}, "weights": [0.1, 0.2]}

    store.save_evolution_event(
        "promotion_approved",
        "coverage_gap",
        "variant-1",
        metadata=metadata,
    )

    events = _sqlite_events(db_path)
    assert json.loads(events[0]["metadata"]) == metadata


def test_sqlite_save_evolution_event_without_metadata(tmp_path):
    db_path = tmp_path / "graph.sqlite"
    store = SQLiteGraphStore(db_path)

    store.save_evolution_event("shadow_started", "coverage_gap", "variant-1")

    events = _sqlite_events(db_path)
    assert json.loads(events[0]["metadata"]) == {}


def test_sqlite_graph_store_satisfies_protocol_after_evolution_extension(tmp_path):
    assert isinstance(SQLiteGraphStore(tmp_path / "graph.sqlite"), GraphStore)
