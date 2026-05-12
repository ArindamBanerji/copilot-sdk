from __future__ import annotations

from copilot_sdk.rl import PnLRewardFunction, WasteReductionRewardFunction


def test_pnl_positive_negative_and_clamp():
    reward = PnLRewardFunction()

    assert reward.compute("buy", "buy", {"pnl_bps": 25}) == 0.25
    assert reward.compute("buy", "buy", {"pnl_bps": -40}) == -0.4
    assert reward.compute("buy", "buy", {"pnl_bps": 250}) == 1.0
    assert reward.compute("buy", "buy", {"pnl_bps": -250}) == -1.0


def test_waste_reduction_positive():
    reward = WasteReductionRewardFunction()

    assert reward.compute("order_less", "order_less", {"waste_pct_change": -5}) == 0.5
    assert reward.compute("order_less", "order_less", {"waste_pct_change": -20}) == 1.0


def test_waste_increase_negative():
    reward = WasteReductionRewardFunction()

    assert reward.compute("order_less", "order_more", {"waste_pct_change": 4}) == -0.4
    assert reward.compute("order_less", "order_more", {"waste_pct_change": 20}) == -1.0
