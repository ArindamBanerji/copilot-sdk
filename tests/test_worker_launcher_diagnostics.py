from __future__ import annotations

from pathlib import Path

import pytest

import demo


def test_worker_default_and_reload_arguments() -> None:
    parser = demo.create_parser()
    assert parser.parse_args([]).workers == 1
    args = parser.parse_args(["--workers", "2", "--reload", "--no-browser"])
    assert args.workers == 2 and args.reload and args.no_browser
    for value in ("0", "-1", "two"):
        with pytest.raises(SystemExit):
            parser.parse_args(["--workers", value])


def test_startup_hint_survives_worker_respawn_noise(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "worker.log"
    path.write_text("ModuleNotFoundError: missing_dependency\n" + "Worker restarting\n" * 25)
    demo.print_backend_startup_diagnostics("Purchasing", path)
    output = capsys.readouterr().out
    assert output.count("Worker restarting") == 20
    assert "missing_dependency" not in output
    assert "Hint: Activate" in output


@pytest.mark.parametrize("pattern", [
    "ImportError", "ModuleNotFoundError", "KeyError", "Address in use",
    "GRAPH_DSN", "ConnectionRefusedError",
])
def test_startup_diagnostics_tail_and_hint(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], pattern: str,
) -> None:
    path = tmp_path / "purchasing.log"
    lines = [f"startup line {index}" for index in range(25)] + [pattern]
    path.write_text("\n".join(lines), encoding="utf-8")
    demo.print_backend_startup_diagnostics("Purchasing", path)
    output = capsys.readouterr().out
    assert "startup line 5\n" not in output
    assert "startup line 6\n" in output
    assert pattern in output
    assert "Hint:" in output
