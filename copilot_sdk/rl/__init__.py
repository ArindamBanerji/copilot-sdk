"""Optional reinforcement-learning primitives for SDK copilots."""

from copilot_sdk.rl.credit import CreditAssigner
from copilot_sdk.rl.domains import DataOpsReward, PurchasingReward, TradingReward
from copilot_sdk.rl.exploration import ConservationBoundedThompson, ExplorationPolicy
from copilot_sdk.rl.reward import DomainRewardFunction, RewardComputer, RewardFunction
from copilot_sdk.rl.reward_functions import (
    BinaryRewardFunction,
    GradedFinancialRewardFunction,
    PnLRewardFunction,
    WasteReductionRewardFunction,
)
from copilot_sdk.rl.types import CreditAssignment, ExplorationDecision, RewardResult

__all__ = [
    "RewardFunction",
    "DomainRewardFunction",
    "RewardComputer",
    "BinaryRewardFunction",
    "GradedFinancialRewardFunction",
    "PnLRewardFunction",
    "WasteReductionRewardFunction",
    "CreditAssigner",
    "DataOpsReward",
    "PurchasingReward",
    "TradingReward",
    "ExplorationPolicy",
    "ConservationBoundedThompson",
    "RewardResult",
    "CreditAssignment",
    "ExplorationDecision",
]
