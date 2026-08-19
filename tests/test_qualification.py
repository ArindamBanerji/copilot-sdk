"""Contract tests for the Day-0 qualification gate."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.evidence import ClaimRecord, EvidenceGate, EvidenceTier
from copilot_sdk.pilot import (
    ConservationHealthCheck,
    EvidenceGateCheck,
    FrozenTwinCheck,
    PromotionRecordsCheck,
    QualificationCheck,
    QualificationGate,
    TruthPreflightCheck,
    VerifiedCountCheck,
    create_qualification_router,
)
from copilot_sdk.promotion import PromotionEngine, S2PPromotionPolicy


class _Twin:
    def __init__(self, frozen: bool) -> None:
        self.frozen = frozen

    def is_frozen(self) -> bool:
        return self.frozen


def _evidence_gate(tier: EvidenceTier = EvidenceTier.T_O) -> EvidenceGate:
    gate = EvidenceGate()
    gate.register(ClaimRecord("PILOT-1", "Operational claim", tier, "verified outcomes", "test"))
    return gate


def _promotion_engine(with_record: bool = True) -> PromotionEngine:
    engine = PromotionEngine(S2PPromotionPolicy())
    if with_record:
        engine.create("test", "class-a")
    return engine


def _checks() -> list[QualificationCheck]:
    return [
        FrozenTwinCheck(_Twin(True)),
        EvidenceGateCheck(_evidence_gate()),
        PromotionRecordsCheck(_promotion_engine()),
        ConservationHealthCheck(lambda: {"phase": "GREEN"}),
        VerifiedCountCheck(3, minimum=1),
        TruthPreflightCheck(lambda copilot: []),
    ]


def test_pq_01_all_checks_pass_for_preseeded_copilot() -> None:
    report = QualificationGate().run("test", _checks())
    assert report.passed
    assert len(report.checks) == 6


def test_pq_02_frozen_twin_missing_fails() -> None:
    result = FrozenTwinCheck(_Twin(False)).check("test")
    assert not result.passed


def test_pq_03_unregistered_claims_fail() -> None:
    result = EvidenceGateCheck(EvidenceGate()).check("test")
    assert not result.passed


def test_pq_04_missing_promotion_records_fail() -> None:
    result = PromotionRecordsCheck(_promotion_engine(False)).check("test")
    assert not result.passed


def test_pq_05_red_conservation_fails() -> None:
    result = ConservationHealthCheck(lambda: {"phase": "RED"}).check("test")
    assert not result.passed


def test_pq_06_verified_count_floor_fails() -> None:
    result = VerifiedCountCheck(2, minimum=3).check("test")
    assert not result.passed


def test_pq_07_truth_preflight_wraps_checker() -> None:
    result = TruthPreflightCheck(lambda copilot: ["F-26"]).check("test")
    assert not result.passed
    assert result.evidence["failures"] == ["F-26"]


def test_pq_08_report_contains_every_result() -> None:
    report = QualificationGate().run("test", _checks())
    assert {result.name for result in report.checks} == {
        "frozen_twin", "evidence_gate", "promotion_records",
        "conservation_health", "verified_count", "truth_preflight",
    }


def test_pq_09_report_hash_is_deterministic() -> None:
    first = QualificationGate().run("test", _checks())
    second = QualificationGate().run("test", _checks())
    assert first.report_hash == second.report_hash


def test_pq_10_partial_failures_fail_report() -> None:
    report = QualificationGate().run("test", [FrozenTwinCheck(_Twin(False))])
    assert not report.passed


def test_pq_11_router_qualify_works() -> None:
    app = FastAPI()
    app.include_router(create_qualification_router(QualificationGate(), lambda _: _checks(), ["test"]))
    response = TestClient(app).get("/api/pilot/qualify", params={"copilot": "test"})
    assert response.status_code == 200
    assert response.json()["passed"] is True


def test_pq_12_cli_dry_run_contract() -> None:
    from scripts.qualify_for_pilot import main

    assert main(["--copilot", "trading", "--dry-run"]) == 0


def test_pq_13_qualify_all_returns_each_copilot() -> None:
    app = FastAPI()
    app.include_router(create_qualification_router(QualificationGate(), lambda _: _checks(), ["a", "b"]))
    response = TestClient(app).get("/api/pilot/qualify/all")
    assert [row["copilot"] for row in response.json()["reports"]] == ["a", "b"]


def test_pq_14_check_order_does_not_change_outcome() -> None:
    gate = QualificationGate()
    first = gate.run("test", _checks())
    second = gate.run("test", list(reversed(_checks())))
    assert first.passed == second.passed
    assert {item.name for item in first.checks} == {item.name for item in second.checks}


def test_pq_15_concurrent_qualification_is_safe() -> None:
    gate = QualificationGate()
    with ThreadPoolExecutor(max_workers=4) as pool:
        reports = list(pool.map(lambda _: gate.run("test", _checks()), range(8)))
    assert all(report.passed for report in reports)


def test_pq_16_report_is_json_safe() -> None:
    report = QualificationGate().run("test", _checks())
    encoded = json.dumps(report.to_dict())
    assert "report_hash" in encoded


def test_pq_17_unavailable_truth_preflight_fails_closed() -> None:
    result = TruthPreflightCheck(lambda copilot: False).check("s2p")
    assert not result.passed


def test_pq_18_report_exports_to_json(tmp_path: Path) -> None:
    report = QualificationGate().run("test", _checks())
    output = tmp_path / "qualification.json"
    report.write_json(str(output))
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["report_hash"] == report.report_hash
