"""EXP-REGIME: a four-arm regime-memory bake-off.

Every arm receives the same generated category/factor sequence and the same
oracle-authorized outcomes.  The only intervention is model state at the
regime break.  ``gamma_regime`` is computed solely from post-break distance to
the phase-2 oracle ground truth; it is not epsilon_firm and is not canonical
distance.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from examples.jm_reference.generator import GeneratorConfig, SyntheticGenerator
from examples.jm_reference.oracle import GroundTruthOracle, OracleConfig

from .config import (
    CHECKPOINT_INTERVAL,
    CONVERGENCE_THRESHOLD,
    EXPERIMENT_GENERATOR,
    PHASE_1_ORACLE,
    PHASE_2_ORACLE,
    REGIME_1,
    REGIME_2,
    experiment_configs,
)


@dataclass
class ArmResult:
    """Serializable metrics for one experiment arm."""

    name: str
    strategy: str
    gt_distances: list[float] = field(default_factory=list)
    convergence_step: int | None = None
    gamma_regime: float | None = None
    reinitialize_called: bool = False
    reinitialize_result: dict[str, Any] | None = None
    pre_break_centroids: list[list[list[float]]] | None = None
    post_reinit_centroids: list[list[list[float]]] | None = None
    decisions_phase_1: int = 0
    decisions_phase_2: int = 0
    checkpoints_by_regime: dict[str, int] = field(default_factory=dict)


def _centroids(scorer: CompoundingScorer) -> np.ndarray:
    return np.asarray(scorer._scorer.centroids, dtype=np.float64)


def compute_gt_distance(scorer: CompoundingScorer, oracle: GroundTruthOracle) -> float:
    """Return normalized Frobenius distance to the hidden oracle centroids."""

    current = _centroids(scorer)
    ground_truth = np.asarray(oracle.ground_truth_centroids, dtype=np.float64)
    if current.shape != ground_truth.shape:
        raise ValueError(f"centroid shape {current.shape} != oracle shape {ground_truth.shape}")
    delta = (current - ground_truth).reshape(-1)
    return float(np.linalg.norm(delta, ord=2) / max(np.sqrt(current.size), 1.0))


def compute_gamma(cold_convergence_step: int | None, strategy_convergence_step: int | None) -> float | None:
    """Compute gamma_regime from post-break convergence steps."""

    if cold_convergence_step is None and strategy_convergence_step is None:
        return None
    if strategy_convergence_step is None:
        return 0.0
    if cold_convergence_step is None:
        return float("inf")
    if strategy_convergence_step == 0:
        return float("inf")
    return float(cold_convergence_step / strategy_convergence_step)


def _correct_action(
    oracle: GroundTruthOracle,
    category: str,
    factors: dict[str, float],
    action_names: list[str],
) -> str:
    """Ask the oracle for the authorized action without exposing its centroids."""

    for action in action_names:
        if oracle.label_correct(category, action, factors):
            return action
    raise RuntimeError(f"oracle did not select an action for {category!r}")


def _checkpoint(scorer: CompoundingScorer, scored: Any, regime: str, count: int) -> bool:
    """Persist a V2 checkpoint tagged for regime retrieval.

    This intentionally uses the scorer's existing checkpoint writer so DK
    weights, temperature, factor schema, and centroids are captured together.
    """

    return bool(
        scorer._save_centroids_checkpoint(
            decision_id=str(scored.decision_id),
            category=str(scored.category),
            action=str(scored.action),
            iks=0.0,
            boundary="exp_regime",
            decisions_in_batch=count,
            regime_tag=regime,
            raise_on_error=True,
        )
    )


def _new_scorer(db_path: str) -> tuple[CompoundingScorer, SQLiteGraphStore]:
    store = SQLiteGraphStore(db_path, domain="trading")
    scorer = CompoundingScorer.from_preset(
        domain="trading",
        graph_store=store,
        profile="test",
        evolve=False,
        consolidation_enabled=False,
        enable_rl=False,
    )
    return scorer, store


def run_arm(
    name: str,
    strategy: str,
    gen_config: GeneratorConfig,
    phase1_oracle_config: OracleConfig,
    phase2_oracle_config: OracleConfig,
    break_point: int,
    convergence_threshold: float,
    output_dir: str | os.PathLike[str] | None = None,
) -> ArmResult:
    """Run one arm with an isolated SQLite store."""

    del output_dir  # reserved for future per-arm artifacts; stores stay temporary
    temp_dir = Path(tempfile.mkdtemp(prefix=f"exp_regime_{name}_"))
    previous_outbox = os.environ.get("CI_PERSISTENCE_OUTBOX_PATH")
    os.environ["CI_PERSISTENCE_OUTBOX_PATH"] = str(temp_dir / "outbox.db")
    scorer, store = _new_scorer(str(temp_dir / "arm.db"))
    generator = SyntheticGenerator(gen_config)
    phase1_oracle = GroundTruthOracle(phase1_oracle_config)
    phase2_oracle = GroundTruthOracle(phase2_oracle_config)
    action_names = list(phase1_oracle_config.action_names or [])
    result = ArmResult(name=name, strategy=strategy)
    phase1_checkpoint_count = 0
    phase2_checkpoint_count = 0

    try:
        for step in range(gen_config.n_decisions):
            # Reinitialize before the first post-break decision.  The latest
            # stored checkpoint is intentionally from decision 225, leaving a
            # measurable pre-break endpoint for the restore comparison.
            if step == break_point and strategy != "cold":
                result.pre_break_centroids = _centroids(scorer).tolist()
                result.reinitialize_result = scorer.reinitialize_from_regime(
                    regime_tag=REGIME_1,
                    strategy=strategy,
                )
                result.reinitialize_called = True
                if not result.reinitialize_result.get("success"):
                    raise RuntimeError(f"reinitialization failed: {result.reinitialize_result}")
                result.post_reinit_centroids = _centroids(scorer).tolist()
            elif step == break_point and strategy == "cold":
                result.pre_break_centroids = _centroids(scorer).tolist()
                # Cold start is a bootstrap reset, not a regime-memory call.
                scorer._scorer.centroids = np.asarray(
                    scorer._preset.bootstrap_centroids, dtype=np.float64
                ).copy()
                result.post_reinit_centroids = _centroids(scorer).tolist()

            category, factors = generator.generate()
            oracle = phase2_oracle if step >= break_point else phase1_oracle
            scored = scorer.score(factors, category)
            is_correct = oracle.label_correct(category, scored.action, factors)
            actual_action = (
                scored.action
                if is_correct
                else _correct_action(oracle, category, factors, action_names)
            )
            scorer.learn(
                decision_id=str(scored.decision_id),
                actual_action=actual_action,
                outcome="confirmed" if is_correct else "corrected",
                context={"benchmark": True, "preseed": True, "regime": REGIME_2 if step >= break_point else REGIME_1},
                persist_artifacts=False,
            )

            if step < break_point:
                result.decisions_phase_1 += 1
            else:
                result.decisions_phase_2 += 1
                distance = compute_gt_distance(scorer, phase2_oracle)
                result.gt_distances.append(distance)
                if result.convergence_step is None and distance <= convergence_threshold:
                    result.convergence_step = step - break_point

            # Do not write the endpoint at the break: the latest prior-regime
            # checkpoint remains a genuine earlier state, and each arm has
            # multiple checkpoints to support evidence-depth reporting.
            if (step + 1) % CHECKPOINT_INTERVAL == 0 and step + 1 < break_point:
                if _checkpoint(scorer, scored, REGIME_1, step + 1):
                    phase1_checkpoint_count += 1
            elif step >= break_point and (step + 1 - break_point) % CHECKPOINT_INTERVAL == 0:
                if _checkpoint(scorer, scored, REGIME_2, step + 1):
                    phase2_checkpoint_count += 1
    finally:
        store.close()
        if previous_outbox is None:
            os.environ.pop("CI_PERSISTENCE_OUTBOX_PATH", None)
        else:
            os.environ["CI_PERSISTENCE_OUTBOX_PATH"] = previous_outbox

    result.checkpoints_by_regime = {REGIME_1: phase1_checkpoint_count, REGIME_2: phase2_checkpoint_count}
    return result


def run_experiment(
    total_decisions: int = EXPERIMENT_GENERATOR.n_decisions,
    break_point: int | None = None,
    convergence_threshold: float = CONVERGENCE_THRESHOLD,
    output_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Run cold/A/B/C on identical inputs and return JSON-ready results."""

    gen_config, phase1_config, phase2_config, actual_break = experiment_configs(
        total_decisions=total_decisions,
        break_point=break_point,
    )
    arms: dict[str, ArmResult] = {}
    for name, strategy in (("cold_start", "cold"), ("strategy_A", "A"), ("strategy_B", "B"), ("strategy_C", "C")):
        arms[name] = run_arm(
            name,
            strategy,
            gen_config,
            phase1_config,
            phase2_config,
            actual_break,
            convergence_threshold,
            output_dir,
        )

    cold_step = arms["cold_start"].convergence_step
    for arm in arms.values():
        arm.gamma_regime = 1.0 if arm.strategy == "cold" else compute_gamma(cold_step, arm.convergence_step)

    candidates = [
        (name, arm.gamma_regime)
        for name, arm in arms.items()
        if arm.strategy != "cold" and arm.gamma_regime is not None
    ]
    winner = max(candidates, key=lambda item: item[1])[0] if candidates else None
    serialized = {
        name: {
            "name": arm.name,
            "strategy": arm.strategy,
            "gt_distances": arm.gt_distances,
            "convergence_step": arm.convergence_step,
            "gamma_regime": arm.gamma_regime,
            "reinitialize_called": arm.reinitialize_called,
            "reinitialize_result": arm.reinitialize_result,
            "pre_break_centroids": arm.pre_break_centroids,
            "post_reinit_centroids": arm.post_reinit_centroids,
            "decisions_phase_1": arm.decisions_phase_1,
            "decisions_phase_2": arm.decisions_phase_2,
            "checkpoints_by_regime": arm.checkpoints_by_regime,
        }
        for name, arm in arms.items()
    }
    winner_gamma = serialized[winner]["gamma_regime"] if winner else None
    recommendation = (
        "NEAR"
        if isinstance(winner_gamma, (int, float)) and winner_gamma > 1
        else "ARCH"
    )
    return {
        "experiment": "EXP-REGIME",
        "metric": "gamma_regime",
        "metric_definition": "cold post-break GT-distance convergence time / strategy post-break GT-distance convergence time",
        "distance_basis": "phase-2 oracle ground-truth centroids; normalized Frobenius distance",
        "epsilon_firm_is_distinct": True,
        "break_point": actual_break,
        "total_decisions": total_decisions,
        "decisions_per_regime": {REGIME_1: actual_break, REGIME_2: total_decisions - actual_break},
        "threshold": convergence_threshold,
        "arms": serialized,
        "winner": winner,
        "recommendation": recommendation,
    }
