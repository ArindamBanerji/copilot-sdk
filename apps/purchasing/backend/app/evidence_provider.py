"""Purchasing-specific evidence provider for VLD investigation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
except ModuleNotFoundError:  # pragma: no cover - import path varies by caller cwd
    from copilot_sdk.scoring.presets.purchasing import PurchasingPreset


FACTOR_NAMES = tuple(PurchasingPreset().shape.factor_names)


class PurchasingEvidenceProvider:
    """Read Purchasing order, supplier, inventory, and cost evidence."""

    def __init__(self, data_source: dict[str, Any] | str | Path | None = None, order_id: str | None = None) -> None:
        self.data = load_purchasing_vld_data(data_source)
        self.order_id = str(order_id or "")

    def read_evidence(
        self,
        decision_id: str,
        dimension: int,
        factor_name: str,
    ) -> dict[str, Any] | None:
        order_id = str(decision_id or self.order_id)
        order = self._order(order_id)
        if order is None:
            return None
        factor = self._canonical_factor(factor_name)
        readers = {
            "expected_demand": self._demand_evidence,
            "day_of_week": self._day_evidence,
            "weather_forecast": self._weather_evidence,
            "event_flag": self._event_evidence,
            "historical_waste": self._vendor_quality_evidence,
            "supplier_lead_time": self._lead_time_evidence,
            "price_memory_index": self._substitution_or_price_evidence,
        }
        reader = readers.get(factor)
        return None if reader is None else reader(order)

    def _order(self, order_id: str) -> dict[str, Any] | None:
        orders = self.data.get("orders", {})
        if isinstance(orders, dict):
            order = orders.get(order_id)
            return order if isinstance(order, dict) else None
        if isinstance(orders, list):
            for order in orders:
                if isinstance(order, dict) and str(order.get("order_id")) == order_id:
                    return order
        return None

    def _supplier(self, order: dict[str, Any]) -> dict[str, Any]:
        supplier_id = str(order.get("supplier_id") or order.get("vendor_id") or "")
        suppliers = self.data.get("suppliers", {})
        if isinstance(suppliers, dict):
            supplier = suppliers.get(supplier_id)
            return supplier if isinstance(supplier, dict) else {}
        if isinstance(suppliers, list):
            for supplier in suppliers:
                if isinstance(supplier, dict) and str(supplier.get("supplier_id") or supplier.get("vendor_id")) == supplier_id:
                    return supplier
        return {}

    def _demand_evidence(self, order: dict[str, Any]) -> dict[str, Any] | None:
        demand = order.get("demand")
        if not isinstance(demand, dict):
            factors = order.get("factors")
            if isinstance(factors, dict) and "expected_demand" in factors:
                return {
                    "value": _bounded(factors["expected_demand"]),
                    "confidence": 0.70,
                    "source": "demand_forecast",
                }
            return None
        return {
            "value": _bounded(demand.get("urgency_score", demand.get("forecast_pressure"))),
            "confidence": _bounded(demand.get("confidence", 0.82)),
            "source": "demand_forecast",
            "forecast_units": demand.get("forecast_units"),
            "inventory_units": demand.get("inventory_units"),
            "safety_stock_units": demand.get("safety_stock_units"),
        }

    def _day_evidence(self, order: dict[str, Any]) -> dict[str, Any] | None:
        schedule = order.get("schedule")
        if isinstance(schedule, dict):
            return {
                "value": _bounded(schedule.get("day_factor", schedule.get("day_of_week"))),
                "confidence": _bounded(schedule.get("confidence", 0.75)),
                "source": "calendar",
            }
        return _factor_override(order, "day_of_week", "calendar")

    def _weather_evidence(self, order: dict[str, Any]) -> dict[str, Any] | None:
        weather = order.get("weather")
        if isinstance(weather, dict):
            return {
                "value": _bounded(weather.get("forecast_factor", weather.get("value"))),
                "confidence": _bounded(weather.get("confidence", 0.72)),
                "source": "weather_service",
            }
        return _factor_override(order, "weather_forecast", "weather_service")

    def _event_evidence(self, order: dict[str, Any]) -> dict[str, Any] | None:
        event = order.get("event")
        if isinstance(event, dict):
            return {
                "value": _bounded(event.get("event_factor", event.get("value"))),
                "confidence": _bounded(event.get("confidence", 0.78)),
                "source": "event_calendar",
            }
        return _factor_override(order, "event_flag", "event_calendar")

    def _vendor_quality_evidence(self, order: dict[str, Any]) -> dict[str, Any] | None:
        vendor = self._supplier(order)
        quality = order.get("vendor_quality")
        if not isinstance(quality, dict):
            quality = vendor.get("quality") if isinstance(vendor.get("quality"), dict) else {}
        if not isinstance(quality, dict) or not quality:
            return _factor_override(order, "historical_waste", "vendor_tracker")
        reliability = quality.get("reliability_score")
        risk = quality.get("risk_score")
        value = risk if risk is not None else 1.0 - _bounded(reliability, default=0.5)
        return {
            "value": _bounded(value),
            "confidence": _bounded(quality.get("confidence", 0.84)),
            "source": "vendor_tracker",
            "reliability_score": _bounded(reliability, default=1.0 - _bounded(value)),
            "quality_incidents_30d": quality.get("quality_incidents_30d", 0),
            "notes": quality.get("notes"),
        }

    def _lead_time_evidence(self, order: dict[str, Any]) -> dict[str, Any] | None:
        supplier = self._supplier(order)
        lead_time = order.get("lead_time")
        if not isinstance(lead_time, dict):
            lead_time = supplier.get("lead_time") if isinstance(supplier.get("lead_time"), dict) else {}
        if not isinstance(lead_time, dict) or not lead_time:
            return _factor_override(order, "supplier_lead_time", "lead_time_tracker")
        value = lead_time.get("risk_score")
        if value is None and lead_time.get("current_days") is not None:
            baseline = max(float(lead_time.get("baseline_days") or 1.0), 1.0)
            value = min(float(lead_time["current_days"]) / (baseline * 2.0), 1.0)
        return {
            "value": _bounded(value),
            "confidence": _bounded(lead_time.get("confidence", 0.85)),
            "source": "lead_time_tracker",
            "current_days": lead_time.get("current_days"),
            "baseline_days": lead_time.get("baseline_days"),
            "backlog_days": lead_time.get("backlog_days"),
            "stretch_pct": lead_time.get("stretch_pct"),
        }

    def _substitution_or_price_evidence(self, order: dict[str, Any]) -> dict[str, Any] | None:
        substitution = order.get("substitution")
        if isinstance(substitution, dict) and substitution:
            return {
                "value": _bounded(substitution.get("score", substitution.get("value"))),
                "confidence": _bounded(substitution.get("confidence", 0.80)),
                "source": "vendor_catalog",
                "alternate_vendor": substitution.get("alternate_vendor"),
                "alternate_lead_days": substitution.get("alternate_lead_days"),
                "premium_pct": substitution.get("premium_pct"),
            }
        benchmark = order.get("cost_benchmark")
        if isinstance(benchmark, dict) and benchmark:
            return {
                "value": _bounded(benchmark.get("price_memory_index", benchmark.get("value"))),
                "confidence": _bounded(benchmark.get("confidence", 0.76)),
                "source": "cost_benchmark",
                "benchmark_unit_cost": benchmark.get("benchmark_unit_cost"),
                "quoted_unit_cost": benchmark.get("quoted_unit_cost"),
            }
        return _factor_override(order, "price_memory_index", "cost_benchmark")

    def _canonical_factor(self, factor_name: str) -> str:
        aliases = {
            "vendor_reliability": "historical_waste",
            "supplier_reliability": "historical_waste",
            "demand_urgency": "expected_demand",
            "cost_benchmark": "price_memory_index",
            "inventory_level": "expected_demand",
            "lead_time": "supplier_lead_time",
            "substitution_available": "price_memory_index",
            "substitution": "price_memory_index",
        }
        return aliases.get(str(factor_name), str(factor_name))


def load_purchasing_vld_data(data_source: dict[str, Any] | str | Path | None = None) -> dict[str, Any]:
    if isinstance(data_source, dict):
        return data_source
    data: dict[str, Any] = {"orders": {}, "suppliers": {}}
    if data_source is None:
        return data
    base = Path(data_source)
    if base.is_file():
        payload = json.loads(base.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else data
    if not base.exists():
        return data
    for filename, key in (
        ("purchasing_orders.json", "orders"),
        ("purchasing_suppliers.json", "suppliers"),
    ):
        path = base / filename
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        data[key] = payload
    return data


def _factor_override(order: dict[str, Any], factor_name: str, source: str) -> dict[str, Any] | None:
    factors = order.get("factors")
    if isinstance(factors, dict) and factor_name in factors:
        return {"value": _bounded(factors[factor_name]), "confidence": 0.65, "source": source}
    return None


def _bounded(value: Any, default: float = 0.5) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = float(default)
    return max(0.0, min(1.0, numeric))


__all__ = ["FACTOR_NAMES", "PurchasingEvidenceProvider", "load_purchasing_vld_data"]
