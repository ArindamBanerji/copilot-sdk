"""Purchasing QuickBooks Online data endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.connectors.mock_qbo import MockQBOConnector
from copilot_sdk.di.profiler import BaseSourceProfiler


def create_qbo_router(connector: Any | None = None) -> APIRouter:
    """Create read-only QBO endpoints for Purchasing."""

    def _connector() -> Any:
        if connector is None:
            return MockQBOConnector()
        if callable(connector) and not hasattr(connector, "fetch"):
            return connector()
        return connector

    router = APIRouter(prefix="/api/purchasing/qbo", tags=["qbo"])

    @router.get("/vendors")
    def get_vendors() -> list[dict]:
        return _connector().fetch_vendors()

    @router.get("/bills")
    def get_bills(since_days: int = 365) -> list[dict]:
        return _connector().fetch_bills(since_days=since_days)

    @router.get("/purchase-orders")
    def get_purchase_orders(since_days: int = 365) -> list[dict]:
        return _connector().fetch_purchase_orders(since_days=since_days)

    @router.get("/payments")
    def get_payments(since_days: int = 365) -> list[dict]:
        return _connector().fetch_payments(since_days=since_days)

    @router.get("/price-history/{vendor_id}/{item_name}")
    def get_price_history(vendor_id: str, item_name: str) -> list[dict]:
        return _connector().compute_price_history(vendor_id, item_name)

    @router.get("/lead-times/{vendor_id}")
    def get_lead_times(vendor_id: str) -> dict:
        return _connector().compute_lead_times(vendor_id)

    @router.get("/status")
    def get_status() -> dict[str, Any]:
        active = _connector()
        try:
            status = active.test_connection()
        except Exception as exc:
            status = {
                "connected": False,
                "company_name": None,
                "realm_id": None,
                "error": str(exc),
            }
        status["source_name"] = str(getattr(active, "source_name", "quickbooks_online_mock"))
        status["entity_type"] = str(getattr(active, "entity_type", "accounting"))
        return status

    @router.get("/profile")
    def get_profile() -> dict[str, Any]:
        active = _connector()
        entity_ids = ["vendors", "bills", "purchase_orders", "payments"]
        profile = BaseSourceProfiler(active).profile(entity_ids)
        payload = profile.to_dict()
        payload["entity_ids"] = entity_ids
        return payload

    return router
