"""Predictive par planning for Purchasing."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from typing import Any

from app.services.par_optimizer import ParLevelOptimizer
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset


DAY_MULTIPLIERS = {
    "Monday": 0.80,
    "Tuesday": 0.85,
    "Wednesday": 0.90,
    "Thursday": 1.00,
    "Friday": 1.40,
    "Saturday": 1.50,
    "Sunday": 1.20,
}


@dataclass
class PredictiveParResult:
    item: str
    category: str
    date: str
    day: str
    base_par: float
    adjusted_par: float
    confidence: str
    dollar_impact: float
    explanation: str
    breakdown: list[str]
    provenance: str = "demo"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PredictivePar:
    """Layer day, weather, cover, and event signals on P73 base par."""

    def __init__(self, optimizer: ParLevelOptimizer | None = None) -> None:
        self.optimizer = optimizer or ParLevelOptimizer()

    def predict(
        self,
        item: str,
        category: str,
        target_date: date | str,
        base_par: float,
        conservation_status: str = "UNKNOWN",
        weather: dict[str, Any] | None = None,
        cover_forecast: float | None = None,
        event: bool = False,
    ) -> PredictiveParResult:
        day = _to_date(target_date)
        day_name = day.strftime("%A")
        base = max(float(base_par or 0), 0.0)
        if str(conservation_status or "").upper() != "GREEN":
            return PredictiveParResult(
                item=str(item),
                category=str(category),
                date=day.isoformat(),
                day=day_name,
                base_par=round(base, 2),
                adjusted_par=round(base, 2),
                confidence="blocked",
                dollar_impact=0.0,
                explanation="Smart par waits until this category is GREEN.",
                breakdown=["Manager review stays on until local learning is GREEN."],
            )
        day_mult = DAY_MULTIPLIERS.get(day_name, 1.0)
        weather_mult, weather_text = _weather_multiplier(category, weather)
        cover_mult = _cover_multiplier(cover_forecast)
        event_mult = 1.3 if event else 1.0

        raw = base * day_mult * weather_mult * cover_mult * event_mult
        adjusted = min(max(raw, base * 0.5), base * 2.0) if base else 0.0
        confidence = "high" if sum([weather is not None, cover_forecast is not None, event]) >= 2 else "medium"
        weekday_text = _change_text(day_mult, "weekend") if day_mult >= 1.2 else _change_text(day_mult, "slow day")
        breakdown = [f"{day_name}: base {base:g} lbs {weekday_text}"]
        if weather_text:
            breakdown.append(weather_text)
        if cover_forecast is not None:
            breakdown.append(_change_text(cover_mult, "cover count"))
        if event:
            breakdown.append("event prep adds 30% cushion")
        return PredictiveParResult(
            item=str(item),
            category=str(category),
            date=day.isoformat(),
            day=day_name,
            base_par=round(base, 2),
            adjusted_par=round(adjusted, 2),
            confidence=confidence,
            dollar_impact=180.0 if str(category).lower() == "protein" else 45.0,
            explanation=f"{day_name} needs {round(adjusted, 1):g} lbs instead of a flat {base:g} lbs.",
            breakdown=breakdown,
        )

    def predict_week(
        self,
        items: list[dict[str, Any]],
        weather_forecast: list[dict[str, Any]] | None = None,
        covers: dict[str, float] | None = None,
        start_date: date | str | None = None,
    ) -> dict[str, Any]:
        start = _to_date(start_date or date(2026, 6, 22))
        forecast_by_day = {
            _to_date(row.get("date", start)).isoformat(): row
            for row in (weather_forecast or [])
            if isinstance(row, dict)
        }
        rows = []
        for offset in range(7):
            day = start + timedelta(days=offset)
            day_key = day.isoformat()
            for item in items:
                rows.append(
                    self.predict(
                        item=str(item.get("item") or item.get("name") or "salmon"),
                        category=str(item.get("category") or "protein"),
                        target_date=day,
                        base_par=float(item.get("base_par") or item.get("current_par") or 40),
                        conservation_status=str(item.get("conservation_status") or "UNKNOWN"),
                        weather=forecast_by_day.get(day_key),
                        cover_forecast=(covers or {}).get(day_key),
                        event=bool(item.get("event")),
                    ).to_dict()
                )
        return {
            "items": rows,
            "provenance": "demo",
            "dollar_impact": 180.0,
            "summary": "Two-tier par saves about $180/week in protein waste.",
        }

    def base_from_optimizer(self, item: str, category: str, orders: list[dict[str, Any]]) -> float:
        try:
            rec = self.optimizer.recommend(item, category, orders, current_par=40, unit_cost=8)
            return rec.recommended_par
        except Exception:
            return 40.0


def demo_par_items() -> list[dict[str, Any]]:
    preset_categories = list(PurchasingPreset().shape.category_names)
    protein = "protein" if "protein" in preset_categories else preset_categories[0]
    produce = "produce" if "produce" in preset_categories else preset_categories[min(1, len(preset_categories) - 1)]
    return [
        {"item": "salmon", "category": protein, "base_par": 40},
        {"item": "romaine", "category": produce, "base_par": 25},
    ]


def _weather_multiplier(category: str, weather: dict[str, Any] | None) -> tuple[float, str | None]:
    if not weather:
        return 1.0, None
    condition = str(weather.get("condition") or weather.get("type") or "").lower()
    if "storm" in condition or float(weather.get("rain", 0) or 0) > 1:
        if str(category).lower() == "produce":
            return 0.85, "storm forecast trims produce by 15%"
        return 0.95, "storm forecast trims ordering by 5%"
    if "heat" in condition and str(category).lower() == "dairy":
        return 0.90, "hot weather trims dairy by 10%"
    return 1.0, None


def _cover_multiplier(covers: float | None) -> float:
    if covers is None:
        return 1.0
    return min(max(float(covers) / 100.0, 0.75), 1.5)


def _change_text(multiplier: float, label: str) -> str:
    change = round((multiplier - 1.0) * 100)
    if change >= 0:
        return f"+ {change}% {label}"
    return f"- {abs(change)}% {label}"


def _to_date(value: date | str) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return date.today()
