# Group A/D: Routing, K Learning, Transfer and Robustness

**Date:** September 13, 2026. **Evidence:** exported production centroids with synthetic, oracle-labeled scenarios. No live endpoint, application database, external provider, or customer outcome experiment.

All six experiments completed. Static+K leads DataOps routing; RNN+K leads task accuracy by point estimate. No transfer pair shares an exact factor name. Distribution and conservation verdicts below follow their pre-registered criteria.

## 1. RI-1 — Routing × K Interaction

**Protocol correction:** RV-0's published headline already used K learning. Its learned/fixed evaluations consumed different cases. This experiment explicitly trains all eight cells and evaluates paired cohorts.

500 decisions per cell/seed, 10 checkpoints, 50 fresh held-out cases/checkpoint, B=2, 10 seeds. K starts at 0.5, updates +0.02/-0.005, and is clipped to [0.1,3.0]. No doubled reward for action flips; that differs from KUtilityStore's optional flip behavior. Fixed K stays at 0.5. GRU/LSTM use the unchanged hand-set RV-0 gates, not trained neural networks.

| Variant | Fixed K routing | Learned K routing | K lift (paired 95% CI) | Fixed / learned accuracy | Fixed / learned selection starvation |
|---|---:|---:|---:|---:|---:|
| STATIC | 51.9% ± 5.2% | 60.8% ± 5.6% | +8.9 pp [+7.4, +10.4] | 61.8% / 75.2% | 2.8% / 5.0% |
| RNN | 46.5% ± 3.6% | 56.6% ± 4.3% | +10.1 pp [+8.5, +11.7] | 63.2% / 78.2% | 5.6% / 7.8% |
| GRU | 46.2% ± 3.3% | 50.6% ± 3.8% | +4.4 pp [+2.6, +6.2] | 65.2% / 71.4% | 8.3% / 8.6% |
| LSTM | 46.0% ± 3.4% | 48.6% ± 3.2% | +2.6 pp [+1.2, +4.0] | 65.2% / 69.2% | 6.4% / 6.7% |

**Ranking flip: False.** Fixed: static > rnn > gru > lstm. Learned: static > rnn > gru > lstm.

Static−RNN with K: routing +4.2 pp [+1.1, +7.3]; accuracy -3.0 pp [-6.3, +0.3]. Routing difference-in-differences: -1.2 pp [-3.2, +0.8].

**Paper verdict:** recommend Static+K as the routing-efficiency baseline on this DataOps benchmark. Retain RNN+K as the accuracy comparator; do not call Static universally better. Static computes Q once and uses two policy scorer calls; recurrent variants compute Q twice and use three. These are actual calls in the new harness; RV-0's 3/4 accounting included extra nominal calls.

Fixed K has 100% update starvation by design; the table reports selection starvation. Final hurts are measured. Sample SD is across seeds, and paired t-intervals are unadjusted exploratory comparisons.

![RI-1 heatmap](charts/pub_ri1_interaction_heatmap.png)

## 2. RI-2 — UCB Sweep

Five seeds per copilot/coefficient with matched greedy controls. UCB is the RV-1 bonus Q + c·σ/√(attempts+1), not conventional log-time UCB. Evaluation retains exploration using frozen training counts. Best c is the lowest tested c with mean starvation ≤10% and mean routing loss ≤2 pp.

| Copilot | c | Routing | Starvation | Routing vs greedy (95% CI) | Pass |
|---|---:|---:|---:|---:|---|
| dataops | 0.1 | 58.0% | 2.2% | +0.0 pp [-0.9, +0.9] | YES |
| dataops | 0.25 | 57.6% | 0.0% | -0.4 pp [-1.1, +0.3] | YES |
| dataops | 0.5 | 57.0% | 0.0% | -1.0 pp [-1.9, -0.1] | YES |
| dataops | 0.75 | 57.0% | 0.0% | -1.0 pp [-1.9, -0.1] | YES |
| dataops | 1 | 56.8% | 0.0% | -1.2 pp [-2.2, -0.2] | YES |
| trading | 0.1 | 75.2% | 12.4% | +1.0 pp [-1.3, +3.3] | NO |
| trading | 0.25 | 71.2% | 0.0% | -3.0 pp [-5.0, -1.0] | NO |
| trading | 0.5 | 67.6% | 0.0% | -6.6 pp [-10.0, -3.2] | NO |
| trading | 0.75 | 66.4% | 0.0% | -7.8 pp [-11.6, -4.0] | NO |
| trading | 1 | 65.4% | 0.0% | -8.8 pp [-11.6, -6.0] | NO |
| purchasing | 0.1 | 67.2% | 13.1% | +0.0 pp [-1.5, +1.5] | NO |
| purchasing | 0.25 | 67.6% | 2.9% | +0.4 pp [-2.5, +3.3] | YES |
| purchasing | 0.5 | 67.0% | 0.0% | -0.2 pp [-2.9, +2.5] | YES |
| purchasing | 0.75 | 65.8% | 0.0% | -1.4 pp [-2.8, +0.0] | YES |
| purchasing | 1 | 65.2% | 0.0% | -2.0 pp [-4.3, +0.3] | YES |
| soc | 0.1 | 83.4% | 3.3% | +1.6 pp [-1.0, +4.2] | YES |
| soc | 0.25 | 84.2% | 0.0% | +2.4 pp [+1.3, +3.5] | YES |
| soc | 0.5 | 84.4% | 0.0% | +2.6 pp [+0.7, +4.5] | YES |
| soc | 0.75 | 83.6% | 0.0% | +1.8 pp [-1.2, +4.8] | YES |
| soc | 1 | 82.8% | 0.0% | +1.0 pp [+0.1, +1.9] | YES |
| s2p | 0.1 | 66.0% | 13.5% | +1.8 pp [-3.0, +6.6] | NO |
| s2p | 0.25 | 67.4% | 5.0% | +3.2 pp [+0.1, +6.3] | YES |
| s2p | 0.5 | 66.2% | 0.0% | +2.0 pp [-1.6, +5.6] | YES |
| s2p | 0.75 | 64.0% | 0.0% | -0.2 pp [-3.4, +3.0] | YES |
| s2p | 1 | 64.0% | 0.0% | -0.2 pp [-4.8, +4.4] | YES |

| Copilot | Lowest qualifying c | Non-dominated c values |
|---|---:|---|
| dataops | 0.1 | 0.1, 0.25 |
| trading | None | 0.1, 0.25 |
| purchasing | 0.25 | 0.25, 0.5 |
| soc | 0.1 | 0.5 |
| s2p | 0.25 | 0.25, 0.5 |

These are point-estimate selections from a five-seed sweep, not a held-out hyperparameter certification. Trading has no c meeting both constraints. Paired intervals and accuracy deltas remain available in JSON.

![UCB trade-off](charts/pub_ri2_ucb_pareto.png)

## 3. RI-3 — Hybrid Strategies

Independent ε draws at each read; random choice among valid unattempted factors. Greedy-then-explore uses greedy Q first and UCB c=1 second. Five seeds, 500 decisions, ten 50-case evaluations, with the same paired greedy cohorts as RI-2.

| Copilot | Strategy | Routing | Accuracy | Starvation | Routing vs greedy | ≤10% / ≤2 pp |
|---|---|---:|---:|---:|---:|---|
| dataops | greedy | 58.0% | 79.6% | 7.8% | +0.0 pp | YES |
| dataops | epsilon_0.05 | 57.4% | 80.0% | 0.6% | -0.6 pp | YES |
| dataops | epsilon_0.1 | 57.0% | 78.4% | 0.0% | -1.0 pp | YES |
| dataops | epsilon_0.2 | 54.4% | 73.6% | 0.0% | -3.6 pp | NO |
| dataops | epsilon_0.3 | 53.4% | 69.6% | 0.0% | -4.6 pp | NO |
| dataops | greedy_then_explore | 56.8% | 78.0% | 0.0% | -1.2 pp | YES |
| trading | greedy | 74.2% | 89.6% | 48.0% | +0.0 pp | NO |
| trading | epsilon_0.05 | 72.8% | 87.2% | 18.0% | -1.4 pp | NO |
| trading | epsilon_0.1 | 71.2% | 85.6% | 5.2% | -3.0 pp | NO |
| trading | epsilon_0.2 | 65.8% | 78.4% | 0.4% | -8.4 pp | NO |
| trading | epsilon_0.3 | 62.0% | 77.2% | 0.0% | -12.2 pp | NO |
| trading | greedy_then_explore | 69.6% | 82.8% | 0.0% | -4.6 pp | NO |
| purchasing | greedy | 67.2% | 72.8% | 30.3% | +0.0 pp | NO |
| purchasing | epsilon_0.05 | 66.2% | 71.6% | 8.0% | -1.0 pp | YES |
| purchasing | epsilon_0.1 | 62.0% | 66.8% | 0.0% | -5.2 pp | NO |
| purchasing | epsilon_0.2 | 59.0% | 62.4% | 0.0% | -8.2 pp | NO |
| purchasing | epsilon_0.3 | 57.4% | 59.6% | 0.0% | -9.8 pp | NO |
| purchasing | greedy_then_explore | 66.0% | 72.8% | 0.0% | -1.2 pp | YES |
| soc | greedy | 81.8% | 93.2% | 31.7% | +0.0 pp | NO |
| soc | epsilon_0.05 | 79.4% | 90.4% | 7.8% | -2.4 pp | NO |
| soc | epsilon_0.1 | 77.2% | 86.8% | 1.7% | -4.6 pp | NO |
| soc | epsilon_0.2 | 71.4% | 78.4% | 0.0% | -10.4 pp | NO |
| soc | epsilon_0.3 | 67.4% | 76.8% | 0.0% | -14.4 pp | NO |
| soc | greedy_then_explore | 82.8% | 93.6% | 0.0% | +1.0 pp | YES |
| s2p | greedy | 64.2% | 81.2% | 21.0% | +0.0 pp | NO |
| s2p | epsilon_0.05 | 63.4% | 80.4% | 7.0% | -0.8 pp | YES |
| s2p | epsilon_0.1 | 61.8% | 79.6% | 1.0% | -2.4 pp | NO |
| s2p | epsilon_0.2 | 58.6% | 77.6% | 0.5% | -5.6 pp | NO |
| s2p | epsilon_0.3 | 56.2% | 76.0% | 0.0% | -8.0 pp | NO |
| s2p | greedy_then_explore | 64.2% | 81.2% | 0.0% | +0.0 pp | YES |

Greedy-first guarantees a greedy first choice, not an optimal B=2 allocation. The hybrid clears starvation but Trading loses routing quality beyond the threshold; ε=0.05 preserves more quality but leaves 18% starvation. No tested Trading policy satisfies both constraints.

![Hybrid comparison](charts/pub_ri3_hybrid_comparison.png)

## 4. RI-4 — Cross-Copilot Transfer

Each donor trains for 500 decisions/seed. Cold and warm target arms then train for 500 decisions each; five seeds/pair. Exact factor names only; if shared factors existed, their donor-category mean K would initialize every target category. Unmatched factors default to 0.5.

The common target is 90% of each cold run's mean routing at N=400/450/500, an observed-tail proxy rather than a proven asymptote. Crossing is measured at N=0 and 50-decision checkpoints; censored/zero-baseline cases are explicit in JSON. Donor training cost is separately reported.

| Pair | Exact overlap | Mean cold / warm target decisions | Warm/cold | Acceleration | ≥30% keep | L4 evidence |
|---|---:|---:|---:|---:|---|---|
| soc_to_s2p | 0 | 30 / 30 | 1.00 | 0.0% | NO | NOT TESTABLE: zero exact overlap; identical initialization |
| s2p_to_soc | 0 | 130 / 130 | 1.00 | 0.0% | NO | NOT TESTABLE: zero exact overlap; identical initialization |
| dataops_to_trading | 0 | 100 / 100 | 1.00 | 0.0% | NO | NOT TESTABLE: zero exact overlap; identical initialization |

No semantic alias, positional mapping, or fabricated shared factor was introduced. Initial K, routes and outcomes match exactly. These null interventions provide no positive or negative efficacy test of non-empty transfer, and no L4/RSI benefit evidence.

![Transfer overlap](charts/pub_ri4_transfer_overlap.png)

## 5. KE-4 — Distribution Sensitivity

Five paired learned/fixed runs per distribution. Uniform uses the current centroid-corruption generator with uniform category/action sampling, not uniform [0,1] vectors. Clustered is 60% first-two-category / 40% all-category mixture (73.3% expected in the first two). Adversarial is an exact midpoint of a closest weighted centroid pair with random endpoint truth; nearest-two distance equality is asserted. Evaluation matches each distribution.

| Distribution | Learned routing | Fixed routing | K lift (95% CI) | Relative lift | Starvation | Final / all-checkpoint hurts |
|---|---:|---:|---:|---:|---:|---:|
| uniform | 58.0% | 47.0% | +11.0 pp [+8.5, +13.5] | 23.4% | 7.8% | 0 / 0 |
| clustered | 54.0% | 42.4% | +11.6 pp [+7.2, +16.0] | 27.4% | 8.9% | 0 / 0 |
| adversarial | 100.0% | 100.0% | +0.0 pp [+0.0, +0.0] | 0.0% | 63.9% | 0 / 0 |

**Pre-registered verdict: FRAGILE.** Adversarial K lift is non-positive. Both arms already reach 100% routing and accuracy; zero lift is a ceiling effect, not absolute failure on ambiguous cases. The +43% magnitude is not reproduced uniformly.

The earlier KE-4 script evaluated all distributions on uniform and used a hardcoded historical baseline. This run uses a matched fixed-K control within each distribution.

![Distribution curves](charts/pub_ke4_distribution_robustness_group_a_d.png)

## 6. KE-5 — Conservation Interaction

Five paired DataOps runs. After each verification, canonical calibration receives α=covered categories/total categories, q=cumulative correct/verified, V=verified decisions, penalty_ratio=10. θ_min=23.53/(α·V), signal=α·q·V. GREEN: signal ≥2θ_min; AMBER: signal ≥θ_min; RED otherwise. Only GREEN allows K updates. Verification advances even when K updates are blocked; no bootstrap bypass.

**Penalty limitation:** the canonical function accepts penalty_ratio but does not use it in threshold/status calculation. This is the canonical gate at the requested DataOps setting, not a validated asymmetric-loss experiment. K learning rates were not silently changed.

| Arm | Final routing | Accuracy | N350 dip | N450 dip | Blocked decisions / factor updates |
|---|---:|---:|---:|---:|---:|
| without_conservation | 58.0% | 79.6% | 1.6% | 1.0% | 0.0 / 0.0 |
| with_conservation | 58.0% | 79.6% | 1.6% | 1.0% | 10.2 / 20.4 |

**HELPS: False; COSTS: False.** Primary N350/N450 dip reductions: 0.0% / 0.0%. Final relative routing loss: 0.0% (+0.0 pp). Cost criterion: ≥5% relative; ≥5 pp interpretation also recorded.

Supplemental fixed 50-case longitudinal cohort: dip reductions 0.0% / 0.2%. This small secondary result does not override the primary verdict. Fresh-cohort fluctuations are not automatically harmful model updates.

Blocks occur early while support accumulates; with growing V and frozen geometry the gate need not track late curve fluctuations. The earlier KE-5 script compared q directly to θ_min and bypassed 50 decisions. Those results are not interchangeable with this canonical gate run.

![Conservation curves](charts/pub_ke5_conservation_curves_group_a_d.png)

## 7. Combined Production Recommendation

These experiments identify benchmark candidates, not a universal production optimum. RI-1 tests architecture only on DataOps; RI-2/RI-3 test exploration on RNN. Static combined with a selected UCB/ε policy has not been factorially tested and is not claimed as measured.

**DataOps paper baseline:** Static+K for routing efficiency, retaining RNN+K for task accuracy. For existing RNN deployments, the table selects highest measured routing quality among tested configurations satisfying ≤10% starvation / ≤2 pp loss; ties favor greedy. These are candidates for shadow evaluation.

| Copilot | Tested RNN candidate | Routing | Starvation | Decision |
|---|---|---:|---:|---|
| dataops | greedy | 58.0% | 7.8% | Candidate; validate accuracy and uncertainty |
| trading | greedy | 74.2% | 48.0% | No candidate meets both constraints; coverage gap remains |
| purchasing | ucb_0.25 | 67.6% | 2.9% | Candidate; validate accuracy and uncertainty |
| soc | ucb_0.5 | 84.4% | 0.0% | Candidate; validate accuracy and uncertainty |
| s2p | ucb_0.25 | 67.4% | 5.0% | Candidate; validate accuracy and uncertainty |

Keep K bounded and frozen within episodes, record uncovered factors, and validate policy changes on held-out operational cases. This work does not establish customer time savings, provider availability, unconstrained transfer or guaranteed future improvement.

## 8. Three-Metric Summary

**M-VALUE:** final informative-read routing/task accuracy. **M-COST:** actual policy scorer/Q calls and B=2 reads, excluding scenario-generation/oracle work. **M-GOV:** K bounds, frozen episode state, immutable evaluation, explicit coverage and blocked-update accounting. Mechanical checks are not deployment-safety proof.

Every row passed the state/bounds/accounting checks. JSONs retain per-seed K tensors, selection/update counts, cohort hashes, sample traces and gate histories. In-process latency is recorded, but concurrent execution prevents fine comparative latency claims.

| Experiment / configuration | M-VALUE: routing / accuracy | M-COST: scorer / Q / reads | M-GOV: starvation / blocked updates | Final hurts |
|---|---:|---:|---:|---:|
| RI-1 / static_fixed | 51.9% / 61.8% | 2 / 1 / 2 | 2.8% / 0.0 | 0 |
| RI-1 / static_learning | 60.8% / 75.2% | 2 / 1 / 2 | 5.0% / 0.0 | 0 |
| RI-1 / rnn_fixed | 46.5% / 63.2% | 3 / 2 / 2 | 5.6% / 0.0 | 0 |
| RI-1 / rnn_learning | 56.6% / 78.2% | 3 / 2 / 2 | 7.8% / 0.0 | 0 |
| RI-1 / gru_fixed | 46.2% / 65.2% | 3 / 2 / 2 | 8.3% / 0.0 | 0 |
| RI-1 / gru_learning | 50.6% / 71.4% | 3 / 2 / 2 | 8.6% / 0.0 | 0 |
| RI-1 / lstm_fixed | 46.0% / 65.2% | 3 / 2 / 2 | 6.4% / 0.0 | 0 |
| RI-1 / lstm_learning | 48.6% / 69.2% | 3 / 2 / 2 | 6.7% / 0.0 | 0 |
| RI2 / dataops / greedy | 58.0% / 79.6% | 3 / 2 / 2 | 7.8% / 0.0 | 0 |
| RI2 / dataops / ucb_0.1 | 58.0% / 79.6% | 3 / 2 / 2 | 2.2% / 0.0 | 0 |
| RI2 / dataops / ucb_0.25 | 57.6% / 79.2% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / dataops / ucb_0.5 | 57.0% / 78.4% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / dataops / ucb_0.75 | 57.0% / 78.0% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / dataops / ucb_1 | 56.8% / 77.6% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / trading / greedy | 74.2% / 89.6% | 3 / 2 / 2 | 48.0% / 0.0 | 0 |
| RI2 / trading / ucb_0.1 | 75.2% / 90.8% | 3 / 2 / 2 | 12.4% / 0.0 | 0 |
| RI2 / trading / ucb_0.25 | 71.2% / 85.6% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / trading / ucb_0.5 | 67.6% / 82.0% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / trading / ucb_0.75 | 66.4% / 80.0% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / trading / ucb_1 | 65.4% / 80.4% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / purchasing / greedy | 67.2% / 72.8% | 3 / 2 / 2 | 30.3% / 0.0 | 0 |
| RI2 / purchasing / ucb_0.1 | 67.2% / 73.6% | 3 / 2 / 2 | 13.1% / 0.0 | 0 |
| RI2 / purchasing / ucb_0.25 | 67.6% / 74.8% | 3 / 2 / 2 | 2.9% / 0.0 | 0 |
| RI2 / purchasing / ucb_0.5 | 67.0% / 73.6% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / purchasing / ucb_0.75 | 65.8% / 72.4% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / purchasing / ucb_1 | 65.2% / 72.4% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / soc / greedy | 81.8% / 93.2% | 3 / 2 / 2 | 31.7% / 0.0 | 0 |
| RI2 / soc / ucb_0.1 | 83.4% / 94.0% | 3 / 2 / 2 | 3.3% / 0.0 | 0 |
| RI2 / soc / ucb_0.25 | 84.2% / 94.8% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / soc / ucb_0.5 | 84.4% / 95.6% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / soc / ucb_0.75 | 83.6% / 95.2% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / soc / ucb_1 | 82.8% / 93.2% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / s2p / greedy | 64.2% / 81.2% | 3 / 2 / 2 | 21.0% / 0.0 | 0 |
| RI2 / s2p / ucb_0.1 | 66.0% / 82.0% | 3 / 2 / 2 | 13.5% / 0.0 | 0 |
| RI2 / s2p / ucb_0.25 | 67.4% / 82.4% | 3 / 2 / 2 | 5.0% / 0.0 | 0 |
| RI2 / s2p / ucb_0.5 | 66.2% / 80.8% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / s2p / ucb_0.75 | 64.0% / 80.8% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI2 / s2p / ucb_1 | 64.0% / 80.4% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI3 / dataops / greedy | 58.0% / 79.6% | 3 / 2 / 2 | 7.8% / 0.0 | 0 |
| RI3 / dataops / epsilon_0.05 | 57.4% / 80.0% | 3 / 2 / 2 | 0.6% / 0.0 | 0 |
| RI3 / dataops / epsilon_0.1 | 57.0% / 78.4% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI3 / dataops / epsilon_0.2 | 54.4% / 73.6% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI3 / dataops / epsilon_0.3 | 53.4% / 69.6% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI3 / dataops / greedy_then_explore | 56.8% / 78.0% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI3 / trading / greedy | 74.2% / 89.6% | 3 / 2 / 2 | 48.0% / 0.0 | 0 |
| RI3 / trading / epsilon_0.05 | 72.8% / 87.2% | 3 / 2 / 2 | 18.0% / 0.0 | 0 |
| RI3 / trading / epsilon_0.1 | 71.2% / 85.6% | 3 / 2 / 2 | 5.2% / 0.0 | 0 |
| RI3 / trading / epsilon_0.2 | 65.8% / 78.4% | 3 / 2 / 2 | 0.4% / 0.0 | 0 |
| RI3 / trading / epsilon_0.3 | 62.0% / 77.2% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI3 / trading / greedy_then_explore | 69.6% / 82.8% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI3 / purchasing / greedy | 67.2% / 72.8% | 3 / 2 / 2 | 30.3% / 0.0 | 0 |
| RI3 / purchasing / epsilon_0.05 | 66.2% / 71.6% | 3 / 2 / 2 | 8.0% / 0.0 | 0 |
| RI3 / purchasing / epsilon_0.1 | 62.0% / 66.8% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI3 / purchasing / epsilon_0.2 | 59.0% / 62.4% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI3 / purchasing / epsilon_0.3 | 57.4% / 59.6% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI3 / purchasing / greedy_then_explore | 66.0% / 72.8% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI3 / soc / greedy | 81.8% / 93.2% | 3 / 2 / 2 | 31.7% / 0.0 | 0 |
| RI3 / soc / epsilon_0.05 | 79.4% / 90.4% | 3 / 2 / 2 | 7.8% / 0.0 | 0 |
| RI3 / soc / epsilon_0.1 | 77.2% / 86.8% | 3 / 2 / 2 | 1.7% / 0.0 | 0 |
| RI3 / soc / epsilon_0.2 | 71.4% / 78.4% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI3 / soc / epsilon_0.3 | 67.4% / 76.8% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI3 / soc / greedy_then_explore | 82.8% / 93.6% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI3 / s2p / greedy | 64.2% / 81.2% | 3 / 2 / 2 | 21.0% / 0.0 | 0 |
| RI3 / s2p / epsilon_0.05 | 63.4% / 80.4% | 3 / 2 / 2 | 7.0% / 0.0 | 0 |
| RI3 / s2p / epsilon_0.1 | 61.8% / 79.6% | 3 / 2 / 2 | 1.0% / 0.0 | 0 |
| RI3 / s2p / epsilon_0.2 | 58.6% / 77.6% | 3 / 2 / 2 | 0.5% / 0.0 | 0 |
| RI3 / s2p / epsilon_0.3 | 56.2% / 76.0% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI3 / s2p / greedy_then_explore | 64.2% / 81.2% | 3 / 2 / 2 | 0.0% / 0.0 | 0 |
| RI-4 / soc_to_s2p / source_training | 81.8% / 93.2% | 3 / 2 / 2 | 31.7% / 0.0 | 0 |
| RI-4 / soc_to_s2p / cold | 64.2% / 81.2% | 3 / 2 / 2 | 21.0% / 0.0 | 0 |
| RI-4 / soc_to_s2p / warm | 64.2% / 81.2% | 3 / 2 / 2 | 21.0% / 0.0 | 0 |
| RI-4 / s2p_to_soc / source_training | 64.2% / 81.2% | 3 / 2 / 2 | 21.0% / 0.0 | 0 |
| RI-4 / s2p_to_soc / cold | 81.8% / 93.2% | 3 / 2 / 2 | 31.7% / 0.0 | 0 |
| RI-4 / s2p_to_soc / warm | 81.8% / 93.2% | 3 / 2 / 2 | 31.7% / 0.0 | 0 |
| RI-4 / dataops_to_trading / source_training | 58.0% / 79.6% | 3 / 2 / 2 | 7.8% / 0.0 | 0 |
| RI-4 / dataops_to_trading / cold | 74.2% / 89.6% | 3 / 2 / 2 | 48.0% / 0.0 | 0 |
| RI-4 / dataops_to_trading / warm | 74.2% / 89.6% | 3 / 2 / 2 | 48.0% / 0.0 | 0 |
| KE-4 / uniform / fixed | 47.0% / 63.6% | 3 / 2 / 2 | 5.6% / 0.0 | 0 |
| KE-4 / uniform / learning | 58.0% / 79.6% | 3 / 2 / 2 | 7.8% / 0.0 | 0 |
| KE-4 / clustered / fixed | 42.4% / 61.2% | 3 / 2 / 2 | 7.2% / 0.0 | 0 |
| KE-4 / clustered / learning | 54.0% / 78.8% | 3 / 2 / 2 | 8.9% / 0.0 | 0 |
| KE-4 / adversarial / fixed | 100.0% / 100.0% | 3 / 2 / 2 | 63.9% / 0.0 | 0 |
| KE-4 / adversarial / learning | 100.0% / 100.0% | 3 / 2 / 2 | 63.9% / 0.0 | 0 |
| KE-5 / without_conservation | 58.0% / 79.6% | 3 / 2 / 2 | 7.8% / 0.0 | 0 |
| KE-5 / with_conservation | 58.0% / 79.6% | 3 / 2 / 2 | 7.8% / 20.4 | 0 |

All-checkpoint evaluation hurts across listed arms: **0**. Some controls recur across experiments and are not independent samples.

**Mechanism-test limits:** oracle labels define useful dimensions; only those reads restore full values, and usefulness labels train K. This favorable evidence model is inherited. A no-op can count as informative when the initial action is already correct. Zero hurts here cannot establish real-world safety or independent predictive validity. Exported centroids and σ are frozen; all exported σ values are 1.0. No centroid training or actual provider traversal occurs.

**Reproduction:** run the six new experiment scripts using the requested virtual environment with -B -X utf8, then scripts/generate_group_a_d_charts.py. JSON outputs and the report refuse overwrite. Chart names use _group_a_d when a requested name already exists.

**Validation:** all six result schemas, 85 aggregate configurations and 465 seed-arm runs passed count, bounds and independent aggregation checks. Paired cohort hashes matched. A complete stochastic Trading seed replay matched all non-timing results. All 12 PNGs and report links passed artifact checks. The 1,208 pre-existing Python source files and protected KE chart artifacts hashed before the run remained byte-identical; the three required source fingerprints below match the supplied prefixes. No git commands were used.

**Post-check source fingerprints:**
- copilot_sdk/scoring/investigation.py: 3441dcbdb67a93e231ceda9827db36b46413e5d2fd29e750e3310caf1a2df6b4
- copilot_sdk/backend/investigation_router.py: 08f4df7ad872a6cf0dc53c0bd7250fe854ca7481e508aa592b35fe06440a744b
- copilot_sdk/scoring/scorer.py: 24ac9e49a070e0f9421fa0e3e7417a828c0ec88610ef906ce4987311c721b460

**Results and checksums:**
- [ri1_routing_k_interaction.json](ri1_routing_k_interaction.json) — SHA-256 0db824e06fe9aa96567941db0ce7c2024087416166d2850837a5d89c5d09ab5d
- [ri2_ucb_sweep.json](ri2_ucb_sweep.json) — SHA-256 51b625045cb5ce657817e1461a92d65c7046f59e78f83948598988c35e0f5e64
- [ri3_hybrid.json](ri3_hybrid.json) — SHA-256 4edb2cda3189a296e9eb8def3a90efd7dec92fb49b67eaddc9a939a8dd20e553
- [ri4_cross_copilot_transfer.json](ri4_cross_copilot_transfer.json) — SHA-256 c902da9d80a0f3ffd7515a7fc8fa5568cce53a7d18ec282037bcf32fb76ff0c5
- [ke4_distribution_sensitivity.json](ke4_distribution_sensitivity.json) — SHA-256 99cbb0c77c4da0a7e218cf749bf349c1840049c581d6d49666b1ff5e7976ab14
- [ke5_conservation_interaction.json](ke5_conservation_interaction.json) — SHA-256 25861bdae77e4ff8da12d14d266912d9ed3b3f8fcb60112b0a6e87abb1c1dd8a

**All chart artifacts:**
- [pub_ri1_interaction_heatmap.png](charts/pub_ri1_interaction_heatmap.png)
- [pub_ri1_ranking_comparison.png](charts/pub_ri1_ranking_comparison.png)
- [pub_ri1_k_lift.png](charts/pub_ri1_k_lift.png)
- [pub_ri2_ucb_pareto.png](charts/pub_ri2_ucb_pareto.png)
- [pub_ri2_ucb_sweep_by_copilot.png](charts/pub_ri2_ucb_sweep_by_copilot.png)
- [pub_ri3_hybrid_comparison.png](charts/pub_ri3_hybrid_comparison.png)
- [pub_ri4_transfer_speedup.png](charts/pub_ri4_transfer_speedup.png)
- [pub_ri4_transfer_overlap.png](charts/pub_ri4_transfer_overlap.png)
- [pub_ke4_distribution_robustness_group_a_d.png](charts/pub_ke4_distribution_robustness_group_a_d.png) (prior requested-name artifact preserved)
- [pub_ke4_final_comparison_group_a_d.png](charts/pub_ke4_final_comparison_group_a_d.png) (prior requested-name artifact preserved)
- [pub_ke5_conservation_curves_group_a_d.png](charts/pub_ke5_conservation_curves_group_a_d.png) (prior requested-name artifact preserved)
- [pub_ke5_blocked_updates_group_a_d.png](charts/pub_ke5_blocked_updates_group_a_d.png) (prior requested-name artifact preserved)
