"""Oracle protocols and shared measurement-pipeline helpers."""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from math import ceil
from statistics import NormalDist
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Oracle(Protocol):
    """T-O: parametric oracle for pipeline validation.

    Oracles validate that a measurement instrument detects a known injected
    effect. They never substantiate a customer-specific magnitude claim.
    """

    known_effect: float
    known_accuracy_effect: float

    def synthetic_outcome(self, *, shown: bool) -> dict:
        """Generate one synthetic outcome.

        Returns at least: {action, was_override, quality_signal, correct}.
        The `correct` field must be modeled, never hardcoded true.
        """
        ...


class BaseOracle:
    """Reusable base shared by domain-specific oracle implementations."""

    def __init__(
        self,
        *,
        actions: list[str],
        base_rate: float,
        treatment_lift: float,
        base_accuracy: float,
        accuracy_lift: float,
        override_rate: float = 0.15,
        seed: int = 42,
    ) -> None:
        if not actions:
            raise ValueError("actions must be non-empty")
        self.known_effect = treatment_lift
        self.known_accuracy_effect = accuracy_lift
        self._actions = actions
        self._base_rate = base_rate
        self._lift = treatment_lift
        self._base_accuracy = base_accuracy
        self._accuracy_lift = accuracy_lift
        self._override_rate = override_rate
        self._rng = random.Random(seed)

    def synthetic_outcome(self, *, shown: bool) -> dict:
        p_action = self._base_rate + (self._lift if shown else 0.0)
        took_action = self._rng.random() < _clamp_probability(p_action)

        p_correct = self._base_accuracy + (self._accuracy_lift if shown else 0.0)
        correct = self._rng.random() < _clamp_probability(p_correct)

        return {
            "action": self._primary_action(took_action),
            "was_override": self._rng.random() < _clamp_probability(self._override_rate),
            "quality_signal": 1.0 if correct else 0.0,
            "correct": correct,
        }

    def _primary_action(self, took_action: bool) -> str:
        """Override in domain code for custom action selection."""
        return self._actions[0] if took_action else self._actions[-1]


@dataclass(frozen=True)
class LiftResult:
    treatment_rate: float
    control_rate: float
    escalation_lift: float


@dataclass(frozen=True)
class AccuracyResult:
    treatment: float
    control: float


@dataclass(frozen=True)
class ExperimentResult:
    name: str
    expected_lift: float
    measured_lift: float
    passed: bool
    detail: Any


def compute_lift(
    treatment: Sequence[dict],
    control: Sequence[dict],
    action_key: str = "action",
    positive_action: str | None = None,
) -> LiftResult:
    """Treatment action-rate minus control action-rate."""
    _validate_nonempty_arms(treatment, control)
    if positive_action is not None:
        treatment_rate = _action_rate(treatment, action_key, positive_action)
        control_rate = _action_rate(control, action_key, positive_action)
    else:
        treatment_rate = sum(1 for row in treatment if row[action_key] != "dismiss") / len(
            treatment
        )
        control_rate = sum(1 for row in control if row[action_key] != "dismiss") / len(
            control
        )

    return LiftResult(
        treatment_rate=treatment_rate,
        control_rate=control_rate,
        escalation_lift=treatment_rate - control_rate,
    )


def compute_accuracy(
    treatment: Sequence[dict],
    control: Sequence[dict],
) -> AccuracyResult:
    """Treatment accuracy vs control accuracy."""
    _validate_nonempty_arms(treatment, control)
    treatment_accuracy = sum(1 for row in treatment if row.get("correct")) / len(
        treatment
    )
    control_accuracy = sum(1 for row in control if row.get("correct")) / len(control)
    return AccuracyResult(treatment=treatment_accuracy, control=control_accuracy)


def floor_power(
    base_rate: float,
    delta: float,
    alpha: float = 0.05,
    power: float = 0.80,
) -> int:
    """Gaussian lower-bound sample size per arm.

    This is a floor; real sample sizes are usually higher because operational
    outcomes are overdispersed.
    """
    if delta <= 0:
        raise ValueError("delta must be positive")
    base_rate = _clamp_probability(base_rate)
    z_alpha = NormalDist().inv_cdf(1 - alpha / 2)
    z_beta = NormalDist().inv_cdf(power)
    return ceil(((z_alpha + z_beta) ** 2 * 2 * base_rate * (1 - base_rate)) / (delta**2))


def _action_rate(rows: Sequence[dict], action_key: str, positive_action: str) -> float:
    return sum(1 for row in rows if row[action_key] == positive_action) / len(rows)


def _validate_nonempty_arms(treatment: Sequence[dict], control: Sequence[dict]) -> None:
    if not treatment or not control:
        raise ValueError("treatment and control arms must be non-empty")


def _clamp_probability(value: float) -> float:
    return max(0.0, min(float(value), 1.0))
