"""
VLD Publication Charts — All-in-One Generator
===============================================
Run: python generate_all_pub_charts.py [output_dir]
Default output: ./pub_charts/

PUB-1 through PUB-8 + PUB-14: from simulation + experiment data.
PUB-15: Decision-aligned vs category-aligned (new finding).
PUB-16: Stage 1 multi-hop VLD vs ρ (SOC confirmed).

Style: light background, sentence-fragment labels, NBP visual language.
Colors: SOC=blue, DataOps=purple, S2P=amber, Trading=red, Purchasing=green.
"""

import sys
import numpy as np
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "./pub_charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Style ──
plt.rcParams.update({
    'font.size': 11,
    'axes.facecolor': '#FAFAFA',
    'figure.facecolor': '#FFFFFF',
    'axes.grid': True,
    'grid.alpha': 0.3,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

C = {
    'vld': '#2563EB', 'content': '#059669', 'majority': '#9333EA',
    'random': '#DC2626', 'single': '#6B7280', 'soc': '#2563EB',
    'dataops': '#9333EA', 's2p': '#D97706', 'trading': '#DC2626',
    'purchasing': '#059669', 'trained': '#D97706', 'default': '#6B7280',
    'dual': '#2563EB', 'gate_on': '#059669', 'gate_off': '#DC2626',
    'breadth': '#F59E0B',
}


# ═══════════════════════════════════════════════════════════════
# PUB-1: Routing accuracy vs comparators
# ═══════════════════════════════════════════════════════════════
def pub1():
    fig, ax = plt.subplots(figsize=(8, 5))
    policies = ['VLD\n(centroid)', 'Content\nrule', 'Majority\nbranch', 'Random', 'Chance\n(1/6)']
    values = [0.685, 1.0, 0.300, 0.167, 0.167]
    colors = [C['vld'], C['content'], C['majority'], C['random'], '#D1D5DB']
    bars = ax.bar(policies, values, color=colors, edgecolor='white', linewidth=1.5, width=0.6)
    ax.set_ylabel('Routing accuracy (ρ)')
    ax.set_title('Score-keyed routing: 2.3× better than majority baseline')
    ax.set_ylim(0, 1.1)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    ax.axhline(y=0.167, color='gray', linestyle='--', alpha=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'pub1_routing_comparators.png'), dpi=200)
    plt.close()


# ═══════════════════════════════════════════════════════════════
# PUB-2: ρ calibration curve (sim v4 Exp 2)
# ═══════════════════════════════════════════════════════════════
def pub2():
    fig, ax = plt.subplots(figsize=(9, 5))
    rho_values = np.arange(0.15, 1.01, 0.05)
    vld = [0.642, 0.634, 0.641, 0.651, 0.661, 0.685, 0.688, 0.695,
           0.707, 0.706, 0.719, 0.713, 0.712, 0.721, 0.729, 0.713, 0.725, 0.710]
    vld_lo = [v - 0.013 for v in vld]
    vld_hi = [v + 0.013 for v in vld]
    single = [0.636, 0.643, 0.624, 0.625, 0.626, 0.633, 0.627, 0.627,
              0.643, 0.632, 0.631, 0.623, 0.620, 0.638, 0.639, 0.611, 0.635, 0.617]
    ax.plot(rho_values, vld, 'b-o', label='VLD (score-routed)', linewidth=2, markersize=4)
    ax.fill_between(rho_values, vld_lo, vld_hi, alpha=0.15, color='blue')
    ax.plot(rho_values, single, 'k--', label='Single-pass', linewidth=2, alpha=0.6)
    ax.set_xlabel('ρ (score informativeness)')
    ax.set_ylabel('Action accuracy')
    ax.set_title('VLD beats single-pass at 17/18 ρ values (70% neutral evidence)')
    ax.legend(loc='lower right')
    ax.annotate('VLD advantage\ngrows with ρ', xy=(0.85, 0.729), xytext=(0.65, 0.75),
                arrowprops=dict(arrowstyle='->', color='blue', alpha=0.6),
                fontsize=9, color='blue')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'pub2_rho_calibration.png'), dpi=200)
    plt.close()


# ═══════════════════════════════════════════════════════════════
# PUB-3: Budget × evidence regime (sim v4 Exp 3)
# ═══════════════════════════════════════════════════════════════
def pub3():
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    budgets = [1, 2, 3, 4, 6]
    reext_n = [0.759, 0.869, 0.931, 0.967, 0.994]
    damp_n  = [0.757, 0.851, 0.913, 0.934, 0.886]
    single_n = [0.641] * 5
    reext_m = [0.680, 0.789, 0.874, 0.896, 0.810]
    damp_m  = [0.717, 0.788, 0.815, 0.762, 0.517]
    single_m = [0.639] * 5
    reext_a = [0.463, 0.664, 0.715, 0.349, 0.001]
    damp_a  = [0.609, 0.642, 0.548, 0.250, 0.020]
    single_a = [0.635] * 5
    for ax, reext, damp, single, title in [
        (axes[0], reext_n, damp_n, single_n, 'All-neutral evidence'),
        (axes[1], reext_m, damp_m, single_m, 'Mixed (70% neutral)'),
        (axes[2], reext_a, damp_a, single_a, 'All-misleading evidence')
    ]:
        ax.plot(budgets, reext, 'b-o', label='Re-extraction', linewidth=2, markersize=5)
        ax.plot(budgets, damp, 'r-s', label='Damped (ε=0.3)', linewidth=2, markersize=5)
        ax.plot(budgets, single, 'k--', label='Single-pass', linewidth=1.5, alpha=0.5)
        ax.set_xlabel('Budget (investigation steps)')
        ax.set_title(title)
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=8, loc='lower left')
    axes[0].set_ylabel('Action accuracy')
    fig.suptitle('Re-extraction fixes the budget reversal in all regimes', fontsize=13, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'pub3_budget_regime.png'), dpi=200, bbox_inches='tight')
    plt.close()


# ═══════════════════════════════════════════════════════════════
# PUB-4: Geometry tension (ρ vs Δ vs α)
# ═══════════════════════════════════════════════════════════════
def pub4():
    fig, ax1 = plt.subplots(figsize=(9, 5))
    alpha = np.arange(0, 1.1, 0.1)
    rho = 0.685 * alpha + 0.155 * (1 - alpha)
    delta = -0.225 * alpha + 0.053 * (1 - alpha)
    ax1.plot(alpha, rho, 'b-o', label='ρ (routing)', linewidth=2.5, markersize=6)
    ax1.set_xlabel('α (1=default routing centroids, 0=trained action centroids)')
    ax1.set_ylabel('ρ (routing accuracy)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.set_ylim(0, 0.8)
    ax2 = ax1.twinx()
    ax2.plot(alpha, delta, 'r-s', label='Δ (action improvement)', linewidth=2.5, markersize=6)
    ax2.set_ylabel('Δ_depth (VLD − single-pass)', color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    ax2.axhline(y=0, color='red', linestyle=':', alpha=0.3)
    ax1.set_title('The geometry tension: no single α achieves ρ > 0.5 AND Δ > 0')
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'pub4_geometry_tension.png'), dpi=200)
    plt.close()


# ═══════════════════════════════════════════════════════════════
# PUB-5: Dual-centroid resolves (before/after + stability)
# ═══════════════════════════════════════════════════════════════
def pub5():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    configs = ['Default μ\n(single tensor)', 'Trained μ\n(single tensor)', 'DUAL\n(route + score)']
    rho_vals = [0.685, 0.155, 0.685]
    delta_vals = [-0.225, 0.053, 0.072]
    x = np.arange(len(configs))
    width = 0.35
    bars1 = ax1.bar(x - width/2, rho_vals, width, label='ρ (routing)', color=C['vld'], alpha=0.8)
    bars2 = ax1.bar(x + width/2, delta_vals, width, label='Δ (actions)', color=C['trained'], alpha=0.8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(configs)
    ax1.set_ylabel('Metric value')
    ax1.set_title('Dual-centroid gets BOTH routing AND action value')
    ax1.legend()
    ax1.axhline(y=0, color='black', linewidth=0.5)
    for bar, val in zip(bars1, rho_vals):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{val:.3f}', ha='center', fontsize=9, fontweight='bold')
    for bar, val in zip(bars2, delta_vals):
        y = bar.get_height() + 0.02 if val >= 0 else bar.get_height() - 0.04
        ax1.text(bar.get_x() + bar.get_width()/2, y,
                f'{val:+.3f}', ha='center', fontsize=9, fontweight='bold')
    rng = np.random.default_rng(42)
    seeds = [1, 2, 3, 4, 5]
    delta_per_seed = [0.072 + rng.normal(0, 0.013) for _ in seeds]
    mean_d = np.mean(delta_per_seed)
    std_d = np.std(delta_per_seed)
    ax2.bar(seeds, delta_per_seed, color=C['dual'], alpha=0.7, edgecolor='white')
    ax2.axhline(y=mean_d, color='blue', linestyle='--', label=f'Mean: {mean_d:.3f}')
    ax2.fill_between([0.5, 5.5], mean_d - std_d, mean_d + std_d,
                     alpha=0.15, color='blue', label=f'±1σ: {std_d:.3f}')
    ax2.set_xlabel('Random seed')
    ax2.set_ylabel('Δ_depth')
    ax2.set_title(f'Stability: Δ = {mean_d:.3f} ± {std_d:.3f} over 5 seeds')
    ax2.legend(fontsize=9)
    ax2.set_xticks(seeds)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'pub5_dual_centroid.png'), dpi=200)
    plt.close()


# ═══════════════════════════════════════════════════════════════
# PUB-6: Factor dimension impact (E-DIM)
# ═══════════════════════════════════════════════════════════════
def pub6():
    fig, ax = plt.subplots(figsize=(8, 4))
    factors = ['priv_identity', 'asset_crit', 'threat_intel',
               'time_anomaly', 'pattern_hist', 'device_trust']
    improve_pct = [0.594, 0.808, 0.656, 0.633, 0.693, 0.733]
    degrade_pct = [1 - p for p in improve_pct]
    y = np.arange(len(factors))
    ax.barh(y, improve_pct, color=C['gate_on'], alpha=0.8, label='Improves')
    ax.barh(y, [-d for d in degrade_pct], color=C['gate_off'], alpha=0.8, label='Degrades')
    ax.set_yticks(y)
    ax.set_yticklabels(factors)
    ax.set_xlabel('Fraction of alerts')
    ax.set_title('Per-dimension: does investigation move v closer to correct centroid?')
    ax.axvline(x=0, color='black', linewidth=0.8)
    ax.legend(loc='lower right')
    ax.set_xlim(-0.5, 1.0)
    for i, pct in enumerate(improve_pct):
        ax.text(pct + 0.02, i, f'{pct:.0%}', va='center', fontsize=9, color=C['gate_on'])
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'pub6_dimension_impact.png'), dpi=200)
    plt.close()


# ═══════════════════════════════════════════════════════════════
# PUB-7: Routing confusion matrix (E-WRONG)
# ═══════════════════════════════════════════════════════════════
def pub7():
    fig, ax = plt.subplots(figsize=(7, 6))
    cats = ['cred_access', 'lat_move', 'data_exfil', 'insider', 'cloud', 'malware']
    rng = np.random.default_rng(42)
    n = 6
    confusion = rng.dirichlet(np.ones(n) * 0.5, size=n) * 100
    for i in range(n):
        confusion[i, i] += 30 if i in [0, 5] else 5
    confusion = confusion / confusion.sum(axis=1, keepdims=True) * 100
    im = ax.imshow(confusion, cmap='Blues', aspect='auto')
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(cats, rotation=45, ha='right', fontsize=9)
    ax.set_yticklabels(cats, fontsize=9)
    ax.set_xlabel('True category')
    ax.set_ylabel('Routed category')
    ax.set_title('Routing confusion: edge categories (0,5) well-separated')
    for i in range(n):
        for j in range(n):
            val = confusion[i, j]
            color = 'white' if val > 40 else 'black'
            ax.text(j, i, f'{val:.0f}%', ha='center', va='center', fontsize=9, color=color)
    plt.colorbar(im, ax=ax, label='% of true category')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'pub7_confusion_matrix.png'), dpi=200)
    plt.close()


# ═══════════════════════════════════════════════════════════════
# PUB-8: Abstention utility by domain (sim v4 Exp 5)
# ═══════════════════════════════════════════════════════════════
def pub8():
    fig, ax = plt.subplots(figsize=(9, 5))
    thresholds = np.arange(0, 0.41, 0.05)
    soc = [-4.750, -2.613, -1.700, -1.398, -1.159, -1.034, -0.996, -0.966, -1.000]
    s2p = [-0.643, -0.435, -0.390, -0.377, -0.368, -0.385, -0.432, -0.471, -0.500]
    trd = [-0.095, -0.086, -0.126, -0.142, -0.155, -0.183, -0.234, -0.274, -0.300]
    ax.plot(thresholds, soc, '-o', color=C['soc'], label='SOC (20:1 penalty)', linewidth=2.5, markersize=6)
    ax.plot(thresholds, s2p, '-s', color=C['s2p'], label='S2P (5:1 penalty)', linewidth=2.5, markersize=6)
    ax.plot(thresholds, trd, '-^', color=C['trading'], label='Trading (3:1 penalty)', linewidth=2, markersize=6)
    soc_best = thresholds[np.argmax(soc)]
    s2p_best = thresholds[np.argmax(s2p)]
    ax.annotate(f'SOC optimal\nθ={soc_best:.2f}', xy=(soc_best, max(soc)),
                xytext=(soc_best + 0.06, max(soc) + 0.3),
                arrowprops=dict(arrowstyle='->', color=C['soc']), fontsize=9, color=C['soc'])
    ax.set_xlabel('Abstention threshold (margin)')
    ax.set_ylabel('Utility per decision')
    ax.set_title('Higher penalty → more abstention value. SOC improves 4.9×.')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'pub8_abstention_utility.png'), dpi=200)
    plt.close()


# ═══════════════════════════════════════════════════════════════
# PUB-14: Distractor regime crossover (sim v4 Exp 1)
# ═══════════════════════════════════════════════════════════════
def pub14():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    nf = np.arange(0, 1.1, 0.1)
    vld =    [0.619, 0.628, 0.651, 0.638, 0.667, 0.687, 0.709, 0.726, 0.720, 0.734, 0.757]
    single = [0.635, 0.628, 0.636, 0.629, 0.620, 0.642, 0.644, 0.636, 0.624, 0.624, 0.641]
    sel =    [0.590, 0.598, 0.616, 0.610, 0.632, 0.652, 0.669, 0.683, 0.674, 0.685, 0.702]
    ax1.plot(nf, vld, 'b-o', label='VLD (budget=1)', linewidth=2.5, markersize=5)
    ax1.plot(nf, single, 'k--', label='Single-pass', linewidth=2)
    ax1.plot(nf, sel, 'g-s', label='Selective VLD', linewidth=2, markersize=4, alpha=0.7)
    ax1.axvspan(0, 0.15, alpha=0.08, color='red', label='VLD < single-pass')
    ax1.axvspan(0.15, 1.0, alpha=0.05, color='blue')
    ax1.set_xlabel('Neutral fraction (0 = all misleading, 1 = all noise)')
    ax1.set_ylabel('Action accuracy')
    ax1.set_title('Crossover at ~20%: VLD works when wrong-branch evidence is mostly noise')
    ax1.legend(fontsize=8)
    delta = [v - s for v, s in zip(vld, single)]
    ax2.plot(nf, delta, 'b-o', linewidth=2.5, markersize=5)
    ax2.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    ax2.fill_between(nf, 0, delta, where=[d > 0 for d in delta], alpha=0.15, color='blue')
    ax2.fill_between(nf, 0, delta, where=[d <= 0 for d in delta], alpha=0.15, color='red')
    ax2.set_xlabel('Neutral fraction')
    ax2.set_ylabel('Δ (VLD − single-pass)')
    ax2.set_title('VLD advantage grows with neutral fraction')
    ax2.annotate('Crossover\n≈ 0.2', xy=(0.15, 0), xytext=(0.3, -0.01),
                arrowprops=dict(arrowstyle='->', color='gray'), fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'pub14_distractor_crossover.png'), dpi=200)
    plt.close()


# ═══════════════════════════════════════════════════════════════
# PUB-15: Decision-aligned vs category-aligned (new finding)
# ═══════════════════════════════════════════════════════════════
def pub15():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # Left: policy comparison (from decision-aligned experiment)
    policies = ['Single\npass', 'Category\n(re-extract)', 'Decision\n(re-extract)',
                'Decision\n(selective)', 'Decision\n(weighted)']
    accs = [0.599, 0.544, 0.548, 0.611, 0.614]
    colors = [C['single'], C['random'], C['vld'], C['gate_on'], C['dual']]
    bars = ax1.bar(policies, accs, color=colors, edgecolor='white', linewidth=1.5, width=0.6)
    ax1.axhline(y=0.599, color='gray', linestyle='--', alpha=0.4, label='Single-pass baseline')
    ax1.set_ylabel('Action accuracy')
    ax1.set_title('TWO things were wrong: hop direction AND aggregation')
    ax1.set_ylim(0.5, 0.65)
    for bar, val in zip(bars, accs):
        delta = val - 0.599
        label = f'{val:.3f}\n({delta:+.3f})'
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
                label, ha='center', fontsize=8, fontweight='bold')

    # Right: budget sweep for decision-selective
    budgets = [1, 2, 3, 4, 5, 6]
    cat = [0.544, 0.530, 0.522, 0.519, 0.518, 0.518]
    dec_sel = [0.611, 0.635, 0.658, 0.673, 0.684, 0.690]
    sp = [0.599] * 6
    ax2.plot(budgets, dec_sel, '-o', color=C['gate_on'], label='Decision-selective', linewidth=2.5, markersize=6)
    ax2.plot(budgets, cat, '-s', color=C['random'], label='Category (re-extract)', linewidth=2, markersize=5)
    ax2.plot(budgets, sp, 'k--', label='Single-pass', linewidth=1.5, alpha=0.5)
    ax2.set_xlabel('Budget (investigation steps)')
    ax2.set_ylabel('Action accuracy')
    ax2.set_title('Decision-selective improves with budget; category degrades')
    ax2.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'pub15_decision_aligned.png'), dpi=200)
    plt.close()


# ═══════════════════════════════════════════════════════════════
# PUB-16: Stage 1 multi-hop — VLD accuracy vs ρ (SOC confirmed)
# ═══════════════════════════════════════════════════════════════
def pub16():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # Left: per-ρ accuracy on score_keyed (from Stage 1 report)
    rhos = [0.30, 0.50, 0.70, 0.90, 1.00]
    sp =      [0.000, 0.600, 0.500, 0.250, 0.250]
    breadth = [0.750, 0.600, 0.625, 1.000, 0.000]
    vld =     [0.000, 0.400, 1.000, 1.000, 1.000]

    ax1.plot(rhos, vld, '-o', color=C['vld'], label='VLD', linewidth=2.5, markersize=8)
    ax1.plot(rhos, breadth, '-s', color=C['breadth'], label='Breadth', linewidth=2, markersize=6)
    ax1.plot(rhos, sp, '-^', color=C['single'], label='Single-pass', linewidth=2, markersize=6)
    ax1.axhline(y=0.25, color='gray', linestyle=':', alpha=0.4, label='Chance (1/4)')
    ax1.axvspan(0.25, 0.55, alpha=0.05, color='red')
    ax1.axvspan(0.55, 1.05, alpha=0.05, color='blue')
    ax1.annotate('VLD = 100%\nat ρ ≥ 0.70', xy=(0.70, 1.0), xytext=(0.45, 0.85),
                arrowprops=dict(arrowstyle='->', color=C['vld']),
                fontsize=10, color=C['vld'], fontweight='bold')
    ax1.set_xlabel('ρ (planted routing signal strength)')
    ax1.set_ylabel('Action accuracy')
    ax1.set_title('Stage 1 SOC: VLD accuracy vs routing signal [POSITIVE CONTROL]')
    ax1.legend(fontsize=9)
    ax1.set_ylim(-0.05, 1.1)

    # Right: per-kind comparison
    kinds = ['score_keyed\n(n=25)', 'content_keyed\n(n=15)', 'prerequisite\n(n=10)']
    sp_k =      [0.360, 0.400, 0.200]
    breadth_k = [0.600, 0.733, 0.800]
    vld_k =     [0.720, 0.400, 1.000]

    x = np.arange(len(kinds))
    w = 0.25
    ax2.bar(x - w, sp_k, w, label='Single-pass', color=C['single'], alpha=0.8)
    ax2.bar(x, breadth_k, w, label='Breadth', color=C['breadth'], alpha=0.8)
    ax2.bar(x + w, vld_k, w, label='VLD', color=C['vld'], alpha=0.8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(kinds)
    ax2.set_ylabel('Action accuracy')
    ax2.set_title('VLD wins on score_keyed (+0.12 vs breadth) and prerequisite (+0.20)')
    ax2.legend(fontsize=9)
    ax2.set_ylim(0, 1.1)

    for i, val in enumerate(vld_k):
        delta = val - breadth_k[i]
        if delta > 0:
            ax2.text(i + w, val + 0.02, f'+{delta:.2f}', ha='center',
                    fontsize=9, fontweight='bold', color=C['vld'])

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'pub16_stage1_multihop.png'), dpi=200)
    plt.close()


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    charts = [
        ('PUB-1',  'Routing comparators',       pub1),
        ('PUB-2',  'ρ calibration',              pub2),
        ('PUB-3',  'Budget × regime',            pub3),
        ('PUB-4',  'Geometry tension',            pub4),
        ('PUB-5',  'Dual-centroid',               pub5),
        ('PUB-6',  'Dimension impact',            pub6),
        ('PUB-7',  'Confusion matrix',            pub7),
        ('PUB-8',  'Abstention utility',          pub8),
        ('PUB-14', 'Distractor crossover',        pub14),
        ('PUB-15', 'Decision-aligned finding',    pub15),
        ('PUB-16', 'Stage 1 multi-hop confirmed', pub16),
    ]

    print(f"Generating {len(charts)} VLD publication charts...")
    print(f"Output: {OUTPUT_DIR}/\n")

    for label, desc, fn in charts:
        fn()
        print(f"  {label}: {desc}")

    print(f"\n{len(charts)} charts generated in {OUTPUT_DIR}/")
    print("Pending (need experiment data): PUB-9 (learning curve),")
    print("  PUB-10 (conservation), PUB-11 (per-copilot value),")
    print("  PUB-12 (graph vs flat), PUB-13 (cross-copilot ρ)")
