# JM Implementation Review — Part 1A

Review date: 2026-07-31  
Scope: shared infrastructure, SOC, S2P, and the three stated blockers  
Method: review-only; source code is authoritative; every conclusion below has file:line evidence.

## §1 EXECUTIVE SUMMARY

| Item | Result |
|---|---|
| Blocker A — SOC scorer store | **CLOSED** — `init_learning_state()` creates the store through the factory and injects it into the SOC adapter; the adapter rejects a missing store. Evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:208-221`; `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py:18-28`. |
| Blocker B — S2P dual graph | **OPEN** — the legacy Aura client is disabled and the runtime score/outcome path is governed, but the application still exposes a SQLite enrichment primary and a separate shadow AGE graph. Evidence: `s2p-copilot/backend/app/main.py:172-183`; `s2p-copilot/backend/app/s2p_shadow.py:117-126,223-250`. |
| Blocker C — factory/scorer defaults | **CLOSED** — no implicit factory backend, AGE/dual-write missing DSNs raise, and production `from_preset()` requires an injected store. Evidence: `copilot-sdk/copilot_sdk/graph/factory.py:27-38,205-210,260-262`; `copilot-sdk/copilot_sdk/scoring/scorer.py:238-260`. |
| Original P1 findings (shared infra + SOC + S2P) | **12 → 1 remaining PARTIAL**. The remaining item is the dormant legacy S2P Decision reader in `domains/s2p/graph.py`; it has no runtime application caller in the traced search. Evidence: `s2p-copilot/backend/app/domains/s2p/graph.py:50-71`; `s2p-copilot/backend/tests/test_s2p_graph.py:15,58-60`. |
| Original P2 findings (shared infra + SOC + S2P) | **15 → 6 remaining PARTIAL/GAP**. Residuals are projection direct-client construction, SOC seed direct-client construction, S2P SQLite enrichment, separate shadow graph configuration, mixed situation context, and JSON Decision-shaped seed input. Evidence: sections §5–§7. |

The review does not accept comments or design text as implementation evidence. The authoritative contract itself says AGE failures must raise, GraphConfig must own graph configuration, Decision reads must be scoped, and Decision writes must stamp a domain (`copilot-sdk/docs/design/age_unification_gaps_v1.md:28-43`).

## §2 BLOCKER A: SOC SCORER

### `gae_state.py`

**CONFORMANT for P1-SOC-1.** `init_learning_state()` loads the typed SOC `GraphConfig`, calls `create_graph_store(...)`, and passes the resulting `graph_store` to `SOCCompoundingScorerAdapter`; it does not omit the store (`gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:208-221`). The factory’s AGE return is `AGEGraphStoreAdapter` (`copilot-sdk/copilot_sdk/graph/factory.py:260-285`).

**CONFORMANT for P1-SOC-2.** The scorer construction resolves backend, DSN, graph, and authorization from `GraphConfig` (`gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:208-215`). The separate L5 learning-store helper also uses `GraphConfig.load("soc")` and `graph_config.dsn` (`gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:156-175`), although that helper still returns `None` after configuration/adapter failures (`:177-183`).

### `scorer_adapter.py`

**CONFORMANT for P1-SOC-1.** The adapter requires a non-`None` store and passes it to `CompoundingScorer.from_preset(..., graph_store=graph_store)` (`gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py:18-28`). If no store is injected, construction raises `TypeError`; there is no production default store.

`InMemoryGraphStore` references remaining in this file: **1**, at `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py:22`. It is only part of the explicit test-use error message; it is not imported or constructed.

**CONFORMANT.** `capture_existing_state()` delegates to the compound scorer (`gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py:117-123`).

**Blocker A status: CLOSED.**  
SOC scorer store class: `AGEGraphStoreAdapter`, constructed through `create_graph_store` at `copilot-sdk/copilot_sdk/graph/factory.py:278-285` and injected at `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:208-221`.  
SOC DSN resolution: `GraphConfig.load("soc")` at `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:208`, with DSN passed at `:212`.  
InMemoryGraphStore references remaining: **1**, `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py:22`.

## §3 BLOCKER B: S2P DUAL GRAPH

### `db/neo4j.py`

**CONFORMANT for P1-S2P-1, P1-S2P-2, and P1-S2P-4.** The file is retained only as a compatibility sentinel. Its constructor raises and it creates no global client, reads no Neo4j environment variables, and contains no Decision write/count functions (`s2p-copilot/backend/app/db/neo4j.py:1-16`).

`neo4j.py` Decision functions: **retired**. There are no active write or count functions in the file (`s2p-copilot/backend/app/db/neo4j.py:10-16`).

### `domains/s2p/graph.py`

**PARTIAL for P1-S2P-5.** The old module still contains `get_s2p_decision(driver, decision_id)` and uses a caller-supplied Neo4j driver/session (`s2p-copilot/backend/app/domains/s2p/graph.py:15-47,50-71`). Its query now includes `WHERE d.domain = 's2p'` (`:52-55`), but the function is not a GraphStore operation. The traced application search found only the test import/use (`s2p-copilot/backend/tests/test_s2p_graph.py:15,58-60`); no router/service caller was found.

`s2p/graph.py` Decision functions: **one legacy read remains; writes are retired; runtime callers are retired**. Evidence: `s2p-copilot/backend/app/domains/s2p/graph.py:50-71`; `s2p-copilot/backend/tests/test_s2p_graph.py:15,58-60`.

### `routers/s2p.py`

**CONFORMANT for P1-S2P-3 core score writes.** The score path calls the configured scorer (`s2p-copilot/backend/app/routers/s2p.py:1920-1926`), then links the decision through `scorer.graph_store`/`S2PGraphReader` (`:1981-1986`). It no longer writes score traces through direct Neo4j.

**CONFORMANT for P1-S2P-3 outcome writes.** Both `/learn` and `/outcome` use the configured scorer’s learning path (`s2p-copilot/backend/app/routers/s2p.py:2083-2112`; `:2198-2232`). The shadow write is separate and explicitly non-authoritative; its failure handling records a failed diagnostic and only raises in strict mode (`s2p-copilot/backend/app/routers/s2p.py:303-322,428-450`). The core scorer write is not wrapped in the former direct-write/bare-swallow pattern.

Score traces today: **GraphStore/scorer path**, not direct Neo4j (`s2p-copilot/backend/app/routers/s2p.py:1920-1926`).  
Outcome traces today: **GraphStore/scorer path** (`s2p-copilot/backend/app/routers/s2p.py:2083-2112,2227-2232`).  
Exceptions still swallowed for the core trace writes: **NO**; non-core invoice-link and shadow side effects remain best-effort (`s2p-copilot/backend/app/routers/s2p.py:798-823`; `:303-322`).

### `similar_cases_base.py`

**CONFORMANT for P1-S2P-6.** The base class defaults to `domain="s2p"`, rejects a domain mismatch against the reader, and obtains rows through the domain-bound `S2PGraphReader` (`s2p-copilot/backend/app/framework/similar_cases_base.py:61-80`).

### `framework_router.py`

**6/6 original framework Decision-read groups are scoped.** Evidence for each requested group:

1. Centroid history: `WHERE d.domain = $domain`, with `domain=s2p` passed (`s2p-copilot/backend/app/routers/framework_router.py:113-130`). **CONFORMANT.**
2. Decision counts by factor: `WHERE d.domain = $domain` (`s2p-copilot/backend/app/routers/framework_router.py:183-190`). **CONFORMANT.**
3. OLS score history: `WHERE d.domain = $domain` (`s2p-copilot/backend/app/routers/framework_router.py:256-260`). **CONFORMANT.**
4. OLS override counts: `WHERE d.domain = $domain` (`s2p-copilot/backend/app/routers/framework_router.py:267-271`). **CONFORMANT.**
5. Evolution and latest Decision reads: both use `d.domain = $domain` (`s2p-copilot/backend/app/routers/framework_router.py:320-324,339-343`). **CONFORMANT.**
6. Auto-approve counts: `WHERE d.domain = $domain` (`s2p-copilot/backend/app/routers/framework_router.py:548-557`). **CONFORMANT.**

The adjacent `LearningState` query is not a Decision query and has no domain predicate (`s2p-copilot/backend/app/routers/framework_router.py:276-285`). It is a residual unpartitioned state read, but it does not reduce the six Decision-read count above.

**CONFORMANT for P1-S2P-7.** Caller-supplied Cypher was replaced by a closed `QUERY_REGISTRY`; the endpoint accepts only a `query_name` and rejects unknown names (`s2p-copilot/backend/app/routers/framework_router.py:37-50,589-605`). The explorer is **restricted**, not open arbitrary Cypher.

### `main.py`

**CONFORMANT for P2-S2P-1.** Runtime profile selection is explicit and production is the default (`s2p-copilot/backend/app/main.py:92-99`). `build_s2p_scorer()` loads `GraphConfig`, creates the configured store, and injects it into `CompoundingScorer.from_preset()` (`:101-139`).

**GAP for P2-S2P-2.** The application intentionally extracts the SQLite `primary` from the active store for enrichment and can replace `app.state.graph_store` with that primary (`s2p-copilot/backend/app/main.py:172-183`). The same file documents that enrichment remains SQLite-owned during the split-read migration (`:172-178`). This is an active non-authoritative path, not a unified AGE path.

### `s2p_shadow.py`

**GAP for P2-S2P-3 and a blocker residual.** Production shadow configuration uses `GraphConfig` when legacy overrides are absent (`s2p-copilot/backend/app/s2p_shadow.py:74-95`), and the factory is shared (`:223-235`), but shadow still requires a separate DSN/graph concept and explicitly forbids targeting `soc_graph` (`:117-129`). It therefore remains a separate AGE graph rather than the shared authoritative graph.

### `s2p_situation.py`

**PARTIAL for P2-S2P-6.** The route asserts `domain="s2p"` in the normalized intent (`s2p-copilot/backend/app/routers/s2p_situation.py:56-69`) and rejects a foreign-domain decision (`:141-145`). However, it merges decision metadata/local values into the intent payload before traversal (`:49-72`), so the route is not a universal graph-only/domain-asserted context path.

### `seed_graph.py`

**PARTIAL for P2-S2P-7.** Seed input remains JSON/local-file based: `_load_json()` loads invoices, suppliers, and process data and falls back to deterministic process data (`s2p-copilot/backend/app/seed_graph.py:43-65`). Decision-shaped seed nodes are still produced, but now stamp `domain="s2p"` (`:206-220`). Operational seeding requires an explicit graph and refuses `soc_graph` unless explicitly authorized (`:116-135`).

### `supplier_profile_accumulator.py`

**CONFORMANT for P2-S2P-8 isolation requirement; local fixtures remain by design.** The module explicitly declares that supplier events are local operational data and must never be used as a Decision-store substitute (`s2p-copilot/backend/app/services/supplier_profile_accumulator.py:1-5`). It still loads fixture JSON (`:69-103`) and the process-wide accumulator is initialized with the default fixture path (`:403-405,523`), so this is not a graph-backed profile store; the required separation is explicit.

**Blocker B status: OPEN.** The old direct Neo4j Decision system is retired, but the SQLite enrichment primary and separate shadow graph remain active non-unified paths (`s2p-copilot/backend/app/main.py:172-183`; `s2p-copilot/backend/app/s2p_shadow.py:117-129`).

neo4j.py Decision functions: **retired**.  
s2p/graph.py Decision functions: **legacy read remains; runtime-retired**.  
Framework router scoped: **6/6 original Decision-read groups**; adjacent `LearningState` read remains unscoped (`s2p-copilot/backend/app/routers/framework_router.py:276-285`).  
Cypher explorer: **restricted** (`s2p-copilot/backend/app/routers/framework_router.py:589-605`).  
Remaining S2P non-unified paths in this review: **6**, listed at `s2p-copilot/backend/app/main.py:172-183`; `s2p-copilot/backend/app/s2p_shadow.py:74-129`; `s2p-copilot/backend/app/domains/s2p/graph.py:50-71`; `s2p-copilot/backend/app/routers/framework_router.py:276-285`; `s2p-copilot/backend/app/routers/s2p_situation.py:49-72`; `s2p-copilot/backend/app/seed_graph.py:43-65,206-220`.

## §4 BLOCKER C: FACTORY/SCORER DEFAULTS

### `factory.py`

**CONFORMANT for P1-INFRA-1.** There is no SQLite default backend. `_normalize_backend()` rejects a missing backend (`copilot-sdk/copilot_sdk/graph/factory.py:27-38`); config-driven construction loads `GraphConfig` (`:145-166`). SQLite is selected only when the resolved/explicit backend is `sqlite` (`:177-192`).

**CONFORMANT for P1-INFRA-2.** `dual_write` constructs the SQLite primary only after selecting that explicit backend, then requires a nonblank AGE DSN and raises `GraphConfigError` after closing the primary when absent (`copilot-sdk/copilot_sdk/graph/factory.py:194-210`). It no longer silently returns the primary. AGE with a missing DSN raises `ValueError` (`:257-262`).

Factory default backend: **none; missing is rejected**, `copilot-sdk/copilot_sdk/graph/factory.py:27-32`.  
AGE + missing DSN: **raises**, `copilot-sdk/copilot_sdk/graph/factory.py:260-262`.  
DualWriteStore silent degradation: **no**, missing DSN raises before return, `copilot-sdk/copilot_sdk/graph/factory.py:205-255`.

### `scorer.py`

**CONFORMANT for P1-INFRA-3.** `from_preset()` raises in production when no store is injected (`copilot-sdk/copilot_sdk/scoring/scorer.py:238-242`). Test profile uses `InMemoryGraphStore`, development profile uses explicit SQLite, and production rejects both store classes (`:243-260`).

Without a store: **production raises; test uses explicit in-memory profile; development uses explicit SQLite** (`copilot-sdk/copilot_sdk/scoring/scorer.py:238-260`). It does not silently create SQLite in production.

### `age_client.py`

**CONFORMANT for P2-INFRA-1 and P2-INFRA-2.** The client requires explicit DSN and graph arguments and raises when either is missing (`ci-platform/ci_platform/graph/age_client.py:113-126`). The singleton factory also requires explicit `dsn` and `graph_name`; its documentation identifies GraphConfig as the caller-side resolver (`ci-platform/ci_platform/graph/age_client.py:1163-1178`). No localhost/default DSN resolution exists in the reviewed path.

AGE client DSN source: **caller-supplied after GraphConfig resolution, not raw env fallback**, `ci-platform/ci_platform/graph/age_client.py:21-23,104-107,113-126,1163-1178`.

### `projection.py`

**PARTIAL for P2-INFRA-3.** `AGEProjection` uses `GraphConfig.load(domain)` when DSN/graph are absent (`copilot-sdk/copilot_sdk/graph/projection.py:224-239`), but it directly constructs `AGEClient` instead of using the common graph factory (`:227-239`). It is read-only and rejects mutation verbs (`:241-244`), but it remains a separate client-construction path.

**Blocker C status: CLOSED.** The requested outputs are: factory default backend **none** (`copilot-sdk/copilot_sdk/graph/factory.py:27-38`); AGE+missing DSN **raises** (`:257-262`); `from_preset()` without store **raises in production** (`copilot-sdk/copilot_sdk/scoring/scorer.py:238-242`); AGE client DSN **caller-supplied from GraphConfig-owned configuration** (`ci-platform/ci_platform/graph/age_client.py:21-23,1163-1178`).

## §5 SOC P2 FINDINGS

| Finding | File:Line | Original issue | Current status | Evidence |
|---|---|---|---|---|
| P2-SOC-1 | `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:36-52,73-88,94-108,114-124` | `POSTERIOR_DSN` localhost fallback and suppressed psycopg mutation failures | **CONFORMANT** | `POSTERIOR_DSN` is test-only; production/test configuration comes from `GraphConfig.load("soc", profile=...)`, missing DSN raises, and save/load/clear re-raise `RuntimeError` (`:36-52,54-88,90-108,114-124`). Direct psycopg remains the intentional relational posterior implementation (`:73-86`). |
| P2-SOC-2 | `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:557-587` | In-memory RL priors fallback | **CONFORMANT** | Outside test mode, PosteriorStore creation/load failure raises; only explicit pytest mode sets the store to `None` and uses in-memory priors (`:562-587`). |
| P2-SOC-3 | `gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py:28-56` | Legacy Neo4j driver active for `GRAPH_BACKEND=neo4j` | **CONFORMANT** | `GraphConfig` is loaded, `neo4j` selection raises a retired-backend error, non-AGE backends raise, and only the AGE factory is constructed (`:28-56`). |
| P2-SOC-4 | `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/graph_schema.py` (missing); replacement `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:210-224` | Direct AGE factory plus environment mutation | **PARTIAL** | The originally referenced file no longer exists. The active replacement resolves `GraphConfig`, validates AGE/DSN, and calls `get_graph_client` directly (`:210-224`). The direct client construction remains outside the shared factory; the requested path’s original environment-mutation implementation is not present. |

## §6 S2P P2 FINDINGS

| Finding | File:Line | Original issue | Current status | Evidence |
|---|---|---|---|---|
| P2-S2P-1 | `s2p-copilot/backend/app/main.py:92-139` | Raw backend/scorer construction | **CONFORMANT** | Profile selection is explicit; scorer construction loads `GraphConfig`, creates the selected store, and injects it into `from_preset()` (`:92-139`). |
| P2-S2P-2 | `s2p-copilot/backend/app/main.py:172-183` | SQLite enrichment split | **GAP** | Enrichment is intentionally assigned the SQLite primary and may replace `app.state.graph_store` with it (`:172-183`). |
| P2-S2P-3 | `s2p-copilot/backend/app/s2p_shadow.py:74-129,223-250` | Separate S2P AGE DSN/factory | **GAP** | Production may use GraphConfig, but shadow still requires a separate graph and rejects `soc_graph` (`:74-129`); it constructs a separate AGE store when enabled (`:223-250`). |
| P2-S2P-4 | `s2p-copilot/backend/app/db/neo4j.py:1-16` | Evolution/Decision-link writes in legacy Neo4j module | **CONFORMANT** | The module has no evolution or Decision-link functions and the sentinel constructor raises (`:1-16`). |
| P2-S2P-5 | `s2p-copilot/backend/app/framework/similar_cases_base.py:63-109`; `s2p-copilot/backend/app/routers/framework_router.py:144-145,195-196,262-274,363-367` | Graph errors converted to empty/default output | **CONFORMANT for graph query failures** | Similar-case reads are domain-bound (`similar_cases_base.py:63-80`); framework graph failures raise HTTP 503 in the reviewed query paths (`framework_router.py:144-145,195-196,262-274,363-367`). Intentional cold-start/default display behavior remains separately documented (`framework_router.py:164-174,201-218`). |
| P2-S2P-6 | `s2p-copilot/backend/app/routers/s2p_situation.py:49-72,120-145` | Mixed graph-store/local metadata without universal assertion | **PARTIAL** | The route asserts S2P in the intent and rejects foreign Decision domains (`:56-69,141-145`), but combines local Decision metadata with graph traversal input (`:49-72`). |
| P2-S2P-7 | `s2p-copilot/backend/app/seed_graph.py:43-65,116-135,206-220` | JSON Decision-shaped seed substitution | **PARTIAL** | JSON/local fallback data remains (`:43-65`), while seed target validation and explicit `domain="s2p"` are now present (`:116-135,206-220`). |
| P2-S2P-8 | `s2p-copilot/backend/app/services/supplier_profile_accumulator.py:1-5,69-103,403-405,523` | Local event/fixture files | **CONFORMANT for isolation; not AGE-backed** | The module explicitly forbids treating local supplier data as a Decision-store substitute (`:1-5`), but it still loads fixture JSON and initializes from a fixture path (`:69-103,403-405,523`). |

## §7 SHARED INFRA P2 FINDINGS

| Finding | File:Line | Original issue | Current status | Evidence |
|---|---|---|---|---|
| P2-INFRA-1 | `ci-platform/ci_platform/graph/age_client.py:21-23,113-126` | Raw env DSN and localhost fallback | **CONFORMANT** | The client requires explicit DSN/graph and documents caller-side GraphConfig resolution (`:21-23,113-126`). |
| P2-INFRA-2 | `ci-platform/ci_platform/graph/age_client.py:1158-1191` | Singleton raw DSN/graph resolution | **CONFORMANT** | The singleton accepts explicit `dsn` and `graph_name`, constructs the client with those values, and only checks configuration mismatch (`:1163-1191`). |
| P2-INFRA-3 | `copilot-sdk/copilot_sdk/graph/projection.py:224-244` | Read-only AGE bypasses factory | **PARTIAL** | Projection resolves absent values through `GraphConfig`, but directly constructs `AGEClient` (`:227-239`); read-only enforcement is present (`:241-244`). |

## §8 REMAINING GAPS

1. **P1 / high — dormant S2P legacy reader.** `get_s2p_decision()` still accepts a Neo4j driver, even though it is domain-filtered and only test-referenced in the traced search (`s2p-copilot/backend/app/domains/s2p/graph.py:50-71`; `s2p-copilot/backend/tests/test_s2p_graph.py:15,58-60`). Risk: future callers can reintroduce the second graph API.

2. **P1 / high — blocker B remains open from active split paths.** Enrichment can be pointed at SQLite primary (`s2p-copilot/backend/app/main.py:172-183`) and enabled shadow state can target a separate AGE graph (`s2p-copilot/backend/app/s2p_shadow.py:117-129,223-250`). Risk: one user operation can observe different stores and cannot prove one-graph traversal.

3. **P2 / medium — projection direct client.** `AGEProjection` bypasses the common factory while remaining read-only (`copilot-sdk/copilot_sdk/graph/projection.py:224-244`). Risk: factory authorization and lifecycle policy can diverge from projection reads.

4. **P2 / medium — SOC seed direct client.** The active seed replacement calls `get_graph_client` directly after GraphConfig validation (`gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:210-224`). Risk: direct construction remains an alternate AGE lifecycle/configuration path.

5. **P2 / medium — mixed S2P situation context.** The route merges local metadata with graph-derived context even though it asserts the S2P intent and rejects foreign Decision domains (`s2p-copilot/backend/app/routers/s2p_situation.py:49-72,141-145`). Risk: local context can influence a response without a graph-domain provenance assertion.

6. **P2 / medium — JSON Decision-shaped seed data.** Seed data still originates from local JSON/fallback inputs, although the target graph is guarded and Decision nodes carry `domain="s2p"` (`s2p-copilot/backend/app/seed_graph.py:43-65,116-135,206-220`). Risk: fixture-derived Decisions can be mistaken for live learned data unless operational seed boundaries remain enforced.

## §9 READING LOG

| File | Read range |
|---|---:|
| `copilot-sdk/docs/design/age_unification_gaps_v1.md` | 1-817 |
| `copilot-sdk/CLAUDE.md` | 1-139 |
| `gen-ai-roi-demo-v4-v50/CLAUDE.md` | 1-250 |
| `s2p-copilot/CLAUDE.md` | 1-75 |
| `copilot-sdk/graphify-out/GRAPH_REPORT.md` | 1-610 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py` | 1-1113 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py` | 1-123 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py` | 1-165 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py` | 1-613 |
| `gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py` | 1-56 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/graph_schema.py` | **missing** |
| `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py` (active replacement) | 1-888 |
| `s2p-copilot/backend/app/db/neo4j.py` | 1-16 |
| `s2p-copilot/backend/app/domains/s2p/graph.py` | 1-71 |
| `s2p-copilot/backend/app/routers/s2p.py` | 1-2351 |
| `s2p-copilot/backend/app/framework/similar_cases_base.py` | 1-174 |
| `s2p-copilot/backend/app/routers/framework_router.py` | 1-819 |
| `s2p-copilot/backend/app/main.py` | 1-291 |
| `s2p-copilot/backend/app/s2p_shadow.py` | 1-261 |
| `s2p-copilot/backend/app/routers/s2p_situation.py` | 1-225 |
| `s2p-copilot/backend/app/seed_graph.py` | 1-363 |
| `s2p-copilot/backend/app/services/supplier_profile_accumulator.py` | 1-523 |
| `copilot-sdk/copilot_sdk/graph/factory.py` | 1-285 |
| `copilot-sdk/copilot_sdk/scoring/scorer.py` | 1-2157 |
| `ci-platform/ci_platform/graph/age_client.py` | 1-1191 |
| `copilot-sdk/copilot_sdk/graph/projection.py` | 1-320 |

READY: YES
