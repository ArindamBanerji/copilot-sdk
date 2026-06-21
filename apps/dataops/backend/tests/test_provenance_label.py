from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.celonis_connector import CelonisConnector
from app.data_helpers import assert_no_sample_in_metric, is_sample_data
from app.sap_connector import SAPConnector


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_all_fixture_jsons_have_provenance() -> None:
    for path in DATA_DIR.rglob("*.json"):
        payload = _load_json(path)
        _assert_sample_payload(payload, path)


def test_fallback_jsons_have_provenance() -> None:
    for path in (DATA_DIR / "fallback").glob("*.json"):
        payload = _load_json(path)
        assert isinstance(payload, dict), path
        assert payload.get("provenance") == "sample"


def test_sap_orders_have_provenance() -> None:
    orders = _load_json(DATA_DIR / "sap_purchase_orders.json")

    assert len(orders) == 12
    assert all(order.get("provenance") == "sample" for order in orders)


def test_sap_suppliers_have_provenance() -> None:
    suppliers = _load_json(DATA_DIR / "sap_suppliers.json")

    assert len(suppliers) == 10
    assert all(supplier.get("provenance") == "sample" for supplier in suppliers)


def test_sap_connector_provenance_tier() -> None:
    assert SAPConnector().provenance_tier == "sample"


def test_celonis_connector_provenance_tier() -> None:
    assert CelonisConnector().provenance_tier == "sample"


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        ({"provenance": "sample"}, True),
        ({"provenance": "scraped_external"}, False),
        ({}, False),
    ],
)
def test_is_sample_data(record: dict, expected: bool) -> None:
    assert is_sample_data(record) is expected


def test_assert_no_sample_raises() -> None:
    records = [{"provenance": "sample"}, {"provenance": "scraped_external"}]

    with pytest.raises(ValueError, match="F-26 VIOLATION: 1/2 records feeding metric 'cycle_time'"):
        assert_no_sample_in_metric(records, "cycle_time")


def test_assert_no_sample_passes() -> None:
    records = [{"provenance": "scraped_external"}, {"provenance": "live_customer"}]

    assert_no_sample_in_metric(records, "cycle_time")


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_sample_payload(payload, path: Path) -> None:
    if isinstance(payload, list):
        assert payload, path
        assert all(isinstance(record, dict) and record.get("provenance") == "sample" for record in payload), path
        return

    assert isinstance(payload, dict), path
    assert payload.get("provenance") == "sample", path
