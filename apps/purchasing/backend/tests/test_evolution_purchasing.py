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
    assert len(PURCHASING_VARIANTS) == 12
    assert {variant.id for variant in PURCHASING_VARIANTS} == {
        "WASTE_THRESHOLD_v1",
        "WASTE_THRESHOLD_v2",
        "LEAD_TIME_BUFFER_v1",
        "LEAD_TIME_BUFFER_v2",
        "ORDER_QUANTITY_THRESHOLD_v1",
        "ORDER_QUANTITY_THRESHOLD_v2",
        "WEATHER_SENSITIVITY_v1",
        "WEATHER_SENSITIVITY_v2",
        "EVENT_LEAD_TIME_v1",
        "EVENT_LEAD_TIME_v2",
        "PRICE_MEMORY_ALERT_v1",
        "PRICE_MEMORY_ALERT_v2",
    }
    assert {variant.family for variant in PURCHASING_VARIANTS} == {
        "waste_threshold",
        "lead_time_buffer",
        "order_quantity_threshold",
        "weather_sensitivity",
        "event_lead_time",
        "price_memory_alert",
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
        "order_quantity_threshold": {"active", "shadow"},
        "weather_sensitivity": {"active", "shadow"},
        "event_lead_time": {"active", "shadow"},
        "price_memory_alert": {"active", "shadow"},
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


def test_order_quantity_threshold_metadata_loads_pd_dimensions() -> None:
    variants = _by_id()
    v1 = variants["ORDER_QUANTITY_THRESHOLD_v1"]["metadata"]
    v2 = variants["ORDER_QUANTITY_THRESHOLD_v2"]["metadata"]

    assert v1["display_name"] == "How much to adjust before flagging"
    assert v2["display_name"] == "How much to adjust before flagging"
    assert v1["par_adjustment_pct"] == 15
    assert v2["par_adjustment_pct"] == 20
    assert v1["candidate_par_adjustment_pct"] == [15, 20]
    assert v2["candidate_par_adjustment_pct"] == [15, 20]


def test_weather_sensitivity_metadata_loads_pd_dimensions() -> None:
    variants = _by_id()
    v1 = variants["WEATHER_SENSITIVITY_v1"]["metadata"]
    v2 = variants["WEATHER_SENSITIVITY_v2"]["metadata"]

    assert v1["display_name"] == "Minimum forecast confidence to act on weather"
    assert v2["display_name"] == "Minimum forecast confidence to act on weather"
    assert v1["forecast_confidence_min"] == pytest.approx(0.70)
    assert v2["forecast_confidence_min"] == pytest.approx(0.80)
    assert v1["candidate_forecast_confidence_min"] == [0.70, 0.80]
    assert v2["candidate_forecast_confidence_min"] == [0.70, 0.80]


def test_event_lead_time_metadata_loads_pd_dimensions() -> None:
    variants = _by_id()
    v1 = variants["EVENT_LEAD_TIME_v1"]["metadata"]
    v2 = variants["EVENT_LEAD_TIME_v2"]["metadata"]

    assert v1["display_name"] == "How far ahead to adjust for events"
    assert v2["display_name"] == "How far ahead to adjust for events"
    assert v1["pre_event_days"] == 3
    assert v2["pre_event_days"] == 5
    assert v1["candidate_pre_event_days"] == [3, 5]
    assert v2["candidate_pre_event_days"] == [3, 5]


def test_price_memory_alert_metadata_loads_pd_dimensions() -> None:
    variants = _by_id()
    v1 = variants["PRICE_MEMORY_ALERT_v1"]["metadata"]
    v2 = variants["PRICE_MEMORY_ALERT_v2"]["metadata"]

    assert v1["display_name"] == "Price deviation before surfacing memory"
    assert v2["display_name"] == "Price deviation before surfacing memory"
    assert v1["deviation_pct"] == 8
    assert v2["deviation_pct"] == 12
    assert v1["candidate_deviation_pct"] == [8, 12]
    assert v2["candidate_deviation_pct"] == [8, 12]


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
        "order_quantity_threshold",
        "weather_sensitivity",
        "event_lead_time",
        "price_memory_alert",
    }
    assert [variant["id"] for variant in variants] == [
        "WASTE_THRESHOLD_v1",
        "WASTE_THRESHOLD_v2",
        "LEAD_TIME_BUFFER_v1",
        "LEAD_TIME_BUFFER_v2",
        "ORDER_QUANTITY_THRESHOLD_v1",
        "ORDER_QUANTITY_THRESHOLD_v2",
        "WEATHER_SENSITIVITY_v1",
        "WEATHER_SENSITIVITY_v2",
        "EVENT_LEAD_TIME_v1",
        "EVENT_LEAD_TIME_v2",
        "PRICE_MEMORY_ALERT_v1",
        "PRICE_MEMORY_ALERT_v2",
    ]
    assert len({variant["id"] for variant in variants}) == len(variants)
