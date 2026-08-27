"""Live Trading claim-gate and withheld-impact surface."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter


GraphStoreFactory = Callable[[], Any]


def create_claim_gate_router(
    graph_store_factory: GraphStoreFactory,
    *,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-claim-gate"])

    @router.get("/claim-gate")
    def claim_gate() -> dict[str, Any]:
        """Report claim-gate counts from the live domain-scoped graph."""
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


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
