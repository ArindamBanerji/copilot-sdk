"""Safety and smoke tests for the offline Trading APP-3 example."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLONE = ROOT / "examples" / "trading_clone"


def _python_sources() -> list[str]:
    return [path.read_text(encoding="utf-8") for path in CLONE.glob("*.py")]


def test_trading_clone_runs(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "examples.trading_clone.run",
            "--decisions",
            "50",
            "--output-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "report.json").exists()
    assert (tmp_path / "report.html").exists()


def test_trading_clone_no_live_orders() -> None:
    source = "\n".join(_python_sources()).lower()
    assert not any(term in source for term in ("order", "execute", "submit", "live"))


def test_trading_clone_no_api_keys() -> None:
    source = "\n".join(_python_sources()).lower()
    assert not any(term in source for term in ("api_key", "secret", "token", "password", "alpaca"))


def test_oracle_separation() -> None:
    generator = (CLONE / "generator.py").read_text(encoding="utf-8")
    assert "is_correct" not in generator
    assert "label_correct" not in generator
