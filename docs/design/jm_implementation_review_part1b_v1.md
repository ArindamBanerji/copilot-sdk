# JM Implementation Review — Part 1B

Review-only audit of Trading, Purchasing, DataOps, and the Goal 2/3 synthesis. Findings are adversarial: comments and intended architecture are not treated as implementation evidence. Every status below is supported by file/line evidence.

## §1 EXECUTIVE SUMMARY

| Area | Result |
|---|---|
| Trading | P1 remaining: **1/4**; P2 remaining: **0/2** |
| Purchasing | P1 remaining: **0/2**; P2 remaining: **1/5** |
| DataOps | P1 remaining: **2/2**; P2 remaining: **3/5** |
| Goal 2 — GraphConfig usage | **PARTIAL** |
| Goal 3 — no silent substitution | **GAP** |

The central remaining implementation defect is silent `age`→`sqlite` conversion in Trading and DataOps before the common factory (`copilot-sdk/apps/trading/backend/app/main.py:116-135`; `copilot-sdk/apps/dataops/backend/app/main.py:103-120`). Purchasing uses the typed configuration and common factory for its active store (`copilot-sdk/apps/purchasing/backend/app/main.py:145-162,414-442`).

## §2 TRADING FINDINGS

| Finding | File:Line | Original issue | Current status | Evidence |
|---|---|---|---|---|
| P1-TRD-1 | `copilot-sdk/apps/trading/backend/app/main.py:119-135` | Startup silently downgraded AGE to SQLite; fixture seed target was ambiguous. | **GAP** | Startup loads `GraphConfig` at `:119-120`, then unconditionally changes `backend == "age"` to `"sqlite"` at `:127-128` before calling `create_graph_store` at `:129-135`. The fallback `seed_graph_store` is created through this path at `:321`. If an active AGE store exists, startup skips fixture seeding at `:362-363`; otherwise it restores/seeds the SQLite fallback at `:365-367`. |
| P1-TRD-2 | `copilot-sdk/apps/trading/backend/app/graph_status.py:155-175,224-311,320-362` | `dual_write` rejected and active AGE store unavailable. | **CONFORMANT** | Validation accepts `sqlite`, `age`, and `dual_write` at `:155-160`; AGE/dual configurations require DSN at `:161-175`. `TradingActiveAGEGraphStore` exists at `:224-311`, stamps `domain="trading"`, and the active factory calls common `create_graph_store` at `:342-357`, returning the wrapper at `:358-362`. |
| P1-TRD-3 | `copilot-sdk/apps/trading/backend/app/cli_sdk.py:52-71,120-140,609-637` | CLI bypassed GraphConfig/factory and restore copied directly into SQLite. | **CONFORMANT** | `_load_cli_graph_config` uses `GraphConfig.load(DOMAIN, profile)` at `:52-71`; `_get_scorer` calls common `create_graph_store` and injects it into `CompoundingScorer.from_preset` at `:120-140`. Restore explicitly rejects AGE-backed Trading at `:629-630` and copies the backup only after that check at `:632-637`. |
| P1-TRD-4 | `copilot-sdk/apps/trading/backend/app/services/regime_classifier.py:139-145` | Failed domain query retried without `domain="trading"`. | **CONFORMANT** | The verified-decision reader is called with `self._domain` at `:139-145`; there is no unscoped retry in the current function. |
| P2-TRD-1 | `copilot-sdk/apps/trading/backend/app/routers/execution_router.py:26-44`; `copilot-sdk/apps/trading/backend/app/routers/journal.py:218-240` | Graph exceptions swallowed and local records returned. | **CONFORMANT** | Both routes convert graph-factory/query failure into HTTP 503: execution at `execution_router.py:30-43`, journal at `journal.py:224-237`. |
| P2-TRD-2 | `copilot-sdk/apps/trading/backend/app/context_router.py:314-345,348-370,482-498` | Context provider failure returned fixture data. | **CONFORMANT** | Provider errors and sample sources become 503 outside demo mode at `:318-330`; fixture/cache fallback is only returned in demo mode at `:339-345`, `:367-370`, and `:482-498`. |

**Trading P1 remaining: 1/4. Trading P2 remaining: 0/2.**

## §3 PURCHASING FINDINGS

| Finding | File:Line | Original issue | Current status | Evidence |
|---|---|---|---|---|
| P1-PUR-1 | `copilot-sdk/apps/purchasing/backend/app/main.py:145-162,414-425` | Raw `GRAPH_BACKEND` resolution and AGE→SQLite downgrade. | **CONFORMANT** | `_graph_store` loads `GraphConfig.load(DOMAIN)` at `:148-154` and passes the selected backend to common `create_graph_store` at `:156-162`; there is no AGE→SQLite rewrite. Application startup obtains active configuration/store at `:416-420` and selects it at `:422-425`. |
| P1-PUR-2 | `copilot-sdk/apps/purchasing/backend/app/graph_status.py:370-417` | Active graph status did not reflect the actual backend. | **CONFORMANT** | Status derives `active_backend` from the requested active configuration at `:394-401` and reports `requested_backend`, `sqlite_authoritative`, and `age_active` at `:408-417`; dual-write is not converted to SQLite. |
| P2-PUR-1 | `copilot-sdk/apps/purchasing/backend/app/graph_status.py:394-417` | `dual_write` misreported as SQLite. | **CONFORMANT** | `requested_backend` is retained and `age_active` explicitly accepts `age` and `dual_write` at `:394-401`; the returned status distinguishes active and requested backends at `:408-417`. |
| P2-PUR-2 | `copilot-sdk/apps/purchasing/backend/app/routers/discovery_router.py:12-52` | Discovery always returned demo decisions. | **CONFORMANT** | The route rejects non-demo use at `:28-30`; demo decisions are returned only after the explicit demo check and are labeled with demo/sample provenance at `:31-52`. |
| P2-PUR-3 | `copilot-sdk/apps/purchasing/backend/app/routers/pos_router.py:19-23,31-93,95-119`; `spend_router.py:19-48,112-145`; `commodity_data_provider.py:101-158` | POS, spend, and commodity paths returned mocks/sample data when live data failed. | **CONFORMANT** | POS raises for unavailable non-demo connectors and rejects mock/fixture output outside demo mode (`pos_router.py:31-71,77-93,95-119`). Spend raises 503 for the default mock outside demo (`spend_router.py:41-48`) and rejects sample commodity data (`:135-145`). Commodity provider raises on non-demo sample/fixture fallback (`commodity_data_provider.py:107-118,131-158`). |
| P2-PUR-4 | `copilot-sdk/apps/purchasing/backend/app/main.py:693-708` | Demo routes exposed fixture data without a clear runtime boundary. | **CONFORMANT** | Demo-only chain/discovery routers are conditionally included at `:693-697`; the always-included POS/spend/commodity routes are guarded by their own non-demo failure checks cited above. |
| P2-PUR-5 | `copilot-sdk/apps/purchasing/backend/app/main.py:180-189` | `CI_DATA_DIR` resolved directly instead of through typed configuration. | **GAP** | `_resolve_scoring_db` reads `os.environ.get("CI_DATA_DIR")` and `os.environ["CI_DATA_DIR"]` directly at `:180-186`. |

**Purchasing P1 remaining: 0/2. Purchasing P2 remaining: 1/5.**

## §4 DATAOPS FINDINGS

| Finding | File:Line | Original issue | Current status | Evidence |
|---|---|---|---|---|
| P1-DOPS-1 | `copilot-sdk/apps/dataops/backend/app/context_router.py:110-121,381-403,431-437,902-987` | Decision-shaped metadata came from local JSON without domain enforcement. | **PARTIAL** | Demo JSON/seed records are still assembled by `_demo_context_decisions` at `:110-121`; `_normalize_seed_decision` creates Decision-shaped records at `:381-403` but does not add a `domain` field. `_all_context_decisions` gates that JSON path to explicit demo/test mode and labels it sample at `:431-437`, while production endpoints consume it at `:902-987` through the common helper. Guarding and labeling reduce the risk, but do not enforce domain on the records. |
| P1-DOPS-2 | `copilot-sdk/apps/dataops/backend/app/graph_queries.py:46-69,509-527,550-564` | AGE failure fell back to fixtures; DSN path was generic. | **PARTIAL** | Required AGE configuration now raises when no client exists (`:550-554`) or when a query fails (`:558-564`), so configured AGE failure does not silently become a fixture. However, topology setup still inspects and temporarily restores generic `GRAPH_BACKEND` at `:46-63`, and query methods still return fixture results whenever `_run_graph` returns `None` at `:509-527`; therefore the non-required/offline path remains a fixture substitution path. |
| P2-DOPS-1 | `copilot-sdk/apps/dataops/backend/app/main.py:103-120` | Raw backend handling and AGE→SQLite conversion. | **GAP** | The path loads `GraphConfig` at `:106-107`, then changes `age` to `sqlite` at `:112-113` before calling the factory at `:114-120`. |
| P2-DOPS-2 | `copilot-sdk/apps/dataops/backend/app/main.py:527-552,564-573` | Scorer startup seeded from fixtures/SQLite path. | **PARTIAL** | The scorer is constructed with the selected graph store at `:534-552`, and startup seeds the bundle/fixture path whenever the DB is not memory at `:564-573`. The selected store can be active AGE, but the startup source remains local demo/seed data and the underlying fallback `_graph_store` still rewrites AGE to SQLite (`:103-120`). |
| P2-DOPS-3 | `copilot-sdk/apps/dataops/backend/app/main.py:660-668` | Health returned OK even when source was fixture. | **CONFORMANT** | Health derives `graph_source` from `DataOpsGraphClient` and returns `ok` only for `graph`, otherwise `error`, at `:660-668`. |
| P2-DOPS-4 | `copilot-sdk/apps/dataops/backend/app/context_router.py:1603-1615` | Decision-shaped metadata written to local JSON without domain validation. | **PARTIAL** | The route still reads and writes `METADATA_PATH` JSON at `:1609-1614`. It now forcibly stamps `domain=DOMAIN` and `provenance="demo"` at `:1610-1612`, but it remains a local JSON write path rather than a governed graph write. |
| P2-DOPS-5 | `copilot-sdk/apps/dataops/backend/app/services/graph_enrichment.py:30-37,51-60,99-130` | AGE enrichment query had no domain predicate. | **CONFORMANT** | Query parameters include `domain="dataops"` at `:51-60`; read/update Cypher predicates use the domain at `:99-117`, and created records stamp it at `:120-130`. |

**DataOps P1 remaining: 2/2. DataOps P2 remaining: 3/5.**

## §5 GOAL 2: GRAPHCONFIG SYNTHESIS

| Copilot | File:Line | Method | GraphConfig? | Status |
|---|---|---|---|---|
| SOC | `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:208-221` | `GraphConfig.load("soc")`, then common `create_graph_store` and scorer injection. | Yes | **CONFORMANT** |
| S2P | `s2p-copilot/backend/app/main.py:101-139` | Typed GraphConfig drives startup backend/DSN/graph and common factory. | Yes, but Part 1A identified a separate shadow graph path (`s2p-copilot/backend/app/s2p_shadow.py:117-126,223-250`). | **PARTIAL** |
| Shared infra | `copilot-sdk/copilot_sdk/graph/factory.py:145-166`; caller-supplied AGE client `ci-platform/ci_platform/graph/age_client.py:1163-1178` | Factory requires explicit backend/config inputs; AGE client receives caller-supplied DSN. | Yes at factory boundary | **CONFORMANT** |
| Trading | `copilot-sdk/apps/trading/backend/app/main.py:119-135` | `GraphConfig.load(DOMAIN)` resolves backend, but `age` is rewritten to `sqlite` before factory invocation. | Yes, then overridden | **PARTIAL** |
| Purchasing | `copilot-sdk/apps/purchasing/backend/app/main.py:148-162,416-425` | GraphConfig/common factory path plus active graph store initialization. | Yes | **CONFORMANT** |
| DataOps | `copilot-sdk/apps/dataops/backend/app/main.py:106-120` | `GraphConfig.load(DOMAIN)` resolves backend, but `age` is rewritten to `sqlite` before factory invocation. | Yes, then overridden | **GAP** |

**GOAL 2 VERDICT: PARTIAL.** Typed configuration is used at the principal startup boundaries, but Trading and DataOps override the resolved backend, and S2P retains a separate shadow graph configuration path. The result is not a single authoritative GraphConfig-controlled graph lifecycle across all copilots.

## §6 GOAL 3: NO SILENT SUBSTITUTION SYNTHESIS

| Copilot | Failure behavior when AGE is unreachable | Silent substitution? | Status |
|---|---|---|---|
| Shared infra | AGE/missing-DSN factory paths raise; DualWrite missing DSN raises (`copilot-sdk/copilot_sdk/graph/factory.py:205-210,260-262`). | No at factory boundary | **CONFORMANT** |
| SOC | GraphConfig/factory path is injected into the scorer and rejects absent store (`gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:208-221`; `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py:18-28`). | No | **CONFORMANT** |
| S2P | Part 1A found a SQLite enrichment primary and separate shadow AGE path (`copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:12,15`; `s2p-copilot/backend/app/s2p_shadow.py:117-126,223-250`). | Yes on the enrichment split; shadow remains separate | **GAP** |
| Trading | `age` is converted to `sqlite` before the factory (`copilot-sdk/apps/trading/backend/app/main.py:127-135`). Non-demo context failures otherwise return 503 rather than fixtures (`context_router.py:318-345,482-498`). | Yes for the graph/scorer path | **GAP** |
| Purchasing | Active store is built from the requested GraphConfig backend (`copilot-sdk/apps/purchasing/backend/app/main.py:416-425`); live-data mock/fixture failures become 503 outside demo (`pos_router.py:31-71`; `spend_router.py:41-48`; `commodity_data_provider.py:131-158`). | No in the reviewed paths | **CONFORMANT** |
| DataOps | Required AGE query/client failures raise (`copilot-sdk/apps/dataops/backend/app/graph_queries.py:550-564`), but the main graph-store path converts AGE to SQLite (`copilot-sdk/apps/dataops/backend/app/main.py:112-120`). Unconfigured/offline graph queries return fixtures (`graph_queries.py:509-527`), and explicit demo context uses JSON (`context_router.py:431-437`). | Yes in the main Decision path; guarded fixture substitution remains elsewhere | **GAP** |

**GOAL 3 VERDICT: GAP.** Even though the shared factory, SOC, and Purchasing paths reject the reviewed failure rather than silently substituting, Trading and DataOps still select SQLite before AGE failure can be observed. S2P retains the Part 1A enrichment/shadow split.

## §7 COMBINED GAP INVENTORY

The following includes every remaining PARTIAL/GAP item from Part 1A plus Part 1B. Part 1A reported one remaining P1 and six remaining P2 items (`copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:14-15`).

### Critical / high

| Severity | Item | Status | Evidence / risk |
|---|---|---|---|
| High | P1-TRD-1 — Trading rewrites AGE to SQLite | **GAP** | `copilot-sdk/apps/trading/backend/app/main.py:127-135`. AGE outage or misconfiguration can be hidden behind a local SQLite scorer. |
| High | P1-DOPS-1 — DataOps JSON Decision-shaped records lack domain field | **PARTIAL** | `copilot-sdk/apps/dataops/backend/app/context_router.py:381-403,431-437`. Demo gating exists, but record-level domain enforcement is absent. |
| High | P1-DOPS-2 — DataOps mixed required-AGE and fixture/offline paths | **PARTIAL** | `copilot-sdk/apps/dataops/backend/app/graph_queries.py:46-63,509-527,550-564`. Required AGE fails closed, but non-required mode still returns fixture results and generic backend state is bridged. |
| High | P2-DOPS-1 — DataOps rewrites AGE to SQLite | **GAP** | `copilot-sdk/apps/dataops/backend/app/main.py:112-120`. This independently defeats Goal 3 on the Decision/scorer path. |
| High | P2-S2P-3 — SQLite enrichment primary / dual graph behavior | **GAP/PARTIAL** | `copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:12,15`; Part 1A evidence identifies SQLite enrichment as a remaining split. Risk is divergent authorities. |

### Medium

| Severity | Item | Status | Evidence / risk |
|---|---|---|---|
| Medium | P2-PUR-5 — direct `CI_DATA_DIR` resolution | **GAP** | `copilot-sdk/apps/purchasing/backend/app/main.py:180-186`. A second untyped environment path can diverge from the shared configuration contract. |
| Medium | P2-DOPS-2 — fixture-driven startup seeding remains | **PARTIAL** | `copilot-sdk/apps/dataops/backend/app/main.py:564-573`. Fixture provenance is explicit, but startup still seeds persisted Decision state from local data. |
| Medium | P2-DOPS-4 — DataOps local JSON metadata write | **PARTIAL** | `copilot-sdk/apps/dataops/backend/app/context_router.py:1603-1615`. Domain is stamped, but the local JSON authority remains. |
| Medium | P2-INFRA-3 — projection direct AGE client | **PARTIAL** | `copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:15`; Part 1A evidence identifies direct read-only AGE construction in `copilot_sdk/graph/projection.py`. Risk is a second AGE lifecycle. |
| Medium | P2-SOC-3 — SOC seed direct AGE client | **PARTIAL** | `copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:181`. Risk is an alternate AGE construction/configuration path. |
| Medium | P2-S2P-4 — separate S2P shadow graph configuration | **GAP/PARTIAL** | `s2p-copilot/backend/app/s2p_shadow.py:117-126,223-250`; `copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:12,15`. Risk is a second graph authority. |
| Medium | P2-S2P-6 — mixed situation context | **PARTIAL** | `copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:183`; local metadata can still be merged into S2P context without the same graph-domain provenance. |
| Medium | P2-S2P-7 — JSON Decision-shaped seed input | **PARTIAL** | `copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:185`; seed writes are domain-stamped, but fixture-derived Decisions remain an operational boundary risk. |

### Low / hygiene

| Severity | Item | Status | Evidence / risk |
|---|---|---|---|
| Low | P1-S2P dormant legacy Decision reader | **PARTIAL** | `copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:14`; `s2p-copilot/backend/app/domains/s2p/graph.py:50-71`. It is not traced as an application caller, but remains callable code and test-covered. |

## §8 READING LOG

All files below were read in full, not by snippet or grep. Line ranges are the complete file ranges read.

| File | Read range |
|---|---:|
| `copilot-sdk/docs/design/age_unification_gaps_v1.md` | 1-817 |
| `copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md` | 1-218 |
| `copilot-sdk/CLAUDE.md` | 1-139 |
| `copilot-sdk/apps/trading/backend/app/main.py` | 1-534 |
| `copilot-sdk/apps/trading/backend/app/graph_status.py` | 1-456 |
| `copilot-sdk/apps/trading/backend/app/cli_sdk.py` | 1-1125 |
| `copilot-sdk/apps/trading/backend/app/services/regime_classifier.py` | 1-198 |
| `copilot-sdk/apps/trading/backend/app/routers/execution_router.py` | 1-80 |
| `copilot-sdk/apps/trading/backend/app/routers/journal.py` | 1-618 |
| `copilot-sdk/apps/trading/backend/app/context_router.py` | 1-558 |
| `copilot-sdk/apps/purchasing/backend/app/main.py` | 1-799 |
| `copilot-sdk/apps/purchasing/backend/app/graph_status.py` | 1-474 |
| `copilot-sdk/apps/purchasing/backend/app/routers/discovery_router.py` | 1-55 |
| `copilot-sdk/apps/purchasing/backend/app/routers/pos_router.py` | 1-190 |
| `copilot-sdk/apps/purchasing/backend/app/routers/spend_router.py` | 1-145 |
| `copilot-sdk/apps/purchasing/backend/app/services/commodity_data_provider.py` | 1-222 |
| `copilot-sdk/apps/dataops/backend/app/context_router.py` | 1-1620 |
| `copilot-sdk/apps/dataops/backend/app/graph_queries.py` | 1-604 |
| `copilot-sdk/apps/dataops/backend/app/main.py` | 1-678 |
| `copilot-sdk/apps/dataops/backend/app/services/graph_enrichment.py` | 1-131 |

READY: YES
