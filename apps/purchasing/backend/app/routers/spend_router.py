"""Purchasing spend dashboard endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.data_helpers import assert_no_sample_in_metric
from app.services.spend_dashboard import SpendDashboardService


SCRAPED_EXTERNAL_PROVENANCE = "scraped_external"


def create_spend_router(
    orders: list[dict] | None = None,
    connector: Any | None = None,
) -> APIRouter:
    if connector is None:
        from app.connectors.mock_qbo import MockQBOConnector

        connector = MockQBOConnector()

    router = APIRouter(prefix="/api/purchasing/spend", tags=["spend"])

    def _get_orders() -> list[dict]:
        if orders is not None:
            rows = list(orders)
        else:
            rows = qbo_bills_for_spend(connector)
        assert_no_sample_in_metric(rows, "spend_dashboard")
        return rows

    def _service() -> SpendDashboardService:
        return SpendDashboardService(_get_orders())

    @router.get("/summary")
    def get_summary(days: int = 7) -> dict:
        return _service().summary(days=days)

    @router.get("/by-category")
    def get_by_category(days: int = 30) -> list[dict]:
        return _service().by_category(days=days)

    @router.get("/by-supplier")
    def get_by_supplier(days: int = 30, limit: int = 10) -> list[dict]:
        return _service().by_supplier(days=days, limit=limit)

    @router.get("/alerts")
    def get_alerts(threshold: float = 10.0) -> list[dict]:
        return _service().price_alerts(threshold_pct=threshold)

    @router.get("/cost-per-cover")
    def get_cost_per_cover(days: int = 30) -> list[dict]:
        return _service().cost_per_cover_trend(days=days)

    return router


def qbo_bills_for_spend(connector: Any) -> list[dict]:
    """Return QBO invoice records normalized for spend analytics."""
    bills = connector.fetch_bills()
    return [_normalize_qbo_bill_for_spend(bill) for bill in bills if isinstance(bill, dict)]


def _normalize_qbo_bill_for_spend(bill: dict[str, Any]) -> dict[str, Any]:
    raw_line_items = bill.get("line_items") if isinstance(bill.get("line_items"), list) else []
    line_items = [
        _normalize_qbo_line_item(line)
        for line in raw_line_items
        if isinstance(line, dict)
    ]
    category = str(
        bill.get("category")
        or next((line.get("category") for line in line_items if line.get("category")), "")
    )
    row = dict(bill)
    row.update(
        {
            "provenance": SCRAPED_EXTERNAL_PROVENANCE,
            "order_id": bill.get("order_id") or bill.get("invoice_id"),
            "order_date": bill.get("order_date") or bill.get("invoice_date") or bill.get("timestamp"),
            "total_value": bill.get("total_value") if bill.get("total_value") is not None else bill.get("amount"),
            "category": category,
            "items": line_items,
        }
    )
    return row


def _normalize_qbo_line_item(line: dict[str, Any]) -> dict[str, Any]:
    item = dict(line)
    item_name = item.get("name") or item.get("item_name") or item.get("item_id")
    if item_name is not None:
        item.setdefault("name", str(item_name))
        item.setdefault("item_id", str(item_name).replace(" ", "_"))
    return item
