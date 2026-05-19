"""Trading domain preset."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from copilot_sdk.evolution import PlateauConfig
from copilot_sdk.scoring.config import DomainShape


class TradingPreset:
    @property
    def name(self) -> str:
        return "trading"

    @property
    def shape(self) -> DomainShape:
        return DomainShape(
            n_categories=5,
            n_actions=3,
            n_factors=6,
            category_names=(
                "equity_long",
                "equity_short",
                "crypto_spot",
                "options",
                "etf",
            ),
            action_names=("buy", "hold", "sell"),
            factor_names=(
                "conviction",
                "research_depth",
                "technical_signal",
                "position_size",
                "time_horizon",
                "market_regime",
            ),
        )

    @property
    def penalty_ratio(self) -> float:
        return 2.0

    @property
    def eta_confirm(self) -> float:
        return 0.05

    @property
    def eta_override(self) -> float:
        return 0.01

    @property
    def temperature(self) -> float:
        return 0.1

    @property
    def plateau_config(self) -> PlateauConfig:
        # C*A=15; window=round(10*sqrt((C*A)/20))=9; cooldown=5*window.
        return PlateauConfig(
            plateau_window=9,
            min_improvement_rate=0.20,
            plateau_cooldown=45,
        )

    @property
    def bootstrap_centroids(self) -> np.ndarray:
        return _load_bootstrap(self)


def _load_bootstrap(preset: TradingPreset) -> np.ndarray:
    path = Path(__file__).parent / "trading_bootstrap.json"
    expected_shape = preset.shape.tensor_shape
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        centroids = np.asarray(data["centroids"], dtype=np.float64)
        if centroids.shape != expected_shape:
            raise ValueError(f"trading bootstrap shape {centroids.shape} != {expected_shape}")
        return centroids
    except Exception:
        return np.full(expected_shape, 0.5, dtype=np.float64)
