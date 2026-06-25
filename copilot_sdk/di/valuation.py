"""Valuation for discovered data combinations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


DOMAIN_DECISION_VALUES = {
    "soc": 85.0,
    "s2p": 45.0,
    "trading": 25.0,
    "purchasing": 12.0,
    "dataops": 65.0,
}

CONSERVATIVE_FACTOR = 0.70


@dataclass
class DataValuation:
    combination_id: str
    factor_a: str
    factor_b: str
    improvement_pp: float
    annual_value: float
    confidence: float
    description: str
    decisions_per_year: int
    decision_value: float
    acquisition_cost: float | None = None
    roi_multiple: float | str | None = None
    payback_months: float | None = None
    provenance: str = "derived"
    narrative: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValuationReport:
    valuations: list[DataValuation]
    top_combination: DataValuation | None
    narrative: str
    provenance: str = "derived"

    def to_dict(self) -> dict[str, Any]:
        return {
            "valuations": [valuation.to_dict() for valuation in self.valuations],
            "top_combination": self.top_combination.to_dict() if self.top_combination else None,
            "narrative": self.narrative,
            "provenance": self.provenance,
        }


class DataValuationEngine:
    """Assign dollar value to discovered data combinations."""

    def __init__(self, domain: str, decisions_per_year: int | None = None, custom_value: float | None = None) -> None:
        self.domain = domain
        self.decisions_per_year = decisions_per_year
        self._decision_value = float(custom_value if custom_value is not None else DOMAIN_DECISION_VALUES.get(domain, 25.0))

    def valuate(self, candidates: list[Any], decisions_per_year: int | None = None) -> ValuationReport:
        valuations = [
            self._from_candidate(candidate, decisions_per_year=decisions_per_year)
            for candidate in candidates
        ]
        valuations.sort(key=lambda item: item.annual_value, reverse=True)
        top = valuations[0] if valuations else None
        narrative = (
            f"Top data combination: {top.factor_a} x {top.factor_b}, estimated value ${_money(top.annual_value)}/year."
            if top
            else "No data combinations are ready for valuation."
        )
        return ValuationReport(valuations, top, narrative)

    def valuate_single(
        self,
        improvement_pp: float,
        decisions_per_year: int | None = None,
        factor_a: str = "source_a",
        factor_b: str = "source_b",
        description: str | None = None,
        confidence: float = 0.70,
    ) -> DataValuation:
        annual_decisions = int(decisions_per_year if decisions_per_year is not None else self.decisions_per_year or 0)
        clamped_pp = _clamp_pp(improvement_pp)
        value = self._annual_value(clamped_pp, annual_decisions)
        label = description or f"{factor_a} x {factor_b}"
        narrative = (
            f"{label}: +{_pp(clamped_pp)} predictive power. "
            f"Estimated annual value: ${_money(value)} "
            "(conservative: 70% of measured improvement)."
        )
        return DataValuation(
            _combination_id(factor_a, factor_b),
            factor_a,
            factor_b,
            clamped_pp,
            round(value, 2),
            _clamp(confidence),
            label,
            annual_decisions,
            self._decision_value,
            None,
            None,
            None,
            "derived",
            narrative,
        )

    def estimate_annual_decisions(self, decisions: list[dict[str, Any]]) -> int:
        return int(len(decisions) * 4)

    def with_acquisition_cost(self, valuation: DataValuation, cost: float) -> DataValuation:
        monthly_value = valuation.annual_value / 12.0
        payback = round(float(cost) / monthly_value, 2) if monthly_value > 0 and cost > 0 else None
        roi: float | str
        roi = "infinite" if cost == 0 and valuation.annual_value > 0 else round(valuation.annual_value / float(cost), 2) if cost > 0 else 0.0
        return DataValuation(
            **{
                **valuation.to_dict(),
                "acquisition_cost": float(cost),
                "roi_multiple": roi,
                "payback_months": payback,
            }
        )

    def _from_candidate(self, candidate: Any, decisions_per_year: int | None = None) -> DataValuation:
        factor_a = str(getattr(candidate, "factor_a", "source_a"))
        factor_b = str(getattr(candidate, "factor_b", "source_b"))
        improvement_pp = float(getattr(candidate, "lift_pp", getattr(candidate, "improvement_pp", 0.0)) or 0.0)
        confidence = _confidence(candidate)
        description = str(getattr(candidate, "description", f"{factor_a} x {factor_b}"))
        return self.valuate_single(improvement_pp, decisions_per_year, factor_a, factor_b, description, confidence)

    def _annual_value(self, improvement_pp: float, decisions_per_year: int) -> float:
        return (float(improvement_pp) / 100.0) * max(int(decisions_per_year), 0) * self._decision_value * CONSERVATIVE_FACTOR


def _confidence(candidate: Any) -> float:
    correlation = abs(float(getattr(candidate, "correlation", 0.0) or 0.0))
    sample_size = max(int(getattr(candidate, "sample_size", 0) or 0), 0)
    sample_component = min(sample_size / 100.0, 1.0)
    return _clamp(0.5 * correlation + 0.5 * sample_component)


def _combination_id(factor_a: str, factor_b: str) -> str:
    return f"{factor_a}__{factor_b}".replace(" ", "_").lower()


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _clamp_pp(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _money(value: float) -> str:
    if abs(value) >= 1000:
        return f"{round(value / 1000)}K"
    return f"{round(value):,}"


def _pp(value: float) -> str:
    number = round(float(value), 1)
    return str(int(number)) if number.is_integer() else str(number)
