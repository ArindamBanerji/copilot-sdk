from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.multi_unit import MultiUnitManager, demo_locations


def test_dashboard_3_locations():
    data = MultiUnitManager().dashboard(demo_locations())
    assert len(data.locations) == 3


def test_weighted_accuracy():
    data = MultiUnitManager().dashboard(demo_locations())
    improved = demo_locations()
    improved[1]["accuracy"] = 0.90
    improved_data = MultiUnitManager().dashboard(improved)

    assert data.weighted_accuracy > 0.75
    assert improved_data.weighted_accuracy > data.weighted_accuracy


def test_best_worst():
    data = MultiUnitManager().dashboard(demo_locations())
    assert data.best_location == "Chicago"
    assert data.needs_help_location == "Miami"


def test_transfer_found():
    opportunities = MultiUnitManager().find_transfer_opportunities(demo_locations())
    assert any(row["source"] == "Chicago" and row["target"] == "Miami" for row in opportunities)


def test_transfer_eligible():
    opportunity = MultiUnitManager().find_transfer_opportunities(demo_locations())[0]
    assert opportunity["estimated_accuracy"] >= 0.70


def test_transfer_not_eligible():
    locations = demo_locations()
    locations[0]["conservation"] = "RED"
    assert MultiUnitManager().find_transfer_opportunities(locations) == []


def test_purchasing_power():
    data = MultiUnitManager().group_purchasing_power(demo_locations())
    assert data["supplier"] == "Sysco"
    assert data["monthly_spend"] == 45000


def test_volume_discount_callout():
    data = MultiUnitManager().group_purchasing_power(demo_locations())
    assert "$45,000/month" in data["callout"]
    assert "$50K" in data["callout"]


def test_single_location():
    data = MultiUnitManager().dashboard([demo_locations()[0]])
    assert data.best_location == "Chicago"
    assert data.needs_help_location == "Chicago"


def test_compare_sorted():
    rows = MultiUnitManager().compare(demo_locations(), metric="accuracy")
    assert rows[0]["name"] == "Chicago"


def test_cross_location_price():
    result = MultiUnitManager().cross_location_price(demo_locations(), item="salmon")
    assert result["price_spread_pct"] > 0
    assert "cheaper" in result["recommendation"].lower()


def test_cross_location_waste():
    result = MultiUnitManager().cross_location_waste(demo_locations())
    assert result["waste_spread_pct"] > 0
    assert "adopt" in result["recommendation"].lower()


def test_cross_location_supplier_perf():
    result = MultiUnitManager().cross_location_supplier(demo_locations(), supplier="Sysco")
    assert result["otif_spread_pct"] > 0
    assert "receiving process" in result["recommendation"]


def test_cross_location_price_behavioral():
    result = MultiUnitManager().cross_location_price(demo_locations(), item="salmon")
    assert result["high_location"] == "Miami"
    assert "supplier pricing" in result["recommendation"]


def test_cross_location_waste_behavioral():
    result = MultiUnitManager().cross_location_waste(demo_locations())
    assert result["best_location"] == "Chicago"
    assert result["needs_help_location"] == "Miami"


def test_router_dashboard():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/purchasing/multi-unit/dashboard")
    assert response.status_code == 200
    assert len(response.json()["locations"]) == 3


def test_router_transfer_opportunities():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/purchasing/multi-unit/transfer-opportunities")
    assert response.status_code == 200
    assert isinstance(response.json()["opportunities"], list)
    assert response.json()["opportunities"][0]["source"] == "Chicago"
