"""Purchasing spend dashboard endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.data_helpers import load_purchasing_orders
from app.services.spend_dashboard import SpendDashboardService


def create_spend_router(orders: list[dict] | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing/spend", tags=["spend"])

    def _service() -> SpendDashboardService:
        return SpendDashboardService(list(orders) if orders is not None else load_purchasing_orders())

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
