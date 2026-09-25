"""Render the twelve Group B/C figures and eleven-section evidence report.

Reads completed JSON results only. Run with -B after the nine experiments.
"""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'experiments/vld'
CHARTS = OUT / 'charts'
FILES = dict(ri5='ri5_rich_k_state', ri6='ri6_temporal_decay', ri7='ri7_category_conditional',
             ri8='ri8_sequence_aware', ri9='ri9_regime_indexed', rv4='rv4_risk_sensitive',
             rv5='rv5_hierarchical', rv8='rv8_adaptive_q', rv9='rv9_mcts')
NAMES = dict(dataops='DataOps', trading='Trading', purchasing='Purchasing', soc='SOC', s2p='S2P')
COLORS = ['#2563a6', '#d07823', '#27917e', '#9b5f9e', '#65758a']


def save(fig, name):
    fig.savefig(CHARTS / name, dpi=180, facecolor='white', bbox_inches='tight')
    plt.close(fig)


def grouped(data, variants, labels, metric, ylabel, title, filename):
    fig, ax = plt.subplots(figsize=(10, 5))
    cats = list(data)
    x = np.arange(len(cats))
    width = .8/len(variants)
    for i, (v, label) in enumerate(zip(variants, labels)):
        vals = [100*data[c][v][metric] for c in cats]
        bars = ax.bar(x + (i-(len(variants)-1)/2)*width, vals, width, label=label, color=COLORS[i])
        if metric == 'starvation':
            ax.bar_label(bars, labels=[f'{v:.1f}' for v in vals], padding=3, fontsize=9)
    ax.set(xticks=x, xticklabels=[NAMES[c] for c in cats], ylabel=ylabel, title=title)
    ax.legend(ncol=min(3, len(variants)), frameon=False, loc='upper center', bbox_to_anchor=(.5, 1.01))
    ax.set_ylim(0, 60 if metric == 'starvation' else max(100, ax.get_ylim()[1]*1.15))
    fig.tight_layout()
    save(fig, filename)


def curves(rows, title, filename):
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, (name, row) in enumerate(rows.items()):
        cps = row['checkpoints']
        x = [r['decision_count'] for r in cps]
        y = np.array([100*r['routing_quality_mean'] for r in cps])
        std = np.array([100*r['routing_quality_std'] for r in cps])
        ax.plot(x, y, '-o', color=COLORS[i], label=name, markersize=4)
        ax.fill_between(x, np.maximum(0, y-std), np.minimum(100, y+std), color=COLORS[i], alpha=.12)
    ax.axvline(250, color='#555', linestyle='--', linewidth=1)
    ax.set(xlabel='Training decisions', ylabel='Routing quality (%)', title=title, ylim=(0, 100))
    ax.legend(frameon=False)
    fig.tight_layout()
    save(fig, filename)


def charts(all_data):
    plt.rcParams.update({'figure.facecolor': 'white', 'axes.facecolor': '#fafbfd', 'axes.spines.top': False,
                         'axes.spines.right': False, 'axes.grid': True, 'axes.axisbelow': True,
                         'grid.alpha': .18, 'font.size': 10, 'axes.titlesize': 14})
    CHARTS.mkdir(exist_ok=True)
    d = {k: v['results'] for k, v in all_data.items()}
    variants = ['GREEDY-SCALAR-K', 'THOMPSON-SCALAR-K', 'THOMPSON-RICH-K']
    labels = ['Scalar greedy', 'Scalar Thompson', 'Rich Thompson']
    grouped(d['ri5'], variants, labels, 'starvation', 'Never-read cells (%)', 'RI-5 · Starvation', 'pub_ri5_starvation_comparison.png')
    fig, ax = plt.subplots(figsize=(10, 6))
    points = {c: [] for c in d['ri5']}
    for i, v in enumerate(variants):
        for j, (c, rows) in enumerate(d['ri5'].items()):
            x, y = 100*rows[v]['starvation'], 100*rows[v]['final_routing_mean']
            points[c].append((x, y))
            ax.scatter(x, y, color=COLORS[i], marker=['o','s','^','D','P'][j], s=65,
                       label=labels[i] if j == 0 else None)
    for c, pairs in points.items():
        frontier = sorted(set((x,y) for x,y in pairs if not any(a <= x and b >= y and (a < x or b > y) for a,b in pairs)))
        ax.plot([p[0] for p in frontier], [p[1] for p in frontier], '--', color='#777', alpha=.55, linewidth=1)
    ax.plot([], [], '--', color='#777', label='Within-copilot frontier')
    ax.set(xlabel='Never-read cells (%)', ylabel='Routing quality (%)', title='RI-5 · Routing and starvation', xlim=(-3, 60))
    first_legend = ax.legend(frameon=False, loc='lower right', fontsize=9)
    ax.add_artist(first_legend)
    handles = [Line2D([], [], color='#555', marker=m, linestyle='None', label=NAMES[c]) for c,m in zip(d['ri5'], ['o','s','^','D','P'])]
    ax.legend(handles=handles, frameon=False, loc='center right', fontsize=9)
    fig.tight_layout()
    save(fig, 'pub_ri5_routing_vs_starvation.png')
    curves(d['ri6']['dataops'], 'RI-6 · DataOps regime shift · mean ± seed SD', 'pub_ri6_regime_recovery.png')
    fig, axs = plt.subplots(2, 2, figsize=(11, 7), sharex=True, sharey=True)
    for ax, (name, row) in zip(axs.flat, d['ri6']['dataops'].items()):
        for dim in range(4):
            for field, style in [('k', ':'), ('k_effective', '-')]:
                y = [np.mean([np.mean([a[dim] for a in run['checkpoints'][i]['state'][field].values()]) for run in row['seed_runs']]) for i in range(10)]
                ax.plot(range(50, 501, 50), y, style, color=COLORS[dim], label=f'Dim {dim}' if field == 'k_effective' else None)
        ax.axvline(250, color='#555', linestyle='--', linewidth=1)
        ax.set_title(name)
    axs[0, 0].legend(ncol=2, frameon=False, fontsize=9)
    fig.supxlabel('Training decisions')
    fig.supylabel('K weight')
    fig.suptitle('RI-6 · Effective K (solid) · Stored K (dotted)')
    fig.tight_layout()
    save(fig, 'pub_ri6_k_weight_evolution.png')
    grouped(d['ri7'], ['UNIFORM-GREEDY', 'UNIFORM-UCB-0.5', 'CATEGORY-ADAPTIVE'], ['Greedy', 'UCB 0.5', 'Category adaptive'],
            'final_routing_mean', 'Routing quality (%)', 'RI-7 · Category-conditional routing', 'pub_ri7_adaptive_vs_uniform.png')
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, (c, rows) in enumerate(d['ri8'].items()):
        ax.errorbar([0, .1, .5, 1.], [100*r['final_routing_mean'] for r in rows.values()],
                    yerr=[100*r['checkpoints'][-1]['routing_quality_std'] for r in rows.values()], fmt='-o', capsize=4, color=COLORS[i], label=NAMES[c])
    ax.set(xlabel='Sequence bonus β', ylabel='Routing quality (%)', title='RI-8 · Sequence effect · mean ± seed SD')
    ax.legend(frameon=False)
    fig.tight_layout()
    save(fig, 'pub_ri8_sequence_effect.png')
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    for ax, (c, rows) in zip(axs, d['ri9'].items()):
        for i, (name, row) in enumerate(rows.items()):
            rec = row['recovery']
            ax.plot([p['decision_count'] for p in row['checkpoints']], [100*p['routing_quality_mean'] for p in row['checkpoints']], '-o',
                    color=COLORS[i], label=f"{name} · recovery {rec['restricted_mean_decisions']:g}", markersize=4)
        ax.axvline(250, color='#555', linestyle='--', linewidth=1)
        ax.set(title=NAMES[c], xlabel='Training decisions', ylim=(0, 100))
        ax.legend(frameon=False, fontsize=9)
    axs[0].set_ylabel('Routing quality (%)')
    fig.suptitle('RI-9 · Category shift · Recovery decisions (restricted mean)')
    fig.tight_layout()
    save(fig, 'pub_ri9_regime_recovery.png')
    grouped(d['rv4'], ['UNIFORM-B2', 'ADAPTIVE-B'], ['Uniform B=2', 'Risk-adaptive B'], 'final_routing_mean',
            'Routing quality (%)', 'RV-4 · Adaptive budget', 'pub_rv4_adaptive_budget.png')
    fig, ax = plt.subplots(figsize=(8, 5))
    penalties = dict(soc=20, dataops=10, s2p=5, purchasing=3, trading=2)
    for c, rows in d['rv4'].items():
        y = 100*(rows['ADAPTIVE-B']['final_routing_mean']-rows['UNIFORM-B2']['final_routing_mean'])
        ax.scatter(penalties[c], y, s=65, color=COLORS[0])
        offset = (-5, -17) if c == 'trading' else (5, 7)
        ax.annotate(NAMES[c], (penalties[c], y), xytext=offset, textcoords='offset points')
    ax.axhline(0, color='#555', linestyle='--', linewidth=1)
    ax.set(xlabel='Penalty ratio', ylabel='Adaptive routing gain (pp)', title='RV-4 · Penalty and routing gain', xlim=(0, 23))
    fig.tight_layout()
    save(fig, 'pub_rv4_penalty_vs_gain.png')
    fig, ax = plt.subplots(figsize=(9, 6))
    for i, (c, rows) in enumerate(d['rv5'].items()):
        a, b = rows['FLAT-RNN'], rows['HIERARCHICAL']
        ax.plot([a['avg_reads'], b['avg_reads']], [100*a['final_accuracy_mean'], 100*b['final_accuracy_mean']], color=COLORS[i], alpha=.65)
        for variant, marker in [('FLAT-RNN', 'o'), ('HIERARCHICAL', '^')]:
            r = rows[variant]
            ax.scatter(r['avg_reads'], 100*r['final_accuracy_mean'], color=COLORS[i], marker=marker, s=80,
                       label=f'{NAMES[c]} · {"Flat" if marker == "o" else "Hierarchy"}')
    ax.set(xlabel='Average reads / decision', ylabel='Accuracy (%)', title='RV-5 · C4 fallback hierarchy', xlim=(0, 2.2))
    ax.legend(frameon=False, fontsize=9, bbox_to_anchor=(1.02, 1), loc='upper left')
    fig.tight_layout()
    save(fig, 'pub_rv5_hierarchical.png')
    grouped(d['rv8'], ['CLOSED-FORM', 'LEARNED-Q'], ['Closed form', 'Learned Q'], 'final_routing_mean',
            'Routing quality (%)', 'RV-8 · Linear-Q headroom', 'pub_rv8_headroom.png')
    rows = d['rv9']['dataops']
    fig, axs = plt.subplots(1, 2, figsize=(10, 5))
    names = ['Greedy', '1-step', '2-step']
    axs[0].bar(names, [100*r['final_routing_mean'] for r in rows.values()], color=COLORS[:3])
    axs[0].set(ylabel='Routing quality (%)', ylim=(0, 100))
    axs[1].bar(names, [r['scorer_evals'] for r in rows.values()], color=COLORS[:3])
    axs[1].set(ylabel='Scorer evaluations / decision', yscale='log')
    fig.suptitle('RV-9 · Lookahead value and cost')
    fig.tight_layout()
    save(fig, 'pub_rv9_lookahead.png')


def pct(x):
    return f'{100*x:.1f}%'


def table(results):
    lines = ['| Copilot | Variant | Routing ± seed SD | Δ routing (pp), paired 95% CI | Accuracy | Starvation | Reads |',
             '|---|---|---:|---:|---:|---:|---:|']
    for c, rows in results.items():
        for name, r in rows.items():
            delta = r['paired_routing_vs_control']
            low, high = delta['bootstrap_95_interval']
            lines.append(f"| {NAMES[c]} | {name} | {pct(r['final_routing_mean'])} ± {100*r['checkpoints'][-1]['routing_quality_std']:.1f} | {100*delta['mean']:+.1f} [{100*low:+.1f}, {100*high:+.1f}] | {pct(r['final_accuracy_mean'])} | {pct(r['starvation'])} | {r['avg_reads']:.2f} |")
    return lines


def report(data):
    lines = ['# Group B/C recurrence and routing report', '',
             'Protocol date: September 13, 2026. Nine experiments, ten new scripts, twelve figures. Artifact-only synthetic probes on exported real centroid geometry; no production adoption.', '',
             '## Protocol and interpretation', '',
             'Each arm trains for 500 verified synthetic decisions, with 10 checkpoints and 50 held-out cases per checkpoint. Five paired seeds per arm, except RV-8 with ten. Training cases use a separate RNG from policy exploration, and evaluation never updates K, counts, sequence state, or Q coefficients. Raw seed runs, evaluation rows, training rows, state snapshots, configuration, and hashes are retained in the nine JSON files. Every control/candidate pair has an identical training-stream hash.', '',
             'Routing quality is informative reads / actual reads; accuracy is final action agreement with the full-vector centroid scorer. Starvation is the fraction of category-dimension cells never read during training. The RI-7 policy uses a separate baseline-weight metric (K≈0.5), which can also count weights that returned to baseline. Tables use the final held-out checkpoint. Intervals are paired-seed bootstrap percentile intervals, descriptive with five or ten seeds and no multiple-comparison correction. Keep/kill gates use the requested point-estimate thresholds, not significance tests.', '',
             'The prior RV-1 synthetic generator defines a read as informative if its counterfactual action is correct OR it materially raises correct-action probability; already-correct surfaces can therefore label unchanged dimensions informative. Reads outside that set return unchanged evidence. K updates follow the prior bandit harness (+0.02 for correct informative reads, −0.005 otherwise, clipped to [0.1,3]); the production flip bonus and early-halting rules are not exercised. These probes measure this harness, not live routing value or production-scorer parity.', '',
             'The requested routing memo and MAP v17 were not found in the workspace. The detailed user protocol is the experiment authority here. Section 10 distinguishes measured mechanisms from an unverified R0–R5 numbering; it does not invent official taxonomy coverage.', '',
             'Source integrity: all 1,800 source files present in the initial audit retain their exact hashes (dependencies, caches, and build outputs excluded). investigation.py already began **3441dcbd**, while the prompt expected **3441dcdb** (transposed final characters). The router and scorer match expected prefixes 08f4df7a and 24ac9e49. This pre-existing discrepancy was not repaired. Concurrently created scripts outside this task are excluded from the before/after modification check.', '',
             'RI-7 was rerun after aligning its UCB bonus with RV-1: c × sigma_centroid / sqrt(N+1). The other eight JSON files preserve the originally executed shared-harness hash plus an audit showing that the sole subsequent edit changed an unused UCB branch. Their execution paths are unchanged.', '']
    titles = ['RI-5 — Rich K State', 'RI-6 — Temporal Decay', 'RI-7 — Category-Conditional Routing', 'RI-8 — Sequence-Aware Q',
              'RI-9 — Regime-Indexed K', 'RV-4 — Risk-Sensitive Q', 'RV-5 — Hierarchical C4→RNN', 'RV-8 — Adaptive-Q Headroom', 'RV-9 — MCTS Lookahead Value']
    chart_names = [['pub_ri5_starvation_comparison.png', 'pub_ri5_routing_vs_starvation.png'], ['pub_ri6_regime_recovery.png', 'pub_ri6_k_weight_evolution.png'],
                   ['pub_ri7_adaptive_vs_uniform.png'], ['pub_ri8_sequence_effect.png'], ['pub_ri9_regime_recovery.png'],
                   ['pub_rv4_adaptive_budget.png', 'pub_rv4_penalty_vs_gain.png'], ['pub_rv5_hierarchical.png'], ['pub_rv8_headroom.png'], ['pub_rv9_lookahead.png']]
    for idx, (key, title) in enumerate(zip(FILES, titles), 1):
        d = data[key]
        verdict = d['verdict']
        status = ('KEEP' if verdict['keep'] else 'DO NOT KEEP') if 'keep' in verdict else 'REPORT ONLY'
        lines += [f'## {idx}. {title}', '', f'**{status}.** {verdict["criterion"]}.', '']
        if key == 'ri5':
            lines += [f"Rich Thompson reduces Trading starvation by **{verdict['trading_starvation_reduction_pp']:.1f}pp**. Trading routing changes by **{verdict['routing_deltas_pp']['trading']:+.1f}pp**. This decides whether the exploration is precise enough under the preregistered gate; lower starvation alone does not establish benefit.", '']
        if key in ('ri6', 'ri9'):
            lines += ['Recovery is the first held-out checkpoint at or above 90% of mean pre-shift quality at decisions 200 and 250, including an immediate post-shift probe. Resolution is 50 decisions. Unrecovered seeds are right-censored at 250; restricted means are reported alongside censor counts. A zero-time control cannot support a percentage speedup. Training-window 201–250 metrics are also available in JSON.', '',
                      '| Copilot | Variant | Pre-shift routing | Recovery decisions, restricted mean | Censored seeds | Immediate recovery seeds |',
                      '|---|---|---:|---:|---:|---:|']
            for c, rows in d['results'].items():
                for name, r in rows.items():
                    q = r['recovery']
                    lines.append(f"| {NAMES[c]} | {name} | {pct(q['pre_shift_quality'])} | {q['restricted_mean_decisions']:.1f} | {q['censored_seeds']} | {q['recovered_at_zero']} |")
            lines += ['', 'Per-comparison gates: `' + json.dumps(verdict['comparisons'], sort_keys=True) + '`.', '']
        if key == 'ri7':
            lines += [f"Greedy's best routing copilot is {NAMES[verdict['best_control_copilot']]}; its worst is {NAMES[verdict['worst_control_copilot']]}. Adaptive mode must retain quality on the former and improve the latter while meeting the starvation cap everywhere.", '']
        if key == 'ri8':
            lines += ['Per-copilot β candidates meeting +2pp: `' + json.dumps(verdict['per_copilot_candidates']) + '`. The global keep gate requires one β to meet the threshold on both copilots.', '']
        if key == 'rv4':
            lines += ['Positive Q scaling at fixed B=2 is **exactly invariant** for every seed: both training route digests and all evaluation rows match. Adaptive budgets are SOC 5, DataOps 4, S2P 3, Purchasing 2, Trading 2. The 5% gain gate is relative routing improvement, evaluated separately for SOC and DataOps; low-penalty checks use Purchasing and Trading.', '',
                      'Adaptive relative gains: ' + ', '.join(f'{NAMES[c]} {100*g:+.1f}%' for c,g in verdict['adaptive_relative_gains'].items()) + '.', '']
        if key == 'rv5':
            lines += ['This measures the **existing C4 fallback**. No trained classifier artifact is available; the fallback emits S1/S3/S6 only. The requested six-class budget table is implemented, but S2/S4/S5 coverage is zero. Per-copilot efficiency gates: `' + json.dumps(verdict['comparisons']) + '`.', '']
        if key == 'rv8':
            lines += [f"Measured linear-learner headroom is **{verdict['headroom_pp']:+.1f}pp**; >5pp flag: **{verdict['flag_large_gain']}**. This is a specified online-regression probe, not a proven upper bound on all learned routers. The three coefficients are inspectable, but fitting them erodes the no-trained-router separator. No adoption is made.", '']
        if key == 'rv9':
            lines += ['The requested lookahead is implemented as exact finite centroid expectimax, not Monte Carlo tree search. Simulations see only current evidence, centroids, and the action posterior. Margin improvement can reinforce an incorrect high-confidence action. Gains (pp): `' + json.dumps(verdict['gains_pp']) + '`; scorer-cost multipliers: `' + json.dumps(verdict['scorer_eval_multipliers']) + '`.', '']
        lines += table(d['results']) + ['', '**Implementation choices and limits:**', ''] + ['- '+note for note in d['notes']] + ['']
        lines += [f'[Raw results]({FILES[key]}.json). ' + ' · '.join(f'[Figure {i+1}](charts/{name})' for i, name in enumerate(chart_names[idx-1])), '']
    old = json.loads((OUT/'rv0_gru_ablation_results.json').read_text(encoding='utf-8'))
    old_bandit = json.loads((OUT/'rv1_bandit_results.json').read_text(encoding='utf-8'))
    ri1_path = OUT/'ri1_routing_k_interaction.json'
    ri1 = json.loads(ri1_path.read_text(encoding='utf-8')) if ri1_path.exists() else None
    lines += ['## 10. Recurrence Taxonomy — Complete Picture', '',
              'The mechanism inventory below covers the completed probes and prior RV-0/RV-1 artifacts. The R0–R5 assignments are **provisional descriptive groupings**, not verified MAP v17 definitions. Official numbering still requires the missing authority documents; a complete six-class trained C4 test is also unavailable.', '',
              '| Provisional level | Mechanism | Evidence and key finding |', '|---|---|---|',
              f"| R0 | Static read plan | Prior RV-0 STATIC routing {pct(old['results']['static']['final_routing_mean'])}; frozen initial plan. |",
              f"| R1 | Within-episode recurrent Q | Prior RV-0 RNN {pct(old['results']['rnn']['final_routing_mean'])}, GRU {pct(old['results']['gru']['final_routing_mean'])}, LSTM {pct(old['results']['lstm']['final_routing_mean'])}; LSTM did not clear its +2pp-over-GRU gate. |",
              '| R2 | Cross-decision scalar utility | Prior K-learning cross-copilot summary shows positive learning-minus-control routing on all five copilots, with Trading starvation 48%; prior RV-1 exploration removes starvation at a routing tradeoff. |',
              f"| R3 | Rich utility and temporal persistence | RI-5 keep={data['ri5']['verdict']['keep']}; RI-6 decay keep={data['ri6']['verdict']['keep']}; uncertainty and age change exploration/persistence. |",
              f"| R4 | Conditional and ordered recurrence | RI-7 adaptive keep={data['ri7']['verdict']['keep']}; RI-8 sequence keep={data['ri8']['verdict']['keep']}; RI-9 regime keep={data['ri9']['verdict']['keep']}; category indexing already exists in production. |",
              f"| R5 | Policy hierarchy, learned Q, lookahead | RV-5 fallback keep={data['rv5']['verdict']['keep']}; RV-8 headroom {data['rv8']['verdict']['headroom_pp']:+.1f}pp; RV-9 evaluated explicitly with simulation cost. |", '',
              'Risk-sensitive RV-4 is orthogonal to recurrence depth: scalar multiplication cannot change an argmax, while budget and posterior-scale changes can. Prior results use their original seeds/protocol; they are not merged statistically with the new paired runs.', '',
              '## 11. Three-Metric Summary', '',
              '**M-VALUE** reports final routing and final-action accuracy. **M-COST** reports actual reads, scorer calls per evaluation decision (including every hypothetical rollout), accuracy/scorer call, and additional training-only counterfactual scorer calls. Wall times are retained for diagnostics but are not latency benchmarks because experiments may run concurrently. **M-GOV** is a design assessment of state traceability and training dependence, not a compliance score or measured governance outcome.', '',
              'Codes: **I** = named factor/category state and closed-form rule; **S** = I plus stochastic exploration (seed and state required for replay); **C4** = inspectable existing fallback, trained model absent; **L** = three learned coefficients plus privileged counterfactual training labels, separator eroded; **P** = inspectable centroid simulation, model assumptions and expanded scorer cost. All remain offline experiments.', '',
              '| Experiment | Copilot | Variant | M-VALUE: routing / accuracy | M-COST: reads / scores / accuracy per score | Training extra scores | M-GOV |',
              '|---|---|---|---:|---:|---:|---|']
    if ri1 is not None:
        marker = lines.index('## 11. Three-Metric Summary')
        rr = ri1['results']
        companion = [
            'The concurrently completed [Group A/D report](group_a_d_report.md) supplies RI-1 through RI-4 and their full M-VALUE/M-COST/M-GOV tables:', '',
            f"- RI-1: STATIC+K routing {pct(rr['static_learning']['final_routing_mean'])}, RNN+K {pct(rr['rnn_learning']['final_routing_mean'])}; RNN accuracy {pct(rr['rnn_learning']['final_accuracy_mean'])} versus STATIC {pct(rr['static_learning']['final_accuracy_mean'])}. K helps all four architectures; their routing rank does not flip.",
            '- RI-2: the UCB sweep finds qualifying coefficients on DataOps, Purchasing, SOC, and S2P; Trading has no coefficient satisfying both its starvation and routing constraints.',
            '- RI-3: hybrid first-greedy/second-UCB removes Trading starvation but loses 4.6pp routing; no tested Trading epsilon/hybrid policy satisfies both constraints.',
            '- RI-4: all three transfer pairs have zero exact factor-name overlap. Cold and warm initializations are identical; transfer efficacy is not testable on these pairs.', '',
            'These companion results complete the requested RI-1–RI-9 experiment inventory. They do not turn zero-overlap transfer or missing classifier classes into positive coverage evidence. Group A/D reuses scorer outputs and counts 2/3 calls for static/recurrent policies; this group retains actual 4-call baseline execution to match the older RV-0 loop. Compare cost conventions before combining tables.', '']
        lines[marker:marker] = companion
    for key, d in data.items():
        for c, rows in d['results'].items():
            for name, r in rows.items():
                cfg = d['configs'][c][name]
                gov = 'L' if cfg.get('learned') else 'P' if cfg.get('lookahead') else 'C4' if key == 'rv5' else 'S' if cfg.get('mode') in ('thompson', 'rich') else 'I'
                lines.append(f"| {key.upper()} | {NAMES[c]} | {name} | {pct(r['final_routing_mean'])} / {pct(r['final_accuracy_mean'])} | {r['avg_reads']:.2f} / {r['scorer_evals']:.1f} / {r['accuracy_per_scorer_eval']:.4f} | {r['learning_scorer_evals']:.1f} | {gov} |")
    lines += ['', 'Prior taxonomy comparators (original artifacts, not rerun):', '',
              '| Prior experiment | Copilot | Variant | M-VALUE: routing / accuracy | M-COST | M-GOV |', '|---|---|---|---:|---|---|']
    for n, r in old['results'].items():
        lines.append(f"| RV-0 | DataOps | {n} | {pct(r['final_routing_mean'])} / {pct(r['final_accuracy_mean'])} | {r['scorer_evals_per_decision']:.1f} scorer calls; B=2 | Dimension-aligned state (prior assessment) |")
    for c, rows in old_bandit['results'].items():
        for n in ['greedy', 'thompson', 'ucb']:
            r = rows[n]
            lines.append(f"| RV-1 | {NAMES[c]} | {n} | {pct(r['final_routing_mean'])} / {pct(r['final_accuracy_mean'])} | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |")
    lines += ['', '## Reproduction and checks', '',
              'Run each scripts/ri5…ri9 and scripts/rv4,rv5,rv8,rv9 entrypoint with the supplied project Python interpreter and `-B`, then `python -B scripts/generate_group_b_c_charts.py`. Each experiment imports shared machinery from the newly created ri5_rich_k_state.py and reads the existing routing_variant_bandit.py without modification. The chart/report script reads completed JSON only.', '',
              'Automated checks assert formula parity in preflight, paired training streams, frozen evaluation state, and exact fixed-Q-scale routing invariance. JSON preserves full pre/post production hashes, centroid hash, entrypoint hash, and shared-harness hash. Results are serialized with nonfinite values forbidden. Recovery censoring and missing-authority/model limitations are explicit.']
    (OUT/'group_b_c_report.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


def main():
    data = {k: json.loads((OUT/(v+'.json')).read_text(encoding='utf-8')) for k, v in FILES.items()}
    charts(data)
    report(data)
    print('Wrote 12 charts and group_b_c_report.md')


if __name__ == '__main__':
    main()
