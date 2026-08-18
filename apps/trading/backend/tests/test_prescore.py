from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.routers import prescore
from app.routers.data_import import _trade_store_ref
from app.services.regime import RegimeService


@pytest.fixture(autouse=True)
def reset_trade_store():
    _trade_store_ref.clear()
    yield
    _trade_store_ref.clear()


@pytest.fixture(autouse=True)
def default_regime(monkeypatch):
    monkeypatch.setattr(
        RegimeService,
        "get_current_regime",
        lambda self: {
            "regime": "ranging",
            "vix": 20.0,
            "adx": 20.0,
            "spy_price": 0.0,
            "source": "default",
        },
    )
    monkeypatch.setattr(RegimeService, "get_regime_accuracy", lambda self, trades: {})


def _payload(**overrides):
    payload = {
        "ticker": "AAPL",
        "direction": "long",
        "strategy_tag": "momentum",
        "category": "trend_following",
        "size_pct": 2.0,
    }
    payload.update(overrides)
    return payload


def _factors(**overrides):
    factors = {
        "signal_alignment": 0.8,
        "market_regime": 0.8,
        "position_sizing": 0.8,
        "timing_quality": 0.8,
        "risk_reward_actual": 0.8,
        "emotional_indicator": 0.8,
        "signal_confidence": 0.8,
    }
    factors.update(overrides)
    return factors


def _trade(trade_id: str, *, pnl: float = 10.0, minutes_ago: int = 60) -> dict:
    entry_time = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()
    return {
        "trade_id": trade_id,
        "ticker": "AAPL",
        "direction": "long",
        "category": "trend_following",
        "strategy_tag": "momentum",
        "regime": "ranging",
        "pnl": pnl,
        "entry_time": entry_time,
        "size": 2.0,
        "factors": _factors(),
        "metadata": {"source": "test"},
    }


def test_prescore_returns_recommendation(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())

    response = client.post("/api/trading/prescore", json=_payload())

    assert response.status_code == 200
    assert response.json()["recommendation"].startswith("Observation:")


def test_prescore_requires_ticker(client):
    response = client.post("/api/trading/prescore", json=_payload(ticker=""))

    assert response.status_code == 400
    assert response.json()["detail"] == "ticker is required"


def test_prescore_skip_on_low_confidence(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors(**{name: 0.35 for name in _factors()}))

    response = client.post("/api/trading/prescore", json=_payload())

    assert response.json()["recommendation"].startswith("Observation:")
    assert response.json()["confidence"] == 0.35


def test_prescore_skip_on_low_regime_accuracy(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())
    monkeypatch.setattr(RegimeService, "get_regime_accuracy", lambda self, trades: {"trend_following": {"ranging": 0.35}})

    response = client.post("/api/trading/prescore", json=_payload())

    assert response.json()["recommendation"].startswith("Observation:")
    assert "Your trend_following accuracy in ranging: 35%" in response.json()["warnings"]


def test_prescore_reduce_on_decision_context_pattern(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors(emotional_indicator=0.45))

    response = client.post("/api/trading/prescore", json=_payload())

    assert response.json()["recommendation"].startswith("Observation:")
    assert "Decision context: elevated pattern detected" in response.json()["warnings"]


def test_prescore_proceed_when_clear(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())
    monkeypatch.setattr(RegimeService, "get_regime_accuracy", lambda self, trades: {"trend_following": {"ranging": 0.7}})

    response = client.post("/api/trading/prescore", json=_payload())

    assert response.json()["recommendation"].startswith("Observation:")
    assert response.json()["warnings"] == []


def test_prescore_includes_evidence_text(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())

    response = client.post("/api/trading/prescore", json=_payload())

    assert "Observed decision context is" in response.json()["evidence"]


def test_prescore_includes_warnings_list(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors(emotional_indicator=0.45))

    payload = response_payload(client)

    assert isinstance(payload["warnings"], list)


def test_prescore_includes_regime_data(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())

    payload = client.post("/api/trading/prescore", json=_payload()).json()

    assert payload["regime"]["regime"] == "ranging"
    assert payload["regime_accuracy"] == 0.5


def test_prescore_auto_classifies_category(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())

    payload = client.post("/api/trading/prescore", json=_payload(category=None, strategy_tag="rsi_oversold")).json()

    assert payload["category"] == "mean_reversion"


def test_prescore_no_historical_trades(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())

    payload = client.post("/api/trading/prescore", json=_payload()).json()

    assert payload["regime_accuracy"] == 0.5
    assert payload["recommendation"].startswith("Observation:")


def test_prescore_response_has_all_keys(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())

    payload = client.post("/api/trading/prescore", json=_payload()).json()

    assert set(payload) == {
        "recommendation",
        "confidence",
        "action",
        "factors",
        "regime",
        "regime_accuracy",
        "warnings",
        "evidence",
        "category",
        "observation_only",
    }


def test_prescore_read_only_does_not_increment_decision_count(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())
    before = len(client.get("/api/history").json()["decisions"])

    response = client.post("/api/trading/prescore", json=_payload())
    after = len(client.get("/api/history").json()["decisions"])

    assert response.status_code == 200
    assert after == before


def test_auto_classify_rsi_is_mean_reversion():
    assert prescore._auto_classify({"ticker": "AAPL", "strategy_tag": "rsi_oversold"}) == "mean_reversion"


def test_auto_classify_earnings_is_event():
    assert prescore._auto_classify({"ticker": "AAPL", "strategy_tag": "earnings_catalyst"}) == "event_driven"


def test_auto_classify_default_is_trend():
    assert prescore._auto_classify({"ticker": "AAPL", "strategy_tag": "breakout"}) == "trend_following"


def test_consecutive_wins_counts_correctly():
    trades = [
        _trade("old-loss", pnl=-1, minutes_ago=90),
        _trade("win-1", pnl=2, minutes_ago=30),
        _trade("win-2", pnl=3, minutes_ago=10),
    ]

    assert prescore._consecutive_wins(trades) == 2


def test_minutes_since_last_no_trades_returns_999():
    assert prescore._minutes_since_last([]) == 999.0


def test_last_was_loss_empty_returns_false():
    assert prescore._last_was_loss([]) is False


def test_prescore_skip_boundary_confidence_040(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors(**{name: 0.4 for name in _factors()}))

    payload = client.post("/api/trading/prescore", json=_payload()).json()

    assert payload["recommendation"].startswith("Observation:")


def test_prescore_skip_boundary_regime_acc_040(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())
    monkeypatch.setattr(RegimeService, "get_regime_accuracy", lambda self, trades: {"trend_following": {"ranging": 0.4}})

    payload = client.post("/api/trading/prescore", json=_payload()).json()

    assert payload["recommendation"].startswith("Observation:")


def test_prescore_reduce_boundary_emotional_050(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors(emotional_indicator=0.5, signal_confidence=1.0))

    payload = client.post("/api/trading/prescore", json=_payload()).json()

    assert payload["recommendation"].startswith("Observation:")


def test_prescore_warns_on_quick_reentry_after_loss(client, monkeypatch):
    _trade_store_ref.append(_trade("loss", pnl=-5, minutes_ago=5))
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())

    payload = client.post("/api/trading/prescore", json=_payload()).json()

    assert "Quick re-entry after loss detected" in payload["warnings"]


def test_prescore_market_regime_uses_accuracy_dict(client, monkeypatch):
    monkeypatch.setattr(
        RegimeService,
        "get_current_regime",
        lambda self: {"regime": "trending", "vix": 18.0, "adx": 32.0},
    )
    monkeypatch.setattr(
        RegimeService,
        "get_regime_accuracy",
        lambda self, trades: {"trend_following": {"trending": 0.82}},
    )

    payload = client.post("/api/trading/prescore", json=_payload()).json()

    assert payload["regime_accuracy"] == 0.82
    assert payload["factors"]["market_regime"] == 0.82


def test_prescore_signal_confidence_has_context_keys(client, monkeypatch):
    for index in range(6):
        trade = _trade(
            f"trade-{index}",
            pnl=10.0 if index < 5 else -10.0,
            minutes_ago=120 - index,
        )
        trade["verified"] = True
        trade["is_correct"] = index < 5
        _trade_store_ref.append(trade)

    captured: dict = {}
    real_compute_factors = prescore.compute_factors

    def spy_compute_factors(context):
        captured.update(context)
        return real_compute_factors(context)

    monkeypatch.setattr(prescore, "compute_factors", spy_compute_factors)

    payload = client.post("/api/trading/prescore", json=_payload()).json()

    assert captured["similar_trade_count"] == 6
    assert captured["category_accuracy"] == pytest.approx(5 / 6)
    assert captured["factors_with_data"] == 7
    assert payload["factors"]["signal_confidence"] != 0.5


def test_prescore_all_10_factors_wired(client, monkeypatch):
    for index in range(20):
        trade = _trade(f"trade-{index}", minutes_ago=300 - index)
        trade["verified"] = True
        trade["is_correct"] = index < 18
        _trade_store_ref.append(trade)
    monkeypatch.setattr(
        RegimeService,
        "get_current_regime",
        lambda self: {"regime": "trending", "vix": 18.0, "adx": 32.0},
    )
    monkeypatch.setattr(
        RegimeService,
        "get_regime_accuracy",
        lambda self, trades: {"trend_following": {"trending": 0.82}},
    )

    payload = client.post(
        "/api/trading/prescore",
        json=_payload(
            context={
                "tagged_signals": [
                    {"name": "breakout", "confirmed": True},
                    {"name": "volume", "confirmed": True},
                ],
                "rsi_at_entry": 25.0,
                "macd_signal": "bullish",
                "price_vs_sma": 1.1,
                "entry_delay_minutes": 5,
                "hold_time_vs_plan_pct": 1.0,
                "time_of_day_accuracy": 0.8,
                "planned_risk_reward": 2.0,
                "actual_risk_reward": 2.5,
                "delta": 0.65,
                "iv_percentile": 80,
                "gamma": 0.04,
            },
        ),
    ).json()

    factors = payload["factors"]
    assert len(factors) == 10
    assert all(value != 0.5 for value in factors.values())


def test_prescore_empty_history_defaults_gracefully(client):
    response = client.post("/api/trading/prescore", json=_payload())

    assert response.status_code == 200
    assert set(response.json()["factors"]) == set(prescore.compute_factors({}))


def response_payload(client):
    return client.post("/api/trading/prescore", json=_payload()).json()
