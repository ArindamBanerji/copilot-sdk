"""Purchasing VLD showcase fixture data.

The vectors in this file were selected after refreshing the Purchasing demo
centroid checkpoint from the regenerated bundle. They are intentionally small
fixtures for VLD demo contracts, not production-order examples.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast


def seed_vld_purchasing_showcase(data_source: dict[str, Any] | str | Path | None = None) -> dict[str, Any]:
    """Seed three Purchasing VLD showcase orders into a dict or JSON directory.

    The function is idempotent and additive. Passing ``None`` returns an in-memory
    fixture payload. Passing a dict mutates and returns that dict. Passing a path
    writes ``purchasing_orders.json`` and ``purchasing_suppliers.json``.
    """
    showcase = _showcase_data()
    if data_source is None:
        return showcase
    if isinstance(data_source, dict):
        _merge_showcase(data_source, showcase)
        return data_source

    base = Path(data_source)
    base.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {"orders": {}, "suppliers": {}}
    for filename, key in (("purchasing_orders.json", "orders"), ("purchasing_suppliers.json", "suppliers")):
        path = base / filename
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            existing[key] = payload if isinstance(payload, dict) else {}
    _merge_showcase(existing, showcase)
    (base / "purchasing_orders.json").write_text(json.dumps(existing["orders"], indent=2, sort_keys=True), encoding="utf-8")
    (base / "purchasing_suppliers.json").write_text(json.dumps(existing["suppliers"], indent=2, sort_keys=True), encoding="utf-8")
    return existing


def showcase_order(order_id: str) -> dict[str, Any] | None:
    """Return one showcase order fixture by id."""
    return cast(dict[str, Any] | None, deepcopy(_showcase_data()["orders"].get(order_id)))


def _merge_showcase(target: dict[str, Any], showcase: dict[str, Any]) -> None:
    orders = target.setdefault("orders", {})
    suppliers = target.setdefault("suppliers", {})
    for order_id, order in showcase["orders"].items():
        orders[order_id] = deepcopy(order)
    for supplier_id, supplier in showcase["suppliers"].items():
        suppliers[supplier_id] = deepcopy(supplier)


def _showcase_data() -> dict[str, Any]:
    return {
        "orders": {
            # VLD-PUR-1: looks like a demand spike on the surface. The refreshed
            # produce geometry scores the surface as order_more (margin ~0.195).
            # The first read, supplier_lead_time=0.20, keeps the recommendation;
            # the second read, a strong substitution/price-memory signal=0.95,
            # flips to order_less (margin ~0.148). This preserves the existing
            # lead-time -> catalog trace while making it valid against the real
            # differentiated Purchasing centroids.
            "VLD-PUR-DEMAND-SPIKE": {
                "order_id": "VLD-PUR-DEMAND-SPIKE",
                "sku": "PUR-FRESH-BERRY-CASE",
                "item": "Fresh berry case",
                "category": "produce",
                "supplier_id": "SUP-PUR-ALT-FRESH",
                "surface_action": "order_more",
                "expected_vld_action": "order_less",
                "budget": 2,
                "factors": {
                    "expected_demand": 0.6846,
                    "day_of_week": 0.4664,
                    "weather_forecast": 0.7015,
                    "event_flag": 0.3365,
                    "historical_waste": 0.5097,
                    "supplier_lead_time": 0.3914,
                    "price_memory_index": 0.4074,
                },
                "demand": {
                    "urgency_score": 0.6846,
                    "confidence": 0.86,
                    "forecast_units": 118,
                    "inventory_units": 43,
                    "safety_stock_units": 28,
                },
                "schedule": {"day_factor": 0.4664, "confidence": 0.65},
                "weather": {"forecast_factor": 0.7015, "confidence": 0.70},
                "event": {"event_factor": 0.3365, "confidence": 0.65},
                "vendor_quality": {
                    "risk_score": 0.5097,
                    "confidence": 0.65,
                    "reliability_score": 0.4903,
                    "quality_incidents_30d": 0,
                    "notes": "Neutral spoilage history; not the decisive read.",
                },
                "lead_time": {
                    "risk_score": 0.20,
                    "confidence": 0.90,
                    "current_days": 2,
                    "baseline_days": 5,
                    "backlog_days": 0,
                    "stretch_pct": -0.60,
                },
                "substitution": {
                    "score": 0.95,
                    "confidence": 1.00,
                    "alternate_vendor": "SUP-PUR-LOCAL-FRESH",
                    "alternate_lead_days": 2,
                    "premium_pct": 0.08,
                },
                "narrative": "Demand appears high, but short lead time plus a strong alternate-source signal changes the recommendation to order less.",
            },
            # VLD-PUR-2: the surface sits near order_as_planned in dry_goods. The
            # first read finds vendor-quality risk=0.72 and flips to skip; the
            # second lead-time read reinforces the skip decision. Evidence values
            # come from PurchasingEvidenceProvider dimensions 4 and 5.
            "VLD-PUR-VENDOR-CASCADE": {
                "order_id": "VLD-PUR-VENDOR-CASCADE",
                "sku": "PUR-DRY-LEGUME-BULK",
                "item": "Bulk legumes",
                "category": "dry_goods",
                "supplier_id": "SUP-PUR-RISKY-DRY",
                "surface_action": "order_as_planned",
                "expected_vld_action": "skip",
                "budget": 2,
                "factors": {
                    "expected_demand": 0.6601,
                    "day_of_week": 0.5255,
                    "weather_forecast": 0.4478,
                    "event_flag": 0.2365,
                    "historical_waste": 0.1538,
                    "supplier_lead_time": 0.5737,
                    "price_memory_index": 0.4566,
                },
                "demand": {
                    "urgency_score": 0.6601,
                    "confidence": 0.70,
                    "forecast_units": 96,
                    "inventory_units": 52,
                    "safety_stock_units": 34,
                },
                "schedule": {"day_factor": 0.5255, "confidence": 0.65},
                "weather": {"forecast_factor": 0.4478, "confidence": 0.65},
                "event": {"event_factor": 0.2365, "confidence": 0.65},
                "vendor_quality": {
                    "risk_score": 0.72,
                    "confidence": 0.90,
                    "reliability_score": 0.28,
                    "quality_incidents_30d": 2,
                    "notes": "Two recent delivery-quality incidents on the same SKU family.",
                },
                "lead_time": {
                    "risk_score": 0.92,
                    "confidence": 0.90,
                    "current_days": 11,
                    "baseline_days": 5,
                    "backlog_days": 6,
                    "stretch_pct": 1.20,
                },
                "substitution": {
                    "score": 0.4566,
                    "confidence": 0.65,
                    "alternate_vendor": "SUP-PUR-STABLE-DRY",
                    "alternate_lead_days": 6,
                    "premium_pct": 0.02,
                },
                "narrative": "The order looks acceptable until vendor-quality and lead-time evidence reveal a supplier cascade risk; VLD recommends skipping this order.",
            },
            # VLD-PUR-S1: high-margin no-investigation control. The refreshed
            # dry_goods geometry scores this vector as order_more with margin
            # >0.59. The demo contract sets budget=0, so VLD conserves the
            # surface decision and produces no trace steps.
            "VLD-PUR-S1-STANDARD": {
                "order_id": "VLD-PUR-S1-STANDARD",
                "sku": "PUR-DRY-STAPLE-REORDER",
                "item": "Staple dry-goods reorder",
                "category": "dry_goods",
                "supplier_id": "SUP-PUR-STABLE-DRY",
                "surface_action": "order_more",
                "expected_vld_action": "order_more",
                "budget": 0,
                "factors": {
                    "expected_demand": 0.58,
                    "day_of_week": 0.50,
                    "weather_forecast": 0.50,
                    "event_flag": 0.50,
                    "historical_waste": 0.20,
                    "supplier_lead_time": 0.20,
                    "price_memory_index": 0.84,
                },
                "demand": {
                    "urgency_score": 0.58,
                    "confidence": 0.92,
                    "forecast_units": 80,
                    "inventory_units": 42,
                    "safety_stock_units": 30,
                },
                "schedule": {"day_factor": 0.50, "confidence": 0.80},
                "weather": {"forecast_factor": 0.50, "confidence": 0.78},
                "event": {"event_factor": 0.50, "confidence": 0.80},
                "vendor_quality": {
                    "risk_score": 0.20,
                    "confidence": 0.90,
                    "reliability_score": 0.80,
                    "quality_incidents_30d": 0,
                    "notes": "Stable vendor and repeatable replenishment pattern.",
                },
                "lead_time": {
                    "risk_score": 0.20,
                    "confidence": 0.88,
                    "current_days": 3,
                    "baseline_days": 5,
                    "backlog_days": 0,
                    "stretch_pct": -0.40,
                },
                "cost_benchmark": {
                    "price_memory_index": 0.84,
                    "confidence": 0.86,
                    "benchmark_unit_cost": 4.80,
                    "quoted_unit_cost": 4.76,
                },
                "narrative": "High-margin reorder control: VLD should not spend investigation budget on an already clear decision.",
            },
        },
        "suppliers": {
            "SUP-PUR-ALT-FRESH": {
                "supplier_id": "SUP-PUR-ALT-FRESH",
                "name": "Local Fresh Alternative",
                "lead_time": {"risk_score": 0.20, "confidence": 0.90, "current_days": 2, "baseline_days": 5},
                "quality": {"risk_score": 0.5097, "confidence": 0.65, "reliability_score": 0.4903, "quality_incidents_30d": 0},
            },
            "SUP-PUR-RISKY-DRY": {
                "supplier_id": "SUP-PUR-RISKY-DRY",
                "name": "Backlogged Dry Goods Supplier",
                "lead_time": {"risk_score": 0.92, "confidence": 0.90, "current_days": 11, "baseline_days": 5},
                "quality": {"risk_score": 0.72, "confidence": 0.90, "reliability_score": 0.28, "quality_incidents_30d": 2},
            },
            "SUP-PUR-STABLE-DRY": {
                "supplier_id": "SUP-PUR-STABLE-DRY",
                "name": "Stable Dry Goods Vendor",
                "lead_time": {"risk_score": 0.20, "confidence": 0.88, "current_days": 3, "baseline_days": 5},
                "quality": {"risk_score": 0.20, "confidence": 0.90, "reliability_score": 0.80, "quality_incidents_30d": 0},
            },
        },
    }


__all__ = ["seed_vld_purchasing_showcase", "showcase_order"]
