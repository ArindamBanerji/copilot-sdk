"""Read-only DataOps investigation patterns."""

from __future__ import annotations

import inspect
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, cast

import numpy as np

FACTOR_NAMES = (
    "impact_scope",
    "source_reliability",
    "recurrence_frequency",
    "downstream_urgency",
    "data_freshness",
    "business_criticality",
)

DATAOPS_PATTERN_CATEGORIES = (
    "source_failure",
    "schema_impact",
    "quality_drift",
    "cross_system",
    "known_pattern",
)

CONTRACT_NODE_TYPES = {
    "Alert",
    "Pipeline",
    "Dataset",
    "QualityRule",
    "ProcessModel",
    "Activity",
    "Transformation",
    "Decision",
}

CONTRACT_EDGE_TYPES = {
    "DETECTED_IN",
    "CONSUMES",
    "PRODUCES",
    "MONITORS",
    "CONTAINS",
    "FOLLOWS",
    "TRIGGERED_BY",
    "DECIDED_ON",
}


class InvestigationPattern(Protocol):
    category_name: str
    pattern_name: str
    selected_edge: str
    enriched_factors: tuple[str, ...]
    candidate_read: str
    graph_query: str

    async def execute(self, alert: dict[str, Any], graph_store: Any) -> dict[str, Any]:
        ...

    def evidence_keys(self) -> list[str]:
        ...

    def evidence_vector(self, evidence: dict[str, Any]) -> np.ndarray:
        ...


class DataOpsPatternBase:
    category_name = ""
    pattern_name = ""
    selected_edge = "DETECTED_IN"
    enriched_factors: tuple[str, ...] = ()
    candidate_read = ""
    graph_query = ""
    read_cost = 1.0

    def __init__(self, data_dir: str | Path | None = None) -> None:
        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[2] / "data"
        self.data_dir = Path(data_dir)

    @property
    def category(self) -> str:
        return self.category_name

    def evidence_keys(self) -> list[str]:
        raise NotImplementedError

    async def execute(self, alert: dict[str, Any], graph_store: Any) -> dict[str, Any]:
        raise NotImplementedError

    def evidence_vector(self, evidence: dict[str, Any]) -> np.ndarray:
        vector = np.zeros(len(FACTOR_NAMES), dtype=np.float64)
        supplied = evidence.get("vld_factor_vector")
        if isinstance(supplied, list) and len(supplied) == len(FACTOR_NAMES):
            return cast(np.ndarray, np.asarray(supplied, dtype=np.float64))
        for factor in self.enriched_factors:
            if factor in FACTOR_NAMES:
                vector[FACTOR_NAMES.index(factor)] = float(evidence.get(factor, 0.0) or 0.0)
        return cast(np.ndarray, np.clip(vector, 0.0, 1.0))

    def _base_evidence(self, alert: dict[str, Any], evidence: dict[str, Any], vector: list[float]) -> dict[str, Any]:
        keys = self.evidence_keys()
        return {
            **evidence,
            "evidence_keys": keys,
            "investigation_category": self.category_name,
            "investigation_pattern": self.pattern_name,
            "traversal": self.graph_query,
            "selected_edge": self.selected_edge,
            "candidate_read": self.candidate_read,
            "candidate_reads": [self.candidate_read],
            "enriched_factors": list(self.enriched_factors),
            "read_cost": self.read_cost,
            "schema_source": "DataOps graph contract plus fixture-backed relationships",
            "alert_id": _alert_id(alert),
            "vld_factor_vector": [float(x) for x in np.clip(vector, 0.0, 1.0)],
        }


class UpstreamSourcePattern(DataOpsPatternBase):
    category_name = "source_failure"
    pattern_name = "upstream_source"
    selected_edge = "DETECTED_IN"
    enriched_factors: tuple[str, ...] = ("source_reliability", "data_freshness")
    candidate_read = "pipeline.upstream"
    graph_query = "Alert-[:DETECTED_IN]->Pipeline, then fixture upstream dependencies"

    def evidence_keys(self) -> list[str]:
        return ["upstream_system_status", "dependency_chain_depth", "last_healthy_timestamp"]

    async def execute(self, alert: dict[str, Any], graph_store: Any) -> dict[str, Any]:
        pipelines = await _pipelines(graph_store, self.data_dir)
        system = _system(alert)
        pipeline = pipelines.get(system, {})
        upstream = list(pipeline.get("upstream") or [])
        status = "ok"
        if any((pipelines.get(name, {}).get("status") in {"critical", "degraded"}) for name in upstream):
            status = "degraded"
        last_healthy = _latest_timestamp(
            [pipelines.get(name, {}).get("last_run") for name in upstream]
            + [pipeline.get("last_run")]
        )
        depth = _dependency_depth(system, pipelines, direction="upstream")
        vector = _factor_vector(alert)
        vector[FACTOR_NAMES.index("source_reliability")] = min(
            vector[FACTOR_NAMES.index("source_reliability")], 0.95 if status == "ok" else 0.35
        )
        vector[FACTOR_NAMES.index("data_freshness")] = min(
            vector[FACTOR_NAMES.index("data_freshness")], 0.85 if status == "ok" else 0.4
        )
        return self._base_evidence(
            alert,
            {
                "upstream_system_status": status,
                "dependency_chain_depth": depth,
                "last_healthy_timestamp": last_healthy or "unknown",
                "upstream_systems": upstream,
            },
            vector,
        )


class SchemaChangePattern(DataOpsPatternBase):
    category_name = "schema_impact"
    pattern_name = "schema_change"
    selected_edge = "CONSUMES"
    enriched_factors: tuple[str, ...] = ("impact_scope", "downstream_urgency", "business_criticality")
    candidate_read = "schema_changes.by_system"
    graph_query = "Alert-[:DETECTED_IN]->Pipeline-[:CONSUMES|PRODUCES]->Dataset plus schema_changes fixture"
    read_cost = 1.2

    def evidence_keys(self) -> list[str]:
        return ["schema_change_type", "affected_columns", "join_fanout_factor", "days_since_change"]

    async def execute(self, alert: dict[str, Any], graph_store: Any) -> dict[str, Any]:
        change = _schema_change_for_alert(alert, self.data_dir)
        changed_at = str(change.get("detected") or "")
        days = _days_since(changed_at, "2026-05-20T00:00:00Z")
        fanout = float(change.get("downstream_impact") or _root_cause(alert).get("fanout_multiplier") or 1.0)
        impacted = list(change.get("impacted_systems") or [])
        vector = _factor_vector(alert)
        vector[FACTOR_NAMES.index("impact_scope")] = max(vector[FACTOR_NAMES.index("impact_scope")], min(1.0, fanout / 10.0))
        vector[FACTOR_NAMES.index("downstream_urgency")] = max(
            vector[FACTOR_NAMES.index("downstream_urgency")], min(1.0, len(impacted) / 8.0)
        )
        vector[FACTOR_NAMES.index("business_criticality")] = max(
            vector[FACTOR_NAMES.index("business_criticality")], 0.9 if fanout >= 4 else 0.65
        )
        return self._base_evidence(
            alert,
            {
                "schema_change_type": str(change.get("change_type") or _root_cause(alert).get("change_type") or "unknown"),
                "affected_columns": [str(change.get("column") or _root_cause(alert).get("field") or "unknown")],
                "join_fanout_factor": fanout,
                "days_since_change": days,
                "impacted_systems": impacted,
                "proposed_fix": change.get("proposed_fix"),
            },
            vector,
        )


class DataQualityPattern(DataOpsPatternBase):
    category_name = "quality_drift"
    pattern_name = "data_quality"
    selected_edge = "MONITORS"
    enriched_factors: tuple[str, ...] = ("impact_scope", "source_reliability", "data_freshness")
    candidate_read = "pipeline.quality_rules"
    graph_query = "Alert-[:DETECTED_IN]->Pipeline<-[:MONITORS]-QualityRule plus historical alert recurrence"

    def evidence_keys(self) -> list[str]:
        return ["validation_rule_name", "violation_rate", "baseline_rate", "drift_magnitude"]

    async def execute(self, alert: dict[str, Any], graph_store: Any) -> dict[str, Any]:
        recurrence = await _recurrence(graph_store, alert, self.data_dir)
        factors = _factors(alert)
        recurrence_value = float(recurrence.get("recurrence_frequency") or recurrence.get("value") or factors.get("recurrence_frequency") or 0.0)
        severity_boost = 0.08 if str(alert.get("severity") or "").lower() == "critical" else 0.04
        baseline = max(0.02, min(0.2, recurrence_value / 4.0))
        violation = min(1.0, baseline + max(0.08, recurrence_value / 2.0) + severity_boost)
        drift = max(0.0, violation - baseline)
        vector = _factor_vector(alert)
        vector[FACTOR_NAMES.index("source_reliability")] = min(vector[FACTOR_NAMES.index("source_reliability")], max(0.05, 1.0 - violation))
        vector[FACTOR_NAMES.index("data_freshness")] = min(vector[FACTOR_NAMES.index("data_freshness")], max(0.05, 1.0 - drift))
        return self._base_evidence(
            alert,
            {
                "validation_rule_name": _quality_rule_name(alert),
                "violation_rate": round(violation, 4),
                "baseline_rate": round(baseline, 4),
                "drift_magnitude": round(drift, 4),
            },
            vector,
        )


class BlastRadiusPattern(DataOpsPatternBase):
    category_name = "cross_system"
    pattern_name = "blast_radius"
    selected_edge = "DETECTED_IN"
    enriched_factors: tuple[str, ...] = ("impact_scope", "downstream_urgency", "business_criticality")
    candidate_read = "pipeline.downstream"
    graph_query = "Alert-[:DETECTED_IN]->Pipeline, then fixture downstream dependency tree"
    read_cost = 1.1

    def evidence_keys(self) -> list[str]:
        return ["affected_systems_count", "critical_systems", "estimated_impact_hours"]

    async def execute(self, alert: dict[str, Any], graph_store: Any) -> dict[str, Any]:
        blast = await _blast_radius(graph_store, alert, self.data_dir)
        systems = _flatten_blast_systems(blast)
        pipelines = await _pipelines(graph_store, self.data_dir)
        critical = [
            system
            for system in systems
            if pipelines.get(system, {}).get("business_criticality", 0.0) >= 0.9
            or pipelines.get(system, {}).get("status") in {"critical", "degraded"}
        ]
        max_depth = max([int(item.get("depth") or 0) for item in _flatten_blast_nodes(blast)] or [0])
        impact_hours = round(max(1.0, len(systems) * 1.5 + len(critical) * 2.0 + max_depth), 2)
        vector = _factor_vector(alert)
        vector[FACTOR_NAMES.index("impact_scope")] = max(vector[FACTOR_NAMES.index("impact_scope")], min(1.0, len(systems) / 8.0))
        vector[FACTOR_NAMES.index("downstream_urgency")] = max(
            vector[FACTOR_NAMES.index("downstream_urgency")], min(1.0, (len(critical) + max_depth) / 5.0)
        )
        vector[FACTOR_NAMES.index("business_criticality")] = max(
            vector[FACTOR_NAMES.index("business_criticality")], 0.9 if critical else 0.55
        )
        return self._base_evidence(
            alert,
            {
                "affected_systems_count": len(systems),
                "critical_systems": critical,
                "estimated_impact_hours": impact_hours,
                "affected_systems": systems,
            },
            vector,
        )


class RecurringPattern(DataOpsPatternBase):
    category_name = "known_pattern"
    pattern_name = "recurring_pattern"
    selected_edge = "DECIDED_ON"
    enriched_factors: tuple[str, ...] = ("recurrence_frequency", "business_criticality")
    candidate_read = "alert.recurrence"
    graph_query = "Alert-[:DECIDED_ON]->Decision history plus fixture recurrence clusters"

    def evidence_keys(self) -> list[str]:
        return ["pattern_match_confidence", "last_occurrence", "known_resolution", "times_resolved"]

    async def execute(self, alert: dict[str, Any], graph_store: Any) -> dict[str, Any]:
        recurrence = await _recurrence(graph_store, alert, self.data_dir)
        count = int(recurrence.get("prior_count") or alert.get("recurrence_count") or 0)
        frequency = float(recurrence.get("recurrence_frequency") or recurrence.get("value") or _factors(alert).get("recurrence_frequency") or 0.0)
        confidence = min(0.99, max(0.05, 0.2 + frequency * 0.65 + min(count, 12) * 0.025))
        vector = _factor_vector(alert)
        vector[FACTOR_NAMES.index("recurrence_frequency")] = max(vector[FACTOR_NAMES.index("recurrence_frequency")], confidence)
        return self._base_evidence(
            alert,
            {
                "pattern_match_confidence": round(confidence, 4),
                "last_occurrence": recurrence.get("last_occurrence") or "2026-05-17T23:45:00Z",
                "known_resolution": _known_resolution(alert),
                "times_resolved": count,
            },
            vector,
        )


def build_default_investigation_patterns(data_dir: str | Path | None = None) -> list[InvestigationPattern]:
    patterns: list[InvestigationPattern] = [
        UpstreamSourcePattern(data_dir),
        SchemaChangePattern(data_dir),
        DataQualityPattern(data_dir),
        BlastRadiusPattern(data_dir),
        RecurringPattern(data_dir),
    ]
    return patterns


PATTERN_REGISTRY: dict[str, InvestigationPattern] = {
    pattern.category_name: pattern for pattern in build_default_investigation_patterns()
}


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def _load_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return default


async def _pipelines(graph_store: Any, data_dir: Path) -> dict[str, dict[str, Any]]:
    if hasattr(graph_store, "get_pipelines"):
        try:
            payload = await _maybe_await(graph_store.get_pipelines())
            rows = payload.get("pipelines", payload) if isinstance(payload, dict) else payload
            if isinstance(rows, list):
                return {str(row.get("name") or row.get("system")): dict(row) for row in rows if isinstance(row, dict)}
        except Exception:
            pass
    payload = _load_json(data_dir / "fallback" / "pipelines.json", {"pipelines": []})
    return {str(row.get("name") or row.get("system")): dict(row) for row in payload.get("pipelines", [])}


async def _blast_radius(graph_store: Any, alert: dict[str, Any], data_dir: Path) -> dict[str, Any]:
    alert_id = _alert_id(alert)
    if hasattr(graph_store, "get_blast_radius"):
        try:
            payload = await _maybe_await(graph_store.get_blast_radius(alert_id))
            if isinstance(payload, dict) and payload:
                return payload
        except Exception:
            pass
    payload = _load_json(data_dir / "fallback" / "blast_radius.json", {"systems": {}, "alerts": {}})
    tree_ref = payload.get("alerts", {}).get(alert_id, {}).get("tree_ref") or _system(alert)
    return {"tree": payload.get("systems", {}).get(tree_ref, {"system": tree_ref, "children": []})}


async def _recurrence(graph_store: Any, alert: dict[str, Any], data_dir: Path) -> dict[str, Any]:
    if hasattr(graph_store, "get_recurrence"):
        try:
            payload = await _maybe_await(graph_store.get_recurrence(_alert_id(alert)))
            if isinstance(payload, dict) and payload:
                return payload
        except Exception:
            pass
    return {
        "source": "fixture",
        "system": _system(alert),
        "category": str(alert.get("category") or alert.get("alert_type") or "unknown"),
        "prior_count": int(alert.get("recurrence_count") or 0),
        "recurrence_frequency": float(_factors(alert).get("recurrence_frequency") or 0.0),
        "last_occurrence": "2026-05-17T23:45:00Z",
    }


def _schema_change_for_alert(alert: dict[str, Any], data_dir: Path) -> dict[str, Any]:
    payload = _load_json(data_dir / "schema_changes.json", {"systems": {}})
    systems = payload.get("systems", {})
    system = _system(alert)
    changes = systems.get(system) or systems.get("sap_mm") or []
    if changes:
        return dict(changes[0])
    root = _root_cause(alert)
    return {
        "column": root.get("field", "unknown"),
        "change_type": root.get("change_type", "unknown"),
        "downstream_impact": root.get("fanout_multiplier", 1),
        "detected": "unknown",
        "impacted_systems": [],
    }


def _root_cause(alert: dict[str, Any]) -> dict[str, Any]:
    refs = alert.get("cross_graph_refs")
    if isinstance(refs, dict) and isinstance(refs.get("root_cause"), dict):
        return dict(refs["root_cause"])
    return {}


def _alert_id(alert: dict[str, Any]) -> str:
    return str(alert.get("alert_id") or alert.get("id") or alert.get("event_id") or "unknown")


def _system(alert: dict[str, Any]) -> str:
    return str(alert.get("system") or alert.get("system_name") or "unknown").strip()


def _factors(alert: dict[str, Any]) -> dict[str, float]:
    raw_value = alert.get("factors")
    raw = raw_value if isinstance(raw_value, dict) else {}
    return {name: float(raw.get(name, 0.0) or 0.0) for name in FACTOR_NAMES}


def _factor_vector(alert: dict[str, Any]) -> list[float]:
    factors = _factors(alert)
    return [float(factors.get(name, 0.0)) for name in FACTOR_NAMES]


def _quality_rule_name(alert: dict[str, Any]) -> str:
    category = str(alert.get("category") or "unknown")
    dataset = str(alert.get("dataset") or "dataset")
    if category == "quality_anomaly":
        return f"{dataset}.material_taxonomy_completeness"
    if category == "freshness_violation":
        return f"{dataset}.freshness_sla"
    return f"{dataset}.schema_contract"


def _known_resolution(alert: dict[str, Any]) -> str:
    category = str(alert.get("category") or "")
    if category == "schema_change":
        return "Apply pre-join material taxonomy bridge before invoice matching."
    if category == "freshness_violation":
        return "Pause downstream consumers and rerun the delayed extract after source catch-up."
    if int(alert.get("recurrence_count") or 0) >= 7:
        return "Use the previously approved recurring-impact escalation rule."
    return "Open owner investigation with recent resolution history attached."


def _dependency_depth(system: str, pipelines: dict[str, dict[str, Any]], *, direction: str) -> int:
    seen: set[str] = set()

    def walk(name: str, depth: int) -> int:
        if name in seen:
            return depth
        seen.add(name)
        neighbors = pipelines.get(name, {}).get(direction) or []
        if not neighbors:
            return depth
        return max(walk(str(neighbor), depth + 1) for neighbor in neighbors)

    return walk(system, 0)


def _latest_timestamp(values: list[Any]) -> str | None:
    strings = [str(value) for value in values if value]
    return max(strings) if strings else None


def _days_since(value: str, now_value: str) -> int:
    try:
        changed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        now = datetime.fromisoformat(now_value.replace("Z", "+00:00"))
        return max(0, (now - changed).days)
    except ValueError:
        return 0


def _flatten_blast_nodes(blast: dict[str, Any]) -> list[dict[str, Any]]:
    root = blast.get("tree") or blast
    nodes: list[dict[str, Any]] = []

    def visit(node: dict[str, Any]) -> None:
        nodes.append(node)
        for child in node.get("children") or []:
            if isinstance(child, dict):
                visit(child)

    if isinstance(root, dict):
        visit(root)
    return nodes


def _flatten_blast_systems(blast: dict[str, Any]) -> list[str]:
    systems: list[str] = []
    for node in _flatten_blast_nodes(blast):
        name = str(node.get("system") or "")
        if name and name not in systems:
            systems.append(name)
    return systems
