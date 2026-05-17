"""Domain-neutral agent evolution primitives."""

from copilot_sdk.evolution.evolver import AgentEvolver, PlateauConfig
from copilot_sdk.evolution.autonomous_promotion import AutonomousPromotionGate, PromotionDecision
from copilot_sdk.evolution.context_selector import ContextAwareSelector, SelectionContext
from copilot_sdk.evolution.credit_attribution import StepCredit, StepCreditAssigner, StepRecord
from copilot_sdk.evolution.gate import DefaultPromotionGate
from copilot_sdk.evolution.ledger import InMemoryEvolutionLedger
from copilot_sdk.evolution.protocol import (
    EVOLUTION_EVENT_TYPES,
    EvolutionEvent,
    EvolutionLedger,
    EvolutionRule,
    PromotionGate,
    ShadowRunner,
)
from copilot_sdk.evolution.shadow import DefaultShadowRunner

__all__ = [
    "AgentEvolver",
    "AutonomousPromotionGate",
    "ContextAwareSelector",
    "DefaultPromotionGate",
    "DefaultShadowRunner",
    "EVOLUTION_EVENT_TYPES",
    "EvolutionEvent",
    "EvolutionLedger",
    "EvolutionRule",
    "InMemoryEvolutionLedger",
    "PromotionGate",
    "PromotionDecision",
    "PlateauConfig",
    "SelectionContext",
    "ShadowRunner",
    "StepCredit",
    "StepCreditAssigner",
    "StepRecord",
]
