"""Closed, read-only AGE projections for compatibility consumers."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from ci_platform.graph.age_client import AGEClient
from ci_platform.graph.agtype import normalize_agtype_value
from copilot_sdk.config import GraphConfig


_SAFE_DOMAIN_RE = re.compile(r"^[a-zA-Z0-9_-]{1,200}$")
_MUTATION_VERBS = (
    "CREATE", "SET", "DELETE", "DETACH", "M" + "ERGE", "REMOVE", "DROP", "ALTER", "INSERT", "UPDATE", "TRUNCATE"
)
_MUTATION_RE = re.compile(r"\b(" + "|".join(_MUTATION_VERBS) + r")\b", re.IGNORECASE)


@dataclass(frozen=True)
class ProjectionPattern:
    """One documented, read-only AGE projection pattern."""

    description: str
    query_template: str
    returns: tuple[str, ...]


class ProjectionRegistry:
    """Closed registry of read-only AGE projection patterns."""

    PATTERNS: Mapping[str, ProjectionPattern] = MappingProxyType(
        {
            "decision_verified": ProjectionPattern(
                "Verified decisions with the D2 predicate",
                "MATCH (d:Decision) WHERE <d2> RETURN d",
                ("decision_id", "domain", "category", "status", "confidence"),
            ),
            "decision_with_outcome": ProjectionPattern(
                "Decisions with embedded or canonical Outcome data",
                "MATCH (d:Decision) OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o:Outcome) RETURN d, o",
                ("decision_id", "actual_action", "is_correct", "verified_at"),
            ),
            "factor_vector": ProjectionPattern(
                "Factor-vector projection from Decision properties",
                "MATCH (d:Decision) WHERE d.factor_vector IS NOT NULL RETURN d",
                ("decision_id", "factor_vector", "factor_names"),
            ),
            "count_verified": ProjectionPattern(
                "D2 verified count by domain",
                "MATCH (d:Decision) WHERE <d2> RETURN count(DISTINCT d.decision_id)",
                ("count",),
            ),
            "count_correct": ProjectionPattern(
                "D2 correct count by domain",
                "MATCH (d:Decision) WHERE <d2-correct> RETURN count(DISTINCT d.decision_id)",
                ("count",),
            ),
            "profile_snapshot": ProjectionPattern(
                "Category counts and correct-count inputs for a profile snapshot",
                "MATCH (d:Decision) WHERE <d2> RETURN d.category, count(d)",
                ("category", "verified_count", "correct_count"),
            ),
        }
    )


def parse_projection_json(value: Any) -> Any:
    """Parse AGE JSON-like string values while leaving scalar values intact."""
    value = normalize_agtype_value(value)
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def normalize_projection_node(value: Any) -> dict[str, Any]:
    """Return normalized AGE node properties as a plain dictionary."""
    normalized = normalize_agtype_value(value)
    return dict(normalized) if isinstance(normalized, Mapping) else {}


def project_decision(decision: Mapping[str, Any], *, default_domain: str) -> dict[str, Any]:
    """Project legacy or canonical Decision properties into common fields."""
    return {
        "decision_id": decision.get("decision_id") or decision.get("id") or decision.get("alert_id"),
        "domain": decision.get("domain") or default_domain,
        "category": decision.get("category") or decision.get("alert_category"),
        "recommended_action": decision.get("recommended_action") or decision.get("action") or decision.get("outcome"),
        "status": decision.get("status"),
        "confidence": decision.get("confidence"),
        "created_at": decision.get("created_at") or decision.get("timestamp") or decision.get("timestamp_epoch"),
    }


def project_outcome(decision: Mapping[str, Any], outcome: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Merge canonical Outcome data with SOC's legacy embedded properties."""
    outcome = outcome or {}
    correct = outcome.get("is_correct", decision.get("correct"))
    if correct is True:
        status = "confirmed"
    elif correct is False:
        status = "overridden"
    else:
        status = "verified"
    return {
        "actual_action": outcome.get("actual_action", decision.get("outcome")),
        "actual_index": outcome.get("actual_index"),
        "is_correct": correct,
        "verified_at": outcome.get("verified_at", decision.get("verified_at")),
        "status": status,
    }


def project_factor_vector(
    decision: Mapping[str, Any],
    *,
    factor_names: list[str],
    factor_schema_version: str,
    factor_names_hash: str,
) -> dict[str, Any]:
    """Project embedded vectors with caller-owned, ordered schema metadata."""
    vector = parse_projection_json(decision.get("factor_vector"))
    if not isinstance(vector, list) or not vector or not all(isinstance(value, (int, float)) for value in vector):
        raise ValueError("Decision.factor_vector must be a non-empty numeric list")
    if len(vector) != len(factor_names):
        raise ValueError("Decision.factor_vector length does not match factor_names")
    graph_factor_names = parse_projection_json(decision.get("factor_names"))
    if graph_factor_names is not None and graph_factor_names != factor_names:
        raise ValueError("Decision.factor_names conflicts with projection schema")
    graph_schema_version = decision.get("factor_schema_version")
    if graph_schema_version is not None and graph_schema_version != factor_schema_version:
        raise ValueError("Decision.factor_schema_version conflicts with projection schema")
    graph_hash = decision.get("factor_names_hash")
    if graph_hash is not None and graph_hash != factor_names_hash:
        raise ValueError("Decision.factor_names_hash conflicts with projection schema")
    return {
        "factor_names": list(factor_names),
        "factor_schema_version": factor_schema_version,
        "shape": [len(factor_names)],
        "factor_names_hash": factor_names_hash,
        "values": vector,
    }


def first_present(node: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    """Return the first non-empty compatibility property from a node."""
    for key in keys:
        value = node.get(key)
        if value not in (None, ""):
            return value
    return None


def normalize_domain(value: Any) -> str | None:
    """Normalize an optional domain value without inventing a partition."""
    if value is None:
        return None
    normalized = str(value).strip().lower()
    return normalized or None


def classify_domain_context(
    node: Mapping[str, Any],
    label: str,
    *,
    allowed_domains: set[str],
) -> dict[str, Any]:
    """Classify context as canonical only when its partition provenance is explicit."""
    explicit_domain = normalize_domain(first_present(node, ("domain", "source_domain", "owner_domain")))
    entity_type = first_present(node, ("entity_type", "system_type", "node_type", "type"))
    stable_key = first_present(
        node,
        ("data_quality_alert_id", "alert_id", "pipeline_id", "system_id", "entity_id", "id", "name"),
    )
    provenance = first_present(
        node,
        ("owner_copilot", "created_by", "source_domain", "owner_domain", "producer", "source_system"),
    )
    if explicit_domain in allowed_domains and entity_type and stable_key and provenance:
        return {
            "status": "canonical_domain_context",
            "domain": explicit_domain,
            "entity_type": str(entity_type),
            "natural_key": str(stable_key),
            "label": label,
            "is_soc_alert_context": False,
        }
    return {
        "status": "blocked_unpartitioned_context",
        "domain": explicit_domain,
        "entity_type": str(entity_type) if entity_type else None,
        "natural_key": str(stable_key) if stable_key else None,
        "label": label,
        "is_soc_alert_context": False,
    }


class AGEProjection:
    """Read-only projection from a shared AGE graph for one safe domain."""

    def __init__(self, dsn: str | None = None, graph_name: str | None = None, domain: str = "") -> None:
        if not _SAFE_DOMAIN_RE.fullmatch(domain):
            raise ValueError(f"unsupported graph domain: {domain}")
        if dsn is None or graph_name is None:
            config = GraphConfig.load(domain)
            dsn = dsn or config.dsn
            graph_name = graph_name or config.graph
        if not dsn or not graph_name:
            raise ValueError(f"GraphConfig for {domain!r} must provide DSN and graph name")
        self.dsn = dsn
        self.graph_name = graph_name
        self.domain = domain
        self._client = AGEClient(dsn=dsn, graph_name=graph_name)

    def _query(self, cypher: str) -> list[dict[str, Any]]:
        if _MUTATION_RE.search(cypher):
            raise ValueError("AGEProjection permits read-only Cypher only")
        return asyncio.run(self._client.run_query(cypher, None))

    def _d2_where(self, alias: str = "d") -> str:
        domain = AGEClient.serialize_for_age(self.domain)
        return (
            f"{alias}.domain = {domain} "
            f"AND ({alias}.archived IS NULL OR {alias}.archived <> true) "
            "AND ("
            f"({alias}.status IS NOT NULL AND {alias}.status IN ['confirmed', 'overridden']) "
            f"OR ({alias}.status IS NULL AND {alias}.outcome IS NOT NULL)"
            ")"
        )

    def count_verified(self) -> int:
        """Return the D2 verified count scoped to this projection's domain."""
        rows = self._query(
            f"MATCH (d:Decision) WHERE {self._d2_where()} RETURN count(DISTINCT d.decision_id) AS cnt"
        )
        return int(parse_projection_json(rows[0].get("cnt", 0))) if rows else 0

    def count_correct(self) -> int:
        """Return D2-correct decisions, using canonical or legacy outcome data."""
        domain = AGEClient.serialize_for_age(self.domain)
        rows = self._query(
            "MATCH (d:Decision) "
            "OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o:Outcome) "
            f"WHERE d.domain = {domain} "
            "AND (d.archived IS NULL OR d.archived <> true) "
            "AND ((d.status IS NOT NULL AND d.status IN ['confirmed', 'overridden'] AND o.is_correct = true) "
            "OR (d.status IS NULL AND d.correct = true)) "
            "RETURN count(DISTINCT d.decision_id) AS cnt"
        )
        return int(parse_projection_json(rows[0].get("cnt", 0))) if rows else 0

    def get_verified_decisions(self, limit: int = 400) -> list[dict[str, Any]]:
        """Return D2-matching Decisions with canonical and embedded outcome fields merged."""
        if limit < 1 or limit > 10_000:
            raise ValueError("limit must be between 1 and 10000")
        rows = self._query(
            "MATCH (d:Decision) "
            f"WHERE {self._d2_where()} "
            "OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o:Outcome) "
            f"RETURN d, o ORDER BY d.created_at LIMIT {limit}"
        )
        projected: list[dict[str, Any]] = []
        for row in rows:
            decision = normalize_projection_node(row.get("d"))
            outcome = normalize_projection_node(row.get("o"))
            projected.append(
                {
                    **project_decision(decision, default_domain=self.domain),
                    **project_outcome(decision, outcome),
                }
            )
        return projected

    def get_category_breakdown(self) -> dict[str, dict[str, int]]:
        """Return verified and correct totals grouped by category."""
        breakdown: dict[str, dict[str, int]] = {}
        for decision in self.get_verified_decisions(limit=10_000):
            category = decision.get("category")
            if not category:
                continue
            bucket = breakdown.setdefault(str(category), {"verified_count": 0, "correct_count": 0})
            bucket["verified_count"] += 1
            if decision.get("is_correct") is True:
                bucket["correct_count"] += 1
        return breakdown

    def get_profile_snapshot(self) -> dict[str, Any]:
        """Return the read-only count and category inputs used by SOC startup."""
        return {
            "domain": self.domain,
            "verified_count": self.count_verified(),
            "correct_count": self.count_correct(),
            "category_breakdown": self.get_category_breakdown(),
        }
