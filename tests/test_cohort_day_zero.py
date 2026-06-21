from __future__ import annotations

import pytest

from copilot_sdk.substantiation.cohort_day_zero import (
    ACCUMULATING,
    INSTRUMENT_VALIDATED,
    MEASURED,
    STATES,
    BaseCohortDayZeroState,
    compute_state,
    evaluate_v7_gate,
)


def test_compute_state_instrument_validated() -> None:
    assert compute_state(0, 0, 50) == INSTRUMENT_VALIDATED


def test_compute_state_accumulating() -> None:
    assert compute_state(5, 3, 50) == ACCUMULATING


def test_compute_state_measured() -> None:
    assert compute_state(50, 50, 50) == MEASURED


def test_compute_state_one_arm_below() -> None:
    assert compute_state(50, 10, 50) == ACCUMULATING


def test_states_enum() -> None:
    assert STATES == (INSTRUMENT_VALIDATED, ACCUMULATING, MEASURED)


def test_v7_gate_abstains() -> None:
    result = evaluate_v7_gate(
        {"provenance": "real", "treatment_n": 5, "control_n": 3},
        threshold_k=50,
    )

    assert result["status"] == "awaiting_real_cohorts"
    assert result["lift"] is None


def test_v7_gate_conditions_met() -> None:
    result = evaluate_v7_gate(
        {"provenance": "real", "treatment_n": 50, "control_n": 50, "lift": 0.12},
        threshold_k=50,
    )

    assert result["status"] == "conditions_met"
    assert result["lift"] == 0.12


def test_v7_gate_rejects_non_real() -> None:
    with pytest.raises(ValueError):
        evaluate_v7_gate(
            {"provenance": "sample", "treatment_n": 50, "control_n": 50},
            threshold_k=50,
        )


def test_base_class_abstract() -> None:
    with pytest.raises(TypeError):
        BaseCohortDayZeroState()


def test_get_status_shape() -> None:
    status = _MockCohortState(treatment_n=50, control_n=50).get_status()

    assert sorted(status.keys()) == ["instrument", "real", "state", "structure"]
    assert status["state"] == MEASURED
    assert status["real"]["lift"] == 0.2


def test_get_status_lift_null_below_k() -> None:
    status = _MockCohortState(treatment_n=10, control_n=50).get_status()

    assert status["state"] == ACCUMULATING
    assert status["real"]["lift"] is None


def test_get_status_instrument_always_present() -> None:
    for treatment_n, control_n in [(0, 0), (1, 0), (50, 50)]:
        status = _MockCohortState(
            treatment_n=treatment_n,
            control_n=control_n,
        ).get_status()
        assert status["instrument"]["provenance"] == "oracle"


class _MockCohortState(BaseCohortDayZeroState):
    DOMAIN = "mock"
    THRESHOLD_K = 50

    def __init__(self, *, treatment_n: int, control_n: int) -> None:
        self._treatment_n = treatment_n
        self._control_n = control_n

    def _count_real_cohorts(self) -> dict:
        return {
            "treatment_n": self._treatment_n,
            "control_n": self._control_n,
        }

    def _count_structure_cohorts(self) -> dict:
        return {
            "present": False,
            "treatment_n": 0,
            "control_n": 0,
            "provenance": "sample",
        }

    def _load_instrument(self) -> dict:
        return {
            "validated": True,
            "provenance": "oracle",
            "source_artifact": "mock",
            "experiments": [],
        }

    def _compute_real_lift(self) -> float:
        return 0.2
