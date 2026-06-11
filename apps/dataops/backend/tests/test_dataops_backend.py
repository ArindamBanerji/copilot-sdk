from __future__ import annotations

import json
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
DATAOPS_SEED_PATH = Path(__file__).resolve().parents[4] / "copilot_sdk" / "scoring" / "presets" / "dataops_seed.json"


def _score(client: TestClient) -> dict:
    response = client.post(
        "/api/score",
        json={"category": "freshness_violation", "factors": DATAOPS_FACTORS},
    )
    assert response.status_code == 200
    return response.json()


def _learn(client: TestClient, decision_id: str, actual_action: str) -> dict:
    response = client.post(
        "/api/learn",
        json={
            "decision_id": decision_id,
            "actual_action": actual_action,
            "outcome": "confirmed",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["domain"] == "dataops"
    assert payload["graph_connected"] is False
    assert payload["graph_source"] == "fixture"
    assert "gae.evolution" in payload["engine"]


def test_api_health_returns_phase_alpha_and_engine(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["phase"] in {"A", "B"}
    assert isinstance(payload["alpha"], (int, float))
    assert "engine" in payload
    assert payload["engine"]


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


def test_auto_seed_empty_db(tmp_path: Path) -> None:
    from app.main import create_app

    db_path = tmp_path / "dataops_seeded.db"
    with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client:
        assert startup_client.get("/health").status_code == 200

    expected_verified, expected_correct = _fixture_outcome_counts(DATAOPS_SEED_PATH)
    assert _count_decisions(db_path, "dataops") == 20
    assert _count_verified(db_path, "dataops") == expected_verified
    assert _count_correct(db_path, "dataops") == expected_correct


def test_auto_seed_skips_populated(tmp_path: Path) -> None:
    from app.main import create_app
    from copilot_sdk.graph import SQLiteGraphStore

    db_path = tmp_path / "dataops_populated.db"
    store = SQLiteGraphStore(db_path, domain="dataops")
    try:
        _save_proxy_decision(store, "existing")
    finally:
        store.close()

    with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client:
        assert startup_client.get("/health").status_code == 200

    assert _count_decisions(db_path, "dataops") == 1


def test_ci_data_dir_creates_db(tmp_path: Path, monkeypatch) -> None:
    from app.main import create_app

    data_dir = tmp_path / "ci-data"
    monkeypatch.setenv("CI_DATA_DIR", str(data_dir))
    with TestClient(create_app(demo_bundle_path=False)) as startup_client:
        assert startup_client.get("/health").status_code == 200

    db_path = data_dir / "dataops.db"
    assert db_path.exists()
    assert _count_decisions(db_path, "dataops") == 20
    assert _count_verified(db_path, "dataops") == _fixture_outcome_counts(DATAOPS_SEED_PATH)[0]


def test_explicit_db_path_wins(tmp_path: Path, monkeypatch) -> None:
    from app.main import create_app

    ci_dir = tmp_path / "ci-data"
    explicit_db = tmp_path / "explicit.db"
    monkeypatch.setenv("CI_DATA_DIR", str(ci_dir))

    with TestClient(create_app(db_path=explicit_db, demo_bundle_path=False)) as startup_client:
        assert startup_client.get("/health").status_code == 200

    assert explicit_db.exists()
    assert not (ci_dir / "dataops.db").exists()
    assert _count_decisions(explicit_db, "dataops") == 20


def test_no_env_uses_explicit_fallback(tmp_path: Path, monkeypatch) -> None:
    from app.main import create_app

    monkeypatch.delenv("CI_DATA_DIR", raising=False)
    db_path = tmp_path / "fallback.db"
    with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client:
        assert startup_client.get("/health").status_code == 200

    assert db_path.exists()
    assert _count_decisions(db_path, "dataops") == 20


def test_startup_records_l5_source_status(tmp_path: Path) -> None:
    from app.main import create_app

    with TestClient(create_app(db_path=tmp_path / "l5-status.db", demo_bundle_path=False)) as client:
        assert client.get("/health").status_code == 200
        status = client.app.state.l5_startup_status
    assert status["dk_source"] in {"missing", "l5", "error", "deferred"}
    assert status["welford_source"] in {"missing", "l5", "error"}
    assert status["centroid_source"] in {"missing", "l5", "error", "deferred"}
    assert status["conservation_source"] in {"missing", "l5", "error"}


def test_l5_startup_restore_runs_after_seed_setup(tmp_path: Path, monkeypatch) -> None:
    from app import main as app_main

    calls: list[str] = []

    def fake_seed(_store):
        calls.append("seed")

    def fake_evolution_seed(_store):
        calls.append("evolution_seed")

    def fake_restore(*, domain, scorer, learning_store, welford_tracker=None):
        calls.append("restore")
        assert domain == "dataops"
        assert scorer is not None
        assert learning_store is not None
        assert welford_tracker is not None
        return {
            "dk_source": "missing",
            "welford_source": "missing",
            "centroid_source": "missing",
            "conservation_source": "missing",
            "welford_tracker": None,
        }

    monkeypatch.setattr(app_main, "_auto_seed_if_needed", fake_seed)
    monkeypatch.setattr(app_main, "_seed_demo_evolution_events_if_needed", fake_evolution_seed)
    monkeypatch.setattr(app_main, "restore_l5_runtime_state", fake_restore)

    with TestClient(app_main.create_app(db_path=tmp_path / "ordered.db", demo_bundle_path=False)) as client:
        assert client.get("/health").status_code == 200
        status = client.app.state.l5_startup_status

    assert calls == ["seed", "evolution_seed", "restore"]
    assert status["dk_source"] == "missing"


def test_alert_detail(client: TestClient) -> None:
    payload = client.get("/api/context/alert/ALERT-TIRE-001").json()

    assert payload["source"] == "fixture"
    assert payload["alert"]["alert_id"] == "ALERT-TIRE-001"
    assert payload["alert"]["system"] == "sap_mm"


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
    response = client.get("/api/context/alert/ALERT-TIRE-001")

    assert response.status_code == 200
    alert = response.json()["alert"]
    assert _parse_utc(alert["created_at"])
    assert alert["sla_minutes"] == 60


def test_alert_sla_by_severity(client: TestClient) -> None:
    payload = client.get("/api/context/alerts").json()
    critical = next((alert for alert in payload["alerts"] if alert.get("severity") == "critical"), None)
    low = next((alert for alert in payload["alerts"] if alert.get("severity") == "low"), None)

    if critical and low:
        assert critical["sla_minutes"] <= low["sla_minutes"]


def test_blast_radius(client: TestClient) -> None:
    payload = client.get("/api/context/alert/ALERT-TIRE-015/deps").json()

    assert payload["source"] == "fixture"
    assert payload["alert_id"] == "ALERT-TIRE-015"
    assert payload["tree"]["system"] == "logistics_dhl"
    assert payload["tree"]["children"]


def test_recurrence(client: TestClient) -> None:
    payload = client.get("/api/context/alert/ALERT-TIRE-001/recurrence").json()

    assert payload["source"] == "fixture"
    assert payload["alert_id"] == "ALERT-TIRE-001"
    assert payload["prior_count"] >= 1
    assert payload["recurrence_frequency"] > 0


def test_factor_auto_fill(client: TestClient) -> None:
    payload = client.get("/api/context/alert/ALERT-TIRE-001/factors").json()

    assert payload["source"] == "fixture"
    assert payload["all_auto_computed"] is True
    assert set(payload["factors"]) == set(DATAOPS_FACTORS)
    assert payload["factors"]["impact_scope"]["value"] >= 0


def test_audit_trail_for_known_alert(client: TestClient) -> None:
    response = client.get("/api/context/audit-trail/ALERT-TIRE-001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["alert_id"] == "ALERT-TIRE-001"
    assert len(payload["chain"]) >= 2
    assert payload["chain"][0]["step"] == "signal"
    assert any(step["step"] == "context" for step in payload["chain"])


def test_audit_trail_incomplete_for_untriaged(client: TestClient) -> None:
    response = client.get("/api/context/audit-trail/ALERT-TIRE-020")

    assert response.status_code == 200
    payload = response.json()
    assert payload["alert_id"] == "ALERT-TIRE-020"
    assert payload["complete"] is False
    assert not any(step["step"] == "outcome" for step in payload["chain"])


def test_audit_trail_unknown_alert_returns_empty(client: TestClient) -> None:
    response = client.get("/api/context/audit-trail/NONEXISTENT")

    assert response.status_code in {200, 404}
    if response.status_code == 200:
        payload = response.json()
        assert payload["chain"] == []
        assert payload["complete"] is False


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
        pipeline for pipeline in payload["pipelines"] if pipeline["name"] == "sap_mm"
    )

    assert "sap_mm" in names
    assert "erp_export" not in names
    assert "SAP" in sap_pipeline["display_name"]


def test_sap_downstream_references(client: TestClient) -> None:
    payload = client.get("/api/context/pipelines").json()
    pipeline_map = {pipeline["name"]: pipeline for pipeline in payload["pipelines"]}

    assert "sap_mm" in pipeline_map["sap_fi"]["upstream"]
    assert "sap_mm" in pipeline_map["warehouse_wms"]["upstream"]
    assert "erp_export" not in pipeline_map["sap_fi"]["upstream"]
    assert "erp_export" not in pipeline_map["warehouse_wms"]["upstream"]


def test_ae_recommendation_match(client: TestClient) -> None:
    payload = client.get("/api/ae/recommendation/ALERT-TIRE-018").json()

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


def test_ae_endpoints_return_evolution_store_source(client: TestClient) -> None:
    recommendation = client.get("/api/ae/recommendation/DQ-001").json()
    pattern_origin = client.get("/api/ae/pattern-origin").json()
    lifecycle = client.get("/api/ae/rule-lifecycle").json()
    operational_rules = client.get("/api/ae/operational-rules").json()

    assert recommendation["source"] == "evolution_store"
    assert pattern_origin["source"] == "evolution_store"
    assert lifecycle["source"] == "evolution_store"
    assert operational_rules["source"] == "evolution_store"


def test_ae_router_has_no_production_fixture_read_site() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    production_files = [
        repo_root / "apps" / "dataops" / "backend" / "app" / "ae_router.py",
        repo_root / "apps" / "dataops" / "backend" / "app" / "main.py",
        repo_root / "apps" / "dataops" / "backend" / "app" / "context_router.py",
        repo_root / "apps" / "purchasing" / "backend" / "app" / "main.py",
        repo_root / "apps" / "purchasing" / "backend" / "app" / "context_router.py",
    ]

    for path in production_files:
        source = path.read_text(encoding="utf-8")
        assert "evolution_fixtures" not in source, str(path)
        assert "load_fixtures" not in source, str(path)


def test_ae_fresh_store_returns_empty_responses(tmp_path: Path) -> None:
    from app.main import create_app

    client = TestClient(create_app(db_path=tmp_path / "fresh_dataops.db", demo_bundle_path=False))

    recommendation = client.get("/api/ae/recommendation/ALERT-TIRE-018").json()
    impact = client.get("/api/ae/impact").json()
    pattern_origin = client.get("/api/ae/pattern-origin").json()
    lifecycle = client.get("/api/ae/rule-lifecycle").json()
    operational_rules = client.get("/api/ae/operational-rules").json()

    assert recommendation["recommendations"] == []
    assert recommendation["count"] == 0
    assert impact["active_rules"] == []
    assert impact["rejected_rules"] == []
    assert pattern_origin["patterns"] == []
    assert pattern_origin["rejected"] == []
    assert lifecycle["rules"] == []
    assert lifecycle["total"] == 0
    assert operational_rules["rules"] == []
    assert operational_rules["total"] == 0


def test_dataops_audit_trail_uses_store_backed_recommendation(client: TestClient) -> None:
    payload = client.get("/api/context/audit-trail/ALERT-TIRE-018").json()

    ae_steps = [step for step in payload["chain"] if step.get("label") == "AE Recommendation"]
    assert ae_steps
    assert ae_steps[0]["variant_id"] == "dataops-recurring-impact-v1"
    assert ae_steps[0]["data"]["variant_id"] == "dataops-recurring-impact-v1"


def test_dataops_audit_trail_fresh_store_has_clean_empty_recommendation(tmp_path: Path) -> None:
    from app.main import create_app

    client = TestClient(create_app(db_path=tmp_path / "fresh_audit_dataops.db", demo_bundle_path=False))
    payload = client.get("/api/context/audit-trail/ALERT-TIRE-018").json()

    ae_steps = [step for step in payload["chain"] if step.get("label") == "AE Recommendation"]
    assert ae_steps
    assert ae_steps[0]["detail"] == "No AE recommendation"
    assert ae_steps[0]["data"] == {}


def test_ae_impact(client: TestClient) -> None:
    payload = client.get("/api/ae/impact").json()

    assert payload["auto_resolved_count"] > 0
    assert payload["accuracy"] > 0
    assert "V-DO-RECUR-001" in payload["active_rules"]
    assert payload["engine"]["gae"] == "gae.evolution"


def test_ae_pattern_origin(client: TestClient) -> None:
    payload = client.get("/api/ae/pattern-origin").json()

    assert payload["engine"]["gae"] == "gae.evolution"
    assert len(payload["chain"]) == 2
    assert [step["copilot"] for step in payload["chain"]] == ["dataops", "dataops"]
    assert payload["narrative"]
    assert len(payload["patterns"]) == 2
    assert payload["patterns"][0]["source_copilot"] == "dataops"
    assert all(pattern["source_copilot"] != "S2P" for pattern in payload["patterns"])
    assert payload["rejected"][0]["id"] == "V-DO-AUTO-001"


def test_pattern_origin_includes_genealogy(client: TestClient) -> None:
    payload = client.get("/api/ae/pattern-origin").json()

    assert "genealogy" in payload
    assert len(payload["genealogy"]["stages"]) >= 2
    assert all("win_rate" in stage for stage in payload["genealogy"]["stages"])
    assert payload["genealogy"]["stages"][0]["copilot"] == "dataops"
    assert payload["genealogy"]["stages"][-1]["copilot"] == "dataops"
    assert "improvement" in payload["genealogy"]


def test_pattern_origin_exposes_seeded_shadow_rule_source(tmp_path: Path) -> None:
    from app.main import create_app

    client = TestClient(create_app(db_path=tmp_path / "seeded_pattern_origin.db", demo_bundle_path=False))
    client.get("/api/health")

    payload = client.get("/api/ae/pattern-origin").json()

    assert payload["chain"]
    assert any(step["copilot"] == "S2P" for step in payload["chain"])
    assert payload["patterns"][0]["source_copilot"] == "S2P"


def test_rule_lifecycle_returns_all(client: TestClient) -> None:
    response = client.get("/api/ae/rule-lifecycle")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 4
    assert len(payload["rules"]) == 4
    assert payload["engine"]["gae"] == "gae.evolution"


def test_rule_lifecycle_has_events(client: TestClient) -> None:
    payload = client.get("/api/ae/rule-lifecycle?variant_id=dataops-recurring-impact-v1").json()

    assert payload["total"] == 1
    rule = payload["rules"][0]
    event_types = [event["type"] for event in rule["lifecycle_events"]]
    assert event_types[0] == "proposed"
    assert "shadow_result" in event_types
    assert "promoted" in event_types
    assert rule["win_rate"] == 0.75
    assert rule["decisions_evaluated"] == 24


def test_rule_lifecycle_rejected_has_reason(client: TestClient) -> None:
    payload = client.get("/api/ae/rule-lifecycle?status=rejected").json()

    assert payload["total"] == 1
    rule = payload["rules"][0]
    assert rule["status"] == "rejected"
    assert "downstream incidents" in rule["rejected_reason"]
    assert any(event["type"] == "rejected" and "downstream incidents" in event["detail"] for event in rule["lifecycle_events"])


def test_rule_lifecycle_summary_counts(client: TestClient) -> None:
    payload = client.get("/api/ae/rule-lifecycle").json()

    assert payload["summary"] == {
        "promoted": 2,
        "rejected": 1,
        "shadow": 1,
        "proposed": 0,
    }


def test_rule_lifecycle_filter_variant_id(client: TestClient) -> None:
    payload = client.get("/api/ae/rule-lifecycle?variant_id=dataops-freshness-sla-v1").json()

    assert payload["total"] == 1
    assert payload["rules"][0]["id"] == "V-DO-FRESH-001"
    assert payload["summary"]["promoted"] == 1


def test_ae_incident(client: TestClient) -> None:
    payload = client.get("/api/ae/incident").json()

    assert payload["estimated_cost"] == 0
    assert payload["affected_systems"] == []
    assert payload["fingerprint_insight"] == {}
    assert payload["engine"]["gae"] == "gae.evolution"


def test_ae_conservation_history(client: TestClient) -> None:
    payload = client.get("/api/ae/conservation-history").json()

    assert payload["engine"]["gae"] == "gae.calibration"
    assert payload["events"] == []


def test_process_signals_known_system(client: TestClient) -> None:
    payload = client.get("/api/context/process-signals/sap_mm").json()

    assert payload["source"] == "celonis_ems"
    assert "matkl_v2_new_combinations" in payload["signals"]
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
    payload = client.get("/api/context/process-signals/sap_fi").json()

    assert "invoice_exceptions_per_day" in payload["signals"]
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
        group for group in payload["groups"] if group["root_system"] == "supplier_portal"
    )

    assert sap_group["alert_count"] >= 1
    assert "Supplier" in sap_group["root_display"]


def test_alert_groups_no_orphans(client: TestClient) -> None:
    payload = client.get("/api/context/alert-groups").json()
    total_in_groups = sum(group["alert_count"] for group in payload["groups"])

    assert total_in_groups + len(payload["ungrouped"]) == payload["total_alerts"]


def test_system_history_with_seed(client: TestClient) -> None:
    response = client.get("/api/context/system/warehouse_etl/history")

    assert response.status_code == 200
    payload = response.json()
    assert payload["system"] == "warehouse_etl"
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


def test_decisions_returns_all(client: TestClient) -> None:
    response = client.get("/api/context/decisions")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 20
    assert len(payload["decisions"]) == 20
    assert payload["summary"]["total_decisions"] == payload["total"]
    assert all(decision["source"] in {"seed_history", "live_decision"} for decision in payload["decisions"])


def test_decisions_include_live_metadata(client: TestClient) -> None:
    client.post(
        "/api/context/alert-metadata",
        json={
            "decision_id": "DO-LIVE-001",
            "alert_id": "DQ-017",
            "system_name": "billing_api",
            "category": "freshness_violation",
            "action_taken": "escalate_to_owner",
            "outcome": "correct",
            "score_confidence": 0.91,
        },
    )

    payload = client.get("/api/context/decisions?system=billing_api&action=escalate_to_owner").json()

    assert any(decision["decision_id"] == "DO-LIVE-001" for decision in payload["decisions"])
    live = next(decision for decision in payload["decisions"] if decision["decision_id"] == "DO-LIVE-001")
    assert live["source"] == "live_decision"
    assert live["is_correct"] is True
    assert live["score_confidence"] == 0.91


def test_decisions_enrich_missing_category(client: TestClient) -> None:
    client.post(
        "/api/context/alert-metadata",
        json={
            "decision_id": "test-no-cat",
            "alert_id": "ALERT-TIRE-001",
            "system_name": "sap_mm",
            "action_taken": "investigate",
        },
    )

    payload = client.get("/api/context/decisions?system=sap_mm").json()
    decision = next(item for item in payload["decisions"] if item["decision_id"] == "test-no-cat")

    assert decision["category"] == "schema_change"
    assert decision["category"] is not None
    assert decision["category"] != "unknown"
    assert payload["summary"]["by_category"]["schema_change"]["count"] >= 1


def test_decisions_filter_by_system(client: TestClient) -> None:
    payload = client.get("/api/context/decisions?system=billing_api").json()

    assert payload["decisions"]
    assert payload["filters_applied"]["system"] == "billing_api"
    assert all(decision["system"] == "billing_api" for decision in payload["decisions"])


def test_decisions_filter_by_category(client: TestClient) -> None:
    payload = client.get("/api/context/decisions?category=pipeline_failure").json()

    assert payload["decisions"]
    assert payload["filters_applied"]["category"] == "pipeline_failure"
    assert all(decision["category"] == "pipeline_failure" for decision in payload["decisions"])


def test_decisions_filter_correct_only(client: TestClient) -> None:
    payload = client.get("/api/context/decisions?correct=true").json()

    assert payload["decisions"]
    assert payload["filters_applied"]["correct"] == "true"
    assert all(decision["is_correct"] is True for decision in payload["decisions"])


def test_decisions_empty_for_nonexistent(client: TestClient) -> None:
    payload = client.get("/api/context/decisions?system=nonexistent").json()

    assert payload["decisions"] == []
    assert payload["total"] == 0
    assert payload["summary"]["accuracy"] is None


def test_decisions_summary_has_breakdowns(client: TestClient) -> None:
    payload = client.get("/api/context/decisions").json()
    summary = payload["summary"]

    assert summary["by_action"]
    assert summary["by_category"]
    assert {"count", "correct", "win_rate"} <= set(summary["by_action"]["auto_approve"])
    assert {"count", "correct", "win_rate"} <= set(summary["by_category"]["pipeline_failure"])


def test_decisions_limit_applies_only_to_returned_rows(client: TestClient) -> None:
    payload = client.get("/api/context/decisions?limit=3").json()

    assert len(payload["decisions"]) == 3
    assert payload["total"] >= 20
    assert payload["summary"]["total_decisions"] == payload["total"]


def test_accuracy_by_category_returns_all(client: TestClient) -> None:
    response = client.get("/api/context/accuracy-by-category")

    assert response.status_code == 200
    payload = response.json()
    assert payload["categories"]
    assert payload["overall_accuracy"] is not None
    assert payload["total_decisions"] > 0
    assert "pipeline_failure" in payload["categories"]


def test_accuracy_by_category_has_trend(client: TestClient) -> None:
    payload = client.get("/api/context/accuracy-by-category").json()

    for category in payload["categories"].values():
        assert category["trend"] in {"declining", "improving", "stable"}
        assert "recent_accuracy" in category


def test_accuracy_by_category_alert_levels(client: TestClient) -> None:
    payload = client.get("/api/context/accuracy-by-category").json()

    for category in payload["categories"].values():
        assert category["alert_level"] in {"critical", "warning", "ok"}
        assert category["total"] > 0
        assert 0 <= category["correct"] <= category["total"]


def test_accuracy_declining_list(client: TestClient) -> None:
    payload = client.get("/api/context/accuracy-by-category").json()

    assert isinstance(payload["categories_declining"], list)
    assert isinstance(payload["categories_improving"], list)


def test_centroid_history_has_snapshots(client: TestClient) -> None:
    response = client.get("/api/context/centroid-history")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["snapshots"]) >= 2
    assert payload["total_decisions"] > 0


def test_centroid_history_initial_is_generic(client: TestClient) -> None:
    payload = client.get("/api/context/centroid-history").json()
    initial = payload["snapshots"][0]

    assert initial["decision_index"] == 0
    assert "Initial" in initial["label"]
    assert all(value == 0.5 for value in initial["centroids_sample"].values())


def test_centroid_history_top_shifts(client: TestClient) -> None:
    payload = client.get("/api/context/centroid-history").json()
    current = payload["snapshots"][-1]

    assert current["top_shifts"]
    for shift in current["top_shifts"]:
        assert {"factor", "from", "to", "delta"} <= set(shift)


def test_centroid_history_factor_names(client: TestClient) -> None:
    payload = client.get("/api/context/centroid-history").json()

    assert set(DATAOPS_FACTORS) <= set(payload["factor_names"])


def test_transformations_for_known_system(client: TestClient) -> None:
    response = client.get("/api/context/transformations/sap_mm")

    assert response.status_code == 200
    payload = response.json()
    assert payload["system"] == "sap_mm"
    assert len(payload["transformations"]) == 3
    assert payload["summary"]["total"] == 3
    assert payload["summary"]["bottleneck"]


def test_transformations_unknown_system(client: TestClient) -> None:
    response = client.get("/api/context/transformations/nonexistent_system")

    assert response.status_code == 200
    payload = response.json()
    assert payload["transformations"] == []
    assert payload["summary"] == {
        "total": 0,
        "total_duration_minutes": 0,
        "bottleneck": None,
        "bottleneck_pct": 0,
    }


def test_transformations_summary_has_bottleneck(client: TestClient) -> None:
    payload = client.get("/api/context/transformations/sap_mm").json()

    assert payload["summary"]["bottleneck"] == "Map Supplier Catalog"
    assert payload["summary"]["bottleneck_pct"] > 0.5


def test_bottleneck_for_known_system(client: TestClient) -> None:
    response = client.get("/api/context/bottleneck/sap_mm")

    assert response.status_code == 200
    payload = response.json()
    assert payload["bottleneck"]["name"] == "Map Supplier Catalog"
    assert payload["bottleneck"]["pct_of_total"] > 0.5
    assert payload["total_duration_minutes"] > 0


def test_bottleneck_has_recommendation(client: TestClient) -> None:
    payload = client.get("/api/context/bottleneck/sap_mm").json()

    assert payload["recommendation"]["action"] == "optimize_bottleneck"
    assert "Map Supplier Catalog" in payload["recommendation"]["detail"]
    assert payload["recommendation"]["estimated_savings_minutes"] > 0


def test_bottleneck_steps_ranked_by_duration(client: TestClient) -> None:
    payload = client.get("/api/context/bottleneck/sap_mm").json()
    durations = [step["duration_minutes"] for step in payload["all_steps_ranked"]]
    pct_values = [step["pct_of_total"] for step in payload["all_steps_ranked"]]

    assert durations == sorted(durations, reverse=True)
    assert payload["all_steps_ranked"][0]["id"] == "map_supplier_catalog"
    assert all(isinstance(value, (int, float)) for value in pct_values)
    assert any(value > 0 for value in pct_values)


def test_schema_impact_for_known_system(client: TestClient) -> None:
    response = client.get("/api/context/schema-impact/sap_mm")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_changes"]
    assert payload["total_changes"] == 1
    assert payload["total_impacts"] >= 1


def test_schema_impact_has_proposed_fix(client: TestClient) -> None:
    payload = client.get("/api/context/schema-impact/sap_mm").json()

    assert payload["schema_changes"][0]["proposed_fix"]
    assert payload["schema_changes"][0]["column"] == "MATKL_V2"
    assert payload["total_alerts_preventable"] == 11


def test_process_timeline_endpoint_returns_activities(client: TestClient) -> None:
    response = client.get("/api/context/process-timeline")

    assert response.status_code == 200
    payload = response.json()
    assert payload["bottleneck_id"] == "ACT-MATCH"
    assert payload["normal_duration"] == 252
    assert payload["current_duration"] == 2520
    assert payload["slowdown_multiplier"] == 10.0
    assert [activity["name"] for activity in payload["activities"]] == [
        "Create Purchase Requisition",
        "Approve Purchase Order",
        "Match Invoice to GR",
        "Process Payment",
    ]


def test_process_timeline_has_bottleneck_flag(client: TestClient) -> None:
    payload = client.get("/api/context/process-timeline").json()

    bottlenecks = [activity for activity in payload["activities"] if activity["is_bottleneck"]]
    assert len(bottlenecks) == 1
    assert bottlenecks[0]["id"] == "ACT-MATCH"
    assert bottlenecks[0]["slowdown_multiplier"] == 10.0


def test_process_timeline_activities_have_required_fields(client: TestClient) -> None:
    payload = client.get("/api/context/process-timeline").json()

    required = {"id", "name", "avg_duration", "automation_rate", "rework_rate"}
    assert payload["activities"]
    for activity in payload["activities"]:
        assert required <= set(activity)
        assert isinstance(activity["avg_duration"], (int, float))
        assert 0 <= activity["automation_rate"] <= 1
        assert 0 <= activity["rework_rate"] <= 1


def test_process_timeline_dollar_calibration_matches_story(client: TestClient) -> None:
    payload = client.get("/api/context/process-timeline").json()
    calibration = payload["dollar_calibration"]

    assert calibration["exception_cost_per_investigation"] == 47
    assert calibration["daily_invoice_volume"] == 8400
    assert calibration["current_exception_rate"] == 0.12
    assert calibration["target_exception_rate"] == 0.048
    assert calibration["annual_exception_cost"] == 17300000
    assert calibration["target_annual_exception_cost"] == 7100000
    assert calibration["bottleneck_cost_per_day"] == 8400
    assert calibration["option_a_savings_per_year"] == 547000
    assert calibration["total_trajectory_per_year"] == 1620000


def test_cross_graph_insight_returns_triple_correlation(client: TestClient) -> None:
    response = client.get("/api/context/cross-graph-insight/ALERT-TIRE-001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["alert_id"] == "ALERT-TIRE-001"
    assert payload["process_signal"]
    assert payload["erp_impact"]
    assert payload["root_cause"]
    assert payload["sources_used"] == ["celonis", "sap", "graph"]


def test_cross_graph_insight_has_combined_impact(client: TestClient) -> None:
    payload = client.get("/api/context/cross-graph-insight/ALERT-TIRE-001").json()

    assert payload["process_signal"]["slowdown_factor"] == 10.0
    assert payload["erp_impact"]["daily_cost"] == 8400
    assert payload["combined_impact"]["daily_cost"] == 8400
    assert payload["combined_impact"]["monthly_cost"] == 252000
    assert payload["combined_impact"]["annualized_cost"] == 3066000
    assert payload["combined_impact"]["confidence"] == 0.89


def test_cross_graph_insight_unknown_alert_returns_404(client: TestClient) -> None:
    response = client.get("/api/context/cross-graph-insight/ALERT-DOES-NOT-EXIST")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_cross_graph_insight_alert_without_refs_returns_404(client: TestClient) -> None:
    response = client.get("/api/context/cross-graph-insight/ALERT-TIRE-002")

    assert response.status_code == 404
    assert response.json()["detail"] == "No cross-graph data for this alert"


def test_cross_graph_insight_values_come_from_fixture(client: TestClient) -> None:
    payload = client.get("/api/context/cross-graph-insight/ALERT-TIRE-001").json()

    assert payload["process_signal"]["activity"] == "Match Invoice to GR"
    assert payload["process_signal"]["current_duration"] == 2520
    assert payload["process_signal"]["normal_duration"] == 252
    assert payload["erp_impact"]["affected_pos"] == 340
    assert payload["erp_impact"]["affected_plants"] == 5
    assert payload["erp_impact"]["backlog_value"] == 2100000
    assert payload["root_cause"]["field"] == "MATKL_V2"
    assert payload["root_cause"]["new_combinations"] == 340000
    assert payload["root_cause"]["upstream_supplier"] == "Aster Rubber"


def _valid_apply_fix_request() -> dict:
    return {
        "alert_id": "ALERT-TIRE-001",
        "option": "A",
        "option_label": "Pre-join filter on MATKL_V2 range",
        "entity_type": "PurchaseOrder",
        "entity_id": "PO-4500001234",
        "payload": {"matching_parameter": "MATKL_V2_FILTER"},
    }


def test_apply_fix_returns_success(client: TestClient) -> None:
    response = client.post("/api/context/apply-fix", json=_valid_apply_fix_request())

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "applied"
    assert payload["alert_id"] == "ALERT-TIRE-001"
    assert payload["option"] == "A"
    assert payload["option_label"] == "Pre-join filter on MATKL_V2 range"
    assert payload["estimated_savings"] == "$547K/year"
    assert payload["timestamp"] == "2026-05-19T10:00:00Z"


def test_apply_fix_includes_conservation_check(client: TestClient) -> None:
    payload = client.post("/api/context/apply-fix", json=_valid_apply_fix_request()).json()
    conservation = payload["conservation_check"]

    assert conservation["status"] == "GREEN"
    assert conservation["current_automation"] == 0.35
    assert conservation["projected_automation"] == 0.38
    assert conservation["theta_min"] == 0.67
    assert conservation["safe"] is True


def test_context_router_uses_canonical_theta_min() -> None:
    from apps.dataops.backend.app import context_router

    source = Path(context_router.__file__).read_text(encoding="utf-8")

    assert "from copilot_sdk.scoring.scorer import compute_theta_min" in source
    assert "compute_theta_min(APPLY_FIX_OVERRIDE_RATE, APPLY_FIX_VERIFIED_COUNT)" in source
    assert "23.53" not in source


def test_apply_fix_includes_sap_response(client: TestClient) -> None:
    payload = client.post("/api/context/apply-fix", json=_valid_apply_fix_request()).json()

    sap_response = payload["sap_response"]["d"]
    assert sap_response["PurchaseOrder"] == "PO-4500001234"
    assert sap_response["Status"] == "updated"
    assert sap_response["MatchingParameter"] == "MATKL_V2_FILTER"
    assert sap_response["LastChangedDateTime"] == "2026-05-19T10:00:00Z"


def test_apply_fix_rejects_invalid_entity_type(client: TestClient) -> None:
    request = _valid_apply_fix_request()
    request["entity_type"] = "BusinessPartner"

    response = client.post("/api/context/apply-fix", json=request)

    assert response.status_code == 400
    assert "PurchaseOrder" in response.json()["detail"]


def test_apply_fix_rejects_empty_payload(client: TestClient) -> None:
    request = _valid_apply_fix_request()
    request["payload"] = {}

    response = client.post("/api/context/apply-fix", json=request)

    assert response.status_code == 400
    assert "non-empty" in response.json()["detail"]


def test_apply_fix_rejects_unknown_payload_field(client: TestClient) -> None:
    request = _valid_apply_fix_request()
    request["payload"] = {"matching_parameter": "MATKL_V2_FILTER", "unsafe_field": "x"}

    response = client.post("/api/context/apply-fix", json=request)

    assert response.status_code == 400
    assert "unsafe_field" in response.json()["detail"]


def test_apply_fix_unknown_alert_returns_404(client: TestClient) -> None:
    request = _valid_apply_fix_request()
    request["alert_id"] = "ALERT-DOES-NOT-EXIST"

    response = client.post("/api/context/apply-fix", json=request)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_operational_rules_returns_all(client: TestClient) -> None:
    response = client.get("/api/ae/operational-rules")

    assert response.status_code == 200
    payload = response.json()
    assert payload["rules"]
    assert payload["total"] == len(payload["rules"])
    assert payload["summary"]
    assert payload["engine"]["gae"] == "gae.evolution"
    scheduling = [rule for rule in payload["rules"] if rule["id"] == "V-DO-SCHED-001"]
    assert scheduling
    assert scheduling[0]["type"] == "scheduling_rule"
    assert "off-peak" in scheduling[0]["recommendation"]
    assert "quality" in scheduling[0]["recommendation"]


def test_operational_rules_summary_counts(client: TestClient) -> None:
    payload = client.get("/api/ae/operational-rules").json()

    assert sum(payload["summary"].values()) == len(payload["rules"])
    assert payload["summary"]["promoted"] == 2
    assert payload["summary"]["rejected"] == 1
    assert payload["summary"]["shadow"] == 1


def test_score_via_sdk(client: TestClient) -> None:
    payload = _score(client)
    assert payload["action"] in {
        "auto_approve",
        "investigate",
        "escalate_to_owner",
        "pause_downstream",
        "refer_to_specialist",
    }
    assert payload["decision_id"].startswith("DOPS-")
    assert payload["engine"]["scoring"] == "copilot_sdk.scoring.CompoundingScorer"


def test_learn_returns_reward(client: TestClient) -> None:
    score = _score(client)
    payload = _learn(client, score["decision_id"], score["action"])
    assert payload["decision_id"] == score["decision_id"]
    assert payload["reward"] > 0
    assert payload["engine"]["gae"] == "gae.profile_scorer.ProfileScorer"


def test_conservation_status_returns_live_counts(client: TestClient) -> None:
    before = client.get("/api/conservation/status").json()
    assert before["total_decisions"] == 0
    assert before["verified_count"] == 0
    assert before["correct_count"] == 0

    score = _score(client)
    after_score = client.get("/api/conservation/status").json()
    # Conservation V is verified-only; pending score writes do not increase total_decisions.
    assert after_score["total_decisions"] == 0
    assert after_score["verified_count"] == 0
    assert after_score["correct_count"] == 0

    _learn(client, score["decision_id"], score["action"])
    payload = client.get("/api/conservation/status").json()

    assert payload["domain"] == "dataops"
    assert payload["total_decisions"] == 1
    assert payload["verified_count"] == 1
    assert payload["correct_count"] == 1
    assert payload["penalty_ratio"] == 10.0
    assert payload["engine"]["gae"] == "gae.calibration"


def test_in_memory_scoring_and_conservation_share_proxy_store(dataops_data_dir: Path) -> None:
    from app.main import create_app

    with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as memory_client:
        score = _score(memory_client)
        payload = memory_client.get("/api/conservation/status").json()
        learn = _learn(memory_client, score["decision_id"], score["action"])
        after_learn = memory_client.get("/api/conservation/status").json()

    assert score["decision_id"].startswith("DOPS-")
    assert payload["domain"] == "dataops"
    assert learn["decision_id"] == score["decision_id"]
    assert payload["total_decisions"] == 0
    assert payload["verified_count"] == 0
    assert after_learn["total_decisions"] == 1
    assert after_learn["verified_count"] == 1


def test_conservation_what_if(client: TestClient) -> None:
    response = client.post("/api/conservation/what-if", json={"alpha": 0.7, "q": 0.2, "V": 100})

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "dataops"
    assert "passed" in payload
    assert payload["engine"]["component"] == "check_conservation"


def test_evolution_variants(client: TestClient) -> None:
    response = client.get("/api/evolution/variants")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "dataops"
    assert "variants" in payload
    assert isinstance(payload["variants"], list)
    assert {variant["id"] for variant in payload["variants"]} >= {
        "AUTO_APPROVE_THRESHOLD_v1",
        "AUTO_APPROVE_THRESHOLD_v2",
        "SCHEDULING_CRITERIA_v1",
        "SCHEDULING_CRITERIA_v2",
        "V-DO-RECUR-001",
        "V-DO-FRESH-001",
        "V-DO-AUTO-001",
    }
    persisted = next(variant for variant in payload["variants"] if variant["id"] == "V-DO-RECUR-001")
    assert {"id", "variant_id", "event_type", "description"}.issubset(persisted)
    assert all(variant.get("triggered_by") != "fixture" for variant in payload["variants"])
    assert payload["active_rules"] == []
    assert payload["promoted_rules"] == []
    assert payload["total_active"] == 0
    assert payload["total_promoted"] == 0


def test_evolution_variants_fresh_store_is_empty(tmp_path: Path) -> None:
    from app.main import create_app

    client = TestClient(create_app(db_path=tmp_path / "fresh_variants_dataops.db", demo_bundle_path=False))
    payload = client.get("/api/evolution/variants").json()

    assert payload["domain"] == "dataops"
    assert {variant["id"] for variant in payload["variants"]} == {
        "AUTO_APPROVE_THRESHOLD_v1",
        "AUTO_APPROVE_THRESHOLD_v2",
        "SCHEDULING_CRITERIA_v1",
        "SCHEDULING_CRITERIA_v2",
    }


def test_evolution_history(client: TestClient) -> None:
    response = client.get("/api/evolution/history")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "dataops"
    assert payload["events"] == []
    assert payload["count"] == 0


def test_evolution_promoted(client: TestClient) -> None:
    response = client.get("/api/evolution/promoted")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "dataops"
    assert payload["promoted"] == []


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


def _save_proxy_decision(store, decision_id: str) -> None:
    store.write_decision(
        "dataops",
        category="freshness_violation",
        action="auto_approve",
        confidence=0.8,
        factors=DATAOPS_FACTORS,
        metadata={
            "decision_id": decision_id,
            "category_index": 0,
            "factor_vector": list(DATAOPS_FACTORS.values()),
            "recommended_index": 0,
            "probabilities": [0.8, 0.05, 0.05, 0.05, 0.05],
        },
    )


def _count_decisions(db_path: Path, domain: str) -> int:
    from copilot_sdk.graph import SQLiteGraphStore

    store = SQLiteGraphStore(db_path, domain=domain)
    try:
        return store.count_decisions(domain)
    finally:
        store.close()


def _count_verified(db_path: Path, domain: str) -> int:
    from copilot_sdk.graph import SQLiteGraphStore

    store = SQLiteGraphStore(db_path, domain=domain)
    try:
        return store.count_verified(domain)
    finally:
        store.close()


def _count_correct(db_path: Path, domain: str) -> int:
    from copilot_sdk.graph import SQLiteGraphStore

    store = SQLiteGraphStore(db_path, domain=domain)
    try:
        return store.count_correct(domain)
    finally:
        store.close()


def _fixture_outcome_counts(path: Path) -> tuple[int, int]:
    seed = json.loads(path.read_text(encoding="utf-8"))
    verified = sum(1 for entry in seed if "is_correct" in entry)
    correct = sum(1 for entry in seed if bool(entry.get("is_correct")))
    return verified, correct
