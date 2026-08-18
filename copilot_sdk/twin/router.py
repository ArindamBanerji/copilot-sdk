"""Optional FastAPI adapter for Frozen Twin operations."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from .service import FrozenTwin


def create_frozen_twin_router(twin: FrozenTwin, live_scorer: Any | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/twin", tags=["frozen-twin"])

    @router.get("/status")
    def status() -> dict[str, Any]:
        if not twin.is_frozen():
            return {"frozen": False, "snapshot_time": None, "decision_count": 0}
        snapshot = twin.get_snapshot()
        return {
            "frozen": True,
            "snapshot_time": snapshot.metadata.get("timestamp"),
            "decision_count": snapshot.metadata.get("decision_count", 0),
        }

    @router.get("/drift")
    def drift() -> dict[str, Any]:
        if live_scorer is None:
            raise HTTPException(status_code=503, detail="live scorer is not configured")
        if not twin.is_frozen():
            raise HTTPException(status_code=404, detail="Frozen Twin is not frozen")
        return twin.get_drift_report(live_scorer).__dict__

    @router.get("/parallel-score")
    def parallel_score(factor_vector: str, category_index: int = 0) -> dict[str, Any]:
        if live_scorer is None:
            raise HTTPException(status_code=503, detail="live scorer is not configured")
        try:
            vector = [float(value.strip()) for value in factor_vector.split(",") if value.strip()]
            result = twin.score_parallel(vector, category_index, live_scorer)
        except (TypeError, ValueError, RuntimeError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {"live_result": _result_payload(result.live_result), "frozen_result": _result_payload(result.frozen_result), "delta": result.delta}

    @router.post("/freeze", status_code=201)
    async def freeze(request: Request) -> dict[str, Any]:
        if live_scorer is None:
            raise HTTPException(status_code=503, detail="live scorer is not configured")
        body = await request.json()
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="request body must be an object")
        try:
            snapshot = twin.freeze(
                live_scorer,
                dict(body.get("conservation_state") or {}),
                float(body.get("iks", 0.0)),
                str(body["copilot"]),
            )
        except FileExistsError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except (KeyError, TypeError, ValueError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {"frozen": True, "checksum": snapshot.checksum, "snapshot_time": snapshot.metadata["timestamp"]}

    return router


def _result_payload(result: Any) -> dict[str, Any]:
    return {
        "action_index": int(result.action_index),
        "action_name": str(result.action_name),
        "probabilities": result.probabilities.tolist(),
        "distances": result.distances.tolist(),
        "confidence": float(result.confidence),
        "entropy": float(result.entropy),
        "confidence_gap": float(result.confidence_gap),
    }

