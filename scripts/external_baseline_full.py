"""C1 + Fig-2b: extend PAPER-EXTERNAL through its existing read-only harness.

PRE-REGISTERED BEFORE EXECUTION (seed=42; ordered first-400 / last-143):
  Original majority category: 30--34% (banked 46/143 = 32.17%).
  Original RF full-feature category: 70--74% (banked 103/143 = 72.03%).
  Original VLD category: 66--70% (banked 98/143 = 68.53%).
  No expected range for NEW strict two-feature arms; no tuning to results.

The original fixture has six surface features and CATEGORY-PATTERN reads, not
two independent dimension acquisitions. Its 68.5% cannot truthfully be called a
two-feature result. Reproduce it with external_baseline.run_experiment(), then
report a clearly named restricted-feature sensitivity. No original source edits.

USER-SELECTED STRICT PROTOCOL (trace-frequency revision, before this execution):
  RF/SVM/LinUCB pair: most frequently advertised enriched_factors in the first
  two pattern reads of the unchanged VLD traces over ALL 543 fixture alerts.
  Factor-index ties. No labels in selection, but selection is transductive:
  the held-out alert features influence the full-fixture routing frequencies.
  Do not describe this feature selector as train-only or an independent holdout.
  FI-routing: original full-feature action RF's top-2 importances, training only.
  VLD B2 sensitivity: original category router, neutral 0.5 missing coordinates,
  one scalar acquisition per routed pattern (first unread enriched_factors entry
  in registry order). Reroute after each scalar, at most two distinct coordinates.
  Final original geometric readout uses ONLY the acquired coordinates. Missing
  values never enter final scoring; no free initial six-factor extraction.
  This dimension adapter is a restricted adaptive sensitivity, not the banked
  full InvestigationLoop. Banked VLD is displayed separately as reference bars.
  Budget is unique scalar observations. RF(full) is exempt at six, majority zero.

Targets and fitting preserve the original harness: fixture categories and
centroid-derived action TRAINING targets, independent models. action_accuracy
EVALUATES those predictions against correct-decision fixture action votes.
teacher_action_agreement is separate. Both target sources are synthetic.

Usage: python -B scripts/external_baseline_full.py
One execution calls the original harness once, fits all new arms, verifies the
saved banked predictions, and writes seven comparison rows + audit JSON + chart.
"""
from __future__ import annotations

import asyncio
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from experiments.vld import external_baseline as original

SEED = 42
OUT = ROOT / 'experiments/vld/results'
CHARTS = ROOT / 'experiments/vld/paper_charts'
NAMES = ('majority', 'linucb', 'rf_budget2', 'svm', 'feature_importance_routing', 'vld', 'rf_full')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rf():
    return RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=1)


def svm():
    return LinearSVC(random_state=SEED, dual='auto', max_iter=10000)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')


def render(rows, reference):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter
    from matplotlib.patches import Patch
    import seaborn as sns
    sns.set_theme(style='whitegrid', font='DejaVu Sans', font_scale=1,
                  rc={'figure.facecolor':'#FAFAFA','axes.facecolor':'#FAFAFA',
                      'font.size':11,'axes.labelsize':11,'axes.titlesize':14,
                      'xtick.labelsize':11,'ytick.labelsize':11,'svg.fonttype':'none'})
    fig, ax = plt.subplots(figsize=(10,6))
    fig.subplots_adjust(left=.08, right=.985, top=.66, bottom=.28)
    labels=['Majority','LinUCB\n(budget 2)','RF\n(budget 2)','SVM\n(budget 2)',
            'FI-routing\n(budget 2)','VLD\n(B=2 adaptive)','RF\n(all features)']
    x=np.arange(len(rows)); width=.33
    category_colors=['#94A3B8']*5+['#2563EB','#D1D5DB']
    action_colors=['#CBD5E1']*5+['#93C5FD','#F1F5F9']
    ax.axvspan(4.52,5.48,color='#DBEAFE',alpha=.65,zorder=0)
    for offset,metric,colors,hatch in [(-width/2,'category_accuracy',category_colors,None),
                                      (width/2,'action_accuracy',action_colors,'///')]:
        bars=ax.bar(x+offset,[r[metric] for r in rows],width,color=colors,
                    edgecolor=['#64748B']*5+['#2563EB','#94A3B8'],linewidth=.7,hatch=hatch,zorder=3)
        bars[-1].set_hatch('xx' if metric=='category_accuracy' else '///xx')
        ax.bar_label(bars,labels=[f'{r[metric]:.1%}' for r in rows],padding=4,fontsize=9)
    ax.set_ylim(0,1.03)
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_ylabel('Accuracy')
    ax.set_xticks(x,[f'{label}\n{r["labels_required"]} labels' for label,r in zip(labels,rows)])
    ax.tick_params(axis='x',length=0,pad=8)
    ax.xaxis.grid(False)
    ax.spines[['top','right','left']].set_visible(False)
    fig.suptitle('Adaptive baseline comparison (SOC 543-alert,\n400/143 split)',fontsize=14,x=.08,ha='left',y=.965)
    fig.text(.08,.815,'Strict scalar budget: 2\nRF/SVM/LinUCB: VLD-frequency pair',fontsize=11,color='#475569',va='top')
    ax.legend(handles=[Patch(facecolor='#94A3B8',edgecolor='#64748B',label='Category accuracy'),
                       Patch(facecolor='#CBD5E1',edgecolor='#64748B',hatch='///',label='Action accuracy')],
              loc='upper left',frameon=False,ncol=2,fontsize=11)
    ref=fig.add_axes([.62,.745,.29,.10],facecolor='#FAFAFA')
    ref.barh([1,0],[reference['category_accuracy'],reference['fixture_action_accuracy']],
             color=['#2563EB','#93C5FD'],edgecolor='#2563EB',height=.6)
    ref.set_yticks([1,0],['Category','Action'],fontsize=9)
    ref.set_xlim(0,1); ref.set_xticks([]); ref.grid(False)
    ref.spines[['top','right','bottom','left']].set_visible(False)
    for y,v in [(1,reference['category_accuracy']),(0,reference['fixture_action_accuracy'])]:
        ref.text(v+.025,y,f'{v:.1%}',va='center',fontsize=9)
    ref.set_title('Banked VLD reference · 0 labels',fontsize=10,loc='left',pad=3)
    fig.text(.62,.716,'6 initial features + up to 3 pattern reads',fontsize=9,color='#475569')
    fig.text(.08,.112,'VLD: scalar adapter sensitivity  |  Action truth: synthetic fixture votes',fontsize=10,color='#475569')
    fig.text(.08,.065,'VLD REAL_COMPONENT; learners SIMULATED  |  Frequency selection: all 543 alerts',fontsize=10,color='#475569')
    CHARTS.mkdir(parents=True,exist_ok=True)
    for suffix in ['png','svg']:
        fig.savefig(CHARTS/f'fig_2b_baseline_comparison.{suffix}',dpi=300,facecolor=fig.get_facecolor())
    plt.close(fig)


async def run():
    protected=[ROOT/'copilot_sdk/scoring/scorer.py', ROOT/'copilot_sdk/scoring/investigation.py',
               ROOT/'copilot_sdk/backend/investigation_router.py', ROOT/'experiments/vld/external_baseline.py',
               OUT/'external_baseline.json', original.FIXTURE, original.GEOMETRY, original.HISTORICAL]
    before={str(p):sha(p) for p in protected}
    np.random.seed(SEED)
    banked=json.loads((OUT/'external_baseline.json').read_text(encoding='utf-8'))
    print('Reproducing original PAPER-EXTERNAL harness once...', flush=True)
    # Capture actual unmodified loop traces without changing its source or predictions.
    runtime_factory=original.soc_runtime
    runtime=runtime_factory()
    complete_traces={}
    class RecordingLoop(runtime.loop):
        async def investigate(self, alert_context, graph_store):
            result=await super().investigate(alert_context,graph_store)
            if self.L_max==3:
                complete_traces[alert_context['alert_id']]=[step.pattern for step in result.trace]
            return result
    traced_runtime=SimpleNamespace(**vars(runtime)); traced_runtime.loop=RecordingLoop
    try:
        original.soc_runtime=lambda:traced_runtime
        reproduced=await original.run_experiment()
    finally:
        original.soc_runtime=runtime_factory
    for name in original.METHODS:
        for metric in ['category_accuracy','action_accuracy','fixture_action_accuracy']:
            assert reproduced[name][metric]==banked[name][metric], (name,metric)
    assert reproduced['test_decisions']==banked['test_decisions'], 'Banked predictions/trace summaries changed'
    assert reproduced['historical_reproduction']['matches_saved_report']
    assert .30 <= reproduced['majority']['category_accuracy'] <= .34
    assert .70 <= reproduced['rf']['category_accuracy'] <= .74
    assert .66 <= reproduced['vld']['category_accuracy'] <= .70
    print('Banked majority, RF(full), VLD and all held-out predictions reproduced.',flush=True)

    data=original.load_data()
    train=np.arange(400); test=np.arange(400,543)
    assert original.SEED==SEED and original.TRAIN_SIZE==400
    assert len(data.alerts)==543
    mu=data.scorer.centroids
    assert len(complete_traces)==543
    counts=Counter({f:0 for f in data.geometry['factor_names']})
    for trace in complete_traces.values():
        for pattern in trace[:2]:
            counts.update(data.runtime.patterns[pattern].enriched_factors)
    dims=sorted(range(6),key=lambda i:(-counts[data.geometry['factor_names'][i]],i))[:2]
    pair=[data.geometry['factor_names'][d] for d in dims]
    x2=data.x[:,dims].copy()
    assert x2.shape==(543,2)
    train_x=x2[train]; test_x=x2[test]
    router=data.runtime.router(data.runtime.patterns,L_max=2)
    def projected_scorer(selected):
        return SimpleNamespace(centroids=mu[:,:,selected].copy(),mu=mu[:,:,selected].copy(),
                               categories=data.scorer.categories,actions=data.scorer.actions,tau=data.scorer.tau)
    def geometry_predictions(vectors, selected):
        scores=[router.score_best_from_centroids(v,projected_scorer(selected)) for v in vectors]
        return np.asarray([s.category_index for s in scores]),np.asarray([s.action_index for s in scores])
    def adaptive_prediction(acquire):
        # acquire is the ONLY path to alert factor values. No metadata or truth input.
        state=np.full(6,.5); selected=[]; considered=set(); trace=[]
        acquisition_router=data.runtime.router(data.runtime.patterns,L_max=len(data.runtime.patterns))
        while len(selected)<2:
            route=acquisition_router.route_decision(state,data.scorer,considered)
            if route.pattern is None:
                raise RuntimeError('No pattern advertising an unread coordinate')
            considered.add(route.selected_category)
            candidates=[data.geometry['factor_names'].index(f) for f in route.pattern.enriched_factors
                        if data.geometry['factor_names'].index(f) not in selected]
            if not candidates:
                continue
            dim=candidates[0]
            state[dim]=acquire(dim)
            selected.append(dim)
            trace.append({'pattern':route.selected_category,'dimension':data.geometry['factor_names'][dim],
                          'dimension_index':dim,'value':float(state[dim])})
        cp,ap=geometry_predictions(state[selected][None,:],selected)
        return int(cp[0]),int(ap[0]),trace
    adaptive_categories,adaptive_actions,adaptive_traces=[],[],[]
    for i in test:
        acquired=[]
        def acquire(dim):
            assert dim not in acquired and len(acquired)<2
            acquired.append(dim)
            return float(data.x[i,dim])
        cp,ap,trace=adaptive_prediction(acquire)
        assert len(acquired)==2
        # Replay with an oracle that refuses every unobserved coordinate. This
        # checks actual acquisition boundaries, not just output feature names.
        replay_values={r['dimension_index']:r['value'] for r in trace}
        assert adaptive_prediction(replay_values.__getitem__)==(cp,ap,trace)
        adaptive_categories.append(cp); adaptive_actions.append(ap); adaptive_traces.append(trace)
    vld_predictions=(np.asarray(adaptive_categories),np.asarray(adaptive_actions))
    predictions={'vld':vld_predictions}
    majority=original.mode(data.y_category[train])
    majority_action=original.mode(data.y_action[train][data.y_category[train]==majority])
    predictions['majority']=(np.full(143,majority),np.full(143,majority_action))
    fitted={}
    for name,factory,xt,xv in [
        ('linucb',None,train_x,test_x),('rf_budget2',rf,train_x,test_x),
        ('rf_full',rf,data.x[train],data.x[test]),('svm',svm,train_x,test_x)]:
        if name=='linucb':
            cm=original.LinUCB(6,n_features=2,alpha=1.)
            am=original.LinUCB(4,n_features=2,alpha=1.)
        else:
            cm,am=factory(),factory()
        cm.fit(xt,data.y_category[train]); am.fit(xt,data.y_action[train])
        predictions[name]=(cm.predict(xv),am.predict(xv))
        fitted[name]=(cm,am)
    assert np.mean(predictions['rf_full'][0]==data.y_category[test])==reproduced['rf']['category_accuracy']
    importances=fitted['rf_full'][1].feature_importances_
    fi_dims=sorted(range(6),key=lambda d:(-float(importances[d]),d))[:2]
    predictions['feature_importance_routing']=geometry_predictions(data.x[test][:,fi_dims],fi_dims)
    # LinUCB evaluation is frozen, selected-arm training inherited unchanged.
    for model in fitted['linucb']:
        a,b=model.a.copy(),model.b.copy(); model.predict(test_x)
        assert np.array_equal(model.a,a) and np.array_equal(model.b,b)
    rows=[]
    for name in NAMES:
        cp,ap=predictions[name]
        category_correct=int(np.sum(cp==data.y_category[test]))
        action_correct=int(np.sum(ap==data.y_fixture[test]))
        row={'name':name,'category_accuracy':category_correct/143,'action_accuracy':action_correct/143,
             'category_correct':category_correct,'action_correct':action_correct,
             'teacher_action_agreement':float(np.mean(ap==data.y_action[test])),
             'labels_required':0 if name=='vld' else 400,
             'budget':0 if name=='majority' else 6 if name=='rf_full' else 2,
             'tier':'REAL_COMPONENT' if name=='vld' else 'SIMULATED',
             'N_train':0 if name=='vld' else 400,'N_test':143,'seed':SEED,
             'split':'original ordered 400/143; no shuffle',
             'fixture':str(original.FIXTURE.relative_to(ROOT.parent)),
             'feature_names':([] if name=='majority' else data.geometry['factor_names'] if name=='rf_full'
                              else sorted({r['dimension'] for t in adaptive_traces for r in t}) if name=='vld'
                              else [data.geometry['factor_names'][i] for i in fi_dims] if name=='feature_importance_routing' else pair),
             'feature_selection_labels_required':400 if name=='feature_importance_routing' else 0,
             'training_features_available':0 if name=='vld' else 6 if name in ['rf_full','feature_importance_routing'] else 0 if name=='majority' else 2,
             'feature_access':'two adaptively chosen scalars per alert' if name=='vld' else 'fixed feature subset',
             'budget_unit':'unique scalar surface features; no additional evidence',
             'protocol':'strict two-scalar sensitivity; classifier pair from full-fixture banked VLD frequencies; FI train-selected; VLD adaptive; RF(full) exempt reference',
             'category_metric_definition':'predicted category == fixture true category',
             'action_metric_definition':'predicted final action == correct-decision fixture action vote',
             'label_source':'synthetic 543-alert fixture; not operationally verified outcomes',
             'action_training_target':'category-conditioned centroid pseudo-labels, unchanged from original harness; evaluation uses fixture votes',
             'original_policy_reproduced':name in ['majority','rf_full'],
             'caveat':('original category router with new one-scalar-per-pattern adapter; not the full banked investigation loop' if name=='vld'
                       else 'original training RF importance ranking; restricted two-coordinate readout without pattern enrichment' if name=='feature_importance_routing'
                       else 'six features; excluded from matched-budget claim' if name=='rf_full' else ''),
             'predictions':[{'alert_id':data.alerts[i]['alert_id'],
                             'category':data.scorer.categories[int(cp[j])],
                             'action':data.scorer.actions[int(ap[j])]} for j,i in enumerate(test)]}
        rows.append(row)
        if name=='vld': row['acquisition_traces']=adaptive_traces
        print(f"{name:27s} category={row['category_accuracy']:.2%} action={row['action_accuracy']:.2%} labels={row['labels_required']} B={row['budget']}",flush=True)
    audit={
        'protocol_version':'C1.strict_scalar_trace_frequency.v2',
        'adaptive_scalar_sensitivity_complete':True,
        'banked_policy_matched_feature_comparison':False,
        'limitation':'The banked harness acquires category patterns. Strict scalar results use a declared restricted adaptive adapter. Feature selection over all 543 alerts is transductive, as requested.',
        'script_sha256':sha(Path(__file__)), 'seed':SEED,
        'preregistered_ranges':{'majority_original':[.30,.34],'rf_full_original':[.70,.74],'vld_original':[.66,.70]},
        'banked_reproduction':{name:{**reproduced[name],
            'tier':'REAL_COMPONENT' if name.startswith('vld') else 'SIMULATED',
            'labels_required':0 if name.startswith('vld') else 400}
            for name in [*original.METHODS,'vld_b2']},
        'historical_reproduction':reproduced['historical_reproduction'],
        'banked_metric_warning':'banked action_accuracy is centroid-teacher agreement; banked fixture_action_accuracy is synthetic verified-action accuracy',
        'original_vld_rf_category_gap_pp':100*(reproduced['rf']['category_accuracy']-reproduced['vld']['category_accuracy']),
        'strict_vld_rf_budget2_category_gap_pp':100*(rows[2]['category_accuracy']-rows[5]['category_accuracy']),
        'shared_pair':pair,'shared_pair_indices':dims,'vld_dimension_frequencies':dict(counts),
        'frequency_unit':'one occurrence per advertised enriched factor per pattern, first two reads of banked L3 traces; all 543 eligible alerts',
        'shared_pair_selection':'descending VLD dimension frequency; factor-index ties; no labels; full-fixture transductive selection',
        'complete_banked_traces':complete_traces,
        'fi_order':[data.geometry['factor_names'][j] for j in fi_dims],'fi_action_rf_importances':importances.tolist(),
        'adaptive_scalar_protocol':'missing values initially 0.5; original category router; first unread advertised dimension per selected pattern; reroute after each scalar; final score projected to exactly two observations',
        'train_alert_ids':[data.alerts[i]['alert_id'] for i in train],
        'test_truth':[{'alert_id':data.alerts[i]['alert_id'],'category':data.scorer.categories[data.y_category[i]],
                       'action':data.scorer.actions[data.y_fixture[i]],'teacher_action':data.scorer.actions[data.y_action[i]]} for i in test],
        'original_test_decisions':reproduced['test_decisions'],
        'original_protocol':reproduced['protocol'],
        'sources_before':before,'sources_after':{str(p):sha(p) for p in protected},
        'checks':{'all_banked_predictions_identical':True,'majority_rf_vld_ranges_pass':True,
                  'same_two_features_for_rf_svm_linucb':True,'feature_selector_zero_labels':True,'linucb_evaluation_frozen':True,
                  'adaptive_oracle_enforces_two_distinct_scalars':True,'adaptive_observed_only_replay':True,
                  'train_test_disjoint':not bool(set(train)&set(test))},
    }
    assert audit['sources_before']==audit['sources_after']
    write_json(OUT/'external_baseline_full.json',rows)
    write_json(OUT/'external_baseline_full_audit.json',audit)
    render(rows,reproduced['vld'])
    print('Generated external_baseline_full.json, external_baseline_full_audit.json, Fig-2b PNG/SVG.',flush=True)
    print('Original VLD gap to RF(full): %.2fpp; this reference is NOT a matched-feature comparison.' % audit['original_vld_rf_category_gap_pp'])


if __name__=='__main__':
    asyncio.run(run())
