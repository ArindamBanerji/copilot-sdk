from __future__ import annotations

import pytest

import copilot_sdk.evolution.ledger as ledger_module
from copilot_sdk.evolution import EvolutionEvent, InMemoryEvolutionLedger
from copilot_sdk.graph import SQLiteGraphStore


class KeywordOnlyEvolutionStore:
    def __init__(self):
        self.calls = []

    def save_evolution_event(
        self,
        *,
        domain,
        event_type,
        rule_name,
        variant_id=None,
        metadata=None,
    ):
        self.calls.append(
            {
                "domain": domain,
                "event_type": event_type,
                "rule_name": rule_name,
                "variant_id": variant_id,
                "metadata": metadata or {},
            }
        )


def test_ledger_passes_domain_and_keyword_fields_to_store():
    store = KeywordOnlyEvolutionStore()
    ledger = InMemoryEvolutionLedger(evolution_store=store, domain="trading")

    ledger.append(EvolutionEvent("shadow_started", "rule-a", "variant-a", metadata={"x": 1}))

    assert store.calls == [
        {
            "domain": "trading",
            "event_type": "shadow_started",
            "rule_name": "rule-a",
            "variant_id": "variant-a",
            "metadata": {
                "x": 1,
                "timestamp": ledger.get_events()[0]["timestamp"],
            },
        }
    ]


def test_ledger_without_store_still_records_events():
    ledger = InMemoryEvolutionLedger(domain="trading")

    ledger.append(EvolutionEvent("variant_generated", "rule-a", "variant-a"))

    assert ledger.event_count == 1
    assert ledger.get_events()[0]["event_type"] == "variant_generated"


def test_ledger_with_sqlite_store_persists_correct_domain(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")
    ledger = InMemoryEvolutionLedger(evolution_store=store, domain="dataops")

    ledger.append(EvolutionEvent("promoted", "rule-a", "variant-a"))

    events = store.get_evolution_events("dataops")
    assert len(events) == 1
    assert events[0]["domain"] == "dataops"
    assert events[0]["event_type"] == "promoted"
    assert events[0]["rule_name"] == "rule-a"
    assert events[0]["variant_id"] == "variant-a"
    assert store.get_evolution_events("trading") == []


def test_legacy_graph_store_keyword_is_removed():
    with pytest.raises(TypeError):
        InMemoryEvolutionLedger(graph_store=KeywordOnlyEvolutionStore(), domain="trading")


def test_pre_domain_adapter_is_removed():
    assert not hasattr(ledger_module, "_PreDomainEvolutionStoreAdapter")
