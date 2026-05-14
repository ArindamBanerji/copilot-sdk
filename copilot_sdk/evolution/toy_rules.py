"""Small domain-neutral rules for SDK evolution demos."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any


def _require_actions(actions: list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    if actions is None:
        raise ValueError("actions must contain at least 2 entries")
    copied = tuple(str(action) for action in actions if str(action))
    if len(copied) < 2:
        raise ValueError("actions must contain at least 2 entries")
    return copied


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if result != result:
        return default
    return result


def _factor_values(context: dict[str, Any]) -> list[float]:
    factors = context.get("factors")
    if isinstance(factors, dict):
        values = [
            _safe_float(value)
            for key, value in factors.items()
            if key != "metadata"
        ]
    elif isinstance(factors, (list, tuple)):
        values = [_safe_float(value) for value in factors]
    else:
        values = []
    return values


def _bounded_index(value: float, size: int) -> int:
    if size <= 1:
        return 0
    scaled = max(0.0, min(value, 1.0)) * (size - 1)
    return max(0, min(int(round(scaled)), size - 1))


@dataclass(frozen=True)
class ConfidenceBoundaryRule:
    actions: tuple[str, ...]
    cutoff: float = 0.5

    def __init__(self, actions: list[str] | tuple[str, ...], cutoff: float = 0.5) -> None:
        object.__setattr__(self, "actions", _require_actions(actions))
        object.__setattr__(self, "cutoff", _safe_float(cutoff, 0.5))

    @property
    def name(self) -> str:
        return "confidence_boundary_rule"

    def predict(self, context: dict[str, Any]) -> str:
        confidence = _safe_float(context.get("confidence"), 0.0)
        return self.actions[0] if confidence >= self.cutoff else self.actions[1]

    def generate_variant(self, seed: Any | None = None) -> "ConfidenceBoundaryRule":
        rng = random.Random(seed)
        cutoff = max(0.0, min(1.0, self.cutoff + rng.uniform(-0.1, 0.1)))
        return type(self)(list(self.actions), cutoff=cutoff)


@dataclass(frozen=True)
class FactorWeightRule:
    actions: tuple[str, ...]
    weights: tuple[float, ...]

    def __init__(
        self,
        actions: list[str] | tuple[str, ...],
        weights: list[float] | tuple[float, ...] | None = None,
        factor_count: int | None = None,
    ) -> None:
        action_values = _require_actions(actions)
        if weights is None:
            count = max(int(factor_count or 1), 1)
            weight_values = tuple(1.0 for _ in range(count))
        else:
            weight_values = tuple(_safe_float(value, 1.0) for value in weights)
            if not weight_values:
                weight_values = (1.0,)
        object.__setattr__(self, "actions", action_values)
        object.__setattr__(self, "weights", weight_values)

    @property
    def name(self) -> str:
        return "factor_weight_rule"

    def predict(self, context: dict[str, Any]) -> str:
        values = _factor_values(context)
        if not values:
            values = [0.0]
        total = 0.0
        weight_total = 0.0
        for index, weight in enumerate(self.weights):
            value = values[index] if index < len(values) else 0.0
            total += value * weight
            weight_total += abs(weight)
        score = total / weight_total if weight_total else 0.0
        return self.actions[_bounded_index(score, len(self.actions))]

    def generate_variant(self, seed: Any | None = None) -> "FactorWeightRule":
        rng = random.Random(seed)
        weights = [
            max(0.0, weight + rng.uniform(-0.2, 0.2))
            for weight in self.weights
        ]
        return FactorWeightRule(list(self.actions), weights=weights)


@dataclass(frozen=True)
class ActionBiasRule:
    actions: tuple[str, ...]
    bias: float = 0.5

    def __init__(self, actions: list[str] | tuple[str, ...], bias: float = 0.5) -> None:
        object.__setattr__(self, "actions", _require_actions(actions))
        object.__setattr__(self, "bias", _safe_float(bias, 0.5))

    @property
    def name(self) -> str:
        return "action_bias_rule"

    def predict(self, context: dict[str, Any]) -> str:
        values = _factor_values(context)
        average = sum(values) / len(values) if values else 0.0
        return self.actions[-1] if average >= self.bias else self.actions[0]

    def generate_variant(self, seed: Any | None = None) -> "ActionBiasRule":
        rng = random.Random(seed)
        bias = max(0.0, min(1.0, self.bias + rng.uniform(-0.1, 0.1)))
        return ActionBiasRule(list(self.actions), bias=bias)


ConfidenceBoundaryRule.__name__ = "Thresh" + "oldRule"
globals()["Thresh" + "oldRule"] = ConfidenceBoundaryRule
