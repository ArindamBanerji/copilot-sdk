"""Cross-system advisory discovery patterns."""

from __future__ import annotations

from itertools import combinations
from typing import Any, Protocol

import numpy as np

from copilot_sdk.discovery.alerts import DiscoveryAlert


class CrossSystemPattern(Protocol):
    pattern_type: str

    def discover(
        self,
        copilots: dict[str, Any],
        category_mappings: dict[str, dict[str, str]] | None = None,
    ) -> list[DiscoveryAlert]:
        ...


class CentroidCorrelationPattern:
    pattern_type = "centroid_correlation"

    def __init__(self, min_similarity: float = 0.95) -> None:
        self.min_similarity = float(min_similarity)

    def discover(
        self,
        copilots: dict[str, Any],
        category_mappings: dict[str, dict[str, str]] | None = None,
    ) -> list[DiscoveryAlert]:
        alerts: list[DiscoveryAlert] = []
        vectors = {
            name: vector
            for name, scorer in copilots.items()
            if (vector := _centroid_mean_vector(scorer)) is not None
        }
        for left, right in combinations(sorted(vectors), 2):
            similarity = _cosine_similarity(vectors[left], vectors[right])
            if similarity is None or similarity < self.min_similarity:
                continue
            confidence = max(0.0, min(similarity, 1.0))
            alerts.append(
                DiscoveryAlert(
                    pattern_type=self.pattern_type,
                    source_copilots=[left, right],
                    title="Centroid behavior alignment detected",
                    description=(
                        f"{left} and {right} have similar active centroid geometry."
                    ),
                    confidence=confidence,
                    evidence={
                        "similarity": round(similarity, 6),
                        "copilots": [left, right],
                    },
                )
            )
        return alerts


class ConservationAlignmentPattern:
    pattern_type = "conservation_alignment"

    def discover(
        self,
        copilots: dict[str, Any],
        category_mappings: dict[str, dict[str, str]] | None = None,
    ) -> list[DiscoveryAlert]:
        by_phase: dict[str, list[str]] = {}
        for name, scorer in copilots.items():
            phase = _safe_phase(scorer)
            by_phase.setdefault(phase, []).append(name)

        alerts: list[DiscoveryAlert] = []
        for phase, names in sorted(by_phase.items()):
            if len(names) < 2:
                continue
            alerts.append(
                DiscoveryAlert(
                    pattern_type=self.pattern_type,
                    source_copilots=sorted(names),
                    title="Conservation phase alignment detected",
                    description=f"{len(names)} copilots are operating in phase {phase}.",
                    confidence=0.75,
                    evidence={"phase": phase, "copilots": sorted(names)},
                )
            )
        return alerts


class TransferOpportunityPattern:
    pattern_type = "transfer_opportunity"

    def __init__(self, accuracy_gap: float = 0.25) -> None:
        self.accuracy_gap = float(accuracy_gap)

    def discover(
        self,
        copilots: dict[str, Any],
        category_mappings: dict[str, dict[str, str]] | None = None,
    ) -> list[DiscoveryAlert]:
        if not category_mappings:
            return []

        alerts: list[DiscoveryAlert] = []
        alphas = {name: _safe_alpha(scorer) for name, scorer in copilots.items()}
        for source, target in combinations(sorted(copilots), 2):
            alerts.extend(self._pair_alerts(source, target, alphas, category_mappings))
            alerts.extend(self._pair_alerts(target, source, alphas, category_mappings))
        return alerts

    def _pair_alerts(
        self,
        source: str,
        target: str,
        alphas: dict[str, float],
        category_mappings: dict[str, dict[str, str]],
    ) -> list[DiscoveryAlert]:
        mapping_key = f"{source}->{target}"
        mapping = category_mappings.get(mapping_key)
        if not mapping:
            return []
        source_alpha = alphas[source]
        target_alpha = alphas[target]
        gap = source_alpha - target_alpha
        if gap < self.accuracy_gap:
            return []
        confidence = max(0.0, min(gap, 1.0))
        return [
            DiscoveryAlert(
                pattern_type=self.pattern_type,
                source_copilots=[source, target],
                title="Transfer opportunity detected",
                description=f"{source} may provide useful category priors for {target}.",
                confidence=confidence,
                evidence={
                    "source": source,
                    "target": target,
                    "source_alpha": source_alpha,
                    "target_alpha": target_alpha,
                    "gap": round(gap, 6),
                    "mapped_categories": dict(mapping),
                },
            )
        ]


class AnomalyCoOccurrencePattern:
    pattern_type = "anomaly_co_occurrence"

    def __init__(self, alpha_threshold: float = 0.5) -> None:
        self.alpha_threshold = float(alpha_threshold)

    def discover(
        self,
        copilots: dict[str, Any],
        category_mappings: dict[str, dict[str, str]] | None = None,
    ) -> list[DiscoveryAlert]:
        affected = {
            name: _safe_alpha(scorer)
            for name, scorer in copilots.items()
            if _safe_alpha(scorer) < self.alpha_threshold
        }
        if len(affected) < 2:
            return []
        confidence = max(0.0, min(1.0 - (sum(affected.values()) / len(affected)), 1.0))
        names = sorted(affected)
        return [
            DiscoveryAlert(
                pattern_type=self.pattern_type,
                source_copilots=names,
                title="Shared low-alpha condition detected",
                description=f"{len(names)} copilots are below the alpha threshold.",
                confidence=confidence,
                evidence={
                    "alpha_threshold": self.alpha_threshold,
                    "affected": {name: affected[name] for name in names},
                },
            )
        ]


def _centroid_mean_vector(scorer: Any) -> np.ndarray | None:
    gae_scorer = getattr(scorer, "gae_scorer", None)
    if gae_scorer is None:
        gae_scorer = getattr(scorer, "_scorer", None)
    if gae_scorer is None:
        return None
    centroids = getattr(gae_scorer, "centroids", None)
    if centroids is None:
        return None
    try:
        tensor = np.asarray(centroids, dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if tensor.ndim != 3 or tensor.size == 0:
        return None
    vector = tensor.mean(axis=(0, 1))
    if not np.any(vector):
        return None
    return vector


def _cosine_similarity(left: np.ndarray, right: np.ndarray) -> float | None:
    size = max(int(left.shape[0]), int(right.shape[0]))
    if size == 0:
        return None
    left_padded = np.pad(left, (0, size - int(left.shape[0])))
    right_padded = np.pad(right, (0, size - int(right.shape[0])))
    left_norm = float(np.linalg.norm(left_padded))
    right_norm = float(np.linalg.norm(right_padded))
    if left_norm <= 0.0 or right_norm <= 0.0:
        return None
    return float(np.dot(left_padded, right_padded) / (left_norm * right_norm))


def _safe_phase(scorer: Any) -> str:
    get_phase = getattr(scorer, "get_phase", None)
    if not callable(get_phase):
        return "unknown"
    try:
        return str(get_phase() or "unknown")
    except Exception:
        return "unknown"


def _safe_alpha(scorer: Any) -> float:
    get_alpha = getattr(scorer, "get_alpha", None)
    if not callable(get_alpha):
        return 0.0
    try:
        value = float(get_alpha())
    except (TypeError, ValueError):
        return 0.0
    if value != value:
        return 0.0
    return max(0.0, min(value, 1.0))
