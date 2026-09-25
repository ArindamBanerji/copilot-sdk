# Recursive Graph Improvement: How Compounding Intelligence Makes Enterprise Decisions Get Measurably Better
### The first decision graph whose judgment reshapes from verified outcomes — demonstrated across five enterprise domains

*v7.3. Audience: AI architects and deeply-technical VCs. Every number carries its evidence tier; every
claim we tested and dropped is stated in §10. Adversarial questions sit where the objection is loudest.
Chart placeholders mark where figures will be added.*

---

**The headline result.** We built a system where every verified decision reshapes the math the
next decision is made with — composing prototype scoring, geometric evidence acquisition, and
conservation governance into a single governed loop — and we can now show it, not assert it. On real production decision-geometry,
across all five domain copilots, decision-routing measurably improved from verified outcomes — **routing
quality +17–43%, accuracy +14–32 points, in 5 of 5 copilots, zero regressions** (controlled mechanism
test on real component geometry; tier and ceiling in §10). Two curves that start at the same point on
day 1 and *diverge and stay diverged.* That divergence is the whole thesis, and it is the first thing here
because it is the thing everyone else's system cannot draw.

We tested 15 alternative routing configurations across four design axes — neural recurrence, exploration
policy, temporal weighting, trained routers — and the graph's own geometry beat them all on routing
quality. We ablated the acquisition score into its three component terms and found that leverage
dominates, precision tiebreaks, and the discriminative term awaits heterogeneous variance to activate.
The graph IS the memory. That is not a metaphor; it is the measured result (§5).

We call the property **Recursive Graph Improvement (RGI)**: a system whose decision geometry on a graph
reshapes from verified outcomes and reasons measurably better because of it. RGI is a governed instance
of recursive self-improvement (RSI), bounded at L3 experience-acquisition autonomy and excluding L5
meta-improvement by design. The word "Self" in RSI names the self-poisoning vector RGI excludes:
improvement comes from the verified-outcome judgment graph, not from the model's own parameters.
**CI-VLD is its first working instance.**

---

## 1. The only axis left

Three things that were hard two years ago are commodities now. **The model** improves for everyone at once
and your competitor rents the same one. **Graph engineering** — a knowledge graph to retrieve, a graph of
agents to route through MCP — ships as standard tooling. **Orchestration** — the ten-thousand-agent demo —
is a procurement exercise. All three are real advances; all three stop at the same line: *the graph is
structure the model reads or routes through, the reasoning is the model's, done once, and gone.* Alert
#10,000 is handled exactly like alert #1. *"It learns"* is the most abused verb in this market, because in
almost every system the learning produces a better-informed guess that arrives one step too late and never
changes the decision itself.

So the question that decides enterprise AI is not which model, which graph, or how many agents. It is what
happens **after you ship**: does the system **compound** — get better at *the firm's own decisions* with
every one it makes — or **plateau** on day 1? Everything on the market plateaus. There is exactly one axis
of durable advantage left, and this is it.

> **"Isn't 'it compounds' just online learning / fine-tuning with a new name?"** No, and the distinction is
> the whole design. Fine-tuning changes a *model's parameters* from data it generates or is fed — the
> vector that produces self-poisoning. RGI changes a *decision geometry* from **verified human outcomes** —
> grounded, auditable, reversible. The recursion is over the firm's judgment graph, not model weights; the
> improvement is *outcome-grounded, not self-generated.* That is why it compounds safely and stays
> inspectable rather than drifting. (What we deliberately *don't* let it do: §10.)

## 2. What RGI is — a category shift, not a definition

The industry climbed a ladder and mistook the second rung for the top:

| | What the graph does | After 10,000 decisions |
|---|---|---|
| **Read** (knowledge graph / RAG) | retrieve what's stated | same retrieval — plateau |
| **Route** (graph of agents) | orchestrate work | same routing — plateau |
| **Reshape (RGI)** | **decide, verify, reshape its own decision geometry** | **compounds — +14–32 pts on the firm's own decisions** |

Read and route are *structure.* Reshape is *judgment.* Graph engineering builds a graph that remembers or
wires a graph that routes; **graph-native reasoning runs a graph that decides — and reshapes itself with
every verified decision.** That third rung is RGI, and until now it has been asserted. §4.1 is the first
time it is *shown* on real geometry. Two properties make it safe to claim and to deploy:

- **Bounded and governed.** RGI is a deliberately restrained instance of recursive self-improvement: it
  acquires experience and improves its own routing, but **excludes self-rewriting of its objective by
  design** — because self-generated improvement is where self-poisoning lives. The restraint is the safety
  architecture, not a gap.
- **Inspectable — three artifacts, not a black box.** "Judgment as geometry" is three objects a buyer can
  open and audit, each physically reshaped by verified outcomes: the **centroid geometry μ** (the learned
  prototype of a good decision *here*); the **noise fingerprint σ** (per-factor signal-vs-noise — which
  surfaces *trust traps*: the factor a team trusts most is often its noisiest predictor); the
  **conservation status** (the auditable gate that decides whether the system may act, or must abstain).
  These three artifacts are not diagnostic outputs — they ARE the decision substrate. §3 explains why.

> **"Every vendor says 'it learns.' What's different at the moment of decision?"** Ask the one question
> that matters: *when the invoice must be approved, the alert escalated, or the never-before-seen attack
> contained — what does it do, and does the record of that decision change the next one?* Read retrieves;
> route dispatches; both reason once and forget. CI-VLD **decides or abstains, acts under a gate, verifies
> the outcome, and writes it back into the geometry** — so the next decision is measurably sharper. The
> test isn't whether a system *claims* to learn; it's whether you can *open the three artifacts and watch
> them move.* Here you can.

## 3. Judgment memory — the missing cognitive layer

Enterprise AI systems use three memory classes: episodic (what happened — logs, traces), semantic (what's
true — knowledge graphs, RAG), procedural (how to do it — agent routines, workflows). None of them
reshape from outcomes. None of them change the next decision. RAG retrieves episodic or semantic memory;
agents execute procedural routines; fine-tuning changes model weights but produces something inspectable
by no one and governed by nothing.

RGI introduces a fourth engineering class: **judgment memory** — verified decision outcomes that physically
reshape the geometry the next decision is computed on.

| Memory type | What's stored | What it does at decision time | Reshapes from outcomes? |
|---|---|---|---|
| Episodic | "What happened" | Recall a similar past event | No — retrieval, not reasoning |
| Semantic | "What's true" | Look up a fact | No — static knowledge |
| Procedural | "How to do it" | Execute a learned routine | No — fixed policy |
| **Judgment** | **"What worked HERE"** | **Reshape which evidence to check and how to weight it** | **Yes — every verified outcome changes the geometry** |

**Why this isn't experience replay.** ML practitioners will hear "judgment memory" and reach for
"experience replay buffer" — store (s, a, r, s') tuples and retrain a model. The difference is
structural. Experience replay feeds a training loop that updates model parameters; the result is a
changed model that is neither inspectable nor auditable. Judgment memory directly reshapes three physical
artifacts — no retraining step, no gradient, no model update:

- **Centroids μ** = "what a good decision looks like here" — the learned prototype. When a human confirms
  a decision, the relevant centroid moves toward the verified factor vector. When a human overrides, it
  moves away. The prototype IS the accumulated judgment of every verified decision in that category.
- **K utility weights** = "which evidence dimensions matter here" — the routing memory. When investigating
  a dimension leads to a correct outcome, K_d increases; when it doesn't, K_d decreases. After 500
  decisions, K encodes which evidence was *actually informative* for this deployment's decisions — not
  which evidence the designer *assumed* would be informative.
- **Conservation state** = "how much to trust what we've learned" — the governance memory. θ_min, α, q, V
  together gate whether the system may learn, act, or must abstain. The gate opens as verified evidence
  accumulates and closes if accuracy deteriorates. The system earns the right to act.

**Why "memory" and not "learned prior."** A Bayesian reader will see the centroid update rule
(μ ← μ + η·y·(v − μ)) and translate it into a running posterior mean — which it is, mechanically. The
word "memory" earns its place for three reasons the word "prior" does not carry. First,
**inspectability**: a prior is a distribution parameter inside a model; judgment memory is a physical
artifact a buyer opens and reads. The centroid values, K weights, and conservation state are not summary
statistics of a latent variable — they are the decision substrate itself, stored in a table, auditable by
a non-statistician, and replayable decision by decision. Second, **governance**: a prior updates by Bayes'
rule unconditionally; judgment memory updates only when conservation gates permit — the governance memory
(θ_min) constrains the other two, and that constraint is an explicit, inspectable parameter, not an
implicit regularizer. Third, **verified grounding**: a prior updates from observations; judgment memory
updates from *human-verified outcomes* — confirm or override, not observe. The verification step is what
makes the recursion safe (outcome-grounded, not self-generated) and what distinguishes it from every
form of online learning that updates from its own outputs. These three properties — inspectable, governed,
verified — travel together and justify a term that carries all three rather than one that carries none.

**The connection to §2's three artifacts.** The three inspectable artifacts ARE judgment memory — they are
not diagnostic views of a hidden model; they are the substrate itself. When a buyer audits the system,
they are reading judgment memory directly. When the §4.1 compounding curve diverges from the frozen
baseline, that divergence IS judgment memory accumulating. The inspectability claim and the compounding
claim are the same claim, made concrete in three artifacts.

**Why this matters commercially.** Every competitor's "memory" is one of two things:
- **Retrieval memory** (RAG, knowledge graphs): episodic or semantic. Doesn't reshape the decision. Alert
  #10,000 uses the same scoring as alert #1 — the system retrieves more context but reasons identically.
- **Parameter memory** (fine-tuning, RLHF): reshapes, but into a model that is neither inspectable nor
  governed nor auditable. The self-poisoning vector that EVOMAL documents lives here.

Judgment memory is the third option: **reshapes AND inspectable AND governed.** The geometry moves; a human
can open it and see exactly how; conservation gates prevent it from moving too far. That combination —
compounding that is auditable — is the category CI occupies alone.

> **"If the 'memory' is just three small tensors, how much can it really learn?"** The small dimensionality
> is the mechanism, not the limitation. A 6×4×6 judgment geometry (144 cells) can represent 144 distinct
> decision prototypes — enough to capture the structure of SOC alert triage, where 6 severity categories ×
> 4 action types × 6 evidence factors spans the operational decision space. Each cell accumulates judgment
> from every verified decision that falls in it. The question is not "how many parameters" but "how many
> verified decisions reshape the geometry" — and on a compounding curve, 500 decisions produce +43% routing
> improvement. A 175B-parameter model has more capacity and zero judgment memory.

## 4. What it does — four capabilities, each shown

Four claims survived hostile scrutiny. Each is stated as the consequence, the exhibit that proves it, and
exactly how far the proof goes. Everything that *didn't* survive is in §10 — read it first if you're a
skeptic; it's what makes these four believable.

### 4.1 It compounds — the curve everyone else can only assert
**Consequence.** The copilot gets measurably better at *your* decisions the more it makes — from verified
outcomes, not a bigger model. Day 500 ≠ day 1.
**Exhibit.** Two identical systems from one start; one learns its routing from verified outcomes, one is
frozen. DataOps, real production geometry:

| After N decisions | Routing (learn) | Routing (frozen) | Accuracy (learn) | Accuracy (frozen) |
|---|---|---|---|---|
| 50 | 0.42 | 0.40 | 0.56 | 0.52 |
| 250 | 0.56 | 0.42 | 0.72 | 0.58 |
| 500 | 0.63 | 0.44 | 0.90 | 0.58 |

*Figure 1: K-learning divergence — learned (rising) vs frozen (flat), DataOps, 500 decisions.
See also Figure 2 (all five copilots). [paper_charts/fig_1_k_divergence.png]*

Two lines from a shared origin that **diverge and stay diverged**, plateauing ~500 (confirmed on 2,000
decisions). That shape *is* RGI — the frozen line is every system on the market. It holds across all five
copilots at N=500:

| Copilot | Routing (learn / frozen) | Accuracy (learn / frozen) | Routing Δ |
|---|---|---|---|
| DataOps | 0.630 / 0.440 | 0.900 / 0.580 | **+43%** |
| Purchasing | 0.720 / 0.510 | 0.820 / 0.520 | **+41%** |
| Trading | 0.750 / 0.630 | 0.920 / 0.780 | **+19%** |
| SOC | 0.810 / 0.690 | 0.860 / 0.720 | **+17%** |
| S2P | 0.650 / 0.620 | 0.840 / 0.780 | **+5%** |

Five copilots, **+5% to +43% routing improvement, zero regressions.** The curve is judgment memory
accumulating — K weights reshaping from verified outcomes, centroids sharpening toward each deployment's
decision prototypes.

**The starvation fix.** Under greedy routing, 8–48% of evidence dimensions are never checked (worst:
Trading at 48%). Category-conditional routing (RI-7) resolves this: explore starved categories, exploit
healthy ones. Trading achieves 74.8% routing with 0% starvation — the only tested policy satisfying both
constraints on all five copilots. The system learns where its blindspots are — and fixes them.

**The safety contract: 57 corrections, 0 degradations.** On 250 constructed decision scenarios
(50 per copilot, B=3, ground-truth verified), VLD investigation corrected 57 initially-wrong surface
decisions to the correct action. Zero decisions were degraded — no correct surface score was changed to
an incorrect one. Mean accuracy uplift: +22.8pp across all five copilots. The saves:hurts ratio (57:0,
or 114:1 including copilot-level accounting) demonstrates the mechanism on constructed scenarios.
**Generator limitation:** in this fixture, evidence reads reveal true factor values — there is no channel
for misleading evidence (reads that move the vector toward the wrong action). Zero degradations is
therefore structurally guaranteed by the generator, not a property of the mechanism under adversarial
evidence. A fixture with misleading reads and a binding budget would produce a lower ratio and a more
credible one; that test remains open. The investigation traces are domain-appropriate — SOC
reads threat_intel → pattern_history; S2P reads price_conformance → contract_coverage; DataOps reads
schema_stability → transformation_health. Each trace maps to the graph traversal an analyst would
perform. *Tier: SIMULATED (constructed scenarios, synthetic oracle).* These are not operational
decisions; they demonstrate the mechanism on designed situations. The natural prevalence of "hard"
decisions (where investigation changes the outcome) remains unmeasured — §10 states this directly.

**Budget sensitivity reveals domain structure.** SOC scenarios require deeper investigation — B=4
produces 13 saves versus B=2's 0, because privilege chains and insider threats need 4-factor
corrections. Trading achieves the highest saves at every budget (13 at B=2, 18 at B=3, 22 at B=4) —
the 10-factor geometry with 4 actions produces sharp Q discrimination. Purchasing plateaus at B=2 (11
saves) — the correct 2 dimensions are identified immediately. This is not a parameter to tune; it is
geometry telling you how deep the evidence structure runs in each domain.

| Copilot | B=2 | B=3 | B=4 |
|---|---|---|---|
| SOC | 0:0 | 4:0 | 13:0 |
| S2P | 6:0 | 12:0 | 14:0 |
| DataOps | 8:0 | 12:0 | 15:0 |
| Trading | 13:0 | 18:0 | 22:0 |
| Purchasing | 11:0 | 11:0 | 11:0 |

**Time-to-value: the curve answers "how long until it's worth it?"** RGI compounds at the rate the firm
verifies decisions — not at the rate decisions arrive. Divergence is visible by ~250 verified decisions
and plateaus by ~500. At a $7B industrial manufacturer (the reference firm for these estimates):

| Copilot | Decision volume | Verified/week | Diverges | Plateaus |
|---|---|---|---|---|
| SOC | 400 analyst-triaged alerts/day | ~1,200 | 2-3 days | <1 week |
| S2P | 108 invoice exceptions/day | ~486 | 3-4 days | ~1 week |
| Purchasing | 66 reorder decisions/day | ~231 | 5-8 days | 2-3 weeks |
| DataOps | 25 pipeline incidents/day | ~106 | 2-3 weeks | 5-6 weeks |
| Trading | 4 hedge decisions/day | ~19 | ~3 months | ~6 months |

*Tier: ILLUSTRATIVE — volume and verification-rate estimates from industry benchmarks, not measured at a
specific firm. K-curve divergence/plateau points are REAL_COMPONENT (from KE-1).*

**The 90-day deployment sequence follows the mechanism, not the sales map.** S2P and SOC compound fastest
(tight verification loops, high volume) — deploy first. Purchasing follows (moderate volume, supplier-
specific learning). DataOps takes longer (fewer daily incidents, richer graph structure). Trading is the
long game (low volume, but highest per-decision value). The mechanism picks the GTM order: lead with the
copilots whose verification loops are tightest, expand into the domains whose graph complexity produces
the deepest moats.

**What a design partner supplies:** a decision stream and verified outcomes. No labeled training data, no
fine-tuning corpus, no model retraining. The system earns its judgment memory from the partner's
operational process. The first 500 verified decisions produce the compounding curve; the first 90 days
can put 2-4 copilots past divergence.

**When verification slows — analysts stop confirming, review cadence lapses — the geometry freezes at its
current quality.** It does not degrade (conservation prevents that), but it stops compounding. The
conservation gate addresses the "too much autonomy" direction; sparse verification addresses the "too
little signal" direction. Both bound the system: one from above, one from below.

**The exported geometry is pre-compounding.** All five copilots export σ=1.0 (uniform variance across
every factor dimension). σ differentiates from verified outcomes — that is the mechanism itself — so
uniform σ means these exports have not yet accumulated differentiating evidence. The synthetic
verification stream is precisely why: it demonstrates the compounding mechanism on geometry that has not
yet compounded, which is the starting condition every new deployment faces. σ differentiation is the
first observable a design partner will produce; its absence here is the operating envelope, not a gap.
**Tier.** REAL_COMPONENT — real pre-compounding geometry, synthetic verification; a controlled mechanism
test, not live-operational value (§10).
**Un-copyable.** A competitor can add a learned retriever tomorrow; they cannot make what it learns *be the
firm's own accumulated judgment* — earned from decision history, not shipped in a model. The first mover
per domain compounds a lead nothing static closes.

> **Sidebar: One decision, end to end — how K changes what the system reads**
>
> S2P-SC2 is a planted fixture that makes the K mechanism concrete. An invoice at $47,200 against a
> $42,000 PO arrives. Surface score: 12.4% variance → flag_leakage. Two reads budgeted.
>
> *At startup (K uniform at 0.5).* Q ranks match_status first (Q=0.474), amount_variance_ratio second
> (Q=0.200). The system reads contract coverage → pricing benchmark. Nothing changes the variance
> signal. Action: flag_leakage. Correct for the geometry — but it missed the commodity index data at
> dim 5 (value 0.82) that would have flipped the decision.
>
> *After learning (K₅ = 1.0, others at 0.5).* Q still reads match_status first (highest base Q). But
> now dim 5 (commodity_index_correlation) beats dim 1: 0.16 × 1.0 > 0.1998 × 0.5. Second read goes to
> commodity context instead of pricing variance. With that evidence: auto_approve. The invoice variance
> was within the commodity index corridor.
>
> *What it took to learn.* K₅ must exceed 0.624375 to beat dim 1 — seven idealized +0.02 updates from
> 0.5. Reaching 1.0 takes 25 credited updates, assuming no negatives. These are not guaranteed decision
> counts: the system must first encounter decisions where dim 5 is read (via exploration or other
> categories), receive verified outcomes, and earn the credit. The walkthrough demonstrates that the
> K mechanism produces a reachable, bounded change in evidence priority — not that 25 decisions will
> always suffice or that the learning path is deterministic.
>
> *Evidence tier: PLANTED FIXTURE.* The K vector is injected, not learned. KE-1 separately measures
> synthetic K learning on the same exported geometry. This is a designed demonstration of the acquisition
> effect, not an operational learning history.
>
> *[Source: S2P-SC2 reachable-K analysis, prepaper v10 §XI]* — the system earns the right to act, or declines
**Consequence.** On the decisions it commits to, accuracy is dramatically higher — because it reliably
identifies the fraction it would get wrong and declines to act on them.
**Exhibit.** Act on the confident cases, abstain on the rest. Accuracy on acted-upon:

| Copilot | Coverage | Act on everything | Act on confident subset | Lift |
|---|---|---|---|---|
| DataOps | 90% | 77.9% | 81.3% | +3.4 pts |
| DataOps | 75% | 77.9% | 87.4% | **+9.5 pts** |
| DataOps | 50% | 77.9% | 94.0% | **+16.1 pts** |
| Purchasing | 90% | 77.0% | 83.6% | +6.6 pts |
| Purchasing | 75% | 77.0% | 92.2% | **+15.2 pts** |
| Purchasing | 50% | 77.0% | 98.0% | **+21.0 pts** |
| SOC | 90% | 91.5% | 95.6% | +4.1 pts |
| SOC | 75% | 91.5% | 100.0% | **+8.5 pts** |
| SOC | 50% | 91.5% | 100.0% | +8.5 pts |

*Figure 4: Risk-coverage curve — coverage vs accuracy-on-acted, DataOps/Purchasing/SOC.
Post-investigation d_min strictly monotonic. [paper_charts/fig_4_risk_coverage.png]*

Strictly monotonic — decline more and accuracy-on-acted keeps rising. The tradeoff is smooth, not
cliff-edge: even at 90% coverage (decline only 10%), you gain +3–7pp.

**Mechanism (the part that matters).** It works only on **post-investigation confidence.** Every surface
signal — margin, distance, entropy measured *before* investigating — is non-monotonic and fails. *The
system cannot know what it doesn't know before it investigates; the investigation produces the
calibration.* (A naive pre-investigation version on the same SOC fixture failed outright — 86% abstained,
17.6% accuracy on the rest versus 21.6% single-pass. Same experiment, mechanism-correct signal, opposite
result.)

This is judgment memory in action: the confidence the system uses to decide whether to commit is not a
model's prior — it is the distance to the nearest *learned centroid* in the *enriched* factor space. That
centroid was shaped by verified outcomes. The abstention quality is a direct consequence of judgment memory
quality.

**Tier & boundary.** REAL_COMPONENT. Abstention spends the full budget — the value is *fewer committed
errors, not fewer reads.* A quality-and-safety claim, not a cost one.
**Un-copyable.** A confidence-thresholded LLM thresholds on what it knew *going in*; CI-VLD thresholds on
what it knew *after reasoning over the firm's judgment geometry.* Investigation-produced calibration is a
property of the substrate, not the threshold.

### 4.3 The right evidence — not fewer checks, the *right* checks
**Consequence.** Facing many things it could investigate, it reads the two or three its own geometry says
are decisive — reaching most of exhaustive-investigation quality at a fraction of the work.
**Exhibit.** VLD at a 2-read budget, as a fraction of exhaustive:

| Copilot | Investigable dims | 2 reads vs exhaustive |
|---|---|---|
| SOC | 6 | **91.7%** |
| Trading | 10 | **90.7%** |
| DataOps | 6 | **84.4%** |
| S2P | 8 | **84.1%** |
| Purchasing | 7 | **79.8%** |

*Figure 3: Budget-accuracy frontier — B=2 achieves 80–92% of exhaustive across all 5 copilots.
[paper_charts/fig_3_budget_frontier.png]*

**80–92% of exhaustive-investigation accuracy at 20–33% of the reads** — because judgment memory (the
learned K weights) tells the Q heuristic which dimensions have been informative for *this deployment's*
decisions, and the geometric terms (precision, discriminative, leverage) tell it which dimensions would
move *this specific* decision.

**Reframe (from a negative).** We tested early halting (adaptive C4 convergence); it cannot read
fewer than two because wrong-first-step recovery (VLD-SOC-2) requires the second read. At higher budgets,
the system reads MORE (2.2–2.7 reads at B=4) and gains +5–10pp accuracy. The efficiency claim is
*selection quality*, not brevity: "the right two reads," not "fewer reads." (Stated as "fewer reads," a
reviewer answers "so does a smaller top-k"; stated as "the right reads," there is no such rejoinder.)
**Tier.** REAL_COMPONENT; exhaustive = 100% *by construction* (synthetic oracle), so this is "% of a
synthetic ceiling," not "% of human accuracy."

### 4.4 The graph is its own memory — neural recurrence is overhead
**Consequence.** We tested every recurrence mechanism the field builds — RNN, GRU, LSTM, sequence memory,
temporal decay, trained routers, lookahead planning — and the graph's own geometry beat them all on
routing quality. The compounding comes from the graph, not from a neural network bolted onto it.
**Exhibit.** The routing × K interaction experiment (RI-1), DataOps, all on real geometry:

| Routing variant | K-Fixed routing | K-Learning routing | K lift |
|---|---|---|---|
| Static (graph only) | 51.9% | **60.8%** | +8.9pp |
| RNN | 46.5% | 56.6% | +10.1pp |
| GRU | 46.2% | 50.6% | +4.4pp |
| LSTM | 46.0% | 48.6% | +2.6pp |

The ranking does NOT flip under K learning: Static > RNN > GRU > LSTM with and without K. Static+K —
the graph's own learned weights with no neural recurrence — leads routing. RNN+K leads accuracy (78.2%
vs 75.2%, a 3pp gap that may justify the extra scorer call in production). But the *routing value* comes
from K learning (R2), not from within-decision recurrence (R1).

*Figure 5: RI-1 interaction heatmap — Static > RNN > GRU > LSTM, with and without K.
Static+K leads routing at 60.8%. [paper_charts/fig_5_ri1_heatmap.png]*

**The five-level recurrence taxonomy.** We organized investigation recurrence into five levels and tested
each independently:

| Level | What recurs | Where state lives | Finding |
|---|---|---|---|
| R0 Static | Nothing (fixed plan) | — | **Leads routing** (60.8% with K) |
| R1 Within-episode | Hidden state per read | RNN/GRU/LSTM h_t | All underperform static |
| R2 Between-decision | K utility weights | KUtilityStore | **Dominant effect** (+3–21%, 0 hurts) |
| R3 Cross-episode | Trajectory patterns | Trajectory store | Not tested (needs Tier 6) |
| R4 Cross-copilot | K transfer across domains | Factor-name map | Not testable (zero overlap) |
| R5 Temporal / regime | Time-weighted K | Decay / indexed | Decay hurts; regime validates production |

R2 is the mechanism. The graph remembers through judgment memory — centroids, K weights, conservation
state — not through a bolted-on neural network. This is why the system is inspectable: the "memory" is
three auditable artifacts (§2), not a hidden state vector no one can read.

**Twelve killed alternatives (equally important).** We tested and rejected: temporal K decay (all λ>0
hurt routing, RI-6), sequence-aware Q (helps DataOps +2.2pp but destroys SOC −14.4pp, RI-8), MCTS
lookahead (−31pp at 15× scorer cost — wrong objective at B=2, RV-9), risk-sensitive adaptive budget
(more reads ≠ better routing — SOC loses 36pp at B=5, RV-4), and hierarchical C4→RNN (needs a trained
6-class classifier that doesn't exist, RV-5). Each is a measured negative, not an untested alternative.

**Tier.** REAL_COMPONENT. 15 configurations × 5 copilots × 5 seeds = 375 experimental cells, each with
pre-registered kill/keep criteria and a three-metric protocol (M-VALUE routing/accuracy, M-COST
scorer-calls-per-decision, M-GOV inspectability/replay).

## 5. The Q equation — what it is, which terms matter, and why

The acquisition score that drives evidence selection is a closed-form geometric heuristic over the
centroid geometry. No neural network. No training data. No gradient. Three additive terms, each
computable from the decision substrate:

**Q_d = K_d × [ precision_d + discriminative_d + leverage_d ]**

where:

- **precision_d = 1 / (100 × max(σ²_d, 0.001))** — how reliable this dimension's evidence is. Low
  variance (precise measurements) means high precision. In production with learned σ from verified
  outcomes, this term routes toward dimensions with consistent, trustworthy evidence. At startup (σ=1.0),
  precision is a constant and does not discriminate.
- **discriminative_d = |μ_{a1,d} − μ_{a2,d}|** — how much the top two action centroids disagree on this
  dimension. High separation means this dimension is decisive for choosing between the leading
  alternatives. In production with heterogeneous centroid structure, this term routes toward dimensions
  where the decision genuinely depends on the evidence. At startup (σ=1.0), this term can interfere with
  leverage (§5.1 explains why).
- **leverage_d = |(v_d − μ_{a1,d})² − (v_d − μ_{a2,d})²|** — how much this dimension would *move this
  specific decision* if the evidence changed. High leverage means the current observation sits at a point
  where new evidence would shift the action choice. This is the only term that depends on the current
  factor vector v, making it situation-specific rather than geometry-generic.

**K modulates multiplicatively** — the learned utility weight from §4.1. After 500 decisions, K encodes
which dimensions were *actually informative* for this deployment's decisions. K turns a geometry-generic
heuristic into a deployment-specific one. Without K: routing at 46–63%. With K: routing at 59–81%
(the +17–43% headline).

### 5.1 Q term ablation — which terms do what

We ablated Q into all 7 combinations under three normalization regimes — RAW (un-normalized), Z-NORM
(z-score per component across dimensions), and MINMAX (min-max to [0,1]) — across all 5 copilots
(575 experimental cells total, 115,000 evaluation episodes):

*Figure 6: Q term ablation — RAW (magnitude artifact) vs Z-NORM (three-term form correct) vs MINMAX.
575 cells, 115K episodes. [paper_charts/fig_6_q_ablation_normalized.png]*

**The un-normalized finding was a magnitude artifact.** At σ=1.0, the three Q terms have different units
and scales: precision = 0.01 (constant), discriminative = O(0.01–1.0), leverage = O(0.01–10.0). Adding
these raw and concluding the biggest term is most informative measured arithmetic dominance, not
information content. Under z-normalization, each term contributes at its natural information scale:

| Normalization | Leverage-only | P+L vs ALL-THREE | Finding |
|---|---|---|---|
| RAW | 70.5% | +4.6pp (all 5 copilots) | Magnitude artifact |
| Z-NORM | 65.1% | −0.8pp (CI includes zero) | Three-term form correct |
| MINMAX | 69.3% | +0.2pp (CI includes zero) | Three-term form correct |

**Three findings from the normalized lattice:**

**1. Leverage is the strongest single term — this holds under all normalizations.** L-only leads the
single-term ranking at 70.5% (RAW), 65.1% (Z-NORM), and 69.3% (MINMAX). The routing question "which
dimension would move *this* decision?" is more informative than "which dimension separates the centroids?"
or "which dimension is most precise?" This is an information finding, not a scale artifact.

**2. The three-term form is not suboptimal.** Under z-normalization, ALL-THREE matches or slightly beats
P+L (−0.8pp, CI includes zero). The discriminative term is not interfering — it was swamped by leverage's
larger magnitude in the un-normalized version. Once scales are equalized, all three terms contribute.

**3. Normalized precision contributes zero at σ=1.0.** This is structural: when all σ values are
identical, z-normalizing precision produces a constant (zero variance → zero z-score). With learned σ
from verified outcomes (heterogeneous per dimension), precision will differentiate. The normalization
result predicts that learned σ activates the precision channel without requiring it to be tested.

> **Sidebar: The σ trust-trap — a falsifiable prediction from the geometry**
>
> The exported σ=1.0 geometry reveals a structural pattern that production deployments will encounter.
> In each copilot's factor space, human teams develop habitual confidence in specific evidence sources —
> the SOC analyst who trusts threat_intel above identity_context, the procurement team that weights
> supplier_history over commodity_index. Those habits are reasonable but often encode which evidence is
> *checked most*, not which evidence is *most reliable*.
>
> Once σ differentiates from verified outcomes (Phase 2 of centroid learning, §2.3), the precision
> term in Q becomes live: 1/(100 × σ²_d) will be high for low-noise dimensions and low for noisy ones.
> If a team's trusted source turns out to have high variance (measured, not assumed), the precision term
> will DOWN-weight it even if K UP-weights it from frequency of use. The two terms act as opposing
> forces: K says "we always check this"; precision says "but its evidence is unreliable."
>
> **This is falsifiable.** The prediction: once σ heterogeneity exceeds the noise_ratio > 1.5 threshold
> (triggering DiagonalKernel, §2.2), at least one dimension per copilot will show K > 1.0 and
> precision below median — the trust-trap signature. If no deployed copilot shows this pattern after
> 500+ verified decisions, the trust-trap hypothesis is wrong. The data to test it is a single σ
> export from a design-partner deployment.
>
> *The σ=1.0 export cannot show this.* The precision term is 0.01 on every dimension — a constant that
> contributes nothing to routing. The normalized ablation (§5.1) confirms: precision contributes zero
> discriminative information at uniform σ. The trust-trap diagnostic is a production-geometry prediction,
> not a simulation result.*

**The normalized ablation corrects the un-normalized result and strengthens the design:** the three-term
Q equation is correct as designed. The +1.4pp trained-router headroom (RV-8) is not explained by
"downweighting discriminative" — it comes from somewhere else in the routing geometry, and its small
magnitude confirms the closed-form heuristic captures nearly all available routing value.

**K is the mechanism; Q terms are the routing within K.** NO-K drops 0.6–19pp vs ALL-THREE. RANDOM is
the floor at 30–37%. The overwhelming routing value comes from K learning (§4.1), not from which terms
appear in Q. The Q equation selects *which* two dimensions to read; K determines *how much* to weight
them. The dominant contribution is K.

### 5.2 The trained-router headroom is small and uncharacterized

RV-8 measured +1.4pp headroom between the closed-form Q and a trained linear router on DataOps. The
normalized ablation rules out the original explanation (that the trained router downweights discriminative).
Under z-normalization, discriminative contributes positively; the headroom comes from elsewhere in the
routing geometry — likely the trained router's ability to adapt weights per decision rather than using
fixed coefficients. The no-trained-router separator holds: +1.4pp is small, the geometric heuristic
captures nearly all routing value without model training, without training data, and without the
self-poisoning vector that trained routers carry.

## 6. One engine, five copilots — the generality is the proof

The four capabilities are one operator over five domains, not five hand-tuned systems. Under all of them:
the **Graph Attention Engine (GAE)** and a fixed set of governed decision-loops. Formally, every copilot is
the same object:

- A decision is a factor vector **v ∈ ℝ^d** read from the graph; the scorer is a prototype classifier over
  judgment memory **Θ = {μ centroids, σ noise, K utility, τ calibration}**, readout
  **a\*(v) = argmin_a ‖v − μ_{c,a}‖²_DK**, confidence **p(v) = softmax(−d²/τ)**.

- Investigation is a **state-conditioned recurrence** (the VLD step), each pass reading *new* evidence
  judgment memory itself selects:
  **v_{t+1} = Reshape(v_t, e\*_t), e\*_t = graph_read(k\*_t), k\*_t = argmax_k Q(k; v_t, Θ)**

- Every verified outcome updates judgment memory:
  - **Centroid update:** μ ← μ + η·y·(v − μ), with η_confirm = 0.05, η_override = 0.01
  - **K update:** K_d ← clip(K_d + η_K · reward_d, 0.1, 3.0), with +0.02/−0.005
  - **Conservation gate:** θ_min = 23.53/(α·V), signal = α·q·V; GREEN/AMBER/RED
  *The operator that decides is the operator that reshapes* — that is RGI.

Copilots differ only in tensor shape — **SOC 6×4×6, Trading 5×4×10, Purchasing 5×4×7, DataOps 6×5×6, S2P
5×5×8** (situations × actions × factors) — and in their verified-outcome stream. One operator producing the
compounding curve on all five shapes is the generality claim, and why a lesson about *how to reason* is
substrate-level, not domain-level.

**The self-validation question.** The five copilots are CI's own deployed copilots, built by CI, with
factor spaces chosen by CI. A skeptic will say: "you tested your own system on your own data — that's
internal consistency, not external validation." The distinction matters and we state it plainly. What
REAL_COMPONENT already establishes: the geometry is exported from production — not fabricated for the
experiment — so the mechanism test runs on the actual learned structure. What it does NOT establish: that
independently-designed factor spaces, independently-chosen categories, or independently-verified outcomes
would produce the same result. The path to external validation is a design-partner deployment where the
factor space is co-designed with a domain owner, the verification stream comes from their operational
process, and the compounding curve is measured on their live decisions. That experiment has not been run.
We claim mechanism validity on real geometry; we do not claim generalization beyond the systems we built.
The S2P consistency signal (weakest on every axis, §4.4) is itself a structural prediction — it would
not survive fabrication.

**Wedge-and-expand.** Source-to-pay and restaurant purchasing are the revenue wedge (dollar-legible
decisions, fast-arriving outcomes); trading is the open-sourced community reference application; security
operations and data operations are the expansion path (highest stakes, richest evidence chains, strongest
RGI signal). The bimodal result is the GTM guide: expansion follows the mechanism (where multi-step
evidence structure is richest), not the sales map.

> **"Five 6-to-10-dimensional tensors is a small model. Is this even 'AI' at the scale that matters?"** The
> small dimensionality is the mechanism, not the limitation. Judgment memory that compounds lives in a
> *low-dimensional, inspectable decision geometry* so that every factor's contribution is auditable (the σ
> trust-trap diagnostic only means something because d is small), the recurrence is matrix–vector cheap
> (sub-ms, no GPU, no LLM/hop), and verified outcomes have enough leverage to *move* the geometry in
> hundreds of decisions, not millions. A 175B-parameter model has more capacity and zero judgment memory;
> a 6×4×6 judgment geometry has less capacity and *all* the judgment memory. The scale that matters is the
> decision, and the decision is low-dimensional.

## 7. Open source — give away the commodity, keep the compound

We are open-sourcing the layers this paper has argued are commoditizing: the **Graph Attention Engine
(GAE)**, the **copilot-SDK**, and the **trading copilot** as a full reference application. The objection is
obvious, so we meet it directly.

**Moat-consistent.** The engine is on the commodity side of the line; the moat is on the other. What GAE
*is* — attention over a graph, prototype scoring, the VLD recurrence, the conservation gate — is in the
equations above and reproducible by a competent team; there is no defensibility in hiding it. What GAE
*is not* is what makes a deployment valuable: **the firm's accumulated judgment memory — Θ and K after ten
thousand of that firm's decisions.** Open source ships the operator; it cannot ship the fixed point the
operator converges to on your data. Clone the repo tonight and you start, as everyone does, at day 1 of
the flat line.

**Adoption / standards.** Open-sourcing the engine is how CI becomes the **default substrate others build
judgment on.** Every team adopting GAE for its inspectability and no-LLM economics accrues its decision-
geometry *in our substrate's format*. Formally: **we open-source the operator family and the mechanism
(VLD, Q, conservation); we do not — and structurally cannot — open-source the judgment memory Θ, K a firm
earns.**

> **"A well-funded incumbent forks GAE, wires it to their customer base, and out-compounds you. What stops
> them?"** Three things. First, **compounding is per-firm and non-transferable** — the incumbent's own
> customers each start at day 1; the fork ships the engine, not their customers' earned geometry, and (§10)
> judgment doesn't transfer even between *our own* copilots without a shared factor space. Second,
> **first-mover-per-domain compounds an opening lead a later entrant is always chasing** on the same rising
> curve. Third: an incumbent adopting GAE is adopting our substrate, inspectability model, and governance
> semantics *as the standard* — that is the adoption win.

**The moat, made numeric.** The learn-vs-frozen gap *is* the deficit a fast-follower inherits. From the
KE-1 per-checkpoint data on real geometry:

| Copilot | Gap at 250 decisions | Gap at 500 decisions | Calendar at reference firm |
|---|---|---|---|
| Purchasing | +15.0pp routing | +21.0pp routing | 1 week → 2-3 weeks |
| DataOps | +14.0pp routing | +19.0pp routing | 2-3 weeks → 5-6 weeks |
| SOC | +12.0pp routing | +12.0pp routing | 3 days → 5 days |
| Trading | +9.0pp routing | +12.0pp routing | 3 months → 6 months |
| S2P | −3.0pp routing | +3.0pp routing | 4 days → 1 week |

*Gap values: REAL_COMPONENT. Calendar conversions: ILLUSTRATIVE ($7B manufacturer estimates).*

An entrant starting N weeks later begins at the frozen line and must climb a curve the leader is already
climbing — on a compounding axis where the lead widens before it stabilizes. The follower's deficit is
not a head start on a shared track; it requires the follower's OWN verified decisions to close, and those
decisions take the same calendar time, produce geometry-specific learning, and cannot be borrowed, bought,
or transferred from the leader's deployment.

**S2P's moat is shallow (+3pp).** S2P is the GTM wedge — fast verification, dollar-legible, easy to prove
value — not the GTM moat. DataOps (+19pp) and Purchasing (+21pp) are the moat domains: deep gaps, supplier-
specific and graph-specific patterns that take weeks to earn and cannot be replicated without the firm's own
operational decisions. The mechanism predicts its own commercial sequencing.

## 8. What this changes — the economics of compounding judgment

**Decision-making moves from the model to the firm's judgment.** Today the unit of intelligence is the
*model* — rented, static between releases, improving for everyone (so an advantage to no one). RGI moves it
to **the firm's accumulated judgment memory** — proprietary, compounding, improving only for whoever
verifies outcomes. Reasoning becomes an *owned, appreciating asset*; Θ and K are how it's represented, the
§4.1 curve is it appreciating.

**Decision-storage moves from logs to judgment memory.** Enterprises store decisions as *logs* — inert
records of what was decided. RGI stores them as **judgment memory** (§3): verified outcomes that physically
reshape the geometry. A log tells you what was decided; judgment memory tells you *what was learned from
deciding* — and uses that learning next time.

**The economic structure: compounding + non-transferable + first-mover = winner-take-most per domain.**
Three properties compose into a market structure:

*Compounding:* The system measurably improves with use (+5–43% routing over 500 decisions). A static
system's value is constant from day 1; a compounding system's value increases. The integral under the
rising curve exceeds the rectangle under the flat line starting at any deployment month.

*Non-transferable:* Judgment memory is earned from the firm's own verified decisions. It cannot be copied
(the geometry lives in the firm's deployment, not a shared model), transferred (L4 cross-copilot: zero
factor overlap, null result — §10), or approximated (K weights encode which evidence was informative for
THIS firm's decisions, not general domain knowledge). Open-sourcing the engine gives away the operator,
not the fixed point.

*First-mover per domain:* The follower starts at the frozen line. Closing the +3 to +21pp gap requires
their own verified decisions at the same calendar rate. During that time, the leader continues to
compound (though returns diminish past ~500 decisions). This is not winner-take-all — a competitor can
deploy in a different domain or at a different firm. But within a firm×domain, the first deployment
past plateau has a structural lead.

**What the customer buys.** Factor-space design for their domain (which dimensions to score, which evidence
sources map to each), verification-loop engineering (how verified outcomes flow back into geometry
updates), and the first 500 decisions' worth of compounding. After that, judgment memory is the lock-in —
it lives in our substrate, the next copilot (domain expansion) comes from us, and the alternative is
starting at day 1 of a fresh flat line.

**The open-source play as land-grab.** Open-source GAE + copilot-SDK → community adoption → every
adopter's judgment memory accrues in our substrate format → CI becomes the default judgment substrate.
The revenue layers: design-partner services (co-design), managed judgment memory (hosted compounding),
and domain expansion (each new copilot is the same engine on new geometry).

## 9. The routing category — where RGI beats what others build

On 543 SOC fixture alerts (the same geometry as §4.2's abstention experiment), CI-VLD's geometry-directed
routing recovered the correct alert category at 68.5% versus 30.0% for majority routing (+38.5pp). The
routing mechanism — which evidence to check — works.

The caveat: final-action accuracy on the same fixture *fell* (31.3% vs 53.8%), meaning the system
routes to the right category but struggles at action-level discrimination within that category. Category
routing works; action discrimination is the remaining gap. **Both numbers are reported because reporting
only the positive one misrepresents the finding.** The same geometry that succeeds at category routing and fails
at action discrimination is the finding — it tells us exactly where the remaining work is.

**The 2026 wave and why it's a foil, not a threat.** The components in CI's composition are individually
commoditizing. Self-reflective retrieval (SELF-RAG, Asai et al., ICLR 2024) learns when to retrieve and
critiques its own outputs. Uncertainty-conditioned adaptive retrieval (Dey et al., arXiv 2607.07380,
SIGIR'26 workshop) uses hidden-state uncertainty to trigger retrieval. In-context active feature
acquisition (Learning-to-Measure, Kobayashi et al., arXiv 2510.12624) learns acquisition policies
across tasks with greedy mutual-information selection. Each demonstrates one element CI uses. None
composes all four substrate properties that produce the compounding curve:

- **No LLM in the acquisition loop.** CI's Q is closed-form from scorer geometry. The routing cost is a
  matrix-vector product, not an LLM call. SELF-RAG and the uncertainty framework require LLM inference
  per retrieval decision.
- **Enterprise action centroids, not document relevance.** CI routes to named factor dimensions of a
  decision geometry, not to documents in a corpus. The acquisition target is "which evidence changes
  *this* decision," not "which passage answers *this* question."
- **Scorer-parameter reuse.** Q reads the same μ, σ, K that the scorer uses to classify. No separate
  router model, no separate embedding space, no separate training loop. L2M trains a separate
  autoregressive model for acquisition; CI's acquisition function is derived from the classifier's own
  parameters.
- **Verified-outcome compounding under conservation governance.** The K weights that change routing
  quality are updated from verified human decisions, bounded by K ∈ [0.1, 3.0], and gated by conservation.
  SELF-RAG's reflection tokens do not compound from verified outcomes; L2M's meta-learning does not
  retain deployment-specific acquisition state.

**The composition, not the loop, is the contribution.** Any of these teams could add a learned retriever
tomorrow — but coupling it to a verified-outcome compounding substrate, under conservation governance,
on enterprise decision geometry, without an LLM in the acquisition path, is the composition CI has built
and measured across five domains. The mechanism is replicable; the §7 moat arithmetic shows why the
*result* of running it is not.

**Tier.** REAL_COMPONENT (real geometry, synthetic fixture).

## 10. What we are *not* claiming — the map, and the ceiling

Everything above is believable in proportion to what we'll say we haven't shown.

**The recursion ladder — how far up, and why we stop.** RSI has five autonomy levels (execute → strategize
→ acquire-experience → adapt-environment → rewrite-the-objective). CI-VLD occupies **L1–L3 and stops on
purpose:**
- **L1 execute / L2 strategize / L3 acquire-experience — demonstrated** (the compounding curve, geometry-
  directed investigation, routing memory K).
- **L4 cross-domain adaptation — NOT claimed; it is a null result.** Transfer across three copilot pairs
  showed *zero* exact factor-name overlap; cold-start equalled warm-start. Judgment memory does not
  transfer between domains without a shared factor space we have not built. "A lesson in one domain
  transfers to the next" is **not supportable**, and is removed.
- **L5 self-rewriting of the objective — excluded by design.** Where self-poisoning lives. Boundedness is
  the safety architecture, not a missing feature.

**Six more retractions:**
- **"Saves reads / saves cost" — retracted (negative result).** Adaptive halting can't read fewer than two
  (C4 residual halt requires 2 acquired reads by design). The efficiency claim is *selection quality*.
- **Grounded dollar figures — illustrative only.** The $0.9M and $1.62M in circulation are *modeled*.
  No dollar claim is grounded in measured customer outcomes.
- **Calibrated abstention was harder than it looked.** Naive pre-investigation version failed — 86%
  abstained, worse on the rest. §4.2 works only because it thresholds *post-investigation* confidence.
- **Conservation is inert at this scale.** KE-5: 10.2 decisions blocked early, same final routing.
  The safety value is in the bound (K ∈ [0.1, 3.0], θ_min gate), not in frequent intervention.
- **Temporal decay, sequence bias, MCTS — all killed.** RI-6: all λ>0 hurt. RI-8: SOC −14.4pp. RV-9:
  −31pp at 15× cost. RV-4: SOC loses 36pp at B=5. RV-5: needs trained classifier. Each measured.
- **Un-normalized Q ablation was a magnitude artifact.** The initial finding that P+L outperforms
  ALL-THREE (+4.6pp) did not survive z-normalization: under equalized scales, ALL-THREE matches P+L
  (−0.8pp, CI includes zero). The three-term form is correct as designed (§5.1). The methodology caught
  its own mistake in 575 additional experimental cells.

**The ceiling on the headline numbers.** Every §4 result is **REAL_COMPONENT**: real, exported decision-
geometry of five shipped copilots, with synthetic verification labels. The compounding, calibration,
selection, and recurrence findings are demonstrated *on the actual learned structure* — not a toy — but the
last mile, *that they move a firm's live decisions and P&L*, is a validation we have **not** run and do
**not** claim. The self-validation question (§6) is stated directly: we claim mechanism validity on real
geometry, not generalization beyond the systems we built.

> **"You just spent a page on what you can't prove. Why is that a pitch?"** Because on a compounding,
> safety-critical decision system sold to auditors and CISOs, **the retractions are the product.** A system
> that claims to self-improve is one that can self-poison — so testing transfer and finding null, halting
> and finding negative, naive abstention and finding failure, twelve routing alternatives killed,
> discriminative Q characterized and bounded, and *excluding L5 on purpose* is not a list of weaknesses;
> it's evidence the same discipline governs the running system. The four capabilities in §4 are worth
> exactly as much as this section is accurate — and no more. We think that's the highest price they can
> command.

## 11. Where this stands

RGI is demonstrated — judgment memory compounds decision quality from verified outcomes, on real geometry,
across five copilots, zero regressions; the system earns the right to act or declines, with post-
investigation calibration; it selects the decisive evidence, 80–92% of exhaustive at a third of the reads;
and the graph's own geometry outperforms neural recurrence on routing quality. The Q equation's three
terms are individually characterized: leverage dominates, precision tiebreaks, discriminative awaits
heterogeneous σ. It is bounded (L1–L3), governed (conservation-gated, L5 excluded), inspectable (three
auditable artifacts that ARE judgment memory). The engine, SDK, and a reference copilot are open; the
firm's judgment memory is not, and structurally cannot be.

The compounding rate is bounded by verification throughput — the system freezes when verification stops,
but does not degrade. The path to revenue is a design-partner deployment with co-designed factor spaces
and operationally-verified outcomes. On a compounding curve, the value of starting is highest today.

*The model is a commodity that improves for everyone. CI makes the firm's own verified judgment the thing
that compounds — owned, governed, inspectable, and demonstrably rising. That is the shift: from renting a
model that reads a graph, to owning a judgment memory that recursively improves the decisions it makes.*

---

## Appendix A: Equation Reference

**Q acquisition score (from investigation.py):**
Q_d = K_d × [ 1/(100 × max(σ²_d, 0.001)) + |μ_{a1,d} − μ_{a2,d}| + |(v_d − μ_{a1,d})² − (v_d − μ_{a2,d})²| ]
where a1 = argmax_a P(a|v), a2 = second-highest. Additive: precision + discriminative + leverage.
Ablation (§5.1): P+L optimal at σ=1.0; full triple optimal at heterogeneous σ.

**K utility update:**
K_d ← clip(K_d + η_K · reward_d, 0.1, 3.0)
η_K = +0.02 (informative read → correct outcome), −0.005 (otherwise). Category-indexed in production.

**Centroid update (LVQ-style):**
μ_{c,a} ← μ_{c,a} + η · y · (v − μ_{c,a})
η_confirm = 0.05, η_override = 0.01. y = +1 (verified correct), −1 (overridden).

**Conservation gate:**
θ_min = 23.53 / (α · V), signal = α · q · V
α = covered_categories / total_categories, q = correct / verified, V = verified_count.
GREEN: signal ≥ 2θ_min (learning + action). AMBER: signal ≥ θ_min (action only). RED: abstain.

## Appendix B: Tensor Shapes

| Copilot | Shape (sit × act × fac) | Cells | Penalty ratio |
|---|---|---|---|
| SOC | 6 × 4 × 6 | 144 | 20:1 |
| DataOps | 6 × 5 × 6 | 180 | 10:1 |
| S2P | 5 × 5 × 8 | 200 | 5:1 |
| Purchasing | 5 × 4 × 7 | 140 | 3:1 |
| Trading | 5 × 4 × 10 | 200 | 2:1 |

## Appendix C: Evidence Tiers

| Tier | Definition | Applies to |
|---|---|---|
| REAL_COMPONENT | Real exported production geometry + synthetic verification | K curves, budget frontier, routing variants, abstention, Q ablation |
| SIMULATED | Constructed scenarios with synthetic oracle | 57:0 Astra saves, Sim-1 ρ instrument |
| ILLUSTRATIVE | Modeled arithmetic on assumed inputs | $0.9M, $1.62M dollar figures |
| DEMONSTRATED | Code verified with unit/integration tests | EpisodeSnapshot, C4 halt, conservation gate |
| NOT TESTABLE | Experiment blocked by structural prerequisite | L4 cross-copilot transfer (zero factor overlap) |

---

*Changes v7.2→v7.3 (Astra gap #1 — figure references): All 5 chart placeholders replaced with figure
references to PAPER-CHARTS Codex output (paper_charts/). Fig 1: K-divergence hero (DataOps learn vs
frozen). Fig 3: budget-accuracy frontier (B=2 = 80-92%). Fig 4: risk-coverage curve (post-investigation
d_min monotonic). Fig 5: RI-1 heatmap (Static > RNN > GRU > LSTM). Fig 6: Q ablation normalized
(three-term correct). Figs 2, 7, 8 (cross-copilot K, budget sensitivity, R0-R5 taxonomy) available in
paper_charts/ for supplementary use. All 7 Astra gaps now closed.*

*Changes v7.1→v7.2 (Astra gap #3 — competitive dismissal): §9 expanded from 3 paragraphs to full
competitive positioning. Three 2024-2026 neighbors named and cited: SELF-RAG (Asai et al., ICLR 2024),
uncertainty-conditioned adaptive retrieval (Dey et al., arXiv 2607.07380, SIGIR'26 workshop), L2M
(Kobayashi et al., arXiv 2510.12624). Four substrate differentiators stated: no-LLM acquisition loop,
enterprise action centroids (not document relevance), scorer-parameter reuse (no separate router), and
verified-outcome compounding under conservation governance. "The composition, not the loop, is the
contribution." Cite correction: original Astra memo referenced "RLT" as recurrent-loop — actually
Ranked List Truncation (Meng et al., SIGIR 2024), a retrieval-noise method, not an adaptive loop.
Replaced with accurate cites.*

*Changes v7.0→v7.1 (Astra gaps #2, #6 — worked walkthrough, trust-traps): (1) §4.1: S2P-SC2 worked
walkthrough sidebar — one end-to-end decision showing how K changes evidence priority. Uniform K reads
match_status→amount_variance; learned K₅=1.0 reads match_status→commodity_index. Threshold arithmetic
(K₅>0.624375, 7-25 credited updates). PLANTED FIXTURE tier. (2) §5.1: σ trust-trap sidebar — falsifiable
prediction that production σ heterogeneity will reveal K-vs-precision opposing forces (team trusts noisy
evidence). Testable from a single design-partner σ export after 500+ decisions. Remaining: v7.2 (#3
competitive dismissal), v7.3 (#1 figure references).*

*Changes v6→v7.0 (Astra gaps #4, #5, #7 — moat, time-to-value, economics): (1) §4.1: verification
throughput expanded into time-to-value table for $7B manufacturer (SOC 3 days → S2P 1 week → Purchasing
3 weeks → DataOps 6 weeks → Trading 6 months). 90-day deployment sequence. Design-partner pitch. All
calendar estimates ILLUSTRATIVE; K-curve points REAL_COMPONENT. (2) §7: moat arithmetic added — per-
checkpoint learn-vs-frozen gaps from KE-1 (+3 to +21pp). S2P moat shallow (wedge, not moat). DataOps/
Purchasing are moat domains. Mechanism predicts GTM sequencing. (3) §8 rewritten: three-part economic
logic (compounding + non-transferable + first-mover = winner-take-most per firm×domain). What the customer
buys. Open-source as land-grab. Remaining: v7.2 (#3 competitive dismissal), v7.3 (#1 figure references).*

*Changes v5→v6 (Fable review + normalized Q ablation): (1) §5.1 rewritten with normalized
Q ablation (575 cells, 115K episodes): P+L advantage was magnitude artifact, three-term form correct
under z-norm. (2) §5.2: trained-router headroom explanation corrected — not discriminative downweighting.
(3) §4.1: σ=1.0 owned as pre-compounding geometry with falsifiable prediction (Fable fix #1). (4) §4.1:
57:0 generator limitation stated — no misleading-evidence channel (Fable fix #3). (5) §3: "fourth
cognitive type" → "fourth engineering memory class" (Fable terminology). (6) Headline: "built a system"
not "built the first system" — claims composition under governance, not the primitive (Fable positioning).
(7) §10: magnitude-artifact retraction replaces discriminative-interferes retraction. (8) "honest/honesty"
removed throughout (4 instances) — the retractions speak for themselves.*

*Changes v4→v5: (1) Title: "Recursive Graph Improvement: How Compounding Intelligence Makes
Enterprise Decisions Get Measurably Better." Subtitle connects judgment memory to graph-based reasoning.
(2) §4.1: 57:0 Astra saves paragraph — 250 constructed scenarios, +22.8pp, saves:hurts 114:1, domain-
appropriate traces, SIMULATED tier tag. (3) §4.1: budget sensitivity table (B=2/3/4 × 5 copilots) —
SOC needs depth, Trading discriminates sharply, Purchasing plateaus at B=2.*

*Changes v3→v4: (1) §3: "Why memory and not learned prior" paragraph — inspectability, governance,
verified grounding as the three properties "prior" doesn't carry. (2) §5 promoted to full section: Q
term ablation (9 variants × 5 copilots × 5 seeds = 225 cells), complete combination lattice, three
findings (leverage dominates, P+L optimal at σ=1.0, discriminative awaits heterogeneous σ), §5.2
trained-router headroom characterized. (3) §6: dedicated self-validation paragraph — what REAL_COMPONENT
establishes vs what it doesn't, path to external validation via design-partner deployment.
(4) §4.1: verification throughput paragraph — compounding rate bounded by verification, concrete
examples (SOC ~1 week, procurement ~10 weeks), what happens when verification stops. (5) §10: sixth
retraction (discriminative Q at σ=1.0). (6) Chart placeholders for 6 figures. (7) Appendix C:
evidence tier definitions. (8) Section numbers updated (11 sections + 3 appendices).*

*Evidence base: CI-VLD pre-paper v10 (246KB). 21 experiments + Q ablation (225 cells) + GAP 1 + GAP 2.
49 JSON result files. 49 charts. All data in ci_core.*
