from __future__ import annotations

from fastapi.testclient import TestClient
from tests.evolution_contract_helpers import make_contract_app


def test_trading_evolver_has_variants() -> None:
    app = make_contract_app("trading")
    variants = app.state.evolver.store.get_all_variants()
    assert len(variants) == 2
    assert {variant.status for variant in variants} == {"active", "shadow"}


def test_trading_conservation_not_literal() -> None:
    from pathlib import Path

    path = Path(__file__).parents[1] / "apps" / "trading" / "backend" / "app" / "services" / "trading_evolver.py"
    source = path.read_text(encoding="utf-8")
    assert 'conservation_state="GREEN"' not in source
    assert "conservation_state='GREEN'" not in source


def test_trading_evolution_endpoint() -> None:
    app = make_contract_app("trading")
    response = TestClient(app).get("/api/self/evolution/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "trading"
    assert payload["schema_version"] == 1
    assert len(payload["inventory"]["active"]) == 1
    assert len(payload["inventory"]["shadow"]) == 1
