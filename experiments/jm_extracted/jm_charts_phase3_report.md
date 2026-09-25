# JM-CHARTS Phase 3 Verification Report

Date: Sep 20, 2026

Phase 3 reworked only the 14 Phase 2 failures. All protocols use deterministic seeds; expected values were verification targets, not tuning objectives.

## Reworked charts

| # | File | Diagnosis | Phase 3 correction | New result | Status |
|---:|---|---|---|---|---|
| 2 | `e_jm_1_benefit_scatter.png` | design_flaw | Paired retained-memory and cold-start arms on identical Person-B labels, observations, and noise, and corrected the final 300-decision window. | +10.59pp retained-memory advantage; 95% CI [+10.01, +11.17]pp (60 paired trials; seed 42) | PASS |
| 6 | `e_jm_3_trajectories.png` | design_flaw | Held the target stream and operator difficulty fixed across cold, partial, and warm arms; varied only centroid initialization. | Transfer speed increases with similarity (Spearman rho=0.829); warm speedup reaches 1.56-1.78x for similarity 0.6-1.0 (60 paired trials/level; seed 42) | PASS |
| 7 | `e_jm_3_convergence_speed.png` | design_flaw | Used paired target streams and measured decisions to 80% rolling accuracy for initialization-only comparisons. | Warm-start speedup is 1.77x at similarity 0.6, 1.78x at 0.8, and 1.56x at 1.0 (60 paired trials/level; seed 42) | PASS |
| 9 | `e_jm_4_trajectories.png` | design_flaw | Replaced the always-firing toy gate with the SDK recent-window quality rule (100 decisions, q<0.75) and routed paused cases to a fixed human-review control. | Conservation improves post-change quality by +3.12 to +28.59pp across four degradation streams (100 trials; seed 42) | PASS |
| 10 | `e_jm_4_conservation_status.png` | design_flaw | Calibrated status transitions against a clean control using the SDK recent-window quality threshold. | Clean control remains GREEN (0% false positives); degraded streams transition to PAUSED with class-dependent timing (100 trials; seed 42) | PASS |
| 11 | `e_jm_4_degradation_depth.png` | design_flaw | Measured paired post-degradation quality with and without calibrated conservation intervention. | Constrained degradation is shallower by +28.59, +22.07, +13.30, and +3.12pp; all 95% CIs exclude zero (100 trials; seed 42) | PASS |
| 12 | `e_jm_4_detection_rates.png` | genuine_negative | Removed clean-stream false positives with the SDK recent-window gate and evaluated four degradation classes without tuning the threshold per class. | 0% clean false positives; detection is 100% for personnel change, 30% corruption, and gradual drift, but 57% for sparse 10% adversarial events (100 trials; seed 42) | FAIL (mismatch) |
| 15 | `e_jm_5_convergence.png` | bug | Computed Spearman and Kendall directly on true and learned factor values instead of correlating argsort index arrays. | At 2,000 decisions: Spearman 0.440 +/-0.029, Kendall 0.352 +/-0.025, top-3 overlap 0.636 +/-0.020, cosine 0.825 +/-0.011 (95% CI half-width; 500 runs; seed 42) | PASS |
| 17 | `e_jm_6_trajectories.png` | genuine_negative | Replaced the toy loop with existing five-copilot real K-learning outputs and measured decision utility as routing quality times action accuracy. | Real K-learning gains +21.96pp over frozen control at 500 decisions, but the raw utility power exponent is c=0.643 (R2=0.955), not super-linear (five deterministic copilot seeds) | FAIL (mismatch) |
| 18 | `e_jm_6_iks_trajectory.png` | design_flaw | Used real K-learning utility and defined approved scope with the SDK recent-quality threshold q>=0.75. | Eligible deployment scope expands from 3/5 to 5/5 while mean real K-learning utility rises from 0.445 to 0.618 (five deterministic copilot seeds) | PASS |
| 19 | `e_jm_6_combined_metric.png` | design_flaw | Replaced the identically-zero toy metric with real mean utility multiplied by conservation-eligible deployment fraction. | Combined utility-scope metric has c=1.243 with R2=0.795 and non-zero amplitude (five deterministic copilot seeds) | PASS |
| 21 | `e_jm_6b_exponent_ci.png` | genuine_negative | Bootstrapped whole copilot deployments, recomputed utility and eligible scope, and refit the exponent in each of 2,000 resamples. | Combined point estimate c=1.243; deployment-bootstrap 95% CI [0.355, 1.817] crosses c=1 (bootstrap seed 6042; 2,000 resamples) | FAIL (mismatch) |
| 22 | `e_jm_7_accuracy.png` | design_flaw | Allocated independent weight arrays per entity and added a distinct hierarchical arm with a shared global prior; all arms use the same imbalanced stream. | Hierarchical entity-contextualized accuracy exceeds global by +4.67pp; 95% CI [+3.90, +5.44]pp (50 paired trials; seed 42) | PASS |
| 24 | `fig2_centroid_geometry.png` | bug | Sampled action-conditioned observations and updated the matching centroid cell; retained a fixed late-snapshot PCA basis for all panels. | Silhouette improves from 0.257 at 50 decisions to 0.665 at 500 and 0.701 at 3,000 (seed 42) | PASS |

## Diagnosis summary

- Bugs fixed: 2 charts (#15 rank statistics; #24 action-conditioned centroid generation).
- Design flaws fixed: 9 charts (#2, #6, #7, #9, #10, #11, #18, #19, #22).
- Genuine negatives after correction: 3 charts (#12, #17, #21).
- Final score: 21/24 PASS, 3/24 FAIL, 0 BLOCKED.

## Genuine findings and paper corrections

1. E-JM-4 should not claim 97-100% detection across every degradation class. At 0% clean false positives, the calibrated gate detects personnel change, 30% corruption, and gradual drift in 100% of trials, but sparse 10% adversarial events in 57%.
2. E-JM-6 should not describe raw K-learning utility as super-linear. The real five-copilot trajectory is strongly improving (+21.96pp over frozen control) but sub-linear, c=0.643 (R2=0.955).
3. E-JM-6b may report the combined utility-scope point estimate c=1.243, but must not call c>1 robust: the deployment-bootstrap 95% CI is [0.355, 1.817].

## FIGURE-2

The Phase 2 stream ignored action when generating observations. With action-conditioned geometry and cell-specific updates, fixed-basis PCA silhouettes rise from 0.257 (50 decisions) to 0.665 (500) and 0.701 (3,000). The centroids visibly differentiate; this is simulated experimental output, not a schematic.

## Appendix B correction

Appendix B should state: all 24 figures were rendered and checked; 21 claims pass under corrected paired/calibrated protocols. Three claims require qualification: sparse adversarial detection is 57% at 0% clean false positives; raw K-learning utility is improving but sub-linear (c=0.643); and the combined c=1.243 estimate is not statistically robust because its deployment-bootstrap 95% CI [0.355, 1.817] includes one. Seeds are 42 for rebuilt simulations, 6042 for the deployment bootstrap, and the real K-learning trajectories retain their five recorded seeds.

## Seeds and confidence intervals

- Rebuilt paired simulations: seed 42; trial-level 95% t intervals.
- E-JM-5: seed 42; 500 runs; 95% t intervals.
- E-JM-6: recorded copilot seeds 20260912, 20261657, 20261988, 20261237, 20261189.
- E-JM-6b: bootstrap seed 6042; 2,000 whole-deployment resamples; percentile 95% CI.
