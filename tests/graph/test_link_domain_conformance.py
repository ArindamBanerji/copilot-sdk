from __future__ import annotations

from typing import Any

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


@pytest.fixture(params=["memory", "sqlite"])
def store(request: pytest.FixtureRequest, tmp_path):
    if request.param == "memory":
        graph_store: Any = InMemoryGraphStore(domain="test")
    else:
        graph_store = SQLiteGraphStore(tmp_path / "links.sqlite", domain="test")
    try:
        yield graph_store
    finally:
        graph_store.close()


def _seed_decision(store: Any, decision_id: str = "decision-1") -> str:
    created_id = store.write_decision(
        "test",
        "category",
        "approve",
        0.9,
        {"factor": 0.5},
        metadata={"decision_id": decision_id},
    )
    return str(created_id)


def test_link_stores_domain(store: Any) -> None:
    decision_id = _seed_decision(store)

    store.link_decision_to_entity(decision_id, "entity-1", domain="test")

    links = store.get_decision_links(decision_id, domain="test")
    assert len(links) == 1
    assert links[0]["entity_id"] == "entity-1"
    if isinstance(store, SQLiteGraphStore):
        row = store.connection.execute(
            "SELECT domain FROM decision_entity_edges WHERE decision_id = ?",
            (decision_id,),
        ).fetchone()
        assert row["domain"] == "test"
    else:
        assert store._edges[0]["domain"] == "test"


def test_link_requires_domain(store: Any) -> None:
    with pytest.raises(TypeError):
        store.link_decision_to_entity("missing", "entity-1")


def test_link_rejects_empty_domain(store: Any) -> None:
    with pytest.raises(ValueError, match="non-empty domain"):
        store.link_decision_to_entity("missing", "entity-1", domain=" ")


def test_link_domain_matches_decision(store: Any) -> None:
    decision_id = _seed_decision(store)

    with pytest.raises(ValueError, match="does not match"):
        store.link_decision_to_entity(decision_id, "entity-1", domain="other")
