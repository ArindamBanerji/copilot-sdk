"""Variant provider for Trading Level 2 evolution."""

from __future__ import annotations

from .dimensions import DEFAULT_VARIANTS, get_default_variants_copy


def get_trading_variants() -> list[dict]:
    """Return current Trading evolution variants."""

    return get_default_variants_copy()


def get_trading_variant(variant_id: str) -> dict | None:
    for variant in DEFAULT_VARIANTS:
        if str(variant.get("variant_id")) == str(variant_id):
            return dict(variant)
    return None
