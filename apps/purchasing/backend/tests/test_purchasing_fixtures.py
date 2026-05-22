from __future__ import annotations

from collections import Counter
from datetime import date
from statistics import mean

import pytest

from app import data_helpers
from app.data_helpers import (
    get_orders_by_category,
    get_orders_by_supplier,
    get_supplier_by_id,
    load_purchasing_orders,
    load_purchasing_suppliers,
    reset_purchasing_fixtures,
)
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from generators.purchasing_synthetic import (
    ARCHETYPE_COUNTS,
    NAMED_SUPPLIERS,
    SEED,
    generate_orders,
    generate_suppliers,
)
import random


SUPPLIER_FIELDS = {
    "supplier_id",
    "name",
    "archetype",
    "categories",
    "primary_category",
    "otif_score",
    "avg_order_value",
    "price_index",
    "lead_time_days",
    "waste_rate",
    "order_count_90d",
    "exception_rate",
    "payment_terms",
    "quality_score",
    "recent_trend",
    "years_active",
    "min_order_value",
    "delivery_window",
    "notes",
}
ORDER_FIELDS = {
    "order_id",
    "supplier_id",
    "supplier_name",
    "category",
    "items",
    "total_value",
    "order_date",
    "delivery_date",
    "status",
    "day_of_week",
    "factors",
    "outcome",
    "verified",
    "verification_score",
}
OUTCOME_FIELDS = {
    "action_taken",
    "actual_usage_pct",
    "waste_pct",
    "stockout",
    "quality_issue",
    "cost_variance_pct",
}


@pytest.fixture(autouse=True)
def reset_fixture_cache():
    reset_purchasing_fixtures()
    yield
    reset_purchasing_fixtures()


def test_50_suppliers():
    assert len(load_purchasing_suppliers()) == 50


def test_supplier_has_required_fields():
    for supplier in load_purchasing_suppliers():
        assert SUPPLIER_FIELDS <= set(supplier)
        for field in SUPPLIER_FIELDS:
            assert supplier[field] is not None


def test_supplier_ids_unique():
    supplier_ids = [supplier["supplier_id"] for supplier in load_purchasing_suppliers()]

    assert len(supplier_ids) == len(set(supplier_ids))


def test_all_categories_represented():
    categories = {
        category
        for supplier in load_purchasing_suppliers()
        for category in supplier["categories"]
    }

    assert categories == set(PurchasingPreset().shape.category_names)


def test_12_archetypes_represented():
    counts = Counter(supplier["archetype"] for supplier in load_purchasing_suppliers())

    assert counts == ARCHETYPE_COUNTS


def test_otif_bounded():
    assert all(0.0 <= supplier["otif_score"] <= 1.0 for supplier in load_purchasing_suppliers())


def test_sierra_farms_exists():
    supplier = get_supplier_by_id("PUR-SUP-001")

    assert supplier["name"] == "Sierra Farms"
    assert supplier["archetype"] == "reliable_premium"
    assert set(supplier["categories"]) == {"protein", "produce"}


def test_greenleaf_is_declining():
    supplier = get_supplier_by_id("PUR-SUP-009")

    assert supplier["name"] == "Greenleaf Organics"
    assert supplier["recent_trend"] == "declining"
    assert supplier["primary_category"] == "produce"


def test_nuvend_is_new():
    supplier = get_supplier_by_id("PUR-SUP-008")

    assert supplier["name"] == "NuVend Supply"
    assert supplier["archetype"] == "new_vendor"
    assert set(supplier["categories"]) == set(PurchasingPreset().shape.category_names)


def test_500_orders():
    assert len(load_purchasing_orders()) == 500


def test_order_has_required_fields():
    for order in load_purchasing_orders():
        assert ORDER_FIELDS <= set(order)
        assert OUTCOME_FIELDS <= set(order["outcome"])


def test_order_ids_unique():
    order_ids = [order["order_id"] for order in load_purchasing_orders()]

    assert len(order_ids) == len(set(order_ids))


def test_factors_have_7_fields():
    expected = set(PurchasingPreset().shape.factor_names)

    for order in load_purchasing_orders():
        assert set(order["factors"]) == expected


def test_factor_values_bounded():
    for order in load_purchasing_orders():
        assert all(0.0 <= value <= 1.0 for value in order["factors"].values())


def test_all_categories_in_orders():
    categories = {order["category"] for order in load_purchasing_orders()}

    assert categories == set(PurchasingPreset().shape.category_names)


def test_all_actions_in_outcomes():
    actions = {order["outcome"]["action_taken"] for order in load_purchasing_orders()}

    assert actions == set(PurchasingPreset().shape.action_names)


def test_verified_orders_have_score():
    for order in load_purchasing_orders():
        assert order["verified"] is True
        assert 0.0 <= order["verification_score"] <= 1.0


def test_supplier_ids_match_suppliers():
    supplier_ids = {supplier["supplier_id"] for supplier in load_purchasing_suppliers()}

    assert all(order["supplier_id"] in supplier_ids for order in load_purchasing_orders())


def test_monday_over_ordering_pattern():
    orders = load_purchasing_orders()
    monday = [order["outcome"]["waste_pct"] for order in orders if order["day_of_week"] == "Monday"]
    non_monday = [order["outcome"]["waste_pct"] for order in orders if order["day_of_week"] != "Monday"]

    assert len(monday) >= 40
    assert mean(monday) > mean(non_monday)


def test_weather_insensitive_produce_pattern():
    orders = load_purchasing_orders()
    hot_produce = [
        order
        for order in orders
        if order["category"] == "produce" and order["factors"]["weather_forecast"] < 0.4
    ]
    baseline = [
        order
        for order in orders
        if not (order["category"] == "produce" and order["factors"]["weather_forecast"] < 0.4)
    ]

    assert len(hot_produce) >= 30
    assert mean(order["outcome"]["waste_pct"] for order in hot_produce) > mean(
        order["outcome"]["waste_pct"] for order in baseline
    )


def test_event_overreaction_pattern():
    event_orders = [
        order
        for order in load_purchasing_orders()
        if order["factors"]["event_flag"] > 0.7
    ]

    assert len(event_orders) >= 25
    assert mean(order["outcome"]["waste_pct"] for order in event_orders) > 0.15
    assert mean(order["outcome"]["actual_usage_pct"] for order in event_orders) < 0.75


def test_declining_supplier_quality_trend():
    orders = sorted(get_orders_by_supplier("PUR-SUP-009"), key=lambda row: row["order_date"])
    midpoint = len(orders) // 2
    early_issues = sum(order["outcome"]["quality_issue"] for order in orders[:midpoint])
    late_issues = sum(order["outcome"]["quality_issue"] for order in orders[midpoint:])

    assert 20 <= len(orders) <= 40
    assert late_issues > early_issues


def test_heritage_loyalty_bias():
    orders = get_orders_by_supplier("PUR-SUP-007")

    assert 30 <= len(orders) <= 50
    assert mean(order["factors"]["price_memory_index"] for order in orders) < 0.5
    assert all(order["outcome"]["action_taken"] != "skip" for order in orders)


def test_nuvend_underutilized():
    orders = get_orders_by_supplier("PUR-SUP-008")

    assert 10 <= len(orders) < 25
    assert mean(order["verification_score"] for order in orders) >= 0.75


def test_get_supplier_by_id():
    assert get_supplier_by_id("PUR-SUP-002")["name"] == "Pacific Seafood Co"


def test_get_supplier_not_found():
    assert get_supplier_by_id("missing") is None


def test_get_orders_by_supplier():
    orders = get_orders_by_supplier("PUR-SUP-007")

    assert orders
    assert all(order["supplier_id"] == "PUR-SUP-007" for order in orders)


def test_get_orders_by_category():
    orders = get_orders_by_category("produce")

    assert orders
    assert all(order["category"] == "produce" for order in orders)


def test_reset_clears_cache():
    load_purchasing_suppliers()
    load_purchasing_orders()

    assert data_helpers._supplier_cache is not None
    assert data_helpers._order_cache is not None
    reset_purchasing_fixtures()
    assert data_helpers._supplier_cache is None
    assert data_helpers._order_cache is None


def test_generator_is_deterministic():
    first_rng = random.Random(SEED)
    second_rng = random.Random(SEED)

    first_suppliers = generate_suppliers(first_rng)
    second_suppliers = generate_suppliers(second_rng)
    first_orders = generate_orders(first_rng, first_suppliers)
    second_orders = generate_orders(second_rng, second_suppliers)

    assert first_suppliers == second_suppliers
    assert first_orders == second_orders


def test_order_dates_cover_six_months():
    order_dates = [date.fromisoformat(order["order_date"]) for order in load_purchasing_orders()]

    assert min(order_dates).isoformat() >= "2025-11-24"
    assert max(order_dates).isoformat() <= "2026-05-21"
    assert (max(order_dates) - min(order_dates)).days >= 150


def test_required_named_suppliers_exist():
    suppliers = {supplier["supplier_id"]: supplier for supplier in load_purchasing_suppliers()}

    for supplier_id, name, archetype, categories in NAMED_SUPPLIERS:
        supplier = suppliers[supplier_id]
        assert supplier["name"] == name
        assert supplier["archetype"] == archetype
        assert set(supplier["categories"]) == set(categories)
