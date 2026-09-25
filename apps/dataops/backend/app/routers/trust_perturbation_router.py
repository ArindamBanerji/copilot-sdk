"""Reversible, demo-labelled source trust perturbations for DataOps."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from copilot_sdk.backend.conservation_utils import compute_conservation_status_payload


DOMAIN = "dataops"
SOURCE_FACTORS = {
    "sap_s4hana": "source_reliability",
    "sap_s4hana_extract": "source_reliability",
    "celonis": "recurrence_frequency",
    "celonis_p2p": "recurrence_frequency",
    "snowflake": "source_reliability",
    "airflow": "data_freshness",
    "dbt": "downstream_urgency",
}


class TrustPerturbRequest(BaseModel):
    source_id: str = Field(min_length=1)
    perturbation_type: Literal["degrade", "improve"]
    magnitude: float = Field(default=0.15, ge=0.05, le=0.30)
    decisions: int = Field(default=5, ge=1, le=50)


class TrustResetRequest(BaseModel):
    source_id: str = Field(min_length=1)


@dataclass
class _SourceTrustState:
    baseline: float
    current: float


class SourceTrustPerturbationService:
    """Keep a reversible, in-memory overlay for an explicitly simulated demo."""

    def __init__(self) -> None:
        self._sources: dict[str, _SourceTrustState] = {}

    def perturb(
        self,
        *,
        source_id: str,
        perturbation_type: str,
        magnitude: float,
        decisions: int,
        scorer: Any,
    ) -> dict[str, Any]:
        factor_name = _factor_for_source(source_id)
        state = self._sources.get(source_id)
        if state is None:
            baseline = _trust_from_scorer(scorer, factor_name)
            state = _SourceTrustState(baseline=baseline, current=baseline)
            self._sources[source_id] = state

        before = state.current
        direction = -1.0 if perturbation_type == "degrade" else 1.0
        state.current = round(max(0.0, min(1.0, before + direction * magnitude)), 3)
        return {
            "source_id": source_id,
            "factor_name": factor_name,
            "trust_before": before,
            "trust_after": state.current,
            "decisions_injected": decisions,
            "simulated_verified_outcomes": decisions,
            "simulation": True,
            "learning_mode": "reversible_demo_overlay",
        }

    def reset(self, *, source_id: str, scorer: Any) -> dict[str, Any]:
        factor_name = _factor_for_source(source_id)
        state = self._sources.pop(source_id, None)
        baseline = state.baseline if state is not None else _trust_from_scorer(scorer, factor_name)
        return {
            "source_id": source_id,
            "trust_reset_to": baseline,
            "simulation": True,
            "learning_mode": "reversible_demo_overlay",
        }


def create_trust_perturbation_router(
    *,
    scorer_provider: Callable[[], Any],
    service: SourceTrustPerturbationService,
) -> APIRouter:
    router = APIRouter()

    @router.post("/trust/perturb")
    def perturb(request: TrustPerturbRequest) -> dict[str, Any]:
        try:
            scorer = scorer_provider()
            result = service.perturb(
                source_id=_source_id(request.source_id),
                perturbation_type=request.perturbation_type,
                magnitude=request.magnitude,
                decisions=request.decisions,
                scorer=scorer,
            )
            result["conservation_status"] = _conservation_status(scorer)
            return result
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/trust/reset")
    def reset(request: TrustResetRequest) -> dict[str, Any]:
        try:
            scorer = scorer_provider()
            result = service.reset(source_id=_source_id(request.source_id), scorer=scorer)
            result["conservation_status"] = _conservation_status(scorer)
            return result
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router


def _source_id(source_id: str) -> str:
    return source_id.strip().lower().replace("-", "_").replace(" ", "_")


def _factor_for_source(source_id: str) -> str:
    factor_name = SOURCE_FACTORS.get(source_id)
    if factor_name is None:
        raise ValueError(f"Unknown DataOps source: {source_id}")
    return factor_name


def _trust_from_scorer(scorer: Any, factor_name: str) -> float:
    fingerprint = scorer.fingerprint()
    raw_factors = fingerprint.get("factors", []) if isinstance(fingerprint, dict) else getattr(fingerprint, "factors", [])
    for factor in raw_factors or []:
        name = factor.get("name") if isinstance(factor, dict) else getattr(factor, "name", None)
        if name != factor_name:
            continue
        raw_weight = factor.get("weight", factor.get("dk_weight", 0.0)) if isinstance(factor, dict) else getattr(factor, "weight", getattr(factor, "dk_weight", 0.0))
        return round(max(0.0, min(1.0, float(raw_weight))), 3)
    raise ValueError(f"Trust factor unavailable for source: {factor_name}")


def _conservation_status(scorer: Any) -> str:
    try:
        store = getattr(scorer, "graph_store", None)
        return str(compute_conservation_status_payload(DOMAIN, store).get("status", "UNAVAILABLE"))
    except Exception:
        return "UNAVAILABLE"
