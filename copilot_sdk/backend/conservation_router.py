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
from copilot_sdk.scoring.composite_gate import CompositeGate, outcomes_from_state
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
    projection_provider: Callable[[int], dict[str, Any]] | None = None,
) -> APIRouter:
    """Create a domain-parametric conservation router."""

    router = APIRouter()

    @router.get("/conservation/status", response_model=None)
    def status(request: Request) -> dict[str, Any]:
        try:
            state = _resolve_state(state_provider)
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Graph store unavailable: {exc}") from exc
        if state_provider is not None and state is None:
            raise HTTPException(status_code=503, detail="Graph store unavailable")
        try:
            payload = compute_conservation_status_payload(domain, state)
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Graph store unavailable: {exc}") from exc
        outcomes = outcomes_from_state(state)
        gate = CompositeGate(
            w_short=int(getattr(getattr(state, "_preset", None), "w_short", 20) or (state.get("w_short", 20) if isinstance(state, dict) else 20)),
            m_rate=float(getattr(getattr(state, "_preset", None), "m_rate", 0.85) or (state.get("m_rate", 0.85) if isinstance(state, dict) else 0.85)),
            m_rel=float(payload.get("relative_trigger_ratio") or 0.7),
        )
        layer_status = gate.evaluate(
            alpha_q_v=float(payload.get("signal") or 0.0),
            theta_min=_finite_or_none(payload.get("theta_min")),
            rolling_accuracy=float(payload.get("q") or 0.0),
            baseline=float(payload.get("baseline_q") or 0.0),
            verified_outcomes=outcomes,
            base_status=str(payload.get("status") or "GREEN"),
        )
        payload.update(layer_status)
        mode = str(payload.get("conservation_mode") or "normal")
        if mode == "cold_start":
            payload.update({"status": "COLD_START", "passed": True})
        elif mode == "bootstrap":
            payload.update({"status": "BOOTSTRAP", "passed": True})
        gate_status = str(layer_status.get("status") or "GREEN")
        gate_active = any(
            isinstance(details, dict) and details.get("active") is True
            for name, details in layer_status.items()
            if name.startswith("g_")
        )
        if gate_active and gate_status in {"AMBER", "RED"}:
            if gate_status == "RED":
                reason = "Gate RED"
            else:
                active_layers = [
                    name.upper()
                    for name, details in layer_status.items()
                    if name.startswith("g_")
                    and isinstance(details, dict)
                    and details.get("active") is True
                ]
                reason = "/".join(active_layers) + " active" if active_layers else "Gate AMBER"
            payload.update({"status": gate_status, "passed": False, "reason": reason})
        if projection_provider is not None:
            # Projection is explanatory only; it must never change gate fields.
            try:
                projection = projection_provider(int(payload.get("verified_count") or 0))
            except (ValueError, TypeError):
                projection = {"projected_divergence_week": None, "readiness_score": None,
                              "evidence_label": "INVALID_PROJECTION_INPUTS"}
            for key in ("projected_divergence_week", "readiness_score", "evidence_label",
                        "projection_definition", "projection_inputs", "projected_weekly_net_benefit",
                        "projection_status", "projection_tier", "readiness_definition"):
                if key in projection:
                    payload[key] = projection[key]
        return payload

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
