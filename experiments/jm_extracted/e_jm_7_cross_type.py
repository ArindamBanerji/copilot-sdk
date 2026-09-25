#!/usr/bin/env python3
"""
E-JM-7: Cross-Type Interaction (Semantic × Judgment)
=====================================================
Tests whether entity-contextualized trust trap detection outperforms
global detection — i.e., does combining semantic (entity type) with
judgment (factor weights) produce capabilities unattainable by either alone?

Design:
  - Domain with 3 entity groups (finance, engineering, operations)
  - GLOBAL factor weights are the average across groups
  - PER-GROUP factor weights differ (F3 predictive for finance, not engineering)
  - Condition A: GLOBAL DK weights (judgment only, no entity context)
  - Condition B: PER-ENTITY DK weights (semantic × judgment interaction)
  - Condition C: SEPARATE STORES simulation (entity lookup + global DK,
    no per-entity DK — simulates API-stitched architecture)
  - Measure: scoring accuracy, trust trap detection per entity group
"""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import json

N_FACTORS = 7
N_ENTITY_GROUPS = 3
ENTITY_NAMES = ["Finance", "Engineering", "Operations"]
N_DECISIONS = 2000
N_TRIALS = 25
Q_WINDOW = 50
SEED = 42
OUTPUT_DIR = Path("results/e_jm_7"); OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class WelfordVar:
    def __init__(self, d):
        self.n, self.mean, self.M2 = 0, np.zeros(d), np.zeros(d)
    def update(self, x):
        self.n += 1; d = x - self.mean; self.mean += d/self.n; self.M2 += d*(x-self.mean)
    def variance(self):
        return self.M2/max(self.n-1,1) if self.n>1 else np.ones_like(self.mean)

def generate_domain(rng):
    """Generate domain with entity-specific factor weights."""
    # Global weights (average)
    raw = rng.exponential(1.0, N_FACTORS)
    global_w = raw / raw.sum()
    # Per-entity weights: share base structure but each group has 2-3 factors
    # that are MORE or LESS important than global average
    entity_weights = []
    for g in range(N_ENTITY_GROUPS):
        modifier = rng.uniform(0.3, 2.5, N_FACTORS)
        # Make modifications more dramatic for some factors
        modifier[rng.choice(N_FACTORS, 2, replace=False)] = rng.uniform(0.1, 0.3, 2)
        modifier[rng.choice(N_FACTORS, 2, replace=False)] = rng.uniform(2.0, 4.0, 2)
        ew = global_w * modifier
        entity_weights.append(ew / ew.sum())
    noise = 0.15 + 0.20 * (1.0 - global_w / global_w.max())
    return global_w, entity_weights, noise

def run_condition(global_w, entity_weights, noise, condition, rng):
    """Run one condition over N_DECISIONS."""
    person_acc = rng.uniform(0.65, 0.80)
    results_by_entity = [[] for _ in range(N_ENTITY_GROUPS)]
    results_all = []

    # State for each condition
    if condition == "global":
        # One set of DK weights for everything
        stats_all = WelfordVar(N_FACTORS)
        conf_all, over_all = WelfordVar(N_FACTORS), WelfordVar(N_FACTORS)
        dk_w = np.ones(N_FACTORS) / N_FACTORS
    elif condition == "per_entity":
        # Per-entity DK weights (semantic × judgment)
        stats = [WelfordVar(N_FACTORS) for _ in range(N_ENTITY_GROUPS)]
        conf = [WelfordVar(N_FACTORS) for _ in range(N_ENTITY_GROUPS)]
        over = [WelfordVar(N_FACTORS) for _ in range(N_ENTITY_GROUPS)]
        dk_w_per = [np.ones(N_FACTORS)/N_FACTORS for _ in range(N_ENTITY_GROUPS)]
    elif condition == "separate_stores":
        # Entity lookup exists, but DK weights are global (simulates no cross-type join)
        stats_all = WelfordVar(N_FACTORS)
        conf_all, over_all = WelfordVar(N_FACTORS), WelfordVar(N_FACTORS)
        dk_w = np.ones(N_FACTORS) / N_FACTORS

    centroids = np.zeros((N_ENTITY_GROUPS, 4, N_FACTORS))
    counts = np.zeros((N_ENTITY_GROUPS, 4), dtype=int)

    for i in range(N_DECISIONS):
        entity_group = rng.integers(0, N_ENTITY_GROUPS)
        true_w = entity_weights[entity_group]
        action = rng.integers(0, 4)
        fv = rng.normal(0, 1, N_FACTORS) * noise + true_w * 1.5

        # Scoring: use appropriate DK weights
        if condition == "per_entity":
            w = dk_w_per[entity_group]
        else:
            w = dk_w

        if counts[entity_group, action] > 10:
            ca = centroids[entity_group, action]
            weighted = ca * w
            al = np.dot(weighted, true_w) / (np.linalg.norm(weighted)+1e-8)
            adj = person_acc * (0.55 + 0.25 * np.clip(al, 0, 1))
        else:
            adj = person_acc * 0.55
        adj = np.clip(adj, 0.10, 0.95)
        is_correct = rng.random() < adj

        # Update centroids (all conditions use per-entity centroids)
        counts[entity_group, action] += 1
        eta = 0.05 if is_correct else 0.01
        centroids[entity_group, action] += eta * (fv - centroids[entity_group, action])

        # Update DK weights
        if condition == "global" or condition == "separate_stores":
            stats_all.update(fv)
            if is_correct: conf_all.update(fv)
            else: over_all.update(fv)
            if conf_all.n >= 15 and over_all.n >= 10:
                sep = np.abs(conf_all.mean - over_all.mean)
                ps = np.sqrt((conf_all.variance()+over_all.variance())/2+1e-6)
                disc = sep / ps
                inv = 1.0/(np.sqrt(stats_all.variance())+1e-6)
                c = disc * inv; dk_w = c/(c.sum()+1e-8)
        elif condition == "per_entity":
            g = entity_group
            stats[g].update(fv)
            if is_correct: conf[g].update(fv)
            else: over[g].update(fv)
            if conf[g].n >= 15 and over[g].n >= 10:
                sep = np.abs(conf[g].mean - over[g].mean)
                ps = np.sqrt((conf[g].variance()+over[g].variance())/2+1e-6)
                disc = sep / ps
                inv = 1.0/(np.sqrt(stats[g].variance())+1e-6)
                c = disc * inv; dk_w_per[g] = c/(c.sum()+1e-8)

        results_by_entity[entity_group].append(is_correct)
        results_all.append(is_correct)

    # Compute per-entity trust trap detection
    trap_detection = {}
    for g in range(N_ENTITY_GROUPS):
        true_top = np.argsort(entity_weights[g])[::-1][0]
        global_top = np.argsort(global_w)[::-1][0]
        if condition == "per_entity":
            learned_top = np.argsort(dk_w_per[g])[::-1][0]
        else:
            learned_top = np.argsort(dk_w)[::-1][0]
        # Entity-specific trap: true_top differs from global_top
        has_entity_trap = true_top != global_top
        detected = learned_top == true_top and has_entity_trap
        trap_detection[ENTITY_NAMES[g]] = {
            "has_entity_trap": bool(has_entity_trap),
            "detected": bool(detected),
            "true_top": int(true_top),
            "learned_top": int(learned_top),
            "global_top": int(global_top),
        }

    return results_all, results_by_entity, trap_detection

# Run experiment
print("=" * 60)
print("E-JM-7: Cross-Type Interaction (Semantic × Judgment)")
print("=" * 60)

all_data = {c: {"results": [], "per_entity": [], "traps": []}
            for c in ["global", "per_entity", "separate_stores"]}

for trial in range(N_TRIALS):
    rng = np.random.default_rng(SEED + trial)
    gw, ew, noise = generate_domain(rng)
    for cond in all_data:
        t_rng = np.random.default_rng(SEED + trial)
        res_all, res_ent, traps = run_condition(gw, ew, noise, cond, t_rng)
        all_data[cond]["results"].append(res_all)
        all_data[cond]["per_entity"].append(res_ent)
        all_data[cond]["traps"].append(traps)
    if (trial+1) % 5 == 0: print(f"  Trial {trial+1}/{N_TRIALS}")

def rolling_acc(results_list, window=Q_WINDOW):
    mx = max(len(r) for r in results_list)
    arr = np.full((len(results_list), mx), np.nan)
    for i, r in enumerate(results_list): arr[i, :len(r)] = r
    roll = np.full_like(arr, np.nan)
    for i in range(len(results_list)):
        for j in range(window, mx): roll[i, j] = np.nanmean(arr[i, j-window:j])
    return np.nanmean(roll, axis=0), np.nanstd(roll, axis=0)

# Chart 1: Overall accuracy comparison
fig, ax = plt.subplots(1, 1, figsize=(14, 7))
x = np.arange(N_DECISIONS)
for cond, color, lw, label in [
    ("global", "orange", 1.5, "Global DK (judgment only)"),
    ("separate_stores", "gray", 1.5, "Separate stores (entity + global DK)"),
    ("per_entity", "green", 2.5, "Per-entity DK (semantic × judgment)"),
]:
    mean, std = rolling_acc(all_data[cond]["results"])
    ci = 1.96 * std / np.sqrt(N_TRIALS)
    ax.fill_between(x, mean-ci, mean+ci, alpha=0.10, color=color)
    ax.plot(x, mean, color=color, linewidth=lw, label=label)
ax.set_xlabel('Decision', fontsize=12); ax.set_ylabel(f'Rolling accuracy', fontsize=12)
ax.set_title('E-JM-7: Cross-Type Interaction — Entity-Contextualized DK\n'
             f'{N_TRIALS} trials, {N_ENTITY_GROUPS} entity groups, {N_FACTORS} factors',
             fontsize=14)
ax.legend(fontsize=10); ax.set_ylim(0.30, 0.80); ax.grid(True, alpha=0.3)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_7_accuracy.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_7_accuracy.pdf", bbox_inches='tight')
plt.close(); print("\nChart 1 saved")

# Chart 2: Entity-specific trust trap detection
fig, ax = plt.subplots(1, 1, figsize=(12, 7))
for cond_idx, (cond, color, label) in enumerate([
    ("global", "#FFB74D", "Global DK"),
    ("separate_stores", "#BDBDBD", "Separate stores"),
    ("per_entity", "#66BB6A", "Per-entity DK"),
]):
    detection_rates = []
    for g in range(N_ENTITY_GROUPS):
        traps_with = [t[ENTITY_NAMES[g]] for t in all_data[cond]["traps"]
                      if t[ENTITY_NAMES[g]]["has_entity_trap"]]
        if traps_with:
            rate = sum(1 for t in traps_with if t["detected"]) / len(traps_with) * 100
        else:
            rate = 0
        detection_rates.append(rate)
    x_pos = np.arange(N_ENTITY_GROUPS) + cond_idx * 0.25
    ax.bar(x_pos, detection_rates, 0.22, color=color, edgecolor='black',
           linewidth=0.5, label=label, alpha=0.8)
    for i, r in enumerate(detection_rates):
        if r > 0: ax.text(x_pos[i], r+2, f'{r:.0f}%', ha='center', fontsize=9)

ax.set_xticks(np.arange(N_ENTITY_GROUPS) + 0.25)
ax.set_xticklabels(ENTITY_NAMES, fontsize=11)
ax.set_ylabel('Entity-specific trust trap detection (%)', fontsize=12)
ax.set_title('E-JM-7: Per-Entity Trust Trap Detection\n'
             'Can the system discover that factor importance differs by entity group?',
             fontsize=14)
ax.legend(fontsize=10); ax.set_ylim(0, 105); ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_7_trap_detection.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_7_trap_detection.pdf", bbox_inches='tight')
plt.close(); print("Chart 2 saved")

# Summary
summary = {"experiment": "E-JM-7", "n_trials": N_TRIALS, "n_entity_groups": N_ENTITY_GROUPS,
           "results": {}}
print(f"\n{'='*60}\nSUMMARY\n{'='*60}")
for cond in all_data:
    late_acc = [np.mean(r[N_DECISIONS//2:]) for r in all_data[cond]["results"]]
    # Entity trap detection
    total_traps, total_detected = 0, 0
    for trial_traps in all_data[cond]["traps"]:
        for g in ENTITY_NAMES:
            if trial_traps[g]["has_entity_trap"]:
                total_traps += 1
                if trial_traps[g]["detected"]: total_detected += 1
    det_rate = total_detected / max(total_traps, 1) * 100
    summary["results"][cond] = {
        "late_accuracy_mean": float(np.mean(late_acc)),
        "entity_trap_detection_pct": float(det_rate),
        "total_entity_traps": total_traps, "total_detected": total_detected,
    }
    print(f"  {cond:20s}: acc={np.mean(late_acc):.3f}  entity trap detection={det_rate:.1f}%")

pe = summary["results"]["per_entity"]["late_accuracy_mean"]
gl = summary["results"]["global"]["late_accuracy_mean"]
ss = summary["results"]["separate_stores"]["late_accuracy_mean"]
print(f"\n  Per-entity advantage over global:   {(pe-gl)*100:+.2f}pp")
print(f"  Per-entity advantage over separate: {(pe-ss)*100:+.2f}pp")

with open(OUTPUT_DIR / "e_jm_7_summary.json", "w") as f: json.dump(summary, f, indent=2)
print(f"\nResults saved to {OUTPUT_DIR}/")
