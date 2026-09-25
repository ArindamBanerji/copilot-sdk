"""RV-5: existing C4 fallback chooses the prompt-specified situation budget."""
from ri5_rich_k_state import COPILOTS, run_experiment


def verdict(results):
    comparisons = {}
    for c, rows in results.items():
        a, b = rows['FLAT-RNN'], rows['HIERARCHICAL']
        comparisons[c] = dict(accuracy_delta_pp=100*(b['final_accuracy_mean']-a['final_accuracy_mean']),
                              reads_saved=a['avg_reads']-b['avg_reads'],
                              keep=b['final_accuracy_mean'] >= a['final_accuracy_mean'] and b['avg_reads'] < a['avg_reads'])
    return dict(keep=all(v['keep'] for v in comparisons.values()), comparisons=comparisons,
                criterion='>= flat held-out accuracy at strictly fewer average reads on each copilot',
                scope='existing C4 fallback only; trained six-class C4 artifact absent')


if __name__ == '__main__':
    run_experiment('rv5', 'rv5_hierarchical.json', {'FLAT-RNN': {}, 'HIERARCHICAL': {'hierarchical': True}}, COPILOTS, verdict,
                   notes=['Uses existing SituationClassifier with no model_path: d_min<.05 => S1, d_min>.5 => S6, otherwise S3. No fitted classifier artifact was found.',
                          'Applies prompt budgets S1:0,S2:1,S3:2,S4:3,S5:2,S6:1, overriding the production budget mapping only in experiment memory.',
                          'Fallback cannot emit S2/S4/S5, so this is a fallback hierarchy measurement, not a validation of a trained six-class classifier. Situation counts retained for every checkpoint.'])
