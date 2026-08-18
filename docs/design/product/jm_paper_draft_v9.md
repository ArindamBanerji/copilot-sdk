# Judgment Memory: A Conservation-Bounded Fourth Cognitive Type for Multi-Domain AI Decision Systems

**Authors:** Arindam Banerjee
**Affiliation:** Dakshineshwari LLC
**Date:** May 2026
**Alt title:** Conservation-Bounded Factor Reliability Learning for AI Decision Systems
**Draft:** v9.0

---

## Abstract

Deployed AI decision systems process their ten-thousandth recommendation
with identical logic to their first. They log events (episodic memory),
query knowledge graphs (semantic memory), and execute learned rules
(procedural memory), but, to our knowledge, none maintains a persistent structured
representation of which of their own factors reliably predict which
outcomes — the quality structure of domain expertise. We
propose **judgment memory** as a computationally distinct fourth cognitive
type that stores this structure as centroid geometry over verified human
decisions. We show that judgment memory, when bounded by a conservation
law α·q·V ≥ θ_min, enables capabilities not present in surveyed
stateless AI advisory systems: detection of signal-confidence inversions ("trust
traps"), cross-domain transfer of learned expertise, and personnel-change
detection. Across nine synthetic simulation experiments on 500+ domains with known ground truth,
we find that (1) trust traps affect 93.6% of domains under a noise-attracted
attention model (6.4% under familiarity-biased), (2) the system surfaces 63% of these inversions
with zero false positives, (3) quality improvement and conservation-gated scope expansion interact
to create increasing returns — accuracy alone is sub-linear, but scope
expansion gated by conservation produces a feedback loop, (4)
cross-domain transfer provides 1.5–2× convergence speedup, and (5)
conservation detects quality degradation with 97–100% reliability while
creating an explicit safety-adaptability tradeoff that supervisor-
approved recalibration closes (87% recovery in E-JM-4b), (6) entity-
contextualized factor weighting detects 2.7× more trust traps than
global analysis, providing initial evidence for the shared-graph
hypothesis (E-JM-7), and (7) DiagonalKernel outperforms Bayesian
online regression by +1.21pp on the same verified decisions (E-JM-6b). We argue that a single governed graph substrate for all four memory
types facilitates cross-type interactions (e.g., entity-contextualized
trust trap detection, conservation-gated transfer) that are substantially
harder to implement and maintain via stitched architectures; direct
empirical comparison of shared vs. stitched approaches is future work.

---

## §1 — Introduction

Many commercial AI advisory systems share a common structural
limitation: they do not learn from its own verified outcomes.
Security information and event management (SIEM) platforms process
millions of alerts, but the analyst who reviews alert number fifty
thousand receives the same scoring logic as the analyst who reviewed
alert number one. Source-to-pay platforms evaluate supplier invoices
against static rules regardless of how many thousands of invoices
analysts have already approved or flagged. Trading signal engines score
opportunities with fixed models irrespective of which signals
historically predicted which outcomes for a given portfolio.

The institutional knowledge accumulated across those thousands of
verified decisions — which factors predict which outcomes, which signals
to trust, which to ignore — exists only in the heads of the analysts who
made them. When an analyst leaves, that knowledge leaves too. In a
50,000-alert SOC where an experienced analyst has calibrated their
attention to the 2-3 factors that actually predict threats, replacing
that analyst means restarting from zero. The cost is not just recruiting;
it is the silent degradation of decision quality while the system
continues operating with the same confidence but without the domain
expertise that justified it.

This is not a training-data problem. These systems are trained on
historical data, fine-tuned on domain corpora, and occasionally
retrained on accumulated logs. The problem is architectural: no deployed
system maintains a persistent, structured representation of *which of
its own scoring factors reliably predict which outcomes*, updated
continuously from verified human decisions, bounded by a mathematical
guarantee of human oversight quality.

### What this looks like in practice

Consider a security analyst reviewing an alert about suspicious login
activity. The system scores the alert using seven factors: geo-anomaly,
time-of-day, failed-login-count, device-fingerprint, VPN-flag,
privilege-level, and prior-alert-history. The analyst confirms the
escalation. In a conventional system, this confirmation is logged as an
event and nothing else changes. In a system with judgment memory, this
confirmation updates the centroid for "account-takeover / escalate"
along all seven factor axes, with a learning rate of η=0.05 (the system
was right — reinforce this pattern). After 500 such verified decisions,
the system has learned that geo-anomaly and prior-alert-history are the
strongest predictors of confirmed escalations, while time-of-day and
VPN-flag are noise. The next alert arrives pre-scored with confidence
calibrated to these learned weights — not because someone retrained a
model, but because the judgment geometry has been refined by every
verified decision in between.

This is judgment memory: the persistent, structured encoding of which
factors predict which outcomes, learned continuously from verified human
decisions.

### Three eras of AI decision systems

This work proposes that AI decision systems are entering a third era:

- **Detection era (current):** Systems detect events and present them
  to humans. SIEM tools, procurement scanners, data quality monitors.
  The system processes; the human decides. Decision quality depends
  entirely on the human's expertise, which is neither captured nor
  accumulated.

- **Learning era (emerging):** Systems learn from outcomes and adapt
  scoring. Reinforcement learning from feedback, automated retraining.
  Decision quality improves but without mathematical guarantees of
  oversight quality, and without structured factor-level learning.

- **Compounding era (this work):** Systems accumulate judgment memory
  bounded by conservation law. Each verified decision refines the quality
  structure, which improves subsequent scoring, which produces more
  correct decisions — a positive feedback loop with provable safety
  bounds. The system does not just learn; it compounds.

Cognitive science identifies three established types of human memory that
AI systems have partially adopted: **episodic memory** (specific past
events — implemented as decision logs and experience replay buffers),
**semantic memory** (structured knowledge — implemented as knowledge
graphs and retrieval-augmented generation), and **procedural memory**
(learned skills and rules — implemented as reinforcement learning
policies and automation playbooks). Each has a mature literature and
production implementations.

We propose a fourth type: **judgment memory** — the learned quality
structure that encodes which factors predict which outcomes, conditioned
on verified human decisions, bounded by a conservation law that
guarantees minimum human oversight quality. Judgment memory is not
reducible to the other three types. Episodic memory records *what*
happened; judgment memory encodes *which factors predicted it*. Semantic
memory represents *entities and their relationships*; judgment memory
represents *quality relationships between factors and outcomes*.
Procedural memory stores *rules for action*; judgment memory stores the
*reliability structure from which rules should be derived*.

[FIGURE-1: Four memory types taxonomy. 2×2 grid showing
Episodic (what happened), Semantic (what is known),
Procedural (what to do), Judgment (what to trust).
Each cell: definition, AI implementation, compounds via.
Below: timeline arrow showing Detection → Learning → Compounding eras.]

This paper makes four contributions:

1. **Taxonomy.** We formally define judgment memory as a fourth cognitive
   type with distinct computational properties: centroid geometry
   representation, asymmetric learning rates, and conservation-law
   bounding (§3).

2. **Trust trap prevalence.** We demonstrate that signal-confidence
   inversion — where human decision-makers systematically prioritize
   the factors least predictive of outcomes — affects 93.6% of
   synthetic domains under realistic human attention models (§5.1).

3. **Quality-scope interaction.** We show that accuracy improvement
   alone is sub-linear, but its interaction with conservation-gated
   scope expansion creates a feedback loop that produces increasing
   returns. Conservation is not merely a safety constraint; it gates
   the scope expansion that makes the system more valuable over time
   (§5.3).

4. **Architecture.** We argue that the capabilities enabled by judgment
   memory are facilitated by a single governed graph substrate where
   cross-type interactions (episodic × judgment, semantic × judgment)
   are native traversals rather than orchestrated joins. Direct
   empirical comparison of shared vs. stitched architectures is
   identified as future work (§6.4).

---

## §2 — Background and Related Work

### 2.1 Memory in AI Systems

**Episodic memory** in AI originates with experience replay in deep
reinforcement learning. Mnih et al. (2015) showed that storing and
replaying past transitions stabilized training in deep Q-networks.
Subsequent work introduced prioritized experience replay (Schaul et al.,
2016) and episodic memory modules for few-shot learning (Vinyals et al.,
2016). In production systems, episodic memory takes the form of decision
logs, alert histories, and transaction records — flat tables that record
what happened but encode no quality structure.

**Semantic memory** in AI corresponds to knowledge representation:
knowledge graphs (Bollacker et al., 2008), ontologies, and more recently
retrieval-augmented generation (Lewis et al., 2020). GraphRAG (Edge et
al., 2024) extends retrieval with graph-structured knowledge. Production
implementations include threat intelligence graphs in cybersecurity,
supplier relationship databases in procurement, and entity-relationship
models in data management. These systems encode *what is known* about
entities and their relationships but not *which knowledge predicts which
outcomes*.

**Procedural memory** in AI maps to learned policies and automation
rules. Reinforcement learning produces policies that encode how to act
(Sutton & Barto, 2018). In production, procedural memory appears as
playbooks, automation workflows, and escalation rules. Meta-learning
approaches (Finn et al., 2017; Nichol et al., 2018) optimize the
*initialization* of procedural policies for fast adaptation — the
closest existing work to cross-domain transfer of learned patterns.

**The gap.** Three decades of research across episodic, semantic, and
procedural memory have produced mature AI implementations for each type
in isolation. Yet to our knowledge, no production system or published
architecture
combines all three with a fourth type that encodes the quality structure
of domain expertise — the knowledge of *which factors to trust*,
conditioned on verified human decisions, bounded by a mathematical
guarantee of oversight quality. This is the gap we fill.

### 2.2 Human Oversight and AI Safety

Reinforcement learning from human feedback (RLHF) (Christiano et al.,
2017; Ouyang et al., 2022) uses human preferences to align language
model outputs during training. Constitutional AI (Bai et al., 2022)
embeds principles during training that guide model behavior at inference.
Both operate on the *training* phase: they shape model weights before
deployment.

The conservation law we propose operates on the *deployment* phase: it
is a mathematical invariant that bounds system behavior during live
operation, not during training. The distinction is fundamental. A system
trained with RLHF can still degrade at deployment if the distribution
shifts. A system bounded by conservation law α·q·V ≥ θ_min detects
such shifts at deployment time and responds by pausing autonomous
operation — a capability that training-time alignment cannot provide.

### 2.3 Meta-Learning and Transfer

Model-agnostic meta-learning (MAML) (Finn et al., 2017) learns an
initialization from which a model can quickly adapt to new tasks. This
is optimization of *hyperparameters* for fast adaptation. Judgment memory
transfer is different: it transfers the *quality structure of domain
expertise* — which factors matter, which are noisy, which separate good
outcomes from bad. A MAML-initialized model knows how to learn quickly;
a judgment-memory-initialized model knows *what to pay attention to* in
a related domain.

### 2.4 Why Not Just Retrain?

The most common objection from practitioners is: "Why not periodically
retrain on accumulated data?" Periodic retraining is not equivalent to
judgment memory for three reasons:

First, retraining produces a new model; judgment memory produces a
persistent, interpretable quality structure that humans can inspect,
challenge, and transfer. An analyst can look at the radar chart and say
"the system thinks geo-anomaly matters more than time-of-day — I agree
with that" or "I disagree — let me investigate." A retrained model
offers no such transparency into factor-level quality.

Second, the conservation law bounds deployment quality continuously;
retraining bounds training quality at training time. Between retraining
cycles — which may be weeks or months apart — the system operates
unbounded. This is precisely the window where silent degradation occurs:
personnel changes, data corruption, or domain drift accumulate without
detection until the next retraining cycle reveals the damage
retrospectively.

Third, judgment memory is additive and transferable. Centroid geometry
and precision weights from one domain can warm-start a related domain.
Retraining from scratch in each domain discards the cross-domain
structure that judgment memory preserves.

### 2.5 Positioning: Why Not Prototype Learning, Bandits, or CoALA?

Several established techniques share surface-level similarities with
judgment memory. We address the three most likely objections.

**"This is just prototype/centroid learning."** Centroid-based
representations (e.g., Nearest Class Mean, ProtoPNet) learn class
prototypes from labeled data. Judgment memory centroids differ in three
respects: (1) they are updated *asymmetrically* from verified human
decisions with η_confirm ≠ η_override, encoding a quality asymmetry
absent from standard prototype learning; (2) they are *domain-partitioned*
(C×A×d tensor, not a flat set of prototypes), encoding category-action
structure; (3) they are *conservation-bounded* — the system's autonomous
scope is mathematically gated by oversight quality, not just accuracy.
Prototype learning optimizes classification; judgment memory accumulates
the quality structure of human expertise under a deployment-time safety
invariant.

**"This is online learning with a quality gate."** This is the closest
analogy, and the conservation law is the irreducible differentiator.
Standard online learning bounds (PAC, regret bounds) guarantee
convergence given sufficient i.i.d. data at training time. Conservation
law α·q·V ≥ θ_min guarantees *minimum human oversight quality at
deployment time* under potentially non-stationary, adversarial, or
personnel-dependent input. The invariant bounds *breadth × verified-accuracy × volume* at
deployment time — a deployment-phase guarantee that no training-time
bound provides. Without the
conservation law, the centroid + precision mechanism is indeed a
variant of online LVQ with factor weighting. WITH the conservation law,
the system's autonomous scope is mathematically gated by verified human
oversight quality — a property no standard online learner provides.

**"CoALA already formalizes agent memory."** Sumers et al. (2023)
propose Cognitive Architectures for Language Agents (CoALA), formalizing
working memory + episodic + semantic + procedural for LLM-based agents.
Our taxonomy adds judgment memory as a distinct type that CoALA does not
address: CoALA's procedural memory stores action policies; judgment
memory stores the *factor-quality structure* from which policies should
be derived. CoALA does not include a conservation invariant, a
centroid-geometry representation, or DiagonalKernel precision weighting.
The contribution is orthogonal: CoALA organizes agent cognition; judgment
memory adds a quality-accumulation mechanism with safety bounds.

---

## §3 — Judgment Memory: Definition and Properties

### 3.1 Formal Definition

Let a decision domain D be characterized by C categories, A possible
actions per category, and d scoring factors. A **decision** is a tuple
(c, a, f, o) where c ∈ {1,...,C} is the category, a ∈ {1,...,A} is the
recommended action, f ∈ ℝ^d is the factor vector, and o ∈ {confirmed,
overridden} is the verified outcome provided by a human decision-maker.

**Definition 1 (Judgment Memory).** The judgment memory of a domain D
after V verified decisions is the tuple J = (M, W, S) where:

- **M** ∈ ℝ^{C×A×d} is the centroid tensor: M_{c,a} is the running centroid
  for category c, action a — an exponentially-weighted average updated
  asymmetrically from verified decisions.

- **W** ∈ ℝ^d is the DiagonalKernel precision vector: W_k encodes the
  reliability of factor k as measured by its inverse variance and
  discriminability between confirmed and overridden outcomes.

- **S** = (V, q, α, status) is the conservation state: verified decision
  count V, rolling accuracy q, category coverage α, and conservation
  status ∈ {GREEN, AMBER, RED}.

[EQUATION-1: J = (M, W, S) with component definitions]

**Definition 2 (Centroid Update).** Given a verified decision (c, a, f, o),
the centroid update uses asymmetric learning rates:

[EQUATION-2:
M_{c,a} ← M_{c,a} + η · (f - M_{c,a})
where η = η_confirm = 0.05 if o = confirmed
      η = η_override = 0.01 if o = overridden]

The 5:1 asymmetry encodes a fundamental insight: confirmed decisions
reinforce the centroid (the system was right — move toward this pattern),
while overridden decisions provide weaker correction (the system was
wrong, but the human's action may not be the optimal centroid target
either).

**Definition 3 (DiagonalKernel Precision).** The precision weight for
factor k is computed from the inverse variance and outcome
discriminability:

[EQUATION-3:
W_k = (d_k · σ_k^{-1}) / Σ_j (d_j · σ_j^{-1})
where σ_k = std of factor k across all verified decisions
      d_k = |μ_k^{confirmed} - μ_k^{overridden}| / pooled_std_k]

Factors with low noise (low σ_k) and high discriminability (large d_k)
receive the highest weight. This mechanism naturally discovers which
factors are reliable predictors of outcomes — and, crucially, which
factors human decision-makers *should* be paying attention to but may
not be.

**Computational complexity.** Each centroid update (Definition 2) is
O(d) per verified decision. DiagonalKernel weight computation
(Definition 3) requires maintaining running means and variances via
Welford's algorithm, also O(d) per update. The centroid tensor M
occupies O(C·A·d) space. For typical production parameters (C=6, A=4,
d=7), M has 168 values and W has 7 values — negligible storage. The
conservation check (Definition 4, §4) is O(1) given precomputed V, q, α.
Total per-decision cost is O(d), independent of V — the system does not
slow down as it accumulates decisions.

### 3.2 Why Judgment Memory Is Distinct

The four memory types differ along three axes: what they store, how they
are created, and how they compound.

| Type | Stores | Created by | Compounds via |
|---|---|---|---|
| Episodic | Specific events (c, a, f, o) | Every score + outcome | Volume accumulation |
| Semantic | Entity relationships | System integration + linking | Connection density |
| Procedural | Learned rules and policies | AgentEvolver promotion | Rule refinement |
| **Judgment** | **Factor quality structure (M, W)** | **Verified decisions only** | **Geometric refinement + scope expansion** |

The critical distinction is in the *compounds via* column. Episodic
memory grows linearly with decisions — decision #1000 adds one more
record, same as decision #1. Semantic memory grows with entity
connections. Procedural memory grows with rule promotions. Judgment
memory compounds through two interacting mechanisms: each verified
decision refines the centroid tensor M and precision vector W (geometric
refinement, which is individually sub-linear), AND as quality improves,
more categories pass conservation gates and become eligible for
autonomous processing (scope expansion). As we demonstrate in §5.3,
neither mechanism alone produces compounding; their multiplicative
interaction does.

| Analysis approach | Operates on | Answers | Source |
|---|---|---|---|
| SHAP / permutation importance | Model features | "Which features did the model use?" | Model internals |
| **DiagonalKernel precision** | **Verified human decisions** | **"Which factors should the human trust?"** | **Outcome data** |

This distinction is fundamental when the human is the decision-maker and
the AI system is advisory. SHAP explains the model; DK explains the
domain.

**Why this is not merely online learning.** Judgment memory is related
to online learning but differs in its unit of persistence and use.
Standard online learning updates a predictor to improve future outputs.
Judgment memory persists an inspectable factor-quality state derived
only from verified human decisions, separates this state from the
scoring procedure, exposes it for human review and challenge, transfers
it across related domains, and gates autonomous scope through a
deployment-time conservation invariant. The contribution is not the
centroid update alone — that is standard — but the specific combination
of verified-outcome factor geometry, precision weighting, conservation
state, and operational use as governed, inspectable, transferable
memory.

### 3.3 The Centroid Geometry Representation

For a domain with C=6 categories, A=4 actions, and d=7 factors, the
judgment memory contains:

- **168 centroid values** (6 × 4 × 7): per-category, per-action mean
  factor vectors encoding "what does a confirmed decision in this
  category with this action typically look like?"

- **7 precision weights**: per-factor reliability scores encoding
  "which factors actually differentiate good decisions from bad?"

- **1 IKS value** (Institutional Knowledge Score): aggregate alignment
  between centroids and true domain structure, ranging from 0 (no
  knowledge) to 100 (perfect domain model).

[FIGURE-2: Centroid geometry visualization.
Three panels showing progression:
Day 1: sparse, overlapping centroids, DK weights uniform.
Month 6: tighter clusters, DK weights separating, 3/6 categories GREEN.
Month 12: well-separated geometry, trust traps surfaced (radar chart),
5/6 categories GREEN, IKS=72.
Caption: "The system accumulates judgment. Each verified decision
refines the geometry. The radar chart reveals which factors the analyst
should trust — and which they have been over-trusting."]

The centroid geometry is *not* a classifier. It does not make decisions.
It is a *quality reference* that the scoring engine consults to evaluate
how similar a new observation is to the established pattern for its
category and action. The human remains the decision-maker; the centroid
geometry tells the system how much confidence to place in its
recommendation.

### 3.4 Why All Four Types Must Share One Graph

The cross-type interactions between memory types are the capability
source. With separate stores for each type, each interaction requires
an API call, a join, and a reconciliation — and most interactions
simply never happen because no one builds the glue code. With one
graph, each interaction is a single traversal:

- **Episodic × Judgment:** "This specific decision moved the centroid
  for account-takeover/escalate by +0.12 along the geo-anomaly axis"
  — connects individual events to quality structure changes.

- **Semantic × Judgment:** "Alerts about entities in the *finance*
  department have a different centroid from *engineering*" — entity
  context refines quality assessment.

- **Procedural × Judgment:** "The auto-escalation rule was promoted
  because the centroid gap between escalate and ignore exceeded 0.25
  across 200 verified decisions" — judgment geometry drives rule
  evolution.

- **Judgment × Judgment (cross-domain):** "The SOC's factor weighting
  pattern transferred to the S2P copilot, providing 1.8× convergence
  speedup" — quality structure transfers between domains.

We argue that the shared graph substantially reduces the complexity of
cross-type interactions compared to stitched architectures. Separate
stores require orchestration layers (API joins, materialized views,
event buses) to achieve interactions that a shared graph provides as
native traversals. While modern tooling (GraphQL federation, Kafka,
Airflow) can bridge separate stores, each bridge adds latency,
maintenance burden, and failure modes — and in practice, most cross-type
interactions simply never get built because the integration cost
exceeds the perceived benefit. The shared graph lowers the marginal cost
of each interaction to a single query. Direct empirical comparison of
shared vs. stitched latency and maintenance cost is future work.

---

## §4 — Conservation Law as Safety Bound

### 4.1 The Conservation Formula

The conservation law bounds the system's autonomous operating authority
based on the quality of its verified human oversight:

[EQUATION-4: α · q · V ≥ θ_min]

where:

- **α** = category coverage among verified decisions. The fraction of
  categories with at least one verified decision: α = c_d / C where c_d
  is the count of unique categories with verified data.

- **q** = rolling verified accuracy. Computed over a sliding window of
  the most recent q_window = 400 verified decisions. q = (number
  confirmed) / (number verified) within the window.

- **V** = verified decision count. Only decisions with status ∈
  {confirmed, overridden} count. Pending decisions, observations
  (preview/read scoring), and archived decisions are excluded.

- **θ_min** = adaptive quality threshold. Defined as θ_min =
  23.53 / (α × V), which tightens as the system accumulates more
  verified decisions and broader category coverage.

[EQUATION-5: θ_min = 23.53 / (α × V)]

**Per-category gate form.** The scope expansion in §5.3 is evaluated per
candidate category, not on global coverage. A category k becomes eligible
for autonomous approval when its own verified count V_k and rolling
per-category accuracy q_k satisfy q_k · V_k ≥ θ_cat, with θ_cat
calibrated from the same N_half basis as θ_min. Global α (coverage) is
an *outcome* of categories passing this gate, not the gating variable —
avoiding the circularity of coverage gating coverage.

[EQUATION-6: Per-category gate: q_k · V_k ≥ θ_cat for each candidate k]

The conservation formula has been proven through four independent paths:
analytic derivation, coded verification, oracle-separation simulation,
and centroid-distance analysis. Full proofs are provided in the companion
paper on Compounding Generalized Agents (Banerjee, 2026). Here we use
the conservation law as an engineering constraint and demonstrate its
empirical properties.

### 4.2 Decision Lifecycle

A decision progresses through a strict lifecycle:

[FIGURE-3: Conservation state machine.
Top: Decision lifecycle: pending → confirmed (is_correct=True)
                                → overridden (is_correct=False)
Bottom: System conservation: GREEN (learning active, scope expanding)
  → AMBER (q drops, learning paused, alert surfaced)
  → RED (q critical, autonomous scope frozen)
  → GREEN (q recovers after recalibration)]

- **Pending:** Created at score time. Not counted toward V. Not used
  for centroid updates.

- **Confirmed:** Human agreed with recommendation (is_correct = True).
  Counted toward V. Updates centroid with η_confirm = 0.05.

- **Overridden:** Human disagreed with recommendation (is_correct =
  False). Counted toward V. Updates centroid with η_override = 0.01.

- **Observation:** Created by preview/read endpoints. Never becomes a
  Decision. Excluded from V. Excluded from AgentEvolver. Used only
  for audit and analytics.

The distinction between Decisions and Observations is a hard
architectural boundary: GET endpoints that preview scores must not
create nodes that count toward conservation V. Violating this boundary
inflates V with unverified observations, undermining the conservation
guarantee.

### 4.3 The Safety-Adaptability Tradeoff

The conservation law creates an explicit, managed tradeoff between
safety and adaptability. When quality degrades — due to personnel
change, data corruption, adversarial input, or domain drift — the
conservation law detects the degradation and pauses autonomous
learning. This prevents the system from learning bad patterns from
degraded input.

However, pausing learning also prevents the system from *adapting*
to legitimately changed conditions. A new analyst with a different
(but valid) decision style will trigger conservation AMBER because
their quality profile differs from the established baseline. The
system correctly identifies that "something changed" but cannot
distinguish "degradation" from "different but valid."

Conservation is a **circuit breaker**, not a controller. Like an
electrical circuit breaker, it reduces immediate throughput; its value
is preventing silent unsafe operation. The system surfaces the change
to human supervisors, who decide whether to:

- **Recalibrate:** Reset learning rates for fresh centroid
  accumulation while preserving the geometric prior.
- **Supervised period:** Reduce autonomous scope until the new
  baseline stabilizes.
- **Investigate:** Examine whether the quality change indicates a
  real problem requiring intervention.

The conservation law does not automate the response to quality change.
It automates the *detection* of quality change and provides the
mathematical framework for reasoning about whether the change requires
action.

**Asymmetric risk routing.** In many decision domains, the cost of
errors is sharply asymmetric. In SOC triage, a false negative
(missed threat) may be 20× more damaging than a false positive
(unnecessary escalation). Conservation status should route uncertain
or degraded decisions to a graduated human-review tier — e.g., AMBER
status routes high-confidence decisions to auto-processing but sends
low-confidence decisions to analyst review, rather than globally
freezing all autonomous processing. This graduated response is not
implemented in our experiments but is a natural extension of the
conservation state machine that production deployment requires.

---

## §5 — Experiments

We conducted nine simulation experiments to test the empirical properties
of judgment memory. All experiments use synthetic domains with known
ground truth, enabling precise measurement of convergence, detection,
and transfer properties. The simulation code, data, and analysis scripts
are provided as supplementary material.

**Design principles (anti-confirmation-bias):**
- All experiments include negative cases where judgment memory may not
  help or may perform worse than baselines.
- Person/domain parameters are drawn from distributions, not hand-tuned.
- Results report full distributions with confidence intervals, not
  cherry-picked exemplars.
- Control conditions (no memory, perfect calibration) are included in
  every experiment.

Experiments are ordered from strongest to most nuanced findings.

**Baseline reference.** All experiments with A=4 actions have a chance
floor of 25% (1/A). Accuracy values should be interpreted relative to
this floor. The Bayes-optimal ceiling depends on noise level and varies
by experiment; where relevant, we note it in the results.

### 5.1 Trust Trap Prevalence (E-JM-2) — Problem Quantification

**Question:** How common is signal-confidence inversion — the situation
where human decision-makers prioritize the factors that are *least*
predictive of outcomes?

**Motivation:** If trust traps are rare (affecting <5% of domains), then
judgment memory is a niche optimization. If they are common (>50%),
then every AI decision system that does not detect them is operating
with systematically wrong factor priorities — and the cost is real. In
a 50,000-alert SOC where analysts spend 30 minutes per escalation,
systematic attention to the wrong factors means thousands of hours
per year spent investigating signals that do not predict threats.

**Design:** We generated 500 synthetic domains, each with 7 scoring
factors. For each domain, we assigned ground-truth factor weights
(representing actual predictive importance) drawn from an exponential
distribution, producing realistic skew where a few factors dominate. We
then simulated five human attention models representing different
mechanisms by which decision-makers allocate attention to factors:

1. **Random:** Attention weights drawn from a Dirichlet distribution
   independent of true weights. Represents unsystematic attention.

2. **Noise-attracted:** Attention proportional to factor noise level.
   Represents the well-documented salience bias: humans attend to
   signals that vary more, mistaking variability for importance.

3. **Recency-biased:** Attention proportional to an exponential random
   variable uncorrelated with true weights. Represents attention driven
   by whatever changed recently.

4. **Familiarity-biased:** Attention partially correlated with true
   weights but with strong bias toward the first 2–3 factors. Represents
   attention driven by factor familiarity and accessibility.

5. **Perfect (control):** Attention equal to true weights. Represents
   perfectly calibrated human judgment with zero inversion.

For each domain and attention model, we measured three inversion metrics:
*top-1 mismatch* (the factor receiving the most attention is not the
most predictive), *top in bottom half* (the most-attended factor is in
the bottom half of true predictive ranking — the full "trust trap"),
and *full inversion* (the most-attended factor is the *least* predictive).

[FIGURE-4: e_jm_2_inversion_rates.png
Bar chart showing inversion rates by attention model.
Three bars per model: top-1 mismatch, trust trap, full inversion.]

**Results:**

| Attention model | Top-1 mismatch | Trust trap | Full inversion | Spearman r |
|---|---|---|---|---|
| Random | 85.2% | 56.4% | 16.2% | ≈ 0 |
| **Noise-attracted** | **97.4%** | **93.6%** | **41.2%** | **negative** |
| Recency-biased | 88.6% | 59.8% | 17.6% | ≈ 0 |
| Familiarity-biased | 37.4% | 6.4% | 0.2% | positive |
| Perfect (control) | 0.0% | 0.0% | 0.0% | +1.0 |

[FIGURE-5: e_jm_2_radar_worst_case.png
Radar chart showing the most inverted domain. Red shape (intuitive
attention) is roughly the inverse of green shape (actual importance).]

[FIGURE-6: e_jm_2_spearman_dist.png
Distribution of Spearman rank correlation between intuitive and
true factor rankings, by attention model.]

**Finding:** Under noise-attracted attention — a stylized operationalization of salience-like
bias in which high-variance factors are overweighted, directionally
consistent with the availability heuristic (Tversky & Kahneman, 1973)
but not a direct test of it — **93.6% of
domains exhibit the trust trap** and **41.2% exhibit full inversion**.
The control condition correctly produces zero inversions, confirming the
experimental design. We note that this is a synthetic parameterization,
not a human-subject validation; the prevalence rate is model-dependent
and would differ under other attention assumptions (e.g., 6.4% under
familiarity-biased attention).

**Business consequence:** For an enterprise deploying AI advisors across
security, procurement, and data quality, domains whose human attention resembles the noise-attracted model
may start with systematically wrong factor priorities. The system is, by default,
reinforcing what humans already believe rather than surfacing what
actually predicts outcomes. Trust trap detection is not an optimization
— it is a correction of the baseline. In a typical deployment, surfacing
the inverted factors could redirect 20-40% of analyst attention from
noise to signal — a direct impact on false positive rates, mean time to
detect, and analyst retention.

The familiarity-biased model shows only 6.4% trust trap rate, suggesting
that when humans have strong domain-specific training that partially
aligns their attention with true importance, inversions are rare. This
provides a testable prediction: trust traps should be more prevalent in
domains where practitioners lack formal decision training — which
describes most enterprise AI deployment contexts.

### 5.2 Factor Weight Discovery (E-JM-5) — The Core Contribution

The prevalence finding in §5.1 establishes that trust traps are common
under plausible attention models. The more important question is whether
the system can *discover* them — and do so without false positives.
This experiment is the central empirical contribution of the paper.

**Question:** Can the system learn the true factor importance from
verified decisions, thereby surfacing trust traps?

**Motivation:** §5.1 quantifies the problem. This experiment tests
whether the DiagonalKernel mechanism can *solve* it — i.e., whether the learned precision weights converge toward the
true factor importance, contradicting the intuitive (inverted) weights.

**Design:** We simulated 100 domains, each with a known trust trap
(noise-attracted intuitive weights). For each domain, we ran 5 trials
of DiagonalKernel learning using inverse-variance × discriminability
weighting — the actual mechanism by which the production system
estimates factor importance. We measured convergence at checkpoints
from 50 to 2,000 verified decisions using four metrics: Spearman rank
correlation, top-3 factor overlap, cosine similarity of weight vectors,
and trust trap surfaced rate (learned ranking matches true AND
contradicts intuitive for the top factor).

[FIGURE-7: e_jm_5_convergence.png
Four-panel chart showing convergence of Spearman r, top-3 overlap,
cosine similarity, and Kendall τ over verified decisions.]

**Results:**

| Verified decisions | Spearman r | Top-3 overlap | Cosine sim | Trap discovered |
|---|---|---|---|---|
| 50 | +0.12 | 0.61 | 0.82 | 62% |
| 200 | +0.13 | 0.61 | 0.82 | 62% |
| 800 | +0.14 | 0.62 | 0.84 | 64% |
| 2,000 | **+0.16** | **0.67** | **0.85** | **63%** |

[FIGURE-8: e_jm_5_discovery_rate.png
Discovery rate over decisions, with reference line at 93.6%
(prevalence from Experiment 1).]

**Finding:** By 2,000 verified decisions, weight vectors achieve 0.85
cosine similarity with ground truth (magnitude recovery) and 67% of the
true top-3 factors are correctly identified. However, Spearman rank
correlation remains low (r = +0.16) and the discovery trajectory is
largely flat from 62% at 50 decisions to 63% at 2,000 — indicating that
factor magnitude is recovered but full ranking resolution is not achieved
in this decision range. **63% of real trust traps are surfaced** with a
false discovery rate of **zero** — the system never claims an inversion
that does not exist. We characterize this as conservative early
detection: the system identifies the majority of trust traps quickly
(within 50 decisions) but does not substantially improve its detection
rate with additional data in the range tested.

**Interpretation:** The system detects roughly two-thirds of trust traps
early (within 50 decisions) and maintains zero false positives throughout.
The flat discovery trajectory (62%→63%) suggests that the remaining
~30% of traps involve factor-importance differences too subtle for the
inverse-variance estimator to resolve at the tested noise levels and
decision volumes. Whether longer horizons (>2,000 decisions) or richer
factor spaces improve detection remains open.

### 5.3 Operational Compounding (E-JM-6)

**Question:** Does intelligence compound super-linearly, and if so,
through what mechanism?

**Motivation:** The central claim of the Compounding
architecture is that decision quality improves faster than linearly with
verified decisions. If quality merely improves linearly (each decision
adds a fixed increment), then the system is a learning tool — useful,
but with linear returns. If quality compounds (each decision makes
subsequent decisions more valuable), then the system creates increasing
returns — a qualitatively different value proposition. Consider the operational difference: a linear system that improves
accuracy by 5% handles the same scope forever. A compounding system
that improves accuracy by 5% AND passes two more categories through
conservation gates doubles its autonomous scope — the VALUE grows
not by 5% but by 5% accuracy × 2× scope.

**Design:** We simulated three learning regimes over 3,000 decisions:
no learning (stateless), linear (uniform kernel — all factors weighted
equally), and compounding (DiagonalKernel with multiplicative
centroid×precision interaction + conservation-gated auto-approval
expansion). The compounding regime models the multiplicative feedback
loop: better DK weights amplify centroids on the right factors, which
produces more correct decisions, which further refines both centroids
and weights. We measured accuracy trajectory, IKS (Institutional
Knowledge Score), and auto-approved category count. 15 trials.

We fit two models to each trajectory: linear (q(n) = a + bn) and
power-law (q(n) = a + bn^c). We also measured a *combined metric*:
accuracy × (approved_categories / total_categories), which captures
both quality improvement and scope expansion.

**Results:**

**The compounding feedback loop.** The mathematical basis for the
quality × scope interaction is a positive feedback cycle with four
stages: (1) centroid refinement improves scoring accuracy q; (2) higher
q passes more categories through the conservation gate α·q·V ≥ θ_min;
(3) broader category coverage α increases the verified decision volume V
per unit time; (4) higher V accelerates centroid refinement (more data
per cell), returning to step 1. Each stage is individually sub-linear,
but the CYCLE produces increasing returns because the output of each
stage is an input to the next. The conservation law is the mechanism
that converts accuracy improvement (stage 1) into scope expansion
(stage 2) — without it, the loop has no gate and scope expansion is
either manual or unbounded.

**Definition (Operational compounding).** We call a trajectory
operationally compounding when a quality-adjusted deployment metric
follows a power-law fit with exponent c > 1 over the measured decision
range. In this experiment, the quality-adjusted metric is *approved
correct-coverage*: verified accuracy multiplied by the fraction of
categories eligible for autonomous approval. We do not claim
super-linear accuracy improvement alone — centroid refinement has
diminishing returns by itself.

We analyzed accuracy improvement and scope expansion independently:

| Metric | Trajectory shape | Exponent |
|---|---|---|
| Accuracy alone | Sub-linear (diminishing returns) | 0.10 |
| Approved categories (scope) | Step-wise expansion | N/A (discrete) |

When both trends are combined — accuracy multiplied by the fraction of
categories passing conservation gates — the resulting composite follows
a super-linear trajectory (exponent 1.14) during the category onboarding
phase. We present this composite as one way to visualize the quality×scope
interaction, not as a definitive measure of intelligence. **This is a
bounded transient:** once all categories have passed the conservation
gate, scope saturates and the metric reverts to accuracy-alone growth
(exponent 0.10). The super-linear phase coincides with category
onboarding — precisely the period where the system's operational value
is expanding most rapidly. Alternative formulations (e.g., economic
value, downstream task success) may yield different exponents and should
be tested.

[FIGURE-18: e_jm_6_trajectories.png
Quality trajectories. Compounding (green) separates from linear
(orange) and stateless (gray) after ~500 decisions.]

[FIGURE-19: e_jm_6_iks_trajectory.png
Two panels: IKS trajectory (top) and approved category count (bottom).]

[FIGURE-20: e_jm_6_combined_metric.png
Combined metric (accuracy × scope). Power-law fit with exponent 1.14.]

**Finding:** Accuracy alone improves sub-linearly — each additional
decision provides diminishing marginal accuracy improvement. This is
expected: centroid refinement has diminishing returns as centroids
converge. However, the *combined metric* — accuracy multiplied by the
fraction of categories that have passed conservation quality gates —
follows a super-linear trajectory with exponent 1.14.

**Interpretation:** Compounding intelligence is an *emergent property*
of the interaction between two mechanisms, not a property of either
mechanism alone:

1. **Quality improvement** (from centroid refinement and DK weight
   learning): each decision makes scoring slightly more accurate.
   This is sub-linear by itself.

2. **Scope expansion** (from conservation-gated auto-approval): as
   category-level quality passes conservation thresholds, more
   categories become eligible for autonomous processing. This is
   gated by conservation.

3. **The product compounds:** when accuracy improves AND scope expands,
   their product follows a super-linear trajectory. More accurate
   scoring across more categories creates increasing returns.

**Bayesian baseline comparison (E-JM-6b).** We compared DiagonalKernel
scoring against a Bayesian online linear regression baseline receiving
the same verified decisions. Over 3,000 decisions (20 trials), DK
achieved +1.21pp higher late-stage accuracy than the Bayesian baseline
(0.371 vs 0.358). The advantage is modest but consistent, and comes from
DK's per-factor precision weighting — the Bayesian model learns a
weight vector but does not separately weight factors by reliability.

[FIGURE-25: e_jm_6b_dk_vs_bayesian.png
DK vs Bayesian accuracy trajectories.]

**Confidence interval for exponent.** Bootstrap resampling (100 samples)
of the approved-correct-coverage exponent yields c = 1.14. All bootstrap
samples produce c > 1, consistent with super-linear growth in the
composite metric. We note that the CI is narrow because the exponent
estimate is stable across trial subsets; wider variation is expected
with more diverse domain configurations.

[FIGURE-26: e_jm_6b_exponent_ci.png
Bootstrap distribution of the compounding exponent.]

The strategic implication is that compounding requires *both*
mechanisms. A system with learning but no conservation (unconstrained)
cannot expand scope safely — there is no quality gate. A system with
conservation but no learning (static rules) cannot improve accuracy —
there are no centroids to refine. Only the combination produces the
interaction effect. This is why the conservation law, which appears to
be a constraint, is actually a *prerequisite* for compounding.

### 5.4 Cross-Domain Transfer (E-JM-3)

**Question:** Does judgment memory learned in one domain accelerate
learning in a related domain?

**Motivation:** In practice, organizations deploy AI decision systems
across multiple domains (security, procurement, data quality). If
judgment memory transfers across related domains, each new deployment
starts with a warm prior rather than cold-starting from zero — reducing
time-to-value from months to weeks.

**Design:** We generated pairs of synthetic domains with controllable
similarity (0.0 = unrelated, 1.0 = identical factor structure). A source
domain learned for 500 verified decisions, building centroid geometry.
We then transferred this geometry to a target domain under three
conditions: cold start (no transfer), partial transfer (0.5× discount),
and full warm start. We measured the number of decisions required to
reach 80% of the source domain's final quality. 20 trials per similarity
level.

[FIGURE-9: e_jm_3_trajectories.png
Six panels showing learning curves by similarity level.]

**Results:**

| Similarity | Cold start | Warm start | Speedup | Negative transfer |
|---|---|---|---|---|
| 0.0 (unrelated) | 346 decisions | 168 decisions | 2.06× | 25% |
| 0.4 (moderate) | 340 decisions | 181 decisions | 1.88× | 0% |
| 0.8 (high) | 282 decisions | 190 decisions | 1.48× | 15% |
| 1.0 (identical) | 350 decisions | 178 decisions | 1.97× | 5% |

Note: The 2.06× speedup at similarity=0.0 appears counterintuitive for
unrelated domains. This is driven by lucky random alignment in some
trials — the warm-start centroid geometry happens to partially match the
target domain by chance. The 25% negative transfer rate at this
similarity level confirms that this speedup is not reliable: in one
quarter of trials, the unrelated prior actually slows convergence.

[FIGURE-10: e_jm_3_convergence_speed.png
Convergence speed vs similarity.]

[FIGURE-11: e_jm_3_negative_transfer.png
Bar chart showing negative transfer rate by similarity level.]

**Finding:** Warm-start transfer provides consistent 1.5–2× convergence
speedup across moderate-to-high similarity levels. However, negative
transfer is real: at similarity 0.0, **25% of trials show warm start
converging slower than cold start**. This motivates the architectural
requirement for *transfer patterns* — explicit nodes in the judgment
memory graph that record which source domain contributed to which target
domain, with similarity metadata. A production system should gate
transfer on measured domain similarity, not blindly apply warm-start
from any available source.

### 5.5 Personnel Change Detection (E-JM-1)

**Question:** Can the conservation law detect when a new decision-maker
with a different quality profile begins operating?

**Motivation:** Personnel turnover is the most common source of quality
disruption in enterprise AI deployments. An experienced analyst leaves;
a new hire begins reviewing decisions with different accuracy and
different factor attention. If the system detects this silently and
surfaces it to supervisors, the organization can respond with additional
training, a supervised period, or recalibration. If it does not detect
it, the quality degradation is invisible until a downstream failure.

**Design:** We simulated 30 trials where Person A (accuracy drawn from
[0.70, 0.90]) makes 500 decisions, then Person B (accuracy drawn from
[0.45, 0.85] — sometimes worse, sometimes comparable) makes 300
decisions. Three conditions: no memory (stateless), flat database
(centroids without conservation), and full judgment memory (centroids +
conservation monitoring). Person B's quality intentionally varies to
include cases where the change is benign.

[FIGURE-12: e_jm_1_trajectory.png
Quality trajectory showing all three conditions.]

**Results:**

- **Detection rate:** 97% (29/30 trials). Conservation correctly
  identified the quality change in nearly all trials.

- **Post-change accuracy:** Judgment memory averaged **-1.69pp** versus
  flat database, with JM performing better in only 9 of 30 trials.

- **Detection speed:** Mean 38 decisions after personnel change.
  Median 25 decisions.

[FIGURE-13: e_jm_1_benefit_scatter.png
Scatter plot: Person B quality (x-axis) vs JM advantage over flat DB
(y-axis). JM helps most when Person B quality is very different from
Person A.]

**Finding:** Conservation detects personnel changes with 97% reliability
and a mean delay of approximately 38 decisions. However, detection does
not automatically translate to improved outcomes. The judgment memory
system averaged slightly worse post-change accuracy than the flat
database because conservation pauses learning, which prevents adaptation
to the new decision-maker's patterns. This is the safety-adaptability
tradeoff identified in §4.3.

**Interpretation:** Conservation is a *diagnostic* tool, not an
automatic corrector. Its value lies in surfacing the change to human
supervisors, who can then decide on the appropriate response. A system
that silently continues learning from a degraded decision-maker will
accumulate centroid drift without any organizational awareness — this is
the failure mode that conservation prevents. The -1.69pp average
accuracy cost is the explicit, measurable price of that detection
capability.

### 5.6 Conservation as Safety Mechanism (E-JM-4)

**Question:** Does the conservation law prevent quality degradation
from corrupted inputs, and what is the cost of the safety guarantee?

**Design:** We simulated four types of quality degradation — personnel
change, 30% data corruption, gradual drift, and 10% adversarial
injection — each applied after 500 healthy decisions. Two conditions:
conservation law active (constrained) and no conservation
(unconstrained). 30 trials per degradation type.

[FIGURE-14: e_jm_4_trajectories.png
Quality trajectories for all degradation types.]

**Results:**

| Degradation type | Detection rate | Conservation advantage |
|---|---|---|
| Personnel change | 100% | -8.0 pp |
| Data corruption (30%) | 100% | -11.1 pp |
| Gradual drift | 100% | -6.5 pp |
| Adversarial (10%) | 100% | -10.5 pp |

[FIGURE-15: e_jm_4_conservation_status.png
Stacked area chart showing GREEN/AMBER/RED status over time.]

[FIGURE-16: e_jm_4_degradation_depth.png
Worst rolling accuracy comparison.]

[FIGURE-17: e_jm_4_detection_rates.png
Detection rates: true positive vs false positive.]

**Finding:** Conservation detects all four degradation types with 100%
reliability. However, the constrained system consistently performs
*worse* than the unconstrained system in post-degradation accuracy, by
6.5 to 11.1 percentage points.

**Interpretation:** This is the most important nuanced finding of our
experimental program. The conservation law is *not* a free lunch — it
trades adaptability for safety. The unconstrained system adapts to
degraded conditions faster because it continues learning. The
constrained system detects the degradation but cannot adapt while paused.

**Recalibration recovery (E-JM-4b).** We tested the full lifecycle:
detect → pause → recalibrate → recover. After Person B arrives with
different factor attention (shifted distribution on 4 of 7 factors),
three conditions: unconstrained, conservation-only (frozen centroids),
and conservation + supervisor-approved recalibration (centroid decay to
15% of prior, count reset, grace period of 200 decisions before
conservation re-engages). 30 trials.

[FIGURE-21: e_jm_4b_trajectory.png
Three-condition trajectory showing conservation pausing, then
recalibration recovering to near-unconstrained accuracy.]

[FIGURE-22: e_jm_4b_recovery_box.png
Late-stage accuracy boxplot comparing the three conditions.]

| Condition | Late-stage accuracy | vs conservation-only |
|---|---|---|
| Unconstrained | 0.497 ± 0.034 | — |
| Conservation only (frozen) | 0.297 ± 0.027 | baseline |
| **Conservation + recalibration** | **0.470 ± 0.035** | **+17.3pp (87% of gap closed)** |

The recalibrated system recovers to within 2.7pp of unconstrained
performance. The full lifecycle works: conservation detects the change
(circuit breaker fires), pauses learning (prevents centroid drift from
misaligned input), supervisor approves recalibration (explicit human
decision), and the system rebuilds centroids aligned with Person B's
patterns. This closes the main gap identified in §5.5/§5.6: conservation
is not just a detector — with recalibration, it is a complete
operational lifecycle.

These results should be read as testing conservation as a circuit
breaker — a detector that prevents silent unsafe operation — not as a
full recovery controller. Conservation's value is not in *improving*
post-degradation accuracy. It is in *preventing silent degradation* — the scenario where an
unconstrained system gradually learns from corrupted input without any
organizational awareness. Silent degradation is invisible until a
downstream failure reveals it; conservation makes degradation visible at
the point of occurrence. The analogy is financial reserves: they reduce
the capital available for lending but prevent institutional failure
during downturns. Conservation is a *quality reserve* — the cost is
explicit, and the catastrophe it prevents is not.

---

## §6 — Discussion

### 6.1 The Trust Trap as a Universal Phenomenon

The 93.6% prevalence finding under noise-attracted attention connects
to a broader literature on cognitive biases. The availability heuristic
(Tversky & Kahneman, 1973) causes people to weight information by how
easily it comes to mind — which correlates with salience and variability,
not with predictive accuracy. The representativeness heuristic leads
people to attend to features that seem "representative" of a category
rather than features that statistically discriminate between categories.

To our knowledge, judgment memory provides the first *computational
mechanism* designed to detect and surface trust traps from verified
outcomes in a production decision-support system. Existing
approaches to factor importance analysis (e.g., SHAP values, permutation
importance) operate on model features, not on human decision factors.
They answer "which features does the model use?" rather than "which
factors should the human trust?" — a fundamentally different question
when the human is the decision-maker and the model is advisory.

### 6.2 The Safety-Adaptability Tradeoff

Our experimental results show that conservation's value is not in
improving post-degradation outcomes (where it performs worse than
unconstrained learning) but in *preventing silent degradation* — the
invisible accumulation of centroid drift from corrupted inputs. This
distinction is analogous to other engineering tradeoffs:

- **Type systems** in programming languages prevent certain classes of
  errors but restrict the expressiveness of code. No serious engineer
  argues that dynamic typing is "better" because it allows more programs
  to run; the question is whether the prevented errors justify the
  restriction.

- **Financial reserves** in banking reduce the capital available for
  lending but prevent institutional failure during downturns. The
  2008 financial crisis demonstrated the cost of insufficient reserves.

Conservation is a *quality reserve*: it restricts the system's
adaptation speed to ensure that human oversight quality never drops
below a provable floor. The cost of this restriction (slower adaptation)
is explicit and measurable (-6.5 to -11.1pp in §5.6), and recoverable:
supervisor-approved recalibration closes 87% of the gap (§5.6,
E-JM-4b). The cost of the alternative (silent degradation) is typically
invisible until a downstream failure reveals it — which may be catastrophic in
domains like security operations, financial compliance, or clinical
decision support.

### 6.3 Limitations

**Simplified simulations.** Our experiments use synthetic domains with
known ground truth. Production domains are messier: factor spaces are
larger, correlations are non-linear, and human decision quality varies
within a single person across sessions. Our simulations capture the
qualitative dynamics but likely underestimate the difficulty of
convergence in real-world factor spaces.

**Conservation threshold calibration.** The simplified simulation uses
fixed quality thresholds, which produced elevated false positive rates in
§5.6 (conservation safety, E-JM-4). The production system uses an adaptive threshold
(θ_min = 23.53/(α×V)) that tightens with volume, addressing this issue.
We did not replicate the adaptive threshold in our experiments.

**Single-process experiments.** All experiments assume a single process
writing to a single graph. Production deployment involves concurrent
writers, network partitions, and eventual consistency — dynamics that
affect conservation guarantees and centroid convergence.

**Scale.** Our experiments use 7 factors and 5-6 categories. Production
domains may involve 15-30 factors and 20+ categories. Convergence
dynamics, centroid separation, and DK weight estimation may differ at
larger scale — a question that only production deployment can resolve.

**No real-world validation.** All results are from simulation. Production
validation awaits pilot deployment, which is underway but has not yet
produced publishable outcome data.

### 6.4 Why Separate Stores Cannot Replicate These Capabilities

An architecture with separate stores for each memory type (a decision
log database, a knowledge graph, a rules engine, and a centroid store)
could in principle replicate any individual capability we demonstrate.
Trust trap detection requires only the centroid store. Cross-domain
transfer requires only centroid geometry. Conservation monitoring
requires only verified decision counts.

What separate stores cannot replicate is the *interaction* between
memory types that produces emergent capabilities:

- **Trust trap contextualized by entity:** "The trust trap on factor F3
  applies specifically to decisions involving entities in the finance
  department" — requires traversing from Judgment to Semantic to Episodic.

- **Transfer gated by conservation:** "Transfer from Domain A to
  Domain B is approved because both domains have conservation status
  GREEN with V > 200" — requires traversing from Judgment to Conservation
  within a single query.

- **Personnel change identified via entity + decision pattern:** "The
  quality drop correlates with decisions reviewed by entity analyst-47
  after date D" — requires traversing from Conservation to Episodic to
  Semantic.

Each of these queries is a single graph traversal in a shared substrate.
Achieving equivalent results via joins across separate stores is possible
in principle but substantially more complex to implement, maintain, and
keep consistent — particularly under concurrent writes and schema
evolution.

**Cross-type interaction experiment (E-JM-7).** We tested whether
entity-contextualized factor weighting (semantic × judgment interaction)
outperforms global factor weighting (judgment only). A domain with 3
entity groups (Finance, Engineering, Operations) has entity-specific
factor importance: factor F3 is highly predictive for Finance but not
Engineering. Three conditions: global DK weights (one set of weights for
all entities), per-entity DK weights (separate weights learned per
entity group — requires semantic × judgment traversal), and separate
stores (entity lookup exists but DK weights are global — simulates an
API-stitched architecture without cross-type joins). 25 trials, 2000
decisions.

[FIGURE-23: e_jm_7_accuracy.png
Accuracy trajectories for three conditions.]

[FIGURE-24: e_jm_7_trap_detection.png
Per-entity trust trap detection rates by condition.]

| Condition | Late accuracy | Entity-specific trap detection |
|---|---|---|
| Global DK | 0.485 | 8.6% |
| Separate stores | 0.485 | 8.6% |
| **Per-entity DK** | **0.486** | **22.9%** |

The accuracy advantage is modest (+0.12pp), but the entity-specific
trust trap detection rate is **2.7× higher** with per-entity DK weights
(22.9%) compared to global or separate-store conditions (8.6%). This
demonstrates that **per-entity factor weighting detects entity-specific
inversions that global analysis misses** — a method-level finding about
the value of conditioning DK weights on entity context.

**Important limitation:** The separate-stores condition simulates entity
lookup + global DK (no per-entity join), but a practitioner could achieve
per-entity weighting in a stitched architecture via SQL GROUP BY or
equivalent partitioning. We expect such an implementation would match the
22.9% detection rate. The finding is therefore that per-entity > global
weighting — not that a shared graph is strictly necessary for this
capability. The shared-graph argument rests on reduced integration
complexity for multiple simultaneous cross-type interactions (§3.4),
not on this single experiment.

This experiment provides initial evidence for the shared-graph
hypothesis, though the effect on accuracy is small. Larger-scale
experiments with more entity groups and production-scale factor spaces
may show stronger differentiation. Latency and operational cost
comparisons remain future work.

---

## §7 — Related Work Comparison

| System | Episodic | Semantic | Procedural | Judgment | Conservation | Cross-type |
|---|---|---|---|---|---|---|
| CrowdStrike Falcon | Alert log | Threat graph | Playbooks | ❌ | ❌ | API-stitched |
| Splunk SOAR | Event store | ❌ | Automation | ❌ | ❌ | ❌ |
| MS Sentinel + Copilot | Alert log | Entity graph | KQL rules | ❌ | ❌ | LLM-mediated |
| Palo Alto XSOAR | Incident log | Threat intel | Playbooks | ❌ | ❌ | Orchestrated |
| Darktrace | Packet log | Device model | Auto-response | Partial¹ | ❌ | Proprietary |
| Coupa BSM | Transaction log | Supplier DB | Approval rules | ❌ | ❌ | Report joins |
| MAML (Finn 2017) | ❌ | ❌ | Meta-policy | ❌ | ❌ | N/A |
| GraphRAG (Edge 2024) | ❌ | KG + LLM | ❌ | ❌ | ❌ | LLM-mediated |
| RLHF (Ouyang 2022) | ❌ | ❌ | Aligned policy | ❌ | ❌ | N/A |
| **This work** | ✅ | ✅ | ✅ | ✅ | ✅ | **Graph traversal** |

¹ Darktrace's Enterprise Immune System uses unsupervised Bayesian
methods to learn "normal" network behavior and detect deviations. Three
distinctions from judgment memory: (a) *Data source:* Darktrace learns
from packet/flow telemetry; judgment memory learns from verified human
decisions (analyst confirm/override). (b) *Factor-level quality:*
Darktrace's anomaly scores are aggregate deviations; judgment memory
maintains per-factor precision weights (W_k) that tell the human which
specific factors to trust. (c) *Conservation invariant:* Darktrace has
no published deployment-time quality bound analogous to α·q·V ≥ θ_min;
its autonomous response (Antigena) is gated by confidence thresholds,
not by a mathematical invariant on verified human oversight quality.
We acknowledge that Darktrace's proprietary internals may include
additional mechanisms not described in public documentation.

**Judgment memory requires all of the following** (our proposed
discriminator for related-work comparison):
(1) verified human outcome labels as the learning signal,
(2) persistent per-factor quality state (not hidden model weights),
(3) category/action-conditioned geometry (centroid tensor),
(4) inspectable factor-reliability weights (DiagonalKernel),
(5) deployment-time conservation state bounding autonomous scope, and
(6) transferable memory artifacts across related domains.
We found no publicly documented system that implements all six elements.

The distinguishing capability is not any single column but the
combination of all six: four memory types, conservation bounding, and
cross-type interaction via graph traversal rather than API stitching,
LLM mediation, or orchestration middleware. Each competitor implements
1-3 memory types; we found no publicly documented system implementing
all six elements of judgment memory defined above.

---

## §8 — Conclusion

We have proposed judgment memory as a computationally distinct fourth
cognitive type for AI decision systems. Unlike episodic memory (what
happened), semantic memory (what is known), and procedural memory (what
to do), judgment memory encodes *what to trust* — the quality structure
of domain expertise learned from verified human decisions.

Our experimental program (9 experiments, 500+ synthetic domains)
establishes five principal results:

1. **Trust traps are prevalent and discoverable.** Under a stylized
   operationalization of salience-like attention, 93.6% of domains
   exhibit signal-confidence inversion (§5.1). The DiagonalKernel
   mechanism surfaces 63% of these with zero false positives within
   2,000 verified decisions, outperforming Bayesian online regression
   by +1.21pp on the same data (§5.2, E-JM-6b).

2. **Quality and scope compound through their interaction.** Accuracy
   alone improves sub-linearly. But its interaction with conservation-
   gated scope expansion creates a feedback loop (accuracy → scope →
   volume → accuracy) that produces increasing returns. Conservation
   is not merely a safety constraint — it is a prerequisite for the
   scope expansion that creates compounding value. (§5.3)

3. **Conservation is a complete lifecycle.** The conservation law
   detects quality changes with 97–100% reliability, and supervisor-
   approved recalibration recovers 87% of the accuracy gap, closing
   the detect-pause-recalibrate cycle. The cost of the safety
   constraint (-6.5 to -11.1pp) is explicit and recoverable. (§5.5,
   §5.6)

4. **Cross-domain transfer works when gated by similarity.** Warm-start
   provides 1.5–2× convergence speedup at moderate-to-high similarity.
   Negative transfer at low similarity (25%) must be gated. (§5.4)

5. **Cross-type interactions produce capabilities isolation misses.**
   Entity-contextualized factor weighting detects 2.7× more entity-
   specific trust traps than global or separate-store architectures,
   providing initial evidence for the shared-graph hypothesis. (§6.4)

E-JM-7 provides initial evidence that cross-type interactions
(semantic × judgment) produce capabilities that global or stitched
approaches miss. We argue that these capabilities are best served by a
single governed graph substrate enabling native traversals. While
stitched architectures could achieve similar results in principle,
E-JM-7 shows that the separate-stores condition (entity lookup + global
DK, no per-entity join) performs identically to the global-only
condition — the interaction, not just the presence of both data types,
drives the improvement. Broader empirical comparison (latency, cost,
scale) remains future work.

The question is not whether AI decision systems should learn from
verified outcomes — the alternative is permanent amnesia. The question
is whether they can do so safely, transparently, and with mathematical
guarantees of human oversight quality. Judgment memory, bounded by
conservation law, implemented in a shared graph substrate, is our
answer. Any AI advisory system that lacks verified-outcome factor learning
is vulnerable to trust traps: it may continue reinforcing human
attention patterns even when those patterns diverge from predictive
structure. Judgment memory is the proposed architectural correction —
and conservation law is the deployment-time guarantee that the
correction does not create new risks.

---

## References

Bai, Y., et al. (2022). Constitutional AI: Harmlessness from AI
Feedback. *arXiv:2212.08073*.

Banerjee, A. (2026). Compounding Generalized Agents: Conservation Law
and Re-Convergence for Multi-Domain Decision Systems. *In preparation*.

Bollacker, K., et al. (2008). Freebase: A Collaboratively Created
Graph Database for Structuring Human Knowledge. *SIGMOD*.

Christiano, P., et al. (2017). Deep Reinforcement Learning from
Human Preferences. *NeurIPS*.

Edge, D., et al. (2024). From Local to Global: A Graph RAG Approach to
Query-Focused Summarization. *arXiv:2404.16130*.

Finn, C., Abbeel, P., & Levine, S. (2017). Model-Agnostic
Meta-Learning for Fast Adaptation of Deep Networks. *ICML*.

Lewis, P., et al. (2020). Retrieval-Augmented Generation for
Knowledge-Intensive NLP Tasks. *NeurIPS*.

Mnih, V., et al. (2015). Human-Level Control Through Deep
Reinforcement Learning. *Nature*, 518(7540), 529-533.

Nichol, A., Achiam, J., & Schulman, J. (2018). On First-Order
Meta-Learning Algorithms. *arXiv:1803.02999*.

Ouyang, L., et al. (2022). Training Language Models to Follow
Instructions with Human Feedback. *NeurIPS*.

Schaul, T., et al. (2016). Prioritized Experience Replay. *ICLR*.

Sutton, R. S., & Barto, A. G. (2018). *Reinforcement Learning:
An Introduction* (2nd ed.). MIT Press.

Tversky, A., & Kahneman, D. (1973). Availability: A Heuristic for
Judging Frequency and Probability. *Cognitive Psychology*, 5(2), 207-232.

Sumers, T. R., et al. (2023). Cognitive Architectures for Language
Agents. *arXiv:2309.02427*.

Vinyals, O., et al. (2016). Matching Networks for One Shot Learning.
*NeurIPS*.

---

## Appendix A — Experiment Parameters

| Parameter | E-JM-2 | E-JM-5 | E-JM-6 | E-JM-6b | E-JM-3 | E-JM-1 | E-JM-4 | E-JM-4b | E-JM-7 |
|---|---|---|---|---|---|---|---|---|---|
| Domains | 500 | 100 | 1/trial | 1/trial | variable | 1/trial | 1/trial | 1/trial | 1/trial |
| Factors | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 |
| Categories | N/A | N/A | 6 | 6 | 5 | 5 | 5 | 5 | 5 |
| Decisions | N/A | 2,000 | 3,000 | 3,000 | 500+400 | 800 | 800 | 1,000 | 2,000 |
| Trials | 500 | 5/dom | 15 | 20 | 20/lvl | 30 | 30 | 30 | 25 |
| Key metric | Prevalence | Discovery | Exponent | Baseline | Speedup | Detection | Tradeoff | Recovery | Cross-type |

## Appendix B — Graphics and Equation Inventory

| Marker | Source | Type | Status |
|---|---|---|---|
| FIGURE-1 | Manual design | Taxonomy + Three Eras timeline | ❌ Create |
| FIGURE-2 | Manual design | Centroid geometry Day 1→Month 6→Month 12 | ❌ Create |
| FIGURE-3 | Manual design | Conservation state machine | ❌ Create |
| EQUATION-1 | LaTeX | J = (M, W, S) definition | ❌ Typeset |
| EQUATION-2 | LaTeX | Centroid update rule | ❌ Typeset |
| EQUATION-3 | LaTeX | DiagonalKernel precision | ❌ Typeset |
| EQUATION-4 | LaTeX | Conservation formula | ❌ Typeset |
| EQUATION-5 | LaTeX | θ_min definition | ❌ Typeset |
| FIGURE-4 | e_jm_2_inversion_rates.png | Bar chart | ✅ Ready |
| FIGURE-5 | e_jm_2_radar_worst_case.png | Radar chart | ✅ Ready |
| FIGURE-6 | e_jm_2_spearman_dist.png | Histogram panels | ✅ Ready |
| FIGURE-7 | e_jm_5_convergence.png | 4-panel convergence | ✅ Ready |
| FIGURE-8 | e_jm_5_discovery_rate.png | Discovery rate curve | ✅ Ready |
| FIGURE-9 | e_jm_3_trajectories.png | 6-panel learning curves | ✅ Ready |
| FIGURE-10 | e_jm_3_convergence_speed.png | Speed vs similarity | ✅ Ready |
| FIGURE-11 | e_jm_3_negative_transfer.png | Bar chart | ✅ Ready |
| FIGURE-12 | e_jm_1_trajectory.png | 3-condition trajectory | ✅ Ready |
| FIGURE-13 | e_jm_1_benefit_scatter.png | Scatter plot | ✅ Ready |
| FIGURE-14 | e_jm_4_trajectories.png | 5-panel trajectories | ✅ Ready |
| FIGURE-15 | e_jm_4_conservation_status.png | Stacked area | ✅ Ready |
| FIGURE-16 | e_jm_4_degradation_depth.png | Bar comparison | ✅ Ready |
| FIGURE-17 | e_jm_4_detection_rates.png | Detection rates | ✅ Ready |
| FIGURE-18 | e_jm_6_trajectories.png | 3-regime trajectories | ✅ Ready |
| FIGURE-19 | e_jm_6_iks_trajectory.png | IKS + scope panels | ✅ Ready |
| FIGURE-20 | e_jm_6_combined_metric.png | Combined metric | ✅ Ready |

| FIGURE-21 | e_jm_4b_trajectory.png | 3-condition recalibration | ✅ Ready |
| FIGURE-22 | e_jm_4b_recovery_box.png | Recovery boxplot | ✅ Ready |
| FIGURE-23 | e_jm_7_accuracy.png | Cross-type accuracy | ✅ Ready |
| FIGURE-24 | e_jm_7_trap_detection.png | Entity trap detection | ✅ Ready |
| FIGURE-25 | e_jm_6b_dk_vs_bayesian.png | DK vs Bayesian | ✅ Ready |
| FIGURE-26 | e_jm_6b_exponent_ci.png | Bootstrap CI | ✅ Ready |

**23 of 26 figures ready.** 3 conceptual diagrams + 5 equations to create.

---

*Judgment Memory: A Conservation-Bounded Fourth Cognitive Type*
*Draft v9.0 · June 1, 2026*
*~10,500 words · 8 sections · 9 experiments · 26 figures*
