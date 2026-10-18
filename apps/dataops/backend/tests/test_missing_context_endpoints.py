from __future__ import annotations


def test_context_provenance_contract_and_unknown_default(client) -> None:
    response = client.get("/api/context/provenance/billing_api")
    unknown = client.get("/api/context/provenance/unknown")

    assert response.status_code == unknown.status_code == 200
    assert {
        "system",
        "lineage",
        "sources",
        "freshness",
        "quality_score",
        "decision_id",
        "complete",
        "steps",
        "evidence_tier",
        "evidence_label",
    } <= response.json().keys()
    assert response.json()["lineage"]
    assert unknown.json()["system"] == "unknown"
    assert unknown.json()["lineage"] == []


def test_context_di_trust_contract_and_unknown_default(client) -> None:
    response = client.get("/api/context/di-trust/billing_api")
    unknown = client.get("/api/context/di-trust/unknown")

    assert response.status_code == unknown.status_code == 200
    assert {
        "system",
        "trust_score",
        "factors",
        "trend",
        "source_id",
        "trust_label",
        "conservation_status",
        "recommendation",
        "columns",
    } <= response.json().keys()
    assert response.json()["factors"]
    assert unknown.json()["trust_score"] == 0.0
    assert unknown.json()["factors"] == []


def test_context_di_consumers_contract_and_unknown_default(client) -> None:
    response = client.get("/api/context/di-consumers/billing_api")
    unknown = client.get("/api/context/di-consumers/unknown")

    assert response.status_code == unknown.status_code == 200
    assert {"system", "source_id", "consumers"} <= response.json().keys()
    assert {
        "name",
        "type",
        "dependency_level",
        "consumer_id",
        "source_id",
        "quality_bar",
        "satisfaction_rate",
        "last_issue",
    } <= response.json()["consumers"][0].keys()
    assert unknown.json()["system"] == "unknown"
    assert unknown.json()["consumers"] == []


def test_context_cross_graph_contract_and_unknown_default(client) -> None:
    response = client.get("/api/context/cross-graph-insight/billing_api")
    unknown = client.get("/api/context/cross-graph-insight/unknown")

    assert response.status_code == unknown.status_code == 200
    assert {
        "system",
        "insights",
        "connections",
        "impact_score",
        "alert_id",
        "process_signal",
        "erp_impact",
        "root_cause",
        "combined_impact",
        "sources_used",
    } <= response.json().keys()
    assert response.json()["insights"]
    assert unknown.json()["system"] == "unknown"
    assert unknown.json()["insights"] == []
