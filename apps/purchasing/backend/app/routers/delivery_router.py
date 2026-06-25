"""Delivery schedule endpoints."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter

from app.services.delivery_coordinator import DeliveryCoordinator


def create_delivery_router() -> APIRouter:
    router = APIRouter(prefix="/api/purchasing/delivery", tags=["purchasing-delivery"])
    coordinator = DeliveryCoordinator()

    @router.get("/today")
    def today() -> dict[str, Any]:
        schedule = coordinator.schedule_day(date.today())
        return {**schedule, "suggestions": coordinator.suggest_consolidation(schedule)}

    @router.get("/week")
    def week(start: str | None = None) -> dict[str, Any]:
        return coordinator.schedule_week(start or date.today())

    @router.get("/consolidation")
    def consolidation() -> dict[str, Any]:
        schedule = coordinator.schedule_day(date.today())
        return {"suggestions": coordinator.suggest_consolidation(schedule), "provenance": "demo"}

    return router
