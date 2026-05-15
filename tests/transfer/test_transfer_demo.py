from __future__ import annotations

import subprocess
import sys


def test_transfer_demo_runs() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/transfer_demo.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "TRANSFER COMPLETE" in result.stdout
