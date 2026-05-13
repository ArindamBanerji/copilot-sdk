"""FastAPI scoring router factory backed by copilot_sdk.scoring."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Callable

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from copilot_sdk.scoring import CompoundingScorer


ENGINE = {
    "scoring": "copilot_sdk.scoring.CompoundingScorer",
    "gae": "gae.profile_scorer.ProfileScorer",
}


class ScoreRequest(BaseModel):
    category: str
    factors: dict[str, float] = Field(default_factory=dict)
    context: dict[str, Any] | None = None


class LearnRequest(BaseModel):
    decision_id: str
    actual_action: str
    outcome: str = "confirmed"
    context: dict[str, Any] | None = None


def create_scoring_router(
    domain: str,
    db_path: str | None = None,
    scorer_factory: Callable[..., Any] | None = None,
) -> APIRouter:
    """Create a domain-parametric scoring router."""

    router = APIRouter()
    scorer_cache: dict[str, Any] = {}

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

    @router.post("/score")
    def score(request: ScoreRequest) -> dict[str, Any]:
        scorer = get_scorer()
        try:
            result = scorer.score(request.factors, request.category)
        except AssertionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        payload = _json_safe(result)
        payload["engine"] = ENGINE
        return payload

    @router.post("/learn")
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
        payload["reward"] = reward
        payload["previous_reward"] = previous_reward
        payload["reward_multiplier"] = _reward_multiplier(reward, previous_reward)
        payload["engine"] = ENGINE
        return payload

    @router.get("/fingerprint")
    def fingerprint() -> dict[str, Any]:
        scorer = get_scorer()
        payload = _json_safe(scorer.fingerprint())
        payload["engine"] = ENGINE
        return payload

    @router.get("/trajectory")
    def trajectory() -> dict[str, Any]:
        scorer = get_scorer()
        payload = _json_safe(scorer.trajectory())
        payload["engine"] = ENGINE
        return payload

    @router.get("/health")
    def health() -> dict[str, Any]:
        scorer = get_scorer()
        return {
            "phase": scorer.get_phase(),
            "alpha": scorer.get_alpha(),
            "engine": ENGINE,
        }

    @router.get("/history")
    def history() -> dict[str, Any]:
        scorer = get_scorer()
        store = _scorer_data_store(scorer)
        get_decisions = getattr(store, "get_decisions", None)
        if callable(get_decisions):
            decisions = get_decisions(limit=10**12)
        else:
            get_all = getattr(store, "get_all_decisions", None)
            decisions = get_all() if callable(get_all) else []
        return {"engine": ENGINE, "decisions": _json_safe(decisions)}

    return router


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
    for name in ("graph_store", "_graph_store", "store", "_store"):
        store = getattr(scorer, name, None)
        if store is not None:
            return store
    return None


def _previous_reward(context: dict[str, Any]) -> float | None:
    if "previous_reward" not in context:
        return None
    return float(context.get("previous_reward") or 0.0)


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
