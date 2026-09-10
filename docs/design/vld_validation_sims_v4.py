"""
VLD Validation Simulations v4
==============================
Fixes from v3:
- Three evidence regimes: NEUTRAL (noise), MISLEADING (active pull),
  MIXED (realistic: some neutral, some misleading)
- Distractor sweep: 0.0 → 0.6 to find the crossover
- Selective VLD: only investigate when margin < threshold (VLD + abstain combined)
- Larger n_cases (5000) for statistical power
- 95% confidence intervals via bootstrap
- Comprehensive budget × distractor × ρ interaction

Run: python vld_validation_sims_v4.py
Expected runtime: ~5-10 minutes
"""

import numpy as np
import os
from dataclasses import dataclass
from typing import Optional

# ──────────────────────────────────────────────────────────────
# World model
# ──────────────────────────────────────────────────────────────

@dataclass
class Decision:
    true_category: int
    true_action: int
    surface_features: np.ndarray
    branch_evidence: list
    correct_branch: int
    has_label: bool
    distractor_pull: float


def generate_world(n_cases, n_dims, n_branches, rho_target,
                   distractor_strength=0.4, neutral_fraction=0.5,
                   content_keyed_fraction=0.5, rng=None):
    """
    neutral_fraction: fraction of wrong branches that are NEUTRAL (noise only)
    vs MISLEADING (active pull toward wrong class).
    At neutral_fraction=1.0: all wrong branches are noise (no distraction).
    At neutral_fraction=0.0: all wrong branches actively mislead.
    At neutral_fraction=0.5: half noise, half misleading (realistic mix).
    """
    if rng is None:
        rng = np.random.default_rng(42)

    decisions = []
    for _ in range(n_cases):
        true_cat = rng.integers(0, n_branches)
        true_action = rng.integers(0, 2)
        correct_branch = true_cat

        surface = rng.normal(0, 0.5, n_dims)
        class_noise = rng.normal(0, 0.6)
        surface[0] = (2 * true_action - 1) * 0.2 + class_noise

        signal_strength = max((rho_target - 1.0 / n_branches) * 4.0, 0)
        routing_noise = rng.normal(0, 1.0)
        surface[1] = ((true_cat / max(n_branches - 1, 1)) - 0.5) * 2 * signal_strength + routing_noise

        branch_evidence = []
        for b in range(n_branches):
            ev = rng.normal(0, 0.2, n_dims)
            if b == correct_branch:
                ev[0] = (2 * true_action - 1) * 2.0
            else:
                is_neutral = rng.random() < neutral_fraction
                if is_neutral:
                    ev[0] = rng.normal(0, 0.3)  # noise only, no directional pull
                else:
                    ev[0] = -(2 * true_action - 1) * distractor_strength * 2.0  # active mislead
            branch_evidence.append(ev)

        has_label = rng.random() < content_keyed_fraction

        decisions.append(Decision(
            true_category=true_cat, true_action=true_action,
            surface_features=surface, branch_evidence=branch_evidence,
            correct_branch=correct_branch, has_label=has_label,
            distractor_pull=distractor_strength
        ))
    return decisions


# ──────────────────────────────────────────────────────────────
# Scorer
# ──────────────────────────────────────────────────────────────

class CentroidScorer:
    def __init__(self, n_dims, n_categories):
        self.n_categories = n_categories
        self.centroids = np.zeros((n_categories, 2, n_dims))
        for c in range(n_categories):
            cat_offset = (c / max(n_categories - 1, 1) - 0.5) * 2
            self.centroids[c, 0, 0] = -1.0
            self.centroids[c, 1, 0] = 1.0
            self.centroids[c, :, 1] = cat_offset

    def score(self, v):
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
        return best_cat, best_act, second_dist - best_dist

    def category_distances(self, v):
        return [min(np.linalg.norm(v - self.centroids[c, a]) for a in range(2))
                for c in range(self.n_categories)]

    def route_category(self, v):
        return int(np.argmin(self.category_distances(v)))


# ──────────────────────────────────────────────────────────────
# Policies
# ──────────────────────────────────────────────────────────────

def single_pass(d, scorer):
    _, action, _ = scorer.score(d.surface_features)
    return action

def vld_investigate(d, scorer, budget=1, eps=0.3, reextract=False):
    v = d.surface_features.copy()
    investigated = set()
    all_evidence = {}
    for step in range(budget):
        dists = scorer.category_distances(v)
        sorted_cats = np.argsort(dists)
        chosen = None
        for c in sorted_cats:
            if int(c) not in investigated:
                chosen = int(c)
                break
        if chosen is None:
            break
        investigated.add(chosen)
        evidence = d.branch_evidence[chosen]
        all_evidence[chosen] = evidence
        if reextract:
            combined = d.surface_features.copy()
            for ev in all_evidence.values():
                combined = combined + ev
            v = combined / (1 + len(all_evidence))
        else:
            v = (1 - eps) * v + eps * evidence
    _, action, _ = scorer.score(v)
    return action

def selective_vld(d, scorer, budget=1, eps=0.3, margin_gate=0.3):
    """Only investigate if initial margin < gate. Otherwise single-pass."""
    _, action, margin = scorer.score(d.surface_features)
    if margin >= margin_gate:
        return action  # confident — skip investigation
    return vld_investigate(d, scorer, budget=budget, eps=eps)

def content_rule(d, scorer, budget=1, eps=0.3):
    if not d.has_label:
        return single_pass(d, scorer)
    v = d.surface_features.copy()
    v = (1 - eps) * v + eps * d.branch_evidence[d.true_category]
    _, action, _ = scorer.score(v)
    return action

def majority_branch(d, scorer, majority_cat, budget=1, eps=0.3):
    v = d.surface_features.copy()
    v = (1 - eps) * v + eps * d.branch_evidence[majority_cat]
    _, action, _ = scorer.score(v)
    return action

def breadth_investigate(d, scorer, budget=1, eps=0.3):
    v = d.surface_features.copy()
    for b in range(min(budget, len(d.branch_evidence))):
        v = (1 - eps) * v + eps * d.branch_evidence[b]
    _, action, _ = scorer.score(v)
    return action

def random_investigate(d, scorer, budget=1, eps=0.3, rng=None):
    if rng is None:
        rng = np.random.default_rng()
    v = d.surface_features.copy()
    branches = rng.choice(len(d.branch_evidence),
                          size=min(budget, len(d.branch_evidence)), replace=False)
    for b in branches:
        v = (1 - eps) * v + eps * d.branch_evidence[b]
    _, action, _ = scorer.score(v)
    return action

def abstain_policy(d, scorer, margin_threshold=0.2, budget=1, eps=0.3):
    v = d.surface_features.copy()
    investigated = set()
    for step in range(budget):
        dists = scorer.category_distances(v)
        sorted_cats = np.argsort(dists)
        chosen = None
        for c in sorted_cats:
            if int(c) not in investigated:
                chosen = int(c)
                break
        if chosen is None:
            break
        investigated.add(chosen)
        v = (1 - eps) * v + eps * d.branch_evidence[chosen]
    _, action, margin = scorer.score(v)
    return action if margin >= margin_threshold else None


# ──────────────────────────────────────────────────────────────
# Bootstrap CI
# ──────────────────────────────────────────────────────────────

def bootstrap_ci(values, n_boot=1000, alpha=0.05, rng=None):
    """95% confidence interval via bootstrap."""
    if rng is None:
        rng = np.random.default_rng(99)
    arr = np.array(values)
    means = [rng.choice(arr, size=len(arr), replace=True).mean() for _ in range(n_boot)]
    lo = np.percentile(means, 100 * alpha / 2)
    hi = np.percentile(means, 100 * (1 - alpha / 2))
    return np.mean(arr), lo, hi


# ──────────────────────────────────────────────────────────────
# EXPERIMENT 1: Distractor Regime Sweep
# ──────────────────────────────────────────────────────────────

def exp1_distractor_regime(n_cases=5000, n_dims=8, n_branches=6, rho=0.6):
    """
    THE KEY EXPERIMENT: sweep neutral_fraction from 0 (all misleading)
    to 1 (all neutral noise). Find where VLD crosses single-pass.
    """
    print("=" * 70)
    print("EXP 1: DISTRACTOR REGIME SWEEP")
    print(f"  n={n_cases}, dims={n_dims}, branches={n_branches}, ρ={rho}")
    print(f"  Sweeping neutral_fraction: how much wrong-branch evidence is noise vs misleading")
    print("=" * 70)

    scorer = CentroidScorer(n_dims, n_branches)

    print(f"\n  {'NeutFrac':<10} {'VLD-b1':<10} {'Single':<10} {'Δ_VLD':<10} "
          f"{'Breadth-b1':<12} {'Majority':<10} {'SelectVLD':<10}")

    results = {'nf': [], 'vld': [], 'single': [], 'breadth': [],
               'majority': [], 'selective': [], 'delta': []}

    for nf in np.arange(0.0, 1.01, 0.1):
        rng = np.random.default_rng(42)  # fresh rng per condition for fair comparison
        world = generate_world(n_cases, n_dims, n_branches, rho,
                               distractor_strength=0.4, neutral_fraction=nf,
                               content_keyed_fraction=0.0, rng=rng)
        eval_rng = np.random.default_rng(99)  # separate rng for random policy
        maj_cat = max(range(n_branches),
                      key=lambda c: sum(1 for d in world if d.true_category == c))

        vld = sum(1 for d in world if vld_investigate(d, scorer, budget=1) == d.true_action) / n_cases
        sing = sum(1 for d in world if single_pass(d, scorer) == d.true_action) / n_cases
        br = sum(1 for d in world if breadth_investigate(d, scorer, budget=1) == d.true_action) / n_cases
        maj = sum(1 for d in world if majority_branch(d, scorer, maj_cat, budget=1) == d.true_action) / n_cases
        sel = sum(1 for d in world if selective_vld(d, scorer, budget=1, margin_gate=0.15) == d.true_action) / n_cases

        results['nf'].append(nf)
        results['vld'].append(vld)
        results['single'].append(sing)
        results['breadth'].append(br)
        results['majority'].append(maj)
        results['selective'].append(sel)
        results['delta'].append(vld - sing)

        marker = " ← VLD > Single" if vld > sing else ""
        print(f"  {nf:<10.1f} {vld:<10.3f} {sing:<10.3f} {vld - sing:<+10.3f} "
              f"{br:<12.3f} {maj:<10.3f} {sel:<10.3f}{marker}")

    crossover = None
    for i in range(len(results['delta']) - 1):
        if results['delta'][i] < 0 and results['delta'][i + 1] >= 0:
            crossover = results['nf'][i]
    if crossover is not None:
        print(f"\n  CROSSOVER: VLD beats single-pass when neutral_fraction ≈ {crossover:.1f}")
    else:
        if all(d >= 0 for d in results['delta']):
            print(f"\n  VLD beats single-pass at ALL neutral fractions")
        else:
            print(f"\n  VLD never beats single-pass (even with all-neutral wrong branches)")

    return results


# ──────────────────────────────────────────────────────────────
# EXPERIMENT 2: ρ Calibration (6 branches, with bootstrap CI)
# ──────────────────────────────────────────────────────────────

def exp2_rho_calibration(n_cases=5000, n_dims=8, n_branches=6,
                         neutral_fraction=0.7, distractor=0.4):
    """
    ρ calibration with realistic evidence regime (70% neutral, 30% misleading).
    Includes bootstrap 95% CIs.
    """
    print(f"\n{'=' * 70}")
    print(f"EXP 2: ρ CALIBRATION (neutral_frac={neutral_fraction}, {n_branches} branches)")
    print(f"{'=' * 70}")

    scorer = CentroidScorer(n_dims, n_branches)
    rng = np.random.default_rng(42)
    boot_rng = np.random.default_rng(99)

    print(f"\n  {'ρ':<6} {'VLD':<16} {'Content':<10} {'Majority':<10} "
          f"{'Random':<10} {'Single':<10} {'Selective':<10}")

    results = {'rho': [], 'vld': [], 'vld_lo': [], 'vld_hi': [],
               'content': [], 'majority': [], 'random': [], 'single': [],
               'selective': [], 'delta': []}

    for rho in np.arange(0.15, 1.01, 0.05):
        world = generate_world(n_cases, n_dims, n_branches, rho, distractor,
                               neutral_fraction=neutral_fraction,
                               content_keyed_fraction=0.5, rng=rng)
        maj_cat = max(range(n_branches),
                      key=lambda c: sum(1 for d in world if d.true_category == c))

        vld_correct = [1 if vld_investigate(d, scorer, budget=1) == d.true_action else 0
                       for d in world]
        vld_mean, vld_lo, vld_hi = bootstrap_ci(vld_correct, rng=boot_rng)

        cont = sum(1 for d in world if content_rule(d, scorer, budget=1) == d.true_action) / n_cases
        maj = sum(1 for d in world if majority_branch(d, scorer, maj_cat, budget=1) == d.true_action) / n_cases
        rand = sum(1 for d in world if random_investigate(d, scorer, budget=1, rng=rng) == d.true_action) / n_cases
        sing = sum(1 for d in world if single_pass(d, scorer) == d.true_action) / n_cases
        sel = sum(1 for d in world if selective_vld(d, scorer, budget=1, margin_gate=0.15) == d.true_action) / n_cases

        results['rho'].append(rho)
        results['vld'].append(vld_mean)
        results['vld_lo'].append(vld_lo)
        results['vld_hi'].append(vld_hi)
        results['content'].append(cont)
        results['majority'].append(maj)
        results['random'].append(rand)
        results['single'].append(sing)
        results['selective'].append(sel)
        results['delta'].append(vld_mean - sing)

        print(f"  {rho:<6.2f} {vld_mean:.3f} [{vld_lo:.3f},{vld_hi:.3f}]  {cont:<10.3f} "
              f"{maj:<10.3f} {rand:<10.3f} {sing:<10.3f} {sel:<10.3f}")

    corr = np.corrcoef(np.array(results['rho']) - 1/n_branches,
                       np.array(results['delta']))[0, 1]
    print(f"\n  Correlation(Δ_VLD-vs-single, ρ): {corr:.3f}")
    beats_single = sum(1 for d in results['delta'] if d > 0)
    print(f"  VLD > single-pass at {beats_single}/{len(results['delta'])} ρ values")
    sel_beats = sum(1 for s, si in zip(results['selective'], results['single']) if s > si)
    print(f"  Selective VLD > single-pass at {sel_beats}/{len(results['selective'])} ρ values")

    return results


# ──────────────────────────────────────────────────────────────
# EXPERIMENT 3: Budget × Distractor Interaction
# ──────────────────────────────────────────────────────────────

def exp3_budget_distractor(n_cases=5000, n_dims=8, n_branches=6, rho=0.6):
    """
    Budget sweep at three evidence regimes: all-neutral, mixed, all-misleading.
    Shows where VLD, re-extraction, and breadth each win.
    """
    print(f"\n{'=' * 70}")
    print(f"EXP 3: BUDGET × DISTRACTOR INTERACTION")
    print(f"{'=' * 70}")

    scorer = CentroidScorer(n_dims, n_branches)
    rng = np.random.default_rng(42)

    for regime_name, nf, dist in [("ALL-NEUTRAL", 1.0, 0.0),
                                   ("MIXED (70/30)", 0.7, 0.4),
                                   ("ALL-MISLEADING", 0.0, 0.4)]:
        print(f"\n  --- {regime_name} ---")
        world = generate_world(n_cases, n_dims, n_branches, rho, dist,
                               neutral_fraction=nf, content_keyed_fraction=0.0, rng=rng)

        print(f"  {'Budget':<8} {'VLD-damp':<10} {'VLD-reext':<10} {'Breadth':<10} "
              f"{'SelectVLD':<10} {'Single':<10}")

        for budget in [0, 1, 2, 3, 4, 6]:
            if budget == 0:
                # Budget 0 = single-pass for all policies
                sing = sum(1 for d in world
                           if single_pass(d, scorer) == d.true_action) / n_cases
                print(f"  {budget:<8} {'—':<10} {'—':<10} {'—':<10} "
                      f"{'—':<10} {sing:<10.3f}  ← baseline")
                continue
            vld_d = sum(1 for d in world
                        if vld_investigate(d, scorer, budget=budget, reextract=False) == d.true_action) / n_cases
            vld_r = sum(1 for d in world
                        if vld_investigate(d, scorer, budget=budget, reextract=True) == d.true_action) / n_cases
            br = sum(1 for d in world
                     if breadth_investigate(d, scorer, budget=budget) == d.true_action) / n_cases
            sel = sum(1 for d in world
                      if selective_vld(d, scorer, budget=budget, margin_gate=0.15) == d.true_action) / n_cases
            sing = sum(1 for d in world
                       if single_pass(d, scorer) == d.true_action) / n_cases

            best = max(vld_d, vld_r, br, sel, sing)
            markers = []
            if vld_d == best: markers.append("damp")
            if vld_r == best: markers.append("reext")
            if br == best: markers.append("breadth")
            if sel == best: markers.append("selective")
            if sing == best: markers.append("single")

            print(f"  {budget:<8} {vld_d:<10.3f} {vld_r:<10.3f} {br:<10.3f} "
                  f"{sel:<10.3f} {sing:<10.3f}  ← best: {','.join(markers)}")


# ──────────────────────────────────────────────────────────────
# EXPERIMENT 4: Selective VLD Margin Gate Sweep
# ──────────────────────────────────────────────────────────────

def exp4_selective_gate(n_cases=5000, n_dims=8, n_branches=6,
                        rho=0.6, neutral_fraction=0.7, distractor=0.4):
    """
    Sweep the margin gate for selective VLD. Find optimal threshold
    where investigating low-confidence + skipping high-confidence
    beats both always-investigate and never-investigate.
    """
    print(f"\n{'=' * 70}")
    print(f"EXP 4: SELECTIVE VLD MARGIN GATE SWEEP")
    print(f"{'=' * 70}")

    scorer = CentroidScorer(n_dims, n_branches)
    rng = np.random.default_rng(42)
    world = generate_world(n_cases, n_dims, n_branches, rho, distractor,
                           neutral_fraction=neutral_fraction,
                           content_keyed_fraction=0.0, rng=rng)

    sing_acc = sum(1 for d in world if single_pass(d, scorer) == d.true_action) / n_cases
    vld_acc = sum(1 for d in world if vld_investigate(d, scorer, budget=1) == d.true_action) / n_cases

    print(f"  Baselines: single-pass={sing_acc:.3f}, VLD-always={vld_acc:.3f}")
    print(f"\n  {'Gate':<8} {'Accuracy':<10} {'Investigated':<14} {'Skipped':<10} "
          f"{'Δ_vs_single':<14} {'Δ_vs_VLD':<12}")

    best_gate, best_acc = 0, 0
    gate_results = []
    for gate in np.arange(0.0, 1.01, 0.05):
        sel_results = []
        n_investigated = 0
        for d in world:
            _, _, margin = scorer.score(d.surface_features)
            if margin < gate:
                action = vld_investigate(d, scorer, budget=1)
                n_investigated += 1
            else:
                action = single_pass(d, scorer)
            sel_results.append(1 if action == d.true_action else 0)

        acc = np.mean(sel_results)
        inv_frac = n_investigated / n_cases
        if acc > best_acc:
            best_acc = acc
            best_gate = gate

        gate_results.append((gate, acc, inv_frac))

    # Print with BEST marker only on the actual optimum
    for gate, acc, inv_frac in gate_results:
        marker = " ← BEST" if gate == best_gate else ""
        print(f"  {gate:<8.2f} {acc:<10.3f} {inv_frac:<14.1%} {1 - inv_frac:<10.1%} "
              f"{acc - sing_acc:<+14.3f} {acc - vld_acc:<+12.3f}{marker}")

    print(f"\n  OPTIMAL GATE: {best_gate:.2f} (accuracy={best_acc:.3f})")
    print(f"  vs single-pass: {best_acc - sing_acc:+.3f}")
    print(f"  vs VLD-always:  {best_acc - vld_acc:+.3f}")
    return best_gate, best_acc


# ──────────────────────────────────────────────────────────────
# EXPERIMENT 5: Abstention with Utility Model
# ──────────────────────────────────────────────────────────────

def exp5_abstain_utility(n_cases=5000, n_dims=8, n_branches=6,
                         rho=0.6, neutral_fraction=0.7, distractor=0.4):
    """
    Full abstention analysis: sweep threshold, compute utility for
    different penalty ratios (SOC=20:1, S2P=5:1, Trading=3:1).
    """
    print(f"\n{'=' * 70}")
    print(f"EXP 5: ABSTENTION UTILITY (three penalty ratios)")
    print(f"{'=' * 70}")

    scorer = CentroidScorer(n_dims, n_branches)
    rng = np.random.default_rng(42)
    world = generate_world(n_cases, n_dims, n_branches, rho, distractor,
                           neutral_fraction=neutral_fraction,
                           content_keyed_fraction=0.0, rng=rng)

    for penalty_name, penalty, abstain_cost in [
        ("SOC (20:1)", 20.0, 1.0),
        ("S2P (5:1)",   5.0, 0.5),
        ("Trading (3:1)", 3.0, 0.3)
    ]:
        print(f"\n  --- {penalty_name}: penalty={penalty}, abstain_cost={abstain_cost} ---")
        print(f"  {'Threshold':<12} {'Committed':<12} {'Abstained':<12} "
              f"{'Accuracy':<10} {'Utility':<10}")

        best_thresh, best_util = 0, -float('inf')
        for thresh in np.arange(0.0, 0.81, 0.05):
            results = [abstain_policy(d, scorer, margin_threshold=thresh, budget=1)
                       for d in world]
            committed = [(r, d) for r, d in zip(results, world) if r is not None]
            n_abstain = sum(1 for r in results if r is None)

            if committed:
                acc = sum(1 for r, d in committed if r == d.true_action) / len(committed)
                util = sum(1.0 if r == d.true_action else -penalty
                           for r, d in committed)
            else:
                acc = 0
                util = 0
            util += n_abstain * (-abstain_cost)
            util /= n_cases

            if util > best_util:
                best_util = util
                best_thresh = thresh

            marker = " ← BEST" if thresh == best_thresh and util == best_util else ""
            print(f"  {thresh:<12.2f} {len(committed):<12} {n_abstain:<12} "
                  f"{acc:<10.3f} {util:<+10.3f}{marker}")

        print(f"  Optimal: threshold={best_thresh:.2f}, utility={best_util:+.3f}")


# ──────────────────────────────────────────────────────────────
# EXPERIMENT 6: Score-Keyed Routing Quality (detailed)
# ──────────────────────────────────────────────────────────────

def exp6_routing_quality(n_cases=5000, n_dims=8, n_branches=6,
                         rho=0.6, neutral_fraction=0.7, distractor=0.4):
    """
    Detailed analysis of routing quality: per-category ρ, confusion
    matrix of routed vs true categories, margin vs routing accuracy.
    """
    print(f"\n{'=' * 70}")
    print(f"EXP 6: ROUTING QUALITY ANALYSIS")
    print(f"{'=' * 70}")

    scorer = CentroidScorer(n_dims, n_branches)
    rng = np.random.default_rng(42)
    world = generate_world(n_cases, n_dims, n_branches, rho, distractor,
                           neutral_fraction=neutral_fraction,
                           content_keyed_fraction=0.0, rng=rng)

    # Routing accuracy per category
    cat_correct = {c: 0 for c in range(n_branches)}
    cat_total = {c: 0 for c in range(n_branches)}
    margins = []
    routing_correct = []

    for d in world:
        routed = scorer.route_category(d.surface_features)
        _, _, margin = scorer.score(d.surface_features)
        correct = 1 if routed == d.true_category else 0
        cat_correct[d.true_category] += correct
        cat_total[d.true_category] += 1
        margins.append(margin)
        routing_correct.append(correct)

    print(f"\n  PER-CATEGORY ROUTING ACCURACY:")
    for c in range(n_branches):
        if cat_total[c] > 0:
            acc = cat_correct[c] / cat_total[c]
            print(f"    Category {c}: {acc:.3f} ({cat_correct[c]}/{cat_total[c]})")

    overall = sum(routing_correct) / len(routing_correct)
    print(f"    Overall: {overall:.3f}")

    # Routing accuracy by margin quartile
    margins = np.array(margins)
    routing_correct = np.array(routing_correct)
    for plo, phi, label in [(0, 25, "P0-P25 (hardest)"),
                             (25, 50, "P25-P50"),
                             (50, 75, "P50-P75"),
                             (75, 100, "P75-P100 (easiest)")]:
        lo_val = np.percentile(margins, plo)
        hi_val = np.percentile(margins, phi)
        mask = (margins >= lo_val) & (margins < hi_val) if phi < 100 else (margins >= lo_val)
        if mask.sum() > 0:
            acc = routing_correct[mask].mean()
            print(f"    {label}: ρ={acc:.3f} (n={mask.sum()}, margin {lo_val:.3f}-{hi_val:.3f})")

    # Action accuracy: VLD vs single-pass on correctly vs incorrectly routed
    vld_on_correct_route = []
    vld_on_wrong_route = []
    single_on_all = []
    for d, rc in zip(world, routing_correct):
        s = 1 if single_pass(d, scorer) == d.true_action else 0
        v = 1 if vld_investigate(d, scorer, budget=1) == d.true_action else 0
        single_on_all.append(s)
        if rc:
            vld_on_correct_route.append(v)
        else:
            vld_on_wrong_route.append(v)

    print(f"\n  ACTION ACCURACY BREAKDOWN:")
    print(f"    Single-pass (all):            {np.mean(single_on_all):.3f}")
    print(f"    VLD on correctly-routed:      {np.mean(vld_on_correct_route):.3f} (n={len(vld_on_correct_route)})")
    print(f"    VLD on incorrectly-routed:    {np.mean(vld_on_wrong_route):.3f} (n={len(vld_on_wrong_route)})")
    print(f"    VLD value = correct-route acc × routing_freq + wrong-route acc × (1-routing_freq)")


# ──────────────────────────────────────────────────────────────
# Plotting
# ──────────────────────────────────────────────────────────────

def plot_results(exp1_results, exp2_results, output_dir="."):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [matplotlib not available]")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Exp 1: distractor regime
    ax = axes[0, 0]
    ax.plot(exp1_results['nf'], exp1_results['vld'], 'b-o', label='VLD budget=1', linewidth=2, markersize=4)
    ax.plot(exp1_results['nf'], exp1_results['single'], 'k--', label='Single-pass', linewidth=2)
    ax.plot(exp1_results['nf'], exp1_results['selective'], 'g-s', label='Selective VLD', linewidth=2, markersize=4)
    ax.plot(exp1_results['nf'], exp1_results['majority'], 'm:', label='Majority', linewidth=1)
    ax.axhline(y=exp1_results['single'][0], color='gray', alpha=0.3)
    ax.set_xlabel('Neutral fraction (0=all misleading, 1=all noise)')
    ax.set_ylabel('Action accuracy')
    ax.set_title('Exp 1: When does VLD beat single-pass?')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    # Exp 1: delta
    ax = axes[0, 1]
    ax.plot(exp1_results['nf'], exp1_results['delta'], 'b-o', linewidth=2, markersize=4)
    ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    ax.set_xlabel('Neutral fraction')
    ax.set_ylabel('Δ (VLD − Single-pass)')
    ax.set_title('Exp 1: VLD advantage by evidence regime')
    ax.grid(True, alpha=0.3)

    # Exp 2: ρ calibration
    ax = axes[1, 0]
    ax.plot(exp2_results['rho'], exp2_results['vld'], 'b-o', label='VLD', linewidth=2, markersize=3)
    ax.fill_between(exp2_results['rho'], exp2_results['vld_lo'], exp2_results['vld_hi'],
                     alpha=0.15, color='blue')
    ax.plot(exp2_results['rho'], exp2_results['single'], 'k--', label='Single-pass', linewidth=2)
    ax.plot(exp2_results['rho'], exp2_results['selective'], 'g-s', label='Selective VLD', linewidth=2, markersize=3)
    ax.plot(exp2_results['rho'], exp2_results['content'], 'r-', label='Content-rule', linewidth=1, alpha=0.6)
    ax.set_xlabel('ρ (score informativeness)')
    ax.set_ylabel('Action accuracy')
    ax.set_title('Exp 2: ρ calibration (70% neutral evidence)')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    # Exp 2: delta vs single-pass
    ax = axes[1, 1]
    ax.plot(exp2_results['rho'], exp2_results['delta'], 'b-o', label='Δ VLD vs Single', linewidth=2, markersize=3)
    sel_delta = [s - si for s, si in zip(exp2_results['selective'], exp2_results['single'])]
    ax.plot(exp2_results['rho'], sel_delta, 'g-s', label='Δ Selective vs Single', linewidth=2, markersize=3)
    ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    ax.set_xlabel('ρ')
    ax.set_ylabel('Δ accuracy')
    ax.set_title('Exp 2: VLD and Selective VLD advantage')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(output_dir, 'vld_sim4_comprehensive.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"\n  Plot saved: {path}")


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    N = 5000

    exp1 = exp1_distractor_regime(n_cases=N)
    exp2 = exp2_rho_calibration(n_cases=N, neutral_fraction=0.7)
    exp3_budget_distractor(n_cases=N)
    exp4_selective_gate(n_cases=N, neutral_fraction=0.7)
    exp5_abstain_utility(n_cases=N, neutral_fraction=0.7)
    exp6_routing_quality(n_cases=N, neutral_fraction=0.7)

    output_dir = os.path.dirname(os.path.abspath(__file__))
    plot_results(exp1, exp2, output_dir)

    print(f"\n{'=' * 70}")
    print("SUMMARY — KEY QUESTIONS ANSWERED")
    print(f"{'=' * 70}")
    print("1. Does VLD beat single-pass?")
    print("   → Depends on evidence regime (Exp 1 crossover point)")
    print("2. Does selective VLD (investigate only when uncertain) help?")
    print("   → Exp 4 optimal gate shows the margin threshold")
    print("3. Which aggregation works at budget > 1?")
    print("   → Exp 3 compares damped vs re-extraction per regime")
    print("4. Is abstention valuable?")
    print("   → Exp 5 shows optimal threshold per penalty ratio")
    print("5. Where does VLD routing work well vs poorly?")
    print("   → Exp 6 breaks down by category and margin quartile")
