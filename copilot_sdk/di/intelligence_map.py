"""Data model builder for the Intelligence Map visualization."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import re
from typing import Any


@dataclass
class MapNode:
    id: str
    label: str
    domain: str
    brightness: float
    size: int
    record_count: int
    quality_score: float | None = None
    freshness_hours: float = 0.0
    quality_status: str = "healthy"
    quality_issues: list[str] = field(default_factory=list)
    status_color: str = "green"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MapEdge:
    source: str
    target: str
    thickness: float
    correlation: float
    label: str
    style: str = "solid"
    color: str = "standard"
    annual_value: float | None = None
    confidence: float | None = None
    narrative: str = ""
    weight: float = 1.0
    type: str = "correlation"
    computed: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.annual_value is not None:
            data["value"] = self.annual_value
        return data


@dataclass
class IKSBadge:
    domain: str
    score: int
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntelligenceMapData:
    nodes: list[MapNode]
    edges: list[MapEdge]
    gold_lines: list[MapEdge]
    iks_badges: list[IKSBadge]
    domain_clusters: dict[str, list[str]]
    narrative: str
    websocket_pulsing: str = "deferred to DI-7.1"
    join_keys: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "gold_lines": [line.to_dict() for line in self.gold_lines],
            "iks_badges": [badge.to_dict() for badge in self.iks_badges],
            "domain_clusters": dict(self.domain_clusters),
            "narrative": self.narrative,
            "websocket_pulsing": self.websocket_pulsing,
            "join_keys": list(self.join_keys),
        }


class IntelligenceMapBuilder:
    """Build map data from source profiles, relationships, and valuations."""

    def __init__(self) -> None:
        self._connectors: list[Any] = []
        self._connector_sources: list[dict[str, Any]] = []
        self._join_keys: list[dict[str, Any]] = []
        self._edge_weights: dict[tuple[str, str], float] = {}
        self._quality_issues: dict[str, list[str]] = {}
        self._freshness: dict[str, float] = {}
        self._enrichment_relationships: list[dict[str, Any]] = []

    def build(
        self,
        sources: list[dict[str, Any]] | None = None,
        correlations: list[dict[str, Any]] | None = None,
        valuations: list[Any] | None = None,
        iks_by_domain: dict[str, int] | None = None,
    ) -> IntelligenceMapData:
        if sources is None:
            source_rows = self._connector_sources if self._connector_sources else self._default_sources()
        else:
            source_rows = sources
        nodes = [self._node(source, index) for index, source in enumerate(source_rows)]
        edges = [self._edge(item) for item in correlations or []]
        self._apply_enrichment(nodes, edges)
        gold_lines = self.add_suggestions(valuations or [])
        badges = self.add_iks_badges(iks_by_domain or {})
        clusters = self.group_by_domain(nodes)
        narrative = self._narrative(nodes, gold_lines, badges)
        return IntelligenceMapData(nodes, edges, gold_lines, badges, clusters, narrative, join_keys=list(self._join_keys))

    def enrich_from_connectors(self, connectors: list[Any]) -> None:
        """Read connector metadata and retain it for subsequent map builds."""
        self._connectors = list(connectors)
        self._connector_sources = []
        self._enrichment_relationships = []
        for connector in self._connectors:
            to_map_nodes = getattr(connector, "to_map_nodes", None)
            if callable(to_map_nodes):
                self._connector_sources.extend(_dict_rows(to_map_nodes()))
        self.auto_discover_join_keys()
        self.compute_node_sizes()
        self.compute_edge_weights()
        self._derive_connector_relationships()
        self.apply_freshness_signals()
        self.apply_quality_overlays()

    def auto_discover_join_keys(self) -> list[dict[str, Any]]:
        """Find exact shared column names across connector metadata."""
        columns: dict[str, set[tuple[str, str]]] = {}
        for connector in self._connectors:
            rows = _connector_columns(connector)
            for row in rows:
                table = str(row.get("table_name", row.get("model_name", "")))
                column = str(row.get("column_name", row.get("name", "")))
                if table and column:
                    columns.setdefault(column.lower(), set()).add((table, column))
        discovered: list[dict[str, Any]] = []
        for normalized in sorted(columns):
            owners = sorted(columns[normalized])
            for index, (source_a, column_a) in enumerate(owners):
                for source_b, _ in owners[index + 1 :]:
                    discovered.append({
                        "source_a": source_a,
                        "source_b": source_b,
                        "column": column_a,
                        "confidence": 1.0,
                    })
        self._join_keys = discovered
        return list(discovered)

    def compute_node_sizes(self) -> None:
        """Index node sizes by Snowflake row counts."""
        for row in self._connector_sources:
            count = _int_value(row.get("row_count", row.get("record_count", row.get("size", 0))))
            row["record_count"] = count
            row["size"] = count if count > 0 else 100

    def compute_edge_weights(self) -> None:
        """Compute dependency strength, with shallow dbt dependencies strongest."""
        for connector in self._connectors:
            rows = _dependency_rows(connector)
            for row in rows:
                source = _endpoint(row, "source", "source_a", "upstream")
                target = _endpoint(row, "target", "source_b", "downstream")
                if source and target:
                    depth = max(0, _int_value(row.get("dependency_depth", row.get("depth", 0))))
                    self._edge_weights[(source.lower(), target.lower())] = 1.0 / (depth + 1.0)
                    self._enrichment_relationships.append(
                        {"source": source, "target": target, "weight": 1.0 / (depth + 1.0), "type": "dependency"}
                    )

    def _derive_connector_relationships(self) -> None:
        """Create deterministic metadata edges when connectors expose no explicit lineage."""
        rows = self._connector_sources
        for index, left in enumerate(rows):
            left_key = _logical_name(left)
            if not left_key:
                continue
            for right in rows[index + 1 :]:
                right_key = _logical_name(right)
                if left_key != right_key or str(left.get("id")) == str(right.get("id")):
                    continue
                left_id = str(left.get("id", ""))
                right_id = str(right.get("id", ""))
                if left_id and right_id:
                    self._enrichment_relationships.append(
                        {"source": left_id, "target": right_id, "weight": 0.75, "type": "dependency"}
                    )

    def apply_freshness_signals(self) -> None:
        """Set freshness hours and status colors from Airflow successful runs."""
        for connector in self._connectors:
            if str(getattr(connector, "source_name", "")).lower() != "airflow":
                continue
            for row in _freshness_rows(connector):
                name = str(row.get("dag_id", row.get("name", ""))).lower()
                if name:
                    self._freshness[f"airflow_{name}"] = _hours_since(row)

    def apply_quality_overlays(self) -> None:
        """Mark dbt models with failed tests as degraded."""
        for connector in self._connectors:
            if str(getattr(connector, "source_name", "")).lower() != "dbt":
                continue
            fetch_tests = getattr(connector, "fetch_tests", None)
            if not callable(fetch_tests):
                continue
            for row in _dict_rows(fetch_tests()):
                failures = _int_value(row.get("failures", 0))
                if str(row.get("status", "")).lower() in {"error", "fail", "failed"} or failures > 0:
                    model = str(row.get("model_name", ""))
                    if model:
                        self._quality_issues.setdefault(f"dbt_{model}".lower(), []).append(
                            str(row.get("test_name", "dbt test failed"))
                        )

    def _apply_enrichment(self, nodes: list[MapNode], edges: list[MapEdge]) -> None:
        if not self._connectors:
            return
        known = {node.id for node in nodes}
        for relationship in self._enrichment_relationships:
            source = _find_node_id(known, str(relationship.get("source", "")))
            target = _find_node_id(known, str(relationship.get("target", "")))
            if source and target and source != target and not any(
                edge.source == source and edge.target == target for edge in edges
            ):
                weight = float(relationship.get("weight", 1.0) or 1.0)
                edges.append(
                    MapEdge(
                        source,
                        target,
                        max(1.0, weight * 4.0),
                        weight,
                        "connector metadata",
                        weight=weight,
                        type=str(relationship.get("type", "dependency")),
                    )
                )
        for node in nodes:
            issues = sorted(set(self._quality_issues.get(node.id, [])))
            node.quality_issues = issues
            if issues:
                node.quality_status = "degraded"
                node.status_color = "red"
            hours = self._freshness.get(node.id)
            if hours is not None:
                node.freshness_hours = hours
                if hours > 24 and not issues:
                    node.quality_status = "stale"
                    node.status_color = "red"
                elif not issues:
                    node.status_color = "green"
        for edge in edges:
            edge_key = (edge.source.lower(), edge.target.lower())
            if edge_key in self._edge_weights:
                edge.weight = self._edge_weights[edge_key]
                edge.type = "dependency"
        for join_key in self._join_keys:
            source_a = _find_node_id(known, join_key["source_a"])
            source_b = _find_node_id(known, join_key["source_b"])
            if source_a and source_b:
                edges.append(MapEdge(source_a, source_b, 2.0, 1.0, join_key["column"], weight=1.0, type="join_key"))

    def discover_combinations(self) -> list[dict[str, Any]]:
        """Return deterministic demo combinations for the standalone DI endpoint."""
        return [
            {
                "source_a": "orders",
                "source_b": "etl_orders",
                "correlation_strength": 0.87,
                "value_estimate_annual": 180000.0,
                "description": "Customer orders plus pipeline reliability improves churn prediction.",
                "status": "discovered",
            }
        ]

    def _default_sources(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "orders",
                "name": "orders",
                "domain": "dataops",
                "source_reliability": 0.94,
                "record_count": 120000,
            },
            {
                "id": "etl_orders",
                "name": "etl_orders",
                "domain": "dataops",
                "source_reliability": 0.82,
                "record_count": 30000,
            },
        ]

    def add_suggestions(self, valuations: list[Any]) -> list[MapEdge]:
        lines = []
        for valuation in valuations:
            item = _as_dict(valuation)
            value = float(item.get("annual_value") or 0.0)
            factor_a = str(item.get("factor_a") or item.get("source_a") or "source_a")
            factor_b = str(item.get("factor_b") or item.get("source_b") or "source_b")
            lines.append(
                MapEdge(
                    factor_a,
                    factor_b,
                    max(1.0, min(value / 50000.0, 8.0)),
                    float(item.get("confidence") or 0.0),
                    f"${_money(value)}/year",
                    "dotted",
                    "gold",
                    value,
                    float(item.get("confidence") or 0.0),
                    str(item.get("narrative") or f"Connect {factor_b} to improve {factor_a}."),
                    computed=bool(item.get("computed", item.get("computed_value_annual") is not None)),
                )
            )
        return lines

    def add_iks_badges(self, iks_by_domain: dict[str, int]) -> list[IKSBadge]:
        return [
            IKSBadge(domain, int(score), _iks_status(int(score)))
            for domain, score in sorted(iks_by_domain.items())
        ]

    def group_by_domain(self, nodes: list[MapNode]) -> dict[str, list[str]]:
        clusters: dict[str, list[str]] = {}
        for node in nodes:
            clusters.setdefault(node.domain, []).append(node.id)
        return clusters

    def _node(self, source: dict[str, Any], index: int) -> MapNode:
        quality = _optional_float(source.get("quality_score", source.get("overall_quality")))
        trust = _optional_float(source.get("source_reliability", source.get("trust", quality)))
        records = int(source.get("record_count", source.get("records", 0)) or 0)
        label = str(source.get("name", source.get("source_name", f"source-{index + 1}")))
        return MapNode(
            str(source.get("id", label)).replace(" ", "_").lower(),
            label,
            str(source.get("domain", "dataops")),
            max(0.25, min(trust if trust is not None else 0.5, 1.0)),
            records if records > 0 else 100,
            max(records, 0),
            quality,
        )

    def _edge(self, item: dict[str, Any]) -> MapEdge:
        correlation = abs(float(item.get("correlation", 0.0) or 0.0))
        depth = item.get("dependency_depth", item.get("depth"))
        dependency = depth is not None
        weight = 1.0 / (max(0, _int_value(depth)) + 1.0) if dependency else (correlation or 1.0)
        return MapEdge(
            str(item.get("source", item.get("source_a", ""))),
            str(item.get("target", item.get("source_b", ""))),
            max(1.0, min(correlation * 8.0, 8.0)),
            correlation,
            str(item.get("label", f"{round(correlation * 100)}% relationship")),
            weight=weight,
            type="dependency" if dependency else "correlation",
        )

    def _narrative(self, nodes: list[MapNode], gold_lines: list[MapEdge], badges: list[IKSBadge]) -> str:
        if gold_lines:
            best = max(gold_lines, key=lambda item: item.annual_value or 0.0)
            return f"Intelligence Map found {len(gold_lines)} suggested data connections. Top value: {best.source} x {best.target}, {best.label}."
        return f"Intelligence Map contains {len(nodes)} source nodes and {len(badges)} IKS badges."


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        result = value.to_dict()
        return result if isinstance(result, dict) else {}
    result = asdict(value) if hasattr(value, "__dataclass_fields__") else {}
    return result if isinstance(result, dict) else {}


def _optional_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _iks_status(score: int) -> str:
    if score >= 70:
        return "mature"
    if score >= 30:
        return "developing"
    return "learning"


def _money(value: float) -> str:
    if abs(value) >= 1000:
        return f"{round(value / 1000)}K"
    return f"{round(value):,}"


def _dict_rows(value: Any) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _int_value(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _connector_columns(connector: Any) -> list[dict[str, Any]]:
    fetch_all = getattr(connector, "fetch_all_columns", None)
    if callable(fetch_all):
        return _dict_rows(fetch_all())
    rows: list[dict[str, Any]] = []
    for source in _dict_rows(getattr(connector, "to_map_nodes", lambda: [])()):
        for column in source.get("columns", []) if isinstance(source.get("columns"), list) else []:
            if isinstance(column, str):
                rows.append({"table_name": source.get("name"), "column_name": column})
            elif isinstance(column, dict):
                rows.append({"table_name": source.get("name"), **column})
    return rows


def _dependency_rows(connector: Any) -> list[dict[str, Any]]:
    for method_name in ("fetch_dependencies", "fetch_lineage", "dependencies"):
        value = getattr(connector, method_name, None)
        if callable(value):
            return _dict_rows(value())
        if isinstance(value, list):
            return _dict_rows(value)
    return []


def _endpoint(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        if row.get(key):
            return str(row[key])
    return ""


def _freshness_rows(connector: Any) -> list[dict[str, Any]]:
    fetch_freshness = getattr(connector, "fetch_freshness", None)
    if callable(fetch_freshness):
        return _dict_rows(fetch_freshness())
    fetch = getattr(connector, "fetch", None)
    runs = _dict_rows(fetch("all") if callable(fetch) else [])
    by_dag: dict[str, dict[str, Any]] = {}
    for row in runs:
        if str(row.get("state", "")).lower() != "success":
            continue
        dag = str(row.get("dag_id", ""))
        if dag and str(row.get("execution_date", "")) > str(by_dag.get(dag, {}).get("execution_date", "")):
            by_dag[dag] = row
    return list(by_dag.values())


def _hours_since(row: dict[str, Any]) -> float:
    if row.get("hours_since_run") is not None:
        try:
            return max(0.0, float(row["hours_since_run"]))
        except (TypeError, ValueError):
            pass
    raw = row.get("last_successful_run", row.get("last_run", row.get("end_date", row.get("execution_date"))))
    if not raw:
        return 0.0
    try:
        timestamp = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - timestamp).total_seconds() / 3600.0)
    except (TypeError, ValueError):
        return 0.0


def _find_node_id(known: set[str], source: str) -> str:
    normalized = source.replace(" ", "_").lower()
    for candidate in (normalized, f"snowflake_{normalized}", f"dbt_{normalized}", f"airflow_{normalized}"):
        if candidate in known:
            return candidate
    return ""


def normalize_suggestion_id(value: Any) -> str:
    """Return a stable node ID for a catalog provider or data type."""
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value or "").casefold()).strip("_")
    return normalized or "suggested_source"


def enrich_payload_with_suggestions(
    payload: dict[str, Any], valuations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Add suggested catalog nodes and connect each computed gold line to them."""
    nodes = payload.setdefault("nodes", [])
    existing_ids = {str(node.get("id")) for node in nodes if isinstance(node, dict)}
    gold_lines: list[dict[str, Any]] = []
    for item in valuations:
        raw_catalog = item.get("catalog_entry")
        catalog: dict[str, Any] = raw_catalog if isinstance(raw_catalog, dict) else {}
        provider_id = str(catalog.get("provider_id") or item.get("provider_id") or item.get("provider") or item.get("source_name", ""))
        provider_label = str(catalog.get("provider_name") or item.get("source_name") or provider_id)
        data_type = str(item.get("signal") or catalog.get("data_type") or "external_data")
        source_id = normalize_suggestion_id(provider_id)
        target_id = normalize_suggestion_id(data_type)
        _append_suggested_node(nodes, existing_ids, source_id, provider_label)
        _append_suggested_node(nodes, existing_ids, target_id, data_type)
        gold_lines.append(
            {
                "source": source_id,
                "target": target_id,
                "value": float(item.get("computed_value_annual", item.get("annual_value", 0.0)) or 0.0),
                "computed": True,
                "type": "suggested",
            }
        )
    payload["gold_lines"] = gold_lines
    return payload


def _append_suggested_node(
    nodes: list[Any], existing_ids: set[str], node_id: str, label: str,
) -> None:
    if node_id in existing_ids:
        return
    nodes.append(
        {
            "id": node_id,
            "label": label,
            "name": label,
            "domain": "external",
            "type": "suggested",
            "trust": None,
            "brightness": 0.0,
            "size": 0,
            "record_count": 0,
            "quality_status": "external",
            "quality_issues": [],
        }
    )
    existing_ids.add(node_id)


def _logical_name(row: dict[str, Any]) -> str:
    raw = str(row.get("name", row.get("source_name", row.get("table_name", row.get("model_name", "")))).casefold())
    if not raw:
        return ""
    return re.sub(r"^(stg|int|fct|dim|rpt|etl|sync)_", "", raw)
