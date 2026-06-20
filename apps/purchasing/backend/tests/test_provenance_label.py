from __future__ import annotations

import json
import random

import pytest

from app.connectors.mock_qbo import MockQBOConnector
from app.data_helpers import (
    ORDERS_PATH,
    SUPPLIERS_PATH,
    assert_no_sample_in_metric,
    is_sample_data,
    load_purchasing_orders,
    reset_purchasing_fixtures,
)
from app.routers.spend_router import SCRAPED_EXTERNAL_PROVENANCE, qbo_bills_for_spend
from generators.purchasing_synthetic import (
    SAMPLE_PROVENANCE,
    SEED,
    generate_orders,
    generate_suppliers,
)


def _raw_orders() -> list[dict]:
    return json.loads(ORDERS_PATH.read_text(encoding="utf-8"))


def _raw_suppliers() -> list[dict]:
    return json.loads(SUPPLIERS_PATH.read_text(encoding="utf-8"))


def _generated_fixture() -> tuple[list[dict], list[dict]]:
    rng = random.Random(SEED)
    suppliers = generate_suppliers(rng)
    orders = generate_orders(rng, suppliers)
    return suppliers, orders


def test_all_orders_have_provenance():
    orders = _raw_orders()

    assert orders
    assert all("provenance" in order for order in orders)
    assert all(order["provenance"] == SAMPLE_PROVENANCE for order in orders)


def test_all_suppliers_have_provenance():
    suppliers = _raw_suppliers()

    assert suppliers
    assert all("provenance" in supplier for supplier in suppliers)
    assert all(supplier["provenance"] == SAMPLE_PROVENANCE for supplier in suppliers)


def test_generator_output_has_provenance():
    suppliers, orders = _generated_fixture()

    assert all(supplier.get("provenance") == SAMPLE_PROVENANCE for supplier in suppliers)
    assert all(order.get("provenance") == SAMPLE_PROVENANCE for order in orders)


def test_generator_deterministic_with_provenance():
    first_suppliers, first_orders = _generated_fixture()
    second_suppliers, second_orders = _generated_fixture()

    assert first_suppliers == second_suppliers
    assert first_orders == second_orders


def test_load_orders_preserves_provenance():
    reset_purchasing_fixtures()
    orders = load_purchasing_orders()

    assert orders
    assert all(order.get("provenance") == SAMPLE_PROVENANCE for order in orders)


def test_is_sample_data():
    assert is_sample_data({"provenance": "sample"}) is True
    assert is_sample_data({"provenance": "scraped_external"}) is False
    assert is_sample_data({}) is False


def test_assert_no_sample_raises():
    with pytest.raises(ValueError, match="F-26 VIOLATION"):
        assert_no_sample_in_metric([{"provenance": "sample"}], "food_cost")


def test_assert_no_sample_passes_real():
    assert_no_sample_in_metric([{"provenance": "scraped_external"}], "food_cost")


def test_assert_no_sample_passes_empty():
    assert_no_sample_in_metric([], "food_cost")


def test_spend_dashboard_uses_real_data():
    rows = qbo_bills_for_spend(MockQBOConnector())

    assert rows
    assert all(row.get("provenance") == SCRAPED_EXTERNAL_PROVENANCE for row in rows)
    assert all(row.get("provenance") != SAMPLE_PROVENANCE for row in rows)
    assert_no_sample_in_metric(rows, "spend_dashboard")
