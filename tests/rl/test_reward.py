from __future__ import annotations

from copilot_sdk.rl import (
    BinaryRewardFunction,
    GradedFinancialRewardFunction,
    RewardComputer,
    RewardFunction,
)


class FixedRewardFunction:
    def __init__(self, value: float) -> None:
        self.value = value

    def compute(self, recommended_action: str, actual_action: str, outcome: dict) -> float:
        del recommended_action, actual_action, outcome
        return self.value


def test_reward_function_protocol_runtime_checks_for_builtins():
    assert isinstance(BinaryRewardFunction(), RewardFunction)
    assert isinstance(GradedFinancialRewardFunction(), RewardFunction)


def test_binary_confirm_and_override():
    reward = BinaryRewardFunction()

    assert reward.compute("approve", "approve", {}) == 1.0
    assert reward.compute("approve", "review", {}) == -1.0


def test_graded_confirm_recovery():
    reward = GradedFinancialRewardFunction()

    assert reward.compute("approve", "approve", {"recovered": 25, "at_risk": 100}) == 0.25
    assert reward.compute("approve", "approve", {"recovered": 200, "at_risk": 100}) == 1.0


def test_graded_override_cycle_time():
    reward = GradedFinancialRewardFunction()

    assert reward.compute("approve", "review", {"cycle_time_hours": 6}) == -0.25
    assert reward.compute("approve", "review", {"cycle_time_hours": 48}) == -1.0


def test_graded_no_impact():
    reward = GradedFinancialRewardFunction()

    assert reward.compute("approve", "approve", {}) == 0.0


def test_reward_computer_positive_passthrough():
    computer = RewardComputer(FixedRewardFunction(0.4), penalty_ratio=10.0)

    assert computer.compute_reward("a", "a") == 0.4
    assert computer.penalty_ratio == 10.0


def test_reward_computer_negative_scaled_by_penalty():
    computer = RewardComputer(FixedRewardFunction(-0.25), penalty_ratio=4.0)

    assert computer.compute_reward("a", "b") == -1.0


def test_reward_computer_raw_clamp_before_penalty():
    negative = RewardComputer(FixedRewardFunction(-2.0), penalty_ratio=3.0)
    positive = RewardComputer(FixedRewardFunction(2.0), penalty_ratio=3.0)

    assert negative.compute_reward("a", "b") == -3.0
    assert positive.compute_reward("a", "a") == 1.0
