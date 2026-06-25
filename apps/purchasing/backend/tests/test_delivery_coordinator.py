from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.delivery_coordinator import DeliveryCoordinator


def test_schedule_basic():
    schedule = DeliveryCoordinator().schedule_day(date(2026, 6, 24))
    assert len(schedule["deliveries"]) == 2


def test_schedule_no_deliveries():
    schedule = DeliveryCoordinator().schedule_day(date(2026, 6, 28))
    assert schedule["deliveries"] == []


def test_supplier_delivery_day():
    schedule = DeliveryCoordinator().schedule_day(date(2026, 6, 23))
    suppliers = {row["supplier"] for row in schedule["deliveries"]}
    assert "Sysco" not in suppliers


def test_consolidation_same_supplier():
    schedule = DeliveryCoordinator().schedule_day(date(2026, 6, 24))
    assert DeliveryCoordinator().suggest_consolidation(schedule)


def test_consolidation_suggestion():
    text = DeliveryCoordinator().suggest_consolidation(DeliveryCoordinator().schedule_day(date(2026, 6, 24)))[0]["text"]
    assert "Save 30 min receiving" in text


def test_receiving_time():
    schedule = DeliveryCoordinator().schedule_day(date(2026, 6, 24))
    assert schedule["receiving_minutes"] == 60


def test_week_schedule():
    week = DeliveryCoordinator().schedule_week(date(2026, 6, 24))
    assert len(week["days"]) == 7


def test_pending_orders_mapped():
    schedule = DeliveryCoordinator().schedule_day(date(2026, 6, 24))
    assert any("protein" in row["items"] for row in schedule["deliveries"])


def test_time_window_no_overlap():
    windows = [row["window"] for row in DeliveryCoordinator().schedule_day(date(2026, 6, 24))["deliveries"]]
    assert len(windows) == len(set(windows))


def test_unknown_supplier():
    schedule = DeliveryCoordinator().schedule_day(date(2026, 6, 24), pending_orders=[{"supplier": "unknown"}])
    assert schedule["unknown_suppliers"]


def test_provenance_demo():
    assert DeliveryCoordinator().schedule_day(date(2026, 6, 24))["provenance"] == "demo"


def test_router_today():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/purchasing/delivery/today")
    assert response.status_code == 200
    assert "deliveries" in response.json()


def test_router_consolidation():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/purchasing/delivery/consolidation")
    assert response.status_code == 200
    assert "suggestions" in response.json()


def test_duplicate_supplier_merges_not_new_window():
    schedule = DeliveryCoordinator().schedule_day(date(2026, 6, 24))
    sysco = [row for row in schedule["deliveries"] if row["supplier_id"] == "sysco"]
    assert len(sysco) == 1
    assert sysco[0]["merged_orders"] == 2


def test_merge_increases_total_amount():
    schedule = DeliveryCoordinator().schedule_day(date(2026, 6, 24))
    sysco = next(row for row in schedule["deliveries"] if row["supplier_id"] == "sysco")
    assert sysco["amount"] == 1660


def test_merge_preserves_supplier_window():
    schedule = DeliveryCoordinator().schedule_day(date(2026, 6, 24))
    sysco = next(row for row in schedule["deliveries"] if row["supplier_id"] == "sysco")
    assert sysco["window"] == "7am-9am"


def test_three_orders_same_supplier_one_slot():
    orders = [
        {"supplier": "sysco", "items": ["protein"], "amount": 100},
        {"supplier": "sysco", "items": ["dry_goods"], "amount": 200},
        {"supplier": "sysco", "items": ["beverages"], "amount": 300},
    ]
    schedule = DeliveryCoordinator().schedule_day(date(2026, 6, 24), pending_orders=orders)
    assert len(schedule["deliveries"]) == 1
    assert schedule["deliveries"][0]["amount"] == 600


def test_different_suppliers_separate_slots():
    orders = [
        {"supplier": "sysco", "items": ["protein"], "amount": 100},
        {"supplier": "dairy_direct", "items": ["dairy"], "amount": 200},
    ]
    schedule = DeliveryCoordinator().schedule_day(date(2026, 6, 24), pending_orders=orders)
    assert len(schedule["deliveries"]) == 2


def test_weekly_consolidation_all_days():
    week = DeliveryCoordinator().schedule_week(date(2026, 6, 22))
    assert week["opportunities"] >= 2


def test_weekly_consolidation_count():
    week = DeliveryCoordinator().schedule_week(date(2026, 6, 22))
    assert week["opportunities"] == 3


def test_weekly_no_consolidation():
    orders = [
        {"supplier": "sysco", "items": ["protein"], "amount": 100},
        {"supplier": "dairy_direct", "items": ["dairy"], "amount": 200},
    ]
    week = DeliveryCoordinator().schedule_week(date(2026, 6, 22), pending_orders=orders)
    assert week["opportunities"] == 0
