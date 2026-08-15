"""Aggregated purchasing alerts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.services.delivery_coordinator import DeliveryCoordinator
from app.services.menu_engineer import MenuEngineer
from app.services.par_optimizer import ParLevelOptimizer
from app.services.supplier_signal_publisher import SupplierSignalPublisher
from app.services.supplier_scorecard import SupplierScorecardService
from app.services.waste_tracker import WasteTracker


ALERT_TYPES = [
    "price_spike",
    "supplier_degradation",
    "waste_threshold",
    "stockout_risk",
    "conservation_amber",
    "delivery_conflict",
    "margin_erosion",
]


@dataclass
class PurchasingAlert:
    alert_type: str
    severity: str
    title: str
    recommendation: str
    scenario: str
    provenance: str = "demo"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PurchasingAlertEngine:
    """Aggregate checks from existing Purchasing services."""

    def __init__(
        self,
        waste_tracker_cls: type[WasteTracker] = WasteTracker,
        menu_engineer: MenuEngineer | None = None,
        par_optimizer: ParLevelOptimizer | None = None,
        delivery: DeliveryCoordinator | None = None,
        scorecard_service: Any | None = None,
        signal_publisher: SupplierSignalPublisher | None = None,
    ) -> None:
        self.waste_tracker_cls = waste_tracker_cls
        self.menu_engineer = menu_engineer or MenuEngineer()
        self.par_optimizer = par_optimizer or ParLevelOptimizer()
        self.delivery = delivery or DeliveryCoordinator()
        self.scorecard_service = scorecard_service
        self.signal_publisher = signal_publisher

    def evaluate(
        self,
        orders: list[dict[str, Any]] | None = None,
        suppliers: list[dict[str, Any]] | None = None,
        decisions: list[dict[str, Any]] | None = None,
        conservation_status: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        order_rows = demo_orders() if orders is None else orders
        supplier_rows = demo_suppliers() if suppliers is None else suppliers
        rows = []
        rows.extend(self._price_spikes(order_rows))
        rows.extend(self._supplier_degradation(supplier_rows))
        rows.extend(self._waste_alerts(order_rows))
        rows.extend(self._stockout_risk(order_rows))
        rows.extend(self._conservation(conservation_status))
        rows.extend(self._delivery_conflicts())
        rows.extend(self._margin_alerts())
        unique = _dedupe(rows)
        unique.sort(key=lambda item: {"critical": 0, "warning": 1, "info": 2}.get(item.severity, 9))
        return [item.to_dict() for item in unique]

    def _default_rules(self) -> list[str]:
        return list(ALERT_TYPES)

    def _price_spikes(self, orders: list[dict[str, Any]]) -> list[PurchasingAlert]:
        alerts = []
        for order in orders:
            item = str(order.get("item") or "salmon")
            current = float(order.get("current_price") or 0)
            average = float(order.get("average_price") or current or 1)
            if average > 0 and (current - average) / average >= 0.15:
                pct = round(((current - average) / average) * 100)
                alerts.append(PurchasingAlert("price_spike", "warning", f"Price alert: {item} up {pct}% from 30-day average", "Check the last quoted rate before approving.", "I2"))
        return alerts

    def _supplier_degradation(self, suppliers: list[dict[str, Any]]) -> list[PurchasingAlert]:
        alerts = []
        service = self.scorecard_service
        if service is None:
            service = SupplierScorecardService(
                _supplier_scorecard_orders(suppliers),
                _supplier_scorecard_vendors(suppliers),
                verified_decisions=[],
            )
        try:
            scorecards = service.build_all(min_orders=1)
        except Exception:
            scorecards = []
        for card in scorecards:
            reliability = float(getattr(card, "reliability_pct", 100.0))
            trend = str(getattr(card, "trend", "")).lower()
            if trend == "declining" or reliability < 80.0:
                name = str(getattr(card, "supplier_name", "Supplier"))
                if self.signal_publisher is not None:
                    self.signal_publisher.check_and_publish(card)
                alerts.append(PurchasingAlert("supplier_degradation", "critical", f"{name} reliability is slipping", f"Now {round(reliability)}% on-time. Confirm backup supplier before service.", "P7"))
        return alerts

    def _waste_alerts(self, orders: list[dict[str, Any]]) -> list[PurchasingAlert]:
        alerts = []
        tracker = self.waste_tracker_cls(orders)
        for profile in tracker.analyze_all():
            waste = float(getattr(profile, "average_waste_pct", 0))
            benchmark = float(getattr(profile, "benchmark_pct", 0.01) or 0.01)
            if waste >= benchmark * 1.5:
                item = str(getattr(profile, "item", "Item"))
                alerts.append(PurchasingAlert("waste_threshold", "warning", f"{item} waste is above the kitchen benchmark", "Use pre-portioned prep or lower slow-day par.", "F3"))
        return alerts

    def _stockout_risk(self, orders: list[dict[str, Any]]) -> list[PurchasingAlert]:
        alerts = []
        try:
            recommendations = self.par_optimizer.recommend_all(_par_items_from_orders(orders), orders)
        except Exception:
            recommendations = []
        for rec in recommendations:
            current = float(getattr(rec, "current_par", 0.0) or 0.0)
            recommended = float(getattr(rec, "recommended_par", 0.0) or 0.0)
            if recommended > 0 and current / recommended < 0.3:
                item = str(getattr(rec, "item_name", "item"))
                alerts.append(PurchasingAlert("stockout_risk", "critical", f"Low stock alert: {item} is below 30% of par", "Order before the next service window.", "P3"))
        return alerts

    def _conservation(self, status: dict[str, Any] | str | None) -> list[PurchasingAlert]:
        if status is None:
            state = "UNKNOWN"
            category = "this category"
        elif isinstance(status, str):
            state = status
            category = "this category"
        else:
            state = str(status.get("state") or status.get("status") or "")
            category = str(status.get("category") or "this category")
        if state.upper() == "GREEN":
            return []
        return [PurchasingAlert("conservation_amber", "warning", f"System paused auto-ordering for {category}", "Keep manager review on until learning turns GREEN.", "P3")]

    def _delivery_conflicts(self) -> list[PurchasingAlert]:
        schedule = self.delivery.schedule_day("2026-06-24")
        if len(schedule.get("deliveries", [])) < 4:
            return []
        return [PurchasingAlert("delivery_conflict", "info", "4 deliveries on Wednesday", "Combine receiving slots where suppliers overlap.", "M2")]

    def _margin_alerts(self) -> list[PurchasingAlert]:
        alerts = self.menu_engineer.margin_alerts(self.menu_engineer.analyze(_demo_menu()))
        return [
            PurchasingAlert("margin_erosion", "warning", str(alert.get("message") or "Menu cost alert"), "Review supplier price or menu placement.", "P7")
            for alert in alerts
        ]


def demo_orders() -> list[dict[str, Any]]:
    return [
        {"item": "salmon", "current_price": 7.20, "average_price": 6.00, "par_pct": 0.2, "category": "protein", "quantity": 40, "unit_cost": 7.20, "waste_pct": 0.22},
        {"item": "salmon", "category": "protein", "quantity": 38, "unit_cost": 7.20, "waste_pct": 0.20},
        {"item": "salmon", "category": "protein", "quantity": 42, "unit_cost": 7.20, "waste_pct": 0.21},
        {"item": "salmon", "category": "protein", "quantity": 41, "unit_cost": 7.20, "waste_pct": 0.24},
        {"item": "salmon", "category": "protein", "quantity": 39, "unit_cost": 7.20, "waste_pct": 0.22},
        {"item": "romaine", "current_price": 2.10, "average_price": 2.00, "par_pct": 0.8, "category": "produce", "quantity": 20, "unit_cost": 2.10},
    ]


def demo_suppliers() -> list[dict[str, Any]]:
    return [{"name": "Sysco", "previous_otif": 0.93, "current_otif": 0.74}]


def _demo_menu() -> list[dict[str, Any]]:
    return [
        {"name": "Salmon entree", "price": 25, "food_cost": 9, "previous_food_cost_pct": 0.28, "orders": 80},
        {"name": "Pasta", "price": 18, "food_cost": 5, "previous_food_cost_pct": 0.27, "orders": 40},
    ]


def _par_items_from_orders(orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    seen = set()
    for order in orders:
        item_name = order.get("item_name") or order.get("item") or order.get("name")
        category = order.get("category")
        if not item_name or not category:
            continue
        key = (str(item_name), str(category))
        if key in seen:
            continue
        seen.add(key)
        items.append({
            "item_name": str(item_name),
            "category": str(category),
            "current_par": order.get("current_par") or order.get("par_level") or order.get("par_pct") or 0,
            "unit_cost": order.get("unit_cost") or order.get("current_price") or 1,
        })
    return items


def _supplier_scorecard_vendors(suppliers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    vendors = []
    for index, supplier in enumerate(suppliers):
        supplier_id = str(supplier.get("supplier_id") or supplier.get("vendor_id") or f"supplier-{index}")
        vendors.append({
            "supplier_id": supplier_id,
            "display_name": str(supplier.get("name") or supplier.get("supplier_name") or supplier_id),
        })
    return vendors


def _supplier_scorecard_orders(suppliers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, supplier in enumerate(suppliers):
        supplier_id = str(supplier.get("supplier_id") or supplier.get("vendor_id") or f"supplier-{index}")
        name = str(supplier.get("name") or supplier.get("supplier_name") or supplier_id)
        current = float(supplier.get("current_otif") or supplier.get("reliability") or 1.0)
        on_time_count = max(0, min(5, int(current * 5)))
        for offset in range(5):
            rows.append({
                "supplier_id": supplier_id,
                "supplier_name": name,
                "purchase_order_date": f"2026-06-{10 + offset:02d}",
                "expected_delivery_date": f"2026-06-{12 + offset:02d}",
                "delivery_date": f"2026-06-{12 + offset:02d}" if offset < on_time_count else f"2026-06-{14 + offset:02d}",
                "line_items": [{"unit_price": supplier.get("unit_price") or 1.0}],
                "provenance": "scraped_external",
            })
    return rows


def _dedupe(alerts: list[PurchasingAlert]) -> list[PurchasingAlert]:
    seen = set()
    unique = []
    for alert in alerts:
        key = (alert.alert_type, alert.title)
        if key in seen:
            continue
        seen.add(key)
        unique.append(alert)
    return unique
