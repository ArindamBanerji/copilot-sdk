"""Trading-specific evolution dimensions for presentation variants."""

from __future__ import annotations

from typing import Any

from .evolver_config import get_trading_variants


TRADING_VARIANT_DIMENSIONS: list[dict[str, Any]] = [
    {
        "name": "execution_threshold",
        "description": "Controls Trading execution confidence thresholds.",
        "values": ["baseline", "selective"],
        "default": "baseline",
    },
    {
        "name": "revenge_cooldown",
        "description": "Controls post-loss cooldown and post-loss size limits.",
        "values": ["baseline", "conservative"],
        "default": "baseline",
    },
]


DEFAULT_VARIANTS: list[dict[str, Any]] = get_trading_variants()


def get_default_variants_copy() -> list[dict[str, Any]]:
    return get_trading_variants()
