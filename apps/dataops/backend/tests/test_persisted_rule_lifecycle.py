"""Lifecycle responses reflect stored transitions, not generated histories."""
from importlib import import_module

from fastapi import FastAPI
from fastapi.testclient import TestClient
from copilot_sdk.graph.memory_store import InMemoryGraphStore


def test_promoted_then_demoted_response():
    store = InMemoryGraphStore(domain="dataops")
    try:
        for index, kind in enumerate(("proposed", "promoted", "demoted")):
            store.write_evolution_event(event_id=f"rule-{index}", domain="dataops", event_type=kind,
                rule_name="rule", variant_id="rule-v1", metadata={"reason": f"reason-{kind}"})
        app = FastAPI()
        app.include_router(import_module("app.ae_router").create_ae_router(lambda: store), prefix="/api/ae")
        with TestClient(app) as client:
            response = client.get("/api/ae/rule-lifecycle")
            assert response.status_code == 200
            body = response.json()
            assert body["total"] == 1
            rule = body["rules"][0]
            assert rule["status"] == "demoted"
            assert body["summary"]["demoted"] == 1
            assert [event["type"] for event in rule["lifecycle_events"]] == ["proposed", "promoted", "demoted"]
            assert all(event["date"] is not None for event in rule["lifecycle_events"])
            assert rule["lifecycle_events"][-1]["detail"] == "reason-demoted"
    finally:
        store.close()


def test_missing_transitions_are_not_invented():
    builder = import_module("app.ae_router")._persisted_rule_lifecycles
    rules = builder([{"event_type": "promoted", "variant_id": "one", "timestamp": 20}])
    assert [event["type"] for event in rules[0]["lifecycle_events"]] == ["promoted"]
    assert builder([]) == []


def test_unsorted_history_is_grouped_and_sorted():
    builder = import_module("app.ae_router")._persisted_rule_lifecycles
    rules = builder([
        {"event_type": "demoted", "variant_id": "one", "timestamp": "2026-09-19T00:00:00Z"},
        {"event_type": "promoted", "variant_id": "two", "timestamp": "2026-09-18T00:00:00Z"},
        {"event_type": "promoted", "variant_id": "one", "timestamp": "2026-09-17T00:00:00Z"},
    ])
    assert len(rules) == 2
    rule = next(row for row in rules if row["variant_id"] == "one")
    assert [event["type"] for event in rule["lifecycle_events"]] == ["promoted", "demoted"]


def test_synthetic_history_does_not_activate_operational_rules():
    store = InMemoryGraphStore(domain="dataops")
    try:
        for kind in ("promoted", "demoted"):
            store.write_evolution_event(event_id=kind, domain="dataops", event_type=kind,
                rule_name="demo", variant_id="demo", metadata={"planted": True, "reason": "Demo only"})
        app = FastAPI()
        app.include_router(import_module("app.ae_router").create_ae_router(lambda: store), prefix="/api/ae")
        with TestClient(app) as client:
            assert client.get("/api/ae/rule-lifecycle").json()["total"] == 1
            assert client.get("/api/ae/operational-rules").json()["rules"] == []
            assert client.get("/api/ae/impact").json()["active_rules"] == []
    finally:
        store.close()
