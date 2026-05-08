"""Domain configuration contracts for CompoundingScorer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class DomainShape:
    """Canonical tensor and label shape for one domain."""

    n_categories: int
    n_actions: int
    n_factors: int
    category_names: tuple[str, ...]
    action_names: tuple[str, ...]
    factor_names: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.category_names) != self.n_categories:
            raise ValueError("category_names length must match n_categories")
        if len(self.action_names) != self.n_actions:
            raise ValueError("action_names length must match n_actions")
        if len(self.factor_names) != self.n_factors:
            raise ValueError("factor_names length must match n_factors")

    @property
    def tensor_shape(self) -> tuple[int, int, int]:
        return (self.n_categories, self.n_actions, self.n_factors)

    @property
    def tensor_size(self) -> int:
        return self.n_categories * self.n_actions * self.n_factors


class DomainPreset(Protocol):
    """Protocol implemented by domain preset adapters."""

    name: str
    shape: DomainShape
    penalty_ratio: float
    bootstrap_centroids: np.ndarray
    eta_confirm: float
    eta_override: float
    temperature: float
