from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.evolution_router import create_evolution_router


class RecordingGraphStore:
    def __init__(self) -> None:
        self.events = []

    def save_evolution_event(self, domain, event_type=None, rule_name="", variant_id="", metadata=None):
        if event_type is None or (variant_id == "" and rule_name):
            old_event_type = domain
            old_rule_name = event_type or ""
            old_variant_id = rule_name
            domain = "dataops"
            event_type = old_event_type
            rule_name = old_rule_name
            variant_id = old_variant_id
        self.events.append((domain, event_type, rule_name, variant_id, metadata or {}))


def build_client(graph_store_factory=None, domain="dataops") -> TestClient:
    app = FastAPI()
    app.include_router(
        create_evolution_router(
            graph_store_factory=graph_store_factory,
            domain=domain,
        )
    )
    return TestClient(app)


def test_factory_creates_apirouter():
    router = create_evolution_router(domain="dataops")

    assert isinstance(router, APIRouter)


def test_variants_returns_empty_active_and_promoted_on_fresh_router():
    client = build_client()

    response = client.get("/api/evolution/variants")

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "domain": "dataops",
        "variants": [],
        "active_rules": [],
        "promoted_rules": [],
        "total_active": 0,
        "total_promoted": 0,
    }


def test_history_returns_empty_on_fresh_router():
    client = build_client()

    response = client.get("/api/evolution/history")

    assert response.status_code == 200
    assert response.json() == {"domain": "dataops", "events": [], "count": 0}


def test_promoted_returns_empty_on_fresh_router():
    client = build_client()

    response = client.get("/api/evolution/promoted")

    assert response.status_code == 200
    assert response.json() == {"domain": "dataops", "promoted": []}


def test_domain_is_propagated():
    client = build_client(domain="custom")

    assert client.get("/api/evolution/variants").json()["domain"] == "custom"
    assert client.get("/api/evolution/history").json()["domain"] == "custom"
    assert client.get("/api/evolution/promoted").json()["domain"] == "custom"


def test_graph_store_factory_called_lazily():
    calls = []

    def factory():
        calls.append(RecordingGraphStore())
        return calls[-1]

    client = build_client(graph_store_factory=factory)
    assert calls == []

    response = client.get("/api/evolution/variants")

    assert response.status_code == 200
    assert len(calls) == 1


def test_variants_uses_variant_provider_when_available():
    app = FastAPI()
    app.include_router(
        create_evolution_router(
            domain="dataops",
            variant_provider=lambda: [{"id": "variant-1", "description": "candidate"}],
        )
    )
    client = TestClient(app)

    payload = client.get("/api/evolution/variants").json()

    assert payload["variants"] == [{"id": "variant-1", "description": "candidate"}]
    assert payload["active_rules"] == []


def test_graph_store_factory_called_once_per_router_instance():
    calls = []

    def factory():
        calls.append(RecordingGraphStore())
        return calls[-1]

    client = build_client(graph_store_factory=factory)

    client.get("/api/evolution/variants")
    client.get("/api/evolution/history")
    client.get("/api/evolution/promoted")

    assert len(calls) == 1


def test_two_router_instances_have_distinct_evolver_closures():
    calls_a = []
    calls_b = []

    def factory_a():
        calls_a.append(RecordingGraphStore())
        return calls_a[-1]

    def factory_b():
        calls_b.append(RecordingGraphStore())
        return calls_b[-1]

    client_a = build_client(graph_store_factory=factory_a, domain="a")
    client_b = build_client(graph_store_factory=factory_b, domain="b")

    assert client_a.get("/api/evolution/variants").json()["domain"] == "a"
    assert client_b.get("/api/evolution/variants").json()["domain"] == "b"
    assert len(calls_a) == 1
    assert len(calls_b) == 1
    assert calls_a[0] is not calls_b[0]


def test_no_forbidden_modules_loaded():
    import sys

    build_client().get("/api/evolution/variants")

    assert not any("domains.soc" in module for module in sys.modules)
    assert not any("domains.s2p" in module for module in sys.modules)
    assert not any("gen-ai-roi-demo" in module for module in sys.modules)
