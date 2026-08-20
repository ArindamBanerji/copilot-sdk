"""Verification history for the DataOps agent-trust gateway."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query

from copilot_sdk.backend.conservation_utils import compute_conservation_status_payload


def create_di_gateway_router(
    scorer_provider: Callable[[], Any],
    graph_store_provider: Callable[[], Any],
) -> APIRouter:
    """Expose the decisions checked by the DataOps trust gate."""

    router = APIRouter(tags=["dataops-di-gateway"])

    @router.get("/trust/verify")
    def verification_history(
        category: str | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=400),
    ) -> dict[str, Any]:
        store = graph_store_provider()
        all_decisions = list(store.get_decisions("dataops", category=category, limit=limit) or [])
        verified_ids = {
            str(row.get("decision_id"))
            for row in (store.get_verified_decisions("dataops") or [])
            if row.get("decision_id") is not None
        }
        verified_by_id = {
            str(row.get("decision_id")): row
            for row in (store.get_verified_decisions("dataops") or [])
            if row.get("decision_id") is not None
        }
        conservation = compute_conservation_status_payload("dataops", store)
        conservation_status = str(conservation.get("status", "UNKNOWN")).upper()

        verifications = [
            _verification_record(
                decision,
                verified=bool(str(decision.get("decision_id")) in verified_ids),
                verified_row=verified_by_id.get(str(decision.get("decision_id"))),
                conservation_status=conservation_status,
            )
            for decision in all_decisions
        ]
        if not verifications:
            verifications = [_snapshot_record(scorer_provider(), conservation_status, category)]

        return {
            "verifications": verifications,
            "summary": _summary(verifications),
        }

    return router


def _verification_record(
    decision: dict[str, Any],
    *,
    verified: bool,
    verified_row: dict[str, Any] | None,
    conservation_status: str,
) -> dict[str, Any]:
    confidence = _bounded_float(decision.get("confidence"))
    if not verified:
        gate_result = "ABSTAIN"
    elif verified_row and verified_row.get("is_correct") is False:
        gate_result = "BLOCK"
    elif conservation_status == "RED":
        gate_result = "BLOCK"
    else:
        gate_result = "PASS"
    vector = decision.get("factor_vector")
    source_count = len(vector) if isinstance(vector, list) else 0
    return {
        "action_id": str(decision.get("decision_id") or decision.get("entity_id") or "unknown"),
        "category": str(decision.get("category") or "unknown"),
        "trust_score": confidence,
        "gate_result": gate_result,
        "timestamp": _timestamp(decision.get("created_at")),
        "source_count": source_count,
        "evidence_tier": "T_O" if verified else "T_S",
    }


def _snapshot_record(scorer: Any, conservation_status: str, category: str | None) -> dict[str, Any]:
    fingerprint = scorer.fingerprint()
    factors = fingerprint.get("factors", []) if isinstance(fingerprint, dict) else []
    weights = [_bounded_float(item.get("weight", item.get("dk_weight"))) for item in factors if isinstance(item, dict)]
    trust_score = round(sum(weights) / len(weights), 3) if weights else 0.0
    return {
        "action_id": "trust-gate-snapshot",
        "category": category or "dataops",
        "trust_score": trust_score,
        "gate_result": "BLOCK" if conservation_status == "RED" else "ABSTAIN",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_count": len(factors),
        "evidence_tier": "T_S",
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    passed = sum(row["gate_result"] == "PASS" for row in rows)
    blocked = sum(row["gate_result"] == "BLOCK" for row in rows)
    abstained = sum(row["gate_result"] == "ABSTAIN" for row in rows)
    scores = [row["trust_score"] for row in rows if row["trust_score"] is not None]
    return {
        "total": total,
        "passed": passed,
        "blocked": blocked,
        "abstained": abstained,
        "avg_trust_score": round(sum(scores) / len(scores), 3) if scores else None,
    }


def _bounded_float(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 3)
    except (TypeError, ValueError):
        return 0.0


def _timestamp(value: Any) -> str:
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError, OverflowError, OSError):
        return str(value or datetime.now(timezone.utc).isoformat(timespec="seconds"))
