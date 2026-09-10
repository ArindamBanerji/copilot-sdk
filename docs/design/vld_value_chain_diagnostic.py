"""
VLD Value Chain Diagnostic (E-DIAG)
====================================
Phase 1b showed: ρ_scorekey = 0.685 BUT Δ_depth = -0.225.
Routing works. Actions get worse. WHY?

This diagnostic tests 5 hypotheses for the value chain break.
Calibrated to real Phase 1b parameters (ρ=0.685, 6 categories, 6 factors).

Run: python vld_value_chain_diagnostic.py
"""

import numpy as np
import os
from dataclasses import dataclass

# ──────────────────────────────────────────────────────────────
# Calibrated world model (matches Phase 1b parameters)
# ──────────────────────────────────────────────────────────────

@dataclass
class Alert:
    true_category: int
    true_action: int
    surface: np.ndarray
    branch_evidence: list  # per-category evidence
    correct_branch: int


class Scorer:
    def __init__(self, n_dims, n_cats, n_actions=4):
        self.n_cats = n_cats
        self.n_actions = n_actions
        self.centroids = np.random.default_rng(7).normal(0, 0.5, (n_cats, n_actions, n_dims))
        # Make centroids more structured: category in dim 1, action in dim 0
        for c in range(n_cats):
            for a in range(n_actions):
                self.centroids[c, a, 0] = (a / (n_actions - 1) - 0.5) * 2
                self.centroids[c, a, 1] = (c / (n_cats - 1) - 0.5) * 2

    def category_distances(self, v):
        return [min(np.linalg.norm(v - self.centroids[c, a])
                    for a in range(self.n_actions))
                for c in range(self.n_cats)]

    def route_category(self, v):
        return int(np.argmin(self.category_distances(v)))

    def score_in_category(self, v, cat):
        """Score within a specific category → best action."""
        dists = [np.linalg.norm(v - self.centroids[cat, a])
                 for a in range(self.n_actions)]
        return int(np.argmin(dists))

    def score_best(self, v):
        """Score across ALL categories → best (category, action)."""
        best_cat, best_act, best_d = 0, 0, float('inf')
        for c in range(self.n_cats):
            for a in range(self.n_actions):
                d = np.linalg.norm(v - self.centroids[c, a])
                if d < best_d:
                    best_d = d
                    best_cat, best_act = c, a
        return best_cat, best_act


def generate_alerts(n, n_dims, n_cats, n_actions, rho_target=0.685,
                    neutral_fraction=0.7, distractor=0.3, rng=None):
    if rng is None:
        rng = np.random.default_rng(42)
    alerts = []
    for _ in range(n):
        true_cat = rng.integers(0, n_cats)
        true_act = rng.integers(0, n_actions)

        surface = rng.normal(0, 0.4, n_dims)
        # Action signal in dim 0 (moderate)
        surface[0] = (true_act / (n_actions - 1) - 0.5) * 2 * 0.4 + rng.normal(0, 0.5)
        # Category signal in dim 1 (controlled by rho_target)
        signal = max((rho_target - 1 / n_cats) * 3.5, 0)
        surface[1] = (true_cat / (n_cats - 1) - 0.5) * 2 * signal + rng.normal(0, 0.8)

        branches = []
        for b in range(n_cats):
            ev = rng.normal(0, 0.15, n_dims)
            if b == true_cat:
                # Correct branch: strong action signal
                ev[0] = (true_act / (n_actions - 1) - 0.5) * 2 * 1.5
                ev[1] = (true_cat / (n_cats - 1) - 0.5) * 2 * 0.5
            else:
                is_neutral = rng.random() < neutral_fraction
                if is_neutral:
                    ev[0] = rng.normal(0, 0.3)
                else:
                    ev[0] = -(true_act / (n_actions - 1) - 0.5) * 2 * distractor
            branches.append(ev)

        alerts.append(Alert(true_cat, true_act, surface, branches, true_cat))
    return alerts


# ──────────────────────────────────────────────────────────────
# Investigation policies
# ──────────────────────────────────────────────────────────────

def single_pass(alert, scorer):
    """Single-pass: score across all categories from surface."""
    _, action = scorer.score_best(alert.surface)
    return action

def single_pass_in_true_category(alert, scorer):
    """Content-rule: score within the TRUE category from surface."""
    return scorer.score_in_category(alert.surface, alert.true_category)

def vld_score_in_routed_category(alert, scorer, budget=1,
                                  neutral_fraction=0.7):
    """VLD: route to category, read evidence, score WITHIN routed category."""
    v = alert.surface.copy()
    routed_cat = scorer.route_category(v)

    evidence = alert.branch_evidence[routed_cat]
    # Re-extraction
    v = (alert.surface + evidence) / 2

    # Score within the ROUTED category (not the true category)
    return scorer.score_in_category(v, routed_cat)

def vld_score_best_after_evidence(alert, scorer, budget=1):
    """VLD: route, read evidence, score across ALL categories."""
    v = alert.surface.copy()
    routed_cat = scorer.route_category(v)

    evidence = alert.branch_evidence[routed_cat]
    v = (alert.surface + evidence) / 2

    # Score across ALL categories (not just routed)
    _, action = scorer.score_best(v)
    return action

def content_then_best(alert, scorer):
    """Content-rule: use true category evidence, score across all."""
    evidence = alert.branch_evidence[alert.true_category]
    v = (alert.surface + evidence) / 2
    _, action = scorer.score_best(v)
    return action


# ──────────────────────────────────────────────────────────────
# HYPOTHESIS TESTS
# ──────────────────────────────────────────────────────────────

def run_diagnostics(n=5000, n_dims=6, n_cats=6, n_actions=4):
    print("=" * 70)
    print("VLD VALUE CHAIN DIAGNOSTIC")
    print(f"  n={n}, dims={n_dims}, cats={n_cats}, actions={n_actions}")
    print(f"  Calibrated to Phase 1b: ρ_target=0.685")
    print("=" * 70)

    scorer = Scorer(n_dims, n_cats, n_actions)
    rng = np.random.default_rng(42)
    alerts = generate_alerts(n, n_dims, n_cats, n_actions, rng=rng)

    # Measure routing accuracy (should be ~0.685)
    routing_correct = [1 if scorer.route_category(a.surface) == a.true_category else 0
                       for a in alerts]
    rho = np.mean(routing_correct)
    print(f"\n  Routing accuracy (ρ): {rho:.3f} (target: 0.685)")

    # ──────────────────────────────────────────────────────────
    # HYPOTHESIS 1: Is single-pass already sufficient?
    # If surface features resolve the action without investigation,
    # any investigation adds noise.
    # ──────────────────────────────────────────────────────────
    print(f"\n{'─' * 70}")
    print("H1: Is single-pass already sufficient?")

    sp_acc = np.mean([1 if single_pass(a, scorer) == a.true_action else 0
                      for a in alerts])
    print(f"  Single-pass accuracy: {sp_acc:.3f}")
    print(f"  If this is high (>0.8), investigation may add noise.")
    print(f"  Assessment: {'LIKELY CAUSE' if sp_acc > 0.7 else 'not the cause'}")

    # ──────────────────────────────────────────────────────────
    # HYPOTHESIS 2: Does scoring WITHIN routed category hurt?
    # VLD routes to a category and scores WITHIN it. If the wrong
    # category's action space is incompatible, the action is wrong.
    # ──────────────────────────────────────────────────────────
    print(f"\n{'─' * 70}")
    print("H2: Does scoring within routed category (vs best-across-all) hurt?")

    vld_in_routed = np.mean([1 if vld_score_in_routed_category(a, scorer) == a.true_action else 0
                             for a in alerts])
    vld_best_after = np.mean([1 if vld_score_best_after_evidence(a, scorer) == a.true_action else 0
                              for a in alerts])

    print(f"  VLD score-in-routed-category: {vld_in_routed:.3f}")
    print(f"  VLD score-best-across-all:    {vld_best_after:.3f}")
    print(f"  Δ (best - in-routed):         {vld_best_after - vld_in_routed:+.3f}")
    print(f"  Assessment: {'LIKELY CAUSE' if vld_in_routed < vld_best_after - 0.02 else 'not the cause'}")

    # ──────────────────────────────────────────────────────────
    # HYPOTHESIS 3: Does re-extraction dilute the surface signal?
    # v = (surface + evidence) / 2 means evidence has 50% weight.
    # If evidence is weaker than surface for action selection,
    # re-extraction hurts.
    # ──────────────────────────────────────────────────────────
    print(f"\n{'─' * 70}")
    print("H3: Does re-extraction dilute the surface signal?")

    # Compare: surface-only vs surface+evidence re-extraction
    # Use TRUE category evidence (remove routing error from the equation)
    content_sp = np.mean([1 if single_pass_in_true_category(a, scorer) == a.true_action else 0
                          for a in alerts])
    content_enriched = np.mean([1 if content_then_best(a, scorer) == a.true_action else 0
                                for a in alerts])

    print(f"  Content-rule, surface-only:    {content_sp:.3f}")
    print(f"  Content-rule, with evidence:   {content_enriched:.3f}")
    print(f"  Δ (enriched - surface):        {content_enriched - content_sp:+.3f}")
    print(f"  If negative: evidence dilutes even with correct routing.")
    print(f"  Assessment: {'LIKELY CAUSE' if content_enriched < content_sp else 'not the cause'}")

    # ──────────────────────────────────────────────────────────
    # HYPOTHESIS 4: Is the damage from wrong routing catastrophic?
    # When routing is wrong (31.5%), how bad is the action?
    # ──────────────────────────────────────────────────────────
    print(f"\n{'─' * 70}")
    print("H4: Is wrong-routing damage catastrophic?")

    correct_route_actions = []
    wrong_route_actions = []
    sp_on_correct = []
    sp_on_wrong = []

    for a, rc in zip(alerts, routing_correct):
        vld_act = vld_score_in_routed_category(a, scorer)
        sp_act = single_pass(a, scorer)
        if rc:
            correct_route_actions.append(1 if vld_act == a.true_action else 0)
            sp_on_correct.append(1 if sp_act == a.true_action else 0)
        else:
            wrong_route_actions.append(1 if vld_act == a.true_action else 0)
            sp_on_wrong.append(1 if sp_act == a.true_action else 0)

    cr_acc = np.mean(correct_route_actions) if correct_route_actions else 0
    wr_acc = np.mean(wrong_route_actions) if wrong_route_actions else 0
    sp_cr = np.mean(sp_on_correct) if sp_on_correct else 0
    sp_wr = np.mean(sp_on_wrong) if sp_on_wrong else 0

    print(f"  VLD on correctly-routed:      {cr_acc:.3f} (n={len(correct_route_actions)})")
    print(f"  VLD on incorrectly-routed:    {wr_acc:.3f} (n={len(wrong_route_actions)})")
    print(f"  Single-pass on same correct:  {sp_cr:.3f}")
    print(f"  Single-pass on same wrong:    {sp_wr:.3f}")
    print(f"  VLD gain on correct route:    {cr_acc - sp_cr:+.3f}")
    print(f"  VLD loss on wrong route:      {wr_acc - sp_wr:+.3f}")
    print(f"  Weighted Δ: {rho:.3f}×{cr_acc - sp_cr:+.3f} + {1-rho:.3f}×{wr_acc - sp_wr:+.3f} "
          f"= {rho*(cr_acc-sp_cr) + (1-rho)*(wr_acc-sp_wr):+.3f}")
    print(f"  Assessment: {'LIKELY CAUSE' if wr_acc < sp_wr - 0.05 else 'not the cause'}")

    # ──────────────────────────────────────────────────────────
    # HYPOTHESIS 5: Is the action space interaction the problem?
    # The scorer selects the best action WITHIN a category.
    # Different categories have different centroid slices.
    # Scoring in the wrong category's slice → systematically
    # wrong action even if the factor vector is good.
    # ──────────────────────────────────────────────────────────
    print(f"\n{'─' * 70}")
    print("H5: Does wrong-category scoring produce systematically wrong actions?")

    # For incorrectly-routed cases: what action does the wrong slice give
    # vs what the correct slice would give?
    wrong_slice_correct = 0
    right_slice_correct = 0
    wrong_route_cases = [(a, scorer.route_category(a.surface))
                         for a, rc in zip(alerts, routing_correct) if not rc]

    for a, routed_cat in wrong_route_cases:
        evidence = a.branch_evidence[routed_cat]
        v = (a.surface + evidence) / 2
        wrong_action = scorer.score_in_category(v, routed_cat)
        right_action = scorer.score_in_category(v, a.true_category)
        if wrong_action == a.true_action:
            wrong_slice_correct += 1
        if right_action == a.true_action:
            right_slice_correct += 1

    n_wrong = len(wrong_route_cases)
    if n_wrong > 0:
        print(f"  On {n_wrong} incorrectly-routed cases:")
        print(f"    Action from WRONG category slice: {wrong_slice_correct/n_wrong:.3f}")
        print(f"    Action from TRUE category slice:  {right_slice_correct/n_wrong:.3f}")
        print(f"    Δ: {(right_slice_correct - wrong_slice_correct)/n_wrong:+.3f}")
        print(f"  Assessment: {'LIKELY CAUSE' if wrong_slice_correct/n_wrong < right_slice_correct/n_wrong - 0.05 else 'not the cause'}")

    # ──────────────────────────────────────────────────────────
    # SUMMARY: What's causing the negative Δ_depth?
    # ──────────────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("DIAGNOSIS SUMMARY")
    print(f"{'=' * 70}")

    print(f"\n  Single-pass accuracy:          {sp_acc:.3f}")
    print(f"  VLD (score-in-routed):         {vld_in_routed:.3f}")
    print(f"  VLD (score-best-after):        {vld_best_after:.3f}")
    print(f"  Δ_depth (in-routed vs SP):     {vld_in_routed - sp_acc:+.3f}")
    print(f"  Δ_depth (best-after vs SP):    {vld_best_after - sp_acc:+.3f}")

    print(f"\n  HYPOTHESES:")
    causes = []
    if sp_acc > 0.7:
        causes.append("H1: surface already sufficient")
    if vld_in_routed < vld_best_after - 0.02:
        causes.append("H2: scoring within routed category hurts")
    if content_enriched < content_sp:
        causes.append("H3: re-extraction dilutes signal")
    if wr_acc < sp_wr - 0.05:
        causes.append("H4: wrong routing damage is catastrophic")
    if n_wrong > 0 and wrong_slice_correct / n_wrong < right_slice_correct / n_wrong - 0.05:
        causes.append("H5: wrong-category action space is incompatible")

    if causes:
        for c in causes:
            print(f"    ✗ {c}")
    else:
        print(f"    No single dominant cause identified — interaction effect")

    # ──────────────────────────────────────────────────────────
    # PRESCRIPTION: What fixes the value chain?
    # ──────────────────────────────────────────────────────────
    print(f"\n  PRESCRIPTION:")

    if vld_best_after > sp_acc:
        print(f"    → score-best-after-evidence beats single-pass ({vld_best_after:.3f} vs {sp_acc:.3f})")
        print(f"    → FIX: score across ALL categories after investigation, not within routed")
        print(f"    → The value chain works IF the final scoring doesn't lock to the routed category")
    elif content_enriched > sp_acc:
        print(f"    → Content-rule enrichment beats single-pass ({content_enriched:.3f} vs {sp_acc:.3f})")
        print(f"    → FIX: routing is the bottleneck, not enrichment")
        print(f"    → Improve routing accuracy or fall back to content-rule for step 0")
    else:
        print(f"    → Investigation doesn't help: even correct-branch evidence doesn't improve actions")
        print(f"    → FIX: redesign evidence enrichment — current patterns don't enrich action-relevant factors")

    # ──────────────────────────────────────────────────────────
    # ADDITIONAL: Decompose by factor dimension
    # ──────────────────────────────────────────────────────────
    print(f"\n{'─' * 70}")
    print("FACTOR DIMENSION ANALYSIS")

    # For each dimension: does investigation move v in the right direction?
    dim_improvements = np.zeros(n_dims)
    dim_degradations = np.zeros(n_dims)

    for a in alerts[:1000]:  # sample for speed
        routed = scorer.route_category(a.surface)
        evidence = a.branch_evidence[routed]
        v_after = (a.surface + evidence) / 2

        # Target: the centroid for (true_category, true_action)
        target = scorer.centroids[a.true_category, a.true_action]
        for d in range(n_dims):
            before_dist = abs(a.surface[d] - target[d])
            after_dist = abs(v_after[d] - target[d])
            if after_dist < before_dist:
                dim_improvements[d] += 1
            else:
                dim_degradations[d] += 1

    print(f"  Per-dimension: does investigation move v closer to the correct centroid?")
    factor_names = ['priv_identity', 'asset_crit', 'threat_intel',
                    'time_anomaly', 'pattern_hist', 'device_trust']
    for d in range(n_dims):
        total = dim_improvements[d] + dim_degradations[d]
        pct = dim_improvements[d] / total if total > 0 else 0
        direction = "✓ improves" if pct > 0.5 else "✗ degrades"
        print(f"    dim {d} ({factor_names[d] if d < len(factor_names) else '?'}): "
              f"{direction} ({pct:.1%} improve, {1-pct:.1%} degrade)")


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    run_diagnostics(n=5000, n_dims=6, n_cats=6, n_actions=4)
