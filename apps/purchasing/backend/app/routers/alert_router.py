"""Aggregated purchasing alert endpoints."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter

from app.services.alert_engine import PurchasingAlertEngine


def create_alert_router(conservation_provider: Callable[[], dict[str, Any] | None] | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing/alerts", tags=["purchasing-alerts"])
    engine = PurchasingAlertEngine()

    @router.get("")
    def alerts(severity: str | None = None) -> dict:
        conservation_status = conservation_provider() if conservation_provider else None
        rows = engine.evaluate(conservation_status=conservation_status)
        if severity:
            rows = [row for row in rows if str(row.get("severity")) == severity]
        return {"alerts": rows, "provenance": "demo"}

    return router
