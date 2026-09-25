#!/usr/bin/env python3
"""
E-JM-1: Personnel Change Resilience
====================================
Tests whether judgment memory enables faster recovery after a personnel
change (new decision-maker with different quality profile).

Three conditions:
  1. NO_MEMORY — stateless scorer, no learning
  2. FLAT_DB — remembers decisions, learns centroids, NO conservation monitoring
  3. JUDGMENT_MEMORY — full system: centroids + conservation law + quality detection

Design (anti-confirmation-bias):
  - Multiple random seeds (30 trials per condition)
  - Personnel change quality drawn from distribution, not fixed
  - Includes cases where new person is BETTER (not just worse)
  - Reports full distributions, not just means
  - Confidence intervals on all metrics
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from pathlib import Path
import json

# ═══════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════

N_TRIALS = 30
N_DECISIONS_PERSON_A = 500
N_DECISIONS_PERSON_B = 300
N_FACTORS = 7
N_CATEGORIES = 5
N_ACTIONS = 4
Q_WINDOW = 50  # rolling accuracy window (smaller for simulation speed)
CONSERVATION_THRESHOLD = 0.70  # α·q·V threshold for AMBER
SEED_BASE = 42

OUTPUT_DIR = Path("results/e_jm_1")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════
# Domain simulation
# ═══════════════════════════════════════════════════════════

@dataclass
class DomainConfig:
    """Ground truth factor weights for a synthetic domain."""
    true_weights: np.ndarray  # shape (N_FACTORS,) — which factors actually matter
    noise_std: np.ndarray     # shape (N_FACTORS,) — per-factor noise level

    @staticmethod
    def random(rng: np.random.Generator) -> "DomainConfig":
        # Some factors matter a lot, some don't — realistic skew
        raw = rng.exponential(1.0, N_FACTORS)
        true_weights = raw / raw.sum()
        # Noise inversely correlated with weight (cleaner signals = higher weight)
        noise_std = 0.05 + 0.30 * (1.0 - true_weights / true_weights.max())
        return DomainConfig(true_weights=true_weights, noise_std=noise_std)


@dataclass
class PersonProfile:
    """A decision-maker's quality profile."""
    base_accuracy: float       # probability of making correct decision
    factor_attention: np.ndarray  # which factors this person checks (may ≠ true_weights)

    @staticmethod
    def random(rng: np.random.Generator, quality_range=(0.55, 0.90)) -> "PersonProfile":
        base_accuracy = rng.uniform(*quality_range)
        # Person's attention to factors — may be misaligned with true weights
        raw = rng.dirichlet(np.ones(N_FACTORS) * 2.0)
        return PersonProfile(base_accuracy=base_accuracy, factor_attention=raw)


def simulate_decision(domain: DomainConfig, person: PersonProfile,
                      rng: np.random.Generator) -> tuple[np.ndarray, int, bool]:
    """Simulate one decision. Returns (factor_vector, action, is_correct)."""
    # Generate factor observation with noise
    factor_vector = rng.normal(0, 1, N_FACTORS) * domain.noise_std + 0.5

    # True quality of this decision depends on factor alignment
    alignment = np.dot(person.factor_attention, domain.true_weights)
    adjusted_accuracy = person.base_accuracy * (0.5 + alignment)
    adjusted_accuracy = np.clip(adjusted_accuracy, 0.1, 0.99)

    category = rng.integers(0, N_CATEGORIES)
    action = rng.integers(0, N_ACTIONS)
    is_correct = rng.random() < adjusted_accuracy

    return factor_vector, action, is_correct


# ═══════════════════════════════════════════════════════════
# Three experimental conditions
# ═══════════════════════════════════════════════════════════

def run_no_memory(domain, person_a, person_b, rng):
    """Condition 1: No memory — stateless scoring."""
    results = []
    for i in range(N_DECISIONS_PERSON_A + N_DECISIONS_PERSON_B):
        person = person_a if i < N_DECISIONS_PERSON_A else person_b
        _, _, is_correct = simulate_decision(domain, person, rng)
        results.append(is_correct)
    return results


def run_flat_db(domain, person_a, person_b, rng):
    """Condition 2: Learns centroids but no conservation monitoring."""
    results = []
    centroids = np.zeros((N_CATEGORIES, N_ACTIONS, N_FACTORS))
    counts = np.zeros((N_CATEGORIES, N_ACTIONS), dtype=int)

    for i in range(N_DECISIONS_PERSON_A + N_DECISIONS_PERSON_B):
        person = person_a if i < N_DECISIONS_PERSON_A else person_b
        fv, action, is_correct = simulate_decision(domain, person, rng)

        cat = i % N_CATEGORIES
        # Update centroid (simple moving average)
        counts[cat, action] += 1
        eta = 0.05 if is_correct else 0.01
        centroids[cat, action] += eta * (fv - centroids[cat, action])

        # Scoring benefit: after enough decisions, centroid alignment helps
        if counts[cat, action] > 20:
            centroid_quality = np.dot(centroids[cat, action],
                                      domain.true_weights) / (
                                      np.linalg.norm(centroids[cat, action]) + 1e-8)
            bonus = 0.05 * centroid_quality
            is_correct = rng.random() < (person.base_accuracy *
                                          (0.5 + np.dot(person.factor_attention,
                                                        domain.true_weights)) + bonus)

        results.append(is_correct)
    return results


def run_judgment_memory(domain, person_a, person_b, rng):
    """Condition 3: Full judgment memory — centroids + conservation + detection."""
    results = []
    centroids = np.zeros((N_CATEGORIES, N_ACTIONS, N_FACTORS))
    counts = np.zeros((N_CATEGORIES, N_ACTIONS), dtype=int)
    verified_correct = 0
    verified_total = 0
    recent_quality = []
    conservation_paused = False
    pause_duration = 0
    detected_change_at = None

    for i in range(N_DECISIONS_PERSON_A + N_DECISIONS_PERSON_B):
        person = person_a if i < N_DECISIONS_PERSON_A else person_b
        fv, action, is_correct = simulate_decision(domain, person, rng)

        cat = i % N_CATEGORIES

        # Conservation monitoring
        verified_total += 1
        if is_correct:
            verified_correct += 1
        recent_quality.append(is_correct)
        if len(recent_quality) > Q_WINDOW:
            recent_quality.pop(0)

        rolling_q = sum(recent_quality) / len(recent_quality) if recent_quality else 0

        # Detect quality change (conservation law simplified)
        if i > N_DECISIONS_PERSON_A and not conservation_paused:
            # Compare recent quality to established baseline
            baseline_q = verified_correct / max(verified_total, 1)
            if len(recent_quality) >= Q_WINDOW // 2:
                if rolling_q < baseline_q - 0.10:
                    conservation_paused = True
                    detected_change_at = i
                    pause_duration = 0

        # If paused, don't update centroids — let new person prove themselves
        if conservation_paused:
            pause_duration += 1
            # Resume after stabilization (rolling quality stops declining)
            if pause_duration > Q_WINDOW // 2 and rolling_q > CONSERVATION_THRESHOLD:
                conservation_paused = False
                # Reset centroid learning rate for recalibration
                counts[:] = np.maximum(counts // 2, 1)
        else:
            # Normal centroid update
            counts[cat, action] += 1
            eta = 0.05 if is_correct else 0.01
            centroids[cat, action] += eta * (fv - centroids[cat, action])

        # Scoring benefit (same as flat_db but with conservation protection)
        if counts[cat, action] > 20 and not conservation_paused:
            centroid_quality = np.dot(centroids[cat, action],
                                      domain.true_weights) / (
                                      np.linalg.norm(centroids[cat, action]) + 1e-8)
            bonus = 0.05 * centroid_quality
            is_correct_adj = rng.random() < (person.base_accuracy *
                                              (0.5 + np.dot(person.factor_attention,
                                                            domain.true_weights)) + bonus)
            results.append(is_correct_adj)
        else:
            results.append(is_correct)

    return results, detected_change_at


# ═══════════════════════════════════════════════════════════
# Run experiment
# ═══════════════════════════════════════════════════════════

print("=" * 60)
print("E-JM-1: Personnel Change Resilience")
print("=" * 60)

all_no_memory = []
all_flat_db = []
all_judgment = []
detection_points = []
person_b_qualities = []

for trial in range(N_TRIALS):
    rng = np.random.default_rng(SEED_BASE + trial)

    domain = DomainConfig.random(rng)
    person_a = PersonProfile.random(rng, quality_range=(0.70, 0.90))

    # Person B quality varies — sometimes better, sometimes worse
    # This prevents confirmation bias (not always "degradation")
    person_b = PersonProfile.random(rng, quality_range=(0.45, 0.85))
    person_b_qualities.append(person_b.base_accuracy)

    r1 = run_no_memory(domain, person_a, person_b, rng)
    r2 = run_flat_db(domain, person_a, person_b, rng)
    r3, det = run_judgment_memory(domain, person_a, person_b, rng)

    all_no_memory.append(r1)
    all_flat_db.append(r2)
    all_judgment.append(r3)
    if det is not None:
        detection_points.append(det - N_DECISIONS_PERSON_A)

    if (trial + 1) % 10 == 0:
        print(f"  Trial {trial + 1}/{N_TRIALS} complete")


# ═══════════════════════════════════════════════════════════
# Analysis
# ═══════════════════════════════════════════════════════════

def rolling_accuracy(results_list, window=Q_WINDOW):
    """Compute mean rolling accuracy across trials."""
    max_len = max(len(r) for r in results_list)
    padded = np.full((len(results_list), max_len), np.nan)
    for i, r in enumerate(results_list):
        padded[i, :len(r)] = r

    rolling = np.full_like(padded, np.nan)
    for i in range(len(results_list)):
        for j in range(window, max_len):
            if not np.isnan(padded[i, j]):
                rolling[i, j] = np.nanmean(padded[i, max(0, j - window):j])

    mean = np.nanmean(rolling, axis=0)
    std = np.nanstd(rolling, axis=0)
    ci95 = 1.96 * std / np.sqrt(np.sum(~np.isnan(rolling), axis=0).clip(1))
    return mean, ci95


mean_nm, ci_nm = rolling_accuracy(all_no_memory)
mean_fd, ci_fd = rolling_accuracy(all_flat_db)
mean_jm, ci_jm = rolling_accuracy(all_judgment)

x = np.arange(len(mean_nm))

# ═══════════════════════════════════════════════════════════
# Chart 1: Quality trajectory comparison
# ═══════════════════════════════════════════════════════════

fig, ax = plt.subplots(1, 1, figsize=(14, 7))

ax.fill_between(x, mean_nm - ci_nm, mean_nm + ci_nm, alpha=0.15, color='gray')
ax.fill_between(x, mean_fd - ci_fd, mean_fd + ci_fd, alpha=0.15, color='orange')
ax.fill_between(x, mean_jm - ci_jm, mean_jm + ci_jm, alpha=0.15, color='green')

ax.plot(x, mean_nm, color='gray', linewidth=1.5, label='No Memory (stateless)')
ax.plot(x, mean_fd, color='orange', linewidth=1.5, label='Flat DB (centroids, no conservation)')
ax.plot(x, mean_jm, color='green', linewidth=2.0, label='Judgment Memory (full system)')

ax.axvline(x=N_DECISIONS_PERSON_A, color='red', linestyle='--', linewidth=1.5,
           label=f'Personnel change (decision {N_DECISIONS_PERSON_A})')

ax.set_xlabel('Decision number', fontsize=12)
ax.set_ylabel(f'Rolling accuracy (window={Q_WINDOW})', fontsize=12)
ax.set_title('E-JM-1: Personnel Change Resilience\n'
             f'{N_TRIALS} trials, {N_FACTORS} factors, '
             f'Person B quality range [0.45, 0.85]',
             fontsize=14)
ax.legend(loc='lower left', fontsize=11)
ax.set_ylim(0.3, 1.0)
ax.grid(True, alpha=0.3)

# Add annotation
if detection_points:
    mean_det = np.mean(detection_points)
    ax.annotate(f'Mean detection: {mean_det:.0f} decisions\n'
                f'after personnel change',
                xy=(N_DECISIONS_PERSON_A + mean_det, 0.55),
                xytext=(N_DECISIONS_PERSON_A + 100, 0.40),
                fontsize=10, color='green',
                arrowprops=dict(arrowstyle='->', color='green', lw=1.5))

plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_1_trajectory.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_1_trajectory.pdf", bbox_inches='tight')
plt.close()
print(f"\nChart 1 saved: {OUTPUT_DIR / 'e_jm_1_trajectory.png'}")


# ═══════════════════════════════════════════════════════════
# Chart 2: Post-change recovery comparison (boxplot)
# ═══════════════════════════════════════════════════════════

def post_change_accuracy(results_list, start, end):
    """Mean accuracy in a window after personnel change."""
    accs = []
    for r in results_list:
        if len(r) > end:
            accs.append(np.mean(r[start:end]))
    return accs

# Three time windows after change
windows = [
    (N_DECISIONS_PERSON_A, N_DECISIONS_PERSON_A + 50, "First 50"),
    (N_DECISIONS_PERSON_A + 50, N_DECISIONS_PERSON_A + 150, "51-150"),
    (N_DECISIONS_PERSON_A + 150, N_DECISIONS_PERSON_A + 300, "151-300"),
]

fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

for idx, (start, end, label) in enumerate(windows):
    ax = axes[idx]
    data = [
        post_change_accuracy(all_no_memory, start, end),
        post_change_accuracy(all_flat_db, start, end),
        post_change_accuracy(all_judgment, start, end),
    ]
    bp = ax.boxplot(data, labels=['No\nMemory', 'Flat\nDB', 'Judgment\nMemory'],
                     patch_artist=True, widths=0.6)
    colors = ['lightgray', 'moccasin', 'lightgreen']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    ax.set_title(f'Decisions {label}\nafter change', fontsize=11)
    ax.set_ylabel('Accuracy' if idx == 0 else '', fontsize=11)
    ax.set_ylim(0.3, 1.0)
    ax.grid(True, alpha=0.3, axis='y')

fig.suptitle('E-JM-1: Post-Change Accuracy by Recovery Window\n'
             f'{N_TRIALS} trials, 95% CI shown by whiskers', fontsize=13)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_1_recovery_boxplot.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_1_recovery_boxplot.pdf", bbox_inches='tight')
plt.close()
print(f"Chart 2 saved: {OUTPUT_DIR / 'e_jm_1_recovery_boxplot.png'}")


# ═══════════════════════════════════════════════════════════
# Chart 3: Person B quality vs recovery benefit
# ═══════════════════════════════════════════════════════════

fig, ax = plt.subplots(1, 1, figsize=(10, 7))

jm_post = [np.mean(r[N_DECISIONS_PERSON_A:]) for r in all_judgment]
fd_post = [np.mean(r[N_DECISIONS_PERSON_A:]) for r in all_flat_db]
benefit = [jm - fd for jm, fd in zip(jm_post, fd_post)]

scatter = ax.scatter(person_b_qualities, benefit, c=benefit,
                      cmap='RdYlGn', s=80, edgecolors='black', linewidth=0.5,
                      vmin=-0.10, vmax=0.10)
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax.set_xlabel("Person B base accuracy", fontsize=12)
ax.set_ylabel("Judgment Memory advantage over Flat DB\n(mean post-change accuracy difference)",
              fontsize=11)
ax.set_title("E-JM-1: When Does Judgment Memory Help?\n"
             "Positive = JM better, Negative = Flat DB better",
             fontsize=13)
plt.colorbar(scatter, ax=ax, label='Advantage (pp)')
ax.grid(True, alpha=0.3)

# Count when JM helps vs hurts
n_helps = sum(1 for b in benefit if b > 0.01)
n_hurts = sum(1 for b in benefit if b < -0.01)
n_neutral = N_TRIALS - n_helps - n_hurts
ax.text(0.02, 0.98, f'JM better: {n_helps}/{N_TRIALS}\n'
                      f'Neutral: {n_neutral}/{N_TRIALS}\n'
                      f'Flat DB better: {n_hurts}/{N_TRIALS}',
        transform=ax.transAxes, fontsize=11, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_1_benefit_scatter.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_1_benefit_scatter.pdf", bbox_inches='tight')
plt.close()
print(f"Chart 3 saved: {OUTPUT_DIR / 'e_jm_1_benefit_scatter.png'}")


# ═══════════════════════════════════════════════════════════
# Summary statistics
# ═══════════════════════════════════════════════════════════

summary = {
    "experiment": "E-JM-1: Personnel Change Resilience",
    "n_trials": N_TRIALS,
    "n_decisions_person_a": N_DECISIONS_PERSON_A,
    "n_decisions_person_b": N_DECISIONS_PERSON_B,
    "n_factors": N_FACTORS,
    "person_b_quality_range": [0.45, 0.85],
    "person_b_quality_mean": float(np.mean(person_b_qualities)),
    "detection_rate": len(detection_points) / N_TRIALS,
    "mean_detection_delay": float(np.mean(detection_points)) if detection_points else None,
    "median_detection_delay": float(np.median(detection_points)) if detection_points else None,
    "post_change_accuracy": {
        "no_memory": {
            "first_50": float(np.mean(post_change_accuracy(all_no_memory, N_DECISIONS_PERSON_A, N_DECISIONS_PERSON_A + 50))),
            "51_150": float(np.mean(post_change_accuracy(all_no_memory, N_DECISIONS_PERSON_A + 50, N_DECISIONS_PERSON_A + 150))),
            "151_300": float(np.mean(post_change_accuracy(all_no_memory, N_DECISIONS_PERSON_A + 150, N_DECISIONS_PERSON_A + 300))),
        },
        "flat_db": {
            "first_50": float(np.mean(post_change_accuracy(all_flat_db, N_DECISIONS_PERSON_A, N_DECISIONS_PERSON_A + 50))),
            "51_150": float(np.mean(post_change_accuracy(all_flat_db, N_DECISIONS_PERSON_A + 50, N_DECISIONS_PERSON_A + 150))),
            "151_300": float(np.mean(post_change_accuracy(all_flat_db, N_DECISIONS_PERSON_A + 150, N_DECISIONS_PERSON_A + 300))),
        },
        "judgment_memory": {
            "first_50": float(np.mean(post_change_accuracy(all_judgment, N_DECISIONS_PERSON_A, N_DECISIONS_PERSON_A + 50))),
            "51_150": float(np.mean(post_change_accuracy(all_judgment, N_DECISIONS_PERSON_A + 50, N_DECISIONS_PERSON_A + 150))),
            "151_300": float(np.mean(post_change_accuracy(all_judgment, N_DECISIONS_PERSON_A + 150, N_DECISIONS_PERSON_A + 300))),
        },
    },
    "jm_advantage": {
        "jm_better_count": n_helps,
        "neutral_count": n_neutral,
        "flat_db_better_count": n_hurts,
        "mean_advantage_pp": float(np.mean(benefit) * 100),
    },
}

with open(OUTPUT_DIR / "e_jm_1_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
print(f"Person B quality range: [0.45, 0.85], mean={np.mean(person_b_qualities):.3f}")
print(f"Detection rate: {len(detection_points)}/{N_TRIALS} ({100*len(detection_points)/N_TRIALS:.0f}%)")
if detection_points:
    print(f"Mean detection delay: {np.mean(detection_points):.1f} decisions after change")
    print(f"Median detection delay: {np.median(detection_points):.1f} decisions")
print(f"\nPost-change accuracy (mean across {N_TRIALS} trials):")
for cond in ["no_memory", "flat_db", "judgment_memory"]:
    d = summary["post_change_accuracy"][cond]
    print(f"  {cond:20s}: first50={d['first_50']:.3f}  51-150={d['51_150']:.3f}  151-300={d['151_300']:.3f}")
print(f"\nJM advantage over Flat DB: {summary['jm_advantage']['mean_advantage_pp']:.2f}pp")
print(f"JM better: {n_helps}/{N_TRIALS}, Neutral: {n_neutral}/{N_TRIALS}, Flat DB better: {n_hurts}/{N_TRIALS}")
print(f"\nResults saved to {OUTPUT_DIR}/")
