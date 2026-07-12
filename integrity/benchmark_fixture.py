"""Generate the frozen v1 benchmark fixture.

This script is deterministic and writes only under ``integrity/fixtures``.
The checked-in JSON files are the benchmark source of truth.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from copilot_sdk.graph.memory_store import InMemoryGraphStore  # noqa: E402
from copilot_sdk.scoring.scorer import CompoundingScorer  # noqa: E402


VERSION = "v1"
DOMAIN = "trading"
GENERATED = "2026-07-11"
N_TRAIN = 400
N_EVAL = 100
SEED = 20260711
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
FACTORS_PATH = FIXTURE_DIR / "benchmark_factors_v1.json"
OUTCOMES_PATH = FIXTURE_DIR / "benchmark_outcomes_v1.json"


def _header(n_factors: int) -> dict[str, Any]:
    return {
        "version": VERSION,
        "domain": DOMAIN,
        "n_train": N_TRAIN,
        "n_eval": N_EVAL,
        "n_factors": n_factors,
        "generated": GENERATED,
        "frozen": True,
    }


def _outcome_action(
    factors: dict[str, float],
    factor_names: tuple[str, ...],
    action_names: tuple[str, ...],
    category_index: int,
) -> str:
    weights = (1.4, 0.7, 1.2, 0.5, 1.3, -0.8, 1.1, -0.5, 0.6, -0.7)
    z = sum(
        weights[index] * (float(factors[name]) - 0.5)
        for index, name in enumerate(factor_names)
    )
    z += (category_index - 2) * 0.12
    if z >= 0.55:
        return action_names[0]
    if z >= 0.05:
        return action_names[1]
    if z >= -0.45:
        return action_names[2]
    return action_names[3]


def build_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    rng = random.Random(SEED)
    scorer = CompoundingScorer.from_preset(
        DOMAIN,
        graph_store=InMemoryGraphStore(domain=DOMAIN),
        enable_rl=False,
    )
    shape = scorer._preset.shape
    category_names = tuple(shape.category_names)
    action_names = tuple(shape.action_names)
    factor_names = tuple(shape.factor_names)

    decisions: list[dict[str, Any]] = []
    rows: list[tuple[str, str, dict[str, float], str]] = []
    for index in range(N_TRAIN):
        category_index = index % len(category_names)
        factors = {
            name: round(0.05 + 0.90 * rng.random(), 6)
            for name in factor_names
        }
        decision_id = f"bench-{index:04d}"
        rows.append((decision_id, "train", factors, category_names[category_index]))
        decisions.append({
            "decision_id": decision_id,
            "split": "train",
            "category": category_names[category_index],
            "factors": factors,
        })

    outcome_by_id: dict[str, str] = {}
    for decision_id, split, factors, category in rows:
        if split != "train":
            continue
        category_index = category_names.index(category)
        outcome_by_id[decision_id] = _outcome_action(factors, factor_names, action_names, category_index)

    for probe_index in range(N_TRAIN, N_TRAIN + N_EVAL):
        category_index = probe_index % len(category_names)
        factors = {
            name: round(0.05 + 0.90 * rng.random(), 6)
            for name in factor_names
        }
        category = category_names[category_index]
        decision_id = f"bench-{probe_index:04d}"
        rows.append((decision_id, "eval", factors, category))
        decisions.append({
            "decision_id": decision_id,
            "split": "eval",
            "category": category,
            "factors": factors,
        })
        outcome_by_id[decision_id] = _outcome_action(factors, factor_names, action_names, category_index)

    outcomes: list[dict[str, Any]] = []
    for decision_id, split, _factors, _category in rows:
        outcomes.append({
            "decision_id": decision_id,
            "split": split,
            "actual_action": outcome_by_id[decision_id],
            "verified": True,
            "correct": True,
        })

    header = _header(len(factor_names))
    return (
        {**header, "decisions": decisions},
        {**header, "outcomes": outcomes},
    )


def main() -> int:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    if FACTORS_PATH.exists() or OUTCOMES_PATH.exists():
        print("Benchmark fixture already exists. Delete manually to regenerate.")
        return 0
    factors, outcomes = build_fixture()
    FACTORS_PATH.write_text(json.dumps(factors, indent=2) + "\n", encoding="utf-8")
    OUTCOMES_PATH.write_text(json.dumps(outcomes, indent=2) + "\n", encoding="utf-8")
    print("Benchmark fixture generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
