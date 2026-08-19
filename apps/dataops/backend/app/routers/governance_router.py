"""DataOps governance routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..dataops_governance import DataOpsGovernance


class HoldoutRequest(BaseModel):
    decision_id: str
    source_id: str = "unknown"
    decision_class: str = "default"
    factor_vector: list[float] | None = None
    score_payload: dict[str, Any] = Field(default_factory=dict)


class VerifyRequest(BaseModel):
    decision_id: str
    verdict: dict[str, Any] = Field(default_factory=dict)


class PromotionRequest(BaseModel):
    decision_class: str
    evidence: dict[str, Any] = Field(default_factory=dict)


def create_governance_router(governance: DataOpsGovernance) -> APIRouter:
    router = APIRouter(prefix="/api/dataops", tags=["dataops-governance"])

    @router.get("/claims")
    def claims(context: str = "demo") -> dict[str, Any]:
        return {"claims": governance.claim_status(context), "context": context}

    @router.get("/abstention-check")
    def abstention_check(source_id: str = Query(...), evidence_floor: int = 10) -> dict[str, Any]:
        return governance.abstention(source_id, evidence_floor)

    @router.post("/holdout/register")
    def register_holdout(request: HoldoutRequest) -> dict[str, Any]:
        return governance.register_holdout(request.decision_id, request.source_id, request.decision_class, request.factor_vector, request.score_payload)

    @router.get("/holdout/status")
    def holdout_status(source_id: str | None = None) -> dict[str, Any]:
        return {"entries": governance.holdout_status(source_id), "holdout_days": 30}

    @router.post("/holdout/verify")
    def verify_holdout(request: VerifyRequest) -> dict[str, Any]:
        try:
            return governance.verify_holdout(request.decision_id, request.verdict)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown holdout: {exc.args[0]}") from exc

    @router.get("/provenance/{decision_id}")
    def provenance(decision_id: str) -> dict[str, Any]:
        try:
            return governance.provenance(decision_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown decision: {exc.args[0]}") from exc

    @router.post("/promotion")
    def promotion(request: PromotionRequest) -> dict[str, Any]:
        return governance.promotion_status(request.decision_class)

    @router.post("/promotion/{record_id}/advance")
    def advance(record_id: str, evidence: dict[str, Any]) -> dict[str, Any]:
        try:
            return governance.advance_promotion(record_id, evidence)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown promotion: {exc.args[0]}") from exc

    @router.get("/frozen-twin/status")
    def frozen_status() -> dict[str, Any]:
        return {"frozen": governance.frozen_twin.is_frozen(), "copilot": "dataops"}

    @router.post("/frozen-twin/freeze")
    def freeze_twin() -> dict[str, Any]:
        try:
            return governance.freeze_twin()
        except FileExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (RuntimeError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=f"Frozen Twin unavailable: {exc}") from exc

    return router
