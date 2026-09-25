#!/usr/bin/env python3
"""
E-JM-6b: Bayesian Online Learning Baseline + Confidence Interval
==================================================================
Adds:
  1. Bayesian linear regression baseline (online, same verified decisions)
  2. Bootstrap confidence interval for the compounding exponent
"""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import optimize, stats
from pathlib import Path
import json

N_FACTORS, N_CATEGORIES, N_ACTIONS = 7, 6, 4
N_DECISIONS, N_TRIALS, Q_WINDOW = 3000, 20, 100
CONSERVATION_Q, SEED = 0.70, 42
N_BOOTSTRAP = 100
OUTPUT_DIR = Path("results/e_jm_6b"); OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class WelfordVar:
    def __init__(self, d):
        self.n, self.mean, self.M2 = 0, np.zeros(d), np.zeros(d)
    def update(self, x):
        self.n += 1; d = x - self.mean; self.mean += d/self.n; self.M2 += d*(x-self.mean)
    def variance(self):
        return self.M2/max(self.n-1,1) if self.n>1 else np.ones_like(self.mean)

def generate_domain(rng):
    raw = rng.exponential(1.0, N_FACTORS)
    true_w = raw / raw.sum()
    noise = 0.20 + 0.25 * (1.0 - true_w / true_w.max())
    return true_w, noise

def run_bayesian(true_w, noise, rng):
    """Bayesian online linear regression baseline."""
    # Prior: w ~ N(0, I), sigma^2 known
    alpha_prior = 1.0  # prior precision
    beta = 1.0 / (0.2**2)  # noise precision
    S_inv = alpha_prior * np.eye(N_FACTORS)
    m = np.zeros(N_FACTORS)
    person_acc = rng.uniform(0.60, 0.80)
    results, approved = [], []
    cat_quality = np.zeros(N_CATEGORIES)
    cat_count = np.zeros(N_CATEGORIES)

    for i in range(N_DECISIONS):
        cat = i % N_CATEGORIES; action = rng.integers(0, N_ACTIONS)
        fv = rng.normal(0, 1, N_FACTORS) * noise + true_w * 1.5

        # Scoring: Bayesian prediction
        if i > 30:
            pred = np.dot(m, fv)
            adj = person_acc * (0.50 + 0.20 * np.clip(pred, 0, 1))
        else:
            adj = person_acc * 0.50
        adj = np.clip(adj, 0.10, 0.95)
        is_correct = rng.random() < adj

        # Bayesian update: posterior = prior × likelihood
        target = 1.0 if is_correct else -0.5
        S_inv_new = S_inv + beta * np.outer(fv, fv)
        m = np.linalg.solve(S_inv_new, S_inv @ m + beta * target * fv)
        S_inv = S_inv_new

        results.append(is_correct)
        cat_count[cat] += 1
        cat_quality[cat] += (is_correct - cat_quality[cat]) / cat_count[cat]
        n_approved = sum(1 for c in range(N_CATEGORIES)
                        if cat_count[c] > 30 and cat_quality[c] >= CONSERVATION_Q)
        if (i+1) % 50 == 0: approved.append(n_approved)

    return results, approved

def run_dk(true_w, noise, rng):
    """DiagonalKernel compounding (same as E-JM-6 v2)."""
    centroids = np.zeros((N_CATEGORIES, N_ACTIONS, N_FACTORS))
    counts = np.zeros((N_CATEGORIES, N_ACTIONS), dtype=int)
    dk_w = np.ones(N_FACTORS) / N_FACTORS
    conf_s, over_s, all_s = WelfordVar(N_FACTORS), WelfordVar(N_FACTORS), WelfordVar(N_FACTORS)
    person_acc = rng.uniform(0.60, 0.80)
    results, approved = [], []
    cat_quality = np.zeros(N_CATEGORIES)
    cat_count = np.zeros(N_CATEGORIES)

    for i in range(N_DECISIONS):
        cat = i % N_CATEGORIES; action = rng.integers(0, N_ACTIONS)
        fv = rng.normal(0, 1, N_FACTORS) * noise + true_w * 1.5
        if counts[cat, action] > 10 and all_s.n > 30:
            wc = centroids[cat, action] * dk_w
            al = np.dot(wc, true_w); prec = np.dot(dk_w, true_w)
            adj = person_acc * (0.50 + 0.35 * np.clip(al*prec*5, 0, 1))
        else:
            adj = person_acc * 0.50
        adj = np.clip(adj, 0.10, 0.95)
        is_correct = rng.random() < adj

        counts[cat, action] += 1
        eta = 0.05 if is_correct else 0.01
        centroids[cat, action] += eta * (fv - centroids[cat, action])
        all_s.update(fv)
        if is_correct: conf_s.update(fv)
        else: over_s.update(fv)
        if conf_s.n >= 15 and over_s.n >= 10:
            sep = np.abs(conf_s.mean - over_s.mean)
            ps = np.sqrt((conf_s.variance()+over_s.variance())/2+1e-6)
            disc = sep / ps; inv = 1.0/(np.sqrt(all_s.variance())+1e-6)
            c = disc * inv; dk_w = c/(c.sum()+1e-8)

        results.append(is_correct)
        cat_count[cat] += 1
        cat_quality[cat] += (is_correct - cat_quality[cat]) / cat_count[cat]
        n_approved = sum(1 for c in range(N_CATEGORIES)
                        if cat_count[c] > 30 and cat_quality[c] >= CONSERVATION_Q)
        if (i+1) % 50 == 0: approved.append(n_approved)

    return results, approved

print("=" * 60)
print("E-JM-6b: Bayesian Baseline + Confidence Interval")
print("=" * 60)

dk_data, bayes_data = {"results":[],"approved":[]}, {"results":[],"approved":[]}
for trial in range(N_TRIALS):
    rng = np.random.default_rng(SEED + trial)
    tw, n = generate_domain(rng)
    r1, a1 = run_dk(tw, n, np.random.default_rng(SEED+trial))
    r2, a2 = run_bayesian(tw, n, np.random.default_rng(SEED+trial))
    dk_data["results"].append(r1); dk_data["approved"].append(a1)
    bayes_data["results"].append(r2); bayes_data["approved"].append(a2)
    if (trial+1) % 5 == 0: print(f"  Trial {trial+1}/{N_TRIALS}")

def rolling_acc(results_list, window=Q_WINDOW):
    mx = max(len(r) for r in results_list)
    arr = np.full((len(results_list), mx), np.nan)
    for i, r in enumerate(results_list): arr[i, :len(r)] = r
    roll = np.full_like(arr, np.nan)
    for i in range(len(results_list)):
        for j in range(window, mx): roll[i, j] = np.nanmean(arr[i, j-window:j])
    return np.nanmean(roll, axis=0), np.nanstd(roll, axis=0)

def fit_power(y):
    valid = ~np.isnan(y); x = np.arange(len(y))[valid].astype(float); yc = y[valid]
    if len(x) < 20: return 1.0, 0.0
    try:
        def pf(x, a, b, c): return a + b * np.power(x/x.max(), c)
        popt, _ = optimize.curve_fit(pf, x, yc, p0=[yc[0], 0.1, 1.5],
                                      maxfev=10000, bounds=([0, -1, 0.1], [1, 1, 5]))
        yp = pf(x, *popt)
        ss_res = np.sum((yc - yp)**2); ss_tot = np.sum((yc - yc.mean())**2)
        return popt[2], 1 - ss_res / max(ss_tot, 1e-8)
    except: return 1.0, 0.0

# Bootstrap CI for exponent
print("\nBootstrapping exponent CI...")
boot_exponents = []
for b in range(N_BOOTSTRAP):
    indices = np.random.default_rng(SEED+1000+b).choice(N_TRIALS, N_TRIALS, replace=True)
    # Compute combined metric for bootstrap sample
    boot_acc = []
    for idx in indices:
        r = dk_data["results"][idx]; a = dk_data["approved"][idx]
        mx = len(r)
        acc_roll = np.full(mx, np.nan)
        for j in range(Q_WINDOW, mx):
            acc_roll[j] = np.mean(r[j-Q_WINDOW:j])
        appr_interp = np.interp(np.arange(mx), np.arange(len(a))*50, a)
        combined = acc_roll * (appr_interp / N_CATEGORIES)
        boot_acc.append(combined)
    boot_mean = np.nanmean(boot_acc, axis=0)
    exp, _ = fit_power(boot_mean)
    boot_exponents.append(exp)

boot_exponents = np.array(boot_exponents)
ci_low, ci_high = np.percentile(boot_exponents, [2.5, 97.5])
mean_exp = np.mean(boot_exponents)

print(f"  Exponent: {mean_exp:.3f} (95% CI: [{ci_low:.3f}, {ci_high:.3f}])")

# Chart 1: DK vs Bayesian accuracy
fig, ax = plt.subplots(1, 1, figsize=(14, 7))
x = np.arange(N_DECISIONS)
for data, color, lw, label in [
    (bayes_data, "purple", 1.5, "Bayesian online linear regression"),
    (dk_data, "green", 2.5, "DiagonalKernel (judgment memory)"),
]:
    mean, std = rolling_acc(data["results"])
    ci = 1.96 * std / np.sqrt(N_TRIALS)
    ax.fill_between(x, mean-ci, mean+ci, alpha=0.10, color=color)
    ax.plot(x, mean, color=color, linewidth=lw, label=label)
ax.set_xlabel('Decision', fontsize=12); ax.set_ylabel('Rolling accuracy', fontsize=12)
ax.set_title('E-JM-6b: DiagonalKernel vs Bayesian Online Baseline\n'
             f'{N_TRIALS} trials, {N_DECISIONS} decisions', fontsize=14)
ax.legend(fontsize=11); ax.set_ylim(0.25, 0.80); ax.grid(True, alpha=0.3)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_6b_dk_vs_bayesian.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_6b_dk_vs_bayesian.pdf", bbox_inches='tight')
plt.close(); print("\nChart 1 saved")

# Chart 2: Exponent bootstrap distribution
fig, ax = plt.subplots(1, 1, figsize=(10, 6))
ax.hist(boot_exponents, bins=40, color='green', edgecolor='black', linewidth=0.5, alpha=0.7)
ax.axvline(x=1.0, color='red', linestyle='--', linewidth=2, label='c=1 (linear)')
ax.axvline(x=mean_exp, color='green', linestyle='-', linewidth=2,
           label=f'Mean c={mean_exp:.3f}')
ax.axvline(x=ci_low, color='green', linestyle=':', linewidth=1)
ax.axvline(x=ci_high, color='green', linestyle=':', linewidth=1)
ax.axvspan(ci_low, ci_high, alpha=0.1, color='green', label=f'95% CI [{ci_low:.3f}, {ci_high:.3f}]')
ax.set_xlabel('Power-law exponent c', fontsize=12)
ax.set_ylabel('Bootstrap count', fontsize=12)
ax.set_title('E-JM-6b: Bootstrap Distribution of Compounding Exponent\n'
             f'{N_BOOTSTRAP} bootstrap samples. c>1 = super-linear.',
             fontsize=14)
ax.legend(fontsize=10); ax.grid(True, alpha=0.3)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "e_jm_6b_exponent_ci.png", dpi=150, bbox_inches='tight')
fig.savefig(OUTPUT_DIR / "e_jm_6b_exponent_ci.pdf", bbox_inches='tight')
plt.close(); print("Chart 2 saved")

# Summary
dk_late = [np.mean(r[N_DECISIONS//2:]) for r in dk_data["results"]]
bay_late = [np.mean(r[N_DECISIONS//2:]) for r in bayes_data["results"]]

summary = {"experiment": "E-JM-6b", "n_trials": N_TRIALS, "n_bootstrap": N_BOOTSTRAP,
    "dk_late_accuracy": float(np.mean(dk_late)),
    "bayesian_late_accuracy": float(np.mean(bay_late)),
    "dk_advantage_pp": float((np.mean(dk_late)-np.mean(bay_late))*100),
    "exponent_mean": float(mean_exp),
    "exponent_ci_95": [float(ci_low), float(ci_high)],
    "exponent_gt_1_pct": float(np.mean(boot_exponents > 1.0) * 100),
}
with open(OUTPUT_DIR / "e_jm_6b_summary.json", "w") as f: json.dump(summary, f, indent=2)

print(f"\n{'='*60}\nSUMMARY\n{'='*60}")
print(f"  DK late accuracy:      {np.mean(dk_late):.3f}")
print(f"  Bayesian late accuracy: {np.mean(bay_late):.3f}")
print(f"  DK advantage:          {(np.mean(dk_late)-np.mean(bay_late))*100:+.2f}pp")
print(f"  Exponent:              {mean_exp:.3f} (95% CI: [{ci_low:.3f}, {ci_high:.3f}])")
print(f"  % bootstraps with c>1: {np.mean(boot_exponents>1.0)*100:.1f}%")
print(f"\nResults saved to {OUTPUT_DIR}/")
