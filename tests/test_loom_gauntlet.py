"""Gauntlet reports retain blocked evidence without counting it as success."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from scripts import loom_gauntlet as gauntlet


def test_gauntlet_tally_separates_blocked_and_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[str] = []

    def command(_runner: gauntlet.GauntletRunner, name: str, _command: list[str]) -> gauntlet.StageResult:
        calls.append(name)
        return gauntlet.StageResult(name, "passed", 0.0, 0)

    def beat(domain: str, _port: int, name: str) -> Any:
        calls.append(name)
        status = {"c2": "completed", "c3": "unavailable", "c4": "blocked", "c5": "conservation_blocked"}[name]
        return gauntlet.hero_moments.HeroResult(name, domain, status, "observed result")

    monkeypatch.setattr(gauntlet.GauntletRunner, "_command_stage", command)
    monkeypatch.setattr(gauntlet.hero_moments, "run", beat)
    report_path = tmp_path / "report.json"
    storyboard_path = tmp_path / "storyboard.md"
    assert gauntlet.main(["--copilots", "trading", "--report", str(report_path),
                          "--storyboard", str(storyboard_path)]) == 0  # Existing non-hero exit policy.
    assert calls == ["preseed", "truth_preflight", "c2", "c3", "c4", "c5"]
    assert "1/4 beats passed, 2 blocked, 1 failed" in capsys.readouterr().out
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert [beat["status"] for beat in report["beats"]] == ["completed", "unavailable", "blocked", "conservation_blocked"]
    assert "conservation_blocked" in storyboard_path.read_text(encoding="utf-8")


@pytest.mark.parametrize("result,status,code", [
    (subprocess.CompletedProcess([], 0, "ok", ""), "passed", 0),
    (subprocess.CompletedProcess([], 2, "", "failed"), "failed", 2),
    (subprocess.TimeoutExpired(["test"], 120), "unavailable", None),
])
def test_gauntlet_command_stage_captures_exit_and_timeout(
    monkeypatch: pytest.MonkeyPatch, result: Any, status: str, code: int | None,
) -> None:
    def run(*_args: Any, **_kwargs: Any) -> Any:
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(gauntlet.subprocess, "run", run)
    stage = gauntlet.GauntletRunner()._command_stage("preflight", ["test"])
    assert stage.status == status
    assert stage.return_code == code
    assert stage.output


def test_gauntlet_hero_stage_failure_keeps_nonzero_exit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def command(_runner: gauntlet.GauntletRunner, name: str, _command: list[str]) -> gauntlet.StageResult:
        assert name == "c1_heroes"
        return gauntlet.StageResult(name, "failed", 0.0, 1, "prerequisite_not_met")

    monkeypatch.setattr(gauntlet.GauntletRunner, "_command_stage", command)
    monkeypatch.setattr(gauntlet.hero_moments, "run_verified", lambda domain, _port, beat:
                        gauntlet.hero_moments.HeroResult(beat, domain, "available", "observed"))
    assert gauntlet.main(["--copilots", "dataops", "--heroes", "--skip-preseed", "--skip-preflight",
                          "--report", str(tmp_path / "report.json"),
                          "--storyboard", str(tmp_path / "storyboard.md")]) == 1
