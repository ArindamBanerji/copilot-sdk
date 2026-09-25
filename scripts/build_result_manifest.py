"""A2: audit paper claims against existing results, without rerunning experiments.

Only new manifest outputs are written. Source values, cohorts, and metric units
are retained. Paper-only claims are explicitly unverified, never matched merely
because an unrelated JSON contains the same number. Run with python -B.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/vld"
OUT = BASE / "results"
PAPER = ROOT / "docs/design/ci_rgi_impact_core_v7_3.md"
FIELDS = "experiment_id script fixture N_train N_test budget metric_name metric_definition label_source tier value paper_section".split()
DEFS = {
    "routing_quality": "informative reads / total actual reads; source oracle determines informativeness",
    "category_accuracy": "count(predicted category == true category) / evaluated decisions",
    "action_accuracy": "count(predicted final action == verified action) / evaluated decisions; label_source specifies synthetic verification",
    "teacher_action_agreement": "count(predicted final action == nearest-centroid pseudo-label) / evaluated decisions; NOT verified action accuracy",
    "action_accuracy_on_acted": "count(correct final action AND acted) / count(acted)",
    "routing_lift_pp": "100 * (learning routing_quality - control routing_quality)",
    "routing_relative_lift_pct": "100 * (learning routing_quality / control routing_quality - 1)",
    "action_lift_pp": "100 * (action_accuracy - reference action_accuracy)",
    "starvation_rate": "never-selected category-dimension cells / all category-dimension cells",
    "saves": "count(surface action wrong AND final action correct)",
    "hurts": "count(surface action correct AND final action wrong)",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    rows, conflicts, inventory, ledger = [], [], [], []
    def add(eid, script, source, pointer, metric, value, section, train=500,
            test=50, budget=2, tier="REAL_COMPONENT", label="synthetic full-vector oracle",
            definition=None):
        fixture = source
        if source.endswith(('external_baseline.json', 'external_baseline_full.json')):
            fixture = '../gen-ai-roi-demo-v4-v50/backend/support/setup/zero_day_decisions_v5.json'
        elif '/astra_' in source:
            fixture = 'Astra constructed scenarios; raw fixture not recovered; paper-table transcription'
        elif source.startswith('experiments/vld/'):
            generator = ('scripts/k_learning_curve_experiment.py:scenario'
                         if any(n in source for n in ['k_learning_curve','budget_accuracy_frontier','gap1_','q_term_'])
                         else 'scripts/routing_variant_bandit.py:make_case')
            fixture = 'real_centroids_v1.json + ' + generator + ' (synthetic verification)'
        rows.append(dict(zip(FIELDS, [eid, script, fixture, train, test, budget, metric,
            definition or DEFS.get(metric, metric.replace('_', ' ')),
            f"{label}; result={source}#{pointer}", tier, value, section])))

    # Read EVERY result JSON, including large episode files, one at a time.
    # Hash inventory is a coverage audit, not an assertion that every file is cited.
    for path in sorted(BASE.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        inventory.append((path.relative_to(ROOT).as_posix(), path.stat().st_size, digest(path),
                          ", ".join(list(data)[:8]) if isinstance(data, dict) else "list"))
        del data

    def read(name):
        return json.loads((BASE / name).read_text(encoding="utf-8"))

    def emit(name, eid, pointer, metric, value, section, **kwargs):
        scripts = {
            "k_learning_curve_cross_copilot_summary.json": "k_learning_curve_cross_copilot.py",
            "k_learning_curve_results.json": "k_learning_curve_experiment.py",
        }
        script = scripts.get(name, name.replace('.json', '.py'))
        if name.startswith('k_learning_curve_') and name not in scripts:
            script = 'k_learning_curve_cross_copilot.py'
        script_path = f"scripts/{script}"
        if not (ROOT / script_path).exists():
            script_path = "UNKNOWN (not recovered from local outputs)"
        add(eid, script_path, f"experiments/vld/{name}", pointer, metric, value, section, **kwargs)

    summary = read('k_learning_curve_cross_copilot_summary.json')
    for i, c in enumerate(summary['copilots']):
        name = c['name']
        for arm, rk, ak in [('learning', 'final_routing_learning', 'accuracy_learning'),
                            ('fixed', 'final_routing_control', 'accuracy_control')]:
            for metric, key in [('routing_quality', rk), ('action_accuracy', ak)]:
                emit('k_learning_curve_cross_copilot_summary.json', f'KE-1/{name}/{arm}/N500',
                     f'/copilots/{i}/{key}', metric, c[key], 'Headline; §2; §4.1; §5; §7; §8')
        for metric, value in [('routing_lift_pp', 100*c['routing_delta']),
                             ('routing_relative_lift_pct', 100*c['routing_delta']/c['final_routing_control']),
                             ('action_lift_pp', 100*c['accuracy_delta']), ('hurts', c['hurts']),
                             ('starvation_rate', c['starvation_rate']), ('tensor_cells', c['tensor_cells'])]:
            emit('k_learning_curve_cross_copilot_summary.json', f'KE-1/{name}/contrast/N500',
                 f'/copilots/{i}', metric, value, 'Headline; §4.1; §7; §8; Appendix B')
        curve_name = 'k_learning_curve_results.json' if name == 'dataops' else f'k_learning_curve_{name}.json'
        curve = read(curve_name)
        for j, point in enumerate(curve['checkpoints']):
            if name=='dataops' and point['decision_count'] in (50,250,500):
                for arm in ['learning_arm','control_arm']:
                    for metric,key in [('routing_quality','routing_quality'),('action_accuracy','accuracy')]:
                        emit(curve_name,f"KE-1/dataops/{arm}/N{point['decision_count']}",
                             f'/checkpoints/{j}/{arm}/{key}',metric,point[arm][key],'§4.1 hero table',
                             train=point['decision_count'])
            if point['decision_count'] in (250, 500):
                delta = point['learning_arm']['routing_quality'] - point['control_arm']['routing_quality']
                emit(curve_name, f"KE-1/{name}/contrast/N{point['decision_count']}",
                     f'/checkpoints/{j}', 'routing_lift_pp', 100*delta, '§7 moat table', train=point['decision_count'])
    rel = [100*c['routing_delta']/c['final_routing_control'] for c in summary['copilots']]
    acc = [100*c['accuracy_delta'] for c in summary['copilots']]
    conflicts += [
        f"KE-1/all-five/routing_relative_lift_pct: headline and §5 give +17–43%; §4.1 and §8 give +5–43%. Saved endpoints give {min(rel):.2f}–{max(rel):.2f}%. SAME experiment and metric; S2P omitted by the headline range.",
        f"KE-1/all-five/action_lift_pp: headline/§2 give +14–32pp; §4.1 endpoints give {min(acc):.1f}–{max(acc):.1f}pp (S2P +6pp). SAME cohort and metric.",
        "KE-1/R2 taxonomy: '+3–21%' in §4.4 conflates percentage points with relative percentages; the endpoint routing gaps span +3–21pp, while relative lifts span +5–43%.",
        "KE-1/§5 absolute ranges 46–63% (without K) and 59–81% (with K) do not match the §4.1 five-copilot endpoint ranges 44–69% and 63–81%. No separate cohort is identified there.",
    ]
    for metric, value in [('copilot_count', 5), ('improved_copilot_count', sum(c['routing_delta'] > 0 for c in summary['copilots'])),
                          ('regressed_copilot_count', sum(c['routing_delta'] < 0 for c in summary['copilots'])),
                          ('training_decisions', 500)]:
        emit('k_learning_curve_cross_copilot_summary.json', 'KE-1/all-five', '/copilots', metric, value, 'Headline; §4.1; §11')
    for i,c in enumerate(summary['copilots']):
        for axis,metric in enumerate(['category_count','action_count','factor_count']):
            emit('k_learning_curve_cross_copilot_summary.json',f"GEOMETRY/{c['name']}",
                 f'/copilots/{i}/tensor_shape/{axis}',metric,c['tensor_shape'][axis],'§6; Appendix B',
                 train='',test='',budget='',label='exported geometry configuration, not outcome measurement')

    for filename in ['astra_57_0_summary.csv', 'astra_budget_sensitivity_summary.csv']:
        source = f'experiments/vld/{filename}'
        with (BASE / filename).open(newline='', encoding='utf-8') as f:
            records = list(csv.DictReader(f))
        for i, c in enumerate(records):
            for key in ['saves', 'hurts', 'single_pass_accuracy', 'vld_accuracy', 'accuracy_uplift_pp']:
                if key not in c:
                    continue
                metric = {'single_pass_accuracy': 'action_accuracy', 'vld_accuracy': 'action_accuracy',
                          'accuracy_uplift_pp': 'action_lift_pp'}.get(key, key)
                add(f"ASTRA/{c['copilot']}/B{c['budget']}/{key}", 'NOT AVAILABLE: paper-table transcription',
                    source, f'row/{i+2}/{key}', metric, float(c[key]), '§4.1', train=0,
                    test=int(c['scenarios']), budget=int(c['budget']), tier='SIMULATED',
                    label='constructed truth-revealing scenarios; transcribed aggregate, not independently rerun')
        if filename == 'astra_57_0_summary.csv':
            for metric, value in [('saves', sum(int(c['saves']) for c in records)),
                                  ('hurts', sum(int(c['hurts']) for c in records)), ('scenario_count', 250),
                                  ('action_lift_pp', sum(float(c['accuracy_uplift_pp']) for c in records)/5)]:
                add('ASTRA/all-five/B3', 'NOT AVAILABLE: paper-table transcription', source, '/all', metric,
                    value, '§4.1', 0, 250, 3, 'SIMULATED', 'constructed scenarios; transcribed paper table')
    conflicts.append('ASTRA/B3 saves:hurts: 57:0 is supported by the transcribed domain counts. 114:1 is not an equivalent raw count ratio; no documented smoothing/accounting derivation was found. Do not substitute it for saves or hurts.')

    frontier = read('budget_accuracy_frontier.json')
    for i, r in enumerate(frontier['rows']):
        if r['policy'] != 'vld' or r['budget'] not in [2, 'exhaustive']:
            continue
        for metric, key in [('action_accuracy', 'accuracy_mean'), ('routing_quality', 'routing_quality_mean'),
                            ('reads_mean', 'reads_mean')]:
            emit('budget_accuracy_frontier.json', f"FRONTIER/{r['copilot']}/vld/B{r['budget']}",
                 f'/rows/{i}/{key}', metric, r[key], '§4.3; §11', test=200*5, budget=r['budget'])
    del frontier
    gap = read('gap2_abstention_curve.json')
    claims = {'dataops': {0.9:81.3, 0.75:87.4, 0.5:94.0},
              'purchasing': {0.9:83.6, 0.75:92.2, 0.5:98.0}, 'soc': {0.9:95.6, 0.75:100., 0.5:100.}}
    for i, c in enumerate(gap['copilots']):
        signals = c['post_investigation_diagnostic']['signals']
        si = next(j for j,s in enumerate(signals) if s['signal']=='d_min')
        for j, point in enumerate(signals[si]['curve']):
            cov = point['coverage']
            if cov not in [1., .9, .75, .5]:
                continue
            for metric, key in [('action_accuracy_on_acted', 'accuracy_on_acted'), ('coverage', 'coverage'),
                                ('action_accuracy', 'baseline_accuracy_all'), ('acted_count', 'n_acted')]:
                emit('gap2_abstention_curve.json', f"GAP-2/{c['copilot']}/final_d_min/coverage={cov}",
                     f'/copilots/{i}/post_investigation_diagnostic/signals/{si}/curve/{j}/{key}',
                     metric, point[key], '§4.2 (heading missing in v7.3); Fig 4', test=2500)
            emit('gap2_abstention_curve.json', f"GAP-2/{c['copilot']}/final_d_min/coverage={cov}",
                 f'/copilots/{i}/post_investigation_diagnostic/signals/{si}/curve/{j}', 'action_lift_pp',
                 100*point['accuracy_lift_vs_baseline'], '§4.2', test=2500)
            if cov in claims[c['copilot']]:
                claimed = claims[c['copilot']][cov]
                observed = 100*point['accuracy_on_acted']
                if abs(claimed-observed) > .050001:
                    conflicts.append(f"GAP-2/{c['copilot']}/final_d_min/coverage={cov}/action_accuracy_on_acted: §4.2 claims {claimed:.1f}%, saved JSON gives {observed:.4f}%. Corresponding reported lift also needs recalculation.")
    del gap
    halting = read('gap1_adaptive_halting.json')
    for i,r in enumerate(halting['rows']):
        if r['delta'] not in [None, .05]:
            continue
        for metric,key in [('action_accuracy','acc_mean'), ('reads_mean','reads_mean')]:
            emit('gap1_adaptive_halting.json', f"GAP-1/{r['copilot']}/{r['policy']}/delta={r['delta']}",
                 f'/rows/{i}/{key}', metric,r[key],'§4.3; §10',test=1000,budget=2 if r['delta'] is None else 4)
    del halting

    interaction = read('ri1_routing_k_interaction.json')
    for arm,r in interaction['results'].items():
        for metric,key in [('routing_quality','final_routing_mean'),('action_accuracy','final_accuracy_mean')]:
            emit('ri1_routing_k_interaction.json', f'RI-1/dataops/{arm}', f'/results/{arm}/{key}', metric,r[key],'§4.4',test=500)
    for variant in ['static','rnn','gru','lstm']:
        delta = interaction['results'][variant+'_learning']['final_routing_mean'] - interaction['results'][variant+'_fixed']['final_routing_mean']
        emit('ri1_routing_k_interaction.json', f'RI-1/dataops/{variant}/contrast', '/results', 'routing_lift_pp', 100*delta, '§4.4',test=500)

    norm = read('q_term_ablation_normalized.json')
    for i,s in enumerate(norm['normalization_summary']):
        variants = {v['variant']: v['routing_mean'] for v in s['variants']}
        for variant in ['LEVERAGE-ONLY', 'PREC+LEV', 'ALL-THREE']:
            emit('q_term_ablation_normalized.json',f"Q-NORM/{s['normalization']}/{variant}/macro-five",
                 f'/normalization_summary/{i}/variants', 'routing_quality', variants[variant], '§5.1; §10',test=5000)
        emit('q_term_ablation_normalized.json', f"Q-NORM/{s['normalization']}/P+L-minus-ALL/macro-five",
             f'/normalization_summary/{i}/variants', 'routing_lift_pp', 100*(variants['PREC+LEV']-variants['ALL-THREE']), '§5.1; §10',test=5000)
    for metric,value in [('experimental_cells',23*5*5), ('evaluation_episodes',23*5*5*200)]:
        emit('q_term_ablation_normalized.json','Q-NORM/all','/protocol',metric,value,'§5.1; §10',test=115000)
    del norm
    raw = read('q_term_ablation.json')
    for i,r in enumerate(raw['rows']):
        if r['variant'] in ['RANDOM','NO-K','ALL-THREE']:
            emit('q_term_ablation.json',f"Q-RAW/{r['copilot']}/{r['variant']}",f'/rows/{i}/routing_mean',
                 'routing_quality',r['routing_mean'],'§5.1',test=1000)
    del raw
    # Distinct variants and cohorts are part of the ID; never cross-match rounded values.
    for filename in ['ri7_category_conditional.json','ri8_sequence_aware.json','ri6_temporal_decay.json',
                     'ri9_regime_indexed.json','rv8_adaptive_q.json','rv9_mcts.json','rv4_risk_sensitive.json']:
        d=read(filename)
        for copilot, arms in d['results'].items():
            for arm,r in arms.items():
                for metric,key in [('routing_quality','final_routing_mean'),('action_accuracy','final_accuracy_mean'),
                                   ('starvation_rate','starvation'),('scorer_calls_per_decision','scorer_evals')]:
                    if key in r:
                        emit(filename,f"{d['experiment'].upper()}/{copilot}/{arm}",f'/results/{copilot}/{arm}/{key}',
                             metric,r[key],'§4.1; §4.4; §5.2; §10',test=50*d['protocol']['seeds'],
                             budget=r.get('avg_reads',2))
        if filename=='rv8_adaptive_q.json':
            emit(filename,'RV8/dataops/learned-minus-closed-form','/verdict/headroom_pp','routing_lift_pp',d['verdict']['headroom_pp'],'§5.2',test=500)
        if filename=='rv9_mcts.json':
            for arm,value in d['verdict']['gains_pp'].items():
                emit(filename,f'RV9/dataops/{arm}/contrast',f'/verdict/gains_pp/{arm}','routing_lift_pp',value,'§4.4; §10',test=250)
            for arm,value in d['verdict']['scorer_eval_multipliers'].items():
                emit(filename,f'RV9/dataops/{arm}/contrast',f'/verdict/scorer_eval_multipliers/{arm}','scorer_cost_ratio',value,'§4.4; §10',test=250)
        del d
    conflicts.append('RI-7/category-adaptive/starvation_rate: §4.1 implies zero starvation on all five copilots. Saved final rates are 0% for Trading, DataOps and SOC, 1.1429% Purchasing and 0.5% S2P; Trading 74.8% routing / 0% starvation is supported. The saved keep verdict is false under its full preregistered criterion.')
    d=read('ke5_conservation_interaction.json')
    emit('ke5_conservation_interaction.json','KE-5/dataops/conservation','/summary/with_conservation/blocked_decisions_mean',
         'blocked_decisions_mean',d['summary']['with_conservation']['blocked_decisions_mean'],'§10',test=250)
    d=read('ri4_cross_copilot_transfer.json')
    for pair,r in d['results'].items():
        emit('ri4_cross_copilot_transfer.json',f'RI-4/{pair}','/results/'+pair+'/overlap_count',
             'factor_overlap_count',r['overlap_count'],'§4.4; §8; §10',tier='NOT TESTABLE',test=250)

    ext=read('results/external_baseline.json')
    for name in ['majority','linucb','rf','svm','fi_routing','vld','vld_b2']:
        for metric,key in [('category_accuracy','category_accuracy'),('action_accuracy','fixture_action_accuracy'),
                           ('teacher_action_agreement','action_accuracy')]:
            add(f'PAPER-EXTERNAL/SOC/400-143/{name}','experiments/vld/external_baseline.py',
                'experiments/vld/results/external_baseline.json',f'/{name}/{key}',metric,ext[name][key],
                '§9 companion PAPER-EXTERNAL request (not yet in v7.3)',400,143,
                '6 surface factors; '+('2 pattern reads' if name=='vld_b2' else '3 pattern reads' if name=='vld' else 'classifier/FI protocol'),
                'REAL_COMPONENT' if name.startswith('vld') else 'SIMULATED',
                'synthetic fixture correct-decision action votes' if metric=='action_accuracy' else 'fixture categories / category-conditioned centroid teacher')
    for metric,key in [('category_accuracy','vld_category_accuracy'),('action_accuracy','vld_fixture_action_accuracy'),
                       ('category_accuracy','majority_category_accuracy'),('action_accuracy','single_pass_fixture_action_accuracy')]:
        add(f'PAPER-SOC/full543/{key}','experiments/vld/external_baseline.py',
            'experiments/vld/results/external_baseline.json','/historical_reproduction/'+key,metric,
            ext['historical_reproduction'][key],'§9',0,543,'6 surface factors; VLD up to 3 pattern reads',
            'REAL_COMPONENT','synthetic fixture categories / historical correct-decision action votes')

    if (OUT/'external_baseline_full.json').exists():
        full=read('results/external_baseline_full.json')
        for i,r in enumerate(full):
            for metric in ['category_accuracy','action_accuracy','teacher_action_agreement','labels_required']:
                add(f"C1/SOC/strict-two-feature/{r['name']}", 'scripts/external_baseline_full.py',
                    'experiments/vld/results/external_baseline_full.json',f'/{i}/{metric}',metric,r[metric],
                    'Fig-2b / C1 requested companion; not yet in v7.3',r['N_train'],r['N_test'],r['budget'],
                    r['tier'],r['label_source'],definition=DEFS.get(metric,metric))

    # Claim ledger: every numeric body line (not references/changelog) gets a row.
    # Unmapped prose claims stay explicit; source matching is never by value alone.
    # This also retains illustrative amounts, timing assumptions, constants and
    # unsupported headline counts rather than silently dropping difficult claims.
    section='Headline'
    tier='UNVERIFIED'
    for line_no,line in enumerate(PAPER.read_text(encoding='utf-8').splitlines(),1):
        if line.startswith('*Changes '):
            break
        if line.startswith('## '):
            section=line.strip('# ').split(' — ')[0]
        if line.startswith('### 4.') or line.startswith('### 5.'):
            section=line.strip('# ').split(' — ')[0]
        if '**Consequence.** On the decisions it commits' in line:
            section='4.2 Governed autonomy (heading missing)'
        if not re.search(r'\d',line) or line.startswith(('#','*v7.3')):
            continue
        # Strip structural references/IDs so §4.1, R2 and Fig 4 aren't data points.
        cleaned=re.sub(r'(?:§|RI-|RV-|KE-|R|L|B=|dim |Phase |Tier |Figure |Fig )\d+(?:\.\d+)*', '',line)
        cleaned=re.sub(r'\[[^\]]*\]\([^)]*\)|paper_charts/\S+|arXiv \d+\.\d+', '',cleaned)
        tokens=re.findall(r'(?<![A-Za-z_])[$+−-]?\d[\d,]*(?:\.\d+)?(?:%|pp|K|M|B|×)?',cleaned)
        if not tokens:
            continue
        # Each occurrence gets a row; full context retains range/ratio semantics.
        if any(word in line.lower() for word in ['week','days','months','/day','$7b','$0.9m','$1.62m','90-day','90 days','modeled']):
            tier='ILLUSTRATIVE'
        elif section.startswith('Appendix A'):
            tier='DEMONSTRATED'
        elif section.startswith('Appendix B'):
            tier='REAL_COMPONENT'
        elif line.startswith('>') and section.startswith('4.1'):
            tier='PLANTED FIXTURE'
        else:
            tier='UNVERIFIED'
        metric='paper_claim_numeric_tokens'
        source=f'{PAPER.relative_to(ROOT).as_posix()}:L{line_no}'
        for index, token in enumerate(tokens,1):
            add(f'PAPER-CLAIM/L{line_no}/number{index}','scripts/build_result_manifest.py',source,'',metric,
                token,section,train='',test='',budget='',tier=tier,
                label='paper text only; consult measured rows and conflict audit; not an independent measurement',
                definition=f'Numeric occurrence {index}/{len(tokens)}; original units; '+line.strip())
            ledger.append((line_no,section,tier,token))

    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'result_manifest.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
    measured=len(rows)-len(ledger)
    readme=[
        '# Result manifest — paper v7.3', '',
        f'{len(rows)} rows: {measured} source-derived metrics and {len(ledger)} paper numeric-claim occurrences. '
        f'All {len(inventory)} pre-existing experiment JSONs were parsed; inventory and hashes below.', '',
        '## Metric contract', '',
        *[f'- **{k}**: {DEFS[k]}.' for k in ['routing_quality','category_accuracy','action_accuracy']], '',
        'These metrics routinely disagree. In paper §4.4 / RI-1, Static+K leads routing (60.8% versus RNN+K 56.6%), '
        'but RNN+K leads action accuracy (78.2% versus 75.2%). Routing quality is not category accuracy. '
        'A routing lift in pp is 100 times a difference; a relative lift is 100 times a ratio minus one.', '',
        '## Provenance and coverage', '',
        'Source-derived rows retain JSON pointers (or CSV row numbers) in label_source. The fixture column '
        'identifies the actual fixture or exported geometry plus synthetic generator. '
        'KE/RI/RV use real_centroids_v1.json; detailed generator protocol and seed provenance remain in the cited result artifact. '
        'PAPER-EXTERNAL uses ../gen-ai-roi-demo-v4-v50/backend/support/setup/zero_day_decisions_v5.json. '
        'N_train is per seed; N_test is pooled endpoint evaluation count unless a row explicitly describes episodes. '
        'Fixed K arms share the stream without updates. Offline training budgets do not equal evaluation acquisition budgets.', '',
        'PAPER-CLAIM rows preserve each numeric occurrence plus its full line, including ranges and ratios. They are an exhaustive claim '
        'ledger, not additional experiment results. UNVERIFIED means no independent result mapping for that line has '
        'been established; it is not an evidence tier upgrading the claim. ILLUSTRATIVE timing/dollar assumptions '
        'and PLANTED FIXTURE walkthrough arithmetic are retained separately. Equations and tensor dimensions are '
        'configuration facts, not accuracy estimates. Bibliographic dates and structural numbers may appear in '
        'the conservative line ledger but are never treated as measurements. Changelog repeats are excluded.', '',
        'Astra CSVs are explicitly paper-table transcriptions, not fresh experimental confirmation. '
        'No raw execution provenance for the 57:0 count was recovered here. Claims such as 15 configurations / '
        '375 cells, twelve killed alternatives, the naive-abstention 86% / 17.6% / 21.6%, the walkthrough '
        '0.624375 threshold and calendar estimates remain claim-ledger entries unless separately sourced. '
        'This manifest exposes unresolved provenance rather than inventing it.', '',
        '## Conflicts and unsupported equivalences', '',
        *[f'{i+1}. {c}' for i,c in enumerate(conflicts)], '',
        '## Differences that are not conflicts', '',
        '- §9 full-fixture majority is 163/543 = 30.02%; the held-out training-majority control is 46/143 = 32.17%. Different cohorts.',
        '- §9 VLD 372/543 = 68.51% and held-out VLD 98/143 = 68.53% use different cohorts. Neither is informative-read routing_quality.',
        '- Historical VLD action accuracy 31.31% uses all 543 fixture-vote labels; held-out L3 is 26.57%, held-out L2 is 30.77%. Different cohort/budget.',
        '- The old external harness calls centroid-teacher agreement action_accuracy. This manifest renames that metric teacher_action_agreement and maps fixture_action_accuracy to action_accuracy. Those fixture labels are synthetic votes, not customer-verified outcomes.',
        '- GAP-2 synthetic post-investigation calibration is not the historical 543-alert SOC cohort; its own protocol explicitly denies a matched causal comparison with naive B7.',
        '- The 57:0 B3 constructed cohort differs from the frontier B2 cohort; neither can be substituted for the other.',
        '- Raw and normalized Q results have distinct experiment IDs; changing normalization is not a contradictory measurement.', '',
        '## Parsed JSON inventory', '',
        '| Result | Bytes | SHA-256 | Top-level fields |','|---|---:|---|---|',
        *[f'| {p} | {n} | `{h}` | {keys} |' for p,n,h,keys in inventory], '',
        '## Numeric paper-line ledger', '',
        '| Line | Section | Classification | Tokens (original units) |','|---:|---|---|---|',
        *[f"| {n} | {s} | {t} | {v.replace('|', ';')} |" for n,s,t,v in ledger], '',
        f'Paper SHA-256: `{digest(PAPER)}`',
        '## C1 / Fig-2b protocol', '',
        'The new C1 rows use the same ordered 400/143 split. RF/SVM/LinUCB receive the two most frequent '
        'advertised dimensions from banked VLD first-two-pattern traces across all 543 alerts, as requested. '
        'That selector uses no labels but does use the held-out feature distribution (transductive selection). '
        'FI uses the original training RF importance ranking. The adaptive VLD sensitivity admits only two '
        'scalar observations via a declared adapter over the original category router; it is not the banked '
        'six-surface-feature investigation loop. Original VLD reference bars remain separate; RF(all features) '
        'is the final, hatched reference group. See external_baseline_full_audit.json for all traces and exact '
        'protocol. Action fitting keeps the original centroid-teacher targets; reported action accuracy uses '
        'the historical synthetic fixture votes. Teacher agreement is separately named.', '',
        'Regenerate: `python -B scripts/build_result_manifest.py`', '',
    ]
    (OUT/'result_manifest_README.md').write_text('\n'.join(readme),encoding='utf-8')
    print(f'Manifest: {len(rows)} rows ({measured} source-derived; {len(ledger)} claim lines); {len(conflicts)} audit flags')
    for c in conflicts: print('FLAG:',c)


if __name__=='__main__':
    main()
