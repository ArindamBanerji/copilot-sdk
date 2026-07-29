"""GAE-backed CompoundingScorer facade."""

from __future__ import annotations

import importlib
import hashlib
import json
import logging
import math
import os
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, cast

import numpy as np

from copilot_sdk.scoring.config import DomainPreset
from copilot_sdk.scoring.conflict import JudgmentConflict, detect_conflict
from copilot_sdk.evidence.provenance import Provenanced
from copilot_sdk.scoring.fingerprint import FingerprintResult, compute_fingerprint
from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.scoring.trajectory import TrajectoryResult, compute_trajectory
from copilot_sdk.evolution.protocol import EvolutionStore
from copilot_sdk.graph.protocol import GraphStore, ProtocolV2GraphStore
from copilot_sdk.scoring.persistence_outbox import PersistenceOutbox


def _ensure_gae_path() -> None:
    workspace = Path(__file__).resolve().parents[3]
    gae_path = workspace / "graph-attention-engine-v50"
    if gae_path.exists() and str(gae_path) not in sys.path:
        sys.path.insert(0, str(gae_path))


_ensure_gae_path()

from gae.dk_estimator import CoordinateDescentEstimator  # noqa: E402
from gae.profile_scorer import (  # noqa: E402
    DecisionCountPolicy,
    FixedAlpha,
    LearningStrategy,
    ProfileScorer,
)

logger = logging.getLogger(__name__)


def _resolve_governed_writes(governed_writes: bool | None) -> bool:
    """Resolve the construction-time governed-write feature gate.

    ``None`` means use the process default; an explicit ``False`` always
    overrides ``SCORER_GOVERNED_WRITES``.  This keeps the legacy raw-write
    path available for callers that need to opt out during rollout.
    """
    if governed_writes is not None:
        return bool(governed_writes)
    return os.environ.get("SCORER_GOVERNED_WRITES", "").strip() == "1"


def compute_theta_min(alpha: float, verified: int | float) -> float | None:
    """Return the canonical conservation threshold.

    ``alpha`` is analyst override rate: the fraction of verified decisions where
    the analyst disagreed with the system recommendation. It is not the domain
    penalty ratio used for asymmetric loss or reward scaling.

    Returns None when inputs are invalid or alpha is zero (no override baseline).
    """
    try:
        alpha_value = float(alpha)
        verified_value = float(verified)
    except (TypeError, ValueError):
        return None
    if (
        not np.isfinite(alpha_value)
        or not np.isfinite(verified_value)
        or alpha_value <= 0
        or verified_value <= 0
    ):
        return None
    return 23.53 / (alpha_value * verified_value)


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
        scorer: ProfileScorer,
        graph_store: GraphStore,
        reward_function: Any | None = None,
        credit_assigner: Any | None = None,
        exploration_policy: Any | None = None,
        evolve: bool = False,
        consolidation_enabled: bool = False,
        governed_writes: bool | None = None,
    ):
        self._preset = preset
        self._scorer = scorer
        self._graph_store = graph_store
        self._domain = str(getattr(graph_store, "domain", preset.name) or preset.name)
        self._reward_fn = reward_function
        self._credit = credit_assigner
        self._explorer = exploration_policy
        self._evolve = bool(evolve)
        self._evolver: Any | None = None
        self._evolve_count = 0
        self._last_conflict: JudgmentConflict | None = None
        self._consolidation_enabled = bool(consolidation_enabled)
        self._governed_writes = _resolve_governed_writes(governed_writes)
        if self._governed_writes and not isinstance(graph_store, ProtocolV2GraphStore):
            raise TypeError(
                "Governed writes require a Protocol V2 graph store. "
                "Ensure GRAPH_BACKEND supports V2."
            )
        self._batch_decision_count = 0
        self._batch_decision_time_start: str | None = None
        self._batch_decision_time_end: str | None = None
        self._last_checkpoint_decision_id: str | None = None
        self._last_checkpoint_category: str | None = None
        self._last_checkpoint_action: str | None = None
        self._last_checkpoint_iks: float | None = None
        self._last_persisted_fingerprint_signature: str | None = None
        try:
            self._outbox: PersistenceOutbox | None = PersistenceOutbox(self._domain)
            drained, failed = self._outbox.drain(self._graph_store)
            if drained or failed:
                logger.info("Outbox drain: %d replayed, %d failed", drained, failed)
        except Exception as exc:
            self._outbox = None
            logger.warning("Persistence outbox unavailable for %s: %s", self._domain, exc)
        if self._evolve:
            self._setup_evolution()

    def _predict(
        self,
        factors: dict[str, float],
        category: str,
    ) -> tuple[int, dict[str, float], np.ndarray, Any, int, str, list[float]]:
        _reject_sample_provenance(factors)
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
        return (
            category_index,
            factor_values,
            factor_vector,
            gae_result,
            action_index,
            action,
            probabilities,
        )

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
        consolidation_enabled: bool = False,
        enable_rl: bool = True,
        governed_writes: bool | None = None,
        profile: str = "production",
    ) -> "CompoundingScorer":
        if profile not in {"production", "test", "development"}:
            raise ValueError("profile must be 'production', 'test', or 'development'")
        if domain not in PRESET_REGISTRY:
            available = ", ".join(sorted(PRESET_REGISTRY)) or "(none)"
            raise ValueError(f"Unknown preset {domain!r}. Available presets: {available}")

        preset_cls = PRESET_REGISTRY[domain]
        preset = preset_cls()
        if db_path is None:
            data_dir = Path(__file__).resolve().parents[1] / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / f"{domain}.db")

        if graph_store is None and profile == "production":
            raise RuntimeError(
                "Production scorer requires an injected GraphStore. "
                "Use create_graph_store() or pass graph_store explicitly."
            )
        if graph_store is None and profile == "test":
            from copilot_sdk.graph.memory_store import InMemoryGraphStore

            graph_store = InMemoryGraphStore(domain=preset.name)
        elif graph_store is None:
            # Development-only SQLite fallback; production requires an injected
            # AGE-backed store and is rejected above.
            from copilot_sdk.graph.sqlite_store import SQLiteGraphStore

            graph_store = SQLiteGraphStore(db_path, domain=preset.name)
        if profile == "production":
            from copilot_sdk.graph.memory_store import InMemoryGraphStore
            from copilot_sdk.graph.sqlite_store import SQLiteGraphStore

            if isinstance(graph_store, (SQLiteGraphStore, InMemoryGraphStore)):
                raise RuntimeError(
                    "Production scorer requires an AGE-backed GraphStore; "
                    "SQLite and InMemoryGraphStore are test/development stores."
                )
        centroids = graph_store.load_latest_centroids(preset.name)
        if centroids is None:
            centroids = np.array(preset.bootstrap_centroids, dtype=np.float64, copy=True)

        learning_strategy = LearningStrategy(
            phase_policy=DecisionCountPolicy(n=200),
            dk_estimator=CoordinateDescentEstimator(),
            shrinkage_schedule=FixedAlpha(0.5),
        )
        scorer = ProfileScorer(
            mu=centroids,
            actions=list(preset.shape.action_names),
            categories=list(preset.shape.category_names),
            eta_override=0.01,
            auto_pause_on_amber=True,
            learning_strategy=learning_strategy,
        )
        if enable_rl and (
            reward_function is None
            or credit_assigner is None
            or exploration_policy is None
        ):
            try:
                from copilot_sdk.rl.presets import get_rl_components

                components = get_rl_components(domain, preset, graph_store=graph_store)
            except Exception as exc:
                logger.warning("RL setup failed for preset %s; continuing without RL: %s", domain, exc)
            else:
                if components is not None:
                    if reward_function is None:
                        reward_function = components.get("reward_function")
                    if credit_assigner is None:
                        credit_assigner = components.get("credit_assigner")
                    if exploration_policy is None:
                        exploration_policy = components.get("exploration_policy")
        return cls(
            preset=preset,
            scorer=scorer,
            graph_store=graph_store,
            reward_function=reward_function,
            credit_assigner=credit_assigner,
            exploration_policy=exploration_policy,
            evolve=evolve,
            consolidation_enabled=consolidation_enabled,
            governed_writes=governed_writes,
        )

    def score(
        self,
        factors: dict[str, float],
        category: str,
        metadata: dict[str, Any] | None = None,
    ) -> ScoreResult:
        (
            category_index,
            factor_values,
            factor_vector,
            gae_result,
            action_index,
            action,
            probabilities,
        ) = self._predict(factors, category)
        if self._governed_writes:
            governed_store = cast(ProtocolV2GraphStore, self._graph_store)
            decision_id = governed_store.generate_decision_id(self._domain)
            logger.info("GOVERNED_SCORE: id=%s store=%s", decision_id, type(self._graph_store).__name__)
        else:
            decision_id = uuid.uuid4().hex[:12]
        decision_metadata = dict(metadata or {})
        decision_metadata.update({
            "decision_id": decision_id,
            "domain": self._domain,
            "category_index": category_index,
            "factor_vector": factor_vector.tolist(),
            "recommended_index": action_index,
            "probabilities": probabilities,
            "created_at": time.time(),
        })
        decision_metadata.setdefault("entity_id", decision_id)
        if self._governed_writes:
            governed_store.write_governed_decision(
                decision_id=decision_id,
                domain=self._domain,
                category=category,
                category_index=category_index,
                recommended_action=action,
                recommended_index=action_index,
                confidence=float(gae_result.confidence),
                probabilities=probabilities,
                factor_vector=factor_vector.tolist(),
                factor_names=list(self._preset.shape.factor_names),
                source="compounding_scorer",
                scorer_version="copilot_sdk.compounding_scorer.v1",
                preset_version=f"{self._preset.name}.v1",
                factor_schema_version=f"{self._preset.name}.factor_schema.v1",
                metadata=decision_metadata,
            )
        else:
            stored_id = self._graph_store.write_decision(
                self._domain,
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

    def score_read_only(
        self,
        factors: dict[str, float],
        category: str,
    ) -> ScoreResult:
        """Return a live scorer prediction without persisting a Decision."""
        (
            _category_index,
            factor_values,
            _factor_vector,
            gae_result,
            action_index,
            action,
            probabilities,
        ) = self._predict(factors, category)
        return ScoreResult(
            decision_id=f"preview-{uuid.uuid4().hex[:12]}",
            action=action,
            action_index=action_index,
            confidence=float(gae_result.confidence),
            probabilities=probabilities,
            category=category,
            factors=factor_values,
        )

    def reestimate_dk_if_due(self) -> bool:
        """Run GAE DK re-estimation and report whether active weights changed."""
        before = getattr(self._scorer, "_dk_weights", None)
        before_array = None if before is None else np.asarray(before, dtype=np.float64).copy()

        self._scorer.reestimate_dk()

        after = getattr(self._scorer, "_dk_weights", None)
        if after is None:
            graph_decisions = _dk_decisions_from_store(self._graph_store, self._preset.shape.n_factors)
            if len(graph_decisions) >= 2:
                graph_decision_count = len(graph_decisions)
                after = CoordinateDescentEstimator().estimate(
                    graph_decisions,
                    self._scorer.centroids,
                    self._preset.shape.n_categories,
                    self._preset.shape.n_factors,
                )
                if float(np.var(np.asarray(after, dtype=np.float64))) < 1e-12:
                    if graph_decision_count < 200:
                        logger.warning(
                            "DK estimation: insufficient decisions (N=%s < 200), using dispersion fallback",
                            graph_decision_count,
                        )
                        after = _dk_factor_dispersion_weights(
                            graph_decisions,
                            self._preset.shape.n_categories,
                            self._preset.shape.n_factors,
                        )
                    else:
                        logger.warning(
                            "DK estimation: uniform weights at N=%s decisions (genuine no-discrimination signal)",
                            graph_decision_count,
                        )
                setattr(self._scorer, "_dk_weights", after)
        if after is None:
            return False
        after_array = np.asarray(after, dtype=np.float64).copy()
        if before_array is None:
            return True
        return bool(not np.array_equal(before_array, after_array))

    def get_dk_weights(self) -> list[list[float]] | None:
        """Return a copy of current GAE DK weights when variance learning is active."""
        weights = getattr(self._scorer, "_dk_weights", None)
        if weights is None:
            return None
        return cast(list[list[float]], np.asarray(weights, dtype=np.float64).copy().tolist())

    def get_centroid(self, category: str, action: str) -> list[float] | None:
        """Return a copy of the current centroid vector for category/action."""
        if category not in self._preset.shape.category_names:
            raise ValueError(f"unknown category: {category}")
        if action not in self._preset.shape.action_names:
            raise ValueError(f"unknown action: {action}")
        category_index = self._preset.shape.category_names.index(category)
        action_index = self._preset.shape.action_names.index(action)
        centroids = np.asarray(self._scorer.centroids, dtype=np.float64)
        expected = (
            self._preset.shape.n_categories,
            len(self._preset.shape.action_names),
            self._preset.shape.n_factors,
        )
        if centroids.shape != expected:
            raise ValueError(f"centroid tensor shape {centroids.shape} != {expected}")
        vector = centroids[category_index, action_index, :]
        return cast(list[float], vector.copy().tolist())

    def get_category_phase(self, category: str) -> str:
        """Return the GAE learning phase for a category when available."""
        if category not in self._preset.shape.category_names:
            raise ValueError(f"unknown category: {category}")
        category_index = self._preset.shape.category_names.index(category)
        category_states = getattr(self._scorer, "_category_states", None)
        if category_states is None:
            category_states = getattr(self._scorer, "category_states", None)
        if category_states is None:
            return "UNKNOWN"
        try:
            state = category_states[category_index]
        except (IndexError, KeyError, TypeError):
            return "UNKNOWN"
        phase = getattr(state, "phase", None)
        if phase is None and isinstance(state, dict):
            phase = state.get("phase")
        if phase is None:
            return "UNKNOWN"
        value = getattr(phase, "value", phase)
        name = getattr(value, "name", value)
        phase_name = str(name)
        if phase_name in {"MEAN_CONVERGENCE", "VARIANCE_LEARNING"}:
            return phase_name
        if phase_name.endswith(".MEAN_CONVERGENCE"):
            return "MEAN_CONVERGENCE"
        if phase_name.endswith(".VARIANCE_LEARNING"):
            return "VARIANCE_LEARNING"
        return "UNKNOWN"

    def load_dk_weights_from_l5(self, weight_tensor: Any) -> bool:
        """Load validated L5 DK weights into the active GAE scorer."""
        weights = np.asarray(weight_tensor, dtype=np.float64)
        expected = (
            self._preset.shape.n_categories,
            self._preset.shape.n_factors,
        )
        if weights.shape != expected:
            raise ValueError(f"DK weight shape {weights.shape} != {expected}")
        if not np.all(np.isfinite(weights)):
            raise ValueError("DK weights must be finite")
        self._scorer._dk_weights = weights.copy()
        return True

    def load_centroids_from_l5(self, centroids: list[dict[str, Any]]) -> bool:
        """Load validated L5 centroid rows into the active GAE centroid tensor."""
        if not centroids:
            return False
        restored = np.asarray(self._scorer.centroids, dtype=np.float64).copy()
        category_index = {
            name: index for index, name in enumerate(self._preset.shape.category_names)
        }
        action_index = {
            name: index for index, name in enumerate(self._preset.shape.action_names)
        }
        for row in centroids:
            category = str(row.get("category"))
            action = str(row.get("action"))
            if category not in category_index or action not in action_index:
                raise ValueError(f"unknown centroid identity: {category}/{action}")
            vector = np.asarray(row.get("vector_json"), dtype=np.float64)
            expected = (self._preset.shape.n_factors,)
            if vector.shape != expected:
                raise ValueError(f"centroid vector shape {vector.shape} != {expected}")
            if not np.all(np.isfinite(vector)):
                raise ValueError("centroid vector must be finite")
            restored[category_index[category], action_index[action], :] = vector
        self._scorer.centroids = restored
        return True

    def get_verified_count(self) -> int:
        """Return the current verified-decision count from the GraphStore."""
        return int(self._graph_store.count_verified_decisions(self._domain))

    def learn(
        self,
        decision_id: str,
        actual_action: str,
        outcome: str = "confirmed",
        *,
        consolidate: bool = False,
        context: dict[str, Any] | None = None,
        persist_artifacts: bool = True,
    ) -> LearnResult | dict[str, Any]:
        decision = self._graph_store.get_decision(decision_id, domain=self._domain)
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
        self._detect_judgment_conflict(
            decision_id=decision_id,
            decision=decision,
            predicted_index=predicted_index,
            actual_correct=is_correct,
            factor_vector=factor_vector,
            confidence=confidence,
        )

        conservation_pause = self._conservation_pause()
        if conservation_pause is not None:
            return conservation_pause
        iks_before = self._compute_iks(persist_artifacts=False)
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
        category = str(_decision_field(decision, "category", ""))
        outcome_metadata: dict[str, Any] = {
            "actual_index": actual_index,
            "verified_at": time.time(),
            "outcome": outcome,
        }
        if context is not None:
            outcome_metadata["context"] = dict(context)
        self._graph_store.write_outcome(
            decision_id=decision_id,
            actual_action=actual_action,
            is_correct=is_correct,
            metadata=outcome_metadata,
            domain=self._domain,
        )
        if persist_artifacts:
            self._persist_evidence_receipt(
                decision_id=decision_id,
                actual_action=actual_action,
                is_correct=is_correct,
                outcome=outcome,
                metadata=outcome_metadata,
            )
        self._refresh_dk_after_learn()
        invoice_id = (context or {}).get("invoice_id")
        if invoice_id and isinstance(self._graph_store, ProtocolV2GraphStore):
            self._graph_store.link_entity(
                decision_id=decision_id,
                entity_id=str(invoice_id),
                entity_type="invoice",
                domain=self._domain,
            )
        iks_after = self._compute_iks(
            persist_artifacts=persist_artifacts,
            decision_id=decision_id,
        )
        self._last_checkpoint_decision_id = decision_id
        self._last_checkpoint_category = category
        self._last_checkpoint_action = actual_action
        self._last_checkpoint_iks = iks_after
        decision_timestamp = self._extract_decision_timestamp(decision)
        self._update_batch_decision_time_range(decision_timestamp)
        if self._consolidation_enabled:
            self._batch_decision_count += 1
            if consolidate:
                if persist_artifacts:
                    self._save_centroids_checkpoint(
                        decision_id=decision_id,
                        category=category,
                        action=actual_action,
                        iks=iks_after,
                        boundary="learn",
                        decisions_in_batch=self._batch_decision_count,
                        consolidation=True,
                        decision_time_start=self._batch_decision_time_start,
                        decision_time_end=self._batch_decision_time_end,
                    )
                self._batch_decision_count = 0
                self._batch_decision_time_start = None
                self._batch_decision_time_end = None
        else:
            if persist_artifacts:
                self._save_centroids_checkpoint(
                    decision_id=decision_id,
                    category=category,
                    action=actual_action,
                    iks=iks_after,
                    decision_time_start=decision_timestamp,
                    decision_time_end=decision_timestamp,
                )
        reward_raw, reward = self._compute_rl_reward(decision, actual_action, outcome, context)
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

        self._maybe_archive()

        if persist_artifacts:
            self._persist_learning_artifacts(
                decision_id,
                actual_action=actual_action,
                is_correct=is_correct,
                outcome=outcome,
                category=category,
                metadata=outcome_metadata,
                evidence_already_persisted=True,
                checkpoint_already_persisted=True,
            )

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

    def fingerprint(
        self,
        *,
        persist: bool = True,
        decision_id: str | None = None,
    ) -> FingerprintResult:
        result = compute_fingerprint(
            self._graph_store.get_verified_decisions(self._domain),
            list(self._preset.shape.factor_names),
        )
        if persist:
            self._persist_fingerprint(result, decision_id=decision_id)
        return result

    def _persist_learning_artifacts(
        self,
        decision_id: str,
        *,
        actual_action: str | None = None,
        is_correct: bool | None = None,
        outcome: str | None = None,
        category: str | None = None,
        metadata: dict[str, Any] | None = None,
        evidence_already_persisted: bool = False,
        checkpoint_already_persisted: bool = False,
    ) -> None:
        """Persist learning artifacts after a successful update.

        The shared ``learn`` path already persists its evidence receipt and
        centroid checkpoint before reaching this coordinator.  The explicit
        flags preserve that ordering without duplicating those writes, while
        allowing the SOC raw-profile bridge to use this method independently.
        """
        if not isinstance(self._graph_store, ProtocolV2GraphStore):
            return

        decision: dict[str, Any] | None = None

        def load_decision() -> dict[str, Any]:
            nonlocal decision
            if decision is None:
                loaded = self._graph_store.get_decision(decision_id, domain=self._domain)
                if loaded is None:
                    raise KeyError(decision_id)
                decision = loaded
            return decision

        def record_failure(
            artifact_type: str,
            payload: dict[str, Any],
            exc: Exception,
        ) -> None:
            if self._outbox is None:
                return
            try:
                self._outbox.record_failure(decision_id, artifact_type, payload, str(exc))
            except Exception as outbox_exc:
                logger.warning(
                    "Persistence outbox record failed: domain=%s decision=%s artifact=%s error=%s: %s",
                    self._domain,
                    decision_id,
                    artifact_type,
                    type(outbox_exc).__name__,
                    outbox_exc,
                )

        conservation_payload: dict[str, Any] = {}
        try:
            from copilot_sdk.backend.conservation_utils import compute_conservation_metrics

            metrics = compute_conservation_metrics(self, domain=self._domain)
            theta_min = float(metrics["theta_min"])
            if not math.isfinite(theta_min):
                logger.warning(
                    "Cold start: theta_min=%s, skipping conservation snapshot",
                    theta_min,
                )
            else:
                conservation_payload = {
                    "status_id": f"{self._domain}:conservation:{decision_id}",
                    "domain": self._domain,
                    "V": int(metrics["V"]),
                    "q": float(metrics["q"]),
                    "alpha": float(metrics["alpha"]),
                    "theta_min": theta_min,
                    "verified_count": int(metrics["V"]),
                    "correct_count": int(round(float(metrics["q"]) * int(metrics["V"]))),
                    "status": str(metrics["status"]),
                    "policy_version": "conservation.v1",
                }
                self._graph_store.write_conservation_status(**conservation_payload)
        except Exception as exc:
            logger.warning(
                "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",
                self._domain, decision_id, "conservation", type(exc).__name__, exc,
            )
            record_failure("conservation", conservation_payload, exc)

        try:
            fingerprint = self.fingerprint(persist=False)
            self._persist_fingerprint(fingerprint, decision_id=decision_id)
        except Exception as exc:
            logger.warning(
                "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",
                self._domain, decision_id, "fingerprint", type(exc).__name__, exc,
            )
            record_failure("fingerprint", {}, exc)

        if not evidence_already_persisted:
            try:
                row = load_decision()
                resolved_correct = bool(
                    is_correct if is_correct is not None else _is_correct_decision(row)
                )
                resolved_action = actual_action
                if resolved_action is None:
                    resolved_action = _decision_field(
                        row,
                        "actual_action",
                        _decision_field(row, "recommended_action", _decision_field(row, "action", "")),
                    )
                resolved_outcome = outcome
                if resolved_outcome is None:
                    resolved_outcome = _decision_field(
                        row,
                        "outcome",
                        "confirmed" if resolved_correct else "overridden",
                    )
                resolved_metadata = metadata
                if resolved_metadata is None:
                    candidate_metadata = _decision_field(row, "outcome_metadata", {})
                    resolved_metadata = candidate_metadata if isinstance(candidate_metadata, dict) else {}
                self._persist_evidence_receipt(
                    decision_id=decision_id,
                    actual_action=str(resolved_action or ""),
                    is_correct=resolved_correct,
                    outcome=str(resolved_outcome),
                    metadata=dict(resolved_metadata),
                )
            except Exception as exc:
                logger.warning(
                    "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",
                    self._domain, decision_id, "evidence_receipt", type(exc).__name__, exc,
                )
                record_failure("evidence_receipt", {}, exc)

        if not checkpoint_already_persisted:
            try:
                row = load_decision()
                checkpoint_category = category or str(_decision_field(row, "category", ""))
                if not checkpoint_category:
                    raise ValueError(f"Decision {decision_id} has no category")
                resolved_action = actual_action
                if resolved_action is None:
                    resolved_action = _decision_field(
                        row,
                        "actual_action",
                        _decision_field(row, "recommended_action", _decision_field(row, "action", "")),
                    )
                if not resolved_action:
                    raise ValueError(f"Decision {decision_id} has no action")
                self._save_centroids_checkpoint(
                    decision_id=decision_id,
                    category=checkpoint_category,
                    action=str(resolved_action),
                    iks=self._compute_iks(persist_artifacts=False),
                    decision_time_start=self._extract_decision_timestamp(row),
                    decision_time_end=self._extract_decision_timestamp(row),
                )
            except Exception as exc:
                logger.warning(
                    "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",
                    self._domain, decision_id, "centroid_checkpoint", type(exc).__name__, exc,
                )
                record_failure("centroid_checkpoint", {}, exc)

    def _persist_evidence_receipt(
        self,
        *,
        decision_id: str,
        actual_action: str,
        is_correct: bool,
        outcome: str,
        metadata: dict[str, Any],
    ) -> None:
        if not isinstance(self._graph_store, ProtocolV2GraphStore):
            return
        receipt_intent_id = f"{self._domain}:outcome:{decision_id}:{uuid.uuid4().hex}"
        canonical_payload: dict[str, Any] = {
            "receipt_type": "post_outcome_verification",
            "decision_id": decision_id,
            "actual_action": actual_action,
            "is_correct": bool(is_correct),
            "outcome": outcome,
            "metadata": dict(metadata),
        }
        evidence_payload: dict[str, Any] = {
            "receipt_intent_id": receipt_intent_id,
            "domain": self._domain,
            "decision_id": decision_id,
            "canonical_payload": canonical_payload,
            "actor": "compounding_scorer",
            "source_route": "copilot_sdk.scoring.learn",
        }
        try:
            self._graph_store.append_evidence_receipt(
                receipt_intent_id=receipt_intent_id,
                domain=self._domain,
                decision_id=decision_id,
                canonical_payload=canonical_payload,
                actor="compounding_scorer",
                source_route="copilot_sdk.scoring.learn",
            )
        except Exception as exc:
            logger.warning(
                "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",
                self._domain, decision_id, "evidence_receipt", type(exc).__name__, exc,
            )
            if self._outbox is not None:
                try:
                    self._outbox.record_failure(
                        decision_id,
                        "evidence_receipt",
                        evidence_payload,
                        str(exc),
                    )
                except Exception as outbox_exc:
                    logger.warning("Persistence outbox record failed: %s", outbox_exc)

    def _persist_fingerprint(
        self,
        result: FingerprintResult,
        *,
        decision_id: str | None = None,
    ) -> None:
        if not isinstance(self._graph_store, ProtocolV2GraphStore):
            return
        factor_names = list(self._preset.shape.factor_names)
        factor_stats = {
            "factors": [
                {
                    "name": factor.name,
                    "sigma": float(factor.sigma),
                    "weight": float(factor.weight),
                    "interpretation": factor.interpretation,
                }
                for factor in result.factors
            ],
            "overall_win_rate": float(result.overall_win_rate),
            "per_category_precision": dict(result.per_category_precision),
            "decisions_analyzed": int(result.decisions_analyzed),
        }
        canonical = json.dumps(
            {
                "domain": self._domain,
                "factor_names": factor_names,
                "factor_stats": factor_stats,
                "skipped_incompatible": int(result.skipped_decisions),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        signature = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if signature == self._last_persisted_fingerprint_signature:
            return
        fingerprint_id = f"{self._domain}:fingerprint:{signature[:32]}"
        fingerprint_metadata: dict[str, Any] = {
            "source": "compounding_scorer.fingerprint",
        }
        fingerprint_payload: dict[str, Any] = {
            "fingerprint_id": fingerprint_id,
            "domain": self._domain,
            "factor_names": factor_names,
            "factor_stats": factor_stats,
            "skipped_incompatible": int(result.skipped_decisions),
            "window": int(result.decisions_analyzed),
            "metadata": fingerprint_metadata,
        }
        try:
            self._graph_store.write_fingerprint(
                fingerprint_id=fingerprint_id,
                domain=self._domain,
                factor_names=factor_names,
                factor_stats=factor_stats,
                skipped_incompatible=int(result.skipped_decisions),
                window=int(result.decisions_analyzed),
                metadata=fingerprint_metadata,
            )
        except Exception as exc:
            logger.warning(
                "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",
                self._domain,
                decision_id or "unknown",
                "fingerprint",
                type(exc).__name__,
                exc,
            )
            if self._outbox is not None:
                try:
                    self._outbox.record_failure(
                        decision_id or "unknown",
                        "fingerprint",
                        fingerprint_payload,
                        str(exc),
                    )
                except Exception as outbox_exc:
                    logger.warning("Persistence outbox record failed: %s", outbox_exc)
            return
        self._last_persisted_fingerprint_signature = signature

    @property
    def last_conflict(self) -> JudgmentConflict | None:
        return self._last_conflict

    def flush_centroids(self, reason: str = "manual") -> int:
        if not self._consolidation_enabled or self._batch_decision_count == 0:
            return 0
        if self._last_checkpoint_decision_id is None or self._last_checkpoint_category is None:
            return 0
        flushed = self._batch_decision_count
        self._save_centroids_checkpoint(
            decision_id=self._last_checkpoint_decision_id,
            category=self._last_checkpoint_category,
            action=self._last_checkpoint_action or self._preset.shape.action_names[0],
            iks=self._last_checkpoint_iks if self._last_checkpoint_iks is not None else self._compute_iks(),
            boundary=str(reason),
            decisions_in_batch=flushed,
            consolidation=True,
            decision_time_start=self._batch_decision_time_start,
            decision_time_end=self._batch_decision_time_end,
        )
        self._batch_decision_count = 0
        self._batch_decision_time_start = None
        self._batch_decision_time_end = None
        return flushed

    def trajectory(
        self,
        *,
        checkpoint_time_start: str | None = None,
        checkpoint_time_end: str | None = None,
        decision_time_start: str | None = None,
        decision_time_end: str | None = None,
        category: str | None = None,
    ) -> TrajectoryResult:
        return compute_trajectory(
            self._graph_store.get_centroid_checkpoints(
                self._domain,
                checkpoint_time_start=checkpoint_time_start,
                checkpoint_time_end=checkpoint_time_end,
                decision_time_start=decision_time_start,
                decision_time_end=decision_time_end,
                category=category,
            ),
            self._graph_store.get_verified_decisions(self._domain),
            self._preset.shape,
        )

    def get_phase(self) -> str:
        """Return the current SDK phase from GraphStore verification counts."""
        try:
            verified = int(self._graph_store.count_verified(self._domain))
            if verified < 10:
                return "A"
            correct = int(self._graph_store.count_correct(self._domain))
            q = correct / verified
            return "B" if q >= 0.5 else "A"
        except Exception:
            return "A"

    def get_alpha(self) -> float:
        """Return current verified accuracy from GraphStore counts."""
        try:
            verified = int(self._graph_store.count_verified(self._domain))
            if verified == 0:
                return 0.0
            correct = int(self._graph_store.count_correct(self._domain))
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
            if isinstance(self._graph_store, GraphStore):
                try:
                    self._graph_store.save_centroids(
                        self._domain,
                        "warm_start",
                        self._scorer.centroids,
                        metadata={
                            "decision_id": f"warm-start-{uuid.uuid4().hex[:12]}",
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
            "decisions": self._graph_store.get_all_decisions(self._domain),
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

    def _compute_iks(
        self,
        *,
        persist_artifacts: bool = True,
        decision_id: str | None = None,
    ) -> float:
        try:
            verified = self._graph_store.count_verified(self._domain)
        except Exception:
            verified_decisions = _verified_decisions(self._graph_store) or []
            verified = len(verified_decisions)
        if verified == 0:
            return 0.0

        try:
            correct = self._graph_store.count_correct(self._domain)
        except Exception:
            verified_decisions = _verified_decisions(self._graph_store) or []
            correct = sum(1 for decision in verified_decisions if _is_correct_decision(decision))
        accuracy = correct / verified
        fingerprint = self.fingerprint(
            persist=persist_artifacts,
            decision_id=decision_id,
        )
        mean_sigma = (
            sum(factor.sigma for factor in fingerprint.factors) / len(fingerprint.factors)
            if fingerprint.factors
            else 0.5
        )
        fingerprint_component = max(0.0, min((1.0 - mean_sigma / 0.5) * 25.0, 25.0))
        coverage = _count_categories_with_n(
            self._graph_store.get_verified_decisions(self._domain),
            10,
        ) / self._preset.shape.n_categories

        iks = (
            min(verified / 500.0, 1.0) * 25.0
            + accuracy * 25.0
            + fingerprint_component
            + coverage * 25.0
        )
        return round(iks, 1)

    def _refresh_dk_after_learn(self) -> None:
        """Refresh DK weights once enough verified decisions exist."""
        if self.get_verified_count() < 400:
            return
        try:
            self.reestimate_dk_if_due()
        except Exception as exc:
            logger.warning("DK re-estimation failed for %s: %s", self._domain, exc)

    def _conservation_pause(self) -> dict[str, Any] | None:
        try:
            verified, correct, override_rate = _conservation_stats(self._graph_store)
        except Exception:
            return None
        if verified <= 0:
            return None

        q = correct / verified
        recent_window = max(int(getattr(self._preset, "conservation_recent_window", 100)), 1)
        recent_q_threshold = float(getattr(self._preset, "conservation_recent_q_threshold", 0.75))
        recent_quality = _recent_quality(self._graph_store, window=recent_window)
        if recent_quality is not None:
            recent_count, recent_q = recent_quality
            if recent_count >= recent_window and recent_q < recent_q_threshold:
                return {
                    "status": "paused",
                    "reason": "conservation_red",
                    "q": q,
                    "theta_min": recent_q_threshold,
                    "verified_count": verified,
                    "correct_count": correct,
                    "override_rate": override_rate,
                    "recent_q": recent_q,
                    "recent_window": recent_count,
                }
        theta_min = compute_theta_min(override_rate, verified)
        dispersion = _conservation_dispersion(self._graph_store)
        effective_q = q
        if dispersion is not None and float(dispersion.get("inflation", 0.0)) > 1.3:
            logger.info(
                "Conservation dispersion: inflation=%.2f",
                float(dispersion["inflation"]),
            )
            effective_q = max(0.0, q - float(dispersion.get("effective_se", 0.0)))
        if theta_min is not None and effective_q < theta_min:
            if dispersion is not None and float(dispersion.get("inflation", 0.0)) > 1.3:
                dispersion = {**dispersion, "q_conservative": effective_q}
            result = {
                "status": "paused",
                "reason": "conservation_red",
                "q": q,
                "theta_min": theta_min,
                "verified_count": verified,
                "correct_count": correct,
                "override_rate": override_rate,
            }
            if dispersion is not None:
                result["dispersion"] = dispersion
            return result
        return None

    def _compute_rl_reward(
        self,
        decision: dict[str, Any],
        actual_action: str,
        outcome: str,
        context: dict[str, Any] | None = None,
    ) -> tuple[float | None, float | None]:
        if self._reward_fn is None:
            return None, None

        outcome_dict = {"outcome": outcome}
        if context:
            outcome_dict.update(dict(context))
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

    def _detect_judgment_conflict(
        self,
        *,
        decision_id: str,
        decision: dict[str, Any],
        predicted_index: int,
        actual_correct: bool,
        factor_vector: np.ndarray,
        confidence: float,
    ) -> None:
        self._last_conflict = None
        try:
            self._last_conflict = detect_conflict(
                decision_id=decision_id,
                predicted_success=_predicted_success(decision, predicted_index, confidence),
                actual_correct=actual_correct,
                factors=factor_vector.tolist(),
                fingerprint_weights=self._fingerprint_weight_map(),
                factor_names=list(self._preset.shape.factor_names),
            )
        except (TypeError, ValueError) as exc:
            logger.debug("Could not compute judgment conflict for %s: %s", decision_id, exc)
            self._last_conflict = None

    def _fingerprint_weight_map(self) -> dict[str, float]:
        try:
            fingerprint = self.fingerprint()
        except Exception as exc:
            logger.debug("Could not compute fingerprint weights for conflict detection: %s", exc)
            return {}
        weights: dict[str, float] = {}
        for factor in fingerprint.factors:
            try:
                weight = float(factor.weight)
            except (TypeError, ValueError):
                weight = 0.0
            if not np.isfinite(weight):
                weight = 0.0
            weights[str(factor.name)] = max(0.0, min(weight, 1.0))
        return weights

    def _save_centroids_checkpoint(
        self,
        *,
        decision_id: str,
        category: str,
        action: str,
        iks: float,
        boundary: str | None = None,
        decisions_in_batch: int | None = None,
        consolidation: bool = False,
        decision_time_start: str | None = None,
        decision_time_end: str | None = None,
    ) -> None:
        metadata: dict[str, Any] = {"iks": iks}
        if consolidation:
            metadata.update({
                "boundary": boundary,
                "decisions_in_batch": decisions_in_batch,
                "consolidation": True,
            })
        checkpoint_payload: dict[str, Any] = {}
        try:
            self._graph_store.save_centroids(
                self._domain,
                category,
                self._scorer.centroids,
                metadata=metadata,
                decision_id=decision_id,
                decision_time_start=decision_time_start,
                decision_time_end=decision_time_end,
            )
        except Exception as exc:
            logger.warning(
                "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",
                self._domain, decision_id, "centroid_checkpoint", type(exc).__name__, exc,
            )
        if not isinstance(self._graph_store, ProtocolV2GraphStore):
            return
        try:
            # NOTE: Legacy checkpoint creates HAS_CENTROID_CHECKPOINT edge.
            # V2 checkpoint stores richer metadata without the edge.
            # When V2 adds edge creation, legacy path should be removed.
            # Until then, both writes are intentional.
            factor_names = list(self._preset.shape.factor_names)
            factor_names_hash = hashlib.sha256(
                json.dumps(factor_names, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            checkpoint_payload = {
                "checkpoint_id": f"{self._domain}:checkpoint:{uuid.uuid4().hex}",
                "domain": self._domain,
                "category": category,
                "action": action,
                "centroids": self._scorer.centroids,
                "decisions_count": int(decisions_in_batch or 1),
                "verified_count": self.get_verified_count(),
                "iks": float(iks),
                "shape": [int(value) for value in self._scorer.centroids.shape],
                "factor_names_hash": factor_names_hash,
                "metadata": {**metadata, "decision_id": decision_id},
            }
            self._graph_store.write_centroid_checkpoint(**checkpoint_payload)
        except Exception as exc:
            logger.warning(
                "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",
                self._domain, decision_id, "centroid_checkpoint", type(exc).__name__, exc,
            )
            if self._outbox is not None:
                try:
                    self._outbox.record_failure(
                        decision_id,
                        "centroid_checkpoint",
                        checkpoint_payload,
                        str(exc),
                    )
                except Exception as outbox_exc:
                    logger.warning("Persistence outbox record failed: %s", outbox_exc)

    def _maybe_archive(self, keep_recent: int = 800) -> None:
        try:
            count = int(self._graph_store.count_decisions(self._domain))
            if count <= keep_recent:
                return
            archived = int(
                self._graph_store.archive_old_decisions(
                    self._domain,
                    keep_recent=keep_recent,
                )
            )
            if archived > 0:
                print(f"[{self._domain}] archived {archived} old decisions")
        except Exception as exc:
            logger.warning("Decision archive failed for %s: %s", self._domain, exc)

    def _extract_decision_timestamp(self, decision: dict[str, Any] | None) -> str | None:
        """Extract the decision-time timestamp without substituting wall clock time."""
        if not isinstance(decision, dict):
            return None
        for key in ("decision_time", "event_time", "timestamp", "created_at"):
            normalized = _normalize_decision_timestamp(_decision_field(decision, key))
            if normalized is not None:
                return normalized
        return None

    def _update_batch_decision_time_range(self, timestamp: str | None) -> None:
        if timestamp is None:
            return
        if self._batch_decision_time_start is None or timestamp < self._batch_decision_time_start:
            self._batch_decision_time_start = timestamp
        if self._batch_decision_time_end is None or timestamp > self._batch_decision_time_end:
            self._batch_decision_time_end = timestamp

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
            from copilot_sdk.evolution.toy_rules import ActionBiasRule, ConfidenceBoundaryRule, FactorWeightRule
            ThresholdRule = ConfidenceBoundaryRule
        except Exception as exc:
            logger.warning("Evolution disabled: failed to import evolution components: %s", exc)
            self._evolve = False
            self._evolver = None
            return

        ledger = InMemoryEvolutionLedger(
            evolution_store=cast(EvolutionStore, self._graph_store),
            domain=self._domain,
        )
        evolver = AgentEvolver(
            ledger=ledger,
            shadow_runner=DefaultShadowRunner(),
            promotion_gate=DefaultPromotionGate(),
            plateau_config=getattr(self._preset, "plateau_config", None),
        )
        evolver.register_rule(ThresholdRule(actions))
        evolver.register_rule(FactorWeightRule(actions, factor_count=factor_count))
        evolver.register_rule(ActionBiasRule(actions))
        self._evolver = evolver

    def _run_evolution(self) -> None:
        if self._evolver is None:
            return
        try:
            decisions = list(self._graph_store.get_verified_decisions(self._domain) or [])
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
            verified, correct, override_rate = _conservation_stats(self._graph_store)
        except Exception:
            return None
        if verified <= 0:
            return {
                "status": "GREEN",
                "verified_count": 0,
                "correct_count": 0,
                "q": 0.0,
                "theta_min": None,
                "override_rate": 0.0,
            }
        q = correct / verified
        theta_min = compute_theta_min(override_rate, verified)
        return {
            "status": "GREEN" if (theta_min is None or q >= theta_min) else "RED",
            "verified_count": verified,
            "correct_count": correct,
            "q": q,
            "theta_min": theta_min,
            "override_rate": override_rate,
        }

    @property
    def graph_store(self) -> GraphStore:
        """The GraphStore single source of truth."""
        return self._graph_store

    @property
    def gae_scorer(self) -> ProfileScorer:
        return self._scorer


def _conservation_counts(store: Any) -> tuple[int, int]:
    verified, correct, _override_rate = _conservation_stats(store)
    return verified, correct


def _conservation_dispersion(store: Any) -> dict[str, float] | None:
    verified_decisions = _conservation_verified_decisions(store)
    if not verified_decisions:
        return None
    q_window = [
        1.0 if _is_correct_decision(decision) else 0.0
        for decision in verified_decisions[-400:]
    ]
    if len(q_window) < 20:
        return None
    try:
        diagnostic = _block_bootstrap_mean_se(q_window)
    except Exception:
        return None
    inflation = float(diagnostic.inflation)
    effective_se = float(diagnostic.block_se if inflation > 1.3 else diagnostic.iid_se)
    return {
        "iid_se": float(diagnostic.iid_se),
        "block_se": float(diagnostic.block_se),
        "effective_se": effective_se,
        "inflation": inflation,
    }


def _block_bootstrap_mean_se(q_window: list[float]) -> Any:
    quant_root = Path(__file__).resolve().parents[2]
    if str(quant_root) not in sys.path:
        sys.path.insert(0, str(quant_root))
    quant_module = importlib.import_module("ci_trading.quant")
    return getattr(quant_module, "block_bootstrap_mean_se")(q_window, block=20, n_boot=200)


def _reject_sample_provenance(factors: dict[str, Any]) -> None:
    for name, value in factors.items():
        if isinstance(value, Provenanced) and str(value.source).strip().lower() == "sample":
            raise ValueError(f"F-22: sample-provenance value cannot enter scoring: {name}")


def _dk_decisions_from_store(store: Any, n_dims: int) -> list[tuple[np.ndarray, int, int]]:
    decisions = _verified_decisions(store) or []
    output: list[tuple[np.ndarray, int, int]] = []
    for decision in decisions:
        if not _is_correct_decision(decision):
            continue
        vector = np.asarray(_decision_field(decision, "factor_vector", []), dtype=np.float64)
        if vector.shape != (n_dims,):
            continue
        try:
            category_index = int(_decision_field(decision, "category_index", 0))
            action_index = int(_decision_field(decision, "actual_index", _decision_field(decision, "recommended_index", 0)))
        except (TypeError, ValueError):
            continue
        output.append((vector, category_index, action_index))
    return output


def _dk_factor_dispersion_weights(
    decisions: list[tuple[np.ndarray, int, int]],
    n_categories: int,
    n_dims: int,
) -> np.ndarray:
    vectors = np.asarray([vector for vector, _category, _action in decisions], dtype=np.float64)
    if vectors.ndim != 2 or vectors.shape[1] != n_dims:
        return np.ones((n_categories, n_dims), dtype=np.float64)
    variances = np.var(vectors, axis=0)
    mean_variance = float(np.mean(variances))
    if mean_variance <= 0.0:
        return np.ones((n_categories, n_dims), dtype=np.float64)
    weights = np.clip(variances / mean_variance, 0.25, 4.0)
    return np.tile(weights.reshape(1, n_dims), (n_categories, 1))


def _recent_quality(store: Any, *, window: int) -> tuple[int, float] | None:
    verified_decisions = _conservation_verified_decisions(store)
    if not verified_decisions:
        return None
    recent = verified_decisions[-max(int(window), 1):]
    if not recent:
        return None
    correct = sum(1 for decision in recent if _is_correct_decision(decision))
    return len(recent), correct / len(recent)


def _conservation_stats(store: Any) -> tuple[int, int, float]:
    domain = _store_domain(store)
    verified = max(int(store.count_verified(domain)), 0)
    correct = max(int(store.count_correct(domain)), 0)
    decisions = _conservation_verified_decisions(store)
    overrides = sum(1 for decision in decisions if _is_override_decision(decision))
    override_rate = overrides / verified if verified > 0 else 0.0
    return verified, correct, override_rate


def _verified_decisions(store: Any) -> list[dict[str, Any]]:
    domain = _store_domain(store)
    decisions = store.get_verified_decisions(domain)
    return [decision for decision in decisions if _is_verified_decision(decision)]


def _conservation_verified_decisions(store: Any) -> list[dict[str, Any]]:
    decisions = _verified_decisions(store)
    return [
        decision
        for decision in decisions
        if not _is_benchmark_decision(decision)
    ]


def _store_domain(store: Any) -> str:
    return str(getattr(store, "domain", "") or "")

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


def _normalize_decision_timestamp(value: Any) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float, np.integer, np.floating)):
        epoch = float(value)
        if not np.isfinite(epoch):
            return None
        return datetime.fromtimestamp(epoch, timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.astimezone(timezone.utc)
        return parsed.isoformat().replace("+00:00", "Z")
    return None


def _predicted_success(decision: dict[str, Any], predicted_index: int, confidence: float) -> float:
    probabilities = _decision_field(decision, "probabilities")
    if isinstance(probabilities, (list, tuple)) and 0 <= predicted_index < len(probabilities):
        try:
            predicted = float(probabilities[predicted_index])
        except (TypeError, ValueError):
            predicted = float(confidence)
    else:
        predicted = float(confidence)
    if not np.isfinite(predicted):
        predicted = 0.0
    return max(0.0, min(predicted, 1.0))


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


def _is_override_decision(decision: dict[str, Any]) -> bool:
    actual_action = _decision_field(decision, "actual_action")
    recommended_action = _decision_field(
        decision,
        "recommended_action",
        _decision_field(decision, "action"),
    )
    if actual_action is None or recommended_action is None:
        return False
    return str(actual_action) != str(recommended_action)


def _is_benchmark_decision(decision: dict[str, Any]) -> bool:
    context = decision.get("context")
    if isinstance(context, dict) and context.get("benchmark") is True:
        return True
    metadata = decision.get("outcome_metadata")
    if isinstance(metadata, dict):
        nested = metadata.get("context")
        if isinstance(nested, dict) and nested.get("benchmark") is True:
            return True
    return False


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
