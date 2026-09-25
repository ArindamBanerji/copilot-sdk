# AGE + Judgment Memory architecture compliance sweep

Date: 2026-09-22  
Scope: copilot-sdk, s2p-copilot, gen-ai-roi-demo-v4-v50, ci-platform  
Mode: read-only source audit; no git commands; no application, test, seed, migration or database mutations executed. Only this report and the requested session-state append are deliverables.

## Executive Summary

**66 remediation gaps: P1 23; P2 25; P3 7; P4 9; P5 2. The full JM shared-graph architecture is not implemented.** These are distinct remediation groups, not a count of grep matches or individual exception handlers. Groups include active defects, reachable ungated library defaults, and missing architecture/verification contracts; their descriptions distinguish those cases. The appendices retain additional uncertain candidates rather than treating them as cleared.

**Which copilots are NOT on AGE?** Source does not support saying that an entire copilot is simply “off AGE.” Current production wiring in all five selects AGE for core Decision storage. All five nevertheless have non-AGE runtime memory paths. DataOps additionally has a separate failed topology path in the user-observed deployment. Purchasing's missing graph fields on /health coexist with graph fields on /api/health. S2P's minimal health says nothing reliable about its configured backend. SOC uses AGE, but remains noncompliant with the strict GraphStore-only requirement and has numerous swallowed failures.

The highest-risk defects are normal scoring success after failed Decision persistence (G001), learning memory advancing beyond durable artifacts (G003/G006), demo pattern application by the legacy transfer endpoint (G005), incomplete Decision relationships (G007), DataOps fixture substitution above a fail-closed client (G011/G012), and SOC's history guard returning proceed after an exception (G019). SQLite K-utility stores run in **all five** apps; SQLite cross-app signals run in Trading, Purchasing and DataOps. AGE state blobs, file-based fingerprints, local episode lists and synthetic platform panels do not satisfy a single-traversal memory-interaction requirement.

Important corrections to historical assumptions:

- The current scorer does **not** silently default to SQLite in ordinary production construction: it requires an injected store and rejects concrete SQLite/InMemory stores. Explicit factory/wrapper/default-constructor escape paths remain.
- Current SOC scorer initialization injects an AGE GraphStore adapter. The old “SOC scorer is always in-memory” finding is stale.
- Current S2P startup shares its selected GraphStore with enrichment and uses graph proposal/budget/autonomy components. The old “every S2P route still uses a separate Neo4j driver” claim is not supported.
- Current HTTP preseed calls score/learn endpoints; it does **not** directly seed SQLite. Other legacy seed/bundle/example paths still use local stores.
- DataOps graph_source=fixture is an ambiguous health label: its AGE-required graph client generally raises 503 rather than serving fixtures. Higher-level investigation and the special abstention-alert route do reintroduce fixture behavior.
- Demo-labelled results are not necessarily falsely claimed to be live. They still leave the production shared-memory capability unimplemented when always mounted or used as authoritative input.

### Evidence and confidence boundary

The five observed health results in the request are **user-supplied observations**, not new live measurements by this audit. No live endpoint calls were made: some nominal GET/health paths trigger startup seeding/replay, and strict read-only analysis takes precedence. No outage, restart, E2E, transaction or migration experiments were run. Causal explanations below are source-backed mechanisms, not a claim to have reproduced the supplied runtime state.

The full jm_paper_draft_v13.md was not available at the searched location; §3.4 is assessed against the quotation supplied in the request. The local design requirements in copilot-sdk/docs/design/age_unification_gaps_v1_1.md were read, but historical findings there were checked against current source rather than copied.

“Exhaustive” here means untruncated repository-wide candidate enumeration, tracing the requested runtime paths, and retaining uncertain matches. It is **not** a mathematical proof that arbitrary dynamic Python dispatch has no other bypass. Appendices explicitly distinguish confirmed findings, intentional test/demo/operator paths, and candidates requiring call-site/outage verification. Uncertain candidates are not silently declared compliant.

## Architecture Compliance Matrix

✅ = the inspected canonical path meets this goal; ❌ = a concrete violation exists; ⚠️ = partial, residual escape paths, or deployment identity not proved. A ✅ for DG-5 does not certify every dynamically supplied graph query.

| Copilot | DG-1 | DG-2 | DG-3 | DG-4 | DG-5 | DG-6 | DG-7 | JM §3.4 |
|---|---|---|---|---|---|---|---|---|
| Trading | ❌ | ⚠️ | ❌ | ⚠️ | ✅ | ⚠️ | ❌ | ❌ |
| Purchasing | ❌ | ⚠️ | ❌ | ⚠️ | ✅ | ⚠️ | ❌ | ❌ |
| DataOps | ❌ | ❌ | ❌ | ⚠️ | ✅ | ⚠️ | ❌ | ❌ |
| S2P | ❌ | ⚠️ | ❌ | ⚠️ | ✅ | ⚠️ | ❌ | ❌ |
| SOC | ❌ | ⚠️ | ❌ | ❌ | ✅ | ⚠️ | ❌ | ❌ |

DG-1 is scored using the requested broad criterion that production SQLite judgment/learning paths count, even where the narrower Decision CRUD protocol is AGE-backed. Connector transport caches and deterministic bootstrap constants are not automatically Decision-store violations; their use as memory/evidence is assessed separately. DG-6 requires one database **and** graph, not merely identical graph-name strings.

### Requirement-to-capability mapping

| JM interaction | Existing capability | Missing production integration |
|---|---|---|
| Episodic × judgment | Decision/Outcome/entity links, domain-scoped GraphStore reads | Trading import episodes, DataOps holdout/process history and S2P supplier events remain local; failed links and surrogate links defeat ordinary traversal |
| Semantic × judgment | AGE query_context and domain entity topology | Local fixture evidence, independent DataOps topology config, unscoped roots/intermediates, signals in SQLite |
| Procedural × judgment | Evolution, promotion, posterior and governance graph operations | K utilities and promotion defaults outside graph; JSON payload snapshots without constituent evidence relationships; best-effort learning writes |
| Judgment × judgment, cross-domain | Real AGE TransferPattern/domain edges and typed source/target operations | JSON fingerprint discovery, optional in-memory registry, generated fallback patterns, synthetic platform projections; no required end-to-end traversal contract |

## Audit Coverage: Requested Steps 1–14

The requested First 50/40/20 sampling limits were intentionally removed. Matches were collected from all four repositories; dependency, bytecode and test trees were separated from runtime evidence. A broad Python inventory enumerated 2,506 files: copilot-sdk 1,377; s2p-copilot 310; SOC 730; ci-platform 89. These counts include tests/tooling before classification, not 2,506 production modules.

| Step | Completed analysis and evidence |
|---|---|
| 1 SQLite | Untruncated sqlite/SQLite/.db/sqlite3 scan; actual runtime stores, false .db imports, local APIs, examples and operator tools classified in Appendix A |
| 2 Fixture/fallback | Untruncated fixture/fallback/default/static JSON/sample/demo/mock scan; runtime candidate index in Appendix B, plus explicit proven paths below |
| 3 Graph exceptions | AST graph/store/connect/learning-context candidate scan: 877 handlers. All retained in Appendix C, including rethrows/explicit unavailable and conditional-raise handlers |
| 4 Direct imports | All direct psycopg/neo4j/age import matches retained; legitimate adapter/operator uses separated from SOC raw posterior API |
| 5 Startup | Full Trading/Purchasing/DataOps/S2P main.py read; SOC startup/health and graph/scorer initialization read beyond the requested first 150 lines |
| 6 Protocol | GraphStore, GraphTraversalStore, ProtocolV2GraphStore and L5LearningStore definitions, factory, scorer and per-app injection/call sites traced |
| 7 Health | Both aliases, graph-status builders, topology status and launcher readiness checked statically for all five |
| 8 Preseed | HTTP all-copilot runner, demo.py dispatch, legacy DemoPreseed and SQLite bundle restore traced separately |
| 9 Reference apps | JM reference, trading clone and build-your-own run/engine implementations inspected |
| 10 Tests | conftest overrides, real AGE fixtures/skips, validator/allowlist and all four main CI workflows inspected |
| 11 Learning | Decision writes, learn conservation/centroids/DK/receipts, utility K, startup restore, evolution, promotion and posterior paths traced |
| 12 Cross-domain | Graph transfer support compared with file fingerprints, memory registry, legacy execute, cross-signals and synthetic discovery/platform panels |
| 13 E2E | Current four named Trading specs, related components/API routing and backend projections inspected; no tests run or changed |
| 14 Report/session | This comprehensive report and the requested append-only session entry; no source changes |

## Per-Copilot Detailed Findings

### Trading

Startup: main.py:175/181 resolves GraphConfig, :190 enforces shared graph, :197 constructs via factory; :386–408 selects/injects the active store. Production AGE selection/construction failure is not replaced by SQLite; :188 is a test-profile path. Later score/learn failures are suppressed by shared code. Expected graph_name is soc_graph through GraphConfig; actual database identity was not probed.

| Goal | Status and evidence | Required change |
|---|---|---|
| DG-1 | ❌ Canonical scoring uses GraphStore at main.py:404; K utility :595 and cross-signal store :584 use SQLite; journal context_router.py:531 and journal.py:583 use JSON | G024/G026/G029; persist all judgment-side state in graph |
| DG-2 | ⚠️ main.py:181 uses GraphConfig; graph_status.py:381 infers status but /health lacks fresh connection/config-source proof | G043/G049; use one resolved destination and status contract |
| DG-3 | ❌ scorer.py:440/460 returns success on write failure; Trading evidence/trust catches and transfer behavior add gaps | G001–G006/G020/G021; fail or explicitly mark unavailable/pending |
| DG-4 | ⚠️ Canonical reads pass trading; shared query_context root/intermediate scoping and arbitrary metadata IDs are unresolved escape paths | G029/G040; scope every alias/anchor and validate IDs |
| DG-5 | ✅ scorer.py:409 adds domain; AGE writer stamps domain. Raw metadata side files are not canonical graph Decision writes | Preserve mandatory domain in the consolidated writer and test every write entry point |
| DG-6 | ⚠️ shared guard selects soc_graph, but same DSN is not proved and cross-domain files/SQLite remain | G026/G043/G044/G047 |
| DG-7 | ❌ Memory trades, JSON analytics/journal/promotion/rejections and SQLite K/signals remain | G023–G026/G029–G032 |
| JM §3.4 | ❌ Operational episodes and procedural authority cannot all be joined to judgments by one graph traversal | Complete G047 after moving the contributing stores |

Health: /health main.py:714 has graph_backend (:726) and graph_status (:727), but “ok” is not a fresh AGE readiness proof. cutover_ready/product_claim_allowed are independent, intentionally incomplete gates (G065), not evidence of SQLite scoring.

### Purchasing

Startup: main.py:224 loads typed config; :512–541 selects/injects active AGE; shared factory failures are not silently converted to SQLite except explicit test construction. Evolution uses create_variant_store with the selected store (:555). GraphProof/Outcome ledgers are active when AGE capabilities exist; capability-based SQLite fallbacks still exist in purchasing_control.py. Default graph is soc_graph.

| Goal | Status and evidence | Required change |
|---|---|---|
| DG-1 | ❌ Canonical scorer is graph-injected; main.py:849/872 create SQLite signals/K and purchasing_control.py:159/160 has local-ledger fallbacks | G024/G026/G028 |
| DG-2 | ⚠️ Startup uses GraphConfig; /api/health :624 contains fields, /health :960 does not | G043/G050; unify aliases and expose config provenance |
| DG-3 | ❌ Shared write/learning catches plus main.py:416, context_router.py:82, evidence.py:182/193, trust_router.py:163 hide failures | G001–G004/G013 |
| DG-4 | ⚠️ Canonical reads bind purchasing; inherited traversal/metadata/default API paths are not a universal scoped boundary | G040/G042; domain collision and foreign-ID tests |
| DG-5 | ✅ Canonical scorer/AGE writer includes explicit purchasing domain | Keep mandatory domain and verify the graph result after writes |
| DG-6 | ⚠️ soc_graph intended; destination agreement and cross-type traversal not demonstrated | G026/G043/G047 |
| DG-7 | ❌ SQLite K/signals, fallback ledgers, orders/par/waste files and always-mounted demo disruption/payment/audit services | G024/G026/G028/G033 |
| JM §3.4 | ❌ Operational and audit evidence remain separate from graph judgments | Link orders/suppliers/procedures/receipts; replace hard-coded audit proof |

The no-graph-health observation is correct for /health, not /api/health. Demo/chain discovery routes that now have explicit demo gating must not be misreported as unconditional live fallback. Demo-labelled payment/audit services remain architecture gaps even without deception about their provenance.

### DataOps

Startup: main.py:667/668 resolves/selects the Decision store and :712 injects it into the scorer. Independently, :679 creates DataOpsGraphClient. graph_queries.py:48–68 alters the process environment temporarily while resolving a separate GraphConfig; :100–134 catches topology initialization failure. _age_required (:115) makes normal graph queries raise 503 when AGE is required. Therefore “fixture” health does not prove the Decision store is SQLite, nor that every query actually serves fixtures. Default graph is soc_graph when consistently resolved.

| Goal | Status and evidence | Required change |
|---|---|---|
| DG-1 | ❌ Core Decisions use selected GraphStore; dataops_governance.py:30/87/114 persists holdout judgments in SQLite; K/signals are local too | G024/G026/G027 |
| DG-2 | ❌ Separate topology resolution mutates environment and can lose generic DSN precedence; health describes only topology | G043/G051; inject the one resolved config/store |
| DG-3 | ❌ Topology constructor suppresses failure; query layer mostly fails closed, but investigation_patterns.py:352/365/378 and context_router.py:1423 bypass it | G011/G012/G022; do not catch-and-fixture above 503 |
| DG-4 | ⚠️ Decision reads bind dataops; inherited entity traversal and local holdout receipt scope are not universally enforced | G027/G040 |
| DG-5 | ✅ Canonical scorer/AGE writer includes dataops; demo alert-metadata correctly stamps domain/provenance at context_router.py:1695 | Preserve explicit domain; migrating holdouts must also include it |
| DG-6 | ⚠️ Core intends soc_graph; observed topology disconnected and separate config can diverge | G043/G051; prove database identity and required topology on startup |
| DG-7 | ❌ Holdout/K/signal SQLite, process fixtures, injected abstention alert, enterprise evidence files and object() discovery remain | G011/G012/G024/G026/G027/G034/G047/G048 |
| JM §3.4 | ❌ Topology, enterprise evidence, holdout judgments and discovery are not one reliable traversable memory | G047 plus graph-native ingestion and complete evidence links |

Health: main.py:1054 returns status=error if graph_source is not graph, and fields graph_connected/source (:1065/1066), but not the required graph_backend/graph_status or Decision-store readiness. The label is misleading and the HTTP response itself can still be 200. Alert metadata POST/GET (:1675/1702) now requires explicit demo mode; this is a correctly gated file path, not an ungated production write.

### S2P

Startup: main.py:216 builds with GraphConfig (:230), shared guard (:231), factory (:238), scorer (:256). Selected store is created at :306–312 and reused for enrichment (:410–415); graph proposals (:383), budget (:314) and autonomy (:407) are present. These are genuine improvements. Production AGE construction failure raises; warmup reads (:574/586) are caught. Default graph is soc_graph.

| Goal | Status and evidence | Required change |
|---|---|---|
| DG-1 | ❌ Current canonical scorer/proposal/enrichment stores are graph-backed, but main.py:46/499 opens SQLite K; supplier accumulator retains judgment-relevant events outside graph | G024/G025/G035 |
| DG-2 | ⚠️ Typed startup config works; /health and /api/health :590–593 expose no graph information | G043/G052 |
| DG-3 | ❌ s2p.py learning catches and s2p_demo_beats.py:49 turn errors into best-effort/default results | G001–G004/G014/G015 |
| DG-4 | ⚠️ S2PGraphReader supplies domain on canonical calls; main.py:358 TypeError compatibility retry calls a getter without domain; inherited traversal holes remain | Remove no-domain compatibility retries in production; G040 |
| DG-5 | ✅ Canonical scorer/AGE writer includes s2p explicitly | Preserve it for all migrated supplier/receipt relationships |
| DG-6 | ⚠️ Active/enrichment now share store and intended soc_graph; actual shared DB and interaction coverage not proved | G043/G047 |
| DG-7 | ❌ SQLite K, supplier memory/fixtures, synthetic invoice/PVG/context paths and latent ProposalService SQLite default remain | G024/G035/G036/G045/G048 |
| JM §3.4 | ❌ Supplier episodes and acquired evidence do not all participate in the shared graph with judgment/procedure state | G025/G035/G047/G048 |

No blanket claim of active Neo4j is justified: the direct driver import found under S2P is migration/s2p_entity_migration.py:493 (operator tooling). Existing graph-backed receipt/proposal components should be extended, not replaced with another storage abstraction.

### SOC

Startup: db/graph_client.py:27 resolves GraphConfig, :29 requires shared graph, :37 rejects non-AGE and :49 creates AGEClient; :54 fails startup on initialization failure. main.py:311/327 propagates AGE bootstrap failure. services/gae_state.py:279–296 creates the shared GraphStore adapter and passes it into SOCCompoundingScorerAdapter; it rejects SQLite-primary dual_write. Default graph is soc_graph. This is the strongest AGE integration, but not a compliant reference for every requirement.

| Goal | Status and evidence | Required change |
|---|---|---|
| DG-1 | ❌ Many production Decision reads/writes call AGEClient.run_query directly (triage.py:1119/1795/2104); main.py:200/249 opens SQLite K | G024/G041; centralize the protocol boundary |
| DG-2 | ⚠️ Graph client and normal posterior use typed config; posterior_store.py:53 raw-DSN API remains; health does not expose graph identity/source | G043/G046/G053 |
| DG-3 | ❌ Numerous read/write catches; variant_generator.py:86 returns proceed; soc.py:592 serves static metric material | G016–G019 and Appendix C |
| DG-4 | ❌ domains/soc/campaigns.py:490 has unscoped target and related Decision aliases; graph_explorer.py:117/138 accepts arbitrary read-only Cypher | G040; scope/authorize every Decision access including explorer |
| DG-5 | ✅ Inspected live triage CREATEs explicitly set domain='soc' (:1121/:1801), as do canonical AGE writes | Preserve this; dynamic raw-query APIs prevent universal static certification |
| DG-6 | ⚠️ soc_graph configured and user reports healthy; actual same DB across apps and complete cross-type paths still unproved | G043/G047 |
| DG-7 | ❌ SQLite K, latent authority local defaults, static platform projections and best-effort/local snapshot mechanisms remain | G024/G037/G045/G046 |
| JM §3.4 | ❌ Rich AGE topology exists, but procedural/episodic inputs and cross-copilot platform panels are not uniformly shared-graph interactions | G038/G041/G047/G048 |

Normal PosteriorStoreGraph(GraphConfig) uses GraphStore and is not the same as the raw psycopg compatibility branch. Authority initialization injects GraphPromotionStore at authority_ladder.py:335; :341 remains a dangerous ungated fallback when no manager was initialized.

## Infrastructure Gaps

### GraphStore usage and the actual boundary

copilot-sdk/copilot_sdk/graph/protocol.py defines GraphStore (:16), GraphTraversalStore (:238), ProtocolV2GraphStore (:264) and L5LearningStore (:464). The five canonical scoring paths have graph injection; protocol existence alone does not constrain raw queries, local side stores, default constructors or exception behavior. SOC is the largest raw-Decision-query bypass. DataOps topology has its own AGE client. SDK framework copies expose legacy run_query-style consumers. Driver imports inside ci-platform's AGE adapter are legitimate implementation details, not copilot violations; migration/preflight imports are a separate operator boundary.

GraphConfig defaults to AGE/expected AGE and soc_graph (graph_config.py:213–225). Per-domain aliases/config overrides and profile guards matter. A graph_name check cannot certify identical host/database/schema destination; expose a redacted resolved identity and configuration key provenance, not credentials. The existing broad source tag env/file/default is less useful than identifying which setting won.

### Preseed and migration

The current preseed_all_copilots runner invokes live APIs at :400/407 and :583/590. If the server's selected store is AGE and writes are durable, those Decisions land in AGE. G001 means HTTP success alone still does not prove that. Check :229 merely tests health reachability; :630 verification is not a complete graph census.

demo.py:936 dispatches SDK/SOC/S2P seed jobs (:941–944), but its older deterministic path (:1472–1480) uses DemoPreseed, now conflicting with the scorer's production store guard. SQLite bundle restoration is separately local-only. Historical local decisions therefore need explicit migration; this is not evidence that the current HTTP preseed always writes SQLite. After migration verify all memory types, IDs, receipts, links, domain partitions and learned-state versions, not only row counts.

### Reference applications

JM reference explicitly selects SQLite/test mode; Trading clone delegates; build-your-own has a SQLite engine. They are useful offline examples but do not demonstrate §3.4. Add a runnable shared-AGE mode with one interaction of each memory type and cross-domain traversal, retaining the offline examples with clear non-production labels.

### Tests and CI

Mocks/local stores are appropriate for unit tests, insufficient for an AGE compliance gate. Real AGE tests exist in SDK, ci-platform, S2P and SOC, but availability-based skips let the important failures disappear. The four inspected ci.yml workflows run tests without provisioning a required AGE service. Static validator weaknesses are enumerated in G062. The fix is a required graph job that fails on missing infrastructure or skipped graph tests—not banning useful unit mocks.

### Health endpoint contract

| App | Current endpoint behavior | Required missing evidence |
|---|---|---|
| Trading | /health has graph_backend/status; backend inferred and flags incomplete | Fresh read, resolved graph identity and config key source, durable learning/receipt completeness |
| Purchasing | /api/health has graph fields, /health lacks them | Identical aliases plus fresh read/identity/source |
| DataOps | Topology source/connected and error status; no core store report | Decision + topology component health, unambiguous unavailable, unified config |
| S2P | Both aliases minimal static health | Entire canonical graph contract |
| SOC | components.graph derived through posterior health | Backend/name/source and required Decision/topology/learning checks |
| Launcher | [AGE] from requested requirement; permissive health wait | Actual verified backend and cross-app identity agreement |

A safe readiness response should include graph_backend, graph_status.connected, graph_status.graph_name, redacted database identity, dsn_source/config_source, domain, last successful check, last error category, pending/failed/abandoned artifact counts, and learning restore/version status. Keep a lightweight liveness endpoint separate. Readiness failure must be machine-actionable (normally 503), and the check itself must never seed or replay data.

## Silent Fallback Inventory (DG-3 Violations)

The confirmed families below are the P1 groups in the fix plan. Logging an error does not satisfy DG-3 when the caller still receives ordinary success, empty evidence, a neutral phase or fixture-derived data. “Unavailable/deny” responses are distinguished from silent success: they may fail the strict raise/readiness contract without authorizing an unsafe action.

| Family | Exact failure sites | Substitute / consequence |
|---|---|---|
| Core scoring and failure queue | scorer.py:440,460,185,1257 | ScoreResult returned after failed Decision write; local SQLite queue may also fail |
| Shared learning/artifact persistence | scorer.py:1332,1386,1424,1515,1525,1563,1650,1725,2456,2525,2603,2624; scoring_router.py:600,605,629,716,740,761; dk_persistence.py:270 | Partial receipts/centroids/conservation/DK and in-memory advancement |
| Restore/phase/RL | startup_restore.py:155,169,249; scorer.py:363,1895,1906; ci_platform/strategy/two_phase_strategy.py:31,47 | Bootstrap/default A/alpha zero or disabled RL instead of verified state |
| Warm-start | scorer.py:1983,2034,2060 | In-memory transfer remains applied despite conservation/pattern/checkpoint error |
| Graph topology write | age_graph_store.py:792,810 | Decision success without domain/FactorVector topology |
| AGE count helpers | age_client.py:660,679 (see Appendix C for each handler) | Zero counts mask read failure |
| SDK copied framework | decision_history.py:59; composite_gate.py:120; similar_cases_base.py:99; provenance.py:326; shadow_mode.py:106; checkpoint.py:98 | [], None, default counts/accuracy; SOC/S2P corresponding sites retained in Appendix C |
| Trading | trader_profiles.py:85; trust_analysis.py:173; claim_gate.py:97; evidence_providers.py:83; services/cohort_status.py:158 | Missing/partial/stale evidence presented as ordinary projection |
| Purchasing | main.py:416; context_router.py:82; routers/evidence.py:182,193; trust_router.py:163; purchasing_control.py:70; services/cohort_status.py:206 | Empty variants/evidence/counts; omitted cohorts |
| DataOps | investigation_patterns.py:352,365,378; context_router.py:1423; ae_router.py:47; services/cohort_status.py:149 | Fixture pipeline/blast/recurrence/alert substitution; empty evolution/cohort state |
| S2P | s2p_demo_beats.py:49; s2p_governance.py:38; s2p_evidence.py:206,220; s2p_context_builder.py:271; centroid_explorer.py:208 | Empty/unknown evidence and outage mistaken for day-zero |
| S2P learning | routers/s2p.py:831,842,866,899,921,970,1004,1063,1491,1832,2352,2469,2493,2512,2540 | Best-effort learning/links/receipts and substituted counts/snapshots |
| SOC metric/history | routers/soc.py:592,2164,2200,2261,2286; triage.py:3561; learning_health.py:1026,1036,1063,1081 | Static metric data, empty graph and apparent accumulating state |
| SOC context/audit/learning | triage.py:1242,1473,2151,2639,2882; reconvergence_logger.py:106,178; snapshots.py:68; learning_health.py:725 | Secondary judgment artifacts and lineage omitted |
| SOC investigation | services/investigation_patterns.py:120,133 | Bounded graph read -> []; context fallback -> read_error; source acquisition may be partial |
| SOC guard | services/variant_generator.py:86 | action=proceed after history exception |
| Enterprise evidence filtering | copilot_sdk/di/query_providers.py:178 | ProviderUnavailableError -> empty allowed-ID set; upstream read helper correctly raises at :104 |
| Transfer projection/reset | transfer_router.py:214,654 and checkpoint helper :699 onward | Partial impact sum, False reset and optional checkpoint after transfer |

Complete file paths and additional sites are in the fix plan and Appendix C. The AST inventory includes conditional handlers with a raise because a raise anywhere in a handler does **not** prove all branches raise (DataOps alert_detail is the concrete example).

### Exceptions that must NOT automatically be called silent AGE fallbacks

- AGEClient warm-connection retry (age_client.py:212) remains an AGE retry, not substitution with SQLite/fixtures.
- GraphConfig validation/test-profile branches intentionally select test/development stores. They become defects only when production can enter them without an explicit safe boundary.
- DataOps _run_graph AGE-required error handling returns/raises 503; the higher-level catches listed above are the violation.
- Health probes may catch and return connected=false/unavailable. That is acceptable diagnostic behavior if readiness fails and no authoritative data is fabricated.
- Safety gates returning RED/UNKNOWN deny rather than approve. Preserve denial, but expose unavailable separately and ensure consumers never count these values as measured conservation.
- Parsing serialized graph properties with json.loads is not file-backed fixture storage. Likewise a Python return {} for an absent optional field is not necessarily an AGE exception handler.
- SQLite lock retries, JSON parse failures, optional imports and remote connector failures are not automatically graph failures. Appendix C retains these lexical candidates with their outcomes, not a false assertion that all 877 are DG-3 violations.

## Non-Unified Path Inventory (DG-7 Violations)

### Connector and semantic-source fallback boundary

External connector fallbacks are also in scope, but must not be mislabeled as an AGE-driver failure. DataOps startup at `copilot-sdk/apps/dataops/backend/app/main.py:217` through its connector initialization branches can select mock Snowflake/dbt/Airflow sources; `copilot-sdk/apps/dataops/backend/app/enterprise_router.py:116,202,211` explicitly constructs fixture SAP/Celonis alternatives. The shared implementations are `ci-platform/ci_platform/connectors/sap.py` and `ci-platform/ci_platform/connectors/celonis.py`; Purchasing also retains `copilot-sdk/apps/purchasing/backend/app/connectors/mock_qbo.py` and the QBO selector in its startup/router code. Their complete matching sites are retained in Appendix B.

These are semantic-memory integration candidates under G033/G034/G048, not extra independently counted findings. A connector can legitimately be an external ingestion source. It does **not** satisfy JM merely because its result is later passed to a graph-backed scorer. Required follow-up: trace each production caller, forbid automatic fixture substitution for required live evidence, preserve source/error/age-of-data, ingest the observation into AGE, and link the consumed observation version to the resulting Decision/receipt. An explicitly demo-gated mock or non-authoritative transport cache can remain outside the graph. Do not count mock connection health as live enterprise readiness.

### Authoritative and potentially authoritative state

| State / path | Production reachability and role | Evidence / fixes |
|---|---|---|
| K utilities | All five startup paths create SQLite; procedural/acquisition utility outside graph | G024/G025 |
| Failed artifacts | Shared scorer uses a separate SQLite outbox (plus other legacy outbox implementations) | G001–G003; Appendix A differentiates repair queue from canonical store |
| Shared cross-app signals | Trading/Purchasing/DataOps explicitly mount shared_signals.db | G026 |
| DataOps holdout judgments | SQLite decisions/factors/scores/verdict receipts | G027 |
| Purchasing proof/outcome/twin fallback | Dormant with full AGE adapter, activated by missing capability without production guard | G028 |
| Trading metadata/journal | Ungated JSON judgment context and verification projection | G029 |
| Trading imported episodes | Process-local trade list feeds trust/pattern/safety views | G030 |
| Trading promotions | Multiple JSON/memory authority paths mounted | G031 |
| Trading analytics/rejections | JSON cache and persisted preseed evolution log used by UI projections | G023/G032 |
| Purchasing operational context | Orders/par/waste/report files and always-mounted demo analysis/audit services | G033 |
| DataOps context/audit | Local process/schema/timeline/signals/fixture audit projections | G034 |
| DataOps demonstration pollution | DI-ABSTENTION-001 injected into graph-live alert results; exception substitute | G012 |
| S2P supplier episodes | Global memory plus fixture history blend | G035 |
| S2P semantic/simulation inputs | Synthetic invoices, PVG/preview and neutral-factor branches | G036; distinguish isolated preview from authoritative state |
| SOC platform cross-domain story | Static JSON platform/chain/transfer summaries | G037 |
| AGE blob state | Same database, but not fully traversable linked memory | G038 |
| Surrogate entity links | Graph node with ID fields instead of a traversable relationship | G039 |
| Raw SOC Decision access | AGE-backed but outside GraphStore | G041 |
| File fingerprints | Shared graph discovery still depends on JSON export directory | G044 |
| Reusable API local defaults | Promotion/pilot/proposal/authority SQLite; registry/evolver memory/JSON | G045 |
| Raw posterior compatibility | SQL state behind legacy raw-DSN constructor, not normal typed configuration | G046 |
| Discovery and investigation | object() discovery, hard-coded cross-domain records, fixture evidence providers | G047/G048 |
| Offline tooling/examples | SQLite bundles, examples, seed artifacts and backup paths | G057–G059/G063; do not mistake them for normal AGE web scoring |

Appendix A lists **every SQLite-scan hit by file and line**; Appendix B does the same for fixtures and fallback candidates; Appendix D adds memory/JSON-write sites. This includes false positives and operator/test/demo-only paths to make the exclusions auditable. Unclassified runtime candidates are explicitly OPEN, not exonerated. File parsers, model presets, exports and caches can remain outside AGE only if they are not authoritative memory and a graph outage never promotes them to that role.

## E2E Impact Analysis

No failing traces or current E2E run were provided or executed. The following separates demonstrated dependency defects from plausible failure mechanisms and spec assumptions. It does not assign a historical test failure to a cause without reproduction.

| Surface/spec | Actual backend state | Graph-related mechanism | Spec/UI issue or limitation |
|---|---|---|---|
| conservation-breakdown | /api/context/conservation-breakdown; Trading context_router.py:426/430 uses process-local imported trades and scorer state; global /api/conservation/status is separate authority | AGE preseed does not populate import memory; write/restore failures can change global state while proxy data stays empty | Current spec :34–39 explicitly accepts populated, unavailable OR empty. Passing therefore does not demonstrate AGE health; panel is labelled simplified proxy |
| day-zero | Shared DayZeroPanel fetches /api/health and /api/conservation/status; DayZeroCard fetches /api/trading/measurement-state | Swallowed reads/count defaults can manufacture “instrument/accumulating”; minimal health aliases cannot prove graph readiness | Current day-zero.spec :33/36/48 mocks these exact three sources. **The measurement-state alias mock is not an established bug**: the inspected DayZeroCard actually uses that route. beforeEach :4 checks a hard-coded backend and can skip |
| trust-radar | /api/context/trust-analysis (:393/394) combines imported-memory trades with scorer/DK weights | AGE-only seed can leave memory episodes absent; failed graph-derived profile reads may look like insufficient data | Spec requires 10 factor rows (:127) and no “error/unavailable” in a full walkthrough (:242); this is incompatible with an outage scenario unless deliberately seeded/healthy. It is not evidence that all UI failures are graph failures |
| rejection-moment | Component fetches both evolution summary and rejection summary; local evolution_log.json also feeds Trading summaries/tab state | Graph evolution, local log and cached tab projection can disagree; preseed “learned” fixture labels are a concrete provenance bug | new-surfaces :12–18 largely tests rendered structure, not durable rejection evidence. Displayed counters need a source/version assertion |
| measurement-state/new-surfaces | /api/self/diagnostics, /api/conservation/status, /api/self/transfers, /api/self/centroid-history | Conservation/centroid/receipt restore gaps and success-on-write-error can produce inconsistent trajectories across these endpoints | Several requests hard-code 127.0.0.1:8010. Most assertions check shape or HTTP 200, not source, graph identity or evidence completeness |

Frontend DayZeroPanel itself resets to a default instrument state on fetch error while also setting an error (copilot_sdk/frontend/DayZeroPanel.tsx:97–103). This is not proof of a silent backend fallback, but the rendered availability must be tested so default labels do not become measured evidence.

Required verification after fixes:

1. UI-only deterministic tests retain route mocks and do not claim AGE integration.
2. A required integration suite seeds named AGE episodes/Decisions/outcomes/receipts, reopens each app and checks the same IDs and learning version across all panels.
3. Stop or fault the disposable AGE service; readiness fails, APIs show unavailable, no score/learn/transfer returns ordinary success, and no panel upgrades fixtures to live/learned evidence.
4. Recover AGE; verify no stale default/empty cache survives and no duplicate outcomes/transfer artifacts appear.
5. Domain collision fixtures use the same entity/decision-like identifier in different domains to detect unscoped roots and joins.

## Prioritized Fix Plan

Priorities follow the requested ordering. Estimates are **rough implementation LOC**, excluding migration data, generated artifacts and most tests; they are planning ranges expressed as a central estimate, not delivery promises. Shared dependencies may be implemented first even when their category is P2/P4. An item is complete only when its acceptance tests pass against real AGE and its residual candidate sites are disposed of.


### P1 — Silent wrong-data / failure semantics

#### G001 — Scoring acknowledges failed Decision persistence

- Functions / construction points: `scorer.py:score`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/scoring/scorer.py:437,440,453,460,465`.
- Current behavior: score() catches both governed and ordinary write failures, queues if possible, then returns a normal ScoreResult and decision ID.
- Change: Make persisted Decision + required receipt the success boundary; propagate GraphUnavailable/PersistenceError to a 503. Do not expose an unpersisted ID as an accepted decision.
- Estimated implementation: ~80 LOC. Dependencies: None.

#### G002 — SQLite failure outbox can itself disappear; replay identity is incomplete

- Functions / construction points: `scorer.py:__init__`, `scorer.py:_record_persistence_failure`, `persistence_outbox.py:__init__`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/scoring/scorer.py:178,185,1246,1253,1257`; `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:46,51,57,65,116`.
- Current behavior: Outbox construction/enqueue errors are logged and ignored. Queue lives under domain only (or temp directory), stores no target database/graph identity, and abandons entries after ten retries.
- Change: Do not substitute it for authoritative success. Make pending/error state explicit; bind any approved repair queue to domain + graph/database identity + schema, expose abandoned entries, and require deliberate replay into the same destination.
- Estimated implementation: ~180 LOC. Dependencies: G001.

#### G003 — Shared learning succeeds while artifacts fail

- Functions / construction points: `scorer.py:_persist_conservation_snapshot`, `scorer.py:_persist_learning_artifacts`, `scorer.py:capture_existing_state`, `scorer.py:_persist_evidence_receipt`, `scorer.py:_persist_fingerprint`, `scorer.py:_save_centroids_checkpoint`, `scorer.py:_maybe_archive`, `scorer.py:_run_evolution`, `scorer.py:_evolution_conservation_state`, `scoring_router.py:_persist_conservation_state_l5_locked`, `scoring_router.py:_persist_centroid_l5`, `scoring_router.py:_read_centroid_for_l5`, `dk_persistence.py:persist_dk_after_reestimate`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/scoring/scorer.py:1332,1386,1424,1515,1525,1563,1650,1725,2456,2525,2603,2624`; `copilot-sdk/copilot_sdk/backend/scoring_router.py:600,605,629,716,740,761`; `copilot-sdk/copilot_sdk/scoring/dk_persistence.py:270`.
- Current behavior: Conservation, receipts, centroids, fingerprints, archives, and evolution persistence have catch-and-continue paths; memory can move beyond graph state.
- Change: Define one versioned learn transaction/checkpoint, commit artifacts and outcome together, publish memory only after commit, and return a failed/pending result on any required artifact error.
- Estimated implementation: ~500 LOC. Dependencies: G001,G002,G008.

#### G004 — Restore and phase failures look like bootstrap/no learning

- Functions / construction points: `startup_restore.py:_restore_centroids`, `startup_restore.py:_restore_conservation`, `scorer.py:from_preset`, `scorer.py:get_phase`, `scorer.py:get_alpha`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/scoring/startup_restore.py:155,169,249`; `copilot-sdk/copilot_sdk/scoring/scorer.py:363,1895,1906`.
- Current behavior: Restore catches retain bootstrap/error state; phase/alpha exceptions return A/0; RL creation failure disables learning. Error and genuinely empty graph are conflated by consumers.
- Change: Permit cold bootstrap only after a successful empty graph read. Fail readiness on restore failure and expose learning-component readiness separately.
- Estimated implementation: ~150 LOC. Dependencies: G003.

#### G005 — Legacy transfer executes generated demo patterns

- Functions / construction points: `transfer_router.py:create_transfer_router`, `transfer_router.py:transfer_execute`, `transfer_router.py:_patterns_for_execute`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/backend/transfer_router.py:109,136,163,594,613`.
- Current behavior: _patterns_for_execute falls back to _demo_patterns_for_mapping without a demo-profile guard; /execute can apply them to the live scorer after a real GREEN check.
- Change: Require persisted AGE source patterns and evidence; no match means no transfer. Move generated patterns into a separate explicit demo/test endpoint and prohibit production mutation from that provenance.
- Estimated implementation: ~100 LOC. Dependencies: None.

#### G006 — Warm-start mutates centroids before graph evidence is durable

- Functions / construction points: `scorer.py:warm_start`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/scoring/scorer.py:1963,1983,2034,2060,2068`.
- Current behavior: In-memory centroids change before conservation lookup, pattern emission, and checkpoint persistence; failures are logged, yet applied remains positive.
- Change: Validate source/target evidence first; persist an atomic transfer + target checkpoint, then swap memory. Roll back on failure and never report applied when persistence failed.
- Estimated implementation: ~160 LOC. Dependencies: G003,G005.

#### G007 — Decision write can succeed without required graph edges

- Functions / construction points: `age_graph_store.py:write_decision`.
- Evidence / edit targets: `ci-platform/ci_platform/graph/age_graph_store.py:748,777,786,790,792,810`.
- Current behavior: write_decision creates a Decision, may fall back to an unlinked node when entity matching returns no row, and logs domain/FactorVector linking failures.
- Change: Make required Decision, domain, entity and factor links one transaction with cardinality assertions. Treat deliberately missing context as explicit incomplete evidence, not an equivalent success.
- Estimated implementation: ~220 LOC. Dependencies: None.

#### G008 — Platform-state replacement is delete-then-create across commits

- Functions / construction points: `age_graph_store.py:_save_platform_state`.
- Evidence / edit targets: `ci-platform/ci_platform/graph/age_graph_store.py:109,117,126`.
- Current behavior: _save_platform_state deletes the previous state before a separate CREATE call; interruption/concurrent writers can lose state or race.
- Change: Use a single transaction/connection and version-checked replacement; add crash and concurrent-writer tests for posterior, promotion, evolution, governance and compounding state.
- Estimated implementation: ~170 LOC. Dependencies: None.

#### G009 — Low-level graph/count errors become zero or phase A

- Functions / construction points: `age_client.py:get_sequence_count`, `age_client.py:get_cross_category_count`, `two_phase_strategy.py:get_phase`, `two_phase_strategy.py:get_status`.
- Evidence / edit targets: `ci-platform/ci_platform/graph/age_client.py:660,679`; `ci-platform/ci_platform/strategy/two_phase_strategy.py:31,47`.
- Current behavior: Count/phase helpers catch graph exceptions and substitute empty-phase results; availability is not equivalent to zero verified history.
- Change: Raise typed unavailable errors; represent counts as unknown on failed reads. Do not advance readiness or learning from substituted zero.
- Estimated implementation: ~80 LOC. Dependencies: None.

#### G010 — Copied framework helpers conceal graph failures

- Functions / construction points: `decision_history.py:get_category_stats`, `composite_gate.py:evaluate`, `similar_cases_base.py:_fetch_verified_decisions`, `provenance.py:get_provenance_from_graph`, `shadow_mode.py:get_shadow_report`, `checkpoint.py:list_checkpoints`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/framework/decision_history.py:59`; `copilot-sdk/copilot_sdk/framework/composite_gate.py:120`; `copilot-sdk/copilot_sdk/framework/similar_cases_base.py:99`; `copilot-sdk/copilot_sdk/framework/provenance.py:326`; `copilot-sdk/copilot_sdk/framework/shadow_mode.py:106`; `copilot-sdk/copilot_sdk/framework/checkpoint.py:98`.
- Current behavior: History/gates/similarity/provenance/shadow/checkpoint helpers return defaults, [], None or neutral accuracy after failures; SOC and S2P retain copies with analogous catches (Appendix C).
- Change: Replace the copies with one fail-closed GraphStore-backed implementation. Distinguish no rows from unavailable; keep an explicit error-bearing diagnostic response only where no authoritative decision depends on it.
- Estimated implementation: ~350 LOC. Dependencies: G001.

#### G011 — DataOps investigation reintroduces fixtures above a fail-closed client

- Functions / construction points: `investigation_patterns.py:_pipelines`, `investigation_patterns.py:_blast_radius`, `investigation_patterns.py:_recurrence`.
- Evidence / edit targets: `copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:352,365,378`.
- Current behavior: Investigation catches get_pipelines/blast-radius/recurrence failures and reads fallback fixtures/defaults, including exceptions the AGE-required client turned into 503.
- Change: Propagate unavailable through evidence acquisition; allow fixtures only under explicit demo mode and preserve their provenance through score/receipt.
- Estimated implementation: ~90 LOC. Dependencies: None.

#### G012 — DataOps live alerts inject a fixture; one detail route swallows outages

- Functions / construction points: `context_router.py:_append_abstention_fixture`, `context_router.py:alerts`, `context_router.py:alert_groups`, `context_router.py:alert_detail`.
- Evidence / edit targets: `copilot-sdk/apps/dataops/backend/app/context_router.py:545,549,859,873,1423,1427`.
- Current behavior: DI-ABSTENTION-001 is appended to live results; alert_detail returns its fixture even after any graph exception. This catch contains a later raise, so a simplistic no-raise scan misses it.
- Change: Demo-gate the injected alert and the special exception branch. In production, let graph failure remain unavailable and seed real scenarios through AGE if required.
- Estimated implementation: ~65 LOC. Dependencies: None.

#### G013 — Purchasing graph-read errors become empty evidence

- Functions / construction points: `main.py:_evolution_variants`, `context_router.py:_evolution_variants`, `evidence.py:_verified_decisions`, `evidence.py:_centroid_checkpoints`, `trust_router.py:_decisions_total`, `purchasing_control.py:refresh`.
- Evidence / edit targets: `copilot-sdk/apps/purchasing/backend/app/main.py:416`; `copilot-sdk/apps/purchasing/backend/app/context_router.py:82`; `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:182,193`; `copilot-sdk/apps/purchasing/backend/app/routers/trust_router.py:163`; `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:70`.
- Current behavior: Evolution, evidence, trust and outcome checks suppress failures into []/0/False; clients cannot tell graph outage from no evidence.
- Change: Propagate typed graph errors through these projections; safety gates may deny but must include unavailable and prevent success/readiness claims.
- Estimated implementation: ~150 LOC. Dependencies: None.

#### G014 — S2P no-history/default projections hide graph outages

- Functions / construction points: `s2p_demo_beats.py:_rows`, `s2p_governance.py:_safe_conservation_snapshot`, `s2p_evidence.py:_conservation_snapshot`, `s2p_context_builder.py:_supplier_enrichment`, `centroid_explorer.py:_p39_evidence`.
- Evidence / edit targets: `s2p-copilot/backend/app/routers/s2p_demo_beats.py:49`; `s2p-copilot/backend/app/routers/s2p_governance.py:38`; `s2p-copilot/backend/app/routers/s2p_evidence.py:206,220`; `s2p-copilot/backend/app/services/s2p_context_builder.py:271`; `s2p-copilot/backend/app/services/centroid_explorer.py:208`.
- Current behavior: GraphUnavailableError can become []; evidence/context becomes {}; governance uses unknown/zero. Some deny safely, but no-history and failed-read remain conflated.
- Change: Return explicit unavailable for failed reads. Day-zero is valid only after a successful zero-count query; keep safety denials visibly error-bearing.
- Estimated implementation: ~170 LOC. Dependencies: None.

#### G015 — S2P learning and lineage writes are best-effort

- Functions / construction points: `s2p.py:_persist_l5_conservation_state`, `s2p.py:_persist_l5_centroid_state`, `s2p.py:_persist_l5_dk_state`, `s2p.py:_read_centroid_for_l5`, `s2p.py:_link_decision_to_invoice`, `s2p.py:_receipt_conservation_snapshot`, `s2p.py:_record_supplier_profile`, `s2p.py:score_procurement_event`.
- Evidence / edit targets: `s2p-copilot/backend/app/routers/s2p.py:831,842,866,899,921,970,1004,1063,1491,1832,2352,2469,2493,2512,2540`.
- Current behavior: Local learn pipeline catches conservation/centroid/DK/supplier/receipt/link errors and continues; prior counts and snapshots can default.
- Change: Move required learn/outcome/context linkage behind the shared transactional contract; distinguish optional telemetry failures from required judgment evidence.
- Estimated implementation: ~350 LOC. Dependencies: G003,G007.

#### G016 — SOC metric fallback serves static data after graph failure

- Functions / construction points: `soc.py:query_soc_metrics`.
- Evidence / edit targets: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:592`.
- Current behavior: Graph-backed metric context catches failure and calls get_metric_data(metric_id).
- Change: Surface unavailable in production; route static metric material only through explicit demo fixtures with no learned/measured claim.
- Estimated implementation: ~50 LOC. Dependencies: None.

#### G017 — SOC graph reads become empty history or fabricated no-data

- Functions / construction points: `soc.py:get_analyst_benchmarking`, `triage.py:get_graph_data`, `learning_health.py:compute_verification_health`, `campaigns.py:fetch_all_events`, `campaigns.py:fetch_recent_events`, `campaigns.py:fetch_single_alert_event`, `campaigns.py:get_campaigns`, `campaigns.py:get_campaign_detail`.
- Evidence / edit targets: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2164,2200,2261,2286`; `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3561`; `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:1026,1036,1063,1081`; `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1340,1377,1413,1756,1780`.
- Current behavior: Graph read catches return accumulating/empty lists/zero counts/None across metrics, topology, learning and campaigns. Appendix C includes every AST candidate, including explicit diagnostic exceptions.
- Change: Require typed no-data versus unavailable responses; preserve error context and fail readiness for required components. Do not render outage as healthy accumulating history.
- Estimated implementation: ~400 LOC. Dependencies: None.

#### G018 — SOC judgment-side context and audit writes are optional in code

- Functions / construction points: `triage.py:analyze_alert`, `triage.py:report_decision_outcome`, `reconvergence_logger.py:log_reconvergence_event`, `reconvergence_logger.py:log_decision_distance`, `snapshots.py:_write_profile_snapshot`, `learning_health.py:_persist_l5_conservation_state`, `investigation_patterns.py:_bounded_read`, `investigation_patterns.py:_fallback_context`.
- Evidence / edit targets: `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1242,1473,2151,2639,2882`; `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:106,178`; `gen-ai-roi-demo-v4-v50/backend/app/services/snapshots.py:68`; `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:725`; `gen-ai-roi-demo-v4-v50/backend/app/services/investigation_patterns.py:120,133`.
- Current behavior: Campaign flags, RL metadata, outcome audit, DK, TRIGGERED_EVOLUTION, snapshots and reconvergence catches log/return rather than invalidating accepted work.
- Change: Declare the required evidence bundle and atomically persist it. Optional observability must be named optional and cannot supply later safety or learning evidence.
- Estimated implementation: ~450 LOC. Dependencies: G003,G007.

#### G019 — SOC variant history guard fails open

- Functions / construction points: `variant_generator.py:_consult_history`.
- Evidence / edit targets: `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:86`.
- Current behavior: A failed history check returns action=proceed.
- Change: Return unavailable/deny and require a successful history read before variant generation or promotion.
- Estimated implementation: ~25 LOC. Dependencies: None.

#### G020 — Trading projections suppress graph failure

- Functions / construction points: `trader_profiles.py:_verified_decisions`, `trust_analysis.py:_decisions_until_dk`, `claim_gate.py:refresh_from_store`, `evidence_providers.py:_domain_context`.
- Evidence / edit targets: `copilot-sdk/apps/trading/backend/app/services/trader_profiles.py:85`; `copilot-sdk/apps/trading/backend/app/services/trust_analysis.py:173`; `copilot-sdk/apps/trading/backend/app/services/claim_gate.py:97`; `copilot-sdk/apps/trading/backend/app/evidence_providers.py:83`.
- Current behavior: History/trust/claim evidence failures become []/None or retain stale state. Conservative RED/UNKNOWN gate catches also need explicit availability.
- Change: Propagate unavailable; invalidate cached claim evidence on failed reads. Keep fail-closed RED/UNKNOWN but label it a read failure, not measured state.
- Estimated implementation: ~150 LOC. Dependencies: None.

#### G021 — Transfer impact and reset tolerate incomplete graph state

- Functions / construction points: `transfer_router.py:_pattern_dollar_impact`, `transfer_router.py:_reset_conservation_state`, `transfer_router.py:_save_transfer_checkpoint`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/backend/transfer_router.py:202,214,631,654,699`.
- Current behavior: Financial impact silently sums whichever domain reads succeed; reset failure returns False after centroids have changed; checkpoint persistence is best-effort.
- Change: Return unknown impact on any failed contributing read; make reset/event/checkpoint atomic with transfer and validate source-decision scope rather than summing unrelated decisions.
- Estimated implementation: ~140 LOC. Dependencies: G006.

#### G022 — DataOps evolution/cohort failures look empty

- Functions / construction points: `ae_router.py:_events`, `cohort_status.py:_read_decisions`.
- Evidence / edit targets: `copilot-sdk/apps/dataops/backend/app/ae_router.py:47`; `copilot-sdk/apps/dataops/backend/app/services/cohort_status.py:149`.
- Current behavior: Evolution reads and per-cohort failures are suppressed; omission creates a plausible partial result.
- Change: Fail the projection or mark every omitted cohort unavailable with completeness=false; never publish complete learned telemetry from partial reads.
- Estimated implementation: ~65 LOC. Dependencies: None.

#### G023 — Preseed rejection history is labelled learned without graph learning

- Functions / construction points: `preseed.py:preseed_trading`, `preseed.py:_persist_trading_rejections`, `evolution_router.py:variants`, `evolution_router.py:build_evolution_summary`, `main.py:create_app`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/demo/preseed.py:143,153,330`; `copilot-sdk/copilot_sdk/backend/evolution_router.py:90,299`; `copilot-sdk/apps/trading/backend/app/main.py:563`.
- Current behavior: Deterministic preseed creates five rejected variants with learned provenance in evolution_log.json; runtime merges persisted rejection material into the panel.
- Change: Tag synthetic seeded evidence as synthetic, keep it out of learned counters, and derive production rejection history from persisted AGE evaluations/receipts.
- Estimated implementation: ~100 LOC. Dependencies: None.


### P2 — GraphStore bypasses and shared-memory architecture

#### G024 — All five runtimes create a SQLite K-utility store

- Functions / construction points: `investigation.py:KUtilityStore`, `investigation.py:__init__`, `investigation.py:update_weights`, `main.py:__init__`, `main.py:create_app`, `main.py:module initialization`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/scoring/investigation.py:404,415,441`; `copilot-sdk/apps/trading/backend/app/main.py:140,595`; `copilot-sdk/apps/purchasing/backend/app/main.py:152,872`; `copilot-sdk/apps/dataops/backend/app/main.py:117,991`; `s2p-copilot/backend/app/main.py:46,499`; `gen-ai-roi-demo-v4-v50/backend/app/main.py:200,249`.
- Current behavior: KUtilityStore expects a raw SQLite connection and stores category/dimension utility outside AGE; its table has no domain column.
- Change: Add domain-scoped graph utility/learning operations linked to investigation, evidence, outcome and Decision; inject the common GraphStore into all five routers.
- Estimated implementation: ~240 LOC. Dependencies: G003.

#### G025 — Investigation traces and K feedback are not a closed production learning loop

- Functions / construction points: `investigation_router.py:investigate`, `investigation.py:update_weights`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/backend/investigation_router.py:83,122`; `copilot-sdk/copilot_sdk/scoring/investigation.py:441`.
- Current behavior: Investigation returns traces and reads K weights; non-test update_weights callers found are experiments/scripts, not the five production verification paths.
- Change: Persist trace/evidence identities to AGE and call idempotent utility updates from verified outcome processing. Add restart/replay tests proving weights derive from those graph receipts.
- Estimated implementation: ~260 LOC. Dependencies: G024,G003.

#### G026 — Cross-application signals are shared through SQLite, not graph edges

- Functions / construction points: `signal_store.py:shared_signal_path`, `signal_store.py:SQLiteSignalStore`, `signal_store.py:_connection`, `cross_signal_router.py:create_cross_signal_router`, `main.py:create_app`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/backend/signal_store.py:21,25,48`; `copilot-sdk/copilot_sdk/backend/cross_signal_router.py:57,61`; `copilot-sdk/apps/trading/backend/app/main.py:584`; `copilot-sdk/apps/purchasing/backend/app/main.py:849`; `copilot-sdk/apps/dataops/backend/app/main.py:872`.
- Current behavior: Three apps explicitly mount SQLiteSignalStore(shared_signal_path()). File-based shared delivery is a second semantic/cross-domain memory store.
- Change: Model source-domain Signal/Event nodes with provenance and receiving-domain links; query/deliver via GraphStore with acknowledgement/version semantics. Migrate retained signals before disabling SQLite.
- Estimated implementation: ~230 LOC. Dependencies: None.

#### G027 — DataOps holdout judgments remain in SQLite

- Functions / construction points: `dataops_governance.py:__init__`, `dataops_governance.py:register_holdout`, `dataops_governance.py:verify_holdout`, `dataops_governance.py:provenance`, `main.py:create_app`.
- Evidence / edit targets: `copilot-sdk/apps/dataops/backend/app/dataops_governance.py:24,30,32,44,87,114,126`; `copilot-sdk/apps/dataops/backend/app/main.py:732`.
- Current behavior: Holdout decisions, factor vectors, score payloads and verdict receipts use dataops_governance.sqlite3; missing graph event capabilities select a SQLite OutcomeLedger.
- Change: Store holdout/evaluation judgments and receipts in AGE, linked to the evaluated variant and domain. Remove production capability fallback; retain test stores only with an explicit test profile.
- Estimated implementation: ~260 LOC. Dependencies: G003.

#### G028 — Purchasing control has ungated capability-based local-store fallbacks

- Functions / construction points: `purchasing_control.py:__init__`, `purchasing_control.py:PurchasingControlService`.
- Evidence / edit targets: `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:136,153,159,160,165`.
- Current behavior: With the current full AGE adapter graph ledgers are selected, but missing capabilities silently select SQLite proof/outcome ledgers and local twin persistence.
- Change: Validate complete required capabilities at production startup and raise; make SQLite constructors explicit test/development dependencies, not hasattr fallback branches.
- Estimated implementation: ~100 LOC. Dependencies: None.

#### G029 — Trading metadata and journal evidence persist to JSON

- Functions / construction points: `context_router.py:save_trade_metadata`, `context_router.py:get_trade_metadata`, `journal.py:_read_json_unlocked`, `journal.py:_write_json_atomic_unlocked`.
- Evidence / edit targets: `copilot-sdk/apps/trading/backend/app/context_router.py:525,531,541`; `copilot-sdk/apps/trading/backend/app/routers/journal.py:565,583`.
- Current behavior: Trade metadata and journal/verification projection data have local JSON state separate from canonical Decisions.
- Change: Move evidence/annotations into typed domain-scoped graph operations linked to Decision IDs; reject unknown or foreign-domain IDs and rebuild projections from graph evidence.
- Estimated implementation: ~240 LOC. Dependencies: None.

#### G030 — Trading trust/pattern/conservation projections use process-local trades

- Functions / construction points: `context_router.py:module initialization`, `context_router.py:trust_analysis`, `context_router.py:behavioral_patterns`, `context_router.py:conservation_breakdown`, `data_import.py:module initialization`, `trading_registry.py:trust_analysis`.
- Evidence / edit targets: `copilot-sdk/apps/trading/backend/app/context_router.py:13,393,394,406,407,426,430`; `copilot-sdk/apps/trading/backend/app/routers/data_import.py:216`; `copilot-sdk/apps/trading/backend/app/state/trading_registry.py:101`.
- Current behavior: Import-router memory supplies operational episodes; AGE-preseeded Decisions need not populate that list. Strategy breakdown is explicitly a proxy, not the authoritative conservation computation.
- Change: Ingest imported trades as domain-scoped episodic nodes and join to Decisions/outcomes. Read trust/pattern/proxy views from that graph-backed projection, with proxy labelling retained.
- Estimated implementation: ~280 LOC. Dependencies: None.

#### G031 — Trading promotion authority is split between JSON and memory stores

- Functions / construction points: `promotion.py:_load`, `promotion.py:_save`, `promotion_state.py:PromotionStateStore`, `promotion_state.py:_load`, `promotion_state.py:_save`, `promotion_router.py:module initialization`, `main.py:create_app`.
- Evidence / edit targets: `copilot-sdk/apps/trading/backend/app/services/promotion.py:42,57`; `copilot-sdk/apps/trading/backend/app/services/promotion_state.py:52,65,105`; `copilot-sdk/apps/trading/backend/app/routers/promotion_router.py:33`; `copilot-sdk/apps/trading/backend/app/main.py:658,665`.
- Current behavior: Both promotion route families are mounted; their state is not the common graph promotion record and one default is in-memory.
- Change: Consolidate routes onto one GraphPromotionStore, with versioned promotion/rollback evidence and restart-safe authority. Remove or migrate both local stores.
- Estimated implementation: ~260 LOC. Dependencies: G003.

#### G032 — Trading analytics cache remains an ungated local source

- Functions / construction points: `context_router.py:_load_json_optional`, `context_router.py:module initialization`, `context_router.py:analytics`.
- Evidence / edit targets: `copilot-sdk/apps/trading/backend/app/context_router.py:58,66,381,384`.
- Current behavior: /analytics reads analytics_cache JSON; optional loader can fall back to the packaged data directory. Several other market/similarity fixture paths now correctly require demo mode.
- Change: Use graph-derived analytics with cache provenance/version tied to graph identity; require demo mode for packaged analytics and never silently fall across configured roots.
- Estimated implementation: ~100 LOC. Dependencies: None.

#### G033 — Purchasing operational and audit surfaces are fixture-backed

- Functions / construction points: `main.py:_load_order_rows`, `main.py:waste_analysis`, `main.py:predictive_par_week`, `main.py:create_app`, `audit_export.py:generate_pack`, `payment_timing.py:__init__`, `disruption_recovery.py:__init__`.
- Evidence / edit targets: `copilot-sdk/apps/purchasing/backend/app/main.py:650,690,715,724,725,726,729`; `copilot-sdk/apps/purchasing/backend/app/services/audit_export.py:16`; `copilot-sdk/apps/purchasing/backend/app/services/payment_timing.py:11`; `copilot-sdk/apps/purchasing/backend/app/services/disruption_recovery.py:12`.
- Current behavior: Orders/par/waste/report calculations load JSON or demo_par_items. Always-mounted demo services fabricate disruption/payment history and a hash-verified audit pack (honestly tagged demo).
- Change: Demo-gate these services; build production projections from graph episodes, outcomes and policies. Audit exports must verify actual receipts/hash chains rather than hard-code GREEN/verified.
- Estimated implementation: ~400 LOC. Dependencies: None.

#### G034 — DataOps operational process/audit context remains local material

- Functions / construction points: `context_router.py:_load_transformations`, `context_router.py:_load_schema_changes`, `context_router.py:_pipeline_count`, `context_router.py:pipeline_decisions`, `context_router.py:process_timeline`, `context_router.py:_cross_graph_daily_cost`, `context_router.py:cross_graph_insight`, `context_router.py:_apply_fix_estimated_savings`, `context_router.py:process_signals`, `context_router.py:module initialization`, `context_router.py:audit_trail`.
- Evidence / edit targets: `copilot-sdk/apps/dataops/backend/app/context_router.py:681,693,705,1042,1176,1259,1286,1346,1511,1556,1588`.
- Current behavior: Transformations, schema changes, process timeline/signals and audit-trail construction read local files; not all are graph-derived even when topology is live. Some mutation routes are correctly explicit demo-only.
- Change: Make each production projection graph-backed and linked to episode/Decision evidence; keep demo apply-fix/metadata routes separated and never count their chains as canonical audit receipts.
- Estimated implementation: ~400 LOC. Dependencies: None.

#### G035 — S2P supplier memory is process-local and blended with fixtures

- Functions / construction points: `supplier_profile_accumulator.py:__init__`, `supplier_profile_accumulator.py:_load_fixtures`, `supplier_profile_accumulator.py:get_profile`, `supplier_profile_accumulator.py:module initialization`.
- Evidence / edit targets: `s2p-copilot/backend/app/services/supplier_profile_accumulator.py:69,79,121,124,137,523`.
- Current behavior: Global accumulator loads demo suppliers, retains events in memory, and blends fixture history until a threshold; restart can lose accumulated episodes.
- Change: Ingest suppliers and verified invoice events into AGE, compute profile projections with evidence links and restart/replay consistency; fixture priors must remain separately labelled.
- Estimated implementation: ~260 LOC. Dependencies: G015.

#### G036 — S2P context and comparison surfaces still have fixture pathways

- Functions / construction points: `s2p_pvg.py:_load_candidate_json`, `s2p_pvg.py:variants`, `s2p_preview.py:_load_fixture_json`, `s2p_preview.py:_load_celonis_cache`, `s2p_preview.py:_get_preview_simulation_scorer`, `factors.py:compute_all_factors`.
- Evidence / edit targets: `s2p-copilot/backend/app/routers/s2p_pvg.py:39,156`; `s2p-copilot/backend/app/routers/s2p_preview.py:42,55,284`; `s2p-copilot/backend/app/domains/s2p/factors.py:438`.
- Current behavior: PVG/preview/context paths read synthetic invoices or use a separate in-memory simulation; factor acquisition can substitute neutral values. Isolated preview is not itself a production Decision fallback, but it cannot prove shared-graph learning.
- Change: Separate simulation APIs/provenance from authoritative endpoints; ingest production semantic context into AGE and reject unavailable required factors. Review all remaining S2P fixture candidates in Appendix B.
- Estimated implementation: ~250 LOC. Dependencies: None.

#### G037 — SOC cross-copilot platform panels are fixture projections

- Functions / construction points: `platform.py:_load_cross_signals`, `platform.py:_load_domain_table`, `platform.py:_load_warm_start_evidence`, `platform.py:_load_chain_credit_demo`, `platform.py:_load_rl_reward_demo`, `platform.py:_load_rl_exploration_demo`.
- Evidence / edit targets: `gen-ai-roi-demo-v4-v50/backend/app/routers/platform.py:46,77,111,144,177,210`.
- Current behavior: Platform signal/domain/warm-start/chain-credit/RL summaries load fixture material instead of performing shared-graph traversals.
- Change: Replace production panels with typed cross-domain AGE projections; keep static platform stories behind an explicit demo namespace.
- Estimated implementation: ~220 LOC. Dependencies: None.

#### G038 — State in AGE is often JSON co-location, not traversable memory

- Functions / construction points: `age_graph_store.py:_save_platform_state`, `age_graph_store.py:save_evolution`, `age_graph_store.py:delete_governance`.
- Evidence / edit targets: `ci-platform/ci_platform/graph/age_graph_store.py:109,115,170,234`.
- Current behavior: Posterior/evolution/promotion/compounding/governance state is serialized into payload properties. Merely putting blobs in soc_graph does not connect constituent procedures, judgments or observations.
- Change: Model stable state/version, rule, evidence and outcome nodes with explicit relationships; retain payloads as snapshots only. Provide single-query interaction tests for the four memory types.
- Estimated implementation: ~600 LOC. Dependencies: G008.

#### G039 — DecisionEntityLink fallback is not a graph relationship

- Functions / construction points: `age_graph_store.py:link_decision_to_entity`, `age_graph_store.py:get_decision_links`.
- Evidence / edit targets: `ci-platform/ci_platform/graph/age_graph_store.py:3217,3248,3269,3285`.
- Current behavior: When a real entity edge cannot be made, link_decision_to_entity creates a surrogate node; special readers merge it, but ordinary graph traversals do not follow it.
- Change: Require a real scoped entity and relationship or explicitly create a typed placeholder entity with provenance; migrate surrogate records and verify each with a traversal.
- Estimated implementation: ~200 LOC. Dependencies: G007.

#### G040 — Domain isolation has residual query and entity-anchor holes

- Functions / construction points: `age_graph_store.py:write_decision`, `age_graph_store.py:query_context`, `campaigns.py:module initialization`, `campaigns.py:get_campaign_context_for_decision`, `graph_explorer.py:run_safe_query`, `graph_explorer.py:get_node_neighbors`, `projection.py:ProjectionRegistry`, `projection.py:render`, `nl_query.py:_query_template`.
- Evidence / edit targets: `ci-platform/ci_platform/graph/age_graph_store.py:777,3776,3797`; `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:490,509`; `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:117,138,213`; `copilot-sdk/copilot_sdk/graph/projection.py:70,73`; `copilot-sdk/copilot_sdk/di/nl_query.py:132`.
- Current behavior: Entity matching uses entity_id alone; query_context scopes returned n but not root/intermediates. SOC campaign context lacks domain for both Decision aliases; read-only explorer accepts unrestricted caller Cypher. Projection/NL helpers permit missing domain.
- Change: Require scoped composite identities and domain-aware query APIs; bind every Decision alias, root and allowed intermediate. Put deliberate cross-domain access behind explicit source/target authorization, not a missing predicate.
- Estimated implementation: ~320 LOC. Dependencies: None.

#### G041 — SOC production Decision access still bypasses GraphStore

- Functions / construction points: `graph_client.py:module initialization`, `triage.py:analyze_alert`, `triage.py:execute_action`, `triage.py:report_decision_outcome`, `soc.py:explain_decision`.
- Evidence / edit targets: `gen-ai-roi-demo-v4-v50/backend/app/db/graph_client.py:27,49`; `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1119,1795,2104`; `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1140`.
- Current behavior: SOC uses AGEClient.run_query directly across routers/services despite its correct AGE configuration and GraphStore-backed scorer adapter. This violates the requested protocol-only boundary, not necessarily AGE backing.
- Change: Move Decision reads/writes into domain-scoped GraphStore operations; leave raw semantic graph internals inside the adapter only, with explicit protocol traversal methods.
- Estimated implementation: ~900 LOC. Dependencies: G007,G040.

#### G042 — Factory/profile guards are not a universal capability boundary

- Functions / construction points: `factory.py:create_graph_store`, `scorer.py:from_preset`, `graph_config.py:require_shared_graph`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/graph/factory.py:153,160,183,209`; `copilot-sdk/copilot_sdk/scoring/scorer.py:282,306,311`; `copilot-sdk/copilot_sdk/config/graph_config.py:26,50`.
- Current behavior: Normal production from_preset rejects concrete SQLite/memory stores, but factory explicit overrides bypass its config-only validation path; wrappers and test flags can evade concrete-type/profile assumptions. Dual-write's primary is SQLite.
- Change: Require a validated production GraphConfig and an authoritative-backend capability descriptor for every factory/injection; isolate test factories. Production must reject SQLite-primary dual-write even through wrappers.
- Estimated implementation: ~200 LOC. Dependencies: None.

#### G043 — One graph name does not enforce one graph destination

- Functions / construction points: `graph_queries.py:_load_topology_config`, `graph_queries.py:DataOpsGraphClient`, `main.py:create_app`, `graph_config.py:load`, `graph_config.py:_default`.
- Evidence / edit targets: `copilot-sdk/apps/dataops/backend/app/graph_queries.py:48,62,68,100`; `copilot-sdk/apps/dataops/backend/app/main.py:679`; `copilot-sdk/copilot_sdk/config/graph_config.py:112,213`.
- Current behavior: DataOps resolves a separate topology client while temporarily removing generic environment settings. All apps can select the same soc_graph name on different databases; current shared-name guard cannot prove identity.
- Change: Inject the resolved shared GraphConfig/store into topology services; eliminate process-environment mutation; compare redacted database identity + graph OID/name across all five at readiness.
- Estimated implementation: ~220 LOC. Dependencies: None.

#### G044 — Cross-domain discovery still reads exported fingerprints

- Functions / construction points: `transfer.py:save_fingerprint`, `transfer.py:load_fingerprints_with_warnings`, `transfer_router.py:transfer_opportunities`, `scorer.py:export`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/backend/transfer.py:24,41,51,62`; `copilot-sdk/copilot_sdk/backend/transfer_router.py:60,62`; `copilot-sdk/copilot_sdk/scoring/scorer.py:2093`.
- Current behavior: Opportunity detection reads per-domain JSON exports and does a Python merge, even though AGE has transfer/fingerprint operations.
- Change: Use one explicit cross-domain graph projection linked to verified fingerprint evidence and source/target domains. Keep JSON only as export, never the production discovery source.
- Estimated implementation: ~180 LOC. Dependencies: None.

#### G045 — Ungated default stores remain in reusable production APIs

- Functions / construction points: `core.py:__init__`, `transfer.py:__init__`, `prompt_evolver.py:__init__`, `proposal_service.py:__init__`, `authority_ladder.py:__init__`, `authority_ladder.py:get_authority_manager`, `registry.py:register`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/promotion/core.py:114,222`; `copilot-sdk/copilot_sdk/pilot/transfer.py:50,262`; `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:68`; `s2p-copilot/backend/app/services/proposal_service.py:45,302`; `gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:132,141,341`; `copilot-sdk/copilot_sdk/transfer/registry.py:89`.
- Current behavior: Default promotion/pilot/proposal/authority constructors use SQLite; evolver/registry defaults use memory/JSON. Some current app startup paths inject graph alternatives, so these are latent API bypasses, not proof that those configured apps run on SQLite.
- Change: Require store injection in production constructors and fail if absent; move local defaults to named test/demo builders. Add construction tests covering every public SDK entry point.
- Estimated implementation: ~250 LOC. Dependencies: None.

#### G046 — SOC legacy posterior API still permits raw DSN SQL

- Functions / construction points: `posterior_store.py:__init__`, `posterior_store.py:save`, `posterior_store.py:load`, `posterior_store.py:clear`, `posterior_store.py:_ping_storage`, `posterior_store.py:_ensure_table`.
- Evidence / edit targets: `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:53,68,120,156,184,208,221`.
- Current behavior: Typed GraphConfig uses GraphStore now, but a raw-string constructor route retains psycopg SQL state persistence without a test-only guard.
- Change: Remove or explicitly quarantine the raw-DSN constructor; migrate old relational posterior records and require typed graph config in all production callers.
- Estimated implementation: ~120 LOC. Dependencies: None.

#### G047 — No complete production single-traversal contract covers all four memories

- Functions / construction points: `protocol.py:GraphStore`, `protocol.py:GraphTraversalStore`, `protocol.py:ProtocolV2GraphStore`, `protocol.py:L5LearningStore`, `age_graph_store.py:_link_transfer_edges`, `age_graph_store.py:write_transfer_pattern`, `age_graph_store.py:query_context`, `main.py:create_app`, `discovery_router.py:_domain_decisions`, `discovery_router.py:_demo_domain_decisions`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/graph/protocol.py:16,238,264,464`; `ci-platform/ci_platform/graph/age_graph_store.py:1432,2263,3776`; `copilot-sdk/apps/dataops/backend/app/main.py:941`; `copilot-sdk/copilot_sdk/backend/discovery_router.py:75,98`.
- Current behavior: GraphStore/AGE contains real entity/transfer support, but DataOps discovery is constructed with object() and can fall back to hard-coded SOC/S2P records; many cross-type consumers use files, memory, JSON blobs and Python orchestration.
- Change: Specify and implement episodic×judgment, semantic×judgment, procedural×judgment and cross-domain judgment×judgment queries. Require evidence-linked returned paths and no second-store lookup; replace object() discovery with a real engine.
- Estimated implementation: ~700 LOC. Dependencies: G024,G026,G035,G038,G039,G044.

#### G048 — Investigation evidence providers are fixture/local sources in all five apps

- Functions / construction points: `main.py:create_app`, `main.py:module initialization`, `query_providers.py:_decision_invoice_ids`, `query_providers.py:_decisions`.
- Evidence / edit targets: `copilot-sdk/apps/trading/backend/app/main.py:595`; `copilot-sdk/apps/purchasing/backend/app/main.py:870,872`; `copilot-sdk/apps/dataops/backend/app/main.py:988,991`; `s2p-copilot/backend/app/main.py:496,499`; `gen-ai-roi-demo-v4-v50/backend/app/main.py:249`; `copilot-sdk/copilot_sdk/di/query_providers.py:178`; `copilot-sdk/copilot_sdk/di/query_providers.py:104,178`.
- Current behavior: VLD investigation routers inject local evidence providers; DataOps mixes AGE decisions with local SAP invoice/trust material. Scoring on graph Decisions does not make these evidence reads graph traversals.
- Change: Persist source observations with source system, time, version and provenance into the semantic/episodic graph; obtain investigation evidence through scoped graph traversal and link every acquired item to its trace.
- Estimated implementation: ~550 LOC. Dependencies: G025,G047.


### P3 — Observability and health

#### G049 — Trading health infers backend but does not prove connection/config provenance

- Functions / construction points: `main.py:create_app`, `main.py:health`, `graph_status.py:build_trading_graph_status`.
- Evidence / edit targets: `copilot-sdk/apps/trading/backend/app/main.py:714,719,726`; `copilot-sdk/apps/trading/backend/app/graph_status.py:381,429,452`.
- Current behavior: Health contains graph_backend/graph_status, but status=ok and object-type/selection evidence are not a fresh domain query or a redacted DSN-source report.
- Change: Return one schema with selected/actual backend, fresh read result, graph identity, config sources, restore/artifact readiness and error; separate liveness from readiness.
- Estimated implementation: ~100 LOC. Dependencies: G001,G004,G043.

#### G050 — Purchasing health aliases disagree

- Functions / construction points: `main.py:create_app`, `main.py:api_health`.
- Evidence / edit targets: `copilot-sdk/apps/purchasing/backend/app/main.py:624,631,632,960`.
- Current behavior: /api/health includes graph fields, while /health lacks them; observing the latter cannot establish that Purchasing is off AGE.
- Change: Use one health builder for both aliases, probe the authoritative store, and include graph_name, connection state, config provenance and component failures.
- Estimated implementation: ~90 LOC. Dependencies: G043.

#### G051 — DataOps health reports topology only and an ambiguous fixture label

- Functions / construction points: `main.py:create_app`, `main.py:health`, `graph_queries.py:DataOpsGraphClient`, `graph_queries.py:__init__`, `graph_queries.py:graph_source`, `graph_queries.py:_run_graph`.
- Evidence / edit targets: `copilot-sdk/apps/dataops/backend/app/main.py:1054,1061,1065,1066`; `copilot-sdk/apps/dataops/backend/app/graph_queries.py:100,131,140,568`.
- Current behavior: Disconnected topology reports source=fixture even when AGE-required reads would raise. Health omits graph_backend/status and the independent Decision store; connection state can remain stale after a query failure.
- Change: Report decision_store and topology separately using the same config; use unavailable rather than fixture when fixture delivery is forbidden. Refresh successful/failed probe state and return non-ready status on either failure.
- Estimated implementation: ~140 LOC. Dependencies: G043.

#### G052 — S2P health provides no graph readiness

- Functions / construction points: `main.py:module initialization`, `main.py:health`, `s2p_graph_status.py:build_s2p_graph_status`.
- Evidence / edit targets: `s2p-copilot/backend/app/main.py:590,593`; `s2p-copilot/backend/app/s2p_graph_status.py:408,475`.
- Current behavior: Both health aliases return a minimal static payload despite an internal graph status subsystem.
- Change: Expose and probe actual AGE store plus restored learning/proposal/enrichment state; include graph_name and DSN/config source without credentials.
- Estimated implementation: ~90 LOC. Dependencies: G043.

#### G053 — SOC health is not the requested shared graph contract

- Functions / construction points: `main.py:health`.
- Evidence / edit targets: `gen-ai-roi-demo-v4-v50/backend/app/main.py:108,121,134`.
- Current behavior: components.graph can look healthy based on posterior-store health; required graph_backend/graph_status/name/DSN source are absent.
- Change: Expose the same contract as other copilots; probe authoritative Decision and required memory traversal components, not just posterior connectivity.
- Estimated implementation: ~110 LOC. Dependencies: G041,G043.

#### G054 — Launcher AGE badges/readiness can be optimistic

- Functions / construction points: `demo.py:wait_for_health`, `demo.py:_wait_all_healthy`, `demo.py:cmd_status`, `demo.py:cmd_start`, `preseed_all_copilots.py:check_health`.
- Evidence / edit targets: `copilot-sdk/demo.py:597,658,826,1312`; `copilot-sdk/scripts/preseed_all_copilots.py:229`.
- Current behavior: AGE badges come from requires_age selection, while health wait/checks can accept reachability or HTTP success rather than full graph readiness.
- Change: Render selected versus verified backend separately. Require consistent ready graph identity across all five before claiming AGE-ready or allowing preseed.
- Estimated implementation: ~120 LOC. Dependencies: G049,G050,G051,G052,G053.

#### G055 — No uniform visibility into incomplete learning and repair backlog

- Functions / construction points: `persistence_outbox.py:__init__`, `scorer.py:_record_persistence_failure`, `graph_status.py:build_trading_graph_status`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:116`; `copilot-sdk/copilot_sdk/scoring/scorer.py:1246`; `copilot-sdk/apps/trading/backend/app/graph_status.py:421`.
- Current behavior: A live store can coexist with failed/abandoned artifacts, missing receipts and restored/bootstrap differences; health does not expose a common completeness invariant.
- Change: Add pending/failed/abandoned counts, latest durable learn version, receipt/edge completeness and freshness. Readiness must fail when required judgment state is incomplete.
- Estimated implementation: ~180 LOC. Dependencies: G002,G003,G049,G050,G051,G052,G053.


### P4 — Preseed, tests, reference apps and enforcement

#### G056 — HTTP preseed does not prove graph destination or completeness

- Functions / construction points: `preseed_all_copilots.py:check_health`, `preseed_all_copilots.py:check_already_seeded`, `preseed_all_copilots.py:seed_s2p_domain`, `preseed_all_copilots.py:seed_domain`, `preseed_all_copilots.py:verify_domain`.
- Evidence / edit targets: `copilot-sdk/scripts/preseed_all_copilots.py:229,236,400,407,583,590,613,630`.
- Current behavior: Current all-copilot preseed POSTs score/learn APIs (not direct SQLite); health and fingerprint/count verification do not establish AGE identity, every Decision/Outcome, or cross-type edges.
- Change: Before seeding, require canonical graph readiness; afterward verify each returned ID, explicit domain, outcome/receipt and required edges via read-only GraphStore checks on the same graph.
- Estimated implementation: ~170 LOC. Dependencies: G001,G007,G054.

#### G057 — Legacy deterministic preseed conflicts with production scorer guards

- Functions / construction points: `demo.py:_seed_during_start`, `demo.py:_run_deterministic_seed`, `preseed.py:_preseed_domain`.
- Evidence / edit targets: `copilot-sdk/demo.py:1368,1472,1476,1480`; `copilot-sdk/copilot_sdk/demo/preseed.py:217,218`.
- Current behavior: Older launcher path builds InMemoryGraphStore and calls from_preset without an explicit test profile; current production guard rejects it. Launcher catches/logs the failure.
- Change: Retire this path or use the canonical API/AGE seed runner. If retained for isolated artifact generation, pass explicit test mode and do not report it as production seeding.
- Estimated implementation: ~90 LOC. Dependencies: G056.

#### G058 — Demo state bundle restoration remains SQLite-only

- Functions / construction points: `bundle.py:_restore`, `main.py:_run_startup_locked`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/demo/bundle.py:49,58,61,155`; `copilot-sdk/apps/trading/backend/app/main.py:497`.
- Current behavior: Bundle restore directly accesses SQLite and acknowledges AGE migration is separate. AGE paths skip or cannot consume it; historical local bundles are not automatically visible in graph.
- Change: Implement graph-native seed/restore with explicit provenance and all memory relationships, or remove the feature from AGE startup. Require migration receipts before claiming parity.
- Estimated implementation: ~220 LOC. Dependencies: G056.

#### G059 — JM and clone reference apps teach isolated local storage

- Functions / construction points: `run.py:run_experiment`, `engine.py:_new_governed_arm`, `run.py:module initialization`.
- Evidence / edit targets: `copilot-sdk/examples/jm_reference/run.py:83,93`; `copilot-sdk/examples/trading_clone/run.py:29`; `copilot-sdk/examples/build_your_own/engine.py:89`; `copilot-sdk/examples/build_your_own/run.py:1`.
- Current behavior: JM reference uses explicit test-profile SQLite; clone delegates; build-your-own engine uses SQLite. Valid offline examples, not demonstrations of shared-graph JM.
- Change: Keep an explicitly labelled offline mode and add a first-class AGE/sharedGraph mode with typed config, linked four-memory examples and a cross-domain traversal assertion.
- Estimated implementation: ~280 LOC. Dependencies: G047.

#### G060 — Backend tests replace production graph behavior

- Functions / construction points: `conftest.py:store`, `conftest.py:_graph_environment`, `conftest.py:S2PTestGraphStore`, `conftest.py:module initialization`, `conftest.py:isolated_app_graph_state`.
- Evidence / edit targets: `copilot-sdk/tests/scoring/conftest.py:52`; `copilot-sdk/apps/trading/backend/conftest.py:19`; `copilot-sdk/apps/purchasing/backend/conftest.py:19`; `copilot-sdk/apps/dataops/backend/conftest.py:19`; `s2p-copilot/backend/tests/conftest.py:16,189,214`.
- Current behavior: Many tests deliberately force SQLite or an in-memory fixture before app import; they cannot establish AGE behavior or correct production startup config.
- Change: Keep fast unit suites, add a separate production-profile contract suite with unmocked stores and all five real app factories; verify injected-store rejection and outage behavior.
- Estimated implementation: ~350 LOC. Dependencies: G042.

#### G061 — Live AGE tests exist but are optional/skippable and CI provisions no AGE service

- Functions / construction points: `conftest.py:age_test_graph`, `conftest.py:s2p_age_test_env`, `conftest.py:soc_stress_test_graph`, `conftest.py:_count_persistent`, `conftest.py:report_graph_contract`.
- Evidence / edit targets: `copilot-sdk/tests/graph/conftest.py:20,22,28`; `s2p-copilot/backend/tests/conftest.py:133,136,146`; `gen-ai-roi-demo-v4-v50/backend/tests/conftest.py:51,54,64`; `gen-ai-roi-demo-v4-v50/backend/conftest.py:95,159,174`; `copilot-sdk/.github/workflows/ci.yml:31`; `s2p-copilot/.github/workflows/ci.yml:31`; `ci-platform/.github/workflows/ci.yml:24`; `gen-ai-roi-demo-v4-v50/.github/workflows/ci.yml:36`.
- Current behavior: AGE tests skip when unavailable; shown CI workflows run pytest without provisioning required shared AGE. SOC fixture diagnostics can print rather than fail.
- Change: Provision a disposable shared AGE database with a required graph-integration job; fail on skip/unavailable in that job. Exercise all four interaction classes, restart, crash/outage and domain collision scenarios.
- Estimated implementation: ~400 LOC. Dependencies: G047,G060.

#### G062 — Static unification gates check text, not architecture

- Functions / construction points: `validate_age_unification.py:production_files`, `validate_age_unification.py:check_domain_isolation`, `validate_age_unification.py:check_config_completeness`, `validate_age_unification.py:check_fail_closed`, `validate_age_unification.py:check_no_bare_except`, `validate_age_unification.py:check_health_graph_status`.
- Evidence / edit targets: `copilot-sdk/scripts/validate_age_unification.py:35,59,75,83,132,153`; `copilot-sdk/docs/design/age_unification_forbidden_patterns_allowlist.toml:13,44,49`.
- Current behavior: Validator scans SDK only, treats imports as isolation, any 503 token as fail-closed, and any graph_status token as health support; ordinary except Exception escapes the bare-except check. Broad/stale allowlists suppress proof obligations.
- Change: Use AST call-graph/import boundaries plus typed config/store injection; scope all four repos, require expiring narrow exemptions and a required live contract job. Fail newly introduced runtime SQLite/fixture fallback and ungated defaults.
- Estimated implementation: ~400 LOC. Dependencies: G061.

#### G063 — Maintenance/migration tools and Trading backup still bypass unified configuration

- Functions / construction points: `sqlite_to_age.py:module initialization`, `sqlite_to_age.py:_default_source_path`, `cli_sdk.py:module initialization`, `cli_sdk.py:backup_sdk`, `cli_sdk.py:restore_sdk`, `s2p_entity_migration.py:_ensure_invoice_index`, `demo.py:verify_age`.
- Evidence / edit targets: `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:23,75`; `copilot-sdk/apps/trading/backend/app/cli_sdk.py:47,578,591,598`; `s2p-copilot/backend/app/migration/s2p_entity_migration.py:493`; `copilot-sdk/demo.py:331`.
- Current behavior: Operator paths directly connect for migration/preflight; Trading backup/restore remains SQLite-oriented. These are not normal web-Decision traffic, but explicit DSN targets can diverge from the running apps.
- Change: Retain justified adapter/migration driver use with GraphConfig-derived, confirmed source/target identity. Add AGE-aware backup/restore documentation/tooling and verify full state, not only Decision counts.
- Estimated implementation: ~260 LOC. Dependencies: G043,G058.

#### G064 — E2E success and data assumptions do not establish graph correctness

- Functions / construction points: .
- Evidence / edit targets: `copilot-sdk/e2e/trading/conservation-breakdown.spec.ts:34,39`; `copilot-sdk/e2e/trading/day-zero.spec.ts:4,33,36,48`; `copilot-sdk/e2e/trading/trust-radar.spec.ts:48,127,242`; `copilot-sdk/e2e/trading/new-surfaces.spec.ts:36,52,59`.
- Current behavior: Some tests accept unavailable/empty, some mock day-zero independently of AGE, some assume populated factors/no unavailable text, and several hard-code port 8010.
- Change: Separate UI contract tests from required real-AGE integration E2E. Seed named graph evidence, use configured base URLs, assert unavailable on outage, and verify graph-backed data identity rather than panel presence.
- Estimated implementation: ~180 LOC. Dependencies: G030,G056,G061.


### P5 — Incomplete cutover

#### G065 — Trading cutover/claim flags are intentionally incomplete

- Functions / construction points: `graph_status.py:build_trading_graph_status`.
- Evidence / edit targets: `copilot-sdk/apps/trading/backend/app/graph_status.py:421,429,452`.
- Current behavior: cutover_ready is tied to test-graph readiness conditions and product_claim_allowed is hard-coded false; AGE active is not equivalent to complete cutover.
- Change: Define evidence-based cutover criteria, run them against an authorized disposable graph, migrate/reconcile history and receipts, and compute flags from durable validation artifacts. Do not simply change false to true.
- Estimated implementation: ~160 LOC. Dependencies: G001,G003,G007,G040,G055,G056,G061.

#### G066 — Cross-app cutover excludes receipt/rollback completeness

- Functions / construction points: `graph_status.py:module initialization`, `s2p_graph_status.py:module initialization`, `s2p_graph_status.py:build_s2p_graph_status`, `verify_state.py:verify_level3`.
- Evidence / edit targets: `copilot-sdk/apps/purchasing/backend/app/graph_status.py:1`; `copilot-sdk/apps/dataops/backend/app/graph_status.py:1`; `s2p-copilot/backend/app/s2p_graph_status.py:35,437,475`; `copilot-sdk/copilot_sdk/migrate/verify_state.py:486`.
- Current behavior: Status modules retain historical SQLite visibility warnings, receipt exclusions and partial rollback/parity criteria; count/state parity is not full memory/edge/receipt parity.
- Change: Inventory and migrate local judgment/procedural state, then verify domain counts, IDs, canonical receipts, links, learning version and reversible rollback. Publish one cutover schema for all five.
- Estimated implementation: ~400 LOC. Dependencies: G024,G027,G029,G031,G035,G038,G039,G058,G065.

## Root Cause Analysis

The recurring gaps are structural, not explained by a single missed environment variable.

1. **Backend selection is being used as a proxy for architecture.** A class name, [AGE] badge or Decision row in soc_graph says nothing about local K, episode lists, promotion authority, receipts, semantic evidence or cross-domain links.
2. **Failure handling encodes demo continuity rather than production truth.** “Non-blocking,” “bootstrap,” “empty” and “best effort” catches surround data needed by safety/learning. Inner adapters can fail closed while callers catch their 503 and restore fixtures.
3. **The data boundary is porous.** Concrete isinstance checks do not constrain wrappers, raw run_query calls, hasattr fallbacks or reusable constructors with local defaults. A GraphStore Protocol is not an enforced architectural boundary.
4. **There are several authorities for the same story.** AGE events, file rejection logs, imported-memory trades, SQLite holdouts/signals and cached frontend/tab summaries can all produce plausible but mutually inconsistent panels.
5. **Three copies of framework logic and several health contracts drift.** Fixing the SDK or one route does not repair SOC/S2P copies or the other health alias.
6. **Tests chiefly prove local semantics and UI shape.** AGE-specific suites can skip; CI does not require a provisioned shared graph. Static rules search for tokens (503, graph_status), not actual endpoint behavior or exception propagation.
7. **Cutover verification is too narrow.** Decision/count/centroid parity does not prove receipt completeness, entity relationships, procedural authority, supplier episodes or cross-domain traversal.
8. **Fixtures are not uniformly separated by execution profile.** Honest demo labels help users but do not prevent live mutation or prove the production capability exists.

### Structural prevention

Adopt one production dependency-injection root that resolves GraphConfig once, requires the complete authoritative AGE capability set, injects it into every memory consumer, and disallows implicit local stores. Move test/demo constructors into explicitly named modules and profiles. Require a typed unavailable result or raised graph exception; no data-bearing default may represent an unavailable required read. Publish in-memory learning versions only after durable graph commits.

Add a **required, fail-on-skip CI job** running the five apps against one disposable AGE database and soc_graph. Assert the same redacted database/graph identity, each health alias's schema, fresh connectivity and complete learning/receipt state. Test an AGE outage at startup and during score/learn/transfer; assert no SQLite/fixture substitution, no accepted unpersisted ID and no changed in-memory learner after rejected work. Recovery/restart tests must reconstruct the same state solely from AGE.

Enforce a runtime module allowlist for SQLite/driver/file-store use, not a whole-file exception list. Each exemption needs an owner, purpose (test/demo/export/operator/cache), permitted entry points, expiry and a test proving it cannot become authoritative production memory. Add AST rules for broad catch-and-default and for construction of local stores outside test/demo boundaries; dynamic assertions and fault tests are still required.

Finally, use four mandatory **single graph traversal** acceptance cases, returning inspectable paths:

- Episode → Decision → verified Outcome, including acquired investigation evidence.
- Semantic entity/context → Decision → outcome-conditioned relevance.
- Procedure/variant/promotion → its supporting Decisions/receipts → current authority.
- Source-domain judgment/fingerprint → validated TransferPattern → target-domain judgment/checkpoint.

A health gate alone is necessary but insufficient: a connected graph with disconnected memory blobs or local fixture evidence can still pass it. Do not permit the claim “JM shared-graph implemented” until these traversals, durability, domain collision and outage tests all pass.

## Appendix Conventions and Remaining Uncertainty

The following indexes deliberately preserve noisy matches so nothing disappears behind a First-N sample. Counts: 889 SQLite-pattern hits in 178 files; 2,343 fixture/fallback-pattern hits in 488 files; 877 AST exception candidates; 548 additional memory/JSON-write hits in 243 files; 62 direct-driver import hits in 58 files. Counts describe this scan snapshot and include comments, serialized-property parsers, tools and archived material; they are **not extra confirmed gaps**.

Classification keys:

- **CONFIRMED / Gxxx:** linked to a specific remediation group; read the group for active versus latent reachability.
- **TEST/DEMO/OPERATOR:** not automatically a live Decision path. It must stay isolated; current reference/seed/tool gaps are separately counted.
- **IMPLEMENTATION:** legitimate adapter/local-store implementation exists; production construction/injection determines compliance.
- **FALSE-POSITIVE:** e.g. app.db module imports, self.db variable names or mere comments.
- **OPEN:** source candidate retained because runtime reachability/authority is not conclusively proved here. It is not approved for production. Resolve by tracing callers and fault-testing; if it carries judgment/episodic/semantic/procedural authority, migrate it to graph or gate it explicitly.

The full exception index gives each except line, selected calls in its try block and the handler outcome. It is an auditable candidate inventory, not a claim that every parse/import/cache exception is an AGE failure. A rethrow marker is not clearance when another branch can return a default.


## Appendix A — Complete SQLite / .db Reference Index

Each numbered hit is retained. C = comment/doc-only candidate; M = module/member .db false-positive; R = executable/local-store/config reference requiring the file disposition. C is not automatic clearance for the surrounding function. Historical filenames passed into an AGE-selected factory are not proof that SQLite is active.

### ci-platform/prompt0_ci_structural_map.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `ci-platform/prompt0_ci_structural_map.py:4` [R] import sqlite3
- `ci-platform/prompt0_ci_structural_map.py:7` [R] db_path = os.path.join(".code-review-graph", "graph.db")
- `ci-platform/prompt0_ci_structural_map.py:12` [R] conn = sqlite3.connect(db_path)
- `ci-platform/prompt0_ci_structural_map.py:13` [R] conn.row_factory = sqlite3.Row

### copilot-sdk/apps/dataops/backend/app/dataops_governance.py

CONFIRMED family / G027; individual branches may be test/demo/parser-only.

- `copilot-sdk/apps/dataops/backend/app/dataops_governance.py:6` [R] import sqlite3
- `copilot-sdk/apps/dataops/backend/app/dataops_governance.py:30` [R] self._db = sqlite3.connect(str(db_path), check_same_thread=False)
- `copilot-sdk/apps/dataops/backend/app/dataops_governance.py:31` [R] self._db.row_factory = sqlite3.Row
- `copilot-sdk/apps/dataops/backend/app/dataops_governance.py:41` [R] except sqlite3.OperationalError:
- `copilot-sdk/apps/dataops/backend/app/dataops_governance.py:44` [R] self._outcomes = GraphOutcomeLedger(graph_store, "dataops") if age_events else OutcomeLedger(":memory:" if str(db_path) == ":memory:" else str(Path(db_path).with_name("dataops_outcomes.sqlite3")))
- `copilot-sdk/apps/dataops/backend/app/dataops_governance.py:76` [R] def _rows(self, source_id: str   None = None) -> list[sqlite3.Row]:
- `copilot-sdk/apps/dataops/backend/app/dataops_governance.py:203` [R] def _row_payload(row: sqlite3.Row) -> dict[str, Any]:

### copilot-sdk/apps/dataops/backend/app/graph_queries.py

CONFIRMED family / G043, G051; individual branches may be test/demo/parser-only.

- `copilot-sdk/apps/dataops/backend/app/graph_queries.py:39` [R] "CI_ALLOW_SQLITE_FALLBACK",

### copilot-sdk/apps/dataops/backend/app/graph_status.py

CONFIRMED family / G066; individual branches may be test/demo/parser-only.

- `copilot-sdk/apps/dataops/backend/app/graph_status.py:20` [R] "Historical SQLite records are not visible in AGE-active mode unless migrated."
- `copilot-sdk/apps/dataops/backend/app/graph_status.py:76` [R] "DATAOPS_SHARED_GRAPH_AUTHORIZED", "CI_ALLOW_SQLITE_FALLBACK",
- `copilot-sdk/apps/dataops/backend/app/graph_status.py:92` [R] os.environ["DATAOPS_ACTIVE_GRAPH_BACKEND"] = "sqlite"
- `copilot-sdk/apps/dataops/backend/app/graph_status.py:93` [R] os.environ["CI_ALLOW_SQLITE_FALLBACK"] = "1"
- `copilot-sdk/apps/dataops/backend/app/graph_status.py:117` [R] requested_backend: str = "sqlite"
- `copilot-sdk/apps/dataops/backend/app/graph_status.py:134` [R] message = "DATAOPS_ACTIVE_GRAPH_BACKEND must be 'sqlite' or 'age'"
- `copilot-sdk/apps/dataops/backend/app/graph_status.py:152` [R] if self.requested_backend not in {"sqlite", "age"}:
- `copilot-sdk/apps/dataops/backend/app/graph_status.py:154` [R] "DATAOPS_ACTIVE_GRAPH_BACKEND must be 'sqlite' or 'age'"
- `copilot-sdk/apps/dataops/backend/app/graph_status.py:156` [R] if self.requested_backend == "sqlite":
- `copilot-sdk/apps/dataops/backend/app/graph_status.py:366` [R] "active_backend": "age" if age_active else "sqlite",
- `copilot-sdk/apps/dataops/backend/app/graph_status.py:368` [R] "sqlite_authoritative": not age_active,
- `copilot-sdk/apps/dataops/backend/app/graph_status.py:371` [R] "graph_kind": "sqlite" if not requested_age else graph_kind,
- `copilot-sdk/apps/dataops/backend/app/graph_status.py:384` [R] "Unset DATAOPS_ACTIVE_GRAPH_BACKEND or set it to sqlite.",
- `copilot-sdk/apps/dataops/backend/app/graph_status.py:386` [R] "Rollback routes new scorer writes to SQLite; it does not reconcile AGE data.",
- `copilot-sdk/apps/dataops/backend/app/graph_status.py:396` [R] else "DataOps SQLite remains authoritative for scorer decisions.",
- `copilot-sdk/apps/dataops/backend/app/graph_status.py:398` [R] "Historical SQLite migration/backfill is not in scope.",

### copilot-sdk/apps/dataops/backend/app/main.py

CONFIRMED family / G024, G026, G027, G043, G047, G048, G051; individual branches may be test/demo/parser-only.

- `copilot-sdk/apps/dataops/backend/app/main.py:8` [R] import sqlite3
- `copilot-sdk/apps/dataops/backend/app/main.py:80` [R] from copilot_sdk.backend.signal_store import SQLiteSignalStore, shared_signal_path  # noqa: E402
- `copilot-sdk/apps/dataops/backend/app/main.py:117` [R] self.conn = sqlite3.connect(path, check_same_thread=False)
- `copilot-sdk/apps/dataops/backend/app/main.py:140` [R] if os.environ.get("CI_ALLOW_SQLITE_FALLBACK") == "1":
- `copilot-sdk/apps/dataops/backend/app/main.py:149` [R] DB_FILENAME = "dataops.db"
- `copilot-sdk/apps/dataops/backend/app/main.py:194` [R] backend = "sqlite"
- `copilot-sdk/apps/dataops/backend/app/main.py:732` [R] governance_db = ":memory:" if scoring_db == ":memory:" else str(DATA_DIR / "dataops_governance.sqlite3")
- `copilot-sdk/apps/dataops/backend/app/main.py:872` [R] create_cross_signal_router(SQLiteSignalStore(shared_signal_path())), prefix="/api"
- `copilot-sdk/apps/dataops/backend/app/main.py:991` [R] **_vld_k_router_kwargs(DATA_DIR / "k_utility.db", len(FACTOR_NAMES)),

### copilot-sdk/apps/purchasing/backend/app/graph_status.py

CONFIRMED family / G066; individual branches may be test/demo/parser-only.

- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:21` [R] "Historical SQLite records are not visible in AGE-active mode unless migrated."
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:78` [R] "CI_ALLOW_SQLITE_FALLBACK",
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:94` [R] os.environ["PURCHASING_ACTIVE_GRAPH_BACKEND"] = "sqlite"
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:95` [R] os.environ["CI_ALLOW_SQLITE_FALLBACK"] = "1"
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:119` [R] requested_backend: str = "sqlite"
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:138` [R] message = "PURCHASING_ACTIVE_GRAPH_BACKEND must be 'sqlite' or 'age'"
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:155` [R] if self.requested_backend not in {"sqlite", "age", "dual_write"}:
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:157` [R] "PURCHASING_ACTIVE_GRAPH_BACKEND must be 'sqlite', 'age', or 'dual_write'"
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:159` [R] if self.requested_backend == "sqlite":
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:408` [R] else "sqlite"
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:421` [R] "sqlite_authoritative": active_backend == "sqlite",
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:426` [R] "graph_kind": "sqlite" if not requested_age else graph_kind,
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:437` [R] "Unset PURCHASING_ACTIVE_GRAPH_BACKEND or set it to sqlite.",
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:439` [R] "Rollback routes new writes to SQLite; it does not reconcile AGE data.",
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:449` [R] else "Purchasing SQLite remains authoritative.",
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py:450` [R] "Historical SQLite migration/backfill is not in scope.",

### copilot-sdk/apps/purchasing/backend/app/main.py

CONFIRMED family / G013, G024, G026, G033, G048, G050; individual branches may be test/demo/parser-only.

- `copilot-sdk/apps/purchasing/backend/app/main.py:8` [R] import sqlite3
- `copilot-sdk/apps/purchasing/backend/app/main.py:102` [R] from copilot_sdk.backend.signal_store import SQLiteSignalStore, shared_signal_path  # noqa: E402
- `copilot-sdk/apps/purchasing/backend/app/main.py:135` [R] if os.environ.get("CI_ALLOW_SQLITE_FALLBACK") == "1":
- `copilot-sdk/apps/purchasing/backend/app/main.py:147` [R] DB_FILENAME = "purchasing.db"
- `copilot-sdk/apps/purchasing/backend/app/main.py:152` [R] self.conn = sqlite3.connect(path, check_same_thread=False)
- `copilot-sdk/apps/purchasing/backend/app/main.py:161` [R] OUTBOX_DB_FILENAME = "purchasing_outbox.db"
- `copilot-sdk/apps/purchasing/backend/app/main.py:229` [R] backend = "sqlite"
- `copilot-sdk/apps/purchasing/backend/app/main.py:849` [R] create_cross_signal_router(SQLiteSignalStore(shared_signal_path())), prefix="/api"
- `copilot-sdk/apps/purchasing/backend/app/main.py:872` [R] **_vld_k_router_kwargs(DATA_DIR / "k_utility.db", PurchasingPreset().shape.n_factors),

### copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py

CONFIRMED family / G013, G028; individual branches may be test/demo/parser-only.

- `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:7` [R] import sqlite3
- `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:136` [R] self._db = sqlite3.connect(self.path, check_same_thread=False)
- `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:137` [R] self._db.row_factory = sqlite3.Row
- `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:159` [R] self.proof = GraphProofLedger(graph_store, "purchasing") if age_events else ProofLedger(data_dir / "purchasing_proof_ledger.sqlite3")
- `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:160` [R] self.outcomes = GraphOutcomeLedger(graph_store, "purchasing") if age_events else OutcomeLedger(data_dir / "purchasing_verified_outcomes.sqlite3")

### copilot-sdk/apps/purchasing/backend/cli.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/apps/purchasing/backend/cli.py:39` [R] DEFAULT_DB_PATH = BACKEND_ROOT / "data" / "purchasing.db"
- `copilot-sdk/apps/purchasing/backend/cli.py:54` [R] backend="sqlite",
- `copilot-sdk/apps/purchasing/backend/cli.py:293` [R] help="SQLite scorer state path.",

### copilot-sdk/apps/regime_experiment/experiment.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/apps/regime_experiment/experiment.py:22` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/apps/regime_experiment/experiment.py:120` [R] def _new_scorer(db_path: str) -> tuple[CompoundingScorer, SQLiteGraphStore]:
- `copilot-sdk/apps/regime_experiment/experiment.py:121` [R] store = SQLiteGraphStore(db_path, domain="trading")
- `copilot-sdk/apps/regime_experiment/experiment.py:143` [C] """Run one arm with an isolated SQLite store."""
- `copilot-sdk/apps/regime_experiment/experiment.py:148` [R] os.environ["CI_PERSISTENCE_OUTBOX_PATH"] = str(temp_dir / "outbox.db")
- `copilot-sdk/apps/regime_experiment/experiment.py:149` [R] scorer, store = _new_scorer(str(temp_dir / "arm.db"))

### copilot-sdk/apps/s2p_differentiation/engine.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/apps/s2p_differentiation/engine.py:19` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/apps/s2p_differentiation/engine.py:178` [R] store = SQLiteGraphStore(path, domain="s2p")
- `copilot-sdk/apps/s2p_differentiation/engine.py:243` [R] scorer = _make_scorer(path / "tg1.db", enable_rl=True)
- `copilot-sdk/apps/s2p_differentiation/engine.py:278` [R] ci = _make_scorer(output / "ci.db", enable_rl=True)
- `copilot-sdk/apps/s2p_differentiation/engine.py:279` [R] hand = _make_scorer(output / "hand_specified.db", enable_rl=False)

### copilot-sdk/apps/trading/backend/app/cli_sdk.py

CONFIRMED family / G063; individual branches may be test/demo/parser-only.

- `copilot-sdk/apps/trading/backend/app/cli_sdk.py:16` [R] import sqlite3
- `copilot-sdk/apps/trading/backend/app/cli_sdk.py:45` [C] """Load typed AGE graph configuration; never substitute SQLite."""
- `copilot-sdk/apps/trading/backend/app/cli_sdk.py:47` [R] DEFAULT_DB_PATH = os.path.expanduser("~/.ci-platform/trading/trading.db")
- `copilot-sdk/apps/trading/backend/app/cli_sdk.py:578` [R] backup_path = str(backup_dir / f"trading_{timestamp}.db")
- `copilot-sdk/apps/trading/backend/app/cli_sdk.py:591` [C] """Restore the SDK Trading DB from a validated SQLite backup."""
- `copilot-sdk/apps/trading/backend/app/cli_sdk.py:598` [R] conn = sqlite3.connect(backup_path)
- `copilot-sdk/apps/trading/backend/app/cli_sdk.py:600` [R] conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
- `copilot-sdk/apps/trading/backend/app/cli_sdk.py:601` [R] except sqlite3.DatabaseError:
- `copilot-sdk/apps/trading/backend/app/cli_sdk.py:606` [R] if _load_cli_graph_config(_cli_profile()).backend != "sqlite":
- `copilot-sdk/apps/trading/backend/app/cli_sdk.py:607` [R] return {"error": "SQLite restore is unavailable for AGE-backed Trading"}

### copilot-sdk/apps/trading/backend/app/graph_status.py

CONFIRMED family / G049, G055, G065; individual branches may be test/demo/parser-only.

- `copilot-sdk/apps/trading/backend/app/graph_status.py:19` [R] "Historical SQLite records are not visible in AGE-active mode unless migrated."
- `copilot-sdk/apps/trading/backend/app/graph_status.py:75` [R] "CI_ALLOW_SQLITE_FALLBACK",
- `copilot-sdk/apps/trading/backend/app/graph_status.py:83` [C] # expected_backend contract; no implicit SQLite fallback.
- `copilot-sdk/apps/trading/backend/app/graph_status.py:93` [C] # Preserve the historical explicit-test default of SQLite while
- `copilot-sdk/apps/trading/backend/app/graph_status.py:95` [R] os.environ["TRADING_ACTIVE_GRAPH_BACKEND"] = "sqlite"
- `copilot-sdk/apps/trading/backend/app/graph_status.py:96` [R] os.environ["CI_ALLOW_SQLITE_FALLBACK"] = "1"
- `copilot-sdk/apps/trading/backend/app/graph_status.py:120` [R] requested_backend: str = "sqlite"
- `copilot-sdk/apps/trading/backend/app/graph_status.py:137` [R] "TRADING_ACTIVE_GRAPH_BACKEND must be 'sqlite' or 'age'; "
- `copilot-sdk/apps/trading/backend/app/graph_status.py:156` [R] if self.requested_backend not in {"sqlite", "age", "dual_write"}:
- `copilot-sdk/apps/trading/backend/app/graph_status.py:158` [R] "TRADING_ACTIVE_GRAPH_BACKEND must be 'sqlite' or 'age'; "
- `copilot-sdk/apps/trading/backend/app/graph_status.py:161` [R] if self.requested_backend == "sqlite":
- `copilot-sdk/apps/trading/backend/app/graph_status.py:389` [R] else "sqlite"
- `copilot-sdk/apps/trading/backend/app/graph_status.py:409` [R] "sqlite_authoritative": not age_active,
- `copilot-sdk/apps/trading/backend/app/graph_status.py:414` [R] "graph_kind": "sqlite" if not requested_age else graph_kind,
- `copilot-sdk/apps/trading/backend/app/graph_status.py:425` [R] "Unset TRADING_ACTIVE_GRAPH_BACKEND or set it to sqlite.",
- `copilot-sdk/apps/trading/backend/app/graph_status.py:427` [R] "Rollback routes new writes to SQLite; it does not reconcile AGE data.",
- `copilot-sdk/apps/trading/backend/app/graph_status.py:437` [R] else "Trading SQLite remains authoritative.",
- `copilot-sdk/apps/trading/backend/app/graph_status.py:438` [R] "Historical SQLite migration/backfill is not in scope.",

### copilot-sdk/apps/trading/backend/app/main.py

CONFIRMED family / G023, G024, G026, G031, G048, G049, G058; individual branches may be test/demo/parser-only.

- `copilot-sdk/apps/trading/backend/app/main.py:8` [R] import sqlite3
- `copilot-sdk/apps/trading/backend/app/main.py:93` [R] from copilot_sdk.backend.signal_store import SQLiteSignalStore, shared_signal_path  # noqa: E402
- `copilot-sdk/apps/trading/backend/app/main.py:127` [R] if os.environ.get("CI_ALLOW_SQLITE_FALLBACK") == "1":
- `copilot-sdk/apps/trading/backend/app/main.py:131` [R] DB_FILENAME = "trading.db"
- `copilot-sdk/apps/trading/backend/app/main.py:140` [R] self.conn = sqlite3.connect(path, check_same_thread=False)
- `copilot-sdk/apps/trading/backend/app/main.py:188` [R] backend = "sqlite"
- `copilot-sdk/apps/trading/backend/app/main.py:584` [R] create_cross_signal_router(SQLiteSignalStore(shared_signal_path())), prefix="/api"
- `copilot-sdk/apps/trading/backend/app/main.py:595` [R] **_vld_k_router_kwargs(DATA_DIR / "k_utility.db", len(FACTOR_NAMES)),

### copilot-sdk/copilot_sdk/backend/cross_signal_router.py

CONFIRMED family / G026; individual branches may be test/demo/parser-only.

- `copilot-sdk/copilot_sdk/backend/cross_signal_router.py:20` [R] SQLiteSignalStore,
- `copilot-sdk/copilot_sdk/backend/cross_signal_router.py:57` [R] def create_cross_signal_router(store: SQLiteSignalStore   None = None) -> APIRouter:
- `copilot-sdk/copilot_sdk/backend/cross_signal_router.py:58` [C] """Inject a shared-file store; standalone callers default to isolated SQLite."""
- `copilot-sdk/copilot_sdk/backend/cross_signal_router.py:61` [R] signal_store = store if store is not None else SQLiteSignalStore()

### copilot-sdk/copilot_sdk/backend/signal_store.py

CONFIRMED family / G026; individual branches may be test/demo/parser-only.

- `copilot-sdk/copilot_sdk/backend/signal_store.py:1` [C] """SQLite-backed, bounded cross-application fact delivery."""
- `copilot-sdk/copilot_sdk/backend/signal_store.py:9` [R] import sqlite3
- `copilot-sdk/copilot_sdk/backend/signal_store.py:21` [R] default = Path(__file__).resolve().parents[2] / "data" / "shared_signals.db"
- `copilot-sdk/copilot_sdk/backend/signal_store.py:25` [R] class SQLiteSignalStore:
- `copilot-sdk/copilot_sdk/backend/signal_store.py:26` [C] """Atomic publication/eviction across processes sharing a SQLite file."""
- `copilot-sdk/copilot_sdk/backend/signal_store.py:32` [R] sqlite3.connect(":memory:", check_same_thread=False)
- `copilot-sdk/copilot_sdk/backend/signal_store.py:46` [R] def _connection(self) -> Iterator[sqlite3.Connection]:
- `copilot-sdk/copilot_sdk/backend/signal_store.py:48` [R] db = self._memory if self._memory is not None else sqlite3.connect(self.db_path, timeout=30)
- `copilot-sdk/copilot_sdk/backend/signal_store.py:57` [R] def _prune(db: sqlite3.Connection) -> None:
- `copilot-sdk/copilot_sdk/backend/signal_store.py:87` [R] except sqlite3.IntegrityError:

### copilot-sdk/copilot_sdk/config/graph_config.py

CONFIRMED family / G042, G043; individual branches may be test/demo/parser-only.

- `copilot-sdk/copilot_sdk/config/graph_config.py:19` [R] Backend = Literal["sqlite", "age", "dual_write"]
- `copilot-sdk/copilot_sdk/config/graph_config.py:237` [R] if self.backend not in {"sqlite", "age", "dual_write"}:
- `copilot-sdk/copilot_sdk/config/graph_config.py:239` [R] if self.expected_backend not in {"sqlite", "age", "dual_write"}:
- `copilot-sdk/copilot_sdk/config/graph_config.py:243` [R] if self.expected_backend == "age" and self.backend == "sqlite":
- `copilot-sdk/copilot_sdk/config/graph_config.py:244` [R] allowed = profile == "development" and os.environ.get("CI_ALLOW_SQLITE_FALLBACK") == "1"
- `copilot-sdk/copilot_sdk/config/graph_config.py:247` [R] f"expected backend age but resolved sqlite for domain '{self.domain}'"

### copilot-sdk/copilot_sdk/demo/bundle.py

CONFIRMED family / G058; individual branches may be test/demo/parser-only.

- `copilot-sdk/copilot_sdk/demo/bundle.py:1` [C] """Restore demo state bundles into a cold SQLite graph store."""
- `copilot-sdk/copilot_sdk/demo/bundle.py:13` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/copilot_sdk/demo/bundle.py:49` [R] sqlite_store = _sqlite_restore_store(store)
- `copilot-sdk/copilot_sdk/demo/bundle.py:52` [R] current = int(sqlite_store.count_decisions(domain))
- `copilot-sdk/copilot_sdk/demo/bundle.py:58` [R] connection = _sqlite_connection(sqlite_store)
- `copilot-sdk/copilot_sdk/demo/bundle.py:59` [R] lock = getattr(sqlite_store, "_lock", None)
- `copilot-sdk/copilot_sdk/demo/bundle.py:61` [R] LOGGER.warning("Demo bundle restore requires a direct-write SQLiteGraphStore")
- `copilot-sdk/copilot_sdk/demo/bundle.py:155` [R] LOGGER.info("Bundle restored to SQLite. AGE migration required for graph parity.")
- `copilot-sdk/copilot_sdk/demo/bundle.py:159` [R] def _sqlite_connection(store: Any) -> Any   None:
- `copilot-sdk/copilot_sdk/demo/bundle.py:173` [R] def _sqlite_restore_store(store: Any) -> Any:
- `copilot-sdk/copilot_sdk/demo/bundle.py:174` [C] """Use the SQLite primary when bundle restore receives a dual-write store."""

### copilot-sdk/copilot_sdk/evolution/__init__.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `copilot-sdk/copilot_sdk/evolution/__init__.py:31` [R] SQLiteVariantStore,
- `copilot-sdk/copilot_sdk/evolution/__init__.py:55` [R] "SQLiteVariantStore",

### copilot-sdk/copilot_sdk/evolution/graph_store.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `copilot-sdk/copilot_sdk/evolution/graph_store.py:171` [C] # AGE returns newest first; SQLite returns the selected rows oldest first.

### copilot-sdk/copilot_sdk/evolution/variant_store.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `copilot-sdk/copilot_sdk/evolution/variant_store.py:10` [R] import sqlite3
- `copilot-sdk/copilot_sdk/evolution/variant_store.py:191` [R] class SQLiteVariantStore:
- `copilot-sdk/copilot_sdk/evolution/variant_store.py:192` [C] """SQLite-backed variant registry with restart-safe statistics.
- `copilot-sdk/copilot_sdk/evolution/variant_store.py:204` [R] self._connection = sqlite3.connect(
- `copilot-sdk/copilot_sdk/evolution/variant_store.py:209` [R] self._connection.row_factory = sqlite3.Row
- `copilot-sdk/copilot_sdk/evolution/variant_store.py:404` [R] def _row_to_spec(row: sqlite3.Row) -> VariantSpec:
- `copilot-sdk/copilot_sdk/evolution/variant_store.py:416` [R] def _row_to_global_stats(row: sqlite3.Row   None) -> VariantStats:

### copilot-sdk/copilot_sdk/framework/intervention_controls.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `copilot-sdk/copilot_sdk/framework/intervention_controls.py:41` [M] self.db = db_client
- `copilot-sdk/copilot_sdk/framework/intervention_controls.py:122` [M] result = await self.db.run_query(
- `copilot-sdk/copilot_sdk/framework/intervention_controls.py:151` [M] graph_service=self.db,
- `copilot-sdk/copilot_sdk/framework/intervention_controls.py:256` [M] rows = await self.db.run_query(
- `copilot-sdk/copilot_sdk/framework/intervention_controls.py:289` [M] rows = await self.db.run_query(
- `copilot-sdk/copilot_sdk/framework/intervention_controls.py:340` [M] await self.db.run_query(

### copilot-sdk/copilot_sdk/graph/__init__.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `copilot-sdk/copilot_sdk/graph/__init__.py:11` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/copilot_sdk/graph/__init__.py:25` [R] "SQLiteGraphStore",

### copilot-sdk/copilot_sdk/graph/dual_write_store.py

IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045).

- `copilot-sdk/copilot_sdk/graph/dual_write_store.py:19` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/copilot_sdk/graph/dual_write_store.py:61` [R] if isinstance(primary, SQLiteGraphStore) and isinstance(secondary, SQLiteGraphStore):
- `copilot-sdk/copilot_sdk/graph/dual_write_store.py:63` [R] "SQLite primary and secondary do not implement ProtocolV2GraphStore"

### copilot-sdk/copilot_sdk/graph/factory.py

CONFIRMED family / G042; individual branches may be test/demo/parser-only.

- `copilot-sdk/copilot_sdk/graph/factory.py:13` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/copilot_sdk/graph/factory.py:18` [R] _VALID_BACKENDS = {"sqlite", "age", "dual_write"}
- `copilot-sdk/copilot_sdk/graph/factory.py:66` [R] def _resolve_sqlite_path(
- `copilot-sdk/copilot_sdk/graph/factory.py:76` [R] return Path(ci_data_dir) / f"{domain}.db"
- `copilot-sdk/copilot_sdk/graph/factory.py:166` [R] and selected_backend == "sqlite"
- `copilot-sdk/copilot_sdk/graph/factory.py:169` [R] f"production domain '{domain}' resolved SQLite while AGE is expected"
- `copilot-sdk/copilot_sdk/graph/factory.py:183` [R] if selected_backend == "sqlite":
- `copilot-sdk/copilot_sdk/graph/factory.py:184` [R] sqlite_path = _resolve_sqlite_path(
- `copilot-sdk/copilot_sdk/graph/factory.py:190` [R] "creating SQLite GraphStore for domain=%s path=%s",
- `copilot-sdk/copilot_sdk/graph/factory.py:192` [R] sqlite_path,
- `copilot-sdk/copilot_sdk/graph/factory.py:196` [R] SQLiteGraphStore(
- `copilot-sdk/copilot_sdk/graph/factory.py:197` [R] sqlite_path,
- `copilot-sdk/copilot_sdk/graph/factory.py:204` [R] sqlite_path = _resolve_sqlite_path(
- `copilot-sdk/copilot_sdk/graph/factory.py:209` [R] primary = SQLiteGraphStore(
- `copilot-sdk/copilot_sdk/graph/factory.py:210` [R] sqlite_path,
- `copilot-sdk/copilot_sdk/graph/factory.py:264` [R] sqlite_path,
- `copilot-sdk/copilot_sdk/graph/factory.py:267` [R] outbox_path = Path(sqlite_path).parent / f"{selected_domain}_dual_write_outbox.db"

### copilot-sdk/copilot_sdk/graph/outbox.py

IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045).

- `copilot-sdk/copilot_sdk/graph/outbox.py:6` [R] import sqlite3
- `copilot-sdk/copilot_sdk/graph/outbox.py:16` [C] """SQLite-backed durable outbox for failed secondary writes."""
- `copilot-sdk/copilot_sdk/graph/outbox.py:22` [R] self._connection = sqlite3.connect(self.path, check_same_thread=False, timeout=30.0)
- `copilot-sdk/copilot_sdk/graph/outbox.py:23` [R] self._connection.row_factory = sqlite3.Row
- `copilot-sdk/copilot_sdk/graph/outbox.py:54` [R] def _row_to_entry(row: sqlite3.Row) -> dict[str, Any]:
- `copilot-sdk/copilot_sdk/graph/outbox.py:78` [R] raise RuntimeError("SQLite did not return an outbox row ID")

### copilot-sdk/copilot_sdk/graph/outcome_service.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `copilot-sdk/copilot_sdk/graph/outcome_service.py:24` [R] changing the real SQLite state store used for V and replay verification.

### copilot-sdk/copilot_sdk/graph/read_diff_runner.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `copilot-sdk/copilot_sdk/graph/read_diff_runner.py:15` [C] # These are semantic Decision fields common to SQLite and AGE return values.

### copilot-sdk/copilot_sdk/graph/sqlite_store.py

IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045).

- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1` [C] """Domain-scoped SQLite GraphStore implementation."""
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:7` [R] import sqlite3
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:31` [R] SQLITE_BUSY_TIMEOUT_MS = 5000
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:32` [R] SQLITE_LOCK_RETRY_DELAYS = (0.05, 0.1, 0.25, 0.5)
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:388` [R] def _is_transient_sqlite_lock(error: sqlite3.OperationalError) -> bool:
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:393` [R] class SQLiteGraphStore:
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:394` [C] """SQLite-backed GraphStore that owns decisions, outcomes, and graph tables."""
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:402` [R] self._conn: sqlite3.Connection   None = sqlite3.connect(
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:405` [R] timeout=SQLITE_BUSY_TIMEOUT_MS / 1000,
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:407` [R] self._conn.row_factory = sqlite3.Row
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:408` [R] self._conn.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:427` [R] def connection(self) -> sqlite3.Connection:
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:429` [R] raise RuntimeError("SQLiteGraphStore is closed")
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1170` [R] delays = (0.0, *SQLITE_LOCK_RETRY_DELAYS)
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1180` [R] except sqlite3.OperationalError as error:
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1182` [R] if not _is_transient_sqlite_lock(error) or attempt == len(delays) - 1:
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1187` [R] raise RuntimeError("SQLite write retry loop exited unexpectedly")
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:3727` [R] def _decision_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:3762` [R] def _verified_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:3778` [R] def _archived_decision_from_row(row: sqlite3.Row) -> dict[str, Any]:
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:3779` [C] """Normalize the denormalized SQLite archive row for history reads."""
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:3802` [R] def _entity_enrichment_record_from_row(self, row: sqlite3.Row) -> EntityEnrichmentRecord:
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:3819` [R] def _checkpoint_from_row(self, row: sqlite3.Row) -> dict[str, Any]:

### copilot-sdk/copilot_sdk/migrate/__main__.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/copilot_sdk/migrate/__main__.py:11` [R] from .sqlite_to_age import _default_source_path, run_migration
- `copilot-sdk/copilot_sdk/migrate/__main__.py:18` [R] sqlite_to_age = subparsers.add_parser(
- `copilot-sdk/copilot_sdk/migrate/__main__.py:19` [R] "sqlite_to_age",
- `copilot-sdk/copilot_sdk/migrate/__main__.py:20` [R] help="Migrate verified SQLite decision logs into AGE Decision nodes.",
- `copilot-sdk/copilot_sdk/migrate/__main__.py:22` [R] sqlite_to_age.add_argument("--domain", required=True)
- `copilot-sdk/copilot_sdk/migrate/__main__.py:23` [R] sqlite_to_age.add_argument("--source", default=None)
- `copilot-sdk/copilot_sdk/migrate/__main__.py:24` [R] sqlite_to_age.add_argument("--age-dsn", required=True)
- `copilot-sdk/copilot_sdk/migrate/__main__.py:25` [R] sqlite_to_age.add_argument("--graph-name", default="soc_graph")
- `copilot-sdk/copilot_sdk/migrate/__main__.py:26` [R] sqlite_to_age.add_argument("--dry-run", action="store_true")
- `copilot-sdk/copilot_sdk/migrate/__main__.py:27` [R] sqlite_to_age.add_argument(
- `copilot-sdk/copilot_sdk/migrate/__main__.py:32` [R] sqlite_to_age.add_argument(
- `copilot-sdk/copilot_sdk/migrate/__main__.py:37` [R] sqlite_to_age.add_argument("--batch-size", type=int, default=1000)
- `copilot-sdk/copilot_sdk/migrate/__main__.py:38` [R] sqlite_to_age.add_argument(
- `copilot-sdk/copilot_sdk/migrate/__main__.py:43` [R] sqlite_to_age.add_argument("--no-verify", action="store_true")
- `copilot-sdk/copilot_sdk/migrate/__main__.py:44` [R] sqlite_to_age.add_argument(
- `copilot-sdk/copilot_sdk/migrate/__main__.py:52` [R] help="Mark AGE Decisions archived when SQLite has archived their IDs.",
- `copilot-sdk/copilot_sdk/migrate/__main__.py:68` [R] if args.command == "sqlite_to_age":
- `copilot-sdk/copilot_sdk/migrate/__main__.py:91` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/copilot_sdk/migrate/__main__.py:94` [R] sqlite_store = SQLiteGraphStore(args.source, domain=args.domain)
- `copilot-sdk/copilot_sdk/migrate/__main__.py:97` [R] reconciler = ArchiveReconciler(sqlite_store, age_store, args.domain)
- `copilot-sdk/copilot_sdk/migrate/__main__.py:110` [R] sqlite_store.close()

### copilot-sdk/copilot_sdk/migrate/reconcile_archive.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py:1` [C] """Resumable baseline reconciliation for SQLite and AGE archive state."""
- `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py:16` [C] """Mark AGE Decisions archived when SQLite has archived the same IDs."""
- `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py:20` [R] sqlite_store: Any,
- `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py:25` [R] self.sqlite_store = sqlite_store
- `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py:28` [R] data_dir = Path(getattr(sqlite_store, "db_path", ".")).parent
- `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py:51` [R] for record in self.sqlite_store.get_archived_decisions(self.domain)
- `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py:60` [R] raise ValueError("reconciliation checkpoint source IDs do not match SQLite archive")
- `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py:68` [R] "total_sqlite_archived": len(source_ids),
- `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py:110` [R] f"{report['not_found_in_age']} SQLite archived decision IDs were not found in AGE"
- `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py:124` [R] runner = ReadDiffRunner(self.sqlite_store, self.age_store, self.domain)
- `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py:156` [R] d.archive_reason = 'sqlite_baseline_reconciliation',
- `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py:201` [R] "source_sqlite_archive_count": report["total_sqlite_archived"],

### copilot-sdk/copilot_sdk/migrate/scratch_graph.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/copilot_sdk/migrate/scratch_graph.py:1` [C] """Scratch AGE graph helpers for SQLite-to-AGE migration validation."""
- `copilot-sdk/copilot_sdk/migrate/scratch_graph.py:145` [R] from copilot_sdk.migrate.sqlite_to_age import _write_batch

### copilot-sdk/copilot_sdk/migrate/shadow_scorer.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:1` [C] """Shadow scorer discipline for SQLite-to-AGE backend validation.

### copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1` [C] """SQLite decision-log to AGE topology migration.
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:17` [R] import sqlite3
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:75` [R] return Path(os.path.expanduser("~")) / ".ci-platform" / domain / f"{domain}.db"
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:99` [R] with sqlite3.connect(db_path) as conn:
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:100` [R] conn.row_factory = sqlite3.Row
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:106` [R] with sqlite3.connect(db_path) as conn:
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:107` [R] conn.row_factory = sqlite3.Row
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:109` [R] "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'outcomes'"
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:117` [R] def _table_columns(conn: sqlite3.Connection, table: str) -> tuple[str, ...]:
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:118` [C] """Read a fixed SQLite table's columns without assuming schema versions."""
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:123` [R] conn: sqlite3.Connection,
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:146` [C] """Produce governed Decision properties while retaining SQLite source fields."""
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:167` [R] "migration_source": "sqlite",
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:177` [C] """Read schema-adaptive decision topology records in SQLite rowid order."""
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:179` [R] with sqlite3.connect(db_path) as conn:
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:180` [R] conn.row_factory = sqlite3.Row
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:240` [R] conn: sqlite3.Connection, domain: str
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:242` [C] """Read denormalized SQLite archive rows as final archived AGE topology."""
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:244` [R] conn.row_factory = sqlite3.Row
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:335` [C] """Compare optional integer fields across SQLite and AGE representations."""
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:351` [C] """Normalize SQLite INTEGER/TEXT truth values for AGE Outcome properties."""
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:364` [C] """Map SQLite decision/outcome columns to AGE Decision properties."""
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:463` [R] "Decision": _age_topology_count(conn, graph_name, f"MATCH (d:Decision {{domain: {domain_literal}, migration_source: 'sqlite'}}) RETURN count(d) AS cnt"),
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:464` [R] "Outcome": _age_topology_count(conn, graph_name, f"MATCH (o:Outcome {{domain: {domain_literal}, migration_source: 'sqlite'}}) RETURN count(o) AS cnt"),
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:465` [R] "HAS_OUTCOME": _age_topology_count(conn, graph_name, f"MATCH (d:Decision {{domain: {domain_literal}, migration_source: 'sqlite'}})-[r:HAS_OUTCOME]->(o:Outcome {{domain: {domain_literal}, migration_source: 'sqlite'}}) RET
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:466` [R] "CentroidCheckpoint": _age_topology_count(conn, graph_name, f"MATCH (c:CentroidCheckpoint {{domain: {domain_literal}, migration_source: 'sqlite'}}) RETURN count(c) AS cnt"),
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:467` [R] "EvidenceReceipt": _age_topology_count(conn, graph_name, f"MATCH (r:EvidenceReceipt {{domain: {domain_literal}, migration_source: 'sqlite'}}) RETURN count(r) AS cnt"),
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:479` [R] f"MATCH (d:Decision {{domain: {domain_literal}, decision_id: {_S(decision_id)}, migration_source: 'sqlite'}}) "
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:510` [R] "Decision": _age_topology_count(conn, graph_name, f"MATCH (d:Decision {{domain: {domain_literal}, migration_source: 'sqlite'}}) WHERE d.archived = true RETURN count(d) AS cnt"),
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:511` [R] "Outcome": _age_topology_count(conn, graph_name, f"MATCH (d:Decision {{domain: {domain_literal}, migration_source: 'sqlite'}})-[:HAS_OUTCOME]->(o:Outcome {{domain: {domain_literal}, migration_source: 'sqlite'}}) WHERE d.
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:512` [R] "HAS_OUTCOME": _age_topology_count(conn, graph_name, f"MATCH (d:Decision {{domain: {domain_literal}, migration_source: 'sqlite'}})-[r:HAS_OUTCOME]->(:Outcome) WHERE d.archived = true RETURN count(r) AS cnt"),
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:601` [R] "migration_source": "sqlite",
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:628` [R] {"domain": domain, "decision_id": decision_id, "migration_source": "sqlite", "migration_ts": properties.get("migration_ts")}
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:650` [R] {"domain": domain, "decision_id": decision_id, "migration_source": "sqlite", "migration_ts": properties.get("migration_ts")}
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:754` [R] def _sqlite_level1_summary(db_path: str, domain: str) -> dict[str, Any]:
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:755` [R] with sqlite3.connect(db_path) as conn:
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:785` [R] sqlite_summary = _sqlite_level1_summary(db_path, domain)
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:788` [R] int(age_summary["count"] or 0) == int(sqlite_summary["count"] or 0)
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:789` [R] and _float_equal(age_summary["first_created_at"], sqlite_summary["first_created_at"])
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:790` [R] and _float_equal(age_summary["last_created_at"], sqlite_summary["last_created_at"])
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:792` [R] return {"passed": passed, "details": {"sqlite": sqlite_summary, "age": age_summary}}
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:799` [R] with sqlite3.connect(db_path) as source_conn:
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:801` [R] sqlite_count = (
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:806` [R] f"MATCH (d:Decision {{domain: {_S(domain)}, migration_source: 'sqlite'}}) "
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:810` [R] return {"passed": sqlite_count == age_count, "details": {"sqlite": sqlite_count, "age": age_count}}
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1015` [R] with sqlite3.connect(source_db) as source_conn:
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1115` [R] logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1149` [R] logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1193` [R] logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1201` [R] logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1209` [R] logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1218` [R] logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1226` [R] logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1233` [R] logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1241` [R] logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1252` [R] logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1266` [R] "SQLite to AGE migration retained scratch graph %s after %s live copy errors",
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1277` [R] "SQLite to AGE migration retained scratch graph %s after live copy failure: %s",
- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1293` [R] logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])

### copilot-sdk/copilot_sdk/migrate/verify_state.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/copilot_sdk/migrate/verify_state.py:371` [R] label_a: str = "sqlite",
- `copilot-sdk/copilot_sdk/migrate/verify_state.py:486` [C] """Run Level 3 state-vector verification for SQLite vs AGE logs."""
- `copilot-sdk/copilot_sdk/migrate/verify_state.py:487` [R] from copilot_sdk.migrate.sqlite_to_age import _read_outcomes, _read_verified_decisions
- `copilot-sdk/copilot_sdk/migrate/verify_state.py:489` [R] sqlite_decisions = _read_verified_decisions(source_db)
- `copilot-sdk/copilot_sdk/migrate/verify_state.py:491` [R] if len(sqlite_decisions) != len(age_decisions):
- `copilot-sdk/copilot_sdk/migrate/verify_state.py:496` [R] "sqlite_count": len(sqlite_decisions),
- `copilot-sdk/copilot_sdk/migrate/verify_state.py:501` [R] sqlite_state = replay_decisions(
- `copilot-sdk/copilot_sdk/migrate/verify_state.py:502` [R] sqlite_decisions,
- `copilot-sdk/copilot_sdk/migrate/verify_state.py:513` [R] comparison = compare_states(sqlite_state, age_state)

### copilot-sdk/copilot_sdk/outbox/__init__.py

IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045).

- `copilot-sdk/copilot_sdk/outbox/__init__.py:1` [C] """SQLite outbox replay worker public API."""

### copilot-sdk/copilot_sdk/outbox/cli.py

IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045).

- `copilot-sdk/copilot_sdk/outbox/cli.py:19` [R] return Path.home() / ".ci-platform" / safe_domain / f"{safe_domain}_outbox.db"

### copilot-sdk/copilot_sdk/outbox/store.py

IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045).

- `copilot-sdk/copilot_sdk/outbox/store.py:1` [C] """SQLite-backed outbox store."""
- `copilot-sdk/copilot_sdk/outbox/store.py:6` [R] import sqlite3
- `copilot-sdk/copilot_sdk/outbox/store.py:16` [C] """SQLite-backed outbox table stored separately from GraphStore."""
- `copilot-sdk/copilot_sdk/outbox/store.py:22` [R] self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
- `copilot-sdk/copilot_sdk/outbox/store.py:23` [R] self._conn.row_factory = sqlite3.Row
- `copilot-sdk/copilot_sdk/outbox/store.py:176` [C] """Close the underlying SQLite connection."""
- `copilot-sdk/copilot_sdk/outbox/store.py:182` [R] def _from_row(row: sqlite3.Row) -> OutboxEvent:

### copilot-sdk/copilot_sdk/outcome/ledger.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `copilot-sdk/copilot_sdk/outcome/ledger.py:1` [C] """SQLite persistence for canonical verified-outcome receipts."""
- `copilot-sdk/copilot_sdk/outcome/ledger.py:7` [R] import sqlite3
- `copilot-sdk/copilot_sdk/outcome/ledger.py:21` [R] self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
- `copilot-sdk/copilot_sdk/outcome/ledger.py:22` [R] self._connection.row_factory = sqlite3.Row

### copilot-sdk/copilot_sdk/pilot/transfer.py

CONFIRMED family / G045; individual branches may be test/demo/parser-only.

- `copilot-sdk/copilot_sdk/pilot/transfer.py:12` [R] import sqlite3
- `copilot-sdk/copilot_sdk/pilot/transfer.py:47` [C] """Thread-safe SQLite persistence for pilot sessions and paired outcomes."""
- `copilot-sdk/copilot_sdk/pilot/transfer.py:50` [R] self._connection = sqlite3.connect(db_path, check_same_thread=False)

### copilot-sdk/copilot_sdk/promotion/core.py

CONFIRMED family / G045; individual branches may be test/demo/parser-only.

- `copilot-sdk/copilot_sdk/promotion/core.py:6` [R] import sqlite3
- `copilot-sdk/copilot_sdk/promotion/core.py:111` [C] """SQLite-backed persistence for promotion records."""
- `copilot-sdk/copilot_sdk/promotion/core.py:114` [R] self._connection = sqlite3.connect(db_path, check_same_thread=False)

### copilot-sdk/copilot_sdk/scoring/persistence_outbox.py

CONFIRMED family / G002, G055; individual branches may be test/demo/parser-only.

- `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:8` [R] import sqlite3
- `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:51` [R] or Path.home() / ".ci-platform" / self.domain / "outbox.db"
- `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:57` [R] Path(tempfile.gettempdir()) / ".ci-platform" / self.domain / "outbox.db"
- `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:127` [R] def _connect(self) -> sqlite3.Connection:
- `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:128` [R] connection = sqlite3.connect(self.db_path, timeout=30.0)
- `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:129` [R] connection.row_factory = sqlite3.Row
- `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:242` [C] # The claim spans SELECT, graph replay and acknowledgement. SQLite WAL

### copilot-sdk/copilot_sdk/scoring/scorer.py

CONFIRMED family / G001, G002, G003, G004, G006, G042, G044, G055; individual branches may be test/demo/parser-only.

- `copilot-sdk/copilot_sdk/scoring/scorer.py:280` [R] db_path = str(data_dir / f"{domain}.db")
- `copilot-sdk/copilot_sdk/scoring/scorer.py:292` [C] # Development-only SQLite fallback; production requires an injected
- `copilot-sdk/copilot_sdk/scoring/scorer.py:294` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/copilot_sdk/scoring/scorer.py:298` [R] SQLiteGraphStore(db_path, domain=preset.name),
- `copilot-sdk/copilot_sdk/scoring/scorer.py:303` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/copilot_sdk/scoring/scorer.py:306` [R] if isinstance(graph_store, (SQLiteGraphStore, InMemoryGraphStore)):
- `copilot-sdk/copilot_sdk/scoring/scorer.py:309` [R] "SQLite and InMemoryGraphStore are test/development stores."
- `copilot-sdk/copilot_sdk/scoring/scorer.py:313` [R] (SQLiteGraphStore, InMemoryGraphStore),
- `copilot-sdk/copilot_sdk/scoring/scorer.py:317` [R] "dual-write stores with a SQLite or in-memory primary are "

### copilot-sdk/copilot_sdk/transfer/entity_edges.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `copilot-sdk/copilot_sdk/transfer/entity_edges.py:60` [R] which keeps the shared AGE/SQLite/Memory contract identical.

### copilot-sdk/demo.py

CONFIRMED family / G054, G057, G063; individual branches may be test/demo/parser-only.

- `copilot-sdk/demo.py:224` [R] ("trading-clone", "examples/trading_clone", "examples.trading_clone.run", "SQLite-backed Trading clone"),
- `copilot-sdk/demo.py:1643` [R] SCRIPT_DIR / "data" / "shared_signals.db",
- `copilot-sdk/demo.py:1645` [R] for pattern in ("apps/*/backend/data/*.db",
- `copilot-sdk/demo.py:1646` [R] "apps/*/backend/data/*.db-wal",
- `copilot-sdk/demo.py:1647` [R] "apps/*/backend/data/*.db-shm"):

### copilot-sdk/examples/build_your_own/engine.py

CONFIRMED family / G059; individual branches may be test/demo/parser-only.

- `copilot-sdk/examples/build_your_own/engine.py:3` [R] The governed arm uses the real CompoundingScorer and SQLiteGraphStore. The
- `copilot-sdk/examples/build_your_own/engine.py:19` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/examples/build_your_own/engine.py:89` [R] store = SQLiteGraphStore(work_dir / "decisions.sqlite", domain=preset.name)

### copilot-sdk/examples/build_your_own/run.py

CONFIRMED family / G059; individual branches may be test/demo/parser-only.

- `copilot-sdk/examples/build_your_own/run.py:30` [C] # The shared engine wires CompoundingScorer, conservation, SQLite, and

### copilot-sdk/examples/jm_reference/report.py

DEMO/REFERENCE — local simulation/artifact path; see G057–G059.

- `copilot-sdk/examples/jm_reference/report.py:191` [R] <p>Oracle-separated synthetic reference run; SQLite-backed, zero server.</p>

### copilot-sdk/examples/jm_reference/run.py

CONFIRMED family / G059; individual branches may be test/demo/parser-only.

- `copilot-sdk/examples/jm_reference/run.py:1` [C] """JM Reference App — the real SQLite-backed compounding loop.
- `copilot-sdk/examples/jm_reference/run.py:8` [R] ''SQLiteGraphStore''.  ''CompoundingScorer.learn'' performs the real outcome
- `copilot-sdk/examples/jm_reference/run.py:24` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/examples/jm_reference/run.py:68` [R] def _evolution_events(store: SQLiteGraphStore, domain: str) -> list[dict[str, Any]]:
- `copilot-sdk/examples/jm_reference/run.py:82` [R] db_path = str(Path(tempfile.mkdtemp(prefix=f"jm_{label}_")) / f"{label}.db")
- `copilot-sdk/examples/jm_reference/run.py:83` [R] store = SQLiteGraphStore(db_path, domain="trading")
- `copilot-sdk/examples/jm_reference/run.py:85` [R] outbox_path = str(Path(db_path).with_name(f"{label}_outbox.db"))
- `copilot-sdk/examples/jm_reference/run.py:91` [C] # SQLite is intentionally a standalone reference-app store; the SDK

### copilot-sdk/examples/trading_clone/run.py

CONFIRMED family / G059; individual branches may be test/demo/parser-only.

- `copilot-sdk/examples/trading_clone/run.py:1` [C] """SQLite-backed, oracle-separated Trading clone-and-compound demo.
- `copilot-sdk/examples/trading_clone/run.py:5` [R] and records verified outcomes in a temporary SQLite graph.
- `copilot-sdk/examples/trading_clone/run.py:45` [R] print("Trading clone complete. Synthetic factors, SQLite, and paper-only scoring.")

### copilot-sdk/experiments/vld/c1_c6_campaign_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/experiments/vld/c1_c6_campaign_v1.py:82` [R] lm=k.KUtilityStore(k.SQLiteDecisionStore(),len(factors))
- `copilot-sdk/experiments/vld/c1_c6_campaign_v1.py:83` [R] fixed=k.KUtilityStore(k.SQLiteDecisionStore(),len(factors))

### copilot-sdk/experiments/vld/vld_cons_pd_decision_features_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/experiments/vld/vld_cons_pd_decision_features_v1.py:9` [R] import sqlite3
- `copilot-sdk/experiments/vld/vld_cons_pd_decision_features_v1.py:49` [R] class SQLiteDecisionStore:
- `copilot-sdk/experiments/vld/vld_cons_pd_decision_features_v1.py:51` [R] self.conn = sqlite3.connect(":memory:")
- `copilot-sdk/experiments/vld/vld_cons_pd_decision_features_v1.py:119` [R] store = c5m.KUtilityStore(SQLiteDecisionStore(), d=len(factors))

### copilot-sdk/experiments/vld/vld_conservation_characterization_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/experiments/vld/vld_conservation_characterization_v1.py:48` [R] import sqlite3
- `copilot-sdk/experiments/vld/vld_conservation_characterization_v1.py:50` [R] self.conn = sqlite3.connect(":memory:")

### copilot-sdk/experiments/vld/vld_conservation_lag_c5_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/experiments/vld/vld_conservation_lag_c5_v1.py:22` [R] import sqlite3
- `copilot-sdk/experiments/vld/vld_conservation_lag_c5_v1.py:319` [R] class SQLiteDecisionStore:
- `copilot-sdk/experiments/vld/vld_conservation_lag_c5_v1.py:321` [R] self.conn = sqlite3.connect(":memory:")
- `copilot-sdk/experiments/vld/vld_conservation_lag_c5_v1.py:347` [R] learning_store = KUtilityStore(SQLiteDecisionStore(), d=len(factor_names))

### copilot-sdk/experiments/vld/vld_conservation_perdecision_signals_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/experiments/vld/vld_conservation_perdecision_signals_v1.py:10` [R] import sqlite3
- `copilot-sdk/experiments/vld/vld_conservation_perdecision_signals_v1.py:46` [R] class SQLiteDecisionStore:
- `copilot-sdk/experiments/vld/vld_conservation_perdecision_signals_v1.py:48` [R] self.conn = sqlite3.connect(":memory:")
- `copilot-sdk/experiments/vld/vld_conservation_perdecision_signals_v1.py:107` [R] store = c5m.KUtilityStore(SQLiteDecisionStore(), d=len(factors))

### copilot-sdk/experiments/vld/vld_decision_complexity_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/experiments/vld/vld_decision_complexity_v1.py:272` [R] learned = kcurve.KUtilityStore(kcurve.SQLiteDecisionStore(), d=len(factors))

### copilot-sdk/experiments/vld/vld_delayed_entrant_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/experiments/vld/vld_delayed_entrant_v1.py:25` [R] supplied to replay. Migration copies SQLite K weights/counters and deep-copies mu.
- `copilot-sdk/experiments/vld/vld_delayed_entrant_v1.py:55` [R] bytes. No timestamps, latency measurements, temp paths, SQLite file paths or
- `copilot-sdk/experiments/vld/vld_delayed_entrant_v1.py:148` [R] harness.KUtilityStore(harness.SQLiteDecisionStore(), d=len(factors)),
- `copilot-sdk/experiments/vld/vld_delayed_entrant_v1.py:375` [R] 'mu_and_sigma_updates': False, 'state_migration': 'deep-copy mu and sigma plus SQLite K weights/update counters; no shared arrays or connection',

### copilot-sdk/experiments/vld/vld_gate_calibration_f2_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/experiments/vld/vld_gate_calibration_f2_v1.py:86` [R] store = c5.KUtilityStore(c5.SQLiteDecisionStore(), d=len(names))

### copilot-sdk/experiments/vld/vld_looped_depth_c7_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/experiments/vld/vld_looped_depth_c7_v1.py:200` [R] memory = kcurve.SQLiteDecisionStore()

### copilot-sdk/experiments/vld/vld_moat_b2_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/experiments/vld/vld_moat_b2_v1.py:173` [R] self.store=h.KUtilityStore(h.SQLiteDecisionStore(),len(self.factors))
- `copilot-sdk/experiments/vld/vld_moat_b2_v1.py:639` [R] "independent_memory_and_sqlite":True,"tier":"REAL_COMPONENT"},

### copilot-sdk/experiments/vld/vld_rl_ctrl_enrichment_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/experiments/vld/vld_rl_ctrl_enrichment_v1.py:81` [R] h.reward_learning_store(h.KUtilityStore(h.SQLiteDecisionStore(),len(i.sigma)),cat,list(info['factor_names']),{},i,run,set(case['informative']))

### copilot-sdk/experiments/vld/vld_rl_ctrl_fork_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/experiments/vld/vld_rl_ctrl_fork_v1.py:18` [R] import sqlite3
- `copilot-sdk/experiments/vld/vld_rl_ctrl_fork_v1.py:130` [R] class SQLiteDecisionStore:
- `copilot-sdk/experiments/vld/vld_rl_ctrl_fork_v1.py:132` [R] self.conn = sqlite3.connect(":memory:")
- `copilot-sdk/experiments/vld/vld_rl_ctrl_fork_v1.py:378` [R] CompoundingScorer.from_preset(preset_name, db_path=str(Path(tmp) / f"{copilot}.db"), profile="test")
- `copilot-sdk/experiments/vld/vld_rl_ctrl_fork_v1.py:382` [R] learning_store = KUtilityStore(SQLiteDecisionStore(), d=len(factor_names))
- `copilot-sdk/experiments/vld/vld_rl_ctrl_fork_v1.py:383` [R] control_store = KUtilityStore(SQLiteDecisionStore(), d=len(factor_names))

### copilot-sdk/experiments/vld/vld_rl_ctrl2c_constrained_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/experiments/vld/vld_rl_ctrl2c_constrained_v1.py:49` [R] "persistence": "run_arm constructs h.KUtilityStore(h.SQLiteDecisionStore(), ...) inside each decision before reward_learning_store",

### copilot-sdk/experiments/vld/vld_rl_ctrl2c_redesign_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/experiments/vld/vld_rl_ctrl2c_redesign_v1.py:63` [C] """SQLite-compatible in-memory connection for KUtilityStore."""
- `copilot-sdk/experiments/vld/vld_rl_ctrl2c_redesign_v1.py:66` [R] import sqlite3
- `copilot-sdk/experiments/vld/vld_rl_ctrl2c_redesign_v1.py:68` [R] self.conn = sqlite3.connect(":memory:")

### copilot-sdk/integrity/architecture_scan.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/integrity/architecture_scan.py:79` [R] "copilot_sdk/migrate/sqlite_to_age.py": "migration module - direct psycopg required during cross-db migration",

### copilot-sdk/scripts/age_migration_benchmark.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/age_migration_benchmark.py:1` [C] """Measure direct SQLite-to-AGE migration throughput on a disposable graph.
- `copilot-sdk/scripts/age_migration_benchmark.py:11` [R] import sqlite3
- `copilot-sdk/scripts/age_migration_benchmark.py:20` [R] from copilot_sdk.migrate import sqlite_to_age as migration
- `copilot-sdk/scripts/age_migration_benchmark.py:24` [R] conn = sqlite3.connect(path)
- `copilot-sdk/scripts/age_migration_benchmark.py:108` [C] # Windows can retain a just-closed SQLite handle briefly after a large
- `copilot-sdk/scripts/age_migration_benchmark.py:113` [R] source = Path(temporary) / "benchmark.db"

### copilot-sdk/scripts/age_pf_blockers.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/age_pf_blockers.py:3` [R] Blocker 1: Do trading/dataops SQLite decision_ids overlap with the orphan AGE decision_ids?
- `copilot-sdk/scripts/age_pf_blockers.py:9` [R] import sqlite3
- `copilot-sdk/scripts/age_pf_blockers.py:20` [R] SQLITE_CANDIDATES = {
- `copilot-sdk/scripts/age_pf_blockers.py:22` [R] os.path.join(CI_DATA_DIR, "trading", "trading.db"),
- `copilot-sdk/scripts/age_pf_blockers.py:23` [R] os.path.join(BASE, "apps", "trading", "backend", "app", "data", "trading.db"),
- `copilot-sdk/scripts/age_pf_blockers.py:26` [R] os.path.join(CI_DATA_DIR, "purchasing", "purchasing.db"),
- `copilot-sdk/scripts/age_pf_blockers.py:27` [R] os.path.join(BASE, "apps", "purchasing", "backend", "app", "data", "purchasing.db"),
- `copilot-sdk/scripts/age_pf_blockers.py:30` [R] os.path.join(CI_DATA_DIR, "dataops", "dataops.db"),
- `copilot-sdk/scripts/age_pf_blockers.py:31` [R] os.path.join(BASE, "apps", "dataops", "backend", "app", "data", "dataops.db"),
- `copilot-sdk/scripts/age_pf_blockers.py:34` [R] os.path.join(CI_DATA_DIR, "s2p", "s2p.db"),
- `copilot-sdk/scripts/age_pf_blockers.py:35` [R] os.path.join(S2P_BASE, "backend", "app", "data", "s2p.db"),
- `copilot-sdk/scripts/age_pf_blockers.py:52` [R] def find_sqlite(domain):
- `copilot-sdk/scripts/age_pf_blockers.py:53` [C] """Find the SQLite DB for a domain. Returns (path, None) or (None, tried_paths)."""
- `copilot-sdk/scripts/age_pf_blockers.py:54` [R] for path in SQLITE_CANDIDATES.get(domain, []):
- `copilot-sdk/scripts/age_pf_blockers.py:60` [R] def get_sqlite_decision_ids(db_path):
- `copilot-sdk/scripts/age_pf_blockers.py:61` [C] """Extract decision_ids from a SQLite GraphStore DB."""
- `copilot-sdk/scripts/age_pf_blockers.py:63` [R] with sqlite3.connect(db_path) as sconn:
- `copilot-sdk/scripts/age_pf_blockers.py:66` [R] "SELECT name FROM sqlite_master WHERE type='table'"
- `copilot-sdk/scripts/age_pf_blockers.py:104` [C] # BLOCKER 1: Do SDK SQLite decision_ids overlap with AGE orphan IDs?
- `copilot-sdk/scripts/age_pf_blockers.py:133` [C] # Check each SDK copilot's SQLite
- `copilot-sdk/scripts/age_pf_blockers.py:134` [R] print("\n--- 1b. SQLite decision_id overlap per copilot ---")
- `copilot-sdk/scripts/age_pf_blockers.py:137` [R] db_path = find_sqlite(domain)
- `copilot-sdk/scripts/age_pf_blockers.py:140` [R] for p in SQLITE_CANDIDATES.get(domain, []):
- `copilot-sdk/scripts/age_pf_blockers.py:145` [R] sqlite_ids = get_sqlite_decision_ids(db_path)
- `copilot-sdk/scripts/age_pf_blockers.py:146` [R] print(f"    SQLite decisions: {len(sqlite_ids)}")
- `copilot-sdk/scripts/age_pf_blockers.py:147` [R] if not sqlite_ids:
- `copilot-sdk/scripts/age_pf_blockers.py:151` [C] # Show sample SQLite IDs for format comparison
- `copilot-sdk/scripts/age_pf_blockers.py:152` [R] for sid in sorted(list(sqlite_ids))[:3]:
- `copilot-sdk/scripts/age_pf_blockers.py:156` [R] o_overlap = orphan_outcome & sqlite_ids
- `copilot-sdk/scripts/age_pf_blockers.py:157` [R] er_overlap = orphan_er & sqlite_ids
- `copilot-sdk/scripts/age_pf_blockers.py:158` [R] cc_overlap = orphan_cc & sqlite_ids

### copilot-sdk/scripts/age_v35_review_checks.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/age_v35_review_checks.py:6` [R] import sqlite3
- `copilot-sdk/scripts/age_v35_review_checks.py:50` [R] primary = base / domain / f"{domain}.db"
- `copilot-sdk/scripts/age_v35_review_checks.py:56` [R] / "backend" / "app" / "data" / "s2p.db"
- `copilot-sdk/scripts/age_v35_review_checks.py:60` [R] raise FileNotFoundError(f"No SQLite DB for {domain}: {primary}")
- `copilot-sdk/scripts/age_v35_review_checks.py:63` [R] def open_sqlite(path: Path) -> sqlite3.Connection:
- `copilot-sdk/scripts/age_v35_review_checks.py:64` [R] conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
- `copilot-sdk/scripts/age_v35_review_checks.py:65` [R] conn.row_factory = sqlite3.Row
- `copilot-sdk/scripts/age_v35_review_checks.py:74` [R] def sqlite_inventory(domain: str) -> dict[str, Any]:
- `copilot-sdk/scripts/age_v35_review_checks.py:76` [R] with open_sqlite(path) as conn:
- `copilot-sdk/scripts/age_v35_review_checks.py:130` [R] def print_rows(rows: list[sqlite3.Row]) -> None:
- `copilot-sdk/scripts/age_v35_review_checks.py:136` [R] section("FINDING 1 - UNVERIFIED SQLITE DECISIONS")
- `copilot-sdk/scripts/age_v35_review_checks.py:139` [R] result = sqlite_inventory(domain)
- `copilot-sdk/scripts/age_v35_review_checks.py:238` [R] sqlite_results = finding_one()
- `copilot-sdk/scripts/age_v35_review_checks.py:250` [R] print(f"{domain.upper()}: {ghost_classification(sqlite_results[domain])}")

### copilot-sdk/scripts/budget_accuracy_frontier.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/budget_accuracy_frontier.py:28` [R] from k_learning_curve_experiment import SQLiteDecisionStore, geometry_hash, scenario
- `copilot-sdk/scripts/budget_accuracy_frontier.py:209` [R] memory = SQLiteDecisionStore()

### copilot-sdk/scripts/d1_recursion_trace_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/d1_recursion_trace_v1.py:8` [R] import sqlite3
- `copilot-sdk/scripts/d1_recursion_trace_v1.py:42` [R] conn = sqlite3.connect(":memory:")

### copilot-sdk/scripts/demo_warm_start.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/demo_warm_start.py:64` [R] db_path=str(db_dir / f"{SOURCE_COPILOT}.db"),
- `copilot-sdk/scripts/demo_warm_start.py:68` [R] db_path=str(db_dir / f"{TARGET_COPILOT}.db"),

### copilot-sdk/scripts/design_drift_inventory.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/design_drift_inventory.py:30` [R] if path.suffix in {".db", ".sqlite", ".sqlite3"}:

### copilot-sdk/scripts/evolve_demo.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/evolve_demo.py:47` [R] db_path = str(Path(tmp) / f"{domain}.db")

### copilot-sdk/scripts/factor0_agg_verify_v1.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/factor0_agg_verify_v1.py:380` [R] and not f.endswith(".sqlite3")
- `copilot-sdk/scripts/factor0_agg_verify_v1.py:381` [R] and not f.endswith(".sqlite3-shm")
- `copilot-sdk/scripts/factor0_agg_verify_v1.py:382` [R] and not f.endswith(".sqlite3-wal")]

### copilot-sdk/scripts/k_learning_conservation_interaction.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/k_learning_conservation_interaction.py:10` [R] import sqlite3
- `copilot-sdk/scripts/k_learning_conservation_interaction.py:35` [R] self.conn = sqlite3.connect(":memory:")

### copilot-sdk/scripts/k_learning_curve_cross_copilot.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/k_learning_curve_cross_copilot.py:16` [R] import sqlite3
- `copilot-sdk/scripts/k_learning_curve_cross_copilot.py:95` [R] class SQLiteDecisionStore:
- `copilot-sdk/scripts/k_learning_curve_cross_copilot.py:97` [R] self.conn = sqlite3.connect(":memory:")
- `copilot-sdk/scripts/k_learning_curve_cross_copilot.py:341` [R] CompoundingScorer.from_preset(preset_name, db_path=str(Path(tmp) / f"{copilot}.db"), profile="test")
- `copilot-sdk/scripts/k_learning_curve_cross_copilot.py:345` [R] learning_store = KUtilityStore(SQLiteDecisionStore(), d=len(factor_names))
- `copilot-sdk/scripts/k_learning_curve_cross_copilot.py:346` [R] control_store = KUtilityStore(SQLiteDecisionStore(), d=len(factor_names))

### copilot-sdk/scripts/k_learning_curve_experiment.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/k_learning_curve_experiment.py:14` [R] import sqlite3
- `copilot-sdk/scripts/k_learning_curve_experiment.py:49` [R] class SQLiteDecisionStore:
- `copilot-sdk/scripts/k_learning_curve_experiment.py:51` [R] self.conn = sqlite3.connect(":memory:")
- `copilot-sdk/scripts/k_learning_curve_experiment.py:306` [R] db_path=str(Path(tmp) / "dataops.db"),
- `copilot-sdk/scripts/k_learning_curve_experiment.py:310` [R] learning_store = KUtilityStore(SQLiteDecisionStore(), d=len(factor_names))
- `copilot-sdk/scripts/k_learning_curve_experiment.py:311` [R] control_store = KUtilityStore(SQLiteDecisionStore(), d=len(factor_names))

### copilot-sdk/scripts/k_learning_curve_extended.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/k_learning_curve_extended.py:14` [R] import sqlite3
- `copilot-sdk/scripts/k_learning_curve_extended.py:52` [R] class SQLiteDecisionStore:
- `copilot-sdk/scripts/k_learning_curve_extended.py:54` [R] self.conn = sqlite3.connect(":memory:")
- `copilot-sdk/scripts/k_learning_curve_extended.py:304` [R] CompoundingScorer.from_preset("dataops", db_path=str(Path(tmp) / "dataops.db"), profile="test")
- `copilot-sdk/scripts/k_learning_curve_extended.py:306` [R] learning_store = KUtilityStore(SQLiteDecisionStore(), d=len(factor_names))
- `copilot-sdk/scripts/k_learning_curve_extended.py:307` [R] control_store = KUtilityStore(SQLiteDecisionStore(), d=len(factor_names))

### copilot-sdk/scripts/k_learning_distribution_sensitivity.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/k_learning_distribution_sensitivity.py:9` [R] import sqlite3
- `copilot-sdk/scripts/k_learning_distribution_sensitivity.py:32` [R] self.conn = sqlite3.connect(":memory:")

### copilot-sdk/scripts/phase_config.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/phase_config.py:33` [R] "trading": {"prefix": "TRD-", "db_path": SDK_ROOT / "apps/trading/backend/data/trading.db", "port": 8010, "score_path": "/api/score", "learn_path": "/api/learn", "score_payload_fn": _default_score_payload},
- `copilot-sdk/scripts/phase_config.py:34` [R] "purchasing": {"prefix": "PUR-", "db_path": SDK_ROOT / "apps/purchasing/backend/data/purchasing.db", "port": 8020, "score_path": "/api/score", "learn_path": "/api/learn", "score_payload_fn": _default_score_payload},
- `copilot-sdk/scripts/phase_config.py:35` [R] "dataops": {"prefix": "DOPS-", "db_path": SDK_ROOT / "apps/dataops/backend/data/dataops.db", "port": 8030, "score_path": "/api/score", "learn_path": "/api/learn", "score_payload_fn": _default_score_payload},
- `copilot-sdk/scripts/phase_config.py:39` [R] os.path.join(SDK_ROOT, "..", "s2p-copilot", "backend", "app", "data", "s2p.db")
- `copilot-sdk/scripts/phase_config.py:61` [R] configured_path = os.environ.get("MIGRATION_SQLITE_PATH")
- `copilot-sdk/scripts/phase_config.py:76` [R] cfg["outbox_path"] = str(Path(cfg["db_path"]).parent / f"{selected}_dual_write_outbox.db")

### copilot-sdk/scripts/phase_dual_write_e2e.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/phase_dual_write_e2e.py:1` [C] """Score and learn decisions, then prove SQLite/AGE dual-write for one domain."""
- `copilot-sdk/scripts/phase_dual_write_e2e.py:3` [R] import argparse, sqlite3, time
- `copilot-sdk/scripts/phase_dual_write_e2e.py:6` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/scripts/phase_dual_write_e2e.py:13` [R] store=SQLiteGraphStore(cfg["db_path"], domain=cfg["domain"], decision_id_prefix=cfg["prefix"]); baseline=store.count_decisions(cfg["domain"]); store.close()
- `copilot-sdk/scripts/phase_dual_write_e2e.py:23` [R] store=SQLiteGraphStore(cfg["db_path"], domain=cfg["domain"], decision_id_prefix=cfg["prefix"]); delta=store.count_decisions(cfg["domain"])-baseline; store.close()
- `copilot-sdk/scripts/phase_dual_write_e2e.py:32` [R] with sqlite3.connect(cfg['outbox_path']) as outbox:
- `copilot-sdk/scripts/phase_dual_write_e2e.py:36` [R] print(f"domain={cfg['domain']} sqlite_delta={delta} age={found}/{len(scored)} outbox_clean={outbox_clean}")

### copilot-sdk/scripts/phase_read_diff.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/phase_read_diff.py:1` [C] """Compare active and archived SQLite/AGE records for one copilot."""
- `copilot-sdk/scripts/phase_read_diff.py:5` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/scripts/phase_read_diff.py:12` [R] primary = SQLiteGraphStore(cfg["db_path"], domain=cfg["domain"], decision_id_prefix=cfg["prefix"])

### copilot-sdk/scripts/phase_verify.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/phase_verify.py:1` [C] """Verify SQLite source counts against AGE topology for one domain."""
- `copilot-sdk/scripts/phase_verify.py:3` [R] import argparse, sqlite3
- `copilot-sdk/scripts/phase_verify.py:14` [R] with sqlite3.connect(cfg["db_path"]) as source:
- `copilot-sdk/scripts/phase_verify.py:17` [R] archived = source.execute("SELECT count(*) FROM decisions_archive").fetchone()[0] if source.execute("SELECT 1 FROM sqlite_master WHERE name='decisions_archive'").fetchone() else 0

### copilot-sdk/scripts/phase3_cycle_gate_v3.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/phase3_cycle_gate_v3.py:12` [R] Windows SQLite WAL prevents cross-process reads while the backend
- `copilot-sdk/scripts/phase3_cycle_gate_v3.py:29` [R] SQLITE_PATH = os.path.join(SDK_ROOT, "apps", "trading", "backend", "data", "trading.db")
- `copilot-sdk/scripts/phase3_cycle_gate_v3.py:131` [R] import sqlite3
- `copilot-sdk/scripts/phase3_cycle_gate_v3.py:134` [R] "trading_dual_write_outbox.db",
- `copilot-sdk/scripts/phase3_cycle_gate_v3.py:138` [R] conn = sqlite3.connect(outbox_path)
- `copilot-sdk/scripts/phase3_cycle_gate_v3.py:143` [R] "SELECT name FROM sqlite_master WHERE type='table' AND name='secondary_outbox'"
- `copilot-sdk/scripts/phase3_cycle_gate_v3.py:241` [R] if not os.path.exists(SQLITE_PATH):
- `copilot-sdk/scripts/phase3_cycle_gate_v3.py:242` [R] print(f"ERROR: SQLite not found at {SQLITE_PATH}")

### copilot-sdk/scripts/phase3_dual_parity_v2.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/phase3_dual_parity_v2.py:4` [R] Run with Trading backend STOPPED to avoid SQLite WAL visibility issues.
- `copilot-sdk/scripts/phase3_dual_parity_v2.py:9` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/scripts/phase3_dual_parity_v2.py:14` [R] SQLITE_PATH = os.path.join(SDK_ROOT, "apps", "trading", "backend", "data", "trading.db")
- `copilot-sdk/scripts/phase3_dual_parity_v2.py:18` [R] if not os.path.exists(SQLITE_PATH):
- `copilot-sdk/scripts/phase3_dual_parity_v2.py:19` [R] print(f"ERROR: SQLite not found at {SQLITE_PATH}")
- `copilot-sdk/scripts/phase3_dual_parity_v2.py:25` [R] print(f"Source: {SQLITE_PATH}")
- `copilot-sdk/scripts/phase3_dual_parity_v2.py:27` [R] primary = SQLiteGraphStore(SQLITE_PATH, domain=DOMAIN, decision_id_prefix="TRD-")
- `copilot-sdk/scripts/phase3_dual_parity_v2.py:39` [R] print(f"\nPrimary (SQLite):")

### copilot-sdk/scripts/phase3_dual_write_e2e_v2.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:46` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:48` [R] sqlite_path = os.path.expanduser("~/.ci-platform/trading/trading.db")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:49` [R] sqlite = SQLiteGraphStore(sqlite_path, domain="trading", decision_id_prefix="TRD-")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:50` [R] baseline_total = sqlite.count_decisions("trading")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:51` [R] baseline_verified = sqlite.count_verified("trading")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:52` [R] print(f"  SQLite: {baseline_total} total, {baseline_verified} verified")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:53` [R] sqlite.close()
- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:102` [R] sqlite = SQLiteGraphStore(sqlite_path, domain="trading", decision_id_prefix="TRD-")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:103` [R] after_total = sqlite.count_decisions("trading")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:104` [R] after_verified = sqlite.count_verified("trading")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:105` [R] print(f"  SQLite: {after_total} total (+{after_total - baseline_total}), {after_verified} verified (+{after_verified - baseline_verified})")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:106` [R] sqlite.close()
- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:143` [R] new_in_sqlite = after_total > baseline_total
- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:147` [R] print(f"New decisions in SQLite: {new_in_sqlite} {'✅' if new_in_sqlite else '❌'}")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:150` [R] if all_prefixed and new_in_sqlite and new_in_age:
- `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:157` [R] sys.exit(0 if (all_prefixed and new_in_sqlite and new_in_age) else 1)

### copilot-sdk/scripts/phase3_dual_write_e2e_v4.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:4` [R] Verifies: TRD- prefix, SQLite writes, AGE writes, outbox health.
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:13` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:17` [R] SQLITE_PATH = os.path.expanduser("~/.ci-platform/trading/trading.db")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:19` [R] OUTBOX_PATH = os.path.expanduser("~/.ci-platform/trading/trading_dual_write_outbox.db")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:52` [R] sqlite = SQLiteGraphStore(SQLITE_PATH, domain="trading", decision_id_prefix="TRD-")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:53` [R] base_total = sqlite.count_decisions("trading")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:54` [R] base_verified = sqlite.count_verified("trading")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:55` [R] sqlite.close()
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:101` [C] # Post-scoring SQLite counts
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:102` [R] sqlite = SQLiteGraphStore(SQLITE_PATH, domain="trading", decision_id_prefix="TRD-")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:103` [R] after_total = sqlite.count_decisions("trading")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:104` [R] after_verified = sqlite.count_verified("trading")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:105` [R] sqlite.close()
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:108` [R] print(f"\nSQLite after: {after_total} total (+{delta_total}), {after_verified} verified (+{delta_verified})")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:138` [R] import sqlite3
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:141` [R] oconn = sqlite3.connect(OUTBOX_PATH)
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:155` [R] except sqlite3.OperationalError:
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:169` [R] new_in_sqlite = delta_total >= N
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:173` [R] print(f"SQLite new:          +{delta_total} (expected +{N}) {'PASS' if new_in_sqlite else 'FAIL'}")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:178` [R] gate = all_prefixed and new_in_sqlite and all_in_age and outbox_ok

### copilot-sdk/scripts/phase3_dual_write_e2e_v5.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:3` [R] import sqlite3 as sqlite3_mod
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:10` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:15` [R] SQLITE_PATH = os.path.join(SDK_ROOT, "apps", "trading", "backend", "data", "trading.db")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:35` [R] print(f"SQLite: {SQLITE_PATH}")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:37` [R] if not os.path.exists(SQLITE_PATH):
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:38` [R] print(f"ERROR: SQLite not found")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:49` [R] sqlite = SQLiteGraphStore(SQLITE_PATH, domain="trading", decision_id_prefix="TRD-")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:50` [R] base_total = sqlite.count_decisions("trading")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:51` [R] base_verified = sqlite.count_verified("trading")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:52` [R] sqlite.close()
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:95` [C] # Post-scoring SQLite
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:96` [R] sqlite = SQLiteGraphStore(SQLITE_PATH, domain="trading", decision_id_prefix="TRD-")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:97` [R] after_total = sqlite.count_decisions("trading")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:98` [R] after_verified = sqlite.count_verified("trading")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:99` [R] sqlite.close()
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:102` [R] print(f"\nSQLite after: {after_total} total (+{delta_total}), {after_verified} verified (+{delta_verified})")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:133` [R] os.path.join(OUTBOX_DIR, "trading_dual_write_outbox.db"),
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:134` [R] os.path.expanduser("~/.ci-platform/trading/trading_dual_write_outbox.db"),
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:138` [R] oconn = sqlite3_mod.connect(candidate)
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:149` [R] except sqlite3_mod.OperationalError:
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:163` [R] new_in_sqlite = delta_total >= N
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:167` [R] print(f"SQLite new:     +{delta_total} (expected +{N}) {'PASS' if new_in_sqlite else 'FAIL'}")
- `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:172` [R] gate = all_prefixed and new_in_sqlite and all_in_age and outbox_ok

### copilot-sdk/scripts/phase3_read_diff_v2.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/phase3_read_diff_v2.py:3` [R] Constructs separate SQLite and AGE stores for independent comparison.
- `copilot-sdk/scripts/phase3_read_diff_v2.py:9` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/scripts/phase3_read_diff_v2.py:12` [R] SQLITE_PATH = os.path.expanduser("~/.ci-platform/trading/trading.db")
- `copilot-sdk/scripts/phase3_read_diff_v2.py:21` [C] # Primary: SQLite
- `copilot-sdk/scripts/phase3_read_diff_v2.py:22` [R] primary = SQLiteGraphStore(SQLITE_PATH, domain=DOMAIN, decision_id_prefix="TRD-")
- `copilot-sdk/scripts/phase3_read_diff_v2.py:65` [R] print(f"\nMissing in SQLite ({len(report.missing_in_primary)}):")
- `copilot-sdk/scripts/phase3_read_diff_v2.py:78` [R] print("GATE: ✅ PASS — Trading SQLite and AGE are in parity.")

### copilot-sdk/scripts/phase3_read_diff_v4.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/phase3_read_diff_v4.py:3` [R] We migrated verified decisions only. Pending decisions remain in SQLite.
- `copilot-sdk/scripts/phase3_read_diff_v4.py:9` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/scripts/phase3_read_diff_v4.py:13` [R] SQLITE_PATH = os.path.expanduser("~/.ci-platform/trading/trading.db")
- `copilot-sdk/scripts/phase3_read_diff_v4.py:22` [R] primary = SQLiteGraphStore(SQLITE_PATH, domain=DOMAIN, decision_id_prefix="TRD-")
- `copilot-sdk/scripts/phase3_read_diff_v4.py:35` [R] print(f"Primary (SQLite)  — verified: {p_verified}, correct: {p_correct}, total: {p_total}")
- `copilot-sdk/scripts/phase3_read_diff_v4.py:61` [R] missing_in_sqlite = [k for k in s_map if k not in p_map]
- `copilot-sdk/scripts/phase3_read_diff_v4.py:91` [R] print(f"Missing in SQLite: {len(missing_in_sqlite)}")
- `copilot-sdk/scripts/phase3_read_diff_v4.py:99` [R] if missing_in_sqlite:
- `copilot-sdk/scripts/phase3_read_diff_v4.py:100` [R] print(f"\n  Missing in SQLite (first 10):")
- `copilot-sdk/scripts/phase3_read_diff_v4.py:101` [R] for did in missing_in_sqlite[:10]:
- `copilot-sdk/scripts/phase3_read_diff_v4.py:116` [R] and not missing_in_age and not missing_in_sqlite

### copilot-sdk/scripts/phase3_read_diff_v5.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/phase3_read_diff_v5.py:5` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/scripts/phase3_read_diff_v5.py:10` [R] SQLITE_PATH = os.path.join(SDK_ROOT, "apps", "trading", "backend", "data", "trading.db")
- `copilot-sdk/scripts/phase3_read_diff_v5.py:14` [R] if not os.path.exists(SQLITE_PATH):
- `copilot-sdk/scripts/phase3_read_diff_v5.py:15` [R] print(f"ERROR: SQLite not found at {SQLITE_PATH}")
- `copilot-sdk/scripts/phase3_read_diff_v5.py:21` [R] print(f"Source: {SQLITE_PATH}")
- `copilot-sdk/scripts/phase3_read_diff_v5.py:23` [R] primary = SQLiteGraphStore(SQLITE_PATH, domain=DOMAIN, decision_id_prefix="TRD-")
- `copilot-sdk/scripts/phase3_read_diff_v5.py:33` [R] print(f"Primary (SQLite)  — verified: {p_verified}, correct: {p_correct}, total: {p_total}")
- `copilot-sdk/scripts/phase3_read_diff_v5.py:58` [R] missing_in_sqlite = [k for k in s_map if k not in p_map]
- `copilot-sdk/scripts/phase3_read_diff_v5.py:84` [R] print(f"Missing in SQLite: {len(missing_in_sqlite)}")
- `copilot-sdk/scripts/phase3_read_diff_v5.py:91` [R] if missing_in_sqlite:
- `copilot-sdk/scripts/phase3_read_diff_v5.py:92` [R] for did in missing_in_sqlite[:10]:
- `copilot-sdk/scripts/phase3_read_diff_v5.py:93` [R] print(f"  Missing in SQLite: {did}")
- `copilot-sdk/scripts/phase3_read_diff_v5.py:106` [R] and not missing_in_age and not missing_in_sqlite

### copilot-sdk/scripts/phase3_reset_v3.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/phase3_reset_v3.py:6` [R] import sqlite3
- `copilot-sdk/scripts/phase3_reset_v3.py:14` [R] CORRECT_DB = os.path.join(SDK_ROOT, "apps", "trading", "backend", "data", "trading.db")
- `copilot-sdk/scripts/phase3_reset_v3.py:43` [R] conn_sq = sqlite3.connect(CORRECT_DB)
- `copilot-sdk/scripts/phase3_reset_v3.py:154` [R] print(f"  python -m copilot_sdk.migrate sqlite_to_age \\")

### copilot-sdk/scripts/phase3_verify_v2.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/phase3_verify_v2.py:19` [R] ("Trading migration_source","MATCH (d:Decision {domain:'trading', migration_source:'sqlite'}) RETURN count(d)",         EXPECTED_TRADING),

### copilot-sdk/scripts/phase3_verify_v3.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/phase3_verify_v3.py:3` [R] import sqlite3
- `copilot-sdk/scripts/phase3_verify_v3.py:9` [R] SQLITE_PATH = os.path.join(SDK_ROOT, "apps", "trading", "backend", "data", "trading.db")
- `copilot-sdk/scripts/phase3_verify_v3.py:21` [C] # Discover expected from SQLite
- `copilot-sdk/scripts/phase3_verify_v3.py:22` [R] if not os.path.exists(SQLITE_PATH):
- `copilot-sdk/scripts/phase3_verify_v3.py:23` [R] print(f"ERROR: SQLite not found at {SQLITE_PATH}")
- `copilot-sdk/scripts/phase3_verify_v3.py:26` [R] sq = sqlite3.connect(SQLITE_PATH)
- `copilot-sdk/scripts/phase3_verify_v3.py:37` [R] print(f"Source: {SQLITE_PATH}")

### copilot-sdk/scripts/pilot_report.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/pilot_report.py:20` [R] parser.add_argument("--db", type=Path, default=ROOT / "data" / "measured_transfer.sqlite3")
- `copilot-sdk/scripts/pilot_report.py:22` [R] store = MeasuredTransferStore(str(args.db))

### copilot-sdk/scripts/preseed_demo_fixtures.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/preseed_demo_fixtures.py:125` [R] db_path=root / "apps/purchasing/backend/data/purchasing.db")
- `copilot-sdk/scripts/preseed_demo_fixtures.py:136` [R] store = create_graph_store(domain="dataops", db_path=root / "apps/dataops/backend/data/dataops.db")
- `copilot-sdk/scripts/preseed_demo_fixtures.py:184` [R] store = create_graph_store(domain="purchasing", db_path=root / "apps/purchasing/backend/data/purchasing.db")

### copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py:4` [R] warm SQLite databases still contain collapsed legacy checkpoint tensors. It does
- `copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py:13` [R] import sqlite3
- `copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py:40` [R] db_path=ROOT / "apps" / "purchasing" / "backend" / "data" / "purchasing.db",
- `copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py:51` [R] db_path=ROOT / "apps" / "trading" / "backend" / "data" / "trading.db",
- `copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py:121` [R] def _table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
- `copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py:125` [R] def _table_count(conn: sqlite3.Connection, table: str) -> int:
- `copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py:128` [R] except sqlite3.OperationalError:
- `copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py:132` [R] def latest_checkpoint(conn: sqlite3.Connection) -> dict[str, Any]   None:
- `copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py:142` [R] def latest_checkpoint_centroids(conn: sqlite3.Connection) -> np.ndarray   None:
- `copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py:150` [R] conn: sqlite3.Connection,
- `copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py:216` [R] conn = sqlite3.connect(db_path)

### copilot-sdk/scripts/routing_variant_risk_sensitive.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/routing_variant_risk_sensitive.py:13` [R] import sqlite3
- `copilot-sdk/scripts/routing_variant_risk_sensitive.py:39` [R] self.conn = sqlite3.connect(":memory:")

### copilot-sdk/scripts/shadow_live_test.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/shadow_live_test.py:1` [C] """Live Trading shadow-scorer validation using SQLite source data.
- `copilot-sdk/scripts/shadow_live_test.py:3` [R] The script reads verified Trading decisions from an existing SQLite database,
- `copilot-sdk/scripts/shadow_live_test.py:18` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `copilot-sdk/scripts/shadow_live_test.py:25` [R] Path.home() / ".ci-platform" / "trading" / "trading.db",
- `copilot-sdk/scripts/shadow_live_test.py:26` [R] Path("apps") / "trading" / "backend" / "data" / "trading.db",
- `copilot-sdk/scripts/shadow_live_test.py:30` [R] def _open_readable_store(path: Path) -> SQLiteGraphStore   None:
- `copilot-sdk/scripts/shadow_live_test.py:32` [R] return SQLiteGraphStore(path, domain="trading")
- `copilot-sdk/scripts/shadow_live_test.py:47` [R] raise SystemExit(f"No readable Trading SQLite DB found. Checked: {checked}")
- `copilot-sdk/scripts/shadow_live_test.py:72` [R] source_store = SQLiteGraphStore(source, domain="trading")
- `copilot-sdk/scripts/shadow_live_test.py:83` [R] primary_db = temp_path / "primary_trading.db"
- `copilot-sdk/scripts/shadow_live_test.py:84` [R] shadow_db = temp_path / "shadow_trading.db"
- `copilot-sdk/scripts/shadow_live_test.py:88` [R] primary_store = SQLiteGraphStore(primary_db, domain="trading", decision_id_prefix="TRD-P-")
- `copilot-sdk/scripts/shadow_live_test.py:89` [R] shadow_store = SQLiteGraphStore(shadow_db, domain="trading", decision_id_prefix="TRD-S-")
- `copilot-sdk/scripts/shadow_live_test.py:123` [R] parser = argparse.ArgumentParser(description="Run Trading SQLite shadow scorer validation.")
- `copilot-sdk/scripts/shadow_live_test.py:124` [R] parser.add_argument("--source", help="Path to Trading SQLite DB. Defaults to home DB, then repo demo DB.")

### copilot-sdk/scripts/sqlite_copilot_audit.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/sqlite_copilot_audit.py:1` [C] """SQLite Copilot Audit — All 4 SDK Copilots
- `copilot-sdk/scripts/sqlite_copilot_audit.py:8` [R] - Rule #38 compliance (direct SQLiteGraphStore construction)
- `copilot-sdk/scripts/sqlite_copilot_audit.py:16` [R] import sqlite3
- `copilot-sdk/scripts/sqlite_copilot_audit.py:22` [R] SQLITE_PATHS = {
- `copilot-sdk/scripts/sqlite_copilot_audit.py:24` [R] os.path.join(CI_DATA_DIR, "trading", "trading.db"),
- `copilot-sdk/scripts/sqlite_copilot_audit.py:25` [R] os.path.join(SDK_BASE, "apps", "trading", "backend", "app", "data", "trading.db"),
- `copilot-sdk/scripts/sqlite_copilot_audit.py:28` [R] os.path.join(CI_DATA_DIR, "purchasing", "purchasing.db"),
- `copilot-sdk/scripts/sqlite_copilot_audit.py:29` [R] os.path.join(SDK_BASE, "apps", "purchasing", "backend", "app", "data", "purchasing.db"),
- `copilot-sdk/scripts/sqlite_copilot_audit.py:32` [R] os.path.join(CI_DATA_DIR, "dataops", "dataops.db"),
- `copilot-sdk/scripts/sqlite_copilot_audit.py:33` [R] os.path.join(SDK_BASE, "apps", "dataops", "backend", "app", "data", "dataops.db"),
- `copilot-sdk/scripts/sqlite_copilot_audit.py:36` [R] os.path.join(CI_DATA_DIR, "s2p", "s2p.db"),
- `copilot-sdk/scripts/sqlite_copilot_audit.py:37` [R] os.path.join(S2P_BASE, "backend", "app", "data", "s2p.db"),
- `copilot-sdk/scripts/sqlite_copilot_audit.py:63` [R] for p in SQLITE_PATHS.get(domain, []):
- `copilot-sdk/scripts/sqlite_copilot_audit.py:69` [R] def audit_sqlite(domain, db_path):
- `copilot-sdk/scripts/sqlite_copilot_audit.py:70` [C] """Full audit of one copilot's SQLite DB."""
- `copilot-sdk/scripts/sqlite_copilot_audit.py:74` [R] conn = sqlite3.connect(db_path)
- `copilot-sdk/scripts/sqlite_copilot_audit.py:77` [R] "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
- `copilot-sdk/scripts/sqlite_copilot_audit.py:190` [C] """Check Rule #38: does main.py construct SQLiteGraphStore directly?"""
- `copilot-sdk/scripts/sqlite_copilot_audit.py:209` [R] if "SQLiteGraphStore(" in stripped:
- `copilot-sdk/scripts/sqlite_copilot_audit.py:216` [R] print(f"    VIOLATION: {len(direct_constructions)} direct SQLiteGraphStore() calls:")
- `copilot-sdk/scripts/sqlite_copilot_audit.py:220` [R] print(f"    COMPLIANT: no direct SQLiteGraphStore() calls")
- `copilot-sdk/scripts/sqlite_copilot_audit.py:267` [R] conn = sqlite3.connect(db_path)
- `copilot-sdk/scripts/sqlite_copilot_audit.py:269` [R] "SELECT name FROM sqlite_master WHERE type='table'"
- `copilot-sdk/scripts/sqlite_copilot_audit.py:334` [R] section("SQLite COPILOT AUDIT — ALL 4 SDK COPILOTS")
- `copilot-sdk/scripts/sqlite_copilot_audit.py:343` [R] print(f"  SQLite DB NOT FOUND")
- `copilot-sdk/scripts/sqlite_copilot_audit.py:344` [R] for p in SQLITE_PATHS.get(domain, []):
- `copilot-sdk/scripts/sqlite_copilot_audit.py:350` [R] stats = audit_sqlite(domain, db_path)

### copilot-sdk/scripts/transfer_demo.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/transfer_demo.py:28` [R] db_path = Path(tempfile.mkdtemp()) / "s2p-transfer-demo.db"

### copilot-sdk/scripts/validate_age_unification.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `copilot-sdk/scripts/validate_age_unification.py:109` [R] if "domain" not in context and "sqlite" not in context:

### gen-ai-roi-demo-v4-v50/backend/app/connectors/crowdstrike_mock.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/connectors/crowdstrike_mock.py:23` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/connectors/greynoise.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/connectors/greynoise.py:33` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py:29` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/data/alert_pool.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/data/alert_pool.py:405` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/framework/audit.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/framework/audit.py:298` [M] from app.db.graph_client import graph_client  # noqa: PLC0415

### gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py:41` [M] self.db = db_client
- `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py:122` [M] result = await self.db.run_query(
- `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py:151` [M] graph_service=self.db,
- `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py:256` [M] rows = await self.db.run_query(
- `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py:289` [M] rows = await self.db.run_query(
- `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py:340` [M] await self.db.run_query(

### gen-ai-roi-demo-v4-v50/backend/app/main.py

CONFIRMED family / G024, G048, G053; individual branches may be test/demo/parser-only.

- `gen-ai-roi-demo-v4-v50/backend/app/main.py:7` [R] import sqlite3
- `gen-ai-roi-demo-v4-v50/backend/app/main.py:200` [R] self.conn = sqlite3.connect(path, check_same_thread=False)
- `gen-ai-roi-demo-v4-v50/backend/app/main.py:241` [M] from app.db.graph_client import graph_client
- `gen-ai-roi-demo-v4-v50/backend/app/main.py:249` [R] **_vld_k_router_kwargs(Path(__file__).resolve().parents[1] / "data" / "k_utility.db", 6),
- `gen-ai-roi-demo-v4-v50/backend/app/main.py:285` [M] from app.db.graph_client import graph_client, soc_decision_where, _GRAPH_BACKEND
- `gen-ai-roi-demo-v4-v50/backend/app/main.py:630` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:114` [M] from app.db.graph_client import graph_client
- `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:186` [M] from app.db.graph_client import graph_client
- `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:422` [M] from app.db.graph_client import graph_client
- `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:440` [M] from app.db.graph_client import graph_client
- `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:485` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/routers/cohort_status_router.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/routers/cohort_status_router.py:10` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/routers/discoveries_router.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/routers/discoveries_router.py:8` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:20` [M] from app.db.graph_client import graph_client, soc_decision_where

### gen-ai-roi-demo-v4-v50/backend/app/routers/explain.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/routers/explain.py:10` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:9` [R] app.db.*

### gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:23` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/routers/judgment.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/routers/judgment.py:19` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:11` [M] from app.db.graph_client import graph_client, soc_decision_where

### gen-ai-roi-demo-v4-v50/backend/app/routers/simulation.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/routers/simulation.py:219` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/routers/soc_demo_beats.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_demo_beats.py:16` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py

CONFIRMED family / G016, G017, G041; individual branches may be test/demo/parser-only.

- `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:17` [M] from app.db.graph_client import graph_client, soc_decision_where
- `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:4362` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/routers/time_machine_router.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/routers/time_machine_router.py:9` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py

CONFIRMED family / G017, G018, G041; individual branches may be test/demo/parser-only.

- `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:51` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/services/attack_chain.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/attack_chain.py:64` [M] self.db = db_client
- `gen-ai-roi-demo-v4-v50/backend/app/services/attack_chain.py:116` [M] records = await self.db.run_query(query, {})

### gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py

CONFIRMED family / G045; individual branches may be test/demo/parser-only.

- `gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:7` [R] import sqlite3
- `gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:128` [R] configured = Path(__file__).resolve().parents[2] / "data" / "soc_authority.sqlite3"
- `gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:141` [R] self._audit = sqlite3.connect(self.db_path, check_same_thread=False)

### gen-ai-roi-demo-v4-v50/backend/app/services/benchmarking_report.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/benchmarking_report.py:32` [M] self.db = db_client
- `gen-ai-roi-demo-v4-v50/backend/app/services/benchmarking_report.py:167` [M] records = self.db.run_query(query)

### gen-ai-roi-demo-v4-v50/backend/app/services/evidence_room.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/evidence_room.py:178` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:432` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:5` [M] from app.db.graph_client import soc_decision_where
- `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:163` [M] self.db = db_client
- `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:214` [M] records = self.db.run_query(query)
- `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:230` [M] totals = self.db.run_query(total_query)
- `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:261` [M] chain_records = self.db.run_query(chain_query)
- `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:271` [M] u_r = self.db.run_query("MATCH (u:User) RETURN count(u) AS cnt")
- `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:272` [M] a_r = self.db.run_query("MATCH (a:Asset) RETURN count(a) AS cnt")
- `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:273` [M] t_r = self.db.run_query("MATCH (t:ThreatIndicator) RETURN count(t) AS cnt")
- `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:299` [M] iks_result = compute_iks(self.db)
- `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:333` [M] records = self.db.run_query(counts_query)
- `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:338` [M] camp_r = self.db.run_query(camp_q)
- `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:342` [M] iks_result = compute_iks(self.db)
- `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:372` [M] records = self.db.run_query(counts_query)
- `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:378` [M] chain_r = self.db.run_query(chain_q)
- `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:383` [M] iks_result = compute_iks(self.db)

### gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:290` [R] "dual_write reads from SQLite primary and is not authoritative"
- `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:292` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/services/governance_report.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/governance_report.py:8` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py

CONFIRMED family / G040; individual branches may be test/demo/parser-only.

- `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:22` [M] from app.db.graph_client import soc_decision_where

### gen-ai-roi-demo-v4-v50/backend/app/services/iks.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:34` [M] from app.db.graph_client import soc_decision_where
- `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:153` [M] from app.db.graph_client import graph_client
- `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:314` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py

CONFIRMED family / G017, G018; individual branches may be test/demo/parser-only.

- `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:31` [M] from app.db.graph_client import soc_decision_where

### gen-ai-roi-demo-v4-v50/backend/app/services/model_swap.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/model_swap.py:11` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/services/override_detector.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/override_detector.py:53` [R] (e.g. app.db.graph_client.graph_client).

### gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:623` [M] from app.db.graph_client import graph_client
- `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:662` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/services/shadow_promotion.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_promotion.py:136` [M] from app.db.graph_client import graph_client as default_graph_client
- `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_promotion.py:156` [M] from app.db.graph_client import graph_client as default_graph_client
- `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_promotion.py:226` [M] from app.db.graph_client import graph_client as default_graph_client

### gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py:166` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/services/simulation.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/simulation.py:286` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/services/snapshots.py

CONFIRMED family / G018; individual branches may be test/demo/parser-only.

- `gen-ai-roi-demo-v4-v50/backend/app/services/snapshots.py:40` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py:261` [M] from app.db.graph_client import soc_decision_where

### gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:20` [M] from app.db.graph_client import soc_decision_where

### gen-ai-roi-demo-v4-v50/backend/app/services/timestamp_backfill.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/timestamp_backfill.py:23` [M] from app.db.graph_client import graph_client, soc_decision_where  # noqa: PLC0415

### gen-ai-roi-demo-v4-v50/backend/app/services/triage.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `gen-ai-roi-demo-v4-v50/backend/app/services/triage.py:23` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py

CONFIRMED family / G019; individual branches may be test/demo/parser-only.

- `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:24` [M] from app.db.graph_client import soc_decision_where

### gen-ai-roi-demo-v4-v50/backend/cleanup_decisions.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/backend/cleanup_decisions.py:2` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/diagnose_decisions.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/backend/diagnose_decisions.py:2` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/ingest_shadow_decisions.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/backend/ingest_shadow_decisions.py:23` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/scripts/ingest_synthetic_decisions.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/backend/scripts/ingest_synthetic_decisions.py:25` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/scripts/migrate_datetime_to_epoch.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/backend/scripts/migrate_datetime_to_epoch.py:37` [M] from app.db.graph_client import graph_client  # noqa: E402

### gen-ai-roi-demo-v4-v50/backend/scripts/run_sentinel_mock.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/backend/scripts/run_sentinel_mock.py:36` [M] from app.db.graph_client import graph_client                           # noqa: E402

### gen-ai-roi-demo-v4-v50/backend/scripts/seed_verified_decisions.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/backend/scripts/seed_verified_decisions.py:605` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/scripts/sprint/a2_production_scorer.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/backend/scripts/sprint/a2_production_scorer.py:19` [R] persisted = [p for p in ["data/soc_centroids.npy", "data/centroids.json", "data/soc_authority.sqlite3"] if os.path.exists(p)]

### gen-ai-roi-demo-v4-v50/backend/scripts/verify_rollback_readiness.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/backend/scripts/verify_rollback_readiness.py:3` [R] The script never mutates AGE or SQLite.  It records the configured graph,
- `gen-ai-roi-demo-v4-v50/backend/scripts/verify_rollback_readiness.py:4` [R] best-effort live node counts, and the configured SQLite fallback path so the
- `gen-ai-roi-demo-v4-v50/backend/scripts/verify_rollback_readiness.py:21` [R] BACKEND_DIR / "data" / "soc.db",
- `gen-ai-roi-demo-v4-v50/backend/scripts/verify_rollback_readiness.py:22` [R] BACKEND_DIR / "data" / "graph.db",
- `gen-ai-roi-demo-v4-v50/backend/scripts/verify_rollback_readiness.py:25` [R] "SOC_ROLLBACK_SQLITE_PATH",
- `gen-ai-roi-demo-v4-v50/backend/scripts/verify_rollback_readiness.py:26` [R] "ROLLBACK_SQLITE_PATH",
- `gen-ai-roi-demo-v4-v50/backend/scripts/verify_rollback_readiness.py:27` [R] "SQLITE_FALLBACK_PATH",
- `gen-ai-roi-demo-v4-v50/backend/scripts/verify_rollback_readiness.py:36` [R] configured.append(Path(data_dir) / "soc.db")
- `gen-ai-roi-demo-v4-v50/backend/scripts/verify_rollback_readiness.py:120` [R] "sqlite_fallback": fallback,

### gen-ai-roi-demo-v4-v50/backend/seed_neo4j.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/backend/seed_neo4j.py:24` [M] from app.db.graph_client import graph_client

### gen-ai-roi-demo-v4-v50/backend/support/setup/repair_zero_day_timestamps.py

ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material.

- `gen-ai-roi-demo-v4-v50/backend/support/setup/repair_zero_day_timestamps.py:298` [M] from app.db.graph_client import graph_client  # noqa: PLC0415

### gen-ai-roi-demo-v4-v50/deep_audit.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/deep_audit.py:16` [R] import sqlite3
- `gen-ai-roi-demo-v4-v50/deep_audit.py:23` [R] db_path = os.path.join(".code-review-graph", "graph.db")
- `gen-ai-roi-demo-v4-v50/deep_audit.py:24` [R] conn = sqlite3.connect(db_path)
- `gen-ai-roi-demo-v4-v50/deep_audit.py:25` [R] conn.row_factory = sqlite3.Row

### gen-ai-roi-demo-v4-v50/full_audit.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/full_audit.py:5` [R] import sqlite3
- `gen-ai-roi-demo-v4-v50/full_audit.py:15` [R] db_path = os.path.join(".code-review-graph", "graph.db")
- `gen-ai-roi-demo-v4-v50/full_audit.py:20` [R] conn = sqlite3.connect(db_path)
- `gen-ai-roi-demo-v4-v50/full_audit.py:21` [R] conn.row_factory = sqlite3.Row

### gen-ai-roi-demo-v4-v50/graphify-out/soc_triage_source_review_20260609_023852/backend_app_routers_triage.py

ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material.

- `gen-ai-roi-demo-v4-v50/graphify-out/soc_triage_source_review_20260609_023852/backend_app_routers_triage.py:34` [M] from app.db.neo4j import neo4j_client

### gen-ai-roi-demo-v4-v50/prompt0_structural_map.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/prompt0_structural_map.py:6` [R] import sqlite3
- `gen-ai-roi-demo-v4-v50/prompt0_structural_map.py:9` [R] db_path = os.path.join(".code-review-graph", "graph.db")
- `gen-ai-roi-demo-v4-v50/prompt0_structural_map.py:14` [R] conn = sqlite3.connect(db_path)
- `gen-ai-roi-demo-v4-v50/prompt0_structural_map.py:15` [R] conn.row_factory = sqlite3.Row

### gen-ai-roi-demo-v4-v50/prompt0_tab_content_map.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/prompt0_tab_content_map.py:5` [R] import sqlite3
- `gen-ai-roi-demo-v4-v50/prompt0_tab_content_map.py:8` [R] db_path = os.path.join(".code-review-graph", "graph.db")
- `gen-ai-roi-demo-v4-v50/prompt0_tab_content_map.py:13` [R] conn = sqlite3.connect(db_path)
- `gen-ai-roi-demo-v4-v50/prompt0_tab_content_map.py:14` [R] conn.row_factory = sqlite3.Row

### gen-ai-roi-demo-v4-v50/query_graph.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/query_graph.py:1` [C] """Query the code-review-graph SQLite DB directly for BACKLOG-069 verification."""
- `gen-ai-roi-demo-v4-v50/query_graph.py:2` [R] import sqlite3, os
- `gen-ai-roi-demo-v4-v50/query_graph.py:4` [R] db_path = os.path.join(".code-review-graph", "graph.db")
- `gen-ai-roi-demo-v4-v50/query_graph.py:9` [R] conn = sqlite3.connect(db_path)
- `gen-ai-roi-demo-v4-v50/query_graph.py:10` [R] conn.row_factory = sqlite3.Row
- `gen-ai-roi-demo-v4-v50/query_graph.py:17` [R] tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

### gen-ai-roi-demo-v4-v50/query_graph2.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/query_graph2.py:1` [C] """Query code-review-graph SQLite -- fixed for actual schema."""
- `gen-ai-roi-demo-v4-v50/query_graph2.py:2` [R] import sqlite3
- `gen-ai-roi-demo-v4-v50/query_graph2.py:5` [R] db_path = os.path.join(".code-review-graph", "graph.db")
- `gen-ai-roi-demo-v4-v50/query_graph2.py:10` [R] conn = sqlite3.connect(db_path)
- `gen-ai-roi-demo-v4-v50/query_graph2.py:11` [R] conn.row_factory = sqlite3.Row

### gen-ai-roi-demo-v4-v50/query_graph3.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/query_graph3.py:6` [R] import sqlite3
- `gen-ai-roi-demo-v4-v50/query_graph3.py:9` [R] db_path = os.path.join(".code-review-graph", "graph.db")
- `gen-ai-roi-demo-v4-v50/query_graph3.py:10` [R] conn = sqlite3.connect(db_path)
- `gen-ai-roi-demo-v4-v50/query_graph3.py:11` [R] conn.row_factory = sqlite3.Row

### gen-ai-roi-demo-v4-v50/query_graph4_final.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/query_graph4_final.py:2` [R] import sqlite3
- `gen-ai-roi-demo-v4-v50/query_graph4_final.py:5` [R] db_path = os.path.join(".code-review-graph", "graph.db")
- `gen-ai-roi-demo-v4-v50/query_graph4_final.py:6` [R] conn = sqlite3.connect(db_path)
- `gen-ai-roi-demo-v4-v50/query_graph4_final.py:7` [R] conn.row_factory = sqlite3.Row

### gen-ai-roi-demo-v4-v50/query_graph5_alerts.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/query_graph5_alerts.py:15` [R] import sqlite3
- `gen-ai-roi-demo-v4-v50/query_graph5_alerts.py:18` [R] db_path = os.path.join(".code-review-graph", "graph.db")
- `gen-ai-roi-demo-v4-v50/query_graph5_alerts.py:19` [R] conn = sqlite3.connect(db_path)
- `gen-ai-roi-demo-v4-v50/query_graph5_alerts.py:20` [R] conn.row_factory = sqlite3.Row

### gen-ai-roi-demo-v4-v50/query_graph6_statemanager.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/query_graph6_statemanager.py:11` [R] import sqlite3
- `gen-ai-roi-demo-v4-v50/query_graph6_statemanager.py:14` [R] db_path = os.path.join(".code-review-graph", "graph.db")
- `gen-ai-roi-demo-v4-v50/query_graph6_statemanager.py:15` [R] conn = sqlite3.connect(db_path)
- `gen-ai-roi-demo-v4-v50/query_graph6_statemanager.py:16` [R] conn.row_factory = sqlite3.Row

### gen-ai-roi-demo-v4-v50/query_graph7_schema.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/query_graph7_schema.py:10` [R] import sqlite3
- `gen-ai-roi-demo-v4-v50/query_graph7_schema.py:13` [R] db_path = os.path.join(".code-review-graph", "graph.db")
- `gen-ai-roi-demo-v4-v50/query_graph7_schema.py:14` [R] conn = sqlite3.connect(db_path)
- `gen-ai-roi-demo-v4-v50/query_graph7_schema.py:15` [R] conn.row_factory = sqlite3.Row

### gen-ai-roi-demo-v4-v50/scripts/ingest_shadow_decisions.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/scripts/ingest_shadow_decisions.py:21` [C] # Run this from gen-ai-roi-demo-v4-v50/backend/ so app.db.neo4j resolves.
- `gen-ai-roi-demo-v4-v50/scripts/ingest_shadow_decisions.py:26` [M] from app.db.neo4j import neo4j_client

### gen-ai-roi-demo-v4-v50/scripts/preseed_demo_scenarios.py

OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution.

- `gen-ai-roi-demo-v4-v50/scripts/preseed_demo_scenarios.py:171` [R] module = __import__("app.db.graph_client", fromlist=["graph_client"])

### gen-ai-roi-demo-v4-v50/support/setup/rebuild_neo4j_v6.py

ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material.

- `gen-ai-roi-demo-v4-v50/support/setup/rebuild_neo4j_v6.py:46` [M] from app.db.graph_client import graph_client  # noqa: E402  (after sys.path insert)

### s2p-copilot/backend/app/framework/intervention_controls.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `s2p-copilot/backend/app/framework/intervention_controls.py:156` [M] self.db = db_client
- `s2p-copilot/backend/app/framework/intervention_controls.py:238` [M] result = await self.db.run_query(
- `s2p-copilot/backend/app/framework/intervention_controls.py:264` [M] graph_service=self.db,
- `s2p-copilot/backend/app/framework/intervention_controls.py:415` [M] rows = await self.db.run_query(
- `s2p-copilot/backend/app/framework/intervention_controls.py:450` [M] rows = await self.db.run_query(
- `s2p-copilot/backend/app/framework/intervention_controls.py:501` [M] await self.db.run_query(

### s2p-copilot/backend/app/main.py

CONFIRMED family / G024, G048, G052; individual branches may be test/demo/parser-only.

- `s2p-copilot/backend/app/main.py:2` [R] import sqlite3
- `s2p-copilot/backend/app/main.py:46` [R] self.conn = sqlite3.connect(path, check_same_thread=False)
- `s2p-copilot/backend/app/main.py:308` [R] str(DATA_DIR / "s2p.db"),
- `s2p-copilot/backend/app/main.py:410` [C] # There is no production SQLite side store: AGE capability failures surface
- `s2p-copilot/backend/app/main.py:415` [R] DATA_DIR / "s2p.db",
- `s2p-copilot/backend/app/main.py:499` [R] **_vld_k_router_kwargs(DATA_DIR / "k_utility.db", len(S2PDomainConfig.factors)),

### s2p-copilot/backend/app/routers/framework_router.py

OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment.

- `s2p-copilot/backend/app/routers/framework_router.py:9` [R] app.db.*

### s2p-copilot/backend/app/s2p_graph_status.py

CONFIRMED family / G052, G066; individual branches may be test/demo/parser-only.

- `s2p-copilot/backend/app/s2p_graph_status.py:4` [R] store or change the authoritative SQLite runtime path.
- `s2p-copilot/backend/app/s2p_graph_status.py:35` [R] "Historical SQLite records are not visible in AGE-active mode unless migrated."
- `s2p-copilot/backend/app/s2p_graph_status.py:77` [R] "S2P_SHARED_GRAPH_AUTHORIZED", "CI_ALLOW_SQLITE_FALLBACK",
- `s2p-copilot/backend/app/s2p_graph_status.py:93` [R] os.environ["S2P_ACTIVE_GRAPH_BACKEND"] = "sqlite"
- `s2p-copilot/backend/app/s2p_graph_status.py:94` [R] os.environ["CI_ALLOW_SQLITE_FALLBACK"] = "1"
- `s2p-copilot/backend/app/s2p_graph_status.py:142` [R] requested_backend: str = "sqlite"
- `s2p-copilot/backend/app/s2p_graph_status.py:158` [R] message = "S2P_ACTIVE_GRAPH_BACKEND must be 'sqlite' or 'age'"
- `s2p-copilot/backend/app/s2p_graph_status.py:160` [R] if graph_config.backend not in {"sqlite", "age"}:
- `s2p-copilot/backend/app/s2p_graph_status.py:162` [R] "S2P_ACTIVE_GRAPH_BACKEND must be 'sqlite' or 'age'"
- `s2p-copilot/backend/app/s2p_graph_status.py:165` [R] if graph_config.backend == "sqlite" and "S2P_ACTIVE_AGE_GRAPH" not in source:
- `s2p-copilot/backend/app/s2p_graph_status.py:182` [R] if self.requested_backend == "sqlite":
- `s2p-copilot/backend/app/s2p_graph_status.py:415` [R] "active_backend": "age" if age_active else "sqlite",
- `s2p-copilot/backend/app/s2p_graph_status.py:417` [R] "sqlite_authoritative": not age_active,
- `s2p-copilot/backend/app/s2p_graph_status.py:423` [R] "graph_kind": "sqlite" if not requested_age else graph_kind,
- `s2p-copilot/backend/app/s2p_graph_status.py:440` [R] "historical_sqlite_count_warning": _HISTORICAL_VISIBILITY_WARNING,
- `s2p-copilot/backend/app/s2p_graph_status.py:442` [R] "Unset S2P_ACTIVE_GRAPH_BACKEND or set it to sqlite.",
- `s2p-copilot/backend/app/s2p_graph_status.py:444` [R] "Rollback routes new writes to SQLite; it does not reconcile AGE data.",
- `s2p-copilot/backend/app/s2p_graph_status.py:479` [R] "Historical SQLite migration/backfill is not in scope.",

### s2p-copilot/backend/app/services/proposal_service.py

CONFIRMED family / G045; individual branches may be test/demo/parser-only.

- `s2p-copilot/backend/app/services/proposal_service.py:6` [R] import sqlite3
- `s2p-copilot/backend/app/services/proposal_service.py:42` [C] """Restart-safe SQLite store for proposals and canonical outcomes."""
- `s2p-copilot/backend/app/services/proposal_service.py:45` [R] self._connection = sqlite3.connect(db_path, check_same_thread=False)

### s2p-copilot/backend/demo/s2p_demo.py

DEMO/REFERENCE — local simulation/artifact path; see G057–G059.

- `s2p-copilot/backend/demo/s2p_demo.py:12` [R] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
- `s2p-copilot/backend/demo/s2p_demo.py:221` [R] graph_store=SQLiteGraphStore(":memory:", domain="s2p", decision_id_prefix="S2P-DEMO-"),

## Appendix B — Complete Fixture / Fallback Reference Index

All matched line numbers are listed, without first-N truncation. The disposition applies to the file/call family, not a blanket claim that every line is a live fallback. json.loads on an AGE property is serialization, not a separate store; external-source mock/cache behavior is a semantic ingestion question, not automatically an AGE outage. OPEN rows remain explicitly unresolved candidates.

| File | All matching lines | Disposition |
|---|---|---|
| `ci-platform/ci_platform/auth/saml.py` | 111 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `ci-platform/ci_platform/connectors/celonis.py` | 1, 4, 70, 79, 95, 97, 99, 102, 107, 109, 111, 117, 118, 166, 167, 179, 181, 183, 185, 192, 201, 211, 231, 232, 233, 234, 237, 238, 239, 240, 247, 248, 249, 250, 287, 292, 295, 310, 311, 315, 316, 324, 325, 329, 342, 343, 345, 350, 354, 360, 363, 367, 374, 380, 390, 391, 393, 399, 406, 413, 416, 424, 434, 435, 437, 443, 451, 458, 461, 467, 475, 492, 498, 499, 504, 505, 516, 522, 527, 528, 530, 558, 559, 560, 561 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `ci-platform/ci_platform/connectors/sap.py` | 1, 3, 70, 72, 81, 91, 103, 104, 111, 113, 115, 117, 119, 121, 127, 128, 146, 147, 161, 177, 192, 208, 210, 214, 254, 255, 256, 261, 266, 269, 270, 281, 282, 292, 293, 298, 299, 306, 307, 314, 315, 321, 327, 328, 340, 364, 365, 468, 469, 470, 471, 494, 496, 498 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `ci-platform/ci_platform/copilot_core/counters.py` | 160, 537, 538 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `ci-platform/ci_platform/graph/age_client.py` | 12, 18, 152, 172, 218, 245, 300, 314, 334, 456, 488, 499 | CONFIRMED family / G009; individual branches may be test/demo/parser-only. |
| `ci-platform/ci_platform/graph/age_graph_store.py` | 140, 158, 548, 1948, 2806, 3847, 3854, 4014, 4015, 4051, 4052, 4055 | CONFIRMED family / G007, G008, G038, G039, G040, G047; individual branches may be test/demo/parser-only. |
| `ci-platform/scripts/seed_dataops_graph.py` | 76 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/.codex_fast_q_demand.py` | 4 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/.codex_search_noK.py` | 4 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/.codex_trading_search2.py` | 7 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/dataops/backend/app/ae_router.py` | 24, 27, 28, 80 | CONFIRMED family / G022; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/dataops/backend/app/celonis_connector.py` | 1, 113 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/app/connector_cache.py` | 38, 67 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/app/connectors/dq_benchmark_provider.py` | 102, 118, 168, 170, 172, 205, 234, 244, 270 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/app/context_router.py` | 1, 82, 97, 165, 355, 520, 523, 531, 532, 545, 546, 549, 550, 551, 705, 859, 873, 892, 1042, 1255, 1256, 1257, 1273, 1286, 1297, 1336, 1367, 1390, 1425, 1427, 1431, 1433, 1434, 1558, 1570, 1588, 1589 | CONFIRMED family / G012, G034; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/dataops/backend/app/data_helpers.py` | 4, 8, 9, 10, 12 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/app/dataops_governance.py` | 59, 107, 108, 146, 148, 174, 186, 204 | CONFIRMED family / G027; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/dataops/backend/app/di_config.py` | 55 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/app/enterprise_router.py` | 32, 33, 35, 59, 63, 74, 75, 76, 77, 116, 118, 123, 126, 128, 131, 135, 137, 138, 139, 140, 161, 172, 174, 178, 180, 186, 198, 201, 202, 203, 207, 210, 211, 237 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/app/evidence_provider.py` | 43, 304, 307, 308, 310, 345, 346, 349, 350, 351, 352, 355, 382 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/app/graph_queries.py` | 1, 19, 72, 74, 104, 108, 111, 122, 129, 141, 223, 224, 232, 233, 234, 235, 251, 257, 286, 300, 336, 337, 338, 339, 399, 403, 421, 430, 459, 463, 469, 476, 482, 498, 523, 544, 566, 593, 615, 618, 621 | CONFIRMED family / G043, G051; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/dataops/backend/app/main.py` | 239, 261, 284, 465, 467, 469, 472, 527, 547, 679, 783, 940 | CONFIRMED family / G024, G026, G027, G043, G047, G048, G051; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/dataops/backend/app/models/investigation.py` | 45 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/app/routers/dataops_status.py` | 29, 122, 142, 143, 145, 146, 147, 151, 160, 166, 168, 169, 170, 174, 187, 192, 193, 203, 204, 208, 211 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/app/sap_connector.py` | 1, 19, 115 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/app/seed_graph.py` | 18, 74, 76, 77 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/app/services/cohort_status.py` | 74, 90, 91, 231 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/app/services/investigation_loop.py` | 150, 168, 169, 172 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py` | 118, 130, 173, 247, 291, 340, 354, 367, 381 | CONFIRMED family / G011; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/dataops/backend/scripts/evaluate_multihop_stage1.py` | 213 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/dataops/backend/scripts/measure_rho_dataops.py` | 38, 39 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/dataops/backend/scripts/validate_stage1.py` | 4 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/dataops/backend/scripts/validate_use_cases.py` | 36, 37, 53, 81 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/purchasing/backend/app/connectors/__init__.py` | 4, 5, 6 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/connectors/commodity_provider.py` | 10, 20, 26, 32, 37, 61, 62, 64, 88, 226, 230, 232, 236 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/connectors/commodity_source.py` | 79, 121 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/connectors/mock_commodity.py` | 1, 7, 84, 85 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/connectors/mock_qbo.py` | 11, 22, 23, 26, 36, 115, 116, 344, 351 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/connectors/mock_toast.py` | 7, 17, 18, 21, 25, 43, 49, 94, 110 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/connectors/qbo_connector.py` | 295, 299, 325, 332 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/context_router.py` | 15, 44, 45, 46, 294 | CONFIRMED family / G013; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/purchasing/backend/app/data_cache.py` | 1, 3, 4, 5, 31, 38 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/data_helpers.py` | 1, 22, 39, 45, 46, 53, 76, 77, 91, 93, 94, 96, 98 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/evidence_provider.py` | 205, 216 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/evidence_providers.py` | 1, 4, 54, 64, 65, 68, 75, 88, 110, 114, 152, 155, 162, 173, 174, 177, 178, 179, 270, 274, 285 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/factors/weather_forecast.py` | 127, 131 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/inventory_router.py` | 19 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/investigation_config.py` | 50, 56, 63, 64, 71 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/main.py` | 310, 312, 314, 317, 369, 388, 596, 655, 870, 880, 881 | CONFIRMED family / G013, G024, G026, G033, G048, G050; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/purchasing/backend/app/routers/auto_order_router.py` | 10, 113, 114, 115, 172 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/routers/discovery_router.py` | 24 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py` | 84, 90, 93 | CONFIRMED family / G013; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/purchasing/backend/app/routers/match.py` | 223, 228, 229, 305, 325 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/routers/par_router.py` | 10, 11, 35 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/routers/pos_router.py` | 13, 29, 31, 72, 82, 83, 84, 85, 86, 87, 88, 95, 96, 103, 111, 112, 113, 114, 121, 122, 189, 196, 197, 198 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py` | 88 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/routers/qbo_router.py` | 11 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/routers/queue.py` | 10, 11, 73 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/routers/scorecard_router.py` | 10, 11, 104, 116 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/routers/spend_router.py` | 11, 35, 50, 124, 142 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/seed_graph.py` | 20 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/services/cohort_status.py` | 6, 114, 138, 143, 303 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/services/commodity_data_provider.py` | 11, 31, 55, 60, 67, 116, 117, 143, 144, 148, 151, 152, 155, 195, 196, 199, 202, 206, 211, 216, 217 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/services/cross_discovery.py` | 45 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/services/event_planner.py` | 114, 118 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/services/menu_engineer.py` | 105, 109 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/services/par_optimizer.py` | 4, 56, 234 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py` | 114, 150, 244 | CONFIRMED family / G013, G028; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/purchasing/backend/app/services/supplier_scorecard.py` | 246, 247, 249 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/vld_preseed.py` | 1, 5, 20, 36, 45 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/cli.py` | 99, 457 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/purchasing/backend/generators/__init__.py` | 1 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/purchasing/backend/generators/purchasing_synthetic.py` | 1, 3, 444, 455 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/purchasing/backend/scripts/evaluate_multihop_stage1.py` | 232 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/purchasing/backend/scripts/validate_stage1.py` | 4 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/trading/backend/app/cli_sdk.py` | 146 | CONFIRMED family / G063; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/app/connectors/ibkr_connector.py` | 112, 113 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/trading/backend/app/connectors/market_source.py` | 107, 112, 114, 115 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/trading/backend/app/connectors/yfinance_provider.py` | 41 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/trading/backend/app/context_router.py` | 55, 62, 66, 67, 69, 115, 118, 311, 312, 323, 328, 329, 344, 345, 350, 362, 364, 377, 387, 389, 480, 518, 519 | CONFIRMED family / G029, G030, G032; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/app/data_helpers.py` | 8, 9, 13, 15, 16, 18, 20 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/trading/backend/app/evidence_providers.py` | 1, 4, 55, 65, 66, 68, 74, 87, 102, 106, 143, 146, 153, 164, 165, 168, 169, 170, 312, 316, 327 | CONFIRMED family / G020; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/app/evidence.py` | 412, 416, 418 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/trading/backend/app/graph_status.py` | 83 | CONFIRMED family / G049, G055, G065; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/app/investigation_config.py` | 51, 57, 66 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/trading/backend/app/main.py` | 272, 274, 276, 279, 332, 351, 496, 603, 604 | CONFIRMED family / G023, G024, G026, G031, G048, G049, G058; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py` | 304 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/trading/backend/app/routers/journal.py` | 565 | CONFIRMED family / G029; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/app/seed_graph.py` | 28 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/trading/backend/app/services/claim_gate.py` | 178 | CONFIRMED family / G020; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/app/services/cohort_status.py` | 83, 99, 100, 240 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/trading/backend/app/services/market_data_provider.py` | 37, 42, 47, 167, 168, 170, 171, 173, 176, 213, 214, 217, 218, 219, 223, 226, 227, 228, 234, 235, 238, 246 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/trading/backend/app/services/promotion_state.py` | 65 | CONFIRMED family / G031; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/app/services/promotion.py` | 42 | CONFIRMED family / G031; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/app/services/regime_recommender.py` | 37, 38, 57, 115, 116, 138, 141, 206, 207, 216, 217, 225, 235, 236, 245, 246, 282, 283, 290, 291, 298, 311, 312, 319, 320, 322, 355, 356, 461, 474, 482, 484, 488, 505, 513, 524, 529, 530, 532, 533 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/trading/backend/app/services/regime_scoring.py` | 442, 457 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/trading/backend/cli.py` | 76, 88, 787 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/trading/backend/generators/trading_synthetic.py` | 1 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/trading/backend/scripts/evaluate_multihop_stage1.py` | 230, 246 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/trading/backend/scripts/validate_stage1.py` | 4 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/trading/scripts/volatility_walkthrough.py` | 67 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/ci_trading/quant/integrations.py` | 85 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/copilot_sdk/ae/gate.py` | 30, 40, 41 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/ae/store.py` | 33, 36 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/ae/types.py` | 29, 39 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/backend/conservation_utils.py` | 377, 378 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/backend/di_router.py` | 256 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/backend/discovery_router.py` | 85, 91 | CONFIRMED family / G047; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py` | 566, 567, 965, 976 | CONFIRMED family / G003; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/backend/signal_store.py` | 113, 128 | CONFIRMED family / G026; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/backend/transfer.py` | 62, 93, 95, 143, 144 | CONFIRMED family / G044; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/connectors/airflow_connector.py` | 58 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/connectors/dbt_connector.py` | 44 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/connectors/mock_weather.py` | 9 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/demo/bundle.py` | 25 | CONFIRMED family / G058; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/demo/preseed.py` | 129, 162 | CONFIRMED family / G023, G057; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/di/catalog.py` | 99 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/di/claude_parser.py` | 49 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/di/combination_discovery.py` | 23, 117, 119, 160, 210, 211, 225, 233, 239 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/di/enrichment.py` | 35, 130, 178, 229, 232 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/di/query_providers.py` | 196, 301, 303, 305 | CONFIRMED family / G048; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/di/query_service.py` | 246, 594, 595 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/di/valuation.py` | 266, 267, 268 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/diagnostics/platform_dump.py` | 30 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/evidence/f26.py` | 21, 24, 39, 41, 42, 43, 44, 62, 73 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/evidence/gate.py` | 127 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/evolution/context_selector.py` | 67 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/evolution/graph_store.py` | 47 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/evolution/shadow.py` | 88 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/evolution/variant_store.py` | 406 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/framework/checkpoint.py` | 147, 166, 181 | CONFIRMED family / G010; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/framework/composite_gate.py` | 37 | CONFIRMED family / G010; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/framework/intervention_controls.py` | 311 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/framework/learning_state.py` | 70, 108 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/framework/narrative_base.py` | 85, 86, 95 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/framework/similar_cases_base.py` | 109, 179 | CONFIRMED family / G010; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py` | 101 | IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045). |
| `copilot-sdk/copilot_sdk/graph/enrichment.py` | 56, 57, 58, 59, 94, 103, 159 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/graph/outbox.py` | 59 | IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045). |
| `copilot-sdk/copilot_sdk/graph/projection.py` | 107 | CONFIRMED family / G040; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/graph/read_diff_runner.py` | 109, 188, 219, 247, 248, 249, 250 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py` | 52, 220, 2616, 2726 | IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045). |
| `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py` | 181 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py` | 367, 378 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py` | 474, 488, 493, 497, 693, 814, 818, 819, 877, 898, 908, 912, 913, 942 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/copilot_sdk/migrate/verify_state.py` | 184 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/copilot_sdk/outbox/store.py` | 183 | IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045). |
| `copilot-sdk/copilot_sdk/outcome/ledger.py` | 71, 101 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/promotion/core.py` | 204, 393, 395, 397, 400, 402, 404 | CONFIRMED family / G045; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/reporting/weekly.py` | 357, 370 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/scoring/investigation.py` | 126 | CONFIRMED family / G024, G025; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py` | 274, 448 | CONFIRMED family / G002, G055; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/scoring/presets/dataops.py` | 103 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/scoring/presets/purchasing.py` | 109 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/scoring/presets/trading.py` | 127 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py` | 222, 292, 596, 879, 882, 896, 933, 952, 2097, 2738 | CONFIRMED family / G001, G002, G003, G004, G006, G042, G044, G055; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/scoring/verification/price.py` | 88 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/scoring/verification/weather.py` | 73, 88 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/situation/templates.py` | 92, 129 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/substantiation/chef_oracle.py` | 72, 86, 113, 133 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/substantiation/dataops_oracle.py` | 62, 80, 111, 135 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/substantiation/declaration.py` | 7, 10 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/substantiation/populate_registry.py` | 179, 184, 185, 186, 198, 203, 204, 205, 217, 222, 223, 224, 459 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/substantiation/tiers.py` | 24 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/substantiation/trader_oracle.py` | 67, 81, 108, 128 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/transfer/chain_transfer.py` | 121, 125 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/transfer/registry.py` | 148 | CONFIRMED family / G045; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/twin/models.py` | 104 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/twin/store.py` | 80 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/demo.py` | 25, 322, 866, 877, 941, 1348, 1496, 1563, 1702, 1830 | CONFIRMED family / G054, G057, G063; individual branches may be test/demo/parser-only. |
| `copilot-sdk/e2e/fix_flaky_health.py` | 6 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/e2e/fix_health_retry.py` | 1, 8 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/e2e/fix_strict_mode.py` | 101 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/examples/conservation_demo/conservation_demo.py` | 17, 46 | DEMO/REFERENCE — local simulation/artifact path; see G057–G059. |
| `copilot-sdk/experiments/htrust/run_htrust_v2.py` | 97 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/jm_extracted/jm_phase3_corrected.py` | 458, 491, 522, 523, 524, 525, 527 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/jm_extracted/jm_phase3_finalize.py` | 119, 232 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/jm_extracted/jm_redesign.py` | 99, 145, 252, 254, 257 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/jm_extracted/render_modified_charts.py` | 65 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/c1_c6_campaign_v1.py` | 270, 271, 272 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/charts/pub_safety_multiplier.py` | 14 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/charts/pub_safety_rate_threshold.py` | 18 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/external_baseline.py` | 1, 5, 8, 45, 66, 67, 68, 69, 74, 76, 79, 83, 87, 88, 123, 125, 128, 130, 131, 170, 216, 236, 240, 241, 246, 247, 253, 254, 257, 260, 261, 265, 266, 267, 268, 274, 277, 281, 282, 283, 284, 303, 319, 321 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/harnesses/safety_layer_characterization_r2.py` | 127 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/harnesses/safety_layer_characterization.py` | 36 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/k14_compounding_noise.py` | 22 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/k14_generate_k2_labels.py` | 1, 5, 7, 42, 72, 98, 119, 133, 147 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/k14_validation_tier.py` | 40, 251 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/render_publication_figures.py` | 96, 97, 98, 124 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/scripts/merge_supplement.py` | 9, 11 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/scripts/validate_astra_scenarios.py` | 5 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/scripts/vld_graph_reasoning_experiments_v2.py` | 48 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/scripts/vld_universal_eval_v2.py` | 16 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/scripts/vld_with_without_v2.py` | 43 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_adversarial_saves_hurts_v1.py` | 41 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_cons_pd_decision_features_v1.py` | 248 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_cons_pd_routing_analysis_v1.py` | 135 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_conservation_characterization_v1.py` | 42 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_conservation_lag_c5_v1.py` | 58, 554, 555, 559, 560, 588, 589, 593, 594, 630, 631, 635, 636, 640, 641, 642, 698, 699, 706, 707, 709, 714, 722, 783, 897 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_conservation_perdecision_signals_v1.py` | 262 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_conservation_stage2_composite_v1.py` | 39 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_conservation_stage3_track_v1.py` | 46 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_d2_control_signal_v1.py` | 119, 134, 135, 142, 147, 153, 158, 170 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_decision_complexity_v1.py` | 30, 315, 316, 317, 318, 380, 387, 388, 403, 530 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_delayed_entrant_v1.py` | 341, 411 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_eta_sweep_f1_v1.py` | 81 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_label_breadth_c3_v1.py` | 194, 293 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_moat_b2_seeds_v1.py` | 151 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_moat_b2_v1.py` | 485 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_moat_c2_mu_all_five_v1.py` | 231, 232 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_moat_mu_probe_v1.py` | 132 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_oracle_ceiling_diagnostic_v1.py` | 148, 175 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_rec_action_readout_v1.py` | 202, 280, 281, 282 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_rl_characterization_full_v1.py` | 291 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_rl_ctrl_fork_v1.py` | 136, 306, 469 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_rl_ctrl_reconcile_v1.py` | 24, 25, 83 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_rl_ctrl_trajectory_live_v2.py` | 78 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_rl_ctrl_trajectory_live_v3.py` | 19 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_rl_ctrl_trajectory_optC.py` | 175, 206 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_rl_ctrl_trajectory_v1.py` | 29 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_rl_ctrl2c_constrained_v1.py` | 37 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/experiments/vld/vld_rl1_characterization_v1.py` | 373 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/integrity/benchmark_fixture.py` | 1, 3, 30, 68, 141, 143, 146 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/integrity/load_benchmark.py` | 1, 11, 17, 24, 26 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/render_chart1.py` | 25 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/render_chart2.py` | 14 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/render_chart3.py` | 15 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/render_k14_agreement.py` | 14 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/render_k14_noise.py` | 14 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/age_complete_inventory.py` | 72, 149, 162, 188, 228 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/age_pf_investigate.py` | 119, 120, 122, 126, 134 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/age_preflight.py` | 224, 225, 228, 232, 233 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/age_v35_review_checks.py` | 54, 58, 59 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/analyze_factor0_panel.py` | 35, 125, 126, 129, 321 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/backfill_jm_edges.py` | 113 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/benchmark_age_latency.py` | 37 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/budget_accuracy_frontier.py` | 307, 315 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/build_result_manifest.py` | 21, 46, 48, 50, 55, 56, 63, 69, 249, 256, 257, 258, 262, 330, 331, 350, 352, 353, 373 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/create_age_indexes.py` | 57, 58, 59, 63, 65, 67 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/d1_recursion_trace_v1.py` | 36, 95, 104, 105, 111 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/demo_truth_preflight.py` | 74, 128, 133 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/external_baseline_full.py` | 9, 16, 18, 30, 32, 118, 123, 127, 141, 160, 254, 263, 271, 272, 273, 274, 275, 298, 303, 309 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/factor0_debiased_battery_v4.py` | 190 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/factor0_loo_margin_v3.py` | 113 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/factor0_margin_contribution_v2.py` | 105 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/factor0_margin_contribution.py` | 90 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/gap1_adaptive_halting.py` | 244, 245, 247 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/gap2_abstention_curve.py` | 247, 263, 269 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/gap2_abstention_heldout_v1.py` | 113 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_budget_frontier_charts.py` | 41 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_cross_copilot_charts.py` | 17 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_d1_d2_paper_figures_v1.py` | 38 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_gap1_charts.py` | 32 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_gap2_charts.py` | 133 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_group_a_d_charts.py` | 233 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_group_b_c_charts.py` | 148, 220, 227, 228, 230, 239, 243, 278 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_k_learning_charts.py` | 18 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_paper_charts.py` | 69 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_q_ablation_charts.py` | 30 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_q_ablation_normalized_charts.py` | 38 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_rv_charts.py` | 22 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_rv4_ke45_charts.py` | 19 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/hero_moments.py` | 70 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/jm_v27_live_validation.py` | 61 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/k_learning_curve_cross_copilot.py` | 101, 270, 428 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/k_learning_curve_experiment.py` | 4, 55, 148 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/k_learning_curve_extended.py` | 5, 58, 132 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/mutable_flow_probe.py` | 40 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase_cycle_gate.py` | 10 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase3_cycle_gate_v3.py` | 62 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/plant_remaining_fixtures.py` | 1, 5, 17, 26, 34, 49, 58, 70, 84, 86, 88, 91 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/preseed_all_copilots.py` | 218, 270, 700, 735, 736 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/preseed_demo_fixtures.py` | 17, 49, 194, 204, 232, 233, 238 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/preseed_verification_gap.py` | 2, 4, 9, 30, 91 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/q_term_ablation_normalized.py` | 271, 272, 274, 302 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/q_term_ablation.py` | 65, 244, 245, 247, 271, 273 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py` | 92, 146, 171 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/regenerate_demo_bundles.py` | 162, 179 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/ri1_routing_k_interaction.py` | 78 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/ri5_rich_k_state.py` | 342, 367 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/routing_variant_bandit.py` | 34 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/routing_variant_gru_ablation.py` | 40 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/rv5_hierarchical.py` | 1, 14, 21 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/sc_endpoint_probe.py` | 26 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/sqlite_copilot_audit.py` | 168, 169, 390 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/trigger_warm_start.py` | 35, 54 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/validate_age_migration.py` | 137 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/verify_factor0_values.py` | 88 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/verify_l5_completion.py` | 41, 53, 102 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/support/scripts/calibrate_dataops_bootstrap.py` | 30 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `copilot-sdk/support/scripts/calibrate_purchasing_bootstrap.py` | 30 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `copilot-sdk/support/scripts/calibrate_trading_bootstrap.py` | 30 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `copilot-sdk/verify_di3.py` | 27, 62 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/verify_gold_lines.py` | 7 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/base.py` | 23 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/celonis.py` | 1, 30, 35, 51, 52, 84, 92 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/greynoise.py` | 12, 71, 83, 93, 103, 179, 197, 206, 222, 230, 231, 234, 247, 248, 249, 254, 256, 258, 260, 261, 262, 263, 378, 391 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/mitre_client.py` | 64, 74 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/nvd_client.py` | 49 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py` | 11, 69, 77, 91, 105, 119, 133, 244, 250, 266, 275, 291, 300, 301, 304, 318, 319, 320, 321, 326, 328, 330, 332, 333, 334, 335, 464, 477 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/sap.py` | 1, 31, 36, 52, 53, 86, 94 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/sentinel_mock.py` | 58, 97 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/sentinel_real.py` | 72 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/threat_intel_provider.py` | 36, 70, 82, 92, 100, 121, 139, 202, 216, 229, 256, 266, 274 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/data/alert_pool.py` | 392 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py` | 267, 1582, 1583 | CONFIRMED family / G017, G040; individual branches may be test/demo/parser-only. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py` | 50, 489, 520, 524, 557, 573, 854, 895, 900 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/orchestrator.py` | 42, 79, 91, 106, 112, 120, 130, 153, 154 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/severity.py` | 30 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/checkpoint.py` | 135, 154 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/composite_gate.py` | 37 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py` | 311 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/learning_state.py` | 70, 108 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/narrative_base.py` | 85, 86, 95 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/similar_cases_base.py` | 103, 172 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py` | 147, 524, 563, 567 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py` | 466 | CONFIRMED family / G024, G048, G053; individual branches may be test/demo/parser-only. |
| `gen-ai-roi-demo-v4-v50/backend/app/models/investigation.py` | 45 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/oracle/pipeline_test.py` | 58, 71, 113, 150 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evaluation.py` | 23, 47 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py` | 117, 128 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py` | 228, 382 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py` | 177 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py` | 264, 276, 362, 619, 621, 626, 633, 648, 650, 655, 662 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/platform.py` | 4, 42, 44, 47, 65, 67, 70, 78, 101, 103, 106, 112, 130, 132, 136, 138, 145, 163, 165, 169, 171, 178, 196, 198, 202, 204, 211 | CONFIRMED family / G037; individual branches may be test/demo/parser-only. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/simulation.py` | 73, 75 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py` | 1182, 1794, 1801, 2421, 2761, 2777, 2801, 2909, 2926, 3084, 3092, 3102, 3114, 3173, 3180, 3230, 3347, 3471, 4375 | CONFIRMED family / G016, G017, G041; individual branches may be test/demo/parser-only. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py` | 1749, 2186, 3089 | CONFIRMED family / G017, G018, G041; individual branches may be test/demo/parser-only. |
| `gen-ai-roi-demo-v4-v50/backend/app/seed/entities.py` | 41 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py` | 86, 109, 134, 151, 175, 200, 203, 223, 278 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/benchmarking_report.py` | 56 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cohort_status.py` | 73, 100, 134 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py` | 65, 78, 413 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evidence_room.py` | 176, 225, 226, 229, 230, 232, 241 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py` | 570, 617, 629, 633 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/flywheel_comparison.py` | 13, 27 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py` | 671, 677, 851, 854 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py` | 64, 113, 177, 336 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/industry_profile.py` | 28 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/investigation_loop.py` | 146, 180, 181 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/investigation_patterns.py` | 8, 89, 127, 134 | CONFIRMED family / G018; individual branches may be test/demo/parser-only. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py` | 187 | CONFIRMED family / G017, G018; individual branches may be test/demo/parser-only. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/multihop_scenarios.py` | 227, 402 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/narrative.py` | 372, 401 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py` | 340, 343, 347, 354, 361 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reasoning.py` | 87, 94, 96, 97 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/referral_policy.py` | 14, 77, 128 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py` | 169, 171 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/route_policy.py` | 34, 49, 73, 123, 143, 170, 192, 209, 235 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_promotion.py` | 47, 63, 82, 109, 114, 118, 141, 144, 161, 163, 176, 186, 231, 234 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py` | 231 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/similar_cases.py` | 44 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/simulation.py` | 49, 100, 115, 278, 354 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/soc_domain_profile.py` | 4 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py` | 73, 189 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_intel.py` | 4 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/time_machine.py` | 58, 66 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/triage.py` | 206 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_registry.py` | 86 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/experiments/vld_action_boundary_c8_v1.py` | 4, 24, 222, 305, 308, 311, 312, 313, 320, 332, 336, 398, 406 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/ingest_shadow_decisions.py` | 64 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/bootstrap_soc_decisions.py` | 1, 22, 54, 63, 64, 65, 84, 143, 145, 167, 183, 185, 196, 204, 218, 226 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/centroid_diagnostics.py` | 49, 71, 98 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/diagnose_value_chain.py` | 1, 24, 129, 130, 131, 132, 231, 284, 286, 294, 305, 314 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/evaluate_multihop_stage1.py` | 194, 220, 251 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/exp_baseline_verify.py` | 45, 102, 127 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/exp_data_quality.py` | 1, 70, 71 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/exp_split_enrichment.py` | 31, 40 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/expand_demo_alerts.py` | 186 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/generate_score_keyed_alerts.py` | 21, 37, 41, 44, 45, 64, 75, 79 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/generate_seed.py` | 45 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/ingest_synthetic_decisions.py` | 64 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/measure_rho.py` | 66, 67, 70, 71, 129, 130, 131, 132, 180, 181, 234, 245, 248, 250, 292, 312, 321 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/seed_multihop_graph.py` | 1, 21 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/seed_verified_decisions.py` | 333, 397, 452 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/sprint/a3_factor_decomposition.py` | 17 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/sprint/b2_dimension_gating.py` | 23 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/sprint/c_validate_best.py` | 37, 119 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/sprint/sprint_lib.py` | 324 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/train_experiment_centroids.py` | 1, 20, 34, 43, 44, 45, 46, 68, 69, 73, 95, 106, 110, 114, 115, 116, 123, 131, 139, 166, 167, 168, 170, 172, 181, 186, 188, 199, 203 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/v_soc_31a_real_check.py` | 25 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/v_soc_37_investigation.py` | 25 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/v_soc_canonical_scan.py` | 26 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/v_soc_diagnostic.py` | 24 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/validate_stage1.py` | 4 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/value_chain_experiment_lib.py` | 25, 68, 73, 77, 78, 79 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/verify_rollback_readiness.py` | 4, 32, 94, 95, 96, 98, 110, 111, 112, 113, 116, 120 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/write_mu_zero_sidecar.py` | 17 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/seed_neo4j.py` | 27, 1417, 1619 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/support/setup/bootstrap_learning_loop.py` | 63, 80, 155 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/backend/support/setup/enrich_zero_day_v5.py` | 34 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/backend/support/setup/seed_shadow_decisions.py` | 65 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/backend/support/setup/seed_zero_day.py` | 42 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/check_drift.py` | 127 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/frontend/soc_pw_diagnostic.py` | 12 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/full_audit.py` | 104, 178, 180 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/graphify-out/soc_triage_source_review_20260609_023852/backend_app_routers_triage.py` | 1094, 1465, 2240 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/graphify-out/soc_triage_source_review_20260609_023852/scripts_diagnostics_perf_soc_perf_common.py` | 69 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/graphify-out/soc_triage_source_review_20260609_023852/scripts_diagnostics_perf_soc_perf_trace_summary.py` | 89 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/graphify-out/soc_triage_source_review_20260609_023852/scripts_diagnostics_perf_soc_perf_trace.py` | 95, 107 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/graphify-out/soc_triage_source_review_20260609_023852/scripts_diagnostics_run_soc_diag_f.py` | 308, 346 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/scratch/temp/diag_e4_runner.py` | 44, 51 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/scratch/temp/diag_f_runner.py` | 54, 61, 74, 78 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/scratch/temp/diag_f2_runner.py` | 43, 47 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/scratch/temp/runner_debug_20260610_154609/copilot-sdk/demo.py` | 128, 744 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/scratch/temp/runner_debug_20260610_154609/scripts/diagnostics/run_soc_diag_f.py` | 222, 321, 360, 392, 393 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/scratch/temp/runner_debug_20260610_154609/scripts/diagnostics/run_soc_route_validation.py` | 64, 561, 605, 733 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/scratch/temp/soc_c9b_diag_e3_runner.py` | 48, 54 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/scratch/temp/step0_connection_tax_spike.py` | 38, 49, 238 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/scripts/check_neo4j.py` | 29 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/collect_tab_content.py` | 49 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/diagnose_soc_diag_prefix.py` | 131 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/perf/soc_perf_common.py` | 69 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/perf/soc_perf_trace_summary.py` | 89 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/perf/soc_perf_trace.py` | 95, 107 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/run_soc_diag_f.py` | 222, 321, 360, 392, 393 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/run_soc_route_validation.py` | 66, 586, 630, 837 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/summarize_soc_diag_report.py` | 11 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/ingest_shadow_decisions.py` | 152 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/preseed_demo_scenarios.py` | 3, 4, 24, 37, 39, 65, 106, 107, 108, 109, 115, 123, 124, 132, 133, 134, 135, 136, 137, 140, 141, 144, 145, 146, 175, 176, 178, 179, 198, 202, 203, 204, 205, 206, 209, 212, 213, 220, 221, 223, 235, 236, 241, 297, 365, 421, 424, 427, 433, 441, 447, 451, 452, 459, 468, 547, 548, 550, 553 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/validate_contracts.py` | 29, 33, 63, 91 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/support/scripts/retroactive_grading.py` | 31 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/support/scripts/validate-setup.py` | 53 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/support/setup/neo4j_seed_data.py` | 2 | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `s2p-copilot/backend/app/connectors/fda_client.py` | 46 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/connectors/sec_client.py` | 48 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/connectors/supplier_intel_provider.py` | 36, 60, 71, 83, 125, 153, 171, 189, 202, 216, 219, 220, 237, 247, 258 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/domains/s2p/config.py` | 14, 16 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/domains/s2p/evolution/rule_templates.py` | 67, 72 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/domains/s2p/evolution/service.py` | 20, 21, 25, 31, 32, 35, 38, 40, 45, 52, 75, 93, 94, 112, 114, 120, 121, 122, 129, 157 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/domains/s2p/evolution/shadow_runner.py` | 13, 16, 17, 27 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/domains/s2p/factors.py` | 1, 74, 172, 173, 229, 257, 280, 298, 306, 322, 348, 349, 402, 440 | CONFIRMED family / G036; individual branches may be test/demo/parser-only. |
| `s2p-copilot/backend/app/evidence_provider.py` | 103, 116, 164, 275, 304, 336 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/framework/audit.py` | 4, 44 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/framework/checkpoint.py` | 135, 145 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/framework/composite_gate.py` | 37 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/framework/intervention_controls.py` | 472 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/framework/learning_state.py` | 70, 108 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/framework/narrative_base.py` | 85, 86, 95 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/framework/similar_cases_base.py` | 96, 168 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/graph_contract.py` | 125 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/migration/s2p_entity_migration.py` | 284 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `s2p-copilot/backend/app/oracle/pipeline_test.py` | 14, 15, 26, 27, 49, 50, 101 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/factor_proposer_router.py` | 80, 155 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/framework_router.py` | 222, 365 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/lead_time_router.py` | 140, 149, 161, 162, 163, 164, 172 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/s2p_audit_export.py` | 320 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/s2p_clustering.py` | 29, 30, 34, 35, 36, 37, 38, 39, 40, 48 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/s2p_control_tower.py` | 108 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/s2p_data_helpers.py` | 1, 14, 29, 30, 40, 42, 43, 45 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/s2p_demo_beats.py` | 394 | CONFIRMED family / G014; individual branches may be test/demo/parser-only. |
| `s2p-copilot/backend/app/routers/s2p_demo_control.py` | 22, 40, 44, 46, 92 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/s2p_early_warning.py` | 43, 47, 50, 51, 52, 53, 54, 55, 56, 57, 58, 66, 272 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/s2p_enrichment.py` | 96 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/s2p_evidence.py` | 481, 510 | CONFIRMED family / G014; individual branches may be test/demo/parser-only. |
| `s2p-copilot/backend/app/routers/s2p_explorer.py` | 276, 540 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/s2p_governance.py` | 317 | CONFIRMED family / G014; individual branches may be test/demo/parser-only. |
| `s2p-copilot/backend/app/routers/s2p_insight.py` | 52, 124, 210 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/s2p_payment.py` | 21, 108, 112, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 314, 329, 344 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/s2p_preview.py` | 1, 40, 42, 55, 135, 263, 266, 276, 374, 375, 398, 453, 454, 456, 460, 461, 463, 481, 558, 586 | CONFIRMED family / G036; individual branches may be test/demo/parser-only. |
| `s2p-copilot/backend/app/routers/s2p_pvg.py` | 39, 86, 125, 156, 167 | CONFIRMED family / G036; individual branches may be test/demo/parser-only. |
| `s2p-copilot/backend/app/routers/s2p_situation.py` | 276 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/s2p_suppliers.py` | 172, 209, 301, 359 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/s2p.py` | 1107, 1667, 2091, 2092, 2093, 2115, 2322, 2323, 2334, 3022 | CONFIRMED family / G015; individual branches may be test/demo/parser-only. |
| `s2p-copilot/backend/app/s2p_shadow.py` | 151 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/seed_graph.py` | 33, 45, 283, 305, 321, 334 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/services/cohort_status.py` | 92, 108, 109, 239 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/services/compounding_ledger.py` | 71 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/services/financial_impact.py` | 136 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/services/lead_time.py` | 1, 24, 203 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/services/proposal_service.py` | 178, 450, 451, 452, 456, 457 | CONFIRMED family / G045; individual branches may be test/demo/parser-only. |
| `s2p-copilot/backend/app/services/s2p_context_builder.py` | 22, 23, 71, 79, 84, 217, 223, 245, 250, 257, 297, 310, 315, 322, 325, 336, 341, 346, 353, 355, 364, 437, 443, 451, 462, 467, 476, 498, 503, 508, 626, 635 | CONFIRMED family / G014; individual branches may be test/demo/parser-only. |
| `s2p-copilot/backend/app/services/s2p_enrichment.py` | 129, 377, 378, 380, 381, 383, 387, 391, 422, 423, 613 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/services/s2p_situation_pattern.py` | 24, 82 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/services/situation_traversals.py` | 149, 153, 162, 165, 169, 172, 189, 192, 201, 203, 207, 210, 233, 237, 239, 243, 246, 271, 273, 282, 285, 289, 292, 307, 310, 314, 317, 388, 444, 577, 593, 600, 607, 613, 629, 633, 642 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/services/supplier_intelligence.py` | 3, 83, 94, 95, 97, 98, 187, 213, 275, 283, 290, 295, 352, 357, 358, 360, 361, 362, 396, 421, 427, 431, 434, 436, 462 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/services/supplier_profile_accumulator.py` | 40, 69, 70, 73, 74, 76, 77, 79, 93, 101, 102, 103, 121, 123, 124, 125, 126, 129, 130, 131, 137, 139, 142, 228, 230, 231, 395, 397, 399, 400, 403, 507, 515, 523 | CONFIRMED family / G035; individual branches may be test/demo/parser-only. |
| `s2p-copilot/backend/app/services/synthetic_invoices.py` | 1, 52, 150, 151, 153 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/vld_preseed.py` | 31, 139 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/scripts/evaluate_multihop_stage1.py` | 53 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `s2p-copilot/backend/scripts/validate_stage1.py` | 4 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `s2p-copilot/examples/procurement_approval/run_scenarios.py` | 90 | DEMO/REFERENCE — local simulation/artifact path; see G057–G059. |
| `s2p-copilot/generators/generate_5k_invoices.py` | 4, 39 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `s2p-copilot/generators/s2p_synthetic.py` | 1, 3, 431 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `s2p-copilot/scripts/conservation_s2p.py` | 50 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `s2p-copilot/scripts/preseed_demo_scenarios.py` | 1, 5, 20, 30, 33, 58, 77, 78, 79 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `s2p-copilot/scripts/preseed_s2p_demo.py` | 22, 33, 35, 37, 64, 306, 359, 362, 375, 376, 377, 379, 474 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `s2p-copilot/scripts/seed_s2p_graph.py` | 1, 24, 219, 378, 386, 411 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |

## Appendix C — Complete AST Graph/Store Exception Candidate Index

877 candidate handlers. RAISE means a textual raise exists in the handler, **not** proof every branch raises. RETURN/CONTINUE means no textual raise was found; determine whether the try actually reached a required graph operation. Calls are selected from the try body (nested calls included). Handler text is compacted; full source remains the authority. P1-linked families are confirmed at the specific sites discussed above; other sites remain candidates or explicit diagnostics.

| Except site | Calls / operation | Handler / disposition |
|---|---|---|
| `ci-platform/ci_platform/connectors/celonis.py:98` | json.loads, fixture_path.read_text | RAISE / inspect branches: except JSONDecodeError as exc:             raise ValueError(f"Invalid process fixture JSON in {fixture_path}: {exc}") from exc |
| `ci-platform/ci_platform/connectors/celonis.py:323` | self._fetch_via_rest | RETURN/CONTINUE candidate: except ConnectionError as exc:                 if self._can_use_fixture():                     self._source = "fixture"                     self._last_reason = str(exc)                     return {                         "status": "degraded",                         "source": "fixture",                         "reason": str(exc),         |
| `ci-platform/ci_platform/connectors/celonis.py:526` | self._fetch_via_rest | RAISE / inspect branches: except ConnectionError as exc:             if self._can_use_fixture():                 self._source = "fixture"                 self._last_reason = str(exc)                 return fallback()             raise |
| `ci-platform/ci_platform/connectors/sap.py:497` | json.loads, path.read_text | RAISE / inspect branches: except JSONDecodeError as exc:         raise ValueError(f"Invalid SAP fixture JSON in {path}: {exc}") from exc |
| `ci-platform/ci_platform/connectors/sentinel.py:119` | self._get_token, httpx.AsyncClient, client.get | RETURN/CONTINUE candidate: except Exception:             pass |
| `ci-platform/ci_platform/graph/age_client.py:212` | ConnectionPool | RETURN/CONTINUE candidate: except Exception as exc:                 logger.warning(                     "AGE connection pool initialization failed; falling back to warm connection reuse: %s",                     exc,                 )                 self._pool_available = False                 self._connection_mode = "warm_fallback"                 self._pool = No |
| `ci-platform/ci_platform/graph/age_client.py:278` | conn.execute, logger.info | RAISE / inspect branches: except Exception as e:                     if "already exists" not in str(e).lower():                         raise |
| `ci-platform/ci_platform/graph/age_client.py:498` | self._ensure_warm_connection, pool.connection, self._ensure_warm_connection, self._connect_fresh, threading.RLock, threading.RLock | RAISE / inspect branches: except Exception as e:                 if self.connection_mode == "warm_fallback":                     self._discard_warm_connection()                 if "Entity failed to be updated" in str(e) and attempt < MAX_RETRIES - 1:                     delay = 0.1 * (attempt + 1) + random.uniform(0, 0.05)                     time.sleep(delay)     |
| `ci-platform/ci_platform/graph/age_client.py:670` | self.run_query | RETURN/CONTINUE candidate: except Exception:             return 0 |
| `ci-platform/ci_platform/graph/age_client.py:697` | self.run_query | RETURN/CONTINUE candidate: except Exception:             return 0 |
| `ci-platform/ci_platform/graph/age_client.py:763` | self.run_query | RETURN/CONTINUE candidate: except (TypeError, ValueError, KeyError):             return 0 |
| `ci-platform/ci_platform/graph/age_client.py:778` | self.run_query | RETURN/CONTINUE candidate: except (TypeError, ValueError, KeyError):             return 0 |
| `ci-platform/ci_platform/graph/age_graph_store.py:408` | float | RAISE / inspect branches: except (TypeError, ValueError) as error:             raise TypeError("centroid_vector must contain only numeric values") from error |
| `ci-platform/ci_platform/graph/age_graph_store.py:447` | int | RAISE / inspect branches: except (TypeError, ValueError) as error:             raise TypeError("n_decisions_used must be an integer") from error |
| `ci-platform/ci_platform/graph/age_graph_store.py:721` | self._client.run_query | RAISE / inspect branches: except Exception as exc:             if type(exc).__name__ == "PoolClosed":                 log.error("AGE pool closed during query: %s", exc)                 return []             raise |
| `ci-platform/ci_platform/graph/age_graph_store.py:792` | self._link_decision_to_domain | RETURN/CONTINUE candidate: except Exception as exc:             log.warning(                 "Decision IN_DOMAIN edge creation failed: decision=%s domain=%s error=%s: %s",                 decision_id,                 domain,                 type(exc).__name__,                 exc,             ) |
| `ci-platform/ci_platform/graph/age_graph_store.py:810` | self._factor_vector_from_factors, self._create_factor_vector_node | RETURN/CONTINUE candidate: except Exception as exc:             log.warning(                 "FactorVector persistence failed: decision=%s domain=%s error=%s: %s",                 decision_id,                 domain,                 type(exc).__name__,                 exc,             ) |
| `ci-platform/ci_platform/graph/age_graph_store.py:3189` | np.asarray | RETURN/CONTINUE candidate: except (TypeError, ValueError):             # A checkpoint payload may be readable history metadata without             # being a numeric centroid tensor. It must not poison startup.             return None |
| `ci-platform/ci_platform/strategy/two_phase_strategy.py:31` | self._counts | RETURN/CONTINUE candidate: except Exception:             return "A" |
| `ci-platform/ci_platform/strategy/two_phase_strategy.py:47` | self._counts | RETURN/CONTINUE candidate: except Exception as exc:             return {                 "phase": "A",                 "verified": 0,                 "correct": 0,                 "q": 0.0,                 "min_verified": self.min_verified,                 "q_threshold": self.q_threshold,                 "error": str(exc),             } |
| `copilot-sdk/apps/dataops/backend/app/ae_router.py:47` | evolution_store_factory, store.get_evolution_events | RETURN/CONTINUE candidate: except Exception:         return [] |
| `copilot-sdk/apps/dataops/backend/app/connector_cache.py:65` | request, validate | RETURN/CONTINUE candidate: except Exception as exc:                     # Do not log URLs, credentials, or response bodies.                     logger.warning("Enterprise request failed (%s); using cached fallback", type(exc).__name__) |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:108` | _evolution_store_factory | RAISE / inspect branches: except HTTPException:         raise |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:110` | _evolution_store_factory | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="DataOps Decision graph unavailable") from exc |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:117` | _decision_store().get_all_decisions, _decision_store | RAISE / inspect branches: except HTTPException:         raise |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:119` | _decision_store().get_all_decisions, _decision_store | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="DataOps Decision graph query failed") from exc |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:796` | _graph_client, graph.get_pipelines, pipeline_payload.get | RETURN/CONTINUE candidate: except Exception:         graph_health = {"status": "unavailable", "source": "unavailable", "live": False,                         "connected": False, "cached": False, "pipeline_count": 0} |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:849` | connector.health | RETURN/CONTINUE candidate: except Exception as exc:         return {"status": "unavailable", "live": False, "source": "cache", "error": str(exc)} |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:1423` | _graph_client().get_alert, _graph_client | RAISE / inspect branches: except Exception:         if id == "DI-ABSTENTION-001":             alert = _fallback_alerts_by_id().get(id)             if alert:                 return {"source": "fixture", "alert": _with_alert_runtime_fields(alert)}         raise |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:1546` | _celonis_connector().health, _celonis_connector | RETURN/CONTINUE candidate: except Exception:         celonis_live = False |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:1551` | _sap_connector().get_purchase_orders, _sap_connector | RETURN/CONTINUE candidate: except Exception:         sap_po_count = 0 |
| `copilot-sdk/apps/dataops/backend/app/enterprise_router.py:125` | connector.health_check | RETURN/CONTINUE candidate: except Exception:         connector = fixture_factory()         result = await connector.health_check()         return (result if isinstance(result, dict) else {"status": "degraded"}), "fixture" |
| `copilot-sdk/apps/dataops/backend/app/enterprise_router.py:136` | connector.to_process_manifest | RETURN/CONTINUE candidate: except Exception:         connector = fixture_factory()         fixture = ProcessFixture.from_json(CELONIS_FIXTURE)         manifest = ProcessManifestBuilder(fixture).build()         source = "fixture" |
| `copilot-sdk/apps/dataops/backend/app/enterprise_router.py:173` | connector.fetch_purchase_orders, connector.fetch_invoices, connector.fetch_suppliers | RETURN/CONTINUE candidate: except Exception:         connector = fixture_factory()         purchase_orders = await connector.fetch_purchase_orders()         invoices = await connector.fetch_invoices()         suppliers = await connector.fetch_suppliers()         source = "fixture" |
| `copilot-sdk/apps/dataops/backend/app/graph_queries.py:88` |  | RETURN/CONTINUE candidate: except Exception:         return None |
| `copilot-sdk/apps/dataops/backend/app/graph_queries.py:131` | cls, getattr | RETURN/CONTINUE candidate: except Exception:                     self._age_client = None                     self._graph_connected = False |
| `copilot-sdk/apps/dataops/backend/app/graph_status.py:131` | _load_dataops_graph_config | RAISE / inspect branches: except GraphConfigError as exc:             message = str(exc)             if message.startswith("invalid backend"):                 message = "DATAOPS_ACTIVE_GRAPH_BACKEND must be 'sqlite' or 'age'"             raise DataOpsActiveGraphConfigError(message) from exc |
| `copilot-sdk/apps/dataops/backend/app/graph_status.py:322` | require_shared_graph | RAISE / inspect branches: except GraphConfigError as exc:         raise DataOpsActiveGraphConfigError(str(exc)) from exc |
| `copilot-sdk/apps/dataops/backend/app/main.py:191` | GraphConfig.load | RAISE / inspect branches: except GraphConfigError:         if profile != "test":             raise         backend = "sqlite" |
| `copilot-sdk/apps/dataops/backend/app/main.py:235` | SnowflakeMetaConnector | RETURN/CONTINUE candidate: except ImportError:             logger.info("CONNECTOR: SNOWFLAKE = DEMO (client library unavailable)") |
| `copilot-sdk/apps/dataops/backend/app/main.py:237` | SnowflakeMetaConnector | RETURN/CONTINUE candidate: except Exception as exc:             logger.info("CONNECTOR: SNOWFLAKE = DEMO (initialization unavailable: %s)", exc) |
| `copilot-sdk/apps/dataops/backend/app/main.py:257` | DBTConnector | RETURN/CONTINUE candidate: except ImportError:             logger.info("CONNECTOR: DBT = DEMO (client library unavailable)") |
| `copilot-sdk/apps/dataops/backend/app/main.py:259` | DBTConnector | RETURN/CONTINUE candidate: except Exception as exc:             logger.info("CONNECTOR: DBT = DEMO (initialization unavailable: %s)", exc) |
| `copilot-sdk/apps/dataops/backend/app/main.py:280` | AirflowConnector | RETURN/CONTINUE candidate: except ImportError:             logger.info("CONNECTOR: AIRFLOW = DEMO (client library unavailable)") |
| `copilot-sdk/apps/dataops/backend/app/main.py:282` | AirflowConnector | RETURN/CONTINUE candidate: except Exception as exc:             logger.info("CONNECTOR: AIRFLOW = DEMO (initialization unavailable: %s)", exc) |
| `copilot-sdk/apps/dataops/backend/app/main.py:322` | profiler.profile(_dataops_profile_entity_ids(source_name)).to_dict, profiler.profile, _dataops_profile_entity_ids, profile.setdefault, int, getattr | RETURN/CONTINUE candidate: except Exception:             continue |
| `copilot-sdk/apps/dataops/backend/app/main.py:468` | json.loads, SEED_FIXTURE_PATH.read_text | RETURN/CONTINUE candidate: except (OSError, json.JSONDecodeError) as exc:         print(f"[{DOMAIN}] auto-seed fixture unavailable: {exc}")         return {"decisions_seeded": 0, "outcomes_seeded": 0} |
| `copilot-sdk/apps/dataops/backend/app/main.py:521` | graph_store.write_outcome | RETURN/CONTINUE candidate: except Exception as exc:             print(f"[{DOMAIN}] auto-seed skipped entry {sequence}: {exc}") |
| `copilot-sdk/apps/dataops/backend/app/main.py:534` | graph_store.count_decisions | RAISE / inspect branches: except Exception as exc:         logger.warning("[%s] auto-seed count failed", DOMAIN, exc_info=True)         raise RuntimeError(f"[{DOMAIN}] auto-seed count failed") from exc |
| `copilot-sdk/apps/dataops/backend/app/main.py:558` | graph_store.get_evolution_events | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[{DOMAIN}] demo evolution seed check failed: {exc}")         return |
| `copilot-sdk/apps/dataops/backend/app/main.py:588` | graph_store.save_evolution_event | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[{DOMAIN}] demo evolution seed failed: {exc}") |
| `copilot-sdk/apps/dataops/backend/app/main.py:615` | store.get_evolution_events | RAISE / inspect branches: except Exception as exc:         raise RuntimeError(f"[{DOMAIN}] evolution graph read failed") from exc |
| `copilot-sdk/apps/dataops/backend/app/main.py:754` | evolver.record_outcome, decision.get | RETURN/CONTINUE candidate: except (KeyError, ValueError):             return |
| `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:55` | governance.verify_holdout | RAISE / inspect branches: except KeyError as exc:             raise HTTPException(status_code=404, detail=f"Unknown holdout: {exc.args[0]}") from exc |
| `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:62` | governance.provenance | RAISE / inspect branches: except KeyError as exc:             raise HTTPException(status_code=404, detail=f"Unknown decision: {exc.args[0]}") from exc |
| `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:73` | governance.advance_promotion | RAISE / inspect branches: except KeyError as exc:             raise HTTPException(status_code=404, detail=f"Unknown promotion: {exc.args[0]}") from exc |
| `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:85` | governance.freeze_twin, governance.frozen_twin_status | RAISE / inspect branches: except FileExistsError as exc:             raise HTTPException(status_code=409, detail=str(exc)) from exc |
| `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:87` | governance.freeze_twin, governance.frozen_twin_status | RAISE / inspect branches: except (RuntimeError, TypeError, ValueError) as exc:             raise HTTPException(status_code=503, detail=f"Frozen Twin unavailable: {exc}") from exc |
| `copilot-sdk/apps/dataops/backend/app/routers/perturbation_router.py:44` | cast, service.perturb, scorer_provider | RAISE / inspect branches: except PerturbationActiveError as exc:             raise HTTPException(status_code=409, detail=str(exc)) from exc |
| `copilot-sdk/apps/dataops/backend/app/routers/perturbation_router.py:46` | cast, service.perturb, scorer_provider | RAISE / inspect branches: except PerturbationError as exc:             raise HTTPException(status_code=400, detail=str(exc)) from exc |
| `copilot-sdk/apps/dataops/backend/app/routers/regime_router.py:47` | getattr, scorer_provider, getattr, callable, list, getter | RETURN/CONTINUE candidate: except (AttributeError, TypeError, ValueError):         decisions = [] |
| `copilot-sdk/apps/dataops/backend/app/routers/trust_perturbation_router.py:112` | _conservation_status | RAISE / inspect branches: except ValueError as exc:             raise HTTPException(status_code=400, detail=str(exc)) from exc |
| `copilot-sdk/apps/dataops/backend/app/routers/trust_perturbation_router.py:122` | _conservation_status | RAISE / inspect branches: except ValueError as exc:             raise HTTPException(status_code=400, detail=str(exc)) from exc |
| `copilot-sdk/apps/dataops/backend/app/routers/trust_perturbation_router.py:155` | compute_conservation_status_payload(DOMAIN, store).get, compute_conservation_status_payload | RETURN/CONTINUE candidate: except Exception:         return "UNAVAILABLE" |
| `copilot-sdk/apps/dataops/backend/app/routers/trust_router.py:66` | scorer.fingerprint, _factor_payload, fingerprint.get, compute_conservation_status_payload, conservation.get, fingerprint.get | RAISE / inspect branches: except HTTPException:             raise |
| `copilot-sdk/apps/dataops/backend/app/routers/trust_router.py:68` | scorer.fingerprint, _factor_payload, fingerprint.get, compute_conservation_status_payload, conservation.get, fingerprint.get | RAISE / inspect branches: except Exception as exc:             raise HTTPException(status_code=503, detail="Trust profile unavailable") from exc |
| `copilot-sdk/apps/dataops/backend/app/services/cohort_status.py:149` | list, method, list, method | RETURN/CONTINUE candidate: except Exception:                 continue |
| `copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:352` | graph_store.get_pipelines, payload.get | RETURN/CONTINUE candidate: except Exception:             pass |
| `copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:365` | graph_store.get_blast_radius | RETURN/CONTINUE candidate: except Exception:             pass |
| `copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:378` | graph_store.get_recurrence | RETURN/CONTINUE candidate: except Exception:             pass |
| `copilot-sdk/apps/purchasing/backend/app/connectors/qbo_connector.py:298` | float | RETURN/CONTINUE candidate: except (TypeError, ValueError):         return fallback |
| `copilot-sdk/apps/purchasing/backend/app/context_router.py:82` | _evolution_store_factory, store.get_evolution_events | RETURN/CONTINUE candidate: except Exception:         return [] |
| `copilot-sdk/apps/purchasing/backend/app/evidence_providers.py:84` | reader | RETURN/CONTINUE candidate: except Exception:             return {}, False |
| `copilot-sdk/apps/purchasing/backend/app/factors/weather_forecast.py:130` | float | RETURN/CONTINUE candidate: except (TypeError, ValueError):         return fallback |
| `copilot-sdk/apps/purchasing/backend/app/graph_status.py:135` | _load_purchasing_graph_config | RAISE / inspect branches: except GraphConfigError as exc:             message = str(exc)             if message.startswith("invalid backend"):                 message = "PURCHASING_ACTIVE_GRAPH_BACKEND must be 'sqlite' or 'age'"             raise PurchasingActiveGraphConfigError(message) from exc |
| `copilot-sdk/apps/purchasing/backend/app/graph_status.py:373` | require_shared_graph | RAISE / inspect branches: except GraphConfigError as exc:         raise PurchasingActiveGraphConfigError(str(exc)) from exc |
| `copilot-sdk/apps/purchasing/backend/app/main.py:226` | GraphConfig.load | RAISE / inspect branches: except GraphConfigError:             if profile != "test":                 raise             backend = "sqlite" |
| `copilot-sdk/apps/purchasing/backend/app/main.py:259` | FREDCommoditySource | RETURN/CONTINUE candidate: except ImportError:             logger.info("CONNECTOR: FRED = DEMO (client library unavailable)") |
| `copilot-sdk/apps/purchasing/backend/app/main.py:261` | FREDCommoditySource | RETURN/CONTINUE candidate: except Exception as exc:             logger.info("CONNECTOR: FRED = DEMO (initialization unavailable: %s)", exc) |
| `copilot-sdk/apps/purchasing/backend/app/main.py:313` | json.loads, SEED_FIXTURE_PATH.read_text | RETURN/CONTINUE candidate: except (OSError, json.JSONDecodeError) as exc:         print(f"[{DOMAIN}] auto-seed fixture unavailable: {exc}")         return {"decisions_seeded": 0, "outcomes_seeded": 0} |
| `copilot-sdk/apps/purchasing/backend/app/main.py:363` | graph_store.write_outcome | RETURN/CONTINUE candidate: except Exception as exc:             print(f"[{DOMAIN}] auto-seed skipped entry {sequence}: {exc}") |
| `copilot-sdk/apps/purchasing/backend/app/main.py:376` | graph_store.count_decisions | RAISE / inspect branches: except Exception as exc:         raise RuntimeError(f"[{DOMAIN}] auto-seed count failed") from exc |
| `copilot-sdk/apps/purchasing/backend/app/main.py:419` | store.get_evolution_events | RETURN/CONTINUE candidate: except Exception:         return [] |
| `copilot-sdk/apps/purchasing/backend/app/main.py:569` | evolver.record_outcome, decision.get | RETURN/CONTINUE candidate: except (KeyError, ValueError):             # A legacy decision may predate the registered variant inventory.             # Learning remains authoritative; stale evolution metadata is ignored.             return |
| `copilot-sdk/apps/purchasing/backend/app/main.py:672` | compute_conservation_status_payload | RETURN/CONTINUE candidate: except Exception:             return "UNKNOWN" |
| `copilot-sdk/apps/purchasing/backend/app/main.py:682` | compute_conservation_status_payload | RETURN/CONTINUE candidate: except Exception:             return None |
| `copilot-sdk/apps/purchasing/backend/app/routers/auto_order_router.py:87` | _learn_auto_order | RAISE / inspect branches: except (KeyError, AssertionError, ValueError) as exc:                 raise HTTPException(status_code=400, detail=str(exc)) from exc |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:182` | get_verified, isinstance | RETURN/CONTINUE candidate: except Exception:         return [] |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:193` | graph_store.get_centroid_checkpoints | RETURN/CONTINUE candidate: except Exception:         return [] |
| `copilot-sdk/apps/purchasing/backend/app/routers/iks.py:33` | IKSService, PurchasingPreset, service.summary | RAISE / inspect branches: except HTTPException:             raise |
| `copilot-sdk/apps/purchasing/backend/app/routers/iks.py:35` | IKSService, PurchasingPreset, service.summary | RAISE / inspect branches: except Exception as exc:             raise HTTPException(status_code=503, detail="IKS graph service unavailable") from exc |
| `copilot-sdk/apps/purchasing/backend/app/routers/iks.py:54` | graph_store_factory | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="IKS graph store is unavailable") from exc |
| `copilot-sdk/apps/purchasing/backend/app/routers/iks.py:64` | store.get_verified_decisions | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="IKS graph store is unavailable") from exc |
| `copilot-sdk/apps/purchasing/backend/app/routers/match.py:591` | writer | RETURN/CONTINUE candidate: except Exception as exc:         return {             "attempted": True,             "status": "failed",             "decision_id": None,             "error": str(exc),         } |
| `copilot-sdk/apps/purchasing/backend/app/routers/par_router.py:32` | qbo_bills_for_spend | RETURN/CONTINUE candidate: except Exception:             return [] |
| `copilot-sdk/apps/purchasing/backend/app/routers/pos_router.py:47` | ToastConnector | RAISE / inspect branches: except ImportError:             if not _demo_mode():                 raise RuntimeError("Toast provider is unavailable")             logger.info("CONNECTOR: TOAST = DEMO (client library unavailable)") |
| `copilot-sdk/apps/purchasing/backend/app/routers/pos_router.py:51` | ToastConnector | RAISE / inspect branches: except Exception as exc:             if not _demo_mode():                 raise RuntimeError("Toast provider failed to initialize") from exc             logger.info("CONNECTOR: TOAST = DEMO (initialization unavailable: %s)", exc) |
| `copilot-sdk/apps/purchasing/backend/app/routers/pos_router.py:74` | _is_mock_connector | RAISE / inspect branches: except Exception as exc:             raise HTTPException(status_code=503, detail="Toast POS provider unavailable") from exc |
| `copilot-sdk/apps/purchasing/backend/app/routers/pos_router.py:105` | _is_mock_connector | RAISE / inspect branches: except Exception as exc:             raise HTTPException(status_code=503, detail="Toast POS provider unavailable") from exc |
| `copilot-sdk/apps/purchasing/backend/app/routers/qbo_router.py:33` | QBOConnector._ensure_live_dependencies, QBOConnector, connector.validate_connection_config | RETURN/CONTINUE candidate: except ImportError:             logger.info("CONNECTOR: QBO = DEMO (client library unavailable)") |
| `copilot-sdk/apps/purchasing/backend/app/routers/qbo_router.py:35` | QBOConnector._ensure_live_dependencies, QBOConnector, connector.validate_connection_config | RETURN/CONTINUE candidate: except Exception as exc:             logger.info("CONNECTOR: QBO = DEMO (initialization unavailable: %s)", exc) |
| `copilot-sdk/apps/purchasing/backend/app/routers/qbo_router.py:82` | active.test_connection | RETURN/CONTINUE candidate: except Exception as exc:             status = {                 "connected": False,                 "company_name": None,                 "realm_id": None,                 "error": str(exc),             } |
| `copilot-sdk/apps/purchasing/backend/app/routers/queue.py:70` | MockQBOConnector | RETURN/CONTINUE candidate: except (FileNotFoundError, OSError):         return [] |
| `copilot-sdk/apps/purchasing/backend/app/routers/queue.py:338` | graph_store_factory, _call_count, _call_count | RETURN/CONTINUE candidate: except Exception:         return {"status": "UNKNOWN", "source": "graph_store_error"} |
| `copilot-sdk/apps/purchasing/backend/app/routers/regime_router.py:47` | getattr, scorer_provider, getattr, callable, list, getter | RETURN/CONTINUE candidate: except (AttributeError, TypeError, ValueError):         decisions = [] |
| `copilot-sdk/apps/purchasing/backend/app/routers/scorecard_router.py:71` | graph_store_factory, IKSService(store, domain=DOMAIN, shape=PurchasingPreset().shape, categories=CATEGORIES).summary | RETURN/CONTINUE candidate: except Exception:         return _empty_iks_summary() |
| `copilot-sdk/apps/purchasing/backend/app/routers/trust_router.py:163` | count_verified | RETURN/CONTINUE candidate: except Exception:             return 0 |
| `copilot-sdk/apps/purchasing/backend/app/routers/verify_router.py:121` | _learn_with_context, _learn_payload, _is_conservation_paused, _record_paused_outcome | RAISE / inspect branches: except KeyError as exc:             raise HTTPException(status_code=404, detail=f"Unknown decision: {decision_id}") from exc |
| `copilot-sdk/apps/purchasing/backend/app/routers/verify_router.py:123` | _learn_with_context, _learn_payload, _is_conservation_paused, _record_paused_outcome | RAISE / inspect branches: except AssertionError as exc:             raise HTTPException(status_code=400, detail=str(exc)) from exc |
| `copilot-sdk/apps/purchasing/backend/app/routers/verify_router.py:125` | _learn_with_context, _learn_payload, _is_conservation_paused, _record_paused_outcome | RAISE / inspect branches: except ValueError as exc:             if "already exists" in str(exc).lower():                 raise HTTPException(status_code=409, detail=f"Decision already verified: {decision_id}") from exc             raise HTTPException(status_code=400, detail=str(exc)) from exc |
| `copilot-sdk/apps/purchasing/backend/app/services/cohort_status.py:206` | list, method, list, method | RETURN/CONTINUE candidate: except Exception:                 continue |
| `copilot-sdk/apps/purchasing/backend/app/services/event_planner.py:117` | float | RETURN/CONTINUE candidate: except (TypeError, ValueError):         return fallback |
| `copilot-sdk/apps/purchasing/backend/app/services/menu_engineer.py:108` | float | RETURN/CONTINUE candidate: except (TypeError, ValueError):         return fallback |
| `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:70` | graph_store.get_verified_decisions | RETURN/CONTINUE candidate: except Exception:             has_outcomes = False |
| `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:189` | self._store().get_all_decisions, self._store | RAISE / inspect branches: except Exception as exc:             raise PurchasingGraphUnavailableError(                 "Purchasing graph read failed: get_all_decisions"             ) from exc |
| `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:197` | self._store().get_verified_decisions, self._store | RAISE / inspect branches: except Exception as exc:             raise PurchasingGraphUnavailableError(                 "Purchasing graph read failed: get_verified_decisions"             ) from exc |
| `copilot-sdk/apps/purchasing/backend/cli.py:346` | _scorer(ctx.obj['db_path']).learn | RAISE / inspect branches: except KeyError as exc:         raise click.ClickException(f"Decision ID not found: {decision_id}") from exc |
| `copilot-sdk/apps/trading/backend/app/cli_sdk.py:729` | get_broker | RAISE / inspect branches: except (ValueError, KeyError, ImportError) as exc:         raise CLIUsageError(             f"Unknown or unavailable broker: {broker}",             "Valid brokers: mock, alpaca, ibkr",         ) from exc |
| `copilot-sdk/apps/trading/backend/app/connectors/alpaca_connector.py:35` | client.get_account | RETURN/CONTINUE candidate: except Exception as exc:             return {"connected": False, "error": str(exc)} |
| `copilot-sdk/apps/trading/backend/app/connectors/ibkr_connector.py:43` | self._ib.isConnected, self._ib.connect, self._ib.isConnected | RETURN/CONTINUE candidate: except Exception:             return False |
| `copilot-sdk/apps/trading/backend/app/connectors/ibkr_connector.py:50` | self._ib.isConnected, self._ib.disconnect | RETURN/CONTINUE candidate: except Exception:             pass |
| `copilot-sdk/apps/trading/backend/app/connectors/ibkr_connector.py:60` | self._ib.managedAccounts | RETURN/CONTINUE candidate: except Exception as exc:             return {"connected": False, "error": str(exc)} |
| `copilot-sdk/apps/trading/backend/app/evidence_providers.py:83` | reader | RETURN/CONTINUE candidate: except Exception:             return {}, False |
| `copilot-sdk/apps/trading/backend/app/evidence.py:415` | float | RETURN/CONTINUE candidate: except (TypeError, ValueError):         return fallback |
| `copilot-sdk/apps/trading/backend/app/factors/registry.py:26` | tuple, TradingPreset | RETURN/CONTINUE candidate: except Exception:     ALL_FACTOR_NAMES = (         "signal_alignment",         "market_regime",         "position_sizing",         "timing_quality",         "risk_reward_actual",         "emotional_indicator",         "signal_confidence",         "options_delta_exposure",         "options_iv_percentile",         "options_gamma_risk",      |
| `copilot-sdk/apps/trading/backend/app/graph_status.py:133` | _load_trading_graph_config | RAISE / inspect branches: except GraphConfigError as exc:             message = str(exc)             if message.startswith("invalid backend"):                 message = (                     "TRADING_ACTIVE_GRAPH_BACKEND must be 'sqlite' or 'age'; "                     "'dual_write' is also supported"                 )             raise TradingActiveGraphConfigErr |
| `copilot-sdk/apps/trading/backend/app/graph_status.py:344` | require_shared_graph | RAISE / inspect branches: except GraphConfigError as exc:         raise TradingActiveGraphConfigError(str(exc)) from exc |
| `copilot-sdk/apps/trading/backend/app/main.py:183` | GraphConfig.load | RAISE / inspect branches: except GraphConfigError:         if profile != "test":             raise         # A generic AGE value without complete AGE config is intentionally not         # an active Trading-store selection in isolated tests.         backend = "sqlite" |
| `copilot-sdk/apps/trading/backend/app/main.py:275` | json.loads, SEED_FIXTURE_PATH.read_text | RETURN/CONTINUE candidate: except (OSError, json.JSONDecodeError) as exc:         print(f"[{DOMAIN}] auto-seed fixture unavailable: {exc}")         return {"decisions_seeded": 0, "outcomes_seeded": 0} |
| `copilot-sdk/apps/trading/backend/app/main.py:326` | graph_store.write_outcome | RETURN/CONTINUE candidate: except Exception as exc:             print(f"[{DOMAIN}] auto-seed skipped entry {sequence}: {exc}") |
| `copilot-sdk/apps/trading/backend/app/main.py:339` | graph_store.count_decisions | RAISE / inspect branches: except Exception as exc:         raise RuntimeError(f"[{DOMAIN}] auto-seed count failed") from exc |
| `copilot-sdk/apps/trading/backend/app/main.py:449` | trading_store_factory | RETURN/CONTINUE candidate: except Exception as exc:         app.state.trading_vld_showcase = {"status": "unavailable", "error": str(exc)}         print(f"[{DOMAIN}] VLD showcase preseed failed (non-blocking): {exc}") |
| `copilot-sdk/apps/trading/backend/app/routers/analytics.py:265` |  | RETURN/CONTINUE candidate: except (TypeError, IndexError):             continue |
| `copilot-sdk/apps/trading/backend/app/routers/analytics.py:276` | category_centroids.tolist | RETURN/CONTINUE candidate: except AttributeError:         rows = category_centroids |
| `copilot-sdk/apps/trading/backend/app/routers/data_import.py:130` | payload.get, _broker_import_connector | RETURN/CONTINUE candidate: except (TypeError, ValueError):             return JSONResponse(status_code=400, content={"error": "Invalid days parameter"}) |
| `copilot-sdk/apps/trading/backend/app/routers/data_import.py:132` | payload.get, _broker_import_connector | RAISE / inspect branches: except Exception as exc:             raise HTTPException(status_code=400, detail=f"{broker_name} import failed: {exc}") from exc |
| `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:228` | graph_store_factory, _state_counts, conservation_status, store.count_categories_with_n, _check_payload | RETURN/CONTINUE candidate: except Exception:         return {"status": "UNKNOWN", "conservation_status": "UNKNOWN", "domain": domain} |
| `copilot-sdk/apps/trading/backend/app/routers/execution_router.py:35` | graph_store_factory, store.get_all_decisions | RAISE / inspect branches: except Exception as exc:                 raise HTTPException(                     status_code=503,                     detail="Trading graph unavailable",                 ) from exc |
| `copilot-sdk/apps/trading/backend/app/routers/journal.py:230` | graph_store_factory, store.get_all_decisions | RAISE / inspect branches: except Exception as exc:             raise HTTPException(                 status_code=503,                 detail="Trading graph unavailable",             ) from exc |
| `copilot-sdk/apps/trading/backend/app/routers/promotion_router.py:104` | _conservation_status, _conservation_status | RAISE / inspect branches: except ValueError as exc:             raise HTTPException(status_code=409, detail=str(exc)) from exc |
| `copilot-sdk/apps/trading/backend/app/routers/promotion_router.py:139` | graph_store_factory, _state_counts, conservation_status, store.count_categories_with_n, _check_payload | RETURN/CONTINUE candidate: except Exception:         return {"status": "UNKNOWN", "conservation_status": "UNKNOWN", "domain": domain} |
| `copilot-sdk/apps/trading/backend/app/routers/promotion.py:105` | graph_store_factory, _state_counts, conservation_status, store.count_categories_with_n, _check_payload | RETURN/CONTINUE candidate: except Exception:         return {"status": "RED", "passed": False} |
| `copilot-sdk/apps/trading/backend/app/routers/regime_router.py:174` | graph_store_factory, _state_counts, conservation_status, store.count_categories_with_n, _check_payload | RETURN/CONTINUE candidate: except Exception:         return None |
| `copilot-sdk/apps/trading/backend/app/routers/regime.py:153` | graph_store_factory, _state_counts, conservation_status, store.count_categories_with_n, _check_payload | RETURN/CONTINUE candidate: except Exception:         return None |
| `copilot-sdk/apps/trading/backend/app/services/claim_gate.py:97` | graph_store.get_verified_decisions | RETURN/CONTINUE candidate: except Exception:             return |
| `copilot-sdk/apps/trading/backend/app/services/cohort_status.py:158` | list, method, list, method | RETURN/CONTINUE candidate: except Exception:                 continue |
| `copilot-sdk/apps/trading/backend/app/services/trader_profiles.py:85` | get_verified, isinstance | RETURN/CONTINUE candidate: except Exception:             return [] |
| `copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:115` | decision.get | RETURN/CONTINUE candidate: except (TypeError, ValueError):             adjusted = 0.0 |
| `copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:146` | setattr | RETURN/CONTINUE candidate: except Exception:             return |
| `copilot-sdk/apps/trading/backend/app/services/trust_analysis.py:173` | scorer.graph_store.get_decisions | RETURN/CONTINUE candidate: except Exception:             return None |
| `copilot-sdk/apps/trading/backend/cli.py:293` | IBKRConnector().import_trades, IBKRConnector | RETURN/CONTINUE candidate: except RuntimeError as exc:             print(str(exc), file=sys.stderr)             return 1 |
| `copilot-sdk/apps/trading/backend/generators/trading_synthetic.py:172` | TradingPreset, tuple, tuple, tuple | RETURN/CONTINUE candidate: except Exception:         return FALLBACK_CATEGORIES, FALLBACK_ACTIONS, FALLBACK_FACTORS |
| `copilot-sdk/copilot_sdk/backend/conservation_router.py:55` | compute_conservation_status_payload | RAISE / inspect branches: except Exception as exc:             raise HTTPException(status_code=503, detail=f"Graph store unavailable: {exc}") from exc |
| `copilot-sdk/copilot_sdk/backend/conservation_router.py:100` | payload.get | RETURN/CONTINUE candidate: except (ValueError, TypeError):                 projection = {"projected_divergence_week": None, "readiness_score": None,                               "evidence_label": "INVALID_PROJECTION_INPUTS"} |
| `copilot-sdk/copilot_sdk/backend/conservation_router.py:124` | check_conservation | RAISE / inspect branches: except ValueError as exc:             raise HTTPException(status_code=400, detail=str(exc)) from exc |
| `copilot-sdk/copilot_sdk/backend/conservation_utils.py:170` |  | RETURN/CONTINUE candidate: except AttributeError:             getter = None |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:109` | int, _call | RETURN/CONTINUE candidate: except Exception as exc:         if issues is not None:             issues.append(f"graph_artifacts {method}: {type(exc).__name__}: {exc}")         return None |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:230` | _call, isinstance, len, int | RETURN/CONTINUE candidate: except Exception:             continue |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:283` | _cypher_count | RETURN/CONTINUE candidate: except Exception as exc:         issues.append(f"graph_artifacts {label}: {type(exc).__name__}: {exc}")         return None |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:329` | _protocol_store | RETURN/CONTINUE candidate: except Exception as exc:             infra.error = str(exc)             issues.append(f"infrastructure: {exc}") |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:359` | int, _call | RETURN/CONTINUE candidate: except Exception as exc:                     scorer_diag.categories_with_decisions = None                     issues.append(f"scorer_state categories_with_decisions: {type(exc).__name__}: {exc}") |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:368` | _count_rows | RETURN/CONTINUE candidate: except Exception as exc:             scorer_diag.error = str(exc)             issues.append(f"scorer_state: {exc}") |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:378` | _call | RETURN/CONTINUE candidate: except Exception:                 pass |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:398` | str(state.get('status', state.get('conservation_status', 'unavailable'))).upper | RETURN/CONTINUE candidate: except Exception as exc:             conservation.error = str(exc)             issues.append(f"conservation: {exc}") |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:406` | bool, _call | RETURN/CONTINUE candidate: except Exception:             try:                 anchor = bool(_cypher_count(store, "Domain", domain))             except Exception:                 anchor = None                 issues.append("graph_artifacts Domain: domain anchor query unavailable") |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:409` | _cypher_count | RETURN/CONTINUE candidate: except Exception:                 anchor = None                 issues.append("graph_artifacts Domain: domain anchor query unavailable") |
| `copilot-sdk/copilot_sdk/backend/evolution_router.py:65` | graph_store_factory | RAISE / inspect branches: except Exception as exc:                         raise HTTPException(status_code=503, detail=f"Graph store unavailable: {exc}") from exc |
| `copilot-sdk/copilot_sdk/backend/evolution_router.py:156` | provider | RETURN/CONTINUE candidate: except Exception:                 pass |
| `copilot-sdk/copilot_sdk/backend/evolution_router.py:259` | store.get_global_stats | RETURN/CONTINUE candidate: except (KeyError, ValueError):             return None |
| `copilot-sdk/copilot_sdk/backend/investigation_router.py:127` | _read_centroid_tensor, _action_centroids_from_tensor, _read_sigma, _read_factor_names, _read_tau, _read_action_names, k_store.get_weights | RAISE / inspect branches: except ValueError as exc:             raise HTTPException(status_code=400, detail=str(exc)) from exc |
| `copilot-sdk/copilot_sdk/backend/investigation_router.py:129` | _read_centroid_tensor, _action_centroids_from_tensor, _read_sigma, _read_factor_names, _read_tau, _read_action_names, k_store.get_weights | RAISE / inspect branches: except Exception as exc:             raise HTTPException(status_code=503, detail=f"Investigation unavailable: {exc}") from exc |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:234` | variant_selector, _decision_variant_id | RAISE / inspect branches: except AssertionError as exc:                 raise HTTPException(status_code=400, detail=str(exc)) from exc |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:236` | variant_selector, _decision_variant_id | RAISE / inspect branches: except ValueError as exc:                 raise HTTPException(status_code=400, detail=str(exc)) from exc |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:238` | variant_selector, _decision_variant_id | RAISE / inspect branches: except Exception as exc:                 raise HTTPException(status_code=503, detail=f"Graph store unavailable: {exc}") from exc |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:287` | _get_decision, str(decision.get('status') or '').lower, decision.get, decision.get, _decision_category, _read_centroid_for_l5, learn_context.pop | RAISE / inspect branches: except KeyError as exc:                 raise HTTPException(status_code=404, detail=f"Unknown decision: {request.decision_id}") from exc |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:289` | _get_decision, str(decision.get('status') or '').lower, decision.get, decision.get, _decision_category, _read_centroid_for_l5, learn_context.pop | RAISE / inspect branches: except AssertionError as exc:                 raise HTTPException(status_code=400, detail=str(exc)) from exc |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:291` | _get_decision, str(decision.get('status') or '').lower, decision.get, decision.get, _decision_category, _read_centroid_for_l5, learn_context.pop | RAISE / inspect branches: except ValueError as exc:                 raise HTTPException(status_code=400, detail=str(exc)) from exc |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:293` | _get_decision, str(decision.get('status') or '').lower, decision.get, decision.get, _decision_category, _read_centroid_for_l5, learn_context.pop | RAISE / inspect branches: except Exception as exc:                 raise HTTPException(status_code=503, detail=f"Graph store unavailable: {exc}") from exc |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:409` | getattr, isinstance, dict, os.environ.get, os.environ.get, get_scorer, build_diagnostics | RETURN/CONTINUE candidate: except Exception as exc:             logger.exception("Diagnostics failed for %s", domain)             result = build_diagnostics(domain, None, None, extras={"error": str(exc)})             return result |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:600` | compute_conservation_metrics | RETURN/CONTINUE candidate: except Exception as exc:  # pragma: no cover - exercised through caller behavior         log.warning("L5 conservation state skipped for %s: %s", domain, exc)         return None |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:605` | store.get_conservation_state | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("L5 conservation state read failed for %s: %s", domain, exc)         return None |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:629` | store.update_conservation_state | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("L5 conservation state write failed for %s: %s", domain, exc) |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:716` | get_centroid | RETURN/CONTINUE candidate: except Exception as exc:         if logger is not None:             logger.debug("L5 centroid persistence skipped for %s: centroid unavailable: %s", domain, exc)         return False |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:724` | float | RETURN/CONTINUE candidate: except (TypeError, ValueError):         return False |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:740` | store.update_centroid | RETURN/CONTINUE candidate: except Exception as exc:         if logger is not None:             logger.warning("L5 centroid write failed for %s: %s", domain, exc)         return False |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:761` | get_centroid | RETURN/CONTINUE candidate: except Exception as exc:         if logger is not None:             logger.debug("L5 centroid pre-read skipped: %s", exc)         return None |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:769` | float | RETURN/CONTINUE candidate: except (TypeError, ValueError):         return None |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:825` | _dk_learning_store_for, persist_dk_after_reestimate | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("L5 DK persistence skipped for %s: %s", domain, exc) |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:276` | np.asarray | RAISE / inspect branches: except (TypeError, ValueError):             raise HTTPException(                 status_code=422,                 detail="Checkpoint does not contain a centroid tensor",             ) from None |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:421` | checkpoint.get | RAISE / inspect branches: except (TypeError, ValueError) as exc:             raise HTTPException(status_code=422, detail=str(exc)) from exc |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:498` | scorer.rollback_to_checkpoint | RAISE / inspect branches: except ValueError as exc:             raise HTTPException(status_code=404, detail=str(exc)) from exc |
| `copilot-sdk/copilot_sdk/backend/switching_cost_router.py:46` | store.count_decisions | RETURN/CONTINUE candidate: except (TypeError, ValueError):             return len(records) |
| `copilot-sdk/copilot_sdk/backend/switching_cost_router.py:50` | scorer.get_decision_count | RETURN/CONTINUE candidate: except (AttributeError, TypeError, ValueError):         pass |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:214` | store.get_all_decisions | RETURN/CONTINUE candidate: except Exception:             continue |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:380` | store.get_centroid_checkpoints | RETURN/CONTINUE candidate: except Exception:         return None |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:496` | store.get_latest_conservation_statuses, _normalize_conservation_state | RETURN/CONTINUE candidate: except Exception:             pass |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:503` | store.get_conservation_state, _normalize_conservation_state | RETURN/CONTINUE candidate: except Exception:             pass |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:512` | _normalize_conservation_state, _normalize_conservation_state | RETURN/CONTINUE candidate: except Exception:             pass |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:548` | store.get_latest_conservation_statuses, _normalize_conservation_state | RETURN/CONTINUE candidate: except Exception:             pass |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:555` | store.get_conservation_state, _normalize_conservation_state | RETURN/CONTINUE candidate: except Exception:             pass |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:572` | _normalize_conservation_state, _normalize_conservation_state | RETURN/CONTINUE candidate: except Exception:             _raise_unknown_conservation() |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:654` | update | RETURN/CONTINUE candidate: except Exception:         return False |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:705` | store.save_centroids | RETURN/CONTINUE candidate: except Exception:         return |
| `copilot-sdk/copilot_sdk/connectors/__init__.py:20` |  | RAISE / inspect branches: except KeyError as exc:         raise KeyError(f"Unknown connector: {name}") from exc |
| `copilot-sdk/copilot_sdk/connectors/snowflake_meta.py:50` |  | RAISE / inspect branches: except ImportError as exc:             raise RuntimeError("snowflake connector dependency is not installed") from exc |
| `copilot-sdk/copilot_sdk/demo/bundle.py:53` | sqlite_store.count_decisions | RETURN/CONTINUE candidate: except Exception:         current = 0 |
| `copilot-sdk/copilot_sdk/demo/bundle.py:147` | connection.commit, connection.execute, _rowcount, connection.execute, _rowcount, connection.execute, connection.execute | RETURN/CONTINUE candidate: except Exception:         connection.rollback()         LOGGER.exception("Demo bundle restore failed for domain %s", domain)         return False |
| `copilot-sdk/copilot_sdk/demo/bundle.py:164` | getattr | RETURN/CONTINUE candidate: except Exception:         return None |
| `copilot-sdk/copilot_sdk/demo/connector_freeze.py:103` | spec.loader.exec_module | RETURN/CONTINUE candidate: except Exception:             return None |
| `copilot-sdk/copilot_sdk/di/enrichment.py:311` | graph_store.write_entity_enrichment | RETURN/CONTINUE candidate: except NotImplementedError as exc:             return None, False, [str(exc) or "entity enrichment writes unsupported"] |
| `copilot-sdk/copilot_sdk/di/profiler.py:35` | self.connector.fetch | RETURN/CONTINUE candidate: except Exception as exc:                 message = f"fetch failed for {entity_id}: {exc.__class__.__name__}: {exc}"                 logger.warning(message)                 errors.append(message)                 continue |
| `copilot-sdk/copilot_sdk/di/profiler.py:47` | self.connector.validate | RETURN/CONTINUE candidate: except Exception as exc:                     message = f"validate failed for {entity_id}: {exc.__class__.__name__}: {exc}"                     logger.warning(message)                     errors.append(message)                     validation_results.append(False) |
| `copilot-sdk/copilot_sdk/di/query_providers.py:102` | reader, reader, reader, reader | RAISE / inspect branches: except ProviderUnavailableError:             raise |
| `copilot-sdk/copilot_sdk/di/query_providers.py:104` | reader, reader, reader, reader | RAISE / inspect branches: except Exception as exc:             raise ProviderUnavailableError("Governed GraphStore read failed") from exc |
| `copilot-sdk/copilot_sdk/di/query_providers.py:178` | self.graph_provider._decisions | RETURN/CONTINUE candidate: except ProviderUnavailableError:             return set() |
| `copilot-sdk/copilot_sdk/di/query_providers.py:302` | json.loads, path.read_text | RAISE / inspect branches: except (OSError, json.JSONDecodeError) as exc:         raise ProviderUnavailableError("SAP invoice fixture is unavailable") from exc |
| `copilot-sdk/copilot_sdk/di/query_service.py:239` | self.compute, self.route | RETURN/CONTINUE candidate: except ProviderUnavailableError:             LOGGER.warning("di3_query_provider_unavailable", extra={"query_id": query_id})             return self._response_for_plan(                 plan,                 query_id,                 "Insufficient verified data to answer this question.",                 "provider_unavailable",               |
| `copilot-sdk/copilot_sdk/di/search_service.py:127` | connector.fetch | RETURN/CONTINUE candidate: except Exception:             return None |
| `copilot-sdk/copilot_sdk/diagnostics/platform_dump.py:76` | run_census, census.get('sections', {}).get, census.get, int, census.get | RETURN/CONTINUE candidate: except Exception as exc:         result["error"] = f"{type(exc).__name__}: {exc}" |
| `copilot-sdk/copilot_sdk/diagnostics/platform_dump.py:184` | run_census | RETURN/CONTINUE candidate: except Exception as exc:         state["census"] = {"graph_name": graph_name, "sections": {}, "errors": [f"census_error: {exc}"]} |
| `copilot-sdk/copilot_sdk/discovery/patterns.py:197` | np.asarray | RETURN/CONTINUE candidate: except (TypeError, ValueError):         return None |
| `copilot-sdk/copilot_sdk/evolution/conservation_contract.py:108` | normalize_conservation_state, normalize_conservation_state | RETURN/CONTINUE candidate: except Exception as exc:             logger.warning("[EVOLUTION] Conservation read failed: %s", exc)             return normalize_conservation_state(                 {"status": "UNKNOWN", "reason": str(exc)},                 domain=self._domain,                 source="scorer",             ) |
| `copilot-sdk/copilot_sdk/evolution/conservation_contract.py:153` | self._snapshot_fn, normalize_conservation_state | RETURN/CONTINUE candidate: except Exception as exc:             logger.warning(                 "[EVOLUTION] domain conservation stale, returning UNKNOWN: %s", exc             )             return normalize_conservation_state(                 {"status": "UNKNOWN", "reason": "stale_or_error"},                 domain="unknown",                 source="learning_health |
| `copilot-sdk/copilot_sdk/evolution/ledger.py:73` | self._evolution_store.write_evolution_event, self._evolution_store.save_evolution_event | RETURN/CONTINUE candidate: except Exception as exc:  # pragma: no cover - warning path is tested with caplog             logger.warning("Failed to persist evolution event: %s", exc)             if self._outbox is not None:                 try:                     self._outbox.record_failure(event_id, "evolution", payload, str(exc))                 except Exception  |
| `copilot-sdk/copilot_sdk/framework/audit.py:235` | _LEDGER.append_outcome | RETURN/CONTINUE candidate: except ValueError:                 pass  # hash mismatch — skip silently |
| `copilot-sdk/copilot_sdk/framework/checkpoint.py:98` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[CHECKPOINT] list_checkpoints query failed: %s", exc)             return [] |
| `copilot-sdk/copilot_sdk/framework/checkpoint.py:135` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[CHECKPOINT] rollback query failed: %s", exc)             return {"error": f"AGE query failed: {exc}"} |
| `copilot-sdk/copilot_sdk/framework/checkpoint.py:158` | json.loads, np.isfinite(mu_restored).all | RETURN/CONTINUE candidate: except Exception as exc:             log.error("[CHECKPOINT] mu restore failed: %s", exc)             return {"error": f"mu restore failed: {exc}"} |
| `copilot-sdk/copilot_sdk/framework/checkpoint.py:171` | json.loads, np.isfinite(counts_restored).all | RETURN/CONTINUE candidate: except Exception as exc:                 log.debug("[CHECKPOINT] counts restore skipped: %s", exc) |
| `copilot-sdk/copilot_sdk/framework/checkpoint.py:184` | json.loads, np.isfinite(dk_restored).all | RETURN/CONTINUE candidate: except (TypeError, ValueError, json.JSONDecodeError) as exc:                 log.warning("[CHECKPOINT] DK weights restore skipped: %s", exc) |
| `copilot-sdk/copilot_sdk/framework/composite_gate.py:120` | DecisionHistoryService.get_category_stats | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[COMPOSITE] category_stats failed: %s", exc)             cat_stats = {"cat_count": 0, "rolling_accuracy": 0.5, "verified_count": 0} |
| `copilot-sdk/copilot_sdk/framework/decision_history.py:59` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[DECISION-HISTORY] query failed for category=%r: %s", category, exc)             return {"cat_count": 0, "rolling_accuracy": 0.5, "verified_count": 0} |
| `copilot-sdk/copilot_sdk/framework/intervention_controls.py:126` | self.db.run_query | RETURN/CONTINUE candidate: except Exception as exc:                 return {"error": f"AGE query failed: {exc}", "preview": True} |
| `copilot-sdk/copilot_sdk/framework/learning_state.py:99` | history.append | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[GAE] Skipping malformed history entry: %s", exc) |
| `copilot-sdk/copilot_sdk/framework/learning_state.py:162` | os.fdopen, json.dump, os.replace, log.debug | RAISE / inspect branches: except Exception:         try:             os.unlink(tmp)         except OSError:             pass         raise |
| `copilot-sdk/copilot_sdk/framework/provenance.py:326` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[PROVENANCE] query failed for decision=%r: %s", decision_id, exc)             return None |
| `copilot-sdk/copilot_sdk/framework/shadow_mode.py:106` | graph_service.run_query, graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[SHADOW] get_shadow_report query failed: %s", exc)             result = [] |
| `copilot-sdk/copilot_sdk/framework/similar_cases_base.py:99` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[SIMILAR-CASES] AGE query failed for category=%r: %s", category, exc)             return [] |
| `copilot-sdk/copilot_sdk/graph/factory.py:91` | importlib.import_module | RAISE / inspect branches: except ImportError as exc:         raise RuntimeError(             "AGE graph backend requires ci-platform with "             "ci_platform.graph.age_sdk_adapter importable"         ) from exc |
| `copilot-sdk/copilot_sdk/graph/factory.py:98` |  | RAISE / inspect branches: except AttributeError as exc:         raise RuntimeError(             "AGE graph backend requires ci_platform.graph.age_sdk_adapter."             "AGEGraphStoreAdapter"         ) from exc |
| `copilot-sdk/copilot_sdk/graph/memory_store.py:59` | float | RAISE / inspect branches: except (TypeError, ValueError) as error:         raise TypeError("centroid_vector must contain only numeric values") from error |
| `copilot-sdk/copilot_sdk/graph/memory_store.py:100` | int | RAISE / inspect branches: except (TypeError, ValueError) as error:         raise TypeError("n_decisions_used must be an integer") from error |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:78` | float | RAISE / inspect branches: except (TypeError, ValueError) as error:         raise TypeError("centroid_vector must contain only numeric values") from error |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:119` | int | RAISE / inspect branches: except (TypeError, ValueError) as error:         raise TypeError("n_decisions_used must be an integer") from error |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1180` | self.connection.commit | RAISE / inspect branches: except sqlite3.OperationalError as error:                 self.connection.rollback()                 if not _is_transient_sqlite_lock(error) or attempt == len(delays) - 1:                     raise |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1184` | self.connection.commit | RAISE / inspect branches: except Exception:                 self.connection.rollback()                 raise |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:2919` | np.asarray, _from_json | RETURN/CONTINUE candidate: except (TypeError, ValueError):             # A checkpoint payload may be readable history metadata without             # being a numeric centroid tensor. It must not poison startup.             return None |
| `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py:182` | json.loads, self.checkpoint_file.read_text | RAISE / inspect branches: except json.JSONDecodeError as exc:             raise ValueError(f"Reconciliation checkpoint is corrupted: {self.checkpoint_file}") from exc |
| `copilot-sdk/copilot_sdk/migrate/scratch_graph.py:85` | conn.execute | RETURN/CONTINUE candidate: except Exception:             pass |
| `copilot-sdk/copilot_sdk/migrate/scratch_graph.py:100` | conn.execute | RETURN/CONTINUE candidate: except Exception:             pass |
| `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:113` | self.shadow.score, _get_field, _get_field, str, str, self.compare_score_results | RETURN/CONTINUE candidate: except Exception as exc:             comparison = ComparisonResult(                 matched=False,                 decision_id=_get_field(primary_result, "decision_id"),                 field_results={                     "shadow_exception": {                         "matched": False,                         "primary": None,               |
| `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:137` | self._shadow_learn_args, self._shadow_learn_kwargs, self.shadow.learn | RETURN/CONTINUE candidate: except Exception as exc:             comparison = ComparisonResult(                 matched=False,                 decision_id=str(args[0]) if args else kwargs.get("decision_id"),                 field_results={                     "shadow_exception": {                         "matched": False,                         "primary": None,     |
| `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:365` | set, list, get_verified, row.get, categories.add, categories.add, row.get | RETURN/CONTINUE candidate: except Exception as exc:             logger.warning(                 "shadow scorer category coverage fallback to zero; "                 "output is non-authoritative: %s",                 exc,             )             return 0.0 |
| `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:376` | count_categories_with_n | RETURN/CONTINUE candidate: except Exception as exc:             logger.warning(                 "shadow scorer category coverage fallback to zero after "                 "category-count failure; output is non-authoritative: %s",                 exc,             )             return 0.0 |
| `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:667` | conn.execute(_age_sql(graph_name, match, 'd agtype')).fetchone, outcome_properties.update, outcome_properties.items | RAISE / inspect branches: except Exception:             errors += 1             if commit:                 conn.rollback()             else:                 raise |
| `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:980` | _read_checkpoint | RETURN/CONTINUE candidate: except ValueError as exc:         return {             "status": "FAIL",             "domain": domain,             "source": source_db,             "graph_name": graph_name,             "checkpoint_file": str(checkpoint),             "fail_reason": str(exc),         } |
| `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1144` | _write_batch | RETURN/CONTINUE candidate: except Exception as exc:                     conn.rollback()                     result["status"] = "FAIL"                     result["fail_reason"] = f"batch {batch_number} failed: {type(exc).__name__}: {exc}"                     result["write"] = totals                     logger.error("SQLite to AGE migration failed: %s", result["fail_ |
| `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1271` | copy_to_live, int, live_copy.get, logger.warning | RETURN/CONTINUE candidate: except Exception as exc:                 result["status"] = "FAIL"                 result["fail_reason"] = f"live copy failed: {type(exc).__name__}: {exc}"                 result["scratch_retained"] = scratch_graph                 result["scratch_retained_reason"] = "live copy failed"                 logger.warning(                     "S |
| `copilot-sdk/copilot_sdk/outbox/worker.py:66` | self._store.mark_processed | RETURN/CONTINUE candidate: except Exception as exc:                 logger.error("Handler failed for event %d: %s", event.event_id, exc)                 self._store.mark_dead_letter(event.event_id, str(exc)) |
| `copilot-sdk/copilot_sdk/outcome/router.py:21` | VerifiedOutcome.from_dict, processor.process(outcome).to_dict | RAISE / inspect branches: except (TypeError, ValueError) as error:             raise HTTPException(status_code=400, detail=str(error)) from error |
| `copilot-sdk/copilot_sdk/pilot/checks.py:102` | _verified_count | RETURN/CONTINUE candidate: except Exception as exc:             return _result(self.name, False, "Verified decision count unavailable", {"error": str(exc), "minimum": self.minimum}) |
| `copilot-sdk/copilot_sdk/pilot/transfer_router.py:48` | transfer.record_decision | RAISE / inspect branches: except KeyError as exc:             raise HTTPException(status_code=404, detail=str(exc)) from exc |
| `copilot-sdk/copilot_sdk/pilot/transfer_router.py:50` | transfer.record_decision | RAISE / inspect branches: except ValueError as exc:             raise HTTPException(status_code=422, detail=str(exc)) from exc |
| `copilot-sdk/copilot_sdk/promotion/core.py:366` | self.conservation_provider | RETURN/CONTINUE candidate: except Exception:                 return "UNKNOWN" |
| `copilot-sdk/copilot_sdk/promotion/core.py:396` | max, int, values.get | RETURN/CONTINUE candidate: except (TypeError, ValueError):         return max(int(fallback), 0) |
| `copilot-sdk/copilot_sdk/promotion/core.py:403` | float, values.get | RETURN/CONTINUE candidate: except (TypeError, ValueError):         return float(fallback) |
| `copilot-sdk/copilot_sdk/reporting/weekly.py:202` | self._cost_extractor, float, impact.get, float, impact.get | RETURN/CONTINUE candidate: except Exception:                 continue |
| `copilot-sdk/copilot_sdk/reporting/weekly.py:267` | self._scorer.get_phase, self._scorer.get_alpha, self._store.get_conservation_state | RETURN/CONTINUE candidate: except Exception:             return "UNKNOWN", 0.0, 0.0 |
| `copilot-sdk/copilot_sdk/scoring/dk_persistence.py:270` | welford_tracker.to_welford_state, getattr, update_dk_weights, deepcopy, time.time | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("L5 DK persistence failed for %s: %s", domain, exc)         return False |
| `copilot-sdk/copilot_sdk/scoring/gate_enforced_scorer.py:129` |  | RETURN/CONTINUE candidate: except AttributeError:             getter = None |
| `copilot-sdk/copilot_sdk/scoring/investigation.py:253` | evidence_provider.read_evidence | RETURN/CONTINUE candidate: except Exception as exc:                 evidence = None                 status = "error"                 error_source = f"error:{exc.__class__.__name__}" |
| `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:275` | json.loads | RETURN/CONTINUE candidate: except Exception as exc:                 failed += 1                 schema_stale = int(row["schema_version"]) < CURRENT_PAYLOAD_SCHEMA                 incompatible = isinstance(exc, TypeError) or schema_stale                 new_status = (                     "abandoned"                     if incompatible or int(row["retry_count"]) + 1  |
| `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:403` | self.pending_count | RETURN/CONTINUE candidate: except Exception:                 _LOG.warning("periodic drain failed", exc_info=True) |
| `copilot-sdk/copilot_sdk/scoring/presets/dataops.py:108` | json.loads, path.read_text | RETURN/CONTINUE candidate: except Exception:         return cast(np.ndarray, np.full(expected_shape, 0.5, dtype=np.float64)) |
| `copilot-sdk/copilot_sdk/scoring/presets/purchasing.py:118` | json.loads, path.read_text, _migrate_legacy_centroids | RETURN/CONTINUE candidate: except Exception:         return cast(np.ndarray, np.full(expected_shape, 0.5, dtype=np.float64)) |
| `copilot-sdk/copilot_sdk/scoring/presets/trading.py:134` | json.loads, path.read_text, _migrate_legacy_centroids | RETURN/CONTINUE candidate: except Exception:         return cast(np.ndarray, np.full(expected_shape, 0.5, dtype=np.float64)) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:183` | PersistenceOutbox | RETURN/CONTINUE candidate: except Exception as exc:             self._outbox = None             logger.warning("Persistence outbox unavailable for %s: %s", self._domain, exc) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:363` | get_rl_components | RETURN/CONTINUE candidate: except Exception as exc:                 logger.warning("RL setup failed for preset %s; continuing without RL: %s", domain, exc) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:440` | governed_store.write_governed_decision, decision_payload.items | RETURN/CONTINUE candidate: except Exception as exc:                 self._record_persistence_failure(decision_id, "decision", decision_payload, exc) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:460` | self._graph_store.write_decision, decision_payload.items | RETURN/CONTINUE candidate: except Exception as exc:                 self._record_persistence_failure(decision_id, "decision", decision_payload, exc) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:751` | compute_conservation_status_payload | RAISE / inspect branches: except BaseException as exc:             if not _is_conservation_read_error(exc):                 raise             self._conservation_read_failures += 1             self._conservation_mode = "unavailable"             logger.error(                 "Conservation health read failed closed for %s: %s: %s",                 self._domain,       |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:937` | event_writer, checkpoint.get | RAISE / inspect branches: except Exception:             self._scorer.centroids = old_centroids             if old_dk is None:                 if hasattr(self._scorer, "_dk_weights"):                     self._scorer._dk_weights = None             else:                 self._scorer._dk_weights = old_dk             self._scorer.tau = old_tau             self._calibr |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1021` | self._persist_conservation_snapshot | RETURN/CONTINUE candidate: except Exception as exc:                     # The snapshot helper isolates normal persistence errors;                     # retain a final guard so a pause response is never blocked.                     logger.warning(                         "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",                         se |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1052` | self._save_centroids_checkpoint, _decision_field, _decision_field, _decision_field | RETURN/CONTINUE candidate: except Exception as exc:                     logger.warning(                         "Paused conservation checkpoint failed: domain=%s decision=%s error=%s",                         self._domain,                         decision_id,                         exc,                     ) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1067` | self.fingerprint, self._persist_fingerprint | RETURN/CONTINUE candidate: except Exception as exc:                         logger.warning(                             "Paused conservation fingerprint failed: domain=%s decision=%s error=%s",                             self._domain,                             decision_id,                             exc,                         ) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1257` | self._outbox.record_failure, str | RETURN/CONTINUE candidate: except Exception as outbox_exc:             logger.warning(                 "Persistence outbox record failed: domain=%s decision=%s artifact=%s error=%s: %s",                 self._domain,                 decision_id,                 artifact_type,                 type(outbox_exc).__name__,                 outbox_exc,             ) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1332` | compute_conservation_metrics, self._graph_store.write_conservation_status | RETURN/CONTINUE candidate: except Exception as exc:             logger.warning(                 "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",                 self._domain,                 decision_id,                 "conservation",                 type(exc).__name__,                 exc,             )             self._record_persistence_fa |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1386` | self.fingerprint, self._persist_fingerprint | RETURN/CONTINUE candidate: except Exception as exc:                 logger.warning(                     "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",                     self._domain, decision_id, "fingerprint", type(exc).__name__, exc,                 )                 self._record_persistence_failure(decision_id, "fingerprint", {}, exc) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1424` | load_decision, _is_correct_decision, _decision_field, _decision_field, _decision_field, _decision_field, _decision_field | RETURN/CONTINUE candidate: except Exception as exc:                 logger.warning(                     "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",                     self._domain, decision_id, "evidence_receipt", type(exc).__name__, exc,                 )                 self._record_persistence_failure(decision_id, "evidence_receipt", { |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1458` | load_decision, _decision_field, _decision_field, _decision_field, _decision_field, self._save_centroids_checkpoint, self._extract_decision_timestamp | RAISE / inspect branches: except Exception as exc:                 if raise_on_error:                     raise                 logger.warning(                     "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",                     self._domain, decision_id, "centroid_checkpoint", type(exc).__name__, exc,                 )                 sel |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1515` | self._capture_conservation_state, self._persist_conservation_snapshot | RETURN/CONTINUE candidate: except Exception as exc:             errors.append(f"conservation: {type(exc).__name__}: {exc}")             logger.warning("State capture conservation failed for %s: %s", self._domain, exc) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1525` | self.fingerprint, self._persist_fingerprint | RETURN/CONTINUE candidate: except Exception as exc:             errors.append(f"fingerprint: {type(exc).__name__}: {exc}")             logger.warning("State capture fingerprint failed for %s: %s", self._domain, exc) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1563` | self._graph_store.get_centroid_checkpoints, self._graph_store.count_verified, hashlib.sha256(centroids.tobytes()).hexdigest, hashlib.sha256(f'{self._domain} {capture_reason} {centroid_digest} {verified}'.encode('utf-8')).hexdigest | RETURN/CONTINUE candidate: except Exception as exc:             errors.append(f"checkpoint: {type(exc).__name__}: {exc}")             logger.warning("State capture checkpoint failed for %s: %s", self._domain, exc) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1650` | self._graph_store.append_evidence_receipt | RETURN/CONTINUE candidate: except Exception as exc:             logger.warning(                 "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",                 self._domain, decision_id, "evidence_receipt", type(exc).__name__, exc,             )             if self._outbox is not None:                 try:                     self._outbox.reco |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1663` | self._outbox.record_failure, str | RETURN/CONTINUE candidate: except Exception as outbox_exc:                     logger.warning("Persistence outbox record failed: %s", outbox_exc) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1725` | self._graph_store.write_fingerprint | RETURN/CONTINUE candidate: except Exception as exc:             logger.warning(                 "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",                 self._domain,                 decision_id or "unknown",                 "fingerprint",                 type(exc).__name__,                 exc,             )             if self._outbox |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1742` | self._outbox.record_failure, str | RETURN/CONTINUE candidate: except Exception as outbox_exc:                     logger.warning("Persistence outbox record failed: %s", outbox_exc) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1895` | self._graph_store.count_verified, self._graph_store.count_correct | RETURN/CONTINUE candidate: except Exception:             return "A" |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1906` | self._graph_store.count_verified, self._graph_store.count_correct | RETURN/CONTINUE candidate: except Exception:             return 0.0 |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1983` | self._graph_store.get_latest_conservation_statuses | RETURN/CONTINUE candidate: except Exception as exc:                     logger.warning(                         "Warm-start conservation lookup failed: domain=%s error=%s: %s",                         self._domain,                         type(exc).__name__,                         exc,                     ) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2034` | self._graph_store.write_transfer_pattern | RETURN/CONTINUE candidate: except Exception as exc:                         logger.warning(                             "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",                             self._domain,                             "warm_start",                             "transfer_pattern",                             type(exc).__name_ |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2060` | self._graph_store.save_centroids | RETURN/CONTINUE candidate: except Exception as exc:                     logger.warning("Failed to save warm-start centroid checkpoint: %s", exc) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2112` | self._verified_decisions | RETURN/CONTINUE candidate: except Exception:             verified = self._graph_store.count_verified(self._domain) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2119` | _is_correct_decision | RETURN/CONTINUE candidate: except Exception:             correct = self._graph_store.count_correct(self._domain) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2204` | self._read_conservation_inputs_with_retry | RAISE / inspect branches: except BaseException as exc:             if _is_conservation_read_error(exc):                 self._conservation_read_failures += 1                 self._conservation_mode = "unavailable"                 logger.error(                     "Conservation read failed closed for %s after retry: %s: %s",                     self._domain,        |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2305` | self._read_conservation_inputs_once | RAISE / inspect branches: except BaseException as exc:             if not _is_conservation_read_error(exc):                 raise             logger.warning(                 "Conservation read failed for %s; retrying once: %s: %s",                 self._domain,                 type(exc).__name__,                 exc,             )             time.sleep(CONSERVATI |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2371` | self._fingerprint_weight_map | RETURN/CONTINUE candidate: except (TypeError, ValueError) as exc:             logger.debug("Could not compute judgment conflict for %s: %s", decision_id, exc)             self._last_conflict = None |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2456` | self._graph_store.save_centroids | RETURN/CONTINUE candidate: except Exception as exc:                 logger.warning(                     "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",                     self._domain, decision_id, "centroid_checkpoint", type(exc).__name__, exc,                 ) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2489` | self.get_verified_count, checkpoint_writer | RAISE / inspect branches: except Exception as exc:             if raise_on_error:                 raise             logger.warning(                 "Persistence failed: domain=%s decision=%s artifact=%s error=%s: %s",                 self._domain, decision_id, "centroid_checkpoint", type(exc).__name__, exc,             )             if self._outbox is not None:    |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2504` | self._outbox.record_failure, str | RETURN/CONTINUE candidate: except Exception as outbox_exc:                     logger.warning("Persistence outbox record failed: %s", outbox_exc) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2525` | self._graph_store.count_decisions, self._graph_store.archive_old_decisions | RETURN/CONTINUE candidate: except Exception as exc:             logger.warning("Decision archive failed for %s: %s", self._domain, exc) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2603` | self._graph_store.get_verified_decisions, self._evolution_conservation_state, decisions[-1].get, decisions[-1].get | RETURN/CONTINUE candidate: except Exception as exc:             logger.warning("Evolution run failed: %s", exc) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2624` | _conservation_stats | RETURN/CONTINUE candidate: except Exception:             return None |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2756` | _decision_field, _decision_field, _decision_field | RETURN/CONTINUE candidate: except (TypeError, ValueError):             continue |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2961` | __import__ | RETURN/CONTINUE candidate: except Exception:         return False |
| `copilot-sdk/copilot_sdk/scoring/startup_restore.py:79` | capture, active_log.info, capture_result.get, capture_result.get, capture_result.get | RETURN/CONTINUE candidate: except Exception as exc:         active_log.warning("J6 startup state capture failed: %s", exc) |
| `copilot-sdk/copilot_sdk/scoring/startup_restore.py:155` | get_centroids | RETURN/CONTINUE candidate: except Exception as exc:         active_log.warning("L5 centroid startup read failed for %s: %s", domain, exc)         status["centroid_source"] = "error"         return |
| `copilot-sdk/copilot_sdk/scoring/startup_restore.py:169` | load_centroids, _pad_legacy_s2p_centroids | RETURN/CONTINUE candidate: except Exception as exc:         active_log.warning("L5 centroid startup restore failed for %s: %s", domain, exc)         status["centroid_source"] = "error" |
| `copilot-sdk/copilot_sdk/scoring/startup_restore.py:249` | get_conservation_state | RETURN/CONTINUE candidate: except Exception as exc:         active_log.warning("L5 conservation startup read failed for %s: %s", domain, exc)         status["conservation_source"] = "error"         return |
| `copilot-sdk/copilot_sdk/situation/templates.py:83` | template.format_map, _SafeFormatMap | RETURN/CONTINUE candidate: except Exception:             coerced = {                 name: self._coerce_value(render_variables.get(name), name in numeric_fields)                 for name in used_variables             }             missing.update(name for name in used_variables if name not in render_variables)             try:                 rendered = template.for |
| `copilot-sdk/copilot_sdk/situation/templates.py:91` | template.format_map, _SafeFormatMap | RETURN/CONTINUE candidate: except Exception:                 rendered = self._fallback_render(template, used_variables, missing) |
| `copilot-sdk/copilot_sdk/state/cached_static.py:67` | _store_value | RAISE / inspect branches: except BaseException as exc:                     _finish_flight(flight_key, flight, error=exc)                     raise |
| `copilot-sdk/copilot_sdk/state/cached_static.py:90` | _store_value | RAISE / inspect branches: except BaseException as exc:                 _finish_flight(flight_key, flight, error=exc)                 raise |
| `copilot-sdk/copilot_sdk/testing/fixtures.py:37` | GraphConfig.load, psycopg.connect | RETURN/CONTINUE candidate: except Exception as exc:  # pragma: no cover - depends on external AGE         log.debug("AGE unavailable for tests: %s", exc)         return False |
| `copilot-sdk/copilot_sdk/twin/router.py:59` | twin.freeze, dict, float, str, body.get, body.get | RAISE / inspect branches: except FileExistsError as error:             raise HTTPException(status_code=409, detail=str(error)) from error |
| `copilot-sdk/copilot_sdk/twin/router.py:61` | twin.freeze, dict, float, str, body.get, body.get | RAISE / inspect branches: except (KeyError, TypeError, ValueError) as error:             raise HTTPException(status_code=400, detail=str(error)) from error |
| `copilot-sdk/demo.py:314` | s.connect | RETURN/CONTINUE candidate: except Exception:         return False |
| `copilot-sdk/demo.py:335` | psycopg.connect | RETURN/CONTINUE candidate: except Exception:         return False |
| `copilot-sdk/demo.py:351` | GraphConfig.load | RETURN/CONTINUE candidate: except Exception:         graph = _get_soc_graph_config().graph |
| `copilot-sdk/demo.py:810` | _shared_graph_proof, _get_soc_graph_config | RETURN/CONTINUE candidate: except Exception:             print("  Graph proof             UNAVAILABLE (AGE not reachable)") |
| `copilot-sdk/demo.py:885` | json.loads, urlopen(_http_url(port, path), timeout=5).read, str(response.get('status') or response.get('conservation_status') or 'unknown').upper | RETURN/CONTINUE candidate: except Exception:                 continue |
| `copilot-sdk/demo.py:981` | cmd_kill_all, cmd_start, preseed_environment, os.environ.copy, env.update, _http_url, int | RETURN/CONTINUE candidate: except Exception as exc:         failure = str(exc) |
| `copilot-sdk/demo.py:1072` | ensure_soc_diag_graph, Path(age_graph_store.__file__).resolve | RETURN/CONTINUE candidate: except Exception as exc:             print(f"  ✗ SOC diagnostic graph setup failed: {exc}")             return |
| `copilot-sdk/demo.py:1359` | subprocess.run, str, str, print | RETURN/CONTINUE candidate: except Exception as e:             print(f"  WARN: Graph seed failed: {e}")             del os.environ["GRAPH_DSN"] |
| `copilot-sdk/demo.py:1462` | payload.get, payload.get, payload.get, payload.get | RETURN/CONTINUE candidate: except Exception as exc:             print(f"{name}: diagnostics unavailable: {exc}")             blocking.append(f"{name}/endpoint") |
| `copilot-sdk/demo.py:1530` | ConnectorFreeze(SCRIPT_DIR / '.record_freeze').freeze, ConnectorFreeze | RETURN/CONTINUE candidate: except Exception as exc:         print(f"  WARN: connector freeze failed: {exc}") |
| `copilot-sdk/demo.py:1551` | ConnectorFreeze(SCRIPT_DIR / '.record_freeze').unfreeze, ConnectorFreeze | RETURN/CONTINUE candidate: except Exception as exc:         print(f"  WARN: record reset verification failed: {exc}") |
| `copilot-sdk/demo.py:1618` | (analysis.get('decision') or {}).get, (analysis.get('decision') or {}).get, str(health.get('status') or health.get('conservation_status') or 'unknown').upper | RAISE / inspect branches: except Exception as exc:         print(f"  WARN: SOC pre-seed failed: {exc}")         if fail_hard:             raise |
| `copilot-sdk/examples/build_your_own/engine.py:112` | scorer.get_conservation_state | RETURN/CONTINUE candidate: except Exception as exc:         return {"status": "RED", "reason": f"conservation unavailable: {exc}"} |
| `copilot-sdk/examples/jm_reference/run.py:98` | CompoundingScorer.from_preset | RAISE / inspect branches: except Exception:         store.close()         raise |
| `gen-ai-roi-demo-v4-v50/backend/age_experiments.py:60` | c.run_query | RETURN/CONTINUE candidate: except Exception as e:         print(f"  Query raised: {e}") |
| `gen-ai-roi-demo-v4-v50/backend/age_experiments.py:183` | f.read, content[:pos].count | RETURN/CONTINUE candidate: except FileNotFoundError:             print(f"  {filename}: NOT FOUND") |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/crowdstrike_mock.py:146` | graph_client.run_query, graph_client.run_query, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:                 print(f"[CROWDSTRIKE] Failed to write {device['device_id']} to AGE: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/crowdstrike_mock.py:187` | graph_client.run_query, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:                 print(f"[CROWDSTRIKE] Failed to link {device['hostname']}: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/greynoise.py:218` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:                 logger.warning("[GREYNOISE] Existing observation lookup failed for %s: %s", ip, exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/greynoise.py:317` | graph_client.run_query, graph_client.run_query, graph_client.run_query, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:                 print(f"[GREYNOISE] Failed to write {entry['ip']} to AGE: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/greynoise.py:340` | graph_client.run_query, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:                 print(f"[GREYNOISE] Failed to link {entry['ip']}: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py:287` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:                 logger.warning("[PULSEDIVE] Existing observation lookup failed for %s: %s", value, exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py:403` | graph_client.run_query, graph_client.run_query, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:                 print(f"[PULSEDIVE] Failed to write {ioc['value']} to AGE: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py:427` | graph_client.run_query, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:                     print(f"[PULSEDIVE] Failed to link {ioc_value} -> {alert_id}: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/registry.py:95` | connector.refresh | RETURN/CONTINUE candidate: except Exception as exc:                 error_result = ConnectorResult(                     source=f"{connector.name}_error",                     indicators_ingested=0,                     relationships_created=0,                     enrichment_summary=[{"error": str(exc)}],                     timestamp=datetime.now(timezone.utc).isofor |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/registry.py:116` | connector.health_check | RETURN/CONTINUE candidate: except Exception as exc:                 status = HealthStatus(                     healthy=False,                     source=connector.name,                     message=f"Health check raised exception: {exc}",                     last_checked=datetime.now(timezone.utc).isoformat(),                 )                 print(f"[CONNECTOR] {c |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/sentinel_mock.py:26` | datetime.fromisoformat, iso_str.replace | RETURN/CONTINUE candidate: except ValueError:         # Fallback: treat as UTC naive         dt = datetime.strptime(iso_str[:19], "%Y-%m-%dT%H:%M:%S").replace(             tzinfo=timezone.utc         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/sentinel_real.py:253` | msal.ConfidentialClientApplication, app.acquire_token_for_client, logger.info, time.time, result.get, result.get, logger.error | RETURN/CONTINUE candidate: except Exception as exc:             logger.error("[Sentinel] Token acquisition failed: %s", exc)             return None |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/sentinel_real.py:335` | httpx.AsyncClient, http.patch, logger.info, logger.error | RETURN/CONTINUE candidate: except Exception as exc:             logger.error("[Sentinel-WB] PATCH exception for incident=%s: %s", incident_id, exc)             return {"success": False, "status_code": None, "error": str(exc)} |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/sentinel_real.py:382` | min, httpx.AsyncClient, resp.raise_for_status, resp.json, http.get, data.get, _normalize_sentinel_alert | RETURN/CONTINUE candidate: except Exception as exc:             logger.error("[Sentinel] Alert fetch failed: %s", exc)             return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/threat_intel_provider.py:111` | self._write_cache | RETURN/CONTINUE candidate: except Exception:             cached = self._read_cache(cache_key)             if cached is not None:                 return Provenanced(                     value=cached,                     source="cached",                     provenance_tier=self.provenance_tier,                     fetched_at=time.time(),                 )             |
| `gen-ai-roi-demo-v4-v50/backend/app/db/graph_client.py:53` | _age_factory | RAISE / inspect branches: except Exception as _exc:     raise SystemExit(f"FATAL: AGEClient init failed: {_exc}") from _exc |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1340` | self.graph.run_query | RETURN/CONTINUE candidate: except Exception as e:             log.warning(f"fetch_all_events failed: {e}")             return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1377` | _campaign_trace_query, self.graph.run_query | RETURN/CONTINUE candidate: except Exception as e:             log.warning(f"fetch_recent_events failed: {e}")             return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1413` | _campaign_trace_query, self.graph.run_query | RETURN/CONTINUE candidate: except Exception as e:             log.warning(f"fetch_single_alert_event failed: {e}")             return None |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1459` | self._has_transactional_graph_client, self._persist_campaign_seed_locked | RETURN/CONTINUE candidate: except Exception as e:             log.warning(f"persist_campaign_seed failed for {seed_for_persist['seed_key']}: {e}")             return None |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1488` | _campaign_trace_query, self.graph.run_query | RETURN/CONTINUE candidate: except Exception as e:             log.warning(f"mark_campaign_seed_promoted failed for {seed_key}: {e}")             return False |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1513` | self._has_transactional_graph_client, self.write_campaign | RETURN/CONTINUE candidate: except Exception as e:             log.warning(f"materialize_seed_campaign failed for {campaign.campaign_id}: {e}")             return False |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1555` | _campaign_trace_query, self.graph.run_query | RETURN/CONTINUE candidate: except Exception as e:             log.warning(f"cleanup_orphan_campaign_seeds failed: {e}")             return 0 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1577` | self._write_campaign_locked | RETURN/CONTINUE candidate: except Exception as e:                 log.error(f"write_campaign locked transaction failed for {campaign.campaign_id}: {e}")                 return False |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1733` | _campaign_trace_query, self.graph.run_query, _campaign_trace_query, _campaign_trace_query, self.graph.run_query, self.graph.run_query | RETURN/CONTINUE candidate: except Exception as e:             log.error(f"write_campaign failed for {campaign.campaign_id}: {e}")             return False |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1756` | self.graph.run_query | RETURN/CONTINUE candidate: except Exception as e:             log.warning(f"get_campaigns failed: {e}")             return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1780` | self.graph.run_query | RETURN/CONTINUE candidate: except Exception as e:             log.warning(f"get_campaign_detail failed: {e}")             return None |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1791` | self.graph.run_query | RETURN/CONTINUE candidate: except Exception:             return False |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:2027` | _campaign_trace_query, self.graph.run_query | RETURN/CONTINUE candidate: except Exception as e:             log.warning(f"_check_materialized_campaign failed: {e}")             return None |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:2158` | _campaign_trace_query, self.graph.run_query | RETURN/CONTINUE candidate: except Exception as e:             log.warning(f"_find_matching_campaign failed: {e}")             return None |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:2202` | _campaign_trace_query, self.graph.run_query, _campaign_trace_query, self.graph.run_query, _campaign_trace_query, self.graph.run_query | RETURN/CONTINUE candidate: except Exception as e:             log.warning(f"_add_alert_to_campaign failed: {e}") |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:227` | graph.run_query | RAISE / inspect branches: except Exception as exc:             log.warning("TravelMatchFactor error: %s", exc)             raise RuntimeError("AGE query failed for travel factor") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:291` | graph.run_query | RAISE / inspect branches: except Exception as exc:             log.warning("AssetCriticalityFactor error: %s", exc)             raise RuntimeError("AGE query failed for asset factor") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:351` | graph.run_query | RAISE / inspect branches: except Exception as exc:             log.warning("ThreatIntelEnrichmentFactor Pass 1 error: %s", exc)             raise RuntimeError("AGE query failed for threat intel factor Pass 1") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:410` | graph.run_query | RAISE / inspect branches: except Exception as e:             log.warning("_internal_campaign_score failed for %s: %s", alert_id, e)             raise RuntimeError("AGE query failed for campaign score") from e |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:473` | graph.run_query | RAISE / inspect branches: except Exception as exc:             log.warning("PatternHistoryFactor error: %s", exc)             raise RuntimeError("AGE query failed for pattern history") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:552` | graph.run_query | RAISE / inspect branches: except Exception as exc:             log.warning("PatternHistoryFactorComputer error: %s", exc)             raise RuntimeError("AGE query failed for pattern computation") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/orchestrator.py:183` | graph.run_query | RETURN/CONTINUE candidate: except Exception:         return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:124` | self.graph_client.run_query | RETURN/CONTINUE candidate: except Exception:                 return None |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/audit.py:228` | _LEDGER.append_outcome | RETURN/CONTINUE candidate: except ValueError:                 pass  # hash mismatch -- skip silently |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/checkpoint.py:86` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[CHECKPOINT] list_checkpoints query failed: %s", exc)             return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/checkpoint.py:123` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[CHECKPOINT] rollback query failed: %s", exc)             return {"error": f"AGE query failed: {exc}"} |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/checkpoint.py:146` | json.loads, np.isfinite(mu_restored).all | RETURN/CONTINUE candidate: except Exception as exc:             log.error("[CHECKPOINT] mu restore failed: %s", exc)             return {"error": f"mu restore failed: {exc}"} |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/checkpoint.py:159` | json.loads, np.isfinite(counts_restored).all | RETURN/CONTINUE candidate: except Exception as exc:                 log.debug("[CHECKPOINT] counts restore skipped: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/composite_gate.py:120` | DecisionHistoryService.get_category_stats | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[COMPOSITE] category_stats failed: %s", exc)             cat_stats = {"cat_count": 0, "rolling_accuracy": 0.5, "verified_count": 0} |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/decision_history.py:49` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[DECISION-HISTORY] query failed for category=%r: %s", category, exc)             return {"cat_count": 0, "rolling_accuracy": 0.5, "verified_count": 0} |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py:126` | self.db.run_query | RETURN/CONTINUE candidate: except Exception as exc:                 return {"error": f"AGE query failed: {exc}", "preview": True} |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/learning_state.py:99` | history.append | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[GAE] Skipping malformed history entry: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/learning_state.py:162` | os.fdopen, json.dump, os.replace, log.debug | RAISE / inspect branches: except Exception:         try:             os.unlink(tmp)         except OSError:             pass         raise |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/provenance.py:320` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[PROVENANCE] query failed for decision=%r: %s", decision_id, exc)             return None |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/shadow_mode.py:86` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[SHADOW] get_shadow_report query failed: %s", exc)             result = [] |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/similar_cases_base.py:93` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[SIMILAR-CASES] AGE query failed for category=%r: %s", category, exc)             return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:925` | graph_store.write_governed_decision, graph_store.write_outcome, graph_store.link_decision_to_entity | RETURN/CONTINUE candidate: except Exception as exc:             fail += 1             if fail <= 5:                 log.warning("[8/9] Decision %s failed: %s",                             d.get("decision_id", "?"), exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:122` | GraphConfig.load, PosteriorStore, store.health_check | RETURN/CONTINUE candidate: except Exception as exc:         logger.exception("PosteriorStore health check failed")         posterior_health = {             "healthy": False,             "status": "FAILED",             "reason": str(exc),             "error": str(exc),         } |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:321` | graph_client.run_query | RAISE / inspect branches: except Exception as _e:         print(             f"[STARTUP] Backend={_backend.upper()} "             f"verification FAILED: {_e}"         )         if _backend == "age":             raise SystemExit(                 f"FATAL: AGE verification failed: {_e}"             ) from _e         raise |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:362` | graph_client.run_query, soc_decision_where, graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as _cd_exc:         print(f"[STARTUP] correct_decisions bootstrap failed (non-blocking): {_cd_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:370` | rebuild_shadow_index, print, len | RETURN/CONTINUE candidate: except Exception as _shadow_exc:         print(f"[STARTUP] Evolution shadow index rebuild failed (non-blocking): {_shadow_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:379` | _variant_registry.get | RETURN/CONTINUE candidate: except Exception as _registry_exc:         print(f"[STARTUP] Variant registry rebuild failed (non-blocking): {_registry_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:388` | seed_vld_showcase, print | RETURN/CONTINUE candidate: except Exception as _vld_seed_exc:         print(f"[VLD] Showcase preseed failed (non-blocking): {_vld_seed_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:426` | register_rollback_handler, print | RETURN/CONTINUE candidate: except Exception as _rollback_exc:         print(f"[STARTUP] Promotion rollback handler registration failed (non-blocking): {_rollback_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:434` | write_bootstrap_state | RETURN/CONTINUE candidate: except Exception as _ds_exc:         print(f"[GAE] DeploymentState write failed (non-blocking): {_ds_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:460` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as _sync_exc:         print(f"[STARTUP] decision_count sync failed (non-blocking): {_sync_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:473` | graph_client.count_verified_decisions | RETURN/CONTINUE candidate: except Exception as _vd_exc:         print(f"[STARTUP] count_verified_decisions failed (non-blocking): {_vd_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:491` | GraphSnapshot.from_graph, _set_snapshot | RETURN/CONTINUE candidate: except Exception as _snap_exc:         print(f"[SNAPSHOT] GraphSnapshot init failed (non-blocking): {_snap_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:589` | discovery_service.refresh, logger.info | RETURN/CONTINUE candidate: except Exception as _disc_exc:         logger.warning("[Discovery] Startup warm failed (non-blocking): %s", _disc_exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:608` | _camp_repo.write_campaign | RETURN/CONTINUE candidate: except Exception as _camp_exc:         print(f"[F6] Startup recorrelation failed (non-blocking): {_camp_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:225` | graph_client.run_query, graph_client.run_query, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("Onboarding node write failed: %s", exc)             summary["errors"].append({"kind": "node", "error": str(exc)}) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:256` | graph_client.run_query, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("Onboarding relationship write failed: %s", exc)             summary["errors"].append({"kind": "relationship", "error": str(exc)}) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:427` | VariantGenerator().scan_for_opportunities, VariantGenerator | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=500, detail=str(exc)) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:471` | record_evolution_event, transition_status | RAISE / inspect branches: except HTTPException:         raise |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:473` | record_evolution_event, transition_status | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=500, detail=str(exc)) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:503` | evaluate_promotion, execute_promotion, execute_rejection | RAISE / inspect branches: except HTTPException:         raise |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:505` | evaluate_promotion, execute_promotion, execute_rejection | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=500, detail=str(exc)) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:543` | connector.get_token | RETURN/CONTINUE candidate: except Exception as exc:         return {             "status": "auth_error",             "token_valid": False,             "error": _sanitize_sentinel_health_error(str(exc), connector),         } |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/audit.py:100` | get_decision_rows, csv.writer, writer.writerow, writer.writerow | RAISE / inspect branches: except Exception as exc:         print(f"[ERROR] Audit retrieval failed: {exc}")         raise HTTPException(             status_code=500,             detail=f"Audit retrieval failed: {str(exc)}",         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/audit.py:141` | reconstruct_from_memory, verify_chain, print | RAISE / inspect branches: except Exception as exc:         print(f"[ERROR] Chain verification failed: {exc}")         raise HTTPException(             status_code=500,             detail=f"Chain verification failed: {str(exc)}",         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/cohort_status_router.py:46` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         logger.debug("cohort status graph read failed: %s", exc)         return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/compat_router.py:85` | _json_safe, scorer.trajectory, isinstance, TypeError, raw.setdefault, raw.setdefault, raw.setdefault | RAISE / inspect branches: except HTTPException:         raise |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/compat_router.py:87` | _json_safe, scorer.trajectory, isinstance, TypeError, raw.setdefault, raw.setdefault, raw.setdefault | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="SOC trajectory unavailable") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/compat_router.py:122` | learning_health | RETURN/CONTINUE candidate: except RuntimeError as exc:         return JSONResponse(             status_code=503,             content={                 "status": "UNAVAILABLE",                 "reason": "Conservation dependency unavailable",                 "detail": str(exc),             },         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/discoveries_router.py:132` | discovery_service.refresh | RETURN/CONTINUE candidate: except Exception as exc:         return {             "domain": domain,             "source_domains": [domain],             "generated_at": None,             "as_of_epoch_ms": None,             "cache": {                 "hit": False,                 "stale": False,                 "ttl_seconds": discovery_service.ttl_seconds,             |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/discoveries_router.py:154` | discovery_service.refresh | RETURN/CONTINUE candidate: except Exception as exc:         return {             "domain": domain,             "source_domains": [domain],             "generated_at": None,             "as_of_epoch_ms": None,             "cache": {                 "hit": False,                 "stale": False,                 "ttl_seconds": discovery_service.ttl_seconds,             |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/discoveries_router.py:176` | discovery_service.get_summary | RETURN/CONTINUE candidate: except Exception as exc:         return {             "domain": domain,             "source_domains": [domain],             "total": 0,             "high_count": 0,             "medium_count": 0,             "low_count": 0,             "top_discoveries": [],             "cache": {                 "hit": False,                 "stale": Fal |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:107` | graph_client.run_query, soc_decision_where | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="Deployment graph data unavailable") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:461` | graph_client.get_alert, graph_client.get_security_context, DecisionResult | RAISE / inspect branches: except HTTPException:         raise |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:463` | graph_client.get_alert, graph_client.get_security_context, DecisionResult | RAISE / inspect branches: except Exception as e:         raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:610` | graph_client.get_security_context, graph_client.create_decision_trace | RAISE / inspect branches: except HTTPException:         raise |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:612` | graph_client.get_security_context, graph_client.create_decision_trace | RAISE / inspect branches: except Exception as e:         raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:663` | _snapshot_scorer_state, _restore_scorer_state, scorer.set_conservation_status | RAISE / inspect branches: except RuntimeError as exc:         raise HTTPException(status_code=503, detail=str(exc)) from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:752` | graph_client.run_query, soc_decision_where | RAISE / inspect branches: except Exception as exc:         raise RuntimeError("Failed to load recent evolution events") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:766` | get_ledger_variant_history | RAISE / inspect branches: except ValueError as exc:         raise HTTPException(status_code=400, detail=str(exc)) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:768` | get_ledger_variant_history | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="AGE query failed for variant history") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:781` | get_ledger_evolution_summary | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="AGE query failed for evolution summary") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:790` | get_ledger_evolution_summary | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="AGE query failed for rejection summary") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:794` | get_ledger_recent_events | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="AGE query failed for rejection events") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:831` | get_ledger_recent_events, len | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="AGE query failed for recent events") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:961` | graph_client.run_query, graph_client.run_query, graph_client.run_query, soc_decision_where | RAISE / inspect branches: except Exception as e:         raise HTTPException(status_code=503, detail="AGE query failed for graph stats") from e |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:162` | _get_age_client().run_query | RAISE / inspect branches: except Exception as exc:         raise HTTPException(             status_code=503,             detail="AGE query failed for centroid evolution",         ) from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:225` | _get_age_client().run_query | RAISE / inspect branches: except Exception as exc:             raise HTTPException(status_code=503, detail="Convergence graph data unavailable") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:236` | get_learning_state, _get_age_client().run_query, decisions_per_factor.values | RAISE / inspect branches: except RuntimeError as exc:         raise HTTPException(status_code=503, detail="Convergence state unavailable") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:238` | get_learning_state, _get_age_client().run_query, decisions_per_factor.values | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="Convergence state unavailable") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:293` | _get_age_client().run_query | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="AGE query failed for OLS history") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:304` | _get_age_client().run_query | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="AGE query failed for analyst overrides") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:402` | _get_age_client().run_query, _get_age_client().run_query, decision_result[0].get, json.loads, decision_result[0].get, decision_result[0].get | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="AGE query failed for flywheel comparison") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:429` | compute_iks_v2, _get_age_client | RAISE / inspect branches: except Exception as exc:         print(f"[SOC] iks-trend compute failed: {exc}")         raise HTTPException(status_code=503, detail="AGE query failed for IKS") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:603` | _get_age_client().run_query | RAISE / inspect branches: except Exception as exc:             raise HTTPException(status_code=503, detail="AGE query failed") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:649` | _get_age_client().run_query | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="AGE query failed") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:1121` | len, getattr, getattr | RETURN/CONTINUE candidate: except Exception:             freeze_point = None             n_decisions = 0 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:1160` | int, getattr | RETURN/CONTINUE candidate: except Exception:         decision_count = 0 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:1188` | get_snapshot | RETURN/CONTINUE candidate: except Exception:         ch2_desc = "Graph snapshot unavailable." |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:68` | get_learning_state | RAISE / inspect branches: except RuntimeError as exc:         raise HTTPException(status_code=503, detail=str(exc)) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:70` | get_learning_state | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=500, detail=f"gae/weights failed: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:125` | get_learning_state, history_out.append | RAISE / inspect branches: except RuntimeError as exc:         raise HTTPException(status_code=503, detail=str(exc)) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:127` | get_learning_state, history_out.append | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=500, detail=f"gae/history failed: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:176` | get_learning_state | RAISE / inspect branches: except RuntimeError as exc:         raise HTTPException(status_code=503, detail=str(exc)) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:178` | get_learning_state | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=500, detail=f"gae/convergence failed: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:217` | get_learning_state | RAISE / inspect branches: except RuntimeError as exc:         raise HTTPException(status_code=503, detail=str(exc)) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:219` | get_learning_state | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=500, detail=f"gae/confidence-trajectory failed: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:278` | get_learning_state | RAISE / inspect branches: except RuntimeError as exc:         raise HTTPException(status_code=503, detail=str(exc)) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:280` | get_learning_state | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=500, detail=f"gae/trust-curve failed: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:334` | get_learning_state | RAISE / inspect branches: except RuntimeError as exc:         raise HTTPException(status_code=503, detail=str(exc)) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:336` | get_learning_state | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=500, detail=f"gae/before-after failed: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:371` | get_learning_state | RAISE / inspect branches: except RuntimeError as exc:         raise HTTPException(status_code=503, detail=str(exc)) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:373` | get_learning_state | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=500, detail=f"gae/weight-evolution failed: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:197` | refresh_threat_intel, print | RAISE / inspect branches: except Exception as exc:         print(f"[ERROR] Threat intel refresh failed: {exc}")         raise HTTPException(             status_code=500,             detail=f"Threat intel refresh failed: {str(exc)}",         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:229` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[WARN] ThreatIndicator persistence failed (non-fatal): {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:328` | graph_client.run_query | RAISE / inspect branches: except Exception as exc:         print(f"[ERROR] Enrichment aggregate query failed for {indicator!r}: {exc}")         raise HTTPException(             status_code=500,             detail=f"Enrichment query failed: {str(exc)}",         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:368` | graph_client.run_query | RAISE / inspect branches: except Exception as exc:         print(f"[ERROR] Enrichment summary query failed: {exc}")         raise HTTPException(             status_code=500,             detail=f"Enrichment summary query failed: {str(exc)}",         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:399` | ThreatIndicatorService.get_all_indicators | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[WARN] ThreatIndicator summary failed (non-fatal): {exc}")         threat_indicators = {"total": 0, "by_type": {}, "by_severity": {}} |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:448` | graph_client.run_query | RAISE / inspect branches: except Exception as exc:         print(f"[ERROR] Enrichment by-alert query failed for {alert_id!r}: {exc}")         raise HTTPException(             status_code=500,             detail=f"Enrichment query failed: {str(exc)}",         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/judgment.py:166` | graph_client.run_query | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=500, detail=f"AGE query failed: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:235` | graph_client.run_query, graph_client.run_query, soc_decision_where, soc_decision_where | RETURN/CONTINUE candidate: except Exception as exc:             print(f"[COMPOUNDING] weekly-trend AGE query failed: {exc}")             weekly_trend = [] |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:275` | graph_client.run_query, soc_decision_where, graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as _fb_exc:                 print(f"[COMPOUNDING] Historical fallback query failed: {_fb_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:305` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as exc:             print(f"[COMPOUNDING] evolution_events AGE query failed: {exc}")             response["evolution_events"] = [] |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:314` | graph_client.run_query, graph_client.run_query, soc_decision_where, soc_decision_where, graph_client.run_query | RAISE / inspect branches: except Exception as e:         print(f"[ERROR] Compounding metrics failed: {e}")         raise HTTPException(             status_code=500,             detail=f"Failed to generate compounding metrics: {str(e)}"         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:433` | graph_client.run_query, soc_decision_where | RAISE / inspect branches: except Exception as e:         print(f"[ERROR] Evolution events fetch failed: {e}")         raise HTTPException(status_code=503, detail="Evolution events unavailable") from e |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:479` | graph_client.run_query, soc_decision_where | RAISE / inspect branches: except Exception as e:         print(f"[METRICS] weekly-trends AGE query failed: {e}")         raise HTTPException(status_code=503, detail="Weekly trends unavailable") from e |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:534` | graph_client.run_query, soc_decision_where | RAISE / inspect branches: except Exception as throughput_exc:             print(f"[METRICS] decision-economics decisions_per_day query failed: {throughput_exc}")             raise HTTPException(                 status_code=503,                 detail="Decision economics throughput data unavailable",             ) from throughput_exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:552` | build_switching_cost_trajectory_payload | RETURN/CONTINUE candidate: except Exception as trajectory_exc:             print(f"[METRICS] switching-cost trajectory failed: {trajectory_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:565` | graph_client.run_query, soc_decision_where, graph_client.run_query, soc_decision_where, graph_client.run_query, soc_decision_where, build_switching_cost_trajectory_payload | RAISE / inspect branches: except Exception as e:         print(f"[METRICS] decision-economics AGE query failed: {e}")         raise HTTPException(status_code=503, detail="Decision economics unavailable") from e |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:637` | graph_client.run_query, soc_decision_where | RAISE / inspect branches: except Exception as exc:         print(f"[METRICS] MTTD query failed: {exc}")         raise HTTPException(status_code=503, detail="MTTD data unavailable") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:666` | graph_client.run_query, soc_decision_where | RAISE / inspect branches: except Exception as exc:         print(f"[METRICS] MTTR query failed: {exc}")         raise HTTPException(status_code=503, detail="MTTR data unavailable") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:696` | graph_client.run_query, soc_decision_where | RAISE / inspect branches: except Exception as exc:         print(f"[METRICS] FP rate query failed: {exc}")         raise HTTPException(status_code=503, detail="False-positive rate data unavailable") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:741` | graph_client.run_query, soc_decision_where, graph_client.run_query, soc_decision_where, graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[METRICS] board-export AGE query failed: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:803` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[ECON] decision query failed: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:820` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[ECON] user query failed: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/platform.py:46` | json.load | RETURN/CONTINUE candidate: except Exception as exc:         logger.warning("Cross-copilot signal fixture unavailable: %s", exc)         _SIGNAL_CACHE = [] |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/platform.py:77` | json.load | RETURN/CONTINUE candidate: except Exception as exc:         logger.warning("Domain applicability fixture unavailable: %s", exc)         _DOMAIN_TABLE_CACHE = {             "domains": [],             "engine_version": "v0.7.23",             "note": "",             "cross_domain_surfaces": "",         } |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/platform.py:111` | json.load | RETURN/CONTINUE candidate: except Exception as exc:         logger.warning("Warm-start evidence fixture unavailable: %s", exc)         _WARM_START_CACHE = {"warm_start_evidence": [], "note": ""} |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/platform.py:144` | json.load | RETURN/CONTINUE candidate: except Exception as exc:         logger.warning("Chain-credit demo fixture unavailable: %s", exc)         _CHAIN_CREDIT_CACHE = {"chain_credits": [], "summary": {}, "note": ""} |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/platform.py:177` | json.load | RETURN/CONTINUE candidate: except Exception as exc:         logger.warning("RL reward demo fixture unavailable: %s", exc)         _RL_REWARD_CACHE = {"reward_breakdown": [], "summary": {}, "note": ""} |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/platform.py:210` | json.load | RETURN/CONTINUE candidate: except Exception as exc:         logger.warning("RL exploration demo fixture unavailable: %s", exc)         _RL_EXPLORATION_CACHE = {"exploration_log": [], "summary": {}, "note": ""} |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/rl_router.py:155` | get_reward_ledger().get_chain_credits, get_reward_ledger, _to_dict, item.get, credits_received.append, item.get, credits_given.append | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("[RL API] chain credit lookup failed: %s", exc)         return {             "decision_id": decision_id,             "credits_received": [],             "credits_given": [],             "error": _safe_error(exc),         } |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/rl_router.py:190` | getattr, getattr, ledger.get_entries, len, bool, bool, bool | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("[RL API] status failed: %s", exc)         return {"error": _safe_error(exc)} |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/simulation.py:72` | get_alert_pool, a.get, print, len, len | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[SIM] Could not load alert pool from module ({exc}); using fallback") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/simulation.py:180` | _load_alert_pool | RETURN/CONTINUE candidate: except Exception as exc:         import traceback         traceback.print_exc()         _simulations[sim_id].update({             "status": "error",             "error":  str(exc),         })         print(f"[SIM] {sim_id[:8]} FAILED: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_demo_beats.py:37` | graph_client.run_query | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="SOC AGE decision counts unavailable") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_demo_beats.py:58` | graph_client.run_query | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="SOC AGE decision history unavailable") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_demo_beats.py:139` | graph_client.run_query | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="SOC AGE novelty query unavailable") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:69` | payload.get | RETURN/CONTINUE candidate: except FileNotFoundError:             payload["frozen_comparison"] = None |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:72` | payload.get | RAISE / inspect branches: except HTTPException:         raise |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:74` | payload.get | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="SOC learning control room unavailable") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:101` | LearningHealthMonitor.evaluate | RAISE / inspect branches: except FileNotFoundError as exc:         raise HTTPException(status_code=404, detail="SOC Frozen Twin has not been initialized") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:103` | LearningHealthMonitor.evaluate | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="SOC Frozen Twin comparison unavailable") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:62` | get_learning_state, get_learning_store | RETURN/CONTINUE candidate: except Exception as exc:         logger.exception("Diagnostics failed for soc")         result = build_diagnostics("soc", None, None, extras={"error": str(exc)})         return result |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:592` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as qe:                 print(f"[SOC] cross-context AGE query failed: {qe}")                 data = get_metric_data(metric_id) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:634` | graph_client.run_query | RAISE / inspect branches: except HTTPException:         raise |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:636` | graph_client.run_query | RAISE / inspect branches: except Exception as e:         print(f"[ERROR] SOC query failed: {e}")         raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:680` | get_profile_scorer, enumerate, float, round, category_scores.append, np.mean, np.abs | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[SOC] detection-engineering scorer error: {exc}")         category_scores = [             {"category": cat, "quality_score": None, "drift": None, "status": "unavailable"}             for cat in SOC_CATEGORIES         ] |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:705` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as qe:             print(f"[SOC] noise-map query failed for {cat}: {qe}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:848` | graph_client.run_query, graph_client.run_query, graph_client.run_query, graph_client.run_query, soc_decision_where, graph_client.run_query, graph_client.run_query | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="Threat landscape data unavailable") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:909` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[SOC] attack-tactic-breakdown query failed: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:990` | graph_client.run_query, graph_client.run_query, graph_client.run_query, soc_decision_where, graph_client.run_query, soc_decision_where, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as e:         print(f"[SOC] analytics AGE query failed: {e}")         return {             "total_alerts": 0,             "open_alerts": 0,             "total_decisions": 0,             "correct_decisions": 0,             "accuracy_pct": None,             "category_breakdown": [],             "source": "unavailable",      |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1034` | _get_ls, getattr, bool, getattr | RETURN/CONTINUE candidate: except RuntimeError:         # Learning state not initialized yet — return defaults         pass |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1037` | _get_ls, getattr, bool, getattr | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[SOC] learning-state error: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1054` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[SOC] learning-state verified_at query failed: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1062` | compute_iks_v2 | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[SOC] learning-state iks_v2 failed: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1079` | _get_snap_ls, iks_v2_data.get | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] learning-state verified_decisions query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1166` | graph_client.run_query, soc_decision_where | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=500, detail=f"AGE query failed: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1222` | graph_client.run_query, soc_decision_where | RAISE / inspect branches: except Exception as _exc:         raise HTTPException(             status_code=503,             detail="SOC calibration data unavailable",         ) from _exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1242` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception:         pass |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1532` | LearningHealthMonitor.evaluate | RETURN/CONTINUE candidate: except Exception as exc:         logger.warning("[COMPLIANCE] Conservation status unavailable: %s", exc)         return "UNKNOWN" |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1543` | verify_chain, bool, verification.get | RETURN/CONTINUE candidate: except Exception as exc:         logger.warning("[COMPLIANCE] Audit chain verification unavailable: %s", exc)         return False |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2089` | graph_client.run_query, soc_decision_where | RAISE / inspect branches: except Exception as exc:         raise HTTPException(             status_code=503,             detail="SOC accuracy trajectory unavailable",         ) from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2164` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as _exc:         import logging as _log         _log.getLogger(__name__).warning("[analyst-benchmarking] AGE query failed: %s", _exc)         return {             "status": "accumulating",             "message": "Shadow decision data not yet loaded. Run Step 3 ingest first.",         } |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2200` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception:         cat_result = [] |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2261` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception:         arch_result = [] |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2286` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception:         day_result = [] |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2393` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception:         pass |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2444` | val.to_native, native.replace, int, native.timestamp | RETURN/CONTINUE candidate: except AttributeError:             pass |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2513` | graph_client.run_query, _graph_dt_to_epoch_s | RETURN/CONTINUE candidate: except Exception:             graph_reachable = False |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2628` | create_centroid_checkpoint | RAISE / inspect branches: except RuntimeError as exc:         from fastapi import HTTPException         raise HTTPException(status_code=503, detail=str(exc)) from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2651` | restore_centroid_checkpoint | RAISE / inspect branches: except FileNotFoundError as exc:         raise HTTPException(status_code=404, detail=str(exc)) from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2653` | restore_centroid_checkpoint | RAISE / inspect branches: except ValueError as exc:         raise HTTPException(status_code=409, detail=str(exc)) from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2655` | restore_centroid_checkpoint | RAISE / inspect branches: except RuntimeError as exc:         raise HTTPException(status_code=503, detail=str(exc)) from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2675` | list_centroid_checkpoints | RAISE / inspect branches: except RuntimeError as exc:         from fastapi import HTTPException         raise HTTPException(status_code=503, detail=str(exc)) from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2699` | get_learning_state | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] gate-config n_decisions query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2789` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] tab2 alert_count query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2798` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] tab2 pending_count query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2811` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] tab2 raw_top categories query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2838` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as _exc:             print(f"[SOC] tab2 per-category verified_map query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2905` | compute_visible_iks, interpret_iks_v2 | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] tab2 iks drift query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2917` | compute_iks_v2, iks_data.get, iks_data.get, iks_data.get, iks_data.get | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] tab2 iks_v2 query failed: {_exc}")         try:             from app.state.graph_snapshot import get_snapshot as _get_snap_t2_iks             snapshot_iks = float(_get_snap_t2_iks().iks_score)             if iks_score <= 0.0 and snapshot_iks > 0.0:                 iks_score = snapshot_iks    |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2925` | float, _get_snap_t2_iks, interpret_iks_v2 | RETURN/CONTINUE candidate: except Exception as _snap_iks_exc:             print(f"[SOC] tab2 snapshot IKS fallback unavailable: {_snap_iks_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2935` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] tab2 drift_alert_count query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2972` | _get_snap_t2 | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] tab2 verified_decisions snapshot failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3101` | _BOOTSTRAP_CENTROIDS_PATH.open, json.load, payload.get | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] bootstrap baseline unavailable; using uniform fallback: {_exc}")         return None |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3144` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] tab3 graph_node_count query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3205` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as _exc:             print(f"[SOC] tab3 pending alert query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3231` | _np.full, _scorer.score, round, float | RETURN/CONTINUE candidate: except Exception as _exc:                 print(f"[SOC] tab3 live scoring failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3263` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as _exc:             print(f"[SOC] tab3 override_rate query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3275` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] tab3 total_verified query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3337` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] tab4 total_decisions query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3346` | max, _get_ls_t4 | RETURN/CONTINUE candidate: except Exception as _exc:             print(f"[SOC] tab4 decision_count fallback failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3366` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] tab4 decisions_per_day query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3375` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] tab4 learning_events_count query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3412` | _get_snap_t4 | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] tab4 verified_decisions snapshot failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3441` | build_switching_cost_trajectory_payload | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] tab4 switching_cost_trajectory failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3478` | compute_visible_iks | RETURN/CONTINUE candidate: except Exception:         try:             from app.state.graph_snapshot import get_snapshot             snapshot = get_snapshot()             verified_decisions = snapshot.verified_decisions             iks_score = snapshot.iks_score         except RuntimeError:             pass |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3485` | get_snapshot | RETURN/CONTINUE candidate: except RuntimeError:             pass |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3495` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] tab5 flywheel_edge_count query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3779` | _get_ls | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] analyst-eta n_decisions query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3864` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] analyst-detail decision_counts query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3871` | _get_ls | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] analyst-detail n_decisions query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:4012` | compute_volume_baseline, baseline.get | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] learning-health baseline_daily query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:4101` | compute_iks_v2, iks_data.get | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] centroid-export iks_score query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:4261` | get_bootstrap_centroids | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] centroid-evolution bootstrap query failed: {_exc}")         bootstrap = None |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:4367` | read_decision_distance_log | RETURN/CONTINUE candidate: except Exception as _exc:         print(f"[SOC] reconvergence-log entries query failed: {_exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/time_machine_router.py:71` | get_evolution_timeline | RAISE / inspect branches: except RuntimeError as exc:         raise HTTPException(status_code=503, detail=str(exc)) from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:220` | run_soc_decision_pipeline_shadow | RETURN/CONTINUE candidate: except Exception as exc:         shadow = {             "enabled": True,             "matched": False,             "status": "shadow_failed",             "error_type": type(exc).__name__,             "error": "shadow pipeline unavailable",             "differences": [],             "excluded_fields": [                 "decision_id",       |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:517` | graph_client.run_query, redact_payload | RAISE / inspect branches: except Exception as e:         print(f"[ERROR] Failed to fetch alert queue: {e}")         import traceback         traceback.print_exc()         raise HTTPException(             status_code=500,             detail=f"Failed to fetch alerts from AGE: {str(e)}"         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:897` | get_soc_conservation_provider().update_from_health, get_soc_conservation_provider, (_health.get('conservation') or {}).get | RETURN/CONTINUE candidate: except Exception as _rl_health_exc:                         logger.warning("[RL] Exploration health check failed: %s", _rl_health_exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:921` | _soc_perf_phase, get_soc_conservation_provider().update_from_health, get_soc_conservation_provider, (_health.get('conservation') or {}).get | RETURN/CONTINUE candidate: except Exception as _rl_explore_exc:             logger.warning("[RL] Exploration proposal failed: %s", _rl_explore_exc)             _rl_exploration_decision = None             _rl_explored_action_name = None             _rl_exploration_executed = False             _rl_exploration_status = "unavailable" |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:983` | _authority_decision.to_dict | RETURN/CONTINUE candidate: except Exception as _authority_exc:             # Authority is a safety layer, never a reason to take down triage.             # Preserve the original scorer action if the authority subsystem is             # unavailable or malformed; downstream referral rules still run.             logger.warning(                 "[AUTHORITY] evaluation  |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1223` | _soc_perf_phase, build_campaign_context_payload | RETURN/CONTINUE candidate: except Exception as _camp_exc:             logger.warning("[TRIAGE] Campaign wiring failed for %s: %s", alert_id, _camp_exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1242` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as _camp_flag_exc:             logger.warning(                 "[TRIAGE] Campaign Decision flag write failed for %s: %s",                 alert_id,                 _camp_flag_exc,             ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1339` | _soc_perf_phase, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as _cg_exc:             logger.warning("[TRIAGE] composite gate failed: %s", _cg_exc)             _composite = {                 "auto_approve": False,                 "approval_score": 0.0,                 "reason_codes": [f"gate error: {_cg_exc}"],                 "features": {},             } |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1385` | _soc_perf_phase | RETURN/CONTINUE candidate: except Exception as _prov_exc:             logger.warning("[TRIAGE] provenance build failed: %s", _prov_exc)             _provenance_payload = {"decision_id": decision_id, "factors": [], "error": str(_prov_exc)} |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1473` | _soc_perf_phase, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as _rl_meta_exc:                 logger.warning("[RL] Exploration metadata write failed: %s", _rl_meta_exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1555` | _soc_perf_phase, _get_cluster_history | RETURN/CONTINUE candidate: except Exception as _cluster_exc:             logger.warning("[TRIAGE] Cluster history failed for %s: %s", alert_id, _cluster_exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1692` | _soc_perf_phase, _soc_perf_phase, graph_client.get_alert, _soc_perf_phase, _soc_perf_phase, _soc_perf_phase, _soc_perf_phase | RAISE / inspect branches: except HTTPException as exc:         _perf_total_status = "error"         _perf_total_exception = type(exc).__name__         raise |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1696` | _soc_perf_phase, _soc_perf_phase, graph_client.get_alert, _soc_perf_phase, _soc_perf_phase, _soc_perf_phase, _soc_perf_phase | RAISE / inspect branches: except Exception as e:         _perf_total_status = "error"         _perf_total_exception = type(e).__name__         print(f"[ERROR] Failed to analyze alert: {e}")         import traceback         traceback.print_exc()         raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1765` | get_decision_factors | RETURN/CONTINUE candidate: except Exception as exc:             print(f"[EXECUTE] get_decision_factors failed for {alert_id}: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1885` | graph_client.get_security_context, get_decision_factors, graph_client.run_query | RAISE / inspect branches: except HTTPException:         raise |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1887` | graph_client.get_security_context, get_decision_factors, graph_client.run_query | RAISE / inspect branches: except Exception as e:         print(f"[ERROR] Failed to execute action: {e}")         raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}") |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1940` | graph_client.run_query | RAISE / inspect branches: except Exception as e:         print(f"[ERROR] Failed to reset alerts: {e}")         raise HTTPException(             status_code=500,             detail=f"Failed to reset alerts: {str(e)}"         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2151` | _soc_perf_phase, _audit_outcome, _outcome_rec.get, _outcome_rec.get, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as _e:             logger.warning("[AUDIT] Outcome audit failed: %s", _e) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2177` | _soc_perf_phase, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as _qe:                 logger.debug("[ETA] Analyst quality query: %s", _qe) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2220` | _rl_soc_config, getattr, get_reward_computer().compute, get_reward_ledger, get_reward_computer, record.get | RETURN/CONTINUE candidate: except Exception as _rl_reward_exc:                 logger.warning("[RL] Reward computation failed: %s", _rl_reward_exc)                 reward_result = None                 _rl_reward_ledger = None |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2244` | _acquire_scorer_non_scorable, isinstance, _ps_non_scorable.capture_existing_state | RETURN/CONTINUE candidate: except Exception as _snapshot_exc:                     logger.warning(                         "[GAE][LEARN] SOC non-scorable state capture failed: %s",                         _snapshot_exc,                     ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2357` | _soc_perf_phase, get_soc_conservation_provider().update_from_health, _soc_effective_conservation_status, _soc_perf_phase, LearningHealthMonitor.evaluate, get_soc_conservation_provider | RETURN/CONTINUE candidate: except Exception as _cse:                     logger.warning("Conservation status update failed: %s", _cse)                     _conservation_block = True  # fail-closed: unknown health -> block |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2441` | _ps_blocked.capture_existing_state | RETURN/CONTINUE candidate: except Exception as _snapshot_exc:                                         logger.warning(                                             "[GAE][LEARN] SOC guarded-pause state capture failed: %s",                                             _snapshot_exc,                                         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2446` | _acquire_scorer, isinstance, _ps_blocked.capture_existing_state, logger.warning | RETURN/CONTINUE candidate: except Exception as _acquire_exc:                             # The outcome write above remains authoritative. A                             # cold-start scorer snapshot is only an optional                             # learning artifact and must not turn the route into                             # a 500 response.                         |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2526` | _ps_out.capture_existing_state | RETURN/CONTINUE candidate: except Exception as _snapshot_exc:                                             logger.warning(                                                 "[GAE][LEARN] SOC guarded-pause state capture failed: %s",                                                 _snapshot_exc,                                             ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2545` | _soc_perf_phase | RETURN/CONTINUE candidate: except Exception as _welford_exc:                                         logger.warning(                                             "[GAE][LEARN] SOC DK Welford update failed: %s",                                             _welford_exc,                                         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2576` | _compound_scorer._persist_learning_artifacts | RETURN/CONTINUE candidate: except KeyError as _checkpoint_exc:                                                 # The authoritative graph outcome and                                                 # centroid write already succeeded.                                                 # A stale scorer-local decision index                                                  |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2622` | _soc_perf_phase, _persist_soc_outcome_and_centroid, _pre_centroids.get | RAISE / inspect branches: except Exception as _centroid_exc:                                         logger.exception(                                             "[GAE][LEARN] SOC L5 centroid persistence failed: %s",                                             _centroid_exc,                                         )                                         raise |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2639` | _soc_perf_phase, _persist_soc_dk_weights | RETURN/CONTINUE candidate: except Exception as _dk_persist_exc:                                             logger.warning(                                                 "[GAE][LEARN] SOC L5 DK persistence failed: %s",                                                 _dk_persist_exc,                                             ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2761` | _snap.on_verified_decision | RETURN/CONTINUE candidate: except Exception as _snap_exc:                         logger.warning(                             "[SNAPSHOT] verified_decisions increment failed: %s",                             _snap_exc,                         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2776` | _get_ps_snap, _snap.on_iks_recalculated, _compute_visible_iks | RETURN/CONTINUE candidate: except Exception as _snap_exc:                             logger.warning(                                 "[SNAPSHOT] IKS recalculation failed: %s",                                 _snap_exc,                             ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2781` | _snap.on_verified_decision | RETURN/CONTINUE candidate: except Exception as _snap_exc:                     logger.warning(                         "[SNAPSHOT] Snapshot update failed (non-blocking): %s",                         _snap_exc,                     ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2822` | _get_mu_zero, _get_ps, _asyncio.create_task, logger.info, float, _g1_task, len | RETURN/CONTINUE candidate: except Exception as _g1_exc:                     logger.warning("[EXP-G1] Distance log scheduling failed: %s", _g1_exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2882` | _soc_perf_phase, graph_client.run_query, get_learning_state | RETURN/CONTINUE candidate: except Exception as _evo_exc:                         logger.warning(                             "[FLYWHEEL] TRIGGERED_EVOLUTION creation failed (non-blocking): %s",                             _evo_exc,                         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2910` | get_learning_state | RETURN/CONTINUE candidate: except Exception as _rl_chain_exc:                     logger.warning("[RL] Chain credit assignment failed: %s", _rl_chain_exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2928` | _rl_reward_ledger.append, _rl_bool, _rl_bool, _record_for_reward.get, _record_for_reward.get | RETURN/CONTINUE candidate: except Exception as _rl_ledger_exc:                 logger.warning("[RL] Reward ledger append failed: %s", _rl_ledger_exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2981` | _result_payload.get | RETURN/CONTINUE candidate: except Exception as _sn_exc:                 logger.warning("ServiceNow mock creation failed: %s", _sn_exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3006` | _soc_perf_phase, _soc_perf_phase, _soc_perf_phase, _soc_store.get_decision, _decision_before.get, graph_client.run_query | RAISE / inspect branches: except HTTPException as exc:         _perf_total_status = "error"         _perf_total_exception = type(exc).__name__         raise |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3010` | _soc_perf_phase, _soc_perf_phase, _soc_perf_phase, _soc_store.get_decision, _decision_before.get, graph_client.run_query | RAISE / inspect branches: except ValueError as exc:         _perf_total_status = "error"         _perf_total_exception = type(exc).__name__         raise |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3014` | _soc_perf_phase, _soc_perf_phase, _soc_perf_phase, _soc_store.get_decision, _decision_before.get, graph_client.run_query | RAISE / inspect branches: except Exception as e:         _perf_total_status = "error"         _perf_total_exception = type(e).__name__         print(f"[ERROR] Failed to process outcome: {e}")         import traceback         traceback.print_exc()         raise HTTPException(             status_code=500,             detail=f"Failed to process outcome: {str(e)}"     |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3352` | get_reward_summary, print | RAISE / inspect branches: except Exception as e:         print(f"[ERROR] Failed to get reward summary: {e}")         raise HTTPException(             status_code=500,             detail=f"Failed to get reward summary: {str(e)}"         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3404` | get_decision_factors | RAISE / inspect branches: except HTTPException:         raise |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3406` | get_decision_factors | RAISE / inspect branches: except Exception as e:         print(f"[ERROR] Failed to get decision factors: {e}")         raise HTTPException(             status_code=500,             detail=f"Failed to get decision factors: {str(e)}",         ) |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3561` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as e:         print(f"[ERROR] Failed to get graph data: {e}")         return {"nodes": [], "relationships": []} |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:85` | np.array, compute_snr_report, np.asarray, list, list, list | RETURN/CONTINUE candidate: except Exception as exc:         _log.warning("ceiling_estimate(balance_sheet): SNR computation failed -- returning None (source=fallback): %s", exc)         return None, {} |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:101` | get_snapshot | RETURN/CONTINUE candidate: except RuntimeError:         return {}, 0 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:108` | float, compute_visible_iks | RETURN/CONTINUE candidate: except Exception as exc:         _log.warning("overall_iks(balance_sheet): IKS computation failed -- returning 0.0 (source=fallback): %s", exc)         return 0.0 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:133` | build_centroid_export | RETURN/CONTINUE candidate: except Exception as exc:         _log.warning("centroid_drift(balance_sheet): drift computation failed -- returning 0.0 per category (source=fallback): %s", exc)         return {category: 0.0 for category in SOC_CATEGORIES} |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:141` | LearningHealthMonitor.evaluate | RETURN/CONTINUE candidate: except Exception:         return {"status": "unavailable"} |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:150` | cast, auto_approve_stats | RETURN/CONTINUE candidate: except Exception as exc:         _log.warning("auto_approve_coverage_pct(balance_sheet): stats fetch failed -- returning 0.0 (source=fallback): %s", exc)         return {"by_category": {}, "coverage_pct": 0.0, "total_decisions": 0, "auto_approved": 0} |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:158` | get_evolution_timeline | RETURN/CONTINUE candidate: except Exception:         return {"timeline": [], "ceiling_estimate": None} |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cluster_history.py:155` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         logger.warning("[CLUSTER-HISTORY] query failed for user=%s: %s", source_user, exc)         return None |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py:210` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:                 log.warning("Discovery graph clock query failed: %s", exc)                 continue |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py:270` | self._get_as_of_epoch_ms | RETURN/CONTINUE candidate: except Exception as exc:             errors.append(f"graph_clock: {exc}")             log.warning("Discovery graph clock failed: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py:327` | discoveries.extend, self._cross_factor_anomaly_discovery | RETURN/CONTINUE candidate: except Exception as exc:                 algorithm_failures += 1                 errors.append(f"{DiscoveryType.CROSS_FACTOR_MISROUTE.value}: {exc}")                 log.warning("Cross-factor discovery failed: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evidence_room.py:125` | get_decision_rows | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[EvidenceRoom] audit collection failed: %s", exc)             return _empty_audit_trail(), _empty_hash_chain(), [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evidence_room.py:182` | LearningHealthMonitor.evaluate | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[EvidenceRoom] conservation collection failed: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evidence_room.py:196` | get_snapshot | RETURN/CONTINUE candidate: except Exception as exc:             log.debug("[EvidenceRoom] graph snapshot unavailable for conservation: %s", exc)             try:                 from app.services.gae_state import get_learning_state                 verified_decisions = _safe_int(get_learning_state().decision_count)             except Exception as state_exc:          |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evidence_room.py:202` | get_learning_state | RETURN/CONTINUE candidate: except Exception as state_exc:                 log.debug("[EvidenceRoom] learning state unavailable for conservation: %s", state_exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evidence_room.py:231` | float, compute_visible_iks | RETURN/CONTINUE candidate: except Exception as exc:                 log.debug("[EvidenceRoom] IKS conservation fallback unavailable: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evidence_room.py:267` | get_snapshot, (snap.category_counts or {}).items | RETURN/CONTINUE candidate: except Exception as exc:             log.debug("[EvidenceRoom] graph snapshot unavailable for override analysis: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:282` | LearningHealthMonitor.evaluate | RETURN/CONTINUE candidate: except Exception as exc:             self.mark_unknown(f"learning_health_error:{exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:234` | self.db.run_query, self.db.run_query | RETURN/CONTINUE candidate: except Exception:             pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:344` | soc_decision_where, self.db.run_query, self.db.run_query | RETURN/CONTINUE candidate: except Exception:             pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:385` | soc_decision_where, self.db.run_query, self.db.run_query | RETURN/CONTINUE candidate: except Exception:             pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:421` | graph_service.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception:         pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:430` | max, _get_ls_en | RETURN/CONTINUE candidate: except Exception:             pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:441` | graph_service.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception:         pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:451` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception:         pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:461` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception:         pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:475` | _get_ps_en, _compute_iks_drift_en, float | RETURN/CONTINUE candidate: except Exception:         pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:482` | compute_iks_v2, float, iks_data.get | RETURN/CONTINUE candidate: except Exception:             pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:503` | graph_service.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception:         pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:524` | graph_service.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception:         category_accuracy = [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:546` | graph_service.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception:         pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:583` | graph_service.run_query, json.loads | RETURN/CONTINUE candidate: except Exception:         pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:613` | LearningHealthMonitor.evaluate | RETURN/CONTINUE candidate: except Exception:         health_metadata = {} |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:635` | float, compute_visible_iks | RETURN/CONTINUE candidate: except Exception:             pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:235` | GraphConfig.load | RAISE / inspect branches: except GraphConfigError as exc:         raise GraphConfigError(             "SOC L5 learning store requires valid GraphConfig"         ) from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:251` | _load_age_learning_store_adapter | RAISE / inspect branches: except Exception as exc:         raise RuntimeError(             f"SOC L5 learning store initialization failed (graph={graph_name})"         ) from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:370` | _profile_scorer.capture_existing_state, log.info | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("SOC startup state capture failed: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:455` | np.asarray(centroids[category_index, action_index], dtype=np.float64).copy().tolist, np.asarray(centroids[category_index, action_index], dtype=np.float64).copy | RETURN/CONTINUE candidate: except Exception:         return _optional_absence() |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:499` | target_store.update_centroid | RAISE / inspect branches: except Exception as exc:         (logger or log).error("SOC L5 centroid persistence failed", exc_info=True)         raise RuntimeError("SOC L5 centroid persistence failed") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:568` | store.get_posterior | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("[GAE] Could not load mu0 from AGE: %s", exc)         return _optional_absence() |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:828` | graph_client.run_query, graph_client.run_query, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as e:         log.warning("DeploymentState persist failed: %s", e) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:861` | graph_client.run_query, json.loads, json.loads | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("[GAE] get_bootstrap_centroids failed: %s", exc)         return _optional_absence() |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:144` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[GRAPH-EXPLORER] run_safe_query failed: %s", exc)             return {"error": str(exc), "query": cypher} |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:196` | soc_decision_where, graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[GRAPH-EXPLORER] get_top_nodes failed: %s", exc)             return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:221` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning(                 "[GRAPH-EXPLORER] get_node_neighbors failed node_id=%r: %s", node_id, exc             )             neighbors = [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:254` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[GRAPH-EXPLORER] get_graph_summary node count failed: %s", exc)             counts = [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:266` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[GRAPH-EXPLORER] get_graph_summary rel count failed: %s", exc)             rel_counts = [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:308` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning(                 "[GRAPH-EXPLORER] prebuilt query %r failed: %s", query_name, exc             )             return {"error": str(exc), "query": cypher} |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:131` | get_mu_zero, compute_iks, float, result.get | RETURN/CONTINUE candidate: except Exception:             pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:138` | compute_iks_v2, float, iks_data.get | RETURN/CONTINUE candidate: except Exception:             pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:165` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("[IKS] get_iks_trend query failed: %s", exc)         return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:184` | json.loads | RETURN/CONTINUE candidate: except Exception as exc:             log.debug("[IKS] Skipping malformed snapshot row: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:217` | graph_service.run_query, soc_decision_where | RAISE / inspect branches: except Exception as exc:         log.warning("[IKS-v2] graph_richness query failed: %s", exc)         raise RuntimeError("AGE query failed for IKS graph richness") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:235` | graph_service.run_query, soc_decision_where | RAISE / inspect branches: except Exception as exc:         log.warning("[IKS-v2] decision_maturity query failed: %s", exc)         raise RuntimeError("AGE query failed for IKS decision maturity") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:251` | graph_service.run_query, soc_decision_where | RAISE / inspect branches: except Exception as exc:         log.warning("[IKS-v2] trust_coverage query failed: %s", exc)         raise RuntimeError("AGE query failed for trust coverage") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:274` | graph_service.run_query, soc_decision_where | RAISE / inspect branches: except Exception as exc:         log.warning("[IKS-v2] factor_quality query failed: %s", exc)         raise RuntimeError("AGE query failed for factor quality") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:326` | graph_client.run_query | RAISE / inspect branches: except Exception as exc:         log.debug("[IKS] delta_7d query failed: %s", exc)         raise RuntimeError("AGE query failed for IKS delta") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/investigation_patterns.py:120` | run_query, self.graph_query.format | RETURN/CONTINUE candidate: except Exception as exc:             logger.warning("SOC VLD pattern %s bounded read failed: %s", self.pattern_name, exc)             return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/investigation_patterns.py:133` | _maybe_await, get_context | RETURN/CONTINUE candidate: except Exception as exc:             logger.warning("SOC VLD pattern %s context fallback failed: %s", self.pattern_name, exc)             return {"read_error": type(exc).__name__} |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:500` | graph_service.run_query | RAISE / inspect branches: except Exception as exc:             log.debug("[HEALTH] red_days query failed: %s", exc)             raise RuntimeError("AGE query failed for RED-day count") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:620` | soc_decision_where, graph_service.run_query | RAISE / inspect branches: except Exception as exc:         log.debug("[HEALTH] SOC verified conservation query failed: %s", exc)         raise RuntimeError("AGE query failed for SOC conservation stats") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:687` | store.get_conservation_state | RETURN/CONTINUE candidate: except Exception as exc:             log.warning(                 "[HEALTH][L5] Conservation state read failed; skipping persistence "                 "(domain=soc, status=%s, error_type=%s)",                 status,                 type(exc).__name__,             )             return |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:725` | store.update_conservation_state | RETURN/CONTINUE candidate: except Exception as exc:             log.warning(                 "[HEALTH][L5] Conservation state update failed "                 "(domain=soc, status=%s, error_type=%s)",                 status,                 type(exc).__name__,             ) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:776` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("[D3] volume_baseline query failed: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:789` | _get_ls | RETURN/CONTINUE candidate: except Exception:         pass |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:874` | graph_client.run_query | RAISE / inspect branches: except Exception as exc:         log.warning("[D2] compute_category_baseline query failed: %s", exc)         raise RuntimeError("AGE query failed for category baseline") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:976` | soc_decision_where, graph_client.run_query | RAISE / inspect branches: except Exception as exc:         log.warning("[D5] compute_analyst_precision query failed: %s", exc)         raise RuntimeError("AGE query failed for analyst precision") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:1026` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as exc:         log.debug("[VERIF-HEALTH] total_decisions query failed: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:1036` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as exc:         log.debug("[VERIF-HEALTH] verified_decisions query failed: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:1063` | soc_decision_where, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         log.debug("[VERIF-HEALTH] last_7d query failed: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:1081` | soc_decision_where, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         log.debug("[VERIF-HEALTH] prior_7d query failed: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:1099` | LearningHealthMonitor.evaluate | RETURN/CONTINUE candidate: except Exception as exc:         log.debug("[VERIF-HEALTH] conservation check failed: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/model_swap.py:152` | _score_alert, alert_results.append | RETURN/CONTINUE candidate: except Exception as exc:             errors.append(f"{alert.get('alert_id') or alert.get('id') or 'UNKNOWN'}: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/services/model_swap.py:171` | _score_alert, _score_alert | RETURN/CONTINUE candidate: except Exception as exc:             reproducibility_check = {                 "passed": False,                 "reason": str(exc),             }             errors.append(f"reproducibility_check: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/services/narrative.py:345` | decision.get, decision.get, decision.get | RETURN/CONTINUE candidate: except Exception as exc:             logger.error("[NARRATIVE] TemplateNarrativeProvider.generate failed: %s", exc)             alert_id = alert.get("id", "UNKNOWN")             return (                 f"Investigation narrative unavailable for {alert_id}. "                 "Review the recommendation and situation analysis panels below."  |
| `gen-ai-roi-demo-v4-v50/backend/app/services/narrative.py:397` | self._build_prompt, httpx.post, resp.raise_for_status, resp.json, (data.get('response') or '').strip, data.get, ValueError | RETURN/CONTINUE candidate: except Exception as exc:             logger.warning(                 "[NARRATIVE] Ollama unavailable (%s); falling back to template", exc             )             return self._fallback.generate(alert, decision, factors, calibration_context) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/override_detector.py:62` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("[OverrideDetector] AGE query failed -- using empty set: %s", exc)         examples = [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:134` | psycopg.connect | RAISE / inspect branches: except Exception as exc:             raise RuntimeError("[PosteriorStore] save failed") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:168` | psycopg.connect | RAISE / inspect branches: except Exception as exc:             raise RuntimeError("[PosteriorStore] load failed") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:190` | psycopg.connect | RAISE / inspect branches: except Exception as exc:             raise RuntimeError("[PosteriorStore] clear failed") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:198` | self._graph_store.get_posterior | RETURN/CONTINUE candidate: except Exception as exc:                 return {"healthy": False, "error": str(exc)} |
| `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:390` | get_variant_history, _paired_outcomes | RETURN/CONTINUE candidate: except Exception as exc:         log.debug("Shadow batch stats unavailable for %s: %s", variant_id, exc)         return {"batch_count": 0, "batch_std": 0.0, "win_rates": []} |
| `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:529` | getattr, callable, call_soon, _create_rollback_task | RETURN/CONTINUE candidate: except RuntimeError as exc:             log.warning("Promotion rollback scheduling failed on captured loop: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:568` | asyncio.get_running_loop, get_profile_scorer, _state_machine_for_scorer, hasattr, id, _schedule_rollback_check, state_machine.register_handler | RETURN/CONTINUE candidate: except Exception as exc:         log.debug("Promotion rollback handler registration failed: %s", exc)         return False |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reasoning.py:92` | self.model.generate_content_async, cast(str, response.text).strip, cast | RETURN/CONTINUE candidate: except Exception as e:             # Fallback reasoning if LLM fails             return self._fallback_reasoning(action, context) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:106` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("[EXP-G1] Failed to log reconvergence event: %s", exc)         return None |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:178` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("[EXP-G1] DecisionDistanceLog failed: %s", exc)         return None |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:190` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("[EXP-G1] Failed to read DecisionDistanceLog: %s", exc)         return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:208` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("[EXP-G1] Failed to fetch category distribution: %s", exc)         return {} |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:224` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("[EXP-G1] Failed to read reconvergence events: %s", exc)         return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:469` | int, int | RETURN/CONTINUE candidate: except (TypeError, ValueError) as exc:             log.warning("[CreditAssigner] invalid chain-credit numeric input: %s", exc)             return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:493` | self.graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[CreditAssigner] chain-credit query failed: %s", exc)             return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:506` | int, cast, row.get | RETURN/CONTINUE candidate: except (TypeError, ValueError):                 continue |
| `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:644` | GraphConfig.load, create_soc_graph_store, PosteriorStore, PosteriorStore | RAISE / inspect branches: except Exception as exc:             log.error("[RL] graph configuration/posterior initialization failed: %s", exc)             raise RuntimeError("[RL] graph configuration is required for exploration") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:653` | ExplorationPolicy, len, len | RAISE / inspect branches: except Exception as exc:             log.error("[RL] posterior graph load failed: %s", exc)             raise RuntimeError("[RL] posterior graph state is unavailable") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/sentinel_poller.py:127` | connector.fetch_alerts | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("Sentinel poll failed: %s", exc)             return {                 "fetched": 0,                 "new": 0,                 "duplicates": 0,                 "ingested": 0,                 "ingestion_blocked": 0,                 "errors": 1,             } |
| `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py:244` | record_evolution_event, round, round | RETURN/CONTINUE candidate: except Exception as exc:                 log.warning("Shadow batch write failed for variant_id=%s: %s", variant_id, exc)                 continue |
| `gen-ai-roi-demo-v4-v50/backend/app/services/simulation.py:351` | graph_client.get_alert | RETURN/CONTINUE candidate: except Exception:                 alert_data = None |
| `gen-ai-roi-demo-v4-v50/backend/app/services/simulation.py:365` | graph_client.get_security_context | RETURN/CONTINUE candidate: except Exception:                 ctx = None |
| `gen-ai-roi-demo-v4-v50/backend/app/services/simulation.py:553` | _sim_outcome | RETURN/CONTINUE candidate: except Exception as _e:                 print(f"[SIM-AUDIT] Outcome audit: {_e}") |
| `gen-ai-roi-demo-v4-v50/backend/app/services/snapshots.py:68` | scorer.centroids.tolist, scorer.counts.tolist, graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("[GAE] ProfileSnapshot write failed at step=%d: %s", decision_count, exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py:194` | json.loads | RETURN/CONTINUE candidate: except (KeyError, TypeError, ValueError):                 excluded += 1                 continue |
| `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:187` | self._ls_svc.reset_learning_state, self.clear_session_decisions | RAISE / inspect branches: except Exception as exc:             log.error(                 "[StateManager] soft_reset failed (committed=%s): %s",                 committed, exc,             )             if "learning_state" in committed:                 self._rollback_learning_state(rollback_W, rollback_history, rollback_count)             raise ResetError(         |
| `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:257` | self._ls_svc.reset_learning_state, self.delete_session_decisions | RAISE / inspect branches: except Exception as exc:             log.error(                 "[StateManager] hard_reset failed (committed=%s): %s",                 committed, exc,             )             if "learning_state" in committed:                 self._rollback_learning_state(rollback_W, rollback_history, rollback_count)             raise ResetError(         |
| `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:294` | self._ls_svc.get_learning_state, self._ls_svc.save_learning_state | RETURN/CONTINUE candidate: except Exception as rb_exc:             log.error(                 "[StateManager] Learning state rollback failed (state may be inconsistent): %s",                 rb_exc,             ) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_indicator.py:103` | graph_service.run_query, graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning(                 "[THREAT-INDICATOR] upsert failed indicator_value=%r: %s",                 indicator_value, exc,             )             return "" |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_indicator.py:132` | graph_service.run_query, graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning(                 "[THREAT-INDICATOR] link_to_alert failed indicator_value=%r alert=%r: %s",                 indicator_value, alert_id, exc,             ) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_indicator.py:151` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning(                 "[THREAT-INDICATOR] get_indicators_for_alert failed alert=%r: %s",                 alert_id, exc,             )             return [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_indicator.py:187` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[THREAT-INDICATOR] get_all_indicators failed: %s", exc)             indicators = [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_indicator.py:210` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[THREAT-INDICATOR] cleanup_expired failed: %s", exc)             return 0 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/time_machine.py:59` | json.loads | RAISE / inspect branches: except json.JSONDecodeError as exc:             raise SnapshotCorruptError("AGE checkpoint centroid tensor is invalid JSON") from exc |
| `gen-ai-roi-demo-v4-v50/backend/app/services/time_machine.py:98` | payloads.append, _checkpoint_payload | RETURN/CONTINUE candidate: except SnapshotCorruptError as exc:             log.warning("[TIME_MACHINE] Skipping incomplete AGE checkpoint: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/time_machine.py:163` | np.array, compute_snr_report, np.asarray, list, list, list, float | RETURN/CONTINUE candidate: except Exception:         return None |
| `gen-ai-roi-demo-v4-v50/backend/app/services/time_machine.py:394` | compute_iks_v2 | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("[TIME_MACHINE] IKS estimate unavailable: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/triage.py:178` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[TRIAGE] AGE threat-intel query failed for {alert_id}: {exc}")         results = [] |
| `gen-ai-roi-demo-v4-v50/backend/app/services/triage.py:235` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[TRIAGE] alert_type lookup failed for {alert_id}: {exc}") |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:86` | get_variant_history | RETURN/CONTINUE candidate: except Exception as exc:         log.debug("Variant history unavailable for %s: %s", variant_id, exc)         return {"action": "proceed"} |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:242` | graph_client.run_query, soc_decision_where | RETURN/CONTINUE candidate: except Exception as exc:             log.debug("Accuracy trajectory live decision query failed: %s", exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:313` | importlib.import_module | RETURN/CONTINUE candidate: except ImportError:             return None |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:462` | _get_per_category_accuracy_trends | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("Drift threshold detection failed: %s", exc)             return None |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:717` | graph_client.run_query, soc_decision_where, counts.values, counts.items, GraphSignal | RETURN/CONTINUE candidate: except Exception as exc:             log.debug("Coverage gap detection failed: %s", exc)             return None |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:811` | _variant_id, _consult_history, history.get, history.get, rule.generate_variant, history.get, VariantRecord | RETURN/CONTINUE candidate: except Exception as exc:                 log.warning(                     "Evolution rule %s failed: %s",                     getattr(rule, "rule_id", type(rule).__name__),                     exc,                 ) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_registry.py:196` | VariantRecord | RETURN/CONTINUE candidate: except ValueError:         return None |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_registry.py:280` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("Variant registry rebuild query failed for %s: %s", event_type, exc)         return [], str(exc) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/whatif_service.py:143` | np.array, compute_snr_report, np.asarray, list, list, list, float | RETURN/CONTINUE candidate: except Exception:         return None |
| `gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:88` |  | RETURN/CONTINUE candidate: except Exception:             pass |
| `gen-ai-roi-demo-v4-v50/backend/conftest.py:94` | graph_client.run_query | RETURN/CONTINUE candidate: except Exception:             return -1  # AGE unreachable -- sentinel, skip checks |
| `gen-ai-roi-demo-v4-v50/backend/conftest.py:153` | verify_graph | RETURN/CONTINUE candidate: except Exception as exc:             return {"healthy": None, "issues": [str(exc)], "counts": {}} |
| `gen-ai-roi-demo-v4-v50/backend/repro_orphan.py:33` | c.run_query | RETURN/CONTINUE candidate: except Exception as e:             failures += 1             print(f"  [{i}] FAILED: {e}") |
| `s2p-copilot/backend/app/connectors/supplier_intel_provider.py:143` | self._write_cache | RETURN/CONTINUE candidate: except Exception:             cached = self._read_cache(cache_key)             if cached is not None:                 return Provenanced(                     value=cached,                     source="cached",                     provenance_tier=self.provenance_tier,                     fetched_at=time.time(),                 )             |
| `s2p-copilot/backend/app/domains/s2p/evolution/rule_templates.py:36` | float | RETURN/CONTINUE candidate: except (TypeError, ValueError):                 return 0.0 |
| `s2p-copilot/backend/app/domains/s2p/evolution/rule_templates.py:44` | decision.get | RETURN/CONTINUE candidate: except (TypeError, ValueError):         return 0.0 |
| `s2p-copilot/backend/app/domains/s2p/factors.py:438` | factor.compute | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("S2P factor %s failed: %s", factor.name, exc)             value = _fallback(invoice_dict, factor.name, 0.5) |
| `s2p-copilot/backend/app/framework/audit.py:290` | _read_entries, _graph_store, configured.get_all_decisions, configured.get_archived_decisions | RETURN/CONTINUE candidate: except Exception as exc:         # Do not expose backend paths, credentials, queries, or exception messages.         result.update(verified=False, reason="verification_unavailable", error=type(exc).__name__)         return result |
| `s2p-copilot/backend/app/framework/checkpoint.py:86` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[CHECKPOINT] list_checkpoints query failed: %s", exc)             return [] |
| `s2p-copilot/backend/app/framework/checkpoint.py:123` | graph_service.run_query | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[CHECKPOINT] rollback query failed: %s", exc)             return {"error": f"AGE query failed: {exc}"} |
| `s2p-copilot/backend/app/framework/checkpoint.py:137` | json.loads | RETURN/CONTINUE candidate: except Exception as exc:             log.error("[CHECKPOINT] mu restore failed: %s", exc)             return {"error": f"mu restore failed: {exc}"} |
| `s2p-copilot/backend/app/framework/checkpoint.py:147` | json.loads | RETURN/CONTINUE candidate: except Exception as exc:                 log.debug("[CHECKPOINT] counts restore skipped: %s", exc) |
| `s2p-copilot/backend/app/framework/composite_gate.py:119` | DecisionHistoryService.get_category_stats | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[COMPOSITE] category_stats failed: %s", exc)             cat_stats = {"cat_count": 0, "rolling_accuracy": 0.5, "verified_count": 0} |
| `s2p-copilot/backend/app/framework/decision_history.py:51` | graph_service.run_query | RAISE / inspect branches: except Exception as exc:             log.warning("[DECISION-HISTORY] query failed for category=%r: %s", category, exc)             raise |
| `s2p-copilot/backend/app/framework/intervention_controls.py:243` | self.db.run_query | RETURN/CONTINUE candidate: except Exception as exc:                 return {"error": f"AGE query failed: {exc}", "preview": True} |
| `s2p-copilot/backend/app/framework/learning_state.py:99` | history.append | RETURN/CONTINUE candidate: except Exception as exc:             log.warning("[GAE] Skipping malformed history entry: %s", exc) |
| `s2p-copilot/backend/app/framework/learning_state.py:162` | os.fdopen, json.dump, os.replace, log.debug | RAISE / inspect branches: except Exception:         try:             os.unlink(tmp)         except OSError:             pass         raise |
| `s2p-copilot/backend/app/framework/provenance.py:320` | graph_service.run_query | RAISE / inspect branches: except Exception as exc:             log.warning("[PROVENANCE] query failed for decision=%r: %s", decision_id, exc)             raise |
| `s2p-copilot/backend/app/framework/shadow_mode.py:88` | graph_service.run_query | RAISE / inspect branches: except Exception as exc:             log.warning("[SHADOW] get_shadow_report query failed: %s", exc)             raise RuntimeError("Shadow mode report query failed") from exc |
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py:194` | self._age_store | RAISE / inspect branches: except GraphUnavailableError:             query_context = getattr(self.store, "query_context", None)             if not callable(query_context):                 raise GraphUnavailableError("S2P AGE store does not expose directed query support")             context_reader = cast(Callable[..., Any], query_context)             return self._r |
| `s2p-copilot/backend/app/main.py:574` | get_decision | RETURN/CONTINUE candidate: except Exception as exc:             logger.debug("S2P learn connection warmup skipped: %s", exc) |
| `s2p-copilot/backend/app/main.py:586` | get_centroid, fingerprint | RETURN/CONTINUE candidate: except Exception as exc:         logger.debug("S2P learn-path warmup skipped: %s", exc) |
| `s2p-copilot/backend/app/migration/s2p_entity_migration.py:505` | psycopg.connect | RAISE / inspect branches: except Exception as exc:         if "already exists" in str(exc).lower():             return False         raise |
| `s2p-copilot/backend/app/routers/centroid_router.py:22` | service.get_all_centroid_cells | RAISE / inspect branches: except CentroidExplorerError as exc:         raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc |
| `s2p-copilot/backend/app/routers/centroid_router.py:42` | _service(request).explain_decision(decision_id).to_dict, _service(request).explain_decision | RAISE / inspect branches: except CentroidExplorerError as exc:         raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc |
| `s2p-copilot/backend/app/routers/centroid_router.py:50` | _service(request).get_centroid_drift(category, action, limit=limit).to_dict, _service(request).get_centroid_drift | RAISE / inspect branches: except CentroidExplorerError as exc:         raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc |
| `s2p-copilot/backend/app/routers/centroid_router.py:58` | _service(request).get_centroid_cell(category, action).to_dict, _service(request).get_centroid_cell | RAISE / inspect branches: except CentroidExplorerError as exc:         raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc |
| `s2p-copilot/backend/app/routers/financial_router.py:117` | store.get_chain | RETURN/CONTINUE candidate: except TypeError:         rows = store.get_chain() |
| `s2p-copilot/backend/app/routers/financial_router.py:119` | store.get_chain | RAISE / inspect branches: except Exception as exc:         log.exception("Failed to read S2P financial receipts")         raise HTTPException(             status_code=500,             detail="Unable to read financial impact receipts",         ) from exc |
| `s2p-copilot/backend/app/routers/financial_router.py:367` | warm_financial_snapshots, _graph_reader | RAISE / inspect branches: except GraphUnavailableError as exc:             log.exception("Failed to read S2P financial decisions")             raise HTTPException(                 status_code=503,                 detail="S2P graph unavailable for financial impact",             ) from exc |
| `s2p-copilot/backend/app/routers/framework_router.py:169` | _run_graph_query | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="Decision graph unavailable") from exc |
| `s2p-copilot/backend/app/routers/framework_router.py:219` | _run_graph_query | RAISE / inspect branches: except Exception as exc:             raise HTTPException(status_code=503, detail="Decision graph unavailable") from exc |
| `s2p-copilot/backend/app/routers/framework_router.py:229` | _run_graph_query, decisions_per_factor.values | RAISE / inspect branches: except HTTPException:         raise |
| `s2p-copilot/backend/app/routers/framework_router.py:231` | _run_graph_query, decisions_per_factor.values | RETURN/CONTINUE candidate: except RuntimeError:         pass  # not yet initialised — stay with defaults |
| `s2p-copilot/backend/app/routers/framework_router.py:233` | _run_graph_query, decisions_per_factor.values | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[convergence-calendar] state read failed: {exc}") |
| `s2p-copilot/backend/app/routers/framework_router.py:286` | _run_graph_query | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="AGE query failed for OLS status") from exc |
| `s2p-copilot/backend/app/routers/framework_router.py:297` | _run_graph_query | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="AGE query failed for OLS status") from exc |
| `s2p-copilot/backend/app/routers/framework_router.py:310` | _run_graph_query | RETURN/CONTINUE candidate: except Exception as exc:         print(f"[ols-status] warm_start query failed: {exc}") |
| `s2p-copilot/backend/app/routers/framework_router.py:488` | _run_graph_query | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="AGE query failed") from exc |
| `s2p-copilot/backend/app/routers/framework_router.py:534` | _s2p_query_spec, _run_graph_query | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="AGE query failed") from exc |
| `s2p-copilot/backend/app/routers/framework_router.py:602` | _s2p_query_spec, _run_graph_query | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="AGE query failed") from exc |
| `s2p-copilot/backend/app/routers/s2p_audit_export.py:224` | _graph_store | RETURN/CONTINUE candidate: except Exception as exc:         return {             "available": False,             "verification": {                 "verified": False,                 "reason": "verification_unavailable",                 "entries_checked": 0,                 "tamper_evidence": [],                 "error": type(exc).__name__,             },         } |
| `s2p-copilot/backend/app/routers/s2p_audit_export.py:336` | _all_graph_decisions, _graph_reader | RAISE / inspect branches: except GraphUnavailableError as exc:         raise HTTPException(status_code=503, detail="S2P graph unavailable for audit export") from exc |
| `s2p-copilot/backend/app/routers/s2p_autonomy.py:49` | _score_write_governance, _reject_red_write | RAISE / inspect branches: except ValueError as exc:             raise HTTPException(status_code=422, detail=str(exc)) from exc |
| `s2p-copilot/backend/app/routers/s2p_autonomy.py:62` | _score_write_governance, _reject_red_write | RAISE / inspect branches: except ValueError as exc:             raise HTTPException(status_code=422, detail=str(exc)) from exc |
| `s2p-copilot/backend/app/routers/s2p_autonomy.py:75` | _score_write_governance, _reject_red_write | RAISE / inspect branches: except ValueError as exc:             raise HTTPException(status_code=422, detail=str(exc)) from exc |
| `s2p-copilot/backend/app/routers/s2p_demo_beats.py:49` | reader.get_verified_decisions, reader.get_all_decisions | RETURN/CONTINUE candidate: except GraphUnavailableError:         # These are read-only presentation endpoints.  The graph enriches         # them with history, but scorer/config state remains sufficient for a         # truthful day-zero response when AGE is temporarily unavailable.         return [] |
| `s2p-copilot/backend/app/routers/s2p_demo_control.py:45` | json.loads, FIXTURES.read_text | RAISE / inspect branches: except (OSError, ValueError) as exc:         raise HTTPException(status_code=503, detail="S2P demo invoice fixtures unavailable") from exc |
| `s2p-copilot/backend/app/routers/s2p_demo_control.py:146` | selected_twin(manager).get_snapshot, handle.write, manager.conservation.get_state | RAISE / inspect branches: except (OSError, ValueError, RuntimeError, KeyError) as exc:             raise HTTPException(status_code=503, detail="Demo re-freeze unavailable; previous selection retained") from exc |
| `s2p-copilot/backend/app/routers/s2p_demo_control.py:181` | scorer.get_centroid, store.get_centroids, store.save_governance, store.update_centroid, store.get_centroids | RAISE / inspect branches: except Exception as exc:             raise HTTPException(status_code=503, detail="Demo runtime persistence incomplete; do not restart") from exc |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:75` |  | RETURN/CONTINUE candidate: except AttributeError:         graph_store = None |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:206` |  | RETURN/CONTINUE candidate: except Exception:         return {} |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:218` | _graph_verified_counts, _graph_reader(request).get_all_decisions, _graph_reader, _current_conservation_status | RAISE / inspect branches: except GraphUnavailableError:         raise |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:220` | _graph_verified_counts, _graph_reader(request).get_all_decisions, _graph_reader, _current_conservation_status | RETURN/CONTINUE candidate: except Exception:         return {} |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:299` | _graph_linked_decisions, _enrich_decision_invoice_metadata, reader.get_all_decisions, _decision_matches_invoice | RAISE / inspect branches: except GraphUnavailableError as exc:         raise HTTPException(status_code=503, detail="S2P graph unavailable for evidence") from exc |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:350` | get_receipt_store, store.get_chain, store.verify_chain, _conservation_snapshot | RAISE / inspect branches: except GraphUnavailableError as exc:         raise HTTPException(status_code=503, detail="S2P graph unavailable for evidence") from exc |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:372` | _graph_reader | RETURN/CONTINUE candidate: except HTTPException:         reader = None         graph_store = None |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:538` | extinction_history | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="S2P extinction evidence unavailable") from exc |
| `s2p-copilot/backend/app/routers/s2p_explorer.py:195` | _get_graph_reader, reader.count_verified, reader.count_correct, reader.count_verified_decisions, conservation_status | RAISE / inspect branches: except GraphUnavailableError as exc:         raise HTTPException(status_code=503, detail="S2P graph query failed") from exc |
| `s2p-copilot/backend/app/routers/s2p_explorer.py:197` | _get_graph_reader, reader.count_verified, reader.count_correct, reader.count_verified_decisions, conservation_status | RETURN/CONTINUE candidate: except Exception:         return "UNKNOWN" |
| `s2p-copilot/backend/app/routers/s2p_explorer.py:303` | np.asarray, _uniform_ranked, int, values.reshape, np.var(rows, axis=0).tolist, np.var | RETURN/CONTINUE candidate: except Exception:         return _uniform_ranked(factors) |
| `s2p-copilot/backend/app/routers/s2p_explorer.py:454` | _checkpoint_imported_centroids | RAISE / inspect branches: except Exception as exc:         gae_scorer.centroids = previous_centroids         raise HTTPException(             status_code=500,             detail=f"Centroid import checkpoint failed: {exc}",         ) from exc |
| `s2p-copilot/backend/app/routers/s2p_explorer.py:573` | _find_scored_decision | RAISE / inspect branches: except GraphUnavailableError as exc:         raise HTTPException(status_code=503, detail="S2P graph query failed") from exc |
| `s2p-copilot/backend/app/routers/s2p_governance.py:36` | _graph_verified_counts, _s2p_graph_reader(request).get_all_decisions, _s2p_graph_reader, _current_conservation_status | RAISE / inspect branches: except GraphUnavailableError as exc:         raise HTTPException(status_code=503, detail="S2P graph unavailable for governance") from exc |
| `s2p-copilot/backend/app/routers/s2p_governance.py:38` | _graph_verified_counts, _s2p_graph_reader(request).get_all_decisions, _s2p_graph_reader, _current_conservation_status | RETURN/CONTINUE candidate: except Exception:         return {             "state": "UNKNOWN",             "verified_count": 0,             "correct_count": 0,             "total_decisions": 0,         } |
| `s2p-copilot/backend/app/routers/s2p_performance.py:167` | round, float, compute_theta_min | RETURN/CONTINUE candidate: except (TypeError, ValueError):         return 1.0 |
| `s2p-copilot/backend/app/routers/s2p_performance.py:178` | reader.store.get_centroid_checkpoints, _count_verified | RAISE / inspect branches: except GraphUnavailableError as exc:         raise HTTPException(status_code=503, detail="S2P graph unavailable for performance") from exc |
| `s2p-copilot/backend/app/routers/s2p_performance.py:180` | reader.store.get_centroid_checkpoints, _count_verified | RAISE / inspect branches: except Exception as exc:         raise HTTPException(status_code=503, detail="S2P graph unavailable for performance") from exc |
| `s2p-copilot/backend/app/routers/s2p_performance.py:203` | _count_verified, _count_correct | RAISE / inspect branches: except GraphUnavailableError as exc:         raise HTTPException(status_code=503, detail="S2P graph unavailable for performance") from exc |
| `s2p-copilot/backend/app/routers/s2p_performance.py:235` | _graph_reader | RAISE / inspect branches: except GraphUnavailableError as exc:         raise HTTPException(status_code=503, detail="S2P graph unavailable for performance") from exc |
| `s2p-copilot/backend/app/routers/s2p_situation.py:41` | _graph_reader, asyncio.to_thread | RAISE / inspect branches: except GraphUnavailableError as exc:         raise HTTPException(status_code=503, detail="Decision graph unavailable") from exc |
| `s2p-copilot/backend/app/routers/s2p_situation.py:91` | asyncio.to_thread | RETURN/CONTINUE candidate: except asyncio.TimeoutError:         return _degraded_response(             decision_id,             category,             decision,             status="timeout",             reason="Graph traversal exceeded 8s deadline",         ) |
| `s2p-copilot/backend/app/routers/s2p_situation.py:99` | asyncio.to_thread | RAISE / inspect branches: except RuntimeError as exc:         raise HTTPException(status_code=503, detail="Decision graph unavailable") from exc |
| `s2p-copilot/backend/app/routers/s2p.py:97` | store.save_governance | RAISE / inspect branches: except Exception as exc:             raise HTTPException(status_code=503, detail="Audit persistence unavailable") from exc |
| `s2p-copilot/backend/app/routers/s2p.py:104` | store.delete_governance | RAISE / inspect branches: except Exception as exc:             raise HTTPException(status_code=503, detail="Audit persistence unavailable") from exc |
| `s2p-copilot/backend/app/routers/s2p.py:123` | audit.LedgerEntry, audit._append_entry, datetime.now(timezone.utc).isoformat, dict, float, datetime.now | RAISE / inspect branches: except Exception as exc:             raise HTTPException(status_code=503, detail="Decision audit sealing failed") from exc |
| `s2p-copilot/backend/app/routers/s2p.py:151` | audit.OutcomeEntry, audit._read_entries | RAISE / inspect branches: except Exception as exc:             # The caller retains its pending marker on failure. Verification             # must not certify an outcome committed without its sealed entry.             raise HTTPException(status_code=503, detail="Outcome audit sealing failed") from exc |
| `s2p-copilot/backend/app/routers/s2p.py:252` | _graph_store_from_request | RETURN/CONTINUE candidate: except Exception as exc:         logger.exception("Diagnostics failed for s2p")         result = build_diagnostics("s2p", None, None, extras={"error": str(exc)})         return result |
| `s2p-copilot/backend/app/routers/s2p.py:568` | shadow.store.write_governed_decision | RETURN/CONTINUE candidate: except Exception as exc:         _handle_shadow_error(             shadow,             operation="score_shadow",             operation_id=operation_id,             error=exc,             start=start,         )         return |
| `s2p-copilot/backend/app/routers/s2p.py:660` | shadow.store.write_outcome, shadow.store.get_decision, shadow.store.write_outcome | RETURN/CONTINUE candidate: except Exception as exc:         _handle_shadow_error(             shadow,             operation=operation,             operation_id=decision_id,             error=exc,             start=start,         )         return |
| `s2p-copilot/backend/app/routers/s2p.py:831` | compute_conservation_metrics | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("S2P L5 conservation state skipped: %s", exc)         return None |
| `s2p-copilot/backend/app/routers/s2p.py:842` | store.get_conservation_state | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("S2P L5 conservation state read failed: %s", exc)         return None |
| `s2p-copilot/backend/app/routers/s2p.py:866` | store.update_conservation_state | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("S2P L5 conservation state write failed: %s", exc) |
| `s2p-copilot/backend/app/routers/s2p.py:899` | get_centroid | RETURN/CONTINUE candidate: except Exception as exc:         log.debug("S2P L5 centroid persistence skipped: centroid unavailable: %s", exc)         return False |
| `s2p-copilot/backend/app/routers/s2p.py:906` | float | RETURN/CONTINUE candidate: except (TypeError, ValueError):         return False |
| `s2p-copilot/backend/app/routers/s2p.py:921` | store.update_centroid | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("S2P L5 centroid write failed: %s", exc)         return False |
| `s2p-copilot/backend/app/routers/s2p.py:970` | _dk_learning_store_from_request, persist_dk_after_reestimate | RETURN/CONTINUE candidate: except Exception as exc:         log.warning("S2P L5 DK persistence skipped: %s", exc) |
| `s2p-copilot/backend/app/routers/s2p.py:1004` | get_centroid | RETURN/CONTINUE candidate: except Exception as exc:         log.debug("S2P L5 centroid pre-read skipped: %s", exc)         return None |
| `s2p-copilot/backend/app/routers/s2p.py:1011` | float | RETURN/CONTINUE candidate: except (TypeError, ValueError):         return None |
| `s2p-copilot/backend/app/routers/s2p.py:1061` | (reader or S2PGraphReader(store=graph_store)).get_decision_links, S2PGraphReader | RAISE / inspect branches: except GraphUnavailableError:         raise |
| `s2p-copilot/backend/app/routers/s2p.py:1063` | (reader or S2PGraphReader(store=graph_store)).get_decision_links, S2PGraphReader | RETURN/CONTINUE candidate: except Exception:         log.exception("S2P graph invoice link skipped for decision %s", decision_id) |
| `s2p-copilot/backend/app/routers/s2p.py:1081` | reader.get_decision_links | RAISE / inspect branches: except GraphUnavailableError:         raise |
| `s2p-copilot/backend/app/routers/s2p.py:1172` | _graph_store_from_request, _graph_domain, _cached_conservation_counts, compute_conservation_status_payload | RETURN/CONTINUE candidate: except Exception:         log.exception("Unable to evaluate conservation status for auto-approve gate")         return "UNKNOWN" |
| `s2p-copilot/backend/app/routers/s2p.py:1491` | _current_conservation_status, _graph_verified_counts | RETURN/CONTINUE candidate: except Exception:         log.exception("Unable to capture S2P receipt conservation snapshot")         return {"state": "", "verified_count": 0} |
| `s2p-copilot/backend/app/routers/s2p.py:1609` | get_receipt_store, _decision_context, payload.get, _decision_invoice_id, payload.get, (decision or {}).get, _decision_recommended_action | RETURN/CONTINUE candidate: except (TypeError, ValueError, AttributeError) as exc:         log.warning("S2P outcome receipt creation skipped: %s", exc) |
| `s2p-copilot/backend/app/routers/s2p.py:1732` | append | RAISE / inspect branches: except Exception as append_exc:         try:             outbox_id = _enqueue_evidence_receipt_intent(                 graph_store=graph_store,                 receipt_intent_id=receipt_intent_id,                 domain=domain,                 decision_id=decision_id,                 canonical_payload=canonical_payload,                 ac |
| `s2p-copilot/backend/app/routers/s2p.py:1756` | _enqueue_evidence_receipt_intent | RAISE / inspect branches: except Exception as outbox_exc:             log.exception("S2P evidence receipt persistence failed before outcome")             raise HTTPException(                 status_code=503,                 detail="Evidence receipt persistence failed before outcome write",             ) from outbox_exc |
| `s2p-copilot/backend/app/routers/s2p.py:1832` | supplier_profile_accumulator.on_decision_verified, payload.get, _decision_recommended_action | RETURN/CONTINUE candidate: except Exception:         log.exception("Supplier profile accumulator update failed") |
| `s2p-copilot/backend/app/routers/s2p.py:1889` | max, int | RETURN/CONTINUE candidate: except (TypeError, ValueError):         decisions = 0 |
| `s2p-copilot/backend/app/routers/s2p.py:1925` | reader.get_decision | RAISE / inspect branches: except GraphUnavailableError as exc:         raise HTTPException(status_code=503, detail="S2P decision lookup failed") from exc |
| `s2p-copilot/backend/app/routers/s2p.py:1959` | original_link | RETURN/CONTINUE candidate: except Exception:                         log.exception("S2P graph invoice link skipped for decision %s", linked_decision_id) |
| `s2p-copilot/backend/app/routers/s2p.py:1969` | scorer.learn | RAISE / inspect branches: except KeyError as exc:             raise HTTPException(status_code=404, detail=f"Unknown decision: {decision_id}") from exc |
| `s2p-copilot/backend/app/routers/s2p.py:2006` | record_extinction | RAISE / inspect branches: except Exception as exc:                 # Outcome may be committed, but do not claim evidence was                 # recorded. Preserve the pending audit marker for reconciliation.                 raise HTTPException(status_code=503, detail="S2P extinction evidence persistence failed") from exc |
| `s2p-copilot/backend/app/routers/s2p.py:2349` | getattr(scorer, 'get_verified_count') | RETURN/CONTINUE candidate: except (AttributeError, TypeError, ValueError):         try:             prior_verified_count, _ = _graph_verified_counts(http_request)         except Exception:             prior_verified_count = 0 |
| `s2p-copilot/backend/app/routers/s2p.py:2352` | _graph_verified_counts | RETURN/CONTINUE candidate: except Exception:             prior_verified_count = 0 |
| `s2p-copilot/backend/app/routers/s2p.py:2381` | _invoice_decision_metadata | RAISE / inspect branches: except AssertionError as exc:             raise HTTPException(status_code=422, detail=str(exc)) from exc |
| `s2p-copilot/backend/app/routers/s2p.py:2469` | _snapshot_score_centroids | RETURN/CONTINUE candidate: except Exception:             log.exception("S2P score centroid snapshot skipped")             centroid_snapshot = {} |
| `s2p-copilot/backend/app/routers/s2p.py:2493` | _should_auto_approve | RETURN/CONTINUE candidate: except Exception:         log.exception("S2P auto-approve enrichment failed")         auto_approve = None |
| `s2p-copilot/backend/app/routers/s2p.py:2512` | compute_threshold_decision | RETURN/CONTINUE candidate: except Exception:         log.exception("S2P threshold decision enrichment failed")         threshold_decision = None |
| `s2p-copilot/backend/app/routers/s2p.py:2540` | proposal_service.create_from_score, str, float | RETURN/CONTINUE candidate: except Exception:             logger.exception("S2P decision-change proposal creation failed") |
| `s2p-copilot/backend/app/routers/s2p.py:2692` | reader.get_decision | RAISE / inspect branches: except GraphUnavailableError as exc:             raise HTTPException(status_code=503, detail="S2P decision lookup failed") from exc |
| `s2p-copilot/backend/app/routers/s2p.py:2857` | _ensure_outcome_decision | RAISE / inspect branches: except GraphUnavailableError as exc:             raise HTTPException(status_code=503, detail="S2P decision lookup failed") from exc |
| `s2p-copilot/backend/app/routers/s2p.py:2861` | reader.get_decision | RAISE / inspect branches: except GraphUnavailableError as exc:             raise HTTPException(status_code=503, detail="S2P decision lookup failed") from exc |
| `s2p-copilot/backend/app/s2p_graph_status.py:124` | GraphConfig.load | RETURN/CONTINUE candidate: except GraphConfigError:         return False |
| `s2p-copilot/backend/app/s2p_graph_status.py:155` | _load_s2p_graph_config | RAISE / inspect branches: except GraphConfigError as exc:             message = str(exc)             if message.startswith("invalid backend"):                 message = "S2P_ACTIVE_GRAPH_BACKEND must be 'sqlite' or 'age'"             raise S2PActiveGraphConfigError(message) from exc |
| `s2p-copilot/backend/app/s2p_graph_status.py:347` | require_shared_graph | RAISE / inspect branches: except GraphConfigError as exc:         raise S2PActiveGraphConfigError(str(exc)) from exc |
| `s2p-copilot/backend/app/s2p_shadow.py:91` | GraphConfig.load | RAISE / inspect branches: except GraphConfigError as exc:                 raise S2PShadowConfigError(str(exc)) from exc |
| `s2p-copilot/backend/app/services/budget_persistence.py:159` | self._store.get_decision, (decision or {}).get, (decision or {}).get, self._history[-1].update, self._store.save_governance, self._snapshot | RAISE / inspect branches: except Exception:                 self._restore(before)                 raise |
| `s2p-copilot/backend/app/services/centroid_explorer.py:160` | self.graph_store.get_centroid_checkpoints | RETURN/CONTINUE candidate: except Exception:             return DriftResponse(                 category=category,                 action=action,                 supported=False,                 reason="centroid_history_unavailable",                 points=[],             ) |
| `s2p-copilot/backend/app/services/centroid_explorer.py:208` | self.graph_store.read_entity_enrichment | RETURN/CONTINUE candidate: except Exception:             return {} |
| `s2p-copilot/backend/app/services/centroid_explorer.py:475` |  | RETURN/CONTINUE candidate: except (IndexError, TypeError):             return None |
| `s2p-copilot/backend/app/services/optimizer_export.py:151` | _centroids_from_scorer | RETURN/CONTINUE candidate: except Exception:                 return None |
| `s2p-copilot/backend/app/services/s2p_auto_approve_gate.py:407` | active_reader.get_verified_decisions | RETURN/CONTINUE candidate: except GraphUnavailableError as exc:             return [], [f"GraphStore verified-decision read failed: {exc}"] |
| `s2p-copilot/backend/app/services/s2p_context_builder.py:271` | self.graph_store.read_entity_enrichment | RETURN/CONTINUE candidate: except Exception:             return {} |
| `s2p-copilot/backend/app/services/s2p_context_builder.py:390` | get_centroid | RETURN/CONTINUE candidate: except Exception:             result.warnings.append("centroid context unavailable from scorer")             return |
| `s2p-copilot/backend/app/services/s2p_enrichment.py:217` | self.graph_store.read_entity_enrichment | RETURN/CONTINUE candidate: except Exception:             return {} |
| `s2p-copilot/backend/app/services/s2p_enrichment.py:228` | self.graph_store.list_entity_enrichments | RETURN/CONTINUE candidate: except Exception:             return [] |
| `s2p-copilot/backend/app/services/s2p_enrichment.py:301` | self.graph_store.write_entity_enrichment | RETURN/CONTINUE candidate: except NotImplementedError as exc:             receipt = _unsupported_receipt(supplier_id, dry_run=dry_run)             receipt.warnings.append(str(exc))             return receipt |
| `s2p-copilot/backend/app/services/s2p_enrichment.py:305` | self.graph_store.write_entity_enrichment | RETURN/CONTINUE candidate: except Exception as exc:             receipt = _unsupported_receipt(supplier_id, dry_run=dry_run)             receipt.warnings.append(f"entity enrichment write failed: {exc}")             return receipt |
| `s2p-copilot/backend/app/services/s2p_enrichment.py:329` | self.graph_store.write_entity_enrichment | RETURN/CONTINUE candidate: except NotImplementedError:                 pass |
| `s2p-copilot/backend/app/services/s2p_enrichment.py:331` | self.graph_store.write_entity_enrichment | RETURN/CONTINUE candidate: except Exception as exc:                 receipt = _unsupported_receipt(supplier_id, dry_run=True)                 receipt.warnings.append(f"dry-run validation failed: {exc}")                 return receipt |
| `s2p-copilot/backend/app/services/s2p_situation_pattern.py:180` | receipts.extend, store.get_for_invoice | RETURN/CONTINUE candidate: except Exception:             pass |
| `s2p-copilot/backend/app/services/s2p_situation_pattern.py:185` | receipts.extend, store.get_for_decision | RETURN/CONTINUE candidate: except Exception:             pass |
| `s2p-copilot/backend/app/services/situation_traversals.py:548` | graph_store.read_entity_enrichment | RAISE / inspect branches: except Exception as exc:         raise RuntimeError("S2P enrichment lookup failed") from exc |
| `s2p-copilot/backend/app/services/situation_traversals.py:662` | graph_store.query_similar | RAISE / inspect branches: except Exception as exc:             raise RuntimeError("S2P similar-decision graph lookup failed") from exc |
| `s2p-copilot/backend/app/services/supplier_intelligence.py:377` | self.graph_store.read_entity_enrichment | RETURN/CONTINUE candidate: except (AttributeError, NotImplementedError, ValueError):             return {} |

## Appendix D — Additional Memory / JSON-Write Index

This extends the SQLite/fixture scans to explicit InMemory, :memory:, memory-store and JSON/file writes. Ephemeral request objects and export formatting are not persistent memory substitutes. Each OPEN runtime candidate needs caller/provenance review; persistent authority must move to AGE or become an explicit isolated simulation.

| File | All matching lines | Disposition |
|---|---|---|
| `ci-platform/ci_platform/audit/evidence_ledger.py` | 67, 105 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `ci-platform/ci_platform/graph/age_client.py` | 352, 354, 361, 878, 893, 1135 | CONFIRMED family / G009; individual branches may be test/demo/parser-only. |
| `ci-platform/ci_platform/graph/age_graph_store.py` | 115, 761, 762, 865, 866, 868, 972, 973, 974, 979, 1137, 1342, 1343, 1344, 1588, 1589, 1592, 1651, 1652, 1655, 1731, 1735, 1743, 1832, 1836, 1860, 1982, 2007, 2012, 2194, 2286, 2294, 2312, 2320, 2506, 2742, 2851, 2857, 3142, 3143, 3203, 3972, 3973, 3974 | CONFIRMED family / G007, G008, G038, G039, G040, G047; individual branches may be test/demo/parser-only. |
| `ci-platform/scripts/seed_dataops_graph.py` | 126 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/dataops/backend/app/connector_cache.py` | 33, 50 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/app/connectors/dq_benchmark_provider.py` | 218, 219 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/app/context_router.py` | 170 | CONFIRMED family / G012, G034; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/dataops/backend/app/dataops_governance.py` | 44, 92, 114 | CONFIRMED family / G027; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/dataops/backend/app/main.py` | 414, 732, 784 | CONFIRMED family / G024, G026, G027, G043, G047, G048, G051; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/dataops/backend/app/services/graph_enrichment.py` | 83 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/dataops/backend/scripts/evaluate_multihop_stage1.py` | 575, 576 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/dataops/backend/scripts/measure_rho_dataops.py` | 90 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/dataops/backend/scripts/validate_use_cases.py` | 151 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/purchasing/backend/app/data_helpers.py` | 67 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/main.py` | 192 | CONFIRMED family / G013, G024, G026, G033, G048, G050; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/purchasing/backend/app/routers/queue.py` | 197 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/services/audit_export.py` | 41 | CONFIRMED family / G033; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py` | 126, 142, 144 | CONFIRMED family / G013, G028; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/purchasing/backend/app/services/supplier_signal_publisher.py` | 68, 87, 112 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/app/vld_preseed.py` | 39, 40 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/apps/purchasing/backend/cli.py` | 79, 227, 332, 444 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/purchasing/backend/generators/purchasing_synthetic.py` | 449, 450 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/purchasing/backend/scripts/evaluate_multihop_stage1.py` | 666, 667 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/regime_experiment/report.py` | 43, 44, 90 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/s2p_differentiation/engine.py` | 362 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/s2p_differentiation/report.py` | 34, 37, 38 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/trading/backend/app/cli_sdk.py` | 556, 699, 830, 840, 844 | CONFIRMED family / G063; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/app/main.py` | 99, 218, 224, 737 | CONFIRMED family / G023, G024, G026, G031, G048, G049, G058; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/app/routers/data_import.py` | 83, 85 | CONFIRMED family / G030; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/app/routers/journal.py` | 583 | CONFIRMED family / G029; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/app/services/claim_gate.py` | 123, 195 | CONFIRMED family / G020; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/app/services/promotion_state.py` | 105 | CONFIRMED family / G031; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/app/services/promotion.py` | 57 | CONFIRMED family / G031; individual branches may be test/demo/parser-only. |
| `copilot-sdk/apps/trading/backend/cli.py` | 81, 94, 267, 747, 776, 993, 1203 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/trading/backend/generators/trading_synthetic.py` | 152, 153 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/trading/backend/scripts/evaluate_multihop_stage1.py` | 644, 645 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/apps/trading/scripts/volatility_walkthrough.py` | 48, 178 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/copilot_sdk/atomic_json.py` | 21 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/backend/evolution_router.py` | 14, 71 | CONFIRMED family / G023; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py` | 131 | CONFIRMED family / G003; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py` | 902 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/backend/signal_store.py` | 28, 32, 33, 84 | CONFIRMED family / G026; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py` | 484 | CONFIRMED family / G005, G021, G044; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/demo/bundle.py` | 160, 330 | CONFIRMED family / G058; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/demo/connector_freeze.py` | 70 | DEMO/REFERENCE — local simulation/artifact path; see G057–G059. |
| `copilot-sdk/copilot_sdk/demo/preseed.py` | 14, 79, 217, 350, 351 | CONFIRMED family / G023, G057; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/demo/startup.py` | 15 | DEMO/REFERENCE — local simulation/artifact path; see G057–G059. |
| `copilot-sdk/copilot_sdk/di/claude_parser.py` | 73 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/di/enrichment.py` | 326 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/diagnostics/platform_dump.py` | 196 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/enterprise/roi.py` | 77 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/evidence/gate.py` | 123 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/evolution/__init__.py` | 15, 30, 53, 54 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/evolution/evolver.py` | 11, 35 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/evolution/graph_store.py` | 13, 33, 38, 186, 188, 343 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/evolution/ledger.py` | 16 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py` | 13, 68 | CONFIRMED family / G045; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/evolution/variant_store.py` | 64, 81, 194, 264 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/framework/audit.py` | 13 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/framework/checkpoint.py` | 71, 72, 74 | CONFIRMED family / G010; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/framework/intervention_controls.py` | 357 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/framework/learning_state.py` | 156 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/generators/archetype.py` | 313 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/graph/__init__.py` | 4, 20 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py` | 113 | IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045). |
| `copilot-sdk/copilot_sdk/graph/factory.py` | 77 | CONFIRMED family / G042; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/graph/memory_store.py` | 1, 318, 327, 374, 485 | IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045). |
| `copilot-sdk/copilot_sdk/graph/outbox.py` | 67 | IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045). |
| `copilot-sdk/copilot_sdk/graph/protocol.py` | 265 | CONFIRMED family / G047; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py` | 48, 363, 373, 413, 417, 2322, 2571, 2648, 2654 | IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045). |
| `copilot-sdk/copilot_sdk/migrate/__main__.py` | 83, 107 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py` | 207 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py` | 321, 685, 1087 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/copilot_sdk/outbox/cli.py` | 135 | IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045). |
| `copilot-sdk/copilot_sdk/outbox/store.py` | 58 | IMPLEMENTATION — local/migration storage; must not be authoritative production memory (G002/G042/G045). |
| `copilot-sdk/copilot_sdk/outcome/ledger.py` | 17, 19, 59 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/pilot/models.py` | 46, 65 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/pilot/transfer.py` | 49, 213, 240, 253 | CONFIRMED family / G045; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/promotion/core.py` | 113, 157 | CONFIRMED family / G045; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/regime/experiment.py` | 313 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/rl/outcome_receipt.py` | 44 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/scaffold/generator.py` | 114 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/scoring/investigation.py` | 361 | CONFIRMED family / G024, G025; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py` | 160, 216 | CONFIRMED family / G002, G055; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py` | 78, 288, 290, 302, 306, 309, 313, 1491, 1689, 2005, 2093, 2560, 2570 | CONFIRMED family / G001, G002, G003, G004, G006, G042, G044, G055; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/state/tab_state_cache.py` | 501, 503 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/transfer/registry.py` | 179, 180 | CONFIRMED family / G045; individual branches may be test/demo/parser-only. |
| `copilot-sdk/copilot_sdk/twin/models.py` | 25 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/twin/service.py` | 11, 22 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/copilot_sdk/twin/store.py` | 95 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `copilot-sdk/demo.py` | 467, 589, 1518, 1556 | CONFIRMED family / G054, G057, G063; individual branches may be test/demo/parser-only. |
| `copilot-sdk/e2e/fix_health_retry.py` | 91 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/e2e/fix_playwright_failures.py` | 41 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/examples/build_your_own/report.py` | 27, 54 | DEMO/REFERENCE — local simulation/artifact path; see G057–G059. |
| `copilot-sdk/examples/conservation_demo/conservation_demo.py` | 50 | DEMO/REFERENCE — local simulation/artifact path; see G057–G059. |
| `copilot-sdk/examples/jm_reference/report.py` | 32, 33 | DEMO/REFERENCE — local simulation/artifact path; see G057–G059. |
| `copilot-sdk/integrity/benchmark_fixture.py` | 20, 72, 144, 145 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/integrity/commercial_smoke.py` | 15, 32 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/analyze_factor0_panel.py` | 324 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/backfill_jm_edges.py` | 155, 156, 158 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/backfill_snapshot_after.py` | 29 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/benchmark_age_latency.py` | 31, 295 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/budget_accuracy_frontier.py` | 48, 209, 308, 397 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/build_result_manifest.py` | 376 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/c9_live_age_smoke.py` | 483, 495, 648 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/d1_recursion_trace_v1.py` | 42, 70, 97, 181, 182 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/demo_cross_copilot_finding.py` | 24, 41 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/design_drift_backend_probe.py` | 75, 76, 129, 130 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/design_drift_inventory.py` | 65, 66 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/discovery_demo.py` | 25, 26 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/evolve_demo.py` | 15, 19 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/external_baseline_full.py` | 77 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/gap1_adaptive_halting.py` | 248, 338 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/gap2_abstention_curve.py` | 317 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/gap2_abstention_heldout_v1.py` | 157, 163 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_d1_d2_paper_figures_v1.py` | 78, 267, 359, 360 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_group_a_d_charts.py` | 239 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_group_b_c_charts.py` | 211, 215, 220, 224, 274 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_rv_charts.py` | 211 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_rv4_ke45_charts.py` | 223 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/generate_tab_state_types.py` | 158 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/hero_moments.py` | 62, 346 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/jm_v27_live_validation.py` | 336, 337 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/k_learning_conservation_interaction.py` | 35, 212 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/k_learning_curve_cross_copilot.py` | 97, 113, 420, 526 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/k_learning_curve_experiment.py` | 51, 68, 368 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/k_learning_curve_extended.py` | 54, 71, 347 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/k_learning_distribution_sensitivity.py` | 32, 188 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/loom_gauntlet.py` | 156, 160, 266 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/multitenant_demo.py` | 6, 11 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/mutable_flow_probe.py` | 29, 46, 69 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase_cycle_gate.py` | 28 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase3_cycle_gate_v3.py` | 73 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py` | 41 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase6_claim_proof.py` | 235 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/plant_remaining_fixtures.py` | 87, 88 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/preseed_all_copilots.py` | 200 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/preseed_demo_fixtures.py` | 70, 106, 250, 253 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/preseed_verification_gap.py` | 92, 97 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/q_term_ablation_normalized.py` | 275, 336 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/q_term_ablation.py` | 248, 313 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/qualify_for_pilot.py` | 42 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py` | 68, 161 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/regenerate_demo_bundles.py` | 149, 259, 261, 263, 418, 422 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/ri1_routing_k_interaction.py` | 146, 408 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/ri5_rich_k_state.py` | 264, 269, 281, 375 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/routing_variant_bandit.py` | 306 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/routing_variant_gru_ablation.py` | 361 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/routing_variant_risk_sensitive.py` | 39, 260 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/run_exp_regime.py` | 26, 28 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/sc_endpoint_probe.py` | 50, 54 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/scan_forbidden_patterns.py` | 21, 36, 168, 198 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/seed_604k_scenario.py` | 111, 227, 230 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/shadow_live_test.py` | 130 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/tab_inventory.py` | 527, 537, 556, 814, 818 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/trigger_warm_start.py` | 186, 199 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/validate_age_migration.py` | 268, 271 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/validate_age_unification.py` | 139, 144, 188, 217 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/verify_factor0_values.py` | 240 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/verify_l5_completion.py` | 442, 448, 465, 485 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/verify_di3.py` | 13, 50 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/analyze_cypher_compat.py` | 246 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/celonis.py` | 99 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/crowdstrike_mock.py` | 38 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/greynoise.py` | 48 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/mitre_client.py` | 69 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py` | 44, 360 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/sap.py` | 101 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/threat_intel_provider.py` | 130, 131 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py` | 64, 223 | CONFIRMED family / G017, G040; individual branches may be test/demo/parser-only. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py` | 22 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/audit.py` | 13 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/checkpoint.py` | 63, 64 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py` | 357 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/learning_state.py` | 156 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py` | 68, 70 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py` | 298 | CONFIRMED family / G024, G048, G053; individual branches may be test/demo/parser-only. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py` | 155 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/simulation.py` | 24 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py` | 4092 | CONFIRMED family / G016, G017, G041; individual branches may be test/demo/parser-only. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py` | 373, 1125, 1126, 1799, 2867 | CONFIRMED family / G017, G018, G041; individual branches may be test/demo/parser-only. |
| `gen-ai-roi-demo-v4-v50/backend/app/seed/metadata.py` | 14 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py` | 130 | CONFIRMED family / G045; individual branches may be test/demo/parser-only. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/bootstrap_neo4j.py` | 12, 139 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py` | 413 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evidence_room.py` | 281 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py` | 24, 107 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py` | 91, 277, 690, 800, 801, 908 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py` | 40 | CONFIRMED family / G046; individual branches may be test/demo/parser-only. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py` | 96, 169 | CONFIRMED family / G018; individual branches may be test/demo/parser-only. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py` | 109 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/demo_showcase_alerts.py` | 64 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/diagnose_value_chain.py` | 308 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/evaluate_multihop_stage1.py` | 587, 588 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/exp_g1_reconvergence.py` | 393 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/expand_demo_alerts.py` | 189 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/generate_score_keyed_alerts.py` | 58, 59, 80 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/generate_seed.py` | 71 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/measure_rho.py` | 315 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/seed_multihop_graph.py` | 61 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/sprint/sprint_lib.py` | 29 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/value_chain_experiment_lib.py` | 43 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/verify_rollback_readiness.py` | 131, 133 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/write_mu_zero_sidecar.py` | 74 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/frontend/fix_recharts_key.py` | 20, 38 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/frontend/fix_soc_playwright.py` | 24 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/frontend/fix_soc_pw_final.py` | 28 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/frontend/fix_soc_pw_round2.py` | 32, 56 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/collect_tab_content.py` | 120 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/diagnose_soc_diag_prefix.py` | 149 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/perf/soc_perf_02_readonly_http.py` | 142, 201, 264 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/perf/soc_perf_03_phase3_commit_spike.py` | 48 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/perf/soc_perf_common.py` | 185, 189 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/perf/soc_perf_trace_summary.py` | 350, 351 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/perf/soc_perf_trace.py` | 126 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/run_soc_diag_f.py` | 317, 1114, 1334, 1335 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/run_soc_route_validation.py` | 350, 581, 842, 1063, 1337, 1347 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/preseed_demo_scenarios.py` | 48, 86, 514, 543 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/soc_c9b_live_age_smoke.py` | 419, 426, 427 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/soc_c9b_seed_alerts.py` | 393 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/validate_contracts.py` | 61, 63, 76 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `s2p-copilot/backend/app/connectors/supplier_intel_provider.py` | 162, 163 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/framework/checkpoint.py` | 62, 63 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/framework/intervention_controls.py` | 516 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/framework/learning_state.py` | 156 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/main.py` | 222, 223 | CONFIRMED family / G024, G048, G052; individual branches may be test/demo/parser-only. |
| `s2p-copilot/backend/app/models/outcome_receipt.py` | 105 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/s2p_demo_control.py` | 142 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/routers/s2p_preview.py` | 281, 284 | CONFIRMED family / G036; individual branches may be test/demo/parser-only. |
| `s2p-copilot/backend/app/routers/s2p.py` | 141, 1619 | CONFIRMED family / G015; individual branches may be test/demo/parser-only. |
| `s2p-copilot/backend/app/services/compliance_screener.py` | 94 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/services/optimizer_export.py` | 77 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/services/proposal_service.py` | 44, 149, 193, 194, 195, 199, 200, 206 | CONFIRMED family / G045; individual branches may be test/demo/parser-only. |
| `s2p-copilot/backend/app/services/receipt_store.py` | 1 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/app/vld_preseed.py` | 37 | OPEN runtime candidate — trace callers/profile and whether this supplies authoritative memory; do not clear by filename or comment. |
| `s2p-copilot/backend/demo/s2p_demo.py` | 221 | DEMO/REFERENCE — local simulation/artifact path; see G057–G059. |
| `s2p-copilot/backend/scripts/evaluate_multihop_stage1.py` | 530, 531 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `s2p-copilot/backend/scripts/scan_forbidden_patterns.py` | 91, 92, 126 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `s2p-copilot/backend/scripts/verify_s2p_domain_isolation.py` | 100, 107 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `s2p-copilot/generators/generate_5k_invoices.py` | 172, 173, 182 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `s2p-copilot/generators/s2p_synthetic.py` | 422 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `s2p-copilot/scripts/conservation_s2p.py` | 31, 187 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `s2p-copilot/scripts/preseed_s2p_demo.py` | 47, 479, 481 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |

## Appendix E — Every Direct Driver Import

Driver use belongs in the AGE implementation boundary. Migration, offline diagnostics and launcher preflight are not production copilot Decision queries, but must still resolve/verify their destination (G063). Imports alone cannot discover raw-client calls through injected objects; the SOC bypass is independently traced in G041.

| Import site | Source | Classification |
|---|---|---|
| `ci-platform/ci_platform/graph/age_client.py:40` | import psycopg  # sync only — no AsyncConnection anywhere | IMPLEMENTATION — legitimate AGE driver boundary. |
| `ci-platform/ci_platform/graph/age_graph_store.py:20` | import psycopg | IMPLEMENTATION — legitimate AGE driver boundary. |
| `copilot-sdk/copilot_sdk/migrate/scratch_graph.py:9` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:23` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/copilot_sdk/migrate/verify_state.py:11` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/demo.py:331` | import psycopg | Launcher preflight, not Decision CRUD; G054/G063. |
| `copilot-sdk/scripts/age_catalog_diag.py:6` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/age_catalog_fix.py:7` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/age_catalog_test.py:5` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/age_complete_inventory.py:14` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/age_migration_benchmark.py:17` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/age_pf_blockers.py:8` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/age_pf_investigate.py:9` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/age_preflight.py:10` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/age_v35_review_checks.py:10` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/backfill_d_correct.py:24` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/backfill_jm_edges.py:17` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/backfill_soc_status.py:16` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/benchmark_age_latency.py:58` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/check_deleted_labels.py:2` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/create_age_indexes_v2.py:8` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/create_age_indexes.py:8` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/d2_v_diagnostic.py:7` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/graph_census_v2.py:8` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/graph_census.py:9` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase_age_check.py:13` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase_reset.py:4` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase_verify.py:4` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase1_backfill.py:18` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase1_cleanup.py:13` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase1_graph_cleanup_v2.py:9` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase1_graph_cleanup.py:10` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase3_cycle_gate_v3.py:26` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase3_dual_write_e2e_v2.py:110` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase3_dual_write_e2e_v4.py:11` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase3_dual_write_e2e_v5.py:8` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase3_flip_verify_v2.py:12` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase3_reset_v3.py:9` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase3_verify_v2.py:3` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/phase3_verify_v3.py:6` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/validate_age_migration.py:86` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `copilot-sdk/scripts/verify_l5_completion.py:112` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:120` | import psycopg | G046 — legacy raw-DSN runtime API, normal typed path uses GraphStore. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:156` | import psycopg | G046 — legacy raw-DSN runtime API, normal typed path uses GraphStore. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:184` | import psycopg | G046 — legacy raw-DSN runtime API, normal typed path uses GraphStore. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:208` | import psycopg | G046 — legacy raw-DSN runtime API, normal typed path uses GraphStore. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:221` | import psycopg | G046 — legacy raw-DSN runtime API, normal typed path uses GraphStore. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/b0_v_reconciliation.py:39` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:17` | import psycopg2 | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/v_soc_31a_real_check.py:7` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/v_soc_37_investigation.py:7` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/v_soc_canonical_scan.py:7` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/v_soc_diagnostic.py:7` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/backend/scripts/verify_rollback_readiness.py:64` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/check_correct.py:1` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/check_orphans.py:1` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scratch/temp/runner_debug_20260610_154609/copilot-sdk/demo.py:136` | import psycopg | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/scratch/temp/step0_connection_tax_spike.py:7` | import psycopg | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `gen-ai-roi-demo-v4-v50/scripts/check_neo4j.py:9` | from neo4j import GraphDatabase | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/scripts/diagnostics/perf/soc_perf_03_phase3_commit_spike.py:24` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |
| `gen-ai-roi-demo-v4-v50/support/setup/setup_notebook_v4.py:1343` | from neo4j import GraphDatabase | ARCHIVED/SUPPORT — not the inspected app import root; retain only as non-runtime material. |
| `s2p-copilot/backend/app/migration/s2p_entity_migration.py:493` | import psycopg | OPERATOR/EXPERIMENT — standalone tooling, not automatically imported app code; audit destination/config before execution. |

## Appendix F — Domain-Query Candidates and False-Positive Controls

The literal-query scan retained 52 candidates missing an inline domain token. Many are safe because a helper such as soc_decision_where, _d2_where, a domain-bearing props map or a separately constructed WHERE clause supplies the filter. The confirmed holes are G040. Do not infer that every row below is unscoped; no candidate is silently dropped.

| Candidate | Query fragment | Required disposition |
|---|---|---|
| `copilot-sdk/copilot_sdk/di/nl_query.py:132` | MATCH (s:Source)-[:EMITS]->(d:Decision) RETURN s, d | OPEN until complete helper/call-site scope is established. |
| `copilot-sdk/copilot_sdk/di/nl_query.py:133` | MATCH (d:Decision) WHERE d.data_freshness IS NOT NULL RETURN d | OPEN until complete helper/call-site scope is established. |
| `copilot-sdk/copilot_sdk/di/nl_query.py:134` | MATCH (d:Decision) WHERE d.recurrence_frequency IS NOT NULL RETURN d | OPEN until complete helper/call-site scope is established. |
| `copilot-sdk/copilot_sdk/di/nl_query.py:135` | MATCH (d:Decision)-[:AFFECTS]->(s:System) RETURN d, s | OPEN until complete helper/call-site scope is established. |
| `copilot-sdk/copilot_sdk/di/nl_query.py:136` | MATCH (d:Decision) RETURN d | OPEN until complete helper/call-site scope is established. |
| `copilot-sdk/copilot_sdk/graph/projection.py:277` | f"MATCH (d:Decision) WHERE {self._d2_where()} RETURN count(DISTINCT d.decision_id) AS cnt" | Templates/helper-injected predicates; render(domain=None) remains an API candidate (G040). |
| `copilot-sdk/copilot_sdk/graph/projection.py:296` | "MATCH (d:Decision) "             f"WHERE {self._d2_where()} "             "OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o:Outcome) "             f"RETURN d, o ORDER BY d.created_at LIMIT {limit}" | Templates/helper-injected predicates; render(domain=None) remains an API candidate (G040). |
| `copilot-sdk/copilot_sdk/graph/projection.py:39` | MATCH (d:Decision) WHERE <d2> RETURN d | Templates/helper-injected predicates; render(domain=None) remains an API candidate (G040). |
| `copilot-sdk/copilot_sdk/graph/projection.py:44` | MATCH (d:Decision) OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o:Outcome) RETURN d, o | Templates/helper-injected predicates; render(domain=None) remains an API candidate (G040). |
| `copilot-sdk/copilot_sdk/graph/projection.py:49` | MATCH (d:Decision) WHERE d.factor_vector IS NOT NULL RETURN d | Templates/helper-injected predicates; render(domain=None) remains an API candidate (G040). |
| `copilot-sdk/copilot_sdk/graph/projection.py:54` | MATCH (d:Decision) WHERE <d2> RETURN count(DISTINCT d.decision_id) | Templates/helper-injected predicates; render(domain=None) remains an API candidate (G040). |
| `copilot-sdk/copilot_sdk/graph/projection.py:59` | MATCH (d:Decision) WHERE <d2-correct> RETURN count(DISTINCT d.decision_id) | Templates/helper-injected predicates; render(domain=None) remains an API candidate (G040). |
| `copilot-sdk/copilot_sdk/graph/projection.py:64` | MATCH (d:Decision) WHERE <d2> RETURN d.category, count(d) | Templates/helper-injected predicates; render(domain=None) remains an API candidate (G040). |
| `copilot-sdk/copilot_sdk/graph/projection.py:83` | MATCH (d:Decision) | Templates/helper-injected predicates; render(domain=None) remains an API candidate (G040). |
| `copilot-sdk/copilot_sdk/graph/projection.py:84` | f"MATCH (d:Decision) WHERE {predicate}", | Templates/helper-injected predicates; render(domain=None) remains an API candidate (G040). |
| `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:219` | MATCH (d:Decision {origin: ' | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:490` | MATCH (target:Decision {decision_id: $decision_id})-[:DECIDED_ON]->(target_alert:Alert)-[:MEMBER_OF]->(campaign:Campaign) OPTIONAL MATCH (campaign)-[:CONTINUES]->(next_campaign:Campaign) OPTIONAL MATCH (previous_campaign:Campaign)-[:CONTINU | CONFIRMED G040: target and related Decision aliases lack domain in this query. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:520` | MATCH (d:Decision)                 WHERE | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1043` | MATCH (d:Decision)             WHERE | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1140` | MATCH (d:Decision {decision_id: $decision_id})             WHERE | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1232` | MATCH (d:Decision {decision_id: $decision_id})-[:DECIDED_ON]->(a:Alert)             -[:HAS_INDICATOR]->(ti:ThreatIndicator)             WHERE | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2079` | MATCH (d:Decision)             WHERE | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3352` | MATCH (d:Decision)             WHERE | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:192` | MATCH (d:Decision)         WHERE | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:202` | MATCH (d:Decision)         WHERE | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:325` | MATCH (a:Alert) WITH count(a) AS alerts             OPTIONAL MATCH (d:Decision)             WHERE | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:364` | MATCH (a:Alert) WITH count(a) AS alerts             OPTIONAL MATCH (d:Decision)             WHERE | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:187` | MATCH (n)-[r]-() WHERE NOT n:Decision AND NOT n:Checkpoint RETURN n.id AS id, head(labels(n)) AS type,coalesce(n.name, n.hostname, n.id) AS display_name, count(r) AS connections ORDER BY connections DESC LIMIT $limit | OPEN until complete helper/call-site scope is established. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:260` | MATCH (d:Decision)             WHERE | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:610` | f"""             MATCH (d:Decision)             WHERE {_soc_where}               AND {_soc_verified_predicate("d")}             RETURN d.category AS category,                    count(d) AS verified,                    sum(CASE WHEN d.corre | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:965` | f"""             MATCH (d:Decision)             WHERE {_soc_where}               AND d.source_id IS NOT NULL AND d.verified_by IS NOT NULL             WITH d.verified_by AS analyst,                  count(d) AS total,                  sum(C | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:1051` | f"""             MATCH (d:Decision)             WHERE {_soc_where}               AND d.timestamp_epoch >= {last_7d_start} AND d.timestamp_epoch < {now_ms}             RETURN               count(d) AS total,               count(CASE WHEN {_s | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:1069` | f"""             MATCH (d:Decision)             WHERE {_soc_where}               AND d.timestamp_epoch >= {prior_7d_start} AND d.timestamp_epoch < {last_7d_start}             RETURN               count(d) AS total,               count(CASE  | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:111` | CREATE (d:DecisionDistanceLog {     decision_id:                     $decision_id,     centroid_distance_to_canonical:  $distance,     pattern_history_value:           $ph_value,     alert_category_distribution:     $cat_dist,     logged_at | Auxiliary label, not necessarily a Decision query; still inspect identity/link domain. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:130` | MATCH (d:DecisionDistanceLog) RETURN d.decision_id                    AS decision_id,        d.centroid_distance_to_canonical AS centroid_distance_to_canonical,        d.pattern_history_value          AS pattern_history_value,        d.aler | Auxiliary label, not necessarily a Decision query; still inspect identity/link domain. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:86` | f"MATCH (d:Decision) {filter_clause} "             f"RETURN count(CASE WHEN d.origin = '{self.PERSISTENT_ORIGIN}' "             f"THEN 1 ELSE null END) AS n" | OPEN until complete helper/call-site scope is established. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:97` | f"MATCH (d:Decision) {filter_clause} RETURN count(d) AS n" | OPEN until complete helper/call-site scope is established. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:105` | f"MATCH (d:Decision) {self.PERSISTENT_FILTER} "             "REMOVE d.correct, d.outcome "             "RETURN count(d) AS cleared" | OPEN until complete helper/call-site scope is established. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:129` | f"MATCH (d:Decision) {self.PERSISTENT_FILTER} "             "OPTIONAL MATCH (d)-[:HAD_CONTEXT]->(ctx:DecisionContext) "             "DETACH DELETE d, ctx" | OPEN until complete helper/call-site scope is established. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:229` | MATCH (d:Decision)                 WHERE | Often concatenated/helper domain predicate; inspect complete expression, not this fragment. |
| `ci-platform/ci_platform/graph/age_client.py:1142` | MATCH (d:DecisionDistanceLog {decision_id: $did})             SET d.centroid_distance_to_canonical = $dist,                 d.pattern_history_value          = $phv,                 d.alert_category_distribution    = $acd,                 d. | Auxiliary label, not necessarily a Decision query; still inspect identity/link domain. |
| `ci-platform/ci_platform/graph/age_client.py:959` | MATCH (ctx:DecisionContext {context_id: $ctx_id})                 SET ctx.decision_id = $did,                     ctx.created_at  = $ts                 RETURN ctx | Auxiliary label, not necessarily a Decision query; still inspect identity/link domain. |
| `ci-platform/ci_platform/graph/age_client.py:1155` | CREATE (d:DecisionDistanceLog {                     decision_id:                    $did,                     centroid_distance_to_canonical: $dist,                     pattern_history_value:          $phv,                     alert_categor | Auxiliary label, not necessarily a Decision query; still inspect identity/link domain. |
| `ci-platform/ci_platform/graph/age_client.py:969` | CREATE (ctx:DecisionContext {                         context_id:  $ctx_id,                         decision_id: $did,                         created_at:  $ts                     })                     RETURN ctx | Auxiliary label, not necessarily a Decision query; still inspect identity/link domain. |
| `ci-platform/ci_platform/graph/age_graph_store.py:777` | entity_query = f"""             MATCH (e {{entity_id: {self._S(entity_id)}}})             WITH e LIMIT 1             CREATE (d:Decision {props})             CREATE (d)-[:DECIDED_ON]->(e)             RETURN d             """ | Inspect props/where builder; entity_id-only anchor and traversal issues confirmed separately in G007/G040. |
| `ci-platform/ci_platform/graph/age_graph_store.py:984` | self._run_query(f"CREATE (d:Decision {props}) RETURN d") | Inspect props/where builder; entity_id-only anchor and traversal issues confirmed separately in G007/G040. |
| `ci-platform/ci_platform/graph/age_graph_store.py:2623` | f"""             MATCH (d:Decision)             {where_clause}             RETURN d             ORDER BY d.created_at, d.decision_id             LIMIT {limit_value}             """ | Inspect props/where builder; entity_id-only anchor and traversal issues confirmed separately in G007/G040. |
| `ci-platform/ci_platform/graph/age_graph_store.py:3269` | f"""             MATCH (d:Decision)-[r]->(e)             {where_relationship}             RETURN d.decision_id AS decision_id,                    e.entity_id AS entity_id,                    type(r) AS edge_type,                    r.create | Inspect props/where builder; entity_id-only anchor and traversal issues confirmed separately in G007/G040. |
| `ci-platform/ci_platform/graph/age_graph_store.py:3285` | f"""             MATCH (l:DecisionEntityLink)             MATCH (d:Decision {{decision_id: l.decision_id}})             {where_link}             RETURN l             {limit_clause}             """ | Auxiliary label, not necessarily a Decision query; still inspect identity/link domain. |
| `ci-platform/ci_platform/graph/age_graph_store.py:775` | self._run_query(f"CREATE (d:Decision {props}) RETURN d") | Inspect props/where builder; entity_id-only anchor and traversal issues confirmed separately in G007/G040. |
| `ci-platform/ci_platform/graph/age_graph_store.py:3248` | self._run_query(f"CREATE (l:DecisionEntityLink {props}) RETURN l") | Auxiliary label, not necessarily a Decision query; still inspect identity/link domain. |
| `ci-platform/ci_platform/graph/age_graph_store.py:786` | self._run_query(f"CREATE (d:Decision {props}) RETURN d") | Inspect props/where builder; entity_id-only anchor and traversal issues confirmed separately in G007/G040. |

## Handoff / Audit Limitations

The source defects and explicit missing capabilities in G001–G066 are actionable without mutating the environment. Remaining OPEN inventory candidates are deliberately retained under the user's “if unsure, list it” rule. They need bounded call-site/availability verification during remediation; this report does not certify them safe. No historical E2E failure was causally reproduced, no live data was exported, and no credentials are included. No source/spec/backend file was modified and no git command was used.
