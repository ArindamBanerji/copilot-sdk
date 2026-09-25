# Recursive Graph Improvement: A Governed Architecture for Self-Improving Enterprise Decisions

*A decision architecture that gets measurably better at a firm's own decisions the longer it runs — while
the decisions themselves stay inspectable and cannot be rewritten by the learning. This paper defines the
class (Recursive Graph Improvement), specifies the machine that implements it, and characterizes it across
five enterprise copilots.*

## Abstract

Enterprises want AI that improves with use; no risk owner will approve AI that can change its own decisions.
Those two demands have been mutually exclusive — which is why the standard stack (a rented model, a
knowledge graph read for retrieval, a graph of agents wired for orchestration) is frozen at deployment: it
reasons once per decision and never gets better at the firm's own decisions.

**Recursive Graph Improvement (RGI) resolves the conflict.** Its decision *boundary* reshapes from
*verified outcomes* — recursion over a judgment graph, not model weights — while the decision *procedure*
stays fixed and governed. It is neither retrieval, orchestration, nor adaptive retrieval; it is the first
architecture that gets measurably better at a firm's decisions *and* remains approvable by that firm's risk
owners. The keystone: **RGI compounds the firm's judgment, reinforcement learning tunes how it learns, and
neither can change the decision procedure the firm signed off on.**

Characterized across five enterprise copilots (reference implementation CI-VLD): judgment compounds (3–21
routing points, 5/5); the advantage is firm-specific and non-transferable; a single investigation loop
yields — at once — which evidence to read, how much, a better action, and a calibrated self-confidence
(AUC 0.81–0.88); RL controls the enrichment loop (~6.5–6.8 points at fewer reads); conservation bounds
sustained degradation; and value scales with decision complexity, so the architecture states where it
applies. Results are tagged by grounding, and the magnitude on a firm's live decisions is a deployment
measurement, never synthesized.

## 0. RGI is a new class of system

Enterprise AI is taxonomized today by what it does to a graph. **Read** systems (knowledge graphs, RAG)
retrieve what is stored. **Route** systems (graphs of agents, orchestration) dispatch work. Both are real
advances; both share a ceiling — the graph is structure the model reads or routes through, the reasoning is
the model's, performed once and discarded. A read system's ten-thousandth retrieval is its first; a route
system's ten-thousandth dispatch is its first. Adaptive-retrieval and active-acquisition methods push on
*when* and *what* to fetch, but they too leave the graph static: the fetching gets cleverer, the graph does
not get better at the firm's decisions.

**RGI is a third category: Reshape.** A Reshape system's decision geometry is changed by the verified
outcomes of its own decisions, so its reasoning compounds — decision ten-thousand is measurably sharper than
decision one, on *this firm's* decisions. The definitional test is precise and it excludes the incumbents:

> **A system is an RGI system iff (1) it reshapes the *decision boundary* (the prototype surface that
> assigns actions), not merely a retrieval ranking, from verified outcomes of its own decisions; and
> (2) that reshaping is governed by a conservation law, and the *decision procedure class* — the fixed
> functional form `a*(v) = argmin_a ‖v − μ‖²_DK` — is an architectural invariant the reshaping cannot
> alter.**

The two clauses do distinct work. Clause (1) is about *what* reshapes: the decision **boundary** (the
prototype surface `μ`) moves from outcomes — not a retrieval ranking. This excludes static RAG and
orchestration, and also the harder case of an *adaptive* retriever that updates its retrieval priors from
labeled outcomes: such a system reshapes what it *fetches*, not the surface that *decides*, so it fails
clause (1) by construction of the mathematics rather than by assertion. Clause (2) is about what stays
*fixed*: the prototypes `μ` evolve, but the functional form `a*(v)` does not — that invariance is what a
risk owner approves and what the learning layers architecturally cannot cross (§6.2, §7.1). This graph-vs-weights boundary is not merely definitional: §9.1 shows empirically that a shared-weights substrate cannot even be *validated* on investigation-dependent decisions, while an explicit geometry can. RGI is the
intersection that has been empty: **the decision boundary compounds from verified outcomes while the
decision procedure class stays invariant and governed.** CI-VLD is its first instance.

**Implications for the builder.** RGI is also a better way to *build*. One mathematics (attention over
learned geometry) spans discovery, scoring, and evidence acquisition — not three bolted-on subsystems. The
decision is a nearest-prototype computation in a low-dimensional, inspectable geometry — no language model
in the decision loop, sub-millisecond per read, and every factor's contribution auditable. And the
reasoning-depth question has a proven answer (Lemma A0, §2): iterating an operator over fixed evidence is
inert — value comes from *acquiring* the right evidence, not from deeper computation over the same evidence.
For an architect, this is a different foundation from stacking LLM calls: fewer moving parts, lower per-decision cost, and an auditable decision surface.

**Implications for enterprise deployment.** Enterprises want systems that improve with use but cannot
approve automation that changes its own decision procedure — a conflict that freezes most enterprise AI at
deployment. RGI is designed to satisfy both constraints at once: the decision boundary compounds while the
decision procedure class stays invariant and conservation-governed (§6.2). The architectural property is
what this paper establishes; whether a given deployment clears a specific firm's review is for that review,
which the design is built to satisfy rather than to pre-judge.

The contribution is not any single layer — each mechanism below is commoditizing on its own — but the
governed composition: a stack in which the decision boundary compounds while the decision procedure class
stays invariant. §1 lays out that stack as a running machine; the sections after zoom into each part.

### 0.1 Is Reshape just online learning, or a knowledge graph that updates?

No — and this is the objection the category must survive, so it is answered here rather than deferred. A
knowledge graph that updates changes *what is stored* (facts); RGI changes *the geometry that decides*
(where the boundaries between actions are), from verified outcomes, under a gate that forbids changing the
decision procedure. Online learning updates a model's weights from streaming data — the self-poisoning
vector, and unapprovable because the decision rule drifts opaquely. RGI's recursion is over an explicit,
auditable geometry, outcome-grounded, and architecturally barred from touching the decision rule. The
distinction is the whole point: it is *why* Reshape can be both compounding and governed where the others
cannot.

---

## 1. The machine: the static and dynamic architecture of RGI

Before the layer-by-layer detail, here is the whole machine in one place — its parts (the static
architecture) and how they run together on a decision (the dynamic architecture) — so that nothing below
arrives as a surprise.

### The static architecture — the building blocks
RGI is one decision system with a small, fixed set of parts. Each is a section of this paper; each is named
here with its one-line role and a domain example.

- **GAE — the Graph Attention Engine.** The substrate: an attention-family operator over a graph, shared
  across discovery, scoring, and evidence acquisition. Everything else is expressed on it. *(All five
  copilots run on one GAE instance.)*
- **The decision geometry (μ, σ, DK, τ).** A prototype surface that assigns an action to a factor vector —
  the thing that *decides*. *(SOC: a login's factor vector maps to "escalate" or "suppress" by its nearest
  prototype.)*
- **Routing.** Which evidence to acquire next, scored off the geometry (`Q`). *(S2P: for a borderline
  invoice, routing reads the contract-clause match before the vendor-history field.)*
- **Enrichment.** Acquiring that evidence and re-scoring the decision against the geometry. *(DataOps: pull
  the upstream-job status, re-score whether to auto-remediate.)*
- **The VLD loop.** Routing + enrichment composed into an investigation before the system commits
  (`Φ = A∘Ψ`). *(Trading: investigate counterparty exposure, then correlation, before executing.)*
- **Compounding.** Verified outcomes reshape μ and the routing memory K over time, so the loop gets better.
  *(Purchasing: each confirmed reorder sharpens the approve/hold surface for the next one.)*
- **RL control.** Reinforcement learning tunes *how much* to investigate (the enrichment budget) — never
  what to decide. *(S2P: spend one read on an easy invoice, three on a contested one.)*
- **Conservation.** An auditable gate over the system's recent verified accuracy that decides whether it may
  act autonomously or must escalate. *(SOC: pause auto-close on an alert class whose recent accuracy dipped
  below the floor.)*

Two of these — **the decision geometry and the conservation gate** — are what a firm approves and what the
learning layers can never alter; the rest are how the system investigates and improves *around* that fixed
core. [FIG 1a — pub_rgi_static_arch — infographic, NEW: the 8 building blocks as a stack, two invariant blocks highlighted; light bg, fragment labels]

### The dynamic architecture — the compounding decision loop
The parts run as two coupled loops on every decision, one fast and one slow:

- **The fast loop (within a decision, milliseconds).** A factor vector arrives → the geometry proposes an
  action → if the decision sits near a prototype boundary, routing picks the next evidence and enrichment
  acquires it → re-score → repeat until settled or the (RL-tuned) budget is spent → conservation decides
  emit-or-escalate. This is the VLD investigation.
- **The slow loop (across decisions, as outcomes verify).** Each verified outcome reshapes μ and K, so the
  fast loop's routing and decision both improve — decision ten-thousand computed on a sharper surface than
  decision one. This is compounding.

The slow loop is what the standard stack lacks: a read system (RAG) or a route system (agent orchestration)
has the fast loop at most and never the slow one; its ten-thousandth decision is its first. RGI's
contribution is the slow loop made **governed** (conservation bounds it) and **inspectable** (it reshapes an
explicit geometry, not opaque weights). [FIG 1b — pub_rgi_compounding_loop — infographic, REUSE graphics-renamed/pub_rgi_mechanism_schematic.png; relabel inner/outer clocks as fast loop (within a decision) / slow loop (across decisions)]

### What RGI unlocks
Naming the machine up front makes its payoff statable up front, so the reader knows where the paper is
headed:

- **It compounds** — gets better at *the firm's own* decisions with use, not at a generic benchmark (§4).
- **The advantage is the firm's own** — the compounded geometry is specific to the firm's verified
  outcomes and does not transfer to a competitor (§4.2).
- **One investigation, four payoffs** — the same loop yields which evidence to read, how much, a better
  action, and a calibrated confidence (§3).
- **Self-improvement a risk owner can approve** — the learning tunes *how it investigates and what its
  geometry looks like*, never the decision procedure, which stays fixed and governed (§6, §7).
- **It states where it applies** — value scales with decision complexity, estimable per deployment (§4.3).

Each is a claim the rest of the paper substantiates at a stated evidence grounding; the magnitude on a
firm's live decisions is always a deployment measurement, never synthesized.

---

## 2. The mathematical substrate

Every claim is a consequence of a small set of mechanisms, stated here so the rest reads as their
application. This layer is the foundation of the stack; the architecture's rigor and its inspectability both
live here.

> **Adversarial question — "Six-to-ten-dimensional geometry is a small model; is this even AI at scale?"**
> The low dimensionality is the design, not a limitation. It is what makes each factor's contribution
> auditable (the σ trust-trap diagnostic is meaningful only because `d` is small), what makes the loop
> matrix–vector cheap and language-model-free, and what lets a few hundred verified outcomes move the
> geometry — where a high-parameter model needs far more and is inspectable by no one. The scale that
> matters is the decision, and enterprise decisions are low-dimensional and high-stakes — exactly the regime
> an inspectable, compounding geometry fits.

**Decision geometry.** A decision is a factor vector `v ∈ ℝ^d` read from the reasoning graph. The scorer is
a prototype classifier over learned state `Θ = {μ, DK, σ, τ}` — centroids `μ_{c,a}` per category `c` and
action `a`, a diagonal metric `DK` (per-factor weights), a per-factor noise fingerprint `σ`, calibration
`τ`. The decision is nearest-prototype:

  `a*(v) = argmin_a ‖v − μ_{c,a}‖²_DK`,  confidence `p(v) = softmax(−d²/τ)`,

with margin `m(v)` the gap between the two nearest prototypes. This is graph *reasoning*, not *retrieval*:
the graph does not return what is stored; the geometry computes what the decision should be — and that
geometry is the object that compounds. *(SOC: a login is a factor vector; the nearest prototype is
"benign" or "escalate," not a retrieved past alert.)*

**σ⊥μ — separating judgment from noise.** `μ` carries the firm's judgment (where the boundaries are); `σ`
carries per-factor reliability (how noisy each factor is). Keeping them orthogonal lets the system act on
*what it has learned to trust* rather than raw factor values, and it surfaces **trust traps** — a factor a
team relies on that σ shows to be among its noisiest predictors. `σ` and `μ` are updated by different rules
and used for different purposes throughout. *(S2P: a vendor-reputation field the AP team trusts may carry
high σ — noisy — while a contract-clause match carries low σ; σ⊥μ is why the system weights the reliable
one.)*

**Cross-graph attention.** Judgment does not live in one graph. Cross-graph attention lets structure learned
on one decision graph inform another — the same attention-family operator that, at the acquisition layer,
ranks which evidence to read. One operator family spans discovery, scoring, and acquisition: the
architecture has one mathematics in several roles, not bolted-together subsystems. *(DataOps: a failure
pattern learned on one pipeline's graph informs scoring on a sibling pipeline via the same operator.)*

**Routing: the acquisition score.** When a single scoring pass is insufficient — the decision sits near a
boundary, decisive factors unread — the system acquires more evidence, directed by the scorer's own
geometry. The acquisition score for reading factor `k` given the current state is a closed-form function of
that geometry, three additive terms scaled by a learned per-category routing weight:

  `Q(k; v_t) = K_{c,k} · ( precision(k) + leverage(k) + discriminative(k) )`,

- `precision(k) = σ_k^{-1}` — reliability (inverse noise)
- `leverage(k) = |∂d_a/∂v_k|` — how much reading `k` moves the current decision
- `discriminative(k) = |μ[a₁,k] − μ[a₂,k]|` — how much `k` separates the two leading actions
- `K_{c,k}` — per-category routing memory, compounds from verified outcomes

The next read is `k* = argmax_k Q(k; v_t)`. Nothing here is trained by gradient descent on a separate
objective: the additive terms are read directly off `Θ`, and `K` is updated by the same verified-outcome
rule that moves the prototypes. *(Trading: for an ambiguous position, `Q` ranks "counterparty exposure"
above "recent volatility" if exposure both separates the leading actions and is reliably measured.)*

**Learning: how the geometry compounds.** A verified outcome updates the geometry. Prototypes move LVQ-style
toward correct factor vectors and away from incorrect ones,

  `μ_{c,a} ← μ_{c,a} + η · y · (v − μ_{c,a})`  (y = +1 correct, −1 incorrect),

and the routing memory `K` accumulates from which reads proved decisive. The operator that decides is the
operator that reshapes — this identity is what makes improvement recursive over the graph rather than bolted
alongside it. *(Purchasing: each verified reorder outcome nudges the "approve"/"hold" centroids, so the next
seasonal decision is scored on a surface shaped by the last one.)*

**Conservation.** Emission is gated by a conservation law — an auditable accuracy floor over recent verified
decisions (§6). The gate is a property of the running system's own verified record, not of the current
decision, which is what lets it govern self-improvement without becoming a tunable knob inside the loop. *(Purchasing: if the last 100 verified reorder decisions fell below the domain floor, the gate pauses autonomous approval and routes to a human.)*

**Lemma A0 (acquisition, not depth).** With the graph and `Θ` frozen and enrichment inert, `Φ` reduces to a
fixed map and the trajectory `v_0 → v_L` is a deterministic re-expression of `v_0` — one scoring pass
reproduces it. Iterating the operator over unchanged evidence cannot improve the decision. RGI's reasoning
depth is not loop count; it is the state-conditioned acquisition of new evidence. Proved here, confirmed
empirically (§5.3): adding recurrent depth over fixed evidence does not help and mildly hurts. *(SOC:
re-scoring the same alert factors five times changes nothing; reading the user's recent role change does.)*

These mechanisms — prototype geometry, σ⊥μ, cross-graph attention, the routing score, the LVQ compounding
update, conservation, and A0 — are the whole vocabulary. Everything that follows is what they produce when
composed into a loop, run over time, controlled, and governed. A per-claim map of equation → tier →
evidence is consolidated in Appendix B.


---

## 3. The investigation loop: routing, enrichment, and what one investigation produces

*Where we are in the machine (§1): the investigation loop — routing and enrichment composed into the fast loop.*

Routing and enrichment (§2) are not used in isolation. They compose into a loop, and that loop is the unit
of reasoning. This section describes the loop, walks one decision through it end to end, and then makes the
claim that reorganizes how its value should be read: a single investigation is the common source of four
capabilities that had been treated as separate features. [FIG 3-HERO — pub_rgi_hero — infographic, AUTHOR-SUPPLIED: one investigation → four readouts]

### 3.1 The loop

Before committing, the system investigates. The reasoning step is a composition `Φ = A∘Ψ`:

  `G_{t+1} = Ψ(v_t, a*(v_t); G₀)` — enrichment: admit the next evidence the current decision implicates,
  from the point-in-time graph `G₀`, chosen by `k* = argmax_k Q(k; v_t)`;
  `v_{t+1} = (1−ε)·v_t + ε·A(s, G_{t+1}, Θ)` — re-extract and damp toward the enriched read.

The sequence `v_0 → … → v_L` is the **inference trajectory**. Reads continue until the normalized update
falls below a threshold or the budget is exhausted; emission is subject to the conservation gate. No
language model participates; `Q`, `A`, and the halting test are matrix–vector operations over `Θ`, cheap
because the geometry is low-dimensional.

**Efficiency is selection, not brevity.** At a two-read budget the loop reaches ~80–92% of exhaustive-
investigation accuracy across the five copilots — SOC 91.7%, Trading 90.7%, DataOps 84.4%, S2P 84.1%,
Purchasing 79.8% — reading 20–33% of available factors [FIG 3a — pub_budget_frontier_all_copilots.png + pub_budget_efficiency.png — experiment, RENDERED (charts/)] (geometry-derived). Against a trained random forest given the *same* two-read
budget, the loop is within 1.4 points on category routing with *zero* training labels.

The full comparison, all at the matched two-read budget (SOC fixture, 400/143 split; category-routing
accuracy):

| Comparator | Budget | Category acc. | Training labels |
|---|---|---|---|
| Majority class | — | 32.2% | — |
| Contextual bandit (LinUCB) | 2 reads | 26.6% | 400 |
| Random forest (full-feature) | all features | 72.0% | 400 |
| Random forest (budget-2) | 2 reads | 39.2% | 400 |
| Feature-importance routing | 2 reads | ~38% | 400 |
| **VLD (zero labels)** | **2 reads** | **37.8%** | **0** |

Read precisely: a full-feature RF trained on 400 labels leads on raw accuracy, but at the *matched* two-read
budget VLD is within ~1.4 points of the budget-matched RF *with no training labels at all* — the
day-zero property (§7.2). *(geometry-derived; SOC fixture.)* Early halting saves
nothing (recovering from a wrong first read needs the second), so the claim is "the right two reads out of
many," not "fewer reads" — and the reason it holds is that the routing score, which picks the reads, is the
firm's compounding judgment (§4), not a fixed relevance heuristic.

### 3.2 One investigation, walked end to end (S2P)

A source-to-pay copilot faces an invoice exception. The initial factor vector `v_0` is read from the graph;
on surface factors alone the nearest prototype is **hold-for-review** by a thin margin — the decision sits
near a boundary, so the loop investigates rather than committing.

- **Route (read 1).** `Q` ranks the unread factors. The contract-clause-match factor scores highest — it is
  reliable (low σ → high `precision`), it would move the decision (`leverage`), and it separates
  hold from auto-approve (`discriminative`). The loop reads it. Enrichment folds the clause match into `v_1`.
- **The decision shifts.** `delta_1` (how much read 1 moved the action scores) is large: the clause match
  strongly supports auto-approve. The post-read margin between the top two actions widens.
- **Route (read 2).** `Q` now ranks the vendor's recent dispute history highest given `v_1`. It is read;
  it is consistent with auto-approve; `v_2` settles.
- **Commit or abstain.** The two governors run: recent verified accuracy for this category is above the
  per-domain floor (gate = ALLOW), and the post-investigation confidence (from `delta_1` and the final
  margin) is high. The system **auto-approves**, and — because this is a $12K invoice under the deployment's
  $50K auto-threshold at this confidence — does so autonomously; a $120K invoice at the same confidence
  would route to a human approver (§6.4).
- **Verify and reshape.** The approval is later confirmed correct. The LVQ update nudges the auto-approve
  centroid toward `v_2`; `K` for this category increments the weight on the contract-clause factor (it
  proved decisive). The *next* similar invoice starts on a slightly sharper surface and reaches the clause
  match one step sooner.

Four things came out of that single investigation: which evidence to read (route), the fact that two reads
sufficed (effort), a better final action than the surface prototype (the enriched decision), and a
calibrated confidence that made the auto-vs-escalate call. The next section makes precise that these are not
four mechanisms but four readouts of the one loop.

### 3.3 Four readouts of one process

**Why this matters.** A buyer evaluating the loop would otherwise see four separate features to purchase,
validate, and maintain — routing, effort control, action scoring, confidence. The claim of this section is
that they are not four features but four *payoffs of the one investigation*, so they are bought, validated,
and improved together. Precisely: **two of these four capabilities share a *source* (they are
measurements read from the investigation trajectory), and all four share a *substrate* (the same geometry
`Θ` and conservation gate).** Readouts 1–2 (which evidence, how much) are *actions of and controls on* the
loop — `Q` exists before a given trajectory and is updated between trajectories; the budget is a controller
*over* the loop. Readouts 3–4 (better action, confidence) are *outputs measured from* the trajectory. The
asymmetry is real and the paper does not paper over it. The strong, ablation-backed claim is about the
shared *source* of 3 and 4: removing trajectory features collapses confidence discrimination below the
population baseline (§3.5), establishing that the investigation itself — not static geometry or aggregate
history — carries the confidence signal, and that the same trajectory that reweights the action (Readout 3)
discriminates its correctness (Readout 4).

**Readout 1 — which evidence (routing).** `Q` selects the decisive reads: ~80–92% of exhaustive at two reads
(§3.1). *(Five copilots, geometry-derived.)*

**Readout 2 — how much evidence (adaptive effort).** The budget need not be fixed. A learned controller sets
it per decision — fewer reads where confident, more where not — for ~6.5–6.8 points of quality at *fewer*
average reads (1.4–1.7 vs 2.0), safely (two copilots — S2P, SOC — in-distribution, geometry-derived +
simulated; §5.2). "Spend smarter, not more." Note this is a *control on* the loop, not a readout *from* it
(§3.4).

**Readout 3 — a better final action.** Trajectory-conditioned scoring of the action — reweighting reads by
reliability (`Q×K`) and by how much each moved the decision — **recovers accuracy in inverse proportion to
how good the prior readout was** (a descriptive inverse relationship across the five copilots; n=5, not a significance claim): where the category-level readout was the
bottleneck it recovers **+20–22 points** (DataOps, Purchasing); where the readout was already strong the
gain is small. The result is therefore not "+20 points from one investigation" in general — it is a
mechanism that recovers gaps created by weak prior routing. The evidence was sufficient all along (an oracle
on complete evidence reaches near-100% action accuracy); the gain is in *scoring the acquired evidence well*
[FIG 3b — pub_oracle_ceiling_gaps.png — experiment, RENDERED (charts/)]. *(Five copilots, geometry-derived; readout-limited, not
architecture-limited — §8.)*

**Readout 4 — how much to trust the result (calibrated confidence).** The same trajectory yields a
per-decision confidence, carried by two features: `delta_1` (how much read 1 moved the action scores — "was
the investigation informative?") and `post_investigation_margin` (the top-two gap after reading — "how
decisive was the result?"). A calibrated model on these plus recent accuracy reaches **AUC 0.809–0.875
across all five copilots** (pooled 0.814, pooled ECE 0.011). At a 0.80 confidence threshold the system
auto-acts on 48–86% of decisions at 91–100% accuracy, escalating the rest [FIG 3c — pub_confidence_frontier — experiment, RENDER from conservation_decision_features.json: accuracy-vs-coverage per copilot
— TO RENDER]. *(Five copilots; per-copilot ECE up to 0.082 for DataOps → recalibrate before absolute-
threshold routing — §8.)*

### 3.4 Why "four readouts of one process" is the right reading

Readouts 3 and 4 are carried by *the same trajectory features* (`delta_1`, `post_investigation_margin`): the
signals that reweight the action readout are the signals that discriminate correct from incorrect. That is
the sense in which the investigation *is* the source, and the ablation makes it precise (§3.5): remove the
trajectory features and confidence discrimination drops to AUC 0.642 — below the population-signal baseline
of 0.650 — while removing geometric features changes nothing. The confidence signal is the investigation
trajectory; strip it and there is no signal.

The consequence is the point: an enterprise does not buy four separately-engineered, separately-tuned,
separately-maintained features. It gets one mechanism — the investigation — whose byproducts are selection,
effort, action quality, and self-knowledge. And because the confidence is a byproduct of reasoning rather
than a bolted-on calibration layer, it is inspectable (a small model over named trajectory features), which
is what makes it usable in a governed setting (§6).

**The critical test — not a confirmatory aside.** If the confidence signal is genuinely the investigation
trajectory rather than a confound with a copilot's decision volume or history, then it should carry signal
*exactly where aggregate history fails.* That is a falsifiable prediction, and DataOps is the case that
tests it: the trajectory features lift the *weakest* copilot the *most*. DataOps discriminated
barely above chance on population signals (AUC 0.577) and reaches **0.826** with trajectory features — the
largest single-copilot gain. Population signals (recent accuracy) are weak where a copilot's decisions are
shallow; but *every* decision has an investigation trajectory, so the trajectory feature carries signal even
where aggregate history does not. The readout intrinsic to the mechanism generalizes where the aggregate one
cannot.

### 3.5 Ablation
Confidence-model discrimination (pooled AUC) by feature class removed: all features 0.814; without
trajectory (routing-class) features **0.642** (below the 0.650 population baseline); without geometric
features 0.814 (no change); without population signals 0.774. Trajectory features are necessary and nearly
sufficient; geometric features contribute nothing; population signals are marginal [FIG 3d — pub_confidence_ablation — experiment, RENDER from conservation_decision_features.json: pooled-AUC bar by feature-class removed;
pub_confidence_ablation.png — TO RENDER] (geometry-derived).

> **Adversarial question — "A bigger top-k, or an adaptive-RAG retriever, does the selection already."** The
> routing is not top-k over embeddings; it is `argmax Q` over the scorer's own precision/leverage/
> discriminative geometry, and that ranking *compounds from verified outcomes* — a fixed retriever selects
> the same way on decision ten-thousand as on decision one. And §5.3 shows that iterating the operator over
> the acquired evidence adds nothing (A0), so the value is demonstrably in acquisition, which a generic
> retriever does not ground in a compounding decision geometry. The deeper difference: a retriever returns
> passages; this loop returns an action, an effort level, and a calibrated confidence — from one pass.

---

## 4. Compounding: the loop improves over time, and the improvement is the firm's own

*Where we are in the machine (§1): the slow loop — verified outcomes reshaping the geometry across decisions.*

The loop of §3 is not static. Every verified outcome reshapes the geometry it runs over (§2), so routing,
enrichment, and the decision all improve with use. This is the temporal layer — and where the durable value
lives, because what compounds is specific to the firm and does not transfer.

### 4.1 It compounds
Two learners run from an identical start on the same stream: one applies the verified-outcome updates, one
holds its geometry frozen. On exported production geometry, the learning geometry separates from the frozen
one and stays separated. On DataOps, routing quality rises from parity to a sustained gap and accuracy rises
with it, plateauing near five hundred verified decisions and holding on an extended run [FIG 4a — pub_k_learning_routing/accuracy/convergence.png — experiment, RENDERED (charts/);
pub_k_learning_routing.png, pub_k_learning_accuracy.png, pub_k_convergence.png]. Across all five copilots
routing quality improves by **3 to 21 points** over the frozen control (relative gains 4.8–43.2%, different
denominators), no copilot regressing at plateau [FIG 4a cont. — pub_k_extended_routing.png + pub_k_heatmap_evolution.png — RENDERED (charts/)] (real-component + geometry-derived). Under five-seed replication the separation
is stable (§4.2). *(SOC: a copilot that has resolved ten thousand of a firm's own alerts has reshaped its
geometry around that firm's normal privileged-access patterns; the frozen alternative triages alert
ten-thousand as it triaged alert one.)*

On a dedicated measurement apparatus (JM apparatus, 40 deployments, 5,000 whole-deployment bootstrap
resamples), cumulative K-learning advantage against a decision-0 frozen twin on identical scenarios scaled as
**t^1.387, 95% CI [1.308, 1.477]** — super-linear, the interval excluding 1 (measured, JM apparatus).
Bounded decision quality — the raw accuracy curve — improved by **+21.96 percentage points** over the frozen
twin and, as expected for a bounded quantity, **saturated logistically (c_acc = 0.643)** near the accuracy
ceiling. Super-linearity is a property of the *advantage* and *discovery* curves (unbounded quantities), not
accuracy itself — which must saturate by construction.

Cross-domain discoveries scaled as **n^2.150 across domains** (95% CI [2.030, 2.299]) and **t^2.622 across
sequential evidence sweeps** (95% CI [2.436, 2.964]; measured, JM apparatus) — confirming the n² structural
floor with a small cross-discovery excess. The discovery time-scaling exponent (β_d = 2.622) is distinct from
the cumulative-advantage exponent c = 1.387; together they form the measured exponent family that supersedes
the earlier modeled estimates.

### 4.2 The advantage does not transfer
A competitor can clone the engine — the mathematics is in §2 — and still start from zero on the firm's
decisions. What compounds is the geometry the firm's verified outcomes reshape, specific to the firm's
decisions. The moat is tested learning-curve against learning-curve: an independent competitor learns from a
*different* firm's stream and is evaluated on the incumbent's held-out decisions. The simulated competitor is an identical learner — same engine, same cold-start geometry — trained on a
*different* firm's decision stream and evaluated on the incumbent's held-out decisions; it never sees the
incumbent's verified outcomes. Across five seeds it never reaches sustained parity — a routing-quality gap
of **19.6 ± 5.4 points (SOC), 5.7 ± 1.1 points (DataOps), 0/5 seeds** (real-component geometry + simulated
competitor stream; a constructed experiment, not an observed market dynamic) [FIG 4b — pub_moat_catchup — experiment, RENDER from moat_b2_seeds.json: competitor-vs-incumbent learning curves, 0/5 parity]. The gap closes only when the competitor is handed roughly half the incumbent's *labeled*
verified stream; no realistic label-acquisition strategy short of that reaches parity. The asset is the
verified-outcome labels — not the engine, not the inputs.

Two depths, differing by copilot: **routing-level** specificity holds on all five and is stable across an
eight-fold learning-rate sweep (not a hyperparameter artifact); **judgment-level** (the prototypes `μ`
becoming firm-specific) holds for SOC (lead *widens* +15.9 points, 3/3 seeds, when `μ` compounds) but not
the other four (routing-specific only). We claim judgment-level for SOC and routing-level generally, not the
average. Stated bound: state migration collapses the gap — an entrant handed a copy of `μ`/`K` starts at
parity — so the advantage is *non-transferable*, not *un-copyable in principle*: it rests on the labels
being unobtainable and on a real switching cost, not on impossibility. That RL extracts *more* value from
the verified-outcome stream (§5) only raises the stream's worth — the moat deepens, it does not dilute.

> **Adversarial question — "An incumbent forks the open engine and wires it to their existing customers."**
> The fork ships the operator, not the fixed point it converges to on a given firm's data. The incumbent's
> customers each begin at their own decision one; judgment does not transfer between firms without the
> verified-outcome labels, and not even between two of the incumbent's own copilots without a shared factor
> space. On a compounding axis a head start widens before it closes. The scenario where a fork wins is one
> where the category this paper defines — governed compounding — is the category everyone competes in.

### 4.3 Value scales with decision complexity
RGI does not claim uniform value; its value tracks a measurable property — how much a decision's outcome
depends on sequential, conditional evidence — estimable per deployment before committing. This follows from
the mechanism: the loop's value is state-conditioned acquisition (§3), and a decision fixed by a single read
has nothing to route and little to compound.

Five complexity measures were computed per copilot from exported geometry. Intrinsic dimensionality is the
strongest single descriptor (mean |Spearman ρ| = 0.66): +0.899 with the compounding accuracy gain, +0.800
with the conservation clean-pause fraction, +0.771 with the action-readout gap [FIG 4c — pub_complexity_scatter.png — experiment, RENDERED (charts/);
pub_complexity_scatter.png]. The ordering — SOC/DataOps high, restaurant purchasing/single-firm S2P low — is
the ordering seen across every capability, explained by one property rather than five weaknesses
(exploratory: n = 5–6, low-power descriptive correlations).

The decisive test is *within-domain* variation. Single-firm S2P and a constructed multi-enterprise S2P
differ only in decision structure: the multi-enterprise configuration raises the conditional-evidence
fraction (0.213 → 0.279) and evidence-chain length (1 → 2), and the paired compounding gain rises with it
(+6.0 → +16.4 points). Same copilot, higher complexity, larger effect — so complexity is a property of the
decision path, not a domain label. *(Restaurant purchasing — reorder against par levels — is shallow and
one-shot, so its low measured value is expected; multi-enterprise procurement, with conditional cross-org
approval chains, is the decision the loop is built for.)* The applicability measure distinguishes the two
before deployment: the architecture states where it applies.

---

## 5. Reinforcement learning: controlling the loops, never the decision

*Where we are in the machine (§1): RL control — tuning how much the loop investigates, never the decision.*

Learning appears at three places in the stack, and the stance at each is deliberate. The decision is
selected by geometry — RL never selects it. The judgment compounds from verified outcomes (§4) — that is
not RL. The remaining place learning can act is *the loops themselves* — how the system investigates. That
is RL's role: a governed controller over the loops, and the boundary that keeps it off the decision is what
makes self-improvement deployable.

### 5.1 RL stays out of the decision (and the judgment core)
Tested directly: RL *inside* the scorer — learning-rate allocation, Thompson/UCB convergence strategies —
did not beat uniform η; the judgment core converges on its own. RL out of the decision is a design choice
backed by a null, not a limitation. The centroid geometry selects the action; RL is confined to controlling
the investigation loops around it.

### 5.2 RL controls the enrichment loop — the deployable result
Of the loops RL could control, the **enrichment loop** — the acquisition budget per decision (Readout 2 of
§3) — is the one RL controls with real, safe, consistent value. A learned budget controller, under the
conservation gate on persistent judgment state:

| Copilot | Baseline (fixed B=2) | Controlled | Quality gain | Reads/decision | Clean-pause | Poison detection |
|---|---|---|---|---|---|---|
| S2P | 0.634 | 0.702 | **+6.82 pts** | 1.43 (vs 2.0) | 3.27% → **0%** | **100%** |
| SOC | 0.765 | 0.830 | **+6.47 pts** | 1.75 (vs 2.0) | → **0%** | **100%** |

[FIG 5a — pub_ri7_adaptive_vs_uniform.png — experiment, RENDERED (charts/)]. Higher quality at fewer reads — one read where a decision is easy,
more where it is hard, matching effort to difficulty. Situational, as the complexity axis predicts (S2P gain
≥ SOC). It genuinely requires learning: a rule-based budget heuristic *hurt* (−2.1 pts S2P). *(Two copilots
— S2P, SOC — in-distribution; geometry-derived + simulated.)*

**Safe by construction, not by tuning — the deepest point.** A Lagrangian sweep over the constraint penalty
(λ ∈ {0,1,5,10,20,50}) found the best point at **λ = 0** — the controller is already inside the conservation
envelope (0% clean-pause, 100% poison) with *no* explicit penalty. Safety came from the substrate —
persistent judgment state, the per-domain calibrated floor (§6), the real poison protocol — not from a tuned
constraint; raising λ only made the controller overspend reads and lose quality. This is the difference
between RL as a *bounded asset* here and RL as the *unbounded liability* it is when bolted onto an agent that
selects actions: the safety is a property of the governed substrate the controller runs on.

### 5.3 The recurrence ladder — where control pays, and where it does not
Recurrence can be added to the reasoning step at increasing levels of machinery; the ladder places each
result and keeps the claims precise:

- **R0** — single scoring pass
- **R1** — state-conditioned re-scoring over *fixed* evidence (the A0 case)
- **R2** — state-conditioned *acquisition*: new evidence each pass (the VLD loop, §3)
- **R3** — carried recurrent state (RNN-style)
- **R4** — gated recurrent state (GRU/LSTM)
- **R5** — a learned recurrence/routing policy

Value appears at **R2 (acquisition)** and does *not* increase — in these experiments it decreases — as
machinery is added above it. On a paired DataOps study the closed-form static router with compounding `K`
reached 60.8% routing quality; adding carried recurrent state reached only 56.6%, and gated variants
underperformed both [FIG 5b — pub_recurrence_ladder_state_k — experiment, RENDER from ri1_routing_k_interaction.json if not in charts/] (geometry-derived). This is A0 confirmed:
iterating the operator (R1) and carrying/gating state (R3–R4) are inert-to-negative; the value is the
acquisition at R2. The one loop RL controls with gain is *how much to acquire* (R2's budget, §5.2) — not
depth over fixed evidence.

### 5.4 Stated bound
RL controls the *enrichment* loop (the RL-CTRL parametrization found it the one loop that pays, §5.2); it
does not reliably control the *trajectory* (learning-rate) loop — that was copilot- and
implementation-dependent, a null. RL is a *mapped, bounded* control surface, not a
general agent: it tunes how much to investigate where that pays, confined by conservation and by never
touching the decision. "RL tunes the learning" is the claim, at the loop where it is demonstrated, not "RL
tunes everything." The result is in-distribution and deployment-specific (a learned policy specializes to
the firm — consistent with the moat, §4 — and does not port); the magnitude on live decisions is a
deployment measurement.

> **Adversarial question — "Offline RL on your verified outcomes would beat the closed-form router; you just
> under-powered it."** We tested a learned router (fitted-Q) directly: it beat the closed form by +10–21
> points *in-distribution* but collapsed **−32.75 points out-of-distribution** — it overfits the training
> firm's structure. And a fitted-*linear* router (the closest inspectable form) *hurt* (−35.6%), so the
> gain is genuinely nonlinear, which is exactly what does not port. The precise conclusion is not "RL wins"
> or "RL loses" but "learned routing is a per-deployment upgrade; the closed-form router is the portable,
> inspectable, day-zero default." Offline RL addresses self-poisoning (it trains on verified outcomes) — but
> it forfeits inspectability and portability, so it is an option a deployment can exercise, not the default.

---

## 6. Governed autonomy: the conservation gate and its characterized envelope

*Where we are in the machine (§1): this is the conservation gate — the governor on the slow loop, and the part (with the decision geometry) that the learning layers can never alter.*

Expanding automation is defensible only if the system does less exactly when doing less is warranted. The
conservation gate is that governor — and, for the keystone, it is what lets the learning layers (§4, §5) run
without endangering the decisions the firm signed off on.

### 6.1 The gate, characterized per deployment
Emission requires recent verified accuracy to clear an auditable floor; below it, the system pauses and
escalates. The floor is **per-deployment**, fit at startup on the first 100–500 verified decisions (count
varies by copilot), not a global constant — because a global floor is structurally wrong for copilots whose
normal accuracy sits near it: under a global 0.75 floor, Purchasing paused on ~48% of *healthy* decisions.
The per-domain calibrated floor (DataOps 0.669, Trading 0.766, Purchasing 0.655, SOC 0.764, S2P 0.769)
reduces clean-stream false-pauses to **<5% across all five copilots while preserving 100% sustained-
poisoning detection** — the deployability fix and the safety guarantee together. *(Purchasing: its normal
0.735 accuracy sat below the global 0.75 and paused it into uselessness; the 0.655 calibrated floor lets it
operate.)*

### 6.2 The architectural partition (what the keystone actually protects)
The keystone claim — that the learning layers cannot change the decision the firm approved — is an
architectural partition, statable as which parameters each layer may touch. This is the boundary a risk
owner can audit:

| Parameter set | Status | Who may change it |
|---|---|---|
| Decision function form `a*(v)=argmin_a‖v−μ‖²_DK`; floor thresholds; autonomy-level bounds | **Fixed at approval** | No layer — architectural invariant |
| Prototypes `μ`, routing memory `K` | **Updated by verified outcomes** (LVQ), bounded by conservation | The compounding update only |
| Acquisition budget `B` | **Controlled at inference** | The RL controller only (§5) |
| The conservation gate's own update rule | **Never modified** by any learning layer | None |

The partition is disjoint by construction: the RL controller acts on `B`, never on `μ`/`K` or the decision
function; the compounding update moves `μ`/`K` within the conservation envelope, never the functional form;
and no layer can modify the gate that governs them, because the gate reads the system's verified record from
outside the learning loop (it is not a parameter the loop can optimize around). "The decision procedure the
firm signed off on" is the first row — the functional form and the approval thresholds — and it is the one
thing no learning layer can reach. The prototypes evolve; the procedure class does not.

### 6.2a The safety guarantee, scoped
The calibrated conservation gate detected sustained corruption, gradual drift, and sudden personnel change in
**100% of trials with 0% clean false positives**; sparse 10% adversarial injection was detected in **57%,
defining the measured sensitivity boundary** (per-threat-model sweep, JM apparatus E-JM-4, calibrated
thresholds). The boundary is stated, not hidden: sparse targeted poisoning is the characterized edge of the
gate's envelope — the point where detection degrades — and stating it is what makes the safety claim
auditable rather than a bare guarantee. A system that improves from verified outcomes and gates emission on
its own verified record detects sustained corruption of that record and stops — where an ungoverned learner
absorbs it silently. This is the concrete answer to the self-evolving-agent poisoning risk.

*A1 reconciliation.* The per-threat-model results above (E-JM-4) and the production gate characterization
(A1-R2, W_short=20, m_rate=0.85, 7.5% FPR on Bernoulli streams) measure the same conservation gate at
different operating points. E-JM-4 defines *detection capability per threat model*; A1-R2 defines *production
false-pause rate*. They do not contradict — they answer different questions about the same gate.

### 6.3 The characterized envelope (boundaries as a strength)
A four-stage characterization mapped what the gate catches and misses — and stating the edges is what makes
the safety claim auditable rather than a bare guarantee:
- **Sustained degradation** — caught; detection lag 9–328 records.
- **Fast regime breaks** (< the record window) — missed by an accuracy floor; a faster trigger is future work.
- **Slow drift** — a genuine boundary: no static composite, deployment-fitted tracker, or second-derivative
  signal closes it without regressing false-pause or the poison guarantee. Product answer: a scheduled
  re-verification cadence (e.g., weekly model-health checks against held-out decisions, automated
  escalation) — simpler and more reliable than real-time drift detection. Untested candidate: ensemble
  disagreement (divergence between two geometries — a non-accuracy signal).

### 6.4 Conservation as a per-decision governance layer
The gate's inputs exist per decision, and the loop produces a calibrated per-decision confidence (Readout 4,
§3). Together they turn conservation from a system-level switch into a per-decision, risk-adjusted governance
layer: auto-act on the high-confidence decisions, escalate the rest, thresholds set by the accountable owner
— a $50K approval requiring higher confidence than a $500 one (the worked example, §3.2). Because the
confidence is a byproduct of reasoning and inspectable, the buying *committee* is served at once: the
functional owner sets the dollar/severity threshold, security sets the minimum confidence, audit gets a
per-decision defensibility signal. This is the mechanism behind the keystone: learning improves the loops and
the geometry; the governed decision — inspectable, floor-gated, confidence-routed — is what the firm signed
off on and what no learning layer can rewrite.

> **Adversarial question — "A self-improving system will poison itself (per the self-evolving-agents
> literature)."** Self-poisoning arises when a system improves from self-generated signal. RGI improves only
> from verified outcomes, and the gate is the measured defense: it detects sustained poisoning of the
> verified stream (100%) and pauses. It does *not* catch fast breaks and needs per-domain calibration — both
> stated above. The claim is a governed, measured bound on sustained self-poisoning, not immunity — and RGI
> is confined to acquiring evidence and reshaping routing/prototypes, not to rewriting its objective (L5
> excluded, §7), which is the regime where self-poisoning is most acute.

---

## 7. RGI: bounded recursive self-improvement, and day-zero readiness

*Where we are in the machine (§1): naming the governed whole — the two loops, bounded and inspectable.*

With the machine specified (§1) and each part characterized (§§2–6), this section names what the whole is,
draws the bound that makes it governable, and states why it is useful before a firm's data exists.

### 7.1 What RGI names, and where it stops
The governed stack of §§1–6 is Recursive Graph Improvement: recursion over the *judgment graph* — the
decision geometry reshaping from verified outcomes — rather than over model weights. RGI is a deliberately
bounded instance of the recursive-self-improvement agenda the field has begun to formalize (Duan et al., 2609.11873, which lays out the autonomy ladder below and argues genuine recursion requires experience-grounded improvement). In that agenda's autonomy ladder — execute → strategize → acquire-experience → adapt-environment
→ rewrite-the-objective — CI-VLD occupies **L1–L3** (it executes improvements, chooses which evidence to
acquire, and accumulates routing memory from outcomes) and **excludes L5 (self-rewriting of its objective) by
design**, because self-generated improvement is the regime where self-poisoning is most acute — the failure mode
EVOMAL (2608.25776) documents in self-evolving agents that learn from their own outputs. The boundedness is the safety architecture, not a gap: for the enterprise, governed-and-
verifiable beats maximally-recursive. *(Trading: the system learns which evidence to investigate and
re-shapes its risk geometry from verified P&L, but it cannot rewrite its own objective — a bound a risk
committee requires before any autonomy.)* Where that agenda measures headroom with survey-level diagnostics, RGI
offers a concrete, per-deployment analogue — the compounding curve's re-convergence property — though its
magnitude is a deployment measurement, not a synthesized number.

The keystone is now earned rather than asserted. §6.2's partition table is the proof: the RL controller acts
only on the acquisition budget, the compounding update moves μ and K only within the conservation envelope,
and no layer can reach the decision function form or the gate's own rule. So "self-improvement an enterprise
can deploy" is not a slogan but a statable architectural fact — the learning improves *how the system
investigates and what its geometry looks like*, and the decision procedure the firm approved is, by
construction, outside every learning layer's reach. The improvement is outcome-grounded, the decision
procedure class is invariant, and the boundary between them is an architectural partition (§6.2) rather than
a policy — which is what lets a system be both self-improving and governable, the property the standard
stack cannot offer.

### 7.2 Day-zero readiness
RGI is useful before the firm's data exists, and explicit about the one thing it cannot know beforehand. The
routing that selects evidence is a closed-form read off the scorer geometry — no separately trained
acquisition model, no cold-start on a learned router; the scorer reasons from the first decision. At a
two-read budget the system is within 1.4 points of a trained baseline on category routing with zero training
labels (§3.1). Substantiation is **geometry-derived** — deterministic, annotator-free, reproducible, a
rigorous standard for *mechanism and capability* — but synthetic; the *magnitude* of compounding on a firm's
live decisions is a deployment measurement, not synthesizable in advance. In a market where the magnitude
number cannot be faked without being caught, drawing that line cleanly is the position that survives
diligence. The commodity layers (engine, SDK, a reference copilot) can be open; the compounding judgment a
firm accrues cannot (§4). *(S2P: a new deployment routes and triages invoices from day one on the exported
geometry; the firm-specific compounding begins accruing with its first verified approvals.)*

---

## 8. What RGI does not claim: the operating envelope

For an adversarial reader the boundaries are part of the result; the program pre-registered what each null
would mean before results were in.

The bounds are stated in-section; consolidated: magnitude is deployment-only, not synthesized;
judgment-level specificity holds for SOC, routing-level for all five (§4.2); the moat is non-transferable,
not un-copyable (§4.2); RL controls the enrichment loop (deployable) but not the trajectory loop (a null),
and learned routing overfits out-of-distribution (§5.2–5.4); the action frontier is readout-limited, not
architecture-limited (§3.3); per-decision confidence discriminates strongly (AUC 0.81–0.88) but needs
per-copilot recalibration on DataOps (§8 detail below); conservation catches sustained degradation (100%
poison) but leaves slow-drift open (§6.3); bounded decision quality gains +21.96pp but saturates
logistically (c_acc = 0.643) — super-linearity is a property of the advantage and discovery curves, not
accuracy (§4.1); and applicability is an exploratory n=5–6 finding (§4.3). The
recurring pattern — strength where decisions are complex, weakness where shallow — is the single
characterized property of §4.3, not scattered defects. Per-decision confidence detail: pooled ECE 0.011,
per-copilot up to 0.082 (DataOps), recalibrate before absolute-threshold routing (engineering, not
research).

These are the bounds of what RGI *does*; the next section turns to what the competing approaches cannot even
*measure*.

---

## 9. Competitive landscape and related work

Every mechanism RGI uses is commoditizing; the separation is the governed composition on a compounding
substrate, and — per §9.1 — the fact that the standard stack cannot even *measure* the decisions RGI
handles. This section positions RGI against the current field (bullets + a capability landscape) and
against the academic lineage.

### 9.1 The field is blind on the decisions RGI is built for (K14)

The competitive separation is not only that RGI compounds and others do not. It is that the standard way of
building *and validating* self-improvement is architecturally blind on exactly the decision class RGI
monetizes — and we measured it.

**Two choices the standard stack makes, and RGI does not.** First, *implementation*: the industry does
self-improvement by updating **shared model weights** — every update folded into one opaque parameter
tensor. RGI reshapes an **explicit decision geometry** (the prototypes μ and routing memory K over a graph),
updated from verified outcomes (§2, §4). Second, *validation*: because opaque weights expose no per-decision
object to inspect, the only scalable way to check whether an update helped is to have an **LLM judge** the
decisions (call this K2). RGI's explicit geometry can instead be checked directly against outcomes (K3 —
nearest-centroid over the exported geometry). **The first choice forces the second:** a shared-weights
substrate has no inspectable decision surface, so LLM-judged validation is the only option left.

**Why LLM-judged validation is blind — measured.** An LLM judge sees a decision's *surface* factors; it
cannot perform the multi-hop investigation the decision requires. So its agreement with ground truth is a
function of how much the correct answer is visible on the surface, not of whether the decision was right.
K14 tested this on 240 real LLM judgments (Claude Sonnet, temperature 0) against planted ground truth across
five copilots. The judge's agreement with ground truth **collapses from 0.86 on surface-resolvable decisions
(SOC) to 0.08–0.12 on investigation-dependent decisions (S2P 0.08, Trading 0.10, DataOps 0.12)** [FIG 9b — pub_k14_agreement — experiment, RENDER from k14_validation_tier.py output: K2-vs-anchor agreement per copilot, K3 overlay] — the
decisions whose correct action only emerges after acquiring non-surface evidence. The collapse is not noise:
where measurable, the judge's correctness tracks its *own* confidence (r = 0.60 SOC, 0.45 Purchasing on
n = 50 per copilot) — it rates its own surface-competence, not the system's decision; and on the
investigation-dependent copilots (S2P, Trading, DataOps) agreement is near-random *regardless* of the
judge's confidence, so it has no signal there at all.
These figures are measured on scenarios deliberately constructed to be surface-wrong, so they isolate the judge's blindness where the answer is not on the surface — not a natural-prevalence agreement rate.

**The two consequences.** (1) *The blind spot and the value are the same set.* The decisions the judge fails
on — investigation-dependent, multi-hop (§4.3) — are definitionally the decisions RGI's loop is built for. A
shared-weights, LLM-validated competitor's "it learns" claim is therefore unfalsifiable *precisely on the
decision class RGI monetizes.* (2) *You cannot compound what you cannot measure.* This is not rhetorical — it is measured. Injecting the
K2 noise rates into the compounding loop shows that noisy labels do not merely *misreport* learning, they
*prevent* it: below ~60% label noise compounding is unaffected, but at the 88–92% effective noise the LLM
judge produces on investigation-dependent decisions, learning degrades by 5–10 points and at 92% it
*reverses* (the loop unlearns). So a shared-weights competitor validating by LLM judgment on the hard
decisions has near-random signal (Part 1) *and*, were it to learn from that signal, would degrade rather
than improve (Part 2) — the mechanical reason the compounding moat (§4) is un-catchable, not merely that
"we learn faster." *(K14 Part 2: noise injected into the KE-1 compounding generator; geometry-derived.)* [FIG 9c — pub_k14_compounding_noise — experiment, RENDER from k14_compounding_noise.py output: compounding gain vs noise rate, crossover 60→92%]

**RGI is not itself blind.** The same K14 study shows the geometry-derived check (K3) agrees with the same
ground truth on four of five copilots (0.76–1.00) — so the blindness is a property of *LLM-judged* validation
over a shared-weights substrate, not of validation per se. (K3-vs-anchor overlaps cleanly where the
evaluation and production action vocabularies match, strongest on SOC; the cross-copilot figures carry that
caveat.)

This is the empirical payoff of the §0 category boundary. §0 defines RGI by *recursion over the judgment
graph, not model weights*; K14 is the data showing why that boundary is load-bearing rather than semantic:
the weights side is blind and unvalidatable on investigation-dependent decisions; the graph side is both the
thing that compounds and the thing that can be measured. For a buyer the diagnostic is concrete — ask a
vendor how its self-improvement is *implemented* (shared weights or an inspectable decision geometry) and
*validated* (LLM judgment or ground-truth-checkable) — because a K2-validated claim returns near-random
signal on the decisions you are paying to automate.

### The vendor landscape
The rows are the capabilities that decide the enterprise-decision case; the columns are the strongest
current exemplar of each approach. Rows 1–3 are table stakes (every serious approach delivers them); rows
4–6 are the compounding layer, where RGI separates. RGI's cells carry the tiers of §§4–6.

| Capability | Graph-RAG (MS GraphRAG) | Agent orchestration (LangGraph/AG2) | Uncertainty retrieval (Dey 2607.07380) | Active acquisition (L2M 2510.12624) | Self-evolving agents (EVOMAL 2608.25776) | Enterprise platforms (Palantir/Dropzone/CrowdStrike) | **RGI (CI-VLD)** |
|---|---|---|---|---|---|---|---|
| 1. Reasons over enterprise data | ✓ | ✓ | ✓ | ~ | ✓ | ✓ | **✓** |
| 2. Adapts computation to difficulty | ✗ | ~ | ✓ | ✓ | ✓ | ~ | **✓** |
| 3. Inspectable decision | ~ | ~ | ~ | ~ | ✗ | ~ | **✓** |
| 4. Compounds from verified outcomes | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | **✓** |
| 5. Firm-specific, non-transferable moat | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | **✓ ¹** |
| 6. Governed self-improvement (decision procedure fixed) | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | **✓ ²** |

¹ routing-level all five copilots, judgment-level SOC; non-transferable, not un-copyable (§4.2). ²
sustained-degradation bounded, per-domain calibration required, slow-drift a stated boundary (§6). The
scopes are what make the RGI column defensible — "✓ within stated bounds," where the alternatives are "✗."
[FIG 9a — pub_rgi_landscape — infographic, REFRESH graphics-renamed/CI_COMPETE_MATRIX_landscape.jpg: keep table-stakes/compounding format; update to the §9 six capabilities + current approach columns + the K14 blindness punchline; drop stale Eq.2/3/4 & 57%/14%]

### What each family lacks (the bullets)
- **Graph-RAG / knowledge-graph retrieval** — reads a graph that does not learn; decision ten-thousand is
  served like decision one. No slow loop.
- **Agent orchestration** — routes work between agents; the graph is a dispatch topology, not a decision
  geometry that reshapes. No compounding.
- **Uncertainty-conditioned retrieval** — shares RGI's spend-more-on-harder-decisions intuition, but
  conditions on model uncertainty (not verified outcomes), runs an LLM in the loop, and does not compound.
- **Active feature acquisition** — budgeted test-time acquisition with a *separate* trained model; RGI's
  routing is a closed-form read off the scorer's own geometry, and the ranking is the compounding asset.
- **Self-evolving agents** — do compound, but by updating shared weights from self-generated signal (the
  self-poisoning vector, §6) with the decision procedure itself mutable — unapprovable by a risk owner.
- **Enterprise platforms** — bring integration, per-alert depth, and case recall, but their memory is world
  memory or precedent retrieval, not a decision geometry that reshapes from outcomes; none shows a
  compounding curve or a conservation gate. RGI sits on top of these as substrate — fitment, not
  replacement.

**Closest competitor.** On mechanism, uncertainty-conditioned adaptive retrieval is nearest — both condition
acquisition on the current decision. RGI separates on four axes: no LLM in the acquisition loop; acquisition
that compounds from verified outcomes; scorer-parameter reuse with no separately trained acquisition model;
and conservation governance over autonomous action. No surveyed system claims a compounding,
verified-outcome-grounded substrate — the governed composition, not any single mechanism, is the separation.

### Related work (academic lineage)
- **Adaptive/recurrent inference-time computation.** The name adapts *virtual logical depth* (Shi et al.,
  2506.18233) — effective depth by weight reuse; RGI applies the term to evidence acquisition on an explicit
  judgment graph, not weight reuse in a latent state. §2's A0 and §5's recurrence-ladder null bear on the
  2025–26 looped/recurrent-transformer line: over an explicit graph with evidence fixed, iterating the
  operator is inert.
- **Uncertainty-conditioned adaptive retrieval** (Dey et al., 2607.07380) — RGI shares the intuition, claims
  no mechanism novelty, separates on the substrate (above).
- **Active feature acquisition** (L2M, 2510.12624) — separate acquisition model; RGI's is closed-form off
  the geometry, and the ranking compounds.
- **Recursive self-improvement** (Duan et al., 2609.11873) — RGI is a bounded, governed instance:
  L1–L3, L5 excluded; improvement from verified human outcomes over a graph, not model self-generation; the
  self-poisoning failure mode it guards against is documented in EVOMAL (2608.25776).
- **Judgment memory.** Reshaping decision geometry from verified outcomes is a persistent record of which
  factors predict which outcomes — a fourth memory type distinct from episodic, semantic, and procedural.
  RGI is the inference- and learning-time operation on that memory; and, per §3, the same investigation that
  reads from it produces the confidence to govern it.

---

## Appendix A — Chart-to-claim map
| Claim | § | Figure | Grounding |
|---|---|---|---|
| Static + dynamic architecture | 1 | pub_rgi_static_arch, pub_rgi_compounding_loop | infographic |
| Budget frontier (~80–92% at 2 reads) | 3.1 | pub_budget_frontier_all_copilots, pub_budget_efficiency | geometry-derived |
| One investigation → four readouts (hero) | 3 | pub_rgi_hero | infographic |
| Action recovery (oracle gap) | 3.3 | pub_oracle_ceiling_gaps | geometry-derived |
| Confidence frontier | 3.3 | pub_confidence_frontier | geometry-derived |
| Confidence ablation | 3.5 | pub_confidence_ablation | geometry-derived |
| Compounding curves (3–21 pts) | 4.1 | pub_k_learning_routing/accuracy/convergence, pub_k_extended_routing, pub_k_heatmap_evolution | real-component + geometry-derived |
| Moat catch-up (0/5 parity) | 4.2 | pub_moat_catchup | real-component + simulated |
| Complexity scatter | 4.3 | pub_complexity_scatter | exploratory |
| Enrichment controller (~6.5–6.8) | 5.2 | pub_ri7_adaptive_vs_uniform | geometry-derived + simulated |
| Recurrence ladder / A0 | 5.3 | pub_recurrence_ladder_state_k | geometry-derived |
| Conservation (poison, false-pause) | 6 | pub_gap2_risk_coverage_*, pub_cross_copilot_starvation | real-component + simulated |
| Cumulative advantage (t^1.387, CI excl. 1) | 4.1 | — (JM apparatus) | measured, JM apparatus |
| Discovery scaling (n^2.150, t^2.622) | 4.1 | — (JM apparatus) | measured, JM apparatus |
| Bounded accuracy (+21.96pp, c_acc=0.643) | 4.1 | — (JM apparatus) | measured, JM apparatus |
| Conservation per threat model (100/100/100/57%) | 6.2a | — (JM apparatus E-JM-4) | measured, JM apparatus |
| K14 validation-tier (field is blind) | 9.1 | pub_k14_agreement, pub_k14_compounding_noise | geometry-derived |
| Capability landscape | 9 | pub_rgi_landscape | infographic |
| Consolidated formalism (all §2 equations) | 2 | pub_rgi_formalism | equation graphic |

## Appendix B — Formalism index (equation → status → evidence)
A single-view rendering of the equations below is provided as the consolidated formalism graphic [FIG B — pub_rgi_formalism — equation graphic, CLAUDE-CHAT-GENERATED PNG/PDF, extra-large fonts] to avoid inline rendering issues; the index maps each to its status and evidence.

| Mechanism | Equation (§2) | Status | Evidence |
|---|---|---|---|
| Prototype decision | `a*(v)=argmin_a‖v−μ‖²_DK` | architectural | five-copilot scoring |
| σ⊥μ separation | `σ` ⟂ `μ` (distinct update rules) | architectural + validated | trust-trap surfacing |
| Cross-graph attention | attention over learned geometry | architectural | one operator, three roles |
| Routing score | `Q=K·(σ⁻¹+leverage+discriminative)` | validated (in-dist) | budget frontier §3.1 |
| Compounding update | `μ←μ+η·y·(v−μ)` | validated (real-component) | K-curves §4.1 |
| Conservation floor | per-domain accuracy floor | validated (real-component) | §6.1–6.2 |
| A0 (depth inert) | `Φ` fixed when `Ψ` inert | proven + confirmed | recurrence ladder §5.3 |
| Partition (governance) | disjoint {fixed / μ,K / B / gate} | architectural | §6.2 table |
