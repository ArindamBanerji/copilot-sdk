"""Adaptive investigation read-budget policy.

This module is intentionally separate from the investigation implementation.
It selects a read budget; the existing investigator remains responsible for
executing those reads and enforcing its own safety behavior.
"""

from __future__ import annotations

from typing import Any


MAX_HISTORY = 200


class AdaptiveBudgetPolicy:
    """Allocate investigation reads from confidence and cold-start state."""

    def __init__(
        self,
        min_reads: int = 1,
        max_reads: int = 4,
        default_reads: int = 2,
        safety_lambda: float = 0.0,
    ) -> None:
        if not 1 <= min_reads <= default_reads <= max_reads:
            raise ValueError("read budgets must satisfy 1 <= min <= default <= max")
        if safety_lambda < 0.0:
            raise ValueError("safety_lambda must be non-negative")
        self.min_reads = min_reads
        self.max_reads = max_reads
        self.default_reads = default_reads
        self.safety_lambda = safety_lambda
        self._history: list[dict[str, Any]] = []
        self._total_allocations = 0
        self._total_easy = 0
        self._total_hard = 0
        self._total_easy_reads = 0
        self._total_hard_reads = 0
        self._total_reads_saved = 0

    def allocate(self, confidence: float, category: str, verified_count: int) -> int:
        """Return fewer reads for easy decisions and more for hard ones."""
        if verified_count < 30:
            return self.default_reads

        if confidence >= 0.85:
            reads = self.min_reads
        elif confidence >= 0.65:
            reads = self.default_reads
        else:
            reads = self.max_reads

        self._history.append(
            {
                "confidence": confidence,
                "category": category,
                "reads_allocated": reads,
            }
        )
        if len(self._history) > MAX_HISTORY:
            del self._history[:-MAX_HISTORY]
        self._total_allocations += 1
        self._total_reads_saved += self.default_reads - reads
        if reads <= self.min_reads:
            self._total_easy += 1
            self._total_easy_reads += reads
        if reads >= self.max_reads:
            self._total_hard += 1
            self._total_hard_reads += reads
        return reads

    def get_stats(self) -> dict[str, Any]:
        """Return aggregate policy telemetry for the budget strip."""
        if self._total_allocations == 0:
            return {
                "controller": "adaptive",
                "decisions": 0,
                "safety_lambda": self.safety_lambda,
                "mean_reads_easy": None,
                "mean_reads_hard": None,
                "total_reads_saved": 0,
                "easy_count": 0,
                "hard_count": 0,
            }

        return {
            "controller": "adaptive",
            "decisions": self._total_allocations,
            "mean_reads_easy": self._total_easy_reads / max(self._total_easy, 1),
            "mean_reads_hard": self._total_hard_reads / max(self._total_hard, 1),
            "total_reads_saved": self._total_reads_saved,
            "easy_count": self._total_easy,
            "hard_count": self._total_hard,
            "safety_lambda": self.safety_lambda,
        }


__all__ = ["AdaptiveBudgetPolicy"]
