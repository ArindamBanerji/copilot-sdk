"""Comparator policies for DataOps investigation routing."""

from __future__ import annotations

import random
from typing import Any, Protocol, cast

import numpy as np

from .investigation_patterns import InvestigationPattern


EXPECTED_PATTERN_BY_ALERT_CATEGORY = {
    "schema_change": "schema_impact",
    "quality_anomaly": "quality_drift",
    "freshness_violation": "known_pattern",
    "pipeline_failure": "source_failure",
    "volume_anomaly": "source_failure",
    "transform_drift": "cross_system",
}


class ComparatorPolicy(Protocol):
    name: str

    def select(
        self,
        alert_context: dict[str, Any],
        patterns: list[InvestigationPattern],
        router: Any,
        scorer: Any,
        investigated: set[str] | None = None,
    ) -> InvestigationPattern | None:
        ...


class SinglePassPolicy:
    name = "single_pass"

    def select(
        self,
        alert_context: dict[str, Any],
        patterns: list[InvestigationPattern],
        router: Any,
        scorer: Any,
        investigated: set[str] | None = None,
    ) -> InvestigationPattern | None:
        return None


class ContentRulePolicy:
    name = "content_rule"

    def select(
        self,
        alert_context: dict[str, Any],
        patterns: list[InvestigationPattern],
        router: Any,
        scorer: Any,
        investigated: set[str] | None = None,
    ) -> InvestigationPattern | None:
        expected = expected_pattern_category(alert_context)
        return _by_category(patterns).get(expected)


class MajorityBranchPolicy:
    name = "majority_branch"

    def __init__(self, category: str = "source_failure") -> None:
        self.category = category

    def select(
        self,
        alert_context: dict[str, Any],
        patterns: list[InvestigationPattern],
        router: Any,
        scorer: Any,
        investigated: set[str] | None = None,
    ) -> InvestigationPattern | None:
        if investigated and self.category in investigated:
            return None
        return _by_category(patterns).get(self.category)


class RandomBranchPolicy:
    name = "random_branch"

    def __init__(self, seed: int = 7) -> None:
        self.rng = random.Random(seed)

    def select(
        self,
        alert_context: dict[str, Any],
        patterns: list[InvestigationPattern],
        router: Any,
        scorer: Any,
        investigated: set[str] | None = None,
    ) -> InvestigationPattern | None:
        blocked = investigated or set()
        choices = [pattern for pattern in patterns if pattern.category_name not in blocked]
        if not choices:
            return None
        return self.rng.choice(choices)


class BreadthPolicy:
    name = "breadth"

    def select(
        self,
        alert_context: dict[str, Any],
        patterns: list[InvestigationPattern],
        router: Any,
        scorer: Any,
        investigated: set[str] | None = None,
    ) -> InvestigationPattern | None:
        blocked = investigated or set()
        for pattern in patterns:
            if pattern.category_name not in blocked:
                return pattern
        return None


def expected_pattern_category(alert_context: dict[str, Any]) -> str:
    category = str(alert_context.get("category") or alert_context.get("alert_type") or "")
    return EXPECTED_PATTERN_BY_ALERT_CATEGORY.get(category, "source_failure")


def pattern_matches_alert(pattern: InvestigationPattern | None, alert_context: dict[str, Any]) -> bool:
    return pattern is not None and pattern.category_name == expected_pattern_category(alert_context)


def factor_vector(alert_context: dict[str, Any], factor_names: tuple[str, ...]) -> np.ndarray:
    raw_factors = alert_context.get("factors")
    factors = raw_factors if isinstance(raw_factors, dict) else {}
    return cast(np.ndarray, np.asarray([float(factors.get(name, 0.0) or 0.0) for name in factor_names], dtype=np.float64))


def _by_category(patterns: list[InvestigationPattern]) -> dict[str, InvestigationPattern]:
    return {pattern.category_name: pattern for pattern in patterns}
