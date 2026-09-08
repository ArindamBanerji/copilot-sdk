# VLD v13 Addendum — Decision Geometry (merge into v12)

**What this adds:** §3E (Decision Geometry), corrections to §3B/§3D/§3A, E0 redesign,
and a v13 LLM judge prompt (Appendix G). This is the theoretical contribution that
reframes VLD from "iterative depth" to "deliberation over folded decision boundaries."

**Why this is needed:** The pilot (§3A) showed Δ_trajectory = 0 — the loop adds no value
over single-shot evidence acquisition. The natural conclusion is "the loop doesn't work."
But that conclusion assumes decision boundaries are geometrically simple. If the boundary
is *folded* — conditional dimensions change which side you're on — the loop's value is
precisely in navigating the fold. The pilot didn't test folded boundaries. This section
develops the formalism.

---

## §3E. Decision Geometry — why the loop's value depends on boundary shape, not chain length

### The core distinction

**Decision complexity** = how many steps/dependencies a decision involves (graph-theoretic).
Predicts: long chains → VLD helps. But the pilot shows Δ_trajectory = 0 on 3-hop chains.
Wrong frame.

**Decision geometry** = the shape of the decision boundary relative to the evidence
structure (geometric). Predicts: VLD helps when the boundary is *folded* — when
intermediate re-scoring changes the traversal path. Right frame.

CI is already geometric: a decision is a point `v ∈ R^d`, the centroid tensor `μ` defines
a Voronoi partition, the scorer's output = which Voronoi cell `v` falls in. A "hard"
decision sits near a Voronoi boundary.

### Three boundary geometries

**Simple boundary.** The Voronoi boundary between action A and action B is a flat
hyperplane in the *revealed subspace* — the dimensions that evidence makes visible. Once
the decisive dimensions are revealed (by any mechanism — Ψ-once, breadth, or the loop),
the decision resolves unambiguously. The damped iterate converges to the same point
regardless of traversal path.

→ *Ψ-once suffices. VLD adds no value. Δ_trajectory = 0 by construction.*

**Folded boundary.** The boundary between A and B *folds* in factor space — some decisive
dimensions are **conditionally visible**. Dimension 5 (supplier capacity) is only
meaningful after resolving dimension 3 (BOM dependency), because the *relevant supplier*
depends on which component you're sourcing, which depends on the production schedule.

In geometric terms: the decision boundary in the full space projects to a *fold* in the
observable subspace. The same point in the visible dimensions maps to *different sides* of
the boundary depending on the hidden conditional dimensions. Crucially: **which conditional
dimensions to reveal depends on the current score** — the intermediate `a*(v_t)` determines
which branch of the fold to explore.

→ *VLD's iterative re-scoring matters. Each pass resolves a conditional dimension, which
changes which branch of the fold applies, which changes what to read next. Ψ-once reads
the wrong conditional branch ~50% of the time (it picks without knowing which fold it's on).
Δ_trajectory > 0 when the boundary is folded.*

**Entangled boundary.** Multiple Voronoi boundaries interact — a decision near the A/B
boundary also sits near the C/D boundary in correlated factor dimensions. Moving `v` to
resolve one boundary shifts the decision relative to the other. Portfolio-correlated
trading decisions exhibit this: the "buy AAPL" decision interacts with the "hedge SPY"
decision through shared market factors.

→ *The loop's value is in navigating the entanglement — resolving the A/B boundary while
not inadvertently crossing the C/D boundary. This requires awareness of the joint
Voronoi structure, not just the nearest boundary.*

### Reinterpretation of the pilot

The pilot's Δ_trajectory = 0 is a *geometric prediction*, not a negative result:

The synthetic chains have **clean single boundaries** — the decisive dimensions, once
revealed, unambiguously resolve the boundary. The boundary is a flat hyperplane in the
revealed subspace. There is no fold: knowing what to read next doesn't depend on the
current score. The damped iterate converges to the final evidence extraction because
the path through the space is unique.

For Δ_trajectory > 0, the planted effect must have a boundary with **curvature in the
traversal direction** — where `a*(v_t)` at pass t determines which evidence branch to
follow at pass t+1. The current E0 does not plant such a boundary.

### m is a geometric measure

Redefine m for §3B:

`m` = the fraction of hard-tail decisions where the decision boundary is **folded or
entangled** relative to the evidence graph's traversal structure — where the optimal
next evidence read depends on the current decision state `a*(v_t)`, not just on the
initial observation.

This is NOT the same as "multi-hop fraction" (complexity). A 5-hop chain with a simple
boundary has m = 0 (Ψ-once resolves it). A 2-hop chain with a folded boundary has
m > 0 (the second hop depends on the first read's effect on the score).

### m varies by deployment geometry, not by copilot

The v12 per-copilot table (SOC moderate, Trading ≈0) reflects the **demo configuration's
decision topology**, not the copilot's architectural limit:

| Deployment | Boundary geometry | m |
|---|---|---|
| Trading: independent trades | Simple — each trade resolves in the same factor subspace | ≈0 |
| Trading: multi-strategy portfolio | Entangled — portfolio constraints create correlated boundaries | >>0 |
| Purchasing: independent POs | Simple | ≈0 |
| Purchasing: manufacturing BOM | Folded — component sourcing depends on production schedule | >>0 |
| SOC: independent phishing alerts | Simple | low |
| SOC: coordinated APT campaign | Entangled — alert A's classification depends on B, C, D | high |
| S2P: simple invoices | Simple | low |
| S2P: complex supply chain | Folded — invoice matching depends on upstream PO/GR chain | moderate-high |

The same CompoundingScorer, the same conservation law, the same factor vectors — the
difference is the *topology of the customer's decision flow*, which determines whether
the Voronoi boundaries are simple, folded, or entangled.

### Connections to existing work

Decision geometry as a concept touches several established fields:

- **Information geometry** (Amari, 1985): Fisher information metric on statistical
  manifolds — regions of high curvature in the score distribution are exactly where
  traversal direction matters.
- **Active learning / value of information** (Lindley 1956, MacKay 1992): the optimal
  next observation depends on the current belief state — the geometric framing of
  this is well-established but not applied to Voronoi-partitioned judgment graphs.
- **Voronoi diagram sensitivity** (computational geometry): the robustness of a
  Voronoi classification to perturbation is a function of boundary geometry — this
  literature characterizes exactly the "margin" concept CI already uses.
- **Manifold learning** (Tenenbaum 2000, Roweis 2000): if decisions lie on a
  low-dimensional manifold in R^d, the effective boundary geometry depends on the
  manifold's curvature, not the ambient dimension.
- **Conditional computation / adaptive inference** (Graves 2016, Dehghani 2018):
  halting based on intermediate confidence — related but on neural architectures,
  not reified judgment graphs.

**CI's specific construction may be novel:** decision geometry over a *reified judgment
graph* where (a) the Voronoi structure is *learned from verified outcomes* (not from
training data), (b) the evidence graph provides *traversal paths* through factor space
(not just a feature extractor), and (c) conservation *bounds* the permitted traversal
region (not just a cost). The combination of learned-Voronoi + graph-traversal + bounded-
deliberation appears not to have a direct precedent. **This needs validation — search
the literature before claiming novelty.**

### Implications for the experiment program

**E0 redesign (critical).** The positive control must plant a **folded boundary**, not
just a long chain:

Current E0: surface node → 3 decisive chain nodes → resolve. The boundary is flat in
the revealed subspace. Δ_trajectory = 0 by construction.

Proposed E0: surface node → first chain node reveals dimension subset D1 AND a **branch
selector** (conditioned on the score after D1, which of two chain-2 nodes to follow) →
chain-2a reveals dimensions D2a, chain-2b reveals dimensions D2b → only one branch
resolves the boundary. The boundary is **folded**: in the D1 subspace alone, the case
is still ambiguous because both branches project to the same region. Intermediate
rescoring (`a*(v_t)` after admitting D1) determines which branch to follow. Ψ-once
picks a random branch (50% chance of the right one). VLD follows the score-conditioned
branch.

If Δ_trajectory = 0 even with a folded boundary → the loop genuinely doesn't help and
the geometry story is wrong. If Δ_trajectory > 0 → the geometry story is right, and the
loop's value is proportional to the fraction of folded/entangled boundaries in real data.

**E3 redesign.** The hard-tail definition should include a geometric criterion:
not just "low margin" (numerical difficulty) but "conditioned on which fold the
decision is on" (geometric difficulty). The routing signal that predicts VLD benefit
is the **geometric complexity of the boundary**, not the margin.

---

## Corrections to existing sections

### §3B correction
Add after point 2:

"**Sharpening (v13):** m is a *geometric* measure, not a complexity count. A decision with
a long dependency chain but a flat boundary has m = 0 (one read resolves it). A decision
with a short chain but a folded boundary has m > 0 (the second read depends on the first
read's effect on the score). See §3E. The routing signal that predicts VLD benefit is
boundary geometry, and margin/σ are proxies for it — good proxies when folds correlate
with ambiguity, bad when they don't."

### §3D correction
Replace "SOC and S2P have m; Trading/Purchasing ≈0" framing with:

"m varies by **deployment geometry**, not by copilot type. The demo configuration shows
m ≈ 0 for Trading/Purchasing because the demo's decision topology is simple. The same
copilot deployed at a multi-strategy fund or a manufacturing supply chain would show
m >> 0 because the customer's decision flow creates folded/entangled boundaries. The
entity wiring gap (Tier 2 in v12) is what prevents the demo from exhibiting this geometry
— it is engineering, not research."

### §3A pilot reinterpretation
Add after the "Go/no-go implication":

"**Geometric reinterpretation (v13):** Δ_trajectory = 0 reflects geometrically simple
planted boundaries (flat hyperplanes in the revealed subspace), not 'the loop doesn't
work.' The decisive E3 test is whether folded boundaries — where argmin changes during
traversal — produce Δ_trajectory > 0. See §3E."

---

## Appendix G — LLM Judge Prompt (v13)

### Purpose
You are reviewing v13 of the VLD-Depth memo. The new material is §3E (Decision Geometry)
and its implications for the experiment design. Read §3E, §3A (pilot), §3C (retrieval
geometry), and Appendix E (P1 report) before responding.

### What to respond to

**J1 — Is the simple/folded/entangled boundary taxonomy correct and exhaustive?**
(a) Do folded boundaries exist in real decision domains? Give examples beyond the ones
    listed.
(b) Are there boundary geometries not captured by {simple, folded, entangled}?
(c) Is the distinction between "folded" and "entangled" sharp enough, or do they blur?

**J2 — Does "decision geometry" have precedent?**
(a) Has this specific construction (learned-Voronoi + graph-traversal + bounded-
    deliberation) been studied?
(b) Which of the cited connections (Amari, active learning, Voronoi sensitivity) is
    most relevant?
(c) Are there uncited literatures that directly address this? (mechanism design,
    multi-armed bandits with geometric structure, geometric active learning?)

**J3 — Does the folded-boundary E0 redesign correctly isolate the geometry effect?**
(a) Does the branch-selector mechanism (score after D1 determines which chain-2 to
    follow) actually create a fold, or is it just a longer chain?
(b) What is the minimum fold complexity needed to produce Δ_trajectory > 0?
(c) Could breadth accidentally resolve folded boundaries (by reading both branches)?

**J4 — Is "m varies by deployment geometry, not copilot" the right product framing?**
(a) Is this too abstract for buyers?
(b) Does it weaken the per-copilot value story?
(c) Is there a concrete way to help a customer estimate their m before deployment?

**J5 — Does this reframe change the program's economics?**
(a) If VLD's value is concentrated at complex deployments, and simple deployments get
    Ψ-once, is VLD still worth building as a platform feature?
(b) Or should VLD be a premium tier / add-on?
(c) What fraction of the target market has folded-boundary decision flows?

### Format
Answer by ID (J1–J5). Distinguish facts from opinions. One paragraph of J1 or J3 is
more valuable than a full J5 essay.
