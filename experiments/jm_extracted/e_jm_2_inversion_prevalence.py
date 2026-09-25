#!/usr/bin/env python3
"""
E-JM-2: Signal-Confidence Inversion Prevalence
================================================
Tests how common the "trust trap" is — how often do decision-makers
prioritize factors that are actually the WORST predictors?

Design:
  - Generate 500 synthetic domains with 7 factors each
  - For each domain: assign true weights (outcome-predictive) and
    intuitive weights (what humans check first)
  - Measure: in how many domains is the #1 intuitive factor NOT the
    #1 true factor?
  - Also: how often is the #1 intuitive factor in the BOTTOM HALF
    of true weights? (the full trust trap)

Anti-confirmation-bias:
  - Intuitive weights are drawn from a plausible model of human
    attention (recency, visibility, familiarity), not from a model
    designed to produce inversions
  - Multiple attention models tested (not just worst-case)
  - Reports full distribution of inversion severity
  - Includes a control where intuitive = true (perfect calibration)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path
import json

# ═══════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════

N_DOMAINS = 500
N_FACTORS = 7
N_DECISIONS_PER_DOMAIN = 800  # to compute empirical weights
SEED = 42
OUTPUT_DIR = Path("results/e_jm_2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════
# Human attention models (how people intuitively weight factors)
# ═══════════════════════════════════════════════════════════

def attention_random(true_weights, rng):
    """Random attention — no systematic bias, just noise."""
    raw = rng.dirichlet(np.ones(N_FACTORS) * 2.0)
    return raw

def attention_inverse_noise(true_weights, rng):
    """Humans attend to NOISIER signals (more salient, more variable)."""
    # Noisy factors attract attention because they seem "important"
    noise_level = 0.05 + 0.30 * (1.0 - true_weights / true_weights.max())
    attention = noise_level / noise_level.sum()
    # Add some randomness
    attention = attention * rng.uniform(0.5, 1.5, N_FACTORS)
    return attention / attention.sum()

def attention_recency(true_weights, rng):
    """Humans attend to whatever changed recently."""
    # Random "recency" weighting — uncorrelated with true weights
    recency = rng.exponential(1.0, N_FACTORS)
    return recency / recency.sum()

def attention_familiarity(true_weights, rng):
    """Humans attend to factors they understand (named, visible)."""
    # Some factors are "price" (familiar) vs "supplier OTIF pattern" (unfamiliar)
    # Familiarity partially correlates with true importance but not perfectly
    familiarity = true_weights * rng.uniform(0.3, 1.7, N_FACTORS)
    # Add strong bias toward first 2-3 factors (the "obvious" ones)
    familiarity[:3] *= rng.uniform(1.5, 3.0, 3)
    return familiarity / familiarity.sum()

def attention_perfect(true_weights, rng):
    """Control: perfect calibration (intuitive = true)."""
    return true_weights.copy()

ATTENTION_MODELS = {
    "Random": attention_random,
    "Noise-attracted": attention_inverse_noise,
    "Recency-biased": attention_recency,
    "Familiarity-biased": attention_familiarity,
    "Perfect (control)": attention_perfect,
}


# ═══════════════════════════════════════════════════════════
# Domain generation and inversion detection
# ═══════════════════════════════════════════════════════════

def generate_domain(rng):
    """Generate a synthetic domain with true factor weights."""
    raw = rng.exponential(1.0, N_FACTORS)
    true_weights = raw / raw.sum()
    noise_std = 0.05 + 0.30 * (1.0 - true_weights / true_weights.max())
    return true_weights, noise_std


def detect_inversions(true_weights, intuitive_weights):
    """Detect various types of signal-confidence inversion."""
    true_rank = np.argsort(true_weights)[::-1]  # best first
    intuit_rank = np.argsort(intuitive_weights)[::-1]

    # Type 1: Top intuitive factor is not top true factor
    top1_mismatch = true_rank[0] != intuit_rank[0]

    # Type 2: Top intuitive factor is in bottom half of true ranking
    top_intuit_true_rank = np.where(true_rank == intuit_rank[0])[0][0]
    top_in_bottom_half = top_intuit_true_rank >= N_FACTORS // 2

    # Type 3: Full inversion — top intuitive is bottom true
    full_inversion = top_intuit_true_rank == N_FACTORS - 1

    # Type 4: Rank correlation (Spearman)
    spearman_r, spearman_p = stats.spearmanr(
        np.argsort(true_weights)[::-1],
        np.argsort(intuitive_weights)[::-1]
    )

    # Type 5: Inversion severity — how much weight is on wrong factors
    # Weight-rank displacement
    displacement = 0
    for i in range(N_FACTORS):
        true_pos = np.where(true_rank == i)[0][0]
        intuit_pos = np.where(intuit_rank == i)[0][0]
        displacement += abs(true_pos - intuit_pos) * true_weights[i]

    return {
        "top1_mismatch": top1_mismatch,
        "top_in_bottom_half": top_in_bottom_half,
        "full_inversion": full_inversion,
        "spearman_r": spearman_r,
        "spearman_p": spearman_p,
        "displacement": displacement,
        "top_intuit_true_rank": top_intuit_true_rank,
        "true_weight_of_top_intuitive": true_weights[intuit_rank[0]],
        "true_weight_of_top_true": true_weights[true_rank[0]],
    }


# ═══════════════════════════════════════════════════════════
# Run experiment
# ═══════════════════════════════════════════════════════════

print("=" * 60)
print("E-JM-2: Signal-Confidence Inversion Prevalence")
print("=" * 60)

rng = np.random.default_rng(SEED)
results = {model_name: [] for model_name in ATTENTION_MODELS}

for domain_idx in range(N_DOMAINS):
    true_weights, noise_std = generate_domain(rng)

    for model_name, model_fn in ATTENTION_MODELS.items():
        intuitive = model_fn(true_weights, rng)
        inv = detect_inversions(true_weights, intuitive)
        results[model_name].append(inv)

    if (domain_idx + 1) % 100 == 0:
        print(f"  Domain {domain_idx + 1}/{N_DOMAINS} complete")


# ═══════════════════════════════════════════════════════════
# Analysis
# ═══════════════════════════════════════════════════════════

print(f"\n{'='*60}")
print("RESULTS")
print(f"{'='*60}")

summary_data = {}
for model_name, inv_list in results.items():
    n = len(inv_list)
    top1 = sum(1 for r in inv_list if r["top1_mismatch"]) / n * 100
    bottom = sum(1 for r in inv_list if r["top_in_bottom_half"]) / n * 100
    full = sum(1 for r in inv_list if r["full_inversion"]) / n * 100
    mean_spearman = np.mean([r["spearman_r"] for r in inv_list])
    mean_disp = np.mean([r["displacement"] for r in inv_list])

    summary_data[model_name] = {
        "top1_mismatch_pct": top1,
        "top_in_bottom_half_pct": bottom,
        "full_inversion_pct": full,
        "mean_spearman_r": float(mean_spearman),
        "mean_displacement": float(mean_disp),
    }

    print(f"\n{model_name}:")
    print(f"  Top-1 mismatch:     {top1:5.1f}%")
    print(f"  Top in bottom half: {bottom:5.1f}% (the trust trap)")
    print(f"  Full inversion:     {full:5.1f}%")
    print(f"  Mean Spearman r:    {mean_spearman:+.3f}")
    print(f"  Mean displacement:  {mean_disp:.3f}")


# ═══════════════════════════════════════════════════════════
# Chart 1: Inversion rates by attention model
# ═══════════════════════════════════════════════════════════

fig, ax = plt.subplots(1, 1, figsize=(12, 7))

models = list(summary_data.keys())
x = np.arange(len(models))
width = 0.25

top1_vals = [summary_data[m]["top1_mismatch_pct"] for m in models]
bottom_vals = [summary_data[m]["top_in_bottom_half_pct"] for m in models]
full_vals = [summary_data[m]["full_inversion_pct"] for m in models]

bars1 = ax.bar(x - width, top1_vals, width, label='Top-1 mismatch', color='#FFB74D', edgecolor='black', linewidth=0.5)
bars2 = ax.bar(x, bottom_vals, width, label='Top in bottom half (trust trap)', color='#EF5350', edgecolor='black', linewidth=0.5)
bars3 = ax.bar(x + width, full_vals, width, label='Full inversion (worst→best)', color='#B71C1C', edgecolor='black', linewidth=0.5)

ax.set_xlabel('Human attention model', fontsize=12)
ax.set_ylabel('Prevalence (%)', fontsize=12)
ax.set_title(f'E-JM-2: Signal-Confidence Inversion Prevalence\n'
             f'{N_DOMAINS} synthetic domains × {N_FACTORS} factors',
             fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(models, rotation=15, ha='right', fontsize=10)
ax.legend(fontsize=10)
ax.set_ylim(0, 100)
ax.grid(True, alpha=0.3, axis='y')

# Add value labels
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        if height > 2:
            ax.annotate(f'{height:.0f}%', xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points", ha='center', fontsize=8)

plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_2_inversion_rates.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_2_inversion_rates.pdf", bbox_inches='tight')
plt.close()
print(f"\nChart 1 saved: {OUTPUT_DIR / 'e_jm_2_inversion_rates.png'}")


# ═══════════════════════════════════════════════════════════
# Chart 2: Distribution of Spearman correlations
# ═══════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, len(ATTENTION_MODELS), figsize=(18, 5), sharey=True)

for idx, (model_name, inv_list) in enumerate(results.items()):
    ax = axes[idx]
    spearman_vals = [r["spearman_r"] for r in inv_list]
    ax.hist(spearman_vals, bins=30, color=['lightgray', 'moccasin', 'lightyellow',
                                           'lightyellow', 'lightgreen'][idx],
            edgecolor='black', linewidth=0.5, alpha=0.8)
    ax.axvline(x=0, color='red', linestyle='--', linewidth=1)
    ax.axvline(x=np.mean(spearman_vals), color='blue', linestyle='-', linewidth=1.5,
               label=f'Mean={np.mean(spearman_vals):.2f}')
    ax.set_title(model_name, fontsize=10)
    ax.set_xlabel("Spearman r" if idx == 2 else "", fontsize=10)
    ax.set_ylabel("Count" if idx == 0 else "", fontsize=10)
    ax.legend(fontsize=8)

fig.suptitle('E-JM-2: Spearman Rank Correlation Between Intuitive and True Factor Rankings\n'
             'r < 0 = inverted priorities (trust trap), r = 0 = random, r = 1 = perfect',
             fontsize=12)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_2_spearman_dist.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_2_spearman_dist.pdf", bbox_inches='tight')
plt.close()
print(f"Chart 2 saved: {OUTPUT_DIR / 'e_jm_2_spearman_dist.png'}")


# ═══════════════════════════════════════════════════════════
# Chart 3: Trust trap radar — most inverted domain example
# ═══════════════════════════════════════════════════════════

# Find the most inverted domain under "Noise-attracted" model
noise_results = results["Noise-attracted"]
worst_idx = max(range(len(noise_results)),
                key=lambda i: noise_results[i]["displacement"])

# Regenerate that domain
rng2 = np.random.default_rng(SEED)
for i in range(worst_idx + 1):
    tw, ns = generate_domain(rng2)
    if i == worst_idx:
        true_w = tw
        intuit_w = attention_inverse_noise(tw, rng2)

factor_labels = [f'F{i+1}' for i in range(N_FACTORS)]

# Radar chart
angles = np.linspace(0, 2 * np.pi, N_FACTORS, endpoint=False).tolist()
angles += angles[:1]
true_plot = (true_w / true_w.max()).tolist() + [(true_w / true_w.max())[0]]
intuit_plot = (intuit_w / intuit_w.max()).tolist() + [(intuit_w / intuit_w.max())[0]]

fig, ax = plt.subplots(1, 1, figsize=(8, 8), subplot_kw=dict(polar=True))
ax.plot(angles, true_plot, 'o-', linewidth=2, color='green', label='Actual importance')
ax.fill(angles, true_plot, alpha=0.15, color='green')
ax.plot(angles, intuit_plot, 'o-', linewidth=2, color='red', label='Intuitive attention')
ax.fill(angles, intuit_plot, alpha=0.15, color='red')
ax.set_xticks(angles[:-1])
ax.set_xticklabels(factor_labels, fontsize=11)
ax.set_title('E-JM-2: Most Inverted Domain (Noise-Attracted Model)\n'
             'Red shape (intuitive) should match green shape (actual).\n'
             'Inversion = the shapes are flipped.',
             fontsize=12, pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)

plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_2_radar_worst_case.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_2_radar_worst_case.pdf", bbox_inches='tight')
plt.close()
print(f"Chart 3 saved: {OUTPUT_DIR / 'e_jm_2_radar_worst_case.png'}")


# ═══════════════════════════════════════════════════════════
# Save summary
# ═══════════════════════════════════════════════════════════

full_summary = {
    "experiment": "E-JM-2: Signal-Confidence Inversion Prevalence",
    "n_domains": N_DOMAINS,
    "n_factors": N_FACTORS,
    "seed": SEED,
    "results_by_model": summary_data,
    "interpretation": {
        "top1_mismatch": "% of domains where the #1 intuitive factor is not the #1 true factor",
        "top_in_bottom_half": "% of domains where the #1 intuitive factor is in the bottom half of true ranking — this IS the trust trap",
        "full_inversion": "% of domains where the #1 intuitive factor is the WORST true factor",
        "spearman_r": "Rank correlation between intuitive and true. r<0 = systematically inverted",
    },
}

with open(OUTPUT_DIR / "e_jm_2_summary.json", "w") as f:
    json.dump(full_summary, f, indent=2)

print(f"\nSummary saved: {OUTPUT_DIR / 'e_jm_2_summary.json'}")
print(f"\nAll results in {OUTPUT_DIR}/")
