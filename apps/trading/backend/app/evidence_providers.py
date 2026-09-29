"""Tier 5D trading evidence from domain records and explicit fixture data.

Computed values use the established factor conventions. Missing inputs produce
a labeled neutral fallback; fixture records retain their sample provenance.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from app.evidence_provider import TradingEvidenceProvider as LegacyEvidenceProvider
from app.evidence_provider import get_showcase_evidence

FACTOR_NAMES = ["signal_alignment","market_regime","position_sizing","timing_quality","risk_reward_actual","emotional_indicator","signal_confidence","options_delta_exposure","options_iv_percentile","options_gamma_risk"]
POLICY_VERSION = "tier5d-trading-providers-v1"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

def _number(value: Any) -> float | None:
    try:
        if isinstance(value, bool):
            return None
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _bounded(value: Any) -> float:
    number = _number(value)
    return 0.5 if number is None else max(0.0, min(1.0, number))


def _field(context: dict, *names: str) -> Any:
    for name in names:
        for block in (context, context.get("metadata"), context.get("options")):
            if isinstance(block, dict) and name in block:
                return block[name]
    return None


def _record(rows: Any, entity_id: str, key: str) -> dict:
    if isinstance(rows, dict):
        row = rows.get(entity_id)
        return dict(row) if isinstance(row, dict) else {}
    if isinstance(rows, list):
        return next((dict(row) for row in rows if isinstance(row, dict)
                     and str(row.get(key)) == entity_id), {})
    return {}


def _json_data(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}


def _flatten(record: dict) -> dict:
    metadata = record.get("metadata")
    return {**(metadata if isinstance(metadata, dict) else {}), **record}


def _domain_context(entity_id, data_source, fixture_data, decision_id=None):
    source = fixture_data if fixture_data is not None else data_source
    context = {}
    fixture_match = False
    from_file = False
    graph_available = True
    if isinstance(source, dict):
        context = _record(source.get("trades", source), entity_id, "trade_id")
        if not context and any(key in source for key in ("metadata", "options", "actual_risk_reward", "delta", "gamma", "iv_percentile")):
            context = dict(source)
        fixture_match = bool(context) and fixture_data is not None
    if not context:
        reader = getattr(data_source, "get_vld_context", None)
        getter = getattr(data_source, "get_decision", None)
        try:
            if callable(reader):
                context = reader(entity_id) or {}
            elif callable(getter):
                context = getter(decision_id or entity_id, "trading") or {}
        except (ConnectionError, TimeoutError, RuntimeError):
            return {}, False, False
    if not isinstance(context, dict):
        return {}, False, False
    if not fixture_match and not isinstance(data_source, dict):
        root = Path(source) if isinstance(source, (str, Path)) else DATA_DIR
        if root.is_file():
            data = _json_data(root)
            rows = data.get("trades", {}) if isinstance(data, dict) else data
            local = _record(rows, entity_id, "trade_id")
        else:
            rows = _json_data(root / "trade_metadata.json")
            local = (_record(rows, entity_id, "trade_id")
                     or _record(rows, decision_id or entity_id, "trade_id"))
            if not local:
                local = _record(_json_data(root / "trading_seed_v2.json"), entity_id, "trade_id")
        from_file = bool(local)
        context = {**local, **_flatten(context)}
    context = _flatten(context)
    sample = fixture_match or from_file or context.get("provenance") in {"sample", "synthetic"}
    return context, sample, graph_available


def _fixture_read(entity_id, dimension, factor_name, source):
    return LegacyEvidenceProvider(source, entity_id).read_evidence(entity_id, dimension, factor_name)

def _valid_payload(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict) or payload.get("value") is None:
        return None
    try:
        value = float(payload["value"])
        confidence = float(payload.get("confidence", 0.8))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value) or not math.isfinite(confidence):
        return None
    return {**payload, "value": max(0.0, min(1.0, value)),
            "confidence": max(0.0, min(1.0, confidence))}


class FactorEvidenceProvider:
    factor_name: str
    dimension_index: int

    def _compute(self, context: dict) -> float | None:
        factors = context.get("factors")
        value = context.get(self.factor_name)
        if value is None and isinstance(factors, dict):
            value = factors.get(self.factor_name)
        return _number(value)

    def provide(self, context: dict) -> float:
        """Return a finite [0,1] factor; missing or invalid input is neutral 0.5."""
        try:
            value = self._compute(context if isinstance(context, dict) else {})
            return _bounded(value)
        except (TypeError, ValueError, OverflowError, ZeroDivisionError):
            return 0.5

    def read_payload(self, entity_id: str, data_source: Any = None, *,
                     fixture_data: Any = None, seed_entity_id: str | None = None,
                     decision_id: str | None = None):
        if self.dimension_index >= 4:
            context, sample, graph_available = _domain_context(entity_id, data_source, fixture_data, decision_id)
            try:
                computed = self._compute(context)
            except (TypeError, ValueError, OverflowError, ZeroDivisionError):
                computed = None
            missing = _number(computed) is None
            tier = "MISSING_DATA" if missing else "SYNTHETIC" if sample else "DOMAIN_DATA"
            source = ("MISSING_DATA:neutral:" if missing else "SYNTHETIC:fixture:" if sample else "computed:")
            return {"value": _bounded(computed), "confidence": 0.0 if missing else 1.0,
                    "source": source + self.factor_name,
                    "evidence_tier": tier, "missing_data": missing,
                    "graph_available": graph_available,
                    "input_entity_id": entity_id}
        payload = None
        graph_read = False
        reader = getattr(data_source, "get_vld_evidence", None)
        if callable(reader):
            payload = _valid_payload(reader(entity_id, self.dimension_index, self.factor_name))
            graph_read = payload is not None
        fallback_source: Any = fixture_data if fixture_data is not None else data_source
        if callable(reader) and fixture_data is None and not isinstance(fallback_source, dict):
            fallback_source = None
        if payload is None:
            payload = _valid_payload(_fixture_read(entity_id, self.dimension_index, self.factor_name, fallback_source))
        if payload is not None and not graph_read and (fixture_data is not None or isinstance(fallback_source, dict) or bool(get_showcase_evidence(entity_id))):
            payload = {**payload, "source": "SYNTHETIC:fixture:" + str(payload.get("source", "fixture")),
                       "evidence_tier": "SYNTHETIC"}
        return payload

    def read(self, entity_id: str, data_source: Any = None, **kwargs: Any) -> float | None:
        payload = self.read_payload(entity_id, data_source, **kwargs)
        return None if payload is None else float(payload["value"])


class SignalAlignmentProvider(FactorEvidenceProvider):
    factor_name = "signal_alignment"
    dimension_index = 0


class MarketRegimeProvider(FactorEvidenceProvider):
    factor_name = "market_regime"
    dimension_index = 1


class PositionSizingProvider(FactorEvidenceProvider):
    factor_name = "position_sizing"
    dimension_index = 2


class TimingQualityProvider(FactorEvidenceProvider):
    factor_name = "timing_quality"
    dimension_index = 3


class RiskRewardActualProvider(FactorEvidenceProvider):
    """Normalize realized/planned R using the existing Trading factor convention."""
    factor_name = "risk_reward_actual"
    dimension_index = 4
    def _compute(self, context):
        actual = _number(_field(context, "actual_risk_reward", "r_multiple"))
        planned = _number(_field(context, "planned_risk_reward", "rr_ratio", "rrRatio"))
        if actual is None:
            entry = _number(_field(context, "entry_price", "entryPrice"))
            exit_price = _number(_field(context, "exit_price", "exitPrice"))
            stop = _number(_field(context, "stop_loss", "stopLoss"))
            if entry is None or exit_price is None or stop is None or entry == stop:
                return None
            side = -1.0 if context.get("side") == "short" else 1.0
            actual = side * (exit_price - entry) / abs(entry - stop)
        if planned is None:
            return _bounded((actual + 1.0) / 3.0)
        return None if planned <= 0 else _bounded((actual / planned + 0.5) / 2.0)


class EmotionalIndicatorProvider(FactorEvidenceProvider):
    """Trading behavior score: deduct for rapid loss re-entry, oversizing and chasing."""
    factor_name = "emotional_indicator"
    dimension_index = 5
    def _compute(self, context):
        keys = ("minutes_since_last_trade", "last_trade_was_loss", "consecutive_wins",
                "size_vs_rolling_avg", "entry_at_day_extreme")
        values = {key: _field(context, key) for key in keys}
        if not any(value is not None for value in values.values()):
            return None
        for key in ("minutes_since_last_trade", "consecutive_wins", "size_vs_rolling_avg"):
            if values[key] is not None and _number(values[key]) is None:
                return None
        for key in ("last_trade_was_loss", "entry_at_day_extreme"):
            if values[key] is not None and not isinstance(values[key], bool):
                return None
        minutes = _number(values["minutes_since_last_trade"])
        wins = _number(values["consecutive_wins"])
        sizing = _number(values["size_vs_rolling_avg"])
        score = 1.0
        if values["last_trade_was_loss"] is True and minutes is not None and minutes < 30:
            score -= 0.4
        if wins is not None and sizing is not None and wins >= 3 and sizing > 1.3:
            score -= 0.3
        if values["entry_at_day_extreme"] is True:
            score -= 0.2
        return _bounded(score)


class SignalConfidenceProvider(FactorEvidenceProvider):
    """Mean of available coverage, category accuracy, support and novelty scores."""
    factor_name = "signal_confidence"
    dimension_index = 6
    def _compute(self, context):
        scores = []
        for key, scale in (("factors_with_data", 10.0), ("category_accuracy", 1.0),
                           ("similar_trade_count", 100.0)):
            value = _number(_field(context, key))
            if value is not None:
                scores.append(_bounded(value / scale))
        distance = _number(_field(context, "novelty_distance"))
        if distance is not None:
            scores.append(1.0 if distance <= 0.3 else 0.7 if distance <= 0.6
                          else 0.4 if distance <= 1.0 else 0.1)
        return sum(scores) / len(scores) if scores else None


class OptionsDeltaExposureProvider(FactorEvidenceProvider):
    """Absolute unit-normalized options delta exposure, capped at one."""
    factor_name = "options_delta_exposure"
    dimension_index = 7
    def _compute(self, context):
        delta = _number(_field(context, "delta", "options_delta", "delta_exposure", "net_delta"))
        return None if delta is None else round(_bounded(abs(delta)), 4)


class OptionsIvPercentileProvider(FactorEvidenceProvider):
    """Normalize IV percentile/rank: fractions stay fractions; values above one are percentages."""
    factor_name = "options_iv_percentile"
    dimension_index = 8
    def _compute(self, context):
        value = _number(_field(context, "iv_percentile", "iv_rank", "options_iv_percentile",
                               "implied_volatility_percentile", "implied_volatility_rank"))
        return None if value is None else round(_bounded(value / 100 if value > 1 else value), 4)


class OptionsGammaRiskProvider(FactorEvidenceProvider):
    """Absolute options gamma divided by the existing 0.10 risk scale, capped at one."""
    factor_name = "options_gamma_risk"
    dimension_index = 9
    def _compute(self, context):
        gamma = _number(_field(context, "gamma", "options_gamma", "gamma_risk", "net_gamma"))
        return None if gamma is None else round(_bounded(abs(gamma) / 0.10), 4)


PROVIDER_REGISTRY = {
    "signal_alignment": SignalAlignmentProvider(),
    "market_regime": MarketRegimeProvider(),
    "position_sizing": PositionSizingProvider(),
    "timing_quality": TimingQualityProvider(),
    "risk_reward_actual": RiskRewardActualProvider(),
    "emotional_indicator": EmotionalIndicatorProvider(),
    "signal_confidence": SignalConfidenceProvider(),
    "options_delta_exposure": OptionsDeltaExposureProvider(),
    "options_iv_percentile": OptionsIvPercentileProvider(),
    "options_gamma_risk": OptionsGammaRiskProvider(),
}


class TradingEvidenceProvider:
    """Adapt per-factor reads to the frozen SDK EvidenceProvider protocol."""

    def __init__(self, data_source: Any, decision_id: str, *, attachment: dict[str, Any],
                 fixture_data: Any = None, provider_registry: dict | None = None):
        self.data_source = data_source
        self.decision_id = str(decision_id)
        self.attachment = dict(attachment)
        self.fixture_data = fixture_data
        self.provider_registry = PROVIDER_REGISTRY if provider_registry is None else provider_registry

    def read_evidence(self, decision_id: str, dimension: int, factor_name: str):
        if str(decision_id) != self.decision_id:
            raise ValueError("Evidence provider is bound to a different decision")
        provider = self.provider_registry.get(factor_name)
        if provider is None or provider.dimension_index != dimension:
            raise ValueError("Factor name and dimension must match the canonical registry")
        payload = provider.read_payload(
            self.attachment["lookup_id"], self.data_source,
            fixture_data=self.fixture_data, seed_entity_id=self.attachment["entity_id"],
            decision_id=self.decision_id)
        if payload is None:
            return None
        return {**payload, "decision_attachment": dict(self.attachment),
                "policy_version": POLICY_VERSION}
