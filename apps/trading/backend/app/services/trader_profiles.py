"""Trader profile analytics for Trading execution quality."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from copilot_sdk.scoring.presets.trading import TradingPreset


DOMAIN = "trading"
_SHAPE = TradingPreset().shape
VALID_CATEGORIES = set(_SHAPE.category_names)
VALID_ACTIONS = set(_SHAPE.action_names)
FACTOR_NAMES = tuple(_SHAPE.factor_names)
STRONG_ACTION = "strong_execution"


class TraderProfileService:
    def __init__(self, graph_store: Any):
        self._store = graph_store

    def list_traders(self) -> list[dict[str, Any]]:
        profiles = [
            self._profile_from_decisions(trader_id, decisions)
            for trader_id, decisions in sorted(self._grouped_decisions().items())
        ]
        return [
            {
                "trader_id": profile["trader_id"],
                "verified_count": profile["verified_count"],
                "accuracy": profile["accuracy"],
                "top_category": profile["top_category"],
                "strongest_factor": profile["strongest_factor"],
            }
            for profile in sorted(profiles, key=lambda row: (-row["verified_count"], row["trader_id"]))
        ]

    def get_trader_profile(self, trader_id: str) -> dict[str, Any]:
        decisions = self._grouped_decisions().get(_normalize_trader(trader_id), [])
        return self._profile_from_decisions(_normalize_trader(trader_id), decisions)

    def get_trader_edge(self, trader_id: str) -> dict[str, Any]:
        profile = self.get_trader_profile(trader_id)
        return {
            "trader_id": profile["trader_id"],
            "verified_count": profile["verified_count"],
            "accuracy": profile["accuracy"],
            "factor_strengths": profile["factor_strengths"],
            "edge_summary": profile["edge_summary"],
            "recommendations": _execution_recommendations(profile),
            "source": "graphstore",
        }

    def get_trader_comparison(self, trader_ids: list[str]) -> dict[str, Any]:
        normalized = [_normalize_trader(trader_id) for trader_id in trader_ids if _normalize_trader(trader_id)]
        profiles = [self.get_trader_profile(trader_id) for trader_id in normalized]
        return {
            "traders": profiles,
            "leader": _leader(profiles),
            "complementary_edges": _complementary_edges(profiles),
            "source": "graphstore",
        }

    def leaderboard(self, metric: str = "accuracy") -> list[dict[str, Any]]:
        rows = self.list_traders()
        key = "verified_count" if metric == "verified_count" else "accuracy"
        return sorted(rows, key=lambda row: (-float(row.get(key) or 0.0), row["trader_id"]))

    def _grouped_decisions(self) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for decision in self._verified_decisions():
            if not _valid_decision(decision):
                continue
            grouped[_decision_trader(decision)].append(decision)
        return dict(grouped)

    def _verified_decisions(self) -> list[dict[str, Any]]:
        get_verified = getattr(self._store, "get_verified_decisions", None)
        if not callable(get_verified):
            return []
        try:
            return [row for row in get_verified(DOMAIN) if isinstance(row, dict)]
        except Exception:
            return []

    def _profile_from_decisions(self, trader_id: str, decisions: list[dict[str, Any]]) -> dict[str, Any]:
        verified_count = len(decisions)
        correct_count = sum(1 for decision in decisions if decision.get("is_correct") is True)
        by_category = _by_category(decisions)
        factor_strengths = _factor_strengths(decisions)
        strongest_factor = factor_strengths[0]["factor"] if factor_strengths else None
        top_category = _top_category(by_category)
        accuracy = _ratio(correct_count, verified_count)
        return {
            "trader_id": _normalize_trader(trader_id),
            "verified_count": verified_count,
            "correct_count": correct_count,
            "accuracy": accuracy,
            "by_category": by_category,
            "factor_strengths": factor_strengths,
            "top_category": top_category,
            "strongest_factor": strongest_factor,
            "edge_summary": _edge_summary(_normalize_trader(trader_id), verified_count, accuracy, strongest_factor, top_category),
            "source": "graphstore",
        }


def _valid_decision(decision: dict[str, Any]) -> bool:
    return (
        str(decision.get("category") or "") in VALID_CATEGORIES
        and str(decision.get("recommended_action") or "") in VALID_ACTIONS
        and str(decision.get("actual_action") or "") in VALID_ACTIONS
    )


def _decision_trader(decision: dict[str, Any]) -> str:
    value = decision.get("entity_id")
    if not value:
        metadata = decision.get("metadata") if isinstance(decision.get("metadata"), dict) else {}
        value = metadata.get("entity_id") or metadata.get("trader_id")
    return _normalize_trader(value)


def _normalize_trader(value: Any) -> str:
    text = str(value or "").strip()
    return text or "default"


def _by_category(decisions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for decision in decisions:
        grouped[str(decision.get("category"))].append(decision)
    result: dict[str, dict[str, Any]] = {}
    for category in sorted(VALID_CATEGORIES):
        rows = grouped.get(category, [])
        verified = len(rows)
        correct = sum(1 for row in rows if row.get("is_correct") is True)
        result[category] = {
            "verified_count": verified,
            "accuracy": _ratio(correct, verified),
            "strong_execution_rate": _ratio(
                sum(1 for row in rows if row.get("recommended_action") == STRONG_ACTION),
                verified,
            ),
        }
    return result


def _factor_strengths(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    totals = {factor: 0.0 for factor in FACTOR_NAMES}
    counts = {factor: 0 for factor in FACTOR_NAMES}
    for decision in decisions:
        if decision.get("recommended_action") != STRONG_ACTION:
            continue
        factors = _decision_factors(decision)
        for factor in FACTOR_NAMES:
            value = _finite_float(factors.get(factor))
            if value is None:
                continue
            totals[factor] += value
            counts[factor] += 1
    rows = [
        {"factor": factor, "score": round(totals[factor] / counts[factor], 4)}
        for factor in FACTOR_NAMES
        if counts[factor] > 0
    ]
    return sorted(rows, key=lambda row: (-row["score"], row["factor"]))


def _decision_factors(decision: dict[str, Any]) -> dict[str, Any]:
    factors = decision.get("factors") if isinstance(decision.get("factors"), dict) else {}
    metadata = factors.get("metadata") if isinstance(factors.get("metadata"), dict) else {}
    scored = metadata.get("scored_factors") if isinstance(metadata.get("scored_factors"), dict) else {}
    vector = decision.get("factor_vector") if isinstance(decision.get("factor_vector"), list) else []
    result: dict[str, Any] = {}
    for index, factor in enumerate(FACTOR_NAMES):
        value = factors.get(factor)
        if value is None:
            value = scored.get(factor)
        if value is None and index < len(vector):
            value = vector[index]
        if _finite_float(value) is not None:
            result[factor] = _finite_float(value)
    return result


def _top_category(by_category: dict[str, dict[str, Any]]) -> str | None:
    rows = [
        (category, stats)
        for category, stats in by_category.items()
        if int(stats.get("verified_count") or 0) > 0
    ]
    if not rows:
        return None
    return sorted(rows, key=lambda item: (-float(item[1].get("accuracy") or 0.0), item[0]))[0][0]


def _edge_summary(
    trader_id: str,
    verified_count: int,
    accuracy: float,
    strongest_factor: str | None,
    top_category: str | None,
) -> str:
    if verified_count <= 0:
        return f"{trader_id} has no verified Trading execution outcomes yet."
    parts = [f"{trader_id} execution accuracy is {accuracy:.0%} across {verified_count} verified outcomes"]
    if top_category:
        parts.append(f"strongest category: {top_category}")
    if strongest_factor:
        parts.append(f"strongest execution factor: {strongest_factor}")
    return "; ".join(parts) + "."


def _execution_recommendations(profile: dict[str, Any]) -> list[str]:
    if int(profile.get("verified_count") or 0) <= 0:
        return ["Verify execution outcomes to identify trader-specific strengths."]
    recommendations = []
    if profile.get("top_category"):
        recommendations.append(f"Observation: {profile['top_category']} contains repeatable execution-quality patterns.")
    if profile.get("strongest_factor"):
        recommendations.append(f"Observation: {profile['strongest_factor']} is the strongest post-trade review signal.")
    return recommendations[:3]


def _leader(profiles: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not profiles:
        return None
    rows = [profile for profile in profiles if int(profile.get("verified_count") or 0) > 0]
    if not rows:
        return None
    return sorted(rows, key=lambda row: (-float(row.get("accuracy") or 0.0), row["trader_id"]))[0]


def _complementary_edges(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for source in profiles:
        source_factor = source.get("strongest_factor")
        if not source_factor:
            continue
        for target in profiles:
            if source["trader_id"] == target["trader_id"]:
                continue
            target_factor = target.get("strongest_factor")
            if target_factor and target_factor == source_factor:
                continue
            rows.append({
                "source_trader": source["trader_id"],
                "target_trader": target["trader_id"],
                "shared_focus": source_factor,
                "message": (
                    f"Compare {source['trader_id']}'s {source_factor} review pattern with "
                    f"{target['trader_id']}'s execution checklist."
                ),
            })
    return rows[:5]


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 4)


def _finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
