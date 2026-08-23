"""FastAPI conservation router factory backed by GAE calibration."""

from __future__ import annotations

import math
from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from copilot_sdk.backend.conservation_utils import (
    ENGINE_WHAT_IF,
    check_payload,
    compute_conservation_status_payload,
    state_counts,
)
from copilot_sdk.backend.models import (
    ConservationStatusResponse,
    ConservationWhatIfResponse,
)
from copilot_sdk.state.cached_static import cached_static


from gae.calibration import check_conservation, compute_theta_min


class ConservationWhatIfRequest(BaseModel):
    alpha: float = Field(..., gt=0.0)
    q: float = Field(..., ge=0.0)
    V: float = Field(..., gt=0.0)
    theta_min: float | None = None


def create_conservation_router(
    domain: str,
    state_provider: Callable[[], Any] | Any | None = None,
) -> APIRouter:
    """Create a domain-parametric conservation router."""

    router = APIRouter()

    @router.get("/conservation/status", response_model=ConservationStatusResponse)
    @cached_static("conservation", copilot=domain)
    def status(request: Request) -> dict[str, Any]:
        try:
            state = _resolve_state(state_provider)
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Graph store unavailable: {exc}") from exc
        if state_provider is not None and state is None:
            raise HTTPException(status_code=503, detail="Graph store unavailable")
        try:
            return compute_conservation_status_payload(domain, state)
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Graph store unavailable: {exc}") from exc

    @router.post("/conservation/what-if", response_model=ConservationWhatIfResponse)
    def what_if(request: ConservationWhatIfRequest) -> dict[str, Any]:
        try:
            theta_min = (
                request.theta_min
                if request.theta_min is not None
                else compute_theta_min(request.alpha, request.V)
            )
            check = check_conservation(
                alpha=request.alpha,
                q=request.q,
                V=request.V,
                theta_min=theta_min,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {
            "engine": ENGINE_WHAT_IF,
            "domain": domain,
            "inputs": {
                "alpha": request.alpha,
                "q": request.q,
                "V": request.V,
                "theta_min": _finite_or_none(theta_min),
            },
            **check_payload(check),
        }

    return router


def _resolve_state(state_provider: Callable[[], Any] | Any | None) -> Any:
    if callable(state_provider):
        return state_provider()
    return state_provider


def _state_counts(state: Any) -> dict[str, float | int]:
    if state is None:
        return _default_counts()
    return state_counts(state)


def _check_payload(check: Any) -> dict[str, Any]:
    return check_payload(check)


def _default_counts() -> dict[str, float | int]:
    return {
        "verified_count": 0,
        "correct_count": 0,
        "total_decisions": 0,
        "penalty_ratio": 1.0,
    }


def _finite_or_none(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
