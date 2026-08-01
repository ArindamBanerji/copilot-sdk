# JM Implementation Review — Part 1: Infrastructure and Blockers

Review type: read-only adversarial review  
Scope: Design Goals 1–3 and Systemic Blockers A–C  
Date: 2026-07-31

## §1 Executive Summary

| Area | Verdict | Summary |
|---|---|---|
| Goal 1 — Decision access through GraphStore/AGE | **GAP** | The principal scorer paths use AGE-backed GraphStores, but direct AGE Decision reads remain in SOC and S2P auxiliary paths, S2P retains a callable legacy Neo4j graph module, and Trading/DataOps retain helpers that explicitly convert AGE to SQLite. |
| Goal 2 — GraphConfig for DSN/graph resolution | **PARTIAL** | Production startup paths generally resolve typed configuration through `GraphConfig`; test/development overrides and legacy helper paths remain, and some callers construct AGE clients directly after receiving config values. |
| Goal 3 — No silent substitution | **GAP** | Trading and DataOps explicitly downgrade a resolved AGE backend to SQLite. DataOps also has fixture fallback behavior outside an explicitly required AGE configuration. Dual-write secondary failure is logged/outboxed but remains best effort. |

| Blocker | Status | Evidence summary |
|---|---|---|
| A — SOC scorer uses InMemoryGraphStore | **CLOSED** | `init_learning_state()` creates a configured store and injects it into `SOCCompoundingScorerAdapter`; the adapter rejects a missing store. `gae_state.py:208-221`; `scorer_adapter.py:18-29`. |
| B — S2P has two graph systems | **OPEN** | The legacy client is disabled, but `app/domains/s2p/graph.py` remains a callable Neo4j/S2PDecision path and the framework router directly queries AGE outside GraphStore. `s2p/graph.py:50-71`; `framework_router.py:27-32,548-559`. |
| C — Factory/Scorer SQLite defaults | **OPEN** | Production `from_preset()` rejects a missing injected store, but development and test profiles still create SQLite/InMemory stores, while Trading/DataOps app helpers explicitly turn AGE into SQLite. `scorer.py:238-261`; Trading `main.py:120-129`; DataOps `main.py:103-114`. |

Finding totals: **11 P1**, **10 P2**, **3 P3**. Severity reflects production Decision-path risk first; retained compatibility and non-Decision paths are lower severity.

## §2 Goal 1: Decision Read/Write Through GraphStore/AGE

### Shared infrastructure

| File | Original finding | Current line | Status | Evidence |
|---|---|---:|---|---|
| `copilot_sdk/graph/factory.py` | P1-INFRA-1: SQLite default | 27-38, 147-166 | **CONFORMANT for production resolution** | Missing backend/domain now raises `GraphConfigError`; config-driven production resolution uses `GraphConfig.load()`, and an expected AGE backend resolving to SQLite raises at `162-164`. |
| `copilot_sdk/graph/factory.py` | P1-INFRA-2: silent DualWrite fallback | 194-255 | **PARTIAL** | Dual-write requires an AGE DSN and constructs both stores. However, `DualWriteStore` is explicitly primary-authoritative and secondary-best-effort (`copilot_sdk/graph/dual_write_store.py:34-42`); secondary exceptions are caught, recorded, and the primary result is returned (`dual_write_store.py:280-290`). |
| `copilot_sdk/scoring/scorer.py` | P1-INFRA-3: `from_preset()` creates SQLite | 238-261 | **CONFORMANT for production; PARTIAL overall** | Production with no injected store raises at `238-242`; test uses InMemory at `243-246`; development uses SQLite at `247-252`. The compatibility fallback remains available outside production. |
| `ci_platform/graph/age_client.py` | P2-INFRA-1/2: raw DSN and singleton | 113-140, 1163-1190 | **CONFORMANT for caller resolution** | `AGEClient` requires explicit `dsn` and `graph_name` and does not resolve them from environment (`121-126`). The singleton receives explicit values and detects configuration mismatch (`1176-1189`). It is still a direct AGE client rather than a GraphStore. |
| `copilot_sdk/graph/projection.py` | P2-INFRA-3: read-only AGE bypass | 224-244 | **GAP** | The projection resolves DSN/graph through `GraphConfig` when absent (`230-235`) but constructs `AGEClient` directly (`239`) and queries it directly (`241-244`), bypassing the GraphStore protocol. |

### SOC

| File | Original finding | Current line | Status | Evidence |
|---|---|---:|---|---|
| `app/services/gae_state.py` | P1-SOC-1: scorer without graph store | 204-221 | **CONFORMANT** | `GraphConfig.load("soc")` is used and passed to `create_graph_store()` (`208-214`); the resulting store is injected into `SOCCompoundingScorerAdapter` (`221`). Dual-write is explicitly rejected for SOC reads (`216-220`). |
| `app/domains/soc/scorer_adapter.py` | P1-SOC-1: InMemory default | 18-29, 117-123 | **CONFORMANT** | The adapter requires a store and constructs `CompoundingScorer` with it (`18-29`). Its state-capture method delegates to the compound scorer (`121-123`). InMemory is permitted only when explicitly supplied by tests, per the error text at `20-23`. |
| `app/services/posterior_store.py` | P2-SOC-1: direct PostgreSQL posterior store | 28-52, 73-88 | **CONFORMANT for Goal 1 scope; PARTIAL for unified persistence** | This is an RL posterior table, not Decision data (`1-5`). Production DSN resolution uses `GraphConfig.load("soc")` (`46-52`); direct `psycopg` writes are used for that relational artifact (`73-85`). |
| `app/services/rl_engine.py` | P2-SOC-2: in-memory RL fallback | 557-588 | **CONFORMANT in production; PARTIAL in test mode** | Production exceptions raise at `568-570` and `578-580`; only test mode creates an in-memory `ExplorationPolicy` with no posterior store (`570-587`). |
| `app/db/neo4j.py` | P2-SOC-3: legacy Neo4j driver | 1-5, 28-54 | **PARTIAL** | The module states that Neo4j was removed (`1-5`) and resolves GraphConfig (`28-43`), but still exposes a variable named `neo4j_client` backed by `get_graph_client()` (`45-54`). It is an AGE client, not a GraphStore, and SOC startup/auxiliary code still calls it directly (`app/main.py:176-203`). |
| `app/graph_schema.py` | P2-SOC-4: direct AGE factory | 210-224 | **GAP** | Schema verification/seeding loads GraphConfig and requires AGE (`212-220`) but constructs and returns a direct AGE client (`223-224`) rather than a GraphStore. |
| `app/main.py` | Direct SOC Decision reads | 176-237 | **GAP** | Startup directly calls `neo4j_client.run_query()` for node count and Decision counts (`202-205`, `229-237`). The client is AGE-backed, but these Decision reads bypass the GraphStore protocol. |

### S2P

| File | Original finding | Current line | Status | Evidence |
|---|---|---:|---|---|
| `app/db/neo4j.py` | P1-S2P-1: independent Neo4j client | 1-16 | **CONFORMANT** | The module is a disabled sentinel; construction raises and no client or Neo4j environment is read (`1-16`). |
| `app/domains/s2p/graph.py` | P1-S2P-2/5: S2PDecision Neo4j path | 1-71 | **GAP** | The module remains callable and documents/writes a Neo4j `S2PDecision` path (`1-5`); `get_s2p_decision()` executes a caller-supplied driver session (`15-47`, `50-71`). Repository search found only tests importing it, not the main router, so it is a retained but still available legacy path. |
| `app/routers/s2p.py` | P1-S2P-3: direct Neo4j trace write | 1981-1985 | **CONFORMANT for this path** | The observed path links the decision through `scorer.graph_store` and `S2PGraphReader`; it does not call the disabled Neo4j client. Governed Decision persistence is explicitly guarded by `ProtocolV2GraphStore` and calls `write_governed_decision()` (`s2p.py:1641-1663`). |
| `app/framework/similar_cases_base.py` | P1-S2P-6: unscoped similar-case reads | 63-109 | **CONFORMANT** | The method requires the requested domain to equal `graph_reader.domain` (`78-80`) and reads through `S2PGraphReader.get_verified_decisions()` (`80`). |
| `app/routers/framework_router.py` | P1-S2P-6: unscoped framework reads | 37-50, 112-145, 181-196, 548-559 | **PARTIAL** | Registered Decision queries include `d.domain = $domain` (`37-48`), and endpoint queries do too (`115-129`, `185-190`, `550-556`). However, the router obtains a direct `AGEClient` from GraphConfig (`27-32`) rather than using GraphStore, so protocol unification is incomplete. |
| `app/routers/framework_router.py` | P1-S2P-7: arbitrary Cypher explorer | 589-605 | **CONFORMANT for query restriction; GAP for protocol** | Callers select only a registry key and cannot supply Cypher or parameters (`589-600`); execution is still direct AGE client access (`602-605`). |
| `app/main.py` | P2-S2P-1/2: startup construction and SQLite enrichment | 101-141, 160-193 | **PARTIAL** | Main resolves S2P GraphConfig and creates the configured store (`115-126`), then injects it into the scorer (`134-139`). In dual-write mode, enrichment is deliberately pointed to the SQLite primary (`172-183`), while scorer writes use the dual-write store. This is not the canonical Decision scorer path, but it remains a second persistence path. |
| `app/s2p_shadow.py` | P2-S2P-3: separate DSN/factory | 67-129, 223-235 | **PARTIAL** | Production shadow configuration loads GraphConfig (`82-89`) and creates an AGE store (`226-234`), but it is explicitly a separate optional shadow graph (`123-129`), not the canonical scorer store. Legacy `S2P_AGE_*` values are accepted only under test (`76-80`). |

### Trading

| File | Original finding | Current line | Status | Evidence |
|---|---|---:|---|---|
| `apps/trading/backend/app/main.py` | P1-TRD-1: AGE→SQLite downgrade | 116-137 | **GAP** | `_graph_store()` loads the configured backend (`120`) and then unconditionally changes `age` to `sqlite` (`127-129`). The fallback store is therefore SQLite even when GraphConfig reports AGE. |
| `apps/trading/backend/app/graph_status.py` | P1-TRD-2: rejects dual_write | 320-362 | **CONFORMANT** | The active factory accepts both `age` and `dual_write` (`325`), validates configuration (`329`), creates the configured store (`347-357`), and wraps it as an active AGE store (`358-362`). Product/shared-graph restrictions are explicit at `338-341`. |
| `apps/trading/backend/app/cli_sdk.py` | P1-TRD-3: local SQLite scorer bypass | 120-140 | **CONFORMANT** | CLI resolves typed config (`125-126`), creates the store through `create_graph_store()` with the resolved backend/DSN/graph (`127-137`), and injects it into `from_preset()` (`138-140`). |
| `apps/trading/backend/app/services/regime_classifier.py` | P1-TRD-4: retry without domain | 139-144 | **CONFORMANT** | Verified decisions are requested with `self._domain` (`143`); a non-callable reader returns an empty result rather than retrying unscoped (`140-144`). |

### Purchasing

| File | Original finding | Current line | Status | Evidence |
|---|---|---:|---|---|
| `apps/purchasing/backend/app/main.py` | P1-PUR-1: raw backend resolution | 145-164, 414-443 | **CONFORMANT for production startup** | The generic helper resolves the backend through `GraphConfig.load(DOMAIN)` (`148-155`) and passes it to `create_graph_store()` (`156-162`). `create_app()` creates the active configured store and injects it through `FreshScorerProxy` (`416-443`). Test-only config errors may select SQLite at `151-154`. |

### DataOps

| File | Original finding | Current line | Status | Evidence |
|---|---|---:|---|---|
| `apps/dataops/backend/app/context_router.py` | P1-DOPS-1: JSON fixture Decision metadata | 94-107, 431-437, 960-987, 1032-1063 | **PARTIAL** | Normal Decision summaries call the GraphStore-backed `_graph_decisions()` (`431-434`, `94-103`). JSON/demo decisions are substituted only when explicit demo/test mode is enabled (`106-107`, `433-437`). Other context endpoints still read local JSON fixtures, so the router is not uniformly graph-backed. |
| `apps/dataops/backend/app/graph_queries.py` | P1-DOPS-2: fixture fallback on AGE failure | 100-139, 550-564 | **PARTIAL** | If AGE is required, missing connection raises (`550-554`) and query errors re-raise (`560-564`). If AGE is not required, `_run_graph()` returns `None` and callers use fixture results, e.g. `get_system()` (`200-215`) and `compute_downstream_urgency()` (`518-527`). This is explicit offline mode, but it is still substitution when configuration is incomplete. |
| `apps/dataops/backend/app/main.py` | AGE→SQLite downgrade helper | 103-120 | **GAP** | The helper loads GraphConfig (`107`) but converts `age` to `sqlite` (`112-114`) before creating the store. The active AGE factory is used in the normal active path (`271-283`, `534-545`), but the fallback helper itself violates the declared-backend contract. |

## §3 Goal 2: GraphConfig for All DSN/Graph Resolution

| Copilot/path | DSN/graph resolution | GraphConfig? | Status | Evidence |
|---|---|---|---|---|
| SOC startup | `GraphConfig.load("soc")`, then `create_graph_store()` | Yes | **CONFORMANT** | `gae_state.py:208-214`. The legacy-named AGE client also receives `config.dsn` and `config.graph` (`db/neo4j.py:28-54`). |
| S2P startup | `GraphConfig.load("s2p", profile=...)`, then factory | Yes | **CONFORMANT** | `s2p/main.py:115-126`. |
| Trading active startup | Active config loader delegates to GraphConfig; factory receives typed values | Yes | **CONFORMANT for active path** | `graph_status.py:79-109`, `320-362`; `main.py:303-313`. The separate `_graph_store()` helper remains unsafe for Goal 3 (`main.py:120-129`). |
| Purchasing active startup | Active config plus GraphConfig-backed generic helper | Yes | **CONFORMANT for active path** | `main.py:145-162`, `416-443`; active factory passes `config.dsn` and `config.graph` to the shared factory (`graph_status.py:353-387`). |
| DataOps active startup | Active config delegates to GraphConfig; active factory passes typed DSN/graph | Yes | **CONFORMANT for active path; PARTIAL overall** | `graph_status.py:80-106`, `306-337`; `main.py:534-545`. The generic helper still downgrades AGE (`main.py:103-120`). |
| AGE client | Requires explicit caller-supplied DSN/graph | Caller-owned | **PARTIAL** | `age_client.py:113-126` does not itself load GraphConfig. This is safe only when every caller follows the typed-config contract. |
| S2P shadow | GraphConfig in production; legacy env values only in tests | Yes in production | **PARTIAL** | `s2p_shadow.py:67-89`, `76-80`. |

## §4 Goal 3: No Silent Substitution

| File/path | Failure scenario | Current behavior | Status | Evidence |
|---|---|---|---|---|
| `copilot_sdk/graph/factory.py` | AGE selected with missing DSN | Raises `ValueError` before construction | **CONFORMANT** | `factory.py:260-262`. |
| `copilot_sdk/graph/factory.py` | Production expected AGE resolves SQLite | Raises `GraphConfigError` | **CONFORMANT** | `factory.py:157-164`. |
| `scorer.py` | Production `from_preset()` has no injected store | Raises `RuntimeError`; does not create SQLite | **CONFORMANT** | `scorer.py:238-242`. |
| `apps/trading/backend/app/main.py` | GraphConfig reports AGE | Explicitly rewrites backend to SQLite | **GAP / P1** | `main.py:120-129`. |
| `apps/dataops/backend/app/main.py` | GraphConfig reports AGE in generic helper | Explicitly rewrites backend to SQLite | **GAP / P1** | `main.py:103-120`. |
| `apps/dataops/backend/app/graph_queries.py` | AGE configured but client absent or query fails | Raises when `_age_required` is true | **CONFORMANT for declared AGE** | `graph_queries.py:550-564`. |
| `apps/dataops/backend/app/graph_queries.py` | No required AGE configuration | Returns `None`; callers serve fixtures | **PARTIAL / P2** | `graph_queries.py:551-554`, `200-215`, `518-527`. |
| `DualWriteStore` | Secondary AGE write fails | Primary result is returned; failure is logged and sent to durable outbox | **PARTIAL / P2** | `dual_write_store.py:280-290`, `128-199`. This is observable and durable, but it is still best-effort secondary persistence. |
| `s2p-copilot/backend/app/s2p_shadow.py` | Optional shadow AGE unavailable | Shadow is separate and status-driven; canonical scorer is not replaced | **CONFORMANT for canonical path; PARTIAL overall** | Shadow is explicitly non-authoritative (`s2p_shadow.py:1-5`) and config is optional (`67-89`). |
| Trading execution router | Graph store factory/query fails | Raises HTTP 503; no fixture substitution | **CONFORMANT** | `apps/trading/backend/app/routers/execution_router.py:30-43`. |
| SOC startup | AGE verification fails | Startup raises after reporting failure | **CONFORMANT** | `gen-ai-roi-demo-v4-v50/backend/app/main.py:200-221`. |

## §5 Blocker Status

### Blocker A — SOC InMemoryGraphStore

**Status: CLOSED for the production scorer construction path.**

`init_learning_state()` resolves SOC GraphConfig and constructs the graph store through the shared factory (`gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:208-214`). That store is passed to `SOCCompoundingScorerAdapter` (`gae_state.py:221`). The adapter rejects `None` and explicitly requires an AGE-backed store (`scorer_adapter.py:18-29`). The adapter’s compound scorer is therefore not constructed with an implicit InMemory store. Test callers may still explicitly pass InMemory, as documented in `scorer_adapter.py:20-23`.

### Blocker B — S2P dual graph system

**Status: OPEN.**

The old `Neo4jClient` constructor is disabled (`s2p-copilot/backend/app/db/neo4j.py:10-16`), and the main scorer path uses the configured GraphStore (`s2p-copilot/backend/app/main.py:115-139`). However, the legacy `app/domains/s2p/graph.py` remains a callable Neo4j/S2PDecision read path (`s2p/graph.py:15-71`), and the framework router directly constructs/uses an AGE client outside GraphStore (`framework_router.py:27-32`, `548-559`). Consequently, the governed GraphStore is not the sole graph access abstraction.

### Blocker C — Factory SQLite defaults

**Status: OPEN.**

The shared production scorer now fails when no GraphStore is injected (`copilot-sdk/copilot_sdk/scoring/scorer.py:238-242`), and the factory fails closed for missing AGE DSN (`factory.py:260-262`). However, development/test SQLite/InMemory creation remains (`scorer.py:243-252`), and both Trading and DataOps retain application helpers that convert a resolved AGE backend to SQLite (`trading/main.py:120-129`; `dataops/main.py:103-120`). Therefore a copilot path can still end in SQLite despite AGE being declared, even though the canonical active-store paths are more strongly guarded.

## §6 Remaining Gaps

| ID | File:line | Violated goal | Severity | Risk if unfixed |
|---|---|---|---|---|
| GAP-01 | `copilot-sdk/apps/trading/backend/app/main.py:127-129` | Goals 1/3 | P1 | A fallback/startup path can write Trading Decision data to SQLite after AGE is declared. |
| GAP-02 | `copilot-sdk/apps/dataops/backend/app/main.py:112-120` | Goals 1/3 | P1 | A fallback/startup path can write DataOps Decision data to SQLite after AGE is declared. |
| GAP-03 | `gen-ai-roi-demo-v4-v50/backend/app/main.py:202-205,229-237` | Goal 1 | P1 | SOC Decision verification/counts bypass GraphStore, creating a second graph access contract. |
| GAP-04 | `s2p-copilot/backend/app/routers/framework_router.py:27-32,548-559` | Goals 1/2 | P1 | S2P framework Decision reads bypass the governed GraphStore and can diverge from scorer reads. |
| GAP-05 | `s2p-copilot/backend/app/domains/s2p/graph.py:50-71` | Goal 1 | P1 | A retained callable legacy path still reads `S2PDecision` through a caller-supplied Neo4j driver. |
| GAP-06 | `copilot-sdk/copilot_sdk/graph/projection.py:227-244` | Goal 1 | P2 | Read-only consumers bypass GraphStore even though DSN/graph resolution is typed. |
| GAP-07 | `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:210-224` | Goal 1 | P2 | SOC schema/seeding accesses AGE directly rather than through the common GraphStore boundary. |
| GAP-08 | `copilot-sdk/copilot_sdk/graph/dual_write_store.py:280-290` | Goal 3 | P2 | Secondary persistence can fail while primary operations continue; outbox durability mitigates but does not provide atomic consistency. |
| GAP-09 | `s2p-copilot/backend/app/main.py:172-183` | Goal 1 | P2 | Dual-write enrichment is intentionally redirected to SQLite, leaving split persistence semantics. |
| GAP-10 | `copilot-sdk/apps/dataops/backend/app/graph_queries.py:551-564,200-215` | Goal 3 | P2 | In incomplete/non-required configuration, graph query failure becomes fixture data rather than a hard failure. |
| GAP-11 | `s2p-copilot/backend/app/routers/framework_router.py:589-605` | Goal 1 | P2 | Cypher is registry-restricted, but still executed through a direct AGE client rather than GraphStore. |
| GAP-12 | `gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py:45-54` | Goal 1 | P2 | The legacy-named client remains an active direct AGE access surface and is consumed by SOC startup helpers. |
| GAP-13 | `copilot-sdk/copilot_sdk/scoring/scorer.py:243-252` | Goal 3 | P3 | Test/development profiles still permit InMemory/SQLite stores; accidental profile selection could hide backend substitution. |
| GAP-14 | `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:562-587` | Goal 3 | P3 | Test-mode RL can silently use in-memory priors, reducing parity of failure behavior in tests. |

## §7 Reading Log

The following files were read in full. Line ranges cited above are the relevant evidence locations.

- `copilot-sdk/CLAUDE.md`
- `gen-ai-roi-demo-v4-v50/CLAUDE.md`
- `s2p-copilot/CLAUDE.md`
- `copilot-sdk/docs/design/age_unification_gaps_v1.md`
- `copilot-sdk/docs/design/judgment_memory_v2_7.md`
- `copilot-sdk/copilot_sdk/graph/factory.py`
- `copilot-sdk/copilot_sdk/scoring/scorer.py`
- `ci-platform/ci_platform/graph/age_client.py`
- `copilot-sdk/copilot_sdk/graph/projection.py`
- `copilot-sdk/copilot_sdk/graph/dual_write_store.py`
- `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py`
- `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py`
- `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py`
- `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py`
- `gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py`
- `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py`
- `gen-ai-roi-demo-v4-v50/backend/app/main.py`
- `s2p-copilot/backend/app/db/neo4j.py`
- `s2p-copilot/backend/app/domains/s2p/graph.py`
- `s2p-copilot/backend/app/routers/s2p.py`
- `s2p-copilot/backend/app/framework/similar_cases_base.py`
- `s2p-copilot/backend/app/routers/framework_router.py`
- `s2p-copilot/backend/app/main.py`
- `s2p-copilot/backend/app/s2p_shadow.py`
- `copilot-sdk/apps/trading/backend/app/main.py`
- `copilot-sdk/apps/trading/backend/app/graph_status.py`
- `copilot-sdk/apps/trading/backend/app/cli_sdk.py`
- `copilot-sdk/apps/trading/backend/app/services/regime_classifier.py`
- `copilot-sdk/apps/trading/backend/app/routers/execution_router.py`
- `copilot-sdk/apps/purchasing/backend/app/main.py`
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py`
- `copilot-sdk/apps/dataops/backend/app/context_router.py`
- `copilot-sdk/apps/dataops/backend/app/graph_queries.py`
- `copilot-sdk/apps/dataops/backend/app/main.py`
- `copilot-sdk/apps/dataops/backend/app/graph_status.py`

The requested root-level `CLAUDE.md` was not present at the workspace root; the three repository-level instruction files listed above were present and read in full.

**Review conclusion: READY = NO.** Goals 1 and 3 remain blocked by the P1 downgrade/direct-access findings above; Goal 2 is substantially implemented for canonical production startup but is not yet universal across all graph access paths.
