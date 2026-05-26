from __future__ import annotations

import math
from typing import Any

from fastapi.testclient import TestClient


def test_dataops_health_alias_returns_domain_status(client: TestClient) -> None:
    response = client.get("/api/dataops/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"healthy", "degraded", "unknown"}
    assert payload["domain"] == "dataops"
    assert {"scorer", "conservation", "connectors"} <= set(payload)
    assert {"celonis", "sap"} <= set(payload["connectors"])
    assert_json_safe(payload)


def test_celonis_status_alias_is_offline_safe(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("CELONIS_URL", "https://example.invalid")

    response = client.get("/api/dataops/celonis/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["connector"] == "celonis"
    assert payload["status"] in {"available", "configured", "fixture", "unconfigured", "unknown"}
    assert payload["connection_state"]
    assert payload["source"] in {"connector", "fixture", "config", "unknown"}
    assert payload["live"] is False
    assert_json_safe(payload)


def test_sap_status_alias_is_offline_safe(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("SAP_API_KEY", "test-key")

    response = client.get("/api/dataops/sap/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["connector"] == "sap"
    assert payload["status"] in {"available", "configured", "fixture", "unconfigured", "unknown"}
    assert payload["connection_state"]
    assert payload["source"] in {"connector", "fixture", "config", "unknown"}
    assert payload["live"] is False
    assert_json_safe(payload)


def test_enterprise_health_alias_returns_combined_payload(client: TestClient) -> None:
    response = client.get("/api/dataops/enterprise-health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "dataops"
    assert {"sap", "celonis"} <= set(payload["connectors"])
    assert {"sap", "celonis", "graph", "engine_version"} <= set(payload["enterprise"])
    assert payload["enterprise"]["graph"]["pipeline_count"] >= 0
    assert_json_safe(payload)


def test_existing_health_endpoints_remain_available(client: TestClient) -> None:
    api_health = client.get("/api/health")
    context_health = client.get("/api/context/enterprise-health")

    assert api_health.status_code == 200
    assert "engine" in api_health.json()
    assert context_health.status_code == 200
    assert {"sap", "celonis", "graph"} <= set(context_health.json())


def assert_json_safe(value: Any) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            assert_json_safe(nested)
    elif isinstance(value, list):
        for nested in value:
            assert_json_safe(nested)
    elif isinstance(value, float):
        assert math.isfinite(value)
