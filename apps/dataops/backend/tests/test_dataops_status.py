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
    assert {"sap", "celonis", "graph", "overall"} <= set(payload)
    assert payload["overall"] in {"healthy", "degraded", "disconnected"}
    assert isinstance(payload["sap"]["connected"], bool)
    assert isinstance(payload["sap"]["record_count"], int)
    assert "last_sync" in payload["sap"]
    assert payload["sap"]["last_sync"] is None or isinstance(payload["sap"]["last_sync"], str)
    assert isinstance(payload["celonis"]["connected"], bool)
    assert isinstance(payload["celonis"]["kpi_count"], int)
    assert "last_sync" in payload["celonis"]
    assert payload["celonis"]["last_sync"] is None or isinstance(payload["celonis"]["last_sync"], str)
    assert isinstance(payload["graph"]["connected"], bool)
    assert isinstance(payload["graph"]["node_count"], int)
    assert_json_safe(payload)


def test_enterprise_health_alias_handles_subsystem_failure(client: TestClient, monkeypatch) -> None:
    from app.routers import dataops_status

    def fail_sap_status() -> dict[str, Any]:
        raise RuntimeError("secret-token traceback should not leak")

    monkeypatch.setattr(dataops_status, "_sap_status", fail_sap_status)

    response = client.get("/api/dataops/enterprise-health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sap"] == {"connected": False, "record_count": 0, "last_sync": None}
    assert "secret-token" not in response.text
    assert payload["overall"] in {"degraded", "disconnected"}
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
