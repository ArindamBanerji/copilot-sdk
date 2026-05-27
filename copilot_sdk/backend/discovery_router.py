"""FastAPI discovery router factory."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Query

from copilot_sdk.backend.models import (
    DiscoveryAlertsResponse,
    DiscoveryDigestResponse,
    DiscoverySweepResponse,
)


def create_discovery_router(engine: Any) -> APIRouter:
    """Create advisory discovery endpoints for a DiscoveryEngine."""

    router = APIRouter(prefix="/api/discovery", tags=["Discovery"])

    @router.post("/sweep", response_model=DiscoverySweepResponse)
    def sweep() -> dict[str, Any]:
        alerts = list(engine.sweep())
        return {
            "new_alerts": len(alerts),
            "alerts": [_alert_payload(alert) for alert in alerts],
        }

    @router.get("/digest", response_model=DiscoveryDigestResponse)
    def digest(min_confidence: float = Query(0.5, ge=0.0, le=1.0)) -> dict[str, Any]:
        return {
            "alerts": [
                _alert_payload(alert)
                for alert in engine.get_digest(min_confidence=min_confidence)
            ]
        }

    @router.get("/alerts", response_model=DiscoveryAlertsResponse)
    def alerts() -> dict[str, Any]:
        all_alerts = list(getattr(engine, "_alerts", []))
        return {
            "total": len(all_alerts),
            "alerts": [_alert_payload(alert) for alert in all_alerts],
        }

    return router


def _alert_payload(alert: Any) -> dict[str, Any]:
    return asdict(alert)
