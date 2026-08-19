"""Domain-specific regime policies built on the shared detector protocol."""

from __future__ import annotations

from typing import Any, Mapping

from copilot_sdk.regime.policy import RegimePolicy, _finite


def _value(indicators: Mapping[str, Any], *names: str) -> float | None:
    for name in names:
        result = _finite(indicators.get(name))
        if result is not None:
            return result
    return None


def _confidence(distance: float, scale: float = 1.0) -> float:
    return min(1.0, max(0.05, abs(distance) / scale))


class S2PRegimePolicy(RegimePolicy):
    """Supplier delivery policy: normal, disrupted, or seasonal."""

    regime_names = ("normal", "disrupted", "seasonal", "unknown")
    indicator_names = ("otif", "lead_time", "exception_rate", "seasonality")

    def __init__(self, thresholds: Mapping[str, float] | None = None, **kwargs: Any) -> None:
        values = {
            "disrupted_otif": 0.80,
            "disrupted_lead_time": 14.0,
            "disrupted_exception_rate": 0.25,
            "seasonal_score": 0.60,
        }
        values.update(thresholds or {})
        super().__init__(thresholds=values, **kwargs)

    def classify(self, indicators: Mapping[str, Any]) -> tuple[str, float, dict[str, float]]:
        otif = _value(indicators, "otif", "otif_rate")
        lead_time = _value(indicators, "lead_time", "average_lead_time")
        exception_rate = _value(indicators, "exception_rate", "supplier_exception_rate")
        seasonality = _value(indicators, "seasonality", "seasonality_score")
        output = {key: value for key, value in {
            "otif": otif, "lead_time": lead_time,
            "exception_rate": exception_rate, "seasonality": seasonality,
        }.items() if value is not None}
        if not output:
            return "unknown", 0.0, {}
        disrupted = (
            (otif is not None and otif <= self.threshold("disrupted_otif", 0.80))
            or (lead_time is not None and lead_time >= self.threshold("disrupted_lead_time", 14.0))
            or (exception_rate is not None and exception_rate >= self.threshold("disrupted_exception_rate", 0.25))
        )
        if disrupted:
            distances = [
                self.threshold("disrupted_otif", 0.80) - otif if otif is not None else 0.0,
                lead_time - self.threshold("disrupted_lead_time", 14.0) if lead_time is not None else 0.0,
                exception_rate - self.threshold("disrupted_exception_rate", 0.25) if exception_rate is not None else 0.0,
            ]
            return "disrupted", _confidence(max(distances), 0.25), output
        if seasonality is not None and seasonality >= self.threshold("seasonal_score", 0.60):
            return "seasonal", _confidence(seasonality - self.threshold("seasonal_score", 0.60), 0.40), output
        return "normal", 0.95, output


class DataOpsRegimePolicy(RegimePolicy):
    """Pipeline health policy: stable, degraded, or disrupted."""

    regime_names = ("stable", "degraded", "disrupted", "unknown")
    indicator_names = ("pipeline_success_rate", "alert_volume", "failure_rate", "latency_p95")

    def __init__(self, thresholds: Mapping[str, float] | None = None, **kwargs: Any) -> None:
        values = {
            "degraded_success_rate": 0.90,
            "disrupted_success_rate": 0.70,
            "degraded_alert_volume": 20.0,
            "disrupted_alert_volume": 50.0,
            "degraded_failure_rate": 0.10,
            "disrupted_failure_rate": 0.30,
        }
        values.update(thresholds or {})
        super().__init__(thresholds=values, **kwargs)

    def classify(self, indicators: Mapping[str, Any]) -> tuple[str, float, dict[str, float]]:
        success = _value(indicators, "pipeline_success_rate", "success_rate", "pipeline_success")
        alerts = _value(indicators, "alert_volume", "alerts")
        failure = _value(indicators, "failure_rate")
        latency = _value(indicators, "latency_p95")
        output = {key: value for key, value in {
            "pipeline_success_rate": success, "alert_volume": alerts,
            "failure_rate": failure, "latency_p95": latency,
        }.items() if value is not None}
        if not output:
            return "unknown", 0.0, {}
        disrupted = (
            (success is not None and success < self.threshold("disrupted_success_rate", 0.70))
            or (alerts is not None and alerts >= self.threshold("disrupted_alert_volume", 50.0))
            or (failure is not None and failure >= self.threshold("disrupted_failure_rate", 0.30))
        )
        degraded = (
            (success is not None and success < self.threshold("degraded_success_rate", 0.90))
            or (alerts is not None and alerts >= self.threshold("degraded_alert_volume", 20.0))
            or (failure is not None and failure >= self.threshold("degraded_failure_rate", 0.10))
        )
        if disrupted:
            return "disrupted", _confidence(max(
                self.threshold("disrupted_success_rate", 0.70) - (success or 0.0),
                (alerts or 0.0) - self.threshold("disrupted_alert_volume", 50.0),
                (failure or 0.0) - self.threshold("disrupted_failure_rate", 0.30),
            ), 1.0), output
        if degraded:
            return "degraded", 0.70, output
        return "stable", 0.95, output


class PurchasingRegimePolicy(RegimePolicy):
    """Demand/supply policy: balanced, shortage, surplus, or seasonal."""

    regime_names = ("balanced", "shortage", "surplus", "seasonal", "unknown")
    indicator_names = ("demand_variance", "stock_days", "supply_fill_rate", "seasonality")

    def __init__(self, thresholds: Mapping[str, float] | None = None, **kwargs: Any) -> None:
        values = {
            "shortage_stock_days": 7.0,
            "surplus_stock_days": 30.0,
            "shortage_fill_rate": 0.80,
            "seasonal_score": 0.60,
        }
        values.update(thresholds or {})
        super().__init__(thresholds=values, **kwargs)

    def classify(self, indicators: Mapping[str, Any]) -> tuple[str, float, dict[str, float]]:
        demand_variance = _value(indicators, "demand_variance")
        stock_days = _value(indicators, "stock_days", "inventory_days")
        fill_rate = _value(indicators, "supply_fill_rate", "fill_rate")
        seasonality = _value(indicators, "seasonality", "seasonality_score")
        output = {key: value for key, value in {
            "demand_variance": demand_variance, "stock_days": stock_days,
            "supply_fill_rate": fill_rate, "seasonality": seasonality,
        }.items() if value is not None}
        if not output:
            return "unknown", 0.0, {}
        shortage = (
            (stock_days is not None and stock_days < self.threshold("shortage_stock_days", 7.0))
            or (fill_rate is not None and fill_rate < self.threshold("shortage_fill_rate", 0.80))
        )
        if shortage:
            return "shortage", 0.90, output
        if stock_days is not None and stock_days > self.threshold("surplus_stock_days", 30.0):
            return "surplus", 0.90, output
        if seasonality is not None and seasonality >= self.threshold("seasonal_score", 0.60):
            return "seasonal", _confidence(seasonality - self.threshold("seasonal_score", 0.60), 0.40), output
        return "balanced", 0.95, output
