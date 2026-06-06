from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.dataops.backend.app.evolution import (
    DATAOPS_EVOLVER_CONFIG,
    DATAOPS_VARIANTS,
    get_dataops_variant_specs,
    get_dataops_variants,
)
from apps.dataops.backend.app.main import create_app
from copilot_sdk.scoring.presets.dataops import DataOpsPreset


def _by_id(variants: list[dict]) -> dict[str, dict]:
    return {str(variant["id"]): variant for variant in variants}


def test_dataops_variant_specs_define_expected_families() -> None:
    specs = get_dataops_variant_specs()

    assert len(DATAOPS_VARIANTS) == 4
    assert len(specs) == 4
    assert {spec.family for spec in specs} == {"auto_approve_threshold", "scheduling_criteria"}
    assert {spec.status for spec in specs if spec.family == "auto_approve_threshold"} == {"active", "shadow"}
    assert {spec.status for spec in specs if spec.family == "scheduling_criteria"} == {"active", "shadow"}
    assert len({spec.id for spec in specs}) == 4


def test_dataops_variant_metadata_values() -> None:
    variants = _by_id(get_dataops_variants())

    auto_v1 = variants["AUTO_APPROVE_THRESHOLD_v1"]["metadata"]
    auto_v2 = variants["AUTO_APPROVE_THRESHOLD_v2"]["metadata"]
    assert auto_v1["confidence_threshold"] == 0.85
    assert auto_v1["scope_limit"] == 0.30
    assert auto_v2["confidence_threshold"] == 0.90
    assert auto_v2["scope_limit"] == 0.25
    assert auto_v2["confidence_threshold"] > auto_v1["confidence_threshold"]
    assert auto_v2["scope_limit"] < auto_v1["scope_limit"]

    sched_v1 = variants["SCHEDULING_CRITERIA_v1"]["metadata"]
    sched_v2 = variants["SCHEDULING_CRITERIA_v2"]["metadata"]
    assert sched_v1["off_peak_hours"] == [2, 6]
    assert sched_v1["resource_threshold"] == 0.70
    assert sched_v2["off_peak_hours"] == [1, 5]
    assert sched_v2["resource_threshold"] == 0.65
    assert sched_v2["off_peak_hours"][0] < sched_v1["off_peak_hours"][0]
    assert sched_v2["resource_threshold"] < sched_v1["resource_threshold"]

    for metadata in (sched_v1, sched_v2):
        start, end = metadata["off_peak_hours"]
        assert 0 <= start < end <= 23


def test_dataops_evolver_config_matches_preset() -> None:
    preset = DataOpsPreset()

    assert DATAOPS_EVOLVER_CONFIG.categories == list(preset.shape.category_names)
    assert len(DATAOPS_EVOLVER_CONFIG.categories) == 6
    assert DATAOPS_EVOLVER_CONFIG.promotion_min_samples == 50
    assert DATAOPS_EVOLVER_CONFIG.exploration_constant == pytest.approx(1.414)
    assert DATAOPS_EVOLVER_CONFIG.promotion_improvement_threshold == pytest.approx(0.05)


def test_get_dataops_variants_returns_fresh_payloads() -> None:
    first = get_dataops_variants()
    second = get_dataops_variants()

    assert first is not second
    assert first[0] is not second[0]
    assert first[0]["metadata"] is not second[0]["metadata"]

    first_by_id = _by_id(first)
    second_by_id = _by_id(second)
    first_by_id["SCHEDULING_CRITERIA_v1"]["metadata"]["off_peak_hours"].append(99)

    assert second_by_id["SCHEDULING_CRITERIA_v1"]["metadata"]["off_peak_hours"] == [2, 6]


def test_dataops_evolution_variants_endpoint_merges_configured_and_persisted(client: TestClient) -> None:
    payload = client.get("/api/evolution/variants").json()
    variants = payload["variants"]
    ids = [variant.get("id") or variant.get("variant_id") for variant in variants]

    assert payload["domain"] == "dataops"
    assert {"domain", "variants", "active_rules", "promoted_rules", "total_active", "total_promoted"} == set(payload)
    assert len(ids) == len(set(ids))
    assert {
        "AUTO_APPROVE_THRESHOLD_v1",
        "AUTO_APPROVE_THRESHOLD_v2",
        "SCHEDULING_CRITERIA_v1",
        "SCHEDULING_CRITERIA_v2",
        "V-DO-SCHED-001",
    } <= set(ids)
    assert {variant.get("family") for variant in variants if variant.get("family")} == {
        "auto_approve_threshold",
        "scheduling_criteria",
    }


def test_dataops_evolution_variants_fresh_store_returns_static_config(tmp_path) -> None:
    client = TestClient(create_app(db_path=tmp_path / "fresh_dataops_variants.db", demo_bundle_path=False))
    payload = client.get("/api/evolution/variants").json()
    variants = payload["variants"]

    assert payload["domain"] == "dataops"
    assert {variant["id"] for variant in variants} == {
        "AUTO_APPROVE_THRESHOLD_v1",
        "AUTO_APPROVE_THRESHOLD_v2",
        "SCHEDULING_CRITERIA_v1",
        "SCHEDULING_CRITERIA_v2",
    }
