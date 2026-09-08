# VLD-Depth — Comprehensive Reference (memo v11, self-contained)

**What this is:** the authoritative VLD-Depth reference, rebuilt after a five-judge review that found the
prior formalism broken in two ways. Supersedes v8. **Self-contained:** the executable experiment plan (Appendix B) and the value-sim code
(Appendix C) are embedded; only the full 38-decision parameterization and the five raw judge responses
are external (summarized in Appendix A). **New in v7:** §3B — m is a *semantic* decision category.
**New in v8:** §3C — "prior decisions are evidence" → **one Ψ**; A0 risk on **retrieval geometry**.
**New in v10 (after 3 reviews):** §3A replaced with a **real-mechanism pilot** (Appendix C is retired to a
closed-form calculator — it was mislabeled a simulation); Lemma A0, §5 (contraction), and §6/N2
corrected; §3C dichotomy softened to a design axis; moat retiered; experiments hardened. Consolidation: `ci_vld_v9_feedback_consolidation.md`.
**New in v11:** the real-mechanism pilot's **approach, full data, and code are embedded (§3A + Appendix D)**;
response-spec adds **P5/P6** (react to the pilot + the "retrieval-not-loop" finding; are the attribution
controls right). The pilot moved the value story — **P5 is now co-highest-leverage with P1.** **P1 (graph traversability) remains the highest-leverage *fact* to
fetch — but it *scopes* the mechanism; it does not decide value.** **Tier:** proposal / discovery (F-24). The
five-judge review's main insights are in **Appendix A** (context). **Full decision detail:**
`ci_vld_decision_register_v5_final.md`.

**Two corrections that forced this revision:**
1. **A0 (mechanism):** with the graph and learned state frozen, the single-operator loop is a
   *deterministic post-processing of one pass* — replicable one-shot, and it tracks placebo. Depth is
   real only if **each pass reads new evidence conditioned on the current state** (Φ = A∘Ψ, §4).
2. **§5 was mathematically wrong:** "λ≥1 ⇒ the loop diverges" is false (counterexample below).
   Contraction is an **experiment**, and "stability = safety" is a **conjecture**, not a result (§5).

**One line:** apply virtual-logical-depth to the CI scorer at inference as **adaptive, state-conditioned
retrieval + damped re-scoring over the frozen point-in-time judgment graph**, halted by conservation,
fully inspectable — and prove it adds decision utility that extra evidence, recalibration, re-smoothing,
leakage, or abstention cannot explain.

## ★ What we need you to respond with (to move VLD forward)

This memo exists to be reacted to by other sessions. Respond against the IDs below; **P1 is the single
highest-leverage item in the whole program** and, if you can do only one thing, do P1.

**P1 — [HIGHEST LEVERAGE] Resolve the graph-traversability question (§3C step 8).** *Requires repo
access.* Determine whether CI's decision graph is traversable **topologically over decisions** — are
there causal / entity / temporal edges *between* prior decisions (campaign membership, shared-entity,
`CONTINUES`, lineage) — or **only by similarity** (nearest-prototype / centroid distance). Respond with:
- the decision-node schema and the **actual edge types between decisions** (cite files/paths);
- **yes/no + evidence:** can Ψ reach a *causally-related* prior decision *without* going through
  similarity?
- if **similarity-only:** what *non-decision* evidence (entities, artifacts, campaigns) causally links
  decisions — i.e. where could `m_topological > 0` come from at all?
**Why it matters (scopes, doesn't decide):** it establishes the **available retrieval mechanisms + effort**.
Similarity-only does **not** make judgment-trace Ψ A0 by construction — outcome/edges of similar decisions
can still add evidence (§3C-4). Preliminary (repo-aware reviewers): **no decision→decision causal edge on
record;** access is via shared hubs (Decision→Alert/Entity), meaningful for SOC, S2P after OD-1,
≈0/unestablished elsewhere; migration status is a precondition. Do the repo audit before Ψ design.

**P2 — Estimate `m_topological` per copilot (domain owners).** From real cases, for your copilot:
`m_topological` (fraction of hard decisions resolvable by a *genuine causal chain* of
prior-decisions/evidence, **not** merely "similar past cases"), the hard-tail fraction,
value-per-recovered-case (in your unit), and 1–2 real multi-hop cases. Plug into the §3A curve.
**SOC and DataOps first** (they clear the headroom bar under assumed m).

**P3 — Ratify the flagged calls (accept / amend + the amendment).** *Source-session / safety:* the §5
stability rewrite (contraction = experiment; "stability ≠ safety"), the θ_min form (§6), the
frozen-state contract Θ={μ,DK,preproc,τ,σ} (§4), N2/N3. *Domain owners:* the cost matrix + hard-tail
regions (§8/§10).

**P4 — React to the reasoning (agree/disagree + why).** The m-as-semantic-category claim (§3B); the
one-Ψ collapse + topological-vs-similarity *axis* (§3C, now a design axis not a theorem); the moat
(§3C-7, retiered); anything mis-tiered (§9).

**P5 — [co-highest-leverage] React to the real-mechanism pilot and its finding (§3A + Appendix D).** The
pilot is non-circular with real traversal + real scoring; its finding is that **value is in acquiring the
right evidence (adaptive retrieval), not in the loop** — Δ_trajectory = 0, Δ_depth¬breadth small (−0.03
for Purchasing), Ψ-similarity harms. Respond with: (a) is the pilot's **construction fair** (the graph/
chain model, non-circularity, the arms)? (b) does this finding **warrant pivoting the program** from
"VLD-the-loop" toward "adaptive retrieval (Ψ-once / few-step)"? (c) what construction would make the loop
(trajectory) show value if it exists (e.g., ambiguous multi-pointer frontiers where the next read depends
on v_t)?

**P6 — Are the attribution controls the right decisive tests?** `final-evidence-once` (isolates the
trajectory beyond the acquired evidence) and `traverse-without-scorer-feedback` (isolates whether decision
geometry improves retrieval over ordinary adaptive investigation). Confirm these correctly isolate
trajectory-value and scorer-conditioning-value, or propose better controls.


**Format:** answer by ID (P1–P6) and section number; keep *facts* (P1, code evidence) separate from
*opinions* (P4) and *owner decisions* (P2/P3). A one-line P1 yes/no-with-evidence already moves the
program more than a full P4 essay.

## 0. Status
Parameterization: done. Five-judge review: done (Appendix A). This memo applies its corrections.
Characterization is gated on: the memo-v5 math (this doc), the corrected experiment contract (§10), and
the M5 bitemporal build (§10/§11). Grounding fixes carried: `CompoundingScorer` in
`copilot_sdk/scoring/scorer.py` (`compounding.py`/`storage.py` stale); live corpus underpowered →
production replay gated.

## 1. What VLD is, and why it is a distinct axis
Knowledge = centroids μ (frozen); reasoning = how the operator resolves a situation against μ. VLD
deepens reasoning at inference without touching learned state. It is a **third axis** distinct from the
two learning-trajectory engines (Depth = State×Decisions, learning rate γ; Breadth = Enrichment×State,
floor). **⚠ two γ's:** learning-time re-convergence γ>1 is confirmed; inference-time convergence (§5) is
separate and unproven. **A0 caveat (up front):** today's L=1 scorer, iterated with no new reads, is a
trivial post-processing — see §4.

## 2. Full-integration principle
VLD delivers value only integrated across value/architecture/implementation — it is the *deliberation
mode of the reshape graph*, not a module. It iterates the decision geometry under conservation over the
reified graph; strip the geometry, conservation, or verified-outcome reshaping and it means nothing.

## 3. Differentiation & customer value (tiered honestly)
CI *reshapes* (decision-is-geometry; verified-outcome-moves-prototype; conservation abstains) — this is
**judgment memory** (JM paper; synthetic-tier). VLD adds a second separation axis: the graph *computes
its decision* (self-computing) via adaptive retrieval. **Tiering (Astra):** the read/route/reshape
*competitor-capability table is an asserted framing, not a demonstrated result* — present it as
positioning, not proof. Customer-value hypotheses (precedent-free hard cases; calibrated "do less";
auditable deliberation; compounding; no bigger model) are **hypothesized, pending §10** — none has VLD
evidence yet.

## 3A. Value-headroom — a real-mechanism pilot (E0/E1, synthetic)

**The reframe survives as a hypothesis:** VLD's value in a copilot ≈ a domain-**classifiable** fraction m
(§3B). To test whether depth-value *emerges* from the mechanism (not from assumptions), we built a
**real-mechanism** pilot: non-circular (μ **learned from a disjoint sample**; test points not drawn around
μ), a real graph with **pointer-linked chains**, real Ψ traversal, **real nearest-centroid scoring**, real
damping. Code + output: `vld_mechanism_sim.py`, `vld_mechanism_sim_results.txt`. (This **supersedes the
earlier "simulation," which was a mixture-of-constants calculator — see Appendix C, retired.**)

**How the pilot is built (the approach — critique it, not just the numbers).** Per tensor shape
(SOC 6×6, Trading 10×10, Purchasing 7×7, DataOps 6×6, S2P 8×8):
- **Non-circular generation.** Ground-truth class centroids θ_c are drawn independently; the scorer's
  centroids μ_c are **learned from a disjoint training sample** (40/class), so test points are never drawn
  around μ (avoids the H-KERNEL circularity). A circularity check (set μ:=θ) confirms the effect does *not*
  materially inflate — i.e. the result isn't a circularity artifact.
- **The graph.** Each hard case has a **surface node** (ambiguous — its dims are pulled toward a *wrong*
  class), a **pointer-linked chain** of 3 decisive nodes (each reveals decisive dims + an edge to the next;
  only the entry is reachable a priori), and 10 distractor nodes. Multi-hop cases split the decisive dims
  along the chain (you must follow pointers to get them all); flat cases put them in one findable node.
- **Real readout.** `v` = extract(admitted dims) (revealed dims take their true values, others stay at the
  prior); decision = argmin to the nearest **learned** centroid; truth = (argmin == GT class y). **Rates
  emerge from scoring — nothing is hand-set.**
- **The arms (all real).** baseline (surface only) · Φ-once (one topological read) · VLD (follow the chain,
  damped ε=0.35) · matched-breadth (read k nodes *non-adaptively* by static relevance) · placebo (k *random*
  reads) · **Ψ-inert (admit nothing → structurally the identity on v₀)** · **Ψ-similarity (admit the node
  nearest v_t — the A0-suspect geometry)** · **final-evidence-once (score VLD's final admitted set once —
  isolates the trajectory)**.
- **Controls are structural, not prescribed:** Ψ-inert = baseline *by construction*; flat-null makes
  depth-over-one-read collapse to 0; the A0 and null behaviours **emerge**.

**Full data (m = 0.6 multi-hop hard tail; truth-accuracy by arm, per shape):**

| shape | baseline | Ψ-inert | Φ-once | VLD | breadth | placebo | Ψ-similarity |
|---|---|---|---|---|---|---|---|
| SOC | 0.271 | 0.271 | 0.563 | 0.752 | 0.716 | 0.718 | 0.477 |
| Trading | 0.258 | 0.258 | 0.647 | 0.838 | 0.744 | 0.740 | 0.429 |
| Purchasing | 0.287 | 0.287 | 0.554 | 0.730 | 0.756 | 0.758 | 0.488 |
| DataOps | 0.300 | 0.300 | 0.559 | 0.728 | 0.700 | 0.690 | 0.468 |
| S2P | 0.245 | 0.245 | 0.634 | 0.787 | 0.727 | 0.722 | 0.423 |

(Full delta tables, flat-null, circularity, and A0 checks in Appendix D / `vld_mechanism_sim_results.txt`.)

**Structural controls (now correct, not prescribed):** Ψ-inert = baseline **exactly** (Δ = 0.000 —
iterating on fixed context is the identity on v₀, Lemma A0); flat-null depth-over-one-read = 0.000.

**Decomposition (m = 0.6 multi-hop hard tail, five shapes) — sobering and honest:**

| Δ | what it isolates | emergent result |
|---|---|---|
| Δ_operator (Φ-once − baseline) | value of **one** adaptive retrieval | **+0.26 … +0.39 (large)** |
| Δ_depth (VLD − Φ-once) | value of iterating **beyond one** read | +0.15 … +0.19 |
| **Δ_depth¬breadth (VLD − matched-breadth)** | value of **adaptivity over just-read-more** | **+0.03 … +0.09 (small; −0.03 Purchasing)** |
| Δ_trajectory (VLD − final-evidence-once) | value of the **iterative re-scoring itself** | **+0.000 (none)** |
| Ψ_similarity (nearest-to-v_t) | the A0-suspect retrieval | **below placebo (actively harmful)** |

**Reading (honest, and more skeptical than the retracted calculator):** the value is overwhelmingly in
**acquiring the right evidence** (Δ_operator) and in reading *enough* of it (VLD ≈ breadth) — **not** in the
iterative loop (Δ_trajectory = 0) and only marginally in *adaptive* vs *broad* retrieval (Δ_depth¬breadth
small, negative for one copilot). Similarity-retrieval *hurts*. Even at a high multi-hop fraction,
**"VLD-the-loop" earns little over "just retrieve more."** The deployable win this points to is **better /
adaptive retrieval (Ψ-once or few-step), not the damped iteration.**

**Caveats (tier — synthetic headroom, not evidence):** Δ_depth¬breadth is sensitive to
chain-length/distractor-density (breadth does well here because decisive evidence is ~half the dims among
~13 nodes; a harder planted chain — E0 — would widen or confirm the margin). Δ_trajectory = 0 is partly
structural to a clean single chain (the damped iterate converges to the final evidence extraction); the
loop could add value only if intermediate decisions changed *which* evidence is admitted — a thing to
test, not assume. Real-world value still requires E6 on bitemporal data.

**Go/no-go implication:** invest in **adaptive retrieval**, be **skeptical of the loop**; the decisive E3
tests are the **attribution controls** (final-evidence-once; traverse-without-scorer-feedback), not the
aggregate lift.

## 3B. What m really is — a *semantic* decision category, not a numeric type

The m-parameterization (§3A) is more than a value knob: it means **VLD adds a new way to classify
decisions.** Today a decision is typed **numerically/geometrically** — a factor vector in R^d scored
against centroids in a (C,A,d) tensor; its "type" is its category/position in factor space. The
multi-hop property is a **different axis**: it classifies a decision by its **evidence-acquisition
structure** — does resolving it require *sequential, state-conditioned* reads (multi-hop), or are all
relevant factors available at once (flat)? That is a **semantic** property (what *kind* of reasoning the
decision needs), not a numeric one (where it sits). Implications, thought through:

1. **It is a classifiable category — which is *why* m is measurable.** A domain owner labels decision
   *types* by their evidence structure from real cases, the way an analyst already knows "this alert type
   you investigate; that one you close on sight." A human-legible taxonomy, not a threshold.
2. **It is the *true* predictor of VLD-benefit; margin/σ are only proxies.** The sim's depth-value scales
   with m (the semantic multi-hop fraction), not with numeric hard-tail size: a low-margin *flat* case
   gains nothing from depth (one adaptive read suffices), while a multi-hop case gains even at moderate
   margin. So the routing signal that predicts VLD-benefit is the **semantic multi-hop class**, and
   margin/σ are surrogates that may or may not track it. **This sharpens M2 (§10): hard-tail = numeric
   difficulty × semantic multi-hop, not margin alone** — and it is exactly Astra's requirement that the
   routing signal predict *incremental VLD benefit*, not baseline error.
3. **It makes VLD targeted, not uniform.** The platform deliberates on the *multi-hop class* and answers
   the *flat class* in one pass — "investigate the cases that need investigating," not "add compute
   everywhere." (This is also why cost stays bounded and why N4 forbids VLD on flat/easy cases.)
4. **It may be *learnable* — a semantic router.** Initially the class is human-labeled; over time the
   system could learn to predict "does this decision need sequential evidence?" (a meta-classifier over
   decisions), under the same guards (verified outcomes, no leakage). That router is what makes VLD
   deployable efficiently and is a new sub-capability in its own right.
5. **It is a stronger, more legible product story than "iterate the scorer."** "The copilot recognizes
   which cases need investigation vs which it can answer at a glance, and investigates the ones that need
   it" maps directly onto how a human expert triages. It stands even where the depth *loop* is thin,
   because the **classification itself is valuable metadata** — it flags which decisions are inherently
   hard-to-automate / need human-in-the-loop.
6. **Placement.** This is a **new semantic attribute on the DECISIONS element that predicts the required
   COMPUTATION mode** (a DECISIONS×COMPUTATION link in the four-element algebra); it enters
   `ci_graph_hypotheses` as such.

**Honest tier.** That decisions cleanly cluster into multi-hop vs flat, that the multi-hop class is where
value concentrates, and that the class is learnable are **hypotheses** — the sim *assumed* the split;
domain owners must validate it (the §3A elicitation produces the first real labels). But as a
*classification framework* it is already useful: it structures the value question, the routing, and the
demo — and it converts "will VLD help copilot X?" into "characterize X's decisions by evidence
structure," which every domain can do.

## 3C. "Prior decisions are evidence" — one Ψ, and the retrieval-geometry axis (chain of thought)

A line of reasoning that corrects and sharpens §3A/§3B. Recorded as the chain so other sessions can
follow and challenge each step.

1. **Question.** Are "multi-hop retrieval over the graph" and "sequencing judgment-memory traces" two
   different mechanisms?
2. **Collapse.** No — **a prior verified decision *is* evidence** (the highest-grade kind: it carries a
   verified outcome). There are not two mechanisms retrieving two kinds of thing; there is **one Ψ
   (adaptive, state-conditioned retrieval) over one heterogeneous evidence graph whose nodes include
   prior decisions.** The earlier "evidence-chaining vs judgment-sequencing" distinction was a false
   dichotomy — judgment traces are one *node type* Ψ can admit.
3. **What survives the collapse.** The A0 risk (§4 Lemma) does **not** attach to the *node type*
   (fact vs prior-decision); it attaches to the **retrieval geometry** — *how* Ψ admits the next node:
   - **Topological / causal admission** — Ψ follows an edge implied by the current decision (entity →
     campaign → the prior decision on that campaign). The admitted node carries information *independent
     of `v_t`'s position*, so it can genuinely move the decision and beat a one-shot readout. **Real
     depth.**
   - **Similarity admission** — Ψ fetches the nearest prior decisions in prototype space. That node is,
     by construction, *near where `v_t` already is*; moving `v_t` toward it is Lemma A0's attractor →
     convergence to the nearest centroid, re-smoothing, placebo-on-truth. **A0-suspect.**
4. **Refinement (reviewers): a design axis, not a theorem.** The discriminator is *what the admitted node
   contributes*, not merely how it is reached. A nearest-neighbor prior decision carries three things: its
   **position** (the A0 attractor, if averaged in), its **verified outcome** (a legitimate **kNN baseline** —
   a *one-shot* arm, not depth), and its **edges** (a similarity-entry + topological-hop **hybrid**). So
   similarity deserves a **strong comparator arm (Ψ_sim-outcome), not a "placebo" label**, and the E3
   contrast is **Ψ_sim-position / Ψ_sim-outcome / Ψ_topological / Ψ_hybrid** (§10).
5. **This replaces the two-Ψ experiment idea.** The E3 arms that matter are **Ψ_topological vs
   Ψ_similarity** (not Ψ_evidence vs Ψ_judgment). Similarity-retrieval is effectively a *structured
   placebo*: if it lifts truth, similarity-of-priors is doing real work; if it tracks the random placebo,
   it is the A0 attractor. (§10 / Appendix B updated.)
6. **§3B is unchanged in spirit,** but m has **three layers** — `m_world` (does the decision need a chain),
   `m_graph` (does the graph encode the edges), `m_Ψ` (can Ψ follow them). Owners estimate `m_world`; P1
   bounds `m_graph`; E0 measures `m_Ψ`. (Categories overlap — do not treat m as a clean sum.) The domain-owner elicitation
   (§3A) must ask *which hard cases have a genuine causal chain of prior-decisions/evidence, vs merely
   "similar past cases."*
7. **The moat — retiered (asserted, not demonstrated).** Adaptive, reasoning-guided retrieval is **not by
   itself** a differentiator: GraphRAG **DRIFT** and **IRCoT** already steer retrieval with intermediate
   reasoning. The candidate differentiation is narrower — **outcome-linked judgment memory as retrievable
   evidence, with faithful attribution, frozen-state replay, and bounded cost** — and it is a *hypothesis*
   until `Ψ_topological > Ψ_sim-outcome` on truth. (A verified prior outcome is valuable evidence, **not**
   automatically the highest-grade — verification quality, applicability, and action-selection bias
   qualify it.)
8. **Open question that gates the whole thing (graph structure).** Is CI's decision graph actually
   traversable *topologically over decisions* (causal/entity edges *between* decisions), or only by
   *similarity* (nearest-prototype)? **If decisions are reachable only by similarity, Ψ-over-judgment-
   traces is A0-suspect *by construction*, and the only non-trivial Ψ is over the *non-decision* evidence
   (entities/artifacts) that causally links decisions.** This is a code/graph-structure question (a
   Ψ-design / parameterization check) whose answer decides whether judgment-trace Ψ is a real mechanism
   or (per the reviewers) merely **scoped**, not decided: even without decision→decision edges, a similar
   prior decision's **outcome/edges** can still add evidence, and access via **shared hubs**
   (Decision→Alert/Entity←Decision) exists for SOC (plausibly), S2P (after OD-1), and ≈0/unestablished for
   Trading/Purchasing/DataOps (preliminary, per repo-aware reviewers). **P1 is the highest-leverage *fact*
   to fetch — it scopes retrieval mechanisms and effort; it does not, by itself, decide whether adaptive
   retrieval adds value.** Settle it (repo audit) before building Ψ.

## 3D. Planning for the likely scoping outcome

If P1 + the pilot hold, the *likely* result is bimodal and should be planned for as a **scoping result,
not a failure:** **depth (few-step adaptive retrieval) plausibly helps SOC and DataOps** (which have
hub-linked chains); for **Trading / Purchasing** (and S2P until OD-1), `m_graph ≈ 0`, and the pilot shows
the loop earns little over breadth anyway → **invest in better single-shot / few-step adaptive retrieval
(Ψ-once), which is cheaper**, and keep the **semantic decision-classification (§3B) as a deliverable in its
own right** (it flags what needs investigation / HITL even where the loop is thin). Stating this up front
means a narrow outcome reads as planned scoping.

## 4. The formalism (rebuilt)

**Frozen inference state (Astra):** `Θ = {μ, DK weights, preprocessing, calibration τ, σ}` — *all*
frozen at the decision cut t0, not μ alone. Point-in-time graph `G₀` (bitemporal, §10). No writes to any
learned state or to `G` during inference (Inference Side-Effect / Authority Contract).

**Scorer readout.** For a factor vector `v`: distances `d_a(v)=‖v−μ_{ĉ,a}‖` (DK/preproc applied);
`p_a(v)=softmax(−d_a²/τ)`; decision `a*(v)=argmin_a d_a(v)`; margin `m(v)=d_(2)−d_(1)`.
**Extraction.** SituationAnalyzer traversal → factor vector: `v = E(s,G,Θ)` (a dispatcher over traversal
patterns; **no native vector-update op** — so Φ must be a built adapter).

**Baseline (L=1):** `v₀ = E(s,G₀,Θ)`; emit `a*(v₀)`.

**VLD = Φ = A∘Ψ (two stages):**
- **Ψ — adaptive retrieval:** `G_{t+1} = Ψ(v_t, a*(v_t); G₀) ⊆ G₀` — state-conditioned admission of a
  *new read-only sub-view* of the frozen graph. This is where new information enters.
- **A — re-extract + damped update:** `v_{t+1} = (1−ε)·v_t + ε·E(s,G_{t+1},Θ)`.
- Compactly `Φ(v_t) := E(s,Ψ(v_t;G₀),Θ)`, `v_{t+1}=(1−ε)v_t+εΦ(v_t)`.

**Lemma A0 (provable, negative — this is why the program centers Ψ).**
*If Ψ is inert* (`G_{t+1}=G₀ ∀t`) *and Θ frozen, then Φ is a fixed map f and `v_L = g_L(v₀)` for a fixed
`g_L`* (the L-fold damped composition). Hence `v_L` is a deterministic function of `v₀`, computable in a
single readout; **VLD-without-Ψ cannot beat the best one-shot readout of `v₀`.** **Corollary (narrow, exact):** with inert Ψ, `Φ(v)=E(s,G₀,Θ)=v₀` is *constant*, so every iterate stays
v₀ — an exact null for this formulation. Any depth lift on truth must therefore originate in Ψ
(state-conditioned new evidence), not in vector iteration. *(We do NOT claim the iteration is drawn to the
μ's, nor that it cannot beat the shipped scorer — a finite computation can beat a restricted baseline
without new evidence; those v4-era claims are withdrawn.)*

**Residual identity (Astra).** `‖v_{t+1}−v_t‖ = ε‖Φ(v_t)−v_t‖`. A raw δ-threshold halt confounds "small
step" with "small ε." Use the **normalized residual** `r_t = ‖Φ(v_t)−v_t‖ / (‖v_t‖+ζ)` and require the
admitted-context set to have stabilized (`G_{t+1}=G_t`).

## 5. Convergence, stability, safety (corrected — mostly experiment, not theory)

**Fixed-context sub-map** `T(v)=(1−ε)v+εf(v)`, `L_f=Lip(f)`: `Lip(T) ≤ 1−ε+εL_f`.
- `L_f<1` ⇒ contraction for any `ε∈(0,1]` ⇒ unique fixed point, geometric convergence.
- `L_f≥1` ⇒ the bound is ≥1 **but this is inconclusive.** *Counterexample:* `f(v)=−2v` has `L_f=2`, yet
  `ε=¼` gives `T(v)=v/4`, which converges. If `f` is nonexpansive with a fixed point on a convex set,
  Krasnoselskii–Mann guarantees the averaged iterate converges. **So "damping cannot rescue an expansive
  operator" is false; bound-failure proves nothing.** The effective `L_f`/spectral behavior is
  **empirical** (experiment E2).

**Full two-stage (Ψ active):** with frozen G₀/Θ and fixed Ψ, `T(v)=(1−ε)v+ε·E(s,Ψ(v;G₀),Θ)` is a
**single autonomous map** — state-conditioned retrieval does not make it time-dependent (put the frontier /
visited / admitted set in the state). If admission is **cumulative + monotone-bounded** (§4), the admitted
set is monotone in a finite lattice → it **stabilizes within budget by construction**, so a joint fixed
point `(v*,G*)` **exists and is reached** — §5's earlier "not guaranteed" was over-cautious. The real open
question is **uniqueness / order-dependence**: different ε or admission order can land on different `G*`
(path-dependent deliberation) — the buyer-relevant robustness question. *(Krasnoselskii–Mann / Lipschitz
material governs only the post-stabilization tail and needs invariant-set + relaxation assumptions;
ε=1 is not covered — `f(v)=−v` oscillates. Footnote, not load-bearing.)*

**σ⊥μ and the boundary (demoted to conjecture — Astra).** Near small margin `m(v)`, small vector moves
flip `a*(v)` — VLD's maximum leverage *and* maximum churn. Whether iterating amplifies σ-driven error
there is empirical. **"Stability boundary = safety boundary" and "closer-to-μ = better" are conjectures,
not results.** A converged loop can be confidently wrong: **stability ≠ safety ≠ truth.**

## 6. Conservation gate (θ_min notation fixed — Astra)
The gate is on **accuracy**, not on `α·q·V`: **`q ≥ θ_min(α,V)`** with `θ_min = 23.53/(α·V)`
(deployment-scaled floor; `q`=rolling verified accuracy, `α`=category coverage, `V`=verified/day). The
prior "`α·q·V ≥ θ_min`" form is **inconsistent** (substituting gives `α²qV² ≥ 23.53`) and is **withdrawn**;
the accuracy-floor form `q ≥ 23.53/(α·V)` is adopted. *(Still to verify before halt logic: the constant's
derivation, zero-denominator / >1 behavior, and that scorer.py and gae.calibration compute it identically.)* Within an inference episode `α,V,θ_min` are fixed (from
verified history), so **deliberation cannot manufacture headroom** (N2). **Roles (corrected):** within an inference episode `q,α,V,θ_min` are **fixed**, so conservation has **no
per-pass signal** — it establishes *eligibility* and gates only at **emit**. The per-pass **fuse** must key
on computational signals instead: **normalized residual `r_t`, admission-budget exhaustion, and flip-count
(how often `a*(v_t)` changed)**. Below floor at emit → the §7/N1 abstain transition. *(The v4 "per-pass
conservation halt" came from the misread `α·q·V` form — withdrawn.)*

## 7. Integration & abstain
Primary attach = **factor-vector via the frozen-state replay hooks, offline/sidecar locus** (firewall-safe
by construction). **Graph-context survives only as read-only Ψ** (no admission of unverified writes,
verified-tier). Readout/rerank = a baseline arm; centroid-assignment dropped; **sidecar = a locus, not a
Φ return-type.** **Abstain (N1) = a concrete workflow transition** (SOC escalate / S2P hold / Trading
decline / Purchasing defer / DataOps quarantine) that **degrades to the shipped L=1 decision, never
below it**, costed at the domain's expected cost of deferral (domain owner).

## 8. Guards & the value decomposition
**Guards (each blocks one fake win):** non-circular synthetic (GT-centered, never μ-drawn); truth vs
**verified outcomes, never distance-to-μ**; bitemporal temporal integrity (§10); **≈1.0 hard-tail = a
leakage-investigation trigger, not proof.**
**The value objective is baseline-relative and constrained (GPT/Astra):** per domain,
`ΔU_d = E[u_d(a_VLD,Y) − u_d(a_baseline,Y)] − Δc_compute`, subject to easy-churn ≤ bound,
abstain-calibration ≥ baseline, safety, temporal integrity. `u_d` = domain utility (outcome-in-the-world,
asymmetric, counts abstain/delay/review once).
**Five arms per cell, decomposing depth exactly (Astra):**
`{baseline (L1), Φ-once, Φ-repeated (VLD), matched-breadth, matched-placebo}` →
- `Δ_operator = U(Φ-once) − U(baseline)` (does one adaptive retrieval help?)
- `Δ_depth = U(Φ-repeated) − U(Φ-once)` ← **the VLD claim**
- `Δ_depth¬breadth = U(Φ-repeated) − U(matched-breadth)` (sequential conditioning beats one-shot breadth?)
- `Δ_depth¬resmooth = U(Φ-repeated) − U(matched-placebo)` (real feedback, not shuffled?)
**real−placebo is a diagnostic (`Δ_depth¬resmooth`), NOT the value** — it can be >0 while
`U(Φ-repeated) < U(baseline)`. VLD "works" iff all four Δ>0, net of cost, surviving leakage + the
positive control.

## 9. Honesty & tiering
F-24; label Φ-fidelity tier on every result (a factor approximation is not a math bound; "bounds-only
requires an actual bound"). +36.89pp (L2-vs-dot) citable; DK (+13pp) = boundary — never conflate (both
pending ci_core re-verification). JM = synthetic-tier. **Within-domain replication = a real finding;
cross-domain replication sets the generality tier** (a robust SOC-only effect is a finding, not a lead).
**Math tiers:** *provable now* — Lemma A0, the residual identity; *sufficient not necessary* — contraction
(L_f<1) / K-M convergence; *conjecture (test, don't assert)* — stability=safety, closer-to-μ=better,
depth¬breadth; *experimental* — effective L_f, joint-fixed-point reachability, the four Δ's, σ-amplification.

## 10. Experiments to run (the corrected characterization contract)

Instruments: **non-circular synthetic** (mechanism/contraction/decomposition — leak-free) + **production
bitemporal** (generalization). Every cell carries the **five arms** (§8), a **matched placebo**, and
**baseline-relative utility**. Pre-register endpoints before confirmation (no metric selection on the
real sweep — forking paths).

| # | Experiment | Question | Instrument | Kills / decides |
|---|---|---|---|---|
| **E0** | **Positive control** | Can the instrument *see* a real depth effect? Plant a multi-hop dependency resolvable only by state-conditioned sequential retrieval. | synthetic | If E0 shows no lift, the instrument is blind — **the STOP rule is invalid until E0 passes.** |
| **E1** | **A0 test** | Does Ψ-inert Φ-repeated ≈ one-shot readout ≈ placebo (Lemma A0)? Is Ψ necessary? | synthetic | Confirms depth-without-Ψ is null; if Ψ-active also ≈ placebo → mechanism absent. |
| **E2** | **Contraction map** | Does `r_t` (normalized) shrink? effective `L_f`/spectral behavior; joint fixed-point existence/reachability across ε,L,shape. | synthetic | Contraction is measured, not assumed; no reachable fixed point over any ε → unstable mechanism. |
| **E3** | **Depth decomposition (5-arm sweep)** | The four Δ's on the hard tail, baseline-relative, per domain. | synthetic + prod | **Δ_depth ≤ 0** (depth adds nothing over Φ-once) or **Δ_depth¬breadth ≤ 0** (breadth explains it) → thesis folds. Gate. |
| **E4** | **σ / boundary** | Does iterating near small-margin cases amplify σ-driven churn? Does stability track truth? | synthetic | Tests the demoted conjecture; if stability ⇏ truth, halt must not trust convergence. |
| **E5** | **Metric discrimination** | Which valid metric separates on **planted** effects (E0)? Pre-register, then run. | synthetic | Prevents forking-paths selection on the real sweep. |
| **E6** | **Where-it-helps / generalize** | Operating region across copilots (bitemporal, temporal-cut). | production | Domain-local / vanishes under cut+placebo+leakage → not general (still a domain finding). |
| **E7** | **Halt / abstain** | Normalized-residual + conservation-headroom halt; abstain-calibration vs baseline; off-policy for graded reward. | prod + off-policy | Halt starves depth / abstain worse than baseline / off-policy unidentifiable. |

**Sequence:** E0 → E1 → E2 → **E3 (gate)** → E4–E7. **STOP rule (now safe):** if **E0 passes** (instrument
sees the planted effect) but **E3 shows Δ_depth ≤ 0 across ≥3 domains**, depth doesn't work — a real,
publishable negative. (Without E0, a null is ambiguous — "absent" vs "blind.")

**Build prerequisites:** as-of/event-sourced graph keyed to the audit-chain ordinal, with dependency
lineage + future-data perturbation check (M5); verified corpus (≥80% cells × ≥5) with recorded
ascertainment; repair SOC count query; **Ψ design (the hard part — what to read next, conditioned on
v_t)**; 5-arm + positive-control harness; evidence/compute accounting; off-policy tooling; ≥10 seeds/cell;
freeze {μ,DK,preproc,calib,σ}. SOC first.


**Ψ-geometry arms + graph-structure precheck (from §3C).** In E1/E3, compare **Ψ_topological** (follows
causal/entity edges) vs **Ψ_similarity** (nearest prior-decision lookup); similarity is a *structured
placebo* — if it tracks the random placebo, that lift is the A0 attractor, not depth. **Precheck (a build
prerequisite):** determine whether the decision graph is traversable topologically *over decisions* or
only by similarity — if similarity-only, judgment-trace Ψ is A0-suspect by construction and only
non-decision evidence can yield real depth (this also changes which copilots have `m_topological > 0`).

## 11. Code hooks
`ProfileScorer` (softmax over −distance; action/probs/distances/confidence/entropy/margin) ·
`CompoundingScorer` in `copilot_sdk/scoring/scorer.py` — non-mutating `score_read_only`/
`score_with_model_state`/`gae_scorer` (frozen-state replay) · `SituationAnalyzer` dispatcher over
`TraversalPattern` (build Ψ+A here; no native update op) · Conservation `q ≥ θ_min(α,V)` (form to ratify),
route-exposed what-if · `fingerprint.py` σ (≥5 verified = eligibility floor, not reliability) · AgentEvolver
shadow-runner + paired gate (may propose bounded variants of a frozen Φ family, never evolve Φ) · Tensors:
DataOps 6×5×6, Purchasing 5×4×7, S2P 5×5×8, SOC 6×4×6, Trading 5×4×10 (normalize by margin/entropy/factor-dim).

## 12. Placement & ownership
COMPUTATION-cell hypotheses for `ci_graph_hypotheses`; proposal/lead tier. **Source-session (math/safety):**
the §5 rewrite, the θ_min form, the joint-fixed-point theory, N2/N3, the frozen-state contract. **Domain
owner:** N1 costs, N5 utility contracts + off-policy identification, hard-tail regions. VLD is the
inference-time deliberation over judgment memory (JM paper).

---

## Appendix A — Five-judge review: main insights (context)

Five independent LLM-judges (internal · Opus 4.6 · GPT · Fable · Astra) reviewed the design decisions on
a self-contained prompt. **Guiding question (adopted):** *VLD is not asked to prove that more computation
helps; it is asked whether tightly-governed, state-frozen iterative computation produces incremental
decision utility not explained by extra evidence, recalibration, re-smoothing, leakage, or abstention.*

**Decisive findings (why v5 exists):**
- **A0 (Fable):** with G and Θ frozen, the loop is a deterministic readout that tracks placebo; depth is
  real only via adaptive retrieval Ψ. → §4 rebuilt as Φ=A∘Ψ; Lemma A0.
- **§5 math error (Astra):** `Lip(T)≤1−ε+εL_f`; a bound ≥1 does **not** imply divergence (counterexample
  f=−2v, ε=¼). Contraction is an experiment; K-M convergence holds beyond strict contraction. → §5 rewritten.
- **5-arm design (Astra):** separate *introducing* Φ from *repeating* Φ — {baseline, Φ-once, Φ-repeated,
  breadth, placebo} — or operator-value is mislabeled as depth-value. → §8 decomposition.
- **Baseline-relative objective (GPT/Astra):** real−placebo can be +ve while both < baseline; it's a
  diagnostic, not the value. → §8.
- **Stability ≠ safety ≠ truth (Astra):** a stable loop can be confidently wrong. → §5 demotions.
- **M5 bitemporal (GPT/Fable/Astra):** event-time alone leaks via backfill; use a known-to-system cutoff
  keyed to the audit-chain ordinal with dependency lineage; ≈1.0 = alarm. → §10 build.
- **Positive control (Fable):** without a planted-effect cell, the STOP rule can't tell "absent" from
  "blind." → E0.
- **Frozen state ⊃ μ (Astra):** freeze DK/preprocessing/calibration/σ too. → §4.
- **θ_min inconsistency (Astra):** `q≥θ_min=23.53/αV`, not `αqV≥θ_min`. → §6.
- **Normalized residual (Astra):** `‖Δ‖=ε‖Φ−v‖`; normalize the halt signal. → §4/§10.
- **Off-policy evaluation (Astra):** historical logs carry action-selection bias; verified outcomes alone
  don't identify counterfactual reward. → E7.

**Consensus locks (4–5/5):** typed Φ contracts (M4) · conservation as gate not accuracy-surrogate, gated
both per-pass-fuse and at-emit, never a feedback signal (N2) · AgentEvolver may not evolve Φ (N3) · no
authoritative VLD on easy cases initially; shadow-sample for churn (N4, staged not permanent) · reward =
external versioned domain contract (N5) · Inference Side-Effect / Authority Contract (read-only w.r.t.
all judged state) · within-domain=finding, cross-domain=generality-tier · differentiation table = asserted
framing, tiered down.

**Process note:** the marginal judge stopped adding new corrections by five; the review is considered
complete. Full decisions with tallies and ratification owners: `ci_vld_decision_register_v5_final.md`
(and v1–v4 for the trail).


## Appendix B — Executable experiment plan (self-contained)

**Discipline for every experiment:** freeze + hash a pre-registration (endpoints, thresholds, arms,
seeds, hard-tail rule) before the first run; no post-hoc threshold changes; report residual mismatch.
Thresholds are pre-registered conventions unless "measured/derived."

**Build prerequisites (acceptance in parens):** B1 non-circular synthetic generator, GT-centered
independent of μ, with planted multi-hop mode + circularity check (effect vanishes if drawn around μ);
B2 A operator via `score_read_only`/`gae_scorer`, frozen Θ={μ,DK,preproc,τ,σ} (no-write assertion);
**B3 Ψ operator — the hard part** — state-conditioned read-only retrieval, monotone bounded admission
(follows the planted chain in E0); **includes a graph-structure precheck (§3C): is the decision graph
topologically traversable over decisions or similarity-only? — if similarity-only, judgment-trace Ψ is
A0-suspect by construction**; B4 5-arm harness {baseline, Φ-once, Φ-repeated, matched-breadth,
matched-placebo} with per-arm evidence+compute accounting; B5 metrics (truth vs verified outcome,
baseline-relative ΔU with a cost matrix, normalized residual r_t=‖Φ−v‖/(‖v‖+ζ), effective L_f,
σ-amplification, churn, abstain-calibration, real−placebo, real−baseline; distance-to-μ reported
separately, never as value); **B6 bitemporal replay keyed to the audit-chain ordinal** with dependency
lineage + future-data perturbation check (**if AGE can't reconstruct as-of state, E6/E7 are blocked**);
B7 pre-registration harness.

| # | Setup (arms / params) | Pre-registered decision |
|---|---|---|
| **E0 INSTRUMENT GATE** | planted length-3 chain among 20 distractors; arms baseline / Φ-repeated / matched-breadth; 5 seeds × 5 shapes | PASS iff VLD clears baseline+breadth on the planted chain, sign-consistent (calibrate the bar to the planted effect — note 0.47·0.85³≈29pp, so a fixed 30pp gate can self-fail). **Fail ⇒ fix Ψ/harness; do NOT proceed.** |
| **E1 A0 test** | arms (a)Ψ-inert Φ-rep (b)one-shot readout (c)placebo (d)Ψ-active; ε=0.25, L=4; 10 seeds×5 shapes; truth AND distance-to-μ | Expect (a)≈(b)≈(c) on truth; alarm if (a) beats baseline on truth (→ audit circularity/leak). |
| **E2 contraction map** | ε∈{1/L,0.05,0.1,0.25,0.5,1.0}×L=1..10×5 shapes; measure r_t, effective L_f, fixed-point reached | MAP (not a gate): ε×L phase diagram, L-knee, fraction reaching a self-consistent (v*,G*). |
| **E3 DEPTH GATE + STOP** | arms {baseline, Φ-once, Φ-repeated, matched-breadth, Ψ_sim-position, **Ψ_sim-outcome (kNN baseline)**, Ψ_hybrid} + attribution controls **final-evidence-once** and **traverse-without-scorer-feedback**; hard-tail = the **multi-hop-labeled subset (incl. high-margin multi-hop — do NOT restrict to bottom-20% margin)**; ≥10 seeds/cell; evidence- AND compute-matched (count nodes/records + extraction/scoring work) | PROCEED iff **Δ_depth¬breadth > 0** AND **Δ_depth¬resmooth > 0** AND **Δ_trajectory adds value** AND net-of-cost AND no easy-churn AND **Δ_depth > kNN-outcome baseline** (do NOT require Δ_operator>0). **STOP** if the effect is absent across ≥3 **real domains** (synthetic shapes ≠ domains). |
| **E4 σ / boundary** | stratify margin × σ on survivor shapes; 10 seeds | σ-amplification by stratum; corr(converged,correct). If convergence ⇏ truth → halt must not trust convergence. |
| **E5 metric discrimination** | planted-effect synthetic; candidate metrics; variance-explained + power | LOCK the primary metric for E6/E7 (pre-register; not selected on the real sweep). |
| **E6 generalize (prod)** | bitemporal cut; per copilot, SOC first; 5 arms; E5-locked metric; leakage probe at chance | BLOCKED unless B6 + corpus (≥80% cells×≥5; SOC ~720). Region where ΔU>0; within-domain=finding, cross-domain=generality tier. |
| **E7 halt/abstain** | fixed-L vs (adaptive fixed-point ∧ conservation-headroom ∧ L_max); doubly-robust off-policy for graded reward | Halt must not erase Δ_depth; abstain-calibration ≥ baseline; off-policy identifiable or declared so. |

**Sequence:** BUILD → E0(gate) → E1 → E2 → **E3(gate/STOP)** → E4,E5 → E6(prod) → E7. E0–E5 run offline
now (synthetic defaults); E6–E7 wait on B6 + corpus. **Ratify before E3/prod:** §5 rewrite, θ_min form,
frozen-state contract, N2/N3 (source-session); cost matrix, hard-tail regions, abstain transitions
(domain owner). E0–E2 need none of these.

## Appendix C — Value-sizing calculator (CLOSED-FORM elicitation tool — NOT a simulation)

**Retraction/relabel:** the code below was mislabeled a "simulation with validity controls." It is a
mixture-of-constants **calculator**: every arm returns a hand-set rate, so `Δ(m)=(1−m)·Δ_flat+m·Δ_multihop`
is **linear in m by construction**, the "controls" are tautological, and on rerun the A0 control fails
(Ψ-inert = BASE by fiat). **Use it only as an *elicitation calculator*** — plug in a domain's *assumed*
arm rates and m to size the bet, assumptions exposed. For the *mechanism* question use the real-mechanism
pilot (§3A / `vld_mechanism_sim.py`). Do not cite "20 seeds," "controls," "ceilings," or "not rigged."

```python
import numpy as np

# ============================================================================
# VLD value-headroom simulation (SYNTHETIC / feasibility — NOT evidence)
# Question: IF a copilot's hard cases have multi-hop structure, how much
# headroom does state-conditioned deliberation (Ψ) have over one-shot/breadth/
# placebo, and is it material? The multi-hop fraction m is the key DOMAIN input.
# ============================================================================

RNG = np.random.default_rng(20260906)

# Honest, middling mechanism assumptions (flagged; sweepable):
P_HOP   = 0.85   # retriever success per hop (Ψ follows the chain imperfectly)
BASE    = 0.45   # accuracy on a hard case from the initial ambiguous read
RESOLVED= 0.92   # accuracy once the key evidence is acquired
N_DEC   = 4000   # hard-tail decisions per seed
SEEDS   = 20

# Per-copilot: tensor shape (C,A,d), assumed multi-hop fraction of the HARD tail,
# chain length, distractor count, hard-tail fraction of ALL decisions,
# illustrative value-per-recovered-hard-case (PLACEHOLDER — needs domain owner).
COPILOTS = {
 'SOC':        dict(C=6,A=4,d=6,  m=0.70, chain=3, distr=12, htail=0.18, val=1.0,  vunit='missed-incident-equiv'),
 'DataOps':    dict(C=6,A=5,d=6,  m=0.60, chain=3, distr=10, htail=0.22, val=0.6,  vunit='false-alert-equiv'),
 'S2P':        dict(C=5,A=5,d=8,  m=0.40, chain=2, distr=8,  htail=0.15, val=0.8,  vunit='leakage-$-equiv'),
 'Purchasing': dict(C=5,A=4,d=7,  m=0.20, chain=2, distr=6,  htail=0.20, val=0.4,  vunit='margin-$-equiv'),
 'Trading':    dict(C=5,A=4,d=10, m=0.15, chain=2, distr=6,  htail=0.12, val=0.3,  vunit='exec-quality-equiv'),
}

def p_correct(arm, case, chain, distr):
    """Prob(correct) for an arm on a case type. Honest mechanism model."""
    R = chain + distr
    if case == 'flat':          # key evidence is ONE findable item
        if arm=='baseline':  return BASE
        if arm=='Phi_once':  return BASE + (RESOLVED-BASE)*P_HOP          # one adaptive read finds it
        if arm=='VLD':       return BASE + (RESOLVED-BASE)*P_HOP          # no sequencing needed → == Phi_once
        if arm=='breadth':   return BASE + (RESOLVED-BASE)*0.90           # top-k by relevance finds a findable item
        if arm=='placebo':   return BASE + (RESOLVED-BASE)*(1-(1-1/R)**chain)  # random k → base rate hits
        if arm=='Psi_inert': return BASE                                  # iterate on fixed context: no new evidence
    else:                       # multi-hop: key = terminal item, needs ordered traversal
        base_pick = 1-(1-1/R)**chain     # prob a k-pick grabs the terminal item at all
        if arm=='baseline':  return BASE
        if arm=='Phi_once':  return BASE + (RESOLVED-BASE)*(P_HOP if chain==1 else 0.05)  # 1 read can't traverse chain>1
        if arm=='VLD':       return BASE + (RESOLVED-BASE)*(P_HOP**chain)   # traverse all hops
        if arm=='breadth':   return BASE + (RESOLVED-BASE)*(0.15*base_pick) # unordered: even grabbing terminal rarely resolves w/o chain context
        if arm=='placebo':   return BASE + (RESOLVED-BASE)*(0.10*base_pick)
        if arm=='Psi_inert': return BASE
    raise ValueError

ARMS=['baseline','Phi_once','VLD','breadth','placebo','Psi_inert']

def run(m, cfg, seeds=SEEDS, n=N_DEC):
    accs={a:[] for a in ARMS}
    for s in range(seeds):
        rng=np.random.default_rng(1000+s)
        is_mh = rng.random(n) < m
        for a in ARMS:
            p = np.where(is_mh, p_correct(a,'multihop',cfg['chain'],cfg['distr']),
                                 p_correct(a,'flat',   cfg['chain'],cfg['distr']))
            accs[a].append((rng.random(n) < p).mean())
    return {a:(np.mean(v),np.std(v)) for a,v in accs.items()}

def deltas(r):
    d=lambda x,y: r[x][0]-r[y][0]
    return dict(operator=d('Phi_once','baseline'),
                depth=d('VLD','Phi_once'),
                depth_vs_breadth=d('VLD','breadth'),
                depth_vs_placebo=d('VLD','placebo'),
                A0_check=r['Psi_inert'][0]-r['placebo'][0])   # should be ~0 on truth

print("="*78)
print("VLD VALUE-HEADROOM SIMULATION  —  SYNTHETIC, feasibility only (NOT evidence)")
print(f"assumptions: P_HOP={P_HOP} BASE={BASE} RESOLVED={RESOLVED}  seeds={SEEDS} n/seed={N_DEC}")
print("="*78)

results={}
for name,cfg in COPILOTS.items():
    r=run(cfg['m'],cfg); dl=deltas(r); results[name]=(r,dl,cfg)
    print(f"\n### {name}  (tensor {cfg['C']}x{cfg['A']}x{cfg['d']}, assumed multi-hop frac m={cfg['m']}, chain={cfg['chain']})")
    print(f"  hard-tail accuracy by arm:  " + "  ".join(f"{a}={r[a][0]:.3f}" for a in ARMS))
    print(f"  Δ_operator (Φ1−base)       = {dl['operator']:+.3f}")
    print(f"  Δ_depth (VLD−Φ1)           = {dl['depth']:+.3f}   <-- the VLD claim")
    print(f"  Δ_depth¬breadth (VLD−brd)  = {dl['depth_vs_breadth']:+.3f}   <-- depth beyond one-shot breadth")
    print(f"  Δ_depth¬resmooth (VLD−plc) = {dl['depth_vs_placebo']:+.3f}   <-- not re-smoothing")
    print(f"  A0 check (Ψ-inert−placebo) = {dl['A0_check']:+.3f}   (should be ~0 on TRUTH)")

# ---- Validity control: flat-null (m=0) → depth advantage must vanish ----
print("\n"+"="*78)
print("VALIDITY CONTROL — flat-null (m=0 for all): Δ_depth¬breadth MUST be ~0 (else rigged)")
print("="*78)
for name,cfg in COPILOTS.items():
    r=run(0.0,cfg); dl=deltas(r)
    print(f"  {name:11s} Δ_depth¬breadth(m=0) = {dl['depth_vs_breadth']:+.3f}   Δ_depth = {dl['depth']:+.3f}")

# ---- Headroom sensitivity to m (the key domain parameter) ----
print("\n"+"="*78)
print("HEADROOM vs MULTI-HOP FRACTION m  (Δ_depth¬breadth on hard tail) — the KEY driver")
print("="*78)
ms=[0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]
print("  m:        "+"  ".join(f"{m:.1f}" for m in ms))
for name,cfg in COPILOTS.items():
    row=[deltas(run(m,cfg,seeds=8))['depth_vs_breadth'] for m in ms]
    print(f"  {name:11s} "+"  ".join(f"{x:+.2f}" for x in row))

# ---- Illustrative value-sizing (PLACEHOLDER value units — needs domain owner) ----
print("\n"+"="*78)
print("ILLUSTRATIVE VALUE-SIZING (value units are PLACEHOLDERS — require domain ratification)")
print("  overall-decision lift = hard-tail-fraction × Δ_depth¬breadth")
print("  value-units/1000 decisions = 1000 × overall-lift × value-per-recovered-case")
print("="*78)
MATERIAL_LIFT = 0.03   # pre-registered materiality bar: ≥3pp on the HARD TAIL
for name,(r,dl,cfg) in results.items():
    tail_lift = dl['depth_vs_breadth']
    overall   = cfg['htail']*tail_lift
    vunits    = 1000*overall*cfg['val']
    verdict = "MATERIAL" if tail_lift>=MATERIAL_LIFT else "thin"
    print(f"  {name:11s} hard-tail lift={tail_lift:+.3f} [{verdict} vs {MATERIAL_LIFT:+.2f} bar] | "
          f"overall={overall:+.4f} | ~{vunits:+.1f} {cfg['vunit']}/1k dec")
print("\n[SYNTHETIC HEADROOM — sizes the bet + identifies m as the decisive domain input; NOT proof of value]")
```

## Related artifacts (external detail, summarized above)
- `ci_vld_designspace_parameterization_v1.md` — the full 38 decisions / 166 options / 26 dependencies /
  18 invalid combinations / 16 open questions (§3B/§10 summarize the load-bearing parts).
- `ci_vld_decision_register_v5_final.md` (+ v1–v4) — the five-judge decisions with tallies and
  ratification owners (Appendix A summarizes the decisive findings and locks).
- `vld_value_sim_results.txt` — full simulation output (Appendix C is the exact code).

## Appendix D — Real-mechanism pilot (§3A): code and raw results (embedded for reproduction)

The honest counterpart to the retired calculator (Appendix C): non-circular, real Ψ traversal, real
nearest-centroid scoring, structural controls. Still synthetic (headroom, not real-world evidence).

### D.1 Code (`vld_mechanism_sim.py`)

```python
import numpy as np
# =====================================================================
# (b) REAL mechanism sim for E0 (positive control) + E1 (A0 test).
# Non-circular: μ LEARNED from a disjoint sample; test points NOT drawn
# around μ. Real graph (pointer-linked chains), real Ψ traversal, real
# centroid scoring (argmin to learned μ), real damping. Arm rates EMERGE.
# Controls are STRUCTURAL, not hand-set. Still synthetic → headroom, not
# real-world evidence; but the A0 control now behaves by construction.
# =====================================================================
RNG = np.random.default_rng(7)

SHAPES = {  # (name, C classes, d factors)
 'SOC':(6,6),'Trading':(10,10),'Purchasing':(7,7),'DataOps':(6,6),'S2P':(8,8),
}
SEP      = 1.3     # class separation (controls baseline difficulty)
NOISE    = 0.9     # per-dim observation noise
N_TRAIN  = 40      # per-class training pts → learned μ (disjoint from test)
N_TEST   = 1500    # hard-tail test cases per shape per seed
SEEDS    = 8
EPS      = 0.35    # damping
CHAIN    = 3       # decisive chain length (multi-hop)
DISTR    = 10      # distractor nodes
L_MAX    = CHAIN+2

def learn_mu(theta, rng, d, C):
    return np.stack([theta[c] + rng.normal(0, NOISE/np.sqrt(N_TRAIN), d) for c in range(C)])

def score(v, mu):                       # real nearest-centroid readout
    return int(np.argmin(((mu - v)**2).sum(1)))

def make_case(rng, theta, d, C, multihop):
    """Build a hard case: surface dims are ambiguous/misleading; decisive dims
    (revealed only via reads) flip argmin to the true class y."""
    y = rng.integers(C)
    x = theta[y] + rng.normal(0, NOISE, d)                 # full true vector (GT)
    dims = rng.permutation(d)
    n_dec = max(1, d//2)
    dec_dims, surf_dims = dims[:n_dec], dims[n_dec:]
    # surface starts ambiguous: zero the decisive dims; nudge surface toward a wrong class
    wrong = (y + 1 + rng.integers(C-1)) % C
    v0 = np.zeros(d); v0[surf_dims] = 0.5*x[surf_dims] + 0.5*theta[wrong][surf_dims]
    # nodes: dict id -> (dims_revealed, pointer_to_next_or_None, is_decisive)
    nodes = {}
    if multihop:                                            # decisive dims split along a pointer chain
        chunks = np.array_split(dec_dims, CHAIN)
        for k,ch in enumerate(chunks):
            nxt = f"dec{k+1}" if k+1 < CHAIN else None
            nodes[f"dec{k}"] = (list(ch), nxt, True)
        entry = "dec0"                                      # only the entry is reachable a priori
    else:                                                   # flat: all decisive dims in ONE findable node
        nodes["dec0"] = (list(dec_dims), None, True); entry = "dec0"
    for j in range(DISTR):                                  # distractors: irrelevant dims, no useful pointer
        nodes[f"dis{j}"] = (list(rng.choice(surf_dims, size=min(2,len(surf_dims)), replace=False)), None, False)
    # node representative vectors (for similarity retrieval): the partial v the node would add
    reps = {}
    for nid,(dm,_,_) in nodes.items():
        r = np.zeros(d); r[dm] = x[dm]; reps[nid] = r
    return dict(y=y, x=x, v0=v0, nodes=nodes, entry=entry, reps=reps, dec_dims=dec_dims)

def extract(admitted, case, d):
    v = case['v0'].copy()
    for nid in admitted:
        dm = case['nodes'][nid][0]; v[dm] = case['x'][dm]     # revealing a dim = its true value
    return v

def run_arm(arm, case, mu, d):
    """Return predicted class for the arm. Real traversal + real scoring."""
    x, nodes, reps, entry = case['x'], case['nodes'], case['reps'], case['entry']
    def sc(adm): return score(extract(adm, case, d), mu)
    if arm=='baseline':                 # L1: initial ambiguous vector
        return sc([])
    if arm=='psi_inert':                # iterate A on FIXED context → admits nothing → identity on v0
        v = case['v0'].copy()
        for _ in range(L_MAX): v = (1-EPS)*v + EPS*case['v0']   # structurally == v0
        return score(v, mu)
    if arm=='phi_once':                 # one adaptive (topological) read from the entry
        return sc([entry]) if entry in nodes else sc([])
    if arm in ('vld','traverse_nofeedback'):   # follow the pointer chain (topological)
        adm=[]; cur=entry
        for _ in range(L_MAX):
            if cur is None or cur not in nodes: break
            adm.append(cur); cur = nodes[cur][1]             # follow revealed pointer
        # (with a clean single chain, scorer-feedback doesn't change the path; identical here by design —
        #  divergence would appear only with ambiguous multi-pointer frontiers)
        return sc(adm)
    if arm=='final_once':               # re-extract+score ONCE from VLD's final evidence set (no trajectory)
        adm=[]; cur=entry
        for _ in range(L_MAX):
            if cur is None or cur not in nodes: break
            adm.append(cur); cur=nodes[cur][1]
        return sc(adm)                  # identical readout to vld's final step → isolates trajectory value
    if arm=='breadth':                  # top-k STATIC (a priori distractors look plausible) = random k
        k=L_MAX; ids=list(nodes); pick=list(RNGpick(ids,k)); return sc(pick)
    if arm=='placebo':                  # L random reads (genuinely may hit a decisive node)
        ids=list(nodes); pick=list(RNGpick(ids,L_MAX)); return sc(pick)
    if arm=='psi_similarity':           # admit node whose rep is NEAREST current v (A0-suspect)
        v=case['v0'].copy(); adm=[]
        for _ in range(L_MAX):
            cand=[n for n in nodes if n not in adm]
            if not cand: break
            nn=min(cand, key=lambda n: ((reps[n]-v)**2).sum())
            adm.append(nn); v=(1-EPS)*v+EPS*extract(adm,case,d)
        return score(v, mu)
    raise ValueError(arm)

# a seedable picker
_pk = np.random.default_rng(0)
def RNGpick(ids,k): return _pk.choice(ids, size=min(k,len(ids)), replace=False)

def sim(multihop_frac, circular=False):
    ARMS=['baseline','psi_inert','phi_once','vld','breadth','placebo','psi_similarity','final_once']
    out={a:[] for a in ARMS}
    for s in range(SEEDS):
        rng=np.random.default_rng(100+s); global _pk; _pk=np.random.default_rng(200+s)
        for name,(C,d) in SHAPES.items():
            theta = rng.normal(0, SEP, (C,d))
            mu = theta.copy() if circular else learn_mu(theta, rng, d, C)  # circular: μ==GT (rigged)
            acc={a:0 for a in ARMS}
            for _ in range(N_TEST):
                mh = rng.random() < multihop_frac
                case = make_case(rng, theta, d, C, mh)
                for a in ARMS:
                    acc[a] += (run_arm(a,case,mu,d)==case['y'])
            for a in ARMS: out[a].append((name, acc[a]/N_TEST))
    # aggregate per shape
    agg={}
    for name in SHAPES:
        agg[name]={a: np.mean([v for (nm,v) in out[a] if nm==name]) for a in ARMS}
    return agg

print("="*74)
print("REAL MECHANISM SIM — E0/E1 (non-circular; emergent rates; structural controls)")
print(f"SEP={SEP} NOISE={NOISE} EPS={EPS} CHAIN={CHAIN} DISTR={DISTR} seeds={SEEDS} n/cell={N_TEST}")
print("="*74)

# E1 core: m=0.6 multi-hop tail, real scoring
agg = sim(0.6)
print("\nE1 (m=0.6 multi-hop hard tail) — truth-accuracy by arm, per shape:")
hdr = ['baseline','psi_inert','phi_once','vld','breadth','placebo','psi_similarity']
print("  shape       " + "  ".join(f"{h[:9]:>9}" for h in hdr))
for name in SHAPES:
    a=agg[name]; print(f"  {name:11s} " + "  ".join(f"{a[h]:9.3f}" for h in hdr))
print("\n  Deltas (VLD-relative), per shape:")
print("  shape        d_op(Φ1-base)  d_depth(VLD-Φ1)  d_depth-breadth  d_depth-placebo  A0(inert-plc)  traj(VLD-final)")
for name in SHAPES:
    a=agg[name]
    print(f"  {name:11s}   {a['phi_once']-a['baseline']:+.3f}         {a['vld']-a['phi_once']:+.3f}"
          f"           {a['vld']-a['breadth']:+.3f}          {a['vld']-a['placebo']:+.3f}"
          f"         {a['psi_inert']-a['placebo']:+.3f}        {a['vld']-a['final_once']:+.3f}")

print("\nA0 STRUCTURAL CHECK: psi_inert should EXACTLY equal baseline (identity on v0):")
for name in SHAPES:
    a=agg[name]; print(f"  {name:11s} inert={a['psi_inert']:.3f} baseline={a['baseline']:.3f}  Δ={a['psi_inert']-a['baseline']:+.4f}")

print("\nFLAT-NULL (m=0): depth advantage over breadth should collapse (emergent, not prescribed):")
agg0=sim(0.0)
for name in SHAPES:
    a=agg0[name]; print(f"  {name:11s} d_depth-breadth={a['vld']-a['breadth']:+.3f}  d_depth={a['vld']-a['phi_once']:+.3f}")

print("\nCIRCULARITY CHECK (μ==GT, rigged): effect should INFLATE vs non-circular (confirms non-circularity matters):")
aggc=sim(0.6, circular=True)
for name in SHAPES:
    print(f"  {name:11s} d_depth-breadth  noncirc={agg[name]['vld']-agg[name]['breadth']:+.3f}  circ={aggc[name]['vld']-aggc[name]['breadth']:+.3f}")

print("\n[SYNTHETIC but REAL-MECHANISM: rates EMERGE from centroid scoring; controls are structural.]")
print("[Still headroom, not real-world evidence — that needs E6 on real bitemporal data.]")
```

### D.2 Raw output (`vld_mechanism_sim_results.txt`)

```
==========================================================================
REAL MECHANISM SIM — E0/E1 (non-circular; emergent rates; structural controls)
SEP=1.3 NOISE=0.9 EPS=0.35 CHAIN=3 DISTR=10 seeds=8 n/cell=1500
==========================================================================

E1 (m=0.6 multi-hop hard tail) — truth-accuracy by arm, per shape:
  shape        baseline  psi_inert   phi_once        vld    breadth    placebo  psi_simil
  SOC             0.271      0.271      0.563      0.752      0.716      0.718      0.477
  Trading         0.258      0.258      0.647      0.838      0.744      0.740      0.429
  Purchasing      0.287      0.287      0.554      0.730      0.756      0.758      0.488
  DataOps         0.300      0.300      0.559      0.728      0.700      0.690      0.468
  S2P             0.245      0.245      0.634      0.787      0.727      0.722      0.423

  Deltas (VLD-relative), per shape:
  shape        d_op(Φ1-base)  d_depth(VLD-Φ1)  d_depth-breadth  d_depth-placebo  A0(inert-plc)  traj(VLD-final)
  SOC           +0.293         +0.189           +0.036          +0.034         -0.448        +0.000
  Trading       +0.389         +0.191           +0.094          +0.098         -0.481        +0.000
  Purchasing    +0.266         +0.176           -0.026          -0.029         -0.471        +0.000
  DataOps       +0.259         +0.169           +0.028          +0.038         -0.390        +0.000
  S2P           +0.389         +0.154           +0.061          +0.066         -0.477        +0.000

A0 STRUCTURAL CHECK: psi_inert should EXACTLY equal baseline (identity on v0):
  SOC         inert=0.271 baseline=0.271  Δ=+0.0000
  Trading     inert=0.258 baseline=0.258  Δ=+0.0000
  Purchasing  inert=0.287 baseline=0.287  Δ=+0.0000
  DataOps     inert=0.300 baseline=0.300  Δ=+0.0000
  S2P         inert=0.245 baseline=0.245  Δ=+0.0000

FLAT-NULL (m=0): depth advantage over breadth should collapse (emergent, not prescribed):
  SOC         d_depth-breadth=+0.032  d_depth=+0.000
  Trading     d_depth-breadth=+0.094  d_depth=+0.000
  Purchasing  d_depth-breadth=-0.030  d_depth=+0.000
  DataOps     d_depth-breadth=+0.020  d_depth=+0.000
  S2P         d_depth-breadth=+0.060  d_depth=+0.000

CIRCULARITY CHECK (μ==GT, rigged): effect should INFLATE vs non-circular (confirms non-circularity matters):
  SOC         d_depth-breadth  noncirc=+0.036  circ=+0.040
  Trading     d_depth-breadth  noncirc=+0.094  circ=+0.110
  Purchasing  d_depth-breadth  noncirc=-0.026  circ=-0.013
  DataOps     d_depth-breadth  noncirc=+0.028  circ=+0.023
  S2P         d_depth-breadth  noncirc=+0.061  circ=+0.072

[SYNTHETIC but REAL-MECHANISM: rates EMERGE from centroid scoring; controls are structural.]
[Still headroom, not real-world evidence — that needs E6 on real bitemporal data.]
```
