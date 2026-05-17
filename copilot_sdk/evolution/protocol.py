"""Domain-neutral contracts for rule evolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable


EVOLUTION_EVENT_TYPES = frozenset(
    {
        "variant_generated",
        "shadow_started",
        "shadow_completed",
        "promoted",
        "rejected",
        "rollback",
        "plateau_detected",
    }
)


@dataclass(frozen=True)
class EvolutionEvent:
    event_type: str
    rule_name: str
    variant_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.event_type not in EVOLUTION_EVENT_TYPES:
            raise ValueError(f"Unsupported evolution event type: {self.event_type}")
        object.__setattr__(self, "metadata", dict(self.metadata or {}))


@runtime_checkable
class EvolutionRule(Protocol):
    @property
    def name(self) -> str:
        ...

    def generate_variant(self, seed: Any | None = None) -> Any:
        ...


@runtime_checkable
class EvolutionLedger(Protocol):
    def append(self, event: EvolutionEvent) -> None:
        ...

    def get_events(
        self,
        rule_name: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        ...

    def get_promoted_rules(self) -> list[str]:
        ...

    def reset(self) -> None:
        ...


@runtime_checkable
class ShadowRunner(Protocol):
    def run_shadow(
        self,
        variant: Any,
        decisions: list[dict[str, Any]],
        baseline: Any | None = None,
    ) -> dict[str, Any]:
        ...


@runtime_checkable
class PromotionGate(Protocol):
    def evaluate(
        self,
        shadow_results: dict[str, Any],
        conservation_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ...
