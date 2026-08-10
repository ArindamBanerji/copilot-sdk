"""Ground-truth centroid oracle for the JM Reference App.

This module is the sole source of correctness labels.  Its centroids are
hidden from the factor-vector generator and are derived from an independent
seed so the demonstrated learning dynamics remain genuinely measured.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class OracleConfig:
    """Configuration for hidden ground-truth centroids."""

    seed: int = 99
    n_categories: int = 6
    n_actions: int = 6
    n_factors: int = 6
    category_names: list[str] | None = None
    action_names: list[str] | None = None
    factor_names: list[str] | None = None
    epsilon_firm: float = 0.20
    canonical_prior: np.ndarray | None = None


class GroundTruthOracle:
    """Label an action by nearest hidden centroid for its category."""

    def __init__(self, config: OracleConfig):
        self._config = config
        self._rng = np.random.default_rng(config.seed)
        self._category_names = list(
            config.category_names
            or [f"cat_{i}" for i in range(config.n_categories)]
        )
        self._action_names = list(
            config.action_names
            or [f"action_{i}" for i in range(config.n_actions)]
        )
        self._factor_names = list(
            config.factor_names
            or [f"factor_{i}" for i in range(config.n_factors)]
        )
        expected_shape = (
            len(self._category_names),
            len(self._action_names),
            len(self._factor_names),
        )
        if config.canonical_prior is None:
            self._canonical = np.full(expected_shape, 0.5, dtype=float)
        else:
            self._canonical = np.asarray(config.canonical_prior, dtype=float).copy()
            if self._canonical.shape != expected_shape:
                raise ValueError(
                    f"canonical_prior shape {self._canonical.shape} "
                    f"does not match {expected_shape}"
                )
        self._ground_truth = self._build_ground_truth()

    def _build_ground_truth(self) -> np.ndarray:
        """Displace centroids to the configured normalized epsilon."""

        ground_truth = self._canonical.copy()
        normalized_cell_count = np.sqrt(
            len(self._category_names) * len(self._action_names)
        )
        for category_index in range(len(self._category_names)):
            for action_index in range(len(self._action_names)):
                direction = self._rng.standard_normal(len(self._factor_names))
                direction /= max(float(np.linalg.norm(direction)), 1e-10)
                ground_truth[category_index, action_index] += (
                    direction
                    * self._config.epsilon_firm
                    * normalized_cell_count
                )
        return np.clip(ground_truth, 0.0, 1.0)

    def _category_index(self, category: str | int) -> int:
        if isinstance(category, int):
            index = category
        else:
            index = self._category_names.index(category)
        if not 0 <= index < len(self._category_names):
            raise IndexError(f"category index out of range: {index}")
        return index

    def _action_index(self, action: str | int) -> int:
        if isinstance(action, int):
            index = action
        else:
            index = self._action_names.index(action)
        if not 0 <= index < len(self._action_names):
            raise IndexError(f"action index out of range: {index}")
        return index

    def label_correct(
        self,
        category: str | int,
        chosen_action: str | int,
        factor_vector: dict[str, float] | np.ndarray,
    ) -> bool:
        """Return whether the chosen action is nearest to hidden truth."""

        category_index = self._category_index(category)
        action_index = self._action_index(chosen_action)
        if isinstance(factor_vector, dict):
            vector = np.asarray(
                [factor_vector[name] for name in self._factor_names], dtype=float
            )
        else:
            vector = np.asarray(factor_vector, dtype=float)
        if vector.shape != (len(self._factor_names),):
            raise ValueError(
                f"factor vector shape {vector.shape} does not match "
                f"({len(self._factor_names)},)"
            )
        distances = np.linalg.norm(
            self._ground_truth[category_index] - vector, axis=1
        )
        return int(np.argmin(distances)) == action_index

    @property
    def ground_truth_centroids(self) -> np.ndarray:
        """Return a copy for tests and visualization, never mutation."""

        return self._ground_truth.copy()

    @property
    def measured_epsilon_firm(self) -> float:
        """Return normalized Frobenius distance from the canonical prior."""

        difference = self._ground_truth - self._canonical
        raw_distance = float(np.linalg.norm(difference))
        return raw_distance / max(float(np.sqrt(self._ground_truth.size)), 1.0)
