"""GAE-backed CompoundingScorer facade."""

from __future__ import annotations

import asyncio
import hashlib
import inspect
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
from typing import Any, Coroutine, Optional, cast

import numpy as np

from copilot_sdk.scoring.config import DomainPreset
from copilot_sdk.scoring.conflict import JudgmentConflict, detect_conflict
from copilot_sdk.evidence.provenance import Provenanced
from copilot_sdk.scoring.fingerprint import FingerprintResult, compute_fingerprint
from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.scoring.trajectory import TrajectoryResult, compute_trajectory
from copilot_sdk.evolution.protocol import EvolutionStore
from copilot_sdk.graph.protocol import GraphStore, ProtocolV2GraphStore
from copilot_sdk.graph.dual_write_store import DualWriteStore
from copilot_sdk.scoring.persistence_outbox import PersistenceOutbox
from copilot_sdk.stats.bootstrap import block_bootstrap_mean_se


def _ensure_gae_path() -> Path:
    workspace = Path(__file__).resolve().parents[3]
    default_gae_path = workspace / "graph-attention-engine-v50"
    gae_path = Path(os.environ.get("CLAUDE_GAE", str(default_gae_path)))
    if gae_path.exists() and str(gae_path) not in sys.path:
        sys.path.insert(0, str(gae_path))
    return gae_path


_ensure_gae_path()

from gae.dk_estimator import CoordinateDescentEstimator  # noqa: E402
from gae.calibration import compute_theta_min  # noqa: E402
from gae.profile_scorer import (  # noqa: E402
    DecisionCountPolicy,
    FixedAlpha,
    LearningStrategy,
    ProfileScorer,
)

logger = logging.getLogger(__name__)

# JM §6's canonical coverage query counts categories with at least one
# verified decision; keep that threshold explicit rather than conflating it
# with the analyst override rate.
CONSERVATION_CATEGORY_MIN_VERIFIED = 1
# Conservation is not meaningful until a small verified sample exists.  Keep
# the first nine verified outcomes in an explicit calibration warm-up; mature
# domains still use the full alpha*q gate from the tenth outcome onward.
CONSERVATION_MIN_VERIFIED = 10
REGIME_CALIBRATION_THRESHOLD = 10

# JM canonical checkpoint IKS: centroid drift from the domain bootstrap prior.
# The scorer's composite learning-health metric remains available through
# ``_compute_iks``; checkpoint history uses this separate canonical value.
CANONICAL_IKS_D_MAX = 0.20
QUALITY_WINDOW_SIZE = 400
QUALITY_POLICY_VERSION = "quality.v1"


def _factor_names_hash(factor_names: list[str]) -> str:
    return hashlib.sha256(
        json.dumps(list(factor_names), separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _resolve_governed_writes(governed_writes: bool | None) -> bool:
    """Resolve the construction-time governed-write feature gate.

    ``None`` means use the process default; an explicit ``False`` always
    overrides ``SCORER_GOVERNED_WRITES``.  This keeps the legacy raw-write
    path available for callers that need to opt out during rollout.
    """
    if governed_writes is not None:
        return bool(governed_writes)
    return os.environ.get("SCORER_GOVERNED_WRITES", "").strip() == "1"


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
        # The preset bootstrap is the immutable canonical prior.  Persisting
        # this separately from the live scorer state makes convergence metrics
        # comparable after a restart or checkpoint restore.
        self._canonical_mu = np.array(preset.bootstrap_centroids, dtype=np.float64, copy=True)
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
        governed_store = isinstance(graph_store, ProtocolV2GraphStore) or (
            isinstance(graph_store, DualWriteStore)
            and isinstance(graph_store.primary, ProtocolV2GraphStore)
            and isinstance(graph_store.secondary, ProtocolV2GraphStore)
        )
        if self._governed_writes and not governed_store:
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
        self._verified_decisions_cache: list[dict[str, Any]] | None = None
        self._fingerprint_cache: FingerprintResult | None = None
        self._calibration_overlay: dict[str, Any] | None = None
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

    def compute_centroid_distance_to_canonical(self) -> float | None:
        """Return the raw Frobenius distance from current to canonical centroids."""
        canonical = getattr(self, "_canonical_mu", None)
        if canonical is None:
            return None
        current = np.asarray(self._scorer.centroids, dtype=np.float64)
        canonical_array = np.asarray(canonical, dtype=np.float64)
        if current.shape != canonical_array.shape:
            return None
        from gae.convergence import centroid_distance_to_canonical

        return float(centroid_distance_to_canonical(current, canonical_array))

    def compute_epsilon_firm(self) -> dict[str, Any] | None:
        """Return normalized canonical distance and the gamma>1 threshold."""
        distance = self.compute_centroid_distance_to_canonical()
        if distance is None:
            return None
        tensor_cells = int(np.asarray(self._scorer.centroids).size)
        normalized = distance / max(float(tensor_cells) ** 0.5, 1.0)
        return {
            "epsilon_firm": float(normalized),
            "raw_distance": float(distance),
            "threshold": 0.128,
            "clears_threshold": bool(normalized > 0.128),
            "tensor_cells": tensor_cells,
        }

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

            graph_store = cast(
                GraphStore,
                SQLiteGraphStore(db_path, domain=preset.name),
            )
        assert graph_store is not None
        if profile == "production":
            from copilot_sdk.graph.memory_store import InMemoryGraphStore
            from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
            from copilot_sdk.graph.dual_write_store import DualWriteStore

            if isinstance(graph_store, (SQLiteGraphStore, InMemoryGraphStore)):
                raise RuntimeError(
                    "Production scorer requires an AGE-backed GraphStore; "
                    "SQLite and InMemoryGraphStore are test/development stores."
                )
            if isinstance(graph_store, DualWriteStore) and isinstance(
                cast(DualWriteStore, graph_store).primary,
                (SQLiteGraphStore, InMemoryGraphStore),
            ):
                raise RuntimeError(
                    "Production scorer requires AGE to be the primary GraphStore; "
                    "dual-write stores with a SQLite or in-memory primary are "
                    "test/migration stores."
                )
        centroids = graph_store.load_latest_centroids(preset.name)
        latest_checkpoints = graph_store.get_centroid_checkpoints(
            preset.name,
            include_v2=True,
            limit=1,
        )
        if latest_checkpoints:
            stored_hash = latest_checkpoints[-1].get("factor_names_hash")
            current_hash = _factor_names_hash(list(preset.shape.factor_names))
            if stored_hash and stored_hash != current_hash:
                logger.warning(
                    "Factor schema changed for %s: stored=%s current=%s. "
                    "Falling back to bootstrap centroids.",
                    preset.name,
                    str(stored_hash)[:8],
                    current_hash[:8],
                )
                centroids = None
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
            decision_payload: dict[str, Any] = {
                "decision_id": decision_id,
                "domain": self._domain,
                "category": category,
                "category_index": category_index,
                "recommended_action": action,
                "recommended_index": action_index,
                "confidence": float(gae_result.confidence),
                "probabilities": probabilities,
                "factor_vector": factor_vector.tolist(),
                "factor_names": list(self._preset.shape.factor_names),
                "source": "compounding_scorer",
                "scorer_version": "copilot_sdk.compounding_scorer.v1",
                "preset_version": f"{self._preset.name}.v1",
                "factor_schema_version": f"{self._preset.name}.factor_schema.v1",
                "metadata": decision_metadata,
                "_governed": True,
            }
            try:
                governed_store.write_governed_decision(
                    **{key: value for key, value in decision_payload.items() if key != "_governed"}
                )
            except Exception as exc:
                self._record_persistence_failure(decision_id, "decision", decision_payload, exc)
        else:
            decision_payload = {
                "decision_id": decision_id,
                "domain": self._domain,
                "category": category,
                "action": action,
                "confidence": float(gae_result.confidence),
                "factors": factor_values,
                "metadata": decision_metadata,
            }
            try:
                stored_id = self._graph_store.write_decision(
                    **{
                        key: value
                        for key, value in decision_payload.items()
                        if key != "decision_id"
                    }
                )
            except Exception as exc:
                self._record_persistence_failure(decision_id, "decision", decision_payload, exc)
            else:
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

    def score_with_centroids(
        self,
        centroids: np.ndarray,
        factors: dict[str, float],
        category: str,
    ) -> ScoreResult:
        """Score with alternate centroids and the live kernel and temperature.

        This is a centroid ablation, not a point-in-time replay.  The live
        scorer is never assigned to, learned from, or persisted by this path.
        """
        return self.score_with_model_state(
            centroids,
            factors,
            category,
            dk_weights=self.get_dk_weights(),
            temperature=self.get_temperature(),
        )

    def score_with_model_state(
        self,
        centroids: np.ndarray,
        factors: dict[str, float],
        category: str,
        *,
        dk_weights: list[list[float]] | None = None,
        temperature: float | None = None,
    ) -> ScoreResult:
        """Score without mutation using an historical centroid model state."""
        (
            category_index,
            factor_values,
            factor_vector,
            _gae_result,
            _action_index,
            _action,
            _probabilities,
        ) = self._predict(factors, category)

        live = self._scorer
        temporary = ProfileScorer(
            mu=np.asarray(centroids, dtype=np.float64).copy(),
            actions=list(self._preset.shape.action_names),
            categories=list(self._preset.shape.category_names),
            kernel=getattr(live, "kernel", None),
            factor_mask=(
                None
                if getattr(live, "factor_mask", None) is None
                else np.asarray(live.factor_mask, dtype=np.float64).copy()
            ),
            scoring_kernel=getattr(live, "scoring_kernel", None),
            eta_override=0.0,
        )
        if dk_weights is not None:
            weights = np.asarray(dk_weights, dtype=np.float64)
            expected = (
                self._preset.shape.n_categories,
                self._preset.shape.n_factors,
            )
            if weights.shape != expected or not np.all(np.isfinite(weights)):
                raise ValueError(f"DK weight shape/value mismatch: {weights.shape} != {expected}")
            temporary._dk_weights = weights.copy()
        temporary.tau = float(live.tau if temperature is None else temperature)

        result = temporary.score(factor_vector, category_index)
        return ScoreResult(
            decision_id=f"cf-{uuid.uuid4().hex[:12]}",
            action=str(result.action_name),
            action_index=int(result.action_index),
            confidence=float(result.confidence),
            probabilities=[float(value) for value in result.probabilities],
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

    def get_temperature(self) -> float:
        """Return the active scorer temperature τ."""
        return float(getattr(self._scorer, "tau", self._preset.temperature))

    def _checkpoint_dk_weights(self) -> list[list[float]]:
        """Return the explicit DK tensor used by a checkpoint replay.

        Before variance learning initializes DK, the scorer uses isotropic
        unit weights. Persisting that effective tensor makes the checkpoint
        replayable without claiming that learned DK weights existed.
        """
        weights = self.get_dk_weights()
        if weights is not None:
            return weights
        return cast(list[list[float]], np.ones(
            (self._preset.shape.n_categories, self._preset.shape.n_factors),
            dtype=np.float64,
        ).tolist())

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

    def get_conservation_state(self) -> dict[str, Any]:
        """Return the complete explainable conservation-panel payload.

        The evolution gate consumes the smaller internal state returned by
        ``_evolution_conservation_state``.  The status panel needs the
        additional derived metrics and explanation supplied by the shared
        backend payload builder.
        """

        from copilot_sdk.backend.conservation_utils import (
            compute_conservation_status_payload,
        )

        payload = cast(dict[str, Any], compute_conservation_status_payload(self._domain, self))
        overlay = self._calibration_overlay
        if overlay is None:
            return payload
        actual_v = self.get_verified_count()
        new_verified = max(0, actual_v - int(overlay["actual_V"]))
        overlay["new_regime_verified"] = new_verified
        if new_verified >= int(overlay["threshold"]):
            self._calibration_overlay = None
            return payload
        effective_v = min(
            actual_v,
            int(overlay["effective_V_base"]) + new_verified,
        )
        alpha = float(payload.get("alpha") or 0.0)
        q = float(payload.get("q") or 0.0)
        theta_min = compute_theta_min(alpha, effective_v)
        signal = alpha * q * effective_v
        payload.update(
            {
                "status": "CALIBRATING",
                "phase": "CALIBRATING",
                "actual_V": actual_v,
                "effective_V": effective_v,
                "signal": signal,
                "theta_min": theta_min,
                "headroom": signal - theta_min if theta_min is not None else None,
                "calibration": dict(overlay),
                "reason": (
                    f"Regime {overlay['regime_tag']} is calibrating: "
                    f"{new_verified}/{overlay['threshold']} new verified decisions."
                ),
            }
        )
        return payload

    def reinitialize_from_regime(
        self,
        regime_tag: str,
        strategy: str = "A",
        blend_weight: float = 0.5,
        v_discount: float = 0.5,
    ) -> dict[str, Any]:
        """Atomically restore a prior regime model with calibration evidence."""
        strategy = str(strategy).upper()
        if strategy not in {"A", "B", "C"}:
            return {"success": False, "reason": f"unknown_strategy_{strategy}"}
        if not 0.0 <= float(blend_weight) <= 1.0:
            return {"success": False, "reason": "invalid_blend_weight"}
        if not 0.0 <= float(v_discount) <= 1.0:
            return {"success": False, "reason": "invalid_v_discount"}

        loader = getattr(self._graph_store, "load_latest_checkpoint_for_regime", None)
        checkpoint = loader(self._domain, regime_tag) if callable(loader) else None
        if checkpoint is None:
            checkpoints = self._graph_store.get_centroid_checkpoints(
                self._domain, include_v2=True, limit=None
            )
            matching = [
                item for item in checkpoints
                if str((item.get("metadata") or {}).get("regime_tag") or "")
                == str(regime_tag)
            ]
            checkpoint = max(
                enumerate(matching),
                key=lambda item: (
                    float(
                        item[1].get(
                            "created_at_epoch", item[1].get("created_at", 0.0)
                        )
                        or 0.0
                    ),
                    item[0],
                ),
                default=None,
            )
            checkpoint = None if checkpoint is None else checkpoint[1]
        if checkpoint is None:
            return {"success": False, "reason": "no_checkpoint_for_regime"}

        raw_centroids = checkpoint.get("centroids")
        restored = np.asarray(raw_centroids, dtype=np.float64)
        current = np.asarray(self._scorer.centroids, dtype=np.float64)
        if restored.shape != current.shape or not np.all(np.isfinite(restored)):
            return {"success": False, "reason": "checkpoint_centroid_shape_or_value_invalid"}

        old_centroids = current.copy()
        old_dk = getattr(self._scorer, "_dk_weights", None)
        old_dk = None if old_dk is None else np.asarray(old_dk, dtype=np.float64).copy()
        old_tau = self.get_temperature()
        old_overlay = None if self._calibration_overlay is None else dict(self._calibration_overlay)
        prior_v = int(checkpoint.get("verified_count") or checkpoint.get("decisions_count") or 0)
        actual_v = self.get_verified_count()
        effective_base = min(actual_v, max(0, int(float(v_discount) * prior_v)))
        fallback_reason: str | None = None

        def apply_state(_transaction: Any = None) -> None:
            nonlocal fallback_reason
            if strategy in {"A", "C"}:
                next_centroids = restored.copy()
            else:
                next_centroids = (
                    float(blend_weight) * restored
                    + (1.0 - float(blend_weight)) * current
                )
            self._scorer.centroids = next_centroids
            if strategy == "C":
                metadata = checkpoint.get("metadata") or {}
                dk = metadata.get("dk_weights", checkpoint.get("dk_weights"))
                tau = metadata.get("temperature", checkpoint.get("temperature"))
                if dk is None or tau is None:
                    fallback_reason = "legacy_checkpoint_missing_model_state"
                else:
                    self.load_dk_weights_from_l5(dk)
                    self._scorer.tau = float(tau)
            self._calibration_overlay = {
                "phase": "CALIBRATING",
                "regime_tag": str(regime_tag),
                "strategy": strategy,
                "reset_at": time.time(),
                "actual_V": actual_v,
                "effective_V_base": effective_base,
                "effective_V": effective_base,
                "discount": float(v_discount),
                "prior_regime_V": prior_v,
                "new_regime_verified": 0,
                "threshold": REGIME_CALIBRATION_THRESHOLD,
            }

        try:
            transaction_runner = getattr(self._graph_store, "run_transaction", None)
            if callable(transaction_runner):
                result = transaction_runner(apply_state)
                if inspect.isawaitable(result):
                    asyncio.run(cast(Coroutine[Any, Any, Any], result))
            else:
                apply_state()
            event_writer = getattr(self._graph_store, "save_evolution_event", None)
            if callable(event_writer):
                event_writer(
                    self._domain,
                    event_type="regime_reinitialize",
                    rule_name="",
                    variant_id="",
                    metadata={
                        "regime_tag": str(regime_tag),
                        "strategy": strategy,
                        "checkpoint_id": checkpoint.get("checkpoint_id"),
                        "fallback_reason": fallback_reason,
                        "effective_V": effective_base,
                    },
                )
        except Exception:
            self._scorer.centroids = old_centroids
            if old_dk is None:
                if hasattr(self._scorer, "_dk_weights"):
                    self._scorer._dk_weights = None
            else:
                self._scorer._dk_weights = old_dk
            self._scorer.tau = old_tau
            self._calibration_overlay = old_overlay
            raise
        return {
            "success": True,
            "strategy": strategy,
            "regime_tag": str(regime_tag),
            "checkpoint_id": checkpoint.get("checkpoint_id"),
            "fallback_reason": fallback_reason,
            "calibration": dict(self._calibration_overlay or {}),
        }

    def domain_scoped_reset(self) -> None:
        """Reset this scorer's domain and discard pending persistence replays."""
        reset = getattr(self._graph_store, "domain_scoped_reset", None)
        if not callable(reset):
            raise AttributeError("graph store does not support domain_scoped_reset")
        reset(self._domain)
        self._verified_decisions_cache = None
        self._fingerprint_cache = None
        if self._outbox is not None:
            self._outbox.clear()

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
        regime_tag = _decision_regime_tag(decision)
        assert actual_action in self._preset.shape.action_names, f"unknown action: {actual_action}"

        actual_index = self._preset.shape.action_names.index(actual_action)
        predicted_index = int(_decision_field(decision, "recommended_index", 0))
        recommended_action = str(_decision_field(decision, "recommended_action", _decision_field(decision, "action", "")))
        is_correct = actual_action == recommended_action
        factor_vector = np.asarray(_decision_field(decision, "factor_vector", []), dtype=np.float64)
        category_index = int(_decision_field(decision, "category_index", 0))
        confidence = float(_decision_field(decision, "confidence", 0.0))
        if context and (context.get("benchmark") is True or context.get("preseed") is True):
            # Synthetic benchmark/preseed runs do not represent live judgments.
            # Avoid recomputing the full verified-history fingerprint on every
            # synthetic learn; production conflict detection remains unchanged.
            self._last_conflict = None
        else:
            self._detect_judgment_conflict(
                decision_id=decision_id,
                decision=decision,
                predicted_index=predicted_index,
                actual_correct=is_correct,
                factor_vector=factor_vector,
                confidence=confidence,
            )

        synthetic_preseed = bool(context and context.get("preseed") is True)
        conservation_pause = None if synthetic_preseed else self._conservation_pause()
        if conservation_pause is not None:
            conservation_pause["decision_id"] = decision_id
            if persist_artifacts:
                try:
                    self._persist_conservation_snapshot(
                        decision_id,
                        V=int(conservation_pause["verified_count"]),
                        q=float(conservation_pause["q"]),
                        alpha=float(conservation_pause["alpha"]),
                        theta_min=float(conservation_pause["theta_min"]),
                        status="RED",
                        )
                except Exception as exc:
                    # The snapshot helper isolates normal persistence errors;
                    # retain a final guard so a pause response is never blocked.
                    logger.warning(
                        "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",
                        self._domain,
                        decision_id,
                        "conservation",
                        type(exc).__name__,
                        exc,
                    )
                try:
                    centroids = np.asarray(self._scorer.centroids, dtype=np.float64)
                    if centroids.size and np.any(np.isfinite(centroids)):
                        pause_category = str(_decision_field(decision, "category", ""))
                        pause_action = str(
                            _decision_field(
                                decision,
                                "recommended_action",
                                _decision_field(decision, "action", ""),
                            )
                        )
                        self._save_centroids_checkpoint(
                            decision_id=decision_id,
                            category=pause_category,
                            action=pause_action,
                            iks=self._compute_iks(persist_artifacts=False),
                            boundary="conservation_pause",
                            decisions_in_batch=int(conservation_pause["verified_count"]),
                            regime_tag=regime_tag,
                        )
                except Exception as exc:
                    logger.warning(
                        "Paused conservation checkpoint failed: domain=%s decision=%s error=%s",
                        self._domain,
                        decision_id,
                        exc,
                    )
                if persist_artifacts:
                    try:
                        paused_fingerprint = self.fingerprint(persist=False)
                        if paused_fingerprint.decisions_analyzed >= 5:
                            self._persist_fingerprint(
                                paused_fingerprint,
                                decision_id=decision_id,
                            )
                    except Exception as exc:
                        logger.warning(
                            "Paused conservation fingerprint failed: domain=%s decision=%s error=%s",
                            self._domain,
                            decision_id,
                            exc,
                        )
            return conservation_pause
        iks_before = self._compute_iks(
            persist_artifacts=False,
            skip_history_scan=synthetic_preseed,
        )
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
        self._verified_decisions_cache = None
        self._fingerprint_cache = None
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
            skip_history_scan=synthetic_preseed,
        )
        self._last_checkpoint_decision_id = decision_id
        self._last_checkpoint_category = category
        self._last_checkpoint_action = actual_action
        self._last_checkpoint_iks = iks_after
        decision_timestamp = self._extract_decision_timestamp(decision)
        self._update_batch_decision_time_range(decision_timestamp)
        checkpoint_already_persisted = False
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
                        regime_tag=regime_tag,
                    )
                    checkpoint_already_persisted = True
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
                    regime_tag=regime_tag,
                )
                checkpoint_already_persisted = True
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
                checkpoint_already_persisted=checkpoint_already_persisted,
                skip_history_scan=synthetic_preseed,
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
        if self._fingerprint_cache is None:
            self._fingerprint_cache = compute_fingerprint(
                self._verified_decisions(),
                list(self._preset.shape.factor_names),
            )
        result = self._fingerprint_cache
        if persist:
            self._persist_fingerprint(result, decision_id=decision_id)
        return result

    def _record_persistence_failure(
        self,
        decision_id: str,
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

    def _persist_conservation_snapshot(
        self,
        decision_id: str,
        *,
        V: int | None = None,
        q: float | None = None,
        alpha: float | None = None,
        theta_min: float | None = None,
        status: str | None = None,
        policy_version: str = "conservation.v1",
        status_id: str | None = None,
    ) -> bool:
        """Persist the current conservation state independently of learning."""
        if not isinstance(self._graph_store, ProtocolV2GraphStore):
            return False

        conservation_payload: dict[str, Any] = {}
        try:
            if any(value is None for value in (V, q, alpha, theta_min, status)):
                from copilot_sdk.backend.conservation_utils import compute_conservation_metrics

                metrics = compute_conservation_metrics(self, domain=self._domain)
                V = int(metrics["V"])
                q = float(metrics["q"])
                alpha = float(metrics["alpha"])
                theta_min = float(metrics["theta_min"])
                status = str(metrics["status"])

            assert V is not None
            assert q is not None
            assert alpha is not None
            assert theta_min is not None
            assert status is not None
            if not math.isfinite(float(theta_min)):
                logger.warning(
                    "Cold start: theta_min=%s, skipping conservation snapshot",
                    theta_min,
                )
                return False

            conservation_payload = {
                "status_id": status_id or f"{self._domain}:conservation:{decision_id}",
                "domain": self._domain,
                "V": int(V),
                "q": float(q),
                "alpha": float(alpha),
                "theta_min": float(theta_min),
                "verified_count": int(V),
                "correct_count": int(round(float(q) * int(V))),
                "status": str(status),
                "policy_version": policy_version,
            }
            self._graph_store.write_conservation_status(
                status_id=str(conservation_payload["status_id"]),
                domain=str(conservation_payload["domain"]),
                V=int(conservation_payload["V"]),
                q=float(conservation_payload["q"]),
                alpha=float(conservation_payload["alpha"]),
                theta_min=float(conservation_payload["theta_min"]),
                verified_count=int(conservation_payload["verified_count"]),
                correct_count=int(conservation_payload["correct_count"]),
                status=str(conservation_payload["status"]),
                policy_version=str(conservation_payload["policy_version"]),
            )
            return True
        except Exception as exc:
            logger.warning(
                "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",
                self._domain,
                decision_id,
                "conservation",
                type(exc).__name__,
                exc,
            )
            self._record_persistence_failure(decision_id, "conservation", conservation_payload, exc)
            return False

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
        skip_history_scan: bool = False,
        transaction: Any | None = None,
        raise_on_error: bool = False,
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

        self._persist_conservation_snapshot(decision_id)

        if not skip_history_scan:
            try:
                fingerprint = self.fingerprint(persist=False)
                self._persist_fingerprint(fingerprint, decision_id=decision_id)
            except Exception as exc:
                logger.warning(
                    "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",
                    self._domain, decision_id, "fingerprint", type(exc).__name__, exc,
                )
                self._record_persistence_failure(decision_id, "fingerprint", {}, exc)

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
                self._record_persistence_failure(decision_id, "evidence_receipt", {}, exc)

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
                    regime_tag=_decision_regime_tag(row),
                    write_legacy=False,
                    transaction=transaction,
                    raise_on_error=raise_on_error,
                )
            except Exception as exc:
                if raise_on_error:
                    raise
                logger.warning(
                    "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",
                    self._domain, decision_id, "centroid_checkpoint", type(exc).__name__, exc,
                )
                self._record_persistence_failure(decision_id, "centroid_checkpoint", {}, exc)

    def capture_existing_state(
        self,
        *,
        capture_reason: str,
        decision_id: str | None = None,
    ) -> dict[str, Any]:
        """Capture Type A state artifacts without recording a learning event."""
        # Phase E reseed-ledger processing must treat this snapshot as the
        # current V observation, not as a new reseed or learning event.
        result: dict[str, Any] = {
            "conservation": 0,
            "fingerprint": 0,
            "checkpoint": 0,
            "errors": [],
        }
        if not isinstance(self._graph_store, ProtocolV2GraphStore):
            return result

        capture_key = decision_id or f"capture:{capture_reason}"
        errors = result["errors"]

        try:
            conservation = self._capture_conservation_state()
            if conservation is not None:
                canonical = json.dumps(
                    {
                        "domain": self._domain,
                        "V": conservation["V"],
                        "q": conservation["q"],
                        "alpha": conservation["alpha"],
                        "theta_min": conservation["theta_min"],
                        "status": conservation["status"],
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                status_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]
                result["conservation"] = int(
                    self._persist_conservation_snapshot(
                        capture_key,
                        V=int(conservation["V"]),
                        q=float(conservation["q"]),
                        alpha=float(conservation["alpha"]),
                        theta_min=float(conservation["theta_min"]),
                        status=str(conservation["status"]),
                        status_id=f"{self._domain}:conservation:{status_digest}",
                    )
                )
        except Exception as exc:
            errors.append(f"conservation: {type(exc).__name__}: {exc}")
            logger.warning("State capture conservation failed for %s: %s", self._domain, exc)

        try:
            fingerprint = self.fingerprint(persist=False)
            if fingerprint.decisions_analyzed >= 5:
                result["fingerprint"] = int(
                    self._persist_fingerprint(fingerprint, decision_id=capture_key)
                )
        except Exception as exc:
            errors.append(f"fingerprint: {type(exc).__name__}: {exc}")
            logger.warning("State capture fingerprint failed for %s: %s", self._domain, exc)

        try:
            centroids = np.asarray(self._scorer.centroids, dtype=np.float64)
            finite_nonzero = np.isfinite(centroids) & (centroids != 0.0)
            if centroids.size and np.any(finite_nonzero):
                verified = int(self._graph_store.count_verified(self._domain))
                centroid_digest = hashlib.sha256(centroids.tobytes()).hexdigest()[:32]
                checkpoint_digest = hashlib.sha256(
                    f"{self._domain}|{capture_reason}|{centroid_digest}|{verified}".encode("utf-8")
                ).hexdigest()[:32]
                checkpoint_id = f"{self._domain}:checkpoint:{checkpoint_digest}"
                existing_checkpoints = self._graph_store.get_centroid_checkpoints(
                    self._domain,
                    include_v2=True,
                    limit=1000,
                )
                if any(
                    str(checkpoint.get("checkpoint_id")) == checkpoint_id
                    for checkpoint in existing_checkpoints
                ):
                    logger.info("Startup checkpoint already exists, skipping: %s", checkpoint_id)
                else:
                    result["checkpoint"] = int(
                        self._save_centroids_checkpoint(
                            decision_id=capture_key,
                            category=self._preset.shape.category_names[0],
                            action=self._preset.shape.action_names[0],
                            iks=self._compute_iks(persist_artifacts=False),
                            boundary=capture_reason,
                            decisions_in_batch=verified,
                            write_legacy=False,
                            checkpoint_id=checkpoint_id,
                            capture_reason=capture_reason,
                        )
                    )
        except Exception as exc:
            errors.append(f"checkpoint: {type(exc).__name__}: {exc}")
            logger.warning("State capture checkpoint failed for %s: %s", self._domain, exc)

        return result

    def _capture_conservation_state(self) -> dict[str, float | int | str] | None:
        if not self._domain:
            logger.debug("Skipping conservation capture: domain not set")
            return None
        paused = self._conservation_pause()
        if paused is not None:
            return {
                "V": int(paused["verified_count"]),
                "q": float(paused["q"]),
                "alpha": float(paused["alpha"]),
                "theta_min": float(paused["theta_min"]),
                "status": str(paused.get("conservation_status", "RED")),
            }

        verified, correct, _override_rate = _conservation_stats(self._graph_store)
        if verified <= 0:
            return None
        alpha = self._category_coverage()
        q = correct / verified
        if verified < CONSERVATION_MIN_VERIFIED or alpha <= 0.0:
            theta_min = compute_theta_min(1.0, verified)
            status = "CALIBRATING"
        else:
            theta_min = compute_theta_min(alpha, verified)
            signal = alpha * q * verified
            status = "GREEN" if theta_min is not None and signal >= theta_min else "RED"
        if theta_min is None or not math.isfinite(float(theta_min)):
            return None
        return {
            "V": int(verified),
            "q": float(q),
            "alpha": float(alpha),
            "theta_min": float(theta_min),
            "status": status,
        }

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
    ) -> bool:
        if not isinstance(self._graph_store, ProtocolV2GraphStore):
            return False
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
            return True
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
            return False
        self._last_persisted_fingerprint_signature = signature
        return True

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
            regime_tag=_decision_regime_tag(
                self._graph_store.get_decision(
                    self._last_checkpoint_decision_id,
                    domain=self._domain,
                ) or {}
            ),
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
        # Trajectory is derived solely from verified decisions. The legacy
        # checkpoint filter arguments remain accepted for API compatibility;
        # compute_trajectory has always ignored checkpoints and these filters.
        return compute_trajectory(
            [],
            self._graph_store.get_verified_decisions(self._domain),
            self._preset.shape,
        )

    def rollback_to_checkpoint(self, checkpoint_id: str) -> dict[str, Any]:
        """Restore centroids to a V2 checkpoint targeted by SNAPSHOT_AFTER."""
        checkpoints = self._graph_store.get_centroid_checkpoints(
            self._domain,
            limit=None,
            include_v2=True,
        )
        checkpoint = next(
            (
                item for item in checkpoints
                if str(item.get("checkpoint_id") or "") == str(checkpoint_id)
            ),
            None,
        )
        if checkpoint is None:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        lineage = self._graph_store.get_checkpoint_lineage(self._domain, checkpoint_id)
        if lineage is None:
            raise ValueError(f"Checkpoint {checkpoint_id} has no SNAPSHOT_AFTER lineage")

        raw_centroids = checkpoint.get("centroids")
        restored = np.asarray(raw_centroids, dtype=np.float64)
        current = np.asarray(self._scorer.centroids)
        if restored.shape != current.shape:
            raise ValueError(
                f"Checkpoint {checkpoint_id} shape {restored.shape} does not match current {current.shape}"
            )
        self._scorer.centroids = np.array(restored, dtype=np.float64, copy=True)
        metadata = checkpoint.get("metadata") or {}
        dk_weights = metadata.get("dk_weights", checkpoint.get("dk_weights"))
        temperature = metadata.get("temperature", checkpoint.get("temperature"))
        if dk_weights is not None:
            self.load_dk_weights_from_l5(dk_weights)
        if temperature is not None:
            restored_temperature = float(temperature)
            if not np.isfinite(restored_temperature) or restored_temperature <= 0:
                raise ValueError(f"Checkpoint {checkpoint_id} has invalid temperature")
            self._scorer.tau = restored_temperature
        restored_decision_count = metadata.get(
            "decision_count", checkpoint.get("decision_count")
        )
        if restored_decision_count is not None and hasattr(self._scorer, "decision_count"):
            self._scorer.decision_count = int(restored_decision_count)
        restored_frozen = metadata.get("frozen", checkpoint.get("frozen"))
        if restored_frozen is not None:
            if bool(restored_frozen):
                self._scorer.freeze()
            else:
                self._scorer.unfreeze()
        restored_paused = metadata.get(
            "paused_by_conservation", checkpoint.get("paused_by_conservation")
        )
        if restored_paused is not None and hasattr(
            self._scorer, "_paused_by_conservation"
        ):
            self._scorer._paused_by_conservation = bool(restored_paused)
        self._verified_decisions_cache = None

        current_count = self.get_verified_count()
        checkpoint_count = int(checkpoint.get("verified_count") or checkpoint.get("decisions_count") or 0)
        decisions_undone = max(0, current_count - checkpoint_count)
        lineage_decision_id = str(
            lineage.get("decision_id")
            or lineage.get("metadata", {}).get("decision_id")
            or checkpoint.get("decision_id")
            or ""
        )
        event_writer = getattr(self._graph_store, "save_evolution_event", None)
        if callable(event_writer):
            event_writer(
                self._domain,
                event_type="decision_rollback",
                metadata={
                    "checkpoint_id": str(checkpoint_id),
                    "edge_type": "SNAPSHOT_AFTER",
                    "lineage_decision_id": lineage_decision_id,
                    "decisions_undone": decisions_undone,
                },
            )
        return {
            "rolled_back": True,
            "checkpoint_id": str(checkpoint_id),
            "lineage_decision_id": lineage_decision_id,
            "decisions_undone": decisions_undone,
            "restored_iks": checkpoint.get("iks"),
        }

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
        existing = self._graph_store.get_centroid_checkpoints(
            self._domain,
            limit=None,
            include_v2=True,
        )
        if any(record.get("category") != "warm_start" for record in existing):
            logger.info(
                "warm_start skipped: learned checkpoint exists for %s",
                self._domain,
            )
            return {
                "applied": 0,
                "score": 0.0,
                "skipped": True,
                "reason": "learned_checkpoint_exists",
            }

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
            emitted = 0
            skipped = 0
            emission_errors = 0
            source_copilots = sorted(
                {
                    str(getattr(pattern, "source_copilot", ""))
                    for pattern in applied_transfer_patterns
                    if str(getattr(pattern, "source_copilot", ""))
                }
            )
            if isinstance(self._graph_store, ProtocolV2GraphStore):
                current_conservation_status = "unavailable"
                try:
                    statuses = self._graph_store.get_latest_conservation_statuses(
                        domains=[self._domain]
                    )
                    if statuses and statuses[0].get("status"):
                        current_conservation_status = str(statuses[0]["status"])
                except Exception as exc:
                    logger.warning(
                        "Warm-start conservation lookup failed: domain=%s error=%s: %s",
                        self._domain,
                        type(exc).__name__,
                        exc,
                    )

                for pattern in applied_transfer_patterns:
                    metadata = getattr(pattern, "metadata", {})
                    metadata = dict(metadata) if isinstance(metadata, dict) else {}
                    source_domain = str(
                        metadata.get("source_domain")
                        or getattr(pattern, "source_copilot", "")
                    ).strip()
                    source_fingerprint_id = metadata.get("source_fingerprint_id")
                    if not source_fingerprint_id:
                        skipped += 1
                        continue
                    factor_mapping = metadata.get("factor_mapping", {})
                    if not isinstance(factor_mapping, dict):
                        factor_mapping = {}
                    canonical_mapping = json.dumps(
                        factor_mapping,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    hash_input = (
                        f"{source_domain}|{self._domain}|factor_quality_transfer|"
                        f"{source_fingerprint_id}||{canonical_mapping}"
                    )
                    pattern_id = (
                        "TP-"
                        + hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:32]
                    )
                    try:
                        self._graph_store.write_transfer_pattern(
                            pattern_id=pattern_id,
                            source_domain=source_domain,
                            target_domain=self._domain,
                            pattern_type="factor_quality_transfer",
                            factor_mapping=factor_mapping,
                            confidence=float(getattr(pattern, "confidence", 0.0)),
                            validation_status=("validated" if factor_mapping else "partial"),
                            conservation_status=current_conservation_status,
                            source_rule=None,
                            target_rule=None,
                            source_fingerprint_id=str(source_fingerprint_id),
                            evolution_event_id=None,
                        )
                        emitted += 1
                    except Exception as exc:
                        logger.warning(
                            "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",
                            self._domain,
                            "warm_start",
                            "transfer_pattern",
                            type(exc).__name__,
                            exc,
                        )
                        emission_errors += 1
            else:
                skipped = applied
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
            emitted = 0
            skipped = 0
            emission_errors = 0

        return {
            "applied": applied,
            "score": score,
            "source_copilots": source_copilots,
            "emitted": emitted,
            "skipped": skipped,
            "emission_errors": emission_errors,
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
        skip_history_scan: bool = False,
    ) -> float:
        try:
            verified_decisions = self._verified_decisions()
            verified = len(verified_decisions)
        except Exception:
            verified = self._graph_store.count_verified(self._domain)
        if verified == 0:
            return 0.0

        try:
            correct = sum(1 for decision in verified_decisions if _is_correct_decision(decision))
        except Exception:
            correct = self._graph_store.count_correct(self._domain)
        accuracy = correct / verified
        if skip_history_scan:
            fingerprint_component = 0.0
            coverage = 0.0
        else:
            fingerprint = self.fingerprint(
                persist=False,
                decision_id=decision_id,
            )
            mean_sigma = (
                sum(factor.sigma for factor in fingerprint.factors) / len(fingerprint.factors)
                if fingerprint.factors
                else 0.5
            )
            fingerprint_component = max(0.0, min((1.0 - mean_sigma / 0.5) * 25.0, 25.0))
            coverage = _count_categories_with_n(
                self._conservation_verified_decisions(),
                10,
            ) / self._preset.shape.n_categories

        iks = (
            min(verified / 500.0, 1.0) * 25.0
            + accuracy * 25.0
            + fingerprint_component
            + coverage * 25.0
        )
        return round(iks, 1)

    def _compute_checkpoint_iks(self) -> float:
        """Return the JM canonical centroid-drift IKS for checkpoint history."""
        from copilot_sdk.framework.iks_base import compute_iks

        result = compute_iks(
            np.asarray(self._scorer.centroids, dtype=np.float64),
            np.asarray(self._preset.bootstrap_centroids, dtype=np.float64),
            CANONICAL_IKS_D_MAX,
        )
        return float(result["current"])

    def _checkpoint_quality(self, decision_time_end: str | None) -> dict[str, Any]:
        """Compute the explicit rolling accuracy contract for a new checkpoint."""
        recent_reader = getattr(self._graph_store, "get_recent_verified_decisions", None)
        if callable(recent_reader):
            window = list(recent_reader(self._domain, QUALITY_WINDOW_SIZE))
        else:
            verified = self._graph_store.get_verified_decisions(self._domain)
            window = verified[-QUALITY_WINDOW_SIZE:]
        verified_count = len(window)
        correct_count = sum(
            1
            for decision in window
            if decision.get("is_correct") is True or decision.get("correct") is True
        )
        window_end: str | None = decision_time_end
        if window_end is None and window:
            candidate = window[-1].get("created_at") or window[-1].get("verified_at")
            window_end = str(candidate) if candidate is not None else None
        return {
            "quality_window_size": QUALITY_WINDOW_SIZE,
            "quality_verified_count": verified_count,
            "quality_correct_count": correct_count,
            "rolling_accuracy": (
                correct_count / verified_count if verified_count > 0 else None
            ),
            "quality_window_end": window_end,
            "quality_policy_version": QUALITY_POLICY_VERSION,
        }

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
            verified_decisions = self._conservation_verified_decisions()
            verified, correct, override_rate = _conservation_stats(
                self._graph_store,
                verified_decisions=verified_decisions,
            )
            category_coverage = self._category_coverage_from_decisions(verified_decisions)
        except Exception:
            return None
        if verified <= 0:
            return None
        if verified < CONSERVATION_MIN_VERIFIED:
            return None

        q = correct / verified
        recent_window = max(int(getattr(self._preset, "conservation_recent_window", 100)), 1)
        recent_q_threshold = float(getattr(self._preset, "conservation_recent_q_threshold", 0.75))
        recent_quality = _recent_quality(
            self._graph_store,
            window=recent_window,
            verified_decisions=verified_decisions,
        )
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
                    "alpha": category_coverage,
                    "category_coverage": category_coverage,
                    "override_rate": override_rate,
                    "conservation_status": "RED",
                    "recent_q": recent_q,
                    "recent_window": recent_count,
                }
        theta_min = compute_theta_min(category_coverage, verified)
        dispersion = _conservation_dispersion(
            self._graph_store,
            verified_decisions=verified_decisions,
        )
        effective_q = q
        if dispersion is not None and float(dispersion.get("inflation", 0.0)) > 1.3:
            logger.info(
                "Conservation dispersion: inflation=%.2f",
                float(dispersion["inflation"]),
            )
            effective_q = max(0.0, q - float(dispersion.get("effective_se", 0.0)))
        conservation_signal = category_coverage * effective_q * verified
        if theta_min is not None and conservation_signal < theta_min:
            if dispersion is not None and float(dispersion.get("inflation", 0.0)) > 1.3:
                dispersion = {**dispersion, "q_conservative": effective_q}
            result = {
                "status": "paused",
                "reason": "conservation_red",
                "q": q,
                "theta_min": theta_min,
                "verified_count": verified,
                "correct_count": correct,
                "alpha": category_coverage,
                "category_coverage": category_coverage,
                "override_rate": override_rate,
                "conservation_status": "RED",
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
            # Conflict detection reads the current fingerprint; persistence
            # belongs after a successful learning update.
            fingerprint = self.fingerprint(persist=False)
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
        write_legacy: bool = False,
        checkpoint_id: str | None = None,
        capture_reason: str | None = None,
        regime_tag: str | None = None,
        transaction: Any | None = None,
        raise_on_error: bool = False,
    ) -> bool:
        checkpoint_iks = self._compute_checkpoint_iks()
        quality_data = self._checkpoint_quality(decision_time_end)
        metadata: dict[str, Any] = {
            "iks": checkpoint_iks,
            "composite_iks": float(iks),
            "centroid_distance_to_canonical": self.compute_centroid_distance_to_canonical(),
            "dk_weights": self._checkpoint_dk_weights(),
            "temperature": self.get_temperature(),
            "decision_count": int(getattr(self._scorer, "decision_count", 0)),
            "frozen": bool(getattr(self._scorer, "_frozen", False)),
            "paused_by_conservation": bool(
                getattr(self._scorer, "_paused_by_conservation", False)
            ),
            "regime_tag": regime_tag,
        }
        if consolidation:
            metadata.update({
                "boundary": boundary,
                "decisions_in_batch": decisions_in_batch,
                "consolidation": True,
            })
        if capture_reason is not None:
            metadata["capture_reason"] = capture_reason
        metadata.update(
            {
                "decision_time_start": decision_time_start,
                "decision_time_end": decision_time_end,
            }
        )
        persisted = False
        checkpoint_payload: dict[str, Any] = {}
        if write_legacy:
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
                persisted = True
            except Exception as exc:
                logger.warning(
                    "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",
                    self._domain, decision_id, "centroid_checkpoint", type(exc).__name__, exc,
                )
        if not isinstance(self._graph_store, ProtocolV2GraphStore):
            return persisted
        try:
            # V2 is the default checkpoint path.  The legacy path remains
            # available only for callers that explicitly opt in above.
            factor_names = list(self._preset.shape.factor_names)
            factor_names_hash = _factor_names_hash(factor_names)
            checkpoint_payload = {
                "checkpoint_id": checkpoint_id or f"{self._domain}:checkpoint:{uuid.uuid4().hex}",
                "domain": self._domain,
                "category": category,
                "action": action,
                "centroids": self._scorer.centroids,
                "decisions_count": int(decisions_in_batch or 1),
                "verified_count": self.get_verified_count(),
                "iks": checkpoint_iks,
                "shape": [int(value) for value in self._scorer.centroids.shape],
                "factor_names_hash": factor_names_hash,
                **quality_data,
                "metadata": {**metadata, "decision_id": decision_id},
            }
            checkpoint_writer = (
                transaction.write_centroid_checkpoint
                if transaction is not None
                else self._graph_store.write_centroid_checkpoint
            )
            checkpoint_writer(**checkpoint_payload)
            return True
        except Exception as exc:
            if raise_on_error:
                raise
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
            return persisted

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
                logger.info(
                    "Archived %d old decisions",
                    archived,
                    extra={"domain": self._domain},
                )
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
            outbox=self._outbox,
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
            decision_id = str(decisions[-1].get("decision_id")) if decisions[-1].get("decision_id") else None
            active_rules = self._evolver.get_active_rules()
            for rule_name in list(active_rules):
                self._evolver.evolve(
                    rule_name,
                    decisions,
                    conservation_state=conservation_state,
                    decision_id=decision_id,
                )
        except Exception as exc:
            logger.warning("Evolution run failed: %s", exc)

    def _evolution_conservation_state(self) -> dict[str, Any] | None:
        if self._calibration_overlay is not None:
            panel = self.get_conservation_state()
            if self._calibration_overlay is not None:
                return {
                    "status": "CALIBRATING",
                    "verified_count": int(panel.get("V") or 0),
                    "effective_V": int(panel.get("effective_V") or 0),
                    "correct_count": int(panel.get("correct_count") or 0),
                    "q": float(panel.get("q") or 0.0),
                    "theta_min": panel.get("theta_min"),
                    "alpha": float(panel.get("alpha") or 0.0),
                    "category_coverage": float(panel.get("alpha") or 0.0),
                    "override_rate": 0.0,
                }
        try:
            verified, correct, override_rate = _conservation_stats(self._graph_store)
            category_coverage = self._category_coverage()
        except Exception:
            return None
        if verified <= 0:
            return {
                "status": "GREEN",
                "verified_count": 0,
                "correct_count": 0,
                "q": 0.0,
                "theta_min": None,
                "alpha": 0.0,
                "category_coverage": 0.0,
                "override_rate": 0.0,
            }
        q = correct / verified
        theta_min = compute_theta_min(category_coverage, verified)
        conservation_signal = category_coverage * q * verified
        return {
            "status": "GREEN" if theta_min is not None and conservation_signal >= theta_min else "RED",
            "verified_count": verified,
            "correct_count": correct,
            "q": q,
            "theta_min": theta_min,
            "alpha": category_coverage,
            "category_coverage": category_coverage,
            "override_rate": override_rate,
        }

    def _category_coverage(self) -> float:
        """Return JM alpha: configured categories with verified data / all categories."""
        return self._category_coverage_from_decisions(self._conservation_verified_decisions())

    def _category_coverage_from_decisions(
        self,
        verified_decisions: list[dict[str, Any]],
    ) -> float:
        """Return JM alpha from a verified-decision snapshot."""
        total_categories = int(self._preset.shape.n_categories)
        if total_categories <= 0:
            return 0.0
        covered_categories = _count_categories_with_n(
            verified_decisions,
            CONSERVATION_CATEGORY_MIN_VERIFIED,
        )
        return min(1.0, covered_categories / total_categories)

    def _verified_decisions(self) -> list[dict[str, Any]]:
        if self._verified_decisions_cache is None:
            decisions = self._graph_store.get_verified_decisions(self._domain)
            self._verified_decisions_cache = [
                decision for decision in decisions if _is_verified_decision(decision)
            ]
        return self._verified_decisions_cache

    def _conservation_verified_decisions(self) -> list[dict[str, Any]]:
        return [
            decision
            for decision in self._verified_decisions()
            if not _is_benchmark_decision(decision)
        ]

    @property
    def graph_store(self) -> GraphStore:
        """The GraphStore single source of truth."""
        return self._graph_store

    def close(self) -> None:
        """Release persistence resources owned by this scorer."""
        if self._outbox is not None:
            self._outbox.stop_periodic_drain()
        self._graph_store.close()

    @property
    def gae_scorer(self) -> ProfileScorer:
        return self._scorer


def _conservation_counts(store: Any) -> tuple[int, int]:
    verified, correct, _override_rate = _conservation_stats(store)
    return verified, correct


def _conservation_dispersion(
    store: Any,
    *,
    verified_decisions: list[dict[str, Any]] | None = None,
) -> dict[str, float] | None:
    if verified_decisions is None:
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
    return block_bootstrap_mean_se(q_window, block=20, n_boot=200)


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
        return cast(np.ndarray, np.ones((n_categories, n_dims), dtype=np.float64))
    variances = np.var(vectors, axis=0)
    mean_variance = float(np.mean(variances))
    if mean_variance <= 0.0:
        return cast(np.ndarray, np.ones((n_categories, n_dims), dtype=np.float64))
    weights = np.clip(variances / mean_variance, 0.25, 4.0)
    return cast(np.ndarray, np.tile(weights.reshape(1, n_dims), (n_categories, 1)))


def _recent_quality(
    store: Any,
    *,
    window: int,
    verified_decisions: list[dict[str, Any]] | None = None,
) -> tuple[int, float] | None:
    if verified_decisions is None:
        verified_decisions = _conservation_verified_decisions(store)
    if not verified_decisions:
        return None
    recent = verified_decisions[-max(int(window), 1):]
    if not recent:
        return None
    correct = sum(1 for decision in recent if _is_correct_decision(decision))
    return len(recent), correct / len(recent)


def _conservation_stats(
    store: Any,
    *,
    verified_decisions: list[dict[str, Any]] | None = None,
) -> tuple[int, int, float]:
    if verified_decisions is None:
        domain = _store_domain(store)
        verified = max(int(store.count_verified(domain)), 0)
        correct = max(int(store.count_correct(domain)), 0)
        decisions = _conservation_verified_decisions(store)
    else:
        decisions = verified_decisions
        verified = len(decisions)
        correct = sum(1 for decision in decisions if _is_correct_decision(decision))
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


def _decision_regime_tag(decision: dict[str, Any]) -> str | None:
    """Return a canonical regime tag from a Decision, if one was supplied."""
    candidate = _decision_field(decision, "regime_tag")
    if candidate is None:
        metadata = decision.get("metadata")
        nested = metadata.get("regime_metadata") if isinstance(metadata, dict) else None
        candidate = nested.get("regime") if isinstance(nested, dict) else None
    tag = str(candidate).strip().lower() if candidate is not None else ""
    return tag if tag in {"trending", "ranging", "volatile"} else None


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
