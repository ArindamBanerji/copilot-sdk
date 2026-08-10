# Solution Design — Quality Axis and `SNAPSHOT_AFTER` v1

**Date:** 2026-08-06  
**Type:** Read + propose. No source, graph, or database modified.

## Executive recommendation

- **`SNAPSHOT_AFTER`: Option B — defer full lineage conformance to Program B, but retain the existing AGE writer.** Do not remove the edge from the model. Complete writer parity, traversal, and SQLite-to-AGE backfill when the shared AGE substrate is introduced.
- **Quality axis: Option A — add an immutable rolling-quality payload to each new checkpoint.** Use the already-available verified decision history to compute the last-window numerator/denominator at checkpoint time. Keep outcome-store recomputation as a read-time verification tool, not as the primary timeline contract.

This separates the two concerns: numerical scoring can proceed without lineage traversal, while every new quality-bearing checkpoint becomes self-describing once the schema change is implemented.

## Part A — `SNAPSHOT_AFTER`

### Evidence: value beyond the math

The math synopsis does not require this edge for the 17 numerical invariants. The JM authority does assign it product value:

- Episodic × Judgment: “which decision moved the centroid” and before/after inspection require `(Decision)-[:SNAPSHOT_AFTER]->(CentroidCheckpoint)` (`copilot-sdk/docs/judgment_memory_v2_7.md:104-108`).
- Procedural × Judgment uses the same edge to connect an evolution-triggering decision to the affected centroid (`:110-114`).
- The audit chain is intended to be traversable as Decision → Outcome → EvidenceReceipt → CentroidCheckpoint (`:208-216`).
- Cross-domain transfer is explicitly a graph operation, not API stitching (`:124-134`, `:208-210`).
- The JM model lists the edge in the canonical topology (`:355-359`).

The edge therefore supports provenance, auditability, “why did this centroid move?” explanations, and future evolution/transfer review. It is not needed to calculate `q`, IKS, centroid distance, or action probabilities.

### Current feasibility and cost evidence

AGE already emits the edge in its V2 write path (`ci-platform/ci_platform/graph/age_graph_store.py:1103-1125`, `:1421-1426`). However, the current migration writes `HAS_CENTROID_CHECKPOINT`, not `SNAPSHOT_AFTER` (`copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:622-640`), and the prior scan found no reader traversal.

SQLite has decision/entity edge tables (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:572-595`), but no generic checkpoint relationship or `SNAPSHOT_AFTER` table. Its checkpoint table is flat (`:441-458`), and `write_centroid_checkpoint` inserts only checkpoint columns (`:1556-1640`). Implementing SQLite parity therefore requires a new relation/table or a separate checkpoint-link table, not only a query change.

### Option A — Keep `SNAPSHOT_AFTER` in P2

**Effort:** Medium/high. AGE emission exists, but P2 would need:

1. verify/complete the AGE writer for every checkpoint-producing path;
2. add a reader traversal and endpoint/query contract;
3. add a SQLite equivalent because four copilots currently use SQLite;
4. update migration/backfill to preserve the relation;
5. add adapter/conformance tests across AGE, SQLite, and InMemory.

**Feasibility:** The scorer has the triggering decision ID at checkpoint creation (`copilot-sdk/copilot_sdk/scoring/scorer.py:1767-1782`), and the V2 payload contains a generated checkpoint ID (`:1826-1839`), so the two endpoints of the relation are available.

**Risk:** High scope coupling. The SQLite store is flat for checkpoints, and the migration currently rejects checkpoints without an identifier (`sqlite_to_age.py:623-626`) and does not emit the edge (`:637-640`). P2 would mix product lineage, adapter parity, and migration concerns before the shared AGE cutover.

**Enables:** Immediate before/after centroid explanations, provenance queries, evolution audit, and JM conformance tests on all stores.

### Option B — Defer full implementation to Program B (recommended)

**Effort:** Low now; medium later. Keep the existing AGE writer and canonical edge in the schema, but defer reader traversal, SQLite parity, migration backfill, and cross-adapter conformance until Program B makes AGE the shared substrate.

**Feasibility:** The AGE writer already creates the edge (`age_graph_store.py:1103-1125`, `:1421-1426`). The scorer already has both `decision_id` and checkpoint identity at `_save_centroids_checkpoint` (`scorer.py:1767-1839`). Program B already owns SQLite-to-AGE migration and batch verification (`sqlite_to_age.py:950-1056`, `:1131-1180`), so it is the correct place to add lineage backfill.

**Risk:** Until Program B completes, the edge is not a usable product surface. Existing AGE rows may be partially useful, while SQLite histories have no equivalent. The implementation must not claim “decision-to-centroid lineage” in P2 UI or audit output.

**Enables:** P2 scoring and quality work without blocking on graph topology; later one-substrate traversal, cross-copilot provenance, and migration validation. It also avoids building a temporary SQLite relation that would immediately become migration input.

**Required guard:** Preserve the edge in AGE writes and preserve the canonical schema name. Add a P2 test that confirms the writer emits it where the AGE adapter is active, but defer read API and full parity.

### Option C — Remove from scope

**Effort:** Lowest short-term effort, because no new work is done beyond possibly removing existing writes.

**Risk:** High architectural risk. It contradicts the JM interaction contract (`judgment_memory_v2_7.md:104-114`) and removes the ability to answer which decision caused a centroid change. A flat checkpoint list can show state history, but cannot prove causal lineage when decisions and checkpoints interleave.

**Consequences:** Before/after explanations, evolution causality, audit-chain traversal, and future provenance claims become unavailable or require heuristic joins. This is not recommended.

### Part A recommendation

**Choose Option B.** Retain `SNAPSHOT_AFTER` as a canonical AGE write contract, but defer complete read/parity/backfill work to Program B. Option A is technically feasible but disproportionate while four copilots remain on isolated SQLite stores; Option C conflicts with the JM authority.

## Part B — Quality axis

### Evidence: where quality data exists today

The underlying data needed for accuracy already exists in decisions/outcomes:

- SQLite decisions include `correct`, `status`, and verification timestamps (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:407-428`).
- SQLite outcomes include `is_correct` and `verified_at` (`:431-439`).
- The shared scorer counts verified and correct decisions through `_conservation_stats` (`copilot-sdk/copilot_sdk/scoring/scorer.py:2125-2141`).
- The scorer computes a rolling quality value by taking the most recent `window` verified decisions and counting correct outcomes (`scorer.py:2108-2122`).
- A 400-sample slice is already used for dispersion diagnostics (`scorer.py:2044-2049`), while the active conservation recent-window default is configurable and currently defaults to 100 (`scorer.py:1642-1643`). This is not automatically the math synopsis’ required 400-decision `q` window.

The conservation snapshot path already computes and persists `correct_count`:

- `_persist_conservation_snapshot` derives `V`, `q`, and related values (`scorer.py:872-923`);
- it writes `verified_count` and `correct_count` through `write_conservation_status` (`:924-935`);
- `_capture_conservation_state` computes `q = correct / verified` (`:1155-1177`).

The gap is specifically the centroid checkpoint payload. `_save_centroids_checkpoint` currently writes `decisions_count`, `verified_count`, `iks`, shape, factor hash, and metadata, but no correct count or quality-window identity (`scorer.py:1767-1839`). The SQLite checkpoint table has the same omission (`sqlite_store.py:441-458`), and `write_centroid_checkpoint` accepts no quality fields (`:1556-1569`).

The DI perturbation system is not a quality source. It creates a reversible in-memory factor overlay and before/after factor/overall values (`copilot-sdk/copilot_sdk/di/perturbation.py:39-110`, `:128-176`); it does not record verified outcomes or a rolling correctness window.

### Option A — Add quality fields to checkpoints (recommended)

**Proposal:** Add an immutable quality snapshot to each V2 checkpoint:

```text
quality_window_size       integer       # normally 400 for the math contract
quality_verified_count    integer       # N_v in that window
quality_correct_count     integer       # correct verified decisions in window
rolling_accuracy          real          # correct / verified, null if N_v = 0
quality_window_end        timestamp/id  # upper-bound decision or verification point
quality_policy_version    text          # e.g. quality.v1
```

Use the verified decision sequence at write time, not `verified_count / decisions_count`. The scorer already has the needed computation pattern (`scorer.py:2108-2122`) and the checkpoint writer already receives the decision ID and current decision context (`:1767-1782`).

**Feasibility:** High. The current `GraphStore` protocol already supports adding optional checkpoint arguments without changing scoring semantics; the existing write path is centralized in `_save_centroids_checkpoint` (`scorer.py:1767-1839`). SQLite schema creation/migration is centralized in `_create_tables`/`_ensure_migrations` (`sqlite_store.py:390-396`), and the AGE adapter already serializes checkpoint properties in one V2 write path. Conservation status proves the adapters can persist `correct_count` (`scorer.py:924-935`).

**Effort:** Medium, approximately 1–2 engineering days for protocol/model signatures, SQLite migration, AGE/Memory/dual-write parity, writer wiring, and tests. The estimate is higher than a single schema edit because all adapters must accept the same contract.

**Risks:**

- A checkpoint may be written before the outcome for the current decision is known; the window must therefore be explicitly “as of last verified outcome,” not implicitly “as of checkpoint decision.”
- `quality_window_size` must be fixed/versioned; the current configurable recent window (`scorer.py:1642-1643`) must not silently produce a non-400 value for the math contract.
- Existing checkpoints need `NULL`/unknown quality fields rather than fabricated zero accuracy.
- Checkpoint identity and factor hash must remain immutable together with the quality snapshot.

**Enables:** Fast timeline rendering, checkpoint-level quality/drift correlation, offline audit without replaying all outcomes, and a stable cross-adapter response shape.

### Option B — Compute rolling accuracy on read

**Proposal:** Leave the checkpoint schema unchanged. When `/api/self/centroid-history` reads checkpoints, compute each checkpoint’s quality by joining its domain and time/decision boundary to verified outcomes.

**Feasibility:** High for SQLite. Outcomes are keyed by `decision_id` and carry `is_correct`/`verified_at` (`sqlite_store.py:431-439`); decisions carry creation and verification data (`:407-428`); and the store already exposes verified-decision counting/query behavior through the scorer (`scorer.py:2125-2141`).

**Effort:** Medium, approximately 2 days for a bounded/batched query, response enrichment, indexes, and tests. AGE parity would require a corresponding query over Outcome/Decision nodes after Program B.

**Performance risk:** Potentially high for long histories. Computing a 400-row window per checkpoint is O(checkpoints × window) unless the endpoint uses one ordered outcome scan and a rolling prefix/deque. The prior DataOps history depth of 219 is already relevant to timeout risk; an unbounded per-checkpoint query would worsen it.

**Data risk:** Historical quality becomes dependent on current outcome retention, archive policy, and ordering semantics. It is not self-describing and can change if old outcomes are migrated or filtered.

**Enables:** No schema migration and immediate compatibility with existing checkpoint rows. It is useful as a verification/read model, but less suitable as the canonical persisted checkpoint contract.

### Option C — Defer quality until Program B

**Cost:** Zero immediate implementation cost.

**Feasibility:** Program B is intended to place decisions, outcomes, checkpoints, and evidence in one AGE graph (`copilot-sdk/docs/implementation_plans/shared_judgment_memory_graph_plan.md:231-263`).

**Risk/blocker:** The quality axis remains unavailable or approximate in all current SQLite-backed copilots. The JM authority explicitly treats conservation as a graph aggregate and persisted snapshot (`judgment_memory_v2_7.md:208-216`), so deferral delays a core judgment-memory surface rather than only a visualization.

**Enables:** A single canonical cross-domain quality query after migration, if the migration preserves outcomes and verification ordering.

### Part B recommendation

**Choose Option A for new checkpoints, with Option B as a read-time audit fallback.** The necessary correct-count data is already available at the scorer/conservation layer, and the checkpoint writer is centralized. Persisting the exact window definition avoids recomputing history, makes the timeline deterministic, and avoids an O(checkpoints × window) endpoint. Do not backfill unknown historical values with defaults. For old checkpoints, return `quality: null` or enrich them through Option B until migration/reconciliation is complete.

## Specific code changes for the recommended design

These are proposed changes only; no files were edited.

### 1. Define the checkpoint quality contract

Update the shared checkpoint protocol/model next to the existing checkpoint fields:

- `copilot-sdk/copilot_sdk/graph/protocol.py` checkpoint write contract (the current writer is implemented by the SQLite signature at `:1556-1569`).
- `copilot-sdk/copilot_sdk/backend/models.py` checkpoint/history response models, if the endpoint exposes typed models.
- Preserve the existing `factor_names_hash` and shape fields from `scorer.py:1822-1837`; add `quality_policy_version` beside them.

### 2. Compute the correct window centrally

Add a helper adjacent to `_recent_quality` (`scorer.py:2108-2122`) that returns:

```python
quality_window_size, quality_verified_count, quality_correct_count,
rolling_accuracy, quality_window_end
```

The helper must use the canonical last-400 verified, non-benchmark decisions and return `None`/unknown when no verified observations exist. The existing `_conservation_verified_decisions` filtering (`scorer.py:2013-2018`) is the correct source boundary.

### 3. Add fields to `_save_centroids_checkpoint`

At `scorer.py:1767-1839`, compute the helper result before building `checkpoint_payload` and pass the fields to `write_centroid_checkpoint`. Do not infer accuracy from `verified_count / decisions_count`; `decisions_count` currently means checkpoint batch count (`:1832`) and is not the quality denominator.

### 4. Implement adapter parity

- SQLite: add nullable columns and an `_ensure_migrations` migration adjacent to table creation (`sqlite_store.py:390-396`, schema `:441-458`); extend `write_centroid_checkpoint` (`:1556-1640`).
- AGE: serialize the same named properties in the existing V2 checkpoint writer (`ci-platform/ci_platform/graph/age_graph_store.py:1103-1125`, `:1421-1426`).
- InMemory and DualWrite: accept and return the same optional fields through their checkpoint methods; these adapters are part of the shared protocol surface.
- Migration: copy the fields when present in `sqlite_to_age.py:622-633`; preserve `NULL` for historical rows.

### 5. Response and fallback behavior

The history endpoint should expose a nested, explicit object rather than ambiguous top-level counts:

```json
{
  "quality": {
    "window_size": 400,
    "verified_count": 37,
    "correct_count": 35,
    "rolling_accuracy": 0.945946,
    "window_end": "...",
    "policy_version": "quality.v1",
    "source": "checkpoint"
  }
}
```

For legacy checkpoints, use `source: "unavailable"` and `rolling_accuracy: null`; never use `0.0` as a silent default. Option B read enrichment may populate `source: "outcome_recompute"` when explicitly requested.

### 6. Tests

Add cross-adapter tests covering:

1. exact 400-window numerator/denominator and accuracy;
2. fewer-than-400 verified decisions;
3. zero verified decisions returns null, not zero;
4. benchmark decisions excluded consistently with `_conservation_verified_decisions`;
5. checkpoint written before a new outcome does not claim that outcome;
6. SQLite/AGE/InMemory/DualWrite payload parity;
7. old checkpoint rows with null quality remain null;
8. migration copies quality fields without manufacturing them;
9. factor-name hash and quality policy version are returned together;
10. endpoint performance uses one bounded history read rather than one query per checkpoint.

### 7. `SNAPSHOT_AFTER` tests deferred to Program B

P2 should only retain an AGE writer assertion using the existing writer locations. Program B should add:

- Decision → checkpoint edge creation during SQLite-to-AGE backfill;
- traversal query proving the triggering decision and resulting checkpoint match;
- no duplicate edges on resume/re-run;
- cross-domain filtering and provenance tests;
- parity tests for AGE and any remaining local adapter.

The migration’s existing resumable batch boundary (`sqlite_to_age.py:1131-1180`) is the appropriate transaction point for those assertions.

## Final decision matrix

| Concern | Recommended option | Why |
|---|---|---|
| `SNAPSHOT_AFTER` | B — defer full implementation to Program B | JM value is real, but current SQLite has no equivalent and the math does not need traversal. Preserve the AGE writer contract. |
| Rolling quality | A — persist quality payload on new checkpoints | Correct/outcome data already exists; centralized writer can produce deterministic, self-describing history without expensive per-checkpoint reads. |
| Legacy quality | B-style read enrichment or `null` | Avoid fabricated values; distinguish persisted quality from recomputed quality. |
| Cross-domain quality | Program B after AGE migration | Current stores are isolated; shared graph is required for a canonical cross-domain aggregate. |

## Cleanup

No source, test, graph, or database files were modified. No scratch scripts were created.
