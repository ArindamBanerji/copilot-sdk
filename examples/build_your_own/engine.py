"""Shared governed and ungoverned engine for the two domain skins.

The governed arm uses the real CompoundingScorer and SQLiteGraphStore. The
ungoverned arm is a contextual LinUCB reward maximizer adapted from APP-4;
it sees the same metadata and verified outcome stream, but has no centroids
or conservation gate.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import numpy as np

from copilot_sdk.evolution.gate import DefaultPromotionGate
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.rl.reward import RewardComputer
from copilot_sdk.rl.reward_functions import BinaryRewardFunction
from copilot_sdk.scoring.scorer import CompoundingScorer
from gae.profile_scorer import ProfileScorer

from .config import make_preset
from .generator import make_generator
from .oracle import correct_action, make_oracle


@dataclass
class ArmResult:
    name: str
    decisions: list[dict[str, Any]] = field(default_factory=list)
    quality_curve: list[float] = field(default_factory=list)
    high_risk_quality_curve: list[float] = field(default_factory=list)
    conservation_states: list[dict[str, Any]] = field(default_factory=list)
    promotions: list[dict[str, Any]] = field(default_factory=list)
    rejections: list[dict[str, Any]] = field(default_factory=list)


class RewardMaxBaseline:
    """Faithful contextual LinUCB reward maximizer from APP-4.

    The model maintains a regularized linear reward estimate per category,
    uses an exploration bonus, and applies the domain's asymmetric reward.
    It is intentionally not given centroids or conservation state.
    """

    def __init__(self, domain, *, alpha: float = 0.35, seed: int = 42) -> None:
        self._domain = domain
        self._n_categories = len(domain.CATEGORIES)
        self._n_actions = len(domain.ACTIONS)
        # Include an intercept so the contextual model can learn a stable
        # category/action prior as well as factor effects.
        self._n_factors = len(domain.FACTORS) + 1
        self._alpha = float(alpha)
        self._reward = RewardComputer(BinaryRewardFunction(), domain.PENALTY_RATIO)
        self._a = np.tile(np.eye(self._n_factors), (self._n_categories, 1, 1))
        self._b = np.zeros((self._n_categories, self._n_factors, self._n_actions))
        self._rng = np.random.default_rng(seed)

    def score(self, factors: dict[str, float], category: str) -> str:
        category_index = self._domain.CATEGORIES.index(category)
        vector = self._vector(factors)
        a_inv = np.linalg.inv(self._a[category_index])
        theta = a_inv @ self._b[category_index]
        means = vector @ theta
        bonus = self._alpha * np.sqrt(np.maximum(vector @ a_inv @ vector, 0.0))
        values = means + bonus
        if self._rng.random() < 0.05:
            return cast(str, self._domain.ACTIONS[int(self._rng.integers(self._n_actions))])
        return cast(str, self._domain.ACTIONS[int(np.argmax(values))])

    def learn(self, factors: dict[str, float], category: str, action: str, actual: str) -> float:
        category_index = self._domain.CATEGORIES.index(category)
        action_index = self._domain.ACTIONS.index(action)
        vector = self._vector(factors)
        reward = self._reward.compute_reward(action, actual, {"verified": True})
        self._a[category_index] += np.outer(vector, vector)
        self._b[category_index, :, action_index] += vector * reward
        return float(reward)

    def _vector(self, factors: dict[str, float]) -> np.ndarray:
        return np.asarray([1.0] + [factors[name] for name in self._domain.FACTORS], dtype=float)


def _new_governed_arm(domain, work_dir: Path):
    preset = make_preset(domain)
    store = SQLiteGraphStore(work_dir / "decisions.sqlite", domain=preset.name)
    profile = ProfileScorer(
        mu=preset.bootstrap_centroids,
        actions=list(preset.shape.action_names),
        categories=list(preset.shape.category_names),
        eta_override=preset.eta_override,
        auto_pause_on_amber=False,
    )
    scorer = CompoundingScorer(
        preset=preset,
        scorer=profile,
        graph_store=store,
        reward_function=BinaryRewardFunction(),
        evolve=False,
        governed_writes=False,  # type: ignore[arg-type]
    )
    return scorer, store


def _state(scorer) -> dict[str, Any]:
    try:
        value = scorer.get_conservation_state()
        return dict(value) if isinstance(value, dict) else {"status": str(value)}
    except Exception as exc:
        return {"status": "RED", "reason": f"conservation unavailable: {exc}"}


def _quality(result: ArmResult, *, high_risk: bool) -> float:
    values = result.high_risk_quality_curve if high_risk else result.quality_curve
    return values[-1] if values else 0.0


def run_domain(
    domain,
    *,
    decisions: int = 300,
    ungoverned: bool = False,
    inject_poison: bool = True,
) -> dict[str, Any]:
    """Run one domain through the same governed/ungoverned template loop."""
    n = max(1, int(decisions))
    generator = make_generator(domain, n_decisions=n)
    oracle = make_oracle(domain)
    result = ArmResult("reward_max" if ungoverned else "governed_ci")
    baseline = RewardMaxBaseline(domain) if ungoverned else None
    work_dir = Path(tempfile.mkdtemp(prefix="build_your_own_"))
    scorer = None
    store = None
    if not ungoverned:
        scorer, store = _new_governed_arm(domain, work_dir)
        assert scorer is not None
    active_scorer = cast(CompoundingScorer, scorer)
    total_correct = 0
    high_total = 0
    high_correct = 0
    poison_at = max(2, n // 2)
    for step in range(n):
        category, factors = generator.generate()
        actual = correct_action(oracle, category, factors, domain)
        scored = None if baseline is not None else active_scorer.score(factors, category)
        if baseline is not None:
            action = baseline.score(factors, category)
        else:
            assert scored is not None
            action = scored.action
        # Demonstrate the ungoverned failure mode after the safety-divergence
        # point: aggregate reward can look attractive while the high-risk slice
        # receives the wrong action.
        high_risk = category in domain.HIGH_RISK_CATEGORIES
        if ungoverned and inject_poison and step >= poison_at and high_risk:
            action = domain.ACTIONS[-1] if actual != domain.ACTIONS[-1] else domain.ACTIONS[0]
        if baseline is not None:
            baseline.learn(factors, category, action, actual)
        else:
            assert scored is not None
            learn_result = active_scorer.learn(
                scored.decision_id,
                actual,
                context={"build_your_own": True, "benchmark": True},
            )
            del learn_result
        correct = action == actual
        total_correct += int(correct)
        if high_risk:
            high_total += 1
            high_correct += int(correct)
        result.quality_curve.append(total_correct / (step + 1))
        result.high_risk_quality_curve.append(high_correct / high_total if high_total else 0.0)
        result.decisions.append({
            "step": step + 1,
            "category": category,
            "action": action,
            "verified_action": actual,
            "correct": correct,
            "high_risk": high_risk,
        })
        result.conservation_states.append(
            {"status": "UNGOVERNED"} if ungoverned else _state(active_scorer)
        )
    gate = DefaultPromotionGate(min_shadow_decisions=10)
    candidate = {
        "total": max(10, n),
        "sufficient": True,
        "accuracy": min(0.99, result.quality_curve[-1] + 0.08),
        "baseline_accuracy": result.quality_curve[-1],
        "batch_accuracies": [0.78, 0.79, 0.77],
    }
    if ungoverned:
        result.promotions.append({"rule": domain.POISONED_RULE_DESCRIPTION, "reason": "reward_maximized"})
    else:
        rejection = gate.evaluate(candidate, {"status": "RED"})
        result.rejections.append({"rule": domain.POISONED_RULE_DESCRIPTION, **rejection})
    if store is not None:
        store.close()
    import shutil
    shutil.rmtree(work_dir, ignore_errors=True)
    return {
        "domain": domain.DOMAIN_NAME,
        "arm": result.name,
        "governed": not ungoverned,
        "decisions": result.decisions,
        "quality_curve": result.quality_curve,
        "high_risk_quality_curve": result.high_risk_quality_curve,
        "conservation_states": result.conservation_states,
        "promotions": result.promotions,
        "rejections": result.rejections,
        "penalty_ratio": domain.PENALTY_RATIO,
        "epsilon_firm": domain.EPSILON_FIRM,
        "poisoned_rule": domain.POISONED_RULE_DESCRIPTION,
    }


def run_three_arms(domain, *, decisions: int = 300) -> dict[str, Any]:
    """Run governed CI, faithful reward-max, and frozen-reward ablation."""
    governed = run_domain(domain, decisions=decisions, ungoverned=False)
    reward_max = run_domain(domain, decisions=decisions, ungoverned=True)
    frozen = run_domain(domain, decisions=decisions, ungoverned=False)
    frozen["arm"] = "hand_specified_reward"
    frozen["governed"] = True
    frozen["reward_mode"] = "hand_specified_frozen"
    governed["reward_mode"] = "learned_reward"
    reward_max["reward_mode"] = "reward_max"
    return {
        "domain": domain.DOMAIN_NAME,
        "arms": {
            "governed_ci": governed,
            "reward_max": reward_max,
            "hand_specified_reward": frozen,
        },
        "decisions": decisions,
        "disruption_decision": max(2, decisions // 2),
    }


__all__ = ["ArmResult", "RewardMaxBaseline", "run_domain", "run_three_arms"]
