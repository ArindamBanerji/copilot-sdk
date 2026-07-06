from __future__ import annotations

import json
import random

import pytest

from app.connectors.mock_qbo import MockQBOConnector
from app.data_helpers import (
    DATA_DIR,
    ORDERS_PATH,
    SUPPLIERS_PATH,
    assert_no_sample_in_metric,
    is_sample_data,
    load_purchasing_orders,
    reset_purchasing_fixtures,
    write_purchasing_fixture,
)
from app.routers.spend_router import qbo_bills_for_spend
from app.main import SEED_FIXTURE_PATH
from generators.purchasing_synthetic import (
    SAMPLE_PROVENANCE,
    SEED,
    VALID_FIXTURE_PROVENANCE,
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


def test_seed_fixture_has_sample_provenance():
    rows = json.loads(SEED_FIXTURE_PATH.read_text(encoding="utf-8"))

    assert rows
    assert all(row.get("provenance") == SAMPLE_PROVENANCE for row in rows)


def test_all_purchasing_fixtures_have_provenance():
    missing: list[str] = []
    for path in sorted(DATA_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for label, record in _fixture_records(path.name, data):
            if record.get("provenance") not in VALID_FIXTURE_PROVENANCE:
                missing.append(f"{path.name}:{label}")

    assert missing == []


def test_valid_fixture_provenance_values():
    """Provenance must be one of the known non-production values."""
    for path in sorted(DATA_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for label, record in _fixture_records(path.name, data):
            prov = record.get("provenance")
            assert prov is not None, f"{path.name}:{label} has no provenance"
            assert prov in VALID_FIXTURE_PROVENANCE, (
                f"{path.name}:{label} has unknown provenance '{prov}'. "
                f"Valid: {VALID_FIXTURE_PROVENANCE}"
            )


def test_write_purchasing_fixture_rejects_missing_provenance(tmp_path):
    path = tmp_path / "order_metadata.json"

    with pytest.raises(ValueError, match="Record decision-1 missing provenance"):
        write_purchasing_fixture(path, {"decision-1": {"decision_id": "decision-1"}})


def test_is_sample_data():
    assert is_sample_data({"provenance": "sample"}) is True
    assert is_sample_data({"provenance": "scraped_external"}) is False
    assert is_sample_data({}) is False
    assert is_sample_data({"supplier_id": "PUR-SUP-001"}) is True
    assert is_sample_data({"order_id": "PUR-ORD-0001"}) is True
    assert is_sample_data({"archetype": "reliable_premium"}) is True


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
    assert all(row.get("provenance") == SAMPLE_PROVENANCE for row in rows)
    with pytest.raises(ValueError, match="F-26 VIOLATION"):
        assert_no_sample_in_metric(rows, "spend_dashboard")


def _fixture_records(filename: str, data: object) -> list[tuple[str, dict]]:
    if isinstance(data, list):
        return [
            (f"[{index}]", record)
            for index, record in enumerate(data)
            if isinstance(record, dict)
        ]

    if not isinstance(data, dict):
        return []

    if filename == "order_metadata.json":
        return [
            (str(decision_id), record)
            for decision_id, record in data.items()
            if isinstance(record, dict)
        ]

    records = [("$", data)]
    variants = data.get("variants")
    if isinstance(variants, list):
        records.extend(
            (f"variants[{index}]", variant)
            for index, variant in enumerate(variants)
            if isinstance(variant, dict)
        )
    return records
