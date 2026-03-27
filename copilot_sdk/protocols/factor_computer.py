"""
FactorComputer Protocol — compute one factor value from event context.
Returns float in [0.0, 1.0]. 0.0 = high risk. 1.0 = low risk / neutral.
Must be deterministic given same inputs.
Must not modify graph state (read-only).
"""
from typing import Protocol


class FactorComputer(Protocol):
    factor_name:  str
    factor_index: int

    def compute(self, event: object) -> float:
        """Returns factor value in [0.0, 1.0]."""
        ...
