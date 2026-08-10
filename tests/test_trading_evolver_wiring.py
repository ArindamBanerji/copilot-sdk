from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient


TRADING_BACKEND = Path(__file__).parents[1] / "apps" / "trading" / "backend"
if str(TRADING_BACKEND) not in sys.path:
    sys.path.insert(0, str(TRADING_BACKEND))


def test_trading_evolver_has_variants():
    from app.main import create_app

    app = create_app(db_path=":memory:", demo_bundle_path=False)
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
    from app.main import create_app

    app = create_app(db_path=":memory:", demo_bundle_path=False)
    response = TestClient(app).get("/api/trading/evolution/log")
    assert response.status_code == 200
    variants = [item for item in response.json() if item.get("variant_id")]
    assert len(variants) == 10
