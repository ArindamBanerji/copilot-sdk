"""Shared counterfactual scoring endpoint."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from copilot_sdk.evidence.provenance import Provenanced
from copilot_sdk.scoring import CompoundingScorer


class CounterfactualRequest(BaseModel):
    base_factors: dict[str, Any] = Field(default_factory=dict)
    perturbed_factors: dict[str, Any] = Field(default_factory=dict)
    category: str


class CounterfactualResponse(BaseModel):
    """Successful counterfactual scoring response."""

    model_config = ConfigDict(extra="allow")

    base_score: float | None = None
    perturbed_score: float | None = None
    delta: float | None = None
    perturbed_factor: str | None = None
    base_action: str | None = None
    perturbed_action: str | None = None
    provenance: str | None = None


def create_counterfactual_router(
    domain: str,
    *,
    prefix: str,
    scorer_provider: Callable[[], Any] | None = None,
    profile: str = "production",
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[f"{domain}-counterfactual"])
    scorer_cache: dict[str, CompoundingScorer] = {}

    def get_scorer() -> Any:
        if scorer_provider is not None:
            return scorer_provider()
        scorer = scorer_cache.get(domain)
        if scorer is None:
            scorer = CompoundingScorer.from_preset(domain, profile=profile)
            scorer_cache[domain] = scorer
        return scorer

    @router.post("/counterfactual", response_model=CounterfactualResponse)
    def counterfactual(request: CounterfactualRequest):
        try:
            base_factors = _coerce_factors(request.base_factors)
            perturbed_factors = _coerce_factors(request.perturbed_factors)
            scorer = get_scorer()
            base_result = scorer.score_read_only(base_factors, request.category)
            perturbed_result = scorer.score_read_only(perturbed_factors, request.category)
        except ValueError as exc:
            message = str(exc)
            if "F-22" in message or "sample-provenance" in message:
                return JSONResponse(
                    status_code=422,
                    content={"error": message, "rejected": True},
                )
            return JSONResponse(
                status_code=400,
                content={"error": message, "rejected": False},
            )

        base_score = float(getattr(base_result, "confidence", 0.0))
        perturbed_score = float(getattr(perturbed_result, "confidence", 0.0))
        return {
            "base_score": round(base_score, 4),
            "perturbed_score": round(perturbed_score, 4),
            "delta": round(perturbed_score - base_score, 4),
            "perturbed_factor": _changed_factor(base_factors, perturbed_factors),
            "base_action": getattr(base_result, "action", None),
            "perturbed_action": getattr(perturbed_result, "action", None),
            "provenance": "learned",
        }

    return router


def _coerce_factors(raw: dict[str, Any]) -> dict[str, Any]:
    factors: dict[str, Any] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            source = str(value.get("provenance") or value.get("source") or "")
            raw_value = value.get("value")
            if source == "sample":
                factors[key] = Provenanced(raw_value, source="sample")
                continue
            value = raw_value
        factors[key] = float(value)
    return factors


def _changed_factor(base: dict[str, Any], perturbed: dict[str, Any]) -> str | None:
    for key, value in perturbed.items():
        if key not in base:
            return key
        try:
            if float(base[key]) != float(value):
                return key
        except (TypeError, ValueError):
            if base[key] != value:
                return key
    return None
