from __future__ import annotations

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.archetype_router import create_archetype_router
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(create_archetype_router())
    return TestClient(app)


def test_list_archetypes_returns_four_plus_entries() -> None:
    payload = _client().get("/api/archetypes").json()

    assert len(payload) >= 4


def test_list_archetypes_has_required_fields() -> None:
    row = _client().get("/api/archetypes").json()[0]

    assert {"name", "domain", "description"}.issubset(row)


def test_get_archetype_by_name_returns_full_details() -> None:
    payload = _client().get("/api/archetypes/financial_services").json()

    assert payload["name"] == "financial_services"
    assert payload["centroids"]
    assert payload["shape"]


def test_get_unknown_archetype_returns_404() -> None:
    response = _client().get("/api/archetypes/missing")

    assert response.status_code == 404


def test_list_for_domain_trading_filters_correctly() -> None:
    payload = _client().get("/api/archetypes?domain=trading").json()

    assert payload
    assert {row["domain"] for row in payload} == {"trading"}


def test_list_for_domain_unknown_returns_empty_list() -> None:
    assert _client().get("/api/archetypes?domain=unknown").json() == []


def test_archetype_shape_matches_preset() -> None:
    payload = _client().get("/api/archetypes/financial_services").json()

    assert payload["shape"] == list(TradingPreset().shape.tensor_shape)


def test_centroid_values_valid() -> None:
    payload = _client().get("/api/archetypes/financial_services").json()
    values = np.asarray(payload["centroids"], dtype=float)

    assert np.all(values >= 0.0)
    assert np.all(values <= 1.0)


def test_apply_returns_valid_preset() -> None:
    payload = _client().post("/api/archetypes/apply/financial_services").json()

    assert payload["applied"] is True
    assert payload["current"] == "financial_services"
    assert payload["preset"]["centroids"]
    assert payload["preset"]["shape"] == list(TradingPreset().shape.tensor_shape)


def test_apply_unknown_returns_404() -> None:
    response = _client().post("/api/archetypes/apply/missing")

    assert response.status_code == 404


def test_apply_preserves_existing_decisions(tmp_path) -> None:
    store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset("trading", db_path=str(tmp_path / "trading.db"), graph_store=store)
    before = store.count_decisions("trading")

    _client().post("/api/archetypes/apply/financial_services")

    assert store.count_decisions("trading") == before
    assert scorer.get_verified_count() == 0


def test_apply_centroids_differ_from_default() -> None:
    payload = _client().post("/api/archetypes/apply/financial_services").json()
    generated = np.asarray(payload["preset"]["centroids"], dtype=float)
    default = TradingPreset().bootstrap_centroids

    assert generated.shape == default.shape
    assert not np.array_equal(generated, default)


def test_apply_twice_last_wins() -> None:
    client = _client()
    first = client.post("/api/archetypes/apply/financial_services").json()
    second = client.post("/api/archetypes/apply/financial_services").json()

    assert first["archetype"] == "financial_services"
    assert second["archetype"] == "financial_services"
    assert second["applied"] is True


def test_current_archetype_endpoint_tracks_apply() -> None:
    client = _client()

    assert client.get("/api/archetypes/current").json()["current"] == "default"
    client.post("/api/archetypes/apply/financial_services")

    assert client.get("/api/archetypes/current").json()["current"] == "financial_services"


def test_full_flow_list_select_apply_verify() -> None:
    client = _client()

    rows = client.get("/api/archetypes").json()
    name = next(row["name"] for row in rows if row["domain"] == "trading")
    detail = client.get(f"/api/archetypes/{name}").json()
    applied = client.post(f"/api/archetypes/apply/{name}").json()
    current = client.get("/api/archetypes/current").json()

    assert detail["shape"] == list(TradingPreset().shape.tensor_shape)
    assert applied["preset"]["shape"] == detail["shape"]
    assert current["current"] == name
    assert applied["conservation_note"]
