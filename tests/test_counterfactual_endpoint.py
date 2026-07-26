from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.counterfactual_router import create_counterfactual_router
from copilot_sdk.scoring import CompoundingScorer
from copilot_sdk.scoring.presets.trading import TradingPreset


def _client() -> tuple[TestClient, dict[str, float], str]:
    scorer = CompoundingScorer.from_preset("trading", profile="test")
    preset = TradingPreset()
    factors = {name: 0.6 for name in preset.shape.factor_names}
    category = preset.shape.category_names[0]
    app = FastAPI()
    app.include_router(
        create_counterfactual_router(
            "trading",
            prefix="/api/trading/score",
            scorer_provider=lambda: scorer,
        )
    )
    return TestClient(app), factors, category


def _highest_weight_factor() -> str:
    scorer = CompoundingScorer.from_preset("trading", profile="test")
    preset = TradingPreset()
    category = preset.shape.category_names[0]
    for index in range(400):
        training_factors = {
            name: 0.25 + ((index + offset) % 7) * 0.08
            for offset, name in enumerate(preset.shape.factor_names)
        }
        score = scorer.score(
            training_factors,
            category,
            metadata={"entity_id": f"counterfactual-direction-{index}"},
        )
        scorer.learn(score.decision_id, score.action, outcome="confirmed")
    weights = scorer.get_dk_weights()
    if weights:
        averages = [
            sum(row[index] for row in weights) / len(weights)
            for index in range(len(preset.shape.factor_names))
        ]
        return preset.shape.factor_names[max(range(len(averages)), key=lambda index: averages[index])]
    # Fallback for scorer configs that do not expose DK weights in endpoint tests.
    return "signal_confidence"


def test_counterfactual_returns_delta():
    client, factors, category = _client()
    changed = dict(factors)
    changed[next(iter(factors))] = 0.1
    response = client.post(
        "/api/trading/score/counterfactual",
        json={"base_factors": factors, "perturbed_factors": changed, "category": category},
    )
    assert response.status_code == 200
    body = response.json()
    assert "base_score" in body
    assert "perturbed_score" in body
    assert "delta" in body


def test_counterfactual_direction_correct():
    client, factors, category = _client()
    factor = next(iter(factors))
    small = dict(factors)
    large = dict(factors)
    small[factor] = 0.5
    large[factor] = 0.1
    small_response = client.post(
        "/api/trading/score/counterfactual",
        json={"base_factors": factors, "perturbed_factors": small, "category": category},
    ).json()
    large_response = client.post(
        "/api/trading/score/counterfactual",
        json={"base_factors": factors, "perturbed_factors": large, "category": category},
    ).json()
    assert abs(large_response["delta"]) >= abs(small_response["delta"])


def test_counterfactual_direction_improvement():
    client, factors, category = _client()
    factor = _highest_weight_factor()
    base = {name: 0.6 for name in factors}
    improved = dict(base)
    improved[factor] = 0.9
    response = client.post(
        "/api/trading/score/counterfactual",
        json={"base_factors": base, "perturbed_factors": improved, "category": category},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["perturbed_factor"] == factor
    assert body["perturbed_score"] > body["base_score"]


def test_counterfactual_direction_degradation():
    client, factors, category = _client()
    factor = _highest_weight_factor()
    base = {name: 0.6 for name in factors}
    degraded = dict(base)
    degraded[factor] = 0.1
    response = client.post(
        "/api/trading/score/counterfactual",
        json={"base_factors": base, "perturbed_factors": degraded, "category": category},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["perturbed_factor"] == factor
    assert body["perturbed_score"] < body["base_score"]


def test_counterfactual_sample_rejected():
    client, factors, category = _client()
    sample = dict(factors)
    sample[next(iter(factors))] = {"value": 0.6, "provenance": "sample"}
    response = client.post(
        "/api/trading/score/counterfactual",
        json={"base_factors": sample, "perturbed_factors": factors, "category": category},
    )
    assert response.status_code == 422
    assert response.json()["rejected"] is True


def test_counterfactual_same_factors_zero_delta():
    client, factors, category = _client()
    response = client.post(
        "/api/trading/score/counterfactual",
        json={"base_factors": factors, "perturbed_factors": factors, "category": category},
    )
    assert response.status_code == 200
    assert response.json()["delta"] == 0


def test_counterfactual_returns_provenance():
    client, factors, category = _client()
    changed = dict(factors)
    changed[next(iter(factors))] = 0.2
    response = client.post(
        "/api/trading/score/counterfactual",
        json={"base_factors": factors, "perturbed_factors": changed, "category": category},
    )
    assert response.status_code == 200
    assert response.json()["provenance"] == "learned"
