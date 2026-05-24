from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import cli  # noqa: E402
from app.connectors.csv_connector import CSVConnector  # noqa: E402
from app.connectors import ibkr_connector  # noqa: E402


def _config_dir(tmp_path: Path) -> Path:
    return tmp_path / "ci-trading"


def _run(config_dir: Path, *args: str) -> int:
    return cli.main(["--config-dir", str(config_dir), *args])


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_trades(config_dir: Path) -> None:
    cli._save_trades(
        [
            {
                "trade_id": "t-1",
                "ticker": "MSFT",
                "direction": "long",
                "entry_price": 100,
                "pnl": 25.5,
                "category": "trend_following",
                "strategy_tag": "momentum",
            },
            {
                "trade_id": "t-2",
                "ticker": "SPY",
                "direction": "short",
                "entry_price": 400,
                "pnl": -10,
                "category": "mean_reversion",
                "strategy_tag": "hedge",
            },
        ],
        config_dir,
    )


def _csv(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "trades.csv"
    path.write_text(body, encoding="utf-8")
    return path


def test_ibkr_not_available_when_uninstalled():
    if ibkr_connector.IB_AVAILABLE:
        assert ibkr_connector.IBKRConnector.is_available() is True
        return
    assert ibkr_connector.IBKRConnector.is_available() is False
    try:
        ibkr_connector.IBKRConnector()
    except RuntimeError as exc:
        assert "pip install ib_insync" in str(exc)
    else:
        raise AssertionError("IBKRConnector should require ib_insync when unavailable")


def test_ibkr_is_available_static():
    assert isinstance(ibkr_connector.IBKRConnector.is_available(), bool)


def test_ibkr_connect_failure_returns_false(monkeypatch):
    class FakeIB:
        def isConnected(self):
            return False

        def connect(self, *_args, **_kwargs):
            raise RuntimeError("no gateway")

    monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)
    monkeypatch.setattr(ibkr_connector, "IB", FakeIB)

    connector = ibkr_connector.IBKRConnector()

    assert connector.connect() is False


def test_ibkr_trade_id_format(monkeypatch):
    class FakeIB:
        def __init__(self):
            self.connected = False

        def isConnected(self):
            return self.connected

        def connect(self, *_args, **_kwargs):
            self.connected = True
            return None

        def disconnect(self):
            self.connected = False
            return None

        def fills(self):
            execution = SimpleNamespace(
                execId="abc123",
                side="BOT",
                price=101.5,
                shares=2,
                time=datetime.now().isoformat(),
            )
            contract = SimpleNamespace(symbol="msft", secType="STK")
            report = SimpleNamespace(commission=1.25, realizedPNL=12.5)
            return [SimpleNamespace(execution=execution, contract=contract, commissionReport=report)]

    monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)
    monkeypatch.setattr(ibkr_connector, "IB", FakeIB)

    trades = ibkr_connector.IBKRConnector().import_trades(days=365)

    assert trades[0].trade_id == "ibkr-abc123"
    assert trades[0].direction == "long"
    assert trades[0].ticker == "MSFT"


def test_auto_detect_standard_headers(tmp_path):
    path = _csv(tmp_path, "symbol,side,price,qty,date\nmsft,buy,100,2,2026-01-01\n")

    trades = CSVConnector().import_flexible(str(path))

    assert len(trades) == 1
    assert trades[0].ticker == "MSFT"


def test_auto_detect_thinkorswim_headers(tmp_path):
    path = _csv(tmp_path, "Exec ID,Symbol,Side,Price,Qty,Exec Time\n1,AAPL,BOT,200,3,01/02/2026\n")

    trades = CSVConnector().import_flexible(str(path), broker_preset="thinkorswim")

    assert trades[0].trade_id == "1"
    assert trades[0].direction == "long"


def test_preset_webull(tmp_path):
    path = _csv(tmp_path, "Order ID,Symbol,Side,Filled Price,Filled,Filled Time\nw1,NVDA,SELL,900,1,2026-01-03\n")

    trades = CSVConnector().import_flexible(str(path), broker_preset="webull")

    assert trades[0].trade_id == "w1"
    assert trades[0].direction == "short"


def test_preset_robinhood(tmp_path):
    path = _csv(tmp_path, "Activity ID,Instrument,Trans Code,Price,Quantity,Activity Date\nr1,TSLA,B,250,4,2026/01/04\n")

    trades = CSVConnector().import_flexible(str(path), broker_preset="robinhood")

    assert trades[0].trade_id == "r1"
    assert trades[0].direction == "long"


def test_custom_column_map(tmp_path):
    path = _csv(tmp_path, "ticker_col,side_col,fill_col,qty_col\nqqq,sell,390,2\n")

    trades = CSVConnector().import_flexible(
        str(path),
        column_map={
            "ticker": "ticker_col",
            "direction": "side_col",
            "entry_price": "fill_col",
            "size": "qty_col",
        },
    )

    assert trades[0].ticker == "QQQ"
    assert trades[0].direction == "short"


def test_dollar_signs_stripped(tmp_path):
    path = _csv(tmp_path, "ticker,direction,entry_price,size,fees,pnl\nMSFT,buy,$100.50,1,$1.25,$12.75\n")

    trade = CSVConnector().import_flexible(str(path))[0]

    assert trade.entry_price == 100.5
    assert trade.fees == 1.25
    assert trade.pnl == 12.75


def test_commas_in_numbers_handled(tmp_path):
    path = _csv(tmp_path, 'ticker,direction,entry_price,size,pnl\nMSFT,buy,"1,000.50",2,"1,250.25"\n')

    trade = CSVConnector().import_flexible(str(path))[0]

    assert trade.entry_price == 1000.5
    assert trade.pnl == 1250.25


def test_multiple_date_formats(tmp_path):
    path = _csv(tmp_path, "ticker,direction,entry_price,size,entry_time\nMSFT,buy,100,1,01/02/26\nSPY,sell,400,1,2026-01-03 10:11:12\n")

    trades = CSVConnector().import_flexible(str(path))

    assert [trade.entry_time.year for trade in trades] == [2026, 2026]


def test_missing_ticker_skips_row(tmp_path):
    path = _csv(tmp_path, "ticker,direction,entry_price,size\n,buy,100,1\nMSFT,buy,100,1\n")

    trades = CSVConnector().import_flexible(str(path))

    assert len(trades) == 1
    assert trades[0].ticker == "MSFT"


def test_direction_buy_maps_long(tmp_path):
    path = _csv(tmp_path, "ticker,direction,entry_price,size\nMSFT,BOT,100,1\n")

    assert CSVConnector().import_flexible(str(path))[0].direction == "long"


def test_direction_sell_maps_short(tmp_path):
    path = _csv(tmp_path, "ticker,direction,entry_price,size\nMSFT,SLD,100,1\n")

    assert CSVConnector().import_flexible(str(path))[0].direction == "short"


def test_import_from_file_backward_compatible(tmp_path):
    path = _csv(tmp_path, "ticker,direction,entry_price,size,entry_time\nMSFT,buy,100,1,2026-01-01\n")

    trade = CSVConnector().import_from_file(str(path))[0]

    assert trade.trade_id == "csv-1"
    assert trade.broker == "csv"


def test_import_csv_with_preset(tmp_path):
    config_dir = _config_dir(tmp_path)
    path = _csv(tmp_path, "Order ID,Symbol,Side,Filled Price,Filled,Filled Time\nw1,NVDA,BUY,900,1,2026-01-03\n")
    assert _run(config_dir, "init") == 0

    assert _run(config_dir, "import", "--file", str(path), "--preset", "webull") == 0

    assert _read_json(config_dir / "trades.json")[0]["trade_id"] == "w1"


def test_import_ibkr_unavailable_fails(tmp_path, capsys):
    if ibkr_connector.IB_AVAILABLE:
        return
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0

    assert _run(config_dir, "import", "--broker", "ibkr") == 1

    assert "pip install ib_insync" in capsys.readouterr().err


def test_export_json(tmp_path):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    _write_trades(config_dir)
    output = tmp_path / "out.json"

    assert _run(config_dir, "export", "--format", "json", "--output", str(output)) == 0

    assert len(_read_json(output)) == 2


def test_export_csv(tmp_path):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    _write_trades(config_dir)
    output = tmp_path / "out.csv"

    assert _run(config_dir, "export", "--format", "csv", "--output", str(output)) == 0

    with output.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert rows[0]["trade_id"] == "t-1"


def test_export_no_trades_fails(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0

    assert _run(config_dir, "export") == 1

    assert "No trades to export" in capsys.readouterr().err


def test_backup_creates_file(tmp_path):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    _write_trades(config_dir)

    assert _run(config_dir, "backup") == 0

    assert list((config_dir / "backup").glob("trading-backup-*.json"))


def test_backup_includes_trades(tmp_path):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    _write_trades(config_dir)

    assert _run(config_dir, "backup") == 0
    backup = _read_json(next((config_dir / "backup").glob("trading-backup-*.json")))

    assert backup["trade_count"] == 2
    assert len(backup["trades"]) == 2


def test_restore_loads_trades(tmp_path):
    source = _config_dir(tmp_path) / "source"
    target = _config_dir(tmp_path) / "target"
    assert _run(source, "init") == 0
    _write_trades(source)
    assert _run(source, "backup") == 0
    backup = next((source / "backup").glob("trading-backup-*.json"))
    assert _run(target, "init") == 0

    assert _run(target, "restore", "--from", str(backup)) == 0

    assert len(_read_json(target / "trades.json")) == 2


def test_restore_missing_file_fails(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0

    assert _run(config_dir, "restore", "--from", str(tmp_path / "missing.json")) == 1

    assert "Backup file not found" in capsys.readouterr().err


def test_backup_restore_roundtrip(tmp_path):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    _write_trades(config_dir)
    assert _run(config_dir, "backup") == 0
    backup = next((config_dir / "backup").glob("trading-backup-*.json"))
    cli._save_trades([], config_dir)

    assert _run(config_dir, "restore", "--from", str(backup)) == 0

    assert [trade["trade_id"] for trade in _read_json(config_dir / "trades.json")] == ["t-1", "t-2"]


def test_retag_changes_category(tmp_path):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    _write_trades(config_dir)

    assert _run(config_dir, "retag", "--trade-id", "t-1", "--category", "event_driven") == 0

    assert _read_json(config_dir / "trades.json")[0]["category"] == "event_driven"


def test_retag_unknown_trade_fails(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    _write_trades(config_dir)

    assert _run(config_dir, "retag", "--trade-id", "missing", "--category", "event_driven") == 1

    assert "Trade not found" in capsys.readouterr().err


def test_retag_persists_to_disk(tmp_path):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    _write_trades(config_dir)

    assert _run(config_dir, "retag", "--trade-id", "t-2", "--category", "scalp_intraday") == 0

    reloaded = cli._load_trades(config_dir)
    assert reloaded[1]["category"] == "scalp_intraday"


def test_ibkr_old_fill_ignored(monkeypatch):
    class FakeIB:
        def __init__(self):
            self.connected = False

        def isConnected(self):
            return self.connected

        def connect(self, *_args, **_kwargs):
            self.connected = True
            return None

        def disconnect(self):
            self.connected = False
            return None

        def fills(self):
            execution = SimpleNamespace(
                execId="old",
                side="BOT",
                price=101.5,
                shares=2,
                time=(datetime.now() - timedelta(days=900)).isoformat(),
            )
            contract = SimpleNamespace(symbol="MSFT", secType="STK")
            return [SimpleNamespace(execution=execution, contract=contract, commissionReport=None)]

    monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)
    monkeypatch.setattr(ibkr_connector, "IB", FakeIB)

    assert ibkr_connector.IBKRConnector().import_trades(days=365) == []


def test_ibkr_import_handles_timezone_aware_execution_time(monkeypatch):
    class FakeIB:
        def __init__(self):
            self.connected = False

        def isConnected(self):
            return self.connected

        def connect(self, *_args, **_kwargs):
            self.connected = True
            return None

        def disconnect(self):
            self.connected = False
            return None

        def fills(self):
            execution = SimpleNamespace(
                execId="aware",
                side="BOT",
                price=101.5,
                shares=2,
                time=datetime.now(timezone.utc).isoformat(),
            )
            contract = SimpleNamespace(symbol="MSFT", secType="STK")
            return [SimpleNamespace(execution=execution, contract=contract, commissionReport=None)]

    monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)
    monkeypatch.setattr(ibkr_connector, "IB", FakeIB)

    trades = ibkr_connector.IBKRConnector().import_trades(days=365)

    assert trades[0].trade_id == "ibkr-aware"
    assert trades[0].direction == "long"
    assert trades[0].ticker == "MSFT"
    assert trades[0].entry_time.tzinfo is None


def test_ibkr_import_filters_old_timezone_aware_execution_time(monkeypatch):
    class FakeIB:
        def __init__(self):
            self.connected = False

        def isConnected(self):
            return self.connected

        def connect(self, *_args, **_kwargs):
            self.connected = True
            return None

        def disconnect(self):
            self.connected = False
            return None

        def fills(self):
            execution = SimpleNamespace(
                execId="old-aware",
                side="BOT",
                price=101.5,
                shares=2,
                time=(datetime.now(timezone.utc) - timedelta(days=900)).isoformat(),
            )
            contract = SimpleNamespace(symbol="MSFT", secType="STK")
            return [SimpleNamespace(execution=execution, contract=contract, commissionReport=None)]

    monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)
    monkeypatch.setattr(ibkr_connector, "IB", FakeIB)

    assert ibkr_connector.IBKRConnector().import_trades(days=365) == []


def test_ibkr_import_skips_unparseable_execution_time(monkeypatch):
    class FakeIB:
        def __init__(self):
            self.connected = False

        def isConnected(self):
            return self.connected

        def connect(self, *_args, **_kwargs):
            self.connected = True
            return None

        def disconnect(self):
            self.connected = False
            return None

        def fills(self):
            execution = SimpleNamespace(
                execId="bad-time",
                side="BOT",
                price=101.5,
                shares=2,
                time="not a timestamp",
            )
            contract = SimpleNamespace(symbol="MSFT", secType="STK")
            return [SimpleNamespace(execution=execution, contract=contract, commissionReport=None)]

    monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)
    monkeypatch.setattr(ibkr_connector, "IB", FakeIB)

    assert ibkr_connector.IBKRConnector().import_trades(days=365) == []


def test_ibkr_import_parses_ibkr_execution_time_format(monkeypatch):
    class FakeIB:
        def __init__(self):
            self.connected = False

        def isConnected(self):
            return self.connected

        def connect(self, *_args, **_kwargs):
            self.connected = True
            return None

        def disconnect(self):
            self.connected = False
            return None

        def fills(self):
            execution = SimpleNamespace(
                execId="ib-format",
                side="SLD",
                price=101.5,
                shares=2,
                time=datetime.now(timezone.utc).strftime("%Y%m%d  %H:%M:%S"),
            )
            contract = SimpleNamespace(symbol="SPY", secType="STK")
            return [SimpleNamespace(execution=execution, contract=contract, commissionReport=None)]

    monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)
    monkeypatch.setattr(ibkr_connector, "IB", FakeIB)

    trades = ibkr_connector.IBKRConnector().import_trades(days=365)

    assert trades[0].trade_id == "ibkr-ib-format"
    assert trades[0].direction == "short"
