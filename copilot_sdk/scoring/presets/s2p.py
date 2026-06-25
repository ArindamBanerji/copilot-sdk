"""Source-to-Pay domain preset."""

from __future__ import annotations

import numpy as np

from copilot_sdk.evolution import PlateauConfig
from copilot_sdk.scoring.config import DomainShape
from copilot_sdk.scoring.polarity import Polarity


class S2PPreset:
    factor_polarities = {
        "match_status": Polarity.POSITIVE,
        "amount_variance_ratio": Polarity.NEGATIVE,
        "duplicate_score": Polarity.NEGATIVE,
        "supplier_exception_history": Polarity.NEGATIVE,
        "payment_terms_impact": Polarity.POSITIVE,
        "commodity_index_correlation": Polarity.NEUTRAL,
        "tax_regulatory_compliance": Polarity.POSITIVE,
        "environmental_risk": Polarity.NEGATIVE,
    }

    @property
    def name(self) -> str:
        return "s2p"

    @property
    def shape(self) -> DomainShape:
        return DomainShape(
            n_categories=5,
            n_actions=5,
            n_factors=8,
            category_names=(
                "price_variance",
                "quantity_mismatch",
                "duplicate_risk",
                "contract_gap",
                "format_compliance",
            ),
            action_names=(
                "auto_approve",
                "hold_for_review",
                "escalate_to_buyer",
                "flag_leakage",
                "refer_to_specialist",
            ),
            factor_names=(
                "match_status",
                "amount_variance_ratio",
                "duplicate_score",
                "supplier_exception_history",
                "payment_terms_impact",
                "commodity_index_correlation",
                "tax_regulatory_compliance",
                "environmental_risk",
            ),
        )

    @property
    def penalty_ratio(self) -> float:
        return 5.0

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
        # C*A=25; window=round(10*sqrt((C*A)/20))=11; cooldown=5*window.
        return PlateauConfig(
            plateau_window=11,
            min_improvement_rate=0.20,
            plateau_cooldown=55,
        )

    @property
    def bootstrap_centroids(self) -> np.ndarray:
        action_centroids = {
            "auto_approve": [0.95, 0.05, 0.02, 0.03, 0.50, 0.80, 0.95, 0.50],
            "hold_for_review": [0.70, 0.30, 0.10, 0.15, 0.40, 0.50, 0.80, 0.50],
            "escalate_to_buyer": [0.50, 0.60, 0.15, 0.30, 0.60, 0.30, 0.70, 0.50],
            "flag_leakage": [0.80, 0.50, 0.10, 0.40, 0.70, 0.20, 0.60, 0.50],
            "refer_to_specialist": [0.40, 0.40, 0.30, 0.50, 0.30, 0.40, 0.50, 0.50],
        }
        centroids = [
            [action_centroids[action] for action in self.shape.action_names]
            for _category in self.shape.category_names
        ]
        return self.migrate_legacy_centroids(np.asarray(centroids, dtype=np.float64))

    @property
    def environmental_risk_decay(self) -> float:
        return 0.005

    def migrate_legacy_centroids(self, centroids: np.ndarray) -> np.ndarray:
        """Pad legacy seven-factor tensors to eight factors with neutral risk."""
        array = np.asarray(centroids, dtype=np.float64)
        if array.size == 0:
            return array
        if array.shape[-1] == 8:
            return array
        if array.shape[-1] == 7:
            pad = np.full((*array.shape[:-1], 1), 0.5, dtype=np.float64)
            return np.concatenate([array, pad], axis=-1)
        raise ValueError(f"s2p legacy tensor has unsupported factor width {array.shape[-1]}")

    def migrate_legacy_vector(self, vector: np.ndarray | list[float]) -> np.ndarray:
        """Pad a legacy seven-factor decision vector to eight factors."""
        array = np.asarray(vector, dtype=np.float64)
        if array.size == 0:
            return array
        if array.shape[-1] == 8:
            return array
        if array.shape[-1] == 7:
            return np.concatenate([array, np.asarray([0.5], dtype=np.float64)])
        raise ValueError(f"s2p legacy vector has unsupported factor width {array.shape[-1]}")
