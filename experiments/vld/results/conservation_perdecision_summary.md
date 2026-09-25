# CONS-PD — Per-decision signal characterization

Rows: 120,000; columns: 23. Conditions: normal, slow-drift, poison-25%, fast-break; 3 seeds; 2,000 decisions/run.

## Q1 — Discriminative power

| Rank | Signal | Pooled AUC |
|---:|---|---:|
| 1 | recent_accuracy_w200 | 0.650 |
| 2 | recent_accuracy_w100 | 0.650 |
| 3 | recent_accuracy_w50 | 0.642 |
| 4 | distance_from_floor | 0.627 |
| 5 | conservation_state | 0.583 |
| 6 | decision_margin | 0.571 |
| 7 | d2_local | 0.508 |
| 8 | residual | 0.508 |
| 9 | category_coverage | 0.502 |
| 10 | sigma_signal | 0.500 |
| 11 | investigation_depth | 0.500 |

Per-copilot AUC is retained in the JSON (`analysis.q1_auc`).

## Q2 — Calibration

| Copilot | ECE |
|---|---:|
| pooled | 0.0085 |
| dataops | 0.0168 |
| trading | 0.0249 |
| purchasing | 0.0215 |
| soc | 0.0093 |
| s2p | 0.0139 |

Top-3 logistic signals: recent_accuracy_w200, recent_accuracy_w100, recent_accuracy_w50.

Per-copilot top-3 AUC:

| signal               | copilot    |      auc |
|:---------------------|:-----------|---------:|
| recent_accuracy_w100 | dataops    | 0.576728 |
| distance_from_floor  | dataops    | 0.576728 |
| recent_accuracy_w200 | dataops    | 0.575553 |
| recent_accuracy_w200 | purchasing | 0.664857 |
| recent_accuracy_w100 | purchasing | 0.664317 |
| distance_from_floor  | purchasing | 0.664317 |
| decision_margin      | s2p        | 0.65462  |
| recent_accuracy_w200 | s2p        | 0.590606 |
| recent_accuracy_w100 | s2p        | 0.584854 |
| decision_margin      | soc        | 0.648638 |
| recent_accuracy_w100 | soc        | 0.645673 |
| distance_from_floor  | soc        | 0.645673 |
| recent_accuracy_w100 | trading    | 0.676418 |
| distance_from_floor  | trading    | 0.676418 |
| recent_accuracy_w200 | trading    | 0.673494 |

Reliability diagram bins:

| copilot    |   bin |   count |   mean_prediction |   observed_accuracy |
|:-----------|------:|--------:|------------------:|--------------------:|
| pooled     |     0 |      17 |         0.0630751 |            0.823529 |
| pooled     |     1 |       7 |         0.151763  |            0.571429 |
| pooled     |     2 |      26 |         0.260508  |            0.615385 |
| pooled     |     3 |      35 |         0.362226  |            0.8      |
| pooled     |     4 |     419 |         0.464869  |            0.606205 |
| pooled     |     5 |    1113 |         0.56009   |            0.636119 |
| pooled     |     6 |    9917 |         0.667417  |            0.681759 |
| pooled     |     7 |   28216 |         0.753937  |            0.736036 |
| pooled     |     8 |   70817 |         0.855338  |            0.855261 |
| pooled     |     9 |    9433 |         0.908441  |            0.927383 |
| dataops    |     0 |       4 |         0.0630751 |            1        |
| dataops    |     2 |       6 |         0.279173  |            1        |
| dataops    |     4 |      26 |         0.48158   |            0.615385 |
| dataops    |     5 |     116 |         0.584045  |            0.75     |
| dataops    |     6 |    2421 |         0.668581  |            0.673689 |
| dataops    |     7 |    8684 |         0.761264  |            0.754721 |
| dataops    |     8 |   12723 |         0.834401  |            0.811129 |
| dataops    |     9 |      20 |         0.92763   |            0.6      |
| trading    |     3 |       3 |         0.389681  |            1        |
| trading    |     4 |      21 |         0.48158   |            0.857143 |
| trading    |     5 |       9 |         0.580116  |            1        |
| trading    |     6 |     585 |         0.67796   |            0.724786 |
| trading    |     7 |    4400 |         0.747224  |            0.726364 |
| trading    |     8 |   12795 |         0.877978  |            0.903712 |
| trading    |     9 |    6187 |         0.908131  |            0.930176 |
| purchasing |     0 |      13 |         0.0630751 |            0.769231 |
| purchasing |     1 |       7 |         0.151763  |            0.571429 |
| purchasing |     2 |      20 |         0.254909  |            0.5      |
| purchasing |     3 |      32 |         0.359652  |            0.78125  |
| purchasing |     4 |     341 |         0.461046  |            0.554252 |
| purchasing |     5 |     924 |         0.555114  |            0.609307 |
| purchasing |     6 |    2579 |         0.664659  |            0.69019  |
| purchasing |     7 |    6952 |         0.748412  |            0.722094 |
| purchasing |     8 |   12314 |         0.867341  |            0.87973  |
| purchasing |     9 |     818 |         0.90455   |            0.90709  |
| soc        |     4 |      15 |         0.48158   |            1        |
| soc        |     5 |      12 |         0.591129  |            0.833333 |
| soc        |     6 |    1474 |         0.672252  |            0.699457 |
| soc        |     7 |    3779 |         0.749423  |            0.726118 |
| soc        |     8 |   16366 |         0.860267  |            0.861909 |
| soc        |     9 |    2354 |         0.91013   |            0.934579 |
| s2p        |     4 |      16 |         0.48158   |            1        |
| s2p        |     5 |      52 |         0.584455  |            0.75     |
| s2p        |     6 |    2858 |         0.664268  |            0.663051 |
| s2p        |     7 |    4401 |         0.758792  |            0.739377 |
| s2p        |     8 |   16619 |         0.840191  |            0.827065 |
| s2p        |     9 |      54 |         0.922158  |            0.722222 |

## Q3 — Confidence × depth

Depth B=3 was unavailable; observed depths are B=1/B=2.

| copilot    | confidence_band   |   investigation_depth |   accuracy |   count |
|:-----------|:------------------|----------------------:|-----------:|--------:|
| dataops    | low               |                     2 |   0.737909 |   11351 |
| dataops    | medium            |                     2 |   0.805746 |   11104 |
| dataops    | high              |                     2 |   0.845955 |    1545 |
| purchasing | low               |                     2 |   0.69968  |   10925 |
| purchasing | medium            |                     2 |   0.849382 |    4123 |
| purchasing | high              |                     2 |   0.897006 |    8952 |
| s2p        | low               |                     2 |   0.71224  |    7402 |
| s2p        | medium            |                     2 |   0.822423 |   14084 |
| s2p        | high              |                     2 |   0.848449 |    2514 |
| soc        | low               |                     2 |   0.72043  |    5301 |
| soc        | medium            |                     2 |   0.834972 |    8138 |
| soc        | high              |                     2 |   0.898779 |   10561 |
| trading    | low               |                     2 |   0.727237 |    5030 |
| trading    | medium            |                     2 |   0.854953 |    2544 |
| trading    | high              |                     2 |   0.921405 |   16426 |

## Q4 — Pause dynamics

| copilot    |   pause_decisions |   normal_decisions |   pause_rate |   pause_episodes |   mean_pause_duration |   max_pause_duration |   clustered_seed_runs |   self_resolved_episodes |
|:-----------|------------------:|-------------------:|-------------:|-----------------:|----------------------:|---------------------:|----------------------:|-------------------------:|
| dataops    |               407 |               6000 |   0.0678333  |               20 |              20.35    |                  117 |                     3 |                       18 |
| trading    |                20 |               6000 |   0.00333333 |                3 |               6.66667 |                   16 |                     1 |                        3 |
| purchasing |               939 |               6000 |   0.1565     |               30 |              31.3     |                  228 |                     3 |                       29 |
| soc        |                13 |               6000 |   0.00216667 |                4 |               3.25    |                    6 |                     1 |                        4 |
| s2p        |               278 |               6000 |   0.0463333  |               17 |              16.3529  |                   68 |                     1 |                       12 |

## Q5 — Confidence × adversarial

| confidence_band   |   accuracy |   count |
|:------------------|-----------:|--------:|
| low               |   0.683801 |   21360 |
| medium            |   0.704846 |     908 |
| high              |   0.75576  |     217 |

Low-confidence vulnerability analysis uses poison-25% post-onset rows.

## Next path

V5: go; V6: no basis; V10: structure. This is characterization data, not a design commitment.

## Table

CSV: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\experiments\vld\results\conservation_perdecision_signals.csv; 120,000 rows × 21 emitted columns. Candidate signals are computed before the current verified label is appended. Frozen source hashes are recorded in the script run.
