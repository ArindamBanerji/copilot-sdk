"""DK Welford tracking and L5 persistence helpers."""

from __future__ import annotations

import logging
import time
from copy import deepcopy
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, cast

import numpy as np


WELFORD_VECTOR_KEYS = (
    "confirmed_mean",
    "confirmed_m2",
    "overridden_mean",
    "overridden_m2",
    "all_mean",
    "all_m2",
)
WELFORD_STATE_KEYS = (*WELFORD_VECTOR_KEYS, "n_all")


def _coerce_vector(vector: Any) -> np.ndarray:
    if isinstance(vector, (str, bytes, bytearray, Mapping)):
        raise TypeError("vector must be a non-string 1D numeric iterable")
    if not isinstance(vector, Iterable):
        raise TypeError("vector must be a 1D numeric iterable")
    values = list(vector)
    if not values:
        raise ValueError("vector must be non-empty")
    try:
        array = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise TypeError("vector must contain only numeric values") from exc
    if array.ndim != 1:
        raise ValueError("vector must be 1D")
    if not np.all(np.isfinite(array)):
        raise ValueError("vector must contain only finite numeric values")
    return cast(np.ndarray, array)


def _coerce_count(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int")
    if value < 0:
        raise ValueError(f"{name} must be >= 0")
    return int(value)


class WelfordAccumulator:
    """Online mean/M2 accumulator for fixed-width factor vectors."""

    def __init__(self, dimension: int | None = None) -> None:
        if dimension is not None:
            if isinstance(dimension, bool) or not isinstance(dimension, int):
                raise TypeError("dimension must be an int")
            if dimension <= 0:
                raise ValueError("dimension must be > 0")
        self._dimension = dimension
        self._n = 0
        self._mean = (
            None if dimension is None else np.zeros(dimension, dtype=np.float64)
        )
        self._m2 = None if dimension is None else np.zeros(dimension, dtype=np.float64)

    @property
    def n(self) -> int:
        return self._n

    @property
    def dimension(self) -> int | None:
        return self._dimension

    def update(self, vector: Sequence[float] | np.ndarray) -> None:
        values = _coerce_vector(vector)
        if self._dimension is None:
            self._dimension = int(values.shape[0])
            self._mean = np.zeros(self._dimension, dtype=np.float64)
            self._m2 = np.zeros(self._dimension, dtype=np.float64)
        elif int(values.shape[0]) != self._dimension:
            raise ValueError(
                f"vector dimension {values.shape[0]} does not match {self._dimension}"
            )

        assert self._mean is not None
        assert self._m2 is not None
        self._n += 1
        delta = values - self._mean
        self._mean += delta / self._n
        delta2 = values - self._mean
        self._m2 += delta * delta2

    def to_state(self) -> dict[str, object]:
        if self._dimension is None or self._mean is None or self._m2 is None:
            raise ValueError("cannot serialize empty accumulator without dimension")
        return {
            "mean": self._mean.copy().tolist(),
            "m2": self._m2.copy().tolist(),
            "n": self._n,
        }

    @classmethod
    def from_state(cls, state: Mapping[str, object]) -> "WelfordAccumulator":
        if not isinstance(state, Mapping):
            raise TypeError("state must be a mapping")
        mean = _coerce_vector(state.get("mean"))
        m2 = _coerce_vector(state.get("m2"))
        if mean.shape != m2.shape:
            raise ValueError("mean and m2 must have equal dimensions")
        n = _coerce_count(state.get("n"), "n")
        accumulator = cls(int(mean.shape[0]))
        accumulator._n = n
        accumulator._mean = mean.copy()
        accumulator._m2 = m2.copy()
        return accumulator


class DKWelfordTracker:
    """Track Welford audit state for confirmed, overridden, and all decisions."""

    def __init__(self, dimension: int | None = None) -> None:
        self._confirmed = WelfordAccumulator(dimension)
        self._overridden = WelfordAccumulator(dimension)
        self._all = WelfordAccumulator(dimension)

    @property
    def n_confirmed(self) -> int:
        return self._confirmed.n

    @property
    def n_overridden(self) -> int:
        return self._overridden.n

    @property
    def n_all(self) -> int:
        return self._all.n

    @property
    def dimension(self) -> int | None:
        return self._all.dimension

    def update(self, factor_vector: Sequence[float] | np.ndarray, is_correct: bool) -> None:
        if not isinstance(is_correct, bool):
            raise TypeError("is_correct must be bool")
        values = _coerce_vector(factor_vector)
        self._all.update(values)
        if is_correct:
            self._confirmed.update(values)
        else:
            self._overridden.update(values)

    def to_welford_state(self) -> dict[str, object]:
        if self._all.dimension is None or self._all.n == 0:
            raise ValueError("cannot serialize Welford state with no decisions")
        dimension = self._all.dimension
        assert dimension is not None
        confirmed = self._accumulator_state_or_zeros(self._confirmed, dimension)
        overridden = self._accumulator_state_or_zeros(self._overridden, dimension)
        all_state = self._all.to_state()
        return {
            "confirmed_mean": deepcopy(confirmed["mean"]),
            "confirmed_m2": deepcopy(confirmed["m2"]),
            "overridden_mean": deepcopy(overridden["mean"]),
            "overridden_m2": deepcopy(overridden["m2"]),
            "all_mean": deepcopy(all_state["mean"]),
            "all_m2": deepcopy(all_state["m2"]),
            "n_all": self.n_all,
        }

    @classmethod
    def from_welford_state(
        cls,
        state: Mapping[str, object],
        *,
        n_confirmed: int,
        n_overridden: int,
    ) -> "DKWelfordTracker":
        if not isinstance(state, Mapping):
            raise TypeError("state must be a mapping")
        missing = [key for key in WELFORD_STATE_KEYS if key not in state]
        if missing:
            raise ValueError(f"missing Welford state keys: {missing}")
        vectors = {key: _coerce_vector(state[key]) for key in WELFORD_VECTOR_KEYS}
        dimensions = {tuple(value.shape) for value in vectors.values()}
        if len(dimensions) != 1:
            raise ValueError("all Welford vectors must have equal dimensions")
        n_all = _coerce_count(state["n_all"], "n_all")
        confirmed_count = _coerce_count(n_confirmed, "n_confirmed")
        overridden_count = _coerce_count(n_overridden, "n_overridden")
        dimension = int(next(iter(vectors.values())).shape[0])
        tracker = cls(dimension)
        tracker._confirmed = WelfordAccumulator.from_state(
            {
                "mean": vectors["confirmed_mean"].tolist(),
                "m2": vectors["confirmed_m2"].tolist(),
                "n": confirmed_count,
            }
        )
        tracker._overridden = WelfordAccumulator.from_state(
            {
                "mean": vectors["overridden_mean"].tolist(),
                "m2": vectors["overridden_m2"].tolist(),
                "n": overridden_count,
            }
        )
        tracker._all = WelfordAccumulator.from_state(
            {
                "mean": vectors["all_mean"].tolist(),
                "m2": vectors["all_m2"].tolist(),
                "n": n_all,
            }
        )
        return tracker

    @staticmethod
    def _accumulator_state_or_zeros(
        accumulator: WelfordAccumulator,
        dimension: int,
    ) -> dict[str, object]:
        if accumulator.n == 0:
            return {
                "mean": [0.0] * dimension,
                "m2": [0.0] * dimension,
                "n": 0,
            }
        return accumulator.to_state()


def persist_dk_after_reestimate(
    *,
    domain: str,
    scorer: object,
    learning_store: object | None,
    welford_tracker: DKWelfordTracker | None,
    entity_group: str | None = None,
    logger: logging.Logger | None = None,
) -> bool:
    """Persist current scorer DK weights and Welford audit state to L5 storage."""
    if learning_store is None:
        return False

    log = logger or logging.getLogger(__name__)
    get_dk_weights = getattr(scorer, "get_dk_weights", None)
    if not callable(get_dk_weights):
        log.warning("DK persistence skipped for %s: scorer has no get_dk_weights", domain)
        return False

    weights = get_dk_weights()
    if weights is None:
        return False
    if welford_tracker is None or welford_tracker.n_all == 0:
        log.debug("DK persistence skipped for %s: Welford state unavailable", domain)
        return False

    try:
        welford_state = welford_tracker.to_welford_state()
        update_dk_weights = getattr(learning_store, "update_dk_weights")
        update_dk_weights(
            domain=domain,
            weight_tensor=deepcopy(weights),
            n_decisions_used=welford_tracker.n_all,
            computed_at=time.time(),
            welford_state=welford_state,
            n_confirmed=welford_tracker.n_confirmed,
            n_overridden=welford_tracker.n_overridden,
            entity_group=entity_group,
        )
    except Exception as exc:
        log.warning("L5 DK persistence failed for %s: %s", domain, exc)
        return False
    return True
