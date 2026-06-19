"""Purchasing delivery match endpoints."""

from __future__ import annotations

import time
from datetime import date
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
MATCH_RESULTS: list[dict[str, Any]] = []

GraphStoreFactory = Callable[[], Any]


class MatchSide(BaseModel):
    order_id: str = "UNKNOWN"
    supplier_id: str | None = None
    category: str = "dry_goods"
    item: str | None = None
    quantity: float = Field(gt=0)
    unit_price: float = Field(gt=0)
    expected_date: str | None = None
    received_date: str | None = None
    invoice_date: str | None = None
    factors: dict[str, float] | None = None


class MatchRequest(BaseModel):
    order: MatchSide
    delivery: MatchSide | None = None
    invoice: MatchSide | None = None
    price_memory_index: float | None = None
    qty_tolerance: float | None = None
    price_tolerance: float | None = None
    date_tolerance_days: int | None = None


def create_match_router(graph_store_factory: GraphStoreFactory | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing", tags=["purchasing-match"])

    @router.post("/match")
    def match_delivery(
        payload: dict[str, Any],
        qty_tolerance: float = 0.05,
        price_tolerance: float = 0.03,
        date_tolerance_days: int = 3,
    ) -> dict[str, Any]:
        match_request = _normalize_payload(payload)
        qty_tol = _bounded_tolerance(match_request.qty_tolerance, qty_tolerance)
        price_tol = _bounded_tolerance(match_request.price_tolerance, price_tolerance)
        date_tol = max(0, int(match_request.date_tolerance_days or date_tolerance_days))

        factors = _factors(match_request)
        quantity_variance = (
            _quantity_variance(match_request.order.quantity, match_request.delivery.quantity)
            if match_request.delivery is not None
            else None
        )
        price_variance = (
            _price_variance(match_request.order.unit_price, match_request.invoice.unit_price)
            if match_request.invoice is not None
            else None
        )
        date_variance_days = _date_variance_days(match_request.order, match_request.delivery, match_request.invoice)
        reasons: list[str] = []
        if match_request.delivery is None:
            reasons.append("missing_delivery")
        if match_request.invoice is None:
            reasons.append("missing_invoice")
        if quantity_variance is not None and quantity_variance > qty_tol:
            reasons.append("qty_variance")
        if price_variance is not None and price_variance > price_tol:
            reasons.append("price_variance")
        if date_variance_days is not None and date_variance_days > date_tol:
            reasons.append("date_variance")

        matched = not reasons
        status = _match_status(reasons, quantity_variance, price_variance)
        match_confidence = _match_confidence(status, quantity_variance, price_variance)
        match_score = match_to_factor_score({"match_confidence": match_confidence})
        discrepancy_messages = _discrepancy_messages(
            match_request,
            quantity_variance,
            price_variance,
            date_variance_days,
            reasons,
        )
        exception = (
            _exception(
                match_request,
                quantity_variance,
                price_variance,
                date_variance_days,
                reasons,
                discrepancy_messages,
            )
            if reasons
            else None
        )
        if exception is not None:
            _upsert_exception(exception)

        decision_write = _write_match_decision(
            graph_store_factory,
            match_request,
            factors,
            matched=matched,
            reasons=reasons,
            quantity_variance=quantity_variance or 0.0,
            price_variance=price_variance or 0.0,
            price_tolerance=price_tol,
            match_confidence=match_confidence,
            match_score=match_score,
            discrepancy_messages=discrepancy_messages,
        )

        result = {
            "matched": matched,
            "status": status,
            "order_id": match_request.order.order_id,
            "supplier_id": match_request.order.supplier_id,
            "supplier_name": str(payload.get("supplier_name") or payload.get("supplier") or match_request.order.supplier_id or ""),
            "item": match_request.order.item,
            "amount": round(match_request.order.quantity * match_request.order.unit_price, 2),
            "qty_diff": round(quantity_variance or 0.0, 4),
            "price_diff": round(price_variance or 0.0, 4),
            "date_diff_days": date_variance_days,
            "qty_tolerance": round(qty_tol, 4),
            "price_tolerance": round(price_tol, 4),
            "date_tolerance_days": date_tol,
            "match_confidence": match_confidence,
            "confidence": match_confidence,
            "match_score": match_score,
            "discrepancy_messages": discrepancy_messages,
            "reasons": reasons,
            "exception": exception,
            "decision_write": decision_write,
        }
        _record_result(result)
        return result

    @router.get("/match/queue")
    def match_queue() -> dict[str, Any]:
        recent_results = _recent_results()
        auto_matched_count = sum(1 for result in recent_results if result.get("matched"))
        exception_count = len(PENDING_EXCEPTIONS)
        return {
            "exceptions": list(PENDING_EXCEPTIONS),
            "recent_results": recent_results,
            "count": exception_count,
            "pending_count": exception_count,
            "auto_matched_count": auto_matched_count,
            "exception_count": exception_count,
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


def _bounded_tolerance(body_value: float | None, query_value: float) -> float:
    value = query_value if body_value is None else body_value
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(number, 1.0))


def _normalize_payload(payload: dict[str, Any]) -> MatchRequest:
    order_raw = payload.get("order") if isinstance(payload.get("order"), dict) else _flat_order_payload(payload)
    order = _side_from_payload(order_raw, fallback_order_id="UNKNOWN")
    delivery_raw = payload.get("delivery") if isinstance(payload.get("delivery"), dict) else _flat_delivery_payload(payload, order)
    invoice_raw = payload.get("invoice") if isinstance(payload.get("invoice"), dict) else _flat_invoice_payload(payload, order)
    return MatchRequest(
        order=order,
        delivery=_side_from_payload(delivery_raw, fallback_order_id=order.order_id) if delivery_raw else None,
        invoice=_side_from_payload(invoice_raw, fallback_order_id=order.order_id) if invoice_raw else None,
        price_memory_index=_optional_float(payload.get("price_memory_index")),
        qty_tolerance=_optional_float(payload.get("qty_tolerance")),
        price_tolerance=_optional_float(payload.get("price_tolerance")),
        date_tolerance_days=_optional_int(payload.get("date_tolerance_days")),
    )


def _flat_order_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": payload.get("order_id") or payload.get("orderId"),
        "supplier_id": payload.get("supplier_id") or payload.get("supplierId"),
        "category": payload.get("category"),
        "item": payload.get("item") or payload.get("item_name") or payload.get("itemName") or payload.get("name"),
        "quantity": payload.get("quantity") or payload.get("qty"),
        "unit_price": payload.get("unit_price") or payload.get("unitPrice") or payload.get("price"),
        "expected_date": payload.get("expected_date") or payload.get("order_date") or payload.get("date"),
        "factors": payload.get("factors") if isinstance(payload.get("factors"), dict) else None,
    }


def _flat_delivery_payload(payload: dict[str, Any], order: MatchSide) -> dict[str, Any] | None:
    quantity = _first_present(
        payload.get("delivery_quantity"),
        payload.get("deliveryQuantity"),
        payload.get("delivered_qty"),
        payload.get("deliveredQty"),
        payload.get("received_quantity"),
        payload.get("receivedQuantity"),
    )
    if quantity is None:
        return None
    return {
        "order_id": order.order_id,
        "supplier_id": order.supplier_id,
        "category": order.category,
        "item": order.item,
        "quantity": quantity,
        "unit_price": _first_present(
            payload.get("delivery_unit_price"),
            payload.get("deliveryUnitPrice"),
            payload.get("unit_price"),
            order.unit_price,
        ),
        "received_date": payload.get("received_date") or payload.get("delivery_date") or payload.get("date"),
    }


def _flat_invoice_payload(payload: dict[str, Any], order: MatchSide) -> dict[str, Any] | None:
    unit_price = _first_present(
        payload.get("invoice_unit_price"),
        payload.get("invoiceUnitPrice"),
        payload.get("invoice_price"),
        payload.get("invoicePrice"),
    )
    quantity = _first_present(payload.get("invoice_quantity"), payload.get("invoiceQuantity"), payload.get("invoice_qty"))
    if unit_price is None and quantity is None:
        return None
    return {
        "order_id": order.order_id,
        "supplier_id": order.supplier_id,
        "category": order.category,
        "item": order.item,
        "quantity": quantity if quantity is not None else order.quantity,
        "unit_price": unit_price if unit_price is not None else order.unit_price,
        "invoice_date": payload.get("invoice_date") or payload.get("date"),
    }


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _side_from_payload(raw: Any, *, fallback_order_id: str) -> MatchSide:
    data = raw if isinstance(raw, dict) else {}
    item = _first_item(data)
    quantity = _first_number(
        data.get("quantity"),
        data.get("qty"),
        item.get("quantity"),
        item.get("qty"),
        item.get("count"),
        default=1.0,
    )
    unit_price = _first_number(
        data.get("unit_price"),
        data.get("price"),
        item.get("unit_price"),
        item.get("price"),
        item.get("current_price"),
        default=1.0,
    )
    return MatchSide(
        order_id=str(data.get("order_id") or data.get("orderId") or fallback_order_id),
        supplier_id=data.get("supplier_id") or data.get("supplierId"),
        category=str(data.get("category") or item.get("category") or "dry_goods"),
        item=data.get("item") or data.get("item_name") or item.get("name") or item.get("item_name"),
        quantity=max(float(quantity), 0.0001),
        unit_price=max(float(unit_price), 0.0001),
        expected_date=data.get("expected_date") or data.get("order_date") or data.get("date"),
        received_date=data.get("received_date") or data.get("delivery_date") or data.get("date"),
        invoice_date=data.get("invoice_date") or data.get("date"),
        factors=data.get("factors") if isinstance(data.get("factors"), dict) else None,
    )


def _first_item(data: dict[str, Any]) -> dict[str, Any]:
    items = data.get("items") if isinstance(data.get("items"), list) else []
    return items[0] if items and isinstance(items[0], dict) else {}


def _first_number(*values: Any, default: float) -> float:
    for value in values:
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if number > 0:
            return number
    return default


def _optional_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _exception(
    payload: MatchRequest,
    quantity_variance: float | None,
    price_variance: float | None,
    date_variance_days: int | None,
    reasons: list[str],
    discrepancy_messages: list[str],
) -> dict[str, Any]:
    return {
        "order_id": payload.order.order_id,
        "reason": reasons[0],
        "reasons": list(reasons),
        "delivered_qty": payload.delivery.quantity if payload.delivery else None,
        "ordered_qty": payload.order.quantity,
        "variance_pct": round((quantity_variance or 0.0) * 100, 2),
        "price_variance_pct": round((price_variance or 0.0) * 100, 2),
        "date_variance_days": date_variance_days,
        "invoice_unit_price": payload.invoice.unit_price if payload.invoice else None,
        "ordered_unit_price": payload.order.unit_price,
        "discrepancy_messages": list(discrepancy_messages),
    }


def _upsert_exception(exception: dict[str, Any]) -> None:
    order_id = str(exception.get("order_id") or "")
    PENDING_EXCEPTIONS[:] = [
        item for item in PENDING_EXCEPTIONS if str(item.get("order_id") or "") != order_id
    ]
    PENDING_EXCEPTIONS.append(exception)


def _record_result(result: dict[str, Any]) -> None:
    order_id = str(result.get("order_id") or "")
    MATCH_RESULTS[:] = [
        item for item in MATCH_RESULTS if str(item.get("order_id") or "") != order_id
    ]
    MATCH_RESULTS.append(
        {
            key: result[key]
            for key in (
                "matched",
                "status",
                "order_id",
                "supplier_id",
                "supplier_name",
                "item",
                "amount",
                "match_confidence",
                "confidence",
                "discrepancy_messages",
                "reasons",
            )
            if key in result
        }
    )


def _recent_results() -> list[dict[str, Any]]:
    if MATCH_RESULTS:
        return list(reversed(MATCH_RESULTS[-20:]))
    return [
        {
            "matched": True,
            "status": "FULL_MATCH",
            "order_id": "DEMO-MATCH-1",
            "supplier_id": "SUP-DEMO",
            "supplier_name": "Demo Supplier",
            "item": "Chicken",
            "amount": 1000.0,
            "match_confidence": 1.0,
            "confidence": 1.0,
            "discrepancy_messages": [],
            "reasons": [],
        }
    ]


def _match_status(
    reasons: list[str],
    quantity_variance: float | None,
    price_variance: float | None,
) -> str:
    if any(reason in reasons for reason in ("missing_delivery", "missing_invoice")):
        return "MISSING_RECEIPT"
    if not reasons:
        return "FULL_MATCH"
    if max(quantity_variance or 0.0, price_variance or 0.0) > 0.10:
        return "MISMATCH"
    if "qty_variance" in reasons or "price_variance" in reasons or "date_variance" in reasons:
        return "PARTIAL"
    return "MISMATCH"


def _match_confidence(
    status: str,
    quantity_variance: float | None,
    price_variance: float | None,
) -> float:
    if status == "FULL_MATCH":
        return 1.0
    if status == "MISSING_RECEIPT":
        return 0.3
    if max(quantity_variance or 0.0, price_variance or 0.0) > 0.10:
        return 0.1
    if quantity_variance and not price_variance:
        return 0.6
    if price_variance and not quantity_variance:
        return 0.7
    if quantity_variance and price_variance:
        return 0.5
    return 0.6


def _date_variance_days(
    order: MatchSide,
    delivery: MatchSide | None,
    invoice: MatchSide | None,
) -> int | None:
    expected = _parse_date(order.expected_date)
    actual = _parse_date(delivery.received_date if delivery else None) or _parse_date(invoice.invoice_date if invoice else None)
    if expected is None or actual is None:
        return None
    return max(0, (actual - expected).days)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _discrepancy_messages(
    payload: MatchRequest,
    quantity_variance: float | None,
    price_variance: float | None,
    date_variance_days: int | None,
    reasons: list[str],
) -> list[str]:
    messages: list[str] = []
    unit = "units"
    if "missing_delivery" in reasons:
        messages.append("Missing receipt for this order")
    if "missing_invoice" in reasons:
        messages.append("Missing invoice for this order")
    if "qty_variance" in reasons and payload.delivery is not None and quantity_variance is not None:
        short = payload.order.quantity - payload.delivery.quantity
        direction = "short" if short > 0 else "over"
        messages.append(
            f"Ordered {_format_qty(payload.order.quantity)} {unit}, received {_format_qty(payload.delivery.quantity)} "
            f"({quantity_variance * 100:.0f}% {direction})"
        )
    if "price_variance" in reasons and payload.invoice is not None and price_variance is not None:
        direction = "over" if payload.invoice.unit_price > payload.order.unit_price else "under"
        messages.append(
            f"Invoice ${payload.invoice.unit_price:.2f}/unit vs order ${payload.order.unit_price:.2f}/unit "
            f"({price_variance * 100:.0f}% {direction})"
        )
    if "date_variance" in reasons and date_variance_days is not None:
        messages.append(f"Delivered {date_variance_days} days late")
    return messages


def _format_qty(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.2f}"


def match_to_factor_score(result: dict[str, Any]) -> float:
    """Convert a match result into a bounded scorer factor value."""
    return _coerce_factor(result.get("match_confidence", result.get("confidence", 0.5)))


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
    match_confidence: float,
    match_score: float,
    discrepancy_messages: list[str],
) -> dict[str, Any]:
    if graph_store_factory is None:
        return {"attempted": False, "status": "not_configured", "decision_id": None}
    store = graph_store_factory()
    writer = getattr(store, "write_decision", None)
    if not callable(writer):
        return {"attempted": True, "status": "unsupported_store", "decision_id": None}

    decision_id = f"MATCH-{payload.order.order_id}"
    action = "order_as_planned" if matched else "skip"
    confidence = match_confidence
    metadata = {
        "decision_id": decision_id,
        "entity_id": payload.order.order_id,
        "decision_type": "delivery_match",
        "matched": matched,
        "reasons": list(reasons),
        "quantity_variance": round(quantity_variance, 6),
        "price_variance": round(price_variance, 6),
        "price_tolerance": round(price_tolerance, 6),
        "match_confidence": match_confidence,
        "match_score": match_score,
        "coverage_depth": match_score,
        "discrepancy_messages": list(discrepancy_messages),
        "created_at": time.time(),
    }
    try:
        stored_id = writer(
            DOMAIN,
            payload.order.category,
            action,
            confidence,
            {**factors, "coverage_depth": match_score},
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
