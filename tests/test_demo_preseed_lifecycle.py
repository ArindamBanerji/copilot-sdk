"""Launcher orchestration tests; process boundaries are explicitly isolated."""
from pathlib import Path
from typing import Any
import subprocess

import pytest
import demo


def test_preseed_environment_is_child_only_and_clears_privileges() -> None:
    parent = {key: "true" for key in demo.PRESEED_ENV_KEYS}
    parent["UNRELATED"] = "preserved"
    before = parent.copy()
    seed = demo.preseed_environment(parent, seeding=True)
    normal = demo.preseed_environment(seed, seeding=False)
    assert parent == before
    assert seed["S2P_DEMO_MODE"] == "true"
    assert seed["SOC_DEMO_RESEED_ENABLED"] == "true"
    assert seed["DATAOPS_PROFILE"] == seed["S2P_PROFILE"] == "production"
    assert normal["UNRELATED"] == "preserved"
    assert normal["S2P_DEMO_READ_MODE"] == "true"
    assert normal["SOC_DEMO_COMPARISON_ENABLED"] == "true"
    assert normal["SOC_PROFILE"] == normal["S2P_PROFILE"] == "production"
    for name in ("COPILOT_PRESEED_MODE", "SOC_DEMO_RESEED_ENABLED", "S2P_DEMO_MODE", "TRADING_DEMO_MODE"):
        assert name not in normal


@pytest.mark.parametrize("failed_stage", [None, "SOC"])
def test_preseed_runs_all_jobs_and_restarts_without_privileges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    failed_stage: str | None,
) -> None:
    events: list[str] = []
    monkeypatch.setattr(demo, "BACKEND_LOG_DIR", tmp_path)
    monkeypatch.setattr(demo, "cmd_kill_all", lambda: events.append("kill"))

    def start(selected: Any, args: Any) -> None:
        assert len(selected) == 5
        events.append(args.preseed_phase)

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        script = command[-1] if command[-1].endswith(".py") else command[2]
        label = "SOC" if "preseed_demo_scenarios" in script else "S2P" if "preseed_s2p_demo" in script else "SDK"
        events.append(label)
        assert kwargs["env"]["COPILOT_PRESEED_MODE"] == "true"
        assert kwargs["timeout"] == 1800
        return subprocess.CompletedProcess(command, int(label == failed_stage))

    monkeypatch.setattr(demo, "cmd_start", start)
    monkeypatch.setattr(demo.subprocess, "run", run)
    args = demo.create_parser().parse_args(["--preseed"])
    if failed_stage:
        with pytest.raises(SystemExit, match="1"):
            demo.cmd_preseed(args)
        assert "NOT READY" in capsys.readouterr().out
    else:
        demo.cmd_preseed(args)
        assert "READY — all copilots" in capsys.readouterr().out
    assert events == ["kill", "seed", "SDK", "SOC", "S2P", "kill", "normal"]
