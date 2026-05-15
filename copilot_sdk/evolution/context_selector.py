"""Optional context-aware variant selection helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SelectionContext:
    category: str
    recent_accuracy: float
    conservation_phase: str
    decision_count: int
    time_of_day: float = field(default_factory=time.time)


class ContextAwareSelector:
    """Score candidate variants without mutating current evolution behavior."""

    def __init__(self, exploration_bonus: float = 1.0) -> None:
        self.exploration_bonus = float(exploration_bonus)
        self._failures: set[tuple[str, str]] = set()

    def select(self, variants: list[dict[str, Any]], context: SelectionContext) -> dict[str, Any]:
        if not variants:
            raise ValueError("variants must not be empty")
        if len(variants) == 1:
            return variants[0]

        scored = [
            (self._score(variant, context), -index, variant)
            for index, variant in enumerate(variants)
        ]
        return max(scored, key=lambda item: (item[0], item[1]))[2]

    def record_failure(self, category: str, variant_id: str) -> None:
        self._failures.add((str(category), str(variant_id)))

    def _score(self, variant: dict[str, Any], context: SelectionContext) -> float:
        score = _base_score(variant)
        phase = str(context.conservation_phase).strip().lower()

        if phase in {"a", "early", "explore"} or int(context.decision_count) < 10:
            score += self.exploration_bonus / (1.0 + _evidence_count(variant))
        elif phase in {"b", "mature", "learning"}:
            score += _category_bonus(variant, context.category)
        else:
            score += min(_evidence_count(variant), 1000.0) / 10000.0

        variant_id = str(variant.get("variant_id") or variant.get("id") or "")
        if (str(context.category), variant_id) in self._failures:
            score -= max(self.exploration_bonus, 0.5)
        return score


def _base_score(variant: dict[str, Any]) -> float:
    if "ucb_score" in variant:
        return float(variant["ucb_score"])
    if "win_rate" in variant:
        return float(variant["win_rate"])
    return 0.5


def _evidence_count(variant: dict[str, Any]) -> float:
    for key in ("decision_count", "n", "trials", "shadow_batches", "sample_size"):
        if key in variant:
            return max(float(variant.get(key) or 0.0), 0.0)
    return 0.0


def _category_bonus(variant: dict[str, Any], category: str) -> float:
    category = str(category)
    evidence = variant.get("category_evidence") or {}
    if isinstance(evidence, dict) and category in evidence:
        value = evidence[category]
        if isinstance(value, dict):
            return 0.25 * float(value.get("win_rate", value.get("score", 1.0)))
        return 0.25 * float(value)

    if variant.get("category") == category:
        return 0.15
    categories = variant.get("categories") or ()
    if category in categories:
        return 0.15
    return 0.0
