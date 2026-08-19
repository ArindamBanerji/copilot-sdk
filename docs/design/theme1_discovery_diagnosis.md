# Theme 1 discovery diagnosis

This report uses the `cross-graph-experiments` working tree as the authority. It distinguishes implementation facts, measured values, and claims that could not be confirmed.

## Q1 Discovery primitive — VERDICT: dot-product only

**[CODE]** `CrossGraphAttention.compute_logits` implements `E_i @ E_j.T / sqrt(d)` at `src/models/cross_attention.py:54-78`; with the unit-norm contract documented at `src/models/cross_attention.py:10-11`, this is scaled cosine similarity.

**[CODE]** `CrossGraphAttention.discover_two_stage` calls `compute_logits` and then row-wise `compute_attention` at `src/models/cross_attention.py:125-177`. Its two stages are a threshold on those logits and a top-K filter on the resulting softmax weights, not a second geometry.

**[CODE]** `CrossGraphAttention.discover_logit_only` calls `compute_logits` at `src/models/cross_attention.py:177-210`; `CrossGraphAttention.discover_topk_only` also calls `compute_logits` before ranking the softmax weights at `src/models/cross_attention.py:210-249`.

**[CODE]** `CrossGraphAttention.cosine_baseline` computes `E_i @ E_j.T` directly at `src/models/cross_attention.py:251-289`. Its own implementation note states that unit-normalized rows make this cosine similarity and that the only difference from attention logits is the `sqrt(d)` scaling.

**[CODE]** Experiment call sites are exhaustive in the discovered runners: `experiments/exp2_cross_graph_discovery/run.py:117-136` invokes `discover_two_stage`, `discover_logit_only`, `discover_topk_only`, and `cosine_baseline`; `experiments/exp2_cross_graph_discovery/run_normalization_ablation.py:248` and `:440` invoke `discover_two_stage`; `experiments/exp3_multidomain_scaling/run.py:79`, `experiments/exp3_multidomain_scaling/run_extended.py:206`, and `experiments/exp4_sensitivity/run.py:45` invoke `discover_two_stage`.

**[CODE]** No distance-based cross-graph discovery method was found: `src/models/cross_attention.py:33-289` contains no L2/Mahalanobis discovery primitive, and the experiment call sites above contain no distance-based alternative. **NOT FOUND.**

**[CODE]** The within-graph comparison point is separate: `ProfileScorer.score` computes squared L2 distances at `src/models/profile_scorer.py:132-206`. That L2 scorer is not called by the cross-graph discovery runners listed above.

## Q2 EXP-2 145x — VERDICT: vs random only

**[MEASURED]** The committed EXP-2 normalization result records the headline as `ratio_above_random: 145.2` for the `zscore_l2` pipeline, with numerator `mean_f1 = 0.0709` and denominator `mean_random_f1 = 0.000488`, in `experiments/exp2_cross_graph_discovery/normalization_summary.json`. The unrounded quotient of those stored values is approximately 145.29; the committed report value is 145.2x.

**[CODE]** The ratio is calculated as `mean_f1 / mean_rand_f1` in `experiments/exp2_cross_graph_discovery/run_normalization_ablation.py` in the summary-building block after the ablation loop; the baseline is explicitly the analytical random F1, not cosine.

**[CODE]** The ordinary EXP-2 runner does evaluate `cosine_baseline` alongside the two-stage, logit-only, top-K-only, and random rows at `experiments/exp2_cross_graph_discovery/run.py:117-146`, and the committed `discovery_results.csv` contains cosine rows. However, the 145.2x figure is not a two-stage-versus-cosine statistic.

**[MEASURED]** For orientation only, selecting each method's best recorded configuration from `experiments/exp2_cross_graph_discovery/results/discovery_results.csv` gives two-stage minus cosine F1 deltas of `+0.28` percentage points for `secxthr`, `+0.925` percentage points for `decxthr`, and `+1.911` percentage points for `secxdec`. These are best-configuration deltas, not a controlled primitive-only comparison, because the selected thresholds/K values differ.

**[CODE]** Since both attention logits and cosine baseline are built from the same dot-product matrix in `src/models/cross_attention.py:54-78` and `:251-289`, any observed two-stage advantage over cosine would be attributable to threshold/top-K filtering and the cross-graph evaluation structure, not to replacing dot-product geometry with a different primitive. The 145.2x headline itself establishes only improvement over the random F1 baseline.

## Q3 Embeddings — VERDICT: planted-synthetic

**[CODE]** `EntityGenerator._raw_matrix` samples semantic features and background/shared noise from NumPy random distributions at `src/data/entity_generator.py:127-177`; `EntityGenerator.generate_domain` then applies per-dimension z-scoring and per-row L2 normalization at `src/data/entity_generator.py:180-214`. There is no learned embedding model or fitting step in this path.

**[CODE]** `inject_signals` selects source/target entities and overwrites target shared dimensions `6:14` with a scaled source copy, then re-normalizes the target at `src/data/entity_generator.py:256-299`. This is the planted cross-graph match mechanism.

**[CODE]** In EXP-2, `run_experiment` generates the domains, calls `inject_signals`, converts the returned entity-ID pairs into an index ground-truth set, and scores discovered index pairs with TP/FP/FN, precision, recall, and F1 in `experiments/exp2_cross_graph_discovery/run.py:96-113` and `:39-59`.

**[CODE]** The cross-attention self-test independently demonstrates the same construction by setting `E_j[3]` near `E_i[0]` before running discovery at `src/models/cross_attention.py:315-355`.

**[CODE]** Therefore the EXP-2 discovery task is recovery of generator-planted near-duplicate pairs, not discovery against independently collected or learned cross-graph relations. The generator defines both the signal and the success labels through `EntityGenerator.generate_domain` and `inject_signals`.

## Q4 Scaling pair-count control — VERDICT: collapses to O(n^2)

**[CODE]** The scaling runner's x-axis is `n_domains`: `run.py` reads `domain_counts` and computes `n_pairs = n_dom * (n_dom - 1) // 2` at `experiments/exp3_multidomain_scaling/run.py:37-55`; `run_extended.py` repeats this at `experiments/exp3_multidomain_scaling/run_extended.py:164-194`.

**[CODE]** The fitted y-axis is raw `total_discoveries`, not yield-per-pair: `run.py` aggregates `total_disc` and fits `discoveries = a*n^b` at `experiments/exp3_multidomain_scaling/run.py:82-107`; `run_extended.py` does the same at `experiments/exp3_multidomain_scaling/run_extended.py:257-278`. The chart labels this quantity “Total Cross-Domain Discoveries” in `src/viz/exp3_charts.py:29-48`.

**[MEASURED]** The committed original-range fit is `b = 2.3043`, `R^2 = 0.999498`, with `n = [2,3,4,5,6]`, from `experiments/exp3_multidomain_scaling/results/extended_scaling_fit.json` under `original_range`.

**[MEASURED]** The committed extended-range fit is `b = 2.1127`, 95% CI `[2.0894, 2.1361]`, and `R^2 = 0.999883`, for `n = [2,3,4,5,6,7,8,9,10,12,15]`, from `experiments/exp3_multidomain_scaling/results/extended_scaling_fit.json` under `extended_range`.

**[MEASURED]** I recomputed `total_discoveries / n_pairs` from `experiments/exp3_multidomain_scaling/results/scaling_data.csv`. The per-pair curve is:

| n domains | pairs | mean total discoveries | mean discoveries per pair |
|---:|---:|---:|---:|
| 2 | 1 | 600 | 600 |
| 3 | 3 | 1,800 | 600 |
| 4 | 6 | 3,600 | 600 |
| 5 | 10 | 6,000 | 600 |
| 6 | 15 | 9,000 | 600 |

**[MEASURED]** I also recomputed the same control from `experiments/exp3_multidomain_scaling/results/extended_scaling_data.csv`. For `n = [2,3,4,5,6,7,8,9,10,12,15]`, the per-pair curve is `[600,600,600,600,600,600,600,600,600,600,600]`.

**[MEASURED]** A power-law refit of those derived per-pair values gives an exponent numerically indistinguishable from zero: `b = 4.87e-09` on `scaling_data.csv` and `b = 1.66e-09` on `extended_scaling_data.csv`. The ordinary R² statistic is undefined for this exactly constant series because its total variance is zero; the constant per-pair yield is the stronger result.

**[CODE]** The constant 600 is structurally explained by the runner: each pair has 200 source entities and `top_k = 3`, so `discover_two_stage` contributes at most and, in these stored runs, exactly `200*3 = 600` discoveries per pair; the relevant fixed values are at `experiments/exp3_multidomain_scaling/run.py:41-48` and `:66-79`, with the method's top-K behavior at `src/models/cross_attention.py:157-177`.

**[MEASURED]** The apparent super-linear law therefore does not survive pair-count control. Within these outputs, total yield is exactly `600 * n(n-1)/2`; the measured exponent near 2 is explained by the number of graph pairs, not by increasing discovery yield per pair.

## Q5 Distance variant — VERDICT: well-defined & small, but not an independent geometry under current normalization

**[CODE]** A distance analog is well-defined for the existing matrix interfaces: replace the similarity matrix with negative squared distances, for example `S[k,l] = -||E_i[k] - E_j[l]||_2^2`, or with negative Mahalanobis distances `S[k,l] = -(E_i[k]-E_j[l])^T M (E_i[k]-E_j[l])`. The current discovery methods only require a 2-D logit matrix from `compute_logits`, as shown by `src/models/cross_attention.py:54-78` and `:125-249`.

**[CODE]** With the generator's unit-norm rows, squared L2 is algebraically `||u-v||² = 2 - 2(u·v)`. Thus negative L2 is a monotone transform of cosine/dot-product similarity, not a genuinely independent cross-graph geometry for the current `generate_domain` output contract at `src/data/entity_generator.py:180-214`.

**[CODE]** An identity-L2 variant would likely be a small change confined to `src/models/cross_attention.py`: add a distance-logit branch or parameter to `compute_logits`, retaining the existing output shape and discovery method interfaces. The current eval harness can consume the returned tuples and calculate the existing TP/FP/FN metrics unchanged, as shown by `experiments/exp2_cross_graph_discovery/run.py:39-59`.

**[CODE]** Threshold plumbing would still need explicit treatment: existing `theta_logit` and cosine thresholds are positive similarity thresholds, whereas negative distance logits reverse the interpretation and scale. A Mahalanobis variant additionally needs a supplied or learned positive-semidefinite `M`; no such metric-learning artifact was found in the cross-graph discovery path. **NOT FOUND.**

## 3-line bottom line

**[CODE]** (a) L1 is L2/distance-geometric inside `src/models/profile_scorer.py:ProfileScorer.score`, but L2 discovery is dot-product/cosine-based in `src/models/cross_attention.py:CrossGraphAttention.compute_logits`; it is convertible to an L2 implementation, but not distance-geometric as coded.

**[MEASURED]** (b) The scaling law collapses to pair-count combinatorics: the stored total yield is 600 per graph pair and the derived per-pair exponent is approximately 0 across `experiments/exp3_multidomain_scaling/results/scaling_data.csv` and `extended_scaling_data.csv`.

**[CODE]** (c) The single largest threat to the two-level thesis is that the proposed cross-graph “distance geometry” is neither implemented nor tested: discovery uses the same dot-product primitive the L1 claim rejects, while its synthetic labels are planted by `src/data/entity_generator.py:inject_signals` and its scaling headline is raw pair-count growth.
