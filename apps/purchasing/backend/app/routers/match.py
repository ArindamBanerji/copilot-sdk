"""Purchasing delivery match endpoints."""

from __future__ import annotations

import time
from typing import Any, Callable

from fastapi import APIRouter
from pydantic import BaseModel, Field


DOMAIN = "purchasing"
FACTOR_NAMES = (
    "expected_demand",
    "day_of_week",
    "weather_forecast",
    "event_flag",
    "historical_waste",
    "supplier_lead_time",
    "price_memory_index",
)
PENDING_EXCEPTIONS: list[dict[str, Any]] = []

GraphStoreFactory = Callable[[], Any]


class MatchSide(BaseModel):
    order_id: str
    supplier_id: str | None = None
    category: str = "dry_goods"
    item: str | None = None
    quantity: float = Field(gt=0)
    unit_price: float = Field(gt=0)
    factors: dict[str, float] | None = None


class MatchRequest(BaseModel):
    order: MatchSide
    delivery: MatchSide
    invoice: MatchSide
    price_memory_index: float | None = None


def create_match_router(graph_store_factory: GraphStoreFactory | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing", tags=["purchasing-match"])

    @router.post("/match")
    def match_delivery(payload: MatchRequest) -> dict[str, Any]:
        factors = _factors(payload)
        quantity_variance = _quantity_variance(payload.order.quantity, payload.delivery.quantity)
        price_variance = _price_variance(payload.order.unit_price, payload.invoice.unit_price)
        price_tolerance = _price_tolerance(factors.get("price_memory_index"))
        reasons: list[str] = []
        if quantity_variance > 0.05:
            reasons.append("qty_variance")
        if price_variance > price_tolerance:
            reasons.append("price_variance")

        matched = not reasons
        exception = _exception(payload, quantity_variance, price_variance, reasons) if reasons else None
        if exception is not None:
            _upsert_exception(exception)

        decision_write = _write_match_decision(
            graph_store_factory,
            payload,
            factors,
            matched=matched,
            reasons=reasons,
            quantity_variance=quantity_variance,
            price_variance=price_variance,
            price_tolerance=price_tolerance,
        )

        return {
            "matched": matched,
            "order_id": payload.order.order_id,
            "qty_diff": round(quantity_variance, 4),
            "price_diff": round(price_variance, 4),
            "price_tolerance": round(price_tolerance, 4),
            "reasons": reasons,
            "exception": exception,
            "decision_write": decision_write,
        }

    @router.get("/match/queue")
    def match_queue() -> dict[str, Any]:
        return {
            "exceptions": list(PENDING_EXCEPTIONS),
            "count": len(PENDING_EXCEPTIONS),
            "source": "router_memory",
        }

    return router


def _quantity_variance(ordered_qty: float, delivered_qty: float) -> float:
    if ordered_qty <= 0:
        return 1.0
    return abs(float(delivered_qty) - float(ordered_qty)) / float(ordered_qty)


def _price_variance(expected_price: float, invoice_price: float) -> float:
    if expected_price <= 0:
        return 1.0
    return abs(float(invoice_price) - float(expected_price)) / float(expected_price)


def _price_tolerance(price_memory_index: float | None) -> float:
    if price_memory_index is None:
        return 0.10
    bounded = max(0.0, min(float(price_memory_index), 1.0))
    return 0.10 + ((1.0 - bounded) * 0.15)


def _factors(payload: MatchRequest) -> dict[str, float]:
    source = payload.order.factors or {}
    output = {name: _coerce_factor(source.get(name, 0.5)) for name in FACTOR_NAMES}
    if payload.price_memory_index is not None:
        output["price_memory_index"] = _coerce_factor(payload.price_memory_index)
    return output


def _coerce_factor(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.5
    return max(0.0, min(number, 1.0))


def _exception(
    payload: MatchRequest,
    quantity_variance: float,
    price_variance: float,
    reasons: list[str],
) -> dict[str, Any]:
    return {
        "order_id": payload.order.order_id,
        "reason": reasons[0],
        "reasons": list(reasons),
        "delivered_qty": payload.delivery.quantity,
        "ordered_qty": payload.order.quantity,
        "variance_pct": round(quantity_variance * 100, 2),
        "price_variance_pct": round(price_variance * 100, 2),
        "invoice_unit_price": payload.invoice.unit_price,
        "ordered_unit_price": payload.order.unit_price,
    }


def _upsert_exception(exception: dict[str, Any]) -> None:
    order_id = str(exception.get("order_id") or "")
    PENDING_EXCEPTIONS[:] = [
        item for item in PENDING_EXCEPTIONS if str(item.get("order_id") or "") != order_id
    ]
    PENDING_EXCEPTIONS.append(exception)


def _write_match_decision(
    graph_store_factory: GraphStoreFactory | None,
    payload: MatchRequest,
    factors: dict[str, float],
    *,
    matched: bool,
    reasons: list[str],
    quantity_variance: float,
    price_variance: float,
    price_tolerance: float,
) -> dict[str, Any]:
    if graph_store_factory is None:
        return {"attempted": False, "status": "not_configured", "decision_id": None}
    store = graph_store_factory()
    writer = getattr(store, "write_decision", None)
    if not callable(writer):
        return {"attempted": True, "status": "unsupported_store", "decision_id": None}

    decision_id = f"MATCH-{payload.order.order_id}"
    action = "order_as_planned" if matched else "skip"
    confidence = 0.95 if matched else 0.65
    metadata = {
        "decision_id": decision_id,
        "entity_id": payload.order.order_id,
        "decision_type": "delivery_match",
        "matched": matched,
        "reasons": list(reasons),
        "quantity_variance": round(quantity_variance, 6),
        "price_variance": round(price_variance, 6),
        "price_tolerance": round(price_tolerance, 6),
        "created_at": time.time(),
    }
    try:
        stored_id = writer(
            DOMAIN,
            payload.order.category,
            action,
            confidence,
            factors,
            metadata=metadata,
        )
    except Exception as exc:
        return {
            "attempted": True,
            "status": "failed",
            "decision_id": None,
            "error": str(exc),
        }
    return {"attempted": True, "status": "written", "decision_id": str(stored_id)}
