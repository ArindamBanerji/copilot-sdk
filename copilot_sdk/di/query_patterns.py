"""Deterministic NL query patterns for Data Intelligence decisions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol


@dataclass(frozen=True)
class QueryResult:
    """Pattern query result that can be downcast to the router's dict response."""

    intent: str
    data: list[dict[str, Any]] | dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    summary: str = ""

    def to_response(self) -> dict[str, Any]:
        payload = self.data if self.data is not None else {}
        evidence = payload if isinstance(payload, list) else []
        result = payload if isinstance(payload, dict) else {"items": payload}
        return {
            "intent": self.intent,
            "answer": self.summary,
            "evidence": evidence,
            "query_template": f"python:{self.intent}",
            "result": result,
            "metadata": {**self.metadata, "intent": self.intent},
        }


@dataclass(frozen=True)
class _WindowSpec:
    start: datetime | None
    end: datetime | None
    label: str
    supported: bool = True
    reason: str = ""
    query_window: str = ""


class QueryPattern(Protocol):
    intent: str
    priority: int

    def matches(self, query: str) -> bool:
        ...

    def execute(
        self,
        query: str,
        decisions: list[dict[str, Any]],
        profiles: list[dict[str, Any]] | None = None,
    ) -> QueryResult:
        ...


class ComparisonPattern:
    intent = "comparison"
    priority = 50
    _keywords = ("compare", " vs ", " versus ", "difference", "better", "worse", "improved", "declined")

    def matches(self, query: str) -> bool:
        lowered = _lower(query)
        return any(keyword in f" {lowered} " for keyword in self._keywords)

    def execute(
        self,
        query: str,
        decisions: list[dict[str, Any]],
        profiles: list[dict[str, Any]] | None = None,
    ) -> QueryResult:
        del profiles
        if not decisions:
            return _empty("comparison", "No decision evidence is available to compare.")

        lowered = _lower(query)
        if "this month" in lowered and "last month" in lowered:
            return self._compare_months(decisions)

        left, right = _comparison_terms(lowered)
        if not left or not right:
            return QueryResult(
                intent=self.intent,
                data={"period_a": {}, "period_b": {}, "delta": 0, "trend": "unavailable"},
                metadata={"count": 0, "warnings": ["comparison terms not recognized"]},
                summary="Comparison terms were not specific enough to evaluate safely.",
            )

        left_rows = [row for row in decisions if _matches_term(row, left)]
        right_rows = [row for row in decisions if _matches_term(row, right)]
        delta = len(left_rows) - len(right_rows)
        trend = "improved" if delta > 0 else "declined" if delta < 0 else "stable"
        return QueryResult(
            intent=self.intent,
            data={
                "period_a": {"label": left, "count": len(left_rows)},
                "period_b": {"label": right, "count": len(right_rows)},
                "delta": delta,
                "trend": trend,
            },
            metadata={"count": len(left_rows) + len(right_rows), "warnings": []},
            summary=f"Compared {left} with {right}: delta {delta}, trend {trend}.",
        )

    def _compare_months(self, decisions: list[dict[str, Any]]) -> QueryResult:
        now = datetime.now(timezone.utc)
        this_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        if now.month == 1:
            last_start = datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
        else:
            last_start = datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc)
        this_rows, missing_this = _rows_between(decisions, this_start, now)
        last_rows, missing_last = _rows_between(decisions, last_start, this_start)
        delta = len(this_rows) - len(last_rows)
        trend = "improved" if delta > 0 else "declined" if delta < 0 else "stable"
        warnings = []
        missing = _timestamp_missing_count(decisions)
        if missing:
            warnings.append(f"{missing} decision(s) missing timestamp")
        return QueryResult(
            intent=self.intent,
            data={
                "period_a": {"label": "this_month", "count": len(this_rows)},
                "period_b": {"label": "last_month", "count": len(last_rows)},
                "delta": delta,
                "trend": trend,
            },
            metadata={
                "count": len(this_rows) + len(last_rows),
                "missing_timestamp_count": missing,
                "warnings": warnings,
            },
            summary=f"This month has {len(this_rows)} decision(s) versus {len(last_rows)} last month; trend {trend}.",
        )


class AggregationPattern:
    intent = "aggregation"
    priority = 40
    _keywords = ("average", "avg", "total", "count", "sum", "mean", "max", "min")

    def matches(self, query: str) -> bool:
        lowered = _lower(query)
        return any(keyword in lowered for keyword in self._keywords)

    def execute(
        self,
        query: str,
        decisions: list[dict[str, Any]],
        profiles: list[dict[str, Any]] | None = None,
    ) -> QueryResult:
        del profiles
        if not decisions:
            return _empty("aggregation", "No decision evidence is available to aggregate.")

        lowered = _lower(query)
        group_by = _group_dimension(lowered)
        metric = _metric_name(lowered)
        groups = _group_rows(decisions, group_by)
        rows: list[dict[str, Any]] = []
        missing_metric = 0
        for key, grouped in groups.items():
            values = [_numeric_metric(row, metric) for row in grouped]
            numeric = [value for value in values if value is not None]
            missing_metric += len(values) - len(numeric)
            if "average" in lowered or "avg" in lowered or "mean" in lowered:
                value = sum(numeric) / len(numeric) if numeric else None
                op = "average"
            elif "sum" in lowered or "total" in lowered:
                value = sum(numeric) if numeric else None
                op = "sum"
            elif "max" in lowered:
                value = max(numeric) if numeric else None
                op = "max"
            elif "min" in lowered:
                value = min(numeric) if numeric else None
                op = "min"
            else:
                value = len(grouped)
                op = "count"
            rows.append({"group": key, "count": len(grouped), "metric": metric, "operation": op, "value": value})
        rows.sort(key=_aggregate_sort_key)
        warnings = [f"{missing_metric} decision(s) missing metric {metric}"] if missing_metric else []
        return QueryResult(
            intent=self.intent,
            data={"groups": rows},
            metadata={"count": len(decisions), "group_by": group_by, "metric": metric, "warnings": warnings},
            summary=f"Aggregated {len(decisions)} decision(s) by {group_by}.",
        )


class AccuracyPattern:
    intent = "accuracy"
    priority = 30
    _keywords = ("accuracy", "accurate", "correct", "incorrect", "performance", "how well")

    def matches(self, query: str) -> bool:
        lowered = _lower(query)
        return any(keyword in lowered for keyword in self._keywords)

    def execute(
        self,
        query: str,
        decisions: list[dict[str, Any]],
        profiles: list[dict[str, Any]] | None = None,
    ) -> QueryResult:
        del profiles
        if not decisions:
            return _empty("accuracy", "No decision evidence is available to compute accuracy.")
        rows = _apply_time_window(decisions, query)
        group_by = _accuracy_group_dimension(_lower(query))
        groups = _group_rows(rows, group_by) if group_by != "overall" else {"overall": rows}
        result_rows: list[dict[str, Any]] = []
        unknown = 0
        for key, grouped in groups.items():
            correctness = [_correctness(row) for row in grouped]
            known = [value for value in correctness if value is not None]
            unknown += len(correctness) - len(known)
            correct = sum(1 for value in known if value)
            total = len(known)
            result_rows.append(
                {
                    "group": key,
                    "correct": correct,
                    "total": total,
                    "accuracy": correct / total if total else None,
                    "error_rate": (total - correct) / total if total else None,
                }
            )
        known_total = sum(row["total"] for row in result_rows)
        if known_total == 0:
            summary = "No verified/correctness evidence is available to compute accuracy."
        else:
            summary = f"Computed accuracy from {known_total} decision(s)."
        return QueryResult(
            intent=self.intent,
            data={"groups": result_rows},
            metadata={
                "count": known_total,
                "group_by": group_by,
                "unknown_correctness_count": unknown,
                "warnings": ["correctness unavailable for some decisions"] if unknown else [],
            },
            summary=summary,
        )


class TimeWindowPattern:
    intent = "time_window"
    priority = 20
    _keywords = ("last", "past", "since", "this week", "this month", "yesterday", "days", "weeks", "months", "quarter")

    def matches(self, query: str) -> bool:
        lowered = _lower(query)
        return any(keyword in lowered for keyword in self._keywords)

    def execute(
        self,
        query: str,
        decisions: list[dict[str, Any]],
        profiles: list[dict[str, Any]] | None = None,
    ) -> QueryResult:
        del profiles
        if not decisions:
            return _empty("time_window", "No decision evidence is available for the requested time window.")
        window = _window(query)
        if not window.supported or window.start is None or window.end is None:
            return QueryResult(
                intent=self.intent,
                data={"items": [], "count": 0},
                metadata={
                    "count": 0,
                    "supported": False,
                    "reason": window.reason or "unsupported_time_window",
                    "query_window": window.query_window or window.label,
                    "missing_timestamp_count": 0,
                    "warnings": [window.reason or "unsupported_time_window"],
                },
                summary=f"The requested {window.query_window or window.label} window could not be parsed safely.",
            )
        rows, missing = _rows_between(decisions, window.start, window.end)
        warnings = [f"{missing} decision(s) missing timestamp"] if missing else []
        summary = (
            f"Found {len(rows)} decision(s) in {window.label}."
            if rows
            else f"No timestamped decision evidence matched {window.label}."
        )
        return QueryResult(
            intent=self.intent,
            data={"items": [_small_payload(row) for row in rows], "count": len(rows)},
            metadata={
                "count": len(rows),
                "window": window.label,
                "start": window.start.isoformat(),
                "end": window.end.isoformat(),
                "missing_timestamp_count": missing,
                "warnings": warnings,
            },
            summary=summary,
        )


class MultiEntityPattern:
    intent = "multi_entity"
    priority = 10
    _keywords = ("all", "every", "which", "list", "show me", "suppliers", "sources", "systems", "entities")

    def matches(self, query: str) -> bool:
        lowered = _lower(query)
        return any(keyword in lowered for keyword in self._keywords)

    def execute(
        self,
        query: str,
        decisions: list[dict[str, Any]],
        profiles: list[dict[str, Any]] | None = None,
    ) -> QueryResult:
        del profiles
        if not decisions:
            return _empty("multi_entity", "No decision evidence is available to list entities.")
        lowered = _lower(query)
        dimension = _group_dimension(lowered)
        threshold = _threshold(lowered)
        groups = _group_rows(decisions, dimension)
        rows = [{"entity": key, "count": len(grouped), "dimension": dimension} for key, grouped in groups.items()]
        if threshold is not None:
            op, threshold_value, is_percent = threshold
            metric = _explicit_metric_name(lowered)
            if is_percent:
                if metric is None or not _is_rate_metric(metric):
                    return QueryResult(
                        intent=self.intent,
                        data={"entities": []},
                        metadata={
                            "count": 0,
                            "dimension": dimension,
                            "threshold": threshold,
                            "supported": False,
                            "reason": "percent_threshold_requires_rate_metric",
                            "warnings": ["percentage thresholds require a rate-like metric"],
                        },
                        summary="Percentage thresholds are only supported for rate-like metrics.",
                    )
                rate_rows = []
                missing_metric = 0
                for row in rows:
                    grouped = groups[str(row["entity"])]
                    rate_value = _group_rate_value(grouped, metric)
                    if rate_value is None:
                        missing_metric += len(grouped)
                        continue
                    row = {**row, "metric": metric, "value": rate_value}
                    if _passes_threshold(rate_value, op, threshold_value):
                        rate_rows.append(row)
                rows = rate_rows
                warnings = [f"{missing_metric} decision(s) missing rate metric {metric}"] if missing_metric else []
                return QueryResult(
                    intent=self.intent,
                    data={"entities": rows},
                    metadata={"count": len(rows), "dimension": dimension, "threshold": threshold, "metric": metric, "warnings": warnings},
                    summary=f"Found {len(rows)} {dimension} group(s) matching {metric} threshold.",
                )
            rows = [row for row in rows if _passes_threshold(_row_count(row), op, threshold_value)]
        rows.sort(key=lambda row: (-_row_count(row), str(row["entity"])))
        return QueryResult(
            intent=self.intent,
            data={"entities": rows},
            metadata={"count": len(rows), "dimension": dimension, "threshold": threshold, "warnings": []},
            summary=f"Found {len(rows)} {dimension} group(s).",
        )


def default_patterns() -> list[QueryPattern]:
    return [
        ComparisonPattern(),
        AggregationPattern(),
        AccuracyPattern(),
        TimeWindowPattern(),
        MultiEntityPattern(),
    ]


def _lower(query: str) -> str:
    return str(query or "").strip().lower()


def _empty(intent: str, summary: str) -> QueryResult:
    return QueryResult(intent=intent, data={"count": 0}, metadata={"count": 0, "warnings": ["no decision data"]}, summary=summary)


def _row_count(row: dict[str, Any]) -> float:
    value = row.get("count", 0)
    return float(value) if isinstance(value, (int, float)) else 0.0


def _aggregate_sort_key(row: dict[str, Any]) -> tuple[float, str]:
    value = row.get("value")
    sort_value = float(value) if isinstance(value, (int, float)) else _row_count(row)
    return (-sort_value, str(row.get("group", "")))


def _metadata(decision: dict[str, Any]) -> dict[str, Any]:
    value = decision.get("metadata")
    return value if isinstance(value, dict) else {}


def _field(decision: dict[str, Any], *names: str) -> Any:
    metadata = _metadata(decision)
    raw_factors = decision.get("factors")
    factors: dict[str, Any] = raw_factors if isinstance(raw_factors, dict) else {}
    for name in names:
        if decision.get(name) not in (None, ""):
            return decision.get(name)
        if metadata.get(name) not in (None, ""):
            return metadata.get(name)
        if factors.get(name) not in (None, ""):
            return factors.get(name)
    return None


def _timestamp(decision: dict[str, Any]) -> datetime | None:
    value = _field(decision, "created_at", "timestamp", "decision_time", "verified_at")
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, (int, float)):
        parsed = datetime.fromtimestamp(float(value), tz=timezone.utc)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _correctness(decision: dict[str, Any]) -> bool | None:
    for name in ("is_correct", "correct"):
        value = _field(decision, name)
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)) and value in (0, 1):
            return bool(value)
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
    outcome = _field(decision, "outcome")
    if isinstance(outcome, str):
        lowered = outcome.lower()
        if lowered in {"confirmed", "correct", "success"}:
            return True
        if lowered in {"override", "incorrect", "failure"}:
            return False
    actual = _field(decision, "actual_action")
    recommended = _field(decision, "recommended_action", "action")
    if actual and recommended:
        return str(actual) == str(recommended)
    return None


def _entity(decision: dict[str, Any], dimension: str) -> str:
    if dimension == "category":
        return str(_field(decision, "category") or "unknown")
    if dimension == "action":
        return str(_field(decision, "recommended_action", "action") or "unknown")
    if dimension == "source":
        source_ids = _field(decision, "source_ids")
        if isinstance(source_ids, list) and source_ids:
            return str(source_ids[0])
        return str(_field(decision, "source_id", "source", "system", "seed_id") or "unknown")
    if dimension == "system":
        return str(_field(decision, "system", "source", "source_id") or "unknown")
    if dimension == "supplier":
        return str(_field(decision, "supplier_id", "supplier", "vendor_id") or "unknown")
    return str(_field(decision, "entity_id", "supplier_id", "source_id", "source", "system") or "unknown")


def _group_dimension(lowered: str) -> str:
    if "supplier" in lowered:
        return "supplier"
    if "source" in lowered:
        return "source"
    if "system" in lowered:
        return "system"
    if "category" in lowered:
        return "category"
    if "action" in lowered:
        return "action"
    return "entity"


def _accuracy_group_dimension(lowered: str) -> str:
    if "by category" in lowered:
        return "category"
    if "by source" in lowered:
        return "source"
    if "by supplier" in lowered:
        return "supplier"
    if "by entity" in lowered:
        return "entity"
    return "overall"


def _group_rows(decisions: list[dict[str, Any]], dimension: str) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for decision in decisions:
        groups.setdefault(_entity(decision, dimension), []).append(decision)
    return groups


def _metric_name(lowered: str) -> str:
    explicit = _explicit_metric_name(lowered)
    if explicit is not None:
        return explicit
    return "confidence"


def _explicit_metric_name(lowered: str) -> str | None:
    for name in ("accuracy", "error_rate", "confidence", "amount", "exception_rate"):
        if name in lowered or name.replace("_", " ") in lowered:
            return name
    return None


def _numeric_metric(decision: dict[str, Any], metric: str) -> float | None:
    return _safe_float(_field(decision, metric))


def _safe_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _window(query: str) -> _WindowSpec:
    lowered = _lower(query)
    now = datetime.now(timezone.utc)
    since_match = re.search(r"\bsince\s+(\d{4}[-/]\d{2}[-/]\d{2})\b", lowered)
    if "since" in lowered:
        if not since_match:
            return _WindowSpec(None, None, "since", supported=False, reason="unsupported_since_window", query_window="since")
        date_text = since_match.group(1).replace("/", "-")
        try:
            start = datetime.fromisoformat(date_text).replace(tzinfo=timezone.utc)
        except ValueError:
            return _WindowSpec(None, None, "since", supported=False, reason="invalid_since_date", query_window="since")
        return _WindowSpec(start, now, f"since {date_text}", query_window="since")
    if "yesterday" in lowered:
        start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return _WindowSpec(start, start + timedelta(days=1), "yesterday")
    if "this week" in lowered:
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        return _WindowSpec(start, now, "this week")
    if "this month" in lowered:
        return _WindowSpec(datetime(now.year, now.month, 1, tzinfo=timezone.utc), now, "this month")
    if "quarter" in lowered:
        month = ((now.month - 1) // 3) * 3 + 1
        return _WindowSpec(datetime(now.year, month, 1, tzinfo=timezone.utc), now, "this quarter")
    match = re.search(r"(?:last|past)?\s*(\d+)\s*(day|days|week|weeks|month|months)", lowered)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        days = amount * 7 if "week" in unit else amount * 30 if "month" in unit else amount
        return _WindowSpec(now - timedelta(days=days), now, f"last {amount} {unit}")
    return _WindowSpec(None, None, "time_window", supported=False, reason="unsupported_time_window", query_window="time_window")


def _rows_between(decisions: list[dict[str, Any]], start: datetime, end: datetime) -> tuple[list[dict[str, Any]], int]:
    rows = []
    missing = 0
    for decision in decisions:
        timestamp = _timestamp(decision)
        if timestamp is None:
            missing += 1
            continue
        if start <= timestamp <= end:
            rows.append(decision)
    return rows, missing


def _timestamp_missing_count(decisions: list[dict[str, Any]]) -> int:
    return sum(1 for decision in decisions if _timestamp(decision) is None)


def _apply_time_window(decisions: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    lowered = _lower(query)
    if not any(term in lowered for term in TimeWindowPattern._keywords):
        return decisions
    window = _window(query)
    if not window.supported or window.start is None or window.end is None:
        return []
    rows, _missing = _rows_between(decisions, window.start, window.end)
    return rows


def _comparison_terms(lowered: str) -> tuple[str | None, str | None]:
    for separator in (" versus ", " vs "):
        if separator in f" {lowered} ":
            left, right = lowered.split(separator.strip(), 1)
            return _last_token(left), _first_token(right)
    return None, None


def _first_token(text: str) -> str | None:
    tokens = re.findall(r"[a-zA-Z0-9_-]+", text)
    return tokens[0] if tokens else None


def _last_token(text: str) -> str | None:
    tokens = re.findall(r"[a-zA-Z0-9_-]+", text)
    return tokens[-1] if tokens else None


def _matches_term(decision: dict[str, Any], term: str) -> bool:
    values = [
        _entity(decision, "supplier"),
        _entity(decision, "source"),
        _entity(decision, "system"),
        _entity(decision, "category"),
        _entity(decision, "action"),
        _entity(decision, "entity"),
    ]
    return any(str(value).lower() == term.lower() for value in values)


def _threshold(lowered: str) -> tuple[str, float, bool] | None:
    match = re.search(r"(>=|<=|>|<)\s*(\d+(?:\.\d+)?)\s*%?", lowered)
    if match:
        value = float(match.group(2))
        is_percent = "%" in match.group(0)
        if is_percent:
            value /= 100.0
        return match.group(1), value, is_percent
    match = re.search(r"\b(above|below)\s*(\d+(?:\.\d+)?)\s*%?", lowered)
    if match:
        value = float(match.group(2))
        is_percent = "%" in match.group(0)
        if is_percent:
            value /= 100.0
        return (">" if match.group(1) == "above" else "<"), value, is_percent
    return None


def _passes_threshold(value: float, op: str, threshold: float) -> bool:
    if op == ">":
        return value > threshold
    if op == ">=":
        return value >= threshold
    if op == "<":
        return value < threshold
    if op == "<=":
        return value <= threshold
    return False


def _is_rate_metric(metric: str) -> bool:
    return metric in {"accuracy", "error_rate", "confidence"} or metric.endswith("_rate") or "rate" in metric


def _group_rate_value(rows: list[dict[str, Any]], metric: str) -> float | None:
    if metric == "accuracy" or metric == "error_rate":
        known = [_correctness(row) for row in rows]
        correctness_values = [value for value in known if value is not None]
        if not correctness_values:
            return None
        correct = sum(1 for value in correctness_values if value)
        accuracy = correct / len(correctness_values)
        return accuracy if metric == "accuracy" else 1.0 - accuracy

    numeric = [_numeric_metric(row, metric) for row in rows]
    numeric_values = [value for value in numeric if value is not None]
    if not numeric_values:
        return None
    average = sum(numeric_values) / len(numeric_values)
    if metric == "confidence" and average > 1.0:
        return average / 100.0
    return average


def _small_payload(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_id": str(_field(decision, "decision_id") or ""),
        "category": _entity(decision, "category"),
        "entity": _entity(decision, "entity"),
        "confidence": _safe_float(_field(decision, "confidence")),
    }
