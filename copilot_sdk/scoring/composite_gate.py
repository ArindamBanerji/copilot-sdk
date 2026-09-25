"""Three-layer conservation gate adapter.

The production scorer remains responsible for its existing conservation
calculation.  This adapter composes that absolute-floor result with the
relative and short-window rate checks for status reporting and pause policy.
It consumes verified outcomes supplied by the caller; it does not maintain a
second independent decision store.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any


class CompositeGate:
    """Evaluate G-ABS, G-REL, and G-RATE over one verified stream."""

    def __init__(self, *, w_short: int = 20, m_rate: float = 0.85, m_rel: float = 0.70, w_long: int = 400) -> None:
        if w_short <= 0 or w_long <= 0:
            raise ValueError("window sizes must be positive")
        if not 0.0 < m_rate <= 1.0 or not 0.0 < m_rel <= 1.0:
            raise ValueError("gate multipliers must be in (0, 1]")
        self.w_short = int(w_short)
        self.m_rate = float(m_rate)
        self.m_rel = float(m_rel)
        self.w_long = int(w_long)

    def evaluate(
        self,
        *,
        alpha_q_v: float,
        theta_min: float | None,
        rolling_accuracy: float,
        baseline: float,
        verified_outcomes: Iterable[bool | int | float] = (),
        base_status: str = "GREEN",
    ) -> dict[str, Any]:
        outcomes = [bool(value) for value in verified_outcomes]
        long_values = outcomes[-self.w_long:]
        short_values = outcomes[-self.w_short:]
        long_baseline = _mean(long_values) if long_values else _clamp(baseline)
        short_accuracy = _mean(short_values) if short_values else None
        abs_active = theta_min is not None and alpha_q_v < theta_min and bool(outcomes)
        rel_threshold = self.m_rel * _clamp(baseline)
        rel_active = bool(outcomes) and _clamp(rolling_accuracy) < rel_threshold
        rate_threshold = self.m_rate * long_baseline
        rate_active = len(short_values) >= self.w_short and short_accuracy is not None and short_accuracy < rate_threshold
        active = abs_active or rel_active or rate_active
        status = "AMBER" if active else base_status
        return {
            "status": status,
            "g_abs": {
                "active": abs_active,
                "alpha_q_v": float(alpha_q_v),
                "theta_min": theta_min,
            },
            "g_rel": {
                "active": rel_active,
                "rolling_accuracy": float(_clamp(rolling_accuracy)),
                "baseline": float(_clamp(baseline)),
                "threshold": float(rel_threshold),
            },
            "g_rate": {
                "active": bool(rate_active),
                "short_accuracy": short_accuracy,
                "long_baseline": float(long_baseline),
                "threshold": float(rate_threshold),
                "w_short": self.w_short,
                "m_rate": self.m_rate,
                "short_window_count": len(short_values),
            },
        }


def outcomes_from_state(state: Any) -> list[bool]:
    """Extract verified correctness values from common state/store adapters."""

    if isinstance(state, dict):
        for key in ("verified_outcomes", "recent_outcomes", "outcomes"):
            values = state.get(key)
            if isinstance(values, (list, tuple)):
                return [bool(value) for value in values]
        return []
    store = getattr(state, "graph_store", None) or getattr(state, "_graph_store", None)
    getter = getattr(store, "get_verified_decisions", None)
    if not callable(getter):
        return []
    domain = str(getattr(state, "domain", "") or getattr(store, "domain", ""))
    try:
        rows = getter(domain)
    except TypeError:
        rows = getter()
    result: list[bool] = []
    for row in rows or []:
        if isinstance(row, dict):
            value = row.get("is_correct")
            if value is not None:
                result.append(bool(value))
    return result


def _mean(values: Sequence[bool]) -> float:
    return sum(1.0 for value in values if value) / len(values)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
