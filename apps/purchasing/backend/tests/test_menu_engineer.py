from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.menu_engineer import MenuEngineer


def _items():
    return [
        {"name": "A", "price": 20, "food_cost": 5, "orders": 100},
        {"name": "B", "price": 20, "food_cost": 5, "orders": 10},
        {"name": "C", "price": 20, "food_cost": 15, "orders": 100},
        {"name": "D", "price": 20, "food_cost": 15, "orders": 10},
    ]


def _by_name():
    return {item.name: item for item in MenuEngineer().analyze(_items())}


def test_classify_star():
    assert _by_name()["A"].classification == "star"


def test_classify_puzzle():
    assert _by_name()["B"].classification == "puzzle"


def test_classify_plow():
    assert _by_name()["C"].classification == "plowhorse"


def test_classify_dog():
    assert _by_name()["D"].classification == "dog"


def test_food_cost_pct():
    item = MenuEngineer().analyze([{"name": "Salmon", "price": 25, "food_cost": 8, "orders": 1}])[0]
    assert item.food_cost_pct == 0.32


def test_contribution_margin():
    item = MenuEngineer().analyze([{"name": "Salmon", "price": 25, "food_cost": 8, "orders": 1}])[0]
    assert item.contribution_margin == 17


def test_popularity_median_split():
    assert _by_name()["A"].classification in {"star", "plowhorse"}


def test_recommendations_per_class():
    recommendations = MenuEngineer().recommendations(list(_by_name().values()))
    assert any("Keep promoting" in row for row in recommendations)
    assert any("Consider seasonal removal" in row for row in recommendations)


def test_margin_alert_triggered():
    item = MenuEngineer().analyze([
        {"name": "Salmon", "price": 25, "food_cost": 9, "previous_food_cost_pct": 0.28, "orders": 10}
    ])[0]
    alerts = MenuEngineer().margin_alerts([item], threshold=5)
    assert alerts


def test_margin_alert_none():
    item = MenuEngineer().analyze([
        {"name": "Salmon", "price": 25, "food_cost": 7.5, "previous_food_cost_pct": 0.28, "orders": 10}
    ])[0]
    assert MenuEngineer().margin_alerts([item], threshold=5) == []


def test_router_analysis():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/purchasing/menu/analysis")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)
    assert data["provenance"] == "demo"


def test_router_alerts():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/purchasing/menu/alerts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["alerts"], list)


def test_router_summary():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/purchasing/menu/summary")
    assert response.status_code == 200
    data = response.json()
    assert "stars" in data
    assert "dogs" in data
