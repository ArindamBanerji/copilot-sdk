# C1 oracle-separation gate and existing-tier reruns

Date: September 14, 2026. Seeds: 42, 123, 7.

**Oracle-separation upgrade pending: harness wiring needed.** Zero of five target domains are wired to GroundTruthOracle in the three requested harnesses. All five were rerun at existing tier; no oracle wiring was built.

GroundTruthOracle exists at examples/jm_reference/oracle.py:30 (label_correct at line100). The domain-agnostic adapter examples/build_your_own/oracle.py:12 is used by email/reading examples; trading_clone re-exports the generic class. These are not exported-five-domain VLD adapters. Substantiation Trader/Chef/DataOps oracles inject treatment effects, not per-case action truth.

K-curve make_case, budget scenario/cases_for, and risk make_case derive labels from the same geometry used by the scorer. They have no existing independent-oracle callback. The budget harness also asserts exhaustive predictions equal its geometry-derived label. Prior labels are synthetic, **not LLM labels**. Creating independent labels and reconciling informative-dimension/evidence semantics would require the prohibited wiring work.

Oracle-separated values, oracle-minus-prior deltas and materiality are null, not zero. **Verdict: label dependence versus independence remains untested.** No claim is upgraded to ORACLE-SEP.

The table below is an existing-tier seed/cohort rerun comparison. A >3pp difference here is NOT evidence of label dependence. Missing B5 historical results are not replaced with exhaustive values.

| Copilot | Experiment | Metric / condition | Prior synthetic % | New existing-tier % | Difference pp | >3pp rerun movement |
|---|---|---|---:|---:|---:|---|
| dataops | K_curve | routing_quality learned N500 | 63.00 | 59.33 | -3.67 | True |
| dataops | K_curve | action_accuracy learned N500 | 90.00 | 78.00 | -12.00 | True |
| dataops | K_curve | routing_quality_delta learned minus frozen N500 | 19.00 | 11.00 | -8.00 | True |
| dataops | budget_frontier | action_accuracy B=1 | 63.90 | 62.83 | -1.07 | False |
| dataops | budget_frontier | action_accuracy B=2 | 84.40 | 81.33 | -3.07 | True |
| dataops | budget_frontier | action_accuracy B=3 | 89.40 | 88.50 | -0.90 | False |
| dataops | budget_frontier | action_accuracy B=5 | not measured | 98.67 | not measured | None |
| dataops | risk_coverage | action_accuracy target=90% | 81.30 | 82.38 | 1.07 | False |
| dataops | risk_coverage | action_accuracy_lift target=90% | 4.54 | 4.58 | 0.03 | False |
| dataops | risk_coverage | action_accuracy target=75% | 87.74 | 88.14 | 0.39 | False |
| dataops | risk_coverage | action_accuracy_lift target=75% | 10.98 | 10.34 | -0.65 | False |
| dataops | risk_coverage | action_accuracy target=50% | 95.26 | 97.66 | 2.41 | False |
| dataops | risk_coverage | action_accuracy_lift target=50% | 18.50 | 19.86 | 1.37 | False |
| purchasing | K_curve | routing_quality learned N500 | 72.00 | 74.00 | 2.00 | False |
| purchasing | K_curve | action_accuracy learned N500 | 82.00 | 84.00 | 2.00 | False |
| purchasing | K_curve | routing_quality_delta learned minus frozen N500 | 21.00 | 21.67 | 0.67 | False |
| purchasing | budget_frontier | action_accuracy B=1 | 51.30 | 52.50 | 1.20 | False |
| purchasing | budget_frontier | action_accuracy B=2 | 79.80 | 82.50 | 2.70 | False |
| purchasing | budget_frontier | action_accuracy B=3 | 94.00 | 94.83 | 0.83 | False |
| purchasing | budget_frontier | action_accuracy B=5 | not measured | 100.00 | not measured | None |
| purchasing | risk_coverage | action_accuracy target=90% | 79.13 | 80.69 | 1.56 | False |
| purchasing | risk_coverage | action_accuracy_lift target=90% | 4.37 | 3.69 | -0.68 | False |
| purchasing | risk_coverage | action_accuracy target=75% | 88.12 | 89.70 | 1.58 | False |
| purchasing | risk_coverage | action_accuracy_lift target=75% | 13.36 | 12.70 | -0.66 | False |
| purchasing | risk_coverage | action_accuracy target=50% | 100.00 | 100.00 | 0.00 | False |
| purchasing | risk_coverage | action_accuracy_lift target=50% | 25.24 | 23.00 | -2.24 | False |
| soc | K_curve | routing_quality learned N500 | 81.00 | 80.67 | -0.33 | False |
| soc | K_curve | action_accuracy learned N500 | 86.00 | 88.67 | 2.67 | False |
| soc | K_curve | routing_quality_delta learned minus frozen N500 | 12.00 | 18.00 | 6.00 | True |
| soc | budget_frontier | action_accuracy B=1 | 54.30 | 55.00 | 0.70 | False |
| soc | budget_frontier | action_accuracy B=2 | 91.70 | 91.17 | -0.53 | False |
| soc | budget_frontier | action_accuracy B=3 | 100.00 | 100.00 | 0.00 | False |
| soc | budget_frontier | action_accuracy B=5 | not measured | 100.00 | not measured | None |
| soc | risk_coverage | action_accuracy target=90% | 96.98 | 98.54 | 1.55 | False |
| soc | risk_coverage | action_accuracy_lift target=90% | 5.90 | 4.00 | -1.90 | False |
| soc | risk_coverage | action_accuracy target=75% | 100.00 | 100.00 | 0.00 | False |
| soc | risk_coverage | action_accuracy_lift target=75% | 8.92 | 5.47 | -3.45 | True |
| soc | risk_coverage | action_accuracy target=50% | 100.00 | 100.00 | 0.00 | False |
| soc | risk_coverage | action_accuracy_lift target=50% | 8.92 | 5.47 | -3.45 | True |
| trading | K_curve | routing_quality learned N500 | 75.00 | 76.00 | 1.00 | False |
| trading | K_curve | action_accuracy learned N500 | 92.00 | 90.00 | -2.00 | False |
| trading | K_curve | routing_quality_delta learned minus frozen N500 | 12.00 | 12.33 | 0.33 | False |
| trading | budget_frontier | action_accuracy B=1 | 72.00 | 78.50 | 6.50 | True |
| trading | budget_frontier | action_accuracy B=2 | 90.70 | 94.33 | 3.63 | True |
| trading | budget_frontier | action_accuracy B=3 | 94.50 | 97.17 | 2.67 | False |
| trading | budget_frontier | action_accuracy B=5 | not measured | 100.00 | not measured | None |
| trading | risk_coverage | action_accuracy target=90% | not measured | 93.33 | not measured | None |
| trading | risk_coverage | action_accuracy_lift target=90% | not measured | 1.26 | not measured | None |
| trading | risk_coverage | action_accuracy target=75% | not measured | 92.22 | not measured | None |
| trading | risk_coverage | action_accuracy_lift target=75% | not measured | 0.16 | not measured | None |
| trading | risk_coverage | action_accuracy target=50% | not measured | 100.00 | not measured | None |
| trading | risk_coverage | action_accuracy_lift target=50% | not measured | 7.93 | not measured | None |
| s2p | K_curve | routing_quality learned N500 | 65.00 | 70.33 | 5.33 | True |
| s2p | K_curve | action_accuracy learned N500 | 84.00 | 88.67 | 4.67 | True |
| s2p | K_curve | routing_quality_delta learned minus frozen N500 | 3.00 | 8.67 | 5.67 | True |
| s2p | budget_frontier | action_accuracy B=1 | 65.20 | 65.17 | -0.03 | False |
| s2p | budget_frontier | action_accuracy B=2 | 84.10 | 85.00 | 0.90 | False |
| s2p | budget_frontier | action_accuracy B=3 | 99.30 | 98.33 | -0.97 | False |
| s2p | budget_frontier | action_accuracy B=5 | not measured | 100.00 | not measured | None |
| s2p | risk_coverage | action_accuracy target=90% | not measured | 83.38 | not measured | None |
| s2p | risk_coverage | action_accuracy_lift target=90% | not measured | 1.05 | not measured | None |
| s2p | risk_coverage | action_accuracy target=75% | not measured | 82.59 | not measured | None |
| s2p | risk_coverage | action_accuracy_lift target=75% | not measured | 0.25 | not measured | None |
| s2p | risk_coverage | action_accuracy target=50% | not measured | 100.00 | not measured | None |
| s2p | risk_coverage | action_accuracy_lift target=50% | not measured | 17.67 | not measured | None |

Every row: REAL_COMPONENT geometry + SIMULATED decisions/evidence/verification.

K-curve keeps 500 decisions, 10 changing 50-case evaluation cohorts, paired learned/frozen K; budget reuses production investigation segments and fixed read quotas at B1/2/3/5, 500 training/200 frozen-K evaluation; risk reuses the unchanged 500/500/500 held-out function. K-curve/risk evidence remains informative-label-filtered; budget reveals every selected coordinate. These evidence semantics are intentionally preserved, not pooled.

Both routing_quality and action_accuracy are retained; category_accuracy is not measured because category is supplied. Risk baseline is B2 acting on all cases, not budget0. Target coverage is set on selection data; actual held-out coverage is measured. Three-seed SD is descriptive.

Two independent full rebuilds per domain/seed matched byte-for-byte. Source/geometry hashes and raw checkpoint/decision data are in the JSON. No production source changed.
