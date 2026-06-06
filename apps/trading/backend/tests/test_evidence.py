from __future__ import annotations

import pytest

from app.evidence import (
    FACTOR_DISPLAY,
    TradingTemplateEngine,
    _emotional_detail,
    _quality,
)
from app.factors.registry import ALL_FACTOR_NAMES
from app.routers.data_import import _trade_store_ref


def _factors(**overrides: float) -> dict[str, float]:
    values = {name: 0.65 for name in ALL_FACTOR_NAMES}
    values.update(overrides)
    return values


def _trade(
    trade_id: str = "e-1",
    *,
    category: str = "trend_following",
    factors: dict[str, float] | None = None,
) -> dict:
    return {
        "trade_id": trade_id,
        "ticker": "MSFT",
        "direction": "long",
        "category": category,
        "action": "strong_execution",
        "confidence": 0.82,
        "factors": factors or _factors(signal_alignment=0.9),
        "metadata": {
            "minutes_since_last_trade": 10,
            "last_trade_was_loss": True,
            "strategy_tag": "momentum",
        },
    }


@pytest.fixture(autouse=True)
def reset_trade_store():
    _trade_store_ref.clear()
    yield
    _trade_store_ref.clear()


def test_quality_strong():
    assert _quality(0.8) == "strong"


def test_quality_moderate():
    assert _quality(0.6) == "moderate"


def test_quality_weak():
    assert _quality(0.4) == "weak"


def test_quality_poor():
    assert _quality(0.39) == "poor"


def test_render_trend_following():
    text = TradingTemplateEngine().render(_trade(category="trend_following"), _factors(), "strong_execution", 0.8)
    assert "Trend-following setup" in text


def test_render_mean_reversion():
    text = TradingTemplateEngine().render(_trade(category="mean_reversion"), _factors(), "strong_execution", 0.8)
    assert "Mean-reversion setup" in text


def test_render_event_driven():
    text = TradingTemplateEngine().render(_trade(category="event_driven"), _factors(), "strong_execution", 0.8)
    assert "Event-driven setup" in text


def test_render_income_strategy():
    text = TradingTemplateEngine().render(_trade(category="income_strategy"), _factors(), "strong_execution", 0.8)
    assert "Income strategy setup" in text


def test_render_scalp_intraday():
    text = TradingTemplateEngine().render(_trade(category="scalp_intraday"), _factors(), "strong_execution", 0.8)
    assert "Intraday scalp setup" in text


def test_render_generic_fallback():
    text = TradingTemplateEngine().render(_trade(category="custom"), _factors(), "strong_execution", 0.8)
    assert "Trading setup" in text


def test_render_includes_ticker_and_direction():
    text = TradingTemplateEngine().render(_trade(), _factors(), "strong_execution", 0.8)
    assert text.startswith("MSFT long:")


def test_render_includes_action_and_confidence():
    text = TradingTemplateEngine().render(_trade(), _factors(), "partial_execution", 0.73)
    assert "partial_execution" in text
    assert "73% confidence" in text


def test_emotional_detail_revenge_pattern():
    detail = _emotional_detail(0.2, {"minutes_since_last_trade": 12, "last_trade_was_loss": True})
    assert detail == "quick re-entry after loss"


def test_emotional_detail_overconfidence():
    detail = _emotional_detail(0.2, {"consecutive_wins": 3, "size_vs_rolling_avg": 1.4})
    assert detail == "elevated sizing after winning streak"


def test_emotional_detail_no_flags():
    assert _emotional_detail(0.5, {}) == "no flags detected"


def test_factor_breakdown_all_10_factors():
    lines = TradingTemplateEngine().render_factor_breakdown(_factors())
    assert len(lines) == 10
    assert any(line.startswith("Decision context:") for line in lines)


def test_factor_breakdown_handles_missing_factors():
    lines = TradingTemplateEngine().render_factor_breakdown({"signal_alignment": 0.9})
    assert "Signal alignment: 0.90 (strong)" in lines
    assert "Regime fit: 0.50 (weak)" in lines


def test_trust_analysis_sorted_by_weight():
    text = TradingTemplateEngine().render_trust_analysis({
        "position_sizing": 0.2,
        "signal_alignment": 0.9,
    })
    assert text.index("Signal alignment 0.90") < text.index("Position sizing 0.20")


def test_trust_analysis_insufficient_data():
    assert TradingTemplateEngine().render_trust_analysis() == "Trust analysis has insufficient data."


def test_render_all_categories_produce_output():
    engine = TradingTemplateEngine()
    for category in (
        "trend_following",
        "mean_reversion",
        "event_driven",
        "income_strategy",
        "scalp_intraday",
    ):
        assert engine.render(_trade(category=category), _factors(), "strong_execution", 0.8)


def test_evidence_returns_text(client):
    _trade_store_ref.append(_trade())

    response = client.get("/api/trading/evidence/e-1")

    assert response.status_code == 200
    assert "evidence_text" in response.json()
    assert "MSFT long" in response.json()["evidence_text"]


def test_evidence_reads_scored_graph_decision(client):
    score = client.post(
        "/api/score",
        json={
            "category": "trend_following",
            "factors": _factors(signal_alignment=0.9),
        },
    )
    decision_id = score.json()["decision_id"]

    response = client.get(f"/api/trading/evidence/{decision_id}")

    assert response.status_code == 200
    assert response.json()["trade_id"] == decision_id
    assert response.json()["factors"]["signal_alignment"] == 0.9


def test_evidence_merges_saved_trade_metadata_for_scored_decision(client):
    score = client.post(
        "/api/score",
        json={
            "category": "trend_following",
            "factors": _factors(signal_alignment=0.9),
        },
    )
    decision_id = score.json()["decision_id"]
    client.post(
        "/api/context/trade-metadata",
        json={
            "decision_id": decision_id,
            "ticker": "AAPL",
            "direction": "long",
            "strategy_tag": "momentum",
            "minutes_since_last_trade": 15,
            "last_trade_was_loss": True,
        },
    )

    response = client.get(f"/api/trading/evidence/{decision_id}")

    assert response.status_code == 200
    assert response.json()["evidence_text"].startswith("AAPL long:")
    assert "quick re-entry after loss" in response.json()["evidence_text"]


def test_evidence_not_found_404(client):
    response = client.get("/api/trading/evidence/missing")

    assert response.status_code == 404
    assert response.json() == {"error": "Trade not found"}


def test_evidence_includes_all_factor_keys_or_defaults(client):
    _trade_store_ref.append(_trade(factors={"signal_alignment": 0.9}))

    response = client.get("/api/trading/evidence/e-1")

    assert response.status_code == 200
    assert set(response.json()["factors"]) == set(ALL_FACTOR_NAMES)


def test_evidence_uses_decision_context_label_not_emotional(client):
    _trade_store_ref.append(_trade())

    response = client.get("/api/trading/evidence/e-1")

    payload = response.json()
    assert FACTOR_DISPLAY["emotional_indicator"] == "Decision context"
    assert "Decision context" in payload["evidence_text"]
    assert any(line.startswith("Decision context:") for line in payload["factor_breakdown"])
    assert "Emotional indicator" not in payload["evidence_text"]
