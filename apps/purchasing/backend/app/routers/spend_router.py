"""Purchasing spend dashboard endpoints."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException

from app.connectors.commodity_provider import CommodityDataProvider
from app.data_helpers import is_sample_data
from app.services.spend_dashboard import SpendDashboardService


SCRAPED_EXTERNAL_PROVENANCE = "scraped_external"
SAMPLE_PROVENANCE = "sample"


def _demo_mode() -> bool:
    configured = os.environ.get("DEMO_MODE", os.environ.get("PURCHASING_DEMO_MODE"))
    if configured is not None:
        return configured.strip().lower() in {"1", "true", "yes", "on"}
    return bool(os.environ.get("PYTEST_CURRENT_TEST"))


def create_spend_router(
    orders: list[dict] | None = None,
    connector: Any | None = None,
    commodity_provider: CommodityDataProvider | None = None,
) -> APIRouter:
    default_connector = connector is None
    if default_connector:
        from app.connectors.mock_qbo import MockQBOConnector

        connector = MockQBOConnector()
    if commodity_provider is None:
        commodity_provider = CommodityDataProvider()

    router = APIRouter(prefix="/api/purchasing/spend", tags=["spend"])

    def _get_orders() -> list[dict]:
        if default_connector and not _demo_mode():
            raise HTTPException(status_code=503, detail="QuickBooks spend provider unavailable")
        if orders is not None:
            rows = list(orders)
        else:
            rows = qbo_bills_for_spend(connector)
        return [row for row in rows if not is_sample_data(row)]

    def _service() -> SpendDashboardService:
        return SpendDashboardService(_get_orders())

    @router.get("/summary")
    def get_summary(days: int = 7) -> dict:
        return {**_service().summary(days=days), "commodity": _commodity_context(commodity_provider)}

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
    connector_source = str(getattr(connector, "source_name", type(connector).__name__))
    return [
        _normalize_qbo_bill_for_spend({**bill, "_connector_source": connector_source})
        for bill in bills
        if isinstance(bill, dict)
    ]


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
            "provenance": _connector_provenance(bill),
            "order_id": bill.get("order_id") or bill.get("invoice_id"),
            "order_date": bill.get("order_date") or bill.get("invoice_date") or bill.get("timestamp"),
            "total_value": bill.get("total_value") if bill.get("total_value") is not None else bill.get("amount"),
            "category": category,
            "items": line_items,
        }
    )
    return row


def _connector_provenance(bill: dict[str, Any]) -> str:
    if bill.get("provenance"):
        return str(bill["provenance"])
    source = str(
        bill.get("source")
        or bill.get("source_name")
        or bill.get("_connector_source")
        or ""
    ).lower()
    if "mock" in source or "fixture" in source:
        return SAMPLE_PROVENANCE
    return SCRAPED_EXTERNAL_PROVENANCE


def _normalize_qbo_line_item(line: dict[str, Any]) -> dict[str, Any]:
    item = dict(line)
    item_name = item.get("name") or item.get("item_name") or item.get("item_id")
    if item_name is not None:
        item.setdefault("name", str(item_name))
        item.setdefault("item_id", str(item_name).replace(" ", "_"))
    return item


def _commodity_context(provider: CommodityDataProvider | None = None) -> dict[str, Any]:
    provider = provider or CommodityDataProvider()
    result = provider.get_all_indices()
    source = str(result.source)
    if source in {SAMPLE_PROVENANCE, "demo_fixture"} and not _demo_mode():
        raise HTTPException(status_code=503, detail="Commodity data provider unavailable")
    return {
        "provenance": source,
        "source": result.label,
        "indices": result.value if source != SAMPLE_PROVENANCE else {},
    }
