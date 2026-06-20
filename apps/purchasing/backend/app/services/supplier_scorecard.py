"""Supplier scorecards from QBO order history and verified decisions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from statistics import mean
from typing import Any


SCRAPED_EXTERNAL_PROVENANCE = "scraped_external"


@dataclass
class SupplierScorecard:
    supplier_id: str
    supplier_name: str
    tier: str
    overall_score: float
    reliability_pct: float
    price_trend_pct: float
    delivery_performance: float
    exception_rate: float
    decision_count: int
    trend: str
    summary: str
    provenance: str


class SupplierScorecardService:
    """Build supplier scorecards from QBO and verified decision history."""

    provenance_tier = SCRAPED_EXTERNAL_PROVENANCE

    def __init__(
        self,
        orders: list[dict[str, Any]],
        vendors: list[dict[str, Any]],
        verified_decisions: list[dict[str, Any]] | None = None,
    ) -> None:
        _assert_no_sample(orders, "supplier_scorecard")
        _assert_no_sample(vendors, "supplier_scorecard")
        self._orders = list(orders)
        self._vendors = list(vendors)
        self._verified_decisions = list(verified_decisions or [])
        self._vendor_by_id = {
            str(vendor.get("supplier_id") or vendor.get("vendor_id")): vendor
            for vendor in self._vendors
            if vendor.get("supplier_id") or vendor.get("vendor_id")
        }

    def build_scorecard(self, supplier_id: str) -> SupplierScorecard | None:
        """Single supplier. Returns None when there is not enough order history."""

        supplier_orders = [
            order
            for order in self._orders
            if str(order.get("supplier_id") or order.get("vendor_id") or "") == str(supplier_id)
        ]
        if len(supplier_orders) < 5:
            return None

        vendor = self._vendor_by_id.get(str(supplier_id), {})
        supplier_name = str(
            vendor.get("supplier_name")
            or vendor.get("display_name")
            or supplier_orders[0].get("supplier_name")
            or supplier_id
        )
        reliability_pct = _reliability_pct(supplier_orders)
        price_trend_pct = _price_trend_pct(supplier_orders)
        delivery_performance = _delivery_performance(supplier_orders)
        decision_rows = [
            row for row in self._verified_decisions if _decision_supplier_id(row) == str(supplier_id)
        ]
        exception_rate = _exception_rate(decision_rows)
        decision_count = len(decision_rows)

        price_score = _bounded(100.0 - max(price_trend_pct, 0.0) * 4.0, 0.0, 100.0)
        overall_score = _bounded(
            reliability_pct * 0.45
            + price_score * 0.25
            + delivery_performance * 0.20
            + (100.0 - exception_rate) * 0.10,
            0.0,
            100.0,
        )

        card = SupplierScorecard(
            supplier_id=str(supplier_id),
            supplier_name=supplier_name,
            tier=self._compute_tier(overall_score),
            overall_score=round(overall_score, 1),
            reliability_pct=round(reliability_pct, 1),
            price_trend_pct=round(price_trend_pct, 1),
            delivery_performance=round(delivery_performance, 1),
            exception_rate=round(exception_rate, 1),
            decision_count=decision_count,
            trend=self._trend(reliability_pct, price_trend_pct, exception_rate),
            summary="",
            provenance=SCRAPED_EXTERNAL_PROVENANCE,
        )
        card.summary = self._generate_summary(card)
        return card

    def build_all(self, min_orders: int = 5) -> list[SupplierScorecard]:
        """All suppliers sorted by overall score descending."""

        supplier_ids = sorted(
            {
                str(order.get("supplier_id") or order.get("vendor_id"))
                for order in self._orders
                if order.get("supplier_id") or order.get("vendor_id")
            }
        )
        cards: list[SupplierScorecard] = []
        for supplier_id in supplier_ids:
            order_count = sum(
                1
                for order in self._orders
                if str(order.get("supplier_id") or order.get("vendor_id") or "") == supplier_id
            )
            if order_count < min_orders:
                continue
            card = self.build_scorecard(supplier_id)
            if card is not None:
                cards.append(card)
        return sorted(cards, key=lambda card: card.overall_score, reverse=True)

    def _compute_tier(self, score: float) -> str:
        if score > 90:
            return "A"
        if score >= 70:
            return "B"
        return "C"

    def _generate_summary(self, card: SupplierScorecard) -> str:
        trend = f"{card.price_trend_pct:+.1f}%"
        return (
            f"{card.supplier_name}: {card.tier}-tier supplier. "
            f"{card.reliability_pct:.0f}% on-time. "
            f"Price trend {trend}. "
            f"Exceptions {card.exception_rate:.0f}%."
        )

    def _trend(self, reliability_pct: float, price_trend_pct: float, exception_rate: float) -> str:
        if reliability_pct >= 92 and price_trend_pct <= 2 and exception_rate <= 10:
            return "improving"
        if reliability_pct < 80 or price_trend_pct > 8 or exception_rate > 25:
            return "declining"
        return "stable"


def _reliability_pct(orders: list[dict[str, Any]]) -> float:
    comparable = []
    for order in orders:
        expected = _parse_date(order.get("expected_delivery_date"))
        actual = _parse_date(order.get("invoice_date") or order.get("delivery_date") or order.get("order_date"))
        if expected is None or actual is None:
            continue
        comparable.append(actual <= expected)
    if not comparable:
        return 100.0
    return 100.0 * sum(1 for value in comparable if value) / len(comparable)


def _delivery_performance(orders: list[dict[str, Any]]) -> float:
    scores = []
    for order in orders:
        order_date = _parse_date(order.get("purchase_order_date") or order.get("created_date"))
        expected = _parse_date(order.get("expected_delivery_date"))
        actual = _parse_date(order.get("invoice_date") or order.get("delivery_date") or order.get("order_date"))
        if order_date is None or expected is None or actual is None:
            continue
        expected_days = max((expected - order_date).days, 1)
        actual_days = max((actual - order_date).days, 1)
        scores.append(_bounded((expected_days / actual_days) * 100.0, 0.0, 120.0))
    if not scores:
        return 100.0
    return min(mean(scores), 100.0)


def _price_trend_pct(orders: list[dict[str, Any]]) -> float:
    price_points: list[tuple[date, float]] = []
    for order in orders:
        order_date = _parse_date(order.get("invoice_date") or order.get("order_date"))
        if order_date is None:
            continue
        for item in _line_items(order):
            unit_price = _finite_float(item.get("unit_price"), default=None)
            if unit_price is not None and unit_price > 0:
                price_points.append((order_date, unit_price))
    if len(price_points) < 2:
        return 0.0
    price_points.sort(key=lambda point: point[0])
    midpoint = max(1, len(price_points) // 2)
    early = [price for _, price in price_points[:midpoint]]
    recent = [price for _, price in price_points[midpoint:]]
    if not recent:
        recent = early
    baseline = mean(early)
    if baseline <= 0:
        return 0.0
    return ((mean(recent) - baseline) / baseline) * 100.0


def _exception_rate(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    exceptions = 0
    for row in rows:
        if row.get("is_correct") is False:
            exceptions += 1
            continue
        actual = row.get("actual_action")
        recommended = row.get("recommended_action") or row.get("action")
        if actual and recommended and str(actual) != str(recommended):
            exceptions += 1
    return 100.0 * exceptions / len(rows)


def _decision_supplier_id(row: dict[str, Any]) -> str:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    context = row.get("context") if isinstance(row.get("context"), dict) else {}
    outcome_metadata = row.get("outcome_metadata") if isinstance(row.get("outcome_metadata"), dict) else {}
    outcome_context = (
        outcome_metadata.get("context")
        if isinstance(outcome_metadata.get("context"), dict)
        else {}
    )
    return str(
        row.get("supplier_id")
        or metadata.get("supplier_id")
        or context.get("supplier_id")
        or outcome_context.get("supplier_id")
        or ""
    )


def _line_items(order: dict[str, Any]) -> list[dict[str, Any]]:
    items = order.get("items") or order.get("line_items") or []
    return items if isinstance(items, list) else []


def _assert_no_sample(records: list[dict[str, Any]], metric_name: str) -> None:
    sample_count = sum(1 for record in records if record.get("provenance") == "sample")
    if sample_count:
        raise ValueError(
            f"F-26 VIOLATION: {sample_count}/{len(records)} records feeding "
            f"metric '{metric_name}' have provenance='sample'."
        )


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if not value:
        return None
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d").date()
        except ValueError:
            return None


def _finite_float(value: Any, *, default: float | None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bounded(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))
