"""Contract tests for TRD-S1 through TRD-S4 situational endpoints."""

from fastapi.testclient import TestClient


def test_trd_s1_regime_mirror_has_regime_history(client: TestClient) -> None:
    response = client.get("/api/trading/regime/mirror")
    assert response.status_code == 200
    payload = response.json()
    assert "current_regime" in payload
    assert payload["regimes"]
    assert payload["observation_only"] is True


def test_trd_s1_regime_mirror_labels_evidence(client: TestClient) -> None:
    payload = client.get("/api/trading/regime/mirror").json()
    assert payload["evidence_tier"] in {"T_O", "T_S"}
    assert payload["observation"]


def test_trd_s1_regime_mirror_exposes_behavior_change(client: TestClient) -> None:
    payload = client.get("/api/trading/regime/mirror").json()
    assert "behavior_change" in payload
    assert "regimes" in payload["behavior_change"]


def test_trd_s2_abstention_has_day_zero_state(client: TestClient) -> None:
    response = client.get("/api/trading/regime/abstention")
    assert response.status_code == 200
    payload = response.json()
    assert "abstention_recommended" in payload
    assert "per_regime_day_zero" in payload
    assert payload["observation_only"] is True


def test_trd_s2_abstention_has_reasons_field(client: TestClient) -> None:
    payload = client.get("/api/trading/regime/abstention").json()
    assert isinstance(payload["abstention_reasons"], list)
    assert payload["evidence_tier"] in {"T_O", "INSUFFICIENT"}


def test_trd_s2_abstention_returns_json_safe_counts(client: TestClient) -> None:
    payload = client.get("/api/trading/regime/abstention").json()
    for value in payload["per_regime_day_zero"].values():
        assert isinstance(value["decision_count"], int)
        assert isinstance(value["verified_count"], int)


def test_trd_s3_throttle_has_authority_and_timeline(client: TestClient) -> None:
    response = client.get("/api/trading/regime/throttle")
    assert response.status_code == 200
    payload = response.json()
    assert "authority_level_by_regime" in payload
    assert "reconvergence_timeline" in payload
    assert payload["observation_only"] is True


def test_trd_s3_throttle_timeline_has_remaining(client: TestClient) -> None:
    payload = client.get("/api/trading/regime/throttle").json()
    assert payload["reconvergence_timeline"]["remaining"] >= 0


def test_trd_s3_throttle_labels_monitor_state(client: TestClient) -> None:
    payload = client.get("/api/trading/regime/throttle").json()
    assert isinstance(payload["regime_break_active"], bool)
    assert payload["evidence_tier"] in {"T_O", "T_S"}


def test_trd_s4_rejection_has_regime_context(client: TestClient) -> None:
    response = client.get("/api/trading/regime/rejection")
    assert response.status_code == 200
    payload = response.json()
    assert "rejections_by_regime" in payload
    assert "regime_context" in payload
    assert payload["observation_only"] is True


def test_trd_s4_rejection_preserves_rejection_counts(client: TestClient) -> None:
    payload = client.get("/api/trading/regime/rejection").json()
    assert isinstance(payload["variants_tested"], int)
    assert isinstance(payload["variants_rejected"], int)
    assert payload["variants_rejected"] >= payload["variants_tested"]


def test_trd_s4_rejection_labels_evidence(client: TestClient) -> None:
    payload = client.get("/api/trading/regime/rejection").json()
    assert payload["evidence_tier"] in {"T_O", "T_S"}
