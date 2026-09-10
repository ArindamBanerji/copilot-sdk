"""
VLD Validation Simulations v3
==============================
Fixes from v2:
- Budget=2 aggregation: added re-extraction alternative (ε=1)
- Multi-branch: 6 branches (matches SOC's 6 categories)
- Abstain arm: conservation-bounded deferral
- Content-rule + majority comparators (not just random)
- Content-keyed vs score-keyed split
- Experiment names align to implementation design (E-ρ, E-ρsk, E-budget)

Run: python vld_validation_sims_v3.py
Output: console report + PNG plots
"""

import numpy as np
import os
from dataclasses import dataclass, field
from typing import Optional

# ──────────────────────────────────────────────────────────────
# World model: conditional investigation with N branches
# ──────────────────────────────────────────────────────────────

@dataclass
class Decision:
    """A synthetic decision with conditional branching across N categories."""
    true_category: int           # 0..N-1 (ground truth category)
    true_action: int             # 0 or 1 (ground truth action within category)
    surface_features: np.ndarray # initial observation (noisy)
    branch_evidence: list        # list of N evidence vectors (one per branch)
    correct_branch: int          # which branch resolves the case
    has_label: bool              # True = content-keyed, False = score-keyed
    distractor_pull: float       # how much wrong-branch evidence misleads


def generate_world(n_cases: int, n_dims: int, n_branches: int,
                   rho_target: float, distractor_strength: float = 0.4,
                   content_keyed_fraction: float = 0.5,
                   rng: np.random.Generator = None) -> list[Decision]:
    """
    Generate synthetic decisions with N conditional branches.

    n_branches: number of investigation branches (6 for SOC categories)
    rho_target: controls score informativeness for routing
    content_keyed_fraction: fraction of cases with explicit category labels
    distractor_strength: how much wrong-branch evidence misleads
    """
    if rng is None:
        rng = np.random.default_rng(42)

    decisions = []
    for _ in range(n_cases):
        true_cat = rng.integers(0, n_branches)
        true_action = rng.integers(0, 2)
        correct_branch = true_cat

        # Surface features: noisy, weak class signal
        surface = rng.normal(0, 0.5, n_dims)
        class_noise = rng.normal(0, 0.6)
        surface[0] = (2 * true_action - 1) * 0.2 + class_noise

        # Routing signal: dim 1 carries category information
        # Strength controlled by rho_target
        signal_strength = (rho_target - 1.0 / n_branches) * 4.0
        signal_strength = max(signal_strength, 0)
        # Encode category in dim 1 as a noisy scalar
        routing_noise = rng.normal(0, 1.0)
        surface[1] = (true_cat / (n_branches - 1) - 0.5) * 2 * signal_strength + routing_noise

        # Build evidence for each branch
        branch_evidence = []
        for b in range(n_branches):
            ev = rng.normal(0, 0.2, n_dims)
            if b == correct_branch:
                # Correct branch: reveals true action clearly
                ev[0] = (2 * true_action - 1) * 2.0
            else:
                # Wrong branch: actively misleads
                ev[0] = -(2 * true_action - 1) * distractor_strength * 2.0
            branch_evidence.append(ev)

        # Content-keyed: alert has an explicit category label
        has_label = rng.random() < content_keyed_fraction

        decisions.append(Decision(
            true_category=true_cat,
            true_action=true_action,
            surface_features=surface,
            branch_evidence=branch_evidence,
            correct_branch=correct_branch,
            has_label=has_label,
            distractor_pull=distractor_strength
        ))
    return decisions


# ──────────────────────────────────────────────────────────────
# Scorer: centroid-distance classifier with category clusters
# ──────────────────────────────────────────────────────────────

class CentroidScorer:
    """Nearest-centroid classifier with per-category centroid clusters."""

    def __init__(self, n_dims: int, n_categories: int):
        self.n_categories = n_categories
        # Two centroids per category: action 0 and action 1
        # Spread categories across dim 1, actions across dim 0
        self.centroids = np.zeros((n_categories, 2, n_dims))
        for c in range(n_categories):
            cat_offset = (c / (n_categories - 1) - 0.5) * 2 if n_categories > 1 else 0
            self.centroids[c, 0, 0] = -1.0  # action 0
            self.centroids[c, 1, 0] = 1.0   # action 1
            self.centroids[c, :, 1] = cat_offset  # category position

    def score(self, v: np.ndarray) -> tuple[int, int, float]:
        """Return (category, action, margin)."""
        best_cat, best_act, best_dist = 0, 0, float('inf')
        second_dist = float('inf')
        for c in range(self.n_categories):
            for a in range(2):
                d = np.linalg.norm(v - self.centroids[c, a])
                if d < best_dist:
                    second_dist = best_dist
                    best_dist = d
                    best_cat, best_act = c, a
                elif d < second_dist:
                    second_dist = d
        margin = second_dist - best_dist
        return best_cat, best_act, margin

    def category_distances(self, v: np.ndarray) -> list[float]:
        """Min distance to each category's centroid cluster."""
        dists = []
        for c in range(self.n_categories):
            min_d = min(np.linalg.norm(v - self.centroids[c, a]) for a in range(2))
            dists.append(min_d)
        return dists

    def route_category(self, v: np.ndarray) -> int:
        """Score-keyed routing: nearest category by centroid distance."""
        dists = self.category_distances(v)
        return int(np.argmin(dists))


# ──────────────────────────────────────────────────────────────
# Investigation policies
# ──────────────────────────────────────────────────────────────

def single_pass(d: Decision, scorer: CentroidScorer) -> int:
    """No investigation. Score from surface only."""
    _, action, _ = scorer.score(d.surface_features)
    return action


def vld_investigate(d: Decision, scorer: CentroidScorer,
                    budget: int = 1, eps: float = 0.3,
                    reextract: bool = False) -> int:
    """
    VLD: score-conditioned routing through branches.
    reextract=True: re-extract from full evidence set (no damping)
    reextract=False: damped average (original method)
    """
    v = d.surface_features.copy()
    investigated = set()
    all_evidence = {}

    for step in range(budget):
        # Route to nearest non-investigated category
        dists = scorer.category_distances(v)
        sorted_cats = np.argsort(dists)
        chosen = None
        for c in sorted_cats:
            if c not in investigated:
                chosen = int(c)
                break
        if chosen is None:
            break

        investigated.add(chosen)
        evidence = d.branch_evidence[chosen]
        all_evidence[chosen] = evidence

        if reextract:
            # Re-extraction: combine surface + all evidence equally
            combined = d.surface_features.copy()
            for ev in all_evidence.values():
                combined = combined + ev
            v = combined / (1 + len(all_evidence))
        else:
            # Damped average
            v = (1 - eps) * v + eps * evidence

    _, action, _ = scorer.score(v)
    return action


def content_rule(d: Decision, scorer: CentroidScorer,
                 budget: int = 1, eps: float = 0.3) -> int:
    """Content-keyed routing: use the label to pick the correct branch."""
    if not d.has_label:
        # No label available — fall back to single-pass
        return single_pass(d, scorer)

    v = d.surface_features.copy()
    # Content-keyed: go straight to the correct category's branch
    evidence = d.branch_evidence[d.true_category]
    v = (1 - eps) * v + eps * evidence
    _, action, _ = scorer.score(v)
    return action


def majority_branch(d: Decision, scorer: CentroidScorer,
                    majority_cat: int, budget: int = 1, eps: float = 0.3) -> int:
    """Always investigate the most common category."""
    v = d.surface_features.copy()
    evidence = d.branch_evidence[majority_cat]
    v = (1 - eps) * v + eps * evidence
    _, action, _ = scorer.score(v)
    return action


def breadth_investigate(d: Decision, scorer: CentroidScorer,
                        budget: int = 1, eps: float = 0.3) -> int:
    """Read branches in fixed order (0, 1, 2, ...)."""
    v = d.surface_features.copy()
    for b in range(min(budget, len(d.branch_evidence))):
        v = (1 - eps) * v + eps * d.branch_evidence[b]
    _, action, _ = scorer.score(v)
    return action


def random_investigate(d: Decision, scorer: CentroidScorer,
                       budget: int = 1, eps: float = 0.3,
                       rng: np.random.Generator = None) -> int:
    """Random branch selection (placebo)."""
    if rng is None:
        rng = np.random.default_rng()
    v = d.surface_features.copy()
    branches = rng.choice(len(d.branch_evidence), size=min(budget, len(d.branch_evidence)), replace=False)
    for b in branches:
        v = (1 - eps) * v + eps * d.branch_evidence[b]
    _, action, _ = scorer.score(v)
    return action


def abstain_policy(d: Decision, scorer: CentroidScorer,
                   margin_threshold: float = 0.3,
                   budget: int = 1, eps: float = 0.3) -> Optional[int]:
    """
    VLD with abstention: if margin < threshold after investigation,
    return None (abstain) instead of committing to an action.
    """
    v = d.surface_features.copy()
    investigated = set()

    for step in range(budget):
        dists = scorer.category_distances(v)
        sorted_cats = np.argsort(dists)
        chosen = None
        for c in sorted_cats:
            if c not in investigated:
                chosen = int(c)
                break
        if chosen is None:
            break
        investigated.add(chosen)
        v = (1 - eps) * v + eps * d.branch_evidence[chosen]

    _, action, margin = scorer.score(v)
    if margin < margin_threshold:
        return None  # abstain
    return action


# ──────────────────────────────────────────────────────────────
# E-ρ: Scorer Routing Accuracy
# ──────────────────────────────────────────────────────────────

def run_e_rho(n_cases=3000, n_dims=8, n_branches=6, distractor=0.4):
    """
    E-ρ: Sweep ρ, measure VLD routing accuracy vs comparators.
    Now includes content-rule and majority baselines.
    """
    print("=" * 65)
    print(f"E-ρ: SCORER ROUTING ACCURACY ({n_branches} branches)")
    print("=" * 65)

    rho_values = np.arange(0.15, 1.01, 0.05)
    scorer = CentroidScorer(n_dims, n_branches)
    rng = np.random.default_rng(42)

    results = {'rho': [], 'vld': [], 'content': [], 'majority': [],
               'random': [], 'single': [], 'delta_vs_majority': []}

    for rho in rho_values:
        world = generate_world(n_cases, n_dims, n_branches, rho, distractor,
                               content_keyed_fraction=0.5, rng=rng)
        majority_cat = max(range(n_branches),
                           key=lambda c: sum(1 for d in world if d.true_category == c))

        vld_ok = sum(1 for d in world
                     if vld_investigate(d, scorer, budget=1) == d.true_action) / n_cases
        content_ok = sum(1 for d in world
                         if content_rule(d, scorer, budget=1) == d.true_action) / n_cases
        majority_ok = sum(1 for d in world
                          if majority_branch(d, scorer, majority_cat, budget=1) == d.true_action) / n_cases
        random_ok = sum(1 for d in world
                        if random_investigate(d, scorer, budget=1, rng=rng) == d.true_action) / n_cases
        single_ok = sum(1 for d in world
                        if single_pass(d, scorer) == d.true_action) / n_cases

        results['rho'].append(rho)
        results['vld'].append(vld_ok)
        results['content'].append(content_ok)
        results['majority'].append(majority_ok)
        results['random'].append(random_ok)
        results['single'].append(single_ok)
        results['delta_vs_majority'].append(vld_ok - majority_ok)

        print(f"  ρ={rho:.2f}  VLD={vld_ok:.3f}  content={content_ok:.3f}  "
              f"majority={majority_ok:.3f}  random={random_ok:.3f}  "
              f"Δ_maj={vld_ok - majority_ok:+.3f}")

    chance = 1.0 / n_branches
    mid_idx = np.argmin(np.abs(np.array(results['rho']) - chance))
    delta_at_chance = results['delta_vs_majority'][mid_idx]

    high_deltas = [d for r, d in zip(results['rho'], results['delta_vs_majority']) if r > 0.4]
    corr = np.corrcoef(np.array(results['rho']) - chance,
                       np.array(results['delta_vs_majority']))[0, 1]

    print(f"\n--- VALIDATION ---")
    print(f"  Chance = 1/{n_branches} = {chance:.3f}")
    print(f"  Δ at ρ≈chance: {delta_at_chance:+.4f} (should be ≈ 0)")
    print(f"  Mean Δ for ρ > 0.4: {np.mean(high_deltas):+.4f} (should be > 0)")
    print(f"  Correlation(Δ, ρ−chance): {corr:.3f} (should be > 0.8)")
    print(f"  VLD beats content-rule at any ρ? {any(v > c for v, c in zip(results['vld'], results['content']))}")

    verdict = "PASS" if corr > 0.7 and np.mean(high_deltas) > 0 else "NEEDS INVESTIGATION"
    print(f"  VERDICT: {verdict}")
    return results


# ──────────────────────────────────────────────────────────────
# E-ρsk: Score-Keyed Only
# ──────────────────────────────────────────────────────────────

def run_e_rho_scorekey(n_cases=3000, n_dims=8, n_branches=6,
                       rho=0.6, distractor=0.4):
    """
    E-ρsk: Measure routing accuracy on score-keyed cases ONLY
    (alerts without category labels).
    """
    print(f"\n{'=' * 65}")
    print(f"E-ρsk: SCORE-KEYED ROUTING (ρ={rho}, {n_branches} branches)")
    print(f"{'=' * 65}")

    scorer = CentroidScorer(n_dims, n_branches)
    rng = np.random.default_rng(42)
    # All cases are score-keyed (no labels)
    world = generate_world(n_cases, n_dims, n_branches, rho, distractor,
                           content_keyed_fraction=0.0, rng=rng)

    majority_cat = max(range(n_branches),
                       key=lambda c: sum(1 for d in world if d.true_category == c))

    # Measure routing accuracy (does VLD pick the correct category?)
    vld_route_correct = sum(1 for d in world
                            if scorer.route_category(d.surface_features) == d.true_category) / n_cases
    majority_route = sum(1 for d in world if d.true_category == majority_cat) / n_cases
    random_route = 1.0 / n_branches

    # Measure action accuracy
    vld_act = sum(1 for d in world
                  if vld_investigate(d, scorer, budget=1) == d.true_action) / n_cases
    majority_act = sum(1 for d in world
                       if majority_branch(d, scorer, majority_cat, budget=1) == d.true_action) / n_cases
    random_act = sum(1 for d in world
                     if random_investigate(d, scorer, budget=1, rng=rng) == d.true_action) / n_cases

    # Margin distribution
    margins = []
    for d in world:
        _, _, margin = scorer.score(d.surface_features)
        margins.append(margin)
    margins = np.array(margins)
    p25 = np.percentile(margins, 25)

    # ρ by difficulty
    hard_tail = [d for d, m in zip(world, margins) if m < p25]
    easy = [d for d, m in zip(world, margins) if m >= p25]
    rho_hard = sum(1 for d in hard_tail
                   if scorer.route_category(d.surface_features) == d.true_category) / max(len(hard_tail), 1)
    rho_easy = sum(1 for d in easy
                   if scorer.route_category(d.surface_features) == d.true_category) / max(len(easy), 1)

    print(f"  ROUTING ACCURACY:")
    print(f"    VLD (centroid distance): {vld_route_correct:.3f}")
    print(f"    Majority branch:         {majority_route:.3f}")
    print(f"    Random:                  {random_route:.3f}")
    print(f"    VLD beats majority?      {'YES' if vld_route_correct > majority_route else 'NO'}")
    print(f"\n  ACTION ACCURACY (budget=1):")
    print(f"    VLD:      {vld_act:.3f}")
    print(f"    Majority: {majority_act:.3f}")
    print(f"    Random:   {random_act:.3f}")
    print(f"\n  MARGIN DISTRIBUTION:")
    print(f"    P10={np.percentile(margins, 10):.3f}  P25={p25:.3f}  "
          f"P50={np.percentile(margins, 50):.3f}  P75={np.percentile(margins, 75):.3f}  "
          f"P90={np.percentile(margins, 90):.3f}")
    print(f"\n  ρ BY DIFFICULTY:")
    print(f"    Hard-tail (margin < P25): {rho_hard:.3f} (n={len(hard_tail)})")
    print(f"    Easy (margin >= P25):     {rho_easy:.3f} (n={len(easy)})")

    verdict = "PASS" if vld_route_correct > majority_route else "NEEDS INVESTIGATION"
    print(f"\n  VERDICT: {verdict}")
    return {
        'rho_vld': vld_route_correct, 'rho_majority': majority_route,
        'rho_random': random_route, 'rho_hard': rho_hard, 'rho_easy': rho_easy,
        'margins': margins
    }


# ──────────────────────────────────────────────────────────────
# E-budget: Budget Sweep with Aggregation Comparison
# ──────────────────────────────────────────────────────────────

def run_e_budget(n_cases=3000, n_dims=8, n_branches=6,
                 rho=0.6, distractor=0.4):
    """
    E-budget: Sweep budget with both damped and re-extraction aggregation.
    Tests whether the budget=2 reversal is fixed by re-extraction.
    """
    print(f"\n{'=' * 65}")
    print(f"E-budget: BUDGET SWEEP (ρ={rho}, {n_branches} branches)")
    print(f"{'=' * 65}")

    scorer = CentroidScorer(n_dims, n_branches)
    rng = np.random.default_rng(42)
    world = generate_world(n_cases, n_dims, n_branches, rho, distractor,
                           content_keyed_fraction=0.0, rng=rng)
    majority_cat = max(range(n_branches),
                       key=lambda c: sum(1 for d in world if d.true_category == c))

    print(f"  {'Budget':<8} {'VLD-damp':<10} {'VLD-reext':<10} {'Breadth':<10} "
          f"{'Majority':<10} {'Random':<10} {'Single':<10}")

    for budget in range(n_branches + 1):
        vld_d = sum(1 for d in world
                    if vld_investigate(d, scorer, budget=max(budget,1), eps=0.3, reextract=False) == d.true_action) / n_cases
        vld_r = sum(1 for d in world
                    if vld_investigate(d, scorer, budget=max(budget,1), eps=0.3, reextract=True) == d.true_action) / n_cases
        br = sum(1 for d in world
                 if breadth_investigate(d, scorer, budget=max(budget,1)) == d.true_action) / n_cases
        maj = sum(1 for d in world
                  if majority_branch(d, scorer, majority_cat, budget=max(budget,1)) == d.true_action) / n_cases
        rand = sum(1 for d in world
                   if random_investigate(d, scorer, budget=max(budget,1), rng=rng) == d.true_action) / n_cases
        sing = sum(1 for d in world
                   if single_pass(d, scorer) == d.true_action) / n_cases

        print(f"  {budget:<8} {vld_d:<10.3f} {vld_r:<10.3f} {br:<10.3f} "
              f"{maj:<10.3f} {rand:<10.3f} {sing:<10.3f}")

    print(f"\n  VLD-damp = damped average (ε=0.3)")
    print(f"  VLD-reext = re-extraction from full admitted set")
    print(f"  If VLD-reext fixes budget>1 reversal → re-extraction is the correct aggregation")


# ──────────────────────────────────────────────────────────────
# E-abstain: Abstention Value
# ──────────────────────────────────────────────────────────────

def run_e_abstain(n_cases=3000, n_dims=8, n_branches=6,
                  rho=0.6, distractor=0.4):
    """
    E-abstain: Does abstaining on low-margin cases improve net utility?
    """
    print(f"\n{'=' * 65}")
    print(f"E-abstain: ABSTENTION VALUE (ρ={rho})")
    print(f"{'=' * 65}")

    scorer = CentroidScorer(n_dims, n_branches)
    rng = np.random.default_rng(42)
    world = generate_world(n_cases, n_dims, n_branches, rho, distractor,
                           content_keyed_fraction=0.0, rng=rng)

    # Sweep abstain threshold
    for threshold in [0.0, 0.1, 0.2, 0.3, 0.5, 0.8]:
        results = [abstain_policy(d, scorer, margin_threshold=threshold, budget=1)
                   for d in world]
        committed = [(r, d) for r, d in zip(results, world) if r is not None]
        abstained = [(r, d) for r, d in zip(results, world) if r is None]

        if committed:
            accuracy = sum(1 for r, d in committed if r == d.true_action) / len(committed)
        else:
            accuracy = 0.0
        abstain_rate = len(abstained) / n_cases

        # Net utility: correct=+1, incorrect=-penalty, abstain=-abstain_cost
        penalty = 5.0
        abstain_cost = 0.5
        utility = sum(1.0 if r == d.true_action else -penalty
                      for r, d in committed)
        utility += sum(-abstain_cost for _ in abstained)
        utility /= n_cases

        print(f"  threshold={threshold:.1f}  committed={len(committed):>5}  "
              f"abstained={len(abstained):>5} ({abstain_rate:.1%})  "
              f"accuracy={accuracy:.3f}  utility={utility:+.3f}")

    print(f"\n  Utility = correct(+1) + incorrect(-5) + abstain(-0.5)")
    print(f"  Optimal threshold balances accuracy gain vs abstain cost")


# ──────────────────────────────────────────────────────────────
# Plotting
# ──────────────────────────────────────────────────────────────

def plot_results(e_rho_results, output_dir="."):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [matplotlib not available — skipping plots]")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(e_rho_results['rho'], e_rho_results['vld'],
             'b-o', label='VLD (score-routed)', linewidth=2, markersize=4)
    ax1.plot(e_rho_results['rho'], e_rho_results['content'],
             'g-s', label='Content-rule', linewidth=2, markersize=4)
    ax1.plot(e_rho_results['rho'], e_rho_results['majority'],
             'm-^', label='Majority-branch', linewidth=1.5, markersize=4)
    ax1.plot(e_rho_results['rho'], e_rho_results['random'],
             'r--', label='Random', linewidth=1, alpha=0.6)
    ax1.plot(e_rho_results['rho'], e_rho_results['single'],
             'k:', label='Single-pass', linewidth=1, alpha=0.4)
    ax1.set_xlabel('ρ (score informativeness)')
    ax1.set_ylabel('Action Accuracy')
    ax1.set_title('E-ρ: Routing Accuracy (6 branches, budget=1)')
    ax1.legend(fontsize=7)
    ax1.grid(True, alpha=0.3)

    ax2.plot(e_rho_results['rho'], e_rho_results['delta_vs_majority'],
             'b-o', label='Δ VLD vs Majority', linewidth=2, markersize=4)
    ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
    ax2.set_xlabel('ρ (score informativeness)')
    ax2.set_ylabel('Δ accuracy (VLD − Majority)')
    ax2.set_title('E-ρ: VLD Advantage vs Majority Baseline')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(output_dir, 'vld_sim3_e_rho.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"\n  Plot saved: {path}")


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    e_rho = run_e_rho(n_cases=3000, n_branches=6, distractor=0.4)
    e_rhosk = run_e_rho_scorekey(n_cases=3000, n_branches=6, rho=0.6, distractor=0.4)
    run_e_budget(n_cases=3000, n_branches=6, rho=0.6, distractor=0.4)
    run_e_abstain(n_cases=3000, n_branches=6, rho=0.6, distractor=0.4)

    output_dir = os.path.dirname(os.path.abspath(__file__))
    plot_results(e_rho, output_dir)

    print(f"\n{'=' * 65}")
    print("SUMMARY")
    print(f"{'=' * 65}")
    print("E-ρ:      Does VLD routing beat majority/random? (calibration)")
    print("E-ρsk:    Does routing work without labels? (VLD's addressable market)")
    print("E-budget: Where does VLD earn its value? (budget constraint)")
    print("E-abstain: Does 'do less' improve net utility? (abstain value)")
    print()
    print("If E-ρ PASS + E-ρsk PASS: mechanism works, proceed to Phase 1b")
    print("If E-budget shows re-extraction fixes reversal: use re-extraction")
    print("If E-abstain shows optimal threshold > 0: abstain has value")
