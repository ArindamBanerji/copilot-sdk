"""Loader for frozen benchmark fixture v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EXPECTED_VERSION = "v1"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
FACTORS_PATH = FIXTURE_DIR / "benchmark_factors_v1.json"
OUTCOMES_PATH = FIXTURE_DIR / "benchmark_outcomes_v1.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_header(data: dict[str, Any], key: str) -> None:
    if data.get("version") != EXPECTED_VERSION:
        raise ValueError(f"unsupported benchmark version: {data.get('version')!r}")
    if data.get("frozen") is not True:
        raise ValueError("benchmark fixture must be frozen")
    if key not in data:
        raise ValueError(f"benchmark fixture missing {key!r}")


def load_benchmark() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    factors = _read_json(FACTORS_PATH)
    outcomes = _read_json(OUTCOMES_PATH)
    _validate_header(factors, "decisions")
    _validate_header(outcomes, "outcomes")
    outcome_by_id = {
        str(row["decision_id"]): row
        for row in outcomes["outcomes"]
    }
    combined: list[dict[str, Any]] = []
    for row in factors["decisions"]:
        decision_id = str(row["decision_id"])
        outcome = outcome_by_id.get(decision_id)
        if outcome is None:
            raise ValueError(f"missing outcome for {decision_id}")
        combined.append({**row, "outcome": outcome})
    train = [row for row in combined if row.get("split") == "train"]
    eval_rows = [row for row in combined if row.get("split") == "eval"]
    if len(train) != int(factors["n_train"]) or len(eval_rows) != int(factors["n_eval"]):
        raise ValueError("benchmark split counts do not match header")
    return train, eval_rows
