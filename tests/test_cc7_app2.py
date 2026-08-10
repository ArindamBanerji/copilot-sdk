from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAE_QUICKSTART = ROOT.parent / "graph-attention-engine-v50" / "examples" / "hello_gae"


def test_hello_gae_runs_and_prints_conservation() -> None:
    result = subprocess.run(
        [sys.executable, "hello_gae.py"],
        cwd=GAE_QUICKSTART,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert any(status in result.stdout for status in ("GREEN", "AMBER", "RED"))


def test_app1_runs_without_server(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment["CI_PERSISTENCE_OUTBOX_PATH"] = str(tmp_path / "outbox.db")
    result = subprocess.run(
        [sys.executable, "-m", "examples.jm_reference.run", "--decisions", "20", "--output-dir", str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        env=environment,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "report.json").exists()
    assert (tmp_path / "report.html").exists()


def test_launcher_ports_keep_working_defaults(monkeypatch) -> None:
    monkeypatch.delenv("S2P_BACKEND_PORT", raising=False)
    import demo

    assert demo._port_env("S2P_BACKEND_PORT", 8002) == 8002
    monkeypatch.setenv("S2P_BACKEND_PORT", "8123")
    assert demo._port_env("S2P_BACKEND_PORT", 8002) == 8123
