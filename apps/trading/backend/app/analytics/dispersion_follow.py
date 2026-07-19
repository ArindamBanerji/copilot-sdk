"""Dispersion signal follow-rate analytics."""

from __future__ import annotations

import math
from typing import Any

from ci_trading.quant import dispersion_signal


MIN_DECISIONS = 30
SIGNAL_GAP = 0.05


def compute_dispersion_follow_rate(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [_dispersion_row(decision) for decision in decisions]
    rows = [row for row in rows if row is not None and row["signal_fired"]]
    followed = [row for row in rows if row["followed"]]
    skipped = [row for row in rows if not row["followed"]]
    skipped_value = sum(row["outcome"] for row in skipped)
    n = len(rows)
    day_zero = n < MIN_DECISIONS
    return {
        "signals_fired": n,
        "followed": len(followed),
        "skipped": len(skipped),
        "follow_rate": round(len(followed) / n, 3) if n else 0.0,
        "skipped_value": round(float(skipped_value), 2),
        "provenance": "real_measured" if not day_zero else "accumulating",
        "substantiation": "T-R" if not day_zero else "T-O",
        "day_zero": day_zero,
        "decisions_until_measured": max(0, MIN_DECISIONS - n),
    }


def _dispersion_row(decision: dict[str, Any]) -> dict[str, Any] | None:
    gap = _finite(decision.get("dispersion_gap"))
    if gap is None:
        index_iv = _finite(decision.get("index_iv"))
        realized = _finite(decision.get("realized_correlation"))
        constituent_ivs = decision.get("constituent_ivs")
        weights = decision.get("weights")
        if index_iv is not None and realized is not None and constituent_ivs is not None and weights is not None:
            diagnostic = dispersion_signal(index_iv, constituent_ivs, weights, realized)
            gap = diagnostic.dispersion_gap if math.isfinite(diagnostic.dispersion_gap) else None
    if gap is None:
        return None
    return {
        "signal_fired": bool(decision.get("dispersion_signal_fired", gap >= SIGNAL_GAP)),
        "followed": bool(decision.get("dispersion_followed") or decision.get("followed")),
        "outcome": _finite(decision.get("skipped_value") or decision.get("outcome_value") or decision.get("pnl")) or 0.0,
    }


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None

