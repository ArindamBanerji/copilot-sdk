"""FastAPI endpoints for measured transfer pilots."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .transfer import MeasuredTransfer


class StartPilotRequest(BaseModel):
    copilot: str
    duration_days: int = 90


class RecordDecisionRequest(BaseModel):
    session_id: str
    decision_id: str
    category: str | None = None
    live_result: dict[str, Any] = Field(default_factory=dict)
    frozen_result: dict[str, Any] = Field(default_factory=dict)
    value: float | None = None


def create_measured_transfer_router(transfer: MeasuredTransfer) -> APIRouter:
    router = APIRouter(prefix="/api/pilot", tags=["measured-transfer"])

    @router.post("/start")
    def start(request: StartPilotRequest) -> dict[str, Any]:
        try:
            return transfer.start_pilot(request.copilot, request.duration_days).to_dict()
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/record")
    def record(request: RecordDecisionRequest) -> dict[str, Any]:
        try:
            return transfer.record_decision(
                request.session_id,
                request.decision_id,
                request.live_result,
                request.frozen_result,
                request.category,
                request.value,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @router.get("/report")
    def report(copilot: str) -> dict[str, Any]:
        try:
            return transfer.latest_report(copilot).to_dict()
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/status")
    def status() -> dict[str, Any]:
        return {"pilots": transfer.status()}

    return router


create_pilot_router = create_measured_transfer_router
