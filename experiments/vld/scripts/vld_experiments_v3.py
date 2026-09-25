"""
VLD Graph Reasoning — Extended Experiments v3
================================================
Adds: composition variants, adaptive halting, evidence quality variance,
"what helped" decomposition, multi-epoch compounding, context complexity
parameterization, fixed EVOI shift measurement.

Builds on v2 (situation-realistic scenarios, pluggable Q/K/V).

Usage: python vld_experiments_v3.py [output_dir]
"""

import sys, os, json, copy
import numpy as np
from collections import defaultdict

try:
    from scipy.stats import spearmanr
except ImportError:
    spearmanr = None

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

# Import v2 modules (assume v2 is in same directory)
# We redefine here for self-containment

# ═══════════════════════════════════════════════════════════════
# SCENARIO GENERATOR (from v2, with evidence quality variance)
# ═══════════════════════════════════════════════════════════════

class ScenarioGenerator:
    def __init__(self, d=6, A=4, seed=42, evidence_quality='uniform'):
        self.rng = np.random.default_rng(seed)
        self.d = d
        self.A = A
        self.evidence_quality = evidence_quality  # 'uniform', 'mixed', 'noisy'
        self.mu = self._generate_centroids()
        self.sigma = self.rng.uniform(0.05, 0.30, d)

    def _generate_centroids(self):
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

    def _evidence_conf(self, etype):
        """Evidence confidence based on quality regime."""
        if self.evidence_quality == 'uniform':
            return self.rng.uniform(0.7, 1.0) if etype == 'informative' else self.rng.uniform(0.4, 0.8)
        elif self.evidence_quality == 'mixed':
            # Some dims have SAP-quality (0.9-1.0), others partner-quality (0.3-0.6)
            if self.rng.random() < 0.4:
                return self.rng.uniform(0.3, 0.6)  # noisy source
            else:
                return self.rng.uniform(0.85, 1.0)  # precise source
        elif self.evidence_quality == 'noisy':
            return self.rng.uniform(0.2, 0.6)  # all sources unreliable
        return self.rng.uniform(0.5, 0.9)

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
        wrong_dims = list(self.rng.choice(self.d, size=3, replace=False))
        v[wrong_dims[0]] = self.mu[wrong1, wrong_dims[0]] + self.rng.normal(0, 0.05)
        wrong2 = (gt + 2) % self.A if self.A > 2 else wrong1
        v[wrong_dims[1]] = (self.mu[gt, wrong_dims[1]] + self.mu[wrong2, wrong_dims[1]]) / 2
        v[wrong_dims[2]] = self.mu[wrong1, wrong_dims[2]] * 0.6 + self.mu[gt, wrong_dims[2]] * 0.4
        return self._build(np.clip(v, 0, 1), gt, wrong_dims, [], conditional=True)

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
        if norm > 0:
            direction = direction / norm
        v = mid + 0.08 * direction + self.rng.normal(0, 0.03, self.d)
        n_needed = int(self.rng.integers(2, 4))
        needed = list(self.rng.choice(self.d, size=n_needed, replace=False))
        return self._build(np.clip(v, 0, 1), gt, needed, [], compositional=True)

    def _build(self, v, gt, informative_dims, misleading_dims,
               conditional=False, compositional=False):
        evidence = {}
        for k in range(self.d):
            if k in informative_dims:
                target = self.mu[gt, k]
                if compositional:
                    target = v[k] + 0.6 * (target - v[k])
                evidence[k] = {
                    'value': float(np.clip(target + self.rng.normal(0, 0.03), 0, 1)),
                    'shift': float(abs(target - v[k])),
                    'confidence': float(self._evidence_conf('informative')),
                    'type': 'informative',
                }
            elif k in misleading_dims:
                wrong_a = (gt + 1) % self.A
                target = self.mu[wrong_a, k]
                evidence[k] = {
                    'value': float(np.clip(target + self.rng.normal(0, 0.05), 0, 1)),
                    'shift': float(abs(target - v[k])),
                    'confidence': float(self._evidence_conf('misleading')),
                    'type': 'misleading',
                }
            else:
                evidence[k] = {
                    'value': float(np.clip(v[k] + self.rng.normal(0, 0.03), 0, 1)),
                    'shift': float(abs(self.rng.normal(0, 0.03))),
                    'confidence': float(self._evidence_conf('neutral')),
                    'type': 'neutral',
                }
        return {
            'v_surface': v, 'gt_action': gt, 'evidence': evidence,
            'informative_dims': informative_dims, 'misleading_dims': misleading_dims,
            'conditional': conditional, 'compositional': compositional,
        }


# ═══════════════════════════════════════════════════════════════
# VLD ENGINE (extended with halting, composition, decomposition)
# ═══════════════════════════════════════════════════════════════

class VLDEngineV3:
    def __init__(self, mu, sigma, tau=0.1):
        self.mu = mu.copy()
        self.sigma = sigma.copy()
        self.sigma_initial = sigma.copy()
        self.tau = tau
        self.A = mu.shape[0]
        self.d = mu.shape[1]
        self.past_utility = np.ones(self.d) * 0.5

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

    def entropy(self, P):
        P_safe = np.clip(P, 1e-10, 1.0)
        return -np.sum(P_safe * np.log(P_safe))

    def margin(self, P):
        s = np.sort(P)[::-1]
        return s[0] - s[1]

    # ── Q variants ──

    def Q_margin(self, v, P, enriched_set=None):
        """Best Q from v2 results: P2 + D_any + U4_margin."""
        a1, a2 = self.top2(P)
        Q = np.zeros(self.d)
        for k in range(self.d):
            if enriched_set and k in enriched_set:
                Q[k] = -1
                continue
            prec = 1.0 / max(self.sigma[k]**2, 0.001)
            disc = abs(self.mu[a1, k] - self.mu[a2, k])
            unc = abs((v[k] - self.mu[a1, k])**2 - (v[k] - self.mu[a2, k])**2)
            Q[k] = prec * disc * unc
        return Q

    def Q_additive(self, v, P, enriched_set=None):
        """Additive composition: P + D + U (normalized)."""
        a1, a2 = self.top2(P)
        Q = np.zeros(self.d)
        for k in range(self.d):
            if enriched_set and k in enriched_set:
                Q[k] = -1
                continue
            prec = 1.0 / max(self.sigma[k]**2, 0.001)
            disc = abs(self.mu[a1, k] - self.mu[a2, k])
            unc = abs((v[k] - self.mu[a1, k])**2 - (v[k] - self.mu[a2, k])**2)
            # Normalize each to [0,1] range roughly
            Q[k] = prec/100.0 + disc + unc
        return Q

    def Q_max(self, v, P, enriched_set=None):
        """Max composition: max(P, D, U)."""
        a1, a2 = self.top2(P)
        Q = np.zeros(self.d)
        for k in range(self.d):
            if enriched_set and k in enriched_set:
                Q[k] = -1
                continue
            prec = 1.0 / max(self.sigma[k]**2, 0.001) / 100.0
            disc = abs(self.mu[a1, k] - self.mu[a2, k])
            unc = abs((v[k] - self.mu[a1, k])**2 - (v[k] - self.mu[a2, k])**2)
            Q[k] = max(prec, disc, unc)
        return Q

    def Q_gap_only(self, v, P, enriched_set=None):
        """Just the gap from best centroid — simplest possible Q."""
        a1, _ = self.top2(P)
        Q = np.zeros(self.d)
        for k in range(self.d):
            if enriched_set and k in enriched_set:
                Q[k] = -1
                continue
            Q[k] = abs(v[k] - self.mu[a1, k])
        return Q

    def Q_random(self, v, P, enriched_set=None):
        Q = np.random.default_rng().uniform(0, 1, self.d)
        if enriched_set:
            for k in enriched_set:
                Q[k] = -1
        return Q

    # ── V update ──

    @staticmethod
    def V_gated(v, k, ev):
        v_new = v.copy()
        c = ev['confidence']
        v_new[k] = c * ev['value'] + (1-c) * v[k]
        return v_new

    @staticmethod
    def V_raw(v, k, ev):
        v_new = v.copy()
        v_new[k] = ev['value']
        return v_new

    # ── Investigation with halting ──

    def investigate(self, scenario, max_budget, q_func, v_func=None,
                    halt='fixed', halt_threshold=0.5, use_utility=False):
        if v_func is None:
            v_func = self.V_gated

        v = scenario['v_surface'].copy()
        enriched_set = set()
        trace = []
        actions_seq = []

        for step in range(max_budget):
            a_before, P = self.score(v)
            actions_seq.append(a_before)

            # Halting check (after step 0)
            if step > 0 and halt != 'fixed':
                if halt == 'margin' and self.margin(P) > halt_threshold:
                    break
                elif halt == 'entropy' and self.entropy(P) < halt_threshold:
                    break
                elif halt == 'residual' and len(trace) > 0:
                    # Compare magnitude of PREVIOUS step's enrichment
                    last_shift = trace[-1].get('shift_magnitude', 999)
                    if last_shift < halt_threshold:
                        break

            Q = q_func(v, P, enriched_set)
            if use_utility:
                for k in range(self.d):
                    if Q[k] > 0:
                        Q[k] *= self.past_utility[k]

            if np.max(Q) <= 0:
                break

            k_star = int(np.argmax(Q))
            v_before = v.copy()
            v = v_func(v, k_star, scenario['evidence'][k_star])
            enriched_set.add(k_star)
            shift_mag = float(np.linalg.norm(v - v_before))

            a_after, P_after = self.score(v)
            trace.append({
                'step': step, 'dim': k_star,
                'action_before': a_before, 'action_after': a_after,
                'flipped': a_before != a_after,
                'evidence_type': scenario['evidence'][k_star]['type'],
                'margin_before': float(self.margin(P)),
                'margin_after': float(self.margin(P_after)),
                'shift_magnitude': shift_mag,
                'v_after': v.copy(),
            })

        final_action, final_P = self.score(v)
        actions_seq.append(final_action)

        return {
            'final_action': final_action,
            'correct': final_action == scenario['gt_action'],
            'trace': trace,
            'n_hops': len(trace),
            'v_final': v,
            'final_margin': float(self.margin(final_P)),
        }

    def single_pass(self, scenario):
        a, _ = self.score(scenario['v_surface'])
        return {'final_action': a, 'correct': a == scenario['gt_action']}

    def random_inv(self, scenario, budget, rng, v_func=None):
        if v_func is None:
            v_func = self.V_gated
        v = scenario['v_surface'].copy()
        dims = list(range(self.d))
        rng.shuffle(dims)
        for k in dims[:budget]:
            v = v_func(v, k, scenario['evidence'][k])
        a, _ = self.score(v)
        return {'final_action': a, 'correct': a == scenario['gt_action']}

    def exhaustive(self, scenario, v_func=None):
        if v_func is None:
            v_func = self.V_gated
        v = scenario['v_surface'].copy()
        for k in range(self.d):
            v = v_func(v, k, scenario['evidence'][k])
        a, _ = self.score(v)
        return {'final_action': a, 'correct': a == scenario['gt_action']}

    def update_utility(self, trace, correct):
        for t in trace:
            k = t['dim']
            if correct:
                self.past_utility[k] = min(1.0, self.past_utility[k] + 0.05)
            else:
                self.past_utility[k] = max(0.1, self.past_utility[k] - 0.02)

    def update_sigma(self, scenario, result):
        """Learn sigma from verified outcome — reduce sigma on enriched dims that helped."""
        if not result['correct']:
            return
        for t in result['trace']:
            k = t['dim']
            if t['evidence_type'] == 'informative':
                self.sigma[k] = max(0.02, self.sigma[k] * 0.98)  # sharpen
            elif t['evidence_type'] == 'misleading':
                self.sigma[k] = min(0.40, self.sigma[k] * 1.02)  # broaden


# ═══════════════════════════════════════════════════════════════
# EXPERIMENT 1: COMPOSITION VARIANTS
# ═══════════════════════════════════════════════════════════════

def exp_composition(engine, scenarios, budget=2, rng=None):
    """Compare Q composition methods: multiply, add, max, gap-only, random."""
    if rng is None:
        rng = np.random.default_rng(99)

    methods = {
        'multiply': engine.Q_margin,
        'additive': engine.Q_additive,
        'max': engine.Q_max,
        'gap_only': engine.Q_gap_only,
        'random': engine.Q_random,
    }

    results = {}
    results['single_pass'] = sum(1 for s in scenarios if engine.single_pass(s)['correct']) / len(scenarios)
    results['exhaustive'] = sum(1 for s in scenarios if engine.exhaustive(s)['correct']) / len(scenarios)
    results['random_B2'] = sum(1 for s in scenarios if engine.random_inv(s, budget, rng)['correct']) / len(scenarios)

    for name, qf in methods.items():
        correct = sum(1 for s in scenarios
                      if engine.investigate(s, budget, qf)['correct'])
        results[name] = correct / len(scenarios)

    print("--- Composition Variants (budget=" + str(budget) + ") ---")
    for k in sorted(results.keys()):
        print("  " + k + ": " + str(round(results[k], 3)))
    return results


# ═══════════════════════════════════════════════════════════════
# EXPERIMENT 2: HALTING STRATEGIES
# ═══════════════════════════════════════════════════════════════

def exp_halting(engine, scenarios, max_budget=6):
    """Compare fixed budget vs adaptive halting."""
    strategies = {}

    # Fixed budgets 1-4
    for b in [1, 2, 3, 4]:
        results_list = [engine.investigate(s, b, engine.Q_margin, halt='fixed') for s in scenarios]
        correct = sum(1 for r in results_list if r['correct'])
        avg_hops = np.mean([r['n_hops'] for r in results_list])
        strategies['fixed_B' + str(b)] = {
            'accuracy': correct / len(scenarios),
            'avg_hops': float(avg_hops),
        }

    # Margin halt (various thresholds)
    for th in [0.2, 0.4, 0.6]:
        results = [engine.investigate(s, max_budget, engine.Q_margin,
                                     halt='margin', halt_threshold=th) for s in scenarios]
        strategies['margin_' + str(th)] = {
            'accuracy': sum(1 for r in results if r['correct']) / len(scenarios),
            'avg_hops': np.mean([r['n_hops'] for r in results]),
        }

    # Entropy halt
    for th in [0.3, 0.5, 0.8]:
        results = [engine.investigate(s, max_budget, engine.Q_margin,
                                     halt='entropy', halt_threshold=th) for s in scenarios]
        strategies['entropy_' + str(th)] = {
            'accuracy': sum(1 for r in results if r['correct']) / len(scenarios),
            'avg_hops': np.mean([r['n_hops'] for r in results]),
        }

    print("\n--- Halting Strategies ---")
    print("  Strategy           Accuracy  Avg Hops")
    for name in sorted(strategies.keys()):
        s = strategies[name]
        print("  " + name.ljust(22) + str(round(s['accuracy'], 3)).ljust(10) + str(round(s['avg_hops'], 1)))
    return strategies


# ═══════════════════════════════════════════════════════════════
# EXPERIMENT 3: WHAT HELPED DECOMPOSITION
# ═══════════════════════════════════════════════════════════════

def exp_what_helped(engine, scenarios, budget=2, rng=None):
    """Decompose VLD improvement into routing vs enrichment vs trajectory."""
    if rng is None:
        rng = np.random.default_rng(99)

    decomp = defaultdict(lambda: {
        'sp_correct': 0, 'random_correct': 0, 'vld_correct': 0,
        'exh_correct': 0, 'total': 0,
        'routing_helped': 0,      # VLD correct AND random wrong
        'enrichment_helped': 0,   # random correct AND SP wrong
        'trajectory_helped': 0,   # VLD correct AND parallel wrong
        'vld_hurt': 0,            # VLD wrong AND random correct
    })

    for s in scenarios:
        sit = s['situation']
        decomp[sit]['total'] += 1

        sp = engine.single_pass(s)['correct']
        rand = engine.random_inv(s, budget, rng)['correct']
        vld = engine.investigate(s, budget, engine.Q_margin)['correct']
        exh = engine.exhaustive(s)['correct']

        # Parallel (Q0 fixed)
        par = engine.investigate(s, budget, engine.Q_margin,
                                halt='fixed')  # use_rnn handled inside Q_margin
        # Actually we need a non-RNN version — but Q_margin always uses current v
        # For decomposition, compare VLD vs random as proxy for routing value

        if sp: decomp[sit]['sp_correct'] += 1
        if rand: decomp[sit]['random_correct'] += 1
        if vld: decomp[sit]['vld_correct'] += 1
        if exh: decomp[sit]['exh_correct'] += 1

        if vld and not rand: decomp[sit]['routing_helped'] += 1
        if rand and not sp: decomp[sit]['enrichment_helped'] += 1
        if vld and not sp and not rand: decomp[sit]['trajectory_helped'] += 1
        if not vld and rand: decomp[sit]['vld_hurt'] += 1

    print("\n--- What Helped Decomposition ---")
    print("  Sit   Routing  Enrichment  Trajectory  VLD_hurt  n")
    for sit in sorted(decomp.keys()):
        d = decomp[sit]
        n = d['total']
        print("  " + sit + "    " +
              str(d['routing_helped']).ljust(9) +
              str(d['enrichment_helped']).ljust(12) +
              str(d['trajectory_helped']).ljust(12) +
              str(d['vld_hurt']).ljust(10) +
              str(n))

    return dict(decomp)


# ═══════════════════════════════════════════════════════════════
# EXPERIMENT 4: COMPOUNDING (MULTI-EPOCH)
# ═══════════════════════════════════════════════════════════════

def exp_compounding(engine, scenarios, budget=2, n_epochs=5):
    """Run multiple epochs. Sigma and utility update from verified outcomes."""
    engine_copy = VLDEngineV3(engine.mu, engine.sigma_initial, engine.tau)

    epoch_results = []

    for epoch in range(n_epochs):
        correct = 0
        q_ranks = []

        for s in scenarios:
            r = engine_copy.investigate(s, budget, engine_copy.Q_margin, use_utility=True)
            if r['correct']:
                correct += 1

            # Track routing quality: did Q pick an informative dim?
            for t in r['trace']:
                q_ranks.append(t['evidence_type'] == 'informative')

            # Learn from outcome
            engine_copy.update_utility(r['trace'], r['correct'])
            engine_copy.update_sigma(s, r)

        acc = correct / len(scenarios)
        routing_quality = np.mean(q_ranks) if q_ranks else 0
        sigma_change = np.mean(np.abs(engine_copy.sigma - engine_copy.sigma_initial))

        epoch_results.append({
            'epoch': epoch,
            'accuracy': round(acc, 4),
            'routing_quality': round(routing_quality, 4),
            'sigma_drift': round(sigma_change, 4),
            'mean_utility': round(np.mean(engine_copy.past_utility), 4),
        })

    print("\n--- Compounding (Multi-Epoch) ---")
    print("  Epoch  Accuracy  Routing_Q  Sigma_drift  Mean_utility")
    for r in epoch_results:
        print("  " + str(r['epoch']).ljust(7) +
              str(r['accuracy']).ljust(10) +
              str(r['routing_quality']).ljust(11) +
              str(r['sigma_drift']).ljust(13) +
              str(r['mean_utility']))

    return epoch_results


# ═══════════════════════════════════════════════════════════════
# EXPERIMENT 5: EVIDENCE QUALITY VARIANCE
# ═══════════════════════════════════════════════════════════════

def exp_evidence_quality(d=6, A=4, budget=2):
    """Same scenarios, different evidence quality regimes."""
    results = {}

    for quality in ['uniform', 'mixed', 'noisy']:
        gen = ScenarioGenerator(d=d, A=A, seed=42, evidence_quality=quality)
        scenarios = gen.generate(n=500)
        engine = VLDEngineV3(gen.mu, gen.sigma)
        rng = np.random.default_rng(99)

        sp = sum(1 for s in scenarios if engine.single_pass(s)['correct']) / len(scenarios)
        rand = sum(1 for s in scenarios if engine.random_inv(s, budget, rng)['correct']) / len(scenarios)
        vld_raw = sum(1 for s in scenarios
                      if engine.investigate(s, budget, engine.Q_margin, v_func=engine.V_raw)['correct']) / len(scenarios)
        vld_gated = sum(1 for s in scenarios
                        if engine.investigate(s, budget, engine.Q_margin, v_func=engine.V_gated)['correct']) / len(scenarios)
        exh = sum(1 for s in scenarios if engine.exhaustive(s)['correct']) / len(scenarios)

        results[quality] = {
            'single_pass': round(sp, 3),
            'random': round(rand, 3),
            'vld_raw_V': round(vld_raw, 3),
            'vld_gated_V': round(vld_gated, 3),
            'exhaustive': round(exh, 3),
            'gating_value': round(vld_gated - vld_raw, 3),
        }

    print("\n--- Evidence Quality Variance ---")
    print("  Quality    SP     Rnd    VLD_raw  VLD_gated  Exh    Gating_value")
    for q, r in results.items():
        print("  " + q.ljust(11) +
              str(r['single_pass']).ljust(7) +
              str(r['random']).ljust(7) +
              str(r['vld_raw_V']).ljust(9) +
              str(r['vld_gated_V']).ljust(11) +
              str(r['exhaustive']).ljust(7) +
              str(r['gating_value']))
    return results


# ═══════════════════════════════════════════════════════════════
# EXPERIMENT 6: FIXED EVOI SHIFT MEASUREMENT
# ═══════════════════════════════════════════════════════════════

def exp_evoi_shift_fixed(engine, scenarios):
    """Correct EVOI shift: compare Q rankings EXCLUDING the enriched dim."""
    shifts = defaultdict(lambda: {'shifted': 0, 'total': 0, 'top1_flipped': 0})

    for s in scenarios:
        sit = s['situation']
        v0 = s['v_surface']
        _, P0 = engine.score(v0)
        Q0 = engine.Q_margin(v0, P0)

        # Top dim at v0 (excluding nothing)
        k0 = int(np.argmax(Q0))

        # Get ranking of REMAINING dims at v0
        Q0_remaining = Q0.copy()
        Q0_remaining[k0] = -1
        rank0_rest = np.argsort(-Q0_remaining)[:2]

        # Enrich k0
        v1 = engine.V_gated(v0, k0, s['evidence'][k0])
        _, P1 = engine.score(v1)
        Q1 = engine.Q_margin(v1, P1, enriched_set={k0})

        # Get ranking of REMAINING dims at v1
        rank1_rest = np.argsort(-Q1)[:2]

        shifts[sit]['total'] += 1

        # Did the ranking of remaining dims change?
        if not np.array_equal(rank0_rest, rank1_rest):
            shifts[sit]['shifted'] += 1

        # Did top-1 of remaining change?
        if rank0_rest[0] != rank1_rest[0]:
            shifts[sit]['top1_flipped'] += 1

    print("\n--- EVOI Shift Rate (FIXED measurement) ---")
    print("  Sit   Shift_rate  Top1_flip  n")
    for sit in sorted(shifts.keys()):
        d = shifts[sit]
        n = d['total']
        sr = d['shifted'] / n if n else 0
        tf = d['top1_flipped'] / n if n else 0
        print("  " + sit + "    " + str(round(sr, 3)).ljust(12) +
              str(round(tf, 3)).ljust(11) + str(n))
    return dict(shifts)


# ═══════════════════════════════════════════════════════════════
# EXPERIMENT 7: BUDGET × SITUATION INTERACTION
# ═══════════════════════════════════════════════════════════════

def exp_budget_situation(engine, scenarios, rng=None):
    """VLD accuracy per situation at different budgets."""
    if rng is None:
        rng = np.random.default_rng(99)

    results = defaultdict(lambda: defaultdict(lambda: {'correct': 0, 'total': 0}))

    for s in scenarios:
        sit = s['situation']
        for b in [0, 1, 2, 3, 4]:
            if b == 0:
                correct = engine.single_pass(s)['correct']
            else:
                correct = engine.investigate(s, b, engine.Q_margin)['correct']
            results[sit][b]['total'] += 1
            if correct:
                results[sit][b]['correct'] += 1

    print("\n--- Budget x Situation ---")
    sits = sorted(set(s['situation'] for s in scenarios))
    header = "  Sit   " + "  ".join("B=" + str(b) for b in [0,1,2,3,4])
    print(header)
    for sit in sits:
        row = "  " + sit + "   "
        for b in [0,1,2,3,4]:
            d = results[sit][b]
            acc = d['correct'] / d['total'] if d['total'] else 0
            row += str(round(acc, 2)).ljust(6)
        print(row)

    return dict(results)


# ═══════════════════════════════════════════════════════════════
# CHARTS
# ═══════════════════════════════════════════════════════════════

def chart_composition(results, label, out_dir):
    fig, ax = plt.subplots(figsize=(9, 5))
    names = sorted(results.keys())
    vals = [results[n] for n in names]
    colors = ['#2563EB' if n in ('multiply','additive','max') else
              '#DC2626' if n == 'random_B2' else
              '#059669' if n == 'exhaustive' else '#6B7280' for n in names]
    bars = ax.bar(range(len(names)), vals, color=colors, edgecolor='white', width=0.7)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([n.replace('_','\n') for n in names], fontsize=8)
    ax.set_ylabel('Accuracy')
    ax.set_title('Q Composition Variants — ' + label)
    ax.set_ylim(0, 1.0)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.008,
                str(round(v, 3)), ha='center', fontsize=8, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'val3_composition_' + label.replace(' ','_') + '.png'), dpi=200)
    plt.close()

def chart_compounding(epochs, label, out_dir):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ep = [r['epoch'] for r in epochs]

    ax1.plot(ep, [r['accuracy'] for r in epochs], '-o', color='#2563EB', lw=2, label='Accuracy')
    ax1.plot(ep, [r['routing_quality'] for r in epochs], '-s', color='#059669', lw=2, label='Routing Quality')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Rate')
    ax1.set_title('Compounding: Accuracy + Routing — ' + label)
    ax1.legend()
    ax1.set_ylim(0, 1.0)

    ax2.plot(ep, [r['sigma_drift'] for r in epochs], '-^', color='#D97706', lw=2, label='Sigma drift')
    ax2.plot(ep, [r['mean_utility'] for r in epochs], '-d', color='#9333EA', lw=2, label='Mean utility')
    ax2.set_xlabel('Epoch')
    ax2.set_title('Learning State — ' + label)
    ax2.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'val3_compounding_' + label.replace(' ','_') + '.png'), dpi=200)
    plt.close()

def chart_evidence_quality(results, out_dir):
    fig, ax = plt.subplots(figsize=(10, 5))
    qualities = sorted(results.keys())
    x = np.arange(len(qualities))
    w = 0.15
    metrics = ['single_pass', 'random', 'vld_raw_V', 'vld_gated_V', 'exhaustive']
    colors = ['#6B7280', '#DC2626', '#F59E0B', '#2563EB', '#059669']
    for i, (m, c) in enumerate(zip(metrics, colors)):
        vals = [results[q][m] for q in qualities]
        ax.bar(x + (i-2)*w, vals, w, label=m.replace('_',' '), color=c)
    ax.set_xticks(x)
    ax.set_xticklabels(qualities)
    ax.set_ylabel('Accuracy')
    ax.set_title('Evidence Quality Regime: gating value increases with noise')
    ax.legend(fontsize=8)
    ax.set_ylim(0, 1.0)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'val3_evidence_quality.png'), dpi=200)
    plt.close()


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("VLD Graph Reasoning — Extended Experiments v3")
    print("=" * 65)

    configs = [
        {'d': 6, 'A': 4, 'label': 'd=6 A=4'},
        {'d': 6, 'A': 6, 'label': 'd=6 A=6'},
    ]

    all_results = {}

    for cfg in configs:
        label = cfg['label']
        print("\n" + "=" * 65)
        print("Config: " + label)
        print("=" * 65)

        gen = ScenarioGenerator(d=cfg['d'], A=cfg['A'])
        scenarios = gen.generate(n=500)
        engine = VLDEngineV3(gen.mu, gen.sigma)
        rng = np.random.default_rng(99)

        cfg_results = {}

        # Exp 1: Composition
        cfg_results['composition'] = exp_composition(engine, scenarios, budget=2, rng=rng)
        chart_composition(cfg_results['composition'], label, OUTPUT_DIR)

        # Exp 2: Halting
        cfg_results['halting'] = exp_halting(engine, scenarios, max_budget=6)

        # Exp 3: What helped
        cfg_results['what_helped'] = exp_what_helped(engine, scenarios, budget=2, rng=rng)

        # Exp 4: Compounding
        cfg_results['compounding'] = exp_compounding(engine, scenarios, budget=2, n_epochs=5)
        chart_compounding(cfg_results['compounding'], label, OUTPUT_DIR)

        # Exp 5: Evidence quality (only on first config to save time)
        if cfg == configs[0]:
            cfg_results['evidence_quality'] = exp_evidence_quality(d=cfg['d'], A=cfg['A'], budget=2)
            chart_evidence_quality(cfg_results['evidence_quality'], OUTPUT_DIR)

        # Exp 6: EVOI shift (fixed)
        cfg_results['evoi_shift'] = exp_evoi_shift_fixed(engine, scenarios)

        # Exp 7: Budget × situation
        cfg_results['budget_situation'] = exp_budget_situation(engine, scenarios, rng=rng)

        all_results[label] = cfg_results

    # Save JSON
    # Convert numpy types for JSON serialization
    def convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, defaultdict):
            return dict(obj)
        return obj

    results_path = os.path.join(OUTPUT_DIR, 'vld_experiments_v3_results.json')
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, default=convert)
    print("\nResults: " + results_path)

    print("\n" + "=" * 65)
    print("DONE. 7 experiments, " + str(len(configs)) + " configs.")
