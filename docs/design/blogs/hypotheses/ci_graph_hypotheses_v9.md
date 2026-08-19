# Self-Computing Graphs: Coalescing Context, Learning What to Trust
### Pre-paper — the formalism and the hypotheses it generates (v9)

*The substrate (S) defines a self-computing graph and the fundamental operations of reasoning on it. Each hypothesis is then a falsifiable claim about what one operation buys you — stated in a consistent structure: claim, concrete example, the before→after shift, how it could be falsified, and a compact evaluation (field impact / reachability / portability / defensibility). The order is conceptual. Project notes — lineage, code status, sequencing, method — are in the appendix, separate from the ideas.*

---

## Thesis

Most graph-based AI is static: the ten-thousandth decision is handled exactly like the first. This work claims a graph system can instead get **broader and better the longer it runs** — coalescing more context and reaching competence in fewer decisions over time — for a structural reason: its own computation lives in the graph, so the operations that broaden it and the operations that sharpen it act on the same object. Two coupled engines follow: a **breadth** engine (coalesce context) and a **depth** engine (learn what to trust). They do different kinds of work — breadth **raises the level** (a broader, better-contextualized graph starts higher on day zero and on each new domain), depth **bends the curve** (judgment sharpens faster over time) — and they couple: a higher-level substrate makes learning more directed, and learning what to trust makes the next coalescing sharper. And because real graph decisions *traverse* the graph rather than fire once, both engines are exercised across **multi-hop** decision processes — a third axis, along which their advantage compounds most (the meta-hypothesis developed below).

---

## S · The formalism: a self-computing graph and its operations *(substrate)*

A self-computing graph is a graph whose own computation is part of the graph. Write it **G = (V ∪ V_f, E ∪ E_f)**: data nodes and edges (V, E) together with *operator* nodes and edges (V_f, E_f) — the decision metric, the per-factor reliability weights, the update rule — represented as graph objects rather than as code operating over a passive graph. The system is **closed under its own computation**: the operations that use, broaden, and improve the graph are themselves expressible on it, and because operators are graph objects, every operation acts on data and computation alike.

**The elements.** Four kinds of thing live in the graph and are what the operations act on: **state** (the persisted operators — the metric, reliability-weights, prototype positions), **computation** (those operators as *executable* objects — the closure target), **enrichment** (unverified context folded in), and **decisions** (the verified-outcome records learning consumes). Reification is a property *per element*: an element is reified when it is a graph object the system reads and writes as graph. Today **state, enrichment, and decisions are reified** — persisted and readable back — while **computation is not yet**: the operators execute in code, and no graph object represents the update rule acting on the graph. That is the *state-reified, computation-not* seam, and it is by design — the formalism states the general form, DataOps is the partial existence proof, and executable closure is the frontier the paper reaches via experiment rather than via current code. A claim's status is set by which elements it needs reified.

A small set of operations is fundamental to reasoning on such a graph — each acting on these elements — not the only ones, but the load-bearing ones:

- **score** — apply the reified metric to a query; decide by proximity to learned prototypes. `decision = score(G, q)`.
- **learn** — reshape the reified operators from verified outcomes. `G' = learn(G, outcome)`. Because the metric and weights are graph objects, learning is a graph write.
- **enrich** — fold unverified context into the graph, fusing many observation streams by learned source-reliability. `G' = enrich(G, observations)`. Enrichment grows and calibrates context; it is firewalled from the verified-outcome signal.
- **merge** — coalesce two graphs or sub-graphs into one, *including their reified operators*. `G = merge(G_i, G_j)`. Structure and trust-structure combine.
- **read** — traverse the reified operators to explain a decision. `explanation = read(G, decision)`.
- **admit** — gate a rewritten operator, deploying it only if it passes a non-degradation test. `G' = admit(G, candidate)`.
- **decay** and others round out the algebra — aging stale observations, pruning, and so on.

**Composition.** The algebra is closed under composition: chaining these operations yields a *multi-hop decision process* — a path or DAG of primitive applications (score → read → enrich → score → merge → …). Most real graph decisions are such compositions, not single applications, and a composed process is itself an object the system can run, read, and improve. The meta-hypothesis below is about these processes.

Two of these — **enrich** and **merge** — are the fundamental **breadth** operations: they make the graph broader and better-contextualized independent of verified outcomes. **score** and **learn** are the **depth** operations: they make judgment sharper over time. Closure is what couples the two: because enrich and merge act on operators as well as data, enrichment can sharpen the metric's inputs and merging can coalesce learned trust across domains — *data and computation coalesce together*, which ordinary graph operations on data alone cannot do. The two engines are coupled but not symmetric in kind: depth carries a *compounding* claim (the curve bends, and keeps bending), whereas breadth is a *leveling* engine — it broadens the graph and lifts the starting point, applied as often as new context arrives. This paper makes no claim of super-linear returns to breadth itself; that was the cross-graph discovery arm, retired as a pair-count artifact.

**The boundary — what is NOT in this algebra.** These operations are structural: they execute on the graph *given an interpretation*; they do not supply it. Deciding which entities across two graphs are the same (entity resolution), or what intent a raw signal carries, is **interpretive** — a judgment about meaning, not a graph operation — and belongs to the situation-analysis layer (ACCP), which supplies the correspondences that `merge` and `enrich` then execute. This separation is what keeps the formalism clean and, incidentally, what keeps the retired cross-graph *discovery* arm out: `merge` combines graphs and operators given a correspondence; it does not search for correspondences.

**Falsifiable if** the operators turn out to be representationally inert — if no capability below actually requires them to be graph objects rather than external code, i.e. if closure buys nothing.

*Field impact — foundational. · Reachability — architectural (a scan, not an experiment). · Portability — high. · Defensibility — medium (reification and closure are strong words; they are shown by the operations below, not asserted).*

---
---

## Depth engine — learning what to trust *(the `score` and `learn` operations)*

## H-TRUST · A learned metric beats the default *(claim about `score`)*

**Claim.** The `score` operation decides what attends to what through a similarity primitive that defaults to normalized dot-product (cosine) — one frozen setting of a parameterized metric, `score(q,K)=softmax(−γ·(q−k)ᵀM(q−k))`, where cosine is the special case `M=I` after normalization. On bounded, interpretable, magnitude-bearing features, weighting each dimension by its measured reliability (`M=diag(1/σ²)`, σ² = outcome-conditioned noise) recovers signal the default discards — and the gain grows with how unevenly noise is spread across dimensions.

**Example.** A triage graph has a clean factor (`device_trust`, low σ) and a noisy one (`user_reported_reason`, high σ). Cosine weights them equally, so the noisy factor drowns the clean one and near-duplicate cases get retrieved for the wrong reasons. A reliability-weighted metric down-weights the noisy dimension and the right neighbors surface. Where all factors are equally noisy, the two behave the same — exactly the boundary the claim predicts. (Honest cost: concentrating weight on reliable factors sharpens the output distribution and *degrades calibration* — the accuracy gain and the calibration loss are one effect, so confidence must be read from a separate, kernel-independent signal.)

**Before → After.** *Before* — embed, normalize, match by similarity; inherit whatever the confident-but-noisy factor says. *After* — keep magnitude, weigh evidence by measured reliability.

**Falsifiable if** cosine matches the metric on genuinely magnitude-bearing data — or, more tellingly, if the metric's edge *survives* normalizing the features, which would mean the effect was never about magnitude.

*Field impact — med/high. · Reachability — high (public bounded-feature data). · Portability — high (one operator, kernel as a parameter, platform-free). · Defensibility — med/high (carried by the operator reframing + the noise-heterogeneity law + the characterized calibration tradeoff, not "L2 beats cosine," which brushes metric-learning folklore).*

## H3 · What `learn` accumulates is memory of the computation *(the hinge)*

**Claim.** Episodic memory stores what happened; semantic memory stores what is true — both are memories of content. When `learn` reshapes a reified operator from verified outcomes, what accumulates is a memory of the *decision procedure itself*. This **judgment memory** is a distinct, fourth memory type because it is memory *of computation*, not of content — a distinction that only exists under reification.

**Example.** Three memories about one domain. Episodic: "alert #4471 was escalated Tuesday." Semantic: "credential-access alerts are high severity." Judgment: "*in this deployment*, threat-intel proved reliable and asset-criticality proved noisy, and the metric now weights them accordingly." The third is not an event or a fact — it is the learned procedure, stored as the reified metric. (A medical record, a textbook, and a protocol can all confirm a biased treatment; only a per-surgeon quality scorecard — judgment — detects the bias.)

**Before → After.** *Before* — a system that gets better accumulates more episodes and retrieves by similarity. *After* — it accumulates reshaped operators; the compounding lives in the decision procedure, not the data.

**Falsifiable if** "memory of the operator" reduces to episodic/semantic storage, or to procedural memory as ordinarily defined — if the fourth category buys no capability the existing three don't cover.

*Field impact — high (a CoALA-positioned taxonomy claim). · Reachability — high (an architectural argument, not a dataset). · Portability — medium. · Defensibility — med/high (a structural claim, not a prevalence claim — so not data-gated, unlike the operational version in the appendix).*

## H-CURVE · `learn` on the metric bends the learning curve *(the spine)*

**Claim.** As judgment memory accumulates, each new domain or disruption costs *fewer* decisions to absorb than the last — not merely that the system improves, but that its *rate* of improvement rises. `learn` has two channels — learning prototype positions (fast, transferable, saturating) and learning the metric, i.e. *what to trust* (ongoing, firm-specific) — and it is the second channel that bends the curve, because once the system knows which dimensions carry signal, every later outcome updates the right things instead of spreading across noise.

**Example.** Learning six alert categories in sequence: category #1 needs ~120 verified decisions to reach competence; by #6 it needs ~40 — not because #6 is easier, but because the first five taught it which factors matter, so credit for #6 lands immediately. After a disruption the same head start applies: re-convergence beats first convergence, provable when the firm-specific deviation exceeds a threshold, with the metric's distance-to-target (not a noisy accuracy-crossing count) as the clean signal.

**Before → After.** *Before* — each new situation costs about the same to learn. *After* — each costs less than the last; the system has learned how to learn in this space.

**Falsifiable if** decisions-to-competence stay flat across shifts, or if the decline is fully explained by position-learning alone — if learning *what to trust* adds nothing to the acceleration. (Known boundary: stale reliability weights carried into a disruption can *reverse* the effect — a characterized failure, not a refutation.)

*Field impact — high (the temporal claim, in decision-cycle units). · Reachability — medium (a dynamics claim; simulation-legitimate with the appendix guardrails). · Portability — high. · Defensibility — medium (circularity climbs here; defend on clean convergence dynamics, not threshold-crossing).*

## H-BOUND · `learn` is bounded — self-modification can't degrade below baseline *(the safety of depth)*

**Claim.** Because the update is a reified operator, the system can bound `learn` with a runtime invariant: a verified-accuracy floor plus a promotion gate (`admit`) that accepts a rewritten operator only when it is non-inferior on held-out outcomes. The curve can bend up but not down past the floor — and the same reification that lets the system learn lets it *prove* it hasn't degraded. Safety and compounding rest on the same substrate — reification — rather than trading off against each other.

**Example.** A poisoned run of feedback is caught two ways: the promotion gate rejects any batch that fails holdout non-inferiority, and the invariant auto-pauses learning if rolling verified accuracy falls below its own baseline; learning resumes from the last good operator. (Honest boundary: under the worst adversarial operators a characterized fraction of runs still fail to recover — the bound is real, not absolute.)

**Before → After.** *Before* — online self-modification risks silent degradation, so you daren't let a production system rewrite its own decisions. *After* — self-modification is bounded and auditable, so a system that learns in production is deployable.

**Falsifiable if** adversarial batches slip past the gate and degrade the system undetected, or if enforcing the bound suppresses the compounding — if safety and learning trade off rather than coincide.

*Field impact — high (safe self-modification is the capability the field most wants and least trusts). · Reachability — medium (simulation-legitimate; the honest negative — a fraction never recover — is a feature). · Portability — high (a runtime invariant + gate any online learner can adopt). · Defensibility — medium (defend on the characterized failure rate, never as an absolute guarantee).*

---
---

## Breadth engine — coalescing context *(the `enrich` and `merge` operations)*

*Breadth raises the level and broadens coverage: it starts the graph higher on day zero and warmer on each new domain, and it is applied whenever new context arrives. The claims here are breadth's day-zero and cross-domain lift, and its coupling to depth — not super-linear returns to breadth itself.*

## H-ENRICH · `enrich` is a second engine, working before any outcome exists *(claim about `enrich`)*

**Claim.** Verified outcomes are slow and absent on day one. `enrich` — folding continuous, high-volume, *unverified* context into the graph and fusing many observation streams by learned *source*-reliability (which feed to trust — a different object from the *factor*-reliability the metric weighs, though learned the same way) — is a second learning curve that lowers decisions-to-competence from the start, and it *feeds the depth engine*: a richer, better-calibrated context sharpens the very inputs the metric weighs. It stays firewalled from the verified-outcome signal, so it improves context, never ground truth.

**Example.** On day zero a security graph has no confirmed decisions to learn from, but enriching it with vendor-master, threat-intel, and org-chart streams — each weighted by how reliable that source has proven — lets it make sensible first calls instead of guessing. The coupling is measurable: enrichment that reduces a factor's noise lets the metric upweight that now-cleaner factor, lifting day-one accuracy — while leaving the convergence *rate* unchanged (enrichment changes the substrate, not the learning speed). That clean split is the honest boundary.

**Before → After.** *Before* — the system is blind until labels arrive. *After* — it starts competent on decision one, on a fast unverified curve alongside the slow verified one, with the two curves coupled through reliability.

**Falsifiable if** enrichment fails to lift the day-zero curve, or only helps by leaking into the verified signal — in which case it is not a second engine but a contamination of the first.

*Field impact — high (answers the cold-start / zero-day problem, and couples the two engines). · Reachability — medium (partly evidenced; source-fusion is the harder part to isolate). · Portability — med/high. · Defensibility — medium (the firewall is what keeps it honest; state it explicitly).*

## H-COALESCE · `merge` coalesces trust, not just data *(claim about `merge`)*

**Claim.** `merge` combines two graphs — and, because computation is reified, *their operators* — into one substrate. The novel content is not merging nodes (folklore) but **coalescing the reified trust-structures**: a factor's learned reliability in one domain informs the merged metric, so the combined graph reasons across domains and a new domain starts warm on borrowed trust rather than cold. (Scope, to reconcile with H-CURVE: this is coalescing across *domains within one deployment* — where the reliability structure is shared because it is the same firm's data — not transfer across *firms*, whose metric weights are firm-specific and do not carry. Cross-domain, same firm: coalesces. Cross-firm: does not.)

**Example.** Merging a security graph and a fraud graph (given the entity correspondence that ACCP supplies): threat-intel's learned reliability from the security side carries into the merged metric, so fraud decisions on shared factors reach competence faster than cold. What coalesces is the *trust-structure*, not merely the shared entities.

**Before → After.** *Before* — N domains are N systems with N separate trust-structures; a new domain starts cold. *After* — one substrate in which learned trust coalesces, and a connected domain starts warm.

**Falsifiable if** merged trust is no better than independent per-graph trust, or if the lift is recoverable by naive feature-sharing with no operator coalescing. (Three things this claim is *not*: not cross-graph relation-*discovery* — that arm is dead, dot-product and pair-count-bound; not entity resolution — the correspondence is interpretive and supplied by ACCP, not decided by `merge`; and not ordinary transfer learning — the claim is that inspectable trust-structures coalesce *additively as graph operators*, not that a shared representation is fine-tuned into a new task.)

*Field impact — high (multi-graph reasoning that carries learned trust is what the field wants and lacks). · Reachability — low/med (a clean multi-graph benchmark isolating trust-coalescing is the hardest to design). · Portability — high. · Defensibility — medium (the novelty is narrow — coalescing operators, not data — and must be stated as such, positioned against transfer/multi-task learning as its nearest prior art). Absorbs the former cross-graph-transfer hypothesis; it is the `merge` operation's payoff.*

---
---

## The process dimension — multi-hop decisions *(meta-layer)*

## H-MULTIHOP · Graph decisions are multi-hop, and the reified algebra's advantage compounds with depth *(meta-hypothesis)*

**Claim.** Real graph decisions are rarely a single `score`; they are *compositions* — a path or DAG that chains primitives (score → read → enrich → score → merge → score) until a terminal decision. Because the algebra is closed under composition, a multi-hop decision process is itself an object the system can run, read, and improve. The meta-claim: every primitive-level hypothesis has a process-level form that becomes *more* consequential with hop depth — the cost of the field's defaults compounds along the path, while the reified operators keep the path correctable and inspectable at every hop.

**Dimensions of a multi-hop decision process** (the axes to define, vary, and measure against):
- **Depth (k)** — number of chained decisions; k=1 is the single-step case, deep reasoning is large k.
- **Branching (b)** — candidates carried per hop (top-K): a committed path versus an explored tree.
- **Composition** — which primitives the path chains, and whether hops stay in one graph or cross enriched/merged sub-graphs (homogeneous vs heterogeneous; single- vs cross-domain).
- **Error propagation** — how a per-hop ranking error carries downstream; with an unlearned metric, one mis-weighted hop derails the rest of the path.
- **Credit assignment** — how a verified outcome at the terminal updates the operators used at *each* hop (terminal-only vs per-hop attribution) — the multi-hop learning problem.
- **Termination & abstention** — when the process stops, commits, or refers up — the process-level form of the abstain and the bound.

**Per-hypothesis manifestations** (this is what makes it meta — each claim re-appears at the path level):
- *Trust (H-TRUST) compounds along hops* — a per-hop ranking error propagates, so the value of a learned metric grows with depth; cosine's defaults hurt most on long paths.
- *Learning (H-CURVE) needs path credit* — the curve bends at the process level only if credit reaches the operators at each hop, not just the terminal; that is the multi-hop credit-assignment condition.
- *The bound (H-BOUND) must span the path* — non-degradation is a property of the whole traversal, not one step.
- *Breadth enables depth* — `enrich` and `merge` are what let a path cross domains at all; a cross-domain hop is only possible on a coalesced substrate.
- *Inspection (H4) and judgment memory (H3) become path-level* — explaining a multi-hop decision means reading the whole traversal, and what judgment memory records is the per-hop operator changes along it.

**Example.** A security decision that looks benign in isolation becomes an escalation after three hops: score the alert (near-threshold) → an enrich-hop pulls in threat-intel context that raises asset-criticality → re-score → a merge-hop into the identity graph, where the account's privilege recently changed → final score crosses the escalation boundary. At each hop the reified metric decides what to attend to next; a mis-weighted early hop would have terminated the path at "benign." Learned trust matters *more* here than in any single score, because its errors compound over three hops.

**Before → After.** *Before* — multi-hop reasoning is a black-box chain (LLM-agent hops, or hand-built traversal) whose errors and rationale are opaque and whose learning is terminal-only. *After* — each hop is a reified, inspectable decision with its own learned trust, credit reaches every hop, and the path's degradation is bounded end-to-end.

**Status (partial).** Data hops are traversable in the graph today, but a composed multi-hop *decision process* is assembled in code, not reified as a process object the system can read back whole. So the process-level *claims* are testable now; the *substrate* form — the path itself as a graph object — is proposed.

**Falsifiable if** the single-hop advantages do *not* amplify with depth — if a learned metric helps no more at k=5 than at k=1, if per-hop error doesn't propagate, or if terminal-only credit bends the curve as well as per-hop credit. Then multi-hop is just repeated single-hop and the meta-claim is false.

*Field impact — high (multi-hop reasoning is where the agent/GraphRAG energy is, and where opacity and error-compounding bite hardest). · Reachability — medium (depth-sweep experiments: vary k and measure whether each advantage scales with depth). · Portability — high (the dimensions apply to any graph decision process). · Defensibility — medium (must show amplification-with-depth, not assert it; nearest prior art is multi-hop QA / knowledge-graph reasoning and RL credit assignment).*

---
---

## Consequence — the graph is inspectable *(the `read` operation)*

## H4 · Reading the operators explains the decision *(claim about `read`)*

**Claim.** Because the operators are (or can be) objects in the graph, `read` explains a decision by *traversing* it — interpretability is structural, and in this regime a closed-form geometric scorer matches learned embeddings or a GNN with no training step and no black box. (Status: decisions and their context are already read from the graph; operator-level explanation — reading the metric and reliability-weights as graph nodes rather than reconstructing them from the scorer's state — is the reification target, not yet the implementation.)

**Example.** "Why did you escalate this?" is answered by reading the three factor-nodes that crossed threshold and the reliability-weights that scaled them — a traversal of the actual decision — rather than a post-hoc SHAP approximation of an opaque model.

**Before → After.** *Before* — reach for a GNN, pay training cost, lose interpretability. *After* — closed-form scorer in the stated regime; no training, and the decision's factors, thresholds, and (once operators are reified) reliability-weights are inspectable by reading the graph.

**Falsifiable if** the GNN/learned baseline wins materially in-regime, or if "interpretability" needs post-hoc explanation rather than reading the reified operators.

*Field impact — med/high. · Reachability — high (public benchmarks vs GNN/embeddings/trees). · Portability — high. · Defensibility — low/med (folklore risk: simple beats GNN on tabular/low-data; novelty is interpretability-via-reification + regime, not the win).*

---
---

## Deliberately outside this paper

**Operational judgment memory** — the stronger claim that judgment memory *measurably* beats accumulate-and-retrieve over long horizons — needs data this argument does not assume and carries higher circularity. Future work; keep it separated from H3-structural.

**Situation analysis / control plane (ACCP)** — the *interpretive* layer: entity resolution (which entities correspond), intent classification (what a signal means), typed-intent routing, and governance. It supplies the correspondences that `enrich` and `merge` execute, and the decision stream the depth engine consumes — but interpretation is a different kind of claim (meaning, latency, governance, audit), not a graph operation. Its own systems paper; connected here by one cross-reference each way. This is the one thing that does *not* fold in.

---
---

## Appendix — project notes (not part of the argument)

*None of this bears on whether a hypothesis is true; a hypothesis is settled by a purpose-built experiment, never by the state of the code.*

**Lineage and absorption.** This pre-paper is the thesis for the *next version of the distance-kernel / cross-graph math paper* — a significant upgrade on the same arXiv lineage, so accumulated outreach and citations carry forward rather than restarting. It **absorbs the production/architecture companion paper's dynamics-and-safety material** (the conservation law becomes H-BOUND's runtime bound; adversarial robustness, defense-in-depth, and James-Stein its characterized safety). The two prior papers overlapped ~70% (kernel, theorem, judgment memory, conservation law); the reification-plus-operations spine is what lets that union read as one argument rather than two near-duplicate papers. The `enrich`→`score` coupling is already partly evidenced in the prior work (enrichment reduced per-factor noise and lifted day-one accuracy via metric reweighting, with a clean null on convergence rate). Landmark results that earned the prior outreach stay visible — the kernel-choice finding (now H-TRUST's mechanism, synthetic ceiling walled, de-circularized real-data number leading), the re-convergence theorem (H-CURVE's core), and judgment memory (H3). **Inclusion rule:** every section must serve "self-computing graphs that coalesce context and learn what to trust," or it is cut or sent to the ACCP paper.

**Code status — informational only (from the DataOps reification scan).** The one-line finding: **state is reified, computation is not — yet.** Operator *state* is graph-persisted and readable back (centroids and reliability-weights, verified outcomes, enrichment nodes with source links, promotion/conservation records); the *operators* — the metric, the update rule, the merge, and operator-level explanation — still execute in code, and no graph node represents the update rule acting on itself (closure is external). This sets phrasing only, never acceptability. Per-claim, from the scan:
- *Implemented-partial (persisted, inspectable state):* H3 (judgment memory queryable), H-TRUST's operator *state*, H-ENRICH (enrichment + source links written), H-BOUND's gate *state* (promotion/conservation records), H4's *data* half (decisions + context read from the graph), H-CURVE's learning *artifacts*.
- *Proposed (design-only in code):* executable closure (the strong form of S), operator-aware `merge` → **H-COALESCE not found in code**, the reified multi-hop *process object* (strong form of H-MULTIHOP), and operator-node explanation (strong form of H4 — trust/metric explanation is currently reconstructed from the scorer's state, not traversed).
The metric, scorer, theorem, two-phase learning, and conservation gate also exist as prose and code in the prior papers/experiments repo; they are rebuilt fresh for any clean test. The paper's claims rest on new, mostly public-data experiments.

**Evidence status — which claims arrive with support, which are proposed.** Not all eight hypotheses are co-equal results, and the paper must not read as eight validated findings. The spine and lever (H-CURVE, H-TRUST) and the taxonomy claim (H3) arrive with results or proofs re-hosted from the absorbed papers (the kernel gap, the re-convergence theorem, the CoALA positioning); H-BOUND arrives with the conservation-law and adversarial-robustness results. H-ENRICH is partly evidenced (the σ-reduction coupling) and partly new (source-fusion). H-COALESCE and H-MULTIHOP are framework claims — proposed and characterized here, tested next, not yet validated. Each must be phrased at its true status in the draft.

**Result states.** Every experiment returns validated / invalidated / inconclusive-underpowered. An invalidation is a first-class, citable result. An underpowered null is a to-do, not an invalidation.

**Sequencing — logistics only, not a reason to reorder the argument.** The `score`/`read` claims (H-TRUST, H4) are the cheapest, lowest-risk, public-data results — bank first. The `learn` claims (H-CURVE, H-BOUND) and the breadth claims (H-ENRICH, H-COALESCE) are higher-impact and harder to land, though much already exists as prose in the absorbed papers. H-COALESCE runs only if a clean multi-graph benchmark exists. A reification scan (~1 day) precedes the framing of S/H3/H-CURVE/H-BOUND; a framing judge-poll and the floor experiments run in parallel after it.

**Method guardrails (hard-won).** For any temporal claim, measure convergence by distance-to-target, not threshold-crossing counts; 30+ seeds; isolate metric-learning from position-learning. For H-TRUST, the main comparison must use magnitude-bearing (non-normalized) features — under unit-normalization squared distance is a monotone transform of cosine and the comparison is vacuous; the normalized case is the falsification control. For H-BOUND, report the adversarial non-recovery rate honestly rather than claiming an absolute guarantee. For H-COALESCE, hold the interpretive step (entity correspondence) fixed and supplied, so the experiment tests operator-coalescing rather than entity resolution.
