"""Event-driven subcategory helpers for Trading metadata analytics."""

from __future__ import annotations

import re
from typing import Any


DIRECTIONAL_TAGS = (
    "earnings_direction",
    "binary_event",
    "earnings_beat",
    "earnings_miss",
    "fda_approval",
    "fda_rejection",
    "guidance_up",
    "guidance_down",
    "merger",
    "acquisition",
    "buyout",
    "split",
    "dividend",
    "upgrade",
    "downgrade",
    "news_long",
    "news_short",
)

VOLATILITY_TAGS = (
    "straddle",
    "strangle",
    "iv_play",
    "iv_crush",
    "iv_expansion",
    "earnings_vol",
    "event_vol",
    "gamma_scalp",
    "calendar_spread",
    "butterfly",
    "iron_condor_earnings",
    "pre_earnings_iv",
)

_VOLATILITY_NOTE_TERMS = (
    "straddle",
    "strangle",
    "iv",
    "volatility",
    "vol play",
)


def classify_event_subcategory(
    strategy_tag: Any = None,
    direction: Any = None,
    notes: Any = None,
) -> str:
    text = _normalize(" ".join(str(value or "") for value in (strategy_tag, direction)))
    notes_text = _normalize(str(notes or ""))

    if any(tag in text for tag in VOLATILITY_TAGS):
        return "volatility"
    if any(term in notes_text for term in _NORMALIZED_VOLATILITY_NOTE_TERMS):
        return "volatility"
    if any(tag in text for tag in DIRECTIONAL_TAGS):
        return "directional"
    return "directional"


def get_subcategory(trade: dict[str, Any]) -> str | None:
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    category = trade.get("category") or metadata.get("category")
    if category != "event_driven":
        return None
    explicit = trade.get("subcategory") or trade.get("event_subcategory") or metadata.get("subcategory") or metadata.get("event_subcategory")
    if explicit in {"directional", "volatility"}:
        return str(explicit)
    return classify_event_subcategory(
        strategy_tag=trade.get("strategy_tag") or metadata.get("strategy_tag") or metadata.get("thesis_type"),
        direction=trade.get("direction") or metadata.get("direction"),
        notes=trade.get("notes") or metadata.get("notes"),
    )


def _normalize(value: str) -> str:
    text = value.strip().lower()
    return re.sub(r"[\s\-/:.]+", "_", text)


_NORMALIZED_VOLATILITY_NOTE_TERMS = tuple(_normalize(term) for term in _VOLATILITY_NOTE_TERMS)
