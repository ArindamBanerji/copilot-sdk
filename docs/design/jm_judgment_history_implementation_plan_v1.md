# JM Judgment History — Executable Implementation Plan v1

**Date:** 2026-08-06  
**Scope:** P-1 through P2 only; Program B migration remains out of scope.  
**Source policy:** This plan reports source-verified behavior. No production files were modified.

## 1. RMAP Verification Results

| Item | Result | Evidence and consequence |
|---|---|---|
| RMAP-1 | CONFIRMED, with drift | `copilot_sdk/graph/sqlite_store.py:2626-2637` filters `checkpoint_id IS NULL` and orders by `id DESC`. It does not order by `created_at`; C1 must change both behaviors. |
| RMAP-2 | CONTRADICTED | `copilot_sdk/graph/memory_store.py:1370-1378` filters only by domain and returns the last legacy entry. It neither filters `checkpoint_id IS NULL` nor reads the V2 `_protocol_centroid_checkpoints` store. |
| RMAP-3 | CONFIRMED, incomplete | `copilot_sdk/backend/self_computation_router.py:29-51` implements `/centroid-history`, but calls `get_centroid_checkpoints` without `include_v2=True`. It returns only `checkpoints` and `total`. |
| RMAP-4 | CONFIRMED only for the envelope | `copilot_sdk/backend/models.py:177-180` defines `CentroidHistoryResponse` with `checkpoints: list[dict[str, Any]]` and `total: int`; it has no typed quality field. |
| RMAP-5 | CONFIRMED, incomplete for C3 | `copilot_sdk/graph/protocol.py:83-102` declares legacy save/load/history methods. `protocol.py:267-281` declares V2 `write_centroid_checkpoint`; neither contract has the six quality fields required by C3. |
| RMAP-6 | CONFIRMED | Memory has separate legacy save (`memory_store.py:1346-1368`), V2 write (`:777-815`), L5 update (`:1182-1205`), and history merge (`:1387-1419`). Its startup loader (`:1370-1378`) ignores V2 and does not timestamp-sort. |
| RMAP-7 | CONFIRMED | `copilot_sdk/migrate/verify_state.py:247-311` replays decisions chronologically and compares scorer state; `copilot_sdk/migrate/shadow_scorer.py:46-231` provides score/learn/state comparison. These are usable as P2 verification infrastructure, not as a production endpoint. |
| RMAP-8 | CONFIRMED for the legacy route; contradicted for shared mounting | SOC route `/soc/centroid-evolution` is `../gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:107-171`; it queries Decision deltas and returns 503 when empty. SOC mounts that router in `main.py:132-142`, not the shared self-computation router. |
| RMAP-9 | CONFIRMED | S2P legacy routes are in `../s2p-copilot/backend/app/routers/centroid_router.py:17-62` and mounted at `../s2p-copilot/backend/app/main.py:247-253`. No shared `/api/self/centroid-history` route is mounted there. |
| RMAP-10 | CONTRADICTED as a zero-caller assumption | DataOps custom route is `apps/dataops/backend/app/context_router.py:1037-1068`; `apps/dataops/frontend/src/api.ts:401-408` calls it, and `apps/dataops/backend/tests/test_dataops_backend.py:817-848` asserts its custom `snapshots` shape. The Panel uses the shared route through `api.ts:410-413`, but deletion is not safe until the legacy caller/tests migrate. |

### Additional source findings that change the implementation

1. `created_at` is not a uniform sortable field. AGE legacy writes an ISO string at `../ci-platform/ci_platform/graph/age_graph_store.py:2620-2642`, while AGE V2 writes a numeric epoch at `:1356-1420`; SQLite writes numeric epochs in `copilot_sdk/graph/sqlite_store.py:2591-2624` and `:1556-1640`; Memory mixes ISO legacy (`memory_store.py:1363`) and numeric V2 (`:813`). A bare `ORDER BY created_at DESC` is therefore not a safe cross-adapter contract.
2. The scorer writes the full V2 tensor and factor hash in `copilot_sdk/scoring/scorer.py:1767-1839`, but startup receives only a tensor from `load_latest_centroids` at `scorer.py:250-282`; there is no current factor-hash validation seam.
3. DataOps, Trading, and Purchasing mount the shared router (`apps/dataops/backend/app/main.py:749-751`, `apps/trading/backend/app/main.py:439-440`, `apps/purchasing/backend/app/main.py:707-709`). SOC and S2P require explicit adapters/mounts.
4. The v6 “7 gaps” statement is stale. The enumerated set is nine: 6, 7, 9, 10, 11, 13, 15, 16, 17. P0-P2 address #13 and #17; seven remain deferred to the GAE conformance program.

## 2. Gap Resolutions

### Gap 1 — C1 loader ordering and `created_at` monotonicity

**Evidence.** SQLite currently selects null-id rows and orders by autoincrement `id` (`sqlite_store.py:2626-2637`). AGE orders mixed representations of `created_at` (`age_graph_store.py:2661-2670`). Memory has no timestamp ordering in its startup loader (`memory_store.py:1370-1378`). Store writers use different representations as listed above.

**Resolution.** Add a canonical numeric `created_at_epoch` to every new legacy and V2 checkpoint. Preserve the existing `created_at` output for compatibility. At read time, order by `created_at_epoch DESC`, then `created_at DESC`, then a stable identifier. Add a one-time SQLite backfill that parses existing ISO/numeric values and an AGE backfill/read fallback for existing rows. Do not claim monotonicity from `created_at` alone.

**Files to change.** `copilot_sdk/graph/protocol.py:83-102,267-281`; `copilot_sdk/graph/sqlite_store.py:2591-2637`; `copilot_sdk/graph/memory_store.py:777-815,1346-1419`; `../ci-platform/ci_platform/graph/age_graph_store.py:1356-1420,2620-2670`; `copilot_sdk/scoring/scorer.py:1767-1839` only if payload metadata needs the canonical field.

**Tests.** Seed a legacy ISO row and a V2 numeric row with intentionally reversed insertion order; assert all adapters load the newest epoch. Assert a legacy row with `checkpoint_id=None` is returned. Assert malformed timestamps are excluded with an explicit warning rather than silently winning.

### Gap 2 — C2 DataOps custom route deletion

**Evidence.** The custom route returns `snapshots`, `factor_names`, and `total_decisions` (`apps/dataops/backend/app/context_router.py:1037-1068`). Its API caller is `apps/dataops/frontend/src/api.ts:401-408`; tests assert the shape at `apps/dataops/backend/tests/test_dataops_backend.py:817-848`. The new Panel uses the shared envelope at `api.ts:410-413`.

**Resolution.** First migrate `getCentroidHistory` to the shared `/api/self/centroid-history` contract and rewrite the four custom-shape tests to assert `checkpoints` and `total`. Keep `/api/context/centroid-history` as a compatibility route returning the shared envelope for one release; then remove the handler only after a repository search has zero callers. Do not delete it in the same change that introduces the shared route.

**Files to change.** `apps/dataops/frontend/src/api.ts:401-413`; `apps/dataops/backend/app/context_router.py:1037-1068`; `apps/dataops/backend/tests/test_dataops_backend.py:817-848`; any DataOps component discovered by the final `context/centroid-history` search.

**Tests.** Assert the old URL returns the shared envelope during the compatibility window; assert the frontend API function requests `/api/self/centroid-history`; assert no test expects `snapshots` after the migration.

### Gap 3 — C3 counterfactual replay endpoint

**Evidence.** V2 checkpoints include the complete `centroids` tensor, shape, and factor hash in `scorer.py:1826-1839`. `graph-attention-engine-v50/gae/profile_scorer.py:408-511` scores an arbitrary factor vector against the scorer’s centroid tensor using distance/softmax. The current `score_read_only` path is `scorer.py:404-427` and is tied to live state.

**Resolution.** Add `GET /api/self/centroid-history/{checkpoint_id}/counterfactual?window=20`. Load the checkpoint tensor and the last `window` decision factor vectors, clone a scorer/profile scorer with the current action/category metadata, replace only its centroid tensor, and score each vector. Never mutate the live scorer or persist learning. Return:

```json
{
  "checkpoint_id": "...",
  "checkpoint_time": "...",
  "decisions_rescored": 20,
  "would_change": 3,
  "change_rate": 0.15,
  "details": [{"decision_id": "...", "original_action": "...", "counterfactual_action": "...", "changed": true}]
}
```

Reject a checkpoint with missing tensor, incompatible shape, or factor hash mismatch with a typed 409/422 response. Bound `window` to 1..400.

**Files to change.** `copilot_sdk/graph/protocol.py:267-281` (checkpoint read with metadata); `copilot_sdk/graph/sqlite_store.py:1556-1640`; `copilot_sdk/graph/memory_store.py:777-815,1387-1419`; `../ci-platform/ci_platform/graph/age_graph_store.py:1356-1420,2834-2853`; `copilot_sdk/backend/self_computation_router.py:29-51`; `copilot_sdk/scoring/scorer.py:404-427` or a new read-only scorer helper adjacent to it.

**Tests.** Create two checkpoints with different tensors and three real decisions; assert the endpoint rescored count, exact `would_change`, and that live `load_latest_centroids` is unchanged after the call.

### Gap 4 — C6 atomicity

**Evidence.** AGE already exposes `run_transaction` and uses it for evidence receipt writes at `../ci-platform/ci_platform/graph/age_graph_store.py:1600-1674`. SOC currently persists its L5 delta through `../gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:396-437` and writes Decision delta properties in `../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2322-2332`; no source-verified atomic Outcome+V2 checkpoint writer exists.

**Resolution — committed, not optional.** Add a SOC persistence helper that executes one `run_transaction` containing: the outcome node/property write, the V2 centroid checkpoint write, the Decision→Outcome link, and the Decision→SNAPSHOT_AFTER→CentroidCheckpoint link. The transaction starts immediately before the first outcome write and ends after the last edge write. On failure, return a failed learning result and do not expose a partially persisted checkpoint. Conservation aggregation and unrelated evidence receipts remain outside this transaction and are explicitly deferred.

**Files to change.** `../gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:396-437`; `../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2322-2332`; SOC tests adjacent to the outcome verification route; shared AGE API only if the existing transaction callback cannot express the combined Cypher.

**Tests.** Force a transaction callback failure after the outcome statement and assert neither Outcome nor CentroidCheckpoint is queryable. On success, assert both nodes and both relationships exist and carry the same decision/checkpoint identity.

### Gap 5 — invariant count 7 vs 9

**Evidence.** The design’s own enumerated gap set is {6,7,9,10,11,13,15,16,17}; only #13 and #17 are assigned to C3/C5. Therefore nine total, two in P0-P2, seven deferred.

**Resolution.** Treat #13 (rolling accuracy) and #17 (factor-version consistency) as mandatory assertions in this plan. Add a “deferred to GAE conformance” section listing #6, #7, #9, #10, #11, #15, #16. Do not mark those seven as implemented by P2.

**Tests.** Add one named assertion per in-scope invariant and a manifest test that the seven deferred IDs are explicitly marked deferred, not silently absent.

### Gap 6 — P1 PgBouncer status

**Evidence.** `../ci-platform/ci_platform/graph/age_client.py:118-129` defines pool settings and `:182-187` constructs the pool; defaults are bounded by a maximum of five. No PgBouncer configuration was found in the scanned repository. Five copilots × five connections is 25 connections, below PostgreSQL’s default 100 noted in the scan context.

**Resolution.** Enable the bounded AGE pool for P1 with `AGE_USE_POOL=true` and `AGE_POOL_MAX_SIZE=5` in each AGE deployment. Treat PgBouncer as a Program B operations item, not a P1 blocker. Add a startup log of pool mode and max size.

**Files to change.** `../ci-platform/ci_platform/graph/age_client.py:118-129,182-187`; deployment/env files for SOC and any other AGE app; pool tests in ci-platform.

**Tests.** Instantiate five clients in a disposable test configuration and assert configured max size is 5; assert no connection count exceeds 25 in the five-copilot test manifest. This is a configuration test, not a production load claim.

### Gap 7 — SOC empty-history response

**Evidence.** SOC raises 503 for no matching evolution rows at `../gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:161-171`.

**Resolution.** Keep the legacy SOC route’s array response for old frontend compatibility, but return `[]` with HTTP 200 when empty. Add the canonical shared route as `/api/self/centroid-history` with `{"checkpoints": [], "total": 0}`. Do not use 404 or 503 for an empty history.

**Files to change.** `../gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:107-171`; SOC `main.py:132-142`; shared model/router `copilot_sdk/backend/models.py:177-180` and `self_computation_router.py:29-51`.

**Tests.** Call both routes against an empty disposable store; assert status 200, legacy body `[]`, canonical body keys `checkpoints` and `total`, and no error log.

### Gap 8 — read/write-splitting scope

**Evidence.** The scorer stores one graph store and uses it during construction/load (`copilot_sdk/scoring/scorer.py:250-282`); no separate read/write handles are present.

**Resolution.** Define store selection at each copilot factory seam. The feature flags choose the single store instance supplied to that copilot’s scorer; they do not split reads and writes inside `CompoundingScorer`. Add `JM_READ_STORE`/`JM_WRITE_STORE` only at app composition if a future dual-store wrapper is explicitly implemented; P1 does not add an internal scorer split.

**Files to change.** `copilot_sdk/scoring/scorer.py:250-282` only for startup identity logging/validation; `apps/dataops/backend/app/main.py:749-751`, `apps/trading/backend/app/main.py:439-440`, `apps/purchasing/backend/app/main.py:707-709`, SOC `main.py:132-142`, and S2P `main.py:247-278` for factory wiring.

**Tests.** Construct each app scorer with its selected store and assert the same object services load and write; assert a store selection flag cannot change another copilot’s store.

### Additional gap A — SOC/S2P shared-router wiring

**Evidence.** Shared mounting exists for DataOps, Trading, Purchasing at the lines cited above. SOC mounts only framework routes (`main.py:132-142`), and S2P mounts only its centroid router (`main.py:247-253`).

**Resolution.** Add a shared-router adapter with the minimal `GraphStore` methods required by history to each app. Mount the canonical route after store creation. Preserve legacy aliases: SOC `/api/soc/centroid-evolution`; S2P `/api/s2p/centroid/all`, `/drift/{category}/{action}`, `/{category}/{action}`, and `/explain/{decision_id}`. The aliases must project the canonical data only where semantics match; S2P cell/explain endpoints remain distinct.

**Tests.** OpenAPI asserts `/api/self/centroid-history` in all five apps; legacy route tests continue to pass; an empty SOC and seeded S2P history return 200.

### Additional gap B — factor-hash validation cannot use current loader alone

**Evidence.** Hash is written by `scorer.py:1822-1839`, but `load_latest_centroids` returns only a tensor (`scorer.py:266-268`), so it cannot validate metadata.

**Resolution.** Add `get_latest_centroid_checkpoint(domain, include_v2=True)` to the protocol and adapters. In `from_preset`, validate tensor shape and `factor_names_hash` before using the checkpoint; on mismatch log checkpoint identity and use bootstrap. Keep `load_latest_centroids` as a compatibility method delegating to the validated reader.

**Tests.** Assert matching hash loads; altered factor order, altered hash, and wrong shape each cause bootstrap plus a visible warning; assert the warning includes domain and checkpoint ID.

### Additional gap C — startup checkpoint identity

**Evidence.** Startup precedence is in `scorer.py:250-282`, but no checkpoint identity is returned by the current loader. The V2 writer has a non-null checkpoint ID at `scorer.py:1826-1839`.

**Resolution.** Log domain, checkpoint ID, created epoch, tensor shape, factor hash, and source (`checkpoint` or `bootstrap`) at startup. Never log the full tensor.

**Test.** Capture startup logs and assert one structured record for both checkpoint and bootstrap paths.

## 3. Phase-by-Phase Implementation Plan

### P-1 — verification and freeze (1 day)

1. **Freeze contracts.** Read the current protocol and all adapters at `protocol.py:83-102,267-281`, SQLite `:1556-1640,2591-2637`, Memory `:777-815,1346-1419`, and AGE `:1356-1420,2620-2670`. Record the canonical factor order from `scorer.py:1822-1825`. Expected result: a matrix showing legacy/V2/L5 methods and timestamp representations.
2. **Freeze routes.** Query mounted routers at DataOps `main.py:749-751`, Trading `:439-440`, Purchasing `:707-709`, SOC `main.py:132-142`, and S2P `main.py:247-253`. Expected result: only three apps currently expose the shared route; SOC/S2P are action items.
3. **Freeze legacy consumers.** Search `/api/context/centroid-history`, `/api/soc/centroid-evolution`, `/api/s2p/centroid/`, and `getCentroidHistory`; expected result includes DataOps tests `test_dataops_backend.py:817-848` and SOC Playwright tests. Do not remove a route until this list is updated.
4. **Freeze invariants.** Create a manifest of nine gap IDs; mark #13 and #17 P0-P2, and #6/#7/#9/#10/#11/#15/#16 deferred to Program B/GAE conformance. This prevents an inaccurate “all invariants pass” claim.

### P0 — surface normalization and empty-state behavior (1–2 days)

1. Extend `CentroidHistoryResponse` at `models.py:177-180` only with backward-compatible optional quality fields (initially null). Add model tests asserting `checkpoints` is a list and `total == len(checkpoints)`.
2. Make the shared handler at `self_computation_router.py:29-51` call `get_centroid_checkpoints(..., include_v2=True)` and preserve `limit` 1..500. Add a real SQLite test with one legacy and one V2 checkpoint asserting both are returned.
3. Add the shared route adapter to SOC and S2P at their router registration points (`SOC main.py:132-142`; `S2P main.py:247-278`). Preserve the legacy aliases listed in Additional gap A.
4. Change SOC empty legacy response at `framework_router.py:161-171` to HTTP 200 `[]`; canonical empty response is the shared envelope. Add exact HTTP/body tests.
5. Migrate DataOps API callers/tests (`api.ts:401-413`, `test_dataops_backend.py:817-848`) to the shared schema. Keep a compatibility custom route until the caller search is empty.

**P0 verification:** run the five-app OpenAPI smoke check; run `python -m pytest tests/ -v` in the SDK and targeted backend suites in each app. The concrete gate is: five canonical routes respond 200, and all empty histories return the prescribed shape.

### P1 — loader, adapters, pool, identity, and transaction foundations (3–4 days)

1. Implement canonical `created_at_epoch` in the protocol and all three stores at the cited save/write/load locations. Backfill SQLite existing rows and add AGE compatibility conversion. Loader precedence becomes: valid V2/legacy checkpoint with highest epoch, then stable tie-breaker; bootstrap only if no valid row.
2. Add `get_latest_centroid_checkpoint` metadata access and factor-hash/shape validation at scorer startup (`scorer.py:250-282`, writer `:1822-1839`). Log checkpoint identity/source.
3. Implement the shared SOC/S2P GraphStore adapter and route aliases. Do not change `query_context` or unrelated scoring behavior.
4. Enable AGE pooling via `age_client.py:118-129,182-187` with max five; add pool-mode startup diagnostics. PgBouncer remains Program B.
5. Implement SOC atomic outcome+checkpoint persistence using `run_transaction` (`age_graph_store.py:1600-1674`) around the SOC persistence boundary (`gae_state.py:396-437`, `triage.py:2322-2332`).

**P1 conformance assertions:** each adapter returns the same newest checkpoint for the mixed timestamp fixture; V2 hash mismatch bootstraps; SOC failure leaves zero outcome/checkpoint artifacts; pool max is five; no legacy route regresses.

### P2 — quality, counterfactuals, lineage edge, and frontend completion (1 week)

1. Extend checkpoint write contracts at `protocol.py:267-281` and stores to carry `quality`, `quality_window`, `quality_correct`, `quality_total`, `quality_source`, and `quality_status`. Compute `_recent_quality(window=400)` from outcome records at checkpoint time. Legacy rows return null quality.
2. Implement the counterfactual endpoint specified in Gap 3. Use the checkpoint tensor and real decision factor vectors; bound the window and reject hash/shape mismatches.
3. Add SOC `SNAPSHOT_AFTER` creation inside the atomic writer. For other AGE V2 writes, retain existing edge creation (`age_graph_store.py:1103-1125,1421-1426`). P2 tests assert edge creation only; no traversal or fleet backfill is claimed.
4. Add factor-name hash validation and tests across SQLite, Memory, and AGE. An incompatible checkpoint is visible and falls back to bootstrap.
5. Finish DataOps frontend migration and delete the custom route only after the repository caller/test search is zero. Update `CentroidTimelinePanel.tsx:1-184` only as needed to consume the shared envelope.
6. Add shared JM writeback only after quality and lineage tests pass; write `decision_id`, checkpoint ID, factor hash, quality fields, and provenance together. This is not a substitute for Program B’s historical migration.

**P2 verification:** counterfactual replay has deterministic counts; quality is null for legacy and numeric only when outcome data exists; every new SOC checkpoint has a lineage edge; five-app route and frontend contract tests pass.

## 4. Test Plan

| Test | Concrete assertion | Store(s) | Phase/invariant |
|---|---|---|---|
| `test_history_includes_legacy_and_v2` | Response contains both IDs and `total == 2` when `include_v2` is enabled | SQLite | P0, C2 |
| `test_latest_uses_created_at_epoch` | Newer epoch wins despite lower insertion ID | SQLite, AGE, Memory | P1, C1 |
| `test_legacy_null_id_is_loadable` | A row with `checkpoint_id is None` is returned by startup load | all adapters | P1, C1 |
| `test_memory_matches_adapter_precedence` | Memory loads the same checkpoint ID as SQLite for identical rows | Memory, SQLite | P1, RMAP-6 |
| `test_factor_hash_mismatch_bootstraps` | Mismatched hash produces bootstrap tensor and a warning containing domain/ID | SQLite | P1, C5 |
| `test_shape_mismatch_bootstraps` | Wrong tensor shape is rejected and preset is used | SQLite | P1, C5 |
| `test_startup_identity_log` | Checkpoint and bootstrap paths each emit one structured source record | SQLite | P1 |
| `test_empty_shared_history` | HTTP 200 body is `{'checkpoints': [], 'total': 0}` | shared route | P0 |
| `test_soc_legacy_empty_history` | HTTP 200 body is `[]`, never 503 | SOC | P0 |
| `test_all_apps_mount_shared_history` | OpenAPI contains `/api/self/centroid-history` for five apps | five apps | P0 |
| `test_dataops_old_route_compatibility` | Compatibility URL returns shared envelope, not `snapshots` | DataOps | P0 |
| `test_counterfactual_exact_change_count` | Three decisions and a known alternate tensor yield expected `would_change` and rate | SQLite | P2, C3 |
| `test_counterfactual_is_read_only` | Checkpoint count, tensor, and live scorer state are unchanged | SQLite | P2 |
| `test_quality_uses_outcome_counts` | `quality_correct/quality_total` equals the last-400 outcome count, not verified rate | SQLite | P2, invariant #13 |
| `test_quality_legacy_is_null` | Legacy checkpoint has null quality fields and explicit legacy status | SQLite, Memory | P2 |
| `test_soc_outcome_checkpoint_atomic_failure` | Injected transaction failure leaves no Outcome, checkpoint, or linking edge | AGE/SOC disposable graph | P1/P2, C6 |
| `test_soc_snapshot_after_success` | Successful write has Decision→SNAPSHOT_AFTER→CentroidCheckpoint with matching ID | AGE/SOC disposable graph | P2, C4 |
| `test_dataops_route_callers_migrated` | Source/test search finds no active custom-route caller before deletion | DataOps | P2 |
| `test_pool_bound` | Configured AGE pool maximum is five | ci-platform | P1 |
| `test_deferred_invariants_manifest` | IDs 6,7,9,10,11,15,16 are explicitly marked deferred | SDK docs/test manifest | P0 |

Tests must use real stores/scorers; the repository testing rules prohibit fake `GraphStore`, scorer, learn, or outcome implementations (`CLAUDE.md:Testing Rules`). External HTTP calls may be mocked only where the test is specifically an adapter/network test.

## 5. Risk Register

| Risk | Severity | Mitigation | Owner |
|---|---|---|---|
| Mixed AGE timestamp types select the wrong checkpoint | P1 | Persist and order by numeric `created_at_epoch`; backfill and test mixed rows | P1 |
| Memory diverges from production adapter behavior | P1 | Add cross-adapter precedence tests and make Memory load V2 metadata | P1 |
| Existing null-id rows disappear on restart | P1 | Remove null filter, preserve legacy IDs, and test restart against real stores | P1 |
| Factor hash mismatch applies a tensor to the wrong factor order | P1 | Validate hash and shape before startup use; visible bootstrap warning | P1 |
| SOC route remains 503 and breaks console-error PW tests | P0 | Return 200 empty shape and retain legacy array alias | P0 |
| DataOps route deletion breaks hidden callers | P0 | Compatibility window plus repository caller search and migrated tests | P0/P2 |
| SOC/S2P cannot import the shared router due to separate app/store types | P0 | Add narrow adapter at each app factory; prove OpenAPI and live disposable-store route | Cross-repo |
| Outcome and checkpoint split after partial failure | P1 | One AGE `run_transaction` around both writes and edges; failure test | SOC/P1 |
| Quality field is mistaken for prediction accuracy | P2 | Source quality only from outcome correctness; label legacy/unknown explicitly | P2 |
| Counterfactual endpoint mutates live scorer | P2 | Clone scorer/profile and assert state unchanged | P2 |
| SNAPSHOT_AFTER is written but not queryable | P2 | Test edge creation now; defer traversal/backfill to Program B explicitly | Program B |
| Pool settings are safe in tests but not deployment | P1 | Log pool mode/max and run five-app smoke configuration | ci-platform |
| Seven deferred math gaps are reported as completed | P0 | Nine-gap manifest with explicit deferred IDs | P0 |

## 6. Dependency Map

```text
P-1 source/route/invariant freeze
  ├── P0 shared response + app mounts + empty-state aliases
  │     └── P1 loader/adapters and frontend caller migration
  │           ├── P2 quality fields
  │           ├── P2 counterfactual endpoint
  │           └── P2 SOC atomic checkpoint/lineage writer
  └── P1 timestamp/hash contract
        └── P2 counterfactual and quality provenance
```

Critical path: protocol/store metadata contract → startup loader validation → shared route mounts → SOC atomic writer → quality/counterfactual tests. DataOps custom-route deletion is dependent on frontend/test migration but does not block the loader implementation if the compatibility alias remains.

## 7. Cross-Repo Coordination

### `copilot-sdk`

Owns the protocol, shared models/router, scorer startup validation, SQLite/Memory adapters, counterfactual service, and SDK tests. Changes are at the cited `protocol.py`, `models.py`, `self_computation_router.py`, `scorer.py`, `sqlite_store.py`, and `memory_store.py` locations.

### `ci-platform`

Owns AGE timestamp normalization, V2/legacy history reads, transaction use, pool configuration, and AGE tests at `age_graph_store.py:1356-1420,1600-1674,2620-2853` and `age_client.py:118-129,182-187`.

### `gen-ai-roi-demo-v4-v50` (SOC)

Owns the shared-route adapter/alias in `main.py:132-142` and `framework_router.py:107-171`, plus atomic outcome/checkpoint persistence at `gae_state.py:396-437` and `triage.py:2322-2332`. SOC must coordinate with ci-platform’s transaction API and copilot-sdk’s response model.

### `s2p-copilot`

Owns mounting the canonical route beside `centroid_router.py:17-62` at `main.py:247-278`, preserving old explorer routes, and adding S2P route tests. It depends on the shared protocol/model but can implement its adapter independently once the P0 contract is frozen.

### Independent versus coordinated work

- Independent after P-1: DataOps caller migration, Trading/Purchasing route contract tests, Memory adapter tests.
- Coordinated: protocol changes with all adapters; shared response model with SOC/S2P; AGE transaction writer with SOC; frontend deletion with DataOps backend tests.
- Deferred: historical SQLite→AGE migration, full SNAPSHOT_AFTER traversal, cross-copilot backfill, and the seven out-of-scope math gaps.

## Exit Criteria

Implementation plan ready. **24 planned files across 4 repositories, 20 concrete test cases, estimated effort: 8–10 engineering days** (P-1 one day, P0 one to two, P1 three to four, P2 one week with parallel work). Production source was not modified by this design scan.
