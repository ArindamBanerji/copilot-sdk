from __future__ import annotations


def test_trading_evolution_variants_returns_200(client):
    response = client.get("/api/evolution/variants")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "trading"
    assert payload["variants"] == []
    assert payload["active_rules"] == []
    assert payload["promoted_rules"] == []


def test_trading_evolution_history_returns_200(client):
    response = client.get("/api/evolution/history")

    assert response.status_code == 200
    payload = response.json()
    assert payload == {"domain": "trading", "events": [], "count": 0}


def test_trading_evolution_promoted_returns_200(client):
    response = client.get("/api/evolution/promoted")

    assert response.status_code == 200
    payload = response.json()
    assert payload == {"domain": "trading", "promoted": []}
