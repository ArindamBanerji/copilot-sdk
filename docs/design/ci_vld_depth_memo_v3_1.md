# VLD-Depth — Comprehensive Reference (memo v3.1)

**What this is:** the single authoritative reference for VLD-Depth in CI. Supersedes v3 (revised after a
Sonnet LLM-judge + internal review: moat claim tiered, γ-warning moved early, guard rationale
de-duplicated, the minimum DX-1 spec inlined, and cost/stopping-rule risks added). **Tier:** proposal /
discovery (F-24 — no claim above its evidence).

**How to read this.** §1–§3 brief a fresh reader (what VLD is, why it's integrated, how it differentiates
+ its customer value). §4–§9 are the mechanism/discipline. §10–§12 are the executor's reference (the
experiment program, incl. an inlined minimum spec, code hooks, ownership). Load-bearing claims are in
**bold**; parentheticals are scaffolding.

**One line:** apply the looped-transformer / virtual-logical-depth result (*reuse the operator to add
reasoning depth without adding parameters*) to the CI scorer at inference — iterated, conservation-gated,
inspectable deliberation over the reified judgment graph.

## 0. Current status

Candidate mechanism, not in production. We are in DISCOVERY — mapping the design space, not chasing a
number. The first confirmatory run (E1) hit a temporal-leakage artifact (offline replay leaked through
the live graph → hard-case accuracy → exactly 1.0), which is why temporal integrity and non-circular
synthetic instruments are load-bearing. Current plan: characterization first (§10); make-or-break later.

## 1. What VLD-depth is, and why it's a distinct axis

- **Borrowed result:** reusing an operator adds reasoning depth without adding parameters — knowledge
  scales with parameters, reasoning with depth. (Frontier version, e.g. Astra, is controversial because
  latent depth is unmonitorable — §5.)
- **CI mapping:** knowledge = centroids μ (STATE, reified, **frozen at inference**); reasoning = how the
  operator resolves a situation against μ (COMPUTATION). VLD deepens COMPUTATION without touching STATE.
- **A distinct third axis:** per-decision *inference* depth — think harder on THIS case, now. Separate
  from the two learning-trajectory engines: Depth = State×Decisions (learning rate, γ>1), Breadth =
  Enrichment×State (floor, +5.9pp). Today's scorer is VLD at L=1.
- **⚠ Two γ's — do not conflate (holds throughout this doc):** *learning-time* re-convergence γ>1 is
  CONFIRMED (proved + apparatus); *inference-time* contraction (§5) is a SEPARATE, UNPROVEN claim. Where
  "γ" appears below, it is the learning-time one unless it says "inference-time contraction."

## 2. The full-integration principle (organizing stance)

**VLD-depth delivers differentiated value only when integrated across value, architecture, and
implementation. It is the deliberation mode of the reshape graph, not a module.**
- **Value:** iteration only helps if it converges toward the firm's learned judgment on the hard,
  precedent-free, and "do-less" cases; iterating a retrieval or a route has nothing to converge to (=
  re-smoothing, which our placebo control showed).
- **Architecture:** VLD iterates the decision geometry (μ), gated by conservation, over the reified
  graph. Strip any of {geometry, conservation, verified-outcome reshaping} and it stops meaning anything.
- **Implementation:** inspectability, firewall-safe re-admission, and per-iteration conservation survive
  only if Φ is woven into the real scorer/SA/conservation components (a replay adapter).

This principle governs the whole doc; later sections reference it rather than restate it.

## 3. Differentiation over graph-engineering, and customer value

**The separation today (graph-native docs):** "graph engineering" is a knowledge graph you *read*
(retrieves what's *stated*, needs a precedent) or a graph of agents you *route* (orchestration, a
snapshot). Both are *structure*. CI *reshapes*: the decision is geometry (nearest-prototype, not an LLM
guess), a verified outcome moves the prototype, conservation abstains. That reified structure is
**judgment memory** — the fourth cognitive type beyond episodic/semantic/procedural (JM paper;
its trust-trap/transfer/personnel results are **synthetic-tier**). Read/route are blind at the
no-precedent case (Stryker) and the "do-less" case.

**What CI+VLD adds — a second axis of separation** (*only when integrated per §2*):

| | Learns from verified outcomes? | Computes the decision (deliberates to convergence/abstention at adaptive depth)? |
|---|---|---|
| Read (GraphRAG/Neo4j) | no | no — single retrieval |
| Route (LangGraph/CrewAI) | no | no — single orchestration |
| CI (reshape) | **yes** | single pass over judgment |
| **CI + VLD** | **yes** | **yes — self-computing: iterates its own decision geometry** |

**The moat — stated as an architectural hypothesis, not a demonstrated result (same honesty tier as the
JM claims).** "Copying the loop copies nothing" rests on two *distinct* barriers, and it is worth keeping
them separate:
- **Structural (strong, untested):** VLD needs the whole integrated reshape architecture — reified
  geometry + conservation gate + verified-outcome reshaping + inspectable implementation — to host it at
  all. A read/route stack cannot bolt on VLD without becoming a reshape architecture.
- **Time-lag (weaker, from the hero doc):** even a competitor who builds that architecture starts with
  empty μ; the firm-specific accumulated judgment takes verified decisions to build.
VLD *depends on* the structural barrier and *amplifies* the time-lag one (it spends accumulated μ
harder). Neither is demonstrated; both are architectural arguments.

**End-customer value (hypothesized; pending the §10 evidence):**
1. **Handles the precedent-free hard cases** (the Stryker gap) — adaptive depth on the cases that become
   incidents/leakage/missed threats. The highest-cost slice.
2. **"Do less," deliberated and calibrated** — abstain and escalate when depth still can't clear
   conservation. Safe autonomy expansion; fewer confident-wrong actions.
3. **Auditable deliberation (anti-Astra)** — depth you can inspect pass-by-pass and roll back.
4. **The deliberation compounds** — it deliberates against μ, and μ compounds.
5. **On top of what you own, no bigger model** — better hard-case decisions without retraining, spent
   only where it helps.
By track: S2P/Purchasing (novel invoices/orders → recovered leakage + right escalations + audit); SOC
(no-precedent attacks → fewer missed incidents + honest abstention); DataOps (ambiguous source-trust).

*The whole of §3 is architectural/hypothesized. The magnitude — does integrated deliberation beat
single-pass on the hard tail — is exactly what §10 tests.*

## 4. The formalism

- One pass (current): `v0 = A(s, G, μ)`; decision `= argmin_a ‖v0 − μ_{c,a}‖` (ProfileScorer, softmax
  over −distance; L2 kernel = the +36.89pp-over-dot capability, distinct from the DK boundary — *both
  pending ci_core re-verification*).
- VLD: `v_{t+1} = (1−ε)·v_t + ε·Φ(v_t; G, μ)`, **μ FROZEN**. Φ = replay adapter (SituationAnalyzer is a
  dispatcher over TraversalPattern adapters, no native update op); CompoundingScorer's non-mutating paths
  (`score_read_only`/`score_with_model_state`/`gae_scorer`) make frozen-μ replay natural.
- Halt: fixed-point (Δ<δ) OR conservation-sufficient q OR L_max; **abstain** if q<θ_min. Conservation is
  a gate, never an accuracy surrogate.

## 5. Stability, convergence, safety — what the theory predicts (falsifiable)

- **Contraction:** `Lip(T) ≤ 1 + ε(λ−1)`, λ=Lip(Φ). λ<1 ⇒ converges (any ε); λ≥1 ⇒ diverges (every ε).
  Damping controls the interior, cannot rescue an expansive operator. ε≈1/N is a candidate knee.
- **σ⊥μ:** interior refines the signal; near decision boundaries the second-order coupling turns on and σ
  amplifies → **that is where the loop must ABSTAIN, not iterate.** Stability boundary = safety boundary.
- **Bounded returns:** VLD plateaus; value question = does the plateau sit above L=1 on the hard region.
- **Monitorability:** the loop runs over the reified graph → inspectable depth (unlike frontier latent
  depth).

## 6. The integration point — the hard design problem (see §2)

| Attach point | What Φ does | Main risk |
|---|---|---|
| factor-vector | refine v directly | geometric drift |
| graph-context refresh | re-admit implicated context | firewall risk — unbounded re-admission accumulates unverified ENRICHMENT; damped monotone admission is a firewall mechanism |
| score-readout / rerank | adjust the readout | false-win trap — calibration shift with no truth gain; measure truth-accuracy |
| centroid-assignment | EM-like reassignment | wrong-basin convergence |
| sidecar-only | AgentEvolver shadow suggestion | governance-clean; may be weaker |

Coupled decisions: feedback signal, firewall integrity, conservation-per-iteration (`C-COUPLE`),
provenance, cost. Minimal test integration: offline replay, no production-scorer change.

## 7. Guards, and why each exists (canonical — other sections reference here)

- **Placebo (random feedback):** separates real reasoning from re-smoothing. Real − placebo is the only
  meaningful effect.
- **Accuracy vs verified outcomes, never distance-to-μ:** iterating toward μ trivially cuts distance-to-μ
  (circular). Held-out truth-accuracy (+ graded reward) is the only non-circular metric.
- **Temporal integrity (production):** point-in-time cut; the live graph holds the outcome (the E1 leak).
  A hard-case jump to ≈1.0 is a leakage alarm.
- **Non-circular synthetic:** GT-centered vectors independent of μ (never μ-drawn — H-KERNEL
  circularity); leak-free; the right instrument for architecture/stability.

## 8. What the patterns mean

Stable contractive region + real>placebo + σ bounded + no easy-churn ⇒ mechanism exists. Depth ≈
matched-compute-and-evidence breadth ⇒ the thesis folds. Placebo tracks real ⇒ re-smoothing. Lift only
near boundary with σ-blowup ⇒ abstain there. ≈1.0 on hard cases / probe predicts outcome ⇒ leakage. A
pattern is a *finding* only if consistent across seeds AND domains AND surviving placebo+leakage; else a
*lead*.

## 9. Honesty & tiering

F-24: no claim above its tier; label the Φ-fidelity tier (approx / SA-replay / live) on every result.
Not-a-safe-default = a **boundary / operating-envelope** result, not a failure. +36.89pp (L2-vs-dot) =
citable capability; DK (+13pp) = boundary — never conflate (*both pending ci_core re-verification*).
γ>1 = learning-time confirmed; inference-time contraction = unproven. JM findings = synthetic-tier. The
§3 moat/value = architectural hypothesis.

## 10. The experiment program (characterization-first; patterns, not numbers)

Map the space *before* make-or-break. Parameterized as **four coupled decision-families**; low-level
parameters are the instrument:
- **A. Architecture** — operator role (transform / rerank / EM-reassign / context-reshape / retrieval) ×
  locus (in-scorer / sidecar / pre-score) × depth structure × termination.
- **B. Hypotheses** — which claims have empirical structure worth formalizing (contraction, σ⊥μ-at-
  inference, depth≠breadth, value-invariant, complement-vs-duplicate-γ).
- **C. Integration** — attach point, feedback, C-COUPLE, firewall, provenance, cost → a consequence-map.
- **D. Metrics (co-equal)** — select the value yardstick(s) that are BOTH *discriminating* (separate
  design choices) AND *valid* (not gamed by distance-to-μ / calibration / leakage). Candidates:
  truth-accuracy, graded reward, net-value (hard-gain − easy-churn − abstain-cost), hard-tail,
  real−placebo, cost-adjusted, generalization, robustness, audit cost.

**First move — DX-1 (minimum spec, inlined so this doc is self-contained):**
- Instrument: non-circular synthetic, GT-centered, independent of μ.
- Tensor shapes (all five — the first-move instrument because they are the real deployed geometries and
  test shape-dependence): SOC 6×4×6, Trading 5×4×10, Purchasing 5×4×7, DataOps 6×5×6, S2P 5×5×8.
- Sweep: attach-point × feedback-signal × geometry-regime (margin×σ×boundary) × L, with a placebo arm.
- ε candidates: {1/N (≈1/L), 0.1, 0.25, 0.5, 1.0}; L = 1..6 (extend if no plateau); seeds ≥ 3
  (deepen promising cells later).
- Φ (minimum): a replay adapter over SA-consolidation with entity-implication feedback, damped monotone
  admission; label its fidelity tier.
- Output: a design-space map (sensitivities, interactions, regimes, chosen value-metric) — **no verdict.**
- Full detail: `ci_vld_depth_experiment_set_consolidated_v2.md` (the S-sequence).

**Risks & stopping rules (for the characterization phase itself):**
- **Cost/latency:** model L-scaling explicitly — graph-query count and abstain/latency cost per pass;
  a pattern that needs large L or unbounded traversal is not shippable regardless of accuracy.
- **Underpowered hard tail:** if a domain's hard tail is too small to detect a real effect, report
  power/Ν limits, don't over-read; pool cautiously and never cross-domain-average away a null.
- **Diffuse-map stopping rule:** if, after the coarse sweep, no decision-family (A/B/C) shows
  discriminating structure and no metric (D) both discriminates and stays valid, **STOP** — do not
  deepen; the mechanism (not the tuning) is the problem, and VLD-as-inference-depth should be
  reconsidered or shelved.

**Invariants (every cell):** paired seeds · placebo · accuracy AND graded reward vs verified outcomes
(never distance-to-μ) · leakage probe + point-in-time cut on production · non-circular synthetic ·
separate reporting of convergence/distance/σ/entropy/churn/cost · Φ-fidelity tier labeled · cross-domain
normalized (margin/entropy/factor-dim) · pattern holds only across seeds AND domains AND surviving
placebo+leakage · cheap-wide-first.

## 11. Available machinery (code hooks)

`ProfileScorer` (softmax over −distance; action/probs/distances/confidence/entropy/gap) ·
`CompoundingScorer` non-mutating paths (frozen-μ replay) · `SituationAnalyzer` dispatcher over
`TraversalPattern` adapters (build Φ here) · Conservation `α·q·V≥θ_min`, `θ_min=23.53/(α·V)` +
recent-quality pause · Fingerprint per-factor σ → inverse-variance weights (observable) · AgentEvolver
shadow-runner + promotion-gate sidecar · Tensors as in §10.

## 12. Placement & ownership

COMPUTATION-cell hypotheses for `ci_graph_hypotheses`; proposal/lead tier until confirmed across the
sweep and validated on production. The contraction / σ⊥μ formalism → source session once DX-1/stability
maps a stable region worth proving. Conservation-coupled halting and sidecar ownership touch H-BOUND / AE
governance → source-session safety calls. Judgment-memory framing aligns with the JM paper; VLD is the
inference-time deliberation over that memory.
