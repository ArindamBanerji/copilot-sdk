"""FastAPI scoring router factory backed by copilot_sdk.scoring."""

from __future__ import annotations

import inspect
import logging
import math
import os
import threading
from dataclasses import asdict, is_dataclass
from typing import Any, Callable

import numpy as np
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from copilot_sdk.backend.conservation_utils import compute_conservation_metrics
from copilot_sdk.backend.diagnostics_models import build_diagnostics
from copilot_sdk.backend.models import (
    FingerprintResponse,
    LearnResponse,
    MeasurementStateResponse,
    ScoreResponse,
    ScoringHealthResponse,
    ScoringHistoryResponse,
    TrajectoryResponse,
)
from copilot_sdk.scoring import CompoundingScorer
from copilot_sdk.scoring.dk_persistence import (
    DKWelfordTracker,
    persist_dk_after_reestimate,
)
from copilot_sdk.scoring.measurement_state import compute_measurement_state
from copilot_sdk.scoring.mutation_lock import mutation_lock_scope
from copilot_sdk.state.invalidation import apply_cache_invalidation_event
from copilot_sdk.state.cached_static import cached_static


ENGINE = {
    "scoring": "copilot_sdk.scoring.CompoundingScorer",
    "gae": "gae.profile_scorer.ProfileScorer",
}
log = logging.getLogger(__name__)


def _require_graph_store(scorer: Any, domain: str) -> Any:
    """Reject a scorer that cannot persist or read governed graph state."""
    store = getattr(scorer, "graph_store", None)
    if store is None:
        store = getattr(scorer, "_graph_store", None)
    if store is None:
        raise HTTPException(
            status_code=503,
            detail=f"Graph store unavailable for domain {domain!r}",
        )
    return store


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


_MUTABLE_CONTEXT_TOKENS = {
    "decision",
    "decisions",
    "outcome",
    "outcomes",
    "reward",
    "correct",
    "conservation",
    "dk",
    "l5",
    "verified",
}


def _stable_context(value: Any) -> Any:
    """Return a JSON-like context snapshot without mutable authority state."""
    if isinstance(value, dict):
        return {
            str(key): _stable_context(item)
            for key, item in value.items()
            if not any(token in str(key).lower() for token in _MUTABLE_CONTEXT_TOKENS)
        }
    if isinstance(value, list):
        return [_stable_context(item) for item in value]
    if isinstance(value, tuple):
        return [_stable_context(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _context_identifier(domain: str, category: str, context: Any) -> str:
    """Build a stable cache identity without using decision identifiers."""
    import hashlib
    import json

    if isinstance(context, dict):
        for name in (
            "ticker",
            "symbol",
            "supplier_id",
            "supplier",
            "pipeline_id",
            "source_id",
            "entity_id",
        ):
            value = context.get(name)
            if value not in (None, ""):
                return str(value)
    encoded = json.dumps(
        {"domain": domain, "category": category, "context": context},
        sort_keys=True,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:24]


def create_scoring_router(
    domain: str,
    db_path: str | None = None,
    scorer_factory: Callable[..., Any] | None = None,
    learning_store: Any | None = None,
    dk_welford_tracker: DKWelfordTracker | None = None,
    profile: str = "production",
    query_cache_invalidator: Callable[[], None] | None = None,
    outcome_recorder: Callable[[dict[str, Any], bool], None] | None = None,
    variant_selector: Callable[[str], str | None] | None = None,
    entity_context_cache: Any | None = None,
) -> APIRouter:
    """Create a domain-parametric scoring router."""

    router = APIRouter()
    scorer_cache: dict[str, Any] = {}
    l5_conservation_lock = threading.RLock()
    l5_dk_lock = threading.RLock()
    l5_centroid_lock = threading.RLock()
    active_dk_welford_tracker = dk_welford_tracker or DKWelfordTracker()

    def get_scorer() -> Any:
        if "scorer" not in scorer_cache:
            try:
                scorer = (
                    scorer_factory()
                    if scorer_factory is not None
                    else CompoundingScorer.from_preset(
                        domain, db_path=db_path, profile=profile
                    )
                )
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            except Exception as exc:
                raise HTTPException(
                    status_code=503,
                    detail=f"Graph store unavailable for domain {domain!r}: {exc}",
                ) from exc
            _require_graph_store(scorer, domain)
            scorer_cache["scorer"] = scorer
        return scorer_cache["scorer"]

    async def load_stable_context(request: ScoreRequest) -> None:
        """Read-through cache only the stable context portion of a score request.

        Decisions, outcomes, conservation, DK, and L5 state are deliberately
        excluded by ``_stable_context``.  The scorer still receives the
        request's current values; cached values only fill stable context that
        is absent from a repeated request.
        """
        if entity_context_cache is None:
            return
        context = request.context or {}
        stable = _stable_context(context)
        identifier = _context_identifier(domain, request.category, stable)
        kind = {
            "trading": "instrument",
            "purchasing": "supplier",
            "dataops": "pipeline",
        }.get(domain, "entity")
        cached = await entity_context_cache.get_context(
            domain,
            kind,
            identifier,
            lambda: stable,
            source=f"{domain}.score_context",
        )
        if isinstance(cached, dict):
            request.context = {**cached, **context}

    @router.post("/score", response_model=ScoreResponse)
    async def score(request: ScoreRequest) -> dict[str, Any]:
        with mutation_lock_scope(domain):
            scorer = get_scorer()
            try:
                await load_stable_context(request)
                if variant_selector is not None:
                    selected_variant = variant_selector(request.category)
                    if selected_variant and not _decision_variant_id({"metadata": request.metadata or {}}):
                        request.metadata = {
                            **(request.metadata or {}),
                            "variant_id": str(selected_variant),
                        }
                result = _score_with_optional_metadata(scorer, request)
            except AssertionError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except Exception as exc:
                raise HTTPException(status_code=503, detail=f"Graph store unavailable: {exc}") from exc
            payload = _json_safe(result)
            payload["engine"] = ENGINE
            payload = _score_response_payload(payload)
            apply_cache_invalidation_event(domain, "score")
            if query_cache_invalidator is not None:
                query_cache_invalidator()
            return payload

    @router.post("/learn", response_model=LearnResponse)
    def learn(request: LearnRequest) -> dict[str, Any]:
        with mutation_lock_scope(domain):
            scorer = get_scorer()
            try:
                decision = _get_decision(scorer, request.decision_id, domain=domain)
                if str(decision.get("status") or "").lower() in {"confirmed", "overridden"}:
                    raise ValueError(
                        f"decision already has a verified outcome: {request.decision_id}"
                    )
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
                category = _decision_category(decision)
                pre_centroid = _read_centroid_for_l5(
                    scorer,
                    category=category,
                    action=request.actual_action,
                    logger=log,
                )
                result = scorer.learn(
                    request.decision_id,
                    request.actual_action,
                    request.outcome,
                    consolidate=bool((request.context or {}).get("consolidate")),
                    context=request.context,
                )
            except KeyError as exc:
                raise HTTPException(status_code=404, detail=f"Unknown decision: {request.decision_id}") from exc
            except AssertionError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except Exception as exc:
                raise HTTPException(status_code=503, detail=f"Graph store unavailable: {exc}") from exc

            if outcome_recorder is not None:
                outcome_recorder(
                    {
                        "decision_id": request.decision_id,
                        "category": category,
                        "variant_id": _decision_variant_id(decision),
                    },
                    bool(is_correct),
                )

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
            _persist_centroid_l5(
                domain=domain,
                scorer=scorer,
                explicit_learning_store=learning_store,
                category=category,
                actual_action=request.actual_action,
                caused_by_decision_id=request.decision_id,
                pre_centroid=pre_centroid,
                persistence_lock=l5_centroid_lock,
                logger=log,
            )
            # NOTE: L5 conservation persistence (update_conservation_state) coexists
            # with V2 conservation persistence (write_conservation_status) in the
            # scorer's _persist_learning_artifacts. They are different contracts:
            # L5 updates operational state; V2 writes a graph snapshot. Both are
            # intentional. Remove L5 only after V2 is proven sufficient and the
            # L5 contract is formally retired.
            _persist_conservation_state_l5(
                domain=domain,
                scorer=scorer,
                explicit_learning_store=learning_store,
                caused_by_decision_id=request.decision_id,
                persistence_lock=l5_conservation_lock,
            )
            _persist_dk_state_l5(
                domain=domain,
                scorer=scorer,
                explicit_learning_store=learning_store,
                decision=decision,
                actual_action=request.actual_action,
                payload=payload,
                welford_tracker=active_dk_welford_tracker,
                persistence_lock=l5_dk_lock,
            )
            apply_cache_invalidation_event(domain, "learn")
            if query_cache_invalidator is not None:
                query_cache_invalidator()
            return payload

    @router.get("/fingerprint", response_model=FingerprintResponse)
    @cached_static("fingerprint", copilot=domain)
    def fingerprint(request: Request) -> dict[str, Any]:
        scorer = get_scorer()
        payload = _json_safe(scorer.fingerprint())
        payload["engine"] = ENGINE
        return payload

    @router.get("/trajectory", response_model=TrajectoryResponse)
    def trajectory(request: Request) -> dict[str, Any]:
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

    @router.get("/diagnostics")
    def diagnostics(request: Request) -> dict[str, Any]:
        try:
            extras: dict[str, Any] = {}
            startup_status = getattr(request.app.state, "l5_startup_status", None)
            if isinstance(startup_status, dict):
                extras["l5_startup_status"] = dict(startup_status)
            if domain == "dataops":
                extras["active_graph_backend"] = os.environ.get("DATAOPS_ACTIVE_GRAPH_BACKEND", "unavailable")
                extras["active_config_source"] = "DATAOPS_ACTIVE_GRAPH_BACKEND" if os.environ.get("DATAOPS_ACTIVE_GRAPH_BACKEND") else "unavailable"
            scorer = get_scorer()
            result: dict[str, Any] = build_diagnostics(domain, scorer, scorer.graph_store, extras=extras)
            return result
        except Exception as exc:
            logger.exception("Diagnostics failed for %s", domain)
            result = build_diagnostics(domain, None, None, extras={"error": str(exc)})
            return result

    @router.get("/history", response_model=ScoringHistoryResponse)
    @cached_static("history-summary", copilot=domain)
    def history(request: Request) -> dict[str, Any]:
        scorer = get_scorer()
        store = _scorer_data_store(scorer)
        store_domain = _store_domain(store, domain)
        decisions = store.get_decisions(store_domain, limit=10**12)
        return {"engine": ENGINE, "decisions": _json_safe(decisions)}

    def measurement_payload() -> dict[str, Any]:
        scorer = get_scorer()
        payload = compute_measurement_state(scorer).to_dict()
        payload["engine"] = ENGINE
        return payload

    @router.get("/measurement-state", response_model=MeasurementStateResponse)
    @cached_static("measurement-state", copilot=domain)
    def measurement_state(request: Request) -> dict[str, Any]:
        return measurement_payload()

    @router.get("/{copilot}/measurement-state", response_model=MeasurementStateResponse)
    def prefixed_measurement_state(copilot: str) -> dict[str, Any]:
        if copilot != domain:
            raise HTTPException(status_code=404, detail=f"Unknown copilot: {copilot}")
        return measurement_payload()

    return router


def _decision_variant_id(decision: dict[str, Any]) -> str | None:
    for key in ("variant_id", "selected_variant_id", "evolution_variant_id"):
        value = decision.get(key)
        if value:
            return str(value)
    for container_key in ("metadata", "context", "factors"):
        container = decision.get(container_key)
        if isinstance(container, dict):
            value = _decision_variant_id(container)
            if value:
                return value
    return None


def create_measurement_state_router(
    domain: str,
    scorer_factory: Callable[[], Any],
) -> APIRouter:
    """Create a router that exposes only a domain's measurement state."""

    router = APIRouter()

    @router.get("/{copilot}/measurement-state", response_model=MeasurementStateResponse)
    def prefixed_measurement_state(copilot: str) -> dict[str, Any]:
        if copilot != domain:
            raise HTTPException(status_code=404, detail=f"Unknown copilot: {copilot}")
        payload = compute_measurement_state(scorer_factory()).to_dict()
        payload["engine"] = ENGINE
        return payload

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


def _get_decision(scorer: Any, decision_id: str, *, domain: str) -> dict[str, Any]:
    store = _scorer_data_store(scorer)
    decision = store.get_decision(decision_id, domain=domain)
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
    lock = persistence_lock or threading.RLock()
    with lock:
        if store is not None:
            _persist_conservation_state_l5_locked(
                domain=domain,
                scorer=scorer,
                store=store,
                caused_by_decision_id=caused_by_decision_id,
            )
    return None


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


def _dk_learning_store_for(scorer: Any, explicit_learning_store: Any | None = None) -> Any | None:
    candidates = [
        explicit_learning_store,
        getattr(scorer, "learning_store", None),
        getattr(scorer, "_learning_store", None),
        _scorer_data_store(scorer),
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        if callable(getattr(candidate, "update_dk_weights", None)):
            return candidate
    return None


def _centroid_learning_store_for(scorer: Any, explicit_learning_store: Any | None = None) -> Any | None:
    candidates = [
        explicit_learning_store,
        getattr(scorer, "learning_store", None),
        getattr(scorer, "_learning_store", None),
        _scorer_data_store(scorer),
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        if callable(getattr(candidate, "update_centroid", None)):
            return candidate
    return None


def _persist_centroid_l5(
    *,
    domain: str,
    scorer: Any,
    explicit_learning_store: Any | None,
    category: str | None,
    actual_action: str,
    caused_by_decision_id: str | None,
    pre_centroid: list[float] | None = None,
    persistence_lock: threading.RLock | None = None,
    logger: logging.Logger | None = None,
) -> bool:
    store = _centroid_learning_store_for(scorer, explicit_learning_store)
    if store is None:
        return False
    if not category:
        return False
    get_phase = getattr(scorer, "get_category_phase", None)
    get_centroid = getattr(scorer, "get_centroid", None)
    if not callable(get_phase) or not callable(get_centroid):
        return False
    try:
        phase = str(get_phase(category))
    except Exception as exc:
        if logger is not None:
            logger.debug("L5 centroid persistence skipped for %s: phase unavailable: %s", domain, exc)
        return False
    if phase == "VARIANCE_LEARNING":
        return False
    if phase != "MEAN_CONVERGENCE":
        if logger is not None:
            logger.debug("L5 centroid persistence skipped for %s: unknown phase %s", domain, phase)
        return False
    try:
        post_centroid = get_centroid(category, actual_action)
    except Exception as exc:
        if logger is not None:
            logger.debug("L5 centroid persistence skipped for %s: centroid unavailable: %s", domain, exc)
        return False
    if post_centroid is None:
        return False
    try:
        post_vector = [float(item) for item in post_centroid]
    except (TypeError, ValueError):
        return False
    if not post_vector or not all(math.isfinite(item) for item in post_vector):
        return False
    delta_norm = _centroid_delta_norm(pre_centroid, post_vector)
    lock = persistence_lock or threading.RLock()
    try:
        with lock:
            store.update_centroid(
                domain=domain,
                category=str(category),
                action=str(actual_action),
                centroid_vector=post_vector,
                delta_norm=delta_norm,
                caused_by_decision_id=caused_by_decision_id,
            )
    except Exception as exc:
        if logger is not None:
            logger.warning("L5 centroid write failed for %s: %s", domain, exc)
        return False
    return True


def _read_centroid_for_l5(
    scorer: Any,
    *,
    category: str | None,
    action: str,
    logger: logging.Logger | None = None,
) -> list[float] | None:
    if not category:
        return None
    get_centroid = getattr(scorer, "get_centroid", None)
    if not callable(get_centroid):
        return None
    try:
        centroid = get_centroid(category, action)
    except Exception as exc:
        if logger is not None:
            logger.debug("L5 centroid pre-read skipped: %s", exc)
        return None
    if centroid is None:
        return None
    try:
        return [float(item) for item in centroid]
    except (TypeError, ValueError):
        return None


def _centroid_delta_norm(
    pre_centroid: list[float] | None,
    post_centroid: list[float],
) -> float:
    if pre_centroid is None or len(pre_centroid) != len(post_centroid):
        return float(np.linalg.norm(np.asarray(post_centroid, dtype=np.float64)))
    before = np.asarray(pre_centroid, dtype=np.float64)
    after = np.asarray(post_centroid, dtype=np.float64)
    return float(np.linalg.norm(after - before))


def _persist_dk_state_l5(
    *,
    domain: str,
    scorer: Any,
    explicit_learning_store: Any | None,
    decision: dict[str, Any],
    actual_action: str,
    payload: dict[str, Any],
    welford_tracker: DKWelfordTracker,
    persistence_lock: threading.RLock,
) -> None:
    if payload.get("status") == "paused" or payload.get("paused") is True:
        return None
    factor_vector = _decision_factor_vector(decision)
    recommended_action = _decision_recommended_action(decision)
    if factor_vector is None or recommended_action is None:
        log.warning("L5 DK persistence skipped for %s: missing decision factor/action data", domain)
        return None
    reestimate = getattr(scorer, "reestimate_dk_if_due", None)
    get_dk_weights = getattr(scorer, "get_dk_weights", None)
    if not callable(reestimate) or not callable(get_dk_weights):
        log.warning("L5 DK persistence skipped for %s: scorer lacks DK runtime helpers", domain)
        return None
    is_correct = str(actual_action) == str(recommended_action)
    try:
        with persistence_lock:
            welford_tracker.update(factor_vector, is_correct)
            reestimate()
            store = _dk_learning_store_for(scorer, explicit_learning_store)
            if store is None:
                return None
            if get_dk_weights() is None:
                return None
            persist_dk_after_reestimate(
                domain=domain,
                scorer=scorer,
                learning_store=store,
                welford_tracker=welford_tracker,
                entity_group=None,
                logger=log,
            )
    except Exception as exc:
        log.warning("L5 DK persistence skipped for %s: %s", domain, exc)
    return None


def _decision_factor_vector(decision: dict[str, Any]) -> list[float] | None:
    value = _decision_lookup(decision, "factor_vector")
    if value is None:
        value = _decision_lookup(decision, "factors")
    if isinstance(value, dict):
        return [float(item) for item in value.values()]
    if isinstance(value, (str, bytes, bytearray)) or value is None:
        return None
    try:
        return [float(item) for item in value]
    except (TypeError, ValueError):
        return None


def _decision_recommended_action(decision: dict[str, Any]) -> str | None:
    value = _decision_lookup(decision, "recommended_action")
    if value is None:
        value = _decision_lookup(decision, "action")
    return None if value is None else str(value)


def _decision_category(decision: dict[str, Any]) -> str | None:
    value = _decision_lookup(decision, "category")
    return None if value is None else str(value)


def _decision_lookup(decision: dict[str, Any], key: str) -> Any:
    if key in decision:
        return decision[key]
    metadata = decision.get("metadata")
    if isinstance(metadata, dict) and key in metadata:
        return metadata[key]
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
        number = float(value)
        return number if math.isfinite(number) else 0.0
    if isinstance(value, float):
        return value if math.isfinite(value) else 0.0
    return value


def _score_response_payload(payload: Any) -> dict[str, Any]:
    normalized = _json_safe(payload)
    if not isinstance(normalized, dict):
        normalized = {}
    try:
        return ScoreResponse.model_validate(normalized).model_dump()
    except Exception as exc:
        log.warning("ScoreResponse validation failed after normalization: %s", exc)

    probabilities = normalized.get("probabilities")
    if not isinstance(probabilities, list):
        probabilities = [_number(normalized.get("confidence", 0.0))]

    factors = normalized.get("factors")
    if not isinstance(factors, dict):
        factors = {}

    engine = normalized.get("engine")
    if not isinstance(engine, dict):
        engine = ENGINE

    fallback = {
        **normalized,
        "decision_id": str(normalized.get("decision_id") or "unknown"),
        "action": str(normalized.get("action") or "unknown"),
        "action_index": int(_number(normalized.get("action_index", 0))),
        "confidence": _number(normalized.get("confidence", 0.0)),
        "probabilities": [_number(item) for item in probabilities],
        "category": str(normalized.get("category") or "unknown"),
        "factors": {str(key): _number(value) for key, value in factors.items()},
        "engine": {str(key): str(value) for key, value in engine.items()},
    }
    return ScoreResponse.model_validate(fallback).model_dump()
