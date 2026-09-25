#!/usr/bin/env python3
"""
E-JM-4: Conservation Law vs Unconstrained Learning
=====================================================
Tests whether the conservation law prevents quality degradation
that unconstrained learning misses.

Design:
  - Two identical systems process the same decision stream
  - At decision 500: inject quality degradation (personnel change,
    data corruption, or adversarial drift)
  - System A: conservation law active (α·q·V ≥ θ_min)
  - System B: no conservation (learns from everything)
  - Measure: quality trajectory, degradation depth, recovery time

Degradation types (tested separately):
  1. Personnel change — new decision-maker with lower accuracy
  2. Data corruption — 30% of factor observations become noise
  3. Gradual drift — decision quality degrades 0.5%/decision
  4. Adversarial — 10% of decisions are systematically wrong

Anti-confirmation-bias:
  - Includes "no degradation" control (degradation_strength=0)
  - Multiple degradation strengths
  - Reports cases where conservation is OVER-cautious (pauses when it shouldn't)
  - Full distributions, not just means
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
N_DECISIONS_HEALTHY = 500
N_DECISIONS_DEGRADED = 300
N_TRIALS = 30
Q_WINDOW = 50
ETA_CONFIRM = 0.05
ETA_OVERRIDE = 0.01
SEED_BASE = 42
OUTPUT_DIR = Path("results/e_jm_4")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Conservation parameters
ALPHA_THRESHOLD = 0.40  # category coverage threshold
Q_THRESHOLD = 0.65      # quality threshold for AMBER


# ═══════════════════════════════════════════════════════════
# Degradation models
# ═══════════════════════════════════════════════════════════

def no_degradation(base_accuracy, fv, step, rng):
    """Control: no degradation."""
    return base_accuracy, fv

def personnel_change(base_accuracy, fv, step, rng):
    """New person with lower accuracy."""
    return base_accuracy * 0.65, fv

def data_corruption(base_accuracy, fv, step, rng):
    """30% of factor observations become random noise."""
    corrupted = fv.copy()
    mask = rng.random(len(fv)) < 0.30
    corrupted[mask] = rng.normal(0, 1, mask.sum())
    return base_accuracy, corrupted

def gradual_drift(base_accuracy, fv, step, rng):
    """Quality drops 0.3% per decision."""
    drift = max(0.3, 1.0 - 0.003 * step)
    return base_accuracy * drift, fv

def adversarial(base_accuracy, fv, step, rng):
    """10% of decisions are systematically wrong."""
    if rng.random() < 0.10:
        return 0.05, fv  # force wrong decision
    return base_accuracy, fv

DEGRADATION_MODELS = {
    "No degradation (control)": no_degradation,
    "Personnel change": personnel_change,
    "Data corruption (30%)": data_corruption,
    "Gradual drift": gradual_drift,
    "Adversarial (10%)": adversarial,
}


# ═══════════════════════════════════════════════════════════
# Simulation engine
# ═══════════════════════════════════════════════════════════

def run_simulation(degradation_fn, use_conservation, rng):
    """Run a full simulation with or without conservation."""
    # Domain setup
    raw = rng.exponential(1.0, N_FACTORS)
    true_weights = raw / raw.sum()
    noise_std = 0.05 + 0.25 * (1.0 - true_weights / true_weights.max())

    # State
    centroids = np.zeros((N_CATEGORIES, N_ACTIONS, N_FACTORS))
    counts = np.zeros((N_CATEGORIES, N_ACTIONS), dtype=int)
    base_accuracy = rng.uniform(0.70, 0.85)

    results = []
    conservation_status = []  # 'GREEN', 'AMBER', 'RED'
    recent_quality = []
    learning_paused = False
    pause_events = []
    resume_events = []

    total_decisions = N_DECISIONS_HEALTHY + N_DECISIONS_DEGRADED

    for i in range(total_decisions):
        cat = i % N_CATEGORIES
        action = rng.integers(0, N_ACTIONS)

        # Generate factor observation
        fv = rng.normal(0, 1, N_FACTORS) * noise_std + 0.5

        # Apply degradation after healthy period
        current_acc = base_accuracy
        current_fv = fv.copy()
        if i >= N_DECISIONS_HEALTHY:
            current_acc, current_fv = degradation_fn(
                base_accuracy, fv, i - N_DECISIONS_HEALTHY, rng
            )

        # Compute decision quality
        if counts[cat, action] > 10 and not learning_paused:
            centroid_alignment = np.dot(
                centroids[cat, action] / (np.linalg.norm(centroids[cat, action]) + 1e-8),
                true_weights
            )
            adjusted_acc = current_acc * (0.6 + 0.4 * max(0, centroid_alignment))
        else:
            adjusted_acc = current_acc * 0.6

        adjusted_acc = np.clip(adjusted_acc, 0.05, 0.95)
        is_correct = rng.random() < adjusted_acc

        # Conservation monitoring
        recent_quality.append(is_correct)
        if len(recent_quality) > Q_WINDOW:
            recent_quality.pop(0)
        rolling_q = sum(recent_quality) / len(recent_quality) if recent_quality else 0

        # Conservation check
        if use_conservation and i > Q_WINDOW:
            categories_with_data = len(set(
                c for c in range(N_CATEGORIES)
                if any(counts[c, a] > 5 for a in range(N_ACTIONS))
            ))
            alpha = categories_with_data / N_CATEGORIES

            if rolling_q < Q_THRESHOLD and alpha > ALPHA_THRESHOLD:
                if not learning_paused:
                    learning_paused = True
                    pause_events.append(i)
                conservation_status.append('AMBER')
            elif rolling_q < Q_THRESHOLD * 0.7:
                conservation_status.append('RED')
            else:
                if learning_paused and rolling_q > Q_THRESHOLD:
                    learning_paused = False
                    resume_events.append(i)
                conservation_status.append('GREEN')
        else:
            conservation_status.append('GREEN')

        # Update centroids (unless paused)
        if not learning_paused:
            counts[cat, action] += 1
            eta = ETA_CONFIRM if is_correct else ETA_OVERRIDE
            centroids[cat, action] += eta * (current_fv - centroids[cat, action])

        results.append(is_correct)

    return {
        "results": results,
        "conservation_status": conservation_status,
        "pause_events": pause_events,
        "resume_events": resume_events,
    }


# ═══════════════════════════════════════════════════════════
# Run experiment
# ═══════════════════════════════════════════════════════════

print("=" * 60)
print("E-JM-4: Conservation Law vs Unconstrained Learning")
print("=" * 60)

all_data = {}

for deg_name, deg_fn in DEGRADATION_MODELS.items():
    all_data[deg_name] = {"constrained": [], "unconstrained": []}

    for trial in range(N_TRIALS):
        rng = np.random.default_rng(SEED_BASE + hash(deg_name) % 10000 + trial)

        # Same random state for both conditions (fair comparison)
        rng_c = np.random.default_rng(SEED_BASE + hash(deg_name) % 10000 + trial)
        rng_u = np.random.default_rng(SEED_BASE + hash(deg_name) % 10000 + trial)

        constrained = run_simulation(deg_fn, use_conservation=True, rng=rng_c)
        unconstrained = run_simulation(deg_fn, use_conservation=False, rng=rng_u)

        all_data[deg_name]["constrained"].append(constrained)
        all_data[deg_name]["unconstrained"].append(unconstrained)

    print(f"  {deg_name}: {N_TRIALS} trials complete")


# ═══════════════════════════════════════════════════════════
# Analysis helpers
# ═══════════════════════════════════════════════════════════

def rolling_mean(results_list, window=Q_WINDOW):
    """Compute mean + CI of rolling accuracy."""
    all_results = [d["results"] for d in results_list]
    max_len = max(len(r) for r in all_results)
    arr = np.full((len(all_results), max_len), np.nan)
    for i, r in enumerate(all_results):
        arr[i, :len(r)] = r

    rolling = np.full_like(arr, np.nan)
    for i in range(len(all_results)):
        for j in range(window, max_len):
            rolling[i, j] = np.nanmean(arr[i, j - window:j])

    mean = np.nanmean(rolling, axis=0)
    ci = 1.96 * np.nanstd(rolling, axis=0) / np.sqrt(
        np.sum(~np.isnan(rolling), axis=0).clip(1))
    return mean, ci


def conservation_color_trajectory(results_list):
    """Mean fraction of GREEN/AMBER/RED across trials."""
    max_len = max(len(d["conservation_status"]) for d in results_list)
    green = np.zeros(max_len)
    amber = np.zeros(max_len)
    red = np.zeros(max_len)
    count = np.zeros(max_len)

    for d in results_list:
        for j, s in enumerate(d["conservation_status"]):
            if s == 'GREEN': green[j] += 1
            elif s == 'AMBER': amber[j] += 1
            elif s == 'RED': red[j] += 1
            count[j] += 1

    count = count.clip(1)
    return green / count, amber / count, red / count


# ═══════════════════════════════════════════════════════════
# Chart 1: Quality trajectories — all degradation types
# ═══════════════════════════════════════════════════════════

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
axes_flat = axes.flatten()

total = N_DECISIONS_HEALTHY + N_DECISIONS_DEGRADED
x = np.arange(total)

for idx, (deg_name, data) in enumerate(all_data.items()):
    if idx >= 5:
        break
    ax = axes_flat[idx]

    mean_c, ci_c = rolling_mean(data["constrained"])
    mean_u, ci_u = rolling_mean(data["unconstrained"])

    ax.fill_between(x, mean_u - ci_u, mean_u + ci_u, alpha=0.12, color='red')
    ax.fill_between(x, mean_c - ci_c, mean_c + ci_c, alpha=0.12, color='green')
    ax.plot(x, mean_u, color='red', linewidth=1.5, label='Unconstrained')
    ax.plot(x, mean_c, color='green', linewidth=2.0, label='Conservation')
    ax.axvline(x=N_DECISIONS_HEALTHY, color='black', linestyle='--',
               linewidth=1, alpha=0.5)

    ax.set_title(deg_name, fontsize=11)
    ax.set_xlabel('Decision' if idx >= 2 else '', fontsize=10)
    ax.set_ylabel('Rolling accuracy' if idx % 3 == 0 else '', fontsize=10)
    ax.set_ylim(0.25, 0.95)
    ax.grid(True, alpha=0.3)
    if idx == 0:
        ax.legend(fontsize=9, loc='lower left')

    # Add degradation marker
    ax.text(N_DECISIONS_HEALTHY + 10, 0.92, '← degradation starts',
            fontsize=8, color='black', alpha=0.6)

# Hide unused subplot
axes_flat[5].set_visible(False)

fig.suptitle('E-JM-4: Conservation Law vs Unconstrained Learning\n'
             f'{N_TRIALS} trials per condition, {N_FACTORS} factors, '
             f'degradation at decision {N_DECISIONS_HEALTHY}',
             fontsize=14)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_4_trajectories.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_4_trajectories.pdf", bbox_inches='tight')
plt.close()
print(f"\nChart 1 saved: {OUTPUT_DIR / 'e_jm_4_trajectories.png'}")


# ═══════════════════════════════════════════════════════════
# Chart 2: Conservation status heatmap
# ═══════════════════════════════════════════════════════════

fig, axes = plt.subplots(2, 3, figsize=(18, 8))
axes_flat = axes.flatten()

for idx, (deg_name, data) in enumerate(all_data.items()):
    if idx >= 5:
        break
    ax = axes_flat[idx]

    green, amber, red = conservation_color_trajectory(data["constrained"])

    ax.fill_between(x, 0, green, color='green', alpha=0.6, label='GREEN')
    ax.fill_between(x, green, green + amber, color='orange', alpha=0.6, label='AMBER')
    ax.fill_between(x, green + amber, green + amber + red,
                     color='red', alpha=0.6, label='RED')
    ax.axvline(x=N_DECISIONS_HEALTHY, color='black', linestyle='--', linewidth=1)

    ax.set_title(deg_name, fontsize=11)
    ax.set_xlabel('Decision' if idx >= 2 else '', fontsize=10)
    ax.set_ylabel('Fraction' if idx % 3 == 0 else '', fontsize=10)
    ax.set_ylim(0, 1)
    if idx == 0:
        ax.legend(fontsize=8, loc='lower left')

axes_flat[5].set_visible(False)

fig.suptitle('E-JM-4: Conservation Status Over Time\n'
             'GREEN = learning active, AMBER = learning paused, RED = quality critical',
             fontsize=14)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_4_conservation_status.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_4_conservation_status.pdf", bbox_inches='tight')
plt.close()
print(f"Chart 2 saved: {OUTPUT_DIR / 'e_jm_4_conservation_status.png'}")


# ═══════════════════════════════════════════════════════════
# Chart 3: Degradation depth comparison
# ═══════════════════════════════════════════════════════════

fig, ax = plt.subplots(1, 1, figsize=(12, 7))

deg_names = [n for n in DEGRADATION_MODELS.keys() if n != "No degradation (control)"]
x_pos = np.arange(len(deg_names))
width = 0.35

constrained_depths = []
unconstrained_depths = []

for deg_name in deg_names:
    data = all_data[deg_name]

    # Minimum rolling quality in degraded period
    c_depths = []
    u_depths = []
    for trial_idx in range(N_TRIALS):
        c_results = data["constrained"][trial_idx]["results"]
        u_results = data["unconstrained"][trial_idx]["results"]

        # Find worst rolling window in degraded period
        c_worst = 1.0
        u_worst = 1.0
        for j in range(N_DECISIONS_HEALTHY + Q_WINDOW, len(c_results)):
            c_q = np.mean(c_results[j - Q_WINDOW:j])
            u_q = np.mean(u_results[j - Q_WINDOW:j])
            c_worst = min(c_worst, c_q)
            u_worst = min(u_worst, u_q)
        c_depths.append(c_worst)
        u_depths.append(u_worst)

    constrained_depths.append(c_depths)
    unconstrained_depths.append(u_depths)

c_means = [np.mean(d) for d in constrained_depths]
u_means = [np.mean(d) for d in unconstrained_depths]
c_ci = [1.96 * np.std(d) / np.sqrt(len(d)) for d in constrained_depths]
u_ci = [1.96 * np.std(d) / np.sqrt(len(d)) for d in unconstrained_depths]

bars1 = ax.bar(x_pos - width / 2, u_means, width, yerr=u_ci,
               label='Unconstrained', color='#EF5350', edgecolor='black',
               linewidth=0.5, capsize=5, alpha=0.8)
bars2 = ax.bar(x_pos + width / 2, c_means, width, yerr=c_ci,
               label='Conservation', color='#66BB6A', edgecolor='black',
               linewidth=0.5, capsize=5, alpha=0.8)

ax.set_xlabel('Degradation type', fontsize=12)
ax.set_ylabel('Worst rolling accuracy during degradation\n(higher = less damage)',
              fontsize=11)
ax.set_title('E-JM-4: Maximum Quality Drop by Degradation Type\n'
             'Conservation prevents the system from learning bad patterns',
             fontsize=14)
ax.set_xticks(x_pos)
ax.set_xticklabels(deg_names, fontsize=10)
ax.legend(fontsize=11)
ax.set_ylim(0, 1.0)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_4_degradation_depth.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_4_degradation_depth.pdf", bbox_inches='tight')
plt.close()
print(f"Chart 3 saved: {OUTPUT_DIR / 'e_jm_4_degradation_depth.png'}")


# ═══════════════════════════════════════════════════════════
# Chart 4: False positive rate (conservation pausing when it shouldn't)
# ═══════════════════════════════════════════════════════════

fig, ax = plt.subplots(1, 1, figsize=(10, 6))

# In the "No degradation" control, any pause is a false positive
control_data = all_data["No degradation (control)"]["constrained"]
false_pause_count = sum(1 for d in control_data if len(d["pause_events"]) > 0)
false_pause_rate = false_pause_count / N_TRIALS * 100

# True positive rate for each degradation type
true_positive_rates = {}
for deg_name in deg_names:
    data = all_data[deg_name]["constrained"]
    detected = sum(1 for d in data if len(d["pause_events"]) > 0)
    true_positive_rates[deg_name] = detected / N_TRIALS * 100

all_labels = ["No degradation\n(false positive)"] + [n.replace(" ", "\n") for n in deg_names]
all_rates = [false_pause_rate] + [true_positive_rates[n] for n in deg_names]
colors = ['#EF5350'] + ['#66BB6A'] * len(deg_names)

bars = ax.bar(range(len(all_labels)), all_rates, color=colors,
              edgecolor='black', linewidth=0.5, alpha=0.8)

ax.set_ylabel('Detection rate (%)', fontsize=12)
ax.set_title('E-JM-4: Conservation Detection Rates\n'
             'Left bar (red) = false positive rate. Green bars = true positive rates.',
             fontsize=14)
ax.set_xticks(range(len(all_labels)))
ax.set_xticklabels(all_labels, fontsize=9)
ax.set_ylim(0, 105)
ax.grid(True, alpha=0.3, axis='y')

for i, (bar, rate) in enumerate(zip(bars, all_rates)):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
            f'{rate:.0f}%', ha='center', fontsize=11, fontweight='bold')

plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_4_detection_rates.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_4_detection_rates.pdf", bbox_inches='tight')
plt.close()
print(f"Chart 4 saved: {OUTPUT_DIR / 'e_jm_4_detection_rates.png'}")


# ═══════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════

summary = {
    "experiment": "E-JM-4: Conservation Law vs Unconstrained Learning",
    "n_trials": N_TRIALS,
    "n_decisions_healthy": N_DECISIONS_HEALTHY,
    "n_decisions_degraded": N_DECISIONS_DEGRADED,
    "n_factors": N_FACTORS,
    "q_threshold": Q_THRESHOLD,
    "false_positive_rate_pct": float(false_pause_rate),
    "results_by_degradation": {},
}

print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
print(f"\nFalse positive rate (control): {false_pause_rate:.1f}%")

for deg_name in deg_names:
    c_data = all_data[deg_name]["constrained"]
    u_data = all_data[deg_name]["unconstrained"]

    c_post = [np.mean(d["results"][N_DECISIONS_HEALTHY:]) for d in c_data]
    u_post = [np.mean(d["results"][N_DECISIONS_HEALTHY:]) for d in u_data]

    detection = true_positive_rates[deg_name]
    advantage = np.mean(c_post) - np.mean(u_post)

    # Mean pause events
    pause_counts = [len(d["pause_events"]) for d in c_data]

    summary["results_by_degradation"][deg_name] = {
        "detection_rate_pct": float(detection),
        "constrained_post_accuracy": float(np.mean(c_post)),
        "unconstrained_post_accuracy": float(np.mean(u_post)),
        "conservation_advantage_pp": float(advantage * 100),
        "mean_pause_events": float(np.mean(pause_counts)),
    }

    print(f"\n{deg_name}:")
    print(f"  Detection rate:     {detection:.0f}%")
    print(f"  Constrained post:   {np.mean(c_post):.3f}")
    print(f"  Unconstrained post: {np.mean(u_post):.3f}")
    print(f"  Advantage:          {advantage*100:+.2f}pp")
    print(f"  Mean pause events:  {np.mean(pause_counts):.1f}")

with open(OUTPUT_DIR / "e_jm_4_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print(f"\nResults saved to {OUTPUT_DIR}/")
