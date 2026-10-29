#!/usr/bin/env python
"""Seed deterministic Trading screenshot scenarios directly into GraphStore."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import math
import os
from pathlib import Path
import random
import statistics
import sys
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from copilot_sdk.config import GraphConfig
from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.graph.protocol import GraphStore, ProtocolV2GraphStore
from copilot_sdk.scoring.presets import PRESET_REGISTRY


DOMAIN = "trading"
DECISION_COUNT = 250
RNG_SEED = 42
BASE_TIMESTAMP = 1_799_000_000.0
RESET_CUTOFF = 32_503_680_000.0  # 3000-01-01 UTC
SOURCE = "trading_screenshot_scenario"


@dataclass(frozen=True)
class ScenarioDecision:
    sequence: int
    category: str
    category_index: int
    factors: dict[str, float]
    recommended_action: str
    recommended_index: int
    actual_action: str
    actual_index: int
    is_correct: bool
    confidence: float


@dataclass(frozen=True)
class CategorySummary:
    category: str
    correct: int
    total: int
    accuracy: float
    signal: str


@dataclass(frozen=True)
class ScenarioSummary:
    scenario: str
    decisions: int
    correct: int
    accuracy: float
    iks_estimate: float
    conservation: str
    categories: tuple[CategorySummary, ...]
    generation: int
    archived: int = 0


def _shape() -> Any:
    return PRESET_REGISTRY[DOMAIN]().shape


def _degraded_categories(categories: Sequence[str]) -> set[str]:
    preferred = {"scalp_intraday", "income_strategy"}
    if preferred <= set(categories):
        return preferred
    return set(categories[1:3])


def _correct_per_category(scenario: str, categories: Sequence[str]) -> dict[str, int]:
    if scenario == "healthy":
        return {category: 38 for category in categories}
    degraded = _degraded_categories(categories)
    remaining = [category for category in categories if category not in degraded]
    counts = {category: 20 for category in degraded}
    for category, correct in zip(remaining, (25, 25, 26), strict=True):
        counts[category] = correct
    return counts


def _block_counts(total_correct: int) -> tuple[int, ...]:
    base, extra = divmod(total_correct, 5)
    return tuple(base + (1 if block < extra else 0) for block in range(5))


def generate_scenario(
    scenario: str,
    *,
    seed: int = RNG_SEED,
) -> list[ScenarioDecision]:
    """Return the complete deterministic scenario without touching storage."""
    if scenario not in {"healthy", "degraded"}:
        raise ValueError(f"unknown Trading scenario: {scenario}")
    shape = _shape()
    categories = tuple(shape.category_names)
    actions = tuple(shape.action_names)
    factor_names = tuple(shape.factor_names)
    if DECISION_COUNT % len(categories):
        raise ValueError("decision count must divide evenly across Trading categories")
    per_category = DECISION_COUNT // len(categories)
    if per_category != 50:
        raise ValueError("scenario allocation expects 50 decisions per category")

    rng = random.Random(seed)
    correct_targets = _correct_per_category(scenario, categories)
    correct_positions: dict[str, set[int]] = {}
    for category in categories:
        positions: set[int] = set()
        for block, block_correct in enumerate(_block_counts(correct_targets[category])):
            start = block * 10
            positions.update(rng.sample(range(start, start + 10), block_correct))
        correct_positions[category] = positions

    category_seen = {category: 0 for category in categories}
    rows: list[ScenarioDecision] = []
    for sequence in range(1, DECISION_COUNT + 1):
        category_index = (sequence - 1) % len(categories)
        category = categories[category_index]
        category_position = category_seen[category]
        category_seen[category] += 1
        is_correct = category_position in correct_positions[category]
        recommended_index = rng.randrange(len(actions))
        actual_index = (
            recommended_index
            if is_correct
            else (recommended_index + 1 + rng.randrange(len(actions) - 1)) % len(actions)
        )
        factors = {
            name: round(
                max(0.0, min(1.0, 0.43 + factor_index * 0.012 + rng.uniform(-0.018, 0.018))),
                6,
            )
            for factor_index, name in enumerate(factor_names)
        }
        rows.append(
            ScenarioDecision(
                sequence=sequence,
                category=category,
                category_index=category_index,
                factors=factors,
                recommended_action=actions[recommended_index],
                recommended_index=recommended_index,
                actual_action=actions[actual_index],
                actual_index=actual_index,
                is_correct=is_correct,
                confidence=round(0.72 + rng.uniform(0.0, 0.18), 6),
            )
        )
    return rows


def _metadata(decision: ScenarioDecision, scenario: str, generation: int) -> dict[str, Any]:
    shape = _shape()
    decision_id = _decision_id(scenario, generation, decision.sequence)
    factor_vector = [decision.factors[name] for name in shape.factor_names]
    probabilities = [0.0] * shape.n_actions
    probabilities[decision.recommended_index] = decision.confidence
    return {
        "decision_id": decision_id,
        "entity_id": decision_id,
        "category_index": decision.category_index,
        "recommended_index": decision.recommended_index,
        "factor_vector": factor_vector,
        "factor_names": list(shape.factor_names),
        "probabilities": probabilities,
        "created_at": BASE_TIMESTAMP + decision.sequence,
        "planted": True,
        "provenance": "sample",
        "evidence_tier": "T-sim",
        "source": SOURCE,
        "seed": RNG_SEED,
        "scenario": scenario,
        "scenario_generation": generation,
        "scenario_index": decision.sequence,
    }


def _decision_id(scenario: str, generation: int, sequence: int) -> str:
    return f"screenshot-trading-{scenario}-g{generation:03d}-{sequence:04d}"


def _scenario_metadata(row: Mapping[str, Any]) -> Mapping[str, Any]:
    metadata = row.get("metadata")
    return metadata if isinstance(metadata, Mapping) else {}


def _next_generation(store: GraphStore, scenario: str) -> int:
    rows = [*store.get_all_decisions(DOMAIN), *store.get_archived_decisions(DOMAIN)]
    generations = [
        int(metadata.get("scenario_generation", 0))
        for row in rows
        for metadata in [_scenario_metadata(row)]
        if metadata.get("source") == SOURCE and metadata.get("scenario") == scenario
    ]
    return max(generations, default=0) + 1


def reset_trading_decisions(store: GraphStore) -> int:
    """Archive all active Trading decisions while preserving every other domain."""
    before = int(store.count_decisions(DOMAIN))
    archived = 0
    for status in ("pending", "confirmed", "overridden"):
        archived += int(
            store.archive_decisions(
                DOMAIN,
                before=RESET_CUTOFF,
                status_filter=status,
                confirm_verified=status != "pending",
            )
        )
    remaining = int(store.count_decisions(DOMAIN))
    if remaining:
        raise RuntimeError(
            f"Trading reset left {remaining} active decisions (started with {before})"
        )
    return archived


def _write_decision(
    store: GraphStore,
    decision: ScenarioDecision,
    scenario: str,
    generation: int,
) -> None:
    shape = _shape()
    metadata = _metadata(decision, scenario, generation)
    decision_id = str(metadata["decision_id"])
    factor_vector = [decision.factors[name] for name in shape.factor_names]
    probabilities = [0.0] * shape.n_actions
    probabilities[decision.recommended_index] = decision.confidence
    if isinstance(store, ProtocolV2GraphStore):
        store.write_governed_decision(
            decision_id=decision_id,
            domain=DOMAIN,
            category=decision.category,
            category_index=decision.category_index,
            recommended_action=decision.recommended_action,
            recommended_index=decision.recommended_index,
            confidence=decision.confidence,
            probabilities=probabilities,
            factor_vector=factor_vector,
            factor_names=list(shape.factor_names),
            source=SOURCE,
            scorer_version="trading_screenshot_v1",
            preset_version="trading_preset_runtime",
            factor_schema_version="trading_preset_runtime",
            metadata=metadata,
        )
    else:
        written = store.write_decision(
            DOMAIN,
            decision.category,
            decision.recommended_action,
            decision.confidence,
            decision.factors,
            metadata=metadata,
        )
        if written != decision_id:
            raise RuntimeError(f"GraphStore changed scenario decision ID {decision_id!r}")
    store.write_outcome(
        decision_id,
        decision.actual_action,
        decision.is_correct,
        {
            "actual_index": decision.actual_index,
            "verified_at": BASE_TIMESTAMP + decision.sequence + 0.5,
            "context": {
                "planted": True,
                "provenance": "sample",
                "evidence_tier": "T-sim",
                "source": SOURCE,
                "scenario": scenario,
                "scenario_generation": generation,
            },
        },
        domain=DOMAIN,
        outcome="confirmed" if decision.is_correct else "overridden",
        verified_at_epoch=BASE_TIMESTAMP + decision.sequence + 0.5,
        analyst_action=decision.actual_action,
        final_action=decision.actual_action,
        recommended_action=decision.recommended_action,
        was_override=not decision.is_correct,
    )


def _scenario_rows(
    store: GraphStore,
    scenario: str,
    generation: int,
) -> list[dict[str, Any]]:
    return [
        row
        for row in store.get_verified_decisions(DOMAIN, chronological=True)
        if _scenario_metadata(row).get("source") == SOURCE
        and _scenario_metadata(row).get("scenario") == scenario
        and int(_scenario_metadata(row).get("scenario_generation", 0)) == generation
    ]


def _factor_stats(rows: Sequence[ScenarioDecision]) -> dict[str, dict[str, float]]:
    stats: dict[str, dict[str, float]] = {}
    for name in _shape().factor_names:
        values = [row.factors[name] for row in rows]
        stats[name] = {
            "mean": round(statistics.fmean(values), 8),
            "sigma": round(statistics.pstdev(values), 8),
        }
    return stats


def _iks_estimate(rows: Sequence[ScenarioDecision]) -> float:
    if not rows:
        return 0.0
    accuracy = sum(row.is_correct for row in rows) / len(rows)
    stats = _factor_stats(rows)
    mean_sigma = statistics.fmean(item["sigma"] for item in stats.values())
    fingerprint_component = max(0.0, min((1.0 - mean_sigma / 0.5) * 25.0, 25.0))
    categories_with_ten = sum(
        sum(row.category == category for row in rows) >= 10
        for category in _shape().category_names
    )
    coverage = categories_with_ten / int(_shape().n_categories)
    value = (
        min(len(rows) / 500.0, 1.0) * 25.0
        + accuracy * 25.0
        + fingerprint_component
        + coverage * 25.0
    )
    return float(round(value, 1))


def summarize(
    scenario: str,
    rows: Sequence[ScenarioDecision],
    generation: int,
    *,
    archived: int = 0,
) -> ScenarioSummary:
    category_rows: list[CategorySummary] = []
    for category in _shape().category_names:
        scoped = [row for row in rows if row.category == category]
        correct = sum(row.is_correct for row in scoped)
        accuracy = correct / len(scoped) if scoped else 0.0
        signal = "GREEN" if accuracy >= 0.70 else "AMBER" if accuracy >= 0.50 else "RED"
        category_rows.append(CategorySummary(category, correct, len(scoped), accuracy, signal))
    correct = sum(row.is_correct for row in rows)
    accuracy = correct / len(rows) if rows else 0.0
    conservation = "GREEN" if accuracy >= 0.75 else "RED (strained)"
    return ScenarioSummary(
        scenario=scenario,
        decisions=len(rows),
        correct=correct,
        accuracy=accuracy,
        iks_estimate=_iks_estimate(rows),
        conservation=conservation,
        categories=tuple(category_rows),
        generation=generation,
        archived=archived,
    )


def _persist_validation_artifacts(
    store: GraphStore,
    scenario: str,
    generation: int,
    rows: Sequence[ScenarioDecision],
    summary: ScenarioSummary,
) -> None:
    if not isinstance(store, ProtocolV2GraphStore):
        return
    artifact_key = f"trading-screenshot-{scenario}-g{generation:03d}"
    factor_stats = _factor_stats(rows)
    factor_hash = hashlib.sha256(
        "\n".join(_shape().factor_names).encode("utf-8")
    ).hexdigest()
    store.write_fingerprint(
        fingerprint_id=f"{artifact_key}-fingerprint",
        domain=DOMAIN,
        factor_names=list(_shape().factor_names),
        factor_stats=factor_stats,
        skipped_incompatible=0,
        window=len(rows),
        metadata={"source": SOURCE, "scenario": scenario, "generation": generation},
    )
    store.write_centroid_checkpoint(
        checkpoint_id=f"{artifact_key}-checkpoint",
        domain=DOMAIN,
        category=_shape().category_names[0],
        action=_shape().action_names[0],
        centroids={"factor_stats": factor_stats},
        decisions_count=len(rows),
        verified_count=len(rows),
        iks=summary.iks_estimate,
        shape=list(_shape().tensor_shape),
        factor_names_hash=factor_hash,
        quality_window_size=len(rows),
        quality_verified_count=len(rows),
        quality_correct_count=summary.correct,
        rolling_accuracy=summary.accuracy,
        quality_policy_version="trading_screenshot_v1",
        metadata={"source": SOURCE, "scenario": scenario, "generation": generation},
        decision_id=_decision_id(scenario, generation, len(rows)),
    )
    store.write_conservation_status(
        status_id=f"{artifact_key}-conservation",
        domain=DOMAIN,
        V=len(rows),
        q=summary.accuracy,
        alpha=1.0,
        theta_min=0.75 * len(rows),
        verified_count=len(rows),
        correct_count=summary.correct,
        status="GREEN" if summary.accuracy >= 0.75 else "RED",
        policy_version="trading_screenshot_v1",
    )


def seed_scenario(
    store: GraphStore,
    scenario: str,
    *,
    reset: bool = False,
) -> ScenarioSummary:
    generation = _next_generation(store, scenario)
    archived = reset_trading_decisions(store) if reset else 0
    generated = generate_scenario(scenario)
    for decision in generated:
        _write_decision(store, decision, scenario, generation)
    summary = summarize(scenario, generated, generation, archived=archived)
    _persist_validation_artifacts(store, scenario, generation, generated, summary)
    return summary


def verify_scenario(store: GraphStore, summary: ScenarioSummary) -> None:
    rows = _scenario_rows(store, summary.scenario, summary.generation)
    if len(rows) != DECISION_COUNT:
        raise ValueError(f"expected {DECISION_COUNT} verified scenario decisions, found {len(rows)}")
    categories = {str(row.get("category") or "") for row in rows}
    if categories != set(_shape().category_names):
        raise ValueError("Trading scenario does not cover every preset category")
    correct = sum(bool(row.get("is_correct")) for row in rows)
    accuracy = correct / len(rows)
    expected = (0.73, 0.77) if summary.scenario == "healthy" else (0.43, 0.50)
    if not expected[0] <= accuracy <= expected[1]:
        raise ValueError(f"{summary.scenario} accuracy {accuracy:.3f} outside {expected}")
    if int(store.count_decisions(DOMAIN)) < 10:
        raise ValueError("validate_graph_seed_v3 Trading Decision minimum is not met")
    if int(store.count_verified_decisions(DOMAIN)) < 1:
        raise ValueError("validate_graph_seed_v3 Trading Outcome minimum is not met")
    if summary.scenario == "healthy" and summary.iks_estimate < 70.0:
        raise ValueError(f"healthy IKS estimate below 70: {summary.iks_estimate}")
    if summary.scenario == "degraded":
        degraded = _degraded_categories(_shape().category_names)
        by_category = {row.category: row for row in summary.categories}
        for category in degraded:
            accuracy_value = by_category[category].accuracy
            if not 0.38 <= accuracy_value <= 0.42:
                raise ValueError(f"{category} accuracy {accuracy_value:.3f} is not degraded")


def print_summary(summary: ScenarioSummary) -> None:
    print(f"\nTrading screenshot scenario: {summary.scenario}")
    print(f"Generation: {summary.generation}  Archived by reset: {summary.archived}")
    print(f"{'Category':<22} {'Correct':>8} {'Total':>7} {'Accuracy':>10} {'Signal':>9}")
    print(f"{'-' * 22} {'-' * 8} {'-' * 7} {'-' * 10} {'-' * 9}")
    for row in summary.categories:
        print(
            f"{row.category:<22} {row.correct:>8} {row.total:>7} "
            f"{row.accuracy:>9.1%} {row.signal:>9}"
        )
    print(f"{'TOTAL':<22} {summary.correct:>8} {summary.decisions:>7} {summary.accuracy:>9.1%}")
    print(f"IKS estimate: {summary.iks_estimate:.1f}")
    print(f"Conservation: {summary.conservation}")


def _configured_store(graph_dsn: str | None) -> GraphStore:
    overrides: dict[str, Any] = {"backend": "age"}
    if graph_dsn:
        overrides["dsn"] = graph_dsn
    return create_graph_store(config=GraphConfig.load(DOMAIN, overrides=overrides))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, choices=("healthy", "degraded"))
    parser.add_argument("--reset", action="store_true", help="Archive active Trading decisions first")
    parser.add_argument("--verify", action="store_true", help="Verify scenario and Trading graph minima")
    parser.add_argument("--graph-dsn", default=os.environ.get("GRAPH_DSN"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    store: GraphStore | None = None
    try:
        store = _configured_store(args.graph_dsn)
        summary = seed_scenario(store, args.scenario, reset=bool(args.reset))
        if args.verify:
            verify_scenario(store, summary)
        print_summary(summary)
        if args.verify:
            print("Verification: PASS")
        return 0
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        if store is not None:
            store.close()


if __name__ == "__main__":
    sys.exit(main())
