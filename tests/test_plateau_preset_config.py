from __future__ import annotations

from math import sqrt

import numpy as np

from copilot_sdk.evolution import PlateauConfig
from copilot_sdk.scoring.config import DomainShape
from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.scoring.scorer import CompoundingScorer


BASELINE_CELLS = 20


def _expected_window(cells: int) -> int:
    return round(10 * sqrt(cells / BASELINE_CELLS))


def test_preset_plateau_config_tensor_derived() -> None:
    assert set(PRESET_REGISTRY) == {"dataops", "purchasing", "s2p", "trading"}

    for preset_cls in PRESET_REGISTRY.values():
        preset = preset_cls()
        cells = preset.shape.n_categories * preset.shape.n_actions
        full_tensor_volume = cells * preset.shape.n_factors
        expected_window = _expected_window(cells)
        tensor_volume_window = _expected_window(full_tensor_volume)

        assert isinstance(preset.plateau_config, PlateauConfig)
        assert preset.plateau_config.plateau_window == expected_window
        assert preset.plateau_config.min_improvement_rate == 0.2
        assert preset.plateau_config.plateau_cooldown == expected_window * 5
        assert preset.plateau_config.plateau_window != tensor_volume_window


def test_purchasing_is_plateau_baseline() -> None:
    preset = PRESET_REGISTRY["purchasing"]()
    cells = preset.shape.n_categories * preset.shape.n_actions

    assert preset.shape.n_categories == 5
    assert preset.shape.n_actions == 4
    assert cells == BASELINE_CELLS
    assert preset.plateau_config.plateau_window == 10
    assert preset.plateau_config.min_improvement_rate == 0.2
    assert preset.plateau_config.plateau_cooldown == 50


def test_plateau_window_ordering_by_cells() -> None:
    presets = {name: preset_cls() for name, preset_cls in PRESET_REGISTRY.items()}

    assert presets["trading"].shape.n_categories * presets["trading"].shape.n_actions == 15
    assert presets["purchasing"].shape.n_categories * presets["purchasing"].shape.n_actions == 20
    assert presets["s2p"].shape.n_categories * presets["s2p"].shape.n_actions == 25
    assert presets["dataops"].shape.n_categories * presets["dataops"].shape.n_actions == 30

    assert (
        presets["trading"].plateau_config.plateau_window
        < presets["purchasing"].plateau_config.plateau_window
        < presets["s2p"].plateau_config.plateau_window
        < presets["dataops"].plateau_config.plateau_window
    )


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
