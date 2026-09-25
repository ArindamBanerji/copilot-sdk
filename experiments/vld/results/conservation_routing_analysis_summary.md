# CONS-PD-R — Per-decision confidence routing analysis

Existing input: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\experiments\vld\results\conservation_perdecision_signals.csv; 120,000 rows. Q2 logistic refit on normal-condition data.

## Q2 model

Features: recent_accuracy_w200, recent_accuracy_w100, recent_accuracy_w50

Coefficients: 2.491102, 1.600791, 0.874232; intercept: -2.396831.

## R1 — Accuracy-coverage frontier

| θ | Coverage | Accuracy | Escalation |
|---|---|---|---|
| 0.50 | 0.9981 | 0.8545903884046355 | 0.0019000000000000128 |
| 0.55 | 0.9960666666666667 | 0.8550632487785289 | 0.003933333333333344 |
| 0.60 | 0.9946666666666667 | 0.8554959785522788 | 0.005333333333333301 |
| 0.65 | 0.9909333333333333 | 0.8559607104413348 | 0.009066666666666667 |
| 0.70 | 0.9856 | 0.8565002705627706 | 0.014399999999999968 |
| 0.75 | 0.9633 | 0.8594415031661995 | 0.036699999999999955 |
| 0.80 | 0.8922666666666667 | 0.8662955768081291 | 0.10773333333333335 |
| 0.85 | 0.6269333333333333 | 0.8876010208421948 | 0.37306666666666666 |
| 0.90 | 0.16086666666666666 | 0.9289266473269788 | 0.8391333333333333 |
| 0.95 | 0.0 | None | 1.0 |

Key binary-gate operating points:

| copilot | coverage | accuracy |
|---|---|---|
| dataops | 0.9321666666666667 | 0.8231718219202575 |
| trading | 0.9966666666666667 | 0.9230769230769231 |
| purchasing | 0.8435 | 0.8498320490021735 |
| soc | 0.9978333333333333 | 0.8725572072824453 |
| s2p | 0.9536666666666667 | 0.8245368752184551 |
| pooled | 0.9447666666666666 | 0.859718448999753 |

The pooled frontier knee is θ=0.90, the first tested point reaching 90% accuracy; gains above this point trade away coverage sharply.

## R2 — Error concentration

Pooled bottom-20% confidence contains 33.5% of errors.

| Copilot | Bottom-20% error share |
|---|---|
| dataops | 0.2718808193668529 |
| trading | 0.43172823218997364 |
| purchasing | 0.32980928689883915 |
| soc | 0.35387776065742166 |
| s2p | 0.31065442936951315 |
| pooled | 0.3353967106452196 |

## R3 — Per-copilot thresholds

| Copilot | θ at 90% | Coverage | θ at 95% | Coverage |
|---|---|---|---|---|
| dataops | None | 0.0 | None | 0.0 |
| trading | 0.5 | 0.9998333333333334 | None | 0.0 |
| purchasing | None | 0.0 | None | 0.0 |
| soc | 0.9 | 0.16216666666666665 | None | 0.0 |
| s2p | None | 0.0 | None | 0.0 |

## R4 — Dollar-threshold simulation

| Copilot | Overall coverage | Auto accuracy | Escalated accuracy | Auto error rate |
|---|---|---|---|---|
| s2p | 0.79 | 0.819620253164557 | 0.8333333333333334 | 0.180379746835443 |
| purchasing | 0.7741666666666667 | 0.8314316469321852 | 0.8428044280442805 | 0.1685683530678148 |

## R5 — Confidence under conditions

| Copilot | Condition | Mean confidence | Below θ=.70 |
|---|---|---|---|
| dataops | normal | 0.8338010906141415 | 0.0165 |
| dataops | slow_drift | 0.8195954289649908 | 0.0165 |
| dataops | poison_25 | 0.7423801377276086 | 0.1895 |
| dataops | fast_break | 0.816953374542416 | 0.007 |
| trading | normal | 0.8929819859009765 | 0.0045 |
| trading | slow_drift | 0.8824586062874303 | 0.0045 |
| trading | poison_25 | 0.7889381012580152 | 0.024666666666666667 |
| trading | fast_break | 0.8910699132185309 | 0.007 |
| purchasing | normal | 0.8341385437346361 | 0.044333333333333336 |
| purchasing | slow_drift | 0.8290950747462571 | 0.044333333333333336 |
| purchasing | poison_25 | 0.7303166977559507 | 0.20533333333333334 |
| purchasing | fast_break | 0.8313691551488603 | 0.15783333333333333 |
| soc | normal | 0.8691833751696213 | 0.0036666666666666666 |
| soc | slow_drift | 0.8687186935175132 | 0.0036666666666666666 |
| soc | poison_25 | 0.7763874463694974 | 0.11283333333333333 |
| soc | fast_break | 0.8661104729674168 | 0.0021666666666666666 |
| s2p | normal | 0.8415412308762668 | 0.003 |
| s2p | slow_drift | 0.8344533607573951 | 0.003 |
| s2p | poison_25 | 0.7429411867205504 | 0.2831666666666667 |
| s2p | fast_break | 0.8451599995010202 | 0.0008333333333333334 |

## V5 verdict

Operationally useful: False. Recommended pooled θ=0.90, coverage=16.1%, accuracy=92.9%.

Conservation co-benefit: True; degradation confidence drops relative to normal operation.

Design implication: use per-copilot thresholds from R3 where coverage is acceptable; retain the dollar-tier structure as a simulation pending real value labels. Confidence routing is a routing layer, not a replacement for the binary conservation gate.

JSON: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\experiments\vld\results\conservation_routing_analysis.json; source table dimensions: 120,000 rows × 21 columns.
