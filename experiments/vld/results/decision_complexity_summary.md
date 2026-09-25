# Decision-complexity characterization

Tier: REAL_COMPONENT geometry + SIMULATED decisions/evidence/verification. Labels/action_accuracy are geometry-derived; multi-enterprise S2P is CONSTRUCTED.
Complexity measures are descriptive. Capability sources are KE-1, C2, BUDGET, F-2, and the seeded oracle ladder; multi-S2P capabilities not run are null.

## Complexity measures

| Configuration | Intrinsic dim | m_conditional | Action separability | Evidence-chain length | Outcome entropy (bits) |
|---|---:|---:|---:|---:|---:|
| dataops | 4.866 | 0.407 | 0.938 | 2.00 | 0.033 |
| trading | 2.712 | 0.503 | 0.575 | 1.00 | 0.045 |
| purchasing | 3.887 | 0.274 | 0.625 | 2.00 | 0.165 |
| soc | 1.159 | 0.138 | 0.824 | 1.00 | 0.020 |
| s2p | 1.911 | 0.212 | 0.666 | 1.00 | 0.000 |
| s2p_multi_enterprise | 2.741 | 0.279 | 0.552 | 2.00 | 0.000 |

## Capability results

| Configuration | K gain (pp action_accuracy) | μ widening (pp routing_quality) | B2/full efficiency | Clean PAUSE fraction | Readout gap (pp action_accuracy) |
|---|---:|---:|---:|---:|---:|
| dataops | +32.000 | -1.789 | +0.844 | +0.247 | +55.611 |
| trading | +14.000 | -1.461 | +0.907 | +0.013 | +47.333 |
| purchasing | +30.000 | +1.272 | +0.798 | +0.461 | +68.111 |
| soc | +14.000 | +15.122 | +0.917 | +0.007 | +0.000 |
| s2p | +6.000 | -5.333 | +0.841 | +0.016 | +16.222 |
| s2p_multi_enterprise | +16.444 | not measured | +0.839 | not measured | +16.111 |

## Spearman correlations

| Complexity measure | k_curve_gain | mu_widening | budget_frontier_efficiency | conservation_false_pause | readout_gap |
|---|---:|---:|---:|---:|---:|
| intrinsic_dimensionality | +0.90 (n=6) | -0.30 (n=5) | -0.54 (n=6) | +0.80 (n=5) | +0.77 (n=6) |
| m_conditional | +0.41 (n=6) | -0.30 (n=5) | -0.03 (n=6) | +0.30 (n=5) | +0.49 (n=6) |
| action_separability | +0.17 (n=6) | -0.10 (n=5) | +0.43 (n=6) | +0.00 (n=5) | +0.09 (n=6) |
| evidence_chain_length | +0.89 (n=6) | +0.00 (n=5) | -0.68 (n=6) | +0.87 (n=5) | +0.49 (n=6) |
| outcome_entropy | +0.47 (n=6) | +0.40 (n=5) | -0.06 (n=6) | +0.50 (n=5) | +0.75 (n=6) |

## S2P within-domain contrast: complexity_increased=True; RGI proxy increased=True; within_domain_proof=True.
RGI value is operationalized as paired K-learning action_accuracy gain, not as a general business-value measure. The constructed multi-firm profile includes three B2-derived geometries and conditional approval hops; its μ widening and conservation PAUSE rate are not measured.

## Scatter artifact

Plot-ready long-form points are in `decision_complexity_scatter.csv`. The strongest mean-absolute correlation is `intrinsic_dimensionality` (0.66); no significance threshold is used.

## Verdict: COMPLEXITY-IS-THE-AXIS

Complexity is the axis in these tested synthetic points: multiple complexity measures track capability outcomes, and the S2P within-domain contrast raises both measured complexity and the K-learning action_accuracy gain. Treat this as a targeting hypothesis, not a complexity law.

## Paper sentence

Across five exported geometries, the measured complexity features did not establish a predictive law for capability outcomes; a constructed three-firm S2P contrast is exploratory and cannot substitute for a multi-enterprise fixture. Spearman coefficients are descriptive at n=5–6, with low p-value power.
