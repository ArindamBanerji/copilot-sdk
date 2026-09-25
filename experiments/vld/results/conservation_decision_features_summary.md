# CONS-PD-2 — Decision-level confidence features

Rows: 30,000; columns: 44; conditions: normal/poison-25%; seeds: 42/123/7; decisions/run: 1,000.

## Feature computability gate

All ten requested decision-level features were computable before the current label. Q vectors, K state, deltas, post-margin, Q×K, category count, factor position, and centroid distances use only decision-time geometry and investigation state.

## Full feature ranking — pooled

| Feature | AUC | Class |
|---|---|---|
| delta_1 | 0.7212099670900192 | routing |
| post_investigation_margin | 0.7117956255153732 | routing |
| recent_accuracy_w100 | 0.6403129303947133 | population |
| recent_accuracy_w50 | 0.6369091488535248 | population |
| recent_accuracy_w200 | 0.6355819215945546 | population |
| distance_from_floor | 0.6157873103999817 | population |
| k_selected_2 | 0.5914634835282306 | routing |
| k_selected_1 | 0.5802459151176472 | routing |
| conservation_state | 0.5798031555551743 | population |
| qk_reliability | 0.5645487645381029 | routing |
| nearest_centroid_distance | 0.5565775507693045 | geometric |
| q_gap | 0.5536988444814872 | routing |
| delta_2 | 0.5507779187773755 | routing |
| q_entropy | 0.5468701412637733 | routing |
| factor_1 | 0.54479898949815 | geometric |
| geometric_margin | 0.5376384236825122 | geometric |
| decision_margin | 0.5361231496287691 | routing |
| k_mean | 0.532663165687158 | routing |
| factor_0 | 0.5317615539595886 | geometric |
| factor_4 | 0.5303709603873893 | geometric |
| factor_6 | 0.5247074359771864 | geometric |
| factor_9 | 0.5246817419057708 | geometric |
| second_centroid_distance | 0.5205253404432345 | geometric |
| category_decision_count | 0.5191666616123723 | routing |
| factor_5 | 0.5177529028063126 | geometric |
| k_std | 0.5161044320386705 | routing |
| factor_2 | 0.5155269814491983 | geometric |
| d2_local | 0.5142973071416354 | population |
| residual | 0.5141822856024643 | population |
| factor_3 | 0.5053406817836654 | geometric |
| category_coverage | 0.5040829231798856 | population |
| factor_7 | 0.5015677406714141 | geometric |
| factor_8 | 0.5006252753702939 | geometric |
| sigma_signal | 0.5 | geometric |
| investigation_depth | 0.5 | geometric |

New features above AUC .650:

delta_1 (0.721), post_investigation_margin (0.712)

## Per-copilot ranking

Top-five per-copilot rows are included in the JSON under feature_ranking.per_copilot.

## Combined model

Top features: delta_1, post_investigation_margin, recent_accuracy_w100, recent_accuracy_w50, recent_accuracy_w200, distance_from_floor, k_selected_2, k_selected_1, conservation_state, qk_reliability

Pooled AUC: 0.814; pooled ECE: 0.0107; baseline-model AUC: 0.656.

| Copilot | AUC | ECE |
|---|---|---|
| soc | 0.8184614926679342 | 0.045994273857034265 |
| dataops | 0.8260947064115989 | 0.08206822175858178 |
| trading | 0.8085796564275569 | 0.07202905552650589 |
| purchasing | 0.8089079451606361 | 0.07284228628233719 |
| s2p | 0.8753339601531208 | 0.07106960126951678 |

## Frontier improvement

| θ | Coverage | Accuracy |
|---|---|---|
| 0.50 | 0.9221333333333334 | 0.8893146327356853 |
| 0.55 | 0.9014 | 0.9000813549293691 |
| 0.60 | 0.8734 | 0.912449431341119 |
| 0.65 | 0.8311333333333333 | 0.9298147108366086 |
| 0.70 | 0.7824666666666666 | 0.9472607991820737 |
| 0.75 | 0.7326 | 0.9606879606879607 |
| 0.80 | 0.6834666666666667 | 0.9677136168552477 |
| 0.85 | 0.6178 | 0.974317470594583 |
| 0.90 | 0.49993333333333334 | 0.9831977597012935 |
| 0.95 | 0.2652 | 0.9901960784313726 |

Coverage at first tested 90% accuracy: 90.1%.

## Feature-class ablation

| Model | Pooled AUC |
|---|---|
| all_classes | 0.8140223758443705 |
| without_population | 0.7736989183181344 |
| without_routing | 0.6422880539492197 |
| without_geometric | 0.8140223758443705 |

Dominant class: routing.

## V5 verdict

gating viable. Decision-level features do materially improve per-decision confidence discrimination under the tested frontier criterion.

JSON: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\experiments\vld\results\conservation_decision_features.json; instrumented table: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\experiments\vld\results\conservation_decision_features.csv. Frozen source hashes are recorded in JSON.
