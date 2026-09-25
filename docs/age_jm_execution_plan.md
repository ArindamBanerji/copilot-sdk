# AGE–JM Dependency-Ordered Execution Plan

Date: 2026-09-22  
Status: planning only; no implementation or runtime verification performed.  
Primary repository: copilot-sdk; implementation spans its three sibling repositories.  
Baseline: [compliance report](age_jm_compliance_report.md), G001–G066 (P1=23, P2=25, P3=7, P4=9, P5=2).  
Plan: **10 phases, 55 engineering days** for one experienced implementer, including tests and migration rehearsal. This is not calendar time or an estimate derived mechanically from the report's LOC figures. Allow approximately 15 additional contingency days if OPEN candidates or legacy-data reconciliation expand the known scope; re-estimate explicitly rather than skipping work.

## 1. Principles

### 1.1 From / to

**FROM:** core AGE Decision storage surrounded by SQLite utility/signal/holdout stores, JSON journals and fingerprints, process-memory episodes, fixture evidence, copied framework helpers, partial graph relationships and catch-and-continue persistence.

**TO:** all authoritative episodic, semantic, procedural and judgment memory lives in **one AGE graph, soc_graph, in the same resolved database**. GraphStore is the application boundary; GraphConfig is the configuration boundary. Single-domain reads stay scoped. Explicitly authorized source/target cross-domain reads traverse the same graph. Required graph errors raise; the HTTP boundary translates them into a truthful unavailable/error response, never success with substituted data.

An API orchestrator, event bus, second database or application-side join across separate stores is **not** an acceptable implementation of a JM memory interaction. Pure numerical computation on graph-derived, versioned state is allowed; the requirement is not “move every floating-point operation into Cypher.” Local caches may hold derived copies only, may not become authority on graph failure, and must be discardable/reconstructable solely from AGE.

Production imports must not construct or depend on SQLite/InMemory/fixture-backed authoritative stores. Offline examples, tests, migration input readers and exports remain permitted only outside the production dependency graph, with explicit profiles and non-production provenance. A grep hit in a validation error message, JSON serialization of a graph property, or app.db module name is not itself a storage bypass. The final gate combines lexical discovery, dependency/AST checks and fault tests—not a naive ban on the word “sqlite.”

### 1.2 Architecture requirements read from the actual paper

Source precedence: this request and the seven design goals define the implementation contract; the current paper supplies memory/lifecycle/conservation semantics; the compliance report supplies gap IDs; source code supplies current locations. Old unification documents contain stale implementation findings and must not override a current source check.

| Requirement | Source | Executable acceptance obligation |
|---|---|---|
| R1: J=(M, σ, S), created from verified outcomes | docs/design/latest_docs_v1/jm_paper_draft_v13.md §3.1, lines 317–388 | Persist versioned centroids, noise/discriminability measurements and conservation state with derivation links to verified outcomes; inspect and rebuild them after restart |
| R2: Four memory types share one graph | Paper §3.2–3.4, lines 390–496 | Episodes, entities, policies/rules and judgment versions coexist with actual edges, not only unrelated JSON payload nodes |
| R3: Four native interaction classes | Paper §3.4, lines 461–496 | One instrumented Cypher traversal per interaction: episodic×judgment, semantic×judgment, procedural×judgment, cross-domain judgment×judgment; return evidence paths |
| R4: Deployment-time conservation | Paper §4.1, lines 502–544 | Derive V, q, α and thresholds from the same committed graph snapshot; gate autonomous changes against that snapshot and reject stale-version races |
| R5: Decision/Observation lifecycle boundary | Paper §4.2, lines 546–569 | Pending/Observation/archived records do not contribute to V or centroid/evolver learning; preview GETs never create countable Decisions |
| R6: Circuit breaker, not an adaptive controller | Paper §4.3, lines 571–614 | Degraded/unavailable conservation cannot silently enable autonomy or reset GREEN. Recalibration/supervised recovery is explicit, versioned and audited |
| R7: Contextual and governed transfer | Paper §6.4, lines 1251–1326 | Entity-context-conditioned judgment, transfer with both source/target conservation evidence, and reviewer/time-linked quality-change analysis are traversable without second-store lookups |
| R8: One engine and an inspectable feedback cycle | innovation_note_v32.md, lines 20–85; ci_blog_v22.md, architecture section and lines 196–207/604–620 | Ingest → decide/abstain → verified outcome → updated judgment/procedure uses shared contracts, with provenance and fixed governance envelope |

Important scientific limits: §6.4 explicitly concedes that a carefully joined separate-store implementation can reproduce an individual capability; E-JM-7 is not proof of graph necessity or a guaranteed accuracy improvement. We choose the shared graph because it is the required architecture. Do not use illustrative 1.8×/2.7× figures, chart captions or marketing ROI as acceptance thresholds. The paper's σ/discriminability measurement survives; it warns against enabling DiagonalKernel scoring by default. Preserve the validated scoring kernel unless separately authorized.

Conservation reference semantics to test:

- α = verified category coverage c_d/C; q is confirmed/verified within the latest **400** eligible verified Decisions; V counts eligible confirmed/overridden Decisions only.
- α·q·V ≥ θ_min, with the paper's reference θ_min = 23.53/(α·V). Handle α·V=0 explicitly as insufficient evidence, never division-by-zero or fabricated GREEN.
- Per-category eligibility uses q_k·V_k ≥ θ_cat with an explicit calibrated policy version; do not circularly gate coverage using its own derived value.
- Confirmed/overridden centroid steps are respectively 0.05/0.01 in the reference policy. Existing approved domain policy overrides must be inventoried, versioned and justified; do not silently retune production constants or equate a legacy field named alpha with category coverage.
- Recording a human verification and authorizing an autonomous learning/promotion are distinct. Persist the verification even if the gate denies autonomous learning. Bootstrap/recalibration may permit explicitly supervised updates through a separate audited policy; never make cold-start or preseed a general conservation bypass.

The innovation note's “six graphs” language is treated as logical domains/source-system graphs ingested into the one governed substrate, not permission to create six authoritative memory stores.

### 1.3 Seven design goals and permanent rules

| Goal | Standing rule | Final gate |
|---|---|---|
| DG-1 | All Decision access and authoritative memory operations through AGE-backed GraphStore; drivers only inside the adapter/approved offline tooling | Import/call-boundary audit + per-app live CRUD/outcome tests |
| DG-2 | Resolve DSN/graph once through GraphConfig, inject it everywhere | Alias-precedence tests and actual database/graph identity agreement |
| DG-3 | Required AGE failure raises; no substituted SQLite/memory/fixtures/empty success | Fault every required operation and inspect API, graph and in-memory state |
| DG-4 | Bind domain on every Decision alias and entity root/intermediate; reviewed cross-domain queries explicitly bind source and target | Same-ID cross-domain collision tests + authorization-negative tests |
| DG-5 | Explicit domain on every Decision write | Reject absent/foreign domain and query census for unstamped Decisions |
| DG-6 | All five use same database and soc_graph, not merely matching names | Shared backend-issued storage identity and cross-copilot path witness |
| DG-7 | Close every authoritative non-unified path and dispose of all candidates | Zero OPEN production candidates; strict runtime dependency and outage gates |

No git in any execution prompt. Preserve unrelated files/changes. Do not change the paper or rewrite the historical compliance report to make a gate pass. Do not delete legacy stores before verified migration and retention approval. No production database reset, seed, migration, outage injection, deployment or real external action without explicit target-specific operator approval. All development writes and failure tests use a disposable database and isolated app data directories.

### 1.4 Target graph contract (design to implement; names may reuse compatible existing labels)

| Memory / control | Required representation and relationships |
|---|---|
| Episodic | Domain-scoped Event/Observation/Decision, immutable verification/Outcome and acquisition trace; source identity, timestamps, schema and provenance; Decision → evidence/entity/Outcome |
| Semantic | Typed Entity and versioned Observation/source facts, entity groups and process relationships; source-domain-qualified identities; consumed observation version linked to Decision |
| Procedural | Rule/Variant, Evaluation, Promotion/Authority and immutable state versions; supporting Decision/receipt edges and activation/rollback evidence |
| Judgment | Versioned centroid/fingerprint/factor-quality/K-utility state, per-category or entity-context partitions where applicable; updates linked to verified outcomes and supporting trace |
| Conservation | Versioned snapshot and policy/calibration identity, eligible-set/version, V/q/coverage/status; links from guarded operation and both domains of a transfer |
| Transfer | Source judgment version → validated mapping/TransferPattern → target judgment version, with source/target conservation and durable application receipt |
| Governance | Canonical receipts, hash/provenance verification, operation/idempotency identity, evaluation/holdout markers that cannot inflate live V |

Serialized arrays/snapshot payloads are allowed for numerical efficiency **in addition to** the relationship spine. No surrogate DecisionEntityLink node, JSON ID list or application-side stitch may be the only representation of a required relationship. Nonexistent source entities must cause rejection or an explicitly typed/provenanced placeholder according to a reviewed policy; never fabricate real semantic facts.

Use composite identities (domain, object_id, schema/version); preserve legacy Decision IDs through domain-qualified migration mappings. Global uniqueness of bare IDs is not assumed. Scope by tenant as well wherever the existing platform exposes tenants; never allow a cross-domain operation to imply cross-tenant access.

### 1.5 Transaction, failure and replay decisions

Reuse/extend existing ci-platform/ci_platform/graph/age_graph_store.py:AGEGraphStoreTransaction and run_transaction, and AGEClient's transaction support. They currently cover only part of the needed write set. Do not wrap several independently committed _run_query calls and call that atomic.

An accepted score commits the Decision, required context/factor/domain links and score receipt atomically. A verified learning operation records a canonical outcome, durable operation receipt and an applied-or-denied learning disposition; an applied operation atomically commits all required derived state, conservation and version links before swapping the in-memory learner. If learning is denied, persist the verified outcome and denial without moving the learner; eligibility and learning versions remain explicitly distinguishable. Use optimistic version checks/appropriate database locking and deterministic idempotency keys.

On a lost commit acknowledgment, return an indeterminate/unavailable result carrying a stable operation key—not ordinary success or a claim that nothing committed. A status/retry lookup on that key resolves the result without duplicate outcome/centroid/utility updates. Network partitions and two independent writers must be tested.

Remove production SQLite repair-queue creation/draining. A graph-resident operation ledger may track intents when AGE is available; when it is unavailable, reject rather than pretend a local queue is equivalent. Legacy SQLite repair queues are offline migration inputs only, destination-bound and explicitly reviewed; ambiguous destination records are quarantined, not auto-replayed or discarded. Diagnostic logs are not canonical memory.

Newly rechecked residual examples reinforce the need to process OPEN candidates: age_graph_store.py:_run_query returns [] for PoolClosed despite otherwise raising; scorer.py has COPILOT_PRESEED_MODE and cold-start/BOOTSTRAP passed branches. Phase 2 must cover the former under G009, Phases 3/9 the latter under G003/G056. These are scope refinements within the 66 groups, not invented additional gap IDs.

### 1.6 Execution environment and proposed verification assets

Run prompts from:
C:/Users/baner/CopyFolder/IoT_thoughts/python-projects/kaggle_experiments/claude_projects

All paths in phase prompts are workspace-relative, including the copilot-sdk prefix. CLAUDE_S2P was checked and points at the sibling s2p-copilot repository; future sessions must re-resolve it rather than assume the variable exists. Do not repurpose HOME/CODEX_HOME.

**NEW assets below are specifications, not currently existing or already passed checks. Phase 1 creates the harness; later phases create their named tests before running them.** Reuse equivalent existing tests only if the mapping is explicit and all assertions remain covered.

- copilot-sdk/integration/age_jm/conftest.py: production-profile app subprocesses in separate working directories; no legacy tests/conftest.py SQLite overrides; safe real-AGE fixture; fail-on-skip/zero-collection enforcement.
- copilot-sdk/integration/age_jm/test_phase_01_contracts.py through the exact phase filenames below: parametrized across required domains, live adapter plus API tests.
- copilot-sdk/scripts/verify_age_jm_phase.py: validates prior-phase artifacts, current phase assertions/JUnit, source/config/schema fingerprints, manifest identity and candidate dispositions; exits nonzero on missing/stale evidence, skipped required tests or incomplete scope.
- copilot-sdk/docs/age_jm_execution_state.json: G001–G066 with phase, status, exact test node IDs, evidence path and source hash; not merely a list of covered IDs.
- copilot-sdk/docs/age_jm_candidate_dispositions.json: every Appendix A–F candidate and new scan hit, stable candidate ID, file/function/line, production reachability, memory authority, owner phase, resolution/test or narrow exclusion justification.
- .codex_tmp/age_jm/manifest.json and phase-NN evidence: isolated test-run artifacts, not production configuration. No credentials embedded in reports.

Manifest minimum: unique test_run_id; expected storage identity and graph_name=soc_graph; DSN obtained from GraphConfig/environment key, not plaintext artifact; disposable=true; mutation_allowed=true; safety marker verified against the target server; isolated data roots; production profile; demo/preseed bypass disabled; domain → backend/frontend URL mapping. Use an isolated **database** so the graph may still be named soc_graph; do not weaken production name guards to test. Refuse a production/default server even if someone labels a local JSON file disposable. Reset only objects/database owned by that test run, after identity confirmation.

Each app gets its own process to avoid collisions between Python packages named app. Keep real broker/SAP/payment/order actions disabled; tests use inert transport stubs at the external boundary, ingest records into AGE, and never substitute a GraphStore mock in live acceptance tests. Connection loss is injected only into test-owned connections/services.

Default developer ports in the request (SOC 8001, S2P 8002, Trading 8010, Purchasing 8020, DataOps 8030) are informational. The manifest owns all test URLs; do not stop existing services to reclaim a port.

Phase gate command contract, created in Phase 1:

```powershell
python -X utf8 -m pytest copilot-sdk/integration/age_jm/test_phase_01_contracts.py --age-jm-manifest .codex_tmp/age_jm/manifest.json --age-jm-require --strict-markers -q --junitxml=.codex_tmp/age_jm/phase-01.junit.xml
python -X utf8 copilot-sdk/scripts/verify_age_jm_phase.py --phase 01 --manifest .codex_tmp/age_jm/manifest.json --junit .codex_tmp/age_jm/phase-01.junit.xml --report .codex_tmp/age_jm/phase-01.json
```

The verifier reruns read-only invariant probes appropriate to the phase and checks a test execution manifest containing node IDs/counts/source hashes; it does not accept a hand-written “passed” JSON file. pytest hooks fail required skip/xfail, missing AGE and zero collected tests. Unit mocks remain useful but are reported separately.

The harness/CI foundation starts in Phase 1; **G061/G062 are not closed until Phase 9** when all interactions, migration and production boundaries are covered. Until then, exact known violations may be tracked in a shrinking baseline with owners; no new violations or expanding exemptions. Partial-phase CI success must be labelled partial, never platform compliant.

## 2. Dependency Graph

The phase order below is conservative and sequential. Each phase may take several future sessions; resume that phase until its gate is green. Do not skip to a later phase because its edit looks independent. No parallel-agent work is assumed or authorized by this plan.

```text
P1  Config + identity + domain isolation + required test foundation
 |
 v
P2  Atomic storage + durable scoring + reject synthetic transfers
 |
 v
P3  Versioned judgment/utility + conservation + atomic learning
 |
 v
P4  All app routes + shared helpers + SOC protocol-only access
 |
 v
P5  Graph-backed episodes, signals, holdouts and procedural authority
 |
 v
P6  Real graph-derived context, audit, analytics and preview boundaries
 |
 v
P7  Four native traversals + cross-domain transfer + investigation evidence
 |
 v
P8  Truthful all-five health/readiness + launcher gating
 |
 v
P9  Graph preseed/migration tools/examples + full CI + all-five E2E
 |
 v
P10 Authorized cutover/rollback proof + final closure
```

Key fix-level dependencies and reasons:

```text
G042 -> G060                         production factory contract before real app tests
G043 + G040 -> coherent scoped reads (and all later health/traversals)
G008 -> G003                        transaction-safe state before durable learning
G007 -> G039                        atomic Decision topology before removing link surrogates
G001 -> G002 -> G003 -> G004         accepted-write truth before learning and restart truth
G005 + G003 -> G006 -> G021          prohibit demo transfer before atomic application/impact
G003 -> G024 -> G025                 durable graph utility before verified feedback loop
G007 + G040 -> G041                  scoped atomic API before SOC raw-query removal
G003 + G007 -> G015/G018             S2P/SOC adopt the common learning transaction
G015 -> G035                        verified invoice outcomes before supplier profile replay
G024/G026/G035/G038/G039/G044 -> G047
G025 + G047 -> G048                  trace/utility and native traversal before evidence closure
G043/G004/G041 -> G049..G053 -> G054/G055
G001/G007/G054 -> G056 -> G057/G058 -> G063
G047 + G060 -> G061 -> G062          complete live architecture tests before strict final lint
G030/G056/G061 -> G064               graph episodes and deterministic seed before AGE E2E
G001/G003/G007/G040/G055/G056/G061 -> G065
G024/G027/G029/G031/G035/G038/G039/G058/G065 -> G066
```

The underlying report's **every listed dependency** is preserved. Within-phase task order below is also topologically sorted. Additional practical dependencies (e.g. schema before app migration, evidence providers before full-stack E2E) are enforced by the phase chain. G061/G062 harness work starts earlier, but their closure stays after the complete graph interactions.

### Complete gap-to-phase closure ledger

Each gap has exactly one closure phase. The phase's named integration file must contain the listed test prefix (parametrized route/site variants as needed); broader regression/E2E evidence is additional.

| Gap | Closure phase | Report prerequisites | Minimum acceptance test prefix |
|---|---|---|---|
| G001 | 2 | None | test_g001_ |
| G002 | 2 | G001 | test_g002_ |
| G003 | 3 | G001, G002, G008 | test_g003_ |
| G004 | 3 | G003 | test_g004_ |
| G005 | 2 | None | test_g005_ |
| G006 | 3 | G003, G005 | test_g006_ |
| G007 | 2 | None | test_g007_ |
| G008 | 2 | None | test_g008_ |
| G009 | 2 | None | test_g009_ |
| G010 | 4 | G001 | test_g010_ |
| G011 | 4 | None | test_g011_ |
| G012 | 4 | None | test_g012_ |
| G013 | 4 | None | test_g013_ |
| G014 | 4 | None | test_g014_ |
| G015 | 4 | G003, G007 | test_g015_ |
| G016 | 4 | None | test_g016_ |
| G017 | 4 | None | test_g017_ |
| G018 | 4 | G003, G007 | test_g018_ |
| G019 | 4 | None | test_g019_ |
| G020 | 4 | None | test_g020_ |
| G021 | 7 | G006 | test_g021_ |
| G022 | 4 | None | test_g022_ |
| G023 | 6 | None | test_g023_ |
| G024 | 3 | G003 | test_g024_ |
| G025 | 3 | G024, G003 | test_g025_ |
| G026 | 5 | None | test_g026_ |
| G027 | 5 | G003 | test_g027_ |
| G028 | 5 | None | test_g028_ |
| G029 | 5 | None | test_g029_ |
| G030 | 5 | None | test_g030_ |
| G031 | 5 | G003 | test_g031_ |
| G032 | 6 | None | test_g032_ |
| G033 | 6 | None | test_g033_ |
| G034 | 6 | None | test_g034_ |
| G035 | 5 | G015 | test_g035_ |
| G036 | 6 | None | test_g036_ |
| G037 | 7 | None | test_g037_ |
| G038 | 3 | G008 | test_g038_ |
| G039 | 2 | G007 | test_g039_ |
| G040 | 1 | None | test_g040_ |
| G041 | 4 | G007, G040 | test_g041_ |
| G042 | 1 | None | test_g042_ |
| G043 | 1 | None | test_g043_ |
| G044 | 7 | None | test_g044_ |
| G045 | 5 | None | test_g045_ |
| G046 | 4 | None | test_g046_ |
| G047 | 7 | G024, G026, G035, G038, G039, G044 | test_g047_ |
| G048 | 7 | G025, G047 | test_g048_ |
| G049 | 8 | G001, G004, G043 | test_g049_ |
| G050 | 8 | G043 | test_g050_ |
| G051 | 8 | G043 | test_g051_ |
| G052 | 8 | G043 | test_g052_ |
| G053 | 8 | G041, G043 | test_g053_ |
| G054 | 8 | G049, G050, G051, G052, G053 | test_g054_ |
| G055 | 8 | G002, G003, G049, G050, G051, G052, G053 | test_g055_ |
| G056 | 9 | G001, G007, G054 | test_g056_ |
| G057 | 9 | G056 | test_g057_ |
| G058 | 9 | G056 | test_g058_ |
| G059 | 9 | G047 | test_g059_ |
| G060 | 1 | G042 | test_g060_ |
| G061 | 9 | G047, G060 | test_g061_ |
| G062 | 9 | G061 | test_g062_ |
| G063 | 9 | G043, G058 | test_g063_ |
| G064 | 9 | G030, G056, G061 | test_g064_ |
| G065 | 10 | G001, G003, G007, G040, G055, G056, G061 | test_g065_ |
| G066 | 10 | G024, G027, G029, G031, G035, G038, G039, G058, G065 | test_g066_ |

## 3. Execution Phases

Each fenced block is a complete paste-ready session prompt. The referenced plan/report are local inputs a fresh session must read; line numbers are audit-era anchors, so resolve current functions before editing. Do not assume a renamed/deleted symbol means the gap is fixed—trace its replacement and prove the same gate.

The prompts authorize implementation **only when the user subsequently chooses to execute a phase**. They do not authorize source changes during this planning session. Gate commands are specifications for the Phase-1 harness and later test files, not claims those assets exist today.

### Phase 1: Production graph contract, isolation, and required test harness (estimated effort: 4d)

**Gaps closed:** G042, G043, G040, G060

**Depends on:** No earlier phase; requires approved disposable AGE test infrastructure.

**Repos touched:** copilot-sdk, ci-platform, s2p-copilot, gen-ai-roi-demo-v4-v50.

**Codex prompt specification:**

```text
/model astra
/reasoning high

Codex Prompt: AGE-JM-PHASE-01
Execute Phase 1 only: Production graph contract, isolation, and required test harness.
Workspace: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects
Repositories allowed: copilot-sdk, ci-platform, s2p-copilot, gen-ai-roi-demo-v4-v50.
Closure IDs, in implementation order: G042, G043, G040, G060.

RULES
- No git. Preserve unrelated work. Do not edit the JM paper or historical compliance report.
- Read copilot-sdk/docs/age_jm_execution_plan.md sections 1, 2, 4 and 7 and this phase, plus the complete assigned findings in copilot-sdk/docs/age_jm_compliance_report.md.
- Follow applicable AGENTS.md. Use current symbol definitions, not stale line numbers. Do not spawn agents unless separately authorized.
- Change only this phase's listed implementation targets, their typed adapter/protocol/call-site dependencies, tests/harness/CI required by this phase, and execution/candidate/session evidence. Explain any necessary scope expansion before changing unrelated components.
- Use a verified disposable AGE database with graph soc_graph, isolated app processes/data roots, production profile, and no demo/preseed conservation bypass. Never reset or fault the user's active database or invoke real broker/payment/SAP/order actions.
- Missing test infrastructure is BLOCKED, never a skipped PASS. No production deployment/migration without explicit target approval. Do not remove or overwrite original legacy stores.
- Each accepted operation must be durable and domain-scoped; graph errors cannot become fixture/local/empty-data success. No scoring-kernel or unapproved threshold changes.

PRE-CHECKS
1. Confirm workspace and sibling repo paths; inspect only in-scope files. Read execution_state.json and candidate_dispositions.json if present; verify predecessor gate artifacts and source/schema/config hashes. Create the NEW harness and ledgers specified in section 1.6; no predecessor artifact is required.
2. Read GraphConfig.load/_default/require_shared_graph; create_graph_store; CompoundingScorer.from_preset; DataOps _load_topology_config/create_app; AGE query_context/write_decision; SOC campaign/explorer query entry points; SDK projection/NL templates; all app conftest overrides. Re-read DG-1..DG-7 and paper §§3.1,3.4,4.2. Record current production entry points without importing apps into the planning process.
3. Validate the .codex_tmp/age_jm/manifest.json target against the server-owned disposable marker before any app startup/test that may write. Capture source fingerprints without git. Record changed/renamed call sites and preserve unrelated edits.

PHASE-SPECIFIC IMPLEMENTATION
A. Create the NEW verification assets in §1.6. Reuse the installed/pinned AGE setup after checking local deployment configuration; do not guess an image tag or download dependencies without required approval. Provision only a confirmed disposable database and graph soc_graph. Establish an immutable server-side test-run ownership marker. Separate app subprocesses and data directories from the user's stack.
B. Make GraphConfig the sole resolver, with explicit setting-key provenance and a redacted storage identity. Remove DataOps process-environment mutation and inject the same resolved config/store into topology, scorer and enrichment. Validate actual backend identity on the connection, not just a duck-typed backend='age' string.
C. Guard every production injection/factory path including explicit kwargs, wrappers, dual-write primaries, profile/test flag conflicts and missing capabilities. Move test construction behind explicit factories; no implicit SQLite or InMemory default. Introduce the reusable production dependency boundary now; side-store migrations are later phases and remain tracked failures until then.
D. Scope each Decision alias, entity anchor and intermediate relevant to G040; require domain in ProjectionRegistry.render and NL templates. Replace arbitrary explorer execution with a reviewed read-only query catalogue/domain binding; explicitly authorized cross-domain methods take source+target and authorization context. Read-only Cypher alone is not domain-safe.
E. Import all report Appendix A–F candidates into the disposition ledger, deduplicate by file/function/site/category, and assign owners: adapter/config/isolation→1/2, persistence/learning→3, copied/framework/SOC/catch behavior→4, local stores→5, contextual fixtures→6, interaction/evidence→7, health→8, tools/tests/references→9. Deleted files require caller/route evidence, not automatic clearance. Baseline known remaining issues; fail any newly introduced bypass.
F. Add production-profile tests outside legacy conftest scope. Make a minimal required AGE CI job run Phase-1 assertions and fail if AGE is missing. It may track not-yet-implemented later contracts as explicit work, but must not claim G061/G062 complete.

EXACT GAP WORK ITEMS

G042: Factory/profile guards are not a universal capability boundary
Targets: copilot-sdk/copilot_sdk/graph/factory.py:153,160,183,209; copilot-sdk/copilot_sdk/scoring/scorer.py:282,306,311; copilot-sdk/copilot_sdk/config/graph_config.py:26,50.
Functions: factory.py:create_graph_store, scorer.py:from_preset, graph_config.py:require_shared_graph.
Required change: Require a validated production GraphConfig and an authoritative-backend capability descriptor for every factory/injection; isolate test factories. Production must reject SQLite-primary dual-write even through wrappers.
Acceptance ownership: add test_g042_* cases to copilot-sdk/integration/age_jm/test_phase_01_contracts.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G043: One graph name does not enforce one graph destination
Targets: copilot-sdk/apps/dataops/backend/app/graph_queries.py:48,62,68,100; copilot-sdk/apps/dataops/backend/app/main.py:679; copilot-sdk/copilot_sdk/config/graph_config.py:112,213.
Functions: graph_queries.py:_load_topology_config, graph_queries.py:DataOpsGraphClient, main.py:create_app, graph_config.py:load, graph_config.py:_default.
Required change: Inject the resolved shared GraphConfig/store into topology services; eliminate process-environment mutation; compare redacted database identity + graph OID/name across all five at readiness.
Acceptance ownership: add test_g043_* cases to copilot-sdk/integration/age_jm/test_phase_01_contracts.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G040: Domain isolation has residual query and entity-anchor holes
Targets: ci-platform/ci_platform/graph/age_graph_store.py:777,3776,3797; gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:490,509; gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:117,138,213; copilot-sdk/copilot_sdk/graph/projection.py:70,73; copilot-sdk/copilot_sdk/di/nl_query.py:132.
Functions: age_graph_store.py:write_decision, age_graph_store.py:query_context, campaigns.py:module initialization, campaigns.py:get_campaign_context_for_decision, graph_explorer.py:run_safe_query, graph_explorer.py:get_node_neighbors, projection.py:ProjectionRegistry, projection.py:render, nl_query.py:_query_template.
Required change: Require scoped composite identities and domain-aware query APIs; bind every Decision alias, root and allowed intermediate. Put deliberate cross-domain access behind explicit source/target authorization, not a missing predicate.
Acceptance ownership: add test_g040_* cases to copilot-sdk/integration/age_jm/test_phase_01_contracts.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G060: Backend tests replace production graph behavior
Targets: copilot-sdk/tests/scoring/conftest.py:52; copilot-sdk/apps/trading/backend/conftest.py:19; copilot-sdk/apps/purchasing/backend/conftest.py:19; copilot-sdk/apps/dataops/backend/conftest.py:19; s2p-copilot/backend/tests/conftest.py:16,189,214.
Functions: conftest.py:store, conftest.py:_graph_environment, conftest.py:S2PTestGraphStore, conftest.py:module initialization, conftest.py:isolated_app_graph_state.
Required change: Keep fast unit suites, add a separate production-profile contract suite with unmocked stores and all five real app factories; verify injected-store rejection and outage behavior.
Acceptance ownership: add test_g060_* cases to copilot-sdk/integration/age_jm/test_phase_01_contracts.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

VERIFICATION
Create/extend copilot-sdk/integration/age_jm/test_phase_01_contracts.py; do not run a nonexistent test file and interpret non-collection as success.
From workspace root, on the disposable stack, run:
python -X utf8 -m pytest copilot-sdk/integration/age_jm/test_phase_01_contracts.py --age-jm-manifest .codex_tmp/age_jm/manifest.json --age-jm-require --strict-markers -q --junitxml=.codex_tmp/age_jm/phase-01.junit.xml
python -X utf8 copilot-sdk/scripts/verify_age_jm_phase.py --phase 01 --manifest .codex_tmp/age_jm/manifest.json --junit .codex_tmp/age_jm/phase-01.junit.xml --report .codex_tmp/age_jm/phase-01.json
Run the impacted existing unit/adapter/backend tests as separate processes per repository/app, using approved isolated configuration. Run prior phase tests whenever shared code changed; the verifier invalidates stale dependent artifacts. Use section 4's exact additional health/E2E commands when this phase owns them.

Required assertions:
1. All five canonical app configurations resolve AGE and identical server-issued storage identity + soc_graph; DataOps topology shares that object/config. No mutation of os.environ during topology resolution.
2. Production rejects missing DSN, SQLite/memory injection, SQLite-primary dual-write, incompatible capabilities, and a production/test-mode conflict; explicit offline test builders still work.
3. Same bare entity/Decision identifier in two domains cannot leak across normal reads; reviewed cross-domain query returns only its authorized pair. Missing domain is rejected.
4. Required real-AGE tests collect >0 cases, zero skips/xfails, and exercise actual app subprocess configuration without root conftest substitution.
5. Every original candidate has a stable ID and owning phase; none is dropped by a First-N limit. All 66 IDs have planned tests and one closure owner.

POST-CHECKS
- Re-scan all four production dependency roots for local stores, fixture/default branches, raw Decision queries, missing domain and broad/conditional exception suppression. Classify new hits; do not truncate scans or broaden allowlists.
- Verify zero new violations and no unresolved production candidates owned by this phase. Update each assigned gap with actual test node IDs, counts, source/config/schema hashes and evidence links; do not mark later-phase gaps closed.
- Review required health components: before Phase 8, report the harness's direct read-only component probes rather than claiming existing health aliases are fixed. After Phase 8, validate both /health and /api/health, readiness failure/recovery and storage identity.
- A phase is complete only if all its assertions pass. Otherwise record BLOCKED/INCOMPLETE with failing test/candidate and exact next action; do not proceed or weaken an assertion.

SESSION STATE
Append (do not rewrite) copilot-sdk/docs/session_state.md under AGE-JM-PHASE-01 with date, G042, G043, G040, G060, exact changes, commands and pass/fail/skip counts, target's redacted identity, evidence path, candidate dispositions, remaining blockers and next phase readiness. Update copilot-sdk/docs/age_jm_execution_state.json without losing previous entries. Never paste DSN secrets.
```

**Verification gate:**

- All five canonical app configurations resolve AGE and identical server-issued storage identity + soc_graph; DataOps topology shares that object/config. No mutation of os.environ during topology resolution.
- Production rejects missing DSN, SQLite/memory injection, SQLite-primary dual-write, incompatible capabilities, and a production/test-mode conflict; explicit offline test builders still work.
- Same bare entity/Decision identifier in two domains cannot leak across normal reads; reviewed cross-domain query returns only its authorized pair. Missing domain is rejected.
- Required real-AGE tests collect >0 cases, zero skips/xfails, and exercise actual app subprocess configuration without root conftest substitution.
- Every original candidate has a stable ID and owning phase; none is dropped by a First-N limit. All 66 IDs have planned tests and one closure owner.

Gate artifact: `.codex_tmp/age_jm/phase-01.json`; required tests: `copilot-sdk/integration/age_jm/test_phase_01_contracts.py`. Phase 2 must not start on a missing, failed or stale gate.

### Phase 2: Atomic storage and fail-closed scoring (estimated effort: 5d)

**Gaps closed:** G008, G007, G039, G001, G002, G009, G005

**Depends on:** Phase 1 gate and all earlier gates; stale predecessor evidence must be rerun.

**Repos touched:** ci-platform, copilot-sdk.

**Codex prompt specification:**

```text
/model astra
/reasoning high

Codex Prompt: AGE-JM-PHASE-02
Execute Phase 2 only: Atomic storage and fail-closed scoring.
Workspace: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects
Repositories allowed: ci-platform, copilot-sdk.
Closure IDs, in implementation order: G008, G007, G039, G001, G002, G009, G005.

RULES
- No git. Preserve unrelated work. Do not edit the JM paper or historical compliance report.
- Read copilot-sdk/docs/age_jm_execution_plan.md sections 1, 2, 4 and 7 and this phase, plus the complete assigned findings in copilot-sdk/docs/age_jm_compliance_report.md.
- Follow applicable AGENTS.md. Use current symbol definitions, not stale line numbers. Do not spawn agents unless separately authorized.
- Change only this phase's listed implementation targets, their typed adapter/protocol/call-site dependencies, tests/harness/CI required by this phase, and execution/candidate/session evidence. Explain any necessary scope expansion before changing unrelated components.
- Use a verified disposable AGE database with graph soc_graph, isolated app processes/data roots, production profile, and no demo/preseed conservation bypass. Never reset or fault the user's active database or invoke real broker/payment/SAP/order actions.
- Missing test infrastructure is BLOCKED, never a skipped PASS. No production deployment/migration without explicit target approval. Do not remove or overwrite original legacy stores.
- Each accepted operation must be durable and domain-scoped; graph errors cannot become fixture/local/empty-data success. No scoring-kernel or unapproved threshold changes.

PRE-CHECKS
1. Confirm workspace and sibling repo paths; inspect only in-scope files. Read execution_state.json and candidate_dispositions.json if present; verify predecessor gate artifacts and source/schema/config hashes. Do not proceed unless Phase 1 and all earlier required gates passed.
2. Read AGEClient.run_transaction, AGEGraphStoreTransaction/run_transaction/_run_query, write_decision/write_governed_decision, _save_platform_state, link_decision_to_entity/get_decision_links; scorer.score and persistence outbox; two_phase_strategy count/phase helpers; legacy transfer execute. Reproduce failure cases only in the test-owned database.
3. Validate the .codex_tmp/age_jm/manifest.json target against the server-owned disposable marker before any app startup/test that may write. Capture source fingerprints without git. Record changed/renamed call sites and preserve unrelated edits.

PHASE-SPECIFIC IMPLEMENTATION
A. Extend the existing transaction facade to cover score receipts, domain/factor/entity edges and state replacement. Keep every participating statement on the same connection/transaction; no inner _run_query that independently commits. Verify AGE-compatible syntax and concurrency behavior with the existing adapter tests.
B. Fix delete-then-create state replacement with a version check and single transaction; prevent racing creators/duplicate logical keys. Make missing entity/cardinality explicit. Replace surrogate link nodes with actual relationships for new writes; produce a read-only legacy-surrogate migration inventory for Phase 9, not an uncontrolled backfill now.
C. Make score() return success only after durable commit; map graph failure to 503 at the HTTP boundary. Add idempotency at operation/Decision identity so lost acknowledgments and retries never create duplicates. An indeterminate commit is a distinct error/status lookup, not synthetic success.
D. Remove automatic production SQLite outbox creation/drain. Record intents/receipts in AGE when available; otherwise reject. Quarantine legacy queue items lacking destination identity for later operator migration. No automatic replay into whichever graph happens to be configured today.
E. Make get_sequence_count/get_cross_category_count/two-phase status and AGEGraphStore._run_query fail rather than return zero/[] on graph faults, including the PoolClosed branch with a later raise.
F. Remove _demo_patterns_for_mapping from production /api/transfer/execute. An absent persisted eligible pattern yields an explicit no-transfer/rejection. Disable mutation until the governed path is complete, rather than generate demo deltas. Offline simulation may remain outside production routing.
G. Add adapter-level transactional tests and API fault tests. Inject failure after every write boundary, before/after commit, and concurrent writers; inspect both a new connection and the app's response.

EXACT GAP WORK ITEMS

G008: Platform-state replacement is delete-then-create across commits
Targets: ci-platform/ci_platform/graph/age_graph_store.py:109,117,126.
Functions: age_graph_store.py:_save_platform_state.
Required change: Use a single transaction/connection and version-checked replacement; add crash and concurrent-writer tests for posterior, promotion, evolution, governance and compounding state.
Acceptance ownership: add test_g008_* cases to copilot-sdk/integration/age_jm/test_phase_02_durability.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G007: Decision write can succeed without required graph edges
Targets: ci-platform/ci_platform/graph/age_graph_store.py:748,777,786,790,792,810.
Functions: age_graph_store.py:write_decision.
Required change: Make required Decision, domain, entity and factor links one transaction with cardinality assertions. Treat deliberately missing context as explicit incomplete evidence, not an equivalent success.
Acceptance ownership: add test_g007_* cases to copilot-sdk/integration/age_jm/test_phase_02_durability.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G039: DecisionEntityLink fallback is not a graph relationship
Targets: ci-platform/ci_platform/graph/age_graph_store.py:3217,3248,3269,3285.
Functions: age_graph_store.py:link_decision_to_entity, age_graph_store.py:get_decision_links.
Required change: Require a real scoped entity and relationship or explicitly create a typed placeholder entity with provenance; migrate surrogate records and verify each with a traversal.
Acceptance ownership: add test_g039_* cases to copilot-sdk/integration/age_jm/test_phase_02_durability.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G001: Scoring acknowledges failed Decision persistence
Targets: copilot-sdk/copilot_sdk/scoring/scorer.py:437,440,453,460,465.
Functions: scorer.py:score.
Required change: Make persisted Decision + required receipt the success boundary; propagate GraphUnavailable/PersistenceError to a 503. Do not expose an unpersisted ID as an accepted decision.
Acceptance ownership: add test_g001_* cases to copilot-sdk/integration/age_jm/test_phase_02_durability.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G002: SQLite failure outbox can itself disappear; replay identity is incomplete
Targets: copilot-sdk/copilot_sdk/scoring/scorer.py:178,185,1246,1253,1257; copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:46,51,57,65,116.
Functions: scorer.py:__init__, scorer.py:_record_persistence_failure, persistence_outbox.py:__init__.
Required change: Do not substitute it for authoritative success. Make pending/error state explicit; bind any approved repair queue to domain + graph/database identity + schema, expose abandoned entries, and require deliberate replay into the same destination.
Acceptance ownership: add test_g002_* cases to copilot-sdk/integration/age_jm/test_phase_02_durability.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G009: Low-level graph/count errors become zero or phase A
Targets: ci-platform/ci_platform/graph/age_client.py:660,679; ci-platform/ci_platform/strategy/two_phase_strategy.py:31,47.
Functions: age_client.py:get_sequence_count, age_client.py:get_cross_category_count, two_phase_strategy.py:get_phase, two_phase_strategy.py:get_status.
Required change: Raise typed unavailable errors; represent counts as unknown on failed reads. Do not advance readiness or learning from substituted zero.
Acceptance ownership: add test_g009_* cases to copilot-sdk/integration/age_jm/test_phase_02_durability.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G005: Legacy transfer executes generated demo patterns
Targets: copilot-sdk/copilot_sdk/backend/transfer_router.py:109,136,163,594,613.
Functions: transfer_router.py:create_transfer_router, transfer_router.py:transfer_execute, transfer_router.py:_patterns_for_execute.
Required change: Require persisted AGE source patterns and evidence; no match means no transfer. Move generated patterns into a separate explicit demo/test endpoint and prohibit production mutation from that provenance.
Acceptance ownership: add test_g005_* cases to copilot-sdk/integration/age_jm/test_phase_02_durability.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

VERIFICATION
Create/extend copilot-sdk/integration/age_jm/test_phase_02_durability.py; do not run a nonexistent test file and interpret non-collection as success.
From workspace root, on the disposable stack, run:
python -X utf8 -m pytest copilot-sdk/integration/age_jm/test_phase_02_durability.py --age-jm-manifest .codex_tmp/age_jm/manifest.json --age-jm-require --strict-markers -q --junitxml=.codex_tmp/age_jm/phase-02.junit.xml
python -X utf8 copilot-sdk/scripts/verify_age_jm_phase.py --phase 02 --manifest .codex_tmp/age_jm/manifest.json --junit .codex_tmp/age_jm/phase-02.junit.xml --report .codex_tmp/age_jm/phase-02.json
Run the impacted existing unit/adapter/backend tests as separate processes per repository/app, using approved isolated configuration. Run prior phase tests whenever shared code changed; the verifier invalidates stale dependent artifacts. Use section 4's exact additional health/E2E commands when this phase owns them.

Required assertions:
1. Fault any required score node/edge/receipt write: no ordinary 2xx success; no partial accepted Decision bundle survives rollback. If commit acknowledgment is lost, retry by operation key yields exactly one durable bundle.
2. Competing state updates produce one accepted next version or an explicit conflict/retry; failure after prior-state deletion does not destroy the previous committed state.
3. Every new Decision has domain and required actual graph relationships. Missing entity policies are explicit; no surrogate node is returned as equivalent proof.
4. AGE errors and PoolClosed propagate as unavailable, never zero/empty/default phase; runtime scoring creates no SQLite outbox/WAL.
5. Legacy /transfer/execute cannot mutate a production scorer from generated or fixture patterns, even when source conservation is GREEN.

POST-CHECKS
- Re-scan all four production dependency roots for local stores, fixture/default branches, raw Decision queries, missing domain and broad/conditional exception suppression. Classify new hits; do not truncate scans or broaden allowlists.
- Verify zero new violations and no unresolved production candidates owned by this phase. Update each assigned gap with actual test node IDs, counts, source/config/schema hashes and evidence links; do not mark later-phase gaps closed.
- Review required health components: before Phase 8, report the harness's direct read-only component probes rather than claiming existing health aliases are fixed. After Phase 8, validate both /health and /api/health, readiness failure/recovery and storage identity.
- A phase is complete only if all its assertions pass. Otherwise record BLOCKED/INCOMPLETE with failing test/candidate and exact next action; do not proceed or weaken an assertion.

SESSION STATE
Append (do not rewrite) copilot-sdk/docs/session_state.md under AGE-JM-PHASE-02 with date, G008, G007, G039, G001, G002, G009, G005, exact changes, commands and pass/fail/skip counts, target's redacted identity, evidence path, candidate dispositions, remaining blockers and next phase readiness. Update copilot-sdk/docs/age_jm_execution_state.json without losing previous entries. Never paste DSN secrets.
```

**Verification gate:**

- Fault any required score node/edge/receipt write: no ordinary 2xx success; no partial accepted Decision bundle survives rollback. If commit acknowledgment is lost, retry by operation key yields exactly one durable bundle.
- Competing state updates produce one accepted next version or an explicit conflict/retry; failure after prior-state deletion does not destroy the previous committed state.
- Every new Decision has domain and required actual graph relationships. Missing entity policies are explicit; no surrogate node is returned as equivalent proof.
- AGE errors and PoolClosed propagate as unavailable, never zero/empty/default phase; runtime scoring creates no SQLite outbox/WAL.
- Legacy /transfer/execute cannot mutate a production scorer from generated or fixture patterns, even when source conservation is GREEN.

Gate artifact: `.codex_tmp/age_jm/phase-02.json`; required tests: `copilot-sdk/integration/age_jm/test_phase_02_durability.py`. Phase 3 must not start on a missing, failed or stale gate.

### Phase 3: Graph-native judgment state and conservation-bounded learning (estimated effort: 6d)

**Gaps closed:** G038, G003, G004, G024, G025, G006

**Depends on:** Phase 2 gate and all earlier gates; stale predecessor evidence must be rerun.

**Repos touched:** ci-platform, copilot-sdk, s2p-copilot, gen-ai-roi-demo-v4-v50.

**Codex prompt specification:**

```text
/model astra
/reasoning high

Codex Prompt: AGE-JM-PHASE-03
Execute Phase 3 only: Graph-native judgment state and conservation-bounded learning.
Workspace: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects
Repositories allowed: ci-platform, copilot-sdk, s2p-copilot, gen-ai-roi-demo-v4-v50.
Closure IDs, in implementation order: G038, G003, G004, G024, G025, G006.

RULES
- No git. Preserve unrelated work. Do not edit the JM paper or historical compliance report.
- Read copilot-sdk/docs/age_jm_execution_plan.md sections 1, 2, 4 and 7 and this phase, plus the complete assigned findings in copilot-sdk/docs/age_jm_compliance_report.md.
- Follow applicable AGENTS.md. Use current symbol definitions, not stale line numbers. Do not spawn agents unless separately authorized.
- Change only this phase's listed implementation targets, their typed adapter/protocol/call-site dependencies, tests/harness/CI required by this phase, and execution/candidate/session evidence. Explain any necessary scope expansion before changing unrelated components.
- Use a verified disposable AGE database with graph soc_graph, isolated app processes/data roots, production profile, and no demo/preseed conservation bypass. Never reset or fault the user's active database or invoke real broker/payment/SAP/order actions.
- Missing test infrastructure is BLOCKED, never a skipped PASS. No production deployment/migration without explicit target approval. Do not remove or overwrite original legacy stores.
- Each accepted operation must be durable and domain-scoped; graph errors cannot become fixture/local/empty-data success. No scoring-kernel or unapproved threshold changes.

PRE-CHECKS
1. Confirm workspace and sibling repo paths; inspect only in-scope files. Read execution_state.json and candidate_dispositions.json if present; verify predecessor gate artifacts and source/schema/config hashes. Do not proceed unless Phase 2 and all earlier required gates passed.
2. Read scorer learn/restore/warm_start paths, L5 persistence helpers, KUtilityStore/update_weights, investigation route, state/protocol methods, conservation utilities and paper §§3.1–4.3. Inventory domain-specific policies and identify which artifacts are required versus telemetry. Do not enable a new scoring kernel.
3. Validate the .codex_tmp/age_jm/manifest.json target against the server-owned disposable marker before any app startup/test that may write. Capture source fingerprints without git. Record changed/renamed call sites and preserve unrelated edits.

PHASE-SPECIFIC IMPLEMENTATION
A. Implement typed versioned graph state and the relationship spine for G038 before connecting consumers: centroid/fingerprint/conservation snapshots, procedure/evaluation/authority evidence, K utilities and acquisition traces. Preserve array payloads as snapshots but expose traversal links. Extend GraphStore protocols/adapters without a second persistence interface.
B. Implement the versioned outcome-and-learning command using Phase-2 transactions: record verified outcome + operation receipt + learning disposition; only on an allowed disposition commit centroid/noise/K/conservation/evolution-required artifacts and next version. Publish a copy-on-write learner snapshot after commit. On denied learning, retain the verification and denial without changing M; expose evidence/learning-version lag explicitly.
C. Compute V/q/coverage from one canonical eligible population and committed snapshot. Test the paper's reference policy and explicitly version approved domain calibrations. Distinguish alpha coverage from same-named learning-rate fields. Exclude pending, Observations, archived, holdout-only and synthetic/demo records from live conservation and measured claims. Imported fixtures with manually set confirmed status do not become real human verification.
D. Make startup restore fail readiness if graph reads or required artifact completeness fail; bootstrap only after a successful empty read. Bootstrap priors are graph-recorded priors with V=0, not learned evidence or automatic GREEN. Restrict PRESEED/COLD_START/BOOTSTRAP passed branches so they cannot authorize ordinary production autonomy.
E. Replace all five _VLDKDecisionConnection/_create_vld_k_store injections with domain-scoped graph utility operations. Persist every investigation trace and consumed evidence identity. Wire update_weights into actual verified outcome processing once, with idempotency by outcome/trace. Keep fixture providers barred from production learning; graph-native evidence-provider completion is Phase 7.
F. Make warm_start compute a candidate state without mutating the live scorer, validate persisted source/target conservation, and commit transfer application/checkpoint/receipt under expected versions before publishing. A failure leaves the old learner intact; retries are idempotent. Full discovery/traversal UX remains Phase 7.
G. Reuse existing SOC outcome/checkpoint transaction tests, extend them to all required artifacts and two processes. Implement supervised recovery as a separate audited policy, not an unconditional GREEN reset.

EXACT GAP WORK ITEMS

G038: State in AGE is often JSON co-location, not traversable memory
Targets: ci-platform/ci_platform/graph/age_graph_store.py:109,115,170,234.
Functions: age_graph_store.py:_save_platform_state, age_graph_store.py:save_evolution, age_graph_store.py:delete_governance.
Required change: Model stable state/version, rule, evidence and outcome nodes with explicit relationships; retain payloads as snapshots only. Provide single-query interaction tests for the four memory types.
Acceptance ownership: add test_g038_* cases to copilot-sdk/integration/age_jm/test_phase_03_learning.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G003: Shared learning succeeds while artifacts fail
Targets: copilot-sdk/copilot_sdk/scoring/scorer.py:1332,1386,1424,1515,1525,1563,1650,1725,2456,2525,2603,2624; copilot-sdk/copilot_sdk/backend/scoring_router.py:600,605,629,716,740,761; copilot-sdk/copilot_sdk/scoring/dk_persistence.py:270.
Functions: scorer.py:_persist_conservation_snapshot, scorer.py:_persist_learning_artifacts, scorer.py:capture_existing_state, scorer.py:_persist_evidence_receipt, scorer.py:_persist_fingerprint, scorer.py:_save_centroids_checkpoint, scorer.py:_maybe_archive, scorer.py:_run_evolution, scorer.py:_evolution_conservation_state, scoring_router.py:_persist_conservation_state_l5_locked, scoring_router.py:_persist_centroid_l5, scoring_router.py:_read_centroid_for_l5, dk_persistence.py:persist_dk_after_reestimate.
Required change: Define one versioned learn transaction/checkpoint, commit artifacts and outcome together, publish memory only after commit, and return a failed/pending result on any required artifact error.
Acceptance ownership: add test_g003_* cases to copilot-sdk/integration/age_jm/test_phase_03_learning.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G004: Restore and phase failures look like bootstrap/no learning
Targets: copilot-sdk/copilot_sdk/scoring/startup_restore.py:155,169,249; copilot-sdk/copilot_sdk/scoring/scorer.py:363,1895,1906.
Functions: startup_restore.py:_restore_centroids, startup_restore.py:_restore_conservation, scorer.py:from_preset, scorer.py:get_phase, scorer.py:get_alpha.
Required change: Permit cold bootstrap only after a successful empty graph read. Fail readiness on restore failure and expose learning-component readiness separately.
Acceptance ownership: add test_g004_* cases to copilot-sdk/integration/age_jm/test_phase_03_learning.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G024: All five runtimes create a SQLite K-utility store
Targets: copilot-sdk/copilot_sdk/scoring/investigation.py:404,415,441; copilot-sdk/apps/trading/backend/app/main.py:140,595; copilot-sdk/apps/purchasing/backend/app/main.py:152,872; copilot-sdk/apps/dataops/backend/app/main.py:117,991; s2p-copilot/backend/app/main.py:46,499; gen-ai-roi-demo-v4-v50/backend/app/main.py:200,249.
Functions: investigation.py:KUtilityStore, investigation.py:__init__, investigation.py:update_weights, main.py:__init__, main.py:create_app, main.py:module initialization.
Required change: Add domain-scoped graph utility/learning operations linked to investigation, evidence, outcome and Decision; inject the common GraphStore into all five routers.
Acceptance ownership: add test_g024_* cases to copilot-sdk/integration/age_jm/test_phase_03_learning.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G025: Investigation traces and K feedback are not a closed production learning loop
Targets: copilot-sdk/copilot_sdk/backend/investigation_router.py:83,122; copilot-sdk/copilot_sdk/scoring/investigation.py:441.
Functions: investigation_router.py:investigate, investigation.py:update_weights.
Required change: Persist trace/evidence identities to AGE and call idempotent utility updates from verified outcome processing. Add restart/replay tests proving weights derive from those graph receipts.
Acceptance ownership: add test_g025_* cases to copilot-sdk/integration/age_jm/test_phase_03_learning.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G006: Warm-start mutates centroids before graph evidence is durable
Targets: copilot-sdk/copilot_sdk/scoring/scorer.py:1963,1983,2034,2060,2068.
Functions: scorer.py:warm_start.
Required change: Validate source/target evidence first; persist an atomic transfer + target checkpoint, then swap memory. Roll back on failure and never report applied when persistence failed.
Acceptance ownership: add test_g006_* cases to copilot-sdk/integration/age_jm/test_phase_03_learning.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

VERIFICATION
Create/extend copilot-sdk/integration/age_jm/test_phase_03_learning.py; do not run a nonexistent test file and interpret non-collection as success.
From workspace root, on the disposable stack, run:
python -X utf8 -m pytest copilot-sdk/integration/age_jm/test_phase_03_learning.py --age-jm-manifest .codex_tmp/age_jm/manifest.json --age-jm-require --strict-markers -q --junitxml=.codex_tmp/age_jm/phase-03.junit.xml
python -X utf8 copilot-sdk/scripts/verify_age_jm_phase.py --phase 03 --manifest .codex_tmp/age_jm/manifest.json --junit .codex_tmp/age_jm/phase-03.junit.xml --report .codex_tmp/age_jm/phase-03.json
Run the impacted existing unit/adapter/backend tests as separate processes per repository/app, using approved isolated configuration. Run prior phase tests whenever shared code changed; the verifier invalidates stale dependent artifacts. Use section 4's exact additional health/E2E commands when this phase owns them.

Required assertions:
1. One verified operation advances graph and in-memory versions together after commit; injected failure at each required artifact boundary leaves learner unchanged and no partial applied learning bundle.
2. Repeated/parallel outcome, trace and warm-start requests do not double-count V, update K twice, or apply a centroid delta twice; conflict retry is bounded and explicit.
3. Fresh processes reconstruct identical M, sigma/discriminability, K and conservation from AGE without SQLite/JSON side files.
4. V excludes pending/preview/archived/holdout/synthetic evidence; q-window=400 and coverage/category-gate reference tests pass, including zero evidence and threshold boundaries.
5. Non-GREEN/unavailable conservation prevents autonomous learning/promotion/transfer; a separately authorized supervised policy is auditable. No default DiagonalKernel enablement.
6. All five K stores are graph-injected and production verification endpoints call trace-linked utility updates; an API-returned trace alone is insufficient.

POST-CHECKS
- Re-scan all four production dependency roots for local stores, fixture/default branches, raw Decision queries, missing domain and broad/conditional exception suppression. Classify new hits; do not truncate scans or broaden allowlists.
- Verify zero new violations and no unresolved production candidates owned by this phase. Update each assigned gap with actual test node IDs, counts, source/config/schema hashes and evidence links; do not mark later-phase gaps closed.
- Review required health components: before Phase 8, report the harness's direct read-only component probes rather than claiming existing health aliases are fixed. After Phase 8, validate both /health and /api/health, readiness failure/recovery and storage identity.
- A phase is complete only if all its assertions pass. Otherwise record BLOCKED/INCOMPLETE with failing test/candidate and exact next action; do not proceed or weaken an assertion.

SESSION STATE
Append (do not rewrite) copilot-sdk/docs/session_state.md under AGE-JM-PHASE-03 with date, G038, G003, G004, G024, G025, G006, exact changes, commands and pass/fail/skip counts, target's redacted identity, evidence path, candidate dispositions, remaining blockers and next phase readiness. Update copilot-sdk/docs/age_jm_execution_state.json without losing previous entries. Never paste DSN secrets.
```

**Verification gate:**

- One verified operation advances graph and in-memory versions together after commit; injected failure at each required artifact boundary leaves learner unchanged and no partial applied learning bundle.
- Repeated/parallel outcome, trace and warm-start requests do not double-count V, update K twice, or apply a centroid delta twice; conflict retry is bounded and explicit.
- Fresh processes reconstruct identical M, sigma/discriminability, K and conservation from AGE without SQLite/JSON side files.
- V excludes pending/preview/archived/holdout/synthetic evidence; q-window=400 and coverage/category-gate reference tests pass, including zero evidence and threshold boundaries.
- Non-GREEN/unavailable conservation prevents autonomous learning/promotion/transfer; a separately authorized supervised policy is auditable. No default DiagonalKernel enablement.
- All five K stores are graph-injected and production verification endpoints call trace-linked utility updates; an API-returned trace alone is insufficient.

Gate artifact: `.codex_tmp/age_jm/phase-03.json`; required tests: `copilot-sdk/integration/age_jm/test_phase_03_learning.py`. Phase 4 must not start on a missing, failed or stale gate.

### Phase 4: Close every copilot's swallowed failure and protocol bypass (estimated effort: 8d)

**Gaps closed:** G041, G046, G010, G011, G012, G013, G014, G015, G016, G017, G018, G019, G020, G022

**Depends on:** Phase 3 gate and all earlier gates; stale predecessor evidence must be rerun.

**Repos touched:** copilot-sdk, ci-platform, s2p-copilot, gen-ai-roi-demo-v4-v50.

**Codex prompt specification:**

```text
/model astra
/reasoning high

Codex Prompt: AGE-JM-PHASE-04
Execute Phase 4 only: Close every copilot's swallowed failure and protocol bypass.
Workspace: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects
Repositories allowed: copilot-sdk, ci-platform, s2p-copilot, gen-ai-roi-demo-v4-v50.
Closure IDs, in implementation order: G041, G046, G010, G011, G012, G013, G014, G015, G016, G017, G018, G019, G020, G022.

RULES
- No git. Preserve unrelated work. Do not edit the JM paper or historical compliance report.
- Read copilot-sdk/docs/age_jm_execution_plan.md sections 1, 2, 4 and 7 and this phase, plus the complete assigned findings in copilot-sdk/docs/age_jm_compliance_report.md.
- Follow applicable AGENTS.md. Use current symbol definitions, not stale line numbers. Do not spawn agents unless separately authorized.
- Change only this phase's listed implementation targets, their typed adapter/protocol/call-site dependencies, tests/harness/CI required by this phase, and execution/candidate/session evidence. Explain any necessary scope expansion before changing unrelated components.
- Use a verified disposable AGE database with graph soc_graph, isolated app processes/data roots, production profile, and no demo/preseed conservation bypass. Never reset or fault the user's active database or invoke real broker/payment/SAP/order actions.
- Missing test infrastructure is BLOCKED, never a skipped PASS. No production deployment/migration without explicit target approval. Do not remove or overwrite original legacy stores.
- Each accepted operation must be durable and domain-scoped; graph errors cannot become fixture/local/empty-data success. No scoring-kernel or unapproved threshold changes.

PRE-CHECKS
1. Confirm workspace and sibling repo paths; inspect only in-scope files. Read execution_state.json and candidate_dispositions.json if present; verify predecessor gate artifacts and source/schema/config hashes. Do not proceed unless Phase 3 and all earlier required gates passed.
2. Read every G010–G022 site assigned here plus G041/G046 in current source and all matching Appendix-C handlers in those modules. Read SDK/SOC/S2P copies of framework helpers, S2P score/learn routes and SOC triage/metrics/campaign/evidence services. Identify all HTTP consumers of newly raised errors.
3. Validate the .codex_tmp/age_jm/manifest.json target against the server-owned disposable marker before any app startup/test that may write. Capture source fingerprints without git. Record changed/renamed call sites and preserve unrelated edits.

PHASE-SPECIFIC IMPLEMENTATION
A. Move all SOC production Decision access, including analyze_alert/execute_action/report_decision_outcome/explain_decision and campaign/explorer paths, behind typed GraphStore operations. Keep raw driver/Cypher implementation inside ci-platform. Remove the raw-DSN PosteriorStore compatibility path from production; retain only an explicit offline migration adapter if needed.
B. Adopt the shared Phase-3 outcome/learning transaction in S2P and SOC, including required invoice/entity links, conservation, centroids, K/DK measurements, receipts, promotion lineage and snapshots. Remove code paths that commit a primary write and quietly omit evidence required later by safety/learning.
C. Consolidate copied framework history/composite gate/similarity/provenance/shadow/checkpoint behavior into a shared fail-closed implementation, preserving public API compatibility through thin delegates only. No second fork with weaker semantics.
D. Fix every assigned catch-and-default site: DataOps _pipelines/_blast_radius/_recurrence and DI-ABSTENTION injection/detail exception; Purchasing evidence/trust/evolution; S2P day-zero/context/governance; Trading claim/trust/profile; SOC static metric fallbacks and empty history/topology/cohorts. Fix _consult_history to deny/unavailable, never proceed on error.
E. Translate typed graph errors once at route boundaries. Diagnostic endpoints may catch and explicitly report unavailable without data-bearing defaults; health must be non-ready. Safety gates may deny with UNKNOWN but must identify the failed read. A graph error is not no rows, zero verified history, a bootstrap state or an empty cohort.
F. Generate a route/call-site fault matrix from the candidate ledger. Include conditional handlers containing both return and raise, per-item continue loops, stale-cache retention and optional import disablement. Resolve every production catch candidate owned by this phase with a test or narrow documented non-memory classification.
G. Keep ingestion/fixture migrations scheduled later separate: removing a fallback may temporarily make a feature return unavailable. Do not claim the production feature restored until its graph-backed path in Phases 5–7 passes.

EXACT GAP WORK ITEMS

G041: SOC production Decision access still bypasses GraphStore
Targets: gen-ai-roi-demo-v4-v50/backend/app/db/graph_client.py:27,49; gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1119,1795,2104; gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1140.
Functions: graph_client.py:module initialization, triage.py:analyze_alert, triage.py:execute_action, triage.py:report_decision_outcome, soc.py:explain_decision.
Required change: Move Decision reads/writes into domain-scoped GraphStore operations; leave raw semantic graph internals inside the adapter only, with explicit protocol traversal methods.
Acceptance ownership: add test_g041_* cases to copilot-sdk/integration/age_jm/test_phase_04_routes.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G046: SOC legacy posterior API still permits raw DSN SQL
Targets: gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:53,68,120,156,184,208,221.
Functions: posterior_store.py:__init__, posterior_store.py:save, posterior_store.py:load, posterior_store.py:clear, posterior_store.py:_ping_storage, posterior_store.py:_ensure_table.
Required change: Remove or explicitly quarantine the raw-DSN constructor; migrate old relational posterior records and require typed graph config in all production callers.
Acceptance ownership: add test_g046_* cases to copilot-sdk/integration/age_jm/test_phase_04_routes.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G010: Copied framework helpers conceal graph failures
Targets: copilot-sdk/copilot_sdk/framework/decision_history.py:59; copilot-sdk/copilot_sdk/framework/composite_gate.py:120; copilot-sdk/copilot_sdk/framework/similar_cases_base.py:99; copilot-sdk/copilot_sdk/framework/provenance.py:326; copilot-sdk/copilot_sdk/framework/shadow_mode.py:106; copilot-sdk/copilot_sdk/framework/checkpoint.py:98.
Functions: decision_history.py:get_category_stats, composite_gate.py:evaluate, similar_cases_base.py:_fetch_verified_decisions, provenance.py:get_provenance_from_graph, shadow_mode.py:get_shadow_report, checkpoint.py:list_checkpoints.
Required change: Replace the copies with one fail-closed GraphStore-backed implementation. Distinguish no rows from unavailable; keep an explicit error-bearing diagnostic response only where no authoritative decision depends on it.
Acceptance ownership: add test_g010_* cases to copilot-sdk/integration/age_jm/test_phase_04_routes.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G011: DataOps investigation reintroduces fixtures above a fail-closed client
Targets: copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:352,365,378.
Functions: investigation_patterns.py:_pipelines, investigation_patterns.py:_blast_radius, investigation_patterns.py:_recurrence.
Required change: Propagate unavailable through evidence acquisition; allow fixtures only under explicit demo mode and preserve their provenance through score/receipt.
Acceptance ownership: add test_g011_* cases to copilot-sdk/integration/age_jm/test_phase_04_routes.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G012: DataOps live alerts inject a fixture; one detail route swallows outages
Targets: copilot-sdk/apps/dataops/backend/app/context_router.py:545,549,859,873,1423,1427.
Functions: context_router.py:_append_abstention_fixture, context_router.py:alerts, context_router.py:alert_groups, context_router.py:alert_detail.
Required change: Demo-gate the injected alert and the special exception branch. In production, let graph failure remain unavailable and seed real scenarios through AGE if required.
Acceptance ownership: add test_g012_* cases to copilot-sdk/integration/age_jm/test_phase_04_routes.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G013: Purchasing graph-read errors become empty evidence
Targets: copilot-sdk/apps/purchasing/backend/app/main.py:416; copilot-sdk/apps/purchasing/backend/app/context_router.py:82; copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:182,193; copilot-sdk/apps/purchasing/backend/app/routers/trust_router.py:163; copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:70.
Functions: main.py:_evolution_variants, context_router.py:_evolution_variants, evidence.py:_verified_decisions, evidence.py:_centroid_checkpoints, trust_router.py:_decisions_total, purchasing_control.py:refresh.
Required change: Propagate typed graph errors through these projections; safety gates may deny but must include unavailable and prevent success/readiness claims.
Acceptance ownership: add test_g013_* cases to copilot-sdk/integration/age_jm/test_phase_04_routes.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G014: S2P no-history/default projections hide graph outages
Targets: s2p-copilot/backend/app/routers/s2p_demo_beats.py:49; s2p-copilot/backend/app/routers/s2p_governance.py:38; s2p-copilot/backend/app/routers/s2p_evidence.py:206,220; s2p-copilot/backend/app/services/s2p_context_builder.py:271; s2p-copilot/backend/app/services/centroid_explorer.py:208.
Functions: s2p_demo_beats.py:_rows, s2p_governance.py:_safe_conservation_snapshot, s2p_evidence.py:_conservation_snapshot, s2p_context_builder.py:_supplier_enrichment, centroid_explorer.py:_p39_evidence.
Required change: Return explicit unavailable for failed reads. Day-zero is valid only after a successful zero-count query; keep safety denials visibly error-bearing.
Acceptance ownership: add test_g014_* cases to copilot-sdk/integration/age_jm/test_phase_04_routes.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G015: S2P learning and lineage writes are best-effort
Targets: s2p-copilot/backend/app/routers/s2p.py:831,842,866,899,921,970,1004,1063,1491,1832,2352,2469,2493,2512,2540.
Functions: s2p.py:_persist_l5_conservation_state, s2p.py:_persist_l5_centroid_state, s2p.py:_persist_l5_dk_state, s2p.py:_read_centroid_for_l5, s2p.py:_link_decision_to_invoice, s2p.py:_receipt_conservation_snapshot, s2p.py:_record_supplier_profile, s2p.py:score_procurement_event.
Required change: Move required learn/outcome/context linkage behind the shared transactional contract; distinguish optional telemetry failures from required judgment evidence.
Acceptance ownership: add test_g015_* cases to copilot-sdk/integration/age_jm/test_phase_04_routes.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G016: SOC metric fallback serves static data after graph failure
Targets: gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:592.
Functions: soc.py:query_soc_metrics.
Required change: Surface unavailable in production; route static metric material only through explicit demo fixtures with no learned/measured claim.
Acceptance ownership: add test_g016_* cases to copilot-sdk/integration/age_jm/test_phase_04_routes.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G017: SOC graph reads become empty history or fabricated no-data
Targets: gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2164,2200,2261,2286; gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3561; gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:1026,1036,1063,1081; gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1340,1377,1413,1756,1780.
Functions: soc.py:get_analyst_benchmarking, triage.py:get_graph_data, learning_health.py:compute_verification_health, campaigns.py:fetch_all_events, campaigns.py:fetch_recent_events, campaigns.py:fetch_single_alert_event, campaigns.py:get_campaigns, campaigns.py:get_campaign_detail.
Required change: Require typed no-data versus unavailable responses; preserve error context and fail readiness for required components. Do not render outage as healthy accumulating history.
Acceptance ownership: add test_g017_* cases to copilot-sdk/integration/age_jm/test_phase_04_routes.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G018: SOC judgment-side context and audit writes are optional in code
Targets: gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1242,1473,2151,2639,2882; gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:106,178; gen-ai-roi-demo-v4-v50/backend/app/services/snapshots.py:68; gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:725; gen-ai-roi-demo-v4-v50/backend/app/services/investigation_patterns.py:120,133.
Functions: triage.py:analyze_alert, triage.py:report_decision_outcome, reconvergence_logger.py:log_reconvergence_event, reconvergence_logger.py:log_decision_distance, snapshots.py:_write_profile_snapshot, learning_health.py:_persist_l5_conservation_state, investigation_patterns.py:_bounded_read, investigation_patterns.py:_fallback_context.
Required change: Declare the required evidence bundle and atomically persist it. Optional observability must be named optional and cannot supply later safety or learning evidence.
Acceptance ownership: add test_g018_* cases to copilot-sdk/integration/age_jm/test_phase_04_routes.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G019: SOC variant history guard fails open
Targets: gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:86.
Functions: variant_generator.py:_consult_history.
Required change: Return unavailable/deny and require a successful history read before variant generation or promotion.
Acceptance ownership: add test_g019_* cases to copilot-sdk/integration/age_jm/test_phase_04_routes.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G020: Trading projections suppress graph failure
Targets: copilot-sdk/apps/trading/backend/app/services/trader_profiles.py:85; copilot-sdk/apps/trading/backend/app/services/trust_analysis.py:173; copilot-sdk/apps/trading/backend/app/services/claim_gate.py:97; copilot-sdk/apps/trading/backend/app/evidence_providers.py:83.
Functions: trader_profiles.py:_verified_decisions, trust_analysis.py:_decisions_until_dk, claim_gate.py:refresh_from_store, evidence_providers.py:_domain_context.
Required change: Propagate unavailable; invalidate cached claim evidence on failed reads. Keep fail-closed RED/UNKNOWN but label it a read failure, not measured state.
Acceptance ownership: add test_g020_* cases to copilot-sdk/integration/age_jm/test_phase_04_routes.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G022: DataOps evolution/cohort failures look empty
Targets: copilot-sdk/apps/dataops/backend/app/ae_router.py:47; copilot-sdk/apps/dataops/backend/app/services/cohort_status.py:149.
Functions: ae_router.py:_events, cohort_status.py:_read_decisions.
Required change: Fail the projection or mark every omitted cohort unavailable with completeness=false; never publish complete learned telemetry from partial reads.
Acceptance ownership: add test_g022_* cases to copilot-sdk/integration/age_jm/test_phase_04_routes.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

VERIFICATION
Create/extend copilot-sdk/integration/age_jm/test_phase_04_routes.py; do not run a nonexistent test file and interpret non-collection as success.
From workspace root, on the disposable stack, run:
python -X utf8 -m pytest copilot-sdk/integration/age_jm/test_phase_04_routes.py --age-jm-manifest .codex_tmp/age_jm/manifest.json --age-jm-require --strict-markers -q --junitxml=.codex_tmp/age_jm/phase-04.junit.xml
python -X utf8 copilot-sdk/scripts/verify_age_jm_phase.py --phase 04 --manifest .codex_tmp/age_jm/manifest.json --junit .codex_tmp/age_jm/phase-04.junit.xml --report .codex_tmp/age_jm/phase-04.json
Run the impacted existing unit/adapter/backend tests as separate processes per repository/app, using approved isolated configuration. Run prior phase tests whenever shared code changed; the verifier invalidates stale dependent artifacts. Use section 4's exact additional health/E2E commands when this phase owns them.

Required assertions:
1. For each affected app route, successful empty graph read differs from injected graph failure in status/provenance; no fixture, []/0 neutral-data success or stale claim survives.
2. Both governed and legacy S2P/SOC score/outcome paths use the durable command; faults in required lineage/audit persistence cannot yield an applied learning response.
3. SOC production Decision queries/writes no longer call AGEClient/psycopg directly; reviewed adapter operations are domain-scoped and covered by collision tests.
4. DataOps live alert lists never append DI-ABSTENTION-001 from disk; graph failure in its detail route is unavailable.
5. SOC history guard cannot proceed after an exception. Copied framework call sites all delegate to the tested shared implementation.
6. All phase-owned Appendix-C production candidates are resolved with evidence; no broad file allowlist or catch-and-log-only replacement.

POST-CHECKS
- Re-scan all four production dependency roots for local stores, fixture/default branches, raw Decision queries, missing domain and broad/conditional exception suppression. Classify new hits; do not truncate scans or broaden allowlists.
- Verify zero new violations and no unresolved production candidates owned by this phase. Update each assigned gap with actual test node IDs, counts, source/config/schema hashes and evidence links; do not mark later-phase gaps closed.
- Review required health components: before Phase 8, report the harness's direct read-only component probes rather than claiming existing health aliases are fixed. After Phase 8, validate both /health and /api/health, readiness failure/recovery and storage identity.
- A phase is complete only if all its assertions pass. Otherwise record BLOCKED/INCOMPLETE with failing test/candidate and exact next action; do not proceed or weaken an assertion.

SESSION STATE
Append (do not rewrite) copilot-sdk/docs/session_state.md under AGE-JM-PHASE-04 with date, G041, G046, G010, G011, G012, G013, G014, G015, G016, G017, G018, G019, G020, G022, exact changes, commands and pass/fail/skip counts, target's redacted identity, evidence path, candidate dispositions, remaining blockers and next phase readiness. Update copilot-sdk/docs/age_jm_execution_state.json without losing previous entries. Never paste DSN secrets.
```

**Verification gate:**

- For each affected app route, successful empty graph read differs from injected graph failure in status/provenance; no fixture, []/0 neutral-data success or stale claim survives.
- Both governed and legacy S2P/SOC score/outcome paths use the durable command; faults in required lineage/audit persistence cannot yield an applied learning response.
- SOC production Decision queries/writes no longer call AGEClient/psycopg directly; reviewed adapter operations are domain-scoped and covered by collision tests.
- DataOps live alert lists never append DI-ABSTENTION-001 from disk; graph failure in its detail route is unavailable.
- SOC history guard cannot proceed after an exception. Copied framework call sites all delegate to the tested shared implementation.
- All phase-owned Appendix-C production candidates are resolved with evidence; no broad file allowlist or catch-and-log-only replacement.

Gate artifact: `.codex_tmp/age_jm/phase-04.json`; required tests: `copilot-sdk/integration/age_jm/test_phase_04_routes.py`. Phase 5 must not start on a missing, failed or stale gate.

### Phase 5: Move episodic and procedural side stores into AGE (estimated effort: 7d)

**Gaps closed:** G026, G027, G028, G029, G030, G031, G035, G045

**Depends on:** Phase 4 gate and all earlier gates; stale predecessor evidence must be rerun.

**Repos touched:** copilot-sdk, ci-platform, s2p-copilot, gen-ai-roi-demo-v4-v50.

**Codex prompt specification:**

```text
/model astra
/reasoning high

Codex Prompt: AGE-JM-PHASE-05
Execute Phase 5 only: Move episodic and procedural side stores into AGE.
Workspace: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects
Repositories allowed: copilot-sdk, ci-platform, s2p-copilot, gen-ai-roi-demo-v4-v50.
Closure IDs, in implementation order: G026, G027, G028, G029, G030, G031, G035, G045.

RULES
- No git. Preserve unrelated work. Do not edit the JM paper or historical compliance report.
- Read copilot-sdk/docs/age_jm_execution_plan.md sections 1, 2, 4 and 7 and this phase, plus the complete assigned findings in copilot-sdk/docs/age_jm_compliance_report.md.
- Follow applicable AGENTS.md. Use current symbol definitions, not stale line numbers. Do not spawn agents unless separately authorized.
- Change only this phase's listed implementation targets, their typed adapter/protocol/call-site dependencies, tests/harness/CI required by this phase, and execution/candidate/session evidence. Explain any necessary scope expansion before changing unrelated components.
- Use a verified disposable AGE database with graph soc_graph, isolated app processes/data roots, production profile, and no demo/preseed conservation bypass. Never reset or fault the user's active database or invoke real broker/payment/SAP/order actions.
- Missing test infrastructure is BLOCKED, never a skipped PASS. No production deployment/migration without explicit target approval. Do not remove or overwrite original legacy stores.
- Each accepted operation must be durable and domain-scoped; graph errors cannot become fixture/local/empty-data success. No scoring-kernel or unapproved threshold changes.

PRE-CHECKS
1. Confirm workspace and sibling repo paths; inspect only in-scope files. Read execution_state.json and candidate_dispositions.json if present; verify predecessor gate artifacts and source/schema/config hashes. Do not proceed unless Phase 4 and all earlier required gates passed.
2. Read every constructor/default in signal_store, DataOpsGovernance, PurchasingControlService, Trading journal/import/promotion, supplier accumulator, promotion/pilot/evolver/proposal/authority/registry APIs. Inventory persistent local schemas and distinguish genuine verified data, demo artifacts and ambiguous history without changing originals.
3. Validate the .codex_tmp/age_jm/manifest.json target against the server-owned disposable marker before any app startup/test that may write. Capture source fingerprints without git. Record changed/renamed call sites and preserve unrelated edits.

PHASE-SPECIFIC IMPLEMENTATION
A. Add graph-backed Signal/Event publication, recipient/domain links and acknowledgement semantics; migrate retained test-copy signals and replace SQLiteSignalStore injections in the three apps. Retention/bounded delivery cannot silently delete the evidence needed by Decisions.
B. Move DataOps holdout/evaluation judgments and receipts into typed graph nodes marked evaluation-only; keep them excluded from production V. Require Purchasing graph proof/outcome/twin capabilities instead of hasattr-based local fallbacks.
C. Move Trading metadata/journal and imported trades into domain-qualified graph evidence/episodes; reject unknown or foreign-domain Decision IDs. Rebuild trust/pattern/proxy-conservation projections from graph episodes, not _trade_store_ref.
D. Consolidate both Trading promotion route families onto one graph authority record with evaluation evidence, version check and reversible promotion history.
E. Replace S2P's process-local supplier events/fixture blend with graph Supplier + verified Invoice/Outcome episodes and deterministic profile projection. Priors remain prior-labelled and never count as verified events.
F. Require explicit graph injection in SDK promotion/pilot/evolver and S2P proposal/SOC authority/transfer registry APIs. Move local implementations/defaults to explicit offline/test modules so production import dependency checks can exclude them structurally, not by hopeful runtime flags.
G. For each old store, implement an idempotent dry-run migrator/read-only inventory against a COPY: source hash, classification, target graph identity, domain-qualified ID mapping, migrated count, relationship/receipt validation, unresolved conflicts. Do not mutate/delete original stores or run live migration. Complete reusable import mechanics in Phase 9 and execute authorized cutover only in Phase 10.
H. Two-instance and restart tests must show no hidden authority in process memory or a shared filesystem. Cross-process graph versions, not a process-local RLock alone, protect mutation.

EXACT GAP WORK ITEMS

G026: Cross-application signals are shared through SQLite, not graph edges
Targets: copilot-sdk/copilot_sdk/backend/signal_store.py:21,25,48; copilot-sdk/copilot_sdk/backend/cross_signal_router.py:57,61; copilot-sdk/apps/trading/backend/app/main.py:584; copilot-sdk/apps/purchasing/backend/app/main.py:849; copilot-sdk/apps/dataops/backend/app/main.py:872.
Functions: signal_store.py:shared_signal_path, signal_store.py:SQLiteSignalStore, signal_store.py:_connection, cross_signal_router.py:create_cross_signal_router, main.py:create_app.
Required change: Model source-domain Signal/Event nodes with provenance and receiving-domain links; query/deliver via GraphStore with acknowledgement/version semantics. Migrate retained signals before disabling SQLite.
Acceptance ownership: add test_g026_* cases to copilot-sdk/integration/age_jm/test_phase_05_side_stores.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G027: DataOps holdout judgments remain in SQLite
Targets: copilot-sdk/apps/dataops/backend/app/dataops_governance.py:24,30,32,44,87,114,126; copilot-sdk/apps/dataops/backend/app/main.py:732.
Functions: dataops_governance.py:__init__, dataops_governance.py:register_holdout, dataops_governance.py:verify_holdout, dataops_governance.py:provenance, main.py:create_app.
Required change: Store holdout/evaluation judgments and receipts in AGE, linked to the evaluated variant and domain. Remove production capability fallback; retain test stores only with an explicit test profile.
Acceptance ownership: add test_g027_* cases to copilot-sdk/integration/age_jm/test_phase_05_side_stores.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G028: Purchasing control has ungated capability-based local-store fallbacks
Targets: copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:136,153,159,160,165.
Functions: purchasing_control.py:__init__, purchasing_control.py:PurchasingControlService.
Required change: Validate complete required capabilities at production startup and raise; make SQLite constructors explicit test/development dependencies, not hasattr fallback branches.
Acceptance ownership: add test_g028_* cases to copilot-sdk/integration/age_jm/test_phase_05_side_stores.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G029: Trading metadata and journal evidence persist to JSON
Targets: copilot-sdk/apps/trading/backend/app/context_router.py:525,531,541; copilot-sdk/apps/trading/backend/app/routers/journal.py:565,583.
Functions: context_router.py:save_trade_metadata, context_router.py:get_trade_metadata, journal.py:_read_json_unlocked, journal.py:_write_json_atomic_unlocked.
Required change: Move evidence/annotations into typed domain-scoped graph operations linked to Decision IDs; reject unknown or foreign-domain IDs and rebuild projections from graph evidence.
Acceptance ownership: add test_g029_* cases to copilot-sdk/integration/age_jm/test_phase_05_side_stores.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G030: Trading trust/pattern/conservation projections use process-local trades
Targets: copilot-sdk/apps/trading/backend/app/context_router.py:13,393,394,406,407,426,430; copilot-sdk/apps/trading/backend/app/routers/data_import.py:216; copilot-sdk/apps/trading/backend/app/state/trading_registry.py:101.
Functions: context_router.py:module initialization, context_router.py:trust_analysis, context_router.py:behavioral_patterns, context_router.py:conservation_breakdown, data_import.py:module initialization, trading_registry.py:trust_analysis.
Required change: Ingest imported trades as domain-scoped episodic nodes and join to Decisions/outcomes. Read trust/pattern/proxy views from that graph-backed projection, with proxy labelling retained.
Acceptance ownership: add test_g030_* cases to copilot-sdk/integration/age_jm/test_phase_05_side_stores.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G031: Trading promotion authority is split between JSON and memory stores
Targets: copilot-sdk/apps/trading/backend/app/services/promotion.py:42,57; copilot-sdk/apps/trading/backend/app/services/promotion_state.py:52,65,105; copilot-sdk/apps/trading/backend/app/routers/promotion_router.py:33; copilot-sdk/apps/trading/backend/app/main.py:658,665.
Functions: promotion.py:_load, promotion.py:_save, promotion_state.py:PromotionStateStore, promotion_state.py:_load, promotion_state.py:_save, promotion_router.py:module initialization, main.py:create_app.
Required change: Consolidate routes onto one GraphPromotionStore, with versioned promotion/rollback evidence and restart-safe authority. Remove or migrate both local stores.
Acceptance ownership: add test_g031_* cases to copilot-sdk/integration/age_jm/test_phase_05_side_stores.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G035: S2P supplier memory is process-local and blended with fixtures
Targets: s2p-copilot/backend/app/services/supplier_profile_accumulator.py:69,79,121,124,137,523.
Functions: supplier_profile_accumulator.py:__init__, supplier_profile_accumulator.py:_load_fixtures, supplier_profile_accumulator.py:get_profile, supplier_profile_accumulator.py:module initialization.
Required change: Ingest suppliers and verified invoice events into AGE, compute profile projections with evidence links and restart/replay consistency; fixture priors must remain separately labelled.
Acceptance ownership: add test_g035_* cases to copilot-sdk/integration/age_jm/test_phase_05_side_stores.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G045: Ungated default stores remain in reusable production APIs
Targets: copilot-sdk/copilot_sdk/promotion/core.py:114,222; copilot-sdk/copilot_sdk/pilot/transfer.py:50,262; copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:68; s2p-copilot/backend/app/services/proposal_service.py:45,302; gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:132,141,341; copilot-sdk/copilot_sdk/transfer/registry.py:89.
Functions: core.py:__init__, transfer.py:__init__, prompt_evolver.py:__init__, proposal_service.py:__init__, authority_ladder.py:__init__, authority_ladder.py:get_authority_manager, registry.py:register.
Required change: Require store injection in production constructors and fail if absent; move local defaults to named test/demo builders. Add construction tests covering every public SDK entry point.
Acceptance ownership: add test_g045_* cases to copilot-sdk/integration/age_jm/test_phase_05_side_stores.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

VERIFICATION
Create/extend copilot-sdk/integration/age_jm/test_phase_05_side_stores.py; do not run a nonexistent test file and interpret non-collection as success.
From workspace root, on the disposable stack, run:
python -X utf8 -m pytest copilot-sdk/integration/age_jm/test_phase_05_side_stores.py --age-jm-manifest .codex_tmp/age_jm/manifest.json --age-jm-require --strict-markers -q --junitxml=.codex_tmp/age_jm/phase-05.junit.xml
python -X utf8 copilot-sdk/scripts/verify_age_jm_phase.py --phase 05 --manifest .codex_tmp/age_jm/manifest.json --junit .codex_tmp/age_jm/phase-05.junit.xml --report .codex_tmp/age_jm/phase-05.json
Run the impacted existing unit/adapter/backend tests as separate processes per repository/app, using approved isolated configuration. Run prior phase tests whenever shared code changed; the verifier invalidates stale dependent artifacts. Use section 4's exact additional health/E2E commands when this phase owns them.

Required assertions:
1. Run core score/verify/holdout/signal/promotion/journal/supplier flows in two app instances: state agrees through AGE and survives removing all derived local caches.
2. No production constructor creates SQLite, a local authoritative JSON file, or a default InMemory store; a missing graph capability fails startup/operation explicitly.
3. Holdout/synthetic/prior populations stay outside live V and measured evidence even when they have outcome-like fields.
4. Migration dry-run on preserved test copies is repeatable and non-mutating; duplicate imports are idempotent, foreign-domain IDs are rejected, conflicts are not guessed.
5. Trading trust/pattern/safety proxy and S2P supplier projections see records created through graph APIs without warming a local import list.

POST-CHECKS
- Re-scan all four production dependency roots for local stores, fixture/default branches, raw Decision queries, missing domain and broad/conditional exception suppression. Classify new hits; do not truncate scans or broaden allowlists.
- Verify zero new violations and no unresolved production candidates owned by this phase. Update each assigned gap with actual test node IDs, counts, source/config/schema hashes and evidence links; do not mark later-phase gaps closed.
- Review required health components: before Phase 8, report the harness's direct read-only component probes rather than claiming existing health aliases are fixed. After Phase 8, validate both /health and /api/health, readiness failure/recovery and storage identity.
- A phase is complete only if all its assertions pass. Otherwise record BLOCKED/INCOMPLETE with failing test/candidate and exact next action; do not proceed or weaken an assertion.

SESSION STATE
Append (do not rewrite) copilot-sdk/docs/session_state.md under AGE-JM-PHASE-05 with date, G026, G027, G028, G029, G030, G031, G035, G045, exact changes, commands and pass/fail/skip counts, target's redacted identity, evidence path, candidate dispositions, remaining blockers and next phase readiness. Update copilot-sdk/docs/age_jm_execution_state.json without losing previous entries. Never paste DSN secrets.
```

**Verification gate:**

- Run core score/verify/holdout/signal/promotion/journal/supplier flows in two app instances: state agrees through AGE and survives removing all derived local caches.
- No production constructor creates SQLite, a local authoritative JSON file, or a default InMemory store; a missing graph capability fails startup/operation explicitly.
- Holdout/synthetic/prior populations stay outside live V and measured evidence even when they have outcome-like fields.
- Migration dry-run on preserved test copies is repeatable and non-mutating; duplicate imports are idempotent, foreign-domain IDs are rejected, conflicts are not guessed.
- Trading trust/pattern/safety proxy and S2P supplier projections see records created through graph APIs without warming a local import list.

Gate artifact: `.codex_tmp/age_jm/phase-05.json`; required tests: `copilot-sdk/integration/age_jm/test_phase_05_side_stores.py`. Phase 6 must not start on a missing, failed or stale gate.

### Phase 6: Replace fixture-backed operational and evidence surfaces (estimated effort: 5d)

**Gaps closed:** G023, G032, G033, G034, G036

**Depends on:** Phase 5 gate and all earlier gates; stale predecessor evidence must be rerun.

**Repos touched:** copilot-sdk, ci-platform, s2p-copilot.

**Codex prompt specification:**

```text
/model astra
/reasoning high

Codex Prompt: AGE-JM-PHASE-06
Execute Phase 6 only: Replace fixture-backed operational and evidence surfaces.
Workspace: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects
Repositories allowed: copilot-sdk, ci-platform, s2p-copilot.
Closure IDs, in implementation order: G023, G032, G033, G034, G036.

RULES
- No git. Preserve unrelated work. Do not edit the JM paper or historical compliance report.
- Read copilot-sdk/docs/age_jm_execution_plan.md sections 1, 2, 4 and 7 and this phase, plus the complete assigned findings in copilot-sdk/docs/age_jm_compliance_report.md.
- Follow applicable AGENTS.md. Use current symbol definitions, not stale line numbers. Do not spawn agents unless separately authorized.
- Change only this phase's listed implementation targets, their typed adapter/protocol/call-site dependencies, tests/harness/CI required by this phase, and execution/candidate/session evidence. Explain any necessary scope expansion before changing unrelated components.
- Use a verified disposable AGE database with graph soc_graph, isolated app processes/data roots, production profile, and no demo/preseed conservation bypass. Never reset or fault the user's active database or invoke real broker/payment/SAP/order actions.
- Missing test infrastructure is BLOCKED, never a skipped PASS. No production deployment/migration without explicit target approval. Do not remove or overwrite original legacy stores.
- Each accepted operation must be durable and domain-scoped; graph errors cannot become fixture/local/empty-data success. No scoring-kernel or unapproved threshold changes.

PRE-CHECKS
1. Confirm workspace and sibling repo paths; inspect only in-scope files. Read execution_state.json and candidate_dispositions.json if present; verify predecessor gate artifacts and source/schema/config hashes. Do not proceed unless Phase 5 and all earlier required gates passed.
2. Read Trading analytics/rejection summary consumers and preseed artifact code; Purchasing orders/par/waste/disruption/payment/audit services; DataOps process/schema/timeline/audit context; S2P PVG/preview/factor acquisition. Trace source provenance all the way to UI consumers and source-system connectors.
3. Validate the .codex_tmp/age_jm/manifest.json target against the server-owned disposable marker before any app startup/test that may write. Capture source fingerprints without git. Record changed/renamed call sites and preserve unrelated edits.

PHASE-SPECIFIC IMPLEMENTATION
A. Replace Trading production analytics/rejection counters with graph episode/evaluation queries. Remove the evolution_log.json overlay from authoritative summaries and cached tab state. Historical synthetic rejection artifacts stay synthetic; do not merely rename their source to learned.
B. Implement Purchasing order/payment/disruption/par/waste/audit projections on graph data. Audit exports validate actual receipts and hash chain. Move hard-coded demo services behind isolated demo routing; missing live evidence returns a no-data/unavailable state, not the sample audit pack.
C. Implement DataOps process transformations/schema changes/timelines/signals/audit trails as graph-derived views with consumed source observation versions. Remove unguarded file reads and invented 'complete' chains. Keep explicitly demo-only apply-fix/metadata simulations isolated and non-authoritative.
D. Replace required S2P factor/PVG context with ingested semantic evidence. Missing graph-required factors cause abstention/unavailable, not a neutral 0.5. Preview simulations remain isolated observations and cannot mutate canonical Decisions, V or the evolver.
E. Make SAP/Celonis/QBO/Snowflake/dbt/Airflow source adapters distinguish live, unavailable and offline demo. Production ingestion persists source identity, timestamp, schema and provenance in AGE before evidence is used. A transport cache may be an ingestion input with freshness/provenance, never a silent replacement for an AGE read.
F. Return typed availability/evidence tier throughout these views; preserve legitimate empty/cold-start UX and proxy labelling. Update backend contracts before final E2E expectations. Exhaust phase-owned Appendix-B/D fixture/file candidates, not only the obvious named services.

EXACT GAP WORK ITEMS

G023: Preseed rejection history is labelled learned without graph learning
Targets: copilot-sdk/copilot_sdk/demo/preseed.py:143,153,330; copilot-sdk/copilot_sdk/backend/evolution_router.py:90,299; copilot-sdk/apps/trading/backend/app/main.py:563.
Functions: preseed.py:preseed_trading, preseed.py:_persist_trading_rejections, evolution_router.py:variants, evolution_router.py:build_evolution_summary, main.py:create_app.
Required change: Tag synthetic seeded evidence as synthetic, keep it out of learned counters, and derive production rejection history from persisted AGE evaluations/receipts.
Acceptance ownership: add test_g023_* cases to copilot-sdk/integration/age_jm/test_phase_06_projections.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G032: Trading analytics cache remains an ungated local source
Targets: copilot-sdk/apps/trading/backend/app/context_router.py:58,66,381,384.
Functions: context_router.py:_load_json_optional, context_router.py:module initialization, context_router.py:analytics.
Required change: Use graph-derived analytics with cache provenance/version tied to graph identity; require demo mode for packaged analytics and never silently fall across configured roots.
Acceptance ownership: add test_g032_* cases to copilot-sdk/integration/age_jm/test_phase_06_projections.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G033: Purchasing operational and audit surfaces are fixture-backed
Targets: copilot-sdk/apps/purchasing/backend/app/main.py:650,690,715,724,725,726,729; copilot-sdk/apps/purchasing/backend/app/services/audit_export.py:16; copilot-sdk/apps/purchasing/backend/app/services/payment_timing.py:11; copilot-sdk/apps/purchasing/backend/app/services/disruption_recovery.py:12.
Functions: main.py:_load_order_rows, main.py:waste_analysis, main.py:predictive_par_week, main.py:create_app, audit_export.py:generate_pack, payment_timing.py:__init__, disruption_recovery.py:__init__.
Required change: Demo-gate these services; build production projections from graph episodes, outcomes and policies. Audit exports must verify actual receipts/hash chains rather than hard-code GREEN/verified.
Acceptance ownership: add test_g033_* cases to copilot-sdk/integration/age_jm/test_phase_06_projections.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G034: DataOps operational process/audit context remains local material
Targets: copilot-sdk/apps/dataops/backend/app/context_router.py:681,693,705,1042,1176,1259,1286,1346,1511,1556,1588.
Functions: context_router.py:_load_transformations, context_router.py:_load_schema_changes, context_router.py:_pipeline_count, context_router.py:pipeline_decisions, context_router.py:process_timeline, context_router.py:_cross_graph_daily_cost, context_router.py:cross_graph_insight, context_router.py:_apply_fix_estimated_savings, context_router.py:process_signals, context_router.py:module initialization, context_router.py:audit_trail.
Required change: Make each production projection graph-backed and linked to episode/Decision evidence; keep demo apply-fix/metadata routes separated and never count their chains as canonical audit receipts.
Acceptance ownership: add test_g034_* cases to copilot-sdk/integration/age_jm/test_phase_06_projections.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G036: S2P context and comparison surfaces still have fixture pathways
Targets: s2p-copilot/backend/app/routers/s2p_pvg.py:39,156; s2p-copilot/backend/app/routers/s2p_preview.py:42,55,284; s2p-copilot/backend/app/domains/s2p/factors.py:438.
Functions: s2p_pvg.py:_load_candidate_json, s2p_pvg.py:variants, s2p_preview.py:_load_fixture_json, s2p_preview.py:_load_celonis_cache, s2p_preview.py:_get_preview_simulation_scorer, factors.py:compute_all_factors.
Required change: Separate simulation APIs/provenance from authoritative endpoints; ingest production semantic context into AGE and reject unavailable required factors. Review all remaining S2P fixture candidates in Appendix B.
Acceptance ownership: add test_g036_* cases to copilot-sdk/integration/age_jm/test_phase_06_projections.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

VERIFICATION
Create/extend copilot-sdk/integration/age_jm/test_phase_06_projections.py; do not run a nonexistent test file and interpret non-collection as success.
From workspace root, on the disposable stack, run:
python -X utf8 -m pytest copilot-sdk/integration/age_jm/test_phase_06_projections.py --age-jm-manifest .codex_tmp/age_jm/manifest.json --age-jm-require --strict-markers -q --junitxml=.codex_tmp/age_jm/phase-06.junit.xml
python -X utf8 copilot-sdk/scripts/verify_age_jm_phase.py --phase 06 --manifest .codex_tmp/age_jm/manifest.json --junit .codex_tmp/age_jm/phase-06.junit.xml --report .codex_tmp/age_jm/phase-06.json
Run the impacted existing unit/adapter/backend tests as separate processes per repository/app, using approved isolated configuration. Run prior phase tests whenever shared code changed; the verifier invalidates stale dependent artifacts. Use section 4's exact additional health/E2E commands when this phase owns them.

Required assertions:
1. With local fixture directories unavailable, graph-populated production analytics/audit/PVG/process endpoints work and return graph evidence IDs; no graph data yields honest empty state, an outage yields unavailable.
2. Rejection summaries and tab-state counters agree on graph evaluation IDs/version; synthetic preseed entries never inflate learned/rejected metrics.
3. Purchasing audit export verifies real receipt chains; deliberately corrupt/missing evidence fails verification rather than returning hard-coded verified=True.
4. Preview GET/Observation workloads leave Decision count, V, centroid versions and evolver population unchanged.
5. Connector outage cannot silently produce mock live evidence; provenance/freshness are queryable via consumed graph observations.

POST-CHECKS
- Re-scan all four production dependency roots for local stores, fixture/default branches, raw Decision queries, missing domain and broad/conditional exception suppression. Classify new hits; do not truncate scans or broaden allowlists.
- Verify zero new violations and no unresolved production candidates owned by this phase. Update each assigned gap with actual test node IDs, counts, source/config/schema hashes and evidence links; do not mark later-phase gaps closed.
- Review required health components: before Phase 8, report the harness's direct read-only component probes rather than claiming existing health aliases are fixed. After Phase 8, validate both /health and /api/health, readiness failure/recovery and storage identity.
- A phase is complete only if all its assertions pass. Otherwise record BLOCKED/INCOMPLETE with failing test/candidate and exact next action; do not proceed or weaken an assertion.

SESSION STATE
Append (do not rewrite) copilot-sdk/docs/session_state.md under AGE-JM-PHASE-06 with date, G023, G032, G033, G034, G036, exact changes, commands and pass/fail/skip counts, target's redacted identity, evidence path, candidate dispositions, remaining blockers and next phase readiness. Update copilot-sdk/docs/age_jm_execution_state.json without losing previous entries. Never paste DSN secrets.
```

**Verification gate:**

- With local fixture directories unavailable, graph-populated production analytics/audit/PVG/process endpoints work and return graph evidence IDs; no graph data yields honest empty state, an outage yields unavailable.
- Rejection summaries and tab-state counters agree on graph evaluation IDs/version; synthetic preseed entries never inflate learned/rejected metrics.
- Purchasing audit export verifies real receipt chains; deliberately corrupt/missing evidence fails verification rather than returning hard-coded verified=True.
- Preview GET/Observation workloads leave Decision count, V, centroid versions and evolver population unchanged.
- Connector outage cannot silently produce mock live evidence; provenance/freshness are queryable via consumed graph observations.

Gate artifact: `.codex_tmp/age_jm/phase-06.json`; required tests: `copilot-sdk/integration/age_jm/test_phase_06_projections.py`. Phase 7 must not start on a missing, failed or stale gate.

### Phase 7: Complete native cross-type interactions and governed transfer (estimated effort: 6d)

**Gaps closed:** G044, G021, G037, G047, G048

**Depends on:** Phase 6 gate and all earlier gates; stale predecessor evidence must be rerun.

**Repos touched:** copilot-sdk, ci-platform, s2p-copilot, gen-ai-roi-demo-v4-v50.

**Codex prompt specification:**

```text
/model astra
/reasoning high

Codex Prompt: AGE-JM-PHASE-07
Execute Phase 7 only: Complete native cross-type interactions and governed transfer.
Workspace: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects
Repositories allowed: copilot-sdk, ci-platform, s2p-copilot, gen-ai-roi-demo-v4-v50.
Closure IDs, in implementation order: G044, G021, G037, G047, G048.

RULES
- No git. Preserve unrelated work. Do not edit the JM paper or historical compliance report.
- Read copilot-sdk/docs/age_jm_execution_plan.md sections 1, 2, 4 and 7 and this phase, plus the complete assigned findings in copilot-sdk/docs/age_jm_compliance_report.md.
- Follow applicable AGENTS.md. Use current symbol definitions, not stale line numbers. Do not spawn agents unless separately authorized.
- Change only this phase's listed implementation targets, their typed adapter/protocol/call-site dependencies, tests/harness/CI required by this phase, and execution/candidate/session evidence. Explain any necessary scope expansion before changing unrelated components.
- Use a verified disposable AGE database with graph soc_graph, isolated app processes/data roots, production profile, and no demo/preseed conservation bypass. Never reset or fault the user's active database or invoke real broker/payment/SAP/order actions.
- Missing test infrastructure is BLOCKED, never a skipped PASS. No production deployment/migration without explicit target approval. Do not remove or overwrite original legacy stores.
- Each accepted operation must be durable and domain-scoped; graph errors cannot become fixture/local/empty-data success. No scoring-kernel or unapproved threshold changes.

PRE-CHECKS
1. Confirm workspace and sibling repo paths; inspect only in-scope files. Read execution_state.json and candidate_dispositions.json if present; verify predecessor gate artifacts and source/schema/config hashes. Do not proceed unless Phase 6 and all earlier required gates passed.
2. Read transfer.py and both transfer router families, SharedPatternRegistry, discovery router, AGE transfer/fingerprint/traversal methods, all five investigation evidence providers and SOC platform summaries. Confirm Phase-3 linked judgment versions and Phase-5/6 semantic/episodic data are available.
3. Validate the .codex_tmp/age_jm/manifest.json target against the server-owned disposable marker before any app startup/test that may write. Capture source fingerprints without git. Record changed/renamed call sites and preserve unrelated edits.

PHASE-SPECIFIC IMPLEMENTATION
A. Replace file-fingerprint discovery and memory/JSON registry reads with a single graph query over source judgment/fingerprint and target context; JSON remains export-only. Category/factor mappings must be persisted, schema-compatible, validated and provenance-bearing, not synthesized merely to make the demonstration run.
B. Implement four named typed traversal operations: decision_movement(domain, decision_id), contextual_judgment(domain, entity_group, category), promotion_basis(domain, rule_id), and transfer_witness(source_domain, target_domain, pattern_id). These are NEW contract names unless existing equivalents are reused with an explicit mapping. Each returns linked evidence and uses one Cypher traversal, with no second-store read or app-side join.
C. Include the §6.4 reviewer/time quality-change and entity-specific factor-quality cases. Entity-context conditioning must return genuinely different evidence partitions, not one global fingerprint cosmetically filtered by entity.
D. Complete production transfer application: both source and target conservation/version/policy checks from a consistent graph snapshot, explicit reviewed source/target authorization, expected-version check at commit, no unconditional GREEN reset. Compute impact only for evidence linked to the pattern; failed contributing reads yield unknown/error, not a partial sum presented as complete. Restrict actual transfer eligibility (e.g. V>200) through the explicit policy; do not treat the paper's illustrative number as a universal constant.
E. Replace DataOps create_discovery_router(object()) with a real graph-backed engine and eliminate _demo_domain_decisions from production. Replace SOC cross-signal/domain/chain-credit/RL/warm-start panels with graph projections; unsupported measured claims stay unavailable.
F. Replace every production investigation evidence provider with graph-native typed observation acquisition, persist trace-step → consumed observation-version links, and complete verified feedback into K. Use Phase-3 trace/utility transaction rather than adding another history store.
G. Instrument the adapter to count actual Cypher traversals (not connection setup SQL). Assert one traversal per named interaction and zero file/SQLite/remote-join reads while executing it. Store returned path witnesses for inspection.
H. Add the requested Trading→S2P demo: seed compatible test judgment/fingerprint/centroid state in trading, query it through an authorized S2P transfer_witness, show matching source version and real path; then apply under the governed transaction and verify a target checkpoint. Denied mapping/conservation/permission cases must also pass.

EXACT GAP WORK ITEMS

G044: Cross-domain discovery still reads exported fingerprints
Targets: copilot-sdk/copilot_sdk/backend/transfer.py:24,41,51,62; copilot-sdk/copilot_sdk/backend/transfer_router.py:60,62; copilot-sdk/copilot_sdk/scoring/scorer.py:2093.
Functions: transfer.py:save_fingerprint, transfer.py:load_fingerprints_with_warnings, transfer_router.py:transfer_opportunities, scorer.py:export.
Required change: Use one explicit cross-domain graph projection linked to verified fingerprint evidence and source/target domains. Keep JSON only as export, never the production discovery source.
Acceptance ownership: add test_g044_* cases to copilot-sdk/integration/age_jm/test_phase_07_traversals.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G021: Transfer impact and reset tolerate incomplete graph state
Targets: copilot-sdk/copilot_sdk/backend/transfer_router.py:202,214,631,654,699.
Functions: transfer_router.py:_pattern_dollar_impact, transfer_router.py:_reset_conservation_state, transfer_router.py:_save_transfer_checkpoint.
Required change: Return unknown impact on any failed contributing read; make reset/event/checkpoint atomic with transfer and validate source-decision scope rather than summing unrelated decisions.
Acceptance ownership: add test_g021_* cases to copilot-sdk/integration/age_jm/test_phase_07_traversals.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G037: SOC cross-copilot platform panels are fixture projections
Targets: gen-ai-roi-demo-v4-v50/backend/app/routers/platform.py:46,77,111,144,177,210.
Functions: platform.py:_load_cross_signals, platform.py:_load_domain_table, platform.py:_load_warm_start_evidence, platform.py:_load_chain_credit_demo, platform.py:_load_rl_reward_demo, platform.py:_load_rl_exploration_demo.
Required change: Replace production panels with typed cross-domain AGE projections; keep static platform stories behind an explicit demo namespace.
Acceptance ownership: add test_g037_* cases to copilot-sdk/integration/age_jm/test_phase_07_traversals.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G047: No complete production single-traversal contract covers all four memories
Targets: copilot-sdk/copilot_sdk/graph/protocol.py:16,238,264,464; ci-platform/ci_platform/graph/age_graph_store.py:1432,2263,3776; copilot-sdk/apps/dataops/backend/app/main.py:941; copilot-sdk/copilot_sdk/backend/discovery_router.py:75,98.
Functions: protocol.py:GraphStore, protocol.py:GraphTraversalStore, protocol.py:ProtocolV2GraphStore, protocol.py:L5LearningStore, age_graph_store.py:_link_transfer_edges, age_graph_store.py:write_transfer_pattern, age_graph_store.py:query_context, main.py:create_app, discovery_router.py:_domain_decisions, discovery_router.py:_demo_domain_decisions.
Required change: Specify and implement episodic×judgment, semantic×judgment, procedural×judgment and cross-domain judgment×judgment queries. Require evidence-linked returned paths and no second-store lookup; replace object() discovery with a real engine.
Acceptance ownership: add test_g047_* cases to copilot-sdk/integration/age_jm/test_phase_07_traversals.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G048: Investigation evidence providers are fixture/local sources in all five apps
Targets: copilot-sdk/apps/trading/backend/app/main.py:595; copilot-sdk/apps/purchasing/backend/app/main.py:870,872; copilot-sdk/apps/dataops/backend/app/main.py:988,991; s2p-copilot/backend/app/main.py:496,499; gen-ai-roi-demo-v4-v50/backend/app/main.py:249; copilot-sdk/copilot_sdk/di/query_providers.py:178; copilot-sdk/copilot_sdk/di/query_providers.py:104,178.
Functions: main.py:create_app, main.py:module initialization, query_providers.py:_decision_invoice_ids, query_providers.py:_decisions.
Required change: Persist source observations with source system, time, version and provenance into the semantic/episodic graph; obtain investigation evidence through scoped graph traversal and link every acquired item to its trace.
Acceptance ownership: add test_g048_* cases to copilot-sdk/integration/age_jm/test_phase_07_traversals.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

VERIFICATION
Create/extend copilot-sdk/integration/age_jm/test_phase_07_traversals.py; do not run a nonexistent test file and interpret non-collection as success.
From workspace root, on the disposable stack, run:
python -X utf8 -m pytest copilot-sdk/integration/age_jm/test_phase_07_traversals.py --age-jm-manifest .codex_tmp/age_jm/manifest.json --age-jm-require --strict-markers -q --junitxml=.codex_tmp/age_jm/phase-07.junit.xml
python -X utf8 copilot-sdk/scripts/verify_age_jm_phase.py --phase 07 --manifest .codex_tmp/age_jm/manifest.json --junit .codex_tmp/age_jm/phase-07.junit.xml --report .codex_tmp/age_jm/phase-07.json
Run the impacted existing unit/adapter/backend tests as separate processes per repository/app, using approved isolated configuration. Run prior phase tests whenever shared code changed; the verifier invalidates stale dependent artifacts. Use section 4's exact additional health/E2E commands when this phase owns them.

Required assertions:
1. All four named memory interactions execute as a single AGE Cypher traversal and return actual linked nodes/edges; payload IDs or Python stitching alone fail.
2. From S2P, the authorized query sees the exact Trading centroid/fingerprint version through a transfer path in the same graph; an unrelated domain or unauthorized caller cannot see it.
3. Source/target conservation changes between read and commit cause conflict/rejection; retry is idempotent and no reset manufactures GREEN.
4. Removing fingerprint files/fixture providers and restarting does not change discovery, platform projections or investigation evidence.
5. Each verified investigation outcome updates graph K once and is traceable through Decision→trace→observation→outcome→utility version.
6. Financial impact is evidence-scoped, complete and provenance-bearing or explicitly unavailable; no partial-domain sum is called complete.

POST-CHECKS
- Re-scan all four production dependency roots for local stores, fixture/default branches, raw Decision queries, missing domain and broad/conditional exception suppression. Classify new hits; do not truncate scans or broaden allowlists.
- Verify zero new violations and no unresolved production candidates owned by this phase. Update each assigned gap with actual test node IDs, counts, source/config/schema hashes and evidence links; do not mark later-phase gaps closed.
- Review required health components: before Phase 8, report the harness's direct read-only component probes rather than claiming existing health aliases are fixed. After Phase 8, validate both /health and /api/health, readiness failure/recovery and storage identity.
- A phase is complete only if all its assertions pass. Otherwise record BLOCKED/INCOMPLETE with failing test/candidate and exact next action; do not proceed or weaken an assertion.

SESSION STATE
Append (do not rewrite) copilot-sdk/docs/session_state.md under AGE-JM-PHASE-07 with date, G044, G021, G037, G047, G048, exact changes, commands and pass/fail/skip counts, target's redacted identity, evidence path, candidate dispositions, remaining blockers and next phase readiness. Update copilot-sdk/docs/age_jm_execution_state.json without losing previous entries. Never paste DSN secrets.
```

**Verification gate:**

- All four named memory interactions execute as a single AGE Cypher traversal and return actual linked nodes/edges; payload IDs or Python stitching alone fail.
- From S2P, the authorized query sees the exact Trading centroid/fingerprint version through a transfer path in the same graph; an unrelated domain or unauthorized caller cannot see it.
- Source/target conservation changes between read and commit cause conflict/rejection; retry is idempotent and no reset manufactures GREEN.
- Removing fingerprint files/fixture providers and restarting does not change discovery, platform projections or investigation evidence.
- Each verified investigation outcome updates graph K once and is traceable through Decision→trace→observation→outcome→utility version.
- Financial impact is evidence-scoped, complete and provenance-bearing or explicitly unavailable; no partial-domain sum is called complete.

Gate artifact: `.codex_tmp/age_jm/phase-07.json`; required tests: `copilot-sdk/integration/age_jm/test_phase_07_traversals.py`. Phase 8 must not start on a missing, failed or stale gate.

### Phase 8: Unified readiness, truthful health, and launcher enforcement (estimated effort: 3d)

**Gaps closed:** G049, G050, G051, G052, G053, G054, G055

**Depends on:** Phase 7 gate and all earlier gates; stale predecessor evidence must be rerun.

**Repos touched:** copilot-sdk, ci-platform, s2p-copilot, gen-ai-roi-demo-v4-v50.

**Codex prompt specification:**

```text
/model astra
/reasoning high

Codex Prompt: AGE-JM-PHASE-08
Execute Phase 8 only: Unified readiness, truthful health, and launcher enforcement.
Workspace: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects
Repositories allowed: copilot-sdk, ci-platform, s2p-copilot, gen-ai-roi-demo-v4-v50.
Closure IDs, in implementation order: G049, G050, G051, G052, G053, G054, G055.

RULES
- No git. Preserve unrelated work. Do not edit the JM paper or historical compliance report.
- Read copilot-sdk/docs/age_jm_execution_plan.md sections 1, 2, 4 and 7 and this phase, plus the complete assigned findings in copilot-sdk/docs/age_jm_compliance_report.md.
- Follow applicable AGENTS.md. Use current symbol definitions, not stale line numbers. Do not spawn agents unless separately authorized.
- Change only this phase's listed implementation targets, their typed adapter/protocol/call-site dependencies, tests/harness/CI required by this phase, and execution/candidate/session evidence. Explain any necessary scope expansion before changing unrelated components.
- Use a verified disposable AGE database with graph soc_graph, isolated app processes/data roots, production profile, and no demo/preseed conservation bypass. Never reset or fault the user's active database or invoke real broker/payment/SAP/order actions.
- Missing test infrastructure is BLOCKED, never a skipped PASS. No production deployment/migration without explicit target approval. Do not remove or overwrite original legacy stores.
- Each accepted operation must be durable and domain-scoped; graph errors cannot become fixture/local/empty-data success. No scoring-kernel or unapproved threshold changes.

PRE-CHECKS
1. Confirm workspace and sibling repo paths; inspect only in-scope files. Read execution_state.json and candidate_dispositions.json if present; verify predecessor gate artifacts and source/schema/config hashes. Do not proceed unless Phase 7 and all earlier required gates passed.
2. Read all five main.py health routes/aliases, graph_status builders, shared health/scoring routers, DataOps graph_source/_run_graph state, launcher wait_for_health/_wait_all_healthy/cmd_status/cmd_start, and preseed check_health. Identify GET middleware that currently seeds/replays.
3. Validate the .codex_tmp/age_jm/manifest.json target against the server-owned disposable marker before any app startup/test that may write. Capture source fingerprints without git. Record changed/renamed call sites and preserve unrelated edits.

PHASE-SPECIFIC IMPLEMENTATION
A. Implement one typed readiness builder in the SDK, injected with each app's actual production GraphStore and resolved GraphConfig. Use fresh bounded read-only probes for Decision, topology, restored learning, evidence/receipt completeness and schema/capabilities. Report the same resolved database identity and soc_graph across all apps.
B. Expose /health and /api/health consistently: graph_backend='age', graph_connected boolean, graph_name='soc_graph', graph_status.connected/name/storage_identity/dsn_source, required component statuses, latest durable version and pending/failed/abandoned repair/migration state. Never return raw DSN credentials.
C. Return 503 for non-ready graph/required memory, 200 for ready; add /livez for process liveness if needed. Cold but successfully read empty graph is distinct from disconnected; eligibility/autonomy false does not necessarily mean service unhealthy. Do not make measurement claims or cutover flags equivalent to connectivity.
D. Remove all seeding/replay/repair from GET health and its middleware. Startup orchestration and authorized preseed are explicit commands. Refresh recovery state after successful probes rather than retaining stale disconnected flags.
E. DataOps reports actual decision_store and topology separately but from shared identity, with unavailable (not fixture) when graph queries cannot run. SOC probes actual required graph state rather than only posterior health.
F. Launcher badges distinguish requested/selected and verified backend; waits require validated readiness, all five agreeing on storage identity. Preseed health gating uses this exact contract. Required components and completeness are data-driven, not class-name inference.

EXACT GAP WORK ITEMS

G049: Trading health infers backend but does not prove connection/config provenance
Targets: copilot-sdk/apps/trading/backend/app/main.py:714,719,726; copilot-sdk/apps/trading/backend/app/graph_status.py:381,429,452.
Functions: main.py:create_app, main.py:health, graph_status.py:build_trading_graph_status.
Required change: Return one schema with selected/actual backend, fresh read result, graph identity, config sources, restore/artifact readiness and error; separate liveness from readiness.
Acceptance ownership: add test_g049_* cases to copilot-sdk/integration/age_jm/test_phase_08_health.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G050: Purchasing health aliases disagree
Targets: copilot-sdk/apps/purchasing/backend/app/main.py:624,631,632,960.
Functions: main.py:create_app, main.py:api_health.
Required change: Use one health builder for both aliases, probe the authoritative store, and include graph_name, connection state, config provenance and component failures.
Acceptance ownership: add test_g050_* cases to copilot-sdk/integration/age_jm/test_phase_08_health.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G051: DataOps health reports topology only and an ambiguous fixture label
Targets: copilot-sdk/apps/dataops/backend/app/main.py:1054,1061,1065,1066; copilot-sdk/apps/dataops/backend/app/graph_queries.py:100,131,140,568.
Functions: main.py:create_app, main.py:health, graph_queries.py:DataOpsGraphClient, graph_queries.py:__init__, graph_queries.py:graph_source, graph_queries.py:_run_graph.
Required change: Report decision_store and topology separately using the same config; use unavailable rather than fixture when fixture delivery is forbidden. Refresh successful/failed probe state and return non-ready status on either failure.
Acceptance ownership: add test_g051_* cases to copilot-sdk/integration/age_jm/test_phase_08_health.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G052: S2P health provides no graph readiness
Targets: s2p-copilot/backend/app/main.py:590,593; s2p-copilot/backend/app/s2p_graph_status.py:408,475.
Functions: main.py:module initialization, main.py:health, s2p_graph_status.py:build_s2p_graph_status.
Required change: Expose and probe actual AGE store plus restored learning/proposal/enrichment state; include graph_name and DSN/config source without credentials.
Acceptance ownership: add test_g052_* cases to copilot-sdk/integration/age_jm/test_phase_08_health.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G053: SOC health is not the requested shared graph contract
Targets: gen-ai-roi-demo-v4-v50/backend/app/main.py:108,121,134.
Functions: main.py:health.
Required change: Expose the same contract as other copilots; probe authoritative Decision and required memory traversal components, not just posterior connectivity.
Acceptance ownership: add test_g053_* cases to copilot-sdk/integration/age_jm/test_phase_08_health.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G054: Launcher AGE badges/readiness can be optimistic
Targets: copilot-sdk/demo.py:597,658,826,1312; copilot-sdk/scripts/preseed_all_copilots.py:229.
Functions: demo.py:wait_for_health, demo.py:_wait_all_healthy, demo.py:cmd_status, demo.py:cmd_start, preseed_all_copilots.py:check_health.
Required change: Render selected versus verified backend separately. Require consistent ready graph identity across all five before claiming AGE-ready or allowing preseed.
Acceptance ownership: add test_g054_* cases to copilot-sdk/integration/age_jm/test_phase_08_health.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G055: No uniform visibility into incomplete learning and repair backlog
Targets: copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:116; copilot-sdk/copilot_sdk/scoring/scorer.py:1246; copilot-sdk/apps/trading/backend/app/graph_status.py:421.
Functions: persistence_outbox.py:__init__, scorer.py:_record_persistence_failure, graph_status.py:build_trading_graph_status.
Required change: Add pending/failed/abandoned counts, latest durable learn version, receipt/edge completeness and freshness. Readiness must fail when required judgment state is incomplete.
Acceptance ownership: add test_g055_* cases to copilot-sdk/integration/age_jm/test_phase_08_health.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

VERIFICATION
Create/extend copilot-sdk/integration/age_jm/test_phase_08_health.py; do not run a nonexistent test file and interpret non-collection as success.
From workspace root, on the disposable stack, run:
python -X utf8 -m pytest copilot-sdk/integration/age_jm/test_phase_08_health.py --age-jm-manifest .codex_tmp/age_jm/manifest.json --age-jm-require --strict-markers -q --junitxml=.codex_tmp/age_jm/phase-08.junit.xml
python -X utf8 copilot-sdk/scripts/verify_age_jm_phase.py --phase 08 --manifest .codex_tmp/age_jm/manifest.json --junit .codex_tmp/age_jm/phase-08.junit.xml --report .codex_tmp/age_jm/phase-08.json
Run the impacted existing unit/adapter/backend tests as separate processes per repository/app, using approved isolated configuration. Run prior phase tests whenever shared code changed; the verifier invalidates stale dependent artifacts. Use section 4's exact additional health/E2E commands when this phase owns them.

Required assertions:
1. Both aliases on all five apps return the same graph contract and storage identity; ready means graph_backend=age, graph_connected=true, graph_name=soc_graph, fresh required-component success.
2. Fault Decision reads, topology, restore or required evidence separately: readiness is 503 with the failed component, never a synthetic healthy payload. Recovery becomes ready after successful repair/recheck.
3. Calling health repeatedly changes no graph counts/versions, creates no fixture/SQLite files, performs no seed/replay and never exposes credentials.
4. Launcher refuses verified [AGE] and preseed admission if any app is not ready, uses another DB, or supplies a malformed/minimal health response.
5. Repair backlog/completeness and durable version are visible; cutover/product claims remain false until Phase 10's evidence.

POST-CHECKS
- Re-scan all four production dependency roots for local stores, fixture/default branches, raw Decision queries, missing domain and broad/conditional exception suppression. Classify new hits; do not truncate scans or broaden allowlists.
- Verify zero new violations and no unresolved production candidates owned by this phase. Update each assigned gap with actual test node IDs, counts, source/config/schema hashes and evidence links; do not mark later-phase gaps closed.
- Review required health components: before Phase 8, report the harness's direct read-only component probes rather than claiming existing health aliases are fixed. After Phase 8, validate both /health and /api/health, readiness failure/recovery and storage identity.
- A phase is complete only if all its assertions pass. Otherwise record BLOCKED/INCOMPLETE with failing test/candidate and exact next action; do not proceed or weaken an assertion.

SESSION STATE
Append (do not rewrite) copilot-sdk/docs/session_state.md under AGE-JM-PHASE-08 with date, G049, G050, G051, G052, G053, G054, G055, exact changes, commands and pass/fail/skip counts, target's redacted identity, evidence path, candidate dispositions, remaining blockers and next phase readiness. Update copilot-sdk/docs/age_jm_execution_state.json without losing previous entries. Never paste DSN secrets.
```

**Verification gate:**

- Both aliases on all five apps return the same graph contract and storage identity; ready means graph_backend=age, graph_connected=true, graph_name=soc_graph, fresh required-component success.
- Fault Decision reads, topology, restore or required evidence separately: readiness is 503 with the failed component, never a synthetic healthy payload. Recovery becomes ready after successful repair/recheck.
- Calling health repeatedly changes no graph counts/versions, creates no fixture/SQLite files, performs no seed/replay and never exposes credentials.
- Launcher refuses verified [AGE] and preseed admission if any app is not ready, uses another DB, or supplies a malformed/minimal health response.
- Repair backlog/completeness and durable version are visible; cutover/product claims remain false until Phase 10's evidence.

Gate artifact: `.codex_tmp/age_jm/phase-08.json`; required tests: `copilot-sdk/integration/age_jm/test_phase_08_health.py`. Phase 9 must not start on a missing, failed or stale gate.

### Phase 9: Graph-native preseed, examples, CI enforcement, and E2E (estimated effort: 7d)

**Gaps closed:** G056, G057, G058, G059, G061, G062, G063, G064

**Depends on:** Phase 8 gate and all earlier gates; stale predecessor evidence must be rerun.

**Repos touched:** copilot-sdk, ci-platform, s2p-copilot, gen-ai-roi-demo-v4-v50.

**Codex prompt specification:**

```text
/model astra
/reasoning high

Codex Prompt: AGE-JM-PHASE-09
Execute Phase 9 only: Graph-native preseed, examples, CI enforcement, and E2E.
Workspace: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects
Repositories allowed: copilot-sdk, ci-platform, s2p-copilot, gen-ai-roi-demo-v4-v50.
Closure IDs, in implementation order: G056, G057, G058, G059, G061, G062, G063, G064.

RULES
- No git. Preserve unrelated work. Do not edit the JM paper or historical compliance report.
- Read copilot-sdk/docs/age_jm_execution_plan.md sections 1, 2, 4 and 7 and this phase, plus the complete assigned findings in copilot-sdk/docs/age_jm_compliance_report.md.
- Follow applicable AGENTS.md. Use current symbol definitions, not stale line numbers. Do not spawn agents unless separately authorized.
- Change only this phase's listed implementation targets, their typed adapter/protocol/call-site dependencies, tests/harness/CI required by this phase, and execution/candidate/session evidence. Explain any necessary scope expansion before changing unrelated components.
- Use a verified disposable AGE database with graph soc_graph, isolated app processes/data roots, production profile, and no demo/preseed conservation bypass. Never reset or fault the user's active database or invoke real broker/payment/SAP/order actions.
- Missing test infrastructure is BLOCKED, never a skipped PASS. No production deployment/migration without explicit target approval. Do not remove or overwrite original legacy stores.
- Each accepted operation must be durable and domain-scoped; graph errors cannot become fixture/local/empty-data success. No scoring-kernel or unapproved threshold changes.

PRE-CHECKS
1. Confirm workspace and sibling repo paths; inspect only in-scope files. Read execution_state.json and candidate_dispositions.json if present; verify predecessor gate artifacts and source/schema/config hashes. Do not proceed unless Phase 8 and all earlier required gates passed.
2. Read preseed_all_copilots.py, demo.py's current and legacy seed paths, bundle restore, all three reference app engines, migration/backup tools, test fixtures/workflows, static validator/allowlist, E2E global setup/projects and the current four Trading specs. Read ALL remaining OPEN candidate dispositions, not only G056–G064.
3. Validate the .codex_tmp/age_jm/manifest.json target against the server-owned disposable marker before any app startup/test that may write. Capture source fingerprints without git. Record changed/renamed call sites and preserve unrelated edits.

PHASE-SPECIFIC IMPLEMENTATION
A. Make HTTP preseed require Phase-8 readiness and exact target identity before any mutation. Seed only a manifest-authorized disposable demo/test dataset here. Verify every returned Decision ID/domain and required outcome/receipt/path in AGE after each batch; idempotent reruns cannot duplicate counts. No permissive health 200 shortcut or fingerprint-only success.
B. Retire legacy InMemory DemoPreseed production startup path or constrain it to explicit offline generation. Replace SQLite-only bundle restore with graph-native import that covers all four memories and marks synthetic provenance. Do not flip COPILOT_PRESEED_MODE in a live process to bypass conservation; use an isolated seed capability with no ordinary autonomous authorization.
C. Finish reusable idempotent migration/dry-run/verify tooling for legacy SQLite/outboxes/JSON/blob/surrogate links and raw posterior SQL. All tools resolve through GraphConfig, show redacted source/target identities, require matching signed/run-owned authorization and preserve source hashes. AGE backup/restore replaces misleading Trading SQLite backup claims. Rehearse with copies; no destructive production execution.
D. Add AGE as the primary JM reference demonstration; trading_clone delegates to that mode and build_your_own uses an explicit graph/domain config. Support custom isolated demo domains only through validated registration, not hardcoded five-domain loopholes. Keep a distinctly named offline mode without shared-JM claims. Demonstrate the four traversals and restart reconstruction in real AGE.
E. Complete required CI across all four repos: pinned tested AGE/PostgreSQL service, production-profile subprocess apps, no skip/xfail for the required graph suite, all phase assertions and graph contract failures blocking. Tighten validator to all four runtime roots, import/call-boundary reachability, conditional catches and expiring narrow exemptions. No global allowlist for a whole offender file.
F. Dispose of every remaining production OPEN candidate: source trace, fault test and either migration/removal or a proven isolated/non-authoritative classification. New genuine bypasses are assigned and fixed within their owning family; expand estimates and record blockers if materially outside scope. Zero unresolved production candidates is a hard gate; do not relabel them operator-only without caller evidence.
G. Split E2E UI-mock contracts from unmocked graph-integration projects. Parameterize URLs from the manifest; fix backend truth before expectations. Seed named graph episodes/verification/receipts, test empty/accumulating/measured/unavailable honestly, and assert data identity/version across panels. Existing day-zero mocks already cover actual endpoints; do not 'fix' that alias without source evidence.
H. Run all SDK Trading/Purchasing/DataOps/S2P E2E projects and SOC's separate frontend suite against the isolated AGE stack. Keep mock UI suites as separate tests; do not count them as graph integration or weaken unavailable/error assertions to force green.

EXACT GAP WORK ITEMS

G056: HTTP preseed does not prove graph destination or completeness
Targets: copilot-sdk/scripts/preseed_all_copilots.py:229,236,400,407,583,590,613,630.
Functions: preseed_all_copilots.py:check_health, preseed_all_copilots.py:check_already_seeded, preseed_all_copilots.py:seed_s2p_domain, preseed_all_copilots.py:seed_domain, preseed_all_copilots.py:verify_domain.
Required change: Before seeding, require canonical graph readiness; afterward verify each returned ID, explicit domain, outcome/receipt and required edges via read-only GraphStore checks on the same graph.
Acceptance ownership: add test_g056_* cases to copilot-sdk/integration/age_jm/test_phase_09_delivery.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G057: Legacy deterministic preseed conflicts with production scorer guards
Targets: copilot-sdk/demo.py:1368,1472,1476,1480; copilot-sdk/copilot_sdk/demo/preseed.py:217,218.
Functions: demo.py:_seed_during_start, demo.py:_run_deterministic_seed, preseed.py:_preseed_domain.
Required change: Retire this path or use the canonical API/AGE seed runner. If retained for isolated artifact generation, pass explicit test mode and do not report it as production seeding.
Acceptance ownership: add test_g057_* cases to copilot-sdk/integration/age_jm/test_phase_09_delivery.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G058: Demo state bundle restoration remains SQLite-only
Targets: copilot-sdk/copilot_sdk/demo/bundle.py:49,58,61,155; copilot-sdk/apps/trading/backend/app/main.py:497.
Functions: bundle.py:_restore, main.py:_run_startup_locked.
Required change: Implement graph-native seed/restore with explicit provenance and all memory relationships, or remove the feature from AGE startup. Require migration receipts before claiming parity.
Acceptance ownership: add test_g058_* cases to copilot-sdk/integration/age_jm/test_phase_09_delivery.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G059: JM and clone reference apps teach isolated local storage
Targets: copilot-sdk/examples/jm_reference/run.py:83,93; copilot-sdk/examples/trading_clone/run.py:29; copilot-sdk/examples/build_your_own/engine.py:89; copilot-sdk/examples/build_your_own/run.py:1.
Functions: run.py:run_experiment, engine.py:_new_governed_arm, run.py:module initialization.
Required change: Keep an explicitly labelled offline mode and add a first-class AGE/sharedGraph mode with typed config, linked four-memory examples and a cross-domain traversal assertion.
Acceptance ownership: add test_g059_* cases to copilot-sdk/integration/age_jm/test_phase_09_delivery.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G061: Live AGE tests exist but are optional/skippable and CI provisions no AGE service
Targets: copilot-sdk/tests/graph/conftest.py:20,22,28; s2p-copilot/backend/tests/conftest.py:133,136,146; gen-ai-roi-demo-v4-v50/backend/tests/conftest.py:51,54,64; gen-ai-roi-demo-v4-v50/backend/conftest.py:95,159,174; copilot-sdk/.github/workflows/ci.yml:31; s2p-copilot/.github/workflows/ci.yml:31; ci-platform/.github/workflows/ci.yml:24; gen-ai-roi-demo-v4-v50/.github/workflows/ci.yml:36.
Functions: conftest.py:age_test_graph, conftest.py:s2p_age_test_env, conftest.py:soc_stress_test_graph, conftest.py:_count_persistent, conftest.py:report_graph_contract.
Required change: Provision a disposable shared AGE database with a required graph-integration job; fail on skip/unavailable in that job. Exercise all four interaction classes, restart, crash/outage and domain collision scenarios.
Acceptance ownership: add test_g061_* cases to copilot-sdk/integration/age_jm/test_phase_09_delivery.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G062: Static unification gates check text, not architecture
Targets: copilot-sdk/scripts/validate_age_unification.py:35,59,75,83,132,153; copilot-sdk/docs/design/age_unification_forbidden_patterns_allowlist.toml:13,44,49.
Functions: validate_age_unification.py:production_files, validate_age_unification.py:check_domain_isolation, validate_age_unification.py:check_config_completeness, validate_age_unification.py:check_fail_closed, validate_age_unification.py:check_no_bare_except, validate_age_unification.py:check_health_graph_status.
Required change: Use AST call-graph/import boundaries plus typed config/store injection; scope all four repos, require expiring narrow exemptions and a required live contract job. Fail newly introduced runtime SQLite/fixture fallback and ungated defaults.
Acceptance ownership: add test_g062_* cases to copilot-sdk/integration/age_jm/test_phase_09_delivery.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G063: Maintenance/migration tools and Trading backup still bypass unified configuration
Targets: copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:23,75; copilot-sdk/apps/trading/backend/app/cli_sdk.py:47,578,591,598; s2p-copilot/backend/app/migration/s2p_entity_migration.py:493; copilot-sdk/demo.py:331.
Functions: sqlite_to_age.py:module initialization, sqlite_to_age.py:_default_source_path, cli_sdk.py:module initialization, cli_sdk.py:backup_sdk, cli_sdk.py:restore_sdk, s2p_entity_migration.py:_ensure_invoice_index, demo.py:verify_age.
Required change: Retain justified adapter/migration driver use with GraphConfig-derived, confirmed source/target identity. Add AGE-aware backup/restore documentation/tooling and verify full state, not only Decision counts.
Acceptance ownership: add test_g063_* cases to copilot-sdk/integration/age_jm/test_phase_09_delivery.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G064: E2E success and data assumptions do not establish graph correctness
Targets: copilot-sdk/e2e/trading/conservation-breakdown.spec.ts:34,39; copilot-sdk/e2e/trading/day-zero.spec.ts:4,33,36,48; copilot-sdk/e2e/trading/trust-radar.spec.ts:48,127,242; copilot-sdk/e2e/trading/new-surfaces.spec.ts:36,52,59.
Functions: Current spec test bodies, fetchTrust/mockMeasurementState helpers, UI API consumers and Playwright setup/project configuration
Required change: Separate UI contract tests from required real-AGE integration E2E. Seed named graph evidence, use configured base URLs, assert unavailable on outage, and verify graph-backed data identity rather than panel presence.
Acceptance ownership: add test_g064_* cases to copilot-sdk/integration/age_jm/test_phase_09_delivery.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

VERIFICATION
Create/extend copilot-sdk/integration/age_jm/test_phase_09_delivery.py; do not run a nonexistent test file and interpret non-collection as success.
From workspace root, on the disposable stack, run:
python -X utf8 -m pytest copilot-sdk/integration/age_jm/test_phase_09_delivery.py --age-jm-manifest .codex_tmp/age_jm/manifest.json --age-jm-require --strict-markers -q --junitxml=.codex_tmp/age_jm/phase-09.junit.xml
python -X utf8 copilot-sdk/scripts/verify_age_jm_phase.py --phase 09 --manifest .codex_tmp/age_jm/manifest.json --junit .codex_tmp/age_jm/phase-09.junit.xml --report .codex_tmp/age_jm/phase-09.json
Run the impacted existing unit/adapter/backend tests as separate processes per repository/app, using approved isolated configuration. Run prior phase tests whenever shared code changed; the verifier invalidates stale dependent artifacts. Use section 4's exact additional health/E2E commands when this phase owns them.

Required assertions:
1. Preseed rerun preserves IDs/counts/versions; every seeded artifact and relationship is visible from the same graph through the intended copilot. Wrong identity/unready app blocks before first write.
2. No startup or ordinary production route can enable conservation bypass from demo/preseed flags. Synthetic seed data remains synthetic and outside live/measured eligibility.
3. Each migration fixture has source-preserving dry-run, apply-to-test-copy, idempotent rerun, parity/receipt/path verification and restoration proof. Unknown legacy destination/provenance blocks rather than guesses.
4. All three reference apps have a tested AGE mode; JM reference proves four single traversals and restart persistence, not SQLite equivalence.
5. Required CI jobs provision AGE and fail on missing AGE, skips/xfails, missing expected tests or graph-contract warnings. DG-1..DG-7 assertions pass and OPEN production candidate count is zero.
6. Full E2E suites for all five apps pass on the graph-backed stack with required test inventory and no masked data assertions; outage cases return/render unavailable. Mock-only runs are separately labelled.

POST-CHECKS
- Re-scan all four production dependency roots for local stores, fixture/default branches, raw Decision queries, missing domain and broad/conditional exception suppression. Classify new hits; do not truncate scans or broaden allowlists.
- Verify zero new violations and no unresolved production candidates owned by this phase. Update each assigned gap with actual test node IDs, counts, source/config/schema hashes and evidence links; do not mark later-phase gaps closed.
- Review required health components: before Phase 8, report the harness's direct read-only component probes rather than claiming existing health aliases are fixed. After Phase 8, validate both /health and /api/health, readiness failure/recovery and storage identity.
- A phase is complete only if all its assertions pass. Otherwise record BLOCKED/INCOMPLETE with failing test/candidate and exact next action; do not proceed or weaken an assertion.

SESSION STATE
Append (do not rewrite) copilot-sdk/docs/session_state.md under AGE-JM-PHASE-09 with date, G056, G057, G058, G059, G061, G062, G063, G064, exact changes, commands and pass/fail/skip counts, target's redacted identity, evidence path, candidate dispositions, remaining blockers and next phase readiness. Update copilot-sdk/docs/age_jm_execution_state.json without losing previous entries. Never paste DSN secrets.
```

**Verification gate:**

- Preseed rerun preserves IDs/counts/versions; every seeded artifact and relationship is visible from the same graph through the intended copilot. Wrong identity/unready app blocks before first write.
- No startup or ordinary production route can enable conservation bypass from demo/preseed flags. Synthetic seed data remains synthetic and outside live/measured eligibility.
- Each migration fixture has source-preserving dry-run, apply-to-test-copy, idempotent rerun, parity/receipt/path verification and restoration proof. Unknown legacy destination/provenance blocks rather than guesses.
- All three reference apps have a tested AGE mode; JM reference proves four single traversals and restart persistence, not SQLite equivalence.
- Required CI jobs provision AGE and fail on missing AGE, skips/xfails, missing expected tests or graph-contract warnings. DG-1..DG-7 assertions pass and OPEN production candidate count is zero.
- Full E2E suites for all five apps pass on the graph-backed stack with required test inventory and no masked data assertions; outage cases return/render unavailable. Mock-only runs are separately labelled.

Gate artifact: `.codex_tmp/age_jm/phase-09.json`; required tests: `copilot-sdk/integration/age_jm/test_phase_09_delivery.py`. Phase 10 must not start on a missing, failed or stale gate.

### Phase 10: Migration rehearsal, cutover evidence, and final closure (estimated effort: 4d)

**Gaps closed:** G065, G066

**Depends on:** Phase 9 gate and all earlier gates; stale predecessor evidence must be rerun.

**Repos touched:** copilot-sdk, ci-platform, s2p-copilot, gen-ai-roi-demo-v4-v50.

**Codex prompt specification:**

```text
/model astra
/reasoning high

Codex Prompt: AGE-JM-PHASE-10
Execute Phase 10 only: Migration rehearsal, cutover evidence, and final closure.
Workspace: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects
Repositories allowed: copilot-sdk, ci-platform, s2p-copilot, gen-ai-roi-demo-v4-v50.
Closure IDs, in implementation order: G065, G066.

RULES
- No git. Preserve unrelated work. Do not edit the JM paper or historical compliance report.
- Read copilot-sdk/docs/age_jm_execution_plan.md sections 1, 2, 4 and 7 and this phase, plus the complete assigned findings in copilot-sdk/docs/age_jm_compliance_report.md.
- Follow applicable AGENTS.md. Use current symbol definitions, not stale line numbers. Do not spawn agents unless separately authorized.
- Change only this phase's listed implementation targets, their typed adapter/protocol/call-site dependencies, tests/harness/CI required by this phase, and execution/candidate/session evidence. Explain any necessary scope expansion before changing unrelated components.
- Use a verified disposable AGE database with graph soc_graph, isolated app processes/data roots, production profile, and no demo/preseed conservation bypass. Never reset or fault the user's active database or invoke real broker/payment/SAP/order actions.
- Missing test infrastructure is BLOCKED, never a skipped PASS. No production deployment/migration without explicit target approval. Do not remove or overwrite original legacy stores.
- Each accepted operation must be durable and domain-scoped; graph errors cannot become fixture/local/empty-data success. No scoring-kernel or unapproved threshold changes.

PRE-CHECKS
1. Confirm workspace and sibling repo paths; inspect only in-scope files. Read execution_state.json and candidate_dispositions.json if present; verify predecessor gate artifacts and source/schema/config hashes. Do not proceed unless Phase 9 and all earlier required gates passed.
2. Read all phase evidence/current source hashes, candidate dispositions, graph_status cutover conditions/receipt exclusions and verify_state.verify_level3. Build a full legacy-state inventory and graph census on authorized read-only targets. Ask for separate approval before live migration/cutover; a rehearsal is not deployment authorization.
3. Validate the .codex_tmp/age_jm/manifest.json target against the server-owned disposable marker before any app startup/test that may write. Capture source fingerprints without git. Record changed/renamed call sites and preserve unrelated edits.

PHASE-SPECIFIC IMPLEMENTATION
A. Re-run all prior gates with current code/schema/config hashes. A changed dependency invalidates stale evidence; all 66 gaps and every production candidate require current passing evidence.
B. Rehearse backup → dry-run migration → apply to disposable copy → verify → restart all five → rollback restore in an isolated database. Cover Decisions/outcomes/receipts, centroids/fingerprints/K/conservation, signals/episodes/entities, rules/promotion/authority, holdouts, supplier history, JSON state and actual edges. Compare IDs/domains/content/provenance/version semantics, not only totals.
C. Do not reconstruct unverifiable historical receipts and call them original verified evidence. Mark imported prior/history explicitly, preserve original sources, and block required product claims until evidence is actually sufficient. Unknown/corrupt legacy records need operator disposition.
D. Replace Trading's hardcoded/test-only cutover flags and app-specific receipt/rollback exclusions with one evidence-based readiness/claim model. Proof must match actual target storage identity, code/schema/policy versions, freshness, required traversals, migration parity and rollback drill. Connectivity alone never makes product_claim_allowed true.
E. If explicitly authorized for the named live target: snapshot/back up, fence authoritative writers, drain/reconcile in-flight operations, migrate idempotently, validate census/paths/receipts, restart against the target, run read-only readiness and semantic checks, then unfreeze. Abort on any mismatch; no SQLite-primary rollback. Roll back code+graph snapshot as a compatible pair with writes fenced and an explicit no-loss reconciliation plan.
F. If live authorization is absent, finish the rehearsal and code but record 'deployment/cutover blocked pending approval'; do not mark G065/G066 or the architecture operationally complete.
G. Preserve migration inputs/backups per retention policy; no deletion is implicit. Record full final evidence and remaining limitations in session state, and publish architecture-complete only if §7 passes.

EXACT GAP WORK ITEMS

G065: Trading cutover/claim flags are intentionally incomplete
Targets: copilot-sdk/apps/trading/backend/app/graph_status.py:421,429,452.
Functions: graph_status.py:build_trading_graph_status.
Required change: Define evidence-based cutover criteria, run them against an authorized disposable graph, migrate/reconcile history and receipts, and compute flags from durable validation artifacts. Do not simply change false to true.
Acceptance ownership: add test_g065_* cases to copilot-sdk/integration/age_jm/test_phase_10_cutover.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

G066: Cross-app cutover excludes receipt/rollback completeness
Targets: copilot-sdk/apps/purchasing/backend/app/graph_status.py:1; copilot-sdk/apps/dataops/backend/app/graph_status.py:1; s2p-copilot/backend/app/s2p_graph_status.py:35,437,475; copilot-sdk/copilot_sdk/migrate/verify_state.py:486.
Functions: graph_status.py:module initialization, s2p_graph_status.py:module initialization, s2p_graph_status.py:build_s2p_graph_status, verify_state.py:verify_level3.
Required change: Inventory and migrate local judgment/procedural state, then verify domain counts, IDs, canonical receipts, links, learning version and reversible rollback. Publish one cutover schema for all five.
Acceptance ownership: add test_g066_* cases to copilot-sdk/integration/age_jm/test_phase_10_cutover.py, covering current behavior, failure and domain/provenance/restart cases applicable to this gap. Trace and resolve every candidate in the same reachable path; a one-line fix is not sufficient if callers still suppress the error.

VERIFICATION
Create/extend copilot-sdk/integration/age_jm/test_phase_10_cutover.py; do not run a nonexistent test file and interpret non-collection as success.
From workspace root, on the disposable stack, run:
python -X utf8 -m pytest copilot-sdk/integration/age_jm/test_phase_10_cutover.py --age-jm-manifest .codex_tmp/age_jm/manifest.json --age-jm-require --strict-markers -q --junitxml=.codex_tmp/age_jm/phase-10.junit.xml
python -X utf8 copilot-sdk/scripts/verify_age_jm_phase.py --phase 10 --manifest .codex_tmp/age_jm/manifest.json --junit .codex_tmp/age_jm/phase-10.junit.xml --report .codex_tmp/age_jm/phase-10.json
Run the impacted existing unit/adapter/backend tests as separate processes per repository/app, using approved isolated configuration. Run prior phase tests whenever shared code changed; the verifier invalidates stale dependent artifacts. Use section 4's exact additional health/E2E commands when this phase owns them.

Required assertions:
1. Current unmocked all-five stack passes every DG and four-memory traversal assertion with identical target identity; all 66 closure records and zero OPEN production candidates are verified.
2. Migration parity includes canonical receipts, domains, edge cardinality, provenance and learning versions; no accepted Decision lacks required artifacts and no orphan authority/promotion survives.
3. Crash/restart, lost-ack retry, concurrent writers and outage/recovery tests preserve conservation and idempotency; rollback drill restores a consistent AGE-backed system without silent loss.
4. cutover_ready and product_claim_allowed are computed from current target-bound evidence, not hardcoded true, test mode, class name, liveness or counts alone.
5. Authorized live verification passes or deployment remains explicitly blocked; no production-complete claim based solely on disposable rehearsal.

POST-CHECKS
- Re-scan all four production dependency roots for local stores, fixture/default branches, raw Decision queries, missing domain and broad/conditional exception suppression. Classify new hits; do not truncate scans or broaden allowlists.
- Verify zero new violations and no unresolved production candidates owned by this phase. Update each assigned gap with actual test node IDs, counts, source/config/schema hashes and evidence links; do not mark later-phase gaps closed.
- Review required health components: before Phase 8, report the harness's direct read-only component probes rather than claiming existing health aliases are fixed. After Phase 8, validate both /health and /api/health, readiness failure/recovery and storage identity.
- A phase is complete only if all its assertions pass. Otherwise record BLOCKED/INCOMPLETE with failing test/candidate and exact next action; do not proceed or weaken an assertion.

SESSION STATE
Append (do not rewrite) copilot-sdk/docs/session_state.md under AGE-JM-PHASE-10 with date, G065, G066, exact changes, commands and pass/fail/skip counts, target's redacted identity, evidence path, candidate dispositions, remaining blockers and next phase readiness. Update copilot-sdk/docs/age_jm_execution_state.json without losing previous entries. Never paste DSN secrets.
```

**Verification gate:**

- Current unmocked all-five stack passes every DG and four-memory traversal assertion with identical target identity; all 66 closure records and zero OPEN production candidates are verified.
- Migration parity includes canonical receipts, domains, edge cardinality, provenance and learning versions; no accepted Decision lacks required artifacts and no orphan authority/promotion survives.
- Crash/restart, lost-ack retry, concurrent writers and outage/recovery tests preserve conservation and idempotency; rollback drill restores a consistent AGE-backed system without silent loss.
- cutover_ready and product_claim_allowed are computed from current target-bound evidence, not hardcoded true, test mode, class name, liveness or counts alone.
- Authorized live verification passes or deployment remains explicitly blocked; no production-complete claim based solely on disposable rehearsal.

Gate artifact: `.codex_tmp/age_jm/phase-10.json`; required tests: `copilot-sdk/integration/age_jm/test_phase_10_cutover.py`. Passing a rehearsal without live approval does not satisfy the operational Definition of Done.

## 4. CI Prevention Gates

These are blocking requirements, not dashboard-only warnings. Phase 1 establishes the harness; Phase 9 closes the full gates; Phase 10 consumes their target-bound evidence. Every required job reports collected/pass/fail/skip/xfail counts and the source/config/schema fingerprint. Missing AGE, missing tests, changed expected inventory, expired exemptions or stale artifacts fail the job.

### 4.1 Required jobs and ownership

| Job | Required assertion | Introduced / fully enforced |
|---|---|---|
| age-jm-static | All four production dependency roots; no runtime SQLite/InMemory/fixture authority, raw copilot drivers/Decision Cypher, missing domain or catch-and-substitute; enumerate conditional handlers and indirect constructors | Phase 1 baseline; Phase 9 zero unresolved |
| age-jm-config-domain | Production config/injection cannot downgrade; all five target one identity/soc_graph; same-ID isolation, explicit cross-domain authorization | Phase 1 |
| age-jm-durability | Fault every bundle boundary; version conflict, lost acknowledgment and retry; no 2xx on failed required write; no SQLite repair path | Phase 2 |
| age-jm-learning | Eligible-set V/q/coverage; verified-only updates; conservation gate; learner published after graph commit; deterministic restart; utility/trace closure | Phase 3, app paths Phase 4 |
| age-jm-memory | All migrated side stores and context projections work from AGE with local memory/fixtures unavailable | Phases 5–6 |
| age-jm-traversals | All four single-Cypher interactions, evidence paths, entity conditioning, authorized Trading→S2P witness and governed apply | Phase 7 |
| age-jm-health | Both aliases, all five domains, same identity, fresh component results, readiness 503 on failure and no GET mutation | Phase 8 |
| age-jm-preseed-migrate | Wrong target blocked before mutation; every seed visible; idempotent full-memory migration and receipt/path parity on preserved copies | Phase 9 |
| age-jm-reference | JM/trading-clone/build-your-own AGE modes; restart and four-memory interaction proof | Phase 9 |
| age-jm-e2e | All-five AGE integration + separate mocked UI contracts; deterministic named evidence, failure/recovery, no unapproved skips | Phase 9 |
| age-jm-cutover | Target-bound all-gap/candidate closure, current proof, actual rollback rehearsal and approved migration evidence | Phase 10 |

Run adapter tests in ci-platform and SDK plus app-specific tests in separate processes. Existing useful examples to extend include ci-platform/tests/test_soc_outcome_checkpoint_transaction.py, test_age_graph_store_topology.py, test_domain_enforcement.py, and SDK graph domain-required/link-domain conformance tests. Do not assume these already cover full JM or cannot skip.

### 4.2 Static boundary / grep gate

A lexical discovery command (from workspace root):

```powershell
rg -n -i "sqlite3|SQLiteGraphStore|InMemoryGraphStore|SQLiteSignalStore|json\.load|fixture|fallback|except|run_query|import psycopg|from psycopg|import neo4j|from neo4j" copilot-sdk/copilot_sdk copilot-sdk/apps/trading/backend/app copilot-sdk/apps/purchasing/backend/app copilot-sdk/apps/dataops/backend/app s2p-copilot/backend/app gen-ai-roi-demo-v4-v50/backend/app ci-platform/ci_platform -g "*.py" -g "!**/__pycache__/**"
```

Do not require this entire regex to produce zero lines: legitimate JSON graph serialization, explicit rejection messages, adapter drivers and exception rethrows match. Pipe the **complete** findings into the strengthened scripts/validate_age_unification.py and candidate ledger, not Select-Object -First. Phase 9 must extend that script's command interface (NEW flags) to support:

```powershell
python -X utf8 copilot-sdk/scripts/validate_age_unification.py --workspace-root . --strict-production --candidate-ledger copilot-sdk/docs/age_jm_candidate_dispositions.json --fail-on-open
```

Strict pass conditions: zero reachable local authoritative stores; zero copilot driver/Decision-query boundary violations; zero missing-domain operations; zero data-bearing substitutes on required graph failure. Local store implementations move to explicit offline/test modules or remain unreachable from the production dependency graph with proved isolation. Each permitted operator/parser/export match has a narrow symbol-level rationale and a caller/profile test. No whole-file allowlist or “it has a 503 somewhere” heuristic.

The AST checker is a regression detector, not a proof of dynamic Python behavior; fault tests and actual runtime store identity close that gap. Updating the exemption/baseline requires review and may not reduce test coverage. No replacing “except Exception: return []” with a helper that does the same thing.

### 4.3 Canonical health assertions

Phase 8 implements the following contract for BOTH /health and /api/health. Example successful shape (not a claim about current endpoints):

```json
{
  "ready": true,
  "graph_backend": "age",
  "graph_connected": true,
  "graph_name": "soc_graph",
  "graph_status": {
    "connected": true,
    "graph_name": "soc_graph",
    "storage_identity": "server-issued-redacted-database-and-graph-identity",
    "dsn_source": "env:GRAPH_DSN",
    "checked_at": "2026-09-22T12:00:00Z",
    "components": {
      "decisions": "ready",
      "topology": "ready",
      "learning_restore": "ready",
      "required_evidence": "ready"
    },
    "durable_learning_version": 0,
    "required_incomplete_operations": 0
  },
  "autonomy_allowed": false,
  "cutover_ready": false,
  "product_claim_allowed": false
}
```

A successfully read empty graph can be ready while autonomy/claims are false. Failed availability is not GREEN or “day zero.” The concrete identity is issued/verified by the database and graph metadata, not a client-provided DSN hash that changes when credentials rotate. DSN source names the winning config key/file without its secret value.

After Phase 8, run read-only assertions against the manifest-owned stack:

```powershell
$jmManifest = Get-Content -LiteralPath .codex_tmp/age_jm/manifest.json -Raw | ConvertFrom-Json
$jmIdentities = @()
foreach ($jmDomain in @("soc", "s2p", "trading", "purchasing", "dataops")) {
    $jmBase = $jmManifest.backends.$jmDomain
    if (-not $jmBase) { throw "Missing backend URL for $jmDomain" }
    foreach ($jmAlias in @("/health", "/api/health")) {
        $jmHealth = Invoke-RestMethod -Uri ($jmBase + $jmAlias) -TimeoutSec 10
        if ($jmHealth.ready -ne $true -or $jmHealth.graph_backend -ne "age" -or
            $jmHealth.graph_connected -ne $true -or $jmHealth.graph_name -ne "soc_graph" -or
            $jmHealth.graph_status.connected -ne $true -or
            $jmHealth.graph_status.graph_name -ne "soc_graph") {
            throw "Graph readiness failed: $jmDomain $jmAlias"
        }
        if (-not $jmHealth.graph_status.storage_identity -or -not $jmHealth.graph_status.dsn_source) {
            throw "Missing identity/config provenance: $jmDomain"
        }
        $jmAge = [DateTimeOffset]::UtcNow - [DateTimeOffset]::Parse($jmHealth.graph_status.checked_at)
        if ($jmAge.TotalSeconds -gt 30 -or $jmAge.TotalSeconds -lt -5) { throw "Stale graph probe" }
        if ($jmHealth.graph_status.required_incomplete_operations -ne 0) { throw "Incomplete required state" }
        $jmIdentities += $jmHealth.graph_status.storage_identity
    }
}
if (@($jmIdentities | Select-Object -Unique).Count -ne 1) { throw "Copilots do not share one graph" }
if ($jmIdentities[0] -ne $jmManifest.expected_storage_identity) { throw "Wrong graph target" }
```

The integration suite additionally validates the whole JSON schema, field types, required components and alias equivalence. For failures use tests that inspect HTTP 503/error bodies; Invoke-RestMethod throwing is not enough to prove correct contents. Health probes must leave before/after graph censuses identical.

### 4.4 Preseed, migration and traversal verification

Required test records cover all five domains, actual entities/episodes, pending Decisions, approved verification identities, canonical receipts and links, judgment versions, procedure evaluations and one reviewed compatible transfer mapping. Seed data must carry truthful test/synthetic provenance; it is not customer-measured evidence. Use a disposable **test evidence population** to exercise verified-state transitions, and independently prove production eligibility excludes test/demo populations. Do not globally turn off eligibility/conservation checks to force measured state. UI-only simulated MEASURED states remain clearly separate mocks.

For each preseed response verify ID/domain/content with GraphStore, outcome/receipt/hash chain, required edge cardinality and learning disposition/version. Capture a census before/after and after an idempotent rerun. Verify unready/mismatched targets abort before the first POST.

For each named interaction, assert exactly one Cypher traversal and return a nonempty connected path for its seeded witness; all participating IDs, domains, evidence versions and policy state must match. Disable local fixture/file readers during the test and prohibit application-side cross-store joins. A graph query returning a precomputed static demo answer or a serialized list of unrelated IDs fails.

The requested Trading→S2P test must prove an actual source centroid/fingerprint version written by the Trading workflow is visible to the authorized S2P traversal; compatible mapping and both-domain gate evidence are mandatory before apply. A single shared GraphStore object in a mocked unit test does not prove shared database reachability.

### 4.5 Test and E2E command matrix

The Phase-1 harness introduces the --age-jm-* options below; they are not existing pytest options today. Run complete phase regression after Phase 9:

```powershell
python -X utf8 -m pytest copilot-sdk/integration/age_jm --age-jm-manifest .codex_tmp/age_jm/manifest.json --age-jm-require --strict-markers -q --junitxml=.codex_tmp/age_jm/all-phases.junit.xml
```

App unit/legacy live suites must run with test-run-owned configuration and reviewed conftest safety, each as a separate command/process. Typical existing commands (after that setup):

```powershell
python -X utf8 -m pytest copilot-sdk/tests -q
python -X utf8 -m pytest copilot-sdk/apps/trading/backend/tests -q
python -X utf8 -m pytest copilot-sdk/apps/purchasing/backend/tests -q
python -X utf8 -m pytest copilot-sdk/apps/dataops/backend/tests -q
python -X utf8 -m pytest ci-platform/tests -q
python -X utf8 -m pytest s2p-copilot/backend/tests -q
python -X utf8 -m pytest gen-ai-roi-demo-v4-v50/backend/tests -q
```

These existing suites can contain isolated mocks/skips; report them separately and do not let their configuration overwrite the required production-profile integration job. Do not run them against ambient/default DATABASE_URL/GRAPH_DSN. ci-platform currently has pytest environment defaults: the safety wrapper must explicitly replace target settings and verify identity before collection/import.

Phase 9 changes Playwright config/global setup to honor a NEW AGE_JM_MANIFEST variable for all backend/frontend URLs and seed ownership. From workspace root:

```powershell
$env:AGE_JM_MANIFEST = (Resolve-Path -LiteralPath .codex_tmp/age_jm/manifest.json).Path
Push-Location copilot-sdk/e2e
try {
    npx tsc --noEmit
    npx playwright test --project=trading --project=purchasing --project=dataops --project=s2p --project=demo-soc
    npx playwright test
} finally {
    Pop-Location
}
Push-Location gen-ai-roi-demo-v4-v50/frontend
try {
    npx playwright test
} finally {
    Pop-Location
}
```

Capture exit codes after EACH native command; PowerShell does not automatically abort for every nonzero native exit. The CI wrapper must throw/exit on any nonzero status and fail if expected tests are skipped/missing. The matrix includes SOC's separate frontend suite, not only SDK's three main apps. If another repo has a distinct required S2P/SOC suite, inventory and add it; no silently narrowing “all E2E” to four specs. Existing mock UI tests may still run, but the **unmocked AGE integration** project must prove graph state rather than route fulfillments.

Do not execute current global setup against the user's active demo stack: it can seed/reset data. First implement manifest enforcement and isolate the stack. Browser/UI tools, if used by future sessions, must follow the applicable browser skill.

### 4.6 Evidence and regression rules

- Each G ID closes only with named assertions, test node IDs, target identity, source/config/schema fingerprint and candidate disposition evidence. Merely mentioning G001–G066 is not coverage.
- Every required test must collect and pass. Missing AGE, skip, xfail, warning-only graph contract or zero-test success is a failed gate.
- A later source/schema/policy change invalidates affected earlier evidence. Rerun dependent gates, not just the current phase.
- Candidate entries cannot be deleted to reach zero. An excluded match needs reachability and authority reasoning plus isolation test; unresolved production candidates block G062/G066.
- Schema migration and source compatibility are tested in expand → migrate → verify → switch order. Contract tests cover both supported transitional readers; no dual-write SQLite authority.
- CI artifacts are redacted and target-bound. No DSNs, customer payloads or raw sensitive evidence in session markdown.

## 5. E2E Impact Map

These are dependency-based expectations, not a claim to have reproduced historical failures. The compliance audit was static. Backend defects and outdated spec assumptions must be distinguished during Phase 9.

| Spec / surface | Gap IDs | Backend resolution phases | Final E2E gate |
|---|---|---|---|
| copilot-sdk/e2e/trading/conservation-breakdown.spec.ts | G030, G003, G004, G064 | 3 (durable conservation), 5 (graph episodes), 6 (truthful projection) | 9: named AGE categories/outcomes agree with proxy/global provenance; empty/unavailable tested separately, not counted as populated proof |
| copilot-sdk/e2e/trading/day-zero.spec.ts | G001, G003, G004, G049, G064 | 2–3, 8 | 9: zero vs unavailable vs accumulating/measured; /api/health + /api/conservation/status + /api/trading/measurement-state actual consumers verified; preserve correct UI mocks in separate suite |
| copilot-sdk/e2e/trading/trust-radar.spec.ts | G020, G030, G032, G048, G064 | 4, 5, 6, 7 | 9: graph-backed episodes/K/fingerprint evidence after restart; 10-factor UI contract does not fabricate live history or forbid legitimate unavailable state |
| copilot-sdk/e2e/trading/new-surfaces.spec.ts — rejection moment | G023, G003, G031, G064 | 3, 5, 6 | 9: counters/reasons reference real graph evaluation/promotions; no learned JSON seed overlay |
| copilot-sdk/e2e/trading/new-surfaces.spec.ts — diagnostics/measurement/conservation/history | G001, G003, G004, G049, G055, G064 | 2–3, 8 | 9: consistent durable version/eligible counts across endpoints; not just HTTP 200/shape |
| copilot-sdk/e2e/trading/new-surfaces.spec.ts — transfers | G005, G006, G021, G044, G047, G064 | 2, 3, 7 | 9: explicit same-graph witness, both-domain gate, no demo pattern or partial impact |
| SDK Purchasing E2E directory | G013, G024, G028, G033, G050, G056, G064 | 3–6, 8–9 | 9: graph order/payment/audit evidence and both health aliases; no hard-coded verified audit pack |
| SDK DataOps E2E directory | G011, G012, G022, G027, G034, G043, G048, G051, G056, G064 | 1, 4–9 | 9: consistent topology/Decision identity, real lineage/evidence, no fixture injection on live/outage |
| SDK S2P E2E and any separate S2P suite | G014, G015, G035, G036, G048, G052, G056, G064 | 4–9 | 9: supplier replay, evidence/receipt persistence, verified-only learning and graph-ready health |
| gen-ai-roi-demo-v4-v50/frontend Playwright + SDK demo-soc | G016, G017, G018, G019, G037, G041, G046, G053, G064 | 4, 7–9 | 9: real graph metric/history/authority, no proceed-on-failure and no raw Decision bypass |

Product/UI code may need availability/error presentation changes after backends stop lying. Do not “resolve” tests by restoring fixture fallbacks, accepting any 200, skipping graph-backed cases or removing evidence assertions.

## 6. Risk Register

| Risk | Detect | Mitigate / stop condition |
|---|---|---|
| Test points to active production/demo data | Manifest identity differs from server-owned disposable marker; app data root outside test run | Refuse collection/startup/mutation. Never infer permission from localhost or graph name |
| Report/source drift | Symbol moved, source fingerprint differs, new catch/store found | Re-resolve callers, update execution ledger, retest; keep audit historical |
| OPEN candidates are larger than 66 group estimates | Candidate remains reachable/authoritative and has no test/disposition | Assign to its family, revise effort; block final closure, never drop it from inventory |
| AGE transaction facade commits inner operations independently | Fault after each operation; new connection sees partial bundle | Extend existing transaction-scoped facade; forbid independent _run_query inside bundle |
| Lost response after successful commit | Retry creates duplicate V/centroid/K delta | Stable operation keys, committed-result lookup, idempotent receipt; surface indeterminate rather than invent success/failure certainty |
| Concurrent writer lost update or conservation TOCTOU | Two-process same-version tests; source/target state changes before transfer commit | Version checks/locks, consistent snapshot, bounded retry and commit-time policy validation |
| Health healthy while partial evidence exists | Component fault tests; missing edge/receipt with healthy posterior ping | Probe required graph components/completeness, non-ready 503; never infer from class/DSN selection |
| Health/preview GET changes data | Before/after counts/versions or outbox drain/seed telemetry | Remove middleware/startup write triggers from GET; explicit commands; Observations never counted Decisions |
| Cold-start gating deadlock or unsafe bypass | V=0 tests; PRESEED/COLD_START passed authorizes normal action | Explicit supervised/bootstrap policy with V=0; forbid general bypass and separate service readiness from authority |
| Conservation math silently changed | Reference-policy tests, field semantics and calibration/version comparison | Preserve approved policy, surface mismatch for owner decision; no unapproved retuning or DK-default enablement |
| Synthetic/holdout/test data contaminates measured state | Population/provenance census and negative eligibility tests | Typed population/verification provenance; isolated test populations; no renamed fixture→learned migration |
| Historical receipts cannot be validated | Hash/ID/domain mismatch, no original verifier/source | Preserve and label imported prior/history; quarantine ambiguity; do not forge verification/chain |
| Old outbox replay targets wrong database | Missing graph identity or source lineage | Offline destination-bound review/migration only; no startup replay |
| Same IDs collide across domains/tenants | Collision fixtures leak neighbors or metadata updates | Composite identities; scope every alias/anchor; authorize explicit source/target traversals |
| Moving blobs to AGE mistaken for JM | Witness query requires JSON parsing/extra store/join to reconstruct links | Required actual relationships and one-Cypher path tests |
| Migrations leave lost local authority or duplicated counters | Full content/version/receipt/edge census, restart and idempotent rerun | Preserve sources, reviewed mappings, expand/migrate/verify/switch, explicit conflict disposition |
| Rollback reintroduces SQLite or loses post-cutover writes | Rollback rehearsal and operation-ledger reconciliation | Compatible code+AGE snapshot restore with writers fenced; no SQLite-primary fallback |
| Existing tests silently force SQLite/default DSN | Production subprocess identity and loaded fixture/config audit | Independent required harness; isolated legacy suites; fail on skips and target mismatch |
| Fixture removal breaks legitimate UI states | API contract and full E2E empty/unavailable/provenance checks | Implement truthful graph projection/error UX; never weaken evidence semantics for screenshots |
| Cross-domain transfer leaks data or uses incompatible geometry | Unauthorized read tests; source/target factor/category schema mismatch | Explicit reviewed mapping and authorization; conservation of both domains; deny missing mappings |
| Live connector or action runs during tests | Network/action audit and transport call counters | Inert external-action transport boundary; graph remains real; no broker/payment/order permissions |
| Credentials leak in identity/readiness artifacts | Artifact redaction tests and source-key-only config provenance | Server-issued nonsecret identity; never echo DSN or sensitive evidence in markdown/CI |
| CI becomes green through exemptions or stale artifacts | Ledger diff, expired symbol exemption, test inventory/hash mismatch | Blocking verifier; no whole-file exemptions; reviewed source-bound evidence |
| Paper/blog claim contradictions leak into acceptance | Numerical/performance claims sourced from illustrative captions | Architecture-only acceptance; preserve evidence tiers; no promised speedup/ROI or scientific superiority |
| Final live deployment not authorized | No explicit target-bound operator approval | Finish rehearsal, record blocked operational cutover; do not mutate live systems or mark DoD complete |

## 7. Definition of Done

The architecture is implemented only when ALL of the following are evidenced on the current code and schema. A completed plan, passing unit suite, [AGE] badge or 66 checked boxes alone is not sufficient.

1. **All-five identity and readiness.** Trading, Purchasing, DataOps, S2P and SOC each expose /health and /api/health with graph_backend=age, graph_connected=True, graph_name=soc_graph and the **same actual storage identity**. GraphConfig provenance, fresh connection/component checks and required evidence completeness are present. Readiness fails correctly during an AGE outage and recovers without stale fixture/default state.
2. **DG-1…DG-7 all pass automated verification.** Domain-stamped writes and collision-tested reads; only reviewed explicit cross-domain access; no raw copilot Decision-driver access; no production SQLite/memory/fixture authority, including indirect constructors, repair queues and override flags.
3. **One graph contains four traversable memory types.** Episodic, semantic, procedural and judgment data participate through actual relationships. Numerical arrays may be stored as graph snapshot payloads but cannot replace the evidence spine.
4. **Four single-traversal interactions work.** Each named operation returns verifiable connected path witnesses in one Cypher traversal; no file/SQLite/API stitch. Entity-contextualized judgment and reviewer/time provenance are included, not just one generic transfer demo.
5. **Trading centroid visible from S2P.** An authorized S2P graph query traverses to the actual Trading judgment/centroid/fingerprint version; mapping compatibility and source/target conservation are verified. Apply creates a target version and durable receipt idempotently; unauthorized/unready cases deny.
6. **Durability and verified-only learning.** Accepted score/learning/transfer bundles are atomic; failures never yield ordinary success or mutate the learner ahead of AGE. Retry/lost-ack/two-writer/restart tests pass. Pending, Observation, archived and inappropriate synthetic/holdout populations cannot inflate live V or trigger learner/evolver changes.
7. **Conservation is a deployment-time graph invariant.** V/q/coverage and versioned policy derive from graph evidence; boundary/zero-data/per-category tests pass. Degraded or unavailable evidence cannot authorize autonomous action or force GREEN. Supervised recovery is explicit and auditable, not a hidden bypass.
8. **All side stores and candidates resolved.** All 66 gaps have passing evidence; every Appendix A–F and newly discovered production candidate is fixed or proved non-authoritative/isolated. Zero OPEN production candidates. Static/import/call gates plus runtime fault tests enforce this; no deceptive literal grep count.
9. **Seed/migration evidence is complete.** Current preseed writes through the intended AGE APIs and every seeded ID/domain/receipt/link is verified in the same graph. Migrations preserve provenance, are idempotent and non-destructive to retained sources, and reconcile all memory/state—not only counts.
10. **JM reference demonstrates the target.** AGE mode is the primary architecture demonstration in jm_reference and works through trading_clone/build_your_own; shared graph traversals and restart reconstruction are tested. Offline SQLite examples are clearly separate and not used to substantiate JM compliance.
11. **CI cannot silently omit AGE.** Required jobs provision real AGE, run production-profile app paths, and fail on absent infrastructure, skip/xfail, zero collection, missing expected tests, stale evidence or expired/broad exemptions.
12. **All-five E2E passes on the AGE-backed stack.** Required graph integration asserts named evidence and consistency across panels; UI mocks remain separately identified. No spec is weakened, skipped or fixture-fed merely to obtain green.
13. **Cutover and rollback proven.** G065/G066 flags are evidence-derived for the actual target, with complete receipts/edges/learning versions and a successful AGE-backed rollback rehearsal. No hardcoded true or production-as-test exception.
14. **Operational approval respected.** Live migration/cutover is explicitly authorized and verified. Without approval the final status is “implementation/rehearsal complete; deployment blocked,” not full operational JM compliance.
15. **Handoff is reproducible.** Session state and execution/candidate ledgers contain exact tests, counts, source/config/schema fingerprints, redacted target identities, migration/rollback evidence and any residual limitations.

### Plan validation performed during this planning task

The plan is checked for exact G001–G066 ownership (one phase each), missing/out-of-range IDs, ten sequential phases, preservation of every dependency in the report including within-phase ordering, all seven requested sections, one complete prompt and verification gate per phase, and total effort = 55d. These are **document validations**, not implementation tests. The live/CI/E2E gates above remain future work.

The report's 66 remediation groups do not imply that all noisy scan hits were proven defects. Their uncertain candidates are first-class work in the disposition ledger and final closure gate. Any discovery that makes the scope materially larger must be reported and estimated rather than hidden under a passing phase number.

