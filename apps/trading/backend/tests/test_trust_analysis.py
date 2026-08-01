from __future__ import annotations

import pytest

from app.factors.registry import ALL_FACTOR_NAMES, TRADING_FACTOR_COMPUTERS
from app.routers.data_import import _trade_store_ref
from app.services.trust_analysis import TrustAnalyzer
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer


@pytest.fixture(autouse=True)
def reset_trade_store():
    _trade_store_ref.clear()
    yield
    _trade_store_ref.clear()


def _trade(**overrides):
    payload = {
        "trade_id": "t-1",
        "ticker": "MSFT",
        "direction": "long",
        "entry_price": 100.0,
        "size": 1.0,
        "tagged_signals": [{"name": "breakout", "confirmed": True}],
        "has_trade_plan": True,
        "position_conviction": 0.8,
        "size_vs_rolling_avg": 1.0,
        "rsi_at_entry": 42,
        "macd_signal": "bullish",
        "price_vs_sma": 1.05,
        "entry_direction": "long",
        "current_regime": "trending",
        "regime_accuracy": {"trending": 0.8},
    }
    payload.update(overrides)
    return payload


class FakeStore:  # MOCK-OK: read-only analyzer input, no score/learn calls
    def __init__(self, total: int = 0):
        self._total = total

    def get_decisions(self, domain: str = "trading", limit: int = 10000):
        return [{"decision_id": f"d-{idx}"} for idx in range(self._total)]


class FakeScorer:  # MOCK-OK: read-only analyzer input, no score/learn calls
    def __init__(self, phase: str = "A", weights: list[list[float]] | None = None, total: int = 0):
        self._preset = TradingPreset()
        self.phase = phase
        self._weights = weights
        self.graph_store = FakeStore(total=total)

    def get_phase(self) -> str:
        return self.phase

    def get_dk_weights(self):
        return self._weights


def _fake_scorer(phase: str = "A", weights: list[list[float]] | None = None, total: int = 0) -> FakeScorer:
    return FakeScorer(phase=phase, weights=weights, total=total)


def _dk_matrix() -> list[list[float]]:
    factors = TradingPreset().shape.factor_names
    categories = TradingPreset().shape.category_names
    matrix = []
    for cat_index, _category in enumerate(categories):
        row = []
        for factor_index, _factor in enumerate(factors):
            row.append(round(0.42 + cat_index * 0.02 + factor_index * 0.01, 3))
        row[0] = 0.95 - cat_index * 0.01
        row[1] = 0.20
        row[2] = 0.10
        matrix.append(row)
    return matrix


def _trained_real_dk_scorer() -> CompoundingScorer:
    scorer = CompoundingScorer.from_preset(
        "trading",
        profile="test",
        graph_store=InMemoryGraphStore(domain="trading"),
        enable_rl=False,
    )
    shape = scorer._preset.shape
    store = scorer._graph_store
    for index in range(400):
        category = shape.category_names[index % len(shape.category_names)]
        category_index = shape.category_names.index(category)
        action = shape.action_names[index % len(shape.action_names)]
        action_index = shape.action_names.index(action)
        factors = {
            factor: round(0.2 + ((index + offset) % 7) * 0.09, 4)
            for offset, factor in enumerate(shape.factor_names)
        }
        decision_id = f"trust-dk-{index}"
        store.write_decision(
            "trading",
            category,
            action,
            0.9,
            factors,
            metadata={
                "decision_id": decision_id,
                "category_index": category_index,
                "recommended_index": action_index,
            },
        )
        store.write_outcome(
            decision_id,
            action,
            True,
            metadata={"actual_index": action_index},
            domain="trading",
        )
    scorer.reestimate_dk_if_due()
    assert scorer.get_dk_weights() is not None
    return scorer


def _scoring_route_scorer_proxy(app):
    for route in app.routes:
        if getattr(route, "path", None) != "/api/score":
            continue
        endpoint = getattr(route, "endpoint", None)
        code = getattr(endpoint, "__code__", None)
        closure = getattr(endpoint, "__closure__", None)
        if code is None or not closure:
            continue
        for name, cell in zip(code.co_freevars, closure):
            if name == "get_scorer":
                return cell.cell_contents()
    raise AssertionError("Could not find /api/score get_scorer closure")


def test_trust_endpoint_200_empty(client):
    response = client.get("/api/context/trust-analysis")

    assert response.status_code == 200


def test_trust_empty_has_all_10_factors(client):
    payload = client.get("/api/context/trust-analysis").json()

    assert payload["factors"] == list(ALL_FACTOR_NAMES)
    assert len(payload["factors"]) == 10
    assert set(payload["trust_scores"]) == set(ALL_FACTOR_NAMES)
    assert set(score["name"] for score in payload["factor_details"]) == set(ALL_FACTOR_NAMES)


def test_trust_empty_total_trades_zero(client):
    payload = client.get("/api/context/trust-analysis").json()

    assert payload["total_trades"] == 0
    assert isinstance(payload["hero_insight"], str)
    for factor, score in payload["trust_scores"].items():
        assert score["variance"] == 0.0
        assert score["mean"] == 0.5
        assert score["n_samples"] == 0
        expected = "not_computed" if factor not in TRADING_FACTOR_COMPUTERS else "insufficient_data"
        assert score["trust_label"] == expected
        assert score["sigma"] == 0.0


def test_trust_with_trades(client):
    _trade_store_ref.extend(
        [
            _trade(trade_id="t-1", position_conviction=0.9, rsi_at_entry=35),
            _trade(trade_id="t-2", position_conviction=0.6, rsi_at_entry=62, current_regime="ranging"),
            _trade(trade_id="t-3", position_conviction=0.3, rsi_at_entry=76, macd_signal="bearish"),
        ]
    )

    payload = client.get("/api/context/trust-analysis").json()

    assert payload["total_trades"] == 3
    assert payload["trust_scores"]["signal_alignment"]["n_samples"] == 3
    assert payload["trust_scores"]["signal_alignment"]["variance"] > 0.0


def test_trust_scores_have_required_fields(client):
    _trade_store_ref.append(_trade())

    payload = client.get("/api/context/trust-analysis").json()

    for score in payload["trust_scores"].values():
        assert {"variance", "mean", "n_samples", "trust_label", "sigma"} <= set(score)
        assert isinstance(score["variance"], (int, float))
        assert isinstance(score["mean"], (int, float))
        assert isinstance(score["n_samples"], int)
        assert isinstance(score["sigma"], (int, float))


def test_trust_route_mounted(client):
    paths = {route.path for route in client.app.routes}

    assert "/api/context/trust-analysis" in paths


def test_implemented_factors_match_registry(client):
    payload = client.get("/api/context/trust-analysis").json()

    assert set(payload["implemented"]) == set(TRADING_FACTOR_COMPUTERS)


def test_unimplemented_factors_marked_not_computed_or_insufficient(client):
    _trade_store_ref.append(_trade())

    payload = client.get("/api/context/trust-analysis").json()

    for factor in ALL_FACTOR_NAMES:
        label = payload["trust_scores"][factor]["trust_label"]
        if factor in TRADING_FACTOR_COMPUTERS:
            assert label != "not_computed"
        else:
            assert label == "not_computed"


def test_hero_insight_shape_when_available(client):
    _trade_store_ref.extend(
        [
            _trade(trade_id="t-1", position_conviction=0.95, rsi_at_entry=32, current_regime="trending"),
            _trade(trade_id="t-2", position_conviction=0.45, rsi_at_entry=66, current_regime="trending"),
            _trade(trade_id="t-3", position_conviction=0.15, rsi_at_entry=78, current_regime="trending"),
        ]
    )

    payload = client.get("/api/context/trust-analysis").json()
    insight = payload["hero_insight"]

    assert isinstance(insight, str)
    assert "Most consistent factor:" in insight


def test_dk_mode_returns_dk_weights():
    result = TrustAnalyzer().analyze(_fake_scorer("B", _dk_matrix()), [], category=None)

    assert result["mode"] == "dk"
    assert result["phase"] == "B"
    assert all("dk_weight" in factor for factor in result["factors"])


def test_variance_mode_on_phase_a():
    result = TrustAnalyzer().analyze(_fake_scorer("A", _dk_matrix()), [_trade()], category=None)

    assert result["mode"] == "variance"
    assert all("dk_weight" not in factor for factor in result["factors"])


def test_phase_b_missing_dk_falls_to_variance():
    result = TrustAnalyzer().analyze(_fake_scorer("B", None), [_trade()], category=None)

    assert result["mode"] == "variance"
    assert result["phase"] == "B"
    assert len(result["factors"]) == 10
    assert all("variance_score" in factor for factor in result["factors"])
    assert "Phase B reached but DK weights not yet available" in result["hero_insight"]


def test_per_category_dk():
    result = TrustAnalyzer().analyze(_fake_scorer("B", _dk_matrix()), [], category=None)

    assert set(result["per_category"]) == set(TradingPreset().shape.category_names)
    assert all(len(factors) == 10 for factors in result["per_category"].values())


def test_noise_detection():
    result = TrustAnalyzer().analyze(_fake_scorer("B", _dk_matrix()), [], category=None)

    assert {"market_regime", "position_sizing"} <= set(result["noise_signals"])


def test_top_signal():
    result = TrustAnalyzer().analyze(_fake_scorer("B", _dk_matrix()), [], category=None)

    assert result["top_signal"] == "signal_alignment"


def test_hero_insight_dk_mode():
    result = TrustAnalyzer().analyze(_fake_scorer("B", _dk_matrix()), [], category=None)

    assert "Your most trusted signal is signal_alignment" in result["hero_insight"]
    assert "market_regime" in result["hero_insight"]


def test_hero_insight_variance_mode():
    result = TrustAnalyzer().analyze(_fake_scorer("A"), [_trade()], category=None)

    assert "Most consistent factor:" in result["hero_insight"]


def test_available_categories():
    result = TrustAnalyzer().analyze(_fake_scorer("B", _dk_matrix()), [], category=None)

    assert result["available_categories"] == list(TradingPreset().shape.category_names)


def test_backward_compat_trust_scores(client):
    payload = client.get("/api/context/trust-analysis").json()

    assert "trust_scores" in payload
    assert isinstance(payload["trust_scores"], dict)
    assert set(payload["trust_scores"]) == set(payload["factors"])


def test_trust_endpoint_uses_shared_scorer(client):
    scorer_proxy = _scoring_route_scorer_proxy(client.app)
    original_scorer = getattr(scorer_proxy, "_scorer_instance", None)
    scorer_proxy._scorer_instance = _trained_real_dk_scorer()

    try:
        payload = client.get("/api/context/trust-analysis?category=trend_following").json()
    finally:
        scorer_proxy._scorer_instance = original_scorer

    assert payload["mode"] == "dk"
    assert payload["phase"] == "B"
    assert payload["trust_scores"]["signal_alignment"]["dk_weight"] is not None
