"""Public D-CEL health contract backed by the existing connector health reads."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter


def create_enterprise_health_router() -> APIRouter:
    router = APIRouter(tags=["enterprise-health"])

    @router.get("/enterprise-health")
    async def enterprise_health() -> dict[str, Any]:
        # Reuse the application-owned graph client and request-scoped connector
        # caches, including their live/cache/unavailable and provenance labels.
        from .context_router import enterprise_health as connector_health

        health = await connector_health()
        connectors = [
            {"name": name, **health[name]}
            for name in ("sap", "celonis")
        ]
        return {
            "status": health["overall"],
            "connectors": connectors,
            # The connectors expose last_check, not a verified data-refresh
            # timestamp. A health check must not make stale samples look fresh.
            "last_refresh": None,
            "graph": health["graph"],
            "fusion_ready": health["fusion_ready"],
            "engine_version": health["engine_version"],
        }

    return router
