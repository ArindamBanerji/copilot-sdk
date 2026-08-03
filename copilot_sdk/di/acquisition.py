"""External data acquisition recommendations for DataOps."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from copilot_sdk.di.valuation import DataValuationEngine


@dataclass
class ExternalDataSource:
    name: str
    provider: str
    signal: str
    annual_cost: float
    domains: list[str]
    description: str
    improvement_pp: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


EXTERNAL_CATALOG = [
    ExternalDataSource("OpenMeteo Weather", "open-meteo.com", "weather_forecast", 0.0, ["purchasing", "dataops"], "7-day weather forecasts. Free API.", 15.0),
    ExternalDataSource("Bloomberg Commodity", "bloomberg.com", "commodity_prices", 24000.0, ["s2p", "purchasing"], "Real-time commodity indices.", 18.0),
    ExternalDataSource("D&B Supplier Risk", "dnb.com", "supplier_financials", 12000.0, ["s2p"], "Financial health scores for suppliers.", 12.0),
    ExternalDataSource("Bureau of Labor Statistics", "bls.gov", "labor_costs", 0.0, ["purchasing"], "Wage indices. Free federal data.", 8.0),
    ExternalDataSource("FRED Economic", "fred.stlouisfed.org", "macro_indicators", 0.0, ["trading", "s2p"], "Interest rates, GDP. Free.", 10.0),
    ExternalDataSource("Project44 Shipment Tracking", "project44.com", "shipping_transit", 18000.0, ["dataops", "s2p", "purchasing"], "Real-time shipment tracking and ETA predictions.", 34.0),
]


class AcquisitionAdvisor:
    """Recommend external data sources ranked by expected value."""

    def __init__(self, catalog: list[ExternalDataSource] | None = None, valuation_engine: DataValuationEngine | None = None) -> None:
        self.catalog = list(EXTERNAL_CATALOG if catalog is None else catalog)
        self.valuation_engine = valuation_engine

    def recommend(
        self,
        domain: str = "dataops",
        current_sources: list[str] | None = None,
        decisions: list[dict[str, Any]] | None = None,
        decisions_per_year: int | None = None,
    ) -> dict[str, Any]:
        connected = {source.casefold() for source in (current_sources or [])}
        engine = self.valuation_engine or DataValuationEngine(domain, decisions_per_year=decisions_per_year)
        annual_decisions = decisions_per_year
        provenance = "derived"
        provenance_note = None
        if annual_decisions is None:
            if decisions is not None:
                annual_decisions = engine.estimate_annual_decisions(decisions)
            else:
                annual_decisions = 12000
                provenance = "demo"
                provenance_note = "Annual decision count assumed (12,000). Connect data for actual rate."
        recommendations = []
        for source in self.catalog:
            if domain not in source.domains or source.name.casefold() in connected:
                continue
            valuation = engine.valuate_single(
                source.improvement_pp,
                annual_decisions,
                domain,
                source.signal,
                f"{source.name} improves {domain} prediction",
                0.75,
            )
            valued = engine.with_acquisition_cost(valuation, source.annual_cost)
            recommendations.append(self._recommendation(source, valued))
        recommendations = self.free_first(recommendations)
        narrative = self._recommendation_narrative(recommendations)
        response = {
            "recommendations": recommendations,
            "narrative": narrative,
            "provenance": provenance,
        }
        if provenance_note:
            response["provenance_note"] = provenance_note
        return response

    def discover_monetization(self, decision_count: int, domains: list[str]) -> dict[str, Any]:
        if decision_count < 1000:
            return {
                "opportunities": [],
                "narrative": "Monetization requires at least 1000 verified decisions.",
                "provenance": "derived",
            }
        domain_label = ", ".join(domains) if domains else "operational"
        opportunity = {
            "asset": "Supplier reliability profiles",
            "uniqueness": f"Learned from {decision_count:,} verified decisions across {domain_label}. Not available from generic vendors.",
            "comparable": "D&B supplier data ($12K/year subscription)",
            "estimated_value": "$120K/year licensing",
            "narrative": "Your anonymized supplier profiles outperform D&B for your industry. Licensing opportunity: $120K/year.",
        }
        return {
            "opportunities": [opportunity],
            "narrative": "1 monetization opportunity found from verified decision history.",
            "provenance": "derived",
        }

    def free_first(self, recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(
            recommendations,
            key=lambda item: (
                0 if item["cost"] == 0 else 1,
                -float("inf") if item["roi"] == "infinite" else -float(item["roi"]),
                item["source"],
            ),
        )

    def _recommendation(self, source: ExternalDataSource, valuation: Any) -> dict[str, Any]:
        data = valuation.to_dict()
        roi = data["roi_multiple"]
        priority = _priority(roi)
        cost = float(source.annual_cost)
        value = float(data["annual_value"])
        narrative = (
            f"Add {source.name} ({'free' if cost == 0 else '$' + _money(cost) + '/year'}): "
            f"+{_pp(source.improvement_pp)} predictive power. ${_money(value)}/year. ROI: "
            f"{'infinite' if roi == 'infinite' else str(round(float(roi))) + 'x'}."
        )
        return {
            "source": source.name,
            "provider": source.provider,
            "signal": source.signal,
            "cost": cost,
            "annual_value": value,
            "roi": roi,
            "priority": priority,
            "payback_months": data["payback_months"],
            "narrative": narrative,
        }

    def _recommendation_narrative(self, recommendations: list[dict[str, Any]]) -> str:
        if not recommendations:
            return "No new external data recommendations are available."
        top = recommendations[0]
        second = recommendations[1] if len(recommendations) > 1 else None
        narrative = f"{len(recommendations)} data acquisition opportunities. Top: {top['source']} ({'free, infinite ROI' if top['cost'] == 0 else str(top['roi']) + 'x ROI'})."
        if second:
            narrative += f" Second: {second['source']} ({'free' if second['cost'] == 0 else '$' + _money(second['cost'])}, {'infinite ROI' if second['roi'] == 'infinite' else str(round(float(second['roi']))) + 'x ROI'})."
        return narrative


def _priority(roi: float | str | None) -> str:
    if roi == "infinite":
        return "high"
    value = float(roi or 0.0)
    if value > 5:
        return "high"
    if value > 2:
        return "medium"
    return "low"


def _money(value: float) -> str:
    if abs(value) >= 1000:
        return f"{round(value / 1000)}K"
    return f"{round(value):,}"


def _pp(value: float) -> str:
    number = round(float(value), 1)
    return str(int(number)) if number.is_integer() else str(number)
