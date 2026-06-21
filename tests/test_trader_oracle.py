from __future__ import annotations

from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.substantiation import TraderOracle, TraderPipelineTest
from copilot_sdk.substantiation.populate_readiness import populate_default_readiness


def _sample(oracle: TraderOracle, *, shown: bool, n: int = 1000) -> list[dict]:
    return [oracle.synthetic_outcome(shown=shown) for _ in range(n)]


def _follow_rate(outcomes: list[dict]) -> float:
    return sum(
        row["action"] in {"strong_execution", "partial_execution"} for row in outcomes
    ) / len(outcomes)


def test_trader_deterministic():
    first = TraderOracle(seed=7)
    second = TraderOracle(seed=7)
    assert [first.synthetic_outcome(shown=True) for _ in range(20)] == [
        second.synthetic_outcome(shown=True) for _ in range(20)
    ]


def test_trader_treatment_higher():
    treatment = _sample(TraderOracle(seed=11), shown=True)
    control = _sample(TraderOracle(seed=11), shown=False)
    assert _follow_rate(treatment) > _follow_rate(control)


def test_trader_correct_modeled():
    outcomes = _sample(TraderOracle(seed=13), shown=True, n=200)
    assert any(row["correct"] for row in outcomes)
    assert any(not row["correct"] for row in outcomes)


def test_trader_domain_actions():
    preset_actions = set(TradingPreset().shape.action_names)
    outcomes = _sample(TraderOracle(seed=17), shown=True, n=200) + _sample(
        TraderOracle(seed=17),
        shown=False,
        n=200,
    )
    assert {row["action"] for row in outcomes} <= preset_actions


def test_trader_exp1_known_lift():
    result = TraderPipelineTest().exp1_known_lift()
    assert result.passed
    assert abs(result.measured_lift - result.expected_lift) <= 0.04


def test_trader_exp2_zero_lift():
    result = TraderPipelineTest().exp2_zero_lift()
    assert result.passed
    assert abs(result.measured_lift) <= 0.03


def test_trader_exp3_floor_power():
    result = TraderPipelineTest().exp3_floor_power()
    assert result.passed
    assert result.detail["n_per_arm_floor"] > 0


def test_trader_exp4_gate_rejects():
    result = TraderPipelineTest().exp4_gate_rejects()
    assert result.passed
    assert result.detail["gate_correctly_rejected"] is True


def test_readiness_trading_instrumented():
    entry = next(
        row for row in populate_default_readiness() if row.feature == "P53-trust-radar"
    )
    assert entry.instrumented is True
    assert entry.gate() == (False, ["proven"])
