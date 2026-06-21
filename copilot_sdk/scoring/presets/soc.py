"""SOC domain preset."""

from __future__ import annotations

import numpy as np

from copilot_sdk.evolution import PlateauConfig
from copilot_sdk.scoring.config import DomainShape
from copilot_sdk.scoring.polarity import Polarity


class SOCPreset:
    """Security operations center alert-triage scoring preset."""

    factor_polarities = {
        "privileged_identity_context": Polarity.NEGATIVE,
        "asset_criticality": Polarity.NEGATIVE,
        "threat_intel_enrichment": Polarity.NEGATIVE,
        "pattern_history": Polarity.NEGATIVE,
        "time_anomaly": Polarity.NEGATIVE,
        "device_trust": Polarity.POSITIVE,
    }

    @property
    def name(self) -> str:
        return "soc"

    @property
    def shape(self) -> DomainShape:
        return DomainShape(
            n_categories=6,
            n_actions=4,
            n_factors=6,
            category_names=(
                "credential_access",
                "malware_execution",
                "lateral_movement",
                "data_exfiltration",
                "insider_threat",
                "cloud_infrastructure",
            ),
            action_names=(
                "escalate",
                "investigate",
                "suppress",
                "monitor",
            ),
            factor_names=(
                "privileged_identity_context",
                "asset_criticality",
                "threat_intel_enrichment",
                "pattern_history",
                "time_anomaly",
                "device_trust",
            ),
        )

    @property
    def penalty_ratio(self) -> float:
        return 20.0

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
        # C*A=24; window=round(10*sqrt((C*A)/20))=11; cooldown=5*window.
        return PlateauConfig(
            plateau_window=11,
            min_improvement_rate=0.20,
            plateau_cooldown=55,
        )

    @property
    def bootstrap_centroids(self) -> np.ndarray:
        return np.asarray(
            [
                [
                    [0.75, 0.85, 0.8, 0.6, 0.65, 0.15],
                    [0.6, 0.6, 0.55, 0.55, 0.5, 0.4],
                    [0.3, 0.25, 0.15, 0.2, 0.25, 0.85],
                    [0.2, 0.45, 0.25, 0.35, 0.35, 0.65],
                ],
                [
                    [0.75, 0.8, 0.9, 0.55, 0.6, 0.2],
                    [0.6, 0.55, 0.75, 0.5, 0.5, 0.4],
                    [0.3, 0.2, 0.2, 0.15, 0.2, 0.9],
                    [0.2, 0.4, 0.45, 0.3, 0.35, 0.7],
                ],
                [
                    [0.75, 0.8, 0.7, 0.85, 0.7, 0.2],
                    [0.6, 0.6, 0.5, 0.65, 0.55, 0.4],
                    [0.3, 0.25, 0.15, 0.2, 0.25, 0.8],
                    [0.2, 0.4, 0.3, 0.4, 0.35, 0.65],
                ],
                [
                    [0.75, 0.9, 0.75, 0.7, 0.8, 0.15],
                    [0.6, 0.75, 0.5, 0.55, 0.6, 0.45],
                    [0.3, 0.3, 0.1, 0.15, 0.2, 0.9],
                    [0.2, 0.4, 0.25, 0.3, 0.35, 0.7],
                ],
                [
                    [0.75, 0.75, 0.65, 0.85, 0.8, 0.15],
                    [0.6, 0.6, 0.5, 0.7, 0.6, 0.4],
                    [0.3, 0.25, 0.15, 0.2, 0.2, 0.85],
                    [0.2, 0.4, 0.3, 0.45, 0.35, 0.65],
                ],
                [
                    [0.75, 0.85, 0.8, 0.6, 0.75, 0.2],
                    [0.6, 0.65, 0.55, 0.5, 0.55, 0.45],
                    [0.3, 0.25, 0.1, 0.15, 0.2, 0.9],
                    [0.2, 0.45, 0.3, 0.3, 0.35, 0.7],
                ],
            ],
            dtype=np.float64,
        )
