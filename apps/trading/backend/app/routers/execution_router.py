"""Trading execution analysis endpoints."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable

from fastapi import APIRouter

from app.routers.data_import import _trade_store_ref
from app.services.execution_analysis import ExecutionAnalyzer


GraphStoreFactory = Callable[[], Any]


def create_execution_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading/execution", tags=["trading-execution"])
    analyzer = ExecutionAnalyzer()

    def _trades() -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for trade in list(_trade_store_ref):
            records.append(_as_record(trade))
        if graph_store_factory is not None:
            store = None
            try:
                store = graph_store_factory()
                for decision in store.get_all_decisions(domain):
                    records.append(_as_record(decision))
            except Exception:
                pass
            finally:
                close = getattr(store, "close", None)
                if callable(close):
                    close()
        return records

    @router.get("/analysis")
    def analysis() -> dict[str, Any]:
        return asdict(analyzer.analyze(_trades()))

    @router.get("/summary")
    def summary() -> dict[str, Any]:
        comparison = analyzer.analyze(_trades())
        return {
            "broker_count": len(comparison.brokers),
            "best_broker": comparison.best_broker,
            "annual_savings_estimate": comparison.annual_savings_estimate,
            "recommendation": comparison.recommendation,
            "brokers": [
                {
                    "broker": broker.broker,
                    "trade_count": broker.trade_count,
                    "avg_slippage": broker.avg_slippage,
                    "fill_rate": broker.fill_rate,
                    "avg_fill_time_seconds": broker.avg_fill_time_seconds,
                }
                for broker in comparison.brokers
            ],
        }

    return router


def _as_record(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        raw = value.to_dict()
        return dict(raw) if isinstance(raw, dict) else {}
    if isinstance(value, dict):
        return dict(value)
    return {}
