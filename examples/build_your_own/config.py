"""Shared configuration adapter for the two build-your-own domain skins."""

from dataclasses import dataclass

import numpy as np

from copilot_sdk.scoring.config import DomainShape
from copilot_sdk.evolution import PlateauConfig


@dataclass
class BuildYourOwnPreset:
    name: str
    shape: DomainShape
    penalty_ratio: float
    bootstrap_centroids: np.ndarray
    eta_confirm: float = 0.05
    eta_override: float = 0.01
    temperature: float = 0.1
    plateau_config: PlateauConfig | None = None
    conservation_recent_window: int = 100
    conservation_recent_q_threshold: float = 0.75


def make_preset(domain) -> BuildYourOwnPreset:
    shape = DomainShape(
        n_categories=len(domain.CATEGORIES),
        n_actions=len(domain.ACTIONS),
        n_factors=len(domain.FACTORS),
        category_names=tuple(domain.CATEGORIES),
        action_names=tuple(domain.ACTIONS),
        factor_names=tuple(domain.FACTORS),
    )
    # A simple deterministic prior gives the faithful bandit a learnable
    # contextual problem while keeping the harness domain-agnostic.
    centroids = canonical_centroids(shape)
    return BuildYourOwnPreset(
        name=domain.DOMAIN_NAME,
        shape=shape,
        penalty_ratio=float(domain.PENALTY_RATIO),
        bootstrap_centroids=centroids,
    )


def canonical_centroids(shape: DomainShape) -> np.ndarray:
    centroids = np.empty(shape.tensor_shape, dtype=np.float64)
    levels = np.linspace(0.15, 0.85, shape.n_actions)
    for action_index, level in enumerate(levels):
        centroids[:, action_index, :] = level
    return centroids


__all__ = ["BuildYourOwnPreset", "canonical_centroids", "make_preset"]
