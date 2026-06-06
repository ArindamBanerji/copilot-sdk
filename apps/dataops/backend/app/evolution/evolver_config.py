"""DataOps AgentEvolver variant configuration."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from copilot_sdk.evolution import PromptEvolverConfig, VariantSpec

try:
    from copilot_sdk.scoring.presets.dataops import DataOpsPreset

    _CATEGORIES = list(DataOpsPreset().shape.category_names)
except Exception:
    _CATEGORIES = [
        "schema_change",
        "volume_anomaly",
        "quality_anomaly",
        "freshness_violation",
        "pipeline_failure",
        "transform_drift",
    ]


DATAOPS_VARIANTS: tuple[VariantSpec, ...] = (
    VariantSpec(
        id="AUTO_APPROVE_THRESHOLD_v1",
        family="auto_approve_threshold",
        version=1,
        status="active",
        metadata={
            "name": "Auto-approve threshold baseline",
            "description": "Current DataOps auto-approval confidence and impact-scope thresholds.",
            "confidence_threshold": 0.85,
            "scope_limit": 0.30,
        },
    ),
    VariantSpec(
        id="AUTO_APPROVE_THRESHOLD_v2",
        family="auto_approve_threshold",
        version=2,
        status="shadow",
        metadata={
            "name": "Auto-approve threshold selective",
            "description": "More selective auto-approval with a lower impact-scope limit.",
            "confidence_threshold": 0.90,
            "scope_limit": 0.25,
        },
    ),
    VariantSpec(
        id="SCHEDULING_CRITERIA_v1",
        family="scheduling_criteria",
        version=1,
        status="active",
        metadata={
            "name": "Scheduling criteria baseline",
            "description": "Current off-peak scheduling window and resource threshold.",
            "off_peak_hours": [2, 6],
            "resource_threshold": 0.70,
        },
    ),
    VariantSpec(
        id="SCHEDULING_CRITERIA_v2",
        family="scheduling_criteria",
        version=2,
        status="shadow",
        metadata={
            "name": "Scheduling criteria conservative",
            "description": "Earlier off-peak scheduling with a lower resource threshold.",
            "off_peak_hours": [1, 5],
            "resource_threshold": 0.65,
        },
    ),
)


DATAOPS_EVOLVER_CONFIG = PromptEvolverConfig(
    categories=list(_CATEGORIES),
    exploration_constant=1.414,
    promotion_improvement_threshold=0.05,
    promotion_min_samples=50,
)


def get_dataops_variant_specs() -> list[VariantSpec]:
    """Return fresh DataOps VariantSpec instances."""

    return [
        VariantSpec(
            id=variant.id,
            family=variant.family,
            version=variant.version,
            template=variant.template,
            status=variant.status,
            metadata=deepcopy(variant.metadata),
        )
        for variant in DATAOPS_VARIANTS
    ]


def variant_to_payload(variant: VariantSpec) -> dict[str, Any]:
    """Convert a VariantSpec to the existing DataOps provider payload shape."""

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


def get_dataops_variants() -> list[dict[str, Any]]:
    """Return current DataOps configured evolution variants as route payloads."""

    return [variant_to_payload(variant) for variant in get_dataops_variant_specs()]
