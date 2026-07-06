"""Weekly report router factory."""

from __future__ import annotations

import dataclasses
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


class CategorySummaryResponse(BaseModel):
    category: str
    decisions_count: int
    correct_count: int
    accuracy: float
    top_action: str | None


class CostImpactResponse(BaseModel):
    food_cost_saved: float
    prep_waste_avoided: float
    price_flags_surfaced: float
    net_found_period: float


class SupplierChangeResponse(BaseModel):
    supplier_id: str
    metric: str
    previous_value: float
    current_value: float
    direction: str
    supplier: str | None = None
    issue: str | None = None
    pct: float | None = None


class WeeklyReportResponse(BaseModel):
    domain: str
    period_start: float
    period_end: float
    generated_at: float
    total_decisions: int
    total_verified: int
    overall_accuracy: float
    conservation_status: str
    conservation_q: float
    conservation_alpha: float
    categories: list[CategorySummaryResponse]
    cost_impact: CostImpactResponse
    supplier_changes: list[SupplierChangeResponse]
    iks_current: float
    iks_delta: float


def create_report_router(domain: str, report_factory: Any, prefix: str | None = None) -> APIRouter:
    """Create GET /report/weekly under the supplied router prefix."""

    router_prefix = prefix or "/api/report"
    router = APIRouter(prefix=router_prefix, tags=[f"{domain}-report"])

    @router.get("/report/weekly", response_model=WeeklyReportResponse)
    def get_weekly_report(period_days: int = 7) -> dict[str, Any]:
        if period_days < 1:
            raise HTTPException(status_code=400, detail="period_days must be >= 1")
        generator = report_factory()
        report = generator.generate(period_days=period_days)
        payload = dataclasses.asdict(report)
        cost_impact = payload.get("cost_impact", {})
        payload["cost_impact"] = {
            "food_cost_saved": cost_impact.get("dollars_found", 0.0),
            "prep_waste_avoided": cost_impact.get("waste_prevented", 0.0),
            "price_flags_surfaced": cost_impact.get("price_variance_flagged", 0.0),
            "net_found_period": cost_impact.get("net_found_period", 0.0),
        }
        return payload

    return router
