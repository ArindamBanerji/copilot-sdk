"""Optional FastAPI router for promotion state inspection and actions."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query

from .core import PromotionEngine


def create_promotion_router(engine: PromotionEngine) -> APIRouter:
    router = APIRouter(prefix="/api/promotion", tags=["promotion"])

    @router.get("/status")
    def status(copilot: str = Query(...)) -> dict[str, Any]:
        records = engine.get_all(copilot)
        return {"copilot": copilot, "records": [record.to_dict() for record in records]}

    @router.get("/{record_id}")
    def get_record(record_id: str) -> dict[str, Any]:
        record = engine.store.load(record_id)
        if record is None:
            raise HTTPException(status_code=404, detail="promotion record not found")
        return record.to_dict()

    @router.post("/{record_id}/advance")
    def advance(record_id: str, evidence: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        result = engine.advance(record_id, evidence)
        if result.record is None and result.reason == "record_not_found":
            raise HTTPException(status_code=404, detail=result.reason)
        return {
            "advanced": result.advanced,
            "new_stage": result.new_stage.value,
            "reason": result.reason,
            "record": result.record.to_dict() if result.record else None,
        }

    @router.post("/{record_id}/rollback")
    def rollback(record_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        result = engine.rollback(record_id, str(payload.get("reason", "manual rollback")))
        if result.record is None and result.reason == "record_not_found":
            raise HTTPException(status_code=404, detail=result.reason)
        return {
            "advanced": result.advanced,
            "new_stage": result.new_stage.value,
            "reason": result.reason,
            "record": result.record.to_dict() if result.record else None,
        }

    return router
