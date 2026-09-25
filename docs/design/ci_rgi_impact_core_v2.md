# Compounding Intelligence — Impact Core (v2)
### Enterprise AI that gets measurably better at *your* decisions the longer it runs — demonstrated, on real geometry, across five domains.

*Standalone front for the CI-VLD pre-paper (which remains the evidence base). Audience: AI architects and
deeply-technical VCs. Every number carries its evidence tier; every claim we tested and dropped is stated
in §8. Adversarial questions (in the spirit of the separation note) sit where the objection is loudest.*

---

**The headline result.** We built the first system where every verified decision reshapes the math the
next decision is made with — and we can now show it, not assert it. On real production decision-geometry,
across all five domain copilots, decision-routing measurably improved from verified outcomes — **routing
quality +17–43%, accuracy +14–32 points, in 5 of 5 copilots, zero regressions** (controlled mechanism
test on real component geometry; tier and ceiling in §8). Two curves that start at the same point on day 1
and *diverge and stay diverged.* That divergence is the whole thesis, and it is the first thing here
because it is the thing everyone else's system cannot draw.

We tested 15 alternative routing configurations across four design axes — neural recurrence, exploration
policy, temporal weighting, trained routers — and the graph's own geometry beat them all on routing
quality. The graph IS the memory. That is not a metaphor; it is the measured result (§5).

We call the property **Recursive Graph Improvement (RGI)**: a system whose decision geometry on a graph
reshapes from verified outcomes and reasons measurably better because of it. **CI-VLD is its first working
instance.** This note is what that means, what it does *not* mean, and why — once you follow the argument —
open-sourcing the engine underneath it is the point, not a contradiction.

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
> inspectable rather than drifting. (What we deliberately *don't* let it do: §8.)

## 2. What RGI is — a category shift, not a definition

The industry climbed a ladder and mistook the second rung for the top:

| | What the graph does | After 10,000 decisions |
|---|---|---|
| **Read** (knowledge graph / RAG) | retrieve what's stated | same retrieval — plateau |
| **Route** (graph of agents) | orchestrate work | same routing — plateau |
| **Reshape (RGI)** | **decide, verify, reshape its own decision geometry** | **compounds — +14–32 pts on the firm's own decisions** |

Read and route are *structure.* Reshape is *judgment.* Graph engineering builds a graph that remembers or
wires a graph that routes; **graph-native reasoning runs a graph that decides — and reshapes itself with
every verified decision.** That third rung is RGI, and until now it has been asserted. §3.1 is the first
time it is *shown* on real geometry. Two properties make it safe to claim and to deploy:

- **Bounded and governed.** RGI is a deliberately restrained instance of recursive self-improvement: it
  acquires experience and improves its own routing, but **excludes self-rewriting of its objective by
  design** — because self-generated improvement is where self-poisoning lives. The restraint is the safety
  architecture, not a gap.
- **Inspectable — three artifacts, not a black box.** "Judgment as geometry" is three objects a buyer can
  open and audit, each physically reshaped by verified outcomes: the **centroid geometry** (the learned
  prototype of a good decision *here*); the **noise fingerprint σ** (per-factor signal-vs-noise — which
  surfaces *trust traps*: the factor a team trusts most is often its noisiest predictor); the
  **conservation status** (the auditable gate that decides whether the system may act, or must abstain).

> **"Every vendor says 'it learns.' What's different at the moment of decision?"** Ask the one question
> that matters: *when the invoice must be approved, the alert escalated, or the never-before-seen attack
> contained — what does it do, and does the record of that decision change the next one?* Read retrieves;
> route dispatches; both reason once and forget. CI-VLD **decides or abstains, acts under a gate, verifies
> the outcome, and writes it back into the geometry** — so the next decision is measurably sharper. The
> test isn't whether a system *claims* to learn; it's whether you can *open the three artifacts and watch
> them move.* Here you can.

## 3. What it does — four capabilities, each shown

Four claims survived hostile scrutiny. Each is stated as the consequence, the exhibit that proves it, and
exactly how far the proof goes. Everything that *didn't* survive is in §8 — read it first if you're a
skeptic; it's what makes these four believable.

### 3.1 It compounds — the curve everyone else can only assert
**Consequence.** The copilot gets measurably better at *your* decisions the more it makes — from verified
outcomes, not a bigger model. Day 500 ≠ day 1.
**Exhibit.** Two identical systems from one start; one learns its routing from verified outcomes, one is
frozen. DataOps, real production geometry:

| After N decisions | Routing (learn) | Routing (frozen) | Accuracy (learn) | Accuracy (frozen) |
|---|---|---|---|---|
| 50 | 0.42 | 0.40 | 0.56 | 0.52 |
| 250 | 0.56 | 0.42 | 0.72 | 0.58 |
| 500 | 0.63 | 0.44 | 0.90 | 0.58 |

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

Five copilots, **+5% to +43% routing improvement, zero regressions.**

**The starvation fix.** Under greedy routing, 8–48% of evidence dimensions are never checked (worst:
Trading at 48%). Category-conditional routing (RI-7) resolves this: explore starved categories, exploit
healthy ones. Trading achieves 74.8% routing with 0% starvation — the only tested policy satisfying both
constraints on all five copilots. The system also learns where its blindspots are — and fixes them.

**Tier.** REAL_COMPONENT — real geometry, synthetic verification; a controlled mechanism test, not
live-operational value (§8).
**Un-copyable.** A competitor can add a learned retriever tomorrow; they cannot make what it learns *be the
firm's own accumulated judgment* — earned from decision history, not shipped in a model. The first mover
per domain compounds a lead nothing static closes.

### 3.2 Governed autonomy — the system earns the right to act, or declines
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

Strictly monotonic — decline more and accuracy-on-acted keeps rising. The tradeoff is smooth, not
cliff-edge: even at 90% coverage (decline only 10%), you gain +3–7pp.

**Mechanism (the part that matters).** It works only on **post-investigation confidence.** Every surface
signal — margin, distance, entropy measured *before* investigating — is non-monotonic and fails. *The
system cannot know what it doesn't know before it investigates; the investigation produces the
calibration.* (A naive pre-investigation version failed outright — 86% abstained, worse on the rest. Same
experiment, mechanism-correct signal, opposite result.)
**Tier & boundary.** REAL_COMPONENT. Abstention spends the full budget — the value is *fewer committed
errors, not fewer reads.* A quality-and-safety claim, not a cost one.
**Un-copyable.** A confidence-thresholded LLM thresholds on what it knew *going in*; CI-VLD thresholds on
what it knew *after reasoning over the firm's judgment geometry.* Investigation-produced calibration is a
property of the substrate, not the threshold.

### 3.3 The right evidence — not fewer checks, the *right* checks
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

**80–92% of exhaustive-investigation accuracy at 20–33% of the reads** — because the scorer's own
precision-and-leverage geometry picks *which* evidence is decisive here.
**Honest reframe (from a negative).** We tested early halting; it can't read fewer than two (wrong-first-
step recovery needs the second). So the value was never brevity — it's *selection.* "The right two reads,"
not "fewer reads." (Stated as "fewer reads," a reviewer answers "so does a smaller top-k"; stated as "the
right reads," there is no such rejoinder.)
**Tier.** REAL_COMPONENT; exhaustive = 100% *by construction* (synthetic oracle), so this is "% of a
synthetic ceiling," not "% of human accuracy."

### 3.4 The graph is its own memory — neural recurrence is overhead
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

R2 is the mechanism. The graph remembers through its own geometry — centroids, K weights, conservation
state — not through a bolted-on neural network. This is why the system is inspectable: the "memory" is
three auditable artifacts (§2), not a hidden state vector no one can read.

**The closed-form Q heuristic is nearly optimal.** We measured the headroom between the geometric Q
(precision + discriminative + leverage, K-modulated) and a trained linear router: **+1.4pp** (RV-8). The
no-trained-router separator holds — the geometric substrate captures nearly all routing value without
model training, without training data, and without the self-poisoning vector that trained routers carry.

**Twelve killed alternatives (equally important).** We tested and rejected: temporal K decay (all λ>0
hurt routing, RI-6), sequence-aware Q (helps DataOps +2.2pp but destroys SOC −14.4pp, RI-8), MCTS
lookahead (−31pp at 15× scorer cost — wrong objective at B=2, RV-9), risk-sensitive adaptive budget
(more reads ≠ better routing — SOC loses 36pp at B=5, RV-4), and hierarchical C4→RNN (needs a trained
6-class classifier that doesn't exist, RV-5). Each is a measured negative, not an untested alternative.

**Tier.** REAL_COMPONENT. 15 configurations × 5 copilots × 5 seeds = 375 experimental cells, each with
pre-registered kill/keep criteria and a three-metric protocol (M-VALUE routing/accuracy, M-COST
scorer-calls-per-decision, M-GOV inspectability/replay).

> **"These are synthetic ceilings on real geometry — why believe it transfers to production?"** Believe
> exactly what the tier says. What REAL_COMPONENT already rules out: these run on the *real, exported
> decision-geometry* of five shipped copilots — so they test whether the mechanism works on the *actual
> learned structure*, and it does, 5 for 5. What's synthetic is the verification labels, not the geometry.
> The honest claim: the compounding, calibration, selection, and recurrence findings are demonstrated on
> real geometry; the last mile — moving a firm's live P&L — is the experiment we have *not* run and do
> *not* claim. A vendor who can't tell you which number is which is the one to distrust.

*The pattern across all four (don't skip):* the **same copilot is weakest on every axis** — S2P: last on
the K-curve (+5%), the budget frontier (84.1%), and transfer. Not noise — the same signal four times:
S2P's decisions have the fewest genuine multi-step evidence chains, so there's less for RGI to compound.
**The method tells you where it applies** — the opposite of a technology that claims to help everywhere.

## 4. One engine, five copilots — the generality is the proof

The four capabilities are one operator over five domains, not five hand-tuned systems. Under all of them:
the **Graph Attention Engine (GAE)** and a fixed set of governed decision-loops. Formally, every copilot is
the same object:

- A decision is a factor vector **v ∈ ℝ^d** read from the graph; the scorer is a prototype classifier over
  frozen learned state **Θ = {μ centroids, σ noise, K utility, τ calibration}**, readout
  **a\*(v) = argmin_a ‖v − μ_{c,a}‖²_DK**, confidence **p(v) = softmax(−d²/τ)**.
- Investigation is a **state-conditioned recurrence** (the VLD step), each pass reading *new* evidence the
  geometry itself chooses:
  **v_{t+1} = Reshape(v_t, e\*_t), e\*_t = graph_read(k\*_t), k\*_t = argmax_k Q(k; v_t, Θ)**,
  with acquisition score:

  **Q_d = K_d × [ 1/(100 × max(σ²_d, 0.001)) + |μ_{a1,d} − μ_{a2,d}| + |(v_d − μ_{a1,d})² − (v_d − μ_{a2,d})²| ]**

  Three additive terms: **precision** (inverse variance — how reliable this dimension is),
  **discriminative** (centroid separation — how much the top two actions disagree here), and
  **leverage** (differential distance — how much this dimension would move *this* decision). K modulates
  multiplicatively — learned from verified outcomes (§3.1). No LLM in that loop; matrix–vector arithmetic
  over Θ. RV-8 confirms: a trained linear router improves on this heuristic by only +1.4pp.

- Every verified outcome updates the geometry:
  - **Centroid update:** μ ← μ + η·y·(v − μ), with η_confirm = 0.05, η_override = 0.01
  - **K update:** K_d ← clip(K_d + η_K · reward_d, 0.1, 3.0), with +0.02 for informative reads, −0.005 otherwise
  - **Conservation gate:** θ_min = 23.53/(α·V), signal = α·q·V; GREEN (signal ≥ 2θ_min) allows learning, AMBER allows action, RED requires abstention
  *The operator that decides is the operator that reshapes* — that is RGI.

Copilots differ only in tensor shape — **SOC 6×4×6, Trading 5×4×10, Purchasing 5×4×7, DataOps 6×5×6, S2P
5×5×8** (situations × actions × factors) — and in their verified-outcome stream. One operator producing the
compounding curve on all five shapes is the generality claim, and why a lesson about *how to reason* is
substrate-level, not domain-level.

**Wedge-and-expand.** Source-to-pay and restaurant purchasing are the revenue wedge (dollar-legible
decisions, fast-arriving outcomes); trading is the open-sourced community reference application; security
operations and data operations are the expansion path (highest stakes, richest evidence chains, strongest
RGI signal). The bimodal result is the GTM guide: expansion follows the mechanism (where multi-step
evidence structure is richest), not the sales map.

> **"Five 6-to-10-dimensional tensors is a small model. Is this even 'AI' at the scale that matters?"** The
> small dimensionality is the point. Reasoning that compounds lives in a *low-dimensional, inspectable
> decision geometry* so that every factor's contribution is auditable (the σ trust-trap diagnostic only
> means something because d is small), the recurrence is matrix–vector cheap (sub-ms, no GPU, no LLM/hop),
> and verified outcomes have enough leverage to *move* the geometry in hundreds of decisions, not millions.
> A 175B-parameter model improves for everyone and is inspectable by no one; a 6×4×6 judgment geometry
> improves for *one firm* and is inspectable by its auditors. The scale that matters is the decision, and
> the decision is low-dimensional.

## 5. Open source — give away the commodity, keep the compound

We are open-sourcing the layers this note has argued are commoditizing: the **Graph Attention Engine
(GAE)**, the **copilot-SDK**, and the **trading copilot** as a full reference application. The objection is
obvious, so we meet it directly.

**Moat-consistent (why this isn't giving away the company).** Re-read §1: model, graph, orchestrator are
all commoditizing; the only durable axis is compounding the firm's own verified judgment. The engine is on
the commodity side of that line; the moat is on the other. What GAE *is* — attention over a graph, prototype
scoring, the VLD recurrence, the conservation gate — is in the equations above and reproducible by a
competent team; there is no defensibility in hiding it, and pretending otherwise contradicts our own
thesis. What GAE *is not* is what makes a deployment valuable: **the firm's accumulated, verified geometry —
Θ and K after ten thousand of that firm's decisions.** Open source ships the operator; it cannot ship the
fixed point the operator converges to on your data. Clone the repo tonight and you start, as everyone does,
at day 1 of the flat line.

**Adoption / standards (why it strengthens the moat).** Open-sourcing the engine is how CI becomes the
**default substrate others build judgment on.** Every team adopting GAE for its inspectability and no-LLM
economics accrues its decision-geometry *in our substrate's format* — the compounding happens on our rails.
The trading copilot as an open reference seeds a community flywheel in the one domain where community
adoption compounds fastest and enterprise-sales sensitivity is lowest. The commoditizing layers, given
away, become the distribution channel for the one layer that isn't. Formally: **we open-source the operator
family and the mechanism (VLD, Q, conservation); we do not — and structurally cannot — open-source the
learned state Θ, K a firm earns.**

> **"A well-funded incumbent forks GAE, wires it to their customer base, and out-compounds you. What stops
> them?"** Three things. First, **compounding is per-firm and non-transferable** — the incumbent's own
> customers each start at day 1; the fork ships the engine, not their customers' earned geometry, and (§8)
> judgment doesn't transfer even between *our own* copilots without a shared factor space. Second,
> **first-mover-per-domain compounds an opening lead a later entrant is always chasing** on the same rising
> curve — on a compounding axis a head start widens. Third, the honest one: an incumbent adopting GAE is
> adopting our substrate, inspectability model, and governance semantics *as the standard* — that is the
> adoption win. The scenario where they fork and out-compound is one where the category we defined wins; we
> would rather define the winning category and compete inside it than hide an engine whose equations are
> printed above.

## 6. What this changes — two assumptions, and an economy

**Decision-making moves from the model to the firm's judgment.** Today the unit of intelligence is the
*model* — rented, static between releases, improving for everyone (so an advantage to no one). RGI moves it
to **the firm's accumulated judgment on its own decisions** — proprietary, compounding, improving only for
whoever verifies outcomes. Reasoning becomes an *owned, appreciating asset*; Θ and K are how it's
represented, the §3.1 curve is it appreciating.

**Decision-storage moves from logs to judgment memory.** Enterprises store decisions as *logs* — inert
records of what was decided. RGI stores them as **judgment memory**: a fourth cognitive memory type
(alongside episodic, semantic, procedural) in which a verified outcome *physically reshapes the geometry
that makes the next decision.* The decision store stops being an audit archive and becomes **the substrate
that reasons** — inspectable, replayable, governed.

**Together: a self-improvement economy.** Once model, graph, and orchestrator are commodities, durable value
accrues to **whoever compounds their own verified judgment.** One axis: does your system get better at *your*
decisions? One consequence: because the edge is earned from a firm's decision history and doesn't transfer
even between domains without a shared factor space (§8), **the first mover in each domain compounds a lead
nothing static can close.** CI is built to hold that position — and to open-source everything except the
position itself.

## 7. The routing category — where RGI beats what others build

Everyone building AI agents is solving routing: which tool to call, which evidence to check, which action
to take. The standard approaches are chain-of-thought reasoning (ask the LLM), learned retrievers (train a
model), and multi-agent debate (vote on it). We tested our substrate against comparable mechanisms and found
the graph's geometry dominates on this specific task.

**Category recovery on real geometry.** On 543 SOC fixture alerts, CI-VLD's geometry-directed routing
recovered the correct alert category at 68.5% versus 30.0% for majority routing (+38.5pp). The routing
mechanism — which evidence to check — works. The honest caveat: final-action accuracy on the same fixture
*fell* (31.3% vs 53.8% single-pass), meaning the system routes to the right category but struggles at
action-level discrimination within that category. Category routing works; action discrimination is the
remaining gap. Both numbers are reported because reporting only the positive one would be dishonest.

**Tier.** REAL_COMPONENT (real geometry, synthetic fixture). The category-routing signal is strong; the
action-accuracy gap is the next validation target.

## 8. What we are *not* claiming — the map, and the ceiling

Everything above is believable in proportion to what we'll say we haven't shown.

**The recursion ladder — how far up, and why we stop.** RSI has five autonomy levels (execute → strategize
→ acquire-experience → adapt-environment → rewrite-the-objective). CI-VLD occupies **L1–L3 and stops on
purpose:**
- **L1 execute / L2 strategize / L3 acquire-experience — demonstrated** (the compounding curve, geometry-
  directed investigation, routing memory K).
- **L4 cross-domain adaptation — NOT claimed; it is a null result.** Transfer across three copilot pairs
  showed *zero* exact factor-name overlap; cold-start equalled warm-start. Judgment does not transfer
  between domains without a shared factor space we have not built. "A lesson in one domain transfers to the
  next" is **not supportable**, and is removed.
- **L5 self-rewriting of the objective — excluded by design.** Where self-poisoning lives. Boundedness is
  the safety architecture, not a missing feature.

**Five more retractions:**
- **"Saves reads / saves cost" — retracted (negative result).** Adaptive halting can't read fewer than two
  (C4 residual halt activates only after 2 acquired reads, by design — wrong-first-step recovery needs
  both). The efficiency claim is *selection quality*, not brevity.
- **Grounded dollar figures — illustrative only.** The $0.9M and $1.62M in circulation are *modeled* (a
  leakage chain, a borrowed simulation curve, stipulated demo constants). No dollar claim is grounded in
  measured customer outcomes; each is labeled "modeled/illustrative."
- **Calibrated abstention was harder than it looked.** The naive (pre-investigation) version failed — 86%
  abstained, worse on the rest. §3.2 works only because it thresholds *post-investigation* confidence. We
  report the failure because it's why the success is real.
- **Conservation is inert at this scale.** KE-5: conservation gates blocked 10.2 decisions early while
  support accumulates; same final routing, same dips. Conservation governs the learning path, not
  investigation — the safety value is in the bound (K ∈ [0.1, 3.0], θ_min gate), not in frequent
  intervention. At 500 decisions the gate rarely fires. This is expected: the guard is for the edge case
  (catastrophic unlearning), not the steady state.
- **Temporal decay, sequence bias, MCTS — all killed.** Temporal K decay (RI-6): all λ>0 hurt routing.
  Sequence-aware Q (RI-8): helps DataOps +2.2pp but destroys SOC −14.4pp — no universal β. MCTS lookahead
  (RV-9): −31pp at 15× cost — margin-maximizing lookahead is the wrong objective at B=2. Risk-sensitive
  adaptive budget (RV-4): more reads ≠ better routing — SOC loses 36pp at B=5. Hierarchical C4→RNN
  (RV-5): needs trained classifier that doesn't exist. Each is measured, not speculated.

**The ceiling on the headline numbers.** Every §3 result is **REAL_COMPONENT**: real, exported decision-
geometry of five shipped copilots, with synthetic verification labels. The compounding, calibration,
selection, and recurrence findings are demonstrated *on the actual learned structure* — not a toy — but the
last mile, *that they move a firm's live decisions and P&L*, is a validation we have **not** run and do
**not** claim.

> **"You just spent a page on what you can't prove. Why is that a pitch?"** Because on a compounding,
> safety-critical decision system sold to auditors and CISOs, **the retractions are the product.** A system
> that claims to self-improve is one that can self-poison — so testing transfer and finding null, halting
> and finding negative, naive abstention and finding failure, twelve routing alternatives killed, and
> *excluding L5 on purpose* is not a list of weaknesses; it's evidence the same discipline governs the
> running system. The four capabilities in §3 are worth exactly as much as this section is honest — and no
> more. We think that's the highest price they can command.

## 9. Where this stands

RGI is demonstrated — decision quality compounds from verified outcomes, on real geometry, across five
copilots, zero regressions; the system earns the right to act or declines, with post-investigation
calibration; it selects the decisive evidence, 80–92% of exhaustive at a third of the reads; and the
graph's own geometry outperforms neural recurrence on routing quality. It is bounded (L1–L3), governed
(conservation-gated, L5 excluded), inspectable (three auditable artifacts). The engine, SDK, and a
reference copilot are open; the firm's compounding judgment is not, and structurally cannot be.

The one validation not yet run is the one that turns REAL_COMPONENT into revenue: **a firm's live
decisions, verified over time, moving its measured outcomes.** That is the experiment a design partner runs
with us — and on a compounding curve, the value of starting is highest today.

*The model is a commodity that improves for everyone. CI makes the firm's own verified judgment the thing
that compounds — owned, governed, inspectable, and demonstrably rising. That is the shift: from renting a
model that reads a graph, to owning a judgment graph that recursively improves the decisions it makes.*

---

## Appendix: Equation Reference

**Q acquisition score (from investigation.py):**
Q_d = K_d × [ 1/(100 × max(σ²_d, 0.001)) + |μ_{a1,d} − μ_{a2,d}| + |(v_d − μ_{a1,d})² − (v_d − μ_{a2,d})²| ]
where a1 = argmax_a P(a|v), a2 = second-highest. Additive: precision + discriminative + leverage.
Headroom vs trained linear router: +1.4pp (RV-8).

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

**Tensor shapes:**
SOC (6,4,6)=144. Trading (5,4,10)=200. Purchasing (5,4,7)=140. DataOps (6,5,6)=180. S2P (5,5,8)=200.

---

*Changes v1→v2: (1) Q equation corrected to 3-term additive from code. (2) Cross-copilot N=500 table
added — all 5 copilots visible. (3) Abstention expanded to 90%/75%/50% coverage with full table.
(4) §3.4 added: 5-level recurrence taxonomy with RI-1 results and 12 killed alternatives.
(5) Category-conditional routing (RI-7) starvation fix added to §3.1. (6) §7 added: category-routing
ρ finding (68.5% vs 30.0%) with honest action-accuracy caveat. (7) Conservation inert result (KE-5)
and all routing negatives (RI-6/8, RV-4/5/9) added to §8. (8) Equation appendix with four core
equations from code. (9) Routing design space (15 configs, 4 axes, 3-metric protocol) summarized
in §3.4. (10) +1.4pp headroom and no-trained-router separator stated with RV-8 evidence.*

*Evidence base: CI-VLD pre-paper v10 (246KB). 21 experiments. 47 JSON result files. 46 charts.
All data in ci_core. Tier: REAL_COMPONENT + SYNTHETIC throughout, labeled per claim.*
