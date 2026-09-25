# C5 Conservation Gate Detection Lag

Metric: `action_accuracy` (geometry-derived selected action equals the truth action). Tier: REAL_COMPONENT geometry + SIMULATED streams/degradation.

## Gate behavior summary
- The standalone evaluator checks the gate after each verified decision; degradation begins at decision 501 after 500 baseline decisions. It replicates the two checks in `scorer._conservation_pause()`:
  - last-100 verified accuracy must stay above 75% (hard floor)
  - `alpha * q_eff * V` must satisfy `compute_theta_min(alpha, V) = 23.53 / (alpha * V)`
- For sustained degradation, it is a measurable lag rather than a prevention mechanism.

## Detection lag summary

Mean lag is over seeds that were ALLOW at decision 500 and first paused after onset. Seeds already in PAUSE at decision 500 are reported separately and are not credited as detections.

| degradation | copilot | mean lag (records) | detected/3 | already PAUSE at 500 |
|---|---|---:|---:|---:|
| slow drift | dataops | 217.5 | 2/3 | 0 |
| label poisoning 10% | dataops | 102 | 3/3 | 0 |
| label poisoning 25% | dataops | 50.666666666666664 | 3/3 | 0 |
| label poisoning 50% | dataops | 30.666666666666668 | 3/3 | 0 |
| fast break (within 100) | dataops | 54.666666666666664 | 3/3 | 0 |
| slow drift | trading | None | 0/3 | 0 |
| label poisoning 10% | trading | None | 0/3 | 0 |
| label poisoning 25% | trading | 90.66666666666667 | 3/3 | 0 |
| label poisoning 50% | trading | 34.666666666666664 | 3/3 | 0 |
| fast break (within 100) | trading | — | 0/3 | 0 |
| slow drift | purchasing | None | 0/3 | 2 |
| label poisoning 10% | purchasing | 41 | 1/3 | 2 |
| label poisoning 25% | purchasing | 34 | 1/3 | 2 |
| label poisoning 50% | purchasing | 9 | 1/3 | 2 |
| fast break (within 100) | purchasing | — | 0/3 | 0 |
| slow drift | soc | None | 0/3 | 0 |
| label poisoning 10% | soc | 219 | 1/3 | 0 |
| label poisoning 25% | soc | 90.33333333333333 | 3/3 | 0 |
| label poisoning 50% | soc | 44 | 3/3 | 0 |
| fast break (within 100) | soc | — | 0/3 | 0 |
| slow drift | s2p | 328 | 2/3 | 0 |
| label poisoning 10% | s2p | 165.66666666666666 | 3/3 | 0 |
| label poisoning 25% | s2p | 40 | 3/3 | 0 |
| label poisoning 50% | s2p | 26 | 3/3 | 0 |
| fast break (within 100) | s2p | — | 0/3 | 0 |

## Fast-break miss rate
- 3/15 runs paused within 100 records; miss rate: 80.0%. 3/15 eventually paused within the run budget.
- Check A uses a rolling 100-record window that includes pre-break records; it can fire before 100 post-break records when enough outcomes in that mixed window are incorrect. This occurred for DataOps in 3/3 seeds, so the preregistered expectation of an across-the-board fast-break miss was not supported.

## Clean control PAUSE-decision rates

The rate is PAUSE decisions divided by all 900 decisions, not a count of distinct pause episodes.

| copilot | PAUSE decisions | decisions | PAUSE-decision rate |
|---|---:|---:|---:|
| dataops | 370 | 2700 | 0.137037 |
| trading | 20 | 2700 | 0.007407 |
| purchasing | 939 | 2700 | 0.347778 |
| soc | 10 | 2700 | 0.003704 |
| s2p | 95 | 2700 | 0.035185 |

| copilot | seed | PAUSE decisions | total decisions | PAUSE-decision rate |
|---|---:|---:|---:|---:|
| dataops | 42 | 104 | 900 | 0.115556 |
| dataops | 123 | 120 | 900 | 0.133333 |
| dataops | 7 | 146 | 900 | 0.162222 |
| trading | 42 | 4 | 900 | 0.004444 |
| trading | 123 | 16 | 900 | 0.017778 |
| trading | 7 | 0 | 900 | 0.000000 |
| purchasing | 42 | 286 | 900 | 0.317778 |
| purchasing | 123 | 153 | 900 | 0.170000 |
| purchasing | 7 | 500 | 900 | 0.555556 |
| soc | 42 | 10 | 900 | 0.011111 |
| soc | 123 | 0 | 900 | 0.000000 |
| soc | 7 | 0 | 900 | 0.000000 |
| s2p | 42 | 0 | 900 | 0.000000 |
| s2p | 123 | 80 | 900 | 0.088889 |
| s2p | 7 | 15 | 900 | 0.016667 |

## Honest paper sentence
The SDK composite conservation gate (75%/last-100 + check-B volume floor) showed attributable detected-run lags from 9 to 328 records across slow-drift and label-poisoning scenarios; it paused within 100 records in 3/15 fast-break runs (DataOps 3/3), while 12/15 were not paused within that interval. This measures detection, not prevention, and a faster trigger for missed fast breaks remains future work.

## Relevance to self-poisoning concern
- Poisoning detection was stronger at higher corruption rates, but low-rate poisoning and slow drift were missed in some seeds or domains.
- Fast breaks were missed within 100 records in 12/15 runs, while DataOps triggered in all three seeds; clean-control pause rates also varied sharply by copilot.
