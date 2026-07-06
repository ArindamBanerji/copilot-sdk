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
    VariantSpec(
        id="ALERT_THRESHOLD_v1",
        family="alert_threshold",
        version=1,
        status="active",
        metadata={
            "name": "Alert threshold baseline",
            "description": "Current revenge pattern alert timing.",
            "revenge_window_minutes": 30,
            "candidate_revenge_window_minutes": [30, 45, 60],
        },
    ),
    VariantSpec(
        id="ALERT_THRESHOLD_v2",
        family="alert_threshold",
        version=2,
        status="shadow",
        metadata={
            "name": "Alert threshold extended",
            "description": "Longer post-loss window before revenge patterns flag.",
            "revenge_window_minutes": 45,
            "candidate_revenge_window_minutes": [30, 45, 60],
        },
    ),
    VariantSpec(
        id="PATTERN_SENSITIVITY_v1",
        family="pattern_sensitivity",
        version=1,
        status="active",
        metadata={
            "name": "Pattern sensitivity baseline",
            "description": "Current behavioral pattern detector sensitivity.",
            "overconfidence_win_streak": 3,
            "drawdown_size_increase_pct": 30,
            "candidate_overconfidence_win_streak": [3, 4, 5],
            "candidate_drawdown_size_increase_pct": [30, 40, 50],
        },
    ),
    VariantSpec(
        id="PATTERN_SENSITIVITY_v2",
        family="pattern_sensitivity",
        version=2,
        status="shadow",
        metadata={
            "name": "Pattern sensitivity conservative",
            "description": "Less sensitive behavioral pattern thresholds.",
            "overconfidence_win_streak": 4,
            "drawdown_size_increase_pct": 40,
            "candidate_overconfidence_win_streak": [3, 4, 5],
            "candidate_drawdown_size_increase_pct": [30, 40, 50],
        },
    ),
    VariantSpec(
        id="REGIME_BOUNDARY_v1",
        family="regime_boundary",
        version=1,
        status="active",
        metadata={
            "name": "Regime boundary baseline",
            "description": "Current VIX regime classification thresholds.",
            "vix_low_threshold": 20,
            "vix_high_threshold": 30,
            "candidate_vix_low_threshold": [18, 20, 22],
            "candidate_vix_high_threshold": [28, 30, 32],
        },
    ),
    VariantSpec(
        id="REGIME_BOUNDARY_v2",
        family="regime_boundary",
        version=2,
        status="shadow",
        metadata={
            "name": "Regime boundary wider",
            "description": "Wider VIX regime classification thresholds.",
            "vix_low_threshold": 22,
            "vix_high_threshold": 32,
            "candidate_vix_low_threshold": [18, 20, 22],
            "candidate_vix_high_threshold": [28, 30, 32],
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
