"""
VLD Graph Reasoning — Comprehensive Experiment Framework v2
=============================================================
Modular Q/K/V component variants × routing strategies × situation types.

Design principles:
  1. Realistic scenario mix (S1-S6, not all-wrong-side)
  2. Pluggable Q components (precision × discriminative × uncertainty)
  3. Pluggable K components (static, utility-weighted)
  4. Pluggable V update rules (raw, gated, consistency-checked)
  5. Pluggable routing strategies (greedy, RNN, LSTM, CI-integrated)
  6. Clean comparison metrics

Usage: python vld_experiments_v2.py [output_dir]
"""

import sys, os, json
import numpy as np
from collections import defaultdict
from itertools import product as cartesian

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


# ═══════════════════════════════════════════════════════════════
# MODULE 1: SCENARIO GENERATOR — Situation-Realistic
# ═══════════════════════════════════════════════════════════════

class ScenarioGenerator:
    """Generates scenarios with controlled situation distribution."""

    def __init__(self, d=6, A=4, seed=42):
        self.rng = np.random.default_rng(seed)
        self.d = d
        self.A = A

        # Centroids: well-separated in [0.15, 0.85]
        self.mu = self._generate_centroids()

        # Per-dimension sigma (simulates learned DK precision)
        # Some dimensions high precision, some low
        self.sigma = self.rng.uniform(0.05, 0.30, d)

    def _generate_centroids(self):
        mu = self.rng.uniform(0.15, 0.85, (self.A, self.d))
        # Ensure reasonable separation
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
        """Generate n scenarios with given situation distribution."""
        if situation_mix is None:
            situation_mix = {'S1': 0.20, 'S2': 0.10, 'S3': 0.25,
                            'S4': 0.25, 'S5': 0.10, 'S6': 0.10}

        scenarios = []
        for sit, frac in situation_mix.items():
            count = int(n * frac)
            for _ in range(count):
                s = getattr(self, '_gen_' + sit.lower())()
                s['situation'] = sit
                scenarios.append(s)

        # Fill remainder
        while len(scenarios) < n:
            s = self._gen_s3()
            s['situation'] = 'S3'
            scenarios.append(s)

        self.rng.shuffle(scenarios)
        return scenarios

    def _gen_s1(self):
        """S1: Surface-sufficient. v near correct centroid. 0-1 wrong dims."""
        gt = self.rng.integers(0, self.A)
        v = self.mu[gt] + self.rng.normal(0, 0.05, self.d)
        v = np.clip(v, 0, 1)
        return self._build_scenario(v, gt, n_informative=0)

    def _gen_s2(self):
        """S2: Uniformly uncertain. v equidistant from multiple centroids."""
        gt = self.rng.integers(0, self.A)
        # Place v at centroid mean (equidistant from all)
        v = np.mean(self.mu, axis=0) + self.rng.normal(0, 0.08, self.d)
        v = np.clip(v, 0, 1)
        return self._build_scenario(v, gt, n_informative=self.d)

    def _gen_s3(self):
        """S3: Directional. v correct on most dims, 1-2 wrong. Sharp EVOI peak."""
        gt = self.rng.integers(0, self.A)
        wrong = (gt + 1 + self.rng.integers(0, self.A - 1)) % self.A

        v = self.mu[gt].copy() + self.rng.normal(0, 0.05, self.d)

        # Set 1-2 dimensions to the WRONG centroid's values
        n_wrong = self.rng.integers(1, 3)
        wrong_dims = self.rng.choice(self.d, size=n_wrong, replace=False)
        for k in wrong_dims:
            v[k] = self.mu[wrong, k] + self.rng.normal(0, 0.05)

        v = np.clip(v, 0, 1)
        return self._build_scenario(v, gt, n_informative=n_wrong,
                                     informative_dims=list(wrong_dims))

    def _gen_s4(self):
        """S4: Conditional. Which dims matter depends on evidence from others.
        Dim k1 is wrong (surface). After enriching k1, the top-2 actions
        change, making dim k2 the new decision-critical dimension."""
        gt = self.rng.integers(0, self.A)
        wrong1 = (gt + 1 + self.rng.integers(0, self.A - 1)) % self.A

        # Start near wrong1 on 2-3 dimensions
        v = self.mu[gt].copy() + self.rng.normal(0, 0.05, self.d)
        wrong_dims = list(self.rng.choice(self.d, size=3, replace=False))

        # Dim 0 (wrong_dims[0]): clearly wrong, high EVOI at v_0
        v[wrong_dims[0]] = self.mu[wrong1, wrong_dims[0]] + self.rng.normal(0, 0.05)

        # Dim 1 (wrong_dims[1]): looks OK at v_0 but becomes critical after fixing dim 0
        # Set it near midpoint of a DIFFERENT pair of actions
        wrong2 = (gt + 2) % self.A if self.A > 2 else wrong1
        v[wrong_dims[1]] = (self.mu[gt, wrong_dims[1]] + self.mu[wrong2, wrong_dims[1]]) / 2

        # Dim 2 (wrong_dims[2]): slightly wrong, moderate shift needed
        v[wrong_dims[2]] = self.mu[wrong1, wrong_dims[2]] * 0.6 + self.mu[gt, wrong_dims[2]] * 0.4

        v = np.clip(v, 0, 1)
        return self._build_scenario(v, gt, n_informative=3,
                                     informative_dims=wrong_dims, conditional=True)

    def _gen_s5(self):
        """S5: Adversarial. Some evidence is misleading (pushes toward wrong action)."""
        gt = self.rng.integers(0, self.A)
        wrong = (gt + 1 + self.rng.integers(0, self.A - 1)) % self.A

        v = self.mu[gt].copy() + self.rng.normal(0, 0.05, self.d)
        n_wrong = 2
        wrong_dims = list(self.rng.choice(self.d, size=n_wrong, replace=False))
        for k in wrong_dims:
            v[k] = self.mu[wrong, k] + self.rng.normal(0, 0.05)

        v = np.clip(v, 0, 1)

        # Pick 1-2 misleading dims (evidence pushes toward wrong)
        remaining = [k for k in range(self.d) if k not in wrong_dims]
        n_misleading = min(2, len(remaining))
        misleading_dims = list(self.rng.choice(remaining, size=n_misleading, replace=False))

        return self._build_scenario(v, gt, n_informative=n_wrong,
                                     informative_dims=wrong_dims,
                                     misleading_dims=misleading_dims)

    def _gen_s6(self):
        """S6: Compositional. No single dim crosses boundary. Need 2-3 together."""
        gt = self.rng.integers(0, self.A)
        wrong = (gt + 1 + self.rng.integers(0, self.A - 1)) % self.A

        # Place v so it's in wrong cell but CLOSE to boundary
        boundary_mid = (self.mu[gt] + self.mu[wrong]) / 2
        # Slightly on the wrong side
        v = boundary_mid + 0.08 * (self.mu[wrong] - self.mu[gt]) / np.linalg.norm(self.mu[wrong] - self.mu[gt])
        v += self.rng.normal(0, 0.03, self.d)
        v = np.clip(v, 0, 1)

        # Multiple dims need partial shifts
        n_needed = self.rng.integers(2, 4)
        needed_dims = list(self.rng.choice(self.d, size=n_needed, replace=False))

        return self._build_scenario(v, gt, n_informative=n_needed,
                                     informative_dims=needed_dims, compositional=True)

    def _build_scenario(self, v, gt, n_informative=0, informative_dims=None,
                        misleading_dims=None, conditional=False, compositional=False):
        """Build scenario with evidence per dimension."""
        if informative_dims is None:
            informative_dims = []
        if misleading_dims is None:
            misleading_dims = []

        evidence = {}
        for k in range(self.d):
            if k in informative_dims:
                # Informative: shifts toward correct centroid
                target = self.mu[gt, k]
                shift = abs(target - v[k])
                if compositional:
                    # Smaller shifts (need multiple to cross)
                    target = v[k] + 0.6 * (target - v[k])
                    shift = abs(target - v[k])
                conf = self.rng.uniform(0.7, 1.0)
                evidence[k] = {
                    'value': np.clip(target + self.rng.normal(0, 0.03), 0, 1),
                    'shift': shift,
                    'confidence': conf,
                    'type': 'informative'
                }
            elif k in misleading_dims:
                # Misleading: shifts AWAY from correct centroid
                wrong_a = (gt + 1) % self.A
                target = self.mu[wrong_a, k]
                conf = self.rng.uniform(0.4, 0.8)  # lower confidence
                evidence[k] = {
                    'value': np.clip(target + self.rng.normal(0, 0.05), 0, 1),
                    'shift': abs(target - v[k]),
                    'confidence': conf,
                    'type': 'misleading'
                }
            else:
                # Neutral: small random perturbation
                evidence[k] = {
                    'value': np.clip(v[k] + self.rng.normal(0, 0.03), 0, 1),
                    'shift': abs(self.rng.normal(0, 0.03)),
                    'confidence': self.rng.uniform(0.5, 0.9),
                    'type': 'neutral'
                }

        return {
            'v_surface': v,
            'gt_action': gt,
            'evidence': evidence,
            'n_informative': n_informative,
            'informative_dims': informative_dims,
            'misleading_dims': misleading_dims,
            'conditional': conditional,
            'compositional': compositional,
        }


# ═══════════════════════════════════════════════════════════════
# MODULE 2: Q COMPONENT VARIANTS
# ═══════════════════════════════════════════════════════════════

class QComponents:
    """Pluggable Q component variants."""

    @staticmethod
    def precision_none(sigma, k):
        return 1.0

    @staticmethod
    def precision_inv_sigma(sigma, k):
        return 1.0 / max(sigma[k], 0.01)

    @staticmethod
    def precision_inv_sigma2(sigma, k):
        return 1.0 / max(sigma[k] ** 2, 0.001)

    @staticmethod
    def disc_none(mu, a1, a2, k):
        return 1.0

    @staticmethod
    def disc_top2(mu, a1, a2, k):
        return abs(mu[a1, k] - mu[a2, k])

    @staticmethod
    def disc_all_spread(mu, a1, a2, k):
        return np.std(mu[:, k])

    @staticmethod
    def disc_max_any(mu, a1, a2, k):
        return max(abs(mu[a1, k] - mu[a, k]) for a in range(mu.shape[0]))

    @staticmethod
    def unc_none(v, mu, a1, a2, k):
        return 1.0

    @staticmethod
    def unc_gap(v, mu, a1, a2, k):
        """Simple gap from nearest centroid."""
        return abs(v[k] - mu[a1, k])

    @staticmethod
    def unc_boundary(v, mu, a1, a2, k):
        """Corrected boundary proximity (high near boundary, 0 far away)."""
        mid = (mu[a1, k] + mu[a2, k]) / 2
        hw = abs(mu[a1, k] - mu[a2, k]) / 2
        if hw < 1e-8:
            return 0.0
        return max(0, 1 - abs(v[k] - mid) / hw)

    @staticmethod
    def unc_wrong_side(v, mu, a1, a2, k):
        """Wrong-side indicator: high when v[k] is closer to a2 than a1 on dim k.
        Unlike gap (continuous distance), this is a step function that identifies
        which dimensions are on the WRONG SIDE of the decision boundary."""
        d1 = abs(v[k] - mu[a1, k])
        d2 = abs(v[k] - mu[a2, k])
        if d2 < d1:
            return d1 - d2  # magnitude of being on wrong side
        return 0.0  # on correct side — no need to read

    @staticmethod
    def unc_margin_sensitivity(v, mu, a1, a2, k):
        """How much would moving v[k] change the margin between a1 and a2?
        Proportional to the difference in signed distances."""
        return abs((v[k] - mu[a1, k])**2 - (v[k] - mu[a2, k])**2)


# ═══════════════════════════════════════════════════════════════
# MODULE 3: V UPDATE VARIANTS
# ═══════════════════════════════════════════════════════════════

class VUpdates:
    """Pluggable V (state update) variants."""

    @staticmethod
    def raw_replace(v, k, evidence):
        """Replace v[k] with evidence value directly."""
        v_new = v.copy()
        v_new[k] = evidence['value']
        return v_new

    @staticmethod
    def confidence_gated(v, k, evidence):
        """Blend by confidence: conf * evidence + (1-conf) * current."""
        v_new = v.copy()
        conf = evidence['confidence']
        v_new[k] = conf * evidence['value'] + (1 - conf) * v[k]
        return v_new

    @staticmethod
    def consistency_checked(v, k, evidence, threshold=0.5):
        """Gate: if evidence contradicts current v by > threshold, attenuate."""
        v_new = v.copy()
        conf = evidence['confidence']
        delta = abs(evidence['value'] - v[k])
        if delta > threshold:
            # Large contradiction — use lower effective confidence
            eff_conf = conf * 0.5
        else:
            eff_conf = conf
        v_new[k] = eff_conf * evidence['value'] + (1 - eff_conf) * v[k]
        return v_new


# ═══════════════════════════════════════════════════════════════
# MODULE 4: ROUTING STRATEGIES
# ═══════════════════════════════════════════════════════════════

class VLDEngine:
    """Modular VLD engine with pluggable components."""

    def __init__(self, mu, sigma, tau=0.1):
        self.mu = mu
        self.sigma = sigma
        self.tau = tau
        self.A = mu.shape[0]
        self.d = mu.shape[1]
        # Past utility tracking (for K learning)
        self.past_utility = np.ones(self.d) * 0.5  # start uniform

    def score(self, v):
        dists = np.array([np.sum((1/self.sigma**2) * (v - self.mu[a])**2)
                         for a in range(self.A)])
        logits = -dists / self.tau
        logits -= np.max(logits)
        P = np.exp(logits) / np.sum(np.exp(logits))
        return int(np.argmax(P)), P

    def top2(self, P):
        order = np.argsort(-P)
        return order[0], order[1]

    def compute_Q(self, v, P, precision_fn, disc_fn, unc_fn,
                  composition='multiply', enriched_set=None):
        """Compute Q vector with pluggable components."""
        a1, a2 = self.top2(P)
        Q = np.zeros(self.d)
        for k in range(self.d):
            if enriched_set and k in enriched_set:
                Q[k] = -1
                continue
            p = precision_fn(self.sigma, k)
            d_val = disc_fn(self.mu, a1, a2, k)
            u = unc_fn(v, self.mu, a1, a2, k)

            if composition == 'multiply':
                Q[k] = p * d_val * u
            elif composition == 'add':
                Q[k] = p + d_val + u
            elif composition == 'max':
                Q[k] = max(p, d_val, u)
        return Q

    def investigate(self, scenario, budget, precision_fn, disc_fn, unc_fn,
                    v_update_fn, composition='multiply', use_rnn=True,
                    use_utility=False):
        """Run investigation with specified component variants."""
        v = scenario['v_surface'].copy()
        enriched_set = set()
        trace = []

        for step in range(budget):
            a_before, P = self.score(v)

            if use_rnn:
                # RNN: recompute Q from current v_t
                Q = self.compute_Q(v, P, precision_fn, disc_fn, unc_fn,
                                  composition, enriched_set)
            else:
                # Non-RNN: use Q from v_0 only (parallel-like within sequential)
                if step == 0:
                    Q_fixed = self.compute_Q(v, P, precision_fn, disc_fn, unc_fn,
                                            composition, enriched_set)
                Q = Q_fixed.copy()
                for ek in enriched_set:
                    Q[ek] = -1

            if use_utility:
                # K component: weight Q by past utility
                Q = Q * self.past_utility

            if np.max(Q) <= 0:
                break

            k_star = int(np.argmax(Q))
            v = v_update_fn(v, k_star, scenario['evidence'][k_star])
            enriched_set.add(k_star)

            a_after, P_after = self.score(v)
            trace.append({
                'step': step, 'dim': k_star,
                'action_before': a_before, 'action_after': a_after,
                'flipped': a_before != a_after,
                'evidence_type': scenario['evidence'][k_star]['type'],
            })

        final_action, _ = self.score(v)
        return {
            'final_action': final_action,
            'correct': final_action == scenario['gt_action'],
            'trace': trace,
            'n_hops': len(trace),
        }

    def random_investigate(self, scenario, budget, v_update_fn, rng):
        """Random routing baseline."""
        v = scenario['v_surface'].copy()
        dims = list(range(self.d))
        rng.shuffle(dims)
        for k in dims[:budget]:
            v = v_update_fn(v, k, scenario['evidence'][k])
        action, _ = self.score(v)
        return {'final_action': action, 'correct': action == scenario['gt_action']}

    def exhaustive_investigate(self, scenario, v_update_fn):
        """Read all dimensions."""
        v = scenario['v_surface'].copy()
        for k in range(self.d):
            v = v_update_fn(v, k, scenario['evidence'][k])
        action, _ = self.score(v)
        return {'final_action': action, 'correct': action == scenario['gt_action']}

    def update_utility(self, trace, was_correct):
        """Update past_utility from investigation outcome."""
        for t in trace:
            k = t['dim']
            if was_correct:
                self.past_utility[k] = min(1.0, self.past_utility[k] + 0.05)
            else:
                self.past_utility[k] = max(0.1, self.past_utility[k] - 0.02)


# ═══════════════════════════════════════════════════════════════
# MODULE 5: EXPERIMENT RUNNERS
# ═══════════════════════════════════════════════════════════════

def run_q_component_sweep(engine, scenarios, budget=2, rng=None):
    """Test all Q component combinations."""
    if rng is None:
        rng = np.random.default_rng(99)

    precision_variants = {
        'P0_none': QComponents.precision_none,
        'P1_inv_s': QComponents.precision_inv_sigma,
        'P2_inv_s2': QComponents.precision_inv_sigma2,
    }
    disc_variants = {
        'D0_none': QComponents.disc_none,
        'D1_top2': QComponents.disc_top2,
        'D2_spread': QComponents.disc_all_spread,
        'D3_max': QComponents.disc_max_any,
    }
    unc_variants = {
        'U0_none': QComponents.unc_none,
        'U1_gap': QComponents.unc_gap,
        'U2_boundary': QComponents.unc_boundary,
        'U3_wrong_side': QComponents.unc_wrong_side,
        'U4_margin': QComponents.unc_margin_sensitivity,
    }

    results = {}

    # Single-pass baseline
    sp_correct = sum(1 for s in scenarios if engine.score(s['v_surface'])[0] == s['gt_action'])
    results['single_pass'] = sp_correct / len(scenarios)

    # Random baseline
    rand_correct = sum(1 for s in scenarios
                       if engine.random_investigate(s, budget, VUpdates.confidence_gated, rng)['correct'])
    results['random'] = rand_correct / len(scenarios)

    # Exhaustive baseline
    exh_correct = sum(1 for s in scenarios
                      if engine.exhaustive_investigate(s, VUpdates.confidence_gated)['correct'])
    results['exhaustive'] = exh_correct / len(scenarios)

    # Test each combination
    for p_name, p_fn in precision_variants.items():
        for d_name, d_fn in disc_variants.items():
            for u_name, u_fn in unc_variants.items():
                key = p_name + "+" + d_name + "+" + u_name
                correct = 0
                for s in scenarios:
                    r = engine.investigate(s, budget, p_fn, d_fn, u_fn,
                                          VUpdates.confidence_gated)
                    if r['correct']:
                        correct += 1
                results[key] = correct / len(scenarios)

    return results


def run_routing_comparison(engine, scenarios, budget=2, rng=None):
    """Compare routing strategies."""
    if rng is None:
        rng = np.random.default_rng(99)

    Q = QComponents
    V = VUpdates

    strategies = {}

    # 1. Single pass (no investigation)
    sp = sum(1 for s in scenarios if engine.score(s['v_surface'])[0] == s['gt_action'])
    strategies['01_single_pass'] = sp / len(scenarios)

    # 2. Random
    rc = sum(1 for s in scenarios
             if engine.random_investigate(s, budget, V.confidence_gated, rng)['correct'])
    strategies['02_random'] = rc / len(scenarios)

    # 3. Exhaustive
    ec = sum(1 for s in scenarios
             if engine.exhaustive_investigate(s, V.confidence_gated)['correct'])
    strategies['03_exhaustive'] = ec / len(scenarios)

    # 4. Q-greedy (P2+D1+U1) — no RNN, no recompute
    gc = sum(1 for s in scenarios
             if engine.investigate(s, budget, Q.precision_inv_sigma2, Q.disc_top2,
                                  Q.unc_gap, V.confidence_gated, use_rnn=False)['correct'])
    strategies['04_Q_greedy_fixed'] = gc / len(scenarios)

    # 5. Q-RNN (recompute Q at each step)
    rc2 = sum(1 for s in scenarios
              if engine.investigate(s, budget, Q.precision_inv_sigma2, Q.disc_top2,
                                   Q.unc_gap, V.confidence_gated, use_rnn=True)['correct'])
    strategies['05_Q_RNN'] = rc2 / len(scenarios)

    # 6. Q-RNN + boundary uncertainty
    rc3 = sum(1 for s in scenarios
              if engine.investigate(s, budget, Q.precision_inv_sigma2, Q.disc_top2,
                                   Q.unc_boundary, V.confidence_gated, use_rnn=True)['correct'])
    strategies['06_Q_RNN_boundary'] = rc3 / len(scenarios)

    # 7. Q-RNN + margin sensitivity
    rc4 = sum(1 for s in scenarios
              if engine.investigate(s, budget, Q.precision_inv_sigma2, Q.disc_top2,
                                   Q.unc_margin_sensitivity, V.confidence_gated, use_rnn=True)['correct'])
    strategies['07_Q_RNN_margin'] = rc4 / len(scenarios)

    # 8. Q-RNN + raw replace (no gating)
    rc5 = sum(1 for s in scenarios
              if engine.investigate(s, budget, Q.precision_inv_sigma2, Q.disc_top2,
                                   Q.unc_gap, V.raw_replace, use_rnn=True)['correct'])
    strategies['08_Q_RNN_raw_V'] = rc5 / len(scenarios)

    # 9. Q-RNN + consistency-checked V
    rc6 = sum(1 for s in scenarios
              if engine.investigate(s, budget, Q.precision_inv_sigma2, Q.disc_top2,
                                   Q.unc_gap, V.consistency_checked, use_rnn=True)['correct'])
    strategies['09_Q_RNN_consist_V'] = rc6 / len(scenarios)

    # 10. Q-RNN + utility learning (K component)
    # Reset utility, run all scenarios, utility accumulates
    engine.past_utility = np.ones(engine.d) * 0.5
    uc = 0
    for s in scenarios:
        r = engine.investigate(s, budget, Q.precision_inv_sigma2, Q.disc_top2,
                              Q.unc_gap, V.confidence_gated, use_rnn=True,
                              use_utility=True)
        if r['correct']:
            uc += 1
        engine.update_utility(r['trace'], r['correct'])
    strategies['10_Q_CI_utility'] = uc / len(scenarios)

    return strategies


def run_per_situation(engine, scenarios, budget=2, rng=None):
    """Break down accuracy by situation type."""
    if rng is None:
        rng = np.random.default_rng(99)

    Q = QComponents
    V = VUpdates

    by_sit = defaultdict(lambda: {'sp': 0, 'random': 0, 'vld': 0, 'exh': 0, 'total': 0})

    for s in scenarios:
        sit = s['situation']
        by_sit[sit]['total'] += 1

        # Single pass
        if engine.score(s['v_surface'])[0] == s['gt_action']:
            by_sit[sit]['sp'] += 1

        # Random
        if engine.random_investigate(s, budget, V.confidence_gated, rng)['correct']:
            by_sit[sit]['random'] += 1

        # VLD (best Q variant: P2+D1+U1+RNN)
        if engine.investigate(s, budget, Q.precision_inv_sigma2, Q.disc_top2,
                             Q.unc_gap, V.confidence_gated, use_rnn=True)['correct']:
            by_sit[sit]['vld'] += 1

        # Exhaustive
        if engine.exhaustive_investigate(s, V.confidence_gated)['correct']:
            by_sit[sit]['exh'] += 1

    return dict(by_sit)


def run_budget_sweep(engine, scenarios, rng=None):
    """Accuracy vs budget for VLD, random, exhaustive."""
    if rng is None:
        rng = np.random.default_rng(99)

    Q = QComponents
    V = VUpdates
    d = engine.d

    budgets = list(range(0, d + 1))
    vld_acc = []
    random_acc = []

    for b in budgets:
        if b == 0:
            sp = sum(1 for s in scenarios if engine.score(s['v_surface'])[0] == s['gt_action'])
            vld_acc.append(sp / len(scenarios))
            random_acc.append(sp / len(scenarios))
        else:
            vc = sum(1 for s in scenarios
                     if engine.investigate(s, b, Q.precision_inv_sigma2, Q.disc_top2,
                                          Q.unc_gap, V.confidence_gated, use_rnn=True)['correct'])
            rc = sum(1 for s in scenarios
                     if engine.random_investigate(s, b, V.confidence_gated, rng)['correct'])
            vld_acc.append(vc / len(scenarios))
            random_acc.append(rc / len(scenarios))

    ec = sum(1 for s in scenarios
             if engine.exhaustive_investigate(s, V.confidence_gated)['correct'])
    exh_acc = ec / len(scenarios)

    return budgets, vld_acc, random_acc, exh_acc


def run_evoi_shift(engine, scenarios):
    """Measure EVOI state-dependence rate per situation."""
    Q = QComponents
    V = VUpdates

    shifts = defaultdict(lambda: {'shifted': 0, 'total': 0})

    for s in scenarios:
        sit = s['situation']
        v0 = s['v_surface']
        _, P0 = engine.score(v0)
        Q0 = engine.compute_Q(v0, P0, Q.precision_inv_sigma2, Q.disc_top2, Q.unc_gap)
        rank0 = np.argsort(-Q0)[:3]

        # Enrich top dim
        k0 = int(rank0[0])
        v1 = V.confidence_gated(v0, k0, s['evidence'][k0])
        _, P1 = engine.score(v1)
        Q1 = engine.compute_Q(v1, P1, Q.precision_inv_sigma2, Q.disc_top2, Q.unc_gap,
                             enriched_set={k0})
        rank1 = np.argsort(-Q1)[:3]

        shifts[sit]['total'] += 1
        if not np.array_equal(rank0[:2], rank1[:2]):
            shifts[sit]['shifted'] += 1

    return dict(shifts)


# ═══════════════════════════════════════════════════════════════
# MODULE 6: CHARTS
# ═══════════════════════════════════════════════════════════════

def chart_routing_comparison(strategies, label, output_dir):
    fig, ax = plt.subplots(figsize=(12, 5))
    names = sorted(strategies.keys())
    vals = [strategies[n] for n in names]
    short_names = [n.split('_', 1)[1] for n in names]
    colors = ['#6B7280'] * len(names)
    # Highlight VLD variants
    for i, n in enumerate(names):
        if 'Q_RNN' in n or 'Q_CI' in n:
            colors[i] = '#2563EB'
        elif 'random' in n:
            colors[i] = '#DC2626'
        elif 'exhaustive' in n:
            colors[i] = '#059669'

    bars = ax.bar(range(len(names)), vals, color=colors, edgecolor='white', width=0.7)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(short_names, fontsize=7, rotation=45, ha='right')
    ax.set_ylabel('Accuracy')
    ax.set_title('Routing Strategy Comparison — ' + label)
    ax.set_ylim(0, 1.0)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.008,
                str(round(v, 3)), ha='center', fontsize=7, fontweight='bold')
    plt.tight_layout()
    path = os.path.join(output_dir, 'val2_routing_' + label.replace(' ', '_').replace(',','') + '.png')
    plt.savefig(path, dpi=200)
    plt.close()
    print("  Chart: " + os.path.basename(path))


def chart_per_situation(by_sit, label, output_dir):
    situations = sorted(by_sit.keys())
    sp_acc = [by_sit[s]['sp']/by_sit[s]['total'] if by_sit[s]['total'] else 0 for s in situations]
    rand_acc = [by_sit[s]['random']/by_sit[s]['total'] if by_sit[s]['total'] else 0 for s in situations]
    vld_acc = [by_sit[s]['vld']/by_sit[s]['total'] if by_sit[s]['total'] else 0 for s in situations]
    exh_acc = [by_sit[s]['exh']/by_sit[s]['total'] if by_sit[s]['total'] else 0 for s in situations]
    counts = [by_sit[s]['total'] for s in situations]

    x = np.arange(len(situations))
    w = 0.2
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - 1.5*w, sp_acc, w, label='Single-pass', color='#6B7280')
    ax.bar(x - 0.5*w, rand_acc, w, label='Random B=2', color='#DC2626')
    ax.bar(x + 0.5*w, vld_acc, w, label='VLD B=2', color='#2563EB')
    ax.bar(x + 1.5*w, exh_acc, w, label='Exhaustive', color='#059669')
    ax.set_xticks(x)
    ax.set_xticklabels([s + '\n(n=' + str(c) + ')' for s, c in zip(situations, counts)], fontsize=8)
    ax.set_ylabel('Accuracy')
    ax.set_title('Per-Situation Accuracy — ' + label)
    ax.legend(fontsize=8)
    ax.set_ylim(0, 1.05)
    plt.tight_layout()
    path = os.path.join(output_dir, 'val2_per_situation_' + label.replace(' ', '_').replace(',','') + '.png')
    plt.savefig(path, dpi=200)
    plt.close()
    print("  Chart: " + os.path.basename(path))


def chart_budget_sweep(budgets, vld_acc, random_acc, exh_acc, label, output_dir):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(budgets, vld_acc, '-o', color='#2563EB', lw=2.5, ms=7, label='VLD (RNN)')
    ax.plot(budgets, random_acc, '-^', color='#DC2626', lw=2, ms=6, label='Random')
    ax.axhline(y=exh_acc, color='#059669', ls='--', lw=1.5, label='Exhaustive')
    ax.set_xlabel('Budget (reads)')
    ax.set_ylabel('Accuracy')
    ax.set_title('Budget Efficiency — ' + label)
    ax.legend()
    ax.set_ylim(0, 1.0)
    ax.fill_between(budgets, vld_acc, random_acc,
                     where=[v > r for v, r in zip(vld_acc, random_acc)],
                     alpha=0.1, color='#2563EB')
    plt.tight_layout()
    path = os.path.join(output_dir, 'val2_budget_' + label.replace(' ', '_').replace(',','') + '.png')
    plt.savefig(path, dpi=200)
    plt.close()
    print("  Chart: " + os.path.basename(path))


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("VLD Graph Reasoning — Comprehensive Experiments v2")
    print("=" * 65)

    configs = [
        {'d': 6, 'A': 4, 'label': 'd=6 A=4'},
        {'d': 6, 'A': 6, 'label': 'd=6 A=6'},
        {'d': 8, 'A': 5, 'label': 'd=8 A=5'},
    ]

    all_results = {}

    for cfg in configs:
        label = cfg['label']
        print("\n" + "=" * 65)
        print("Config: " + label)
        print("=" * 65)

        gen = ScenarioGenerator(d=cfg['d'], A=cfg['A'])
        scenarios = gen.generate(n=500)
        engine = VLDEngine(gen.mu, gen.sigma)
        rng = np.random.default_rng(99)

        # Situation distribution
        sit_counts = defaultdict(int)
        for s in scenarios:
            sit_counts[s['situation']] += 1
        print("\nSituation distribution:")
        for sit in sorted(sit_counts.keys()):
            print("  " + sit + ": " + str(sit_counts[sit]))

        # Experiment 1: Q component sweep (top 10 results)
        print("\n--- Q Component Sweep (budget=2) ---")
        q_results = run_q_component_sweep(engine, scenarios, budget=2, rng=rng)
        sorted_q = sorted(q_results.items(), key=lambda x: -x[1])
        print("  Top 10:")
        for name, acc in sorted_q[:10]:
            print("    " + name + ": " + str(round(acc, 3)))
        print("  ...")
        print("  Baselines: SP=" + str(round(q_results['single_pass'], 3)) +
              " random=" + str(round(q_results['random'], 3)) +
              " exhaustive=" + str(round(q_results['exhaustive'], 3)))

        # Experiment 2: Routing comparison
        print("\n--- Routing Strategy Comparison (budget=2) ---")
        routing = run_routing_comparison(engine, scenarios, budget=2, rng=rng)
        for name in sorted(routing.keys()):
            print("  " + name + ": " + str(round(routing[name], 3)))

        # Experiment 3: Per-situation breakdown
        print("\n--- Per-Situation Accuracy ---")
        by_sit = run_per_situation(engine, scenarios, budget=2, rng=rng)
        print("  Sit    SP     Rnd    VLD    Exh    n")
        for sit in sorted(by_sit.keys()):
            d = by_sit[sit]
            n = d['total']
            if n == 0:
                continue
            print("  " + sit + "    " +
                  str(round(d['sp']/n, 3)).ljust(7) +
                  str(round(d['random']/n, 3)).ljust(7) +
                  str(round(d['vld']/n, 3)).ljust(7) +
                  str(round(d['exh']/n, 3)).ljust(7) +
                  str(n))

        # Experiment 4: Budget sweep
        print("\n--- Budget Sweep ---")
        budgets, vld_acc, random_acc, exh_acc = run_budget_sweep(engine, scenarios, rng=rng)
        for b in budgets:
            print("  B=" + str(b) + "  VLD=" + str(round(vld_acc[b], 3)) +
                  "  Rnd=" + str(round(random_acc[b], 3)) +
                  "  Exh=" + str(round(exh_acc, 3)))

        # Experiment 5: EVOI shift rate per situation
        print("\n--- EVOI Shift Rate ---")
        shifts = run_evoi_shift(engine, scenarios)
        for sit in sorted(shifts.keys()):
            d = shifts[sit]
            rate = d['shifted'] / d['total'] if d['total'] else 0
            print("  " + sit + ": " + str(round(rate, 3)) +
                  " (" + str(d['shifted']) + "/" + str(d['total']) + ")")

        # Store results
        all_results[label] = {
            'q_top5': [(n, round(v, 4)) for n, v in sorted_q[:5]],
            'q_baselines': {
                'single_pass': round(q_results['single_pass'], 4),
                'random': round(q_results['random'], 4),
                'exhaustive': round(q_results['exhaustive'], 4),
            },
            'routing': {k: round(v, 4) for k, v in routing.items()},
            'per_situation': {sit: {k: round(v/d['total'], 4) if d['total'] else 0
                                   for k, v in d.items() if k != 'total'}
                            for sit, d in by_sit.items()},
        }

        # Charts
        print("\nGenerating charts...")
        chart_routing_comparison(routing, label, OUTPUT_DIR)
        chart_per_situation(by_sit, label, OUTPUT_DIR)
        chart_budget_sweep(budgets, vld_acc, random_acc, exh_acc, label, OUTPUT_DIR)

    # Save JSON
    results_path = os.path.join(OUTPUT_DIR, 'vld_experiments_v2_results.json')
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    print("\nResults: " + results_path)

    print("\n" + "=" * 65)
    print("DONE. " + str(len(configs)) + " configs, 5 experiments each, " +
          str(len(configs) * 3) + " charts.")
