from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from copilot_sdk.graph import GraphStore, InMemoryGraphStore, SQLiteGraphStore


class MinimalOldStore:
    def write_decision(self, *args, **kwargs):
        return "decision-1"

    def write_outcome(self, *args, **kwargs):
        return None

    def get_decision(self, *args, **kwargs):
        return None

    def get_decisions(self, *args, **kwargs):
        return []

    def get_verified_decisions(self):
        return []

    def count_verified(self):
        return 0

    def count_correct(self):
        return 0

    def get_all_decisions(self):
        return []

    def save_centroids(self, *args, **kwargs):
        return None

    def get_centroid_checkpoints(self, *args, **kwargs):
        return []

    def save_evolution_event(self, *args, **kwargs):
        return None

    def close(self):
        return None


def _sqlite_events(db_path: Path) -> list[dict]:
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


def test_graphstore_protocol_remains_narrow_for_old_shape_stores():
    store = MinimalOldStore()

    assert isinstance(store, GraphStore)
    assert not hasattr(GraphStore, "link_decision_to_entity")
    assert not hasattr(GraphStore, "get_decision_links")
    assert not hasattr(store, "link_decision_to_entity")


def test_supports_decision_entity_links_deleted():
    target = "Supports" + "Decision" + "Entity" + "Links"

    protocol_source = Path("copilot_sdk/graph/protocol.py").read_text(encoding="utf-8")
    init_source = Path("copilot_sdk/graph/__init__.py").read_text(encoding="utf-8")

    assert target not in protocol_source
    assert target not in init_source


def test_sdk_production_code_does_not_import_supports_decision_entity_links():
    target = "Supports" + "Decision" + "Entity" + "Links"
    sdk_root = Path("copilot_sdk")
    offenders = []
    for path in sdk_root.rglob("*.py"):
        if path.as_posix() == "copilot_sdk/graph/protocol.py":
            continue
        source = path.read_text(encoding="utf-8")
        if target in source:
            offenders.append(path.as_posix())

    assert offenders == []


def test_inmemory_decision_id_prefix_default_unchanged():
    store = InMemoryGraphStore()
    metadata = {"decision_id": "decision-1", "source": "unit"}

    decision_id = store.write_decision(
        entity_id="entity-1",
        category="category",
        action="approve",
        confidence=0.9,
        factors={},
        metadata=metadata,
    )

    assert decision_id == "decision-1"
    decision = store.get_decision(decision_id)
    assert decision["decision_id"] == "decision-1"
    assert decision["metadata"] == {"decision_id": "decision-1", "source": "unit"}
    assert metadata == {"decision_id": "decision-1", "source": "unit"}


def test_inmemory_no_prefix_metadata_without_decision_id_unchanged():
    store = InMemoryGraphStore()
    metadata = {"source": "unit"}

    decision_id = store.write_decision(
        entity_id="entity-1",
        category="category",
        action="approve",
        confidence=0.9,
        factors={},
        metadata=metadata,
    )

    decision = store.get_decision(decision_id)
    assert decision["metadata"] == {"source": "unit"}
    assert metadata == {"source": "unit"}


def test_inmemory_decision_id_prefix_applied():
    store = InMemoryGraphStore(decision_id_prefix="S2P-")

    decision_id = store.write_decision(
        entity_id="entity-1",
        category="category",
        action="approve",
        confidence=0.9,
        factors={},
        metadata={"decision_id": "decision-1"},
    )

    assert decision_id == "S2P-decision-1"
    assert store.get_decision(decision_id)["decision_id"] == "S2P-decision-1"


def test_inmemory_decision_id_prefix_updates_metadata_decision_id():
    store = InMemoryGraphStore(decision_id_prefix="S2P-")
    metadata = {"decision_id": "decision-1", "source": "scorer"}

    decision_id = store.write_decision(
        entity_id="entity-1",
        category="category",
        action="approve",
        confidence=0.9,
        factors={},
        metadata=metadata,
    )

    decision = store.get_decision(decision_id)
    assert decision_id == "S2P-decision-1"
    assert decision["decision_id"] == "S2P-decision-1"
    assert decision["metadata"]["decision_id"] == decision_id
    assert decision["metadata"]["source"] == "scorer"
    assert metadata == {"decision_id": "decision-1", "source": "scorer"}


def test_inmemory_decision_id_prefix_not_double_applied():
    store = InMemoryGraphStore(decision_id_prefix="S2P-")

    decision_id = store.write_decision(
        entity_id="entity-1",
        category="category",
        action="approve",
        confidence=0.9,
        factors={},
        metadata={"decision_id": "S2P-decision-1"},
    )

    assert decision_id == "S2P-decision-1"
    assert "S2P-S2P-" not in decision_id


def test_inmemory_decision_id_prefix_does_not_double_prefix_metadata():
    store = InMemoryGraphStore(decision_id_prefix="S2P-")

    decision_id = store.write_decision(
        entity_id="entity-1",
        category="category",
        action="approve",
        confidence=0.9,
        factors={},
        metadata={"decision_id": "S2P-decision-1"},
    )

    decision = store.get_decision(decision_id)
    assert decision_id == "S2P-decision-1"
    assert decision["metadata"]["decision_id"] == "S2P-decision-1"
    assert "S2P-S2P-" not in decision["metadata"]["decision_id"]


def test_inmemory_store_has_evolution_and_link_parity():
    store = InMemoryGraphStore()

    store.save_evolution_event("variant_generated", "threshold_rule", "variant-1", {"seed": 7})
    store.link_decision_to_entity("decision-1", "entity-1")

    assert store._evolution_events[0]["event_type"] == "variant_generated"
    assert store._evolution_events[0]["metadata"] == {"seed": 7}
    assert store.get_decision_links("decision-1") == [
        {
            "decision_id": "decision-1",
            "entity_id": "entity-1",
            "edge_type": "DECIDED_ON",
            "created_at": store.get_decision_links("decision-1")[0]["created_at"],
        }
    ]


def test_sqlite_store_has_evolution_and_link_parity(tmp_path):
    db_path = tmp_path / "graph.sqlite"
    store = SQLiteGraphStore(db_path)

    store.save_evolution_event("variant_generated", "threshold_rule", "variant-1", {"seed": 7})
    store.link_decision_to_entity("decision-1", "entity-1", edge_type="REVIEWS")

    events = _sqlite_events(db_path)
    assert events[0]["event_type"] == "variant_generated"
    assert json.loads(events[0]["metadata"]) == {"seed": 7}
    assert store.get_decision_links("decision-1") == [
        {
            "decision_id": "decision-1",
            "entity_id": "entity-1",
            "edge_type": "REVIEWS",
            "created_at": store.get_decision_links("decision-1")[0]["created_at"],
        }
    ]
