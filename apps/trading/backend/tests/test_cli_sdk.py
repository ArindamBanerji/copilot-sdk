from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import cli as backend_cli  # noqa: E402
import app.cli_sdk as cli_sdk  # noqa: E402
from app.cli_sdk import (  # noqa: E402
    CLIUsageError,
    _get_scorer,
    backup_sdk,
    conservation_sdk,
    decide_sdk,
    export_sdk,
    import_sdk,
    init_sdk,
    journal_sdk,
    learn_sdk,
    parse_factors,
    record_sdk,
    restore_sdk,
    score_sdk,
    status_sdk,
    trust_sdk,
)
from copilot_sdk.scoring.presets.trading import TradingPreset  # noqa: E402


@pytest.fixture
def db_path(trading_live_age_graph):
    # Separate CLI invocations must exercise real persistent state.
    if trading_live_age_graph is None:
        pytest.skip("Requires AGE for cross-invocation durability testing")
    return None  # Leave the retired path argument unset; GraphConfig selects AGE.


def _all_factors(value: float = 0.5) -> dict[str, float]:
    return {name: value for name in TradingPreset().shape.factor_names}


def _actions() -> list[str]:
    return list(TradingPreset().shape.action_names)


def _category() -> str:
    return str(TradingPreset().shape.category_names[0])


def _decisions(db_path: str | None) -> list[dict]:
    scorer = _get_scorer(db_path)
    try:
        return cast(list[dict], scorer.graph_store.get_decisions("trading", limit=100))
    finally:
        scorer.graph_store.close()


def _verified(db_path: str | None) -> list[dict]:
    scorer = _get_scorer(db_path)
    try:
        return cast(list[dict], scorer.graph_store.get_verified_decisions("trading"))
    finally:
        scorer.graph_store.close()


def test_init_reports_configured_age_graph(db_path):
    result = init_sdk(db_path)

    assert result["backend"] == "age"
    assert result["graph"].startswith("protocol_v2_test_")
    assert result["categories"]
    assert result["actions"]
    assert result["factors"]


def test_init_idempotent(db_path):
    first = init_sdk(db_path)
    second = init_sdk(db_path)

    assert first["graph"] == second["graph"]
    assert first["categories"] == second["categories"]
    assert first["actions"] == second["actions"]
    assert first["factors"] == second["factors"]


def test_score_valid(db_path):
    result = score_sdk(_category(), _all_factors(), db_path)

    assert result["action"] in _actions()
    assert 0 <= result["confidence"] <= 1
    assert result["persisted"] is False
    assert set(result["probabilities"]) == set(_actions())


def test_score_invalid_category(db_path):
    with pytest.raises(CLIUsageError) as exc:
        score_sdk("forex", _all_factors(), db_path)

    assert "Unknown category 'forex'" in str(exc.value)
    assert "trend_following" in exc.value.hint


def test_score_invalid_factor_name(db_path):
    factors = _all_factors()
    factors["momentum"] = 0.8

    with pytest.raises(CLIUsageError) as exc:
        score_sdk(_category(), factors, db_path)

    assert "Unknown factor 'momentum'" in str(exc.value)
    assert "signal_alignment" in exc.value.hint


def test_score_factor_out_of_range(db_path):
    factors = _all_factors()
    factors["signal_alignment"] = 1.5

    with pytest.raises(CLIUsageError) as exc:
        score_sdk(_category(), factors, db_path)

    assert "signal_alignment" in str(exc.value)
    assert "between 0.0 and 1.0" in exc.value.hint


def test_score_nan_factor(db_path):
    factors = _all_factors()
    factors["signal_alignment"] = float("nan")

    with pytest.raises(CLIUsageError) as exc:
        score_sdk(_category(), factors, db_path)

    assert "not finite" in str(exc.value)
    assert "between 0.0 and 1.0" in exc.value.hint


def test_score_inf_factor(db_path):
    factors = _all_factors()
    factors["signal_alignment"] = float("inf")

    with pytest.raises(CLIUsageError) as exc:
        score_sdk(_category(), factors, db_path)

    assert "not finite" in str(exc.value)
    assert "between 0.0 and 1.0" in exc.value.hint


def test_score_read_only_no_decision(db_path):
    score_sdk(_category(), _all_factors(), db_path)

    assert _decisions(db_path) == []


def test_decide_creates_decision(db_path):
    result = decide_sdk(_category(), _all_factors(), db_path)

    decisions = _decisions(db_path)
    assert result["persisted"] is True
    assert len(decisions) == 1
    assert decisions[0]["decision_id"] == result["decision_id"]


def test_learn_records_outcome(db_path):
    decision = decide_sdk(_category(), _all_factors(), db_path)

    result = learn_sdk(decision["decision_id"], decision["action"], db_path)

    verified = _verified(db_path)
    assert result["decision_id"] == decision["decision_id"]
    assert result["actual_action"] == decision["action"]
    assert result["is_correct"] is True
    assert result["outcome_recorded"] is True
    assert len(verified) == 1


def test_learn_conservation_pause(db_path):
    decision_id, action = _seed_paused_age_scorer()

    result = learn_sdk(decision_id, action, db_path)

    assert result["decision_id"] == decision_id
    assert result["outcome_recorded"] is False
    assert result["reason"] == "conservation_paused"
    assert f"ci-trading learn --decision {decision_id}" in result["hint"]


def test_record_creates_both(db_path):
    result = record_sdk(_category(), _all_factors(), _actions()[0], db_path)

    assert result["decision_id"]
    assert result["outcome_recorded"] is True
    assert len(_decisions(db_path)) == 1
    assert len(_verified(db_path)) == 1


def test_record_conservation_pause(db_path):
    _seed_paused_age_scorer()
    preview = score_sdk(_category(), _all_factors(), db_path)

    result = record_sdk(_category(), _all_factors(), preview["action"], db_path)

    assert result["decision_id"]
    assert result["outcome_recorded"] is False
    assert result["reason"] == "conservation_paused"
    assert result["recommended"] == result["actual"]
    assert result["warning"]


def test_record_self_confirm_warning(db_path):
    preview = score_sdk(_category(), _all_factors(), db_path)

    result = record_sdk(_category(), _all_factors(), preview["action"], db_path)

    assert result["actual"] == result["recommended"]
    assert result["warning"]


def test_record_no_warning_when_different(db_path):
    preview = score_sdk(_category(), _all_factors(), db_path)
    actual = next(action for action in _actions() if action != preview["action"])

    result = record_sdk(_category(), _all_factors(), actual, db_path)

    assert result["actual"] != result["recommended"]
    assert result["warning"] is None


def test_trust_pre_transition(db_path):
    result = trust_sdk(db_path=db_path)

    assert result["status"] == "learning"
    assert result["decisions_needed"] == 200


def test_conservation_initial(db_path):
    result = conservation_sdk(db_path)

    assert result["phase"] == "A"
    assert result["alpha"] == 0.0
    assert result["verified_count"] == 0
    assert result["status"] in {"BOOTSTRAP", "GREEN", "AMBER", "RED"}


def test_journal_empty(db_path):
    result = journal_sdk(db_path=db_path)

    assert result == []


def test_journal_after_records(db_path):
    record_sdk(_category(), _all_factors(0.55), _actions()[0], db_path)
    record_sdk(_category(), _all_factors(0.60), _actions()[0], db_path)
    record_sdk(_category(), _all_factors(0.65), _actions()[0], db_path)

    result = journal_sdk(db_path=db_path)

    assert len(result) == 3
    assert all(row["decision_id"] for row in result)
    assert all(row["verified"] for row in result)


def test_journal_returns_newest(db_path):
    for idx in range(5):
        record_sdk(_category(), _all_factors(0.50 + idx * 0.01), _actions()[0], db_path)

    all_ids = [row["decision_id"] for row in _decisions(db_path)]
    result = journal_sdk(limit=3, db_path=db_path)

    assert [row["decision_id"] for row in result] == list(reversed(all_ids[-3:]))


def test_status_composition(db_path):
    record_sdk(_category(), _all_factors(), _actions()[0], db_path)

    result = status_sdk(db_path=db_path)

    assert result["phase"] == "A"
    assert "alpha" in result
    assert result["total_decisions"] == 1
    assert result["verified_count"] == 1
    assert result["backend"] == "age"


def test_db_path_override_rejected(tmp_path):
    path = tmp_path / "retired.db"
    with pytest.raises(CLIUsageError, match="--db-path is retired"):
        init_sdk(str(path))
    assert not path.exists()


def test_db_path_relative_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(CLIUsageError, match="--db-path is retired"):
        init_sdk("test.db")
    assert not Path("test.db").exists()


def test_malformed_json():
    with pytest.raises(CLIUsageError) as exc:
        parse_factors("{bad")

    assert "Invalid JSON in --factors" in str(exc.value)
    assert '{"signal_alignment": 0.8, ...}' in exc.value.hint


def test_parse_factors_accepts_json_string():
    factors = _all_factors()
    parsed = parse_factors(json.dumps(factors))

    assert parsed == factors


def test_main_help(capsys):
    with pytest.raises(SystemExit) as exc:
        cli_sdk.main(["--help"])

    captured = capsys.readouterr()
    assert exc.value.code == 0
    assert "ci-trading" in captured.out


def test_export_json(db_path, tmp_path):
    for value in (0.51, 0.52, 0.53):
        decide_sdk(_category(), _all_factors(value), db_path)
    output = tmp_path / "decisions.json"

    result = export_sdk(format="json", output_path=str(output), db_path=db_path)

    data = json.loads(output.read_text(encoding="utf-8"))
    assert result["exported"] == 3
    assert len(data) == 3
    assert data[0]["decision_id"]


def test_export_csv(db_path, tmp_path):
    for value in (0.51, 0.52, 0.53):
        decide_sdk(_category(), _all_factors(value), db_path)
    output = tmp_path / "decisions.csv"

    result = export_sdk(format="csv", output_path=str(output), db_path=db_path)

    lines = output.read_text(encoding="utf-8").splitlines()
    assert result["exported"] == 3
    assert lines[0].startswith("decision_id,category,recommended")
    assert len(lines) == 4


def test_export_empty(db_path, tmp_path):
    output = tmp_path / "empty.json"

    result = export_sdk(format="json", output_path=str(output), db_path=db_path)

    assert result["exported"] == 0
    assert json.loads(output.read_text(encoding="utf-8")) == []


def test_age_backup_requires_database_operation(db_path, tmp_path):
    backup = tmp_path / "backup.dump"
    with pytest.raises(NotImplementedError, match="database-level"):
        backup_sdk(backup_path=str(backup))
    assert not backup.exists()


def test_restore_requires_confirm(db_path, tmp_path):
    result = restore_sdk(str(tmp_path / "backup.dump"), confirm=False)
    assert "Restore is destructive" in result["error"]


def test_age_restore_is_not_a_file_copy(db_path, tmp_path):
    decide_sdk(_category(), _all_factors())
    before = _decisions(None)
    with pytest.raises(NotImplementedError, match="database-level"):
        restore_sdk(str(tmp_path / "backup.dump"), confirm=True)
    assert _decisions(None) == before
    assert len(before) == 1


def test_import_csv_basic(db_path, tmp_path):
    csv_path = tmp_path / "trades.csv"
    csv_path.write_text(
        "ticker,direction,entry_price,size,entry_time\n"
        "AAPL,long,100,10,2026-01-01\n"
        "MSFT,short,200,5,2026-01-02\n",
        encoding="utf-8",
    )

    result = import_sdk(source="csv", file_path=str(csv_path), db_path=db_path)

    assert result["imported"] == 2
    assert result["skipped"] == 0
    assert len(_decisions(db_path)) == 2


def test_import_dedup(db_path, tmp_path):
    csv_path = tmp_path / "trades.csv"
    csv_path.write_text(
        "ticker,direction,entry_price,size,entry_time\n"
        "AAPL,long,100,10,2026-01-01\n",
        encoding="utf-8",
    )

    first = import_sdk(source="csv", file_path=str(csv_path), db_path=db_path)
    second = import_sdk(source="csv", file_path=str(csv_path), db_path=db_path)

    assert first["imported"] == 1
    assert second["imported"] == 0
    assert second["skipped"] == 1
    assert len(_decisions(db_path)) == 1


def test_import_csv_missing_file(tmp_path):
    missing = tmp_path / "missing.csv"

    with pytest.raises(CLIUsageError) as exc:
        import_sdk(source="csv", file_path=str(missing))

    assert "CSV file not found" in str(exc.value)
    assert "valid file path" in exc.value.hint


def test_import_unknown_broker(db_path):
    with pytest.raises(CLIUsageError) as exc:
        import_sdk(source="broker", broker="nonexistent", db_path=db_path)

    assert "Unknown or unavailable broker" in str(exc.value)
    assert "mock, alpaca, ibkr" in exc.value.hint


def test_restore_no_confirm_exit_nonzero(capsys):
    result = cli_sdk.main(["restore", "--backup-path", "x.db"])
    payload = json.loads(capsys.readouterr().out)

    assert result == 1
    assert "Restore is destructive" in payload["error"]


def test_error_payload_returns_nonzero(capsys):
    result = cli_sdk._print_payload({"error": "boom", "hint": "fix it"})
    payload = json.loads(capsys.readouterr().out)

    assert result == 1
    assert payload["error"] == "boom"


def test_all_commands_registered(capsys):
    with pytest.raises(SystemExit):
        cli_sdk.main(["--help"])
    output = capsys.readouterr().out

    for command in [
        "init",
        "score",
        "decide",
        "learn",
        "record",
        "trust",
        "conservation",
        "status",
        "journal",
        "export",
        "backup",
        "restore",
        "import",
    ]:
        assert command in output


def test_parser_missing_args_returns_error(capsys):
    with pytest.raises(SystemExit) as exc:
        backend_cli.main(["decide", "--category", _category()])
    captured = capsys.readouterr()

    assert exc.value.code != 0
    payload = json.loads(captured.out)
    assert payload == {"error": "Invalid arguments", "hint": "Run 'ci-trading --help'"}


def _seed_paused_age_scorer() -> tuple[str, str]:
    scorer = _get_scorer()
    try:
        first = scorer.score(category=_category(), factors=_all_factors())
        other = next(action for action in _actions() if action != first.action)
        assert not isinstance(scorer.learn(first.decision_id, other), dict)
        for _ in range(9):
            decision = scorer.score(category=_category(), factors=_all_factors())
            assert not isinstance(scorer.learn(decision.decision_id, decision.action), dict)
        pending = scorer.score(category=_category(), factors=_all_factors())
        return str(pending.decision_id), str(pending.action)
    finally:
        scorer.graph_store.close()


def test_memory_preview_is_read_only_and_durable_commands_reject(monkeypatch):
    monkeypatch.setenv("TRADING_PROFILE", "test")
    monkeypatch.setenv("TRADING_ACTIVE_GRAPH_BACKEND", "memory")
    result = score_sdk(_category(), _all_factors())
    assert result["persisted"] is False
    with pytest.raises(CLIUsageError, match="need AGE backend"):
        decide_sdk(_category(), _all_factors())


def test_memory_backup_restore_are_inapplicable(monkeypatch, tmp_path, caplog):
    monkeypatch.setenv("TRADING_PROFILE", "test")
    monkeypatch.setenv("TRADING_ACTIVE_GRAPH_BACKEND", "memory")
    path = tmp_path / "backup.dump"
    assert "not applicable" in backup_sdk(str(path))["error"]
    assert "not applicable" in restore_sdk(str(path), confirm=True)["error"]
    assert "not applicable" in caplog.text
    assert not path.exists()
