from __future__ import annotations

from datetime import datetime, timezone

import cli
from app.routers import data_import
from app.routers import vix_timing as vix_timing_router
from app.services.vix_timing import VIXTimingService, _bucket_hold_period, _bucket_vix
from copilot_sdk.evidence.provenance import Provenanced


def _trade(
    trade_id: str,
    entry_time: str,
    exit_time: str,
    pnl: float,
    *,
    vix: float | None = None,
) -> dict:
    trade = {
        "trade_id": trade_id,
        "ticker": "SPY",
        "category": "trend_following",
        "entry_time": entry_time,
        "exit_time": exit_time,
        "pnl": pnl,
        "metadata": {},
    }
    if vix is not None:
        trade["metadata"]["vix_at_entry"] = vix
    return trade


def _config_dir(tmp_path):
    return tmp_path / "ci-trading"


def _many_trades(prefix: str, count: int, entry: str, exit_: str, wins: int) -> list[dict]:
    rows = []
    for index in range(count):
        rows.append(_trade(f"{prefix}-{index}", entry, exit_, 1.0 if index < wins else -1.0))
    return rows


class _FakeVixProvider:
    def __init__(self, payload: dict[str, float], calls: dict[str, int] | None = None):
        self._payload = payload
        self._calls = calls

    def get_vix_history(self, start: str, end: str):
        if self._calls is not None:
            self._calls["count"] += 1
        return Provenanced(value=self._payload, source="live")


def test_hold_intraday_under_8h():
    assert _bucket_hold_period("2026-01-01T09:00:00", "2026-01-01T16:30:00") == "intraday"


def test_hold_1_3_days():
    assert _bucket_hold_period("2026-01-01T09:00:00", "2026-01-02T09:00:00") == "1_3_days"


def test_hold_1_2_weeks():
    assert _bucket_hold_period("2026-01-01T09:00:00", "2026-01-05T09:00:00") == "1_2_weeks"


def test_hold_2_plus_weeks():
    assert _bucket_hold_period("2026-01-01T09:00:00", "2026-01-20T09:00:00") == "2_plus_weeks"


def test_hold_missing_times_returns_none():
    assert _bucket_hold_period(None, "2026-01-01T09:00:00") is None


def test_hold_negative_duration_returns_none():
    assert _bucket_hold_period("2026-01-02T09:00:00", "2026-01-01T09:00:00") is None


def test_hold_zero_duration_is_intraday():
    assert _bucket_hold_period("2026-01-01T09:00:00", "2026-01-01T09:00:00") == "intraday"


def test_hold_timezone_aware_datetime_safe():
    entry = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
    exit_ = "2026-01-01T13:00:00-05:00"

    assert _bucket_hold_period(entry, exit_) == "1_3_days"


def test_vix_bucket_low():
    assert _bucket_vix(19.99) == "low"


def test_vix_bucket_medium():
    assert _bucket_vix(25) == "medium"


def test_vix_bucket_high():
    assert _bucket_vix(35) == "high"


def test_vix_bucket_boundary_20():
    assert _bucket_vix(20) == "medium"


def test_vix_bucket_boundary_30():
    assert _bucket_vix(30) == "high"


def test_analyze_returns_matrix_shape():
    payload = VIXTimingService().analyze(
        [_trade("t1", "2026-01-01T09:00:00", "2026-01-01T12:00:00", 1.0)],
        {"2026-01-01": 18.0},
    )

    assert set(payload["matrix"]) == {"intraday", "1_3_days", "1_2_weeks", "2_plus_weeks"}
    assert set(payload["matrix"]["intraday"]) == {"low", "medium", "high"}


def test_analyze_accuracy_computed():
    payload = VIXTimingService().analyze(
        [
            _trade("t1", "2026-01-01T09:00:00", "2026-01-01T12:00:00", 1.0),
            _trade("t2", "2026-01-01T10:00:00", "2026-01-01T12:00:00", -1.0),
        ],
        {"2026-01-01": 18.0},
    )

    assert payload["matrix"]["intraday"]["low"]["accuracy"] == 0.5


def test_analyze_best_worst_identified():
    payload = VIXTimingService().analyze(
        [
            _trade("t1", "2026-01-01T09:00:00", "2026-01-01T12:00:00", 1.0),
            _trade("t2", "2026-01-02T09:00:00", "2026-01-03T09:00:00", -1.0),
        ],
        {"2026-01-01": 18.0, "2026-01-02": 25.0},
    )

    assert payload["best_bucket"]["hold_bucket"] == "intraday"
    assert payload["worst_bucket"]["hold_bucket"] == "1_3_days"


def test_analyze_empty_trades():
    payload = VIXTimingService().analyze([])

    assert payload["total_analyzed"] == 0
    assert payload["total_skipped"] == 0
    assert payload["best_bucket"] is None


def test_analyze_no_vix_data_skips_all():
    payload = VIXTimingService().analyze([
        _trade("t1", "2026-01-01T09:00:00", "2026-01-01T12:00:00", 1.0),
    ])

    assert payload["total_analyzed"] == 0
    assert payload["total_skipped"] == 1


def test_analyze_uses_metadata_vix_fallback():
    payload = VIXTimingService().analyze([
        _trade("t1", "2026-01-01T09:00:00", "2026-01-01T12:00:00", 1.0, vix=31.0),
    ])

    assert payload["matrix"]["intraday"]["high"]["count"] == 1


def test_analyze_timezone_aware_entry_uses_same_local_vix_date_as_regime_lookup():
    payload = VIXTimingService().analyze(
        [
            _trade(
                "t1",
                "2026-01-15T23:30:00-05:00",
                "2026-01-16T02:30:00-05:00",
                1.0,
            ),
        ],
        {"2026-01-15": 35.0},
    )

    assert payload["total_analyzed"] == 1
    assert payload["total_skipped"] == 0
    assert payload["matrix"]["intraday"]["high"]["count"] == 1


def test_recommendations_extend_holds():
    trades = [
        *_many_trades("intra", 5, "2026-01-01T09:00:00", "2026-01-01T12:00:00", 1),
        *_many_trades("swing", 5, "2026-01-02T09:00:00", "2026-01-07T09:00:00", 5),
    ]
    payload = VIXTimingService().analyze(trades, {"2026-01-01": 35.0, "2026-01-02": 35.0})

    assert any("1-2 week holds have outperformed" in item for item in payload["recommendations"])


def test_recommendations_quick_exits_edge():
    trades = [
        *_many_trades("intra", 5, "2026-01-01T09:00:00", "2026-01-01T12:00:00", 5),
        *_many_trades("swing", 5, "2026-01-02T09:00:00", "2026-01-07T09:00:00", 1),
    ]
    payload = VIXTimingService().analyze(trades, {"2026-01-01": 35.0, "2026-01-02": 35.0})

    assert any("intraday holds have outperformed" in item for item in payload["recommendations"])


def test_recommendations_insufficient_data():
    payload = VIXTimingService().analyze([
        _trade("t1", "2026-01-01T09:00:00", "2026-01-01T12:00:00", 1.0, vix=18.0),
    ])

    assert payload["recommendations"] == [
        "Insufficient VIX timing history for a reliable hold-period observation."
    ]


def test_vix_timing_returns_200(client, monkeypatch):
    data_import._trade_store_ref.clear()
    data_import._trade_store_ref.append(_trade("t1", "2026-01-01T09:00:00", "2026-01-01T12:00:00", 1.0))
    monkeypatch.setattr(vix_timing_router, "_provider", _FakeVixProvider({"2026-01-01": 18.0}))

    response = client.get("/api/trading/vix-timing")

    assert response.status_code == 200
    assert response.json()["total_analyzed"] == 1


def test_vix_timing_no_trades_returns_empty_or_all_skipped(client):
    data_import._trade_store_ref.clear()

    payload = client.get("/api/trading/vix-timing").json()

    assert payload["total_analyzed"] == 0
    assert payload["matrix"]["intraday"]["low"]["count"] == 0


def test_vix_timing_uses_provider_vix_mocked(client, monkeypatch):
    data_import._trade_store_ref.clear()
    data_import._trade_store_ref.append(_trade("t1", "2026-01-01T09:00:00", "2026-01-01T12:00:00", 1.0))
    calls = {"count": 0}

    monkeypatch.setattr(vix_timing_router, "_provider", _FakeVixProvider({"2026-01-01": 31.0}, calls))

    payload = client.get("/api/trading/vix-timing").json()

    assert calls["count"] == 1
    assert payload["matrix"]["intraday"]["high"]["count"] == 1


def test_vix_timing_command_output(tmp_path, monkeypatch, capsys):
    config_dir = _config_dir(tmp_path)
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    cli._save_trades([
        _trade("t1", "2026-01-01T09:00:00", "2026-01-01T12:00:00", 1.0, vix=18.0),
    ], config_dir)

    assert cli.main(["--config-dir", str(config_dir), "vix-timing"]) == 0

    output = capsys.readouterr().out
    assert "VIX timing analysis" in output
    assert "Intraday" in output
    assert "100%/1" in output


def test_vix_timing_no_trades_fails(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0

    assert cli.main(["--config-dir", str(config_dir), "vix-timing"]) == 1

    assert "No trades" in capsys.readouterr().err
