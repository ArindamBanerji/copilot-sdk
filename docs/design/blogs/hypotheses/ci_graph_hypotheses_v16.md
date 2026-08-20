# Self-Computing Graphs: Coalescing Context, Compounding From Verified Outcomes
### Pre-paper — the formalism and the hypotheses it generates (v16 — H-CURVE run-ready on ratified constructions; ε★ formula defect logged for cga v8)

*The substrate (S) defines a self-computing graph and the fundamental operations of reasoning on it. Each hypothesis is then a falsifiable claim about what one operation buys you — stated in a consistent structure: claim, concrete example, the before→after shift, how it could be falsified, and a compact evaluation (field impact / reachability / portability / defensibility). The order is conceptual. Project notes — lineage, code status, sequencing, method — are in the appendix, separate from the ideas.*

---

## Thesis

Most graph-based AI is static: the ten-thousandth decision is handled exactly like the first. This work claims a graph system can instead get **broader and better the longer it runs** — coalescing more context and reaching competence in fewer decisions over time — for a structural reason: its own computation lives in the graph, so the operations that broaden it and the operations that sharpen it act on the same object. Two coupled engines follow: a **breadth** engine (coalesce context) and a **depth** engine (compound from verified outcomes). They do different kinds of work — breadth **raises the level** (a broader, better-contextualized graph starts higher on day zero and on each new domain), depth **bends the curve** (verified outcomes reshape the decision geometry, and re-convergence after disruption is faster than first convergence). *What the depth engine is NOT:* it is not a claim that a distance/reliability **kernel** beats the default similarity primitive — that claim (H-KERNEL below) was tested on real data and **invalidated**. The compounding lives in the *geometry* the system learns from verified outcomes (where the decision prototypes sit), not in *which metric weights the dimensions*. The two engines couple: a higher-level substrate makes learning more directed, and learned geometry makes the next coalescing warmer. And because real graph decisions *traverse* the graph rather than fire once, both engines are exercised across **multi-hop** decision processes — a third axis, along which their advantage compounds most (the meta-hypothesis developed below).

---

## S · The formalism: a self-computing graph and its operations *(substrate)*

A self-computing graph is a graph whose own computation is part of the graph. Write it **G = (V ∪ V_f, E ∪ E_f)**: data nodes and edges (V, E) together with *operator* nodes and edges (V_f, E_f) — the decision geometry (centroid prototypes), the update rule, and the scoring metric — represented as graph objects rather than as code operating over a passive graph. The system is **closed under its own computation**: the operations that use, broaden, and improve the graph are themselves expressible on it, and because operators are graph objects, every operation acts on data and computation alike. **"Self-computing" is a spectrum, and today's system is partial.** Full self-computation would require all four elements reified; today **state, enrichment, and decisions are reified** and **computation is not** (operators execute in code). The paper's non-obvious claim is that *even partial reification* — three of four elements — already produces the depth engine's compounding; reifying the fourth (computation) is what unlocks the multi-hop process-object and operator-level explanation. The spectrum is the research program, and the title names its endpoint, not today's state.

**The elements (first-class — the nouns of the algebra).** The algebra has two kinds of first-class citizen: **elements** (what lives in the graph) and **operations** (what acts on them). Four elements are basic:
- **state** — the learned *decision geometry*: the centroid/prototype positions the system has moved from verified outcomes. (The per-factor reliability-weights were also state, but H-KERNEL invalidated their advantage on real data — the load-bearing state is the geometry, not the weights.)
- **computation** — the operators (`learn`, `score`, the update rule) as *executable* objects — the closure target.
- **enrichment** — unverified context folded in, firewalled from the verified signal.
- **decisions** — the verified-outcome records that `learn` consumes.

Reification is a property *per element*: an element is reified when it is a graph object the system reads and writes as graph. Today **state, enrichment, and decisions are reified** — persisted and readable back — while **computation is not yet**: the operators execute in code, and no graph object represents the update rule acting on the graph. That is the *state-reified, computation-not* seam, and it is by design — the formalism states the general form, DataOps is the partial existence proof, and executable closure is the frontier the paper reaches via experiment rather than via current code. A claim's status is set by which elements it needs reified. (Note the element/operation duality: *enrichment* and *decisions* are elements that the operations `enrich` and `learn` produce and consume — the nouns and verbs share names by design.)

A small set of operations is fundamental to reasoning on such a graph — each acting on these elements — not the only ones, but the load-bearing ones:

- **score** — apply the reified metric to a query; decide by proximity to learned prototypes. `decision = score(G, q)`.
- **learn** — reshape the reified decision geometry (centroid positions) from verified outcomes. `G' = learn(G, outcome)`. Because the geometry is a graph object, learning is a graph write. (Reshaping the reliability-*weights* is a separable second channel — H-KERNEL — invalidated on real data; the load-bearing `learn` is geometry movement.)
- **enrich** — fold unverified context into the graph, fusing many observation streams by learned source-reliability. `G' = enrich(G, observations)`. Enrichment grows and calibrates context; it is firewalled from the verified-outcome signal.
- **merge** — coalesce two graphs or sub-graphs into one, *including their reified operators*. `G = merge(G_i, G_j)`. Structure and learned geometry combine.
- **read** — traverse the reified operators to explain a decision. `explanation = read(G, decision)`.
- **admit** — gate a rewritten operator, deploying it only if it passes a non-degradation test. `G' = admit(G, candidate)`.
- **decay** and others round out the algebra — aging stale observations, pruning, and so on.

**Composition.** The algebra is closed under composition: chaining these operations yields a *multi-hop decision process* — a path or DAG of primitive applications (score → read → enrich → score → merge → …). Most real graph decisions are such compositions, not single applications, and a composed process is itself an object the system can run, read, and improve. The meta-hypothesis below is about these processes.

Two of these — **enrich** and **merge** — are the fundamental **breadth** operations: they make the graph broader and better-contextualized independent of verified outcomes. **score** and **learn** are the **depth** operations: they make judgment sharper over time. Closure is what couples the two: because enrich and merge act on operators as well as data, enrichment can sharpen the geometry's inputs and merging can coalesce learned geometry across domains — *data and computation coalesce together*, which ordinary graph operations on data alone cannot do. The two engines are coupled but not symmetric in kind: depth carries a *compounding* claim (the curve bends, and keeps bending), whereas breadth is a *leveling* engine — it broadens the graph and lifts the starting point, applied as often as new context arrives. This paper makes no claim of super-linear returns to breadth itself; that was the cross-graph discovery arm, retired as a pair-count artifact.

**The boundary — what is NOT in this algebra.** These operations are structural: they execute on the graph *given an interpretation*; they do not supply it. Deciding which entities across two graphs are the same (entity resolution), or what intent a raw signal carries, is **interpretive** — a judgment about meaning, not a graph operation — and belongs to the situation-analysis layer (ACCP), which supplies the correspondences that `merge` and `enrich` then execute. This separation is what keeps the formalism clean and, incidentally, what keeps the retired cross-graph *discovery* arm out: `merge` combines graphs and operators given a correspondence; it does not search for correspondences.

**Falsifiable if** the operators turn out to be representationally inert — if no capability below actually requires them to be graph objects rather than external code, i.e. if closure buys nothing.

*Field impact — foundational. · Reachability — architectural (a scan, not an experiment). · Portability — high. · Defensibility — medium (reification and closure are strong words; they are shown by the operations below, not asserted).*

---
---

## Depth engine — compounding from verified outcomes *(the `learn` operation; `score` applies the geometry)*

## H-KERNEL · A distance/reliability metric beats the default — *INVALIDATED on real data* *(a first-class negative)*

**Claim (as tested).** A parameterized metric `score(q,K)=softmax(−γ·(q−k)ᵀM(q−k))` — with cosine the special case `M=I` after normalization — beats the default on bounded interpretable features when the diagonal `M=diag(1/σ²)` weights each dimension by reliability, with the gain growing in noise heterogeneity.

**Verdict: INVALIDATED on real data (de-circularized).** A corrected factorial instrument (single-factor magnitude / reliability / primitive contrasts, three authoritative UCI datasets, hostile scale-sensitivity) found the advantage is **not scale-robust**: effects flip sign or vary 10–20× between min-max, robust-quantile, and standardized scaling. No required dataset cleared the +1pp margin under all three conventions; the reliability contrast reversed sign across scales; the heterogeneity law was flat (F3 fired). The apparent edge lives in the *preprocessing*, not the data. This de-circularizes the prior papers' flagship kernel claims — EXP-C1 (36.89pp, centroidal-synthetic) and UNI-DK-01 (the 0→+7.67pp heterogeneity curve) — which do **not** survive on real data.

**Why the paper keeps it (as a negative).** The invalidation is itself the contribution: it corrects the lineage's own record and stops others chasing a kernel advantage that is a scaling artifact. Nothing downstream depends on it — the depth engine runs on *geometry* (`learn` moving centroids), not on the kernel. Removed as a positive claim; retained as a cited boundary.

**Open scope (stated, not a rescue).** Tested on flat tabular features, not the multi-hop graph-decision regime the metric was designed for. The scale-artifact finding is strong and we do not expect the regime to overturn it — but 'graph-decision regime untested' is the honest caveat, not a reason to keep the positive claim alive.

*Field impact — the negative de-circularizes two flagship prior-paper claims. · Reachability — done (run complete). · Result tier — INVALIDATED, scale-artifact, three real datasets. · Role — cited boundary; not a pillar.*

## H3 · What `learn` accumulates is memory of the computation *(the hinge)*

**Claim.** Episodic memory stores what happened; semantic memory stores what is true — both are memories of content. When `learn` reshapes a reified operator from verified outcomes, what accumulates is a memory of the *decision procedure itself*. This **judgment memory** is a distinct, fourth memory type because it is memory *of computation*, not of content — a distinction that only exists under reification.

**Example.** Three memories about one domain. Episodic: "alert #4471 was escalated Tuesday." Semantic: "credential-access alerts are high severity." Judgment: "*in this deployment*, these decision prototypes have moved to *here* because verified outcomes said so." The third is not an event or a fact — it is the learned decision geometry, stored as the reified centroid state. (A medical record, a textbook, and a protocol can all confirm a biased treatment; only a per-surgeon quality scorecard — judgment — detects the bias.)

**Before → After.** *Before* — a system that gets better accumulates more episodes and retrieves by similarity. *After* — it accumulates reshaped operators; the compounding lives in the decision procedure, not the data.

**Two distinctions from procedural memory** (the fourth type is not "knowing how to decide" in the ordinary sense): (1) *verification-dependence* — procedural memory accumulates from repetition; judgment memory accumulates from **verified outcomes**, an outcome signal reshaping the geometry, not practice. (2) *inspectability via reification* — procedural memory is opaque (you cannot articulate how you ride a bike); judgment memory, because the geometry is a reified graph object, is **inspectable and boundable**. The second is the capability gap: reification is what lets H-BOUND enforce non-degradation on the learned operator — you cannot bound what you cannot inspect. So the fourth type earns its place by enabling *bounded* learning, which procedural memory cannot.

**Falsifiable if** "memory of the operator" reduces to episodic/semantic storage, or to procedural memory as ordinarily defined — if neither verification-dependence nor reification-enabled boundability buys a capability the existing three do not cover.

*Field impact — high (a CoALA-positioned taxonomy claim). · Reachability — high (an architectural argument, not a dataset). · Portability — medium. · Defensibility — med/high (a structural claim, not a prevalence claim — so not data-gated, unlike the operational version in the appendix).*

## H-CURVE · `learn` moving the geometry bends the learning curve *(the spine)*

**Claim.** As learned decision geometry accumulates, each new domain or disruption costs *fewer* decisions to absorb than the last — not merely that the system improves, but that its *rate* of improvement rises. The mechanism is **centroid re-convergence**: after a disruption, accumulated prototype positions give a head start, so re-convergence is faster than first convergence. Crucially this is stated in **centroid-distance space** — the re-convergence condition (γ>1 ⇔ ε_firm > ε★) is *independent of the scoring metric* (the accuracy threshold θ cancels), so it does **not** inherit H-KERNEL's invalidation. The bending channel is geometry movement, not reliability weighting.

**Example.** Learning six alert categories in sequence: category #1 needs ~120 verified decisions to reach competence; by #6 it needs ~40 — because the first five have moved the shared prototype geometry, so #6 starts near-converged. After a disruption the same head start applies: re-convergence beats first convergence when the firm-specific deviation exceeds ε★, measured as centroid-distance-to-target (not a noisy accuracy-crossing count).

**Before → After.** *Before* — each new situation costs about the same to learn. *After* — each costs less than the last; the system has learned how to learn in this space.

**Falsifiable if** decisions-to-competence stay flat across successive shifts, or if re-convergence is no faster than first convergence when ε_firm > ε★.

**Status — two separate circularities, and where each stands** (from the session that ran the γ audit). The re-convergence theorem is θ-independent *in theory*, and it faces two distinct threats that must be tracked separately:
- **Data circularity — largely cleared.** The γ audit used oracle separation: LLM-generated factor vectors (confirmed realistic variance 0.077–0.089 and regime differentiation; distributionally distinct across regimes) — *not* the centroidal-synthetic blobs that sank H-KERNEL (those were the separate EXP-C1/EXP-B1 "architecture-validation" runs). Critically, the oracle's ground-truth centroids (GT = canonical μ₀ + ε_firm) are **not** the scorer's learned centroids μ: at the production ε_firm ≈ 0.20 they start 0.20 apart, so the oracle tests whether μ *converges toward a target it has not reached*, not whether GT = μ. One confirmatory recompute remains (vector-to-GT-centroid distances + a θ-free γ from the logged distance trajectories). It was attempted and came back **NOT FOUND — blocked, not refuted**: every code path exists (`FactorVectorSampler`, `OracleSeparationExperiment`, `centroid_distance_to_canonical`, `reconvergence_logger`), but the *persisted outputs* (LLM vectors, GT/scorer centroid snapshots, per-seed distance trajectories) are not in the accessible repo tree — they live on an external location the tooling cannot read. So data-circularity is **argued, with a clean path to confirm that does not depend on the lost files.** The original runs used LLM-generated vectors (provenance now uncertain), but `OracleSeparationExperiment` also runs on **parametric** factor vectors that are *non-centroidal by construction* — a *stronger* de-circularization than checking whether LLM vectors happened to avoid the centroids. The seeds and config are fully documented (42/123/777; ε_firm 0.05/0.20/0.35; σ=0.08; w=10), so a fresh parametric run can (a) confirm the binary prediction (γ<1 below ε★, γ>1 above) on non-centroidal data, (b) recompute γ θ-free from its own logged centroid-distance trajectories, and (c) **persist its artifacts**, closing the reproducibility gap. Status until that runs: **the mechanism is confirmable on non-centroidal parametric data (documented, reproducible); the original LLM-vector runs remain corroborating but provenance-uncertain.**
- **Model validity — untested, and EXP-G1's job.** Even with non-circular data, the formalism *assumes* correctness is centroidal proximity. If real decisions do not follow that geometry, γ>1 *within the model* does not prove γ>1 *in reality*. Only real pilot data (EXP-G1) tests this — and **EXP-G1 has not started** (the system is pilot-gated, no real analysts yet; the "production-faithful γ≈1.2" is a better *simulation*, not real measurement). Data circularity cleared is **necessary but not sufficient**.

So H-CURVE's honest status: **analytically proven (four paths); mechanism-confirmed on oracle-separated, non-circular data; data circularity largely cleared (one confirmatory recompute pending); magnitude and model-validity pending EXP-G1, which is not yet started.** A strong, specific position — not "unverified," not "done."

**Measurement consistency (a real gap in the existing numbers).** The *reported* γ headlines — γ=0.714 at ε=0.05, γ=1.033 at ε=0.20 — are **N_half ratios**, and N_half counts decisions until rolling accuracy crosses θ=0.85, so it is a **θ-dependent** proxy (and noisy at few seeds). The θ-*free* signal — centroid-distance-to-target — was logged alongside and decreases monotonically in every seed and phase (e.g. 3.015→2.386, −21%), but **γ was never recomputed from it**. Recomputing γ as a centroid-distance-rate ratio from the already-logged trajectories is post-processing on existing data, and it is what would confirm the theorem's θ-independence *empirically*. EXP-G1, when it runs, must log `centroid_distance_to_canonical` per decision (infrastructure exists in `gae/convergence.py`).

*Field impact — high (the temporal claim, in decision-cycle units — and the paper's actual spine now). · Reachability — medium (dynamics claim; the EXP-G1 centroid-distance ratio is the clean instrument). · Portability — high. · Defensibility — medium, PENDING de-circularization — do not claim as proven-on-real-data until the scan clears it.*

## H-BOUND · `learn` is bounded — self-modification can't degrade below baseline *(the safety of depth)*

**Claim.** Because the update is a reified operator, the system can bound `learn` with a runtime invariant: a verified-accuracy floor plus a promotion gate (`admit`) that accepts a rewritten operator only when it is non-inferior on held-out outcomes. The curve can bend up but not down past the floor — and the same reification that lets the system learn lets it *prove* it hasn't degraded. Safety and compounding rest on the same substrate — reification — rather than trading off against each other.

**Example.** A poisoned run of feedback is caught two ways: the promotion gate rejects any batch that fails holdout non-inferiority, and the invariant auto-pauses learning if rolling verified accuracy falls below its own baseline; learning resumes from the last good operator. (Honest boundary: under the worst adversarial operators a characterized fraction of runs still fail to recover — the bound is real, not absolute.)

**Before → After.** *Before* — online self-modification risks silent degradation, so you daren't let a production system rewrite its own decisions. *After* — self-modification is bounded and auditable, so a system that learns in production is deployable.

**Falsifiable if** adversarial batches slip past the gate and degrade the system undetected, or if enforcing the bound suppresses the compounding — if safety and learning trade off rather than coincide.

**Deployed, not proposed.** H-BOUND is the one depth-safety claim already running in production: the conservation-law invariant (α·q·V ≥ θ_min, auto-pause on violation) is deployed across all copilots (the LearningHealthMonitor runs live; SDK safety track complete, SOC track through its diagnostic gate at 250/250), and the characterized adversarial non-recovery rate is from live simulation. The reification principle is **recursive**: reification enables learning, enables *bounding* learning (H-BOUND), enables *bounding claims about* learning — a deterministic treatment/control holdout, persisted to the decision node, with an accuracy guard (treatment ≥ control) that prevents the perverse case where showing context makes decisions worse. (Deployed status confirmed by the June closeout; the holdout writes treatment/control flags today but is **pilot-gated** — it is not yet producing measurable effect data because there are no real analysts. The *instrument* is deployed; the *measurement* awaits real use.)

**Consequence — the instrument is the asset.** A system that can *measure* its own learning effect and *prove* it has not degraded holds a stronger position than one that merely claims improvement — even if the measured effect is zero, the measured zero is honest and the unmeasured claim is not. The auditability H-BOUND enables is itself the moat, which reframes self-modification from "risky but powerful" to "auditable and therefore deployable." *(Attribution: the deployed-status and holdout details rest on the project's production/companion work, surfaced in external review; stated here as project fact, not re-derived.)*

*Field impact — high (safe self-modification is the capability the field most wants and least trusts). · Reachability — medium (simulation-legitimate; the honest negative — a fraction never recover — is a feature). · Portability — high (a runtime invariant + gate any online learner can adopt). · Defensibility — medium (defend on the characterized failure rate, never as an absolute guarantee).*

---
---

## Breadth engine — coalescing context *(the `enrich` and `merge` operations)*

*Breadth raises the level and broadens coverage: it starts the graph higher on day zero and warmer on each new domain, and it is applied whenever new context arrives. The claims here are breadth's day-zero and cross-domain lift, and its coupling to depth — not super-linear returns to breadth itself.*

## H-ENRICH · `enrich` is a second engine, working before any outcome exists *(claim about `enrich`)*

**Claim.** Verified outcomes are slow and absent on day one. `enrich` — folding continuous, high-volume, *unverified* context into the graph and fusing many observation streams by learned *source*-reliability (which feed to trust — a graph-object distinct from anything the invalidated kernel weighed) — is a second learning curve that lowers decisions-to-competence from the start, and it *feeds the depth engine*: a richer, better-contextualized graph gives `learn` cleaner geometry to move. It stays firewalled from the verified-outcome signal, so it improves context, never ground truth. Enrichment is a **leveling** engine, not a compounding one: it raises the floor, it does not bend the curve — the coupling runs one way, breadth feeds depth, and breadth itself does not compound.

**Example.** On day zero a security graph has no confirmed decisions to learn from, but enriching it with vendor-master, threat-intel, and org-chart streams — each weighted by how reliable that source has proven — lets it make sensible first calls instead of guessing. The coupling is measurable: enrichment that adds a cleaner factor gives the decision geometry better-separated prototypes, lifting day-one accuracy — while leaving the convergence *rate* unchanged (enrichment changes the substrate, not the learning speed). That clean split is the honest boundary. (Note: this coupling no longer runs through the reliability-metric — H-KERNEL invalidated that — but through context/geometry quality.)

**Before → After.** *Before* — the system is blind until labels arrive. *After* — it starts competent on decision one, on a fast unverified curve alongside the slow verified one, with the two curves coupled through context/geometry quality.

**Validated instance — temporal enrichment (CONTINUES).** Edges that link today's campaign to yesterday's ("day 5 of an ongoing incident, 23 total alerts") coalesce campaign **state** as richer context — not decision **geometry**. That places them squarely in the breadth engine (context assembly, leveling), *not* in H-COALESCE (geometry coalescing, compounding) — the same leveling-vs-compounding line the thesis draws. Reported validated (category/entity match, temporal order, zero duplicates) in the project's SOC work; cited here as a concrete H-ENRICH instance, with the geometry-coalescing claim (H-COALESCE) still proposed.

**Falsifiable if** enrichment fails to lift the day-zero curve, or only helps by leaking into the verified signal — in which case it is not a second engine but a contamination of the first.

*Field impact — high (answers the cold-start / zero-day problem, and couples the two engines). · Reachability — medium (partly evidenced; source-fusion is the harder part to isolate). · Portability — med/high. · Defensibility — medium (the firewall is what keeps it honest; state it explicitly).*

## H-COALESCE · `merge` coalesces trust, not just data *(claim about `merge`)*

**Claim.** `merge` combines two graphs — and, because computation is reified, *their operators* — into one substrate. The novel content is not merging nodes (folklore) but **coalescing the learned decision geometry**: prototype positions accumulated in one domain warm-start a connected domain, so the combined graph reaches competence faster than cold. The *direction* re-grounds cleanly — geometry (Phase-1 centroids), not reliability-weights (Phase-2, firm-specific, −5.6pp, and invalidated anyway per H-KERNEL): what coalesces is geometry, what does not is the kernel. **This is an ahead-of-code claim — validated by a fresh experiment, not by legacy evidence.** The number it used to cite, the +28pp cross-deployment transfer ("K19"), is *dropped as an anchor*: its data type, methodology, and output location are all undetermined, it is not in the ~180-entry experiment record, and it cannot be regenerated — and the same centroidal-synthetic circularity that killed H-KERNEL cannot be ruled out for it. So K19 does not appear in the draft. Instead, H-COALESCE is validated the way H-CURVE is being cleared: a **fresh oracle-separated cross-deployment experiment** (candidate basis: the V-CGA-FROZEN oracle-separated line, whose cross-deployment variant would test geometry-coalescing on non-centroidal data). Status: **proposed, direction-sound, ahead of the code — a first-class forward claim, not a deprecated one.**

**Example.** Merging a security graph and a fraud graph (given the entity correspondence that ACCP supplies): decision-prototype geometry learned on the security side warm-starts fraud decisions on shared factors, so they reach competence faster than cold. What coalesces is the *decision geometry*, not merely the shared entities.

**Before → After.** *Before* — N domains are N systems with N separate geometries; a new domain starts cold. *After* — one substrate in which learned geometry coalesces, and a connected domain starts warm.

**Falsifiable if** merged geometry is no better than independent per-graph geometry, or if the lift is recoverable by naive feature-sharing with no operator coalescing. (Three things this claim is *not*: not cross-graph relation-*discovery* — that arm is dead, dot-product and pair-count-bound; not entity resolution — the correspondence is interpretive and supplied by ACCP, not decided by `merge`; and not ordinary transfer learning — the claim is that inspectable decision geometry coalesces *additively as graph operators*, not that a shared representation is fine-tuned into a new task.)

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
- *Geometry (depth) compounds along hops* — a per-hop mis-placement propagates, so the value of well-learned decision geometry grows with depth; a cold graph's errors compound most on long paths. (Not a kernel claim — H-KERNEL is invalidated; this is about geometry quality along the path.)
- *Learning (H-CURVE) needs path credit* — the curve bends at the process level only if credit reaches the operators at each hop, not just the terminal; that is the multi-hop credit-assignment condition.
- *The bound (H-BOUND) must span the path* — non-degradation is a property of the whole traversal, not one step.
- *Breadth enables depth* — `enrich` and `merge` are what let a path cross domains at all; a cross-domain hop is only possible on a coalesced substrate.
- *Inspection (H4) and judgment memory (H3) become path-level* — explaining a multi-hop decision means reading the whole traversal, and what judgment memory records is the per-hop operator changes along it.

**Example.** A security decision that looks benign in isolation becomes an escalation after three hops: score the alert (near-threshold) → an enrich-hop pulls in threat-intel context that raises asset-criticality → re-score → a merge-hop into the identity graph, where the account's privilege recently changed → final score crosses the escalation boundary. At each hop the reified geometry decides what to attend to next; a mis-placed early prototype would have terminated the path at "benign." Learned geometry matters *more* here than in any single score, because its errors compound over three hops.

**Before → After.** *Before* — multi-hop reasoning is a black-box chain (LLM-agent hops, or hand-built traversal) whose errors and rationale are opaque and whose learning is terminal-only. *After* — each hop is a reified, inspectable decision with its own learned geometry, credit reaches every hop, and the path's degradation is bounded end-to-end.

**Status (partial).** Data hops are traversable in the graph today, but a composed multi-hop *decision process* is assembled in code, not reified as a process object the system can read back whole. So the process-level *claims* are testable now; the *substrate* form — the path itself as a graph object — is proposed.

**Falsifiable if** the single-hop advantages do *not* amplify with depth — if well-learned geometry helps no more at k=5 than at k=1, if per-hop error doesn't propagate, or if terminal-only credit bends the curve as well as per-hop credit. Then multi-hop is just repeated single-hop and the meta-claim is false.

*Field impact — high (multi-hop reasoning is where the agent/GraphRAG energy is, and where opacity and error-compounding bite hardest). · Reachability — medium (depth-sweep experiments: vary k and measure whether each advantage scales with depth). · Portability — high (the dimensions apply to any graph decision process). · Defensibility — medium (must show amplification-with-depth, not assert it; nearest prior art is multi-hop QA / knowledge-graph reasoning and RL credit assignment).*

---
---

## Consequence — the graph is inspectable *(the `read` operation)*

## H4 · Reading the operators explains the decision *(claim about `read`)*

**Claim.** Because the operators are (or can be) objects in the graph, `read` explains a decision by *traversing* it — interpretability is structural, and in this regime a closed-form geometric scorer matches learned embeddings or a GNN with no training step and no black box. (Status: decisions and their context are already read from the graph; operator-level explanation — reading the decision geometry as graph nodes rather than reconstructing it from the scorer's state — is the reification target, not yet the implementation.)

**Example.** "Why did you escalate this?" is answered by reading the factor-nodes that crossed threshold and the prototype geometry the decision was scored against — a traversal of the actual decision — rather than a post-hoc SHAP approximation of an opaque model.

**Before → After.** *Before* — reach for a GNN, pay training cost, lose interpretability. *After* — closed-form scorer in the stated regime; no training, and the decision's factors, thresholds, and prototype geometry are inspectable by reading the graph.

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

**Lineage and absorption.** This pre-paper is the thesis for the *next version of the distance-kernel / cross-graph math paper* — a significant upgrade on the same arXiv lineage, so accumulated outreach and citations carry forward rather than restarting. It **absorbs the production/architecture companion paper's dynamics-and-safety material** (the conservation law becomes H-BOUND's runtime bound; adversarial robustness, defense-in-depth, and James-Stein its characterized safety). The two prior papers overlapped ~70% (kernel, theorem, judgment memory, conservation law); the reification-plus-operations spine is what lets that union read as one argument rather than two near-duplicate papers. The `enrich`→depth coupling is already partly evidenced in the prior work (enrichment lifted day-one accuracy with a clean null on convergence rate); its mechanism is re-stated as context/geometry quality, not the invalidated metric reweighting. Landmark results that earned the prior outreach stay visible, but their status is corrected: the kernel-choice finding (EXP-C1) and the reliability-weighting curve (UNI-DK-01) are now reported as a **de-circularized NEGATIVE** (H-KERNEL — the advantage is a scaling artifact on real data); the **re-convergence theorem is the spine** (H-CURVE, pending its own de-circularization); and judgment memory (H3) re-grounds on centroid geometry. **Inclusion rule:** every section must serve "self-computing graphs that coalesce context and compound from verified outcomes," or it is cut or sent to the ACCP paper.

**Code status — informational only (from the DataOps reification scan).** The one-line finding: **state is reified, computation is not — yet.** Operator *state* is graph-persisted and readable back (centroids and reliability-weights, verified outcomes, enrichment nodes with source links, promotion/conservation records); the *operators* — the metric, the update rule, the merge, and operator-level explanation — still execute in code, and no graph node represents the update rule acting on itself (closure is external). This sets phrasing only, never acceptability. Per-claim, from the scan:
- *Implemented-partial (persisted, inspectable state):* H3 (judgment memory queryable), H-KERNEL's persisted *state* (centroids), H-ENRICH (enrichment + source links written), H-BOUND's gate *state* (promotion/conservation records), H4's *data* half (decisions + context read from the graph), H-CURVE's learning *artifacts*.
- *Proposed (design-only in code):* executable closure (the strong form of S), operator-aware `merge` → **H-COALESCE not found in code**, the reified multi-hop *process object* (strong form of H-MULTIHOP), and operator-node explanation (strong form of H4 — trust/metric explanation is currently reconstructed from the scorer's state, not traversed).
The metric, scorer, theorem, two-phase learning, and conservation gate also exist as prose and code in the prior papers/experiments repo; they are rebuilt fresh for any clean test. The paper's claims rest on new, mostly public-data experiments.

**Evidence status — post-invalidation (this is the load-bearing appendix note).** The claims are NOT co-equal:
- **H-KERNEL — INVALIDATED on real data.** The kernel/reliability-metric advantage is a scaling artifact; de-circularizes EXP-C1 and UNI-DK-01. Cited as a negative, not a pillar.
- **H-CURVE — the spine, PENDING de-circularization.** The re-convergence theorem is θ-independent and analytically proven (four paths), but its simulations may share the centroidal-synthetic circularity that sank H-KERNEL. Must pass a γ/re-convergence diagnosis + real-data run before it is claimed as proven-on-real-data. Until then: strong by theory, unverified on real data.
- **H3 (judgment memory) — structural, survives.** Re-grounded on centroid geometry; a taxonomy argument, not a metric-advantage claim, so untouched by the invalidation.
- **H-BOUND — survives.** Conservation-law + adversarial-robustness; about the update dynamics, not the kernel.
- **H-ENRICH — partly evidenced, coupling re-grounded.** Cold-start lift stands; the depth coupling now runs through context/geometry quality, not metric reweighting.
- **H-COALESCE — proposed, ahead-of-code (validated by a fresh experiment).** The geometry-not-weights direction is clean; the legacy +28pp/K19 anchor is *dropped* (undocumented, unregenerable, centroidal-circularity not excludable) and does not appear in the draft. Validated the same way H-CURVE is cleared — a fresh oracle-separated cross-deployment run. A first-class forward claim, not deprecated.
- **H-MULTIHOP — framework claim, proposed.** Tested via depth-sweep, not yet validated.
- **H4 — partial (per the reification scan).** Decision/context reads are real; operator-level (geometry) explanation is the reification target.
The paper must phrase each at its true status; the honest headline is *the kernel died, the geometry-compounding spine stands pending de-circularization.*

**Result states.** Every experiment returns validated / invalidated / inconclusive-underpowered. An invalidation is a first-class, citable result. An underpowered null is a to-do, not an invalidation.

**Draft-time ordering (a directive, not a change to this map).** This pre-paper keeps the *conceptual* order (substrate → depth → breadth → meta → consequence), with H-KERNEL shown in place inside the depth engine because it *is* a depth claim and the invalidation-in-place is the honest map. The *publication draft* should reorder to **lead with what survives** — H3, H-CURVE (the spine), H-BOUND (deployed) — and present H-KERNEL as "what we tested and corrected" *after* the reader knows what stands, so the negative reads as a contribution positioned within a strong structure rather than the first thing encountered. Ordering is a draft decision; the hypothesis set and their statuses are fixed here.

**Sequencing — logistics only, not a reason to reorder the argument.** H-KERNEL is **done — invalidated** (the de-circularized negative). The immediate next step is the **H-CURVE de-circularization**: a γ/re-convergence diagnosis of the prior experiments, then a real-data run — the spine cannot be claimed until it clears (it is where H-KERNEL was before *its* run). H4 (`read`) is the cheapest remaining public-data result. H-BOUND leans on the absorbed conservation-law/adversarial results. The breadth claims (H-ENRICH, H-COALESCE) and H-MULTIHOP follow; H-COALESCE runs only if a clean multi-graph benchmark exists.

**Method guardrails (hard-won).** For any temporal claim, measure convergence by distance-to-target, not threshold-crossing counts; 30+ seeds; isolate metric-learning from position-learning. For any surviving geometry/convergence claim (esp. H-CURVE), the decisive guardrail is **de-circularization**: run on non-centroidal / real data, never on blobs generated around the scorer's own centroids — the lesson H-KERNEL taught when its centroidal-synthetic ceiling collapsed on real data. Measure convergence by centroid-distance-to-target, not threshold-crossing counts. For H-BOUND, report the adversarial non-recovery rate honestly rather than claiming an absolute guarantee. For H-COALESCE, hold the interpretive step (entity correspondence) fixed and supplied, so the experiment tests operator-coalescing rather than entity resolution.

**Reproducibility guardrail (from the recompute attempt).** A result the paper relies on must be re-derivable from artifacts persisted in the accessible repo — not from an external drive or a one-time run whose outputs weren't saved. The γ-audit's headline numbers could not be recomputed because the vectors, centroid snapshots, and distance trajectories were not persisted where the tooling can read them. Before any such result appears in the draft, its underlying artifacts must be committed (or the result regenerated by a reproducible script). This is the operational companion to de-circularization: a result must be both non-circular *and* re-openable.

**Reproducibility inventory (from the source session).** Where each evidence class stands:
- *Regenerable (code + params documented, artifacts must be persisted on re-run):* the γ oracle-separation runs (H-CURVE) — via `OracleSeparationExperiment` on parametric vectors; V3A/V3B; bootstrap calibration.
- *Committed (in repo or project docs):* the code (`gae/synthetic.py`, `gae/convergence.py`, ProfileScorer, conservation law) and the equation/results write-ups (math_synopsis, production paper, arxiv draft).
- *Location-unknown outputs (documented method, outputs on an external drive / Colab, not in repo):* γ-audit result files (7), V-MV-KERNEL-HET, UNI-DK-01, B5B-PROXY, V-CGA-FROZEN — regenerable from documented method if needed.
- *Dropped (unverifiable legacy):* **K19 (+28pp / −5.6pp transfer)** — no documented methodology/data-type/location, not in the experiment record, unregenerable, centroidal-circularity not excludable. Dropped as evidence; H-COALESCE is validated by a fresh oracle-separated run instead. **Blast radius (confirmed):** K19 is the *same* measurement as the prior math paper's two-phase "+28pp means transfer" — so the cga v8 upgrade must re-verify or re-frame that two-phase citation too, not only H-COALESCE. A second upstream defect for cga v8: `synthetic_data_generation_v2.md` states the re-convergence threshold in a pre-cancellation form, `ε★ = α·‖Δ‖·θ/(θ−(1−α))`, and claims ≈0.128 — but that expression evaluates to ≈0.387 with the standing inputs (α=2/6, ‖Δ‖=0.25, θ=0.85). The correct θ-cancelled form is `ε★ = (α·‖Δ‖)/(1−α) = 0.125`, matching math_synopsis's "θ cancels" and the standing 0.125. A transcription error in the source doc — no effect on H-CURVE (the binary test is on the ε grid, not the formula), but it must be corrected in the upgrade so a reviewer doesn't hit a threshold that doesn't compute.
- *Not regenerable:* FX-1-PROXY-REAL — needs the external real-IOC dataset.
The bright line: any number that reaches the draft must sit in the regenerable/committed tiers. K19 does not — so it is dropped, and both H-COALESCE and the two-phase transfer claim get fresh, oracle-separated support.

**Identifiability guardrail (from the γ oracle-separation audit).** Synthetic data generated by an LLM-persona measures the *simulator's* competence prior, not the system's learning effect — an identifiability problem, not a prompt-engineering gap. Any experiment validating a learning or behavioral claim must use **oracle separation** (LLM generates inputs; a mathematical oracle labels correctness) or real data. LLM-persona data can substantiate *capability and mechanism*; it structurally cannot substantiate the *magnitude* of a behavioral or learning effect that depends on the real agent. This is the methodological companion to H-KERNEL's empirical negative: H-KERNEL says the kernel advantage is a scaling artifact on real data; the identifiability result says you cannot even test a behavioral-magnitude claim with synthetic agents.

**Evidence taxonomy (which generated data proves what).** Four kinds of data, with bright lines on evidential power:

| Kind | Data | Proves |
|---|---|---|
| K1 (oracle-behavioral) | parametric oracle | pipeline / safety |
| K2 (factor-vector oracle) | LLM inputs + mathematical oracle | mechanism |
| K3 (LLM-persona) | simulated agents | **nothing** — must not be cited as evidence |
| K4 (real external) | scraped/real data | context claims |
| T-R (real operational) | live pilot data | **magnitude** of learning/behavioral effects |

The bright lines: K1/K2 validate mechanism and pipeline, never magnitude; K3 validates nothing (the identifiability line above); K4 validates context; only T-R validates magnitude. Mapped onto this paper: H-KERNEL's invalidation used real UCI data (the decisive test); H-CURVE's γ theorem is K2 (mechanism) pending T-R via EXP-G1 (magnitude); H-BOUND's conservation is K1 (deployed); H-ENRICH's cold-start lift is mixed K4/K2. *(This taxonomy and the identifiability result originate in the project's substantiation work; included because they are the paper's own evidence discipline, and are a standalone methodological contribution the field needs.)*
