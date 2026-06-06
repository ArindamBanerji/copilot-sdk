from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from copilot_sdk.graph import SQLiteGraphStore


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
WORKSPACE_ROOT = REPO_ROOT.parent
CI_PLATFORM_ROOT = WORKSPACE_ROOT / "ci-platform"

for path in (BACKEND_ROOT, REPO_ROOT, CI_PLATFORM_ROOT):
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))


@pytest.fixture()
def dataops_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv("GRAPH_DSN", raising=False)

    source = BACKEND_ROOT / "data"
    target = tmp_path / "data"
    target.mkdir()
    fallback = target / "fallback"
    fallback.mkdir()

    for name in (
        "evolution_fixtures.json",
        "ae_impact.json",
        "incident.json",
        "conservation_history.json",
        "process_signals.json",
        "transformations.json",
        "schema_changes.json",
        "sap_purchase_orders.json",
        "sap_supplier_invoices.json",
        "sap_suppliers.json",
        "celonis_knowledge_models.json",
        "celonis_kpis.json",
        "celonis_process_data.json",
        "process_timeline.json",
        "transfer_status.json",
    ):
        shutil.copyfile(source / name, target / name)

    for name in ("pipelines.json", "alerts.json", "blast_radius.json"):
        shutil.copyfile(source / "fallback" / name, fallback / name)

    (target / "alert_metadata.json").write_text("{}\n", encoding="utf-8")

    from app import ae_router, context_router, main

    ae_router.reset_ae_fixtures()
    monkeypatch.setattr(context_router, "DATA_DIR", target)
    monkeypatch.setattr(context_router, "METADATA_PATH", target / "alert_metadata.json")
    monkeypatch.setattr(ae_router, "DATA_DIR", target)
    monkeypatch.setattr(main, "DATA_DIR", target)
    monkeypatch.setattr(main, "DEFAULT_DB_PATH", target / "dataops.db")
    ae_router.reset_ae_fixtures()
    try:
        store = SQLiteGraphStore(str(target / "test_dataops.db"), domain="dataops", decision_id_prefix="DOPS-")
        _seed_ae_events(store)
        yield target
    finally:
        ae_router.reset_ae_fixtures()


@pytest.fixture()
def client(dataops_data_dir: Path) -> TestClient:
    from app.main import create_app

    app = create_app(db_path=dataops_data_dir / "test_dataops.db", demo_bundle_path=False)
    return TestClient(app)


def _seed_ae_events(store: SQLiteGraphStore) -> None:
    store.save_evolution_event(
        domain="dataops",
        event_type="promotion_approved",
        rule_name="recurrence_frequency_signal",
        variant_id="dataops-recurring-impact-v1",
        metadata={
            "id": "V-DO-RECUR-001",
            "artifact_type": "routing_rule",
            "description": "Escalate recurring DataOps alerts with downstream impact.",
            "impact": "recurrence_reduction",
            "magnitude": 0.24,
            "timestamp": "2026-05-08T10:30:00Z",
            "wins": 18,
            "total": 24,
            "estimated_hours_saved": 42.5,
            "source_copilot": "dataops",
            "source_rule": "recurrence_frequency_signal",
            "match": {
                "min_recurrence_count": 7,
                "min_impact_scope": 0.25,
                "categories": ["pipeline_failure", "quality_anomaly", "transform_drift"],
            },
        },
    )
    store.save_evolution_event(
        domain="dataops",
        event_type="promotion_approved",
        rule_name="freshness_violation_signal",
        variant_id="dataops-freshness-sla-v1",
        metadata={
            "id": "V-DO-FRESH-001",
            "artifact_type": "context_policy",
            "description": "Pause downstream consumers when freshness breaches affect urgent systems.",
            "impact": "sla_protection",
            "magnitude": 0.19,
            "timestamp": "2026-05-08T10:45:00Z",
            "wins": 14,
            "total": 19,
            "estimated_hours_saved": 27.0,
            "source_copilot": "dataops",
            "source_rule": "freshness_violation_signal",
            "match": {
                "categories": ["freshness_violation"],
                "max_data_freshness": 0.35,
                "min_downstream_urgency": 0.7,
            },
        },
    )
    store.save_evolution_event(
        domain="dataops",
        event_type="promotion_rejected",
        rule_name="high_impact_auto_rule",
        variant_id="dataops-high-impact-auto-v1",
        metadata={
            "id": "V-DO-AUTO-001",
            "artifact_type": "scoring_threshold",
            "description": "Reject auto-approval for high-impact, low-reliability alerts.",
            "impact": "risk_control",
            "magnitude": 0.11,
            "timestamp": "2026-05-08T11:00:00Z",
            "wins": 6,
            "total": 18,
            "reject_reason": "High-impact auto-approvals increased downstream incidents",
            "match": {
                "action": "auto_approve",
                "min_impact_scope": 0.7,
                "max_source_reliability": 0.5,
            },
        },
    )
    store.save_evolution_event(
        domain="dataops",
        event_type="shadow_started",
        rule_name="resource_quality_scheduling_signal",
        variant_id="dataops-off-peak-scheduling-v1",
        metadata={
            "id": "V-DO-SCHED-001",
            "artifact_type": "scheduling_rule",
            "description": "Schedule resource-intensive quality checks during off-peak windows.",
            "impact": "quality_scheduling",
            "magnitude": 0.17,
            "timestamp": "2026-05-08T11:15:00Z",
            "system": "celonis_transform",
            "trigger": "resource contention during quality validation",
            "recommendation": "Move data quality checks to off-peak scheduling windows when resource pressure is high.",
            "expected_impact": "Reduce resource contention while preserving data quality checks.",
            "source_copilot": "dataops",
            "source_rule": "resource_quality_scheduling_signal",
            "match": {
                "categories": ["quality_anomaly", "transform_drift"],
                "min_downstream_urgency": 0.4,
            },
        },
    )
