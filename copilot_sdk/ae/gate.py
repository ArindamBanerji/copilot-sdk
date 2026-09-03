"""Conservative paired-bootstrap promotion gate (E22)."""

from __future__ import annotations

import math
import random
from typing import Sequence

from copilot_sdk.ae.types import PromotionDecision


class PromotionGate:
    """Promote only with at least 30 paired observations and FPR below 5%."""

    def __init__(self, min_n: int = 30, fpr_threshold: float = 0.05, bootstrap_samples: int = 1000, random_seed: int | None = 0) -> None:
        if min_n < 1 or bootstrap_samples < 1:
            raise ValueError("min_n and bootstrap_samples must be positive")
        if not 0.0 < fpr_threshold < 1.0:
            raise ValueError("fpr_threshold must be between 0 and 1")
        self.min_n = min_n
        self.fpr_threshold = fpr_threshold
        self.bootstrap_samples = bootstrap_samples
        self.random_seed = random_seed

    def evaluate(self, candidate: Sequence[float], baseline: Sequence[float], conservation_state: str = "GREEN") -> PromotionDecision:
        if len(candidate) != len(baseline):
            raise ValueError("candidate and baseline samples must be paired")
        n = len(candidate)
        if n < self.min_n:
            return self._reject("insufficient_sample_size", n, 0.0, 1.0)
        if conservation_state.strip().upper() != "GREEN":
            return self._reject("conservation_not_green", n, 0.0, 1.0)
        differences = [float(c) - float(b) for c, b in zip(candidate, baseline)]
        if not all(math.isfinite(value) for value in differences):
            raise ValueError("samples must contain only finite values")
        effect = sum(differences) / n
        rng = random.Random(self.random_seed)
        at_or_below_zero = 0
        for _ in range(self.bootstrap_samples):
            sample_mean = sum(rng.choice(differences) for _ in range(n)) / n
            if sample_mean <= 0.0:
                at_or_below_zero += 1
        p_value = (at_or_below_zero + 1) / (self.bootstrap_samples + 1)
        checks = {"minimum_sample": True, "conservation": True, "superiority": effect > 0.0, "fpr": p_value < self.fpr_threshold}
        promoted = effect > 0.0 and p_value < self.fpr_threshold
        return PromotionDecision(promoted, "promoted" if promoted else "bootstrap_not_significant", p_value, n, effect, self.fpr_threshold, checks)

    def check(self, candidate: Sequence[float], baseline: Sequence[float], conservation_state: str = "GREEN") -> PromotionDecision:
        return self.evaluate(candidate, baseline, conservation_state)

    def should_promote(self, candidate: Sequence[float], baseline: Sequence[float], conservation_state: str = "GREEN") -> bool:
        return self.evaluate(candidate, baseline, conservation_state).promoted

    def _reject(self, reason: str, n: int, effect: float, p_value: float) -> PromotionDecision:
        return PromotionDecision(False, reason, p_value, n, effect, self.fpr_threshold, {"minimum_sample": n >= self.min_n, "conservation": reason != "conservation_not_green", "superiority": False, "fpr": False})
