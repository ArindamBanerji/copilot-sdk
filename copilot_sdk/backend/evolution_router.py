"""FastAPI evolution router factory backed by SDK AgentEvolver."""

from __future__ import annotations

import inspect
from typing import Any, Callable

from fastapi import APIRouter, Query

from copilot_sdk.evolution import (
    AgentEvolver,
    DefaultPromotionGate,
    DefaultShadowRunner,
    InMemoryEvolutionLedger,
)


def create_evolution_router(
    graph_store_factory: Callable[[], Any] | str | None = None,
    domain: str = "unknown",
    ledger_provider: Callable[[], Any] | Any | None = None,
    variant_provider: Callable[[], list[dict[str, Any]]] | None = None,
) -> APIRouter:
    legacy_mount = isinstance(graph_store_factory, str) or ledger_provider is not None
    if isinstance(graph_store_factory, str):
        domain = graph_store_factory
        graph_store_factory = None
    if graph_store_factory is None and ledger_provider is not None:
        graph_store_factory = ledger_provider if callable(ledger_provider) else lambda: ledger_provider

    router = APIRouter(prefix="/evolution" if legacy_mount else "/api/evolution", tags=["evolution"])
    evolver_cache: dict[str, AgentEvolver | None] = {"evolver": None}

    def _get_evolver() -> AgentEvolver:
        if evolver_cache["evolver"] is None:
            graph_store = graph_store_factory() if graph_store_factory is not None else None
            ledger = InMemoryEvolutionLedger(graph_store=graph_store)
            evolver_cache["evolver"] = AgentEvolver(
                ledger=ledger,
                shadow_runner=DefaultShadowRunner(),
                promotion_gate=DefaultPromotionGate(),
            )
        return evolver_cache["evolver"]

    @router.get("/variants")
    async def variants() -> dict[str, Any]:
        if legacy_mount:
            legacy_variants = await _legacy_variants(graph_store_factory)
            return {
                "domain": domain,
                "engine": {"gae": "gae.evolution", "component": "get_recent_events"},
                "variants": legacy_variants,
                "active_rules": [],
                "promoted_rules": [],
                "total_active": 0,
                "total_promoted": 0,
            }
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


async def _legacy_variants(provider: Callable[[], Any] | None) -> list[dict[str, Any]]:
    if provider is None:
        return []
    try:
        value = provider()
        if inspect.isawaitable(value):
            value = await value
        run_query = getattr(value, "run_query", None)
        if not callable(run_query):
            return []
        result = run_query("")
        if inspect.isawaitable(result):
            result = await result
        return list(result or [])
    except Exception:
        return []
