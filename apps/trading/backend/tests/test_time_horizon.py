from __future__ import annotations

from app.factors.time_horizon import TimeHorizonFactor


def test_no_context_neutral():
    assert TimeHorizonFactor().compute({}) == 0.5


def test_non_dict_neutral():
    assert TimeHorizonFactor().compute(object()) == 0.5


def test_plan_adherence_full_band():
    factor = TimeHorizonFactor()

    assert factor.compute({"planned_hold_hours": 10, "actual_hold_hours": 7}) == 1.0
    assert factor.compute({"planned_hold_hours": 10, "actual_hold_hours": 15}) == 1.0


def test_plan_adherence_too_short():
    value = TimeHorizonFactor().compute({"planned_hold_hours": 10, "actual_hold_hours": 3.5})

    assert value == 0.5


def test_plan_adherence_too_long():
    value = TimeHorizonFactor().compute({"planned_hold_hours": 10, "actual_hold_hours": 35})

    assert value == 0.2


def test_exit_reason_target():
    assert TimeHorizonFactor().compute({"exit_reason": "target"}) == 1.0


def test_exit_reason_stop():
    assert TimeHorizonFactor().compute({"exit_reason": "stop"}) == 0.8


def test_exit_reason_impulse():
    assert TimeHorizonFactor().compute({"exit_reason": "impulse"}) == 0.2


def test_session_alignment_preferred():
    assert TimeHorizonFactor().compute({"entry_hour": 10, "preferred_session": "morning"}) == 1.0


def test_session_misalignment():
    assert TimeHorizonFactor().compute({"entry_hour": 15, "preferred_session": "morning"}) == 0.4


def test_overlapping_session_boundary():
    factor = TimeHorizonFactor()

    assert factor.compute({"entry_hour": 11, "preferred_session": "morning"}) == 1.0
    assert factor.compute({"entry_hour": 11, "preferred_session": "midday"}) == 1.0


def test_unknown_session_neutral():
    assert TimeHorizonFactor().compute({"entry_hour": 11, "preferred_session": "overnight"}) == 0.5


def test_combined_high():
    value = TimeHorizonFactor().compute(
        {
            "planned_hold_hours": 10,
            "actual_hold_hours": 10,
            "exit_reason": "target",
            "entry_hour": 11,
            "preferred_session": "morning",
        }
    )

    assert value == 1.0


def test_combined_low():
    value = TimeHorizonFactor().compute(
        {
            "planned_hold_hours": 10,
            "actual_hold_hours": 35,
            "exit_reason": "impulse",
            "entry_hour": 15,
            "preferred_session": "morning",
        }
    )

    assert round(value, 4) == 0.2667


def test_output_bounded():
    value = TimeHorizonFactor().compute(
        {"planned_hold_hours": 1, "actual_hold_hours": 1000, "exit_reason": "target"}
    )

    assert 0.0 <= value <= 1.0
