"""
GAE decision-mirror — the RGI loop end-to-end on a synthetic stream.

This is the "more than a toy" example: it shows the three things that make
GAE *Recursive Graph Improvement*, not just an attention library —

  1. COMPOUND   decision accuracy climbs as verified outcomes reshape the
                centroid geometry (ProfileScorer.update, Eq. 4b/4c).
  2. GOVERN     the conservation gate abstains on a category it has not yet
                earned the right to decide (check_conservation / conservation_status).
  3. INSPECT    every decision is traceable to the centroid cell it moved —
                open the tensor, point to the cell, see what changed.
  4. REMEMBER   the "judgment memory" is just the centroid tensor — ~200
                floats, a few KB — saved and reloaded in one line. No database.

This is a runnable sketch of the Judgment Memory paper's core experiments
(Banerji, "Judgment Memory: A Conservation-Bounded Fourth Cognitive Type"):
  COMPOUND  ~ E-JM-6  (bounded accuracy +21.96pp, saturating at c_acc=0.643)
  GOVERN    ~ E-JM-4  (conservation + the compounding feedback loop:
                       higher q clears more categories through the gate)
  TRUST TRAP~ E-JM-2/5 (93.6% of domains hold a trust trap; the paper surfaces
                        63% of them at a 0% false-discovery rate)

Fully synthetic. No external data, no network, numpy-only (matplotlib optional
for the learning-curve PNG). Domain is deliberately generic — a refund-triage
stream — so nothing here is a shipped Compounding Intelligence copilot.

Run:
    python examples/decision_mirror/run_decision_mirror.py
"""

from __future__ import annotations

import numpy as np

from gae import (
    ProfileScorer,
    KernelType,
    check_conservation,
    compute_theta_min,
    run_ablation,
    EvaluationScenario,
)

# Coverage proxy for the conservation gate (override rate). Held fixed here so
# the demo's gate is driven by accumulated VOLUME — the thing a new category
# lacks. θ_min = 23.53/(α·V); signal = α·q·V; GREEN at signal ≥ 2·θ_min.
ALPHA_COVERAGE = 0.30


def gate_for(verified: int, correct: int) -> tuple[str, float]:
    """Conservation status for one category from its accumulated volume."""
    if verified == 0:
        return "RED", 0.0
    q = correct / verified
    theta_min = compute_theta_min(ALPHA_COVERAGE, max(verified, 1))
    chk = check_conservation(ALPHA_COVERAGE, q, float(verified), theta_min)
    return chk.status, float(chk.signal)

RNG = np.random.default_rng(7)

# ─────────────────────────────────────────────────────────────────────
# Domain — a generic refund-triage decision (not a CI product copilot)
# ─────────────────────────────────────────────────────────────────────
CATEGORIES   = ["standard", "subscription", "high_value"]
ACTIONS      = ["auto_approve", "manual_review", "deny"]
FACTOR_NAMES = ["amount_ratio", "account_age", "prior_disputes", "policy_match"]

N_CAT, N_ACT, N_FAC = len(CATEGORIES), len(ACTIONS), len(FACTOR_NAMES)
cat_i = {c: i for i, c in enumerate(CATEGORIES)}
act_i = {a: i for i, a in enumerate(ACTIONS)}

# The firm's TRUE policy the engine must learn (hidden oracle). One prototype
# per (category, action). The engine never sees this — it only sees whether a
# verified outcome said its decision was right.
MU_TRUE = np.full((N_CAT, N_ACT, N_FAC), 0.5)
for c in range(N_CAT):
    MU_TRUE[c, act_i["auto_approve"]]  = [0.15, 0.85, 0.10, 0.90]   # clean, trusted
    MU_TRUE[c, act_i["manual_review"]] = [0.55, 0.45, 0.50, 0.50]   # ambiguous
    MU_TRUE[c, act_i["deny"]]          = [0.90, 0.20, 0.90, 0.15]   # risky
# high_value is stricter: shift its deny prototype so the firm's policy differs
MU_TRUE[cat_i["high_value"], act_i["deny"]] = [0.70, 0.30, 0.70, 0.25]


def sample_case(category_index: int) -> tuple[np.ndarray, int]:
    """Draw a synthetic factor vector near one of the true prototypes and
    return (factor_vector, ground_truth_action_index)."""
    gt_action = int(RNG.integers(0, N_ACT))
    center = MU_TRUE[category_index, gt_action]
    # σ=0.16 → prototypes overlap, so the firm's policy is genuinely learned
    # over hundreds of decisions, not memorised in one window.
    f = np.clip(center + RNG.normal(0.0, 0.16, size=N_FAC), 0.0, 1.0)
    return f, gt_action


def category_stream(n: int) -> np.ndarray:
    """Category mix: high_value is RARE (6%) — so the engine must wait before
    it has earned the right to decide on it (conservation stays below floor)."""
    return RNG.choice(N_CAT, size=n, p=[0.57, 0.37, 0.06])


# ─────────────────────────────────────────────────────────────────────
# Build the scorer from GENERIC centroids (nothing firm-specific yet)
# ─────────────────────────────────────────────────────────────────────
mu0 = np.full((N_CAT, N_ACT, N_FAC), 0.5)          # neutral prior — knows nothing
scorer = ProfileScorer(mu=mu0.copy(), actions=ACTIONS, kernel=KernelType.L2,
                       categories=CATEGORIES, eta_override=0.01)

print("GAE decision-mirror — learning a refund-triage policy from verified outcomes")
print(f"  tensor shape {mu0.shape}  (categories={N_CAT}, actions={N_ACT}, factors={N_FAC})")
print(f"  kernel: L2   |   start: generic centroids (0.5), zero firm knowledge\n")

# ─────────────────────────────────────────────────────────────────────
# THE RGI LOOP — score → verify → reshape, over a stream of decisions
# ─────────────────────────────────────────────────────────────────────
N = 1200
WINDOW = 75
cats = category_stream(N)

# per-category running counts (for the conservation gate)
seen   = np.zeros(N_CAT, dtype=int)
correct_cat = np.zeros(N_CAT, dtype=int)
roll_correct: list[int] = []
curve_x, curve_y = [], []
abstained = np.zeros(N_CAT, dtype=int)     # auto-action withheld (gate not GREEN)
first_green: dict[int, int] = {}            # step each category earned the right

# capture one high_value case to show the inspectable centroid move
watched_before = None
watched_cell = None

for step in range(1, N + 1):
    c = int(cats[step - 1])
    f, gt = sample_case(c)

    # 1) GOVERN — has the engine earned the right to act on this category?
    status, _ = gate_for(int(seen[c]), int(correct_cat[c]))
    acting = status == "GREEN"
    if acting and c not in first_green:
        first_green[c] = step
    if not acting:
        abstained[c] += 1          # route to a human; still learn below

    # 2) SCORE — typed decision (this is the jev-parity object)
    result = scorer.score(f, category_index=c)
    pred = result.action_index
    is_correct = (pred == gt)

    # 3) RESHAPE — the verified outcome moves the geometry
    if CATEGORIES[c] == "high_value" and watched_before is None and seen[c] >= 3:
        watched_cell = (c, gt)
        watched_before = scorer.centroids[c, gt].copy()
    scorer.update(f, category_index=c, action_index=pred, correct=is_correct,
                  gt_action_index=None if is_correct else gt)

    seen[c] += 1
    correct_cat[c] += int(is_correct)
    roll_correct.append(int(is_correct))
    if step % WINDOW == 0:
        acc = float(np.mean(roll_correct[-WINDOW:]))
        curve_x.append(step); curve_y.append(acc)
        hv_status, _ = gate_for(int(seen[cat_i["high_value"]]),
                                int(correct_cat[cat_i["high_value"]]))
        print(f"  decisions {step:5d}  |  rolling accuracy (last {WINDOW}) = {acc:5.1%}"
              f"   high_value gate = {hv_status:5s} (seen={seen[cat_i['high_value']]})")

# ─────────────────────────────────────────────────────────────────────
# 1) COMPOUND — the headline number
# ─────────────────────────────────────────────────────────────────────
first = float(np.mean(roll_correct[:WINDOW]))
last  = float(np.mean(roll_correct[-WINDOW:]))
print(f"\n[COMPOUND ~ E-JM-6]  accuracy  {first:.1%} (first {WINDOW})  ->  {last:.1%} (last {WINDOW})"
      f"   = +{(last-first)*100:.1f}pp from verified outcomes, no model retraining")
print("    (the paper measures +21.96pp on this curve, saturating sub-linearly at c_acc=0.643;")
print("     the super-linear part is the cumulative *advantage*, c=1.387, not the accuracy.)")

# ─────────────────────────────────────────────────────────────────────
# 2) GOVERN — the gate abstained before it had earned the right
# ─────────────────────────────────────────────────────────────────────
print("\n[GOVERN ~ E-JM-4]  the gate grants autonomy per category, only once earned")
print("    (this IS the paper's compounding feedback loop: higher q → more categories")
print("     clear α·q·V ≥ θ_min → autonomous scope widens):")
for c in range(N_CAT):
    status, _ = gate_for(int(seen[c]), int(correct_cat[c]))
    earned = f"earned GREEN at decision {first_green[c]}" if c in first_green else "never earned GREEN"
    print(f"    {CATEGORIES[c]:13s} seen={seen[c]:4d}  abstained={abstained[c]:4d}  "
          f"final={status:5s}  ({earned})")
print("    → the rare category abstains (routes to a human) until volume clears the")
print("      conservation floor θ_min = 23.53/(α·V); autonomy is earned, not assumed.")

# ─────────────────────────────────────────────────────────────────────
# 3) INSPECT — point to the exact centroid cell a decision moved
# ─────────────────────────────────────────────────────────────────────
if watched_cell is not None:
    c, a = watched_cell
    after = scorer.centroids[c, a]
    print(f"\n[INSPECT]  centroid cell  (category='{CATEGORIES[c]}', action='{ACTIONS[a]}')")
    print(f"    before verified outcomes : {np.round(watched_before, 3)}")
    print(f"    after  verified outcomes : {np.round(after, 3)}")
    print(f"    moved by L2 norm         : {float(np.linalg.norm(after - watched_before)):.4f}")
    print("    → every number the engine emits traces to a cell like this. Open it. Audit it. Undo it.")

# ─────────────────────────────────────────────────────────────────────
# Bonus — the trust trap: which factor is most load-bearing (ablation)
# ─────────────────────────────────────────────────────────────────────
holdout = []
for i in range(60):
    c = int(RNG.integers(0, N_CAT)); f, gt = sample_case(c)
    holdout.append(EvaluationScenario(
        scenario_id=f"HO{i}", domain="refund", category=CATEGORIES[c],
        category_index=c, factors=f, expected_action=ACTIONS[gt],
        expected_action_index=gt, description="holdout"))
abl = run_ablation(scorer, holdout, FACTOR_NAMES)
print(f"\n[TRUST TRAP ~ E-JM-2/5]  factor importance (remove it, watch accuracy fall):")
print(f"    most load-bearing : {abl.most_important}")
print(f"    least             : {abl.least_important}")
print("    (the paper: 93.6% of domains hold a trust trap — a factor people trust that")
print("     the data does not; the σ fingerprint surfaces 63% at a 0% false-discovery rate.)")

# ─────────────────────────────────────────────────────────────────────
# 4) REMEMBER — the judgment memory IS the centroid tensor: a tiny file
# ─────────────────────────────────────────────────────────────────────
import os, tempfile
mem = scorer.centroids
with tempfile.TemporaryDirectory() as d:
    path = os.path.join(d, "judgment_memory.npy")
    np.save(path, mem)
    reloaded = np.load(path)
    kb = os.path.getsize(path) / 1024
print(f"\n[REMEMBER] judgment memory = centroid tensor {mem.shape} = {mem.size} floats "
      f"(~{kb:.1f} KB on disk)")
print(f"    saved → reloaded identical: {bool(np.array_equal(reloaded, mem))}  "
      f"— no database, no server. Your firm's judgment is a file you own, read, and version.")

# ─────────────────────────────────────────────────────────────────────
# Optional learning-curve PNG (skipped cleanly if matplotlib absent)
# ─────────────────────────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.figure(figsize=(7, 4))
    plt.plot(curve_x, curve_y, color="#D98A1B", linewidth=2.5, marker="o")
    plt.ylim(0, 1); plt.xlabel("verified decisions"); plt.ylabel("rolling accuracy")
    plt.title("GAE decision-mirror — accuracy compounds from verified outcomes")
    plt.grid(alpha=0.3)
    out = "examples/decision_mirror/learning_curve.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    print(f"\nSaved learning curve → {out}")
except Exception as exc:  # pragma: no cover
    print(f"\n(matplotlib not available, skipped PNG: {exc})")

print("\n=== done ===")
