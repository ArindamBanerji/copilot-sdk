"""Compatibility endpoints for the Purchasing frontend API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query


router = APIRouter(prefix="/api/purchasing", tags=["purchasing-completeness"])

_COMMODITY_PRICES: dict[str, list[dict[str, Any]]] = {
    "produce": [
        {
            "date": "2026-10-17",
            "item": "Produce basket",
            "price": 3.42,
            "unit": "lb",
        }
    ],
}

_PAR_RECOMMENDATIONS: dict[str, dict[str, Any]] = {
    "produce": {
        "item_name": "Produce basket",
        "category": "produce",
        "current_par": 24.0,
        "recommended_par": 22.0,
        "avg_daily_usage": 18.0,
        "usage_std": 2.5,
        "waste_rate": 0.08,
        "service_level": 0.95,
        "weekly_savings_estimate": 28.0,
        "confidence": "moderate",
        "seasonal_adjustment": None,
        "data_days": 30,
        "provenance": "mock",
    },
}

_SUPPLIER_SCORECARDS: dict[str, dict[str, Any]] = {
    "SUP-001": {
        "supplier_id": "SUP-001",
        "supplier_name": "Fresh Foods Distribution",
        "tier": "A",
        "overall_score": 92.0,
        "reliability_pct": 96.0,
        "price_trend_pct": -1.5,
        "delivery_performance": 94.0,
        "exception_rate": 0.02,
        "decision_count": 48,
        "trend": "stable",
        "summary": "Reliable preferred supplier.",
        "provenance": "mock",
    },
}


@router.get("/commodity-prices/{category}")
def commodity_prices(category: str) -> dict[str, Any]:
    prices = _COMMODITY_PRICES.get(category.casefold(), [])
    return {
        "value": prices,
        "source": "mock",
        "label": category,
        "as_of": "2026-10-17",
    }


@router.get("/par-recommendations")
def par_recommendations(
    category: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    if category is None:
        return list(_PAR_RECOMMENDATIONS.values())
    recommendation = _PAR_RECOMMENDATIONS.get(category.casefold())
    return [recommendation] if recommendation is not None else []


@router.get("/supplier-scorecard/{supplier_id}")
def supplier_scorecard(supplier_id: str) -> dict[str, Any]:
    scorecard = _SUPPLIER_SCORECARDS.get(supplier_id.upper())
    if scorecard is not None:
        return scorecard
    return {
        "supplier_id": supplier_id,
        "supplier_name": "",
        "tier": "C",
        "overall_score": 0.0,
        "reliability_pct": 0.0,
        "price_trend_pct": 0.0,
        "delivery_performance": 0.0,
        "exception_rate": 0.0,
        "decision_count": 0,
        "trend": "stable",
        "summary": "No supplier data available.",
        "provenance": "mock",
    }
