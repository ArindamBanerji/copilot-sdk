# C4 Gamma Re-Convergence — GATE-B (Analytic Only)

No runnable two-phase re-convergence harness for the requested C4 estimand was found in the SDK scripts/experiments, the GAE Python tree, or the searched design documents and harness filename patterns. The K-learning harness measures learn-versus-frozen performance over time; it does not measure the ratio of two convergence phases separated by a disruption. No K-curve was relabeled as gamma and no new simulation was run.

The stated theorem is conditional: gamma = N_half,1 / N_half,2 > 1 is predicted when the initial geometry error epsilon_sim is much smaller than the disruption magnitude ||Delta||. If the initial geometry already lies near the post-disruption truth, Phase 1 can start unusually close to its target and gamma may fall below 1. The testable C4 condition is epsilon_sim << ||Delta||.

## Available condition table

| Evidence | epsilon_sim / archived epsilon | ||Delta|| | gamma | Condition result |
|---|---:|---:|---:|---|
| Current C4: each of five copilots × seeds 42, 123, 7 | Not measured | Not measured | Not measured | Unclassifiable; no runnable harness or outputs |
| Archived Oracle separation v8 | Not reported (archived epsilon parameter 0.05) | Not reported | 0.714 (<1); N_half,1=25, N_half,2=35 | Below the old 0.125 threshold; cannot map to the current epsilon_sim versus disruption condition |
| Archived Oracle separation v3 | Not reported (archived epsilon parameter 0.20) | Not reported | 1.033 (>1); N_half,1=125, N_half,2=121 | Above the old 0.125 threshold; cannot map to the current epsilon_sim versus disruption condition |

The archived binary points are documented in `docs/design/blogs/new_docs/math_synopsis_v20.md`. They record one gamma below and one above 1 under an older epsilon_firm parameterization. They do not report ||Delta||, per-copilot/seed outcomes, or the current C4 geometry measurements. Historical text also discusses a Phase-1-starts-near-GT artifact, but the searched repository did not expose runnable provenance or values sufficient to classify those observations against the current condition.

## Interpretation

The current geometric-condition claim is neither confirmed nor falsified by C4. Null-stakes are unresolved: no new measurement tested whether gamma > 1 holds when epsilon_sim << ||Delta||. The paper can retain only a clearly labeled conditional analytic mechanism; the old binary points must not be presented as validation of this current geometric condition. Gamma magnitude remains pilot-only (T-R).

Tier: REAL_COMPONENT geometry + SIMULATED streams/disruption. Labels are geometry-derived nearest-centroid labels; there is no LLM prior.
