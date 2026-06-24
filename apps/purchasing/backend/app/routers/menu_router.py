"""Menu engineering endpoints."""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter

from app.services.menu_engineer import MenuEngineer, demo_menu_items


def create_menu_router() -> APIRouter:
    router = APIRouter(prefix="/api/purchasing/menu", tags=["purchasing-menu"])
    engineer = MenuEngineer()

    @router.get("/analysis")
    def analysis() -> dict:
        return {
            "items": [item.to_dict() for item in engineer.analyze(demo_menu_items())],
            "provenance": "demo",
            "note": "Analysis based on sample menu data. Connect POS for live intelligence.",
        }

    @router.get("/alerts")
    def alerts() -> dict:
        return {
            "alerts": engineer.margin_alerts(engineer.analyze(demo_menu_items())),
            "provenance": "demo",
            "note": "Alerts based on sample menu data. Connect POS for live intelligence.",
        }

    @router.get("/summary")
    def summary() -> dict:
        counts = Counter(item.classification for item in engineer.analyze(demo_menu_items()))
        return {
            "stars": counts.get("star", 0),
            "puzzles": counts.get("puzzle", 0),
            "plowhorses": counts.get("plowhorse", 0),
            "dogs": counts.get("dog", 0),
            "provenance": "demo",
            "note": "Summary based on sample menu data. Connect POS for live intelligence.",
        }

    return router
