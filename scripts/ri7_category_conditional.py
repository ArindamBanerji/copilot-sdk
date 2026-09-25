"""RI-7: checkpoint-selected per-category UCB exploration strength."""
from ri5_rich_k_state import COPILOTS, run_experiment


def verdict(results):
    control = {c: r['UNIFORM-GREEDY']['final_routing_mean'] for c, r in results.items()}
    best, worst = max(control, key=control.get), min(control, key=control.get)
    gaps = {c: r['CATEGORY-ADAPTIVE']['final_routing_mean']-control[c] for c, r in results.items()}
    starv = {c: r['CATEGORY-ADAPTIVE']['starvation'] for c, r in results.items()}
    return dict(keep=max(starv.values()) <= .15 and gaps[best] >= -.02 and gaps[worst] > 0,
                best_control_copilot=best, worst_control_copilot=worst, routing_deltas_pp={c: 100*v for c, v in gaps.items()},
                starvation=starv, criterion='starvation <=15% on all; routing loss <=2pp on best greedy copilot; improvement on worst')


if __name__ == '__main__':
    run_experiment('ri7', 'ri7_category_conditional.json', {'UNIFORM-GREEDY': {}, 'UNIFORM-UCB-0.5': {'mode': 'ucb', 'c': .5}, 'CATEGORY-ADAPTIVE': {'mode': 'adaptive'}}, COPILOTS, verdict,
                   notes=['UCB = Q + c*sigma_centroid/sqrt(N_d+1), matching the existing RV-1 bonus; c is .5 above 30% baseline-weight cells, .25 from 10% through 30%, and zero below 10%.',
                          'Mode starts at c=.5 (all K=.5), then updates every 50 decisions. Reported starvation uses never-read counts; baseline-weight starvation driving the policy is retained separately.'])
