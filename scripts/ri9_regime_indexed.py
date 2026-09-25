"""RI-9: pooled vs category-indexed K across a category-frequency shift."""
from ri5_rich_k_state import run_experiment


def verdict(results):
    comparisons = {}
    for c, rows in results.items():
        base, candidate = rows['SINGLE-K']['recovery'], rows['REGIME-K']['recovery']
        speed = None if base['restricted_mean_decisions'] == 0 else 1-candidate['restricted_mean_decisions']/base['restricted_mean_decisions']
        comparisons[c] = dict(speedup=speed, keep=speed is not None and speed >= .3 and candidate['censored_seeds'] == 0)
    return dict(keep=all(r['keep'] for r in comparisons.values()), comparisons=comparisons,
                criterion='post-shift recovery >=30% faster on both copilots; zero-time control cannot establish recovery gain')


if __name__ == '__main__':
    run_experiment('ri9', 'ri9_regime_indexed.json', {'SINGLE-K': {'pooled': True}, 'REGIME-K': {}}, ['trading', 'soc'], verdict,
                   notes=['Before shift, first floor(C/2) categories receive 80% probability, remaining categories 20%; after decision 250 those masses reverse. Uniform within each group. Evaluation follows the active distribution.',
                          'Production KUtilityStore is already category-indexed. SINGLE-K is a deliberately pooled ablation; REGIME-K matches production storage semantics.',
                          'No change to per-category evidence geometry; a category-frequency shift need not cause a quality drop. Recovery that is immediate is explicitly reported.'])
