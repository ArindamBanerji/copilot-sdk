# C3: label-acquisition breadth

Evidence tier: REAL_COMPONENT geometry + SIMULATED streams/verification/label sources. All gaps are percentage points.
Residual gaps use incumbent final-three mean minus competitor endpoint, matching B2 access tables. JSON also reports incumbent-horizon comparisons, both metrics at every checkpoint, label counts and costs.
B2 rows are seed42 references, NOT reruns. C3 rows are means ± sample SD over seeds42/123/7.

| Copilot | Source/access | Routing gap | Action gap | Label accuracy | Joint parity |
|---|---|---:|---:|---:|---|
| soc | B2 3a (seed42) | 21.61 | 26.83 | unmeasured | not_reached |
| soc | B2 3b_10 (seed42) | 18.86 | 18.17 | 100.0% | not_reached |
| soc | B2 3b_50 (seed42) | 6.03 | 7.17 | 100.0% | not_reached |
| soc | B2 3c_eps10 (seed42) | 0.69 | 3.33 | 90.0% | not_reached |
| soc | B2 3c_eps25 (seed42) | 0.78 | 3.00 | 74.9% | not_reached |
| soc | WS-1 (3 seeds) | 10.40 ± 0.97 | 11.30 ± 3.76 | 30.5% | 0/3 |
| soc | FM-1 (3 seeds) | 12.79 ± 3.43 | 16.96 ± 3.88 | 80.0% | 0/3 |
| soc | FM-2 (3 seeds) | 11.76 ± 3.22 | 15.69 ± 4.44 | 90.0% | 0/3 |
| dataops | B2 3a (seed42) | 7.00 | 12.50 | unmeasured | not_reached |
| dataops | B2 3b_10 (seed42) | 4.50 | 12.83 | 100.0% | not_reached |
| dataops | B2 3b_50 (seed42) | -1.50 | 1.83 | 100.0% | not_reached |
| dataops | B2 3c_eps10 (seed42) | 2.92 | 4.67 | 90.2% | not_reached |
| dataops | B2 3c_eps25 (seed42) | 2.67 | 3.17 | 75.0% | not_reached |
| dataops | WS-1 (3 seeds) | 3.65 ± 1.45 | 14.02 ± 2.97 | 16.3% | 0/3 |
| dataops | FM-1 (3 seeds) | 4.73 ± 0.23 | 11.85 ± 1.73 | 80.0% | 0/3 |
| dataops | FM-2 (3 seeds) | 4.76 ± 1.21 | 12.07 ± 3.12 | 90.0% | 0/3 |

## Source definitions and access boundaries
WS-1 uses only S_B training surface statistics: equally weighted standardized factor scores binned at action-count quantiles. Fixed low-to-high action orders are SOC suppress/monitor/investigate/escalate and DataOps auto_approve/investigate/refer_to_specialist/escalate_to_owner/pause_downstream. Means, SDs and cutpoints are exported per seed. No oracle labels fit this heuristic.
FM-1/FM-2 are simulated noisy proxies, not measured foundation-model performance: exactly 20%/10% labels flipped in blocks of ten to another action. They label S_B, not S_A.
Credit uses the existing received-label helper. Development correctness and informative tags come from the pseudo-labels; no clean-label stopping. All conditions evaluate the identical frozen S_A held-out set and use unchanged B2 joint parity/convergence rules.
The inherited training evidence availability is oracle-coupled. This experiment is not oracle-separated; it isolates label-source access conditional on that synthetic evidence model.
B2 3a updates K using its own predictions and surface-only evidence; it is not a frozen-K control. B2 3c also delays labels by 50 decisions. These distinctions matter for comparing conditions.

## Verdict and acquisition cost
No tested new source reaches sustained joint parity. The preregistered claim strengthens within these profiles and horizons. This does NOT establish that verified labels are universally un-acquirable: source accuracy, firm distribution and access are distinct axes.

| Copilot | Source | Pseudo-labels used (mean) | Evidence reads (mean) |
|---|---|---:|---:|
| soc | WS-1 | 533.3 | 1066.7 |
| soc | FM-1 | 516.7 | 1033.3 |
| soc | FM-2 | 533.3 | 1066.7 |
| dataops | WS-1 | 733.3 | 1466.7 |
| dataops | FM-1 | 583.3 | 1166.7 |
| dataops | FM-2 | 583.3 | 1166.7 |

No dollar/API acquisition cost is measured; the labelers are local simulations.

## Quality threshold and plot-ready access data
The JSON stores every B2 reference and C3 condition with label accuracy, access, routing gap, action gap, parity and costs. Do not collapse access-to-S_A and accuracy-on-S_B into one causal scale.
soc: neither 80% nor 90% S_B pseudo-label accuracy reaches parity. No sufficient label-quality threshold is identified or bracketed; interpolation is unjustified.
dataops: neither 80% nor 90% S_B pseudo-label accuracy reaches parity. No sufficient label-quality threshold is identified or bracketed; interpolation is unjustified.

## Null stakes and limitations
Parity uses routing_quality AND action_accuracy within 1pp over three checkpoints. Later loss is recorded. Non-parity is censored at the arm's actual development-convergence stop, at most 2000.
One heuristic and two noise proxies cannot exhaust realistic label acquisition. No causal claim that labels alone explain the moat follows when the competitor also has a different distribution.
Two independent complete stream/learner/cache rebuilds per seed must match byte for byte.
