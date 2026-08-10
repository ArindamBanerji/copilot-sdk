"""Domain-agnostic APP-1 oracle adapter.

The oracle is the only component that knows the synthetic ground truth.
Production code would replace this module with verified outcomes.
"""

from examples.jm_reference.oracle import GroundTruthOracle, OracleConfig

from .config import make_preset


def make_oracle(domain, *, seed=99):
    preset = make_preset(domain)
    config = OracleConfig(
        seed=seed,
        n_categories=len(domain.CATEGORIES),
        n_actions=len(domain.ACTIONS),
        n_factors=len(domain.FACTORS),
        category_names=domain.CATEGORIES,
        action_names=domain.ACTIONS,
        factor_names=domain.FACTORS,
        epsilon_firm=domain.EPSILON_FIRM,
        canonical_prior=preset.bootstrap_centroids,
    )
    return GroundTruthOracle(config)


def correct_action(oracle, category, factors, domain):
    """Return the verified action for one synthetic metadata record."""
    return max(
        domain.ACTIONS,
        key=lambda action: oracle.label_correct(category, action, factors),
    )


__all__ = ["GroundTruthOracle", "OracleConfig", "make_oracle", "correct_action"]
