import importlib.util
from pathlib import Path

from copilot_sdk.scoring.scorer import CompoundingScorer


def test_discovery_demo_runs(monkeypatch, capsys):
    original = CompoundingScorer.from_preset

    def from_preset(*args, **kwargs):
        kwargs.setdefault("profile", "test")
        return original(*args, **kwargs)

    monkeypatch.setattr(CompoundingScorer, "from_preset", from_preset)
    path = Path(__file__).resolve().parents[2] / "scripts" / "discovery_demo.py"
    spec = importlib.util.spec_from_file_location("discovery_demo", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.main() == 0
    assert "DISCOVERY COMPLETE" in capsys.readouterr().out
