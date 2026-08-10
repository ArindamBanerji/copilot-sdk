"""Isolated tests for the ci-platform enterprise connector routes."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.enterprise_router import create_enterprise_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(create_enterprise_router(), prefix="/api/dataops")
    return TestClient(app)


def test_enterprise_health_returns_systems() -> None:
    response = _client().get("/api/dataops/enterprise-health")

    assert response.status_code == 200
    payload = response.json()
    assert {"sap", "celonis", "graph", "overall"} <= payload.keys()
    assert payload["sap"]["source"] == "fixture"
    assert payload["celonis"]["source"] == "fixture"


def test_enterprise_health_sap_metrics() -> None:
    payload = _client().get("/api/dataops/enterprise-health").json()

    assert payload["sap"]["record_count"] == 3
    assert payload["sap"]["open_purchase_order_value"] == 1_315_000
    assert payload["sap"]["exception_invoice_count"] == 1


def test_enterprise_health_celonis_metrics() -> None:
    payload = _client().get("/api/dataops/enterprise-health").json()

    assert payload["celonis"]["kpi_count"] == 2
    assert payload["celonis"]["bottleneck_activity"] == "Match Invoice to GR"
    assert payload["celonis"]["bottleneck_duration_seconds"] == 2520


def test_enterprise_health_fixture_fallback() -> None:
    payload = _client().get("/api/dataops/enterprise-health").json()

    assert payload["sap"]["live"] is False
    assert payload["celonis"]["live"] is False
    assert payload["sap"]["source"] == "fixture"
    assert payload["celonis"]["source"] == "fixture"


def test_process_data_returns_activities() -> None:
    response = _client().get("/api/dataops/process-data")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "fixture"
    assert payload["activities"]
    assert any(activity["name"] == "Match Invoice to GR" for activity in payload["activities"])


def test_sap_data_returns_purchase_orders() -> None:
    response = _client().get("/api/dataops/sap-data")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "fixture"
    assert len(payload["purchase_orders"]) == 3
    assert payload["purchase_orders"][0]["PurchaseOrder"] == "PO-4500001234"
