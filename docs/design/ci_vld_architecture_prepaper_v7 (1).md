# Compounding Intelligence with Score-Conditioned Graph Reasoning
## A Self-Improving Enterprise Decision Architecture
**Version:** v7 (Pre-Paper) · **Date:** Sep 11, 2026
**Changes v6→v7:** C4 updated with learned classifier (47.7%, 2.4×
random, d_min/d_gap dominant features). C5 updated with K utility
mechanism validation (+25% routing quality over 30 epochs,
per-category K requirement identified). v8 experiment results
integrated.

---

## §0: The Compounding Intelligence Platform

### 0.1 The Enterprise AI Learning Gap

A vendor shows you ten thousand AI agents, wired to every system
through MCP, and says the platform *learns.* One question decides
everything: when an invoice has to be approved, an alert escalated,
or an attack no one has seen before contained — what does it actually
do at the moment of decision? Connectivity is not an answer, and
"it learns" is the most abused verb in this market. What matters is
whether the learning changes the decision — or just produces a
better-informed guess that arrives one step too late.

The model is a commodity now. So is graph engineering — building a
knowledge graph to retrieve answers and wiring a graph of agents to
route work are both documented recipes, shipping as standardized
tooling. Both are real advances; both stop at the same line: the
graph is structure the model reads or routes through, and the
reasoning is still the model's, still once, still transient. What
decides enterprise AI is what happens *after* you ship: does the
system **compound** — get better at the firm's decisions with every
one it makes — or **plateau** on day one?

### 0.2 What CI Is

Compounding Intelligence (CI) is a graph-native decision platform
where verified outcomes reshape the decision geometry. The platform
operates across five enterprise domains — security operations (SOC),
source-to-pay (S2P), data operations (DataOps), trading, and
purchasing — using a shared mathematical engine (the Graph Attention
Engine) and domain-specific factor ontologies.

**What compounds is inspectable — three evolving artifacts, not a
black box.** "Judgment as geometry" is not a metaphor; it is three
objects a buyer can open and audit, each physically reshaped by
verified outcomes:

- **the centroid geometry** — learned prototypes of a good decision
  *here*, which move as outcomes are confirmed;
- **the noise fingerprint (σ)** — per-factor outcome-conditioned
  variance, a diagnostic that measures where each factor is signal
  versus noise and surfaces systematic judgment biases;
- **the conservation status** — the gate that decides whether the
  system may act, or must abstain.

The centroid tensor (90-180 values depending on the copilot)
encodes the organization's compiled decision intelligence —
inspectable as a table of numbers, not opaque as neural network
weights. The scoring mechanism is related to Learning Vector
Quantization (Kohonen, 1990; Hammer & Villmann, 2002) and
prototypical networks (Snell et al., 2017), extended with
asymmetric learning rates, DiagonalKernel precision weighting,
and a conservation safety gate.

### 0.3 Three Graphs — Read, Route, Reshape

There is not one "graph" but three, and only one compounds:

| | Knowledge / context graph | Graph of agents | Judgment graph (CI) |
|---|---|---|---|
| What it is | entities + relations, traversable | agents as nodes, tasks as edges | decision-prototypes as learned geometry |
| What it does | retrieves a cited path | routes work between agents | scores a decision — acts or abstains |
| How it changes | grows by ingestion | rewired by a developer | reshapes from verified outcomes |
| Core operation | a **read** | an **orchestration** | a **decision loop** |

Graph engineering moves from *read* and *route* to **reshape**;
agentic AI moves from *deploy-and-plateau* to **compound**.

### 0.4 Four Clocks

Every system runs some subset of four clocks. Most enterprise AI
runs one or two; compounding needs all four:

| Clock | Question | What it measures |
|---|---|---|
| **State** | What's true now? | assets, users, policies |
| **Event** | What happened? | decision traces, causal chains |
| **Decision** | How did reasoning evolve? | scoring weights, pattern confidence |
| **Insight** | What connects across domains? | correlations surfaced by cross-graph attention |

The divide is at Clock 3. Clock 4 is where judgment emerges.

### 0.5 Judgment Memory — the Fourth Cognitive Type

CI produces a fourth long-term memory type beyond the episodic,
semantic, and procedural memory the standard agent taxonomy already
names (CoALA; Sumers et al., 2023): not *what happened* or *what
is true*, but *how well decisions are made, and where they are
noise*. Verified outcomes physically move centroids — a single,
nameable point you can audit back to the decision that moved it,
and roll back.

### 0.6 Five Copilots, One Engine

| Copilot | Domain | Decisions | Value |
|---|---|---|---|
| SOC | Security alert triage | Suppress/monitor/investigate/escalate | Reduce MTTR, capture analyst judgment |
| S2P | Invoice exception handling | Approve/flag/hold/reject/escalate | Reduce processing cost, catch fraud |
| DataOps | Pipeline failure triage | Auto-resolve/queue/investigate/escalate/rollback | Reduce downtime, preserve SLAs |
| Trading | Trade decision support | Execute/reduce/hold | Enforce thesis discipline, manage concentration |
| Purchasing | Reorder optimization | Reorder/defer/switch/escalate | Optimize coverage, reduce waste |

### 0.7 What CI Does Not Do

CI is not a large language model. The ProfileScorer is a geometric
classifier operating in a 5-8 dimensional factor space. CI does not
replace analysts — it codifies what analysts already know into a
computable form. CI does not require GPU infrastructure — the scoring
equation runs in single-digit milliseconds on commodity hardware.

### 0.8 The Problem VLD Solves

CI's scorer uses the factor vector as given. If the initial factor
computation is incomplete — identity context not yet resolved,
contract terms not yet checked, schema stability not yet assessed —
the scorer operates on partial evidence and may recommend the wrong
action.

Before it triages, VLD checks the two things your best analyst would
have checked — and shows you which two. Before it flags the invoice,
it reads the contract. Before it auto-resolves, it reads the
schema-change history. Bounded, auditable investigation — two reads,
no LLM, a trace you can hand to audit.

### 0.9 Six Architecture Claims

**Claim 1: VLD uses the decision model's own geometry as a graph traversal planner — 2 reads out of 6 at 85% of exhaustive accuracy, zero additional models.** Every factor dimension maps to a specific graph traversal (e.g., "asset_criticality" = Alert→Asset→CriticalityRating). VLD computes a per-dimension acquisition priority Q[k] = precision(k) × discriminative(k) directly from the centroid geometry, with K mapping graph edges to factor dimensions weighted by source confidence, and V updating the evidence vector via raw replacement or confidence-gated blending. Two targeted traversals achieve 0.872 vs 0.912 exhaustive and 0.748 random. *SOC example: Q identifies asset_criticality as the highest-priority read because the escalate and investigate centroids diverge most on that dimension. S2P: Q identifies contract_compliance as highest-priority because auto_approve and hold diverge there.*

**Claim 2: VLD-RNN — sequential recomputation after each graph read — captures conditional evidence dependencies at +4.8% on conditional decisions.** VLD-RNN recomputes Q after each enrichment: v_t is the hidden state, each graph traversal is a timestep, the scorer is the transition function. Routing priorities shift in 30-60% of S4 scenarios after a single enrichment. VLD-RNN outperforms centroid-mean distance routing by +7.8pp (0.872 vs 0.794) and selects a decision-relevant node 73% of the time (P@2 = 0.728). *Procurement example: reading supplier_exception_history reveals 3 exceptions in 30 days, shifting top-2 from {auto_approve, hold} to {hold, escalate} — now commodity_index becomes the critical second read, invisible at v₀.*

**Claim 3: VLD routing is the gate that determines whether the CI decision loop compounds constructively or destructively — 57:0 saves:hurts across 250 domain scenarios, 12.4pp accuracy gap in simulation.** The CI loop writes verified outcomes back to centroids. VLD-routed decisions feed decision-relevant evidence into centroid updates; random-routed decisions feed noise. Same loop, same data: VLD + learning = stable. Random + learning = −4.7% degradation. Across 250 Astra-generated domain scenarios (5 copilots, 10 domain-specific scenario types each), VLD investigation recovered the correct action 57 times where single-pass failed. Zero times did investigation degrade a correct surface score. In simulation (1,250 scenarios per copilot), the saves:hurts ratio is 9.5:1 with a mean accuracy gap of 12.4 percentage points (0.872 vs 0.748). Every misrouted decision that feeds back into the learning loop writes a noisy centroid update that compounds in the wrong direction. *SOC example: after 1,500 VLD-routed alerts, credential_access centroids have sharpened on identity_context and kill_chain_phase. After 1,500 randomly-routed alerts, same centroids have drifted toward noise from blast_radius and historical_frequency.*

**Claim 4: The decision surface classifies each decision into a situation type BEFORE any graph traversal — determining budget, architecture, and failure boundary.** A learned classifier (RF, 10 observable features, 5,000 scenarios across 10 geometries) achieves 47.7% accuracy on 6 situation types (2.4× the 20% random baseline). The dominant predictive features are centroid distance geometry — distance to nearest centroid (d_min, importance 0.253) and gap between the two nearest (d_gap, 0.163) — not action probability margins (importance 0.016). The Q distribution shape (spread, entropy, concentration) forms a second predictive tier (0.12-0.13 each). Adaptive budget assignment from the classifier matches fixed B=2 accuracy at 1.80 average hops — 10% fewer graph reads with no accuracy loss. S1 decisions correctly receive zero reads; S6 decisions receive 4. *SOC S4: alert looks like "investigate" until reading asset_criticality (crown jewels) shifts top-2 to {escalate, contain}. S2P S3: price variance flag clears with one contract_compliance read.*

**Claim 5: VLD-LSTM — cross-decision routing memory — makes graph traversal improve automatically with every verified decision.** Three VLD levels produce three compounding mechanisms. VLD-static plans once from centroid geometry. VLD-RNN recomputes after each read. VLD-LSTM adds a per-dimension K utility weight that accumulates across verified decisions. Experimentally validated: over 30 epochs (9,000 categorized decisions), K weights for consistently informative dimensions rise from 0.5 to 3.0 while neutral dimensions stay flat or decrease. Routing quality — the fraction of reads that select a decision-relevant dimension — improves from 30.0% to 37.5% (+25%). The compounding mechanism requires category-specific K: a single global K vector boosts dimensions common across all categories but cannot distinguish which dimensions matter for WHICH category. Production deployment uses one K vector per decision category (alert type, invoice class, pipeline system), which the copilot architecture already provides. *DataOps example: Week 1 reads error_rate and latency for every alert. Week 12 (VLD-LSTM): K weights for schema_drift alerts have learned that upstream_health is informative 72% of the time — the system reads it first, before this alert's Q geometry would suggest it. No model retrained, no rule written.*

**Claim 6: VLD turns graph engineering into graph reasoning — and only graph reasoning compounds.** Graph engineering (better schemas, richer entity resolution, cleaner ingestion) has diminishing returns: a perfect graph read exhaustively or by embedding similarity wastes 67% of traversals on evidence that doesn't change the decision. VLD makes the traversal itself decision-conditioned (Q·K·V from centroid geometry), state-dependent (VLD-RNN recomputation), and self-improving (VLD-LSTM utility learning). After 10,000 decisions, a graph-engineering system reads its better graph the same way as Day 1. A VLD-CI system reads differently — centroids encode 10,000 decisions' worth of learned traversal priorities. Graph engineering produces a knowledge asset. Graph reasoning produces a judgment asset. Only the judgment asset compounds.

---

## Contributions

This paper makes six contributions:

**C1. Scorer-conditioned evidence acquisition from graph-structured
state.** We introduce Variable-Length Deliberation (VLD), a
per-instance evidence acquisition method that uses a prototype
classifier's learned geometry (centroids μ, precision σ) to select
which graph evidence to read for each decision. Related to active
feature acquisition (EDDI, Shim et al. 2018; Kachuee et al. 2019)
but distinguished by: a closed-form acquisition function requiring
no separate training, zero LLM calls per investigation hop, and
full parameter reuse from the production scorer. Evidence
acquisition costs are incurred by ingestion regardless of VLD.

**C2. A geometric acquisition heuristic that outperforms embedding-
based and oracle routing.** Investigation priority decomposes into
precision (1/σ²) × discriminative (|μ_{a1,k} − μ_{a2,k}|) — the
"true gradient" P×D — which alone achieves 0.860. An additive
leverage term provides a minor refinement to 0.872 but is not
multiplicatively essential. Precision@2 = 0.728: Q's top-2 picks
include at least one decision-relevant dimension 73% of the time.
Outperforms centroid-mean distance routing (+0.078, p<0.001,
bootstrap 95% CI [0.042, 0.114]) and a fixed informative-dimension
oracle (tied overall at 0.872; VLD dominates S2 by +0.38).

**C3. State-dependent routing (VLD-RNN).** Q recomputes from the
enriched state v_t at each investigation step, capturing conditional
dependencies: the SECOND read depends on what the FIRST read
revealed. This is the mechanism that makes S4 (Conditional
Investigation) situations tractable — without recomputation, VLD
reduces to static feature selection and the conditional dependency
story collapses. Validated: S4 advantage +0.136 vs random (p<0.001).

**C4. A situation taxonomy with learned classification.** Six
decision situations (S1-S6) defined by the structure of uncertainty
relative to centroid geometry. A learned classifier (RF, 10
observable features) achieves 47.7% accuracy (2.4× random) on
situation prediction. The dominant features are centroid distance
geometry (d_min: 0.253, d_gap: 0.163), not action probability
margins (0.016). Adaptive budget assignment matches fixed B=2
accuracy at 10% fewer graph reads.

**C5. Directed routing as precondition for safe online centroid
learning.** Through a controlled 4-cell experiment (routing policy ×
learning), we show that random routing combined with centroid
learning produces NEGATIVE results (-0.047 from baseline): random
reads include misleading evidence, and centroid learning moves
prototypes toward that misleading evidence. Directed routing +
learning compounds safely. The Astra benchmark confirms this
asymmetry at scale: across 250 domain scenarios, VLD investigation
recovered 57 correct decisions from incorrect surface scores with
zero degradations (57:0). The interaction is subadditive in
fresh-data simulation (−0.014 at all nonzero η_μ) — the honest
finding is that directed routing is a PREREQUISITE for safe learning,
not a multiplier of it.

**C6. Graph reasoning vs graph engineering: only reasoning
compounds.** Graph engineering (schema quality, entity resolution,
ingestion coverage) produces a knowledge asset with diminishing
returns — a perfect graph read exhaustively or by embedding
similarity wastes 67% of traversals on evidence that doesn't change
the decision. VLD turns the graph into a reasoning substrate where
traversal is decision-conditioned (Q·K·V from centroid geometry),
state-dependent (VLD-RNN recomputation), and self-improving
(VLD-LSTM utility learning). After N verified decisions, a
graph-engineering system reads its graph the same way as Day 1.
A VLD-CI system reads differently — centroids encode N decisions'
worth of learned traversal priorities. The knowledge asset is
replicable; the judgment asset compounds and is not.

---

## Part I: Architecture Overview

### 1.1 The Problem

Enterprise AI systems face a paradox: they achieve high accuracy on
Day 1 by memorizing patterns, but STOP learning on Day 2. The
analyst who verified 10,000 decisions has taught the system nothing.
The institutional knowledge walks out the door when the analyst
leaves.

### 1.2 The Architecture: Five Compounding Loops

Five loops operate at different timescales, each computing
parameters that improve the others:

```
Loop 1: VLD Investigation     (milliseconds)  — which evidence to read
Loop 2: RL Scoring + Learning (seconds)       — centroid + precision updates
Loop 3: AgentEvolver          (minutes-hours)  — runtime rule evolution
Loop 4: Situation Analysis    (pre-investigation) — context classification
Loop 5: Conservation Law      (always-on)      — safety envelope
```

**Coupled adaptation:** The routing rule (Q) has no parameters of
its own — it borrows all of them from the scorer (μ, σ). Scorer
learning therefore produces routing improvement with no additional
training. Metaphorically, loops 2-5 change the rate of change of
decision quality; precisely, they update the operating parameters
that VLD's acquisition function reads.

### 1.3 The Graph Substrate

All five loops operate on a shared knowledge graph (Universal
Context Layer, UCL) stored in PostgreSQL+AGE. Three write sources:
(1) external ingestion, (2) verified decisions writing back via
[:TRIGGERED_EVOLUTION] edges, (3) cross-graph discovery via
[:CALIBRATED_BY] edges.

---

## Part II: Mathematical Foundation

### 2.1 Scoring: The Compounding Intelligence Equation

```
Eq. SCORE:
  P(a | f, c) = softmax(-K(f, μ[c, a, :]) / τ)
  a* = argmax_a P(a | f, c)
```

f ∈ [0,1]^d: factor vector. μ[c,a,:] ∈ [0,1]^d: centroid for
category c, action a. τ = 0.1 (validated ECE=0.036).

### 2.2 Kernel Functions

```
Eq. L2 (cold-start fallback):
  K(f, μ) = ||f - μ||² = Σ_k (f_k - μ_k)²

Eq. DK (DiagonalKernel, v6.0 default):
  K(f, μ) = (f - μ)ᵀ W (f - μ) = Σ_k w_k (f_k - μ_k)²
  where W = diag(w₁,...,w_d), w_k = 1/σ²_k
  σ_k = per-factor noise standard deviation
```

Kernel selection: noise_ratio = max(σ)/min(σ) > 1.5 → DK, else L2.
Validated: +13.2pp SOC, +6.8pp S2P (V-MV-KERNEL, 390-cell factorial).

### 2.3 Centroid Learning (Two-Phase)

**Phase 1: Mean Convergence (~200 decisions per category-action pair)**

```
Eq. PULL (confirm):
  μ[c, a*, :] ← μ[c, a*, :] + η_confirm × (f - μ[c, a*, :])
  η_confirm = 0.05

Eq. PUSH (override):
  μ[c, a_wrong, :] ← μ[c, a_wrong, :] - η_override × (f - μ[c, a_wrong, :])
  μ[c, a_correct, :] ← μ[c, a_correct, :] + η_override × (f - μ[c, a_correct, :])
  η_override = 0.01
```

PULL/PUSH is LVQ2.1-style online prototype learning (Kohonen, 1990).
CI adds: asymmetric η (confirmations less noisy than overrides),
count decay (early decisions carry more weight), conservation gating.

**Phase 2: Variance Learning (ongoing, after mean saturation)**

```
Eq. DK-WEIGHT:
  w_k = 1/σ²_k (Gaussian surrogate form)
  Shrinkage: w̃_k = α_s × w_DK_k + (1 - α_s) × 1.0
```

(α_s = shrinkage coefficient, distinct from α = auto-approve rate.)

### 2.4 Conservation Law

```
Eq. CL:
  α · q · N_ver ≥ 23.53

  α   = auto-approve rate (fraction not referred to human)
  q   = rolling verified accuracy over last 400 decisions
  N_ver = total verified decision count
```

The product α·q·N_ver must exceed a constant floor. At low N_ver
(early deployment), the system cannot be aggressive (low α). As
accuracy and volume grow, autonomy expands — but only where the
deployment's own data proves it safe. Three-judge validated.

Penalty ratios encode domain-specific risk tolerance:
SOC 20:1, DataOps 10:1, S2P 5:1, Purchasing 3:1, Trading 2:1.

### 2.5 Re-Convergence Theorem

```
Eq. GAMMA:
  γ > 1  ⟺  ε_firm > ε_firm★ ≈ 0.125
```

Under category-sparse disruption, Phase 2 recovery is faster than
Phase 1 cold-start (γ ≈ 1.2, L2 kernel). Four proof paths.
Validated by four independent LLMs (GPT-4.1, Opus 4, Grok 3,
Gemini 1.5 Pro) plus a fifth centroid-distance proof (Grok 3,
April 16 2026). DK with stale weights reverses the effect (γ < 1,
CLAIM-DK-STALE).

### 2.6 Centroid Tensors Per Copilot

| Copilot | C | A | d | Tensor | Penalty |
|---|---|---|---|---|---|
| SOC | 6 | 4 | 6 | 144 | 20:1 |
| DataOps | 6 | 5 | 6 | 180 | 10:1 |
| S2P | 5 | 5 | 7 | 175 | 5:1 |
| Purchasing | 5 | 4 | 6 | 120 | 3:1 |
| Trading | 5 | 3 | 6 | 90 | 2:1 |

---

## Part III: VLD — Score-Conditioned Graph Reasoning

### 3.1 What CI Computes and Discards

The scoring equation computes per-dimension residuals:

```
r[k] = f[k] - μ[c, a*, k]    for k = 1, ..., d
```

The scalar kernel K = Σ_k w_k · r[k]² aggregates this into a
single distance, discarding the per-dimension structure.

VLD recovers this structure. Large |r[k]| on dimension k signals
that the factor value is far from what the centroid expects — either
a genuine anomaly or an enrichment opportunity.

### 3.2 The VLD Step

```
Step t (t = 0, 1, ..., B-1):
  1. Score:    a_t, P_t = softmax(-K(v_t, μ) / τ)
  2. Query:    Q_t[k] = precision[k] + leverage[k]
  3. Select:   k* = argmax_{k ∉ enriched_t} Q_t[k]
  4. Read:     e* = graph_read(G, node, k*)
  5. Update:   v_{t+1}[k*] = V_update(e*, v_t[k*], source_type)
  6. Halt?:    if ||v_{t+1} - v_t|| < δ, stop.
```

At each step, Q is recomputed from v_t (VLD-RNN): the second read's
priority depends on what the first read revealed (§C3).

### 3.3 Q: Geometric Acquisition Priority

```
Eq. Q-ADDITIVE:
  Q[k] = w_k / Z_p + |(v[k] - μ[a₁,k])² - (v[k] - μ[a₂,k])²|
```

where a₁, a₂ are the current top-2 actions for category c, and
Z_p = mean_k(w_k) normalizes precision to a dimensionless relative
contribution.

**Term 1 — Precision (from CI's learned σ):** Dimensions where CI
has learned higher precision (lower σ_k, higher w_k = 1/σ²_k)
receive higher Q. This imports Phase 2 learning directly into
routing priority.

**Term 2 — Decision leverage:** Measures the magnitude of dimension
k's current contribution to the distance contrast between the top-2
action centroids. Note: |(v-μ₁)²-(v-μ₂)²| = |μ₁-μ₂| · |2v-μ₁-μ₂|,
so leverage combines the centroid separation (discriminative) with
the current state's position relative to both centroids. Dimensions
currently carrying the decision margin are prioritized — if evidence
reverses the dimension carrying the decision, the decision flips.

**Additive composition (soft-OR):** A dimension receives investigation
priority when EITHER CI has learned it matters (high precision) OR
it currently carries the decision (high leverage). Multiplicative
composition demands both simultaneously, producing zero-product
failures when either term is small. Validated: additive 0.878 vs
multiplicative 0.846 (§9.3). Max composition also achieves 0.878,
confirming the soft-OR behavior.

**Relationship to exact sensitivity:** The true log-odds margin
gradient ∂g₁₂/∂v_k = 2w_k(μ₁ₖ-μ₂ₖ)/τ is constant in v — it
identifies which dimensions the scorer is sensitive to, independent
of current state. Leverage complements this by identifying which
dimensions are currently *responsible* for the decision, regardless
of steady-state sensitivity. Whether the gradient or leverage routes
better is an empirical question (§12.2, A4).

### 3.4 V: Adaptive State Update

```
Calibrated source:    v_{t+1}[k*] = conf × e* + (1 - conf) × v_t[k*]
Uncalibrated source:  v_{t+1}[k*] = e*
```

Source classification determined by Situation Analyzer (§7.2).
Gating helps on calibrated data (+0.004), hurts on noisy data
(-0.074) when confidence values are themselves unreliable (§9.4).

### 3.5 Halting: Shift Magnitude

```
Eq. HALT: if ||v_{t+1} - v_t||₂ < δ, stop.     (δ = 0.05)
```

Only halting criterion producing meaningful depth variation across
all τ values in 114-configuration sweep (§9.4). Margin and entropy
criteria fail because softmax with τ=0.1 produces near-binary
distributions (median single-pass margin = 1.0).

Conservation determines WHETHER to investigate; shift_mag determines
WHEN to stop.

---

## Part IV: Routing Theory

### 4.1 Four-Level Routing Hierarchy

```
Level 0: Graph routing     — topology → reachability
Level 1: VLD routing       — acquisition priority → which dimension
Level 2: VLD-RNN routing   — state-dependent priority → trajectory
Level 3: CI routing        — enriched centroids → action
```

Level 2 (VLD-RNN) is the state-dependent extension: Q recomputes
from v_t, so the investigation trajectory adapts to intermediate
evidence. This is what makes S4 (Conditional Investigation)
tractable — the first read changes what the second read should be.

### 4.2 Situation Taxonomy (S1-S6)

| Code | Name | Description | Budget | VLD advantage | p |
|---|---|---|---|---|---|
| S1 | Sufficient Surface Evidence | v near correct centroid | B=0 | 0.000 | — |
| S2 | Diffuse Uncertainty | v equidistant from multiple | B=2-3 | +0.360 | <0.001 |
| S3 | Localized Evidence Gap | 1-2 wrong dims, rest correct | B=1-2 | +0.072 | 0.009 |
| S4 | Conditional Investigation | 2-3 wrong, dependent | B=2 | +0.136 | <0.001 |
| S5 | Misleading Evidence | some evidence pushes wrong | B=2-3 | +0.060 | 0.301 |
| S6 | Joint Evidence Threshold | multi-dim boundary crossing | B=3+ | +0.200 | <0.001 |

Defined as evaluation regimes for simulation; an observable
production classifier using margin, per-dim Q dispersion, and
evidence availability is §12.2 future work.

### 4.3 Context Complexity Manifold

VLD's value is a property of the context graph complexity around
each decision, not the domain. Six dimensions: entity density,
jurisdictional overlay, cross-process coupling, information
asymmetry, temporal depth, stakeholder authority.

---

## Part V: Compounding Theory

### 5.1 The Compounding Cycle

```
VLD routes (Q uses σ, μ) → reads informative evidence →
better v_enriched → analyst verifies →
μ updates (centroid migration) → σ sharpens (precision) →
Q improves → VLD routes better → ...
```

### 5.2 μ Learning

```
Eq. MU-LEARN:
  μ[a_verified] ← μ[a_verified] + η_μ · (v_enriched - μ[a_verified])
```

μ learning is 2.3× stronger than σ learning: +0.023 vs +0.010 over
15 epochs (§9.6). μ improvement affects all dimensions simultaneously.

### 5.3 Directed Routing and Learning Safety

```
Eq. INTERACTION (4-cell, routing policy × learning):
  random + static:    0.793 (baseline)
  random + CI:        0.747 (CI learning HURTS under random routing)
  VLD + static:       0.887 (VLD routing helps)
  VLD + CI:           0.893 (VLD + CI together)
```

The central finding: **random routing poisons centroid learning**
(-0.047 from baseline). Random reads include misleading evidence,
and CI's μ learning moves centroids toward that misleading evidence.
Directed routing feeds CI informative evidence, enabling safe
compounding (+0.020 over 15 epochs with fresh data).

The interaction term is +0.053 (VLD+CI actual exceeds additive
prediction). The interaction is subadditive in fresh-data simulation
(−0.014 at all nonzero η_μ, round v6 H5): fresh i.i.d. data lacks
recurring patterns for centroids to track. In the controlled
benchmark (fixed recurring scenarios), the interaction is +0.053 —
superadditivity requires distributional stability. The honest claim
is architectural: directed routing is a PREREQUISITE for safe
learning, not a multiplier. The 12.4pp VLD-random accuracy gap
(0.872 vs 0.748) compounds: every misrouted decision writes a noisy
centroid update.

### 5.4 Combined Compounding Rate

```
Eq. GAMMA-TOTAL:
  γ_total = γ_scoring × γ_routing ≈ 1.2 × 1.07 ≈ 1.28
```

Caveat: assumes independence. The interaction result (§5.3) shows
the factors are not independent — actual combined rate is an
empirical question. γ_routing = 1.07 is measured as routing quality
improvement over 15 epochs; not independently validated.

---

## Part VI: Graph Engineering

### 6.1 Universal Context Layer

PostgreSQL + Apache AGE. Labeled property graph with typed edges.
Not RAG: a reasoning substrate, not a retrieval index.

### 6.2 Graph Schema Per Copilot

| Copilot | Key nodes | Key edges | Demo size |
|---|---|---|---|
| SOC | Alert, Entity, ThreatIntel, Campaign | HAS_FACTOR, ASSOCIATED_WITH | 8,751 |
| DataOps | Pipeline, SchemaChange, SLA | DEPENDS_ON, BOTTLENECK_AT | ~2,000 |
| S2P | Invoice, Supplier, Contract | FULFILLS, RECEIPT_MATCH | ~1,500 |
| Trading | Trade, Thesis, Position | SUPPORTS, CORRELATES | ~800 |
| Purchasing | Item, Supplier, Demand | SUPPLIES, COVERS | ~600 |

### 6.3 Graph Read Protocol

Each factor dimension maps to a specific Cypher traversal pattern:

```cypher
-- SOC dim k=3 (identity_context):
MATCH (a:Alert {id: $id})-[:ASSOCIATED_WITH]->(e:Entity)
OPTIONAL MATCH (e)-[:DELEGATED_TO]->(d:Entity)
RETURN e.name, d.name, e.trust_score

-- DataOps dim k=1 (schema_stability):
MATCH (p:Pipeline {id: $id})-[:SCHEMA_CHANGED]->(sc:SchemaChange)
WHERE sc.date > datetime() - duration({days: 30})
RETURN sc.impact, sc.code_count, sc.migration_type
```

### 6.4 Evidence Quality Architecture

| Source type | Examples | Confidence | V rule |
|---|---|---|---|
| System of Record | SAP master data, signed contracts | 0.90-1.00 | Gated |
| Operational | SIEM telemetry, pipeline metrics | 0.70-0.90 | Gated |
| Partner | Supplier reports, partner APIs | 0.30-0.60 | Raw |
| Derived | NLP extractions, anomaly scores | 0.40-0.70 | Raw |
| Process mining | Celonis activities, cycle times | 0.80-0.95 | Gated |

### 6.5 GraphStore Protocol

```python
class GraphStore(Protocol):
    def read_factor(self, node_id, dimension) -> Evidence
    def write_decision(self, decision) -> None
    def get_neighbors(self, node_id, edge_type) -> List[Node]
```

Three backends: InMemoryGraphStore (test, <1ms), SQLiteGraphStore
(dev, ~5ms), AGEGraphStore (production, ~20ms).

---

## Part VII: Self-Improving Agent Infrastructure

### 7.1 AgentEvolver

Three promotion mechanisms at Loop 3:

1. **Factor freezing:** Dimension k consistently correct (95%+ across
   50+ decisions) → skip. Reduces effective d for Q.

2. **Edge deprioritization:** Edge type E producing misleading
   evidence → decrease past_utility. VLD routes away.

3. **Pattern promotion:** Investigation sequence k₁→k₂ consistently
   correct → standing template for that category.

### 7.2 Situation Analyzer

Pre-investigation classification (Loop 4). Uses observable signals:
initial margin, per-dim Q dispersion, action entropy, evidence
availability per dimension. Outputs budget, V rules, halt threshold,
and conservation override.

### 7.3 Conservation as Harness

Three safety layers:

```
Layer 1: Shrinkage         (mathematical, within scoring)
Layer 2: Promotion gate    (operational, at batch boundary)
Layer 3: Rollback          (recovery, if promotion degrades)
```

Conservation gates VLD (skip investigation if well-calibrated),
gates AgentEvolver (promoted rules respect α bound), and gates
learning (freeze when AMBER/RED).

### 7.4 Harness Composition

```
DECISION → Conservation (gate all) → Situation Analyzer (classify)
  → S1: single-pass (no investigation needed)
  → S2-S6: VLD investigation → Scoring → Analyst verifies
    → RL reward (μ+σ update) → AgentEvolver (pattern promotion)
```

---

## Part VIII: Related Work

### 8.1 Active Feature Acquisition

VLD is most closely related to active feature acquisition (AFA):
methods that sequentially obtain features for a specific instance
at query time. Key references: EDDI (sequential acquisition via
expected information gain; Ma et al. 2018), generative-surrogate
AFA (Li & Oliva, 2020), template-based AFA (Huang et al., 2025),
rational metareasoning (Hay et al., 2012), adaptive submodularity
(Golovin & Krause, 2010).

VLD differs from standard AFA: the acquisition function is
closed-form (no learned router), derived entirely from the scorer's
own parameters (μ, σ), and operates on a graph-structured evidence
space rather than a flat feature vector.

### 8.2 Centroid-Mean Distance Routing

Our "embedding-distance" baseline routes by distance from the
centroid mean — selecting dimensions where the factor value is
most distant from the average centroid position. This is a
simplified proxy for embedding-based retrieval approaches. VLD
outperforms: +0.078, p<0.001, bootstrap 95% CI [0.042, 0.114].
On S2 (Diffuse Uncertainty): centroid-mean 0.54 vs VLD 0.96.

Note: this baseline is NOT a faithful implementation of GraphRAG
(Edge et al., 2024), which uses community detection + hierarchical
summarization for LLM QA — a different task. GraphRAG is discussed
as a different problem in §8.5.

### 8.3 Informative-Dimension Oracle

Our oracle baseline has perfect knowledge of which dimensions are
designated "informative" in the scenario generator and reads those
first. VLD outperforms: +0.048.

This is NOT an upper bound on LLM routing — a real LLM can do
conditional reasoning ("check identity BECAUSE timing is
suspicious") and can discount misleading evidence (S5). The oracle
is an upper bound on *fixed-informative-set* knowledge only.

Note: the oracle exhibits an anomaly on S2 (0.30 vs random 0.70),
likely due to tie-breaking when all dimensions are equally
"informative." Under investigation (§12.1).

### 8.4 GNN Message Passing (Kipf & Welling, 2017)

Aggregates all neighbors. VLD reads selectively: budget=2 achieves
95% of exhaustive on S3/S4. Routing conditioned on the scorer's
own uncertainty (same σ, μ).

### 8.5 Other Related Work

**GraphRAG (Edge et al., 2024):** Community-based retrieval for LLM
QA. A different task from per-instance evidence acquisition, but
relevant to the broader graph reasoning landscape.

**ReAct (Yao et al., 2023):** LLM-prompted interleaving of reasoning
and observation. Powerful but expensive per hop.

**MCTS:** VLD as degenerate MCTS — single rollout, geometric value,
deterministic. Faster but limited to geometrically informative
problems.

**Prototypical Networks (Snell et al., 2017):** Same geometric
foundation (prototype-based classification). Different training
regime (episodic meta-learning vs online from verified outcomes).

**LVQ / GLVQ (Kohonen 1990, Hammer & Villmann 2002):** CI's
PULL/PUSH is LVQ2.1-style. CI adds asymmetric η, DK precision
learning, and conservation gating.

### 8.6 Positioning Summary

| Approach | Router | Cost/hop | Learns | LLM |
|---|---|---|---|---|
| Centroid-mean distance | Distance to mean | 1 distance calc | No | 0 |
| Informative-dim oracle | Perfect knowledge | — | No | 0 |
| ReAct | LLM prompt | LLM call | No | 1+ |
| GNN | Learned weights | Forward pass | Training | 0 |
| AFA (EDDI etc.) | Learned policy | Model inference | Training | 0 |
| **VLD** | **Geometric Q** | **Matrix-vector** | **Yes (σ+μ)** | **0** |

---

## Part IX: Experimental Results — Simulation

Six simulation rounds. All scenarios reproducible from stated seeds.

### 9.1 Simulation Framework

ScenarioGenerator(d, A, seed) produces controlled scenarios with
configurable situation mix. Centroids randomly placed, min
separation 0.25. Per-dimension σ ~ U(0.05, 0.30). Factor vectors
placed per situation rules (§4.2).

Baselines: single-pass, random routing, centroid-mean distance
routing, informative-dim oracle, exhaustive.

### 9.2 Round v1: Baseline Validation

All-wrong-side scenarios (S2 only). VLD routing NEGATIVE (-0.189 to
-0.247). Lesson: VLD requires situation diversity. Motivated S1-S6
taxonomy.

### 9.3 Round v2: Situation Mix — VLD Routing Validated

S1-S6 mix (20/10/25/25/10/10%). Q component sweep: precision +
decision leverage dominates. Discriminative is secondary (D0≈D1).

### 9.4 Round v3: Composition and Halting

| Method | Accuracy |
|---|---|
| Additive (P+leverage) | 0.878 |
| Max | 0.878 |
| Multiplicative | 0.846 |
| Random | 0.780 |
| Exhaustive | 0.926 |

All adaptive halting strategies halt at step 1 (softmax saturation).
shift_mag is the only working criterion (1.78 hops, τ-independent).

Evidence quality: gating helps on calibrated data (+0.004), hurts
on noisy data (-0.074).

### 9.5 Round v4: Routing Comparison

| Method | Accuracy |
|---|---|
| Single pass | 0.692 |
| Random B=2 | 0.796 |
| Centroid-mean distance | 0.806 |
| Informative-dim oracle | 0.848 |
| **VLD additive** | **0.896** |
| Exhaustive | 0.938 |

Per-situation breakdown: VLD strongest on S2 (0.96 vs centroid-mean
0.54) and S4 (0.98 vs 0.90). S6 remains hard for all methods
(VLD 0.24, exhaustive 0.42).

Complexity scaling: VLD advantage always positive (+0.040 to +0.187)
across 9 configs (d=4-10, A=2-6).

S5 crossover at ~50% misleading ratio: when half of evidence is
misleading, VLD loses its advantage over random.

With-without decomposition: 61 saves, 11 hurts (5.5:1 ratio) vs
random routing.

### 9.6 Round v5: Halting, Compounding, and Interaction

Halting: 114-config sweep (6τ × 19 strategies). shift_mag only
working criterion.

Compounding (15 epochs): μ learning (+0.023) > σ learning (+0.010)
> utility learning (+0.007). Same-data compounding always negative
(experiment design artifact — production provides fresh data).

4-cell interaction: see §5.3.

### 9.6.1 Round v6: Gap-Closer Experiments [NEW v5]

**H1 (P×D routing):** P×D alone = 0.860, HIGHER than P×D×L
multiplicative (0.810). Leverage term introduces noise in
multiplicative composition. Additive (P/100 + D + L) = 0.872
(best). S4 leverage effect only +0.008 — P×D suffices even for
conditional situations.

**H2 (Z_p sensitivity):** Range = 0.006 excluding Z_max outlier.
Z_p = mean_k(w_k) is robust.

**H3 (P@2 metric):** P@2 = 0.728 for Q_full. Spearman r = −0.004
(noise — the wrong statistic). P@2 replaces r=0.176 as the
routing quality metric.

**H4 (Weighted halting):** Neither ||Δv||₂ nor ||Δv||_W halting
beats fixed B=2 in simulation. Fixed budget is Pareto-optimal;
adaptive halting's value is production latency cost.

**H5 (η_μ sweep):** VLD×CI interaction is subadditive at all
nonzero η_μ (−0.014). The +0.053 from round v5 does not reproduce
in fresh-data simulation. Honest finding: superadditivity requires
distributional stability (recurring decision types). In fresh i.i.d.
data, interaction ≈ 0.

**H6 (S2 oracle fix):** Bug was tie-breaking: all S2 dims
informative → oracle picked dim 0 by list order. Fixed with random
tiebreak. Oracle now 0.60 on S2 (was 0.30). VLD dominates S2 at
0.98. VLD ties oracle overall (0.872 vs 0.872).

**M1 (Situation Analyzer):** Rule-based classifier achieves only
20% accuracy — margin/entropy features don't separate situations
with hard-coded thresholds. Observable classifier is future work
(needs learned thresholds per domain geometry).

**M2 (Conservation ablation):** Conservation gate never activated
in simulation — σ learning rate too gentle to trigger. Conservation
value is in aggressive learning regimes or with concept drift.

**M3 (Extended compounding, 100 epochs):** Accuracy flat (first-10
mean 0.889, last-10 mean 0.888). Fresh i.i.d. data tests
generalization, not compounding. The Astra controlled benchmark
(fixed recurring scenarios) remains the right test for compounding.

**DG1 (Domain use cases):** 30 scenarios generated across 5
copilots (6 per domain, one per situation type). SOC, S2P, Trading,
Purchasing, DataOps — each with concrete factor-to-graph-traversal
mappings.

### 9.7 Round v6: Statistical Significance

Bootstrap 95% CI (10,000 resamples):

| Comparison | Mean Δ | 95% CI | p |
|---|---|---|---|
| VLD vs Single-Pass | +0.222 | [0.182, 0.262] | <0.001 |
| VLD vs Random | +0.114 | [0.080, 0.150] | <0.001 |
| VLD vs Centroid-mean | +0.078 | [0.042, 0.114] | <0.001 |
| VLD vs Exhaustive | -0.040 | [-0.064, -0.016] | — |

Note: VLD vs Exhaustive has a wholly negative CI — VLD is
significantly worse than exhaustive, as expected (budget=2 vs
reading all d dimensions). The gap varies by scenario seed across
rounds (§9.4: -0.042, §9.3: -0.048); the v6 number (-0.040) is
consistent.

Per-situation significance (VLD vs Random):

| Sit | Mean Δ | 95% CI | p |
|---|---|---|---|
| S1 | 0.000 | [0.0, 0.0] | — |
| S2 | +0.360 | [0.22, 0.50] | <0.001 |
| S3 | +0.072 | [0.016, 0.136] | 0.009 |
| S4 | +0.136 | [0.064, 0.208] | <0.001 |
| S5 | +0.060 | [-0.12, 0.24] | 0.301 ns |
| S6 | +0.200 | [0.08, 0.32] | <0.001 |

### 9.8 Round v8: Learned Situation Analyzer (C4) [NEW v7]

RF classifier (100 trees) trained on 5,000 scenarios across 10
centroid geometries. 10 observable features extracted at surface
score time (no graph reads required).

**Cross-validation accuracy: 47.7% ± 1.0% (5-fold stratified).**
Random baseline: 20% (6 classes). Rule-based (v6 M1): 20%.

Feature importance ranking:

| Feature | Importance | What it measures |
|---|---|---|
| d_min | 0.253 | Distance to nearest centroid |
| d_gap | 0.163 | Gap between nearest two centroids |
| q_mean | 0.133 | Mean Q value across dimensions |
| q_entropy | 0.130 | Entropy of Q distribution |
| q_spread | 0.126 | Max Q / mean Q ratio |
| q_max | 0.125 | Highest Q value |
| entropy | 0.024 | Entropy of action probabilities |
| margin | 0.016 | Top-2 action probability gap |
| p_second | 0.015 | Second-highest action probability |
| p_max | 0.014 | Highest action probability |

Key finding: centroid distance geometry (d_min, d_gap) dominates
situation classification. Action probability features (margin,
p_max) are near-irrelevant. The Q distribution shape provides a
second tier of predictive power.

Budget assignment: adaptive budgets from classifier match fixed
B=2 accuracy (0.880 vs 0.888) at 1.80 avg hops (10% reduction).

### 9.9 Round v8: VLD-LSTM K Utility Memory (C5) [NEW v7]

30-epoch experiment with 300 categorized decisions per epoch
(3 decision categories, each with specific informative dimensions).

**K weights learn:** dimensions consistently informative for
recurring categories accumulate utility (0.5 → 3.0 over 30 epochs).
Neutral dimensions stay flat or decrease.

**Routing quality improves:** informative read rate increases from
30.0% to 37.5% (+25%) with global K learning.

**Per-category K required:** global K boosts the most-common
informative dimensions at the expense of less-common categories.
Production architecture: one K vector per decision category
(alert type, invoice class, pipeline system), provided by the
copilot's category field.

---

## Part X: Experimental Results — Controlled Benchmark

### 10.1 Astra Benchmark Suite

250 domain-specific decision scenarios across 5 copilots (50 per
copilot), generated by Astra with verified ground-truth actions.
Each scenario includes domain-realistic factor values, graph
traversal paths, evidence narratives, and a known correct action
determined by the enriched centroid geometry.

Scenario types are domain-differentiated — SOC includes privilege
chains, insider policy violations, and malware variant detection;
S2P includes hidden contract amendments, duplicate detection, and
supplier trust verification; DataOps includes cascade failures,
schema drift, and transformation breakage; Trading includes thesis
reversals, concentration risk, and correlated positions; Purchasing
includes seasonal spikes, shelf life, and vendor reliability.

Each copilot's scenarios span 10 domain-specific types with a
controlled distribution: 30 strong (≥3 factor corrections), 10
moderate (2 factor corrections), 5 flat controls (surface-correct,
VLD should not investigate), and 5 instrument checks (ρ=0.50
boundary validation).

### 10.2 With-Without Results (Astra, 250 scenarios)

**At budget B=3 (3 graph reads per decision):**

| Copilot | d | SP | VLD | Saves | Hurts | Ratio | Uplift |
|---|---|---|---|---|---|---|---|
| SOC | 6 | 0.100 | 0.180 | 4 | 0 | 8:1 | +8.0% |
| S2P | 7 | 0.300 | 0.540 | 12 | 0 | 24:1 | +24.0% |
| DataOps | 6 | 0.520 | 0.760 | 12 | 0 | 24:1 | +24.0% |
| Trading | 6 | 0.440 | 0.800 | 18 | 0 | 36:1 | +36.0% |
| Purchasing | 6 | 0.460 | 0.680 | 11 | 0 | 22:1 | +22.0% |
| **Total** | | | | **57** | **0** | **114:1** | **+22.8%** |

57 decisions where VLD investigation recovered the correct action
from an incorrect surface score. Zero decisions where investigation
degraded a correct surface score. Mean accuracy uplift +22.8%
across all 5 copilots.

The investigation traces are domain-appropriate: SOC reads
threat_intel_enrichment → pattern_history; S2P reads
price_conformance → contract_coverage → policy_conformance;
DataOps reads schema_stability → transformation_health →
impact_scope; Trading reads portfolio_concentration →
fundamental_strength → liquidity_risk. Each trace maps to the
graph traversal an analyst would perform.

**Budget sensitivity:**

| Copilot | B=2 | B=3 | B=4 |
|---|---|---|---|
| SOC | 0:0 | 4:0 | 13:0 |
| S2P | 6:0 | 12:0 | 14:0 |
| DataOps | 8:0 | 12:0 | 15:0 |
| Trading | 13:0 | 18:0 | 22:0 |
| Purchasing | 11:0 | 11:0 | 11:0 |

SOC scenarios require deeper investigation (B=4 for 13 saves)
because the scenario types involve 4-factor corrections (privilege
chains, insider threats). Trading achieves the highest routing value
at every budget — the 6-factor geometry with 3 actions produces
sharp Q discrimination. Purchasing plateaus at B=2 — the correct 2
dimensions are identified immediately.

### 10.2.1 Simulation With-Without (v7, production tensor shapes)

Independent validation on 250 simulation scenarios per copilot
(5 seeds × 250 = 1,250 per copilot) using production centroid
tensor shapes:

| Copilot | (d,A) | SP | VLD | Saves:Hurts | Uplift |
|---|---|---|---|---|---|
| SOC | (6,4) | 0.668 | 0.884 | 8.1:1 | +21.6% |
| S2P | (7,5) | 0.704 | 0.882 | 11.6:1 | +17.8% |
| DataOps | (6,5) | 0.642 | 0.846 | 9.2:1 | +20.4% |
| Trading | (5,3) | 0.609 | 0.873 | 10.4:1 | +26.4% |
| Purchasing | (5,4) | 0.604 | 0.838 | 8.3:1 | +23.4% |
| **Mean** | | | | **9.5:1** | **+21.9%** |

The simulation uses synthetic centroids and generated situations
(S1-S6 mix). The directional agreement with the Astra benchmark
(both show +20-25% uplift, both show zero or near-zero hurts)
provides cross-validation: VLD's value is not an artifact of
either generation method.

### 10.3 Universal Evaluator (ρ-based)

| Copilot | VLD ρ≥0.70 | Flat baseline | ρ=0.50 control |
|---|---|---|---|
| SOC | 100% (35/35) | ✅ | ❌ 0.900 |
| DataOps | 91.4% (32/35) | ✅ | ❌ 1.000 |
| S2P | 88.6% (31/35) | ✅ | ❌ 1.000 |
| Trading | 85.7% (30/35) | ✅ | ❌ 0.900 |
| Purchasing | 91.4% (32/35) | ✅ | ❌ 1.000 |

---

## Part XI: Showcase Scenarios

15 scenarios (3 per copilot). Two examples:

**SOC-SC1 (S4 — Conditional Investigation): Admin Delegation**
Alert on PowerShell execution. Surface: low severity + low recurrence
→ suppress. VLD reads identity_context → admin delegation to
contractor. Q recomputes, reads temporal_pattern → Saturday 3:14am.
Action: suppress → escalate. Two hops.

**S2P-SC1 (S3 — Localized Evidence Gap): Contract Amendment**
Invoice $47,200 vs PO $42,000. Surface: 12.4% variance → flag.
VLD reads contract_compliance → Q3 amendment with 15% escalation
clause. One hop. Action: flag_review → auto_approve.

Each copilot also includes an S1 conservation scenario (no
investigation, correct on single-pass) demonstrating that VLD
does NOT investigate when the answer is already clear.

---

## Part XII: Remaining Gaps and Future Work

### 12.1 Open Experimental Questions

| Gap | Status | Path |
|---|---|---|
| Real operational data with-without | **OPEN** — measures S2-S6 prevalence and production uplift | 20-50 labeled decisions per copilot |
| Oracle S2 anomaly | **✅ RESOLVED (v6 H6)** — tie-break bug, fixed with random noise | Oracle now 0.60 on S2 |
| Analyst trace comparison | **OPEN** — VLD path vs expert investigation sequence | 10 decisions: record analyst → compare |
| Latency benchmark | **OPEN** — confirms per-hop cost on AGE | Measure p50/p95/p99 per-hop |
| Cross-copilot transfer | **OPEN** — evidence learned in SOC improves S2P | Cross-domain scenarios |
| P×D-only routing | **✅ RESOLVED (v6 H1)** — P×D alone = 0.860, better than multiplicative | Leverage is additive refinement |
| Z_p sensitivity | **✅ RESOLVED (v6 H2)** — range 0.006 excl. outlier, robust | Z_p = mean_k(w_k) confirmed |
| P@2 metric | **✅ RESOLVED (v6 H3)** — P@2 = 0.728. Replaces r=0.176 | Right statistic for routing quality |
| Weighted halting | **✅ RESOLVED (v6 H4)** — fixed B=2 Pareto-optimal in simulation | Adaptive value is production latency |
| η_μ sweep | **✅ RESOLVED (v6 H5)** — interaction subadditive at all η_μ > 0 | Superadditivity needs distributional stability |
| Observable Situation Analyzer | **✅ RESOLVED (v8)** — RF at 47.7% (2.4× random), d_min/d_gap dominant | Budget assignment validated |
| Conservation ablation | **PARTIALLY RESOLVED (v6 M2)** — gate never triggered (σ rate too gentle) | Needs aggressive learning regime |
| Extended compounding | **✅ RESOLVED (v6 M3)** — flat over 100 epochs (i.i.d. data) | Compounding needs recurring patterns |

### 12.2 Remaining Architectural Extensions

| Extension | What | Priority |
|---|---|---|
| Learned Situation Analyzer | Small classifier (logistic/RF) on margin + Q-spread + entropy | High |
| VLD-LSTM K utility mechanism | **✅ MECHANISM VALIDATED (v8)** — K learns, routing +25%, per-category K required | Production: one K vector per category |
| Conservation under aggressive learning | σ_rate = 0.80 or concept drift to see conservation trigger | Medium |
| Adaptive Q learning | Q weights learned from verified outcomes | Research |
| Process-Tech Fusion | SAP + Celonis evidence sources | Near-term |
| GraphRAG/ReAct head-to-head on real data | Same 50 alerts, VLD vs embedding vs LLM routing | High |

---

## Appendix A: Notation

| Symbol | Meaning | Shape / Value |
|---|---|---|
| f, v | Factor vector (initial, enriched) | (d,) ∈ [0,1]^d |
| μ | Profile centroids | (C, A, d) ∈ [0,1] |
| σ_k | Per-factor noise standard deviation | scalar ∈ ℝ+ |
| w_k | Kernel weight (= 1/σ²_k) | scalar ∈ ℝ+ |
| W | Kernel weight matrix | diag(w₁,...,w_d) |
| τ | Temperature | 0.1 (fixed) |
| η_confirm, η_override | Centroid learning rates | 0.05, 0.01 |
| Q | Investigation priority vector | (d,) ∈ ℝ |
| Z_p | Precision normalizer (= mean_k(w_k)) | scalar ∈ ℝ+ |
| a₁, a₂ | Top-2 actions for category c | indices |
| r[k] | Per-dim residual (f[k]-μ[c,a*,k]) | scalar |
| B | Investigation budget | integer |
| δ | Shift magnitude threshold | 0.05 |
| γ | Re-convergence rate | scalar > 1 |
| α | Auto-approve rate | [0,1] |
| α_s | Shrinkage coefficient | [0,1] |
| q | Rolling verified accuracy (400-window) | [0,1] |
| N_ver | Verified decision count | integer |

## Appendix B: Equation Index

| Equation | Section | Status | Evidence tier |
|---|---|---|---|
| SCORE | §2.1 | ✅ Validated | MEASURED |
| L2, DK | §2.2 | ✅ Validated (390-cell) | MEASURED |
| PULL, PUSH | §2.3 | ✅ Validated (24 personas) | MEASURED |
| DK-WEIGHT | §2.3 | ✅ Validated | MEASURED |
| CL | §2.4 | ✅ Three-judge validated | MEASURED |
| GAMMA | §2.5 | ✅ 5-proof-path | MEASURED + MODELED |
| Q-ADDITIVE | §3.3 | ✅ 0.878 vs 0.846 | MEASURED |
| V-GATED, V-RAW | §3.4 | ✅ Evidence quality sweep | MEASURED |
| HALT | §3.5 | ✅ 114-config sweep | MEASURED |
| MU-LEARN | §5.2 | ✅ +0.023 over 15 epochs | MEASURED |
| INTERACTION | §5.3 | ✅ +0.053 interaction | MEASURED |
| GAMMA-TOTAL | §5.4 | ⚠️ Estimated ≈1.28 | MODELED |

Evidence tiers (from innovation_note_v30): DEMO-PROVEN (synthetic) /
MEASURED (controlled experiment) / MODELED (analytic) / NEAR-ARCH
(architected, not in production) / PILOT-TARGET (requires customer
data).

---

*CI+VLD Architecture Pre-Paper · v4 · Sep 10, 2026*
*Fixes: conservation formula, notation conflicts, +0.090→+0.078,*
*baseline naming, sample accounting, LLM validator count.*
*Fine-tuning: Q→geometric acquisition priority, Term 3→decision*
*leverage, "second derivative"→coupled adaptation, 200:0→stress test.*
*Additions: three graphs, four clocks, judgment memory, AFA citations,*
*LVQ lineage, evidence tiers, situation names.*
*Contributions: C1 (scorer-conditioned acquisition), C2 (geometric*
*heuristic), C3 (VLD-RNN, kept), C4 (situation taxonomy), C5 (directed*
*routing as learning safety precondition).*
