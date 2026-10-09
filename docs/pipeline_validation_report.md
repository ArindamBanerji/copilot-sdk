# Pipeline Validation Report

**Date:** 2026-10-06  
**Result:** VALIDATION COMPLETE  
**Scope:** Validate the proposed 16-step S2P/JM/AGE pipeline against the current `copilot-sdk`, `s2p-copilot`, and `ci-platform` worktrees. No source or test code was changed.

## 1. Session and baselines

The most recent `copilot-sdk/docs/session_state.md` entry before this validation is **F-02 S2P Cross-Repo Verification**. Repository instructions in `AGENTS.md` say `DecisionStore` is deprecated, new scoring persistence uses `GraphStore`, memory is test/development only, AGE is production, and new SQLite graph consumers are forbidden.

| Suite | Pipeline assumption | Actual 2026-10-06 | Delta |
|---|---:|---:|---:|
| S2P | 2,187 passed, 18 failed, 45 errors; 2,250 collected | **2,186 passed, 19 failed, 45 errors; 2,250 collected** | -1 pass, +1 failure |
| SDK | 4,495 passed, 0 failed | **4,506 passed, 3 xfailed, 0 failed** | +11 passes; still clean |

The S2P delta is order/state sensitive: the former evolution-router ordering failure did not reproduce, while `test_s2p_record_outcome_updates_stats` and `test_s2p_promotion_when_threshold_exceeded` failed. The evolution migration step therefore remains real but its design must include state/reset determinism rather than only response-family ordering.

## 2. Codebase reality scan

### F-01 — GraphStoreNamespace and experiment isolation

Requested SDK grep results:

- `GraphStoreNamespace|graph_namespace|namespace.*graph` under `copilot_sdk/`: **EMPTY**.
- `GraphStoreNamespace|graph_namespace` under `tests/`: **EMPTY**.
- `copilot_sdk/s2p_differentiation/`: **MISSING**.

The finding is nevertheless real at the actual path:

- `apps/s2p_differentiation/engine.py:20` imports `InMemoryGraphStore`.
- `apps/s2p_differentiation/engine.py:178` defines `_make_scorer`.
- `apps/s2p_differentiation/engine.py:179` creates `InMemoryGraphStore(domain="s2p")`.
- `run_three_arms()` calls `_make_scorer` separately for the governed and hand-specified arms.

**Answer:** `GraphStoreNamespace` does not exist and no equivalent domain-rewriting experiment view was found. The module location in the design is wrong, but the per-arm store violation exists under `apps/`.

### F-03 — SQLiteGraphStore and DualWriteStore

SDK source matches:

- `copilot_sdk/migrate/__main__.py:91` imports `SQLiteGraphStore`.
- `copilot_sdk/migrate/__main__.py:94` constructs the SQLite migration source.
- `copilot_sdk/migrate/__main__.py:97` passes it to `ArchiveReconciler`.
- `copilot_sdk/graph/dual_write_store.py:19` imports `SQLiteGraphStore`.
- `copilot_sdk/graph/dual_write_store.py:36` defines `DualWriteStore`.
- `copilot_sdk/graph/dual_write_store.py:61` contains concrete SQLite type checks.
- `copilot_sdk/graph/sqlite_store.py:393` defines `SQLiteGraphStore`.
- `copilot_sdk/migrate/reconcile_archive.py:20-28` retains a SQLite-shaped source dependency.
- Runtime `apps/` grep for `SQLiteGraphStore|DualWriteStore`: **EMPTY**.
- `copilot_sdk/graph/sqlite_store.py`: **EXISTS**.
- `copilot_sdk/graph/dual_write_store.py`: **EXISTS**.
- `copilot_sdk/graph/migrate/`: **MISSING**; the actual migration package is `copilot_sdk/migrate/`.
- Graph exports/factory/outcome service grep: **EMPTY** for the retired types.

Additional blast radius:

- 50 SDK test files still reference `SQLiteGraphStore` or `DualWriteStore`.
- 9 S2P Python files reference those types, including production/demo `backend/demo/s2p_demo.py`.
- `ci-platform/tests/test_age_graph_store_v.py:154-156` imports and constructs `SQLiteGraphStore`.

**Answer:** DSTORE-MIGRATE-2 removed these backends from the factory and app runtime wiring, but it did not delete the implementations, migration dependency, or extensive tests. F-03 is partial, not complete.

### F-04 — SQLiteSignalStore and cross-copilot signals

Matches:

- `copilot_sdk/backend/signal_store.py:24` defines `SQLiteSignalStore`.
- `copilot_sdk/backend/cross_signal_router.py:16-20` imports it.
- `copilot_sdk/backend/cross_signal_router.py:61-66` documents and constructs it as the default.
- `apps/trading/backend/app/main.py:98,579` imports and wires it.
- `apps/purchasing/backend/app/main.py:106,930` imports and wires it.
- `apps/dataops/backend/app/main.py:85,936` imports and wires it.
- `copilot_sdk/signals/`: **MISSING**; the actual implementation is under `copilot_sdk/backend/`.
- S2P backend `SignalStore|signal_store` grep: **EMPTY**.

**Answer:** the separate SQLite signal authority exists and is live in all three SDK-hosted copilots. F-04 is needed.

### F-05 — durable side-store fallbacks

The paths named in the exploratory grep are partly stale:

- `copilot_sdk/scoring/outcome/`: **MISSING**.
- `copilot_sdk/scoring/promotion/`: **MISSING**.
- `copilot_sdk/evolution/variant_store.py`: **EXISTS**.
- `copilot_sdk/twin/store.py`: **EXISTS**.

The real implementations exist elsewhere:

- `copilot_sdk/outcome/ledger.py:14` defines SQLite-backed `OutcomeLedger`.
- `copilot_sdk/promotion/core.py:111` defines SQLite-backed `PromotionStore`.
- `copilot_sdk/promotion/core.py:225` silently selects `store or PromotionStore()`.
- `copilot_sdk/evolution/variant_store.py:191` defines `SQLiteVariantStore`.
- `copilot_sdk/evolution/__init__.py:33,59` exports `SQLiteVariantStore`.
- `copilot_sdk/twin/store.py:14` defines file-backed `FrozenTwinStore`.
- `copilot_sdk/twin/service.py:21` silently selects `store or FrozenTwinStore()`.
- `apps/purchasing/backend/app/services/purchasing_control.py:203-209` selects SQLite/file ledgers when capabilities are absent.
- `apps/trading/backend/app/services/claim_gate.py:134-136` selects `PromotionStore` when no graph store is supplied.
- `tests/evolution/test_sqlite_variant_store.py` and outcome/promotion/twin test suites directly exercise these durable authorities.

The requested scoring grep also finds `copilot_sdk/scoring/persistence_outbox.py:8,127-129`; this is the explicitly exempt pending-write outbox and must stay.

**Answer:** some proposed paths are phantom, but F-05 itself is real and needed at the actual module locations.

### F-06 — cross-request verified-decision cache

Matches in `copilot_sdk/scoring/scorer.py`:

- `218` declares `_verified_decisions_cache`.
- `1008-1009`, `1185-1186`, and `1991` invalidate it only on local paths.
- `2886-2892` returns the retained list across calls.
- `_fingerprint_cache` at `219,1347-1352` is another scorer-object cache and must be classified during implementation; it is derived from verified decisions.
- `copilot_sdk/scoring/compounding.py`: **MISSING**.

**Answer:** the governed verified-decision cache exists exactly as described. F-06 is needed; its scope should explicitly classify `_fingerprint_cache` rather than deleting it blindly.

### F-07 — query-serving caches

Matches:

- `copilot_sdk/backend/conservation_router.py:46` reads a materialized conservation response before live state.
- `copilot_sdk/backend/response_materializer.py:21-110` retains graph-derived responses with a TTL.
- `copilot_sdk/backend/scoring_router.py:152,183-208` accepts and reads prior entity context.
- `copilot_sdk/backend/scoring_router.py:158-180` retains a scorer object; this is dependency-object reuse, not by itself a query-response cache, but that scorer contains F-06 caches.
- `copilot_sdk/di/query_service.py:54-69,220-228,292` retains and serves complete `QueryResponse` values.
- Trading, Purchasing, and DataOps mains instantiate `EntityCache`/`EntityContextCacheAdapter` and graph response materializers.
- `copilot_sdk/backend/conservation_router.py:22` imports `cached_static` but does not use it; this is a stale import, not the substantive cache.

**Answer:** prohibited cross-request query/context/conservation caches are live. F-07 is needed.

### F-08 — shared demo preseed

Matches:

- `copilot_sdk/demo/` exists with `preseed.py`, `bundle.py`, `startup.py`, and related modules.
- `scripts/preseed_all_copilots.py`: **EXISTS**.
- `copilot_sdk/demo/preseed.py:118-136` seeds all domains.
- `copilot_sdk/demo/preseed.py:175` returns a detached cross-copilot signal dictionary.
- `copilot_sdk/demo/preseed.py:224-230` creates a separate `InMemoryGraphStore(domain=domain)` for each domain.

**Answer:** preseed infrastructure exists and the isolated-store/detached-signal finding remains. F-08 is needed after F-04 defines the graph signal contract.

### F-09 — governed transfer artifacts

Matches:

- `copilot_sdk/transfer/` exists with cross-domain, registry, warm-start, mapping, and chain-transfer modules.
- `copilot_sdk/backend/transfer_router.py:642` falls back to `_demo_patterns_for_mapping`.
- `copilot_sdk/backend/transfer_router.py:725` defines the fabricated pattern helper.
- `copilot_sdk/backend/transfer_router.py:754` labels those patterns `provenance="demo"`.
- `copilot_sdk/backend/transfer_router.py:354` persists `validation_status="validated"`.
- Source/target conservation fields exist at `290-300`, so the original design should preserve rather than re-add them; source artifact IDs and the no-demo execution rule remain missing.
- `copilot_sdk/transfer/chain_transfer.py:63,100` also emits demo provenance and must be reviewed for execution versus preview semantics.

**Answer:** transfer infrastructure exists and synthetic execution fallback is live. F-09 is needed with slightly reduced metadata scope because both conservation states are already produced in one path.

### AGE unification and graph contracts

SDK/ci-platform evidence:

- The concrete `AGEGraphStore` is not implemented inside `copilot-sdk`; `copilot_sdk/graph/factory.py:57-71` dynamically loads `ci_platform.graph.age_sdk_adapter.AGEGraphStoreAdapter`.
- `copilot_sdk/graph/factory.py:189-208` constructs the adapter and performs production validation.
- `ci-platform/ci_platform/graph/age_graph_store.py:94` defines `AGEGraphStore`.
- `ci-platform/ci_platform/graph/age_sdk_adapter.py:11` defines `AGEGraphStoreAdapter`.
- `ci-platform/ci_platform/graph/age_sdk_adapter.py:29` exposes `production_ready` structurally.
- `copilot_sdk/graph/protocol.py:40-50` defines `ProductionReadyStore`.

Graph contracts already exist:

- `apps/trading/backend/app/graph_contract.py:8` defines `TRADING_GRAPH_CONTRACT`.
- `apps/purchasing/backend/app/graph_contract.py:8` defines `PURCHASING_GRAPH_CONTRACT`.
- `apps/dataops/backend/app/graph_contract.py:8` defines `DATAOPS_GRAPH_CONTRACT`.
- `s2p-copilot/backend/app/graph_contract.py:108` defines `S2P_GRAPH_CONTRACT`.

**Answer:** AGE production infrastructure and per-copilot graph contracts already exist. Remaining AGE work is targeted adapter/protocol and stale-runtime cleanup; a general “introduce AGE/graph contracts” step would be redundant.

### Factory state

`copilot_sdk/graph/factory.py:19` declares `_VALID_BACKENDS = {"memory", "age"}`. Lines `41-46` reject every other backend. The memory branch is `159-171`; AGE is the only remaining alternative at `173-208`. `db_path` is retained only as a deprecated no-op for compatibility (`115-119`, `159-165`). SQLite is already gone from the factory.

## 3. Cross-repository scan

### s2p-copilot

- `backend/demo/s2p_demo.py:12,221` imports and constructs `SQLiteGraphStore` in production/demo code.
- Eight additional S2P test files import or construct it, for 9 affected Python files total.
- `backend/app/s2p_graph_status.py:231` defines `S2PActiveAGEGraphStore`.
- `backend/tests/conftest.py:51,59` imports/constructs ci-platform `AGEGraphStore` for live fixtures.
- `backend/app/graph_contract.py:108` defines `S2P_GRAPH_CONTRACT`.
- No S2P `SignalStore` reference exists.
- `backend/app/main.py:3,54` uses SQLite for another local store; `proposal_service.py` and several evidence/enrichment modules also use SQLite or SQLite exceptions. These are not automatically graph backends, so each must be classified under F-05/P8 before deletion.

### ci-platform

- `ci_platform/graph/` contains `age_client.py`, `age_graph_store.py`, `age_sdk_adapter.py`, `agtype.py`, and exports.
- Production code contains no `SQLiteGraphStore` or `DualWriteStore` match.
- `tests/test_age_graph_store_v.py:154-156` still imports and constructs SDK `SQLiteGraphStore`; F-03 deletion would break this test unless it is migrated first.

## 4. Validation of the original 16 steps

The original 16 steps are the eight S2P migration categories plus the eight approved JM execution groups.

| Step | Finding | Status | Evidence | Recommendation |
|---:|---|---|---|---|
| 1 | S2P RC-2 concrete SQLite assertion | NEEDED | `test_graphstore_consolidation.py` still imports/asserts `SQLiteGraphStore`; live suite fails it. | Merge into the consolidated F-03/S2P SQLite retirement step rather than execute separately. |
| 2 | S2P RC-3 ledger ordering | NEEDED | Two live failures show reversed IKS/conservation history; stale test-store ordering remains. | Keep as a small test migration. |
| 3 | S2P RC-4 F-02 conservation fixtures | NEEDED | Two live failures remain: obsolete monkeypatch and aggregate-only fixture. | Keep; seed real ordered rows and use live F-02 interface. |
| 4 | S2P RC-8 health marker | NEEDED | Both health paths return fail-closed 503 because test double lacks `production_ready`. | Keep as test-only protocol-conformance fix. |
| 5 | S2P RC-5 evolution determinism | PARTIAL | Former router-order failure did not reproduce; two state/stat/promotion tests now fail. | Redesign scope around fixture/reset/store-order determinism, including canonical family order. |
| 6 | S2P RC-1 SQLite config/status/rollback | NEEDED | 45 setup errors plus rollback failure reproduce; config still says `sqlite|age`. | Merge with F-03; memory is test/dev rollback, production stays AGE-only/fail-closed. |
| 7 | S2P RC-6 ISO timestamp ordering | NEEDED | `composite_gate.py:113` and `legacy_signal_filter.py:53` call `float(created_at)`; two live AGE shadow failures. | Keep as shared SDK normalization work. |
| 8 | S2P RC-7 private AGE traversal | NEEDED | Seven live failures; reader calls `_store`, `_run_query`, and `_node_to_dict`. | Keep; add the minimal bounded public traversal protocol across ci-platform/S2P. |
| 9 | JM Group 1 / F-02 rolling-400 | ALREADY_DONE | Session records complete/fixer/re-review; SDK has shared `_rolling_q`, canonical ordering, tests; SDK suite is clean. | Remove from execution pipeline; retain regression checks. |
| 10 | JM Group 2 / F-06 + F-07 caches | NEEDED | `_verified_decisions_cache`, DI response cache, entity-context read-through, response materializer, and conservation shortcut all exist. | Keep; explicitly classify `_fingerprint_cache` and static-only caches. |
| 11 | JM Group 3 / F-01 namespace experiment | NEEDED | Namespace greps are empty; actual engine creates separate per-arm memory stores. | Keep with corrected `apps/s2p_differentiation` paths; AGE infrastructure already exists. |
| 12 | JM Group 4 / F-03 SQLite/dual retirement | PARTIAL | Factory/apps runtime are clean, but implementation files, migration imports, 50 SDK test files, 9 S2P files, and one ci-platform test remain. | Keep with reduced factory scope and expanded cross-repo migration inventory; merge S2P steps 1 and 6. |
| 13 | JM Group 5 / F-04 graph signals | NEEDED | `SQLiteSignalStore` is the router default and is explicitly wired in three apps. | Keep; use each app's already-selected graph store. |
| 14 | JM Group 6 / F-05 side stores | NEEDED | Outcome, promotion, variant, proof, and twin durable fallbacks exist at corrected paths. | Keep after F-03 interface decisions; preserve only write-only outboxes. |
| 15 | JM Group 7 / F-09 transfer | NEEDED | Router fabricates demo patterns and can persist them as validated. | Keep; scope metadata work to fields still missing. |
| 16 | JM Group 8 / F-08 preseed | NEEDED | Preseed creates one memory store per domain and returns detached signal data. | Keep after F-04; reuse one local store only for offline/test demo. |

### Status totals

- **NEEDED:** 13
- **PARTIAL:** 2
- **ALREADY_DONE:** 1
- **PHANTOM:** 0
- **DEFERRED:** 0

Paths/modules were phantom in F-01 and F-05, but the underlying violations were found at current paths; therefore the steps themselves are not classified PHANTOM. AGE infrastructure exists cross-repository, so no remaining step must be deferred for lack of AGE.

## 5. Simplified pipeline

| Phase | Step | What | Principal files | Model | Effort |
|---:|---:|---|---|---|---|
| 1 | 1 | Fix S2P ledger test-store ordering (RC-3). | `s2p-copilot/backend/tests/test_compounding_ledger.py` | spark | Simple |
| 1 | 2 | Migrate S2P conservation fixtures to real F-02 rows (RC-4). | `test_s2p_conservation_coverage.py`, `test_s2p_score_endpoint.py` | spark | Simple |
| 1 | 3 | Make health test double satisfy `ProductionReadyStore` (RC-8). | `s2p-copilot/backend/tests/test_scaffold.py` | spark | Simple |
| 1 | 4 | Diagnose and fix evolver store/reset/order determinism (RC-5 revised). | `app/services/s2p_evolver.py`, evolver/router tests | sol | Medium |
| 2 | 5 | Remove scorer/query/context/conservation cross-request caches (F-06/F-07). | scorer, DI query service, routers/materializer, three app mains/tests | sol | Complex |
| 2 | 6 | Normalize numeric/ISO decision timestamps with stable-ID ordering (RC-6). | SDK composite gate/legacy filter and S2P shadow tests | sol | Medium |
| 3 | 7 | Consolidated SQLite graph retirement and S2P cutover (F-03 + RC-1 + RC-2). | SDK graph/migrate/tests; S2P graph status/demo/tests; ci-platform migration test | sol | Complex |
| 3 | 8 | Move cross-copilot signals to shared graph events (F-04). | signal store/router, three app mains, event tests | sol | Complex |
| 3 | 9 | Remove durable side-store authorities from integrated paths (F-05). | outcome, promotion, evolution, twin, Purchasing/Trading composition/tests | sol | Complex |
| 4 | 10 | Replace S2P private AGE traversal with bounded public protocol (RC-7). | S2P reader/wrapper/tests; ci-platform store/adapter/tests | sol | Complex |
| 4 | 11 | Add `GraphStoreNamespace` and run experiment arms on one AGE graph (F-01). | namespace adapter, scorer domain wiring, `apps/s2p_differentiation` | sol | Complex |
| 4 | 12 | Require governed persisted transfer artifacts; remove synthetic execution (F-09). | transfer router/types/adapters/tests | spark | Medium |
| 5 | 13 | Share offline demo graph and persist/read signal evidence (F-08). | `copilot_sdk/demo/preseed.py`, preseed/demo tests | spark | Medium |

Dependencies:

- Steps 1-4 are independent cleanup and may run in any order.
- Step 5 precedes Step 11 so namespace work is built on fresh reads.
- Step 7 precedes Steps 9 and 10; it stabilizes graph retirement and removes the stale S2P config surface also touched by traversal wiring.
- Step 8 precedes Step 13 because preseed must use the final graph signal schema.
- Steps 8, 9, and 12 can otherwise proceed in parallel after Step 7's protocol/retirement decisions are recorded.
- Step 10 is internally sequential: ci-platform store, adapter, S2P wrapper, then consumer/tests.

### Removed

- **Original Step 9 / F-02:** already complete and verified by the clean 4,506-pass SDK suite. Keep regression tests only.

### Merged

- **Original S2P steps 1 and 6** merge into JM F-03. They are the S2P caller/test portion of the same SQLite backend retirement and should not be edited twice.

### Kept

- All other findings have live source evidence or reproduce in current tests.

### Scope reductions and corrections

- F-03 no longer changes factory backend selection or app runtime exports; those are already clean. It still has a large cross-repo deletion/migration surface.
- F-01 targets `apps/s2p_differentiation`, not nonexistent `copilot_sdk/s2p_differentiation`.
- F-05 targets `copilot_sdk/outcome`, `promotion`, `evolution`, and `twin`, not nonexistent `copilot_sdk/scoring/outcome` and `scoring/promotion` directories.
- F-09 need not invent source/target conservation fields already emitted in the current router; it must remove demo execution and persist complete governed source artifact evidence.
- General AGE/graph-contract creation is removed from scope because the adapter and all four contracts exist.
- RC-5 scope is revised rather than reduced: current evidence requires state/reset determinism in addition to family ordering.

### Revised size

- **Original:** 16 steps.
- **Simplified:** 13 implementation steps.
- **Effort mix:** 3 simple, 4 medium, 6 complex.
- **Estimated effort:** approximately 13 implementation prompts plus review rounds; about 60-90 focused engineering hours excluding live AGE provisioning and data-cutover waits. Consolidating steps reduces repeated edits, but F-03 remains larger than its original factory-only framing because of the newly confirmed cross-repo test/demo blast radius.

## 6. Risk flags and surprises

1. **S2P baseline drift:** the suite now has 19 failures rather than 18. Evolution failures are state/order sensitive, so the prior RC-5 design is incomplete.
2. **SQLite deletion blast radius is much larger than the prior S2P design:** 50 SDK test files, 9 S2P files, and a ci-platform test reference the retired backend. Deleting the implementation before migrating these imports will break collection.
3. **S2P production/demo dependency:** `backend/demo/s2p_demo.py` still constructs `SQLiteGraphStore`; this was not part of the 63-case failure design because that path is not exercised by the failing suite.
4. **Migration package location:** planned paths using `copilot_sdk/graph/migrate` are wrong; archive migration lives at `copilot_sdk/migrate` and still depends on the GraphStore-shaped SQLite class.
5. **F-05 phantom paths conceal real code:** outcome and promotion stores are real under top-level SDK packages and integrated app services still select them.
6. **Additional S2P SQLite stores need classification:** proposal, VLD/K-utility, evidence, and enrichment modules use `sqlite3` or SQLite exceptions. Some may be non-graph local workflow state, but each must be checked against P8 before F-05 concludes; do not bulk-delete by token.
7. **Outbox carve-out:** `copilot_sdk/scoring/persistence_outbox.py` is a legitimate write-only outage buffer and must not be removed with F-03/F-05.
8. **Cache classification:** the scorer's `_fingerprint_cache` and scorer-object reuse were not explicitly separated in the original F-06/F-07 plan. Derived graph memory must be fresh; dependency object reuse can remain if it holds no cross-request graph results.
9. **AGE is external but available:** the SDK has no concrete AGE implementation, but ci-platform provides the store and adapter now. Work should remain cross-repo and protocol-first, not be deferred or duplicate AGE inside the SDK.
10. **Graph contracts already exist:** any planned creation of Trading, Purchasing, DataOps, or S2P graph contracts would conflict with live definitions and tests.
