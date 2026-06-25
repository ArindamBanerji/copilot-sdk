"""Purchasing cross-category discovery endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.services.cross_discovery import PurchasingCrossDiscovery, demo_discovery_decisions


def create_discovery_router() -> APIRouter:
    router = APIRouter(prefix="/api/purchasing/discovery", tags=["purchasing-discovery"])
    service = PurchasingCrossDiscovery()

    @router.get("/insights")
    def insights() -> dict:
        rows = [item.to_dict() for item in service.discover(demo_discovery_decisions())]
        return {
            "insights": rows,
            "provenance": "demo",
            "note": "Analysis based on sample decisions.",
        }

    @router.get("/digest")
    def digest() -> dict:
        return {
            "digest": service.weekly_digest(demo_discovery_decisions()),
            "provenance": "demo",
            "note": "Analysis based on sample decisions.",
        }

    return router
