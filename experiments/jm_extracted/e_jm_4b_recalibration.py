#!/usr/bin/env python3
"""E-JM-4b v6: Minimal clean recalibration proof."""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import json

N_F, N_C, N_A = 7, 5, 4
N1, N2 = 500, 700  # longer post-change for recovery visibility
N_TRIALS, Q_WIN, SEED = 30, 40, 42
OUTPUT_DIR = Path("results/e_jm_4b"); OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def run(shift, regime, rng):
    cent = np.zeros((N_C, N_A, N_F))
    cnt = np.zeros((N_C, N_A), dtype=int)
    results = []; paused = False; recalibrated = False; grace_until = 0

    for i in range(N1 + N2):
        c, a = i % N_C, rng.integers(0, N_A)
        # Factor vector: centered at 0 for Person A, shifted for Person B
        fv = rng.normal(0, 0.3, N_F)
        if i >= N1: fv += shift

        # Score: exp(-distance²) — closer to centroid = better
        if cnt[c, a] > 5 and not paused:
            d2 = np.sum((fv - cent[c, a])**2)
            acc = 0.30 + 0.55 * np.exp(-d2 * 1.0)
        else:
            acc = 0.30
        acc = np.clip(acc, 0.15, 0.85)
        ok = rng.random() < acc

        # Conservation: detect quality drop after change
        if regime != "unconstrained" and i >= N1 + Q_WIN and i > grace_until and not recalibrated:
            recent = results[max(0, len(results)-Q_WIN):]
            roll = sum(recent) / len(recent)
            if roll < 0.40 and not paused:
                paused = True
            # Recalibrate: after being paused for 60 decisions, supervisor approves
            if regime == "recalibrate" and paused and not recalibrated and i >= N1 + Q_WIN + 60:
                recalibrated = True
                paused = False
                cent[:] = 0  # full reset
                cnt[:] = 0
                grace_until = i + 200  # grace period: 150 decisions to rebuild

        if not paused:
            cnt[c, a] += 1
            eta = 0.05 if ok else 0.01
            cent[c, a] += eta * (fv - cent[c, a])

        results.append(ok)
    return results

print("E-JM-4b v6: Minimal Recalibration Proof")
data: dict[str, list[list[bool]]] = {
    r: [] for r in ["unconstrained", "conservation", "recalibrate"]
}
for trial in range(N_TRIALS):
    rng = np.random.default_rng(SEED + trial)
    shift = np.zeros(N_F)
    shift[rng.choice(N_F, 4, replace=False)] = rng.uniform(0.5, 1.0, 4)
    for reg in data:
        data[reg].append(run(shift, reg, np.random.default_rng(SEED + trial)))
    if (trial+1) % 10 == 0: print(f"  Trial {trial+1}/{N_TRIALS}")

def roll_acc(rl, w=Q_WIN):
    mx = max(len(r) for r in rl)
    a = np.full((len(rl), mx), np.nan)
    for i, r in enumerate(rl): a[i, :len(r)] = r
    ro = np.full_like(a, np.nan)
    for i in range(len(rl)):
        for j in range(w, mx): ro[i, j] = np.nanmean(a[i, j-w:j])
    return np.nanmean(ro, axis=0), np.nanstd(ro, axis=0)

fig, ax = plt.subplots(1, 1, figsize=(14, 7)); x = np.arange(N1+N2)
for reg, col, lw, lab in [("unconstrained","red",1.5,"Unconstrained"),
    ("conservation","orange",1.5,"Conservation only (frozen)"),
    ("recalibrate","green",2.5,"Conservation + recalibration")]:
    m, s = roll_acc(data[reg]); ci = 1.96*s/np.sqrt(N_TRIALS)
    ax.fill_between(x, m-ci, m+ci, alpha=0.10, color=col)
    ax.plot(x, m, color=col, linewidth=lw, label=lab)
ax.axvline(x=N1, color='black', linestyle='--', linewidth=1, alpha=0.5)
ax.set_xlabel('Decision', fontsize=12); ax.set_ylabel('Rolling accuracy', fontsize=12)
ax.set_title(f'E-JM-4b: Detect → Pause → Recalibrate → Recover\n'
             f'{N_TRIALS} trials. Person B shifts 4/7 factor means.', fontsize=14)
ax.legend(fontsize=10, loc='lower left'); ax.set_ylim(0.10, 0.90); ax.grid(True, alpha=0.3)
plt.tight_layout()
fig.savefig(OUTPUT_DIR/"e_jm_4b_trajectory.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR/"e_jm_4b_trajectory.pdf", bbox_inches='tight')
plt.close(); print("Chart 1 saved")

fig, ax = plt.subplots(1, 1, figsize=(10, 7))
pd = [[np.mean(r[-200:]) for r in data[reg]] for reg in ["unconstrained","conservation","recalibrate"]]
bp = ax.boxplot(pd, labels=['Unconstrained','Conservation\nonly','Conserv +\nrecalibration'],
                patch_artist=True, widths=0.5)
for p, c in zip(bp['boxes'], ['#EF5350','#FFB74D','#66BB6A']): p.set_facecolor(c)
ax.set_ylabel('Late-stage accuracy (last 200)', fontsize=12)
ax.set_title('E-JM-4b: Recovery', fontsize=14)
ax.grid(True, alpha=0.3, axis='y'); plt.tight_layout()
fig.savefig(OUTPUT_DIR/"e_jm_4b_recovery_box.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR/"e_jm_4b_recovery_box.pdf", bbox_inches='tight')
plt.close(); print("Chart 2 saved")

s = {}
for reg in data:
    post = [np.mean(r[-200:]) for r in data[reg]]
    s[reg] = {"mean": float(np.mean(post)), "std": float(np.std(post))}
gc = s["recalibrate"]["mean"] - s["conservation"]["mean"]
gt = s["unconstrained"]["mean"] - s["conservation"]["mean"]

summary = {"experiment": "E-JM-4b v6", "results": s,
    "gap_closed_pp": float(gc*100), "total_gap_pp": float(gt*100),
    "recovery_pct": float(gc/max(abs(gt),1e-8)*100)}
with open(OUTPUT_DIR/"e_jm_4b_summary.json","w") as f: json.dump(summary, f, indent=2)

print(f"\nSUMMARY:")
for r in s: print(f"  {r:20s}: {s[r]['mean']:.3f} ± {s[r]['std']:.3f}")
print(f"  Recalibration recovery: {gc*100:+.1f}pp ({gc/max(abs(gt),1e-8)*100:.0f}% of gap)")
