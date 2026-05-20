"""Diagnostic judgment conflict detection."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

CONFLICT_LOW_THRESHOLD = 0.30
CONFLICT_HIGH_THRESHOLD = 0.70


@dataclass(frozen=True)
class JudgmentConflict:
    decision_id: str
    conflict_type: str
    predicted_success: float
    actual_correct: bool
    factors: dict[str, float]
    contradicting_factors: list[tuple[str, float, float]]
    message: str


def detect_conflict(
    *,
    decision_id: str,
    predicted_success: float,
    actual_correct: bool,
    factors: Mapping[str, Any] | Sequence[Any],
    fingerprint_weights: Mapping[str, float],
    factor_names: Sequence[str],
    low_threshold: float = CONFLICT_LOW_THRESHOLD,
    high_threshold: float = CONFLICT_HIGH_THRESHOLD,
) -> JudgmentConflict | None:
    """Return a diagnostic conflict when prediction and outcome diverge."""

    predicted = _clamp_probability(predicted_success)
    if predicted >= float(high_threshold) and not bool(actual_correct):
        conflict_type = "surprising_failure"
    elif predicted <= float(low_threshold) and bool(actual_correct):
        conflict_type = "surprising_success"
    else:
        return None

    factor_values = _coerce_factors(factors, factor_names)
    weights = _coerce_weights(fingerprint_weights)
    contradicting = sorted(
        (
            (name, value, weights.get(name, 0.0))
            for name, value in factor_values.items()
            if weights.get(name, 0.0) > 0.0
        ),
        key=lambda item: abs(item[1] - 0.5) * item[2],
        reverse=True,
    )
    percent = round(predicted * 100)
    label = "correct" if actual_correct else "incorrect"
    message = (
        f"{conflict_type}: predicted {percent}% success but outcome was {label}"
    )
    return JudgmentConflict(
        decision_id=str(decision_id),
        conflict_type=conflict_type,
        predicted_success=predicted,
        actual_correct=bool(actual_correct),
        factors=factor_values,
        contradicting_factors=contradicting,
        message=message,
    )


def _coerce_factors(
    factors: Mapping[str, Any] | Sequence[Any],
    factor_names: Sequence[str],
) -> dict[str, float]:
    names = [str(name) for name in factor_names]
    if isinstance(factors, Mapping):
        return {
            name: _finite_float(factors.get(name, 0.0), default=0.0)
            for name in names
        }

    values = list(factors)
    if len(values) != len(names):
        raise ValueError("factor values length must match factor_names length")
    return {
        name: _finite_float(value, default=0.0)
        for name, value in zip(names, values)
    }


def _coerce_weights(fingerprint_weights: Mapping[str, float]) -> dict[str, float]:
    return {
        str(name): max(0.0, min(_finite_float(weight, default=0.0), 1.0))
        for name, weight in fingerprint_weights.items()
    }


def _clamp_probability(value: Any) -> float:
    return max(0.0, min(_finite_float(value, default=0.0), 1.0))


def _finite_float(value: Any, *, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default
