from __future__ import annotations

from statistics import mean, pstdev
from typing import Any
from urllib.parse import quote

from fastapi.testclient import TestClient

from apps.purchasing.backend.app.connectors.mock_qbo import MockQBOConnector
from apps.purchasing.backend.app.connectors.qbo_connector import QBOConnector
from apps.purchasing.backend.app.main import create_app
from copilot_sdk.di.profiler import BaseSourceProfiler


def _client() -> TestClient:
    return TestClient(create_app(db_path=":memory:", demo_bundle_path=False))


def _walk_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(nested))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_keys(item))
    return keys


def _invoice_rows(connector: MockQBOConnector, supplier_id: str) -> list[dict]:
    return [row for row in connector.fetch_bills() if row["supplier_id"] == supplier_id]


def _first_item_name(connector: MockQBOConnector, supplier_id: str) -> str:
    invoice = next(row for row in _invoice_rows(connector, supplier_id) if row.get("line_items"))
    return str(invoice["line_items"][0]["item_name"])


def _price_history(connector: MockQBOConnector, supplier: dict) -> list[dict]:
    return connector.compute_price_history(supplier["supplier_id"], _first_item_name(connector, supplier["supplier_id"]))


def _price_cv(history: list[dict]) -> float:
    prices = [row["unit_price"] for row in history]
    return pstdev(prices) / mean(prices) if len(prices) > 1 else 0.0


def test_protocol_source_name():
    assert QBOConnector.source_name == "quickbooks_online"
    assert MockQBOConnector.source_name == "quickbooks_online_mock"


def test_protocol_entity_type():
    assert QBOConnector.entity_type == "accounting"
    assert MockQBOConnector.entity_type == "accounting"


def test_protocol_trust_tier():
    assert QBOConnector.trust_tier == 1
    assert MockQBOConnector.trust_tier == 1


def test_protocol_fetch():
    records = MockQBOConnector().fetch("vendors")

    assert records
    assert isinstance(records[0], dict)


def test_protocol_validate():
    record = MockQBOConnector().fetch("vendors")[0]

    assert MockQBOConnector().validate(record) is True


def test_mock_vendors_count():
    assert len(MockQBOConnector().fetch_vendors()) >= 30


def test_mock_bills_count():
    assert len(MockQBOConnector().fetch_bills()) >= 200


def test_mock_purchase_orders_count():
    assert len(MockQBOConnector().fetch_purchase_orders()) >= 150


def test_mock_payments_count():
    assert len(MockQBOConnector().fetch_payments()) >= 50


def test_price_history_returns_dated_prices():
    connector = MockQBOConnector()
    supplier = connector.fetch_vendors()[0]
    first_invoice = next(row for row in connector.fetch_bills() if row["supplier_id"] == supplier["supplier_id"])
    item_name = first_invoice["line_items"][0]["item_name"]

    history = connector.compute_price_history(supplier["supplier_id"], item_name)

    assert history
    assert {"date", "unit_price"}.issubset(history[0])


def test_price_history_gold_vendor_stable():
    connector = MockQBOConnector()
    history = connector.compute_price_history("SUP-001", "salmon filet")
    prices = [row["unit_price"] for row in history]

    assert len(prices) >= 3
    assert pstdev(prices) < mean(prices) * 0.05


def test_lead_time_computation():
    payload = MockQBOConnector().compute_lead_times("SUP-001")

    assert payload["sample_count"] > 0
    assert payload["mean_days"] is not None


def test_lead_time_by_quarter():
    payload = MockQBOConnector().compute_lead_times("SUP-001")

    assert isinstance(payload["by_quarter"], dict)
    assert payload["by_quarter"]


def test_no_qbo_field_names():
    data = MockQBOConnector()._data
    bad_tokens = ("Vendor", "Bill", "TotalAmt", "DisplayName", "VendorRef")

    for key in _walk_keys(data):
        assert not any(token in key for token in bad_tokens), key


def test_credentials_not_in_fixtures():
    data = MockQBOConnector()._data
    bad_tokens = ("client_secret", "refresh_token", "access_token")

    for key in _walk_keys(data):
        assert key not in bad_tokens


def test_validate_valid_vendor():
    record = {"record_type": "supplier", "supplier_id": "SUP-001", "supplier_name": "Sysco Valley"}

    assert MockQBOConnector().validate(record) is True


def test_validate_missing_name():
    record = {"record_type": "supplier", "supplier_id": "SUP-001"}

    assert MockQBOConnector().validate(record) is False


def test_qbo_router_vendors_200():
    response = _client().get("/api/purchasing/qbo/vendors")

    assert response.status_code == 200
    assert len(response.json()) >= 30


def test_qbo_router_profile_200():
    response = _client().get("/api/purchasing/qbo/profile")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_name"] == "quickbooks_online_mock"
    assert payload["record_count"] >= 430


def test_qbo_router_mounted():
    response = _client().get("/api/purchasing/qbo/status")

    assert response.status_code == 200
    assert response.json()["connected"] is True


def test_profiler_integration():
    connector = MockQBOConnector()
    profile = BaseSourceProfiler(connector).profile(["vendors", "bills"])

    assert profile.source_name == "quickbooks_online_mock"
    assert profile.entity_type == "accounting"
    assert profile.record_count >= 230


def test_price_memory_index_computable():
    connector = MockQBOConnector()
    target_archetypes = {"gold_reliable", "seasonal_premium", "price_memory"}

    for supplier in connector.fetch_vendors():
        if supplier["archetype"] not in target_archetypes:
            continue
        history = _price_history(connector, supplier)
        assert len(history) >= 3, supplier["supplier_id"]
        assert all(row["unit_price"] > 0 for row in history)


def test_supplier_lead_time_computable():
    connector = MockQBOConnector()

    for supplier in connector.fetch_vendors():
        has_orders = any(row["supplier_id"] == supplier["supplier_id"] for row in connector.fetch_purchase_orders())
        has_bills = any(row["supplier_id"] == supplier["supplier_id"] for row in connector.fetch_bills())
        if not (has_orders and has_bills):
            continue
        stats = connector.compute_lead_times(supplier["supplier_id"])
        assert stats["sample_count"] > 0, supplier["supplier_id"]
        assert stats["mean_days"] > 0


def test_all_30_vendors_have_price_history():
    connector = MockQBOConnector()

    for supplier in connector.fetch_vendors():
        invoices = _invoice_rows(connector, supplier["supplier_id"])
        assert invoices, supplier["supplier_id"]
        assert any(invoice.get("line_items") for invoice in invoices)


def test_vendor_archetypes_distinct():
    connector = MockQBOConnector()
    vendors = connector.fetch_vendors()
    gold_cv = mean(_price_cv(_price_history(connector, row)) for row in vendors if row["archetype"] == "gold_reliable")
    seasonal_cv = mean(
        _price_cv(_price_history(connector, row)) for row in vendors if row["archetype"] == "seasonal_premium"
    )

    assert seasonal_cv > gold_cv


def test_seasonal_vendors_price_spike():
    connector = MockQBOConnector()

    for supplier in connector.fetch_vendors():
        if supplier["archetype"] != "seasonal_premium":
            continue
        history = _price_history(connector, supplier)
        peak = [row["unit_price"] for row in history if int(row["date"][5:7]) in (11, 12)]
        off_season = [row["unit_price"] for row in history if int(row["date"][5:7]) not in (11, 12)]
        assert peak and off_season
        assert mean(peak) >= mean(off_season) * 1.10


def test_price_memory_step_up():
    connector = MockQBOConnector()

    for supplier in connector.fetch_vendors():
        if supplier["archetype"] != "price_memory":
            continue
        history = _price_history(connector, supplier)
        first_half = history[: len(history) // 2]
        second_half = history[len(history) // 2 :]
        assert mean(row["unit_price"] for row in second_half) >= mean(row["unit_price"] for row in first_half) * 1.05


def test_trust_trap_vendors():
    connector = MockQBOConnector()

    for supplier in connector.fetch_vendors():
        if supplier["archetype"] != "trust_trap":
            continue
        history = _price_history(connector, supplier)
        split = max(1, int(len(history) * 0.8))
        early = history[:split]
        late = history[split:]
        assert late
        assert mean(row["unit_price"] for row in late) >= mean(row["unit_price"] for row in early) * 1.10


def test_po_bill_matching_coverage():
    connector = MockQBOConnector()
    bill_keys = {
        (row["supplier_id"], round(float(row["amount"]), 2))
        for row in connector.fetch_bills()
    }
    matched = [
        row for row in connector.fetch_purchase_orders()
        if (row["supplier_id"], round(float(row["amount"]), 2)) in bill_keys
    ]

    assert len(matched) >= len(connector.fetch_purchase_orders()) * 0.5


def test_lead_time_realistic():
    connector = MockQBOConnector()

    for supplier in connector.fetch_vendors():
        stats = connector.compute_lead_times(supplier["supplier_id"])
        if stats["sample_count"] == 0:
            continue
        assert 1 <= stats["mean_days"] <= 14
        assert all(value >= 0 for value in stats["by_quarter"].values())


def test_fetch_unknown_entity_id():
    assert MockQBOConnector().fetch("nonexistent") == []


def test_vendor_with_no_bills():
    fixture = {
        "vendors": [{"record_type": "supplier", "supplier_id": "SUP-X", "supplier_name": "No Bill Supply"}],
        "bills": [],
        "purchase_orders": [],
        "payments": [],
    }

    assert MockQBOConnector(fixture).compute_price_history("SUP-X", "salmon filet") == []


def test_vendor_with_no_pos():
    fixture = {
        "vendors": [{"record_type": "supplier", "supplier_id": "SUP-X", "supplier_name": "No Order Supply"}],
        "bills": [],
        "purchase_orders": [],
        "payments": [],
    }

    assert MockQBOConnector(fixture).compute_lead_times("SUP-X")["sample_count"] == 0


def test_empty_line_items():
    fixture = {
        "vendors": [{"record_type": "supplier", "supplier_id": "SUP-X", "supplier_name": "Empty Lines"}],
        "bills": [
            {
                "record_type": "invoice",
                "invoice_id": "INV-X",
                "supplier_id": "SUP-X",
                "supplier_name": "Empty Lines",
                "invoice_date": "2025-01-01",
                "amount": 100.0,
                "line_items": [],
                "timestamp": "2025-01-01",
            }
        ],
        "purchase_orders": [],
        "payments": [],
    }

    assert MockQBOConnector(fixture).compute_price_history("SUP-X", "salmon filet") == []


def test_qbo_router_all_endpoints_200():
    client = _client()

    for path in (
        "/api/purchasing/qbo/vendors",
        "/api/purchasing/qbo/bills",
        "/api/purchasing/qbo/purchase-orders",
        "/api/purchasing/qbo/payments",
        "/api/purchasing/qbo/status",
        "/api/purchasing/qbo/profile",
    ):
        response = client.get(path)
        assert response.status_code == 200, path


def test_qbo_price_history_endpoint():
    connector = MockQBOConnector()
    supplier = connector.fetch_vendors()[0]
    item_name = _first_item_name(connector, supplier["supplier_id"])

    response = _client().get(
        f"/api/purchasing/qbo/price-history/{supplier['supplier_id']}/{quote(item_name)}"
    )

    assert response.status_code == 200
    assert response.json()


def test_qbo_lead_times_endpoint():
    response = _client().get("/api/purchasing/qbo/lead-times/SUP-001")

    assert response.status_code == 200
    assert response.json()["mean_days"] > 0


def test_qbo_unknown_vendor_graceful():
    response = _client().get("/api/purchasing/qbo/price-history/NONEXISTENT/salmon%20filet")

    assert response.status_code == 200
    assert response.json() == []
