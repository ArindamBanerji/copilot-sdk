# DecisionStore + SQLiteGraphStore Elimination — Design

**Date:** October 2, 2026
**New Standing Rule:** DecisionStore is deprecated; no new code may add DecisionStore dependencies; all new scoring persistence goes through GraphStore. SQLiteGraphStore is eliminated — two backends remain: InMemoryGraphStore (test/dev) and AGEGraphStore (prod).

---

## 1. Problem

Two parallel SQLite paths exist alongside the GraphStore protocol:

1. **DecisionStore** (`copilot_sdk/scoring/storage.py`) — legacy SQLite class with its own tables (decisions, centroids, decisions_archive). Predates GraphStore. Still importable. Gravity well for Codex.

2. **SQLiteGraphStore** (`copilot_sdk/graph/sqlite_store.py`, 167KB) — proper GraphStore implementation over SQLite. Used as "dev profile" backend. But: as long as any SQLite exists, Codex routes through it. Every protocol addition requires a third implementation. The dev use case is served by InMemoryGraphStore (fast, no setup) or local AGE (real backend).

Both must go. Two backends remain: InMemoryGraphStore (test/dev) and AGEGraphStore (prod).

## 2. Migration Surface

### 2A. class DecisionStore (storage.py) — DELETE

All methods already have GraphStore equivalents:
- save_decision -> GraphStore.write_decision
- save_outcome -> GraphStore.write_outcome
- save_centroids -> GraphStore.write_outcome_and_update_centroid
- load_latest_centroids -> GraphStore.read_centroids
- get_decision -> GraphStore.get_decision
- get_verified_decisions -> GraphStore.get_verified_decisions
- get_all_decisions -> GraphStore.get_all_decisions
- count_verified -> GraphStore.count_verified
- count_correct -> GraphStore.count_correct
- count_categories_with_n -> GraphStore.count_categories_with_n
- get_centroid_checkpoints -> review if needed on GraphStore

### 2B. SQLiteGraphStore (sqlite_store.py) — DELETE

167KB file. All protocol methods implemented. But InMemoryGraphStore covers the same protocol for test/dev. AGEGraphStore covers prod.

Consumers that specify SQLiteGraphStore or db_path must switch to InMemoryGraphStore (test/dev) or AGEGraphStore (prod injection).

### 2C. KUtilityStore (investigation.py) — MIGRATE

Reaches into decision_store.conn for raw SQL on k_utility table. Already has production guard rejecting SQLite connections.

Action: Add save_k_utility / get_k_utilities to GraphStore protocol. Implement in InMemoryGraphStore (dict) and AGEGraphStore (graph node). Update KUtilityStore to use protocol methods.

### 2D. DataOpsGovernance (dataops_governance.py) — MIGRATE

Opens its own sqlite3.connect() for dataops_holdout table. Already has production guard.

Action: Add save_holdout_decision / get_holdout_decisions to GraphStore protocol. Implement in both backends. Update DataOpsGovernance to accept GraphStore.

### 2E. from_preset db_path parameter — REMOVE

Creates SQLiteGraphStore for dev profile. With SQLiteGraphStore gone, db_path has no target. Remove parameter. Dev profile uses InMemoryGraphStore.

### 2F. Experiment scripts — UPDATE

c1_c6_campaign_v1.py references SQLiteDecisionStore. Update to InMemoryGraphStore.

### 2G. Test files (~10-15 files) — UPDATE

- Tests testing DecisionStore itself: DELETE
- Tests testing SQLiteGraphStore: DELETE or convert to InMemoryGraphStore
- Tests using DecisionStore/SQLiteGraphStore as fixtures: switch to InMemoryGraphStore
- Tests importing from storage.py: remove imports

### 2H. _S2PGraphStore, DemoGraphStore, AGEGraphStoreAdapter — REVIEW

graphstore_consolidation.md documents these subclasses. If any inherit from SQLiteGraphStore, they must be reparented or eliminated.

## 3. GraphStore Protocol Additions

### 3A. K-Utility Storage

    save_k_utility(domain, episode_id, k, utility, metadata=None) -> str
    get_k_utilities(domain, episode_id=None, limit=100) -> list[dict]

### 3B. Holdout Storage

    save_holdout_decision(domain, decision_id, holdout_group, metadata=None) -> str
    get_holdout_decisions(domain, holdout_group=None) -> list[dict]

Two implementations each: InMemoryGraphStore (dict/list) and AGEGraphStore (graph nodes or properties).

## 4. Execution Phases

### Phase A: Protocol extension (non-breaking)
1. Add k_utility + holdout abstract methods to GraphStore protocol
2. Implement in InMemoryGraphStore
3. Implement in AGEGraphStore
4. Tests for new protocol methods

### Phase B: Consumer migration (non-breaking)
5. KUtilityStore -> use GraphStore protocol
6. DataOpsGovernance -> use GraphStore protocol
7. Update test fixtures: DecisionStore -> InMemoryGraphStore
8. Update test fixtures: SQLiteGraphStore -> InMemoryGraphStore
9. Remove db_path from from_preset
10. Update experiment scripts

### Phase C: Deletion (breaking)
11. Delete class DecisionStore from storage.py (or delete storage.py if nothing else lives there)
12. Delete sqlite_store.py (SQLiteGraphStore)
13. Delete tests that tested DecisionStore/SQLiteGraphStore directly
14. Remove all imports of DecisionStore and SQLiteGraphStore
15. Handle _S2PGraphStore/DemoGraphStore/AGEGraphStoreAdapter if they inherit from SQLiteGraphStore

### Phase D: Gates + verification
16. Add no_decision_store_import_anywhere gate to test_age_unification_invariants.py
17. Add no_sqlite_graphstore_import gate
18. Full test suite passes
19. mypy clean

## 5. Files Changed (estimated)

DELETE:
- copilot_sdk/scoring/storage.py (or gut DecisionStore from it)
- copilot_sdk/graph/sqlite_store.py
- Tests that test DecisionStore directly
- Tests that test SQLiteGraphStore directly

MODIFY:
- copilot_sdk/graph/memory_store.py (add k_utility + holdout)
- ci_platform/graph/age_client.py (add k_utility + holdout)
- copilot_sdk/scoring/investigation.py (KUtilityStore migration)
- copilot_sdk/scoring/dataops_governance.py (holdout migration)
- copilot_sdk/scoring/scorer.py (remove db_path from from_preset)
- tests/test_age_unification_invariants.py (new gates)
- ~10-15 test files (fixture updates)
- 1-2 experiment scripts

## 6. Risk

| Risk | Mitigation |
|---|---|
| Hidden SQLiteGraphStore subclasses | Phase C step 15 reviews _S2PGraphStore etc. |
| Tests that construct SQLiteGraphStore for fixtures | grep catches all, switch to InMemoryGraphStore |
| db_path used in CI or scripts | grep for db_path across all repos |
| AGEGraphStore missing methods that SQLiteGraphStore had | Protocol is canonical — if AGE doesn't have it, it wasn't protocol |

## 7. Separate Concern: Performance

The deep-copy bottleneck in get_verified_decisions() (169.6s in 1,000-decision tests) is a SEPARATE issue from this migration. It lives in InMemoryGraphStore's implementation and will persist after this migration. A follow-up prompt should optimize the deep-copy path. This migration does NOT attempt to fix performance.

---

*DecisionStore + SQLiteGraphStore Elimination Design v2 — October 2, 2026*
