from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.trust_router import FACTOR_LABELS, LEARNING_THRESHOLD, create_trust_router
from copilot_sdk.scoring.scorer import CompoundingScorer


def _scorer(tmp_path, *, verified_count: int = 0, load_weights: bool = False) -> CompoundingScorer:
    db_path = os.path.join(str(tmp_path), "trust.db")
    scorer = CompoundingScorer.from_preset("purchasing", db_path=db_path)
    shape = scorer._preset.shape
    factors = {name: 0.6 for name in shape.factor_names}
    categories = list(shape.category_names)
    for index in range(verified_count):
        result = scorer.score(category=categories[index % len(categories)], factors=factors)
        learn_result = scorer.learn(result.decision_id, result.action)
        if isinstance(learn_result, dict):
            raise AssertionError(f"learn paused unexpectedly: {learn_result}")
    if load_weights:
        weights = [
            [0.45, 0.35, 0.92, 0.30, 0.68, 0.58, 0.74],
            [0.60, 0.30, 0.40, 0.80, 0.78, 0.42, 0.50],
            [0.50, 0.62, 0.44, 0.38, 0.90, 0.56, 0.66],
            [0.76, 0.48, 0.36, 0.40, 0.55, 0.82, 0.60],
            [0.42, 0.40, 0.50, 0.74, 0.52, 0.46, 0.88],
        ]
        assert scorer.load_dk_weights_from_l5(weights) is True
    return scorer


def _client(scorer: CompoundingScorer) -> TestClient:
    app = FastAPI()
    app.include_router(create_trust_router(lambda: scorer))
    return TestClient(app)


def test_trust_weights_endpoint(tmp_path):
    response = _client(_scorer(tmp_path)).get("/api/purchasing/trust-weights")

    assert response.status_code == 200
    assert "phase" in response.json()


def test_trust_weights_pre_transition(tmp_path):
    response = _client(_scorer(tmp_path, verified_count=5)).get("/api/purchasing/trust-weights")

    payload = response.json()
    assert payload["phase"] == "learning"
    assert payload["weights"] is None
    assert payload["decisions_needed"] == LEARNING_THRESHOLD - 5


def test_trust_weights_post_transition(tmp_path):
    response = _client(
        _scorer(tmp_path, verified_count=LEARNING_THRESHOLD, load_weights=True)
    ).get("/api/purchasing/trust-weights")

    payload = response.json()
    assert payload["phase"] == "active"
    assert payload["weights"]


def test_trust_all_categories(tmp_path):
    payload = _client(
        _scorer(tmp_path, verified_count=LEARNING_THRESHOLD, load_weights=True)
    ).get("/api/purchasing/trust-weights").json()

    assert set(payload["weights"]) == {"protein", "produce", "dairy", "dry_goods", "beverages"}


def test_trust_all_factors(tmp_path):
    payload = _client(
        _scorer(tmp_path, verified_count=LEARNING_THRESHOLD, load_weights=True)
    ).get("/api/purchasing/trust-weights").json()

    assert all(len(factors) == 7 for factors in payload["weights"].values())


def test_trust_weights_bounded(tmp_path):
    payload = _client(
        _scorer(tmp_path, verified_count=LEARNING_THRESHOLD, load_weights=True)
    ).get("/api/purchasing/trust-weights").json()

    for factors in payload["weights"].values():
        assert all(0 <= value <= 1 for value in factors.values())


def test_trust_provenance_real(tmp_path):
    payload = _client(
        _scorer(tmp_path, verified_count=LEARNING_THRESHOLD, load_weights=True)
    ).get("/api/purchasing/trust-weights").json()

    assert payload["provenance"] == "real_measured"


def test_expected_weights(tmp_path):
    payload = _client(_scorer(tmp_path)).get("/api/purchasing/trust-weights/expected").json()

    assert set(payload["weights"]) == {"protein", "produce", "dairy", "dry_goods", "beverages"}
    assert all(len(factors) == 7 for factors in payload["weights"].values())


def test_expected_source(tmp_path):
    payload = _client(_scorer(tmp_path)).get("/api/purchasing/trust-weights/expected").json()

    assert payload["source"] == "preset_default"


def test_insights_endpoint(tmp_path):
    response = _client(
        _scorer(tmp_path, verified_count=LEARNING_THRESHOLD, load_weights=True)
    ).get("/api/purchasing/trust-weights/insights")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_insights_kitchen_language(tmp_path):
    payload = _client(
        _scorer(tmp_path, verified_count=LEARNING_THRESHOLD, load_weights=True)
    ).get("/api/purchasing/trust-weights/insights").json()

    text = " ".join(item["insight"] for item in payload)
    assert any(label in text for label in FACTOR_LABELS.values())
    assert "weather_forecast" not in text
    assert "price_memory_index" not in text


def test_insights_gap_threshold(tmp_path):
    payload = _client(
        _scorer(tmp_path, verified_count=LEARNING_THRESHOLD, load_weights=True)
    ).get("/api/purchasing/trust-weights/insights").json()

    assert payload
    assert all(item["gap"] > 0.15 for item in payload)


def test_insights_empty_pre_transition(tmp_path):
    payload = _client(_scorer(tmp_path, verified_count=5)).get(
        "/api/purchasing/trust-weights/insights"
    ).json()

    assert payload == []


def test_trust_endpoint_200(client):
    response = client.get("/api/purchasing/trust-weights")

    assert response.status_code == 200


def test_expected_endpoint_200(client):
    response = client.get("/api/purchasing/trust-weights/expected")

    assert response.status_code == 200


def test_insights_endpoint_200(client):
    response = client.get("/api/purchasing/trust-weights/insights")

    assert response.status_code == 200
