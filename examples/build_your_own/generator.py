"""Domain-agnostic synthetic metadata generator.

This deliberately reuses the APP-1 generator contract: it emits a category
and factor metadata only. It never computes correctness or labels.
"""

from examples.jm_reference.generator import GeneratorConfig, SyntheticGenerator


def make_generator(domain, *, seed=42, n_decisions=300):
    config = GeneratorConfig(
        seed=seed,
        n_decisions=n_decisions,
        n_categories=len(domain.CATEGORIES),
        n_factors=len(domain.FACTORS),
        category_names=domain.CATEGORIES,
        factor_names=domain.FACTORS,
        disruption_decision=max(1, n_decisions // 2),
        disruption_categories=[0],
    )
    return SyntheticGenerator(config)


__all__ = ["GeneratorConfig", "SyntheticGenerator", "make_generator"]
