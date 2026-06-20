from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.auto_order_router import create_auto_order_router
from app.services.auto_order import AutoOrderGate


def enabled_gate(**kwargs) -> AutoOrderGate:
    gate = AutoOrderGate(min_verified=0, **kwargs)
    payload = gate.enable("GREEN")
    assert payload["enabled"] is True
    return gate


def test_disabled_by_default():
    gate = AutoOrderGate()

    assert gate.status["enabled"] is False


def test_conservation_red_blocks():
    gate = enabled_gate()

    payload = gate.evaluate("protein", 0.99, "RED", 100)

    assert payload["auto_order"] is False
    assert payload["reason"] == "conservation_not_green"


def test_conservation_green_allows():
    gate = AutoOrderGate()

    payload = gate.enable("GREEN")

    assert payload["enabled"] is True
    assert payload["reason"] == "enabled"


def test_below_threshold_rejected():
    gate = enabled_gate()

    payload = gate.evaluate("protein", 0.80, "GREEN", 100)

    assert payload["auto_order"] is False
    assert payload["reason"] == "below_threshold"


def test_above_threshold_accepted():
    gate = enabled_gate()

    payload = gate.evaluate("protein", 0.95, "GREEN", 100)

    assert payload["auto_order"] is True
    assert payload["reason"] in {"accepted", "spot_check"}


def test_spot_check_rate():
    gate = enabled_gate()

    spot_checks = sum(
        1
        for _ in range(1000)
        if gate.evaluate("produce", 0.95, "GREEN", 100)["spot_check"]
    )

    assert 10 <= spot_checks <= 35


def test_threshold_contracts_on_error():
    gate = AutoOrderGate(initial_threshold=0.90)

    payload = gate.contract_threshold(error_rate=0.05)

    assert payload["changed"] is True
    assert payload["threshold"] > 0.90


def test_threshold_expands_on_accuracy():
    gate = AutoOrderGate(initial_threshold=0.90)

    payload = gate.expand_threshold(accuracy=0.98)

    assert payload["changed"] is True
    assert payload["threshold"] < 0.90


def test_threshold_floor():
    gate = AutoOrderGate(initial_threshold=0.76, min_threshold=0.75)

    first = gate.expand_threshold(accuracy=0.99)
    second = gate.expand_threshold(accuracy=0.99)

    assert first["threshold"] == 0.75
    assert second["threshold"] == 0.75


def test_enable_requires_green():
    app = FastAPI()
    gate = AutoOrderGate()
    app.include_router(create_auto_order_router(gate))
    client = TestClient(app)

    response = client.post("/api/purchasing/auto-order/enable")

    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled"] is False
    assert payload["reason"] == "conservation_not_green"


def test_auto_ordered_source_in_audit():
    gate = enabled_gate()

    payload = gate.evaluate(
        "dairy",
        0.96,
        "GREEN",
        100,
        order_id="ORDER-1",
        decision_id="DEC-1",
    )

    assert payload["auto_order"] is True
    assert gate.audit()[-1]["source"] == "auto_order"


def test_disabled_old_behavior():
    gate = AutoOrderGate()

    payload = gate.evaluate("protein", 1.0, "GREEN", 1000)

    assert payload["auto_order"] is False
    assert payload["reason"] == "disabled"


def test_kitchen_language():
    gate = enabled_gate()
    gate.evaluate("protein", 0.95, "GREEN", 100)

    text = str({"status": gate.status, "audit": gate.audit()})

    assert "auto_approve" not in text
    assert "Vendor" not in text


def test_status_endpoint_200(client):
    response = client.get("/api/purchasing/auto-order/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled"] is False
    assert "threshold" in payload


def test_audit_endpoint_returns_list(client):
    response = client.get("/api/purchasing/auto-order/audit")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_auto_order_per_category_conservation():
    app = FastAPI()
    gate = AutoOrderGate(min_verified=50)
    assert gate.enable("GREEN")["enabled"] is True
    app.include_router(create_auto_order_router(gate, _CategoryState()))
    client = TestClient(app)

    protein = client.post(
        "/api/purchasing/auto-order/evaluate",
        json={"category": "protein", "confidence": 0.95},
    ).json()
    dairy = client.post(
        "/api/purchasing/auto-order/evaluate",
        json={"category": "dairy", "confidence": 0.95},
    ).json()

    assert protein["auto_order"] is True
    assert protein["conservation_status"] == "GREEN"
    assert protein["verified_count"] == 50
    assert protein["conservation_source"] == "category"
    assert dairy["auto_order"] is False
    assert dairy["reason"] == "conservation_not_green"
    assert dairy["conservation_status"] == "RED"
    assert dairy["verified_count"] == 50


def test_auto_order_evaluate_below_min_verified():
    gate = AutoOrderGate(min_verified=50)
    assert gate.enable("GREEN")["enabled"] is True

    payload = gate.evaluate("protein", 0.95, "GREEN", 49)

    assert payload["auto_order"] is False
    assert payload["reason"] == "insufficient_verified_count"


def test_auto_order_threshold_value_in_status():
    gate = AutoOrderGate(initial_threshold=0.91)

    assert gate.status["threshold"] == 0.91


def test_auto_order_audit_has_source():
    gate = enabled_gate()

    payload = gate.evaluate("protein", 0.95, "GREEN", 100)

    assert payload["event"]["source"] == "auto_order"
    assert gate.audit()[-1]["source"] == "auto_order"


class _CategoryStore:
    def get_verified_decisions(self, domain: str) -> list[dict]:
        assert domain == "purchasing"
        return [
            {
                "decision_id": f"PROTEIN-{index}",
                "domain": "purchasing",
                "category": "protein",
                "status": "confirmed",
                "is_correct": index < 10,
            }
            for index in range(50)
        ] + [
            {
                "decision_id": f"DAIRY-{index}",
                "domain": "purchasing",
                "category": "dairy",
                "status": "overridden",
                "is_correct": False,
            }
            for index in range(50)
        ]


class _CategoryState:
    graph_store = _CategoryStore()
