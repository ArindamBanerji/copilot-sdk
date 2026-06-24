from __future__ import annotations

from fastapi.testclient import TestClient

from app.factors.weather_forecast import compute, compute_weather_impact
from app.main import create_app
from copilot_sdk.connectors.mock_weather import MockWeatherConnector


def test_weather_factor_produce_storm():
    assert compute({"weather": "storm", "category": "produce"}) <= 0.2


def test_weather_factor_seafood_storm():
    assert compute({"weather": "storm", "category": "seafood"}) <= 0.2


def test_storm_seafood_high_risk():
    score = compute_weather_impact(
        {"precipitation_mm": 30, "wind_speed_max": 70},
        category="seafood",
    )
    assert score < 0.3


def test_storm_dry_goods_low_risk():
    score = compute_weather_impact(
        {"precipitation_mm": 30, "wind_speed_max": 70},
        category="dry_goods",
    )
    assert score > 0.7


def test_weather_factor_seafood_storm_vs_dry_goods():
    storm = {"precipitation_mm": 30, "wind_speed_max": 70}
    seafood = compute_weather_impact(storm, category="seafood")
    dry_goods = compute_weather_impact(storm, category="dry_goods")
    assert seafood < dry_goods
    assert dry_goods - seafood >= 0.5


def test_weather_factor_heat_dairy():
    assert compute({"condition": "heat", "temperature_f": 94, "category": "dairy"}) == 0.3


def test_weather_factor_no_data():
    assert compute({}) == 0.5


def test_weather_factor_normal():
    assert 0.7 <= compute({"weather": "clear"}) <= 0.9


def test_weather_endpoint():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/context/weather")
    assert response.status_code == 200
    assert "source" in response.json()


def test_mock_connector_7_days():
    rows = MockWeatherConnector().fetch()
    assert len(rows) == 7
    assert any(row["condition"] == "storm" for row in rows)
    assert any(row["condition"] == "heat" for row in rows)
