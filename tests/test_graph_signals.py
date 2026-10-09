"""Graph-backed signal delivery contract, including real AGE persistence."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from freezegun import freeze_time
import pytest

from copilot_sdk.backend.graph_signals import GraphSignalEvents, MAX_SIGNALS, EVICTION_BATCH
from copilot_sdk.config.tenant import tenant_context
from copilot_sdk.graph.memory_store import InMemoryGraphStore


def _fact(index: int = 0) -> dict[str, Any]:
    return {
        "source_copilot": "trading", "target_copilot": "purchasing",
        "signal_type": "supplier_risk", "entity_id": f"vendor-{index}",
        "confidence": 0.8, "detail": None,
    }


def test_publication_is_an_evolution_event_not_a_decision() -> None:
    graph = InMemoryGraphStore()
    signals = GraphSignalEvents(graph)
    signal_id = signals.publish(_fact())
    events = graph.get_evolution_events("cross_signals_ZGVmYXVsdA", limit=None)
    assert len(events) == 1
    event = events[0]
    assert event["event_id"] == signal_id
    assert event["event_type"] == "cross_signal"
    assert event["source_copilot"] == "trading"
    assert isinstance(event["metadata"]["published_at"], float)
    assert isinstance(event["metadata"]["signal_timestamp"], float)
    assert event["metadata"]["payload"] == signals.get(signal_id)
    assert graph.count_decisions("trading") == 0
    assert graph.count_decisions("cross_signals_ZGVmYXVsdA") == 0


def test_read_is_fresh_across_adapters_and_detached_from_graph() -> None:
    graph = InMemoryGraphStore()
    publisher, receiver = GraphSignalEvents(graph), GraphSignalEvents(graph)
    assert receiver.count() == 0
    fact = _fact()
    signal_id = publisher.publish(fact)
    fact["entity_id"] = "mutated-input"
    record = receiver.get(signal_id)
    assert record is not None
    assert record["entity_id"] == "vendor-0"
    record["entity_id"] = "mutated-output"
    assert receiver.list()[0]["entity_id"] == "vendor-0"


def test_tenant_scope_applies_to_publish_list_and_id_read() -> None:
    signals = GraphSignalEvents(InMemoryGraphStore())
    with tenant_context("tenant-a"):
        signal_id = signals.publish(_fact())
    with tenant_context("tenant-b"):
        assert signals.get(signal_id) is None
        assert signals.page() == ([], 0)
        signals.publish(_fact(1))
    with tenant_context("tenant-a"):
        assert signals.count() == 1
        assert signals.get(signal_id) is not None


def test_unrelated_evolution_events_are_not_facts() -> None:
    graph = InMemoryGraphStore()
    graph.write_evolution_event(
        "proof-1", "cross_signals_ZGVmYXVsdA", "proof_record", "rule", "variant",
        metadata={"proof": True},
    )
    assert GraphSignalEvents(graph).page() == ([], 0)


def test_publication_order_is_independent_of_fact_timestamp() -> None:
    signals = GraphSignalEvents(InMemoryGraphStore())
    now = datetime.now(timezone.utc)
    first = signals.publish({**_fact(), "timestamp": now.isoformat()})
    second = signals.publish({**_fact(1), "timestamp": (now - timedelta(hours=1)).isoformat()})
    assert [row["signal_id"] for row in signals.list()] == [first, second]


def test_equal_publication_times_have_deterministic_id_order() -> None:
    graph = InMemoryGraphStore()
    with freeze_time("2026-10-06T10:00:00Z"):
        signals = GraphSignalEvents(graph)
        ids = [signals.publish(_fact(index)) for index in range(3)]
        assert [row["signal_id"] for row in signals.list()] == sorted(ids)
        assert GraphSignalEvents(graph).list() == signals.list()


def test_expiration_after_publication_preserves_history() -> None:
    graph = InMemoryGraphStore()
    signals = GraphSignalEvents(graph)
    with freeze_time("2026-10-06T10:00:00Z") as clock:
        signal_id = signals.publish(_fact())
        clock.tick(timedelta(hours=24))
        assert signals.get(signal_id) is not None
        clock.tick(timedelta(microseconds=1))
        assert signals.page() == ([], 0)
        assert signals.get(signal_id) is None
    assert len(graph.get_evolution_events("cross_signals_ZGVmYXVsdA", limit=None)) == 1


def test_expiration_before_next_publication_avoids_batch_eviction() -> None:
    signals = GraphSignalEvents(InMemoryGraphStore())
    with freeze_time("2026-10-06T10:00:00Z") as clock:
        signals.publish(_fact())
        clock.tick(timedelta(hours=1))
        ids = [signals.publish(_fact(index)) for index in range(MAX_SIGNALS - 1)]
        clock.tick(timedelta(hours=23, seconds=1))
        newest = signals.publish(_fact(MAX_SIGNALS))
        assert signals.count() == MAX_SIGNALS
        assert signals.get(ids[0]) is not None
        assert signals.get(newest) is not None


def test_evicted_facts_do_not_reappear_when_newer_facts_expire() -> None:
    signals = GraphSignalEvents(InMemoryGraphStore())
    with freeze_time("2026-10-06T10:00:00Z") as clock:
        for index in range(MAX_SIGNALS):
            signals.publish(_fact(index))
        retained_before = signals.list(limit=MAX_SIGNALS)
        clock.tick(timedelta(seconds=1))
        signals.publish({**_fact(MAX_SIGNALS), "timestamp": "2026-10-05T11:00:00Z"})
        assert signals.count() == MAX_SIGNALS - EVICTION_BATCH + 1
        clock.tick(timedelta(hours=2))
        assert signals.list(limit=MAX_SIGNALS) == retained_before[EVICTION_BATCH:]


@pytest.mark.parametrize("limit,offset", [(0, 0), (MAX_SIGNALS + 1, 0), (1, -1)])
def test_invalid_adapter_pagination_fails(limit: int, offset: int) -> None:
    with pytest.raises(ValueError, match="pagination"):
        GraphSignalEvents(InMemoryGraphStore()).page(limit, offset)


def test_age_unbounded_event_history_preserves_batch_eviction(
    age_graph_store: Callable[[str], Any],
) -> None:
    graph = age_graph_store("trading")
    signals = GraphSignalEvents(graph)
    ids = [signals.publish(_fact(index)) for index in range(MAX_SIGNALS + 1)]
    events = graph.get_evolution_events("cross_signals_ZGVmYXVsdA", event_type="cross_signal", limit=None)
    assert len(events) == MAX_SIGNALS + 1
    assert len(graph.get_evolution_events("cross_signals_ZGVmYXVsdA", limit=1)) == 1
    rows, total = signals.page(limit=MAX_SIGNALS)
    assert total == MAX_SIGNALS + 1 - EVICTION_BATCH
    assert [row["signal_id"] for row in rows] == ids[EVICTION_BATCH:]
    assert signals.get(ids[0]) is None
    assert signals.get(ids[-1]) is not None
    assert graph.count_decisions("trading") == 0


def test_age_tenant_names_preserve_punctuation_and_maximum_length(
    age_graph_store: Callable[[str], Any],
) -> None:
    signals = GraphSignalEvents(age_graph_store("trading"))
    tenants = ["tenant:a", "tenant.a", "tenant-a", "a" * 128]
    ids = []
    for tenant in tenants:
        with tenant_context(tenant):
            assert signals.count() == 0
            ids.append(signals.publish(_fact()))
    for tenant, expected in zip(tenants, ids):
        with tenant_context(tenant):
            assert [row["signal_id"] for row in signals.list()] == [expected]
