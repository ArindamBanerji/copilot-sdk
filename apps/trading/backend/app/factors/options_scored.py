"""Scored options factors for the Trading tensor."""

from __future__ import annotations

from typing import Any

from app.factors.base import clamp


MAX_DELTA_EXPOSURE = 1.0
MAX_GAMMA_RISK = 0.10


class OptionsDeltaExposureFactor:
    factor_name = "options_delta_exposure"
    factor_index = 7

    def compute(self, event: object) -> float:
        ctx = event if isinstance(event, dict) else {}
        delta = _number(_value(ctx, "delta", "options_delta", "delta_exposure", "net_delta"))
        if delta is None:
            return 0.5
        return round(clamp(abs(delta) / MAX_DELTA_EXPOSURE), 4)


class OptionsIVPercentileFactor:
    factor_name = "options_iv_percentile"
    factor_index = 8

    def compute(self, event: object) -> float:
        ctx = event if isinstance(event, dict) else {}
        value = _number(
            _value(
                ctx,
                "iv_percentile",
                "iv_rank",
                "options_iv_percentile",
                "implied_volatility_percentile",
                "implied_volatility_rank",
            )
        )
        if value is None:
            return 0.5
        if value > 1.0:
            value = value / 100.0
        return round(clamp(value), 4)


class OptionsGammaRiskFactor:
    factor_name = "options_gamma_risk"
    factor_index = 9

    def compute(self, event: object) -> float:
        ctx = event if isinstance(event, dict) else {}
        gamma = _number(_value(ctx, "gamma", "options_gamma", "gamma_risk", "net_gamma"))
        if gamma is None:
            return 0.5
        return round(clamp(abs(gamma) / MAX_GAMMA_RISK), 4)


def _value(context: dict[str, Any], *keys: str) -> Any:
    metadata = context.get("metadata") if isinstance(context.get("metadata"), dict) else {}
    options = context.get("options") if isinstance(context.get("options"), dict) else {}
    for key in keys:
        if key in context:
            return context.get(key)
        if key in metadata:
            return metadata.get(key)
        if key in options:
            return options.get(key)
    return None


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


__all__ = [
    "OptionsDeltaExposureFactor",
    "OptionsIVPercentileFactor",
    "OptionsGammaRiskFactor",
]
