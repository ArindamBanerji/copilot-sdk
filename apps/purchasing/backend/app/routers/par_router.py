"""Par intelligence API sourced from QBO order history."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.connectors.mock_qbo import MockQBOConnector
from app.data_helpers import is_sample_data
from app.routers.spend_router import qbo_bills_for_spend
from app.services.par_optimizer import ParLevelOptimizer

CATEGORIES = ["protein", "produce", "dairy", "dry_goods", "beverages"]
SCRAPED_EXTERNAL_PROVENANCE = "scraped_external"


def create_par_router(
    optimizer: ParLevelOptimizer | None = None,
    connector: MockQBOConnector | None = None,
) -> APIRouter:
    optimizer = optimizer or ParLevelOptimizer()
    connector = connector or MockQBOConnector()
    router = APIRouter(prefix="/api/purchasing/par", tags=["par"])

    def _orders() -> list[dict[str, Any]]:
        """QBO-only order history. If QBO is unavailable, return no pars."""

        try:
            orders = qbo_bills_for_spend(connector)
        except Exception:
            return []

        return [order for order in orders if not is_sample_data(order)]

    def _recommendations(
        category: str | None = None, service_level: float = 0.95
    ) -> list[dict[str, Any]]:
        if category and category not in CATEGORIES:
            raise HTTPException(status_code=404, detail=f"Unknown category: {category}")

        orders = _orders()
        if not orders:
            return []

        active_optimizer = (
            optimizer
            if abs(getattr(optimizer, "_target", service_level) - service_level) < 0.0001
            else ParLevelOptimizer(target_service_level=service_level)
        )
        items = _items_from_orders(orders, category=category)
        recommendations: list[dict[str, Any]] = []
        for rec in active_optimizer.recommend_all(items, orders):
            row = asdict(rec)
            metadata = dict(row.get("decision_metadata") or {})
            metadata["par_shown"] = True
            row["decision_metadata"] = metadata
            row["par_shown"] = True
            recommendations.append(row)
        return recommendations

    @router.get("/recommendations")
    def get_recommendations(
        category: str | None = Query(default=None),
        service_level: float = Query(default=0.95, ge=0.5, le=0.999),
    ) -> list[dict[str, Any]]:
        return _recommendations(category=category, service_level=service_level)

    @router.get("/recommendations/{category}")
    def get_category_recommendations(
        category: str,
        service_level: float = Query(default=0.95, ge=0.5, le=0.999),
    ) -> list[dict[str, Any]]:
        return _recommendations(category=category, service_level=service_level)

    @router.get("/status")
    def get_status() -> dict[str, Any]:
        orders = _orders()
        items = _items_from_orders(orders)
        categories = sorted({item["category"] for item in items})
        return {
            "total_items": len(items),
            "categories": categories,
            "data_source": "quickbooks_online",
            "provenance_tier": SCRAPED_EXTERNAL_PROVENANCE if orders else "sample",
        }

    return router


def _items_from_orders(
    orders: list[dict[str, Any]], category: str | None = None
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for order in orders:
        for item in _line_items(order):
            name = item.get("item_name") or item.get("name")
            item_category = item.get("category") or order.get("category")
            if not name or not item_category:
                continue
            if category and item_category != category:
                continue

            key = str(name).casefold()
            entry = grouped.setdefault(
                key,
                {
                    "item_name": str(name),
                    "category": str(item_category),
                    "quantities": [],
                    "prices": [],
                    "lead_time_days": 2.0,
                },
            )
            quantity = _to_float(item.get("quantity") or item.get("qty"), default=0.0)
            unit_price = _to_float(item.get("unit_price"), default=0.0)
            if quantity > 0:
                entry["quantities"].append(quantity)
            if unit_price > 0:
                entry["prices"].append(unit_price)

    items: list[dict[str, Any]] = []
    for entry in grouped.values():
        quantities = entry.pop("quantities")
        prices = entry.pop("prices")
        if not quantities or not prices:
            continue
        avg_qty = sum(quantities) / len(quantities)
        avg_price = sum(prices) / len(prices)
        entry["current_par"] = round(avg_qty, 2)
        entry["unit_cost"] = round(avg_price, 2)
        items.append(entry)

    return sorted(items, key=lambda item: item["item_name"])


def _line_items(order: dict[str, Any]) -> list[dict[str, Any]]:
    items = order.get("items") or order.get("line_items") or []
    return items if isinstance(items, list) else []


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default
