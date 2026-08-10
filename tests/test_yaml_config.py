"""APP-5: YAML configuration uses the real SDK scoring loop."""

from __future__ import annotations

import importlib
from pathlib import Path
import subprocess
import sys
from typing import Any, cast

from examples.yaml_config.loader import build_scorer, load_domain_config, load_scorer
from examples.yaml_config.run import run_loop

yaml = cast(Any, importlib.import_module("yaml"))

_EXAMPLE = Path(__file__).parents[1] / "examples" / "yaml_config" / "domain.yaml"


def test_yaml_config_runs() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "examples.yaml_config.run", str(_EXAMPLE)],
        cwd=_EXAMPLE.parents[2],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert "Surfaces:" in result.stdout


def test_yaml_equals_python() -> None:
    yaml_config = load_domain_config(_EXAMPLE)
    python_config = {
        "from": "trading",
        "penalty_ratio": 5.0,
        "factor_weights": {
            "signal_confidence": 1.5,
            "risk_reward_actual": 0.8,
        },
    }
    yaml_decisions = run_loop(build_scorer(yaml_config), seed=19, steps=8)
    python_decisions = run_loop(build_scorer(python_config), seed=19, steps=8)
    assert yaml_decisions == python_decisions


def test_yaml_override_changes_behavior(tmp_path: Path) -> None:
    original = yaml.safe_load(_EXAMPLE.read_text(encoding="utf-8"))
    original["overrides"]["factors"]["thesis_conviction"]["weight"] = 3.0
    modified = tmp_path / "modified.yaml"
    modified.write_text(yaml.safe_dump(original), encoding="utf-8")
    default_decisions = run_loop(load_scorer(_EXAMPLE), seed=5, steps=12)
    modified_decisions = run_loop(load_scorer(modified), seed=5, steps=12)
    assert default_decisions != modified_decisions
