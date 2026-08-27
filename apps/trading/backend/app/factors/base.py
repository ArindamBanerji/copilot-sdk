"""Shared helpers for Trading factor computers."""

from __future__ import annotations

from typing import Any, cast

from copilot_sdk.protocols.factor_computer import FactorComputer


def clamp(value: Any, default: float = 0.5) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return cast(float, max(0.0, min(1.0, numeric)))


def mean_or_neutral(values: list[float]) -> float:
    if not values:
        return 0.5
    return clamp(sum(values) / len(values))


__all__ = ["FactorComputer", "clamp", "mean_or_neutral"]
