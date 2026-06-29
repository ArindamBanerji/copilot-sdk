"""Demo supply disruption recovery service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class DisruptionRecoveryService:
    """Tracks recovery from supply disruptions."""

    def __init__(self, active: bool = True) -> None:
        self.active = active
        self._categories = ["protein", "produce"] if active else []
        self._started_at = datetime(2026, 6, 26, tzinfo=timezone.utc)

    def trigger_disruption(self, category: str) -> dict[str, Any]:
        clean = str(category).strip().lower()
        if clean and clean not in self._categories:
            self._categories.append(clean)
        self.active = True
        return self.recovery_status()

    def recovery_status(self) -> dict[str, Any]:
        if not self.active:
            return {
                "status": "stable",
                "days_since_disruption": 0,
                "categories_affected": [],
                "gamma": 1.0,
                "re_calibration_progress_pct": 100,
                "estimated_days_to_green": 0,
                "narrative": "No active supply disruption. Ordering patterns are stable.",
                "provenance": "demo",
            }
        return {
            "status": "recovering",
            "days_since_disruption": 3,
            "categories_affected": list(self._categories),
            "gamma": 1.6,
            "re_calibration_progress_pct": 60,
            "estimated_days_to_green": 4,
            "narrative": (
                "Protein supply disrupted 3 days ago. Recovery: 60% complete. "
                "The system is re-learning patterns from your last 50 orders."
            ),
            "provenance": "demo",
        }

    def recovery_history(self) -> list[dict[str, Any]]:
        return [
            {
                "disruption_id": "DISR-2026-06-PROTEIN",
                "category": "protein",
                "days_to_green": 7,
                "peak_gamma": 1.6,
                "resolved": False,
                "provenance": "demo",
            },
            {
                "disruption_id": "DISR-2026-04-DAIRY",
                "category": "dairy",
                "days_to_green": 5,
                "peak_gamma": 1.4,
                "resolved": True,
                "provenance": "demo",
            },
        ]
