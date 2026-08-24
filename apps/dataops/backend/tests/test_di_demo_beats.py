from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


ENDPOINTS = (
    ("/api/dataops/di/earned-trust", ("live_trust", "what_if")),
    ("/api/dataops/di/acquisition-advice", ("recommendations", "gold_lines")),
    ("/api/dataops/di/abstention", ("should_abstain", "agent_action")),
    ("/api/dataops/di/trust-gateway", ("verifications", "safe_for_autonomous")),
    ("/api/dataops/di/source-compounding", ("source_count", "learning_curve")),
    ("/api/dataops/di/frozen-twin", ("frozen", "current_fingerprint")),
)


@pytest.mark.parametrize("path,_keys", ENDPOINTS)
def test_dataops_demo_beat_returns_success(client: TestClient, path: str, _keys: tuple[str, ...]) -> None:
    response = client.get(path)
    assert response.status_code == 200


@pytest.mark.parametrize("path,keys", ENDPOINTS)
def test_dataops_demo_beat_contract(path: str, keys: tuple[str, ...], client: TestClient) -> None:
    payload = client.get(path).json()
    assert all(key in payload for key in keys)


@pytest.mark.parametrize("path,_keys", ENDPOINTS)
def test_dataops_demo_beat_reports_provenance(client: TestClient, path: str, _keys: tuple[str, ...]) -> None:
    payload = client.get(path).json()
    assert isinstance(payload, dict)
    assert "provenance" in payload or "measurement_state" in payload or "observation_only" in payload
