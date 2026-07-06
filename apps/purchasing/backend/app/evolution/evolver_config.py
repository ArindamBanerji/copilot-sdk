"""Purchasing AgentEvolver variant configuration."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from copilot_sdk.evolution import PromptEvolverConfig, VariantSpec

try:
    from copilot_sdk.scoring.presets.purchasing import PurchasingPreset

    _CATEGORIES = list(PurchasingPreset().shape.category_names)
except Exception:
    _CATEGORIES = ["protein", "produce", "dairy", "dry_goods", "beverages"]


PURCHASING_VARIANTS: tuple[VariantSpec, ...] = (
    VariantSpec(
        id="WASTE_THRESHOLD_v1",
        family="waste_threshold",
        version=1,
        status="active",
        metadata={
            "name": "Waste threshold baseline",
            "description": "Current food-service waste versus stockout penalty balance.",
            "over_order_penalty": 0.30,
            "under_order_penalty": 0.70,
        },
    ),
    VariantSpec(
        id="WASTE_THRESHOLD_v2",
        family="waste_threshold",
        version=2,
        status="shadow",
        metadata={
            "name": "Waste threshold balanced",
            "description": "Less asymmetric waste versus stockout penalty balance.",
            "over_order_penalty": 0.40,
            "under_order_penalty": 0.60,
        },
    ),
    VariantSpec(
        id="LEAD_TIME_BUFFER_v1",
        family="lead_time_buffer",
        version=1,
        status="active",
        metadata={
            "name": "Lead time buffer baseline",
            "description": "Current supplier lead-time buffer and reliability floor.",
            "buffer_days": 2,
            "supplier_reliability_floor": 0.60,
        },
    ),
    VariantSpec(
        id="LEAD_TIME_BUFFER_v2",
        family="lead_time_buffer",
        version=2,
        status="shadow",
        metadata={
            "name": "Lead time buffer conservative",
            "description": "Longer ordering buffer with higher supplier reliability floor.",
            "buffer_days": 3,
            "supplier_reliability_floor": 0.70,
        },
    ),
    VariantSpec(
        id="ORDER_QUANTITY_THRESHOLD_v1",
        family="order_quantity_threshold",
        version=1,
        status="active",
        metadata={
            "name": "Order quantity threshold baseline",
            "display_name": "How much to adjust before flagging",
            "description": "Current par adjustment before the kitchen gets a flag.",
            "par_adjustment_pct": 15,
            "candidate_par_adjustment_pct": [15, 20],
        },
    ),
    VariantSpec(
        id="ORDER_QUANTITY_THRESHOLD_v2",
        family="order_quantity_threshold",
        version=2,
        status="shadow",
        metadata={
            "name": "Order quantity threshold wider",
            "display_name": "How much to adjust before flagging",
            "description": "Larger par adjustment before the kitchen gets a flag.",
            "par_adjustment_pct": 20,
            "candidate_par_adjustment_pct": [15, 20],
        },
    ),
    VariantSpec(
        id="WEATHER_SENSITIVITY_v1",
        family="weather_sensitivity",
        version=1,
        status="active",
        metadata={
            "name": "Weather sensitivity baseline",
            "display_name": "Minimum forecast confidence to act on weather",
            "description": "Current confidence floor before weather changes the order.",
            "forecast_confidence_min": 0.70,
            "candidate_forecast_confidence_min": [0.70, 0.80],
        },
    ),
    VariantSpec(
        id="WEATHER_SENSITIVITY_v2",
        family="weather_sensitivity",
        version=2,
        status="shadow",
        metadata={
            "name": "Weather sensitivity stricter",
            "display_name": "Minimum forecast confidence to act on weather",
            "description": "Higher confidence floor before weather changes the order.",
            "forecast_confidence_min": 0.80,
            "candidate_forecast_confidence_min": [0.70, 0.80],
        },
    ),
    VariantSpec(
        id="EVENT_LEAD_TIME_v1",
        family="event_lead_time",
        version=1,
        status="active",
        metadata={
            "name": "Event lead time baseline",
            "display_name": "How far ahead to adjust for events",
            "description": "Current number of days ahead before event orders adjust.",
            "pre_event_days": 3,
            "candidate_pre_event_days": [3, 5],
        },
    ),
    VariantSpec(
        id="EVENT_LEAD_TIME_v2",
        family="event_lead_time",
        version=2,
        status="shadow",
        metadata={
            "name": "Event lead time earlier",
            "display_name": "How far ahead to adjust for events",
            "description": "Earlier event ordering window for busy kitchen weeks.",
            "pre_event_days": 5,
            "candidate_pre_event_days": [3, 5],
        },
    ),
    VariantSpec(
        id="PRICE_MEMORY_ALERT_v1",
        family="price_memory_alert",
        version=1,
        status="active",
        metadata={
            "name": "Price memory alert baseline",
            "display_name": "Price deviation before surfacing memory",
            "description": "Current price jump threshold before the kitchen sees a memory alert.",
            "deviation_pct": 8,
            "candidate_deviation_pct": [8, 12],
        },
    ),
    VariantSpec(
        id="PRICE_MEMORY_ALERT_v2",
        family="price_memory_alert",
        version=2,
        status="shadow",
        metadata={
            "name": "Price memory alert wider",
            "display_name": "Price deviation before surfacing memory",
            "description": "Larger price jump threshold before the kitchen sees a memory alert.",
            "deviation_pct": 12,
            "candidate_deviation_pct": [8, 12],
        },
    ),
)


PURCHASING_EVOLVER_CONFIG = PromptEvolverConfig(
    categories=list(_CATEGORIES),
    exploration_constant=1.414,
    promotion_improvement_threshold=0.05,
    promotion_min_samples=50,
)


def get_purchasing_variant_specs() -> list[VariantSpec]:
    """Return fresh Purchasing VariantSpec instances."""

    return [
        VariantSpec(
            id=variant.id,
            family=variant.family,
            version=variant.version,
            template=variant.template,
            status=variant.status,
            metadata=deepcopy(variant.metadata),
        )
        for variant in PURCHASING_VARIANTS
    ]


def variant_to_payload(variant: VariantSpec) -> dict[str, Any]:
    """Convert a VariantSpec to the existing Purchasing provider payload shape."""

    metadata = deepcopy(variant.metadata)
    return {
        "id": variant.id,
        "variant_id": variant.id,
        "family": variant.family,
        "version": variant.version,
        "name": str(metadata.get("name") or variant.id),
        "description": str(metadata.get("description") or variant.family),
        "dimensions": {
            "family": variant.family,
            "version": variant.version,
        },
        "status": variant.status,
        "metadata": metadata,
    }


def get_purchasing_variants() -> list[dict[str, Any]]:
    """Return current Purchasing configured evolution variants as route payloads."""

    return [variant_to_payload(variant) for variant in get_purchasing_variant_specs()]
