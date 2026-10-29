"""DataOps prompt-evolution rejection telemetry API."""

from __future__ import annotations

import concurrent.futures
import logging
from typing import Any, Callable, cast

from fastapi import APIRouter

from copilot_sdk.evolution import PromptVariantEvolver
from copilot_sdk.scoring.evolution import ScorerEvolution

from ..evolution.evolver_config import (
    DATAOPS_EVOLVER_CONFIG,
    get_dataops_variant_specs,
)

GraphStoreFactory = Callable[[], Any]
REJECTION_SUMMARY_TIMEOUT_SECONDS = 8.0
_REJECTION_CALL_FAILED = object()
_REJECTION_SUMMARY_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=1)

logger = logging.getLogger(__name__)


def create_dataops_evolution_router(
    evolver: PromptVariantEvolver | None = None,
    graph_store_factory: GraphStoreFactory | None = None,
    domain: str = "dataops",
    include_persisted_rejections: bool = False,
) -> APIRouter:
    """Create DataOps-specific evolution telemetry routes."""

    router = APIRouter(
        prefix="/api/dataops/evolution",
        tags=["dataops-evolution"],
    )
    use_persisted_rejections = evolver is None or include_persisted_rejections
    service = evolver or _default_dataops_evolver()
    parameter_service = ScorerEvolution(domain)

    @router.get("/log")
    def evolution_log() -> list[dict[str, Any]]:
        variant_entries = [
            {"kind": "variant", **entry}
            for entry in _dataops_variant_log(service)
        ]
        parameter_entries = [
            {"kind": "parameter", **entry}
            for entry in parameter_service.evolution_log()
        ]
        return variant_entries + parameter_entries

    @router.get("/rejection-summary")
    def rejection_summary() -> dict[str, Any]:
        result = _guarded_rejection_summary()
        if result is _REJECTION_CALL_FAILED:
            return {
                "total_tested": 0,
                "total_promoted": 0,
                "total_rejected": 0,
                "rejection_breakdown": {},
                "rejected_variants": [],
                "provenance": "timeout",
                "degraded": True,
            }
        return cast(dict[str, Any], result)

    def _rejection_summary_payload() -> dict[str, Any]:
        persisted: dict[str, Any] | None = None
        if use_persisted_rejections and graph_store_factory is not None:
            try:
                raw_persisted = graph_store_factory().get_evolution(
                    domain,
                    "preseed_rejection_summary",
                )
                if isinstance(raw_persisted, dict):
                    persisted = raw_persisted
            except Exception as exc:
                logger.warning("DataOps persisted rejection summary unavailable: %s", exc)
        entries = _persisted_rejection_entries(persisted)
        breakdown = {
            "correctness_floor": 0,
            "conservation": 0,
            "variance_stability": 0,
        }
        for entry in entries:
            reason = str(entry.get("reason") or "")
            if reason in breakdown:
                breakdown[reason] += 1
        persisted_tested = int((persisted or {}).get("total_tested") or 0)
        persisted_promoted = int((persisted or {}).get("total_promoted") or 0)
        origins = {str(entry["provenance"]) for entry in entries}
        provenance = (
            next(iter(origins))
            if len(origins) == 1
            else "mixed"
            if origins
            else "learned"
        )
        return {
            "total_tested": persisted_tested,
            "total_promoted": persisted_promoted,
            "total_rejected": len(entries),
            "rejection_breakdown": breakdown,
            "rejected_variants": entries[:10],
            "provenance": provenance,
        }

    def _guarded_rejection_summary() -> dict[str, Any] | object:
        future = _REJECTION_SUMMARY_EXECUTOR.submit(_rejection_summary_payload)
        try:
            return future.result(timeout=REJECTION_SUMMARY_TIMEOUT_SECONDS)
        except concurrent.futures.TimeoutError:
            return _REJECTION_CALL_FAILED

    @router.get("/active")
    def active_variant() -> dict[str, Any]:
        variants = _dataops_variant_log(service)
        active = [
            entry
            for entry in variants
            if str(entry.get("status") or "").lower() == "active"
        ]
        return {
            "variant": active[0] if active else None,
            "active_variants": active,
            "parameter_adjustments": parameter_service.active_adjustments(),
            "domain": domain,
        }

    return router


def _default_dataops_evolver() -> PromptVariantEvolver:
    service = PromptVariantEvolver(config=DATAOPS_EVOLVER_CONFIG)
    service.register_variants(get_dataops_variant_specs())
    return service


def _dataops_variant_log(service: PromptVariantEvolver) -> list[dict[str, Any]]:
    summary = service.get_summary()
    variants = summary.get("variants", [])
    return [dict(entry) for entry in variants if isinstance(entry, dict)]


def _persisted_rejection_entries(
    persisted: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Normalize rejection evidence read from the DataOps graph store."""

    entries: list[dict[str, Any]] = []
    for raw_entry in (persisted or {}).get("rejected_variants", []):
        if not isinstance(raw_entry, dict):
            continue
        variant_id = str(
            raw_entry.get("variant_id") or raw_entry.get("variantId") or ""
        )
        if not variant_id:
            continue
        reason = _canonical_rejection_reason(str(raw_entry.get("reason") or ""))
        entries.append(
            {
                "variant_id": variant_id,
                "reason": reason,
                "detail": str(
                    raw_entry.get("detail") or _default_rejection_detail(reason)
                ),
                "tested_at": raw_entry.get("tested_at")
                or raw_entry.get("created_at"),
                "provenance": str(
                    raw_entry.get("provenance")
                    or (persisted or {}).get("provenance")
                    or "learned"
                ),
            }
        )
    return entries


def _canonical_rejection_reason(reason: str) -> str:
    normalized = reason.strip().lower()
    mapping = {
        "insufficient_improvement": "correctness_floor",
        "correctness_floor": "correctness_floor",
        "promotion_min_samples": "correctness_floor",
        "conservation_not_green": "conservation",
        "conservation_gate_red": "conservation",
        "conservation_gate_unsafe": "conservation",
        "conservation_gate_unavailable": "conservation",
        "conservation": "conservation",
        "unstable_improvement": "variance_stability",
        "variance_stability": "variance_stability",
    }
    return mapping.get(normalized, "correctness_floor")


def _default_rejection_detail(reason: str) -> str:
    if reason == "conservation":
        return "conservation gate did not authorize DataOps promotion"
    if reason == "variance_stability":
        return "pipeline outcome variance exceeded the stability threshold"
    return "DataOps correctness improvement did not meet the promotion floor"
