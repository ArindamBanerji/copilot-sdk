"""
VLD Experiments v5 — Parametrize Halting, Compounding, VLD×CI Interaction
==========================================================================
Three broad sweeps to MAP the parameter space before optimizing.

SWEEP-H:  Halting parametrization (τ × halt_criterion × threshold)
SWEEP-C:  Compounding parametrization (fresh data × σ_rate × μ_learning × epochs)
SWEEP-I:  VLD × CI interaction (4-cell: VLD±, CI±)

Usage: python vld_experiments_v5.py [output_dir]
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
# SCENARIO GENERATOR (same centroids, fresh placements per call)
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
        """Each call produces DIFFERENT scenarios (rng advances)."""
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

    def generate_fresh(self, n=500, seed_offset=0, situation_mix=None):
        """Generate with a SPECIFIC seed offset — reproducible fresh data.
        Same centroids (self.mu), different v placements."""
        saved_rng = self.rng
        self.rng = np.random.default_rng(42 + seed_offset + 1000)
        result = self.generate(n, situation_mix)
        self.rng = saved_rng
        return result

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


# ═══════════════════════════════════════════════════════════════
# VLD ENGINE (extended with CI learning)
# ═══════════════════════════════════════════════════════════════

class VLDEngine:
    def __init__(self, mu, sigma, tau=0.1):
        self.mu = mu.copy()
        self.sigma = sigma.copy()
        self.mu_initial = mu.copy()
        self.sigma_initial = sigma.copy()
        self.tau = tau
        self.A = mu.shape[0]
        self.d = mu.shape[1]
        self.past_utility = np.ones(self.d) * 0.5
        self.centroid_mean = np.mean(mu, axis=0)

    def reset(self):
        self.mu = self.mu_initial.copy()
        self.sigma = self.sigma_initial.copy()
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

    def margin(self, P):
        s = np.sort(P)[::-1]
        return float(s[0] - s[1])

    def entropy(self, P):
        P_safe = np.clip(P, 1e-10, 1.0)
        return float(-np.sum(P_safe * np.log(P_safe)))

    def Q_additive(self, v, P, enriched_set=None):
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

    def V_raw(self, v, k, ev):
        v_new = v.copy()
        v_new[k] = ev['value']
        return v_new

    def investigate(self, scenario, budget, q_func=None, v_func=None,
                    halt='fixed', halt_param=None):
        if q_func is None:
            q_func = self.Q_additive
        if v_func is None:
            v_func = self.V_raw

        v = scenario['v_surface'].copy()
        enriched_set = set()
        trace = []

        for step in range(budget):
            a_before, P = self.score(v)
            margin_before = self.margin(P)
            entropy_before = self.entropy(P)

            # ── HALTING CHECKS ──
            if step > 0:
                if halt == 'margin_abs' and margin_before > halt_param:
                    break
                elif halt == 'entropy_abs' and entropy_before < halt_param:
                    break
                elif halt == 'margin_delta':
                    # Stop if margin improvement from last hop < threshold
                    delta = margin_before - trace[-1]['margin_before']
                    if delta < halt_param:
                        break
                elif halt == 'entropy_delta':
                    delta = trace[-1]['entropy_before'] - entropy_before
                    if delta < halt_param:
                        break
                elif halt == 'shift_mag':
                    if trace[-1]['shift'] < halt_param:
                        break
                elif halt == 'no_flip':
                    # Stop if last hop didn't flip the action
                    if not trace[-1]['flipped']:
                        break

            Q = q_func(v, P, enriched_set)
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
                'entropy_before': entropy_before,
                'entropy_after': float(self.entropy(P_after)),
                'shift': float(np.linalg.norm(v - v_before)),
            })

        final_action, _ = self.score(v)
        return {
            'final_action': final_action,
            'correct': final_action == scenario['gt_action'],
            'trace': trace,
            'n_hops': len(trace),
        }

    def random_inv(self, scenario, budget, rng):
        v = scenario['v_surface'].copy()
        dims = list(range(self.d))
        rng.shuffle(dims)
        trace = []
        for k in dims[:budget]:
            a_before, P_before = self.score(v)
            v = self.V_raw(v, k, scenario['evidence'][k])
            a_after, P_after = self.score(v)
            trace.append({
                'dim': k,
                'evidence_type': scenario['evidence'][k]['type'],
                'flipped': a_before != a_after,
                'action_before': a_before, 'action_after': a_after,
                'margin_before': float(self.margin(P_before)),
                'margin_after': float(self.margin(P_after)),
                'shift': float(abs(scenario['evidence'][k]['value'] - scenario['v_surface'][k])),
            })
        a, _ = self.score(v)
        return {'final_action': a, 'correct': a == scenario['gt_action'], 'trace': trace}

    def exhaustive(self, scenario):
        v = scenario['v_surface'].copy()
        for k in range(self.d):
            v = self.V_raw(v, k, scenario['evidence'][k])
        a, _ = self.score(v)
        return {'final_action': a, 'correct': a == scenario['gt_action']}

    # ── CI LEARNING ──

    def ci_learn_sigma(self, scenario, result, rate=0.97):
        """Update sigma from verified outcome."""
        if not result['correct']:
            return
        for t in result['trace']:
            k = t['dim']
            if t['evidence_type'] == 'informative':
                self.sigma[k] = max(0.02, self.sigma[k] * rate)
            elif t['evidence_type'] == 'misleading':
                self.sigma[k] = min(0.40, self.sigma[k] * (2 - rate))

    def ci_learn_mu(self, scenario, result, lr=0.01):
        """Update centroids toward verified v (like centroid update in production)."""
        if not result['correct']:
            return
        gt = scenario['gt_action']
        v_final = scenario['v_surface'].copy()
        for t in result['trace']:
            v_final = self.V_raw(v_final, t['dim'], scenario['evidence'][t['dim']])
        # Move centroid toward verified v
        self.mu[gt] = self.mu[gt] + lr * (v_final - self.mu[gt])

    def ci_learn_utility(self, result, lr=0.01):
        """Update past_utility from investigation outcome."""
        for t in result['trace']:
            k = t['dim']
            if result['correct']:
                self.past_utility[k] = min(1.0, self.past_utility[k] + lr)
            else:
                self.past_utility[k] = max(0.1, self.past_utility[k] - lr * 0.5)


# ═══════════════════════════════════════════════════════════════
# SWEEP-H: HALTING PARAMETRIZATION
# ═══════════════════════════════════════════════════════════════

def sweep_halting(gen, scenarios):
    """Broad sweep of halting strategies across τ values."""
    print("\n" + "=" * 65)
    print("SWEEP-H: Halting Parametrization")
    print("=" * 65)

    tau_values = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0]

    halt_configs = [
        ('fixed', 'fixed', None),
        ('margin_abs_0.3', 'margin_abs', 0.3),
        ('margin_abs_0.5', 'margin_abs', 0.5),
        ('margin_abs_0.7', 'margin_abs', 0.7),
        ('margin_abs_0.9', 'margin_abs', 0.9),
        ('margin_abs_0.95', 'margin_abs', 0.95),
        ('margin_abs_0.99', 'margin_abs', 0.99),
        ('entropy_abs_0.1', 'entropy_abs', 0.1),
        ('entropy_abs_0.3', 'entropy_abs', 0.3),
        ('entropy_abs_0.5', 'entropy_abs', 0.5),
        ('margin_delta_0.01', 'margin_delta', 0.01),
        ('margin_delta_0.05', 'margin_delta', 0.05),
        ('margin_delta_0.1', 'margin_delta', 0.1),
        ('entropy_delta_0.01', 'entropy_delta', 0.01),
        ('entropy_delta_0.05', 'entropy_delta', 0.05),
        ('shift_mag_0.05', 'shift_mag', 0.05),
        ('shift_mag_0.1', 'shift_mag', 0.1),
        ('shift_mag_0.2', 'shift_mag', 0.2),
        ('no_flip', 'no_flip', None),
    ]

    results = []

    for tau in tau_values:
        engine = VLDEngine(gen.mu, gen.sigma, tau=tau)

        # Measure margin distribution at SP (no investigation)
        sp_margins = [engine.margin(engine.score(s['v_surface'])[1]) for s in scenarios[:100]]
        median_sp_margin = float(np.median(sp_margins))
        p90_sp_margin = float(np.percentile(sp_margins, 90))

        print("\n  τ=" + str(tau) + "  median_SP_margin=" + str(round(median_sp_margin, 3)) +
              "  p90=" + str(round(p90_sp_margin, 3)))

        for name, halt, param in halt_configs:
            runs = [engine.investigate(s, budget=6, halt=halt, halt_param=param)
                    for s in scenarios]
            acc = sum(1 for r in runs if r['correct']) / len(scenarios)
            avg_hops = np.mean([r['n_hops'] for r in runs])
            results.append({
                'tau': tau, 'halt': name, 'accuracy': round(acc, 4),
                'avg_hops': round(float(avg_hops), 2),
                'median_sp_margin': round(median_sp_margin, 3),
            })

            if avg_hops > 1.1 or name == 'fixed' or 'no_flip' in name:
                print("    " + name.ljust(22) +
                      "acc=" + str(round(acc, 3)).ljust(8) +
                      "hops=" + str(round(avg_hops, 2)))

    return results


# ═══════════════════════════════════════════════════════════════
# SWEEP-C: COMPOUNDING PARAMETRIZATION
# ═══════════════════════════════════════════════════════════════

def sweep_compounding(gen):
    """Broad sweep of compounding with fresh data, learning rates, μ learning."""
    print("\n" + "=" * 65)
    print("SWEEP-C: Compounding Parametrization")
    print("=" * 65)

    n_epochs = 15
    budget = 2

    configs = [
        # (name, fresh_data, sigma_rate, mu_lr, utility_lr)
        ('static_same',       False, None,  None,  None),
        ('sigma_0.99_same',   False, 0.99,  None,  None),
        ('sigma_0.97_same',   False, 0.97,  None,  None),
        ('sigma_0.95_same',   False, 0.95,  None,  None),
        ('sigma_0.90_same',   False, 0.90,  None,  None),
        ('sigma_0.97_fresh',  True,  0.97,  None,  None),
        ('sigma_0.95_fresh',  True,  0.95,  None,  None),
        ('sigma_0.90_fresh',  True,  0.90,  None,  None),
        ('mu_0.01_fresh',     True,  None,  0.01,  None),
        ('mu_0.05_fresh',     True,  None,  0.05,  None),
        ('mu_0.10_fresh',     True,  None,  0.10,  None),
        ('all_slow_fresh',    True,  0.97,  0.01,  0.01),
        ('all_med_fresh',     True,  0.95,  0.05,  0.05),
        ('all_fast_fresh',    True,  0.90,  0.10,  0.10),
        ('util_only_fresh',   True,  None,  None,  0.05),
    ]

    all_curves = {}

    for name, fresh, sigma_rate, mu_lr, util_lr in configs:
        engine = VLDEngine(gen.mu, gen.sigma)
        curve = []

        print("\n  Config: " + name)

        for epoch in range(n_epochs):
            if fresh:
                scenarios = gen.generate_fresh(n=300, seed_offset=epoch)
            else:
                if epoch == 0:
                    scenarios_fixed = gen.generate_fresh(n=300, seed_offset=999)
                scenarios = scenarios_fixed

            correct = 0
            q_informative = 0
            q_total = 0

            for s in scenarios:
                r = engine.investigate(s, budget)
                if r['correct']:
                    correct += 1
                for t in r['trace']:
                    q_total += 1
                    if t['evidence_type'] == 'informative':
                        q_informative += 1

                # CI learning
                if sigma_rate is not None:
                    engine.ci_learn_sigma(s, r, rate=sigma_rate)
                if mu_lr is not None:
                    engine.ci_learn_mu(s, r, lr=mu_lr)
                if util_lr is not None:
                    engine.ci_learn_utility(r, lr=util_lr)

            acc = correct / len(scenarios)
            rq = q_informative / max(q_total, 1)
            sd = float(np.mean(np.abs(engine.sigma - gen.sigma)))
            md = float(np.mean(np.abs(engine.mu - gen.mu)))

            curve.append({
                'epoch': epoch, 'accuracy': round(acc, 4),
                'routing_q': round(rq, 4),
                'sigma_drift': round(sd, 4),
                'mu_drift': round(md, 4),
            })

        all_curves[name] = curve
        # Print first and last
        print("    Epoch 0: acc=" + str(curve[0]['accuracy']) +
              "  rq=" + str(curve[0]['routing_q']) +
              "  σ_drift=" + str(curve[0]['sigma_drift']) +
              "  μ_drift=" + str(curve[0]['mu_drift']))
        print("    Epoch " + str(n_epochs-1) + ": acc=" + str(curve[-1]['accuracy']) +
              "  rq=" + str(curve[-1]['routing_q']) +
              "  σ_drift=" + str(curve[-1]['sigma_drift']) +
              "  μ_drift=" + str(curve[-1]['mu_drift']))
        delta_acc = curve[-1]['accuracy'] - curve[0]['accuracy']
        print("    Δ_acc: " + ("+" if delta_acc >= 0 else "") + str(round(delta_acc, 4)))

    return all_curves


# ═══════════════════════════════════════════════════════════════
# SWEEP-I: VLD × CI INTERACTION
# ═══════════════════════════════════════════════════════════════

def sweep_interaction(gen):
    """4-cell experiment: VLD±, CI±. Tests superadditivity."""
    print("\n" + "=" * 65)
    print("SWEEP-I: VLD × CI Interaction")
    print("=" * 65)

    n_epochs = 15
    budget = 2

    # 4 cells:
    # (1) No VLD, No CI  = random routing, static centroids
    # (2) No VLD, CI     = random routing, centroids learn
    # (3) VLD, No CI     = Q routing, static centroids
    # (4) VLD, CI        = Q routing, centroids learn

    cells = {
        'random_static': {'use_vld': False, 'use_ci': False},
        'random_CI':     {'use_vld': False, 'use_ci': True},
        'VLD_static':    {'use_vld': True,  'use_ci': False},
        'VLD_CI':        {'use_vld': True,  'use_ci': True},
    }

    all_curves = {}

    for cell_name, cfg in cells.items():
        engine = VLDEngine(gen.mu, gen.sigma)
        curve = []
        rng = np.random.default_rng(99)

        print("\n  Cell: " + cell_name +
              " (VLD=" + str(cfg['use_vld']) + ", CI=" + str(cfg['use_ci']) + ")")

        for epoch in range(n_epochs):
            scenarios = gen.generate_fresh(n=300, seed_offset=epoch)
            rng_epoch = np.random.default_rng(99 + epoch)

            correct = 0
            q_informative = 0
            q_total = 0

            for s in scenarios:
                if cfg['use_vld']:
                    r = engine.investigate(s, budget)
                else:
                    r = engine.random_inv(s, budget, rng_epoch)

                if r['correct']:
                    correct += 1

                for t in r.get('trace', []):
                    q_total += 1
                    if t['evidence_type'] == 'informative':
                        q_informative += 1

                # CI learning (sigma + mu)
                if cfg['use_ci']:
                    engine.ci_learn_sigma(s, r, rate=0.95)
                    engine.ci_learn_mu(s, r, lr=0.05)

            acc = correct / len(scenarios)
            rq = q_informative / max(q_total, 1)

            curve.append({
                'epoch': epoch,
                'accuracy': round(acc, 4),
                'routing_q': round(rq, 4),
            })

        all_curves[cell_name] = curve
        print("    Epoch 0: acc=" + str(curve[0]['accuracy']))
        print("    Epoch " + str(n_epochs-1) + ": acc=" + str(curve[-1]['accuracy']))
        delta = curve[-1]['accuracy'] - curve[0]['accuracy']
        print("    Δ_acc: " + ("+" if delta >= 0 else "") + str(round(delta, 4)))

    # Superadditivity test
    print("\n  --- Superadditivity Test (epoch " + str(n_epochs-1) + ") ---")
    baseline = all_curves['random_static'][-1]['accuracy']
    ci_only = all_curves['random_CI'][-1]['accuracy'] - baseline
    vld_only = all_curves['VLD_static'][-1]['accuracy'] - baseline
    vld_ci = all_curves['VLD_CI'][-1]['accuracy'] - baseline
    additive = ci_only + vld_only
    interaction = vld_ci - additive

    print("  Baseline (random+static): " + str(round(baseline, 4)))
    print("  CI-only marginal:         +" + str(round(ci_only, 4)))
    print("  VLD-only marginal:        +" + str(round(vld_only, 4)))
    print("  Additive prediction:      +" + str(round(additive, 4)))
    print("  VLD+CI actual:            +" + str(round(vld_ci, 4)))
    print("  Interaction term:         " + ("+" if interaction >= 0 else "") +
          str(round(interaction, 4)))
    print("  Superadditive:            " + ("YES" if interaction > 0 else "NO"))

    return all_curves, {
        'baseline': round(baseline, 4),
        'ci_only': round(ci_only, 4),
        'vld_only': round(vld_only, 4),
        'additive_prediction': round(additive, 4),
        'vld_ci_actual': round(vld_ci, 4),
        'interaction': round(interaction, 4),
    }


# ═══════════════════════════════════════════════════════════════
# CHARTS
# ═══════════════════════════════════════════════════════════════

def chart_halting_pareto(results, out_dir):
    """Accuracy vs avg_hops Pareto for each τ."""
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    tau_values = sorted(set(r['tau'] for r in results))

    for i, tau in enumerate(tau_values):
        ax = axes[i // 3][i % 3]
        subset = [r for r in results if r['tau'] == tau]
        hops = [r['avg_hops'] for r in subset]
        accs = [r['accuracy'] for r in subset]
        names = [r['halt'] for r in subset]

        ax.scatter(hops, accs, s=40, color='#2563EB', zorder=5)
        for h, a, n in zip(hops, accs, names):
            if a > 0.75 or h > 1.5:
                ax.annotate(n.replace('_','\n'), (h, a), fontsize=5,
                           ha='center', va='bottom')
        ax.set_xlabel('Avg Hops')
        ax.set_ylabel('Accuracy')
        ax.set_title('τ=' + str(tau))
        ax.set_xlim(0.5, 6.5)
        ax.set_ylim(0, 1.0)

    plt.suptitle('Halting Pareto: Accuracy vs Depth by Temperature', fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'val5_halting_pareto.png'), dpi=200)
    plt.close()
    print("  Chart: val5_halting_pareto.png")


def chart_compounding_curves(curves, out_dir):
    """Accuracy over epochs for key configs."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Same-data configs
    colors_same = {'static_same': '#6B7280', 'sigma_0.97_same': '#DC2626',
                   'sigma_0.95_same': '#F59E0B', 'sigma_0.90_same': '#9333EA'}
    for name, color in colors_same.items():
        if name in curves:
            eps = [c['epoch'] for c in curves[name]]
            accs = [c['accuracy'] for c in curves[name]]
            ax1.plot(eps, accs, '-o', color=color, lw=1.5, ms=4, label=name)
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Accuracy')
    ax1.set_title('Compounding: Same Scenarios')
    ax1.legend(fontsize=7)
    ax1.set_ylim(0.5, 1.0)

    # Fresh-data configs
    colors_fresh = {
        'sigma_0.97_fresh': '#DC2626', 'sigma_0.95_fresh': '#F59E0B',
        'all_slow_fresh': '#2563EB', 'all_med_fresh': '#059669',
        'all_fast_fresh': '#9333EA', 'mu_0.05_fresh': '#D97706',
    }
    for name, color in colors_fresh.items():
        if name in curves:
            eps = [c['epoch'] for c in curves[name]]
            accs = [c['accuracy'] for c in curves[name]]
            ax2.plot(eps, accs, '-o', color=color, lw=1.5, ms=4, label=name)
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy')
    ax2.set_title('Compounding: Fresh Scenarios Each Epoch')
    ax2.legend(fontsize=7)
    ax2.set_ylim(0.5, 1.0)

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'val5_compounding_curves.png'), dpi=200)
    plt.close()
    print("  Chart: val5_compounding_curves.png")


def chart_interaction(curves, interaction, out_dir):
    """4-cell interaction plot."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    colors = {'random_static': '#6B7280', 'random_CI': '#DC2626',
              'VLD_static': '#F59E0B', 'VLD_CI': '#2563EB'}
    for name, color in colors.items():
        eps = [c['epoch'] for c in curves[name]]
        accs = [c['accuracy'] for c in curves[name]]
        ax1.plot(eps, accs, '-o', color=color, lw=2, ms=5, label=name)
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Accuracy')
    ax1.set_title('VLD × CI: 4-Cell Experiment')
    ax1.legend()
    ax1.set_ylim(0.5, 1.0)

    # Bar chart of marginal contributions
    names = ['CI only', 'VLD only', 'Additive\nprediction', 'VLD+CI\nactual']
    vals = [interaction['ci_only'], interaction['vld_only'],
            interaction['additive_prediction'], interaction['vld_ci_actual']]
    colors_bar = ['#DC2626', '#F59E0B', '#6B7280', '#2563EB']
    bars = ax2.bar(range(len(names)), vals, color=colors_bar, edgecolor='white')
    ax2.set_xticks(range(len(names)))
    ax2.set_xticklabels(names, fontsize=9)
    ax2.set_ylabel('Marginal Accuracy Gain')
    ax2.set_title('Superadditivity: ' + ('YES' if interaction['interaction'] > 0 else 'NO') +
                  ' (interaction=' + str(round(interaction['interaction'], 3)) + ')')
    for b, v in zip(bars, vals):
        ax2.text(b.get_x() + b.get_width()/2, b.get_height() + 0.002,
                str(round(v, 3)), ha='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'val5_interaction.png'), dpi=200)
    plt.close()
    print("  Chart: val5_interaction.png")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("VLD Experiments v5 — Halting, Compounding, VLD×CI")
    print("=" * 65)

    gen = ScenarioGenerator(d=6, A=4, seed=42)
    scenarios = gen.generate(n=500)

    all_results = {}

    # SWEEP-H: Halting
    all_results['halting'] = sweep_halting(gen, scenarios)
    chart_halting_pareto(all_results['halting'], OUTPUT_DIR)

    # SWEEP-C: Compounding
    all_results['compounding'] = sweep_compounding(gen)
    chart_compounding_curves(all_results['compounding'], OUTPUT_DIR)

    # SWEEP-I: Interaction
    interaction_curves, interaction_test = sweep_interaction(gen)
    all_results['interaction_curves'] = {k: v for k, v in interaction_curves.items()}
    all_results['interaction_test'] = interaction_test
    chart_interaction(interaction_curves, interaction_test, OUTPUT_DIR)

    # Save
    results_path = os.path.join(OUTPUT_DIR, 'vld_experiments_v5_results.json')

    def convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, default=convert)
    print("\nResults: " + results_path)

    print("\n" + "=" * 65)
    print("DONE. 3 sweeps, 3 charts.")
