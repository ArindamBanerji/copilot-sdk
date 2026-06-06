from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.evolution import (
    PURCHASING_EVOLVER_CONFIG,
    PURCHASING_VARIANTS,
    get_purchasing_variant_specs,
    get_purchasing_variants,
)
from app.main import create_app
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset


def _by_id() -> dict[str, dict]:
    return {variant["id"]: variant for variant in get_purchasing_variants()}


def test_purchasing_variant_specs_cover_expected_families() -> None:
    assert len(PURCHASING_VARIANTS) == 4
    assert {variant.id for variant in PURCHASING_VARIANTS} == {
        "WASTE_THRESHOLD_v1",
        "WASTE_THRESHOLD_v2",
        "LEAD_TIME_BUFFER_v1",
        "LEAD_TIME_BUFFER_v2",
    }
    assert {variant.family for variant in PURCHASING_VARIANTS} == {
        "waste_threshold",
        "lead_time_buffer",
    }
    assert len({variant.id for variant in PURCHASING_VARIANTS}) == len(PURCHASING_VARIANTS)


def test_purchasing_variants_have_active_and_shadow_per_family() -> None:
    statuses = {
        variant.family: {family_variant.status for family_variant in PURCHASING_VARIANTS if family_variant.family == variant.family}
        for variant in PURCHASING_VARIANTS
    }

    assert statuses == {
        "waste_threshold": {"active", "shadow"},
        "lead_time_buffer": {"active", "shadow"},
    }


def test_waste_threshold_metadata_is_valid_and_less_asymmetric_in_v2() -> None:
    variants = _by_id()
    v1 = variants["WASTE_THRESHOLD_v1"]["metadata"]
    v2 = variants["WASTE_THRESHOLD_v2"]["metadata"]

    for metadata in (v1, v2):
        penalty_sum = metadata["over_order_penalty"] + metadata["under_order_penalty"]
        assert penalty_sum == pytest.approx(1.0)
        assert metadata["under_order_penalty"] >= metadata["over_order_penalty"]

    assert v2["over_order_penalty"] > v1["over_order_penalty"]
    assert v2["under_order_penalty"] < v1["under_order_penalty"]


def test_lead_time_buffer_metadata_is_more_conservative_in_v2() -> None:
    variants = _by_id()
    v1 = variants["LEAD_TIME_BUFFER_v1"]["metadata"]
    v2 = variants["LEAD_TIME_BUFFER_v2"]["metadata"]

    assert v1["buffer_days"] == 2
    assert v2["buffer_days"] == 3
    assert v2["buffer_days"] > v1["buffer_days"]
    assert v1["supplier_reliability_floor"] == pytest.approx(0.60)
    assert v2["supplier_reliability_floor"] == pytest.approx(0.70)
    assert v2["supplier_reliability_floor"] > v1["supplier_reliability_floor"]
    for metadata in (v1, v2):
        assert 0.0 < metadata["supplier_reliability_floor"] < 1.0


def test_purchasing_evolver_config_matches_preset() -> None:
    preset_categories = list(PurchasingPreset().shape.category_names)

    assert PURCHASING_EVOLVER_CONFIG.categories == preset_categories
    assert len(PURCHASING_EVOLVER_CONFIG.categories) == 5
    assert PURCHASING_EVOLVER_CONFIG.promotion_min_samples == 50
    assert PURCHASING_EVOLVER_CONFIG.exploration_constant == pytest.approx(1.414)


def test_purchasing_variant_payloads_are_fresh_copies() -> None:
    first = get_purchasing_variants()
    second = get_purchasing_variants()
    first_specs = get_purchasing_variant_specs()
    second_specs = get_purchasing_variant_specs()

    assert first is not second
    assert first[0] is not second[0]
    assert first[0]["metadata"] is not second[0]["metadata"]
    assert first_specs is not second_specs
    assert first_specs[0].metadata is not second_specs[0].metadata

    first[0]["metadata"]["over_order_penalty"] = 99
    assert second[0]["metadata"]["over_order_penalty"] == pytest.approx(0.30)


def test_purchasing_evolution_endpoint_returns_static_variants_without_persisted_events(tmp_path) -> None:
    client = TestClient(create_app(db_path=tmp_path / "fresh_purchasing.db", demo_bundle_path=False))
    payload = client.get("/api/evolution/variants").json()
    variants = payload["variants"]

    assert payload["domain"] == "purchasing"
    assert set(payload) == {
        "domain",
        "variants",
        "active_rules",
        "promoted_rules",
        "total_active",
        "total_promoted",
    }
    assert {variant["family"] for variant in variants} == {
        "waste_threshold",
        "lead_time_buffer",
    }
    assert [variant["id"] for variant in variants] == [
        "WASTE_THRESHOLD_v1",
        "WASTE_THRESHOLD_v2",
        "LEAD_TIME_BUFFER_v1",
        "LEAD_TIME_BUFFER_v2",
    ]
    assert len({variant["id"] for variant in variants}) == len(variants)
