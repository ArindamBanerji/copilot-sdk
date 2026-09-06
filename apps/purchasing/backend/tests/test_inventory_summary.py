from __future__ import annotations

import json
from pathlib import Path

from app import inventory_router


def test_inventory_summary_returns_catalog_and_contract_fields(client) -> None:
    response = client.get("/api/inventory/summary")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 20
    assert payload["categories"] == ["protein", "produce", "dairy", "dry_goods", "beverages"]
    assert payload["variants"]
    required = {
        "item_id",
        "name",
        "display_name",
        "category",
        "unit",
        "par_level",
        "usage_range",
        "supplier",
        "supplier_lead_time",
        "unit_price",
        "event_sensitivity",
        "waste_history",
        "waste_average_pct",
        "waste_trend",
        "variant_count",
    }
    assert required <= set(payload["items"][0])


def test_inventory_summary_reports_waste_aggregate_and_trend(client) -> None:
    response = client.get("/api/inventory/summary")

    assert response.status_code == 200
    chicken = next(item for item in response.json()["items"] if item["name"] == "chicken_breast")
    values = chicken["waste_history"]["waste_pct"]
    assert chicken["waste_average_pct"] == sum(values) / len(values)
    assert chicken["waste_trend"] in {"up", "down", "flat", "unknown"}


def test_inventory_summary_empty_waste_history_is_unknown(client, tmp_path: Path, monkeypatch) -> None:
    empty_history = tmp_path / "waste_history.json"
    empty_history.write_text(json.dumps({}), encoding="utf-8")
    monkeypatch.setattr(inventory_router, "_WASTE_HISTORY_PATH", empty_history)

    response = client.get("/api/inventory/summary")

    assert response.status_code == 200
    assert all(item["waste_average_pct"] == 0.0 for item in response.json()["items"])
    assert all(item["waste_trend"] == "unknown" for item in response.json()["items"])


def test_inventory_summary_stays_within_payload_budget(client) -> None:
    response = client.get("/api/inventory/summary")

    assert response.status_code == 200
    assert len(response.content) < 10_000
