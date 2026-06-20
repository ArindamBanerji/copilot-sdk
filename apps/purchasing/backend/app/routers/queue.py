"""Purchasing smart order queue endpoint."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable

from fastapi import APIRouter, HTTPException

from app.connectors.mock_qbo import MockQBOConnector
from app.data_helpers import assert_no_sample_in_metric
from app.factors import ALL_FACTOR_NAMES, compute_factors
from app.routers.spend_router import SCRAPED_EXTERNAL_PROVENANCE, qbo_bills_for_spend
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer


DOMAIN = "purchasing"
GraphStoreFactory = Callable[[], Any]
ScorerFactory = Callable[[], Any]
_PRESET = PurchasingPreset()
_FACTOR_POLARITIES = dict(getattr(_PRESET, "factor_polarities", {}) or {})
_SCORER: Any | None = None


def create_queue_router(
    graph_store_factory: GraphStoreFactory | None = None,
    scorer_factory: ScorerFactory | None = None,
    connector: Any | None = None,
) -> APIRouter:
    qbo_connector = connector or MockQBOConnector()
    router = APIRouter(prefix="/api/purchasing", tags=["purchasing-queue"])

    @router.get("/queue")
    def order_queue(limit: int | None = None) -> dict[str, Any]:
        orders = _orders(qbo_connector)
        max_amount = _max_amount(orders)
        scorer = _queue_scorer(scorer_factory)
        rows = [_recommendation(order, scorer=scorer, max_amount=max_amount) for order in orders]
        rows = [row for row in rows if row is not None]
        rows.sort(key=lambda item: item["priority_score"], reverse=True)
        if limit is not None and limit >= 0:
            rows = rows[:limit]
        return {
            "queue": rows,
            "count": len(rows),
            "conservation_status": _conservation_status(graph_store_factory),
            "source": "quickbooks_online",
        }

    @router.get("/queue/{order_id}")
    def order_queue_detail(order_id: str) -> dict[str, Any]:
        orders = _orders(qbo_connector)
        max_amount = _max_amount(orders)
        scorer = _queue_scorer(scorer_factory)
        for order in orders:
            if str(order.get("order_id") or "") != order_id:
                continue
            row = _recommendation(order, scorer=scorer, max_amount=max_amount)
            if row is not None:
                return row
        raise HTTPException(status_code=404, detail=f"Unknown queued order: {order_id}")

    return router


def _orders(connector: Any | None = None) -> list[dict[str, Any]]:
    try:
        rows = qbo_bills_for_spend(connector or MockQBOConnector())
    except (FileNotFoundError, OSError):
        return []
    orders = [order for order in rows if isinstance(order, dict)]
    assert_no_sample_in_metric(orders, "order_queue")
    return orders


def _recommendation(
    order: dict[str, Any],
    scorer: Any | None = None,
    max_amount: float | None = None,
) -> dict[str, Any] | None:
    factors = _merged_factors(order)
    items = order.get("items") if isinstance(order.get("items"), list) else []
    if not items:
        return None
    primary_item = items[0] if isinstance(items[0], dict) else {}
    category = _category(order.get("category"))
    score = _score_read_only(factors, category, scorer)
    confidence = _coerce_factor(score.get("confidence"))
    total_amount = _order_amount(order)
    impact_denominator = max_amount if max_amount and max_amount > 0 else total_amount
    financial_impact = _coerce_factor(total_amount / impact_denominator) if impact_denominator else 0.0
    stockout_risk = _stockout_risk(order, factors)
    priority_score = _priority_score(
        stockout_risk=stockout_risk,
        confidence=confidence,
        financial_impact=financial_impact,
    )
    return {
        "order_id": order.get("order_id"),
        "what_to_order": primary_item.get("name") or primary_item.get("item_id"),
        "how_much": primary_item.get("quantity"),
        "unit": primary_item.get("unit"),
        "from_whom": order.get("supplier_name") or order.get("supplier_id"),
        "supplier_id": order.get("supplier_id"),
        "supplier_name": order.get("supplier_name") or order.get("supplier_id"),
        "category": category,
        "total_amount": round(total_amount, 2),
        "recommended_action": score["recommended_action"],
        "confidence": round(confidence, 6),
        "priority_score": round(priority_score, 6),
        "top_factors": _top_factors(factors),
        "stockout_risk": round(stockout_risk, 6),
        "financial_impact": round(financial_impact, 6),
        "aging_days": _aging_days(order),
        "factors": factors,
        "provenance": order.get("provenance") or SCRAPED_EXTERNAL_PROVENANCE,
        "data_source": "quickbooks_online",
    }


def _merged_factors(order: dict[str, Any]) -> dict[str, float]:
    explicit_factors = order.get("factors") if isinstance(order.get("factors"), dict) else {}
    computed = compute_factors(_factor_context(order))
    return {**computed, **_explicit_factor_overrides(order, explicit_factors)}


def _factor_context(order: dict[str, Any]) -> dict[str, Any]:
    outcome = order.get("outcome") if isinstance(order.get("outcome"), dict) else {}
    context = {
        "forecast_demand": order.get("forecast_demand") or order.get("expected_demand"),
        "par_level": order.get("par_level"),
        "day_of_week": _day_index(order.get("day_of_week")),
        "weather_score": order.get("weather_score") or order.get("weather_forecast"),
        "weather": order.get("weather"),
        "event_flag": order.get("event_flag"),
        "event_covers": order.get("event_covers"),
        "normal_covers": order.get("normal_covers"),
        "waste_pct": order.get("waste_pct") or order.get("historical_waste") or outcome.get("waste_pct"),
        "lead_time_days": order.get("lead_time_days") or order.get("supplier_lead_time"),
        "price_change_count": order.get("price_change_count"),
        "months_tracked": order.get("months_tracked"),
    }
    return {key: value for key, value in context.items() if value is not None}


def _explicit_factor_overrides(order: dict[str, Any], explicit_factors: dict[str, Any]) -> dict[str, float]:
    overrides: dict[str, float] = {}
    for name in ALL_FACTOR_NAMES:
        if name == "day_of_week" and order.get("day_of_week_factor") is not None:
            raw = order.get("day_of_week_factor")
        elif name in explicit_factors:
            raw = explicit_factors.get(name)
        elif name in order:
            raw = order.get(name)
        else:
            continue
        value = _finite_factor(raw)
        if value is not None:
            overrides[name] = value
    return overrides


def _day_index(value: Any) -> Any:
    if isinstance(value, str):
        lookup = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        return lookup.get(value.strip().lower())
    return value


def _finite_factor(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if 0.0 <= number <= 1.0:
        return number
    return None


def _queue_scorer(scorer_factory: ScorerFactory | None = None) -> Any | None:
    global _SCORER
    if scorer_factory is not None:
        try:
            return scorer_factory()
        except Exception:
            return None
    if _SCORER is None:
        try:
            _SCORER = CompoundingScorer.from_preset(DOMAIN, db_path=":memory:")
        except Exception:
            return None
    return _SCORER


def _score_read_only(factors: dict[str, float], category: str, scorer: Any | None = None) -> dict[str, Any]:
    active_scorer = scorer if scorer is not None else _queue_scorer()
    if active_scorer is not None and callable(getattr(active_scorer, "score_read_only", None)):
        try:
            result = active_scorer.score_read_only(factors=factors, category=category)
            return {
                "recommended_action": str(getattr(result, "action", "order_as_planned")),
                "confidence": _coerce_factor(getattr(result, "confidence", 0.5)),
            }
        except Exception:
            pass
    return {"recommended_action": "order_as_planned", "confidence": 0.5}


def _priority_score(*, stockout_risk: float, confidence: float, financial_impact: float) -> float:
    return _coerce_factor((stockout_risk * 0.4) + ((1.0 - confidence) * 0.3) + (financial_impact * 0.3))


def _stockout_risk(order: dict[str, Any], factors: dict[str, float]) -> float:
    par_compliance = _finite_factor(order.get("par_compliance"))
    if par_compliance is None:
        explicit = order.get("factors") if isinstance(order.get("factors"), dict) else {}
        par_compliance = _finite_factor(explicit.get("par_compliance"))
    if par_compliance is not None:
        return 1.0 - par_compliance

    current_stock = _finite_number(order.get("current_stock") or order.get("on_hand"))
    par_level = _finite_number(order.get("par_level"))
    if current_stock is not None and par_level and par_level > 0:
        return 1.0 - _coerce_factor(current_stock / par_level)

    outcome = order.get("outcome") if isinstance(order.get("outcome"), dict) else {}
    if outcome.get("stockout") is True:
        return 1.0
    return _coerce_factor(factors.get("expected_demand"))


def _top_factors(factors: dict[str, float], limit: int = 3) -> list[dict[str, Any]]:
    ranked = sorted(
        ((name, _coerce_factor(value)) for name, value in factors.items() if name in ALL_FACTOR_NAMES),
        key=lambda item: abs(item[1] - 0.5),
        reverse=True,
    )
    return [
        {
            "name": name,
            "value": round(value, 6),
            "interpretation": _polarity_quality(name, value),
        }
        for name, value in ranked[:limit]
    ]


def _polarity_quality(name: str, value: float) -> str:
    polarity = _FACTOR_POLARITIES.get(name, 0)
    if polarity > 0:
        if value >= 0.65:
            return "favorable driver"
        if value <= 0.35:
            return "low support"
        return "neutral support"
    if polarity < 0:
        if value <= 0.35:
            return "favorable low risk"
        if value >= 0.65:
            return "risk pressure"
        return "neutral risk"
    if value >= 0.65:
        return "strong context signal"
    if value <= 0.35:
        return "soft context signal"
    return "neutral context"


def _order_amount(order: dict[str, Any]) -> float:
    for key in ("total_amount", "total_value", "amount", "total_spend"):
        value = _finite_number(order.get(key))
        if value is not None:
            return max(0.0, value)
    total = 0.0
    items = order.get("items") if isinstance(order.get("items"), list) else []
    for item in items:
        if not isinstance(item, dict):
            continue
        quantity = _finite_number(item.get("quantity") or item.get("qty")) or 0.0
        unit_price = _finite_number(item.get("unit_price") or item.get("price")) or 0.0
        total += quantity * unit_price
    return max(0.0, total)


def _max_amount(orders: list[dict[str, Any]]) -> float:
    amounts = [_order_amount(order) for order in orders]
    return max(amounts, default=0.0)


def _aging_days(order: dict[str, Any]) -> int:
    for key in ("order_date", "created_at", "createdAt", "date"):
        parsed = _parse_date(order.get(key))
        if parsed is not None:
            return max(0, (date.today() - parsed).days)
    return 0


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _category(value: Any) -> str:
    category = str(value or "protein")
    if category in _PRESET.shape.category_names:
        return category
    return "protein"


def _finite_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _conservation_status(graph_store_factory: GraphStoreFactory | None) -> dict[str, Any]:
    if graph_store_factory is None:
        return {"status": "BOOTSTRAP", "source": "not_configured"}
    try:
        store = graph_store_factory()
        verified = int(_call_count(store, "count_verified"))
        correct = int(_call_count(store, "count_correct"))
    except Exception:
        return {"status": "UNKNOWN", "source": "graph_store_error"}
    if verified <= 0:
        return {"status": "BOOTSTRAP", "verified_count": 0, "correct_count": 0, "source": "graphstore"}
    accuracy = correct / verified
    return {
        "status": "GREEN" if accuracy >= 0.5 else "AMBER",
        "verified_count": verified,
        "correct_count": correct,
        "accuracy": round(accuracy, 4),
        "source": "graphstore",
    }


def _call_count(store: Any, method_name: str) -> int:
    method = getattr(store, method_name, None)
    if not callable(method):
        return 0
    return int(method(DOMAIN))


def _coerce_factor(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.5
    return max(0.0, min(number, 1.0))
