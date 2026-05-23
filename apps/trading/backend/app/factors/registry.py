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
except Exception:
    ALL_FACTOR_NAMES = (
        "conviction",
        "research_depth",
        "technical_signal",
        "position_size",
        "time_horizon",
        "market_regime",
        "signal_confidence",
    )


TRADING_FACTOR_COMPUTERS = {
    "conviction": ConvictionFactor(),
    "research_depth": ResearchDepthFactor(),
    "technical_signal": TechnicalSignalFactor(),
    "position_size": PositionSizeFactor(),
    "time_horizon": TimeHorizonFactor(),
    "market_regime": MarketRegimeFactor(),
    "signal_confidence": SignalConfidenceFactor(),
}


def compute_factors(context: dict[str, Any]) -> dict[str, float]:
    payload = context if isinstance(context, dict) else {}
    values = {name: 0.5 for name in ALL_FACTOR_NAMES}
    for name, computer in TRADING_FACTOR_COMPUTERS.items():
        try:
            values[name] = clamp(computer.compute(payload))
        except Exception:
            values[name] = 0.5
    return values
