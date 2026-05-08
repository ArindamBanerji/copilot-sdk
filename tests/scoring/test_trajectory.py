from __future__ import annotations

from copilot_sdk.scoring.trajectory import compute_trajectory


def make_decisions(count, start=1_700_000_000.0, step=3600.0):
    return [
        {
            "decision_id": f"d-{index}",
            "created_at": start + index * step,
            "is_correct": index % 4 != 0,
        }
        for index in range(count)
    ]


def test_empty_decisions_returns_zero_point(mock_preset):
    result = compute_trajectory([], [], mock_preset.shape)

    assert len(result.points) == 1
    assert result.points[0].decisions == 0
    assert result.points[0].iks == 0.0
    assert result.points[0].win_rate == 0.50
    assert result.current_iks == 0.0
    assert result.current_win_rate == 0.50
    assert result.days_active == 0.0


def test_trajectory_has_checkpoints_for_40_decisions(mock_preset):
    result = compute_trajectory([], make_decisions(40), mock_preset.shape)

    assert [point.decisions for point in result.points] == [0, 10, 20, 30, 40]
    assert result.decisions_total == 40


def test_trajectory_includes_final_non_multiple_of_ten(mock_preset):
    result = compute_trajectory([], make_decisions(43), mock_preset.shape)

    assert [point.decisions for point in result.points] == [0, 10, 20, 30, 40, 43]
    assert result.current_iks == result.points[-1].iks
    assert result.current_win_rate == result.points[-1].win_rate


def test_trajectory_points_ordered(mock_preset):
    result = compute_trajectory([], make_decisions(25), mock_preset.shape)

    decisions = [point.decisions for point in result.points]
    assert decisions == sorted(decisions)


def test_days_active_computed(mock_preset):
    result = compute_trajectory([], make_decisions(25, step=86400.0), mock_preset.shape)

    assert result.days_active == 24.0
