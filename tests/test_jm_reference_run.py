"""APP-1B tests using the real SQLite scorer path."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from examples.jm_reference.config import (
    RUN_A_GENERATOR,
    RUN_A_ORACLE,
    RUN_B_GENERATOR,
    RUN_B_ORACLE,
)
from examples.jm_reference.report import generate_report
from examples.jm_reference.run import run_experiment


def test_run_a_centroid_distance_is_real_and_recorded() -> None:
    trajectory = run_experiment(
        "test_run_a_distance",
        replace(RUN_A_GENERATOR, n_decisions=100),
        RUN_A_ORACLE,
    )
    assert trajectory["initial_distance"] is not None
    assert trajectory["final_distance"] is not None
    assert len(trajectory["centroid_distances"]) == 100
    # CC-1 is distance from the deployment prior. The real scorer starts at
    # that prior, so learning divergence increases this raw signal; no metric
    # inversion is permitted merely to claim monotone convergence.
    assert trajectory["final_distance"] > trajectory["initial_distance"]


def test_run_a_iks_increases() -> None:
    trajectory = run_experiment(
        "test_run_a_iks",
        replace(RUN_A_GENERATOR, n_decisions=100),
        RUN_A_ORACLE,
    )
    assert trajectory["final_iks"] > trajectory["initial_iks"]


def test_run_b_runs_without_error() -> None:
    trajectory = run_experiment(
        "test_run_b",
        replace(RUN_B_GENERATOR, n_decisions=100),
        RUN_B_ORACLE,
    )
    assert trajectory["verified_count"] == 100
    assert trajectory["final_epsilon_firm"] is not None


def test_report_files_created(tmp_path: Path) -> None:
    trajectory_a = run_experiment(
        "test_report_a",
        replace(RUN_A_GENERATOR, n_decisions=20),
        RUN_A_ORACLE,
    )
    trajectory_b = run_experiment(
        "test_report_b",
        replace(RUN_B_GENERATOR, n_decisions=20),
        RUN_B_ORACLE,
    )
    paths = generate_report(trajectory_a, trajectory_b, tmp_path)
    json_path = Path(paths["json"])
    html_path = Path(paths["html"])
    assert json_path.exists()
    assert html_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert "<html" in html_path.read_text(encoding="utf-8").lower()
    html_report = html_path.read_text(encoding="utf-8")
    assert "centroid-distance" in html_report
    assert "Measurement State" in html_report
    assert "real_measured" in html_report
    assert "INSTRUMENT_VALIDATED" in html_report


def test_full_loop_touches_all_layers() -> None:
    trajectory = run_experiment(
        "test_full_loop",
        replace(RUN_A_GENERATOR, n_decisions=20),
        RUN_A_ORACLE,
    )
    assert trajectory["centroid_distances"]
    assert trajectory["conservation_states"]
    assert trajectory["iks_values"]
    assert trajectory["epsilon_firm_values"]
    assert trajectory["measurement_states"]
    assert trajectory["verified_count"] == 20


def test_measurement_state_records_transition_for_50_decisions() -> None:
    trajectory = run_experiment(
        "test_measurement_state",
        replace(RUN_A_GENERATOR, n_decisions=50),
        RUN_A_ORACLE,
    )
    states = [item["state"] for item in trajectory["measurement_states"]]
    assert states[0] == "instrument_validated"
    assert len(set(states)) >= 2
    assert all("provenance" in item for item in trajectory["measurement_states"])


def test_module_entry_point(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "examples.jm_reference.run",
            "--decisions",
            "10",
            "--output-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=repo_root,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "report.json").exists()
    assert (tmp_path / "report.html").exists()
