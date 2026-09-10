# VLD — Graph-Based Reasoning over Investigation Trajectories
## Deep-Dive Technology, Mathematics & Architecture Memo
**Version:** v4 · **Date:** Sep 8, 2026
**Status:** Working document — incorporates v2 judge feedback + Patel et al. 2026
**Supersedes:** v3 (adds §7.1 persistent semantic context, §7.2 DataOps elevation)

---

## 1. Executive Summary

VLD adds a **governed investigation loop** to CI's existing decision-loops. It
enhances graph-based reasoning by conditioning each evidence retrieval on the
results of prior retrievals — "the second question depends on the first answer."

**Value gates** (all three must hold — these are gates, not multiplicands):
- **m_conditional** > 0 — some hard-tail decisions have conditional investigation
  structure
- **ρ** > comparator — the scorer routes to the correct branch more often than
  the best alternative policy
- **budget < branches** — exhaustive retrieval is infeasible (cost, time, or access)

**What is validated:** The ρ calibration instrument works (Sim 1, correlation 0.986).
VLD dominates at budget=1 by +18.5pp (Sim 2). The mechanism is real in controlled
conditions.

**What is NOT validated:** Whether ρ > comparator on CI's real scorer with real
cases (O-1). Whether conditional branching exists at sufficient density in real
deployments (R2). Whether the time savings translate to analyst workflow (R5).

**These are hypotheses with a validated instrument, not confirmed findings.** §9
("Making It Real") is the structured plan to get real numbers.

---

## 2. CI's Loop Architecture and Where VLD Fits

### 2.1 The existing governed decision-loops

CI is five domain copilots on one shared engine. Beneath all five is the Graph
Attention Engine (GAE) and a set of **governed decision-loops** — parallel,
composable capabilities on a shared substrate:

| Loop | What | Timescale |
|---|---|---|
| **Score → Learn** | Observation → factors → centroid-distance → action; outcome → update μ | Per-decision / per-verification |
| **RL Reward** | Second-derivative rewards, credit assignment | Per-batch |
| **AgentEvolver** | Generate/evaluate/promote variant rules | Per-cycle (days) |
| **SituationAnalyzer** | Dispatch static traversal patterns over graph | Per-decision |
| **Process-Tech Fusion** | Cross-system evidence integration | Per-decision |
| **Conservation** | Eligibility gate — governs all other loops | Continuous |

### 2.2 VLD's architectural placement

VLD is a **controller above SituationAnalyzer and below the scorer**. SA
dispatches static traversal patterns. VLD is a **policy over SA patterns**
conditioned on the current scoring state v_t.

```
Conservation (eligibility gate — emit or abstain)
  └─ Scorer (centroid-distance classification from v_L)
      └─ VLD (state-conditioned policy over SA patterns)
          └─ SituationAnalyzer (static traversal patterns)
              └─ Evidence Graph (GAE substrate)
```

This is the cleanest inspectability story: "which SA pattern was dispatched at
step t, and why (what was v_t, what did a*(v_t) indicate)."

**Runtime dependencies:** VLD orchestrates SA traversal, evidence integration, and
scoring within an episode. These have a call relationship even though they are
organizationally peer capabilities.

**Mutation ownership:**
- Score → Learn: updates judgment state (μ, α)
- RL Reward: evaluates outcomes and acquisition costs
- AgentEvolver: proposes permitted Ψ variants for separate evaluation and promotion
- VLD: appends investigation traces (read-only during episode; no mutations to μ
  or active policy during investigation)

### 2.3 Conservation as eligibility gate (not per-step halt)

Within a single investigation episode, q, α, V are fixed. Conservation status is
**constant throughout the trajectory** — it cannot transition mid-investigation.
Conservation is an **eligibility gate at emit**: the system may act on the result
(GREEN) or must abstain (RED). It is not a per-step stopping criterion.

**Per-step stopping** uses C4-class controls:
- **Update-target residual:** ||E(S_{t+1}) − v_t|| / max(||v_t||, floor) < δ
  (evidence quality diminishing — note: unchanged v_t doesn't mean no valuable
  next read exists; a selector read can enable the decisive acquisition)
- **Budget exhaustion:** total evidence nodes read ≥ B_max
- **Flip-count:** top-1 action a*(v_t) changed > k times (oscillation)

### 2.4 Trace → outer loop feedback

VLD appends investigation traces per episode. Traces feed the outer loops:
- RL Reward computes outcome-level credit (which terminal action was correct)
- **Step-level credit is an estimator, not a direct observation.** A verified
  terminal outcome does not identify which retrieval step caused the improvement.
  Step credit requires counterfactual replay or logged exploration with propensities
  (Dudík et al., 2011). A deterministic handcrafted Ψ logs no exploration, so
  step-level credit is unidentifiable except from natural variation across cases.
- AE can generate shadow Ψ variants that provide the needed variation — but this
  must be explicitly designed, not assumed.

**Trace logging must record:** candidate reads, selected edges, propensities (when
exploration exists), costs, timestamps, policy version, stopping reason, and outcome.
Not only evidence sets and vectors.

### 2.5 The μ train/serve skew (flagged, unresolved)

If centroids μ are updated from fully-investigated vectors v_L, but routing scores
partially-revealed v_t against them, there is a representation mismatch. Centroids
become prototypes of fully-investigated decisions while intermediate scores compare
partially-revealed evidence against them. This systematically biases ρ downward.

**Status:** Unresolved. This could be the single biggest driver of real-world ρ.
Options: (a) update μ from v_0 not v_L (loses investigation value); (b) maintain
separate "routing centroids" from intermediate states; (c) accept the skew and
measure its effect empirically. **R1 will reveal the magnitude.**

---

## 3. Decisions as Investigation Trajectories

### 3.1 The formalism

A **Decision** is:

    D = (s₀, τ, a, o, c)

- **s₀ ∈ V** — initial observation (trigger node)
- **τ = [(S₀, v₀), (S₁, v₁), ..., (S_L, v_L)]** — investigation trajectory
- **a = a*(v_L) ∈ A** — terminal action
- **o ∈ O** — verified outcome (when available)
- **c ∈ {COLD_START, BOOTSTRAP, GREEN, RED}** — conservation eligibility

### 3.2 Trajectory as first-class entity

The trajectory IS the reasoning. It is what makes the system auditable. For each
step: which SA pattern was dispatched, what evidence was admitted, how v changed,
what the intermediate a* was, and why.

### 3.3 Self-computation over trajectories

The system can analyze its own trajectory statistics to identify which investigation
patterns produce correct outcomes. This feeds AE's variant generation (sidecar
variants that adjust routing parameters within the current Ψ structure).

**N3 clarification:** AE may evolve Ψ parameters (branch weights, pattern selection
thresholds, read-order preferences) but NOT Ψ structure (which SA patterns are
available, how they compose, the graph schema they traverse). Parameter vs structure
boundary: parameters are numeric values that adjust existing routing logic; structure
is the code that defines what routing logic exists.

---

## 4. Acquisition Structure

### 4.1 Taxonomy (attributes, not exclusive bins)

Evidence acquisition has three independent attributes:

**Accessibility:**
- Direct: all decisive evidence immediately reachable from s₀
- Prerequisite: evidence must be read in a fixed order (pointer-following)
- Conditional: the useful next read depends on what the last read showed

**Cost:**
- Free: reads have no resource cost (simulation-only; not realistic)
- Costly: reads consume budget (time, compute, API calls, analyst attention)
- Misleading: wrong-branch reads actively pull toward incorrect classification

**Coupling:**
- Independent: each decision's evidence is separate
- Shared: multiple decisions can cache/reuse evidence (coordinated retrieval)
- Coupled: decisions interact through utility or constraints (requires joint optimization)

### 4.2 The critical distinction: content-keyed vs score-keyed branching

**Content-keyed:** The first read literally SAYS which branch to follow. "Mismatch
type = price" → check contract. "Alert category = credential" → check auth trail.
A rule resolves this with ρ = 1 and full inspectability. No scorer needed.

**Score-keyed:** The branch is NOT legible in the evidence. The scorer's intermediate
state v_t, compared against centroids, infers which investigation path is more
likely productive. This is where VLD's distinctive claim lives — and ONLY here.

**Most of the §4.3 examples from v2 are content-keyed.** A buyer will notice. The
honest framing: content-keyed branching is valuable (it's structured investigation)
but any rule engine can do it. VLD earns its keep on score-keyed branching — cases
where the evidence doesn't say which way to go and the learned judgment geometry
provides the routing signal.

**Real score-keyed examples (harder to find, more honest):**
- SOC: alert with mixed indicators (credential AND process anomalies) — the relative
  factor weights in v_t determine which investigation path is more promising
- S2P: invoice exception where the mismatch type is ambiguous (could be price OR
  receipt) — the scorer's confidence distribution across categories determines
  which to check first
- DataOps: pipeline alert where the signature is consistent with both upstream and
  downstream causes — the scorer's experience with similar past alerts routes the
  investigation

### 4.3 Where each policy earns its value

| Acquisition type | Best policy | Why |
|---|---|---|
| Direct | Single-pass | One read resolves |
| Prerequisite (fixed order) | Multi-step traversal without scorer feedback | Follow pointers — GraphRAG territory, real but not VLD-specific |
| Conditional, content-keyed | Rule-based routing | Evidence says where to go; ρ = 1 by construction |
| Conditional, score-keyed | VLD (when ρ > comparator AND budget constrained) | Only the scorer can infer the branch; this is VLD's distinctive claim |

VLD's addressable market is the last row. The question is how large that row is
in real deployments.

---

## 5. The Value Model

### 5.1 Value gates (not multiplicands)

Three conditions gate VLD value. Present as gates, not as a product:

**Gate 1 — Conditional structure exists (m_conditional > 0):**
Some fraction of the hard tail has score-keyed conditional investigation structure.
If all branching is content-keyed or direct, VLD adds nothing.

**Gate 2 — Scorer routes better than alternatives (ρ > comparator):**
ρ = P(scorer's intermediate a*(v_t) points to the correct branch). The comparator
is NOT chance (0.5) — it is the best alternative policy: majority-branch routing,
existing diagnostic rules, strong batch retrieval, or ordinary evidence-adaptive
investigation. VLD must beat THOSE, not a coin flip.

ρ is a distribution, not a point. Mass below the comparator contributes negative
value unless the system can detect low-ρ cases at inference time and fall back to
single-pass (O-3). This makes O-3 part of the value model, not just an open issue.

**Gate 3 — Budget constrains investigation (budget < branches):**
If the budget covers all branches, breadth matches or beats VLD (Sim 2 confirms).
An affordable exhaustive search does NOT eliminate adaptive value entirely — fewer
reads can still save time or cost — but the advantage shrinks.

### 5.2 Formal value expression

    Value = htail × m_cond × E_ρ[g(ρ)] − read_cost

where:
- htail = fraction of decisions in the hard tail
- m_cond = fraction of hard-tail decisions with score-keyed conditional structure
- g(ρ) = the MEASURED calibration curve — utility gain from correct routing minus
  utility loss from incorrect routing, evaluated against the best budget-appropriate
  comparator
- read_cost = per-read cost × expected reads per investigation

g is measured, not assumed. Sim 1's curve (slope ~0.55 per unit of ρ − ½ above ½,
~0.35 below) is the shape, but the amplitude depends on the stakes (utility
difference between correct and incorrect investigation).

### 5.3 What the simulations establish (and don't)

**Sim 1 (ρ calibration) — PASS, but scoped:**

| ρ | VLD | Breadth | Random | Δ_VLD vs random |
|---|---|---|---|---|
| 0.30 | 0.586 | 0.688 | 0.680 | −0.094 |
| 0.50 | 0.684 | 0.698 | 0.685 | −0.001 |
| 0.70 | 0.825 | 0.667 | 0.674 | +0.151 |
| 0.90 | 0.955 | 0.695 | 0.686 | +0.269 |

Correlation(Δ, ρ−½): 0.986. The instrument behaves as constructed. This
**calibrates the instrument** — it does not confirm the value model on real data.
Controlled ρ demonstrates sensitivity; real scorer informativeness is O-1.

**Sim 2 (budget sweep at ρ=0.75) — INFORMATIVE:**

| Budget | VLD | Breadth | Δ |
|---|---|---|---|
| 0 | 0.629 | 0.629 | 0.000 |
| 1 | 0.873 | 0.688 | +0.185 |
| 2 | 0.842 | 0.889 | −0.047 |

Budget=1: VLD dominates (+18.5pp). Budget=2: breadth wins (−4.7pp). The budget=2
reversal is because damped averaging bakes wrong-branch evidence into v. This
supports auditing aggregation under identical evidence; it does not establish that
damping is generally wrong or that attention will close the gap. A one-line fix
(re-extract from full admitted set rather than damped average) should be tested
before motivating learned aggregation.

**What these establish:** The ρ-sensitivity instrument works. VLD dominates at
constrained budgets. The failure mode (ρ < 0.5) is real and measurable.

**What they do NOT establish:** Real scorer informativeness. Real conditional
density. Real analyst time savings. Real cost/benefit.

---

## 6. Future Directions: Learned Investigation

**Status: CONTINGENT. Gated on Phase 1 (R1-R4) producing positive results with
handcrafted Ψ.**

### 6.1 Inspectable learned routing (Phase 1 eligible)

An inspectable learned router — a shallow tree or logistic model over (v_t features,
evidence type) → branch, emitting a per-step reason from a bounded feature set —
is auditable and should be allowed in Phase 1 as a **shadow router** alongside the
handcrafted Ψ. This is also the instrument that estimates ρ at inference time (O-3).

### 6.2 Neural controllers (Phase 3, gated)

RNN/transformer controllers over investigation traces require:
- Backprop-through-trajectory training (off-policy correction needed)
- Attention over unnamed trace states (NOT interpretable by attention weights alone;
  Jain & Wallace 2019)
- Reconciliation with frozen-state/inspectability invariants

**Gate:** Do not build until Phase 1 shows ρ > comparator AND Δ_depth > 0 with
handcrafted + inspectable-learned Ψ, AND the specific limitation of those policies
is understood and documented.

---

## 7. Connections to Established Work

| Work | Relevance |
|---|---|
| **Adaptive submodularity** (Golovin & Krause 2011) | When adaptive beats non-adaptive |
| **Classification with costly features** (Janisch et al. 2019, 2024) | Closest precedent; SOC application |
| **Rational metareasoning** (Russell & Wefald 1991; Callaway 2018) | Bounded deliberation |
| **MINERVA** (Das et al. 2018) | Learned graph navigation |
| **ReaRev** (2022) | Feedback-guided graph reasoning |
| **Adaptive-RAG** (Jeong et al. 2024) | CI's semantic router |
| **SPRT** (Wald); **VoI** (Lindley; Howard) | Per-step halt; read value |
| **"What Happens When the Model Eats the Stack?"** (Patel, Shankar, Luo, Guestrin, Zaharia, Stoica — Berkeley/Stanford, 2609.03141, 2026) | **See §7.1 below** |

### 7.1 The Persistent Semantic Context Paper (Patel et al. 2026)

This paper from the DAWN lab (creators of Spark, MLflow, LOTUS) argues that
as LLMs improve, hand-engineered agent pipelines get subsumed by the model
(the bitter lesson). Their empirical evidence: GPT-5.6 Sol coding agents
already beat specialized data agents on TAG-Bench and DAB; efficiency improves
4× per model generation. But **60%+ of remaining failures are environmental
knowledge failures** — wrong data source, semantic misinterpretation, entity/join
mismatches.

Their thesis: the enduring requirement is **persistent semantic context** —
curated knowledge about the data environment, amortized across queries,
constructed offline. Simple agent-authored context adds +19pp accuracy on DAB.

**Three connections to CI:**

**CI IS persistent semantic context.** The paper's vision — curated environmental
knowledge, amortized across decisions, constructed offline and updated continuously
— is exactly what CI's judgment graph provides. But CI goes further: the context
is LEARNED from verified outcomes (not manually curated), UPDATED through governed
decision-loops (not statically authored), and BOUNDED by conservation (not
unconstrained). The paper describes what to build; CI has built it.

**VLD is the acquisition policy OVER persistent context.** The paper shows that
even static context helps (+19pp). VLD adds state-conditioned navigation — "which
part of the persistent context to read next depends on what the last read showed."
This is the paper's §3.2 "context construction and physical design" taken to its
logical conclusion: not just building the context, but navigating it adaptively
based on the current decision's investigation state.

**Conservation = semantic consistency.** The paper's §3.1 identifies "semantic
consistency" as a key challenge — ensuring persistent context stays correct as the
environment changes. CI's conservation law IS the semantic consistency mechanism:
when accuracy degrades (context is stale), conservation blocks updates until
reliability is restored. The paper calls for "consistency models analogous to
database consistency" — CI has one, derived from statistical reliability theory.

**Positioning implication:** Cite as: "Patel et al. (2026) establish that persistent
semantic context is the enduring requirement for data agents — the part that
survives the bitter lesson. CI's judgment graph is a learning, governed, conservation-
bounded implementation of that vision."

### 7.2 DataOps as the Paper's Primary Use Case

The paper studies "data agents" — systems working with data pipelines, schemas,
queries, transformations. **DataOps is this exact domain.** The paper's 60%+
environmental knowledge failures map directly to DataOps's hardest problems:

| Paper's failure mode | DataOps equivalent | CI mechanism |
|---|---|---|
| Wrong data source | Alert attributed to wrong upstream system | Investigation router: score-keyed routing to correct pipeline branch |
| Semantic misinterpretation | Same field name, different meaning across systems | Judgment graph: entity links preserve semantic context per system |
| Entity/join mismatches | Schema change breaks downstream joins (MATKL_V2) | SchemaImpactPanel: traces join fanout through lineage graph |
| Missing schema knowledge | New transformation, dependencies unknown | Process-Tech Fusion: SAP/Celonis evidence integrated into graph |
| Stale metadata | Pipeline topology changed, routing uses old graph | Conservation: blocks decisions when context staleness degrades accuracy |

**DataOps may be VLD's strongest use case**, stronger than SOC:

1. **The persistent context is richer.** DataOps has pipeline topology (9 systems),
   schema change history, transformation lineage, cross-system dependencies —
   more navigable structure than SOC's alert/campaign graph.

2. **The environmental knowledge failures are more frequent.** SOC alerts often
   have explicit category labels (content-keyed). Pipeline alerts are inherently
   ambiguous — the same metric (throughput drop) can indicate three different root
   causes. This is the score-keyed regime where VLD earns its value.

3. **The paper's evidence supports it.** +19pp from simple context on data tasks.
   CI's context is not simple — it's learned from verified outcomes. The expected
   improvement should be larger.

4. **Process-Tech Fusion IS context construction.** The paper's "persistent semantic
   context" constructed from data catalogs, schemas, and query logs is what
   Process-Tech Fusion does with SAP + Celonis. The D-CEL design (§8 of the session
   continuation doc) integrates these sources into the judgment graph.

**Implication for VLD execution plan:** Consider running Phase 1b measurement on
DataOps IN PARALLEL with SOC, not after. DataOps may show stronger results because:
- More navigable graph structure (pipeline topology > campaign chains)
- More ambiguous alerts (more score-keyed conditional cases)
- Closer match to the paper's validated domain

**Novelty status: OPEN.** "Components established; composition to test" is the
claim. The Patel et al. paper validates the persistent-context thesis but does
not build the adaptive acquisition policy (VLD) or the conservation gate. No
targeted literature search has been run for the full composition.

---

## 8. Making It Real — The Structured Path to Measured Results

This is the execution plan that converts hypotheses into numbers.

### R1 — Measure ρ on real SOC decisions (Astra audit, 2 days)

**What:** Take SOC's existing verified decisions. For each, replay the investigation:
what was the initial observation? After the first evidence read (SA pattern dispatch),
what did the scorer recommend? Did that recommendation match the verified outcome?

**Produces:** Empirical ρ distribution on real cases. Not planted, not controlled —
the actual informativeness of CI's real scorer on real decision data.

**Method:**
1. Query AGE for all verified decisions with campaign membership
2. For each: reconstruct s₀ (initial alert), compute v₀, compute a*(v₀)
3. Identify the first evidence read that SA would dispatch
4. Re-score with that evidence: v₁, a*(v₁)
5. Compare a*(v₁) routing indication against the verified outcome
6. ρ = fraction where a*(v₁) routing was correct

**Gate:** If ρ < comparator across the SOC decision history → VLD doesn't help SOC
→ re-evaluate entire program. If ρ > comparator → proceed to R3.

**The μ skew (§2.5) is directly measurable here:** compute ρ using v_L centroids
vs v_0-only centroids and compare.

### R2 — Audit conditional structure in SOC campaigns (Astra audit, 1 day)

**What:** Count the fraction of hard-tail SOC decisions that have score-keyed
conditional investigation structure (not content-keyed).

**Produces:** m_conditional on real data. The content-keyed vs score-keyed split.

**Method:**
1. Identify all decisions near Voronoi boundaries (margin < P25)
2. For each: does the alert have campaign membership? Entity links?
3. For those with links: is the branching direction readable from the evidence
   (content-keyed: alert.type = "credential") or only from the scorer's state
   (score-keyed: mixed indicators, factor weights determine direction)?
4. m_conditional = score-keyed fraction of the hard tail

**Gate:** If m_conditional ≈ 0 (all conditional cases are content-keyed) → VLD's
distinctive value is zero → invest in rule-based routing instead.

### R3 — Build SOC Ψ prototype (Codex build, 1 week)

**What:** Handcrafted Ψ for SOC campaign investigation. Uses existing SA patterns,
adds score-conditioned pattern selection.

**Build:**
1. Ψ dispatches SA's campaign-traversal pattern after the first read
2. After scoring v₁: if a*(v₁) indicates credential-based → dispatch auth-trail pattern
3. If a*(v₁) indicates process-based → dispatch process-tree pattern
4. Use C4 per-step halt (residual + budget + flip-count)
5. Conservation gate at emit

**Produces:** Working VLD loop for SOC that can be shadow-run.

**Inspectability:** Each step logs which SA pattern was dispatched, what v_t was,
why that pattern was chosen (which centroid was nearest, what the margin was).

### R4 — Shadow-run VLD vs single-pass on SOC (1 week)

**What:** For each incoming SOC decision, run BOTH single-pass and VLD investigation
in parallel. Don't act on VLD results — just record them.

**Produces:**
- Δ_depth on real cases (VLD accuracy vs single-pass accuracy, against verified outcomes)
- Re-investigation rate: how often does VLD's focused investigation match what the
  analyst actually checked?
- ρ in the wild: measured routing accuracy during live operation
- Content-keyed vs score-keyed split in live traffic (validates R2)

**Comparison arms:**
- Single-pass (current production)
- VLD with handcrafted Ψ
- Rule-based routing (content-keyed branching only — the honest comparator)
- Inspectable learned router (shallow tree, shadow-mode)

**Gate:** If VLD ≤ rule-based routing on all metrics → the scorer's routing signal
isn't needed → invest in rules, not VLD.

### R5 — Analyst time measurement (ongoing, with customer)

**What:** Measure actual analyst workflow impact. Not assumed — measured.

**Method:**
1. Time-and-motion baseline: how long does triage take today, broken into
   investigation, validation, escalation, documentation
2. Shadow VLD results shown alongside current workflow
3. Measure: does the analyst's investigation path match VLD's? How often?
4. Measure: time-to-action on cases where VLD was correct vs incorrect
5. Measure: re-investigation rate (analyst checked something VLD didn't surface)

**Produces:**
- Real time savings (not "4-10×" narrative — actual measured median and tail)
- Investigation match rate (how often VLD's trace matches the analyst's path)
- False confidence cost (how much extra time when VLD routes wrong)

**Customer deliverable:** "Investigation profile" — discovery artifact showing
m_conditional, ρ, and projected time savings with uncertainty bounds.

### R6 — Go/no-go for multi-copilot (after R4-R5)

**If R4 shows Δ_depth > 0 and R5 shows real time savings:**
→ Extend to S2P (invoice investigation) and DataOps (root cause triage)
→ Build the investigation profile as a pre-sale discovery tool

**If R4 shows Δ_depth ≤ 0:**
→ Publishable negative result: "score-conditioned routing doesn't beat rules for
SOC investigation" — still valuable (saves the market from building it)
→ Evaluate whether the μ skew (§2.5) explains the null before stopping

**If R5 shows no time savings even when R4 is positive:**
→ Investigation routing works but doesn't translate to analyst workflow →
the bottleneck is elsewhere (validation, documentation, escalation)

---

## 9. Open Issues

### 9.1 Theoretical

| # | Issue | Path | Addressed by |
|---|---|---|---|
| O-1 | Is ρ > comparator for CI's real scorer? | Measure | R1 |
| O-2 | Does the adaptivity gap exceed cost? | Measure | R4 + R5 |
| O-3 | Can ρ < 0.5 be detected at inference time? | Build ρ estimator | R4 (shadow learned router) |
| O-4 | Abstain policy | Define per domain | Not yet addressed |
| O-5 | Precedent search | Literature review | OPEN (no search run) |
| O-6 | Refuting/noisy evidence + damping | Theory + sim | Not yet addressed |
| O-7 | μ train/serve skew magnitude | Measure | R1 (compare v_L vs v_0 centroids) |
| O-8 | Content-keyed fraction of conditional cases | Measure | R2 |

### 9.2 Engineering

| # | Issue | Path | Addressed by |
|---|---|---|---|
| E-1 | Trajectory storage schema | Design | R3 (prototype logging) |
| E-2 | Entity wiring (Trading/Purchasing) | Build | After R6 go decision |
| E-3 | Temporal fidelity in replay | Build | R1 prerequisite |
| E-4 | Per-step halt (C4) | Implement | R3 |
| E-5 | ρ estimator | Build | R4 (shadow learned router) |
| E-6 | Evidence read cost model | Define | R4 (measure actual latency) |
| E-7 | Latency budget | Measure | R4 (S2P score path already multi-second) |
| E-8 | Trace logging: propensities, costs, policy version | Design | R3 |

### 9.3 Must-fix before R3

1. Conservation = emit gate, constant within episode (not per-step halt)
2. Per-step halt = C4 (residual with floor + budget + flip-count)
3. Ψ operates over SA patterns (controller, not peer)
4. Log propensities, costs, timestamps, policy version per step
5. Customer claims labeled "pilot targets, unvalidated" until R5

---

## 10. Implementation Roadmap

### Phase 0: Measurement (2-3 days, Astra prompts)
- R1: measure ρ on real SOC decisions
- R2: audit conditional structure, content-keyed vs score-keyed
- **Gate: ρ > comparator AND score-keyed m > 0 → proceed**

### Phase 1: SOC prototype (2 weeks, Codex build)
- R3: handcrafted Ψ + inspectable learned router (shadow)
- R4: shadow-run on live SOC traffic
- **Gate: Δ_depth > 0 against rule-based routing → proceed**

### Phase 2: Validation (ongoing, with customer)
- R5: analyst time measurement
- R6: go/no-go for multi-copilot
- **Gate: real time savings → extend to S2P/DataOps**

### Phase 3: Learned investigation (contingent, 4-6 weeks)
- Only after Phase 1 positive results
- Start with inspectable (tree/logistic), not neural
- Neural controllers gated on Phase 2 completion

---

## 11. Relationship to Existing CI Documents

| Document | Relationship |
|---|---|
| innovation_note_v30.md | CI's governed decision-loops. VLD is a new loop. |
| ci_vld_depth_memo_v13.md | Parent VLD memo. This doc replaces §3E. |
| separation document | CI as graph-based reasoning. VLD extends the investigation path. |
| rl_sdk_design_v1.md | RL credit assignment evaluates VLD outcomes. |
| ae_sdk_design_v1.md | AE evolves Ψ parameter variants (not structure). |
| math_synopsis_v18.md | Conservation = eligibility gate. |
| vld_depth_p1_decision_graph_topology_report.md | P1: graph traversability per copilot. |
| vld_validation_sims.py | ρ calibration + budget sweep simulations. |
