"""RV-9: deterministic centroid expectimax lookahead at B=2."""
from ri5_rich_k_state import run_experiment


def verdict(results):
    rows = results['dataops']
    base = rows['GREEDY-Q']['final_routing_mean']
    return dict(gains_pp={n: 100*(r['final_routing_mean']-base) for n, r in rows.items()},
                scorer_eval_multipliers={n: r['scorer_evals']/rows['GREEDY-Q']['scorer_evals'] for n, r in rows.items()},
                adopt=False, criterion='report routing value and scorer cost of 1/2-step lookahead at B=2')


if __name__ == '__main__':
    run_experiment('rv9', 'rv9_mcts.json', {'GREEDY-Q': {}, '1-STEP': {'lookahead': 1}, '2-STEP': {'lookahead': 2}}, ['dataops'], verdict,
                   notes=['Exact finite centroid-branch expectimax, not stochastic MCTS/UCT. Current action posterior supplies branch probabilities; hypothetical evidence uses centroid values, never hidden full vector or labels.',
                          'Each candidate maximizes expected post-read probability-margin improvement, recursively through remaining B. Every hypothetical score counts in M-COST.',
                          'K learning runs in every arm. Pure margin-lookahead arms do not use K to select; they test the requested margin objective, and their maintained K is diagnostic only.',
                          'This is model-based lookahead headroom, not an oracle guarantee; saturated action posteriors may reinforce wrong actions.'])
