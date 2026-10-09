"""Real Trading app evolver wiring checks requiring AGE."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from copilot_sdk.testing.fixtures import requires_age


TRADING_BACKEND = Path(__file__).parents[1] / "apps" / "trading" / "backend"


@pytest.fixture(autouse=True)
def _isolate_app_imports():
    original_path = list(sys.path)
    yield
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)
    sys.path[:] = original_path


def _trading_app():
    """Import Trading after clearing another app package loaded by prior tests."""
    trading_path = str(TRADING_BACKEND.resolve())
    sys.path[:] = [
        path for path in sys.path
        if "s2p-copilot" not in path.lower() and path != trading_path
    ]
    sys.path.insert(0, trading_path)
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)
    from app.main import create_app

    return create_app(db_path=":memory:", demo_bundle_path=False)


@requires_age
def test_trading_evolver_has_variants() -> None:
    app = _trading_app()
    variants = app.state.trading_evolver.registered_variants
    assert len(variants) == 10
    assert {variant["status"] for variant in variants} == {"active", "shadow"}


@requires_age
def test_trading_evolution_endpoint() -> None:
    app = _trading_app()
    response = TestClient(app).get("/api/trading/evolution/log")
    assert response.status_code == 200
    variants = [item for item in response.json() if item.get("variant_id")]
    assert len(variants) == 10
