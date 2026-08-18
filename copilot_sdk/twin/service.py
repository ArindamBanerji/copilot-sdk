"""Shared Frozen Twin scorer service."""

from __future__ import annotations

import copy
import time
from typing import Any

import numpy as np

from copilot_sdk.graph.memory_store import InMemoryGraphStore

from .models import DriftReport, FrozenSnapshot, ParallelResult
from .store import FrozenTwinStore


class FrozenTwin:
    """Run an immutable day-0 scorer beside a learning live scorer."""

    def __init__(self, store: FrozenTwinStore | None = None) -> None:
        self.store = store or FrozenTwinStore()
        self.graph_store = InMemoryGraphStore(domain="frozen_twin")
        self._snapshot: FrozenSnapshot | None = None
        self._frozen_scorer: Any | None = None
        self._copilot: str | None = None

    def freeze(
        self,
        scorer: Any,
        conservation_state: dict[str, Any],
        iks: float,
        copilot: str,
    ) -> FrozenSnapshot:
        """Persist the one-time day-0 state and construct its isolated scorer."""
        if self.store.exists(copilot):
            raise FileExistsError(f"Frozen Twin already exists for copilot {copilot!r}")
        snapshot = FrozenSnapshot.create(
            scorer_state=_scorer_state(scorer),
            kernel_state=_kernel_state(scorer),
            conservation_state=copy.deepcopy(conservation_state),
            iks_value=float(iks),
            metadata={
                "timestamp": time.time(),
                "copilot": copilot,
                "decision_count": int(getattr(scorer, "decision_count", 0)),
                "version": "frozen-twin-v1",
            },
        )
        self.store.save(snapshot)
        self._snapshot = snapshot
        self._copilot = copilot
        self._frozen_scorer = _scorer_from_state(snapshot.scorer_state, snapshot.kernel_state)
        return snapshot

    def is_frozen(self) -> bool:
        if self._snapshot is not None:
            return True
        if self._copilot is not None:
            return self.store.exists(self._copilot)
        return False

    def get_snapshot(self) -> FrozenSnapshot:
        if self._snapshot is None:
            raise RuntimeError("Frozen Twin has not been frozen")
        return self._snapshot

    def load(self, copilot: str) -> FrozenSnapshot:
        snapshot = self.store.load(copilot)
        if snapshot is None:
            raise FileNotFoundError(f"No Frozen Twin snapshot exists for copilot {copilot!r}")
        self._snapshot = snapshot
        self._copilot = copilot
        self._frozen_scorer = _scorer_from_state(snapshot.scorer_state, snapshot.kernel_state)
        return snapshot

    def score_frozen(self, factor_vector: Any, category_index: int) -> Any:
        if self._frozen_scorer is None:
            raise RuntimeError("Frozen Twin has not been frozen or loaded")
        # Deliberately no learn/update call: this scorer is a read-only clone.
        return self._frozen_scorer.score(np.asarray(factor_vector, dtype=np.float64), category_index)

    def score_parallel(self, factor_vector: Any, category_index: int, live_scorer: Any) -> ParallelResult:
        live_result = live_scorer.score(np.asarray(factor_vector, dtype=np.float64), category_index)
        frozen_result = self.score_frozen(factor_vector, category_index)
        return ParallelResult(
            live_result=live_result,
            frozen_result=frozen_result,
            delta=float(live_result.confidence - frozen_result.confidence),
        )

    def get_drift_report(self, live_scorer: Any) -> DriftReport:
        snapshot = self.get_snapshot()
        live_state = _scorer_state(live_scorer)
        centroid_drift = _l2(live_state.get("centroids"), snapshot.scorer_state.get("centroids"))
        weight_drift = _l2(
            _nested_array(live_state.get("scoring_kernel")),
            _nested_array(snapshot.kernel_state.get("weights")),
        )
        conservation_drift = _mapping_drift(
            snapshot.conservation_state,
            _live_conservation_state(live_scorer),
        )
        live_iks = getattr(live_scorer, "iks", getattr(live_scorer, "iks_value", snapshot.iks_value))
        decision_count = int(getattr(live_scorer, "decision_count", 0))
        frozen_count = int(snapshot.metadata.get("decision_count", 0))
        return DriftReport(
            centroid_drift=centroid_drift,
            weight_drift=weight_drift,
            conservation_drift=conservation_drift,
            iks_delta=float(live_iks) - snapshot.iks_value,
            decision_count_since_freeze=max(0, decision_count - frozen_count),
        )


def _scorer_state(scorer: Any) -> dict[str, Any]:
    state_method = getattr(scorer, "state_dict", None)
    if callable(state_method):
        state_result = state_method()
        if not isinstance(state_result, dict):
            raise TypeError("scorer.state_dict() must return a dictionary")
        return copy.deepcopy(state_result)
    checkpoint_method = getattr(scorer, "get_checkpoint_state", None)
    if not callable(checkpoint_method):
        raise TypeError("FrozenTwin requires scorer.state_dict() or get_checkpoint_state()")
    checkpoint = checkpoint_method()
    state_payload: dict[str, Any] = {
        "centroids": np.asarray(getattr(scorer, "mu", checkpoint.get("centroids")), dtype=np.float64).copy(),
        "actions": list(getattr(scorer, "actions", [])),
        "categories": copy.deepcopy(getattr(scorer, "categories", None)),
        "kernel": getattr(getattr(scorer, "kernel", "l2"), "value", getattr(scorer, "kernel", "l2")),
        "tau": float(getattr(scorer, "tau", 0.1)),
        "eta": float(getattr(scorer, "eta", 0.05)),
        "eta_neg": float(getattr(scorer, "eta_neg", 0.05)),
        "decay": float(getattr(scorer, "decay", 0.001)),
        "min_confidence": float(getattr(scorer, "min_confidence", 0.0)),
        "eta_override": getattr(scorer, "eta_override", None),
        "factor_mask": copy.deepcopy(getattr(scorer, "factor_mask", None)),
        "decision_count": int(getattr(scorer, "decision_count", 0)),
        "checkpoint": copy.deepcopy(checkpoint),
    }
    return state_payload


def _kernel_state(scorer: Any) -> dict[str, Any]:
    kernel = getattr(scorer, "scoring_kernel", None)
    weights = getattr(kernel, "weights", None)
    return {
        "type": type(kernel).__name__ if kernel is not None else "unknown",
        "weights": None if weights is None else np.asarray(weights, dtype=np.float64).copy(),
    }


def _scorer_from_state(state: dict[str, Any], kernel_state: dict[str, Any]) -> Any:
    from gae.kernels import DiagonalKernel
    from gae.profile_scorer import KernelType, ProfileScorer

    centroids = np.asarray(state["centroids"], dtype=np.float64)
    scorer_kernel = None
    weights = kernel_state.get("weights")
    if weights is not None:
        scorer_kernel = DiagonalKernel(weights=np.asarray(weights, dtype=np.float64))
    kernel = KernelType(str(state.get("kernel", "l2")))
    scorer = ProfileScorer(
        mu=centroids,
        actions=list(state.get("actions") or [f"action_{i}" for i in range(centroids.shape[1])]),
        categories=copy.deepcopy(state.get("categories")),
        kernel=kernel,
        min_confidence=float(state.get("min_confidence", 0.0)),
        eta_override=state.get("eta_override"),
        factor_mask=None if state.get("factor_mask") is None else np.asarray(state["factor_mask"], dtype=np.float64),
        scoring_kernel=scorer_kernel,
    )
    checkpoint = state.get("checkpoint")
    if isinstance(checkpoint, dict) and callable(getattr(scorer, "restore_checkpoint_state", None)):
        scorer.restore_checkpoint_state(checkpoint)
    return scorer


def _nested_array(value: Any) -> np.ndarray | None:
    if value is None:
        return None
    return np.asarray(value, dtype=np.float64)


def _l2(left: Any, right: Any) -> float:
    if left is None or right is None:
        return 0.0
    left_array = np.asarray(left, dtype=np.float64)
    right_array = np.asarray(right, dtype=np.float64)
    if left_array.shape != right_array.shape:
        return float("inf")
    return float(np.linalg.norm(left_array - right_array))


def _live_conservation_state(scorer: Any) -> dict[str, Any]:
    status = getattr(scorer, "conservation_status", None)
    return {} if status is None else {"status": status}


def _mapping_drift(left: dict[str, Any], right: dict[str, Any]) -> float:
    if left == right:
        return 0.0
    numeric_diffs: list[float] = []
    for key in set(left).union(right):
        first, second = left.get(key), right.get(key)
        if isinstance(first, (int, float)) and isinstance(second, (int, float)):
            numeric_diffs.append(abs(float(first) - float(second)))
        elif first != second:
            numeric_diffs.append(1.0)
    return float(max(numeric_diffs, default=1.0))
