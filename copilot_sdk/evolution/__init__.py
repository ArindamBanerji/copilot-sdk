"""Domain-neutral agent evolution primitives."""

from copilot_sdk.evolution.evolver import AgentEvolver, PlateauConfig
from copilot_sdk.evolution.autonomous_promotion import AutonomousPromotionGate, PromotionDecision
from copilot_sdk.evolution.context_selector import ContextAwareSelector, SelectionContext
from copilot_sdk.evolution.credit_attribution import StepCredit, StepCreditAssigner, StepRecord
from copilot_sdk.evolution.gate import DefaultPromotionGate
from copilot_sdk.evolution.ledger import InMemoryEvolutionLedger
from copilot_sdk.evolution.prompt_evolver import PromptEvolverConfig, PromptVariantEvolver
from copilot_sdk.evolution.protocol import (
    EVOLUTION_EVENT_TYPES,
    EvolutionEvent,
    EvolutionLedger,
    EvolutionRule,
    EvolutionStore,
    PromotionGate,
    ShadowRunner,
    VariantSelector,
)
from copilot_sdk.evolution.shadow import DefaultShadowRunner
from copilot_sdk.evolution.variant_store import (
    CategoryVariantStats,
    InMemoryVariantStore,
    VariantSpec,
    VariantStats,
)

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
    "EvolutionStore",
    "InMemoryEvolutionLedger",
    "InMemoryVariantStore",
    "PromotionGate",
    "PromotionDecision",
    "PlateauConfig",
    "PromptEvolverConfig",
    "PromptVariantEvolver",
    "SelectionContext",
    "ShadowRunner",
    "VariantSelector",
    "StepCredit",
    "StepCreditAssigner",
    "StepRecord",
    "CategoryVariantStats",
    "VariantSpec",
    "VariantStats",
]
