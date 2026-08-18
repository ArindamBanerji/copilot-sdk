"""Contract tests for the shared Evidence/Claim Gate (SH-01)."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.evidence import (
    ClaimRecord,
    EvidenceGate,
    EvidenceGateMiddleware,
    EvidenceTier,
    assert_no_sample,
    scan_for_sample,
)


def _claim(
    claim_id: str = "CLAIM-TEST",
    tier: EvidenceTier = EvidenceTier.T_O,
) -> ClaimRecord:
    return ClaimRecord(
        claim_id=claim_id,
        description="Measured test claim",
        tier=tier,
        evidence_basis="verified operational outcomes",
        copilot="test",
    )


def test_eg_01_register_claim_check_passes_at_correct_tier() -> None:
    gate = EvidenceGate()
    gate.register(_claim())

    result = gate.check("CLAIM-TEST", "pilot")

    assert result.passed is True
    assert result.tier is EvidenceTier.T_O
    assert result.minimum is EvidenceTier.T_O
    assert result.label == "measured"


def test_eg_02_check_fails_below_context_minimum() -> None:
    gate = EvidenceGate()
    gate.register(_claim(tier=EvidenceTier.T_S))

    result = gate.check("CLAIM-TEST", "pilot")

    assert result.passed is False
    assert result.minimum is EvidenceTier.T_O
    assert "not measured" in result.label


def test_eg_03_below_minimum_uses_honest_label() -> None:
    gate = EvidenceGate()
    gate.register(_claim(tier=EvidenceTier.T_S))

    result = gate.check("CLAIM-TEST", "publication")

    assert result.passed is False
    assert "synthetic" in result.label
    assert gate.get_label("CLAIM-TEST") == result.label


def test_eg_04_f26_scan_catches_sample_metric() -> None:
    payload = {
        "provenance": "sample",
        "metrics": {"roi": 42},
    }

    violations = scan_for_sample(payload)

    assert violations == ["metrics.roi"]
    with pytest.raises(ValueError, match="F-26"):
        assert_no_sample(payload)


def test_eg_05_f26_scan_passes_clean_metrics() -> None:
    payload = {
        "provenance": "observed",
        "metrics": {"roi": 42, "accuracy": 0.91},
        "structure": {"sample_size": 10},
    }

    assert scan_for_sample(payload) == []
    assert_no_sample(payload)


def test_eg_06_scan_all_returns_failing_claims_for_demo() -> None:
    gate = EvidenceGate()
    gate.register(_claim("SYN", EvidenceTier.T_S))
    gate.register(_claim("OBS", EvidenceTier.T_O))
    gate.register(_claim("REP", EvidenceTier.T_R))

    failures = gate.scan_all("publication")

    assert [result.claim_id for result in failures] == ["SYN", "OBS"]


def test_eg_07_scan_all_empty_when_all_claims_pass() -> None:
    gate = EvidenceGate()
    gate.register(_claim("OBS", EvidenceTier.T_O))
    gate.register(_claim("REP", EvidenceTier.T_R))

    assert gate.scan_all("pilot") == []


def test_eg_08_register_same_claim_updates_record() -> None:
    gate = EvidenceGate()
    gate.register(_claim("CLAIM-TEST", EvidenceTier.T_S))
    gate.register(_claim("CLAIM-TEST", EvidenceTier.T_O))

    result = gate.check("CLAIM-TEST", "pilot")

    assert result.passed is True
    assert gate.get_label("CLAIM-TEST") == "measured"


def test_eg_09_unknown_claim_id_is_clear() -> None:
    gate = EvidenceGate()

    result = gate.check("MISSING", "pilot")

    assert result.passed is False
    assert result.error == "Unknown claim_id: MISSING"
    with pytest.raises(KeyError, match="Unknown claim_id"):
        gate.get_label("MISSING")


def test_eg_10_unregistered_claim_fails_closed() -> None:
    result = EvidenceGate().check("NEVER-REGISTERED", "demo")

    assert result.passed is False
    assert result.label == "unregistered claim — blocked"


def test_eg_11_claim_record_json_round_trip() -> None:
    original = _claim("ROUNDTRIP", EvidenceTier.T_R)

    restored = ClaimRecord.from_json(original.to_json())

    assert restored == original
    assert restored.to_dict() == original.to_dict()


def test_eg_12_reproduced_claim_passes_all_contexts() -> None:
    gate = EvidenceGate()
    gate.register(_claim(tier=EvidenceTier.T_R))

    assert all(
        gate.check("CLAIM-TEST", context).passed
        for context in ("demo", "pilot", "publication")
    )


def test_eg_13_empty_evidence_basis_is_rejected() -> None:
    with pytest.raises(ValueError, match="evidence_basis"):
        ClaimRecord(
            claim_id="EMPTY-BASIS",
            description="No basis",
            tier=EvidenceTier.T_S,
            evidence_basis="",
            copilot="test",
        )


def test_eg_14_middleware_adds_evidence_headers() -> None:
    gate = EvidenceGate()
    gate.register(_claim(tier=EvidenceTier.T_O))
    app = FastAPI()
    app.add_middleware(
        EvidenceGateMiddleware,
        gate=gate,
        claim_id="CLAIM-TEST",
        context="pilot",
    )

    @app.get("/metric")
    def metric() -> dict[str, str]:
        return {"status": "ok"}

    with TestClient(app) as client:
        response = client.get("/metric")

    assert response.status_code == 200
    assert response.headers["X-Evidence-Tier"] == "T_O"
    assert response.headers["X-Evidence-Label"] == "measured"
    assert response.headers["X-Evidence-Gate"] == "passed"


def test_eg_15_thread_safe_register_and_check() -> None:
    gate = EvidenceGate()

    def register_and_check(index: int) -> bool:
        claim_id = f"CONCURRENT-{index}"
        gate.register(_claim(claim_id, EvidenceTier.T_O))
        return gate.check(claim_id, "pilot").passed

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(register_and_check, range(32)))

    assert all(results)
    assert len(gate.scan_all("publication")) == 32
