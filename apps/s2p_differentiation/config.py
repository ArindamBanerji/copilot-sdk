"""APP-4A configuration bound to the real S2P preset shape."""

from examples.jm_reference.generator import GeneratorConfig
from examples.jm_reference.oracle import OracleConfig
from copilot_sdk.scoring.presets.s2p import S2PPreset


S2P_CATEGORIES = [
    "price_variance",
    "quantity_mismatch",
    "duplicate_risk",
    "contract_gap",
    "format_compliance",
]
S2P_ACTIONS = [
    "auto_approve",
    "hold_for_review",
    "escalate_to_buyer",
    "flag_leakage",
    "refer_to_specialist",
]
S2P_FACTORS = [
    "match_status",
    "amount_variance_ratio",
    "duplicate_score",
    "supplier_exception_history",
    "payment_terms_impact",
    "commodity_index_correlation",
    "tax_regulatory_compliance",
    "environmental_risk",
]

S2P_GENERATOR = GeneratorConfig(
    seed=42,
    n_decisions=500,
    n_categories=len(S2P_CATEGORIES),
    n_factors=len(S2P_FACTORS),
    category_names=S2P_CATEGORIES,
    factor_names=S2P_FACTORS,
    disruption_decision=300,
    disruption_categories=[2, 3],
)

S2P_ORACLE = OracleConfig(
    seed=99,
    n_categories=len(S2P_CATEGORIES),
    n_actions=len(S2P_ACTIONS),
    n_factors=len(S2P_FACTORS),
    category_names=S2P_CATEGORIES,
    action_names=S2P_ACTIONS,
    factor_names=S2P_FACTORS,
    epsilon_firm=0.20,
    # Start from the production S2P bootstrap prior, then apply the oracle's
    # independent displacement.  This makes the governed arm's learning
    # problem faithful to the real domain rather than an unrelated random
    # centroid task.
    canonical_prior=S2PPreset().bootstrap_centroids,
)

HIGH_SEVERITY_CATEGORIES = {"duplicate_risk", "contract_gap"}
