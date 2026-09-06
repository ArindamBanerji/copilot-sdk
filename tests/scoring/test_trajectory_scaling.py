from __future__ import annotations

from typing import Any

from copilot_sdk.scoring.trajectory import compute_trajectory


def test_trajectory_preserves_prefix_metrics_without_repeated_outcome_scans() -> None:
    reads = 0

    class Decision(dict[str, Any]):
        def __getitem__(self, key: str) -> Any:
            nonlocal reads
            if key == "is_correct":
                reads += 1
            return super().__getitem__(key)

    decisions: list[dict] = [Decision(decision_id=str(index), created_at=float(index),
                                     is_correct=index % 4 != 0) for index in range(1003)]
    result = compute_trajectory([], list(reversed(decisions)), None)
    assert reads == len(decisions)
    assert result.points[1].win_rate == 0.7  # Seven correct out of the first ten.
    assert result.current_win_rate == round(752 / 1003, 3)
    assert result.points[-1].decisions == 1003
    assert result.points[-1].timestamp == 1002.0


def test_missing_and_null_outcomes_keep_original_denominator() -> None:
    result = compute_trajectory([], [
        {"created_at": 1}, {"created_at": 2, "is_correct": None},
        {"created_at": 3, "is_correct": True},
    ], None)
    assert result.points[0].win_rate == 0.5
    assert result.current_win_rate == 0.5
    assert result.decisions_total == 3
