from __future__ import annotations

from fastapi.testclient import TestClient


def test_gw_01_verification_endpoint_returns_200(client: TestClient) -> None:
    response = client.get("/api/di/trust/verify")
    assert response.status_code == 200


def test_gw_02_verification_endpoint_returns_history(client: TestClient) -> None:
    payload = client.get("/api/di/trust/verify").json()
    assert isinstance(payload["verifications"], list)
    assert payload["verifications"]


def test_gw_03_summary_counts_match_history(client: TestClient) -> None:
    payload = client.get("/api/di/trust/verify").json()
    rows = payload["verifications"]
    summary = payload["summary"]
    assert summary["total"] == len(rows)
    assert summary["passed"] + summary["blocked"] + summary["abstained"] == len(rows)


def test_gw_04_category_filter_is_applied(client: TestClient) -> None:
    response = client.get("/api/di/trust/verify?category=schema_change")
    assert response.status_code == 200
    assert all(row["category"] == "schema_change" for row in response.json()["verifications"])


def test_gw_05_gate_results_are_explicit(client: TestClient) -> None:
    payload = client.get("/api/di/trust/verify").json()
    assert {row["gate_result"] for row in payload["verifications"]} <= {"PASS", "BLOCK", "ABSTAIN"}


def test_gw_06_unknown_source_abstains(client: TestClient) -> None:
    payload = client.get("/api/dataops/abstention-check?source_id=DI-ABSTENTION-001").json()
    assert payload["should_abstain"] is True


def test_gw_07_abstention_fixture_is_present(client: TestClient) -> None:
    alerts = client.get("/api/context/alerts").json()["alerts"]
    fixture = next(alert for alert in alerts if alert["alert_id"] == "DI-ABSTENTION-001")
    assert fixture["category"] == "unseen_source_anomaly"
    assert fixture["novelty_score"] > 0.9


def test_gw_08_verification_history_uses_preseed_data(client: TestClient) -> None:
    rows = client.get("/api/di/trust/verify").json()["verifications"]
    assert rows[0]["action_id"]
    assert rows[0]["evidence_tier"] in {"T_S", "T_O"}
