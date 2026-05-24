from __future__ import annotations

import cli
from app.routers import data_import
from app.services import correlation as correlation_module
from app.services.correlation import CorrelationService, _extract_tickers


def _trades(*tickers: str) -> list[dict]:
    return [
        {"trade_id": f"t-{index}", "ticker": ticker, "category": "trend_following"}
        for index, ticker in enumerate(tickers, start=1)
    ]


def _returns():
    return {
        "AAPL": [0.01, 0.02, -0.01, 0.03, 0.01],
        "MSFT": [0.011, 0.019, -0.012, 0.028, 0.012],
        "SPY": [-0.01, -0.02, 0.01, -0.03, -0.01],
    }


def _config_dir(tmp_path):
    return tmp_path / "ci-trading"


def _mock_fetch(monkeypatch, payload=None):
    monkeypatch.setattr(correlation_module, "YFINANCE_AVAILABLE", True)
    monkeypatch.setattr(CorrelationService, "_fetch_returns", lambda self, tickers: payload or _returns())


def test_insufficient_single_ticker():
    payload = CorrelationService().compute(_trades("AAPL"))

    assert payload["source"] == "insufficient_data"
    assert payload["matrix"] == []


def test_insufficient_no_tickers():
    payload = CorrelationService().compute([{"trade_id": "t-1"}])

    assert payload["source"] == "insufficient_data"
    assert payload["tickers"] == []


def test_extract_tickers_unique():
    assert _extract_tickers(_trades("aapl", "MSFT", "AAPL", "")) == ["AAPL", "MSFT"]


def test_extract_tickers_caps_at_20():
    tickers = _extract_tickers(_trades(*[f"T{i}" for i in range(25)]))

    assert len(tickers) == 20
    assert tickers[-1] == "T19"


def test_compute_returns_matrix_shape(monkeypatch):
    _mock_fetch(monkeypatch)

    payload = CorrelationService(window_days=5).compute(_trades("AAPL", "MSFT", "SPY"))

    assert len(payload["matrix"]) == 3
    assert all(len(row) == 3 for row in payload["matrix"])


def test_matrix_diagonal_is_1(monkeypatch):
    _mock_fetch(monkeypatch)

    payload = CorrelationService(window_days=5).compute(_trades("AAPL", "MSFT", "SPY"))

    assert [row[index] for index, row in enumerate(payload["matrix"])] == [1.0, 1.0, 1.0]


def test_matrix_symmetric(monkeypatch):
    _mock_fetch(monkeypatch)

    matrix = CorrelationService(window_days=5).compute(_trades("AAPL", "MSFT", "SPY"))["matrix"]

    assert matrix[0][1] == matrix[1][0]
    assert matrix[0][2] == matrix[2][0]


def test_avg_correlation_computed(monkeypatch):
    _mock_fetch(monkeypatch, {"AAPL": [1, 2, 3, 4], "MSFT": [1, 2, 3, 4], "SPY": [4, 3, 2, 1]})

    payload = CorrelationService(window_days=4).compute(_trades("AAPL", "MSFT", "SPY"))

    assert payload["avg_correlation"] == -0.3333


def test_max_pair_selected(monkeypatch):
    _mock_fetch(monkeypatch)

    payload = CorrelationService(window_days=5).compute(_trades("AAPL", "MSFT", "SPY"))

    assert payload["max_pair"]["ticker_a"] in {"AAPL", "MSFT", "SPY"}
    assert abs(payload["max_pair"]["correlation"]) >= abs(payload["pairs"][-1]["correlation"])


def test_alert_warning_above_06(monkeypatch):
    _mock_fetch(monkeypatch, {"AAPL": [1, 2, 3, 4, 5], "MSFT": [1, 2, 1, 4, 3]})

    alerts = CorrelationService(window_days=5).compute(_trades("AAPL", "MSFT"))["alerts"]

    assert any(alert["level"] == "warning" for alert in alerts)


def test_alert_critical_above_08(monkeypatch):
    _mock_fetch(monkeypatch, {"AAPL": [1, 2, 3], "MSFT": [1, 2, 3], "SPY": [1, 2, 3]})

    alerts = CorrelationService(window_days=3).compute(_trades("AAPL", "MSFT", "SPY"))["alerts"]

    assert alerts[0]["level"] == "critical"


def test_no_alert_below_06(monkeypatch):
    _mock_fetch(monkeypatch, {"AAPL": [1, 2, 3, 4, 5], "MSFT": [1, 5, 2, 4, 3]})

    alerts = CorrelationService(window_days=5).compute(_trades("AAPL", "MSFT"))["alerts"]

    assert alerts == []


def test_pair_alert_for_high_correlation(monkeypatch):
    _mock_fetch(monkeypatch, {"AAPL": [1, 2, 3], "MSFT": [1, 2, 3], "SPY": [3, 2, 1]})

    alerts = CorrelationService(window_days=3).compute(_trades("AAPL", "MSFT", "SPY"))["alerts"]

    assert any("AAPL" in alert.get("message", "") or "MSFT" in alert.get("message", "") for alert in alerts)


def test_pairs_sorted_by_abs_correlation(monkeypatch):
    _mock_fetch(monkeypatch)

    pairs = CorrelationService(window_days=5).compute(_trades("AAPL", "MSFT", "SPY"))["pairs"]

    assert [abs(pair["correlation"]) for pair in pairs] == sorted(
        [abs(pair["correlation"]) for pair in pairs],
        reverse=True,
    )


def test_yfinance_unavailable_returns_insufficient(monkeypatch):
    monkeypatch.setattr(correlation_module, "YFINANCE_AVAILABLE", False)

    payload = CorrelationService().compute(_trades("AAPL", "MSFT"))

    assert payload["source"] == "insufficient_data"
    assert "yfinance" in payload["reason"]


def test_numpy_unavailable_returns_insufficient(monkeypatch):
    monkeypatch.setattr(correlation_module, "YFINANCE_AVAILABLE", True)
    monkeypatch.setattr(correlation_module, "NUMPY_AVAILABLE", False)

    payload = CorrelationService().compute(_trades("AAPL", "MSFT"))

    assert payload["source"] == "insufficient_data"
    assert "numpy" in payload["reason"]


def test_window_parameter_used():
    assert CorrelationService(window_days=13).window_days == 13


def test_perfectly_correlated_returns_near_1(monkeypatch):
    _mock_fetch(monkeypatch, {"AAPL": [1, 2, 3, 4], "MSFT": [2, 4, 6, 8]})

    payload = CorrelationService(window_days=4).compute(_trades("AAPL", "MSFT"))

    assert payload["pairs"][0]["correlation"] == 1.0


def test_inverse_correlated_returns_near_neg1(monkeypatch):
    _mock_fetch(monkeypatch, {"AAPL": [1, 2, 3, 4], "SPY": [4, 3, 2, 1]})

    payload = CorrelationService(window_days=4).compute(_trades("AAPL", "SPY"))

    assert payload["pairs"][0]["correlation"] == -1.0


def test_constant_series_nan_handled(monkeypatch):
    _mock_fetch(monkeypatch, {"AAPL": [0, 0, 0, 0], "MSFT": [1, 2, 3, 4]})

    payload = CorrelationService(window_days=4).compute(_trades("AAPL", "MSFT"))

    assert payload["matrix"][0][0] == 1.0
    assert payload["matrix"][0][1] == 0.0


def test_correlation_endpoint_returns_200(client, monkeypatch):
    data_import._trade_store_ref.clear()
    data_import._trade_store_ref.extend(_trades("AAPL", "MSFT"))
    monkeypatch.setattr(CorrelationService, "compute", lambda self, trades: {"source": "insufficient_data", "window_days": self.window_days, "tickers": ["AAPL", "MSFT"]})

    response = client.get("/api/trading/correlation")

    assert response.status_code == 200
    assert response.json()["tickers"] == ["AAPL", "MSFT"]


def test_correlation_no_trades_returns_insufficient(client):
    data_import._trade_store_ref.clear()

    payload = client.get("/api/trading/correlation").json()

    assert payload["source"] == "insufficient_data"


def test_correlation_endpoint_window_param(client, monkeypatch):
    data_import._trade_store_ref.clear()
    data_import._trade_store_ref.extend(_trades("AAPL", "MSFT"))
    monkeypatch.setattr(CorrelationService, "compute", lambda self, trades: {"source": "insufficient_data", "window_days": self.window_days, "tickers": []})

    payload = client.get("/api/trading/correlation?window=12").json()

    assert payload["window_days"] == 12


def test_correlation_command_output(tmp_path, monkeypatch, capsys):
    config_dir = _config_dir(tmp_path)
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    cli._save_trades(_trades("AAPL", "MSFT"), config_dir)
    monkeypatch.setattr(
        CorrelationService,
        "compute",
        lambda self, trades: {
            "source": "yfinance",
            "window_days": self.window_days,
            "tickers": ["AAPL", "MSFT"],
            "avg_correlation": 0.75,
            "max_pair": {"ticker_a": "AAPL", "ticker_b": "MSFT", "correlation": 0.75},
            "alerts": [],
            "pairs": [{"ticker_a": "AAPL", "ticker_b": "MSFT", "correlation": 0.75}],
        },
    )

    assert cli.main(["--config-dir", str(config_dir), "correlation", "--window", "11"]) == 0

    output = capsys.readouterr().out
    assert "Correlation monitor (11 days)" in output
    assert "AAPL/MSFT" in output


def test_correlation_command_no_trades_fails(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0

    assert cli.main(["--config-dir", str(config_dir), "correlation"]) == 1

    assert "No trades" in capsys.readouterr().err


def test_correlation_command_insufficient_data(tmp_path, monkeypatch, capsys):
    config_dir = _config_dir(tmp_path)
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    cli._save_trades(_trades("AAPL", "MSFT"), config_dir)
    monkeypatch.setattr(
        CorrelationService,
        "compute",
        lambda self, trades: {"source": "insufficient_data", "reason": "mock insufficient", "window_days": self.window_days},
    )

    assert cli.main(["--config-dir", str(config_dir), "correlation"]) == 0

    assert "mock insufficient" in capsys.readouterr().out
