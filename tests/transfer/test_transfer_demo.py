from __future__ import annotations

import importlib.util
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from copilot_sdk.scoring.scorer import CompoundingScorer


def test_transfer_demo_runs(monkeypatch) -> None:
    original = CompoundingScorer.from_preset

    def from_preset(*args, **kwargs):
        kwargs.setdefault("profile", "test")
        return original(*args, **kwargs)

    monkeypatch.setattr(CompoundingScorer, "from_preset", from_preset)
    path = Path(__file__).resolve().parents[2] / "scripts" / "transfer_demo.py"
    spec = importlib.util.spec_from_file_location("transfer_demo", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = StringIO()
    with redirect_stdout(output):
        assert module.main() == 0
    assert "TRANSFER COMPLETE" in output.getvalue()
