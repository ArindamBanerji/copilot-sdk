"""Public graph persistence protocol for copilot decisions."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class GraphStore(Protocol):
    """Decision/outcome persistence contract shared by graph backends."""

    def write_decision(
        self,
        entity_id: str,
        category: str,
        action: str,
        confidence: float,
        factors: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        ...

    def write_outcome(
        self,
        decision_id: str,
        actual_action: str,
        is_correct: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ...

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        ...

    def get_decisions(
        self,
        category: str | None = None,
        limit: int = 400,
    ) -> list[dict[str, Any]]:
        ...

    def get_verified_decisions(self) -> list[dict[str, Any]]:
        ...

    def count_verified(self) -> int:
        ...

    def count_correct(self) -> int:
        ...

    def get_all_decisions(self) -> list[dict[str, Any]]:
        ...

    def close(self) -> None:
        ...
