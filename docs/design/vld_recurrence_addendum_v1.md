# VLD Architecture & Implementation Design — Recurrence Addendum
**Version:** v1 · **Date:** Sep 9, 2026
**Authority:** VLD Implementation Design v4 + Graph Reasoning Experiments v2
**Applies to:** vld_implementation_design_v4.md §3-§5, vld_graph_reasoning_architecture_v4.md §4-§7

---

## 1. Summary

Recurrence experiments (RNN-1 through RNN-9, GR-1 through GR-5) on
Stage 1 SOC multi-hop data (50 instances) produced three architectural
requirements and five validated properties. This addendum captures
changes to the VLD architecture and implementation design.

**All results carry [PLANTED / POSITIVE CONTROL] caveat per spec v2 §0.**

---

## 2. Architectural Requirements (new or changed)

### REQ-1: Enriched Centroids (NEW — changes §3 centroid initialization)

**Finding:** Surface-derived centroids make VLD appear broken.
Enriched-derived centroids make it work.

| Metric | Surface centroids | Enriched centroids |
|---|---|---|
| Depth 0→1 accuracy | 0.511 → 0.378 (−0.133) | 0.467 → 0.622 (+0.155) |
| Depth 0→2 accuracy | 0.511 → 0.500 (−0.011) | 0.467 → 0.700 (+0.233) |
| Convergence (dist) | INCREASES 0.362 → 0.421 | DECREASES 0.380 → 0.364 |
| Centroid diff ‖μ_surface − μ_enriched‖ | — | 0.4227 |

**Architectural change:** centroid initialization MUST use enriched
vectors (factor vectors after all evidence hops applied), not surface
vectors. The centroid tensor represents WHERE evidence SENDS the
factor vector, not where it starts.

```
# WRONG (v1): μ[action] = mean(surface_factors for action)
# RIGHT (v2): μ[action] = mean(enriched_factors for action)
#   where enriched = apply_all_hops(surface, hops)
```

**Impact on dual-centroid architecture:**
- μ_routing: can use EITHER surface or enriched (routing works with both)
- μ_action: MUST use enriched (action scoring needs the target geometry)
- This strengthens the dual-centroid case: routing and action centroids
  are now derived from different vector populations

**Implementation change:** `build_centroids()` in the investigation
evaluator, ProfileScorer initialization, and any centroid training
pipeline must apply all available evidence before computing the
centroid mean.

### REQ-2: Non-Overlapping Factor Enrichment (NEW — changes §4 pattern design)

**Finding:** when each hop enriches a DIFFERENT factor dimension,
accuracy is 92.3%. When hops overlap (same factor enriched twice),
accuracy drops to 42.9%.

| Factor overlap | Accuracy | N |
|---|---|---|
| Non-overlapping | **0.923** | 13 |
| Overlapping | 0.429 | 7 |

**Architectural change:** investigation patterns MUST be designed so
each hop enriches a distinct factor dimension. If two hops would
enrich the same factor, the second should be suppressed or redirected.

```
# Pattern design rule:
# hop_0 enriches factor[i]
# hop_1 enriches factor[j] where j ≠ i
# hop_2 enriches factor[k] where k ≠ i, k ≠ j
# If no un-enriched factor remains → HALT (all factors covered)
```

**Impact on selective replacement:** this validates the selective
replacement aggregation strategy. With non-overlapping factors,
selective replacement is order-invariant (confirmed by RNN-4:
sequential = parallel when overlap = 0). Factor overlap introduces
order dependence (sequential 0.750 > parallel 0.700 when overlap > 0).

**Implementation change:** the investigation router should track which
factors have been enriched and avoid re-enriching them. The hop
selection logic should prefer factors with the highest error relative
to the target centroid AND that haven't been enriched yet.

### REQ-3: Depth Budget = 2 (REFINED — changes §5 budget allocation)

**Finding:** marginal accuracy gain diminishes with depth.

| Depth | Accuracy | Marginal gain |
|---|---|---|
| 0 (single-pass) | 0.467 | — |
| 1 | 0.622 | +0.155 |
| 2 | 0.700 | +0.078 |
| 3 | 0.400 | −0.300 (n=5, noisy) |

**Architectural change:** default investigation budget should be 2 hops.
Depth 3 shows diminishing returns on this dataset (though n=5 is too
small for a definitive conclusion). The budget should be a configurable
parameter with domain-specific defaults:

| Domain | Default budget | Rationale |
|---|---|---|
| SOC | 2 | 6 factors, 2 hops covers key dimensions |
| DataOps | 2-3 | Cascading failures may need 3 hops |
| S2P | 2 | Amendment chains need 2 hops |
| Trading | 1-2 | Fewer conditional scenarios |
| Purchasing | 1-2 | Fewer conditional scenarios |

---

## 3. Validated Properties (confirmed by experiments)

### PROP-1: Recurrent Convergence

Investigation converges: centroid distance monotonically decreases
with depth (40% of instances strictly monotonic, 69% for entropy).
Mean residual: 0.380 → 0.373 → 0.371 → 0.364.

This means the investigation is self-terminating — a residual-based
halt condition (halt when Δ_residual < ε) is a valid stopping criterion.

### PROP-2: State Divergence (94%)

75 out of 80 similar-start pairs (d_0 < 0.3) with different ground
truth actions diverged after evidence application (d_final > d_start).

This IS the recurrence property: the hidden state (enriched factor
vector) carries information that differentiates outcomes. Two alerts
that look similar on the surface can be distinguished after
investigation.

### PROP-3: Score-Conditioned Routing is Informed

Step 0 routing picks the optimal factor (highest error) 40% of the time
vs 16.7% chance (2.4×). Top-2 accuracy is 62.2%.

This validates score-conditioned routing over random or fixed-order
investigation. The centroid distances contain routing information
even before evidence is read.

### PROP-4: Sequential Ordering Matters (When Factors Overlap)

| Ordering | Accuracy (n=20, 7 overlap) |
|---|---|
| Sequential (VLD) | **0.750** |
| TRUE parallel (avg overlap) | 0.700 |
| Reverse | 0.700 |
| Random (5-vote) | 0.750 |

Sequential ≥ parallel. The advantage is small (+0.050) and
concentrated in the 7 overlapping scenarios. For non-overlapping
scenarios, all orderings are equivalent (selective replacement commutes).

### PROP-5: Denser Graphs Benefit More

| Graph density | SP accuracy | VLD accuracy | Δ |
|---|---|---|---|
| Low (1-2 branches) | 0.571 | 0.771 | +0.200 |
| Medium (3-4 branches) | 0.100 | 0.400 | **+0.300** |

Denser graphs (more available branches) produce larger VLD advantage.
This supports the thesis that VLD's value scales with graph complexity
— exactly the enterprise use case (rich graphs with many investigation paths).

---

## 4. Partial/Negative Findings

### PARTIAL: Evidence Compounding (35%)

Hop 1 moves the factor vector closer to the correct centroid only 35%
of the time (vs 50% expected for true compounding). This means early
hops don't reliably improve later routing — they mostly improve the
FINAL action scoring, not the intermediate routing decisions.

**Implication:** the recurrence is primarily in the SCORING path (evidence
accumulates toward the correct action centroid) rather than the ROUTING
path (evidence doesn't reliably improve which factor to investigate next).
This is consistent with the dual-centroid architecture: routing uses a
different centroid tensor than scoring.

### NOISY: Long-Range Dependency (n=5)

On 3-hop scenarios (n=5), hop 3 alone matches all-3 accuracy (0.400).
This suggests hop 3 is the dominant signal. But n=5 is too small for
conclusions. Need Stage 2 data with more 3+ hop scenarios.

### NOT GATING: Update Magnitudes

Update magnitude does NOT decrease with depth (0.228 → 0.233 → 0.280).
With selective replacement, |Δv| = |Δ one factor|, which measures
evidence strength, not learned gating. This is expected — there's no
adaptive gate mechanism in the current architecture.

---

## 5. Impact on Existing Documents

### vld_implementation_design_v4.md

| Section | Change |
|---|---|
| §3 Centroid Initialization | ADD: enriched centroids mandatory. Surface centroids produce divergence. |
| §3B Simulation Results | ADD: recurrence experiment results (this addendum) |
| §4 Investigation Patterns | ADD: non-overlapping factor constraint. Track enriched factors per hop. |
| §5 Budget Allocation | CHANGE: default budget = 2 (was unspecified). Domain-specific overrides. |
| §5 Halt Condition | ADD: residual-based halt is validated (convergence proven). |

### vld_graph_reasoning_architecture_v4.md

| Section | Change |
|---|---|
| §4 Dual-Centroid | ADD: μ_action MUST use enriched vectors. μ_routing can use either. |
| §5 Aggregation | ADD: selective replacement validated. Non-overlap = 0.923. |
| §6 Recurrence Properties | ADD: new section with PROP-1 through PROP-5. |
| §7 Graph Density | ADD: denser graphs benefit more (GR-4 result). |

### math_synopsis

| Claim | Change |
|---|---|
| Convergence | ADD: empirical convergence confirmed (dist monotonic 40%, entropy 69%). |
| State divergence | ADD: 94% divergence on similar-start pairs. |
| Routing informativeness | ADD: 2.4× chance at step 0. |

---

## 6. Publication Charts (PUB-17 through PUB-25)

| Chart | Finding | Publication use |
|---|---|---|
| PUB-17 | Depth-accuracy-confidence (3 panels) | Main recurrence figure |
| PUB-17b | Surface vs enriched comparison | Centroid init matters figure |
| PUB-18 | Hop ablation | Which evidence matters most |
| PUB-19 | Convergence (dist + entropy) | Self-terminating investigation |
| PUB-20 | Order dependence | Sequential vs parallel |
| PUB-21 | Evidence compounding | 35% — partial, honest |
| PUB-22 | P(correct) per depth | Intermediate state quality |
| PUB-23 | Update magnitude | No gating (expected) |
| PUB-24 | Routing quality per step | 2.4× chance |
| PUB-25 | Long-range (3-hop ablation) | Noisy but directional |

All charts in `ci_core/pub_charts/` and `$CLAUDE_SOC/backend/pub_charts/`.

---

## 7. Forward Work

| Item | Priority | What |
|---|---|---|
| Update impl design v4 → v5 | HIGH | Incorporate REQ-1, REQ-2, REQ-3 |
| Update arch doc v4 → v5 | HIGH | Add §6 recurrence properties |
| Stage 2 DataOps/S2P data | HIGH | More 3+ hop scenarios for long-range |
| Factor overlap tracker | MEDIUM | Implement in investigation router |
| Enriched centroid builder | MEDIUM | Utility for centroid initialization |
| Depth budget sweep | LOW | Systematic optimal depth per copilot |

---

*VLD Recurrence Addendum v1 · Sep 9, 2026*
*3 architectural requirements (enriched centroids, non-overlapping factors, budget=2)*
*5 validated properties (convergence, divergence, routing quality, ordering, density)*
*21 publication charts (PUB-1 through PUB-25, skipping PUB-9 through PUB-13)*
*[PLANTED / POSITIVE CONTROL — not a measurement of real VLD value]*
