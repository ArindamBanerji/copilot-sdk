"""Compact data contracts for Purchasing dashboard views."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.data_cache import load_cached_json


_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_ORDER_METADATA_PATH = _DATA_DIR / "order_metadata.json"

router = APIRouter(tags=["dashboard"])


class DashboardOrderProjection(BaseModel):
    """Fields consumed by Dashboard's order history cards."""

    item: str | None = None
    display_name: str | None = None
    category: str | None = None
    action: str | None = None
    reward: float | None = None
    created_at: str | None = None
    total_cost: float | None = None


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


@router.get("/dashboard/orders", response_model=dict[str, DashboardOrderProjection])
def get_dashboard_orders() -> dict[str, DashboardOrderProjection]:
    """Return the compact order projection used by the Dashboard."""
    metadata = load_cached_json(_ORDER_METADATA_PATH)
    if not isinstance(metadata, dict):
        return {}

    latest_by_item: dict[str, tuple[str, str, dict[str, Any]]] = {}
    for decision_id, value in metadata.items():
        if not isinstance(value, dict):
            continue
        item = value.get("item")
        if not isinstance(item, str) or not item:
            continue
        created_at = str(value.get("created_at") or "")
        previous = latest_by_item.get(item)
        if previous is not None and previous[0] >= created_at:
            continue
        latest_by_item[item] = (created_at, str(decision_id), value)

    projection: dict[str, DashboardOrderProjection] = {}
    for _, decision_id, value in latest_by_item.values():
        projection[str(decision_id)] = DashboardOrderProjection(
            item=str(value["item"]) if value.get("item") is not None else None,
            display_name=(
                str(value["display_name"]) if value.get("display_name") is not None else None
            ),
            category=str(value["category"]) if value.get("category") is not None else None,
            action=str(value["action"]) if value.get("action") is not None else None,
            reward=_number(value.get("reward")),
            created_at=(
                str(value["created_at"]) if value.get("created_at") is not None else None
            ),
            total_cost=_number(value.get("total_cost")),
        )
    return projection
