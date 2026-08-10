# Solution Design — Program B Migration Gaps v1

**Date:** 2026-08-06  
**Type:** Read + propose. No source, graph, or database modified.

## Important correction to the gap statement

The migration does not reject every row whose `checkpoint_id` is null. It first falls back to the SQLite autoincrement `id`:

```python
checkpoint_id = checkpoint_properties.get("checkpoint_id") or checkpoint_properties.get("id")
if checkpoint_id is None:
    raise ValueError(...)
```

(`copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:622-626`). The real defect is that the generated fallback is not written back into `checkpoint_properties["checkpoint_id"]`. The AGE node can therefore retain `checkpoint_id: null`, while the following edge query searches for the generated ID (`:627-640`). In addition, the normal legacy loader intentionally selects `checkpoint_id IS NULL` (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:2626-2637`). Migration must define which legacy/V2 loader semantics remain authoritative.

The local read-only database scan found:

| Store | Rows | Null `checkpoint_id` | Sample identity fields |
|---|---:|---:|---|
| Trading | 5 | 5 | `id=1..3`, `domain=trading`, `created_at` populated |
| Purchasing | 5 | 5 | `id=1..3`, `domain=purchasing`, `created_at` populated |
| DataOps | 219 | 219 | `id=1..3`, `domain=dataops`, `created_at` populated |

The rows also contain `centroids_json`, and the schema contains domain/category/action, timing, metadata, and shape fields (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:441-458`). Therefore deterministic source-row identity is available even though the logical checkpoint ID is absent.

## GAP 1 — Null-id checkpoint preservation

### Evidence

The source schema has a stable autoincrement primary key and a nullable unique logical ID (`sqlite_store.py:441-455`). The migration groups checkpoints by `decision_id` (`sqlite_to_age.py:174-193`) and then uses the fallback described above (`:622-640`).

Two separate preservation issues must be solved:

1. **Identity/edge issue:** fallback `id` is used for lookup but not assigned to the serialized property before `CREATE`.
2. **Loader semantics:** converting legacy null IDs to non-null IDs makes them invisible to `load_latest_centroids`, whose SQL explicitly filters `checkpoint_id IS NULL` (`sqlite_store.py:2626-2637`).

The migration also only carries checkpoint rows attached to a decision group (`sqlite_to_age.py:134-140`, `:191-193`). That matters for warm-start rows and is addressed under GAP 3.

### Option A — Pre-migration ID generation

**Design:** Update each null source row before migration to a deterministic ID such as `legacy_{domain}_{id}`.

**Effort:** Low, approximately 0.5–1 day.

**Feasibility:** `id` is a stable primary key (`sqlite_store.py:442`), and the migration already serializes arbitrary checkpoint properties (`sqlite_to_age.py:627-633`).

**Risk:** It mutates the source database and changes legacy loader behavior because the loader only returns null-ID rows (`sqlite_store.py:2626-2637`). A source backup and a coordinated loader change would be mandatory. It also does not solve rows whose `decision_id` is null, because `_group_by_decision` drops those rows (`sqlite_to_age.py:134-140`).

**Code changes:** A source migration plus loader compatibility logic, and a separate path for unassociated checkpoints.

### Option B — Generate IDs inside the migration (recommended)

**Design:** Keep SQLite immutable. For every checkpoint row:

```python
source_id = checkpoint_properties.get("id")
logical_id = checkpoint_properties.get("checkpoint_id")
if not logical_id:
    if source_id is None:
        raise ValueError("checkpoint has neither logical nor source identity")
    logical_id = f"legacy_{domain}_{int(source_id)}"
checkpoint_properties["checkpoint_id"] = logical_id
checkpoint_properties["legacy_source_id"] = int(source_id)
checkpoint_properties["migration_identity"] = "sqlite_row"
```

Then create and match the AGE node using `logical_id`, not the original null value. This directly fixes the mismatch in `sqlite_to_age.py:622-640` and is safe because source rows already have `id` (`sqlite_store.py:442`).

**Effort:** Approximately 1 day, including a loader policy and tests.

**Risk:** If the startup loader remains `checkpoint_id IS NULL`, migrated legacy rows will no longer be startup candidates. The migration must therefore either:

- preserve a separate `legacy_checkpoint_id`/`legacy_source_id` while keeping `checkpoint_id` null for legacy rows; or
- make the AGE loader explicitly support both legacy and V2 rows, with deterministic ordering and a migration marker.

The second choice is cleaner for a canonical AGE graph, but it is a loader behavior change and must be validated against V2 precedence. No silent fallback to bootstrap is acceptable.

**Code changes:** Migration normalization, AGE node/edge write, loader precedence, and tests. No source SQLite mutation.

### Option C — Separate legacy batch

**Design:** Keep normal V2 rows on the existing path and process null-ID legacy rows through a dedicated writer that assigns `legacy_{domain}_{id}` and links them using the generated identity.

**Effort:** Approximately 1 day.

**Risk:** Duplicates identity rules and creates two migration semantics. The same loader problem remains: non-null generated IDs are invisible to the current null-only loader unless the loader is changed. It also requires a separate count/idempotency proof.

### GAP 1 recommendation

Choose **Option B**, with an explicit legacy identity policy:

1. Preserve source SQLite unchanged.
2. Generate `legacy_{domain}_{id}` inside the migration and write it to the AGE node.
3. Add `legacy_source_id` and `migration_source="sqlite_legacy"`.
4. Make the AGE startup reader order all valid V2 and legacy checkpoints by checkpoint time/created time, while preserving the existing bootstrap fallback only when no valid checkpoint exists.
5. Add a separate unassociated-checkpoint import path because `_group_by_decision` currently drops `decision_id=None` rows.
6. Make the migration idempotent on `(domain, migration_source, legacy_source_id)` and checkpoint ID.

## GAP 2 — Learned state replay

### Evidence

The migration module explicitly excludes learned L5, DK, and conservation state and says it will be re-derived from the ordered decision log (`copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1-5`).

The source SQLite store does contain the state needed for a direct snapshot:

- L5 centroids: `l5_centroids` with vector, delta, causal decision, and update time (`sqlite_store.py:461-471`);
- DK state: `l5_dk_weights` with current marker, weight tensor, decision count, and Welford fields (`:473-491`);
- conservation state: `l5_conservation_state` with status, `alpha`, `q`, `V`, threshold, product, category coverage, and causal decision (`:493-510`).

The source decision log also contains factor vectors, recommended actions, status, correctness, and timestamps (`sqlite_store.py:407-428`), and outcomes contain `is_correct` and `verified_at` (`:431-439`).

A replay implementation already exists for verification:

- `verify_state.replay_decisions` builds a fresh scorer (`copilot-sdk/copilot_sdk/migrate/verify_state.py:247-267`);
- orders decisions by `created_at` and ID (`:269-273`);
- adds each decision and calls `scorer.learn()` (`:273-282`);
- re-estimates DK and computes centroids, verified count, correctness, alpha, and phases (`:282-310`).

The ordinary scorer learn path requires an existing decision, action, factor vector, category, and recommendation (`copilot-sdk/copilot_sdk/scoring/scorer.py:582-617`). Thus replay is feasible for verified decisions with complete rows, but it is not a byte-for-byte restoration of every historical L5 node or checkpoint. It also recomputes using current code/preset semantics, so factor-version and preset-version compatibility must be checked.

### Option A — Full decision-log replay

**Design:** Migrate decisions/outcomes, initialize from bootstrap, replay verified decisions chronologically through `scorer.learn()`, then re-estimate DK and write conservation state.

**Effort:** Approximately 2–3 days for a production migration command, state comparison, and idempotent checkpointing. The core replay already exists (`verify_state.py:247-310`).

**Feasibility:** High when factor vectors and outcomes are complete. The existing Level 3 verifier already compares replay-derived centroids, DK, conservation, and decision counts (`verify_state.py:470-512`).

**Risk:** Floating-point/order drift; current scorer or factor code may differ from historical code; replaying only verified decisions cannot reproduce unverified state; replay writes may create new learning artifacts unless run against a disposable/inactive scorer.

**Result:** Reconstructs logical state, but not exact historical L5/checkpoint lineage.

### Option B — Snapshot plus partial replay (recommended)

**Design:** Migrate the latest source L5 centroid tensor, current DK weights/Welford state, and current conservation state directly. Then replay only decisions after a recorded snapshot boundary, or use replay solely as a verification comparison.

**Effort:** Approximately 1–2 days after the state-copy mappings are defined.

**Feasibility:** Strong. The source schemas carry all three state families (`sqlite_store.py:461-510`), and the AGE/SDK store interfaces already expose corresponding methods, including `get_centroids` (`sqlite_store.py:2322-2342`), `get_dk_weights` (`:2430`), and `get_conservation_state` (`:2558`). The migration already has a durable batch checkpoint mechanism (`sqlite_to_age.py:1131-1180`).

**Risk:** Cross-component consistency. The centroid, DK, and conservation rows must represent one coherent cutoff. Use a source transaction/read lock or a captured `snapshot_time` and record the same boundary in every migrated state object. If no coherent boundary exists, fall back to replay rather than mixing timestamps.

**Result:** Preserves operational behavior quickly and avoids losing accumulated judgment. Replay remains available to verify that the snapshot and decision log agree within tolerance.

### Option C — Accept bootstrap restart

**Design:** Migrate only decisions/outcomes/checkpoints and restart each scorer from bootstrap.

**Effort:** Zero additional migration implementation effort.

**Feasibility:** Technically works because startup already has a bootstrap path when no usable checkpoint is loaded. It is not safe for production learned state.

**Risk:** Loses L5 centroids, DK weights, conservation state, phase state, and accumulated judgment. The migration module itself documents this loss (`sqlite_to_age.py:1-5`). “Re-converges quickly” is not equivalent to preserving behavior and needs a domain-specific acceptance test.

### GAP 2 recommendation

Choose **Option B**, with Option A as the verification fallback:

1. Capture one consistent source-state boundary.
2. Copy latest L5, DK/Welford, and conservation rows with `migration_source` and boundary metadata.
3. Start AGE scorers from the copied state.
4. Replay the ordered verified log in a shadow scorer using `verify_state.replay_decisions`.
5. Compare centroids, DK, conservation, and decision counts using the existing comparison path (`verify_state.py:491-512`).
6. If the snapshot fails tolerance or lacks a coherent boundary, reject the direct copy and use full replay.

## GAP 3 — Warm-start metadata

### Evidence

Warm-start writes a legacy centroid checkpoint with metadata but no explicit `checkpoint_id` argument:

- category is `"warm_start"`;
- metadata includes a generated warm-start decision marker, source, score, applied count, and source copilots;
- the write uses `save_centroids` (`copilot-sdk/copilot_sdk/scoring/scorer.py:1514-1527`).

The SQLite implementation inserts `kwargs.get("decision_id")` into the separate `decision_id` column and writes the supplied metadata JSON (`copilot_sdk/graph/sqlite_store.py:2591-2624`). The transfer router reads at most ten checkpoint rows, reverses them, and selects metadata with `source == "warm_start"` or `source_copilots` (`copilot_sdk/backend/transfer_router.py:181-203`).

There is an additional migration gap beyond null IDs: `_group_by_decision` ignores rows with no `decision_id` (`sqlite_to_age.py:134-140`), and `_read_migration_records` only attaches grouped checkpoints to verified decisions (`:191-193`, `:227-234`). A warm-start row whose metadata has a marker but whose table `decision_id` is null can therefore be omitted before the null-ID check is reached.

The current local Trading/Purchasing/DataOps databases had no rows matching `category='warm_start'` or metadata containing `warm_start`, so the local sample does not prove historical warm-start rows are present. The writer and reader paths prove the contract exists.

### Option A — Preserve warm-start with GAP 1 (recommended)

**Design:** Treat unassociated warm-start checkpoints as first-class migration records. Generate a deterministic identity from `(domain, source row id)`; preserve `category="warm_start"`, all metadata JSON, source timestamp, and the marker in AGE. Do not require a Decision node or fabricate one.

**Effort:** Included in GAP 1 Option B, plus approximately 0.5 day for a second migration record class and transfer-router verification.

**Feasibility:** The metadata is already serialized by `save_centroids` (`sqlite_store.py:2591-2624`), and transfer only needs metadata plus checkpoint ordering (`transfer_router.py:181-203`).

**Risk:** If the migration keeps only decision-attached records, warm-start is silently lost. If the loader changes from null-only to V2 IDs, the transfer router must be tested against the new ordering and identity.

### Option B — Regenerate warm-start after migration

**Design:** Migrate base state, then run a fresh warm-start operation against AGE so a new metadata-bearing checkpoint is created.

**Effort:** Approximately 0.5 day.

**Feasibility:** The scorer has a working warm-start save path (`scorer.py:1514-1527`), and the transfer reader is already metadata-based (`transfer_router.py:181-203`).

**Risk:** It changes the historical transfer event, may produce a different score/source set, and does not preserve the original provenance. It should be a recovery fallback, not the primary migration method.

### GAP 3 recommendation

Choose **Option A**. Preserve historical warm-start metadata and identity during migration. Use Option B only when the source row is irreparably incomplete, and label regenerated metadata as `source="warm_start_regenerated"` so it cannot masquerade as the historical event.

## Combined migration sequence

### Phase 0 — Read-only preflight

1. Inventory decisions, outcomes, checkpoint rows, L5 centroids, DK rows, conservation state, and warm-start metadata per domain.
2. Verify all checkpoint rows have a source `id`; verify all decision-attached rows have valid decision IDs.
3. Capture factor schema/preset version and the ordered decision-log manifest. The decision ordering used by the existing replay verifier is `created_at`, then `decision_id` (`verify_state.py:269-273`).
4. Create a source backup and a migration manifest; do not update SQLite in place.

**Gate:** counts and manifests are stable; no missing required factor vectors/outcomes for the selected replay scope.

### Phase 1 — Build the disposable AGE target

1. Create the domain-scoped scratch graph.
2. Migrate decisions/outcomes and ordinary checkpoint rows in batches using the existing commit/resume boundary (`sqlite_to_age.py:1128-1180`).
3. Normalize null logical IDs to deterministic `legacy_{domain}_{id}` IDs, retaining `legacy_source_id` and migration source metadata.
4. Import unassociated warm-start checkpoints through a dedicated path rather than `_group_by_decision`.

**Gate:** migrated checkpoint count equals source count, including 5/5/219 legacy rows; every generated ID is unique and rerunning the batch writes zero duplicates; warm-start metadata is queryable.

### Phase 2 — Restore learned state

1. Copy the latest coherent L5 centroid, DK/Welford, and conservation rows with one snapshot boundary.
2. If state components do not share a coherent boundary, do not partially copy them; use full replay.
3. Run shadow replay using `verify_state.replay_decisions` (`verify_state.py:247-310`) and compare with the migrated state (`:491-512`).

**Gate:** centroid, DK, conservation, and decision counts pass explicit tolerances; no domain loads bootstrap unexpectedly; warm-start transfer status is preserved.

### Phase 3 — Lineage and cutover

1. Defer complete `SNAPSHOT_AFTER` backfill/traversal until the shared-AGE Program B phase, consistent with the separate solution design.
2. Before live cutover, validate loader precedence for generated legacy IDs versus V2 IDs. The current null-only loader (`sqlite_store.py:2626-2637`) cannot be left as an implicit policy.
3. Enable AGE for one domain, run shadow comparison, then proceed domain by domain.

## Verification gates

| Gate | Required assertion |
|---|---|
| Identity | Every source checkpoint maps to exactly one AGE checkpoint; generated legacy ID is deterministic. |
| Count | Trading 5, Purchasing 5, DataOps 219 legacy rows are present; no source row silently dropped. |
| Idempotency | Re-running the migration creates no duplicate checkpoint, L5, DK, conservation, or warm-start state. |
| Loader | Latest migrated state is loaded at startup; no silent bootstrap fallback. |
| Learned state | L5 vectors, DK weights/Welford state, conservation values, and phase/metadata match source or pass replay tolerance. |
| Warm-start | Transfer router returns the preserved historical metadata; regenerated events are clearly labeled. |
| Replay | Existing Level 3 comparison passes centroid, DK, conservation, and decision-count checks (`verify_state.py:503-512`). |
| Rollback readiness | Original SQLite remains untouched and the AGE target is disposable until all gates pass. |

## Rollback plan

1. Keep the original SQLite stores read-only and unchanged throughout migration.
2. Run all writes first against a disposable AGE graph, using the migration’s scratch-graph path (`sqlite_to_age.py:1107-1115`).
3. If any gate fails, drop the scratch graph and delete only the migration checkpoint/manifest for that attempt; do not modify source stores.
4. If a live AGE cutover has occurred, switch the domain back to its original SQLite store and discard the new domain graph after preserving diagnostic evidence.
5. Never fall back silently to bootstrap. Startup must report whether state came from migrated checkpoint, snapshot restore, replay, or bootstrap.

## Final recommendations

| Gap | Recommendation | Rationale |
|---|---|---|
| Null IDs | Migration-local deterministic IDs plus explicit loader policy | Avoids mutating SQLite, fixes the current node/edge identity mismatch, and preserves all 229 rows. |
| Learned state | Snapshot coherent L5/DK/conservation state, then shadow-replay for proof | Existing schemas contain the state and existing replay verification can validate it. |
| Warm-start | Preserve unassociated metadata-bearing rows as first-class records | Transfer depends on metadata, and decision grouping currently drops unassociated rows. |

## Cleanup

No source, test, graph, or database files were modified. No scratch scripts were created.
