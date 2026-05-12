"""Optional reinforcement-learning primitives for SDK copilots."""

from copilot_sdk.rl.credit import CreditAssigner
from copilot_sdk.rl.exploration import ConservationBoundedThompson
from copilot_sdk.rl.reward import RewardComputer, RewardFunction
from copilot_sdk.rl.reward_functions import (
    BinaryRewardFunction,
    GradedFinancialRewardFunction,
    PnLRewardFunction,
    WasteReductionRewardFunction,
)

__all__ = [
    "RewardFunction",
    "RewardComputer",
    "BinaryRewardFunction",
    "GradedFinancialRewardFunction",
    "PnLRewardFunction",
    "WasteReductionRewardFunction",
    "CreditAssigner",
    "ConservationBoundedThompson",
]
