"""Protocols for substantiation inputs and real measurement."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class RealInstrument(Protocol):
    """T-R: pilot-gated measurement, not day-zero substantiation."""

    decision_node_fields: list[str]

    def measure(self, cohort: list[dict]) -> dict:
        """Compute measured lift, accuracy, and power from a real cohort."""
        ...


@runtime_checkable
class ScrapedContextProvider(Protocol):
    """T-S: real external context for day-zero population."""

    def populate(self, entity_id: str) -> dict:
        """Fetch or compute external context for an entity."""
        ...


@runtime_checkable
class AnalyticClaim(Protocol):
    """T-A: proof reference and its stated conditions."""

    theorem_ref: str
    conditions: list[str]
    bound: str | None
