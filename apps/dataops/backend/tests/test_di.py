from __future__ import annotations

from typing import Any
import pytest
from copilot_sdk.graph.memory_store import InMemoryGraphStore

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.query import create_query_router
from app.services.graph_enrichment import DataOpsGraphEnricher
from copilot_sdk.di import NLQueryRouter


def _seed_store():
    store = InMemoryGraphStore(domain="dataops")
    decision_id = store.write_decision("dataops", "freshness_violation", "investigate", 0.91,
        {"data_freshness": 0.2, "source_reliability": 0.9},
        metadata={"decision_id": "DOPS-1", "source_ids": ["sap_orders"]})
    store.write_outcome(decision_id, "investigate", True, domain="dataops")
    return store


def _enrichment(disposable_age, enrichment_id):
    store = disposable_age.store("dataops")._store
    return store._run_query(
        f"MATCH (n:EnrichmentNode {{enrichment_id: {store._S(enrichment_id)}}}) "
        "WHERE n.domain = 'dataops' RETURN n.enrichment_type AS enrichment_type, "
        "n.payload AS payload, n.source_ids AS source_ids"
    )


def test_nl_query_known_question_pattern_returns_intent():
    result = NLQueryRouter().query("Which source is most reliable?", _seed_store(), domain="dataops")

    assert result["intent"] == "source_reliability"
    assert result["answer"]
    assert result["evidence"]


def test_nl_query_unknown_question_returns_graceful_fallback():
    result = NLQueryRouter().query("tell me something unusual", _seed_store(), domain="dataops")

    assert result["intent"] == "unknown"
    assert result["answer"]
    assert result["evidence"] == []


def test_post_query_returns_answer_evidence_and_intent():
    store = _seed_store()
    app = FastAPI()
    app.include_router(create_query_router(lambda: store))
    response = TestClient(app).post("/api/dataops/query", json={"question": "freshness status?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "freshness"
    assert payload["answer"]
    assert payload["evidence"]


def test_post_query_missing_question_returns_400():
    app = FastAPI()
    app.include_router(create_query_router(lambda: _seed_store()))
    response = TestClient(app).post("/api/dataops/query", json={})

    assert response.status_code == 400


@pytest.mark.age
def test_graph_enricher_write_creates_node_and_returns_id(disposable_age):
    store = disposable_age.client()
    enrichment_id = DataOpsGraphEnricher().write_enrichment(
        store,
        ["sap_orders"],
        "quality_answer",
        {"answer": "freshness risk"},
    )

    rows = _enrichment(disposable_age, enrichment_id)
    assert len(rows) == 1
    assert rows[0]["enrichment_type"] == "quality_answer"


@pytest.mark.age
def test_graph_enricher_is_idempotent_for_same_sources_and_type(disposable_age):
    store = disposable_age.client()
    enricher = DataOpsGraphEnricher()

    first = enricher.write_enrichment(store, ["b", "a"], "quality_answer", {"version": 1})
    second = enricher.write_enrichment(store, ["a", "b"], "quality_answer", {"version": 2})

    assert first == second
    rows = _enrichment(disposable_age, first)
    assert len(rows) == 1
    assert rows[0]["payload"]["version"] == 2


@pytest.mark.age
def test_graph_enricher_persists_all_source_ids(disposable_age):
    store = disposable_age.client()
    enrichment_id = DataOpsGraphEnricher().write_enrichment(
        store,
        ["sap_orders", "salesforce_opportunities"],
        "source_profile",
        {"confidence": 0.94},
    )

    assert set(_enrichment(disposable_age, enrichment_id)[0]["source_ids"]) == {"sap_orders", "salesforce_opportunities"}


def test_query_router_registered_on_main_app(client):
    response = client.post("/api/dataops/query", json={"question": "what is the impact?"})

    assert response.status_code == 200
    assert response.json()["intent"] == "impact"


def test_di_source_profiles_router_registered_on_main_app(client):
    response = client.get("/api/di/profiles")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert {source["source_name"] for source in payload["sources"]} == {"airflow", "dbt", "snowflake"}
