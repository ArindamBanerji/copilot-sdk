"""GAE-backed CompoundingScorer facade."""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np

from copilot_sdk.scoring.config import DomainPreset
from copilot_sdk.scoring.fingerprint import FingerprintResult, compute_fingerprint
from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.scoring.storage import DecisionStore
from copilot_sdk.scoring.trajectory import TrajectoryResult, compute_trajectory
from copilot_sdk.graph.protocol import GraphStore


def _ensure_gae_path() -> None:
    workspace = Path(__file__).resolve().parents[3]
    gae_path = workspace / "graph-attention-engine-v50"
    if gae_path.exists() and str(gae_path) not in sys.path:
        sys.path.insert(0, str(gae_path))


_ensure_gae_path()

from gae.profile_scorer import ProfileScorer  # noqa: E402

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScoreResult:
    decision_id: str
    action: str
    action_index: int
    confidence: float
    probabilities: list[float]
    category: str
    factors: dict[str, float]


@dataclass(frozen=True)
class LearnResult:
    decision_id: str
    iks_before: float
    iks_after: float
    centroid_delta: float
    decisions_total: int
    outcome: str
    reward: float | None = None
    reward_raw: float | None = None
    exploration_used: bool = False


class CompoundingScorer:
    """User-facing wrapper around GAE ProfileScorer."""

    def __init__(
        self,
        preset: DomainPreset,
        store: DecisionStore,
        scorer: ProfileScorer,
        graph_store: GraphStore | None = None,
        reward_function: Any | None = None,
        credit_assigner: Any | None = None,
        exploration_policy: Any | None = None,
        evolve: bool = False,
    ):
        self._preset = preset
        self._store = store
        self._scorer = scorer
        if graph_store is None:
            from copilot_sdk.graph.sqlite_store import SQLiteGraphStore

            graph_store = SQLiteGraphStore(store.db_path, domain=preset.name)
        self._graph_store = graph_store
        self._reward_fn = reward_function
        self._credit = credit_assigner
        self._explorer = exploration_policy
        self._evolve = bool(evolve)
        self._evolver = None
        self._evolve_count = 0
        if self._evolve:
            self._setup_evolution()

    @classmethod
    def from_preset(
        cls,
        domain: str,
        db_path: Optional[str] = None,
        graph_store: GraphStore | None = None,
        reward_function: Any | None = None,
        credit_assigner: Any | None = None,
        exploration_policy: Any | None = None,
        evolve: bool = False,
    ) -> "CompoundingScorer":
        if domain not in PRESET_REGISTRY:
            available = ", ".join(sorted(PRESET_REGISTRY)) or "(none)"
            raise ValueError(f"Unknown preset {domain!r}. Available presets: {available}")

        preset_cls = PRESET_REGISTRY[domain]
        preset = preset_cls()
        if db_path is None:
            data_dir = Path(__file__).resolve().parents[1] / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / f"{domain}.db")

        store = DecisionStore(db_path)
        centroids = store.load_latest_centroids()
        if centroids is None:
            centroids = np.array(preset.bootstrap_centroids, dtype=np.float64, copy=True)
        if graph_store is None:
            from copilot_sdk.graph.sqlite_store import SQLiteGraphStore

            graph_store = SQLiteGraphStore(db_path, domain=preset.name)

        scorer = ProfileScorer(
            mu=centroids,
            actions=list(preset.shape.action_names),
            categories=list(preset.shape.category_names),
        )
        return cls(
            preset=preset,
            store=store,
            scorer=scorer,
            graph_store=graph_store,
            reward_function=reward_function,
            credit_assigner=credit_assigner,
            exploration_policy=exploration_policy,
            evolve=evolve,
        )

    def score(
        self,
        factors: dict[str, float],
        category: str,
        metadata: dict[str, Any] | None = None,
    ) -> ScoreResult:
        assert category in self._preset.shape.category_names, f"unknown category: {category}"
        unknown = set(factors) - set(self._preset.shape.factor_names)
        assert not unknown, f"unknown factors: {sorted(unknown)}"

        category_index = self._preset.shape.category_names.index(category)
        factor_values = {
            name: float(factors.get(name, 0.5))
            for name in self._preset.shape.factor_names
        }
        factor_vector = np.asarray(
            [factor_values[name] for name in self._preset.shape.factor_names],
            dtype=np.float64,
        )

        gae_result = self._scorer.score(factor_vector, category_index)
        action_index = int(gae_result.action_index)
        action = str(gae_result.action_name)
        if action != self._preset.shape.action_names[action_index]:
            action = self._preset.shape.action_names[action_index]

        probabilities = [float(value) for value in gae_result.probabilities]
        decision_id = uuid.uuid4().hex[:12]
        decision_metadata = dict(metadata or {})
        decision_metadata.update({
            "decision_id": decision_id,
            "domain": self._preset.name,
            "category_index": category_index,
            "factor_vector": factor_vector.tolist(),
            "recommended_index": action_index,
            "probabilities": probabilities,
            "created_at": time.time(),
        })
        stored_id = self._graph_store.write_decision(
            entity_id=decision_id,
            category=category,
            action=action,
            confidence=float(gae_result.confidence),
            factors=factor_values,
            metadata=decision_metadata,
        )
        decision_id = stored_id

        return ScoreResult(
            decision_id=decision_id,
            action=action,
            action_index=action_index,
            confidence=float(gae_result.confidence),
            probabilities=probabilities,
            category=category,
            factors=factor_values,
        )

    def learn(
        self,
        decision_id: str,
        actual_action: str,
        outcome: str = "confirmed",
    ) -> LearnResult | dict[str, Any]:
        decision = self._graph_store.get_decision(decision_id)
        if decision is None:
            raise KeyError(decision_id)
        assert actual_action in self._preset.shape.action_names, f"unknown action: {actual_action}"

        actual_index = self._preset.shape.action_names.index(actual_action)
        predicted_index = int(_decision_field(decision, "recommended_index", 0))
        recommended_action = str(_decision_field(decision, "recommended_action", _decision_field(decision, "action", "")))
        is_correct = actual_action == recommended_action
        factor_vector = np.asarray(_decision_field(decision, "factor_vector", []), dtype=np.float64)
        category_index = int(_decision_field(decision, "category_index", 0))
        confidence = float(_decision_field(decision, "confidence", 0.0))

        conservation_pause = self._conservation_pause()
        if conservation_pause is not None:
            return conservation_pause
        iks_before = self._compute_iks()
        before_centroids = self._scorer.centroids.copy()

        old_eta = self._scorer.eta
        old_eta_override = self._scorer.eta_override
        try:
            self._scorer.eta = float(self._preset.eta_confirm)
            self._scorer.eta_override = (
                None
                if is_correct
                else float(self._preset.eta_override) * float(self._preset.penalty_ratio)
            )
            update_result = self._scorer.update(
                f=factor_vector,
                category_index=category_index,
                action_index=predicted_index,
                correct=is_correct,
                gt_action_index=None if is_correct else actual_index,
                confidence=confidence,
            )
        finally:
            self._scorer.eta = old_eta
            self._scorer.eta_override = old_eta_override

        centroid_delta = float(np.linalg.norm(self._scorer.centroids - before_centroids))
        self._graph_store.write_outcome(
            decision_id=decision_id,
            actual_action=actual_action,
            is_correct=is_correct,
            metadata={
                "actual_index": actual_index,
                "verified_at": time.time(),
                "outcome": outcome,
            },
        )
        iks_after = self._compute_iks()
        self._graph_store.save_centroids(
            decision_id,
            str(_decision_field(decision, "category", "")),
            self._scorer.centroids,
            metadata={"iks": iks_after},
        )
        reward_raw, reward = self._compute_rl_reward(decision, actual_action, outcome)
        if reward_raw is not None:
            if self._explorer is not None:
                self._explorer.update(predicted_index, reward_raw)
            if self._credit is not None:
                # DK weight integration is future work; compute credits without mutating scorer weights.
                factors = decision.get("factors") or {}
                factor_names = [
                    name for name in self._preset.shape.factor_names
                    if name in factors
                ]
                self._credit.assign(reward_raw, factor_names)

        if self._evolve and self._evolver is not None:
            self._evolve_count += 1
            if self._evolve_count % 20 == 0:
                self._run_evolution()

        return LearnResult(
            decision_id=decision_id,
            iks_before=iks_before,
            iks_after=iks_after,
            centroid_delta=centroid_delta,
            decisions_total=int(update_result.decision_count),
            outcome=str(update_result.outcome),
            reward=reward,
            reward_raw=reward_raw,
            exploration_used=False,
        )

    def fingerprint(self) -> FingerprintResult:
        return compute_fingerprint(
            self._graph_store.get_verified_decisions(),
            list(self._preset.shape.factor_names),
        )

    def trajectory(self) -> TrajectoryResult:
        return compute_trajectory(
            self._graph_store.get_centroid_checkpoints(),
            self._graph_store.get_verified_decisions(),
            self._preset.shape,
        )

    def get_phase(self) -> str:
        """Return the current SDK phase from GraphStore verification counts."""
        try:
            verified = int(self._graph_store.count_verified())
            if verified < 10:
                return "A"
            correct = int(self._graph_store.count_correct())
            q = correct / verified
            return "B" if q >= 0.5 else "A"
        except Exception:
            return "A"

    def get_alpha(self) -> float:
        """Return current verified accuracy from GraphStore counts."""
        try:
            verified = int(self._graph_store.count_verified())
            if verified == 0:
                return 0.0
            correct = int(self._graph_store.count_correct())
            return round(correct / verified, 4)
        except Exception:
            return 0.0

    def warm_start(
        self,
        patterns: Any,
        category_mapping: dict[str, str] | None = None,
        blend_weight: float = 0.25,
    ) -> dict[str, Any]:
        """Apply shared transfer patterns to the active GAE centroid tensor."""
        from copilot_sdk.transfer.registry import SharedPatternRegistry
        from copilot_sdk.transfer.warm_start import (
            applied_patterns,
            warm_start_centroids,
        )

        target_copilot = str(getattr(self._preset, "name", "") or "unknown")
        if isinstance(patterns, SharedPatternRegistry):
            transfer_patterns = patterns.get_patterns_for_warm_start(
                target_copilot,
                category_mapping=category_mapping,
            )
        else:
            transfer_patterns = list(patterns or [])

        current_centroids = np.array(self._scorer.centroids, dtype=np.float64, copy=True)
        applied_transfer_patterns = applied_patterns(
            current_centroids,
            transfer_patterns,
            self._preset.shape.category_names,
            self._preset.shape.action_names,
        )
        applied = len(applied_transfer_patterns)
        updated_centroids, score = warm_start_centroids(
            current_centroids,
            transfer_patterns,
            self._preset.shape.category_names,
            self._preset.shape.action_names,
            blend_weight=blend_weight,
        )
        if applied:
            self._scorer.centroids = updated_centroids
            source_copilots = sorted(
                {
                    str(getattr(pattern, "source_copilot", ""))
                    for pattern in applied_transfer_patterns
                    if str(getattr(pattern, "source_copilot", ""))
                }
            )
            save_centroids = getattr(self._graph_store, "save_centroids", None)
            if callable(save_centroids):
                try:
                    save_centroids(
                        f"warm-start-{uuid.uuid4().hex[:12]}",
                        "warm_start",
                        self._scorer.centroids,
                        metadata={
                            "source": "warm_start",
                            "score": score,
                            "applied": applied,
                            "source_copilots": source_copilots,
                        },
                    )
                except Exception as exc:
                    logger.warning("Failed to save warm-start centroid checkpoint: %s", exc)
        else:
            source_copilots = []

        return {
            "applied": applied,
            "score": score,
            "source_copilots": source_copilots,
        }

    def export(self, path: str | Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "domain": self._preset.name,
            "centroids": self._scorer.centroids.tolist(),
            "decisions": self._graph_store.get_all_decisions(),
            "shape": {
                "n_categories": self._preset.shape.n_categories,
                "n_actions": self._preset.shape.n_actions,
                "n_factors": self._preset.shape.n_factors,
                "categories": list(self._preset.shape.category_names),
                "actions": list(self._preset.shape.action_names),
                "factors": list(self._preset.shape.factor_names),
            },
        }
        destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path, db_path: Optional[str] = None) -> "CompoundingScorer":
        state = json.loads(Path(path).read_text(encoding="utf-8"))
        scorer = cls.from_preset(state["domain"], db_path=db_path)
        scorer._scorer.centroids = np.asarray(state["centroids"], dtype=np.float64)
        return scorer

    def _compute_iks(self) -> float:
        verified = self._graph_store.count_verified()
        if verified == 0:
            return 0.0

        correct = self._graph_store.count_correct()
        accuracy = correct / verified
        fingerprint = self.fingerprint()
        mean_sigma = (
            sum(factor.sigma for factor in fingerprint.factors) / len(fingerprint.factors)
            if fingerprint.factors
            else 0.5
        )
        fingerprint_component = max(0.0, min((1.0 - mean_sigma / 0.5) * 25.0, 25.0))
        coverage = _count_categories_with_n(
            self._graph_store.get_verified_decisions(),
            10,
        ) / self._preset.shape.n_categories

        iks = (
            min(verified / 500.0, 1.0) * 25.0
            + accuracy * 25.0
            + fingerprint_component
            + coverage * 25.0
        )
        return round(iks, 1)

    def _conservation_pause(self) -> dict[str, Any] | None:
        try:
            verified, correct = _conservation_counts(self._graph_store)
        except Exception:
            return None
        if verified <= 0:
            return None

        q = correct / verified
        penalty_ratio = _positive_penalty_ratio(getattr(self._preset, "penalty_ratio", None))
        theta_min = 23.53 / (penalty_ratio * verified)
        if q < theta_min:
            return {
                "status": "paused",
                "reason": "conservation_red",
                "q": q,
                "theta_min": theta_min,
                "verified_count": verified,
                "correct_count": correct,
            }
        return None

    def _compute_rl_reward(
        self,
        decision: dict[str, Any],
        actual_action: str,
        outcome: str,
    ) -> tuple[float | None, float | None]:
        if self._reward_fn is None:
            return None, None

        outcome_dict = {"outcome": outcome}
        recommended_action = str(_decision_field(decision, "recommended_action", _decision_field(decision, "action", "")))
        reward_raw = float(self._reward_fn.compute(
            recommended_action,
            actual_action,
            outcome_dict,
        ))
        reward = _scale_raw_reward(
            reward_raw,
            _positive_penalty_ratio(getattr(self._preset, "penalty_ratio", None)),
        )
        return reward_raw, reward

    def _setup_evolution(self) -> None:
        actions = list(getattr(self._preset.shape, "action_names", ()) or ())
        if len(actions) < 2:
            logger.warning("Evolution disabled: preset %s has fewer than 2 actions", self._preset.name)
            self._evolve = False
            self._evolver = None
            return

        factor_count = int(getattr(self._preset.shape, "n_factors", 0) or len(getattr(self._preset.shape, "factor_names", ())))
        try:
            from copilot_sdk.evolution import (
                AgentEvolver,
                DefaultPromotionGate,
                DefaultShadowRunner,
                InMemoryEvolutionLedger,
            )
            from copilot_sdk.evolution.toy_rules import ActionBiasRule, FactorWeightRule, ThresholdRule
        except Exception as exc:
            logger.warning("Evolution disabled: failed to import evolution components: %s", exc)
            self._evolve = False
            self._evolver = None
            return

        ledger = InMemoryEvolutionLedger(graph_store=self._graph_store)
        evolver = AgentEvolver(
            ledger=ledger,
            shadow_runner=DefaultShadowRunner(),
            promotion_gate=DefaultPromotionGate(),
        )
        evolver.register_rule(ThresholdRule(actions))
        evolver.register_rule(FactorWeightRule(actions, factor_count=factor_count))
        evolver.register_rule(ActionBiasRule(actions))
        self._evolver = evolver

    def _run_evolution(self) -> None:
        if self._evolver is None:
            return
        try:
            decisions = list(self._graph_store.get_verified_decisions() or [])
            if len(decisions) < 10:
                return
            conservation_state = self._evolution_conservation_state()
            active_rules = self._evolver.get_active_rules()
            for rule_name in list(active_rules):
                self._evolver.evolve(
                    rule_name,
                    decisions,
                    conservation_state=conservation_state,
                )
        except Exception as exc:
            logger.warning("Evolution run failed: %s", exc)

    def _evolution_conservation_state(self) -> dict[str, Any] | None:
        try:
            verified = int(self._graph_store.count_verified())
            correct = int(self._graph_store.count_correct())
        except Exception:
            return None
        if verified <= 0:
            return {
                "status": "GREEN",
                "verified_count": 0,
                "correct_count": 0,
                "q": 0.0,
                "theta_min": None,
            }
        q = correct / verified
        penalty_ratio = _positive_penalty_ratio(getattr(self._preset, "penalty_ratio", None))
        theta_min = 23.53 / (penalty_ratio * verified)
        return {
            "status": "GREEN" if q >= theta_min else "RED",
            "verified_count": verified,
            "correct_count": correct,
            "q": q,
            "theta_min": theta_min,
        }

    @property
    def graph_store(self) -> GraphStore:
        """The GraphStore single source of truth."""
        return self._graph_store

    @property
    def store(self) -> DecisionStore:
        return self._store

    @property
    def gae_scorer(self) -> ProfileScorer:
        return self._scorer


def _conservation_counts(store: Any) -> tuple[int, int]:
    count_verified = getattr(store, "count_verified", None)
    count_correct = getattr(store, "count_correct", None)
    if callable(count_verified) and callable(count_correct):
        return max(int(count_verified()), 0), max(int(count_correct()), 0)

    get_all_decisions = getattr(store, "get_all_decisions", None)
    if not callable(get_all_decisions):
        return 0, 0
    decisions = get_all_decisions()
    verified = sum(1 for decision in decisions if _is_verified_decision(decision))
    correct = sum(1 for decision in decisions if _is_correct_decision(decision))
    return verified, correct


def _decision_field(decision: dict[str, Any], key: str, default: Any = None) -> Any:
    if key in decision:
        return decision[key]
    metadata = decision.get("metadata")
    if isinstance(metadata, dict) and key in metadata:
        return metadata[key]
    factors = decision.get("factors")
    if isinstance(factors, dict):
        nested_metadata = factors.get("metadata")
        if isinstance(nested_metadata, dict) and key in nested_metadata:
            return nested_metadata[key]
    return default


def _count_categories_with_n(decisions: list[dict[str, Any]], n: int) -> int:
    counts: dict[str, int] = {}
    for decision in decisions:
        category = str(decision.get("category") or "")
        if not category:
            continue
        counts[category] = counts.get(category, 0) + 1
    return sum(1 for count in counts.values() if count >= n)


def _is_verified_decision(decision: dict[str, Any]) -> bool:
    outcome = decision.get("outcome")
    if outcome is not None:
        return str(outcome).strip().lower() in {"confirmed", "overridden"}
    return decision.get("is_correct") is not None


def _is_correct_decision(decision: dict[str, Any]) -> bool:
    outcome = str(decision.get("outcome") or "").strip().lower()
    return outcome == "confirmed" or bool(decision.get("is_correct"))


def _positive_penalty_ratio(value: Any) -> float:
    try:
        penalty_ratio = float(value)
    except (TypeError, ValueError):
        return 10.0
    if not np.isfinite(penalty_ratio) or penalty_ratio <= 0:
        return 10.0
    return penalty_ratio


def _scale_raw_reward(raw: float, penalty_ratio: float) -> float:
    clipped = max(-1.0, min(float(raw), 1.0))
    return clipped * penalty_ratio if clipped < 0 else clipped
