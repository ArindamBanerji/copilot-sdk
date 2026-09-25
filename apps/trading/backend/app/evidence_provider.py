"""Trading-specific VLD evidence provider."""
from __future__ import annotations

from typing import Any, Optional

TRADING_VLD_FACTOR_NAMES = [
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
]

TRADING_FACTOR_ALIASES = {
    "thesis_strength": "signal_alignment",
    "thesis_alignment": "signal_alignment",
    "correlation_exposure": "market_regime",
    "correlation_risk": "market_regime",
    "momentum_signal": "timing_quality",
    "momentum": "timing_quality",
    "fundamental_quality": "risk_reward_actual",
    "fundamental_strength": "risk_reward_actual",
    "volatility_regime": "options_iv_percentile",
    "volatility": "options_iv_percentile",
}

_SHOWCASE_EVIDENCE: dict[str, dict[int, dict[str, Any]]] = {}


def normalize_factor_name(factor_name: str | None, dimension: int) -> str:
    if factor_name in TRADING_FACTOR_ALIASES:
        return TRADING_FACTOR_ALIASES[factor_name]
    if factor_name in TRADING_VLD_FACTOR_NAMES:
        return str(factor_name)
    if 0 <= int(dimension) < len(TRADING_VLD_FACTOR_NAMES):
        return TRADING_VLD_FACTOR_NAMES[int(dimension)]
    return str(factor_name or f"factor_{dimension}")


def register_showcase_evidence(trade_id: str, evidence_by_dimension: dict[int, dict[str, Any]]) -> None:
    _SHOWCASE_EVIDENCE[str(trade_id)] = {
        int(dimension): dict(payload)
        for dimension, payload in evidence_by_dimension.items()
    }


def get_showcase_evidence(trade_id: str) -> dict[int, dict[str, Any]]:
    return {k: dict(v) for k, v in _SHOWCASE_EVIDENCE.get(str(trade_id), {}).items()}


class TradingEvidenceProvider:
    """EvidenceProvider implementation for Trading VLD investigations."""

    def __init__(self, data_source: Any, trade_id: str):
        self.data_source = data_source
        self.trade_id = str(trade_id)

    def read_evidence(self, decision_id: str, dimension: int, factor_name: str) -> Optional[dict[str, Any]]:
        dim = int(dimension)
        canonical = normalize_factor_name(factor_name, dim)

        seeded = _SHOWCASE_EVIDENCE.get(self.trade_id, {}).get(dim)
        if seeded is not None:
            return self._normalize_payload(seeded, canonical)

        sourced = self._read_from_data_source(dim, canonical)
        if sourced is not None:
            return sourced
        return None

    def _read_from_data_source(self, dimension: int, factor_name: str) -> Optional[dict[str, Any]]:
        if self.data_source is None:
            return None
        if hasattr(self.data_source, "get_vld_evidence"):
            try:
                payload = self.data_source.get_vld_evidence(self.trade_id, dimension, factor_name)
            except TypeError:
                payload = self.data_source.get_vld_evidence(self.trade_id, dimension)
            return self._normalize_payload(payload, factor_name)
        evidence_map = getattr(self.data_source, "vld_evidence", None)
        if isinstance(evidence_map, dict):
            payload = evidence_map.get((self.trade_id, dimension))
            if payload is None:
                trade_payload = evidence_map.get(self.trade_id)
                if isinstance(trade_payload, dict):
                    payload = trade_payload.get(dimension)
            return self._normalize_payload(payload, factor_name)
        if isinstance(self.data_source, dict):
            trade_payload = self.data_source.get(self.trade_id)
            if isinstance(trade_payload, dict):
                return self._normalize_payload(trade_payload.get(dimension) or trade_payload.get(factor_name), factor_name)
        return None

    def lookup_description(self, factor_name: str) -> str:
        canonical = normalize_factor_name(factor_name, TRADING_VLD_FACTOR_NAMES.index(factor_name) if factor_name in TRADING_VLD_FACTOR_NAMES else 0)
        return {
            "signal_alignment": "current thesis validity indicators",
            "market_regime": "cross-asset correlation and regime reversal context",
            "position_sizing": "portfolio allocation and concentration",
            "timing_quality": "momentum and entry timing divergence",
            "risk_reward_actual": "fundamental quality and realized risk/reward",
            "emotional_indicator": "behavioral or discretionary risk context",
            "signal_confidence": "confidence of the active trading signal",
            "options_delta_exposure": "delta exposure for options-linked trades",
            "options_iv_percentile": "current volatility regime",
            "options_gamma_risk": "gamma concentration and convexity risk",
        }.get(canonical, "trading context")

    def _normalize_payload(self, payload: Any, factor_name: str) -> Optional[dict[str, Any]]:
        if not isinstance(payload, dict):
            return None
        value = payload.get("value")
        if value is None:
            return None
        try:
            numeric_value = float(value)
            confidence = float(payload.get("confidence", 0.8))
        except (TypeError, ValueError):
            return None
        return {
            "value": max(0.0, min(1.0, numeric_value)),
            "confidence": max(0.0, min(1.0, confidence)),
            "source": str(payload.get("source") or self._default_source(factor_name)),
        }

    def _default_source(self, factor_name: str) -> str:
        return {
            "signal_alignment": "thesis_tracker",
            "market_regime": "correlation_engine",
            "position_sizing": "portfolio_engine",
            "timing_quality": "momentum_tracker",
            "risk_reward_actual": "fundamental_db",
            "options_iv_percentile": "vol_tracker",
        }.get(factor_name, "trading_data")
