"""Centroid warm-start math for cross-copilot transfer."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np


def warm_start_centroids(
    current_centroids: Any,
    patterns: Sequence[Any],
    category_names: Sequence[str],
    action_names: Sequence[str],
    blend_weight: float = 0.25,
) -> tuple[np.ndarray, float]:
    """Return updated centroid copy and bounded transfer score."""

    updated = np.array(current_centroids, dtype=np.float64, copy=True)
    if updated.ndim != 3:
        raise ValueError("current_centroids must be a 3D tensor")

    category_index = {name: index for index, name in enumerate(category_names)}
    action_index = {name: index for index, name in enumerate(action_names)}
    applied_weights: list[float] = []

    for pattern in applied_patterns(updated, patterns, category_names, action_names):
        category = str(getattr(pattern, "category", ""))
        action = str(getattr(pattern, "action", ""))
        delta = np.asarray(getattr(pattern, "centroid_delta", []), dtype=np.float64)
        confidence = _bounded_float(getattr(pattern, "confidence", 0.0))
        updated[category_index[category], action_index[action], :] += (
            float(blend_weight) * confidence * delta
        )
        applied_weights.append(confidence * _bounded_float(getattr(pattern, "win_rate", 0.0)))

    if not applied_weights:
        return updated, 0.0
    return updated, _bounded_float(sum(applied_weights) / len(applied_weights))


def applied_patterns(
    current_centroids: Any,
    patterns: Sequence[Any],
    category_names: Sequence[str],
    action_names: Sequence[str],
) -> list[Any]:
    centroids = np.asarray(current_centroids)
    if centroids.ndim != 3:
        return []
    categories = set(category_names)
    actions = set(action_names)
    factor_count = int(centroids.shape[2])
    applied: list[Any] = []
    for pattern in patterns:
        if str(getattr(pattern, "category", "")) not in categories:
            continue
        if str(getattr(pattern, "action", "")) not in actions:
            continue
        delta = np.asarray(getattr(pattern, "centroid_delta", []), dtype=np.float64)
        if delta.shape != (factor_count,):
            continue
        if _bounded_float(getattr(pattern, "confidence", 0.0)) <= 0.0:
            continue
        applied.append(pattern)
    return applied


def count_applicable_patterns(
    current_centroids: Any,
    patterns: Sequence[Any],
    category_names: Sequence[str],
    action_names: Sequence[str],
) -> int:
    return len(applied_patterns(current_centroids, patterns, category_names, action_names))


def _bounded_float(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not np.isfinite(numeric):
        return 0.0
    return max(0.0, min(numeric, 1.0))
