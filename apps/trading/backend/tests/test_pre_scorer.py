from __future__ import annotations

from dataclasses import fields
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.pre_score_router import create_pre_score_router
from app.services.pre_scorer import PreScoreResult, PreScorer
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.presets.trading import TradingPreset


FACTOR_NAMES = tuple(TradingPreset().shape.factor_names)
ACTION_NAMES = tuple(TradingPreset().shape.action_names)


class _RegimeContext:
    def __init__(self, regime: str = "trending") -> None:
        self._regime = regime

    def current_regime(self) -> dict[str, str]:
        return {"regime": self._regime}


def test_pre_score_returns_result() -> None:
    scorer, store = _scorer_store()

    result = PreScorer(scorer, store).pre_score("trend_following", _factors())

    assert isinstance(result, PreScoreResult)
    assert result.category == "trend_following"


def test_pre_score_has_all_fields() -> None:
    expected = {
        "recommended_action",
        "confidence",
        "probabilities",
        "category",
        "factor_values",
        "similar_trades",
        "category_accuracy",
        "current_regime",
        "regime_accuracy",
        "warning",
    }

    assert {field.name for field in fields(PreScoreResult)} == expected


def test_pre_score_no_decision_created() -> None:
    scorer, store = _scorer_store()
    before = store.count_decisions("trading")

    PreScorer(scorer, store).pre_score("trend_following", _factors())

    assert store.count_decisions("trading") == before


def test_pre_score_probabilities_sum_to_one() -> None:
    scorer, store = _scorer_store()

    result = PreScorer(scorer, store).pre_score("trend_following", _factors())

    assert sum(result.probabilities.values()) == pytest.approx(1.0)


def test_pre_score_recommended_action_valid() -> None:
    scorer, store = _scorer_store()

    result = PreScorer(scorer, store).pre_score("trend_following", _factors())

    assert result.recommended_action in ACTION_NAMES


def test_pre_score_invalid_category() -> None:
    response = _client().post("/api/trading/pre-score", json={"category": "unknown", "factors": _factors()})

    assert response.status_code == 400


def test_pre_score_missing_factors() -> None:
    factors = _factors()
    factors.pop(FACTOR_NAMES[0])

    response = _client().post("/api/trading/pre-score", json={"category": "trend_following", "factors": factors})

    assert response.status_code == 400
    assert "missing factors" in response.json()["detail"]


def test_pre_score_extra_factors() -> None:
    factors = _factors(extra_signal=0.99)

    response = _client().post("/api/trading/pre-score", json={"category": "trend_following", "factors": factors})

    assert response.status_code == 200
    assert "extra_signal" not in response.json()["factor_values"]


def test_pre_score_non_numeric_factor() -> None:
    factors = _factors()
    factors[FACTOR_NAMES[0]] = "bad"  # type: ignore[assignment]

    response = _client().post("/api/trading/pre-score", json={"category": "trend_following", "factors": factors})

    assert response.status_code == 400


def test_similar_trades_found() -> None:
    scorer, store = _scorer_store()
    _seed_verified(scorer, "trend_following", _factors(signal_alignment=0.9), correct=True)

    result = PreScorer(scorer, store).pre_score("trend_following", _factors(signal_alignment=0.9))

    assert result.similar_trades


def test_similar_trades_max_5() -> None:
    scorer, store = _scorer_store()
    for index in range(8):
        _seed_verified(scorer, "trend_following", _factors(signal_alignment=0.5 + index / 100), correct=True)

    result = PreScorer(scorer, store).pre_score("trend_following", _factors())

    assert len(result.similar_trades) == 5


def test_similar_trades_same_category_only() -> None:
    scorer, store = _scorer_store()
    _seed_verified(scorer, "mean_reversion", _factors(), correct=True)

    result = PreScorer(scorer, store).pre_score("trend_following", _factors())

    assert result.similar_trades == []


def test_similar_trades_sorted_by_similarity() -> None:
    scorer, store = _scorer_store()
    _seed_verified(scorer, "trend_following", _factors(signal_alignment=0.1), correct=True)
    _seed_verified(scorer, "trend_following", _factors(signal_alignment=0.9), correct=True)

    result = PreScorer(scorer, store).pre_score("trend_following", _factors(signal_alignment=0.9))
    similarities = [row["similarity"] for row in result.similar_trades]

    assert similarities == sorted(similarities, reverse=True)


def test_similar_trades_empty_store() -> None:
    scorer, store = _scorer_store()

    result = PreScorer(scorer, store).pre_score("trend_following", _factors())

    assert result.similar_trades == []


def test_similar_trades_zero_vector() -> None:
    scorer, store = _scorer_store()
    _seed_verified(scorer, "trend_following", _factors(), correct=True)

    result = PreScorer(scorer, store).pre_score("trend_following", _zero_factors())

    assert result.similar_trades == []


def test_similar_trades_include_correctness() -> None:
    scorer, store = _scorer_store()
    _seed_verified(scorer, "trend_following", _factors(), correct=False)

    result = PreScorer(scorer, store).pre_score("trend_following", _factors())

    assert "is_correct" in result.similar_trades[0]


def test_category_accuracy_correct() -> None:
    scorer, store = _scorer_store()
    _seed_many(scorer, "trend_following", correct=3, incorrect=1)

    assert PreScorer(scorer, store)._category_accuracy("trend_following") == 0.75


def test_category_accuracy_no_verified() -> None:
    scorer, store = _scorer_store()

    assert PreScorer(scorer, store)._category_accuracy("trend_following") == 0.0


def test_category_accuracy_division_safe() -> None:
    scorer, store = _scorer_store()

    result = PreScorer(scorer, store).pre_score("trend_following", _factors())

    assert result.category_accuracy == 0.0


def test_regime_context_present() -> None:
    scorer, store = _scorer_store()

    result = PreScorer(scorer, store, _RegimeContext("volatile")).pre_score("trend_following", _factors())

    assert result.current_regime == "volatile"


def test_regime_context_unavailable() -> None:
    scorer, store = _scorer_store()

    result = PreScorer(scorer, store, None).pre_score("trend_following", _factors())

    assert result.current_regime is None
    assert result.regime_accuracy is None


def test_regime_accuracy_present() -> None:
    scorer, store = _scorer_store()
    _seed_many(scorer, "trend_following", correct=2, incorrect=2, regime="trending")

    result = PreScorer(scorer, store, _RegimeContext("trending")).pre_score("trend_following", _factors())

    assert result.regime_accuracy == 0.5


def test_warning_low_accuracy() -> None:
    scorer, store = _scorer_store()
    _seed_many(scorer, "trend_following", correct=1, incorrect=3)

    result = PreScorer(scorer, store).pre_score("trend_following", _factors())

    assert result.warning is not None
    assert "trend_following" in result.warning


def test_warning_low_regime_accuracy() -> None:
    scorer, store = _scorer_store()
    _seed_many(scorer, "trend_following", correct=5, incorrect=0, regime="ranging")
    _seed_many(scorer, "trend_following", correct=2, incorrect=4, regime="volatile")

    result = PreScorer(scorer, store, _RegimeContext("volatile")).pre_score("trend_following", _factors())

    assert result.warning is not None
    assert "volatile conditions" in result.warning


def test_warning_none_good_accuracy() -> None:
    scorer, store = _scorer_store()
    _seed_many(scorer, "trend_following", correct=3, incorrect=1)

    result = PreScorer(scorer, store).pre_score("trend_following", _factors())

    assert result.warning is None


def test_warning_kitchen_language() -> None:
    scorer, store = _scorer_store()
    _seed_many(scorer, "trend_following", correct=0, incorrect=4, regime="volatile")

    warning = PreScorer(scorer, store, _RegimeContext("volatile")).pre_score("trend_following", _factors()).warning

    assert warning is not None
    assert "VIX" not in warning
    assert "ADX" not in warning


def test_endpoint_post_returns_200() -> None:
    response = _client().post("/api/trading/pre-score", json={"category": "trend_following", "factors": _factors()})

    assert response.status_code == 200


def test_endpoint_get_rejected() -> None:
    response = _client().get("/api/trading/pre-score")

    assert response.status_code == 405


def test_endpoint_response_shape() -> None:
    payload = _client().post("/api/trading/pre-score", json={"category": "trend_following", "factors": _factors()}).json()

    assert {
        "recommended_action",
        "confidence",
        "probabilities",
        "category",
        "factor_values",
        "similar_trades",
        "category_accuracy",
        "current_regime",
        "regime_accuracy",
        "warning",
        "preview",
        "message",
    }.issubset(payload)
    assert payload["preview"] is True
    assert payload["message"] == "preview - no decision recorded"


def _client() -> TestClient:
    scorer, store = _scorer_store()
    app = FastAPI()
    app.include_router(
        create_pre_score_router(
            scorer,
            lambda: store,
            regime_context_factory=lambda: _RegimeContext("trending"),
        )
    )
    return TestClient(app)


def _scorer_store() -> tuple[CompoundingScorer, InMemoryGraphStore]:
    store = InMemoryGraphStore("trading")
    scorer = CompoundingScorer.from_preset("trading", graph_store=store)
    return scorer, store


def _factors(**overrides: float) -> dict[str, float]:
    values = {name: 0.5 for name in FACTOR_NAMES}
    values.update(overrides)
    return values


def _zero_factors() -> dict[str, float]:
    return {name: 0.0 for name in FACTOR_NAMES}


def _seed_many(
    scorer: CompoundingScorer,
    category: str,
    *,
    correct: int,
    incorrect: int,
    regime: str = "ranging",
) -> None:
    for index in range(correct + incorrect):
        _seed_verified(
            scorer,
            category,
            _factors(signal_alignment=0.4 + (index % 5) / 10),
            correct=index < correct,
            regime=regime,
        )


def _seed_verified(
    scorer: CompoundingScorer,
    category: str,
    factors: dict[str, float],
    *,
    correct: bool,
    regime: str = "ranging",
) -> str:
    result = scorer.score(factors, category, metadata={"current_regime": regime})
    actual_action = result.action if correct else _different_action(result.action)
    scorer.learn(result.decision_id, actual_action, context={"current_regime": regime})
    store = getattr(scorer, "_graph_store")
    if not any(
        decision.get("decision_id") == result.decision_id
        for decision in store.get_verified_decisions("trading")
    ):
        store.write_outcome(
            result.decision_id,
            actual_action,
            is_correct=correct,
            metadata={"context": {"current_regime": regime}},
        )
    return result.decision_id


def _different_action(action: str) -> str:
    for candidate in ACTION_NAMES:
        if candidate != action:
            return candidate
    return ACTION_NAMES[-1]
