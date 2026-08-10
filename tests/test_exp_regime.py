"""Acceptance tests for the EXP-REGIME A/B/C experiment."""

from __future__ import annotations

import inspect

import numpy as np

from apps.regime_experiment.config import PHASE_1_ORACLE, PHASE_2_ORACLE
from apps.regime_experiment.experiment import compute_gamma, run_experiment
from examples.jm_reference import generator
from examples.jm_reference.oracle import GroundTruthOracle


def test_experiment_runs_to_completion(tmp_path):
    results = run_experiment(total_decisions=100, break_point=50, output_dir=tmp_path)
    assert set(results["arms"]) == {"cold_start", "strategy_A", "strategy_B", "strategy_C"}
    for arm in results["arms"].values():
        assert arm["decisions_phase_1"] == 50
        assert arm["decisions_phase_2"] == 50
        assert len(arm["gt_distances"]) == 50


def test_cold_start_has_no_regime_memory(tmp_path):
    results = run_experiment(total_decisions=60, break_point=30, output_dir=tmp_path)
    cold = results["arms"]["cold_start"]
    assert cold["reinitialize_called"] is False
    assert cold["reinitialize_result"] is None


def test_strategy_a_restores_centroids(tmp_path):
    results = run_experiment(total_decisions=60, break_point=30, output_dir=tmp_path)
    arm = results["arms"]["strategy_A"]
    assert arm["reinitialize_called"] is True
    assert arm["reinitialize_result"]["success"] is True
    assert not np.allclose(arm["pre_break_centroids"], arm["post_reinit_centroids"])


def test_gt_distance_measured_on_oracle(tmp_path):
    results = run_experiment(total_decisions=60, break_point=30, output_dir=tmp_path)
    for arm in results["arms"].values():
        assert arm["gt_distances"]
        assert all(np.isfinite(value) and value > 0.0 for value in arm["gt_distances"])


def test_gamma_computed_when_both_converge():
    assert compute_gamma(100, 50) == 2.0


def test_gamma_none_when_no_convergence():
    assert compute_gamma(None, None) is None


def test_oracle_separation():
    source = inspect.getsource(generator.SyntheticGenerator)
    assert "is_correct" not in source
    assert "label_correct" not in source
    assert "GroundTruthOracle" not in source


def test_two_oracles_have_different_gt():
    first = GroundTruthOracle(PHASE_1_ORACLE).ground_truth_centroids
    second = GroundTruthOracle(PHASE_2_ORACLE).ground_truth_centroids
    assert not np.allclose(first, second)
