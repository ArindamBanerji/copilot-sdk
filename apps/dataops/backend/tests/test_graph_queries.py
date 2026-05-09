from __future__ import annotations

import pytest

from app.graph_queries import DataOpsGraphClient, FALLBACK_DIR, READ_ONLY_FORBIDDEN


class FakeAGEClient:
    serialize_for_age = staticmethod(lambda value: "'" + str(value).replace("'", "\\'") + "'")

    def __init__(self, rows_by_key):
        self.rows_by_key = rows_by_key
        self.queries = []

    async def run_query(self, query, parameters=None):
        self.queries.append((query, parameters))
        if "downstream_count" in query:
            return [{"downstream_count": 4}]
        if "min_sla" in query:
            return [{"min_sla": 15}]
        if "prior_count" in query:
            return [{"prior_count": 6}]
        return self.rows_by_key.get("default", [])


class GraphModeAGEClient:
    serialize_for_age = staticmethod(lambda value: "'" + str(value).replace("'", "\\'") + "'")

    def __init__(self):
        self.queries = []

    async def run_query(self, query, parameters=None):
        self.queries.append((query, parameters))
        if "RETURN alert, system" in query:
            return [
                {
                    "alert": {
                        "alert_id": "DQ-015",
                        "category": "freshness_violation",
                        "factors": {
                            "source_reliability": 0.51,
                            "data_freshness": 0.12,
                            "business_criticality": 0.93,
                        },
                    },
                    "system": {
                        "name": "graph_root",
                        "source_reliability": 0.51,
                        "business_criticality": 0.93,
                        "sla_minutes": 20,
                    },
                }
            ]
        if "collect(DISTINCT {parent:" in query:
            return [
                {
                    "system": {"name": "graph_root", "sla_minutes": 20, "business_criticality": 0.93},
                    "edges": [
                        {
                            "parent": "graph_root",
                            "child": "graph_child_a",
                            "child_sla": 15,
                            "child_criticality": 0.88,
                        },
                        {
                            "parent": "graph_child_a",
                            "child": "graph_child_b",
                            "child_sla": 30,
                            "child_criticality": 0.72,
                        },
                    ],
                }
            ]
        if "downstream_count" in query:
            return [{"downstream_count": 5}]
        if "min_sla" in query:
            return [{"min_sla": 15}]
        if "prior_count" in query:
            return [{"prior_count": 2}]
        return []


class GraphMissAGEClient:
    serialize_for_age = staticmethod(lambda value: "'" + str(value).replace("'", "\\'") + "'")

    def __init__(self):
        self.queries = []

    async def run_query(self, query, parameters=None):
        self.queries.append((query, parameters))
        if "RETURN alert, system" in query:
            return []
        if "downstream_count" in query:
            return [{"downstream_count": 8}]
        if "min_sla" in query:
            return [{"min_sla": 10}]
        if "prior_count" in query:
            return [{"prior_count": 1}]
        return []


@pytest.mark.asyncio
async def test_fixture_fallback():
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)

    assert client.is_graph_connected is False
    assert client.graph_source == "fixture"
    assert (await client.get_pipelines())["source"] == "fixture"


@pytest.mark.asyncio
async def test_get_pipelines_fixture():
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
    payload = await client.get_pipelines()

    assert payload["source"] == "fixture"
    assert len(payload["pipelines"]) == 9
    warehouse = next(item for item in payload["pipelines"] if item["name"] == "warehouse_etl")
    assert warehouse["upstream_count"] == 4
    assert warehouse["downstream_count"] == 1


@pytest.mark.asyncio
async def test_get_alerts_fixture():
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
    payload = await client.get_alerts()

    assert payload["source"] == "fixture"
    assert len(payload["alerts"]) == 20
    assert {alert["alert_id"] for alert in payload["alerts"]} >= {"DQ-001", "DQ-015"}


@pytest.mark.asyncio
async def test_impact_scope_computation_with_mocked_client():
    fake = FakeAGEClient({})
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=fake)
    payload = await client.compute_impact_scope("warehouse_etl")

    assert payload["source"] == "graph"
    assert payload["downstream_count"] == 4
    assert payload["value"] == 0.5
    assert "$" not in fake.queries[-1][0]


@pytest.mark.asyncio
async def test_downstream_urgency_computation_with_mocked_client():
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=FakeAGEClient({}))
    payload = await client.compute_downstream_urgency("billing_api")

    assert payload["source"] == "graph"
    assert payload["min_sla"] == 15
    assert payload["value"] == 0.875


@pytest.mark.asyncio
async def test_recurrence_computation_with_mocked_client():
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=FakeAGEClient({}))
    payload = await client.compute_recurrence("crm_sync", "pipeline_failure")

    assert payload["source"] == "graph"
    assert payload["prior_count"] == 6
    assert payload["value"] == 0.5


@pytest.mark.asyncio
async def test_graph_connected_recurrence_prefers_graph_for_fixture_alert_id():
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=GraphModeAGEClient())
    payload = await client.get_recurrence("DQ-015")

    assert payload["source"] == "graph"
    assert payload["system"] == "graph_root"
    assert payload["prior_count"] == 2
    assert payload["recurrence_frequency"] == 0.1667


@pytest.mark.asyncio
async def test_graph_connected_factors_use_graph_values_for_fixture_alert_id():
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=GraphModeAGEClient())
    payload = await client.get_factors("DQ-015")

    assert payload["source"] == "graph"
    assert payload["factors"]["source_reliability"]["source"] == "graph"
    assert payload["factors"]["source_reliability"]["value"] == 0.51
    assert payload["factors"]["data_freshness"]["source"] == "graph"
    assert payload["factors"]["data_freshness"]["value"] == 0.12
    assert payload["factors"]["business_criticality"]["value"] == 0.93


@pytest.mark.asyncio
async def test_graph_connected_blast_radius_returns_nested_tree():
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=GraphModeAGEClient())
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
async def test_graph_miss_recurrence_falls_back_pure_fixture():
    fake = GraphMissAGEClient()
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=fake)
    payload = await client.get_recurrence("DQ-015")

    assert payload["source"] == "fixture"
    assert payload["system"] == "crm_sync"
    assert payload["prior_count"] == 9
    assert payload["recurrence_frequency"] == 0.75
    assert not any("prior_count" in query for query, _params in fake.queries)


@pytest.mark.asyncio
async def test_graph_miss_factors_fall_back_pure_fixture():
    fake = GraphMissAGEClient()
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client=fake)
    payload = await client.get_factors("DQ-015")

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
    assert not any("downstream_count" in query for query, _params in fake.queries)
    assert not any("min_sla" in query for query, _params in fake.queries)
    assert not any("prior_count" in query for query, _params in fake.queries)


@pytest.mark.asyncio
async def test_fixture_blast_radius_matches_graph_shape():
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
    payload = await client.get_blast_radius("DQ-001")

    assert payload["source"] == "fixture"
    assert payload["engine"] == {"graph": "fixture"}
    assert {"affected_system", "downstream_tree", "total_affected", "max_criticality", "min_sla"} <= set(payload)
    assert payload["affected_system"] == payload["system"]
    assert payload["downstream_tree"] == payload["tree"]
    assert payload["downstream_tree"]["children"][0]["children"] == []
    assert payload["total_affected"] >= 1
    assert payload["max_criticality"] > 0
    assert payload["min_sla"] > 0


@pytest.mark.asyncio
async def test_blast_radius_tree_building():
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
    payload = await client.get_blast_radius("DQ-015")

    assert payload["source"] == "fixture"
    assert payload["system"] == "crm_sync"
    child_names = {child["system"] for child in payload["tree"]["children"]}
    assert {"warehouse_etl", "marketing_db"} <= child_names


@pytest.mark.asyncio
async def test_get_factors_has_all_six():
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
    payload = await client.get_factors("DQ-001")

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
async def test_no_live_graph_required(monkeypatch):
    monkeypatch.delenv("GRAPH_DSN", raising=False)
    client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
    payload = await client.get_alert("DQ-015")

    assert client.is_graph_connected is False
    assert payload["source"] == "fixture"
    assert payload["alert"]["alert_id"] == "DQ-015"


def test_graph_query_strings_are_read_only():
    assert READ_ONLY_FORBIDDEN.search("MATCH (n) RETURN n") is None
    assert READ_ONLY_FORBIDDEN.search("CREATE (n) RETURN n") is not None
