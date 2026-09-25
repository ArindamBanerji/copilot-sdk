# C2: mu-learning moat across five domains

Evidence tier: REAL_COMPONENT geometry + SIMULATED streams and verification. Gap units: percentage points. Means ± sample SD over five seeds.
Primary comparison: routing_quality gap at each condition's incumbent convergence horizon. action_accuracy gaps and every checkpoint are retained in the JSON.

| Copilot | K-only routing gap | Mu+K routing gap | Widening | Seeds >2pp | Verdict |
|---|---:|---:|---:|---:|---|
| soc | 19.56 ± 5.35 | 34.68 ± 3.74 | +15.12 ± 2.87 | 5/5 | judgment-specific |
| dataops | 5.72 ± 1.10 | 3.93 ± 1.81 | -1.79 ± 1.90 | 0/5 | routing-only |
| trading | 11.22 ± 2.19 | 9.76 ± 1.96 | -1.46 ± 2.89 | 0/5 | routing-only |
| purchasing | 10.68 ± 3.41 | 11.96 ± 3.25 | +1.27 ± 5.96 | 2/5 | routing-only |
| s2p | 10.36 ± 3.19 | 5.02 ± 2.39 | -5.33 ± 2.11 | 0/5 | routing-only |

Judgment-specific under the preregistered criterion: soc.
Routing-only classification: dataops, trading, purchasing, s2p (4/5 domains).
This classification tests incremental mu gap widening; failing it is not proof of no mu specificity, and it does not independently establish a positive K-only moat.

## Sanity and reproducibility
All SOC/DataOps seeds 42, 123, 7 reproduce EXP-2 per-seed routing/action gaps, mu drift and full held-out checkpoints. Their three-seed mean widening reproduces +15.935185pp / −2.509259pp. The prompt's seed42-versus-three-seed-mean check is invalid; seed42 is +11.666667pp / −3.333333pp.
Every newly computed seed/domain has two independent stream/learner/cache rebuilds with byte-identical canonical JSON. Existing EXP1 SOC/DataOps K-only controls are reused.

## Protocol and interpretation
SOC/DataOps S_B is unchanged. For the three new domains the preregistered extension repeats the six-factor perturbation vectors cyclically and truncates/normalizes DataOps category weights to [0.0625, 0.125, 0.125, 0.125, 0.5625]; action acceptance uses the first A DataOps entries. The exact per-factor vectors, category/action names and realized distribution distances are in each row.
All target tests freeze before S_B generation in each batch. The actual inherited split is 2000 training / 400 development / 600 held-out; development convergence uses a 0.5pp range over three checkpoints, minimum 500 and maximum 2000. Joint parity requires routing_quality and action_accuracy within 1pp for three consecutive checkpoints. No held-out stopping.
Centroid updates reuse the existing ungated ProfileScorer component. Fixed synthetic oracle labels and informative dimensions remain a limitation. This is not operational evidence or an oracle-separated study.
No multi-step evidence richness variable was measured. Domain differences alone do not establish that mechanism; the results characterize these geometries and this one alternative-firm profile.

## Common-horizon sensitivity
| Copilot | Routing widening at K-only incumbent horizon (pp) |
|---|---:|
| soc | +12.87 ± 2.79 |
| dataops | -2.98 ± 0.56 |
| trading | -1.73 ± 2.65 |
| purchasing | +5.96 ± 7.41 |
| s2p | -4.34 ± 3.29 |

## Null stakes
4/5 domains are routing-only: the broad judgment-specificity claim must narrow to the measured subset. An 'evidence-rich domains' explanation remains untested.
Stopping-horizon sensitivity is disclosed rather than used to change the preregistered verdict.
