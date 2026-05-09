from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend import evolution_router
from copilot_sdk.backend.evolution_router import create_evolution_router


class FakeLedger:
    pass


def build_client(ledger_provider=None) -> TestClient:
    app = FastAPI()
    app.include_router(create_evolution_router("dataops", ledger_provider=ledger_provider))
    return TestClient(app)


def test_factory_creates_apirouter():
    router = create_evolution_router("dataops")

    assert isinstance(router, APIRouter)


def test_variants_returns_empty_shape_and_engine_without_ledger():
    client = build_client()

    response = client.get("/evolution/variants")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "dataops"
    assert payload["engine"]["gae"] == "gae.evolution"
    assert payload["engine"]["component"] == "get_recent_events"
    assert payload["variants"] == []


def test_patterns_returns_empty_shape_and_engine_without_ledger():
    client = build_client()

    response = client.get("/evolution/patterns")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "dataops"
    assert payload["engine"]["gae"] == "gae.evolution"
    assert payload["engine"]["component"] == "get_evolution_summary"
    assert payload["patterns"] == []
    assert payload["summary"]["variants_generated"] == 0


def test_variants_uses_gae_recent_events(monkeypatch):
    async def fake_recent_events(client, limit=20):
        assert isinstance(client, FakeLedger)
        assert limit == 7
        return [
            {
                "id": "evo-1",
                "variant_id": "variant-1",
                "event_type": "variant_created",
                "artifact_type": "routing_rule",
                "description": "candidate generated",
                "impact": "operational",
                "magnitude": 0.4,
                "timestamp": "2026-05-08T00:00:00Z",
                "timestamp_epoch": 1,
                "metadata": {"wins": 3, "total": 5},
            }
        ]

    monkeypatch.setattr(evolution_router.evolution, "get_recent_events", fake_recent_events)
    client = build_client(ledger_provider=FakeLedger)

    response = client.get("/evolution/variants?limit=7")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["variants"]) == 1
    assert payload["variants"][0]["variant_id"] == "variant-1"
    assert payload["variants"][0]["metadata"] == {"wins": 3, "total": 5}


def test_patterns_uses_gae_summary_and_origin_fields(monkeypatch):
    async def fake_recent_events(client, limit=20):
        assert isinstance(client, FakeLedger)
        return [
            {
                "variant_id": "variant-1",
                "artifact_type": "routing_rule",
                "description": "warm-started candidate",
                "source_copilot": "soc",
                "source_rule": "rule-7",
                "warm_start_prior": {"win_rate": 0.8},
            },
            {
                "variant_id": "variant-2",
                "artifact_type": "context_policy",
                "description": "local candidate",
            },
        ]

    async def fake_summary(client):
        assert isinstance(client, FakeLedger)
        return {"variants_generated": 2, "variants_promoted": 1}

    monkeypatch.setattr(evolution_router.evolution, "get_recent_events", fake_recent_events)
    monkeypatch.setattr(evolution_router.evolution, "get_evolution_summary", fake_summary)
    client = build_client(ledger_provider=FakeLedger)

    response = client.get("/evolution/patterns")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == {"variants_generated": 2, "variants_promoted": 1}
    assert len(payload["patterns"]) == 1
    assert payload["patterns"][0]["source_copilot"] == "soc"
    assert payload["patterns"][0]["warm_start_prior"] == {"win_rate": 0.8}


def test_no_forbidden_modules_loaded():
    import sys

    build_client().get("/evolution/variants")

    assert not any("domains.soc" in module for module in sys.modules)
    assert not any("domains.s2p" in module for module in sys.modules)
    assert not any("gen-ai-roi-demo" in module for module in sys.modules)
