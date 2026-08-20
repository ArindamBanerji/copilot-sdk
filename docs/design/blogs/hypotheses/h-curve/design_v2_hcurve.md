# H-CURVE parametric regen — design v2 (CONSOLIDATED, run-ready, frozen)

**This is the single authoritative design.** It consolidates design_v1.md + v1.1 + v1.2 + v1.3 into one document so review and execution run against one touchstone (the v1.x chain remains as the pre-registration trail; where they differ, **v2 is authoritative**). Reviewers and the Stage-4 runner read THIS file. It is run-ready: the only remaining gate is the runtime ε★-straddle assertion, which passes under the frozen disruption config.

Stage-3 experiment location: `graph-attention-engine-v50/experiments/h_curve_parametric_regen/`. Paper-facing design + result live under `copilot-sdk/docs/design/blogs/hypotheses/h-curve/`. Not a reuse of the lost LLM-vector artifacts; a clean parametric test of the same theorem (see Scope note). Scope wall: model validity / EXP-G1 is out of scope.

---

## Frozen constructions (D1–D4, ratified by the source session)

**D1 — cold μ₀ (single init for ALL three ε cells; expert cell retired).** `μ₀ = clip(0.5 + Uniform(−0.15, +0.15), 0, 1)`, i.i.d. per (category, action, factor), from a **dedicated μ₀ RNG seeded `7 × run_seed`** (→ 294 / 861 / 5439 for run_seeds 42 / 123 / 777), distinct from the oracle RNG (seed 99) so μ₀ and GT never share a stream. μ₀ ∈ [0.35, 0.65] — intentionally mediocre (not near GT, not near edges): the genuine cold-start Phase 1 must learn from. The expert init (`GT₁ ± 0.05`) is retired — it had no authoritative construction in the code snapshot and came from the unverifiable original config.

**D2 — GT₁ ≠ μ₀.** GT₁ is built by the oracle's canonical displacement (below), independent of μ₀. The runner **asserts and persists `‖GT₁ − μ₀‖_F > 0` per cell**. No minimum separation — separation is governed by ε_firm (the experiment variable); at ε=0.05 both GT and μ₀ sit near canonical *by design* (the below-threshold test), and a floor would bias exactly that regime.

**D3 — disruption config + tensor shape.** **C = 6** categories, **A = 4** actions (escalate / investigate / suppress / monitor), **d = 6** factors (privileged_identity, asset_criticality, threat_intel, pattern_history, time_anomaly, device_trust) → tensor **(6, 4, 6) = 144**. `disrupted_categories = [0, 1]` (α_disrupt = 2/6), `‖Δ‖ = 0.25`, `θ = 0.85` (N_half only).

**D4 — x-axis + transparency.** Report **ε_firm (configured)** on the x-axis; also log **post-clip `‖GT₁ − prior‖_F`** as a secondary manifest column. The binary prediction needs only the ordering (0.05 < 0.20 < 0.35), which holds regardless of clipping.

## ε★ — canonical form, computed + straddle-gated

ε★ = **(α_disrupt · ‖Δ‖) / (1 − α_disrupt)** (θ-cancelled). Under D3: (0.333·0.25)/0.667 = **0.125**. Grid straddles: 0.05 < 0.125 < 0.20 < 0.35. The runner computes ε★ from the recorded D3 inputs and **asserts the straddle before any γ cell** (STOP if it does not straddle).
*Upstream doc defect (log for cga v8; not an experiment change):* `synthetic_data_generation_v2.md` states the pre-cancellation form `ε★ = α·‖Δ‖·θ/(θ−(1−α))` ≈ 0.128, but that evaluates to ≈ 0.387 with these inputs. Use the θ-cancelled form (0.125). Do NOT use the pre-cancellation form.

---

## Run design

One independent `OracleSeparationExperiment` per seed × ε cell:

| Parameter | Frozen value |
|---|---|
| Seeds | `42`, `123`, `777` |
| `epsilon_firm` | `0.05`, `0.20`, `0.35` |
| `max_decisions` | `300` for `0.05` and `0.20`; `600` for `0.35` |
| Initial scorer state (μ₀) | **cold, per D1, for ALL three ε cells** (single construction; expert cell retired) |
| Phase vectors | `cold_start` for both phases; Phase 2 must not use `post_disruption` |
| Noise | `sigma_noise = 0.08` |
| Rolling window | `w = 10` |
| Accuracy threshold | `theta = 0.85`, secondary `N_half` check only |
| Disruption | per D3: C=6, A=4, d=6, disrupted=[0,1], ‖Δ‖=0.25 — recorded in the manifest |

The runner imports `FactorVectorSampler`, `CanonicalCentroid`, `OracleSeparationExperiment` from `graph-attention-engine-v50/gae/synthetic.py`. `FactorVectorSampler(d, sigma_profile, seed)` creates parametric samples; `.sample("cold_start", n)` builds the Phase-1 list and a second independent `.sample("cold_start", n)` the Phase-2 list. The runner constructs μ₀ (D1) and GT₁ (oracle canonical displacement), records both, then calls `OracleSeparationExperiment(scorer, canonical_gt1, epsilon_firm, disruption_magnitude, disrupted_categories, window=10, theta=0.85, max_decisions=...)`, then `run_phase1`, `run_phase2`, `compute_gamma`.

Oracle separation: `_oracle_correct` labels an action by the nearest action centroid in the hidden canonical target, while the scorer updates its own centroids — the target is not the scorer's current answer. GT₁ = `canonical_μ₀ + ε_firm` in the documented displacement direction (normalized random direction, oracle seed 99, magnitude ε_firm·√(C·A), clipped), so the initial target is unreached by exactly the configured firm mismatch. Implementation evidence: `gae/synthetic.py:FactorVectorSampler,:CanonicalCentroid,:OracleSeparationExperiment.__init__/run_phase1/run_phase2/compute_gamma`; `GammaResult` returns per-decision distance arrays; the Stage-4 runner adds the persistence manifest at the experiment boundary.

## Non-centroidality check

Parametric samples are non-centroidal by construction: the sampler draws each factor vector from a clipped Gaussian around the generic base mean `0.5` with the configured per-factor noise profile (`gae/synthetic.py:FactorVectorSampler.sample`), NOT as perturbations of any scorer centroid nor as selections from the GT tensor. No LLM, competence label, or scorer state enters sample generation.

The runner measures the construction rather than asserting it verbally. Per seed, ε, phase, regime, for each vector `f`, it persists: `||f − GT_action||₂`; `min_a ||f − GT_action_a||₂`; `min_a ||f − μ0_action_a||₂` and the distance to the Phase-1-final μ; and the inter-action / inter-regime centroid spacings. Report: mean, median, sd, IQR per regime, plus the ratio of vector-to-nearest-centroid distance to inter-centroid spacing. `CLUSTERED` = distance small relative to spacing; `DISPERSED` = the opposite. The check **fails closed** if distances are not measurable, if `GT₁ == μ₀`, or if vectors are centroid-centered.

## θ-free γ definition

Primary rate uses only the logged centroid-distance trajectory. Per phase, let `d_t = centroid_distance_to_canonical(μ_t, target_phase)` (`gae/convergence.py`, logged by `ConvergenceTrace.centroid_distances`), `d_0` the first recorded distance, and the fixed half-distance crossing `N_half_dist = min{ t ≥ 1 : d_t ≤ 0.5·d_0 }`. Phase rate `r_dist = 1/N_half_dist`; if not reached by `max_decisions`, the cell is **censored → INCONCLUSIVE**, never a favorable value. Primary statistic `gamma_dist = N_half_dist,1 / N_half_dist,2`. θ-free: no accuracy threshold, window, or correctness count. A `log(d_t)`-vs-index exponential-rate fit is exploratory only. F3 monotonicity is checked on the raw trajectory (violation if any `d_t > d_(t−1)`; no smoothing).

For F2 only: report the secondary `N_half` (θ=0.85) γ from `GammaResult`, `gamma_nhalf`, and compare `sign(gamma_dist − 1)` with `sign(gamma_nhalf − 1)` per cell and at the ε-level. Missing/DNF reported as missing, never coerced to 0/1.

Binary prediction (fixed pre-run): `ε_firm < ε★ ⇒ gamma_dist < 1`; `ε_firm > ε★ ⇒ gamma_dist > 1`, with ε★ computed from the recorded config. **F1** fires if either side fails; **F2** if θ-free and N_half directions disagree; **F3** if any required trajectory is non-monotone (raw rule).

## Persistence + manifest

Fresh artifacts under `graph-attention-engine-v50/experiments/h_curve_parametric_regen/raw/`:

```text
raw/
  manifest.json
  runs/seed-042/epsilon-0.05/
    vectors_phase1.jsonl   vectors_phase2.jsonl
    centroids_gt1.npy  centroids_gt2.npy  centroids_mu0.npy
    centroids_mu_phase1_final.npy  centroids_mu_phase2_final.npy
    distance_trajectories.json  gamma.json  vector_distance_summary.json
  ... one directory per seed/epsilon cell ...
```

Each vector record: seed, ε, phase, regime, generation seed, values, sigma profile. Each centroid snapshot: shape, dtype, construction label (`gt1/gt2/mu0/mu_phase1_final/mu_phase2_final`), content hash. `distance_trajectories.json`: raw per-decision distances, rolling accuracy, phase, target identity, monotonicity result, half-distance crossing. `gamma.json`: `gamma_dist`, exploratory fitted rates, `gamma_nhalf`, DNF/censoring flags, threshold, prediction, F1/F2/F3 status. `manifest.json` (written only after all cells complete): schema version + UTC time; source repo + runner entry point; full frozen config (seeds, ε grid, C=6/A=4/d=6, disrupted=[0,1], ‖Δ‖=0.25, θ, σ, w, μ₀ seed rule 7×run_seed, oracle seed 99, runtime versions); the D1–D4 construction statement + `GT₁ = canonical_μ₀ + ε_firm` + canonical ε★ form/value; per-file relative path, byte size, SHA-256, role; per-cell completion/DNF/censoring status; config hash. Atomic temp-then-replace; FAIL if any expected artifact or hash is absent. **A later analyst can recompute both γ values and all non-centroidality summaries from the artifacts alone, without importing the scorer.**

## Power & reading

Three independent seeds per ε (the documented config). Report every seed, mean, median, and a two-sided 95% small-sample interval for `gamma_dist` and the log-scale distance-rate difference; label n=3 as **thin**. A clean direction at all three seeds is evidence of reproducibility of this parametric mechanism, not a high-powered universal estimate. If seeds disagree or a CI spans the boundary → **INCONCLUSIVE**, and the pre-registered extension is **≥20 seeds per ε** with the same code and manifest — never a silent substitution. No cell is validated on point-estimate sign alone. Report F1/F2/F3 separately; state non-centroidality CLUSTERED/DISPERSED. Keep this oracle-mechanism result separate from EXP-G1 model validity.

## Scope note (frozen)

Single cold init across all ε ⇒ the whole grid is a **clean ε-only contrast** (no init-mode confound; the mixed-init caveat is retired). This is a **clean parametric test of the theorem, NOT a bit-for-bit reproduction** of the original expert/cold γ-audit — consistent with the decision that the parametric run (non-centroidal by construction) is the de-circularization of record; the lost LLM runs are corroborating only. State this in results so it isn't mis-read as a failed reproduction.

## Self-check (could this ONLY confirm?)

No. Fixed below/above cells, raw monotonicity, fail-closed censored γ, persisted vectors/snapshots, and the independent N_half direction check can each produce a clean F1/F2/F3 failure without changing the hypothesis or re-running a favorable generator.

## Open questions — RESOLVED

1. *Runner + persistence format don't exist yet* → Stage 4 implements them in the reserved dir; the μ₀/GT/disruption constructions are frozen (D1–D4), so no init decision is deferred to run time.
2. *ε★ must be computed, not hard-coded* → resolved: canonical θ-cancelled form, computed from recorded D3 inputs (0.125), straddle asserted before any γ cell.
3. *μ₀ construction unresolved* → resolved: D1 freezes cold μ₀ (ratified by the source session); expert cell retired; the diagnosis-flagged gap is closed by specification.

## Freeze statement

D1–D4, the canonical ε★ form, the all-cold init, the retired confound, and the scope note are frozen. Hard build gates: (a) assert+persist `‖GT₁ − μ₀‖ > 0`; (b) compute ε★ and assert the grid straddles — STOP on failure. This design is run-ready; any change to a frozen item is a new design version requiring fresh review.

## Design review v2

| Check | Result | Review note |
|---|---|---|
| 1. Parametric, non-centroidal vectors; not LLM | PASS | `FactorVectorSampler` is the sole vector generator and samples around the generic 0.5 base without scorer or GT input. |
| 2. GT distinct from scorer μ | FAIL | D1 defines scorer `μ₀` as jittered `clip(0.5 + Uniform(-0.15,+0.15))`, while the oracle construction is based on its separate canonical prior; v2 never unambiguously defines whether `canonical_μ₀` means the jittered scorer tensor or the fixed 0.5 tensor. The `>0` assertion proves only inequality, not the claimed `GT₁ = μ₀ + ε_firm` geometry. |
| 3. θ-free γ primary; N_half secondary | PASS | `gamma_dist` is primary; `gamma_nhalf` is explicitly restricted to the F2 direction-agreement check. |
| 4. Persistence and re-openability | PASS | Vectors, centroid snapshots, trajectories, per-cell γ, and hashed manifest fields are specified. |
| 5. Real falsification and honest power reading | PASS | F1, F2, and F3 have independent failure paths, and the n=3 limitation plus inconclusive rule is explicit. |
| 6. Bias test: could it only produce γ>1? | PASS | Below-threshold cells can yield `gamma_dist < 1`; censoring, direction disagreement, and raw monotonicity failures are all reportable outcomes. |

**VERDICT: SEND BACK — define one unambiguous canonical tensor and displacement equation relative to the scorer’s jittered μ₀, including whether the oracle prior is fixed 0.5 or μ₀ itself; the current D1/D2 wording does not establish the claimed target geometry.**
