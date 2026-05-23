from __future__ import annotations

import logging

from copilot_sdk.evolution import EvolutionEvent, InMemoryEvolutionLedger


class RecordingGraphStore:
    def __init__(self):
        self.calls = []

    def save_evolution_event(self, domain, event_type=None, rule_name="", variant_id="", metadata=None):
        if event_type is None or (variant_id == "" and rule_name):
            old_event_type = domain
            old_rule_name = event_type or ""
            old_variant_id = rule_name
            domain = "test"
            event_type = old_event_type
            rule_name = old_rule_name
            variant_id = old_variant_id
        self.calls.append((domain, event_type, rule_name, variant_id, metadata))


class FailingGraphStore:
    def save_evolution_event(self, domain, event_type=None, rule_name="", variant_id="", metadata=None):
        raise RuntimeError("write failed")


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
    graph_store = RecordingGraphStore()
    ledger = InMemoryEvolutionLedger(graph_store=graph_store)

    ledger.append(EvolutionEvent("shadow_started", "rule", "variant", metadata={"x": 1}))

    assert graph_store.calls[0][1:4] == ("shadow_started", "rule", "variant")
    assert graph_store.calls[0][4]["x"] == 1
    assert graph_store.calls[0][4]["timestamp"]


def test_ledger_graph_store_failure_logs_warning(caplog):
    ledger = InMemoryEvolutionLedger(graph_store=FailingGraphStore())

    with caplog.at_level(logging.WARNING):
        ledger.append(EvolutionEvent("shadow_started", "rule", "variant"))

    assert ledger.event_count == 1
    assert "Failed to persist evolution event" in caplog.text
