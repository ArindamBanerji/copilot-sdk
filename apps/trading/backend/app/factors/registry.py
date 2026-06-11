"""Trading factor registry."""

from __future__ import annotations

from typing import Any

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


def compute_factors(context: dict[str, Any]) -> dict[str, float]:
    payload = context if isinstance(context, dict) else {}
    values = {name: 0.5 for name in ALL_FACTOR_NAMES}
    for name, computer in TRADING_FACTOR_COMPUTERS.items():
        try:
            values[name] = clamp(computer.compute(payload))
        except Exception:
            values[name] = 0.5
    return values
