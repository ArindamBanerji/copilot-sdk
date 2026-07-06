from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.scoring.presets.purchasing import PurchasingPreset

from app.routers.iks import create_iks_router
from app.routers.trust import DISPLAY_NAMES, EXPECTED_WEIGHT, create_trust_router


class Store:
    def __init__(self, decisions: list[dict[str, Any]] | None = None) -> None:
        self._decisions = list(decisions or [])

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        return list(self._decisions)


class Scorer:
    def __init__(self, weights: list[list[float]] | None) -> None:
        self._weights = weights

    def get_dk_weights(self) -> list[list[float]] | None:
        return self._weights


def _client(
    *,
    decisions: list[dict[str, Any]] | None = None,
    weights: list[list[float]] | None = None,
) -> TestClient:
    app = FastAPI()
    app.include_router(create_iks_router(lambda: Store(decisions)))
    app.include_router(create_trust_router(Scorer(weights)))
    return TestClient(app)


def _decision(
    decision_id: str,
    category: str = "protein",
    supplier_id: str = "SUP-1",
    invoice_price: float = 10.0,
    otif: bool = True,
    exception: bool = False,
) -> dict[str, Any]:
    return {
        "decision_id": decision_id,
        "category": category,
        "created_at": float(len(decision_id)),
        "is_correct": True,
        "metadata": {
            "supplier_id": supplier_id,
            "invoice_price": invoice_price,
            "otif": otif,
            "exception": exception,
        },
    }


def test_iks_returns_float_and_per_category_dict():
    response = _client(decisions=[_decision("d-1")]).get("/api/purchasing/iks")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["iks"], float)
    assert set(payload["per_category"]) == {"protein", "produce", "dairy", "dry_goods", "beverages"}


def test_iks_no_verified_decisions_returns_zero_without_crash():
    response = _client(decisions=[]).get("/api/purchasing/iks")

    assert response.status_code == 200
    payload = response.json()
    assert payload["iks"] == 0.0
    assert payload["available"] is False


def test_supplier_scorecard_returns_graph_otif_exception_and_price_memory():
    decisions = [
        _decision("d-1", supplier_id="SUP-1", invoice_price=11.0),
        _decision("d-2", supplier_id="SUP-1", invoice_price=12.0, otif=False, exception=True),
    ]

    response = _client(decisions=decisions).get("/api/purchasing/suppliers/SUP-1/scorecard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["supplier_id"] == "SUP-1"
    assert payload["otif_rate"] == 0.5
    assert payload["exception_rate"] == 0.5
    assert payload["price_memory"][-1]["price"] == 12.0
    assert payload["source"] == "graphstore"


def test_supplier_scorecard_unknown_returns_404_without_crash():
    response = _client(decisions=[]).get("/api/purchasing/suppliers/UNKNOWN/scorecard")

    assert response.status_code == 404


def test_trust_returns_all_display_names_and_no_code_names():
    response = _client(weights=[[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]]).get("/api/purchasing/trust")

    assert response.status_code == 200
    payload = response.json()
    names = [row["display_name"] for row in payload["factors"]]
    canonical_names = list(PurchasingPreset().shape.factor_names)
    assert names == [DISPLAY_NAMES[name] for name in canonical_names]
    assert not any("expected_demand" in str(row) for row in payload["factors"])


def test_trust_labels_follow_canonical_factor_order():
    response = _client(weights=[[0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]]).get("/api/purchasing/trust")

    assert response.status_code == 200
    factors = response.json()["factors"]
    canonical_names = list(PurchasingPreset().shape.factor_names)
    assert [row["display_name"] for row in factors] == [DISPLAY_NAMES[name] for name in canonical_names]
    assert factors[-1]["display_name"] == "What They Used to Charge"
    assert factors[-1]["actual_weight"] == 0.1 / 2.8


def test_trust_sets_trust_trap_when_actual_weight_below_half_expected():
    response = _client(weights=[[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.01]]).get("/api/purchasing/trust")

    assert response.status_code == 200
    charge_row = next(row for row in response.json()["factors"] if row["display_name"] == "What They Used to Charge")
    assert charge_row["actual_weight"] < EXPECTED_WEIGHT * 0.5
    assert charge_row["trust_trap"] is True


def test_trust_with_dk_weights_unavailable_returns_available_false():
    response = _client(weights=None).get("/api/purchasing/trust")

    assert response.status_code == 200
    payload = response.json()
    assert payload["available"] is False
    assert all("actual_weight" not in row for row in payload["factors"])
    assert all("trust_trap" not in row for row in payload["factors"])


def test_trust_response_json_does_not_contain_price_memory_index():
    response = _client(weights=[[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.01]]).get("/api/purchasing/trust")

    assert response.status_code == 200
    assert "price_memory_index" not in response.text


def test_iks_and_trust_routes_are_registered_on_main_app(client):
    iks_response = client.get("/api/purchasing/iks")
    trust_response = client.get("/api/purchasing/trust")

    assert iks_response.status_code == 200
    assert trust_response.status_code == 200
