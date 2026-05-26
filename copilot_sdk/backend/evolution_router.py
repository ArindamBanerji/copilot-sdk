"""FastAPI evolution router factory backed by SDK AgentEvolver."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Query

from copilot_sdk.evolution import (
    AgentEvolver,
    DefaultPromotionGate,
    DefaultShadowRunner,
    InMemoryEvolutionLedger,
)


def create_evolution_router(
    graph_store_factory: Callable[[], Any] | None = None,
    domain: str = "unknown",
    evolver_factory: Callable[[], AgentEvolver] | None = None,
    variant_provider: Callable[[], list[dict[str, Any]]] | None = None,
) -> APIRouter:
    if graph_store_factory is not None and not callable(graph_store_factory):
        raise TypeError("graph_store_factory must be callable or None")
    if evolver_factory is not None and not callable(evolver_factory):
        raise TypeError("evolver_factory must be callable or None")

    router = APIRouter(prefix="/api/evolution", tags=["evolution"])
    evolver_cache: dict[str, AgentEvolver | None] = {"evolver": None}

    def _get_evolver() -> AgentEvolver:
        if evolver_cache["evolver"] is None:
            if evolver_factory is not None:
                evolver_cache["evolver"] = evolver_factory()
            else:
                graph_store = graph_store_factory() if graph_store_factory is not None else None
                ledger = InMemoryEvolutionLedger(evolution_store=graph_store, domain=domain)
                evolver_cache["evolver"] = AgentEvolver(
                    ledger=ledger,
                    shadow_runner=DefaultShadowRunner(),
                    promotion_gate=DefaultPromotionGate(),
                )
        return evolver_cache["evolver"]

    @router.get("/variants")
    def variants() -> dict[str, Any]:
        evolver = _get_evolver()
        active_rules = sorted(evolver.get_active_rules())
        promoted_rules = evolver.get_promoted_rules()
        variants_payload = _provided_variants(variant_provider)
        return {
            "domain": domain,
            "variants": variants_payload,
            "active_rules": active_rules,
            "promoted_rules": promoted_rules,
            "total_active": len(active_rules),
            "total_promoted": len(promoted_rules),
        }

    @router.get("/history")
    def history(
        rule_name: str | None = None,
        limit: int = Query(50, ge=0, le=500),
    ) -> dict[str, Any]:
        evolver = _get_evolver()
        events = evolver.get_evolution_history(rule_name=rule_name, limit=limit)
        return {
            "domain": domain,
            "events": events,
            "count": len(events),
        }

    @router.get("/promoted")
    def promoted() -> dict[str, Any]:
        evolver = _get_evolver()
        return {
            "domain": domain,
            "promoted": evolver.get_promoted_rules(),
        }

    return router


def _provided_variants(provider: Callable[[], list[dict[str, Any]]] | None) -> list[dict[str, Any]]:
    if provider is None:
        return []
    try:
        return list(provider() or [])
    except Exception:
        return []
