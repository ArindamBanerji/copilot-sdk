"""Compounding trajectory computation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TrajectoryPoint:
    decisions: int
    iks: float
    win_rate: float
    timestamp: float


@dataclass(frozen=True)
class TrajectoryResult:
    points: list[TrajectoryPoint]
    current_iks: float
    current_win_rate: float
    decisions_total: int
    days_active: float


def compute_trajectory(
    checkpoints: list[dict],
    decisions: list[dict],
    shape: Any,
) -> TrajectoryResult:
    """Compute a simplified compounding trajectory from decision history."""

    del checkpoints, shape

    if not decisions:
        point = TrajectoryPoint(decisions=0, iks=0.0, win_rate=0.50, timestamp=0.0)
        return TrajectoryResult(
            points=[point],
            current_iks=0.0,
            current_win_rate=0.50,
            decisions_total=0,
            days_active=0.0,
        )

    ordered = sorted(decisions, key=lambda item: (float(item["created_at"]), str(item.get("decision_id", ""))))
    total = len(ordered)
    counts = list(range(0, total + 1, 10))
    if counts[-1] != total:
        counts.append(total)

    points = []
    correct = outcomes = previous_count = 0
    for count in counts:
        for index in range(previous_count, count):
            decision = ordered[index]
            if "is_correct" in decision:
                outcomes += 1
                correct += bool(decision["is_correct"])
        win_rate = round(correct / outcomes, 3) if outcomes else 0.50
        points.append(TrajectoryPoint(
            decisions=count,
            iks=_compute_iks(count, win_rate),
            win_rate=win_rate,
            timestamp=_timestamp_for_count(ordered, count),
        ))
        previous_count = count

    days_active = round(
        (float(ordered[-1]["created_at"]) - float(ordered[0]["created_at"])) / 86400.0,
        1,
    )

    return TrajectoryResult(
        points=points,
        current_iks=points[-1].iks,
        current_win_rate=points[-1].win_rate,
        decisions_total=total,
        days_active=days_active,
    )


def _win_rate(decisions: list[dict]) -> float:
    if not decisions:
        return 0.50
    outcomes = [bool(d["is_correct"]) for d in decisions if "is_correct" in d]
    if not outcomes:
        return 0.50
    return round(sum(outcomes) / len(outcomes), 3)


def _compute_iks(n_decisions: int, win_rate: float) -> float:
    iks = (
        min(n_decisions / 500.0, 1.0) * 25.0
        + win_rate * 25.0
        + min(n_decisions / 200.0, 1.0) * 15.0
        + min(n_decisions / 100.0, 1.0) * 10.0
    )
    return round(iks, 1)


def _timestamp_for_count(decisions: list[dict], count: int) -> float:
    if count == 0:
        return float(decisions[0]["created_at"])
    return float(decisions[count - 1]["created_at"])
