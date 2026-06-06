# DataOps Governed Graph Semantics Plan

Date: 2026-06-01

## Purpose

This plan decides whether DataOps can adopt the governed GraphStore
Decision/Outcome pattern used by S2P, Purchasing, and Trading.

The answer is: DataOps can proceed with a scoped scorer-only active AGE
adoption milestone, but only with explicit semantics guards that keep
operational graph behavior separate from scorer Decision/Outcome storage.

This is a design and discovery plan only. It does not switch DataOps to AGE,
change runtime behavior, modify frontend/Playwright, change demo.py, perform
migration/backfill, implement EvidenceReceipt mapping, or mutate `soc_graph`.

## Current Inventory

### App And Storage Construction

- Entrypoint: `copilot-sdk/apps/dataops/backend/app/main.py`.
- Domain: `dataops`.
- SQLite database filename: `dataops.db`.
- SQLite path resolution:
  - explicit `db_path`;
  - then `CI_DATA_DIR / "dataops.db"`;
  - then app-local `apps/dataops/backend/data/dataops.db`.
- Scorer graph store construction:
  - `_graph_store(db_path)` returns `SQLiteGraphStore(str(db_path),
    domain="dataops", decision_id_prefix="DOPS-")`;
  - penalty ratio is set to `10.0`.
- Scorer construction:
  - `FreshScorerProxy("dataops", scoring_db, _graph_store)`;
  - shared `/api/score`, `/api/learn`, `/api/history`, `/api/health`,
    `/api/fingerprint`, and `/api/trajectory` come from
    `create_scoring_router(...)`.
- Conservation construction:
  - `create_conservation_router("dataops", state_provider=scorer_proxy)`.
- Evolution construction:
  - `create_evolution_router(graph_store_factory=lambda:
    _graph_store(scoring_db), domain="dataops", ...)`.
- Self-computation:
  - `mount_self_computation_router(app, _graph_store(scoring_db))`.
- AE routes:
  - `create_ae_router(evolution_store_factory=lambda:
    _graph_store(scoring_db), domain="dataops")`.
- Context router:
  - receives only an evolution-store factory via
    `context_router_module.set_evolution_store_factory(...)`.

### Scorer Write Paths

The governed scorer memory path is the same class of path used by Purchasing
and Trading:

- `/api/score` writes a DataOps Decision through `CompoundingScorer.score(...)`.
- `/api/learn` writes Outcome/status through `CompoundingScorer.learn(...)`.
- startup fixture seeding can write Decisions and Outcomes through
  `scorer.score(...)` and `graph_store.write_outcome(...)`.
- startup demo evolution seeding can write EvolutionEvent through
  `graph_store.save_evolution_event(...)`.

These are GraphStore responsibilities and are candidates for active AGE
test-mode adoption.

### Operational Graph And Context Routes

DataOps also has a separate operational graph meaning:

- `DataOpsGraphClient` in `app/graph_queries.py` reads `PipelineSystem` and
  `DataQualityAlert` graph concepts from an AGE client when `GRAPH_DSN` is set,
  or from fixtures otherwise.
- `DataOpsGraphClient` is used by:
  - `GET /health`;
  - context endpoints for pipelines, alerts, systems, blast radius, recurrence,
    and auto-computed factors;
  - AE recommendation matching.
- `DataOpsGraphClient` is read-only by construction. It rejects Cypher strings
  containing mutating clauses via `READ_ONLY_FORBIDDEN`.
- `app/seed_graph.py` builds a deterministic operational graph with labels such
  as `Pipeline`, `Dataset`, `QualityRule`, `Alert`, `ProcessModel`,
  `Activity`, `Transformation`, and an operational `Decision` label connected
  to `Alert` by `DECIDED_ON`.
- `app/graph_contract.py` describes the operational graph contract and includes
  `Decision`, `Pipeline`, `Dataset`, `QualityRule`, `Alert`, `ProcessModel`,
  `Activity`, and `Transformation`.

Operational graph concepts must not be silently treated as Protocol v2 scorer
Decision/Outcome records.

### Other DataOps Write-Like Routes

These routes are not governed scorer Decision/Outcome writes:

- `POST /api/context/alert-metadata` writes to `alert_metadata.json`.
- `POST /api/context/apply-fix` returns a deterministic fixture/story response
  and does not write scorer Decisions.
- Data import/connector/cache behavior reads fixtures or connector status.

They must remain outside first active AGE scorer adoption unless separately
mapped.

### Existing Tests And E2E

- Backend tests exist under `copilot-sdk/apps/dataops/backend/tests`.
- Graph query tests cover fixture fallback, read-only Cypher filtering, and
  mocked AGE graph reads.
- DataOps Playwright tests exist under `copilot-sdk/e2e/dataops`.
- Discovery run for this plan:
  - `python -m pytest apps/dataops/backend/tests/test_dataops_backend.py
    apps/dataops/backend/tests/test_graph_queries.py
    apps/dataops/backend/tests/test_dataops_status.py -q --timeout=120`
  - Result: 130 passed.

## Semantics Boundary

### A. Scorer Governed Memory

These are governed memory records and can use the common GraphStore/Protocol v2
pattern:

- Decision
- Outcome
- status transition
- verified count `V`
- factor vector
- recommendation/action
- scorer confidence/probabilities
- centroid checkpoint
- evolution event written by GraphStore

For first DataOps adoption, active AGE must apply only to this scorer governed
memory path.

### B. Operational DataOps Graph

These are operational graph/context concepts and are not first-cutover scorer
records:

- Pipeline
- PipelineSystem
- DataQualityAlert
- Alert
- Dataset
- QualityRule
- ProcessModel
- Activity
- Transformation
- connector status
- process timeline
- schema impact
- blast radius
- cross-graph insight
- alert metadata JSON
- apply-fix fixture response

These may later map to DomainContext, Observation, EvidenceReceipt, or a
separate operational graph projection, but they must not be silently written as
Protocol v2 scorer Decisions.

### C. Cross-Domain Context

These need explicit partitioning before a final common-architecture proof:

- DomainContext for operational systems, alerts, and process state.
- Observation for data quality signals and process telemetry.
- EvolutionEvent for rule proposals, shadow starts, promotions, and rejections.
- TransferPattern for patterns crossing from S2P/SOC/Trading/Purchasing into
  DataOps or vice versa.
- EvidenceReceipt for audit-chain material.

The current DataOps AE routes already expose source-copilot and source-rule
fields. That is useful context, but not a complete cross-copilot proof.

## Adoption Decision

DataOps scorer Decision/Outcome storage is separable enough to proceed with a
bundled scorer-only active AGE implementation milestone.

Rationale:

- The scorer GraphStore is constructed in `main.py` through `_graph_store(...)`
  and `FreshScorerProxy`.
- Operational graph reads are constructed separately through
  `DataOpsGraphClient`.
- `DataOpsGraphClient` uses `GRAPH_DSN`, while the future scorer active backend
  must use `DATAOPS_ACTIVE_*`.
- Operational graph queries are read-only and have existing read-only tests.
- `alert-metadata` and `apply-fix` are explicit non-scorer write-like routes.

This is a scoped readiness decision, not a product graph cutover approval.

The next implementation must include an internal semantics guard gate before
active AGE wiring. If those guard tests fail, stop before enabling active AGE.

## Required Semantics Guards

Before DataOps active AGE scorer adoption, implement and test:

- `DATAOPS_ACTIVE_*` config must select only the scorer GraphStore backend.
- Generic `GRAPH_*` must not switch the scorer backend.
- `GRAPH_DSN` may continue to affect `DataOpsGraphClient` operational graph
  reads, but status must label it as operational/read-only and not scorer active
  backend.
- `DataOpsGraphClient` must not receive or use `DATAOPS_ACTIVE_AGE_DSN`.
- `DataOpsGraphClient` must remain read-only.
- Operational labels (`PipelineSystem`, `DataQualityAlert`, `Pipeline`,
  `Alert`, `Activity`, `Transformation`) must not be written by scorer active
  AGE adoption.
- `POST /api/context/alert-metadata` must remain JSON/file-backed or explicitly
  out of first active AGE scope.
- `POST /api/context/apply-fix` must not write scorer Decisions.
- startup fixture seeding must be disabled or explicitly guarded when active AGE
  is enabled, as in Purchasing/Trading.

These are blocker tests inside the next bundled implementation prompt, not a
separate runtime feature.

## Allowed And Forbidden AGE Writes

### Allowed In First DataOps Active AGE Milestone

Only under explicit `DATAOPS_ACTIVE_*` test-mode env:

- governed Decision written by `/api/score`;
- governed Outcome/status written by `/api/learn`;
- centroid/checkpoint writes required by scorer learning;
- EvolutionEvent writes only if they already use the scorer GraphStore and are
  explicitly covered by tests.

### Forbidden In First Milestone

- product graph writes;
- `soc_graph` writes;
- historical migration/backfill;
- EvidenceReceipt writes;
- PipelineSystem/DataQualityAlert/Pipeline/Alert/Activity/Transformation writes;
- operational seed graph projection;
- connector/SAP/Celonis writes;
- alert metadata AGE writes;
- apply-fix AGE writes;
- cross-copilot proof writes.

## Environment Model

DataOps scorer active AGE uses app-specific env only:

- `DATAOPS_ACTIVE_GRAPH_BACKEND=sqlite|age`
- `DATAOPS_ACTIVE_AGE_DSN`
- `DATAOPS_ACTIVE_AGE_GRAPH`
- `DATAOPS_ACTIVE_AGE_DOMAIN=dataops`
- `DATAOPS_ACTIVE_AGE_TEST_MODE=0|1`
- optional future `DATAOPS_SHADOW_AGE`

Rules:

- unset or `sqlite` means SQLite is authoritative;
- generic `GRAPH_*` does not switch DataOps scorer backend;
- `GRAPH_DSN` remains operational graph input for `DataOpsGraphClient` only;
- AGE requires explicit DSN, graph, domain, and test-mode flag;
- domain must equal `dataops`;
- `soc_graph` is rejected;
- blank graph is rejected;
- `protocol_v2_test*` is allowed only with
  `DATAOPS_ACTIVE_AGE_TEST_MODE=1`;
- product-like mode is status/config only unless separately reviewed;
- active AGE and shadow AGE conflict;
- status and logs must redact DSN/password/token/secret values.

## Status Endpoint Requirements

Add `/api/dataops/graph/status` in the implementation milestone.

Required fields should mirror S2P/Purchasing/Trading:

- `active_backend`
- `requested_backend`
- `sqlite_authoritative`
- `age_active`
- `active_graph_name`
- `graph_kind`
- `active_domain`
- `active_test_mode`
- `ignored_generic_graph_env`
- `operational_graph_enabled`
- `operational_graph_source`
- `operational_graph_read_only`
- `operational_graph_dsn_configured` as boolean only
- `migration_backfill_status=not_in_scope`
- `receipt_mapping_status=excluded_first_cutover`
- `evidence_receipt_mapping_status=design_required`
- `historical_visibility_warning`
- `rollback_instructions`
- `new_decision_outcome_writes_ready`
- `full_audit_memory_ready=false`
- `migration_complete=false`
- `evidence_receipt_ready=false`
- readiness flags
- warnings

The endpoint must be read-only and must not construct a live AGE store just to
report status. It must not expose DSN/password/token values.

## Rollback Model

Rollback for DataOps scorer adoption is:

- unset `DATAOPS_ACTIVE_GRAPH_BACKEND` or set it to `sqlite`;
- remove active AGE env or leave it inert under `sqlite`;
- restart DataOps.

Rollback does not:

- delete AGE records;
- copy AGE records into SQLite;
- reconcile alert metadata JSON;
- reconcile operational graph nodes;
- change `GRAPH_DSN` behavior for `DataOpsGraphClient`.

Proof must show:

- active AGE score/learn writes first;
- reconstructed SQLite/default app writes score/learn to SQLite;
- status reports SQLite after rollback;
- AGE-only decision ids are not magically present in SQLite;
- operational graph routes remain available and separate.

## Implementation Recommendation

Proceed with a bundled DataOps governed graph milestone, with stop gates:

### Gate 0: Semantics Guard Baseline

- inventory current store/scorer/operational graph construction;
- run targeted DataOps backend and graph query tests;
- add tests proving `GRAPH_DSN` affects only `DataOpsGraphClient`, not scorer
  backend selection;
- add tests proving `DATAOPS_ACTIVE_AGE_DSN` does not alter operational graph
  client construction.

Stop if scorer and operational graph construction cannot be separated without a
broad rewrite.

### Gate 1: Config And Status

- add `app/graph_status.py`;
- add `/api/dataops/graph/status`;
- default SQLite preserved;
- generic `GRAPH_*` ignored for scorer active backend;
- operational graph state reported separately;
- guard invalid backend, missing DSN, missing/blank graph, `soc_graph`,
  `protocol_v2_test*` without test mode, non-dataops domain, and shadow
  conflict;
- redact secrets.

### Gate 2: Active AGE Test Mode For Scorer Only

- use the Purchasing/Trading active AGE adapter pattern;
- route `/api/score` to governed Decision writes in `protocol_v2_test*`;
- route `/api/learn` to Outcome/status writes;
- keep response shape unchanged;
- preserve one-outcome invariant;
- skip startup fixture seeding while active AGE is enabled;
- do not redirect `DataOpsGraphClient`.

### Gate 3: Operational Graph No-Contamination Tests

- `GET /health` graph source remains operational/fixture or `GRAPH_DSN` based;
- `/api/context/pipelines`, `/api/context/alerts`, `/api/context/alert/{id}`,
  `/api/context/alert/{id}/deps`, `/api/context/alert/{id}/factors`, and
  `/api/ae/recommendation/{alert_id}` do not create scorer Decisions;
- `POST /api/context/alert-metadata` writes only alert metadata JSON;
- `POST /api/context/apply-fix` does not write scorer Decisions;
- `PipelineSystem`/`DataQualityAlert` queries remain read-only.

### Gate 4: Rollback Proof

- active AGE fake-store/test-store writes score and learn;
- reconstruct SQLite/default app;
- score and learn succeed on SQLite;
- status reports SQLite;
- no hidden reconciliation.

### Gate 5: Guarded Live AGE

Skip unless explicit env:

- `DATAOPS_ACTIVE_LIVE_AGE_TEST=1`
- `DATAOPS_ACTIVE_GRAPH_BACKEND=age`
- `DATAOPS_ACTIVE_AGE_TEST_MODE=1`
- `DATAOPS_ACTIVE_AGE_GRAPH=protocol_v2_test`
- `DATAOPS_ACTIVE_AGE_DOMAIN=dataops`
- `DATAOPS_ACTIVE_AGE_DSN=postgresql://postgres:postgres@127.0.0.1:5433/soc_copilot?connect_timeout=5`

Live test must verify:

- score creates AGE Decision with same decision_id;
- learn writes Outcome/status;
- operational graph/read routes do not create Decisions;
- status reports active AGE test mode;
- duplicate outcome invariant;
- no `soc_graph`;
- unique ids and no broad deletion.

### Gate 6: Playwright Smoke

Run targeted DataOps Playwright smoke only if the stack is reachable or safely
started. Do not let Playwright block backend milestone unless it exposes a real
backend/runtime issue.

## Test Plan

Backend:

- default SQLite unchanged;
- active AGE config guards;
- generic `GRAPH_*` ignored for scorer;
- operational `GRAPH_DSN` separated from scorer active env;
- status endpoint redacts secrets;
- score writes Decision under active AGE test mode;
- learn writes Outcome/status;
- duplicate learn rejected;
- conservation counts use active scorer GraphStore;
- operational graph routes do not create scorer Decisions;
- alert-metadata/apply-fix do not create scorer Decisions;
- rollback proof;
- DataOps backend suite;
- graph query suite.

Live AGE:

- guarded skip-by-default live active AGE test;
- no `soc_graph`;
- no broad `dataops` domain deletion;
- accumulated unique rows documented.

Playwright:

- targeted DataOps flow smoke after backend gates;
- optional graph status API assertion if live stack is restarted with new code.

Blocker tests:

- `GRAPH_DSN` operational graph mode does not imply scorer active AGE;
- `DATAOPS_ACTIVE_*` scorer active mode does not imply operational graph mode;
- DataOpsGraphClient remains read-only under both env combinations.

## Scope Guards

- No product graph cutover.
- No historical migration/backfill.
- No EvidenceReceipt mapping.
- No SOC mutation.
- No Trading/Purchasing/S2P changes.
- No frontend/Playwright changes in the backend implementation milestone.
- No demo.py changes.
- No operational graph projection in first scorer active AGE milestone.
- No product/external claim.

## P3 Backlog

- Design DomainContext mapping for PipelineSystem/DataQualityAlert/Pipeline,
  Alert, Activity, and Transformation.
- Design Observation mapping for data quality signals and process telemetry.
- Design EvidenceReceipt mapping for audit-trail and apply-fix evidence.
- Design historical migration/backfill for DataOps scorer Decisions and
  operational graph history.
- Decide whether operational graph should eventually live in
  `governed_copilot_graph`, an app-specific graph, or a read-only projection.
- Add demo.py DataOps AGE flags only after scorer adoption and operational
  semantics are accepted.

## Final Decision

DataOps is ready for a bundled scorer-only active AGE implementation milestone
with semantics guards as internal stop gates.

DataOps is not ready for product graph cutover, operational graph migration,
EvidenceReceipt mapping, historical backfill, or final cross-copilot product
claim.
