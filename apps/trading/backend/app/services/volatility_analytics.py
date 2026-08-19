"""Observation-only volatility scenario analytics for Trading."""

from __future__ import annotations

import math
from statistics import mean
from typing import Any

from app.analytics.dispersion_follow import compute_dispersion_follow_rate
from app.analytics.regime_vrp import compute_regime_vrp
from app.analytics.vol_sharpe import compute_clustering_adjusted_sharpe
from app.analytics.vrp_attribution import compute_vrp_attribution


class VolatilityAnalytics:
    """Compose existing measured analytics into the B35 surface contract."""

    def clustering_adjusted_sharpe(
        self, trades: list[dict[str, Any]], regime: str | None = None
    ) -> dict[str, Any]:
        rows = _for_regime(trades, regime)
        return _observation(
            compute_clustering_adjusted_sharpe(rows),
            f"Observation: clustering-adjusted decision quality is reported for {regime} conditions."
            if regime
            else "Observation: clustering-adjusted decision quality is reported across available conditions.",
        )

    def vrp_analysis(
        self,
        trades: list[dict[str, Any]],
        vix_data: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        del vix_data  # IV/RV and tail dependence are persisted with each decision.
        return _observation(
            compute_vrp_attribution(trades),
            "Observation: IV/RV spread and tail-dependence attribution are reported from eligible decisions.",
        )

    def rich_cheap_regime(
        self, trades: list[dict[str, Any]], regime: str | None = None
    ) -> dict[str, Any]:
        selected = _for_regime(trades, regime)
        payload = compute_regime_vrp(selected)
        payload["current_regime"] = _canonical_regime(regime) if regime else _latest_regime(trades)
        return _observation(
            payload,
            "Observation: regime-conditioned IV/RV bands are reported as rich, cheap, or unknown from measured history.",
        )

    def dispersion_follow_rate(self, trades: list[dict[str, Any]]) -> dict[str, Any]:
        return _observation(
            compute_dispersion_follow_rate(trades),
            "Observation: dispersion signals and their recorded follow outcomes are reported.",
        )

    def effective_bets_in_tail(
        self, trades: list[dict[str, Any]], vix_threshold: float = 30.0
    ) -> dict[str, Any]:
        threshold_value = _finite(vix_threshold, 30.0)
        threshold = threshold_value if threshold_value is not None else 30.0
        tail = [trade for trade in trades if (_vix(trade) or -math.inf) >= threshold]
        effective = _values_for(tail, "n_effective_bets", "effective_bets")
        nominal = _values_for(tail, "nominal_bets", "n_bets", "asset_count")
        measured = len(tail) >= 30 and bool(effective)
        payload = {
            "vix_threshold": threshold,
            "tail_decisions": len(tail),
            "effective_bets": round(mean(effective), 4) if measured else None,
            "nominal_bets": round(mean(nominal), 4) if measured and nominal else None,
            "effective_bets_reduction": (
                round(1.0 - mean(effective) / mean(nominal), 4)
                if measured and nominal and mean(nominal) > 0
                else None
            ),
            "observations_with_effective_bets": len(effective),
            "minimum_observations": 30,
            "day_zero": not measured,
            "decisions_until_measured": max(0, 30 - len(tail)),
            "provenance": "real_measured" if measured else "accumulating",
            "substantiation": "T-R" if measured else "T-O",
        }
        return _observation(
            payload,
            "Observation: effective position breadth in high-volatility conditions is reported when persisted correlation diagnostics are available.",
        )


def _observation(payload: dict[str, Any], message: str) -> dict[str, Any]:
    result = {key: _json_safe(value) for key, value in payload.items()}
    result["evidence_tier"] = str(result.get("substantiation") or "T-O")
    result["observation"] = message
    result["observation_only"] = True
    return result


def _for_regime(trades: list[dict[str, Any]], regime: str | None) -> list[dict[str, Any]]:
    if not regime:
        return list(trades)
    selected = _canonical_regime(regime)
    return [trade for trade in trades if _canonical_regime(_trade_regime(trade)) == selected]


def _latest_regime(trades: list[dict[str, Any]]) -> str | None:
    for trade in reversed(trades):
        value = _trade_regime(trade)
        if value:
            return _canonical_regime(value)
    return None


def _trade_regime(trade: dict[str, Any]) -> str:
    for value in (
        trade.get("regime"),
        trade.get("current_regime"),
        _nested(trade.get("regime_metadata"), "regime"),
        _nested(_nested(trade.get("metadata"), "regime_metadata"), "regime"),
        _nested(trade.get("metadata"), "regime"),
    ):
        if value:
            return str(value)
    return "ranging"


def _canonical_regime(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"range", "ranging", "choppy", "chop"}:
        return "ranging"
    return text if text in {"trending", "volatile", "calm"} else "ranging"


def _vix(trade: dict[str, Any]) -> float | None:
    return _number_from(trade, "vix", "vix_at_entry", "current_vix")


def _number_from(trade: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = _finite(trade.get(key))
        if value is not None:
            return value
        metadata = trade.get("metadata")
        if isinstance(metadata, dict):
            value = _finite(metadata.get(key))
            if value is not None:
                return value
    return None


def _values_for(trades: list[dict[str, Any]], *keys: str) -> list[float]:
    values: list[float] = []
    for trade in trades:
        value = _number_from(trade, *keys)
        if value is not None:
            values.append(value)
    return values


def _nested(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def _finite(value: Any, default: float | None = None) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value
