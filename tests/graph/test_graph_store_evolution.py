from __future__ import annotations

import json
import sqlite3

from copilot_sdk.evolution import EvolutionStore
from copilot_sdk.graph import GraphStore, InMemoryGraphStore, SQLiteGraphStore


def _sqlite_events(db_path):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT domain, event_type, rule_name, variant_id, metadata, timestamp
            FROM evolution_events
            ORDER BY id ASC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def test_graph_store_protocol_excludes_evolution_methods():
    assert not hasattr(GraphStore, "save_evolution_event")
    assert not hasattr(GraphStore, "get_evolution_events")
    assert hasattr(EvolutionStore, "save_evolution_event")
    assert isinstance(InMemoryGraphStore(), GraphStore)
    assert isinstance(InMemoryGraphStore(), EvolutionStore)


def test_in_memory_graph_store_save_evolution_event():
    store = InMemoryGraphStore()

    store.save_evolution_event(
        "mock",
        "variant_created",
        "coverage_gap",
        "variant-1",
        metadata={"source": "unit", "score": 0.7},
    )

    assert store.get_evolution_events("mock") == [
        {
            "domain": "mock",
            "event_type": "variant_created",
            "rule_name": "coverage_gap",
            "variant_id": "variant-1",
            "metadata": {"source": "unit", "score": 0.7},
            "timestamp": store.get_evolution_events("mock")[0]["timestamp"],
        }
    ]


def test_in_memory_reset_clears_evolution_events():
    store = InMemoryGraphStore()
    store.save_evolution_event("mock", "variant_created", "coverage_gap", "variant-1")

    store.reset()

    assert store.get_evolution_events("mock") == []


def test_sqlite_graph_store_save_evolution_event(tmp_path):
    db_path = tmp_path / "graph.sqlite"
    store = SQLiteGraphStore(db_path)

    store.save_evolution_event(
        "mock",
        "variant_created",
        "coverage_gap",
        "variant-1",
        metadata={"trigger": "low_accuracy"},
    )

    events = _sqlite_events(db_path)
    assert events[0]["domain"] == "mock"
    assert events[0]["event_type"] == "variant_created"
    assert events[0]["rule_name"] == "coverage_gap"
    assert events[0]["variant_id"] == "variant-1"
    assert json.loads(events[0]["metadata"]) == {"trigger": "low_accuracy"}
    assert events[0]["timestamp"]


def test_sqlite_graph_store_evolution_table_created(tmp_path):
    db_path = tmp_path / "graph.sqlite"
    store = SQLiteGraphStore(db_path)

    store.save_evolution_event("mock", "shadow_started", "coverage_gap", "variant-1")

    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'evolution_events'"
        ).fetchone()
        assert row is not None
    finally:
        connection.close()


def test_evolution_events_filter_by_domain(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    store.save_evolution_event("alpha", "shadow_started", "rule", "variant-a")
    store.save_evolution_event("beta", "shadow_started", "rule", "variant-b")

    assert [event["variant_id"] for event in store.get_evolution_events("alpha")] == ["variant-a"]
    assert [event["variant_id"] for event in store.get_evolution_events("beta")] == ["variant-b"]


def test_sqlite_save_evolution_event_without_metadata(tmp_path):
    db_path = tmp_path / "graph.sqlite"
    store = SQLiteGraphStore(db_path)

    store.save_evolution_event("mock", "shadow_started", "coverage_gap", "variant-1")

    events = _sqlite_events(db_path)
    assert json.loads(events[0]["metadata"]) == {}


def test_sqlite_graph_store_satisfies_evolution_store_protocol(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")

    assert isinstance(store, GraphStore)
    assert isinstance(store, EvolutionStore)
