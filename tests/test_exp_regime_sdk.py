"""ER acceptance tests for the SDK-level EXP-REGIME experiment."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

from copilot_sdk.regime import ReConvergenceExperiment, generate_regime_break, run_experiment


def test_ER_01_scenario_has_a_valid_break() -> None:
    scenario = generate_regime_break("calm", "volatile", 40)
    assert scenario.break_index == 40
    assert scenario.total_decisions == 80
    assert len(scenario.pre_observations) == len(scenario.post_observations) == 40


def test_ER_02_cold_start_resets_geometry() -> None:
    scenario = generate_regime_break("calm", "volatile", 100)
    curve = ReConvergenceExperiment().run(scenario, cold_start=True)
    assert curve.initialized_from_prior_geometry is False


def test_ER_03_indexed_arm_uses_prior_geometry() -> None:
    scenario = generate_regime_break("calm", "volatile", 100)
    curve = ReConvergenceExperiment().run(scenario, cold_start=False)
    assert curve.initialized_from_prior_geometry is True


def test_ER_04_both_arms_converge() -> None:
    report = run_experiment(decisions_per_regime=250)
    assert report.cold_start_curve.decisions_to_threshold is not None
    assert report.regime_indexed_curve.decisions_to_threshold is not None


def test_ER_05_indexed_arm_is_faster() -> None:
    report = run_experiment(decisions_per_regime=250)
    assert report.gamma is not None and report.gamma > 1.0


def test_ER_06_report_contains_both_curves() -> None:
    data = run_experiment(decisions_per_regime=100).to_dict()
    assert "cold_start_curve" in data and "regime_indexed_curve" in data


def test_ER_07_gamma_is_numeric_or_explicitly_unproven() -> None:
    report = run_experiment(decisions_per_regime=100)
    assert report.gamma is None or report.gamma > 0.0


def test_ER_08_statistical_test_is_included() -> None:
    report = run_experiment(decisions_per_regime=100)
    assert report.statistical_test["method"] == "threshold_crossing_ratio"
    assert "gamma_gt_1" in report.statistical_test


def test_ER_09_plot_data_is_json_safe() -> None:
    json.dumps(run_experiment(decisions_per_regime=100).to_dict(), allow_nan=False)


def test_ER_10_cli_contract_data_is_serializable(tmp_path) -> None:
    path = tmp_path / "report.json"
    report = run_experiment(decisions_per_regime=100)
    path.write_text(json.dumps(report.to_dict(), allow_nan=False), encoding="utf-8")
    assert json.loads(path.read_text(encoding="utf-8"))["experiment"] == "EXP-REGIME"


def test_ER_11_multiple_regimes_work() -> None:
    for regime in ("volatile", "calm", "trending"):
        report = run_experiment(post_regime=regime, decisions_per_regime=100)
        assert report.scenario["post_regime"] == regime


def test_ER_12_identical_regime_has_unit_ratio() -> None:
    report = run_experiment(pre_regime="calm", post_regime="calm", decisions_per_regime=100)
    assert report.gamma == 1.0


def test_ER_13_short_pre_regime_is_supported() -> None:
    scenario = generate_regime_break("calm", "volatile", 10)
    assert scenario.total_decisions == 20


def test_ER_14_fixed_seed_is_deterministic() -> None:
    first = run_experiment(seed=7, decisions_per_regime=100).to_dict()
    second = run_experiment(seed=7, decisions_per_regime=100).to_dict()
    assert first == second


def test_ER_15_concurrent_runs_do_not_share_state() -> None:
    with ThreadPoolExecutor(max_workers=4) as pool:
        reports = list(pool.map(lambda _: run_experiment(seed=11, decisions_per_regime=100).report_hash, range(4)))
    assert len(set(reports)) == 1


def test_ER_16_end_to_end_proves_gamma() -> None:
    report = run_experiment(period="2022", decisions_per_regime=250)
    assert report.experiment == "EXP-REGIME"
    assert report.gamma is not None and report.gamma > 1.0
