"""DI-3 quality-aware query orchestration."""

from __future__ import annotations

import logging
import os
import re
import time
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from copilot_sdk.di.claude_parser import ClaudeQueryParser
from copilot_sdk.di.confidence import compute_confidence, tier_to_score
from copilot_sdk.di.query_allowlists import (
    validate_dimensions,
    validate_domain,
    validate_metric,
)
from copilot_sdk.di.query_models import (
    QueryDescription,
    QueryIntent,
    QueryPlan,
    QueryRequest,
    QueryResponse,
    RawQueryResult,
    ResponseMetadata,
    SourceAttribution,
    SourceUsage,
)
from copilot_sdk.di.query_providers import DataProvider, ProviderUnavailableError


LOGGER = logging.getLogger(__name__)


class InvalidQueryError(ValueError):
    """Raised when a request cannot be safely converted to a QueryPlan."""


class DIQueryService:
    """Parse, execute, and quality-enrich governed DataOps queries."""

    def __init__(
        self,
        provider: DataProvider,
        *,
        allowed_domains: set[str] | None = None,
        source_id_map: Mapping[str, str] | None = None,
        claude_parser: ClaudeQueryParser | None = None,
        minimum_sample: int = 10,
        max_records: int = 1000,
        cache_ttl_seconds: float | None = None,
    ) -> None:
        self.provider = provider
        self.allowed_domains = {value.lower() for value in (allowed_domains or {"dataops"})}
        self.source_id_map = {str(key): str(value) for key, value in (source_id_map or {}).items()}
        self.claude_parser = claude_parser
        self.minimum_sample = minimum_sample
        self.max_records = max(1, max_records)
        configured_ttl = os.environ.get("DI_QUERY_CACHE_TTL_SECONDS", "300")
        self.cache_ttl_seconds = max(
            0.0,
            float(configured_ttl) if cache_ttl_seconds is None else float(cache_ttl_seconds),
        )
        self._response_cache: dict[tuple[str, str, str | None], tuple[float, QueryResponse]] = {}

    def invalidate_cache(self) -> None:
        """Drop query results after score/learn changes governed evidence."""

        self._response_cache.clear()

    def parse(self, question: str, *, context: Any = None) -> QueryPlan:
        normalized = str(question or "").strip()
        if not normalized:
            raise InvalidQueryError("question is required")
        query_context = _context_dict(context)
        domain = validate_domain(str(query_context.get("domain", "dataops")))
        if domain not in self.allowed_domains:
            raise InvalidQueryError(f"Unauthorized query domain: {domain}")
        lowered = normalized.lower()
        if _looks_like_raw_query(lowered):
            return QueryPlan(
                intent=QueryIntent.UNSUPPORTED,
                domain=domain,
                explanation="Raw SQL and Cypher are not accepted as query input.",
                supported=False,
                reason="raw_query_rejected",
            )

        metric = _metric(lowered)
        intent = _intent(lowered, metric)
        dimensions = _dimensions(lowered)
        time_window = _time_window(lowered)
        requested_sources = [str(value) for value in query_context.get("preferred_sources", [])]
        reason = None
        supported = True
        if _explicit_unsupported_metric(lowered, metric):
            supported = False
            intent = QueryIntent.UNSUPPORTED
            reason = "metric_not_available"
        if intent == QueryIntent.UNSUPPORTED and reason is None:
            reason = "question_not_supported"
        deterministic_plan = QueryPlan(
            intent=intent,
            domain=domain,
            metric=metric,
            dimensions=dimensions,
            time_window=time_window,
            requested_sources=requested_sources,
            requires_join=len(requested_sources) > 1 or " and " in lowered,
            explanation=f"Deterministic DI-3 parse classified the question as {intent.value}.",
            supported=supported,
            reason=reason,
        )
        if deterministic_plan.intent != QueryIntent.UNSUPPORTED or self.claude_parser is None:
            return deterministic_plan
        try:
            claude_plan = self.claude_parser.parse(normalized, domain)
        except Exception as exc:
            LOGGER.warning("di3_claude_parser_unavailable", extra={"reason": str(exc)[:120]})
            return deterministic_plan
        if claude_plan is None or claude_plan.intent == QueryIntent.UNSUPPORTED:
            return deterministic_plan
        requested_sources = [str(value) for value in query_context.get("preferred_sources", [])]
        return claude_plan.model_copy(
            update={
                "domain": domain,
                "requested_sources": requested_sources or claude_plan.requested_sources,
                "requires_join": len(requested_sources) > 1 or claude_plan.requires_join,
            }
        )

    def route(self, plan: QueryPlan) -> RawQueryResult:
        return self.provider.execute(plan)

    def compute(self, plan: QueryPlan, data: RawQueryResult) -> RawQueryResult:
        reference_as_of = data.data_as_of if getattr(self.provider, "uses_snapshot_time_windows", False) else None
        rows = _filter_rows(data.rows, plan, reference_as_of=reference_as_of)[: self.max_records]
        data.rows = rows
        data.records_scanned = len(rows)
        data.source_usage = _source_usage(rows, requested_sources=plan.requested_sources)
        data.aggregate = _aggregate(plan, rows)
        data.unmatched_records = _unmatched(rows)
        return data

    def enrich(self, result: RawQueryResult, source_ids: list[str]) -> tuple[list[SourceAttribution], dict[str, Any], dict[str, Any]]:
        profile_ids = [self._profile_source_id(source_id) for source_id in source_ids]
        raw_profiles = self.provider.get_source_profiles(profile_ids)
        mapped_profiles = _profile_map(raw_profiles, profile_ids)
        profiles = {
            source_id: mapped_profiles.get(self._profile_source_id(source_id))
            for source_id in source_ids
        }
        raw_health = self.provider.get_source_health(profile_ids)
        raw_alerts = self.provider.get_active_alerts(profile_ids)
        conservation = self.provider.get_conservation_state(profile_ids)
        alerts = _alert_map(raw_alerts, profile_ids)
        attributions: list[SourceAttribution] = []
        total = sum(max(float(item.contribution), 0.0) for item in result.source_usage) or 1.0
        for index, usage in enumerate(result.source_usage):
            profile = profiles.get(usage.source_id)
            trust = _trust(profile)
            attributions.append(
                SourceAttribution(
                    source_id=self._profile_source_id(usage.source_id),
                    source=_profile_name(profile, self._profile_source_id(usage.source_id)),
                    trust=trust,
                    trust_available=_trust_value(profile) is not None,
                    contribution="primary" if index == 0 else "secondary" if index == 1 else "supporting",
                    weight=max(float(usage.contribution), 0.0) / total,
                    freshness_hours=_freshness(profile, result.data_as_of),
                    records_used=usage.records_used,
                )
            )
        return attributions, profiles, {
            **alerts,
            "__health__": raw_health,
            "__conservation__": conservation,
        }

    def _profile_source_id(self, source_id: str) -> str:
        return self.source_id_map.get(source_id, source_id)

    def _all_profiles(self) -> list[Any]:
        getter = getattr(self.provider, "get_all_source_profiles", None)
        if callable(getter):
            return list(getter())
        catalog = getattr(self.provider, "source_profiles", None)
        if isinstance(catalog, Mapping):
            return [{"source_id": source_id, **dict(profile)} for source_id, profile in catalog.items()]
        return []

    def confidence(
        self,
        result: RawQueryResult,
        profiles: dict[str, Any],
        alerts: dict[str, Any] | list[Any] | None = None,
    ):
        return compute_confidence(
            result.source_usage,
            profiles,
            data_as_of=result.data_as_of,
            unmatched_records=result.unmatched_records,
            records_scanned=result.records_scanned,
            disagreement_ratio=result.disagreement_ratio,
            active_alerts=alerts,
            minimum_sample=self.minimum_sample,
        )

    def execute(self, request: QueryRequest | Mapping[str, Any]) -> QueryResponse:
        query_request = request if isinstance(request, QueryRequest) else QueryRequest.model_validate(request)
        query_id = str(uuid4())
        started = datetime.now(timezone.utc)
        plan = self.parse(query_request.question, context=query_request.context)
        cache_key = (query_request.question.strip().lower(), plan.domain, plan.time_window)
        cached = self._response_cache.get(cache_key)
        if cached is not None and time.monotonic() - cached[0] < self.cache_ttl_seconds:
            response = cached[1].model_copy(deep=True)
            response.metadata.cache = "hit"
            response.metadata.query_id = query_id
            return response
        if cached is not None:
            self._response_cache.pop(cache_key, None)
        LOGGER.info(
            "di3_query_started",
            extra={"query_id": query_id, "domain": plan.domain, "intent": plan.intent.value},
        )
        if not plan.supported:
            return self._response_for_plan(plan, query_id, "Insufficient verified data to answer this question.", plan.reason)
        if plan.intent == QueryIntent.SOURCE_RELIABILITY:
            return self._source_reliability_response(plan, query_id, started)
        try:
            result = self.compute(plan, self.route(plan))
        except ProviderUnavailableError:
            LOGGER.warning("di3_query_provider_unavailable", extra={"query_id": query_id})
            return self._response_for_plan(
                plan,
                query_id,
                "Insufficient verified data to answer this question.",
                "provider_unavailable",
                warning="The governed data provider is unavailable; no fixture substitution was used.",
            )

        source_ids = [item.source_id for item in result.source_usage]
        attributions, profiles, quality = self.enrich(result, source_ids)
        alerts = {
            key: value
            for key, value in quality.items()
            if key not in {"__health__", "__conservation__"}
        }
        confidence = self.confidence(result, profiles, alerts)
        answer = _answer(plan, result)
        warnings = list(confidence.warnings)
        conservation = quality.get("__conservation__")
        conservation_state = str(_value(conservation, "status", "state", default=conservation or "")).upper()
        if conservation_state in {"AMBER", "RED"}:
            warnings.append(f"Conservation state is {conservation_state}; verification is recommended.")
        if not result.rows and result.aggregate is None:
            answer = "Insufficient verified data to answer this question."
            confidence.score = None
            confidence.label = "insufficient"
            warnings.append("No verified records matched the request.")
        evidence = _evidence(plan, result)
        response = QueryResponse(
            answer=answer,
            confidence=confidence.score,
            confidence_label=confidence.label,
            source_attribution=attributions,
            evidence=evidence,
            quality_warning=" ".join(dict.fromkeys(warnings)) or None,
            computation_path=[*result.query_path, _path_step(plan, result)],
            query=QueryDescription(
                intent=plan.intent.value,
                metric=plan.metric,
                time_window=plan.time_window,
                domain=plan.domain,
                supported=plan.supported,
                reason=plan.reason,
            ),
            metadata=ResponseMetadata(
                generated_at=started,
                data_as_of=result.data_as_of,
                cache="miss",
                query_id=query_id,
            ),
        )
        self._response_cache[cache_key] = (time.monotonic(), response)
        LOGGER.info(
            "di3_query_completed",
            extra={
                "query_id": query_id,
                "records_scanned": result.records_scanned,
                "confidence": response.confidence,
            },
        )
        return response

    def _source_reliability_response(
        self,
        plan: QueryPlan,
        query_id: str,
        started: datetime,
    ) -> QueryResponse:
        profiles = [profile for profile in self._all_profiles() if _trust_value(profile) is not None]
        ranked = sorted(profiles, key=lambda profile: _trust(profile), reverse=True)
        if not ranked:
            return self._response_for_plan(
                plan,
                query_id,
                "Insufficient verified data to answer this question.",
                "source_profiles_unavailable",
                warning="No verified source trust profiles are available.",
            )
        top = ranked[0]
        least = ranked[-1]
        top_name = _profile_name(top, "unknown source")
        least_name = _profile_name(least, "unknown source")
        top_tier = _value(top, "trust_tier")
        least_tier = _value(least, "trust_tier")
        answer = (
            f"{top_name} (trust tier {int(top_tier)}) is the most reliable source."
            if top_tier is not None
            else f"{top_name} (trust {_trust(top):.2f}) is the most reliable source."
        )
        least_evidence = (
            f"{least_name} is the least reliable at trust tier {int(least_tier)}."
            if least_tier is not None
            else f"{least_name} is the least reliable at {_trust(least):.2f}."
        )
        attributions = [
            SourceAttribution(
                source_id=str(_value(profile, "source_id", "id", default=f"source-{index}")),
                source=_profile_name(profile, "unknown source"),
                trust=_trust(profile),
                trust_available=True,
                contribution="primary" if index == 0 else "secondary" if index == 1 else "supporting",
                weight=1.0 / len(ranked),
                records_used=0,
            )
            for index, profile in enumerate(ranked)
        ]
        return QueryResponse(
            answer=answer,
            confidence=1.0,
            confidence_label="high",
            source_attribution=attributions,
            evidence=(
                f"Ranked {len(ranked)} governed source profiles by measured trust; {least_evidence}"
            ),
            computation_path=["DI-1 source profiles → rank by trust"],
            query=QueryDescription(
                intent=plan.intent.value,
                metric="source_trust",
                domain=plan.domain,
                supported=True,
            ),
            metadata=ResponseMetadata(generated_at=started, query_id=query_id),
        )

    def query(self, request: QueryRequest | Mapping[str, Any]) -> QueryResponse:
        return self.execute(request)

    def _response_for_plan(
        self,
        plan: QueryPlan,
        query_id: str,
        answer: str,
        reason: str | None,
        warning: str | None = None,
    ) -> QueryResponse:
        return QueryResponse(
            answer=answer,
            confidence=None,
            confidence_label="insufficient",
            source_attribution=[],
            evidence="The requested metric is not available in the governed DataOps sources.",
            quality_warning=warning,
            computation_path=[],
            query=QueryDescription(
                intent=plan.intent.value,
                metric=plan.metric,
                time_window=plan.time_window,
                domain=plan.domain,
                supported=False,
                reason=reason,
            ),
            metadata=ResponseMetadata(generated_at=datetime.now(timezone.utc), query_id=query_id),
        )


def _context_dict(context: Any) -> dict[str, Any]:
    if context is None:
        return {"domain": "dataops"}
    if isinstance(context, Mapping):
        return dict(context)
    if hasattr(context, "model_dump"):
        return dict(context.model_dump())
    return {"domain": "dataops"}


def _looks_like_raw_query(question: str) -> bool:
    return bool(re.search(r"\b(select|insert|update|delete|match|create|merge|drop)\b", question)) or "cypher" in question or "sql" in question


def _metric(question: str) -> str | None:
    if "unmatched" in question and "invoice" in question and ("rate" in question or "percent" in question):
        return "unmatched_invoice_rate"
    if "unmatched" in question and "invoice" in question:
        return "unmatched_invoice_count"
    if "revenue" in question:
        return "revenue"
    if "invoice" in question and any(word in question for word in ("total", "amount", "sum")):
        return "invoice_total"
    if "accuracy" in question or "correct" in question or "error rate" in question:
        return "accuracy"
    if "confidence" in question:
        return "confidence"
    if "freshness" in question or "stale" in question:
        return "data_freshness"
    if "trust" in question or "reliable" in question:
        return "source_trust"
    if "conservation" in question:
        return "conservation_status"
    if "exception" in question:
        return "exception_rate" if "rate" in question else "exception_count"
    if "decision" in question or "how many" in question or "count" in question:
        return "decision_count"
    return None


def _intent(question: str, metric: str | None) -> QueryIntent:
    if any(word in question for word in ("compare", " versus ", " vs ", "difference")):
        return QueryIntent.COMPARISON
    if any(word in question for word in ("accuracy", "correct", "error rate")):
        return QueryIntent.ACCURACY
    if any(word in question for word in ("trust", "reliable", "reliability")) and "how many" not in question:
        return QueryIntent.SOURCE_RELIABILITY
    if any(word in question for word in ("freshness", "stale", "late")):
        return QueryIntent.FRESHNESS
    if any(word in question for word in ("anomaly", "alert")):
        return QueryIntent.ANOMALY
    if any(word in question for word in ("impact", "blast radius", "downstream", "affected")):
        return QueryIntent.IMPACT
    if any(word in question for word in ("which ", "list ", "show me", "sources", "suppliers")):
        return QueryIntent.ENTITY_LISTING
    if metric is not None and any(word in question for word in ("by ", "per ", "average", "sum", "total", "count", "how many", "top")):
        return QueryIntent.AGGREGATION
    if metric is not None:
        return QueryIntent.METRIC
    return QueryIntent.UNSUPPORTED


def _dimensions(question: str) -> list[str]:
    candidates = [
        ("category", "category"),
        ("source", "source"),
        ("supplier", "supplier"),
        ("system", "system"),
        ("region", "region"),
        ("action", "action"),
        ("month", "month"),
        ("week", "week"),
    ]
    return validate_dimensions([value for marker, value in candidates if marker in question])


def _time_window(question: str) -> str | None:
    if "last month" in question:
        return "last_month"
    if "this month" in question:
        return "this_month"
    match = re.search(r"last\s+(\d+)\s+(days?|weeks?|months?)", question)
    if not match:
        return None
    unit = match.group(2)
    if not unit.endswith("s"):
        unit += "s"
    return f"last_{match.group(1)}_{unit}"


def _explicit_unsupported_metric(question: str, metric: str | None) -> bool:
    if metric is not None:
        return False
    return any(word in question for word in ("profit", "ebitda", "margin", "customer lifetime value"))


def _filter_rows(
    rows: list[dict[str, Any]],
    plan: QueryPlan,
    *,
    reference_as_of: datetime | None = None,
) -> list[dict[str, Any]]:
    if not plan.time_window:
        return rows
    now = reference_as_of or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    number_match = re.search(r"(\d+)", plan.time_window)
    number = int(number_match.group(1)) if number_match else 30
    days = 30 if plan.time_window.endswith("month") else 7 if plan.time_window.endswith("week") else number
    start = now - timedelta(days=days)
    return [row for row in rows if (timestamp := _timestamp(row)) is not None and start <= timestamp <= now]


def _aggregate(plan: QueryPlan, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    metric = plan.metric or "decision_count"
    values = [_numeric(row, metric) for row in rows]
    numeric = [value for value in values if value is not None]
    value: float | int | None
    if metric in {"decision_count", "unmatched_invoice_count", "exception_count"}:
        value = len(rows) if metric == "decision_count" else sum(1 for row in rows if _metric_matches(row, metric))
    elif metric in {"accuracy", "unmatched_invoice_rate", "exception_rate"}:
        value = _rate(rows, metric)
    else:
        value = sum(numeric) if numeric else None
    if value is None:
        return None
    return {"metric": metric, "value": value, "count": len(rows)}


def _numeric(row: Mapping[str, Any], metric: str) -> float | None:
    names = {
        "revenue": ("revenue", "amount", "value"),
        "invoice_total": ("amount", "invoice_total", "value"),
        "confidence": ("confidence",),
    }.get(metric, (metric,))
    for name in names:
        value = row.get(name)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def _rate(rows: list[dict[str, Any]], metric: str) -> float | None:
    if metric == "accuracy":
        known = [row.get("is_correct") for row in rows if isinstance(row.get("is_correct"), bool)]
        return sum(1 for value in known if value) / len(known) if known else None
    matches = sum(1 for row in rows if _metric_matches(row, "unmatched_invoice_count" if "unmatched" in metric else "exception_count"))
    return matches / len(rows) if rows else None


def _metric_matches(row: Mapping[str, Any], metric: str) -> bool:
    status = str(row.get("match_status", row.get("status", ""))).lower()
    if metric == "unmatched_invoice_count":
        return status in {"unmatched", "mismatch", "exception"}
    if metric == "exception_count":
        return bool(row.get("exception")) or status in {"exception", "failed", "error"}
    return True


def _source_usage(rows: list[dict[str, Any]], *, requested_sources: list[str]) -> list[SourceUsage]:
    counts: dict[str, int] = {}
    for row in rows:
        source_ids = row.get("source_ids")
        if isinstance(source_ids, list):
            ids = [str(value) for value in source_ids if value]
        else:
            source = row.get("source_id") or row.get("source") or "graph"
            ids = [str(source)]
        if requested_sources:
            ids = [source_id for source_id in ids if source_id in requested_sources]
        for source_id in ids or ([requested_sources[0]] if requested_sources else ["graph"]):
            counts[source_id] = counts.get(source_id, 0) + 1
    total = sum(counts.values()) or 1
    return [SourceUsage(source_id=key, records_used=value, contribution=value / total) for key, value in counts.items()]


def _profile_map(profiles: list[Any], source_ids: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for profile in profiles:
        source_id = _value(profile, "source_id", "source_name", "id")
        if source_id:
            result[str(source_id)] = profile
    for source_id in source_ids:
        result.setdefault(source_id, None)
    return result


def _alert_map(alerts: list[Any], source_ids: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for index, alert in enumerate(alerts):
        source_id = _value(alert, "source_id", "source", "id", default=source_ids[index] if index < len(source_ids) else "source")
        result[str(source_id)] = alert
    return result


def _profile_name(profile: Any, fallback: str) -> str:
    return str(_value(profile, "source", "source_name", "display_name", default=fallback))


def _trust(profile: Any) -> float:
    value = _trust_value(profile)
    return max(0.0, min(1.0, value)) if value is not None else 0.0


def _trust_value(profile: Any) -> float | None:
    if profile is None:
        return None
    value = _value(profile, "trust", "trust_score", "dk_weight", "overall_trust")
    try:
        if value is not None:
            return float(value)
        tier = _value(profile, "trust_tier")
        return tier_to_score(int(tier)) if tier is not None else None
    except (TypeError, ValueError):
        return None


def _freshness(profile: Any, data_as_of: datetime | None) -> float | None:
    value = _value(profile, "freshness_hours", "age_hours")
    if value is not None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if data_as_of is None:
        return None
    timestamp = data_as_of if data_as_of.tzinfo else data_as_of.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - timestamp).total_seconds() / 3600)


def _value(item: Any, *names: str, default: Any = None) -> Any:
    if item is None:
        return default
    if isinstance(item, Mapping):
        for name in names:
            if item.get(name) is not None:
                return item[name]
    else:
        for name in names:
            value = getattr(item, name, None)
            if value is not None:
                return value
    return default


def _timestamp(row: Mapping[str, Any]) -> datetime | None:
    value = row.get("created_at") or row.get("timestamp") or row.get("verified_at")
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _unmatched(rows: list[dict[str, Any]]) -> int:
    return sum(
        1
        for row in rows
        if str(row.get("match_status", row.get("status", ""))).lower()
        in {"unmatched", "mismatch", "variance", "blocked", "exception"}
    )


def _answer(plan: QueryPlan, result: RawQueryResult) -> str:
    aggregate = result.aggregate or {}
    value = aggregate.get("value")
    if value is None:
        return "Insufficient verified data to answer this question."
    if plan.metric in {"revenue", "invoice_total"}:
        return f"${float(value):,.0f}"
    if plan.metric in {"accuracy", "unmatched_invoice_rate", "exception_rate"}:
        return f"{float(value):.1%}"
    return f"{int(value) if float(value).is_integer() else value}"


def _evidence(plan: QueryPlan, result: RawQueryResult) -> str:
    if not result.rows:
        return "No verified records matched the request."
    unmatched = f", {result.unmatched_records} unmatched" if result.unmatched_records else ""
    return f"{result.records_scanned} governed records contributed{unmatched}."


def _path_step(plan: QueryPlan, result: RawQueryResult) -> str:
    return f"{plan.metric or 'decision_count'} → {result.aggregate.get('value') if result.aggregate else 'insufficient evidence'}"
