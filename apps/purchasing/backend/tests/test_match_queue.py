from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.routers.match import MATCH_RESULTS, PENDING_EXCEPTIONS, create_match_router, match_to_factor_score
from app.routers.queue import create_queue_router


FACTORS = {
    "expected_demand": 0.8,
    "day_of_week": 0.3,
    "weather_forecast": 0.5,
    "event_flag": 0.0,
    "historical_waste": 0.2,
    "supplier_lead_time": 0.25,
    "price_memory_index": 0.9,
}


class RecordingStore:
    def __init__(self) -> None:
        self.decisions: list[dict[str, Any]] = []

    def write_decision(
        self,
        domain: str,
        category: str,
        action: str,
        confidence: float,
        factors: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        decision = {
            "domain": domain,
            "category": category,
            "action": action,
            "confidence": confidence,
            "factors": dict(factors),
            "metadata": dict(metadata or {}),
        }
        self.decisions.append(decision)
        return str(decision["metadata"].get("decision_id") or "RECORDED")

    def count_verified(self, domain: str) -> int:
        return 4

    def count_correct(self, domain: str) -> int:
        return 3


def _match_payload(
    *,
    order_id: str = "ORD-1",
    ordered_qty: float = 100.0,
    delivered_qty: float = 103.0,
    order_price: float = 10.0,
    invoice_price: float = 10.02,
) -> dict[str, Any]:
    return {
        "order": {
            "order_id": order_id,
            "supplier_id": "SUP-1",
            "category": "protein",
            "item": "salmon",
            "quantity": ordered_qty,
            "unit_price": order_price,
            "factors": FACTORS,
        },
        "delivery": {
            "order_id": order_id,
            "supplier_id": "SUP-1",
            "category": "protein",
            "item": "salmon",
            "quantity": delivered_qty,
            "unit_price": order_price,
        },
        "invoice": {
            "order_id": order_id,
            "supplier_id": "SUP-1",
            "category": "protein",
            "item": "salmon",
            "quantity": delivered_qty,
            "unit_price": invoice_price,
        },
    }


def _client(store: RecordingStore | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(create_match_router(lambda: store if store is not None else RecordingStore()))
    app.include_router(create_queue_router(lambda: store if store is not None else RecordingStore()))
    return TestClient(app)


def test_match_auto_matches_quantity_within_five_percent_and_price_tolerance():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    response = _client().post("/api/purchasing/match", json=_match_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched"] is True
    assert payload["qty_diff"] <= 0.05
    assert payload["exception"] is None


def test_match_quantity_difference_over_five_percent_returns_qty_exception():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    response = _client().post(
        "/api/purchasing/match",
        json=_match_payload(order_id="ORD-QTY", delivered_qty=92.0),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched"] is False
    assert payload["exception"]["reason"] == "qty_variance"
    assert "qty_variance" in payload["exception"]["reasons"]


def test_match_price_beyond_tolerance_returns_price_exception():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    response = _client().post(
        "/api/purchasing/match",
        json=_match_payload(order_id="ORD-PRICE", invoice_price=13.0),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched"] is False
    assert payload["exception"]["reason"] == "price_variance"
    assert "price_variance" in payload["exception"]["reasons"]


def test_match_queue_returns_pending_exceptions():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    client = _client()
    client.post("/api/purchasing/match", json=_match_payload(order_id="ORD-QUEUE", delivered_qty=90.0))

    response = client.get("/api/purchasing/match/queue")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["exceptions"][0]["order_id"] == "ORD-QUEUE"


def test_match_writes_decision_equivalent_to_graph_store():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    store = RecordingStore()
    response = _client(store).post("/api/purchasing/match", json=_match_payload(order_id="ORD-WRITE"))

    assert response.status_code == 200
    assert response.json()["decision_write"]["status"] == "written"
    assert len(store.decisions) == 1
    assert store.decisions[0]["domain"] == "purchasing"
    assert store.decisions[0]["metadata"]["decision_type"] == "delivery_match"


def test_match_score_is_wired_into_graph_write_context():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    store = RecordingStore()
    response = _client(store).post(
        "/api/purchasing/match",
        json=_match_payload(order_id="ORD-MATCH-SCORE", delivered_qty=92.0, invoice_price=12.5),
    )

    assert response.status_code == 200
    match_score = response.json()["match_score"]
    assert match_score == 0.1
    assert len(store.decisions) == 1
    assert store.decisions[0]["factors"]["coverage_depth"] == pytest.approx(match_score)
    assert store.decisions[0]["metadata"]["match_score"] == pytest.approx(match_score)
    assert store.decisions[0]["metadata"]["coverage_depth"] == pytest.approx(match_score)


def test_queue_returns_items_sorted_by_priority_score_descending(client):
    response = client.get("/api/purchasing/queue")

    assert response.status_code == 200
    payload = response.json()
    scores = [item["priority_score"] for item in payload["queue"]]
    assert scores == sorted(scores, reverse=True)
    assert payload["queue"][0]["what_to_order"]
    assert payload["queue"][0]["how_much"] is not None
    assert payload["queue"][0]["from_whom"]


def test_queue_empty_context_returns_empty_queue_without_crashing(monkeypatch):
    from app.routers import queue as queue_router

    monkeypatch.setattr(queue_router, "load_purchasing_orders", lambda: [])
    response = _client().get("/api/purchasing/queue")

    assert response.status_code == 200
    payload = response.json()
    assert payload["queue"] == []
    assert payload["count"] == 0


def test_queue_includes_conservation_status():
    store = RecordingStore()
    response = _client(store).get("/api/purchasing/queue")

    assert response.status_code == 200
    payload = response.json()
    assert payload["conservation_status"]["status"] == "GREEN"
    assert payload["conservation_status"]["verified_count"] == 4


def test_match_and_queue_routes_are_registered_on_main_app(client):
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()

    match_response = client.post(
        "/api/purchasing/match",
        json=_match_payload(order_id="ORD-MAIN"),
    )
    queue_response = client.get("/api/purchasing/queue")
    match_queue_response = client.get("/api/purchasing/match/queue")

    assert match_response.status_code == 200
    assert queue_response.status_code == 200
    assert match_queue_response.status_code == 200


def test_match_returns_confidence():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    response = _client().post("/api/purchasing/match", json=_match_payload(order_id="ORD-CONF"))

    assert response.status_code == 200
    payload = response.json()
    assert "match_confidence" in payload
    assert 0.0 <= payload["match_confidence"] <= 1.0


def test_match_full_match_confidence_1():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    response = _client().post(
        "/api/purchasing/match",
        json=_match_payload(order_id="ORD-FULL", delivered_qty=99.0, invoice_price=10.01),
    )

    assert response.status_code == 200
    assert response.json()["matched"] is True
    assert response.json()["match_confidence"] == 1.0


def test_match_quantity_short_confidence():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    response = _client().post(
        "/api/purchasing/match",
        json=_match_payload(order_id="ORD-SHORT", delivered_qty=92.0, invoice_price=10.0),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched"] is False
    assert payload["match_confidence"] == 0.6


def test_match_price_over_confidence():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    response = _client().post(
        "/api/purchasing/match",
        json=_match_payload(order_id="ORD-OVER", delivered_qty=100.0, invoice_price=12.5),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched"] is False
    assert payload["match_confidence"] == 0.1


def test_match_missing_delivery_confidence():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    payload = _match_payload(order_id="ORD-MISSING")
    payload.pop("delivery")
    response = _client().post("/api/purchasing/match", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["matched"] is False
    assert body["status"] == "MISSING_RECEIPT"
    assert body["match_confidence"] == 0.3


def test_match_discrepancy_messages():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    response = _client().post(
        "/api/purchasing/match",
        json=_match_payload(order_id="ORD-MSG", delivered_qty=85.0, invoice_price=12.0),
    )

    assert response.status_code == 200
    messages = response.json()["discrepancy_messages"]
    assert messages
    assert any("Ordered 100 units, received 85" in message for message in messages)
    assert any("Invoice $12.00/unit vs order $10.00/unit" in message for message in messages)


def test_match_accepts_flat_payload_and_returns_new_fields():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    response = _client().post(
        "/api/purchasing/match",
        json={
            "order_id": "ORD-FLAT",
            "item_name": "Chicken",
            "quantity": 100,
            "unit_price": 10.0,
            "delivery_quantity": 92,
            "invoice_quantity": 100,
            "invoice_unit_price": 12.5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["order_id"] == "ORD-FLAT"
    assert payload["item"] == "Chicken"
    assert payload["match_confidence"] == 0.1
    assert payload["discrepancy_messages"]
    assert any("Ordered 100 units, received 92" in message for message in payload["discrepancy_messages"])
    assert any("Invoice $12.50/unit vs order $10.00/unit" in message for message in payload["discrepancy_messages"])


def test_match_accepts_item_array_payload():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    response = _client().post(
        "/api/purchasing/match",
        json={
            "order": {"items": [{"name": "Chicken", "qty": 100, "unit_price": 10}]},
            "delivery": {"items": [{"name": "Chicken", "qty": 98}]},
            "invoice": {"items": [{"name": "Chicken", "qty": 100, "unit_price": 10.05}]},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["match_confidence"] == 1.0
    assert payload["discrepancy_messages"] == []


def test_match_discrepancy_empty_on_full():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    response = _client().post("/api/purchasing/match", json=_match_payload(order_id="ORD-NO-MSG"))

    assert response.status_code == 200
    assert response.json()["matched"] is True
    assert response.json()["discrepancy_messages"] == []


def test_configurable_tolerances():
    PENDING_EXCEPTIONS.clear()
    MATCH_RESULTS.clear()
    response = _client().post(
        "/api/purchasing/match?qty_tolerance=0.1&price_tolerance=0.05",
        json=_match_payload(order_id="ORD-TOL", delivered_qty=92.0, invoice_price=10.4),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched"] is True
    assert payload["qty_tolerance"] == 0.1
    assert payload["price_tolerance"] == 0.05


def test_match_to_factor_score():
    assert match_to_factor_score({"match_confidence": 0.7}) == 0.7
    assert match_to_factor_score({"match_confidence": 2.0}) == 1.0
    assert match_to_factor_score({"match_confidence": -1.0}) == 0.0
