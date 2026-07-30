"""Trading strategy promotion endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter

from app.routers.journal import _journal_records
from app.services.promotion import PromotionService, _metrics, strategy_key
from copilot_sdk.backend.conservation_router import _check_payload, _state_counts


GraphStoreFactory = Callable[[], Any]


def create_promotion_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    config_dir: str | Path | None = None,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-promotion"])

    def _service() -> PromotionService:
        return PromotionService(config_dir=config_dir)

    def _records() -> list[dict[str, Any]]:
        return _journal_records(graph_store_factory, domain)

    @router.get("/promotion")
    def promotion_state() -> dict[str, Any]:
        service = _service()
        trades = _records()
        return {
            "strategies": _strategy_rows(trades, service),
            "history": service.get_history(),
        }

    @router.post("/promotion/evaluate")
    def evaluate_promotion() -> dict[str, Any]:
        service = _service()
        trades = _records()
        conservation = _conservation_status(graph_store_factory)
        events = service.evaluate(trades, conservation)
        return {
            "events": events,
            "conservation_status": conservation,
            "strategies": _strategy_rows(trades, service),
            "history": service.get_history(),
        }

    return router


def _strategy_rows(trades: list[dict[str, Any]], service: PromotionService) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for trade in trades:
        category = trade.get("category")
        if not category:
            continue
        tag = trade.get("strategy_tag")
        metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
        tag = tag or metadata.get("strategy_tag") or trade.get("thesis_type") or metadata.get("thesis_type")
        key = strategy_key(str(category), str(tag) if tag else None)
        groups.setdefault(key, []).append(trade)

    rows: list[dict[str, Any]] = []
    for key, group in sorted(groups.items()):
        category, tag = key.split(":", 1)
        metrics = _metrics(group)
        rows.append({
            "strategy_key": key,
            "category": category,
            "strategy_tag": None if tag == "default" else tag,
            "tier": service.get_tier(key),
            "win_rate": metrics["win_rate"],
            "verified": metrics["verified_count"],
        })
    return rows


def _conservation_status(graph_store_factory: GraphStoreFactory | None) -> dict[str, Any]:
    if graph_store_factory is None:
        return {"status": "GREEN", "passed": True}
    store = None
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
        return {"status": "RED", "passed": False}
    finally:
        if store is not None:
            store.close()
