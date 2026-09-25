# VLD end-to-end architecture design — 2026-09-12

**Status: PROPOSED — design only; no implementation or new experiment result.**  
**Scope:** SDK, SOC, Trading, Purchasing, DataOps and S2P.  
**Decision:** one production scoring function, one immutable episode bundle, one investigation controller, domain-specific read/transform adapters, and a separately governed verified-feedback lifecycle.

This document assigns a single closing item to each of the audit's 16 P0 findings. Assignment is not closure: a finding closes only when its named acceptance evidence exists. Completing code also does not make an empirical claim true. Positive production claims remain conditional on independent, time-valid measurements; a negative result is an acceptable scientific outcome.

## 1. Problem statement

The comprehensive audit found that the factor-acquisition primitive works on constructed fixtures, while production scoring, pattern investigation, governance, persistence and verification do not form one validated chain. Its current reconstruction reports 14/15 fixture action-pair matches and 9/10 flips, with zero hurts **relative to planted labels**; that is not production accuracy or evidence of learned K. All five dedicated K tables were empty, all classifiers used heuristics, and the SOC public Stage1 path could select oracle branches and substitute oracle actions. These are the starting facts, not claims rerun by this design. [Audit, §§1, 7, 15–16](../quality/vld_comprehensive_audit_2026-09-12.md)

### 1.1 Authority and evidence conventions

The following files were read in full before design. References such as PAPER:139 identify actual source lines in this manifest; proposed APIs/files below are explicitly labeled NEW and have no existing-code line numbers.

| Alias | Workspace-relative source | Relevant anchors |
| --- | --- | --- |
| AUDIT | copilot-sdk/docs/quality/vld_comprehensive_audit_2026-09-12.md | 3–71 verdict/current reconstruction; 645–682 fix queue |
| PAPER | copilot-sdk/docs/design/ci_vld_architecture_prepaper_v8.md | 137–149 six claims; 152–219 RSI; 335–403 safety; 709–743 recursion; 1269–1287 K experiment |
| ARCH | copilot-sdk/docs/design/vld_graph_reasoning_architecture_v4.md | 52–108 placement/emit/credit; 179–254 score-keyed value gates |
| IMPL | copilot-sdk/docs/design/vld_implementation_design_v4.md | 181–263 loop/trace; 413–521 experimental qualifications; 876–908 proposed next steps |
| CORE | copilot-sdk/copilot_sdk/scoring/investigation.py | 52–188 scoring/Q/loop; 191–258 K |
| API | copilot-sdk/copilot_sdk/backend/investigation_router.py | 16–119 contracts/handler; 125–198 extraction |
| PROXY | copilot-sdk/copilot_sdk/backend/scorer_proxy.py | 31–84 scorer access/lock; 134–138 conservation |
| SOCLOOP | gen-ai-roi-demo-v4-v50/backend/app/services/investigation_loop.py | 47–148 complete episode; 157–170 action scoring |
| SWEEP | copilot-sdk/tests/vld_validation_report.py | 194–350 collector; 412–430 verdict |
| INTEGRATION | copilot-sdk/tests/test_vld_integration.py | 17–22 shared collector; 179–188 S2P exception; 227–244 robustness/parity |
| DEMO | copilot-sdk/docs/design/demo_scenarios_and_usecases_v2_8.md | 908–914 fixtures; 1014–1112 beats/guards; 1253–1258 Loom |

Additional code was inspected where needed: CompoundingScorer prediction, checkpoint/restore, learning/conservation; GAE scoring/calibration; outcome commit service; SA protocol; and outcome immutability policy. The audit's broader provider/UI inventory is retained as cited evidence, not represented as a new runtime test. No application modules were imported, no live AGE query was run, and no test/centroid export was executed in this design turn.

The architecture resolves conflicts explicitly:

1. Current executable behavior is evidence of what exists; historical experiments do not redefine that behavior.
2. ARCH's frozen episode, evidence-driven state, emit-only conservation and fair-comparator requirements govern the target.
3. PAPER's performance, learning and safety sentences are hypotheses or scoped results until supported by the appropriate evidence tier.
4. IMPL's dual-centroid proposal is a separate experimental arm, not a reason to silently change production action scoring.
5. Contradictory demo requirements require a versioned contract revision, not fabricated numbers or retrospective test expectations.

External research citations in PAPER were read as part of the repository document; their contents, novelty claims and interpretation of the RSI taxonomy were not independently verified in this task.

### 1.2 The 16 P0s to close

| Group | P0 findings | Required capability |
| --- | --- | --- |
| Episode integrity | F02, F04, F20 | Every attempted read persisted; bounded C4 halt; actual selection probabilities |
| Scoring and execution | F11, F13, F14, F26 | Production-equivalent scoring/contrast; no bootstrap substitution; emit authorization; no oracle access |
| Evidence and learning | F10, F15, F23, F30 | Count-derived, time-valid evidence; verified-feedback K; independent measurement; complete linked episodes |
| Verification | F31, F32 | Actual mounted-path equivalence and an independently authored acceptance contract |
| Presentation | F27, F28, F29 | Shared honest trace UI, four Loom manifests, reconciled five-beat contracts |

The exact P0 set is **F02, F04, F10, F11, F13, F14, F15, F20, F23, F26, F27, F28, F29, F30, F31, F32**. F01 is P1, despite being an important mathematical prerequisite. Several P1s are included in foundation work because omitting input, tenant, snapshot or deadline integrity would invalidate P0 closure.

### 1.3 What “production-validated” will mean

Use two independent labels, not the word “real” alone:

- **Execution fidelity:** SIMULATOR / REAL_COMPONENT / MOUNTED_APPLICATION / PRODUCTION_SHADOW / GOVERNED_EXECUTION.
- **Data and labels:** PLANTED / SYNTHETIC / OPERATIONAL_UNVERIFIED / OPERATIONAL_ADJUDICATED, with entity/time split and verification coverage.

A real scorer class on a synthetic vector is REAL_COMPONENT + SYNTHETIC. A real AGE server seeded with demo rows is still PLANTED. Restoring a production tensor does not turn 500 generated decisions into production experience. A human confirming a generated answer does not erase synthetic origin.

For this design, a production-validated mechanism requires the deployed path, captured deployment state, operational evidence with as-of provenance, durable episodes, independent outcomes, and a recorded evaluation scope. A production-validated **benefit** additionally requires improvement against the strongest eligible comparator at matched budgets with uncertainty and harm reporting. Neither a unit-test count nor a margin increase meets that standard.

## 2. Current data flow

This traces the common SDK endpoint first, then identifies the SOC/DataOps differences. It does not assume the sweep is the endpoint used by the UI.

| Stage | Existing component, input → output | What breaks / target requirement |
| --- | --- | --- |
| 1. Request | POST /api/investigation/investigate accepts decision_id, category, factor_vector, optional budget and use_K (API:16–21, 50–53). Pydantic requires nonempty strings/list; core checks vector shape and finiteness. | ID/category/vector are not bound to an owned stored decision. No semantic schema ID, numeric budget cap, provenance or vector authorization. Unknown category can score category0 while echoing the caller's value (API:152–167). A2/B4 bind identity and vocabulary. |
| 2. Scorer state | API:55–59 copies centroids, probes sigma/tau, builds a new VLDInvestigator. PROXY:31–41 lazily constructs CompoundingScorer. from_preset restores a compatible checkpoint or bootstrap (scorer.py:320–339); startup also restores DK, centroids and conservation (startup_restore.py:42–49). | Internal-attribute extraction loses effective metric/state. Sigma falls back to ones; tau to .1. GAE masks both vector and centroid and can use phase2 effective DK (gae/profile_scorer.py:447–488); SDK reproduces neither complete dispatch nor governance. A1/B4 resolve F11/F13. |
| 3. Situation | API:61–70 scores v0 and computes unweighted Q; classifier runs only if budget omitted. Heuristic returns S1/S3/S6; all five mains currently use no model (AUDIT:168–179). | Explicit budget removes situation/confidence from telemetry. K is not used in classification Q. No proof that current S1 is unambiguous or actual recommended budget satisfies narrative. Always assess; separately record and cap allocation. |
| 4. K read | API:73–75 reads category weights once. CORE:216–226 returns .5 for an empty store. Positive uniform weights preserve ordering. API:83 passes weights to loop, not the earlier classifier. | Five dedicated stores wired but empty; no production verified-outcome updater. Keys lack tenant/schema, updates are non-atomic read/modify/write. A1 freezes K; C1 governs learning. |
| 5. Loop | SDK CORE:124–180 chooses factor dimension, marks attempted, overwrites/blends coordinate and re-scores fixed-category actions. SOCLOOP:64–92 selects patterns, accumulates evidence and re-extracts; DataOps has its own maxima-based aggregation. | Three incompatible controllers; SDK drops None attempts and lacks residual/oscillation halt. SOC Stage1 defaults force_correct=True and can overwrite final action with ground truth (triage.py:483–499; multihop_scenarios.py:336, 385–392). B1/B3/B4 reconcile. |
| 6. Evidence | Each real provider returns value/confidence/source or None. SOC gates identity_graph/threat_intel; Trading correlation_engine/portfolio_engine; Purchasing vendor_tracker/lead_time_tracker; DataOps schema_registry/dependency_graph; S2P none (AUDIT:111–128). | Provider class does not establish live evidence. Registry/static fixtures dominate; some counts/defaults are misnormalized. Source-string gating is not source authentication. Errors become400/503 or None, and partial trace is lost (API:108–111). B5 typed evidence/normalization and B1 durable failure handling. |
| 7. Action/contrast | SDK all actions in selected category: diagonal squared-distance softmax; flip is argmax change, no minimum margin (CORE:66–81, 151–167). API:87–93 compares its own surface/final, calling larger margin “improved.” | Production metric differs; SOC initial/final confidence denominators differ. DataOps domain helper can substitute bootstrap (AUDIT:140–142). A1/B4 share kernel and compare identical snapshots; no correctness label before adjudication. |
| 8. Conservation | Shared investigation never calls learn or action execution, and does not obtain conservation eligibility. SOC/DataOps report not_evaluated_read_only (AUDIT:143–154). | Read-only analysis under RED is legitimate. Returning a recommendation is not executing it, but there is no enforceable downstream eligibility contract. B2 adds it without using conservation as a per-step halt. |
| 9. Response | Shared response contains integer actions/margins, optional situation, successful steps and contrast (API:24–36). SOC/DataOps domain routes use different schemas. budget_used equals allocated budget. | No version/vocabulary/episode ID, full provenance, candidates, attempt status, cost, or eligibility. Not a durable E-1 trajectory. A2/A3/B1/B4 provide one envelope and aliases. |
| 10. Verification/reuse | No trajectory append in shared handler. K.update_weights exists, rewarding every successful read in a correct trace and extra reward for flips (CORE:228–258), but no production caller was found. | No outcome→episode→K causal chain, exact-once effect, tenant isolation or replayable state. C1/C2 implement it; terminal correctness alone is not step credit. |

**Current endpoint split:** all five use the shared SDK mount. SOC also exposes /api/soc/investigate, called by its InvestigationPanel; DataOps also exposes /api/dataops/investigate. S2P has no matching domain alias in the inspected current code. Evidence: AUDIT:104–106, 279–299; gen-ai-roi-demo-v4-v50/frontend/src/lib/api.ts:181; copilot-sdk/apps/dataops/backend/app/main.py:963–973.

**Current scorer path worth preserving:** CompoundingScorer.score and score_read_only both call _predict, which orders/defaults factors and delegates to ProfileScorer.score. score additionally persists a Decision. Investigation must reuse the prediction computation without calling the mutating persistence wrapper. Existing score_with_model_state is a useful ablation helper, not a complete frozen-bundle contract; it still references live configuration and calls _predict. Evidence: copilot-sdk/copilot_sdk/scoring/scorer.py:217–244, 385–399, 475–550.

## 3. Pre-paper claim requirements

Throughout this document **C1–C6 mean the six claims in PAPER §0.9**, not its later Contributions numbering. Those two lists differ: §0.9 C5 is K learning; Contributions C5 is safe centroid learning. L1–L4 use the paper's own operational interpretation of the RSI ladder; this design does not certify an external taxonomy.

### 3.1 Six-claim mapping

| Claim and paper line | What must exist | Current status and blockers | Evidence required, beyond architecture |
| --- | --- | --- | --- |
| C1: scorer geometry plans graph reads; 2/6 at “85%” of exhaustive, zero additional models (139) | Production metric snapshot; explicit factor→eligible graph-pattern mapping; metered selective reads; baseline from identical snapshot | PARTIAL factor primitive; F02/F10/F11/F13/F23/F30/F31. Current Q is additive, not the first paragraph's precision×discriminative formula. | Operational topology and read-cost traces; matched-budget best-rule/breadth comparisons. .872/.912 is about95.6%, not85%; preserve raw dataset numbers with correct denominator only after reproducing their source. “Zero additional models” may describe the base planner, not a deployed learned situation classifier. |
| C2: sequential Q recomputation captures conditional dependencies, +4.8%, priorities change30–60% (141) | One stateful-within-episode controller; frontier/prerequisites; recomputation after actual evidence; trace of alternative priorities | PARTIAL; SDK recomputes but scalar fixtures are not proof of conditional graph branches. F02/F04/F11/F20/F23/F26. | Independently adjudicated within-category conditional cases; static versus adaptive routing with same reads available/costs; terminal utility and branch metrics separately. |
| C3: routing determines constructive/destructive compounding, 57:0 and simulation gaps (143) | Verified episode/vector linkage; common learner; separate routing×learning arms; safety gates; no synthetic/oracle label leakage | MISSING end-to-end evidence; F11/F14/F15/F20/F23/F26/F31. Human labels and directed routing do not guarantee absence of poisoning. | Fresh sequential operational outcomes, matched learning schedules and 2×2 factorial evaluation; uncertainty for both harms and interaction. Fixture57:0 cannot establish a universal prerequisite for safe learning. |
| C4: learned classifier before every read assigns budget/type;47.7%,1.80 hops (145) | Signed model/version and feature contract; assessment even with explicit budget; deployment calibration and resource allocation | PARTIAL heuristic objects; no model loaded. F04/F11/F23/F31 plus F05/F17/F33. | Domain/time/geometry-held-out situation and action-quality evaluation; exact fixed-budget comparator. Uniform six-class chance is1/6, not20%; class-prior random and majority baselines must be computed explicitly. .880 versus .888 does not by itself prove “no accuracy loss.” |
| C5: cross-decision K improves with every verified decision; per-category deployed memory (147) | Canonical verification event→eligible episode→credit estimator→atomic bounded K candidate→governed activation→later episode | MISSING production lifecycle; F02/F14/F15/F20/F23/F31/F32. Injected K=6 cannot arise through current cap3. | K checkpoint lineage and changing later routes establish structure; an independent matched-budget holdout with a fixed-K control must establish benefit. No guarantee of improvement after every update. |
| C6: graph reasoning rather than engineering compounds;67% wasted traversals (149) | Operationally grounded C1/C2/C5; separated graph-quality and policy-learning interventions | MISSING universal support; F10/F15/F23/F30/F31. Better ingestion/entity resolution can also improve decisions over time. | A bounded claim about this evaluated acquisition policy, not that no graph-engineering system can learn. Estimate neutral/misleading fractions from the measured deployment; do not assume67%. |

The Contributions paragraph C1 at PAPER:227–236 corresponds to architecture C1; Contributions C2:238–247 mixes architecture C1/C2 empirical routing comparisons; Contributions C3:249–255 corresponds to C2; Contributions C4:257–264 to C4; Contributions C5:266–278 to C3; Contributions C6:280–292 to C6. Apply revisions to both lists rather than leaving conflicting claims.

### 3.2 RSI, safety and recursion requirements

| Requirement | Production evidence means | Current evidence / minimum change |
| --- | --- | --- |
| L1 prescribed improvement (PAPER:162–168) | Mounted operational request acquires evidence and produces the true computed output, later linked to an independently verified outcome; “improvement” measured, not inferred from centroid proximity | Fixture/component tests only for the audited VLD acceptance chain. A+B+C2/C3/C4 supply instrumented production shadowing. A human sign-off may verify a case; a test invocation alone does not. |
| L2 strategy selection (170–177) | Policy varies acquisition based on observable state, obeys budgets and outperforms eligible alternatives in its declared regime | Recomputing Q exists; deployed classifier is heuristic. A+B and C2/C3 establish fixed-policy L2 evidence; C6 required for a learned-classifier deployment claim. |
| L3 acquisition experience (179–197) | Actual verified episodes change an active K version that later requests use; independent prospective results show whether this improves future acquisition | Custom-K intervention and simulation do not demonstrate the lifecycle. C1+C2/C3/C4 needed. A K store alone is not self-improvement. |
| L4 deployment adaptation (199–203) | A bounded pattern-policy candidate is proposed, evaluated, promoted and possibly rolled back in a real deployment, with identifiable effect | Architectural claim only. Optional C5 extension after core evidence gates; never present architectural wiring as production benefit. Cross-copilot K transfer requires explicit semantic alignment and its own trial. |
| L5 exclusion (205–218) | Runtime cannot alter its objective, verifier, operators, pattern structure or policy code; promotion operates on a signed allowed parameter schema | Preserve and enforce N3 via capabilities in A2/B2/C5. Exclusion is a security/governance property, not a measured intelligence claim. |
| Safety1: self-poisoning / safe inheritance (353–373) | Trusted, durable outcome provenance; invalid/unverified inputs excluded from learning; bounded candidate updates, held-out regressions, independent gate and rollback | Partial ordinary learning gates exist, VLD emit/K chain absent. B2/C1/C2/C3; can mitigate risk, cannot mathematically exclude all human error, biased verification, compromised sources or label poisoning. |
| Safety2: autonomy attribution / Guards (380–389) | Schema-enforced origin/measurement status and a shipped UI that actually renders required labels | Missing badges and shared panel; A2/C4/D1/D3 enforce. Claim cannot be upgraded by documenting the guard alone. |
| Safety3: reliable verification / Astra tiers (396–403) | Independent oracle, sealed holdout, non-oracle mounted runtime, matched state and reported missing/failing cases | Synthetic benchmark + shared collector tests are useful but not independent operational proof. B3/C2/C3/C4. |
| Structural recursion (716–719) | Retained K version derived from committed outcomes is reused after restart in a later episode; changes are lineage-linked | Not established by empty stores/injected vectors. C1 lifecycle gate suffices for a scoped structural claim even if quality remains flat. |
| Effective recursion (721–735) | Updated mechanism beats round0 under matched budgets and a frozen independent holdout, with uncertainty | Not established. §5.5 narrates a result that §10.4 explicitly calls a placeholder. C3 experiment may yield positive, null or negative results; code completion is not the acceptance test. |

### 3.3 Corrections that must accompany the design

The following are **exact proposed replacement passages**, for a future paper revision; this task does not edit the paper.

| Location | Proposed replacement text |
| --- | --- |
| §0.9 introductory qualification | “The following are architectural hypotheses and scoped experimental findings. Existing simulations and planted benchmarks do not establish production benefit. Production claims require the versioned scorer, episode, verification and deployment evidence specified in the end-to-end VLD design.” |
| §0.9 C1 mathematical description; §3.3 | “The deployed legacy acquisition heuristic is additive: precision/100 + centroid separation + state-dependent distance contrast, multiplied by category-specific K when supplied. The end-to-end design versions an effective-metric variant separately. Neither heuristic is an exact value-of-information rule. Performance results are attributed to their actual policy and data versions.” |
| §0.9 C3 and Contributions C5 universal-safety conclusion | “In the reported controlled experiments, routing policy changes the effect of centroid learning. This motivates testing routing and learning jointly under matched conditions; it does not establish that directed routing is universally necessary or sufficient for safe learning.” |
| §0.9 C4 deployment statement | “A random-forest situation classifier was evaluated on generated scenarios. The inspected application mounts use a heuristic fallback. Deployment accuracy, budget savings and action non-inferiority remain to be measured on held-out operational episodes.” |
| §0.9 C5 deployment statement | “K is a bounded, category-specific acquisition-memory mechanism. Simulation validates an update mechanism; the production verification-to-K lifecycle and prospective benefit are not yet established. Informative updates may improve later routing, but improvement after every verified decision is not guaranteed.” |
| §0.9 C6 and Contributions C6 | “Graph quality and learned acquisition policy are complementary. VLD tests whether retained decision experience improves which eligible evidence is acquired under a constrained budget. Claims are limited to the evaluated policies, graph snapshots and deployments; graph engineering is not assumed incapable of learning or compounding.” |
| §0.10 “CI occupies L1 through L3 with production evidence” | “CI has component and fixture evidence for prescribed investigation and geometry-conditioned strategy selection. L1–L3 production validation is pending: L3 additionally requires a verified-feedback K lifecycle and evidence that its retained state improves later routing. L4 remains an architectural extension; L5 self-modification is excluded.” |
| §0.10 L4 template promotion / cross-copilot transfer | “L4 remains architected. The initial optional extension permits governed adaptation of a bounded numeric acquisition-policy configuration. Autonomous promotion of new pattern structures and cross-copilot K transfer are separate, unevaluated extensions; they are not established by the initial E2E phases.” |
| §1.4 “self-poisoning vector ... architecturally excluded” and “governed fix” | “Verified-outcome grounding, bounded promotion and conservation eligibility reduce specified feedback risks. They do not eliminate incorrect human labels, selective verification, source compromise or distribution shift. The architecture isolates synthetic labels and oracle controls from production learning and separately measures harmful updates.” |
| §1.4 Guards enforcement paragraph | “The ten VLD Guards are requirements. Their production enforcement is pending the versioned episode API, shared trace panel and claim-manifest gates. Current fixture surfaces must retain planted-origin and unmeasured-routing labels.” |
| §1.4 verification tiers paragraph | “Simulation, generated domain benchmarks and real-component fixture tests are distinct evidence tiers. Production validation additionally requires actual mounted routes, operational as-of evidence and independent adjudication. Shared implementation helpers can support consistency testing but cannot provide an independent numerical oracle.” |
| §3.5, §7.2–7.4 conservation/SA wording | “Conservation supplies frozen eligibility at emit; it neither allocates investigation budget nor halts individual reads. The situation assessor recommends a resource budget and has no conservation override. A separate executor may deny a stale or revoked authorization without changing the episode's frozen scoring trajectory.” |
| §5.5 effective-recursion paragraph | “Effective recursion remains unmeasured on operational data. Section10.4 specifies a prospective comparison of retained K checkpoints with a fixed-K control under matched budgets. No routing improvement is claimed until that experiment completes on an independent holdout.” |
| §10.4 metric and expected-result paragraphs | “Nonempty-read rate measures availability, not routing correctness. Report it separately from adjudicated branch utility, action utility, saves, hurts and costs. The initial K0 snapshot plus checkpoints50 through500 yields eleven evaluation snapshots. A20–30% improvement is a hypothesis, not an expected acceptance target or an observed result.” |
| §11 S2P-SC2 “learned K ... 6.0 ... after250” | “The current S2P-SC2 comparison is a custom-weight routing intervention. It is not evidence of250 production learning updates: the normal K updater caps weights at3.0. A learned-routing demonstration requires reachable weights generated by the verified-feedback lifecycle and a recorded checkpoint lineage.” |

Additional source-grounded corrections belong in Phase A:

- PAPER §2.4 says a constant floor23.53 with α as autonomous-action rate and q as a400-decision window (464–481). Current GAE computes theta=23.53/(αV), compares αqV to theta, and derives α from category coverage and q from supplied correct/verified counts (graph-attention-engine-v50/gae/calibration.py:194–248, 440–474). The SDK learn gate also has a separately configured recent-quality check and dispersion adjustment (scorer.py:2243–2299). These are **not the same equation or inputs**. The design preserves a versioned executable compatibility policy; changing the scientific law requires its own reviewed migration, not a VLD-specific implementation of paper prose.
- PAPER §2.6 and §10 use obsolete S2P/Trading/Purchasing dimensions/actions (499–505, 1198–1205, 1243–1249). Current audited shapes are SOC6×4×6, DataOps6×5×6, S2P5×5×8, Purchasing5×4×7, Trading5×4×10 (AUDIT:43–49, 111–117). Experiments on old shapes remain old-shape experiments; they cannot be relabeled current production.
- RNN/LSTM are metaphors for within-episode recurrence and cross-episode memory here, not claims that deployed recurrent neural networks exist.
- A learned situation model and a learned K vector are additional learned artifacts even when the acquisition equation itself needs no separately trained router. State exactly which “zero additional model” claim is intended.

## 4. Target architecture

All interfaces, schemas and policies in this section are **proposed**. Existing pieces are cited to distinguish reuse from implementation work.

~~~mermaid
flowchart TD
    Request["Authenticated decision request"] --> Bind["Bind stored decision, tenant, schema and as-of time"]
    Bind --> Snapshot["Immutable episode bundle"]
    Snapshot --> Score["Production-equivalent pure scorer"]
    Score --> Assess["Situation assessment and budget allocation"]
    Assess --> Loop["One investigation controller"]
    Loop --> Select["Frozen policy over eligible SA read candidates"]
    Select --> Read["Metered domain evidence adapter"]
    Read --> Facts["Typed admitted facts with provenance"]
    Facts --> Extract["Pure evidence integration and re-extraction"]
    Extract --> Score
    Loop --> Ledger["Durable episode and attempt ledger"]
    Loop --> Halt["C4 / budget / deadline / terminal status"]
    Halt --> Emit["Frozen eligibility and faithful contrast"]
    Emit --> Result["Persisted response / trace panel"]
    Result --> Executor["Separate authorized executor with revocation check"]
    Result --> Verify["Independent canonical outcome commit"]
    Verify --> Credit["Replay-based credit estimator"]
    Credit --> Candidate["Bounded K / model candidate"]
    Candidate --> Promote["Governed evaluation and atomic release"]
    Promote --> Snapshot
~~~

The drawing describes different invocations of the scorer around a bounded loop; it does not imply recursive unbounded service calls. The loop never learns or executes actions. Its orchestration writes only the audit ledger, not μ, K, the evidence graph or the active policy. AGE trajectory projection and verified-feedback mutation occur outside evidence acquisition.

### 4.1 Decision Q1 — One production scoring computation

**Decision.** Extract one pure prediction function from the GAE ProfileScorer.score computation and use it for ordinary production prediction, VLD intermediate/final scores, and the single-pass contrast. CompoundingScorer remains the owner of Decision persistence and verified learning; the predictor has neither capability. This is a refactor of the existing kernel dispatch, not another hand-written NumPy scorer.

**Existing:** _predict→ProfileScorer.score and the read-only wrapper already share computation (scorer.py:217–244, 475–498); GAE applies masks, phase2 shrinkage and kernel selection (profile_scorer.py:447–488). SDK VLD and domain loops are divergent consumers.

**Proposed interface:**

~~~python
# NEW contracts; exact modules are assigned in §5.
predict_from_snapshot(
    model: ModelSnapshot,
    factors: FactorState,
    category_id: str,
) -> Prediction
~~~

Input invariants:

- Tenant/domain/category, action order, factor IDs, units/scales, missing-value policy and schema hash match exactly.
- Finite arrays; d>=1; at least two active actions for VLD; finite positive temperature. Invalid state is an explicit unavailable model, not category0/bootstrap.
- Model contains the actual kernel and effective parameters. It supports the production computation rather than assuming diagonal weights.
- A production default such as missing factor=.5 is preserved only through a named imputation policy and missingness metadata; it is not treated as observed evidence.
- Factor quarantine is reproduced exactly. Current multiplication of vector and centroid by mask means a diagonal squared-distance effective coefficient includes mask², not mask once.

Output Prediction contains category_id, action_id and action_index, ordered action vocabulary, probabilities, distances, p_max, top-two probability gap, entropy, effective metric ID, model hash and any domain decision-policy result. UUID generation and wall-clock calls are outside this pure output. All action probability normalization is within the declared category; no flattening across all category/action cells.

For diagonal/L2 mode, the effective metric can be represented as:

~~~text
D_a(v) = Σ_k ω_k (v_k - μ[c,a,k])²
ω_k = effective_kernel_weight[c,k] × factor_mask[k]²
P_a = softmax(-D_a / temperature)
~~~

The engine must reproduce the actual GAE floor/shrinkage behavior; it must not multiply learned weights by 1/sigma² a second time. For cosine, dot or full covariance kernels, scoring still uses the shared kernel. The initial geometric acquisition policy supports only diagonal/L2 snapshots; unsupported kernels receive an explicit non-VLD fallback, not an unreviewed “equivalent sigma.”

**Category versus branch.** For the primary paper arm, category is validated, externally assigned and frozen. Hypothesis/branch IDs are separate from score categories. The scorer returns an action; it does not secretly infer a new alert category. Within-category factor contributions can rank auth versus process evidence. If category is unknown, run the existing category-assignment policy as a separately logged initial stage, or refer; never use nearest-category distance as an invisible replacement.

A dual-routing-centroid arm is permitted only as an explicitly versioned research policy with its own routing-model provenance. It shares the same **action** predictor with every arm. It cannot claim “full production parameter reuse” or “zero additional learned routing artifacts,” and the synthetic dual-centroid result in IMPL:454–509 is not a universal proof that one tensor is insufficient.

**Closure/enabling:** A1 is the prerequisite; B4 closes F11/F13 after actual endpoint parity and contrast tests. Enables architecture C1/C2/C3, L1/L2, and honest K attribution.

### 4.2 Decision Q2 — An immutable, coherent episode bundle

**Decision.** Capture a release bundle once before classification or evidence reads. Never expose mutable scorer objects to the controller. A copy of μ plus separately read K and sigma is insufficient.

~~~python
capture_episode_bundle(
    identity: AuthorizedIdentity,
    decision: BoundDecision,
    as_of: EvidenceCutoff,
) -> EpisodeBundle
~~~

| Bundle component | Required fields / meaning |
| --- | --- |
| Identity and decision | tenant_id, domain_id, decision_id, decision_version/hash, original scored-action reference, category_id, factor_schema_id, source evidence origin |
| Model | immutable μ tensor, category/action/factor vocabulary, effective per-category metric or complete kernel state, masks, temperature, phase/shrinkage inputs and effective outputs, imputation/extractor version |
| Sigma provenance | observed noise estimate if available, estimator/window/version/sample count; separately sigma_effective=1/sqrt(positive effective weight) if representable. Masked zero-weight factors use an explicit inactive flag, not infinite JSON numbers. “Unit/L2” is labeled, never described as learned sigma. |
| K | bounded values, immutable K version/hash, schema/category key, update/verification watermark, learning policy and source-policy versions; EMPTY_UNIFORM versus unavailable versus trained |
| Governance | raw inputs, definitions, counts, windows, recent-quality/dispersion/regime overlays, resulting statuses and allow decisions, policy hash, evaluated_at, expiry/revocation epoch |
| Acquisition | candidate-catalog version, Q formula/constants, K policy, eligibility/prerequisite rules, tie policy, source gating, integration policy, C4/deadline/budget settings |
| Classifier | heuristic/model mode, feature schema, artifact hash and training geometry domain, budget mapping, calibration/abstention policy |
| Temporal state | evidence as_of cutoff, graph snapshot/version or committed watermark, per-source version support; decision cutoff and eventual outcome time are distinct |
| Release lineage | active_release_id, parent version, checkpoint IDs plus applied L5 versions, complete model hash, bundle hash, compatible component version tuple, capture time, code/config artifact IDs |

**Atomicity, including multiple workers.** Introduce a tenant/domain active-release manifest in the canonical state database. Learning prepares immutable model/K/policy artifacts and publishes their version tuple using compare-and-swap in one transaction. Artifact hashes are verified before publication. A worker reads one manifest and pins those artifacts; it may retain an old but unexpired consistent release, or reload. It may not combine the latest μ from one release with K or masks from another.

K may legitimately have been trained against an older compatible model; its training watermark and compatibility are explicit. “Coherent” means a deliberately published compatible tuple, not a false assertion that all components were learned from the same latest outcome. Incompatible metric/factor/source changes require reset, migration or shadow requalification.

Existing proxy/mutation locks protect in-process access only (PROXY:28–41; copilot_sdk/scoring/mutation_lock.py). During migration, capture under the same in-process lock used for learning and verify the canonical release version before/after copying. Final production acceptance requires all mutation paths to publish/reload through the release mechanism; an RLock alone does not solve multi-process or separate-database consistency. No lock is held across remote evidence I/O.

**Graph time.** A frozen scorer is not a frozen graph. Readers must use source versions and valid/observed/ingested time cutoffs. If AGE/source historical versions cannot be retrieved, capture returned facts and mark factual replay available but counterfactual as-of replay unavailable. Do not emulate historical state by querying today's graph with an old decision ID.

**Failure:** invalid hash, missing required metric or incompatible vocabulary → UNKNOWN eligibility and no production VLD. A known cold-start release may be used in labeled shadow mode; missing state is never silently a cold-start release. K unavailable may use a distinct fixed-K shadow policy only if preconfigured, with explicit degraded status and no claim that learned K was exercised.

**Closure/enabling:** A1/A2; dependencies for F11/F13/F14/F15/F31 and P1 F03/F12/F18. Enables consistent L1–L3 measurement.

### 4.3 Decision Q3 — First-class durable trajectories

**Decision.** Use an **EpisodeStore protocol with a PostgreSQL relational canonical ledger in the same deployment database as AGE**, and a transactionally queued AGE projection. SQLite implements the same schema for isolated dev/replay. AGE is a queryable graph view of completed episodes, not a second competing source of truth.

This satisfies E-1 with actual InvestigationTrace graph records while using SQL constraints for idempotency, append order and event delivery. The user-visible trajectory can be read from the canonical store before projection completes; its projection status must be visible. A v2.8 gate specifically requiring AGE records waits for projection success.

Proposed API:

~~~python
EpisodeStore.begin(bound_request, bundle_ref, surface_state, baseline) -> EpisodeId
EpisodeStore.append_event(episode_id, sequence, event, expected_previous_hash) -> EventRef
EpisodeStore.complete(episode_id, terminal, contrast, eligibility, expected_version) -> EpisodeRecord
EpisodeStore.get(authorized_scope, episode_id) -> EpisodeRecord
EpisodeStore.list_for_decision(authorized_scope, decision_id) -> list[EpisodeRef]
~~~

**Canonical schema (NEW version1):**

| Table | Key and principal columns |
| --- | --- |
| vld_episode | tenant_id/domain_id/episode_id PK; decision_id/version; idempotency_key+request_hash unique within tenant/domain; bundle_id/hash; category/schema; origin/mode; S0 payload/ref/hash; baseline prediction; assessment; requested/recommended/effective budgets; status; start/finish timestamps; final state/prediction; halt; eligibility; contrast; completeness; projection status |
| vld_episode_event | tenant/domain/episode/sequence PK; event_type; attempt_id; payload/ref/hash; previous_event_hash; timestamp. Events append; terminal correction is another event, not an overwritten observation. |
| vld_attempt view/projection | attempt_id/index; candidate-set snapshot, selected candidate/edge/pattern, support mask/prerequisites, Q components/K/priorities, selection probability and policy, state-before hash/vector/P, reservation, started_at/finished_at, result status, source/fact refs, state-after/P, residual, action-change count, costs and error code |
| vld_evidence_blob | scoped content hash; encrypted normalized input sufficient for replay; record IDs and versions; valid/observed/ingested/read timestamps; schema/source/calibration IDs; planted/live/mixed origin; retention/expiry |
| vld_snapshot | immutable model/bundle bytes or artifact reference plus versioned canonical serialization/hash; action/factor vocabulary and all effective scoring parameters |
| vld_outcome_link | canonical outcome ID, episode ID, decision ID, adjudication grade, actual_action/acceptable set if provided, event time/commit sequence, executed/advisory status and re-triage link |
| vld_outbox | transaction ID, event_id unique, event_type, payload hash, destination, retry state; trajectory projection, verification notification and publication jobs |
| vld_schema_migration | version, applied_at, migration hash; explicit factor/policy compatibility mapping |

The attempt result enum is **ACQUIRED, EMPTY, TIMEOUT, ERROR, INVALID, CANCELLED, INTERRUPTED**. Unsupported or unauthorized candidates are excluded with reasons in the considered-candidate snapshot; they are not silently dispatched. Store both allocated and consumed costs, including empty/error work.

**Candidate record contract:** candidate_id, pattern_id/version, root/entity IDs, admissible edge/path template, semantic factor IDs it can update, prerequisite fact refs, acquisition_kind (CONTENT_KEYED / SCORE_KEYED / FIXED_PREREQUISITE / EXPLORATION), enumerator provenance, declared upper cost, availability-known versus unknown, and admissibility reason. Descriptors cannot contain unread answer payloads or adjudicated productive labels. Their discovery query costs count if discovering them requires new evidence reads.

**Durability sequence:**

1. Authorize/bind, capture bundle, compute surface and begin the episode.
2. Persist an ATTEMPT_STARTED intent with candidate set, probability, reservation and state hash before I/O.
3. Dispatch bounded read; append ATTEMPT_FINISHED plus normalized facts and post-state.
4. On crash, an unmatched start becomes INTERRUPTED, with possible work charged conservatively. Do not claim “no read happened.” A resumed request uses the same episode key; retry only idempotent reads under a declared retry budget.
5. Commit terminal episode plus projection event before returning an eligible result. If canonical persistence fails, do not issue execution authority; return unavailable/UNKNOWN with a correlation ID.
6. Project after episode completion: Decision→HAS_INVESTIGATION→InvestigationTrace→HAS_ATTEMPT→InvestigationAttempt→READ_EVIDENCE→evidence-record reference. Outcome→VERIFIES→Decision retains existing canonical outcome semantics, with an explicit episode link. These are NEW proposed edge types, not assertions about current schema.

No inference writes to the evidence graph or judgment model. Ledger writes are audit effects owned by the orchestrator, and AGE projection follows the episode. This makes the meaning of “read-only episode” explicit rather than pretending durable auditing has no writes.

**Privacy:** tenant-authorized retrieval, redacted display projection, encrypted normalized evidence, bounded sizes, retention policy and deletion tombstones. A payload hash alone cannot enable replay after deletion; label such an episode non-replayable. Do not put raw credentials/PII in error strings or general metrics. A hash chain is not authentication against an administrator who can rewrite the entire database; protected checkpoints/access controls are separate.

**Closure/enabling:** A3 foundation and B1 actual append integration close F02; B6 closes probability semantics F20. Enables replay, C2/C3/C5 and all five trace beats.

### 4.4 Decision Q4 — Conservation is an emit contract, not a stopping rule

**Decision.** Adopt a versioned GovernanceEvaluator that takes immutable inputs and returns **three separately named decisions**: read permission, learning/promotion permission and action-emission eligibility. Never equate a cold-start learning exception with authorization to auto-approve an invoice.

Proposed pure interface:

~~~python
evaluate_governance(
    snapshot: GovernanceSnapshot,
    request_mode: str,
    final_prediction: Prediction,
    provenance: EvidenceProvenance,
    execution_context: BoundDecisionContext,
) -> EligibilityResult
~~~

Response fields include eligibility enum, reasons, raw canonical status and nested/overlay statuses, policy/version, evaluated_at, snapshot hash, evidence quality, scope, expiry and executable_action_ref (nullable). Keep final recommendation separate from eligible executable action.

| Eligibility | Meaning / downstream behavior |
| --- | --- |
| ELIGIBLE | Production mode, known allowed release, required evidence/decision checks pass, sufficiently current governance permits the action, and episode is durable. It is an input to the separate executor, not an instruction to execute automatically. |
| ABSTAIN | Known policy denies autonomous emission: RED, AMBER under the initial conservative VLD action policy, missing mandatory evidence, ambiguity or other domain gate. Recommendation remains advisory; executable_action_ref=null; create an idempotent human-review proposal when appropriate. |
| READ_ONLY | Explicit shadow/demo/positive-control mode; no execution capability regardless of apparent confidence. Known conservation facts remain in the response, including RED. |
| UNKNOWN | Snapshot, persistence, evidence trust or governance status cannot be established, is stale beyond policy, or conflicts unresolved. No execution; retry/review as appropriate. Never infer GREEN from absence. |

Precedence: invalid/unknown trust state → UNKNOWN; otherwise explicitly non-executable mode → READ_ONLY; otherwise any known denial → ABSTAIN; otherwise ELIGIBLE. Unknown and read-only conditions are retained independently in reasons even though the enum has one value.

**Initial policy decisions:**

- GREEN is necessary, not sufficient, for autonomous VLD emission. AMBER is not automatically eligible merely because a legacy helper sets passed=True.
- COLD_START(0 verified) and BOOTSTRAP(1–9 verified) can retain explicitly authorized **verified learning** semantics, but autonomous VLD action emission is withheld by default. PRESEED is an isolated demo/research condition, never production authorization.
- CALIBRATING must retain and respect nested RED/unknown status. Use the strictest applicable action restriction; no outer status masks it.
- Domain business policies, Trading's regime-adjusted thresholds, valid action permissions, missingness and source trust remain additional gates. Do not reduce them to one global probability cutoff.
- Learned abstention thresholds require calibration on independent operational outcomes and a domain cost matrix. Existing fixed margins are confidence diagnostics, not calibrated harm probabilities.
- Governance uses an explicit executable policy version matching the reviewed backend semantics (§3.3). No new hardcoded23.53 formula inside VLD. A change from current category-coverage/threshold semantics to the paper equation is a separately approved model-policy migration.

Conservation inputs and eligibility computation are frozen inside the episode. The per-step halt uses residual/budget/oscillation only. A well-calibrated deployment may still contain an unresolved individual decision; GREEN is not an S1 classifier.

**Executor boundary.** A downstream action service reads the canonical episode, checks ownership, mode, stored eligibility, artifact hashes, expiry, decision version and current revocation epoch. It ignores a client-supplied eligibility flag or final_action string. It must deny stale/revoked action authority at execution time, even if the episode was GREEN. This external check may only remove authority; it does not rewrite the historical episode or upgrade its ABSTAIN/READ_ONLY to ELIGIBLE. Re-evaluation needs a new bound request. Human overrides are separately authorized and audited, not a hidden conservation bypass.

**Learning boundary.** A valid human verification is recorded even if active learning is paused; otherwise the system cannot collect evidence to recover. Centroid/K learning and publication remain gated separately. Existing learn combines these responsibilities (scorer.py:1008–1020; scoring_router.py:244–299); migration must separate canonical outcome commitment from model mutation without bypassing their checks.

**Closure/enabling:** B2 closes F14 after all consumers refuse unauthorized action references. Supports C3, safe L1–L3, safety challenge1 and GREEN-at-emit demo semantics.

### 4.5 Decision Q5 — Verified-feedback K lifecycle and credit assignment

**Decision.** Replace direct “final correct → reward every read” updates with a **versioned estimator and event-driven candidate-learning lifecycle**. Retain the bounded interval[0.1,3.0] and initial uniform0.5; do not widen it to accommodate an injected demo value6.

~~~text
Durable episode
  → separately committed, trusted outcome
  → VerificationCommitted event
  → episode/outcome eligibility checks
  → frozen-episode replay and credit estimate
  → atomic K candidate update
  → governed checkpoint evaluation/publication
  → later episode captures new K version
~~~

**Canonical trigger, not HTTP success.** Extend the canonical outcome transaction to append VerificationCommitted with an immutable event_id, tenant/domain, decision/outcome IDs, adjudicator identity/role, origin, actual_action or adjudicated acceptable set, commit sequence and linked episode(s). The existing ProtocolV2OutcomeService distinguishes canonical_committed from accepted_pending_sync (copilot_sdk/graph/outcome_service.py:46–75). A queued/pending outcome cannot trigger production K. Retried outbox delivery has at-least-once delivery with **exactly-once update effect**, not a claim of exactly-once distributed delivery.

Do not call scorer.learn again on an already committed outcome merely to update K: it also owns existing model/outcome operations. Refactor an internal verified-learning operation that consumes the canonical event once. Ordinary Decision/Outcome semantics remain write-once. Corrections create a re-triage Decision and archive/supersede the old one; follow copilot-sdk/docs/design/no_amend_outcome_policy_v1.md:5–17. A supersession invalidates affected learning contributions and triggers deterministic candidate rebuild/requalification from the eligible event ledger, not silent editing of old outcomes.

**Episode linkage.** A decision can have many shadow episodes, but a canonical outcome may credit only the selected executed/adjudicated episode for operational learning, or explicitly designated research arms in an isolated namespace. Do not multiply production updates by rerunning the same decision ten times. Record the exact v_L, category, evidence refs and snapshot used for the committed action; never overwrite an existing Decision's original v0 merely to train on v_L. If the product creates a revised recommendation, persist a new revision/re-triage link and the executed version. A later analyst may discover facts beyond the episode; those facts can inform independent adjudication, not retrospectively enter earlier read states.

**Eligibility for K updates:**

- Canonical outcome is committed; decision/episode tenant/domain match; source is allowed operational evidence; episode complete and replayable; label has adequate action-level meaning; learner version/schema compatible.
- PLANTED/SYNTHETIC/ORACLE_CONTROL cases are excluded from production K, verified-count governance and operational metrics. They may train a separately named experiment K through the same code with an isolated store and synthetic label certificate.
- A binary “correct” flag is insufficient to infer all action probabilities' correctness after an override; require actual_action or an adjudicated distribution/acceptable-action policy. No usable action label → no step-utility update.
- EMPTY and attempted reads remain accounted; infrastructure ERROR/TIMEOUT is recorded as source reliability/cost, not automatically as semantic evidence that the factor is useless.
- Actor authentication, deduplication, supersession, label-quality and verification-selection metadata are part of the event.

**Credit estimator v1: sequential predictive contribution, not causal proof.** For a one-hot independently adjudicated action y and episode-frozen probabilities p_t, define:

~~~text
U(p_t,y) = 1 - 0.5 × Σ_a (p_t[a] - one_hot(y)[a])²       # [0,1]
g_t      = U(p_after,y) - U(p_before,y)                   # [-1,1]
r_t      = clip(g_t - λ × normalized_acquisition_cost_t, -1, 1)
K'_j     = clip(K_j + η_plus × max(r_j,0)
                    - η_minus × max(-r_j,0), 0.1, 3.0)
initial K_j = 0.5; default η_plus=.02, η_minus=.005
~~~

λ, cost normalization and rates are pre-registered/versioned; λ is not tuned on the evaluation holdout. A raw flip has no bonus. This avoids labeling movement toward any centroid as improvement. Domain action loss/saves/hurts remain separate evaluation outputs; this Brier-based training proxy does not replace the domain utility model.

When one accepted read updates one factor, it receives r_t. For a multi-factor read, allocate its net contribution over semantic factors in proportion to absolute effective-metric vector changes; normalize shares to sum1. For selector-only reads with zero factor change, use the catalog's declared descendant impact set with uniform shares for any cost debit; no positive utility is inferred. This attribution is a declared estimator, not an identified causal decomposition. The sum of unpenalized g_t telescopes to terminal-minus-surface utility; allocated credit may not exceed the episode's recorded contribution. Repeated reads of one factor aggregate once per episode in deterministic attempt order.

**Conditional dependencies require an additional credit instrument.** The v1 estimator can under-credit a necessary selector whose benefit appears later. Support a separately versioned **closure replay** estimator: remove the selector fact and its dependent evidence from the admitted set, re-extract, and score under the original snapshot; compare terminal utility. Re-score retained facts only—do not invent an unseen alternative branch. This measures contribution conditional on the captured evidence, not the outcome of a different real investigation policy. If prerequisite closure or complete facts are missing, report credit-unidentifiable rather than reward the selector.

For genuine policy-level attribution use authorized shadow exploration or a prospectively randomized policy comparison with logged probabilities (Q8). A deterministic episode does not identify rewards for unchosen branches. Domain experts' productive-branch labels are a separate measurement signal, never runtime input.

**Persistence/publication.** New tables:

- k_policy_state keyed by tenant, domain, category, factor_schema_id, acquisition_policy_version, credit_policy_version, source-policy/metric-compatibility epoch and semantic factor_id; weight, n_eligible_updates, version.
- k_update_event with unique(event_id, episode_id, learning_arm, credit_policy_version), before/after state hashes, allocated rewards, evidence/outcome IDs, update status and sequence.
- k_checkpoint with immutable vectors, ledger watermark, training geometry hashes, candidate/promoted/rejected status, evaluation artifact IDs and parent version.

Apply one episode's dimensions and idempotency receipt in one SQL transaction. Serialize or lock the scoped K version; on CAS conflict, retry against the new state in canonical verification order. Never increment a counter for an unapplied weight update. Publish the resulting candidate through the active-release manifest only after the configured learning/promotional policy permits it. Bounded local updates and a known learning gate are necessary, but not proof of improvement; a separate regression/harm gate controls activation. Raw K remains bounded; do not renormalize into values above3.

All five copilot main.py factories bind the same protocol and lifecycle through tenant-aware dependency injection. Dedicated existing SQLite tables may be read as migration input, but rows without trustworthy origin/verification lineage are **UNQUALIFIED_LEGACY**, not automatically “trained” production K.

**Experiment support (§10.4):** C3 runs (a) fixed-K control, (b) synthetic-event updates on production geometry, and (c) actual operational-event K learning as separate evidence tiers. K0 plus every50 through500 produces11 checkpoints; same snapshots, budgets, held-out cases and evidence cutoffs across arms. Geometry is frozen for the K-only attribution experiment. Joint μ+K changes are a separate factorial experiment. K=6/8/100 interventions remain explicitly synthetic ablations and cannot be a learned checkpoint.

**Closure/enabling:** C1 closes F15, incorporating F16 and verification linkage dependencies; C3 decides whether effective-recursion/C5/L3 benefit can be claimed. Retention plus later reuse proves structural recurrence; a curve showing improvement is a separate requirement.

### 4.6 Decision Q6 — Public inference cannot access oracle labels

**Decision.** Positive controls and production receive different data capabilities, not merely different values of a force_correct flag.

- Public runtime sees S0, eligible candidate descriptors and evidence returned from selected reads. Its serializer rejects correct_branch, ground_truth_action, ground_truth_confidence, adjudication and expected-route fields.
- A sealed evaluation store maps episode/case IDs to adjudicated outcomes and productive branches. Runtime service credentials cannot read it.
- A positive-control runner is an offline/test service or an explicitly engineering-authorized ORACLE_CONTROL mode with READ_ONLY eligibility. It is excluded from production routing/accuracy/K and never used as the response source for ordinary UI requests.
- Outcome evaluation joins occur only after terminal episode persistence. The action emitted in a trace must be exactly the scorer's computed action.

**Current leak:** triage.py:483–499 calls Stage1 without disabling the default oracle; multihop_scenarios.py:315–317 chooses correct_branches and :385–392 substitutes ground-truth action/confidence. B3 removes this path from public dispatch entirely; changing only the output override is insufficient if the branch policy still reads labels.

**Acceptance:** deliberately disagreeing scorer/label fixtures, randomized label permutation without changing public inputs, code-capability/import checks, and mounted-endpoint tests must demonstrate identical runtime trajectories when only sealed labels change. Merely setting force_correct=False in one test is not enough.

**Closure/enabling:** B3 closes F26. Essential to C1/C2/C3/C5, L1–L3 and safety challenge3.

### 4.7 Decision Q7 — Faithful single-pass contrast

**Decision.** For an episode beginning at v0, compute baseline once:

~~~text
baseline = ProductionPredictor(bundle.model, v0, bound_category)
terminal = ProductionPredictor(bundle.model, vL, bound_category)
~~~

A budget0 episode yields the same prediction payload as baseline. This contrast answers **“what did acquiring these additional facts change?”** It does not isolate routing advantage, because VLD has acquired more information. For routing advantage, use matched-cost content-rule, majority, static-Q and breadth arms, with the same source access and evidence transformation.

Store the original historical production recommendation separately if its model or inputs differed from the captured episode. Do not call the matched-snapshot baseline the historical decision. Include prediction snapshots, action IDs, p_max, gap, distance and provenance; replace improved with action_changed, confidence_gap_delta and verified_utility_delta=null until adjudicated.

The comparator uses no final-evidence inputs at v0. A separate equal-information batch readout scores the same admitted facts without sequential selection to diagnose aggregation differences. It is not charged zero cost. Every comparator has an explicit budget and acquisition/label visibility contract.

**Closure/enabling:** B4 owns F11 closure with A1. Supports C1/C2/C3/C5 experimental attribution and all contrast strips.

### 4.8 Decision Q8 — Independent verification, replay and readiness

**Decision.** Use one production kernel in runtime, and **independent expectations/assembly in verification**. Sharing the kernel for identical deployed semantics is correct; comparing two wrappers around the same wrong snapshot is not independent evidence.

Verification layers:

| Layer | Input and procedure | What it proves / does not prove |
| --- | --- | --- |
| Numerical kernel contract | Small hand-computed L2/DK/mask/phase2 examples, captured kernel states, nontrivial action order; independent reference implementation in tests | Exact distances/probabilities/action equivalence. Tolerance initially1e-10 float64 on the same platform; declare serialization/tie tolerances. No production uplift claim. |
| Mounted application | Construct through actual app lifecycle in isolated state, restore checkpoint + L5 DK/conservation + dedicated K + classifier artifact; call actual authenticated routes | Startup/middleware/adapter equivalence, unknown-category rejection, no bootstrap/oracle substitution. Existing collector is not the fixture provider for expected results. |
| Factual episode replay | Load immutable bundle plus captured normalized fact payloads; replay actual attempted reads/events without live I/O | Reproduces vectors, Q, selected candidate, probability, action, halt and ledger hashes. Missing evidence payload/version means not replayable. |
| Counterfactual routing replay | Requires complete eligible alternative evidence under the same as-of snapshot, or authorized source re-read at that version | Alternative-policy outcome under the recorded environment. Factual traces alone do not expose unchosen evidence. |
| Operational shadow evaluation | Mounted path, real live source versions, independently adjudicated held-out episodes; no action execution | Production mechanism/value in that deployment and interval, not guaranteed execution safety or universal benefit. |
| Governed execution | Separate executor validates canonical eligibility; review/rollback and real workflow observation | Actual execution boundary and operational outcome. Must not be inferred from a shadow test. |

**Propensity contract.** Deterministic argmax: selected probability1, unselected0; deterministic ties follow a documented candidate-ID order. If exploration is explicitly enabled in a shadow-only research policy, sample the logged distribution, record eligible set and RNG/seed, and verify normalization. A possible exploration version is ε-greedy over eligible candidates: winner1−ε+ε/n, othersε/n. ε and eligibility are fixed before evaluation. Never use a softmax score or1/n as propensity for deterministic selection. Deterministic data has no support for off-policy effects of unchosen reads; OPE must reject unsupported actions. Outcome-verification selection bias is distinct from acquisition propensity and must also be reported.

**Metrics.**

- Coverage/availability: attempted, acquired, empty, failed, timeout, source unavailable, label pending, replay incomplete. These are denominators, not filtered-away failures.
- Routing: independently adjudicated productive-branch hit at the specified next decision point after the first read; distinguish content-keyed, prerequisite and score-keyed. Action-label/category recovery is not ρ.
- hit@2 = at least one productive read in the first2; precision@2 = productive reads/2. PAPER:139/243 conflates these terms; choose and name separately. Non-None rate is availability, neither metric.
- Decision value: accuracy and domain loss, saves/hurts, action-change rate, abstention, human referral, costs and latency; score gap is not utility.
- Structure: actual candidate changes/reordering after facts, schema/topology provenance, no-oracle test, frozen geometry/K versions.
- Learning: eligible verified event count, K version chain, per-category vectors, repeated-case/tenant isolation, reachable bounds and fixed-K comparison.
- Budget: attempts, evidence records, logical reads, charged discovery, bytes/time; comparisons at matched declared units.

**Statistical contract.** Freeze train/validation/test splits by campaign/supplier/pipeline or other entity cluster and time. No reusing the50-case evaluation set for K training, reward tuning, fixture tuning, threshold selection or choosing the best checkpoint. Select one final checkpoint as primary before running; interim results are descriptive or use a predeclared sequential analysis. Track source/geometry shifts and delayed verification.

Five hundred training decisions are a protocol choice, not a sample-size proof. Fifty independent binary evaluation cases nearρ=.5 yield roughly±.14 normal-approximation95% uncertainty; repeated evaluation of those same cases does not increase the independent sample size. Rough planning: about96 independent cases for±.10 and384 for±.05 worst-case proportion precision. A paired10pp improvement with discordance probability.30 needs roughly236 independent pairs for80% power at two-sided5% under the usual approximation; entity clustering and the score-keyed subset increase the collection requirement. C3 must produce an actual power/precision plan from pilot rates rather than assert that n>30 is sufficient.

**K experiment design.**

1. Freeze one complete production model bundle and evidence-source protocol. Synthetic cases may use it, with synthetic labels clearly separated.
2. Train candidate K on a fresh chronological500-event stream, logging origin/verification/credit for every event. No injected weight overrides.
3. Evaluate K0,K50,…,K500 on a sealed held-out set using the actual controller and replayable evidence, unchanged budgets and model. Fixed-K0 arm sees equivalent cases and costs.
4. For operational learning, each event is a committed real verified decision; a synthetic verifier in a production-geometry experiment supports only the mechanism claim.
5. Primary benefit is paired domain utility and/or adjudicated routing improvement at fixed cost; availability alone cannot pass. Report negative and neutral dimensions, harmful cases, category heterogeneity and effective sample count.
6. A separate routing×centroid-learning2×2 experiment tests C3. For a joint K experiment, factor K updates independently; do not attribute μ changes to K. No gain is guaranteed.
7. Preserve unused holdout or prospective rollout for final claimed “effective recursion.” Report repeated-scenario controlled benchmarks as such, not a substitute for fresh operational evidence.

**Readiness output.** Replace one ambiguous PAPER_READY flag with an artifact containing architecture_contract_pass, mounted_path_pass, operational_data_grade, independent_labels_pass, replay_pass, oracle_isolation_pass, budget/governance_pass, metric_version, claim-specific evidence gates, scope and exceptions. Missing data/AGE/model yields BLOCKED or NOT_MEASURED, never PASS or silent skip. A paper can be ready to publish a scoped negative result even if performance gates fail. Demo readiness also requires ordered story contract, UI/Guards, declared fixture/geometry versions and exact Loom request.

**Closure/enabling:** B6→F20, C2→F31, C3→F23, C4→F32. Provides the evidence route for every empirical paper claim; cannot ensure a positive result.

### 4.9 Decision Q9 — One controller, domain adapters and versioned policies

**Decision.** Reconcile the shared SDK, SOC and DataOps loops into **one controller**. Domain-specific logic remains in candidate enumeration, SA/read adapters, evidence normalization, feature integration and execution proposals. Do not preserve three action scorers or silently select a loop by fixture ID.

**Interfaces:**

~~~python
# NEW; conceptual signatures, not callable code in the current repository.
DomainInvestigationAdapter.bind(identity, decision_ref) -> BoundDecision
DomainInvestigationAdapter.surface(bound, cutoff) -> SurfaceSnapshot
DomainInvestigationAdapter.enumerate(state, catalog, budget) -> CandidateSet
DomainInvestigationAdapter.read(candidate, cutoff, reservation) -> EvidenceReadResult
DomainInvestigationAdapter.integrate(surface, admitted_facts, schema) -> FactorState
InvestigationPolicy.select(state, prediction, candidates, bundle) -> Selection
SituationAssessor.assess(surface, prediction, q_base, feature_schema) -> Assessment
BudgetPolicy.allocate(assessment, override, access_policy) -> BudgetAllocation
InvestigationController.run(bound, bundle, budget) -> CompletedEpisode
~~~

The existing SDK TraversalPattern has supports(intent) and **traverse(intent, graph_store=..., max_depth=...)**, not execute (copilot_sdk/situation/patterns.py:11–28). SOC patterns expose execute. A typed adapter wraps both into EvidenceReadResult; changing method names in prose does not make them conform. VLD remains above SA: it chooses an eligible read; SA implements the bounded traversal.

**One explicit acquisition policy.** Register:

- q_additive_legacy_v1 for reproducing current synthetic/unit-sigma results exactly, using CORE:106–111. It is a historical/research arm.
- q_effective_additive_v1 as the **proposed primary target**, using the production diagonal metric, the same raw factor scale, and explicit quarantine:

~~~text
For active factor k, using the current top-two actions a1,a2:
p_k = ω_k / 100
d_k = |mask_k × (μ[a1,k] - μ[a2,k])|
l_k = |ω_k × ((v[k]-μ[a1,k])² - (v[k]-μ[a2,k])²)|
q_base[k] = p_k + d_k + l_k
q_effective[k] = K[k] × q_base[k]

priority(candidate) =
    max(q_effective[k] for k in candidate.impact_factors)
    / max(candidate.reserved_cost_units, 1)
~~~

Eligible set masking is a boolean operation, not a sentinel that can turn positive if K is invalid. Inactive/masked factors are excluded unless the candidate is a necessary selector for active descendant factors. Candidate impact sets, including selector descendant sets, come from a versioned static catalog, not unread answer values.

This target reduces to the current Q for unit weights, unit masks and unit-cost scalar candidates, but **is a new policy when weights, masks or costs differ**. No0.872 or other old result is inherited. Precision, separation and leverage are heuristic terms; tau influences predictions/top-two but does not divide this Q. The exact diagonal log-odds sensitivity2ω_k(μ1−μ2)/tau is a separately registered ablation, not mislabeled as the deployed Q. Full-matrix/non-diagonal acquisition requires its own validated policy or falls back explicitly.

Tie order is stable ascending candidate_id after priority; record all tied candidates. K and Q are frozen-policy inputs, but Q is recomputed from v after every successful integration and candidate eligibility is recomputed after selector/empty outcomes. Actual evidence confidence is unknown until the read; it cannot be used to rank the unread answer. Historical source reliability may enter only through a separate declared policy version.

**Candidate and cost semantics.**

- A candidate is a bounded graph/source read with a stable ID, authorized root, prerequisites and impact factors. Domain labels alone do not prove conditional structure.
- An evidence read cannot hide multiple unrestricted queries inside one “hop.” A compound pattern has a declared upper bound; the adapter enforces query, record and byte limits. If prerequisites need separate reads, represent them as separate candidates.
- BudgetAllocation tracks requested_limit, recommended_limit, effective_attempt_limit, cost_limit, record_limit, byte_limit, deadline, override_actor/reason, classification and policy versions.
- Initial proposed service caps:0–8 attempted acquisitions, at most64 catalog candidates per episode, at most32 returned evidence records per attempt, at most128 across the episode,1MiB normalized evidence payload total,1s per read and5s total. These are explicit starting limits to benchmark, **not measured latency claims**. Domain/API upstream limits may reduce them; callers cannot increase server limits.
- Reserve cost before dispatch; no affordable eligible candidate → BUDGET_EXHAUSTED. EMPTY/ERROR/TIMEOUT consumes an attempt and incurred cost. A declared retry is another metered attempt with a unique attempt ID; default no in-episode retry. Graph/external requests must enforce server-side timeout/cancel, not merely abandon a Python future that keeps running.
- Topology enumeration from already admitted facts/catalog is free computation. New database discovery or answer-bearing metadata costs are metered. Cache hits retain their origin/version and declared logical-read cost; report wall time separately.

**Typed evidence and integration.** EvidenceReadResult contains status, normalized facts, value/unit/confidence and calibration ID, authenticated source/record IDs, source versions/timestamps, admitted-path edges, new prerequisite facts, metadata origin and observed cost. A missing record is EMPTY. An authoritative negative fact such as “query succeeded; no active session in interval” is ACQUIRED negative evidence with provenance; it may legitimately change v. Do not encode a provider outage as an empty successful query.

The integrator is a pure function of S0 plus the ordered, deduplicated admitted facts. It has no graph handle: it cannot fetch all unselected evidence during “re-extraction.” For scalar evidence, raw replacement or calibrated confidence interpolation matches the declared source policy; calibrated blend is c*value+(1-c)*prior. Re-extraction folds each distinct fact once from S0, so repeatedly calling it does not repeatedly amplify confidence from the same fact. Multi-factor domain transforms use named versions and can move factors both upward and downward. No universal elementwise max or averaging of unrelated full vectors.

Unknown source/calibration does not automatically become a trusted raw overwrite. A predeclared research policy may retain ungated low-trust replacement as an ablation; production uses approved normalization/gating or rejects the fact. Validate finite numbers before any range clipping, and preserve a clamp flag for finite out-of-range observations. The transform cannot see outcome/expected-action fields.

**Situation and override semantics.** Always compute the10-feature assessment before reads, using **base Q without K** to preserve a stable feature definition. K-weighted priority summaries can be a new feature-schema version, not an implicit input change. Store assessment even when budget overridden. The current mapping S1=0,S2=3,S3=1,S4=2,S5=3,S6=4 is a versioned recommendation, not a mandatory universal optimum.

Fallback heuristic identifies S1 only when its configured closeness, separation, missingness and source-coverage conditions all hold; proximity alone is insufficient. Without validated separation thresholds, label assessment UNCERTAIN and use a declared bounded shadow/default budget, not confident S1. C6 trains/calibrates model-backed classification on production episodes before claiming C4's learned behavior. The classifier has no conservation override or action authority.

**Controller and C4.**

~~~text
validate/bind → capture bundle → pure surface score + baseline
assess → allocate → persist episode start
repeat while a metered acquisition is permitted:
    enumerate eligible candidates from current admitted state
    choose via frozen policy; persist candidate set and actual probability
    reserve cost; persist attempt start; execute bounded read
    record ACQUIRED/EMPTY/TIMEOUT/ERROR/... and actual cost
    integrate only validated acquired facts; re-score via same snapshot
    update frontier/attempt history, raw action-change count and residual
    persist attempt finish
    apply ordered terminal rules
finalize recommendation + matched-snapshot contrast + eligibility
persist completed episode → return durable result
~~~

Terminal rule order: cancellation/security revocation preventing further reads; fatal source/model/integrity error; episode deadline; cost/attempt exhaustion; no eligible candidates; oscillation; eligible residual halt. Record every applicable reason and one primary reason.

Define target residual r=||E(S_next)-v_before||2/max(||v_before||2,0.1), with an initial proposed delta=.05 and max_action_changes=2. Count every argmax action change, including small-gap changes; halt for oscillation at the configured count. These constants are versioned design defaults to calibrate, not proven optimal.

**Residual eligibility matters:** only a valid acquired non-selector update can invoke residual halt, and only if no new prerequisite/eligible branch was unlocked and the policy has no unresolved required continuation. EMPTY, ERROR and a selector-only read with unchanged v do not halt merely because delta-v=0. For true EMPTY the action remains unchanged; attempt history removes that candidate and allows another. This is how the SOC wrong-first-read recovery can exist honestly. A zero-update informative-but-neutral read is not proof that every remaining candidate is useless; compare residual policy with fixed-budget continuation in C3. Budget/deadline always bounds it.

A>=2 and d>=1 validation avoids meaningless single-action and empty-vector loops. Finite identical action centroids are permitted as a labeled degenerate model for diagnostics, but cannot produce an S1 confidence or an eligible autonomous action by tie-breaking. Halt NO_DISCRIMINATIVE_GEOMETRY or use an explicit baseline fallback; no “successful flip” claim.

**Domain reconciliation and routing paths:**

| Domain | Reuse | Required adapter work / target boundary |
| --- | --- | --- |
| SOC | FactorVectorProvider and category-specific pattern/evidence code | Separate surface-only extraction from admitted-fact integration; wrap execute as bounded reads; preserve campaign/entity edges; eliminate oracle selection; retain externally assigned category and score within it. |
| DataOps | Existing schema/dependency/history evidence helpers | Remove separate bootstrap/norm scorer and elementwise-max aggregation; reconcile Alert/Pipeline versus DataQualityAlert/PipelineSystem contracts explicitly; persisted Decision→Alert→Pipeline attachment must match exact case IDs. |
| S2P | Invoice/contract/supplier/receipt readers and canonical scorer | Replace literal3.1/total-invoices-as-verified with linked outcome counts at cutoff; distinguish receipt/contract prerequisites; map workflow adjustment proposals separately from scorer actions. |
| Trading | Current ten-factor provider and runtime scorer | Bind trade/portfolio/ticker provenance and source versions; registry fixtures only in demo namespace; match regime decision policy and time cutoff; no optional generic map described as a live graph implementation. |
| Purchasing | Current seven-factor provider and runtime scorer | Bind order/item/supplier/history IDs; explicit normalization/default provenance and ordered source reads; align current narrative separately from rewritten test expectations. |

Expose canonical **POST /api/v1/investigations** and **GET /api/v1/investigations/{episode_id}**. Existing /api/investigation/investigate and /api/{domain}/investigate become versioned compatibility adapters into the same controller; add all five domain aliases for demo manifests. SOC/DataOps aliases cannot retain their own scoring loops. Old integer-action fields may be returned during a deprecation window with an explicit vocabulary, but a bare legacy response never confers execution authority.

Production request: authenticated decision_ref, expected_decision_version, optional budget override within authorization, idempotency_key and mode. Category/vector/schema are loaded and validated server-side. Explicit caller vectors and policy/K overrides belong to a separate engineering/research request that is forced READ_ONLY.

Canonical response: schema_version, episode_id, decision_ref, category_id, action/factor schema, bundle/model/K/policy IDs, origin/mode, assessment, budget allocation and consumed counters, baseline/final predictions, complete attempted trajectory, contrast, terminal reason, eligibility, persistence/projection status and redacted display evidence. GET serves the persisted record used by the panel. Health reports snapshot/canonical-store/source/model availability separately from “object constructed.”

**Closure/enabling:** B1/F02/F04, B4/F11/F13, B5/F10/F30, B6/F20, C6/C4 claim; P1 errors/budget/schema/source/concurrency addressed as prerequisites. One controller and one prediction function provide common semantics, while domains retain their legitimate evidence differences.

## 5. Implementation plan

All file changes below are **future implementation work**, not changes authorized or made by this document. Paths are relative to copilot-sdk unless prefixed with SOC (gen-ai-roi-demo-v4-v50), S2P (s2p-copilot), CI (ci-platform) or GAE (graph-attention-engine-v50). NEW denotes a proposed file, not an existing component. Final filenames may follow repository conventions, but the contracts and acceptance ownership must remain stable.

Estimates are engineering person-days including implementation, review and focused tests. They are planning estimates, not measured delivery times. Data acquisition, independent adjudication, operational observation, deployment approval and scheduling add elapsed time. The common production predictor lives in GAE today; A1 therefore needs a coordinated GAE dependency release even though application integration centers on the three named repositories. Do not reproduce its private calculation in the SDK to avoid that dependency.

### 5.1 Phase A — foundation (12–18 person-days)

| Item | Future files/components | Effort | Dependencies | Test/acceptance contract | P0 contribution / claims |
| --- | --- | --- | --- | --- | --- |
| **A1: immutable release and production predictor** | GAE gae/profile_scorer.py and NEW gae/scoring_snapshot.py; copilot_sdk/scoring/scorer.py, backend/scorer_proxy.py, scoring/startup_restore.py; NEW scoring/episode_snapshot.py and release repository; every model/DK/conservation/K publication path | 5–8 | Agree canonical storage owner and current effective metric semantics | Independently calculated masked/weighted/phase-2 cases agree with production prediction. Capture after complete startup restore. Concurrent learning cannot produce mixed-version bundles; stale CAS fails. Schema/category/kernel/tau/NaN/Inf failures are explicit. Checkpoint-only and post-L5 exports identify the actual source. | Prerequisite F11/F13/F14/F15/F31; enables geometry reuse, frozen inference and L1 foundations |
| **A2: episode, acquisition and claim contracts** | NEW scoring/investigation_contracts.py; backend/investigation_router.py; situation/patterns.py adapter boundary; NEW versioned policy/fixture/claim manifests and docs/design/vld_policy_contract_v1.md | 3–4 | A1 field agreement; independently reviewed domain vocabularies | Validate category/factor/action ordering, request ownership, explicit/default budgets, policy schemas and evidence provenance. Contract tests reject caller adjudication fields and incompatible artifacts. Catalogue entries describe available reads without seeing their future results. | Prerequisite F02/F20/F26/F29/F32; defines every claim's evidence tier |
| **A3: canonical episode ledger** | NEW graph/episode_store.py, graph/postgres_episode_store.py, graph/sqlite_episode_store.py and migrations; CI graph projection/outbox adapter | 4–6 | A2 schema; database transaction/outbox design | Crash after ATTEMPT_STARTED is recoverable as interrupted; duplicate requests do not re-execute completed reads; finalized record is immutable; tenant isolation and redacted replay hold. AGE projection failure cannot erase canonical SQL history or silently certify graph projection completeness. | Prerequisite F02/F15/F20/F30/F31; enables E-1 and replay |

**Phase gate:** a noninvestigating mounted request produces a persisted episode with a single internally consistent bundle and the exact production-equivalent prediction. Run this contract against all five domain configurations, including nonbootstrap state, nonunit effective weights and a concurrent publication. No Phase B code may invent a second scoring function.

Snapshot provenance includes deployed GAE/SDK/domain versions. Existing model restore and prediction behavior motivating this gate is visible at copilot_sdk/scoring/scorer.py:320–339, 475–550; startup_restore.py:14–50; GAE gae/profile_scorer.py:447–488. A successful A gate closes no P0 by itself; it supplies prerequisites for the named owners in §6.

### 5.2 Phase B — core loop and trustworthy evidence (21–33 person-days)

| Item | Future files/components | Effort | Dependencies | Test/acceptance contract | Closing P0 owner / claims |
| --- | --- | --- | --- | --- | --- |
| **B1: common bounded controller** | NEW scoring/investigation_controller.py; adapt scoring/investigation.py; replace independent orchestration in SOC and DataOps services/investigation_loop.py with adapters | 4–6 | A1–A3 | Persist successful, empty, selector-only, negative-fact, timeout and error attempts with original indices. Enforce attempts, records, cost and wall-clock caps. Empty reads cannot change scores or trigger false residual convergence; actual evidence can move factors either direction. Exercise C4/oscillation, zero budget, exhausted candidates and identical geometry. | **F02, F04**; C1/C2, L2 and bounded inference |
| **B2: governance and executable proposal boundary** | NEW scoring/investigation_governance.py; backend/conservation_utils.py; response models, domain action-proposal/executor adapters and canonical outcome service integration | 4–6 | A1–A3, B1 | RED, nested RED, AMBER, UNKNOWN, COLD_START, BOOTSTRAP and synthetic PRESEED cases return the declared eligibility. No downstream action executes from READ_ONLY/ABSTAIN/UNKNOWN. Expiry, revocation, tenant mismatch and stale proposal reject. Verification can still be recorded while parameter learning is paused. | **F14**; bounded safety portion of C3, conservation answer |
| **B3: remove production oracle capability** | SOC backend/app/routers/triage.py and services/multihop_scenarios.py; production/test fixture loading boundary | 1–2 | A2; B1 mount integration | Changing or permuting sealed labels leaves production trajectory unchanged. Requests cannot supply a correct branch/action. Positive-control endpoint is test-only, isolated and READ_ONLY; it cannot certify the public path. | **F26**; honest C1/C2 measurements and safety |
| **B4: mount reconciliation and faithful contrast** | backend/investigation_router.py; all five main.py wiring sites; SOC triage route; DataOps domain router; compatibility adapters | 4–6 | A1, A2, B1, B2 | Exact UI-mounted endpoints use the same bundle/controller. Learned DataOps state differs from bootstrap when expected, with no fallback. Baseline equals production read-only prediction for the same v0 and bundle; final equals that function for vL. All action/category confidence denominators agree. | **F11, F13**; parameter reuse and valid outcome/contrast experiments |
| **B5: typed time-valid evidence and topology** | All five evidence_provider.py files; SOC triage_providers.py/campaign adapters; DataOps graph_contract.py, graph_queries.py, seed_graph.py and patterns; S2P services/s2p_context_builder.py; separately reviewed versioned fixture packages | 6–10 | A2, A3, B1; source owners supply identifiers/time semantics | Every read declares origin, source version, ordered as-of eligibility and transformation. Exact SOC chain and DataOps billing_api attachment are materialized and traversed. S2P ratio derives from eligible linked verified outcomes, never invoice count/literal. Test late-arriving/future/superseded rows, zero denominator, upward/downward transformations, source outages and nonshowcase coverage. | **F10, F30**; nondecision causal evidence, C1/C2, L2 and valid K feedback |
| **B6: frozen policy and real selection probabilities** | NEW scoring/investigation_policy.py; pattern adapters and trajectory candidate fields | 2–3 | A2, A3, B1 | Log complete eligible candidate sets, scores, costs, selected ID and actual probability. Deterministic policy logs 1 for the selected candidate, not softmax confidence. Controlled exploratory mode reproduces its actual sampled distribution; no inverse-propensity estimate on unsupported actions. | **F20**; identifiable routing evaluation, foundation for L3 |

**Phase gate:** a request traverses request validation → immutable snapshot → assessment/K read → bounded evidence acquisition → production prediction → persisted terminal record → eligibility response through the actual application mount. Verify all five domains with both forced and default budgets, ordinary nonshowcase inputs and provider failures. This gate establishes implementation behavior; operational benefit still requires Phase C.

The cap and timeout defaults in §4 are proposed safety limits, not latency measurements. Measure per-domain source latency before rollout and publish the resulting versioned limits. Failure to support historical as-of reads must be reported as replay/data unavailability, not filled with present-day source data.

### 5.3 Phase C — learning and independent verification (20–32 person-days, plus data)

| Item | Future files/components | Effort | Dependencies | Test/acceptance contract | Closing P0 owner / claims |
| --- | --- | --- | --- | --- | --- |
| **C1: verified-feedback K lifecycle** | NEW scoring/k_learning.py and graph/k_learning_store.py; existing KUtilityStore migration; graph/outcome_service.py; scoring_router.py and domain canonical verification adapters | 6–10 | A1–A3, B1/B2/B5/B6 | Canonical committed outcome triggers exactly one eligible episode update. Duplicate delivery, concurrent workers, failed commits, supersession and paused learning behave as §4.5. Verify tenant/schema isolation, bounded reachable weights, reward provenance and candidate promotion. No direct test-injected weights count as learned state. | **F15**; C5, L3 and the machinery for effective recursion |
| **C2: independent mounted verification and replay** | tests/vld_validation_report.py, tests/test_vld_integration.py, tests/extract_real_centroids.py; NEW tests/test_episode_snapshot_parity.py and tests/test_episode_replay.py; mounted-route tests in all domains; replay/export command | 4–6 | A1–A3, B1–B6; C1 for learned-state runs | Independent arithmetic oracles and full startup production snapshots detect omitted masks/DK/K/governance. Exercise middleware and the route used by the UI. Factual replay exactly reproduces recorded vectors/predictions; unsupported counterfactuals reject. Export all category/effective-metric/policy/source metadata. | **F31**; trustworthy evidence for all empirical claims |
| **C3: preregistered routing, value and K studies** | NEW scripts/evaluate_vld_episodes.py, scripts/evaluate_k_learning_curve.py; independently adjudicated dataset manifests; fixed-K, learned-K, geometry and cost study definitions | 5–8 | B5/B6, C2; C1 for learned-K arm; independent labels/data | Distinguish score-keyed routing from category inference and evidence availability. Run strongest eligible matched-cost comparators and report cluster-aware uncertainty, harms and abstentions. Run fixed-geometry verified K curve with sealed holdout and reachable weights; joint μ/K is a separate arm. Positive claims require their results, not just executable scripts. | **F23**, either validated measurement or explicitly restricted claim scope; C1–C6 empirical adjudication |
| **C4: independent contract/readiness gate** | NEW reviewed claim/beat contract validator; validation report verdict logic and separate contract tests | 2–3 | A2, B4/B5, C2; D3 contract definitions; relevant C3 outputs | Expectations are reviewed before execution. No S2P exception or Purchasing dimension rewrite can hide a mismatch. Gate action pair, ordered narrative reads, default/override budget, S1 assessment, origin, eligibility, persistence, geometry/policy version and required evidence tier. Emit separate per-claim and per-beat flags. | **F32**; honest readiness for every paper/demo claim |
| **C6: classifier artifact and deployment validation** | scoring/situation_classifier.py; training/evaluation command and signed/trusted artifact manifest; all five startup loaders | 3–5 | A1/A2, C2; independently labeled situations; C3 evaluation contract | Freeze feature order and policy version. Test explicit-budget assessment, ambiguous/identical geometry, S1 boundaries and invalid models. Validate learned classifier against heuristic/cost baselines on heldout operational data before claiming RF production benefit. | No exclusive P0 owner; C4 and optional learned budget policy |

**Phase gate:** an operational episode can be replayed; its canonical verification can update a candidate K version exactly once; promotion is governed; independent evaluation can state what changed under a pinned geometry/policy/source context. A wired K object, a loaded model file, or a successful update unit test is insufficient. Null or negative measured benefit is valid and must reduce claim scope.

**Optional C5 — bounded L4 operator adaptation (8–12 additional person-days, plus independent trials):** NEW evolution/vld_policy_candidate.py and evolution/vld_policy_promotion.py may propose only preregistered numeric acquisition-policy coefficients, not objectives, governance rules, source permissions, arbitrary code or vocabulary. Candidate evaluation, promotion, rollback, tenant isolation and safety enforcement reuse A–C. This item is **not required to close the 16 P0s** and is **not included in the core Phase C estimate**. It is required before upgrading L4 from “architected” to production-validated operator adaptation. Warm transfer is a separately evaluated initialization strategy, never an unconditional reuse of another domain's K or credit semantics.

The current evidence for absence of production K learning and invalid propensity logging is CORE:216–258 and AUDIT F15/F20. A design must not erase these observations by injecting a successful synthetic weight vector.

### 5.4 Phase D — presentation and literal demo contracts (10–16 person-days)

| Item | Future files/components | Effort | Dependencies | Test/acceptance contract | Closing P0 owner / claims |
| --- | --- | --- | --- | --- | --- |
| **D1: shared persisted-trace panel and guards** | NEW shared InvestigationTracePanel.tsx under the SDK frontend component structure; replace/adapt SOC panel and mount in all five domain frontends, including the actual S2P frontend application | 5–8 | A2/A3, B1/B2/B4/B5, C2/C4 contracts | Render persisted baseline/final predictions and every empty/error/selector/evidence step; show candidates, selected-state quantity, provenance, routing-measurement status and eligibility. Taken/dimmed states are data-derived. Buyer and engineering views differ explicitly. Case switching cannot display another case's response. All ten guards are checked. | **F27**; faithful presentation, not new scientific proof |
| **D2: four Loom manifests** | NEW versioned L-SOC, L-DATAOPS, L-S2P and L-VLD manifests in actual demo configuration locations | 2–3 | D1; D3 reviewed contract definitions; B4 routes; C4 gates | Validate exact route/request/budget, fixture/geometry/policy IDs, warmups, badges, silence cues and insertion sequence. Manifest refuses incompatible run state. Recordings consume the gated run, not staged unrelated screenshots. | **F28**; demo integration only |
| **D3: reconcile and accept the five beats** | Future version of demo_scenarios_and_usecases; independently reviewed beat/adjudication manifests; new literal-beat acceptance tests and versioned fixture references | 3–5 | Contract drafting begins with A2; final closure requires B1/B4/B5, C2/C4 and D1 | Implement original feasible requirements or adopt the explicit revisions in §8. Independently run each reviewed beat through its mounted route. Never claim the original contract is satisfied by an unreviewed replacement. S2P counts/topology and DO/SOC branch order are verified, not narrated into existence. | **F29**; five truthful demo contracts |

D3 drafting is an early input to A2/C4/D2; D3 final acceptance is a later output. D2 depends on the reviewed definitions, **not** D3's final acceptance. D3 does not depend on D2, so the plan has no acceptance dependency cycle.

**Phase gate:** all five reviewed beats render their persisted episodes; all ten guards and all four manifest sequences pass against mounted applications. A planted run keeps its PLANTED provenance even if every contract passes. Recording/publishing a Loom is outside this implementation estimate.

## 6. P0 closure matrix

The closing owner below is unique for each P0. Dependencies may span phases, but they do not create additional owners. **Current closure status for all rows: OPEN; this document supplies a design and acceptance test, not an implementation.** Evidence anchors refer to the existing audit finding and the source cited there.

| P0 | Existing gap and evidence | Single closing item | Dependencies | Required closure artifact |
| --- | --- | --- | --- | --- |
| F02 | Empty attempts/E-1 absent; CORE:12–37, 138–155; API:105 | **B1** | A2/A3; B6 metadata; C2 replay | Durable complete attempt history, including interrupted/empty/error reads, linked to one episode and replayed |
| F04 | Shared C4/oscillation absent; CORE:131–170; SOCLOOP:82–129 | **B1** | A1/A2; domain adapter parity | Common tested halt policy with residual eligibility, action-change count, budget and terminal reason |
| F10 | S2P ratio/verified history asserted; S2P backend/app/vld_preseed.py:84–89; evidence_provider.py:95–148 | **B5** | A2/A3; linked verified outcomes | As-of count-derived ratio with eligible record IDs, denominator handling and independently tested provenance |
| F11 | Different scorer and contrast; CORE:66–74; GAE gae/profile_scorer.py:447–488 | **B4** | A1; B1/B2; C2 parity verification | Mounted baseline/final both use pure production scoring; masks/DK/temperature tests distinguish old path |
| F13 | DataOps bootstrap substitution; apps/dataops/backend/app/main.py:699–708; services/investigation_router.py:137–157 | **B4** | A1; B1 | Nonbootstrap active-state mounted test; unsupported access fails visibly rather than substituting a prior |
| F14 | No emit eligibility; API:39–111; SOC models/investigation.py:46 | **B2** | A1/A3; downstream executor adapters | Frozen eligibility and executor denial tests for RED/UNKNOWN/RO, expiry, revocation and tenant mismatch |
| F15 | K never production-learned; CORE:216–258 | **C1** | A1/A3; B2/B5/B6; C2 | Canonical verification → idempotent bounded K update → governed published version; operational provenance |
| F20 | False propensities; DataOps services/investigation_router.py:69–79, 160–166; SOC multihop_scenarios.py:315–321 | **B6** | A2/A3; B1/B3 | Actual behavior-policy probabilities and full candidate support; reject invalid off-policy use |
| F23 | No measured operational routing/value; AUDIT §12 F23 | **C3** | B5/B6; C2; independent adjudication | Versioned operational study and uncertainty, or an explicit CLAIM_RESTRICTED paper/demo scope that makes no unsupported production benefit claim |
| F26 | Public SOC oracle branch/action; AUDIT §15 F26; SOC multihop_scenarios.py:315–317, 385–392 | **B3** | A2; B1/B4 | Public label-permutation/noninterference test and unreachable isolated positive-control code |
| F27 | No conforming shared panel; AUDIT §15 F27; SOC frontend/src/components/InvestigationPanel.tsx:131–139, 217–255 | **D1** | A2/A3; B1/B2/B4/B5; C2/C4 | Shared persisted-trace UI, guard badges and case-switch tests across mounts |
| F28 | Four Loom insertions absent; DEMO:1253–1258; AUDIT §15 F28 | **D2** | D1; D3 contract definitions; C4 | Validated four manifests with exact warmups, bodies, pins, badges and insertion cues |
| F29 | All five original beat contracts incomplete; DEMO:1023–1067; AUDIT §15 F29 | **D3** | B1/B4/B5; C2/C4; D1 | Original literal acceptance, or explicitly approved CONTRACT_REVISED definitions plus literal acceptance of that version |
| F30 | Linked/topological/as-of fixture package incomplete; SOC campaigns.py:1148–1212; DataOps seed_graph.py:279–309; S2P s2p_context_builder.py:150–174 | **B5** | A2/A3; B1 | Versioned S0/frontier/evidence/adjudication package, exact graph attachment tests, source-time cutoffs |
| F31 | Sweep omits production state/path; SWEEP:194–285, 341–350; INTEGRATION:17–22 | **C2** | A1/A3; B4/B5; C1 for learned state | Independent arithmetic and actual-mounted parity, full snapshot export and replay |
| F32 | Readiness accepts wrong contract; SWEEP:45–52, 293–302, 412–430; INTEGRATION:179–188, 227–231 | **C4** | A2; B4/B5; C2/C3; D3 reviewed definitions | Independent versioned predicates; all mismatches remain visible; per-claim/per-beat gates |

A CLAIM_RESTRICTED result resolves an unsupported-claim blocker by withdrawing that claim; it does **not** mean the missing production measurement was supplied. A CONTRACT_REVISED result closes the adopted revised contract; the historical literal v2.8 requirement remains unsatisfied unless it was implemented. Report these dispositions separately from IMPLEMENTED_AND_VALIDATED, never as indistinguishable green checkmarks.

## 7. Claim enablement matrix

C1–C6 below refer exclusively to **PAPER §0.9**, not the differently numbered later Contributions section. “Enables” means supplies the architecture to test a claim. Effect sizes, comparative benefit and operational scope require C3 results; architectural completion does not guarantee them.

| Paper claim | Present evidence / limitation | Enabling items | Gate for a production-validated statement | If deferred or unsuccessful |
| --- | --- | --- | --- | --- |
| §0.9 C1: own geometry guides selective evidence acquisition | Prototype/fixture selector; Q and production scorer differ; reported percentage needs correction | A1/A2, B1/B4/B5/B6, C2/C3 | Mounted production snapshot; content/score-keyed strata; stronger-than-best-eligible comparator at matched cost on operational adjudicated episodes | State a geometry-conditioned acquisition design and scoped fixture/simulation results only; do not claim universal efficiency |
| §0.9 C2: sequential conditional routing improves over static selection | Synthetic experiment, not causal operational branch evidence | B1/B5/B6, C2/C3 | Same information/source/cost opportunity, identical prediction/integration; paired static-Q/rule/breadth comparison with conditional branch labels and uncertainty | State structural sequential routing; retain +4.8% only with original experiment scope |
| §0.9 C3: safe joint learning / 57:0 | Simulation harm count; conservation does not guarantee every action correct | A1, B2/B3, C1/C2/C3 | Governed updates and emit; fixed/joint μ/K factorial study; measured harm/abstention bounds on operational outcomes | Remove universal “no harm” language. Say observed harm count with denominator and confidence interval; architecture limits permissions, not truth |
| §0.9 C4: learned situation classifier reduces reads without loss | Current apps use fallback; six-class random arithmetic and no-loss inference need correction | A2, C6, C2/C3; B1/B4 assessment parity | Trusted model artifact; heldout operational situation labels; budget/cost and accuracy noninferiority test with predefined tolerance | Label heuristic budgets as heuristic; report RF numbers as synthetic-only with correct baseline |
| §0.9 C5: K learns useful acquisition | K wired, no canonical verified update; injected 5/6 exceed normal learned bound | A3, B5/B6, C1/C2/C3 | Operational verification lineage, reachable versioned K, sealed fixed-geometry learning curve versus fixed K and independent labels | Fixed-K ablation only; no production experience-acquisition or improving-curve assertion |
| §0.9 C6: compounding advantage / “only” system / 67% wasted | Comparative and universal wording exceeds evidence | A–C plus scoped repeated-round C3 study | Demonstrated improvement across eligible operational rounds relative to declared competitors/baselines; all unsupported uniqueness statements removed | Present compounding as a falsifiable hypothesis. Architecture cannot establish “only” or universal waste percentages |
| §0.10 L1: execution of a prescribed improvement process | Factor-acquisition/scoring primitives exist, but the current acceptance chain is fixture-based and does not prove outcome improvement | A1, B1/B2/B4, C2/C3 | A mounted operational episode executes the prescribed read/re-score process using actual production state and is linked to independent verification; improvement is measured, not inferred from margin | State prescribed investigation machinery and scoped fixture behavior; avoid calling all rescoring an improvement |
| §0.10 L2: frozen-operator execution strategy | Conditional acquisition prototypes, including an oracle path | A1/A2/A3, B1–B6, C2/C3 | Operational source provenance, no oracle capability, frozen policy, recorded state-conditioned choices and independent routing test | Structural or fixture-validated L2 only |
| §0.10 L3: experience-acquisition weights improve | Empty production K history | C1 with A3/B5/B6, then C2/C3 | Verified operational credit updates and independently demonstrated future acquisition benefit under pinned evaluation conditions | Mechanism implemented but benefit unmeasured, or fixed-K only; never equate injection with experience |
| §0.10 L4: operator evolution | Architected positioning, not demonstrated VLD production adaptation | Optional C5 after A–C | Restricted candidate search, separate holdout promotion and operational safety/benefit trial with rollback and provenance | Keep “architected / not demonstrated.” Core A–D does not upgrade this level |
| §0.10 L5: objectives/self-redesign | Explicitly outside scope | None; preserve exclusion | Not an architecture goal or production claim | Continue to disclaim L5; no proposed phase enables it |
| §1.4 answer 1: conservation against self-poisoning | Learning gate exists; VLD emit and snapshot alignment missing | A1, B2, C1/C2 | Canonical verification, governed promotion, frozen emit and downstream enforcement; injected/poisoned feedback tests | Describe a permission/calibration control, never a proof that wrong verified labels are impossible |
| §1.4 answer 2: VLD Guards | Described guards; shared UI/provenance missing | A2/A3, B3/B5, C4, D1/D3 | Automated guard checks against actual recorded episodes and reviewed claims; planted remains planted | Describe policy commitments and engineering controls only, not fully enforced demo safety |
| §1.4 answer 3: Astra verification | Existing sweep shares its own collector and misses mounted state | C2/C3/C4 | Independent numerical/mounted/operational evidence; reproducible failure and denominator reporting | Say fixture/component diagnostic, not independent production certification |
| §5.5 structural recursion | Persistent K storage exists, but the verified-update → retained-version → future-use chain is not demonstrated | A1/A3, B5/B6, C1/C2 | A committed operational outcome revises K; that immutable version survives restart and is captured by a later episode, with complete lineage | This cross-episode retention/reuse claim does not require positive benefit, but it does require the update lifecycle. A frozen-K within-episode loop alone does not establish PAPER's structural RSI claim |
| §5.5 effective recursion | Curve asserted before §10.4 placeholder is filled | C1/C3 with fixed-geometry and separate joint-state arms | Verified experience changes future acquisition and improves heldout utility at comparable cost; report null/negative outcomes too | Call this a hypothesis or implemented feedback mechanism, not established improving recursion |
| §10.4 K curve: fixed-K diagnostic | Production tensors can be exported; synthetic cases can be scored with fixed K | A1/C2 provenance plus C3 evaluation definition | Report geometry source and origin; all K snapshots are equal in a true fixed-K run; use as control, not a learned curve | Can run today only as a carefully labeled diagnostic after validating extraction; does not supply production K learning |
| §10.4 K curve: learned-K production experiment | Missing verified feedback path and independent operational branch labels | A3/B5/B6/C1/C2/C3 | 0-plus-10 evaluation snapshots; no holdout updates; identical heldout cases do not multiply independent N; operational feedback and reachable updates | Synthetic validated learner experiment is still synthetic, even with production μ; revise paper until operational result exists |

The minimum upgrade from fixture to production validation is not “connect AGE.” It is the combination of a mounted production path, time-valid operational evidence, captured state, independent outcomes, durable verification-linked episodes and a declared comparison. Connecting the source without obtaining branch adjudication may permit action-utility measurement while leaving ρ unmeasurable.

## 8. v2.8 unblock matrix

AUDIT §19 marks exactly **five requirements BLOCKED**: the five original beats (AUDIT:605–609). The following matrix accounts for all five, then includes their shared partial/not-built dependencies. Historical values in DEMO are design targets, not observations that a renderer may copy into a trace.

### 8.1 The five BLOCKED beats

| Requirement and current blocker | Target contract / explicit revision decision | Unblocking items and phase | Acceptance evidence |
| --- | --- | --- | --- |
| **§4.17 VLD-SOC-1** — original lateral_movement investigate→escalate with .04→.31 differs from current credential_access monitor→escalate (DEMO:1023–1027; AUDIT F29) | Retain the required score-conditioned causal investigation, but publish a reviewed beat using a feasible fixed scoring category/action vocabulary. If the current credential_access case is chosen, name it as a revised beat rather than silently relabeling the old one. Independently adjudicate the productive branch. The alert's literal category is not itself proof of score-keyed branching. Render computed margins, not .04/.31 constants. | B1/B4/B5 evidence and scoring; B2 emit; D1 panel; **D3 final contract** | Exact pinned request, source chain, ordered reads, independent branch/action label, same-snapshot contrast, durable trace and GREEN-at-emit only when genuinely eligible |
| **§4.17 VLD-SOC-2** — empty first read scripted as moving the action (DEMO:1033–1037; CORE:138–141) | Replace the impossible empty-read explanation with: **“The first check returned no evidence. The score stayed the same; that branch was exhausted. The next check changed the evidence and the recommendation.”** Choose and pin the reviewed first/second branches; current TI→identity is not original auth→process. A negative observed fact is ACQUIRED evidence and may change the action; it must not be encoded as EMPTY. | B1 C4/attempts; B3 oracle removal; B5 branch package; D1; **D3 final contract** | First attempt visible with unchanged vector/prediction and no false convergence; second productive read reachable without labels; final action and residual halt computed |
| **§4.17 VLD-DO-1** — MATKL_V2 dictionary exists, complete billing_api chain/handoff does not (DEMO:1043–1047; AUDIT F30) | Materialize the specific Decision→Alert→Pipeline attachment and source-system dependencies. Reuse contract Alert/Pipeline labels consistently. “Three systems” must be three identified, time-valid evidence sources whose work is metered, not one free dictionary lookup narrated as three investigations. Any apply-fix step is a separate B2-governed proposal. | B4 active scoring; B5 topology/transform; B1 budget; B2 handoff; D1; **D3 final contract** | Exact nodes/edges, source records, dynamic frontier and derived factors; documented cost accounting; final recommendation and separate executor eligibility. Do not claim “three minutes saved” before a time study |
| **§4.17 VLD-DO-2 and sister case** — resource_quota≈.62 / .93 differs from quality_anomaly refer_to_specialist→escalate (DEMO:1053–1057; AUDIT F29/F30) | Treat resource_quota as an investigation hypothesis/pattern ID under a valid deployed scoring category, such as pipeline_failure if independently appropriate; do not invent a tensor category. Alternatively propose an explicit schema/model migration, outside a seed-only change. Create/adopt a reviewed sister case with genuinely computed high-confidence behavior; .62/.93 are illustrative targets. | A2 vocabulary; B1/B4/B5; C4; D1; **D3 final contract** | Both original and sister request contracts, no bootstrap fallback, legitimate branch identity distinct from category, actual budget and unique-action S1 assessment; no heuristic silently credited to centroid routing |
| **§4.17 VLD-S2P-1** — receipt-first/history/action contract replaced by contract→supplier fixture and literal ratio (DEMO:1063–1067; AUDIT F10/F29) | Prefer a reviewed receipt-first beat when eligible supplier history is already in S0. If history must be acquired to justify receipt-first, meter that prerequisite; it cannot be free oracle context. Compute verified partial-delivery/pricing-error counts and ratio as-of time. “Accept with adjustment” is a workflow proposal mapped to the real scorer action and separate approval semantics, not a newly invented action label. | B5 counts/cutoff/receipts; B4 scoring; B2 workflow; C1 only if beat claims learned K; D1; **D3 final contract** | Identified receipt/history records, disjoint adjudicated outcome categories, deduplicated eligible decisions and no future/superseded leakage; numerator/denominator/uncertainty displayed; zero denominator gives unavailable ratio, not infinity |

For the S2P ratio, 31 eligible partial-delivery outcomes divided by 10 eligible pricing-error outcomes would yield 3.1; this is an **illustration of the required calculation**, not a claim that those records exist. Preserve counts and record references. A per-category K preference cannot be described as supplier-specific episodic memory unless supplier-specific evidence actually supplies that context.

Original literal v2.8 acceptance and revised truthful-beat acceptance are separate outcomes. D3 must publish the revised contract and its rationale before implementation tests use it. The design chooses truthful feasible revised contracts when literal old requirements conflict with current semantics; it does not authorize relabeling observed output as the old requirement.

### 8.2 Shared requirements and remaining dependencies

| v2.8 requirement (DEMO:908–914, 1014–1112, 1253–1258; AUDIT §19) | Target / unblocking item | Phase and exact gate |
| --- | --- | --- |
| E-1 trajectory store in AGE | A3 canonical SQL episode/event ledger plus explicit AGE projection; B1 complete attempts | A/B; SQL durability and AGE projection independently visible. If AGE projection is missing, literal AGE requirement remains incomplete |
| frozen_branch_policy / R3 over SA | B6 frozen candidate policy and B1 shared controller with SA adapters | B; scored state maps to eligible actual reads; no oracle; semantic branch IDs and valid propensity |
| C4 residual + budget + flip count | B1 common bounded halt | B; empty/selector reads cannot manufacture evidence residual or action flips |
| Constant conservation emit gate | A1 frozen governance and B2 final eligibility/executor | A/B; no per-read geometry/governance mutation; downstream denies noneligible responses |
| Shared InvestigationTracePanel | D1 | D; persisted trace, selected/dimmed candidates, failed/empty read, buyer/engineering views |
| Contrast strip + stored baseline | B4 prediction parity, A3 persistence, D1 display | B/D; exact same inputs/bundle at budget0; matched-cost controls separately evaluated |
| Structured S0 snapshot per beat | A2/A3 bundle and B5 fixture package | A/B; source time, category/schema, factor provenance, geometry, mode and expected request recorded |
| Branch set + planted evidence | B5 versioned candidate/frontier and source package | B; candidate existence is independent of labels, source-read payloads have origin, costs and as-of eligibility |
| Adjudicated productive branch | B5 sealed labels, B3 separation, C3 independent evaluation | B/C; never sent to public runtime; disagreement/ambiguous branches retained |
| Fixture version / PLANTED origin | A2/B5 package and D1 badges | A/B/D; origin persists through AGE, export, replay and UI; unknown origin never becomes LIVE |
| SOC shared campaign chain | B5 | B; exact showcased Decision→Alert→Campaign→CONTINUES links, direction and as-of access tested |
| DataOps Decision→Pipeline and MATKL_V2 | B5 | B; existing indirect infrastructure reused; exact billing_api case persisted and queried using actual graph contract |
| DO-2 / sister numeric targets | D3 reviewed contract plus B4/B5 computation | B/D; computed values replace hardcoded promises; schema versus hypothesis distinction enforced |
| Supplier Aster history ratio and as-of matcher | B5 | B; eligible committed outcomes, source timestamps, cutoff and denominator policy tested |
| L-SOC after E2 before E3 | D2 L-SOC manifest | D; VLD-SOC-1 SILENCE 7 then VLD-SOC-2, exact warmups and pinning |
| L-DATAOPS after E5 fusion | D2 L-DATAOPS manifest | D; DO-1 then DO-2, same-version persisted cases |
| L-S2P after S14 / SILENCE 2 | D2 L-S2P manifest | D; S2P-1 and reviewed receipt/history handoff |
| Standalone L-VLD | D2 L-VLD manifest | D; explicit scope/origin, request pins and no unsupported learning claim |

### 8.3 All ten guards

| Guard and v2.8 anchor | Enforcement owner | Acceptance rule |
| --- | --- | --- |
| GUARD-1 ARCH→NEAR→LIVE (DEMO:1094) | A2 claim registry, C4 gate, D1/D2 | ARCH by default; NEAR only after the specified R3/E-1 prototype gate; LIVE only with the applicable R4 real-data benefit evidence. Deployment or an AGE connection alone cannot advance the badge |
| GUARD-2 permitted language (1096) | D1/D3 copy contract | Buyer wording describes evidence checks and recommendations; no misleading LLM/RL/thinking claim |
| GUARD-3 PLANTED / routing-accuracy-unmeasured (1098) | B5 provenance, C3 measurement registry, D1 | Every planted run visibly remains planted. Unmeasured ρ remains labeled unmeasured; a number must link to its cohort/policy/estimator |
| GUARD-4 content-keyed label (1100) | B6 acquisition classification, D1 | Mark content/rule-keyed steps; do not call a category lookup evidence of score-keyed routing |
| GUARD-5 no unsupported time savings (1102) | C3/R5 study, D1/D3 | No validated time-saving number until a relevant measured study; attempt count is not minutes saved |
| GUARD-6 frozen behavior / no next-time claim (1104) | A1 snapshot, C4/D3 | The specified beats use frozen state and make no next-time-learning promise. A separate labeled K study does not silently override this beat guard |
| GUARD-7 affordable breadth / budget honesty (1106) | B1/B6 metering, C3 controls, D1/D3 | Show allocated and consumed cost separately; where breadth is affordable, claim only supported ordering/cost benefit, not exclusive access to evidence |
| GUARD-8 computed, provenance-badged values (1108) | B3/B4/B5, C4, D1 | Margins/ratios/actions come from the episode; no literal oracle substitution. Provenance and time window accompany values |
| GUARD-9 buyer versus engineering language (1110) | D1 | Plain-language default; geometry/Q/raw quantities remain available in a separate engineering view without disappearing from the persisted record |
| GUARD-10 no claimed competitor execution (1112) | C4/D3 manifests and copy checks | Named competitors are contextual unless actually evaluated in a separately documented study; no fabricated benchmark, execution or comparative number |

A recorded fixture demo may satisfy guard and presentation contracts while still displaying ARCH or NEAR. It must not receive a LIVE scientific-evidence badge merely because the video is ready.

## 9. Risk assessment

| Phase / risk | Failure mechanism and consequence | Mitigation and honest fallback |
| --- | --- | --- |
| A: scoring extraction changes semantics | Losing mask², shrinkage, logits normalization or alternate-kernel behavior reproduces F11 under a new API | Independent hand-calculated cases plus old-production parity; ship the pure function only after equality. Unsupported acquisition kernels use an explicit versioned rule/breadth policy or READ_ONLY rejection, not diagonal-Q equivalence claims |
| A: distributed mixed state | Local locks do not make μ/DK/K/governance atomic across processes | Immutable artifacts and one canonical release pointer/CAS; capture once. If coherent capture fails, return UNKNOWN/READ_ONLY; no mixed bundle |
| A/B: audit ledger leaks data or outlives evidence retention | Source payloads contain identities/contracts; deleted evidence cannot be recreated from a hash | Scoped encryption/redaction/access and retention policies; deletion tombstones. Replay status becomes unavailable where required payloads are gone |
| B: past evidence reconstructed from current sources | Present-day campaign/supplier records leak future facts into ρ and K rewards | As-of eligibility and recorded evidence; unavailable historical reads reject counterfactual replay. Use forward-collected episodes rather than invented history |
| B: normalization or confidence is uncalibrated | Counts/defaults become “high-confidence” factors, contaminating actions and credit | Factor-specific typed transforms and source confidence provenance; unvalidated transforms remain shadow-only. A source name is not calibration |
| B: C4 suppresses conditional follow-up | Empty/selector read appears as zero residual and stops a useful branch | Separate fact/selector/empty semantics; only eligible evidence updates enter residual criterion. Compare halt policies on heldout cases and retain capped no-residual arm |
| B: conservation semantics remain inconsistent | Panel status, learn thresholds and paper formula disagree | Version the exact domain governance evaluator, record operands and distinguish learning/emit policies. Conservative ABSTAIN on known denial; UNKNOWN on unreadable state. Do not “fix” the formula silently |
| B: outages masquerade as empty evidence | Provider catches exceptions and yields None, producing misleading availability and credit | Typed outcomes and source health; persist errors; cost accounting records failed work. Operational K usefulness is not reduced because infrastructure failed |
| B: fake/live source confusion | Real provider class supplies showcase dictionary; a live database contains planted rows | Preserve origin at record level and evaluate ordinary nonshowcase coverage. Label the run PLANTED regardless of endpoint fidelity |
| C: biased K attribution | Sequential reward is not causal contribution; many facts or one easy case dominate | Explicit credit estimator, deterministic sharing, cost accounting, verification coverage and control arms. Restrict claims to observed acquisition utility unless exploration/identification supports causal attribution |
| C: coupled μ and K confound the curve | Later K appears better because decision geometry or evidence source changed | Freeze geometry/source policy for the primary K study; separate joint-learning factorial arm. Pin every released bundle |
| C: retries/corrections corrupt K | Duplicate outcome events double-update; superseded outcomes retain credit | Unique receipts and canonical ordering; candidate replay/rebuild after corrections, never silent in-place reward erasure. Keep prior deployed artifact auditable |
| C: too few independent score-keyed cases | Hundreds of synthetic variants/holdout repeats are counted as independent operational samples | Entity/time clustering, sealed adjudication and effective sample size; collect more independent cases or report broad uncertainty. Do not report ρ from availability alone |
| C: benefit is null or negative | Correct implementation does not outperform the best simple policy | Publish the null/negative result; retain rule/breadth/fixed-K policy operationally. Withdraw positive C1/C2/C5/effective-recursion claims for that cohort |
| Optional C5: policy search overfits or expands autonomy | Unbounded candidate changes bypass governance or exploit holdout | Restrict parameter space, independent promotion set, separate shadow rollout and rollback. Keep L4 architected if these controls or results are absent |
| D: display hides inconvenient evidence | Empty/error steps disappear; high margins are presented as truth; case switch renders stale response | Render from persisted episode with case/version binding; computed values and status labels; UI tests include failures, low-margin flips and nonflips |
| D: script demands infeasible behavior | Empty reads must flip, wrong category must exist, or a two-read claim needs unmetered prerequisites | D3 explicitly revises the contract or marks the beat blocked. Do not tune tests to observed output or invent evidence |

**What the architecture does not prove:** no finite harm-free sample guarantees no future harm; verified labels can be wrong; content-keyed cases do not identify the value of score-keyed routing; a deterministic policy does not supply off-policy support; production centroids plus synthetic cases are not operational validation; implementing K updates does not prove compounding; no architecture establishes universal uniqueness over other systems.

**Minimum scientific fallback:** publish a fixed-geometry, fixed-K, independently verified factor-acquisition/conditional-routing experiment with truthful fixture or operational scope and fair matched-cost controls. Report empty-read behavior, harms, uncertainty and unmeasured quantities. This is a defensible narrower paper even if learned-K or classifier benefit fails.

**Minimum presentation fallback:** a READ_ONLY planted architecture demonstration can use a truthful ARCH/NEAR badge and a faithful persisted contrast. It is not Demo Complete under this plan and must not claim operational learning, real-data ρ or saved time. Oracle-based public routing is not an acceptable fallback, even for a visually convincing demo.

Deferral consequences are explicit: omit C1 → fixed K and no production L3/effective-recursion claim; omit C6 → heuristic budget claim only; omit C3 operational data → fixture/synthetic evidence labels; omit D1/D3 → do not claim the v2.8 guard/beat contract is enforced; omit C5 → L4 stays architected; omit B2 → READ_ONLY, never executable governed VLD.

## 10. Three targets

These targets distinguish **architecture/test coverage** from **positive empirical outcomes**. A complete study with a negative result supports an honest paper, but not the paper's original positive sentences. “Paper Complete” below means the revised, testable scope in §3/§7 is fully evaluated; it does not promise confirmation of all six claims. “Demo Complete” includes all five reviewed beats and all four Loom manifests.

Calendar estimates assume two engineers with appropriate SDK/domain experience and timely reviews; serial person-week equivalents use five working days. Operational collection/adjudication adds an estimated 2–6+ weeks of elapsed time and may take longer if score-keyed cases are rare. These are assumptions for planning, not commitments. Data readiness is a gate, not a date.

| Target | Included work | Effort / indicative schedule | What can honestly be said | Deferred scope |
| --- | --- | --- | --- | --- |
| **Paper Minimum** | A + B + C2 + C3 fixed-K/primary routing evaluation + C4 | **44–68 person-days**; roughly **6–9 calendar weeks** with two engineers and parallel domain work; **9–14 serial engineering weeks**; data time additional | One production-equivalent bounded acquisition path, immutable/persisted episodes, governed read/emit boundary and independent fixed-K comparisons. C1/C2/L1/L2 claims are limited to the cohorts and positive results actually observed; otherwise describe scoped within-episode/fixture results | No learned-K C5/L3/effective-recursion benefit, no validated learned-classifier C4, no joint-learning safety claim, no L4, no complete shared demo/guards/Loom. F15/F27/F28/F29 remain outside this target; F23 may remain claim-restricted |
| **Paper Complete** | A + B + core C (including C6) + D1 + D3; excludes D2 Loom production and optional C5 | **61–96 person-days**; roughly **8–13 calendar weeks** with two engineers; **12–20 serial engineering weeks**; operational evidence additional | All revised C1–C6 questions evaluated; production-validated L1–L3 only for implemented mechanisms with operational evidence, and benefit only when supported. Full safety-control/guard/independent-verification descriptions become supportable within tested scope. Structural and effective recursion reported separately | L4 remains architected unless optional C5 succeeds. L5 excluded. Four Loom insertions/F28 deferred. Universal uniqueness/no-harm wording remains withdrawn regardless of completion |
| **Demo Complete** | All core A–D | **63–99 person-days**; roughly **9–14 calendar weeks** with two engineers; **13–20 serial engineering weeks**; data/recording scheduling additional | All 16 P0s have their required implementation/validation or explicitly scoped contract/claim dispositions; all five adopted beats, ten guards and four insertion manifests pass. Live versus planted and measured versus unmeasured labels remain visible | Optional L4 adds **8–12 person-days plus independent trials**. Public recording/publishing and a successful positive scientific result are not guaranteed by engineering completion |

For Paper Minimum, at least one operational copilot cohort is necessary to describe **that cohort** as production-validated; all-five production claims require all-five evidence. If no operational cohort is available, the deliverable is still a valid narrower fixture/synthetic paper with the corresponding claims revised. Application parity tests across five domains do not substitute for five-domain efficacy data.

Paper Complete includes D1/D3 because PAPER §1.4 invokes VLD Guards and the paper's cases depend on provenance and literal-beat honesty. Omitting the Loom manifests does not weaken a measured routing result. It does leave the demo-integration P0 open. If publication does not need the demo-based guard claim, a narrower paper can defer presentation and explicitly limit that claim rather than pretend it is enforced.

Demo readiness is scoped per copilot and per beat. A failed Purchasing/S2P/other case stays blocked; passing SOC/DataOps does not promote the failed domain. Optional fixed-K demos may be ready when learned-K demonstrations are not, provided their manifests and spoken claims say so.

### 10.1 Required exit artifacts

1. Immutable production snapshot/release manifest: μ, complete effective metric, sigma semantics, tau, vocabulary/masks, K, governance, classifier, policy/cost/halt versions and origin hashes.
2. Durable episode/evidence ledger with complete attempts, source-as-of provenance, measured cost, actual selection probabilities, eligibility and factual replay.
3. Actual-mounted parity and security/governance denial results, including independent numeric cases and simultaneous publication.
4. Independently adjudicated study manifest/results with comparator scope, heldout units, costs, harms, abstentions, uncertainty and explicit unmeasured quantities.
5. For learned claims: canonical verified-outcome receipts, reachable candidate/published K versions, fixed-geometry curve and independently evaluated classifier artifact; optional L4 promotion record if claimed.
6. For Demo Complete: five reviewed literal beat contracts, shared guard-compliant panel and four version-pinned Loom manifests using persisted episodes.
7. Per-claim/per-beat readiness registry showing IMPLEMENTED_AND_VALIDATED versus CLAIM_RESTRICTED/CONTRACT_REVISED/BLOCKED, with links to actual evidence rather than self-certification.

### 10.2 Read-only design provenance

This document is the sole authored artifact of this task. No source, provider, preseed, test, application configuration, database or centroid export was modified; no git command, application startup, AGE query or test suite was run for this design. Existing audit results are cited as prior results, not rerun evidence. The complete mandatory reading gate was satisfied before the design was assembled.

The initial three-repository source inventory contained **2,817 .py/.ts/.tsx files**, excluding dependency/build/cache directories. Its aggregate SHA-256 was **57b47eb83b571f6c3b96d04db823c9c9e82fd5a838ff3813d56098e4a016b884**. The final check reproduced that exact hash for all 2,817 original files, and all ten mandatory-reading file hashes below were unchanged. One additional helper, copilot-sdk/.codex_tmp/prep_v9_merge.py, appeared during the task; this task did not create or modify it. Including that additional file, the observed inventory was 2,818 files with aggregate **635244f939bea1e03ebf57f3f97a1a86320677316e3cd784a4dcbddb37b48a3f**. This qualification distinguishes the task's read-only behavior from unrelated shared-workspace activity.

| Authority / implementation | SHA-256 at design read |
| --- | --- |
| Comprehensive audit | 91dcb88000e225540d6ce509724932cebd31ac346b16cfacbe467297e5658a3c |
| Pre-paper v8 | 8c658dbb545386c6c22fdfd8ab352915c919aecfc325b0472bcc9d2677b0fff8 |
| Graph architecture v4 | f3254151ed1e755333066243f302f06341d43db904ade6700a8dfbb1a8f77ef9 |
| Implementation design v4 | c605615f5db6da77f156b81a22a75db9389c46dc0b223c71f6c708b07d090e55 |
| SDK investigation core | a1531aea56125475f29cebec64b197a500a7a82bdf56fa1caa1c567ca9c8672a |
| SDK investigation router | f30767bc7080196a358569a16b34ac8159c6250aca3d3fc6244368067bfc8e90 |
| Scorer proxy | e32406d4b450771f69ed23a03e82fc6c560ef0e44d931635d13d296c96b7b878 |
| SOC investigation loop | 49a05415379bdcf9ab7748263170b5a6e1fb5752d6ac6bd296a40b83ca33f856 |
| Validation report generator | 2ec557a55b8bd37d22725d2fa511649f072b72aefcb1b4678395218178904955 |
| Integration suite | 09392cfd5d9245c27b22bc8462794eccec36796d21c7ccf4d281d8a53a94d20b |

Sole authored path: copilot-sdk/docs/design/vld_e2e_architecture_design_2026-09-12.md.
