from __future__ import annotations

import logging
from unittest.mock import Mock

from copilot_sdk.graph.memory_store import InMemoryGraphStore

from copilot_sdk.evolution import EvolutionEvent, InMemoryEvolutionLedger






def test_ledger_appends_events():
    ledger = InMemoryEvolutionLedger()
    ledger.append(EvolutionEvent("variant_generated", "rule-a", "variant-a"))

    assert ledger.event_count == 1
    assert ledger.get_events()[0]["rule_name"] == "rule-a"


def test_ledger_filters_by_rule_name():
    ledger = InMemoryEvolutionLedger()
    ledger.append(EvolutionEvent("variant_generated", "rule-a", "variant-a"))
    ledger.append(EvolutionEvent("variant_generated", "rule-b", "variant-b"))

    assert [event["rule_name"] for event in ledger.get_events(rule_name="rule-b")] == ["rule-b"]


def test_ledger_limit_returns_recent_events():
    ledger = InMemoryEvolutionLedger()
    for index in range(3):
        ledger.append(EvolutionEvent("variant_generated", "rule", f"variant-{index}"))

    assert [event["variant_id"] for event in ledger.get_events(limit=2)] == [
        "variant-1",
        "variant-2",
    ]


def test_ledger_zero_limit_returns_empty():
    ledger = InMemoryEvolutionLedger()
    ledger.append(EvolutionEvent("variant_generated", "rule", "variant"))

    assert ledger.get_events(limit=0) == []


def test_ledger_promoted_rules_are_deterministic():
    ledger = InMemoryEvolutionLedger()
    ledger.append(EvolutionEvent("promoted", "rule-b", "variant-b"))
    ledger.append(EvolutionEvent("promoted", "rule-a", "variant-a"))
    ledger.append(EvolutionEvent("promoted", "rule-b", "variant-b2"))

    assert ledger.get_promoted_rules() == ["rule-b", "rule-a"]


def test_ledger_reset_clears_events():
    ledger = InMemoryEvolutionLedger()
    ledger.append(EvolutionEvent("variant_generated", "rule", "variant"))

    ledger.reset()

    assert ledger.event_count == 0
    assert ledger.get_events() == []


def test_ledger_persists_to_graph_store():
    graph_store = InMemoryGraphStore(domain="test")
    ledger = InMemoryEvolutionLedger(evolution_store=graph_store, domain="test")

    ledger.append(EvolutionEvent("shadow_started", "rule", "variant", metadata={"x": 1}))

    events = graph_store.get_evolution_events("test")
    assert len(events) == 1
    assert (events[0]["event_type"], events[0]["rule_name"], events[0]["variant_id"]) == ("shadow_started", "rule", "variant")
    assert events[0]["metadata"]["x"] == 1
    assert events[0]["metadata"]["timestamp"]
    assert graph_store.get_evolution_events("other") == []


def test_ledger_graph_store_failure_logs_warning(caplog):
    store = InMemoryGraphStore(domain="test")
    store.write_evolution_event = Mock(side_effect=RuntimeError("write failed"))
    ledger = InMemoryEvolutionLedger(evolution_store=store, domain="test")

    with caplog.at_level(logging.WARNING):
        ledger.append(EvolutionEvent("shadow_started", "rule", "variant"))

    assert ledger.event_count == 1
    assert "Failed to persist evolution event" in caplog.text
