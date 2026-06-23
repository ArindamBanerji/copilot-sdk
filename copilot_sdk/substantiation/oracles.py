"""Parametric oracles for measurement-pipeline validation."""

from __future__ import annotations

import random
from typing import Any


class TraderOracle:
    """Parametric oracle for Trading copilot.

    Treatment = trust-radar shown to trader.
    Effect = shown traders execute more strongly.
    """

    known_effect: float = 0.08
    known_accuracy_effect: float = 0.04

    def __init__(
        self,
        *,
        base_rate: float = 0.35,
        treatment_lift: float = 0.08,
        base_accuracy: float = 0.72,
        accuracy_lift: float = 0.04,
        seed: int = 42,
    ) -> None:
        self._base_rate = base_rate
        self._lift = treatment_lift
        self._base_accuracy = base_accuracy
        self._accuracy_lift = accuracy_lift
        self._rng = random.Random(seed)
        self.known_effect = treatment_lift
        self.known_accuracy_effect = accuracy_lift

    def synthetic_outcome(self, *, shown: bool) -> dict[str, Any]:
        p_strong = _clamp_probability(self._base_rate + (self._lift if shown else 0.0))
        p_correct = _clamp_probability(
            self._base_accuracy + (self._accuracy_lift if shown else 0.0)
        )

        draw = self._rng.random()
        if draw < p_strong:
            action = "strong_execution"
        elif draw < p_strong + 0.35:
            action = "partial_execution"
        else:
            action = "skip"
        correct = self._rng.random() < p_correct

        return {
            "action": action,
            "trader_action": action,
            "was_override": self._rng.random() < 0.15,
            "quality_signal": 1.0 if correct else 0.0,
            "correct": correct,
        }


class ChefOracle:
    """Parametric oracle for Purchasing copilot.

    Treatment = par-intelligence / trust shown to chef.
    Effect = shown chefs follow par recommendations more often.
    """

    known_effect: float = 0.07
    known_accuracy_effect: float = 0.03

    def __init__(
        self,
        *,
        base_rate: float = 0.30,
        treatment_lift: float = 0.07,
        base_accuracy: float = 0.68,
        accuracy_lift: float = 0.03,
        seed: int = 42,
    ) -> None:
        self._base_rate = base_rate
        self._lift = treatment_lift
        self._base_accuracy = base_accuracy
        self._accuracy_lift = accuracy_lift
        self._rng = random.Random(seed)
        self.known_effect = treatment_lift
        self.known_accuracy_effect = accuracy_lift

    def synthetic_outcome(self, *, shown: bool) -> dict[str, Any]:
        p_planned = _clamp_probability(self._base_rate + (self._lift if shown else 0.0))
        p_correct = _clamp_probability(
            self._base_accuracy + (self._accuracy_lift if shown else 0.0)
        )

        draw = self._rng.random()
        if draw < p_planned:
            action = "order_as_planned"
        elif draw < p_planned + 0.20:
            action = "order_more"
        elif draw < p_planned + 0.40:
            action = "order_less"
        else:
            action = "skip"
        correct = self._rng.random() < p_correct

        return {
            "action": action,
            "chef_action": action,
            "was_override": self._rng.random() < 0.15,
            "quality_signal": 1.0 if correct else 0.0,
            "correct": correct,
        }


class DataOpsOracle:
    """Parametric oracle for DataOps copilot.

    Treatment = intelligence-map / recommendation shown.
    Effect = shown operators accept valid recommendations more often.
    """

    known_effect: float = 0.10
    known_accuracy_effect: float = 0.05

    def __init__(
        self,
        *,
        base_rate: float = 0.40,
        treatment_lift: float = 0.10,
        base_accuracy: float = 0.75,
        accuracy_lift: float = 0.05,
        seed: int = 42,
    ) -> None:
        self._base_rate = base_rate
        self._lift = treatment_lift
        self._base_accuracy = base_accuracy
        self._accuracy_lift = accuracy_lift
        self._rng = random.Random(seed)
        self.known_effect = treatment_lift
        self.known_accuracy_effect = accuracy_lift

    def synthetic_outcome(self, *, shown: bool) -> dict[str, Any]:
        p_accept = _clamp_probability(self._base_rate + (self._lift if shown else 0.0))
        p_correct = _clamp_probability(
            self._base_accuracy + (self._accuracy_lift if shown else 0.0)
        )

        draw = self._rng.random()
        if draw < p_accept:
            action = "accept"
        elif draw < p_accept + 0.25:
            action = "modify"
        else:
            action = "reject"
        correct = self._rng.random() < p_correct

        return {
            "action": action,
            "dataops_action": action,
            "was_override": self._rng.random() < 0.12,
            "quality_signal": 1.0 if correct else 0.0,
            "correct": correct,
        }


def _clamp_probability(value: float) -> float:
    return max(0.0, min(float(value), 1.0))
