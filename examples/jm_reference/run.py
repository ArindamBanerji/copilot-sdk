"""JM Reference App — the real SQLite-backed compounding loop.

Run with:

    python -m examples.jm_reference.run

The loop uses the SDK's real ``CompoundingScorer`` and
``SQLiteGraphStore``.  ``CompoundingScorer.learn`` performs the real outcome
write, centroid update, checkpointing, conservation evaluation, and (when
enabled) evolution pass.  No server, mock, or fake is used.
"""

from __future__ import annotations

import argparse
import os
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.scoring.measurement_state import compute_measurement_state
from copilot_sdk.scoring.scorer import CompoundingScorer

from .config import (
    RUN_A_GENERATOR,
    RUN_A_ORACLE,
    RUN_B_GENERATOR,
    RUN_B_ORACLE,
)
from .generator import GeneratorConfig, SyntheticGenerator
from .oracle import GroundTruthOracle, OracleConfig
from .report import generate_report


def _correct_action(
    oracle: GroundTruthOracle,
    category: str,
    factors: dict[str, float],
    action_names: list[str],
) -> str:
    """Find the oracle-authorized action without exposing hidden centroids."""

    for action in action_names:
        if oracle.label_correct(category, action, factors):
            return action
    raise RuntimeError(f"oracle did not select an action for category {category!r}")


def _learn_iks(result: Any) -> float:
    if isinstance(result, dict):
        return float(result.get("iks_after", 0.0))
    return float(getattr(result, "iks_after", 0.0))


def _conservation_state(scorer: CompoundingScorer) -> dict[str, Any]:
    """Read the scorer's live conservation state after each real outcome."""

    state = scorer._capture_conservation_state()
    if state is None:
        return {"status": "CALIBRATING", "verified_count": scorer.get_verified_count()}
    return {str(key): value for key, value in state.items()}


def _evolution_events(store: SQLiteGraphStore, domain: str) -> list[dict[str, Any]]:
    return [dict(event) for event in store.get_evolution_events(domain, limit=200)]


def run_experiment(
    label: str,
    gen_config: GeneratorConfig,
    oracle_config: OracleConfig,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Run one oracle-separated experiment with real SDK persistence."""

    temporary_db = db_path is None
    if db_path is None:
        db_path = str(Path(tempfile.mkdtemp(prefix=f"jm_{label}_")) / f"{label}.db")
    store = SQLiteGraphStore(db_path, domain="trading")
    previous_outbox_path = os.environ.get("CI_PERSISTENCE_OUTBOX_PATH")
    outbox_path = str(Path(db_path).with_name(f"{label}_outbox.db"))
    os.environ["CI_PERSISTENCE_OUTBOX_PATH"] = outbox_path
    try:
        scorer = CompoundingScorer.from_preset(
            domain="trading",
            graph_store=store,
            # SQLite is intentionally a standalone reference-app store; the SDK
            # test profile permits it while still executing the real scorer path.
            profile="test",
            evolve=True,
            consolidation_enabled=True,
            enable_rl=False,
        )
    except Exception:
        store.close()
        raise
    generator = SyntheticGenerator(gen_config)
    oracle = GroundTruthOracle(oracle_config)
    action_names = list(oracle_config.action_names or [])
    if not action_names:
        raise ValueError("oracle_config.action_names is required for a scorer run")

    trajectory: dict[str, Any] = {
        "label": label,
        "domain": "trading",
        "decisions": [],
        "centroid_distances": [],
        "gt_distances": [],
        "iks_values": [],
        "conservation_states": [],
        "epsilon_firm_values": [],
        "measurement_states": [],
        "evolution_events": [],
        "disruption_step": gen_config.disruption_decision,
        "epsilon_firm_config": oracle_config.epsilon_firm,
    }
    initial_measurement = compute_measurement_state(scorer).to_dict()
    initial_measurement["step"] = 0
    trajectory["measurement_states"].append(initial_measurement)

    try:
        for step in range(gen_config.n_decisions):
            category, factors = generator.generate()
            scored = scorer.score(factors, category)
            is_correct = oracle.label_correct(category, scored.action, factors)
            actual_action = (
                scored.action
                if is_correct
                else _correct_action(oracle, category, factors, action_names)
            )
            learned = scorer.learn(
                decision_id=scored.decision_id,
                actual_action=actual_action,
                outcome="confirmed" if is_correct else "corrected",
                # Synthetic reference runs must continue collecting the full
                # trajectory after a low-quality window; production safety
                # pauses remain visible through the live state below.
                context={"reference_app": True, "preseed": True, "regime": label},
            )
            distance = scorer.compute_centroid_distance_to_canonical()
            current_mu = np.asarray(scorer._scorer.mu, dtype=np.float64)
            ground_truth = np.asarray(oracle.ground_truth_centroids, dtype=np.float64)
            gt_delta = (current_mu - ground_truth).reshape(-1)
            gt_distance = float(np.linalg.norm(gt_delta, ord=2))
            epsilon = scorer.compute_epsilon_firm()
            conservation = _conservation_state(scorer)
            iks = _learn_iks(learned)
            trajectory["decisions"].append(
                {
                    "step": step,
                    "category": category,
                    "action": scored.action,
                    "actual_action": actual_action,
                    "correct": bool(is_correct),
                    "confidence": float(scored.confidence),
                }
            )
            trajectory["centroid_distances"].append(distance)
            trajectory["gt_distances"].append(gt_distance)
            trajectory["iks_values"].append(iks)
            trajectory["conservation_states"].append(conservation)
            trajectory["epsilon_firm_values"].append(
                None if epsilon is None else epsilon.get("epsilon_firm")
            )
            measurement = compute_measurement_state(scorer).to_dict()
            measurement["step"] = step + 1
            trajectory["measurement_states"].append(measurement)
            if (step + 1) % 50 == 0 or step + 1 == gen_config.n_decisions:
                distance_text = "n/a" if distance is None else f"{distance:.4f}"
                print(
                    f"[{label}] step {step + 1}/{gen_config.n_decisions} "
                    f"canonical={distance_text} gt={gt_distance:.4f} "
                    f"iks={iks:.1f} correct={is_correct}"
                )
        trajectory["evolution_events"] = _evolution_events(store, "trading")
        decisions = trajectory["decisions"]
        trajectory["initial_distance"] = trajectory["centroid_distances"][0]
        trajectory["final_distance"] = trajectory["centroid_distances"][-1]
        trajectory["initial_gt_distance"] = trajectory["gt_distances"][0]
        trajectory["final_gt_distance"] = trajectory["gt_distances"][-1]
        trajectory["initial_iks"] = trajectory["iks_values"][0]
        trajectory["final_iks"] = trajectory["iks_values"][-1]
        trajectory["final_epsilon_firm"] = trajectory["epsilon_firm_values"][-1]
        trajectory["total_correct"] = sum(1 for item in decisions if item["correct"])
        trajectory["accuracy"] = trajectory["total_correct"] / len(decisions)
        trajectory["verified_count"] = scorer.get_verified_count()
        trajectory["evolution_event_count"] = len(trajectory["evolution_events"])
        return trajectory
    finally:
        store.close()
        if previous_outbox_path is None:
            os.environ.pop("CI_PERSISTENCE_OUTBOX_PATH", None)
        else:
            os.environ["CI_PERSISTENCE_OUTBOX_PATH"] = previous_outbox_path
        if temporary_db:
            Path(db_path).unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the offline JM reference app")
    parser.add_argument("--decisions", type=int, default=None, help="override decisions per run")
    parser.add_argument("--output-dir", default=".", help="directory for report.json/report.html")
    args = parser.parse_args()
    if args.decisions is not None and args.decisions <= 0:
        parser.error("--decisions must be positive")

    gen_a = replace(RUN_A_GENERATOR, n_decisions=args.decisions) if args.decisions else RUN_A_GENERATOR
    gen_b = replace(RUN_B_GENERATOR, n_decisions=args.decisions) if args.decisions else RUN_B_GENERATOR
    print("=" * 64)
    print("JM Reference App — Judgment Memory Compounding Demo")
    print("=" * 64)
    print("\n--- Run A: epsilon_firm > 0.128 ---")
    trajectory_a = run_experiment("run_a", gen_a, RUN_A_ORACLE)
    print("\n--- Run B: epsilon_firm < 0.128 ---")
    trajectory_b = run_experiment("run_b", gen_b, RUN_B_ORACLE)
    print("\n--- Generating report ---")
    generate_report(trajectory_a, trajectory_b, args.output_dir)
    print("Done. Open report.html to view the offline compounding surfaces.")


if __name__ == "__main__":
    main()
