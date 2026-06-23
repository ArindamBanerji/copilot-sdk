from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from apps.purchasing.backend.app.main import create_app
from apps.purchasing.backend.app.services.par_optimizer import ParLevelOptimizer


def _client() -> TestClient:
    return TestClient(create_app(db_path=":memory:", demo_bundle_path=False))


def _orders(
    *,
    item_name: str = "flour",
    category: str = "dry_goods",
    days: int = 60,
    base_quantity: float = 16.0,
    variance: float = 2.0,
    start: date = date(2026, 1, 1),
    unit_price: float = 4.0,
) -> list[dict]:
    orders: list[dict] = []
    for offset in range(days):
        quantity = base_quantity + (variance if offset % 2 == 0 else -variance)
        orders.append(
            {
                "order_id": f"QBO-{offset}",
                "order_date": (start + timedelta(days=offset)).isoformat(),
                "provenance": "scraped_external",
                "items": [
                    {
                        "item_name": item_name,
                        "category": category,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "amount": quantity * unit_price,
                    }
                ],
            }
        )
    return orders


def test_recommend_over_par():
    rec = ParLevelOptimizer().recommend(
        "flour",
        "dry_goods",
        _orders(),
        current_par=40,
        unit_cost=4,
        lead_time_days=2,
    )

    assert 34 <= rec.recommended_par <= 38
    assert rec.current_par == 40


def test_recommend_under_par():
    rec = ParLevelOptimizer().recommend(
        "flour",
        "dry_goods",
        _orders(base_quantity=14, variance=1),
        current_par=20,
        unit_cost=4,
        lead_time_days=2,
    )

    assert rec.recommended_par > rec.current_par
    assert 29 <= rec.recommended_par <= 32


def test_recommend_at_par():
    rec = ParLevelOptimizer().recommend(
        "flour",
        "dry_goods",
        _orders(),
        current_par=36,
        unit_cost=4,
        lead_time_days=2,
    )

    assert abs(rec.recommended_par - rec.current_par) <= 2


def test_service_level_95():
    assert ParLevelOptimizer._z_score(0.95) == pytest.approx(1.645, abs=0.01)


def test_service_level_99():
    assert ParLevelOptimizer._z_score(0.99) == pytest.approx(2.326, abs=0.01)


def test_savings_positive():
    rec = ParLevelOptimizer().recommend(
        "flour",
        "dry_goods",
        _orders(),
        current_par=55,
        unit_cost=4,
        lead_time_days=2,
    )

    assert rec.weekly_savings_estimate > 0


def test_savings_zero():
    rec = ParLevelOptimizer().recommend(
        "flour",
        "dry_goods",
        _orders(),
        current_par=36,
        unit_cost=4,
        lead_time_days=2,
    )

    assert rec.weekly_savings_estimate == 0


def test_low_confidence():
    rec = ParLevelOptimizer().recommend(
        "flour",
        "dry_goods",
        _orders(days=20),
        current_par=40,
        unit_cost=4,
    )

    assert rec.confidence == "low"


def test_moderate_confidence():
    rec = ParLevelOptimizer().recommend(
        "flour",
        "dry_goods",
        _orders(days=45),
        current_par=40,
        unit_cost=4,
    )

    assert rec.confidence == "moderate"


def test_high_confidence():
    rec = ParLevelOptimizer().recommend(
        "flour",
        "dry_goods",
        _orders(days=120),
        current_par=40,
        unit_cost=4,
    )

    assert rec.confidence == "high"


def test_seasonal_produce_summer():
    assert ParLevelOptimizer()._seasonal_multiplier(7, "produce") > 1.0


def test_seasonal_protein_winter():
    assert ParLevelOptimizer()._seasonal_multiplier(1, "protein") > 1.0


def test_seasonal_dry_goods_none():
    assert ParLevelOptimizer()._seasonal_multiplier(7, "dry_goods") == 1.0


def test_recommend_all_sorted():
    optimizer = ParLevelOptimizer()
    orders = _orders(item_name="flour") + _orders(item_name="rice", base_quantity=8, unit_price=8)
    items = [
        {"item_name": "flour", "category": "dry_goods", "current_par": 55, "unit_cost": 4},
        {"item_name": "rice", "category": "dry_goods", "current_par": 45, "unit_cost": 8},
    ]

    recs = optimizer.recommend_all(items, orders)

    assert len(recs) == 2
    assert recs[0].weekly_savings_estimate >= recs[1].weekly_savings_estimate


def test_par_endpoint_200():
    r = _client().get("/api/purchasing/par/recommendations")

    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert r.json() == []


def test_par_category_filter():
    r = _client().get("/api/purchasing/par/recommendations/protein")

    assert r.status_code == 200
    assert all(item["category"] == "protein" for item in r.json())


def test_par_status():
    r = _client().get("/api/purchasing/par/status")

    assert r.status_code == 200
    data = r.json()
    assert data["data_source"] == "quickbooks_online"
    assert data["provenance_tier"] == "sample"


def test_par_uses_qbo_not_fixture():
    r = _client().get("/api/purchasing/par/status")

    assert r.status_code == 200
    assert r.json()["data_source"] == "quickbooks_online"


def test_par_no_sample_in_recommendations():
    r = _client().get("/api/purchasing/par/recommendations")

    assert r.status_code == 200
    assert r.json() == []
    assert all(item.get("provenance") != "sample" for item in r.json())


def test_optimizer_rejects_sample_orders():
    orders = _orders()
    orders[0]["provenance"] = "sample"

    with pytest.raises(ValueError, match="F-26 VIOLATION"):
        ParLevelOptimizer().recommend(
            "flour",
            "dry_goods",
            orders,
            current_par=40,
            unit_cost=4,
        )


def test_savings_labeled_estimate():
    rec = ParLevelOptimizer().recommend(
        "flour",
        "dry_goods",
        _orders(),
        current_par=55,
        unit_cost=4,
    )

    assert hasattr(rec, "weekly_savings_estimate")
