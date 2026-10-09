from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import TypeAlias, cast

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
Store: TypeAlias = InMemoryGraphStore


@pytest.fixture
def store() -> Iterator[Store]:
    graph_store = InMemoryGraphStore(domain="test")
    try:
        yield graph_store
    finally:
        graph_store.close()


def _write_decision(store: Store, domain: str = "test") -> str:
    return cast(str, store.write_decision(
        domain,
        category="quality",
        action="approve",
        confidence=0.9,
        factors={"risk": 0.1},
    ))


def _write_event(
    store: Store,
    event_id: str,
    domain: str,
    decision_id: str | None = None,
) -> None:
    store.write_evolution_event(
        event_id=event_id,
        domain=domain,
        event_type="variant_created",
        rule_name="quality-rule",
        variant_id="variant-1",
        decision_id=decision_id,
    )


def _stored_event_decision_id(store: Store, event_id: str) -> str | None:
    if isinstance(store, InMemoryGraphStore):
        assert event_id in store._protocol_evolution_events
        for edge in store._edges:
            if (
                edge.get("edge_type") == "TRIGGERED_EVOLUTION"
                and edge.get("event_id") == event_id
            ):
                return str(edge["decision_id"])
        return None
    raise AssertionError(f"unsupported test store: {type(store)!r}")


def test_evolution_event_linked_to_decision(store: Store) -> None:
    decision_id = _write_decision(store)
    _write_event(store, "event-linked", "test", decision_id)

    assert _stored_event_decision_id(store, "event-linked") == decision_id


def test_evolution_event_without_decision_id_no_edge(store: Store) -> None:
    _write_event(store, "event-unlinked", "test")

    assert _stored_event_decision_id(store, "event-unlinked") is None


def test_evolution_event_wrong_domain_no_edge(store: Store) -> None:
    decision_id = _write_decision(store, domain="trading")
    _write_event(store, "event-cross-domain", "s2p", decision_id)

    assert _stored_event_decision_id(store, "event-cross-domain") is None

