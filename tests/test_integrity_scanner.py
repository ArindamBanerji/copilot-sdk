from __future__ import annotations

import subprocess
import sys

from integrity import architecture_scan
from integrity.load_benchmark import EXPECTED_VERSION, load_benchmark


def test_scanner_imports() -> None:
    assert architecture_scan.SDK_ROOT.name == "copilot-sdk"


def test_scanner_runs_without_error() -> None:
    result = subprocess.run(
        [sys.executable, "integrity/architecture_scan.py", "--report"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "AGE-01:" in result.stdout


def test_scanner_check_mode() -> None:
    result = subprocess.run(
        [sys.executable, "integrity/architecture_scan.py", "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ENFORCED_FAILURES=" in result.stdout


def test_age_01_no_raw_sql() -> None:
    result = architecture_scan.check_age_raw_sql()
    assert result.code == "AGE-01"
    assert isinstance(result.evidence, tuple)


def test_age_01_exemption_list_matches_real_files() -> None:
    assert architecture_scan.AGE_01_EXEMPT_PATHS
    for relative_path, reason in architecture_scan.AGE_01_EXEMPT_PATHS.items():
        assert (architecture_scan.SDK_ROOT / relative_path).exists()
        assert "migration" in reason


def test_f25_no_rl_naming() -> None:
    result = architecture_scan.check_learning_names()
    assert result.code == "F-25"
    assert isinstance(result.evidence, tuple)


def test_benchmark_fixture_loadable() -> None:
    train, eval_rows = load_benchmark()
    assert len(train) == 400
    assert len(eval_rows) == 100
    assert len(train[0]["factors"]) == 10
    assert train[0]["outcome"]["verified"] is True


def test_benchmark_fixture_deterministic() -> None:
    first = load_benchmark()
    second = load_benchmark()
    assert first == second


def test_benchmark_fixture_version() -> None:
    train, _ = load_benchmark()
    assert train[0]["decision_id"] == "bench-0000"
    assert EXPECTED_VERSION == "v1"
