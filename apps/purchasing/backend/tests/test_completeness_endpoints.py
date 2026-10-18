from __future__ import annotations

from fastapi.testclient import TestClient


def test_commodity_prices_compatibility_shape_and_unknown_default(
    client: TestClient,
) -> None:
    response = client.get("/api/purchasing/commodity-prices/produce")

    assert response.status_code == 200
    payload = response.json()
    assert {"value", "source", "label", "as_of"}.issubset(payload)
    assert payload["value"]
    assert {"date", "item", "price", "unit"}.issubset(payload["value"][0])

    unknown = client.get("/api/purchasing/commodity-prices/unknown")
    assert unknown.status_code == 200
    assert unknown.json()["value"] == []


def test_par_recommendations_compatibility_shape_and_unknown_default(
    client: TestClient,
) -> None:
    response = client.get("/api/purchasing/par-recommendations")

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert {
        "item_name",
        "category",
        "current_par",
        "recommended_par",
        "avg_daily_usage",
        "usage_std",
        "waste_rate",
        "service_level",
        "weekly_savings_estimate",
        "confidence",
        "seasonal_adjustment",
        "data_days",
        "provenance",
    }.issubset(payload[0])

    unknown = client.get(
        "/api/purchasing/par-recommendations", params={"category": "unknown"}
    )
    assert unknown.status_code == 200
    assert unknown.json() == []


def test_supplier_scorecard_compatibility_shape_and_unknown_default(
    client: TestClient,
) -> None:
    required = {
        "supplier_id",
        "supplier_name",
        "tier",
        "overall_score",
        "reliability_pct",
        "price_trend_pct",
        "delivery_performance",
        "exception_rate",
        "decision_count",
        "trend",
        "summary",
        "provenance",
    }
    response = client.get("/api/purchasing/supplier-scorecard/SUP-001")

    assert response.status_code == 200
    assert required.issubset(response.json())

    unknown = client.get("/api/purchasing/supplier-scorecard/UNKNOWN")
    assert unknown.status_code == 200
    assert required.issubset(unknown.json())
    assert unknown.json()["decision_count"] == 0
