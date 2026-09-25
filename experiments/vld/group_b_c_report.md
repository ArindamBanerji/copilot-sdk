# Group B/C recurrence and routing report

Protocol date: September 13, 2026. Nine experiments, ten new scripts, twelve figures. Artifact-only synthetic probes on exported real centroid geometry; no production adoption.

## Protocol and interpretation

Each arm trains for 500 verified synthetic decisions, with 10 checkpoints and 50 held-out cases per checkpoint. Five paired seeds per arm, except RV-8 with ten. Training cases use a separate RNG from policy exploration, and evaluation never updates K, counts, sequence state, or Q coefficients. Raw seed runs, evaluation rows, training rows, state snapshots, configuration, and hashes are retained in the nine JSON files. Every control/candidate pair has an identical training-stream hash.

Routing quality is informative reads / actual reads; accuracy is final action agreement with the full-vector centroid scorer. Starvation is the fraction of category-dimension cells never read during training. The RI-7 policy uses a separate baseline-weight metric (K≈0.5), which can also count weights that returned to baseline. Tables use the final held-out checkpoint. Intervals are paired-seed bootstrap percentile intervals, descriptive with five or ten seeds and no multiple-comparison correction. Keep/kill gates use the requested point-estimate thresholds, not significance tests.

The prior RV-1 synthetic generator defines a read as informative if its counterfactual action is correct OR it materially raises correct-action probability; already-correct surfaces can therefore label unchanged dimensions informative. Reads outside that set return unchanged evidence. K updates follow the prior bandit harness (+0.02 for correct informative reads, −0.005 otherwise, clipped to [0.1,3]); the production flip bonus and early-halting rules are not exercised. These probes measure this harness, not live routing value or production-scorer parity.

The requested routing memo and MAP v17 were not found in the workspace. The detailed user protocol is the experiment authority here. Section 10 distinguishes measured mechanisms from an unverified R0–R5 numbering; it does not invent official taxonomy coverage.

Source integrity: all 1,800 source files present in the initial audit retain their exact hashes (dependencies, caches, and build outputs excluded). investigation.py already began **3441dcbd**, while the prompt expected **3441dcdb** (transposed final characters). The router and scorer match expected prefixes 08f4df7a and 24ac9e49. This pre-existing discrepancy was not repaired. Concurrently created scripts outside this task are excluded from the before/after modification check.

RI-7 was rerun after aligning its UCB bonus with RV-1: c × sigma_centroid / sqrt(N+1). The other eight JSON files preserve the originally executed shared-harness hash plus an audit showing that the sole subsequent edit changed an unused UCB branch. Their execution paths are unchanged.

## 1. RI-5 — Rich K State

**DO NOT KEEP.** Trading starvation reduction >=20pp and routing loss <=3pp on every copilot.

Rich Thompson reduces Trading starvation by **48.0pp**. Trading routing changes by **-5.8pp**. This decides whether the exploration is precise enough under the preregistered gate; lower starvation alone does not establish benefit.

| Copilot | Variant | Routing ± seed SD | Δ routing (pp), paired 95% CI | Accuracy | Starvation | Reads |
|---|---|---:|---:|---:|---:|---:|
| DataOps | GREEDY-SCALAR-K | 58.0% ± 3.1 | +0.0 [+0.0, +0.0] | 79.6% | 7.8% | 2.00 |
| DataOps | THOMPSON-SCALAR-K | 55.8% ± 6.1 | -2.2 [-5.0, +0.8] | 74.4% | 0.0% | 2.00 |
| DataOps | THOMPSON-RICH-K | 57.6% ± 4.2 | -0.4 [-1.2, +0.4] | 79.6% | 0.0% | 2.00 |
| Trading | GREEDY-SCALAR-K | 74.2% ± 4.2 | +0.0 [+0.0, +0.0] | 89.6% | 48.0% | 2.00 |
| Trading | THOMPSON-SCALAR-K | 52.4% ± 3.3 | -21.8 [-25.2, -18.4] | 62.4% | 0.0% | 2.00 |
| Trading | THOMPSON-RICH-K | 68.4% ± 4.0 | -5.8 [-7.6, -4.0] | 83.6% | 0.0% | 2.00 |
| Purchasing | GREEDY-SCALAR-K | 67.2% ± 5.3 | +0.0 [+0.0, +0.0] | 72.8% | 30.3% | 2.00 |
| Purchasing | THOMPSON-SCALAR-K | 51.6% ± 3.9 | -15.6 [-19.0, -12.2] | 60.0% | 0.0% | 2.00 |
| Purchasing | THOMPSON-RICH-K | 65.4% ± 5.0 | -1.8 [-3.6, +0.0] | 71.2% | 0.0% | 2.00 |
| SOC | GREEDY-SCALAR-K | 81.8% ± 3.2 | +0.0 [+0.0, +0.0] | 93.2% | 31.7% | 2.00 |
| SOC | THOMPSON-SCALAR-K | 63.2% ± 5.3 | -18.6 [-21.6, -15.8] | 70.8% | 0.0% | 2.00 |
| SOC | THOMPSON-RICH-K | 82.0% ± 3.5 | +0.2 [-1.0, +1.0] | 93.6% | 0.0% | 2.00 |
| S2P | GREEDY-SCALAR-K | 64.2% ± 8.8 | +0.0 [+0.0, +0.0] | 81.2% | 21.0% | 2.00 |
| S2P | THOMPSON-SCALAR-K | 55.2% ± 5.9 | -9.0 [-13.6, -4.0] | 75.2% | 0.0% | 2.00 |
| S2P | THOMPSON-RICH-K | 66.6% ± 7.8 | +2.4 [-0.4, +5.2] | 84.0% | 0.0% | 2.00 |

**Implementation choices and limits:**

- sigma_K is the SD of K update increments; raw sample variance is also retained. Prior variance .25 with one pseudo-observation prevents zero initial uncertainty. Normal scale = sigma_K/sqrt(N+1).
- N counts selected reads that return a result, including unchanged evidence; every synthetic provider read returns a result.

[Raw results](ri5_rich_k_state.json). [Figure 1](charts/pub_ri5_starvation_comparison.png) · [Figure 2](charts/pub_ri5_routing_vs_starvation.png)

## 2. RI-6 — Temporal Decay

**DO NOT KEEP.** >=20% faster recovery without pre-shift routing loss; zero-time control has no measurable speedup.

Recovery is the first held-out checkpoint at or above 90% of mean pre-shift quality at decisions 200 and 250, including an immediate post-shift probe. Resolution is 50 decisions. Unrecovered seeds are right-censored at 250; restricted means are reported alongside censor counts. A zero-time control cannot support a percentage speedup. Training-window 201–250 metrics are also available in JSON.

| Copilot | Variant | Pre-shift routing | Recovery decisions, restricted mean | Censored seeds | Immediate recovery seeds |
|---|---|---:|---:|---:|---:|
| DataOps | lambda=0 | 53.5% | 80.0 | 0 | 1 |
| DataOps | lambda=0.5 | 51.2% | 60.0 | 0 | 1 |
| DataOps | lambda=1 | 56.2% | 190.0 | 0 | 0 |
| DataOps | lambda=2 | 49.9% | 150.0 | 0 | 0 |

Per-comparison gates: `{"lambda=0": {"keep": false, "pre_shift_delta": 0.0, "recovery_speedup": 0.0}, "lambda=0.5": {"keep": false, "pre_shift_delta": -0.0229999999999998, "recovery_speedup": 0.25}, "lambda=1": {"keep": false, "pre_shift_delta": 0.027000000000000024, "recovery_speedup": -1.375}, "lambda=2": {"keep": false, "pre_shift_delta": -0.03599999999999992, "recovery_speedup": -0.875}}`.

| Copilot | Variant | Routing ± seed SD | Δ routing (pp), paired 95% CI | Accuracy | Starvation | Reads |
|---|---|---:|---:|---:|---:|---:|
| DataOps | lambda=0 | 63.0% ± 1.4 | +0.0 [+0.0, +0.0] | 96.0% | 5.0% | 2.00 |
| DataOps | lambda=0.5 | 60.6% ± 4.1 | -2.4 [-5.0, +0.2] | 96.0% | 16.7% | 2.00 |
| DataOps | lambda=1 | 54.6% ± 5.1 | -8.4 [-11.4, -5.0] | 94.0% | 23.9% | 2.00 |
| DataOps | lambda=2 | 53.0% ± 6.9 | -10.0 [-15.8, -4.2] | 91.6% | 38.9% | 2.00 |

**Implementation choices and limits:**

- Decisions 1-250 corrupt/offer evidence only on dims 0,2; decisions 251-500 on dims 1,3. Other coordinates are fully observed. Centroids stay fixed.
- Age is min-max normalized elapsed time since selection within the active category: most recent=0, oldest=1; ties all yield zero. Decay changes effective routing K only, not stored K.
- Recovery uses held-out checkpoints 200 and 250 for pre-shift quality; training-window 201-250 metrics are separately retained. No-recovery is censored, never silently treated as success.

[Raw results](ri6_temporal_decay.json). [Figure 1](charts/pub_ri6_regime_recovery.png) · [Figure 2](charts/pub_ri6_k_weight_evolution.png)

## 3. RI-7 — Category-Conditional Routing

**DO NOT KEEP.** starvation <=15% on all; routing loss <=2pp on best greedy copilot; improvement on worst.

Greedy's best routing copilot is SOC; its worst is DataOps. Adaptive mode must retain quality on the former and improve the latter while meeting the starvation cap everywhere.

| Copilot | Variant | Routing ± seed SD | Δ routing (pp), paired 95% CI | Accuracy | Starvation | Reads |
|---|---|---:|---:|---:|---:|---:|
| DataOps | UNIFORM-GREEDY | 58.0% ± 3.1 | +0.0 [+0.0, +0.0] | 79.6% | 7.8% | 2.00 |
| DataOps | UNIFORM-UCB-0.5 | 57.0% ± 3.0 | -1.0 [-1.6, -0.4] | 78.4% | 0.0% | 2.00 |
| DataOps | CATEGORY-ADAPTIVE | 57.8% ± 3.3 | -0.2 [-0.6, +0.0] | 79.6% | 0.0% | 2.00 |
| Trading | UNIFORM-GREEDY | 74.2% ± 4.2 | +0.0 [+0.0, +0.0] | 89.6% | 48.0% | 2.00 |
| Trading | UNIFORM-UCB-0.5 | 67.6% ± 4.5 | -6.6 [-8.8, -4.8] | 82.0% | 0.0% | 2.00 |
| Trading | CATEGORY-ADAPTIVE | 74.8% ± 5.3 | +0.6 [-0.6, +1.8] | 89.2% | 0.0% | 2.00 |
| Purchasing | UNIFORM-GREEDY | 67.2% ± 5.3 | +0.0 [+0.0, +0.0] | 72.8% | 30.3% | 2.00 |
| Purchasing | UNIFORM-UCB-0.5 | 67.0% ± 6.2 | -0.2 [-2.0, +1.4] | 73.6% | 0.0% | 2.00 |
| Purchasing | CATEGORY-ADAPTIVE | 66.6% ± 5.9 | -0.6 [-2.2, +0.8] | 72.8% | 1.1% | 2.00 |
| SOC | UNIFORM-GREEDY | 81.8% ± 3.2 | +0.0 [+0.0, +0.0] | 93.2% | 31.7% | 2.00 |
| SOC | UNIFORM-UCB-0.5 | 84.4% ± 2.7 | +2.6 [+1.6, +3.8] | 95.6% | 0.0% | 2.00 |
| SOC | CATEGORY-ADAPTIVE | 82.4% ± 4.2 | +0.6 [-0.2, +1.4] | 93.6% | 0.0% | 2.00 |
| S2P | UNIFORM-GREEDY | 64.2% ± 8.8 | +0.0 [+0.0, +0.0] | 81.2% | 21.0% | 2.00 |
| S2P | UNIFORM-UCB-0.5 | 66.2% ± 8.2 | +2.0 [-0.4, +4.2] | 80.8% | 0.0% | 2.00 |
| S2P | CATEGORY-ADAPTIVE | 65.8% ± 7.5 | +1.6 [+0.2, +3.4] | 82.8% | 0.5% | 2.00 |

**Implementation choices and limits:**

- UCB = Q + c*sigma_centroid/sqrt(N_d+1), matching the existing RV-1 bonus; c is .5 above 30% baseline-weight cells, .25 from 10% through 30%, and zero below 10%.
- Mode starts at c=.5 (all K=.5), then updates every 50 decisions. Reported starvation uses never-read counts; baseline-weight starvation driving the policy is retained separately.

[Raw results](ri7_category_conditional.json). [Figure 1](charts/pub_ri7_adaptive_vs_uniform.png)

## 4. RI-8 — Sequence-Aware Q

**DO NOT KEEP.** same beta improves routing >=2pp at B=2 on both tested copilots.

Per-copilot β candidates meeting +2pp: `{"dataops": ["beta=0.5"], "soc": []}`. The global keep gate requires one β to meet the threshold on both copilots.

| Copilot | Variant | Routing ± seed SD | Δ routing (pp), paired 95% CI | Accuracy | Starvation | Reads |
|---|---|---:|---:|---:|---:|---:|
| DataOps | beta=0 | 58.0% ± 3.1 | +0.0 [+0.0, +0.0] | 79.6% | 7.8% | 2.00 |
| DataOps | beta=0.1 | 58.8% ± 4.5 | +0.8 [-0.4, +2.4] | 80.0% | 11.1% | 2.00 |
| DataOps | beta=0.5 | 60.2% ± 9.0 | +2.2 [-2.4, +6.8] | 79.6% | 14.4% | 2.00 |
| DataOps | beta=1 | 58.0% ± 7.8 | +0.0 [-3.8, +3.8] | 78.8% | 18.9% | 2.00 |
| SOC | beta=0 | 81.8% ± 3.2 | +0.0 [+0.0, +0.0] | 93.2% | 31.7% | 2.00 |
| SOC | beta=0.1 | 79.8% ± 5.7 | -2.0 [-6.2, +1.2] | 92.0% | 37.8% | 2.00 |
| SOC | beta=0.5 | 67.4% ± 4.5 | -14.4 [-17.2, -11.8] | 79.6% | 41.1% | 2.00 |
| SOC | beta=1 | 67.0% ± 3.9 | -14.8 [-16.8, -12.8] | 79.2% | 41.1% | 2.00 |

**Implementation choices and limits:**

- One ordered C matrix per category; increment selected adjacent pair after a correct verified decision. No diagonal reads. Evaluation never updates C.
- C is correct-outcome frequency, not a success rate conditional on pair attempts; selection-frequency confounding is part of this probe.

[Raw results](ri8_sequence_aware.json). [Figure 1](charts/pub_ri8_sequence_effect.png)

## 5. RI-9 — Regime-Indexed K

**DO NOT KEEP.** post-shift recovery >=30% faster on both copilots; zero-time control cannot establish recovery gain.

Recovery is the first held-out checkpoint at or above 90% of mean pre-shift quality at decisions 200 and 250, including an immediate post-shift probe. Resolution is 50 decisions. Unrecovered seeds are right-censored at 250; restricted means are reported alongside censor counts. A zero-time control cannot support a percentage speedup. Training-window 201–250 metrics are also available in JSON.

| Copilot | Variant | Pre-shift routing | Recovery decisions, restricted mean | Censored seeds | Immediate recovery seeds |
|---|---|---:|---:|---:|---:|
| Trading | SINGLE-K | 65.4% | 10.0 | 0 | 4 |
| Trading | REGIME-K | 65.8% | 0.0 | 0 | 5 |
| SOC | SINGLE-K | 77.1% | 0.0 | 0 | 5 |
| SOC | REGIME-K | 76.7% | 40.0 | 0 | 2 |

Per-comparison gates: `{"soc": {"keep": false, "speedup": null}, "trading": {"keep": true, "speedup": 1.0}}`.

| Copilot | Variant | Routing ± seed SD | Δ routing (pp), paired 95% CI | Accuracy | Starvation | Reads |
|---|---|---:|---:|---:|---:|---:|
| Trading | SINGLE-K | 65.2% ± 3.1 | +0.0 [+0.0, +0.0] | 79.2% | 52.4% | 2.00 |
| Trading | REGIME-K | 74.2% ± 2.6 | +9.0 [+7.6, +10.4] | 91.2% | 46.4% | 2.00 |
| SOC | SINGLE-K | 68.8% ± 3.3 | +0.0 [+0.0, +0.0] | 79.6% | 36.1% | 2.00 |
| SOC | REGIME-K | 79.2% ± 2.2 | +10.4 [+7.6, +13.2] | 97.2% | 31.7% | 2.00 |

**Implementation choices and limits:**

- Before shift, first floor(C/2) categories receive 80% probability, remaining categories 20%; after decision 250 those masses reverse. Uniform within each group. Evaluation follows the active distribution.
- Production KUtilityStore is already category-indexed. SINGLE-K is a deliberately pooled ablation; REGIME-K matches production storage semantics.
- No change to per-category evidence geometry; a category-frequency shift need not cause a quality drop. Recovery that is immediate is explicitly reported.

[Raw results](ri9_regime_indexed.json). [Figure 1](charts/pub_ri9_regime_recovery.png)

## 6. RV-4 — Risk-Sensitive Q

**DO NOT KEEP.** SOC and DataOps each >=5% relative routing gain; Purchasing and Trading no degradation.

Positive Q scaling at fixed B=2 is **exactly invariant** for every seed: both training route digests and all evaluation rows match. Adaptive budgets are SOC 5, DataOps 4, S2P 3, Purchasing 2, Trading 2. The 5% gain gate is relative routing improvement, evaluated separately for SOC and DataOps; low-penalty checks use Purchasing and Trading.

Adaptive relative gains: DataOps -26.7%, Trading +0.0%, Purchasing +0.0%, SOC -44.2%, S2P -6.5%.

| Copilot | Variant | Routing ± seed SD | Δ routing (pp), paired 95% CI | Accuracy | Starvation | Reads |
|---|---|---:|---:|---:|---:|---:|
| DataOps | UNIFORM-B2 | 58.0% ± 3.1 | +0.0 [+0.0, +0.0] | 79.6% | 7.8% | 2.00 |
| DataOps | RISK-B2 | 58.0% ± 3.1 | +0.0 [+0.0, +0.0] | 79.6% | 7.8% | 2.00 |
| DataOps | ADAPTIVE-B | 42.5% ± 2.7 | -15.5 [-16.0, -14.7] | 88.8% | 0.0% | 4.00 |
| DataOps | THOMPSON | 55.8% ± 6.1 | -2.2 [-5.0, +0.8] | 74.4% | 0.0% | 2.00 |
| DataOps | THOMPSON-RISK | 37.6% ± 5.3 | -20.4 [-22.2, -18.4] | 45.6% | 0.0% | 2.00 |
| Trading | UNIFORM-B2 | 74.2% ± 4.2 | +0.0 [+0.0, +0.0] | 89.6% | 48.0% | 2.00 |
| Trading | RISK-B2 | 74.2% ± 4.2 | +0.0 [+0.0, +0.0] | 89.6% | 48.0% | 2.00 |
| Trading | ADAPTIVE-B | 74.2% ± 4.2 | +0.0 [+0.0, +0.0] | 89.6% | 48.0% | 2.00 |
| Trading | THOMPSON | 52.4% ± 3.3 | -21.8 [-25.2, -18.4] | 62.4% | 0.0% | 2.00 |
| Trading | THOMPSON-RISK | 45.8% ± 4.6 | -28.4 [-30.0, -26.6] | 54.0% | 0.0% | 2.00 |
| Purchasing | UNIFORM-B2 | 67.2% ± 5.3 | +0.0 [+0.0, +0.0] | 72.8% | 30.3% | 2.00 |
| Purchasing | RISK-B2 | 67.2% ± 5.3 | +0.0 [+0.0, +0.0] | 72.8% | 30.3% | 2.00 |
| Purchasing | ADAPTIVE-B | 67.2% ± 5.3 | +0.0 [+0.0, +0.0] | 72.8% | 30.3% | 2.00 |
| Purchasing | THOMPSON | 51.6% ± 3.9 | -15.6 [-19.0, -12.2] | 60.0% | 0.0% | 2.00 |
| Purchasing | THOMPSON-RISK | 39.2% ± 2.8 | -28.0 [-32.2, -22.8] | 44.4% | 0.0% | 2.00 |
| SOC | UNIFORM-B2 | 81.8% ± 3.2 | +0.0 [+0.0, +0.0] | 93.2% | 31.7% | 2.00 |
| SOC | RISK-B2 | 81.8% ± 3.2 | +0.0 [+0.0, +0.0] | 93.2% | 31.7% | 2.00 |
| SOC | ADAPTIVE-B | 45.7% ± 2.7 | -36.1 [-38.2, -33.9] | 100.0% | 0.0% | 5.00 |
| SOC | THOMPSON | 63.2% ± 5.3 | -18.6 [-21.6, -15.8] | 70.8% | 0.0% | 2.00 |
| SOC | THOMPSON-RISK | 38.6% ± 1.1 | -43.2 [-45.4, -41.2] | 38.4% | 0.0% | 2.00 |
| S2P | UNIFORM-B2 | 64.2% ± 8.8 | +0.0 [+0.0, +0.0] | 81.2% | 21.0% | 2.00 |
| S2P | RISK-B2 | 64.2% ± 8.8 | +0.0 [+0.0, +0.0] | 81.2% | 21.0% | 2.00 |
| S2P | ADAPTIVE-B | 60.0% ± 3.6 | -4.2 [-9.5, +1.3] | 97.2% | 18.0% | 3.00 |
| S2P | THOMPSON | 55.2% ± 5.9 | -9.0 [-13.6, -4.0] | 75.2% | 0.0% | 2.00 |
| S2P | THOMPSON-RISK | 35.0% ± 2.7 | -29.2 [-34.8, -23.6] | 40.0% | 0.0% | 2.00 |

**Implementation choices and limits:**

- Includes an unweighted Thompson comparator to isolate posterior-sigma risk effects.
- Risk posterior condition multiplies sigma by penalty ratio while keeping mean Q unchanged. Scaling BOTH mean and sigma would be exactly sample-order invariant; fixed mean isolates uncertainty weighting.
- 5% improvement interpreted as relative routing quality; absolute percentage-point changes also retained. More reads can improve accuracy while lowering informative-read precision.

[Raw results](rv4_risk_sensitive.json). [Figure 1](charts/pub_rv4_adaptive_budget.png) · [Figure 2](charts/pub_rv4_penalty_vs_gain.png)

## 7. RV-5 — Hierarchical C4→RNN

**DO NOT KEEP.** >= flat held-out accuracy at strictly fewer average reads on each copilot.

This measures the **existing C4 fallback**. No trained classifier artifact is available; the fallback emits S1/S3/S6 only. The requested six-class budget table is implemented, but S2/S4/S5 coverage is zero. Per-copilot efficiency gates: `{"dataops": {"accuracy_delta_pp": -4.400000000000004, "reads_saved": 0.21599999999999997, "keep": false}, "trading": {"accuracy_delta_pp": -3.6000000000000143, "reads_saved": 0.04800000000000004, "keep": false}, "purchasing": {"accuracy_delta_pp": 0.0, "reads_saved": 0.05600000000000027, "keep": true}, "soc": {"accuracy_delta_pp": -15.600000000000003, "reads_saved": 0.18399999999999994, "keep": false}, "s2p": {"accuracy_delta_pp": 0.0, "reads_saved": 0.0, "keep": false}}`.

| Copilot | Variant | Routing ± seed SD | Δ routing (pp), paired 95% CI | Accuracy | Starvation | Reads |
|---|---|---:|---:|---:|---:|---:|
| DataOps | FLAT-RNN | 58.0% ± 3.1 | +0.0 [+0.0, +0.0] | 79.6% | 7.8% | 2.00 |
| DataOps | HIERARCHICAL | 59.6% ± 1.9 | +1.6 [-0.2, +3.3] | 75.2% | 8.3% | 1.78 |
| Trading | FLAT-RNN | 74.2% ± 4.2 | +0.0 [+0.0, +0.0] | 89.6% | 48.0% | 2.00 |
| Trading | HIERARCHICAL | 72.8% ± 4.3 | -1.4 [-2.8, -0.5] | 86.0% | 48.0% | 1.95 |
| Purchasing | FLAT-RNN | 67.2% ± 5.3 | +0.0 [+0.0, +0.0] | 72.8% | 30.3% | 2.00 |
| Purchasing | HIERARCHICAL | 68.4% ± 6.3 | +1.2 [+0.4, +2.1] | 72.8% | 30.3% | 1.94 |
| SOC | FLAT-RNN | 81.8% ± 3.2 | +0.0 [+0.0, +0.0] | 93.2% | 31.7% | 2.00 |
| SOC | HIERARCHICAL | 76.4% ± 5.5 | -5.4 [-9.2, -2.1] | 77.6% | 28.3% | 1.82 |
| S2P | FLAT-RNN | 64.2% ± 8.8 | +0.0 [+0.0, +0.0] | 81.2% | 21.0% | 2.00 |
| S2P | HIERARCHICAL | 64.2% ± 8.8 | +0.0 [+0.0, +0.0] | 81.2% | 21.0% | 2.00 |

**Implementation choices and limits:**

- Uses existing SituationClassifier with no model_path: d_min<.05 => S1, d_min>.5 => S6, otherwise S3. No fitted classifier artifact was found.
- Applies prompt budgets S1:0,S2:1,S3:2,S4:3,S5:2,S6:1, overriding the production budget mapping only in experiment memory.
- Fallback cannot emit S2/S4/S5, so this is a fallback hierarchy measurement, not a validation of a trained six-class classifier. Situation counts retained for every checkpoint.

[Raw results](rv5_hierarchical.json). [Figure 1](charts/pub_rv5_hierarchical.png)

## 8. RV-8 — Adaptive-Q Headroom

**REPORT ONLY.** report learned-minus-closed-form headroom; flag >5pp; no automatic adoption.

Measured linear-learner headroom is **+1.4pp**; >5pp flag: **False**. This is a specified online-regression probe, not a proven upper bound on all learned routers. The three coefficients are inspectable, but fitting them erodes the no-trained-router separator. No adoption is made.

| Copilot | Variant | Routing ± seed SD | Δ routing (pp), paired 95% CI | Accuracy | Starvation | Reads |
|---|---|---:|---:|---:|---:|---:|
| DataOps | CLOSED-FORM | 56.6% ± 4.3 | +0.0 [+0.0, +0.0] | 78.2% | 7.8% | 2.00 |
| DataOps | LEARNED-Q | 58.0% ± 5.4 | +1.4 [-0.0, +2.8] | 79.0% | 6.1% | 2.00 |

**Implementation choices and limits:**

- Online squared-error regression with three global coefficients, initialized (1,1,1), learning rate .05 and bounds [.01,10]. One post-verification gradient step per decision.
- Target is one-hot best dimension by counterfactual increase in verified-action probability; ties choose lowest dimension. Full counterfactual labels are privileged training data; no evaluation labels enter updates.
- Q retains category K multiplication. The probe estimates achievable headroom for this specified linear learner, not a mathematical upper bound over every trained router.

[Raw results](rv8_adaptive_q.json). [Figure 1](charts/pub_rv8_headroom.png)

## 9. RV-9 — MCTS Lookahead Value

**REPORT ONLY.** report routing value and scorer cost of 1/2-step lookahead at B=2.

The requested lookahead is implemented as exact finite centroid expectimax, not Monte Carlo tree search. Simulations see only current evidence, centroids, and the action posterior. Margin improvement can reinforce an incorrect high-confidence action. Gains (pp): `{"GREEDY-Q": 0.0, "1-STEP": -31.400000000000006, "2-STEP": -32.00000000000001}`; scorer-cost multipliers: `{"GREEDY-Q": 1.0, "1-STEP": 15.25, "2-STEP": 210.25}`.

| Copilot | Variant | Routing ± seed SD | Δ routing (pp), paired 95% CI | Accuracy | Starvation | Reads |
|---|---|---:|---:|---:|---:|---:|
| DataOps | GREEDY-Q | 58.0% ± 3.1 | +0.0 [+0.0, +0.0] | 79.6% | 7.8% | 2.00 |
| DataOps | 1-STEP | 26.6% ± 4.4 | -31.4 [-34.2, -28.4] | 29.2% | 0.0% | 2.00 |
| DataOps | 2-STEP | 26.0% ± 5.1 | -32.0 [-35.4, -29.0] | 28.4% | 0.0% | 2.00 |

**Implementation choices and limits:**

- Exact finite centroid-branch expectimax, not stochastic MCTS/UCT. Current action posterior supplies branch probabilities; hypothetical evidence uses centroid values, never hidden full vector or labels.
- Each candidate maximizes expected post-read probability-margin improvement, recursively through remaining B. Every hypothetical score counts in M-COST.
- K learning runs in every arm. Pure margin-lookahead arms do not use K to select; they test the requested margin objective, and their maintained K is diagnostic only.
- This is model-based lookahead headroom, not an oracle guarantee; saturated action posteriors may reinforce wrong actions.

[Raw results](rv9_mcts.json). [Figure 1](charts/pub_rv9_lookahead.png)

## 10. Recurrence Taxonomy — Complete Picture

The mechanism inventory below covers the completed probes and prior RV-0/RV-1 artifacts. The R0–R5 assignments are **provisional descriptive groupings**, not verified MAP v17 definitions. Official numbering still requires the missing authority documents; a complete six-class trained C4 test is also unavailable.

| Provisional level | Mechanism | Evidence and key finding |
|---|---|---|
| R0 | Static read plan | Prior RV-0 STATIC routing 57.8%; frozen initial plan. |
| R1 | Within-episode recurrent Q | Prior RV-0 RNN 56.3%, GRU 48.8%, LSTM 47.0%; LSTM did not clear its +2pp-over-GRU gate. |
| R2 | Cross-decision scalar utility | Prior K-learning cross-copilot summary shows positive learning-minus-control routing on all five copilots, with Trading starvation 48%; prior RV-1 exploration removes starvation at a routing tradeoff. |
| R3 | Rich utility and temporal persistence | RI-5 keep=False; RI-6 decay keep=False; uncertainty and age change exploration/persistence. |
| R4 | Conditional and ordered recurrence | RI-7 adaptive keep=False; RI-8 sequence keep=False; RI-9 regime keep=False; category indexing already exists in production. |
| R5 | Policy hierarchy, learned Q, lookahead | RV-5 fallback keep=False; RV-8 headroom +1.4pp; RV-9 evaluated explicitly with simulation cost. |

Risk-sensitive RV-4 is orthogonal to recurrence depth: scalar multiplication cannot change an argmax, while budget and posterior-scale changes can. Prior results use their original seeds/protocol; they are not merged statistically with the new paired runs.

The concurrently completed [Group A/D report](group_a_d_report.md) supplies RI-1 through RI-4 and their full M-VALUE/M-COST/M-GOV tables:

- RI-1: STATIC+K routing 60.8%, RNN+K 56.6%; RNN accuracy 78.2% versus STATIC 75.2%. K helps all four architectures; their routing rank does not flip.
- RI-2: the UCB sweep finds qualifying coefficients on DataOps, Purchasing, SOC, and S2P; Trading has no coefficient satisfying both its starvation and routing constraints.
- RI-3: hybrid first-greedy/second-UCB removes Trading starvation but loses 4.6pp routing; no tested Trading epsilon/hybrid policy satisfies both constraints.
- RI-4: all three transfer pairs have zero exact factor-name overlap. Cold and warm initializations are identical; transfer efficacy is not testable on these pairs.

These companion results complete the requested RI-1–RI-9 experiment inventory. They do not turn zero-overlap transfer or missing classifier classes into positive coverage evidence. Group A/D reuses scorer outputs and counts 2/3 calls for static/recurrent policies; this group retains actual 4-call baseline execution to match the older RV-0 loop. Compare cost conventions before combining tables.

## 11. Three-Metric Summary

**M-VALUE** reports final routing and final-action accuracy. **M-COST** reports actual reads, scorer calls per evaluation decision (including every hypothetical rollout), accuracy/scorer call, and additional training-only counterfactual scorer calls. Wall times are retained for diagnostics but are not latency benchmarks because experiments may run concurrently. **M-GOV** is a design assessment of state traceability and training dependence, not a compliance score or measured governance outcome.

Codes: **I** = named factor/category state and closed-form rule; **S** = I plus stochastic exploration (seed and state required for replay); **C4** = inspectable existing fallback, trained model absent; **L** = three learned coefficients plus privileged counterfactual training labels, separator eroded; **P** = inspectable centroid simulation, model assumptions and expanded scorer cost. All remain offline experiments.

| Experiment | Copilot | Variant | M-VALUE: routing / accuracy | M-COST: reads / scores / accuracy per score | Training extra scores | M-GOV |
|---|---|---|---:|---:|---:|---|
| RI5 | DataOps | GREEDY-SCALAR-K | 58.0% / 79.6% | 2.00 / 4.0 / 0.1990 | 0.0 | I |
| RI5 | DataOps | THOMPSON-SCALAR-K | 55.8% / 74.4% | 2.00 / 4.0 / 0.1860 | 0.0 | S |
| RI5 | DataOps | THOMPSON-RICH-K | 57.6% / 79.6% | 2.00 / 4.0 / 0.1990 | 0.0 | S |
| RI5 | Trading | GREEDY-SCALAR-K | 74.2% / 89.6% | 2.00 / 4.0 / 0.2240 | 0.0 | I |
| RI5 | Trading | THOMPSON-SCALAR-K | 52.4% / 62.4% | 2.00 / 4.0 / 0.1560 | 0.0 | S |
| RI5 | Trading | THOMPSON-RICH-K | 68.4% / 83.6% | 2.00 / 4.0 / 0.2090 | 0.0 | S |
| RI5 | Purchasing | GREEDY-SCALAR-K | 67.2% / 72.8% | 2.00 / 4.0 / 0.1820 | 0.0 | I |
| RI5 | Purchasing | THOMPSON-SCALAR-K | 51.6% / 60.0% | 2.00 / 4.0 / 0.1500 | 0.0 | S |
| RI5 | Purchasing | THOMPSON-RICH-K | 65.4% / 71.2% | 2.00 / 4.0 / 0.1780 | 0.0 | S |
| RI5 | SOC | GREEDY-SCALAR-K | 81.8% / 93.2% | 2.00 / 4.0 / 0.2330 | 0.0 | I |
| RI5 | SOC | THOMPSON-SCALAR-K | 63.2% / 70.8% | 2.00 / 4.0 / 0.1770 | 0.0 | S |
| RI5 | SOC | THOMPSON-RICH-K | 82.0% / 93.6% | 2.00 / 4.0 / 0.2340 | 0.0 | S |
| RI5 | S2P | GREEDY-SCALAR-K | 64.2% / 81.2% | 2.00 / 4.0 / 0.2030 | 0.0 | I |
| RI5 | S2P | THOMPSON-SCALAR-K | 55.2% / 75.2% | 2.00 / 4.0 / 0.1880 | 0.0 | S |
| RI5 | S2P | THOMPSON-RICH-K | 66.6% / 84.0% | 2.00 / 4.0 / 0.2100 | 0.0 | S |
| RI6 | DataOps | lambda=0 | 63.0% / 96.0% | 2.00 / 4.0 / 0.2400 | 0.0 | I |
| RI6 | DataOps | lambda=0.5 | 60.6% / 96.0% | 2.00 / 4.0 / 0.2400 | 0.0 | I |
| RI6 | DataOps | lambda=1 | 54.6% / 94.0% | 2.00 / 4.0 / 0.2350 | 0.0 | I |
| RI6 | DataOps | lambda=2 | 53.0% / 91.6% | 2.00 / 4.0 / 0.2290 | 0.0 | I |
| RI7 | DataOps | UNIFORM-GREEDY | 58.0% / 79.6% | 2.00 / 4.0 / 0.1990 | 0.0 | I |
| RI7 | DataOps | UNIFORM-UCB-0.5 | 57.0% / 78.4% | 2.00 / 4.0 / 0.1960 | 0.0 | I |
| RI7 | DataOps | CATEGORY-ADAPTIVE | 57.8% / 79.6% | 2.00 / 4.0 / 0.1990 | 0.0 | I |
| RI7 | Trading | UNIFORM-GREEDY | 74.2% / 89.6% | 2.00 / 4.0 / 0.2240 | 0.0 | I |
| RI7 | Trading | UNIFORM-UCB-0.5 | 67.6% / 82.0% | 2.00 / 4.0 / 0.2050 | 0.0 | I |
| RI7 | Trading | CATEGORY-ADAPTIVE | 74.8% / 89.2% | 2.00 / 4.0 / 0.2230 | 0.0 | I |
| RI7 | Purchasing | UNIFORM-GREEDY | 67.2% / 72.8% | 2.00 / 4.0 / 0.1820 | 0.0 | I |
| RI7 | Purchasing | UNIFORM-UCB-0.5 | 67.0% / 73.6% | 2.00 / 4.0 / 0.1840 | 0.0 | I |
| RI7 | Purchasing | CATEGORY-ADAPTIVE | 66.6% / 72.8% | 2.00 / 4.0 / 0.1820 | 0.0 | I |
| RI7 | SOC | UNIFORM-GREEDY | 81.8% / 93.2% | 2.00 / 4.0 / 0.2330 | 0.0 | I |
| RI7 | SOC | UNIFORM-UCB-0.5 | 84.4% / 95.6% | 2.00 / 4.0 / 0.2390 | 0.0 | I |
| RI7 | SOC | CATEGORY-ADAPTIVE | 82.4% / 93.6% | 2.00 / 4.0 / 0.2340 | 0.0 | I |
| RI7 | S2P | UNIFORM-GREEDY | 64.2% / 81.2% | 2.00 / 4.0 / 0.2030 | 0.0 | I |
| RI7 | S2P | UNIFORM-UCB-0.5 | 66.2% / 80.8% | 2.00 / 4.0 / 0.2020 | 0.0 | I |
| RI7 | S2P | CATEGORY-ADAPTIVE | 65.8% / 82.8% | 2.00 / 4.0 / 0.2070 | 0.0 | I |
| RI8 | DataOps | beta=0 | 58.0% / 79.6% | 2.00 / 4.0 / 0.1990 | 0.0 | I |
| RI8 | DataOps | beta=0.1 | 58.8% / 80.0% | 2.00 / 4.0 / 0.2000 | 0.0 | I |
| RI8 | DataOps | beta=0.5 | 60.2% / 79.6% | 2.00 / 4.0 / 0.1990 | 0.0 | I |
| RI8 | DataOps | beta=1 | 58.0% / 78.8% | 2.00 / 4.0 / 0.1970 | 0.0 | I |
| RI8 | SOC | beta=0 | 81.8% / 93.2% | 2.00 / 4.0 / 0.2330 | 0.0 | I |
| RI8 | SOC | beta=0.1 | 79.8% / 92.0% | 2.00 / 4.0 / 0.2300 | 0.0 | I |
| RI8 | SOC | beta=0.5 | 67.4% / 79.6% | 2.00 / 4.0 / 0.1990 | 0.0 | I |
| RI8 | SOC | beta=1 | 67.0% / 79.2% | 2.00 / 4.0 / 0.1980 | 0.0 | I |
| RI9 | Trading | SINGLE-K | 65.2% / 79.2% | 2.00 / 4.0 / 0.1980 | 0.0 | I |
| RI9 | Trading | REGIME-K | 74.2% / 91.2% | 2.00 / 4.0 / 0.2280 | 0.0 | I |
| RI9 | SOC | SINGLE-K | 68.8% / 79.6% | 2.00 / 4.0 / 0.1990 | 0.0 | I |
| RI9 | SOC | REGIME-K | 79.2% / 97.2% | 2.00 / 4.0 / 0.2430 | 0.0 | I |
| RV4 | DataOps | UNIFORM-B2 | 58.0% / 79.6% | 2.00 / 4.0 / 0.1990 | 0.0 | I |
| RV4 | DataOps | RISK-B2 | 58.0% / 79.6% | 2.00 / 4.0 / 0.1990 | 0.0 | I |
| RV4 | DataOps | ADAPTIVE-B | 42.5% / 88.8% | 4.00 / 6.0 / 0.1480 | 0.0 | I |
| RV4 | DataOps | THOMPSON | 55.8% / 74.4% | 2.00 / 4.0 / 0.1860 | 0.0 | S |
| RV4 | DataOps | THOMPSON-RISK | 37.6% / 45.6% | 2.00 / 4.0 / 0.1140 | 0.0 | S |
| RV4 | Trading | UNIFORM-B2 | 74.2% / 89.6% | 2.00 / 4.0 / 0.2240 | 0.0 | I |
| RV4 | Trading | RISK-B2 | 74.2% / 89.6% | 2.00 / 4.0 / 0.2240 | 0.0 | I |
| RV4 | Trading | ADAPTIVE-B | 74.2% / 89.6% | 2.00 / 4.0 / 0.2240 | 0.0 | I |
| RV4 | Trading | THOMPSON | 52.4% / 62.4% | 2.00 / 4.0 / 0.1560 | 0.0 | S |
| RV4 | Trading | THOMPSON-RISK | 45.8% / 54.0% | 2.00 / 4.0 / 0.1350 | 0.0 | S |
| RV4 | Purchasing | UNIFORM-B2 | 67.2% / 72.8% | 2.00 / 4.0 / 0.1820 | 0.0 | I |
| RV4 | Purchasing | RISK-B2 | 67.2% / 72.8% | 2.00 / 4.0 / 0.1820 | 0.0 | I |
| RV4 | Purchasing | ADAPTIVE-B | 67.2% / 72.8% | 2.00 / 4.0 / 0.1820 | 0.0 | I |
| RV4 | Purchasing | THOMPSON | 51.6% / 60.0% | 2.00 / 4.0 / 0.1500 | 0.0 | S |
| RV4 | Purchasing | THOMPSON-RISK | 39.2% / 44.4% | 2.00 / 4.0 / 0.1110 | 0.0 | S |
| RV4 | SOC | UNIFORM-B2 | 81.8% / 93.2% | 2.00 / 4.0 / 0.2330 | 0.0 | I |
| RV4 | SOC | RISK-B2 | 81.8% / 93.2% | 2.00 / 4.0 / 0.2330 | 0.0 | I |
| RV4 | SOC | ADAPTIVE-B | 45.7% / 100.0% | 5.00 / 7.0 / 0.1429 | 0.0 | I |
| RV4 | SOC | THOMPSON | 63.2% / 70.8% | 2.00 / 4.0 / 0.1770 | 0.0 | S |
| RV4 | SOC | THOMPSON-RISK | 38.6% / 38.4% | 2.00 / 4.0 / 0.0960 | 0.0 | S |
| RV4 | S2P | UNIFORM-B2 | 64.2% / 81.2% | 2.00 / 4.0 / 0.2030 | 0.0 | I |
| RV4 | S2P | RISK-B2 | 64.2% / 81.2% | 2.00 / 4.0 / 0.2030 | 0.0 | I |
| RV4 | S2P | ADAPTIVE-B | 60.0% / 97.2% | 3.00 / 5.0 / 0.1944 | 0.0 | I |
| RV4 | S2P | THOMPSON | 55.2% / 75.2% | 2.00 / 4.0 / 0.1880 | 0.0 | S |
| RV4 | S2P | THOMPSON-RISK | 35.0% / 40.0% | 2.00 / 4.0 / 0.1000 | 0.0 | S |
| RV5 | DataOps | FLAT-RNN | 58.0% / 79.6% | 2.00 / 4.0 / 0.1990 | 0.0 | C4 |
| RV5 | DataOps | HIERARCHICAL | 59.6% / 75.2% | 1.78 / 3.8 / 0.1986 | 0.0 | C4 |
| RV5 | Trading | FLAT-RNN | 74.2% / 89.6% | 2.00 / 4.0 / 0.2240 | 0.0 | C4 |
| RV5 | Trading | HIERARCHICAL | 72.8% / 86.0% | 1.95 / 4.0 / 0.2176 | 0.0 | C4 |
| RV5 | Purchasing | FLAT-RNN | 67.2% / 72.8% | 2.00 / 4.0 / 0.1820 | 0.0 | C4 |
| RV5 | Purchasing | HIERARCHICAL | 68.4% / 72.8% | 1.94 / 3.9 / 0.1847 | 0.0 | C4 |
| RV5 | SOC | FLAT-RNN | 81.8% / 93.2% | 2.00 / 4.0 / 0.2330 | 0.0 | C4 |
| RV5 | SOC | HIERARCHICAL | 76.4% / 77.6% | 1.82 / 3.8 / 0.2034 | 0.0 | C4 |
| RV5 | S2P | FLAT-RNN | 64.2% / 81.2% | 2.00 / 4.0 / 0.2030 | 0.0 | C4 |
| RV5 | S2P | HIERARCHICAL | 64.2% / 81.2% | 2.00 / 4.0 / 0.2030 | 0.0 | C4 |
| RV8 | DataOps | CLOSED-FORM | 56.6% / 78.2% | 2.00 / 4.0 / 0.1955 | 0.0 | I |
| RV8 | DataOps | LEARNED-Q | 58.0% / 79.0% | 2.00 / 4.0 / 0.1975 | 7.0 | L |
| RV9 | DataOps | GREEDY-Q | 58.0% / 79.6% | 2.00 / 4.0 / 0.1990 | 0.0 | I |
| RV9 | DataOps | 1-STEP | 26.6% / 29.2% | 2.00 / 61.0 / 0.0048 | 0.0 | P |
| RV9 | DataOps | 2-STEP | 26.0% / 28.4% | 2.00 / 841.0 / 0.0003 | 0.0 | P |

Prior taxonomy comparators (original artifacts, not rerun):

| Prior experiment | Copilot | Variant | M-VALUE: routing / accuracy | M-COST | M-GOV |
|---|---|---|---:|---|---|
| RV-0 | DataOps | static | 57.8% / 73.6% | 3.0 scorer calls; B=2 | Dimension-aligned state (prior assessment) |
| RV-0 | DataOps | rnn | 56.3% / 77.6% | 4.0 scorer calls; B=2 | Dimension-aligned state (prior assessment) |
| RV-0 | DataOps | gru | 48.8% / 69.2% | 4.0 scorer calls; B=2 | Dimension-aligned state (prior assessment) |
| RV-0 | DataOps | lstm | 47.0% / 66.4% | 4.0 scorer calls; B=2 | Dimension-aligned state (prior assessment) |
| RV-1 | DataOps | greedy | 56.3% / 77.8% | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |
| RV-1 | DataOps | thompson | 54.4% / 76.8% | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |
| RV-1 | DataOps | ucb | 54.1% / 74.8% | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |
| RV-1 | Trading | greedy | 73.6% / 91.4% | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |
| RV-1 | Trading | thompson | 53.0% / 67.8% | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |
| RV-1 | Trading | ucb | 65.0% / 82.0% | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |
| RV-1 | Purchasing | greedy | 66.4% / 75.2% | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |
| RV-1 | Purchasing | thompson | 51.7% / 58.0% | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |
| RV-1 | Purchasing | ucb | 64.4% / 73.8% | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |
| RV-1 | SOC | greedy | 81.0% / 92.4% | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |
| RV-1 | SOC | thompson | 60.1% / 69.4% | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |
| RV-1 | SOC | ucb | 81.1% / 91.6% | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |
| RV-1 | S2P | greedy | 66.3% / 79.8% | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |
| RV-1 | S2P | thompson | 51.2% / 73.4% | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |
| RV-1 | S2P | ucb | 66.6% / 80.6% | B=2; same scorer loop (prior report) | Named factor state; exploration replay required |

## Reproduction and checks

Run each scripts/ri5…ri9 and scripts/rv4,rv5,rv8,rv9 entrypoint with the supplied project Python interpreter and `-B`, then `python -B scripts/generate_group_b_c_charts.py`. Each experiment imports shared machinery from the newly created ri5_rich_k_state.py and reads the existing routing_variant_bandit.py without modification. The chart/report script reads completed JSON only.

Automated checks assert formula parity in preflight, paired training streams, frozen evaluation state, and exact fixed-Q-scale routing invariance. JSON preserves full pre/post production hashes, centroid hash, entrypoint hash, and shared-harness hash. Results are serialized with nonfinite values forbidden. Recovery censoring and missing-authority/model limitations are explicit.
