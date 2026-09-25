"""RV-4: Q-scale invariance, risk budgets, and posterior-scale exploration."""
import math
from ri5_rich_k_state import COPILOTS, PENALTIES, run_experiment


def configs(c):
    ratio = PENALTIES[c]
    return {'UNIFORM-B2': {}, 'RISK-B2': {'risk_scale': ratio},
            'ADAPTIVE-B': {'risk_scale': ratio, 'budget': math.floor(math.log2(ratio))+1},
            'THOMPSON': {'mode': 'thompson'},
            'THOMPSON-RISK': {'mode': 'thompson', 'risk_sigma': ratio}}


def verdict(results):
    gains, invariance, posterior_gains = {}, {}, {}
    for c, rows in results.items():
        a, b = rows['UNIFORM-B2'], rows['RISK-B2']
        invariance[c] = all(x['training_routes_sha256'] == y['training_routes_sha256'] and
                            [r['eval_rows'] for r in x['checkpoints']] == [r['eval_rows'] for r in y['checkpoints']]
                            for x, y in zip(a['seed_runs'], b['seed_runs']))
        assert invariance[c], 'positive fixed Q scaling changed routing'
        gains[c] = (rows['ADAPTIVE-B']['final_routing_mean']-a['final_routing_mean'])/a['final_routing_mean']
        posterior_gains[c] = 100*(rows['THOMPSON-RISK']['final_routing_mean']-rows['THOMPSON']['final_routing_mean'])
    return dict(keep=all(gains[c] >= .05 for c in ['soc', 'dataops']) and all(gains[c] >= -1e-12 for c in ['purchasing', 'trading']),
                adaptive_relative_gains=gains, fixed_scale_exact_invariance=invariance, risk_sigma_vs_thompson_pp=posterior_gains,
                criterion='SOC and DataOps each >=5% relative routing gain; Purchasing and Trading no degradation')


if __name__ == '__main__':
    run_experiment('rv4', 'rv4_risk_sensitive.json', configs, COPILOTS, verdict,
                   notes=['Includes an unweighted Thompson comparator to isolate posterior-sigma risk effects.',
                          'Risk posterior condition multiplies sigma by penalty ratio while keeping mean Q unchanged. Scaling BOTH mean and sigma would be exactly sample-order invariant; fixed mean isolates uncertainty weighting.',
                          '5% improvement interpreted as relative routing quality; absolute percentage-point changes also retained. More reads can improve accuracy while lowering informative-read precision.'])
