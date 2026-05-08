"""Purchasing domain preset."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from copilot_sdk.scoring.config import DomainShape


class PurchasingPreset:
    @property
    def name(self) -> str:
        return "purchasing"

    @property
    def shape(self) -> DomainShape:
        return DomainShape(
            n_categories=5,
            n_actions=4,
            n_factors=6,
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
    def bootstrap_centroids(self) -> np.ndarray:
        return _load_bootstrap(self)


def _load_bootstrap(preset: PurchasingPreset) -> np.ndarray:
    path = Path(__file__).parent / "purchasing_bootstrap.json"
    expected_shape = preset.shape.tensor_shape
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        centroids = np.asarray(data["centroids"], dtype=np.float64)
        if centroids.shape != expected_shape:
            raise ValueError(
                f"purchasing bootstrap shape {centroids.shape} != {expected_shape}"
            )
        return centroids
    except Exception:
        return np.full(expected_shape, 0.5, dtype=np.float64)
