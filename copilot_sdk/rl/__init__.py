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
from copilot_sdk.rl.outcome_receipt import OutcomeReceipt, OutcomeReceiptStore, read_outcome_receipt
from copilot_sdk.rl.reward_protocol import RewardFunction as MappingRewardFunction, LegacyRewardAdapter
from copilot_sdk.rl.temporal_credit import TemporalCreditAssigner
from copilot_sdk.rl.conservation_budget import ExplorationBudget

__all__ = [
    "OutcomeReceipt",
    "OutcomeReceiptStore",
    "read_outcome_receipt",
    "MappingRewardFunction",
    "LegacyRewardAdapter",
    "TemporalCreditAssigner",
    "ExplorationBudget",
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
