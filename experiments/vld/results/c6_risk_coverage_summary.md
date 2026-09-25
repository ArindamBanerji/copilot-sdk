# C6 held-out risk-coverage: five-domain table

Date: September 14, 2026. Metric: action_accuracy on accepted decisions; all rows REAL_COMPONENT geometry + SIMULATED decisions/evidence/verification.
Trading/S2P use roots42/123/7. DataOps/Purchasing/SOC below retain the prior five-replicate three-way held-out results, as requested; new same-three-seed runs for those domains are in C1.

| Copilot | Replicates | Target coverage | Actual coverage % | Accepted action_accuracy % | Baseline action_accuracy % | Lift pp | Source |
|---|---:|---:|---:|---:|---:|---:|---|
| dataops | 5 | 90% | 90.88 | 81.30 | 76.76 | 4.54 | prior heldout v1 |
| dataops | 5 | 75% | 74.04 | 87.74 | 76.76 | 10.98 | prior heldout v1 |
| dataops | 5 | 50% | 51.56 | 95.26 | 76.76 | 18.50 | prior heldout v1 |
| purchasing | 5 | 90% | 89.28 | 79.13 | 74.76 | 4.37 | prior heldout v1 |
| purchasing | 5 | 75% | 74.56 | 88.12 | 74.76 | 13.36 | prior heldout v1 |
| purchasing | 5 | 50% | 49.80 | 100.00 | 74.76 | 25.24 | prior heldout v1 |
| soc | 5 | 90% | 90.40 | 96.98 | 91.08 | 5.90 | prior heldout v1 |
| soc | 5 | 75% | 73.64 | 100.00 | 91.08 | 8.92 | prior heldout v1 |
| soc | 5 | 50% | 50.56 | 100.00 | 91.08 | 8.92 | prior heldout v1 |
| trading | 3 | 90% | 89.93 | 93.33 | 92.07 | 1.26 | C6 new run |
| trading | 3 | 75% | 76.47 | 92.22 | 92.07 | 0.16 | C6 new run |
| trading | 3 | 50% | 53.40 | 100.00 | 92.07 | 7.93 | C6 new run |
| s2p | 3 | 90% | 90.67 | 83.38 | 82.33 | 1.05 | C6 new run |
| s2p | 3 | 75% | 75.47 | 82.59 | 82.33 | 0.25 | C6 new run |
| s2p | 3 | 50% | 50.47 | 100.00 | 82.33 | 17.67 | C6 new run |

| New copilot | Full-grid monotonic seeds | Requested90/75/50 monotonic seeds | Aggregate full-grid monotonic |
|---|---:|---:|---|
| trading | 0/3 | 0/3 | False |
| s2p | 0/3 | 0/3 | False |

Domain-specific: at least one Trading/S2P seed has a non-monotonic full curve or no positive75% lift; do not claim universal calibration.

Monotonicity means no decrease in accepted-subset action_accuracy as target coverage decreases over the original complete grid, with numerical tolerance1e-12. No curve smoothing or evaluation-set threshold selection. Any small tail decrease is flagged descriptively, not asserted statistically significant.

final_d_min is a ranking signal, not a calibrated probability. Positive75% lift does not establish universal monotonicity or zero population risk. Abstention happens after B2 reads, so this is not an evidence-read saving. Raw selection/evaluation records, split-disjointness and frozen-K checks are retained. The two rebuilds matched. Five-domain table complete at existing tier.
