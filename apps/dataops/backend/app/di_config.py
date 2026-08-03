"""DataOps-specific configuration for Data Intelligence enrichment."""

from __future__ import annotations

import json
import os
from typing import Any


DEFAULT_FACTOR_TO_SOURCE_MAP: dict[str, str] = {
    "impact_scope": "graph_traversal",
    "source_reliability": "sap_s4hana",
    "recurrence_frequency": "alert_history",
    "downstream_urgency": "pipeline_graph",
    "data_freshness": "airflow_metadata",
    "business_criticality": "config",
}

SOURCE_COLUMN_BASELINES: dict[str, dict[str, float]] = {
    "sap_s4hana": {"customer_id": 0.99, "satisfaction_score": 0.14},
    "salesforce_crm": {"customer_id": 0.97, "account_tier": 0.82},
    "airflow_metadata": {"dag_id": 0.95, "freshness": 0.72},
    "alert_history": {"alert_category": 0.70, "recurrence_count": 0.65},
    "pipeline_graph": {"downstream_system": 0.88, "criticality": 0.91},
    "graph_traversal": {"impact_scope": 0.86, "affected_systems": 0.80},
    "config": {"business_criticality": 0.90, "owner": 0.78},
}

DATA_PRODUCTS: tuple[dict[str, Any], ...] = (
    {
        "product_id": "customer-360",
        "product_name": "Customer 360",
        "sources": ("sap_s4hana", "salesforce_crm"),
    },
    {
        "product_id": "operations-health",
        "product_name": "Operations Health",
        "sources": ("airflow_metadata", "pipeline_graph"),
    },
    {
        "product_id": "alert-intelligence",
        "product_name": "Alert Intelligence",
        "sources": ("alert_history", "graph_traversal"),
    },
)


def get_factor_to_source_map() -> dict[str, str]:
    """Return the default map with validated JSON environment overrides."""

    raw_override = os.environ.get("DATAOPS_FACTOR_TO_SOURCE_MAP")
    if not raw_override:
        return dict(DEFAULT_FACTOR_TO_SOURCE_MAP)
    try:
        override = json.loads(raw_override)
    except json.JSONDecodeError:
        return dict(DEFAULT_FACTOR_TO_SOURCE_MAP)
    if not isinstance(override, dict):
        return dict(DEFAULT_FACTOR_TO_SOURCE_MAP)
    result = dict(DEFAULT_FACTOR_TO_SOURCE_MAP)
    for factor, source in override.items():
        if isinstance(factor, str) and isinstance(source, str) and factor and source:
            result[factor] = source
    return result


def known_source_ids() -> set[str]:
    """Return source identifiers exposed by the DataOps DI contract."""

    mapped_sources = set(get_factor_to_source_map().values())
    return mapped_sources | set(SOURCE_COLUMN_BASELINES)
