from __future__ import annotations

from pathlib import Path

from copilot_sdk.scoring.scorer import _ensure_gae_path


def test_gae_path_uses_env_override(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CLAUDE_GAE", str(tmp_path))

    gae_path = _ensure_gae_path()

    assert str(gae_path).startswith(str(tmp_path))


def test_gae_path_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.delenv("CLAUDE_GAE", raising=False)

    gae_path = _ensure_gae_path()

    assert "graph-attention-engine" in str(gae_path)
