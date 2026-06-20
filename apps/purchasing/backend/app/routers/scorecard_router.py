"""Purchasing IKS scorecard endpoints."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Query

from app.connectors.mock_qbo import MockQBOConnector
from app.data_helpers import assert_no_sample_in_metric
from app.routers.spend_router import qbo_bills_for_spend
from app.services.supplier_scorecard import (
    SCRAPED_EXTERNAL_PROVENANCE,
    SupplierScorecardService,
)
from copilot_sdk import IKSService
from copilot_sdk.scoring.presets import PurchasingPreset


DOMAIN = "purchasing"
D_MAX = 0.30
CATEGORIES = tuple(PurchasingPreset().shape.category_names)
GraphStoreFactory = Callable[[], Any]


def create_scorecard_router(
    graph_store_factory: GraphStoreFactory | None = None,
    connector: MockQBOConnector | None = None,
) -> APIRouter:
    connector = connector or MockQBOConnector()
    router = APIRouter(prefix="/api/purchasing", tags=["scorecard"])

    def _service() -> SupplierScorecardService:
        return SupplierScorecardService(
            orders=_qbo_orders(connector),
            vendors=_qbo_vendors(connector),
            verified_decisions=_verified_decisions(graph_store_factory),
        )

    @router.get("/supplier/{supplier_id}/scorecard")
    def supplier_scorecard(supplier_id: str) -> dict[str, Any]:
        card = _service().build_scorecard(supplier_id)
        if card is None:
            raise HTTPException(status_code=404, detail="supplier scorecard not found")
        return asdict(card)

    @router.get("/suppliers/scorecards")
    def supplier_scorecards(min_orders: int = Query(default=5, ge=1)) -> list[dict[str, Any]]:
        return [asdict(card) for card in _service().build_all(min_orders=min_orders)]

    @router.get("/iks/summary")
    def iks_summary() -> dict[str, Any]:
        return build_iks_summary(graph_store_factory)

    return router


def build_iks_summary(graph_store_factory: GraphStoreFactory | None) -> dict[str, Any]:
    if graph_store_factory is None:
        return _empty_iks_summary()

    try:
        store = graph_store_factory()
        raw = IKSService(
            store,
            domain=DOMAIN,
            shape=PurchasingPreset().shape,
            categories=CATEGORIES,
        ).summary()
    except Exception:
        return _empty_iks_summary()

    return {
        "iks_score": _bounded(float(raw.get("iks", 0.0)), 0.0, 100.0),
        "per_category": {
            category: _bounded(float(value), 0.0, 100.0)
            for category, value in (raw.get("per_category") or {}).items()
        },
        "verified_count": int(raw.get("verified_count") or 0),
        "available": bool(raw.get("available")),
        "source": "graphstore",
        "substantiation_tier": "real_measured",
        "d_max": D_MAX,
    }


def _qbo_orders(connector: MockQBOConnector) -> list[dict[str, Any]]:
    rows = qbo_bills_for_spend(connector)
    po_by_order_id = {
        str(order.get("order_id")): order
        for order in connector.fetch_purchase_orders()
        if isinstance(order, dict) and order.get("order_id")
    }
    output: list[dict[str, Any]] = []
    for row in rows:
        next_row = dict(row)
        purchase_order = po_by_order_id.get(str(row.get("order_id")))
        if purchase_order:
            next_row["purchase_order_date"] = purchase_order.get("order_date")
            next_row["expected_delivery_date"] = purchase_order.get("expected_delivery_date")
        next_row["provenance"] = SCRAPED_EXTERNAL_PROVENANCE
        output.append(next_row)
    assert_no_sample_in_metric(output, "supplier_scorecard")
    return output


def _qbo_vendors(connector: MockQBOConnector) -> list[dict[str, Any]]:
    vendors = []
    for vendor in connector.fetch_vendors():
        if not isinstance(vendor, dict):
            continue
        next_vendor = dict(vendor)
        next_vendor["provenance"] = SCRAPED_EXTERNAL_PROVENANCE
        vendors.append(next_vendor)
    assert_no_sample_in_metric(vendors, "supplier_scorecard")
    return vendors


def _verified_decisions(graph_store_factory: GraphStoreFactory | None) -> list[dict[str, Any]]:
    if graph_store_factory is None:
        return []
    store = graph_store_factory()
    getter = getattr(store, "get_verified_decisions", None)
    if not callable(getter):
        return []
    rows = getter(DOMAIN) or []
    return [row for row in rows if isinstance(row, dict)]


def _empty_iks_summary() -> dict[str, Any]:
    return {
        "iks_score": 0.0,
        "per_category": {category: 0.0 for category in CATEGORIES},
        "verified_count": 0,
        "available": False,
        "source": "graphstore",
        "substantiation_tier": "real_measured",
        "d_max": D_MAX,
    }


def _bounded(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))
