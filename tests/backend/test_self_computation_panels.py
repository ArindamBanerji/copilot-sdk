from __future__ import annotations

from fastapi import FastAPI
import pytest
from fastapi.testclient import TestClient
from typing import cast

from copilot_sdk.backend.self_computation_router import mount_self_computation_router
from copilot_sdk.graph.memory_store import InMemoryGraphStore


def _client() -> tuple[TestClient, InMemoryGraphStore]:
    store = InMemoryGraphStore(domain="trading")
    app = FastAPI()
    mount_self_computation_router(app, store, domain="trading")
    return TestClient(app), store


def _seed_decision(store: InMemoryGraphStore, *, correct: bool = True) -> str:
    decision_id = cast(str, store.write_decision(
        "trading", "momentum", "buy", 0.8,
        {"signal": 0.8},
        {"decision_id": "D-SC-1" if correct else "D-SC-2"},
    ))
    store.write_outcome(
        decision_id,
        "buy" if correct else "sell",
        correct,
        domain="trading",
        outcome="confirmed",
    )
    return decision_id


def test_sc11_centroid_timeline_endpoint() -> None:
    client, _ = _client()
    response = client.get("/api/self/centroid-timeline")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_sc12_accuracy_alerts_endpoint() -> None:
    client, store = _client()
    _seed_decision(store, correct=False)
    response = client.get("/api/self/accuracy-alerts?threshold=0.7")
    assert response.status_code == 200
    assert response.json()["categories"][0]["alert"] is True


def test_sc13_rule_genealogy_reads_evolution_state() -> None:
    client, store = _client()
    store.save_evolution_state("trading", "rule-1", {"parent_id": "rule-0", "generation": 1})
    response = client.get("/api/self/rule-genealogy")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_sc14_decision_explorer_filters_category() -> None:
    client, store = _client()
    _seed_decision(store)
    response = client.get("/api/self/decisions?category=momentum")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_sc14_decision_explorer_filters_outcome() -> None:
    client, store = _client()
    _seed_decision(store, correct=False)
    response = client.get("/api/self/decisions?outcome=confirmed")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_sc15_rule_lifecycle_combines_age_state() -> None:
    client, store = _client()
    store.save_evolution_state("trading", "rule-1", {"generation": 2})
    store.save_promotion("trading", "rule-1", {"status": "promoted"})
    response = client.get("/api/self/rule-lifecycle/rule-1")
    assert response.status_code == 200
    assert response.json()["evolution"]["generation"] == 2
    assert response.json()["promotion"]["status"] == "promoted"


def test_sc16_audit_trail_reads_ledger_entries() -> None:
    client, store = _client()
    store.save_ledger("trading", "ledger-1", {"event": "decision_verified"})
    response = client.get("/api/self/audit-trail?limit=50")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_all_sc11_to_sc16_routes_are_mounted() -> None:
    client, _ = _client()
    paths = {route.path for route in client.app.routes}
    assert "/api/self/centroid-timeline" in paths
    assert "/api/self/accuracy-alerts" in paths
    assert "/api/self/rule-genealogy" in paths
    assert "/api/self/decisions" in paths
    assert "/api/self/rule-lifecycle/{rule_id}" in paths
    assert "/api/self/audit-trail" in paths


def test_all_sc_endpoints_use_response_models() -> None:
    client, _ = _client()
    expected = {
        "/api/self/centroid-timeline",
        "/api/self/accuracy-alerts",
        "/api/self/rule-genealogy",
        "/api/self/decisions",
        "/api/self/rule-lifecycle/{rule_id}",
        "/api/self/audit-trail",
    }
    routes = {route.path: route for route in client.app.routes if route.path in expected}
    assert all(route.response_model is not None for route in routes.values())


@pytest.mark.parametrize("path", [
    "/api/self/centroid-timeline",
    "/api/self/accuracy-alerts",
    "/api/self/rule-genealogy",
    "/api/self/decisions",
    "/api/self/rule-lifecycle/rule-absent",
    "/api/self/audit-trail",
])
def test_sc_surface_endpoint_smoke(path: str) -> None:
    client, _ = _client()
    assert client.get(path).status_code == 200


def test_sc12_accuracy_alerts_echoes_threshold() -> None:
    client, _ = _client()
    response = client.get("/api/self/accuracy-alerts?threshold=0.85")
    assert response.json()["threshold"] == 0.85


def test_sc13_genealogy_includes_domain() -> None:
    client, _ = _client()
    assert client.get("/api/self/rule-genealogy").json()["domain"] == "trading"


def test_sc16_audit_trail_honors_limit() -> None:
    client, store = _client()
    for index in range(3):
        store.save_ledger("trading", f"ledger-{index}", {"index": index})
    response = client.get("/api/self/audit-trail?limit=2")
    assert response.json()["total"] == 3
    assert len(response.json()["trails"]) == 2
