from __future__ import annotations

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
