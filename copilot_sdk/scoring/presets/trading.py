"""Trading domain preset."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from copilot_sdk.evolution import PlateauConfig
from copilot_sdk.scoring.config import DomainShape


_LEGACY_ACTION_CONFIDENCE = (0.65, 0.55, 0.50)
_NEUTRAL_SKIP_CENTROID = (0.30, 0.35, 0.50, 0.50, 0.50, 0.25, 0.40, 0.50, 0.50, 0.50)


class TradingPreset:
    @property
    def name(self) -> str:
        return "trading"

    @property
    def shape(self) -> DomainShape:
        return DomainShape(
            n_categories=5,
            n_actions=4,
            n_factors=10,
            category_names=(
                "trend_following",
                "mean_reversion",
                "event_driven",
                "income_strategy",
                "scalp_intraday",
            ),
            action_names=("strong_execution", "partial_execution", "poor_execution", "skip_recommended"),
            factor_names=(
                "signal_alignment",
                "market_regime",
                "position_sizing",
                "timing_quality",
                "risk_reward_actual",
                "emotional_indicator",
                "signal_confidence",
                "options_delta_exposure",
                "options_iv_percentile",
                "options_gamma_risk",
            ),
        )

    @property
    def penalty_ratio(self) -> float:
        # Trading errors are recoverable via stop loss, but still asymmetric.
        return 3.0

    @property
    def eta_confirm(self) -> float:
        return 0.05

    @property
    def eta_override(self) -> float:
        # Calibration pending with pilot data.
        return 0.01

    @property
    def temperature(self) -> float:
        return 0.1

    @property
    def q_window(self) -> int:
        # Theorem-validated / math synopsis v14; active traders converge over months.
        return 400

    @property
    def plateau_config(self) -> PlateauConfig:
        # C*A=20; window=round(10*sqrt((C*A)/20))=10; cooldown=5*window.
        return PlateauConfig(
            plateau_window=10,
            min_improvement_rate=0.20,
            plateau_cooldown=50,
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
        if centroids.shape == (5, 3, 6) and expected_shape == (5, 4, 10):
            return _migrate_legacy_centroids(centroids)
        if centroids.shape != expected_shape:
            raise ValueError(f"trading bootstrap shape {centroids.shape} != {expected_shape}")
        return centroids
    except Exception:
        return np.full(expected_shape, 0.5, dtype=np.float64)


def _migrate_legacy_centroids(centroids: np.ndarray) -> np.ndarray:
    migrated = np.full((5, 4, 10), 0.5, dtype=np.float64)
    migrated[:, :3, :6] = centroids
    for action_index, signal_confidence in enumerate(_LEGACY_ACTION_CONFIDENCE):
        migrated[:, action_index, 6] = signal_confidence
    # Legacy bootstrap data did not include the skip action; use the conservative
    # neutral skip profile for every strategy category until pilot data lands.
    migrated[:, 3, :] = np.asarray(_NEUTRAL_SKIP_CENTROID, dtype=np.float64)
    return migrated
