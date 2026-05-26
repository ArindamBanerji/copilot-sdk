"""Trading-specific evolution dimensions for presentation variants."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


TRADING_VARIANT_DIMENSIONS: list[dict[str, Any]] = [
    {
        "name": "evidence_ordering",
        "description": "Controls which evidence block appears first in trade analysis.",
        "values": ["factor_first", "regime_first", "pattern_first"],
        "default": "factor_first",
    },
    {
        "name": "risk_framing",
        "description": "Controls whether risk is presented numerically, categorically, or comparatively.",
        "values": ["numerical", "categorical", "comparative"],
        "default": "numerical",
    },
    {
        "name": "strategy_weight",
        "description": "Controls how much emphasis is placed on strategy-specific versus general execution context.",
        "values": ["balanced", "strategy_heavy", "general_heavy"],
        "default": "balanced",
    },
]


DEFAULT_VARIANTS: list[dict[str, Any]] = [
    {
        "variant_id": "trd-ev-001",
        "name": "Regime-first evidence",
        "dimensions": {
            "evidence_ordering": "regime_first",
            "risk_framing": "numerical",
            "strategy_weight": "balanced",
        },
        "status": "active",
    },
    {
        "variant_id": "trd-ev-002",
        "name": "Comparative risk framing",
        "dimensions": {
            "evidence_ordering": "factor_first",
            "risk_framing": "comparative",
            "strategy_weight": "balanced",
        },
        "status": "shadow",
    },
    {
        "variant_id": "trd-ev-003",
        "name": "Strategy-heavy weighting",
        "dimensions": {
            "evidence_ordering": "factor_first",
            "risk_framing": "numerical",
            "strategy_weight": "strategy_heavy",
        },
        "status": "shadow",
    },
]


def get_default_variants_copy() -> list[dict[str, Any]]:
    return deepcopy(DEFAULT_VARIANTS)
