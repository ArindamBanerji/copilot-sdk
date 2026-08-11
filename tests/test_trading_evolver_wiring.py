from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient


TRADING_BACKEND = Path(__file__).parents[1] / "apps" / "trading" / "backend"
if str(TRADING_BACKEND) not in sys.path:
    sys.path.insert(0, str(TRADING_BACKEND))


def _trading_app():
    """Import Trading after clearing another app package loaded by prior tests."""

    trading_path = str(TRADING_BACKEND.resolve())
    sys.path[:] = [
        path
        for path in sys.path
        if "s2p-copilot" not in path.lower() and path != trading_path
    ]
    sys.path.insert(0, trading_path)
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)
    from app.main import create_app

    return create_app(db_path=":memory:", demo_bundle_path=False)


def test_trading_evolver_has_variants():
    app = _trading_app()
    variants = app.state.trading_evolver.registered_variants
    assert len(variants) == 10
    assert {variant["status"] for variant in variants} == {"active", "shadow"}


def test_trading_conservation_not_literal():
    from pathlib import Path

    path = Path(__file__).parents[1] / "apps" / "trading" / "backend" / "app" / "services" / "trading_evolver.py"
    source = path.read_text(encoding="utf-8")
    assert 'conservation_state="GREEN"' not in source
    assert "conservation_state='GREEN'" not in source


def test_trading_evolution_endpoint():
    app = _trading_app()
    response = TestClient(app).get("/api/trading/evolution/log")
    assert response.status_code == 200
    variants = [item for item in response.json() if item.get("variant_id")]
    assert len(variants) == 10
