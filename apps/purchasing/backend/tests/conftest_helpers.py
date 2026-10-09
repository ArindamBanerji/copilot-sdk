from __future__ import annotations


from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.graph.factory import create_graph_store


def _shape(scorer: CompoundingScorer):
    return scorer._preset.shape


def seed_green_scorer(
    domain: str = "purchasing",
    n_decisions: int = 50,
) -> CompoundingScorer:
    """Create a real scorer seeded to conservation GREEN."""
    store = create_graph_store(backend="memory", domain=domain, profile="test", env={})
    scorer = CompoundingScorer.from_preset(domain,  graph_store=store, profile="test")
    shape = _shape(scorer)
    factors = {name: 0.6 for name in shape.factor_names}
    category = str(shape.category_names[0])

    for _ in range(n_decisions):
        result = scorer.score(category=category, factors=factors)
        learn_result = scorer.learn(
            decision_id=result.decision_id,
            actual_action=result.action,
        )
        if isinstance(learn_result, dict):
            raise AssertionError(f"expected GREEN seed learn to apply, got {learn_result}")

    return scorer
