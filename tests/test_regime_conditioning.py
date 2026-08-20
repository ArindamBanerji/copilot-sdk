from __future__ import annotations

from copilot_sdk.regime import (
    PerRegimeCentroidTracker,
    RegimeConservation,
    RegimeLearningRate,
)


def test_rc_01_volatile_tightens_theta() -> None:
    assert RegimeConservation().adjust_theta_min(2.0, "volatile") == 3.0


def test_rc_02_calm_loosens_theta() -> None:
    assert RegimeConservation().adjust_theta_min(2.0, "calm") == 1.6


def test_rc_03_volatile_increases_penalty() -> None:
    assert RegimeConservation().adjust_penalty_ratio(3.0, "volatile") == 6.0


def test_rc_04_volatile_slows_learning() -> None:
    assert RegimeLearningRate().adjust_eta(0.05, "volatile") == 0.025


def test_rc_05_calm_accelerates_learning() -> None:
    assert RegimeLearningRate().adjust_eta(0.05, "calm") == 0.07500000000000001


def test_rc_06_default_regime_preserves_base_values() -> None:
    conservation = RegimeConservation()
    learning = RegimeLearningRate()
    assert conservation.adjust_theta_min(2.0, "trending") == 2.0
    assert conservation.adjust_penalty_ratio(3.0, "trending") == 3.0
    assert learning.adjust_eta(0.05, "trending") == 0.05


def test_rc_07_unknown_regime_is_fail_safe() -> None:
    assert RegimeConservation().adjust_theta_min(2.0, "other") == 2.0
    assert RegimeLearningRate().adjust_eta(0.05, "other") == 0.05


def test_rc_08_tracker_records_per_regime_movement() -> None:
    tracker = PerRegimeCentroidTracker()
    tracker.record("volatile", [[0.0, 0.0]], [[3.0, 4.0]])
    tracker.record("calm", [[0.0, 0.0]], [[0.0, 1.0]])
    assert tracker.get("volatile")["last_movement"] == 5.0
    assert tracker.get("calm")["last_movement"] == 1.0


def test_rc_09_convergence_speed_is_regime_specific() -> None:
    tracker = PerRegimeCentroidTracker()
    tracker.record("volatile", [0.0], [1.0])
    tracker.record("calm", [0.0], [0.1])
    assert tracker.convergence_speed("calm") > tracker.convergence_speed("volatile")


def test_rc_14_tracker_output_is_json_safe() -> None:
    snapshot = PerRegimeCentroidTracker().snapshot()
    assert snapshot == {}


def test_rc_16_theta_floor_is_enforced() -> None:
    assert RegimeConservation(absolute_minimum=0.25).adjust_theta_min(0.01, "calm") == 0.25


def test_rc_17_regime_change_recalculates_parameters() -> None:
    conservation = RegimeConservation()
    assert conservation.adjust_theta_min(1.0, "volatile") != conservation.adjust_theta_min(1.0, "calm")
