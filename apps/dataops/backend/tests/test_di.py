from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.query import create_query_router
from app.services.graph_enrichment import DataOpsGraphEnricher
from copilot_sdk.di import NLQueryRouter


class GraphStore:
    def __init__(self) -> None:
        self.enrichments: dict[str, dict[str, Any]] = {}
        self.links: list[tuple[str, str]] = []

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        return [
            {
                "decision_id": "DOPS-1",
                "category": "freshness_violation",
                "confidence": 0.91,
                "metadata": {"source_ids": ["sap_orders"]},
                "factors": {"data_freshness": 0.2, "source_reliability": 0.9},
            }
        ]

    def write_enrichment(self, record: dict[str, Any]) -> str:
        self.enrichments[record["enrichment_id"]] = dict(record)
        return str(record["enrichment_id"])

    def link_enrichment_source(self, enrichment_id: str, source_id: str) -> None:
        link = (enrichment_id, source_id)
        if link not in self.links:
            self.links.append(link)


def test_nl_query_known_question_pattern_returns_intent():
    result = NLQueryRouter().query("Which source is most reliable?", GraphStore())

    assert result["intent"] == "source_reliability"
    assert result["answer"]
    assert result["evidence"]


def test_nl_query_unknown_question_returns_graceful_fallback():
    result = NLQueryRouter().query("tell me something unusual", GraphStore())

    assert result["intent"] == "unknown"
    assert result["answer"]
    assert result["evidence"] == []


def test_post_query_returns_answer_evidence_and_intent():
    store = GraphStore()
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
    app.include_router(create_query_router(lambda: GraphStore()))
    response = TestClient(app).post("/api/dataops/query", json={})

    assert response.status_code == 400


def test_graph_enricher_write_creates_node_and_returns_id():
    store = GraphStore()
    enrichment_id = DataOpsGraphEnricher().write_enrichment(
        store,
        ["sap_orders"],
        "quality_answer",
        {"answer": "freshness risk"},
    )

    assert enrichment_id in store.enrichments
    assert store.enrichments[enrichment_id]["enrichment_type"] == "quality_answer"


def test_graph_enricher_is_idempotent_for_same_sources_and_type():
    store = GraphStore()
    enricher = DataOpsGraphEnricher()

    first = enricher.write_enrichment(store, ["b", "a"], "quality_answer", {"version": 1})
    second = enricher.write_enrichment(store, ["a", "b"], "quality_answer", {"version": 2})

    assert first == second
    assert len(store.enrichments) == 1
    assert store.enrichments[first]["payload"]["version"] == 2


def test_graph_enricher_links_all_source_ids():
    store = GraphStore()
    enrichment_id = DataOpsGraphEnricher().write_enrichment(
        store,
        ["sap_orders", "salesforce_opportunities"],
        "source_profile",
        {"confidence": 0.94},
    )

    assert (enrichment_id, "sap_orders") in store.links
    assert (enrichment_id, "salesforce_opportunities") in store.links


def test_query_router_registered_on_main_app(client):
    response = client.post("/api/dataops/query", json={"question": "what is the impact?"})

    assert response.status_code == 200
    assert response.json()["intent"] == "impact"
