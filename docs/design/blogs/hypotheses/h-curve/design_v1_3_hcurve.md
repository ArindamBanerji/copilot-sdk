# H-CURVE parametric regen — design v1.3 (pre-registration addendum; frozen, run-ready)

Amends `design_v1.2.md`. The μ₀ diagnosis returned COLD μ₀ NOT FULLY SPECIFIED; the source session has now **ratified the four constructions** (D1–D4), so PR-5's precondition is satisfied by *specification* (a pinned, persisted choice — more authoritative than the half-documented legacy value, per "the code is a snapshot, not the touchstone"). This addendum is **run-ready**: no open gate remains except the runtime ε★-straddle assertion (which passes under D3).

In-repo home: `copilot-sdk/docs/design/blogs/hypotheses/h-curve/design_v1.3.md`. Everything passed in v1.0/v1.1/v1.2 stands; v1.3 pins the constructions v1.2 left to a decision.

---

## FROZEN CONSTRUCTIONS (D1–D4, ratified)

**D1 — cold μ₀.** `μ₀ = clip(0.5 + Uniform(−0.15, +0.15), 0, 1)`, i.i.d. per (category, action, factor), drawn from a **dedicated μ₀ RNG seeded `7 × run_seed`** (→ 294 / 861 / 5439 for run_seeds 42 / 123 / 777), distinct from the oracle RNG (seed 99) so μ₀ and GT never share a stream. This yields μ₀ ∈ [0.35, 0.65] — intentionally mediocre (not near GT, not near edges): the genuine cold-start condition Phase 1 must learn from.

**D2 — GT₁ ≠ μ₀.** Runner asserts and persists `‖GT₁ − μ₀‖_F > 0` per cell. **No minimum separation** — separation is governed by ε_firm (the experiment variable), not by μ₀. At ε=0.05 both GT and μ₀ sit near canonical *by design* (that is the below-threshold test); a minimum-separation floor would bias exactly the regime being probed.

**D3 — disruption config + tensor shape.** Canonical SOC values: **C = 6** categories, **A = 4** actions (escalate / investigate / suppress / monitor), **d = 6** factors (privileged_identity, asset_criticality, threat_intel, pattern_history, time_anomaly, device_trust) → tensor shape **(6, 4, 6) = 144**. `disrupted_categories = [0, 1]` (α_disrupt = 2/6), `‖Δ‖ = 0.25`, `θ = 0.85` (N_half only). ε★ = (α_disrupt·‖Δ‖)/(1 − α_disrupt) = (0.333·0.25)/0.667 = **0.125**. Grid straddles: 0.05 < 0.125 < 0.20 < 0.35.

**D4 — x-axis + transparency.** Report **ε_firm (configured)** as the x-axis; additionally log the **post-clip `‖GT₁ − prior‖_F`** as a secondary manifest column. The binary prediction needs only the monotonic ordering (0.05 < 0.20 < 0.35), which holds regardless of clipping.

## ε★ FORMULA — canonical form (record + upstream fix)

Use ε★ = **(α_disrupt · ‖Δ‖) / (1 − α_disrupt)** (θ-cancelled). The runner computes ε★ from the recorded D3 inputs with this form and asserts the straddle before any γ cell.

**Upstream documentation defect (log for cga v8, do NOT change this experiment).** `synthetic_data_generation_v2.md` states the pre-cancellation threshold as `ε★ = α·‖Δ‖·θ/(θ − (1−α))` and claims "≈ 0.128", but that formula evaluates to ≈ **0.387** with these inputs — a transcription error. The correct θ-cancelled form gives 0.125 and matches math_synopsis's "θ cancels in correct derivation." This does not affect the experiment (the binary test is on the ε grid, not the formula), but the source doc must be corrected in the next version.

## Freeze statement

D1–D4 and the canonical ε★ form are frozen. The only remaining runtime gate is PR-3's ε★-straddle assertion, which passes under D3. Stage 4 executes `design_v1.md` as amended by v1.1 → v1.2 → v1.3 (v1.3 authoritative on the constructions). This addendum is run-ready. Scope wall unchanged: model validity / EXP-G1 out of scope.
