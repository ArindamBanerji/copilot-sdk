"""Trading factor computers."""

from app.factors.conviction import ConvictionFactor
from app.factors.market_regime import MarketRegimeFactor, classify_regime
from app.factors.registry import compute_factors
from app.factors.technical_signal import TechnicalSignalFactor

__all__ = [
    "ConvictionFactor",
    "MarketRegimeFactor",
    "TechnicalSignalFactor",
    "classify_regime",
    "compute_factors",
]
