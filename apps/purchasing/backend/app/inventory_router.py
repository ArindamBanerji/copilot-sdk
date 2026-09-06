"""Compact inventory data contract for the Purchasing frontend."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.data_cache import load_cached_json


_APP_DIR = Path(__file__).resolve().parent
_DATA_DIR = _APP_DIR.parent / "data"
_ITEMS_PATH = _APP_DIR / "items.json"
_WASTE_HISTORY_PATH = _DATA_DIR / "waste_history.json"
_EVOLUTION_FIXTURES_PATH = _DATA_DIR / "evolution_fixtures.json"

router = APIRouter(tags=["inventory"])


class InventorySummaryItem(BaseModel):
    """Fields needed to render one catalog item and its waste summary."""

    item_id: str | None = None
    name: str
    display_name: str | None = None
    emoji: str | None = None
    category: str | None = None
    unit: str | None = None
    par_level: float | None = None
    usage_range: str | list[float] | None = None
    supplier: str | None = None
    supplier_lead_time: float | None = None
    unit_price: float | None = None
    event_sensitivity: float | None = None
    waste_history: dict[str, Any] = Field(default_factory=dict)
    waste_average_pct: float = 0.0
    waste_trend: str = "unknown"
    variant_count: int = 0


class InventorySummaryResponse(BaseModel):
    """Bounded inventory response returned by the summary endpoint."""

    items: list[InventorySummaryItem]
    variants: list[dict[str, Any]]
    categories: list[str]
    generated_at: str


def _as_records(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [record for record in value if isinstance(record, dict)]


def _as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _waste_values(history: dict[str, Any], name: str) -> list[float]:
    values = history.get(name, [])
    if not isinstance(values, list):
        return []
    return [float(value) for value in values if isinstance(value, (int, float))]


def _waste_payload(name: str, values: list[float]) -> dict[str, Any]:
    return {"item": name, "waste_pct": values, "count": len(values)}


def _waste_trend(values: list[float]) -> str:
    if len(values) < 2:
        return "unknown"
    delta = values[-1] - values[0]
    if abs(delta) < 0.01:
        return "flat"
    return "up" if delta > 0 else "down"


def _variant_records() -> list[dict[str, Any]]:
    if not _EVOLUTION_FIXTURES_PATH.exists():
        return []
    payload = _as_mapping(load_cached_json(_EVOLUTION_FIXTURES_PATH))
    fields = {
        "id",
        "event_type",
        "variant_id",
        "description",
        "graph_context",
        "metadata",
        "magnitude",
        "source_copilot",
        "source_rule",
        "match",
    }
    return [{key: value for key, value in variant.items() if key in fields} for variant in _as_records(payload.get("variants"))]


def _is_approved(variant: dict[str, Any]) -> bool:
    status = str(variant.get("status") or variant.get("event_type") or variant.get("eventType") or "").lower()
    return status in {"promoted", "approved", "promotion_approved"}


def _matches_item(item: dict[str, Any], variant: dict[str, Any]) -> bool:
    if not _is_approved(variant):
        return False
    match = variant.get("match")
    if not isinstance(match, dict):
        return True
    categories = match.get("categories")
    if not isinstance(categories, list) or not categories:
        return True
    return str(item.get("category") or "") in {str(category) for category in categories}


@router.get("/inventory/summary", response_model=InventorySummaryResponse)
def inventory_summary() -> InventorySummaryResponse:
    """Return one compact, render-ready record per catalog item."""
    items = _as_records(load_cached_json(_ITEMS_PATH))
    waste_history = _as_mapping(load_cached_json(_WASTE_HISTORY_PATH))
    variants = _variant_records()
    summary_items: list[InventorySummaryItem] = []
    categories: list[str] = []

    for item in items:
        name = str(item.get("name") or "")
        values = _waste_values(waste_history, name)
        category = item.get("category")
        category_name = str(category) if category is not None else None
        if category_name and category_name not in categories:
            categories.append(category_name)
        matching_variants = [variant for variant in variants if _matches_item(item, variant)]
        summary_items.append(
            InventorySummaryItem(
                item_id=str(item["item_id"]) if item.get("item_id") is not None else None,
                name=name,
                display_name=str(item["display_name"]) if item.get("display_name") is not None else None,
                emoji=str(item["emoji"]) if item.get("emoji") is not None else None,
                category=category_name,
                unit=str(item["unit"]) if item.get("unit") is not None else None,
                par_level=float(item["par_level"]) if isinstance(item.get("par_level"), (int, float)) else None,
                usage_range=item.get("usage_range") if isinstance(item.get("usage_range"), (str, list)) else None,
                supplier=str(item["supplier"]) if item.get("supplier") is not None else None,
                supplier_lead_time=float(item["supplier_lead_time"])
                if isinstance(item.get("supplier_lead_time"), (int, float))
                else None,
                unit_price=float(item["unit_price"]) if isinstance(item.get("unit_price"), (int, float)) else None,
                event_sensitivity=float(item["event_sensitivity"])
                if isinstance(item.get("event_sensitivity"), (int, float))
                else None,
                waste_history=_waste_payload(name, values),
                waste_average_pct=sum(values) / len(values) if values else 0.0,
                waste_trend=_waste_trend(values),
                variant_count=len(matching_variants),
            )
        )

    return InventorySummaryResponse(
        items=summary_items,
        variants=variants,
        categories=categories,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
