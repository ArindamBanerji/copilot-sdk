"""Budget-policy telemetry endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from copilot_sdk.scoring.budget_policy import AdaptiveBudgetPolicy


def create_budget_router(policy: AdaptiveBudgetPolicy) -> APIRouter:
    """Create the read-only budget telemetry router for one policy instance."""
    router = APIRouter(prefix="/api/self", tags=["self-computation"])

    @router.get("/investigation-budget")
    def investigation_budget() -> dict[str, object]:
        return policy.get_stats()

    return router


__all__ = ["create_budget_router"]
