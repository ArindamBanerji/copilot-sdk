"""FastAPI router for materialized tab-state reads."""

from __future__ import annotations

from fastapi import APIRouter, Query

from copilot_sdk.state.invalidation import get_tab_state_cache
from copilot_sdk.state.tab_state_cache import TabStateCache


def create_tab_state_router(cache: TabStateCache) -> APIRouter:
    router = APIRouter(tags=[f"{cache.copilot}-tab-state"])

    @router.get(f"/api/{cache.copilot}/tab-state")
    async def tab_state(keys: str = Query(default="")) -> dict[str, dict[str, object]]:
        requested = [key.strip() for key in keys.split(",") if key.strip()]
        if not requested:
            return {}
        return await cache.get(requested)

    @router.get("/api/{copilot}/static-urls")
    def static_urls(copilot: str) -> list[str]:
        selected = cache if copilot == cache.copilot else get_tab_state_cache(copilot)
        if selected is None:
            return []
        return [
            registration.url
            for registration in selected.registrations.values()
            if registration.category == "STATIC"
        ]

    return router
