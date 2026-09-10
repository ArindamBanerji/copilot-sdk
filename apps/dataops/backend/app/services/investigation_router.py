"""Score-keyed DataOps investigation router."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import numpy as np

from copilot_sdk.scoring.presets.dataops import DataOpsPreset

from .investigation_patterns import (
    DATAOPS_PATTERN_CATEGORIES,
    InvestigationPattern,
    build_default_investigation_patterns,
)

SCORER_TO_PATTERN_CATEGORY = {
    "schema_change": "schema_impact",
    "volume_anomaly": "source_failure",
    "quality_anomaly": "quality_drift",
    "freshness_violation": "known_pattern",
    "pipeline_failure": "source_failure",
    "transform_drift": "cross_system",
}


@dataclass
class RouteDecision:
    pattern: InvestigationPattern | None
    cat_distances: dict[str, float]
    propensity: float
    candidate_reads: list[str]
    policy_version: str = "dataops_vld_router_v1"


@dataclass
class BestScore:
    category: str
    action: str
    distance: float
    confidence: float
    scorer_category: str


class InvestigationRouter:
    def __init__(self, patterns: list[InvestigationPattern] | None = None) -> None:
        self.patterns = patterns or build_default_investigation_patterns()
        self.by_category = {pattern.category_name: pattern for pattern in self.patterns}

    def route(
        self,
        v: np.ndarray,
        scorer: Any,
        investigated: set[str] | None = None,
        *,
        alert_context: dict[str, Any] | None = None,
    ) -> InvestigationPattern | None:
        return self.route_decision(v, scorer, investigated or set(), alert_context=alert_context).pattern

    def route_decision(
        self,
        v: np.ndarray,
        scorer: Any,
        investigated: set[str],
        *,
        alert_context: dict[str, Any] | None = None,
    ) -> RouteDecision:
        distances = self.category_distances(v, scorer)
        categories = sorted(distances, key=lambda category: distances[category])
        for category in categories:
            if category not in investigated and category in self.by_category:
                pattern = self.by_category[category]
                return RouteDecision(
                    pattern=pattern,
                    cat_distances=distances,
                    propensity=_softmax_propensity(distances, category),
                    candidate_reads=[pattern.candidate_read],
                )
        return RouteDecision(
            pattern=None,
            cat_distances=distances,
            propensity=0.0,
            candidate_reads=[],
        )

    def category_distances(self, v: np.ndarray, scorer: Any) -> dict[str, float]:
        centroids = _centroids(scorer)
        scorer_categories = _scorer_categories(scorer)
        vector = np.asarray(v, dtype=np.float64).reshape(-1)
        distances: dict[str, float] = {category: float("inf") for category in DATAOPS_PATTERN_CATEGORIES}
        for scorer_index, scorer_category in enumerate(scorer_categories):
            pattern_category = SCORER_TO_PATTERN_CATEGORY.get(scorer_category)
            if pattern_category not in distances:
                continue
            category_centroids = centroids[scorer_index]
            best_distance = float(np.min(np.linalg.norm(category_centroids - vector, axis=1)))
            distances[pattern_category] = min(distances[pattern_category], best_distance)
        signal_distances = _factor_signal_distances(vector)
        for category, signal_distance in signal_distances.items():
            distances[category] = min(distances.get(category, float("inf")), signal_distance)
        return {
            category: (distance if np.isfinite(distance) else 1.0e9)
            for category, distance in distances.items()
        }

    def score_best_from_centroids(self, v: np.ndarray, scorer: Any) -> BestScore:
        centroids = _centroids(scorer)
        scorer_categories = _scorer_categories(scorer)
        actions = _scorer_actions(scorer)
        vector = np.asarray(v, dtype=np.float64).reshape(-1)
        best: tuple[float, int, int] | None = None
        for category_index in range(centroids.shape[0]):
            distances = np.linalg.norm(centroids[category_index] - vector, axis=1)
            action_index = int(np.argmin(distances))
            distance = float(distances[action_index])
            if best is None or distance < best[0]:
                best = (distance, category_index, action_index)
        if best is None:
            return BestScore("source_failure", "investigate", 1.0, 0.0, "pipeline_failure")
        distance, category_index, action_index = best
        scorer_category = scorer_categories[category_index]
        pattern_category = SCORER_TO_PATTERN_CATEGORY.get(scorer_category, "source_failure")
        logits = -np.linalg.norm(centroids[category_index] - vector, axis=1) / max(float(getattr(scorer, "tau", 0.1)), 1.0e-8)
        logits = logits - float(np.max(logits))
        exp = np.exp(logits)
        probs = exp / float(np.sum(exp))
        return BestScore(
            category=pattern_category,
            action=actions[action_index],
            distance=distance,
            confidence=float(probs[action_index]),
            scorer_category=scorer_category,
        )


def _centroids(scorer: Any) -> np.ndarray:
    raw = getattr(scorer, "centroids", None)
    if raw is None:
        raw = getattr(scorer, "mu", None)
    if raw is None:
        raw = DataOpsPreset().bootstrap_centroids
    return cast(np.ndarray, np.asarray(raw, dtype=np.float64))


def _scorer_categories(scorer: Any) -> list[str]:
    raw = getattr(scorer, "categories", None)
    if raw is None:
        raw = DataOpsPreset().shape.category_names
    return [str(value) for value in raw]


def _scorer_actions(scorer: Any) -> list[str]:
    raw = getattr(scorer, "actions", None)
    if raw is None:
        raw = DataOpsPreset().shape.action_names
    return [str(value) for value in raw]


def _softmax_propensity(distances: dict[str, float], selected: str) -> float:
    ordered = list(distances)
    values = np.asarray([-distances[category] for category in ordered], dtype=np.float64)
    values = values - float(np.max(values))
    exp = np.exp(values)
    probs = exp / float(np.sum(exp))
    return float(probs[ordered.index(selected)])


def _factor_signal_distances(vector: np.ndarray) -> dict[str, float]:
    values = np.clip(np.asarray(vector, dtype=np.float64).reshape(-1), 0.0, 1.0)
    if values.size < 6:
        values = np.pad(values, (0, 6 - values.size))
    impact_scope, source_reliability, recurrence_frequency, downstream_urgency, data_freshness, business_criticality = values[:6]
    return {
        "source_failure": float(min(source_reliability, data_freshness)),
        "schema_impact": float(1.0 - max(impact_scope, downstream_urgency, business_criticality)),
        "quality_drift": float(1.0 - max(impact_scope, 1.0 - source_reliability)),
        "cross_system": float(1.0 - max(downstream_urgency, business_criticality)),
        "known_pattern": float(1.0 - recurrence_frequency),
    }
