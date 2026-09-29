"""Trading factor registry."""

from __future__ import annotations

from typing import Any

from copilot_sdk.backend.graph_access import GRAPH_CONNECTION_ERRORS

from app.factors.base import clamp
from app.factors.emotional_indicator import EmotionalIndicatorFactor
from app.factors.market_regime import MarketRegimeFactor
from app.factors.options_scored import (
    OptionsDeltaExposureFactor,
    OptionsGammaRiskFactor,
    OptionsIVPercentileFactor,
)
from app.factors.position_size import PositionSizeFactor
from app.factors.risk_reward import RiskRewardActualFactor
from app.factors.signal_alignment import SignalAlignmentFactor
from app.factors.signal_confidence import SignalConfidenceFactor
from app.factors.timing_quality import TimingQualityFactor

try:
    from copilot_sdk.scoring.presets.trading import TradingPreset

    ALL_FACTOR_NAMES = tuple(TradingPreset().shape.factor_names)
    _USING_FALLBACK_FACTOR_NAMES = False
except Exception:
    ALL_FACTOR_NAMES = (
        "signal_alignment",
        "market_regime",
        "position_sizing",
        "timing_quality",
        "risk_reward_actual",
        "emotional_indicator",
        "signal_confidence",
        "options_delta_exposure",
        "options_iv_percentile",
        "options_gamma_risk",
    )
    _USING_FALLBACK_FACTOR_NAMES = True


_PRESET_FACTOR_COMPUTERS = {
    "signal_alignment": SignalAlignmentFactor(),
    "market_regime": MarketRegimeFactor(),
    "position_sizing": PositionSizeFactor(),
    "timing_quality": TimingQualityFactor(),
    "risk_reward_actual": RiskRewardActualFactor(),
    "emotional_indicator": EmotionalIndicatorFactor(),
    "signal_confidence": SignalConfidenceFactor(),
    "options_delta_exposure": OptionsDeltaExposureFactor(),
    "options_iv_percentile": OptionsIVPercentileFactor(),
    "options_gamma_risk": OptionsGammaRiskFactor(),
}

_FALLBACK_FACTOR_COMPUTERS = {
    "signal_alignment": SignalAlignmentFactor(),
    "market_regime": MarketRegimeFactor(),
    "position_sizing": PositionSizeFactor(),
    "timing_quality": TimingQualityFactor(),
    "risk_reward_actual": RiskRewardActualFactor(),
    "emotional_indicator": EmotionalIndicatorFactor(),
    "signal_confidence": SignalConfidenceFactor(),
    "options_delta_exposure": OptionsDeltaExposureFactor(),
    "options_iv_percentile": OptionsIVPercentileFactor(),
    "options_gamma_risk": OptionsGammaRiskFactor(),
}

TRADING_FACTOR_COMPUTERS = (
    _FALLBACK_FACTOR_COMPUTERS if _USING_FALLBACK_FACTOR_NAMES else _PRESET_FACTOR_COMPUTERS
)


def get_factor_registry() -> dict[str, Any]:
    return dict(_FALLBACK_FACTOR_COMPUTERS)


class FactorComputation(dict[str, float]):
    def __init__(self, values: dict[str, float], degraded_factors: list[str]) -> None:
        super().__init__(values)
        self.degraded_factors = list(degraded_factors)
        self.factor_availability = {
            name: name not in degraded_factors for name in values
        }


_FACTOR_ERRORS = (*GRAPH_CONNECTION_ERRORS, RuntimeError)


def compute_factors(context: dict[str, Any]) -> FactorComputation:
    payload = context if isinstance(context, dict) else {}
    values = {name: 0.5 for name in ALL_FACTOR_NAMES}
    degraded_factors: list[str] = []
    for name, computer in TRADING_FACTOR_COMPUTERS.items():
        try:
            raw_value = computer.compute(payload)
        except _FACTOR_ERRORS:
            values[name] = 0.5
            degraded_factors.append(name)
            continue
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
            values[name] = 0.5
            degraded_factors.append(name)
            continue
        values[name] = clamp(raw_value)
    return FactorComputation(values, degraded_factors)
