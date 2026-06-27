from __future__ import annotations

from collections import Counter

from copilot_sdk.connectors import get_connector, list_connectors
from copilot_sdk.connectors.airflow_connector import AirflowConnector
from copilot_sdk.connectors.mock_airflow import MockAirflowConnector
from copilot_sdk.di import BaseSourceProfiler, IntelligenceMapBuilder


def test_protocol_compliance() -> None:
    connector = AirflowConnector()
    for name in ("source_name", "entity_type", "trust_tier", "fetch", "validate"):
        assert hasattr(connector, name)


def test_mock_fetch_dags() -> None:
    dags = {row["dag_id"] for row in MockAirflowConnector().fetch()}
    assert len(dags) == 8


def test_mock_fetch_tasks() -> None:
    tasks = MockAirflowConnector().fetch_tasks("etl_orders", "scheduled__001")
    assert len(tasks) >= 5
    assert all(task["dag_id"] == "etl_orders" for task in tasks)


def test_mock_dag_stats_and_success_rate() -> None:
    connector = MockAirflowConnector()
    all_runs = connector.fetch()
    states = Counter(run["state"] for run in all_runs)
    assert states["success"] / len(all_runs) == 0.8
    stats = connector.fetch_dag_stats("etl_orders")
    assert stats["run_count"] > 0
    assert 0 <= stats["success_rate"] <= 1


def test_validate_valid() -> None:
    assert MockAirflowConnector().validate({"dag_id": "etl_orders", "state": "success", "duration_seconds": 1})


def test_validate_missing_dag() -> None:
    assert not MockAirflowConnector().validate({"state": "success", "duration_seconds": 1})


def test_validate_bad_state() -> None:
    assert not MockAirflowConnector().validate({"dag_id": "etl_orders", "state": "unknown", "duration_seconds": 1})


def test_fixtures_realistic() -> None:
    dags = {row["dag_id"] for row in MockAirflowConnector().fetch()}
    assert {"etl_orders", "sync_inventory", "report_daily", "data_quality"} <= dags


def test_run_states_mixed() -> None:
    states = {row["state"] for row in MockAirflowConnector().fetch()}
    assert {"success", "failed", "running"} <= states


def test_duration_positive() -> None:
    assert all(row["duration_seconds"] >= 0 for row in MockAirflowConnector().fetch())


def test_failure_pattern() -> None:
    assert MockAirflowConnector().fetch_dag_stats("etl_orders")["failure_pattern"] == "Monday"


def test_profiler_integration() -> None:
    profile = BaseSourceProfiler(MockAirflowConnector()).profile(["all"])
    assert profile.source_name == "airflow"
    assert profile.record_count == 30


def test_provenance_demo() -> None:
    connector = MockAirflowConnector()
    records = connector.fetch() + connector.fetch_tasks("etl_orders", "scheduled__001")
    records.append(connector.fetch_dag_stats("etl_orders"))
    assert all(record["provenance"] == "demo" for record in records)


def test_credential_safety() -> None:
    connector = AirflowConnector(password="secret-password", token="secret-token")
    assert "secret-password" not in str(connector)
    assert "secret-token" not in str(connector)
    assert "secret-password" not in repr(connector)
    assert "secret-token" not in repr(connector)


def test_credential_not_in_error() -> None:
    conn = AirflowConnector(password="SECRET_PASS_12345", token="SECRET_TOKEN_12345")
    try:
        conn.fetch()
    except Exception as e:
        msg = str(e)
        assert "SECRET_PASS_12345" not in msg
        assert "SECRET_TOKEN_12345" not in msg


def test_to_map_nodes_and_registry() -> None:
    assert get_connector("airflow") is AirflowConnector
    assert "airflow" in list_connectors()
    nodes = MockAirflowConnector().to_map_nodes()
    colors = {node["source_name"]: node["status_color"] for node in nodes}
    assert colors["etl_orders"] == "red"
    assert colors["data_quality"] == "green"
    assert colors["ml_training"] == "amber"
    rendered = IntelligenceMapBuilder().build(sources=nodes).to_dict()
    assert len(rendered["nodes"]) == 8
