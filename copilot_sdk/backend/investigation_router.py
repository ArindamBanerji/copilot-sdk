"""FastAPI router factory for VLD investigation."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from copilot_sdk.scoring.investigation import KUtilityStore, VLDInvestigator
from copilot_sdk.scoring.situation_classifier import SituationClassifier


class InvestigationRequest(BaseModel):
    decision_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    factor_vector: list[float] = Field(min_length=1)
    budget: int | None = None
    use_K: bool = True


class InvestigationResponse(BaseModel):
    decision_id: str
    category: str
    budget_used: int
    situation: str = ""
    situation_confidence: float = 0.0
    surface_action: int
    surface_margin: float
    final_action: int
    final_margin: float
    action_changed: bool
    steps: list[dict[str, Any]]
    contrast: dict[str, Any]
    snapshot: dict[str, Any] = Field(default_factory=dict)
    halt_reason: str = ""
    evidence_available: bool = True
    degraded: bool = False
    failed_providers: list[str] = Field(default_factory=list)


def create_investigation_router(
    scorer_provider: Callable[[], Any],
    evidence_provider_factory: Callable[[str], Any],
    k_store: KUtilityStore | None = None,
    classifier: SituationClassifier | None = None,
    factor_names: list[str] | None = None,
    default_budget: int = 2,
    gated_sources: set[str] | None = None,
    delta: float = 0.01,
    max_flips: int = 2,
    conservation_status: str = "not_evaluated_read_only",
) -> APIRouter:
    """Create the domain-parametric VLD investigation router."""

    router = APIRouter(prefix="/api/investigation")

    @router.post("/investigate", response_model=InvestigationResponse)
    def investigate(request: InvestigationRequest) -> dict[str, Any]:
        try:
            scorer = scorer_provider()
            centroid_tensor = _read_centroid_tensor(scorer)
            mu = _action_centroids_from_tensor(scorer, centroid_tensor, request.category)
            sigma = _read_sigma(scorer, mu.shape[1])
            names = list(factor_names or _read_factor_names(scorer, mu.shape[1]))
            tau = _read_tau(scorer)
            action_names = _read_action_names(scorer, mu.shape[0])
            investigator = VLDInvestigator(mu, sigma, names, tau=tau, action_names=action_names)
            v = np.asarray(request.factor_vector, dtype=np.float64)
            score_fn = _make_score_fn(scorer, names, centroid_tensor, tau)
            _, p_surface, _surface_margin = investigator.predict(v, request.category, score_fn)
            q_surface = investigator.compute_Q(v, p_surface)
            situation = None
            situation_confidence = None
            budget = request.budget
            if budget is None and classifier is not None:
                assessment = classifier.classify(v, mu, sigma, p_surface, q_surface, default_budget=default_budget)
                situation = assessment.situation
                situation_confidence = assessment.confidence
                budget = assessment.recommended_budget
            if budget is None:
                budget = default_budget
            k_weights = None
            if request.use_K and k_store is not None:
                k_weights = k_store.get_weights(request.category)
            evidence_provider = evidence_provider_factory(request.decision_id)
            trace = investigator.investigate(
                request.decision_id,
                request.category,
                v,
                evidence_provider,
                budget=int(budget),
                K_weights=k_weights,
                gated_sources=gated_sources,
                score_fn=score_fn,
                delta=delta,
                max_flips=max_flips,
                conservation_status=conservation_status,
            )
            action_changed = trace.surface_action != trace.final_action
            faithful_contrast = dict(trace.contrast or {})
            contrast = {
                "sp_action": trace.surface_action,
                "sp_margin": trace.surface_margin,
                "vld_action": trace.final_action,
                "vld_margin": trace.final_margin,
                "improved": trace.final_margin > trace.surface_margin,
                "single_pass": faithful_contrast,
            }
            for key, value in faithful_contrast.items():
                contrast.setdefault(key, value)
            return {
                "decision_id": trace.decision_id,
                "category": trace.category,
                "budget_used": trace.budget,
                "situation": situation or "",
                "situation_confidence": float(situation_confidence or 0.0),
                "surface_action": trace.surface_action,
                "surface_margin": trace.surface_margin,
                "final_action": trace.final_action,
                "final_margin": trace.final_margin,
                "action_changed": action_changed,
                "steps": [
                    {
                        **asdict(step),
                        "evidence_value": float(step.evidence_value or 0.0),
                        "halt_reason": step.halt_reason or "",
                    }
                    for step in trace.steps
                ],
                "contrast": contrast,
                "snapshot": (
                    {**trace.snapshot.public_dict(), "k_weights": (
                        trace.snapshot.public_dict().get("k_weights") or []
                    )}
                    if trace.snapshot is not None else {}
                ),
                "halt_reason": trace.halt_reason or "",
                "evidence_available": trace.evidence_available,
                "degraded": trace.degraded,
                "failed_providers": list(trace.failed_providers),
            }
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Investigation unavailable: {exc}") from exc

    @router.get("/health")
    def health() -> dict[str, Any]:
        return {
            "investigation_available": True,
            "classifier_loaded": bool(classifier.is_available) if classifier is not None else False,
            "k_store_available": k_store is not None,
            "default_budget": int(default_budget),
            "delta": float(delta),
            "max_flips": int(max_flips),
        }

    return router


def _make_score_fn(
    scorer: Any,
    factor_names: list[str],
    frozen_centroids: np.ndarray | None = None,
    tau: float | None = None,
):
    if not hasattr(scorer, "score_read_only") and not hasattr(scorer, "score_with_model_state"):
        return None
    frozen = None if frozen_centroids is None else np.asarray(frozen_centroids, dtype=np.float64).copy()

    def score_fn(factors: np.ndarray, category: str) -> dict[str, Any]:
        vector = np.asarray(factors, dtype=np.float64)
        factor_dict = {name: float(vector[index]) for index, name in enumerate(factor_names)}
        if frozen is not None and hasattr(scorer, "score_with_model_state"):
            result = scorer.score_with_model_state(frozen, factor_dict, category, temperature=tau)
        else:
            result = scorer.score_read_only(factor_dict, category)
        if isinstance(result, dict):
            probabilities = result.get("probabilities") or result.get("action_probabilities")
            action_index = result.get("action_index")
            margin = result.get("margin")
        else:
            probabilities = getattr(result, "probabilities", None)
            action_index = getattr(result, "action_index", None)
            margin = getattr(result, "margin", None)
        return {
            "action_index": action_index,
            "probabilities": probabilities,
            "margin": margin,
        }

    return score_fn


def _read_underlying_scorer(scorer: Any) -> Any:
    gae = getattr(scorer, "gae_scorer", None)
    if gae is not None:
        return gae
    return getattr(scorer, "_scorer", scorer)


def _read_centroid_tensor(scorer: Any) -> np.ndarray:
    source = _read_underlying_scorer(scorer)
    centroids = getattr(source, "centroids", None)
    if centroids is None:
        centroids = getattr(source, "mu", None)
    if centroids is None:
        raise ValueError("scorer does not expose centroids or mu")
    return np.asarray(centroids, dtype=np.float64).copy()


def _read_action_centroids(scorer: Any, category: str) -> np.ndarray:
    return _action_centroids_from_tensor(scorer, _read_centroid_tensor(scorer), category)


def _action_centroids_from_tensor(scorer: Any, mu: np.ndarray, category: str) -> np.ndarray:
    if mu.ndim == 2:
        return np.asarray(mu, dtype=np.float64).copy()
    if mu.ndim != 3:
        raise ValueError("scorer centroids must have shape (actions, factors) or (categories, actions, factors)")
    idx = _category_index(scorer, category, mu.shape[0])
    return np.asarray(mu[idx], dtype=np.float64).copy()


def _category_index(scorer: Any, category: str, n_categories: int) -> int:
    for owner in (scorer, _read_underlying_scorer(scorer), getattr(scorer, "_preset", None)):
        if owner is None:
            continue
        for attr in ("categories", "category_names"):
            values = getattr(owner, attr, None)
            if values is not None and category in list(values):
                return list(values).index(category)
        mappings = getattr(owner, "category_indices", None)
        if isinstance(mappings, dict) and category in mappings:
            return int(mappings[category])
    try:
        idx = int(category)
    except ValueError:
        idx = 0
    return max(0, min(n_categories - 1, idx))


def _read_sigma(scorer: Any, d: int) -> np.ndarray:
    for owner in (scorer, _read_underlying_scorer(scorer)):
        for attr in ("sigma", "_sigma"):
            value = getattr(owner, attr, None)
            if value is not None:
                arr = np.asarray(value, dtype=np.float64)
                if arr.shape == (d,):
                    return arr.copy()
    return np.ones(d, dtype=np.float64)


def _read_factor_names(scorer: Any, d: int) -> list[str]:
    for owner in (scorer, getattr(scorer, "_preset", None), _read_underlying_scorer(scorer)):
        if owner is None:
            continue
        values = getattr(owner, "factor_names", None) or getattr(owner, "factors", None)
        if values is not None and len(list(values)) == d:
            return [str(v) for v in values]
    return [f"factor_{i}" for i in range(d)]


def _read_action_names(scorer: Any, n_actions: int) -> list[str]:
    for owner in (scorer, getattr(scorer, "_preset", None), _read_underlying_scorer(scorer)):
        if owner is None:
            continue
        values = getattr(owner, "action_names", None) or getattr(owner, "actions", None)
        shape = getattr(owner, "shape", None)
        if values is None and shape is not None:
            values = getattr(shape, "action_names", None)
        if values is not None and len(list(values)) == n_actions:
            return [str(v) for v in values]
    return [f"action_{i}" for i in range(n_actions)]


def _read_tau(scorer: Any) -> float:
    for owner in (scorer, _read_underlying_scorer(scorer), getattr(scorer, "_preset", None)):
        if owner is None:
            continue
        value = getattr(owner, "tau", None) or getattr(owner, "temperature", None)
        if value is not None:
            return float(value)
    return 0.1


__all__ = ["create_investigation_router"]
