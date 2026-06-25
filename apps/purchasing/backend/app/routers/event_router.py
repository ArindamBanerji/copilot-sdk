"""Event planning endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services.event_planner import EventPlanner


class EventOutcomeRequest(BaseModel):
    plan: dict[str, Any]
    actual_usage: dict[str, float] = {}
    actual_waste: float = 0.0


def create_event_router() -> APIRouter:
    router = APIRouter(prefix="/api/purchasing/events", tags=["purchasing-events"])

    @router.get("/plan")
    def plan(request: Request, guests: int = 80, cuisine: str = "mixed") -> dict[str, Any]:
        planner = _planner(request)
        return {**planner.plan(guests, cuisine).to_dict(), "provenance": "demo"}

    @router.get("/history")
    def history(request: Request) -> list[dict[str, Any]]:
        return _planner(request).history()

    @router.post("/record")
    def record(payload: EventOutcomeRequest, request: Request) -> dict[str, Any]:
        return _planner(request).record_outcome(payload.plan, payload.actual_usage, payload.actual_waste)

    return router


def reset_event_state(app_state: Any) -> None:
    app_state.purchasing_event_planner = EventPlanner(history=[])


def _planner(request: Request) -> EventPlanner:
    planner = getattr(request.app.state, "purchasing_event_planner", None)
    if planner is None:
        planner = EventPlanner()
        request.app.state.purchasing_event_planner = planner
    return planner
