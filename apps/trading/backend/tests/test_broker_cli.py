from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import cli  # noqa: E402
from app.brokers import MockBroker, OrderRequest, OrderSide  # noqa: E402


def _config_dir(tmp_path: Path) -> Path:
    return tmp_path / "ci-trading"


def _run(config_dir: Path, *args: str) -> int:
    return cli.main(["--config-dir", str(config_dir), *args])


def _read_trades(config_dir: Path) -> list[dict]:
    return json.loads((config_dir / "trades.json").read_text(encoding="utf-8"))


def test_order_command_with_mock(capsys, tmp_path):
    result = _run(_config_dir(tmp_path), "order", "AAPL", "buy", "10", "--broker", "mock")

    assert result == 0
    output = capsys.readouterr().out
    assert "Order submitted" in output
    assert "AAPL" in output


def test_limit_order_command_with_mock(capsys, tmp_path):
    result = _run(
        _config_dir(tmp_path),
        "order",
        "AAPL",
        "buy",
        "10",
        "--type",
        "limit",
        "--limit-price",
        "150",
        "--broker",
        "mock",
    )

    assert result == 0
    assert "150.00" in capsys.readouterr().out


def test_orders_command_with_shared_mock(monkeypatch, capsys, tmp_path):
    broker = MockBroker()
    broker.place_order(OrderRequest(ticker="AAPL", side=OrderSide.BUY, qty=1))
    monkeypatch.setattr(cli, "_get_broker", lambda _name: broker)

    assert _run(_config_dir(tmp_path), "orders", "--status", "filled", "--broker", "mock") == 0

    output = capsys.readouterr().out
    assert "Order ID" in output
    assert "AAPL" in output


def test_positions_command_with_shared_mock(monkeypatch, capsys, tmp_path):
    broker = MockBroker()
    broker.place_order(OrderRequest(ticker="AAPL", side=OrderSide.BUY, qty=2))
    monkeypatch.setattr(cli, "_get_broker", lambda _name: broker)

    assert _run(_config_dir(tmp_path), "positions", "--broker", "mock") == 0

    assert "AAPL" in capsys.readouterr().out


def test_account_command_with_mock(capsys, tmp_path):
    assert _run(_config_dir(tmp_path), "account", "--broker", "mock") == 0

    output = capsys.readouterr().out
    assert "Cash:" in output
    assert "Equity:" in output
    assert "Buying power:" in output


def test_sync_writes_filled_orders_to_journal(monkeypatch, tmp_path):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    broker = MockBroker()
    broker.place_order(OrderRequest(ticker="AAPL", side=OrderSide.BUY, qty=2))
    monkeypatch.setattr(cli, "_get_broker", lambda _name: broker)

    assert _run(config_dir, "sync", "--broker", "alpaca") == 0

    trades = _read_trades(config_dir)
    assert len(trades) == 1
    assert trades[0]["trade_id"].startswith("alpaca_")
    assert trades[0]["ticker"] == "AAPL"
    assert trades[0]["direction"] == "long"
    assert trades[0]["category"] == "uncategorized"
    assert trades[0]["metadata"]["source"] == "alpaca"


def test_sync_is_idempotent(monkeypatch, tmp_path):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    broker = MockBroker()
    broker.place_order(OrderRequest(ticker="AAPL", side=OrderSide.BUY, qty=2))
    monkeypatch.setattr(cli, "_get_broker", lambda _name: broker)

    assert _run(config_dir, "sync", "--broker", "alpaca") == 0
    assert _run(config_dir, "sync", "--broker", "alpaca") == 0

    assert len(_read_trades(config_dir)) == 1


def test_sync_dry_run_writes_nothing(monkeypatch, capsys, tmp_path):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    broker = MockBroker()
    broker.place_order(OrderRequest(ticker="AAPL", side=OrderSide.BUY, qty=2))
    monkeypatch.setattr(cli, "_get_broker", lambda _name: broker)

    assert _run(config_dir, "sync", "--dry-run", "--broker", "alpaca") == 0

    assert "Would sync: 1" in capsys.readouterr().out
    assert _read_trades(config_dir) == []


def test_order_without_credentials_returns_friendly_error(monkeypatch, capsys, tmp_path):
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)

    result = _run(_config_dir(tmp_path), "order", "AAPL", "buy", "1")

    assert result == 1
    assert "Alpaca credentials are not configured" in capsys.readouterr().err


def test_non_broker_command_does_not_call_get_broker(monkeypatch, tmp_path):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0

    def fail(_name: str):
        raise AssertionError("non-broker command touched broker factory")

    monkeypatch.setattr(cli, "_get_broker", fail)

    assert _run(config_dir, "journal") == 1


def test_non_broker_command_rejects_broker_flag(tmp_path):
    with pytest.raises(SystemExit) as exc:
        _run(_config_dir(tmp_path), "journal", "--broker", "mock")

    assert exc.value.code == 2
