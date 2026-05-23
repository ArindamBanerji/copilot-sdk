from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

from copilot_sdk.scoring.scorer import CompoundingScorer


def _load_demo_module() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "scripts" / "demo_warm_start.py"
    spec = importlib.util.spec_from_file_location("demo_warm_start", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_warm_start_transfers_patterns(tmp_path) -> None:
    demo = _load_demo_module()
    target = CompoundingScorer.from_preset(
        "trading",
        db_path=str(tmp_path / "trading.db"),
    )
    try:
        summary = target.warm_start(
            demo.build_transfer_registry(),
            category_mapping={
                "freshness_violation": "equity_long",
                "pipeline_failure": "equity_short",
            },
            blend_weight=0.35,
        )
    finally:
        target.graph_store.close()

    assert summary["applied"] == 2, f"warm_start did not apply demo patterns: {summary}"
    assert summary["score"] > 0.0
    assert summary["source_copilots"] == ["dataops"]


def test_warm_start_demo_script_runs() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/demo_warm_start.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "WARM START TRANSFER COMPLETE" in result.stdout
    assert "source_copilot=dataops" in result.stdout
    assert "target_copilot=trading" in result.stdout
    assert "applied=2" in result.stdout
    assert "source_copilots=dataops" in result.stdout
