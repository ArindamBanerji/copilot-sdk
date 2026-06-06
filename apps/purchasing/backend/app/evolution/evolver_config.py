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
