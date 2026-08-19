"""Configurable regime classification policy."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Mapping


@dataclass(frozen=True)
class RegimePolicy:
    """Per-copilot thresholds and evidence requirements.

    Indicator names are intentionally generic.  A non-market copilot may use
    the same detector with operational indicators mapped to these keys, or
    provide its own threshold names through ``thresholds``.
    """

    thresholds: Mapping[str, float] = field(default_factory=lambda: {
        "volatile": 30.0,
        "ranging": 20.0,
        "trending": 25.0,
        "calm_vix": 15.0,
        "calm_adx": 20.0,
    })
    abstention_minimum: int = 10
    conditioning_enabled: bool = True

    regime_names: tuple[str, ...] = ("trending", "ranging", "volatile", "calm", "unknown")
    indicator_names: tuple[str, ...] = ("vix", "adx", "trend_strength")

    def threshold(self, name: str, default: float) -> float:
        try:
            return float(self.thresholds.get(name, default))
        except (TypeError, ValueError):
            return default

    def classify(self, indicators: Mapping[str, Any]) -> tuple[str, float, dict[str, float]]:
        """Classify the default market indicator vocabulary.

        Policies for non-market copilots override this method. Keeping the
        original market rules here preserves the Trading detector contract
        while making the detector itself domain-neutral.
        """
        vix = _finite(indicators.get("vix"))
        if vix is None:
            vix = _finite(indicators.get("vix_at_entry"))
        adx = _finite(indicators.get("adx"))
        if adx is None:
            adx = _finite(indicators.get("trend_strength"))
        if vix is None and adx is None:
            return "unknown", 0.0, {}

        vix_value = 20.0 if vix is None else vix
        adx_value = 20.0 if adx is None else adx
        volatile_at = self.threshold("volatile", 30.0)
        ranging_at = self.threshold("ranging", 20.0)
        trending_at = self.threshold("trending", 25.0)
        calm_vix = self.threshold("calm_vix", 15.0)
        calm_adx = self.threshold("calm_adx", 20.0)

        if vix_value > volatile_at:
            regime = "volatile"
            distance = vix_value - volatile_at
        elif vix_value < ranging_at and adx_value > trending_at:
            regime = "trending"
            distance = min(ranging_at - vix_value, adx_value - trending_at)
        elif vix_value < calm_vix and adx_value <= calm_adx:
            regime = "calm"
            distance = min(calm_vix - vix_value, calm_adx - adx_value)
        else:
            regime = "ranging"
            distance = min(abs(vix_value - ranging_at), abs(adx_value - trending_at))
        confidence = min(1.0, max(0.05, distance / 10.0))
        output: dict[str, float] = {}
        if vix is not None:
            output["vix"] = vix_value
        if adx is not None:
            output["adx"] = adx_value
        if "trend_strength" in indicators and adx is not None:
            output["trend_strength"] = adx_value
        return regime, confidence, output


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
