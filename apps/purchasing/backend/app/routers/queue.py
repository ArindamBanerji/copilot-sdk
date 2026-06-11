"""Purchasing smart order queue endpoint."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter

from app.data_helpers import load_purchasing_orders


DOMAIN = "purchasing"
GraphStoreFactory = Callable[[], Any]


def create_queue_router(graph_store_factory: GraphStoreFactory | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing", tags=["purchasing-queue"])

    @router.get("/queue")
    def order_queue() -> dict[str, Any]:
        rows = [_recommendation(order) for order in _orders()]
        rows = [row for row in rows if row is not None]
        rows.sort(key=lambda item: item["priority_score"], reverse=True)
        return {
            "queue": rows,
            "count": len(rows),
            "conservation_status": _conservation_status(graph_store_factory),
            "source": "purchasing_fixture_context",
        }

    return router


def _orders() -> list[dict[str, Any]]:
    try:
        return [order for order in load_purchasing_orders() if isinstance(order, dict)]
    except (FileNotFoundError, OSError, ValueError):
        return []


def _recommendation(order: dict[str, Any]) -> dict[str, Any] | None:
    factors = order.get("factors") if isinstance(order.get("factors"), dict) else {}
    expected_demand = _coerce_factor(factors.get("expected_demand"))
    historical_waste = _coerce_factor(factors.get("historical_waste"))
    supplier_lead_time = _coerce_factor(factors.get("supplier_lead_time"))
    priority_score = historical_waste * expected_demand * (1.0 - supplier_lead_time)
    items = order.get("items") if isinstance(order.get("items"), list) else []
    if not items:
        return None
    primary_item = items[0] if isinstance(items[0], dict) else {}
    return {
        "order_id": order.get("order_id"),
        "what_to_order": primary_item.get("name") or primary_item.get("item_id"),
        "how_much": primary_item.get("quantity"),
        "unit": primary_item.get("unit"),
        "from_whom": order.get("supplier_name") or order.get("supplier_id"),
        "supplier_id": order.get("supplier_id"),
        "category": order.get("category"),
        "priority_score": round(priority_score, 6),
        "factors": {
            "historical_waste": historical_waste,
            "expected_demand": expected_demand,
            "supplier_lead_time": supplier_lead_time,
        },
        "data_source": "purchasing_orders_fixture",
    }


def _conservation_status(graph_store_factory: GraphStoreFactory | None) -> dict[str, Any]:
    if graph_store_factory is None:
        return {"status": "BOOTSTRAP", "source": "not_configured"}
    try:
        store = graph_store_factory()
        verified = int(_call_count(store, "count_verified"))
        correct = int(_call_count(store, "count_correct"))
    except Exception:
        return {"status": "UNKNOWN", "source": "graph_store_error"}
    if verified <= 0:
        return {"status": "BOOTSTRAP", "verified_count": 0, "correct_count": 0, "source": "graphstore"}
    accuracy = correct / verified
    return {
        "status": "GREEN" if accuracy >= 0.5 else "AMBER",
        "verified_count": verified,
        "correct_count": correct,
        "accuracy": round(accuracy, 4),
        "source": "graphstore",
    }


def _call_count(store: Any, method_name: str) -> int:
    method = getattr(store, method_name, None)
    if not callable(method):
        return 0
    return int(method(DOMAIN))


def _coerce_factor(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.5
    return max(0.0, min(number, 1.0))
