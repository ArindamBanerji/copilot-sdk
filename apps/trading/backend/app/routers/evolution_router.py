"""Trading AgentEvolver API."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from copilot_sdk.backend.conservation_router import _check_payload, _state_counts
from copilot_sdk.scoring.evolution import EvolutionProposal, ScorerEvolution
from copilot_sdk.scoring.mutation_lock import serialize_mutation
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.state.cached_static import cached_static

from app.services.trading_evolver import (
    MAX_VARIANCE_PP,
    MIN_IMPROVEMENT_PP,
    MIN_SHADOW_BATCHES,
    TradingAgentEvolver,
    create_default_trading_evolver,
)

GraphStoreFactory = Callable[[], Any]
DEFAULT_REJECTION_LOG_PATH = Path(__file__).resolve().parents[2] / "state" / "evolution_log.json"
REJECTION_LOG_ENV = "TRADING_EVOLUTION_LOG_PATH"


class ShadowTestRequest(BaseModel):
    variant_id: str | None = None
    variant: dict[str, Any] | None = None
    decisions: list[dict[str, Any]] | None = None
    batch_size: int = 50


class PromoteRequest(BaseModel):
    variant_id: str


class ApplyProposalRequest(BaseModel):
    proposal_id: str


class RollbackRequest(BaseModel):
    parameter: str


def create_trading_evolution_router(
    evolver: TradingAgentEvolver | None = None,
    graph_store_factory: GraphStoreFactory | None = None,
    domain: str = "trading",
    regime_break_provider: Callable[[], bool] | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/trading/evolution", tags=["trading-evolution"])
    use_persisted_rejections = evolver is None
    service = evolver or create_default_trading_evolver()
    if regime_break_provider is not None:
        service.regime_break_provider = regime_break_provider
    parameter_service = ScorerEvolution("trading")
    parameter_config = _default_parameter_config()

    @router.get("/log")
    def evolution_log(request: Request, kind: str | None = None) -> list[dict[str, Any]]:
        variant_entries = [
            {"kind": "variant", **entry}
            for entry in service.evolution_log()
        ]
        parameter_entries = [
            {"kind": "parameter", **entry}
            for entry in parameter_service.evolution_log()
        ]
        log = variant_entries + parameter_entries
        if kind:
            normalized = kind.strip().lower()
            log = [entry for entry in log if str(entry.get("kind", "")).lower() == normalized]
        return log

    @router.get("/rejection-summary")
    @cached_static("rejection-summary")
    def rejection_summary(request: Request) -> dict[str, Any]:
        persisted = _load_persisted_rejection_summary() if use_persisted_rejections else None
        entries = _merge_rejection_entries(
            _trading_rejection_entries(service),
            persisted.get("rejected_variants", []) if persisted else [],
        )
        promoted = [
            entry for entry in service.evolution_log()
            if str(entry.get("status", "")).lower() == "promoted"
        ]
        tested = [
            entry for entry in service.evolution_log()
            if int(entry.get("batches") or 0) > 0
        ]
        breakdown = {
            "correctness_floor": 0,
            "conservation": 0,
            "variance_stability": 0,
        }
        for entry in entries:
            reason = str(entry.get("reason") or "")
            if reason in breakdown:
                breakdown[reason] += 1
        persisted_tested = int(persisted.get("total_tested") or 0) if persisted else 0
        persisted_promoted = int(persisted.get("total_promoted") or 0) if persisted else 0
        return {
            "total_tested": max(len(tested), persisted_tested),
            "total_promoted": max(len(promoted), persisted_promoted),
            "total_rejected": len(entries),
            "rejection_breakdown": breakdown,
            "rejected_variants": entries[:10],
            "provenance": "learned",
        }

    @router.get("/active")
    def active_variant() -> dict[str, Any]:
        conservation = _current_conservation_status(graph_store_factory, domain)
        return {
            "variant": service.active_variant(),
            "parameter_adjustments": parameter_service.active_adjustments(),
            "conservation_state": _conservation_label(conservation),
            "bounds": parameter_service.bounds_dict(),
        }

    @router.get("/proposals")
    def parameter_proposals() -> dict[str, Any]:
        conservation = _current_conservation_status(graph_store_factory, domain)
        conservation_label = _conservation_label(conservation)
        parameter_service.rollback_on_conservation(conservation_label, parameter_config)
        proposals = parameter_service.evaluate(
            _demo_parameter_decisions(),
            parameter_config,
            conservation_label,
        )
        return {
            "proposals": [proposal.__dict__ for proposal in proposals],
            "provenance": "demo",
            "note": "Based on synthetic evidence. Real proposals require accumulated verified decisions.",
            "conservation_state": conservation_label,
        }

    @router.post("/generate")
    @serialize_mutation(domain, event="evolution")
    def generate_variant() -> dict[str, Any]:
        return service.generate_variant()

    @router.post("/shadow-test")
    @serialize_mutation(domain, event="evolution")
    def shadow_test(request: ShadowTestRequest) -> dict[str, Any]:
        variant = request.variant
        if variant is None:
            if request.variant_id:
                variant = next(
                    (item for item in service.evolution_log() if item.get("variant_id") == request.variant_id),
                    None,
                )
            if variant is None:
                variant = service.generate_variant()
        decisions = request.decisions or _demo_decisions()
        return service.shadow_test(variant, decisions, batch_size=request.batch_size)

    @router.post("/promote")
    @serialize_mutation(domain, event="evolution")
    def promote(request: PromoteRequest) -> dict[str, Any]:
        return service.promote(request.variant_id)

    @router.post("/apply")
    @serialize_mutation(domain, event="evolution")
    def apply_proposal(request: ApplyProposalRequest) -> dict[str, Any]:
        proposal = parameter_service.find_proposal(request.proposal_id)
        if proposal is None:
            raise HTTPException(status_code=404, detail=f"Proposal {request.proposal_id} not found")
        conservation = _current_conservation_status(graph_store_factory, domain)
        conservation_label = _conservation_label(conservation)
        applied = parameter_service.apply(proposal, parameter_config, conservation_label)
        return {
            "applied": applied,
            "proposal_id": proposal.proposal_id,
            "provenance": "demo",
            "conservation_state": conservation_label,
            "config": dict(parameter_config),
        }

    @router.post("/rollback")
    @serialize_mutation(domain, event="evolution")
    def rollback_parameter(request: RollbackRequest) -> dict[str, Any]:
        rolled_back = parameter_service.rollback(request.parameter, parameter_config)
        return {
            "rolled_back": rolled_back,
            "parameter": request.parameter,
            "config": dict(parameter_config),
        }

    return router


def _current_conservation_status(
    graph_store_factory: GraphStoreFactory | None,
    domain: str,
) -> dict[str, Any]:
    if graph_store_factory is None:
        return {"status": "UNKNOWN", "conservation_status": "UNKNOWN", "domain": domain}
    try:
        store = graph_store_factory()
        counts = _state_counts(store)
        from gae.calibration import conservation_status

        check = conservation_status(
            verified_count=counts["verified_count"],
            correct_count=counts["correct_count"],
            total_decisions=counts["total_decisions"],
            penalty_ratio=counts["penalty_ratio"],
        )
        return {**counts, **_check_payload(check)}
    except Exception:
        return {"status": "UNKNOWN", "conservation_status": "UNKNOWN", "domain": domain}


def _conservation_label(conservation: dict[str, Any]) -> str:
    for key in ("status", "conservation_status", "state"):
        value = conservation.get(key)
        if isinstance(value, str) and value:
            return value.strip().upper()
    return "UNKNOWN"


def _default_parameter_config() -> dict[str, float]:
    preset = TradingPreset()
    return {
        "eta_confirm": float(preset.eta_confirm),
        "eta_override": float(preset.eta_override),
        "penalty_ratio": float(preset.penalty_ratio),
        "temperature": float(preset.temperature),
    }


def _demo_parameter_decisions() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(500):
        rows.append({
            "is_correct": index < 455,
            "was_override": index < 25,
        })
    return rows


def _demo_decisions() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(50):
        rows.append({
            "actual_action": "strong_execution",
            "recommended_action": "partial_execution" if index < 5 else "strong_execution",
            "variant_correct": True,
            "baseline_correct": index >= 5,
        })
    return rows


def _trading_rejection_entries(service: TradingAgentEvolver) -> list[dict[str, Any]]:
    rejected: list[dict[str, Any]] = []
    for entry in service.evolution_log():
        variant_id = str(entry.get("variant_id") or "")
        if not variant_id or str(entry.get("status", "")).lower() == "promoted":
            continue
        batches = int(entry.get("batches") or 0)
        if batches < MIN_SHADOW_BATCHES:
            continue
        check = service.check_promotion(variant_id)
        if check.get("promotable"):
            continue
        reason = _canonical_rejection_reason(str(check.get("reason") or ""))
        rejected.append({
            "variant_id": variant_id,
            "reason": reason,
            "detail": _rejection_detail(reason, check, entry),
            "tested_at": entry.get("created_at"),
        })
    return rejected


def _rejection_log_path() -> Path:
    configured = os.environ.get(REJECTION_LOG_ENV)
    return Path(configured) if configured else DEFAULT_REJECTION_LOG_PATH


def _load_persisted_rejection_summary(path: Path | None = None) -> dict[str, Any] | None:
    log_path = path or _rejection_log_path()
    if not log_path.exists():
        return None
    try:
        payload = json.loads(log_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _merge_rejection_entries(
    live_entries: list[dict[str, Any]],
    persisted_entries: list[Any],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for raw_entry in [*persisted_entries, *live_entries]:
        if not isinstance(raw_entry, dict):
            continue
        variant_id = str(raw_entry.get("variant_id") or raw_entry.get("variantId") or "")
        if not variant_id:
            continue
        merged[variant_id] = {
            "variant_id": variant_id,
            "reason": str(raw_entry.get("reason") or "correctness_floor"),
            "detail": str(raw_entry.get("detail") or "promotion gate rejected variant"),
            "tested_at": raw_entry.get("tested_at") or raw_entry.get("created_at"),
        }
    return list(merged.values())


def _canonical_rejection_reason(reason: str) -> str:
    mapping = {
        "insufficient_improvement": "correctness_floor",
        "conservation_not_green": "conservation",
        "unstable_improvement": "variance_stability",
    }
    return mapping.get(reason, "correctness_floor")


def _rejection_detail(reason: str, check: dict[str, Any], entry: dict[str, Any]) -> str:
    if reason == "correctness_floor":
        improvement = float(entry.get("avg_improvement_pp") or 0.0)
        return f"improvement {improvement:.1f}pp < floor {MIN_IMPROVEMENT_PP:.1f}pp"
    if reason == "conservation":
        return "conservation gate not GREEN"
    variance = float(check.get("variance_pp") or 0.0)
    return f"variance {variance:.1f}pp >= threshold {MAX_VARIANCE_PP:.1f}pp"
