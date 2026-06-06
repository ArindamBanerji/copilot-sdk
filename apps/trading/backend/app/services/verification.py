"""Verification metrics for completed Trading executions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VerificationResult:
    r_multiple: float
    execution_quality: float
    outcome_correct: bool
    verification_score: float
    components: dict[str, float]


def compute_r_multiple(
    entry_price: float,
    exit_price: float,
    stop_loss: float | None = None,
    side: str = "long",
) -> float:
    entry = _float_or_zero(entry_price)
    exit_value = _float_or_zero(exit_price)
    if entry <= 0.0:
        return 0.0

    normalized_side = str(side or "long").lower()
    if stop_loss is None:
        if normalized_side == "short":
            value = (entry - exit_value) / entry
        else:
            value = (exit_value - entry) / entry
        return round(value, 4)

    stop = _float_or_zero(stop_loss)
    if normalized_side == "short":
        risk = stop - entry
        if risk <= 0.0:
            return 0.0
        value = (entry - exit_value) / risk
    else:
        risk = entry - stop
        if risk <= 0.0:
            return 0.0
        value = (exit_value - entry) / risk
    return round(value, 4)


def compute_execution_quality(
    expected_entry: float,
    actual_entry: float,
    expected_exit: float,
    actual_exit: float,
    fill_rate: float = 1.0,
) -> float:
    entry_slippage = _clamped_slippage(expected_entry, actual_entry)
    exit_slippage = _clamped_slippage(expected_exit, actual_exit)
    fill = _clamp(_float_or_zero(fill_rate), 0.0, 1.0)

    slippage_score = 1.0 - ((entry_slippage + exit_slippage) / 0.10)
    score = 0.7 * _clamp(slippage_score, 0.0, 1.0) + 0.3 * fill
    return round(_clamp(score, 0.0, 1.0), 4)


def compute_verification_score(
    r_multiple: float,
    execution_quality: float,
    outcome_correct: bool,
) -> VerificationResult:
    normalized_r = _clamp((_float_or_zero(r_multiple) + 2.0) / 5.0, 0.0, 1.0)
    execution = _clamp(_float_or_zero(execution_quality), 0.0, 1.0)
    outcome = 1.0 if bool(outcome_correct) else 0.0
    components = {
        "r_multiple": round(0.4 * normalized_r, 4),
        "execution_quality": round(0.3 * execution, 4),
        "outcome": round(0.3 * outcome, 4),
    }
    score = round(sum(components.values()), 4)
    return VerificationResult(
        r_multiple=round(_float_or_zero(r_multiple), 4),
        execution_quality=round(execution, 4),
        outcome_correct=bool(outcome_correct),
        verification_score=score,
        components=components,
    )


def _clamped_slippage(expected: float, actual: float) -> float:
    expected_value = _float_or_zero(expected)
    actual_value = _float_or_zero(actual)
    if expected_value <= 0.0:
        return 0.05
    return _clamp(abs(actual_value - expected_value) / expected_value, 0.0, 0.05)


def _float_or_zero(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))
