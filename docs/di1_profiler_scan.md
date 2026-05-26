# PLAN-DI-1 Source Profiler Scan

## Executive Summary

DataOps does not currently have a dedicated source-profiler endpoint or service matching `/api/dataops/profiler/source/{source_id}`. The live backend has connector-backed and fixture-backed source-like data, schema-impact evidence, graph-derived DataOps factors, connector health aliases, and context endpoints, but none performs full column profiling with inferred types, null rates, drift detection, completeness/freshness/consistency scoring, and source-level quality aggregation. DI-1-PROFILER status: ABSENT as a dedicated endpoint, PARTIAL as reusable building blocks. Recommended MAP action: KEEP but REDUCE to a narrow endpoint/service implementation first; defer any 6-to-7 factor tensor change. Biggest implementation gap: a source-profiler service/router that converts SAP/Celonis/cache/graph records into schema, null-rate, freshness, drift, and quality summaries before scoring.

## Method and Scope

- Repo path: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`.
- Read-only source/test/config constraint. The only write is this report: `docs/di1_profiler_scan.md`.
- No pytest or test suite was run.
- `CLAUDE.md` was read first; it requires source grounding and file:line citations (`CLAUDE.md:1-8`).
- `graphify-out/GRAPH_REPORT.md` was read for architecture navigation context; it reports a 605-file corpus and graph structure (`graphify-out/GRAPH_REPORT.md:1-9`).
- A TestClient route probe was run for safe GET paths only; no POST or mutating endpoint was called.
- Caveat: frontend scan found no `profiler` route usage, but the scan was focused on backend implementation readiness.

## Section 1: Existing Profiling / Quality / Schema / Drift

| Candidate | Endpoint/File | Lines | What It Does | Source Profiling? | Static/Live/Unknown | Evidence |
|---|---|---:|---|---|---|---|
| MAP profiler path | `/api/dataops/profiler/source/{source_id}` | N/A | TestClient probe returned 404 for `/api/dataops/profiler` and `/api/dataops/profiler/source/test-source`. No route decorator for profiler was found in DataOps app route inventory. | NO | N/A | Probe output: `404 /api/dataops/profiler`, `404 /api/dataops/profiler/source/test-source`; route decorators list has no profiler route, while DataOps status routes are only `/health`, `/celonis/status`, `/sap/status`, `/enterprise-health` (`apps/dataops/backend/app/routers/dataops_status.py:19-55`). |
| Schema impact | `/api/context/schema-impact/{system}` | 1050-1067 | Loads fixture schema changes, optional column filter, returns change count, impact count, and preventable-alert count. | PARTIAL; schema-change summary only, not column profiling/null rates. | Fixture-backed | `apps/dataops/backend/app/context_router.py:1050-1067`. |
| Alert factors | `/api/context/alert/{id}/factors` | 248-312, 1314-1316 | Computes six DataOps factors from graph or fixtures for an alert, including `source_reliability` and `data_freshness`. | PARTIAL; factor explanation, not source profile. | Graph if connected, otherwise fixture | `apps/dataops/backend/app/graph_queries.py:248-312`; mounted by `apps/dataops/backend/app/context_router.py:1314-1316`. |
| Connector health | `/api/context/enterprise-health`, `/api/dataops/*/status` | 667-680, 19-122 | Reports SAP/Celonis connector state and fixture/cache availability. | NO; health/status only. | Mostly fixture/config status | `apps/dataops/backend/app/context_router.py:667-680`; `apps/dataops/backend/app/routers/dataops_status.py:19-122`. |
| SAP purchase orders | `/api/context/sap/purchase-orders` | 683-690 | Returns purchase order records from SAP connector live path or cache fallback. | PARTIAL data source input; no profiling. | Live if configured, else cache | `apps/dataops/backend/app/context_router.py:683-690`; connector behavior at `apps/dataops/backend/app/sap_connector.py:34-93`. |
| Celonis process data | `/api/context/celonis/process-data` | 693-711 | Returns knowledge models, KPIs, and process data from Celonis connector live path or cache fallback. | PARTIAL data source input; no profiling. | Live if configured, else cache | `apps/dataops/backend/app/context_router.py:693-711`; connector behavior at `apps/dataops/backend/app/celonis_connector.py:34-78`. |
| Process signals | `/api/context/process-signals/{system}` | 1368-1397 | Returns process-mining style signals and connector state. | NO; process context, not schema/source profile. | Fixture with connector state | `apps/dataops/backend/app/context_router.py:1368-1397`. |

Profiler endpoints found: NONE. Quality/schema/drift logic found: schema-impact fixture summaries, DataQualityAlert graph queries, factor computation for alerts, and AE/static quality-gate descriptions. Gap against `/api/dataops/profiler/source/{source_id}`: no dedicated route, no source-id resolver, no column type/null-rate computation, no completeness/freshness/consistency quality score, and no explicit drift comparison workflow.

## Section 2: Connector Data Inventory

### CelonisConnector

| Method | Lines | Return/Data Shape | Profiling Relevance | Evidence |
|---|---:|---|---|---|
| `__init__` | 17-32 | Configures base URL/token/cache dir and marks live enabled only when URL/token inputs exist. | Establishes live-vs-cache mode for profiler source classification. | `apps/dataops/backend/app/celonis_connector.py:17-32`. |
| `get_knowledge_models()` | 34-44 | `{"source": "celonis_live"|"celonis_cache", "knowledge_models": list[dict]}`. | Can list models/sources but not schemas/null rates directly. | `apps/dataops/backend/app/celonis_connector.py:34-44`. |
| `get_kpis(km_id)` | 46-56 | `{"source": ..., "kpis": list[dict]}`. | KPI metadata can enrich profiling but does not provide record-level completeness. | `apps/dataops/backend/app/celonis_connector.py:46-56`. |
| `get_process_data(km_id, fields=None, kpis=None)` | 58-78 | `{"source": ..., "process_data": dict}` from live endpoint or `celonis_process_data.json`. | Best Celonis input for profiling; can be inspected if it contains tabular/list payloads, timestamps, activity/case fields. No built-in profile computation. | `apps/dataops/backend/app/celonis_connector.py:58-78`. |
| `health()` | 80-92 | Live/cache status and cached model count. | Health only; distinguish from profiling data. | `apps/dataops/backend/app/celonis_connector.py:80-92`. |

### SAPConnector

| Method | Lines | Return/Data Shape | Profiling Relevance | Evidence |
|---|---:|---|---|---|
| `__init__` | 17-32 | Configures base URL/API key/cache dir and live mode. | Establishes live-vs-cache mode for profiler source classification. | `apps/dataops/backend/app/sap_connector.py:17-32`. |
| `get_purchase_orders(top=20)` | 34-40 | Delegates to `_get_collection`; returns `source`, `total`, `purchase_orders`. | Strong candidate source for profiling record fields, null rates, freshness fields. | `apps/dataops/backend/app/sap_connector.py:34-40`, `apps/dataops/backend/app/sap_connector.py:75-93`. |
| `get_supplier_invoices(top=20)` | 42-48 | Returns `source`, `total`, `supplier_invoices`. | Candidate source for invoice-schema/profile support, not currently exposed by context router. | `apps/dataops/backend/app/sap_connector.py:42-48`, `apps/dataops/backend/app/sap_connector.py:75-93`. |
| `get_suppliers(top=20)` | 50-56 | Returns `source`, `total`, `suppliers`. | Candidate master-data source for completeness/consistency checks, not currently exposed by context router. | `apps/dataops/backend/app/sap_connector.py:50-56`, `apps/dataops/backend/app/sap_connector.py:75-93`. |
| `health()` | 58-73 | Live/cache status and cached record count. | Health only; not a profile. | `apps/dataops/backend/app/sap_connector.py:58-73`. |

Can connector data feed source profiling now? YES, as raw input. Celonis exposes knowledge models, KPIs, and process data; SAP exposes purchase orders, supplier invoices, and suppliers. What is missing: a source resolver, record normalization, type inference, null/completeness metrics, freshness timestamp extraction, drift baseline comparison, and a quality-score aggregate.

## Section 3: Graph Contract / Graph Queries Assessment

| File | Lines | Function/Class | Quality/Profile Signal | Can Support DI-1? | Evidence |
|---|---:|---|---|---|---|
| `graph_contract.py` | 8-31 | `DATAOPS_GRAPH_CONTRACT` | Declares `Dataset` with `schema_columns`, `QualityRule`, `Alert`, `Pipeline`, `ProcessModel`, and transformations plus `MONITORS`/`DETECTED_IN`/lineage-style edges. | PARTIAL; graph schema can represent quality contracts and dataset schema columns, but it is declarative. | `apps/dataops/backend/app/graph_contract.py:8-31`. |
| `graph_queries.py` | 16-23 | `FACTOR_NAMES` | Existing graph layer already computes six DataOps factors, including source reliability and data freshness. | PARTIAL; factor layer can inform quality scoring but is alert-scoped. | `apps/dataops/backend/app/graph_queries.py:16-23`. |
| `DataOpsGraphClient.get_pipelines()` | 94-117 | pipeline graph/fixture query | Provides systems and topology, not source column profiles. | PARTIAL context. | `apps/dataops/backend/app/graph_queries.py:94-117`. |
| `DataOpsGraphClient.get_alerts()` | 119-137 | `DataQualityAlert` graph query/fallback | Exposes quality alerts that can seed drift/quality history. | PARTIAL; alert history, not source profiler. | `apps/dataops/backend/app/graph_queries.py:119-137`. |
| `DataOpsGraphClient.get_factors()` | 248-312 | alert factor computation | Returns `impact_scope`, `source_reliability`, `recurrence_frequency`, `downstream_urgency`, `data_freshness`, `business_criticality`. | PARTIAL; useful signal inputs but not source-level profiling. | `apps/dataops/backend/app/graph_queries.py:248-312`. |
| `compute_impact_scope`, `compute_downstream_urgency`, `compute_recurrence` | 438-493 | graph/fixture computations | Derives topology/recurrence factors. | PARTIAL; not schema/null/freshness profiling. | `apps/dataops/backend/app/graph_queries.py:438-493`. |

Graph contracts represent DataOps entities and relationships, including datasets and quality rules. Graph queries expose DataQualityAlert and pipeline context plus derived factors. Source quality could be partially derived from existing graph data where `DataQualityAlert`, `Dataset.schema_columns`, and `QualityRule` nodes are populated, but live profiling still needs record-level source reads and profile computation. Current graph query data is graph-backed only when `GRAPH_DSN` is available; otherwise it falls back to fixture JSON (`apps/dataops/backend/app/graph_queries.py:56-92`, `apps/dataops/backend/app/graph_queries.py:532-539`).

## Section 4: Factor Assessment

Current live DataOps preset:

- Categories: `schema_change`, `volume_anomaly`, `quality_anomaly`, `freshness_violation`, `pipeline_failure`, `transform_drift` (`copilot_sdk/scoring/presets/dataops.py:21-32`).
- Actions: `auto_approve`, `investigate`, `escalate_to_owner`, `pause_downstream`, `refer_to_specialist` (`copilot_sdk/scoring/presets/dataops.py:33-39`).
- Factors: `impact_scope`, `source_reliability`, `recurrence_frequency`, `downstream_urgency`, `data_freshness`, `business_criticality` (`copilot_sdk/scoring/presets/dataops.py:40-47`).
- Shape: 6 categories x 5 actions x 6 factors (`copilot_sdk/scoring/presets/dataops.py:21-24`).
- Bootstrap tensor expects the preset tensor shape and falls back to `np.full(expected_shape, 0.5)` on mismatch/load error (`copilot_sdk/scoring/presets/dataops.py:80-90`).

`source_quality_score` does not exist as a current factor. Related concepts already exist as `source_reliability` and `data_freshness` factors in both preset and context code (`copilot_sdk/scoring/presets/dataops.py:40-47`, `apps/dataops/backend/app/context_router.py:21-28`, `apps/dataops/backend/app/graph_queries.py:16-23`).

Changing from 6 to 7 factors would change tensor shape from `(6, 5, 6)` to `(6, 5, 7)`, requiring preset shape changes, bootstrap centroid fixture regeneration or fallback acceptance, scoring request/frontend factor updates, seed fixture updates, factor autofill/UI changes, and regression tests. Recommendation: implement DI-1 as endpoint/profile artifact first and map profile metrics into existing `source_reliability` / `data_freshness` / category context if needed. Defer tensor factor change until product explicitly wants the scorer surface expanded and migration/test blast radius is accepted.

## Section 5: Route Inventory

| Method(s) | Path | Source/Purpose | DI-1 Relevance |
|---|---|---|---|
| GET | `/api/dataops/health` | DataOps status alias (`apps/dataops/backend/app/routers/dataops_status.py:19-41`) | Health only |
| GET | `/api/dataops/celonis/status` | Celonis status alias (`apps/dataops/backend/app/routers/dataops_status.py:44-46`) | Connector status only |
| GET | `/api/dataops/sap/status` | SAP status alias (`apps/dataops/backend/app/routers/dataops_status.py:49-51`) | Connector status only |
| GET | `/api/dataops/enterprise-health` | Enterprise health alias (`apps/dataops/backend/app/routers/dataops_status.py:54-76`) | Status only |
| POST | `/api/score` | SDK scoring router mounted in `create_app` (`apps/dataops/backend/app/main.py:241-249`) | Downstream scoring pipeline |
| POST | `/api/learn` | SDK scoring router | Learning pipeline |
| GET | `/api/fingerprint`, `/api/trajectory`, `/api/health`, `/api/history` | SDK scoring router (`copilot_sdk/backend/scoring_router.py:108-135`) | Scorer observability |
| GET | `/api/conservation/status`; POST `/api/conservation/what-if` | Conservation router mounted in `create_app` (`apps/dataops/backend/app/main.py:251-257`) | Not profiler |
| GET | `/api/transfer/status` | Transfer router mounted in `create_app` (`apps/dataops/backend/app/main.py:250`) | Not profiler |
| GET | `/api/evolution/*` | Evolution router mounted in `create_app` (`apps/dataops/backend/app/main.py:258-264`) | Not profiler |
| GET | `/api/self/*` | Self-computation router mounted in `create_app` (`apps/dataops/backend/app/main.py:265`) | Scorer introspection |
| GET | `/api/context/pipelines` | Graph/fixture pipeline list (`apps/dataops/backend/app/context_router.py:662-664`) | Source topology context |
| GET | `/api/context/enterprise-health` | SAP/Celonis/graph health (`apps/dataops/backend/app/context_router.py:667-680`) | Connector health |
| GET | `/api/context/sap/purchase-orders` | SAP purchase-order records (`apps/dataops/backend/app/context_router.py:683-690`) | Raw source input |
| GET | `/api/context/celonis/process-data` | Celonis models/KPIs/process data (`apps/dataops/backend/app/context_router.py:693-711`) | Raw source input |
| GET | `/api/context/alerts`, `/api/context/alert/{id}`, `/api/context/alert/{id}/factors` | Quality alert and factor context (`apps/dataops/backend/app/context_router.py:722-728`, `apps/dataops/backend/app/context_router.py:1295-1316`) | Partial quality/factor signals |
| GET | `/api/context/schema-impact/{system}` | Fixture schema-change impact (`apps/dataops/backend/app/context_router.py:1050-1067`) | Partial schema drift context |
| GET | `/api/context/process-signals/{system}`, `/api/context/process-timeline`, `/api/context/cross-graph-insight/{alert_id}` | Process and cross-source context (`apps/dataops/backend/app/context_router.py:1070-1120`, `apps/dataops/backend/app/context_router.py:1178-1206`, `apps/dataops/backend/app/context_router.py:1368-1397`) | Context, not profiler |
| GET/POST | `/api/context/alert-metadata` | Local metadata store (`apps/dataops/backend/app/context_router.py:1535-1549`) | Not profiler |
| GET | `/api/ae/*` | AE/static impact, recommendation, lifecycle, operational rules (`apps/dataops/backend/app/ae_router.py:291-475`) | Related quality-gate demo content, not source profiler |

Full API route dump from TestClient included no `/api/dataops/profiler` route and no `/api/context/quality` route. Probed paths `/api/dataops/profiler`, `/api/dataops/profiler/source/test-source`, `/api/context/quality`, `/api/dataops/source-profile`, and `/api/context/source-quality` all returned 404.

## Section 6: Context Router / Source-Like Data

The context router already provides source-like data but not DI-1 source profiling:

- `/api/context/sap/purchase-orders` returns SAP purchase-order records from `SAPConnector.get_purchase_orders()` with live/cache source tagging (`apps/dataops/backend/app/context_router.py:683-690`, `apps/dataops/backend/app/sap_connector.py:34-40`, `apps/dataops/backend/app/sap_connector.py:75-93`).
- `/api/context/celonis/process-data` returns Celonis knowledge models, KPIs, and process data with combined live/cache source tagging (`apps/dataops/backend/app/context_router.py:693-711`, `apps/dataops/backend/app/celonis_connector.py:34-78`).
- `/api/context/schema-impact/{system}` returns fixture schema changes and impact totals, including optional column filtering (`apps/dataops/backend/app/context_router.py:1050-1067`).
- `/api/context/alert/{id}/factors` returns alert-scoped factors from graph or fixture data, including existing source reliability and data freshness signals (`apps/dataops/backend/app/graph_queries.py:248-312`, `apps/dataops/backend/app/context_router.py:1314-1316`).
- `/api/context/process-signals/{system}` adds process signal context and connector live/cache state, but not a source profile (`apps/dataops/backend/app/context_router.py:1368-1397`).

Static/live/fixture classification: SAP and Celonis connectors use live HTTP only when configured, otherwise cache fallback (`apps/dataops/backend/app/sap_connector.py:95-106`, `apps/dataops/backend/app/celonis_connector.py:94-103`). Graph queries use AGE only when `GRAPH_DSN`/client is available, otherwise fixture fallback (`apps/dataops/backend/app/graph_queries.py:56-92`, `apps/dataops/backend/app/graph_queries.py:495-505`). Several context endpoints explicitly load local JSON fixtures (`apps/dataops/backend/app/context_router.py:1052-1067`, `apps/dataops/backend/app/context_router.py:1070-1120`).

Frontend check: `apps/dataops/frontend/src` exists. The frontend uses backed context calls such as `/api/context/schema-impact/{system}`, `/api/context/celonis/process-data`, `/api/context/sap/purchase-orders`, `/api/context/alert/{id}/factors`, and `/api/context/cross-graph-insight/{alert_id}` (`apps/dataops/frontend/src/api.ts:224-301`, `apps/dataops/frontend/src/api.ts:251-272`). No active `/api/dataops/profiler/source/{source_id}` call was found in the scanned frontend output.

## Section 7: MAP Impact Assessment

| MAP Item | Status | Evidence | Recommendation |
|---|---|---|---|
| DI-1-PROFILER | ABSENT dedicated endpoint; PARTIAL reusable inputs | Missing profiler paths returned 404; no DataOps profiler route decorators found. Connectors expose raw/cache source data (`apps/dataops/backend/app/sap_connector.py:34-93`, `apps/dataops/backend/app/celonis_connector.py:34-78`), graph contract has Dataset/QualityRule nodes (`apps/dataops/backend/app/graph_contract.py:12-31`), and schema-impact/factors endpoints exist (`apps/dataops/backend/app/context_router.py:1050-1067`, `apps/dataops/backend/app/graph_queries.py:248-312`). | KEEP but REDUCE: implement a minimal source-profiler endpoint/service using existing connector/cache/graph data; defer tensor factor changes. |

## Section 8: Recommended DI-1 Implementation Scope

Because DI-1 is absent as a dedicated endpoint but partial inputs exist, the later implementation should be reduced to the missing profiler pieces:

1. Add a DataOps profiler router, likely `apps/dataops/backend/app/routers/dataops_profiler.py`, with prefix `/api/dataops/profiler` and endpoint `GET /source/{source_id}`. Mount it in `apps/dataops/backend/app/main.py`.
2. Add a small source-profiler service/helper in the DataOps app layer, not SDK core, because this is domain/backend behavior. Candidate file: `apps/dataops/backend/app/source_profiler.py`.
3. Source IDs should map initially to existing connector/cache data:
   - `sap_purchase_orders` -> `SAPConnector.get_purchase_orders()`.
   - `sap_supplier_invoices` -> `SAPConnector.get_supplier_invoices()`.
   - `sap_suppliers` -> `SAPConnector.get_suppliers()`.
   - `celonis_process_data` -> `CelonisConnector.get_process_data()` plus model/KPI metadata where useful.
4. Profile output should include:
   - source id, connector, live/cache/fixture source;
   - row/record count;
   - schema columns and inferred simple types;
   - null/missing rates per column;
   - completeness score;
   - freshness score where timestamp-like fields exist, otherwise `UNKNOWN`;
   - consistency score if simple type/null rules can be inferred;
   - drift status by comparing with `schema-impact` fixture data or prior profile baseline when available.
5. Reuse graph/query context where possible: `Dataset.schema_columns` and `QualityRule` graph contract semantics can inform expected schema and monitored quality rules (`apps/dataops/backend/app/graph_contract.py:12-31`), and `DataQualityAlert`/factor queries can enrich source reliability and freshness (`apps/dataops/backend/app/graph_queries.py:119-137`, `apps/dataops/backend/app/graph_queries.py:248-312`).
6. Do not include a DataOps preset factor change in DI-1 initial implementation. Current tensor is 6x5x6 (`copilot_sdk/scoring/presets/dataops.py:21-47`); adding `source_quality_score` requires tensor/bootstrap/frontend/scoring fixture migration and should be a separate MAP item.
7. Later tests should cover:
   - valid source IDs for SAP and Celonis cache-backed data;
   - unknown source ID 404;
   - type inference and null-rate calculation;
   - empty source behavior;
   - freshness unknown when no timestamp fields exist;
   - drift signal from schema-impact data where applicable;
   - route mount at `/api/dataops/profiler/source/{source_id}`;
   - no live network dependency when connectors are unconfigured.

Likely later files to change:

- `apps/dataops/backend/app/main.py` for router mount.
- `apps/dataops/backend/app/routers/dataops_profiler.py` new router.
- `apps/dataops/backend/app/source_profiler.py` new profiling helper/service.
- `apps/dataops/backend/tests/test_source_profiler.py` or equivalent DataOps backend tests.

No `copilot_sdk/scoring/presets/dataops.py` change is recommended for DI-1 initial scope.

## Appendix A: Search Terms / Commands Used

- Repo and guidance checks: `Get-Location`, `Test-Path .\CLAUDE.md`, `Get-Content .\CLAUDE.md -TotalCount 200`.
- Graph context: `Get-Content .\graphify-out\GRAPH_REPORT.md -TotalCount 80`.
- Required file checks: `Test-Path` for DataOps `main.py`, `context_router.py`, connectors, graph files, and `docs`.
- Source search: recursive `Select-String` over `apps\dataops\backend\app\*.py` for `profil|quality|schema|drift|completeness|freshness|null|column|source|trust|consistency`.
- Route decorators: recursive `Select-String` for `@.*get|@.*post`.
- Safe route probe: TestClient GET for `/api/dataops/profiler`, `/api/dataops/profiler/source/test-source`, `/api/context/quality`, `/api/dataops/source-profile`, `/api/context/source-quality`.
- Route inventory: TestClient app route dump for all `/api/` paths.
- Connector scans: full reads of `celonis_connector.py` and `sap_connector.py`.
- Graph scans: full reads of `graph_contract.py` and relevant `graph_queries.py` methods.
- Factor scan: runtime `DataOpsPreset` import plus source read of `copilot_sdk/scoring/presets/dataops.py`.
- Context router scan: route decorator list plus source reads around connector, schema-impact, factor, process, and metadata endpoints.
- Frontend optional scan: recursive `Select-String` over `apps\dataops\frontend\src` for `/api/|profiler|quality|source|schema|drift`.
