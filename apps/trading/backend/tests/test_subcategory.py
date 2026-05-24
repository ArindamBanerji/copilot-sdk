from __future__ import annotations

import sys
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import cli  # noqa: E402
from app.evidence import TradingTemplateEngine  # noqa: E402
from app.routers import prescore as prescore_module  # noqa: E402
from app.routers.data_import import _trade_store_ref  # noqa: E402
from app.services.subcategory import classify_event_subcategory, get_subcategory  # noqa: E402


@pytest.fixture(autouse=True)
def reset_trade_store():
    _trade_store_ref.clear()
    yield
    _trade_store_ref.clear()


def _trade(
    trade_id: str,
    *,
    category: str = "event_driven",
    strategy_tag: str = "earnings_direction",
    pnl: float = 100.0,
    notes: str | None = None,
) -> dict:
    return {
        "trade_id": trade_id,
        "ticker": "MSFT",
        "direction": "long",
        "category": category,
        "strategy_tag": strategy_tag,
        "pnl": pnl,
        "entry_time": "2026-01-01T09:30:00",
        "notes": notes,
        "metadata": {"notes": notes} if notes else {},
    }


def _factors() -> dict[str, float]:
    return {
        "signal_alignment": 0.8,
        "market_regime": 0.7,
        "position_sizing": 0.7,
        "timing_quality": 0.7,
        "risk_reward_actual": 0.8,
        "emotional_indicator": 0.8,
        "signal_confidence": 0.8,
    }


def _config_dir(tmp_path: Path) -> Path:
    return tmp_path / "ci-trading"


def test_earnings_direction_is_directional():
    assert classify_event_subcategory("earnings_direction") == "directional"


def test_straddle_is_volatility():
    assert classify_event_subcategory("straddle") == "volatility"


def test_strangle_is_volatility():
    assert classify_event_subcategory("strangle") == "volatility"


def test_iv_play_is_volatility():
    assert classify_event_subcategory("iv_play") == "volatility"


def test_iv_play_with_space_is_volatility():
    assert classify_event_subcategory("iv play") == "volatility"


def test_fda_approval_is_directional():
    assert classify_event_subcategory("fda_approval") == "directional"


def test_unknown_tag_defaults_directional():
    assert classify_event_subcategory("custom_event") == "directional"


def test_notes_with_straddle_is_volatility():
    assert classify_event_subcategory("custom_event", notes="post earnings straddle") == "volatility"


def test_notes_with_vol_play_is_volatility():
    assert classify_event_subcategory("custom_event", notes="vol play") == "volatility"


def test_notes_with_vol_play_normalized_underscore_is_volatility():
    assert classify_event_subcategory("custom_event", notes="vol_play") == "volatility"


def test_none_tag_defaults_directional():
    assert classify_event_subcategory(None) == "directional"


def test_non_event_driven_returns_none():
    assert get_subcategory({"category": "trend_following", "strategy_tag": "straddle"}) is None


def test_get_subcategory_event_driven():
    assert get_subcategory(_trade("t-1", strategy_tag="pre_earnings_iv")) == "volatility"


def test_get_subcategory_trend_following_is_none():
    assert get_subcategory(_trade("t-1", category="trend_following", strategy_tag="earnings_direction")) is None


def test_event_driven_no_tag_no_notes_defaults_directional():
    assert get_subcategory(_trade("t-1", strategy_tag="")) == "directional"


def test_analytics_group_by_subcategory(client):
    _trade_store_ref.extend([
        _trade("t-1", strategy_tag="earnings_direction", pnl=100.0),
        _trade("t-2", strategy_tag="straddle", pnl=-50.0),
        _trade("t-3", strategy_tag="iv_play", pnl=75.0),
    ])

    response = client.get("/api/trading/analytics?group_by=subcategory")

    assert response.status_code == 200
    groups = {group["key"]: group for group in response.json()["groups"]}
    assert groups["directional"]["count"] == 1
    assert groups["volatility"]["count"] == 2
    assert groups["volatility"]["win_rate"] == 0.5


def test_analytics_subcategory_only_event_driven(client):
    _trade_store_ref.extend([
        _trade("t-1", strategy_tag="straddle"),
        _trade("t-2", category="trend_following", strategy_tag="straddle"),
    ])

    payload = client.get("/api/trading/analytics?group_by=subcategory").json()

    assert payload["total"] == 1
    assert {group["key"] for group in payload["groups"]} == {"volatility"}


def test_analytics_category_unchanged_no_nested_subcategory(client):
    _trade_store_ref.extend([
        _trade("t-1", strategy_tag="straddle"),
        _trade("t-2", category="trend_following", strategy_tag="momentum"),
    ])

    payload = client.get("/api/trading/analytics?group_by=category").json()

    assert payload["group_by"] == "category"
    groups = {group["key"]: group for group in payload["groups"]}
    assert set(groups) == {"event_driven", "trend_following"}
    assert "subcategory" not in groups["event_driven"]


def test_event_evidence_includes_subcategory_label():
    text = TradingTemplateEngine().render(
        _trade("t-1", strategy_tag="straddle"),
        _factors(),
        "strong_execution",
        0.8,
    )

    assert "Event: Volatility play." in text


def test_non_event_evidence_unchanged():
    text = TradingTemplateEngine().render(
        _trade("t-1", category="trend_following", strategy_tag="straddle"),
        _factors(),
        "strong_execution",
        0.8,
    )

    assert "Event:" not in text


def test_prescore_event_driven_includes_subcategory(client, monkeypatch):
    monkeypatch.setattr(prescore_module.RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0})
    monkeypatch.setattr(prescore_module.RegimeService, "get_regime_accuracy", lambda self, trades: {})
    monkeypatch.setattr(prescore_module, "compute_factors", lambda context: _factors())

    payload = client.post(
        "/api/trading/prescore",
        json={"ticker": "MSFT", "category": "event_driven", "strategy_tag": "straddle", "direction": "long"},
    ).json()

    assert payload["category"] == "event_driven"
    assert payload["subcategory"] == "volatility"


def test_prescore_non_event_omits_subcategory(client, monkeypatch):
    monkeypatch.setattr(prescore_module.RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0})
    monkeypatch.setattr(prescore_module.RegimeService, "get_regime_accuracy", lambda self, trades: {})
    monkeypatch.setattr(prescore_module, "compute_factors", lambda context: _factors())

    payload = client.post(
        "/api/trading/prescore",
        json={"ticker": "MSFT", "category": "trend_following", "strategy_tag": "straddle", "direction": "long"},
    ).json()

    assert payload["category"] == "trend_following"
    assert "subcategory" not in payload


def test_journal_event_driven_subcategory_summary(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    cli._save_trades([
        _trade("t-1", strategy_tag="earnings_direction", pnl=100.0),
        _trade("t-2", strategy_tag="straddle", pnl=-50.0),
        _trade("t-3", strategy_tag="iv_play", pnl=25.0),
    ], config_dir)

    assert cli.main(["--config-dir", str(config_dir), "journal"]) == 0

    output = capsys.readouterr().out
    assert "Event-Driven Subcategories" in output
    assert "- directional: 1 trades, win rate 100.0%" in output
    assert "- volatility: 2 trades, win rate 50.0%" in output


def test_journal_no_event_driven_no_subcategory_summary(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    cli._save_trades([
        _trade("t-1", category="trend_following", strategy_tag="momentum"),
    ], config_dir)

    assert cli.main(["--config-dir", str(config_dir), "journal"]) == 0

    assert "Event-Driven Subcategories" not in capsys.readouterr().out
