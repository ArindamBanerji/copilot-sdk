"""DataOps-specific Data Intelligence enrichment endpoints."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException

from copilot_sdk.backend.conservation_utils import compute_conservation_status_payload
from copilot_sdk.di.models import ConsumerProfile

from ..di_config import (
    DATA_PRODUCTS,
    SOURCE_COLUMN_BASELINES,
    get_factor_to_source_map,
    known_source_ids,
)


def create_dataops_di_enrichment_router(
    scorer_provider: Callable[[], Any],
) -> APIRouter:
    """Create the remaining DataOps DI-1 endpoints."""

    router = APIRouter()

    @router.get("/sources/{source_id}/consumers")
    def consumers(source_id: str) -> dict[str, Any]:
        _require_source(source_id)
        return {
            "source_id": source_id,
            "consumers": [profile.to_dict() for profile in _consumer_profiles(source_id)],
        }

    @router.get("/sources/{source_id}/trust")
    def trust(source_id: str) -> dict[str, Any]:
        _require_source(source_id)
        scorer = scorer_provider()
        weights = _factor_weights(scorer)
        source_trust = _source_trust(source_id, weights)
        conservation = _conservation(scorer)
        columns = [
            {
                "name": name,
                "trust": round(source_trust * baseline, 3),
                "label": _trust_label(source_trust * baseline),
            }
            for name, baseline in SOURCE_COLUMN_BASELINES.get(source_id, {}).items()
        ]
        return {
            "source_id": source_id,
            "trust_score": source_trust,
            "trust_label": _trust_label(source_trust),
            "conservation_status": conservation["status"],
            "verified_decisions": conservation["verified_decisions"],
            "dk_weight": source_trust,
            "recommendation": _recommendation(source_trust),
            "columns": columns,
        }

    @router.get("/products")
    def products() -> dict[str, Any]:
        scorer = scorer_provider()
        weights = _factor_weights(scorer)
        conservation = _conservation(scorer)
        product_payload: list[dict[str, Any]] = []
        for product in DATA_PRODUCTS:
            source_ids = [str(source_id) for source_id in product["sources"]]
            trusts = [_source_trust(source_id, weights) for source_id in source_ids]
            product_trust = sum(trusts) / len(trusts) if trusts else 0.0
            product_payload.append(
                {
                    "product_id": product["product_id"],
                    "product_name": product["product_name"],
                    "iks": round(product_trust * 100),
                    "conservation_status": conservation["status"],
                    "verified_decisions": conservation["verified_decisions"],
                    "sources": source_ids,
                    "maturity_label": _maturity_label(product_trust),
                }
            )
        return {"products": product_payload}

    return router


def _require_source(source_id: str) -> None:
    if source_id not in known_source_ids():
        raise HTTPException(status_code=404, detail=f"Unknown DI source: {source_id}")


def _consumer_profiles(source_id: str) -> list[ConsumerProfile]:
    return [
        ConsumerProfile(
            consumer_id="marketing_dashboard",
            source_id=source_id,
            quality_bar={"freshness": "< 1hr", "completeness": "> 95%"},
            satisfaction_rate=0.89,
            last_issue="stale data 2026-07-15",
        ),
        ConsumerProfile(
            consumer_id="autonomous_triage_agent",
            source_id=source_id,
            quality_bar={"freshness": "< 15min", "completeness": "> 98%"},
            satisfaction_rate=0.94,
            last_issue=None,
        ),
    ]


def _factor_weights(scorer: Any) -> dict[str, float]:
    fingerprint = _as_mapping(scorer.fingerprint())
    weights: dict[str, float] = {}
    for raw_factor in fingerprint.get("factors", []) or []:
        factor = _as_mapping(raw_factor)
        name = str(factor.get("name", "")).strip()
        if name:
            weights[name] = _bounded_float(factor.get("weight", factor.get("dk_weight", 0.0)))
    return weights


def _source_trust(source_id: str, weights: dict[str, float]) -> float:
    factor_map = get_factor_to_source_map()
    mapped_weights = [weight for factor, weight in weights.items() if factor_map.get(factor) == source_id]
    if mapped_weights:
        return round(sum(mapped_weights) / len(mapped_weights), 3)
    return 0.5


def _conservation(scorer: Any) -> dict[str, Any]:
    store = getattr(scorer, "graph_store", None)
    if store is None:
        raise HTTPException(status_code=503, detail="Data Intelligence graph unavailable")
    payload = compute_conservation_status_payload("dataops", store)
    return {
        "status": str(payload.get("status", "UNAVAILABLE")),
        "verified_decisions": int(payload.get("verified_count", 0) or 0),
    }


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {
        key: getattr(value, key)
        for key in ("name", "weight", "dk_weight", "factors", "decisions_analyzed")
        if hasattr(value, key)
    }


def _bounded_float(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _trust_label(value: float) -> str:
    if value > 0.7:
        return "reliable"
    if value >= 0.3:
        return "moderate"
    return "noisy"


def _recommendation(value: float) -> str:
    if value > 0.7:
        return "Safe for autonomous agent consumption."
    if value >= 0.3:
        return "Suitable for agent consumption with monitoring."
    return "Do not use for autonomous agent consumption."


def _maturity_label(value: float) -> str:
    if value > 0.7:
        return "mature"
    if value >= 0.3:
        return "developing"
    return "emerging"
