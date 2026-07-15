from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.scoring_router import create_scoring_router
from copilot_sdk.scoring.measurement_state import MeasurementState, compute_measurement_state
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.presets.trading import TradingPreset
from integrity.load_benchmark import load_benchmark


def _trading_scorer() -> CompoundingScorer:
    return CompoundingScorer.from_preset("trading", db_path=":memory:")


def _feed_decisions(scorer: CompoundingScorer, count: int) -> None:
    train, _eval_rows = load_benchmark()
    for row in train[:count]:
        result = scorer.score(row["factors"], row["category"])
        scorer.learn(result.decision_id, result.action)


def _feed_all_arms(scorer: CompoundingScorer, per_arm: int) -> None:
    preset = TradingPreset()
    factors = {name: 0.8 for name in preset.shape.factor_names}
    store = scorer._graph_store
    index = 0
    for category in preset.shape.category_names:
        category_index = preset.shape.category_names.index(category)
        for action in preset.shape.action_names:
            action_index = preset.shape.action_names.index(action)
            for _ in range(per_arm):
                decision_id = f"measurement-{index}"
                store.write_decision(
                    "trading",
                    category,
                    action,
                    0.9,
                    factors,
                    metadata={
                        "decision_id": decision_id,
                        "category_index": category_index,
                        "recommended_index": action_index,
                    },
                )
                store.write_outcome(
                    decision_id,
                    action,
                    True,
                    metadata={"actual_index": action_index},
                )
                index += 1


def test_instrument_validated_with_zero_decisions():
    status = compute_measurement_state(_trading_scorer())

    assert status.state is MeasurementState.INSTRUMENT_VALIDATED
    assert status.decisions_verified == 0
    assert status.decisions_needed == 30
    assert status.accuracy is None
    assert status.iks is None
    assert status.provenance == "instrument"


def test_accumulating_with_few_decisions():
    scorer = _trading_scorer()
    _feed_decisions(scorer, 10)

    status = compute_measurement_state(scorer)

    assert status.state is MeasurementState.ACCUMULATING
    assert status.decisions_verified == 10
    assert status.decisions_needed == 30
    assert status.accuracy is None
    assert status.iks is None
    assert status.provenance == "accumulating"


def test_measured_with_enough_decisions():
    scorer = _trading_scorer()
    scorer._measurement_k_min = 2
    _feed_all_arms(scorer, 2)

    status = compute_measurement_state(scorer)

    assert status.state is MeasurementState.MEASURED
    assert status.decisions_verified == 40
    assert status.decisions_needed == 0
    assert status.accuracy is not None and status.accuracy > 0
    assert status.iks is not None
    assert status.provenance == "real_measured"


def test_total_decisions_do_not_measure_without_per_arm_coverage():
    scorer = _trading_scorer()
    scorer._measurement_k_min = 2
    _feed_decisions(scorer, 30)

    status = compute_measurement_state(scorer)

    assert status.state is MeasurementState.ACCUMULATING
    assert status.decisions_verified == 30
    assert status.arms_measured < status.arms_total
    assert status.accuracy is None
    assert status.iks is None


def test_measurement_endpoint_returns_200():
    app = FastAPI()
    app.include_router(create_scoring_router("trading", db_path=":memory:"), prefix="/api")
    client = TestClient(app)

    response = client.get("/api/trading/measurement-state")

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "instrument_validated"
    assert payload["decisions_verified"] == 0
    assert payload["provenance"] == "instrument"


def test_measurement_provenance_correct():
    scorer = _trading_scorer()
    empty = compute_measurement_state(scorer)
    assert empty.provenance == "instrument"

    scorer._measurement_k_min = 1
    _feed_all_arms(scorer, 1)
    measured = compute_measurement_state(scorer)

    assert measured.provenance == "real_measured"
    assert measured.provenance != "sample"


def test_k_min_configurable():
    scorer = _trading_scorer()
    scorer._measurement_k_min = 1
    _feed_all_arms(scorer, 1)

    status = compute_measurement_state(scorer)

    assert status.state is MeasurementState.MEASURED
    assert status.decisions_verified == 20
    assert status.decisions_needed == 0
