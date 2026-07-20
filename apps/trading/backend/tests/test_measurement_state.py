from fastapi.testclient import TestClient


def test_trading_measurement_state_has_day_zero_shape(client: TestClient) -> None:
    response = client.get("/api/trading/measurement-state")

    assert response.status_code == 200
    payload = response.json()
    assert {"state", "decisions_verified", "decisions_needed", "accuracy", "iks", "message"} <= payload.keys()


def test_trading_measurement_state_is_a_known_state(client: TestClient) -> None:
    response = client.get("/api/trading/measurement-state")

    assert response.status_code == 200
    assert response.json()["state"] in {"instrument_validated", "accumulating", "measured"}
