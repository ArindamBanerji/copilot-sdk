"""Par level intelligence from QBO order history.

F-26 guardrail: this service expects scraped_external QBO-normalized orders.
It must not be fed K3 demo fixture records.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from math import sqrt
from statistics import NormalDist, mean, pstdev
from typing import Any


@dataclass
class ParRecommendation:
    item_name: str
    category: str
    current_par: float
    recommended_par: float
    avg_daily_usage: float
    usage_std: float
    waste_rate: float
    service_level: float
    weekly_savings_estimate: float
    confidence: str
    seasonal_adjustment: float | None
    data_days: int
    provenance: str


class ParLevelOptimizer:
    """Learn optimal par levels from QBO order history.

    Model: recommended = avg_usage * lead_time + z * usage_std * sqrt(lead_time),
    with conservative safety widening on scarce data and seasonal multipliers.
    """

    def __init__(self, target_service_level: float = 0.95):
        self._target = target_service_level
        self._z = self._z_score(target_service_level)

    def recommend(
        self,
        item_name: str,
        category: str,
        orders: list[dict[str, Any]],
        current_par: float,
        unit_cost: float,
        lead_time_days: float = 2.0,
    ) -> ParRecommendation:
        """Single item recommendation from QBO order history."""

        _assert_no_sample_orders(orders)
        item_orders = self._item_order_history(item_name, orders)
        if not item_orders:
            raise ValueError(f"No QBO order history for item '{item_name}'")

        avg_daily_usage, usage_std = self._compute_usage_stats(item_orders)
        data_days = self._data_days(item_orders)
        confidence = self._confidence(data_days)

        safety_multiplier = 1.5 if confidence == "low" else 1.0
        lead_time = max(float(lead_time_days), 0.0)
        base_usage = avg_daily_usage * lead_time
        safety_stock = self._z * usage_std * sqrt(max(lead_time, 1.0))
        seasonal_multiplier = self._seasonal_multiplier(date.today().month, category)

        recommended = (base_usage + safety_stock * safety_multiplier) * seasonal_multiplier
        recommended = max(recommended, 0.0)

        waste_rate = self._waste_rate(current_par, recommended)
        weekly_savings = self._weekly_savings_estimate(
            current_par=current_par,
            recommended_par=recommended,
            unit_cost=unit_cost,
            waste_rate=waste_rate,
        )

        return ParRecommendation(
            item_name=item_name,
            category=category,
            current_par=round(float(current_par), 2),
            recommended_par=round(recommended, 2),
            avg_daily_usage=round(avg_daily_usage, 2),
            usage_std=round(usage_std, 2),
            waste_rate=round(waste_rate, 3),
            service_level=round(self._target, 3),
            weekly_savings_estimate=round(weekly_savings, 2),
            confidence=confidence,
            seasonal_adjustment=round(seasonal_multiplier, 3)
            if seasonal_multiplier != 1.0
            else None,
            data_days=data_days,
            provenance="scraped_external",
        )

    def recommend_all(
        self, items: list[dict[str, Any]], orders: list[dict[str, Any]]
    ) -> list[ParRecommendation]:
        """All items sorted by weekly savings estimate descending."""

        recommendations: list[ParRecommendation] = []
        for item in items:
            item_name = item.get("item_name") or item.get("name")
            category = item.get("category")
            if not item_name or not category:
                continue

            current_par = _to_float(
                item.get("current_par")
                or item.get("par_level")
                or item.get("currentPar")
                or item.get("avg_order_quantity"),
                default=0.0,
            )
            unit_cost = _to_float(
                item.get("unit_cost") or item.get("unit_price") or item.get("avg_unit_price"),
                default=0.0,
            )
            lead_time_days = _to_float(item.get("lead_time_days"), default=2.0)

            try:
                rec = self.recommend(
                    item_name=str(item_name),
                    category=str(category),
                    orders=orders,
                    current_par=current_par,
                    unit_cost=unit_cost,
                    lead_time_days=lead_time_days,
                )
            except ValueError:
                continue

            if rec.data_days >= 2:
                recommendations.append(rec)

        recommendations.sort(key=lambda rec: rec.weekly_savings_estimate, reverse=True)
        return recommendations

    def _compute_usage_stats(self, item_orders: list[dict[str, Any]]) -> tuple[float, float]:
        """Mean and standard deviation of observed daily usage."""

        by_day: dict[date, float] = defaultdict(float)
        for item_order in item_orders:
            day = _parse_date(item_order.get("date"))
            if day is None:
                continue
            by_day[day] += _to_float(item_order.get("quantity"), default=0.0)

        daily_values = [qty for qty in by_day.values() if qty >= 0]
        if not daily_values:
            return 0.0, 0.0
        if len(daily_values) == 1:
            return daily_values[0], 0.0
        return mean(daily_values), pstdev(daily_values)

    def _seasonal_multiplier(self, month: int, category: str) -> float:
        """Produce rises in summer; protein rises in winter."""

        normalized = category.lower()
        if normalized == "produce" and month in {6, 7, 8}:
            return 1.2
        if normalized == "protein" and month in {12, 1, 2}:
            return 1.15
        return 1.0

    @staticmethod
    def _z_score(service_level: float) -> float:
        """Normal distribution z-score for target service level."""

        return NormalDist().inv_cdf(service_level)

    def _item_order_history(
        self, item_name: str, orders: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        target = item_name.casefold()
        history: list[dict[str, Any]] = []
        for order in orders:
            order_date = order.get("order_date") or order.get("invoice_date") or order.get("date")
            for item in _line_items(order):
                name = item.get("item_name") or item.get("name")
                if not name or str(name).casefold() != target:
                    continue
                history.append(
                    {
                        "date": order_date,
                        "quantity": _to_float(item.get("quantity") or item.get("qty"), 0.0),
                    }
                )
        return history

    def _data_days(self, item_orders: list[dict[str, Any]]) -> int:
        days = sorted(
            day for day in (_parse_date(item.get("date")) for item in item_orders) if day
        )
        if not days:
            return 0
        return (days[-1] - days[0]).days + 1

    def _confidence(self, data_days: int) -> str:
        if data_days < 30:
            return "low"
        if data_days <= 90:
            return "moderate"
        return "high"

    def _waste_rate(self, current_par: float, recommended_par: float) -> float:
        if current_par <= 0 or current_par <= recommended_par:
            return 0.0
        return min((current_par - recommended_par) / current_par, 0.4)

    def _weekly_savings_estimate(
        self,
        current_par: float,
        recommended_par: float,
        unit_cost: float,
        waste_rate: float,
    ) -> float:
        over_par = current_par - recommended_par
        tolerance = max(1.0, current_par * 0.05)
        if over_par <= tolerance:
            return 0.0
        return max(over_par * unit_cost * max(waste_rate, 0.05), 0.0)


def _line_items(order: dict[str, Any]) -> list[dict[str, Any]]:
    items = order.get("items") or order.get("line_items") or []
    return items if isinstance(items, list) else []


def _assert_no_sample_orders(orders: list[dict[str, Any]]) -> None:
    if any(order.get("provenance") == "sample" for order in orders):
        raise ValueError("F-26 VIOLATION: sample records cannot feed par intelligence")


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if not value:
        return None
    text = str(value)
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text[: len(fmt)], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default
