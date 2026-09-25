"""
VLD Q·K·V Mathematical Validation — Simulation Experiments v1
================================================================
Tests the corrected Q formulation and routing properties.

EXP-Q1: Does Q rank dimensions correctly? (correlation with actual delta-P)
EXP-Q2: Does each Q component add ranking accuracy? (ablation)
EXP-Q3: Does state-dependent EVOI make sequential > parallel?
EXP-Q4: Is the Voronoi trajectory efficient? (hops vs wrong-side dimensions)
EXP-Q5: Budget efficiency curve (VLD vs random vs exhaustive)
EXP-Q6: Top-action flip rate per hop (decision changes, not just confidence)
EXP-Q7: Does 1/sigma^2 beat 1/sigma in Q? (precision exponent)

Usage: python vld_math_validation_v1.py [output_dir]
"""

import sys, os, json
import numpy as np
from collections import defaultdict

try:
    from scipy.stats import spearmanr
except ImportError:
    print("WARNING: scipy not installed. EXP-Q1 and EXP-Q4 will be skipped.")
    spearmanr = None

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.size': 11, 'axes.facecolor': '#FAFAFA',
    'figure.facecolor': '#FFFFFF', 'axes.grid': True,
    'grid.alpha': 0.3, 'axes.spines.top': False, 'axes.spines.right': False,
})

C = {'vld': '#2563EB', 'random': '#DC2626', 'exhaustive': '#059669',
     'parallel': '#F59E0B', 'q_full': '#2563EB', 'q_no_sigma': '#D97706',
     'q_no_disc': '#9333EA', 'q_no_unc': '#DC2626', 'q_simple': '#6B7280'}

OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "./pub_charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── Core VLD Math ──

class VLDSimulator:
    """Simulates VLD decisions over synthetic centroid geometry."""

    def __init__(self, d=6, A=4, n_scenarios=500, seed=42):
        self.rng = np.random.default_rng(seed)
        self.d = d       # factor dimensions
        self.A = A       # number of actions
        self.tau = 0.1   # temperature

        # Generate centroid tensor: A actions x d dimensions
        # Centroids spread across [0.2, 0.8] with separation
        self.mu = self.rng.uniform(0.15, 0.85, (A, d))
        # Ensure centroids are reasonably separated
        for i in range(A):
            for j in range(i+1, A):
                while np.linalg.norm(self.mu[i] - self.mu[j]) < 0.3:
                    self.mu[j] = self.rng.uniform(0.15, 0.85, d)

        # Per-dimension precision (sigma) - learned from outcomes
        # Lower sigma = higher precision = more informative dimension
        self.sigma = self.rng.uniform(0.05, 0.30, d)

        # Generate scenarios
        self.scenarios = []
        for _ in range(n_scenarios):
            s = self._generate_scenario()
            self.scenarios.append(s)

    def _generate_scenario(self):
        """Generate one scenario with surface factors and planted evidence."""
        # Pick ground truth action
        gt_action = self.rng.integers(0, self.A)

        # Generate surface factors NEAR a WRONG action's centroid
        wrong_action = (gt_action + 1 + self.rng.integers(0, self.A - 1)) % self.A
        v_surface = self.mu[wrong_action] + self.rng.normal(0, 0.08, self.d)
        v_surface = np.clip(v_surface, 0, 1)

        # For each dimension, generate evidence that would move v toward correct centroid
        evidence = {}
        for k in range(self.d):
            # Evidence value: near the correct centroid on this dimension
            ev_value = self.mu[gt_action, k] + self.rng.normal(0, 0.05)
            ev_value = np.clip(ev_value, 0, 1)
            shift = abs(ev_value - v_surface[k])

            # Confidence varies by dimension
            conf = self.rng.uniform(0.5, 1.0)

            evidence[k] = {
                'value': ev_value,
                'shift': shift,
                'confidence': conf,
                'informative': shift > 0.15
            }

        return {
            'v_surface': v_surface,
            'gt_action': gt_action,
            'wrong_action': wrong_action,
            'evidence': evidence,
        }

    def score(self, v):
        """Score factor vector against centroids. Returns action, margin, P distribution."""
        dists = np.array([np.sum((1/self.sigma**2) * (v - self.mu[a])**2) for a in range(self.A)])
        logits = -dists / self.tau
        logits -= np.max(logits)
        P = np.exp(logits) / np.sum(np.exp(logits))
        a_best = int(np.argmax(P))
        sorted_P = np.sort(P)[::-1]
        margin = sorted_P[0] - sorted_P[1]
        return a_best, margin, P

    def top2(self, v):
        """Return top-2 action indices."""
        dists = np.array([np.sum((1/self.sigma**2) * (v - self.mu[a])**2) for a in range(self.A)])
        order = np.argsort(dists)
        return order[0], order[1]

    def Q_full(self, v, sigma_exp=2):
        """Full Q: precision x discriminative x uncertainty. Returns per-dimension Q."""
        a1, a2 = self.top2(v)
        Q = np.zeros(self.d)
        for k in range(self.d):
            precision = 1.0 / (self.sigma[k] ** sigma_exp)
            discriminative = abs(self.mu[a1, k] - self.mu[a2, k])
            midpoint = (self.mu[a1, k] + self.mu[a2, k]) / 2
            halfwidth = discriminative / 2
            if halfwidth < 1e-8:
                uncertainty = 0.0
            else:
                uncertainty = max(0, 1 - abs(v[k] - midpoint) / halfwidth)
            Q[k] = precision * discriminative * uncertainty
        return Q

    def Q_no_sigma(self, v):
        """Q without precision term."""
        a1, a2 = self.top2(v)
        Q = np.zeros(self.d)
        for k in range(self.d):
            discriminative = abs(self.mu[a1, k] - self.mu[a2, k])
            midpoint = (self.mu[a1, k] + self.mu[a2, k]) / 2
            halfwidth = discriminative / 2
            if halfwidth < 1e-8:
                uncertainty = 0.0
            else:
                uncertainty = max(0, 1 - abs(v[k] - midpoint) / halfwidth)
            Q[k] = discriminative * uncertainty
        return Q

    def Q_no_disc(self, v):
        """Q without discriminative MULTIPLIER.
        Note: uncertainty term still uses centroid separation for halfwidth.
        This tests whether the explicit discriminative multiplier adds value
        beyond what the uncertainty term already captures from centroid geometry."""
        a1, a2 = self.top2(v)
        Q = np.zeros(self.d)
        for k in range(self.d):
            precision = 1.0 / (self.sigma[k] ** 2)
            midpoint = (self.mu[a1, k] + self.mu[a2, k]) / 2
            halfwidth = abs(self.mu[a1, k] - self.mu[a2, k]) / 2
            if halfwidth < 1e-8:
                uncertainty = 0.0
            else:
                uncertainty = max(0, 1 - abs(v[k] - midpoint) / halfwidth)
            Q[k] = precision * uncertainty
        return Q

    def Q_no_unc(self, v):
        """Q without uncertainty term (just precision x discriminative)."""
        a1, a2 = self.top2(v)
        Q = np.zeros(self.d)
        for k in range(self.d):
            precision = 1.0 / (self.sigma[k] ** 2)
            discriminative = abs(self.mu[a1, k] - self.mu[a2, k])
            Q[k] = precision * discriminative
        return Q

    def Q_simple(self, v):
        """Simple Q: just the gap |v[k] - mu[a1,k]|."""
        a1, _ = self.top2(v)
        return np.abs(v - self.mu[a1])

    def Q_random(self, v):
        """Random Q."""
        return self.rng.uniform(0, 1, self.d)

    def actual_delta_P(self, v, scenario):
        """Compute actual delta-P for each dimension if enriched."""
        _, _, P_before = self.score(v)
        gt = scenario['gt_action']
        deltas = np.zeros(self.d)
        for k in range(self.d):
            v_new = v.copy()
            v_new[k] = scenario['evidence'][k]['value']
            _, _, P_after = self.score(v_new)
            deltas[k] = P_after[gt] - P_before[gt]
        return deltas

    def enrich(self, v, k, scenario):
        """Apply evidence on dimension k with confidence gating."""
        ev = scenario['evidence'][k]
        new_val = ev['value']
        conf = ev['confidence']
        v_new = v.copy()
        v_new[k] = conf * new_val + (1 - conf) * v[k]
        return v_new

    def vld_investigate(self, scenario, budget, q_func=None, enriched_set=None):
        """Run VLD investigation with given Q function and budget."""
        if q_func is None:
            q_func = self.Q_full
        if enriched_set is None:
            enriched_set = set()

        v = scenario['v_surface'].copy()
        trace = []
        actions_per_step = []

        for step in range(budget):
            a_before, margin_before, P_before = self.score(v)
            actions_per_step.append(a_before)

            Q = q_func(v)
            # Mask already-enriched dimensions
            for ek in enriched_set:
                Q[ek] = -1

            if np.max(Q) <= 0:
                break  # no informative dimension left

            k_star = int(np.argmax(Q))
            v = self.enrich(v, k_star, scenario)
            enriched_set.add(k_star)

            a_after, margin_after, P_after = self.score(v)
            trace.append({
                'step': step,
                'dim': k_star,
                'Q_value': Q[k_star],
                'action_before': a_before,
                'action_after': a_after,
                'margin_before': margin_before,
                'margin_after': margin_after,
                'flipped': a_before != a_after,
            })

        final_action, final_margin, final_P = self.score(v)
        actions_per_step.append(final_action)

        return {
            'final_action': final_action,
            'correct': final_action == scenario['gt_action'],
            'trace': trace,
            'actions_per_step': actions_per_step,
            'v_final': v,
        }

    def random_investigate(self, scenario, budget):
        """Random dimension selection."""
        v = scenario['v_surface'].copy()
        dims = list(range(self.d))
        self.rng.shuffle(dims)
        for k in dims[:budget]:
            v = self.enrich(v, k, scenario)
        action, _, _ = self.score(v)
        return {'final_action': action, 'correct': action == scenario['gt_action']}

    def exhaustive_investigate(self, scenario):
        """Read ALL dimensions."""
        v = scenario['v_surface'].copy()
        for k in range(self.d):
            v = self.enrich(v, k, scenario)
        action, _, _ = self.score(v)
        return {'final_action': action, 'correct': action == scenario['gt_action']}

    def parallel_investigate(self, scenario, budget):
        """Pick top-B by Q_0 (initial Q, no recomputation)."""
        v = scenario['v_surface'].copy()
        Q0 = self.Q_full(v)
        top_dims = np.argsort(-Q0)[:budget]
        for k in top_dims:
            v = self.enrich(v, k, scenario)
        action, _, _ = self.score(v)
        return {'final_action': action, 'correct': action == scenario['gt_action']}


# ── Experiments ──

def exp_q1(sim):
    """EXP-Q1: Does Q rank dimensions correctly?"""
    print("=" * 65)
    print("EXP-Q1: Q ranking correlation with actual delta-P")

    correlations = []
    if spearmanr is None:
        print("  SKIPPED (scipy not installed)")
        return 0, []

    for s in sim.scenarios:
        v = s['v_surface']
        Q = sim.Q_full(v)
        dP = sim.actual_delta_P(v, s)

        if np.std(Q) > 1e-10 and np.std(dP) > 1e-10:
            r, p = spearmanr(Q, dP)
            if not np.isnan(r):
                correlations.append(r)

    mean_r = np.mean(correlations) if correlations else 0
    print("  Mean Spearman r(Q, delta-P): " + str(round(mean_r, 3)))
    print("  Scenarios with valid correlation: " + str(len(correlations)) + "/" + str(len(sim.scenarios)))
    print("  Interpretation: " + ("GOOD" if mean_r > 0.3 else "WEAK" if mean_r > 0.1 else "POOR"))
    return mean_r, correlations


def exp_q2(sim, budget=2):
    """EXP-Q2: Q component ablation."""
    print("\n" + "=" * 65)
    print("EXP-Q2: Q component ablation (budget=" + str(budget) + ")")

    q_funcs = {
        'Q_full': sim.Q_full,
        'Q_no_sigma': sim.Q_no_sigma,
        'Q_no_disc': sim.Q_no_disc,
        'Q_no_unc': sim.Q_no_unc,
        'Q_simple': sim.Q_simple,
        'Q_random': sim.Q_random,
    }

    results = {}
    for name, qf in q_funcs.items():
        correct = 0
        for s in sim.scenarios:
            r = sim.vld_investigate(s, budget, q_func=qf)
            if r['correct']:
                correct += 1
        acc = correct / len(sim.scenarios)
        results[name] = acc
        print("  " + name + ": " + str(round(acc, 3)))

    # Single-pass baseline
    sp_correct = sum(1 for s in sim.scenarios if sim.score(s['v_surface'])[0] == s['gt_action'])
    sp_acc = sp_correct / len(sim.scenarios)
    results['single_pass'] = sp_acc
    print("  single_pass: " + str(round(sp_acc, 3)))

    return results


def exp_q3(sim, budget=2):
    """EXP-Q3: Sequential (VLD) vs parallel (fixed Q0) vs random."""
    print("\n" + "=" * 65)
    print("EXP-Q3: Sequential vs parallel vs random (budget=" + str(budget) + ")")

    results = {'sequential': 0, 'parallel': 0, 'random': 0, 'exhaustive': 0}
    evoi_shifted = 0

    for s in sim.scenarios:
        # Sequential (VLD)
        r_seq = sim.vld_investigate(s, budget)
        if r_seq['correct']:
            results['sequential'] += 1

        # Parallel (Q0 only)
        r_par = sim.parallel_investigate(s, budget)
        if r_par['correct']:
            results['parallel'] += 1

        # Random
        r_rand = sim.random_investigate(s, budget)
        if r_rand['correct']:
            results['random'] += 1

        # Exhaustive
        r_exh = sim.exhaustive_investigate(s)
        if r_exh['correct']:
            results['exhaustive'] += 1

        # Check EVOI shift
        v0 = s['v_surface']
        Q0 = sim.Q_full(v0)
        rank0 = np.argsort(-Q0)

        if r_seq['trace']:
            k0 = r_seq['trace'][0]['dim']
            v1 = sim.enrich(v0.copy(), k0, s)
            Q1 = sim.Q_full(v1)
            rank1 = np.argsort(-Q1)
            # Did top-2 ranking change?
            if not np.array_equal(rank0[:2], rank1[:2]):
                evoi_shifted += 1

    n = len(sim.scenarios)
    for k in results:
        results[k] = results[k] / n

    state_dep_rate = evoi_shifted / n

    print("  Sequential (VLD):  " + str(round(results['sequential'], 3)))
    print("  Parallel (Q0):     " + str(round(results['parallel'], 3)))
    print("  Random:            " + str(round(results['random'], 3)))
    print("  Exhaustive:        " + str(round(results['exhaustive'], 3)))
    print("  EVOI shift rate:   " + str(round(state_dep_rate, 3)))
    print("  Sequential - Parallel: " + str(round(results['sequential'] - results['parallel'], 3)))

    results['state_dep_rate'] = state_dep_rate
    return results


def exp_q4(sim):
    """EXP-Q4: Voronoi trajectory — hops vs wrong-side dimensions."""
    print("\n" + "=" * 65)
    print("EXP-Q4: Hops needed vs wrong-side dimensions at v0")

    wrong_side_counts = []
    hops_needed = []

    for s in sim.scenarios:
        v = s['v_surface']
        gt = s['gt_action']

        # Count wrong-side dimensions at v0
        wrong = 0
        for k in range(sim.d):
            # Is v[k] closer to wrong centroid than correct on this dim?
            d_correct = abs(v[k] - sim.mu[gt, k])
            d_nearest = min(abs(v[k] - sim.mu[a, k]) for a in range(sim.A) if a != gt)
            if d_nearest < d_correct:
                wrong += 1
        wrong_side_counts.append(wrong)

        # How many hops until VLD gets it right?
        for b in range(1, sim.d + 1):
            r = sim.vld_investigate(s, b)
            if r['correct']:
                hops_needed.append(b)
                break
        else:
            hops_needed.append(sim.d + 1)  # never got it right

    # Correlation
    if spearmanr is None:
        print("  SKIPPED correlation (scipy not installed)")
        return wrong_side_counts, hops_needed, 0
    r, p = spearmanr(wrong_side_counts, hops_needed)
    print("  Spearman r(wrong_side, hops_needed): " + str(round(r, 3)) + " (p=" + str(round(p, 4)) + ")")
    print("  Mean wrong-side dims: " + str(round(np.mean(wrong_side_counts), 1)))
    print("  Mean hops needed: " + str(round(np.mean(hops_needed), 1)))

    return wrong_side_counts, hops_needed, r


def exp_q5(sim):
    """EXP-Q5: Budget efficiency curve."""
    print("\n" + "=" * 65)
    print("EXP-Q5: Budget efficiency curve")

    budgets = range(0, sim.d + 1)
    vld_acc = []
    random_acc = []
    parallel_acc = []

    for b in budgets:
        if b == 0:
            sp = sum(1 for s in sim.scenarios if sim.score(s['v_surface'])[0] == s['gt_action'])
            vld_acc.append(sp / len(sim.scenarios))
            random_acc.append(sp / len(sim.scenarios))
            parallel_acc.append(sp / len(sim.scenarios))
        else:
            vc = sum(1 for s in sim.scenarios if sim.vld_investigate(s, b)['correct'])
            rc = sum(1 for s in sim.scenarios if sim.random_investigate(s, b)['correct'])
            pc = sum(1 for s in sim.scenarios if sim.parallel_investigate(s, b)['correct'])
            vld_acc.append(vc / len(sim.scenarios))
            random_acc.append(rc / len(sim.scenarios))
            parallel_acc.append(pc / len(sim.scenarios))

    # Exhaustive
    ec = sum(1 for s in sim.scenarios if sim.exhaustive_investigate(s)['correct'])
    exh_acc = ec / len(sim.scenarios)

    print("  Budget  VLD      Parallel  Random   Exh")
    for b in budgets:
        print("  " + str(b) + "       " + str(round(vld_acc[b], 3)) + "    " +
              str(round(parallel_acc[b], 3)) + "     " + str(round(random_acc[b], 3)) +
              "    " + str(round(exh_acc, 3)))

    # Routing value = area between VLD and random
    routing_value = sum(vld_acc[b] - random_acc[b] for b in range(1, sim.d + 1)) / sim.d
    print("  Routing value (avg VLD - random): " + str(round(routing_value, 3)))

    return list(budgets), vld_acc, random_acc, parallel_acc, exh_acc


def exp_q6(sim, budget=3):
    """EXP-Q6: Top-action flip rate per hop."""
    print("\n" + "=" * 65)
    print("EXP-Q6: Top-action flip rate (budget=" + str(budget) + ")")

    flips_per_step = defaultdict(lambda: {'flips': 0, 'total': 0})

    for s in sim.scenarios:
        r = sim.vld_investigate(s, budget)
        for t in r['trace']:
            flips_per_step[t['step']]['total'] += 1
            if t['flipped']:
                flips_per_step[t['step']]['flips'] += 1

    print("  Step  Flips  Total  Rate")
    for step in sorted(flips_per_step.keys()):
        d = flips_per_step[step]
        rate = d['flips'] / d['total'] if d['total'] else 0
        print("  " + str(step) + "     " + str(d['flips']) + "      " +
              str(d['total']) + "    " + str(round(rate, 3)))

    return flips_per_step


def exp_q7(sim, budget=2):
    """EXP-Q7: 1/sigma^2 vs 1/sigma in Q."""
    print("\n" + "=" * 65)
    print("EXP-Q7: Precision exponent (1/sigma^n, n=1 vs n=2)")

    def q_sigma1(v):
        return sim.Q_full(v, sigma_exp=1)

    def q_sigma2(v):
        return sim.Q_full(v, sigma_exp=2)

    correct_1 = sum(1 for s in sim.scenarios
                    if sim.vld_investigate(s, budget, q_func=q_sigma1)['correct'])
    correct_2 = sum(1 for s in sim.scenarios
                    if sim.vld_investigate(s, budget, q_func=q_sigma2)['correct'])

    acc_1 = correct_1 / len(sim.scenarios)
    acc_2 = correct_2 / len(sim.scenarios)

    print("  1/sigma^1: " + str(round(acc_1, 3)))
    print("  1/sigma^2: " + str(round(acc_2, 3)))
    print("  Difference: " + str(round(acc_2 - acc_1, 3)))

    return acc_1, acc_2


# ── Charts ──

def generate_charts(q2_results, q3_results, q5_data, output_dir, suffix="", config_label=""):
    """Generate validation charts."""
    label_suffix = " (" + config_label + ")" if config_label else ""

    # Chart 1: Q ablation (EXP-Q2)
    fig, ax = plt.subplots(figsize=(10, 5))
    names = list(q2_results.keys())
    vals = [q2_results[n] for n in names]
    colors = [C.get(n.lower(), '#6B7280') for n in names]
    bars = ax.bar(range(len(names)), vals, color=colors, edgecolor='white', width=0.6)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([n.replace('_', '\n') for n in names], fontsize=8)
    ax.set_ylabel('Accuracy')
    ax.set_title('Q Component Ablation' + label_suffix)
    ax.set_ylim(0, 1.0)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.01,
                str(round(v, 3)), ha='center', fontsize=9, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'val_q2_ablation' + suffix + '.png'), dpi=200)
    plt.close()
    print("  Chart: val_q2_ablation" + suffix + ".png")

    # Chart 2: Sequential vs parallel vs random (EXP-Q3)
    fig, ax = plt.subplots(figsize=(8, 5))
    labels = ['Sequential\n(VLD)', 'Parallel\n(Q0 fixed)', 'Random', 'Exhaustive']
    vals = [q3_results[k] for k in ['sequential', 'parallel', 'random', 'exhaustive']]
    cols = [C['vld'], C['parallel'], C['random'], C['exhaustive']]
    bars = ax.bar(labels, vals, color=cols, edgecolor='white', width=0.6)
    ax.set_ylabel('Accuracy')
    ax.set_title('Sequential routing vs alternatives' + label_suffix)
    ax.set_ylim(0, 1.0)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.01,
                str(round(v, 3)), ha='center', fontsize=9, fontweight='bold')
    ax.text(0.98, 0.02, 'EVOI shift rate: ' + str(round(q3_results['state_dep_rate'], 2)),
            transform=ax.transAxes, ha='right', fontsize=9, style='italic')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'val_q3_sequential_vs_parallel' + suffix + '.png'), dpi=200)
    plt.close()
    print("  Chart: val_q3_sequential_vs_parallel" + suffix + ".png")

    # Chart 3: Budget efficiency curve (EXP-Q5)
    budgets, vld_acc, random_acc, parallel_acc, exh_acc = q5_data
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(budgets, vld_acc, '-o', color=C['vld'], lw=2.5, ms=7, label='VLD (sequential Q)')
    ax.plot(budgets, parallel_acc, '-s', color=C['parallel'], lw=2, ms=6, label='Parallel (Q0 fixed)')
    ax.plot(budgets, random_acc, '-^', color=C['random'], lw=2, ms=6, label='Random')
    ax.axhline(y=exh_acc, color=C['exhaustive'], ls='--', lw=1.5, label='Exhaustive (all dims)')
    ax.set_xlabel('Budget (reads)')
    ax.set_ylabel('Accuracy')
    ax.set_title('Budget efficiency' + label_suffix)
    ax.legend()
    ax.set_ylim(0, 1.0)

    # Shade routing value
    ax.fill_between(budgets, vld_acc, random_acc,
                     where=[v > r for v, r in zip(vld_acc, random_acc)],
                     alpha=0.1, color=C['vld'], label='_routing value')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'val_q5_budget_efficiency' + suffix + '.png'), dpi=200)
    plt.close()
    print("  Chart: val_q5_budget_efficiency" + suffix + ".png")


# ── Main ──

if __name__ == '__main__':
    print("VLD Q.K.V Mathematical Validation")
    print("=" * 65)

    # Run at multiple complexity levels
    configs = [
        {'d': 6, 'A': 4, 'label': 'SOC-like (d=6, A=4)'},
        {'d': 6, 'A': 6, 'label': 'Purchasing-like (d=6, A=6)'},
        {'d': 8, 'A': 5, 'label': 'Complex (d=8, A=5)'},
    ]

    all_results = {}

    for cfg in configs:
        print("\n" + "=" * 65)
        print("Config: " + cfg['label'])
        print("=" * 65)

        sim = VLDSimulator(d=cfg['d'], A=cfg['A'], n_scenarios=500)

        q1_r, q1_corrs = exp_q1(sim)
        q2_results = exp_q2(sim, budget=2)
        q3_results = exp_q3(sim, budget=2)
        q4_wrong, q4_hops, q4_r = exp_q4(sim)
        q5_data = exp_q5(sim)
        q6_flips = exp_q6(sim, budget=3)
        q7_acc1, q7_acc2 = exp_q7(sim, budget=2)

        cfg_key = cfg['label']
        all_results[cfg_key] = {
            'q1_mean_r': round(q1_r, 4),
            'q2': {n: round(v, 4) for n, v in q2_results.items()},
            'q3_sequential': round(q3_results['sequential'], 4),
            'q3_parallel': round(q3_results['parallel'], 4),
            'q3_random': round(q3_results['random'], 4),
            'q3_exhaustive': round(q3_results['exhaustive'], 4),
            'q3_state_dep_rate': round(q3_results['state_dep_rate'], 4),
            'q4_voronoi_r': round(q4_r, 4),
            'q5_vld_at_2': round(q5_data[1][2], 4),
            'q5_random_at_2': round(q5_data[2][2], 4),
            'q7_sigma1': round(q7_acc1, 4),
            'q7_sigma2': round(q7_acc2, 4),
        }

        suffix = "_d" + str(cfg['d']) + "_A" + str(cfg['A'])
        print("\nGenerating charts for " + cfg['label'] + "...")
        generate_charts(q2_results, q3_results, q5_data, OUTPUT_DIR, suffix, cfg['label'])

    # Save JSON
    results_path = os.path.join(OUTPUT_DIR, 'vld_math_validation_results.json')
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    print("\nResults: " + results_path)

    # Summary
    print("\n" + "=" * 65)
    print("SUMMARY (all configs)")
    print("=" * 65)
    for cfg_key, res in all_results.items():
        print("\n  " + cfg_key + ":")
        print("    Q1 ranking r:      " + str(res['q1_mean_r']))
        print("    Q2 full/random:    " + str(res['q2']['Q_full']) + " / " + str(res['q2']['Q_random']))
        print("    Q3 seq/par/rand:   " + str(res['q3_sequential']) + " / " +
              str(res['q3_parallel']) + " / " + str(res['q3_random']))
        print("    Q3 EVOI shift:     " + str(res['q3_state_dep_rate']))
        print("    Q4 Voronoi r:      " + str(res['q4_voronoi_r']))
        print("    Q5 VLD@2/rnd@2:    " + str(res['q5_vld_at_2']) + " / " + str(res['q5_random_at_2']))
        print("    Q7 1/s vs 1/s^2:   " + str(res['q7_sigma1']) + " / " + str(res['q7_sigma2']))
    print("\nDone.")
