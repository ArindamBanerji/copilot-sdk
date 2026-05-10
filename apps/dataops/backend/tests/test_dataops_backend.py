from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient


DATAOPS_FACTORS = {
    "impact_scope": 0.76,
    "source_reliability": 0.58,
    "recurrence_frequency": 0.27,
    "downstream_urgency": 0.84,
    "data_freshness": 0.21,
    "business_criticality": 0.9,
}


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["domain"] == "dataops"
    assert payload["graph_connected"] is False
    assert payload["graph_source"] == "fixture"
    assert "gae.evolution" in payload["engine"]


def test_pipelines(client: TestClient) -> None:
    payload = client.get("/api/context/pipelines").json()

    assert payload["source"] == "fixture"
    assert len(payload["pipelines"]) == 9
    assert payload["pipelines"][0]["name"]
    assert "downstream_count" in payload["pipelines"][0]


def test_alerts(client: TestClient) -> None:
    payload = client.get("/api/context/alerts").json()

    assert payload["source"] == "fixture"
    assert len(payload["alerts"]) == 20
    assert {"alert_id", "system", "category", "factors"} <= set(payload["alerts"][0])


def test_alert_detail(client: TestClient) -> None:
    payload = client.get("/api/context/alert/DQ-001").json()

    assert payload["source"] == "fixture"
    assert payload["alert"]["alert_id"] == "DQ-001"
    assert payload["alert"]["system"] == "warehouse_etl"


def test_alerts_have_timestamps(client: TestClient) -> None:
    response = client.get("/api/context/alerts")

    assert response.status_code == 200
    payload = response.json()
    for alert in payload["alerts"]:
        assert alert["created_at"]
        assert _parse_utc(alert["created_at"])
        assert isinstance(alert["sla_minutes"], int)
        assert alert["sla_minutes"] > 0


def test_alert_detail_has_runtime_sla_fields(client: TestClient) -> None:
    response = client.get("/api/context/alert/DQ-001")

    assert response.status_code == 200
    alert = response.json()["alert"]
    assert _parse_utc(alert["created_at"])
    assert alert["sla_minutes"] == 30


def test_alert_sla_by_severity(client: TestClient) -> None:
    payload = client.get("/api/context/alerts").json()
    critical = next((alert for alert in payload["alerts"] if alert.get("severity") == "critical"), None)
    low = next((alert for alert in payload["alerts"] if alert.get("severity") == "low"), None)

    if critical and low:
        assert critical["sla_minutes"] <= low["sla_minutes"]


def test_blast_radius(client: TestClient) -> None:
    payload = client.get("/api/context/alert/DQ-015/deps").json()

    assert payload["source"] == "fixture"
    assert payload["alert_id"] == "DQ-015"
    assert payload["tree"]["system"] == "crm_sync"
    assert payload["tree"]["children"]


def test_recurrence(client: TestClient) -> None:
    payload = client.get("/api/context/alert/DQ-001/recurrence").json()

    assert payload["source"] == "fixture"
    assert payload["alert_id"] == "DQ-001"
    assert payload["prior_count"] >= 7
    assert payload["recurrence_frequency"] > 0.5


def test_factor_auto_fill(client: TestClient) -> None:
    payload = client.get("/api/context/alert/DQ-001/factors").json()

    assert payload["source"] == "fixture"
    assert payload["all_auto_computed"] is True
    assert set(payload["factors"]) == set(DATAOPS_FACTORS)
    assert payload["factors"]["impact_scope"]["value"] >= 0


def test_similar_alerts(client: TestClient) -> None:
    response = client.get(
        "/api/context/similar",
        params={
            "category": "pipeline_failure",
            "impact_scope": 0.67,
            "source_reliability": 0.92,
            "recurrence_frequency": 0.0,
            "downstream_urgency": 0.95,
            "data_freshness": 0.9,
            "business_criticality": 0.9,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["similar"]
    assert payload["count"] >= len(payload["similar"])
    assert all(item["similarity"] > 0.85 for item in payload["similar"])
    assert all(item["category"] == "pipeline_failure" for item in payload["similar"])
    assert all(item["event_id"] for item in payload["similar"])


def test_similar_alerts_empty_category(client: TestClient) -> None:
    response = client.get(
        "/api/context/similar",
        params={
            "category": "nonexistent",
            "impact_scope": 0.67,
            "source_reliability": 0.92,
            "recurrence_frequency": 0.0,
            "downstream_urgency": 0.95,
            "data_freshness": 0.9,
            "business_criticality": 0.9,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["similar"] == []
    assert payload["count"] == 0


def test_sap_naming_in_pipelines(client: TestClient) -> None:
    payload = client.get("/api/context/pipelines").json()
    names = {pipeline["name"] for pipeline in payload["pipelines"]}
    sap_pipeline = next(
        pipeline for pipeline in payload["pipelines"] if pipeline["name"] == "sap_s4hana_extract"
    )

    assert "sap_s4hana_extract" in names
    assert "erp_export" not in names
    assert "SAP" in sap_pipeline["display_name"]


def test_sap_downstream_references(client: TestClient) -> None:
    payload = client.get("/api/context/pipelines").json()
    pipeline_map = {pipeline["name"]: pipeline for pipeline in payload["pipelines"]}

    assert "sap_s4hana_extract" in pipeline_map["billing_api"]["upstream"]
    assert "erp_export" not in pipeline_map["billing_api"]["upstream"]
    assert "sap_s4hana_extract" in pipeline_map["warehouse_etl"]["upstream"]
    assert "erp_export" not in pipeline_map["warehouse_etl"]["upstream"]


def test_ae_recommendation_match(client: TestClient) -> None:
    payload = client.get("/api/ae/recommendation/DQ-001").json()

    assert payload["has_recommendation"] is True
    assert payload["count"] >= 1
    assert payload["recommendations"][0]["id"] == "V-DO-RECUR-001"
    assert payload["recommendations"][0]["match_reason"]
    assert payload["engine"]["gae"] == "gae.evolution"


def test_ae_recommendation_no_match(client: TestClient) -> None:
    payload = client.get("/api/ae/recommendation/DQ-005").json()

    assert payload["has_recommendation"] is False
    assert payload["recommendations"] == []
    assert payload["count"] == 0


def test_ae_impact(client: TestClient) -> None:
    payload = client.get("/api/ae/impact").json()

    assert payload["auto_resolved_count"] > 0
    assert payload["accuracy"] > 0
    assert "V-DO-RECUR-001" in payload["active_rules"]
    assert payload["engine"]["gae"] == "gae.evolution"


def test_ae_pattern_origin(client: TestClient) -> None:
    payload = client.get("/api/ae/pattern-origin").json()

    assert payload["engine"]["gae"] == "gae.evolution"
    assert len(payload["chain"]) == 3
    assert [step["copilot"] for step in payload["chain"]] == ["soc", "s2p", "dataops"]
    assert payload["chain"][2]["warm_start_prior"] == 0.757
    assert payload["narrative"]
    assert len(payload["patterns"]) == 2
    assert payload["patterns"][0]["source_copilot"] == "dataops"
    assert payload["rejected"][0]["id"] == "V-DO-AUTO-001"


def test_ae_incident(client: TestClient) -> None:
    payload = client.get("/api/ae/incident").json()

    assert payload["estimated_cost"] == 50000
    assert "source_reliability" in payload["fingerprint_insight"]
    assert "recurrence_frequency" in payload["fingerprint_insight"]
    assert payload["engine"]["gae"] == "gae.evolution"


def test_ae_conservation_history(client: TestClient) -> None:
    payload = client.get("/api/ae/conservation-history").json()

    assert payload["engine"]["gae"] == "gae.calibration"
    assert [event["status"] for event in payload["events"]] == ["denied", "denied", "approved"]


def test_process_signals_known_system(client: TestClient) -> None:
    payload = client.get("/api/context/process-signals/sap_s4hana_extract").json()

    assert payload["source"] == "celonis_ems"
    assert "o2c_cycle_time_days" in payload["signals"]
    assert payload["metrics"]
    assert "confidence" in payload["correlation"]
    assert payload["engine"] == "celonis_ems.process_mining"


def test_process_signals_unknown_system(client: TestClient) -> None:
    payload = client.get("/api/context/process-signals/nonexistent_system").json()

    assert payload["source"] == "celonis_ems"
    assert payload["signals"] == {}
    assert payload["metrics"] == []
    assert payload["correlation"] == {}
    assert "celonis_ems" in payload["engine"]


def test_process_signals_billing(client: TestClient) -> None:
    payload = client.get("/api/context/process-signals/billing_api").json()

    assert "invoice_processing_time_hours" in payload["signals"]
    assert payload["metrics"]
    assert payload["source"] == "celonis_ems"


def test_alert_groups_returns_groups(client: TestClient) -> None:
    response = client.get("/api/context/alert-groups")

    assert response.status_code == 200
    payload = response.json()
    assert {"groups", "ungrouped", "total_alerts", "total_groups"} <= set(payload)
    assert payload["total_alerts"] == 20
    assert payload["total_groups"] == len(payload["groups"])
    assert payload["groups"]
    for group in payload["groups"]:
        assert {"root_system", "root_display", "alerts", "cascading_systems", "alert_count"} <= set(group)


def test_alert_groups_include_runtime_sla_fields(client: TestClient) -> None:
    response = client.get("/api/context/alert-groups")

    assert response.status_code == 200
    payload = response.json()
    nested_alerts = [alert for group in payload["groups"] for alert in group["alerts"]]
    assert nested_alerts
    assert any("created_at" in alert and "sla_minutes" in alert for alert in nested_alerts)
    for alert in nested_alerts:
        assert _parse_utc(alert["created_at"])
        assert alert["sla_minutes"] > 0


def test_alert_groups_sap_cluster(client: TestClient) -> None:
    payload = client.get("/api/context/alert-groups").json()
    sap_group = next(
        group for group in payload["groups"] if group["root_system"] == "sap_s4hana_extract"
    )

    assert sap_group["alert_count"] >= 1
    assert "SAP" in sap_group["root_display"]


def test_alert_groups_no_orphans(client: TestClient) -> None:
    payload = client.get("/api/context/alert-groups").json()
    total_in_groups = sum(group["alert_count"] for group in payload["groups"])

    assert total_in_groups + len(payload["ungrouped"]) == payload["total_alerts"]


def test_system_history_with_seed(client: TestClient) -> None:
    response = client.get("/api/context/system/billing_api/history")

    assert response.status_code == 200
    payload = response.json()
    assert payload["system"] == "billing_api"
    assert payload["resolutions"]
    assert payload["action_breakdown"]
    assert "accuracy" in payload
    assert payload["total"] > 0


def test_system_history_unknown_system(client: TestClient) -> None:
    payload = client.get("/api/context/system/nonexistent/history").json()

    assert payload["resolutions"] == []
    assert payload["total"] == 0
    assert payload["accuracy"] is None
    assert payload["action_breakdown"] == {}
    assert payload["best_action"] is None
    assert payload["worst_action"] is None


def test_system_history_action_breakdown(client: TestClient) -> None:
    payload = client.get("/api/context/system/warehouse_etl/history").json()

    assert payload["action_breakdown"]
    for action in payload["action_breakdown"].values():
        assert {"count", "correct", "win_rate"} <= set(action)


def test_system_history_limit(client: TestClient) -> None:
    full_payload = client.get("/api/context/system/billing_api/history").json()
    limited_payload = client.get("/api/context/system/billing_api/history?limit=2").json()

    assert len(limited_payload["resolutions"]) <= 2
    assert limited_payload["total"] == full_payload["total"]


def test_score_via_sdk(client: TestClient) -> None:
    response = client.post(
        "/api/score",
        json={"category": "freshness_violation", "factors": DATAOPS_FACTORS},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] in {
        "auto_approve",
        "investigate",
        "escalate_to_owner",
        "pause_downstream",
        "refer_to_specialist",
    }
    assert payload["decision_id"]
    assert payload["engine"]["scoring"] == "copilot_sdk.scoring.CompoundingScorer"


def test_learn_returns_reward(client: TestClient) -> None:
    score = client.post(
        "/api/score",
        json={"category": "freshness_violation", "factors": DATAOPS_FACTORS},
    ).json()

    response = client.post(
        "/api/learn",
        json={
            "decision_id": score["decision_id"],
            "actual_action": score["action"],
            "outcome": "confirmed",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision_id"] == score["decision_id"]
    assert payload["reward"] > 0
    assert payload["engine"]["gae"] == "gae.profile_scorer.ProfileScorer"


def test_conservation_status(client: TestClient) -> None:
    payload = client.get("/api/conservation/status").json()

    assert payload["domain"] == "dataops"
    assert payload["total_decisions"] == 20
    assert payload["verified_count"] == 20
    assert payload["correct_count"] > 0
    assert payload["penalty_ratio"] == 10.0
    assert payload["engine"]["gae"] == "gae.calibration"


def test_conservation_what_if(client: TestClient) -> None:
    response = client.post("/api/conservation/what-if", json={"alpha": 0.7, "q": 0.2, "V": 100})

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "dataops"
    assert "passed" in payload
    assert payload["engine"]["component"] == "check_conservation"


def test_evolution_variants(client: TestClient) -> None:
    payload = client.get("/api/evolution/variants").json()

    assert payload["domain"] == "dataops"
    assert payload["engine"]["gae"] == "gae.evolution"
    assert len(payload["variants"]) == 3
    assert payload["variants"][0]["id"] == "V-DO-RECUR-001"


def test_alert_metadata_store(client: TestClient, dataops_data_dir: Path) -> None:
    response = client.post(
        "/api/context/alert-metadata",
        json={
            "decision_id": "DO-META-001",
            "alert_id": "DQ-017",
            "owner": "billing",
            "factors": DATAOPS_FACTORS,
        },
    )

    assert response.status_code == 201
    payload = client.get("/api/context/alert-metadata").json()
    assert payload["metadata"]["DO-META-001"]["owner"] == "billing"
    assert (dataops_data_dir / "alert_metadata.json").read_text(encoding="utf-8")


def test_alert_metadata_requires_decision_id(client: TestClient) -> None:
    response = client.post("/api/context/alert-metadata", json={"alert_id": "DQ-017"})

    assert response.status_code == 400
    assert "decision_id" in response.json()["detail"]


def test_fingerprint(client: TestClient) -> None:
    for _ in range(3):
        score = client.post(
            "/api/score",
            json={"category": "freshness_violation", "factors": DATAOPS_FACTORS},
        ).json()
        client.post(
            "/api/learn",
            json={
                "decision_id": score["decision_id"],
                "actual_action": score["action"],
                "outcome": "confirmed",
            },
        )

    response = client.get("/api/fingerprint")

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"]["gae"] == "gae.profile_scorer.ProfileScorer"
    assert payload


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
