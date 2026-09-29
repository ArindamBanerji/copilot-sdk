"""Trading strategy promotion endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, cast

from fastapi import APIRouter

from app.routers.journal import _journal_records
from app.services.promotion import PromotionService, _metrics, strategy_key
from copilot_sdk.backend.conservation_router import _check_payload
from copilot_sdk.scoring.presets.trading import TradingPreset


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
        return cast(list[dict[str, Any]], _journal_records(graph_store_factory, domain))

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
        conservation = _conservation_status(graph_store_factory, domain)
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
        raw_metadata = trade.get("metadata")
        metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
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


def _conservation_status(
    graph_store_factory: GraphStoreFactory | None,
    domain: str = "trading",
) -> dict[str, Any]:
    if graph_store_factory is None:
        return {"status": "GREEN", "passed": True, "conservation_available": True}
    try:
        store = graph_store_factory()
        count_verified = getattr(store, "count_verified", None)
        count_correct = getattr(store, "count_correct", None)
        count_total = getattr(store, "count_verified_decisions", None)
        if not callable(count_verified) or not callable(count_correct) or not callable(count_total):
            return {"status": "RED", "passed": False, "conservation_available": False}
        raw_verified = count_verified(domain)
        raw_correct = count_correct(domain)
        raw_total = count_total(domain)
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in (raw_verified, raw_correct, raw_total)):
            return {"status": "RED", "passed": False, "conservation_available": False}
        counts = {
            "verified_count": max(int(raw_verified), 0),
            "correct_count": max(int(raw_correct), 0),
            "total_decisions": max(int(raw_total), 0),
            "penalty_ratio": float(getattr(store, "penalty_ratio", 1.0) or 1.0),
        }
        from gae.calibration import conservation_status

        check = conservation_status(
            verified_count=counts["verified_count"],
            correct_count=counts["correct_count"],
            total_decisions=counts["total_decisions"],
            penalty_ratio=counts["penalty_ratio"],
            categories_with_data=store.count_categories_with_n(domain, 1),
            total_categories=len(TradingPreset().shape.category_names),
        )
        return {**counts, **_check_payload(check), "conservation_available": True}
    except (ConnectionError, TimeoutError, RuntimeError):
        return {"status": "RED", "passed": False, "conservation_available": False}
