"""Day-zero cohort state machine.

Part 5 extraction: the common state pattern from SOC and Purchasing after
both implementations proved the same three-state contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


INSTRUMENT_VALIDATED = "INSTRUMENT_VALIDATED"
ACCUMULATING = "ACCUMULATING"
MEASURED = "MEASURED"
STATES = (INSTRUMENT_VALIDATED, ACCUMULATING, MEASURED)


def compute_state(real_treatment_n: int, real_control_n: int, threshold_k: int) -> str:
    """Compute the three-state cohort day-zero status.

    No sample or structural counts are considered here.
    """

    if real_treatment_n == 0 and real_control_n == 0:
        return INSTRUMENT_VALIDATED
    if real_treatment_n < threshold_k or real_control_n < threshold_k:
        return ACCUMULATING
    return MEASURED


def evaluate_v7_gate(real: dict[str, Any], threshold_k: int) -> dict[str, Any]:
    """Evaluate the v7.0 tensor expansion gate over real cohorts only.

    The gate abstains while either arm is below threshold and raises if the
    provided real payload or optional records are not provenance=="real".
    """

    if real.get("provenance") != "real":
        raise ValueError("v7 gate input must have provenance=='real'")

    for record in real.get("records") or []:
        provenance = str(
            record.get("provenance") or record.get("provenance_tier") or ""
        ).strip().lower()
        if provenance != "real":
            raise ValueError("v7 gate input records must have provenance=='real'")

    treatment_n = int(real.get("treatment_n", 0))
    control_n = int(real.get("control_n", 0))
    base = {
        "real_treatment_n": treatment_n,
        "real_control_n": control_n,
        "threshold_k": threshold_k,
    }

    if treatment_n < threshold_k or control_n < threshold_k:
        return {**base, "status": "awaiting_real_cohorts", "lift": None}

    lift = real.get("lift")
    return {
        **base,
        "status": "conditions_met" if lift is not None else "conditions_not_met",
        "lift": lift,
    }


class BaseCohortDayZeroState(ABC):
    """Base class for domain-specific cohort day-zero state.

    Subclasses own domain-specific reading, structure counting, instrument
    loading, and lift computation. The base owns the invariant response shape
    and the three-state transition logic.
    """

    DOMAIN: str = ""
    THRESHOLD_K: int = 30

    @abstractmethod
    def _count_real_cohorts(self) -> dict[str, Any]:
        """Count decisions where provenance is real by treatment arm."""

    @abstractmethod
    def _count_structure_cohorts(self) -> dict[str, Any]:
        """Count sample structure for display only."""

    @abstractmethod
    def _load_instrument(self) -> dict[str, Any]:
        """Load oracle self-test results."""

    @abstractmethod
    def _compute_real_lift(self) -> float:
        """Compute lift from provenance=="real" records only."""

    def get_status(self) -> dict[str, Any]:
        """Build the full cohort-status response."""

        instrument = self._load_instrument()
        real = self._count_real_cohorts()
        real["threshold_k"] = self.THRESHOLD_K
        real["provenance"] = "real"
        structure = self._count_structure_cohorts()

        state = compute_state(
            int(real.get("treatment_n", 0)),
            int(real.get("control_n", 0)),
            self.THRESHOLD_K,
        )

        real["status"] = "measured" if state == MEASURED else "pending"
        real["lift"] = self._compute_real_lift() if state == MEASURED else None

        return {
            "state": state,
            "instrument": instrument,
            "real": real,
            "structure": structure,
        }

    def evaluate_gate(self) -> dict[str, Any]:
        """Evaluate the v7.0 gate from the current real cohort counts."""

        real = self._count_real_cohorts()
        real["threshold_k"] = self.THRESHOLD_K
        real["provenance"] = "real"
        return evaluate_v7_gate(real, self.THRESHOLD_K)
