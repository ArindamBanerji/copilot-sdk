"""Regime throttle status endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.services.regime_monitor import RegimeMonitor


def create_regime_status_router(monitor: RegimeMonitor) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-regime-status"])

    @router.get("/regime-status")
    def regime_status() -> dict[str, Any]:
        status = monitor.status()
        restrictions = []
        if status.regime_break_active:
            restrictions = [f"theta_min tightened {monitor.tightening_percent}%", "AE promotions deferred"]
        return {
            "current_regime": status.current_regime,
            "previous_regime": status.previous_regime,
            "regime_break_active": status.regime_break_active,
            "decisions_in_new_regime": status.decisions_in_new_regime,
            "decisions_to_stabilize": status.decisions_to_stabilize,
            "autonomy_level": "restricted" if status.regime_break_active else "normal",
            "restrictions": restrictions,
        }

    return router
