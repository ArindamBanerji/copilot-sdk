"""Measured Transfer (PILOT-02) contract tests."""

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
    MeasuredTransfer,
    MeasuredTransferStore,
    PromotionRecordsCheck,
    QualificationCheck,
    QualificationGate,
    VerifiedCountCheck,
    create_measured_transfer_router,
)
from copilot_sdk.promotion import PromotionEngine, S2PPromotionPolicy


class _FrozenTwin:
    def is_frozen(self) -> bool:
        return True


def _transfer(
    store: MeasuredTransferStore | None = None,
    *,
    threshold: float = 0.0,
    minimum: int = 1,
    claims: list[str] | None = None,
    promotion: PromotionEngine | None = None,
) -> MeasuredTransfer:
    return MeasuredTransfer(
        _FrozenTwin(),
        store=store,
        average_value=100.0,
        authority_threshold=threshold,
        minimum_decisions=minimum,
        claim_ids=claims,
        promotion_engine=promotion,
    )


def _session(transfer: MeasuredTransfer):
    return transfer.start_pilot("trading")


def _record(transfer: MeasuredTransfer, session_id: str, number: int, live: bool, frozen: bool, category: str = "trend"):
    return transfer.record_decision(
        session_id,
        f"decision-{number}",
        {"correct": live},
        {"correct": frozen},
        category=category,
    )


def test_mt_01_start_pilot_requires_frozen_baseline_and_creates_session() -> None:
    session = _session(_transfer())
    assert session.duration_days == 90
    assert session.frozen_baseline_ref == "frozen-twin"


def test_mt_02_record_decision_stores_pair() -> None:
    transfer = _transfer()
    session = _session(transfer)
    stored = _record(transfer, session.session_id, 1, True, False)
    assert stored["live_correct"] is True
    assert len(transfer.store.observations(session.session_id)) == 1


def test_mt_03_report_computes_category_delta() -> None:
    transfer = _transfer()
    session = _session(transfer)
    _record(transfer, session.session_id, 1, True, False)
    report = transfer.generate_report(session.session_id)
    assert report.per_category[0]["live_accuracy"] == 1.0
    assert report.per_category[0]["frozen_accuracy"] == 0.0
    assert report.per_category[0]["delta"] == 1.0


def test_mt_04_financial_impact_uses_decisions_delta_and_value() -> None:
    transfer = _transfer()
    session = _session(transfer)
    _record(transfer, session.session_id, 1, True, False)
    _record(transfer, session.session_id, 2, True, False)
    assert transfer.generate_report(session.session_id).overall["total_financial_impact"] == 200.0


def test_mt_05_positive_measured_delta_recommends_authority() -> None:
    promotion = PromotionEngine(S2PPromotionPolicy())
    promotion.create("trading", "trend")
    transfer = _transfer(promotion=promotion)
    session = _session(transfer)
    _record(transfer, session.session_id, 1, True, False)
    recommendations = transfer.generate_report(session.session_id).authority_recommendations
    assert recommendations[0]["recommended_stage"] == "promoted"
    assert recommendations[0]["evidence"]["evidence_tier"] == "T_O"


def test_mt_06_delta_below_threshold_has_no_recommendation() -> None:
    transfer = _transfer(threshold=0.5)
    session = _session(transfer)
    _record(transfer, session.session_id, 1, True, True)
    assert transfer.generate_report(session.session_id).authority_recommendations == []


def test_mt_07_measured_claims_get_tier_upgrade_records() -> None:
    transfer = _transfer(claims=["CLAIM-1"])
    session = _session(transfer)
    _record(transfer, session.session_id, 1, True, True)
    upgrade = transfer.generate_report(session.session_id).evidence_upgrades[0]
    assert upgrade == {"claim_id": "CLAIM-1", "old_tier": "T_S", "new_tier": "T_O", "evidence_ref": session.session_id}


def test_mt_08_report_hash_is_deterministic() -> None:
    transfer = _transfer()
    session = _session(transfer)
    _record(transfer, session.session_id, 1, True, False)
    assert transfer.generate_report(session.session_id).report_hash == transfer.generate_report(session.session_id).report_hash


def test_mt_09_empty_pilot_is_valid_and_synthetic() -> None:
    transfer = _transfer()
    report = transfer.generate_report(_session(transfer).session_id)
    assert report.overall["total_decisions"] == 0
    assert report.to_dict()["evidence_tier"] == "T_S"


def test_mt_10_partial_data_covers_only_recorded_categories() -> None:
    transfer = _transfer()
    session = _session(transfer)
    _record(transfer, session.session_id, 1, True, False, "category-a")
    report = transfer.generate_report(session.session_id)
    assert [row["category"] for row in report.per_category] == ["category-a"]


def test_mt_11_router_start_works() -> None:
    transfer = _transfer()
    app = FastAPI()
    app.include_router(create_measured_transfer_router(transfer))
    response = TestClient(app).post("/api/pilot/start", json={"copilot": "trading"})
    assert response.status_code == 200
    assert response.json()["duration_days"] == 90


def test_mt_12_router_record_works() -> None:
    transfer = _transfer()
    app = FastAPI()
    app.include_router(create_measured_transfer_router(transfer))
    client = TestClient(app)
    session = client.post("/api/pilot/start", json={"copilot": "trading"}).json()
    response = client.post("/api/pilot/record", json={"session_id": session["session_id"], "decision_id": "d1", "category": "trend", "live_result": {"correct": True}, "frozen_result": {"correct": False}})
    assert response.status_code == 200


def test_mt_13_router_report_works() -> None:
    transfer = _transfer()
    app = FastAPI()
    app.include_router(create_measured_transfer_router(transfer))
    client = TestClient(app)
    session = client.post("/api/pilot/start", json={"copilot": "trading"}).json()
    client.post("/api/pilot/record", json={"session_id": session["session_id"], "decision_id": "d1", "live_result": {"correct": True}, "frozen_result": {"correct": False}})
    assert client.get("/api/pilot/report", params={"copilot": "trading"}).json()["overall"]["total_decisions"] == 1


def test_mt_14_cli_help_is_available() -> None:
    from scripts.pilot_report import main

    assert callable(main)


def test_mt_15_session_persists_across_store_restart(tmp_path: Path) -> None:
    db = tmp_path / "pilot.sqlite3"
    first_store = MeasuredTransferStore(str(db))
    session = _session(_transfer(first_store))
    _record(_transfer(first_store), session.session_id, 1, True, False)
    first_store.close()
    second_store = MeasuredTransferStore(str(db))
    assert second_store.get_session(session.session_id) is not None
    assert len(second_store.observations(session.session_id)) == 1
    second_store.close()


def test_mt_16_concurrent_recording_is_safe() -> None:
    transfer = _transfer()
    session = _session(transfer)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda i: _record(transfer, session.session_id, i, True, False), range(20)))
    assert len(transfer.store.observations(session.session_id)) == 20


def test_mt_17_report_is_json_safe() -> None:
    transfer = _transfer()
    session = _session(transfer)
    _record(transfer, session.session_id, 1, True, False)
    json.dumps(transfer.generate_report(session.session_id).to_dict(), allow_nan=False)


def test_mt_18_qualification_can_precede_pilot() -> None:
    gate = EvidenceGate()
    gate.register(ClaimRecord("C1", "Measured claim", EvidenceTier.T_O, "site outcomes", "trading"))
    promotion = PromotionEngine(S2PPromotionPolicy())
    promotion.create("trading", "trend")
    checks: list[QualificationCheck] = [FrozenTwinCheck(_FrozenTwin()), EvidenceGateCheck(gate), PromotionRecordsCheck(promotion), ConservationHealthCheck({"phase": "GREEN"}), VerifiedCountCheck(1),]
    assert QualificationGate().run("trading", checks).passed
    transfer = _transfer(promotion=promotion)
    session = _session(transfer)
    _record(transfer, session.session_id, 1, True, False)
    assert transfer.generate_report(session.session_id).authority_recommendations


def test_mt_19_negative_delta_has_no_authority_recommendation() -> None:
    transfer = _transfer()
    session = _session(transfer)
    _record(transfer, session.session_id, 1, False, True)
    report = transfer.generate_report(session.session_id)
    assert report.per_category[0]["delta"] < 0
    assert report.authority_recommendations == []


def test_mt_20_insufficient_category_is_marked() -> None:
    transfer = _transfer(minimum=2)
    session = _session(transfer)
    _record(transfer, session.session_id, 1, True, False, "partial")
    row = transfer.generate_report(session.session_id).per_category[0]
    assert row["sufficient_data"] is False
    assert row["evidence_tier"] == "T_S"
