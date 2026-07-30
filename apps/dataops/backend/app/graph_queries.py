"""DataOps topology query layer with explicit offline fixture mode."""

from __future__ import annotations

import json
import os
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from copilot_sdk.config import GraphConfig


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
FALLBACK_DIR = DATA_DIR / "fallback"
FACTOR_NAMES = (
    "impact_scope",
    "source_reliability",
    "recurrence_frequency",
    "downstream_urgency",
    "data_freshness",
    "business_criticality",
)
READ_ONLY_FORBIDDEN = re.compile(
    r"\b(CREATE|MERGE|SET|DELETE|REMOVE|DROP|DETACH|ON\s+CREATE|ON\s+MATCH)\b",
    re.IGNORECASE,
)
_TOPOLOGY_ENV_KEYS = (
    "GRAPH_BACKEND",
    "GRAPH_DSN",
    "GRAPH_NAME",
    "GRAPH_DOMAIN",
    "AGE_DSN",
    "AGE_GRAPH_NAME",
    "CI_ALLOW_SQLITE_FALLBACK",
)
_DATAOPS_GRAPH_CONFIG_KEYS = (
    "DATAOPS_ACTIVE_GRAPH_BACKEND",
    "DATAOPS_ACTIVE_AGE_DSN",
    "DATAOPS_ACTIVE_AGE_GRAPH",
)


def _load_topology_config() -> GraphConfig:
    """Resolve topology connection settings from the typed DataOps config only."""
    previous = {key: os.environ.get(key) for key in _TOPOLOGY_ENV_KEYS}
    try:
        for key in _TOPOLOGY_ENV_KEYS:
            os.environ.pop(key, None)
        has_dataops_backend = bool(os.environ.get(_DATAOPS_GRAPH_CONFIG_KEYS[0], "").strip())
        generic_backend = previous.get("GRAPH_BACKEND")
        has_generic_backend = bool(generic_backend and generic_backend.strip())
        profile = "production" if has_dataops_backend or has_generic_backend else "development"
        if not has_dataops_backend and has_generic_backend:
            for key, value in previous.items():
                if value is not None:
                    os.environ[key] = value
        elif not has_dataops_backend:
            os.environ["DATAOPS_ACTIVE_GRAPH_BACKEND"] = "sqlite"
            os.environ["CI_ALLOW_SQLITE_FALLBACK"] = "1"
        return GraphConfig.load("dataops", profile=profile)
    finally:
        for key in _TOPOLOGY_ENV_KEYS:
            os.environ.pop(key, None)
        for key, value in previous.items():
            if value is not None:
                os.environ[key] = value


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _ci_platform_path() -> Path:
    return Path(__file__).resolve().parents[4].parent / "ci-platform"


def _load_age_client_class() -> type[Any] | None:
    ci_path = _ci_platform_path()
    if ci_path.exists() and str(ci_path) not in sys.path:
        sys.path.insert(0, str(ci_path))
    try:
        from ci_platform.graph.age_client import AGEClient
    except Exception:
        return None
    return AGEClient


def _safe_get_float(payload: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(payload.get(key, default))
    except (TypeError, ValueError):
        return default


class DataOpsGraphClient:
    def __init__(
        self,
        dsn: str | None = None,
        fallback_dir: Path | None = None,
        age_client: Any | None = None,
        age_client_cls: type[Any] | None = None,
    ) -> None:
        self._fallback_dir = fallback_dir or FALLBACK_DIR
        self._graph_connected = False
        self._age_client = None
        self._serializer = self._fixture_serializer
        self.last_query: str | None = None

        active_config = _load_topology_config()
        self._age_required = active_config.backend in {"age", "dual_write"} or age_client is not None
        graph_dsn = active_config.dsn
        graph_name = active_config.graph
        if graph_dsn and "sslmode" not in graph_dsn:
            graph_dsn += " sslmode=disable"
        if age_client is not None:
            self._age_client = age_client
            self._serializer = getattr(age_client, "serialize_for_age", self._fixture_serializer)
            self._graph_connected = True
        elif graph_dsn:
            cls = age_client_cls or _load_age_client_class()
            if cls is not None:
                try:
                    self._age_client = cls(dsn=graph_dsn, graph_name=graph_name)
                    self._serializer = getattr(cls, "serialize_for_age", self._fixture_serializer)
                    self._graph_connected = True
                except Exception:
                    self._age_client = None
                    self._graph_connected = False

    @property
    def is_graph_connected(self) -> bool:
        return self._graph_connected

    @property
    def graph_source(self) -> str:
        return "graph" if self.is_graph_connected else "fixture"

    async def get_pipelines(self) -> dict[str, Any]:
        rows = await self._run_graph(
            """
            MATCH (system:PipelineSystem)
            WHERE system.domain = {self._serialize("dataops")}
            OPTIONAL MATCH (upstream:PipelineSystem)-[:FEEDS]->(system)
            OPTIONAL MATCH (system)-[:FEEDS]->(downstream:PipelineSystem)
            RETURN system, count(DISTINCT upstream) AS upstream_count,
                   count(DISTINCT downstream) AS downstream_count
            ORDER BY system.name
            """
        )
        if rows is not None:
            return {
                "source": "graph",
                "pipelines": [
                    {
                        **dict(row.get("system") or {}),
                        "upstream_count": int(row.get("upstream_count") or 0),
                        "downstream_count": int(row.get("downstream_count") or 0),
                    }
                    for row in rows
                ],
            }
        return deepcopy(self._pipelines())

    async def get_alerts(self) -> dict[str, Any]:
        rows = await self._run_graph(
            """
            MATCH (alert:DataQualityAlert)
            WHERE alert.domain = {self._serialize("dataops")}
            OPTIONAL MATCH (alert)-[:AFFECTS]->(system:PipelineSystem)
            RETURN alert, system
            ORDER BY alert.alert_id
            """
        )
        if rows is not None:
            alerts = []
            for row in rows:
                alert = dict(row.get("alert") or {})
                system = row.get("system") or {}
                if isinstance(system, dict) and system.get("name"):
                    alert.setdefault("system", system["name"])
                alerts.append(alert)
            return {"source": "graph", "alerts": alerts}
        return deepcopy(self._alerts())

    async def get_system(self, name: str) -> dict[str, Any]:
        literal = self._serialize(name)
        rows = await self._run_graph(
            f"""
            MATCH (system:PipelineSystem {{name: {literal}}})
            WHERE system.domain = {self._serialize("dataops")}
            OPTIONAL MATCH (upstream:PipelineSystem)-[:FEEDS]->(system)
            OPTIONAL MATCH (system)-[:FEEDS]->(downstream:PipelineSystem)
            RETURN system, count(DISTINCT upstream) AS upstream_count,
                   count(DISTINCT downstream) AS downstream_count
            """
        )
        if rows is not None:
            if not rows:
                return {"source": "graph", "error": "System not found", "name": name}
            row = rows[0]
            return {
                "source": "graph",
                "system": {
                    **dict(row.get("system") or {}),
                    "upstream_count": int(row.get("upstream_count") or 0),
                    "downstream_count": int(row.get("downstream_count") or 0),
                },
            }
        system = next((item for item in self._pipelines()["pipelines"] if item["name"] == name), None)
        if system is None:
            return {"source": "fixture", "error": "System not found", "name": name}
        return {"source": "fixture", "system": deepcopy(system)}

    async def get_alert(self, alert_id: str) -> dict[str, Any]:
        pair = await self._graph_alert_and_system(alert_id)
        if pair is not None:
            alert, _system = pair
            return {"source": "graph", "alert": alert}
        alert = self._find_alert(alert_id)
        if alert is None:
            return {"source": "fixture", "error": "Alert not found", "alert_id": alert_id}
        return {"source": "fixture", "alert": deepcopy(alert)}

    async def get_blast_radius(self, alert_id: str) -> dict[str, Any]:
        rows = await self._run_graph(
            f"""
            MATCH (alert:DataQualityAlert {{alert_id: {self._serialize(alert_id)}}})-[:AFFECTS]->(system:PipelineSystem)
            WHERE alert.domain = {self._serialize("dataops")}
            OPTIONAL MATCH (parent:PipelineSystem)-[:FEEDS]->(child:PipelineSystem)
            RETURN system, collect(DISTINCT {{parent: parent.name, child: child.name,
                   child_sla: child.sla_minutes,
                   child_criticality: child.business_criticality}}) AS edges
            """
        )
        if rows is not None:
            if not rows:
                return self._fixture_blast_radius(alert_id)
            row = rows[0]
            system = row.get("system") or {}
            affected_system = system.get("name") if isinstance(system, dict) else None
            if not affected_system:
                return self._fixture_blast_radius(alert_id)
            edges = [
                edge for edge in (row.get("edges") or [])
                if isinstance(edge, dict) and edge.get("parent") and edge.get("child")
            ]
            tree = self._build_tree_from_edges(affected_system, edges)
            criticalities = [
                _safe_get_float(edge, "child_criticality")
                for edge in edges
                if edge.get("child_criticality") is not None
            ]
            slas = [
                _safe_get_float(edge, "child_sla", 120.0)
                for edge in edges
                if edge.get("child_sla") is not None
            ]
            return {
                "source": "graph",
                "alert_id": alert_id,
                "system": affected_system,
                "affected_system": affected_system,
                "tree": tree,
                "downstream_tree": tree,
                "total_affected": len({edge["child"] for edge in edges}),
                "max_criticality": max(criticalities, default=_safe_get_float(system, "business_criticality")),
                "min_sla": min(slas, default=_safe_get_float(system, "sla_minutes", 120.0)),
                "engine": {"graph": "ci_platform.graph.AGEClient"},
            }
        return self._fixture_blast_radius(alert_id)

    async def get_recurrence(self, alert_id: str) -> dict[str, Any]:
        alert = None
        recurrence = None
        if self.is_graph_connected:
            pair = await self._graph_alert_and_system(alert_id)
            if pair is not None:
                alert, _system = pair
                recurrence = await self.compute_recurrence(alert["system"], alert["category"])
        if alert is None:
            alert = self._find_alert(alert_id)
            if alert is not None:
                recurrence = self._fixture_recurrence(alert["system"], alert["category"])
        if not alert:
            return {"source": self.graph_source, "error": "Alert not found", "alert_id": alert_id}

        return {
            "source": recurrence["source"],
            "alert_id": alert_id,
            "system": alert["system"],
            "category": alert["category"],
            "prior_count": recurrence["prior_count"],
            "recurrence_frequency": recurrence["value"],
        }

    async def get_factors(self, alert_id: str) -> dict[str, Any]:
        alert = None
        system = None
        use_graph = False
        if self.is_graph_connected:
            pair = await self._graph_alert_and_system(alert_id)
            if pair is not None:
                alert, system = pair
                use_graph = True
        if alert is None:
            alert = self._find_alert(alert_id)
        if not alert:
            return {"source": self.graph_source, "error": "Alert not found", "alert_id": alert_id}

        system_name = alert["system"]
        if use_graph:
            impact = await self.compute_impact_scope(system_name)
            urgency = await self.compute_downstream_urgency(system_name)
            recurrence = await self.compute_recurrence(system_name, alert["category"])
            source = "graph"
            system = system or {}
        else:
            impact = self._fixture_impact_scope(system_name)
            urgency = self._fixture_downstream_urgency(system_name)
            recurrence = self._fixture_recurrence(system_name, alert["category"])
            source = "fixture"
            system = self._find_system(system_name) or {}
        factors = {
            "impact_scope": {
                "value": impact["value"],
                "source": impact["source"],
                "detail": "downstream_count / 8",
            },
            "source_reliability": {
                "value": _safe_get_float(system, "source_reliability", self._alert_factor(alert, "source_reliability")),
                "source": source,
                "detail": "system source reliability",
            },
            "recurrence_frequency": {
                "value": recurrence["value"],
                "source": recurrence["source"],
                "detail": "min(prior_count / 12, 1.0)",
            },
            "downstream_urgency": {
                "value": urgency["value"],
                "source": urgency["source"],
                "detail": "normalized from minimum downstream SLA",
            },
            "data_freshness": {
                "value": self._alert_factor(alert, "data_freshness"),
                "source": source,
                "detail": "alert freshness signal",
            },
            "business_criticality": {
                "value": _safe_get_float(system, "business_criticality", self._alert_factor(alert, "business_criticality")),
                "source": source,
                "detail": "system business criticality",
            },
        }
        return {
            "source": source,
            "alert_id": alert_id,
            "factors": factors,
            "all_auto_computed": set(factors) == set(FACTOR_NAMES),
        }

    async def _graph_alert_and_system(self, alert_id: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        rows = await self._run_graph(
            f"""
            MATCH (alert:DataQualityAlert {{alert_id: {self._serialize(alert_id)}}})
            WHERE alert.domain = {self._serialize("dataops")}
            OPTIONAL MATCH (alert)-[:AFFECTS]->(system:PipelineSystem)
            RETURN alert, system
            """
        )
        if not rows:
            return None
        alert = dict(rows[0].get("alert") or {})
        system = dict(rows[0].get("system") or {})
        if system.get("name"):
            alert.setdefault("system", system["name"])
        if not alert.get("alert_id"):
            alert["alert_id"] = alert_id
        return alert, system

    def _fixture_blast_radius(self, alert_id: str) -> dict[str, Any]:
        blast = self._blast()
        entry = blast["alerts"].get(alert_id)
        if entry is None:
            return {"source": "fixture", "error": "Alert not found", "alert_id": alert_id}
        tree_ref = entry["tree_ref"]
        tree = deepcopy(blast["systems"][tree_ref])
        pipeline_map = {item["name"]: item for item in self._pipelines()["pipelines"]}
        names = [tree["system"]] + self._flatten_tree_names(tree)
        unique_names = list(dict.fromkeys(names))
        downstream_names = [name for name in unique_names if name != tree["system"]]
        criticalities = [
            _safe_get_float(pipeline_map[name], "business_criticality")
            for name in unique_names
            if name in pipeline_map
        ]
        slas = [
            _safe_get_float(pipeline_map[name], "sla_minutes", 120.0)
            for name in unique_names
            if name in pipeline_map
        ]
        return {
            "source": "fixture",
            "alert_id": alert_id,
            "system": entry["system"],
            "affected_system": entry["system"],
            "tree": tree,
            "downstream_tree": tree,
            "total_affected": len(downstream_names),
            "max_criticality": max(criticalities, default=0.0),
            "min_sla": min(slas, default=120.0),
            "engine": {"graph": "fixture"},
        }

    @classmethod
    def _build_tree_from_edges(
        cls,
        root: str,
        edges: list[dict[str, Any]],
        visited: set[str] | None = None,
        depth: int = 0,
        max_depth: int = 5,
    ) -> dict[str, Any]:
        visited = set(visited or set())
        visited.add(root)
        children = []
        if depth < max_depth:
            for edge in edges:
                child = edge["child"]
                if edge["parent"] == root and child not in visited:
                    children.append(cls._build_tree_from_edges(child, edges, visited | {child}, depth + 1, max_depth))
        return {"system": root, "depth": depth, "children": children}

    @staticmethod
    def _alert_factor(alert: dict[str, Any], name: str) -> float:
        factors = alert.get("factors") or {}
        if isinstance(factors, dict) and name in factors:
            return _safe_get_float(factors, name)
        return _safe_get_float(alert, name)

    def _fixture_impact_scope(self, system_name: str) -> dict[str, Any]:
        system = self._find_system(system_name) or {}
        downstream_count = int(system.get("downstream_count") or 0)
        return {
            "source": "fixture",
            "system": system_name,
            "downstream_count": downstream_count,
            "value": round(min(downstream_count / 8, 1.0), 4),
        }

    def _fixture_downstream_urgency(self, system_name: str) -> dict[str, Any]:
        pipeline_map = {item["name"]: item for item in self._pipelines()["pipelines"]}
        blast = self._blast()["systems"].get(system_name, {"system": system_name, "children": []})
        names = [system_name] + self._flatten_tree_names(blast)
        slas = [pipeline_map[name]["sla_minutes"] for name in names if name in pipeline_map]
        min_sla = min(slas) if slas else 120
        return {
            "source": "fixture",
            "system": system_name,
            "min_sla": min_sla,
            "value": self._sla_to_urgency(min_sla),
        }

    def _fixture_recurrence(self, system_name: str, category: str) -> dict[str, Any]:
        prior_count = sum(
            1
            for alert in self._alerts()["alerts"]
            if alert["system"] == system_name and alert["category"] == category
        )
        seed_prior = max(
            (
                alert.get("recurrence_count", 0)
                for alert in self._alerts()["alerts"]
                if alert["system"] == system_name and alert["category"] == category
            ),
            default=prior_count,
        )
        prior_count = max(prior_count, seed_prior)
        return {
            "source": "fixture",
            "system": system_name,
            "category": category,
            "prior_count": prior_count,
            "value": round(min(prior_count / 12, 1.0), 4),
        }

    async def compute_impact_scope(self, system_name: str) -> dict[str, Any]:
        rows = await self._run_graph(
            f"""
            MATCH (system:PipelineSystem {{name: {self._serialize(system_name)}}})
            WHERE system.domain = {self._serialize("dataops")}
            OPTIONAL MATCH (system)-[:FEEDS*1..4]->(downstream:PipelineSystem)
            RETURN count(DISTINCT downstream) AS downstream_count
            """
        )
        if rows is not None:
            downstream_count = int(rows[0].get("downstream_count") or 0) if rows else 0
            return {
                "source": "graph",
                "system": system_name,
                "downstream_count": downstream_count,
                "value": round(min(downstream_count / 8, 1.0), 4),
            }
        return self._fixture_impact_scope(system_name)

    async def compute_downstream_urgency(self, system_name: str) -> dict[str, Any]:
        rows = await self._run_graph(
            f"""
            MATCH (system:PipelineSystem {{name: {self._serialize(system_name)}}})
            WHERE system.domain = {self._serialize("dataops")}
            OPTIONAL MATCH (system)-[:FEEDS*0..4]->(downstream:PipelineSystem)
            RETURN min(downstream.sla_minutes) AS min_sla
            """
        )
        if rows is not None:
            min_sla = float(rows[0].get("min_sla") or 120) if rows else 120.0
            return {
                "source": "graph",
                "system": system_name,
                "min_sla": min_sla,
                "value": self._sla_to_urgency(min_sla),
            }

        return self._fixture_downstream_urgency(system_name)

    async def compute_recurrence(self, system_name: str, category: str) -> dict[str, Any]:
        rows = await self._run_graph(
            f"""
            MATCH (alert:DataQualityAlert)-[:AFFECTS]->(system:PipelineSystem {{name: {self._serialize(system_name)}}})
            WHERE alert.domain = {self._serialize("dataops")}
              AND alert.category = {self._serialize(category)}
            RETURN count(alert) AS prior_count
            """
        )
        if rows is not None:
            prior_count = int(rows[0].get("prior_count") or 0) if rows else 0
            return {
                "source": "graph",
                "system": system_name,
                "category": category,
                "prior_count": prior_count,
                "value": round(min(prior_count / 12, 1.0), 4),
            }

        return self._fixture_recurrence(system_name, category)

    async def _run_graph(self, query: str) -> list[dict[str, Any]] | None:
        if not self._age_client:
            if self._age_required:
                raise RuntimeError("DataOps AGE graph is configured but not connected")
            return None
        if READ_ONLY_FORBIDDEN.search(query):
            raise ValueError(f"DataOps graph query is not read-only: {query[:120]}")
        self.last_query = query
        try:
            return await self._age_client.run_query(query, None)
        except Exception:
            self._graph_connected = False
            if self._age_required:
                raise
            return None

    def _serialize(self, value: Any) -> str:
        return str(self._serializer(value))

    @staticmethod
    def _fixture_serializer(value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, (int, float)):
            return str(value)
        return "'" + str(value).replace("'", "\\'") + "'"

    @staticmethod
    def _sla_to_urgency(sla_minutes: float) -> float:
        return round(max(0.0, min((120.0 - float(sla_minutes)) / 120.0, 1.0)), 4)

    @staticmethod
    def _flatten_tree_names(tree: dict[str, Any]) -> list[str]:
        names = []
        for child in tree.get("children", []):
            names.append(child["system"])
            names.extend(DataOpsGraphClient._flatten_tree_names(child))
        return names

    def _pipelines(self) -> dict[str, Any]:
        return _load_json(self._fallback_dir / "pipelines.json")

    def _alerts(self) -> dict[str, Any]:
        return _load_json(self._fallback_dir / "alerts.json")

    def _blast(self) -> dict[str, Any]:
        return _load_json(self._fallback_dir / "blast_radius.json")

    def _find_system(self, name: str) -> dict[str, Any] | None:
        return next((item for item in self._pipelines()["pipelines"] if item["name"] == name), None)

    def _find_alert(self, alert_id: str) -> dict[str, Any] | None:
        return next((item for item in self._alerts()["alerts"] if item["alert_id"] == alert_id), None)
