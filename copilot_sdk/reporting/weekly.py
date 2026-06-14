"""Domain-agnostic weekly report generation."""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class CategorySummary:
    category: str
    decisions_count: int
    correct_count: int
    accuracy: float
    top_action: str | None


@dataclass
class CostImpact:
    dollars_found: float
    waste_prevented: float
    price_variance_flagged: float
    net_recovered_period: float


@dataclass
class SupplierChange:
    supplier_id: str
    metric: str
    previous_value: float
    current_value: float
    direction: str


@dataclass
class WeeklyReport:
    domain: str
    period_start: float
    period_end: float
    generated_at: float
    total_decisions: int
    total_verified: int
    overall_accuracy: float
    conservation_status: str
    conservation_q: float
    conservation_alpha: float
    categories: list[CategorySummary]
    cost_impact: CostImpact
    supplier_changes: list[SupplierChange]
    iks_current: float
    iks_delta: float


CostExtractor = Callable[[dict[str, Any], dict[str, Any], Any], dict[str, Any]]


class WeeklyReportGenerator:
    """Read-only weekly report engine using graph timestamps for windowing."""

    SECONDS_PER_DAY = 86400

    def __init__(
        self,
        graph_store: Any,
        scorer: Any,
        domain: str,
        cost_extractor: CostExtractor | None = None,
        preset: Any | None = None,
    ) -> None:
        self._store = graph_store
        self._scorer = scorer
        self._domain = str(domain)
        self._cost_extractor = cost_extractor
        self._preset = preset

    def generate(self, period_days: int = 7) -> WeeklyReport:
        """Generate a report for the last period_days using graph time."""

        all_decisions = list(self._store.get_all_decisions(self._domain) or [])
        if not all_decisions:
            return self._empty_report()

        period_end = max(float(decision.get("created_at", 0.0)) for decision in all_decisions)
        period_start = period_end - (int(period_days) * self.SECONDS_PER_DAY)

        window = [
            decision
            for decision in all_decisions
            if float(decision.get("created_at", 0.0)) >= period_start
        ]
        verified = self._window_verified(period_start)
        verified_ids = {str(decision.get("decision_id")) for decision in verified}
        correct = [decision for decision in verified if decision.get("is_correct")]
        category_rows = [
            {**decision, **self._verified_by_id(verified).get(str(decision.get("decision_id")), {})}
            for decision in window
        ]

        categories = self._compute_categories(category_rows)
        cost_impact = self._compute_cost_impact(verified)
        cons_status, cons_q, cons_alpha = self._read_conservation()
        iks_current, iks_delta = self._compute_iks(period_start, period_end)

        return WeeklyReport(
            domain=self._domain,
            period_start=period_start,
            period_end=period_end,
            generated_at=time.time(),
            total_decisions=len(window),
            total_verified=len(verified_ids),
            overall_accuracy=(len(correct) / len(verified)) if verified else 0.0,
            conservation_status=cons_status,
            conservation_q=cons_q,
            conservation_alpha=cons_alpha,
            categories=categories,
            cost_impact=cost_impact,
            supplier_changes=[],
            iks_current=iks_current,
            iks_delta=iks_delta,
        )

    def _empty_report(self) -> WeeklyReport:
        cons_status, cons_q, cons_alpha = self._read_conservation()
        return WeeklyReport(
            domain=self._domain,
            period_start=0.0,
            period_end=0.0,
            generated_at=time.time(),
            total_decisions=0,
            total_verified=0,
            overall_accuracy=0.0,
            conservation_status=cons_status,
            conservation_q=cons_q,
            conservation_alpha=cons_alpha,
            categories=[],
            cost_impact=CostImpact(0.0, 0.0, 0.0, 0.0),
            supplier_changes=[],
            iks_current=0.0,
            iks_delta=0.0,
        )

    def _window_verified(self, period_start: float) -> list[dict[str, Any]]:
        verified = list(self._store.get_verified_decisions(self._domain) or [])
        return [
            decision
            for decision in verified
            if float(decision.get("created_at", 0.0)) >= period_start
        ]

    def _compute_categories(self, window: list[dict[str, Any]]) -> list[CategorySummary]:
        cat_decisions: dict[str, list[dict[str, Any]]] = {}
        for decision in window:
            category = str(decision.get("category") or "unknown")
            cat_decisions.setdefault(category, []).append(decision)

        summaries: list[CategorySummary] = []
        for category, decisions in sorted(cat_decisions.items()):
            cat_verified = [decision for decision in decisions if decision.get("is_correct") is not None]
            cat_correct = [decision for decision in cat_verified if decision.get("is_correct")]
            actions = [
                str(decision.get("recommended_action") or "")
                for decision in decisions
                if decision.get("recommended_action") is not None
            ]
            top_action = Counter(actions).most_common(1)[0][0] if actions else None
            summaries.append(
                CategorySummary(
                    category=category,
                    decisions_count=len(decisions),
                    correct_count=len(cat_correct),
                    accuracy=(len(cat_correct) / len(cat_verified)) if cat_verified else 0.0,
                    top_action=top_action,
                )
            )
        return summaries

    def _compute_cost_impact(self, verified: list[dict[str, Any]]) -> CostImpact:
        if not self._cost_extractor:
            return CostImpact(0.0, 0.0, 0.0, 0.0)

        total_waste = 0.0
        total_variance = 0.0
        for decision in verified:
            try:
                impact = self._cost_extractor(decision, decision, self._preset)
                total_waste += float(impact.get("waste_prevented", 0.0))
                total_variance += float(impact.get("price_variance_flagged", 0.0))
            except Exception:
                continue
        dollars = total_waste + total_variance
        return CostImpact(dollars, total_waste, total_variance, dollars)

    def _read_conservation(self) -> tuple[str, float, float]:
        try:
            status = str(self._scorer.get_phase())
            alpha = float(self._scorer.get_alpha())
            cons = self._store.get_conservation_state(self._domain)
            q = float(cons.get("q", 0.0)) if isinstance(cons, dict) else 0.0
            return status, q, alpha
        except Exception:
            return "UNKNOWN", 0.0, 0.0

    def _compute_iks(self, period_start: float, period_end: float) -> tuple[float, float]:
        try:
            del period_end
            result = self._scorer.trajectory()
            iks_current = float(getattr(result, "current_iks", 0.0) or 0.0)
            iks_prior = 0.0
            points = list(getattr(result, "points", []) or [])
            prior_points = [
                point
                for index, point in enumerate(points)
                if _point_timestamp(point, index) <= period_start
            ]
            if prior_points:
                iks_prior = float(getattr(prior_points[-1], "iks", 0.0) or 0.0)
            return iks_current, iks_current - iks_prior
        except Exception:
            return 0.0, 0.0

    @staticmethod
    def _verified_by_id(verified: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {str(decision.get("decision_id")): decision for decision in verified}


def purchasing_cost_extractor(decision: dict[str, Any], outcome: dict[str, Any], preset: Any = None) -> dict[str, float]:
    """Extract conservative cost impact from one verified purchasing decision."""

    result = {
        "dollars_found": 0.0,
        "waste_prevented": 0.0,
        "price_variance_flagged": 0.0,
    }

    context = _merged_context(decision, outcome)
    waste_cost = context.get("waste_cost") or context.get("stockout_revenue_loss")
    if waste_cost is not None:
        try:
            result["waste_prevented"] = abs(float(waste_cost))
            result["dollars_found"] = result["waste_prevented"]
            return result
        except (TypeError, ValueError):
            pass

    action = str(decision.get("recommended_action") or "")
    historical_waste = _get_factor_value(decision, preset, "historical_waste")
    if historical_waste is not None and historical_waste > 0.5:
        result["waste_prevented"] = max(
            result["waste_prevented"],
            round(historical_waste * 25.0, 2),
        )

    if bool(decision.get("is_correct")) and action in {"order_less", "skip"}:
        floor = 50.0 if action == "skip" else 25.0
        result["waste_prevented"] = max(result["waste_prevented"], floor)

    price_memory_index = _get_factor_value(decision, preset, "price_memory_index")
    if price_memory_index is not None and price_memory_index < 0.3:
        result["price_variance_flagged"] = 15.0

    result["dollars_found"] = result["waste_prevented"] + result["price_variance_flagged"]
    return result


def _merged_context(decision: dict[str, Any], outcome: dict[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for source in (decision, outcome):
        raw_context = source.get("context")
        if isinstance(raw_context, dict):
            context.update(raw_context)
        elif isinstance(raw_context, str):
            try:
                loaded = json.loads(raw_context)
            except (json.JSONDecodeError, TypeError):
                loaded = None
            if isinstance(loaded, dict):
                context.update(loaded)

        metadata = source.get("outcome_metadata")
        if isinstance(metadata, dict):
            nested = metadata.get("context")
            if isinstance(nested, dict):
                context.update(nested)
            elif isinstance(nested, str):
                try:
                    loaded = json.loads(nested)
                except (json.JSONDecodeError, TypeError):
                    loaded = None
                if isinstance(loaded, dict):
                    context.update(loaded)
    return context


def _get_factor_value(decision: dict[str, Any], preset: Any, factor_name: str) -> float | None:
    factor_names = _factor_names(preset)
    raw_factor_vector = decision.get("factor_vector")
    factor_vector = [] if raw_factor_vector is None else raw_factor_vector
    if factor_name in factor_names:
        index = factor_names.index(factor_name)
        try:
            if isinstance(factor_vector, dict):
                return float(factor_vector[factor_name])
            if not isinstance(factor_vector, (str, bytes)) and len(factor_vector) > index:
                return float(factor_vector[index])
        except (KeyError, TypeError, ValueError, IndexError):
            pass

    factors = decision.get("factors")
    if isinstance(factors, dict) and factor_name in factors:
        try:
            return float(factors[factor_name])
        except (TypeError, ValueError):
            return None
    return None


def _point_timestamp(point: Any, index: int) -> float:
    try:
        return float(getattr(point, "timestamp", 0.0) or 0.0)
    except (TypeError, ValueError):
        return float(index)


def _factor_names(preset: Any) -> list[str]:
    if preset is None:
        return []
    shape = getattr(preset, "shape", None)
    if shape is not None:
        return list(getattr(shape, "factor_names", []) or [])
    return list(getattr(preset, "factor_names", []) or [])
