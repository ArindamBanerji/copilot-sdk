from __future__ import annotations

import argparse
import io
from pathlib import Path
from contextlib import redirect_stdout

import pytest

import demo


def _args(*argv: str) -> argparse.Namespace:
    return demo.create_parser().parse_args(list(argv))


def _clear_active_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for prefix in ("TRADING_ACTIVE_", "PURCHASING_ACTIVE_", "DATAOPS_ACTIVE_", "S2P_ACTIVE_"):
        for suffix in (
            "GRAPH_BACKEND",
            "AGE_DSN",
            "AGE_GRAPH",
            "AGE_DOMAIN",
            "AGE_TEST_MODE",
              "LIVE_AGE_TEST",
          ):
              monkeypatch.delenv(f"{prefix}{suffix}", raising=False)


def _copilot(name: str) -> dict:
    return next(c for c in demo.COPILOTS if c["name"].lower() == name.lower())


class _FakeProcess:
    pid = 4242


def _patch_startup_side_effects(monkeypatch: pytest.MonkeyPatch, calls: list[tuple]) -> None:
    monkeypatch.setattr(demo, "kill_port", lambda port, label: calls.append(("kill", label)))
    monkeypatch.setattr(demo, "check_port", lambda port: False)
    monkeypatch.setattr(demo, "wait_for_health", lambda name, port, timeout=30: calls.append(("health", name)) or True)
    monkeypatch.setattr(demo, "wait_for_frontend", lambda name, port, timeout=15: calls.append(("frontend_wait", name)) or True)
    monkeypatch.setattr(demo, "_maybe_migrate_dev_db", lambda copilot, copilot_dir, data_root: None)

    def fake_popen(command, **kwargs):
        cwd = Path(kwargs.get("cwd", ""))
        env = kwargs.get("env")
        app_name = cwd.parent.name if cwd.name in {"backend", "frontend"} else cwd.name
        kind = "frontend" if command and command[0] == "npx" else "backend"
        calls.append((kind, app_name, env))
        return _FakeProcess()

    monkeypatch.setattr(demo.subprocess, "Popen", fake_popen)


def test_parser_defaults_graph_backends_to_none_and_replay_false() -> None:
    args = _args()

    assert args.trading_graph_backend is None
    assert args.purchasing_graph_backend is None
    assert args.dataops_graph_backend is None
    assert args.s2p_graph_backend is None
    assert args.replay_outbox is False


@pytest.mark.parametrize(
    ("flag", "field"),
    [
        ("--trading-graph-backend", "trading_graph_backend"),
        ("--purchasing-graph-backend", "purchasing_graph_backend"),
        ("--dataops-graph-backend", "dataops_graph_backend"),
        ("--s2p-graph-backend", "s2p_graph_backend"),
    ],
)
@pytest.mark.parametrize("backend", ["sqlite", "age"])
def test_parser_accepts_each_app_graph_backend(flag: str, field: str, backend: str) -> None:
    args = _args(flag, backend)

    assert getattr(args, field) == backend


def test_parser_rejects_invalid_backend_and_has_no_soc_graph_backend() -> None:
    with pytest.raises(SystemExit):
        _args("--trading-graph-backend", "neo4j")
    with pytest.raises(SystemExit):
        _args("--soc-graph-backend", "age")


def test_parser_replay_outbox_flag() -> None:
    assert _args("--replay-outbox").replay_outbox is True


@pytest.mark.parametrize("app_name", ["trading", "purchasing", "dataops", "s2p"])
def test_default_and_sqlite_do_not_inject_active_env(app_name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_active_env(monkeypatch)
    env: dict[str, str] = {}

    demo._inject_active_graph_env(env, app_name, _args())
    demo._inject_active_graph_env(env, app_name, _args(f"--{app_name}-graph-backend", "sqlite"))

    assert env == {}


@pytest.mark.parametrize(
    ("app_name", "prefix", "domain"),
    [
        ("trading", "TRADING_ACTIVE_", "trading"),
        ("purchasing", "PURCHASING_ACTIVE_", "purchasing"),
        ("dataops", "DATAOPS_ACTIVE_", "dataops"),
        ("s2p", "S2P_ACTIVE_", "s2p"),
    ],
)
def test_age_injects_only_matching_active_prefix(
    app_name: str,
    prefix: str,
    domain: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_active_env(monkeypatch)
    monkeypatch.setenv(f"{prefix}AGE_DSN", "postgresql://user:secret@example/db")
    env: dict[str, str] = {"EXISTING": "1"}

    demo._inject_active_graph_env(env, app_name, _args(f"--{app_name}-graph-backend", "age"))

    assert env["EXISTING"] == "1"
    assert env[f"{prefix}GRAPH_BACKEND"] == "age"
    assert env[f"{prefix}AGE_DSN"] == "postgresql://user:secret@example/db"
    assert env[f"{prefix}AGE_GRAPH"] == "governed_copilot_graph"
    assert env[f"{prefix}AGE_DOMAIN"] == domain
    assert "GRAPH_BACKEND" not in env
    other_prefixes = {"TRADING_ACTIVE_", "PURCHASING_ACTIVE_", "DATAOPS_ACTIVE_", "S2P_ACTIVE_"} - {prefix}
    for other in other_prefixes:
        assert not any(key.startswith(other) for key in env)


def test_age_injection_preserves_explicit_graph_and_test_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_active_env(monkeypatch)
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_DSN", "postgresql://example/test")
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_GRAPH", "protocol_v2_test")
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_TEST_MODE", "1")
    env: dict[str, str] = {}

    demo._inject_active_graph_env(env, "dataops", _args("--dataops-graph-backend", "age"))

    assert env["DATAOPS_ACTIVE_AGE_GRAPH"] == "protocol_v2_test"
    assert env["DATAOPS_ACTIVE_AGE_TEST_MODE"] == "1"


def test_soc_is_noop_for_active_graph_injection() -> None:
    env: dict[str, str] = {}

    demo._inject_active_graph_env(env, "soc", _args("--s2p-graph-backend", "age"))

    assert env == {}


def test_age_missing_dsn_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_active_env(monkeypatch)

    with pytest.raises(RuntimeError, match="TRADING_ACTIVE_AGE_DSN"):
        demo._inject_active_graph_env({}, "trading", _args("--trading-graph-backend", "age"))


def test_soc_graph_rejected_for_non_soc(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_active_env(monkeypatch)
    monkeypatch.setenv("S2P_ACTIVE_AGE_DSN", "postgresql://example/test")
    monkeypatch.setenv("S2P_ACTIVE_AGE_GRAPH", "soc_graph")

    with pytest.raises(RuntimeError, match="soc_graph"):
        demo._inject_active_graph_env({}, "s2p", _args("--s2p-graph-backend", "age"))


def test_dsn_redaction_handles_url_keyword_and_empty_values() -> None:
    assert demo._redact_dsn("") == ""
    assert demo._redact_dsn(None) == ""
    redacted_url = demo._redact_dsn("postgresql://alice:secret@example.com/db?password=other")
    assert "alice" not in redacted_url
    assert "secret" not in redacted_url
    assert "other" not in redacted_url
    assert "example.com/db" in redacted_url

    redacted_kv = demo._redact_dsn(
        "host=localhost port=5433 dbname=soc_graph user=postgres password=postgres"
    )
    assert "user=***" in redacted_kv
    assert "password=***" in redacted_kv
    assert "localhost" in redacted_kv
    assert "soc_graph" in redacted_kv


def test_status_labels_do_not_overclaim_managed_age_for_sdk_and_s2p(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_active_env(monkeypatch)
    monkeypatch.setattr(demo, "verify_age", lambda dsn: True)
    monkeypatch.setattr(demo, "verify_wsl2_running", lambda: True)
    monkeypatch.setattr(demo, "check_port", lambda port: False)
    monkeypatch.setattr(
        demo,
        "_read_copilot_data_stats",
        lambda copilot, data_root=demo.DEFAULT_DATA_DIR: {
            "copilot": copilot["name"],
            "db_exists": True,
            "decisions": 3,
            "archived": 0,
        },
    )

    buf = io.StringIO()
    selected = [c for c in demo.COPILOTS if c["name"] in {"SOC", "DataOps", "S2P"}]
    with redirect_stdout(buf):
        demo.cmd_status(selected, args=_args("--dataops-graph-backend", "age"))
    output = buf.getvalue()

    assert "SOC" in output
    assert "managed by AGE (PostgreSQL)" in output
    assert "DataOps" in output
    assert "[AGE new-writes + SQLite history]" in output
    assert "S2P" in output
    assert "[SQLite]" in output
    assert "DataOps       managed by AGE" not in output
    assert "S2P           managed by AGE" not in output


def test_status_uses_env_when_status_invocation_has_no_cli_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_active_env(monkeypatch)
    monkeypatch.setenv("DATAOPS_ACTIVE_GRAPH_BACKEND", "age")

    assert demo._active_graph_status_label("DataOps") == "AGE new-writes + SQLite history"


def test_replay_outbox_missing_module_reports_not_available(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = demo.importlib.import_module

    def fake_import(name: str):
        if name == "copilot_sdk.outbox.replay":
            raise ModuleNotFoundError(name)
        return original_import(name)

    monkeypatch.setattr(demo.importlib, "import_module", fake_import)
    buf = io.StringIO()
    with redirect_stdout(buf):
        ran = demo._run_replay_outbox_if_requested(True)

    assert ran is False
    assert "not available yet; not run" in buf.getvalue()
    assert "completed" not in buf.getvalue().lower()


def test_replay_outbox_default_noop() -> None:
    assert demo._run_replay_outbox_if_requested(False) is False


def test_cmd_start_missing_active_dsn_aborts_before_backend_health_or_frontend(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clear_active_env(monkeypatch)
    calls: list[tuple] = []
    _patch_startup_side_effects(monkeypatch, calls)
    monkeypatch.setattr(demo, "ensure_age_available", lambda dsn: calls.append(("age", dsn)) or True)

    buf = io.StringIO()
    with redirect_stdout(buf):
        demo.cmd_start([_copilot("dataops")], _args("--dataops", "--dataops-graph-backend", "age"), data_root=tmp_path)

    output = buf.getvalue()
    assert "DATAOPS_ACTIVE_AGE_DSN is required" in output
    assert "AGE startup aborted" in output
    assert not [call for call in calls if call[0] in {"age", "backend", "health", "frontend", "frontend_wait"}]
    assert "Platform Ready" not in output


def test_cmd_start_forbidden_soc_graph_aborts_before_backend_or_frontend(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clear_active_env(monkeypatch)
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_DSN", "postgresql://dataops_user:secret@example/dataops")
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_GRAPH", "soc_graph")
    calls: list[tuple] = []
    _patch_startup_side_effects(monkeypatch, calls)

    buf = io.StringIO()
    with redirect_stdout(buf):
        demo.cmd_start([_copilot("dataops")], _args("--dataops", "--dataops-graph-backend", "age"), data_root=tmp_path)

    output = buf.getvalue()
    assert "DATAOPS_ACTIVE_AGE_GRAPH=soc_graph is forbidden" in output
    assert not [call for call in calls if call[0] in {"backend", "health", "frontend", "frontend_wait"}]
    assert "Platform Ready" not in output


def test_cmd_start_prechecks_requested_app_dsn_not_dataops_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clear_active_env(monkeypatch)
    trading_dsn = "postgresql://trading_user:secret@db.example/trading"
    monkeypatch.setenv("TRADING_ACTIVE_AGE_DSN", trading_dsn)
    calls: list[tuple] = []
    checked: list[str] = []
    _patch_startup_side_effects(monkeypatch, calls)
    monkeypatch.setattr(demo, "ensure_age_available", lambda dsn: checked.append(dsn) or True)

    buf = io.StringIO()
    with redirect_stdout(buf):
        demo.cmd_start([_copilot("trading")], _args("--trading", "--trading-graph-backend", "age"), data_root=tmp_path)

    assert checked == [trading_dsn]
    assert demo.AGE_DSN_DATAOPS not in checked
    assert "secret" not in buf.getvalue()


def test_cmd_start_prechecks_each_requested_active_age_dsn_before_starting(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clear_active_env(monkeypatch)
    trading_dsn = "postgresql://trading_user:secret@db.example/trading"
    dataops_dsn = "postgresql://dataops_user:secret@db.example/dataops"
    monkeypatch.setenv("TRADING_ACTIVE_AGE_DSN", trading_dsn)
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_DSN", dataops_dsn)
    calls: list[tuple] = []
    _patch_startup_side_effects(monkeypatch, calls)

    def fake_ensure(dsn: str) -> bool:
        calls.append(("age", dsn))
        return True

    monkeypatch.setattr(demo, "ensure_age_available", fake_ensure)

    demo.cmd_start(
        [_copilot("trading"), _copilot("dataops")],
        _args("--trading", "--dataops", "--trading-graph-backend", "age", "--dataops-graph-backend", "age"),
        data_root=tmp_path,
    )

    age_calls = [call for call in calls if call[0] == "age"]
    backend_calls = [call for call in calls if call[0] == "backend"]
    assert age_calls == [("age", trading_dsn), ("age", dataops_dsn)]
    assert backend_calls
    assert max(calls.index(call) for call in age_calls) < min(calls.index(call) for call in backend_calls)


def test_cmd_start_default_sqlite_path_skips_age_precheck_and_starts_normally(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clear_active_env(monkeypatch)
    calls: list[tuple] = []
    _patch_startup_side_effects(monkeypatch, calls)
    monkeypatch.setattr(demo, "ensure_age_available", lambda dsn: calls.append(("age", dsn)) or True)

    demo.cmd_start([_copilot("dataops")], _args("--dataops", "--dataops-graph-backend", "sqlite"), data_root=tmp_path)

    assert not [call for call in calls if call[0] == "age"]
    assert [call for call in calls if call[0] == "backend"]
    assert [call for call in calls if call[0] == "health"]
    assert [call for call in calls if call[0] == "frontend"]
    assert [call for call in calls if call[0] == "frontend_wait"]


def test_cmd_start_soc_age_behavior_uses_existing_soc_dsn_without_active_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clear_active_env(monkeypatch)
    calls: list[tuple] = []
    checked: list[str] = []
    _patch_startup_side_effects(monkeypatch, calls)
    monkeypatch.setattr(demo, "ensure_age_available", lambda dsn: checked.append(dsn) or True)

    demo.cmd_start([_copilot("soc")], _args("--soc"), data_root=tmp_path)

    assert checked == [demo.AGE_DSN_SOC]
    backend_envs = [call[2] for call in calls if call[0] == "backend"]
    if backend_envs:
        assert backend_envs[0]["GRAPH_BACKEND"] == "age"
        assert "SOC_ACTIVE_GRAPH_BACKEND" not in backend_envs[0]
