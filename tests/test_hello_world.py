"""
tests/test_hello_world.py — Hello World smoke tests.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_hello_world_factor_vector_length():
    from examples.hello_world.factors import compute_factor_vector
    fv = compute_factor_vector({"score_a": 0.8, "score_b": 0.6})
    assert len(fv) == 2
    assert all(0 <= v <= 1 for v in fv)


def test_hello_world_iks_cold_start():
    import numpy as np
    from gae import build_profile_scorer, KernelType
    from examples.hello_world.config import HelloWorldConfig
    from copilot_sdk.framework.iks_base import compute_iks

    cfg = HelloWorldConfig()
    scorer = build_profile_scorer(
        categories=cfg.categories, actions=cfg.actions,
        centroids=cfg.get_initial_centroids(),
        n_factors=cfg.n_factors, kernel=KernelType.L2)
    mu_zero = np.full_like(scorer.centroids, 0.5)
    iks = compute_iks(scorer.centroids, mu_zero, cfg.d_max)
    assert iks["current"] == 0.0, f"Expected 0.0 cold start IKS, got {iks['current']}"


def test_hello_world_demo_runs():
    import numpy as np
    from gae import build_profile_scorer, KernelType
    from examples.hello_world.config import HelloWorldConfig
    from examples.hello_world.factors import compute_factor_vector
    from copilot_sdk.framework.iks_base import compute_iks

    cfg    = HelloWorldConfig()
    scorer = build_profile_scorer(
        categories=cfg.categories, actions=cfg.actions,
        centroids=cfg.get_initial_centroids(),
        n_factors=cfg.n_factors, kernel=KernelType.L2)
    mu_zero = np.full_like(scorer.centroids, 0.5)

    events = [
        {"id": "E1", "category": "low_risk",  "score_a": 0.9, "score_b": 0.8},
        {"id": "E2", "category": "high_risk", "score_a": 0.2, "score_b": 0.1},
        {"id": "E3", "category": "low_risk",  "score_a": 0.7, "score_b": 0.6},
    ]
    results = []
    for event in events:
        fv     = compute_factor_vector(event)
        cat_i  = cfg.get_category_index(event["category"])
        result = scorer.score(np.array(fv), cat_i)
        results.append(result)
    assert len(results) == 3
    iks = compute_iks(scorer.centroids, mu_zero, cfg.d_max)
    assert "current" in iks
