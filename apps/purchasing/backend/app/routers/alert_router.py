"""Aggregated purchasing alert endpoints."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter

from app.services.alert_engine import PurchasingAlertEngine
from app.services.supplier_signal_publisher import SupplierSignalPublisher


def create_alert_router(
    conservation_provider: Callable[[], dict[str, Any] | None] | None = None,
    outbox_store: Any | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing/alerts", tags=["purchasing-alerts"])
    publisher = SupplierSignalPublisher(outbox_store) if outbox_store is not None else None
    engine = PurchasingAlertEngine(signal_publisher=publisher)

    @router.get("")
    def alerts(severity: str | None = None) -> dict:
        conservation_status = conservation_provider() if conservation_provider else None
        rows = engine.evaluate(conservation_status=conservation_status)
        if severity:
            rows = [row for row in rows if str(row.get("severity")) == severity]
        return {"alerts": rows, "provenance": "demo"}

    return router
