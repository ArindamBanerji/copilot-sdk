import subprocess
import sys


def test_discovery_demo_runs():
    result = subprocess.run(
        [sys.executable, "scripts/discovery_demo.py"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DISCOVERY COMPLETE" in result.stdout
