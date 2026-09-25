"""RI-6: normalized-age exponential K decay under a planted evidence shift."""
from ri5_rich_k_state import run_experiment


def verdict(results):
    rows = results['dataops']
    base = rows['lambda=0']['recovery']
    comparisons = {}
    for name, row in rows.items():
        r = row['recovery']
        speed = None if base['restricted_mean_decisions'] == 0 else 1-r['restricted_mean_decisions']/base['restricted_mean_decisions']
        comparisons[name] = dict(recovery_speedup=speed,
                                 pre_shift_delta=r['pre_shift_quality']-base['pre_shift_quality'],
                                 keep=name != 'lambda=0' and speed is not None and speed >= .2 and r['pre_shift_quality'] >= base['pre_shift_quality'] and r['censored_seeds'] == 0)
    return dict(keep=any(r['keep'] for r in comparisons.values()), comparisons=comparisons,
                criterion='>=20% faster recovery without pre-shift routing loss; zero-time control has no measurable speedup')


if __name__ == '__main__':
    run_experiment('ri6', 'ri6_temporal_decay.json', {f'lambda={v:g}': {'decay': v} for v in [0, .5, 1., 2.]}, ['dataops'], verdict,
                   notes=['Decisions 1-250 corrupt/offer evidence only on dims 0,2; decisions 251-500 on dims 1,3. Other coordinates are fully observed. Centroids stay fixed.',
                          'Age is min-max normalized elapsed time since selection within the active category: most recent=0, oldest=1; ties all yield zero. Decay changes effective routing K only, not stored K.',
                          'Recovery uses held-out checkpoints 200 and 250 for pre-shift quality; training-window 201-250 metrics are separately retained. No-recovery is censored, never silently treated as success.'])
