"""Position size factor computer."""

from __future__ import annotations

from typing import Any

from app.factors.base import clamp, mean_or_neutral


class PositionSizeFactor:
    factor_name = "timing_quality"
    factor_index = 3

    def compute(self, event: object) -> float:
        ctx = event if isinstance(event, dict) else {}
        if not ctx:
            return 0.5

        components: list[float] = []

        if "position_pct_of_max" in ctx:
            components.append(_size_vs_max_score(ctx.get("position_pct_of_max")))

        if "portfolio_concentration" in ctx:
            components.append(_concentration_score(ctx.get("portfolio_concentration")))

        if "correlated_exposure" in ctx:
            components.append(_correlated_exposure_score(ctx.get("correlated_exposure")))

        if "kelly_ratio" in ctx:
            components.append(_kelly_ratio_score(ctx.get("kelly_ratio")))

        return mean_or_neutral(components)


def _size_vs_max_score(value: Any) -> float:
    try:
        size = float(value)
    except (TypeError, ValueError):
        return 0.5
    if size <= 0:
        return 0.0
    if size < 0.3:
        return clamp(size / 0.3)
    if size <= 1.0:
        return 1.0
    if size <= 1.5:
        return clamp(1.0 - ((size - 1.0) / 0.5) * 0.5)
    return 0.2


def _concentration_score(value: Any) -> float:
    try:
        concentration = float(value)
    except (TypeError, ValueError):
        return 0.5
    if concentration <= 0.05:
        return 1.0
    if concentration <= 0.10:
        return 0.8
    if concentration <= 0.20:
        return 0.5
    return 0.2


def _correlated_exposure_score(value: Any) -> float:
    try:
        exposure = float(value)
    except (TypeError, ValueError):
        return 0.5
    return clamp(1.0 - exposure)


def _kelly_ratio_score(value: Any) -> float:
    try:
        kelly_ratio = float(value)
    except (TypeError, ValueError):
        return 0.5
    return clamp(1.0 - min(abs(kelly_ratio - 1.0), 1.0))
