"""Cross-copilot sunk-investment value aggregation.

The calculator consumes PILOT-02-shaped reports through a deliberately small
mapping/attribute boundary.  It does not manufacture financial impact: a
copilot with no attributed report contributes zero impact and remains
modelled until measured evidence is supplied.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from threading import RLock
from typing import Any


MEASURED_TIERS = {"t_o", "observed", "measured", "t_r", "reproduced"}
MODELLED_TIERS = {"t_s", "synthetic", "modelled", "modeled"}


@dataclass(frozen=True)
class CopilotValue:
    """The attributed value and evidence for one copilot."""

    copilot: str
    decisions: int = 0
    accuracy_delta: float = 0.0
    financial_impact: float = 0.0
    evidence_tier: str = "T_S"
    verified_outcomes: int = 0
    evidence_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "copilot": self.copilot,
            "decisions": self.decisions,
            "accuracy_delta": self.accuracy_delta,
            "financial_impact": self.financial_impact,
            "evidence_tier": self.evidence_tier,
            "verified_outcomes": self.verified_outcomes,
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True)
class EnterpriseROI:
    """A JSON-safe, evidence-labelled platform value report."""

    per_copilot: list[dict[str, Any]] = field(default_factory=list)
    total_impact: float = 0.0
    total_decisions: int = 0
    weighted_accuracy_delta: float = 0.0
    roi_multiplier: float = 0.0
    baseline_cost: float = 0.0
    evidence_label: str = "modelled"

    @property
    def financial_impact(self) -> float:
        """Compatibility alias for consumers that call the total value impact."""

        return self.total_impact

    def to_dict(self) -> dict[str, Any]:
        return {
            "per_copilot": self.per_copilot,
            "total_impact": self.total_impact,
            "total_decisions": self.total_decisions,
            "weighted_accuracy_delta": self.weighted_accuracy_delta,
            "roi_multiplier": self.roi_multiplier,
            "baseline_cost": self.baseline_cost,
            "evidence_label": self.evidence_label,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, allow_nan=False)


class SunkInvestmentCalculator:
    """Aggregate measured transfer value without upgrading weak evidence.

    ``reports`` may contain :class:`ImprovementReport` objects or their
    ``to_dict`` representations.  ``financial_impacts`` is an optional
    explicit attribution source for customers whose report stores the
    financial ledger separately.  ``verified_outcomes`` can supply the
    canonical outcome count independently of the transfer report.
    """

    def __init__(
        self,
        reports: Mapping[str, Any] | None = None,
        *,
        financial_impacts: Mapping[str, float] | None = None,
        verified_outcomes: Mapping[str, int] | None = None,
        baseline_cost: float = 0.0,
    ) -> None:
        if baseline_cost < 0:
            raise ValueError("baseline_cost must be non-negative")
        self._reports = dict(reports or {})
        self._financial_impacts = {
            str(key): float(value) for key, value in (financial_impacts or {}).items()
        }
        self._verified_outcomes = {
            str(key): int(value) for key, value in (verified_outcomes or {}).items()
        }
        if any(value < 0 for value in self._verified_outcomes.values()):
            raise ValueError("verified outcome counts must be non-negative")
        self._baseline_cost = float(baseline_cost)
        self._lock = RLock()

    def compute(self, copilots: list[str]) -> EnterpriseROI:
        """Return cumulative platform value for the requested copilots."""

        with self._lock:
            rows = [self._copilot_value(str(copilot)).to_dict() for copilot in copilots]
            total_decisions = sum(int(row["decisions"]) for row in rows)
            total_impact = sum(float(row["financial_impact"]) for row in rows)
            weighted_delta = (
                sum(float(row["accuracy_delta"]) * int(row["decisions"]) for row in rows)
                / total_decisions
                if total_decisions
                else 0.0
            )
            multiplier = total_impact / self._baseline_cost if self._baseline_cost else 0.0
            return EnterpriseROI(
                per_copilot=rows,
                total_impact=_finite(total_impact),
                total_decisions=total_decisions,
                weighted_accuracy_delta=_finite(weighted_delta),
                roi_multiplier=_finite(multiplier),
                baseline_cost=_finite(self._baseline_cost),
                evidence_label=_evidence_label(row["evidence_tier"] for row in rows),
            )

    @property
    def known_copilots(self) -> frozenset[str]:
        """Return copilot names for which an input source was configured."""

        return frozenset(self._reports) | frozenset(self._financial_impacts) | frozenset(self._verified_outcomes)

    def _copilot_value(self, copilot: str) -> CopilotValue:
        report = self._reports.get(copilot)
        overall = _mapping(_field(report, "overall"))
        decisions = _int(_first(overall, report, ("total_decisions", "decisions")))
        accuracy_delta = _float(
            _first(overall, report, ("overall_delta", "accuracy_delta", "delta"))
        )
        impact = self._financial_impacts.get(copilot)
        if impact is None:
            impact = _float(
                _first(overall, report, ("total_financial_impact", "financial_impact", "impact"))
            )
        tier = str(_first(overall, report, ("evidence_tier", "evidence_label")) or "T_S")
        verified = self._verified_outcomes.get(copilot, decisions if _is_measured(tier) else 0)
        evidence_ref = _first(overall, report, ("evidence_ref", "session_id", "report_hash"))
        return CopilotValue(
            copilot=copilot,
            decisions=decisions,
            accuracy_delta=accuracy_delta,
            financial_impact=impact,
            evidence_tier=tier,
            verified_outcomes=verified,
            evidence_ref=None if evidence_ref is None else str(evidence_ref),
        )


def _field(value: Any, name: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _first(primary: Mapping[str, Any], secondary: Any, names: tuple[str, ...]) -> Any:
    for name in names:
        if name in primary and primary[name] is not None:
            return primary[name]
        value = _field(secondary, name)
        if value is not None:
            return value
    return None


def _float(value: Any) -> float:
    try:
        number = float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
    return _finite(number)


def _int(value: Any) -> int:
    try:
        return max(int(value or 0), 0)
    except (TypeError, ValueError):
        return 0


def _finite(value: float) -> float:
    return value if math.isfinite(value) else 0.0


def _is_measured(tier: str) -> bool:
    return tier.strip().lower() in MEASURED_TIERS


def _evidence_label(tiers: Any) -> str:
    normalized = [str(tier).strip().lower() for tier in tiers]
    if not normalized or all(tier in MODELLED_TIERS for tier in normalized):
        return "modelled"
    if all(_is_measured(tier) for tier in normalized):
        return "measured"
    return "partially measured"
