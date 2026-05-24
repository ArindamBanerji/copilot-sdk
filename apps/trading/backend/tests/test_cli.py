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


CSV_BODY = """ticker,direction,entry_price,size,entry_time,strategy_tag
MSFT,buy,400,2,2026-01-01,momentum
SPY,sell,450,1,2026-01-02,hedge
NVDA,buy,900,1,2026-01-03,momentum
TSLA,buy,250,3,2026-01-04,swing
QQQ,sell,390,2,2026-01-05,hedge
"""


def _config_dir(tmp_path: Path) -> Path:
    return tmp_path / "ci-trading"


def _csv_file(tmp_path: Path) -> Path:
    path = tmp_path / "trades.csv"
    path.write_text(CSV_BODY, encoding="utf-8")
    return path


def _run(config_dir: Path, *args: str) -> int:
    return cli.main(["--config-dir", str(config_dir), *args])


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _init_and_import(tmp_path: Path) -> Path:
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    assert _run(config_dir, "import", "--file", str(_csv_file(tmp_path))) == 0
    return config_dir


def _write_journal_trades(config_dir: Path) -> None:
    cli._save_trades(
        [
            {
                "trade_id": "j-1",
                "ticker": "MSFT",
                "direction": "long",
                "pnl": 120.0,
                "category": "trend_following",
                "strategy_tag": "momentum",
            },
            {
                "trade_id": "j-2",
                "ticker": "SPY",
                "direction": "short",
                "pnl": -30.0,
                "category": "mean_reversion",
                "strategy_tag": "hedge",
            },
            {
                "trade_id": "j-3",
                "ticker": "NVDA",
                "direction": "long",
                "pnl": 40.0,
                "category": "trend_following",
                "strategy_tag": "momentum",
            },
        ],
        config_dir,
    )


def test_init_creates_config(tmp_path):
    config_dir = _config_dir(tmp_path)

    assert _run(config_dir, "init") == 0

    assert (config_dir / "config.json").exists()


def test_init_creates_valid_config(tmp_path):
    config_dir = _config_dir(tmp_path)

    assert _run(config_dir, "init") == 0
    config = _read_json(config_dir / "config.json")

    assert config["version"] == "0.1.0"
    assert config["broker"] is None
    assert config["data_dir"] == str(config_dir)
    assert config["created"]


def test_init_idempotent(tmp_path):
    config_dir = _config_dir(tmp_path)

    assert _run(config_dir, "init") == 0
    first = _read_json(config_dir / "config.json")
    assert _run(config_dir, "init") == 0
    second = _read_json(config_dir / "config.json")

    assert second == first


def test_init_creates_empty_trades(tmp_path):
    config_dir = _config_dir(tmp_path)

    assert _run(config_dir, "init") == 0

    assert _read_json(config_dir / "trades.json") == []


def test_import_csv(tmp_path):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0

    assert _run(config_dir, "import", "--file", str(_csv_file(tmp_path))) == 0

    assert len(_read_json(config_dir / "trades.json")) == 5


def test_import_without_init_fails(tmp_path, capsys):
    result = _run(_config_dir(tmp_path), "import", "--file", str(_csv_file(tmp_path)))

    assert result == 1
    assert "not initialized" in capsys.readouterr().err


def test_import_missing_file_fails(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0

    result = _run(config_dir, "import", "--file", str(tmp_path / "missing.csv"))

    assert result == 1
    assert "not found" in capsys.readouterr().err


def test_import_deduplicates(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    csv_file = _csv_file(tmp_path)
    assert _run(config_dir, "init") == 0
    assert _run(config_dir, "import", "--file", str(csv_file)) == 0

    assert _run(config_dir, "import", "--file", str(csv_file)) == 0
    output = capsys.readouterr().out

    assert "Duplicates: 5" in output
    assert len(_read_json(config_dir / "trades.json")) == 5


def test_import_without_file_flag_fails(tmp_path):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0

    assert _run(config_dir, "import") == 1


def test_imported_trades_have_tickers(tmp_path):
    config_dir = _init_and_import(tmp_path)
    trades = _read_json(config_dir / "trades.json")

    assert {trade["ticker"] for trade in trades} == {"MSFT", "SPY", "NVDA", "TSLA", "QQQ"}


def test_imported_trade_ids_match_connector_format(tmp_path):
    config_dir = _init_and_import(tmp_path)
    trade_ids = [trade["trade_id"] for trade in _read_json(config_dir / "trades.json")]

    assert trade_ids == ["csv-1", "csv-2", "csv-3", "csv-4", "csv-5"]
    assert all(trade_id.startswith("csv-") for trade_id in trade_ids)
    assert "csv-00001" not in trade_ids


def test_score_all_trades(tmp_path, capsys):
    config_dir = _init_and_import(tmp_path)

    assert _run(config_dir, "score") == 0
    output = capsys.readouterr().out

    assert "Trades scored: 5" in output
    assert "Factor summary" in output
    assert "Offline factor scoring only" in output


def test_score_single_trade(tmp_path, capsys):
    config_dir = _init_and_import(tmp_path)
    trade_id = _read_json(config_dir / "trades.json")[0]["trade_id"]

    assert _run(config_dir, "score", "--trade-id", trade_id) == 0
    output = capsys.readouterr().out

    assert f"Trade: {trade_id}" in output
    assert "Factor scores" in output


def test_score_unknown_trade_fails(tmp_path, capsys):
    config_dir = _init_and_import(tmp_path)

    assert _run(config_dir, "score", "--trade-id", "missing") == 1

    assert "Trade not found" in capsys.readouterr().err


def test_score_no_trades_fails(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0

    assert _run(config_dir, "score") == 1

    assert "No trades available" in capsys.readouterr().err


def test_trust_with_trades(tmp_path, capsys):
    config_dir = _init_and_import(tmp_path)

    assert _run(config_dir, "trust") == 0
    output = capsys.readouterr().out

    assert "Implemented factors" in output
    assert "Neutral factor count" in output
    assert "variance=" in output


def test_trust_no_trades_fails(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0

    assert _run(config_dir, "trust") == 1

    assert "No trades available" in capsys.readouterr().err


def test_conservation_with_trades(tmp_path, capsys):
    config_dir = _init_and_import(tmp_path)

    assert _run(config_dir, "conservation") == 0
    output = capsys.readouterr().out

    assert "Offline conservation proxy" in output
    assert "Full conservation requires the scoring server" in output
    assert "RED" in output


def test_conservation_no_trades_fails(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0

    assert _run(config_dir, "conservation") == 1

    assert "No trades available" in capsys.readouterr().err


def test_journal_shows_trades(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    _write_journal_trades(config_dir)

    assert _run(config_dir, "journal") == 0
    output = capsys.readouterr().out

    assert "Trades: 3" in output
    assert "MSFT" in output
    assert "Total P&L: 130.00" in output


def test_journal_filter_ticker(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    _write_journal_trades(config_dir)

    assert _run(config_dir, "journal", "--ticker", "msft") == 0
    output = capsys.readouterr().out

    assert "Trades: 1" in output
    assert "MSFT" in output
    assert "SPY" not in output


def test_journal_filter_wins_only(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    _write_journal_trades(config_dir)

    assert _run(config_dir, "journal", "--wins-only") == 0
    output = capsys.readouterr().out

    assert "Trades: 2" in output
    assert "j-1" in output
    assert "j-3" in output
    assert "j-2" not in output


def test_journal_filter_losses_only(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    _write_journal_trades(config_dir)

    assert _run(config_dir, "journal", "--losses-only") == 0
    output = capsys.readouterr().out

    assert "Trades: 1" in output
    assert "j-2" in output
    assert "j-1" not in output


def test_journal_no_trades_message(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0

    assert _run(config_dir, "journal") == 1

    assert "No trades available" in capsys.readouterr().err


def test_journal_limit_controls_output(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    _write_journal_trades(config_dir)

    assert _run(config_dir, "journal", "--limit", "1") == 0
    output = capsys.readouterr().out

    assert "Trades: 3" in output
    assert "j-1" in output
    assert "j-2" not in output


def test_journal_no_match_message(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert _run(config_dir, "init") == 0
    _write_journal_trades(config_dir)

    assert _run(config_dir, "journal", "--ticker", "AAPL") == 0

    assert "No trades match filters." in capsys.readouterr().out


def test_no_command_prints_help(tmp_path, capsys):
    result = cli.main(["--config-dir", str(_config_dir(tmp_path))])

    assert result == 1
    assert "usage:" in capsys.readouterr().out


def test_help_flag():
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])

    assert exc.value.code == 0


def test_unknown_command_exits(tmp_path):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--config-dir", str(_config_dir(tmp_path)), "unknown"])

    assert exc.value.code == 2


def test_init_help():
    with pytest.raises(SystemExit) as exc:
        cli.main(["init", "--help"])

    assert exc.value.code == 0
