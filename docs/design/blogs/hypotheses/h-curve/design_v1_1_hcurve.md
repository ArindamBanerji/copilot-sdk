# H-CURVE parametric regen — design v1.1 (pre-registration addendum; frozen before build)

Amends `design_v1.md`. Resolves the three open questions from the Stage-3 review — two of them hard gates — in the pre-registration direction, and adds one results-write-up note. Frozen items may not be re-opened during the build; changing one requires a new design version and a fresh Stage-3 review. Everything in `design_v1.md` that the review passed stands (parametric non-centroidal generation, θ-free distance γ as primary, N_half only for F2, fail-closed censoring, full persistence + hashed manifest, raw-trajectory monotonicity, honest 3-seed reading).

In-repo home: `copilot-sdk/docs/design/blogs/hypotheses/h-curve/design_v1.1.md`

---

## GATE-1 (frozen) — ε=0.35 initialization + authoritative μ₀ factory

**PR-1 — ε=0.35 initialization mode is frozen NOW, before any run.** The ε=0.05 case uses expert init (`GT_1 ± 0.05`); ε=0.20 uses cold init (`uniform(0.5) ± 0.15`). The ε=0.35 case uses **cold init (`uniform(0.5) ± 0.15`)** — same as ε=0.20 — so that the two above-threshold cells (0.20, 0.35) share an initialization and differ only in firm mismatch. This is recorded in the manifest as the pre-run decision; it is not inferred after execution. Rationale: freezing it now removes a post-hoc degree of freedom, and matching 0.20's init makes 0.20→0.35 a clean single-variable (ε-only) contrast on the above-threshold side.

**PR-2 — the μ₀ construction must be resolved from the authoritative experiment setup, or the run STOPS.** The review found no single current factory exposing the canonical `μ₀` construction for the expert and cold cases. Before Stage 4 runs, the runner must resolve the exact `μ₀` (expert and cold) from the authoritative experiment configuration and record it — construction rule, displacement direction, and the resulting `GT_1 = canonical_μ₀ + ε_firm` — in the manifest. **If it cannot be resolved authoritatively, the build STOPS** (the design's own instinct: never silently substitute an initialization). No default, no guess.

## GATE-2 (frozen) — ε★ computed from the recorded disruption config, and the ε grid must straddle it

**PR-3 — ε★ is computed, never hard-coded, and the grid is checked to straddle it before the run.** The headline ε★ ≈ 0.125 is a rounded value that depends on disruption magnitude ‖Δ‖ and disrupted-category fraction α_disrupt. The runner computes ε★ from the *recorded* disruption inputs in the manifest (ε★ = α_disrupt·‖Δ‖ / (1 − α_disrupt)), then **asserts the straddle before executing the γ cells**: ε=0.05 must fall *below* the computed ε★, and ε=0.20 and ε=0.35 *above* it. If the computed ε★ does not cleanly straddle the grid (e.g. 0.05 is not below it), the run **STOPS** and the ε grid (or the disruption config) is adjusted and re-frozen in a new design version — the grid is never adjusted after seeing γ. The binary prediction (γ_dist<1 below ε★, γ_dist>1 above) is only meaningful under a confirmed straddle.

## GATE-3 (sequencing, not a blocker) — runner + persistence approved as part of Stage 4

**PR-4 — the Stage-4 runner and persistence format are new code and get reviewed with the run.** The runner is implemented in the reserved experiment dir (`graph-attention-engine-v50/experiments/h_curve_parametric_regen/`); its μ₀ construction (per PR-2), its ε★ computation + straddle assertion (per PR-3), and the manifest/hash layout are confirmed before execution, not discovered mid-run. Persistence must satisfy the design_v1 property: an analyst can recompute both γ values and all non-centroidality summaries from the artifacts *without importing the scorer*.

## Results-write-up note (frozen instruction, not a config change)

**SL-1 — the below/above cells are not a single-variable contrast across the whole grid.** ε=0.05 uses expert init while ε=0.20/0.35 use cold init, so the below-threshold vs above-threshold comparison differs in *init mode as well as ε*. This is faithful to the documented original config and is correct for reproduction — but the results doc must state it explicitly, so the γ difference across the threshold is not read as purely ε-driven. The 0.20→0.35 contrast (same init, per PR-1) is the clean ε-only comparison; cite that as the within-above-threshold check.

## Freeze statement

PR-1, PR-3, and SL-1 are fixed as of this addendum. PR-2 and the PR-3 straddle assertion are **hard build gates**: the Stage-4 build must halt if μ₀ cannot be authoritatively resolved or if the computed ε★ does not straddle the ε grid. Stage 4 executes `design_v1.md` as amended here. Any change to a frozen item is a new design version requiring a fresh Stage-3 review — not a build-time decision. Scope wall unchanged: model validity / EXP-G1 remains out of scope.
