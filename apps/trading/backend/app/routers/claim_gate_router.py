"""Live Trading claim-gate and withheld-impact surface."""

from __future__ import annotations

import logging
from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from copilot_sdk.backend.graph_access import GRAPH_CONNECTION_ERRORS


logger = logging.getLogger(__name__)


GraphStoreFactory = Callable[[], Any]


def create_claim_gate_router(
    graph_store_factory: GraphStoreFactory,
    *,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-claim-gate"])

    @router.get("/claim-gate", response_model=None)
    def claim_gate() -> dict[str, Any] | JSONResponse:
        """Report claim-gate counts from the live domain-scoped graph."""
        try:
            store = graph_store_factory()
            decisions = list(store.get_all_decisions(domain))
            verified = int(store.count_verified(domain))
            correct = int(store.count_correct(domain))
            impact = sum(_number(_value(decision, "pnl", "pnl_dollars", "dollar_impact")) for decision in decisions)
            return {
                "tested": len(decisions),
                "powered": verified,
                "survived": correct,
                "withheld": max(0, len(decisions) - verified),
                "savedImpact": round(max(0.0, impact), 2),
                "certificate": "observation-only: evidence gate active",
                "evidenceTier": "T-O" if verified else "T-S",
                "evidenceLabel": "Live Trading decision ledger",
                "observation": "Claims remain withheld until the live verified ledger supports them.",
                "observationOnly": True,
            }
        except GRAPH_CONNECTION_ERRORS as exc:
            logger.exception("claim gate failed: %s", exc)
            return JSONResponse(
                status_code=503,
                content={"error": "claim_gate_unavailable", "detail": str(exc)},
            )

    return router


def _value(record: Any, *keys: str) -> Any:
    if not isinstance(record, dict):
        return None
    raw_metadata = record.get("metadata")
    metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
    for key in keys:
        value = record.get(key)
        if value is None:
            value = metadata.get(key)
        if value is not None:
            return value
    return None


def _number(value: object) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        logger.warning("claim_gate: malformed value %r, defaulting to 0.0", value)
        return 0.0
