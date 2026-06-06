# SDK Apps Governed Graph Adoption Plan

Date: 2026-06-01

## Purpose

This plan defines how Trading, Purchasing, and DataOps should adopt the common
governed graph architecture using S2P as the reference implementation.

The target architecture is one governed live judgment-memory graph for SOC,
S2P, Trading, Purchasing, and DataOps. PostgreSQL+AGE is the canonical product
graph direction. SQLite remains the default local/test backend and the rollback
fallback until each app passes explicit gates.

This is a design plan only. It does not implement app migration, route changes,
frontend changes, demo changes, SOC mutation, or cross-copilot proof.

## Current accepted gates

- AGE Protocol v2 adapter: accepted.
- SOC projection gate: PASS_WITH_P3.
- GraphStore factory: accepted.
- S2P AGE shadow Phase 1 and Phase 2: accepted.
- S2P preview/read no-Decision-write fixer: accepted.
- S2P active AGE test-mode backend and parallel backend gate: accepted.
- S2P active AGE Playwright workers=1 and command-level workers=4 smoke:
  accepted.
- S2P product graph allow-list/status hardening: accepted.
- S2P active new Decision/Outcome writes under explicit `S2P_ACTIVE_*` env:
  accepted.
- S2P historical migration/backfill: not accepted.
- S2P EvidenceReceipt mapping: not accepted.
- S2P product/external claim: not safe.

## S2P reference pattern

The S2P milestone gives the adoption pattern, not a blanket permission to switch
other apps:

- Default runtime remains SQLite.
- Active AGE is app-specific and explicit, never driven by generic `GRAPH_*`.
- `soc_graph` is forbidden for non-SOC writes.
- `protocol_v2_test*` graphs require test mode.
- Product-like graph names must be allow-listed. The reviewed current product
  candidate is `governed_copilot_graph`.
- Active AGE and shadow AGE cannot run in the same app runtime.
- Score routes write governed Decision records.
- Outcome/learn routes write Outcome/status transitions and preserve the
  one-outcome invariant.
- Preview/read routes do not create Decisions.
- Status endpoints report active backend, graph kind, domain, redacted graph
  settings, migration/backfill status, EvidenceReceipt status, rollback
  instructions, and readiness flags.
- Rollback is config switch plus restart. It does not delete AGE data, copy AGE
  data back to SQLite, or perform hidden reconciliation.
- Acceptance is for new Decision/Outcome writes only unless a later plan covers
  EvidenceReceipt and historical migration/backfill.

The same boundaries must be preserved for Trading, Purchasing, and DataOps.

The implementation path should not repeat the S2P micro-loop. Use bundled
app milestones with internal stop gates:

- stop before active AGE if default SQLite or config guards regress;
- stop before Playwright if backend active AGE or rollback proof fails;
- stop before product-like graph work if test-mode active AGE is not accepted;
- carry P3s into backlog unless they affect correctness or data safety.

## Trading inventory and plan

### Inventory

- App entrypoint: `copilot-sdk/apps/trading/backend/app/main.py`.
- Domain string: `trading`.
- SQLite database filename: `trading.db`.
- SQLite path behavior: `_resolve_scoring_db()` uses an explicit path, then
  `CI_DATA_DIR / "trading.db"`, then the app-local data directory.
- Current graph store construction: `_graph_store(db_path)` returns
  `SQLiteGraphStore(str(db_path), domain="trading", decision_id_prefix="TRD-")`
  and applies the Trading penalty ratio.
- Current scorer construction: `FreshScorerProxy("trading", scoring_db,
  _graph_store)` is passed into the shared `create_scoring_router(...)`.
- Primary write routes: shared SDK scoring router under `/api`, including score
  and outcome/learn semantics from the common backend router.
- App-specific write-like routes:
  - `/api/trading/social/score-as` calls `scorer_proxy.score(...)`.
  - `/api/trading/webhook/tradingview` can auto-score when `auto_score` is set.
  - startup fixture seeding can call `scorer.score(...)` and
    `graph_store.write_outcome(...)`.
- Read/preview-like routes:
  - `/api/trading/prescore` deliberately avoids `scorer.score()`.
  - journal, evidence, analytics, correlation, regime, promotion, VIX timing,
    broker, data import, and context routes read graph or fixture state.
- Conservation/status surfaces:
  - shared `/api/conservation/status`.
  - `/api/trading/conservation-breakdown` is a simplified proxy and points to
    the shared conservation route as authoritative.
- Evolution/transfer surfaces:
  - `create_transfer_router(scorer_proxy)`.
  - `create_evolution_router(..., graph_store_factory=lambda:
    _graph_store(scoring_db), domain="trading", ...)`.
- Self-computation: `mount_self_computation_router(app, _graph_store(scoring_db))`.
- Frontend/e2e coverage: broad Trading Playwright coverage exists under
  `copilot-sdk/e2e/trading`.
- demo.py startup: Trading is a non-AGE SDK app today. `demo.py` passes
  `CI_DATA_DIR`; backend owns the `trading.db` filename.

### Risks

- Store construction is spread across scorer proxy, evolution router,
  self-computation router, and read-oriented routers. Adoption must centralize a
  selected graph-store provider or it will create split-brain behavior.
- `social/score-as`, webhook auto-score, and startup seeding are additional
  Decision/Outcome write paths beyond the common scoring route.
- Prescore is intentionally read-only/hypothetical and must stay no-Decision.
- Trading has the largest app-specific route surface, so it should not be first
  unless Purchasing proves the common pattern.

### Recommended strategy

Trading should use factory adoption with SQLite default first, then direct active
AGE test-mode. It does not need an S2P-style shadow-first path unless parity
tests expose route-specific ambiguity.

Milestone gates:

1. Add app-specific active graph config/status helpers with default SQLite and
   no runtime switch.
2. Replace direct `_graph_store(scoring_db)` lambdas with one selected
   graph-store provider so scorer, evolution, conservation, self-computation,
   journal/evidence, and app-specific write routes share the same backend.
3. Add guard tests for `TRADING_ACTIVE_*` env, ignored generic `GRAPH_*`,
   `soc_graph` rejection, test graph requirements, allow-list, active/shadow
   conflict, and DSN redaction.
4. Add active AGE test-mode fake-store and live guarded tests for score,
   outcome/learn, social score-as, webhook auto-score, conservation counts, and
   rollback to SQLite.
5. Add read-safety tests for prescore and read routes proving no Decision write.
6. Add Playwright smoke with active AGE test mode after backend gates pass.
7. Accept Trading only for new Decision/Outcome writes. EvidenceReceipt and
   historical migration/backfill remain separate.

## Purchasing inventory and plan

### Inventory

- App entrypoint: `copilot-sdk/apps/purchasing/backend/app/main.py`.
- Domain string: `purchasing`.
- SQLite database filename: `purchasing.db`.
- SQLite path behavior: `_resolve_scoring_db()` uses an explicit path, then
  `CI_DATA_DIR / "purchasing.db"`, then the app-local data directory.
- Current graph store construction: `_graph_store(db_path)` returns
  `SQLiteGraphStore(str(db_path), domain="purchasing",
  decision_id_prefix="PUR-")` and applies the Purchasing penalty ratio.
- Current scorer construction: `FreshScorerProxy("purchasing", scoring_db,
  _graph_store)` is passed into the shared `create_scoring_router(...)`.
- Primary write routes: shared SDK scoring router under `/api`, including score
  and outcome/learn semantics from the common backend router.
- Startup fixture seeding can call `scorer.score(...)` and
  `graph_store.write_outcome(...)`.
- Read/preview-like routes:
  - context routes expose today-summary, items, weather, waste history, and
    order metadata.
  - evidence routes expose summary, decisions, audit trail, conservation proof,
    health, and status.
- Conservation/status surfaces:
  - shared `/api/conservation/status`.
  - Purchasing evidence status surfaces compute read-only summaries.
- Evolution/transfer surfaces:
  - `create_transfer_router(scorer_proxy)`.
  - `create_evolution_router(...)`.
  - context router receives an evolution store factory.
- Self-computation: `mount_self_computation_router(app, _graph_store(scoring_db))`.
- Frontend/e2e coverage: Purchasing Playwright coverage exists under
  `copilot-sdk/e2e/purchasing`.
- demo.py startup: Purchasing is a non-AGE SDK app today. `demo.py` passes
  `CI_DATA_DIR`; backend owns the `purchasing.db` filename.

### Risks

- Similar to Trading but smaller. Direct store factories still must be unified
  before any active backend switch.
- Startup seeding writes Decisions/Outcomes and must be explicit in active AGE
  mode. It should be disabled, made idempotent, or separately guarded before any
  active AGE product-like run.
- Evidence endpoints are not Protocol v2 EvidenceReceipt. They must not be
  treated as receipt mapping.

### Recommended strategy

Purchasing should go first. It is the closest SDK app to the common scoring
pattern with the smallest app-specific graph surface.

Recommended path:

1. One bundled implementation prompt with internal stop gates:
   - shared app config/status helper;
   - Purchasing app status endpoint;
   - default SQLite preservation tests;
   - active AGE test-mode wiring;
   - fake-store and guarded live score/outcome/learn tests;
   - read-safety tests for evidence/context/status routes;
   - rollback proof;
   - targeted Playwright smoke if the live stack is available.
2. Product-like allow-list/status hardening only after active test-mode gates
   pass.
3. Product graph implementation remains blocked until the Purchasing milestone
   is reviewed.

Shadow-first is not required unless direct active AGE test-mode shows parity
gaps.

## DataOps inventory and plan

### Inventory

- App entrypoint: `copilot-sdk/apps/dataops/backend/app/main.py`.
- Domain string: `dataops`.
- SQLite database filename: `dataops.db`.
- SQLite path behavior: `_resolve_scoring_db()` uses an explicit path, then
  `CI_DATA_DIR / "dataops.db"`, then the app-local data directory.
- Current graph store construction: `_graph_store(db_path)` returns
  `SQLiteGraphStore(str(db_path), domain="dataops",
  decision_id_prefix="DOPS-")` and applies the DataOps penalty ratio.
- Current scorer construction: `FreshScorerProxy("dataops", scoring_db,
  _graph_store)` is passed into the shared `create_scoring_router(...)`.
- Primary write routes: shared SDK scoring router under `/api`, including score
  and outcome/learn semantics from the common backend router.
- Startup fixture seeding can call `scorer.score(...)`,
  `graph_store.write_outcome(...)`, and `graph_store.save_evolution_event(...)`.
- Read/preview-like routes:
  - context routes expose pipelines, enterprise health, SAP/Celonis data,
    alerts, alert groups, system history, decisions, accuracy by category,
    centroid history, transformations, bottlenecks, schema impact, process
    timeline, cross-graph insight, audit trail, apply-fix, and alert metadata.
  - AE routes expose recommendations, impact, pattern origin, rule lifecycle,
    operational rules, incidents, conservation history, and transfer status.
  - DataOps status routes expose `/api/dataops/health`, connector status, and
    enterprise health aliases.
- Conservation/status surfaces:
  - shared `/api/conservation/status`.
  - DataOps-specific health/status routes include connector and graph signals.
- Evolution/transfer surfaces:
  - `create_transfer_router(scorer_proxy)`.
  - `create_evolution_router(...)`.
  - DataOps startup seeds demo evolution events.
- Self-computation: `mount_self_computation_router(app, _graph_store(scoring_db))`.
- External/adjacent graph behavior:
  - `DataOpsGraphClient` is used in the health endpoint and may use AGE or
    fixture/fallback graph data.
  - `graph_queries.py`, graph contract files, and seed graph utilities model
    Pipeline, Alert, Activity, and Transformation concepts separately from the
    scorer GraphStore.
- Frontend/e2e coverage: DataOps Playwright coverage exists under
  `copilot-sdk/e2e/dataops`.
- demo.py startup: DataOps is a non-AGE SDK app today, but demo.py also contains
  AGE helper logic for DataOps graph seeding. That must not be confused with
  Protocol v2 active GraphStore cutover.

### Risks

- DataOps has two graph-adjacent meanings:
  - governed Decision/Outcome graph writes through the scorer GraphStore; and
  - operational graph/context data for pipelines, alerts, systems, and process
    intelligence.
- SOC projection already classified DataQualityAlert/PipelineSystem projection
  as requiring explicit non-SOC domain partition metadata. Labels alone are not
  enough.
- DataOps may need DomainContext, Observation, EvolutionEvent, and later
  EvidenceReceipt mapping design before a broad product claim.
- The `apply-fix` and `alert-metadata` routes are not equivalent to governed
  Decision/Outcome writes and should not be silently migrated.

### Recommended strategy

DataOps should share the governed graph for scorer Decision/Outcome writes, but
it should be delayed until after Purchasing and Trading.

Recommended path:

1. DataOps-specific blocker/design slice that separates scorer GraphStore
   cutover from operational graph/client behavior.
2. Define DomainContext partition rules for Pipeline, Alert,
   DataQualityAlert-like, PipelineSystem-like, Activity, and Transformation
   concepts.
3. Prove that DataOpsGraphClient, graph query routes, AE routes, connector
   status, and operational graph seed data are not silently redirected by scorer
   GraphStore cutover.
4. Adopt factory/status helpers with SQLite default.
5. Add active AGE test-mode only for scorer Decision/Outcome writes.
6. Keep operational graph/context behavior read-only or fixture-backed until a
   separate DomainContext/Observation plan is reviewed.

## Batch vs sequential recommendation

Do not implement Trading, Purchasing, and DataOps active AGE cutovers in one
runtime-change batch.

Batch only the common, low-risk infrastructure inside the first Purchasing
implementation milestone:

- shared app active graph config parser shape;
- shared status payload schema;
- shared DSN redaction helpers;
- shared guard tests;
- shared fake active AGE test helpers;
- shared Playwright smoke template;
- demo.py design, not implementation.

Implement app adoption sequentially:

1. Purchasing first, because it has the smallest route surface and closest match
   to the shared scoring pattern. Its first implementation should be bundled,
   not split into status-only and active-AGE prompts, provided internal stop
   gates are honored.
2. Trading second, because it shares the SDK scoring pattern but has more
   app-specific score/read surfaces.
3. DataOps third, after a blocker/design slice clarifies operational graph
   semantics.

This compresses the S2P loop without hiding app-specific risk.

## Common environment model

Use app-specific environment variables. Generic `GRAPH_*` variables must not
switch SDK app active backends.

The parser should be a shared helper that accepts an explicit app prefix and
domain, for example `load_app_active_graph_config(prefix="PURCHASING",
domain="purchasing")`. It must read only that prefix for active app cutover
settings. Generic `GRAPH_*` may be reported as ignored by status endpoints, but
must not select an active backend.

Trading:

- `TRADING_ACTIVE_GRAPH_BACKEND=sqlite|age`
- `TRADING_ACTIVE_AGE_DSN`
- `TRADING_ACTIVE_AGE_GRAPH`
- `TRADING_ACTIVE_AGE_DOMAIN=trading`
- `TRADING_ACTIVE_AGE_TEST_MODE=0|1`
- Optional future `TRADING_SHADOW_AGE`, if a shadow phase is chosen.

Purchasing:

- `PURCHASING_ACTIVE_GRAPH_BACKEND=sqlite|age`
- `PURCHASING_ACTIVE_AGE_DSN`
- `PURCHASING_ACTIVE_AGE_GRAPH`
- `PURCHASING_ACTIVE_AGE_DOMAIN=purchasing`
- `PURCHASING_ACTIVE_AGE_TEST_MODE=0|1`
- Optional future `PURCHASING_SHADOW_AGE`, if a shadow phase is chosen.

DataOps:

- `DATAOPS_ACTIVE_GRAPH_BACKEND=sqlite|age`
- `DATAOPS_ACTIVE_AGE_DSN`
- `DATAOPS_ACTIVE_AGE_GRAPH`
- `DATAOPS_ACTIVE_AGE_DOMAIN=dataops`
- `DATAOPS_ACTIVE_AGE_TEST_MODE=0|1`
- Optional future `DATAOPS_SHADOW_AGE`, if a shadow phase is chosen.

Rules for all three:

- Unset or `sqlite` means SQLite is authoritative.
- AGE requires explicit DSN, graph, domain, and test-mode flag.
- Domain must match the app exactly: `trading`, `purchasing`, or `dataops`.
- `soc_graph` is rejected.
- Blank graph is rejected.
- `protocol_v2_test*` is allowed only when `*_ACTIVE_AGE_TEST_MODE=1`.
- Product-like mode requires `*_ACTIVE_AGE_TEST_MODE=0` and an allow-listed
  reviewed graph name.
- `governed_copilot_graph` is the current shared product graph candidate.
- Active AGE and shadow AGE conflict.
- Raw DSN, password, token, and secret values must not appear in status,
  diagnostics, logs, or test assertion messages.
- Direct construction of the config object must enforce the same domain,
  `soc_graph`, test-mode, product allow-list, and active/shadow conflict guards
  as env parsing.

## Common status/diagnostics model

Each app should expose an app-local graph status endpoint:

- `/api/trading/graph/status`
- `/api/purchasing/graph/status`
- `/api/dataops/graph/status`

Implementation should use a shared SDK helper where possible, but each app owns
its endpoint and domain.

Required fields:

- `active_backend`
- `requested_backend`
- `sqlite_authoritative`
- `age_active`
- `shadow_enabled`
- `shadow_allowed`
- `graph_kind`: `sqlite`, `test`, `product`, or `invalid`
- `active_graph_name`: safe display name only
- `active_domain`
- `active_test_mode`
- `ignored_generic_graph_env`
- `migration_backfill_status`: `not_in_scope`
- `receipt_mapping_status`: `excluded_first_cutover` or `design_required`
- `historical_visibility_warning`
- `warnings`: safe operator-facing strings only
- `rollback_instructions`
- `cutover_ready`
- `new_decision_outcome_writes_ready`
- `full_audit_memory_ready`
- `migration_complete`
- `evidence_receipt_ready`
- readiness flags for product graph allow-list, active backend guards,
  rollback proof, true parallel backend gate, Playwright smoke, migration, and
  EvidenceReceipt mapping.

The endpoint is read-only and operator/demo safe. It must not construct a live
AGE store just to report status.

The status schema should mirror S2P field names unless an app needs an
additional field. This keeps Playwright and operator checks reusable across
domains.

## Rollback model

For each app:

- Rollback is unset the app-specific active AGE env or set
  `*_ACTIVE_GRAPH_BACKEND=sqlite`, then restart the app.
- SQLite path behavior through `CI_DATA_DIR` must remain unchanged.
- AGE data written while AGE was active is not deleted.
- AGE data is not copied back into SQLite.
- No hidden reconciliation runs during rollback.
- Status must state that historical records written to one backend are not
  automatically visible in the other backend.
- Rollback proof must show:
  - active AGE score/outcome writes first;
  - app restart/reconstruction with SQLite;
  - new SQLite score/outcome writes succeed;
  - status reports SQLite;
  - AGE-only data is not magically present in SQLite;
  - one-outcome invariant remains preserved.

## Test strategy

Common minimum tests per app:

- Default/no env remains SQLite.
- Explicit `sqlite` remains SQLite.
- Generic `GRAPH_*` env is ignored.
- Active AGE config rejects invalid backend.
- Active AGE config requires DSN and graph.
- `soc_graph` is rejected.
- `protocol_v2_test*` requires test mode.
- Product-like graph requires an allow-list.
- Domain is locked to the app domain.
- Active AGE plus shadow AGE is rejected.
- Status endpoint is read-only and redacts secrets.
- Score writes governed Decision in active AGE test mode.
- Outcome and learn write Outcome/status in active AGE test mode.
- Duplicate outcome/learn is rejected.
- Conservation/status counts use the active graph store in active AGE mode.
- Read/preview routes do not create Decisions.
- Rollback to SQLite is proved.
- Full backend suite remains green.
- Guarded live active AGE tests skip by default and run only with explicit env.
- Playwright smoke passes after backend gates.
- True parallel backend gate runs at least eight independent flows with at
  least four workers before product-claim readiness.

For the first Purchasing implementation, these tests should be bundled into one
prompt with internal stop gates rather than split into a status-only prompt and
a later active-AGE prompt. Stop conditions are:

- baseline/default SQLite tests fail;
- app-specific env guards cannot be made equivalent to S2P guards;
- active AGE test-mode requires broad scorer/router rewrites;
- rollback proof cannot distinguish AGE-only data from SQLite data;
- read routes create Decisions unexpectedly.

App-specific additions:

- Trading:
  - `prescore` does not create Decisions.
  - `social/score-as` writes through the selected active graph store.
  - webhook `auto_score` writes through the selected active graph store.
  - journal/evidence/regime/promotion read the selected active graph store.
- Purchasing:
  - evidence/status routes remain read-only.
  - context metadata routes do not create Decisions unless explicitly designed.
  - startup seeding behavior is guarded in active AGE mode.
- DataOps:
  - scorer Decision/Outcome writes are separated from DataOpsGraphClient and
    operational graph routes.
  - `apply-fix` and `alert-metadata` are not treated as governed
    Decision/Outcome cutover without a separate mapping.
  - DomainContext partition tests cover Pipeline, Alert, DataQualityAlert-like,
    PipelineSystem-like, Activity, and Transformation semantics before a broad
    DataOps graph claim.

## demo.py operational TODO

Do not change `demo.py` as part of this design plan.

Add demo.py support once Purchasing has passed active AGE test-mode and
rollback proof. Do it as one shared operational slice for Purchasing and
Trading flags, not separately per app. DataOps flags should wait for the
DataOps blocker plan.

Future flags:

- `--trading-age-test`
- `--trading-age-product`
- `--purchasing-age-test`
- `--purchasing-age-product`
- `--dataops-age-test`
- `--dataops-age-product`

Status output should distinguish:

- `<App> [SQLite authoritative]`
- `<App> [AGE shadow]`
- `<App> [AGE active test]`
- `<App> [AGE active product]`

Rules:

- Default startup remains unchanged.
- Product flags require reviewed allow-listed graph names.
- Test flags may only use `protocol_v2_test*` with test mode enabled.
- No app flag may point non-SOC writes to `soc_graph`.
- DSN and secret values must be redacted in console output.

## Cross-copilot proof prerequisites

Before final common-graph proof:

- SOC projection remains accepted and non-mutating unless a separate SOC write
  migration is reviewed.
- S2P is accepted for active new Decision/Outcome writes.
- Trading is accepted for active new Decision/Outcome writes.
- Purchasing is accepted for active new Decision/Outcome writes.
- DataOps is accepted for active new Decision/Outcome writes, with operational
  graph semantics separated or explicitly mapped.
- Each app writes to the reviewed common governed graph using its own stable
  lowercase domain.
- Domain separation is tested.
- `soc_graph` contamination is rejected and tested.
- Canonical vocabulary queries work across domains.
- Decision, Outcome, FactorVector, CentroidCheckpoint, EvolutionEvent, and
  DomainContext queries are validated for each accepted domain where applicable.
- Cross-domain transfer/evolution queries are validated where applicable.
- EvidenceReceipt gaps are documented or closed by separate mapping plans.
- Migration/backfill gaps are documented or closed by separate replay plans.
- No external product claim is made until cutover, rollback, receipt/audit
  scope, migration caveats, and cross-copilot proof are reviewed.

## Recommended implementation sequence

### Phase 1: Purchasing bundled governed graph milestone

Scope:

- Add the shared config/status helper shape while wiring Purchasing only.
- Add `/api/purchasing/graph/status`.
- Keep default SQLite.
- Prove generic `GRAPH_*` cannot switch Purchasing.
- Add active AGE test-mode for Purchasing only after config/status guards pass.
- Prove score, outcome/learn, read safety, rollback, and status truthfulness.
- Run targeted Purchasing Playwright smoke if the stack is available.

Exit gate:

- Purchasing accepted for new Decision/Outcome active AGE under explicit env.
- Shared helper shape is ready to reuse for Trading.
- Existing backend behavior remains unchanged when env is absent.

### Phase 2: Trading bundled governed graph milestone

Scope:

- Reuse the Purchasing helper/status pattern.
- Apply the selected graph-store provider pattern to Trading.
- Include social score-as, webhook auto-score, prescore read-only safety,
  journal/evidence/regime/promotion read surfaces, startup seed behavior,
  rollback proof, parallel backend gate, and Playwright smoke.

Exit gate:

- Trading accepted for new Decision/Outcome active AGE under explicit env.

### Phase 3: shared demo.py operational slice

Scope:

- Add Purchasing and Trading AGE test/product flag support only after both
  backend milestones are accepted.
- Keep defaults unchanged.
- Redact DSN values and reject `soc_graph`.
- Do not add DataOps flags yet.

Exit gate:

- Demo startup/status can operate SQLite, AGE active test, and AGE active
  product-like modes for Purchasing and Trading without changing defaults.

### Phase 4: DataOps blocker resolution and adoption

Scope:

- Create a DataOps graph semantics plan before runtime cutover.
- Separate scorer GraphStore cutover from DataOpsGraphClient and operational
  graph routes.
- Define DomainContext/Observation/EvolutionEvent boundaries for pipeline and
  alert concepts.
- Only then add DataOps active AGE test-mode Decision/Outcome adoption.

Exit gate:

- DataOps accepted for new Decision/Outcome active AGE under explicit env, with
  operational graph caveats documented.

### Phase 5: cross-copilot proof design and execution

Scope:

- Run common governed graph proof only after S2P, Trading, Purchasing, and
  DataOps have passed their app-level gates.
- Keep SOC mutation blocked unless a separate SOC write migration is reviewed.
- Carry EvidenceReceipt and migration caveats explicitly.

## P3 backlog carried forward

- S2P live `governed_copilot_graph` smoke: not run. Non-blocking for SDK app
  design, required before stronger product graph claims.
- S2P product-mode Playwright rerun: not run. Non-blocking for SDK app design,
  required before S2P product-claim readiness.
- EvidenceReceipt mapping: excluded from S2P first cutover. Must be designed
  separately before a full canonical audit-memory claim.
- Historical migration/backfill: excluded. Must be designed separately before
  historical continuity claims.
- SOC projection P3s: Outcome double-count backfill, triggered evolution
  forward writes, ShadowDecision mapping, and SOC route migration remain
  separate.

## Open questions

- Should all SDK apps use `governed_copilot_graph` as the product graph, or
  should app-specific product graph names be reviewed for Trading, Purchasing,
  and DataOps?
- Should startup fixture seeding be disabled in active AGE product mode, or
  should it become an explicit idempotent operator action?
- Should Trading webhook auto-score be enabled in active AGE product mode by
  default, or require a separate operator flag?
- Which DataOps operational graph concepts become DomainContext, Observation,
  EvolutionEvent, or EvidenceReceipt in Protocol v2?
- Should a shared SDK `AppGraphStatus` helper live in `copilot_sdk.backend` or
  remain app-local until Trading and Purchasing prove the pattern?
- What is the first acceptable cross-domain query for proof: transfer pattern,
  evolution history, or domain-separated Decision/Outcome inventory?
