"""Trading AgentEvolver variant configuration."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from copilot_sdk.evolution import PromptEvolverConfig, VariantSpec

try:
    from copilot_sdk.scoring.presets.trading import TradingPreset

    _CATEGORIES = list(TradingPreset().shape.category_names)
except Exception:
    _CATEGORIES = [
        "trend_following",
        "mean_reversion",
        "event_driven",
        "income_strategy",
        "scalp_intraday",
    ]


TRADING_VARIANTS: tuple[VariantSpec, ...] = (
    VariantSpec(
        id="EXECUTION_THRESHOLD_v1",
        family="execution_threshold",
        version=1,
        status="active",
        metadata={
            "name": "Execution threshold baseline",
            "description": "Current Trading execution confidence thresholds.",
            "strong_execution_confidence": 0.75,
            "skip_threshold": 0.40,
        },
    ),
    VariantSpec(
        id="EXECUTION_THRESHOLD_v2",
        family="execution_threshold",
        version=2,
        status="shadow",
        metadata={
            "name": "Execution threshold selective",
            "description": "More selective strong execution with a lower skip threshold.",
            "strong_execution_confidence": 0.82,
            "skip_threshold": 0.35,
        },
    ),
    VariantSpec(
        id="REVENGE_COOLDOWN_v1",
        family="revenge_cooldown",
        version=1,
        status="active",
        metadata={
            "name": "Revenge cooldown baseline",
            "description": "Current loss cooldown and size-ratio thresholds.",
            "cooldown_minutes": 30,
            "max_size_ratio": 1.3,
        },
    ),
    VariantSpec(
        id="REVENGE_COOLDOWN_v2",
        family="revenge_cooldown",
        version=2,
        status="shadow",
        metadata={
            "name": "Revenge cooldown conservative",
            "description": "Longer cooldown with a stricter post-loss size limit.",
            "cooldown_minutes": 45,
            "max_size_ratio": 1.2,
        },
    ),
)


TRADING_EVOLVER_CONFIG = PromptEvolverConfig(
    categories=list(_CATEGORIES),
    exploration_constant=1.414,
    promotion_improvement_threshold=0.05,
    promotion_min_samples=50,
)


def get_trading_variant_specs() -> list[VariantSpec]:
    """Return fresh Trading VariantSpec instances."""

    return [
        VariantSpec(
            id=variant.id,
            family=variant.family,
            version=variant.version,
            template=variant.template,
            status=variant.status,
            metadata=deepcopy(variant.metadata),
        )
        for variant in TRADING_VARIANTS
    ]


def variant_to_payload(variant: VariantSpec) -> dict[str, Any]:
    """Convert a VariantSpec to the existing Trading provider payload shape."""

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


def get_trading_variants() -> list[dict[str, Any]]:
    """Return current Trading evolution variants as route/CLI payloads."""

    return [variant_to_payload(variant) for variant in get_trading_variant_specs()]
