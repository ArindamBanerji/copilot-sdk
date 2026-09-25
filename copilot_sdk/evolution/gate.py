"""Default promotion gate for shadow results."""

from __future__ import annotations

from math import erfc, sqrt
from statistics import pstdev
from typing import Any

MIN_BATCHES = 3


class DefaultPromotionGate:
    _SAFE_PHASES = {"GREEN", "VERIFIED", "ACTIVE"}

    def __init__(
        self,
        superiority_threshold_pp: float = 3.0,
        accuracy_floor: float = 0.70,
        min_shadow_decisions: int = 1_000,
        alpha: float = 0.05,
    ) -> None:
        self.superiority_threshold_pp = float(superiority_threshold_pp)
        self.accuracy_floor = float(accuracy_floor)
        self.min_shadow_decisions = int(min_shadow_decisions)
        self.alpha = float(alpha)

    def evaluate(
        self,
        shadow_results: dict[str, Any],
        conservation_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        total = int(shadow_results.get("total") or 0)
        accuracy = float(shadow_results.get("accuracy") or 0.0)
        baseline_accuracy = float(shadow_results.get("baseline_accuracy") or 0.0)
        baseline_total = int(shadow_results.get("baseline_total") or total)
        correct = self._outcome_count(shadow_results, "correct", accuracy, total)
        baseline_correct = self._outcome_count(
            shadow_results,
            "baseline_correct",
            baseline_accuracy,
            baseline_total,
        )
        superiority = accuracy - baseline_accuracy
        superiority_pp = round(superiority * 100.0, 4)
        z_statistic, p_value = self._one_sided_two_proportion_test(
            correct,
            total,
            baseline_correct,
            baseline_total,
        )
        batches = [float(value) for value in shadow_results.get("batch_accuracies", [])]
        variance = pstdev(batches) if len(batches) > 1 else 0.0

        checks = {
            # Older shadow providers did not emit batch data. Preserve their
            # existing sufficient-data decision; every current provider emits
            # this field and is subject to the three-batch requirement.
            "insufficient_batches": (
                "batch_accuracies" not in shadow_results
                or len(batches) >= MIN_BATCHES
            ),
            "sufficient_data": (
                bool(shadow_results.get("sufficient"))
                and total >= self.min_shadow_decisions
                and baseline_total >= self.min_shadow_decisions
            ),
            "statistical_significance": p_value is not None and p_value < self.alpha,
            "practical_significance": superiority_pp > self.superiority_threshold_pp,
            "accuracy_floor": accuracy >= self.accuracy_floor,
            "conservation": self._is_conservation_safe(conservation_state),
            "variance": variance <= 0.10,
        }
        promoted = all(checks.values())
        failed_checks = [name for name, passed in checks.items() if not passed]
        reason = "promoted" if promoted else self._reason(checks)
        if not promoted and not checks["insufficient_batches"]:
            reason = f"insufficient_batches ({len(batches)}/{MIN_BATCHES})"
        return {
            "promoted": promoted,
            "reason": reason,
            "failed_checks": failed_checks,
            "checks": checks,
            "accuracy": round(accuracy, 4),
            "baseline_accuracy": round(baseline_accuracy, 4),
            "superiority_pp": superiority_pp,
            "total": total,
            "baseline_total": baseline_total,
            "correct": correct,
            "baseline_correct": baseline_correct,
            "z_statistic": None if z_statistic is None else round(z_statistic, 6),
            "p_value": None if p_value is None else round(p_value, 8),
            "variance": round(variance, 4),
        }

    @staticmethod
    def _outcome_count(
        shadow_results: dict[str, Any],
        key: str,
        rate: float,
        total: int,
    ) -> int:
        """Return a bounded success count, deriving it for legacy providers."""
        raw_count = shadow_results.get(key)
        count = int(round(rate * total)) if raw_count is None else int(raw_count)
        return min(max(count, 0), max(total, 0))

    @staticmethod
    def _one_sided_two_proportion_test(
        correct: int,
        total: int,
        baseline_correct: int,
        baseline_total: int,
    ) -> tuple[float | None, float | None]:
        """Test H0: shadow accuracy is no greater than baseline accuracy."""
        if total <= 0 or baseline_total <= 0:
            return None, None

        shadow_rate = correct / total
        baseline_rate = baseline_correct / baseline_total
        pooled_rate = (correct + baseline_correct) / (total + baseline_total)
        standard_error_squared = pooled_rate * (1.0 - pooled_rate) * (
            1.0 / total + 1.0 / baseline_total
        )
        if standard_error_squared <= 0.0:
            return 0.0, 0.5

        z_statistic = (shadow_rate - baseline_rate) / sqrt(standard_error_squared)
        p_value = 0.5 * erfc(z_statistic / sqrt(2.0))
        return z_statistic, p_value

    def _reason(self, checks: dict[str, bool]) -> str:
        for name, passed in checks.items():
            if not passed:
                return name
        return "rejected"

    def _is_conservation_safe(self, conservation_state: Any) -> bool:
        if conservation_state is None:
            return False
        if isinstance(conservation_state, str):
            return conservation_state.strip().upper() == "GREEN"
        if not isinstance(conservation_state, dict) or not conservation_state:
            return False
        for key in ("status", "state", "phase"):
            value = conservation_state.get(key)
            if value is None:
                continue
            if not isinstance(value, str):
                return False
            return value.strip().upper() in self._SAFE_PHASES
        if conservation_state.get("overallSafe") is True or conservation_state.get("overall_safe") is True:
            return True
        return False
