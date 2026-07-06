from __future__ import annotations

from datetime import datetime

from app.services.pattern_detector import (
    _accuracy,
    _detect_tod_degradation,
    _parse_time,
    detect_patterns,
)


def _trade(index: int, **overrides):
    payload = {
        "trade_id": f"tod-{index}",
        "entry_time": f"2026-01-05T09:{index % 60:02d}:00",
        "exit_time": None,
        "pnl": 0.0,
        "size": 1.0,
        "size_vs_rolling_avg": 1.0,
        "entry_at_day_extreme": False,
        "in_drawdown": False,
        "is_correct": True,
    }
    payload.update(overrides)
    return payload


def _names(patterns):
    return {pattern["name"] for pattern in patterns}


def _degradation_trades(include_missing_time: bool = False):
    trades = []
    friday_dates = ["2026-01-02", "2026-01-09", "2026-01-16", "2026-01-23"]
    for index in range(8):
        trades.append(
            _trade(
                index,
                trade_id=f"weak-{index}",
                entry_time=f"{friday_dates[index % len(friday_dates)]}T14:{index:02d}:00",
                is_correct=False,
            )
        )
    for index in range(12):
        trades.append(
            _trade(
                index + 8,
                trade_id=f"base-{index}",
                entry_time=f"2026-01-05T{9 + (index % 6):02d}:{index:02d}:00",
                is_correct=True,
            )
        )
    if include_missing_time:
        trades.extend(
            [
                _trade(30, trade_id="missing-time", entry_time=None, is_correct=False),
                _trade(31, trade_id="bad-time", entry_time="not-a-date", is_correct=False),
            ]
        )
    return trades


def test_parse_time_handles_datetime_passthrough():
    value = datetime(2026, 1, 2, 14, 30)

    assert _parse_time(value) is value


def test_parse_time_handles_iso_string_with_t():
    parsed = _parse_time("2026-01-02T14:30:00")

    assert parsed == datetime(2026, 1, 2, 14, 30)


def test_parse_time_handles_fractional_seconds():
    parsed = _parse_time("2026-01-02T14:30:00.123456")

    assert parsed == datetime(2026, 1, 2, 14, 30, 0, 123456)


def test_parse_time_handles_z_suffix():
    parsed = _parse_time("2026-01-02T14:30:00Z")

    assert parsed is not None
    assert parsed.hour == 14
    assert parsed.minute == 30


def test_parse_time_returns_none_for_none_and_invalid_string():
    assert _parse_time(None) is None
    assert _parse_time("not-a-date") is None


def test_accuracy_all_correct():
    assert _accuracy([_trade(1, is_correct=True), _trade(2, is_correct=True)]) == 1.0


def test_accuracy_all_incorrect():
    assert _accuracy([_trade(1, is_correct=False), _trade(2, is_correct=False)]) == 0.0


def test_accuracy_mixed_excludes_unverified():
    trades = [
        _trade(1, is_correct=True),
        _trade(2, is_correct=False),
        _trade(3, is_correct=None),
        _trade(4),
    ]
    del trades[3]["is_correct"]

    assert _accuracy(trades) == 0.5


def test_accuracy_no_verified_and_empty():
    assert _accuracy([_trade(1, is_correct=None), {}]) is None
    assert _accuracy([]) is None


def test_detector_finds_friday_14_degradation():
    pattern = _detect_tod_degradation(_degradation_trades())

    assert pattern is not None
    assert pattern["name"] == "tod_degradation"
    assert pattern["display_name"] == "Time-of-Day Degradation"
    assert "Friday" in pattern["description"]
    assert "2pm-4pm" in pattern["description"]
    assert pattern["affected_trade_count"] == 8
    assert set(pattern["affected_trades"]) == {f"weak-{index}" for index in range(8)}
    assert 0.0 <= pattern["severity"] <= 1.0


def test_detector_returns_none_when_total_trades_below_10():
    assert _detect_tod_degradation(_degradation_trades()[:9]) is None


def test_detector_returns_none_when_weak_bucket_has_fewer_than_5_verified_trades():
    trades = _degradation_trades()[4:]

    assert _detect_tod_degradation(trades) is None


def test_detector_returns_none_when_no_significant_gap():
    trades = []
    for index in range(8):
        trades.append(
            _trade(
                index,
                entry_time=f"2026-01-02T14:{index:02d}:00",
                is_correct=index != 0,
            )
        )
    for index in range(12):
        trades.append(
            _trade(
                index + 8,
                entry_time=f"2026-01-05T{9 + (index % 6):02d}:{index:02d}:00",
                is_correct=True,
            )
        )

    assert _detect_tod_degradation(trades) is None


def test_detector_returns_none_when_all_trades_unverified():
    trades = [_trade(index, is_correct=None) for index in range(12)]

    assert _detect_tod_degradation(trades) is None


def test_missing_entry_time_does_not_crash_or_prevent_valid_detection():
    pattern = _detect_tod_degradation(_degradation_trades(include_missing_time=True))

    assert pattern is not None
    assert pattern["name"] == "tod_degradation"
    assert pattern["affected_trade_count"] == 8


def test_returned_pattern_contains_existing_pattern_fields():
    pattern = _detect_tod_degradation(_degradation_trades())
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

    assert pattern is not None
    assert required <= set(pattern)


def test_detect_patterns_includes_tod_degradation_when_data_triggers_it():
    assert "tod_degradation" in _names(detect_patterns(_degradation_trades()))


def test_detect_patterns_does_not_include_tod_degradation_for_clean_uniform_data():
    trades = [_trade(index, is_correct=index % 2 == 0) for index in range(20)]

    assert "tod_degradation" not in _names(detect_patterns(trades))
