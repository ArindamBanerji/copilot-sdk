# Recursive Graph Improvement: Self-Improving Graph Reasoning for Enterprise Decisions

A decision architecture in which the geometry that makes a decision is reshaped by the verified outcome of
that decision — so reasoning compounds on a firm's own decisions rather than staying fixed at deployment.

> *Evidence convention (inline throughout).* Results are tagged by grounding: **geometry-derived**
> (correctness by nearest-centroid assignment over exported production geometry — deterministic,
> reproducible, synthetic), **simulated** (streams and verification), or **real-component** (the exported
> production geometry itself). The one quantity none of these produces — the magnitude of compounding on a
> specific firm's live decisions — is a deployment measurement, marked as such wherever it arises.

## Abstract

The standard enterprise-AI stack — a rented model, a knowledge graph read for retrieval, a graph of agents
wired for orchestration — reasons once per decision and never gets better at the firm's own decisions:
decision ten thousand is handled as decision one. Recursive Graph Improvement (RGI) removes that ceiling.
A decision is a factor vector scored against learned prototypes on a reasoning graph; when one pass is
insufficient, the system acquires further evidence *conditioned on the current decision state* — a
closed-form geometric rule chooses what to read, with no language model in the loop — and verified outcomes
then reshape both the prototypes and the routing memory. The operator that decides is the operator that
learns; the recursion is over the judgment graph, not over model weights.

Across five enterprise copilots (security operations, source-to-pay, trading, purchasing, data operations),
on exported production geometry with synthetic verification, RGI **compounds** (routing gains of 3–21
points, five of five copilots, no regression at plateau); the compounded advantage is **firm-specific and
does not transfer** (a competitor learning on a different firm's stream never reaches parity — the
verified-outcome labels are the asset); investigation is **efficient by selection** (80–92% of
exhaustive-investigation accuracy at two reads; within 1.4 points of a trained baseline with zero labels);
autonomy is **governed** (post-investigation calibration plus a conservation gate that bounds sustained
degradation, with characterized limits); and the mechanism is **inspectable** and **depth-inert** —
iterating the operator over fixed evidence, or adding recurrent state, does not help; acquisition does. The
obvious extension, reinforcement-learning the router or recurrence, gains little here while forfeiting the
safety, inspectability, and day-zero readiness that define the approach. RGI's value is a **characterized
function of decision complexity** — strong where decisions require sequential, conditional evidence, weak
where they are shallow — so the method states where it applies.

We are explicit about grounding throughout. These results substantiate the RGI *mechanism and
capabilities* on real geometry; the *magnitude* of compounding on a specific firm's live decisions is
established only from real verified outcomes at deployment. That boundary — mechanism substantiated,
firm-specific magnitude deferred to the deployment it requires — is the honest position, and it is the one
that survives technical diligence.

---

## 0. The mechanism: graph reasoning that reshapes itself

The object that *makes* a decision should be the object that *learns* from it. A retrieval system reads a
graph and a routing system dispatches through one, but in both the reasoning is the model's, performed once
and discarded — neither the reading nor the routing gets better at the firm's decisions. RGI closes that
loop: the decision is computed from a geometry on the graph, the verified outcome reshapes that geometry,
and the next decision is computed on the reshaped one. The rest of this section makes that precise, because
every capability in the paper is a consequence of it. [chart: pub_rgi_mechanism_schematic.png — Φ = A∘Ψ
decision/enrichment/learning loop, two clocks]

**Decision geometry.** A decision is a factor vector `v ∈ ℝ^d` read from the reasoning graph. The scorer is
a prototype classifier over learned state `Θ = {μ, DK, σ, τ}` — centroids `μ_{c,a}` per category `c` and
action `a`, a diagonal metric `DK`, a per-factor noise fingerprint `σ`, calibration `τ`. The decision is
nearest-prototype, `a*(v) = argmin_a ‖v − μ_{c,a}‖²_DK`, with confidence `p(v) = softmax(−d²/τ)` and margin
`m(v)` the gap between the two nearest prototypes. This is graph *reasoning*, not graph *retrieval*: the
graph does not return what is stored; the geometry computes what the decision should be — and that geometry
is the object that compounds.

**Enrichment as state-conditioned acquisition.** A single scoring pass uses whatever the initial read
supplied. When that is insufficient — the decision sits near a boundary, decisive factors unread — RGI
enriches the factor vector by acquiring more evidence from the graph, conditioned on the current decision.
The reasoning step is a composition `Φ = A∘Ψ`:

  `G_{t+1} = Ψ(v_t, a*(v_t); G₀)` — admit the next evidence the current decision implicates, from the
  point-in-time graph `G₀`;
  `v_{t+1} = (1−ε)·v_t + ε·A(s, G_{t+1}, Θ)` — re-extract and damp toward the enriched read.

`Ψ` is enrichment (where to read next); `A` is scoring extraction over the enriched read. The sequence
`v_0 → v_1 → … → v_L` is the **inference trajectory** — the provisional decisions and the evidence each
admitted — retained as an auditable object.

**Routing: which evidence to acquire.** `Ψ` is directed by the scorer's own geometry. The acquisition score
for reading factor `k` is a closed-form function of that geometry — three additive terms scaled by a
learned per-category routing weight:

  `Q(k; v_t) = K_{c,k} · ( precision(k) + leverage(k) + discriminative(k) )`,

- `precision(k) = σ_k^{-1}` — reliability of factor `k` (inverse noise);
- `leverage(k) = |∂d_a/∂v_k|` — how much reading `k` would move the current decision;
- `discriminative(k) = |μ[a₁,k] − μ[a₂,k]|` — how much `k` separates the two leading candidate actions;
- `K_{c,k}` — the per-category routing memory that compounds from verified outcomes.

The next read is `k* = argmax_k Q(k; v_t)`. Nothing here is trained by gradient descent on a separate
objective: the additive terms are read directly off `Θ`, and `K` is updated by the same verified-outcome
rule that moves the prototypes. Reads continue until the normalized update falls below a threshold or the
budget is exhausted; emission is subject to the conservation gate.

**Learning: how the geometry compounds.** A verified outcome updates the geometry. Prototypes move LVQ-style
toward correct factor vectors and away from incorrect ones, `μ ← μ + η·y·(v − μ)`; the routing memory `K`
accumulates from which reads proved decisive. The operator that decides is the operator that reshapes —
this identity is what makes the improvement recursive over the graph rather than bolted alongside it.

**Conservation.** Emission is gated by an auditable accuracy floor over recent verified decisions (§5), so
a system whose recent decisions are unreliable pauses rather than acts. The gate is a property of the
running system's own verified record, not of the current decision, which is what lets it govern
self-improvement without becoming a tunable knob inside the loop.

**Two lemmas that shape everything downstream.**
- *A0 (acquisition, not depth).* With the graph and `Θ` frozen and `Ψ` inert, `Φ` reduces to a fixed map
  and `v_0 → v_L` is a deterministic re-expression of `v_0` — one scoring pass reproduces it. Iterating the
  operator over unchanged evidence cannot improve the decision. RGI's reasoning depth is not loop count; it
  is state-conditioned acquisition. Proved here, confirmed empirically in §6.
- *Two clocks.* Within a decision, the trajectory enriches and re-scores (fast); across decisions, verified
  outcomes reshape `μ` and `K` (slow, compounding). Graph engineering has the first clock at most and never
  the second. The claim of this paper is that the second clock — made governed and inspectable — is what
  turns a decision system from static to compounding.

---

## 1. Compounding: the copilot gets better at the firm's own decisions

*A static system handles its ten-thousandth decision exactly as its first. An RGI copilot does not — its
reasoning geometry is measurably sharper because ten thousand verified outcomes have reshaped it. This is
the defining property; the rest of the paper is what it makes possible and what bounds it.*

The mechanism is §0's learning clock. Each verified outcome applies the LVQ update to `μ` and accumulates
routing memory in `K`, so two quantities rise together over a stream of verified decisions: the routing
quality of the inference trajectory (the geometry directs `Ψ` to more decisive reads) and the decision
accuracy of the emission. Compounding here is not shorthand for "we collected more data" — it is the
decision surface being reshaped by outcomes, so the next decision is computed on a better surface than the
last.

The evidence runs two learners from an identical start on the same stream: one applies the verified-outcome
updates, one holds its geometry frozen. On exported production geometry, the learning geometry separates
from the frozen geometry and stays separated. On DataOps, routing quality rises from parity to a sustained
gap and decision accuracy rises with it, plateauing near five hundred verified decisions and holding on an
extended run [chart: pub_k_learning_routing.png / pub_k_convergence.png — DataOps learn-vs-frozen]. Across
all five copilots routing quality improves by **3 to 21 points** over the frozen control (relative gains of
4.8–43.2%, different denominators), no copilot regressing at plateau [chart: pub_k_learning_routing.png,
pub_k_learning_accuracy.png — five-domain curves incl. S2P's weak early behavior] (geometry-derived). Under
five-seed replication the separation is stable: on the moat protocol (§2) the incumbent's advantage over a
non-learning control is 19.6 ± 5.4 points on SOC and 5.7 ± 1.1 points on DataOps, with zero of five seeds
showing the control reach parity (real-component + simulated).

The compounding is uneven, and that unevenness is a result, not a caveat. SOC compounds strongly, DataOps
moderately, S2P weakly — a single property, decision complexity, characterized in §3: RGI compounds in
proportion to how much a decision's resolution depends on sequential, conditional evidence, and a shallow
decision gives the geometry little to compound. Stating where the effect is strong and where it is weak is
part of the capability.

What these results establish is that the compounding *mechanism* operates on real geometry. What they do
not establish is the *magnitude* on a particular firm's live decisions: correctness here is geometry-derived
— deterministic and reproducible, but synthetic — and the magnitude a deployment realizes is measured in
its first weeks of verified operation, not synthesizable in advance.

**Adversarial question — is this just online fine-tuning under a new name?** No. Fine-tuning adjusts a
model's parameters from data the model generates or is fed, which is the mechanism by which a self-improving
system poisons itself. RGI's recursion is over the judgment graph: the geometry is reshaped only by
*verified outcomes*, the update is a bounded, inspectable LVQ move on explicit prototypes rather than an
opaque parameter shift, and emission is conservation-gated (§5). The improvement is outcome-grounded and
auditable, not self-generated — which is why it compounds without drifting, and why the compounding belongs
to the graph rather than to a model checkpoint.

---

## 2. The advantage is the firm's own, and it does not transfer

*A competitor can clone the entire RGI engine tonight — the equations are in §0 — and still start from
zero on your decisions. What compounds is not the mechanism; it is the geometry your verified outcomes
reshape, and that is specific to your decisions.*

The reason is structural. Compounding is driven by verified outcomes on a particular firm's stream (§1); a
different firm's stream reshapes the geometry toward a different surface. The verified-outcome labels are
the operative asset — the LVQ update requires knowing which past decisions were right, and that record is
the firm's, not the market's. A competitor with the same engine, the same schema, even the same *inputs*,
still lacks the *verified outcomes* that direct the reshaping.

The moat is tested as learning-curve against learning-curve — not against a frozen control, which would
understate it. An independent competitor learns from a *different* firm's stream and is evaluated on the
incumbent's held-out decisions. Across five seeds it never reaches sustained parity: a routing-quality gap
of 19.6 ± 5.4 points on SOC and 5.7 ± 1.1 points on DataOps, zero of five seeds reaching parity on either
[chart: moat catch-up (competitor-on-different-stream vs incumbent, 0/5 parity) — TO RENDER]. The gap closes
only when the competitor is handed roughly half of the incumbent's *labeled* verified stream — and no
realistic label-acquisition strategy short of that (self-labeling, weak supervision, purchased partial
labels) reaches parity. That localizes the asset precisely: the verified-outcome labels, not the engine and
not the inputs.

The moat has two depths, and they differ by copilot:

- **Routing-level** — which evidence the geometry directs the trajectory to acquire — is data-specific on
  every copilot tested, and stable across an eight-fold sweep of the learning rate, so it is not a
  hyperparameter artifact.
- **Judgment-level** — whether the prototypes `μ` themselves become firm-specific under outcome learning —
  holds for SOC (the incumbent's lead *widens* by +15.9 points, three of three seeds, when `μ` compounds)
  but not for the other four copilots, which are routing-specific only.

The paper claims judgment-level specificity for SOC and routing-level specificity generally; it does not
average the two into a blanket claim (real-component + simulated).

Source-to-pay makes the depth difference concrete. A single-firm S2P deployment — internal approvals plus
external suppliers — reshapes a relatively shallow geometry. A *multi-enterprise* S2P deployment —
conditional approval chains across organizations with conflicting policies — reshapes a geometry whose
firm-specific structure a competitor cannot reconstruct from its own book, because the decisive
conditionalities are particular to that network of enterprises. The moat deepens with the complexity of the
decisions being compounded (§3).

One honest bound: state migration collapses the gap — a competitor initialized with a copy of the
incumbent's learned `μ`/`K` starts at parity. The advantage is therefore *non-transferable*, not
*un-copyable in principle*: it rests on the labels being unobtainable and on migration carrying a real
switching cost (stale geometry against a moved distribution, re-verification), not on cryptographic
impossibility. For this audience that is the stronger claim, because it is the true one.

**Adversarial question — an incumbent forks the open engine and out-compounds you.** The fork supplies the
operator, not the fixed point the operator converges to on a firm's data. The incumbent's own customers
each begin at their own decision one; judgment does not transfer between firms without the verified-outcome
labels, and not even between two of the incumbent's own copilots without a shared factor space. On a
compounding axis a head start widens before it closes. The scenario in which a fork wins is one in which the
category this paper defines — compounding, verified-outcome-grounded graph reasoning — is the category
everyone competes in, which is the outcome the argument seeks.

---

## 3. Applicability is characterized: value scales with decision complexity

*RGI does not claim uniform value, and does not need to. Its value tracks a measurable property of the
decision — how much the correct outcome depends on sequential, conditional evidence — and that property can
be estimated per deployment before committing. A system that can state where it applies is more useful,
and more credible, than one that claims to apply everywhere.*

This follows directly from the mechanism. RGI's value comes from state-conditioned acquisition (§0): the
geometry directs the trajectory to the evidence that will move the decision, and it compounds by learning
which reads are decisive. A decision whose outcome is fixed by a single read has nothing to route and
little to compound — the acquisition mechanism has no purchase. Value should therefore track decision
complexity, and specifically the *conditional* fraction: decisions where the next useful read depends on
what the last read revealed.

Five complexity measures were computed per copilot from exported geometry — intrinsic dimensionality,
conditional-evidence fraction, action-class separability, evidence-chain length, outcome entropy — and
tested against the campaign's capability results. Intrinsic dimensionality is the strongest single
descriptor (mean |Spearman ρ| = 0.66): +0.899 with the compounding accuracy gain, +0.800 with the
conservation clean-pause fraction, +0.771 with the action-readout gap [chart: pub_complexity_scatter.png].
The ordering places SOC and DataOps high, restaurant purchasing and single-firm S2P low — the same ordering
seen across every capability in the paper, now explained by one property rather than restated as five
weaknesses (exploratory: n = 5–6, low-power descriptive correlations).

The decisive test is that complexity varies *within* a domain, not only across domains. Single-firm S2P and
a constructed multi-enterprise S2P differ only in decision structure: the multi-enterprise configuration
raises the conditional-evidence fraction (0.213 → 0.279) and the evidence-chain length (1 → 2), and the
paired compounding gain rises with it (+6.0 → +16.4 points). Same copilot, higher decision complexity,
larger RGI effect. This is why complexity is the axis and not a domain label — it is a property of the
decision path and its deployment topology, and it moves the RGI value when the path is made more
conditional. Restaurant purchasing (reorder quantities against par levels) is a shallow, largely one-shot
decision, so its low measured value is expected rather than anomalous; multi-enterprise procurement is the
complex, conditional decision the mechanism is built for.

This is an exploratory finding on a small sample with a constructed multi-enterprise configuration — a
targeting hypothesis, not a validated law; observed multi-enterprise validation is the pending step. What
it establishes now is the frame: RGI's applicability is a measurable function of decision complexity, and
the weak copilots are weak for a characterized reason.

**Adversarial question — does it work everywhere?** No — and being able to say so with a number is part of
the capability. The applicability measure identifies the decisions on which the compounding, the moat, and
the investigation efficiency are large, and those on which they are not. For an architect that is the
difference between a technology that must be believed uniformly and one that carries its own operating
envelope; for a buyer it is the difference between a claim and a targeting criterion.

---

## 4. Efficient investigation: the right evidence, not more of it

*Facing a decision with many factors it could read, an RGI copilot reads the two or three its geometry
marks as decisive and reaches most of exhaustive-investigation quality at a fraction of the cost. The
efficiency is selection, not brevity.*

The routing function `Q = precision + leverage + discriminative`, scaled by the compounding memory `K`
(§0), ranks candidate reads by reliability, decision-moving power, and how sharply they distinguish the
leading actions — so the first reads acquired are the ones most likely to resolve the decision, and because
acquisition is state-conditioned, the second read is chosen given what the first revealed. Budget
concentrates on the decisive path rather than spreading across factors.

At a two-read budget RGI reaches 80–92% of exhaustive-investigation accuracy across the five copilots — SOC
91.7%, Trading 90.7%, DataOps 84.4%, S2P 84.1%, Purchasing 79.8% — reading 20–33% of the available factors
[chart: pub_budget_frontier_all_copilots.png / pub_budget_efficiency.png] (geometry-derived). Given the
*same* two-read budget, RGI comes within 1.4 points of a trained random forest on category routing with
*zero* training labels, and ties the full-feature random forest on action accuracy at 47.55%; a
contextual-bandit baseline is worse than the majority class at this budget — the expected failure of
exploration under a tight read budget (real-component + simulated).

A test of early halting — reading fewer than the budget when the decision looks settled — produced no
saving: recovering from a mis-directed first read requires the second, so the trajectory does not read
fewer than two. The efficiency claim is therefore exactly "the right two reads out of many," not "cheaper
investigation." Stated as fewer reads, it invites the reply that a smaller top-k does the same; stated as
geometry-directed selection on the firm's own judgment surface, there is no such equivalent — the ranking
that selects the reads is itself the compounding asset. (Exhaustive here is a geometry-derived oracle
ceiling, 100% by construction, so "80–92% of exhaustive" is a fraction of that oracle, not of independent-
label human accuracy.)

A DataOps alert that looks routine on its surface factors is resolved by reading the one factor the
geometry flags as decisive here — a recent schema change on the implicated source — which a similarity
search over the alert text would not surface, because it is decisive by the firm's learned geometry rather
than by textual resemblance to past alerts.

**Adversarial question — a bigger top-k or an adaptive-RAG retriever does this already.** The routing is not
top-k over embeddings; it is `argmax Q` over the scorer's own precision/leverage/discriminative geometry,
and that ranking compounds from verified outcomes. A fixed retriever selects the same way on decision ten
thousand as on decision one; RGI's selection improves because the ranking is the firm's accumulating
judgment. §6 shows, further, that iterating the operator over the acquired evidence adds no material gain —
so the value is demonstrably in the acquisition, which is the part a generic retriever does not ground in a
compounding decision geometry.

---

## 5. Governed autonomy: the system knows when it cannot be trusted

*Expanding automation is defensible only if the system does less exactly when doing less is warranted. An
RGI copilot commits when its recent verified record supports acting and abstains — reverting to escalation
— when it does not.*

Two governors operate (§0). A conservation gate: emission requires that recent verified accuracy clears an
auditable floor, so a system whose recent decisions are unreliable pauses. And calibrated abstention on the
individual decision: after the inference trajectory runs, post-investigation confidence separates the
decisions the system gets right from those it gets wrong. The calibration is *post-investigation* — the
surface confidence before evidence is acquired does not separate right from wrong; the investigation itself
produces the signal. That is a direct consequence of state-conditioned acquisition: the system learns
whether it can be trusted on this decision only by reasoning through it.

On held-out data with a separate threshold-selection set, accuracy on the acted-upon decisions rises
monotonically as coverage falls — abstaining on the least-confident quarter raises accuracy-on-acted by
+8.5 to +15.2 points on SOC, DataOps, and Purchasing [chart: pub_gap2_risk_coverage_{soc,dataops,purchasing}.png
/ pub_gap2_coverage_vs_lift.png] (geometry-derived). Under injected degradation the conservation gate
detects sustained drift and label-poisoning with a detection lag of 9–328 records and pauses before the
record window falls below the floor; canonical results under a matched decision distribution confirm the
gate's act/pause behavior on clean streams (real-component + simulated).

The governance has characterized limits, and stating them is part of the safety claim:
- **Lagging, not instantaneous.** The gate is a floor over the last hundred verified records — it catches
  *sustained* degradation but *misses fast regime breaks* within that window; a faster trigger is future
  work.
- **Domain-scoped abstention.** The abstention lift is strong on SOC, DataOps, and Purchasing, near zero on
  Trading and S2P, whose decisions do not separate as cleanly post-investigation.
- **Base-accuracy mismatch.** A fixed absolute floor mis-fits copilots whose base accuracy sits near it: on
  restaurant purchasing (steady-state ≈ 0.735) a 0.75 floor pauses on normal operation, so per-domain
  relative-change gating — triggering on a drop from each domain's own baseline — is required and not yet
  resolved.

The capability is "bounds sustained degradation, with a measured lag, on domains that separate
post-investigation," not a universal guarantee. In practice the two governors compose: a Trading copilot
facing an unresolved regime escalates rather than committing, and if its own recent verified accuracy on
that instrument class has fallen below the floor, the gate pauses autonomous action on the class entirely —
the system does less precisely when doing less is warranted.

**Adversarial question — a self-improving system will poison itself.** Self-poisoning arises when a system
improves from self-generated signal. RGI improves only from verified outcomes, and the conservation gate is
the measured defense: it detects sustained poisoning of the verified stream with a stated lag and pauses.
It does not catch fast breaks and it needs per-domain calibration — both stated above. The claim is a
governed, measured bound on sustained self-poisoning, not immunity; and RGI is deliberately confined to
acquiring evidence and reshaping its routing and prototypes, not to rewriting its own objective, which is
the regime where self-poisoning is most acute.

---

## 6. Inspectable reasoning, and why depth is not the trick

*RGI's reasoning is legible end to end — three auditable artifacts and a replayable trajectory, no language
model in the decision loop. And the property most systems assume adds value, reasoning depth, adds none
here: the value is acquisition, not iteration.*

The compounded state is three objects a reviewer can open, each reshaped by verified outcomes:
- **Centroid geometry** `μ` — the learned prototype of a correct decision in each category.
- **Noise fingerprint** `σ` — per-factor reliability, which surfaces *trust traps*: a factor a team relies
  on that is in fact among its noisiest predictors.
- **Conservation status** — the gate's current act-or-pause state and the record window behind it.

The inference trajectory — which reads `Ψ` admitted, in what order, and how each moved the decision — is
retained per decision, so a decision can be replayed against the graph as it stood when it was made.

Depth is not the trick, and this is demonstrated rather than asserted. Recurrence can be added at
increasing levels of machinery — a ladder the paper uses to place each result:
- **R0** single scoring pass;
- **R1** state-conditioned re-scoring over fixed evidence (the A0 case);
- **R2** state-conditioned *acquisition* (RGI's `Φ = A∘Ψ` — new evidence each pass);
- **R3** carried recurrent state (RNN-style); **R4** gated recurrent state (GRU/LSTM); **R5** a learned
  recurrence/routing policy.

Value appears at R2 and does not increase — in these experiments it *decreases* — as machinery is added
above it. On a paired DataOps study the closed-form static router with compounding `K` (`Static+K`) reached
60.8% routing quality; adding a carried recurrent state (`RNN+K`) reached only 56.6%, and hand-set GRU and
LSTM gates underperformed both [chart: pub_recurrence_ladder_state_k.png — Static+K vs RNN+K vs GRU/LSTM,
learned-Q +1.4pp delta; + pub_q_ablation_term_contribution.png] (geometry-derived). (`RNN+K` did show a
higher action-accuracy point estimate — again the routing-vs-action distinction of §8 — but it lost on
routing, the axis recurrence was meant to improve.) Both axes a depth-oriented design would add — iterating
the operator (R1) and carrying or gating recurrent state (R3–R4) — are inert or negative here; the value is
the acquisition at R2, exactly as Lemma A0 predicts.

The contrast with latent-depth approaches is exact. A looped or recurrent transformer adds reasoning depth
inside a model's hidden state, where it is neither inspectable nor, per the result above, evidently
helpful over an explicit graph. RGI adds depth as *observable acquisition over an explicit graph*, where
each step is auditable — obtaining the benefit the looped-transformer line pursues (more reasoning per
decision) without the opacity, and locating the value where the evidence puts it.

**Adversarial question — six-to-ten-dimensional geometry is a small model; is this even AI at the scale
that matters?** The low dimensionality is the design, not a limitation. It is what makes every factor's
contribution auditable (the σ trust-trap diagnostic is meaningful only because `d` is small), what makes
the trajectory matrix–vector cheap and language-model-free, and what lets a few hundred verified outcomes
move the geometry enough to compound — where a high-parameter model would need far more and be inspectable
by no one. The scale that matters here is the decision, and enterprise decisions are low-dimensional and
high-stakes, which is precisely the regime an inspectable, compounding geometry fits.

---

## 7. Why not reinforcement-learn the router? (the obvious RSI extension)

*The first improvement a reader will propose is to make the routing or recurrence learned — RL-tune a
policy against outcomes instead of using the closed-form geometric router. If RGI is recursive
self-improvement, why not let the router self-improve? The answer is already in the evidence, and it is
that the trade is bad here.*

Two results bound the headroom an RL router would chase. Learned linear `Q` coefficients — the closest
thing to an RL-tuned router in the experiment set — improved routing by only **+1.4 points** over the
closed-form `Q`: the ceiling learning reaches sits close to where the closed form already is. And on the
recurrence axis, adding learned/recurrent machinery made routing *worse* (§6's R2–R4 ladder). The reason is
Lemma A0 — the value is *which evidence is acquired*, and the closed-form `Q` already ranks acquisition
near-optimally on this geometry, so there is little for an RL policy to add and the recurrent state it would
carry is inert-to-negative.

Even were the headroom larger, an RL-tuned policy in the decision loop reintroduces exactly what RGI's
design excludes:
- **Self-generated signal.** An RL policy improves from its own rollouts — the self-poisoning vector (§5).
  RGI learns only from verified human outcomes, which is what makes its compounding safe to run unattended.
- **Opacity.** A policy network's action is not auditable; the σ/leverage/discriminative terms are. This is
  the inspectability of §6, given up for +1.4 points.
- **Off-policy bias.** Training the router on historically-logged trajectories inherits the action-selection
  bias of the policy that generated them; the closed-form router carries no such training-distribution debt.
- **Cold-start.** A learned router is a separately trained model — it forfeits the zero-label, day-zero
  readiness of §8.

Where learning belongs, RGI already uses it and bounds it. `μ` and `K` are learned from verified outcomes
(§0), and *bounded exploration* is the one place added learning demonstrably helps — category-conditional
exploration eliminated Trading's selection starvation (48.0% → 0.0% of dimensions never tried) while
holding routing quality (74.2% → 74.8%) [chart: pub_cross_copilot_starvation.png / pub_ri5_starvation_comparison.png]
(geometry-derived). RGI confines that exploration to a governed sidecar under the conservation gate, with
promotion and rollback — not to an unbounded RL policy inside the decision loop. And a perfectly RL-tuned
router is still tuned on *some* firm's verified outcomes; the compounding asset (§2) is unchanged by how the
router is parameterized. RL sharpens the mechanism, which §12 concedes is commoditizing; it does not acquire
the substrate, which is the moat.

**Adversarial question — you just haven't tuned the router hard enough; RL will close the gap.** The gap to
close is +1.4 points on routing and negative on recurrence — the closed form is near the ceiling learning
reaches, because A0 shows the value is acquisition and `Q` already ranks it well. Closing even that small
gap with an RL policy costs inspectability, verified-outcome-only safety, off-policy robustness, and
day-zero readiness — four capabilities — and still leaves the firm-specific compounding, the actual moat,
exactly where it was. Learned routing is a governed-sidecar option with small upside, not a decision-loop
default.

---

## 8. Day-zero readiness: competitive before the firm's data exists

*Enterprise buyers increasingly expect a working system before they grant access to their data or an
experimentation window. An RGI copilot is useful from the first decision, and it is honest about the one
thing it cannot know before deployment — the magnitude of compounding on that firm's decisions.*

Two properties of §0 make this real rather than aspirational. The routing that selects evidence,
`argmax Q`, is a closed-form read off the scorer geometry with no separately trained acquisition model, so
there is no cold-start dependency on a learned router. And the scorer is a geometry classifier —
correctness is a nearest-prototype computation over exported geometry — so the system reasons from the
first decision rather than waiting for a training corpus to accrue. Given the same two-read budget, RGI is
within 1.4 points of a trained random forest on category routing with zero training labels, and ties the
full-feature random forest on action accuracy (§4) (real-component + simulated).

The grounding matters and is stated. These experiments are geometry-derived — correctness by
nearest-centroid assignment over exported geometry — a rigorous, annotator-free, reproducible standard for
substantiating *mechanism and capability*, but synthetic. The one quantity it cannot produce is the
*magnitude* of compounding on a specific firm's live decisions; that is measured from real verified
outcomes at deployment and is not synthesizable in advance. This is not a weakness to apologize for — in a
market where the magnitude number is the thing that cannot be faked without being caught, drawing that line
cleanly is the position that survives diligence. The commodity layers that make day-zero readiness possible
can be given away (the engine, the SDK, a reference copilot); the compounding judgment a firm accrues
cannot (§2).

A source-to-pay copilot deployed at a new firm routes and triages invoice exceptions from the first
decision — it needs no labeled training set to begin — and its compounding on that firm's approval patterns
begins accruing immediately and is reported as it accrues, rather than projected as a pre-computed number.

**Adversarial question — your headline numbers are synthetic; why believe any of it transfers?** Believe
exactly what the grounding states. Geometry-derived rules out a toy: these run on the real, exported
decision geometry of five shipped copilots, so they test whether the mechanism operates on the actual
learned structure — and it does. What is synthetic is the verification labels, not the geometry, and the
one quantity held to deployment is the firm-specific magnitude, which no vendor can produce beforehand. A
vendor who cannot tell you which of their numbers is geometry-derived and which is deployment-measured is
the one to distrust; this paper draws that line in every section.

---

## 9. The action frontier: readout-limited, not architecture-limited

*RGI's demonstrated value is in routing and triage — which evidence to acquire and whether to commit. Its
improvement of the final action chosen is, at present, limited — but the limit is in the action readout,
not the architecture or the evidence, and the headroom is large and measured. This is a frontier with a
demonstrated upside and a specific next step, stated as such.*

Throughout the paper, routing and action behave as distinct axes: RGI improves *which* decision to
investigate more readily than *which action* to take. A pessimistic reading would be that investigation
cannot help the action. The oracle-ceiling diagnostic tests exactly that and refutes it. For each copilot,
action accuracy is measured at three points — the current RGI readout at budget two; an *evidence oracle*
(the same readout run on complete, correct evidence — revealing evidence, not the answer); and an *action
oracle* (the maximum the action space allows). The evidence oracle exceeds the current readout by **+47 to
+68 points** on DataOps, Trading, and Purchasing while the action oracle sits at ceiling (architecture gap
≈ 0) [chart: pub_oracle_ceiling_gaps.png] (geometry-derived). The evidence is sufficient to determine the
correct action almost always, and the current readout is not consuming it. The limitation is a *readout*
problem, not an *architecture* one.

This reframes an earlier, gloomier reading. Taken alone, one experiment suggested action improvement was a
marginal, geometry-dependent frontier; the diagnostic shows why — the readout is the binding constraint,
and it leaves 47–68 points of measured headroom. The honest current statement is that RGI is a compounding
decision-*routing* system whose action improvement is a recoverable frontier, not that action improvement
is architecturally out of reach. On DataOps, RGI reliably routes an ambiguous data-quality alert to the
decisive evidence, yet its final remediation captures little of the +55-point headroom the evidence oracle
shows is available — the evidence is there; the action head does not yet use it.

The recoverable-headroom claim implies one specific experiment: an action readout conditioned on the
acquired evidence and the inference trajectory rather than on the routed category alone — the mechanism by
which a real (non-oracle) readout would capture part of the demonstrated gap. That, not further routing
work, is the path from "routing and triage" to "action improvement," and it is named here as the frontier
it is. (The oracle scores are geometry-derived, so the headroom is against the geometry's own oracle;
independent-label validation is the pending rung.)

---

## 10. What RGI does not claim: the operating envelope

For an adversarial reader, the boundaries are part of the result, and the program that produced them
pre-registered what each null or negative outcome would mean before results were in. Consolidated:

- **Magnitude is deployment-only.** Every capability is substantiated at real-component or geometry-derived
  grounding; the magnitude of any effect on a specific firm's live decisions is measured in that firm's
  first weeks and is not synthesizable in advance.
- **Judgment-level specificity is SOC-only.** The moat is routing-level and data-specific on every copilot
  tested; prototype-level specificity holds for SOC and not the other four (§2).
- **The moat is non-transferable, not un-copyable.** State migration collapses the gap; the advantage rests
  on the labels being unobtainable and on a real switching cost, not on impossibility (§2).
- **Applicability is exploratory.** The decision-complexity axis is a low-power (n = 5–6) descriptive
  finding with a constructed multi-enterprise contrast — a targeting frame, not a validated law, pending
  observed multi-enterprise validation (§3).
- **The conservation gate is lagging and domain-scoped.** It detects sustained degradation (9–328 record
  lag), misses fast breaks within its window, and needs per-domain relative-change calibration where base
  accuracy sits near the fixed floor (§5).
- **Abstention lift is domain-scoped.** Strong on SOC, DataOps, Purchasing; near zero on Trading and S2P
  (§5).
- **Action improvement is a frontier.** Readout-limited with 47–68 points of measured headroom against a
  geometry-derived oracle; independent-label validation and an evidence-conditioned readout are pending
  (§9).
- **The operational lifecycle is not built.** The production leg — verified outcomes flowing back to reshape
  geometry in a live loop — is specified but not operational; current evidence is the controlled update on
  exported geometry.
- **The re-convergence (γ) condition is untested in simulation.** It is stated analytically with its
  geometric condition; the simulation confirmation was not completed and is not claimed (§0).
- **A0 is confirmed for the operator tested.** Depth-over-fixed-evidence is inert for the specific
  refinement operator evaluated on geometry-derived cases; this bounds that operator, not every conceivable
  refinement (§6).

These are the honest bounds of a compounding graph-reasoning system that maps its own applicability. The
recurring pattern in them — SOC strong, shallow-decision copilots weak — is not a scatter of defects but
the single characterized property of §3: RGI compounds where decisions are complex, and it can say where
that is.

---

## 11. Competitive positioning

*[To be written as a bulleted comparison: RGI vs graph-RAG, graph-of-agents, uncertainty-conditioned
adaptive retrieval, active feature acquisition, and RL-tuned routing — scored on the axes that matter to
this audience: compounds from verified outcomes · firm-specific moat · no language model in the decision
loop · inspectable mechanism · day-zero / zero-label readiness · governed autonomy. Each row: what the
alternative does, what it lacks, and the RGI difference. Placeholder; content to follow.]*

---

## 12. Related work: adaptive computation without a compounding substrate

RGI composes several established ideas; the contribution is the composition on a compounding,
verified-outcome-grounded graph substrate, not the individual mechanisms, which are themselves
commoditizing.

**Adaptive and recurrent inference-time computation.** Looped and recurrent transformers add reasoning depth
by reusing an operator over a model's hidden state. §6 bears on this directly: over an explicit graph with
evidence held fixed, iterating the operator is inert — depth-as-such is not the value, acquisition is. RGI
pursues the same objective (more reasoning per decision) but locates the value in *what new evidence is
acquired*, over an inspectable graph rather than an opaque latent state.

**Uncertainty-conditioned adaptive retrieval.** A fast-moving line conditions when and what to retrieve on a
model's own uncertainty. RGI shares the intuition and claims no novelty on the mechanism. The distinction is
the substrate on four axes none of these systems combine: no language model in the loop (routing is a
closed-form read off a prototype scorer); enterprise *decisions* rather than question answering; reuse of
the production scorer's parameters with no separately trained router; and acquisition that feeds
*verified-outcome prototype learning* so that what to acquire *compounds* under a conservation gate. The
mechanism is shared and commoditizing; the compounding substrate is the separation.

**Active feature acquisition.** Acquiring features at decision time under a budget, guided by information
value, is a mature area, typically implemented with a separate acquisition model. RGI's routing is instead
a closed-form function of the scorer's own geometry, needs no additional model, and the ranking it uses is
the compounding asset rather than a fixed policy — the source of §4's zero-label competitiveness.

**Recursive self-improvement.** RGI is a deliberately bounded, governed instance: it acquires experience and
reshapes its routing and prototypes from verified outcomes, and excludes self-rewriting of its own
objective by design, because self-generated improvement is where self-poisoning is most acute (§5, §7). The
distinction from the broader agenda is the source of the improvement signal — verified human outcomes over a
graph, not model self-generation — and the governance that bounds it. The recursion is over the judgment
graph, not over model weights.

**Judgment memory.** Reshaping decision geometry from verified outcomes constitutes a persistent, structured
record of which factors predict which outcomes — a memory of *how well decisions are made*, distinct from
episodic event logs, semantic knowledge graphs, and procedural rules. RGI is the inference-time and
learning-time operation on that memory; the memory is the substrate on which every capability here compounds.
