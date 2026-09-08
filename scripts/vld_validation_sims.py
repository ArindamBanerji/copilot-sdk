"""
VLD Validation Simulations — ρ Calibration + Budget Sweep
=========================================================
Two cheap synthetic simulations that validate the VLD value model
BEFORE committing to the full experiment program.

Value ≈ m_conditional × (ρ − ½) × (1 − budget/branches)

Sim 1: Sweep ρ, confirm Δ_VLD tracks (ρ − ½)
Sim 2: Sweep budget, confirm VLD dominates at intermediate budgets

Run: python vld_validation_sims.py
Output: two PNG plots + console summary

No platform dependencies. Pure numpy + matplotlib.
"""

import numpy as np
import os
from dataclasses import dataclass

# ──────────────────────────────────────────────────────────────
# World model: conditional investigation with branching
# ──────────────────────────────────────────────────────────────

@dataclass
class Decision:
    """A synthetic decision with conditional branching."""
    true_class: int          # 0 or 1 (ground truth)
    surface_features: np.ndarray  # initial observation (noisy)
    branch_a_evidence: np.ndarray  # evidence behind branch A
    branch_b_evidence: np.ndarray  # evidence behind branch B
    correct_branch: str      # 'a' or 'b' — which branch resolves the case
    distractor_pull: float   # how much wrong-branch evidence misleads


def generate_world(n_cases: int, n_dims: int, rho_target: float,
                   distractor_strength: float = 0.3,
                   rng: np.random.Generator = None) -> list[Decision]:
    """
    Generate synthetic decisions with conditional branching.

    rho_target: controls how informative the surface features are about
    which branch to follow. At rho=0.5, surface gives no routing signal.
    At rho=1.0, surface perfectly indicates the correct branch.

    distractor_strength: how much wrong-branch evidence pulls toward
    the wrong class. 0 = noiseless (breadth always wins). >0 = wrong
    branch actively misleads (adaptive selection matters).
    """
    if rng is None:
        rng = np.random.default_rng(42)

    decisions = []
    for _ in range(n_cases):
        true_class = rng.integers(0, 2)
        correct_branch = rng.choice(['a', 'b'])

        # Surface features: NOISY version of true class
        # Class signal is weak and corrupted — surface alone should NOT resolve
        surface = rng.normal(0, 0.5, n_dims)
        class_noise = rng.normal(0, 0.6)  # substantial noise on class dim
        surface[0] = (2 * true_class - 1) * 0.2 + class_noise  # weak + noisy

        # Routing signal: dimension 1 indicates correct branch
        # Strength controlled by rho_target
        routing_signal = 1.0 if correct_branch == 'a' else -1.0
        # At rho=0.5, routing_noise drowns signal; at rho=1.0, signal clear
        routing_noise = rng.normal(0, 1.0)
        signal_strength = (rho_target - 0.5) * 4.0  # 0 at rho=0.5, 2 at rho=1.0
        surface[1] = routing_signal * signal_strength + routing_noise * (1.5 - signal_strength * 0.5)

        # Correct branch: reveals true class clearly
        correct_evidence = rng.normal(0, 0.2, n_dims)
        correct_evidence[0] = (2 * true_class - 1) * 2.0  # strong class signal

        # Wrong branch: actively misleads (pulls toward wrong class)
        wrong_evidence = rng.normal(0, 0.2, n_dims)
        wrong_evidence[0] = -(2 * true_class - 1) * distractor_strength * 2.0

        if correct_branch == 'a':
            branch_a = correct_evidence
            branch_b = wrong_evidence
        else:
            branch_a = wrong_evidence
            branch_b = correct_evidence

        decisions.append(Decision(
            true_class=true_class,
            surface_features=surface,
            branch_a_evidence=branch_a,
            branch_b_evidence=branch_b,
            correct_branch=correct_branch,
            distractor_pull=distractor_strength
        ))
    return decisions


# ──────────────────────────────────────────────────────────────
# Scorer: simple centroid-distance classifier
# ──────────────────────────────────────────────────────────────

class CentroidScorer:
    """Nearest-centroid classifier (the CI scoring mechanism)."""

    def __init__(self, n_dims: int):
        # Two centroids: class 0 at [-1, 0, ...], class 1 at [+1, 0, ...]
        self.centroids = np.zeros((2, n_dims))
        self.centroids[0, 0] = -1.0
        self.centroids[1, 0] = 1.0

    def score(self, v: np.ndarray) -> int:
        """Return predicted class (nearest centroid)."""
        d0 = np.linalg.norm(v - self.centroids[0])
        d1 = np.linalg.norm(v - self.centroids[1])
        return 0 if d0 < d1 else 1

    def confidence(self, v: np.ndarray) -> float:
        """Margin between centroids (higher = more confident)."""
        d0 = np.linalg.norm(v - self.centroids[0])
        d1 = np.linalg.norm(v - self.centroids[1])
        return abs(d0 - d1)

    def route_signal(self, v: np.ndarray) -> str:
        """Use dimension 1 to decide which branch to follow."""
        return 'a' if v[1] > 0 else 'b'


# ──────────────────────────────────────────────────────────────
# Investigation policies
# ──────────────────────────────────────────────────────────────

def single_pass(d: Decision, scorer: CentroidScorer) -> int:
    """Single-pass: score from surface features only."""
    return scorer.score(d.surface_features)


def vld_investigate(d: Decision, scorer: CentroidScorer,
                    budget: int = 2, eps: float = 0.3) -> int:
    """
    VLD: score surface → use intermediate score to route → read
    correct branch → re-score with admitted evidence.
    """
    # Step 0: initial assessment
    v = d.surface_features.copy()

    if budget < 1:
        return scorer.score(v)

    # Step 1: use scorer's routing signal to pick branch
    branch = scorer.route_signal(v)

    if branch == 'a':
        evidence = d.branch_a_evidence
    else:
        evidence = d.branch_b_evidence

    # Damped update with first branch evidence
    v = (1 - eps) * v + eps * evidence

    if budget < 2:
        return scorer.score(v)

    # Step 2: if budget allows, read second branch too
    if branch == 'a':
        evidence2 = d.branch_b_evidence
    else:
        evidence2 = d.branch_a_evidence

    v = (1 - eps) * v + eps * evidence2
    return scorer.score(v)


def breadth_investigate(d: Decision, scorer: CentroidScorer,
                        budget: int = 2, eps: float = 0.3) -> int:
    """
    Breadth: read branches in fixed order (static relevance),
    no score-conditioned routing. Always reads A first, then B.
    """
    v = d.surface_features.copy()

    if budget < 1:
        return scorer.score(v)

    # Always read branch A first (static order)
    v = (1 - eps) * v + eps * d.branch_a_evidence

    if budget < 2:
        return scorer.score(v)

    # Then branch B
    v = (1 - eps) * v + eps * d.branch_b_evidence
    return scorer.score(v)


def random_investigate(d: Decision, scorer: CentroidScorer,
                       budget: int = 2, eps: float = 0.3,
                       rng: np.random.Generator = None) -> int:
    """
    Random: pick branches randomly (placebo arm).
    """
    if rng is None:
        rng = np.random.default_rng()

    v = d.surface_features.copy()

    if budget < 1:
        return scorer.score(v)

    # Random branch selection
    if rng.random() < 0.5:
        first, second = d.branch_a_evidence, d.branch_b_evidence
    else:
        first, second = d.branch_b_evidence, d.branch_a_evidence

    v = (1 - eps) * v + eps * first

    if budget < 2:
        return scorer.score(v)

    v = (1 - eps) * v + eps * second
    return scorer.score(v)


# ──────────────────────────────────────────────────────────────
# Sim 1: ρ calibration curve
# ──────────────────────────────────────────────────────────────

def sim1_rho_calibration(n_cases: int = 2000, n_dims: int = 8,
                         distractor: float = 0.4):
    """
    Sweep ρ from 0.3 to 1.0. Plot Δ_VLD(ρ).
    Success criteria:
    - Δ vanishes at ρ ≈ 0.5
    - Δ > 0 for ρ > 0.5
    - Δ < 0 for ρ < 0.5
    - Approximately linear in (ρ − ½)
    """
    print("=" * 60)
    print("SIM 1: ρ CALIBRATION CURVE")
    print(f"  n_cases={n_cases}, n_dims={n_dims}, distractor={distractor}")
    print("=" * 60)

    rho_values = np.arange(0.3, 1.01, 0.05)
    results = {
        'rho': [],
        'vld_acc': [],
        'breadth_acc': [],
        'random_acc': [],
        'single_acc': [],
        'delta_vld_vs_random': [],
        'delta_vld_vs_breadth': [],
    }

    scorer = CentroidScorer(n_dims)
    rng = np.random.default_rng(42)

    for rho in rho_values:
        world = generate_world(n_cases, n_dims, rho, distractor, rng=rng)

        # Budget = 1 (can only read ONE branch — forces routing to matter)
        vld_correct = sum(1 for d in world
                          if vld_investigate(d, scorer, budget=1) == d.true_class)
        breadth_correct = sum(1 for d in world
                              if breadth_investigate(d, scorer, budget=1) == d.true_class)
        random_correct = sum(1 for d in world
                             if random_investigate(d, scorer, budget=1, rng=rng) == d.true_class)
        single_correct = sum(1 for d in world
                             if single_pass(d, scorer) == d.true_class)

        vld_acc = vld_correct / n_cases
        breadth_acc = breadth_correct / n_cases
        random_acc = random_correct / n_cases
        single_acc = single_correct / n_cases

        results['rho'].append(rho)
        results['vld_acc'].append(vld_acc)
        results['breadth_acc'].append(breadth_acc)
        results['random_acc'].append(random_acc)
        results['single_acc'].append(single_acc)
        results['delta_vld_vs_random'].append(vld_acc - random_acc)
        results['delta_vld_vs_breadth'].append(vld_acc - breadth_acc)

        print(f"  ρ={rho:.2f}  VLD={vld_acc:.3f}  breadth={breadth_acc:.3f}  "
              f"random={random_acc:.3f}  single={single_acc:.3f}  "
              f"Δ_rand={vld_acc - random_acc:+.3f}  Δ_breadth={vld_acc - breadth_acc:+.3f}")

    # Validation checks
    print("\n--- VALIDATION ---")
    mid_idx = np.argmin(np.abs(np.array(results['rho']) - 0.5))
    delta_at_half = results['delta_vld_vs_random'][mid_idx]
    print(f"  Δ at ρ=0.5: {delta_at_half:+.4f} (should be ≈ 0)")

    high_rho_deltas = [d for r, d in zip(results['rho'], results['delta_vld_vs_random'])
                       if r > 0.6]
    low_rho_deltas = [d for r, d in zip(results['rho'], results['delta_vld_vs_random'])
                      if r < 0.45]

    if high_rho_deltas:
        print(f"  Mean Δ for ρ > 0.6: {np.mean(high_rho_deltas):+.4f} (should be > 0)")
    if low_rho_deltas:
        print(f"  Mean Δ for ρ < 0.45: {np.mean(low_rho_deltas):+.4f} (should be < 0)")

    # Linearity check: correlation of Δ with (ρ − 0.5)
    rho_centered = np.array(results['rho']) - 0.5
    deltas = np.array(results['delta_vld_vs_random'])
    corr = np.corrcoef(rho_centered, deltas)[0, 1]
    print(f"  Correlation(Δ, ρ−½): {corr:.3f} (should be > 0.8)")

    verdict = "PASS" if (abs(delta_at_half) < 0.03 and
                         corr > 0.7 and
                         np.mean(high_rho_deltas) > 0) else "NEEDS INVESTIGATION"
    print(f"\n  VERDICT: {verdict}")

    return results


# ──────────────────────────────────────────────────────────────
# Sim 2: Budget sweep
# ──────────────────────────────────────────────────────────────

def sim2_budget_sweep(n_cases: int = 2000, n_dims: int = 8,
                      rho: float = 0.75, distractor: float = 0.4):
    """
    Fix ρ at a realistic value. Sweep budget from 0 to 2 (max branches).
    Success: VLD dominates at budget=1; breadth catches up at budget=2.
    """
    print("\n" + "=" * 60)
    print("SIM 2: BUDGET SWEEP")
    print(f"  n_cases={n_cases}, n_dims={n_dims}, ρ={rho}, distractor={distractor}")
    print("=" * 60)

    scorer = CentroidScorer(n_dims)
    rng = np.random.default_rng(42)
    world = generate_world(n_cases, n_dims, rho, distractor, rng=rng)

    results = {'budget': [], 'vld': [], 'breadth': [], 'random': [], 'single': []}

    for budget in [0, 1, 2]:
        vld_acc = sum(1 for d in world
                      if vld_investigate(d, scorer, budget=budget) == d.true_class) / n_cases
        breadth_acc = sum(1 for d in world
                          if breadth_investigate(d, scorer, budget=budget) == d.true_class) / n_cases
        random_acc = sum(1 for d in world
                         if random_investigate(d, scorer, budget=budget, rng=rng) == d.true_class) / n_cases
        single_acc = sum(1 for d in world
                         if single_pass(d, scorer) == d.true_class) / n_cases

        results['budget'].append(budget)
        results['vld'].append(vld_acc)
        results['breadth'].append(breadth_acc)
        results['random'].append(random_acc)
        results['single'].append(single_acc)

        print(f"  budget={budget}  VLD={vld_acc:.3f}  breadth={breadth_acc:.3f}  "
              f"random={random_acc:.3f}  single={single_acc:.3f}")

    # Validation
    print("\n--- VALIDATION ---")
    vld_b1 = results['vld'][1]
    breadth_b1 = results['breadth'][1]
    vld_b2 = results['vld'][2]
    breadth_b2 = results['breadth'][2]

    print(f"  Budget=1: VLD={vld_b1:.3f} vs breadth={breadth_b1:.3f} "
          f"(VLD should win: Δ={vld_b1 - breadth_b1:+.3f})")
    print(f"  Budget=2: VLD={vld_b2:.3f} vs breadth={breadth_b2:.3f} "
          f"(should converge: Δ={vld_b2 - breadth_b2:+.3f})")

    b1_wins = vld_b1 > breadth_b1 + 0.01
    b2_converges = abs(vld_b2 - breadth_b2) < 0.03

    verdict = "PASS" if (b1_wins and b2_converges) else "NEEDS INVESTIGATION"
    print(f"\n  VERDICT: {verdict}")

    return results


# ──────────────────────────────────────────────────────────────
# Plotting
# ──────────────────────────────────────────────────────────────

def plot_results(sim1_results, sim2_results, output_dir: str = "."):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [matplotlib not available — skipping plots]")
        return

    # Sim 1 plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(sim1_results['rho'], sim1_results['vld_acc'],
             'b-o', label='VLD (score-routed)', linewidth=2)
    ax1.plot(sim1_results['rho'], sim1_results['breadth_acc'],
             'g-s', label='Breadth (static order)', linewidth=2)
    ax1.plot(sim1_results['rho'], sim1_results['random_acc'],
             'r-^', label='Random (placebo)', linewidth=1.5, alpha=0.7)
    ax1.plot(sim1_results['rho'], sim1_results['single_acc'],
             'k--', label='Single-pass (no investigation)', linewidth=1, alpha=0.5)
    ax1.axvline(x=0.5, color='gray', linestyle=':', alpha=0.5, label='ρ = 0.5')
    ax1.set_xlabel('ρ (score informativeness)')
    ax1.set_ylabel('Accuracy')
    ax1.set_title('Sim 1: ρ Calibration Curve (budget=1)')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    ax2.plot(sim1_results['rho'], sim1_results['delta_vld_vs_random'],
             'b-o', label='Δ VLD vs Random', linewidth=2)
    ax2.plot(sim1_results['rho'], sim1_results['delta_vld_vs_breadth'],
             'g-s', label='Δ VLD vs Breadth', linewidth=2)
    ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
    ax2.axvline(x=0.5, color='gray', linestyle=':', alpha=0.5)
    ax2.set_xlabel('ρ (score informativeness)')
    ax2.set_ylabel('Δ accuracy (VLD − comparator)')
    ax2.set_title('Sim 1: VLD Advantage vs ρ')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    path1 = os.path.join(output_dir, 'vld_sim1_rho_calibration.png')
    plt.savefig(path1, dpi=150)
    plt.close()
    print(f"\n  Plot saved: {path1}")

    # Sim 2 plot
    fig, ax = plt.subplots(figsize=(8, 5))

    budgets = sim2_results['budget']
    ax.plot(budgets, sim2_results['vld'], 'b-o', label='VLD', linewidth=2, markersize=10)
    ax.plot(budgets, sim2_results['breadth'], 'g-s', label='Breadth', linewidth=2, markersize=10)
    ax.plot(budgets, sim2_results['random'], 'r-^', label='Random', linewidth=1.5, markersize=8)
    ax.plot(budgets, sim2_results['single'], 'k--', label='Single-pass', linewidth=1, alpha=0.5)
    ax.set_xlabel('Evidence budget (# branch reads)')
    ax.set_ylabel('Accuracy')
    ax.set_title(f'Sim 2: Budget Sweep (ρ={0.75})')
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(['0\n(surface only)', '1\n(one branch)', '2\n(both branches)'])
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path2 = os.path.join(output_dir, 'vld_sim2_budget_sweep.png')
    plt.savefig(path2, dpi=150)
    plt.close()
    print(f"  Plot saved: {path2}")


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    sim1 = sim1_rho_calibration(n_cases=3000, distractor=0.4)
    sim2 = sim2_budget_sweep(n_cases=3000, rho=0.75, distractor=0.4)

    output_dir = os.path.dirname(os.path.abspath(__file__))
    plot_results(sim1, sim2, output_dir)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("If both PASS:")
    print("  → Value model predictions hold in controlled setting")
    print("  → ρ calibration instrument works")
    print("  → Proceed to Phase 1 (SOC handcrafted Ψ)")
    print("If Sim 1 FAILS:")
    print("  → Check: is the scorer actually routing? Is ρ measured correctly?")
    print("If Sim 2 FAILS:")
    print("  → Check: is the budget constraint binding? Is distractor strength sufficient?")
