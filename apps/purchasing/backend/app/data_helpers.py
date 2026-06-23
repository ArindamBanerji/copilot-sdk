"""Helpers for deterministic Purchasing demo fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SUPPLIERS_PATH = DATA_DIR / "purchasing_suppliers.json"
ORDERS_PATH = DATA_DIR / "purchasing_orders.json"

_supplier_cache: list[dict[str, Any]] | None = None
_order_cache: list[dict[str, Any]] | None = None


def _load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_purchasing_suppliers() -> list[dict[str, Any]]:
    global _supplier_cache
    if _supplier_cache is None:
        _supplier_cache = _load_json(SUPPLIERS_PATH)
    return list(_supplier_cache)


def load_purchasing_orders() -> list[dict[str, Any]]:
    global _order_cache
    if _order_cache is None:
        _order_cache = _load_json(ORDERS_PATH)
    return list(_order_cache)


def reset_purchasing_fixtures() -> None:
    global _supplier_cache, _order_cache
    _supplier_cache = None
    _order_cache = None


def is_sample_data(record: dict) -> bool:
    """Check if a record is K3 demo-fixture data (Rule 67)."""
    if record.get("provenance") == "sample":
        return True
    if record.get("provenance") is not None:
        return False
    supplier_id = str(record.get("supplier_id") or "")
    order_id = str(record.get("order_id") or "")
    return (
        bool(record.get("archetype"))
        or supplier_id.startswith("PUR-SUP-")
        or order_id.startswith("PUR-ORD-")
    )


def assert_no_sample_in_metric(records: list[dict], metric_name: str) -> None:
    """F-26 gate: raise if sample data feeds a computed metric."""
    sample_count = sum(1 for record in records if is_sample_data(record))
    if sample_count > 0:
        raise ValueError(
            f"F-26 VIOLATION: {sample_count}/{len(records)} records "
            f"feeding metric '{metric_name}' have provenance='sample'. "
            "K3 demo-fixture data must not feed computed metrics."
        )


def get_supplier_by_id(supplier_id: str) -> Optional[dict[str, Any]]:
    return next(
        (
            supplier
            for supplier in load_purchasing_suppliers()
            if supplier.get("supplier_id") == supplier_id
        ),
        None,
    )


def get_orders_by_supplier(supplier_id: str) -> list[dict[str, Any]]:
    return [
        order
        for order in load_purchasing_orders()
        if order.get("supplier_id") == supplier_id
    ]


def get_orders_by_category(category: str) -> list[dict[str, Any]]:
    return [
        order
        for order in load_purchasing_orders()
        if order.get("category") == category
    ]
