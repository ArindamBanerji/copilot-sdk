"""DataOps domain preset."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from copilot_sdk.evolution import PlateauConfig
from copilot_sdk.scoring.config import DomainShape
from copilot_sdk.scoring.polarity import Polarity


class DataOpsPreset:
    factor_polarities = {
        "impact_scope": Polarity.NEGATIVE,
        "source_reliability": Polarity.POSITIVE,
        "recurrence_frequency": Polarity.NEGATIVE,
        "downstream_urgency": Polarity.NEGATIVE,
        "data_freshness": Polarity.POSITIVE,
        "business_criticality": Polarity.NEGATIVE,
    }

    @property
    def name(self) -> str:
        return "dataops"

    @property
    def shape(self) -> DomainShape:
        return DomainShape(
            n_categories=6,
            n_actions=5,
            n_factors=6,
            category_names=(
                "schema_change",
                "volume_anomaly",
                "quality_anomaly",
                "freshness_violation",
                "pipeline_failure",
                "transform_drift",
            ),
            action_names=(
                "auto_approve",
                "investigate",
                "escalate_to_owner",
                "pause_downstream",
                "refer_to_specialist",
            ),
            factor_names=(
                "impact_scope",
                "source_reliability",
                "recurrence_frequency",
                "downstream_urgency",
                "data_freshness",
                "business_criticality",
            ),
        )

    @property
    def penalty_ratio(self) -> float:
        return 10.0

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
        # C*A=30; window=round(10*sqrt((C*A)/20))=12; cooldown=5*window.
        return PlateauConfig(
            plateau_window=12,
            min_improvement_rate=0.20,
            plateau_cooldown=60,
        )

    @property
    def bootstrap_centroids(self) -> np.ndarray:
        return _load_bootstrap(self)


def _load_bootstrap(preset: DataOpsPreset) -> np.ndarray:
    path = Path(__file__).parent / "dataops_bootstrap.json"
    expected_shape = preset.shape.tensor_shape
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        centroids = np.asarray(data["centroids"], dtype=np.float64)
        if centroids.shape != expected_shape:
            raise ValueError(f"dataops bootstrap shape {centroids.shape} != {expected_shape}")
        return centroids
    except Exception:
        return np.full(expected_shape, 0.5, dtype=np.float64)
