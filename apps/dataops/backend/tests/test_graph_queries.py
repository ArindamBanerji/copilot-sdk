from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock
from ci_platform.graph.age_client import AGEClient
from fastapi import HTTPException

from app.graph_queries import DataOpsGraphClient, FALLBACK_DIR, READ_ONLY_FORBIDDEN


def _graph_client(disposable_age, *, empty=False):
    age = disposable_age.client()
    if not empty:
        store = disposable_age.store("dataops")._store
        for name, count in (("warehouse_etl", 4), ("billing_api", 1), ("crm_sync", 0)):
            store._run_query(f"CREATE (n:PipelineSystem {{domain: 'dataops', name: '{name}', sla_minutes: 120}})")
            for index in range(count):
                store._run_query(f"MATCH (p:PipelineSystem {{name: '{name}'}}) CREATE (p)-[:FEEDS]->"
                    f"(:PipelineSystem {{domain: 'dataops', name: '{name}_{index}', sla_minutes: 15}})")
        for index in range(6):
            store._run_query("MATCH (p:PipelineSystem {name: 'crm_sync'}) CREATE "
                f"(:DataQualityAlert {{domain: 'dataops', alert_id: 'prior-{index}', category: 'pipeline_failure'}})-[:AFFECTS]->(p)")
        store._run_query("""CREATE (root:PipelineSystem {domain:'dataops', name:'graph_root', sla_minutes:20,
            source_reliability:0.51, business_criticality:0.93})-[:FEEDS]->
            (a:PipelineSystem {domain:'dataops', name:'graph_child_a', sla_minutes:15, business_criticality:0.88})-[:FEEDS]->
            (b:PipelineSystem {domain:'dataops', name:'graph_child_b', sla_minutes:30, business_criticality:0.72})""")
        for alert_id in ("DQ-015", "prior-root"):
            store._run_query("MATCH (p:PipelineSystem {name:'graph_root'}) CREATE "
                f"(:DataQualityAlert {{domain:'dataops', alert_id:'{alert_id}', category:'freshness_violation', "
                "factors:{source_reliability:0.51, data_freshness:0.12, business_criticality:0.93}})-[:AFFECTS]->(p)")
    age.run_query = AsyncMock(wraps=age.run_query)
    return age


def test_age_client_constructor_receives_graph_name(monkeypatch, no_graph):

    factory = Mock(wraps=AGEClient)

    monkeypatch.setenv("DATAOPS_ACTIVE_GRAPH_BACKEND", "age")
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_DSN", "host=active port=5433 dbname=dataops")
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_GRAPH", "dataops_graph")

    client = DataOpsGraphClient(
        fallback_dir=FALLBACK_DIR,
        age_client_cls=factory,
    )

    assert client.is_graph_connected is True
    assert [call.kwargs for call in factory.call_args_list] == [
        {
            "dsn": "host=active port=5433 dbname=dataops",
            "graph_name": "dataops_graph",
        }
    ]


def test_dataops_graph_client_uses_active_config(monkeypatch, no_graph):

    factory = Mock(wraps=AGEClient)

    monkeypatch.setenv("DATAOPS_ACTIVE_GRAPH_BACKEND", "age")
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_DSN", "host=active port=5433 dbname=dataops")
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_GRAPH", "governed_copilot_graph")
    monkeypatch.setenv("GRAPH_DSN", "host=generic port=5433 dbname=generic")

    DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client_cls=factory)

    assert [call.kwargs for call in factory.call_args_list] == [{"dsn": "host=active port=5433 dbname=dataops", "graph_name": "governed_copilot_graph"}]


def test_dataops_graph_client_uses_generic_age_config(monkeypatch, no_graph):

    factory = Mock(wraps=AGEClient)

    monkeypatch.delenv("DATAOPS_ACTIVE_GRAPH_BACKEND", raising=False)
    monkeypatch.delenv("DATAOPS_ACTIVE_AGE_DSN", raising=False)
    monkeypatch.delenv("DATAOPS_ACTIVE_AGE_GRAPH", raising=False)
    monkeypatch.setenv("GRAPH_BACKEND", "age")
    monkeypatch.setenv("GRAPH_DSN", "host=generic port=5433 dbname=shared")
    monkeypatch.setenv("AGE_GRAPH_NAME", "soc_graph")

    client = DataOpsGraphClient(
        fallback_dir=FALLBACK_DIR,
        age_client_cls=factory,
    )

    assert client.is_graph_connected is True
    assert [call.kwargs for call in factory.call_args_list] == [
        {
            "dsn": "host=generic port=5433 dbname=shared",
            "graph_name": "soc_graph",
        }
    ]


def test_dataops_graph_client_preserves_generic_aliases(monkeypatch, no_graph):
    monkeypatch.delenv("DATAOPS_ACTIVE_AGE_DSN", raising=False)
    monkeypatch.delenv("DATAOPS_ACTIVE_AGE_GRAPH", raising=False)
    monkeypatch.setenv("DATAOPS_ACTIVE_GRAPH_BACKEND", "age")
    monkeypatch.setenv("GRAPH_DSN", "host=generic port=5433 dbname=generic")
    monkeypatch.setenv("AGE_GRAPH_NAME", "generic_graph")

    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
    assert client.graph_config.dsn == "host=generic port=5433 dbname=generic"
    assert dict(client.graph_config.source_keys)["dsn"] == "GRAPH_DSN"
    assert client.graph_config.graph == "generic_graph"


@pytest.mark.asyncio
async def test_fixture_fallback(no_graph):
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)

    assert client.is_graph_connected is False
    assert client.graph_source == "fixture"
    assert (await client.get_pipelines())["source"] == "fixture"


@pytest.mark.asyncio
async def test_get_pipelines_fixture(no_graph):
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
    payload = await client.get_pipelines()

    assert payload["source"] == "fixture"
    assert len(payload["pipelines"]) == 9
    sap_mm = next(item for item in payload["pipelines"] if item["name"] == "sap_mm")
    assert sap_mm["upstream_count"] == 1
    assert sap_mm["downstream_count"] == 5


@pytest.mark.asyncio
async def test_get_alerts_fixture(no_graph):
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
    payload = await client.get_alerts()

    assert payload["source"] == "fixture"
    assert len(payload["alerts"]) == 21
    assert {alert["alert_id"] for alert in payload["alerts"]} >= {"ALERT-TIRE-001", "ALERT-TIRE-015"}


@pytest.mark.asyncio
@pytest.mark.age
async def test_impact_scope_computation_with_seeded_graph(disposable_age):
    fake = _graph_client(disposable_age)
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=fake)
    payload = await client.compute_impact_scope("warehouse_etl")

    assert payload["source"] == "graph"
    assert payload["downstream_count"] == 4
    assert payload["value"] == 0.5
    assert "$" not in fake.run_query.call_args_list[-1].args[0]


@pytest.mark.asyncio
@pytest.mark.age
async def test_downstream_urgency_computation_with_seeded_graph(disposable_age):
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=_graph_client(disposable_age))
    payload = await client.compute_downstream_urgency("billing_api")

    assert payload["source"] == "graph"
    assert payload["min_sla"] == 15
    assert payload["value"] == 0.875


@pytest.mark.asyncio
@pytest.mark.age
async def test_recurrence_computation_with_seeded_graph(disposable_age):
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=_graph_client(disposable_age))
    payload = await client.compute_recurrence("crm_sync", "pipeline_failure")

    assert payload["source"] == "graph"
    assert payload["prior_count"] == 6
    assert payload["value"] == 0.5


@pytest.mark.asyncio
@pytest.mark.age
async def test_graph_connected_recurrence_prefers_graph_for_fixture_alert_id(disposable_age):
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=_graph_client(disposable_age))
    payload = await client.get_recurrence("DQ-015")

    assert payload["source"] == "graph"
    assert payload["system"] == "graph_root"
    assert payload["prior_count"] == 2
    assert payload["recurrence_frequency"] == 0.1667


@pytest.mark.asyncio
@pytest.mark.age
async def test_graph_connected_factors_use_graph_values_for_fixture_alert_id(disposable_age):
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=_graph_client(disposable_age))
    payload = await client.get_factors("DQ-015")

    assert payload["source"] == "graph"
    assert payload["factors"]["source_reliability"]["source"] == "graph"
    assert payload["factors"]["source_reliability"]["value"] == 0.51
    assert payload["factors"]["data_freshness"]["source"] == "graph"
    assert payload["factors"]["data_freshness"]["value"] == 0.12
    assert payload["factors"]["business_criticality"]["value"] == 0.93


@pytest.mark.asyncio
@pytest.mark.age
async def test_graph_connected_blast_radius_returns_nested_tree(disposable_age):
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=_graph_client(disposable_age))
    payload = await client.get_blast_radius("DQ-015")

    assert payload["source"] == "graph"
    assert payload["affected_system"] == "graph_root"
    assert "downstream" not in payload
    assert payload["downstream_tree"]["system"] == "graph_root"
    assert payload["downstream_tree"]["children"][0]["system"] == "graph_child_a"
    assert payload["downstream_tree"]["children"][0]["children"][0]["system"] == "graph_child_b"
    assert payload["total_affected"] == 2
    assert payload["min_sla"] == 15


@pytest.mark.asyncio
@pytest.mark.age
async def test_graph_miss_recurrence_age_required_raises_503(disposable_age):
    fake = _graph_client(disposable_age, empty=True)
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=fake)

    with pytest.raises(HTTPException) as exc_info:
        await client.get_recurrence("ALERT-TIRE-015")

    assert exc_info.value.status_code == 503
    assert not any("prior_count" in query for query in [call.args[0] for call in fake.run_query.call_args_list])


@pytest.mark.asyncio
async def test_graph_miss_recurrence_falls_back_pure_fixture(no_graph):
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
    payload = await client.get_recurrence("ALERT-TIRE-015")

    assert payload["source"] == "fixture"
    assert payload["system"] == "logistics_dhl"
    assert payload["prior_count"] == 9
    assert payload["recurrence_frequency"] == 0.75


@pytest.mark.asyncio
@pytest.mark.age
async def test_graph_miss_factors_age_required_raises_503(disposable_age):
    fake = _graph_client(disposable_age, empty=True)
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=fake)

    with pytest.raises(HTTPException) as exc_info:
        await client.get_factors("ALERT-TIRE-015")

    assert exc_info.value.status_code == 503
    assert not any("downstream_count" in query for query in [call.args[0] for call in fake.run_query.call_args_list])
    assert not any("min_sla" in query for query in [call.args[0] for call in fake.run_query.call_args_list])
    assert not any("prior_count" in query for query in [call.args[0] for call in fake.run_query.call_args_list])


@pytest.mark.asyncio
async def test_graph_miss_factors_fall_back_pure_fixture(no_graph):
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
    payload = await client.get_factors("ALERT-TIRE-015")

    assert payload["source"] == "fixture"
    assert set(payload["factors"]) == {
        "impact_scope",
        "source_reliability",
        "recurrence_frequency",
        "downstream_urgency",
        "data_freshness",
        "business_criticality",
    }
    assert {factor["source"] for factor in payload["factors"].values()} == {"fixture"}
    assert payload["factors"]["recurrence_frequency"]["value"] == 0.75


@pytest.mark.asyncio
async def test_fixture_blast_radius_matches_graph_shape(no_graph):
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
    payload = await client.get_blast_radius("ALERT-TIRE-001")

    assert payload["source"] == "fixture"
    assert payload["engine"] == {"graph": "fixture"}
    assert {"affected_system", "downstream_tree", "total_affected", "max_criticality", "min_sla"} <= set(payload)
    assert payload["affected_system"] == payload["system"]
    assert payload["downstream_tree"] == payload["tree"]
    assert payload["downstream_tree"]["children"]
    assert payload["total_affected"] >= 1
    assert payload["max_criticality"] > 0
    assert payload["min_sla"] > 0


@pytest.mark.asyncio
async def test_blast_radius_tree_building(no_graph):
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
    payload = await client.get_blast_radius("ALERT-TIRE-015")

    assert payload["source"] == "fixture"
    assert payload["system"] == "logistics_dhl"
    child_names = {child["system"] for child in payload["tree"]["children"]}
    assert {"warehouse_wms", "mes_production"} <= child_names


@pytest.mark.asyncio
async def test_get_factors_has_all_six(no_graph):
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
    payload = await client.get_factors("ALERT-TIRE-001")

    assert payload["source"] == "fixture"
    assert payload["all_auto_computed"] is True
    assert set(payload["factors"]) == {
        "impact_scope",
        "source_reliability",
        "recurrence_frequency",
        "downstream_urgency",
        "data_freshness",
        "business_criticality",
    }
    for factor in payload["factors"].values():
        assert {"value", "source", "detail"} <= set(factor)


@pytest.mark.asyncio
async def test_no_live_graph_required(no_graph):
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
    payload = await client.get_alert("ALERT-TIRE-015")

    assert client.is_graph_connected is False
    assert payload["source"] == "fixture"
    assert payload["alert"]["alert_id"] == "ALERT-TIRE-015"


def test_graph_query_strings_are_read_only():
    assert READ_ONLY_FORBIDDEN.search("MATCH (n) RETURN n") is None
    assert READ_ONLY_FORBIDDEN.search("CREATE (n) RETURN n") is not None


