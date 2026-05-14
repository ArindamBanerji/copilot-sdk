"""Source-to-Pay domain preset."""

from __future__ import annotations

import numpy as np

from copilot_sdk.scoring.config import DomainShape


class S2PPreset:
    @property
    def name(self) -> str:
        return "s2p"

    @property
    def shape(self) -> DomainShape:
        return DomainShape(
            n_categories=5,
            n_actions=5,
            n_factors=7,
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
    def bootstrap_centroids(self) -> np.ndarray:
        action_centroids = {
            "auto_approve": [0.95, 0.05, 0.02, 0.03, 0.50, 0.80, 0.95],
            "hold_for_review": [0.70, 0.30, 0.10, 0.15, 0.40, 0.50, 0.80],
            "escalate_to_buyer": [0.50, 0.60, 0.15, 0.30, 0.60, 0.30, 0.70],
            "flag_leakage": [0.80, 0.50, 0.10, 0.40, 0.70, 0.20, 0.60],
            "refer_to_specialist": [0.40, 0.40, 0.30, 0.50, 0.30, 0.40, 0.50],
        }
        centroids = [
            [action_centroids[action] for action in self.shape.action_names]
            for _category in self.shape.category_names
        ]
        return np.asarray(centroids, dtype=np.float64)
