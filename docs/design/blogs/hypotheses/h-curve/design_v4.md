# H-CURVE parametric regeneration — design v4

This is the corrected, run-ready protocol for the H-CURVE parametric experiment. It carries
forward design_v3's all-cold initialization, independent oracle geometries, threshold straddle,
full persistence, and scorer-free recomputation requirements. EXP-G1 remains out of scope.

## Corrected construction (GT-centered, coverage, active-cell)

### Frozen configuration carried forward

- Run seeds: 42, 123, 777. Firm mismatches: epsilon_firm = 0.05, 0.20, 0.35.
- Tensor shape: C=6, A=4, d=6. Disrupted categories: [0, 1].
- Disruption magnitude: norm(Delta)=0.25; alpha_disrupt=2/6.
- Noise: sigma_noise=0.08. Rolling window w=10. theta=0.85 is used only by N_half.
- The scorer starts from the exact canonical prior, `scorer_mu0 = canonical_prior =
  np.full((6,4,6), 0.5)` for every seed and epsilon. Expert and jittered starts are retired.
- `oracle_seed = 99 + run_seed`: 141, 222, and 876. The vector RNG and oracle RNG remain
  separate. `oracle_epsilon = epsilon_firm / (C*A) = epsilon_firm / 24`.
- Construct GT1 by the existing oracle displacement from the exact canonical prior. Before any
  cell runs, assert elementwise equality of scorer_mu0 and canonical_prior, no clipping of GT1,
  `norm(GT1 - scorer_mu0, ord='fro') == epsilon_firm` within 1e-10 for every seed, and strict
  per-seed ordering 0.05 < 0.20 < 0.35.
- Compute `epsilon_star = (alpha_disrupt * norm(Delta)) / (1-alpha_disrupt)` from the recorded
  disruption inputs. Assert epsilon_star=0.125 and that 0.05 is below it while 0.20 and 0.35
  are above it. Do not use the pre-cancellation expression in the stale generation note.

### Change 1 — GT-centered vectors

The required draw for a decision whose center label is `(c,a)` is exactly:

    f = np.clip(GT1[c, a, :] + rng.normal(0.0, 0.08, size=6), 0.0, 1.0)

The center is the oracle's GT1 cell, never the scorer's current or initial centroid. Persist
`center_label = "GT1[c,a]"`, `(category_index, target_action_index)`, the draw seed/index, and the
unclipped and clipped vectors. This makes the non-circularity explicit: the data are generated
from a fixed oracle target while the scorer begins at the separate canonical prior and must learn;
the target is not obtained from scorer state or from a product scorer.

The current implementation does not meet this construction as-is. In
`graph-attention-engine-v50/gae/synthetic.py:39-66`, `FactorVectorSampler` stores only a global
dimension and sigma profile, and at `:68-98` `sample()` hard-codes a 0.5 base mean with an
optional global offset. `FactorVectorSample` at `:30-36` also has no class/action center label.
The minimal experiment-local change is to add `center: np.ndarray`, `category_index`,
`target_action_index`, and `center_label` to the sample path, with `center` shape-checked as `(6,)`
and used as `base_mean` when supplied. The exact call after that change is:

    sampler.sample(regime="cold_start", n=1, center=GT1[c, a, :],
                   category_index=c, target_action_index=a,
                   center_label=f"GT1[{c},{a}]")

The sampler must use the independent vector RNG for the normal draw and clip only the generated
vector. No scorer centroid is passed into this call.

### Change 2 — coverage of every category/action cell

For each phase, create a deterministic round-robin schedule over all 24 `(c,a)` labels. Keep the
documented decision budgets of 300 for epsilon 0.05 and 0.20 and 600 for epsilon 0.35. The schedule
is repeated and truncated to the budget, so the minimum target-label counts are 12, 12, and 25 per
cell respectively. Persist the complete per-cell counts and assert every count is at least the
corresponding minimum before calculating any convergence metric.

The current `OracleSeparationExperiment._run_phase` in
`graph-attention-engine-v50/gae/synthetic.py:238-289` is not sufficient: it calls `score(...,
category_index=0)` and `update(..., category_index=0, ...)` for every sample. The minimal harness
change is to consume the sample's category index, compute the oracle action for that category, and
pass the target action into the update. This is required because `ProfileScorer.update` at
`copilot-sdk/copilot_sdk/scoring/profile_scorer.py:780-817` can pull the ground-truth cell only
when `gt_action_index` is supplied on an incorrect decision. The required update shape is:

    result = scorer.score(f, category_index=sample.category_index)
    gt_action = oracle_action(f, sample.category_index, phase_target)
    scorer.update(f, sample.category_index, result.action_index,
                  correct=(result.action_index == gt_action),
                  gt_action_index=gt_action)

Coverage is defined by target-label updates, not merely by vectors being generated. The harness
must persist the decision-to-cell mapping and counts, and fail closed if a cell did not receive an
update. This is a minimal experiment harness change, not a change to the scorer's learning rule.

### Change 3 — full-tensor and active-cell distances

At every decision t, persist both distances against the phase target:

    d_full[t] = ||mu[t] - GT_phase||_F
    d_active[t] = ||(mu[t] - GT_phase)[active_cells]||_F

`active_cells` is the `(c,a)` mask whose target-labelled update count is positive at t. The full
distance is retained for comparison with v3; active-cell distance is the primary convergence
signal. With the required schedule, the final active mask contains all 24 cells, so equality of
the final full and active values is expected and is evidence that the prior static-cell floor was
removed, not a coding error. Persist the mask/count snapshot with each trajectory.

The existing phase loop records only a full canonical-target distance at
`synthetic.py:262-263`; it has no active mask. Add an experiment-local trace hook (or equivalent
small `_run_phase` extension) that records the two values after each update. No scorer API or
learning threshold is changed.

## Convergence gate before gamma

For each seed, epsilon, and phase, set `d0` to the first active-cell distance and estimate the
plateau `d_inf` as the mean of the final 20 percent of the active-cell trajectory. The gate passes
only when the active trajectory has a valid positive decay fit and `d_inf/d0 <= 0.50` in both
phases. The 0.50 cutoff is an operational low-plateau gate, not a theorem parameter; it makes the
secondary half-distance crossing reachable. Also require all 24 cells to meet coverage and at least
five positive residual blocks for the rate fit.

If any cell fails this gate, stop that run before forming either gamma and write exactly:

    convergence not restored

The result is then F3 fired / INCONCLUSIVE for gamma, with no binary prediction inferred from a
non-converging trajectory. The old raw-step monotonicity requirement is retired; stochastic
per-decision increases are not a falsifier.

## Theta-free gamma and falsifiers

The primary rate is fit on active-cell distance to the estimated plateau. Partition the trajectory
into non-overlapping ten-decision block means, retain blocks with `d_block > d_inf + noise_sigma`,
and fit `log(d_block-d_inf) = intercept - k*t` using a median-of-pairwise-slopes estimator. Require
at least five retained blocks and k>0. The rate is k, and the primary direction-preserving ratio
is:

    gamma_rate = k_phase2 / k_phase1

Re-convergence faster than first convergence therefore has gamma_rate > 1. Report each seed and
epsilon, followed by the pre-registered three-seed summary; do not collapse away a failed cell.

The half-distance crossing is secondary: record the first decision where active distance is at or
below 0.5*d0 in each phase and report `gamma_half = N_half_phase1 / N_half_phase2` when both
crossings exist. The existing theta-dependent N_half uses theta=0.85 and is used only to test F2
direction agreement with gamma_rate. A missing crossing is censored, not imputed.

F1 fires if the primary binary prediction fails: gamma_rate is not below 1 for the below-threshold
arm and/or not above 1 for the above-threshold arms. The epsilon=0.05 arm remains subject to C3:

    Below-threshold cell inconclusive due to noise dominance at ε_firm < σ_noise (0.05 < 0.08);
    consistent with the theorem's prediction of negligible advantage below ε★, but NOT a confirmed
    γ < 1. The above-threshold arms (ε=0.20, 0.35) carry the binary test and the paper's spine.

F2 fires when the primary theta-free gamma and the theta-dependent N_half gamma disagree in
direction on a non-censored cell. F3 is the convergence-gate failure described above. EXP-G1 is
not run or interpreted.

## Persistence and scorer-free recomputation

Use `graph-attention-engine-v50/experiments/h_curve_parametric_regen/raw/runs/` as the dedicated
experiment location. Every seed/epsilon cell must contain:

- Phase 1 and Phase 2 GT-centered vectors, labels, seeds, and clipping metadata.
- canonical_prior, GT1, GT2, mu_0, mu_phase1_final, and mu_phase2_final snapshots.
- full and active distance trajectories, active masks/counts, and per-cell update counts.
- vector-to-GT/vector-to-mu distance summaries, the geometry assertions, and the gamma record with
  censoring and F1/F2/F3 flags.

Write `manifest.json` only after all cells and expected artifacts exist. It contains schema version,
UTC creation time, source repository and runner entry point, the complete frozen configuration,
construction statement, epsilon_star inputs/value, and for every file its relative path, byte size,
SHA-256, and artifact role. Write atomically via temp file then replace, and fail closed if any
expected file or hash is absent. The results document must state that a later analyst can recompute
both gamma values, active/full distances, and vector-distance summaries without importing the
scorer.

## Analysis, power, and reading

Report non-centroidality per `(seed, epsilon, regime, c, a)` as distances to GT1 and scorer mu0;
label the result DISPERSED or CLUSTERED descriptively. Report full versus active d0, d_inf, and
their ratios before any gamma. The three run seeds now span three independent firm-deviation
geometries, not merely three noise samples at one oracle direction. Three geometries are still thin
for a population-level claim, so report all cells and an across-geometry interval, and describe
the reading as geometric robustness evidence rather than a powered generalization result.

The clean epsilon-only contrast is now the complete all-cold grid: all three epsilon cells use the
same exact scorer prior. The x-axis is configured epsilon_firm; also report post-construction
`||GT1-scorer_mu0||_F` as a secondary geometry column. Do not call this a bit-for-bit reproduction
of the retired expert/cold audit.

## Code-feasibility gate

The required construction is not executable through the current harness without the minimal
experiment-local changes identified above: per-cell center/label support in `FactorVectorSampler`
and `FactorVectorSample`; category-aware scoring and updates with `gt_action_index` in
`OracleSeparationExperiment._run_phase`; and an active-distance trace hook. The canonical prior,
GT displacement, oracle seeds, epsilon-star calculation, scorer update rule, and existing phase
targets are otherwise available in the current code. Do not silently substitute 0.5-centered
vectors, category 0, full-distance-only traces, or scorer-derived centers.

## Self-check

Could this design only produce gamma>1? No: GT-centered draws, balanced all-cell updates, a
fail-closed convergence gate, a fixed primary exponential fit, and both above-threshold arms leave
clear paths to gamma_rate <= 1, F1, F2, or F3.

## Open questions for review

1. Ratify the operational convergence gate `d_inf/d0 <= 0.50`; the theorem fixes the prediction but
   does not supply a numerical phrase for “low plateau.”
2. Approve the minimal experiment-local sampler/sample metadata and category-aware harness changes;
   without them, Changes 1 and 2 cannot be met by the code as-is.
