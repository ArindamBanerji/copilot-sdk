from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

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
    conservation_sdk,
    decide_sdk,
    init_sdk,
    journal_sdk,
    learn_sdk,
    parse_factors,
    record_sdk,
    score_sdk,
    status_sdk,
    trust_sdk,
)
from copilot_sdk.scoring.presets.trading import TradingPreset  # noqa: E402


@pytest.fixture
def db_path():
    temp_dir = tempfile.mkdtemp()
    path = Path(temp_dir) / "trading.db"
    try:
        yield str(path)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _all_factors(value: float = 0.5) -> dict[str, float]:
    return {name: value for name in TradingPreset().shape.factor_names}


def _actions() -> list[str]:
    return list(TradingPreset().shape.action_names)


def _category() -> str:
    return TradingPreset().shape.category_names[0]


def _decisions(db_path: str) -> list[dict]:
    scorer = _get_scorer(db_path)
    try:
        return scorer.graph_store.get_decisions("trading", limit=100)
    finally:
        scorer.graph_store.close()


def _verified(db_path: str) -> list[dict]:
    scorer = _get_scorer(db_path)
    try:
        return scorer.graph_store.get_verified_decisions("trading")
    finally:
        scorer.graph_store.close()


def test_init_creates_db(db_path):
    result = init_sdk(db_path)

    assert Path(db_path).exists()
    assert result["db_path"] == db_path
    assert result["categories"]
    assert result["actions"]
    assert result["factors"]


def test_init_idempotent(db_path):
    first = init_sdk(db_path)
    second = init_sdk(db_path)

    assert first["db_path"] == second["db_path"]
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


def test_learn_conservation_pause(monkeypatch):
    class FakeStore:
        def get_decision(self, decision_id):
            return {"decision_id": decision_id, "recommended_action": _actions()[0]}

        def close(self):
            pass

    class PauseScorer:
        graph_store = FakeStore()

        def learn(self, decision_id, action):
            return {"status": "paused", "reason": "conservation_red"}

    monkeypatch.setattr(cli_sdk, "_get_scorer", lambda db_path=None: PauseScorer())

    result = learn_sdk("decision-1", _actions()[0], "ignored.db")

    assert result["decision_id"] == "decision-1"
    assert result["outcome_recorded"] is False
    assert result["reason"] == "conservation_paused"
    assert "ci-trading learn --decision decision-1" in result["hint"]


def test_record_creates_both(db_path):
    result = record_sdk(_category(), _all_factors(), _actions()[0], db_path)

    assert result["decision_id"]
    assert result["outcome_recorded"] is True
    assert len(_decisions(db_path)) == 1
    assert len(_verified(db_path)) == 1


def test_record_conservation_pause(monkeypatch):
    class FakeStore:
        def close(self):
            pass

    class PauseScorer:
        graph_store = FakeStore()

        def score(self, factors, category):
            return SimpleNamespace(
                decision_id="decision-2",
                action=_actions()[0],
                confidence=0.8,
            )

        def learn(self, decision_id, action):
            return {"status": "paused", "reason": "conservation_red"}

    monkeypatch.setattr(cli_sdk, "_get_scorer", lambda db_path=None: PauseScorer())

    result = record_sdk(_category(), _all_factors(), _actions()[0], "ignored.db")

    assert result["decision_id"] == "decision-2"
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
    assert result["db_path"] == db_path


def test_db_path_override(db_path):
    result = init_sdk(db_path)

    assert result["db_path"] == db_path
    assert Path(db_path).exists()


def test_db_path_relative(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = init_sdk("test.db")

    assert result["db_path"] == "test.db"
    assert Path("test.db").exists()


def test_malformed_json():
    with pytest.raises(CLIUsageError) as exc:
        parse_factors("{bad")

    assert "Invalid JSON in --factors" in str(exc.value)
    assert '{"signal_alignment": 0.8, ...}' in exc.value.hint


def test_parse_factors_accepts_json_string():
    factors = _all_factors()
    parsed = parse_factors(json.dumps(factors))

    assert parsed == factors


def test_parser_missing_args_returns_error(capsys):
    with pytest.raises(SystemExit) as exc:
        backend_cli.main(["decide", "--category", _category()])
    captured = capsys.readouterr()

    assert exc.value.code != 0
    payload = json.loads(captured.out)
    assert payload == {"error": "Invalid arguments", "hint": "Run 'ci-trading --help'"}
