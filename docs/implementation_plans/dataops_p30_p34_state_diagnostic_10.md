# DataOps P30-P34 State Diagnostic 10

Date: 2026-06-06
Model: gpt-5.3
Task Type: Diagnostic document creation only; no source code changes
Repo: copilot-sdk
Diagnostic Scope: DataOps / DI layer state for P30/P32, P34, P42, P43, and P44
Prior Diagnostics Read: sdk_backend_endpoint_map_diagnostic_02.md; dataops_backend.md; dataops_frontend.md; dataops_governed_graph_semantics_plan.md; dataops_preset_plan.md

## Executive Summary

- DataOps app found: YES
- DataOps app path: `apps\dataops`
- DI-1 SourceProfiler verdict: FULL
- DI-2 IntelligenceMap verdict: FULL
- DI-3 NL Query verdict: FULL
- DI-5 Combination Discovery verdict: SUPPLEMENT
- DI-6 Graph Enrichment verdict: SUPPLEMENT
- Biggest blocker: no canonical `SourceProfiler` or equivalent DI-1 service was found; direct DataOps backend source searches found zero matches for `SourceProfiler`, `source_profile`, `profile_source`, `schema_score`, `completeness_score`, `freshness_score`, or `format_compliance`.
- Recommended next prompt: DI-1 SourceProfiler implementation, followed by DI-2 IntelligenceMap implementation.

## Path Resolution

- CLAUDE_SDK value: `C:\Users\baner\CopyFolder\IOT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
- Repo path used: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
- DataOps app path: `apps\dataops`
- DataOps main.py path: `apps\dataops\backend\app\main.py`
- DataOps backend app path: `apps\dataops\backend\app`
- DataOps tests path: `apps\dataops\backend\tests`
- Report path: `docs\implementation_plans\dataops_p30_p34_state_diagnostic_10.md`
- Prior diagnostics found: `sdk_backend_endpoint_map_diagnostic_02.md`, `dataops_backend.md`, `dataops_frontend.md`, `dataops_governed_graph_semantics_plan.md`, `dataops_preset_plan.md`

Path checks showed `copilot-sdk`, `CLAUDE.md`, `apps\dataops`, `copilot_sdk`, `docs`, `docs\implementation_plans`, and `sdk_backend_endpoint_map_diagnostic_02.md` exist. `apps\di` and `apps\data_ops` do not exist. The environment path differs in `IOT_thoughts` casing, so the known workspace path was used.

## CLAUDE.md Relevant Notes

- Docs are aspirational unless verified against code; current source and tests are authoritative.
- Do not use git.
- Prefer existing SDK public interfaces and avoid leaking domain internals into SDK APIs.
- Normal verification instructions mention pytest, but this diagnostic explicitly forbids running tests.
- Graph architecture notes say graph-related work should be read against existing architecture before changes.

## Part 1 - DataOps App File Tree

```text
__init__.py (0KB)
ae_router.py (21.9KB) TODO_OR_STUB_SIGNAL_COUNT=2
celonis_connector.py (5.6KB)
context_router.py (57.7KB) TODO_OR_STUB_SIGNAL_COUNT=14
evolution\__init__.py (0.3KB)
evolution\evolver_config.py (3.6KB)
graph_contract.py (1.5KB)
graph_queries.py (21.1KB) TODO_OR_STUB_SIGNAL_COUNT=31
graph_status.py (13KB)
main.py (15.2KB) TODO_OR_STUB_SIGNAL_COUNT=7
routers\dataops_status.py (6KB) TODO_OR_STUB_SIGNAL_COUNT=20
sap_connector.py (5.1KB)
seed_graph.py (10.7KB)
```

## Graph-Relevant Files Found

| File | Size | Graph Relevance | TODO/Stub Signals |
| --- | ---: | --- | --- |
| `apps\dataops\backend\app\graph_contract.py` | 1.5KB | Formal DataOps graph contract with Decision, Pipeline, Dataset, QualityRule, Alert, ProcessModel, Activity, Transformation nodes. Evidence: lines 8-31. | None observed in tree output. |
| `apps\dataops\backend\app\graph_queries.py` | 21.1KB | Read/query client for DataOps operational graph, imports ci-platform AGEClient when present. Evidence: lines 38-46, 56-75. | 31 TODO/stub/mock/fixture signals from tree output; includes fixture fallback behavior. |
| `apps\dataops\backend\app\graph_status.py` | 13KB | Active AGE GraphStore wrapper and `/api/dataops/graph/status`. Evidence: lines 152-223 and 332-334. | None observed in tree output. |
| `apps\dataops\backend\app\seed_graph.py` | 10.7KB | Deterministic graph seed plan; creates nodes and edges from fallback files. Evidence: lines 32-67, 74-83, 142-181. | None observed in tree output. |
| `apps\dataops\backend\app\main.py` | 15.2KB | Creates SQLiteGraphStore, can select active graph store, mounts graph/status and SDK routers. Evidence: lines 338-392. | 7 TODO/stub/mock/fixture signals from tree output. |

## Part 2 - DI-1 SourceProfiler

Files inspected:
- file: repository-wide source-profiler candidate search
- purpose: locate `SourceProfiler`, `source_profile`, `profile_source`, score fields, or equivalent profiler modules.
- evidence: direct DataOps backend app count for `SourceProfiler|source_profile|profile_source|schema_score|completeness_score|freshness_score|format_compliance` returned `0`.

Related but insufficient signals:
- `apps\dataops\backend\app\graph_queries.py:281-284` returns a `source_reliability` factor from system or alert data.
- `apps\dataops\backend\app\graph_queries.py:296-299` returns a `data_freshness` factor from alert data.
- `apps\dataops\backend\app\context_router.py:1361-1383` exposes `/similar` parameters including `source_reliability` and `data_freshness`.

Score coverage:
- schema score: absent as a canonical profiler output. There is schema-impact UI/context logic, but no `schema_score` profiler evidence.
- completeness score: absent.
- freshness score: partial factor only; no SourceProfiler computation/persistence.
- format-compliance score: absent in DataOps app source search.
- persistence: absent for source profiles.
- endpoint: absent for source profile creation/list/retrieval.
- downstream wiring: absent; factors consume fixture/graph signals, not persisted profile records.

Verdict: FULL
Remaining effort: 2-3 days
Likely files for later implementation: `apps\dataops\backend\app\source_profiler.py`, a DataOps router module, `apps\dataops\backend\app\main.py`, and focused backend tests.

## Part 3 - DI-2 IntelligenceMap

Files inspected:
- file: repository-wide IntelligenceMap/routing search
- purpose: locate `IntelligenceMap`, `FactorRouter`, `source_to_factor`, `route_source`, or equivalent routing.
- evidence: direct DataOps backend app count for `IntelligenceMap|intelligence_map|FactorRouter|source_to_factor|route_source|DataRoute` returned `0`.

Adjacent but insufficient signals:
- `apps\dataops\backend\app\ae_router.py:154-173` contains `_explicit_source_copilot` and `_source_copilot`, which classify AE rule lineage/source copilot metadata.
- `apps\dataops\backend\app\main.py:268-269` seeds evolution metadata with `"source_copilot": "S2P"` and a source rule.

Routing coverage:
- source to copilot: partial lineage metadata only; no DI-2 map from profiled data sources to copilots.
- source to factor: absent.
- uses SourceProfiler output: absent because SourceProfiler is absent.
- endpoint: absent.
- frontend/visualization signal: not proven by backend source inspection.

Verdict: FULL
Remaining effort: 2 days after DI-1
Likely files for later implementation: `apps\dataops\backend\app\intelligence_map.py`, DataOps DI router, `main.py`, and tests that validate profile-to-copilot/factor routing.

## Part 4 - DataOps Router and Endpoint Inventory

Router registrations:
- router/factory: `create_scoring_router`; prefix: `/api`; tags: SDK scoring router; evidence: `apps\dataops\backend\app\main.py:358-365`.
- router/factory: `create_transfer_router`; prefix: SDK default; tags: SDK transfer router; evidence: `apps\dataops\backend\app\main.py:366`.
- router/factory: `create_conservation_router`; prefix: `/api`; tags: SDK conservation router; evidence: `apps\dataops\backend\app\main.py:367-373`.
- router/factory: `create_evolution_router`; prefix: SDK default; tags: SDK evolution router; evidence: `apps\dataops\backend\app\main.py:374-380`.
- router/factory: `mount_self_computation_router`; prefix: SDK default; tags: SDK self-computation router; evidence: `apps\dataops\backend\app\main.py:381`.
- router/factory: `context_router_module.router`; prefix: `/api/context`; tags: context router; evidence: `apps\dataops\backend\app\main.py:382-383`.
- router/factory: `create_ae_router`; prefix: `/api/ae`; tags: AE router; evidence: `apps\dataops\backend\app\main.py:384-390`.
- router/factory: `dataops_graph_status_router`; prefix: `/api/dataops/graph`; tags: graph status; evidence: `apps\dataops\backend\app\main.py:391` and `graph_status.py:332-334`.
- router/factory: `dataops_status_router`; prefix: `/api/dataops`; tags: dataops status; evidence: `apps\dataops\backend\app\main.py:392`.

Endpoint inventory:
- method: GET; path: `/recommendation/{alert_id}`; function: AE recommendation; feature area: AE; evidence: `apps\dataops\backend\app\ae_router.py:381`.
- method: GET; path: `/impact`; function: AE impact; feature area: AE; evidence: `apps\dataops\backend\app\ae_router.py:422`.
- method: GET; path: `/pattern-origin`; function: pattern origin; feature area: AE lineage; evidence: `apps\dataops\backend\app\ae_router.py:426`.
- method: GET; path: `/rule-lifecycle`; function: rule lifecycle; feature area: AE; evidence: `apps\dataops\backend\app\ae_router.py:478`.
- method: GET; path: `/operational-rules`; function: operational rules; feature area: AE; evidence: `apps\dataops\backend\app\ae_router.py:502`.
- method: GET; path: `/incident`; function: incident; feature area: AE; evidence: `apps\dataops\backend\app\ae_router.py:530`.
- method: GET; path: `/conservation-history`; function: conservation history; feature area: AE/conservation; evidence: `apps\dataops\backend\app\ae_router.py:543`.
- method: GET; path: `/transfer-status`; function: transfer status; feature area: transfer; evidence: `apps\dataops\backend\app\ae_router.py:547`.
- method: GET; path: `/pipelines`; function: pipelines; feature area: context; evidence: `apps\dataops\backend\app\context_router.py:701`.
- method: GET; path: `/enterprise-health`; function: enterprise health; feature area: connectors; evidence: `apps\dataops\backend\app\context_router.py:706`.
- method: GET; path: `/sap/purchase-orders`; function: SAP purchase orders; feature area: connector; evidence: `apps\dataops\backend\app\context_router.py:722`.
- method: GET; path: `/celonis/process-data`; function: Celonis process data; feature area: connector; evidence: `apps\dataops\backend\app\context_router.py:732`.
- method: GET; path: `/alerts`; function: alerts; feature area: context; evidence: `apps\dataops\backend\app\context_router.py:761`.
- method: GET; path: `/alert-groups`; function: alert groups; feature area: context; evidence: `apps\dataops\backend\app\context_router.py:770`.
- method: GET; path: `/system/{name}/history`; function: system history; feature area: analytics; evidence: `apps\dataops\backend\app\context_router.py:853`.
- method: GET; path: `/decisions`; function: decisions; feature area: analytics; evidence: `apps\dataops\backend\app\context_router.py:939`.
- method: GET; path: `/accuracy-by-category`; function: category accuracy; feature area: analytics; evidence: `apps\dataops\backend\app\context_router.py:969`.
- method: GET; path: `/centroid-history`; function: centroid history; feature area: analytics; evidence: `apps\dataops\backend\app\context_router.py:1011`.
- method: GET; path: `/transformations/{system}`; function: transformations; feature area: graph/context; evidence: `apps\dataops\backend\app\context_router.py:1045`.
- method: GET; path: `/bottleneck/{system}`; function: bottleneck; feature area: process mining; evidence: `apps\dataops\backend\app\context_router.py:1056`.
- method: GET; path: `/schema-impact/{system}`; function: schema impact; feature area: schema context, not DI-1 profiler; evidence: `apps\dataops\backend\app\context_router.py:1089`.
- method: GET; path: `/process-timeline`; function: process timeline; feature area: process mining; evidence: `apps\dataops\backend\app\context_router.py:1109`.
- method: GET; path: `/cross-graph-insight/{alert_id}`; function: cross graph insight; feature area: DI-5-adjacent; evidence: `apps\dataops\backend\app\context_router.py:1217-1245`.
- method: POST; path: `/apply-fix`; function: apply fix; feature area: action workflow; evidence: `apps\dataops\backend\app\context_router.py:1303`.
- method: GET; path: `/system/{name}`; function: system detail; feature area: context; evidence: `apps\dataops\backend\app\context_router.py:1332`.
- method: GET; path: `/alert/{id}`; function: alert detail; feature area: context; evidence: `apps\dataops\backend\app\context_router.py:1337`.
- method: GET; path: `/alert/{id}/deps`; function: dependencies; feature area: graph query; evidence: `apps\dataops\backend\app\context_router.py:1346`.
- method: GET; path: `/alert/{id}/recurrence`; function: recurrence; feature area: graph query; evidence: `apps\dataops\backend\app\context_router.py:1351-1353`.
- method: GET; path: `/alert/{id}/factors`; function: factors; feature area: factor explanation; evidence: `apps\dataops\backend\app\context_router.py:1356-1358`.
- method: GET; path: `/similar`; function: similar alerts; feature area: vector search/scoring; evidence: `apps\dataops\backend\app\context_router.py:1361-1383`.
- method: GET; path: `/process-signals/{system}`; function: process signals; feature area: process/correlation; evidence: `apps\dataops\backend\app\context_router.py:1410-1439`.
- method: GET; path: `/audit-trail/{alert_id}`; function: audit trail; feature area: audit; evidence: `apps\dataops\backend\app\context_router.py:1458`.
- method: POST; path: `/alert-metadata`; function: metadata write; feature area: context metadata; evidence: `apps\dataops\backend\app\context_router.py:1577`.
- method: GET; path: `/alert-metadata`; function: metadata read; feature area: context metadata; evidence: `apps\dataops\backend\app\context_router.py:1589`.
- method: GET; path: `/api/dataops/graph/status`; function: graph status; feature area: graph status; evidence: `apps\dataops\backend\app\graph_status.py:332-334`.
- method: GET; path: `/api/dataops/health`; function: health alias; feature area: status; evidence: `apps\dataops\backend\app\routers\dataops_status.py:19`.
- method: GET; path: `/api/dataops/celonis/status`; function: Celonis status; feature area: connector status; evidence: `apps\dataops\backend\app\routers\dataops_status.py:44`.
- method: GET; path: `/api/dataops/sap/status`; function: SAP status; feature area: connector status; evidence: `apps\dataops\backend\app\routers\dataops_status.py:49`.
- method: GET; path: `/api/dataops/enterprise-health`; function: enterprise health alias; feature area: connector status; evidence: `apps\dataops\backend\app\routers\dataops_status.py:54`.

SDK routers:
- create_scoring_router: YES, mounted at `/api`.
- create_conservation_router: YES, mounted at `/api`.
- create_evolution_router: YES.
- create_transfer_router: YES.
- mount_self_computation_router: YES.

No source profiling, intelligence map, NL query, combination discovery, or graph enrichment endpoint name was found. The app-local endpoint decorator count is 39.

## Part 5 - DataOps Test Coverage

Test inventory:
- file: `test_bundle_wiring.py`; test count: 4; topics: demo bundle restore and GraphStore behavior.
- file: `test_dataops_backend.py`; test count: 108; topics: health, context endpoints, AE, audit, decisions, accuracy, transformations, process timeline, cross-graph insight, SDK scoring/conservation/evolution.
- file: `test_dataops_graph_status.py`; test count: 13; topics: active AGE configuration, graph status, active AGE write semantics, generic graph env guardrails.
- file: `test_dataops_graph.py`; test count: 9; topics: DataOps graph contract and seed integrity.
- file: `test_dataops_status.py`; test count: 6; topics: DataOps status aliases.
- file: `test_enterprise_connectors.py`; test count: 26; topics: SAP/Celonis connector cache and endpoint parsing.
- file: `test_evolution_dataops.py`; test count: 6; topics: DataOps evolver config and variants endpoint.
- file: `test_graph_queries.py`; test count: 16; topics: fixture fallback, graph-connected factors, blast radius, query read-only checks.
- file: `test_transfer_status.py`; test count: 7; topics: transfer status payload.

Endpoint coverage:
- endpoint: `/api/context/cross-graph-insight/{alert_id}`; test: `test_cross_graph_insight_returns_triple_correlation`, `test_cross_graph_insight_has_combined_impact`; evidence: `apps\dataops\backend\tests\test_dataops_backend.py:933-945`.
- endpoint: `/api/dataops/graph/status`; test: `test_graph_status_default_sqlite`; evidence: `apps\dataops\backend\tests\test_dataops_graph_status.py:29-43`.
- endpoint: `/api/score` and `/api/learn`; test: `test_score_via_sdk`, `test_learn_returns_reward`; evidence: `apps\dataops\backend\tests\test_dataops_backend.py:1104-1117`.
- endpoint: `/api/context/alert/{id}/factors`; test: `test_factor_auto_fill`; evidence: `apps\dataops\backend\tests\test_dataops_backend.py:210-213`.

Mock/fixture setup:
- file: `apps\dataops\backend\tests\conftest.py`; signal: fixture data copied and `GRAPH_DSN` cleared; evidence: lines 22-64 in test output.
- file: `apps\dataops\backend\tests\test_graph_queries.py`; signal: fixture fallback and mocked client tests; evidence: test names at lines 103-296.
- file: `apps\dataops\backend\tests\test_dataops_graph_status.py`; signal: active AGE env monkeypatch setup; evidence: lines 367-373 in test output.

Coverage implications:
- DI-1 covered: NO. No SourceProfiler tests were found.
- DI-2 covered: NO. No IntelligenceMap tests were found.
- DI-3 covered: NO. No NL query tests were found.
- DI-5 covered: PARTIAL. Cross-graph insight and correlation-ish fixture tests exist, but no DI-5 combination discovery/value tests.
- DI-6 covered: PARTIAL. Graph contract, seed, active AGE status, and read-only graph query tests exist; no DI-6 enrichment service tests were found.

## Part 6 - DI-3 NL Query

Signals found:
- file: repository-wide Python search
- line: not applicable
- signal: no `NLQuery`, `natural_language`, `nl_query`, `ask_data`, `query_engine`, or `semantic_query` implementation found outside unrelated confidence/query terms.
- evidence: DI-3 search returned only incidental confidence/question/query strings and no dedicated NL query class, endpoint, or service.

Verdict: FULL
Remaining effort: 2+ days, likely after DI-1/DI-2 so query answers can include source profile/trust.
Likely files for later implementation: DataOps NL query service/router, main router registration, tests, and optional SDK shared abstractions.

## Part 7 - DI-5 Combination Discovery

Signals found:
- file: `apps\dataops\backend\app\context_router.py`
- line: 1217-1245
- signal: `/cross-graph-insight/{alert_id}` combines `process_signal`, `erp_impact`, `root_cause`, `combined_impact`, and `sources_used`.
- evidence: lines 1223-1245 build response from `cross_graph_refs` and combined impact.

Signals found:
- file: `apps\dataops\backend\app\context_router.py`
- line: 1199-1214
- signal: combined impact computes daily/monthly/annualized cost and deterministic fixture confidence.
- evidence: lines 1204-1214 calculate cost fields and confidence.

Signals found:
- file: `apps\dataops\backend\app\context_router.py`
- line: 1410-1439
- signal: `/process-signals/{system}` returns `signals`, `metrics`, `variant`, and `correlation`.
- evidence: lines 1429-1438 include `correlation` from process signal fixture data.

Verdict: SUPPLEMENT
Remaining effort: 1.5-2 days
Likely files for later implementation: a real `combination_discovery.py` service, DataOps DI router endpoint, SourceProfiler/IntelligenceMap integration, graph relationship reads, and tests for value/predictive improvement.

Rationale: there is cross-graph/correlation scaffolding, but no `CombinationDiscovery` implementation, no profiled source reliability input, and no general combination valuation/predictive improvement API.

## Part 8 - DI-6 Graph Enrichment

Signals found:
- file: `apps\dataops\backend\app\graph_contract.py`
- line: 8-31
- signal: formal DataOps graph contract defines node and edge types.
- evidence: `DATAOPS_GRAPH_CONTRACT` defines Decision, Pipeline, Dataset, QualityRule, Alert, ProcessModel, Activity, Transformation and edges such as DECIDED_ON, PRODUCES, CONSUMES, MONITORS, DETECTED_IN, CONTAINS, FOLLOWS, TRIGGERED_BY.

Signals found:
- file: `apps\dataops\backend\app\seed_graph.py`
- line: 32-67
- signal: deterministic node/edge append helpers.
- evidence: `_add_node` and `_add_edge` create node/edge dictionaries.

Signals found:
- file: `apps\dataops\backend\app\seed_graph.py`
- line: 74-83, 142-181
- signal: seed graph loads fallback alerts, pipelines, transformations, Celonis data, creates Dataset/Transformation relationships, and adds CONSUMES/PRODUCES edges.
- evidence: lines 76-83 load files; lines 142-162 create source datasets and CONSUMES edges; lines 163-181 create target dataset and PRODUCES edge.

Signals found:
- file: `apps\dataops\backend\app\graph_queries.py`
- line: 38-46, 56-75
- signal: operational graph client can use ci-platform AGEClient if `GRAPH_DSN` is set and otherwise falls back to fixtures.
- evidence: `_load_age_client_class` imports `ci_platform.graph.age_client.AGEClient`; `DataOpsGraphClient` initializes graph/fixture state.

Signals found:
- file: `apps\dataops\backend\app\graph_status.py`
- line: 152-223, 235-261
- signal: active AGE GraphStore wrapper supports governed decision writes, but not DI-6 source graph enrichment writes.
- evidence: `DataOpsActiveAGEGraphStore.write_decision` writes governed decisions; `create_dataops_active_graph_store` creates an AGE GraphStore only under guarded config.

Verdict: SUPPLEMENT
Remaining effort: 1-2 days after DI-1/DI-2 decisions
Likely files for later implementation: graph enrichment service/router, integration with `graph_contract.py` and `seed_graph.py` patterns, active GraphStore/AGE path, and tests for relationship creation.

Rationale: graph contract, seeded relationships, query client, and active AGE/SQLite infrastructure exist. A DI-6 enrichment layer that consumes SourceProfiler/IntelligenceMap outputs and writes discovered source relationships was not found.

## Final MAP Table for DataOps

| Prompt | Verdict | Effort | Evidence | Next Action |
| --- | --- | --- | --- | --- |
| P30/P32 DI-1-SOURCE-PROFILER | FULL | 2-3d | DataOps app direct search returned 0 SourceProfiler/profile/score symbols; only factors like `source_reliability` and `data_freshness` exist in `graph_queries.py:281-299`. | Implement canonical SourceProfiler first. |
| P34 DI-2-INTELLIGENCE-MAP | FULL | 2d | DataOps app direct search returned 0 IntelligenceMap/routing symbols; AE source_copilot metadata exists but is lineage, not DI-2 routing. | Implement IntelligenceMap after DI-1. |
| P42 DI-3-NL-QUERY | FULL | 2+d | No dedicated NL query service/router found in DI-3 search. | Design after DI-1/DI-2. |
| P43 DI-5-COMBINATION-DISCOVERY | SUPPLEMENT | 1.5-2d | Cross-graph insight and process correlation scaffolding exist at `context_router.py:1199-1245` and `1410-1439`, but no CombinationDiscovery service. | Extend scaffolding into DI-5 service/API. |
| P44 DI-6-GRAPH-ENRICHMENT | SUPPLEMENT | 1-2d | Graph contract/seed/query/AGE status exist at `graph_contract.py:8-31`, `seed_graph.py:32-67`, `graph_queries.py:38-75`, `graph_status.py:152-223`; no DI-6 enrichment writer found. | Add graph enrichment service after profiler/map decisions. |

## Architecture Guardrails for Later Implementation

- DI-1 SourceProfiler should be the canonical source reliability/profile layer, not a one-off route helper.
- DI-2 IntelligenceMap should consume SourceProfiler output rather than duplicate profiling.
- Do not create app-local graph infrastructure if SDK/platform GraphStore or AGEClient already provides the canonical path.
- Do not add fixture-only Data Intelligence paths where live profiled source data is expected.
- Preserve DataOps reset/demo integrity.
- Keep DI layer reusable for cross-copilot P42-P44 work.
- Later implementation must include behavioral tests, not just source-string checks.

## Diagnostic Limitations

- This diagnostic does not run tests.
- This diagnostic does not validate runtime API behavior.
- This diagnostic does not inspect frontend UI unless files are discovered through searches.
- This diagnostic does not implement DI-1/DI-2/DI-3/DI-5/DI-6.
- Verdicts are source-inspection scope verdicts only.

## Recommended Next Step

Smallest next prompt: DI-1 SourceProfiler implementation. P34/P42/P43/P44 should not be treated as complete until source profile records and score semantics exist.
