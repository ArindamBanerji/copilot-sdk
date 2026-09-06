from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.purchasing_control import (
    CLAIMS,
    ProofLedger,
    PurchasingClaimRegistry,
    PurchasingEvidenceMiddleware,
)


def test_claim_registry_starts_synthetic_and_gate_is_fail_closed() -> None:
    registry = PurchasingClaimRegistry()
    result = registry.gate.check(CLAIMS["proof"], "pilot")
    assert result.tier.name == "T_S"
    assert result.passed is False
    assert "not measured" in result.label


def test_evidence_middleware_adds_get_headers_without_body_rewrite() -> None:
    registry = PurchasingClaimRegistry()
    app = FastAPI()
    app.add_middleware(PurchasingEvidenceMiddleware, registry=registry)

    @app.get("/api/purchasing/proof-ledger")
    def route() -> dict[str, str]:
        return {"status": "ok"}

    with TestClient(app) as client:
        response = client.get("/api/purchasing/proof-ledger")
    assert response.status_code == 200
    assert response.headers["X-Evidence-Tier"] == "T_S"
    assert response.headers["X-Evidence-Label"] == "synthetic / modelled - not measured"
    assert response.headers["X-Evidence-Gate"] in {"passed", "blocked"}
    assert response.json() == {"status": "ok"}


def test_evidence_middleware_adds_post_headers_and_fields() -> None:
    registry = PurchasingClaimRegistry()
    app = FastAPI()
    app.add_middleware(PurchasingEvidenceMiddleware, registry=registry)

    @app.post("/api/purchasing/proof-ledger")
    def route() -> dict[str, str]:
        return {"status": "ok"}

    with TestClient(app) as client:
        response = client.post("/api/purchasing/proof-ledger", json={"kind": "outcome"})
    assert response.status_code == 200
    assert response.headers["X-Evidence-Tier"] == "T_S"
    assert response.json()["evidence_tier"] == "T_S"
    assert response.json()["evidence_label"] == "synthetic / modelled — not measured"


def test_proof_ledger_persists_and_is_thread_safe(tmp_path) -> None:
    path = tmp_path / "proof.sqlite3"
    ledger = ProofLedger(path)

    def write(index: int) -> None:
        ledger.record("decision", {"decision_id": f"PUR-{index}", "evidence_tier": "T_S"})

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(write, range(20)))
    assert len(ledger.list_entries()) == 20
    reopened = ProofLedger(path)
    assert len(reopened.list_entries()) == 20


def test_purchasing_control_routes_are_mounted_and_json_safe(client) -> None:
    for path in (
        "/api/purchasing/proof-ledger",
        "/api/purchasing/handoff-pack",
        "/api/purchasing/day-0-readiness",
        "/api/purchasing/legal-exposure",
        "/api/purchasing/frozen-twin",
        "/api/purchasing/discovery-gate",
        "/api/purchasing/yield-quote-audit",
        "/api/purchasing/promotion",
    ):
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.headers["X-Evidence-Tier"]


def test_day_zero_and_discovery_are_not_yet_without_measured_outcomes(client) -> None:
    readiness = client.get("/api/purchasing/day-0-readiness").json()
    discovery = client.get("/api/purchasing/discovery-gate").json()
    assert readiness["not_yet"] is True
    assert discovery["decision"] == "NOT_YET"


def test_promotion_is_blocked_before_measured_evidence(client) -> None:
    response = client.post(
        "/api/purchasing/promotion/produce/advance",
        json={"conservation_status": "GREEN"},
    )
    assert response.status_code == 409
    assert "T_O" in response.json()["detail"]


def test_promotion_is_blocked_when_conservation_is_not_green(client) -> None:
    app = client.app
    registry = app.state.purchasing_claim_registry
    from copilot_sdk.evidence import ClaimRecord, EvidenceTier

    registry.gate.register(ClaimRecord(
        claim_id=CLAIMS["readiness"],
        description="measured purchasing readiness",
        tier=EvidenceTier.T_O,
        evidence_basis="verified outcome receipt",
        copilot="purchasing",
    ))
    response = client.post(
        "/api/purchasing/promotion/produce/advance",
        json={"conservation_status": "RED"},
    )
    assert response.status_code == 409
    assert "GREEN" in response.json()["detail"]


def test_verified_outcome_enters_proof_ledger(client) -> None:
    payload = {
        "copilot": "purchasing",
        "decision_id": "PUR-verified-control-1",
        "category": "produce",
        "factor_vector": [0.2, 0.4, 0.6],
        "predicted_action": "order",
        "human_disposition": "confirm",
        "correct": True,
        "measured_impact": {"waste_delta": -0.1},
        "evidence_provenance": "purchasing-test-receipt",
        "timestamp": "2026-08-18T00:00:00Z",
    }
    response = client.post("/api/purchasing/proof-ledger/outcome", json=payload)
    assert response.status_code == 200
    entries = client.get("/api/purchasing/proof-ledger").json()["entries"]
    assert any(entry["payload"].get("decision_id") == payload["decision_id"] for entry in entries)
