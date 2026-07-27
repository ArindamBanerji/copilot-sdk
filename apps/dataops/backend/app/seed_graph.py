"""Deterministic DataOps graph seed plan."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _slug(value: Any) -> str:
    text = str(value or "unknown").strip().lower()
    return "_".join("".join(ch if ch.isalnum() else "_" for ch in text).split("_")) or "unknown"


def _node_id(label: str, natural_key: Any) -> str:
    return f"{label}:{_slug(natural_key)}"


def _add_node(
    nodes: list[dict[str, Any]],
    seen: dict[str, dict[str, Any]],
    label: str,
    natural_key: Any,
    properties: dict[str, Any],
) -> str:
    node_id = _node_id(label, natural_key)
    if node_id not in seen:
        node = {"id": node_id, "label": label, "properties": dict(properties)}
        nodes.append(node)
        seen[node_id] = node
    return node_id


def _add_edge(
    edges: list[dict[str, Any]],
    seen: set[tuple[str, str, str]],
    label: str,
    from_id: str,
    to_id: str,
    properties: dict[str, Any] | None = None,
) -> None:
    token = (label, from_id, to_id)
    if token in seen:
        return
    seen.add(token)
    edges.append(
        {
            "id": f"{label}:{len(edges) + 1}",
            "label": label,
            "from_id": from_id,
            "to_id": to_id,
            "properties": properties or {},
        }
    )


def _dataset_id(dataset: Any) -> str:
    return _slug(str(dataset or "unknown").split("+")[0].strip())


def seed_dataops_graph(seed: int = 42) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    alerts_payload = _load_json(DATA_DIR / "fallback" / "alerts.json", {})
    pipelines_payload = _load_json(DATA_DIR / "fallback" / "pipelines.json", {})
    transformations_payload = _load_json(DATA_DIR / "transformations.json", {})
    celonis_payload = _load_json(DATA_DIR / "celonis_process_data.json", {})
    alerts = alerts_payload.get("alerts") if isinstance(alerts_payload, dict) else []
    pipelines = pipelines_payload.get("pipelines") if isinstance(pipelines_payload, dict) else []
    transformations = transformations_payload.get("systems") if isinstance(transformations_payload, dict) else {}
    activities = celonis_payload.get("activities") if isinstance(celonis_payload, dict) else []
    if not isinstance(alerts, list):
        alerts = []
    if not isinstance(pipelines, list):
        pipelines = []
    if not isinstance(transformations, dict):
        transformations = {}
    if not isinstance(activities, list):
        activities = []

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_nodes: dict[str, dict[str, Any]] = {}
    seen_edges: set[tuple[str, str, str]] = set()

    pipeline_ids: dict[str, str] = {}
    for pipeline in pipelines:
        if not isinstance(pipeline, dict):
            continue
        name = str(pipeline.get("name") or "unknown")
        pipeline_ids[name] = _add_node(
            nodes,
            seen_nodes,
            "Pipeline",
            name,
            {
                "pipeline_id": name,
                "name": name,
                "display_name": pipeline.get("display_name"),
                "owner": pipeline.get("owner"),
                "status": pipeline.get("status"),
                "sla_minutes": pipeline.get("sla_minutes"),
            },
        )

    dataset_ids: dict[str, str] = {}
    transformation_ids: dict[str, str] = {}
    for system, steps in transformations.items():
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            transform_key = str(step.get("id") or f"{system}-{len(transformation_ids)}")
            transformation_id = _add_node(
                nodes,
                seen_nodes,
                "Transformation",
                transform_key,
                {
                    "transformation_id": transform_key,
                    "name": step.get("name"),
                    "type": step.get("type"),
                    "source": step.get("source"),
                    "target": step.get("target"),
                    "status": step.get("status"),
                },
            )
            transformation_ids[transform_key] = transformation_id
            for raw_source in str(step.get("source") or "").split("+"):
                source_name = raw_source.strip()
                if not source_name:
                    continue
                key = _dataset_id(source_name)
                dataset_id = dataset_ids.setdefault(
                    key,
                    _add_node(
                        nodes,
                        seen_nodes,
                        "Dataset",
                        key,
                        {
                            "dataset_id": key,
                            "name": source_name,
                            "system": system,
                            "schema_columns": step.get("schema_columns", []),
                        },
                    ),
                )
                _add_edge(edges, seen_edges, "CONSUMES", transformation_id, dataset_id)
            target_name = step.get("target")
            if target_name:
                key = _dataset_id(target_name)
                dataset_id = dataset_ids.setdefault(
                    key,
                    _add_node(
                        nodes,
                        seen_nodes,
                        "Dataset",
                        key,
                        {
                            "dataset_id": key,
                            "name": target_name,
                            "system": system,
                            "schema_columns": step.get("schema_columns", []),
                        },
                    ),
                )
                _add_edge(edges, seen_edges, "PRODUCES", transformation_id, dataset_id)

    rule_ids: dict[str, str] = {}
    bottleneck_activity_id: str | None = None
    if isinstance(celonis_payload, dict):
        model_key = celonis_payload.get("process_model") or "process_model"
        model_id = _add_node(
            nodes,
            seen_nodes,
            "ProcessModel",
            model_key,
            {
                "model_id": _slug(model_key),
                "name": celonis_payload.get("process_model"),
                "variant": celonis_payload.get("variant"),
                "source": celonis_payload.get("source"),
            },
        )
        previous_activity_id: str | None = None
        for activity in activities:
            if not isinstance(activity, dict):
                continue
            activity_key = activity.get("id") or activity.get("name")
            activity_id = _add_node(
                nodes,
                seen_nodes,
                "Activity",
                activity_key,
                {
                    "activity_id": activity_key,
                    "name": activity.get("name"),
                    "avg_duration_hours": activity.get("avg_duration_hours"),
                    "case_count": activity.get("case_count"),
                    "status": activity.get("status"),
                    "bottleneck": bool(activity.get("bottleneck")),
                },
            )
            _add_edge(edges, seen_edges, "CONTAINS", model_id, activity_id)
            if previous_activity_id is not None:
                _add_edge(edges, seen_edges, "FOLLOWS", previous_activity_id, activity_id)
            previous_activity_id = activity_id
            if activity.get("bottleneck"):
                bottleneck_activity_id = activity_id

    for alert in alerts:
        if not isinstance(alert, dict):
            continue
        alert_key = str(alert.get("alert_id") or alert.get("event_id") or f"alert-{len(nodes)}")
        dataset_key = _dataset_id(alert.get("dataset"))
        system_name = str(alert.get("system") or "unknown")
        category = str(alert.get("category") or "unknown")
        severity = str(alert.get("severity") or "unknown")
        dataset_id = dataset_ids.setdefault(
            dataset_key,
            _add_node(
                nodes,
                seen_nodes,
                "Dataset",
                dataset_key,
                {
                    "dataset_id": dataset_key,
                    "name": alert.get("dataset"),
                    "system": system_name,
                    "schema_columns": [],
                },
            ),
        )
        rule_key = f"{category}-{severity}"
        rule_id = rule_ids.setdefault(
            rule_key,
            _add_node(
                nodes,
                seen_nodes,
                "QualityRule",
                rule_key,
                {
                    "rule_id": rule_key,
                    "name": f"{category}_{severity}_rule",
                    "category": category,
                    "severity": severity,
                },
            ),
        )
        alert_id = _add_node(
            nodes,
            seen_nodes,
            "Alert",
            alert_key,
            {
                "alert_id": alert_key,
                "event_id": alert.get("event_id"),
                "dataset": alert.get("dataset"),
                "system": system_name,
                "category": category,
                "severity": severity,
                "status": alert.get("status"),
            },
        )
        decision_id = _add_node(
            nodes,
            seen_nodes,
            "Decision",
            alert_key,
            {
                "decision_id": f"decision-{alert_key}",
                "domain": "dataops",
                "category": category,
                "recommended_action": alert.get("action_taken"),
                "confidence": round(0.55 + rng.random() * 0.4, 4),
                "created_at": alert.get("event_id"),
            },
        )
        pipeline_id = pipeline_ids.get(system_name) or _add_node(
            nodes,
            seen_nodes,
            "Pipeline",
            system_name,
            {
                "pipeline_id": system_name,
                "name": system_name,
                "display_name": system_name,
                "owner": None,
                "status": None,
                "sla_minutes": None,
            },
        )
        _add_edge(edges, seen_edges, "DECIDED_ON", decision_id, alert_id)
        _add_edge(edges, seen_edges, "MONITORS", rule_id, dataset_id)
        _add_edge(edges, seen_edges, "DETECTED_IN", alert_id, pipeline_id)
        if bottleneck_activity_id is not None:
            _add_edge(edges, seen_edges, "TRIGGERED_BY", alert_id, bottleneck_activity_id)

    return nodes, edges
