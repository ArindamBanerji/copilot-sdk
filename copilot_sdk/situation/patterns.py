"""Traversal pattern protocol for situation analysis."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from copilot_sdk.situation.models import SituationContext, TypedIntent


@runtime_checkable
class TraversalPattern(Protocol):
    """Domain-specific context traversal adapter."""

    domain: str
    name: str
    default_max_depth: int

    def supports(self, intent: TypedIntent) -> bool:
        ...

    def traverse(
        self,
        intent: TypedIntent,
        *,
        graph_store: Any = None,
        max_depth: int = 3,
    ) -> SituationContext:
        ...
