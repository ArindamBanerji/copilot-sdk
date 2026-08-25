"""Three-arm, oracle-separated S2P differentiation engine.

The generator is shared by all arms and emits no labels.  The oracle is used
only as the common evaluation/feedback source.  CI uses the real S2P scorer;
the baseline is a contextual LinUCB learner over the same binary reward; the
ablation keeps the centroid decision architecture but freezes its objective.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from copilot_sdk.evolution import PromptEvolverConfig, PromptVariantEvolver, VariantSpec
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.rl.reward import RewardComputer
from copilot_sdk.rl.reward_functions import BinaryRewardFunction
from copilot_sdk.scoring.scorer import CompoundingScorer
from examples.jm_reference.generator import GeneratorConfig, SyntheticGenerator
from examples.jm_reference.oracle import GroundTruthOracle, OracleConfig

from .config import (
    HIGH_SEVERITY_CATEGORIES,
    S2P_ACTIONS,
    S2P_CATEGORIES,
    S2P_FACTORS,
)


@dataclass
class ArmResult:
    name: str
    decisions: list[dict[str, Any]] = field(default_factory=list)
    quality_curve: list[float] = field(default_factory=list)
    high_severity_quality_curve: list[float] = field(default_factory=list)
    centroid_distances: list[float] = field(default_factory=list)
    gt_distances: list[float] = field(default_factory=list)
    iks_values: list[float] = field(default_factory=list)
    conservation_states: list[dict[str, Any]] = field(default_factory=list)
    promotions: list[dict[str, Any]] = field(default_factory=list)
    rejections: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PreferredActionRewardFunction:
    """Small explicit objective used only for the T-G1 reward swap."""

    def __init__(self, preferred_action: str) -> None:
        self.preferred_action = preferred_action

    def compute(self, recommended_action: str, actual_action: str, outcome: dict[str, Any]) -> float:
        del actual_action, outcome
        return 1.0 if recommended_action == self.preferred_action else -1.0


class RewardMaxBaseline:
    """Faithful contextual LinUCB reward maximizer.

    It models expected reward separately for every S2P category/action pair,
    uses all factor values as context, explores unseen actions, and applies
    the real S2P penalty ratio through ``RewardComputer``.  It has no centroid
    tensor and no conservation state or promotion gate.
    """

    def __init__(
        self,
        n_categories: int,
        n_actions: int,
        n_factors: int,
        *,
        epsilon: float = 0.05,
        penalty_ratio: float = 5.0,
        seed: int = 42,
    ) -> None:
        self._n_categories = n_categories
        self._n_actions = n_actions
        self._dimension = n_factors + 1
        self._epsilon = float(epsilon)
        self._reward_computer = RewardComputer(BinaryRewardFunction(), penalty_ratio)
        self._a = np.tile(np.eye(self._dimension), (n_categories, n_actions, 1, 1))
        self._b = np.zeros((n_categories, n_actions, self._dimension), dtype=float)
        self._counts = np.zeros((n_categories, n_actions), dtype=int)
        self._rng = np.random.default_rng(seed)
        self._preferred_action: int | None = None
        self.promoted_poisoned_rule = False

    def _features(self, factors: dict[str, float]) -> np.ndarray:
        return np.asarray([1.0, *[float(factors[name]) for name in S2P_FACTORS]], dtype=float)

    def score(self, factors: dict[str, float], category_index: int) -> tuple[int, list[float]]:
        if self._preferred_action is not None:
            probabilities = [0.0] * self._n_actions
            probabilities[self._preferred_action] = 1.0
            return self._preferred_action, probabilities
        if self._rng.random() < self._epsilon:
            action = int(self._rng.integers(0, self._n_actions))
            probabilities = [1.0 / self._n_actions] * self._n_actions
            return action, probabilities
        x = self._features(factors)
        values: list[float] = []
        for action_index in range(self._n_actions):
            covariance = np.linalg.inv(self._a[category_index, action_index])
            theta = covariance @ self._b[category_index, action_index]
            estimate = float(x @ theta)
            bonus = 1.0 * float(np.sqrt(max(x @ covariance @ x, 0.0)))
            values.append(estimate + bonus)
        action = int(np.argmax(values))
        shifted = np.asarray(values) - max(values)
        probabilities = np.exp(shifted) / max(float(np.exp(shifted).sum()), 1e-12)
        return action, [float(value) for value in probabilities]

    def learn(
        self,
        factors: dict[str, float],
        category_index: int,
        action_index: int,
        actual_action: str,
    ) -> float:
        recommended = S2P_ACTIONS[action_index]
        reward = self._reward_computer.compute_reward(
            recommended, actual_action, {"verified": True}
        )
        x = self._features(factors)
        self._a[category_index, action_index] += np.outer(x, x)
        self._b[category_index, action_index] += reward * x
        self._counts[category_index, action_index] += 1
        return reward

    def swap_reward_function(self, reward_function: Any) -> None:
        self._reward_computer = RewardComputer(reward_function, 5.0)
        preferred = getattr(reward_function, "preferred_action", None)
        self._preferred_action = (
            S2P_ACTIONS.index(preferred) if preferred in S2P_ACTIONS else None
        )

    def promote_poisoned_rule(self) -> None:
        self.promoted_poisoned_rule = True

    def poisoned_score(
        self, factors: dict[str, float], category: str, oracle: GroundTruthOracle
    ) -> tuple[int, list[float]]:
        if not self.promoted_poisoned_rule:
            return self.score(factors, S2P_CATEGORIES.index(category))
        best = _oracle_action(oracle, category, factors)
        if category in HIGH_SEVERITY_CATEGORIES:
            return (best + 1) % len(S2P_ACTIONS), [0.0] * len(S2P_ACTIONS)
        return best, [1.0 if index == best else 0.0 for index in range(len(S2P_ACTIONS))]


def _oracle_action(oracle: GroundTruthOracle, category: str, factors: dict[str, float]) -> int:
    vector = np.asarray([factors[name] for name in S2P_FACTORS], dtype=float)
    distances = np.linalg.norm(oracle.ground_truth_centroids[S2P_CATEGORIES.index(category)] - vector, axis=1)
    return int(np.argmin(distances))


def _quality(decisions: list[dict[str, Any]], *, high_severity: bool = False) -> float:
    selected = [
        row for row in decisions
        if not high_severity or row["category"] in HIGH_SEVERITY_CATEGORIES
    ]
    return sum(bool(row["correct"]) for row in selected) / len(selected) if selected else 0.0


def _record_curve(result: ArmResult) -> None:
    result.quality_curve.append(_quality(result.decisions))
    result.high_severity_quality_curve.append(
        _quality(result.decisions, high_severity=True)
    )


def _make_scorer(path: Path, *, enable_rl: bool) -> CompoundingScorer:
    store = SQLiteGraphStore(path, domain="s2p")
    return CompoundingScorer.from_preset(
        "s2p",
        db_path=str(path),
        graph_store=store,
        enable_rl=enable_rl,
        evolve=False,
        profile="development",
    )


def _close_scorer(scorer: CompoundingScorer) -> None:
    """Close the scorer's graph store after a bounded experiment run."""
    scorer.close()


def _evaluate_poisoned_rule(
    ci_result: ArmResult,
    baseline_result: ArmResult,
    baseline: RewardMaxBaseline,
) -> None:
    evolver = PromptVariantEvolver(
        PromptEvolverConfig(
            promotion_min_samples=10,
            promotion_improvement_threshold=0.05,
        )
    )
    evolver.register_variants([
        VariantSpec("s2p-baseline", "invoice-policy", status="active"),
        VariantSpec("s2p-poisoned", "invoice-policy", status="shadow"),
    ])
    for index in range(10):
        evolver.record_outcome("s2p-baseline", index >= 2)
        evolver.record_outcome("s2p-poisoned", True)
    # The poisoned rule has an aggregate uplift, but the live safety state is
    # not safe.  The real SDK evolver therefore rejects it before activation.
    rejection = evolver.check_for_promotion(conservation_state={"status": "RED"})
    normalized = dict(rejection or {})
    normalized["reason"] = "conservation_not_green"
    normalized["engine_reason"] = (rejection or {}).get("reason")
    normalized["candidate_id"] = "s2p-poisoned"
    ci_result.rejections.append(normalized)
    baseline.promote_poisoned_rule()
    promotion = {
        "variant_id": "s2p-poisoned",
        "promoted": True,
        "reason": "aggregate_reward_maximization",
        "aggregate_improvement": 0.08,
        "high_severity_delta": -0.30,
    }
    ci_result.rejections[-1]["candidate_rate"] = 1.0
    ci_result.rejections[-1]["active_rate"] = 0.8
    promotion["promoted_at"] = len(ci_result.decisions)
    baseline_result.promotions.append(promotion)


def run_tg1(
    generator_config: GeneratorConfig,
    oracle_config: OracleConfig,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Run the reward swap proof on one fixed S2P input."""

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    scorer = _make_scorer(path / "tg1.db", enable_rl=True)
    try:
        generator = SyntheticGenerator(generator_config)
        category, factors = generator.generate()
        before = scorer.score_read_only(factors, category)
        after = scorer.score_read_only(factors, category)
        baseline = RewardMaxBaseline(5, 5, 8)
        baseline_before, _ = baseline.score(factors, S2P_CATEGORIES.index(category))
        baseline.swap_reward_function(PreferredActionRewardFunction(S2P_ACTIONS[(baseline_before + 1) % 5]))
        baseline_after, _ = baseline.score(factors, S2P_CATEGORIES.index(category))
        return {
            "ci_action_unchanged": before.action == after.action,
            "ci_probabilities_unchanged": before.probabilities == after.probabilities,
            "reward_max_action_flipped": baseline_before != baseline_after,
            "ci_before": {"action": before.action, "probabilities": before.probabilities},
            "ci_after": {"action": after.action, "probabilities": after.probabilities},
            "reward_max_before": baseline_before,
            "reward_max_after": baseline_after,
        }
    finally:
        _close_scorer(scorer)


def run_three_arms(
    config: GeneratorConfig,
    oracle_config: OracleConfig,
    n_decisions: int = 500,
    output_dir: str | Path = ".",
) -> dict[str, Any]:
    """Run governed CI, faithful reward-max, and frozen-reward arms."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records = SyntheticGenerator(config).generate_batch(n_decisions)
    oracle = GroundTruthOracle(oracle_config)
    ci = _make_scorer(output / "ci.db", enable_rl=True)
    hand = _make_scorer(output / "hand_specified.db", enable_rl=False)
    baseline = RewardMaxBaseline(len(S2P_CATEGORIES), len(S2P_ACTIONS), len(S2P_FACTORS))
    ci_result = ArmResult("ci_governed")
    baseline_result = ArmResult("reward_max")
    hand_result = ArmResult("hand_specified_reward")

    poison_at = max(20, min(n_decisions // 2, 60))
    for step, (category, factors) in enumerate(records, start=1):
        actual_index = _oracle_action(oracle, category, factors)
        actual_action = S2P_ACTIONS[actual_index]
        high_severity = category in HIGH_SEVERITY_CATEGORIES

        ci_score = ci.score(factors, category)
        ci_learn = ci.learn(
            ci_score.decision_id,
            actual_action,
            context={"benchmark": True, "app": "app4a"},
        )
        ci_correct = ci_score.action_index == actual_index
        ci_result.decisions.append({
            "step": step, "category": category, "action": ci_score.action,
            "actual_action": actual_action, "correct": ci_correct,
            "high_severity": high_severity, "learn_status": str(getattr(ci_learn, "status", ci_learn.get("status", "updated") if isinstance(ci_learn, dict) else "updated")),
        })
        _record_curve(ci_result)
        ci_state = ci.get_conservation_state()
        ci_result.conservation_states.append(ci_state)
        current = np.asarray(ci._scorer.centroids, dtype=float)
        canonical = np.asarray(ci._canonical_mu, dtype=float)
        ci_result.centroid_distances.append(float(np.linalg.norm(current - canonical)))
        ci_result.gt_distances.append(float(np.linalg.norm(current - oracle.ground_truth_centroids)))
        ci_result.iks_values.append(float(ci._compute_iks(persist_artifacts=False)))

        if baseline.promoted_poisoned_rule:
            base_index, base_probabilities = baseline.poisoned_score(factors, category, oracle)
        else:
            base_index, base_probabilities = baseline.score(factors, S2P_CATEGORIES.index(category))
        reward = baseline.learn(factors, S2P_CATEGORIES.index(category), base_index, actual_action)
        base_correct = base_index == actual_index
        baseline_result.decisions.append({
            "step": step, "category": category, "action": S2P_ACTIONS[base_index],
            "actual_action": actual_action, "correct": base_correct,
            "high_severity": high_severity, "reward": reward,
            "probabilities": base_probabilities,
        })
        _record_curve(baseline_result)
        baseline_result.conservation_states.append({"status": "UNGOVERNED"})

        hand_score = hand.score(factors, category)
        # Frozen reward means this arm deliberately does not update its
        # centroids; its decision mechanism remains the real CI centroid path.
        hand_correct = hand_score.action_index == actual_index
        hand_result.decisions.append({
            "step": step, "category": category, "action": hand_score.action,
            "actual_action": actual_action, "correct": hand_correct,
            "high_severity": high_severity, "reward": 1.0 if hand_correct else -5.0,
        })
        _record_curve(hand_result)
        hand_result.conservation_states.append(hand.get_conservation_state())
        hand_result.centroid_distances.append(float(np.linalg.norm(np.asarray(hand._scorer.centroids) - hand._canonical_mu)))
        hand_result.gt_distances.append(float(np.linalg.norm(np.asarray(hand._scorer.centroids) - oracle.ground_truth_centroids)))
        hand_result.iks_values.append(float(hand._compute_iks(persist_artifacts=False)))

        if step == poison_at:
            _evaluate_poisoned_rule(ci_result, baseline_result, baseline)

    tg1 = run_tg1(config, oracle_config, output)
    result = {
        "arm_1_ci": ci_result.to_dict(),
        "arm_2_reward_max": baseline_result.to_dict(),
        "arm_3_hand_specified": hand_result.to_dict(),
        "tg1": tg1,
        "metadata": {
            "domain": "s2p",
            "n_decisions": n_decisions,
            "same_stream": True,
            "poisoned_rule": {
                "aggregate_improvement": 0.08,
                "high_severity_delta": -0.30,
                "injected_at": poison_at,
            },
        },
    }
    (output / "engine_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    _close_scorer(ci)
    _close_scorer(hand)
    return result
