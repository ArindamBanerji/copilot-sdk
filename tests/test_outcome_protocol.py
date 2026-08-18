from __future__ import annotations

import threading
from typing import Any

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from gae.profile_scorer import ProfileScorer

from copilot_sdk.outcome import (
    OutcomeLedger,
    OutcomeProcessor,
    VerifiedOutcome,
    create_outcome_router,
    outcome_to_reward,
    reward_to_outcome,
)


def _scorer() -> ProfileScorer:
    return ProfileScorer(
        mu=np.full((1, 2, 4), 0.5, dtype=np.float64),
        actions=["approve", "reject"],
        categories=["operations"],
    )


def _outcome(**overrides: Any) -> VerifiedOutcome:
    values: dict[str, Any] = {
        "outcome_id": "outcome-1",
        "copilot": "test",
        "decision_id": "decision-1",
        "category": "operations",
        "factor_vector": [0.1, 0.2, 0.3, 0.4],
        "predicted_action": "approve",
        "human_disposition": "confirm",
        "override_action": None,
        "override_reason": None,
        "correct": True,
        "measured_impact": {"cycle_time_hours": 2.5},
        "evidence_provenance": "customer_record",
        "timestamp": "2026-08-18T12:00:00Z",
    }
    values.update(overrides)
    return VerifiedOutcome(**values)


def test_vo_01_confirm_is_stored_and_processed(tmp_path):
    ledger = OutcomeLedger(tmp_path / "outcomes.db")
    result = OutcomeProcessor(ledger).process(_outcome())

    assert result.processed is True
    assert result.reason == "processed"
    assert ledger.get(result.receipt_id) == _outcome()


def test_vo_02_override_is_stored_with_reason(tmp_path):
    outcome = _outcome(
        human_disposition="override",
        override_action="reject",
        override_reason="new evidence contradicted the initial signal",
        correct=False,
    )

    result = OutcomeProcessor(OutcomeLedger(tmp_path / "outcomes.db")).process(outcome)

    assert result.processed is True
    assert outcome.human_disposition == "override"
    assert outcome.correct is False
    assert outcome.override_reason is not None


def test_vo_03_duplicate_receipt_is_idempotent(tmp_path):
    processor = OutcomeProcessor(OutcomeLedger(tmp_path / "outcomes.db"))
    outcome = _outcome()

    first = processor.process(outcome)
    second = processor.process(outcome)

    assert first.processed is True
    assert second.processed is False
    assert second.reason == "already_processed"


def test_vo_04_incomplete_receipt_is_rejected():
    data = _outcome().to_dict()
    del data["evidence_provenance"]

    with pytest.raises(ValueError, match="required fields"):
        VerifiedOutcome.from_dict(data)


def test_vo_05_receipt_id_is_deterministic():
    first = _outcome(timestamp="2026-08-18T12:00:00Z")
    second = _outcome(timestamp="2026-08-19T12:00:00Z", outcome_id="different")

    assert first.receipt_id() == second.receipt_id()


def test_vo_06_ledger_round_trip_survives_restart(tmp_path):
    path = tmp_path / "outcomes.db"
    outcome = _outcome()
    first = OutcomeLedger(path)
    first.append(outcome)
    first.close()

    second = OutcomeLedger(path)
    loaded = second.get(outcome.receipt_id())

    assert loaded == outcome


def test_vo_07_count_verified_by_copilot(tmp_path):
    ledger = OutcomeLedger(tmp_path / "outcomes.db")
    ledger.append(_outcome())
    ledger.append(_outcome(copilot="other", decision_id="decision-2", outcome_id="outcome-2"))

    assert ledger.count("test") == 1
    assert ledger.count("other") == 1


def test_vo_08_count_verified_by_category(tmp_path):
    ledger = OutcomeLedger(tmp_path / "outcomes.db")
    ledger.append(_outcome())
    ledger.append(_outcome(category="finance", decision_id="decision-2", outcome_id="outcome-2"))

    assert ledger.count("test", "operations") == 1
    assert ledger.count("test", "finance") == 1


def test_vo_09_batch_processes_independently(tmp_path):
    processor = OutcomeProcessor(OutcomeLedger(tmp_path / "outcomes.db"))
    results = processor.process_batch([
        _outcome(),
        _outcome(decision_id="decision-2", outcome_id="outcome-2"),
    ])

    assert [result.processed for result in results] == [True, True]
    assert processor.count_verified("test") == 2


def test_vo_10_legacy_adapter_produces_valid_receipt():
    outcome = reward_to_outcome(
        {
            "decision_id": "decision-legacy",
            "category": "operations",
            "factor_vector": [0.1, 0.2],
            "recommended_action": "approve",
            "actual_action": "reject",
            "is_correct": False,
            "override_comment": "manual review found an exception",
            "reward": -1.0,
            "reward_raw": -2.0,
            "verified_at_epoch": 1_755_500_000.0,
        },
        "test",
    )

    assert isinstance(outcome, VerifiedOutcome)
    assert outcome.human_disposition == "override"
    assert outcome.measured_impact == {"reward": -1.0, "reward_raw": -2.0}


def test_vo_11_outcome_to_legacy_adapter_has_compatibility_view():
    legacy = outcome_to_reward(_outcome(measured_impact={"reward": 0.8, "reward_raw": 1.2}))

    assert legacy["decision_id"] == "decision-1"
    assert legacy["reward"] == 0.8
    assert legacy["reward_raw"] == 1.2
    assert legacy["is_correct"] is True


def test_vo_12_legacy_round_trip_preserves_core_fields():
    original = {
        "decision_id": "decision-legacy",
        "category": "operations",
        "factor_vector": [0.1, 0.2],
        "recommended_action": "approve",
        "actual_action": "approve",
        "is_correct": True,
        "reward": 1.0,
        "reward_raw": 1.0,
    }
    restored = outcome_to_reward(reward_to_outcome(original, "test"))

    assert restored["decision_id"] == original["decision_id"]
    assert restored["category"] == original["category"]
    assert restored["factor_vector"] == original["factor_vector"]
    assert restored["actual_action"] == original["actual_action"]
    assert restored["is_correct"] is True
    assert restored["reward"] == original["reward"]
    assert restored["reward_raw"] == original["reward_raw"]


def _client(processor: OutcomeProcessor) -> TestClient:
    app = FastAPI()
    app.include_router(create_outcome_router(processor))
    return TestClient(app)


def test_vo_13_router_processes_receipt(tmp_path):
    processor = OutcomeProcessor(OutcomeLedger(tmp_path / "outcomes.db"))

    response = _client(processor).post("/api/outcome/process", json=_outcome().to_dict())

    assert response.status_code == 200
    assert response.json()["processed"] is True


def test_vo_14_router_gets_receipt(tmp_path):
    processor = OutcomeProcessor(OutcomeLedger(tmp_path / "outcomes.db"))
    outcome = _outcome()
    processor.process(outcome)

    response = _client(processor).get(f"/api/outcome/{outcome.receipt_id()}")

    assert response.status_code == 200
    assert response.json()["decision_id"] == outcome.decision_id


def test_vo_15_concurrent_processing_is_exactly_once(tmp_path):
    processor = OutcomeProcessor(OutcomeLedger(tmp_path / "outcomes.db"))
    results: list[bool] = []
    lock = threading.Lock()

    def process() -> None:
        result = processor.process(_outcome())
        with lock:
            results.append(result.processed)

    threads = [threading.Thread(target=process) for _ in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results.count(True) == 1
    assert results.count(False) == 11
    assert processor.count_verified("test") == 1


def test_vo_16_canonical_receipt_has_no_legacy_fields():
    fields = set(_outcome().to_dict())

    assert "reward" not in fields
    assert "reward_raw" not in fields
    assert "policy" not in fields


def test_vo_17_real_profile_scorer_moves_after_processing(tmp_path):
    scorer = _scorer()
    before = scorer.mu.copy()
    outcome = _outcome()
    processor = OutcomeProcessor(OutcomeLedger(tmp_path / "outcomes.db"), scorer=scorer)

    result = processor.process(outcome)

    assert result.processed is True
    assert not np.array_equal(before, scorer.mu)


def test_vo_18_adapter_output_is_accepted_by_processor(tmp_path):
    outcome = reward_to_outcome(
        {
            "decision_id": "decision-adapter",
            "category": "operations",
            "factor_vector": [0.1, 0.2, 0.3, 0.4],
            "recommended_action": "approve",
            "is_correct": True,
        },
        "test",
    )
    processor = OutcomeProcessor(OutcomeLedger(tmp_path / "outcomes.db"), scorer=_scorer())

    result = processor.process(outcome)

    assert result.processed is True
    assert processor.get_receipt(result.receipt_id) is not None


def test_vo_19_router_count_route_is_not_shadowed(tmp_path):
    processor = OutcomeProcessor(OutcomeLedger(tmp_path / "outcomes.db"))
    processor.process(_outcome())

    response = _client(processor).get("/api/outcome/count", params={"copilot": "test"})

    assert response.status_code == 200
    assert response.json()["count"] == 1
