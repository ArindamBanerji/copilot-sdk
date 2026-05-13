"""Default promotion gate for shadow results."""

from __future__ import annotations

from statistics import pstdev
from typing import Any


class DefaultPromotionGate:
    def __init__(
        self,
        superiority_threshold_pp: float = 5.0,
        accuracy_floor: float = 0.70,
        min_shadow_decisions: int = 10,
    ) -> None:
        self.superiority_threshold_pp = float(superiority_threshold_pp)
        self.accuracy_floor = float(accuracy_floor)
        self.min_shadow_decisions = int(min_shadow_decisions)

    def evaluate(
        self,
        shadow_results: dict[str, Any],
        conservation_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        total = int(shadow_results.get("total") or 0)
        accuracy = float(shadow_results.get("accuracy") or 0.0)
        baseline_accuracy = float(shadow_results.get("baseline_accuracy") or 0.0)
        superiority_pp = round((accuracy - baseline_accuracy) * 100.0, 4)
        conservation_status = str((conservation_state or {}).get("status", "GREEN")).upper()
        batches = [float(value) for value in shadow_results.get("batch_accuracies", [])]
        variance = pstdev(batches) if len(batches) > 1 else 0.0

        checks = {
            "sufficient_data": bool(shadow_results.get("sufficient")) and total >= self.min_shadow_decisions,
            "superiority": superiority_pp >= self.superiority_threshold_pp,
            "accuracy_floor": accuracy >= self.accuracy_floor,
            "conservation": conservation_status != "RED",
            "variance": variance <= 0.10,
        }
        promoted = all(checks.values())
        failed_checks = [name for name, passed in checks.items() if not passed]
        reason = "promoted" if promoted else self._reason(checks)
        return {
            "promoted": promoted,
            "reason": reason,
            "failed_checks": failed_checks,
            "checks": checks,
            "accuracy": round(accuracy, 4),
            "baseline_accuracy": round(baseline_accuracy, 4),
            "superiority_pp": superiority_pp,
            "total": total,
            "variance": round(variance, 4),
        }

    def _reason(self, checks: dict[str, bool]) -> str:
        for name, passed in checks.items():
            if not passed:
                return name
        return "rejected"
