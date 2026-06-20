from __future__ import annotations

from datetime import date, timedelta

import pytest

from apps.purchasing.backend.app.services.supplier_scorecard import SupplierScorecardService


def _vendor(supplier_id: str = "SUP-1", name: str = "Sysco Valley") -> dict:
    return {
        "supplier_id": supplier_id,
        "supplier_name": name,
        "primary_category": "protein",
        "provenance": "scraped_external",
    }


def _orders(
    supplier_id: str = "SUP-1",
    *,
    count: int = 20,
    supplier_name: str = "Sysco Valley",
    late_every: int | None = None,
    start_price: float = 10.0,
    price_step: float = 0.05,
) -> list[dict]:
    start = date(2026, 1, 1)
    rows = []
    for idx in range(count):
        order_date = start + timedelta(days=idx * 2)
        expected = order_date + timedelta(days=2)
        late = late_every is not None and late_every > 0 and idx % late_every == 0
        invoice_date = expected + timedelta(days=2 if late else 0)
        unit_price = start_price + price_step * idx
        rows.append(
            {
                "order_id": f"ORD-{idx:04d}",
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
                "purchase_order_date": order_date.isoformat(),
                "expected_delivery_date": expected.isoformat(),
                "invoice_date": invoice_date.isoformat(),
                "order_date": invoice_date.isoformat(),
                "amount": unit_price * 10,
                "provenance": "scraped_external",
                "items": [
                    {
                        "item_name": "chicken breast",
                        "category": "protein",
                        "quantity": 10,
                        "unit_price": unit_price,
                        "amount": unit_price * 10,
                    }
                ],
            }
        )
    return rows


def _decision(
    supplier_id: str = "SUP-1",
    *,
    is_correct: bool = True,
    recommended: str = "approve_order",
    actual: str = "approve_order",
) -> dict:
    return {
        "supplier_id": supplier_id,
        "recommended_action": recommended,
        "actual_action": actual,
        "is_correct": is_correct,
        "metadata": {"supplier_id": supplier_id},
    }


def test_iks_in_health(client):
    r = client.get("/api/health")

    assert r.status_code == 200
    assert "iks_score" in r.json()


def test_iks_bounded(client):
    r = client.get("/api/health")

    assert r.status_code == 200
    assert 0 <= r.json()["iks_score"] <= 100


def test_iks_summary_endpoint(client):
    r = client.get("/api/purchasing/iks/summary")

    assert r.status_code == 200
    data = r.json()
    assert "iks_score" in data
    assert "per_category" in data
    assert data["substantiation_tier"] == "real_measured"


def test_scorecard_basic():
    service = SupplierScorecardService(
        _orders(count=20),
        [_vendor()],
        [_decision(), _decision(is_correct=False)],
    )

    card = service.build_scorecard("SUP-1")

    assert card is not None
    assert card.supplier_name == "Sysco Valley"
    assert 0 <= card.overall_score <= 100
    assert card.provenance == "scraped_external"


def test_scorecard_tier_a():
    service = SupplierScorecardService(_orders(price_step=0.0), [_vendor()])

    assert service._compute_tier(91) == "A"


def test_scorecard_tier_b():
    service = SupplierScorecardService(_orders(price_step=0.0), [_vendor()])

    assert service._compute_tier(75) == "B"


def test_scorecard_tier_c():
    service = SupplierScorecardService(_orders(price_step=0.0), [_vendor()])

    assert service._compute_tier(60) == "C"


def test_scorecard_insufficient():
    service = SupplierScorecardService(_orders(count=4), [_vendor()])

    assert service.build_scorecard("SUP-1") is None


def test_all_scorecards_sorted():
    orders = _orders("SUP-1", count=10, price_step=0.0) + _orders(
        "SUP-2",
        count=10,
        supplier_name="Late Foods",
        late_every=2,
        price_step=0.8,
    )
    vendors = [_vendor("SUP-1", "Sysco Valley"), _vendor("SUP-2", "Late Foods")]
    service = SupplierScorecardService(orders, vendors)

    cards = service.build_all()

    assert len(cards) == 2
    assert cards[0].overall_score >= cards[1].overall_score


def test_summary_kitchen_language():
    service = SupplierScorecardService(_orders(count=20), [_vendor()])
    card = service.build_scorecard("SUP-1")

    assert card is not None
    assert "on-time" in card.summary
    assert "OTIF" not in card.summary
    assert "PO" not in card.summary


def test_trend_detection():
    improving = SupplierScorecardService(_orders(count=20, price_step=-0.02), [_vendor()])
    declining = SupplierScorecardService(
        _orders(count=20, late_every=2, price_step=1.0),
        [_vendor()],
        [_decision(is_correct=False) for _ in range(5)],
    )

    assert improving.build_scorecard("SUP-1").trend == "improving"
    assert declining.build_scorecard("SUP-1").trend == "declining"


def test_scorecard_endpoint_200(client):
    r = client.get("/api/purchasing/supplier/SUP-001/scorecard")

    assert r.status_code == 200
    assert r.json()["supplier_id"] == "SUP-001"


def test_all_scorecards_endpoint_200(client):
    r = client.get("/api/purchasing/suppliers/scorecards")

    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) > 0


def test_scorecard_uses_qbo(client):
    r = client.get("/api/purchasing/suppliers/scorecards")

    assert r.status_code == 200
    assert all(row["provenance"] == "scraped_external" for row in r.json())


def test_scorecard_no_sample():
    orders = _orders()
    orders[0]["provenance"] = "sample"

    with pytest.raises(ValueError, match="F-26 VIOLATION"):
        SupplierScorecardService(orders, [_vendor()])
