"""Self-computation endpoints backed directly by GraphStore."""

from __future__ import annotations

import math
import hashlib
import json
from collections.abc import Callable
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from copilot_sdk.backend.models import (
    AccuracyByCategoryResponse,
    CentroidHistoryResponse,
    CounterfactualResponse,
    DiagnosticsResponse,
    DecisionFlowResponse,
    EvolutionSummaryResponse,
    FlexibleResponse,
    SelfDecisionsResponse,
)
from copilot_sdk.backend.evolution_router import build_evolution_summary
from copilot_sdk.graph import GraphStore
from copilot_sdk.scoring.measurement_state import compute_measurement_state
from copilot_sdk.scoring.trust_traps import TrustTrapDetector, trap_asdict


StoreProvider = GraphStore | Callable[[], GraphStore]
ScorerProvider = Any | Callable[[], Any]


class ReplayScoreRequest(BaseModel):
    checkpoint_id: str
    category: str | None = None
    factors: dict[str, float] | None = None
    factor_vector: list[float] | None = None


def create_self_computation_router(
    graph_store: StoreProvider,
    *,
    prefix: str = "/api/self",
    domain: str | None = None,
    scorer_provider: ScorerProvider | None = None,
    evolver_provider: Callable[[], Any] | None = None,
) -> APIRouter:
    """Create GraphStore-backed self-computation endpoints for one app instance."""
    router = APIRouter(prefix=prefix, tags=["self-computation"])

    def _gs() -> GraphStore:
        return graph_store() if callable(graph_store) else graph_store

    def _domain() -> str:
        return str(domain or getattr(_gs(), "domain", "") or "")

    def _scorer() -> Any:
        if scorer_provider is None:
            raise HTTPException(
                status_code=503,
                detail="Counterfactual scoring is unavailable for this router",
            )
        scorer = scorer_provider() if callable(scorer_provider) else scorer_provider
        if scorer is None:
            raise HTTPException(
                status_code=503,
                detail="Scorer initializing — retry in a moment",
            )
        unwrap = getattr(scorer, "_scorer", None)
        if not hasattr(scorer, "score_with_centroids") and callable(unwrap):
            scorer = unwrap()
        if not hasattr(scorer, "score_read_only") or not hasattr(
            scorer, "score_with_centroids"
        ):
            raise HTTPException(
                status_code=503,
                detail="Counterfactual scoring is unavailable for this scorer",
            )
        return scorer

    def _trap_scorer() -> Any | None:
        if scorer_provider is None:
            return None
        scorer = scorer_provider() if callable(scorer_provider) else scorer_provider
        if scorer is None:
            raise HTTPException(
                status_code=503,
                detail="Scorer initializing — retry in a moment",
            )
        unwrap = getattr(scorer, "_scorer", None)
        if not hasattr(scorer, "rollback_to_checkpoint") and callable(unwrap):
            scorer = unwrap()
        return scorer

    @router.get("/centroid-history", response_model=CentroidHistoryResponse)
    def centroid_history(
        request: Request,
        limit: int = Query(50, ge=1, le=500),
        checkpoint_time_start: str | None = None,
        checkpoint_time_end: str | None = None,
        decision_time_start: str | None = None,
        decision_time_end: str | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        filters = {
            "checkpoint_time_start": checkpoint_time_start,
            "checkpoint_time_end": checkpoint_time_end,
            "decision_time_start": decision_time_start,
            "decision_time_end": decision_time_end,
            "category": category,
        }
        active_filters: dict[str, Any] = {
            key: value for key, value in filters.items() if value is not None
        }
        checkpoints = _gs().get_centroid_checkpoints(
            _domain(), limit=limit, include_v2=True, **active_filters
        )
        normalized = []
        for checkpoint in checkpoints:
            checkpoint_dict = _json_safe(checkpoint)
            checkpoint_metadata = checkpoint_dict.get("metadata")
            if isinstance(checkpoint_metadata, dict):
                checkpoint_dict.setdefault(
                    "centroid_distance_to_canonical",
                    checkpoint_metadata.get("centroid_distance_to_canonical"),
                )
                checkpoint_dict.setdefault("regime_tag", checkpoint_metadata.get("regime_tag"))
            if checkpoint_dict.get("quality_window_size") is None:
                checkpoint_dict["quality"] = None
            else:
                checkpoint_dict["quality"] = {
                    "window_size": checkpoint_dict.get("quality_window_size"),
                    "verified_count": checkpoint_dict.get("quality_verified_count"),
                    "correct_count": checkpoint_dict.get("quality_correct_count"),
                    "rolling_accuracy": checkpoint_dict.get("rolling_accuracy"),
                    "window_end": checkpoint_dict.get("quality_window_end"),
                    "policy_version": checkpoint_dict.get("quality_policy_version"),
                }
            normalized.append(checkpoint_dict)
        return {"checkpoints": normalized, "total": len(normalized)}

    @router.post("/regime-reinit", response_model=FlexibleResponse)
    def regime_reinit(
        regime_tag: str,
        strategy: str = "A",
        blend_weight: float = 0.5,
        v_discount: float = 0.5,
    ) -> dict[str, Any]:
        scorer = _scorer()
        reinitializer = getattr(scorer, "reinitialize_from_regime", None)
        if not callable(reinitializer):
            raise HTTPException(status_code=501, detail="Regime re-initialization is unavailable")
        return reinitializer(
            regime_tag=regime_tag,
            strategy=strategy,
            blend_weight=blend_weight,
            v_discount=v_discount,
        )

    @router.get("/evolution/summary", response_model=EvolutionSummaryResponse)
    def evolution_summary(request: Request) -> dict[str, Any]:
        provider = evolver_provider
        if provider is None:
            provider = lambda: getattr(request.app.state, "evolver", None)
        evolver = provider()
        return build_evolution_summary(evolver, _domain())

    @router.get("/diagnostics", response_model=DiagnosticsResponse)
    def diagnostics() -> dict[str, Any]:
        """Return canonical convergence, epsilon-firm, and IKS diagnostics."""
        scorer = _scorer()
        distance_method = getattr(scorer, "compute_centroid_distance_to_canonical", None)
        epsilon_method = getattr(scorer, "compute_epsilon_firm", None)
        distance = distance_method() if callable(distance_method) else None
        epsilon = epsilon_method() if callable(epsilon_method) else None
        iks_method = getattr(scorer, "_compute_checkpoint_iks", None)
        if not callable(iks_method):
            iks_method = getattr(scorer, "compute_iks", None)
        iks = iks_method() if callable(iks_method) else None
        measurement_state = compute_measurement_state(scorer).to_dict()
        evolver = evolver_provider() if evolver_provider is not None else None
        provider = getattr(getattr(evolver, "config", None), "conservation_state_provider", None)
        if provider is None:
            provider = getattr(evolver, "conservation_provider", None)
        if callable(provider):
            conservation = provider()
        elif provider is not None:
            conservation = provider.get_state()
        else:
            conservation = {"status": "UNKNOWN"}
        return {
            "centroid_distance_to_canonical": distance,
            "epsilon_firm": epsilon,
            "iks": iks,
            "measurement_state": measurement_state,
            "domain": _domain(),
            "conservation": conservation,
        }

    @router.get(
        "/centroid-history/{checkpoint_id}/counterfactual",
        response_model=CounterfactualResponse,
    )
    def counterfactual(
        checkpoint_id: str,
        window: int = Query(20, ge=1, le=400),
    ) -> dict[str, Any]:
        store = _gs()
        current_domain = _domain()
        checkpoints = store.get_centroid_checkpoints(
            current_domain,
            limit=None,
            include_v2=True,
        )
        checkpoint = next(
            (
                item
                for item in checkpoints
                if item.get("checkpoint_id") is not None
                and str(item.get("checkpoint_id")) == checkpoint_id
            ),
            None,
        )
        if checkpoint is None:
            raise HTTPException(status_code=404, detail="Checkpoint not found")

        raw_centroids = checkpoint.get("centroids")
        if raw_centroids is None:
            raise HTTPException(
                status_code=422,
                detail="Checkpoint does not contain a centroid tensor",
            )
        try:
            checkpoint_centroids = np.asarray(raw_centroids, dtype=np.float64)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=422,
                detail="Checkpoint does not contain a centroid tensor",
            ) from None
        if checkpoint_centroids.size == 0 or checkpoint_centroids.ndim != 3:
            raise HTTPException(
                status_code=422,
                detail="Checkpoint does not contain a centroid tensor",
            )

        scorer = _scorer()
        shape = scorer._preset.shape
        expected_shape = (
            int(shape.n_categories),
            int(shape.n_actions),
            int(shape.n_factors),
        )
        if tuple(checkpoint_centroids.shape) != expected_shape:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Checkpoint centroid shape does not match the current "
                    f"preset: {tuple(checkpoint_centroids.shape)} != {expected_shape}"
                ),
            )

        factor_hash = str(checkpoint.get("factor_names_hash") or "")
        current_hash = _factor_names_hash(list(shape.factor_names))
        if factor_hash != current_hash:
            raise HTTPException(
                status_code=409,
                detail="Checkpoint factor_names_hash does not match the current preset",
            )

        verified = store.get_verified_decisions(current_domain)[-window:]
        details: list[dict[str, Any]] = []
        for decision in verified:
            factors = decision.get("factors")
            category = str(decision.get("category") or "")
            if not isinstance(factors, dict) or not category:
                continue
            factor_values = {str(key): float(value) for key, value in factors.items()}
            baseline = scorer.score_read_only(factor_values, category)
            ablated = scorer.score_with_centroids(
                checkpoint_centroids.copy(), factor_values, category
            )
            details.append(
                {
                    "decision_id": str(decision.get("decision_id") or ""),
                    "category": category,
                    "baseline_action": baseline.action,
                    "counterfactual_action": ablated.action,
                    "changed": baseline.action != ablated.action,
                }
            )

        changed = sum(1 for detail in details if detail["changed"])
        rescored = len(details)
        checkpoint_time = _safe_float(
            checkpoint.get("created_at")
            if checkpoint.get("created_at") is not None
            else checkpoint.get("checkpoint_time")
        )
        return {
            "analysis_type": "centroid_ablation",
            "description": (
                "Decisions rescored with this checkpoint's centroids and the "
                "current kernel + temperature; isolates the centroid contribution."
            ),
            "checkpoint_id": checkpoint_id,
            "checkpoint_time": checkpoint_time,
            "baseline": "latest_centroids",
            "held_fixed": ["dk_weights", "temperature"],
            "window_requested": window,
            "decisions_rescored": rescored,
            "would_change": changed,
            "change_rate": changed / rescored if rescored else None,
            "details": details,
        }

    @router.get("/centroid-history/{checkpoint_id}/lineage", response_model=FlexibleResponse)
    def checkpoint_lineage(checkpoint_id: str) -> dict[str, Any]:
        result = _gs().get_checkpoint_lineage(_domain(), checkpoint_id)
        if result is None:
            raise HTTPException(status_code=404, detail="No lineage found for this checkpoint")
        return {
            "checkpoint_id": checkpoint_id,
            "triggered_by": _json_safe(result),
            "edge_type": "SNAPSHOT_AFTER",
        }

    @router.get("/centroid-history/{checkpoint_id}/replay", response_model=FlexibleResponse)
    def checkpoint_replay(checkpoint_id: str) -> dict[str, Any]:
        """Return the complete model state captured at a checkpoint."""
        checkpoint = _find_checkpoint(_gs(), _domain(), checkpoint_id)
        if checkpoint is None:
            raise HTTPException(status_code=404, detail="Checkpoint not found")
        metadata = checkpoint.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        return {
            "checkpoint_id": checkpoint_id,
            "centroids": _json_safe(checkpoint.get("centroids")),
            "dk_weights": _json_safe(metadata.get("dk_weights")),
            "temperature": _safe_float(metadata.get("temperature")),
            "quality": _checkpoint_quality_payload(checkpoint),
            "iks": _safe_float(checkpoint.get("iks")),
            "created_at": _safe_float(
                checkpoint.get("created_at_epoch", checkpoint.get("created_at"))
            ),
        }

    @router.post("/replay-score", response_model=FlexibleResponse)
    def replay_score(payload: ReplayScoreRequest) -> dict[str, Any]:
        """Score a factor vector using the model state at a checkpoint."""
        checkpoint = _find_checkpoint(_gs(), _domain(), payload.checkpoint_id)
        if checkpoint is None:
            raise HTTPException(status_code=404, detail="Checkpoint not found")
        scorer = _scorer()
        metadata = checkpoint.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        category = payload.category or str(checkpoint.get("category") or "")
        if not category:
            raise HTTPException(status_code=422, detail="category is required for replay")
        factors = payload.factors
        if factors is None and payload.factor_vector is not None:
            names = list(scorer._preset.shape.factor_names)
            if len(payload.factor_vector) != len(names):
                raise HTTPException(
                    status_code=422,
                    detail=f"factor_vector must contain {len(names)} values",
                )
            factors = {
                name: float(value) for name, value in zip(names, payload.factor_vector, strict=True)
            }
        if factors is None:
            raise HTTPException(status_code=422, detail="factors or factor_vector is required")
        try:
            result = scorer.score_with_model_state(
                np.asarray(checkpoint.get("centroids"), dtype=np.float64),
                {str(key): float(value) for key, value in factors.items()},
                category,
                dk_weights=metadata.get("dk_weights"),
                temperature=_safe_float(metadata.get("temperature")),
            )
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "checkpoint_id": payload.checkpoint_id,
            "action": result.action,
            "action_index": result.action_index,
            "confidence": result.confidence,
            "probabilities": result.probabilities,
            "category": result.category,
            "factors": result.factors,
        }

    @router.get("/decisions/{decision_id}/checkpoints", response_model=FlexibleResponse)
    def decision_checkpoints(decision_id: str) -> dict[str, Any]:
        results = _gs().get_decision_checkpoints(_domain(), decision_id)
        return {
            "decision_id": decision_id,
            "checkpoints": _json_safe(results),
            "edge_type": "SNAPSHOT_AFTER",
        }

    @router.get("/accuracy-by-category", response_model=AccuracyByCategoryResponse)
    def accuracy_by_category(
        request: Request,
        threshold: float = Query(0.70, ge=0.0, le=1.0),
    ) -> dict[str, Any]:
        verified = _gs().get_verified_decisions(_domain())
        grouped: dict[str, dict[str, int]] = {}
        for decision in verified:
            category = str(decision.get("category") or "uncategorized")
            bucket = grouped.setdefault(category, {"total": 0, "correct": 0})
            bucket["total"] += 1
            if decision.get("is_correct") is True:
                bucket["correct"] += 1

        categories = []
        for category in sorted(grouped):
            total = grouped[category]["total"]
            correct = grouped[category]["correct"]
            accuracy = round(correct / total, 4) if total else 0.0
            categories.append(
                {
                    "category": category,
                    "accuracy": accuracy,
                    "total": total,
                    "correct": correct,
                    "alert": accuracy < threshold,
                }
            )

        return {
            "categories": categories,
            "threshold": threshold,
            "overall_verified": len(verified),
        }

    @router.get("/trust-traps", response_model=FlexibleResponse)
    def trust_traps() -> dict[str, Any]:
        detector = TrustTrapDetector(_trap_scorer(), _gs(), _domain())
        traps = detector.scan()
        return {"traps": [trap_asdict(trap) for trap in traps], "total": len(traps)}

    @router.post("/rollback", response_model=FlexibleResponse)
    def rollback(checkpoint_id: str = Query(..., min_length=1)) -> dict[str, Any]:
        scorer = _trap_scorer()
        if scorer is None or not hasattr(scorer, "rollback_to_checkpoint"):
            raise HTTPException(status_code=503, detail="Checkpoint rollback is unavailable for this scorer")
        try:
            return dict(scorer.rollback_to_checkpoint(checkpoint_id))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/decisions", response_model=SelfDecisionsResponse)
    def decisions(
        request: Request,
        category: str | None = None,
        action: str | None = None,
        limit: int = Query(50, ge=1, le=500),
        verified_only: bool = False,
    ) -> dict[str, Any]:
        store = _gs()
        source = (
            store.get_verified_decisions(_domain())
            if verified_only
            else _merge_verified_fields(
                store.get_all_decisions(_domain()),
                store.get_verified_decisions(_domain()),
            )
        )
        filtered = [
            decision
            for decision in source
            if _matches_decision(decision, category=category, action=action)
        ]
        return {"decisions": filtered[:limit], "total": len(filtered)}

    @router.get("/audit-trail", response_model=dict[str, Any])
    def audit_trail(
        request: Request,
        decision_id: str | None = None,
        limit: int = Query(20, ge=1, le=100),
    ) -> dict[str, Any]:
        store = _gs()
        if decision_id:
            decision = store.get_decision(decision_id, domain=_domain())
            if decision is None:
                return {"error": f"Decision {decision_id} not found"}
            outcome = next(
                (
                    verified
                    for verified in store.get_verified_decisions(_domain())
                    if verified.get("decision_id") == decision_id
                ),
                None,
            )
            return {
                "decision": decision,
                "outcome": outcome,
                "chain_complete": outcome is not None,
            }

        verified = store.get_verified_decisions(_domain())[:limit]
        return {"trails": verified, "total": len(verified)}

    @router.get("/decision-flow", response_model=DecisionFlowResponse)
    def decision_flow(limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
        store = _gs()
        domain = _domain()
        all_decisions = _get_all_decisions(store, domain)
        verified = _get_verified_decisions(store, domain)
        merged = _merge_verified_fields(all_decisions, verified)
        ordered = sorted(merged, key=_decision_sort_key, reverse=True)
        recent = ordered[:limit]
        checkpoints = _get_centroid_checkpoints(store, domain, limit=20)

        verified_count = _count_verified(store, domain, verified)
        correct_count = _count_correct(store, domain, verified)
        total_count = len(all_decisions)
        checkpoint_ids = {
            str(checkpoint.get("decision_id"))
            for checkpoint in checkpoints
            if checkpoint.get("decision_id") is not None
        }

        return _json_safe(
            {
                "domain": domain,
                "total_decisions": total_count,
                "verified_decisions": verified_count,
                "accuracy": _ratio(correct_count, verified_count),
                "by_category": _category_flow_stats(all_decisions, verified),
                "recent_decisions": [_normalize_decision(decision) for decision in recent],
                "centroid_evolution": [
                    _normalize_checkpoint(checkpoint)
                    for checkpoint in checkpoints[-20:]
                ],
                "decision_chain": _decision_chain(recent, checkpoint_ids),
                "flow_statistics": _flow_statistics(all_decisions, verified),
            }
        )

    return router


def mount_self_computation_router(
    app: Any,
    store_provider: StoreProvider,
    prefix: str = "/api/self",
    domain: str | None = None,
    scorer_provider: ScorerProvider | None = None,
    evolver_provider: Callable[[], Any] | None = None,
) -> None:
    """Mount shared self-computation endpoints using a store or lazy provider."""
    app.include_router(
        create_self_computation_router(
            store_provider,
            prefix=prefix,
            domain=domain,
            scorer_provider=scorer_provider,
            evolver_provider=evolver_provider,
        )
    )


def _matches_decision(
    decision: dict[str, Any],
    *,
    category: str | None,
    action: str | None,
) -> bool:
    if category is not None and decision.get("category") != category:
        return False
    if action is None:
        return True
    return action in {
        decision.get("recommended_action"),
        decision.get("actual_action"),
        decision.get("action"),
    }


def _merge_verified_fields(
    decisions: list[dict[str, Any]],
    verified: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    verified_by_id = {
        item.get("decision_id"): item
        for item in verified
        if item.get("decision_id")
    }
    merged = []
    for decision in decisions:
        decision_id = decision.get("decision_id")
        verified_decision = verified_by_id.get(decision_id)
        if verified_decision is None:
            merged.append(decision)
        else:
            merged.append({**decision, **verified_decision})
    return merged


def _get_all_decisions(store: GraphStore, domain: str) -> list[dict[str, Any]]:
    return list(store.get_all_decisions(domain))


def _get_verified_decisions(store: GraphStore, domain: str) -> list[dict[str, Any]]:
    return list(store.get_verified_decisions(domain))


def _count_verified(
    store: GraphStore,
    domain: str,
    verified: list[dict[str, Any]],
) -> int:
    return int(store.count_verified(domain))


def _count_correct(
    store: GraphStore,
    domain: str,
    verified: list[dict[str, Any]],
) -> int:
    return int(store.count_correct(domain))


def _get_centroid_checkpoints(
    store: GraphStore,
    domain: str,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    return list(store.get_centroid_checkpoints(domain, limit=limit))


def _find_checkpoint(
    store: GraphStore,
    domain: str,
    checkpoint_id: str,
) -> dict[str, Any] | None:
    checkpoints = store.get_centroid_checkpoints(domain, limit=None, include_v2=True)
    return next(
        (
            checkpoint
            for checkpoint in checkpoints
            if str(checkpoint.get("checkpoint_id") or "") == str(checkpoint_id)
        ),
        None,
    )


def _checkpoint_quality_payload(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    if checkpoint.get("quality_window_size") is None:
        return None
    return {
        "window_size": checkpoint.get("quality_window_size"),
        "verified_count": checkpoint.get("quality_verified_count"),
        "correct_count": checkpoint.get("quality_correct_count"),
        "rolling_accuracy": checkpoint.get("rolling_accuracy"),
        "window_end": checkpoint.get("quality_window_end"),
        "policy_version": checkpoint.get("quality_policy_version"),
    }


def _category_flow_stats(
    decisions: list[dict[str, Any]],
    verified: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, int]] = {}
    for decision in decisions:
        category = str(decision.get("category") or "uncategorized")
        grouped.setdefault(
            category,
            {"total_decisions": 0, "verified_decisions": 0, "correct_decisions": 0},
        )["total_decisions"] += 1

    for decision in verified:
        category = str(decision.get("category") or "uncategorized")
        bucket = grouped.setdefault(
            category,
            {"total_decisions": 0, "verified_decisions": 0, "correct_decisions": 0},
        )
        bucket["verified_decisions"] += 1
        if decision.get("is_correct") is True:
            bucket["correct_decisions"] += 1

    return {
        category: {
            **bucket,
            "accuracy": _ratio(bucket["correct_decisions"], bucket["verified_decisions"]),
        }
        for category, bucket in sorted(grouped.items())
    }


def _normalize_decision(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_id": _string_or_none(decision.get("decision_id")),
        "entity_id": _string_or_none(decision.get("entity_id")),
        "category": decision.get("category"),
        "action": decision.get("recommended_action") or decision.get("action"),
        "confidence": _safe_float(decision.get("confidence")),
        "factors": decision.get("factors"),
        "outcome": decision.get("actual_action"),
        "is_correct": _bool_or_none(decision.get("is_correct")),
        "timestamp": _timestamp(decision),
    }


def _normalize_checkpoint(checkpoint: dict[str, Any]) -> dict[str, Any]:
    metadata = checkpoint.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    return {
        "timestamp": (
            checkpoint.get("checkpoint_time")
            or checkpoint.get("created_at")
            or checkpoint.get("timestamp")
        ),
        "iks": _safe_float(checkpoint.get("iks")) if "iks" in checkpoint else None,
        "category": checkpoint.get("category"),
        "action": metadata.get("action") or metadata.get("recommended_action"),
        "metadata": metadata,
    }


def _decision_chain(
    decisions: list[dict[str, Any]],
    checkpoint_ids: set[str],
) -> list[dict[str, Any]]:
    chain = []
    for index, decision in enumerate(decisions):
        decision_id = _string_or_none(decision.get("decision_id")) or ""
        next_decision = decisions[index + 1] if index + 1 < len(decisions) else None
        chain.append(
            {
                "decision_id": decision_id,
                "outcome": decision.get("actual_action"),
                "centroid_update": (
                    decision_id in checkpoint_ids
                    or decision.get("is_correct") is not None
                ),
                "next": (
                    _string_or_none(next_decision.get("decision_id"))
                    if next_decision is not None
                    else None
                ),
            }
        )
    return chain


def _flow_statistics(
    decisions: list[dict[str, Any]],
    verified: list[dict[str, Any]],
) -> dict[str, Any]:
    total = len(decisions)
    verified_count = len(verified)
    rewards = [_reward_value(decision) for decision in verified]
    rewards = [reward for reward in rewards if reward is not None]
    return {
        "avg_confidence": _safe_mean(
            _safe_float(decision.get("confidence"))
            for decision in decisions
        ),
        "confirmation_rate": _ratio(verified_count, total),
        "override_rate": _override_rate(verified),
        "mean_reward": _safe_mean(rewards) if rewards else None,
    }


def _override_rate(verified: list[dict[str, Any]]) -> float:
    if not verified:
        return 0.0
    overrides = sum(
        1
        for decision in verified
        if decision.get("actual_action") not in (None, decision.get("recommended_action"), decision.get("action"))
    )
    return _ratio(overrides, len(verified))


def _reward_value(decision: dict[str, Any]) -> float | None:
    for source in (
        decision,
        decision.get("context") if isinstance(decision.get("context"), dict) else {},
        decision.get("outcome_metadata") if isinstance(decision.get("outcome_metadata"), dict) else {},
        decision.get("metadata") if isinstance(decision.get("metadata"), dict) else {},
    ):
        if not isinstance(source, dict):
            continue
        for key in ("reward", "signed_reward", "score_reward"):
            if key in source:
                return _safe_float(source.get(key))
    return None


def _decision_sort_key(decision: dict[str, Any]) -> tuple[float, str]:
    timestamp = _safe_float(
        decision.get("created_at")
        if decision.get("created_at") is not None
        else decision.get("verified_at")
    )
    return (timestamp or 0.0, str(decision.get("decision_id") or ""))


def _timestamp(decision: dict[str, Any]) -> str | int | float | None:
    return (
        decision.get("created_at")
        if decision.get("created_at") is not None
        else decision.get("verified_at")
    )


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _factor_names_hash(factor_names: list[str]) -> str:
    return hashlib.sha256(
        json.dumps(list(factor_names), separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _safe_mean(values: Any) -> float:
    numbers = [number for value in values if (number := _safe_float(value)) is not None]
    return round(sum(numbers) / len(numbers), 6) if numbers else 0.0


def _ratio(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round(float(numerator) / float(denominator), 6)


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _bool_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if value is None or isinstance(value, (str, int, bool)):
        return value

    if not isinstance(value, (str, bytes)):
        tolist = getattr(value, "tolist", None)
        if callable(tolist):
            try:
                converted = tolist()
            except Exception:
                converted = None
            else:
                if converted is not value:
                    return _json_safe(converted)

        item = getattr(value, "item", None)
        if callable(item):
            try:
                return _json_safe(item())
            except Exception:
                pass

    return str(value)
