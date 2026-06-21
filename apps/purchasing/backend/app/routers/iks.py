"""Purchasing IKS and supplier scorecard endpoints."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from fastapi import APIRouter, HTTPException

from copilot_sdk import IKSService
from copilot_sdk.scoring.presets import PurchasingPreset


DOMAIN = "purchasing"
CATEGORIES = tuple(PurchasingPreset().shape.category_names)
GraphStoreFactory = Callable[[], Any]


def create_iks_router(graph_store_factory: GraphStoreFactory | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing", tags=["purchasing-iks"])

    @router.get("/iks")
    def iks_summary() -> dict[str, Any]:
        store = _graph_store(graph_store_factory)
        service = IKSService(
            store,
            domain=DOMAIN,
            shape=PurchasingPreset().shape,
            categories=CATEGORIES,
        )
        return service.summary()

    @router.get("/suppliers/{supplier_id}/scorecard")
    def supplier_scorecard(supplier_id: str) -> dict[str, Any]:
        store = _graph_store(graph_store_factory)
        graph_rows = _supplier_rows_from_graph(store, supplier_id)
        if graph_rows:
            return _scorecard_from_graph(supplier_id, graph_rows)
        raise HTTPException(status_code=404, detail="supplier scorecard not found")

    return router


class _EmptyStore:
    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        return []


def _graph_store(graph_store_factory: GraphStoreFactory | None) -> Any:
    if graph_store_factory is None:
        return _EmptyStore()
    return graph_store_factory()


def _supplier_rows_from_graph(store: Any, supplier_id: str) -> list[dict[str, Any]]:
    getter = getattr(store, "get_verified_decisions", None)
    if not callable(getter):
        return []
    try:
        rows = getter(DOMAIN) or []
    except Exception:
        return []
    return [
        row
        for row in rows
        if isinstance(row, dict) and _row_supplier_id(row) == supplier_id
    ]


def _scorecard_from_graph(supplier_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    otif_values = [_bool_value(row, "otif", default=True) for row in rows]
    exception_values = [_bool_value(row, "exception", default=False) for row in rows]
    return {
        "supplier_id": supplier_id,
        "otif_rate": _ratio(sum(1 for value in otif_values if value), len(otif_values)),
        "exception_rate": _ratio(sum(1 for value in exception_values if value), len(exception_values)),
        "price_memory": _last_prices_by_category(rows),
        "seasonal_patterns": _seasonal_patterns(rows),
        "source": "graphstore",
    }


def _row_supplier_id(row: dict[str, Any]) -> str:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    factors = row.get("factors") if isinstance(row.get("factors"), dict) else {}
    factor_metadata = factors.get("metadata") if isinstance(factors.get("metadata"), dict) else {}
    return str(
        row.get("supplier_id")
        or metadata.get("supplier_id")
        or factor_metadata.get("supplier_id")
        or ""
    )


def _bool_value(row: dict[str, Any], key: str, *, default: bool) -> bool:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    outcome_metadata = row.get("outcome_metadata") if isinstance(row.get("outcome_metadata"), dict) else {}
    context = outcome_metadata.get("context") if isinstance(outcome_metadata.get("context"), dict) else {}
    value = row.get(key, metadata.get(key, context.get(key, default)))
    return bool(value)


def _last_prices_by_category(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        category = str(row.get("category") or _metadata(row).get("category") or "unknown")
        price = _finite_float(row.get("invoice_price", _metadata(row).get("invoice_price")), default=None)
        if price is None:
            continue
        grouped[category].append(
            {
                "category": category,
                "price": price,
            }
        )
    output: list[dict[str, Any]] = []
    for category in sorted(grouped):
        output.extend(grouped[category][-5:])
    return output


def _seasonal_patterns(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seasons = [
        _metadata(row).get("season")
        for row in rows
        if _metadata(row).get("season")
    ]
    return [{"season": str(season)} for season in sorted(set(seasons))]


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 4)


def _bounded(value: Any) -> float:
    return max(0.0, min(_finite_float(value, default=0.0), 1.0))


def _finite_float(value: Any, *, default: float | None) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number
