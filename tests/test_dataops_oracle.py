from __future__ import annotations

from copilot_sdk.scoring.presets.dataops import DataOpsPreset
from copilot_sdk.substantiation import DataOpsOracle, DataOpsPipelineTest
from copilot_sdk.substantiation.populate_readiness import populate_default_readiness


def _sample(oracle: DataOpsOracle, *, shown: bool, n: int = 1000) -> list[dict]:
    return [oracle.synthetic_outcome(shown=shown) for _ in range(n)]


def _accept_rate(outcomes: list[dict]) -> float:
    return sum(row["action"] == "auto_approve" for row in outcomes) / len(outcomes)


def test_dataops_deterministic():
    first = DataOpsOracle(seed=7)
    second = DataOpsOracle(seed=7)
    assert [first.synthetic_outcome(shown=True) for _ in range(20)] == [
        second.synthetic_outcome(shown=True) for _ in range(20)
    ]


def test_dataops_treatment_higher():
    treatment = _sample(DataOpsOracle(seed=11), shown=True)
    control = _sample(DataOpsOracle(seed=11), shown=False)
    assert _accept_rate(treatment) > _accept_rate(control)


def test_dataops_correct_modeled():
    outcomes = _sample(DataOpsOracle(seed=13), shown=True, n=200)
    assert any(row["correct"] for row in outcomes)
    assert any(not row["correct"] for row in outcomes)


def test_dataops_domain_actions():
    preset_actions = set(DataOpsPreset().shape.action_names)
    outcomes = _sample(DataOpsOracle(seed=17), shown=True, n=200) + _sample(
        DataOpsOracle(seed=17),
        shown=False,
        n=200,
    )
    assert {row["action"] for row in outcomes} <= preset_actions


def test_dataops_exp1_known_lift():
    result = DataOpsPipelineTest().exp1_known_lift()
    assert result.passed
    assert abs(result.measured_lift - result.expected_lift) <= 0.04


def test_dataops_exp2_zero_lift():
    result = DataOpsPipelineTest().exp2_zero_lift()
    assert result.passed
    assert abs(result.measured_lift) <= 0.03


def test_dataops_exp3_floor_power():
    result = DataOpsPipelineTest().exp3_floor_power()
    assert result.passed
    assert result.detail["n_per_arm_floor"] > 0


def test_dataops_exp4_gate_rejects():
    result = DataOpsPipelineTest().exp4_gate_rejects()
    assert result.passed
    assert result.detail["gate_correctly_rejected"] is True


def test_readiness_dataops_instrumented():
    entry = next(
        row
        for row in populate_default_readiness()
        if row.feature == "P34-intelligence-map"
    )
    assert entry.instrumented is True
    assert entry.gate() == (False, ["proven"])
