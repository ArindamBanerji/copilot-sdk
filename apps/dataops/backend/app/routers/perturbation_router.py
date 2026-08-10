"""Demo-only endpoints for the DI live perturbation proof."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from copilot_sdk.di.perturbation import PerturbationActiveError, PerturbationError, PerturbationService


class PerturbRequest(BaseModel):
    source_name: str = Field(min_length=1)
    perturbation: str = "degrade"
    magnitude: float = Field(ge=0.1, le=0.9)
    decisions: int = Field(default=20, ge=1, le=100)


def create_perturbation_router(
    *,
    scorer_provider: Callable[[], Any],
    service: PerturbationService,
) -> APIRouter:
    router = APIRouter()

    @router.get("/perturb/status")
    def status() -> dict[str, Any]:
        return {"enabled": _demo_enabled(), **service.status()}

    @router.post("/perturb")
    def perturb(request: PerturbRequest) -> dict[str, Any]:
        _require_demo_mode()
        try:
            return service.perturb(
                scorer_provider(),
                source_name=request.source_name,
                perturbation=request.perturbation,
                magnitude=request.magnitude,
                decisions=request.decisions,
            )
        except PerturbationActiveError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except PerturbationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/perturb/revert")
    def revert() -> dict[str, Any]:
        _require_demo_mode()
        return service.revert()

    return router


def _demo_enabled() -> bool:
    return os.environ.get("DATAOPS_DEMO_MODE") == "1"


def _require_demo_mode() -> None:
    if not _demo_enabled():
        raise HTTPException(status_code=403, detail="DI perturbation is available only in demo mode")
