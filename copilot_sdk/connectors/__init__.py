"""Connector registry for Data Intelligence source connectors."""

from __future__ import annotations

from copilot_sdk.connectors.airflow_connector import AirflowConnector
from copilot_sdk.connectors.dbt_connector import DBTConnector
from copilot_sdk.connectors.snowflake_meta import SnowflakeMetaConnector

CONNECTOR_REGISTRY: dict[str, type] = {
    "snowflake": SnowflakeMetaConnector,
    "dbt": DBTConnector,
    "airflow": AirflowConnector,
}


def get_connector(name: str) -> type:
    """Lookup connector class by source name."""
    try:
        return CONNECTOR_REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"Unknown connector: {name}") from exc


def list_connectors() -> list[str]:
    """Return registered connector names."""
    return sorted(CONNECTOR_REGISTRY)


__all__ = [
    "AirflowConnector",
    "CONNECTOR_REGISTRY",
    "DBTConnector",
    "SnowflakeMetaConnector",
    "get_connector",
    "list_connectors",
]
