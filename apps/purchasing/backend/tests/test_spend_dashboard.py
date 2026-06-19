from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.routers.spend_router import create_spend_router
from app.services.spend_dashboard import SpendDashboardService


def sample_orders() -> list[dict]:
    return [
        {
            "order_id": "O-1",
            "order_date": "2025-01-01",
            "category": "protein",
            "supplier_id": "SUP-1",
            "supplier_name": "Harbor Prime",
            "total_value": 100.0,
            "covers": 25,
            "items": [{"name": "salmon", "quantity": 10, "unit_price": 10.0}],
        },
        {
            "order_id": "O-2",
            "order_date": "2025-01-25",
            "category": "produce",
            "supplier_id": "SUP-2",
            "supplier_name": "Valley Fresh",
            "total_value": 300.0,
            "covers": 50,
            "items": [{"name": "romaine", "quantity": 20, "unit_price": 15.0}],
        },
        {
            "order_id": "O-3",
            "order_date": "2025-01-30",
            "category": "protein",
            "supplier_id": "SUP-1",
            "supplier_name": "Harbor Prime",
            "total_value": 600.0,
            "covers": 75,
            "items": [{"name": "salmon", "quantity": 20, "unit_price": 30.0}],
        },
    ]


def test_summary_total_positive():
    payload = SpendDashboardService(sample_orders()).summary(days=30)

    assert payload["total_spend"] > 0
    assert payload["avg_order_amount"] > 0


def test_summary_order_count():
    payload = SpendDashboardService(sample_orders()).summary(days=7)

    assert payload["order_count"] == 2


def test_by_category_5():
    rows = SpendDashboardService(sample_orders()).by_category(days=30)

    assert len(rows) == 5
    assert {row["category"] for row in rows} == {"protein", "produce", "dairy", "dry_goods", "beverages"}


def test_by_category_pct_sum():
    rows = SpendDashboardService(sample_orders()).by_category(days=30)

    assert sum(row["pct_of_total"] for row in rows) == pytest.approx(100.0)


def test_by_supplier_top10():
    rows = SpendDashboardService(sample_orders()).by_supplier(days=30, limit=10)

    assert len(rows) <= 10
    assert [row["total_amount"] for row in rows] == sorted(
        [row["total_amount"] for row in rows],
        reverse=True,
    )


def test_price_alerts_threshold():
    alerts = SpendDashboardService(sample_orders()).price_alerts(threshold_pct=10)

    assert alerts
    assert alerts[0]["item_name"] == "salmon"
    assert alerts[0]["variance_pct"] > 10


def test_price_alerts_empty():
    alerts = SpendDashboardService(sample_orders()).price_alerts(threshold_pct=500)

    assert alerts == []


def test_cost_per_cover():
    rows = SpendDashboardService(sample_orders()).cost_per_cover_trend(days=30)
    latest = next(row for row in rows if row["date"] == "2025-01-30")

    assert latest["cost_per_cover"] == pytest.approx(8.0)


def test_cost_per_cover_no_covers():
    orders = [{**row, "covers": None} for row in sample_orders()]
    rows = SpendDashboardService(orders).cost_per_cover_trend(days=30)

    assert rows
    assert all(row["cost_per_cover"] is None for row in rows)


def test_period_windowing():
    service = SpendDashboardService(sample_orders())

    assert service.summary(days=7)["total_spend"] < service.summary(days=30)["total_spend"]


def test_empty_orders():
    service = SpendDashboardService([])

    assert service.summary()["total_spend"] == 0
    assert service.summary()["order_count"] == 0
    assert service.by_supplier() == []
    assert service.price_alerts() == []
    assert service.cost_per_cover_trend() == []


def test_summary_endpoint_200(client):
    response = client.get("/api/purchasing/spend/summary")

    assert response.status_code == 200
    assert "total_spend" in response.json()


def test_router_with_custom_orders():
    app = FastAPI()
    app.include_router(create_spend_router(sample_orders()))
    client = TestClient(app)

    response = client.get("/api/purchasing/spend/by-category")

    assert response.status_code == 200
    assert len(response.json()) == 5
