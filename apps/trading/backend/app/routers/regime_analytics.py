"""Read-only regime analytics endpoint."""

from __future__ import annotations

from typing import Any, Callable, cast

from fastapi import APIRouter, Request

from app.services.regime_analytics import RegimeAnalytics
from copilot_sdk.state.cached_static import cached_static


GraphStoreFactory = Callable[[], Any]


def create_regime_analytics_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-regime-analytics"])

    def payload() -> dict[str, Any]:
        decisions = _read_decisions(graph_store_factory, domain)
        return RegimeAnalytics().compute(decisions)

    @router.get("/regime-analytics")
    @cached_static("regime-analytics")
    def regime_analytics(request: Request) -> dict[str, Any]:
        return cast(dict[str, Any], payload())

    @router.get("/regime-analytics/summary")
    @cached_static("regime-analytics-summary")
    def regime_analytics_summary(request: Request) -> dict[str, Any]:
        return cast(dict[str, Any], payload())

    return router


def _read_decisions(
    graph_store_factory: GraphStoreFactory | None,
    domain: str,
) -> list[dict[str, Any]]:
    if graph_store_factory is None:
        return []

    store = graph_store_factory()
    get_all = getattr(store, "get_all_decisions", None)
    get_decisions = getattr(store, "get_decisions", None)
    if callable(get_all):
        decisions = [dict(decision) for decision in get_all(domain)]
    elif callable(get_decisions):
        decisions = [dict(decision) for decision in get_decisions(domain, limit=10000)]
    else:
        decisions = []

    get_verified = getattr(store, "get_verified_decisions", None)
    if not callable(get_verified):
        return decisions

    verified_by_id = {
        str(decision.get("decision_id")): dict(decision)
        for decision in get_verified(domain)
        if decision.get("decision_id") is not None
    }
    if not verified_by_id:
        return decisions

    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for decision in decisions:
        decision_id = str(decision.get("decision_id"))
        seen.add(decision_id)
        if decision_id in verified_by_id:
            merged.append({**decision, **verified_by_id[decision_id], "verified": True})
        else:
            merged.append(decision)
    for decision_id, decision in verified_by_id.items():
        if decision_id not in seen:
            merged.append({**decision, "verified": True})
    return merged
