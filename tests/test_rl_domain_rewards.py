from __future__ import annotations

import pytest
from typing import Any

from copilot_sdk.rl import DataOpsReward, PurchasingReward, TradingReward
from copilot_sdk.rl.reward import DomainRewardFunction


@pytest.mark.parametrize("reward", [TradingReward(), PurchasingReward(), DataOpsReward()])
def test_domain_rewards_implement_protocol_and_declare_range(
    reward: Any,
) -> None:
    assert isinstance(reward, DomainRewardFunction)
    range_method = getattr(reward, "reward_range")
    assert callable(range_method)
    assert range_method() == (0.0, 1.0)


def test_trading_reward_uses_risk_adjusted_pnl_and_clamps() -> None:
    reward = TradingReward()
    assert reward.compute("buy", "buy", {"risk_adjusted_pnl": 50, "max_expected": 100}) == 0.5
    assert reward.compute("buy", "buy", {"pnl": 200, "max_expected": 100}) == 1.0
    assert reward.compute("buy", "buy", {"pnl": -10, "max_expected": 100}) == 0.0


def test_purchasing_reward_uses_cost_impact_or_cost_delta() -> None:
    reward = PurchasingReward()
    assert reward.compute("order", "order", {"cost_impact": 80, "max_cost": 100}) == 0.8
    assert reward.compute(
        "order", "order", {"actual_cost": 120, "optimal_cost": 100, "max_cost": 100}
    ) == 0.8
    assert reward.compute("order", "order", {"cost_impact": -1, "max_cost": 100}) == 0.0


def test_dataops_reward_multiplies_clamped_improvements() -> None:
    reward = DataOpsReward()
    assert reward.compute(
        "investigate", "investigate",
        {"resolution_time_improvement": 0.8, "blast_radius_reduction": 0.5},
    ) == pytest.approx(0.4)
    assert reward.compute(
        "investigate", "investigate",
        {"resolution_time_baseline": 10, "resolution_time": 2,
         "blast_radius_baseline": 20, "blast_radius": 10},
    ) == pytest.approx(0.4)
    assert reward.compute(
        "investigate", "investigate",
        {"resolution_time_improvement": 0.0, "blast_radius_reduction": 1.0},
    ) == 0.0


def test_missing_evidence_does_not_produce_success() -> None:
    assert TradingReward().compute("a", "a", {}) == 0.0
    assert PurchasingReward().compute("a", "a", {}) == 0.0
    assert DataOpsReward().compute("a", "a", {}) == 0.0
