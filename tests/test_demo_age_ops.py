from __future__ import annotations

import argparse
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

import demo
from demo import COPILOTS


# Removed: the old active graph API surface no longer exists in demo.py.
# The refactored launcher exposes command functions plus argparse wiring in
# main(), so these tests exercise current behavior rather than resurrecting
# create_parser/_inject_active_graph_env/_maybe_migrate_dev_db.


class _FakeProcess:
    pid = 4242


def _args(**overrides) -> argparse.Namespace:
    values = {
        "diag_mode": False,
        "age_use_pool": False,
        "no_browser": True,
        "preseed": False,
        "graph": False,
        "diag_backend_port": 8001,
        "diag_graph_dsn": "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres sslmode=disable",
        "diag_graph_name": "soc_graph_test",
        "diag_contract": Path("scratch/temp/test_contract.json"),
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def _selected_copilot(tmp_path: Path, *, name: str = "Trading") -> dict:
    source = next(copilot for copilot in COPILOTS if copilot["name"] == name)
    backend = tmp_path / name.lower() / "backend"
    frontend = tmp_path / name.lower() / "frontend"
    (backend / "app").mkdir(parents=True)
    (backend / "app" / "main.py").write_text("# test app\n", encoding="utf-8")
    frontend.mkdir(parents=True)
    (frontend / "package.json").write_text("{}", encoding="utf-8")
    return {**source, "be_path": backend, "fe_path": frontend}


def _patch_safe_start(monkeypatch: pytest.MonkeyPatch, calls: list[tuple]) -> None:
    monkeypatch.setattr(demo, "kill_port", lambda port, label=None: calls.append(("kill", port, label)) or False)
    monkeypatch.setattr(demo, "check_port", lambda port: False)
    monkeypatch.setattr(demo, "wait_for_health", lambda name, port, timeout=30: calls.append(("health", name, port, timeout)) or True)
    monkeypatch.setattr(demo, "wait_for_frontend", lambda name, port, timeout=15: calls.append(("frontend_wait", name, port, timeout)) or True)
    monkeypatch.setattr(demo.webbrowser, "open_new_tab", lambda url: calls.append(("browser", url)))

    def fake_popen(command, **kwargs):
        calls.append(("popen", tuple(command), kwargs.get("cwd"), kwargs.get("env")))
        return _FakeProcess()

    monkeypatch.setattr(demo.subprocess, "Popen", fake_popen)


def test_current_public_constants_define_expected_copilots() -> None:
    names = {copilot["name"].lower() for copilot in demo.COPILOTS}

    assert names == {"soc", "trading", "purchasing", "dataops", "s2p"}
    assert demo.SDK_NAMES == {"trading", "purchasing", "dataops"}
    assert demo.PLAYWRIGHT_NAMES == {"soc", "s2p"}


def test_redact_dsn_redacts_password_key_only() -> None:
    redacted = demo.redact_dsn(
        "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres sslmode=disable"
    )

    assert "password=***" in redacted
    assert "password=postgres" not in redacted
    assert "host=localhost" in redacted


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", "TRUE"])
def test_env_truthy_accepts_true_values(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("DEMO_TEST_FLAG", value)

    assert demo.env_truthy("DEMO_TEST_FLAG") is True


def test_env_truthy_rejects_absent_and_false_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEMO_TEST_FLAG", raising=False)
    assert demo.env_truthy("DEMO_TEST_FLAG") is False

    monkeypatch.setenv("DEMO_TEST_FLAG", "false")
    assert demo.env_truthy("DEMO_TEST_FLAG") is False


def test_known_ports_includes_backend_and_frontend_ports() -> None:
    expected = {
        port
        for copilot in demo.COPILOTS
        for port in (copilot.get("be_port"), copilot.get("fe_port"))
        if port is not None
    }

    assert set(demo.known_ports()) == expected


def test_main_defaults_to_starting_all_copilots(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(sys, "argv", ["demo.py", "--no-browser"])
    monkeypatch.setattr(
        demo,
        "cmd_start",
        lambda selected, args: captured.update({"selected": selected, "args": args}),
    )

    demo.main()

    assert {copilot["name"].lower() for copilot in captured["selected"]} == {
        "soc",
        "trading",
        "purchasing",
        "dataops",
        "s2p",
    }
    assert captured["args"].no_browser is True


def test_main_sdk_flag_selects_sdk_copilots(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(sys, "argv", ["demo.py", "--sdk", "--no-browser"])
    monkeypatch.setattr(
        demo,
        "cmd_start",
        lambda selected, args: captured.update({"selected": selected, "args": args}),
    )

    demo.main()

    assert {copilot["name"].lower() for copilot in captured["selected"]} == demo.SDK_NAMES


def test_main_playwright_flag_selects_playwright_copilots(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(sys, "argv", ["demo.py", "--playwright", "--no-browser"])
    monkeypatch.setattr(
        demo,
        "cmd_start",
        lambda selected, args: captured.update({"selected": selected, "args": args}),
    )

    demo.main()

    assert {copilot["name"].lower() for copilot in captured["selected"]} == demo.PLAYWRIGHT_NAMES


def test_main_diag_mode_selects_soc_and_sets_diag_args(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "demo.py",
            "--diag-mode",
            "--diag-graph-name",
            "soc_graph_test",
            "--diag-backend-port",
            "8001",
            "--no-browser",
        ],
    )
    monkeypatch.setattr(
        demo,
        "cmd_start",
        lambda selected, args: captured.update({"selected": selected, "args": args}),
    )

    demo.main()

    assert [copilot["name"].lower() for copilot in captured["selected"]] == ["soc"]
    assert captured["args"].diag_mode is True
    assert captured["args"].diag_graph_name == "soc_graph_test"
    assert captured["args"].diag_backend_port == 8001


def test_main_dispatches_status_stop_and_kill_all(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(demo, "cmd_status", lambda selected: calls.append("status"))
    monkeypatch.setattr(demo, "cmd_stop", lambda selected: calls.append("stop"))
    monkeypatch.setattr(demo, "cmd_kill_all", lambda: calls.append("kill_all"))

    for flag, expected in [("--status", "status"), ("--stop", "stop"), ("--kill-all", "kill_all")]:
        monkeypatch.setattr(sys, "argv", ["demo.py", flag])
        demo.main()
        assert calls[-1] == expected


def test_cmd_status_reports_age_and_selected_copilot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(demo, "verify_age", lambda dsn: True)
    monkeypatch.setattr(demo, "verify_wsl2_running", lambda: True)
    monkeypatch.setattr(demo, "check_port", lambda port: port == 8010)
    monkeypatch.setattr(demo, "check_health", lambda port: {"domain": "soc"} if port == 8010 else None)
    soc = next(copilot for copilot in demo.COPILOTS if copilot["name"] == "SOC")

    buf = io.StringIO()
    with redirect_stdout(buf):
        demo.cmd_status([soc])

    output = buf.getvalue()
    assert "AGE/PostgreSQL  UP" in output
    assert "SOC" in output
    assert "[AGE]" in output


def test_cmd_start_starts_backend_and_frontend_with_mocked_processes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[tuple] = []
    _patch_safe_start(monkeypatch, calls)
    selected = [_selected_copilot(tmp_path, name="Trading")]

    demo.cmd_start(selected, _args())

    commands = [call[1] for call in calls if call[0] == "popen"]
    assert any("-m" in command and "uvicorn" in command for command in commands)
    assert any(command[:2] == ("npx", "vite") for command in commands)
    assert any(call[0] == "health" for call in calls)
    assert any(call[0] == "frontend_wait" for call in calls)


def test_cmd_start_age_precheck_blocks_age_only_selection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[tuple] = []
    _patch_safe_start(monkeypatch, calls)
    monkeypatch.setattr(demo, "ensure_age_available", lambda dsn: calls.append(("age", dsn)) or False)
    selected = [_selected_copilot(tmp_path, name="DataOps")]

    buf = io.StringIO()
    with redirect_stdout(buf):
        demo.cmd_start(selected, _args())

    assert ("age", selected[0]["graph_dsn"]) in calls
    assert not [call for call in calls if call[0] == "popen"]
    assert "Cannot start AGE-dependent copilots" in buf.getvalue()


def test_cmd_start_diag_mode_writes_contract_after_healthy_backend(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[tuple] = []
    contract = tmp_path / "soc_diag_backend_contract.json"
    _patch_safe_start(monkeypatch, calls)
    for env_name in (
        "GRAPH_BACKEND",
        "GRAPH_DSN",
        "AGE_GRAPH_NAME",
        "SOC_LEARNING_ENABLED",
        "PYTHONPATH",
        "AGE_USE_POOL",
    ):
        monkeypatch.setenv(env_name, "")
    monkeypatch.setattr(demo, "ensure_age_available", lambda dsn: True)
    monkeypatch.setattr(
        demo,
        "ensure_soc_diag_graph",
        lambda graph_name, dsn: {"connection_mode": "pooled", "pool_available": "true"},
    )
    monkeypatch.setattr(demo, "remove_soc_diag_contract", lambda path: calls.append(("remove_contract", path)))
    monkeypatch.setattr(
        demo,
        "write_soc_diag_contract",
        lambda **kwargs: calls.append(("write_contract", kwargs)),
    )
    soc = _selected_copilot(tmp_path, name="SOC")
    args = _args(
        diag_mode=True,
        age_use_pool=True,
        diag_contract=contract,
        diag_graph_name="soc_graph_test",
    )

    demo.cmd_start([soc], args)

    assert any(call[0] == "remove_contract" for call in calls)
    write_calls = [call for call in calls if call[0] == "write_contract"]
    assert len(write_calls) == 1
    assert write_calls[0][1]["graph_name"] == "soc_graph_test"
    assert write_calls[0][1]["connection_mode"] == "pooled"
    assert write_calls[0][1]["pool_available"] == "true"


def test_run_preseed_skips_soc_live_preseed_when_no_soc_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    dataops = [c for c in COPILOTS if c["name"] == "DataOps"]
    monkeypatch.setattr(demo, "run_deterministic_preseed", lambda fail_hard=True: calls.append("deterministic"))
    monkeypatch.setattr(demo, "run_soc_preseed", lambda copilot: calls.append(f"soc:{copilot['name']}"))

    demo.run_preseed(dataops)

    assert calls == ["deterministic"]
