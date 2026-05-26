"""Public graph persistence protocol for copilot decisions."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class GraphStore(Protocol):
    """Domain-scoped decision/outcome persistence contract."""

    def write_decision(
        self,
        domain: str,
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
        domain: str,
        category: str | None = None,
        limit: int = 400,
    ) -> list[dict[str, Any]]:
        ...

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        ...

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        ...

    def count_verified(self, domain: str) -> int:
        ...

    def count_correct(self, domain: str) -> int:
        ...

    def count_decisions(self, domain: str) -> int:
        ...

    def save_centroids(
        self,
        domain: str,
        category: str,
        centroids: Any,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        ...

    def load_latest_centroids(self, domain: str) -> Any | None:
        ...

    def get_centroid_checkpoints(
        self,
        domain: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        ...

    def archive_old_decisions(self, domain: str, keep_recent: int = 800) -> int:
        ...

    def count_archived(self, domain: str) -> int:
        ...

    def close(self) -> None:
        ...
