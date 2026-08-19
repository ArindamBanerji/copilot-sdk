"""Purchasing proof, readiness, handoff, and authority endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..services.purchasing_control import CLAIMS, PurchasingClaimRegistry, PurchasingControlService


def _is_observed(registry: PurchasingClaimRegistry, claim_id: str) -> bool:
    result = registry.gate.check(claim_id, "pilot")
    return result.tier.name in {"T_O", "T_R"} and result.passed


def create_purchasing_control_router(
    service: PurchasingControlService,
    registry: PurchasingClaimRegistry,
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/purchasing/proof-ledger")
    def proof_ledger() -> dict[str, Any]:
        return service.proof_ledger()

    @router.get("/api/purchasing/handoff-pack")
    def handoff_pack() -> dict[str, Any]:
        return service.handoff()

    @router.get("/api/purchasing/day-0-readiness")
    def day_zero_readiness() -> dict[str, Any]:
        return service.readiness()

    @router.get("/api/purchasing/legal-exposure")
    def legal_exposure() -> dict[str, Any]:
        return service.legal_exposure()

    @router.get("/api/purchasing/frozen-twin")
    def frozen_twin() -> dict[str, Any]:
        return service.frozen_status()

    @router.post("/api/purchasing/frozen-twin/freeze")
    def freeze_frozen_twin() -> dict[str, Any]:
        try:
            return service.freeze()
        except (FileExistsError, RuntimeError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.get("/api/purchasing/frozen-twin/comparison")
    def frozen_twin_comparison() -> dict[str, Any]:
        result = service.frozen_comparison()
        if not result["available"]:
            raise HTTPException(status_code=404, detail="Frozen Twin is not initialized")
        return result

    @router.post("/api/purchasing/proof-ledger/outcome")
    def record_outcome(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return service.record_outcome(payload)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @router.get("/api/purchasing/promotion")
    def promotion_state() -> dict[str, Any]:
        return {"records": [record.to_dict() for record in service.promotion.store.list_all("purchasing")], "observation_only": True}

    @router.post("/api/purchasing/promotion/{decision_class}/advance")
    def advance_promotion(decision_class: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        request = payload or {}
        evidence = registry.gate.check(CLAIMS["readiness"], "pilot")
        conservation = str(request.get("conservation_status", "UNKNOWN")).upper()
        if not _is_observed(registry, CLAIMS["readiness"]):
            raise HTTPException(status_code=409, detail="promotion requires T_O evidence")
        if conservation != "GREEN":
            raise HTTPException(status_code=409, detail="promotion requires GREEN conservation")
        record = service.promotion.store.load_by_class("purchasing", decision_class)
        if record is None:
            record = service.promotion.create("purchasing", decision_class)
        result = service.promotion.advance(record.record_id, {**request, "conservation_state": "GREEN"})
        return {"observation_only": True, "result": result.record.to_dict() if result.record else None, "advanced": result.advanced, "reason": result.reason, "stage": result.new_stage.value}

    @router.get("/api/purchasing/discovery-gate")
    def discovery_gate() -> dict[str, Any]:
        readiness = service.readiness()
        evidence = registry.gate.check(CLAIMS["discovery"], "pilot")
        allowed = bool(readiness["ready"] and _is_observed(registry, CLAIMS["discovery"]))
        return {"decision": "PROCEED" if allowed else "NOT_YET", "reason": "verified coverage and measured evidence required" if not allowed else "measured evidence and coverage available", "out_of_sample_confirmation_required": True, "selection_adjusted": False, "partial_pooling": "within legal entity only", "evidence_tier": evidence.tier.name, "evidence_label": evidence.label}

    @router.get("/api/purchasing/yield-quote-audit")
    def yield_quote_audit() -> dict[str, Any]:
        return {"status": "NOT_YET", "gross_quote_audit": [], "net_plate_cost": 0.0, "reason": "yield and waste measurements are not present in the verified outcome chain", "evidence_tier": registry.gate.check(CLAIMS["yield_audit"], "pilot").tier.name}

    return router
