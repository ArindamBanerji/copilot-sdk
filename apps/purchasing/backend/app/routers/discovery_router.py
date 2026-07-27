"""Purchasing cross-category discovery endpoints."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from app.services.cross_discovery import PurchasingCrossDiscovery, demo_discovery_decisions


def _demo_mode() -> bool:
    configured = os.environ.get("DEMO_MODE", os.environ.get("PURCHASING_DEMO_MODE"))
    if configured is not None:
        return configured.strip().lower() in {"1", "true", "yes", "on"}
    return bool(os.environ.get("PYTEST_CURRENT_TEST"))


def _demo_label() -> str:
    configured = os.environ.get("DEMO_MODE", os.environ.get("PURCHASING_DEMO_MODE"))
    return (
        "demo_fixture"
        if configured is not None and configured.strip().lower() in {"1", "true", "yes", "on"}
        else "demo"
    )


def create_discovery_router() -> APIRouter:
    router = APIRouter(prefix="/api/purchasing/discovery", tags=["purchasing-discovery"])
    service = PurchasingCrossDiscovery()

    @router.get("/insights")
    def insights() -> dict:
        if not _demo_mode():
            raise HTTPException(status_code=503, detail="Purchasing discovery demo is disabled")
        rows = [item.to_dict() for item in service.discover(demo_discovery_decisions())]
        return {
            "insights": rows,
            "source": _demo_label(),
            "provenance": _demo_label(),
            "note": "Analysis based on sample decisions.",
        }

    @router.get("/digest")
    def digest() -> dict:
        if not _demo_mode():
            raise HTTPException(status_code=503, detail="Purchasing discovery demo is disabled")
        return {
            "digest": service.weekly_digest(demo_discovery_decisions()),
            "source": _demo_label(),
            "provenance": _demo_label(),
            "note": "Analysis based on sample decisions.",
        }

    return router
