"""Graph-backed evidence traversal endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request


def create_traversal_router() -> APIRouter:
    router = APIRouter(prefix="/api/traversal", tags=["traversal"])

    @router.get("/decision_movement")
    def decision_movement(decision_id: str, request: Request) -> list[dict[str, Any]]:
        store = request.app.state.graph_store
        domain = getattr(request.app.state, "domain", "trading")
        return store.decision_movement(domain=domain, decision_id=decision_id)

    @router.get("/contextual_judgment")
    def contextual_judgment(entity_group: str, category: str, request: Request) -> list[dict[str, Any]]:
        store = request.app.state.graph_store
        domain = getattr(request.app.state, "domain", "trading")
        return store.contextual_judgment(domain=domain, entity_group=entity_group, category=category)

    @router.get("/promotion_basis")
    def promotion_basis(rule_id: str, request: Request) -> list[dict[str, Any]]:
        store = request.app.state.graph_store
        domain = getattr(request.app.state, "domain", "trading")
        return store.promotion_basis(domain=domain, rule_id=rule_id)

    @router.get("/transfer_witness")
    def transfer_witness(
        source_domain: str,
        target_domain: str,
        request: Request,
        pattern_id: str = "any",
    ) -> list[dict[str, Any]]:
        store = request.app.state.graph_store
        return store.transfer_witness(
            source_domain=source_domain, target_domain=target_domain, pattern_id=pattern_id
        )

    return router
