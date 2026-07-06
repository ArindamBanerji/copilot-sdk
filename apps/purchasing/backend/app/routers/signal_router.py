"""Cross-copilot signal read endpoints backed by the SDK outbox."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.services.supplier_signal_publisher import active_supplier_signals, signal_stats


def create_signal_router(outbox_store: Any) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing/signals", tags=["purchasing-signals"])

    @router.get("/supplier/{supplier_name}")
    def supplier_signals(supplier_name: str) -> list[dict[str, Any]]:
        return active_supplier_signals(outbox_store, supplier_name)

    @router.get("/stats")
    def stats() -> dict[str, int]:
        return signal_stats(outbox_store)

    return router
