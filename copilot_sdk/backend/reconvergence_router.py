"""Read-only reconvergence summary from the live scorer state."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter


def create_reconvergence_router(scorer_provider: Callable[[], Any], *, domain: str) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["reconvergence"])

    @router.get("/reconvergence")
    def get_reconvergence() -> dict[str, int | float | str]:
        scorer = scorer_provider()
        get_count = getattr(scorer, "get_verified_count", None)
        verified = int(get_count()) if callable(get_count) else 50
        cold_start = max(1, verified // 10)
        warm_start = max(1, verified // 50)
        return {"cold_start": cold_start, "warm_start": warm_start,
                "ratio": cold_start / warm_start, "domain": domain, "verified_count": verified}

    return router
