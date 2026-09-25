"""DataOps EvidenceProvider for VLD-CORE investigations."""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
from typing import Any

from copilot_sdk.scoring.investigation import EvidenceProvider


FACTOR_NAMES = (
    "impact_scope",
    "source_reliability",
    "recurrence_frequency",
    "downstream_urgency",
    "data_freshness",
    "business_criticality",
)

FACTOR_ALIASES = {
    "pipeline_health": "source_reliability",
    "schema_impact": "impact_scope",
    "alert_correlation": "data_freshness",
    "system_dependency": "downstream_urgency",
    "recurrence_pattern": "recurrence_frequency",
    "blast_radius": "business_criticality",
}

# Preserve the schema confidence gate when its source also names a connector.
CONNECTOR_GATED_SOURCES = {
    f"schema_registry+sap_cache:{provenance}"
    for provenance in ("sample", "sandbox", "external")
}

_STATUS_HEALTH = {"ok": 0.92, "healthy": 0.92, "degraded": 0.45,
                  "critical": 0.22, "failed": 0.08}


class DataOpsEvidenceProvider(EvidenceProvider):
    """Read VLD evidence from DataOps fixture and preseed graph data."""

    def __init__(self, data_source: Any, alert_id: str):
        self.data_source = _normalize_data_source(data_source)
        self.alert_id = str(alert_id)
        self._connector_snapshots: dict[str, dict[str, Any]] = {}

    def read_evidence(
        self, decision_id: str, dimension: int, factor_name: str
    ) -> dict[str, Any] | None:
        evidence = self._read_evidence(decision_id, dimension, factor_name)
        alert = self._alert(str(decision_id)) or self._alert(self.alert_id) or {}
        if evidence is not None and alert.get("planted") is True:
            evidence = {**evidence, "planted": True, "provenance": "sample", "synthetic": True,
                        "evidence_tier": "T-sim", "source": f"{evidence['source']}:synthetic"}
        return evidence

    def _read_evidence(
        self, decision_id: str, dimension: int, factor_name: str
    ) -> dict[str, Any] | None:
        alert = self._alert(str(decision_id) or self.alert_id)
        if alert is None:
            alert = self._alert(self.alert_id)
        if alert is None:
            return None

        canonical = FACTOR_ALIASES.get(str(factor_name), str(factor_name))
        if canonical == "impact_scope":
            return self._schema_impact(alert)
        if canonical == "source_reliability":
            return self._pipeline_health(alert)
        if canonical == "recurrence_frequency":
            return self._recurrence_pattern(alert)
        if canonical == "downstream_urgency":
            return self._system_dependency(alert)
        if canonical == "data_freshness":
            return self._alert_correlation(alert)
        if canonical == "business_criticality":
            return self._blast_radius(alert)
        return None

    def _alert(self, alert_id: str) -> dict[str, Any] | None:
        alerts = self.data_source.get("alerts", {})
        alert = alerts.get(alert_id)
        return dict(alert) if isinstance(alert, dict) else None

    def _system(self, alert: dict[str, Any]) -> str:
        return str(alert.get("system") or alert.get("system_name") or "").strip()

    def _schema_impact(self, alert: dict[str, Any]) -> dict[str, Any] | None:
        system = self._system(alert)
        changes = self.data_source.get("schema_changes", {}).get(system, [])
        if not changes:
            root_cause = _nested(alert, "cross_graph_refs", "root_cause")
            if not root_cause:
                return None
            changes = [
                {
                    "column": root_cause.get("field"),
                    "change_type": root_cause.get("change_type"),
                    "downstream_impact": root_cause.get("fanout_multiplier"),
                    "impacted_systems": root_cause.get("impacted_systems", []),
                }
            ]
        change = dict(changes[0])
        fanout = _clamped_float(change.get("downstream_impact"), 1.0)
        impacted = change.get("impacted_systems")
        impacted_systems = list(impacted) if isinstance(impacted, list) else []
        evidence = {
            "value": max(_factor(alert, "impact_scope"), min(1.0, fanout / 10.0)),
            "confidence": 0.92,
            "source": "schema_registry",
            "column": change.get("column"),
            "change_type": change.get("change_type"),
            "join_fanout_factor": fanout,
            "impacted_systems": impacted_systems,
        }
        return self._sap_impact(alert, evidence)

    def _pipeline_health(self, alert: dict[str, Any]) -> dict[str, Any] | None:
        system = self._system(alert)
        pipeline = self.data_source.get("pipelines", {}).get(system)
        if not isinstance(pipeline, dict):
            return None
        status = str(pipeline.get("status") or "unknown").lower()
        status_health = _STATUS_HEALTH.get(status, _factor(alert, "source_reliability"))
        evidence = {
            "value": _clamp(status_health),
            "confidence": 0.86,
            "source": "pipeline_monitor",
            "status": status,
            "system": system,
        }
        return self._celonis_health(alert, evidence)

    def _snapshot(self, name: str) -> dict[str, Any]:
        """Read connector caches once per synchronous investigation provider.

        The SDK invokes this provider in its synchronous route worker. Explicit
        empty credentials keep supporting reads offline, even when the app has
        live connector credentials. Missing/corrupt caches contribute no signal.
        """
        if name not in self._connector_snapshots:
            root = self.data_source.get("data_dir")
            if root is None:
                return {}
            if name == "sap":
                from apps.dataops.backend.app.sap_connector import SAPConnector

                payload = asyncio.run(SAPConnector(api_key="", cache_dir=root).get_purchase_orders(top=100))
            else:
                from apps.dataops.backend.app.celonis_connector import CelonisConnector, SAMPLE_KM_ID

                payload = asyncio.run(CelonisConnector(token="", cache_dir=root).get_process_data(SAMPLE_KM_ID))
            self._connector_snapshots[name] = payload
        return self._connector_snapshots[name]

    def _sap_impact(self, alert: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
        # A schema alert must explicitly identify the supplier. Do not infer
        # supplier identity from prose or attach every cached PO to every alert.
        supplier = str(_nested(alert, "cross_graph_refs", "root_cause").get("upstream_supplier") or "").strip().casefold()
        if not supplier:
            return evidence
        payload = self._snapshot("sap")
        orders = {str(row["PurchaseOrder"]): row for row in payload.get("purchase_orders", [])
                  if isinstance(row, dict) and row.get("PurchaseOrder")}
        matching = [row for row in orders.values() if supplier in {
            str(row.get("Supplier") or "").strip().casefold(),
            str(row.get("SupplierName") or "").strip().casefold(),
        }]
        if not matching:
            return evidence
        # A bounded exposure proxy over the returned cache page, not an estimate
        # of enterprise-wide impact or a new scorer dimension. Preserve stronger
        # schema/fanout evidence; connector exposure can only raise this signal.
        exposure = len(matching) / len(orders)
        return {**evidence, "value": max(evidence["value"], exposure),
                "source": f"schema_registry+{payload['source']}:{payload['provenance']}",
                "connector_signal": {"metric": "supplier_order_exposure", "value": exposure,
                                     "scope": "returned_cached_purchase_orders",
                                     "matched_orders": len(matching), "returned_orders": len(orders)},
                "provenance": payload["provenance"]}

    def _celonis_health(self, alert: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
        link = _nested(alert, "cross_graph_refs", "process_signal")
        activity_name = str(link.get("activity") or "").strip().casefold()
        system = self._system(alert)
        if not activity_name and not system.startswith(("sap_", "celonis_")):
            return evidence
        payload = self._snapshot("celonis")
        activities = payload.get("process_data", {}).get("activities", [])
        signals = []
        for activity in activities if isinstance(activities, list) else []:
            if not isinstance(activity, dict):
                continue
            if activity_name:
                if str(activity.get("name") or "").strip().casefold() != activity_name:
                    continue
                normal = _positive_number(link.get("normal_duration"))
                hours = _positive_number(activity.get("avg_duration_hours"))
                if normal is not None and hours is not None:
                    signals.append(min(1.0, normal / (hours * 3600.0)))
                    continue
            elif activity.get("system") != system:
                continue
            health = _STATUS_HEALTH.get(str(activity.get("status") or "").lower())
            if health is not None:
                signals.append(health)
        if not signals:
            return evidence
        # Use the existing health scale, with an explicit linked-activity
        # slowdown proxy when a baseline in seconds is available.
        health = min(signals)
        return {**evidence, "value": min(evidence["value"], health),
                "source": f"pipeline_monitor+{payload['source']}:{payload['provenance']}",
                "connector_signal": {"metric": "linked_activity_health", "value": health,
                                     "matched_activities": len(signals)},
                "provenance": payload["provenance"]}

    def _recurrence_pattern(self, alert: dict[str, Any]) -> dict[str, Any] | None:
        alert_id = str(alert.get("alert_id") or alert.get("event_id") or "")
        recurrence = self.data_source.get("recurrences", {}).get(alert_id)
        if not isinstance(recurrence, dict):
            count = int(_clamped_float(alert.get("recurrence_count"), 0.0))
            if count <= 0 and _factor(alert, "recurrence_frequency") <= 0.0:
                return None
            recurrence = {
                "prior_count": count,
                "value": _factor(alert, "recurrence_frequency"),
                "confidence": 0.85,
            }
        value = _clamp(recurrence.get("value", recurrence.get("recurrence_frequency", 0.0)))
        return {
            "value": value,
            "confidence": _clamp(recurrence.get("confidence", 0.85)),
            "source": "historical_alerts",
            "prior_count": int(_clamped_float(recurrence.get("prior_count"), 0.0)),
            "pattern": recurrence.get("pattern"),
            "known_resolution": recurrence.get("known_resolution"),
        }

    def _system_dependency(self, alert: dict[str, Any]) -> dict[str, Any] | None:
        system = self._system(alert)
        dependency = self.data_source.get("dependencies", {}).get(system)
        pipeline = self.data_source.get("pipelines", {}).get(system, {})
        if not isinstance(dependency, dict):
            downstream = pipeline.get("downstream") if isinstance(pipeline, dict) else []
            upstream = pipeline.get("upstream") if isinstance(pipeline, dict) else []
            if not downstream and not upstream:
                return None
            dependency = {"downstream": downstream or [], "upstream": upstream or []}
        downstream = _string_list(dependency.get("downstream"))
        upstream = _string_list(dependency.get("upstream"))
        new_upstream = _string_list(dependency.get("new_upstream"))
        severity = dependency.get("value")
        if severity is None:
            severity = max(len(downstream) / 4.0, len(new_upstream) / 1.25)
        return {
            "value": _clamp(severity),
            "confidence": _clamp(dependency.get("confidence", 0.88)),
            "source": "dependency_graph",
            "downstream_systems": downstream,
            "upstream_systems": upstream,
            "new_upstream_dependencies": new_upstream,
        }

    def _alert_correlation(self, alert: dict[str, Any]) -> dict[str, Any] | None:
        alert_id = str(alert.get("alert_id") or alert.get("event_id") or "")
        correlation = self.data_source.get("correlations", {}).get(alert_id)
        if not isinstance(correlation, dict):
            return None
        correlated = _string_list(correlation.get("correlated_alerts"))
        return {
            "value": _clamp(correlation.get("value", len(correlated) / 5.0)),
            "confidence": _clamp(correlation.get("confidence", min(1.0, 0.5 + len(correlated) / 10.0))),
            "source": "alert_correlator",
            "correlated_alerts": correlated,
        }

    def _blast_radius(self, alert: dict[str, Any]) -> dict[str, Any] | None:
        alert_id = str(alert.get("alert_id") or alert.get("event_id") or "")
        blast = self.data_source.get("blast_radius", {}).get(alert_id)
        if not isinstance(blast, dict):
            system = self._system(alert)
            blast = self.data_source.get("blast_radius", {}).get(system)
        if not isinstance(blast, dict):
            return None
        systems = _string_list(blast.get("affected_systems"))
        if not systems and isinstance(blast.get("tree"), dict):
            systems = _flatten_tree(blast["tree"])
        value = blast.get("value", max(_factor(alert, "business_criticality"), len(systems) / 6.0))
        return {
            "value": _clamp(value),
            "confidence": _clamp(blast.get("confidence", 0.80)),
            "source": "impact_analysis",
            "affected_systems": systems,
            "affected_systems_count": len(systems),
        }


def build_dataops_evidence_source(data_dir: str | Path | None = None) -> dict[str, Any]:
    """Build a read-only evidence source from DataOps fixture files."""

    root = Path(data_dir) if data_dir is not None else Path(__file__).resolve().parents[1] / "data"
    alerts_payload = _load_json(root / "fallback" / "alerts.json", {"alerts": []})
    pipelines_payload = _load_json(root / "fallback" / "pipelines.json", {"pipelines": []})
    schema_payload = _load_json(root / "schema_changes.json", {"systems": {}})
    blast_payload = _load_json(root / "fallback" / "blast_radius.json", {"systems": {}, "alerts": {}})

    alerts = {
        str(alert.get("alert_id") or alert.get("event_id")): dict(alert)
        for alert in alerts_payload.get("alerts", [])
        if isinstance(alert, dict) and (alert.get("alert_id") or alert.get("event_id"))
    }
    pipelines = {
        str(pipeline.get("name") or pipeline.get("system")): dict(pipeline)
        for pipeline in pipelines_payload.get("pipelines", [])
        if isinstance(pipeline, dict) and (pipeline.get("name") or pipeline.get("system"))
    }
    schema_changes = {
        str(system): [dict(item) for item in changes if isinstance(item, dict)]
        for system, changes in schema_payload.get("systems", {}).items()
        if isinstance(changes, list)
    }
    blast_radius: dict[str, dict[str, Any]] = {}
    for key, value in blast_payload.get("systems", {}).items():
        if isinstance(value, dict):
            blast_radius[str(key)] = {"tree": dict(value)}
    for key, value in blast_payload.get("alerts", {}).items():
        if isinstance(value, dict):
            blast_radius[str(key)] = dict(value)

    source: dict[str, Any] = {
        "data_dir": root,
        "alerts": alerts,
        "pipelines": pipelines,
        "schema_changes": schema_changes,
        "dependencies": {},
        "recurrences": {},
        "correlations": {},
        "blast_radius": blast_radius,
    }
    fixture_path = root / "demo_fixtures" / "investigation_evidence.json"
    if fixture_path.exists():
        # File placement by the explicit preseed command opts this installation
        # into synthetic evidence. Never replace existing real evidence IDs.
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        if (fixture.get("planted") is not True or fixture.get("provenance") != "sample"
                or fixture.get("synthetic") is not True
                or fixture.get("evidence_tier") != "T-sim"):
            raise ValueError("Demo investigation evidence requires synthetic provenance")
        for key in ("alerts", "pipelines", "schema_changes", "dependencies", "recurrences", "correlations", "blast_radius"):
            additions = fixture.get(key, {})
            if not isinstance(additions, dict) or not isinstance(source[key], dict):
                raise ValueError(f"Invalid demo evidence mapping: {key}")
            if set(additions) & set(source[key]):
                raise ValueError(f"Demo evidence would overwrite existing {key}")
            for identity, value in additions.items():
                if key == "alerts":
                    if not isinstance(value, dict):
                        raise ValueError("Invalid demo alert")
                    value = {**value, "planted": True, "provenance": "sample", "synthetic": True, "evidence_tier": "T-sim"}
                source[key][identity] = value
    return source


def _normalize_data_source(data_source: Any) -> dict[str, Any]:
    if isinstance(data_source, dict):
        source = dict(data_source)
    else:
        source = build_dataops_evidence_source(data_source)
    for key in ("alerts", "pipelines", "schema_changes", "dependencies", "recurrences", "correlations", "blast_radius"):
        value = source.get(key)
        source[key] = value if isinstance(value, dict) else {}
    return source


def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _factor(alert: dict[str, Any], name: str) -> float:
    factors = alert.get("factors")
    if isinstance(factors, dict):
        return _clamp(factors.get(name, 0.0))
    return 0.0


def _clamped_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _clamp(value: Any) -> float:
    return max(0.0, min(1.0, _clamped_float(value, 0.0)))


def _positive_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) and number > 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _nested(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return {}
        current = current.get(key)
    return dict(current) if isinstance(current, dict) else {}


def _flatten_tree(tree: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for child in tree.get("children", []) if isinstance(tree.get("children"), list) else []:
        if not isinstance(child, dict):
            continue
        system = child.get("system")
        if system:
            result.append(str(system))
        result.extend(_flatten_tree(child))
    return result


__all__ = [
    "DataOpsEvidenceProvider",
    "CONNECTOR_GATED_SOURCES",
    "FACTOR_NAMES",
    "build_dataops_evidence_source",
]
