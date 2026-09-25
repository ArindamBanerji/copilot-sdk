"""VLD showcase preseed data for DataOps demo beats."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .evidence_provider import build_dataops_evidence_source


VLD_DO1_ALERT_ID = "VLD-DO-1"
VLD_DO2_ALERT_ID = "VLD-DO-2"
VLD_S1_ALERT_ID = "VLD-DO-S1"


def seed_vld_dataops_showcase(data_source: Any = None) -> dict[str, Any]:
    """Seed three idempotent DataOps VLD showcase alerts into a data source."""

    source = _source(data_source)
    _ensure_maps(source)

    source["alerts"][VLD_DO1_ALERT_ID] = {
        "alert_id": VLD_DO1_ALERT_ID,
        "event_id": VLD_DO1_ALERT_ID,
        "title": "Elevated latency on order_ingestion pipeline",
        "description": "Moderate latency hides a schema fanout root cause; the first schema read flips the decision and the dependency read reinforces it.",
        "system": "order_ingestion",
        "system_name": "order_ingestion",
        "dataset": "orders_daily",
        "category": "pipeline_failure",
        "surface_action": "investigate",
        "expected_vld_action": "escalate_to_owner",
        "severity": "high",
        "recurrence_count": 2,
        "factors": {
            "impact_scope": 0.1276,
            "source_reliability": 0.3236,
            "recurrence_frequency": 0.5006,
            "downstream_urgency": 0.6754,
            "data_freshness": 0.6225,
            "business_criticality": 0.8266,
        },
    }
    source["schema_changes"]["order_ingestion"] = [
        {
            "source_table": "SAP_MARA",
            "column": "MATKL_V2",
            "change_type": "schema_expansion",
            "detected": "2026-09-10T16:20:00Z",
            "downstream_impact": 9,
            "impacted_systems": ["pricing_engine", "inventory_sync", "billing_api"],
            "new_codes": 340000,
            "proposed_fix": "Normalize MATKL_V2 before order ingestion joins fan out.",
        }
    ]
    source["dependencies"]["order_ingestion"] = {
        "downstream": ["pricing_engine", "inventory_sync", "billing_api"],
        "value": 0.85,
        "confidence": 0.88,
    }
    source["correlations"][VLD_DO1_ALERT_ID] = {
        "correlated_alerts": ["pricing_engine_latency", "inventory_sync_retries", "billing_api_errors"],
        "value": 0.72,
        "confidence": 0.82,
    }
    source["blast_radius"][VLD_DO1_ALERT_ID] = {
        "affected_systems": ["pricing_engine", "inventory_sync", "billing_api"],
        "value": 0.84,
        "confidence": 0.80,
    }
    source["pipelines"]["order_ingestion"] = {
        "name": "order_ingestion",
        "display_name": "Order Ingestion",
        "status": "degraded",
        "source_reliability": 0.55,
        "business_criticality": 0.90,
        "upstream": ["sap_mara"],
        "downstream": ["pricing_engine", "inventory_sync", "billing_api"],
    }

    source["alerts"][VLD_DO2_ALERT_ID] = {
        "alert_id": VLD_DO2_ALERT_ID,
        "event_id": VLD_DO2_ALERT_ID,
        "title": "Data quality drop on billing_api",
        "description": "A familiar-looking billing quality alert has weaker historical recurrence than the surface suggests, then a new upstream dependency changes the decision.",
        "system": "billing_api",
        "system_name": "billing_api",
        "dataset": "billing_events",
        "category": "quality_anomaly",
        "surface_confidence": 0.62,
        "surface_action": "refer_to_specialist",
        "expected_vld_action": "escalate_to_owner",
        "severity": "high",
        "recurrence_count": 8,
        "factors": {
            "impact_scope": 0.7108,
            "source_reliability": 0.5718,
            "recurrence_frequency": 0.9189,
            "downstream_urgency": 0.3112,
            "data_freshness": 0.7742,
            "business_criticality": 0.971,
        },
    }
    source["recurrences"][VLD_DO2_ALERT_ID] = {
        "pattern": "billing_quality_drop",
        "value": 0.65,
        "confidence": 0.55,
        "prior_count": 8,
        "known_resolution": "Rebuild billing validation cache",
    }
    source["dependencies"]["billing_api"] = {
        "upstream": ["payments_hourly"],
        "new_upstream": ["data_lake_v2"],
        "downstream": ["revenue_mart", "customer_invoices"],
        "value": 0.88,
        "confidence": 0.82,
    }
    source["correlations"][VLD_DO2_ALERT_ID] = {
        "correlated_alerts": ["revenue_mart_missing_rows", "invoice_export_retries"],
        "value": 0.64,
        "confidence": 0.74,
    }
    source["pipelines"]["billing_api"] = {
        "name": "billing_api",
        "display_name": "Billing API",
        "status": "degraded",
        "source_reliability": 0.60,
        "business_criticality": 0.78,
        "upstream": ["payments_hourly", "data_lake_v2"],
        "downstream": ["revenue_mart", "customer_invoices"],
    }

    source["alerts"][VLD_S1_ALERT_ID] = {
        "alert_id": VLD_S1_ALERT_ID,
        "event_id": VLD_S1_ALERT_ID,
        "title": "Scheduled maintenance window on staging_etl",
        "description": "Known maintenance window with strong source reliability and low downstream impact.",
        "system": "staging_etl",
        "system_name": "staging_etl",
        "dataset": "staging_events",
        "category": "pipeline_failure",
        "surface_action": "auto_approve",
        "expected_vld_action": "auto_approve",
        "severity": "low",
        "recurrence_count": 0,
        "factors": {
            "impact_scope": 0.1148601779890048,
            "source_reliability": 0.5414560929201857,
            "recurrence_frequency": 0.23465565901226745,
            "downstream_urgency": 0.530987929219016,
            "data_freshness": 0.9007745072142764,
            "business_criticality": 0.32200758172461463,
        },
    }
    source["pipelines"]["staging_etl"] = {
        "name": "staging_etl",
        "display_name": "Staging ETL",
        "status": "ok",
        "source_reliability": 0.95,
        "business_criticality": 0.10,
        "upstream": [],
        "downstream": [],
    }
    source["vld_showcase_alert_ids"] = [VLD_DO1_ALERT_ID, VLD_DO2_ALERT_ID, VLD_S1_ALERT_ID]
    return source


def _source(data_source: Any) -> dict[str, Any]:
    if isinstance(data_source, dict):
        return data_source
    if data_source is None:
        return build_dataops_evidence_source()
    if isinstance(data_source, (str, Path)):
        return build_dataops_evidence_source(data_source)
    return build_dataops_evidence_source()


def _ensure_maps(source: dict[str, Any]) -> None:
    for key in ("alerts", "pipelines", "schema_changes", "dependencies", "recurrences", "correlations", "blast_radius"):
        if not isinstance(source.get(key), dict):
            source[key] = {}


__all__ = [
    "VLD_DO1_ALERT_ID",
    "VLD_DO2_ALERT_ID",
    "VLD_S1_ALERT_ID",
    "seed_vld_dataops_showcase",
]
