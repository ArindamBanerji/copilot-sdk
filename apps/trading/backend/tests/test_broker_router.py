from __future__ import annotations

import math

from app.brokers import BrokerError, MockBroker


def _clear_alpaca_env(monkeypatch) -> None:
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)


def _assert_json_safe(value):
    if isinstance(value, dict):
        for item in value.values():
            _assert_json_safe(item)
    elif isinstance(value, list):
        for item in value:
            _assert_json_safe(item)
    elif isinstance(value, float):
        assert math.isfinite(value)
    else:
        assert value is None or isinstance(value, (str, int, bool))


def test_broker_status_returns_200_without_env(client, monkeypatch):
    _clear_alpaca_env(monkeypatch)

    response = client.get("/api/broker/status")

    assert response.status_code == 200
    payload = response.json()
    _assert_json_safe(payload)
    assert payload["broker"] == "alpaca"
    assert payload["connected"] is False
    assert payload["status"] == "disconnected"


def test_broker_account_returns_json_without_env(client, monkeypatch):
    _clear_alpaca_env(monkeypatch)

    response = client.get("/api/broker/account")

    assert response.status_code == 200
    payload = response.json()
    _assert_json_safe(payload)
    assert payload["connected"] is False
    assert payload["account"] is None
    assert "Alpaca credentials are not configured" in payload["error"]


def test_broker_positions_returns_json_without_env(client, monkeypatch):
    _clear_alpaca_env(monkeypatch)

    response = client.get("/api/broker/positions")

    assert response.status_code == 200
    payload = response.json()
    _assert_json_safe(payload)
    assert payload["connected"] is False
    assert payload["positions"] == []


def test_broker_orders_returns_json_without_env(client, monkeypatch):
    _clear_alpaca_env(monkeypatch)

    response = client.get("/api/broker/orders")

    assert response.status_code == 200
    payload = response.json()
    _assert_json_safe(payload)
    assert payload["connected"] is False
    assert payload["orders"] == []


def test_broker_sync_returns_unsupported_without_env(client, monkeypatch):
    _clear_alpaca_env(monkeypatch)

    response = client.post("/api/broker/sync")

    assert response.status_code == 200
    payload = response.json()
    _assert_json_safe(payload)
    assert payload["status"] == "unsupported"
    assert payload["sync"]["supported"] is False


def test_broker_unknown_connector_instantiation_failure_is_json(client):
    response = client.get("/api/broker/status", params={"broker": "unknown"})

    assert response.status_code == 200
    payload = response.json()
    _assert_json_safe(payload)
    assert payload["connected"] is False
    assert payload["status"] == "disconnected"
    assert "Unsupported broker" in payload["error"]


def test_broker_account_method_failure_returns_error_json(client, monkeypatch):
    def fail(self):
        raise BrokerError("account unavailable")

    monkeypatch.setattr(MockBroker, "get_account", fail)

    response = client.get("/api/broker/account", params={"broker": "mock"})

    assert response.status_code == 200
    payload = response.json()
    _assert_json_safe(payload)
    assert payload["status"] == "error"
    assert payload["account"] is None
    assert payload["error"] == "account unavailable"


def test_broker_positions_method_failure_returns_error_json(client, monkeypatch):
    def fail(self):
        raise BrokerError("positions unavailable")

    monkeypatch.setattr(MockBroker, "get_positions", fail)

    response = client.get("/api/broker/positions", params={"broker": "mock"})

    assert response.status_code == 200
    payload = response.json()
    _assert_json_safe(payload)
    assert payload["status"] == "error"
    assert payload["positions"] == []
    assert payload["error"] == "positions unavailable"


def test_broker_orders_method_failure_returns_error_json(client, monkeypatch):
    def fail(self, status=None, limit=50):
        raise BrokerError("orders unavailable")

    monkeypatch.setattr(MockBroker, "get_orders", fail)

    response = client.get("/api/broker/orders", params={"broker": "mock"})

    assert response.status_code == 200
    payload = response.json()
    _assert_json_safe(payload)
    assert payload["status"] == "error"
    assert payload["orders"] == []
    assert payload["error"] == "orders unavailable"


def test_broker_status_identifies_mock_connector(client):
    response = client.get("/api/broker/status", params={"broker": "mock"})

    assert response.status_code == 200
    payload = response.json()
    _assert_json_safe(payload)
    assert payload["broker"] == "mock"
    assert payload["connected"] is True
    assert payload["status"] == "connected"
    assert payload["connector"] == "MockBroker"


def test_broker_router_is_mounted_under_api_broker(client):
    paths = {route.path for route in client.app.routes}

    assert "/api/broker/status" in paths
    assert "/api/broker/account" in paths
    assert "/api/broker/positions" in paths
    assert "/api/broker/orders" in paths
    assert "/api/broker/sync" in paths


def test_broker_order_placement_endpoints_are_absent(client):
    assert client.post("/api/broker/order").status_code == 404
    assert client.post("/api/broker/orders/place").status_code in {404, 405}


def test_broker_mock_happy_path_returns_account_positions_orders_shapes(client):
    account = client.get("/api/broker/account", params={"broker": "mock"})
    positions = client.get("/api/broker/positions", params={"broker": "mock"})
    orders = client.get("/api/broker/orders", params={"broker": "mock"})

    assert account.status_code == 200
    assert positions.status_code == 200
    assert orders.status_code == 200
    account_payload = account.json()
    positions_payload = positions.json()
    orders_payload = orders.json()
    _assert_json_safe(account_payload)
    _assert_json_safe(positions_payload)
    _assert_json_safe(orders_payload)
    assert account_payload["connected"] is True
    assert set(account_payload["account"]) == {"cash", "equity", "buying_power"}
    assert positions_payload["positions"] == []
    assert positions_payload["count"] == 0
    assert orders_payload["orders"] == []
    assert orders_payload["count"] == 0
