# JM-CHARTS Phase 2 Verification Report

Date: September 20, 2026  
Seeds: archived seed or seed base 42; `PYTHONHASHSEED=0` for E-JM-4  
Output: `experiments/jm_extracted/charts/` and `experiments/vld/charts/`

## Outcome

All 24 requested PNG files rendered on a light background at 300 dpi. Ten charts pass their stated numerical or structural check; fourteen fail because the actual result contradicts the claim or the statistic is not identified. No chart is blocked.

The prerequisite `experiments/jm_extracted/jm_experiment_map.json` was absent. The 23-chart list was reconstructed from the extracted runners and the paper's experiment specification. The three auxiliary archived charts not in the paper manifest were excluded.

## Per-experiment results

- **E-JM-1 — Personnel change:** 29/30 changes detected (96.7%; Wilson 95% CI 83.33-99.41%), mean delay 65.2 decisions. Judgment memory underperformed flat DB by 1.69pp and was better in only 9/30 trials. The final recovery-window summary is `NaN` because the archived boundary check excludes an exactly 800-decision series.
- **E-JM-2 — Inversion prevalence:** noise-attracted trust traps reproduced at 93.6% (468/500; Wilson 95% CI 91.10-95.43%). This is conditional on a synthetic generator explicitly attracted to noisy factors, not an empirical population estimate.
- **E-JM-3 — Transfer:** speedups were non-monotonic: 2.06x at similarity 0.0, 1.09x at 0.2, 1.88x at 0.4, 1.16x at 0.6, 1.48x at 0.8, and 1.97x at 1.0. Because target arms draw different operator accuracies and streams, the run does not isolate similarity-driven transfer. The negative-transfer checkpoints nevertheless reproduce 25% at 0.0 and 0% at 0.4.
- **E-JM-4 — Conservation safety:** detection was 100%, but the no-degradation false-positive rate was also 100%. Conservation reduced post-degradation accuracy by 7.89pp (personnel), 11.57pp (corruption), 6.54pp (drift), and 10.28pp (adversarial). The safety claim fails.
- **E-JM-4b — Recalibration:** reproduced 86.80% gap closure, with late-stage accuracy 0.4965 unconstrained, 0.2970 frozen, and 0.4702 recalibrated. The implementation performs a full reset, not the paper's stated 15% prior retention.
- **E-JM-5 — Weight discovery:** reproduced 63.4% at 2,000 decisions (naive Wilson 95% CI 59.09-67.51%). All domains were constructed with a top-factor trap, and the rank-correlation panels use order arrays rather than rank vectors; the discovery percentage passes, but the rank-convergence chart does not.
- **E-JM-6 — Operational compounding:** compounding accuracy is sub-linear (`c=0.100`, power-fit `R²=0.047`). No category reaches the approval threshold, so approved scope and the combined metric remain zero. The reported combined exponent `c=1.13865` is an unidentifiable zero-amplitude fit artifact.
- **E-JM-6b — Bayesian comparison:** DK late accuracy was 37.06% versus 35.85% for Bayesian, reproducing +1.21pp. The exponent bootstrap returned the identical value in all 100 samples: 95% CI `[1.13865, 1.13865]`; this is degenerate rather than evidence of robustness.
- **E-JM-7 — Cross-type interaction:** per-entity weighting detected 8/35 traps (22.86%; Wilson 95% CI 12.07-39.02%) versus 3/35 globally (8.57%; CI 2.96-22.38%), a 2.67x ratio. Accuracy improved only 0.12pp. The separate-store arm is code-identical to the global arm, so this does not validate a shared-vs-stitched architecture claim.

## Verification table

| # | File | Source | Expected | Actual | Result | Concerns | Changes |
|---:|---|---|---|---|---|---|---|
| 1 | `e_jm_1_trajectory.png` | RE-RUN | 97-100% detection | 96.7%, delay 65.2 | PASS | Unpaired arms; final-window bug | 300 dpi |
| 2 | `e_jm_1_benefit_scatter.png` | RE-RUN | JM improves recovery | -1.69pp; 9/30 better | FAIL | Unpaired arms | 300 dpi |
| 3 | `e_jm_2_inversion_rates.png` | RE-RUN | 93.6% | 93.6% | PASS | Model-conditional prevalence | 300 dpi |
| 4 | `e_jm_2_radar_worst_case.png` | RE-RUN | Visible inversion | Visible worst-case inversion | PASS | Selected synthetic extreme | 300 dpi |
| 5 | `e_jm_2_spearman_dist.png` | RE-RUN | Inverted vs control | -0.056 vs 1.000 | PASS | Generator-dependent | 300 dpi |
| 6 | `e_jm_3_trajectories.png` | RE-RUN | Related warm-start advantage | Strongest at similarity 0.0 | FAIL | Unpaired operator/stream | 300 dpi |
| 7 | `e_jm_3_convergence_speed.png` | RE-RUN | 1.5-2x moderate/high | 1.16-1.97x; non-monotonic | FAIL | Similarity not isolated | 300 dpi |
| 8 | `e_jm_3_negative_transfer.png` | RE-RUN | 25% at 0.0; 0% at 0.4 | 25%; 0% | PASS | Unpaired arms | 300 dpi |
| 9 | `e_jm_4_trajectories.png` | RE-RUN | Conservation protects | 6.54-11.57pp worse | FAIL | 100% false positives | Hash seed + 300 dpi |
| 10 | `e_jm_4_conservation_status.png` | RE-RUN | Specific status response | Control also pauses 30/30 | FAIL | Non-specific gate | Hash seed + 300 dpi |
| 11 | `e_jm_4_degradation_depth.png` | RE-RUN | Shallower constrained loss | Lower constrained quality | FAIL | Freeze blocks adaptation | Hash seed + 300 dpi |
| 12 | `e_jm_4_detection_rates.png` | RE-RUN | 97-100% useful detection | 100% TP and 100% FP | FAIL | No specificity | Hash seed + 300 dpi |
| 13 | `e_jm_4b_trajectory.png` | ADAPTED | About 87% recovery | 86.80% | PASS | Full reset, not 15% retention | Matplotlib compatibility |
| 14 | `e_jm_4b_recovery_box.png` | ADAPTED | Recalibration near unconstrained | 0.4702 vs 0.4965 | PASS | Protocol mismatch | Matplotlib compatibility |
| 15 | `e_jm_5_convergence.png` | RE-RUN | Valid weight convergence | top-3 0.669; cosine 0.848 | FAIL | Invalid rank metrics; encoded relation | 300 dpi |
| 16 | `e_jm_5_discovery_rate.png` | RE-RUN | 63% | 63.4% | PASS | Clustered, constructed traps | 300 dpi |
| 17 | `e_jm_6_trajectories.png` | RE-RUN | Super-linear accuracy | `c=0.100`, `R²=0.047` | FAIL | Accuracy does not compound | UTF-8 + 300 dpi |
| 18 | `e_jm_6_iks_trajectory.png` | RE-RUN | Scope expansion | Approved scope stays 0/6 | FAIL | Threshold never passed | 300 dpi |
| 19 | `e_jm_6_combined_metric.png` | RE-RUN | `c≈1.14` increasing returns | Metric is zero; fit says 1.139 | FAIL | Unidentified zero-amplitude fit | 300 dpi |
| 20 | `e_jm_6b_dk_vs_bayesian.png` | RE-RUN | +1.21pp | +1.21pp | PASS | Different estimator objectives | UTF-8 + 300 dpi |
| 21 | `e_jm_6b_exponent_ci.png` | RE-RUN | Informative `c>1` CI | `[1.13865, 1.13865]` | FAIL | Degenerate bootstrap | 300 dpi |
| 22 | `e_jm_7_accuracy.png` | RE-RUN | Meaningful accuracy gain | +0.12pp | FAIL | Separate/global identical | 300 dpi |
| 23 | `e_jm_7_trap_detection.png` | RE-RUN | About 2.7x | 2.67x | PASS | Constructed comparator | 300 dpi |
| 24 | `fig2_centroid_geometry.png` | ADAPTED | Increasing separation | -0.102, -0.142, -0.154 | FAIL | Snapshot reproduction | Added fixed-basis diagnostic |

## FIGURE-2

The archived E-JM-6 runner did not expose centroid snapshots. A typed adaptation reproduced its compounding arm at seed 42 and captured tensors after 250, 1,500, and 3,000 decisions. PCA components were fit once on the late snapshot and applied unchanged to all panels. Action-label silhouette scores were:

- 250 decisions: **-0.102**
- 1,500 decisions: **-0.142**
- 3,000 decisions: **-0.154**

The centroids do not differentiate; separation slightly worsens. The chart uses real simulated snapshots and is not a schematic.

## Adaptations

1. A typed runner forces archived Matplotlib outputs to white-background 300-dpi PNGs without modifying experiment logic.
2. E-JM-4 ran with `PYTHONHASHSEED=0` because its seeds include Python string hashes.
3. E-JM-4b changed only the Matplotlib 3.8 boxplot keyword (`tick_labels` to `labels`) and added a type annotation; mypy passes.
4. FIGURE-2 uses a new typed snapshot reproduction because the archived runner discarded centroid tensors.

## Summary

- Rendered: **24/24**
- PASS: **10**
- FAIL (mismatch or invalid statistic): **14**
- BLOCKED: **0**
- Provenance: **0 saved-original, 21 re-run, 3 adapted, 0 rebuilt**

## Appendix B correction

Appendix B should no longer say that E-JM-1 through E-JM-7 were not run or that their charts are unavailable. The accurate status is:

> The archived synthetic E-JM suite was recovered and re-run on September 20, 2026. All 23 experiment charts plus FIGURE-2 rendered at 300 dpi. Ten chart-level checks reproduced their stated result and fourteen failed or exposed invalid statistics. E-JM-4's safety claim, E-JM-6's compounding claim, and FIGURE-2's centroid-separation claim are not supported by the recovered harness. E-JM-3 does not isolate transfer causality. E-JM-4b, E-JM-5, E-JM-6b, and E-JM-7 require the protocol qualifications documented in the Phase 2 verification report.
