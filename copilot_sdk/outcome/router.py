"""Optional FastAPI adapter for verified-outcome processing."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from .models import VerifiedOutcome
from .processor import OutcomeProcessor


def create_outcome_router(processor: OutcomeProcessor) -> APIRouter:
    router = APIRouter(prefix="/api/outcome", tags=["verified-outcome"])

    @router.post("/process")
    async def process(request: Request) -> dict[str, Any]:
        try:
            outcome = VerifiedOutcome.from_dict(await request.json())
            return processor.process(outcome).to_dict()
        except (TypeError, ValueError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @router.get("/count")
    def count(copilot: str, category: str | None = None) -> dict[str, Any]:
        return {"copilot": copilot, "category": category, "count": processor.count_verified(copilot, category)}

    @router.get("/{receipt_id}")
    def get_receipt(receipt_id: str) -> dict[str, Any]:
        outcome = processor.get_receipt(receipt_id)
        if outcome is None:
            raise HTTPException(status_code=404, detail="verified outcome not found")
        return outcome.to_dict()

    return router
