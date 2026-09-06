# CI VLD Design-Space Parameterization v1

Purpose: parameterize the VLD/CI graph-reasoning architecture search before selecting an experiment or implementation. This is a design-space map, not a recommendation, validation result, or production integration plan.

Grounding sources read for this parameterization:

- `docs/design/ci_vld_depth_memo_v3_1.md`: current VLD formalism, guards, experiment program, integration options, and decision families.
- `../graph-attention-engine-v50/gae/profile_scorer.py:97-145`, `:408-438`: `ScoringResult` fields and centroid L2 scoring over `mu[c,a,:]`.
- `copilot_sdk/situation/analyzer.py:20-152`: `SituationAnalyzer` is a dispatcher over traversal patterns with bounded traversal depth; it is not a native iterative update operator.
- `copilot_sdk/scoring/scorer.py:117-180`, `:377-545`, `:923-970`, `:2583`: current `CompoundingScorer`, mutating score/learn paths, read-only scoring, historical model-state scoring, and GAE scorer access. The memo's older `copilot_sdk/scoring/compounding.py` and `storage.py` paths are stale in this checkout.
- `../graph-attention-engine-v50/gae/calibration.py:194-248`, `copilot_sdk/backend/conservation_router.py:24-69`: `theta_min = 23.53 / (alpha * V)` and `alpha*q*V >= theta_min` conservation checks.
- `copilot_sdk/scoring/fingerprint.py:27-83`, `copilot_sdk/scoring/scorer.py:2262-2278`: factor fingerprint sigma and inverse-sigma-derived weights.
- `copilot_sdk/evolution/evolver.py:27-120`, `copilot_sdk/ae/gate.py:12-52`: governed sidecar and promotion gates.
- `copilot_sdk/backend/scoring_router.py:203-234`: POST `/api/score` uses context loading, threadpool scoring, and mutation lock.
- `copilot_sdk/graph/protocol.py:16-80`, `:264-330`: graph store contracts and governed-memory extension.
- Presets: SOC `6x4x6`, Trading `5x4x10`, Purchasing `5x4x7`, DataOps `6x5x6`, S2P `5x5x8` from `copilot_sdk/scoring/presets/*.py`.

Current graph-data caveat: a read-only live AGE check found `GRAPH_DSN` set, but only one verified decision each for Purchasing, Trading, DataOps, and S2P in the current graph; SOC count failed with an AGE `cypher(cstring)` error. Production-trace characterization therefore needs a separate point-in-time verified corpus or a repaired count/query path before it can carry statistical claims.

## A. Architecture Decisions

| Decision | Type | Option-set or range | Grounding | Depends-on / constrains |
|---|---|---|---|---|
| A1. Operator role | Categorical | transform factor vector; context refresh; score rerank; centroid-assignment / EM-like reassignment; retrieval-only; sidecar recommendation | Memo §6/§10; `ProfileScorer.score()` consumes factor vectors and centroids; `SituationAnalyzer` traverses graph context but does not update vectors natively | Constrains attach point, feedback type, conservation coupling, metrics, and replay fidelity |
| A2. Execution locus | Categorical | in-scorer; pre-score adapter; post-score readout; sidecar/shadow only; offline replay only | POST `/score` currently wraps scorer in router/threadpool; `AgentEvolver` exists as sidecar | Constrains latency budget, mutation risk, provenance, and deployment path |
| A3. Depth structure | Categorical | fixed L; adaptive fixed-point; adaptive conservation-headroom; adaptive entropy/margin; branch-and-select | Memo formalism `v_{t+1}=(1-eps)v_t+eps Phi(...)`; conservation and score outputs expose confidence/gap/entropy | Requires stability metrics and halt rules; constrains cost |
| A4. Termination action | Categorical | emit best action; abstain/escalate; emit with lower confidence; defer to L=1; sidecar-only recommendation | Conservation check returns GREEN/AMBER/RED/pass; scorer returns action/confidence/probabilities | Constrains value metric and product semantics |
| A5. State mutability at inference | Binary | frozen mu; mutable mu | Memo invariant says frozen mu. Current `score_read_only` and `score_with_model_state` support frozen replay; `learn()` mutates separately | Mutable mu during VLD is incoherent for inference-depth experiments and collapses into learning-time gamma |
| A6. Graph temporal mode | Categorical | synthetic graph-free; synthetic graph with known GT; production point-in-time cut; live graph current-state replay | Memo guards require non-circular synthetic for architecture/stability and temporal cut for production truth | Production cells require leakage probe and verified outcomes |
| A7. Traversal scope | Categorical | no graph; decision-local context; implicated entities; neighborhood to SA max depth; cross-domain transfer context | `SituationAnalyzer` has `default_max_depth=3`, `max_allowed_depth=5`; graph protocol exposes decisions/outcomes/evidence | Constrains cost, firewall exposure, and leakage risk |
| A8. Decision emission surface | Categorical | action index only; full probability vector; action plus abstain; action plus explanation trace | `ScoringResult` includes action, probabilities, distances, confidence, entropy, confidence gap | Constrains metrics and user-facing provenance |
| A9. Architecture owner | Categorical | scorer-owned; SA-owned; conservation-owned; AE sidecar-owned; orchestration/router-owned | Code has distinct scorer, SA, conservation router, AE, and backend router surfaces | Constrains test seam and production ownership |
| A10. Compute-budget placement | Categorical | all cases; hard-tail only; conservation-amber only; user-triggered/audit only | Memo says spend depth where it helps; scorer exposes margin/confidence; conservation exposes headroom | Constrains latency/cost and easy-case churn interpretation |

## B. Hypothesis Dimensions

These are dimensions the design space must span. They are not selected or tested here.

| Decision | Type | Option-set or range | Grounding | Depends-on / constrains |
|---|---|---|---|---|
| B1. Inference-time contraction claim | Mechanistic hypothesis | globally contractive; locally contractive in interior; non-contractive/expansive; contractive only after projection | Memo §5; current code has no VLD operator, so contraction is a property of proposed Phi plus damping | Requires stability instrumentation by region and epsilon/L sweep |
| B2. Sigma orthogonality at inference | Mechanistic hypothesis | sigma remains first-order orthogonal; sigma couples only near boundaries; sigma amplifies broadly; sigma is not predictive | Fingerprint computes per-factor sigma and weights; memo claims boundary second-order coupling | Constrains halt/abstain design and sigma-weighted feedback |
| B3. Depth not equal breadth | Architecture hypothesis | VLD adds value beyond matched one-pass context; equivalent to breadth; worse than breadth; complementary by region | Memo distinguishes inference depth from enrichment breadth; code has context-loading pre-score seam | Requires matched-compute and matched-evidence controls |
| B4. Value-invariant under metrics | Metric hypothesis | holds for truth accuracy; holds for graded reward; holds only after cost/abstain accounting; metric-specific artifact | Reward functions are domain-specific; scorer emits action probabilities but not domain utility | Constrains metric family selection and promotion criteria |
| B5. Complement vs duplicate learning-time gamma | Mechanistic hypothesis | VLD helps cold mu; helps converged mu; only duplicates learning trajectory; interferes with learning | Memo warns not to conflate learning-time gamma with inference-time contraction | Requires learning-stage sweep and frozen mu snapshots |
| B6. Inspectable deliberation claim | Governance hypothesis | pass-by-pass trace is causally useful; trace is decorative; trace exposes leakage/firewall violations; trace too costly | SA and graph store can provide context/evidence chains; no native VLD trace exists | Constrains provenance schema and audit-cost metric |

## C. Integration Decisions

| Decision | Type | Option-set or range | Grounding | Depends-on / constrains |
|---|---|---|---|---|
| C1. Attach point | Categorical | factor-vector; graph-context; score-readout/rerank; centroid-assignment; sidecar-only | Memo §6; code has factor scoring, context loading, read-only scoring, and AE sidecar | Constrains valid feedback signals and conservation coupling |
| C2. Feedback signal | Categorical | implicated entities; residual to winning centroid; residual to runner-up; uncertainty/entropy; sigma-weighted residual; conservation headroom; random/placebo; none/L=1 | Memo draft options; scorer exposes centroids/probabilities/confidence; fingerprint exposes weights | Must include placebo in every experimental cell |
| C3. Context admission rule | Categorical | no admission; monotone bounded admission; fixed top-k entities; evidence-tier filtered; unbounded refresh | Memo flags firewall risk; graph protocol has evidence receipt/provenance hooks | Constrains firewall integrity and leakage risk |
| C4. Conservation coupling (C-COUPLE) | Categorical | pre-loop gate; per-pass gate; halt-on-headroom; post-loop gate only; no coupling | Conservation check is separately implemented and route-exposed | No-coupling cells are negative controls only, not candidates for production architecture |
| C5. Firewall preservation | Categorical | verified-only; enrichment read-only with tier labels; enrichment admitted with decay; unverified writes; external retrieval | Memo invariant: enrichment is firewalled; repo rules require provenance/substantiation tiering | Constrains provenance and valid value claims |
| C6. Provenance / trace granularity | Categorical | final-only; per-pass vector; per-pass context/evidence; per-pass conservation; full replay transcript | Score result already has final fields; SA context has nodes/edges/evidence; VLD trace absent | Constrains audit cost and storage |
| C7. Replay fidelity tier | Categorical | factor-level approximation; SA replay adapter; production-equivalent offline adapter; live production hook | Memo says approximation bounds, not proves; code has SA dispatcher but no VLD operator | Constrains claim tier and experiment interpretation |
| C8. Mu snapshot strategy | Categorical | bootstrap canonical mu; latest live mu; historical checkpoint; temporal pre-outcome snapshot | `CompoundingScorer` stores canonical mu and supports `score_with_model_state`; production needs point-in-time | Constrains temporal integrity and learning-stage dimension |
| C9. Graph access mode | Categorical | no graph; local SQLite/memory; AGE read-only; AGE with historical cut; sidecar materialized projection | Graph protocol abstracts store; AGE client wraps Cypher and direct queries | Constrains latency and leakage probes |
| C10. Router/runtime integration | Categorical | offline harness only; backend replay endpoint; `/api/score` inline; async sidecar; AE shadow path | `/api/score` currently holds mutation lock in sync threadpool; AE has shadow runner | Inline score integration constrains latency and concurrency |
| C11. Action selection after loop | Categorical | final vector nearest mu; aggregate votes over passes; best conservation-safe pass; abstain if unstable; rerank only | ProfileScorer action comes from probabilities/distance; memo defines halt/abstain options | Constrains metrics and pass trace requirements |
| C12. Placebo construction | Categorical | random entities; irrelevant same-domain context; shuffled residual; permuted sigma weights; no-op smoothing | Memo requires placebo; code can expose vectors, fingerprints, context | Must be structurally matched to real condition per attach point |

## D. Metric Candidates

| Decision | Type | Option-set or range | Grounding | Depends-on / constrains |
|---|---|---|---|---|
| D1. Truth accuracy | Candidate primary metric | exact action correctness; top-k correctness; calibrated action success; abstain-aware accuracy | Memo invariant: verified outcomes only; graph protocol exposes verified decisions/outcomes | Requires held-out verified outcomes and leakage probe |
| D2. Graded reward | Candidate value metric | domain reward; normalized reward; regret vs verified action; cost-weighted reward | RL package has domain reward functions and exploration policy | Requires per-domain reward normalization |
| D3. Net value | Candidate value metric | hard gain minus easy churn; hard gain minus churn and abstain cost; utility-weighted net | Memo names net-value; easy-case churn is required control | Requires region split and abstain semantics |
| D4. Hard-tail definition | Candidate stratifier | low margin; high entropy; near theta_min/headroom; high sigma; disagreement/residual; composite quantile | Scorer exposes confidence/gap/entropy; conservation exposes headroom; fingerprint exposes sigma | Constrains which cases VLD is allowed to affect |
| D5. Real-minus-placebo | Candidate mechanism metric | mean difference; paired per-seed difference; sign consistency; domain-level consistency | Memo says real-placebo is effect of interest | Requires placebo matched to every real cell |
| D6. Cost-adjusted value | Candidate operating metric | ms/pass; graph queries/pass; tokens/context bytes; accuracy per ms; abstain per cost | POST `/score` is latency-sensitive and uses graph/context loading | Constrains L_max and traversal scope |
| D7. Generalization | Candidate architecture metric | cross-seed; cross-domain; tensor-shape normalized; post-snapshot production; synthetic-to-production transfer | Presets define heterogeneous shapes across five copilots | Requires common normalized geometry axes |
| D8. Robustness | Candidate safety metric | perturbation stability; adversarial context; missing graph edges; stale mu; noisy sigma | Fingerprint, graph store, and context adapter create realistic perturbation seams | Constrains production readiness |
| D9. Audit cost / inspectability | Candidate governance metric | trace length; provenance completeness; human review time; replay determinism | Memo differentiates inspectable depth from latent depth; code has evidence/provenance hooks | Constrains trace granularity and storage |
| D10. Abstain calibration | Candidate safety metric | abstain precision; false-abstain rate; unsafe-action reduction; boundary sigma blow-up rate | Conservation and entropy/margin outputs can support abstain rules | Requires explicit abstain action semantics per domain |

## E. Continuous Knobs

| Knob | Type | Plausible range | Code bounds / grounding | Depends-on / constrains |
|---|---|---|---|---|
| E1. Damping epsilon | Continuous / grid | `{1/L, 0.05, 0.1, 0.25, 0.5, 1.0}` for characterization | Memo suggests `{1/N, 0.1, 0.25, 0.5, 1.0}`; current scorer does not implement VLD epsilon | Constrains contraction/stability and latency-value curve |
| E2. Loop depth L | Integer | `1..6` first pass; extend to `10` only if no plateau | Memo first move uses `L=1..6`; no code-imposed VLD loop exists | Constrains cost, termination, trace length |
| E3. Fixed-point delta | Continuous | `1e-4..5e-2` normalized vector norm | No code bound; scorer vectors are finite and expected `[0,1]` | Only applies to adaptive fixed-point depth |
| E4. Conservation headroom halt | Continuous | halt when `signal/theta_min >= {1.0, 1.25, 2.0}`; abstain below 1.0 | `check_conservation` labels AMBER/GREEN around `theta_min` and `2*theta_min` | Applies only to C-COUPLE cells |
| E5. Hard-tail quantile | Continuous / quantile | bottom `{5%,10%,20%,30%}` margin or top entropy/sigma quantile | Score output exposes confidence gap and entropy; fingerprint exposes sigma | Constrains power and operating envelope |
| E6. SA traversal depth | Integer | `0..5`, default `3` | `SituationAnalyzer(default_max_depth=3, max_allowed_depth=5)` | Constrains context cost and leakage/firewall risk |
| E7. Context top-k / admission budget | Integer | `0..20` entities or evidence items; start `{0,1,3,5,10}` | No native VLD code bound; graph traversal and evidence chains can grow | Constrains latency and firewall exposure |
| E8. Sigma amplification bound | Continuous | max per-pass sigma ratio `{1.0,1.1,1.25,1.5,2.0}` | Fingerprint sigma floor is `0.01`; weights normalized by max inverse variance | Constrains abstain vs iterate boundary |
| E9. Temperature / calibration tau | Continuous / fixed for controls | hold production tau fixed; sensitivity only after architecture map | ProfileScorer validates positive tau; comments cite `tau=0.1` as calibrated | Changing tau can create readout placebo artifacts; keep out of primary architecture cells |
| E10. Learning-stage snapshot age | Continuous / staged | bootstrap; early `n<30`; mid; converged; latest live | Canonical bootstrap mu exists; historical state scoring exists | Applies to complement-vs-gamma hypothesis |
| E11. Placebo strength | Continuous / matched | same pass count and epsilon; context/residual distribution matched by norm | Memo requires same structure; code supplies vector/context features | Constrains interpretation of real-minus-placebo |

## F. Dependency / Coupling Structure

Adjacency list of practical dependencies after collapsing the naive cross-product:

1. A1 operator role -> C1 attach point, C2 feedback signal, C11 action selection.
2. A2 execution locus -> C10 runtime integration, C6 trace granularity, D6 cost metric.
3. A3 depth structure -> E1 epsilon, E2 L, E3 delta, E4 conservation halt.
4. A4 termination action -> D3 net value, D10 abstain calibration, C4 conservation coupling.
5. A5 frozen mu -> C8 mu snapshot strategy; rules out learning-time updates inside loop.
6. A6 graph temporal mode -> C9 graph access mode, D1 truth accuracy, leakage probes.
7. A7 traversal scope -> C3 admission rule, E6 traversal depth, E7 top-k budget.
8. A8 emission surface -> D1/D2/D9 metric applicability and C6 trace storage.
9. A9 architecture owner -> C10 deployment seam and C7 fidelity tier.
10. A10 compute-budget placement -> D4 hard-tail definition and D6 cost-adjusted value.
11. B1 contraction -> E1/E2/E3 and stability-region reporting.
12. B2 sigma orthogonality -> C2 sigma-weighted feedback, E8 sigma bound, D10 abstain.
13. B3 depth-vs-breadth -> C3 admission rule and matched compute/evidence controls.
14. B4 value-invariant -> D1/D2/D3/D6 metric selection.
15. B5 complement-vs-gamma -> C8 snapshots and E10 learning-stage age.
16. B6 inspectability -> C6 provenance and D9 audit cost.
17. C1 factor-vector attach -> residual/sigma/entity-derived vector feedback only; excludes pure retrieval metrics.
18. C1 graph-context attach -> requires C3 admission/firewall and C9 graph access.
19. C1 score-readout attach -> requires D1 truth accuracy and placebo guard against calibration-only wins.
20. C1 centroid-assignment attach -> requires frozen mu and wrong-basin diagnostics.
21. C4 per-pass conservation -> requires conservation features per pass and an abstain action.
22. C7 replay fidelity -> caps evidence tier and allowed claims.
23. C8 temporal snapshot -> constrains production data eligibility and excludes outcome/later nodes.
24. C12 placebo construction -> must match C1/C2; invalid if weaker or cheaper than real feedback.
25. D4 hard-tail split -> controls A10 hard-tail-only compute and D3 easy-case churn.
26. E6 SA traversal depth -> bounded by current analyzer max depth 5 unless code changes.

Collapsed dimensionality: the full cross-product is not meaningful. The first meaningful block is `operator role x attach point x feedback x depth/halt x region`, then restricted by instrument. Production cells further require `temporal snapshot x verified outcome x leakage probe`; synthetic cells replace temporal data with independent ground truth and can sweep geometry broadly.

## G. Invalid / Incoherent Combinations

1. Mutable mu inside the VLD loop plus an inference-depth claim: this becomes learning, not inference.
2. Production live-graph replay without point-in-time cut: leaks outcomes/later context.
3. Distance-to-mu convergence as primary success metric: circular because the loop is defined against mu.
4. Real arm without matched placebo arm: cannot separate reasoning from smoothing.
5. Score-readout/rerank attach judged only by confidence or entropy: calibration artifact risk.
6. Retrieval-only operator called VLD-depth: it has no decision geometry to converge against.
7. Unbounded context refresh with firewall-preservation claim: violates enrichment firewall.
8. Centroid-assignment attach with mu updates during pass: mixes EM-like assignment with state learning.
9. Sigma-weighted feedback without enough verified decisions for a valid fingerprint: fingerprint returns insufficient-data defaults below five compatible decisions.
10. Conservation-coupled halting without defined abstain/defer semantics: cannot compute net value.
11. Cross-domain pooled production metric without per-domain consistency: hides domain nulls/artifacts.
12. Synthetic vectors drawn around learned mu for mechanism proof: reintroduces circularity.
13. Placebo arm with fewer graph reads, smaller epsilon, or lower L than real arm: not structurally matched.
14. SA replay claims at production-equivalent fidelity when only factor-level approximation was used.
15. Hard-tail jump to near-perfect accuracy in production trace: treat as leakage alarm, not confirmation.
16. Changing tau/readout calibration in a VLD-depth primary cell: confounds depth with calibration.
17. AGE live graph with current verified counts as primary production sweep: underpowered in the current environment.
18. Traversal depth above 5 using current `SituationAnalyzer` without source change: unsupported by code.

## H. Open Definition Questions

1. What is the canonical per-domain verified corpus for production sweeps? The current live graph appears underpowered.
2. What timestamp/snapshot field establishes point-in-time cuts for mu, graph context, outcomes, fingerprints, and evidence receipts?
3. What exact object is Phi allowed to return at each attach point: vector, context delta, score delta, candidate assignment, or sidecar advice?
4. How should SA traversal output be converted into a factor-vector update without inventing domain semantics?
5. What counts as decision-implicated context for each copilot: entity IDs, policies, evidence chain, category neighbors, or outcome analogs?
6. What is the abstain/defer action and utility cost in each domain?
7. Which reward function is authoritative per copilot for graded reward and regret normalization?
8. Are sigma values intended to be static per mu snapshot or recomputed for each temporal fold?
9. Does C-COUPLE gate each intermediate `v_t`, each emitted action, or both?
10. What fidelity threshold upgrades a factor-level approximation from bounds-only evidence to architecture evidence?
11. What trace schema is sufficient for audit without making the loop too expensive to deploy?
12. How should breadth be matched: same graph reads, same context bytes, same latency, or same number of operator invocations?
13. Should VLD ever run on easy cases in production, or only as an experiment for churn measurement?
14. How should SOC be handled if AGE count queries fail while other domains return counts?
15. What are the valid hard-tail definitions per domain when class imbalance or abstain regions differ?
16. Are AgentEvolver promotions allowed to evolve Phi itself, or only suggest sidecar variants around a frozen Phi family?

## I. Additions from Code / Removals

Additions from code:

1. `score_read_only` and `score_with_model_state` are concrete replay hooks. They make frozen-mu, historical-snapshot experiments real rather than speculative.
2. `SituationAnalyzer` has an implementation bound: traversal depth is capped at `max_allowed_depth=5` by default. Traversal depth is a real knob only within that bound unless source changes are allowed.
3. Fingerprint sigma has an insufficient-data behavior. Below five compatible verified decisions, sigma is `0.5` and weight is `0.0`; sigma-weighted VLD cells are not meaningful without enough compatible verified data.
4. `/api/score` already loads context before scorer invocation and then runs synchronous scoring in a threadpool under a mutation lock. Inline VLD would hit latency/concurrency constraints; offline and sidecar loci are lower-risk design seams.
5. Conservation what-if support is already route-exposed, so C-COUPLE can be characterized without modifying scorer code.
6. AE promotion gates are conservative and paired. If VLD operator evolution is assigned to AE, paired baseline/candidate observations and conservation-green conditions become native constraints.
7. Preset tensor shapes differ enough that shape-normalized synthetic sweeps are necessary: SOC `6x4x6`, Trading `5x4x10`, Purchasing `5x4x7`, DataOps `6x5x6`, S2P `5x5x8`.
8. Current live AGE verified-decision counts are not sufficient for production primary conclusions in this environment.

Removals / merges:

1. Remove `retrieval-only` as a candidate VLD architecture. Keep it only as a negative control or breadth comparator.
2. Merge `score-readout` and `rerank` unless a future implementation distinguishes logit calibration from rank-only transforms.
3. Merge `fixed-point delta` and `delta-convergence halting` as one decision/knob pair.
4. Treat `none` feedback as L=1 baseline/no-op control, not an architecture family.
5. Treat live production hook as code-unsupported for this read-only design phase; only offline replay and sidecar/shadow are currently safe for characterization.
6. Treat `tau` as a sensitivity/control knob, not an architecture parameter, because changing it can mimic score-readout wins.

Counts for this parameterization:

- Decision families: 4.
- Discrete decisions: 38.
- Discrete options: 166.
- Continuous knobs: 11.
- Dependencies: 26.
- Invalid/incoherent combinations: 18.
- Open definition questions: 16.
- Code-unsupported or removed/merged options: 6.
