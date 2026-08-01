# Fix 4 — DataOps Fixture/Offline Substitution Closure

## §1 Executive Summary

DataOps has two distinct data classes that must remain separate:

1. Operational topology and alert context can be read from the DataOps AGE graph, with SQLite/fallback fixtures retained for explicitly disposable demo/test operation.
2. Decision-shaped history must come from the governed Decision graph in production. Local JSON and startup seed bundles may be used only by an explicit demo/test profile and must be labeled as sample data.

The current implementation is partially protected: configured AGE failures already raise from `DataOpsGraphClient._run_graph`, and `_all_context_decisions()` only selects JSON/seed Decision data when `_explicit_demo_mode()` is true. The remaining closure gaps are the fixture returns after a non-required graph result, fixture fallback after an AGE query returns no usable row, unscoped normalization of seed/live Decision records, the local alert-metadata Decision path, and unconditional startup bundle restore/fixture seeding for persistent stores.

The implementation will preserve SQLite and demo behavior, make production AGE failure surface as HTTP 503, keep operational metadata out of the Decision authority path, and gate all local Decision seeding behind the existing explicit controls (`DATAOPS_DEMO_MODE=1` or the existing test profile). No health-route behavior or DataOps domain naming changes are planned.

## §2 Fixture/Offline Path Inventory

### 2.1 `apps/dataops/backend/app/graph_queries.py`

The full file was read. `DataOpsGraphClient` resolves DataOps-specific graph configuration in `_load_topology_config()` (`:46-70`), loads JSON only through `_load_json()` (`:72-74`), and keeps fallback files under `data/fallback` (`:16-17`). The client marks AGE as required when the active backend is `age`/`dual_write` or an AGE client was injected (`:112-114`).

| Function/method | AGE path | Fixture/offline path | Fallback trigger |
|---|---|---|---|
| `get_pipelines` (`:141-166`) | Queries `PipelineSystem`/`FEEDS` and returns graph rows (`:142-164`). | Loads `fallback/pipelines.json` through `_pipelines()` (`:165`, `:591-592`). | `_run_graph()` returns `None`. |
| `get_alerts` (`:167-186`) | Queries `DataQualityAlert`/`AFFECTS` (`:168-185`). | Loads `fallback/alerts.json` (`:186`, `:594-595`). | `_run_graph()` returns `None`. |
| `get_system` (`:188-215`) | Queries one `PipelineSystem` and graph counts (`:190-211`). | Searches `_pipelines()` and returns `source=fixture` (`:212-215`). | `_run_graph()` returns `None`; a graph query with no row stays a graph “not found” response. |
| `get_alert` (`:217-225`) | Uses `_graph_alert_and_system()` (`:218-221`). | Searches `_alerts()` and returns `source=fixture` (`:222-225`). | Graph helper returns no pair. |
| `get_blast_radius` (`:227-273`) | Queries `AFFECTS` and `FEEDS` (`:228-272`). | `_fixture_blast_radius()` loads `blast_radius.json` (`:240`, `:245`, `:273`, `:384-416`). | Empty/malformed graph result or `_run_graph()` returns `None`. |
| `get_recurrence` (`:275-297`) | Uses graph alert lookup and `compute_recurrence()` when connected (`:278-282`). | Uses `_find_alert()` and `_fixture_recurrence()` (`:283-286`, `:467-488`). | No graph pair / no connected graph. |
| `get_factors` (`:299-363`) | Uses graph alert/system and graph factor computations (`:303-319`). | Computes all factors from fallback alerts/pipelines (`:320-325`, `:444-488`). | No graph pair. |
| `compute_impact_scope` (`:490-507`) | Queries `FEEDS` traversal (`:491-506`). | `_fixture_impact_scope()` (`:507`, `:444-452`). | `_run_graph()` returns `None`. |
| `compute_downstream_urgency` (`:509-527`) | Queries downstream SLA (`:510-525`). | `_fixture_downstream_urgency()` (`:527`, `:454-465`). | `_run_graph()` returns `None`. |
| `compute_recurrence` (`:529-548`) | Counts graph alerts (`:530-546`). | `_fixture_recurrence()` (`:548`, `:467-488`). | `_run_graph()` returns `None`. |
| `_run_graph` (`:550-564`) | Raises when required AGE is absent (`:551-554`) and re-raises query failures for required AGE (`:558-564`). | Returns `None` for a non-required/offline client and suppresses non-required query exceptions (`:551-564`). | Active backend is non-required or a non-required AGE call fails. |

The `get_*` and `compute_*` payloads are topology/alert/factor context, not governed `Decision` nodes. They nevertheless become evidence for context routes, so a configured AGE route must not silently label a local copy as graph evidence. The production-critical fixture substitutions are the `None` branches listed above; in SQLite or explicit demo/test mode they remain valid offline behavior.

### 2.2 `apps/dataops/backend/app/context_router.py`

The full file was read. The router is mounted under `/api/context` by `main.py:623-624`. The graph Decision source is `_graph_decisions()` (`:94-103`), which calls the configured store with `DOMAIN` and maps store/query failures to 503. `_explicit_demo_mode()` (`:106-108`) is true for `DATAOPS_DEMO_MODE=1` or an active pytest test. `_demo_context_decisions()` (`:110-121`) combines local alert metadata and `dataops_seed.json`, then stamps `provenance="sample"`.

Decision-shaped normalization occurs at `_normalize_live_decision()` (`:343-363`) and `_normalize_seed_decision()` (`:381-403`). The seed normalizer currently has Decision fields but no `domain`; live normalization also omits a domain field. `_all_context_decisions()` (`:431-437`) queries the graph first and selects local JSON/seed data only when the graph is empty and explicit demo/test mode is active.

| Endpoint/helper | Data source | Fixture fallback? | Decision-shaped? |
|---|---|---:|---:|
| `_graph_decisions` (`:94-103`) | Governed graph store, `get_all_decisions("dataops")` | No; errors become 503 | Yes, live graph |
| `_demo_context_decisions` (`:110-121`) | `alert_metadata.json` and `dataops_seed.json` | Yes, explicit demo/test only | Yes, sample |
| `/pipelines` (`:747-750`) | `DataOpsGraphClient` | Indirectly via graph client | No; topology |
| `/enterprise-health` (`:752-768`) | connectors plus graph client | Indirectly via graph client | No; health/status |
| `/alerts` (`:810-816`) | `DataOpsGraphClient` | Indirectly via graph client | No; alert context |
| `/alert-groups` (`:819-899`) | Local fallback topology/alerts | Yes, currently unconditional | No; alert grouping |
| `/system/{name}/history` (`:902-957`) | `_all_context_decisions()` | Demo/test local path only | Yes, summarized decisions |
| `/decisions` (`:960-987`) | `_all_context_decisions()` | Demo/test local path only | Yes |
| `/accuracy-by-category` (`:990-1029`) | `_all_context_decisions()` | Demo/test local path only | Decision-derived aggregate |
| `/centroid-history` (`:1032-1063`) | `_all_context_decisions()` | Demo/test local path only | Decision-derived aggregate |
| `/transformations`, `/bottleneck`, `/schema-impact`, `/process-timeline` (`:1066-1180`) | Local operational/process JSON | Yes | No; operational metadata |
| `/cross-graph-insight/{alert_id}` (`:1238-1266`) | Fallback alert cross-graph refs | Yes, unconditional | No; demo insight |
| `/apply-fix` (`:1324-1350`) | Story-calibrated local response | Yes, explicitly documented fixture response (`:1329`) | No; demo operation |
| `/system/{name}`, `/alert/{id}`, `/alert/{id}/deps`, `/recurrence`, `/factors` (`:1353-1379`) | `DataOpsGraphClient` | Indirectly via graph client | Topology/alert/factors, not Decision nodes |
| `/similar` (`:1382-1433`) | `dataops_seed.json` | Yes, unconditional | Decision-like historical matches; response already says `source=demo`, `provenance=sample` |
| `/process-signals/{system}` (`:1436-1465`) | `process_signals.json` plus connector health | Cache/fixture when connectors unavailable | No; operational process signal |
| `/audit-trail/{alert_id}` (`:1484-1600`) | Fallback alert plus `_all_context_decisions()` and evolution store | Alert/factor sections are local; Decision/outcome sections are graph or demo-gated metadata | Mixed: audit projection, with Decision/outcome steps derived from Decision-shaped data |
| `POST /alert-metadata` (`:1603-1615`) | Writes `alert_metadata.json` | Yes, local JSON | Yes: requires `decision_id` and stores action/outcome fields |
| `GET /alert-metadata` (`:1618-1620`) | Reads `alert_metadata.json` | Yes | Yes: exposes local Decision metadata |

The `POST /alert-metadata` write is not merely infrastructure metadata: it accepts `decision_id`, stores action/outcome fields, and is consumed by `_iter_metadata_decisions()` and the audit/Decision routes. It is therefore a Decision-shaped sample path. It must remain available for explicit demo/test operation, but must not be a production Decision authority. The existing `domain="dataops"` and `provenance="demo"` stamps are retained and strengthened by the explicit gate.

Operational JSON such as transformations, process timeline, process signals, and connector caches is not a Decision substitute. It remains local operational data; no Decision count or history route may treat it as a Decision.

### 2.3 `apps/dataops/backend/app/main.py`

The full file was read. `_graph_store()` (`:103-120`) loads the typed DataOps graph configuration and passes the selected backend to the common factory; there is no local AGE-to-SQLite rewrite in this file. `create_app()` selects the active graph store at `:532-543`.

| Startup step | Data source | Demo-gated? | Decision-shaped? |
|---|---|---:|---:|
| Resolve scoring DB (`:525-531`) | `CI_DATA_DIR` or local `dataops.db` | No | Storage location only |
| Select active graph store (`:532-543`) | Typed `DATAOPS_ACTIVE_*` config | No | Store selection |
| Restore demo bundle (`:562-570`) | `demo/dataops_demo_bundle.json` via `_restore_demo_bundle` | Only `DEMO_NO_RESEED=1` suppresses it today | Potentially yes; bundle restore writes graph/scoring state |
| Auto-seed fixture decisions/outcomes (`:406-427`, called `:570`) | `copilot_sdk/scoring/presets/dataops_seed.json` | Only `DEMO_NO_RESEED=1` suppresses it today | Yes: scorer `.score()` writes Decisions and `write_outcome()` writes Outcomes |
| Seed evolution event (`:430-465`, called `:571`) | Inline demo event | Only `DEMO_NO_RESEED=1` suppresses it today | No Decision; operational evolution sample |
| Restore L5 runtime state (`:572-581`) | Runtime persistence associated with selected store | No | Runtime state, not local Decision fixture seeding by itself |

The current startup path seeds/restores from local sources for any non-memory DB, including an AGE-selected store. That is the P2-DOPS-2 closure gap. The design gates bundle restore, fixture Decision/Outcome seed, and demo evolution seed behind the existing test/explicit demo boundary. Production AGE startup therefore does not read local Decision fixture files for seeding. Test/explicit demo startup retains the current bundle and fixture behavior, with seed metadata/provenance stamped by the existing DataOps seed metadata path.

## §3 Path Classification

| Type | Classified paths | Decision |
|---|---|---|
| TYPE 1 — legitimate AGE query | All graph branches that return `source="graph"` in `graph_queries.py`; `_graph_decisions()` and governed store reads in `context_router.py` | Keep. Preserve domain-scoped Cypher and 503 mapping. |
| TYPE 2 — AGE failure/fixture substitution | `graph_queries.py` `None`/fixture branches at `:165`, `:186`, `:212-215`, `:222-225`, `:240`, `:245`, `:273`, `:283-286`, `:320-325`, `:507`, `:527`, `:548`; suppression in `_run_graph` `:551-564` | In configured AGE mode, raise/propagate a typed 503 and never return fixture rows. In SQLite/offline mode, retain fixture results. |
| TYPE 3 — demo-only fixture | `_demo_context_decisions()` (`:110-121`), `/similar` (`:1382-1433`), documented demo `/apply-fix` (`:1324-1350`), cross-graph/local process and topology demo data | Keep, but make the explicit demo/test boundary the only Decision-shaped local-data boundary and retain `source`/`provenance` labels. |
| TYPE 4 — Decision-shaped JSON | `_normalize_seed_decision()` (`:381-403`), `_normalize_live_decision()` (`:343-363`), `_iter_metadata_decisions()` (`:275-287`) as consumed by `_demo_context_decisions()`, `POST/GET /alert-metadata` (`:1603-1620`), and startup `_seed_from_fixtures()` (`:340-403`) | Do not use local JSON as production authority. Add `domain="dataops"` to normalized records, retain explicit sample/demo provenance, and gate the alert-metadata read/write and startup seed behind demo/test. Live graph-normalized records are marked `domain="dataops"` and live provenance. |
| TYPE 5 — legitimate operational data | Connector caches, transformations, schema changes, process timeline/signals, alert grouping, health, and other non-Decision summaries | Keep. Add/retain provenance only where the existing response already identifies sample/cache data; do not convert these paths into Decision records. |

For TYPE 2, callers expect topology/alert/factor JSON. Returning 503 can make the affected graph-backed cards unavailable, but it is the correct failure contract when AGE is explicitly selected because a fixture response would falsely claim graph evidence. SQLite and explicit demo/test callers continue to receive the current response shape.

For TYPE 4, callers expect Decision history, accuracy, centroid, audit, or metadata. A production 503/graph-only response may leave those panels empty when no governed decisions exist, but it prevents local JSON from becoming authoritative evidence. The frontend already treats non-2xx responses as errors and several API helpers intentionally convert failures to `null`.

## §4 Frontend Impact

The source-only frontend scan (excluding `node_modules`) found the following consumers:

| Consumer | Endpoint(s) | Expected data | 503 behavior/error state |
|---|---|---|---|
| `src/api.ts:130-168` | All shared GET/POST helpers | Typed JSON payload | `apiGet`/`apiPost` throw on non-2xx; `safeApiGet`/`safeRawApiGet` (`:138-155`) convert failure to `null`. |
| `src/api.ts:198-208` | `/api/context/pipelines`, `/alerts`, `/alert-groups` | Topology and alert lists/groups | Promise failure propagates to caller; shared wrappers provide the common boundary. |
| `src/api.ts:339-406` | Accuracy, centroid, transformations, bottleneck, schema impact, alert detail, audit, blast radius, recurrence, factors | Context panels and Decision-derived summaries | Non-2xx throws; callers can use the existing safe helpers/loading states. |
| `src/api.ts:457-486` | System history and Decision Explorer | Historical Decisions | Non-2xx throws; no fixture-shaped success is assumed. |
| `src/components/CrossGraphInsightCard.tsx:146-173` | Cross-graph insight and alert groups | Cross-graph insight | Explicit error state at `:126-136`; missing groups fall back to a deterministic empty/demo insight. |
| `src/components/ProcessTimelinePanel.tsx:10-43` | Process timeline | Operational timeline | Explicit loading, error, and empty states at `:57-81`. |
| `src/components/AcquisitionPanel.tsx:31-70` | Data acquisition recommendations | Recommendations | Explicit loading and error states. Not affected by graph 503. |
| `src/components/NLQueryPanel.tsx:10-36` | DataOps query POST | Answer/evidence | Explicit loading and error states. |
| `src/api.ts:619` and audit/decision UI callers | `/api/context/alert-metadata` | Demo metadata write | Error propagates; demo operation remains available under explicit demo/test. |

No frontend schema removal is required. A 503 is an existing failure shape at the HTTP layer, and the affected direct components have loading/error states. The implementation will not add a new frontend fallback that could recreate the backend substitution problem. A frontend build is still a Phase 2 verification step.

## §5 Demo Mode Design

### DD1 — Boundary

Use the existing DataOps boundary rather than inventing a second flag:

- `DATAOPS_DEMO_MODE=1` is the explicit runtime demo switch, already recognized by `context_router._explicit_demo_mode()` (`:106-108`).
- The existing test profile (`PYTEST_CURRENT_TEST` / pytest-loaded profile) remains a disposable test boundary so backend tests can use local fixtures without mutating production behavior.
- `DEMO_NO_RESEED=1` remains an independent suppression control and continues to skip bundle restore and fixture seeding (`main.py:565-566`).
- `DATAOPS_ACTIVE_GRAPH_BACKEND=sqlite` retains local SQLite/offline behavior. `DATAOPS_ACTIVE_GRAPH_BACKEND=age` is the graph-required production/AGE path.

### DD2 — Demo behavior

In explicit demo or test mode, existing fallback JSON and `dataops_seed.json` may be read. Every Decision-shaped sample returned by context routes carries `domain="dataops"`, `provenance="sample"`, and a source identifying demo/seed origin. Startup demo/test seeding may continue, and its existing DataOps domain/outcome arguments are preserved.

### DD3 — Production AGE behavior

When the typed active backend is AGE, an unavailable AGE client, query exception, or graph-required no-data fallback raises a 503 from the graph route. It must never return `source="fixture"` or `provenance="sample"` as a successful graph-backed response. No local Decision fixture file is read for startup seeding.

### DD4 — SQLite behavior

SQLite remains a legitimate local/offline backend. Its fallback topology/alert/factor behavior remains unchanged for development and test operation. This is not treated as a production AGE failure because the selected backend is explicitly SQLite.

### DD5 — Existing fixtures

Existing fallback JSON, seed bundles, and demo responses remain in place. They are gated and labeled; they are not deleted. This preserves demos and existing test fixtures while closing the substitution path.

## §6 Design Decisions

1. **Production AGE failure → 503:** Yes. Required AGE failures must be visible to the HTTP caller; no fixture success response is allowed.
2. **Explicit demo mode:** Yes. Reuse `DATAOPS_DEMO_MODE=1`, the existing test profile, and `DEMO_NO_RESEED` suppression. Do not broaden the boundary to arbitrary environment absence.
3. **Local Decision-shaped metadata:** Keep only as explicit demo/test data, stamp `domain="dataops"` and `provenance="demo"`/`"sample"`, and exclude it from production Decision reads. A governed GraphStore write is not introduced in this fix because the endpoint is explicitly a demo metadata path and its existing response contract must remain stable.
4. **Non-Decision metadata:** Keep local operational JSON and cache data. Preserve its source/cache/demo labels; do not expose it as Decision evidence.
5. **Startup seeding:** Demo/test-only for bundle restore, fixture Decision/Outcome seed, and demo evolution seed. Production AGE and production SQLite do not auto-seed local Decision fixtures. Runtime L5 restoration remains separate.
6. **Frontend:** Rely on existing non-2xx handling and loading/error states. No response field is removed, and no frontend fixture fallback is added.
7. **AGE-safe queries:** Keep all existing read-only, domain-scoped Cypher. The implementation adds failure gating without introducing write Cypher.

These decisions resolve the classification: all TYPE 2 and TYPE 4 paths have an explicit disposition, and no source/test edit is required to complete the design phase.

## §7 Implementation Plan

Changes are ordered by production impact and performed one file at a time, with a full re-read and verification after each file.

### Impact 1 — graph failure contract

1. **`apps/dataops/backend/app/graph_queries.py`**
   - Preserve graph results and SQLite fallback results.
   - Add a single AGE-required failure boundary so fixture returns after `_run_graph()` are replaced by HTTP 503 (or the existing required exception is translated at the route boundary) only when AGE is selected.
   - Cover empty/malformed graph result branches in `get_blast_radius` so configured AGE cannot fall through to `_fixture_blast_radius`.
   - Keep `graph_source`, health semantics, read-only validation, and fallback files unchanged for SQLite/demo/test.
   - Blast radius: all `/api/context` graph topology and factor routes; direct `DataOpsGraphClient` tests.
   - Tests: new `test_dataops_fixture_closure.py` production AGE failure, no fixture response, and demo fixture cases; existing graph query tests.

### Impact 2 — Decision provenance and local metadata gate

2. **`apps/dataops/backend/app/context_router.py`**
   - Add `domain="dataops"` to live and seed normalized Decision records.
   - Keep sample provenance on demo/seed decisions and ensure all local Decision-shaped data is selected only by explicit demo/test mode.
   - Gate `POST/GET /alert-metadata` as demo/test-only; retain the current `domain` and `provenance` fields in stored/returned metadata.
   - Do not change non-Decision operational routes or their schemas.
   - Blast radius: Decision Explorer, accuracy, centroid, system history, audit trail, similar-alert demo route, alert metadata UI.
   - Tests: new closure tests for production no-sample Decision responses and metadata provenance/non-Decision separation; existing context tests.

### Impact 3 — startup authority boundary

3. **`apps/dataops/backend/app/main.py`**
   - Add an internal demo/test predicate aligned with `_explicit_demo_mode`/`_resolve_profile`.
   - Run bundle restore, `_auto_seed_if_needed`, and `_seed_demo_evolution_events_if_needed` only in explicit demo/test mode, still honoring `DEMO_NO_RESEED=1`.
   - Ensure production AGE startup cannot read the local seed file for Decision creation. Preserve selected store construction and L5 runtime restoration.
   - Add/retain sample provenance in startup seed metadata without changing Decision IDs/domain.
   - Blast radius: app startup, persistence/resume tests, demo bundle tests, AGE startup matrix.
   - Tests: new closure tests for no production fixture seed and demo seed with provenance; existing startup/seed tests.

### Impact 4 — verification

4. Run `mypy` on each changed Python file before its targeted pytest command. Run the new closure test file, DataOps backend suite, frontend build, and SDK DataOps-targeted tests. If a new failure appears, revert the current file’s change and stop as required by the task rules.

## §8 Risk Analysis

| Risk | What could go wrong | Mitigation |
|---|---|---|
| Demo mode broken by fixture removal | Demo/test routes become empty or 503 | Keep fixture files and SQLite paths; gate rather than delete; test explicit demo and pytest profiles. |
| Frontend receives 503 without usable UI | Graph cards render blank or unhandled errors | Preserve HTTP 503 contract, verify existing `apiGet`/safe helpers and direct component error states, run frontend build. |
| Operational metadata misclassified | Transform/process/cache data disappears or is treated as a Decision | Classify by consumer and fields; only gate `decision_id`/action/outcome metadata; leave operational JSON routes unchanged. |
| Startup fails without AGE configured | Local app loses useful SQLite/demo behavior | Keep typed SQLite default/offline path; gate only local Decision seeding in production; retain explicit demo/test seeding. |
| AGE empty result still leaks fallback | A graph query with no row returns a fixture success | Cover both `_run_graph() is None` and empty/malformed AGE result branches, especially blast radius. |
| Tests accidentally enable demo mode | Pytest profile hides production behavior | New tests explicitly set production/AGE versus demo/test modes and assert source/provenance; no mock/monkeypatch. |
| DataOps domain drift | Normalized sample or live Decision lacks domain | Stamp `domain="dataops"` at both live and seed normalization and preserve store query domain. |

## §9 Reading Log

Read in full before design write:

- `copilot-sdk/docs/implementation_plans/jm_gap_closure_plan_v1.md` — Fix 4 and global constraints.
- `copilot-sdk/docs/design/jm_implementation_review_part1b_v1.md` — P1-DOPS-1, P1-DOPS-2, P2-DOPS-2, P2-DOPS-4 findings.
- `copilot-sdk/CLAUDE.md` — repository edit, verification, AGE-safe query, and test rules.
- `copilot-sdk/apps/dataops/backend/app/graph_queries.py` — all 604 lines.
- `copilot-sdk/apps/dataops/backend/app/context_router.py` — all 1620 lines.
- `copilot-sdk/apps/dataops/backend/app/main.py` — all 676 lines.
- `copilot-sdk/apps/dataops/backend/app/graph_status.py` — active backend/demo/test configuration semantics.
- DataOps frontend source consumers in `apps/dataops/frontend/src/api.ts`, `AcquisitionPanel.tsx`, `CrossGraphInsightCard.tsx`, `NLQueryPanel.tsx`, and `ProcessTimelinePanel.tsx`.

No source or test file was edited during Phase 1. The only allowed write is this design document.

**DESIGN_READY: YES**
