"""Pattern-based natural language routing for Data Intelligence queries."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from copilot_sdk.di.query_patterns import QueryPattern, default_patterns


class NLQueryRouter:
    """Route natural-language questions to deterministic graph query templates."""

    def __init__(self, patterns: Sequence[QueryPattern] | None = None) -> None:
        self._patterns = sorted(
            list(patterns) if patterns is not None else default_patterns(),
            key=lambda pattern: pattern.priority,
            reverse=True,
        )

    def query(
        self, question: str, graph_store: Any, domain: str | None = None
    ) -> dict[str, Any]:
        normalized = str(question or "").strip()
        if not normalized:
            return {
                "intent": "unknown",
                "answer": "Ask a DataOps question to query the graph.",
                "evidence": [],
            }
        intent = self._classify_intent(normalized)
        return self._execute(intent, normalized, graph_store, domain=domain)

    def _classify_intent(self, question: str) -> str:
        lowered = question.lower()
        aggregation_terms = ("average", "avg", "mean", "count", "sum", "total", "max", "min", " by ")
        confidence_as_aggregation = "confidence" in lowered and any(term in lowered for term in aggregation_terms)
        if any(term in lowered for term in ("confidence", "trust", "reliable", "reliability")) and not confidence_as_aggregation:
            return "source_reliability"
        if any(term in lowered for term in ("fresh", "freshness", "stale", "late")):
            return "freshness"
        if any(term in lowered for term in ("recurring", "recurrence", "repeat", "again")):
            return "recurrence"
        if any(term in lowered for term in ("impact", "blast", "downstream", "affected")):
            return "impact"
        if any(term in lowered for term in ("metric", "revenue", "answer", "how much", "what was")):
            return "metric"
        return "unknown"

    def _execute(
        self, intent: str, question: str, graph_store: Any, *, domain: str | None = None
    ) -> dict[str, Any]:
        if intent == "unknown":
            decisions = _decisions(graph_store, domain=domain)
            for pattern in self._patterns:
                if pattern.matches(question):
                    return pattern.execute(question, decisions).to_response()
            return _unknown_response(intent)

        decisions = _decisions(graph_store, domain=domain)
        evidence = _evidence_for_intent(intent, decisions)
        answer = _answer(intent, evidence, question)
        return {
            "intent": intent,
            "answer": answer,
            "evidence": evidence,
            "query_template": _query_template(intent, domain=domain),
        }


def _decisions(graph_store: Any, *, domain: str | None = None) -> list[dict[str, Any]]:
    if isinstance(graph_store, (list, tuple)):
        return [row for row in graph_store if isinstance(row, dict)]
    if graph_store is None:
        return []
    for method_name in ("get_verified_decisions", "get_all_decisions"):
        method = getattr(graph_store, method_name, None)
        if not callable(method):
            continue
        try:
            rows = method(domain or "dataops")
        except TypeError:
            rows = method()
        except Exception:
            rows = []
        if rows:
            return [row for row in rows if isinstance(row, dict)]
    return []


def _unknown_response(intent: str = "unknown") -> dict[str, Any]:
    return {
        "intent": intent,
        "answer": "I could not map that question to a DataOps graph query template.",
        "evidence": [],
    }


def _evidence_for_intent(intent: str, decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [_decision_payload(row) for row in decisions[-5:]]
    for row in rows:
        row["matched_intent"] = intent
    return rows


def _decision_payload(decision: dict[str, Any]) -> dict[str, Any]:
    raw_metadata = decision.get("metadata")
    metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
    raw_factors = decision.get("factors")
    factors: dict[str, Any] = raw_factors if isinstance(raw_factors, dict) else {}
    return {
        "decision_id": str(decision.get("decision_id") or metadata.get("decision_id") or ""),
        "category": str(decision.get("category") or metadata.get("category") or ""),
        "source_ids": _source_ids(decision, metadata),
        "confidence": _safe_float(decision.get("confidence"), default=None),
        "factors": {
            key: _safe_float(value, default=0.0)
            for key, value in factors.items()
            if isinstance(value, (int, float))
        },
    }


def _source_ids(decision: dict[str, Any], metadata: dict[str, Any]) -> list[str]:
    raw = decision.get("source_ids") or metadata.get("source_ids")
    if isinstance(raw, list):
        return [str(item) for item in raw]
    source = decision.get("source_id") or metadata.get("source_id") or metadata.get("seed_id")
    return [str(source)] if source else []


def _answer(intent: str, evidence: list[dict[str, Any]], question: str) -> str:
    if not evidence:
        return f"No graph evidence is available yet for {intent}."
    return (
        f"Matched {intent} for '{question}'. "
        f"Found {len(evidence)} evidence item(s) in the DataOps graph."
    )


def _query_template(intent: str, *, domain: str | None = None) -> str:
    templates = {
        "source_reliability": "MATCH (s:Source)-[:EMITS]->(d:Decision) RETURN s, d",
        "freshness": "MATCH (d:Decision) WHERE d.data_freshness IS NOT NULL RETURN d",
        "recurrence": "MATCH (d:Decision) WHERE d.recurrence_frequency IS NOT NULL RETURN d",
        "impact": "MATCH (d:Decision)-[:AFFECTS]->(s:System) RETURN d, s",
        "metric": "MATCH (d:Decision) RETURN d",
    }
    template = templates[intent]
    if domain is None or "Decision" not in template:
        return template
    safe_domain = str(domain).replace("\\", "\\\\").replace("'", "\\'")
    predicate = f"d.domain = '{safe_domain}'"
    if " WHERE " in template:
        return template.replace(" WHERE ", f" WHERE {predicate} AND ", 1)
    if " RETURN " in template:
        return template.replace(" RETURN ", f" WHERE {predicate} RETURN ", 1)
    return template


def _safe_float(value: Any, *, default: float | None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
