from __future__ import annotations

import pytest

from copilot_sdk.connectors import get_connector, list_connectors
from copilot_sdk.connectors.mock_snowflake import MockSnowflakeConnector
from copilot_sdk.connectors.snowflake_meta import SnowflakeMetaConnector
from copilot_sdk.di import BaseSourceProfiler, IntelligenceMapBuilder


def test_protocol_compliance() -> None:
    connector = SnowflakeMetaConnector()
    for name in ("source_name", "entity_type", "trust_tier", "fetch", "validate"):
        assert hasattr(connector, name)


def test_mock_fetch_tables() -> None:
    assert len(MockSnowflakeConnector().fetch()) == 10


def test_mock_fetch_columns() -> None:
    columns = MockSnowflakeConnector().fetch_columns("orders")
    assert columns
    assert columns[0]["table_name"] == "orders"


def test_mock_query_history() -> None:
    queries = MockSnowflakeConnector().fetch_query_history()
    assert len(queries) == 20
    assert all("SELECT" in row["query_text"] and "FROM" in row["query_text"] for row in queries)


def test_validate_valid() -> None:
    assert MockSnowflakeConnector().validate({"table_name": "orders", "row_count": 1})


def test_validate_missing_name() -> None:
    assert not MockSnowflakeConnector().validate({"row_count": 1})


def test_fixtures_realistic() -> None:
    names = {row["table_name"] for row in MockSnowflakeConnector().fetch()}
    assert {"orders", "customers", "suppliers", "invoices", "inventory"} <= names


def test_row_counts_positive() -> None:
    assert all(row["row_count"] >= 0 for row in MockSnowflakeConnector().fetch())


def test_column_types_valid() -> None:
    valid = {"VARCHAR", "INTEGER", "NUMBER", "TIMESTAMP_NTZ", "DATE", "BOOLEAN", "FLOAT"}
    assert {row["data_type"] for row in MockSnowflakeConnector().fetch_all_columns()} <= valid


def test_profiler_integration() -> None:
    profile = BaseSourceProfiler(MockSnowflakeConnector()).profile(["orders"])
    assert profile.source_name == "snowflake"
    assert profile.record_count == 1


def test_metadata_only() -> None:
    forbidden = {"customer_name", "email", "amount", "line_items", "address"}
    payload_keys = set().union(*(row.keys() for row in MockSnowflakeConnector().fetch()))
    assert payload_keys.isdisjoint(forbidden)


def test_provenance_demo() -> None:
    connector = MockSnowflakeConnector()
    records = connector.fetch() + connector.fetch_columns("orders") + connector.fetch_query_history()
    assert all(record["provenance"] == "demo" for record in records)


def test_credential_safety() -> None:
    connector = SnowflakeMetaConnector(account="acct", user="user", password="secret-password")
    assert "secret-password" not in str(connector)
    assert "secret-password" not in repr(connector)


def test_credential_not_in_error() -> None:
    connector = SnowflakeMetaConnector(password="secret-password")
    with pytest.raises(ValueError) as exc:
        connector.fetch_columns("")
    assert "secret-password" not in str(exc.value)


def test_to_map_nodes_and_registry() -> None:
    assert get_connector("snowflake") is SnowflakeMetaConnector
    assert "snowflake" in list_connectors()
    nodes = MockSnowflakeConnector().to_map_nodes()
    rendered = IntelligenceMapBuilder().build(sources=nodes).to_dict()
    assert len(rendered["nodes"]) == 10
    assert any(node["label"] == "orders" and node["record_count"] == 12_000_000 for node in rendered["nodes"])
