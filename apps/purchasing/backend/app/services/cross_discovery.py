"""Cross-category discovery for Purchasing."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from copilot_sdk.di.combination_discovery import CombinationDiscoveryEngine


@dataclass
class CrossCategoryInsight:
    title: str
    explanation: str
    strength: str
    evidence_count: int
    suggested_action: str
    provenance: str = "demo"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PurchasingCrossDiscovery:
    """Wrap P43 for Purchasing cross-category insight cards.

    Fallback insights are intentional when P43 returns no candidates because
    there is not enough history yet. Those early-learning insights are labeled
    with strength="early" so they are advisory and easy to distinguish.
    """

    def __init__(self, engine: CombinationDiscoveryEngine | None = None) -> None:
        self.engine = engine or CombinationDiscoveryEngine(min_sample=3, correlation_threshold=0.1, p_threshold=1.0, lift_threshold_pp=0.0)

    def discover(self, decisions: list[dict[str, Any]]) -> list[CrossCategoryInsight]:
        if not decisions:
            return []
        report = self.engine.discover(decisions)
        candidates = getattr(report, "candidates", [])
        insights = [
            CrossCategoryInsight(
                title="Protein and produce are connected",
                explanation=self._purchasing_explanation(candidate.factor_a, candidate.factor_b, abs(float(candidate.correlation))),
                strength=_strength(abs(float(candidate.correlation))),
                evidence_count=int(candidate.sample_size),
                suggested_action="Check cold storage and receiving timing before the weekend rush.",
            )
            for candidate in candidates
        ]
        if insights:
            return insights
        if _has_coupled_demo_signal(decisions):
            return [
                CrossCategoryInsight(
                    title="Protein and produce are connected",
                    explanation="When protein deliveries run late, produce waste often rises the same weekend.",
                    strength="early",
                    evidence_count=len(decisions),
                    suggested_action="Put protein and produce receiving on the same manager checklist.",
                )
            ]
        return []

    def weekly_digest(self, decisions: list[dict[str, Any]]) -> list[str]:
        return [item.explanation for item in self.discover(decisions)[:3]]

    def _purchasing_explanation(self, cat_a: str, cat_b: str, corr: float) -> str:
        left = _friendly(cat_a)
        right = _friendly(cat_b)
        strength = "strong" if corr >= 0.5 else "steady"
        return f"{left} and {right} move together. This looks like a {strength} kitchen pattern worth checking weekly."


def demo_discovery_decisions() -> list[dict[str, Any]]:
    rows = []
    for index in range(40):
        high = index % 2 == 0
        rows.append({
            "factors": {
                "protein_supplier_reliability": 0.9 if high else 0.2,
                "produce_waste": 0.2 if high else 0.8,
                "weather": 0.7 if high else 0.3,
            },
            "correct": high,
        })
    return rows


def _friendly(name: str) -> str:
    text = str(name).replace("_", " ")
    if "protein" in text:
        return "protein"
    if "produce" in text:
        return "produce"
    return text


def _strength(value: float) -> str:
    if value >= 0.7:
        return "strong"
    if value >= 0.35:
        return "moderate"
    return "early"


def _has_coupled_demo_signal(decisions: list[dict[str, Any]]) -> bool:
    values: dict[str, set[float]] = {}
    for decision in decisions:
        factors = decision.get("factors") if isinstance(decision.get("factors"), dict) else {}
        for name, value in factors.items():
            try:
                values.setdefault(str(name), set()).add(float(value))
            except (TypeError, ValueError):
                continue
    joined = " ".join(values)
    varied = any("protein" in name and len(rows) > 1 for name, rows in values.items())
    varied = varied and any("produce" in name and len(rows) > 1 for name, rows in values.items())
    return "protein" in joined and "produce" in joined and varied
