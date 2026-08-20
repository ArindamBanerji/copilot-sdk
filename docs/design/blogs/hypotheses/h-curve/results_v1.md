# H-CURVE two-arm parametric run — results v1

## Design fixes applied

Four apparatus fixes were applied without modifying `ProfileScorer`, the theorem update, the
geometry assertions, or the falsification logic.

1. **DF-1 — phase targets:** Phase-2 vectors were previously GT1-centered while distance used
   GT2. Phase 2 now draws around GT2 and measures against GT2, preserving same-target convergence.
2. **DF-2 — outcome labels:** noisy vectors were previously reclassified by nearest GT action. The
   persisted round-robin `(c,a)` label is now the ground-truth outcome, preventing uncontrolled
   label noise from defeating coverage.
3. **DF-3 — fixed active subspace:** the dynamic active mask made d0 incomparable with later
   distances and caused spurious first-decision half crossings. Active distance now uses the known
   final 24-cell coverage mask from t=0; dynamic masks remain persisted coverage evidence.
4. **DF-4 — fit-validity gate:** the prior `d_inf/d0 <= 0.50` absolute-depth gate was removed. It
   violated the scale-free meaning of gamma and censored valid decays near the noise floor. The
   corrected gate requires only `k > 0` and at least five retained ten-decision blocks in both fits.
   Plateau depth remains descriptive. Gamma was recomputed from the persisted trajectories by
   `recompute_fit_gate_v4.py`; no rerun or scorer import was used for this correction.

All fixes are recorded as DF-1 through DF-4 in the manifest.

## Variants tried

| Variant | Change | Finding | Decision |
|---|---|---|---|
| V0 | Absolute plateau gate `d_inf/d0 <= 0.50` | Censored valid rate comparisons near the noise floor | Retired; violates I3 |
| V1 | GT2-centered Phase-2 vectors | Restored same-target Phase-2 trajectories | Retained |
| V2 | Fixed final 24-cell active mask from t=0 | Removed denominator-induced N_half=1 artifact | Retained |
| V3 | Fit-validity-only gate | Allows scale-free rate ratios while rejecting non-positive/degenerate fits | Trusted variant |

V3 is trusted because it tests exactly the required object—the relative decay rate—without an
a-priori absolute-depth censoring rule, while retaining a fail-closed positive-fit requirement.

## Non-centroidality

Phase 1 vectors were generated around GT1 and Phase 2 vectors around the same phase's GT target.
Neither arm supplied a scorer centroid to vector generation. Across both phases and all seeds, the
distance from a vector to its labeled phase center had mean 0.1886, median 0.1859, and SD 0.0548.
The mean distance to the canonical 0.5 prior was 0.1889, 0.1926, and 0.2008 for epsilon 0.05,
0.20, and 0.35. The data are dispersed, class-bearing, and non-circular.

**Verdict: DISPERSED.**

## Per-arm convergence-gate table

The corrected gate is fit-validity only. Plateau ratios are shown for diagnosis, not gating.

| Arm | epsilon | Phase-1 d_inf/d0 (42/123/777) | Phase-2 d_inf/d0 (42/123/777) | Valid fits (3) |
|---|---:|---:|---:|---:|
| A production | 0.05 | 1.892 / 2.371 / 2.000 | 0.859 / 0.799 / 0.822 | 1/3 |
| A production | 0.20 | 0.767 / 0.798 / 0.787 | 0.804 / 0.788 / 0.763 | 3/3 |
| A production | 0.35 | 0.499 / 0.511 / 0.491 | 0.616 / 0.629 / 0.568 | 3/3 |
| B theorem | 0.05 | 3.044 / 2.872 / 2.791 | 0.467 / 0.444 / 0.421 | 2/3 |
| B theorem | 0.20 | 0.787 / 0.745 / 0.752 | 0.467 / 0.444 / 0.419 | 3/3 |
| B theorem | 0.35 | 0.414 / 0.439 / 0.465 | 0.426 / 0.351 / 0.424 | 3/3 |

The Phase-2 sanity assertions passed for all 18 cells: disrupted vector means were closer to GT2
than GT1 and within 2 sigma of GT2, and Phase-2 starting disrupted distance was within 0.10 of the
GT1-to-GT2 shift.

## Gamma rate and N_half on P3 subspaces

Phase 1 rates use all 24 cells; Phase 2 rates use disrupted cells `[0,1]`. Gamma is
`k_phase2/k_phase1`; N_half gamma is `N_half_phase1/N_half_phase2`.

| epsilon | Arm A gamma_rate (42/123/777) | Arm A N_half gamma | Arm B gamma_rate (42/123/777) | Arm B N_half gamma |
|---:|---|---|---|---|
| 0.05 | censored / 1.049 / censored | censored | censored / censored / censored | censored |
| 0.20 | 0.797 / 1.063 / 1.167 | censored | 1.163 / 1.573 / 1.312 | censored |
| 0.35 | 0.866 / 0.776 / 0.758 | censored / 0.951 / 0.902 | 1.310 / 0.682 / 1.011 | 1.387 / 1.597 / 1.925 |

The epsilon=0.20 cells now have valid gamma values for both arms; the earlier absolute gate had
incorrectly censored them. N_half crossings are censored in those cells because the half-distance
criterion is secondary and the noisy trajectories do not cross it reliably.

## Arm A versus Arm B

Arm B satisfies the above-threshold binary prediction at ε=0.20 for all three geometries and at
ε=0.35 for seeds 42 and 777. Arm A is mixed at ε=0.20 and is below one for all three ε=0.35
geometries. This is a substantive A-vs-B divergence under identical GTs, vectors, schedules, and
decision labels: the theorem reference re-converges faster in the higher mismatch arms, while the
production update does not consistently do so.

The divergence is not repaired or averaged away. It separates the idealized theorem dynamics from
the deployed production policy dynamics, which is the purpose of the two-arm design.

## F1/F2/F3 verdicts

- **F1 fired for Arm A** at ε=0.20 seed 42 and all three ε=0.35 seeds; its valid above-threshold
  gamma values were not consistently above one.
- **F1 fired for Arm B** at ε=0.35 seed 123 because gamma=0.682 below one above epsilon_star.
  Its ε=0.20 arm passed all three above-threshold directions.
- **F2 fired for Arm B** at ε=0.35 seed 123: gamma_rate=0.682 but gamma_half=1.597. The other
  valid ε=0.35 Arm B cells agree in direction. Arm A has no valid N_half pair except two ε=0.35
  cells, where both primary and secondary directions are below one.
- **F3 fired only for fit-invalid cells:** Arm A ε=0.05 seeds 42/777 and Arm B ε=0.05 seed 42.
  No absolute plateau ratio fired F3 under the corrected invariant-preserving gate.

For epsilon 0.05, the required scope statement is:

> Below-threshold cell inconclusive due to noise dominance at ε_firm < σ_noise (0.05 < 0.08);
> consistent with the theorem's prediction of negligible advantage below ε★, but NOT a confirmed
> γ < 1. The above-threshold arms (ε=0.20, 0.35) carry the binary test and the paper's spine.

## Verdict

**Arm A production: INVALIDATED for the tested binary claim.** Valid above-threshold cells are not
consistently gamma>1, and the ε=0.35 arm is gamma<1 for all three geometries.

**Arm B theorem reference: PARTIALLY SUPPORTED but not validated.** ε=0.20 is gamma>1 across all
three geometries; ε=0.35 fails in one geometry and also fires F2 there.

**Overall H-CURVE: INCONCLUSIVE / re-defining.** The corrected fit-validity apparatus exposes a
real production-vs-theorem split and a mixed theorem result. The three-seed design is a geometric
robustness check, not sufficient power for a population-level claim; no 20-seed extension was run
because the source session did not ratify that extension.

## Artifacts and persistence completeness

Original artifacts:

`graph-attention-engine-v50/experiments/h_curve_parametric_regen/raw/two_arm_v4/`

Scorer-free recomputation:

`graph-attention-engine-v50/experiments/h_curve_parametric_regen/raw/two_arm_v4/fit_gate_recompute.json`

Manifest:

`graph-attention-engine-v50/experiments/h_curve_parametric_regen/raw/two_arm_v4/manifest.json`

The manifest contains 18 cells and 236 hashed artifact files, including the fit-validity
recomputation. Every listed path, byte size, and SHA-256 passed verification. Each cell contains
GT-centered vectors and labels, canonical prior, GT1, GT2, mu0, both final centroid snapshots,
full/active/disrupted trajectories, dynamic masks, per-cell counts, geometry and Phase-2 sanity
assertions, and gamma/gate/falsifier records. **PERSISTENCE-COMPLETENESS: PASS.** All distance,
fit, and gamma results can be recomputed without importing the scorer.

## Arm C policy sweep

Arm C reused the persisted vectors, GT snapshots, schedules, coverage, P3 subspaces, fit-validity
gate, and falsifiers. Only the update policy changed. The C run covered all three independent
geometries at the two above-threshold values; n=3 remains a geometric robustness probe, not a
population-level validation.

| Policy | epsilon | gamma_rate by seed 42 / 123 / 777 | N_half gamma where available | Gate |
|---|---:|---|---|---|
| C1 symmetric rate | 0.20 | 0.786 / 1.056 / 0.994 | censored / censored / censored | 3/3 pass |
| C1 symmetric rate | 0.35 | 0.797 / 0.504 / 0.921 | censored / censored / censored | 3/3 pass |
| C2 shift-triggered boost | 0.20 | 0.916 / 1.244 / 0.980 | censored / censored / censored | 3/3 pass |
| C2 shift-triggered boost | 0.35 | 0.905 / 0.771 / 0.846 | censored / 0.953 / 0.879 | 3/3 pass |
| C3 production theorem rate | 0.20 | 0.786 / 1.056 / 0.994 | censored / censored / censored | 3/3 pass |
| C3 production theorem rate | 0.35 | 0.797 / 0.504 / 0.921 | censored / censored / censored | 3/3 pass |

C1 and C3 are numerically identical in this standalone harness, so enabling the theorem rate inside
the production machinery did not expose an additional suppressor here. C2 improves the first
geometry at both above-threshold epsilons and the second geometry at epsilon 0.20, but no policy
has gamma_rate > 1 for all three geometries at either above-threshold epsilon. C2 is conditional on
the experiment-local rolling error-spike detector because no production shift detector was found;
it is therefore a roadmap candidate, not a deployable-as-is fix.

**Arm C reading:** no C policy recovers the binary claim consistently at n=3. C1/C3 fail F1 on
multiple above-threshold geometries; C2 also fails F1 at both tested epsilons. F3 is false for all
C cells. F2 is false where N_half is unavailable and otherwise false for the reported C2 epsilon
0.35 cells.

## Design fixes applied (Arm C extension)

- **DF-C1 — policy-only sweep:** reused the exact persisted apparatus and changed only the update
  policy, preserving I1-I6 and preventing a what-if from becoming a data or metric change.
- **DF-C2 — detector disclosure:** verified no production change-point/drift trigger is exposed;
  C2 uses a bounded experiment-local rolling error spike and is labeled conditional rather than
  presented as production-ready.
- **DF-C3 — chart provenance:** generated the verification figure from persisted fit recomputation,
  C summary, and trajectories; registered PNG, PDF, and chart metadata with SHA-256 in the primary
  manifest.

## Verification chart

Publication outputs:

- `graph-attention-engine-v50/experiments/h_curve_parametric_regen/figures/hcurve_gamma_by_epsilon.png`
- `graph-attention-engine-v50/experiments/h_curve_parametric_regen/figures/hcurve_gamma_by_epsilon.pdf`

The primary panel shows all A/B/C seed points and means across epsilon, gamma=1, epsilon-star,
and censored cells as explicit non-numeric markers. The companion panel shows representative
persisted active-distance trajectories for A, B, and C2 at seed 42 and epsilon 0.35. The chart is
not a new analysis: its inputs are the persisted artifacts listed in `chart_metadata.json`.

## Arm C artifacts and persistence

Arm C raw artifacts and summary:
`graph-attention-engine-v50/experiments/h_curve_parametric_regen/raw/arm_c_v4/`

Arm C manifest:
`graph-attention-engine-v50/experiments/h_curve_parametric_regen/raw/arm_c_v4/manifest.json`

The primary A/B manifest now also hashes the verification PNG, PDF, and metadata. Its post-write
verification reports 239 hashed files with valid byte sizes and SHA-256 values. The A/B tree has
236 original/recomputed files and the C tree contains all 18 policy cells; scorer-free recompute
of the reported gamma values and chart inputs remains possible.
