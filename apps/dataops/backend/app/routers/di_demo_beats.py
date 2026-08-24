"""Live DataOps Data Intelligence demo-beat endpoints."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter

from copilot_sdk.backend.conservation_utils import compute_conservation_status_payload
from copilot_sdk.di.acquisition import AcquisitionAdvisor
from copilot_sdk.di.catalog import ExternalDataCatalog

from ..di_config import get_factor_to_source_map, known_source_ids


def create_di_demo_beats_router(
    scorer_provider: Callable[[], Any],
    graph_store_provider: Callable[[], Any],
    governance_provider: Callable[[], Any],
) -> APIRouter:
    router = APIRouter(tags=["dataops-di-beats"])

    def scorer() -> Any:
        return scorer_provider()

    def fingerprint() -> dict[str, Any]:
        value = scorer().fingerprint()
        return value if isinstance(value, dict) else {}

    def conservation() -> dict[str, Any]:
        store = graph_store_provider()
        if store is None:
            return {"status": "UNAVAILABLE", "verified_decisions": 0, "source": "graph_unavailable"}
        payload = compute_conservation_status_payload("dataops", store)
        return {
            "status": str(payload.get("status", "UNKNOWN")),
            "verified_decisions": int(payload.get("verified_count", 0) or 0),
            "source": "live_graph_store",
        }

    @router.get("/earned-trust")
    def earned_trust() -> dict[str, Any]:
        factors = [item for item in fingerprint().get("factors", []) if isinstance(item, dict)]
        weights = [max(0.0, min(1.0, _float(item.get("weight", item.get("dk_weight"))))) for item in factors]
        overall = round(sum(weights) / len(weights), 3) if weights else None
        what_if = []
        for item in factors:
            remaining = [value for other, value in zip(factors, weights) if other is not item]
            without = round(sum(remaining) / len(remaining), 3) if remaining else None
            what_if.append({"factor": str(item.get("name", "unknown")), "trust_without": without, "delta": _delta(without, overall)})
        return {"live_trust": overall, "what_if": what_if, "conservation": conservation(), "provenance": "live scorer fingerprint"}

    @router.get("/acquisition-advice")
    def acquisition_advice() -> dict[str, Any]:
        current = sorted(known_source_ids())
        payload = AcquisitionAdvisor(external_catalog=ExternalDataCatalog()).recommend(
            "dataops", current_sources=current, decisions_per_year=None
        )
        recommendations = payload.get("recommendations", [])
        return {
            **payload,
            "gold_lines": [
                {"source": item.get("source_name", item.get("name")), "roi": item.get("annual_value"), "prospective": True}
                for item in recommendations if isinstance(item, dict)
            ],
            "current_sources": current,
            "conservation": conservation(),
            "provenance": "catalog valuation; connect live history for measured ROI",
        }

    @router.get("/abstention")
    def abstention() -> dict[str, Any]:
        result = governance_provider().abstention("dataops")
        return {**result, "agent_action": "ask_permission" if result.get("should_abstain") else "proceed", "conservation": conservation(), "observation_only": True}

    @router.get("/trust-gateway")
    def trust_gateway() -> dict[str, Any]:
        state = conservation()
        factors = [item for item in fingerprint().get("factors", []) if isinstance(item, dict)]
        values = [_float(item.get("weight", item.get("dk_weight"))) for item in factors]
        trust_score = round(sum(values) / len(values), 3) if values else 0.0
        gate = "PASS" if state["status"] == "GREEN" and state["verified_decisions"] > 0 else "ABSTAIN"
        return {"verifications": [{"decision_id": "runtime-snapshot", "trust_score": trust_score, "gate_result": gate}], "safe_for_autonomous": gate == "PASS", "conservation": state, "endpoint": "/v1/trust/verify", "observation_only": True}

    @router.get("/source-compounding")
    def source_compounding() -> dict[str, Any]:
        source_ids = sorted(known_source_ids())
        verified = conservation()["verified_decisions"]
        return {"source_count": len(source_ids), "sources": source_ids, "learning_curve": [{"source_count": index, "verified_decisions": verified, "time_to_competence": None} for index in range(1, len(source_ids) + 1)], "conservation": conservation(), "measurement_state": "accumulating", "provenance": "live source registry and graph counts"}

    @router.get("/frozen-twin")
    def frozen_twin() -> dict[str, Any]:
        governance = governance_provider()
        frozen = getattr(governance, "frozen_twin", None)
        frozen_state = frozen.to_dict() if frozen is not None and hasattr(frozen, "to_dict") else None
        return {"frozen": frozen_state is not None, "frozen_snapshot": frozen_state, "current_fingerprint": fingerprint(), "missed_catches": [], "conservation": conservation(), "measurement_state": "measured" if frozen_state else "not_frozen"}

    return router


def _float(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _delta(value: float | None, baseline: float | None) -> float | None:
    if value is None or baseline is None:
        return None
    return round(value - baseline, 3)
