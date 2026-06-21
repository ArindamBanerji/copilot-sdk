"""Deterministic holdout assignment protocols."""

from __future__ import annotations

import hashlib
from typing import Protocol, runtime_checkable


@runtime_checkable
class HoldoutAssigner(Protocol):
    """Deterministic per-entity holdout assignment.

    The assigned treatment flag must be persisted to the decision node so real
    measurement can reconstruct treatment/control cohorts.
    """

    def suppressed(self, entity_id: str) -> bool:
        """Return whether the entity is in holdout."""
        ...


class UnconditionalHoldout:
    """Fixed percentage of all entities suppressed."""

    def __init__(self, holdout_pct: int = 15, seed: int = 42) -> None:
        self._pct = holdout_pct
        self._seed = seed

    def suppressed(self, entity_id: str) -> bool:
        return _bucket(entity_id, self._seed) < self._pct


class ConditionalHoldout:
    """Suppress only entities where the enrichment or treatment exists."""

    def __init__(self, holdout_pct: int = 15, seed: int = 42) -> None:
        self._pct = holdout_pct
        self._seed = seed

    def suppressed(self, entity_id: str, has_enrichment: bool = True) -> bool:
        if not has_enrichment:
            return False
        return _bucket(entity_id, self._seed) < self._pct


def _bucket(entity_id: str, seed: int) -> int:
    digest = hashlib.sha256(f"{entity_id}:{seed}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100
