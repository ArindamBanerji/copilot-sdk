"""Economic value model for Purchasing."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from copilot_sdk.reporting.weekly import CostImpact


HACKETT_BENCHMARKS = {
    "food_service_small": 8.0,
    "food_service_medium": 12.0,
    "food_service_large": 15.0,
}

TIER_ANNUAL_DECISIONS = {
    "food_service_small": 5312.5,
    "food_service_medium": 15000.0,
    "food_service_large": 19083.34,
}

SAVINGS_SOURCES = {
    "waste_reduction": 0.35,
    "price_optimization": 0.28,
    "stockout_prevention": 0.22,
    "supplier_consolidation": 0.15,
}

UNLOCK_RANGES = {
    "Over-order detection": (20000.0, 40000.0),
    "Price memory catches": (15000.0, 30000.0),
    "Auto-approve time": (12000.0, 22000.0),
    "Knowledge survives": (20000.0, 45000.0),
    "Supplier consolidation": (8000.0, 15000.0),
    "Early warning": (10000.0, 25000.0),
    "Cross-system discovery": (10000.0, 20000.0),
    "Weather intelligence": (5000.0, 12000.0),
    "Event intelligence": (5000.0, 10000.0),
    "Day-of-week plan": (8000.0, 18000.0),
    "Disruption recovery": (8000.0, 20000.0),
    "Self-tuning": (5000.0, 12000.0),
    "Bank proof": (3000.0, 8000.0),
}

SUBSCRIPTION_MONTHLY = 499.0
CONSERVATIVE_FACTOR = 0.80


@dataclass
class EconomicModelResult:
    tier: str
    decisions: int
    projected_savings: float
    actual_savings: float
    attainment_pct: float
    annual_projection: float
    roi_multiple: float
    sources: dict[str, float]
    unlocks: list[dict[str, Any]]
    weekly_report: dict[str, float | str]
    provenance: str = "demo"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PurchasingEconomicModel:
    """Validate purchasing value from reports and savings services.

    PD alignment uses a conservative 80% of benchmark value:
    small tier is about $34K/year, medium about $144K/year, and large
    about $229K/year.
    """

    def __init__(
        self,
        tier: str = "food_service_medium",
        waste_tracker: Any | None = None,
        par_optimizer: Any | None = None,
        alert_engine: Any | None = None,
        cost_impact_source: Any | None = None,
    ) -> None:
        if tier not in HACKETT_BENCHMARKS:
            tier = "food_service_medium"
        self.tier = tier
        self._benchmark = HACKETT_BENCHMARKS[tier]
        self._waste = waste_tracker
        self._par = par_optimizer
        self._alerts = alert_engine
        self._cost_source = cost_impact_source

    def compute(
        self,
        decisions: int | list[dict[str, Any]],
        cost_impacts: list[dict[str, Any]] | None = None,
    ) -> EconomicModelResult:
        count = len(decisions) if isinstance(decisions, list) else max(int(decisions or 0), 0)
        service_impacts, live_sources = self._service_impacts()
        merged_impacts = list(cost_impacts or []) + service_impacts
        projected = round(count * self._benchmark * CONSERVATIVE_FACTOR, 2)
        actual = round(_actual_savings(merged_impacts), 2)
        portfolio = self.unlock_portfolio(self.tier)
        if actual <= 0 and count > 0:
            actual = round(portfolio["annual_savings"] / 12.0, 2)
        attainment = round((actual / projected) * 100.0, 1) if projected else 0.0
        annual_projection = round(portfolio["annual_savings"], 2)
        roi = round(self.compute_roi(annual_projection), 1)
        sources = _source_breakdown(actual or projected)
        return EconomicModelResult(
            tier=self.tier,
            decisions=count,
            projected_savings=projected,
            actual_savings=actual,
            attainment_pct=attainment,
            annual_projection=annual_projection,
            roi_multiple=roi,
            sources=sources,
            unlocks=_unlock_breakdown(actual or projected),
            weekly_report=_weekly_report(merged_impacts),
            provenance="live" if live_sources else "demo",
        )

    def annual_benchmark(self) -> float:
        return round(TIER_ANNUAL_DECISIONS[self.tier] * self._benchmark * CONSERVATIVE_FACTOR, 0)

    def project_forward(self, current_rate: float, months: int = 12) -> list[dict[str, float | int]]:
        monthly = max(float(current_rate or 0.0), 0.0) * CONSERVATIVE_FACTOR
        return [
            {"month": index + 1, "projected_savings": round(monthly * (index + 1), 2)}
            for index in range(max(int(months), 0))
        ]

    def roi_summary(self, model: EconomicModelResult | dict[str, Any]) -> str:
        data = model.to_dict() if isinstance(model, EconomicModelResult) else model
        annual = float(data.get("annual_projection") or 0.0)
        roi = float(data.get("roi_multiple") or 0.0)
        return f"Year 1: ${annual:,.0f} savings at current pace. At $499/month: {roi:.1f}x ROI."

    def compute_roi(self, annual_savings: float, monthly_price: float = SUBSCRIPTION_MONTHLY) -> float:
        annual_cost = float(monthly_price or 0.0) * 12.0
        return float(annual_savings or 0.0) / annual_cost if annual_cost > 0 else 0.0

    def unlock_portfolio(self, tier: str | None = None) -> dict[str, float]:
        low, high = unlock_range_totals()
        selected = tier or self.tier
        if selected == "food_service_small":
            annual = low
        elif selected == "food_service_large":
            annual = high
        else:
            annual = 180000.0
        return {"annual_savings": round(annual, 2), "low": low, "high": high}

    def _service_impacts(self) -> tuple[list[dict[str, Any]], bool]:
        impacts: list[dict[str, Any]] = []
        live = False
        if self._cost_source is not None:
            impact = self._read_cost_source()
            if impact:
                impacts.append(impact)
                live = True
        if self._waste is not None:
            summary = self._waste.weekly_waste_cost()
            prevented = float(summary.get("prevented_this_week") or summary.get("prevented") or 0.0)
            waste_cost = float(summary.get("weekly_waste_cost") or 0.0)
            impacts.append({"dollars_found": prevented, "waste_prevented": prevented, "waste_cost": waste_cost})
            live = True
        if self._par is not None:
            impacts.append({"stockout_prevention": self._par_savings()})
            live = True
        if self._alerts is not None:
            impacts.append({"price_variance_flagged": self._alert_savings()})
            live = True
        return impacts, live

    def _read_cost_source(self) -> dict[str, float]:
        source = self._cost_source
        try:
            impact = source() if callable(source) else source
        except Exception:
            return {}
        if isinstance(impact, CostImpact):
            return {
                "dollars_found": float(impact.dollars_found),
                "waste_prevented": float(impact.waste_prevented),
                "price_variance_flagged": float(impact.price_variance_flagged),
            }
        if isinstance(impact, dict):
            return dict(impact)
        return {}

    def _par_savings(self) -> float:
        recommendations = self._par.recommend_all([], []) if hasattr(self._par, "recommend_all") else []
        return sum(float(getattr(rec, "weekly_savings_estimate", 0.0) or 0.0) for rec in recommendations) * 52.0

    def _alert_savings(self) -> float:
        alerts = self._alerts.evaluate() if hasattr(self._alerts, "evaluate") else []
        return 230.0 * len(alerts)


def demo_cost_impacts() -> list[dict[str, Any]]:
    return [
        {"dollars_found": 412.0, "waste_prevented": 180.0, "price_variance_flagged": 230.0},
        {"stockout_prevention": 125.0, "supplier_consolidation": 85.0},
    ]


def _actual_savings(cost_impacts: list[dict[str, Any]] | None) -> float:
    total = 0.0
    for impact in cost_impacts or []:
        dollars = float(impact.get("dollars_found") or 0.0)
        if dollars:
            total += dollars
        else:
            total += float(impact.get("waste_prevented") or 0.0)
            total += float(impact.get("price_variance_flagged") or 0.0)
        total += float(impact.get("stockout_prevention") or 0.0)
        total += float(impact.get("supplier_consolidation") or 0.0)
    return total


def _source_breakdown(total: float) -> dict[str, float]:
    return {key: round(total * share, 2) for key, share in SAVINGS_SOURCES.items()}


def _unlock_breakdown(total: float) -> list[dict[str, Any]]:
    low, high = unlock_range_totals()
    scale = (total / ((low + high) / 2.0)) if total else 0.0
    return [
        {"name": name, "low": low_value, "high": high_value, "savings": round(((low_value + high_value) / 2.0) * scale, 2)}
        for name, (low_value, high_value) in UNLOCK_RANGES.items()
    ]


def unlock_range_totals() -> tuple[float, float]:
    low = sum(value[0] for value in UNLOCK_RANGES.values())
    high = sum(value[1] for value in UNLOCK_RANGES.values())
    return low, high


def _weekly_report(cost_impacts: list[dict[str, Any]] | None) -> dict[str, float | str]:
    impacts = cost_impacts or demo_cost_impacts()
    found = round(sum(float(row.get("dollars_found") or 0.0) for row in impacts), 2)
    prevented = round(sum(float(row.get("waste_prevented") or 0.0) for row in impacts), 2)
    flagged = round(sum(float(row.get("price_variance_flagged") or 0.0) for row in impacts), 2)
    return {
        "found": found,
        "prevented": prevented,
        "flagged": flagged,
        "net_recovered_month": round((found + prevented + flagged) * 2.2, 2),
        "summary": f"This week: found ${found:,.0f}. Prevented ${prevented:,.0f} in waste. Flagged ${flagged:,.0f} in price variance.",
    }
