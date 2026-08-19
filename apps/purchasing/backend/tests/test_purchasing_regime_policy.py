"""Purchasing integration checks for the shared regime policy."""

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.routers.regime_router import create_regime_router


def test_purchasing_situation_endpoint_returns_conditioned_state() -> None:
    app = FastAPI()
    app.include_router(create_regime_router(lambda: None))
    client = TestClient(app)
    response = client.get("/api/purchasing/situation", params={"stock_days": 3})
    assert response.status_code == 200
    payload = response.json()
    assert payload["regime"] == "shortage"
    assert payload["conditioned_context"]["regime"] == "shortage"
    assert payload["observation_only"] is True
