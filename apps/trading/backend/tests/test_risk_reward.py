from __future__ import annotations

from app.factors.risk_reward import RiskRewardActualFactor


def test_no_context_neutral():
    assert RiskRewardActualFactor().compute({}) == 0.5


def test_actual_r_multiple_without_plan():
    assert RiskRewardActualFactor().compute({"actual_risk_reward": 2.0}) == 1.0
    assert RiskRewardActualFactor().compute({"actual_risk_reward": -1.0}) == 0.0


def test_actual_vs_planned_risk_reward():
    factor = RiskRewardActualFactor()

    assert factor.compute({"planned_risk_reward": 2.0, "actual_risk_reward": 2.0}) == 0.75
    assert factor.compute({"planned_risk_reward": 2.0, "actual_risk_reward": 3.0}) == 1.0
    assert factor.compute({"planned_risk_reward": 2.0, "actual_risk_reward": -1.0}) == 0.0


def test_invalid_plan_neutral():
    assert RiskRewardActualFactor().compute(
        {"planned_risk_reward": 0.0, "actual_risk_reward": 2.0}
    ) == 0.5
