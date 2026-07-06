"""Purchasing trust analysis endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from copilot_sdk.scoring.presets.purchasing import PurchasingPreset

from .factor_display import DISPLAY_NAMES

FACTOR_NAMES = tuple(PurchasingPreset().shape.factor_names)
EXPECTED_WEIGHT = 1.0 / len(FACTOR_NAMES)
HERO_NARRATIVE = "The factor you trust most is the one that lies to you."


def create_trust_router(graph_store_factory: Any | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing", tags=["purchasing-trust"])

    @router.get("/trust")
    def trust_analysis() -> dict[str, Any]:
        actual_weights = _actual_weights(graph_store_factory)
        available = actual_weights is not None
        return {
            "available": available,
            "hero_narrative": HERO_NARRATIVE,
            "factors": _factor_rows(actual_weights),
        }

    return router


def _factor_rows(actual_weights: dict[str, float] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for code_name in FACTOR_NAMES:
        row: dict[str, Any] = {
            "display_name": DISPLAY_NAMES.get(code_name, code_name),
            "expected_weight": EXPECTED_WEIGHT,
        }
        if actual_weights is not None:
            actual_weight = actual_weights.get(code_name, 0.0)
            row["actual_weight"] = actual_weight
            row["trust_trap"] = actual_weight < EXPECTED_WEIGHT * 0.5
        rows.append(row)
    return rows


def _actual_weights(provider: Any | None) -> dict[str, float] | None:
    scorer = _scorer(provider)
    if scorer is None:
        return None
    getter = getattr(scorer, "get_dk_weights", None)
    if not callable(getter):
        return None
    weights = getter()
    if not weights:
        return None
    factor_names = list(FACTOR_NAMES)
    totals = {name: 0.0 for name in factor_names}
    rows = 0
    for row in weights:
        if not isinstance(row, (list, tuple)):
            continue
        rows += 1
        for index, name in enumerate(factor_names):
            if index < len(row):
                totals[name] += _bounded(row[index])
    if rows <= 0:
        return None
    averages = {name: totals[name] / rows for name in factor_names}
    total = sum(averages.values())
    if total <= 0.0:
        return None
    return {name: averages[name] / total for name in factor_names}


def _scorer(provider: Any | None) -> Any | None:
    if provider is None:
        return None
    if callable(getattr(provider, "get_dk_weights", None)):
        return provider
    factory = getattr(provider, "_scorer", None)
    if callable(factory):
        return factory()
    return None


def _bounded(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return max(0.0, min(number, 1.0))
