# Judgment Memory Compliance Fix Execution Plan

**Document version:** 2  
**Date:** 2026-10-05  
**Status:** APPROVED  
**References:** [Compliance audit](design_compliance_audit_v2.md), [Design fix plan](design_fix_plan_v2.md), [Canonical principles](design_principles_v2.md).

This document turns Groups 1–8 in the design-fix plan into sequential Codex prompt specifications. Each prompt must capture its own live baseline because the checked-out worktree can change between groups. Use actual baseline counts as the regression reference; prior recorded SDK/app counts are historical only.

## GROUP 1: Conservation rolling-window semantics

**Fixes:** F-02  
**Model:** sol + high  
**Sequential/Parallel:** First; Group 2 follows because freshness/cache semantics must be settled before final gate verification.

### What this prompt does

Unify the primary conservation gate and status projection around lifetime verified count `V`, category coverage `alpha`, and accuracy `q` over the latest 400 verified outcomes. Preserve the bootstrap/calibration behavior and ensure preview observations and pending decisions remain excluded.

### Pre-checks

- Read `docs/session_state.md`; confirm no other active edit is modifying conservation math.
- Read F-02 in `docs/design_fix_plan_v2.md`, `copilot_sdk/scoring/scorer.py`, and `copilot_sdk/backend/conservation_utils.py`.
- Trace `_conservation_stats()` → `_conservation_pause()` → primary gate. Confirm whether the checkpoint rolling window already feeds any gate path; narrow the change if so and record evidence.
- Run and record baselines: `python -m pytest tests/ -q --timeout=120`; `python -m pytest apps/trading/backend/tests/ -q --timeout=120`; same for Purchasing and DataOps.
- Read existing conservation/scorer tests, especially 399/400/401 and observation-exclusion cases.

### Files changed

`copilot_sdk/scoring/scorer.py`; `copilot_sdk/backend/conservation_utils.py`; focused scorer/conservation tests; `docs/session_state.md`.

### Key design decisions

- Follow F-02: lifetime `V`, rolling verified `q`, and one shared calculation for gate and API status.
- Use deterministic canonical timestamp plus stable ID ordering; do not use all-time accuracy as fallback.
- In `_rolling_q`, use `verified[-window_size:] if len(verified) > window_size else verified`; document the warm-up case and reject invalid nonpositive window size explicitly.

### Test verification

- `python -m pytest tests/scoring/test_conservation.py tests/test_conservation_utils.py -q --timeout=120`
- `python -m pytest tests/ -q --timeout=120`
- Run all three app backend suites with `python -m pytest apps/<app>/backend/tests/ -q --timeout=120`.
- Mypy: `python -m mypy copilot_sdk/scoring/scorer.py copilot_sdk/backend/conservation_utils.py --config-file pyproject.toml`.
- Expected: focused cases pass; root/app suites have zero new failures versus the captured pre-check baseline; report any legitimate test-count delta.

### Post-check

Append baseline, behavior, exact tests/mypy counts, files, and next group to `docs/session_state.md`.

**Estimated complexity:** Medium (3–5 files, conservation semantics and parity).

## GROUP 2: Fresh graph reads; remove query-serving caches

**Fixes:** F-06, F-07  
**Model:** sol + high  
**Sequential/Parallel:** After Group 1. Run before Group 3 so the experiment namespace path is built on fresh-read semantics.

### What this prompt does

Remove cross-request caches of verified decisions, DI responses, score context, and graph-derived conservation payloads. Each operation reads current graph state; pure memoization may remain only within one request. Conservation status must come from the live provider on every request.

### Pre-checks

- Read `docs/session_state.md`, then F-06/F-07 in the design-fix plan.
- Read `copilot_sdk/scoring/scorer.py`, `copilot_sdk/di/query_service.py`, `copilot_sdk/backend/scoring_router.py`, `copilot_sdk/backend/conservation_router.py`, `copilot_sdk/backend/response_materializer.py`, and the relevant Trading/Purchasing/DataOps `main.py` cache wiring.
- Read `tests/test_di_query_service.py`, scorer-cache tests, scoring-router tests, conservation-router/materializer tests, and app cache tests in full.
- Capture SDK and all three app suite baselines before editing.

### Files changed

`copilot_sdk/scoring/scorer.py`; `copilot_sdk/di/query_service.py`; `copilot_sdk/backend/scoring_router.py`; `copilot_sdk/backend/conservation_router.py`; `copilot_sdk/backend/response_materializer.py` if its graph-backed cache surface must change; three app `main.py` files; directly affected tests; `docs/session_state.md`.

### Key design decisions

- Follow F-06/F-07. Remove object-lifetime verified-decision cache and graph-derived query/context/conservation cache reads.
- A single operation may use one local graph snapshot for internal consistency, but may not retain it across requests.
- Keep only static configuration caches that cannot influence graph-derived decisions/answers; no graph-outage cache fallback.
- Do not broaden the change into unrelated static or frontend caches.

### Test verification

- `python -m pytest tests/test_di_query_service.py tests/test_scoring_router.py tests/scoring/test_conservation.py -q --timeout=120`
- Run the focused conservation-router/materializer tests identified at pre-check.
- `python -m pytest tests/ -q --timeout=120`
- Run Trading, Purchasing, and DataOps backend suites.
- Mypy each changed Python file with `python -m mypy <file> --config-file pyproject.toml`.
- Add/verify a two-client freshness case: client B writes a verified outcome, and client A's next read/status sees it. Expected: zero new failures; cache-only tests are replaced, not merely deleted.

### Post-check

Append exact cache removals, remaining static caches, freshness proof, test counts, mypy, files, and next group to session state.

**Estimated complexity:** Complex (6+ files; graph freshness spans scorer, routers, materialization, and app wiring).

## GROUP 3: Shared AGE experiment graph and GraphStoreNamespace

**Fixes:** F-01 plus the shared `GraphStoreNamespace` component  
**Model:** sol + high  
**Sequential/Parallel:** After Groups 1 and 2. Namespace implementation and S2P rewiring are one atomic group.

### What this prompt does

Change S2P's reasoning-quality experiment to create one authorized AGE GraphStore per run and pass it to both graph-backed arms. Add the protocol-complete namespace adapter specified in the design-fix plan so arm records are isolated within the same graph by rewritten domain scope, not by backend/store/cache instances.

### Pre-checks

- Read session state and F-01 plus the complete `GraphStoreNamespace` specification.
- Read `copilot_sdk/graph/protocol.py` in full, `copilot_sdk/graph/factory.py`, `copilot_sdk/scoring/scorer.py` store call sites, `apps/s2p_differentiation/engine.py`, config, and experiment tests/scripts.
- Inspect the AGE factory/config contract; verify the experiment can request the shared authorized production graph and fail closed if it cannot.
- Capture root, S2P, and app suite baselines. Read namespace-related conformance tests if already present.

### Files changed

`apps/s2p_differentiation/engine.py`; `copilot_sdk/scoring/scorer.py`; new `copilot_sdk/graph/namespace.py` (or the graph module selected by the implementation prompt); S2P engine/namespace tests; any experiment configuration docs needed for credentials/profile; `docs/session_state.md`.

### Key design decisions

- Follow F-01. One physical AGE graph, same store identity for CI and hand-specified arms, different namespace strings only.
- `GraphStoreNamespace` must explicitly implement every `GraphStore` and `ProtocolV2GraphStore` method with exact type hints/signatures from `protocol.py`; no `__getattr__`, missing-method casts, private access, persistence, or cache.
- Rewrite all domain arguments, including both transfer endpoints and optional domain inventories; filter/unprefix returned graph domain fields. `close()` on a view must not close the shared underlying store.
- Keep algorithm-only baseline arms clearly labeled as not measuring graph reasoning. Never fall back to InMemoryGraphStore for integrated experiment execution.

### Test verification

- `python -m pytest apps/s2p_differentiation/ -q --timeout=120`
- `python -m pytest tests/ -q --timeout=120`
- Run all app backend suites.
- Add protocol conformance and two-namespace isolation tests on one underlying store; where available, run the same isolation proof against AGE.
- Mypy `copilot_sdk/graph/namespace.py`, `copilot_sdk/scoring/scorer.py`, and engine/config files.
- Expected: both graph arms expose the same underlying AGE identity, have distinct logical domains, and cannot read each other's verified outcomes; AGE-unavailable path fails closed.

### Post-check

Append graph identity/namespace evidence, no-memory-fallback gate, tests/mypy, file list, and next groups to session state.

**Estimated complexity:** Complex (6+ files; protocol-complete namespace architecture and experiment wiring).

## GROUP 4: Retire SQLiteGraphStore and DualWriteStore

**Fixes:** F-03  
**Model:** sol + high  
**Sequential/Parallel:** May run in parallel with Group 5 after each group records the stable `ProtocolV2GraphStore` event contract. Group 6 waits for graph/backend retirement design to stabilize.

### What this prompt does

Decouple historical migration input from the GraphStore abstraction, then remove the SQLite and dual-write graph implementations while preserving read-only source cutover capability and the outbox carve-out.

### Pre-checks

- Read session state and F-03; confirm no SQLite cutover or backend deletion is concurrently running.
- Read `sqlite_store.py`, `dual_write_store.py`, `migrate/__main__.py`, archive reconciliation, graph exports/factory, `outcome_service.py`, and all direct imports/callers/tests.
- Run the six scan commands in the original DSTORE-CLEANUP prompt; classify any new production-code hit and halt if unexplained.
- Capture SDK and app baselines; inventory historical migration source files without deleting or modifying them.

### Files changed

`copilot_sdk/graph/sqlite_store.py` (delete); `copilot_sdk/graph/dual_write_store.py` (delete); `copilot_sdk/migrate/` source reader/CLI/reconciler; graph exports and `outcome_service.py`; exclusively backend-specific tests and migration tests; `docs/session_state.md`.

### Key design decisions

- Follow F-03. A legacy SQLite reader is read-only migration input and does not implement GraphStore; AGE is the sole migration target.
- Retire implementation files only after callers/exports/tests are migrated. Do not delete historical data or claim cutover without parity verification.
- Preserve SQLite only in the two exempt write-only outboxes and migration-scoped source reading until cutover is verified.
- Do not change `protocol.py` or add a third GraphStore backend.

### Test verification

- Run migration/reconciliation/CLI tests and graph factory/export tests.
- `python -m pytest tests/ -q --timeout=120`; run all three app backend suites.
- Run `python -m mypy copilot_sdk/migrate/ --config-file pyproject.toml` and mypy every changed graph file.
- Architecture checks: `rg -n "SQLiteGraphStore|DualWriteStore|sqlite_store" copilot_sdk tests apps`; only intentional historical migration-reader references may remain, never runtime GraphStore references. Confirm `sqlite3` under outboxes and migration reader only.
- Expected count may decrease only by deleted implementation-specific tests; keep equivalent migration/read/write contract coverage and report exact delta from baseline.

### Post-check

Append scan classifications, preserved data-cutover path, exemptions, exact test-count delta, mypy, files, and next groups to session state.

**Estimated complexity:** Complex (6+ files; migration source and backend retirement).

## GROUP 5: Move cross-copilot signals into graph events

**Fixes:** F-04  
**Model:** sol + high  
**Sequential/Parallel:** May run in parallel with Group 4 once the protocol event contract is stable. Group 8 waits for this group.

### What this prompt does

Replace SQLiteSignalStore as the signal authority with graph `cross_copilot_signal` events on the selected shared graph, and preserve the existing publish/page/get API, filtering, stable IDs, ordering, and TTL behavior.

### Pre-checks

- Read session state and F-04, then `protocol.py`, signal store/router, all three app main wiring blocks, current constants/response schemas, graph AGE `get_evolution_events` filtering/cap behavior, and tests.
- Verify all three app route factories can pass the already-selected store object; do not create a second factory instance.
- Capture SDK and app suite baselines; specifically record event query filter order and maximum results.

### Files changed

`copilot_sdk/backend/signal_store.py`; `copilot_sdk/backend/cross_signal_router.py`; Trading/Purchasing/DataOps `main.py`; signal and app wiring tests; `docs/session_state.md`.

### Key design decisions

- Follow F-04: require `ProtocolV2GraphStore`; remove SQLite defaults and store imports from the runtime route.
- Store under the shared `platform` domain as `cross_copilot_signal`; include stable signal ID, source/target, payload, timestamp and TTL evidence in metadata.
- Implement page/get using only `get_evolution_events(domain, event_type, limit)`. Expire/filter/sort/count/page from returned graph events. Never read from PersistenceOutbox.
- Verify event-type filtering occurs before the 1,000 cap. If the adapter cannot support complete bounded inventory, fail/report the protocol limitation rather than silently mispage.

### Test verification

- `python -m pytest tests/test_cross_signal_router.py tests/test_signal_store.py -q --timeout=120`
- `python -m pytest tests/ -q --timeout=120`
- Run Trading, Purchasing, and DataOps backend suites.
- Mypy each changed file.
- Expected: graph event round-trip, expiry, source/target filtering, idempotency/stable ID behavior and same graph identity in app wiring all pass; outage buffer is write-only.

### Post-check

Append read/write round-trip evidence, cap behavior, no-SQLite-default scan, suites/mypy, files, and next groups to session state.

**Estimated complexity:** Complex (6+ files; shared graph event API and three app roots).

## GROUP 6: Remove durable side-store fallbacks

**Fixes:** F-05  
**Model:** spark + high  
**Sequential/Parallel:** Can run in parallel with Group 7. Complete after Group 4's graph retirement interface decisions are recorded.

### What this prompt does

Make integrated outcome, proof, promotion, variant, and frozen-judgment state use the existing graph adapters; remove silent SQLite/file constructors from production service paths while retaining explicit test doubles and safe read-only data migration.

### Pre-checks

- Read session state and F-05. Confirm GraphStoreNamespace/ProtocolV2 methods and Group 4 migration status.
- Read `outcome/ledger.py`, `promotion/core.py`, `evolution/variant_store.py`, `evolution/graph_store.py`, `twin/store.py`, Purchasing control, Trading claim gate, exports, app wiring, and all affected tests.
- Capture SDK/app baselines and inventory existing durable side-store files; no data deletion.

### Files changed

Outcome ledger and promotion core; variant store and exports; twin store; Purchasing `purchasing_control.py`; Trading `claim_gate.py`; app composition if needed; affected outcome/promotion/variant/twin/control tests; `docs/session_state.md`.

### Key design decisions

- Follow F-05. Integrated constructors receive graph adapters explicitly and fail closed when the required protocol capability is absent.
- Do not use SQLite or JSON/file stores as fallback authority. Keep in-memory doubles only in isolated unit tests.
- Do not discard persisted records. Preserve read-only extraction/parity migration until cutover is verified; outboxes remain write-only.
- Keep each record type inspectable in the shared graph and preserve lifecycle IDs/provenance.

### Test verification

- `python -m pytest tests/test_outcome_protocol.py tests/test_promotion_engine.py tests/evolution/ -q --timeout=120`
- Run affected Purchasing-control and Trading-claim-gate tests; then full SDK and all app suites.
- Mypy every changed production/test file.
- Expected: graph adapter round-trips pass; unsupported graph capabilities fail closed; count delta only reflects SQLite-only implementation tests replaced by equivalent lifecycle tests.

### Post-check

Append each removed fallback, data-retention/parity state, tests/counts/mypy, files, and next group to session state.

**Estimated complexity:** Complex (6+ files, broad service and persistence wiring).

## GROUP 7: Require governed transfer artifacts

**Fixes:** F-09  
**Model:** spark + high  
**Sequential/Parallel:** Can run in parallel with Group 6; integrate after ProtocolV2 transfer contracts are confirmed.

### What this prompt does

Remove synthetic demo patterns from the transfer execution path. Require persisted source artifacts, validate source and target conservation and factor schema, and persist an inspectable transfer witness with both governance states and source links.

### Pre-checks

- Read session state and F-09, `transfer_router.py`, transfer types/adapters/protocol methods, source/target conservation helpers, registry implementation, and `tests/test_transfer_router.py` in full.
- Capture root and three app suite baselines; confirm live AGE transfer test configuration.

### Files changed

`copilot_sdk/backend/transfer_router.py`; graph transfer types/adapters only if required by existing protocol; transfer router/types/AGE integration tests; `docs/session_state.md`.

### Key design decisions

- Follow F-09. No synthetic/demo artifact can be applied or marked validated.
- Missing governed source patterns produce a blocked response and no centroid or graph mutation.
- Persist source/target conservation states, source artifact IDs, exact factor mapping, validation result and provenance in the graph transfer artifact.
- Preserve preview-only demo UI behavior only if it is clearly labeled and has no write/centroid effect.

### Test verification

- `python -m pytest tests/test_transfer_router.py -q --timeout=120`
- Run all app backend suites and full SDK root suite.
- Mypy every changed file; run AGE transfer readback when configured.
- Expected: no-pattern, synthetic provenance, invalid mapping, and either-side conservation failures are blocked without writes; valid transfer readback contains all required evidence.

### Post-check

Append transfer block/readback outcomes, tests/mypy, files, and next groups to session state.

**Estimated complexity:** Medium (3–5 files, transfer behavior and evidence tests).

## GROUP 8: Shared demo preseed graph

**Fixes:** F-08  
**Model:** spark + medium  
**Sequential/Parallel:** After Group 5's signal event schema; may reuse Group 3 GraphStoreNamespace only if a future operation lacks explicit domain parameters.

### What this prompt does

Use one shared graph object for all offline demo scorers and persist/read the seeded cross-copilot signal through that graph. Keep integrated demo mode on AGE and fail closed when it is unavailable.

### Pre-checks

- Read session state and F-08; read `copilot_sdk/demo/preseed.py`, InMemoryGraphStore methods, scorer domain calls, and all preseed/demo tests.
- Verify the current store implementation: domain-explicit protocol methods support multiple domains; the constructor `domain` applies to legacy RL convenience state only. Ensure local demo scorers keep `enable_rl=False` unless an explicitly domain-scoped RL API is added.
- Capture SDK and app baselines.

### Files changed

`copilot_sdk/demo/preseed.py`; preseed/demo tests; integrated demo composition only if it currently permits a memory fallback; `docs/session_state.md`.

### Key design decisions

- Follow F-08. One `InMemoryGraphStore(domain="demo")` instance is shared across all offline seeded domains; each scorer continues using explicit domain arguments. Constructor domain does not collapse decision/outcome records into `demo`.
- Store cross-copilot signals as graph events and read them back by stable ID.
- No per-domain memory stores, persistent caches, or detached signal dictionary as the authoritative signal record.
- AGE is mandatory for integrated/reasoning-quality demo; memory is only offline local demo/test.

### Test verification

- `python -m pytest tests/test_preseed.py -q --timeout=120`
- `python -m pytest tests/ -q --timeout=120`
- Run app suites if integrated demo wiring changes; run mypy for every changed Python file.
- Expected: all preseeded domain scorers share one underlying local store while domain reads remain isolated; signal event round-trip succeeds; integrated mode cannot silently fall back to memory.

### Post-check

Append store identity, per-domain isolation, event readback, profile fail-closed proof, counts/mypy, and completion state to session state.

**Estimated complexity:** Simple (1–2 files for offline preseed; Medium if integrated composition also needs wiring).

## Overall verification

After all eight groups, rerun SDK root, Trading, Purchasing, DataOps, and S2P suites; run mypy on every changed file; run architecture scans for DecisionStore, SQLiteGraphStore/DualWriteStore runtime references, SQLiteSignalStore, persistent/query-serving caches, and per-arm InMemoryGraphStore use. Compare against the captured pre-change baselines, allowing only documented removal of backend-exclusive tests. Do not report AGE production parity without successful live AGE read/write and cross-type integration tests.

## Self-review results

1. **Section E coverage:** PASS — `evolution_router.py` is explicitly listed with its integrated graph-backed app wiring rationale; `conservation_router.py` is in V-07 because it returns materialized status before live resolution.
2. **V-07 severity/count:** PASS — audit classifies V-07 as P1; summary is 8 P1 and 1 P2.
3. **F-08 domain behavior:** PASS — `InMemoryGraphStore` explicit-domain calls support multiple logical domains; only legacy RL helpers use constructor domain, and demo RL stays disabled.
4. **GraphStoreNamespace:** PASS — the fix plan specifies a stateless same-store view, domain transformation/filtering rules, safe close behavior, and the complete inherited `GraphStore` + `ProtocolV2GraphStore` method inventory; the implementation prompt must provide explicit forwarding definitions with the exact protocol signatures.
5. **F-02 pre-check:** PASS — code-path trace is required before changing any conservation path.
6. **F-04 reads:** PASS — page/get use `get_evolution_events` with event type, TTL, source/target filtering, ordering, count and pagination; adapter cap semantics are verified explicitly.
7. **F-02 slicing:** PASS — snippet has no unnecessary `int()` cast and documents bootstrap handling.
8. **All execution groups:** PASS — all eight groups have prompt specs, target files, pre-checks, design decisions, test/mypy checks and session-state post-checks.
9. **Dependency order:** PASS — no group depends on a later group; Groups 4+5 and 6+7 are parallel; Group 8 waits for Group 5.
10. **Model routing:** PASS — Groups 1–5 sol/high; Groups 6–7 spark/high; Group 8 spark/medium.
