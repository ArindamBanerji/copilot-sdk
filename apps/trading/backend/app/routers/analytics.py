"""Decision-level Trading analytics endpoints."""

from __future__ import annotations

import math
from itertools import combinations
from statistics import mean
from typing import Any, Callable

from fastapi import APIRouter, Request

from app.analytics.dispersion_follow import compute_dispersion_follow_rate
from app.analytics.regime_vrp import compute_regime_vrp
from app.analytics.vol_sharpe import compute_clustering_adjusted_sharpe
from app.analytics.vrp_attribution import compute_vrp_attribution
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.state.cached_static import cached_static


GraphStoreFactory = Callable[[], Any]

_PRESET = TradingPreset()
_CATEGORIES = tuple(_PRESET.shape.category_names)
_ACTIONS = tuple(_PRESET.shape.action_names)
_FACTORS = tuple(_PRESET.shape.factor_names)


def create_analytics_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-analytics"])

    @router.get("/execution-analysis")
    def execution_analysis(category: str | None = None) -> dict[str, Any]:
        decisions = _verified_decisions(graph_store_factory, domain)
        if category:
            decisions = [decision for decision in decisions if decision.get("category") == category]

        by_category: dict[str, dict[str, Any]] = {}
        for category_name in _CATEGORIES:
            rows = [decision for decision in decisions if decision.get("category") == category_name]
            if rows or category == category_name:
                by_category[category_name] = {
                    "decision_count": len(rows),
                    "quality_distribution": _quality_distribution(rows),
                    "accuracy": _accuracy(rows),
                }

        insights = _execution_insights(decisions)
        return {
            "decision_count": len(decisions),
            "quality_distribution": _quality_distribution(decisions),
            "by_category": by_category,
            "factor_patterns": _factor_patterns(decisions),
            "actionable_insights": insights,
            "source": "graphstore",
        }

    @router.get("/cross-insights")
    def cross_insights() -> dict[str, Any]:
        decisions = _verified_decisions(graph_store_factory, domain)
        grouped = {
            category: [decision for decision in decisions if decision.get("category") == category]
            for category in _CATEGORIES
        }
        category_accuracy = {
            category: {
                "verified_count": len(rows),
                "accuracy": _accuracy(rows),
                "quality_distribution": _quality_distribution(rows),
            }
            for category, rows in grouped.items()
        }
        vectors = _centroid_vectors(graph_store_factory, domain) or _category_vectors(grouped)
        dominant = {
            category: _dominant_factors(vector)
            for category, vector in vectors.items()
        }
        similar = _similar_categories(vectors, dominant)
        return {
            "category_accuracy": category_accuracy,
            "similar_categories": similar,
            "dominant_factors": dominant,
            "transfer_opportunities": _transfer_opportunities(category_accuracy, similar),
            "source": "graphstore",
        }

    @router.get("/analytics/vol-sharpe")
    @cached_static("vol-sharpe")
    def vol_sharpe(request: Request) -> dict[str, Any]:
        decisions = _verified_decisions(graph_store_factory, domain)
        return compute_clustering_adjusted_sharpe(decisions)

    @router.get("/analytics/vrp-attribution")
    @cached_static("vrp-attribution")
    def vrp_attribution(request: Request) -> dict[str, Any]:
        decisions = _verified_decisions(graph_store_factory, domain)
        return compute_vrp_attribution(decisions)

    @router.get("/analytics/regime-vrp")
    @cached_static("regime-vrp")
    def regime_vrp(request: Request) -> dict[str, Any]:
        decisions = _verified_decisions(graph_store_factory, domain)
        return compute_regime_vrp(decisions)

    @router.get("/analytics/dispersion-follow")
    @cached_static("dispersion-follow")
    def dispersion_follow(request: Request) -> dict[str, Any]:
        decisions = _verified_decisions(graph_store_factory, domain)
        return compute_dispersion_follow_rate(decisions)

    return router


def _verified_decisions(
    graph_store_factory: GraphStoreFactory | None,
    domain: str,
) -> list[dict[str, Any]]:
    if graph_store_factory is None:
        return []
    store = graph_store_factory()
    get_verified = getattr(store, "get_verified_decisions", None)
    if not callable(get_verified):
        return []
    return [dict(decision) for decision in get_verified(domain)]


def _quality_distribution(decisions: list[dict[str, Any]]) -> dict[str, int]:
    counts = {action: 0 for action in _ACTIONS}
    for decision in decisions:
        action = _decision_action(decision)
        if action in counts:
            counts[action] += 1
    return counts


def _decision_action(decision: dict[str, Any]) -> str:
    return str(decision.get("actual_action") or decision.get("recommended_action") or "")


def _accuracy(decisions: list[dict[str, Any]]) -> float:
    if not decisions:
        return 0.0
    correct = sum(1 for decision in decisions if bool(decision.get("is_correct")))
    return _finite_float(correct / len(decisions))


def _factor_patterns(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = []
    strong = [decision for decision in decisions if _decision_action(decision) == "strong_execution"]
    poor = [decision for decision in decisions if _decision_action(decision) == "poor_execution"]
    for factor in _FACTORS:
        strong_mean = _factor_mean(strong, factor)
        poor_mean = _factor_mean(poor, factor)
        delta = None
        if strong_mean is not None and poor_mean is not None:
            delta = _finite_float(strong_mean - poor_mean)
        patterns.append(
            {
                "factor": factor,
                "strong_mean": strong_mean,
                "poor_mean": poor_mean,
                "delta": delta,
            }
        )
    return patterns


def _factor_mean(decisions: list[dict[str, Any]], factor: str) -> float | None:
    values = [_factor_value(decision, factor) for decision in decisions]
    finite = [value for value in values if value is not None]
    if not finite:
        return None
    return _finite_float(mean(finite))


def _factor_value(decision: dict[str, Any], factor: str) -> float | None:
    factors = decision.get("factors")
    value = factors.get(factor) if isinstance(factors, dict) else None
    if value is None:
        vector = decision.get("factor_vector")
        try:
            value = vector[_FACTORS.index(factor)]
        except (TypeError, IndexError, ValueError):
            return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _execution_insights(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[tuple[float, dict[str, Any]]] = []
    for category in _CATEGORIES:
        rows = [decision for decision in decisions if decision.get("category") == category]
        if len(rows) < 2:
            continue
        poor_count = _quality_distribution(rows)["poor_execution"]
        poor_rate = poor_count / len(rows)
        if poor_rate >= 0.5:
            candidates.append(
                (
                    poor_rate,
                    {
                        "message": f"{category} has elevated poor execution outcomes.",
                        "category": category,
                        "factor": None,
                        "severity": "high" if poor_rate >= 0.75 else "medium",
                    },
                )
            )
    for pattern in _factor_patterns(decisions):
        delta = pattern["delta"]
        if delta is None:
            continue
        magnitude = abs(delta)
        if magnitude >= 0.15:
            candidates.append(
                (
                    magnitude,
                    {
                        "message": f"{pattern['factor']} separates strong and poor execution outcomes.",
                        "category": None,
                        "factor": pattern["factor"],
                        "severity": "high" if magnitude >= 0.30 else "medium",
                    },
                )
            )
    return [item for _, item in sorted(candidates, key=lambda entry: (-entry[0], str(entry[1]["message"])))[:3]]


def _category_vectors(grouped: dict[str, list[dict[str, Any]]]) -> dict[str, list[float]]:
    vectors: dict[str, list[float]] = {}
    for category, rows in grouped.items():
        if not rows:
            continue
        vector = []
        for factor in _FACTORS:
            factor_mean = _factor_mean(rows, factor)
            vector.append(0.0 if factor_mean is None else factor_mean)
        vectors[category] = vector
    return vectors


def _centroid_vectors(
    graph_store_factory: GraphStoreFactory | None,
    domain: str,
) -> dict[str, list[float]]:
    if graph_store_factory is None:
        return {}
    store = graph_store_factory()
    checkpoints = store.get_centroid_checkpoints(domain, limit=1)
    if not checkpoints:
        return {}
    centroids = checkpoints[-1].get("centroids")
    vectors: dict[str, list[float]] = {}
    for category_index, category in enumerate(_CATEGORIES):
        try:
            category_centroids = centroids[category_index]
        except (TypeError, IndexError):
            continue
        vector = _coerce_category_centroid(category_centroids)
        if vector:
            vectors[category] = vector
    return vectors


def _coerce_category_centroid(category_centroids: Any) -> list[float]:
    try:
        rows = category_centroids.tolist()
    except AttributeError:
        rows = category_centroids
    if not isinstance(rows, list) or not rows:
        return []
    if all(not isinstance(value, list) for value in rows):
        values = rows
    else:
        values = []
        for factor_index in range(len(_FACTORS)):
            factor_values = []
            for action_row in rows:
                try:
                    value = float(action_row[factor_index])
                except (TypeError, ValueError, IndexError):
                    continue
                if math.isfinite(value):
                    factor_values.append(value)
            values.append(mean(factor_values) if factor_values else 0.0)
    if len(values) != len(_FACTORS):
        return []
    return [_finite_float(value) for value in values]


def _dominant_factors(vector: list[float]) -> list[dict[str, Any]]:
    scored = [
        {"factor": factor, "score": _finite_float(value)}
        for factor, value in zip(_FACTORS, vector)
    ]
    return sorted(scored, key=lambda item: (-abs(item["score"] - 0.5), item["factor"]))[:3]


def _similar_categories(
    vectors: dict[str, list[float]],
    dominant: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for left, right in combinations(sorted(vectors), 2):
        distance = _l2_distance(vectors[left], vectors[right])
        left_factors = {item["factor"] for item in dominant.get(left, [])}
        right_factors = {item["factor"] for item in dominant.get(right, [])}
        pairs.append(
            {
                "category_a": left,
                "category_b": right,
                "distance": distance,
                "shared_dominant_factors": sorted(left_factors & right_factors),
            }
        )
    return sorted(pairs, key=lambda item: (item["distance"], item["category_a"], item["category_b"]))[:10]


def _transfer_opportunities(
    category_accuracy: dict[str, dict[str, Any]],
    similar: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    opportunities: list[tuple[float, dict[str, Any]]] = []
    for pair in similar:
        left = pair["category_a"]
        right = pair["category_b"]
        left_accuracy = category_accuracy[left]["accuracy"]
        right_accuracy = category_accuracy[right]["accuracy"]
        left_count = category_accuracy[left]["verified_count"]
        right_count = category_accuracy[right]["verified_count"]
        if left_count == 0 or right_count == 0:
            continue
        gap = abs(left_accuracy - right_accuracy)
        if gap < 0.15:
            continue
        source, target = (left, right) if left_accuracy > right_accuracy else (right, left)
        source_accuracy = max(left_accuracy, right_accuracy)
        target_accuracy = min(left_accuracy, right_accuracy)
        shared_factor = next(iter(pair["shared_dominant_factors"]), None)
        opportunities.append(
            (
                gap,
                {
                    "source_category": source,
                    "target_category": target,
                    "message": f"Apply {source} execution patterns to {target}.",
                    "source_accuracy": _finite_float(source_accuracy),
                    "target_accuracy": _finite_float(target_accuracy),
                    "shared_factor": shared_factor,
                },
            )
        )
    return [item for _, item in sorted(opportunities, key=lambda entry: (-entry[0], entry[1]["source_category"]))[:5]]


def _l2_distance(left: list[float], right: list[float]) -> float:
    return _finite_float(math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right))))


def _finite_float(value: float) -> float:
    number = float(value)
    if not math.isfinite(number):
        return 0.0
    return round(number, 6)
