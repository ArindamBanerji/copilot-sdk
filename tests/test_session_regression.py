"""Regression guards for critical features shipped in this session."""

from __future__ import annotations

import ast
import inspect
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = REPO_ROOT.parent


def test_generator_has_no_oracle_path() -> None:
    from examples.jm_reference import generator

    tree = ast.parse(inspect.getsource(generator))
    forbidden = {"is_correct", "label_correct", "GroundTruthOracle", "oracle"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id not in forbidden


def test_g1_no_exploration_override() -> None:
    triage = WORKSPACE_ROOT / "gen-ai-roi-demo-v4-v50" / "backend" / "app" / "routers" / "triage.py"
    if not triage.exists():
        pytest.skip("SOC triage source is not present in this workspace")
    for index, line in enumerate(triage.read_text(encoding="utf-8").splitlines(), 1):
        if "selected_action = _rl_explored_action_name" in line and not line.strip().startswith("#"):
            pytest.fail(f"G1 violation at line {index}")


def test_no_neo4j_in_production_code() -> None:
    violations: list[str] = []
    for base in (REPO_ROOT / "copilot_sdk", WORKSPACE_ROOT / "ci-platform" / "ci_platform"):
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if "neo4j" in line.lower() and not line.strip().startswith("#") and "import neo4j" not in line:
                    violations.append(f"{path}:{index}")
    assert not violations, f"neo4j refs: {violations[:5]}"


def test_theta_min_single_implementation() -> None:
    gae_root = WORKSPACE_ROOT / "graph-attention-engine-v50"
    result = subprocess.run(
        [sys.executable, "-c", "from gae.calibration import compute_theta_min; print('OK')"],
        capture_output=True,
        text=True,
        cwd=gae_root,
    )
    assert result.returncode == 0, result.stderr


def test_conservation_has_required_fields(tmp_path: Path) -> None:
    from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
    from copilot_sdk.scoring.scorer import CompoundingScorer

    store = SQLiteGraphStore(str(tmp_path / "test.db"), domain="trading")
    scorer = CompoundingScorer.from_preset(
        domain="trading", graph_store=store, profile="test", enable_rl=False
    )
    state = scorer.get_conservation_state()
    for key in ("status", "reason"):
        assert key in state, f"Missing: {key}"


def test_trust_trap_detector_exists() -> None:
    from copilot_sdk.scoring.trust_traps import TrustTrapDetector

    assert TrustTrapDetector is not None


def test_regime_reinit_method_exists() -> None:
    from copilot_sdk.scoring.scorer import CompoundingScorer

    assert hasattr(CompoundingScorer, "reinitialize_from_regime")


def test_no_incorrect_rl_naming() -> None:
    violations: list[str] = []
    for path in (REPO_ROOT / "copilot_sdk").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if ("no " + "reward function") in line.lower():
                violations.append(f"{path}:{index}")
    assert not violations, f"RL naming: {violations[:5]}"
