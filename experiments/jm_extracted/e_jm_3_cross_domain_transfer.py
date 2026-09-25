#!/usr/bin/env python3
"""
E-JM-3: Cross-Domain Transfer
================================
Tests whether judgment memory learned in one domain accelerates
learning in a related domain (warm-start vs cold-start).

Design:
  - Domain A learns for 500 decisions (builds centroid geometry)
  - Domain B is "related" — shares some factor structure but not all
  - Three conditions:
    1. COLD_START — Domain B starts from scratch
    2. WARM_START — Domain B starts with Domain A's centroids (full transfer)
    3. PARTIAL_TRANSFER — Domain B starts with Domain A's centroids but
       with a transfer discount (warm_start × 0.5)
  - Measure: decisions to reach 80% of Domain A's final quality

Anti-confirmation-bias:
  - Domain similarity varies (0.0 = unrelated, 1.0 = identical)
  - Includes cases where transfer HURTS (negative transfer)
  - Multiple trials per similarity level
  - Reports when warm-start is worse than cold-start
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import json

# ═══════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════

N_FACTORS = 7
N_CATEGORIES = 5
N_ACTIONS = 4
N_DECISIONS_SOURCE = 500
N_DECISIONS_TARGET = 400
N_TRIALS_PER_SIMILARITY = 20
SIMILARITY_LEVELS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
QUALITY_THRESHOLD = 0.80  # target quality fraction of source final
Q_WINDOW = 30
SEED_BASE = 42
OUTPUT_DIR = Path("results/e_jm_3")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════
# Domain generation with controllable similarity
# ═══════════════════════════════════════════════════════════

def generate_domain_pair(rng, similarity):
    """Generate two domains with controllable similarity.
    similarity=1.0: identical factor weights
    similarity=0.0: completely independent
    """
    # Source domain
    raw_a = rng.exponential(1.0, N_FACTORS)
    weights_a = raw_a / raw_a.sum()
    noise_a = 0.05 + 0.25 * (1.0 - weights_a / weights_a.max())

    # Target domain — mix of source and independent
    raw_b_independent = rng.exponential(1.0, N_FACTORS)
    raw_b = similarity * raw_a + (1 - similarity) * raw_b_independent
    weights_b = raw_b / raw_b.sum()
    noise_b = 0.05 + 0.25 * (1.0 - weights_b / weights_b.max())

    return (weights_a, noise_a), (weights_b, noise_b)


def simulate_learning(weights, noise, n_decisions, rng,
                       initial_centroids=None, transfer_discount=1.0):
    """Simulate centroid learning over n_decisions.
    Returns rolling accuracy trajectory.
    """
    centroids = np.zeros((N_CATEGORIES, N_ACTIONS, N_FACTORS))
    counts = np.zeros((N_CATEGORIES, N_ACTIONS), dtype=int)

    if initial_centroids is not None:
        centroids = initial_centroids.copy() * transfer_discount
        counts[:] = max(1, int(20 * transfer_discount))

    results = []
    person_accuracy = rng.uniform(0.65, 0.85)

    for i in range(n_decisions):
        cat = i % N_CATEGORIES
        action = rng.integers(0, N_ACTIONS)

        # Factor observation
        fv = rng.normal(0, 1, N_FACTORS) * noise + 0.5

        # Quality depends on centroid alignment with true weights
        if counts[cat, action] > 10:
            centroid_alignment = np.dot(
                centroids[cat, action] / (np.linalg.norm(centroids[cat, action]) + 1e-8),
                weights
            )
            adjusted_acc = person_accuracy * (0.6 + 0.4 * max(0, centroid_alignment))
        else:
            adjusted_acc = person_accuracy * 0.6  # baseline without centroid help

        adjusted_acc = np.clip(adjusted_acc, 0.1, 0.95)
        is_correct = rng.random() < adjusted_acc

        # Update centroid
        counts[cat, action] += 1
        eta = 0.05 if is_correct else 0.01
        centroids[cat, action] += eta * (fv - centroids[cat, action])

        results.append(is_correct)

    return results, centroids


# ═══════════════════════════════════════════════════════════
# Run experiment
# ═══════════════════════════════════════════════════════════

print("=" * 60)
print("E-JM-3: Cross-Domain Transfer")
print("=" * 60)

all_results = {sim: {"cold": [], "warm": [], "partial": []} for sim in SIMILARITY_LEVELS}
convergence_decisions = {sim: {"cold": [], "warm": [], "partial": []} for sim in SIMILARITY_LEVELS}

for sim in SIMILARITY_LEVELS:
    for trial in range(N_TRIALS_PER_SIMILARITY):
        rng = np.random.default_rng(SEED_BASE + int(sim * 1000) + trial)

        (w_a, n_a), (w_b, n_b) = generate_domain_pair(rng, sim)

        # Source domain learning
        source_results, source_centroids = simulate_learning(
            w_a, n_a, N_DECISIONS_SOURCE, rng
        )
        source_final_q = np.mean(source_results[-Q_WINDOW:])
        target_q = source_final_q * QUALITY_THRESHOLD

        # Condition 1: Cold start
        cold_results, _ = simulate_learning(w_b, n_b, N_DECISIONS_TARGET, rng)

        # Condition 2: Warm start (full transfer)
        warm_results, _ = simulate_learning(
            w_b, n_b, N_DECISIONS_TARGET, rng,
            initial_centroids=source_centroids, transfer_discount=1.0
        )

        # Condition 3: Partial transfer (discounted)
        partial_results, _ = simulate_learning(
            w_b, n_b, N_DECISIONS_TARGET, rng,
            initial_centroids=source_centroids, transfer_discount=0.5
        )

        all_results[sim]["cold"].append(cold_results)
        all_results[sim]["warm"].append(warm_results)
        all_results[sim]["partial"].append(partial_results)

        # Find convergence point (first window where rolling q ≥ target)
        for cond_name, cond_results in [("cold", cold_results),
                                          ("warm", warm_results),
                                          ("partial", partial_results)]:
            converged_at = N_DECISIONS_TARGET  # default: never
            for j in range(Q_WINDOW, len(cond_results)):
                rolling = np.mean(cond_results[j - Q_WINDOW:j])
                if rolling >= target_q:
                    converged_at = j
                    break
            convergence_decisions[sim][cond_name].append(converged_at)

    print(f"  Similarity {sim:.1f} complete ({N_TRIALS_PER_SIMILARITY} trials)")


# ═══════════════════════════════════════════════════════════
# Analysis
# ═══════════════════════════════════════════════════════════

def mean_rolling(results_list, window=Q_WINDOW):
    """Mean rolling accuracy across trials."""
    max_len = max(len(r) for r in results_list)
    arr = np.full((len(results_list), max_len), np.nan)
    for i, r in enumerate(results_list):
        arr[i, :len(r)] = r
    rolling = np.full_like(arr, np.nan)
    for i in range(len(results_list)):
        for j in range(window, max_len):
            rolling[i, j] = np.nanmean(arr[i, max(0, j - window):j])
    return np.nanmean(rolling, axis=0), np.nanstd(rolling, axis=0)


# ═══════════════════════════════════════════════════════════
# Chart 1: Convergence trajectory by similarity level
# ═══════════════════════════════════════════════════════════

fig, axes = plt.subplots(2, 3, figsize=(18, 10), sharey=True)
axes_flat = axes.flatten()

for idx, sim in enumerate(SIMILARITY_LEVELS):
    ax = axes_flat[idx]
    x = np.arange(N_DECISIONS_TARGET)

    for cond, color, label in [
        ("cold", "gray", "Cold start"),
        ("partial", "orange", "Partial transfer (0.5×)"),
        ("warm", "green", "Warm start (full)"),
    ]:
        mean, std = mean_rolling(all_results[sim][cond])
        ci = 1.96 * std / np.sqrt(N_TRIALS_PER_SIMILARITY)
        ax.fill_between(x, mean - ci, mean + ci, alpha=0.12, color=color)
        ax.plot(x, mean, color=color, linewidth=1.5, label=label)

    ax.set_title(f'Similarity = {sim:.1f}', fontsize=12)
    ax.set_xlabel('Decision' if idx >= 3 else '', fontsize=10)
    ax.set_ylabel('Rolling accuracy' if idx % 3 == 0 else '', fontsize=10)
    ax.set_ylim(0.35, 0.90)
    ax.grid(True, alpha=0.3)
    if idx == 0:
        ax.legend(fontsize=8, loc='lower right')

fig.suptitle('E-JM-3: Cross-Domain Transfer — Learning Curves by Similarity\n'
             f'{N_TRIALS_PER_SIMILARITY} trials per level, {N_FACTORS} factors, '
             f'source trained on {N_DECISIONS_SOURCE} decisions',
             fontsize=14)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_3_trajectories.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_3_trajectories.pdf", bbox_inches='tight')
plt.close()
print(f"\nChart 1 saved: {OUTPUT_DIR / 'e_jm_3_trajectories.png'}")


# ═══════════════════════════════════════════════════════════
# Chart 2: Convergence speed vs similarity
# ═══════════════════════════════════════════════════════════

fig, ax = plt.subplots(1, 1, figsize=(12, 7))

for cond, color, marker, label in [
    ("cold", "gray", "s", "Cold start"),
    ("partial", "orange", "^", "Partial transfer (0.5×)"),
    ("warm", "green", "o", "Warm start (full)"),
]:
    means = [np.mean(convergence_decisions[sim][cond]) for sim in SIMILARITY_LEVELS]
    stds = [np.std(convergence_decisions[sim][cond]) for sim in SIMILARITY_LEVELS]
    ci95 = [1.96 * s / np.sqrt(N_TRIALS_PER_SIMILARITY) for s in stds]

    ax.errorbar(SIMILARITY_LEVELS, means, yerr=ci95,
                marker=marker, markersize=10, linewidth=2, capsize=5,
                color=color, label=label)

ax.set_xlabel('Domain similarity (0=unrelated, 1=identical)', fontsize=12)
ax.set_ylabel(f'Decisions to reach {QUALITY_THRESHOLD*100:.0f}% of source quality',
              fontsize=12)
ax.set_title('E-JM-3: Transfer Benefit vs Domain Similarity\n'
             'Lower = faster convergence. Error bars = 95% CI.',
             fontsize=14)
ax.legend(fontsize=11)
ax.set_ylim(0, N_DECISIONS_TARGET + 50)
ax.grid(True, alpha=0.3)

# Add negative transfer annotation
warm_0 = np.mean(convergence_decisions[0.0]["warm"])
cold_0 = np.mean(convergence_decisions[0.0]["cold"])
if warm_0 > cold_0:
    ax.annotate('Negative transfer!\nWarm start slower than cold',
                xy=(0.0, warm_0), xytext=(0.15, warm_0 + 40),
                fontsize=10, color='red',
                arrowprops=dict(arrowstyle='->', color='red'))

plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_3_convergence_speed.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_3_convergence_speed.pdf", bbox_inches='tight')
plt.close()
print(f"Chart 2 saved: {OUTPUT_DIR / 'e_jm_3_convergence_speed.png'}")


# ═══════════════════════════════════════════════════════════
# Chart 3: Negative transfer detection
# ═══════════════════════════════════════════════════════════

fig, ax = plt.subplots(1, 1, figsize=(12, 7))

negative_transfer_rates = []
speedup_ratios = []

for sim in SIMILARITY_LEVELS:
    cold_conv = convergence_decisions[sim]["cold"]
    warm_conv = convergence_decisions[sim]["warm"]

    neg_count = sum(1 for c, w in zip(cold_conv, warm_conv) if w > c)
    neg_rate = neg_count / N_TRIALS_PER_SIMILARITY * 100
    negative_transfer_rates.append(neg_rate)

    # Speedup ratio: cold/warm (>1 = warm faster, <1 = warm slower)
    ratios = [c / max(w, 1) for c, w in zip(cold_conv, warm_conv)]
    speedup_ratios.append(ratios)

# Negative transfer rate bars
ax.bar(SIMILARITY_LEVELS, negative_transfer_rates, width=0.12,
       color='#EF5350', edgecolor='black', linewidth=0.5, alpha=0.8)
ax.set_xlabel('Domain similarity', fontsize=12)
ax.set_ylabel('Negative transfer rate (%)', fontsize=12)
ax.set_title('E-JM-3: When Does Transfer HURT?\n'
             '% of trials where warm-start converges slower than cold-start',
             fontsize=14)
ax.set_ylim(0, 100)
ax.grid(True, alpha=0.3, axis='y')

# Value labels
for i, (sim, rate) in enumerate(zip(SIMILARITY_LEVELS, negative_transfer_rates)):
    ax.text(sim, rate + 2, f'{rate:.0f}%', ha='center', fontsize=11, fontweight='bold')

plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_3_negative_transfer.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_3_negative_transfer.pdf", bbox_inches='tight')
plt.close()
print(f"Chart 3 saved: {OUTPUT_DIR / 'e_jm_3_negative_transfer.png'}")


# ═══════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════

summary = {
    "experiment": "E-JM-3: Cross-Domain Transfer",
    "n_factors": N_FACTORS,
    "n_decisions_source": N_DECISIONS_SOURCE,
    "n_decisions_target": N_DECISIONS_TARGET,
    "n_trials_per_similarity": N_TRIALS_PER_SIMILARITY,
    "quality_threshold": QUALITY_THRESHOLD,
    "results_by_similarity": {},
}

print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")

for sim in SIMILARITY_LEVELS:
    cold_mean = np.mean(convergence_decisions[sim]["cold"])
    warm_mean = np.mean(convergence_decisions[sim]["warm"])
    partial_mean = np.mean(convergence_decisions[sim]["partial"])
    speedup = cold_mean / max(warm_mean, 1)
    neg_rate = negative_transfer_rates[SIMILARITY_LEVELS.index(sim)]

    summary["results_by_similarity"][str(sim)] = {
        "cold_convergence_mean": float(cold_mean),
        "warm_convergence_mean": float(warm_mean),
        "partial_convergence_mean": float(partial_mean),
        "speedup_ratio": float(speedup),
        "negative_transfer_rate_pct": float(neg_rate),
    }

    print(f"\nSimilarity {sim:.1f}:")
    print(f"  Cold: {cold_mean:.0f} decisions  Warm: {warm_mean:.0f}  "
          f"Speedup: {speedup:.2f}×  Negative transfer: {neg_rate:.0f}%")

with open(OUTPUT_DIR / "e_jm_3_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print(f"\nResults saved to {OUTPUT_DIR}/")
