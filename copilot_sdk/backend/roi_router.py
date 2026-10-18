"""Modeled ROI calculator backed by the shared projection primitive."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from pydantic import BaseModel

from copilot_sdk.backend.modeled_projection import modeled_projection


class ROIRequest(BaseModel):
    daily_decisions: float
    analyst_cost_per_hour: float
    current_accuracy: float


def create_roi_router(scorer_provider: Callable[[], Any], *, domain: str = "unknown") -> APIRouter:
    router = APIRouter(prefix="/api/roi", tags=["roi"])

    @router.post("/calculate")
    def calculate_roi(request: ROIRequest) -> dict[str, int | float | None]:
        scorer = scorer_provider()
        get_count = getattr(scorer, "get_verified_count", None)
        verified = int(get_count()) if callable(get_count) else 50
        weekly = request.daily_decisions * 5
        benefit = request.analyst_cost_per_hour * 0.5
        result = modeled_projection({
            "setup_cost": 10000.0, "weekly_decisions": weekly,
            "benefit_per_decision": benefit, "weekly_operating_cost": weekly * 0.1,
            "required_verified_decisions": 100, "provenance": domain,
        }, verified)
        divergence = result.get("projected_divergence_week")
        return {
            "divergence_week": int(divergence) if isinstance(divergence, int | float) else 0,
            "projected_divergence": float(result.get("readiness_score") or 0.0),
            "breakeven_week": max(1, int(10000.0 / max(1.0, weekly * benefit * request.current_accuracy))),
        }

    return router
