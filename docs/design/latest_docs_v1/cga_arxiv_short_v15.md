**Cross-Graph Attention: A Governed Math Engine That Reshapes Decisions From Verified Outcomes**

Arindam Banerji, PhD | Dakshineshwari LLC, Santa Clara, CA | banerji.arindam@gmail.com

# **Abstract**

Graph engineering — building a knowledge graph to *retrieve* answers, and wiring a graph of agents to
*route* work — has moved from research frontier to documented recipe. Both treat the graph as structure:
something to read or to route. This paper specifies a third operation — *reshape* — as a **hardened math
engine**: a small set of typed objects, a fixed set of pure operations over them, a set of invariants that
hold by construction, and a certification discipline that assigns every output a tier by *what generated its
correctness signal*. A graph whose decision geometry reshapes from verified outcomes under this engine is
safe (the decision rule is written by no operation), fast (a decision is a nearest-prototype distance, not a
model call), independent of the enrichment that populates it (a σ⊥μ separation), and produces a fourth
cognitive-architecture type — judgment memory — that no read or route can derive.

The decision kernel is the first evidence for the engine's `score` operation: on identical data and identical
centroids, L2 distance outperforms dot product by **36.89 percentage points** (61.00% → 97.89%) for scoring
on bounded [0,1] features (EXP-C1) — a magnitude-confounding effect that afflicts any scorer on pre-computed
bounded features, and the largest single-variable effect in a ~194-experiment record. Zero-learning accuracy
is 90.6% with a four-action space and no training data; realistic deployment climbs 71.7% → 78.9% over 1,000
verified decisions. A three-layer conservation gate (absolute floor, relative trigger, and a rate detector for sudden drops) governs when the engine may act, with per-threat-model detection at 100%/100%/100%/57% (0% FPR, JM apparatus); a re-convergence
property (γ > 1 ⇔ ε_firm > 0.125, four proof paths) says accumulated geometry re-calibrates faster after a
shock; and cumulative advantage over a frozen twin compounds super-linearly (c = 1.387, 95% CI [1.308, 1.477], measured, JM apparatus).

We add four results that the engine's certification discipline organizes. **(1)** A single investigation
produces four readouts — which evidence to acquire, how much, a better action, and a calibrated confidence —
and the confidence readout is carried by the investigation trajectory: an ablation drops its discrimination
to AUC 0.642 (below a 0.650 population baseline) when trajectory features are removed. **(2)** The compounded
routing advantage is firm-specific and non-transferable: a competitor learning on a different firm's stream
never reaches parity (routing gap 19.6 ± 5.4 pp SOC, 0/5 seeds). **(3)** Reinforcement learning controls the
enrichment budget deployably and safely (+6.5–6.8 points at fewer reads, safe at λ=0) while never selecting
the action. **(4)** The engine's certification rule forbids an LLM-judged correctness signal, and the
measured cost of violating it — an LLM judge agrees with ground truth ~12% of the time on
investigation-dependent decisions versus ~76% for the geometry-derived check — is the bright line that
separates measuring the engine from measuring the judge.

Grounding is explicit throughout: results are tagged by the tier of their correctness signal — by
construction, geometry-derived, real-component, simulated, or verified-pilot — and magnitude on a firm's
live decisions is a pilot measurement, never synthesized. Code and data: github.com/ArindamBanerji/
cross-graph-experiments.

**Keywords:** graph-native reasoning, decision geometry, distance-kernel attention, conservation law,
judgment memory, verified-outcome learning, certification tiers, enterprise AI.

---

# **1. Introduction — read, route, or reshape**

Enterprise AI systems make decisions one at a time and, overwhelmingly, do not get better at them. The
system that triages alert one triages alert ten-thousand with identical logic; hundreds of verified outcomes
accumulate and none writes back. MIT's *State of AI in Business 2025* attributes 95% of enterprise GenAI
pilots delivering no measurable return not to model quality but to a *learning gap* — tools that demo well
and never improve.

Two operations now go by "graph engineering," and both leave that gap open. A **knowledge graph you *read***
retrieves a cited answer; it returns what is stored, and is blindest where there is no precedent to retrieve.
A **graph of agents you *route*** dispatches work between nodes; it rearranges who does the work, not how the
next decision is made. Both treat the graph as structure — the argument becomes *whose graph, which
topology* — and neither changes what a decision *is*.

This paper is about the third operation. A graph you ***reshape*** is one whose decision geometry is changed
by the verified outcomes of its own decisions: the decision is a geometric distance on the graph (not a
model's guess), a human-verified outcome moves that geometry, and the next decision reads the changed
surface. Read and route are structure; **reshape is judgment — the only one that compounds.**

**Why the kernel matters, and why it is only the beginning.** The single most consequential design choice in
a reshape engine is the *similarity kernel* by which a decision is scored. Exporting the dot product from
transformer attention to enterprise feature scoring is a category error, because the dot product's validity
rests on representation learning that pre-computed bounded features do not have. On our data the cost is
**36.89 percentage points** (dot product 61.00% → L2 distance 97.89%, EXP-C1) — the largest single-variable
effect we measured, from changing one operation on identical data. *(A worked example: a SOC alert with
device_trust = 0.90 against a centroid at 0.88 contributes 0.90×0.88 = 0.792 under dot product — dominating
the score despite carrying almost no discriminative information — but (0.90−0.88)² = 0.0004 under L2, near
zero, so the discriminative factors decide. §3.)* But the kernel is one operation of a larger machine. The
rest of this paper specifies that machine — the **math engine** — as objects, operations, invariants, and a
certification discipline, because the kernel finding is only as trustworthy as the engine that certifies it.

**Why an enterprise should care, in one line per stakeholder.** For the firm that *runs* AI: a tool worth
more every quarter instead of the same forever, reasoning on top of the systems it already owns. For the
architect who *builds* it: the defensible layer is no longer the model or the graph — both commoditizing —
but the governed engine that compounds judgment on top, and it is small enough to audit. For the risk owner
who must *approve* it: the decision rule is written by no operation in the engine (§2.3, I1) — the system can
compound aggressively while the procedure the firm signed off on stays fixed, provably.

The contribution of this paper is to make that machine precise enough to be both approved and reproduced.
The next section specifies it whole.

---

# **2. The Math Engine**

*This section specifies the reshape operation as a hardened engine — the backbone of the paper. Read the
first four subsections (§2.0–§2.1) for the whole machine in intuition; the operation contracts (§2.2),
invariants (§2.3), and certification discipline (§2.4) give the formal depth. Every later section is either
evidence for an operation here or a property of the engine run over time.*

## **2.0 The organizing idea: chain of custody**

A math engine is **hardened** when every number it emits carries a complete chain of custody:

> **object read → operation applied → invariant that protected it → tier that certifies it.**

Nothing the engine outputs may skip a link. The four layers below are the four links: **state** (the
objects), **operations** (the pure transforms), **invariants** (what holds by construction), and
**certification** (how each output is known to be right). This chain is what turns "the system learns" from a
claim into an auditable property — and what lets a single decision be followed end to end:

> *A SOC alert arrives: a privileged service account issued a bulk device-management command. The engine
> reads it as a factor vector v (state). It scores nearest to "escalate" but by a thin margin — the decision
> sits near a boundary (operations). So it routes to the next decisive evidence — the account's recent role
> change — enriches, and re-scores: "escalate" is now decisive. The decision rule never changed while this
> happened, only the evidence did (invariant I1). An analyst later confirms the escalation; the update rule
> nudges the "escalate" prototype toward this alert (operations) — allowed only because the confirmation is a
> verified human outcome, not the engine's own guess (invariant I5). And "escalate" is certified
> geometry-derived: real as a mechanism, its live magnitude still a pilot measurement (certification).*

That one alert touches every object, three operations, two invariants, and one tier. A hardened engine is one
where you can always draw that chain. [FIGURE | engine_chain_of_custody | infographic: the four layers as a
left-to-right chain, the SOC alert traced through each — object→operation→invariant→tier | NEW]

## **2.1 State — the objects, and who may write them**

The engine's memory is a small, typed, inspectable set of objects, split into **evolving state** (what it
*learns*) and **configured parameters** (what it is *set up with*). A risk owner's first question — *what
changes after I approve this?* — is answered in one column: only μ, K, σ, R, G move; everything else is fixed
at approval. **Low dimensionality is load-bearing, not a limitation:** a single copilot is sized by one
triple (n_c categories × n_a actions × d factors) — SOC 6×4×6 = 144 prototypes, S2P 5×5×8, Trading 5×4×10 —
small enough that every object is auditable, every operation is cheap, and a few hundred verified outcomes
move the geometry. The "is this even AI at scale?" objection terminates here: the small geometry is the
mechanism, not the shortfall.

| Object | Lifecycle | Meaning | **Who may write it** |
|---|---|---|---|
| μ — centroids | **evolving** | prototypes of a good decision per (category, action) | the update rule only |
| K — routing memory | **evolving** | which evidence proved decisive, per category | the update rule only |
| σ — noise fingerprint | **evolving** | per-factor outcome-conditioned variance (a diagnostic) | the diagnostic only |
| R — verified record | **growing** (append-only, hash-chained) | the outcomes that certify everything | verification only |
| G — graphs | **refreshed** | evidence substrate (four clocks) | ingestion / enrichment |
| DK — scoring metric | **configured** | per-factor weights (L2 identity = default) | calibration only |
| τ, θ_min, ρ, η, ε | **configured** | temperature; conservation floor; penalty ratio; learning + blend rates | fixed at approval |
| **a\*( · ) — decision form** | **fixed** | `argmin` over μ under DK | **NOBODY — architectural invariant** |

Two rows are the whole safety story. **`a*` has no write lane:** the rule that turns a factor vector into an
action is written by no operation — it is what a risk owner approves and what no learning layer can reach.
And **σ is diagnostic, not a scoring weight:** it measures where factors are signal versus noise — surfacing
the *trust trap*, the factor a team trusts most that turns out to be its noisiest predictor — but it is
walled off from DK, the metric that actually scores (why walled off, not merely unused: I2, §2.3). *Example:*
when the analyst confirms the SOC escalation, exactly one cell of μ moves; DK, τ, ρ, and a* are untouched — a
single nameable, auditable, reversible change.

## **2.2 Operations — the pure transforms**

Each operation is a function with a signature and a contract, defined independent of the loop that calls it;
the loop supplies timing, the operation is the same function called once or ten-thousand times.

- **score(v, Θ) → (a, p, m).** `a = argmin_a ‖v − μ[c,a]‖²_DK`; confidence `p = softmax(−d²/τ)`; margin m.
  Reads μ, DK, τ; writes nothing. The action is a *distance*, never a reward maximization. *(The 36.89pp
  kernel result, §3, is the evidence for this contract.)*
- **route(v, Θ) → k\*.** `Q(k) = K_{c,k} · ( σ_k^{-1} + |∂d_a/∂v_k| + |μ[a₁,k] − μ[a₂,k]| )` — precision
  (reliable factors first) + leverage (how much reading k moves the decision) + discriminative (how much k
  separates the two leading actions). Read off Θ; no separately trained acquisition model.
- **enrich(v, e, G) → v'.** `v' = (1−ε)v + ε·A(s, G⊕e, Θ)`: admit evidence, re-extract. Writes only the
  working vector.
- **update(Θ, v, y) → Θ'.** On verified y ∈ {+1,−1}: `μ ← μ + η·y·(v − μ)` (LVQ; asymmetric — η_confirm 0.05,
  η_override 0.01, ratio set by ρ); K accumulates by EMA over which read last flipped a decision to a
  verified-correct action. Reads R; writes only μ, K. The one operation that reshapes the geometry.
- **separate(Θ) → σ.** Per-factor outcome-conditioned variance from R. Feeds route and diagnostics; never the
  scoring metric.
- **gate(R, θ_min, ρ, m_rel, W_short, m_rate) → {GREEN, AMBER, RED}.** A **three-layer** test —
  `allow iff G-ABS ∧ G-REL ∧ G-RATE`, pause if any fires. **G-ABS** (absolute floor): `α·q·V ≥ θ_min`
  (coverage × rolling verified accuracy over 400 decisions × volume) — protects cold-start (the floor clears
  in ≈3 decisions, 3.0–3.3 across copilots, so the window it uniquely protects is small). **G-REL** (relative
  trigger, multiplier m_rel = 0.7×): pauses when rolling accuracy falls below 0.7× its long baseline —
  protects against sustained drift. **G-RATE** (rate detector, W_short = 20, m_rate = 0.85×): pauses when the
  last 20 decisions fall below 0.85× the long baseline — protects against sudden drops that G-REL averages
  away. GREEN = all three pass (may act); AMBER = a layer fired (auto-action pauses, learning continues);
  RED = sustained degradation or hash-chain integrity failure (learning also pauses). Reads R and the
  configured constants; writes nothing. *(Why three layers: §5.4.)*
- **propose(Θ, R) → C** and **calibrate(R, Θ) → {DK, τ, θ_min}.** `propose` writes variant candidates to a
  pool C, promoted only when `gate` clears them (the engine half of AgentEvolver; §2.5). `calibrate` is
  offline and authorized — sets DK/τ/floor at deployment or scheduled recalibration, never in the decision
  stream.
- **attend(G_i, G_j) → discovery.** `softmax(E_i E_jᵀ/√d)·V_j`: `route`'s operator applied *between* graph
  domains rather than within one — the same mathematical object, a different role. One operator family spans
  scoring, acquisition, and discovery.

## **2.3 Invariants — what holds by construction**

These hold as a matter of the mathematics, not of careful operation; they are why the engine is *hardened*.

- **I1 — Decision-form invariance.** `a* = argmin‖v−μ‖²_DK` is written by no operation. So "the system
  compounds" and "the decision procedure never changes" are simultaneously true by construction — the
  invariant that makes self-improvement approvable.
- **I2 — σ⊥μ separation.** The expected update is σ-independent, `E[Δμ] = η·(GT − μ)`; learning (moves μ) and
  enrichment (reduces σ) are independent to first order (~1% coupling at production noise). *Example: buying a
  better data feed lowers σ and lifts day-one accuracy, but does not change how fast the system learns — the
  two investments are separable.*
- **I3 — A0: acquisition, not depth.** With graph and Θ frozen and enrichment inert, iterating the operator
  over unchanged evidence cannot improve the decision. Depth is acquisition, never loop count. *(Confirmed by
  the recurrence-ladder null, §5.)*
- **I4 — Conservation is exogenous.** `gate` reads R, never the current decision or any parameter the loop
  optimizes, so the loop cannot optimize around the gate.
- **I5 — Append-only certified record.** R is hash-chained and append-only; the update fires only on
  human-verified outcomes, never on the system's own guess; integrity failure forces RED.
- **I6 — Re-convergence.** `update` re-initializes from prior geometry, so after a shock the system
  re-converges faster than it first converged: γ > 1 ⇔ ε_firm > 0.125 (four proof paths; γ ≈ 1.2 in
  calibrated simulation, magnitude pilot-only). *Institutional memory is an asset against change, conditional
  on the firm's own deviation clearing the threshold.*

The six compose: I5 supplies certified signal, I1 confines where it writes, I4 governs when it acts, I2 keeps
the two learning engines separable, I3 bounds what iteration claims, I6 makes accumulated geometry pay off
after a shock. Remove any one and a specific failure opens.

## **2.4 Certification — two axes that answer different questions**

Every output carries two tiers on two orthogonal axes; they compose rather than compete.

**Axis A — what does the result certify? (the tier ladder)** T-arch (by construction) · T-geom
(geometry-derived oracle) · T-real (real-component, exported production geometry) · T-sim (simulated
streams/adversaries/competitors) · T-pilot (verified human outcomes, live). Magnitude on live decisions is
**always** T-pilot, never synthesized.

**Axis B — what generated the correctness signal? (the K-taxonomy, a cross-reference)** K1 oracle-behavioral
and K2 factor-vector-oracle are admissible (→ T-geom); K4 real-external supports T-real; **K3 — an LLM
generating both inputs and decisions — is rejected for any tier**, because it certifies the generator's
competence, not the engine's learning.

**The bright line (a rule, not a tier):** the engine forbids an LLM-judged correctness signal (K3) as
evidence for any claim. The *measured cost* of that violation is the result in §5: on investigation-dependent
decisions an LLM judge agrees with ground truth ~12% of the time; the geometry-derived check ~76%. That gap
is the line between measuring the engine and measuring the judge.

**How the two axes work together (the composition rule):** a claim reaches the top of the maturity spectrum —
a deployment-grade magnitude claim — **only when its signal tier is T-pilot.** Analytic + T-geom/T-real/T-sim
evidence establishes mechanism and bounds; the step to a live magnitude claim is exactly the arrival of
verified-pilot signal. The signal axis *gates* the maturity axis at the top — which is why, e.g., the
re-convergence theorem is proved and simulation-confirmed but its magnitude remains pilot-gated.

## **2.5 What is NOT in the engine (the boundary)**

The engine is the *statics* — objects, operations, invariants. The *dynamics* that sequence these operations
over time toward a decision are the surrounding architecture, specified in the control-plane sections
(§10–§11) and companion work: the **fast loop** (within-decision investigation: route→enrich→score iterated
to a halt), the **slow loop** (compounding via repeated `update`), the **enrichment controller** (a policy
over route's budget; §5), **AgentEvolver's promote/demote cycle** (the shadow-test-then-promote sequencing —
the engine exposes `propose` + `gate`, the cycle over time is architecture), and the **four readouts** of an
investigation (which evidence / how much / better action / confidence — outputs of the loop reading the
engine). The test: a noun-operation on state with a contract is the engine; a verb that sequences operations
over time is the architecture. The engine is the instruction set; the architecture is the program.

---

# **3. The kernel finding — evidence for `score`**

The `score` operation (§2.2) is `a = argmin_a ‖v − μ[c,a]‖²_DK`. Its defining design choice is the kernel —
the function by which a factor vector's proximity to a prototype is measured. This section is the primary
evidence for that contract, and it is the paper's most-cited single result.

## **3.1 Why the kernel is the highest-leverage decision**

The dot product is the default similarity function in modern ML because transformers use it — but the dot
product's validity in transformer attention rests on *representation learning*: training guarantees that
semantically similar tokens have high dot products. That guarantee does not transfer to pre-computed bounded
features. Enterprise scorers routinely operate on bounded [0,1] features with no such training — credit
ratios, risk factors, lead-time and quality scores — exactly where the guarantee is absent.

**Magnitude confounding, concretely.** If device_trust has mean 0.85 across all samples, then for any weight
vector W the dot-product contribution from device_trust is ≈ 0.85 × W_device — near-constant regardless of
the correct action. High-mean factors dominate the dot product and suppress the discriminative signal from
lower-mean factors. L2 distance does not have this problem: deviations from the centroid, not absolute
magnitudes, drive the distance. On a SOC alert `f = [0.95, 0.30, 0.10, 0.70, 0.90, 0.85]` against centroid
`μ = [0.90, 0.12, 0.08, 0.35, 0.88, 0.82]`, device_trust dominates the dot product (0.90×0.88 = 0.792) while
carrying almost no discriminative information; under L2 it contributes (0.90−0.88)² = 0.0004 (near zero) and
asset_criticality — (0.30−0.12)² = 0.0324 — correctly drives the decision, 80× more.

**The measured cost (EXP-C1):** dot product 61.00%, cosine 96.42%, L2 97.89% — a **36.89-percentage-point**
gap from one change, on identical data, identical centroids, zero learning. It is the largest single-variable
effect in the ~194-experiment record. [EQUATION GRAPHIC | e_score_kernel | consolidate: dot vs L2 on bounded
features, the device_trust worked example, +36.89pp | REUSE eq_cards e1/e2/e3 in graphics-renamed] At a SOC
processing 10,000 alerts/month, 61% vs 98% misroutes ~3,700 additional alerts — the kernel choice alone is
worth ~$2.5M/yr in analyst productivity.

## **3.2 Calibration and the two accuracy regimes**

`score` returns a calibrated confidence: at τ = 0.1, ECE = 0.036 on L2 (versus 0.190 at the previous τ =
0.25), competitive with post-hoc temperature scaling while requiring no calibration data (V3B). Two accuracy
regimes bound deployment: **centroidal synthetic** (perfect factors, ground-truth-aligned centroids: 97.89%)
and **deployment-realistic** (noisy factors, imperfect routing, 50-seed: 71.7% → 78.9% over 1,000 verified
decisions). The gap is the deployment noise floor; the rise within it is `update` compounding (§4).
Zero-learning accuracy at a four-action space is **90.6%** (SHIFT-2 + A=4) — the day-one value before any
learning, and the reason a reshape engine is useful before the firm's data exists.

## **3.3 The kernel weighting boundary (DK) — a characterized negative**

A candidate refinement — per-factor inverse-variance weighting (the DiagonalKernel, DK = diag(1/σ²)) —
appeared to add up to +13.2pp over L2 on synthetic heterogeneous noise (V-MV-KERNEL-HET) and traced a
monotone curve to +7.67pp (UNI-DK-01 v5.3, 1500 cells). On real data it did not survive de-circularization:
the advantage is preprocessing-dependent — the same dataset flips sign across conventions (Credit: +1.0pp
min-max, −0.8pp robust) — with no general predictor (best correlate r = −0.51, 60% leave-one-out). **L2 is
retained as the production default; DK is a deployment-specific option requiring per-deployment validation.**
This is a *boundary definition*, not a failure — and it is exactly why σ is walled off from DK by default
(I2): using σ in the scoring metric would couple `separate` to `score` and require re-characterizing the
coupling channel, a calibration decision with a named cost, not a free parameter. Signal tier: T-geom
(synthetic) reversed on T-real (three real datasets).

## **3.4 The correspondence — one operator, several roles**

`score`, `route`, and `attend` are the same attention-family operator in different roles, which is why the
engine has one mathematics rather than bolted-together subsystems. The correspondence to transformer
attention is exact at the discovery level and structural at the scoring level:

| Component | Transformer | `score` (Level 1) | `attend` (Level 2 discovery) |
|---|---|---|---|
| Query | token × W^Q | factor vector f | domain-i embeddings E_i |
| Key | token × W^K | centroids μ[c,:,:] | domain-j embeddings E_j |
| Kernel | dot product | **L2 distance** | dot product |
| Scaling | 1/√d_k | 1/τ | 1/√d |
| Multi-head | h projections | n_c categories (MoE) | n(n−1)/2 domain pairs |
| Correspondence | — | structural | **exact (Eq.6 = Eq.1)** |

[EQUATION GRAPHIC | e_correspondence | the transformer↔CGA Rosetta, three levels | REUSE math_blog_rosetta_stone.png in graphics-renamed]

---

# **4. Compounding, discovery, and scaling — the engine run over time**

§3 is `score` at a single decision. This section is what the engine produces when `update` runs over a
stream (compounding), when `attend` runs across domains (discovery), and when both run over months (scaling).
These are properties of the operations, certified at the tiers of §2.4.

## **4.1 Compounding — `update` over a verified stream**

Each verified outcome applies the LVQ move (`update`, §2.2); two learners from an identical start on the same
stream — one applying updates, one frozen — separate and stay separated. Realistic deployment climbs 71.7% →
78.9% over 1,000 verified decisions (V3A); the centroid means saturate near 200 decisions per class and carry
the firm-specific compiled asset. Compounding is not "we collected more data" — it is the decision surface
being reshaped by outcomes, so the next decision is computed on a better surface than the last. Signal tier:
T-real (exported geometry) + T-geom (curves); live magnitude → T-pilot. [CHART | pub_k_learning_accuracy /
pub_k_learning_routing | RENDERED in charts/]

**Cumulative advantage — measured, not modeled (new).** Against a decision-0 frozen twin on identical
scenarios, cumulative K-learning advantage scaled as **t^1.387, 95% CI [1.308, 1.477]** (measured, JM
apparatus, 40 deployments, 5,000 bootstrap resamples) — super-linear, the interval excluding 1. The
advantage curve is unbounded (the frozen twin never improves); accuracy, by contrast, saturates
logistically (c = 0.643, sub-linear by construction for any bounded quantity). K-learning improved bounded
decision quality by **+21.96 percentage points** over a frozen twin. Signal tier: T-real-sim (JM apparatus);
the VLD compounding curves above establish mechanism, this measurement establishes magnitude. [CHART |
e_jm_6a_cumulative_advantage | RENDERED in ci_core/charts/]

**The moat — firm-specific and non-transferable (new).** The compounded advantage does not transfer. Tested
learning-curve against learning-curve: a competitor trained on a *different* firm's stream, evaluated on the
incumbent's held-out decisions, never reaches sustained parity — routing-quality gap **19.6 ± 5.4 pp (SOC),
5.7 ± 1.1 pp (DataOps), 0/5 seeds** at parity. The gap closes only when the competitor is handed ~half the
incumbent's *labeled* verified stream; the asset is the verified-outcome labels, not the engine or the
inputs. Honest bound: non-transferable, not un-copyable — state migration collapses the gap, so the advantage
rests on the labels being unobtainable and a real switching cost, not on impossibility. Signal tier: T-real +
T-sim (constructed competitor); a designed experiment, not an observed market dynamic. [CHART | pub_moat_catchup
| RENDER from moat_b2_seeds.json | NEW]

## **4.2 Re-convergence — `update`'s response to a shock (I6)**

After environmental disruption the engine re-converges *faster than it first calibrated*, because accumulated
geometry provides a head start: γ = N₁/N₂ > 1 ⟺ ε_firm > 0.125, proved via four structural paths (two
four-judge math polls) and confirmed in binary simulation (ε=0.05 → γ=0.714 < 1; ε=0.20 → γ=1.033 > 1). A
prior γ < 1 finding was retracted as a calibration artifact (the apparatus ran at chance accuracy, leaving
conservation trivially always-paused). The dimensional lower bound γ ≥ 4.6 is idealized; the realized
acceleration under production dynamics is smaller but sign-consistent. Signal tier: T-arch (theorem) + T-sim
(γ ≈ 1.2 calibrated); magnitude pilot-gated (EXP-G1). *The business reading: when the threat landscape shifts,
institutional memory speeds re-calibration rather than slowing it — the answer to "should we rebuild after
the campaign?" is no.*

*Note: the re-convergence γ (ratio N₁/N₂, a recovery-speed metric) is distinct from the cumulative-advantage
exponent c = 1.387 (§4.1, JM apparatus) — different quantities, different experiments. See the full exponent
family in the JM paper.*

## **4.3 Discovery and scaling — `attend` across domains**

`attend` (§2.2) runs cross-attention between domain graphs: with z-score + L2 normalization, 111× above
random (EXP-2); without normalization, nothing (a structural prerequisite). Discovery capacity scales as
n(n−1)/2 domain pairs, empirically D(n) ∝ n^{2.11} (95% CI [2.09, 2.14], R² = 0.9999, n = 2–15, V1A) — the
excess 0.11 over the n² structural floor is the cross-discovery cascade. At six domains, 15 heads evaluate
~3.75M pairwise scores per sweep in under two seconds. This was originally a *simulation* result (V1A, T-sim);
the JM redesign harness (40 deployments, 5,000 bootstrap resamples) subsequently measured the discovery
surface directly: **SDK cross-domain discoveries scaled as n^2.150 across domains and t^2.622 across
sequential evidence sweeps, with 95% CIs [2.030, 2.299] and [2.436, 2.964] (measured, JM apparatus)** —
confirming the n² structural floor with a small cross-discovery excess. Signal tier: T-sim (V1A) upgraded to
T-real-sim (JM apparatus) for discovery scaling. [CHART | eq_scaling / discovery log-log | RENDERED in charts/]

*Worked example of discovery.* Attending the identity graph to the threat-intel graph surfaces that a
newly-privileged service account pushing an Intune policy to 40 endpoints is the *same* identity whose
credential appeared in a leak-forum toolkit this week — a legitimate admin channel turned into lateral
movement, a connection no single-domain query would ask for. This is the Stryker-shaped decision: no
signature, no precedent, only a privileged identity doing something it was permitted to do but never should
have.

## **4.4 The two-engine separation — why depth and breadth are independent (I2)**

The engine has two ways to improve `score`: move μ toward ground truth (the *depth engine* — `update`), and
reduce σ, sharpening class separation (the *breadth engine* — enrichment). I2 proves these are independent to
first order: the expected update `E[Δμ] = η·(GT − μ)` contains no σ, so enrichment lifts the decision floor
without changing the convergence rate, and learning bends the convergence curve without depending on σ.
Coupling runs only through a boundary-mislabeling channel, ρ_eff = 2·Φ(−s/2σ)²·(s/ε_firm), ~1% at production
noise (σ = 0.08), growing to ~5.5% at 50% degradation and ~12% at twice production noise. The empirical
signature (V-CGA-FROZEN v3, N=257, 90% power): enrichment lifts Day-1 accuracy +5.9pp (p < 0.0001) with *no*
change in convergence rate (d = −0.010, p = 0.873, a definitive null) — floor lifts, rate holds. Signal tier:
T-geom (proof T-arch). *The investment implication: the depth and breadth engines can be resourced
independently, except where operating noise approaches the decision-boundary scale.*

---

# **5. Experimental validation — organized by operation**

We validated the engine through ~194 experiment entries (59 primary + 1890 factorial sub-cells) across seven
phases (February–September 2026). This section organizes the record **by the operation each result
certifies**, and dual-tags every result on the two axes of §2.4 (signal tier × whether it establishes
mechanism or magnitude). Two principles governed the program: *experiments lead the code* (a theorem-vs-code
mismatch is a discovery, not a mixed result), and *boundary-defining negatives are as valuable as
capability-confirming positives.* All code and data are public.

## **5.1 `score` — the decision**

| Result | Number | Signal tier | Establishes |
|---|---|---|---|
| Kernel gap (EXP-C1) | +36.89pp (61.0 → 97.89%) | T-geom | mechanism (surviving primary finding) |
| Zero-learning (SHIFT-2, A=4) | 90.6% | T-geom | day-one capability |
| Realistic deployment (V3A) | 71.7 → 78.9% / 1K | T-geom, 50-seed | compounding shape |
| Calibration (V3B) | ECE 0.036 at τ=0.1 | T-geom | confidence ≈ accuracy |
| DK weighting (H-KERNEL) | preprocessing-dependent | T-geom → reversed T-real | **boundary: L2 retained** |
| A=4 vs A=5 (EXP-A4-DIAGONAL) | 13pp structural gap | T-geom | kernel-independent action-space choice |

## **5.2 `route` — acquisition, and the four readouts (new)**

The `route` operation selects decisive evidence: at a two-read budget the loop reaches 80–92% of
exhaustive-investigation quality (SOC 91.7% of exhaustive, Trading 90.7%, DataOps 84.4%, S2P 84.1%,
Purchasing 79.8%), reading 20–33% of factors — and against a trained random forest at the *same* two-read
budget, it is within 1.4 points on category routing with *zero* training labels. [CHART |
pub_budget_frontier_all_copilots | RENDERED in charts/]

**One investigation, four readouts (new).** A single `route`+`enrich`+`score` investigation produces four
things — which evidence to read, how much, a better action, and a calibrated confidence — and the confidence
readout is carried by the *investigation trajectory*, not by static geometry. An ablation makes it precise:
per-decision confidence discrimination is AUC 0.809–0.875 across five copilots (pooled 0.814) with the
trajectory features (delta_1 = how much the first read moved the action scores; post-investigation margin);
**removing the trajectory features drops it to AUC 0.642 — below the 0.650 population-signal baseline** —
while removing geometric features changes nothing. The confidence signal *is* the investigation trajectory.
The readout that is intrinsic to the mechanism lifts the weakest copilot the most (DataOps 0.577 → 0.826),
because every decision has a trajectory even where aggregate history is thin. Signal tier: T-geom.
*(A note on classification: the four readouts are outputs of the loop, §2.5 — architecture; this section
certifies the confidence readout's mechanism, T-geom, which is the load-bearing claim.)* [CHART |
pub_confidence_frontier + pub_confidence_ablation | RENDER from conservation_decision_features.json | NEW]

**Learned routing overfits out-of-distribution.** A fitted-Q router beats the closed-form Q by +10–21 points
*in-distribution* but collapses −32.75 points *out-of-distribution*; a fitted-linear router hurts (−35.6%).
The closed-form `route` is the portable, inspectable, day-zero default; learned routing is a per-deployment
upgrade. Signal tier: T-geom, in-distribution.

## **5.3 `update` — compounding, the moat, and re-convergence**

| Result | Number | Signal tier | Establishes |
|---|---|---|---|
| Compounding curves | +3–21 routing pts, 5/5 copilots | T-real + T-geom | mechanism; magnitude → T-pilot |
| **Cumulative advantage (JM, new)** | **c = 1.387, CI [1.308, 1.477]; +21.96pp gain** | **T-real-sim (JM apparatus)** | **super-linear advantage measured, CI excludes 1** |
| **Moat (B2, new)** | 19.6 ± 5.4 pp SOC; 0/5 seeds parity | T-real + T-sim | firm-specific, non-transferable |
| Re-convergence (I6) | γ > 1 ⇔ ε_firm > 0.125; γ ≈ 1.2 | T-arch + T-sim | asset against shocks; magnitude pilot |
| Cross-deployment transfer | ~2–7× warm-start, conservation-mediated | T-sim | within-domain only; K19 +28pp not reproduced |
| Asymmetric η (B5B-PROXY) | prevents 13–27pp degradation | T-geom | derived, not tuned |

[CHART | pub_moat_catchup | RENDER from moat_b2_seeds.json | NEW]

## **5.4 `gate` — conservation, and RL over the enrichment budget (new)**

**Safety is three layers — designed as two, a gap measured, a third added (new).** The gate was designed with
two layers: an absolute floor (cold-start) and a relative trigger (sustained drift). A characterization
experiment (A1, 90-cell factorial, 3-seed) measured a gap neither covers: a **sudden** accuracy drop in
steady state is invisible to the relative trigger, because that trigger compares against a *rolling* long
baseline and a sudden drop averages into its own baseline — even a multi-point drop dilutes to <2pp across
the 400-decision window before the ratio would trip, while the absolute floor has long since cleared
(V_clear ≈ 3). A follow-up added and tuned a third layer, **G-RATE** — a short window (last 20 decisions)
against the long baseline at 0.85× — which is not averaged into its own baseline and so catches the step:
**86.7% of sudden drops detected at 0.87% false-pause** (mean lag 19.67 decisions). The three-layer gate
covers every threat regime tested; the 0.85× operating point trades a longer detection lag (19.67 vs 12.33
at 0.90×) for far fewer false pauses (0.87% vs 7.67%) — a safety-first choice, stated. The gap is the finding
here: a two-layer design, measured against sudden drops, demanded a third mechanism, and the fix is measured,
not asserted. Signal tier: T-real (floors) + T-sim (injected threats). [CHART | pub_safety_layers_r2 +
pub_safety_rate_threshold | RENDERED in charts/]

**Conservation under attack.** Sustained poisoning (20%+ injection) is detected in 100% of tested cases
across five copilots (floor-preserving configurations, 3-seed, synthetic); adversarial stress (EXP-OP2,
N=100) measures 35% non-recovery under sustained poisoning without intervention, with a 0.15pp poisoning
ceiling at A=4 — conservation bounds the damage even when individual centroids are permanently shifted. The
promotion gate for `propose` was re-designed from a strict-inequality point comparison (59% power / 44% FPR
at n=10) to a two-proportion z-test (H₀: Δ≤0, p<0.05 AND Δ̂>3pp) — a production design finding. Signal tier:
T-real (floors) + T-sim (poison). [CHART | pub_gap2_risk_coverage_* | RENDERED in charts/]

**Conservation per threat model (JM apparatus, new).** The JM redesign harness measured the calibrated
conservation gate across four threat types (40 deployments, 5,000 bootstrap resamples): the gate detected
sustained corruption, gradual drift, and sudden change in **100% of trials with 0% clean false positives**;
sparse 10% adversarial injection was detected in **57%, defining the measured sensitivity boundary.** The
three-layer gate (A1 above) and the JM conservation gate (E-JM-4) measure the same mechanism at different
operating points: A1-R2 used production-fixed parameters (W_short=20, m_rate=0.85, 7.5% FPR on Bernoulli
streams); E-JM-4 used a per-threat-model sweep with calibrated thresholds (0% FPR). They do not contradict
— A1-R2 defines *production false-pause rate*, E-JM-4 defines *detection capability per threat model*.
Signal tier: T-real-sim (JM apparatus). [CHART | e_jm_4a_conservation_gate | RENDERED in ci_core/charts/]

**RL controls the enrichment budget — deployable and safe (new).** A learned controller over the enrichment
budget (a policy over `route`, §2.5 — architecture, not an engine operation) delivers **+6.82 pts (S2P) /
+6.47 pts (SOC) at fewer reads** (1.43 / 1.75 vs fixed 2.0), 0% clean-pause, 100% poison detection. A
Lagrangian sweep over the constraint penalty finds the best point at **λ = 0** — safety comes from the
substrate (persistent state, per-domain floors, the real poison protocol), not a tuned penalty
(safe-by-construction). This is the *positive* RL result; the companion *negative* is that RL inside the
scorer does not beat uniform η (EXP-RL-SCORER: none of EMA, Thompson, or hybrid warmup beats uniform on both
decisions-to-competence and AUT_ACC) — so **RL never selects the action** (I1), and its value is confined to
the enrichment loop. Signal tier: T-geom + T-sim, two copilots, in-distribution; magnitude → T-pilot. [CHART
| pub_ri7_adaptive_vs_uniform | RENDERED in charts/]

## **5.5 The certification bright line, measured (K14, new)**

The engine's certification rule (§2.4) forbids an LLM-judged correctness signal (K3). K14 measures the cost
of violating it. On 240 real LLM (Claude Sonnet, T=0) judgments against a geometry-derived ground-truth
anchor across five copilots: LLM-judge agreement with ground truth collapses from ~0.86 on surface-resolvable
decisions (SOC) to **0.08–0.12 on investigation-dependent decisions** (S2P/Trading/DataOps); where measurable,
the judge's correctness tracks its own confidence (r = 0.60 SOC, 0.45 Purchasing, n=50). The geometry-derived
check (T-geom) agrees with the same anchor **0.76–1.00** on four of five copilots. The gap — ~12% vs ~76% on
the hard decisions — is the bright line, measured: an LLM judge scores its own reading of the surface, not the
decision. Injecting these noise rates into the compounding loop shows they do not merely *misreport* learning
but *prevent* it (learning degrades 5–10pp at 88–92% noise, reverses at 92%). Signal tier: T-geom (anchor) +
T-sim (surface-wrong scenarios); this certifies the engine's rule, not a product capability. [CHART |
pub_k14_agreement + pub_k14_compounding_noise | RENDER from k14 outputs | NEW]

## **5.6 Invariants confirmed, and the recurrence-ladder null (A0/I3)**

I2 (σ⊥μ) is proved and its empirical signature confirmed (V-CGA-FROZEN, §4.4). I3 (A0) is confirmed by the
recurrence ladder: over an explicit graph with evidence fixed, adding recurrent depth (carried/gated state)
does not help and mildly hurts — the closed-form static router with compounding K (60.8% routing) beats
carried recurrent state (56.6%) and gated variants. Reasoning depth is acquisition, not iteration. Signal
tier: T-arch (proof) + T-geom (confirmation). [CHART | pub_recurrence_ladder_state_k | RENDERED in charts/]

## **5.7 Applicability — where the engine's value concentrates**

Value tracks a measurable property of the decision — how much the correct outcome depends on sequential,
conditional evidence. Intrinsic dimensionality is the strongest single descriptor (mean |ρ| = 0.66 across
capability results). The decisive test is within-domain: single-firm vs constructed multi-enterprise S2P
differ only in decision structure (conditional-evidence fraction 0.213 → 0.279, chain length 1 → 2), and the
paired compounding gain rises with it (+6.0 → +16.4 pts) — same copilot, higher complexity, larger effect. So
the architecture states where it applies before deployment. Signal tier: T-geom, exploratory (n = 5–6). [CHART
| pub_complexity_scatter | RENDERED in charts/]

---

# **6. Related work**

**Attention and kernels.** Distance-kernel attention is an established variant (Tsai et al. 2019;
Katharopoulos et al. 2020); our contribution is domain-specific — the kernel choice produces a 36.89pp gap on
bounded operational features (§3), and a next-order candidate (per-factor inverse-variance weighting) did not
survive de-circularization on real data (§3.3).

**Prototype networks and metric learning.** Prototypical networks (Snell et al. 2017) use Euclidean distance
for few-shot learning; the `update` operation extends this with asymmetric push/pull derived from worst-case
analyst quality, count-based decay, and mandatory clipping. Full-covariance metric learning (Xing et al.
2003; Weinberger & Saul 2009) is unnecessary here — off-diagonal terms add <1pp (the "naive Bayes paradox").

**Graph attention and cross-graph.** GAT (Veličković et al. 2018) applies attention within one graph;
`attend` operates *between* domain graphs with no shared topology (§4.3).

**Agent memory and cognitive architectures.** CoALA (Sumers et al. 2023) formalizes three long-term memory
types — episodic, semantic, procedural — that every agent-memory system (Mem0, Zep, MAGMA, GAM) implements.
Judgment memory (§7) is a fourth: it stores per-factor decision quality decomposed against verified outcomes,
compounds with use, and produces the conservation-law safety proof — none derivable from the other three.

**Recursive self-improvement and validation.** The engine's certification rule (§2.4) — that an LLM-judged
correctness signal is inadmissible — is a methodological contribution beyond the surveyed self-improving-agent
literature; the K14 measurement (§5.5) is its empirical grounding, and it applies to any system that claims
to learn from user behavior and validates that claim with synthetic users.

---

# **7. Discussion — judgment memory, the fourth cognitive type**

The results compose into a system that not only scores decisions but measures its own judgment quality per
factor. We call this **judgment memory** and position it as the formal payoff that distinguishes graph-native
*reasoning* from graph *engineering*.

| Memory type | Stores | Answers | Graph operation |
|---|---|---|---|
| Episodic | what happened | "did we see this before?" | **read** |
| Semantic | what is true | "what do we know about X?" | **read** |
| Procedural | how to act | "what should I do here?" | **route** |
| **Judgment** | **how well decisions are made, and where they are noise** | **"how reliably does action A work in situation S, and which factors are signal vs noise?"** | **reshape** |

The correspondence in the rightmost column is exact: a graph *read* implements episodic/semantic memory
(centroid geometry stores prototypes, σ stores where factors are signal vs noise, the conservation law stores
the safety proof) — a graph *routed* implements procedural memory — and a graph *reshaped* from verified
outcomes implements judgment memory, which none of the other three can derive because none computes
outcome-conditioned quality decompositions. **Read and route extend existing memory types with better
structure; reshape adds a memory type the others cannot produce — and it is the one that compounds.**

**Signal-confidence inversion — the proof judgment memory measures something new.** The per-factor σ produces
a diagnostic no other memory type can: the factor analysts report highest confidence in (device_trust, mean
4.2/5) has the highest outcome-conditioned variance (σ = 0.28), while the factor they rate routine
(threat_intel) has the lowest (σ = 0.07). This *trust trap* is structurally invisible to episodic, semantic,
and procedural memory. That σ survives the DK preprocessing-dependence (§3.3) — it is a *measurement* on the
geometry regardless of whether it weights the scoring kernel — is exactly why judgment memory is diagnostic
even under L2: its value is *knowing where your factors are noise*, not weighting the score.

**Limitations, stated as the operating envelope.** Magnitude on live decisions is pilot-only (T-pilot),
never synthesized. The DK weighting is preprocessing-dependent (L2 retained). Learned routing overfits OOD.
RL controls the enrichment loop, not the trajectory loop (a null). Judgment-level moat specificity is
SOC-only (routing-level for all five). The moat is non-transferable, not un-copyable. Applicability is an
exploratory n=5–6 finding. Re-convergence magnitude is pilot-gated. Each is a boundary the certification
discipline records rather than hides.

---

# **8. Conclusion**

Graph engineering — building a graph to read, wiring a graph to route — has moved from frontier to recipe.
Both stop at the same line: the graph is structure, the reasoning is the model's, performed once and
discarded. This paper specifies a third operation, *reshape*, as a hardened math engine: a small typed state,
a fixed set of operations, six invariants that hold by construction, and a two-axis certification discipline
that assigns every output a tier by what generated its correctness signal. The kernel finding (36.89pp) is
the first evidence for the engine's `score` operation; the conservation law governs when it acts; the
re-convergence theorem says accumulated geometry re-calibrates faster after a shock; the σ⊥μ separation makes
depth and breadth independent; and four further results — the four-readouts of an investigation, the
non-transferable moat, RL over the enrichment budget, and the measured cost of an LLM-judged correctness
signal — are organized, not asserted, by the certification discipline. A graph that reshapes from verified
outcomes produces judgment memory, a fourth cognitive-architecture type the field's taxonomy does not
contain, and it is the one that compounds. The engine is small enough to audit and governed enough to
approve — which is what it takes for self-improvement to be deployable rather than merely demonstrable.

---

# **9. Future work**

Highest priority is **real-data longitudinal validation** (6–12 months of operational data — the binding
T-pilot gate for every magnitude claim) and **EXP-G1 empirical re-convergence γ** (90-day pilot, centroid-distance metric; note that the cumulative-advantage exponent c = 1.387 is now measured via the JM apparatus — EXP-G1 measures the distinct re-convergence ratio).
Then: per-factor N_half validation; GNN embeddings for `attend`; multi-prototype extensions; kill-chain
sequence modeling; **self-computation** — graphs that reshape their own *structure* (which factors exist,
which sources feed them) under the same conservation gate, for which a formalism, a validated calibration
protocol, and a characterized conservation precondition already exist (convergence proved; full dividend
production-scope pending).

---

# **10. The control plane — the architecture that runs the engine**

The engine (§2) is the statics; the control plane is the dynamics — the loops that sequence the operations
over time (the boundary, §2.5). Four layers: the **GAE substrate** (score/route/update/gate/separate — §2),
the **copilot SDK** (the RL/evolution sidecar, conservation-state contract, promotion gate), **domain
copilots** (five parameterizations — SOC 6×4×6, S2P 5×5×8, Trading 5×4×10, Purchasing 5×4×7, DataOps 6×5×6 —
each with a domain reward and penalty ratio ρ: SOC 20:1, S2P 5:1, Trading 2:1, Purchasing 3:1, DataOps 10:1;
and the shared three-layer gate constants m_rel = 0.7×, W_short = 20, m_rate = 0.85×), and the
**AgentEvolver runtime** (the promote/demote cycle:
`propose` writes candidates, shadow-test over N decisions, `gate` promotes or rolls back). The judgment core
(score) is the authoritative decision path; the sidecar acts only after verified outcomes and never replaces
the centroid-selected action (I1). Seven binding runtime gates operate as a control plane rather than an
advisory layer: conservation, quality, safety, rollback, deployment-qualification (P28), promotion, and
audit-chain gates — each *prevents* an action rather than logging a warning.

# **11. Production characterization**

The conservation law runs across all five copilots on a shared control plane (9,826 tests, zero failures);
campaign-holdout infrastructure assigns treatment/control at the decision-node level by deterministic SHA-256
hash for auditable comparison. Real magnitude measurement awaits pilot deployment with operational analysts
(PILOT_GATED) — the T-pilot gate. The AgentEvolver decision-autonomy result (EXP-AE-DECISION): under
adversarial poisoning (20% harmful inputs), drift-triggered rollback + per-category η damping reduced
non-recovery from 56.9% to 14.4% (3/3 seeds), complementing conservation's aggregate gate with per-category
reversal. Terminal actions are governed recommendations, not autonomous execution — the system advises, a
human acts.

---

## Appendix A — Chart-to-claim map (with graphics reconciliation)

| Claim | § | Figure | Status | Kind |
|---|---|---|---|---|
| Chain of custody (engine spine) | 2.0 | engine_chain_of_custody | **NEW** | infographic |
| Kernel gap + worked example | 3.1 | e_score_kernel (reuse e1/e2/e3) | reuse | equation graphic |
| Transformer↔CGA correspondence | 3.4 | math_blog_rosetta_stone | reuse | equation graphic |
| Compounding curves | 4.1 | pub_k_learning_accuracy/routing | rendered | experiment chart |
| **Moat (B2)** | 4.1/5.3 | pub_moat_catchup | **RENDER** (moat_b2_seeds.json) | experiment chart |
| Discovery scaling | 4.3 | eq_scaling | rendered | experiment chart |
| Budget frontier | 5.2 | pub_budget_frontier_all_copilots | rendered | experiment chart |
| **Four-readouts + ablation** | 5.2 | pub_confidence_frontier + pub_confidence_ablation | **RENDER** | experiment chart |
| Conservation risk-coverage | 5.4 | pub_gap2_risk_coverage_* | rendered | experiment chart |
| Three-layer safety (A1) | 5.4 | pub_safety_layers_r2 + pub_safety_rate_threshold | rendered | experiment chart |
| **RL enrichment controller** | 5.4 | pub_ri7_adaptive_vs_uniform | rendered | experiment chart |
| **K14 bright line** | 5.5 | pub_k14_agreement + pub_k14_compounding_noise | **RENDER** | experiment chart |
| Recurrence ladder (A0) | 5.6 | pub_recurrence_ladder_state_k | rendered | experiment chart |
| Complexity scatter | 5.7 | pub_complexity_scatter | rendered | experiment chart |
| Consolidated engine formalism | 2.2 | e_engine_operations | **NEW** | equation graphic |
| **Cumulative advantage (JM)** | 4.1 | e_jm_6a_cumulative_advantage | RENDERED in ci_core/charts/ | experiment chart |
| **Discovery surface (JM)** | 4.3 | e_jm_6b_discovery_surface | RENDERED in ci_core/charts/ | experiment chart |
| **Conservation per threat (JM)** | 5.4 | e_jm_4a_conservation_gate | RENDERED in ci_core/charts/ | experiment chart |

**Graphics kinds (per the three-type discipline):** infographics (engine spine, judgment-memory table) live
as diagrams; experiment charts are in `charts/` or render from the named JSON; **equation-consolidation
graphics** gather the operation equations (score/route/update/gate) onto one card to avoid inline-math
rendering issues — `e_engine_operations` is NEW (the §2.2 operations on one card); `e_score_kernel` and the
Rosetta reuse existing eq_cards in `graphics-renamed`. All existing charts are in `graphics-renamed` /
`charts/`; only the four flagged **NEW/RENDER** items need generation.

---

*v15 (Sep 2026): JM redesign results propagated from jm_redesign_results_note_v6 — cumulative advantage
c = 1.387 (C1), discovery n^2.150 (C2), per-threat-model conservation (C3), +21.96pp accuracy reframe (C4).
A1 reconciliation added. γ/c exponent disambiguation noted. Prior: v14 synced to CI Math Engine Architecture
v6 and math_synopsis v24 — §2.2 gate is now the
three-layer operation (G-ABS ∧ G-REL ∧ G-RATE; m_rel 0.7×, W_short 20, m_rate 0.85×); §5.4 carries the A1
measured-gap→G-RATE safety story; §10 lists per-copilot ρ (incl. Purchasing 3:1); K14 Part 2 (compounding
under noise) summarized in §5.5 with the full per-copilot table held in the internal math_synopsis. Internal
build tags (SH-05a, SAFE-2) intentionally omitted — external register.*

*Companion internal reference: the CI Math Engine Architecture (canonical definitions of state, operations,
invariants, and certification). This paper inlines the spine to stand alone; where a definition here and the
engine architecture differ, the engine architecture is canonical.*

---

## Blog-cut note (this doc → arxiv AND blog)

**The blog version** is a complete read from: Abstract → §1 (read/route/reshape + the kernel worked example +
why-care) → §2.0–§2.1 (the engine whole, in intuition: chain of custody, the running SOC alert, the state
table + write-partition) → §3.1 (the kernel finding, concretely) → §4.1 moat + §5.5 K14 (the two most
buyer-legible new results) → §7 (judgment memory + the trust trap) → §8 close. It carries every "why care"
and every worked example, and drops the operation contracts (§2.2), invariant proofs (§2.3), the full
validation tables (§5), and the control-plane detail (§10–§11) — which the arxiv keeps. Same spine, two
depths, one source.
