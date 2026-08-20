# H-CURVE parametric regen — design v1

This is a Stage-2 run design only. It does not report a result and does not reuse the lost LLM-vector artifacts. The implementation repo is the sibling `graph-attention-engine-v50`; the dedicated Stage-3 experiment location is `graph-attention-engine-v50/experiments/h_curve_parametric_regen/`. The paper-facing design and, later, the result remain under `copilot-sdk/docs/design/blogs/hypotheses/h-curve/`.

## Run design

The run will execute one independent `OracleSeparationExperiment` for every seed/epsilon cell:

| Parameter | Frozen value |
|---|---|
| Seeds | `42`, `123`, `777` |
| `epsilon_firm` | `0.05`, `0.20`, `0.35` |
| `max_decisions` | `300` for `0.05` and `0.20`; `600` for `0.35` |
| Initial scorer state | expert (`GT_1 ± 0.05`) for the `0.05` case; cold (`uniform(0.5) ± 0.15`) for the `0.20` case; the `0.35` initialization must be recorded explicitly in the manifest before execution rather than inferred after the run |
| Phase vectors | `cold_start` for both phases; Phase 2 must not use `post_disruption` |
| Noise | `sigma_noise = 0.08` |
| Rolling window | `w = 10` |
| Accuracy threshold | `theta = 0.85`, used only for the secondary `N_half` check |
| Disruption | the documented oracle configuration, with disrupted categories and magnitude recorded in the manifest |

The Stage-3 runner will import `FactorVectorSampler`, `CanonicalCentroid`, and `OracleSeparationExperiment` from `graph-attention-engine-v50/gae/synthetic.py`. `FactorVectorSampler(d, sigma_profile, seed)` creates the parametric samples; `.sample("cold_start", n)` creates the Phase-1 list and a second independent `.sample("cold_start", n)` creates the Phase-2 list. The runner constructs `GT_1`, constructs the scorer's `mu_0`, and records both before passing them to `OracleSeparationExperiment(scorer, canonical_gt1, epsilon_firm, disruption_magnitude, disrupted_categories, window=10, theta=0.85, max_decisions=...)`. It then calls `run_phase1(phase1_samples)`, `run_phase2(phase2_samples, phase1_result)`, and `compute_gamma(phase1_result, phase2_result)`.

The protocol is oracle separation: `_oracle_correct` labels an action by the nearest action centroid in the hidden canonical target, while the scorer updates its own centroids. Thus the target is not supplied as the scorer's current answer. The runner must assert and persist `GT_1 != mu_0`; for the production construction the target is `GT_1 = canonical_mu_0 + epsilon_firm` in the documented displacement direction, so the initial target is unreached by exactly the configured firm mismatch rather than copied from the live scorer.

The implementation evidence for this invocation is `graph-attention-engine-v50/gae/synthetic.py:FactorVectorSampler`, `:CanonicalCentroid`, `:OracleSeparationExperiment.__init__`, `:OracleSeparationExperiment.run_phase1`, `:OracleSeparationExperiment.run_phase2`, and `:OracleSeparationExperiment.compute_gamma`. The existing API returns the per-decision distance arrays in `GammaResult`, but it does not provide the persistence manifest; the Stage-3 runner will add that at the experiment boundary.

## Non-centroidality check

Parametric samples are non-centroidal by construction for this run: the sampler draws each factor vector from a clipped Gaussian around the generic base mean `0.5` with the configured per-factor noise profile (`graph-attention-engine-v50/gae/synthetic.py:FactorVectorSampler.sample`, lines 84–98), rather than drawing vectors as perturbations of any scorer centroid or selecting vectors from the GT centroid tensor. No LLM, competence label, or scorer state may enter sample generation.

The runner will nevertheless measure the construction instead of treating it as a verbal guarantee. For every seed, epsilon, phase, and regime, it will persist for each generated vector `f`:

* `||f - GT_action||_2` for the oracle action centroid selected by the regime/action label;
* `min_a ||f - GT_action_a||_2` across actions in that regime;
* `min_a ||f - mu_0_action_a||_2` and the corresponding distance to the Phase-1-final `mu` snapshot;
* the inter-action and inter-regime centroid spacings used for scale comparison.

The report will give mean, median, standard deviation, and IQR per regime, plus the ratio of vector-to-nearest-centroid distance to the relevant inter-centroid spacing. `CLUSTERED` is reserved for a distribution whose distance is small relative to spacing; `DISPERSED` is reserved for the opposite. The pre-registered circularity check fails closed if the distances are not measurable, if `GT_1` and `mu_0` are equal, or if the runner accidentally produces vectors from a centroid-centered construction.

## θ-free γ definition

The primary rate is based only on the logged centroid-distance trajectory, not on rolling accuracy. For each phase independently, let `d_t` be the Frobenius distance `centroid_distance_to_canonical(mu_t, target_phase)` returned by `graph-attention-engine-v50/gae/convergence.py:centroid_distance_to_canonical` and logged by `ConvergenceTrace.centroid_distances`. Let `d_0` be the first recorded distance and define the fixed half-distance crossing:

`N_half_dist = min { t >= 1 : d_t <= 0.5 * d_0 }`.

The primary phase rate is `r_dist = 1 / N_half_dist`; if the crossing is not observed by `max_decisions`, the cell is censored and its primary γ is `INCONCLUSIVE`, never assigned a favorable value. The primary statistic is:

`gamma_dist = r_dist,1 / r_dist,2 = N_half_dist,1 / N_half_dist,2`.

This is θ-free: no accuracy threshold, rolling window, or oracle correctness count is used. The runner will also fit `log(d_t)` against decision index as a prespecified exploratory exponential-rate estimate; it cannot replace the half-distance result. Monotonicity for F3 is checked on the raw stored trajectory, with a violation whenever any `d_t > d_(t-1)`; no smoothing may hide a violation.

For F2 only, the runner reports the existing secondary `N_half` values from `GammaResult` (`theta=0.85`) and `gamma_nhalf = N_half,1 / N_half,2`. It compares the sign of `gamma_dist - 1` with the sign of `gamma_nhalf - 1` per cell and across the epsilon-level summary. Missing or DNF values are reported as missing, not converted to zero or one.

The binary prediction is fixed before execution: `epsilon_firm < epsilon★` predicts `gamma_dist < 1`, while `epsilon_firm > epsilon★` predicts `gamma_dist > 1`, with `epsilon★` computed from the recorded disruption configuration. F1 fires if either side's prediction fails; F2 fires if θ-free and `N_half` directions disagree; F3 fires if any required phase/seed trajectory is non-monotone under the raw rule.

## Persistence + manifest

Stage 3 will write fresh artifacts under:

`graph-attention-engine-v50/experiments/h_curve_parametric_regen/raw/`

The required artifact layout is:

```text
raw/
  manifest.json
  runs/seed-042/epsilon-0.05/
    vectors_phase1.jsonl
    vectors_phase2.jsonl
    centroids_gt1.npy
    centroids_gt2.npy
    centroids_mu0.npy
    centroids_mu_phase1_final.npy
    centroids_mu_phase2_final.npy
    distance_trajectories.json
    gamma.json
    vector_distance_summary.json
  ... one directory per seed/epsilon cell ...
```

Each vector record includes seed, epsilon, phase, regime, generation seed, vector values, and sigma profile. Each centroid snapshot records shape, dtype, construction label (`gt1`, `gt2`, `mu0`, `mu_phase1_final`, `mu_phase2_final`), and the array content hash. `distance_trajectories.json` includes raw per-decision distances, rolling accuracy, phase, target identity, monotonicity result, and the distance-half crossing. `gamma.json` includes `gamma_dist`, the exploratory fitted rates, `gamma_nhalf`, DNF/censoring flags, threshold, theorem prediction, and F1/F2/F3 cell status.

The top-level `manifest.json` is written only after all cells complete and contains:

* schema version and UTC creation time;
* source repository identifier and runner entry point;
* exact seeds, epsilon values, max decisions, initialization mode, vector regime, sigma, window, theta, disruption magnitude/categories, dimension, action/category counts, and software/runtime versions;
* the construction statement that vectors are parametric and that `GT_1 = canonical_mu_0 + epsilon_firm`;
* relative path, byte size, SHA-256, and artifact role for every file;
* per-cell completion/DNF/censoring status and a hash of the canonicalized configuration.

The runner will use atomic temporary-file replacement for each JSON/JSONL artifact and will fail if any expected artifact or hash is absent. A later analyst can recompute both γ values and all non-centroidality summaries from the persisted artifacts without importing the scorer.

## Power & reading

The primary run has three independent seeds per epsilon, exactly matching the documented configuration. The report will show every seed, the mean and median, and a two-sided 95% uncertainty interval for `gamma_dist` and for the distance-rate difference on the log scale. With `n=3`, the interval will use a transparent small-sample method and the report will explicitly label the direction as thin; three seeds are enough to reproduce the historical configuration, but not enough to make a strong population-level precision claim if seed outcomes disagree.

The binary reading is therefore conservative: a clean direction at all three seeds is evidence of reproducibility of this parametric mechanism, not a high-powered estimate of a universal effect. If the three seeds disagree, or a confidence interval spans the decision boundary, the result is inconclusive and the proposed extension is 20 or more preregistered seeds per epsilon with the same code and manifest—not a silent substitution into this run. No epsilon cell may be called validated solely because its point estimate has the predicted sign.

The final result will report F1, F2, and F3 separately, then state whether non-centroidality is `CLUSTERED` or `DISPERSED`. It will keep this oracle-mechanism result separate from EXP-G1 model validity: success here does not establish that real analyst decisions follow centroidal geometry.

## Self-check (could this ONLY confirm?)

No: the fixed below/above-threshold cells, the raw monotonicity test, the fail-closed censored γ, the persisted vectors and snapshots, and the independent `N_half` direction check can produce a clean F1, F2, or F3 failure without changing the hypothesis or rerunning a favorable generator.

## Open questions

1. The source API exposes the sampler and experiment, but no current dedicated runner or persistence format. Stage 3 must implement the runner in the reserved experiment directory and have review approve the exact `0.35` initialization before execution.
2. The documented `epsilon★ ≈ 0.125` depends on disruption magnitude, disrupted-category fraction, and the theorem configuration. The runner must record these values and compute the threshold from the same inputs rather than hard-code the rounded headline.
3. The precise canonical `mu_0` construction for the expert and cold cases is documented at the experiment level but is not exposed by a single current factory in the inspected source. Stage 3 must resolve that factory/configuration from the authoritative experiment setup before any run; if it cannot, the run stops rather than silently substituting an initialization.
