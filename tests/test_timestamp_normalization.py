"""Numeric and historical ISO graph timestamps describe the same instants."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from copilot_sdk.backend.conservation_utils import compute_conservation_status_payload
from copilot_sdk.scoring.composite_gate import chronological_decisions
from copilot_sdk.scoring.trajectory import compute_trajectory
from copilot_sdk.timestamps import normalize_timestamp

EPOCH = 1705314600.0
ISO = "2024-01-15T10:30:00Z"


@pytest.mark.parametrize("value, expected", [
    (EPOCH, EPOCH),
    (1705314600, EPOCH),
    (ISO, EPOCH),
    ("2024-01-15T10:30:00+00:00", EPOCH),
    ("2024-01-15T16:00:00+05:30", EPOCH),
    ("2024-01-15T02:30:00-08:00", EPOCH),
    ("2024-01-15T10:30:00", EPOCH),
    ("2024-01-15", EPOCH - 37800),
    ("2024-01-15T10:30:00.125Z", EPOCH + 0.125),
    ("1705314600.0", EPOCH),
    (" 2024-01-15T10:30:00Z ", EPOCH),
    (0, 0.0),
    (-1.25, -1.25),
])
def test_normalize_timestamp(value: float | int | str, expected: float) -> None:
    result = normalize_timestamp(value)
    assert isinstance(result, float)
    assert result == expected


@pytest.mark.parametrize("value, message", [
    (None, "must not be None"),
    ("", "must not be empty"),
    ("   ", "must not be empty"),
    ("not-a-time", "invalid timestamp"),
    ("2024-02-30T00:00:00Z", "invalid timestamp"),
])
def test_invalid_timestamp_rejected(value: str | None, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        normalize_timestamp(value)


def test_mixed_decisions_sort_by_instant_then_id_without_mutation() -> None:
    rows = [
        {"decision_id": "last", "created_at": EPOCH + 1},
        {"decision_id": "b", "created_at": "2024-01-15T16:00:00+05:30"},
        {"decision_id": "a", "created_at": EPOCH},
        {"decision_id": "first", "created_at": "2024-01-15T10:29:59Z"},
        {"decision_id": "c", "created_at": ISO},
    ]
    original = deepcopy(rows)
    assert [row["decision_id"] for row in chronological_decisions(rows)] == [
        "first", "a", "b", "c", "last",
    ]
    assert rows == original


def test_untimed_legacy_decisions_keep_relative_order() -> None:
    rows: list[Any] = [{"decision_id": "z"}, {"decision_id": "a", "created_at": None}, "legacy"]
    assert chronological_decisions(rows) == rows


@pytest.mark.parametrize("timestamp", ["invalid", "", "2024-99-99"])
def test_gate_rejects_malformed_present_timestamps(timestamp: str) -> None:
    with pytest.raises(ValueError):
        chronological_decisions([{"decision_id": "bad", "created_at": timestamp}])


def test_iso_decisions_select_latest_rolling_400_accuracy() -> None:
    start = datetime(2024, 1, 15, tzinfo=timezone.utc)
    rows = [
        {"decision_id": f"d{index:03d}", "created_at": (start + timedelta(seconds=index)).isoformat(),
         "category": "trend_following", "is_correct": index < 200}
        for index in range(600)
    ]
    payload = compute_conservation_status_payload("trading", {
        "verified_decisions": list(reversed(rows)),
    })
    assert payload["verified_count"] == len(rows)
    assert payload["correct_count"] == 200
    assert payload["q"] == 0.0


def test_trajectory_uses_normalized_order_duration_and_point_times() -> None:
    result = compute_trajectory([], [
        {"decision_id": "last", "created_at": "2024-01-16T10:30:00Z", "is_correct": False},
        {"decision_id": "first", "created_at": EPOCH, "is_correct": True},
    ], None)
    assert result.days_active == 1.0
    assert result.decisions_total == 2
    assert result.current_win_rate == 0.5
    assert [point.timestamp for point in result.points] == [EPOCH, EPOCH + 86400]
