"""Domain-neutral agent evolution primitives."""

from copilot_sdk.evolution.evolver import AgentEvolver
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
    "DefaultPromotionGate",
    "DefaultShadowRunner",
    "EVOLUTION_EVENT_TYPES",
    "EvolutionEvent",
    "EvolutionLedger",
    "EvolutionRule",
    "InMemoryEvolutionLedger",
    "PromotionGate",
    "ShadowRunner",
]
