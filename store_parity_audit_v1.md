# Store Parity Audit v1

**Date:** 2026-08-06  
**Scope:** AGE, SQLite, and InMemory graph stores  
**Production graph modified:** NO

## PARITY MATRIX

| Method | AGE | SQLite | Memory | Parity? | Fixed? |
|---|---|---|---|---|---|
| `write_outcome` | Idempotent identical outcome; conflict raises `ValueError`; missing decision raises `KeyError` (`ci-platform/ci_platform/graph/age_graph_store.py:886-1049`) | Same behavior after fix (`copilot_sdk/graph/sqlite_store.py:1162-1257`) | Same behavior after fix (`copilot_sdk/graph/memory_store.py:549-610`) | YES | YES |
| `write_centroid_checkpoint` | Idempotent by checkpoint ID; conflict raises; stores full V2 payload (`age_graph_store.py:1414-1479`) | Same semantics and full payload (`sqlite_store.py:1569-1653`) | Same semantics and full payload (`memory_store.py:791-815`) | YES | YES |
| `load_latest_centroids` | Selects newest checkpoint across legacy and V2 by `created_at` (`age_graph_store.py:2719-2736`) | Selects newest checkpoint across legacy and V2 by `created_at,id` (`sqlite_store.py:2639-2650`) | Selects newest legacy or V2 checkpoint by timestamp (`memory_store.py:1384-1401`) | YES | YES |
| `get_centroid_checkpoints` | `include_v2` controls null/non-null checkpoint IDs; returns oldest-to-newest (`age_graph_store.py:2891-2910`) | Same filtering/order (`sqlite_store.py:2684-2714`) | Same filtering/order (`memory_store.py:1410-1442`) | YES | YES |
| `update_centroid` (L5) | Domain/category/action upsert with graph persistence (`age_graph_store.py:2275-2312`) | Domain/category/action upsert in `l5_centroids` (`sqlite_store.py:2292-2328`) | Domain/category/action in-memory upsert (`memory_store.py:1196-1234`) | YES | NO |
| `write_conservation_status` + latest read | Writes status and links domain summary; latest query is domain-scoped (`age_graph_store.py:1234-1299,1968-2005`) | Writes/read latest snapshot (`sqlite_store.py:1421-1468,1782-1820`) | Writes/read latest snapshot (`memory_store.py:718-765,976-1018`) | YES, semantic fields normalized | YES |
| `count_verified` / `count_correct` | Counts confirmed/overridden decisions and correct subset (`age_graph_store.py:2216-2246`) | Same status predicates (`sqlite_store.py:2262-2290`) | Same status predicates (`memory_store.py:1160-1181`) | YES | NO |
| `save_centroids` (legacy) | Writes legacy null-ID checkpoint (`age_graph_store.py:2678-2717`) | Writes legacy null-ID checkpoint (`sqlite_store.py:2604-2637`) | Writes legacy checkpoint without an explicit ID; exposed as null-ID semantics | YES, semantic | NO |

## DIVERGENCES FOUND AND FIXED

1. **SQLite duplicate outcomes were never idempotent.**

   SQLite raised on every existing outcome (`sqlite_store.py:1191-1196`), while AGE compared the existing action/correctness and silently accepted an identical retry (`age_graph_store.py:1018-1045`). SQLite now performs the same comparison, returns on an identical retry, rejects conflicts, and enforces pending status (`sqlite_store.py:1191-1209`).

2. **Memory duplicate outcomes were never idempotent.**

   Memory unconditionally raised for an existing outcome (`memory_store.py:572-573`). It now matches AGE’s identical-retry, conflict, and pending-status behavior (`memory_store.py:572-592`).

3. **Legacy-only loader trap.**

   AGE and SQLite filtered `load_latest_centroids` to `checkpoint_id IS NULL`; Memory ignored the V2 protocol checkpoint collection. All three now select the newest checkpoint across legacy and V2 by creation time (`age_graph_store.py:2719-2727`, `sqlite_store.py:2639-2645`, `memory_store.py:1384-1401`).

4. **SQLite omitted the V2 `action` field when normalizing checkpoints.**

   The column exists in the schema and is written by `write_centroid_checkpoint`, but `_checkpoint_from_row` omitted it. The normalized SQLite result now includes `action` (`sqlite_store.py:3466-3484`).

5. **AGE left V2 `shape` as a JSON string.**

   AGE stores `shape` as serialized JSON (`age_graph_store.py:1467-1473`), but `_node_to_dict` did not parse that field. `shape` is now included in the JSON normalization set (`age_graph_store.py:3247-3274`).

6. **AGE conservation domain filtering used SQL tuple syntax instead of AGE list syntax.**

   `get_latest_conservation_statuses` generated `IN (...)`, which AGE rejected as “object of IN must be a list.” It now generates `IN [...]` (`age_graph_store.py:1973-1978`).

## DIVERGENCES DEFERRED

- The persistence substrates differ intentionally: AGE uses graph nodes/edges, SQLite uses relational tables, and Memory uses dictionaries. The tested public semantics are aligned.
- AGE supports an additional optional `decision_id` argument on `write_centroid_checkpoint` (`age_graph_store.py:1426-1428`) that is not part of the shared protocol. This is additive lineage functionality, not a parity failure.
- Live history endpoint checks for Trading, Purchasing, DataOps, and S2P timed out after the launcher could not terminate pre-existing processes due access-denied errors. This is an operational/process-isolation issue, not a store-method parity result. SOC’s live history endpoint returned `200` with an empty envelope.

## PARITY TESTS

Saved to `tests/test_store_parity.py`.

1. `test_write_outcome_idempotent_parity` — identical outcome retries succeed; differing actions raise `ValueError`.
2. `test_write_outcome_not_found_parity` — nonexistent decisions raise `KeyError`.
3. `test_centroid_checkpoint_v2_parity` — V2 ID, action, vectors, shape, and factor hash round-trip consistently.
4. `test_load_latest_centroids_parity` — newest V2 checkpoint wins over the earlier legacy checkpoint.
5. `test_include_v2_false_parity` — legacy-only and combined checkpoint counts are consistent.
6. `test_conservation_write_read_parity` — conservation values and status round-trip consistently.
7. `test_count_verified_correct_parity` — verified and correct counts agree across stores.

The suite uses temporary SQLite and Memory stores. When `GRAPH_DSN` is available, each test creates and drops a unique `protocol_v2_test_parity_*` AGE graph. No `soc_graph` is used.

**Result:** `7 passed` across Memory, SQLite, and disposable AGE.

## LIVE CHECK RESULTS

After invoking the requested fresh launcher sequence:

| Copilot | Expected store | Live result |
|---|---|---|
| SOC | AGE | Learning health returned `learning_enabled=true`; history returned `200`, `total=0`; conservation route returned `404` in the running process |
| Trading | SQLite | Conservation returned `GREEN`, `V=255`, `correct=254`; history request timed out |
| Purchasing | SQLite | Conservation returned `GREEN`, `V=500`, `correct=455`; history request timed out |
| DataOps | SQLite | Conservation returned `GREEN`, `V=417`, `correct=310`; history request timed out |
| S2P | SQLite | Conservation returned `GREEN`, `V=191`, `correct=178`; history request timed out |

The launcher reported access-denied failures while stopping existing PIDs, so the live history timeouts cannot be treated as clean fresh-process evidence. Disposable AGE parity is the authoritative store gate result.

## VERDICT

**Store parity verified for the audited graph methods.** SQLite `write_outcome` is now idempotent like AGE, Memory is aligned, the legacy/V2 loader trap is removed across all stores, and the seven parity tests pass on all three implementations. No production graph was modified; all disposable AGE graphs were dropped.

The live endpoint surface still requires a clean process restart investigation because stale processes could not be terminated and several history requests timed out.
