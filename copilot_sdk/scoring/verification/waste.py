"""Waste and stockout verification for purchasing decisions."""

from __future__ import annotations

from dataclasses import dataclass


WASTE_THRESHOLD = 0.15


@dataclass(frozen=True)
class WasteResult:
    item: str
    quantity_ordered: float
    quantity_remaining: float
    waste_pct: float
    stockout: bool
    is_correct: bool
    explanation: str


def verify_order(
    item: str,
    quantity_ordered: float,
    quantity_remaining: float,
    stockout: bool,
    action_taken: str,
) -> WasteResult:
    ordered = float(quantity_ordered)
    remaining = float(quantity_remaining)
    waste_pct = remaining / ordered if ordered > 0 else 0.0

    if stockout and action_taken in ("order_less", "order_as_planned", "skip"):
        return WasteResult(
            item=item,
            quantity_ordered=ordered,
            quantity_remaining=remaining,
            waste_pct=round(waste_pct, 3),
            stockout=bool(stockout),
            is_correct=False,
            explanation="Stockout occurred; should have ordered more.",
        )

    if waste_pct > WASTE_THRESHOLD and action_taken in (
        "order_as_planned",
        "order_more",
    ):
        return WasteResult(
            item=item,
            quantity_ordered=ordered,
            quantity_remaining=remaining,
            waste_pct=round(waste_pct, 3),
            stockout=bool(stockout),
            is_correct=False,
            explanation="Waste exceeded threshold; over-ordered.",
        )

    return WasteResult(
        item=item,
        quantity_ordered=ordered,
        quantity_remaining=remaining,
        waste_pct=round(waste_pct, 3),
        stockout=bool(stockout),
        is_correct=True,
        explanation="Order outcome within waste and stockout tolerance.",
    )
