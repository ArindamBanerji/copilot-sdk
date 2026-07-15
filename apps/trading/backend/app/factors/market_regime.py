"""Market regime factor computer."""

from __future__ import annotations

from typing import Any

from ci_trading.quant import classify_regime as _quant_classify_regime

from app.factors.base import clamp


def _classify_regime_legacy(vix: float, trend_strength: float = 20.0) -> str:
    if vix > 30:
        return "volatile"
    if vix > 20:
        return "ranging"
    if trend_strength > 25:
        return "trending"
    return "ranging"


def classify_regime(
    vix: float,
    trend_strength: float | None = None,
    price_history: Any | None = None,
    vix_history: Any | None = None,
) -> str:
    return str(classify_regime_context(vix, trend_strength, price_history, vix_history)["regime"])


def classify_regime_context(
    vix: float,
    trend_strength: float | None = None,
    price_history: Any | None = None,
    vix_history: Any | None = None,
) -> dict[str, Any]:
    try:
        result = _quant_classify_regime(vix, trend_strength, price_history, vix_history)
        if isinstance(result, dict) and result.get("regime"):
            return {
                "regime": str(result["regime"]),
                "hurst": result.get("hurst"),
                "vol_state": result.get("vol_state"),
                "vix_percentile": result.get("vix_percentile"),
            }
    except Exception:
        pass
    return {
        "regime": _classify_regime_legacy(vix, 20.0 if trend_strength is None else trend_strength),
        "hurst": None,
        "vol_state": None,
        "vix_percentile": None,
    }


class MarketRegimeFactor:
    factor_name = "market_regime"
    factor_index = 1

    def compute(self, event: object) -> float:
        if not isinstance(event, dict):
            return 0.5

        regime = event.get("current_regime")
        if regime is None:
            if "vix_at_entry" not in event:
                return 0.5
            try:
                vix = float(event.get("vix_at_entry"))
                trend_strength = float(event.get("trend_strength", 20.0))
            except (TypeError, ValueError):
                return 0.5
            regime = classify_regime(vix, trend_strength)

        accuracy = event.get("regime_accuracy", {})
        if not isinstance(accuracy, dict):
            return 0.5
        return clamp(accuracy.get(str(regime), 0.5))
