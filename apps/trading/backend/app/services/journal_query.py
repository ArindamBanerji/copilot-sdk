"""Rule-based natural language queries for the Trading journal."""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any


CATEGORIES = ("trend_following", "mean_reversion", "event_driven", "income_strategy", "scalp_intraday")
ACTIONS = ("strong_execution", "partial_execution", "poor_execution", "skip_recommended")
REGIMES = ("trending", "ranging", "volatile")
MONTHS = {name.lower(): index for index, name in enumerate(calendar.month_name) if name}


@dataclass(frozen=True)
class FactorCondition:
    factor: str
    operator: str
    value: float


class JournalQueryService:
    """Deterministic parser and executor for journal questions."""

    def __init__(self, today: date | None = None) -> None:
        self._today = today or date.today()

    def query(self, question: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
        query_text = str(question or "").strip()
        parsed, warnings = self.parse(query_text)
        results = self.filter_trades(trades, parsed)
        results = self._sort_results(results, parsed)
        return {
            "query": query_text,
            "parsed": self._public_parsed(parsed),
            "results": results,
            "count": len(results),
            "summary": self._summary(parsed, len(results), warnings),
            "warnings": warnings,
        }

    def parse(self, question: str) -> tuple[dict[str, Any], list[str]]:
        lowered = _normalize(question)
        parsed: dict[str, Any] = {}
        warnings: list[str] = []
        if not lowered:
            return parsed, warnings

        category = _match_known(lowered, CATEGORIES)
        if category:
            parsed["category"] = category
        action = _match_known(lowered, ACTIONS)
        if action:
            parsed["action"] = action
        regime = _match_known(lowered, REGIMES)
        if regime:
            parsed["regime"] = regime

        date_range, label = self._date_range(lowered)
        if date_range:
            parsed["date_range"] = date_range
            parsed["period_label"] = label

        factor = self._factor_condition(lowered)
        if factor:
            parsed["factor"] = factor
        if "high confidence" in lowered:
            parsed["confidence_min"] = 0.8

        performance = self._performance_sort(lowered)
        if performance:
            parsed["performance"] = performance

        if not parsed:
            warnings.append("No journal filters matched; showing all trades.")
        return parsed, warnings

    def filter_trades(self, trades: list[dict[str, Any]], parsed: dict[str, Any]) -> list[dict[str, Any]]:
        output = [dict(trade) for trade in trades if isinstance(trade, dict)]
        if parsed.get("category"):
            output = [trade for trade in output if _text(trade.get("category")) == parsed["category"]]
        if parsed.get("action"):
            output = [trade for trade in output if _text(trade.get("action") or trade.get("direction")) == parsed["action"]]
        if parsed.get("regime"):
            output = [trade for trade in output if _text(trade.get("regime")) == parsed["regime"]]
        if parsed.get("date_range"):
            start, end = parsed["date_range"]
            output = [
                trade for trade in output
                if (entry := _entry_date(trade)) is not None and start <= entry <= end
            ]
        if parsed.get("factor"):
            output = [trade for trade in output if self._matches_factor(trade, parsed["factor"])]
        if parsed.get("confidence_min") is not None:
            minimum = float(parsed["confidence_min"])
            output = [trade for trade in output if _number(trade.get("confidence")) is not None and _number(trade.get("confidence")) >= minimum]
        return output

    def _date_range(self, lowered: str) -> tuple[tuple[date, date] | None, str | None]:
        if "last quarter" in lowered:
            quarter = (self._today.month - 1) // 3 + 1
            year = self._today.year
            previous = quarter - 1
            if previous == 0:
                previous = 4
                year -= 1
            return _quarter_range(year, previous), f"Q{previous} {year}"
        if "this month" in lowered:
            start = date(self._today.year, self._today.month, 1)
            end = date(self._today.year, self._today.month, calendar.monthrange(self._today.year, self._today.month)[1])
            return (start, end), start.strftime("%B %Y")
        if "last 30 days" in lowered:
            return (self._today - timedelta(days=30), self._today), "last 30 days"
        if "this year" in lowered:
            return (date(self._today.year, 1, 1), date(self._today.year, 12, 31)), str(self._today.year)

        match = re.search(r"\b(20\d{2})\s*q([1-4])\b", lowered)
        if match:
            year = int(match.group(1))
            quarter = int(match.group(2))
            return _quarter_range(year, quarter), f"Q{quarter} {year}"

        for month, index in MONTHS.items():
            if re.search(rf"\b{re.escape(month)}\b", lowered):
                start = date(self._today.year, index, 1)
                end = date(self._today.year, index, calendar.monthrange(self._today.year, index)[1])
                return (start, end), start.strftime("%B %Y")
        return None, None

    def _factor_condition(self, lowered: str) -> FactorCondition | None:
        match = re.search(r"\b([a-z][a-z0-9_ ]{1,40}?)\s+(?:weight\s+)?(>=|<=|>|<|=)\s*(\d+(?:\.\d+)?)", lowered)
        if not match:
            return None
        factor = _factor_key(match.group(1))
        return FactorCondition(factor=factor, operator=match.group(2), value=float(match.group(3)))

    def _performance_sort(self, lowered: str) -> str | None:
        if any(term in lowered for term in ("best setup", "best performing", "most profitable")):
            return "best"
        if any(term in lowered for term in ("worst setup", "worst performing", "least profitable")):
            return "worst"
        return None

    def _sort_results(self, results: list[dict[str, Any]], parsed: dict[str, Any]) -> list[dict[str, Any]]:
        performance = parsed.get("performance")
        if performance == "best":
            return sorted(results, key=lambda trade: _number(trade.get("pnl")) or 0.0, reverse=True)
        if performance == "worst":
            return sorted(results, key=lambda trade: _number(trade.get("pnl")) or 0.0)
        return results

    def _matches_factor(self, trade: dict[str, Any], condition: FactorCondition) -> bool:
        factors = trade.get("factors") if isinstance(trade.get("factors"), dict) else {}
        value = _number(factors.get(condition.factor))
        if value is None:
            return False
        if condition.operator == ">":
            return value > condition.value
        if condition.operator == ">=":
            return value >= condition.value
        if condition.operator == "<":
            return value < condition.value
        if condition.operator == "<=":
            return value <= condition.value
        return value == condition.value

    def _public_parsed(self, parsed: dict[str, Any]) -> dict[str, Any]:
        output = {
            key: value
            for key, value in parsed.items()
            if key not in {"date_range", "factor"}
        }
        if parsed.get("date_range"):
            start, end = parsed["date_range"]
            output["date_range"] = [start.isoformat(), end.isoformat()]
        if parsed.get("factor"):
            condition: FactorCondition = parsed["factor"]
            output["factor"] = {
                "name": condition.factor,
                "operator": condition.operator,
                "value": condition.value,
            }
        return output

    def _summary(self, parsed: dict[str, Any], count: int, warnings: list[str]) -> str:
        if warnings and not parsed:
            return f"{count} trades shown. No journal filters matched."
        parts: list[str] = []
        if parsed.get("category"):
            parts.append(str(parsed["category"]))
        if parsed.get("regime"):
            parts.append(f"in {parsed['regime']} markets")
        if parsed.get("period_label"):
            parts.append(str(parsed["period_label"]))
        if parsed.get("factor"):
            condition: FactorCondition = parsed["factor"]
            parts.append(f"{condition.factor} {condition.operator} {condition.value:g}")
        if parsed.get("confidence_min") is not None:
            parts.append("high confidence")
        if parsed.get("performance") == "best":
            parts.append("sorted best first")
        if parsed.get("performance") == "worst":
            parts.append("sorted worst first")
        if not parts:
            return f"Showing all {count} trades."
        return f"{count} trades matched: {', '.join(parts)}."


def _normalize(value: str) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def _match_known(text: str, values: tuple[str, ...]) -> str | None:
    compact = text.replace(" ", "_")
    for value in values:
        if re.search(rf"(^|_){re.escape(value)}($|_)", compact):
            return value
    return None


def _quarter_range(year: int, quarter: int) -> tuple[date, date]:
    start_month = (quarter - 1) * 3 + 1
    end_month = start_month + 2
    return (
        date(year, start_month, 1),
        date(year, end_month, calendar.monthrange(year, end_month)[1]),
    )


def _entry_date(trade: dict[str, Any]) -> date | None:
    value = trade.get("entry_time") or trade.get("date")
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _text(value: Any) -> str:
    return str(value or "").strip().lower()


def _factor_key(value: str) -> str:
    text = _normalize(value)
    text = re.sub(r"\b(trades?|where|with|factor|the)\b", "", text)
    return re.sub(r"_+", "_", text.replace(" ", "_")).strip("_")
