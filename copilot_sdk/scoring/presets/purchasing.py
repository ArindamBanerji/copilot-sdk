"""Purchasing domain preset."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import numpy as np

from copilot_sdk.evolution import PlateauConfig
from copilot_sdk.scoring.config import DomainShape
from copilot_sdk.scoring.polarity import Polarity


class PurchasingPreset:
    factor_polarities = {
        "expected_demand": Polarity.POSITIVE,
        "day_of_week": Polarity.NEUTRAL,
        "weather_forecast": Polarity.NEUTRAL,
        "event_flag": Polarity.NEUTRAL,
        "historical_waste": Polarity.NEGATIVE,
        "supplier_lead_time": Polarity.NEGATIVE,
        "price_memory_index": Polarity.POSITIVE,
    }

    @property
    def name(self) -> str:
        return "purchasing"

    @property
    def shape(self) -> DomainShape:
        return DomainShape(
            n_categories=5,
            n_actions=4,
            n_factors=7,
            category_names=(
                "protein",
                "produce",
                "dairy",
                "dry_goods",
                "beverages",
            ),
            action_names=(
                "order_as_planned",
                "order_more",
                "order_less",
                "skip",
            ),
            factor_names=(
                "expected_demand",
                "day_of_week",
                "weather_forecast",
                "event_flag",
                "historical_waste",
                "supplier_lead_time",
                # price_memory_index: historical price tracking per supplier x category.
                # High means price within learned norms; low means anomalous spike or hidden discount.
                "price_memory_index",
            ),
        )

    @property
    def penalty_ratio(self) -> float:
        return 3.0

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
    def q_window(self) -> int:
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


def _load_bootstrap(preset: PurchasingPreset) -> np.ndarray:
    path = Path(__file__).parent / "purchasing_bootstrap.json"
    expected_shape = preset.shape.tensor_shape
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        centroids = np.asarray(data["centroids"], dtype=np.float64)
        if centroids.shape == (5, 4, 6) and expected_shape == (5, 4, 7):
            return _migrate_legacy_centroids(centroids)
        if centroids.shape != expected_shape:
            raise ValueError(
                f"purchasing bootstrap shape {centroids.shape} != {expected_shape}"
            )
        return cast(np.ndarray, centroids)
    except Exception:
        return cast(np.ndarray, np.full(expected_shape, 0.5, dtype=np.float64))


def _migrate_legacy_centroids(centroids: np.ndarray) -> np.ndarray:
    migrated = np.full((5, 4, 7), 0.5, dtype=np.float64)
    migrated[:, :, :6] = centroids
    migrated[:, :, 6] = 0.5
    return cast(np.ndarray, migrated)
