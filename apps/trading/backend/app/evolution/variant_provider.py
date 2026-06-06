"""Variant provider for Trading Level 2 evolution."""

from __future__ import annotations

from .evolver_config import get_trading_variants


def get_trading_variant(variant_id: str) -> dict | None:
    for variant in get_trading_variants():
        if str(variant.get("variant_id")) == str(variant_id):
            return dict(variant)
    return None
