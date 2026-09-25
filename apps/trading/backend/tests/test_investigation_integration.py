"""HTTP contract against the app mount and frozen SDK investigator."""
from copy import deepcopy
import sqlite3
from types import SimpleNamespace
import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.investigation_router import create_investigation_router
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.investigation import KUtilityStore
from app.investigation_config import INVESTIGATION_CONFIG as CONFIG, create_evidence_provider


@pytest.fixture
def isolated():
    graph = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset("trading", graph_store=graph, profile="test")
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    k_store = KUtilityStore(SimpleNamespace(conn=conn), len(CONFIG["factor_names"]))
    conn.execute("INSERT INTO k_utility VALUES (?, ?, ?, ?)", (CONFIG["category_names"][0], 0, 0.9, 20))
    conn.commit()
    app = FastAPI()
    app.include_router(create_investigation_router(
        lambda: scorer, lambda did: create_evidence_provider(graph, did),
        factor_names=CONFIG["factor_names"], default_budget=2,
        gated_sources=CONFIG["gated_sources"], k_store=k_store))
    app.state.test_k_store = k_store
    with TestClient(app) as client:
        yield client, scorer, graph
    graph.close()
    conn.close()


def request_payload(budget=2):
    return {"decision_id": "tier5c-integration", "category": CONFIG["category_names"][0],
            "factor_vector": [0.5] * len(CONFIG["factor_names"]), "budget": budget, "use_K": False}


def test_investigation_endpoint_exists(client):
    response = client.get("/api/investigation/health")
    assert response.status_code == 200
    assert response.json()["investigation_available"]
    paths = [r.path for r in client.app.routes]
    assert paths.count("/api/investigation/investigate") == 1


def test_investigate_returns_trace(client):
    response = client.post("/api/investigation/investigate", json=request_payload())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["steps"] and body["snapshot"]["geometry_hash"]
    assert body["decision_id"] == "tier5c-integration"


@pytest.mark.parametrize("budget", [0, 1, 2])
def test_investigate_respects_budget(isolated, budget):
    client, _, _ = isolated
    response = client.post("/api/investigation/investigate", json=request_payload(budget))
    assert response.status_code == 200, response.text
    steps = response.json()["steps"]
    assert len(steps) <= budget
    assert len({s["dimension"] for s in steps}) == len(steps)


def test_investigate_uses_providers(client, monkeypatch):
    calls = []
    def read(provider, entity_id, data_source=None, **kwargs):
        calls.append((provider.factor_name, entity_id))
        return {"value": 0.25, "confidence": 1.0, "source": "SYNTHETIC:test"}
    for provider in CONFIG["provider_registry"].values():
        monkeypatch.setattr(type(provider), "read_payload", read)
    response = client.post("/api/investigation/investigate", json=request_payload())
    assert response.status_code == 200, response.text
    assert len(calls) == len(response.json()["steps"]) == 2
    assert [x[0] for x in calls] == [s["factor_name"] for s in response.json()["steps"]]


def test_investigation_read_only(isolated, monkeypatch):
    client, scorer, graph = isolated
    before_geometry = scorer.gae_scorer.centroids.copy()
    before_state = deepcopy(graph.__dict__)
    k_store = client.app.state.test_k_store
    before_k = k_store.conn.execute("SELECT * FROM k_utility").fetchall()
    def forbidden(*args, **kwargs):
        raise AssertionError("Investigation attempted a scorer write")
    monkeypatch.setattr(scorer, "learn", forbidden)
    monkeypatch.setattr(scorer, "score", forbidden)
    response = client.post("/api/investigation/investigate", json={**request_payload(), "use_K": True})
    assert response.status_code == 200, response.text
    np.testing.assert_array_equal(before_geometry, scorer.gae_scorer.centroids)
    assert repr(graph.__dict__) == repr(before_state)
    assert k_store.conn.execute("SELECT * FROM k_utility").fetchall() == before_k
    assert response.json()["snapshot"]["k_weights"][0] == 0.9


def test_missing_data_provenance_survives_sdk_response(isolated, monkeypatch):
    client, _, _ = isolated
    # Uniform geometry-independent selection forcing is test-only: verify dispatch/provenance.
    from copilot_sdk.scoring.investigation import VLDInvestigator
    original = VLDInvestigator.compute_Q
    def prioritize(self, *args, **kwargs):
        q = original(self, *args, **kwargs)
        q[9] = 1e9
        return q
    monkeypatch.setattr(VLDInvestigator, "compute_Q", prioritize)
    response = client.post("/api/investigation/investigate", json=request_payload(1))
    assert response.status_code == 200, response.text
    assert response.json()["steps"][0]["evidence_source"].startswith("MISSING_DATA:neutral:")
