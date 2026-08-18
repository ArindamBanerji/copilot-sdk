from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


import cli
from app.routers import data_import
from app.routers.regime import _regime_recommendations
from app.services import regime as regime_module
from app.services.regime import DEFAULT_ADX, RegimeService, classify_regime, compute_adx
from copilot_sdk.evidence.provenance import Provenanced


def test_volatile_above_30():
    assert classify_regime(30.1, 10.0) == "volatile"


def test_ranging_vix_20_to_30():
    assert classify_regime(25.0, 40.0) == "ranging"


def test_trending_low_vix_high_adx():
    assert classify_regime(18.0, 26.0) == "trending"


def test_ranging_low_vix_low_adx():
    assert classify_regime(18.0, 20.0) == "ranging"


def test_boundary_vix_exactly_20():
    assert classify_regime(20.0, 26.0) == "trending"
    assert classify_regime(20.0, 25.0) == "ranging"


def test_boundary_vix_exactly_30():
    assert classify_regime(30.0, 26.0) == "ranging"


def test_adx_returns_float_with_synthetic_data_or_default():
    highs = [100 + offset for offset in range(30)]
    lows = [95 + offset for offset in range(30)]
    closes = [98 + offset for offset in range(30)]

    assert isinstance(compute_adx(highs, lows, closes), float)


def test_adx_insufficient_data_returns_default():
    assert compute_adx([1.0], [1.0], [1.0]) == DEFAULT_ADX


def test_adx_import_failure_returns_default(monkeypatch):
    monkeypatch.setitem(sys.modules, "pandas_ta", None)

    assert compute_adx(list(range(30)), list(range(30)), list(range(30))) == DEFAULT_ADX


def test_service_returns_dict_with_regime_key():
    payload = RegimeService(provider=_empty_provider()).get_current_regime()

    assert payload["regime"] == "ranging"
    assert payload["source"] == "default"


def test_service_caches_result(monkeypatch):
    calls = {"count": 0}

    class CountProvider:
        def get_vix_current(self):
            calls["count"] += 1
            return Provenanced(value=18.0, source="live", as_of="2026-01-01T00:00:00Z")

        def get_ohlcv(self, *_args, **_kwargs):
            calls["count"] += 1
            return Provenanced(
                value=[
                    {"high": 30 + index, "low": 20 + index, "close": 25 + index}
                    for index in range(30)
                ],
                source="live",
                as_of="2026-01-01T00:00:00Z",
            )

    monkeypatch.setattr(regime_module, "compute_adx", lambda *_args, **_kwargs: 30.0)
    service = RegimeService(provider=CountProvider())

    first = service.get_current_regime()
    second = service.get_current_regime()

    assert first["source"] == "live"
    assert second["source"] == "cached"
    assert calls["count"] == 2


def test_service_default_when_provider_empty():
    assert RegimeService(provider=_empty_provider()).get_current_regime() == {
        "regime": "ranging",
        "vix": 20.0,
        "adx": 20.0,
        "spy_price": 0.0,
        "source": "default",
    }


def test_regime_accuracy_groups_correctly():
    trades = [
        {"category": "trend_following", "regime": "trending", "pnl": 10},
        {"category": "trend_following", "regime": "ranging", "pnl": -5},
        {"category": "mean_reversion", "regime": "ranging", "pnl": 2},
    ]

    accuracy = RegimeService().get_regime_accuracy(trades)

    assert set(accuracy) == {"trend_following", "mean_reversion"}
    assert accuracy["trend_following"]["trending"] == 1.0
    assert accuracy["mean_reversion"]["ranging"] == 1.0


def test_regime_accuracy_computes_win_rate():
    trades = [
        {"category": "trend_following", "regime": "trending", "pnl": 10},
        {"category": "trend_following", "regime": "trending", "pnl": -5},
        {"category": "trend_following", "regime": "trending", "pnl": 3},
    ]

    assert RegimeService().get_regime_accuracy(trades)["trend_following"]["trending"] == 0.6667


def test_regime_accuracy_skips_unknown():
    assert RegimeService().get_regime_accuracy([{"category": "trend_following", "pnl": 1}]) == {}


def test_batch_vix_lookup_empty_trades_returns_empty():
    assert RegimeService()._batch_vix_lookup([]) == {}


def test_regime_accuracy_with_retroactive_batch(monkeypatch):
    service = RegimeService()
    monkeypatch.setattr(service, "_batch_vix_lookup", lambda trades: {"2026-01-05": 18.0, "2026-01-06": 31.0})
    trades = [
        {"category": "trend_following", "entry_time": "2026-01-05T09:30:00", "pnl": 10},
        {"category": "trend_following", "entry_time": "2026-01-06T09:30:00", "pnl": -5},
    ]

    accuracy = service.get_regime_accuracy(trades)

    assert accuracy["trend_following"]["ranging"] == 1.0
    assert accuracy["trend_following"]["volatile"] == 0.0


def test_regime_endpoint_returns_200(client, monkeypatch):
    data_import._trade_store_ref.clear()
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "spy_price": 0.0, "source": "default"})

    response = client.get("/api/trading/regime")

    assert response.status_code == 200


def test_regime_endpoint_has_current(client, monkeypatch):
    data_import._trade_store_ref.clear()
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "spy_price": 0.0, "source": "default"})

    payload = client.get("/api/trading/regime").json()

    assert payload["current"]["regime"] == "ranging"


def test_regime_endpoint_includes_accuracy(client, monkeypatch):
    data_import._trade_store_ref.clear()
    data_import._trade_store_ref.append({"trade_id": "t-1", "category": "trend_following", "regime": "ranging", "pnl": 5})
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "spy_price": 0.0, "source": "default"})

    payload = client.get("/api/trading/regime").json()

    assert payload["accuracy_by_category"]["trend_following"]["ranging"] == 1.0


def test_regime_endpoint_includes_recommendations(client, monkeypatch):
    data_import._trade_store_ref.clear()
    data_import._trade_store_ref.extend([
        {"trade_id": "t-1", "category": "trend_following", "regime": "ranging", "pnl": 5},
        {"trade_id": "t-2", "category": "trend_following", "regime": "trending", "pnl": -1},
    ])
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "spy_price": 0.0, "source": "default"})

    payload = client.get("/api/trading/regime").json()

    assert payload["recommendations"][0]["category"] == "trend_following"
    assert payload["recommendations"][0]["action"] == "observed_improving"


def test_regime_recommendations_sorted_by_accuracy():
    recommendations = _regime_recommendations(
        "ranging",
        {
            "mean_reversion": {"ranging": 0.55, "trending": 0.50},
            "trend_following": {"ranging": 0.90, "trending": 0.40},
        },
    )

    assert [row["category"] for row in recommendations] == ["trend_following", "mean_reversion"]


def test_regime_endpoint_cold_start_no_trades_200(client, monkeypatch):
    data_import._trade_store_ref.clear()
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "spy_price": 0.0, "source": "default"})

    payload = client.get("/api/trading/regime").json()

    assert payload["accuracy_by_category"] == {}
    assert payload["recommendations"] == []


def test_regime_shows_current(tmp_path, monkeypatch, capsys):
    config_dir = tmp_path / "ci-trading"
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "trending", "vix": 18.0, "adx": 30.0, "source": "default"})

    assert cli.main(["--config-dir", str(config_dir), "regime"]) == 0

    output = capsys.readouterr().out
    assert "Current regime: trending" in output
    assert "VIX: 18.00" in output


def test_regime_with_trades_shows_table(tmp_path, monkeypatch, capsys):
    config_dir = tmp_path / "ci-trading"
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    cli._save_trades(
        [{"trade_id": "t-1", "category": "trend_following", "regime": "ranging", "pnl": 5}],
        config_dir,
    )
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "source": "default"})

    assert cli.main(["--config-dir", str(config_dir), "regime"]) == 0

    output = capsys.readouterr().out
    assert "Category" in output
    assert "trend_following" in output


def test_regime_no_yfinance_uses_default(tmp_path, monkeypatch, capsys):
    config_dir = tmp_path / "ci-trading"
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "source": "default"})

    assert cli.main(["--config-dir", str(config_dir), "regime"]) == 0

    assert "Source: default" in capsys.readouterr().out


def test_regime_no_trades_still_shows_regime(tmp_path, monkeypatch, capsys):
    config_dir = tmp_path / "ci-trading"
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "source": "default"})

    assert cli.main(["--config-dir", str(config_dir), "regime"]) == 0

    output = capsys.readouterr().out
    assert "Current regime: ranging" in output
    assert "No local trades available" in output


def _empty_provider():
    class EmptyProvider:
        def get_vix_current(self):
            return Provenanced(value=None, source="fixture", label="no data available")

        def get_ohlcv(self, *_args, **_kwargs):
            return Provenanced(value=None, source="fixture", label="no data available")

        def get_vix_history(self, *_args, **_kwargs):
            return Provenanced(value=None, source="fixture", label="no data available")

    return EmptyProvider()
