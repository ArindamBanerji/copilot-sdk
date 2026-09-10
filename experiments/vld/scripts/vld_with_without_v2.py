"""
VLD With-Without Case Study Generator v1
==========================================
For each copilot's Stage 1 data, find scenarios where:
  - Single-pass gets it WRONG
  - VLD gets it RIGHT
Produce human-readable case studies showing the investigation trace,
factor movement, and decision change.

THIS IS THE CREDIBILITY CONTENT for demos and publications.

Usage: python vld_with_without_v1.py [stage1_json] [copilot_name] [output_dir]

Produces:
  - case_studies_{copilot}.md — narrative case studies
  - pub_ww_{copilot}_factor_movement.png — factor bar charts
  - pub_ww_{copilot}_trajectory.png — decision trajectory
  - pub_ww_{copilot}_aggregate.png — with-without summary
"""

import json, sys, os
import numpy as np
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.size': 11, 'axes.facecolor': '#FAFAFA',
    'figure.facecolor': '#FFFFFF', 'axes.grid': True,
    'grid.alpha': 0.3, 'axes.spines.top': False, 'axes.spines.right': False,
})

C = {'vld': '#2563EB', 'sp': '#6B7280', 'correct': '#059669',
     'wrong': '#DC2626', 'hop': '#D97706', 'enriched': '#7C3AED'}


# ── Utilities ──

def load_stage1(path):
    with open(path) as f:
        return json.load(f)['scenarios']

def get_fv(s):
    f = s['alert']['surface_factors']
    keys = sorted(f.keys())
    return np.array([f[k] for k in keys]), keys

def apply_hop(v, hop, keys):
    ef = hop.get('factor_enriched')
    nv = hop.get('factor_new_value')
    if ef and nv is not None and ef in keys:
        out = v.copy(); out[keys.index(ef)] = nv; return out
    return v.copy()

def apply_all_hops(v, hops, keys):
    vt = v.copy()
    for h in hops:
        vt = apply_hop(vt, h, keys)
    return vt

def build_enriched_centroids(scenarios, keys):
    av = defaultdict(list)
    for s in scenarios:
        if s.get('surface_only_resolvable'): continue
        a = s['decision_tree']['ground_truth_action']
        v, _ = get_fv(s)
        v_enr = apply_all_hops(v, s['decision_tree'].get('hops', []), keys)
        av[a].append(v_enr)
    actions = sorted(av.keys())
    ai = {a: i for i, a in enumerate(actions)}
    rng = np.random.default_rng(42)
    mu = np.zeros((len(actions), len(keys)))
    for a in actions:
        vecs = av[a]
        mu[ai[a]] = np.mean(vecs, axis=0) if len(vecs) >= 2 else rng.uniform(0.2, 0.8, len(keys))
    return mu, actions, ai

def score_best(v, mu, actions):
    d = [np.linalg.norm(v - mu[i]) for i in range(len(actions))]
    b = int(np.argmin(d))
    return actions[b], d[b], d


# ── EXP-WW-1: Find With-Without Cases ──

def find_cases(scenarios, mu, actions, keys):
    """Find scenarios where SP wrong + VLD right."""
    cases = {'vld_saves': [], 'vld_hurts': [], 'both_right': [], 'both_wrong': []}

    multihop = [s for s in scenarios
                if not s.get('surface_only_resolvable')
                and len(s['decision_tree'].get('hops', [])) > 0]

    for s in multihop:
        gt = s['decision_tree']['ground_truth_action']
        hops = s['decision_tree'].get('hops', [])
        v_surface, _ = get_fv(s)
        v_enriched = apply_all_hops(v_surface, hops, keys)

        sp_action, sp_dist, sp_dists = score_best(v_surface, mu, actions)
        vld_action, vld_dist, vld_dists = score_best(v_enriched, mu, actions)

        sp_correct = (sp_action == gt)
        vld_correct = (vld_action == gt)

        record = {
            'scenario': s,
            'gt': gt,
            'sp_action': sp_action, 'sp_correct': sp_correct,
            'sp_dist': sp_dist, 'sp_dists': sp_dists,
            'vld_action': vld_action, 'vld_correct': vld_correct,
            'vld_dist': vld_dist, 'vld_dists': vld_dists,
            'v_surface': v_surface, 'v_enriched': v_enriched,
        }

        if not sp_correct and vld_correct:
            cases['vld_saves'].append(record)
        elif sp_correct and not vld_correct:
            cases['vld_hurts'].append(record)
        elif sp_correct and vld_correct:
            cases['both_right'].append(record)
        else:
            cases['both_wrong'].append(record)

    return cases


# ── EXP-WW-2: Generate Case Study Narratives ──

def generate_case_studies(cases, keys, copilot, output_dir, mu, actions):
    """Write human-readable case studies to markdown."""
    lines = []
    lines.append(f"# VLD With-Without Case Studies — {copilot.upper()}")
    lines.append(f"**Generated from Stage 1 multi-hop scenarios**")
    lines.append(f"**[PLANTED POSITIVE CONTROL — not production data]**\n")

    # Aggregate summary
    total = sum(len(v) for v in cases.values())
    lines.append(f"## Summary\n")
    lines.append(f"| Category | Count | % |")
    lines.append(f"|---|---|---|")
    for cat, label in [('vld_saves', 'VLD saves (SP wrong, VLD right)'),
                        ('vld_hurts', 'VLD hurts (SP right, VLD wrong)'),
                        ('both_right', 'Both correct'),
                        ('both_wrong', 'Both wrong')]:
        n = len(cases[cat])
        pct = n / total * 100 if total else 0
        lines.append(f"| {label} | {n} | {pct:.0f}% |")
    lines.append(f"| **Total multi-hop** | **{total}** | |")
    lines.append("")

    # Detailed case studies for VLD saves
    lines.append(f"## Case Studies: VLD Saves\n")
    if not cases['vld_saves']:
        lines.append(f"*No scenarios where SP wrong + VLD right on this dataset.*")
        lines.append(f"*This may indicate centroid sparsity or insufficient conditional structure.*\n")
    else:
        lines.append(f"*Scenarios where single-pass gets it wrong and VLD gets it right.*\n")

    for i, case in enumerate(cases['vld_saves'][:8], 1):
        s = case['scenario']
        hops = s['decision_tree'].get('hops', [])
        lines.append(f"### Case {i}: {s['scenario_id']}")
        lines.append(f"**Type:** {s.get('scenario_type', 'unknown')}")
        lines.append(f"**Kind:** {s['branching_kind']} | **rho:** {s['rho_planted']}\n")
        lines.append(f"**Description:** {s.get('description', '')}\n")

        # Without VLD
        lines.append(f"#### WITHOUT VLD (single-pass)")
        lines.append(f"- Action: **{case['sp_action']}** ❌ (ground truth: {case['gt']})")
        lines.append(f"- Based on surface factors only")
        lines.append(f"- Distance to nearest centroid: {case['sp_dist']:.4f}\n")

        # With VLD — show intermediate action after each hop
        lines.append(f"#### WITH VLD (investigation)")
        v_running = case['v_surface'].copy()
        for j, hop in enumerate(hops):
            ef = hop.get('factor_enriched', '?')
            ev = hop.get('evidence_found', '?')
            narr = hop.get('narration', '')
            new_val = hop.get('factor_new_value')

            if ef in keys and new_val is not None:
                old_val = v_running[keys.index(ef)]
                lines.append(f"- **Hop {j+1}:** {narr}")
                lines.append(f"  - Checked: {hop.get('evidence_source', '?')}")
                lines.append(f"  - Found: {ev}")
                lines.append(f"  - Factor `{ef}`: {old_val:.3f} → {new_val:.3f}")
                v_running = apply_hop(v_running, hop, keys)
            else:
                lines.append(f"- **Hop {j+1}:** {narr}")
                lines.append(f"  - Checked: {hop.get('evidence_source', '?')}")
                lines.append(f"  - Found: {ev}")
                lines.append(f"  - Factor: {ef} (not in factor list — no enrichment)")
                v_running = apply_hop(v_running, hop, keys)

            # Show intermediate action after this hop
            int_action, int_dist, _ = score_best(v_running, mu, actions)
            marker = "✅" if int_action == case['gt'] else "→"
            lines.append(f"  - Action after hop {j+1}: **{int_action}** {marker} (dist: {int_dist:.4f})")

        lines.append(f"\n- Action: **{case['vld_action']}** ✅")
        lines.append(f"- Distance to nearest centroid: {case['vld_dist']:.4f}")

        # The aha moment
        lines.append(f"\n**Why VLD changed the decision:** {s['decision_tree'].get('reasoning', '')}")

        # Factor movement
        lines.append(f"\n**Factor movement:**")
        lines.append(f"| Factor | Surface | Enriched | Δ |")
        lines.append(f"|---|---|---|---|")
        for k, (sv, ev) in enumerate(zip(case['v_surface'], case['v_enriched'])):
            delta = ev - sv
            marker = " ←" if abs(delta) > 0.05 else ""
            lines.append(f"| {keys[k]} | {sv:.3f} | {ev:.3f} | {delta:+.3f}{marker} |")
        lines.append("")

    # VLD hurts cases (if any)
    if cases['vld_hurts']:
        lines.append(f"\n## Cases Where VLD Hurts\n")
        lines.append(f"*{len(cases['vld_hurts'])} scenarios where SP was right but VLD got it wrong.*\n")
        for i, case in enumerate(cases['vld_hurts'][:3], 1):
            s = case['scenario']
            lines.append(f"### Hurt Case {i}: {s['scenario_id']}")
            lines.append(f"- SP: **{case['sp_action']}** ✅ | VLD: **{case['vld_action']}** ❌ | GT: {case['gt']}")
            lines.append(f"- Kind: {s['branching_kind']} | rho: {s['rho_planted']}")
            lines.append(f"- Why: investigation moved factors in wrong direction\n")

    path = os.path.join(output_dir, f'case_studies_{copilot}.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"  Case studies: {path} ({len(cases['vld_saves'])} saves, {len(cases['vld_hurts'])} hurts)")
    return path


# ── EXP-WW-3: Factor Movement Chart ──

def chart_factor_movement(cases, keys, copilot, output_dir):
    """Bar chart showing factor values before/after for top VLD-saves cases."""
    saves = cases['vld_saves'][:4]
    if not saves:
        print(f"  No VLD-saves cases for factor movement chart")
        return

    n_cases = len(saves)
    fig, axes = plt.subplots(1, n_cases, figsize=(5 * n_cases, 5), sharey=True)
    if n_cases == 1:
        axes = [axes]

    for ax, case in zip(axes, saves):
        x = np.arange(len(keys))
        w = 0.35
        ax.barh(x - w/2, case['v_surface'], w, color=C['sp'], label='Surface', alpha=0.8)
        ax.barh(x + w/2, case['v_enriched'], w, color=C['vld'], label='Enriched', alpha=0.8)
        ax.set_yticks(x)
        ax.set_yticklabels([k[:12] for k in keys], fontsize=8)
        ax.set_xlabel('Factor value')
        sid = case['scenario']['scenario_id']
        ax.set_title(f'{sid}\nSP: {case["sp_action"]} ❌ → VLD: {case["vld_action"]} ✅', fontsize=9)
        ax.legend(fontsize=7)

        # Highlight changed factors
        for i, (sv, ev) in enumerate(zip(case['v_surface'], case['v_enriched'])):
            if abs(ev - sv) > 0.05:
                ax.annotate(f'{ev-sv:+.2f}', xy=(max(sv, ev) + 0.02, i + w/2),
                           fontsize=7, color=C['enriched'], fontweight='bold')

    fig.suptitle(f'{copilot.upper()}: Factor movement in VLD-saves cases', fontsize=12, y=1.02)
    plt.tight_layout()
    path = os.path.join(output_dir, f'pub_ww_{copilot}_factor_movement.png')
    plt.savefig(path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  Factor movement chart: {path}")


# ── EXP-WW-4: Aggregate With-Without Chart ──

def chart_aggregate(cases, copilot, output_dir):
    """Stacked bar showing VLD saves / hurts / both right / both wrong."""
    cats = ['VLD saves', 'VLD hurts', 'Both right', 'Both wrong']
    vals = [len(cases['vld_saves']), len(cases['vld_hurts']),
            len(cases['both_right']), len(cases['both_wrong'])]
    colors = [C['correct'], C['wrong'], C['sp'], '#D1D5DB']
    total = sum(vals)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Bar chart
    bars = ax1.bar(cats, vals, color=colors, edgecolor='white', width=0.6)
    ax1.set_ylabel('Scenarios')
    ax1.set_title(f'{copilot.upper()}: With vs Without VLD ({total} multi-hop scenarios)')
    for bar, val in zip(bars, vals):
        pct = val / total * 100 if total else 0
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{val}\n({pct:.0f}%)', ha='center', fontsize=10, fontweight='bold')

    # By branching kind
    kind_data = defaultdict(lambda: {'saves': 0, 'hurts': 0, 'both_right': 0, 'both_wrong': 0})
    for cat_key, label in [('vld_saves', 'saves'), ('vld_hurts', 'hurts'),
                           ('both_right', 'both_right'), ('both_wrong', 'both_wrong')]:
        for case in cases[cat_key]:
            kind = case['scenario']['branching_kind']
            kind_data[kind][label] += 1

    kinds = sorted(kind_data.keys())
    x = np.arange(len(kinds))
    w = 0.2
    for i, (label, color) in enumerate(zip(['saves', 'hurts', 'both_right', 'both_wrong'],
                                           [C['correct'], C['wrong'], C['sp'], '#D1D5DB'])):
        vals_k = [kind_data[k][label] for k in kinds]
        ax2.bar(x + i * w, vals_k, w, color=color, label=label.replace('_', ' ').title(),
                edgecolor='white')
    ax2.set_xticks(x + 1.5 * w)
    ax2.set_xticklabels(kinds, fontsize=9)
    ax2.set_ylabel('Scenarios')
    ax2.set_title('Breakdown by branching kind')
    ax2.legend(fontsize=8)

    plt.tight_layout()
    path = os.path.join(output_dir, f'pub_ww_{copilot}_aggregate.png')
    plt.savefig(path, dpi=200)
    plt.close()
    print(f"  Aggregate chart: {path}")


# ── EXP-WW-5: Decision Trajectory (2D projection) ──

def chart_trajectory(cases, mu, actions, keys, copilot, output_dir):
    """Project factor space to 2D, show surface→enriched trajectories."""
    saves = cases['vld_saves']
    if len(saves) < 2:
        print(f"  Not enough VLD-saves for trajectory chart")
        return

    # Use the 2 factors with highest variance across saves
    all_vecs = np.array([c['v_surface'] for c in saves] + [c['v_enriched'] for c in saves])
    var = np.var(all_vecs, axis=0)
    top2 = np.argsort(-var)[:2]
    dim1, dim2 = top2

    fig, ax = plt.subplots(figsize=(9, 7))

    # Plot centroids
    for i, a in enumerate(actions):
        ax.scatter(mu[i, dim1], mu[i, dim2], s=200, marker='*', zorder=5,
                  label=f'μ({a})', edgecolors='black', linewidth=0.5)
        ax.annotate(a, (mu[i, dim1] + 0.02, mu[i, dim2] + 0.02), fontsize=8)

    # Plot trajectories
    for case in saves[:10]:
        s0 = case['v_surface']
        sf = case['v_enriched']
        ax.scatter(s0[dim1], s0[dim2], c=C['sp'], s=40, alpha=0.6, zorder=3)
        ax.scatter(sf[dim1], sf[dim2], c=C['vld'], s=40, alpha=0.8, zorder=3)
        ax.annotate('', xy=(sf[dim1], sf[dim2]), xytext=(s0[dim1], s0[dim2]),
                   arrowprops=dict(arrowstyle='->', color=C['enriched'], alpha=0.5, lw=1.5))

    ax.set_xlabel(f'{keys[dim1]}')
    ax.set_ylabel(f'{keys[dim2]}')
    ax.set_title(f'{copilot.upper()}: Decision trajectory (surface → enriched)\n'
                f'Gray dots = surface (SP wrong), Blue dots = enriched (VLD right)')
    ax.legend(fontsize=8, loc='best')

    plt.tight_layout()
    path = os.path.join(output_dir, f'pub_ww_{copilot}_trajectory.png')
    plt.savefig(path, dpi=200)
    plt.close()
    print(f"  Trajectory chart: {path}")


# ── EXP-WW-6: Per-rho With-Without Breakdown ──

def chart_per_rho(cases, copilot, output_dir):
    """Show VLD saves rate by rho — proves value scales with routing signal."""
    rho_data = defaultdict(lambda: {'saves': 0, 'total': 0})
    for cat_key in ['vld_saves', 'vld_hurts', 'both_right', 'both_wrong']:
        for case in cases[cat_key]:
            rho = case['scenario']['rho_planted']
            rho_data[rho]['total'] += 1
            if cat_key == 'vld_saves':
                rho_data[rho]['saves'] += 1

    rhos = sorted(rho_data.keys())
    if len(rhos) < 3:
        print(f"  Not enough rho values for per-rho chart")
        return

    rates = [rho_data[r]['saves'] / rho_data[r]['total'] if rho_data[r]['total'] else 0 for r in rhos]
    totals = [rho_data[r]['total'] for r in rhos]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar([f'rho={r}' for r in rhos], rates, color=C['correct'], edgecolor='white', width=0.6)
    ax.set_ylabel('VLD saves rate')
    ax.set_title(f'{copilot.upper()}: VLD saves more decisions at higher rho')
    ax.set_ylim(0, 1.1)
    for bar, rate, n in zip(bars, rates, totals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{rate:.0%}\n(n={n})', ha='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    path = os.path.join(output_dir, f'pub_ww_{copilot}_per_rho.png')
    plt.savefig(path, dpi=200)
    plt.close()
    print(f"  Per-rho chart: {path}")


# ── Main ──

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'data/soc_multihop_stage1.json'
    copilot = sys.argv[2] if len(sys.argv) > 2 else 'soc'
    out = sys.argv[3] if len(sys.argv) > 3 else './pub_charts'
    os.makedirs(out, exist_ok=True)

    print(f"Loading: {path}")
    S = load_stage1(path)
    _, keys = get_fv(S[0])
    mu, actions, ai = build_enriched_centroids(S, keys)
    print(f"Copilot: {copilot}, Scenarios: {len(S)}, Actions: {actions}")

    # Find with-without cases
    cases = find_cases(S, mu, actions, keys)
    print(f"\nWith-Without breakdown:")
    for cat, items in cases.items():
        print(f"  {cat}: {len(items)}")

    # Generate outputs
    print(f"\nGenerating outputs in {out}/")
    generate_case_studies(cases, keys, copilot, out, mu, actions)
    chart_factor_movement(cases, keys, copilot, out)
    chart_aggregate(cases, copilot, out)
    chart_trajectory(cases, mu, actions, keys, copilot, out)
    chart_per_rho(cases, copilot, out)

    print(f"\nDone. Case studies + 4 charts for {copilot}.")
