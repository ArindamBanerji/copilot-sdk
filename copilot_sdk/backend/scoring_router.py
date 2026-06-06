"""FastAPI scoring router factory backed by copilot_sdk.scoring."""

from __future__ import annotations

import inspect
import logging
import threading
from dataclasses import asdict, is_dataclass
from typing import Any, Callable

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from copilot_sdk.backend.conservation_utils import compute_conservation_metrics
from copilot_sdk.backend.models import (
    FingerprintResponse,
    LearnResponse,
    ScoreResponse,
    ScoringHealthResponse,
    ScoringHistoryResponse,
    TrajectoryResponse,
)
from copilot_sdk.scoring import CompoundingScorer


ENGINE = {
    "scoring": "copilot_sdk.scoring.CompoundingScorer",
    "gae": "gae.profile_scorer.ProfileScorer",
}
log = logging.getLogger(__name__)


class ScoreRequest(BaseModel):
    category: str
    factors: dict[str, float] = Field(default_factory=dict)
    context: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class LearnRequest(BaseModel):
    decision_id: str
    actual_action: str
    outcome: str = "confirmed"
    context: dict[str, Any] | None = None


def create_scoring_router(
    domain: str,
    db_path: str | None = None,
    scorer_factory: Callable[..., Any] | None = None,
    learning_store: Any | None = None,
) -> APIRouter:
    """Create a domain-parametric scoring router."""

    router = APIRouter()
    scorer_cache: dict[str, Any] = {}
    l5_conservation_lock = threading.RLock()

    def get_scorer() -> Any:
        if "scorer" not in scorer_cache:
            try:
                scorer_cache["scorer"] = (
                    scorer_factory()
                    if scorer_factory is not None
                    else CompoundingScorer.from_preset(domain, db_path=db_path)
                )
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            except Exception as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"Could not initialize scorer for domain {domain!r}",
                ) from exc
        return scorer_cache["scorer"]

    @router.post("/score", response_model=ScoreResponse)
    def score(request: ScoreRequest) -> dict[str, Any]:
        scorer = get_scorer()
        try:
            result = _score_with_optional_metadata(scorer, request)
        except AssertionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        payload = _json_safe(result)
        payload["engine"] = ENGINE
        return payload

    @router.post("/learn", response_model=LearnResponse)
    def learn(request: LearnRequest) -> dict[str, Any]:
        scorer = get_scorer()
        try:
            decision = _get_decision(scorer, request.decision_id)
            is_correct = request.actual_action == decision.get("recommended_action")
            reward = _signed_reward(
                domain=domain,
                scorer=scorer,
                decision=decision,
                outcome=request.outcome,
                context=request.context or {},
                is_correct=is_correct,
            )
            previous_reward = _previous_reward(request.context or {})
            result = scorer.learn(
                request.decision_id,
                request.actual_action,
                request.outcome,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown decision: {request.decision_id}") from exc
        except AssertionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        payload = _json_safe(result)
        _shape_learn_payload(
            payload,
            request=request,
            decision=decision,
        )
        payload["reward"] = reward
        payload["previous_reward"] = previous_reward
        payload["reward_multiplier"] = _reward_multiplier(reward, previous_reward)
        payload["engine"] = ENGINE
        _persist_conservation_state_l5(
            domain=domain,
            scorer=scorer,
            explicit_learning_store=learning_store,
            caused_by_decision_id=request.decision_id,
            persistence_lock=l5_conservation_lock,
        )
        return payload

    @router.get("/fingerprint", response_model=FingerprintResponse)
    def fingerprint() -> dict[str, Any]:
        scorer = get_scorer()
        payload = _json_safe(scorer.fingerprint())
        payload["engine"] = ENGINE
        return payload

    @router.get("/trajectory", response_model=TrajectoryResponse)
    def trajectory() -> dict[str, Any]:
        scorer = get_scorer()
        payload = _json_safe(scorer.trajectory())
        payload["engine"] = ENGINE
        return payload

    @router.get("/health", response_model=ScoringHealthResponse)
    def health() -> dict[str, Any]:
        scorer = get_scorer()
        return {
            "phase": scorer.get_phase(),
            "alpha": scorer.get_alpha(),
            "engine": ENGINE,
        }

    @router.get("/history", response_model=ScoringHistoryResponse)
    def history() -> dict[str, Any]:
        scorer = get_scorer()
        store = _scorer_data_store(scorer)
        store_domain = _store_domain(store, domain)
        get_decisions = getattr(store, "get_decisions", None)
        if callable(get_decisions):
            decisions = get_decisions(store_domain, limit=10**12)
        else:
            get_all = getattr(store, "get_all_decisions", None)
            decisions = get_all(store_domain) if callable(get_all) else []
        return {"engine": ENGINE, "decisions": _json_safe(decisions)}

    return router


def _score_with_optional_metadata(scorer: Any, request: ScoreRequest) -> Any:
    metadata = request.metadata or None
    score = scorer.score
    if metadata and _score_accepts_metadata(score):
        return score(request.factors, request.category, metadata=metadata)
    return score(request.factors, request.category)


def _score_accepts_metadata(score: Any) -> bool:
    try:
        parameters = inspect.signature(score).parameters
    except (TypeError, ValueError):
        return False
    if "metadata" in parameters:
        return True
    return any(param.kind is inspect.Parameter.VAR_KEYWORD for param in parameters.values())


def compute_reward(
    domain: str,
    factors: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> float:
    """Compute a bounded domain reward from router-visible data."""

    context = context or {}
    domain_key = domain.lower()

    if domain_key == "trading":
        reward = (
            _number(factors.get("position_size"))
            * _number(factors.get("research_depth"))
            * _number(factors.get("time_horizon"))
        )
    elif domain_key == "purchasing":
        if "stockout_revenue_loss" in context:
            reward = _number(context.get("stockout_revenue_loss")) / 1000.0
        elif "waste_cost" in context:
            reward = _number(context.get("waste_cost")) / 1000.0
        else:
            reward = _number(factors.get("expected_demand")) * _number(
                factors.get("historical_waste")
            )
            if reward == 0.0:
                reward = 0.05
    elif domain_key == "dataops":
        reward = _number(factors.get("business_criticality")) * _number(
            factors.get("impact_scope")
        )
    else:
        reward = 0.0

    return round(_clamp(reward), 6)


def _signed_reward(
    *,
    domain: str,
    scorer: Any,
    decision: dict[str, Any],
    outcome: str,
    context: dict[str, Any],
    is_correct: bool,
) -> float:
    preset = getattr(scorer, "_preset", None)
    compute = getattr(preset, "compute_reward", None)
    if callable(compute):
        reward = float(compute(decision, outcome, context))
        reward = _clamp(reward)
    else:
        reward = compute_reward(domain, decision.get("factors", {}), context)
    return round(reward if is_correct else -reward, 6)


def _get_decision(scorer: Any, decision_id: str) -> dict[str, Any]:
    store = _scorer_data_store(scorer)
    get_decision = getattr(store, "get_decision", None)
    if not callable(get_decision):
        raise KeyError(decision_id)
    decision = get_decision(decision_id)
    if decision is None:
        raise KeyError(decision_id)
    return dict(decision)


def _scorer_data_store(scorer: Any) -> Any:
    for name in ("graph_store", "_graph_store"):
        store = getattr(scorer, name, None)
        if store is not None:
            return store
    return None


def _store_domain(store: Any, fallback: str) -> str:
    return str(getattr(store, "domain", "") or fallback)


def _persist_conservation_state_l5(
    *,
    domain: str,
    scorer: Any,
    explicit_learning_store: Any | None = None,
    caused_by_decision_id: str | None = None,
    persistence_lock: threading.RLock | None = None,
) -> None:
    store = _learning_store_for(scorer, explicit_learning_store)
    if store is None:
        return None
    lock = persistence_lock or threading.RLock()
    with lock:
        return _persist_conservation_state_l5_locked(
            domain=domain,
            scorer=scorer,
            store=store,
            caused_by_decision_id=caused_by_decision_id,
        )


def _persist_conservation_state_l5_locked(
    *,
    domain: str,
    scorer: Any,
    store: Any,
    caused_by_decision_id: str | None = None,
) -> None:
    try:
        metrics = compute_conservation_metrics(scorer, domain=domain)
    except Exception as exc:  # pragma: no cover - exercised through caller behavior
        log.warning("L5 conservation state skipped for %s: %s", domain, exc)
        return None
    try:
        old_state = store.get_conservation_state(domain)
    except Exception as exc:
        log.warning("L5 conservation state read failed for %s: %s", domain, exc)
        return None
    old_status = None
    if isinstance(old_state, dict):
        stored_status = old_state.get("status")
        old_status = None if stored_status is None else str(stored_status)
    try:
        store.update_conservation_state(
            domain=domain,
            status=str(metrics["status"]),
            alpha=float(metrics["alpha"]),
            q=float(metrics["q"]),
            V=int(metrics["V"]),
            theta_min=float(metrics["theta_min"]),
            product=float(metrics["product"]),
            categories_total=int(metrics["categories_total"]),
            categories_with_data=int(metrics["categories_with_data"]),
            baseline_product=float(metrics["baseline_product"]),
            relative_threshold=float(metrics["relative_threshold"]),
            complacency_flag=str(metrics["complacency_flag"]),
            caused_by_decision_id=caused_by_decision_id,
            old_status=old_status,
        )
    except Exception as exc:
        log.warning("L5 conservation state write failed for %s: %s", domain, exc)
    return None


def _learning_store_for(scorer: Any, explicit_learning_store: Any | None = None) -> Any | None:
    candidates = [
        explicit_learning_store,
        getattr(scorer, "learning_store", None),
        getattr(scorer, "_learning_store", None),
        _scorer_data_store(scorer),
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        if callable(getattr(candidate, "get_conservation_state", None)) and callable(
            getattr(candidate, "update_conservation_state", None)
        ):
            return candidate
    return None


def _previous_reward(context: dict[str, Any]) -> float | None:
    if "previous_reward" not in context:
        return None
    return float(context.get("previous_reward") or 0.0)


def _shape_learn_payload(
    payload: dict[str, Any],
    *,
    request: LearnRequest,
    decision: dict[str, Any],
) -> None:
    paused = str(payload.get("status", "")).lower() == "paused"
    action = decision.get("recommended_action") or decision.get("action")
    confidence = decision.get("confidence")
    if paused:
        payload.setdefault("decision_id", request.decision_id)
        payload.setdefault("iks_before", 0.0)
        payload.setdefault("iks_after", 0.0)
        payload.setdefault("centroid_delta", 0.0)
        payload.setdefault("decisions_total", int(payload.get("verified_count") or 0))
        payload.setdefault("outcome", request.outcome)
        payload["paused"] = True
        payload["pause_reason"] = str(payload.get("reason") or "conservation_paused")
        payload["centroid_updated"] = False
    else:
        payload.setdefault("paused", False)
        payload.setdefault("centroid_updated", True)
    if action is not None:
        payload.setdefault("action", str(action))
    if confidence is not None:
        payload.setdefault("confidence", float(confidence))


def _reward_multiplier(reward: float, previous_reward: float | None) -> float:
    if previous_reward is not None and previous_reward > 0:
        return round(reward / previous_reward, 6)
    return 1.0


def _number(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not np.isfinite(number):
        return 0.0
    return number


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 1.0))


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value
