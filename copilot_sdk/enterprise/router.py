"""Optional FastAPI surface for the enterprise value report."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from .roi import EnterpriseROI, SunkInvestmentCalculator


def create_enterprise_router(
    calculator: SunkInvestmentCalculator,
    copilots: list[str] | None = None,
) -> APIRouter:
    """Create the read-only enterprise ROI endpoints."""

    configured = list(copilots or [])
    router = APIRouter(prefix="/api/enterprise", tags=["enterprise"])

    @router.get("/roi")
    def roi() -> dict[str, Any]:
        return calculator.compute(configured).to_dict()

    @router.get("/roi/{copilot}")
    def copilot_roi(copilot: str) -> dict[str, Any]:
        if calculator.known_copilots and copilot not in calculator.known_copilots:
            raise HTTPException(status_code=404, detail=f"Unknown copilot: {copilot}")
        report = calculator.compute([copilot])
        return report.per_copilot[0]

    return router


def enterprise_roi_payload(report: EnterpriseROI) -> dict[str, Any]:
    """Return a router-friendly payload for integrations without FastAPI."""

    return report.to_dict()
