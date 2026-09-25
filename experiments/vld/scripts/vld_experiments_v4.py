"""
VLD Experiments v4 — Unblocked Gap-Closers
============================================
Runs all experiments that have NO blockers from MAP v8.

EXP-HALT:  Fixed adaptive halting (relative improvement threshold)
EXP-GRAG:  GraphRAG comparison (embedding-based routing vs Q-based)
EXP-REACT: Simulated ReAct (LLM-cost proxy with oracle routing)
EXP-SCALE: Complexity scaling sweep (d x A)
EXP-S5:    Failure mode catalog (misleading ratio sweep)
EXP-WW:    With-without decomposition per situation (comprehensive)
EXP-COMP:  Compounding v2 (shuffled scenario order each epoch)

Usage: python vld_experiments_v4.py [output_dir]
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
# SCENARIO GENERATOR (reused from v3 with S5 ratio control)
# ═══════════════════════════════════════════════════════════════

class ScenarioGenerator:
    def __init__(self, d=6, A=4, seed=42, misleading_ratio=0.33):
        self.rng = np.random.default_rng(seed)
        self.d = d
        self.A = A
        self.misleading_ratio = misleading_ratio
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
            s = self._gen_s3()
            s['situation'] = 'S3'
            scenarios.append(s)
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
        n_wrong = 2
        wrong_dims = list(self.rng.choice(self.d, size=n_wrong, replace=False))
        for k in wrong_dims:
            v[k] = self.mu[wrong, k] + self.rng.normal(0, 0.05)
        remaining = [k for k in range(self.d) if k not in wrong_dims]
        # Controlled misleading ratio
        n_mis = max(1, int(len(remaining) * self.misleading_ratio))
        n_mis = min(n_mis, len(remaining))
        mis_dims = list(self.rng.choice(remaining, size=n_mis, replace=False))
        return self._build(np.clip(v, 0, 1), gt, wrong_dims, mis_dims)

    def _gen_s6(self):
        gt = self.rng.integers(0, self.A)
        wrong = (gt + 1 + self.rng.integers(0, self.A - 1)) % self.A
        mid = (self.mu[gt] + self.mu[wrong]) / 2
        direction = self.mu[wrong] - self.mu[gt]
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction = direction / norm
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
                    'shift': float(abs(target - v[k])),
                    'confidence': float(self.rng.uniform(0.7, 1.0)),
                    'type': 'informative',
                }
            elif k in misleading_dims:
                wrong_a = (gt + 1) % self.A
                target = self.mu[wrong_a, k]
                evidence[k] = {
                    'value': float(np.clip(target + self.rng.normal(0, 0.05), 0, 1)),
                    'shift': float(abs(target - v[k])),
                    'confidence': float(self.rng.uniform(0.4, 0.8)),
                    'type': 'misleading',
                }
            else:
                evidence[k] = {
                    'value': float(np.clip(v[k] + self.rng.normal(0, 0.03), 0, 1)),
                    'shift': float(abs(self.rng.normal(0, 0.03))),
                    'confidence': float(self.rng.uniform(0.5, 0.9)),
                    'type': 'neutral',
                }
        return {
            'v_surface': v, 'gt_action': gt, 'evidence': evidence,
            'informative_dims': informative_dims, 'misleading_dims': misleading_dims,
            'compositional': compositional,
        }


# ═══════════════════════════════════════════════════════════════
# VLD ENGINE (from v3, with GraphRAG + ReAct routing)
# ═══════════════════════════════════════════════════════════════

class VLDEngine:
    def __init__(self, mu, sigma, tau=0.1):
        self.mu = mu.copy()
        self.sigma = sigma.copy()
        self.sigma_initial = sigma.copy()
        self.tau = tau
        self.A = mu.shape[0]
        self.d = mu.shape[1]
        self.past_utility = np.ones(self.d) * 0.5
        # For GraphRAG: precompute centroid embeddings
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

    def margin(self, P):
        s = np.sort(P)[::-1]
        return float(s[0] - s[1])

    # ── Q variants ──

    def Q_additive(self, v, P, enriched_set=None):
        """Additive Q: precision + discriminative + margin_sensitivity."""
        a1, a2 = self.top2(P)
        Q = np.zeros(self.d)
        for k in range(self.d):
            if enriched_set and k in enriched_set:
                Q[k] = -1
                continue
            prec = 1.0 / max(self.sigma[k]**2, 0.001) / 100.0
            disc = abs(self.mu[a1, k] - self.mu[a2, k])
            unc = abs((v[k] - self.mu[a1, k])**2 - (v[k] - self.mu[a2, k])**2)
            Q[k] = prec + disc + unc
        return Q

    def Q_random(self, v, P, enriched_set=None):
        Q = np.random.default_rng().uniform(0, 1, self.d)
        if enriched_set:
            for k in enriched_set:
                Q[k] = -1
        return Q

    def Q_graphrag(self, v, P, enriched_set=None):
        """GraphRAG-style: route by embedding distance from centroid mean.
        Reads dimensions where v[k] is MOST DIFFERENT from the mean —
        i.e., most 'surprising' dimensions."""
        Q = np.zeros(self.d)
        for k in range(self.d):
            if enriched_set and k in enriched_set:
                Q[k] = -1
                continue
            Q[k] = abs(v[k] - self.centroid_mean[k])
        return Q

    def Q_react_oracle(self, v, P, enriched_set=None, scenario=None):
        """Simulated ReAct: oracle routing (reads informative dims first).
        Represents LLM with perfect domain knowledge — upper bound for ReAct."""
        Q = np.zeros(self.d)
        for k in range(self.d):
            if enriched_set and k in enriched_set:
                Q[k] = -1
                continue
            if scenario and k in scenario.get('informative_dims', []):
                Q[k] = 10.0  # oracle priority
            else:
                Q[k] = 0.1
        return Q

    # ── V update ──

    @staticmethod
    def V_raw(v, k, ev):
        v_new = v.copy()
        v_new[k] = ev['value']
        return v_new

    @staticmethod
    def V_gated(v, k, ev):
        v_new = v.copy()
        c = ev['confidence']
        v_new[k] = c * ev['value'] + (1-c) * v[k]
        return v_new

    # ── Investigation ──

    def investigate(self, scenario, budget, q_func, v_func=None,
                    halt='fixed', halt_threshold=0.1, q_kwargs=None):
        if v_func is None:
            v_func = self.V_raw
        if q_kwargs is None:
            q_kwargs = {}

        v = scenario['v_surface'].copy()
        enriched_set = set()
        trace = []
        prev_improvement = 999

        for step in range(budget):
            a_before, P = self.score(v)
            margin_before = self.margin(P)

            # Adaptive halt: relative improvement
            if step > 0 and halt == 'relative':
                if len(trace) >= 2:
                    imp_prev = trace[-1]['margin_after'] - trace[-1]['margin_before']
                    imp_prev2 = trace[-2]['margin_after'] - trace[-2]['margin_before']
                    if abs(imp_prev2) > 0 and imp_prev / max(abs(imp_prev2), 0.001) < halt_threshold:
                        break
                elif len(trace) == 1:
                    imp = trace[-1]['margin_after'] - trace[-1]['margin_before']
                    if imp < 0.01:
                        break

            Q = q_func(v, P, enriched_set, **q_kwargs)
            if np.max(Q) <= 0:
                break

            k_star = int(np.argmax(Q))
            v_before = v.copy()
            v = v_func(v, k_star, scenario['evidence'][k_star])
            enriched_set.add(k_star)

            a_after, P_after = self.score(v)
            trace.append({
                'step': step, 'dim': k_star,
                'action_before': a_before, 'action_after': a_after,
                'flipped': a_before != a_after,
                'evidence_type': scenario['evidence'][k_star]['type'],
                'margin_before': margin_before,
                'margin_after': float(self.margin(P_after)),
                'shift': float(np.linalg.norm(v - v_before)),
            })

        final_action, final_P = self.score(v)
        return {
            'final_action': final_action,
            'correct': final_action == scenario['gt_action'],
            'trace': trace,
            'n_hops': len(trace),
            'final_margin': float(self.margin(final_P)),
        }

    def single_pass(self, scenario):
        a, _ = self.score(scenario['v_surface'])
        return {'final_action': a, 'correct': a == scenario['gt_action']}

    def random_inv(self, scenario, budget, rng):
        v = scenario['v_surface'].copy()
        dims = list(range(self.d))
        rng.shuffle(dims)
        for k in dims[:budget]:
            v = self.V_raw(v, k, scenario['evidence'][k])
        a, _ = self.score(v)
        return {'final_action': a, 'correct': a == scenario['gt_action']}

    def exhaustive(self, scenario):
        v = scenario['v_surface'].copy()
        for k in range(self.d):
            v = self.V_raw(v, k, scenario['evidence'][k])
        a, _ = self.score(v)
        return {'final_action': a, 'correct': a == scenario['gt_action']}

    def update_sigma(self, scenario, result):
        if not result['correct']:
            return
        for t in result['trace']:
            k = t['dim']
            if t['evidence_type'] == 'informative':
                self.sigma[k] = max(0.02, self.sigma[k] * 0.97)
            elif t['evidence_type'] == 'misleading':
                self.sigma[k] = min(0.40, self.sigma[k] * 1.03)


# ═══════════════════════════════════════════════════════════════
# EXPERIMENTS
# ═══════════════════════════════════════════════════════════════

def exp_halt_fixed(engine, scenarios):
    """EXP-HALT: Relative-improvement halting."""
    print("\n--- Adaptive Halting (relative improvement) ---")

    configs = [
        ('fixed_B1', 'fixed', 1, 0),
        ('fixed_B2', 'fixed', 2, 0),
        ('fixed_B3', 'fixed', 3, 0),
        ('fixed_B4', 'fixed', 4, 0),
        ('relative_0.05', 'relative', 6, 0.05),
        ('relative_0.10', 'relative', 6, 0.10),
        ('relative_0.20', 'relative', 6, 0.20),
        ('relative_0.50', 'relative', 6, 0.50),
    ]

    results = {}
    for name, halt, budget, threshold in configs:
        runs = [engine.investigate(s, budget, engine.Q_additive,
                                   halt=halt, halt_threshold=threshold)
                for s in scenarios]
        acc = sum(1 for r in runs if r['correct']) / len(scenarios)
        avg_hops = np.mean([r['n_hops'] for r in runs])
        results[name] = {'accuracy': round(acc, 3), 'avg_hops': round(avg_hops, 2)}
        print("  " + name.ljust(20) + "acc=" + str(round(acc, 3)).ljust(8) +
              "hops=" + str(round(avg_hops, 2)))

    return results


def exp_graphrag_react(engine, scenarios, budget=2, rng_seed=99):
    """EXP-GRAG + EXP-REACT: Compare VLD vs GraphRAG vs ReAct."""
    rng = np.random.default_rng(rng_seed)

    print("\n--- GraphRAG / ReAct Comparison (budget=" + str(budget) + ") ---")

    # Compute ALL methods ONCE per scenario, store results
    per_scenario = []
    for s in scenarios:
        row = {
            'situation': s['situation'],
            'single_pass': engine.single_pass(s)['correct'],
            'random': engine.random_inv(s, budget, rng)['correct'],
            'VLD_additive': engine.investigate(s, budget, engine.Q_additive)['correct'],
            'GraphRAG': engine.investigate(s, budget, engine.Q_graphrag)['correct'],
            'ReAct_oracle': engine.investigate(s, budget, engine.Q_react_oracle,
                                              q_kwargs={'scenario': s})['correct'],
            'exhaustive': engine.exhaustive(s)['correct'],
        }
        per_scenario.append(row)

    # Overall
    methods = {}
    for m in ['single_pass', 'random', 'VLD_additive', 'GraphRAG', 'ReAct_oracle', 'exhaustive']:
        methods[m] = sum(1 for r in per_scenario if r[m]) / len(per_scenario)

    # Per-situation
    by_sit = defaultdict(lambda: {m: [] for m in ['single_pass', 'random', 'VLD_additive', 'GraphRAG', 'ReAct_oracle', 'exhaustive']})
    for r in per_scenario:
        sit = r['situation']
        for m in ['single_pass', 'random', 'VLD_additive', 'GraphRAG', 'ReAct_oracle', 'exhaustive']:
            by_sit[sit][m].append(r[m])

    print("  Method           Accuracy")
    for m in sorted(methods.keys()):
        print("  " + m.ljust(20) + str(round(methods[m], 3)))

    print("\n  Per-situation:")
    print("  Sit   SP     Rnd    VLD    GRAG   ReAct  Exh    n")
    for sit in sorted(by_sit.keys()):
        n = len(by_sit[sit]['single_pass'])
        row = "  " + sit + "   "
        for m in ['single_pass', 'random', 'VLD_additive', 'GraphRAG', 'ReAct_oracle', 'exhaustive']:
            row += str(round(np.mean(by_sit[sit][m]), 2)).ljust(7)
        row += str(n)
        print(row)

    return methods, dict(by_sit)


def exp_complexity_scaling(budget=2):
    """EXP-SCALE: VLD advantage vs d x (A-1)."""
    print("\n--- Complexity Scaling (d x A sweep) ---")

    configs = [
        (4, 2), (4, 4), (6, 2), (6, 4), (6, 6),
        (8, 4), (8, 6), (10, 4), (10, 6),
    ]

    results = []
    rng = np.random.default_rng(99)

    for d, A in configs:
        if A < 2:
            continue
        gen = ScenarioGenerator(d=d, A=A, seed=42)
        scenarios = gen.generate(n=300)
        engine = VLDEngine(gen.mu, gen.sigma)

        sp_acc = sum(1 for s in scenarios if engine.single_pass(s)['correct']) / len(scenarios)
        rand_acc = sum(1 for s in scenarios if engine.random_inv(s, budget, rng)['correct']) / len(scenarios)
        vld_acc = sum(1 for s in scenarios if engine.investigate(s, budget, engine.Q_additive)['correct']) / len(scenarios)
        exh_acc = sum(1 for s in scenarios if engine.exhaustive(s)['correct']) / len(scenarios)

        complexity = d * (A - 1)
        vld_advantage = vld_acc - rand_acc

        results.append({
            'd': d, 'A': A, 'complexity': complexity,
            'sp': round(sp_acc, 3), 'random': round(rand_acc, 3),
            'vld': round(vld_acc, 3), 'exhaustive': round(exh_acc, 3),
            'vld_advantage': round(vld_advantage, 3),
        })

        print("  d=" + str(d) + " A=" + str(A) + " (dxA-1=" + str(complexity) + ")" +
              "  SP=" + str(round(sp_acc, 3)) +
              "  Rnd=" + str(round(rand_acc, 3)) +
              "  VLD=" + str(round(vld_acc, 3)) +
              "  Adv=" + str(round(vld_advantage, 3)))

    return results


def exp_s5_failure_modes(d=6, A=4, budget=2):
    """EXP-S5: Misleading ratio sweep."""
    print("\n--- S5 Failure Mode Sweep (misleading ratio) ---")

    ratios = [0.0, 0.17, 0.33, 0.50, 0.67, 0.83]
    results = []

    for ratio in ratios:
        rng = np.random.default_rng(99)  # fresh rng per ratio
        gen = ScenarioGenerator(d=d, A=A, seed=42, misleading_ratio=ratio)
        scenarios = gen.generate(n=200, situation_mix={'S5': 1.0})
        engine = VLDEngine(gen.mu, gen.sigma)

        sp_acc = sum(1 for s in scenarios if engine.single_pass(s)['correct']) / len(scenarios)
        exh_acc = sum(1 for s in scenarios if engine.exhaustive(s)['correct']) / len(scenarios)

        # Compute random and VLD once per scenario
        rand_results = [engine.random_inv(s, budget, rng)['correct'] for s in scenarios]
        vld_results = [engine.investigate(s, budget, engine.Q_additive)['correct'] for s in scenarios]

        rand_acc = sum(rand_results) / len(scenarios)
        vld_acc = sum(vld_results) / len(scenarios)
        vld_hurts = sum(1 for r, v in zip(rand_results, vld_results) if r and not v) / len(scenarios)

        results.append({
            'ratio': ratio,
            'sp': round(sp_acc, 3), 'random': round(rand_acc, 3),
            'vld': round(vld_acc, 3), 'exhaustive': round(exh_acc, 3),
            'vld_hurts_pct': round(vld_hurts * 100, 1),
        })

        print("  ratio=" + str(ratio).ljust(6) +
              "  SP=" + str(round(sp_acc, 3)) +
              "  Rnd=" + str(round(rand_acc, 3)) +
              "  VLD=" + str(round(vld_acc, 3)) +
              "  Exh=" + str(round(exh_acc, 3)) +
              "  Hurts=" + str(round(vld_hurts*100, 1)) + "%")

    return results


def exp_with_without_comprehensive(engine, scenarios, budget=2, rng_seed=99):
    """EXP-WW: Comprehensive with-without across all methods."""
    rng = np.random.default_rng(rng_seed)

    print("\n--- With-Without Comprehensive ---")

    # Per situation, per method pair
    pairs = [
        ('VLD_vs_SP', 'vld', 'sp'),
        ('VLD_vs_Random', 'vld', 'random'),
        ('VLD_vs_GraphRAG', 'vld', 'graphrag'),
        ('GraphRAG_vs_SP', 'graphrag', 'sp'),
        ('GraphRAG_vs_Random', 'graphrag', 'random'),
    ]

    by_sit = defaultdict(lambda: {p[0]: {'saves': 0, 'hurts': 0, 'both_right': 0, 'both_wrong': 0}
                                  for p in pairs})
    by_sit_total = defaultdict(int)

    for s in scenarios:
        sit = s['situation']
        by_sit_total[sit] += 1

        sp = engine.single_pass(s)['correct']
        rand = engine.random_inv(s, budget, rng)['correct']
        vld = engine.investigate(s, budget, engine.Q_additive)['correct']
        grag = engine.investigate(s, budget, engine.Q_graphrag)['correct']

        method_results = {'sp': sp, 'random': rand, 'vld': vld, 'graphrag': grag}

        for pair_name, m_better, m_worse in pairs:
            b = method_results[m_better]
            w = method_results[m_worse]
            if b and not w:
                by_sit[sit][pair_name]['saves'] += 1
            elif not b and w:
                by_sit[sit][pair_name]['hurts'] += 1
            elif b and w:
                by_sit[sit][pair_name]['both_right'] += 1
            else:
                by_sit[sit][pair_name]['both_wrong'] += 1

    # Print VLD vs Random (the primary with-without)
    print("\n  VLD vs Random:")
    print("  Sit   Saves  Hurts  Both_R  Both_W  Net    n")
    total_saves = 0
    total_hurts = 0
    for sit in sorted(by_sit.keys()):
        d = by_sit[sit]['VLD_vs_Random']
        n = by_sit_total[sit]
        net = d['saves'] - d['hurts']
        total_saves += d['saves']
        total_hurts += d['hurts']
        print("  " + sit + "    " +
              str(d['saves']).ljust(7) + str(d['hurts']).ljust(7) +
              str(d['both_right']).ljust(8) + str(d['both_wrong']).ljust(8) +
              ("+" if net >= 0 else "") + str(net).ljust(7) + str(n))
    print("  TOTAL " + str(total_saves).ljust(7) + str(total_hurts).ljust(7))

    # Print VLD vs GraphRAG
    print("\n  VLD vs GraphRAG:")
    print("  Sit   Saves  Hurts  Both_R  Both_W  n")
    for sit in sorted(by_sit.keys()):
        d = by_sit[sit]['VLD_vs_GraphRAG']
        n = by_sit_total[sit]
        print("  " + sit + "    " +
              str(d['saves']).ljust(7) + str(d['hurts']).ljust(7) +
              str(d['both_right']).ljust(8) + str(d['both_wrong']).ljust(8) + str(n))

    return dict(by_sit)


def exp_compounding_v2(gen, scenarios_template, budget=2, n_epochs=10):
    """EXP-COMP: Compounding with shuffled order + sigma learning."""
    print("\n--- Compounding v2 (shuffled epochs, sigma learning) ---")

    engine = VLDEngine(gen.mu, gen.sigma.copy())
    rng = np.random.default_rng(42)

    epoch_results = []

    for epoch in range(n_epochs):
        # Shuffle scenario ORDER each epoch (same scenarios, different sequence)
        scenarios = scenarios_template.copy()
        rng.shuffle(scenarios)

        correct = 0
        q_informative = 0
        q_total = 0

        for s in scenarios:
            r = engine.investigate(s, budget, engine.Q_additive)
            if r['correct']:
                correct += 1

            for t in r['trace']:
                q_total += 1
                if t['evidence_type'] == 'informative':
                    q_informative += 1

            # Learn sigma from outcome
            engine.update_sigma(s, r)

        acc = correct / len(scenarios)
        routing_q = q_informative / max(q_total, 1)
        sigma_drift = float(np.mean(np.abs(engine.sigma - gen.sigma)))

        epoch_results.append({
            'epoch': epoch, 'accuracy': round(acc, 4),
            'routing_quality': round(routing_q, 4),
            'sigma_drift': round(sigma_drift, 4),
        })
        print("  Epoch " + str(epoch) + ": acc=" + str(round(acc, 3)) +
              "  routing_q=" + str(round(routing_q, 3)) +
              "  sigma_drift=" + str(round(sigma_drift, 4)))

    return epoch_results


# ═══════════════════════════════════════════════════════════════
# CHARTS
# ═══════════════════════════════════════════════════════════════

def chart_graphrag(methods, by_sit, label, out_dir):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Overall comparison
    names = ['single_pass', 'random', 'GraphRAG', 'VLD_additive', 'ReAct_oracle', 'exhaustive']
    vals = [methods.get(n, 0) for n in names]
    colors = ['#6B7280', '#DC2626', '#F59E0B', '#2563EB', '#9333EA', '#059669']
    bars = ax1.bar(range(len(names)), vals, color=colors, edgecolor='white', width=0.7)
    ax1.set_xticks(range(len(names)))
    ax1.set_xticklabels([n.replace('_','\n') for n in names], fontsize=8)
    ax1.set_ylabel('Accuracy')
    ax1.set_title('Routing Method Comparison — ' + label)
    ax1.set_ylim(0, 1.0)
    for b, v in zip(bars, vals):
        ax1.text(b.get_x() + b.get_width()/2, b.get_height() + 0.01,
                str(round(v, 3)), ha='center', fontsize=8, fontweight='bold')

    # Per-situation VLD vs GraphRAG
    sits = sorted(by_sit.keys())
    x = np.arange(len(sits))
    w = 0.25
    vld_vals = [np.mean(by_sit[s]['VLD_additive']) for s in sits]
    grag_vals = [np.mean(by_sit[s]['GraphRAG']) for s in sits]
    rand_vals = [np.mean(by_sit[s]['random']) for s in sits]
    ax2.bar(x - w, rand_vals, w, label='Random', color='#DC2626')
    ax2.bar(x, grag_vals, w, label='GraphRAG', color='#F59E0B')
    ax2.bar(x + w, vld_vals, w, label='VLD', color='#2563EB')
    ax2.set_xticks(x)
    ax2.set_xticklabels(sits, fontsize=9)
    ax2.set_ylabel('Accuracy')
    ax2.set_title('Per-Situation: VLD vs GraphRAG — ' + label)
    ax2.legend(fontsize=8)
    ax2.set_ylim(0, 1.05)

    plt.tight_layout()
    path = os.path.join(out_dir, 'val4_graphrag_' + label.replace(' ','_').replace(',','') + '.png')
    plt.savefig(path, dpi=200)
    plt.close()
    print("  Chart: " + os.path.basename(path))


def chart_scaling(results, out_dir):
    fig, ax = plt.subplots(figsize=(9, 5))
    x = [r['complexity'] for r in results]
    y = [r['vld_advantage'] for r in results]
    ax.scatter(x, y, s=80, color='#2563EB', zorder=5)
    for r in results:
        ax.annotate("d=" + str(r['d']) + "\nA=" + str(r['A']),
                    (r['complexity'], r['vld_advantage']),
                    fontsize=7, ha='center', va='bottom')
    ax.axhline(y=0, color='#DC2626', ls='--', lw=1, alpha=0.5)
    ax.set_xlabel('Decision Complexity: d x (A-1)')
    ax.set_ylabel('VLD Advantage (VLD - Random)')
    ax.set_title('VLD Value Scales With Decision Complexity')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'val4_complexity_scaling.png'), dpi=200)
    plt.close()
    print("  Chart: val4_complexity_scaling.png")


def chart_s5_sweep(results, out_dir):
    fig, ax = plt.subplots(figsize=(9, 5))
    ratios = [r['ratio'] for r in results]
    ax.plot(ratios, [r['vld'] for r in results], '-o', color='#2563EB', lw=2, label='VLD')
    ax.plot(ratios, [r['random'] for r in results], '-^', color='#DC2626', lw=2, label='Random')
    ax.plot(ratios, [r['exhaustive'] for r in results], '--', color='#059669', lw=1.5, label='Exhaustive')
    # Crossover annotation
    for i in range(1, len(results)):
        if results[i]['vld'] < results[i]['random'] and results[i-1]['vld'] >= results[i-1]['random']:
            ax.axvline(x=(ratios[i]+ratios[i-1])/2, color='#D97706', ls=':', lw=2)
            ax.text((ratios[i]+ratios[i-1])/2, 0.95, 'VLD < Random\ncrossover',
                    ha='center', fontsize=8, color='#D97706', transform=ax.get_xaxis_transform())
    ax.set_xlabel('Misleading Evidence Ratio')
    ax.set_ylabel('Accuracy')
    ax.set_title('S5 Failure Mode: VLD degrades with more misleading evidence')
    ax.legend()
    ax.set_ylim(0, 1.0)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'val4_s5_failure_sweep.png'), dpi=200)
    plt.close()
    print("  Chart: val4_s5_failure_sweep.png")


def chart_compounding(epochs, out_dir):
    fig, ax = plt.subplots(figsize=(9, 5))
    ep = [r['epoch'] for r in epochs]
    ax.plot(ep, [r['accuracy'] for r in epochs], '-o', color='#2563EB', lw=2, label='Accuracy')
    ax.plot(ep, [r['routing_quality'] for r in epochs], '-s', color='#059669', lw=2, label='Routing Quality')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Rate')
    ax.set_title('Compounding v2: sigma learning + shuffled epochs')
    ax.legend()
    ax.set_ylim(0, 1.0)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'val4_compounding_v2.png'), dpi=200)
    plt.close()
    print("  Chart: val4_compounding_v2.png")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("VLD Experiments v4 — Unblocked Gap-Closers")
    print("=" * 65)

    d, A = 6, 4
    gen = ScenarioGenerator(d=d, A=A, seed=42)
    scenarios = gen.generate(n=500)
    engine = VLDEngine(gen.mu, gen.sigma)

    all_results = {}

    # 1. Halting
    all_results['halting'] = exp_halt_fixed(engine, scenarios)

    # 2. GraphRAG + ReAct comparison
    methods, by_sit = exp_graphrag_react(engine, scenarios, budget=2, rng_seed=99)
    all_results['graphrag_react'] = {'methods': methods, 'by_sit_summary': {
        s: {m: round(np.mean(v), 3) for m, v in vals.items()} for s, vals in by_sit.items()
    }}
    chart_graphrag(methods, by_sit, 'd=6 A=4', OUTPUT_DIR)

    # 3. Complexity scaling
    all_results['scaling'] = exp_complexity_scaling(budget=2)
    chart_scaling(all_results['scaling'], OUTPUT_DIR)

    # 4. S5 failure modes
    all_results['s5_sweep'] = exp_s5_failure_modes(d=6, A=4, budget=2)
    chart_s5_sweep(all_results['s5_sweep'], OUTPUT_DIR)

    # 5. With-without comprehensive
    all_results['with_without'] = exp_with_without_comprehensive(engine, scenarios, budget=2, rng_seed=99)

    # 6. Compounding v2
    all_results['compounding'] = exp_compounding_v2(gen, scenarios, budget=2, n_epochs=10)
    chart_compounding(all_results['compounding'], OUTPUT_DIR)

    # Save JSON
    results_path = os.path.join(OUTPUT_DIR, 'vld_experiments_v4_results.json')
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else str(x))
    print("\nResults: " + results_path)

    print("\n" + "=" * 65)
    print("DONE. 6 experiments, 4 charts.")
