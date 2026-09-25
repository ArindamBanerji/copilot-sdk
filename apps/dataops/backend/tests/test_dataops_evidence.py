from __future__ import annotations

from typing import Any, cast

import numpy as np
from fastapi.testclient import TestClient

from app.evidence_provider import (
    FACTOR_NAMES,
    DataOpsEvidenceProvider,
    build_dataops_evidence_source,
)
from app.vld_preseed import (
    VLD_DO1_ALERT_ID,
    VLD_DO2_ALERT_ID,
    VLD_S1_ALERT_ID,
    seed_vld_dataops_showcase,
)
from copilot_sdk.scoring.investigation import EvidenceProvider, VLDInvestigator
from copilot_sdk.scoring.presets.dataops import DataOpsPreset
from copilot_sdk.scoring.situation_classifier import SituationClassifier


def _source(dataops_data_dir: Any) -> dict[str, Any]:
    return cast(dict[str, Any], seed_vld_dataops_showcase(build_dataops_evidence_source(dataops_data_dir)))


def _alert_vector(alert: dict[str, Any]) -> np.ndarray:
    return cast(np.ndarray, np.asarray([float(alert["factors"][name]) for name in FACTOR_NAMES], dtype=np.float64))


def _investigator(category: str) -> tuple[VLDInvestigator, list[str]]:
    preset = DataOpsPreset()
    categories = list(preset.shape.category_names)
    actions = list(preset.shape.action_names)
    category_index = categories.index(category)
    return (
        VLDInvestigator(
            preset.bootstrap_centroids[category_index],
            np.ones(len(FACTOR_NAMES), dtype=np.float64),
            list(FACTOR_NAMES),
            tau=preset.temperature,
        ),
        actions,
    )


def test_evidence_provider_protocol(dataops_data_dir: Any) -> None:
    provider = DataOpsEvidenceProvider(_source(dataops_data_dir), VLD_DO1_ALERT_ID)

    assert isinstance(provider, EvidenceProvider)


def test_evidence_schema_impact_with_change(dataops_data_dir: Any) -> None:
    provider = DataOpsEvidenceProvider(_source(dataops_data_dir), VLD_DO1_ALERT_ID)

    evidence = provider.read_evidence(VLD_DO1_ALERT_ID, 0, "impact_scope")

    assert evidence is not None
    assert evidence["source"] == "schema_registry"
    assert evidence["value"] > 0.8
    assert evidence["column"] == "MATKL_V2"
    assert evidence["join_fanout_factor"] == 9.0


def test_evidence_schema_impact_no_change(dataops_data_dir: Any) -> None:
    provider = DataOpsEvidenceProvider(_source(dataops_data_dir), VLD_S1_ALERT_ID)

    assert provider.read_evidence(VLD_S1_ALERT_ID, 0, "impact_scope") is None


def test_evidence_system_dependency(dataops_data_dir: Any) -> None:
    provider = DataOpsEvidenceProvider(_source(dataops_data_dir), VLD_DO1_ALERT_ID)

    evidence = provider.read_evidence(VLD_DO1_ALERT_ID, 3, "downstream_urgency")

    assert evidence is not None
    assert evidence["source"] == "dependency_graph"
    assert evidence["value"] >= 0.8
    assert evidence["downstream_systems"] == ["pricing_engine", "inventory_sync", "billing_api"]


def test_evidence_empty_branch(dataops_data_dir: Any) -> None:
    provider = DataOpsEvidenceProvider(_source(dataops_data_dir), "missing-alert")

    assert provider.read_evidence("missing-alert", 0, "impact_scope") is None


def test_evidence_all_six_factors(dataops_data_dir: Any) -> None:
    provider = DataOpsEvidenceProvider(_source(dataops_data_dir), VLD_DO1_ALERT_ID)

    evidence_by_factor = {
        factor_name: provider.read_evidence(VLD_DO1_ALERT_ID, index, factor_name)
        for index, factor_name in enumerate(FACTOR_NAMES)
    }

    assert set(evidence_by_factor) == set(FACTOR_NAMES)
    assert evidence_by_factor["impact_scope"] is not None
    assert evidence_by_factor["source_reliability"] is not None
    assert evidence_by_factor["recurrence_frequency"] is not None
    assert evidence_by_factor["downstream_urgency"] is not None
    assert evidence_by_factor["data_freshness"] is not None
    assert evidence_by_factor["business_criticality"] is not None


def test_preseed_creates_three_alerts(dataops_data_dir: Any) -> None:
    source = _source(dataops_data_dir)

    assert source["vld_showcase_alert_ids"] == [VLD_DO1_ALERT_ID, VLD_DO2_ALERT_ID, VLD_S1_ALERT_ID]
    assert all(alert_id in source["alerts"] for alert_id in source["vld_showcase_alert_ids"])


def test_preseed_idempotent(dataops_data_dir: Any) -> None:
    source = _source(dataops_data_dir)
    before = len(source["alerts"])

    seed_vld_dataops_showcase(source)

    assert len(source["alerts"]) == before
    assert source["vld_showcase_alert_ids"] == [VLD_DO1_ALERT_ID, VLD_DO2_ALERT_ID, VLD_S1_ALERT_ID]


def test_preseed_matkl_v2_linked(dataops_data_dir: Any) -> None:
    source = _source(dataops_data_dir)

    changes = source["schema_changes"]["order_ingestion"]

    assert changes[0]["column"] == "MATKL_V2"
    assert changes[0]["downstream_impact"] == 9
    assert source["alerts"][VLD_DO1_ALERT_ID]["system"] == "order_ingestion"


def test_vld_do1_three_systems(dataops_data_dir: Any) -> None:
    source = _source(dataops_data_dir)
    alert = source["alerts"][VLD_DO1_ALERT_ID]
    investigator, actions = _investigator(str(alert["category"]))

    trace = investigator.investigate(
        VLD_DO1_ALERT_ID,
        str(alert["category"]),
        _alert_vector(alert),
        DataOpsEvidenceProvider(source, VLD_DO1_ALERT_ID),
        budget=2,
        K_weights=np.asarray([10.0, 0.1, 0.1, 4.0, 0.1, 0.1], dtype=np.float64),
        gated_sources={"schema_registry", "dependency_graph"},
    )

    assert actions[trace.final_action] == "escalate_to_owner"
    assert [step.factor_name for step in trace.steps] == ["impact_scope", "downstream_urgency"]
    assert [step.evidence_source for step in trace.steps] == ["schema_registry", "dependency_graph"]
    assert actions[trace.steps[0].action_after] == "escalate_to_owner"
    assert actions[trace.steps[1].action_after] == "escalate_to_owner"
    assert trace.steps[1].margin_after >= trace.steps[0].margin_after


def test_vld_do2_known_pattern_new_twist(dataops_data_dir: Any) -> None:
    source = _source(dataops_data_dir)
    alert = source["alerts"][VLD_DO2_ALERT_ID]
    investigator, actions = _investigator(str(alert["category"]))

    trace = investigator.investigate(
        VLD_DO2_ALERT_ID,
        str(alert["category"]),
        _alert_vector(alert),
        DataOpsEvidenceProvider(source, VLD_DO2_ALERT_ID),
        budget=2,
        K_weights=np.asarray([0.1, 0.1, 10.0, 4.0, 0.1, 0.1], dtype=np.float64),
        gated_sources={"schema_registry", "dependency_graph"},
    )

    assert actions[trace.surface_action] == "refer_to_specialist"
    assert actions[trace.final_action] == "escalate_to_owner"
    assert [step.factor_name for step in trace.steps] == ["recurrence_frequency", "downstream_urgency"]
    assert trace.steps[0].evidence_source == "historical_alerts"
    assert trace.steps[0].evidence_confidence == 0.55
    assert trace.steps[1].evidence_source == "dependency_graph"
    assert trace.steps[1].evidence_confidence == 0.82
    assert trace.steps[1].flipped


def test_s1_conservation_skip(dataops_data_dir: Any) -> None:
    source = _source(dataops_data_dir)
    preset = DataOpsPreset()
    actions = list(preset.shape.action_names)
    categories = list(preset.shape.category_names)
    category = "pipeline_failure"
    mu = preset.bootstrap_centroids[categories.index(category)]
    v = mu[actions.index("auto_approve")]
    investigator = VLDInvestigator(mu, np.ones(len(FACTOR_NAMES)), list(FACTOR_NAMES), tau=preset.temperature)
    surface_action, p_surface = investigator.score(v)
    q_surface = investigator.compute_Q(v, p_surface)
    assessment = SituationClassifier().classify(v, mu, np.ones(len(FACTOR_NAMES)), p_surface, q_surface, default_budget=2)

    trace = investigator.investigate(
        VLD_S1_ALERT_ID,
        category,
        v,
        DataOpsEvidenceProvider(source, VLD_S1_ALERT_ID),
        budget=assessment.recommended_budget,
    )

    assert actions[surface_action] == "auto_approve"
    assert assessment.situation == "S1"
    assert assessment.recommended_budget == 0
    assert trace.budget == 0
    assert trace.steps == []


def test_investigation_health(client: TestClient) -> None:
    response = client.get("/api/investigation/health")

    assert response.status_code == 200
    assert response.json()["investigation_available"] is True


def test_investigation_endpoint(client: TestClient) -> None:
    payload = {
        "decision_id": VLD_DO1_ALERT_ID,
        "category": "pipeline_failure",
        "factor_vector": [0.55, 0.55, 0.30, 0.35, 0.55, 0.70],
        "budget": 2,
        "use_K": False,
    }

    response = client.post("/api/investigation/investigate", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["decision_id"] == VLD_DO1_ALERT_ID
    assert body["category"] == "pipeline_failure"
    assert body["budget_used"] == 2
    assert isinstance(body["steps"], list)
