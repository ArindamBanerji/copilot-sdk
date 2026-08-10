"""Valuation for discovered data combinations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


DOMAIN_DECISION_VALUES = {
    "soc": 85.0,
    "s2p": 45.0,
    "trading": 25.0,
    "purchasing": 12.0,
    "dataops": 65.0,
}

CONSERVATIVE_FACTOR = 0.70


class DataValuationModel:
    """Compute annual economic value from verified decision history."""

    def __init__(
        self,
        decisions: list[Any],
        accuracy: dict[str, Any],
        trust_profiles: list[Any],
    ) -> None:
        self._decisions = list(decisions)
        self._accuracy = dict(accuracy)
        self._trust_profiles = list(trust_profiles)

    def compute_value(self, source_name: str, improvement_pp: float) -> float:
        """Return annual value for adding ``source_name``."""
        decisions_per_year = self._annualize(len(self._decisions))
        avg_value = self._avg_decision_value()
        accuracy_gap = max(0.0, 1.0 - self._category_accuracy(source_name))
        trust_uplift = max(0.0, min(float(improvement_pp), 100.0)) / 100.0
        return round(decisions_per_year * avg_value * accuracy_gap * trust_uplift, 2)

    def compute_all_recommendations(self) -> list[dict[str, Any]]:
        """Compute deterministic valuations for the supplied source profiles."""
        results: list[dict[str, Any]] = []
        for profile in self._trust_profiles:
            item = _as_mapping(profile)
            source_name = str(item.get("source_name", item.get("name", item.get("source", ""))))
            if not source_name:
                continue
            improvement = _number(item.get("improvement_pp", item.get("improvement", item.get("lift_pp", 0.0))))
            value = self.compute_value(source_name, improvement)
            results.append(
                {
                    "source_name": source_name,
                    "computed_value_annual": value,
                    "annual_value": value,
                    "improvement_pp": improvement,
                    "methodology": self.methodology(source_name, improvement),
                    "confidence": self.confidence(),
                }
            )
        return results

    def methodology(self, source_name: str, improvement_pp: float) -> str:
        return (
            f"{self._annualize(len(self._decisions)):.0f} decisions/yr × "
            f"${self._avg_decision_value():,.2f}/avg × "
            f"{1.0 - self._category_accuracy(source_name):.3f} accuracy gap × "
            f"{float(improvement_pp):.1f}pp improvement"
        )

    def confidence(self) -> str:
        count = len(self._decisions)
        return "high" if count >= 100 else "moderate" if count >= 20 else "low"

    def _annualize(self, count: int) -> float:
        if count <= 0:
            return 0.0
        dates: list[datetime] = []
        for decision in self._decisions:
            date = _decision_date(decision)
            if date is not None:
                dates.append(date)
        if len(dates) >= 2:
            span_days = max((max(dates) - min(dates)).total_seconds() / 86400.0, 1.0)
            return round(count * 365.0 / span_days, 2)
        return float(count * 4)

    def _avg_decision_value(self) -> float:
        amounts = []
        for decision in self._decisions:
            item = _as_mapping(decision)
            for key in ("amount", "invoice_amount", "decision_value", "transaction_amount", "value"):
                if item.get(key) is not None:
                    amount = _number(item[key])
                    if amount >= 0:
                        amounts.append(amount)
                    break
        return round(sum(amounts) / len(amounts), 2) if amounts else 0.0

    def _category_accuracy(self, source_name: str) -> float:
        normalized = source_name.casefold()
        for key, value in self._accuracy.items():
            if str(key).casefold() == normalized:
                if isinstance(value, dict):
                    value = value.get("accuracy", value.get("current_accuracy", value.get("score", 0.0)))
                return max(0.0, min(1.0, _number(value)))
        for key in ("default", "overall", "accuracy"):
            if key in self._accuracy:
                return max(0.0, min(1.0, _number(self._accuracy[key])))
        return 0.0


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        result = value.to_dict()
        return result if isinstance(result, dict) else {}
    return {}


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _decision_date(decision: Any) -> datetime | None:
    item = _as_mapping(decision)
    raw = next((item.get(key) for key in ("timestamp", "created_at", "decision_at", "date") if item.get(key)), None)
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


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
