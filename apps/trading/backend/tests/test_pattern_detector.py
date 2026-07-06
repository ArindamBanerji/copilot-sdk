from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.routers.data_import import _trade_store_ref
from app.services.pattern_detector import detect_patterns


@pytest.fixture(autouse=True)
def reset_trade_store():
    _trade_store_ref.clear()
    yield
    _trade_store_ref.clear()


def _trade(index: int, **overrides):
    payload = {
        "trade_id": f"t-{index}",
        "entry_time": f"2026-01-01T10:{index:02d}:00",
        "exit_time": f"2026-01-01T10:{index + 1:02d}:00",
        "pnl": 10.0,
        "size": 1.0,
        "size_vs_rolling_avg": 1.0,
        "entry_at_day_extreme": False,
        "in_drawdown": False,
    }
    payload.update(overrides)
    return payload


def _names(patterns):
    return {pattern["name"] for pattern in patterns}


def _dt(minutes: int, *, hour: int = 9, minute: int = 30) -> str:
    start = datetime(2026, 1, 1, hour, minute)
    return (start + timedelta(minutes=minutes)).isoformat()


def _verified_trade(index: int, is_correct: bool, **overrides):
    payload = _trade(
        index,
        entry_time=_dt(index * 90),
        exit_time=_dt(index * 90 + 10),
        pnl=10.0 if is_correct else -10.0,
        is_correct=is_correct,
    )
    payload.update(overrides)
    return payload


def _pattern_by_name(patterns, name: str):
    return next(pattern for pattern in patterns if pattern["name"] == name)


def test_normal_no_revenge():
    trades = [
        _trade(1, pnl=-5.0, entry_time="2026-01-01T09:50:00", exit_time="2026-01-01T10:00:00"),
        _trade(2, entry_time="2026-01-01T11:00:00"),
        _trade(3, entry_time="2026-01-01T12:03:00", exit_time="2026-01-01T12:04:00"),
        _trade(4, entry_time="2026-01-01T13:04:00", exit_time="2026-01-01T13:05:00"),
        _trade(5, entry_time="2026-01-01T14:05:00", exit_time="2026-01-01T14:06:00"),
    ]

    assert "revenge_trading" not in _names(detect_patterns(trades))


def test_closed_loss_plus_10min_detects_revenge():
    trades = [
        _trade(1, pnl=-5.0, entry_time="2026-01-01T09:50:00", exit_time="2026-01-01T10:00:00"),
        _trade(2, entry_time="2026-01-01T10:10:00"),
        _trade(3),
        _trade(4),
        _trade(5),
    ]

    assert "revenge_trading" in _names(detect_patterns(trades))


def test_enough_time_no_revenge():
    trades = [
        _trade(1, pnl=-5.0, entry_time="2026-01-01T09:50:00", exit_time="2026-01-01T10:00:00"),
        _trade(2, entry_time="2026-01-01T10:31:00"),
        _trade(3, entry_time="2026-01-01T12:03:00", exit_time="2026-01-01T12:04:00"),
        _trade(4, entry_time="2026-01-01T13:04:00", exit_time="2026-01-01T13:05:00"),
        _trade(5, entry_time="2026-01-01T14:05:00", exit_time="2026-01-01T14:06:00"),
    ]

    assert "revenge_trading" not in _names(detect_patterns(trades))


def test_open_previous_trade_no_revenge():
    trades = [
        _trade(1, pnl=-5.0, exit_time=None, entry_time="2026-01-01T09:00:00"),
        _trade(2, entry_time="2026-01-01T09:10:00"),
        _trade(3),
        _trade(4),
        _trade(5),
    ]

    assert "revenge_trading" not in _names(detect_patterns(trades))


def test_previous_win_no_revenge():
    trades = [
        _trade(1, pnl=5.0, entry_time="2026-01-01T09:50:00", exit_time="2026-01-01T10:00:00"),
        _trade(2, entry_time="2026-01-01T10:10:00"),
        _trade(3),
        _trade(4),
        _trade(5),
    ]

    assert "revenge_trading" not in _names(detect_patterns(trades))


def test_overconfidence_detected():
    trades = [
        _trade(1, pnl=5.0),
        _trade(2, pnl=6.0),
        _trade(3, pnl=7.0),
        _trade(4, size_vs_rolling_avg=1.4),
        _trade(5),
    ]

    assert "overconfidence" in _names(detect_patterns(trades))


def test_overconfidence_normal_size_no():
    trades = [
        _trade(1, pnl=5.0),
        _trade(2, pnl=6.0),
        _trade(3, pnl=7.0),
        _trade(4, size_vs_rolling_avg=1.1),
        _trade(5),
    ]

    assert "overconfidence" not in _names(detect_patterns(trades))


def test_overconfidence_short_streak_no():
    trades = [
        _trade(1, pnl=5.0),
        _trade(2, pnl=6.0),
        _trade(3, pnl=-1.0),
        _trade(4, size_vs_rolling_avg=1.5),
        _trade(5),
    ]

    assert "overconfidence" not in _names(detect_patterns(trades))


def test_fomo_detected():
    trades = [_trade(index, entry_at_day_extreme=index in {2, 4}) for index in range(1, 6)]

    assert "fomo" in _names(detect_patterns(trades))


def test_fomo_normal_no():
    trades = [_trade(index) for index in range(1, 6)]

    assert "fomo" not in _names(detect_patterns(trades))


def test_tilt_three_in_hour_detected():
    trades = [
        _trade(1, entry_time="2026-01-01T10:01:00"),
        _trade(2, entry_time="2026-01-01T10:20:00"),
        _trade(3, entry_time="2026-01-01T10:45:00"),
        _trade(4, entry_time="2026-01-01T11:05:00"),
        _trade(5, entry_time="2026-01-01T12:05:00"),
    ]

    assert "tilt" in _names(detect_patterns(trades))


def test_tilt_spread_no_tilt():
    trades = [
        _trade(1, entry_time="2026-01-01T09:01:00"),
        _trade(2, entry_time="2026-01-01T10:20:00"),
        _trade(3, entry_time="2026-01-01T11:45:00"),
        _trade(4, entry_time="2026-01-01T12:05:00"),
        _trade(5, entry_time="2026-01-01T13:05:00"),
    ]

    assert "tilt" not in _names(detect_patterns(trades))


def test_drawdown_chase_size_up_during_drawdown_detected():
    trades = [
        _trade(1, size=1.0),
        _trade(2, size=1.3, in_drawdown=True),
        _trade(3),
        _trade(4),
        _trade(5),
    ]

    assert "drawdown_chase" in _names(detect_patterns(trades))


def test_drawdown_chase_size_down_no_chase():
    trades = [
        _trade(1, size=2.0),
        _trade(2, size=1.0, in_drawdown=True),
        _trade(3),
        _trade(4),
        _trade(5),
    ]

    assert "drawdown_chase" not in _names(detect_patterns(trades))


def test_drawdown_chase_previous_size_zero_no_divide_by_zero():
    trades = [
        _trade(1, size=0.0),
        _trade(2, size=2.0, in_drawdown=True),
        _trade(3),
        _trade(4),
        _trade(5),
    ]

    assert "drawdown_chase" not in _names(detect_patterns(trades))


def test_empty_returns_empty():
    assert detect_patterns([]) == []


def test_fewer_than_5_returns_empty():
    assert detect_patterns([_trade(1), _trade(2), _trade(3), _trade(4)]) == []


def test_required_fields_and_bounds():
    patterns = detect_patterns(
        [
            _trade(1, entry_at_day_extreme=True),
            _trade(2, entry_at_day_extreme=True),
            _trade(3),
            _trade(4),
            _trade(5),
        ]
    )

    assert patterns
    required = {
        "name",
        "display_name",
        "description",
        "frequency",
        "severity",
        "affected_trade_count",
        "affected_trades",
        "recommendation",
    }
    for pattern in patterns:
        assert required <= set(pattern)
        assert 0.0 <= pattern["severity"] <= 1.0


def test_affected_trades_capped_at_10():
    patterns = detect_patterns(
        [_trade(index, entry_at_day_extreme=True) for index in range(1, 16)]
    )
    fomo = next(pattern for pattern in patterns if pattern["name"] == "fomo")

    assert fomo["affected_trade_count"] == 15
    assert len(fomo["affected_trades"]) == 10


def test_fomo_and_revenge_coexist():
    trades = [
        _trade(1, pnl=-5.0, exit_time="2026-01-01T10:00:00", entry_at_day_extreme=True),
        _trade(2, entry_time="2026-01-01T10:10:00", entry_at_day_extreme=True),
        _trade(3),
        _trade(4),
        _trade(5),
    ]

    names = _names(detect_patterns(trades))

    assert {"fomo", "revenge_trading"} <= names


def test_endpoint_200_empty(client):
    response = client.get("/api/context/patterns")

    assert response.status_code == 200
    assert response.json() == {
        "patterns": [],
        "total_trades": 0,
        "message": "Import trades to detect patterns.",
    }


def test_endpoint_with_trades(client):
    _trade_store_ref.extend(
        [
            _trade(1, entry_at_day_extreme=True),
            _trade(2, entry_at_day_extreme=True),
            _trade(3),
            _trade(4),
            _trade(5),
        ]
    )

    response = client.get("/api/context/patterns")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_trades_analyzed"] == 5
    assert payload["total_patterns_detected"] >= 1
    assert payload["most_severe"] in _names(payload["patterns"])


def test_route_mounted(client):
    paths = {route.path for route in client.app.routes}

    assert "/api/context/patterns" in paths


def test_revenge_accuracy_comparison():
    trades = []
    trade_id = 1
    for index in range(20):
        base_minute = index * 180
        trades.append(
            _trade(
                trade_id,
                entry_time=_dt(base_minute),
                exit_time=_dt(base_minute + 10),
                pnl=-10.0,
                is_correct=True,
            )
        )
        trade_id += 1
        trades.append(
            _trade(
                trade_id,
                entry_time=_dt(base_minute + 20),
                exit_time=_dt(base_minute + 30),
                pnl=10.0 if index < 6 else -10.0,
                is_correct=index < 6,
            )
        )
        trade_id += 1
    for index in range(80):
        trades.append(_verified_trade(trade_id, index < 52))
        trade_id += 1

    revenge = _pattern_by_name(detect_patterns(trades), "revenge_trading")

    assert revenge["p_value"] is not None
    assert revenge["significant"] is True
    assert revenge["statistical_test"] == "fisher_exact"


def test_revenge_cost_estimation():
    patterns = detect_patterns([
        _trade(1, pnl=-5.0, entry_time="2026-01-01T09:50:00", exit_time="2026-01-01T10:00:00"),
        _trade(2, entry_time="2026-01-01T10:10:00"),
        _trade(3),
        _trade(4),
        _trade(5),
    ])

    revenge = _pattern_by_name(patterns, "revenge_trading")

    assert "estimated_annual_cost" in revenge
    assert revenge["estimated_annual_cost"] is None or revenge["estimated_annual_cost"] >= 0


def test_overconfidence_accuracy_drop():
    trades = []
    trade_id = 1
    for index in range(20):
        base_minute = index * 240
        for offset in range(3):
            trades.append(
                _trade(
                    trade_id,
                    entry_time=_dt(base_minute + offset * 20),
                    exit_time=_dt(base_minute + offset * 20 + 5),
                    pnl=10.0,
                    is_correct=True,
                )
            )
            trade_id += 1
        is_correct = index < 9
        trades.append(
            _trade(
                trade_id,
                entry_time=_dt(base_minute + 70),
                exit_time=_dt(base_minute + 80),
                pnl=10.0 if is_correct else -10.0,
                is_correct=is_correct,
                size_vs_rolling_avg=1.5,
            )
        )
        trade_id += 1

    overconfidence = _pattern_by_name(detect_patterns(trades), "overconfidence")

    assert overconfidence["p_value"] is not None
    assert overconfidence["significant"] is True
    assert overconfidence["statistical_test"] == "fisher_exact"


def test_overconfidence_no_drop_no_flag():
    trades = []
    trade_id = 1
    for index in range(20):
        base_minute = index * 240
        for offset in range(3):
            trades.append(
                _trade(
                    trade_id,
                    entry_time=_dt(base_minute + offset * 20),
                    exit_time=_dt(base_minute + offset * 20 + 5),
                    pnl=10.0 if offset else -10.0,
                    is_correct=offset > 0,
                )
            )
            trade_id += 1
        trades.append(
            _trade(
                trade_id,
                entry_time=_dt(base_minute + 70),
                exit_time=_dt(base_minute + 80),
                pnl=10.0,
                is_correct=True,
                size_vs_rolling_avg=1.5,
            )
        )
        trade_id += 1

    assert "overconfidence" not in _names(detect_patterns(trades))


def _session_trades():
    trades = []
    trade_id = 1
    for index in range(30):
        trades.append(_verified_trade(
            trade_id,
            index < 24,
            entry_time=f"2026-01-{(index % 28) + 1:02d}T10:00:00",
            exit_time=f"2026-01-{(index % 28) + 1:02d}T10:10:00",
        ))
        trade_id += 1
        trades.append(_verified_trade(
            trade_id,
            index < 24,
            entry_time=f"2026-02-{(index % 28) + 1:02d}T12:30:00",
            exit_time=f"2026-02-{(index % 28) + 1:02d}T12:40:00",
        ))
        trade_id += 1
        trades.append(_verified_trade(
            trade_id,
            index < 9,
            entry_time=f"2026-03-{(index % 28) + 1:02d}T14:30:00",
            exit_time=f"2026-03-{(index % 28) + 1:02d}T14:40:00",
        ))
        trade_id += 1
    return trades


def test_tod_chi_squared():
    tod = _pattern_by_name(detect_patterns(_session_trades()), "tod_degradation")

    assert tod["statistical_test"] == "chi_squared"
    assert tod["significant"] is True
    assert tod["worst_session"] == "late"


def test_tod_cost_estimation():
    tod = _pattern_by_name(detect_patterns(_session_trades()), "tod_degradation")

    assert tod["estimated_annual_cost"] > 0


def _regime_trades():
    trades = []
    trade_id = 1
    for index in range(30):
        trades.append(_verified_trade(trade_id, index < 24, regime="trending"))
        trade_id += 1
        trades.append(_verified_trade(trade_id, index < 9, regime="ranging"))
        trade_id += 1
        trades.append(_verified_trade(trade_id, index < 21, regime="volatile"))
        trade_id += 1
    return trades


def test_regime_detected():
    regime = _pattern_by_name(detect_patterns(_regime_trades()), "regime_dependency")

    assert regime["statistical_test"] == "chi_squared"
    assert regime["significant"] is True
    assert regime["worst_regime"] == "ranging"


def test_regime_not_detected():
    trades = []
    trade_id = 1
    for index in range(20):
        for regime in ("trending", "ranging", "volatile"):
            trades.append(_verified_trade(trade_id, index < 15, regime=regime))
            trade_id += 1

    assert "regime_dependency" not in _names(detect_patterns(trades))


def test_regime_insufficient_data():
    trades = [
        _verified_trade(index, index < 8, regime="trending")
        for index in range(1, 11)
    ]
    trades.extend(
        _verified_trade(index + 20, False, regime="ranging")
        for index in range(4)
    )

    assert "regime_dependency" not in _names(detect_patterns(trades))


def test_sizing_drift_detected():
    trades = [
        _verified_trade(
            index,
            index % 2 == 0,
            size=1.0 + index * 0.1,
            entry_time=_dt(index * 1440),
            exit_time=_dt(index * 1440 + 10),
        )
        for index in range(30)
    ]

    drift = _pattern_by_name(detect_patterns(trades), "sizing_drift")

    assert drift["statistical_test"] == "spearman"
    assert drift["significant"] is True


def test_sizing_drift_not_detected():
    trades = [
        _verified_trade(
            index,
            index % 2 == 0,
            size=1.0,
            entry_time=_dt(index * 1440),
            exit_time=_dt(index * 1440 + 10),
        )
        for index in range(30)
    ]

    assert "sizing_drift" not in _names(detect_patterns(trades))


def test_sizing_drift_with_accuracy_improvement():
    trades = [
        _verified_trade(
            index,
            index >= 15,
            size=1.0 + index * 0.1,
            entry_time=_dt(index * 1440),
            exit_time=_dt(index * 1440 + 10),
        )
        for index in range(30)
    ]

    assert "sizing_drift" not in _names(detect_patterns(trades))


def test_all_patterns_have_stats_fields():
    patterns = detect_patterns(
        [_trade(index, entry_at_day_extreme=True) for index in range(1, 6)]
    )

    for pattern in patterns:
        assert "p_value" in pattern
        assert "significant" in pattern
        assert "statistical_test" in pattern
        assert "estimated_annual_cost" in pattern
        assert "cost_components" in pattern


def test_cost_always_positive_or_none():
    patterns = detect_patterns(_session_trades() + _regime_trades())

    for pattern in patterns:
        cost = pattern["estimated_annual_cost"]
        assert cost is None or cost >= 0


def _revenge_stat_trades(*, loss_amount: float = -200.0, win_amount: float = 500.0):
    trades = []
    trade_id = 1
    for index in range(20):
        base_minute = index * 180
        trades.append(
            _trade(
                trade_id,
                entry_time=_dt(base_minute),
                exit_time=_dt(base_minute + 10),
                pnl=loss_amount,
                is_correct=True,
            )
        )
        trade_id += 1
        trades.append(
            _trade(
                trade_id,
                entry_time=_dt(base_minute + 20),
                exit_time=_dt(base_minute + 30),
                pnl=win_amount if index < 6 else loss_amount,
                is_correct=index < 6,
            )
        )
        trade_id += 1
    for index in range(80):
        trades.append(
            _trade(
                trade_id,
                entry_time=_dt(trade_id * 180),
                exit_time=_dt(trade_id * 180 + 10),
                pnl=win_amount if index < 52 else loss_amount,
                is_correct=index < 52,
            )
        )
        trade_id += 1
    return trades


def test_cost_uses_avg_loss_not_avg_size():
    revenge = _pattern_by_name(detect_patterns(_revenge_stat_trades()), "revenge_trading")

    expected = round(
        revenge["cost_components"]["accuracy_delta"]
        * revenge["affected_trade_count"]
        * 200.0,
        2,
    )
    assert revenge["cost_components"]["avg_loss"] == 200.0
    assert revenge["estimated_annual_cost"] == expected


def test_cost_zero_losses():
    trades = _revenge_stat_trades(loss_amount=200.0, win_amount=500.0)
    patterns = detect_patterns(trades)

    for pattern in patterns:
        assert pattern["estimated_annual_cost"] is None
        if pattern["cost_components"]:
            assert pattern["cost_components"]["avg_loss"] is None


def test_cost_no_pnl_data():
    trades = _revenge_stat_trades()
    for trade in trades:
        trade.pop("pnl", None)
        trade["computed_pnl"] = None

    patterns = detect_patterns(trades)

    for pattern in patterns:
        assert pattern["estimated_annual_cost"] is None


def test_mixed_timestamp_formats_no_crash():
    trades = [
        _trade(1, entry_time="2025-03-15T14:30:00Z", exit_time="2025-03-15T14:40:00Z"),
        _trade(2, entry_time="2025-03-15 14:30:00", exit_time="2025-03-15 14:40:00"),
        _trade(3, entry_time="03/15/2025", exit_time="03/15/2025"),
        _trade(4, entry_time=None, exit_time=None),
        _trade(5, entry_time="2025-03-15T15:30:00+00:00", exit_time="2025-03-15T15:40:00+00:00"),
    ]

    assert isinstance(detect_patterns(trades), list)


def test_fisher_exact_degenerate_table():
    trades = []
    trade_id = 1
    for index in range(8):
        base_minute = index * 180
        trades.append(_trade(
            trade_id,
            entry_time=_dt(base_minute),
            exit_time=_dt(base_minute + 10),
            pnl=-10.0,
            is_correct=True,
        ))
        trade_id += 1
        trades.append(_trade(
            trade_id,
            entry_time=_dt(base_minute + 20),
            exit_time=_dt(base_minute + 30),
            pnl=10.0,
            is_correct=True,
        ))
        trade_id += 1

    patterns = detect_patterns(trades)

    revenge = next((pattern for pattern in patterns if pattern["name"] == "revenge_trading"), None)
    assert revenge is None or revenge["p_value"] is None


def test_chi_squared_single_category():
    trades = [_verified_trade(index, index % 2 == 0, regime="trending") for index in range(20)]

    assert "regime_dependency" not in _names(detect_patterns(trades))


def test_spearman_constant_size():
    trades = [
        _verified_trade(
            index,
            index % 2 == 0,
            size=1.0,
            entry_time=_dt(index * 1440),
            exit_time=_dt(index * 1440 + 10),
        )
        for index in range(30)
    ]

    assert "sizing_drift" not in _names(detect_patterns(trades))


def test_heuristic_detectors_legacy_fields():
    patterns = detect_patterns([
        _trade(1, entry_at_day_extreme=True, size=1.0),
        _trade(2, entry_at_day_extreme=True, size=1.3, in_drawdown=True),
        _trade(3, entry_time="2026-01-01T10:15:00"),
        _trade(4, entry_time="2026-01-01T10:25:00"),
        _trade(5, entry_time="2026-01-01T10:35:00"),
    ])
    required = {
        "name",
        "display_name",
        "description",
        "frequency",
        "severity",
        "affected_trade_count",
        "recommendation",
    }

    for name in {"fomo", "tilt", "drawdown_chase"}:
        pattern = _pattern_by_name(patterns, name)
        assert required <= set(pattern)
        assert "p_value" in pattern
        assert "significant" in pattern
        assert "statistical_test" in pattern


def test_tod_morning_vs_late_detected():
    tod = _pattern_by_name(detect_patterns(_session_trades()), "tod_degradation")

    assert tod["statistical_test"] == "chi_squared"
    assert tod["worst_session"] == "late"


def test_tod_insufficient_bucket():
    trades = []
    for index in range(7):
        trades.append(_verified_trade(index, True, entry_time=f"2026-01-01T10:{index:02d}:00"))
        trades.append(_verified_trade(index + 20, False, entry_time=f"2026-01-01T14:{index:02d}:00"))

    assert isinstance(detect_patterns(trades), list)


def _friday_afternoon_trades():
    trades = []
    trade_id = 1
    for index in range(80):
        trades.append(
            _verified_trade(
                trade_id,
                True,
                entry_time=f"2026-01-{5 + (index % 20):02d}T17:00:00",
                exit_time=f"2026-01-{5 + (index % 20):02d}T17:10:00",
                pnl=120.0,
            )
        )
        trade_id += 1
    for index in range(12):
        timestamp = datetime(2026, 1, 2, 14, index % 2) + timedelta(days=index * 7)
        trades.append(
            _verified_trade(
                trade_id,
                index < 2,
                entry_time=timestamp.isoformat(),
                exit_time=(timestamp + timedelta(minutes=20)).isoformat(),
                pnl=120.0 if index < 2 else -200.0,
            )
        )
        trade_id += 1
    return trades


def test_tod_friday_afternoon_window_detected():
    trades = _friday_afternoon_trades()
    tod = _pattern_by_name(detect_patterns(trades), "tod_degradation")
    window_trades = [
        trade
        for trade in trades
        if datetime.fromisoformat(trade["entry_time"]).strftime("%A") == "Friday"
        and 14 <= datetime.fromisoformat(trade["entry_time"]).hour < 16
    ]
    window_times = [datetime.fromisoformat(trade["entry_time"]) for trade in window_trades]
    span_days = max((max(window_times) - min(window_times)).total_seconds() / 86400.0, 1.0)
    annualized_count = len(window_trades) / span_days * 252.0
    expected_annual_cost = round(
        ((82 / 92) - (2 / 12)) * annualized_count * 200.0,
        2,
    )

    assert tod["statistical_test"] == "binomial"
    assert tod["significant"] is True
    assert tod["worst_window"] == {
        "day": "Friday",
        "window": "2pm-4pm",
        "accuracy": 0.1667,
        "baseline_accuracy": 0.8913,
        "estimated_annual_cost": expected_annual_cost,
    }
    assert "Friday 2pm-4pm" in tod["description"]


def test_tod_uniform_accuracy_no_window():
    trades = []
    trade_id = 1
    for index in range(30):
        trades.append(_verified_trade(trade_id, index % 2 == 0, entry_time=f"2026-01-02T14:{index:02d}:00"))
        trade_id += 1
        trades.append(_verified_trade(trade_id, index % 2 == 0, entry_time=f"2026-01-03T17:{index:02d}:00"))
        trade_id += 1

    assert "tod_degradation" not in _names(detect_patterns(trades))


def test_tod_heuristic_minimum_five_trades():
    trades = [_verified_trade(index, True, entry_time=f"2026-01-03T17:{index:02d}:00") for index in range(1, 25)]
    trades.extend(
        _verified_trade(100 + index, False, entry_time=f"2026-01-02T14:0{index}:00")
        for index in range(4)
    )

    assert "tod_degradation" not in _names(detect_patterns(trades))


def test_tod_annual_cost_positive_and_reasonable():
    tod = _pattern_by_name(detect_patterns(_friday_afternoon_trades()), "tod_degradation")

    assert tod["estimated_annual_cost"] > 0
    assert tod["estimated_annual_cost"] < 10000
    assert tod["cost_components"]["avg_loss"] == 200.0
    assert tod["cost_components"]["annualized_count"] > tod["affected_trade_count"]


def test_tod_multiple_bad_windows_surfaced():
    trades = _friday_afternoon_trades()
    trade_id = 1000
    for index in range(10):
        timestamp = datetime(2026, 1, 3, 19, index % 2) + timedelta(days=index * 7)
        trades.append(
            _verified_trade(
                trade_id,
                index < 1,
                entry_time=timestamp.isoformat(),
                exit_time=(timestamp + timedelta(minutes=20)).isoformat(),
                pnl=120.0 if index < 1 else -200.0,
            )
        )
        trade_id += 1

    tod = _pattern_by_name(detect_patterns(trades), "tod_degradation")

    windows = {(window["day"], window["window"]) for window in tod["bad_windows"]}
    assert ("Friday", "2pm-4pm") in windows
    assert ("Saturday", "7pm-9pm") in windows


def test_detect_all_sorted_by_pvalue():
    patterns = [
        pattern
        for pattern in detect_patterns(_session_trades() + _regime_trades() + _revenge_stat_trades())
        if pattern["p_value"] is not None
    ]

    assert patterns
    assert [pattern["p_value"] for pattern in patterns] == sorted(
        pattern["p_value"] for pattern in patterns
    )


def test_detect_all_eight_detectors_callable():
    trades = _session_trades() + _regime_trades() + _revenge_stat_trades()
    trades.extend(
        _verified_trade(
            1000 + index,
            index % 2 == 0,
            size=1.0 + index * 0.1,
            entry_time=_dt(index * 1440),
            exit_time=_dt(index * 1440 + 10),
            entry_at_day_extreme=index < 3,
            in_drawdown=index == 10,
            size_vs_rolling_avg=1.4 if index == 10 else 1.0,
        )
        for index in range(30)
    )

    patterns = detect_patterns(trades)

    assert isinstance(patterns, list)
    assert patterns
