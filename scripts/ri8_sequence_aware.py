"""RI-8: correct-outcome ordered read-pair frequency bonus."""
from ri5_rich_k_state import run_experiment


def verdict(results):
    gains = {c: {n: 100*(r['final_routing_mean']-rows['beta=0']['final_routing_mean']) for n, r in rows.items()} for c, rows in results.items()}
    kept = [name for name in results['dataops'] if name != 'beta=0' and all(g[name] >= 2 for g in gains.values())]
    return dict(keep=bool(kept), kept_betas=kept, gains_pp=gains,
                criterion='same beta improves routing >=2pp at B=2 on both tested copilots',
                per_copilot_candidates={c: [n for n, v in g.items() if v >= 2] for c, g in gains.items()})


if __name__ == '__main__':
    run_experiment('ri8', 'ri8_sequence_aware.json', {f'beta={v:g}': {'beta': v} for v in [0, .1, .5, 1.]}, ['dataops', 'soc'], verdict,
                   notes=['One ordered C matrix per category; increment selected adjacent pair after a correct verified decision. No diagonal reads. Evaluation never updates C.',
                          'C is correct-outcome frequency, not a success rate conditional on pair attempts; selection-frequency confounding is part of this probe.'])
