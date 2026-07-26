from __future__ import annotations

import importlib.util
import contextlib
import io
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
        profile="test",
    )
    try:
        summary = target.warm_start(
            demo.build_transfer_registry(),
            category_mapping={
                "freshness_violation": "trend_following",
                "pipeline_failure": "mean_reversion",
            },
            blend_weight=0.35,
        )
    finally:
        target.graph_store.close()

    assert summary["applied"] == 2, f"warm_start did not apply demo patterns: {summary}"
    assert summary["score"] > 0.0
    assert summary["source_copilots"] == ["dataops"]


def test_warm_start_demo_script_runs(monkeypatch) -> None:
    original = CompoundingScorer.from_preset

    def from_preset(*args, **kwargs):
        kwargs.setdefault("profile", "test")
        return original(*args, **kwargs)

    monkeypatch.setattr(CompoundingScorer, "from_preset", from_preset)
    demo = _load_demo_module()
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        assert demo.main() == 0
    text = output.getvalue()
    assert "WARM START TRANSFER COMPLETE" in text
    assert "source_copilot=dataops" in text
    assert "target_copilot=trading" in text
    assert "applied=2" in text
    assert "source_copilots=dataops" in text
