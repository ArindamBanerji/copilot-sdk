from __future__ import annotations

import numpy as np

from copilot_sdk.evolution import PlateauConfig
from copilot_sdk.scoring.config import DomainShape
from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.scoring.scorer import CompoundingScorer


def test_preset_plateau_config() -> None:
    assert set(PRESET_REGISTRY) == {"dataops", "purchasing", "s2p", "trading"}

    for preset_cls in PRESET_REGISTRY.values():
        preset = preset_cls()

        assert isinstance(preset.plateau_config, PlateauConfig)
        assert preset.plateau_config.plateau_window == 10
        assert preset.plateau_config.min_improvement_rate == 0.2
        assert preset.plateau_config.plateau_cooldown == 50


def test_scorer_uses_preset_plateau_config(monkeypatch, tmp_path) -> None:
    class CustomPreset:
        name = "custom_plateau"
        shape = DomainShape(
            n_categories=1,
            n_actions=2,
            n_factors=2,
            category_names=("category",),
            action_names=("approve", "review"),
            factor_names=("risk", "value"),
        )
        penalty_ratio = 2.0
        bootstrap_centroids = np.full((1, 2, 2), 0.5, dtype=np.float64)
        eta_confirm = 0.05
        eta_override = 0.01
        temperature = 0.1
        plateau_config = PlateauConfig(
            plateau_window=7,
            min_improvement_rate=0.35,
            plateau_cooldown=11,
        )

    monkeypatch.setitem(PRESET_REGISTRY, "custom_plateau", CustomPreset)

    scorer = CompoundingScorer.from_preset(
        "custom_plateau",
        db_path=str(tmp_path / "custom.db"),
        evolve=True,
    )
    try:
        assert scorer._evolver is not None
        assert scorer._evolver.plateau_config == CustomPreset.plateau_config
    finally:
        scorer.graph_store.close()
        scorer.store.close()


def test_plateau_config_backward_compatible(monkeypatch, tmp_path) -> None:
    class LegacyPreset:
        name = "legacy"
        shape = DomainShape(
            n_categories=1,
            n_actions=2,
            n_factors=2,
            category_names=("category",),
            action_names=("approve", "review"),
            factor_names=("risk", "value"),
        )
        penalty_ratio = 2.0
        bootstrap_centroids = np.full((1, 2, 2), 0.5, dtype=np.float64)
        eta_confirm = 0.05
        eta_override = 0.01
        temperature = 0.1

    monkeypatch.setitem(PRESET_REGISTRY, "legacy", LegacyPreset)

    scorer = CompoundingScorer.from_preset(
        "legacy",
        db_path=str(tmp_path / "legacy.db"),
        evolve=True,
    )
    try:
        assert scorer._evolver is not None
        assert scorer._evolver.plateau_config == PlateauConfig()
    finally:
        scorer.graph_store.close()
        scorer.store.close()
