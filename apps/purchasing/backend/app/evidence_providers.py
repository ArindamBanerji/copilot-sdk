"""Tier 5D purchasing evidence from domain records and explicit fixture data.

Computed values use the established factor conventions. Missing inputs produce
a labeled neutral fallback; fixture records retain their sample provenance.
"""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

from app.evidence_provider import PurchasingEvidenceProvider as LegacyEvidenceProvider

FACTOR_NAMES = ["expected_demand","day_of_week","weather_forecast","event_flag","historical_waste","supplier_lead_time","price_memory_index"]
POLICY_VERSION = "tier5d-purchasing-providers-v1"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
LOGGER = logging.getLogger(__name__)

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
    suppliers = {}
    fixture_match = False
    from_file = False
    if isinstance(source, dict):
        context = _record(source.get("orders", source), entity_id, "order_id")
        suppliers = source.get("suppliers", {})
        if not context and any(key in source for key in ("waste_pct", "lead_time_days", "price_change_count")):
            context = dict(source)
        fixture_match = bool(context) and fixture_data is not None
    if not context:
        reader = getattr(data_source, "get_vld_context", None)
        getter = getattr(data_source, "get_decision", None)
        try:
            if callable(reader):
                context = reader(entity_id) or {}
            elif callable(getter):
                context = getter(decision_id or entity_id, "purchasing") or {}
        except Exception as exc:
            LOGGER.warning("Purchasing domain context read failed for %s: %s", entity_id, exc)
            return None
    if not isinstance(context, dict):
        return {}, False, True
    if not fixture_match and not isinstance(data_source, dict):
        root = Path(source) if isinstance(source, (str, Path)) else DATA_DIR
        if root.is_file():
            data = _json_data(root)
            rows = data.get("orders", {}) if isinstance(data, dict) else data
            local = _record(rows, entity_id, "order_id")
            suppliers = data.get("suppliers", {}) if isinstance(data, dict) else {}
        else:
            rows = _json_data(root / "order_metadata.json")
            local = (_record(rows, entity_id, "order_id")
                     or _record(rows, decision_id or entity_id, "order_id"))
            if not local:
                local = _record(_json_data(root / "purchasing_orders.json"), entity_id, "order_id")
            suppliers = _json_data(root / "purchasing_suppliers.json")
        from_file = bool(local)
        context = {**local, **_flatten(context)}
    context = _flatten(context)
    supplier = _record(suppliers, str(context.get("supplier_id", "")), "supplier_id")
    # Preserve order-specific values and do not read a future order outcome.
    for key in ("lead_time_days", "lead_time", "price_change_count", "months_tracked", "monthly_unit_prices"):
        if key not in context and key in supplier:
            context[key] = supplier[key]
    sample = fixture_match or from_file or context.get("provenance") in {"sample", "synthetic"}
    return context, sample, True


def _fixture_read(entity_id, dimension, factor_name, source):
    source = source if isinstance(source, (dict, str, Path)) else None
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
        source: object
        if self.dimension_index >= 4:
            context_result = _domain_context(entity_id, data_source, fixture_data, decision_id)
            if context_result is None:
                context, sample, context_available = {}, False, False
            else:
                context, sample, context_available = context_result
            try:
                computed = self._compute(context)
            except (TypeError, ValueError, OverflowError, ZeroDivisionError):
                computed = None
            missing = _number(computed) is None
            tier = "MISSING_DATA" if missing else "SYNTHETIC" if sample else "DOMAIN_DATA"
            source = ("MISSING_DATA:neutral:" if missing else "SYNTHETIC:fixture:" if sample else "computed:")
            result = {"value": _bounded(computed), "confidence": 0.0 if missing else 1.0,
                    "source": source + self.factor_name,
                    "evidence_tier": tier, "missing_data": missing,
                    "input_entity_id": entity_id}
            if not context_available:
                result.update(
                    data_available=False,
                    degraded=True,
                    failure_reason="Purchasing domain context unavailable",
                )
            return result
        payload = None
        graph_read = False
        reader = getattr(data_source, "get_vld_evidence", None)
        if callable(reader):
            payload = _valid_payload(reader(entity_id, self.dimension_index, self.factor_name))
            graph_read = payload is not None
        source = fixture_data if fixture_data is not None else data_source
        if callable(reader) and fixture_data is None and not isinstance(source, dict):
            source = None
        if payload is None:
            payload = _valid_payload(_fixture_read(entity_id, self.dimension_index, self.factor_name, source))
        if payload is not None and not graph_read and (fixture_data is not None or isinstance(source, dict)):
            payload = {**payload, "source": "SYNTHETIC:fixture:" + str(payload.get("source", "fixture")),
                       "evidence_tier": "SYNTHETIC"}
        return payload

    def read(self, entity_id: str, data_source: Any = None, **kwargs: Any) -> float | None:
        payload = self.read_payload(entity_id, data_source, **kwargs)
        return None if payload is None else float(payload["value"])


class ExpectedDemandProvider(FactorEvidenceProvider):
    factor_name = "expected_demand"
    dimension_index = 0


class DayOfWeekProvider(FactorEvidenceProvider):
    factor_name = "day_of_week"
    dimension_index = 1


class WeatherForecastProvider(FactorEvidenceProvider):
    factor_name = "weather_forecast"
    dimension_index = 2


class EventFlagProvider(FactorEvidenceProvider):
    factor_name = "event_flag"
    dimension_index = 3


class HistoricalWasteProvider(FactorEvidenceProvider):
    """Waste pressure: observed waste fraction divided by the existing 20% ceiling."""
    factor_name = "historical_waste"
    dimension_index = 4
    def _compute(self, context):
        waste = _number(_field(context, "waste_pct", "waste_rate"))
        if waste is None:
            wasted = _number(context.get("waste_units"))
            received = _number(context.get("received_units"))
            if wasted is None or received is None or received <= 0:
                return None
            waste = wasted / received
        return _bounded(waste / 0.20)


class SupplierLeadTimeProvider(FactorEvidenceProvider):
    """Delivery speed: 1 - lead_time_days / 7, matching the Purchasing factor convention."""
    factor_name = "supplier_lead_time"
    dimension_index = 5
    def _compute(self, context):
        days = _number(_field(context, "lead_time_days"))
        if days is None:
            lead_time = context.get("lead_time")
            if isinstance(lead_time, dict):
                days = _number(lead_time.get("current_days"))
        return None if days is None else _bounded(1.0 - days / 7.0)


class PriceMemoryIndexProvider(FactorEvidenceProvider):
    """Price stability: one minus price changes per tracked month, bounded to [0,1]."""
    factor_name = "price_memory_index"
    dimension_index = 6
    def _compute(self, context):
        changes = _number(_field(context, "price_change_count"))
        months = _number(_field(context, "months_tracked"))
        history = context.get("monthly_unit_prices")
        if (changes is None or months is None) and isinstance(history, list) and len(history) >= 2:
            prices = [_number(value) for value in history]
            if any(value is None or value < 0 for value in prices):
                return None
            changes = float(sum(a != b for a, b in zip(prices, prices[1:])))
            months = float(len(prices) - 1)
        if changes is None or months is None or months <= 0:
            return None
        return _bounded(1.0 - changes / months)


PROVIDER_REGISTRY = {
    "expected_demand": ExpectedDemandProvider(),
    "day_of_week": DayOfWeekProvider(),
    "weather_forecast": WeatherForecastProvider(),
    "event_flag": EventFlagProvider(),
    "historical_waste": HistoricalWasteProvider(),
    "supplier_lead_time": SupplierLeadTimeProvider(),
    "price_memory_index": PriceMemoryIndexProvider(),
}


class PurchasingEvidenceProvider:
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
