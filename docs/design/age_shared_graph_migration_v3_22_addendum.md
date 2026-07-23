# AGE Shared Graph Migration - v3.22 Design Addendum

**Version:** v3.22  
**Date:** 2026-07-23  
**Authority:** o1 retention-parity and AGE-archival review  
**Status:** Proposed implementation contract; implementation work must follow this addendum after approval.  
**Supersedes:** v3.20 section 3.5 only for active-only read-diff semantics; v3.20 section 7.5 only for the flip gate; v3.21 section 7.1 only where its `compare_all()` gate is replaced below. All other v3.20 and v3.21 decisions remain in force.

This addendum closes the retention-parity gap introduced by the scorer's automatic active-window cap. It is intentionally limited to retention, archive history, read parity, reconciliation, and flip sequencing.

## 3.5 Retention Contract

### 3.5.1 Normative semantics

1. Retention is **per domain** and applies to the active Decision population only.
2. The active window is the most recent `keep_recent` Decisions, ordered by `(created_at DESC, decision_id DESC)`. All older Decisions are archived. SQLite is the reference implementation: it normalizes `keep_recent` to a non-negative integer, obtains this exact ordering, and selects rows after the retained prefix for archival at `copilot_sdk/graph/sqlite_store.py:2807-2820`.
3. The scorer invokes retention after every successful `learn()` call at `copilot_sdk/scoring/scorer.py:636`, and archives only when `count_decisions(domain) > keep_recent` at `copilot_sdk/scoring/scorer.py:1014-1028`.
4. The effective default is 800. `archive_old_decisions(domain, keep_recent=800)` exposes a caller argument in the GraphStore protocol at `copilot_sdk/graph/protocol.py:86-87`, but `_maybe_archive()` is called without an override, so no environment, preset, or per-domain configuration currently changes the production scorer value at `copilot_sdk/scoring/scorer.py:1014-1023`.
5. **Active** means a Decision returned by `get_all_decisions(domain)` and counted by active count/V methods. SQLite active reads come only from `decisions` at `copilot_sdk/graph/sqlite_store.py:1872-1881`. AGE active reads exclude `d.archived = true` at `ci-platform/ci_platform/graph/age_graph_store.py:2029-2040`.
6. **Archived** means retention has completed and the Decision is no longer in the active population. SQLite physically copies Decision plus Outcome values into `decisions_archive`, deletes active Outcome and entity-edge rows, then deletes the active Decision at `copilot_sdk/graph/sqlite_store.py:2825-2857`. AGE shall use property-based archival: retain the Decision node, Outcome node, and all relationships, but mark the Decision as archived. AGE must never physically delete an archived Decision as part of this contract.

### 3.5.2 D2 interaction

D2 already defines V as an active-only population: its predicate excludes `archived = true` in v3.20 section 3.1.1, `docs/design/age_shared_graph_migration_v3_20.md:134-145`. AGE's `count_verified`, `count_verified_decisions`, `count_correct`, and `get_verified_decisions` already implement that active exclusion at `ci-platform/ci_platform/graph/age_graph_store.py:1573-1641`.

New work is not a D2 rewrite. It makes `archive_old_decisions()` set the same archival property that D2 already excludes, and adds a separate archive-history read path. Archived Decisions must not contribute to active V, active correctness, active totals, or active read-diff.

## 3.6 AGE Archival Implementation

### 3.6.1 Required signature and return contract

Implement in `AGEGraphStore` and forward unchanged through `AGEGraphStoreAdapter`:

```python
def archive_old_decisions(self, domain: str, keep_recent: int = 800) -> int:
    """Archive all but the newest active Decisions for one domain."""
```

The return value is the number of Decisions newly transitioned from active to archived. Return `0` when the active count is at most `keep_recent`, or when a retry finds all candidates already archived. This must match SQLite's integer return contract at `copilot_sdk/graph/sqlite_store.py:2807-2857` and the existing adapter forwarding shape at `ci-platform/ci_platform/graph/age_sdk_adapter.py:442-446`.

### 3.6.2 Property-based archival model

For every selected AGE Decision, set exactly:

```text
archived: true
archived_at: <UTC epoch seconds as float>
archive_reason: "retention_window"
archive_status: "archived"
archived_from_status: <the Decision status before the SET>
```

This property set follows the existing single-purpose `archive_decisions()` behavior at `ci-platform/ci_platform/graph/age_graph_store.py:2319-2332`, except that retention uses `archive_reason = "retention_window"` to mirror SQLite's archive-table default at `copilot_sdk/graph/sqlite_store.py:664-665`.

Do not modify `status`, Outcome properties, `HAS_OUTCOME`, `DECIDED_ON`, or any other relationship. SQLite's active table deletion removes Outcome and entity-edge rows after copying denormalized outcome data at `copilot_sdk/graph/sqlite_store.py:2831-2853`; AGE must preserve those graph records so history can read the same Decision/Outcome facts without reconstructing edges.

### 3.6.3 Required algorithm

1. Normalize `domain = str(domain)` and `keep_recent = max(int(keep_recent), 0)`.
2. Query all active Decision IDs for the domain, ordered `created_at DESC, decision_id DESC`. The `WHERE` clause must include `(d.archived IS NULL OR d.archived = false)`.
3. In Python, retain the first `keep_recent` IDs and make all remaining IDs archive candidates. AGE cannot rely on `SKIP`; v3.20 records the AGE no-`$params` constraint at `docs/design/age_shared_graph_migration_v3_20.md:182-184`. Do not introduce `SKIP`, `$params`, `MERGE`, or `CASE WHEN` into AGE Cypher.
4. De-duplicate candidate IDs, sort them for deterministic execution, and split them into batches of at most 100 IDs.
5. For each batch, emit a literal list built with the store's existing escaping helper, as the existing AGE archival method does at `ci-platform/ci_platform/graph/age_graph_store.py:2315-2328`. Issue one `MATCH ... WHERE ... d.decision_id IN [...] SET ... RETURN count(d)` query.
6. Repeat the active predicate in the update query. That predicate supplies idempotency and makes concurrent/replayed candidates no-ops.
7. Sum returned counts and return that sum. A failure must raise; do not report a successful archive count for a partially failed batch.

Required Cypher shape per batch:

```cypher
MATCH (d:Decision)
WHERE <domain_scope>
  AND (d.archived IS NULL OR d.archived = false)
  AND d.decision_id IN [<escaped literal ids>]
SET d.archived = true,
    d.archived_at = <epoch float>,
    d.archive_reason = 'retention_window',
    d.archive_status = 'archived',
    d.archived_from_status = d.status
RETURN count(d) AS cnt
```

Use the existing `_domain_clause(domain)` form for domain scope, as `get_all_decisions()` does at `ci-platform/ci_platform/graph/age_graph_store.py:2029-2038`; do not reduce SOC's existing compatibility scope to a simple equality predicate.

### 3.6.4 Existing explicit archival is not retention archival

`archive_decisions(domain, before, status_filter, confirm_verified)` is a separate Protocol V2 operation. It validates statuses, requires explicit confirmation before verified archival, filters active nodes, and sets `protocol_v2_archive:<status>` reasons at `ci-platform/ci_platform/graph/age_graph_store.py:2277-2332`. Do not route retention through this method: retention is count/window based and may archive any status selected by the window. Both methods share the same archival properties and active exclusion.

## 3.7 Archive History Protocol Extension

### 3.7.1 New GraphStore method

Add this method immediately after `get_all_decisions` in `GraphStore`, then implement it in SQLite, InMemory, AGE, the AGE adapter, and DualWriteStore:

```python
def get_archived_decisions(self, domain: str) -> list[dict[str, Any]]:
    """Return every archived Decision for one domain in archive order."""
```

Return records sorted by `(created_at ASC, decision_id ASC)`. Every record must expose this normalized field set when the stored value exists:

```text
decision_id, domain, category, category_index,
recommended_action, recommended_index, confidence,
factor_vector, probabilities, created_at,
actual_action, actual_index, is_correct, verified_at,
archived_at, archive_reason
```

### 3.7.2 Store-specific implementation

- **SQLite:** select `decisions_archive`, decode JSON columns, and return the normalized fields above. The archive schema contains Decision fields, flattened Outcome fields, `archived_at`, and `archive_reason` at `copilot_sdk/graph/sqlite_store.py:646-666`. It has no active `status`, metadata JSON, entity edges, or separate Outcome row after archival; those are not part of archive parity.
- **AGE:** match `Decision` nodes with the domain scope and `d.archived = true`; optional-match `HAS_OUTCOME` and merge Decision/Outcome properties using the same result normalization style as active verified reads, which already optional-matches Outcome at `ci-platform/ci_platform/graph/age_graph_store.py:1573-1591`. Return the five archive properties from the Decision. Do not delete or synthesize outcomes.
- **InMemory:** flatten each `_archive` entry's stored `decision` and `outcome`, then add the entry's `archived_at` and `archive_reason`. Its retention archive already saves deep copies of both before deleting active maps at `copilot_sdk/graph/memory_store.py:1355-1383`.
- **DualWriteStore:** `get_archived_decisions` is primary-only, consistent with all other reads at `copilot_sdk/graph/dual_write_store.py:350-364`. ReadDiffRunner receives the two concrete stores directly for parity; DualWriteStore must not make the secondary visible to normal callers.
- **AGE adapter:** add a direct forwarding method next to `get_all_decisions`, matching its existing forwarding pattern at `ci-platform/ci_platform/graph/age_sdk_adapter.py:384-396,442-446`.

### 3.7.3 Comparable and excluded fields

History L2 compares the normalized field set listed in section 3.7.1. Exclude `archive_id`, raw JSON column strings, node IDs, metadata, `context_json`, active `status`, `archive_status`, `archived_from_status`, graph relationships, and storage-specific timestamps. SQLite removes edges while AGE preserves them, so edge equality is explicitly not a history gate.

## 3.8 Read-Diff Parity Modes

Replace the active-only interpretation of `compare_all()` with two explicit modes. Current `compare_all()` compares active count/V/correct/total and active maps, `copilot_sdk/graph/read_diff_runner.py:123-223`; current `compare_sample()` uses the same active comparison with a sampled map, `copilot_sdk/graph/read_diff_runner.py:128-166`.

### 3.8.1 `compare_active(domain)`

Inputs:

- `count_verified`, `count_correct`, `count_decisions` from both stores.
- `get_all_decisions(domain)` and `get_verified_decisions(domain)` from both stores.

L1 checks are exact equality of verified, correct, and active-total counts. L2 compares the existing active fields:

```text
decision_id, domain, category, category_index, recommended_action,
recommended_index, confidence, factor_vector, probabilities, status,
actual_action, actual_index, is_correct
```

Use compound `(domain, decision_id)` identity and the existing JSON/float normalization behavior at `copilot_sdk/graph/read_diff_runner.py:66-105,226-240`. Pass only when every L1 count matches, both ID sets match, and L2 has zero mismatches. `compare_all()` becomes a backward-compatible alias for `compare_active()`; `compare_sample()` becomes `compare_active_sample()` behavior and must not report a pass if its L1 active counts differ.

### 3.8.2 `compare_history(domain)`

Inputs are `get_archived_decisions(domain)` from both stores. It must not call active V/count methods because archived records are intentionally excluded by D2.

L1 checks: exact archive-record count and exact compound ID-set equality. L2 compares only:

```text
decision_id, domain, category, category_index, recommended_action,
recommended_index, confidence, factor_vector, probabilities, created_at,
actual_action, actual_index, is_correct, verified_at,
archived_at, archive_reason
```

Use the same normalizer and 1e-6 numeric tolerance as active diff. `archived_at` is compared only if both stores archived the same operation in the same implementation call; for baseline reconciliation it is excluded from the gate because AGE is marked after pre-existing SQLite archival. Encode that as `compare_history(domain, compare_archived_at: bool = False)` with default `False`; all other history L2 fields remain mandatory.

History passes only when L1 count and ID sets match and required L2 mismatches are zero. Active and history results must be separately visible. Extend `DiffReport` with `mode: str` (`"active"` or `"history"`) and `primary_archive_count`/`secondary_archive_count` for history; retain existing fields for active compatibility. The current report has only active count fields at `copilot_sdk/graph/read_diff_runner.py:35-63`.

## 3.9 Baseline Reconciliation

### 3.9.1 Problem

The migration baseline placed verified Decisions in AGE, while SQLite's post-learn retention may subsequently move some of those IDs into `decisions_archive`. SQLite active reads then omit them, but AGE still presents unmarked nodes as active. AGE's active reads and D2 exclude only nodes already marked archived at `ci-platform/ci_platform/graph/age_graph_store.py:1573-1655,2029-2040`.

### 3.9.2 Required reconciliation script

Implement a one-shot, resumable operator script after AGE retention exists:

1. Read all SQLite archived records through `get_archived_decisions(domain)`; use only their `decision_id` values as the authoritative reconciliation set.
2. Query AGE for those IDs in batches of 100, scoped to the domain and `(archived IS NULL OR archived = false)`.
3. Set the same AGE archive properties as section 3.6, with `archive_reason = "sqlite_baseline_reconciliation"`. Preserve existing Outcome nodes and relationships.
4. Record a JSON checkpoint after each successful batch: domain, sorted source IDs, processed IDs, AGE newly-marked count, started/finished timestamps, and source SQLite archive count.
5. Re-run safely: the active predicate makes already marked IDs no-ops. Fail on a source/AGE ID mismatch report; do not silently treat unmatched IDs as success.
6. Run `compare_active(domain)` and `compare_history(domain, compare_archived_at=False)` immediately after reconciliation. Do not proceed to flip unless both pass.

Run reconciliation after section 3.6 is implemented and tested, after the historical migration/backfill is complete, and before dual-write parity cycles and flip gates.

## 7.2 Revised Phase 3 Flip Sequence

1. Implement and test protocol/archive-history changes in section 8 steps 1-4.
2. Enable dual write with the v3.21 environment:

```text
GRAPH_BACKEND=dual_write
GRAPH_DSN=host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres
GRAPH_NAME=soc_graph
SHARED_GRAPH_AUTHORIZED=trading:soc_graph
SCORER_GOVERNED_WRITES=1
```

These are the existing v3.21 dual-write values, `docs/design/age_shared_graph_migration_v3_21_addendum.md:132-139`.

3. Execute baseline reconciliation for the target domain and retain its checkpoint/report.
4. Run `compare_active(domain)` plus `compare_history(domain, compare_archived_at=False)` on every cycle. For Trading, run both full modes. For S2P-scale domains, active sampling may run between full cycles, but a full active and full history comparison is mandatory before flip.
5. Require 40 consecutive zero-discrepancy cycles for both modes. Any active/history discrepancy or any secondary AGE write failure resets the counter. This extends v3.20's 40-cycle/outbox rule, `docs/design/age_shared_graph_migration_v3_20.md:809-822`.
6. Verify the durable dual-write outbox is empty. v3.20 makes an empty outbox a pre-flip requirement at `docs/design/age_shared_graph_migration_v3_20.md:717-722`.
7. Flip active reads only after steps 3-6 pass, using the existing v3.21 values:

```text
TRADING_ACTIVE_GRAPH_BACKEND=age
TRADING_ACTIVE_AGE_DSN=host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres
TRADING_ACTIVE_AGE_GRAPH=soc_graph
TRADING_ACTIVE_AGE_DOMAIN=trading
TRADING_SHARED_GRAPH_AUTHORIZED=trading:soc_graph
TRADING_ACTIVE_AGE_TEST_MODE=0
TRADING_SHADOW_AGE=0
SCORER_GOVERNED_WRITES=1
```

These values are defined in v3.21 at `docs/design/age_shared_graph_migration_v3_21_addendum.md:141-150`.

Go/no-go checklist: protocol conformance passes; retention parity tests pass; reconciliation report has no unresolved IDs; active and history full diffs pass; 40-cycle counter is intact; durable outbox is empty; authorization variables match the target `(domain, graph)` pair; rollback environment remains available.

## 8 Implementation Order

1. **Protocol and normalized archive reader contract.** Repo: `copilot-sdk`. Add `get_archived_decisions` to `GraphStore`; implement SQLite and InMemory readers. Scope: small. Tests: SQLite retention ordering, archive field normalization, InMemory parity.
2. **AGE archive retention and reader.** Repo: `ci-platform`. Replace the no-op at `age_graph_store.py:2262-2264`; add history reader; preserve Outcomes/edges. Scope: medium. Tests: 0/1/800/801/900 active Decisions; tie-break ordering; batch >100; idempotent retry; D2 and active reads exclude archived; history retains outcome fields.
3. **Adapter and dual-write forwarding.** Repos: `ci-platform`, `copilot-sdk`. Forward history reads in AGE adapter; make DualWrite archive history primary-only. Scope: small. Tests: signature conformance and forwarding.
4. **Read-diff split.** Repo: `copilot-sdk`. Add `compare_active`, `compare_history`, compatibility aliases, and mode-aware reports. Scope: medium. Tests: active-only mismatch, archive-only mismatch, field exclusions, archived-at reconciliation mode, sample behavior.
5. **Baseline reconciliation tool.** Repo: `copilot-sdk` plus AGE access boundary selected by the migration tooling. Scope: medium. Tests: 206-style preexisting archive IDs, resume checkpoint, no-op rerun, unresolved ID failure, active/history diff pass after reconciliation.
6. **Dual-write/flip gate integration.** Repos: deployment configuration and migration runner. Scope: small. Tests: gate rejects non-empty outbox, nonzero diff, unresolved reconciliation, and fewer than 40 zero-diff cycles.

Do not combine these steps with unrelated scorer behavior, D2 predicates, physical AGE deletion, or active response changes.

## 9 Open Questions / Decisions

1. **Keep-recent configuration:** keep 800 globally fixed for this implementation. Decide later whether configuration belongs per domain or per preset; do not add an environment variable in this work because the scorer currently has no such configuration source at `copilot_sdk/scoring/scorer.py:1014-1023`.
2. **Physical AGE pruning:** do not prune archived AGE Decisions in this migration. Revisit only with a retention/legal policy, successful archive-history parity, an Outcome/edge preservation plan, and a separate backup/restore design.
3. **Flip gate:** require both `compare_active` and `compare_history`. Active-only parity can pass while retention has left divergent archived populations, which defeats the stated retention-parity objective.

*v3.22 Addendum - 2026-07-23*
