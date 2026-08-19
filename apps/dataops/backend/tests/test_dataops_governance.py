from __future__ import annotations

from fastapi.testclient import TestClient


def test_de_01_claim_registry_initialized(client: TestClient) -> None:
    payload = client.get("/api/dataops/claims").json()
    assert len(payload["claims"]) == 3


def test_de_02_api_responses_include_evidence_tier(client: TestClient) -> None:
    response = client.get("/api/dataops/claims")
    assert response.headers["x-evidence-tier"] == "synthetic"


def test_de_03_synthetic_claim_gets_modelled_label(client: TestClient) -> None:
    claim = client.get("/api/dataops/claims").json()["claims"][0]
    assert "modelled" in claim["label"]


def test_de_04_measured_claim_label_is_available_after_verification(client: TestClient) -> None:
    client.post("/api/dataops/holdout/register", json={"decision_id": "D1", "source_id": "src", "decision_class": "quality"})
    client.post("/api/dataops/holdout/verify", json={"decision_id": "D1", "verdict": {"expert": "accepted"}})
    assert client.get("/api/dataops/abstention-check?source_id=src").json()["evidence_tier"] == "observed"


def test_de_05_abstention_insufficient(client: TestClient) -> None:
    assert client.get("/api/dataops/abstention-check?source_id=empty").json()["should_abstain"] is True


def test_de_06_abstention_floor_can_be_met(client: TestClient) -> None:
    for index in range(2):
        client.post("/api/dataops/holdout/register", json={"decision_id": f"D{index}", "source_id": "src", "decision_class": "quality"})
        client.post("/api/dataops/holdout/verify", json={"decision_id": f"D{index}", "verdict": {"accepted": True}})
    assert client.get("/api/dataops/abstention-check?source_id=src&evidence_floor=2").json()["should_abstain"] is False


def test_de_07_abstention_contract_has_reason(client: TestClient) -> None:
    payload = client.get("/api/dataops/abstention-check?source_id=x").json()
    assert payload["reason"] == "insufficient_verified_evidence"


def test_de_08_holdout_status_has_30_day_window(client: TestClient) -> None:
    assert client.get("/api/dataops/holdout/status").json()["holdout_days"] == 30


def test_de_09_holdout_verify_records_verdict(client: TestClient) -> None:
    client.post("/api/dataops/holdout/register", json={"decision_id": "D9", "source_id": "src", "decision_class": "drift"})
    payload = client.post("/api/dataops/holdout/verify", json={"decision_id": "D9", "verdict": {"correct": True}}).json()
    assert payload["verdict"]["correct"] is True


def test_de_10_holdout_verify_upgrades_tier(client: TestClient) -> None:
    client.post("/api/dataops/holdout/register", json={"decision_id": "D10", "source_id": "src", "decision_class": "drift"})
    client.post("/api/dataops/holdout/verify", json={"decision_id": "D10", "verdict": {"correct": True}})
    entry = client.get("/api/dataops/holdout/status?source_id=src").json()["entries"][-1]
    assert entry["evidence_tier"] == "observed"


def test_de_11_unknown_provenance_is_404(client: TestClient) -> None:
    assert client.get("/api/dataops/provenance/missing").status_code == 404


def test_de_12_holdout_preserves_factor_vector(client: TestClient) -> None:
    client.post("/api/dataops/holdout/register", json={"decision_id": "D12", "source_id": "src", "decision_class": "quality", "factor_vector": [0.1, 0.2]})
    assert client.get("/api/dataops/holdout/status").json()["entries"][0]["factor_vector"] == [0.1, 0.2]


def test_de_13_promotion_starts_discovered(client: TestClient) -> None:
    payload = client.post("/api/dataops/promotion", json={"decision_class": "quality"}).json()
    assert payload["current_stage"] == "discovered"


def test_de_14_promotion_requires_observed_evidence_after_shadow(client: TestClient) -> None:
    record = client.post("/api/dataops/promotion", json={"decision_class": "quality"}).json()
    client.post(f"/api/dataops/promotion/{record['record_id']}/advance", json={})
    blocked = client.post(f"/api/dataops/promotion/{record['record_id']}/advance", json={}).json()
    assert blocked["reason"] == "evidence_below_T_O"


def test_de_15_existing_health_still_returns_200(client: TestClient) -> None:
    assert client.get("/api/dataops/health").status_code == 200


def test_de_16_holdout_verification_changes_evidence_for_later_check(client: TestClient) -> None:
    before = client.get("/api/dataops/abstention-check?source_id=live").json()
    client.post("/api/dataops/holdout/register", json={"decision_id": "D16", "source_id": "live", "decision_class": "quality"})
    client.post("/api/dataops/holdout/verify", json={"decision_id": "D16", "verdict": {"correct": True}})
    after = client.get("/api/dataops/abstention-check?source_id=live").json()
    assert after["current_evidence"] == before["current_evidence"] + 1


def test_de_17_frozen_twin_status_is_explicit(client: TestClient) -> None:
    payload = client.get("/api/dataops/frozen-twin/status").json()
    assert payload["frozen"] is False


def test_de_18_concurrent_safe_holdout_reads(client: TestClient) -> None:
    for index in range(3):
        client.post("/api/dataops/holdout/register", json={"decision_id": f"D18-{index}", "source_id": "src", "decision_class": "quality"})
    assert len(client.get("/api/dataops/holdout/status?source_id=src").json()["entries"]) == 3


def test_de_19_json_safe_holdout_output(client: TestClient) -> None:
    response = client.get("/api/dataops/holdout/status")
    assert response.headers["content-type"].startswith("application/json")


def test_de_20_full_holdout_pipeline(client: TestClient) -> None:
    created = client.post("/api/dataops/holdout/register", json={"decision_id": "D20", "source_id": "pipeline", "decision_class": "quality", "score_payload": {"confidence": 0.8}})
    assert created.status_code == 200
    verified = client.post("/api/dataops/holdout/verify", json={"decision_id": "D20", "verdict": {"expert": "accepted", "correct": True}})
    assert verified.json()["evidence_tier"] == "observed"
    assert client.get("/api/dataops/abstention-check?source_id=pipeline").json()["current_evidence"] == 1
