"""Purchasing DK trust-weight radar endpoints."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter

from copilot_sdk.scoring.presets.purchasing import PurchasingPreset


LEARNING_THRESHOLD = 200
PROVENANCE_TIER = "real_measured"
EXPECTED_SOURCE = "preset_default"

FACTOR_LABELS = {
    "expected_demand": "Demand forecast",
    "day_of_week": "Day of week",
    "weather_forecast": "Weather impact",
    "event_flag": "Event signal",
    "historical_waste": "Waste history",
    "supplier_lead_time": "Lead time",
    "price_memory_index": "Price memory",
}

EXPECTED_WEIGHTS = {
    "expected_demand": 0.70,
    "day_of_week": 0.50,
    "weather_forecast": 0.50,
    "event_flag": 0.55,
    "historical_waste": 0.65,
    "supplier_lead_time": 0.60,
    "price_memory_index": 0.70,
}

ScorerFactory = Callable[[], Any]


def create_trust_router(scorer_factory: ScorerFactory | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing", tags=["purchasing-trust-radar"])

    @router.get("/trust-weights")
    def trust_weights() -> dict[str, Any]:
        scorer = _scorer(scorer_factory)
        decisions_total = _decisions_total(scorer)
        weights = _weights_payload(scorer)
        if decisions_total < LEARNING_THRESHOLD or weights is None:
            return {
                "weights": None,
                "phase": "learning",
                "decisions_total": decisions_total,
                "decisions_needed": max(LEARNING_THRESHOLD - decisions_total, 0),
                "provenance": PROVENANCE_TIER,
            }
        return {
            "weights": weights,
            "phase": "active",
            "decisions_total": decisions_total,
            "decisions_needed": 0,
            "provenance": PROVENANCE_TIER,
        }

    @router.get("/trust-weights/expected")
    def expected_weights() -> dict[str, Any]:
        return {
            "weights": _expected_weights(),
            "source": EXPECTED_SOURCE,
            "factor_labels": FACTOR_LABELS,
        }

    @router.get("/trust-weights/insights")
    def trust_insights() -> list[dict[str, Any]]:
        scorer = _scorer(scorer_factory)
        decisions_total = _decisions_total(scorer)
        weights = _weights_payload(scorer)
        if decisions_total < LEARNING_THRESHOLD or weights is None:
            return []
        return _insights(weights)

    return router


def _weights_payload(scorer: Any | None) -> dict[str, dict[str, float]] | None:
    if scorer is None:
        return None
    getter = getattr(scorer, "get_dk_weights", None)
    if not callable(getter):
        return None
    raw_weights = getter()
    if not raw_weights:
        return None

    shape = PurchasingPreset().shape
    categories = list(shape.category_names)
    factors = list(shape.factor_names)
    output: dict[str, dict[str, float]] = {}
    for category_index, category in enumerate(categories):
        row = raw_weights[category_index] if category_index < len(raw_weights) else []
        if not isinstance(row, (list, tuple)):
            return None
        output[category] = {
            factor: _bounded(row[factor_index] if factor_index < len(row) else 0.0)
            for factor_index, factor in enumerate(factors)
        }
    return output


def _expected_weights() -> dict[str, dict[str, float]]:
    shape = PurchasingPreset().shape
    return {
        category: dict(EXPECTED_WEIGHTS)
        for category in shape.category_names
    }


def _insights(weights: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    expected = _expected_weights()
    insights: list[dict[str, Any]] = []
    for category, actual_weights in weights.items():
        expected_weights = expected.get(category, {})
        trusted_factor = max(
            expected_weights,
            key=lambda factor: expected_weights.get(factor, 0.0),
        )
        for factor, actual in actual_weights.items():
            gap = actual - expected_weights.get(factor, 0.0)
            if gap <= 0.15:
                continue
            insights.append(
                {
                    "category": category,
                    "insight": (
                        f"You rely on {FACTOR_LABELS[trusted_factor]} but the system "
                        f"learned {FACTOR_LABELS[factor]} matters more."
                    ),
                    "trap_factor": factor,
                    "trusted_factor": trusted_factor,
                    "gap": round(gap, 3),
                }
            )
    insights.sort(key=lambda item: float(item["gap"]), reverse=True)
    return insights


def _scorer(factory: ScorerFactory | None) -> Any | None:
    if factory is None:
        return None
    candidate = factory()
    if callable(getattr(candidate, "get_dk_weights", None)):
        return candidate
    nested = getattr(candidate, "_scorer", None)
    if callable(nested):
        return nested()
    return None


def _decisions_total(scorer: Any | None) -> int:
    if scorer is None:
        return 0
    getter = getattr(scorer, "get_verified_count", None)
    if callable(getter):
        try:
            return int(getter())
        except Exception:
            return 0
    store = getattr(scorer, "graph_store", None)
    count_verified = getattr(store, "count_verified", None)
    if callable(count_verified):
        try:
            return int(count_verified("purchasing"))
        except Exception:
            return 0
    return 0


def _bounded(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return round(max(0.0, min(number, 1.0)), 3)
