from __future__ import annotations

import json
import sqlite3

from copilot_sdk.evolution import EvolutionStore
from copilot_sdk.graph import GraphStore, InMemoryGraphStore
from tests.graph_store_test_helpers import make_memory_store


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
            "event_id": None,
            "source_copilot": None,
            "source_rule": None,
            "metric": None,
            "shadow_batch_size": None,
            "min_shadow_batches": None,
        }
    ]


def test_in_memory_reset_clears_evolution_events():
    store = InMemoryGraphStore()
    store.save_evolution_event("mock", "variant_created", "coverage_gap", "variant-1")

    store.reset()

    assert store.get_evolution_events("mock") == []






def test_evolution_events_filter_by_domain(tmp_path):
    store = make_memory_store(tmp_path / "graph.sqlite")
    store.save_evolution_event("alpha", "shadow_started", "rule", "variant-a")
    store.save_evolution_event("beta", "shadow_started", "rule", "variant-b")

    assert [event["variant_id"] for event in store.get_evolution_events("alpha")] == ["variant-a"]
    assert [event["variant_id"] for event in store.get_evolution_events("beta")] == ["variant-b"]




def test_sqlite_graph_store_satisfies_evolution_store_protocol(tmp_path):
    store = make_memory_store(tmp_path / "graph.sqlite")

    assert isinstance(store, EvolutionStore)

