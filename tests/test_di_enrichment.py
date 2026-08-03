from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.testclient import TestClient

from copilot_sdk.backend.conservation_utils import compute_conservation_status_payload
from copilot_sdk.di.models import ConsumerProfile


KNOWN_SOURCES = {
    "sap_s4hana",
    "salesforce_crm",
    "airflow_metadata",
    "alert_history",
    "pipeline_graph",
    "graph_traversal",
    "config",
}
FACTOR_TO_SOURCE = {"source_reliability": "sap_s4hana"}
SOURCE_COLUMN_BASELINES = {
    "sap_s4hana": {"customer_id": 0.99, "satisfaction_score": 0.14},
    "salesforce_crm": {"customer_id": 0.97, "account_tier": 0.82},
}
DATA_PRODUCTS = (
    {"product_id": "customer-360", "product_name": "Customer 360", "sources": ("sap_s4hana", "salesforce_crm")},
    {"product_id": "operations-health", "product_name": "Operations Health", "sources": ("airflow_metadata", "pipeline_graph")},
    {"product_id": "alert-intelligence", "product_name": "Alert Intelligence", "sources": ("alert_history", "graph_traversal")},
)


class _Store:
    domain = "dataops"

    def count_verified(self, domain: str) -> int:
        assert domain == self.domain
        return 340

    def count_verified_decisions(self, domain: str) -> int:
        assert domain == self.domain
        return 340

    def count_correct(self, domain: str) -> int:
        assert domain == self.domain
        return 300


class _Scorer:
    graph_store = _Store()

    def fingerprint(self) -> dict[str, object]:
        return {
            "factors": [
                {"name": "impact_scope", "weight": 0.87},
                {"name": "source_reliability", "weight": 0.94},
                {"name": "recurrence_frequency", "weight": 0.23},
                {"name": "downstream_urgency", "weight": 0.61},
                {"name": "data_freshness", "weight": 0.72},
                {"name": "business_criticality", "weight": 0.88},
            ]
        }


def _test_enrichment_router(scorer_provider: Callable[[], Any]) -> APIRouter:
    router = APIRouter()

    @router.get("/sources/{source_id}/consumers")
    def consumers(source_id: str) -> dict[str, Any]:
        _require_source(source_id)
        return {"source_id": source_id, "consumers": [profile.to_dict() for profile in _consumer_profiles(source_id)]}

    @router.get("/sources/{source_id}/trust")
    def trust(source_id: str) -> dict[str, Any]:
        _require_source(source_id)
        scorer = scorer_provider()
        source_trust = _source_trust(source_id, _factor_weights(scorer))
        conservation = _conservation(scorer)
        columns = [
            {"name": name, "trust": round(source_trust * baseline, 3), "label": _trust_label(source_trust * baseline)}
            for name, baseline in SOURCE_COLUMN_BASELINES.get(source_id, {}).items()
        ]
        return {
            "source_id": source_id,
            "trust_score": source_trust,
            "trust_label": _trust_label(source_trust),
            "conservation_status": conservation["status"],
            "verified_decisions": conservation["verified_decisions"],
            "dk_weight": source_trust,
            "recommendation": _recommendation(source_trust),
            "columns": columns,
        }

    @router.get("/products")
    def products() -> dict[str, Any]:
        scorer = scorer_provider()
        weights = _factor_weights(scorer)
        conservation = _conservation(scorer)
        result = []
        for product in DATA_PRODUCTS:
            source_ids = list(product["sources"])
            trusts = [_source_trust(source_id, weights) for source_id in source_ids]
            product_trust = sum(trusts) / len(trusts) if trusts else 0.0
            result.append({
                "product_id": product["product_id"],
                "product_name": product["product_name"],
                "iks": round(product_trust * 100),
                "conservation_status": conservation["status"],
                "verified_decisions": conservation["verified_decisions"],
                "sources": source_ids,
                "maturity_label": _maturity_label(product_trust),
            })
        return {"products": result}

    return router


def _require_source(source_id: str) -> None:
    if source_id not in KNOWN_SOURCES:
        raise HTTPException(status_code=404, detail=f"Unknown DI source: {source_id}")


def _consumer_profiles(source_id: str) -> list[ConsumerProfile]:
    return [
        ConsumerProfile("marketing_dashboard", source_id, {"freshness": "< 1hr", "completeness": "> 95%"}, 0.89, "stale data 2026-07-15"),
        ConsumerProfile("autonomous_triage_agent", source_id, {"freshness": "< 15min", "completeness": "> 98%"}, 0.94, None),
    ]


def _factor_weights(scorer: Any) -> dict[str, float]:
    return {
        str(factor["name"]): _bounded_float(factor.get("weight", factor.get("dk_weight", 0.0)))
        for factor in scorer.fingerprint().get("factors", []) or []
        if str(factor.get("name", "")).strip()
    }


def _source_trust(source_id: str, weights: dict[str, float]) -> float:
    mapped = [weight for factor, weight in weights.items() if FACTOR_TO_SOURCE.get(factor) == source_id]
    return round(sum(mapped) / len(mapped), 3) if mapped else 0.5


def _conservation(scorer: Any) -> dict[str, Any]:
    payload = compute_conservation_status_payload("dataops", scorer.graph_store)
    return {"status": str(payload.get("status", "UNAVAILABLE")), "verified_decisions": int(payload.get("verified_count", 0) or 0)}


def _bounded_float(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _trust_label(value: float) -> str:
    return "reliable" if value > 0.7 else "moderate" if value >= 0.3 else "noisy"


def _recommendation(value: float) -> str:
    return "Safe for autonomous agent consumption." if value > 0.7 else "Suitable for agent consumption with monitoring." if value >= 0.3 else "Do not use for autonomous agent consumption."


def _maturity_label(value: float) -> str:
    return "mature" if value > 0.7 else "developing" if value >= 0.3 else "emerging"


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(_test_enrichment_router(lambda: _Scorer()), prefix="/api/di")
    return TestClient(app)


def test_consumers_returns_profiles_with_quality_bars() -> None:
    payload = _client().get("/api/di/sources/sap_s4hana/consumers").json()
    assert payload["source_id"] == "sap_s4hana"
    assert len(payload["consumers"]) == 2
    assert payload["consumers"][0]["quality_bar"]["freshness"]
    assert 0.0 <= payload["consumers"][0]["satisfaction_rate"] <= 1.0


def test_consumers_unknown_source_returns_not_found() -> None:
    assert _client().get("/api/di/sources/missing/consumers").status_code == 404


def test_consumer_profiles_include_issue_field() -> None:
    consumers = _client().get("/api/di/sources/sap_s4hana/consumers").json()["consumers"]
    assert all("last_issue" in consumer for consumer in consumers)


def test_trust_uses_mapped_dk_weight_and_column_propagation() -> None:
    payload = _client().get("/api/di/sources/sap_s4hana/trust").json()
    assert payload["trust_score"] == 0.94
    assert payload["dk_weight"] == 0.94
    assert payload["columns"][0]["trust"] == 0.931
    assert payload["columns"][1]["label"] == "noisy"


def test_trust_returns_agent_recommendation_and_label() -> None:
    payload = _client().get("/api/di/sources/sap_s4hana/trust").json()
    assert payload["trust_label"] == "reliable"
    assert payload["recommendation"] == "Safe for autonomous agent consumption."


def test_trust_includes_conservation_and_verified_count() -> None:
    payload = _client().get("/api/di/sources/sap_s4hana/trust").json()
    assert payload["conservation_status"] in {"GREEN", "AMBER", "RED"}
    assert payload["verified_decisions"] == 340


def test_products_returns_per_product_iks() -> None:
    products = _client().get("/api/di/products").json()["products"]
    assert len(products) == 3
    customer_360 = next(product for product in products if product["product_id"] == "customer-360")
    assert customer_360["iks"] == 72
    assert customer_360["sources"] == ["sap_s4hana", "salesforce_crm"]


def test_products_include_maturity_and_conservation_fields() -> None:
    products = _client().get("/api/di/products").json()["products"]
    assert all(product["maturity_label"] in {"mature", "developing", "emerging"} for product in products)
    assert all(product["conservation_status"] in {"GREEN", "AMBER", "RED"} for product in products)


def test_products_have_verified_decision_count() -> None:
    products = _client().get("/api/di/products").json()["products"]
    assert all(product["verified_decisions"] == 340 for product in products)
