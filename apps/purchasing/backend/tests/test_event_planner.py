from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.event_planner import EventPlanner


def test_plan_basic():
    plan = EventPlanner().plan(80)
    assert plan.guest_count == 80
    assert len(plan.categories) == 5


def test_plan_quantities():
    plan = EventPlanner([]).plan(80)
    protein = next(row for row in plan.categories if row["category"] == "protein")
    assert protein["quantity_lbs"] == 36


def test_plan_cuisine_specific():
    mixed = EventPlanner([]).plan(80, "mixed")
    italian = EventPlanner([]).plan(80, "italian")
    mixed_dairy = next(row for row in mixed.categories if row["category"] == "dairy")
    italian_dairy = next(row for row in italian.categories if row["category"] == "dairy")
    assert italian_dairy["quantity_lbs"] > mixed_dairy["quantity_lbs"]


def test_plan_with_history():
    history = [{"guest_count": 80, "planned_lbs": 40, "used_lbs": 50, "waste_pct": 0.06}]
    plan = EventPlanner(history).plan(80)
    protein = next(row for row in plan.categories if row["category"] == "protein")
    assert protein["quantity_lbs"] > 36


def test_plan_no_history():
    assert EventPlanner([]).plan(80).similar_events == 0


def test_waste_from_history():
    history = [{"guest_count": 80, "planned_lbs": 40, "used_lbs": 40, "waste_pct": 0.04}]
    assert EventPlanner(history).plan(80).expected_waste_pct == 0.04


def test_record_outcome():
    planner = EventPlanner([])
    result = planner.record_outcome({"guest_count": 20}, {"protein": 10}, 0.05)
    assert result["recorded"] is True
    assert len(planner.history()) == 1


def test_similar_events_filter():
    history = [{"guest_count": 80}, {"guest_count": 200}]
    assert len(EventPlanner(history).similar_events(80)) == 1


def test_confidence_levels():
    history = [{"guest_count": 80, "waste_pct": 0.08} for _ in range(10)]
    assert EventPlanner(history).plan(80).confidence == "high"


def test_router_plan():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/purchasing/events/plan?guests=80&cuisine=mixed")
    assert response.status_code == 200
    assert response.json()["categories"]


def test_event_planner_resets():
    with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as client:
        client.post("/api/purchasing/events/record", json={"plan": {"guest_count": 20}, "actual_usage": {"protein": 8}, "actual_waste": 0.05})
        assert client.get("/api/purchasing/events/history").json()
        response = client.post("/api/purchasing/demo/reset")
        assert response.status_code == 200
        assert client.get("/api/purchasing/events/history").json() == []


def test_event_history_survives_within_session():
    with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as client:
        client.post("/api/purchasing/events/record", json={"plan": {"guest_count": 30}, "actual_usage": {"produce": 5}, "actual_waste": 0.04})
        history = client.get("/api/purchasing/events/history").json()
        assert len(history) == 1
        assert history[0]["guest_count"] == 30


def test_event_history_cleared_after_reset():
    with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as client:
        client.post("/api/purchasing/events/record", json={"plan": {"guest_count": 40}, "actual_usage": {}, "actual_waste": 0.03})
        client.post("/api/purchasing/demo/reset")
        assert client.get("/api/purchasing/events/history").json() == []
