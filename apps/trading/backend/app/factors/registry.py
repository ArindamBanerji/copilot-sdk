"""Trading factor registry."""

from __future__ import annotations

from typing import Any

from app.factors.base import clamp
from app.factors.conviction import ConvictionFactor
from app.factors.market_regime import MarketRegimeFactor
from app.factors.position_size import PositionSizeFactor
from app.factors.research_depth import ResearchDepthFactor
from app.factors.signal_confidence import SignalConfidenceFactor
from app.factors.technical_signal import TechnicalSignalFactor
from app.factors.time_horizon import TimeHorizonFactor

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
    )
    _USING_FALLBACK_FACTOR_NAMES = True


_PRESET_FACTOR_COMPUTERS = {
    "signal_alignment": ConvictionFactor(),
    "market_regime": ResearchDepthFactor(),
    "position_sizing": TechnicalSignalFactor(),
    "timing_quality": PositionSizeFactor(),
    "risk_reward_actual": TimeHorizonFactor(),
    "emotional_indicator": MarketRegimeFactor(),
    "signal_confidence": SignalConfidenceFactor(),
}

_FALLBACK_FACTOR_COMPUTERS = {
    "signal_alignment": ConvictionFactor(),
    "market_regime": MarketRegimeFactor(),
    "position_sizing": PositionSizeFactor(),
    "timing_quality": TechnicalSignalFactor(),
    "risk_reward_actual": TimeHorizonFactor(),
    "emotional_indicator": ResearchDepthFactor(),
    "signal_confidence": SignalConfidenceFactor(),
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
