"""Pure compute helpers for Trading materialized tab-state keys."""

from __future__ import annotations

import math
from dataclasses import asdict, is_dataclass
from typing import Any, Callable

import numpy as np

from app.evolution import get_trading_variants
from app.routers.analytics import _verified_decisions
from app.routers.journal import _aggregate, _group_key, _journal_records
from app.routers.promotion_router import _STATE_STORE, _conservation_status
from app.services.promotion_engine import PromotionEngine
from copilot_sdk.generators.archetype import ArchetypeGenerator
from copilot_sdk.scoring.evolution import ScorerEvolution
from copilot_sdk.scoring.presets.trading import TradingPreset


GraphStoreFactory = Callable[[], Any]


def compute_all_decisions(graph_store_factory: GraphStoreFactory, limit: int = 50) -> list[dict[str, Any]]:
    store = graph_store_factory()
    get_all = getattr(store, "get_all_decisions", None)
    get_decisions = getattr(store, "get_decisions", None)
    if callable(get_all):
        rows = get_all("trading")
    elif callable(get_decisions):
        rows = get_decisions("trading", limit=limit)
    else:
        rows = []
    return [json_safe(dict(row)) for row in list(rows)[:limit]]


def compute_verified_decisions(graph_store_factory: GraphStoreFactory) -> list[dict[str, Any]]:
    return _verified_decisions(graph_store_factory, "trading")


def compute_history_summary(graph_store_factory: GraphStoreFactory) -> dict[str, Any]:
    rows = compute_all_decisions(graph_store_factory, limit=50)
    return {
        "decisions": rows,
        "total": count_decisions(graph_store_factory()),
        "bounded": True,
    }


def compute_decisions_summary(graph_store_factory: GraphStoreFactory) -> dict[str, Any]:
    rows = compute_all_decisions(graph_store_factory, limit=50)
    return {"decisions": rows, "total": len(rows), "limit": 50}


def compute_accuracy_summary(graph_store_factory: GraphStoreFactory) -> dict[str, Any]:
    rows = get_accuracy_source_rows(graph_store_factory)
    return select_accuracy_summary(rows)


def get_accuracy_source_rows(graph_store_factory: GraphStoreFactory) -> list[dict[str, Any]]:
    return compute_verified_decisions(graph_store_factory)


def select_accuracy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, int]] = {}
    for row in rows:
        category = str(row.get("category") or "uncategorized")
        bucket = grouped.setdefault(category, {"total": 0, "correct": 0})
        bucket["total"] += 1
        if row.get("is_correct") is True:
            bucket["correct"] += 1
    categories = [
        {
            "category": category,
            "accuracy": round(bucket["correct"] / bucket["total"], 4) if bucket["total"] else 0.0,
            **bucket,
        }
        for category, bucket in sorted(grouped.items())
    ]
    return {"categories": categories, "overall_verified": len(rows)}


def compute_archetypes_summary() -> dict[str, Any]:
    return select_archetypes_summary(get_archetype_presets())


def get_archetype_presets() -> list[dict[str, Any]]:
    items = []
    for name in ["financial_services", *ArchetypeGenerator.list_archetypes()]:
        if name != "financial_services":
            continue
        try:
            preset = ArchetypeGenerator.from_archetype(name)
        except ValueError:
            continue
        items.append(
            {
                "name": name,
                "domain": "trading",
                "description": "Trading and financial services bootstrap template. Generated bootstrap centroids for portfolio, execution, and market-regime decisions.",
                "expected_initial_accuracy": float(preset.expected_initial_accuracy),
                "categories": list(preset.shape.category_names),
                "actions": list(preset.shape.action_names),
                "factors": list(preset.shape.factor_names),
            }
        )
    return items


def select_archetypes_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"items": items}


def compute_counterfactual_default(scorer: Any) -> dict[str, Any]:
    return select_counterfactual_default(get_counterfactual_default_scores(scorer))


def get_counterfactual_default_scores(scorer: Any) -> dict[str, Any]:
    base = {
        "signal_alignment": 0.8,
        "market_regime": 0.7,
        "position_sizing": 0.6,
        "timing_quality": 0.6,
        "risk_reward_actual": 0.7,
        "emotional_indicator": 0.5,
    }
    perturbed = {**base, "signal_alignment": 0.2}
    base_result = scorer.score_read_only(base, "trend_following")
    perturbed_result = scorer.score_read_only(perturbed, "trend_following")
    base_score = float(getattr(base_result, "confidence", 0.0))
    perturbed_score = float(getattr(perturbed_result, "confidence", 0.0))
    return {
        "base_score": base_score,
        "perturbed_score": perturbed_score,
        "base_action": getattr(base_result, "action", None),
        "perturbed_action": getattr(perturbed_result, "action", None),
    }


def select_counterfactual_default(raw: dict[str, Any]) -> dict[str, Any]:
    base_score = float(raw.get("base_score") or 0.0)
    perturbed_score = float(raw.get("perturbed_score") or 0.0)
    return {
        "base_score": round(base_score, 4),
        "perturbed_score": round(perturbed_score, 4),
        "delta": round(perturbed_score - base_score, 4),
        "perturbed_factor": "signal_alignment",
        "base_action": raw.get("base_action"),
        "perturbed_action": raw.get("perturbed_action"),
        "provenance": "learned",
    }


def compute_evolution_summary(rejection_summary: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    return select_evolution_summary(get_evolution_summary_source(rejection_summary))


def get_evolution_summary_source(rejection_summary: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    parameter_service = ScorerEvolution("trading")
    variants = get_trading_variants()
    return {
        "variants": variants,
        "parameter_log": parameter_service.evolution_log(),
        "active_adjustments": parameter_service.active_adjustments(),
        "bounds": parameter_service.bounds_dict(),
        "rejection_summary": rejection_summary(),
    }


def select_evolution_summary(raw: dict[str, Any]) -> dict[str, Any]:
    variants = list(raw.get("variants") or [])
    parameter_entries = [{"kind": "parameter", **entry} for entry in list(raw.get("parameter_log") or [])]
    variant_entries = [{"kind": "variant", **entry} for entry in variants]
    active_variant = next((entry for entry in variants if str(entry.get("status", "")).lower() == "promoted"), None)
    return {
        "variants": variants,
        "log": json_safe(variant_entries + parameter_entries),
        "active": {
            "variant": active_variant,
            "parameter_adjustments": raw.get("active_adjustments"),
            "conservation_state": "GREEN",
            "bounds": raw.get("bounds"),
        },
        "proposals": {
            "proposals": [],
            "provenance": "demo",
            "note": "Based on synthetic evidence. Real proposals require accumulated verified decisions.",
            "conservation_state": "GREEN",
        },
        "rejection_summary": raw.get("rejection_summary"),
        "promoted": [],
    }


def compute_promotion_dashboard(graph_store_factory: GraphStoreFactory) -> list[dict[str, Any]]:
    preset = TradingPreset()
    return PromotionEngine(
        graph_store_factory(),
        preset,
        _conservation_status(graph_store_factory, "trading"),
        state_store=_STATE_STORE,
        domain="trading",
    ).dashboard()


def compute_journal_trades_summary(graph_store_factory: GraphStoreFactory) -> dict[str, Any]:
    rows = _journal_records(graph_store_factory, "trading")
    paged = rows[:50]
    return {
        "trades": json_safe(paged),
        "count": len(paged),
        "total": len(rows),
        "filters_applied": {},
        "aggregate": json_safe(_aggregate(rows)),
    }


def compute_journal_analytics(graph_store_factory: GraphStoreFactory, group_by: str) -> dict[str, Any]:
    rows = get_journal_analytics_rows(graph_store_factory, group_by)
    return select_journal_analytics(rows, group_by)


def get_journal_analytics_rows(graph_store_factory: GraphStoreFactory, group_by: str) -> list[dict[str, Any]]:
    rows = _journal_records(graph_store_factory, "trading")
    if group_by == "subcategory":
        rows = [trade for trade in rows if trade.get("category") == "event_driven"]
    return rows


def select_journal_analytics(rows: list[dict[str, Any]], group_by: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for trade in rows:
        key = _group_key(trade, group_by)
        groups.setdefault(key, []).append(trade)
    return {
        "group_by": group_by,
        "groups": [
            {"key": key, "count": len(items), **json_safe(_aggregate(items))}
            for key, items in sorted(groups.items(), key=lambda item: item[0])
        ],
        "total": len(rows),
    }


def count_decisions(store: Any) -> int:
    count = getattr(store, "count_decisions", None)
    if callable(count):
        try:
            return int(count("trading"))
        except Exception:
            return 0
    return 0


def grouped_accuracy(field: str, decisions: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, int]] = {}
    for decision in decisions:
        key = str(decision.get(field) or "uncategorized")
        bucket = grouped.setdefault(key, {"total": 0, "correct": 0})
        bucket["total"] += 1
        if decision.get("is_correct") is True:
            bucket["correct"] += 1
    rows = [
        {
            field: key,
            "total": bucket["total"],
            "correct": bucket["correct"],
            "accuracy": round(bucket["correct"] / bucket["total"], 4) if bucket["total"] else 0.0,
        }
        for key, bucket in sorted(grouped.items())
    ]
    return {"groups": rows, "total_groups": len(rows)}


def safe_call(func: Callable[[], Any], default: Any) -> Any:
    try:
        return func()
    except Exception:
        return default


def json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value
