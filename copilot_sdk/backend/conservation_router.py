"""FastAPI conservation router factory backed by GAE calibration."""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


def _ensure_gae_path() -> None:
    workspace = Path(__file__).resolve().parents[3]
    gae_path = workspace / "graph-attention-engine-v50"
    if gae_path.exists() and str(gae_path) not in sys.path:
        sys.path.insert(0, str(gae_path))


_ensure_gae_path()

from gae.calibration import check_conservation, compute_theta_min, conservation_status


ENGINE_STATUS = {"gae": "gae.calibration", "component": "conservation_status"}
ENGINE_WHAT_IF = {"gae": "gae.calibration", "component": "check_conservation"}


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

    @router.get("/conservation/status")
    def status() -> dict[str, Any]:
        state = _resolve_state(state_provider)
        counts = _state_counts(state)
        check = conservation_status(
            verified_count=counts["verified_count"],
            correct_count=counts["correct_count"],
            total_decisions=counts["total_decisions"],
            penalty_ratio=counts["penalty_ratio"],
        )
        return {
            "engine": ENGINE_STATUS,
            "domain": domain,
            **counts,
            **_check_payload(check),
        }

    @router.post("/conservation/what-if")
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
            **_check_payload(check),
        }

    return router


def _resolve_state(state_provider: Callable[[], Any] | Any | None) -> Any:
    if callable(state_provider):
        return state_provider()
    return state_provider


def _state_counts(state: Any) -> dict[str, float | int]:
    if state is None:
        return _default_counts()
    if isinstance(state, dict):
        return {
            "verified_count": max(int(state.get("verified_count") or 0), 0),
            "correct_count": max(int(state.get("correct_count") or 0), 0),
            "total_decisions": max(int(state.get("total_decisions") or 0), 0),
            "penalty_ratio": _positive_float(state.get("penalty_ratio"), default=1.0),
        }

    store = getattr(state, "store", None) or getattr(state, "_store", None) or state
    count_verified = getattr(store, "count_verified", None)
    count_correct = getattr(store, "count_correct", None)
    get_all_decisions = getattr(store, "get_all_decisions", None)
    preset = getattr(state, "_preset", None)

    verified_count = int(count_verified()) if callable(count_verified) else 0
    correct_count = int(count_correct()) if callable(count_correct) else 0
    total_decisions = (
        len(get_all_decisions()) if callable(get_all_decisions) else verified_count
    )
    penalty_ratio = _positive_float(
        getattr(preset, "penalty_ratio", None),
        default=1.0,
    )
    return {
        "verified_count": max(verified_count, 0),
        "correct_count": max(correct_count, 0),
        "total_decisions": max(total_decisions, 0),
        "penalty_ratio": penalty_ratio,
    }


def _default_counts() -> dict[str, float | int]:
    return {
        "verified_count": 0,
        "correct_count": 0,
        "total_decisions": 0,
        "penalty_ratio": 1.0,
    }


def _check_payload(check: Any) -> dict[str, Any]:
    return {
        "signal": _finite_or_none(check.signal),
        "theta_min": _finite_or_none(check.theta_min),
        "headroom": _finite_or_none(check.headroom),
        "status": check.status,
        "passed": bool(check.passed),
    }


def _positive_float(value: Any, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number) or number <= 0:
        return default
    return number


def _finite_or_none(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
