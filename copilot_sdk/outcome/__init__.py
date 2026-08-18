"""Shared Verified Outcome Protocol."""

from .adapters import outcome_to_reward, reward_to_outcome  # adapter
from .ledger import OutcomeLedger
from .models import VerifiedOutcome
from .processor import OutcomeProcessor, ProcessResult
from .router import create_outcome_router

__all__ = [
    "OutcomeLedger",
    "OutcomeProcessor",
    "ProcessResult",
    "VerifiedOutcome",
    "create_outcome_router",
    "outcome_to_reward",
    "reward_to_outcome",  # adapter
]
