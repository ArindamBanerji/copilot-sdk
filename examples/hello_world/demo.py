"""
Hello World demo — score + IKS in 30 lines.
Run: python examples/hello_world/demo.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import numpy as np
from gae import build_profile_scorer, KernelType
from examples.hello_world.config import HelloWorldConfig
from examples.hello_world.factors import compute_factor_vector
from copilot_sdk.framework.iks_base import compute_iks

cfg     = HelloWorldConfig()
scorer  = build_profile_scorer(
    categories=cfg.categories, actions=cfg.actions,
    centroids=cfg.get_initial_centroids(),
    n_factors=cfg.n_factors, kernel=KernelType.L2)
mu_zero = np.full_like(scorer.mu, 0.5)

events = [
    {"id": "E1", "category": "low_risk",  "score_a": 0.9, "score_b": 0.8},
    {"id": "E2", "category": "high_risk", "score_a": 0.2, "score_b": 0.1},
    {"id": "E3", "category": "low_risk",  "score_a": 0.7, "score_b": 0.6},
]

print("copilot-sdk Hello World Demo")
print(f"Domain: 2 categories, 3 actions, 2 factors")
print()

for event in events:
    fv     = compute_factor_vector(event)
    cat_i  = cfg.get_category_index(event["category"])
    result = scorer.score(np.array(fv), cat_i)
    action = cfg.actions[result.action_index]
    print(f"  {event['id']} ({event['category']}): "
          f"factors={fv} -> {action} "
          f"(conf={result.confidence:.2f})")

iks = compute_iks(scorer.mu, mu_zero, cfg.d_max)
print()
print(f"IKS: {iks['current']:.1f} (cold start - no decisions yet)")
print("copilot-sdk: same engine, any domain.")
