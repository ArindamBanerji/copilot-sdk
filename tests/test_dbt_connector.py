from __future__ import annotations

from copilot_sdk.connectors import get_connector, list_connectors
from copilot_sdk.connectors.dbt_connector import DBTConnector
from copilot_sdk.connectors.mock_dbt import MockDBTConnector
from copilot_sdk.di import BaseSourceProfiler, IntelligenceMapBuilder


def test_protocol_compliance() -> None:
    connector = DBTConnector()
    for name in ("source_name", "entity_type", "trust_tier", "fetch", "validate"):
        assert hasattr(connector, name)


def test_mock_fetch_models() -> None:
    assert len(MockDBTConnector().fetch()) == 15


def test_mock_fetch_tests() -> None:
    assert len(MockDBTConnector().fetch_tests()) == 8


def test_mock_freshness() -> None:
    rows = MockDBTConnector().fetch_freshness()
    assert len(rows) == 15
    assert all("hours_since_run" in row for row in rows)


def test_validate_valid() -> None:
    assert MockDBTConnector().validate({"model_name": "stg_orders", "status": "pass", "execution_time_s": 1})


def test_validate_missing_model() -> None:
    assert not MockDBTConnector().validate({"status": "pass", "execution_time_s": 1})


def test_validate_bad_status() -> None:
    assert not MockDBTConnector().validate({"model_name": "stg_orders", "status": "bad", "execution_time_s": 1})


def test_fixtures_dbt_naming() -> None:
    names = {row["model_name"] for row in MockDBTConnector().fetch()}
    assert any(name.startswith("stg_") for name in names)
    assert any(name.startswith("int_") for name in names)
    assert any(name.startswith("fct_") for name in names)
    assert any(name.startswith("dim_") for name in names)
    assert any(name.startswith("rpt_") for name in names)


def test_test_statuses_mixed() -> None:
    statuses = {row["status"] for row in MockDBTConnector().fetch_tests()}
    assert {"pass", "warn", "error"} <= statuses


def test_execution_times_positive() -> None:
    assert all(row["execution_time_s"] >= 0 for row in MockDBTConnector().fetch())


def test_stale_models_flagged() -> None:
    stale = [row for row in MockDBTConnector().fetch_freshness() if row["is_stale"]]
    assert {row["model_name"] for row in stale} == {"stg_customers", "fct_orders"}
    assert all(row["hours_since_run"] > 24 for row in stale)


def test_profiler_integration() -> None:
    profile = BaseSourceProfiler(MockDBTConnector()).profile(["latest"])
    assert profile.source_name == "dbt"
    assert profile.record_count == 15


def test_provenance_demo() -> None:
    connector = MockDBTConnector()
    records = connector.fetch() + connector.fetch_tests() + connector.fetch_freshness()
    assert all(record["provenance"] == "demo" for record in records)


def test_credential_safety() -> None:
    connector = DBTConnector(api_token="secret-token", account_id="acct")
    assert "secret-token" not in str(connector)
    assert "secret-token" not in repr(connector)


def test_credential_not_in_error() -> None:
    conn = DBTConnector(api_token="SECRET_TOKEN_12345")
    try:
        conn.fetch()
    except Exception as e:
        assert "SECRET_TOKEN_12345" not in str(e)


def test_to_map_nodes_and_registry() -> None:
    assert get_connector("dbt") is DBTConnector
    assert "dbt" in list_connectors()
    nodes = MockDBTConnector().to_map_nodes()
    colors = {node["source_name"]: node["status_color"] for node in nodes}
    assert colors["stg_orders"] == "green"
    assert colors["stg_customers"] == "amber"
    assert colors["fct_orders"] == "red"
    rendered = IntelligenceMapBuilder().build(sources=nodes).to_dict()
    assert len(rendered["nodes"]) == 15
