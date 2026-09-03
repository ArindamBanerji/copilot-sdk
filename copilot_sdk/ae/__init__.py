"""Portable AgentEvolver framework."""

from copilot_sdk.ae.fitness import FitnessEvaluator
from copilot_sdk.ae.gate import PromotionGate
from copilot_sdk.ae.store import EvolutionStore
from copilot_sdk.ae.types import (
    EvolutionVariant,
    FitnessResult,
    PromotionDecision,
    PromotionResult,
    Variant,
)
from copilot_sdk.ae.variant import VariantGenerator

__all__ = [
    "EvolutionStore",
    "EvolutionVariant",
    "FitnessEvaluator",
    "FitnessResult",
    "PromotionDecision",
    "PromotionGate",
    "PromotionResult",
    "Variant",
    "VariantGenerator",
]
