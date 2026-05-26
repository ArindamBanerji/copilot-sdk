from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from click.testing import CliRunner


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import cli as purchasing_cli  # noqa: E402


FACTORS = {
    "expected_demand": 0.8,
    "day_of_week": 0.3,
    "weather_forecast": 0.6,
    "event_flag": 0.1,
    "historical_waste": 0.2,
    "supplier_lead_time": 0.5,
    "price_memory_index": 0.7,
}


def _runner() -> CliRunner:
    return CliRunner()


def _db_path(tmp_path: Path, name: str = "purchasing.db") -> Path:
    return tmp_path / name


def _invoke(tmp_path: Path, *args: str, db_name: str = "purchasing.db"):
    return _runner().invoke(
        purchasing_cli.cli,
        ["--db-path", str(_db_path(tmp_path, db_name)), *args],
    )


def _score(tmp_path: Path, category: str = "protein", db_name: str = "purchasing.db"):
    return _invoke(
        tmp_path,
        "score",
        "--category",
        category,
        "--factors",
        json.dumps(FACTORS),
        db_name=db_name,
    )


def _decision_id(output: str) -> str:
    match = re.search(r"^decision_id:\s*(\S+)", output, flags=re.MULTILINE)
    assert match is not None
    return match.group(1)


def _decision_count(output: str) -> int:
    match = re.search(r"^total_decisions:\s*(\d+)", output, flags=re.MULTILINE)
    assert match is not None
    return int(match.group(1))


def test_score_valid_input_exits_zero(tmp_path: Path):
    result = _score(tmp_path)

    assert result.exit_code == 0, result.output


def test_score_output_includes_input_category_name(tmp_path: Path):
    result = _score(tmp_path, category="produce")

    assert result.exit_code == 0
    assert "category: produce" in result.output


def test_score_output_includes_purchasing_action_names(tmp_path: Path):
    result = _score(tmp_path)

    assert result.exit_code == 0
    for action in ("order_as_planned", "order_more", "order_less", "skip"):
        assert action in result.output


def test_score_output_includes_decision_id(tmp_path: Path):
    result = _score(tmp_path)

    assert result.exit_code == 0
    assert _decision_id(result.output)


def test_score_output_includes_probabilities(tmp_path: Path):
    result = _score(tmp_path)

    assert result.exit_code == 0
    assert "probabilities:" in result.output


def test_score_accepts_repeated_factor_values(tmp_path: Path):
    args = ["score", "--category", "protein"]
    for name, value in FACTORS.items():
        args.extend(["--factor", f"{name}={value}"])

    result = _invoke(tmp_path, *args)

    assert result.exit_code == 0, result.output
    assert "factor_count: 7" in result.output


def test_score_wrong_factor_count_exits_nonzero(tmp_path: Path):
    factors = dict(FACTORS)
    factors.pop("price_memory_index")

    result = _invoke(
        tmp_path,
        "score",
        "--category",
        "protein",
        "--factors",
        json.dumps(factors),
    )

    assert result.exit_code != 0
    assert "missing factors" in result.output
    assert "price_memory_index" in result.output


def test_score_unknown_factor_exits_nonzero(tmp_path: Path):
    factors = dict(FACTORS)
    factors["unknown_factor"] = 0.4

    result = _invoke(
        tmp_path,
        "score",
        "--category",
        "protein",
        "--factors",
        json.dumps(factors),
    )

    assert result.exit_code != 0
    assert "unknown factors" in result.output
    assert "unknown_factor" in result.output


def test_score_invalid_category_exits_nonzero(tmp_path: Path):
    result = _score(tmp_path, category="unknown_category")

    assert result.exit_code != 0
    assert "Unknown category" in result.output
    assert "protein" in result.output


def test_score_non_numeric_factor_exits_nonzero(tmp_path: Path):
    factors = dict(FACTORS)
    factors["weather_forecast"] = "clear"

    result = _invoke(
        tmp_path,
        "score",
        "--category",
        "protein",
        "--factors",
        json.dumps(factors),
    )

    assert result.exit_code != 0
    assert "weather_forecast" in result.output
    assert "numeric" in result.output


def test_learn_valid_action_exits_zero_after_score(tmp_path: Path):
    score = _score(tmp_path)
    decision_id = _decision_id(score.output)

    result = _invoke(
        tmp_path,
        "learn",
        "--decision-id",
        decision_id,
        "--actual-action",
        "order_as_planned",
    )

    assert result.exit_code == 0, result.output
    assert f"decision_id: {decision_id}" in result.output


def test_score_then_learn_flow_uses_created_decision_id(tmp_path: Path):
    score = _score(tmp_path)
    decision_id = _decision_id(score.output)

    result = _invoke(
        tmp_path,
        "learn",
        "--decision-id",
        decision_id,
        "--actual-action",
        "order_as_planned",
    )

    assert result.exit_code == 0, result.output
    assert "actual_action: order_as_planned" in result.output
    assert "iks_after:" in result.output


def test_learn_invalid_action_exits_nonzero_and_lists_valid_actions(tmp_path: Path):
    score = _score(tmp_path)
    decision_id = _decision_id(score.output)

    result = _invoke(
        tmp_path,
        "learn",
        "--decision-id",
        decision_id,
        "--actual-action",
        "invalid_action",
    )

    assert result.exit_code != 0
    assert "Unknown action" in result.output
    assert "order_as_planned" in result.output


def test_learn_nonexistent_decision_id_exits_nonzero(tmp_path: Path):
    result = _invoke(
        tmp_path,
        "learn",
        "--decision-id",
        "missing-decision",
        "--actual-action",
        "order_as_planned",
    )

    assert result.exit_code != 0
    assert "Decision ID not found" in result.output


def test_conservation_exits_zero(tmp_path: Path):
    result = _invoke(tmp_path, "conservation")

    assert result.exit_code == 0, result.output


def test_conservation_output_includes_status_keyword(tmp_path: Path):
    result = _invoke(tmp_path, "conservation")

    assert result.exit_code == 0
    assert any(status in result.output for status in ("GREEN", "AMBER", "RED"))


def test_conservation_output_includes_q_and_theta_min(tmp_path: Path):
    result = _invoke(tmp_path, "conservation")

    assert result.exit_code == 0
    assert "q:" in result.output
    assert "theta_min:" in result.output


def test_conservation_after_learn_counts_verified_decision(tmp_path: Path):
    score = _score(tmp_path)
    decision_id = _decision_id(score.output)
    learned = _invoke(
        tmp_path,
        "learn",
        "--decision-id",
        decision_id,
        "--actual-action",
        "order_as_planned",
    )
    assert learned.exit_code == 0

    result = _invoke(tmp_path, "conservation")

    assert result.exit_code == 0
    assert "total_decisions: 1" in result.output
    assert "verified_count: 1" in result.output


def test_trajectory_exits_zero(tmp_path: Path):
    result = _invoke(tmp_path, "trajectory")

    assert result.exit_code == 0, result.output


def test_trajectory_output_contains_iks_information(tmp_path: Path):
    result = _invoke(tmp_path, "trajectory")

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["label"] == "IKS trajectory"
    assert "current_iks" in payload
    assert "points" in payload


def test_fingerprint_exits_zero(tmp_path: Path):
    result = _invoke(tmp_path, "fingerprint")

    assert result.exit_code == 0, result.output


def test_fingerprint_output_includes_live_purchasing_factor_names(tmp_path: Path):
    result = _invoke(tmp_path, "fingerprint")

    assert result.exit_code == 0
    payload = json.loads(result.output)
    factor_names = {item["name"] for item in payload["factors"]}
    assert set(FACTORS) == factor_names


def test_backup_exits_zero_and_creates_json_file(tmp_path: Path):
    backup_path = tmp_path / "backup.json"
    assert _score(tmp_path).exit_code == 0

    result = _invoke(tmp_path, "backup", "--output", str(backup_path))

    assert result.exit_code == 0, result.output
    assert backup_path.exists()


def test_backup_json_is_valid_json(tmp_path: Path):
    backup_path = tmp_path / "backup.json"
    assert _score(tmp_path).exit_code == 0

    result = _invoke(tmp_path, "backup", "--output", str(backup_path))

    assert result.exit_code == 0
    payload = json.loads(backup_path.read_text(encoding="utf-8"))
    assert payload["domain"] == "purchasing"
    assert payload["shape"]["n_factors"] == 7


def test_backup_json_includes_decision_count(tmp_path: Path):
    backup_path = tmp_path / "backup.json"
    assert _score(tmp_path).exit_code == 0

    result = _invoke(tmp_path, "backup", "--output", str(backup_path))

    assert result.exit_code == 0
    payload = json.loads(backup_path.read_text(encoding="utf-8"))
    assert payload["decision_count"] == 1
    assert len(payload["decisions"]) == 1
    assert "centroid_checkpoints" in payload


def test_restore_exits_zero_for_cli_backup(tmp_path: Path):
    backup_path = tmp_path / "backup.json"
    assert _score(tmp_path, db_name="source.db").exit_code == 0
    assert _invoke(tmp_path, "backup", "--output", str(backup_path), db_name="source.db").exit_code == 0

    result = _invoke(tmp_path, "restore", "--from", str(backup_path), db_name="target.db")

    assert result.exit_code == 0, result.output
    assert "Restored decisions: 1" in result.output


def test_restore_rejects_wrong_shape_json(tmp_path: Path):
    backup_path = tmp_path / "wrong-shape.json"
    backup_path.write_text(
        json.dumps(
            {
                "domain": "purchasing",
                "shape": {
                    "n_categories": 1,
                    "n_actions": 1,
                    "n_factors": 1,
                    "categories": ["protein"],
                    "actions": ["order_as_planned"],
                    "factors": ["expected_demand"],
                },
                "decisions": [],
                "verified_decisions": [],
            }
        ),
        encoding="utf-8",
    )

    result = _invoke(tmp_path, "restore", "--from", str(backup_path))

    assert result.exit_code != 0
    assert "shape does not match" in result.output
    assert not _db_path(tmp_path).exists()


def test_restore_missing_file_exits_nonzero(tmp_path: Path):
    result = _invoke(tmp_path, "restore", "--from", str(tmp_path / "missing.json"))

    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_restore_malformed_json_exits_nonzero(tmp_path: Path):
    backup_path = tmp_path / "malformed.json"
    backup_path.write_text("{not valid json", encoding="utf-8")

    result = _invoke(tmp_path, "restore", "--from", str(backup_path))

    assert result.exit_code != 0
    assert "Invalid backup JSON" in result.output


def test_restore_invalid_same_shape_payload_does_not_mutate_target_db(tmp_path: Path):
    assert _score(tmp_path, db_name="target.db").exit_code == 0
    before = _invoke(tmp_path, "conservation", db_name="target.db")
    assert _decision_count(before.output) == 1

    backup_path = tmp_path / "invalid-same-shape.json"
    assert _score(tmp_path, db_name="source.db").exit_code == 0
    assert _invoke(tmp_path, "backup", "--output", str(backup_path), db_name="source.db").exit_code == 0
    payload = json.loads(backup_path.read_text(encoding="utf-8"))
    payload["decisions"][0]["decision_id"] = "extra-decision"
    invalid_verified = dict(payload["decisions"][0])
    invalid_verified.update(
        {
            "decision_id": "missing-decision",
            "actual_action": "order_as_planned",
            "actual_index": 0,
            "is_correct": True,
            "verified_at": 1.0,
            "context": {},
        }
    )
    payload["verified_decisions"] = [invalid_verified]
    backup_path.write_text(json.dumps(payload), encoding="utf-8")

    result = _invoke(tmp_path, "restore", "--from", str(backup_path), db_name="target.db")
    after = _invoke(tmp_path, "conservation", db_name="target.db")

    assert result.exit_code != 0
    assert "references unknown decision_id" in result.output
    assert _decision_count(after.output) == 1


def test_backup_restore_roundtrip_preserves_decision_count(tmp_path: Path):
    backup_path = tmp_path / "backup.json"
    assert _score(tmp_path, db_name="source.db").exit_code == 0
    assert _invoke(tmp_path, "backup", "--output", str(backup_path), db_name="source.db").exit_code == 0
    assert _invoke(tmp_path, "restore", "--from", str(backup_path), db_name="target.db").exit_code == 0

    result = _invoke(tmp_path, "conservation", db_name="target.db")

    assert result.exit_code == 0
    assert "total_decisions: 1" in result.output


def test_db_path_isolates_state_between_databases(tmp_path: Path):
    assert _score(tmp_path, db_name="first.db").exit_code == 0

    first = _invoke(tmp_path, "conservation", db_name="first.db")
    second = _invoke(tmp_path, "conservation", db_name="second.db")

    assert "total_decisions: 1" in first.output
    assert "total_decisions: 0" in second.output


def test_weather_forecast_factor_is_numeric_input_only(tmp_path: Path):
    factors = dict(FACTORS)
    factors["weather_forecast"] = 0.25

    result = _invoke(
        tmp_path,
        "score",
        "--category",
        "beverages",
        "--factors",
        json.dumps(factors),
    )

    assert result.exit_code == 0, result.output
    assert "weather_forecast" not in result.output.lower()


def test_help_exits_zero():
    result = _runner().invoke(purchasing_cli.cli, ["--help"])

    assert result.exit_code == 0
    assert "score" in result.output
    assert "restore" in result.output
