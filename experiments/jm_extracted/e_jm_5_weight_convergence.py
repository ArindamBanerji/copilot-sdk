#!/usr/bin/env python3
"""
E-JM-5 v2: Factor Weight Convergence (Redesigned)
====================================================
v1 FLAW: Used signal-to-noise RATIO (correct vs incorrect means)
which requires hundreds of samples per cell. The actual DiagonalKernel
uses INVERSE VARIANCE — weight_k proportional to 1/sigma_k — which
converges faster because it only needs within-outcome variance.

v2 FIXES:
  - Inverse-variance weighting (the actual DK mechanism)
  - Pool across categories for global weight (more samples per factor)
  - Welford's online variance for numerically stable estimates
  - Discriminability bonus (factors that separate correct/incorrect)
  - Three discovery criteria (not just exact top-1)
  - Run to 3000 decisions
  - Track convergence SHAPE (when does rank stabilize?)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path
import json

N_FACTORS = 7
N_DOMAINS = 100
N_DECISIONS = 2000
CHECKPOINTS = [50, 100, 200, 400, 800, 1200, 1600, 2000]
N_TRIALS = 5
SEED = 42
OUTPUT_DIR = Path("results/e_jm_5")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_domain(rng):
    raw = rng.exponential(1.0, N_FACTORS)
    true_weights = raw / raw.sum()
    noise_std = 0.08 + 0.35 * (1.0 - true_weights / true_weights.max())
    intuit_raw = noise_std * rng.uniform(0.7, 1.3, N_FACTORS)
    intuitive_weights = intuit_raw / intuit_raw.sum()
    return true_weights, noise_std, intuitive_weights

class WelfordVariance:
    def __init__(self, n_dims):
        self.n = 0
        self.mean = np.zeros(n_dims)
        self.M2 = np.zeros(n_dims)
    def update(self, x):
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        delta2 = x - self.mean
        self.M2 += delta * delta2
    def variance(self):
        if self.n < 2: return np.ones_like(self.mean)
        return self.M2 / (self.n - 1)
    def std(self):
        return np.sqrt(np.clip(self.variance(), 1e-8, None))

def simulate_dk(true_weights, noise_std, n_decisions, rng):
    confirmed_stats = WelfordVariance(N_FACTORS)
    overridden_stats = WelfordVariance(N_FACTORS)
    all_stats = WelfordVariance(N_FACTORS)
    person_acc = rng.uniform(0.65, 0.85)
    dk_weights = np.ones(N_FACTORS) / N_FACTORS
    weight_history = []

    for i in range(n_decisions):
        fv = rng.normal(0, 1, N_FACTORS) * noise_std + true_weights * 2
        quality = np.dot(fv * true_weights, np.ones(N_FACTORS))
        is_correct = rng.random() < np.clip(
            person_acc * (0.5 + 0.3 * np.tanh(quality)), 0.15, 0.95)

        all_stats.update(fv)
        if is_correct:
            confirmed_stats.update(fv)
        else:
            overridden_stats.update(fv)

        if confirmed_stats.n >= 15 and overridden_stats.n >= 10:
            separation = np.abs(confirmed_stats.mean - overridden_stats.mean)
            pooled_std = np.sqrt(
                (confirmed_stats.variance() + overridden_stats.variance()) / 2 + 1e-6)
            discriminability = separation / pooled_std
            inv_noise = 1.0 / (all_stats.std() + 1e-6)
            combined = discriminability * inv_noise
            dk_weights = combined / (combined.sum() + 1e-8)
        elif all_stats.n >= 20:
            inv_var = 1.0 / (all_stats.variance() + 1e-6)
            dk_weights = inv_var / inv_var.sum()

        if (i + 1) in CHECKPOINTS:
            weight_history.append((i + 1, dk_weights.copy()))

    return dk_weights, weight_history

def measure_convergence(true_w, intuitive_w, learned_w):
    true_rank = np.argsort(true_w)[::-1]
    intuit_rank = np.argsort(intuitive_w)[::-1]
    learned_rank = np.argsort(learned_w)[::-1]
    r_true, _ = stats.spearmanr(np.argsort(true_w), np.argsort(learned_w))
    true_top3 = set(true_rank[:3])
    learned_top3 = set(learned_rank[:3])
    top3_overlap = len(true_top3 & learned_top3) / 3.0
    has_trap = true_rank[0] != intuit_rank[0]
    trap_surfaced = (learned_rank[0] == true_rank[0] and
                     learned_rank[0] != intuit_rank[0] and has_trap)
    cosine = np.dot(learned_w, true_w) / (
        np.linalg.norm(learned_w) * np.linalg.norm(true_w) + 1e-8)
    tau, _ = stats.kendalltau(np.argsort(true_w), np.argsort(learned_w))
    return {"spearman_r": float(r_true), "top3_overlap": float(top3_overlap),
            "trap_surfaced": trap_surfaced, "cosine_similarity": float(cosine),
            "kendall_tau": float(tau), "has_real_trap": has_trap}

print("=" * 60)
print("E-JM-5 v2: Factor Weight Convergence (Inverse Variance)")
print("=" * 60)

rng = np.random.default_rng(SEED)
checkpoint_metrics = {n: {"spearman": [], "top3": [], "trap_surfaced": [],
    "cosine": [], "kendall": []} for n in CHECKPOINTS}
total_with_trap = 0
example_trajectories = []

for domain_idx in range(N_DOMAINS):
    true_w, noise, intuit_w = generate_domain(rng)
    has_trap = np.argsort(true_w)[::-1][0] != np.argsort(intuit_w)[::-1][0]
    if has_trap: total_with_trap += 1

    for trial in range(N_TRIALS):
        trial_rng = np.random.default_rng(SEED + domain_idx * 100 + trial)
        final_w, history = simulate_dk(true_w, noise, N_DECISIONS, trial_rng)
        for n_dec, weights_at_n in history:
            m = measure_convergence(true_w, intuit_w, weights_at_n)
            checkpoint_metrics[n_dec]["spearman"].append(m["spearman_r"])
            checkpoint_metrics[n_dec]["top3"].append(m["top3_overlap"])
            checkpoint_metrics[n_dec]["cosine"].append(m["cosine_similarity"])
            checkpoint_metrics[n_dec]["kendall"].append(m["kendall_tau"])
            checkpoint_metrics[n_dec]["trap_surfaced"].append(m["trap_surfaced"])

    if domain_idx < 5:
        _, history = simulate_dk(true_w, noise, N_DECISIONS, rng)
        example_trajectories.append({"true": true_w, "intuitive": intuit_w, "history": history})

    if (domain_idx + 1) % 50 == 0:
        print(f"  Domain {domain_idx+1}/{N_DOMAINS}")

# === Charts ===
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
for (mk, yl, ax, col) in [
    ("spearman", "Spearman r (learned vs true)", axes[0,0], 'green'),
    ("top3", "Top-3 factor overlap", axes[0,1], 'blue'),
    ("cosine", "Cosine similarity", axes[1,0], 'purple'),
    ("kendall", "Kendall τ", axes[1,1], 'orange'),
]:
    means = [np.mean(checkpoint_metrics[n][mk]) for n in CHECKPOINTS]
    ci = [1.96*np.std(checkpoint_metrics[n][mk])/np.sqrt(len(checkpoint_metrics[n][mk])) for n in CHECKPOINTS]
    p25 = [np.percentile(checkpoint_metrics[n][mk], 25) for n in CHECKPOINTS]
    p75 = [np.percentile(checkpoint_metrics[n][mk], 75) for n in CHECKPOINTS]
    ax.fill_between(CHECKPOINTS, p25, p75, alpha=0.15, color=col, label='IQR')
    ax.errorbar(CHECKPOINTS, means, yerr=ci, marker='o', markersize=6, linewidth=2, capsize=4, color=col, label='Mean±95%CI')
    ax.set_xlabel('Verified decisions', fontsize=10); ax.set_ylabel(yl, fontsize=10)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8); ax.set_xscale('log')
    if mk in ("spearman","kendall"): ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.5)
fig.suptitle(f'E-JM-5 v2: DK Weight Convergence ({N_DOMAINS} domains × {N_TRIALS} trials)', fontsize=14)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_5_convergence.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_5_convergence.pdf", bbox_inches='tight')
plt.close(); print("\nChart 1 saved")

fig, ax = plt.subplots(1, 1, figsize=(12, 7))
disc = [np.mean(checkpoint_metrics[n]["trap_surfaced"])*100 for n in CHECKPOINTS]
ax.plot(CHECKPOINTS, disc, 'o-', markersize=10, linewidth=2.5, color='green', label='Discovery rate')
ax.axhline(y=93.6, color='red', linestyle=':', linewidth=1, label='Trap prevalence (E-JM-2)', alpha=0.7)
ax.set_xlabel('Verified decisions', fontsize=12); ax.set_ylabel('Discovery rate (%)', fontsize=12)
ax.set_title('E-JM-5 v2: Trust Trap Discovery Over Time', fontsize=14)
ax.legend(fontsize=11); ax.set_ylim(0, 100); ax.set_xscale('log'); ax.grid(True, alpha=0.3)
for i, n in enumerate(CHECKPOINTS):
    if disc[i] > 2: ax.annotate(f'{disc[i]:.0f}%', xy=(n, disc[i]), xytext=(0,12), textcoords='offset points', ha='center', fontsize=9, fontweight='bold', color='green')
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_5_discovery_rate.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_5_discovery_rate.pdf", bbox_inches='tight')
plt.close(); print("Chart 2 saved")

fig, axes = plt.subplots(1, min(3, len(example_trajectories)), figsize=(18, 6))
if not isinstance(axes, np.ndarray): axes = [axes]
for ex_idx in range(min(3, len(example_trajectories))):
    ax = axes[ex_idx]; ex = example_trajectories[ex_idx]
    for f in range(N_FACTORS):
        steps = [h[0] for h in ex["history"]]; vals = [h[1][f] for h in ex["history"]]
        ax.plot(steps, vals, '-', linewidth=1.5, alpha=0.7)
        ax.axhline(y=ex["true"][f], color=f'C{f}', linestyle=':', linewidth=0.8, alpha=0.3)
    ax.set_xlabel('Decisions'); ax.set_title(f'Domain {ex_idx+1}'); ax.grid(True, alpha=0.2)
fig.suptitle('E-JM-5 v2: Weight Trajectories (solid=learned, dotted=true)', fontsize=13)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_5_trajectories.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_5_trajectories.pdf", bbox_inches='tight')
plt.close(); print("Chart 3 saved")

summary = {"experiment": "E-JM-5 v2", "mechanism": "inverse_variance+discriminability",
    "n_domains": N_DOMAINS, "n_trials": N_TRIALS, "domains_with_trap": total_with_trap, "results": {}}
print(f"\n{'='*60}\nSUMMARY ({N_DOMAINS} domains, {total_with_trap} with trap)\n{'='*60}")
for n in CHECKPOINTS:
    d = checkpoint_metrics[n]
    r = {"spearman": float(np.mean(d["spearman"])), "top3": float(np.mean(d["top3"])),
         "cosine": float(np.mean(d["cosine"])), "kendall": float(np.mean(d["kendall"])),
         "trap_pct": float(np.mean(d["trap_surfaced"])*100)}
    summary["results"][str(n)] = r
    print(f"{n:>5d}: spearman={r['spearman']:+.3f} top3={r['top3']:.2f} cosine={r['cosine']:.3f} trap={r['trap_pct']:.1f}%")
with open(OUTPUT_DIR / "e_jm_5_summary.json", "w") as f: json.dump(summary, f, indent=2)
print(f"\nResults saved to {OUTPUT_DIR}/")
