"""
VLD Experiments v6 — Statistical Significance + Showcase Scenario Generation
==============================================================================
EX-10: Bootstrap 95% CI on key claims from v4/v5 data.
DG-3:  Generate 3 showcase scenarios per copilot (S3/S4/S6).

Usage: python vld_experiments_v6.py [output_dir]
"""

import sys, os, json
import numpy as np
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.size': 10, 'axes.facecolor': '#FAFAFA',
    'figure.facecolor': '#FFFFFF', 'axes.grid': True,
    'grid.alpha': 0.3, 'axes.spines.top': False, 'axes.spines.right': False,
})

OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "./pub_charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# Reuse ScenarioGenerator + VLDEngine from v5
# ═══════════════════════════════════════════════════════════════

class ScenarioGenerator:
    def __init__(self, d=6, A=4, seed=42):
        self.rng = np.random.default_rng(seed)
        self.d = d
        self.A = A
        self.mu = self._gen_centroids()
        self.sigma = self.rng.uniform(0.05, 0.30, d)

    def _gen_centroids(self):
        mu = self.rng.uniform(0.15, 0.85, (self.A, self.d))
        for _ in range(200):
            ok = True
            for i in range(self.A):
                for j in range(i+1, self.A):
                    if np.linalg.norm(mu[i] - mu[j]) < 0.25:
                        mu[j] = self.rng.uniform(0.15, 0.85, self.d)
                        ok = False
            if ok:
                break
        return mu

    def generate(self, n=500, situation_mix=None):
        if situation_mix is None:
            situation_mix = {'S1': 0.20, 'S2': 0.10, 'S3': 0.25,
                            'S4': 0.25, 'S5': 0.10, 'S6': 0.10}
        scenarios = []
        for sit, frac in situation_mix.items():
            for _ in range(int(n * frac)):
                s = getattr(self, '_gen_' + sit.lower())()
                s['situation'] = sit
                scenarios.append(s)
        while len(scenarios) < n:
            s = self._gen_s3(); s['situation'] = 'S3'; scenarios.append(s)
        self.rng.shuffle(scenarios)
        return scenarios

    def _gen_s1(self):
        gt = self.rng.integers(0, self.A)
        v = self.mu[gt] + self.rng.normal(0, 0.05, self.d)
        return self._build(np.clip(v, 0, 1), gt, [], [])

    def _gen_s2(self):
        gt = self.rng.integers(0, self.A)
        v = np.mean(self.mu, axis=0) + self.rng.normal(0, 0.08, self.d)
        return self._build(np.clip(v, 0, 1), gt, list(range(self.d)), [])

    def _gen_s3(self):
        gt = self.rng.integers(0, self.A)
        wrong = (gt + 1 + self.rng.integers(0, self.A - 1)) % self.A
        v = self.mu[gt].copy() + self.rng.normal(0, 0.05, self.d)
        n_wrong = int(self.rng.integers(1, 3))
        wrong_dims = list(self.rng.choice(self.d, size=n_wrong, replace=False))
        for k in wrong_dims:
            v[k] = self.mu[wrong, k] + self.rng.normal(0, 0.05)
        return self._build(np.clip(v, 0, 1), gt, wrong_dims, [])

    def _gen_s4(self):
        gt = self.rng.integers(0, self.A)
        wrong1 = (gt + 1 + self.rng.integers(0, self.A - 1)) % self.A
        v = self.mu[gt].copy() + self.rng.normal(0, 0.05, self.d)
        wrong_dims = list(self.rng.choice(self.d, size=min(3, self.d), replace=False))
        v[wrong_dims[0]] = self.mu[wrong1, wrong_dims[0]] + self.rng.normal(0, 0.05)
        if len(wrong_dims) > 1:
            wrong2 = (gt + 2) % self.A if self.A > 2 else wrong1
            v[wrong_dims[1]] = (self.mu[gt, wrong_dims[1]] + self.mu[wrong2, wrong_dims[1]]) / 2
        if len(wrong_dims) > 2:
            v[wrong_dims[2]] = self.mu[wrong1, wrong_dims[2]] * 0.6 + self.mu[gt, wrong_dims[2]] * 0.4
        return self._build(np.clip(v, 0, 1), gt, wrong_dims, [])

    def _gen_s5(self):
        gt = self.rng.integers(0, self.A)
        wrong = (gt + 1 + self.rng.integers(0, self.A - 1)) % self.A
        v = self.mu[gt].copy() + self.rng.normal(0, 0.05, self.d)
        wrong_dims = list(self.rng.choice(self.d, size=2, replace=False))
        for k in wrong_dims:
            v[k] = self.mu[wrong, k] + self.rng.normal(0, 0.05)
        remaining = [k for k in range(self.d) if k not in wrong_dims]
        n_mis = min(2, len(remaining))
        mis_dims = list(self.rng.choice(remaining, size=n_mis, replace=False))
        return self._build(np.clip(v, 0, 1), gt, wrong_dims, mis_dims)

    def _gen_s6(self):
        gt = self.rng.integers(0, self.A)
        wrong = (gt + 1 + self.rng.integers(0, self.A - 1)) % self.A
        mid = (self.mu[gt] + self.mu[wrong]) / 2
        direction = self.mu[wrong] - self.mu[gt]
        norm = np.linalg.norm(direction)
        if norm > 0: direction = direction / norm
        v = mid + 0.08 * direction + self.rng.normal(0, 0.03, self.d)
        n_needed = int(self.rng.integers(2, min(4, self.d + 1)))
        needed = list(self.rng.choice(self.d, size=n_needed, replace=False))
        return self._build(np.clip(v, 0, 1), gt, needed, [], compositional=True)

    def _build(self, v, gt, informative_dims, misleading_dims, compositional=False):
        evidence = {}
        for k in range(self.d):
            if k in informative_dims:
                target = self.mu[gt, k]
                if compositional:
                    target = v[k] + 0.6 * (target - v[k])
                evidence[k] = {
                    'value': float(np.clip(target + self.rng.normal(0, 0.03), 0, 1)),
                    'confidence': float(self.rng.uniform(0.7, 1.0)),
                    'type': 'informative',
                }
            elif k in misleading_dims:
                wrong_a = (gt + 1) % self.A
                evidence[k] = {
                    'value': float(np.clip(self.mu[wrong_a, k] + self.rng.normal(0, 0.05), 0, 1)),
                    'confidence': float(self.rng.uniform(0.4, 0.8)),
                    'type': 'misleading',
                }
            else:
                evidence[k] = {
                    'value': float(np.clip(v[k] + self.rng.normal(0, 0.03), 0, 1)),
                    'confidence': float(self.rng.uniform(0.5, 0.9)),
                    'type': 'neutral',
                }
        return {
            'v_surface': v, 'gt_action': gt, 'evidence': evidence,
            'informative_dims': informative_dims, 'misleading_dims': misleading_dims,
            'compositional': compositional,
        }


class VLDEngine:
    def __init__(self, mu, sigma, tau=0.1):
        self.mu = mu.copy()
        self.sigma = sigma.copy()
        self.tau = tau
        self.A = mu.shape[0]
        self.d = mu.shape[1]
        self.centroid_mean = np.mean(mu, axis=0)

    def score(self, v):
        dists = np.array([np.sum((1/self.sigma**2) * (v - self.mu[a])**2)
                         for a in range(self.A)])
        logits = -dists / self.tau
        logits -= np.max(logits)
        P = np.exp(logits) / np.sum(np.exp(logits))
        return int(np.argmax(P)), P

    def top2(self, P):
        order = np.argsort(-P)
        return int(order[0]), int(order[1])

    def Q_additive(self, v, P, enriched_set=None):
        a1, a2 = self.top2(P)
        Q = np.zeros(self.d)
        for k in range(self.d):
            if enriched_set and k in enriched_set:
                Q[k] = -1; continue
            prec = 1.0 / max(self.sigma[k]**2, 0.001) / 100.0
            disc = abs(self.mu[a1, k] - self.mu[a2, k])
            unc = abs((v[k] - self.mu[a1, k])**2 - (v[k] - self.mu[a2, k])**2)
            Q[k] = prec + disc + unc
        return Q

    def Q_graphrag(self, v, P, enriched_set=None):
        Q = np.zeros(self.d)
        for k in range(self.d):
            if enriched_set and k in enriched_set:
                Q[k] = -1; continue
            Q[k] = abs(v[k] - self.centroid_mean[k])
        return Q

    def V_raw(self, v, k, ev):
        v_new = v.copy(); v_new[k] = ev['value']; return v_new

    def investigate(self, scenario, budget, q_func=None):
        if q_func is None: q_func = self.Q_additive
        v = scenario['v_surface'].copy()
        enriched_set = set()
        for step in range(budget):
            _, P = self.score(v)
            Q = q_func(v, P, enriched_set)
            if np.max(Q) <= 0: break
            k_star = int(np.argmax(Q))
            v = self.V_raw(v, k_star, scenario['evidence'][k_star])
            enriched_set.add(k_star)
        a, _ = self.score(v)
        return {'correct': a == scenario['gt_action']}

    def single_pass(self, scenario):
        a, _ = self.score(scenario['v_surface'])
        return {'correct': a == scenario['gt_action']}

    def random_inv(self, scenario, budget, rng):
        v = scenario['v_surface'].copy()
        dims = list(range(self.d)); rng.shuffle(dims)
        for k in dims[:budget]:
            v = self.V_raw(v, k, scenario['evidence'][k])
        a, _ = self.score(v)
        return {'correct': a == scenario['gt_action']}

    def exhaustive(self, scenario):
        v = scenario['v_surface'].copy()
        for k in range(self.d):
            v = self.V_raw(v, k, scenario['evidence'][k])
        a, _ = self.score(v)
        return {'correct': a == scenario['gt_action']}


# ═══════════════════════════════════════════════════════════════
# EX-10: BOOTSTRAP SIGNIFICANCE
# ═══════════════════════════════════════════════════════════════

def bootstrap_ci(results_a, results_b, n_boot=10000, alpha=0.05):
    """Bootstrap confidence interval on accuracy difference A - B."""
    rng = np.random.default_rng(42)
    n = len(results_a)
    diffs = np.array(results_a, dtype=float) - np.array(results_b, dtype=float)
    boot_means = np.zeros(n_boot)
    for i in range(n_boot):
        sample = rng.choice(diffs, size=n, replace=True)
        boot_means[i] = np.mean(sample)
    lo = float(np.percentile(boot_means, 100 * alpha / 2))
    hi = float(np.percentile(boot_means, 100 * (1 - alpha / 2)))
    mean_diff = float(np.mean(diffs))
    p_value = float(np.mean(boot_means <= 0))  # one-sided: P(diff <= 0)
    return {'mean': round(mean_diff, 4), 'ci_lo': round(lo, 4),
            'ci_hi': round(hi, 4), 'p_value': round(p_value, 4)}


def exp_significance():
    """Bootstrap 95% CI on key accuracy gaps."""
    print("\n" + "=" * 65)
    print("EX-10: Statistical Significance (Bootstrap 95% CI)")
    print("=" * 65)

    gen = ScenarioGenerator(d=6, A=4, seed=42)
    scenarios = gen.generate(n=500)
    engine = VLDEngine(gen.mu, gen.sigma)
    rng = np.random.default_rng(99)

    # Collect per-scenario results for each method
    sp_results = [engine.single_pass(s)['correct'] for s in scenarios]
    rand_results = [engine.random_inv(s, 2, np.random.default_rng(99 + i))['correct']
                    for i, s in enumerate(scenarios)]
    vld_results = [engine.investigate(s, 2)['correct'] for s in scenarios]
    grag_results = [engine.investigate(s, 2, engine.Q_graphrag)['correct'] for s in scenarios]
    exh_results = [engine.exhaustive(s)['correct'] for s in scenarios]

    comparisons = [
        ('VLD vs Single-Pass', vld_results, sp_results),
        ('VLD vs Random', vld_results, rand_results),
        ('VLD vs GraphRAG', vld_results, grag_results),
        ('VLD vs Exhaustive', vld_results, exh_results),
        ('GraphRAG vs Random', grag_results, rand_results),
    ]

    results = {}
    print("\n  Comparison                Mean Δ    95% CI            p-value")
    print("  " + "-" * 65)
    for name, a, b in comparisons:
        ci = bootstrap_ci(a, b)
        results[name] = ci
        sig = "***" if ci['p_value'] < 0.001 else "**" if ci['p_value'] < 0.01 else "*" if ci['p_value'] < 0.05 else "ns"
        print("  " + name.ljust(25) +
              str(ci['mean']).ljust(10) +
              "[" + str(ci['ci_lo']) + ", " + str(ci['ci_hi']) + "]".ljust(20) +
              str(ci['p_value']).ljust(8) + sig)

    # Per-situation VLD vs Random
    print("\n  Per-situation VLD vs Random:")
    for sit in ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']:
        idx = [i for i, s in enumerate(scenarios) if s['situation'] == sit]
        if len(idx) < 10:
            continue
        a = [vld_results[i] for i in idx]
        b = [rand_results[i] for i in idx]
        ci = bootstrap_ci(a, b)
        results[sit + '_VLD_vs_Random'] = ci
        sig = "***" if ci['p_value'] < 0.001 else "**" if ci['p_value'] < 0.01 else "*" if ci['p_value'] < 0.05 else "ns"
        print("    " + sit + ": mean=" + str(ci['mean']).ljust(8) +
              "CI=[" + str(ci['ci_lo']) + "," + str(ci['ci_hi']) + "]  p=" +
              str(ci['p_value']) + " " + sig)

    return results


# ═══════════════════════════════════════════════════════════════
# DG-3: SHOWCASE SCENARIO GENERATION
# ═══════════════════════════════════════════════════════════════

# Copilot factor definitions (from production)
COPILOT_FACTORS = {
    'SOC': {
        'factors': ['severity', 'recurrence', 'asset_criticality',
                    'identity_context', 'temporal_pattern', 'blast_radius'],
        'actions': ['suppress', 'monitor', 'investigate', 'escalate'],
        'tensor': '(6,4,6)',
    },
    'DataOps': {
        'factors': ['pipeline_health', 'schema_stability', 'data_freshness',
                    'dependency_impact', 'sla_proximity', 'transformation_health'],
        'actions': ['auto_resolve', 'queue', 'investigate', 'escalate', 'rollback'],
        'tensor': '(6,5,6)',
    },
    'S2P': {
        'factors': ['price_variance', 'contract_compliance', 'supplier_reliability',
                    'receipt_match', 'approval_chain'],
        'actions': ['auto_approve', 'flag_review', 'hold', 'reject', 'escalate'],
        'tensor': '(5,5,7)',
    },
    'Trading': {
        'factors': ['thesis_alignment', 'position_size', 'concentration_risk',
                    'correlation_exposure', 'timing_signal'],
        'actions': ['execute', 'reduce', 'hold'],
        'tensor': '(5,3,6)',
    },
    'Purchasing': {
        'factors': ['demand_signal', 'supplier_capacity', 'cost_variance',
                    'shelf_life', 'coverage_ratio'],
        'actions': ['reorder', 'defer', 'switch_supplier', 'escalate'],
        'tensor': '(5,4,6)',
    },
}

# Showcase scenarios per copilot — hand-designed narratives
SHOWCASE_SCENARIOS = {
    'SOC': [
        {
            'name': 'SOC-SC1: Admin Delegation Discovery (S4)',
            'situation': 'S4',
            'narrative': 'Alert on unusual PowerShell execution. Surface factors suggest low severity + low recurrence → suppress. VLD investigates identity_context → discovers admin delegation to contractor. Q recomputes, now temporal_pattern is most uncertain → Saturday 3:14am execution. Two hops flip action from suppress to escalate.',
            'surface_action': 'suppress',
            'correct_action': 'escalate',
            'informative_dims': ['identity_context', 'temporal_pattern'],
            'hops_needed': 2,
            'demo_moment': 'Watch the action change from suppress to escalate after two reads.',
        },
        {
            'name': 'SOC-SC2: Lateral Movement Chain (S6)',
            'situation': 'S6',
            'narrative': 'RDP connection alert. Each factor alone looks normal — moderate severity, first time, standard workstation. But identity (IT admin) + timing (Sunday 2am) + blast_radius (domain controller access) TOGETHER cross the boundary. No single factor changes the answer.',
            'surface_action': 'monitor',
            'correct_action': 'escalate',
            'informative_dims': ['identity_context', 'temporal_pattern', 'blast_radius'],
            'hops_needed': 3,
            'demo_moment': 'Three reads, each shifts slightly. The COMBINATION crosses the boundary.',
        },
        {
            'name': 'SOC-SC3: Clear Suppress (S1)',
            'situation': 'S1',
            'narrative': 'Windows Update service check. Low severity, high recurrence (seen 47 times), non-critical asset, service account, business hours, no blast radius. VLD correctly does NOT investigate. Margin = 0.99.',
            'surface_action': 'suppress',
            'correct_action': 'suppress',
            'informative_dims': [],
            'hops_needed': 0,
            'demo_moment': 'System says "no investigation needed." Conservation in action.',
        },
    ],
    'DataOps': [
        {
            'name': 'DO-SC1: Schema Cascade (S4)',
            'situation': 'S4',
            'narrative': 'ETL pipeline failure on billing system. Surface: pipeline unhealthy, but schema looks stable → auto_resolve. VLD checks schema_stability → discovers MATKL_V2 migration (+340K codes). Q recomputes, dependency_impact now critical → billing + AR + GL all downstream. Action flips to escalate.',
            'surface_action': 'auto_resolve',
            'correct_action': 'escalate',
            'informative_dims': ['schema_stability', 'dependency_impact'],
            'hops_needed': 2,
            'demo_moment': 'The root cause is a schema change, not the pipeline itself.',
        },
        {
            'name': 'DO-SC2: Cross-System Propagation (S6)',
            'situation': 'S6',
            'narrative': 'Data freshness alert on supplier master. Each factor is borderline: pipeline OK but slow, schema recently changed, freshness 22min (SLA 30min), 3 downstream systems. No single factor triggers escalation, but the combination of slow pipeline + recent schema change + tight SLA margin + 3 downstream dependencies crosses the threshold.',
            'surface_action': 'queue',
            'correct_action': 'investigate',
            'informative_dims': ['pipeline_health', 'schema_stability', 'sla_proximity'],
            'hops_needed': 3,
            'demo_moment': 'Three partial shifts. The SLA countdown makes the combination urgent.',
        },
        {
            'name': 'DO-SC3: Routine Pipeline Restart (S1)',
            'situation': 'S1',
            'narrative': 'Daily refresh pipeline completed with warnings. All factors nominal. Known behavior after maintenance window. VLD does not investigate.',
            'surface_action': 'auto_resolve',
            'correct_action': 'auto_resolve',
            'informative_dims': [],
            'hops_needed': 0,
            'demo_moment': 'System auto-resolves. Zero investigation cost.',
        },
    ],
    'S2P': [
        {
            'name': 'S2P-SC1: Contract Amendment (S3)',
            'situation': 'S3',
            'narrative': 'Invoice $47,200 vs PO $42,000 — 12.4% variance → flag_review. VLD checks contract_compliance → discovers Q3 amendment with 15% price escalation clause. One hop: action changes to auto_approve.',
            'surface_action': 'flag_review',
            'correct_action': 'auto_approve',
            'informative_dims': ['contract_compliance'],
            'hops_needed': 1,
            'demo_moment': 'One read. The contract amendment explains the variance.',
        },
        {
            'name': 'S2P-SC2: Supplier Pattern (S4)',
            'situation': 'S4',
            'narrative': 'Invoice from reliable supplier, small variance → auto_approve. But VLD checks receipt_match → partial delivery found. Q recomputes, supplier_reliability now uncertain → check reveals 3 recent partial deliveries. Action: hold pending receipt reconciliation.',
            'surface_action': 'auto_approve',
            'correct_action': 'hold',
            'informative_dims': ['receipt_match', 'supplier_reliability'],
            'hops_needed': 2,
            'demo_moment': 'Surface says approve. Investigation finds a pattern of partial deliveries.',
        },
        {
            'name': 'S2P-SC3: Clean Three-Way Match (S1)',
            'situation': 'S1',
            'narrative': 'Invoice matches PO and receipt exactly. Known supplier, standard terms. VLD does not investigate.',
            'surface_action': 'auto_approve',
            'correct_action': 'auto_approve',
            'informative_dims': [],
            'hops_needed': 0,
            'demo_moment': 'Auto-approved in milliseconds. Conservation saves analyst time.',
        },
    ],
    'Trading': [
        {
            'name': 'TR-SC1: Thesis Reversal (S4)',
            'situation': 'S4',
            'narrative': 'Trade proposal: buy AAPL. Position size OK, timing neutral → execute. VLD checks thesis_alignment → analyst thesis was "AI hardware cycle" but AAPL guidance just shifted to services. Q recomputes, concentration_risk now relevant → already 8% portfolio weight. Action: hold.',
            'surface_action': 'execute',
            'correct_action': 'hold',
            'informative_dims': ['thesis_alignment', 'concentration_risk'],
            'hops_needed': 2,
            'demo_moment': 'The thesis changed. Concentration makes it worse.',
        },
        {
            'name': 'TR-SC2: Correlation Trap (S3)',
            'situation': 'S3',
            'narrative': 'Buy NVDA, small position → execute. VLD checks correlation_exposure → 0.87 correlation with existing AMD position. Combined exposure exceeds 12% of portfolio in same factor. Action: reduce.',
            'surface_action': 'execute',
            'correct_action': 'reduce',
            'informative_dims': ['correlation_exposure'],
            'hops_needed': 1,
            'demo_moment': 'One read reveals hidden concentration through correlation.',
        },
        {
            'name': 'TR-SC3: Clean Entry (S1)',
            'situation': 'S1',
            'narrative': 'Buy thesis-aligned stock, small position, low correlation, good timing. VLD does not investigate.',
            'surface_action': 'execute',
            'correct_action': 'execute',
            'informative_dims': [],
            'hops_needed': 0,
            'demo_moment': 'Green light. No investigation needed.',
        },
    ],
    'Purchasing': [
        {
            'name': 'PU-SC1: Demand Spike (S3)',
            'situation': 'S3',
            'narrative': 'Reorder trigger on standard item, coverage ratio low → reorder. VLD checks demand_signal → holiday promo starting in 2 weeks, 3x normal demand expected. Standard reorder quantity insufficient. Action: reorder at 3x quantity.',
            'surface_action': 'reorder',
            'correct_action': 'reorder',  # same action, different quantity
            'informative_dims': ['demand_signal'],
            'hops_needed': 1,
            'demo_moment': 'Same action, but the investigation changes the quantity.',
        },
        {
            'name': 'PU-SC2: Supplier Risk (S4)',
            'situation': 'S4',
            'narrative': 'Standard reorder from primary supplier → reorder. VLD checks supplier_capacity → lead time doubled (factory shutdown). Q recomputes, cost_variance now relevant → secondary supplier is 15% cheaper with normal lead time. Action: switch_supplier.',
            'surface_action': 'reorder',
            'correct_action': 'switch_supplier',
            'informative_dims': ['supplier_capacity', 'cost_variance'],
            'hops_needed': 2,
            'demo_moment': 'Supplier problem leads to a better alternative.',
        },
        {
            'name': 'PU-SC3: Stable Replenishment (S1)',
            'situation': 'S1',
            'narrative': 'Regular weekly reorder. Demand stable, supplier reliable, cost unchanged, shelf life fine. VLD does not investigate.',
            'surface_action': 'reorder',
            'correct_action': 'reorder',
            'informative_dims': [],
            'hops_needed': 0,
            'demo_moment': 'Auto-reordered. Zero investigation overhead.',
        },
    ],
}


def print_showcase():
    """Print all showcase scenarios."""
    print("\n" + "=" * 65)
    print("DG-3: Showcase Scenarios (3 per copilot)")
    print("=" * 65)

    for copilot, scenarios in SHOWCASE_SCENARIOS.items():
        info = COPILOT_FACTORS[copilot]
        print("\n  ─── " + copilot + " " + info['tensor'] + " ───")
        print("  Factors: " + ", ".join(info['factors']))
        print("  Actions: " + ", ".join(info['actions']))
        for sc in scenarios:
            print("\n    " + sc['name'])
            print("    Situation: " + sc['situation'] +
                  "  |  Hops: " + str(sc['hops_needed']) +
                  "  |  " + sc['surface_action'] + " → " + sc['correct_action'])
            print("    Reads: " + ", ".join(sc['informative_dims']) if sc['informative_dims'] else "    Reads: (none)")
            print("    Demo: " + sc['demo_moment'])

    total = sum(len(v) for v in SHOWCASE_SCENARIOS.values())
    s4_count = sum(1 for v in SHOWCASE_SCENARIOS.values()
                   for sc in v if sc['situation'] == 'S4')
    s3_count = sum(1 for v in SHOWCASE_SCENARIOS.values()
                   for sc in v if sc['situation'] == 'S3')
    s6_count = sum(1 for v in SHOWCASE_SCENARIOS.values()
                   for sc in v if sc['situation'] == 'S6')
    s1_count = sum(1 for v in SHOWCASE_SCENARIOS.values()
                   for sc in v if sc['situation'] == 'S1')
    print("\n  Total: " + str(total) + " scenarios (" +
          str(s4_count) + " S4, " + str(s3_count) + " S3, " +
          str(s6_count) + " S6, " + str(s1_count) + " S1)")


# ═══════════════════════════════════════════════════════════════
# CHART
# ═══════════════════════════════════════════════════════════════

def chart_significance(results, out_dir):
    """CI bars for key comparisons."""
    comparisons = ['VLD vs Single-Pass', 'VLD vs Random',
                   'VLD vs GraphRAG', 'GraphRAG vs Random']
    vals = [results[c]['mean'] for c in comparisons]
    los = [results[c]['ci_lo'] for c in comparisons]
    his = [results[c]['ci_hi'] for c in comparisons]
    errs_lo = [v - lo for v, lo in zip(vals, los)]
    errs_hi = [hi - v for v, hi in zip(vals, his)]

    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(comparisons))
    colors = ['#2563EB' if v > 0 else '#DC2626' for v in vals]
    ax.barh(x, vals, color=colors, edgecolor='white', height=0.6)
    ax.errorbar(vals, x, xerr=[errs_lo, errs_hi], fmt='none',
                ecolor='black', capsize=5, lw=1.5)
    ax.axvline(x=0, color='black', lw=0.8)
    ax.set_yticks(x)
    ax.set_yticklabels(comparisons)
    ax.set_xlabel('Accuracy Difference (95% CI)')
    ax.set_title('Statistical Significance of VLD Advantages')
    for i, (v, p) in enumerate(zip(vals, [results[c]['p_value'] for c in comparisons])):
        sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
        ax.text(v + 0.005, i, sig, va='center', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'val6_significance.png'), dpi=200)
    plt.close()
    print("  Chart: val6_significance.png")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("VLD Experiments v6 — Statistical Significance + Showcase Scenarios")
    print("=" * 65)

    # EX-10
    sig_results = exp_significance()
    chart_significance(sig_results, OUTPUT_DIR)

    # DG-3
    print_showcase()

    # Save
    all_results = {
        'significance': sig_results,
        'showcase_scenarios': {k: [
            {key: val for key, val in sc.items() if key != 'v_surface'}
            for sc in v
        ] for k, v in SHOWCASE_SCENARIOS.items()},
        'copilot_factors': COPILOT_FACTORS,
    }

    results_path = os.path.join(OUTPUT_DIR, 'vld_experiments_v6_results.json')
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, default=lambda x: float(x) if hasattr(x, '__float__') else str(x))
    print("\nResults: " + results_path)

    print("\n" + "=" * 65)
    print("DONE.")
