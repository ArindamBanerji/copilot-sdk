# AGE Shared Graph Migration — Complete Design & Execution Plan

**Date:** July 20, 2026 · **Version:** v3.19
**Authority:** judgment_memory_v2_7.md
**History:** v1→v3.14 → protocol audit → v3.16 → final review → v3.17 → o1 code-verified edits → v3.18 → o1 sign-off review → v3.19
**Scope:** Current state to "every §2 claim demonstrated"

This document is the single source of truth for the AGE migration.
Implementation prompts reference sections by number. No design spec
lives outside this document.

---

# §1 VERIFIED FACTS

All verified by live AGE queries + SQLite audit, July 19-20, 2026.
File:line evidence recorded in investigation scripts under scripts/.

## §1.1 AGE graph state

- **SOC:** 6,253 Decisions. V_soc = 4,899 (3,749 correct + 1,150 incorrect).
  "incorrect" = overridden per JM §4.2. No status property on SOC Decisions.
  No Outcome nodes. No HAS_OUTCOME edges. Factor vectors embedded on Decision.
- **Forward-write bug:** age_client.py L848 CREATE does not set domain.
- **Scorer:** SOC uses InMemoryGraphStore + file checkpoint. Does NOT read L5.
- **Conservation query:** `d.domain = 'soc' OR d.domain IS NULL` (handles both).
- **Live V bug:** count_verified(store,'soc') returns 0 (edge-based implementation).

## §1.2 Stale nodes (4,871 total)

| Label | Count | Evidence |
|---|---|---|
| Outcome | 1,015 | 100% orphaned, SDK domains, zero Decision overlap |
| EvidenceReceipt | 216 | 100% orphaned |
| CentroidCheckpoint | 1,015 | 100% orphaned |
| DecisionDistanceLog | 2,139 | 100% orphaned |
| DecisionEntityLink | 216 | 100% orphaned |
| EvolutionEvent | 142 | 0 edges, 0 Decision overlap |
| L5Centroid | 17 | Wrong: Trading=4 vs 0 in SQLite |
| L5DKWeight | 4 | Wrong: Trading claims 280 decisions |
| L5ConservationState | 5 | Wrong: Trading V=351 vs actual 150; SOC V=37 vs actual 4,899 |
| L5DKWeightArchive | 102 | Stale archive of wrong state |

SOC confirmed: does not read L5 at startup. L5 deletion inert for SOC.

## §1.3 Other AGE state

- TRIGGERED_EVOLUTION: 0 edges globally. Collision theoretical.
- 19 empty vertex labels: catalog artifacts, all count=0. No action.
- rl_posteriors table: 0 rows.
- protocol_v2_test graph: keep for conformance tests.
- 55 diagnostic/scratch graphs: disposable, from prior sessions.

## §1.4 SQLite copilots

| Copilot | Total | Verified | Pending | V baseline | ID format |
|---|---|---|---|---|---|
| Trading | 201 | 150 | 51 | 150 | TRD-* |
| Purchasing | 520 | 20 | 500 | 20 | bare hex |
| DataOps | 620 | 20 | 600 | 20 | bare hex |
| S2P | 24,032 | 12 | 24,020 | 12 | bare hex |

All 25,171 pending are real scored work (factor_vector, confidence, probabilities).
No ghosts. Centroids derive from write_outcome/learn only — pending exclusion
has zero behavioral impact on scorer state.

## §1.5 Confirmed behaviors

| Behavior | Evidence |
|---|---|
| write_outcome() sets Decision.status to confirmed/overridden | age_graph_store.py:762-810 |
| write_decision() does NOT update centroids | scorer.py:243 |
| learn() → write_outcome() DOES update centroids/DK | scorer.py:464 |
| Factor vectors embedded on Decision (zero FactorVector nodes) | age_graph_store.py:543-670 |
| Category vocabularies completely disjoint across all 5 domains | Live queries, July 20 |
| get_decisions() defaults to 400-row limit | age_graph_store.py:1520 |
| Rule #38 violated in all 4 SDK copilots (1 direct SQLiteGraphStore each) | main.py in each copilot |

---

# §2 DESIGN DECISIONS (locked)

| # | Decision | Resolution |
|---|---|---|
| D1 | DomainContext | Projection, closed registry |
| D2 | V-transition | Property-based, both branches, no edge dependency (§3.1) |
| D3 | ShadowDecision | SOC-specific, excluded from V |
| D4 | FactorVector | Embedded on Decision (matching live writer) |
| D5 | Canonical edges | Forward-only. HAS_OUTCOME for audit chain, not V |
| D6 | SOC compatibility | Permanent projection |
| D7 | DataOps context | Backfill 29 nodes (WHERE domain IS NULL only) |
| D8 | Decision domain | Forward-write fix FIRST, then backfill 5,114 |
| D9 | Stale cleanup | Delete 4,871 nodes (10 labels) |
| D10 | Phase rollback | Dual-write → read-diff → flip. Revert = un-flip + restore gate |
| DA | Pending policy | A2: migrate all (verified + pending). No behavioral cost |
| DB | Outcome topology | Migration writes Outcome + HAS_OUTCOME + status on Decision |
| DC | Scratch promotion | C2: batched direct-write, per-batch PostgreSQL transactions |
| DL | L5 state | Delete stale. Cold start. SOC confirmed not affected |

---

# §2.1 OPEN DECISIONS

These decisions cannot be resolved now. Each has a defined trigger,
investigation, and deadline.

| ID | Decision | Options | Trigger | Deadline | Blocks |
|---|---|---|---|---|---|
| **OD-1** | S2P entity edges (353): migrate, defer, or discard? | (a) Target nodes exist in AGE AND live writer creates them → migrate. (b) Target nodes don't exist → defer. (c) Live writer doesn't create entity edges → defer until it does. | §3.2.7 investigation queries (schema + AGE node check + live writer check) | Before S2P migration (week 6) | §8.3 S2P migration only. Does NOT affect receipt migration (receipts always migrate). |
| **OD-2** | Production scorer convergence: accept bootstrap cold-start for Phase 4 copilots? | (a) Accept — bootstrap centroids converge. (b) L2: migrate SQLite L5 tables to warm-start. | §7.7 Trading observation: after 50 live-verified decisions, compare production centroids against SQLite baseline. **Criterion: cosine >= 0.90 per category with >= 5 verified.** Categories with < 5 excluded. **Time contingency:** if 50 verified decisions have not occurred within 2 weeks, apply the same criterion to however many are available. If >= 20 decisions exist and all qualifying categories pass → accept L1. If < 20 decisions exist → accept L1 for Trading (small impact) and evaluate L2 separately for each Phase 4 copilot based on their verified count (Purchasing=20, DataOps=20, S2P=12). | After Trading flip (week 6), before Phase 4 | §8.1-8.3 Phase 4 migrations |
| **OD-3** | TRIGGERED_EVOLUTION naming: what label do SDK copilots use? | (a) Keep label, different topology. (b) SDK uses EVOLVED_FROM. (c) Coexist, filter by type. | Phase 2 naming analysis | Before any copilot creates evolution events (no urgency — 0 edges) | OD-4 |
| **OD-4** | Evolution events (Trading=1, DataOps=1): migrate or discard? | (a) Migrate after OD-3. (b) Discard — 2 rows. | OD-3 resolution | Before Phase 4 if (a), otherwise no deadline | Nothing critical |
| **OD-5** | V parity: which SOC callable? | Identify exact method in LearningHealthMonitor that computes verified count. | S1 Prompt 0 discovery | **Blocks Phase 1 completion** (not Phase 1 start). §5.9 D2 gate requires V parity. | §5.9 completion, §10.8 V parity |
| **OD-6** | Phase 6 receipt traversal: S2P has 4 receipts — require traversal proof or skip? | (a) Include — 4 rows proves topology. (b) Skip — HAS_OUTCOME sufficient. | Receipt migration completes (unconditional) | Phase 6 (week 8) | §10.4 wording only |
| **OD-7** | write_outcome compound identity: how does domain reach the MATCH clause? | (a) Add domain to AGEGraphStore constructor, use self.domain in MATCH. (b) Add domain parameter to write_outcome protocol signature (broader change, affects all callers). Option (c) single-key is REJECTED — bare hex IDs across Purchasing/DataOps/S2P have no uniqueness guarantee. | §6.1b implementation: read AGEGraphStore constructor + write_outcome, choose (a) or (b) | Before Phase 2 completion (week 4) | §7.5 dual-write flip, §3.4 DualWriteStore |
| **OD-8** | write_entity_enrichment: implement on AGE or defer? | (a) Implement AGE support — required for full dual-write protocol coverage. (b) Defer — AGE raises NotImplementedError today; DualWriteStore skips secondary for this method; accept incomplete dual-write coverage. | Codex S3 Prompt 0 reads AGE enrichment implementation to assess scope | Before Phase 2 DualWriteStore claims full coverage | §3.4.3 delegation completeness, §7.0 go/no-go |

**Phase 1 blocking rule:** Phase 1 CAN START without any OD resolved.
Phase 1 CANNOT COMPLETE until OD-5 is resolved (V parity callable identified).
OD-7 must resolve before Phase 2 completion and any production flip.
OD-8 must resolve before DualWriteStore claims full protocol coverage.
All other ODs resolve in their stated phases.

---

# §3 ARCHITECTURE SPECIFICATIONS

## §3.1 V function (D2) — count_verified

### §3.1.1 Locked predicate

```
V(domain) = count(DISTINCT d.decision_id) WHERE d.domain = domain AND
  (
    (d.status IS NOT NULL AND d.status IN ['confirmed','overridden'])
    OR
    (d.status IS NULL AND d.outcome IS NOT NULL)
  )
```

Property-based. No edge traversal. Two branches are complementary by
construction: `status IS NOT NULL` vs `status IS NULL`. A decision
cannot satisfy both. Double-counting is structurally impossible.

### §3.1.2 Population coverage

| Population | status | outcome prop | Branch | V? |
|---|---|---|---|---|
| SDK verified (migrated) | 'confirmed'/'overridden' | on Outcome node | 1 | ✓ |
| SDK pending (migrated) | 'pending' | absent | neither | ✗ |
| SOC verified | NULL | 'correct'/'incorrect' | 2 | ✓ |
| SOC unverified | NULL | NULL | 2 fails | ✗ |
| SDK live verified (post-flip) | 'confirmed'/'overridden' | on Outcome node | 1 | ✓ |
| SDK live pending (post-flip) | 'pending' | absent | neither | ✗ |

### §3.1.3 Exact AGE Cypher

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)
  WHERE d.domain = '<domain>'
  AND (
    (d.status IS NOT NULL AND d.status IN ['confirmed','overridden'])
    OR
    (d.status IS NULL AND d.outcome IS NOT NULL)
  )
  RETURN count(DISTINCT d.decision_id) AS v
$$) as (v agtype);
```

Use _S() or literal string for domain. No $params (AGE limitation).
**Validate domain against the known set before interpolation:**
```python
VALID_DOMAINS = frozenset({"soc", "trading", "purchasing", "dataops", "s2p"})
if domain not in VALID_DOMAINS:
    raise ValueError(f"Unknown domain: {domain}")
```
This closes the injection path permanently. Domain is internal with five
known values — validation is one line.

### §3.1.4 Methods to change

| Method | File | Current | Change to |
|---|---|---|---|
| count_verified(domain) | age_graph_store.py | Edge-based (HAS_OUTCOME) | §3.1.3 predicate |
| count_verified_decisions(domain) | age_graph_store.py | Status-based only | §3.1.3 predicate |
| get_verified_decisions(domain) | age_graph_store.py | Edge-based | §3.1.3 WHERE clause |
| count_correct(domain) | age_graph_store.py | Edge-based | Dual-branch: Branch 1 traverse HAS_OUTCOME→Outcome.is_correct=true (legitimate edge use); Branch 2 d.correct=true AND d.status IS NULL |
| AGESDKAdapter delegations | age_sdk_adapter.py | Pass-through | Inherits fix via delegation |

### §3.1.5 Callers (must not change signatures)

| Caller | File | Method called |
|---|---|---|
| scorer.py conservation | copilot_sdk/scoring/scorer.py:453 | store.count_verified_decisions() |
| scorer.py DK refresh | copilot_sdk/scoring/scorer.py:811 | store.count_verified_decisions() |
| Various API endpoints | per copilot | Via store interface |

All callers use the GraphStore protocol interface. Method signatures
preserved. No caller changes needed.

### §3.1.6 count_correct — legitimate edge use

count_correct needs the Outcome node to read is_correct. This is a
property read on a linked node, not an existence check for V. The query:

```
Branch 1: MATCH (d:Decision {domain: '<domain>'})
           WHERE d.status IN ['confirmed','overridden']
           MATCH (d)-[:HAS_OUTCOME]->(o:Outcome)
           WHERE o.is_correct = true
Branch 2: MATCH (d:Decision {domain: '<domain>'})
           WHERE d.status IS NULL AND d.correct = true
```

**d.correct type hazard:** V uses `d.outcome IS NOT NULL` (type-agnostic,
safe). count_correct uses `d.correct = true` (equality, type-sensitive).
PF-7 already caught `is_correct` stored as boolean — but `d.correct` on
SOC Decisions is **unverified**. If stored as 1/0, 'true'/'false', or
'correct'/'incorrect', the equality silently returns 0.

**Pre-flight check (add to Phase 1 §5.9):**
```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision) WHERE d.correct IS NOT NULL
  RETURN d.correct, count(*) ORDER BY count(*) DESC
$$) as (val agtype, c agtype);
```

Record the type. If boolean true/false → `d.correct = true` works.
If string or integer → adjust the Branch 2 predicate to match.

### §3.1.7 Fixtures (8)

| # | Setup | Assert |
|---|---|---|
| 1 | Decision: status=NULL, outcome='correct' | counted via Branch 2 |
| 2 | Decision: status='confirmed' | counted via Branch 1 |
| 3 | Decision: status='confirmed', outcome='correct' | counted ONCE (Branch 1 only) |
| 4 | Decision: status='pending', outcome='correct' | NOT counted |
| 5 | Measure V_branch1 + V_branch2 - V_total | must = 0 (no double-count) |
| 6 | count_verified(store, 'soc') | >= 4,899 (live gate) |
| 7 | count_verified(store, 'trading') after Phase 3 | >= 150 |
| 8 | Create pending → write_outcome() → V | increments by exactly 1 |

Run all 8 against BOTH AGEGraphStore and SQLiteGraphStore.

### §3.1.8 V parity (SOC runtime vs adapter)

SOC computes V via LearningHealthMonitor.evaluate() →
internal verified count from direct Decision-property queries
(learning_health.py:470). After D2 fix, add a parity test.

The exact SOC callable must be identified during S1 implementation
(open decision OD-5). The parity assertion is:

```python
soc_internal_v = <discovered callable>(domain='soc')
adapter_v = count_verified(age_store, 'soc')
assert soc_internal_v == adapter_v
```

---

## §3.2 Migration writer

### §3.2.1 Per-table source-to-AGE mapping

| SQLite table | AGE topology | Action | Gate |
|---|---|---|---|
| `decisions` | Decision node (all props + status + factor_vector embedded + migration_source='sqlite') | **MIGRATE** | count(Decision {domain, migration_source:'sqlite'}) = SQLite total |
| `outcomes` | Outcome node + HAS_OUTCOME edge (Decision→Outcome) | **MIGRATE** | count(HAS_OUTCOME for domain) = SQLite verified count |
| `centroid_checkpoints` | CentroidCheckpoint node + HAS_CENTROID_CHECKPOINT edge | **MIGRATE** | count matches SQLite per copilot |
| `evidence_receipts` | EvidenceReceipt node + EMITTED_RECEIPT edge | **MIGRATE** | count matches SQLite per copilot |
| `decision_entity_edges` | Edge from Decision to entity node | **INVESTIGATE (OD-1)** | S2P=353. Verdict required before S2P migration |
| `evolution_events` | Deferred | **DEFER (OD-3/OD-4)** | Trading=1, DataOps=1. Naming decision first |
| `observations` | Not migrated | **RETAIN LOCAL** | S2P=680. Pre-decision input. Not in cross-copilot scope |
| `observation_entity_edges` | Not migrated | **RETAIN LOCAL** | |
| `observation_factor_vectors` | Not migrated | **RETAIN LOCAL** | |
| `conservation_snapshots` | Not migrated | **RE-DERIVE** | Operational state. Re-derived post-flip |
| `l5_centroids` | Not migrated | **RE-DERIVE** | Cold start (§3.6) |
| `l5_conservation_state` | Not migrated | **RE-DERIVE** | Cold start |
| `l5_dk_weights` | Not migrated | **RE-DERIVE** | Cold start |
| `l5_dk_weight_archive` | Not migrated | **DISCARD** | |
| `fingerprints` | Not migrated | **RETAIN LOCAL** | Zero rows in all copilots |
| `rl_state` | Not migrated | **RETAIN LOCAL** | Trading=5 rows. Operational |
| `outbox`, `outbox_quarantine` | Not migrated | **DISCARD** | Transient queues |
| `decisions_archive` | Not migrated | **RETAIN LOCAL** | Empty. Holds future archived data |
| `sqlite_sequence` | Not migrated | **DISCARD** | SQLite internal |

### §3.2.2 Node/edge estimates

| Copilot | Decisions | Outcomes | HAS_OUTCOME | Checkpoints+edges | Receipts+edges | Total |
|---|---|---|---|---|---|---|
| Trading | 201 | 150 | 150 | 5+5 | 0 | ~511 |
| Purchasing | 520 | 20 | 20 | 0 | 0 | ~560 |
| DataOps | 620 | 20 | 20 | 0 | 0 | ~660 |
| S2P | 24,032 | 12 | 12 | 12+12 | 4+4 | ~24,088 |

S2P entity edges (353): deferred pending §3.2.7 investigation.

### §3.2.3 Per-verified-decision write sequence

```
1. MATCH (d:Decision {domain: '<domain>', decision_id: '<id>'}) RETURN d
   → If exists: skip (idempotent)
   → If not exists: CREATE (d:Decision {
        decision_id: '<id>',
        domain: '<domain>',
        status: '<confirmed|overridden>',        ← FROM SQLite
        category: '<cat>',
        confidence: <float>,
        factor_vector: '<json>',                  ← EMBEDDED
        ... all other decision columns ...,
        migration_source: 'sqlite',
        migration_ts: <epoch>
      })

2. CREATE (o:Outcome {
        decision_id: '<id>',
        domain: '<domain>',
        actual_action: '...',
        actual_index: <int>,
        is_correct: <bool>,
        ... other columns present in this copilot's outcomes table ...,
        migration_source: 'sqlite'
   })

3. MATCH (d:Decision {domain:'<domain>', decision_id:'<id>'}),
         (o:Outcome {domain:'<domain>', decision_id:'<id>'})
   CREATE (d)-[:HAS_OUTCOME]->(o) RETURN 1

4. For each centroid_checkpoints row with this decision_id:
   CREATE checkpoint node + HAS_CENTROID_CHECKPOINT edge

5. For each evidence_receipts row with this decision_id:
   CREATE receipt node + EMITTED_RECEIPT edge
```

### §3.2.4 Per-pending-decision write sequence

```
1. MATCH (d:Decision {domain: '<domain>', decision_id: '<id>'}) RETURN d
   → If exists: skip
   → If not exists: CREATE (d:Decision {
        decision_id: '<id>',
        domain: '<domain>',
        status: 'pending',
        ... all other decision columns ...,
        migration_source: 'sqlite',
        migration_ts: <epoch>
      })

   No Outcome node. No HAS_OUTCOME edge.
```

### §3.2.5 Schema discovery

Outcome columns vary per copilot. Before writing Outcome nodes, the
migration must run PRAGMA table_info(outcomes) and map only columns
that exist. Columns to attempt: actual_action, actual_index, is_correct,
reward, verified_at, verifier, metadata. Missing columns are skipped —
the Outcome node is created with available properties only.

Same approach for centroid_checkpoints and evidence_receipts tables.

### §3.2.6 Identity and idempotency

All MATCH operations use compound key: (domain, decision_id).
Never decision_id alone. The shared graph has multiple domains;
collision isolation requires the compound key.

### §3.2.7 Entity edge investigation (pre-S2P gate, OD-1)

S2P has 353 decision_entity_edges. Before S2P migration:

**Investigation queries:**
```sql
-- 1. Schema
-- Run in Python: sqlite3.connect(s2p_db).execute("PRAGMA table_info(decision_entity_edges)")

-- 2. Sample rows (10)
-- SELECT * FROM decision_entity_edges LIMIT 10

-- 3. Distinct entity_id values
-- SELECT DISTINCT entity_id FROM decision_entity_edges

-- 4. For each sample entity_id, check AGE:
SELECT * FROM cypher('soc_graph', $$
  MATCH (n) WHERE n.entity_id = '<sample_id>' RETURN labels(n), properties(n)
$$) as (labels agtype, props agtype);

-- 5. Check live writer
-- Read AGEGraphStoreAdapter for entity edge write methods
-- grep -n "entity_edge\|entity_link\|INVOLVES" age_graph_store.py
```

**Verdict template (must be filled before S2P migration):**
```
ENTITY_EDGE_INVESTIGATION:
  schema: <columns>
  sample_entity_ids: <list>
  target_nodes_exist_in_AGE: YES / NO
  live_writer_creates_entity_edges: YES / NO
  VERDICT: MIGRATE / DEFER / DISCARD
  REASON: <one sentence>
  SIGNED: <date>
```

**Verdict options:**
- Target nodes exist AND live writer creates them → MIGRATE
- Target nodes don't exist → DEFER (edges would dangle)
- Live writer doesn't create entity edges → DEFER until it does

This investigation must complete before Phase 4 S2P migration.

---

## §3.3 Batched direct-write (DC)

### §3.3.1 Batch specification

- **Batch size:** 1,000 decisions (configurable via --batch-size)
- **Ordering:** SQLite rowid (monotonic — decision_id is not ordered)
- **Transaction:** Each batch is one PostgreSQL transaction:
  conn.autocommit = False; <cypher calls>; conn.commit()
  If a batch fails mid-way, the uncommitted transaction is rolled back
  by PostgreSQL. Only committed batches are persisted.
- **Cypher calls per batch:** ~2 per decision (MATCH + CREATE) plus
  ~1 per outcome + edge calls. For a batch of 1,000 with 50 verified:
  ~2,000 decision calls + ~150 outcome/edge calls = ~2,150 total.

### §3.3.2 Checkpoint format

After each committed batch, write to `<domain>_migration_checkpoint.json`:

```json
{
  "domain": "trading",
  "last_rowid": 1000,
  "batch_number": 1,
  "decisions_written": 1000,
  "outcomes_written": 50,
  "timestamp": "2026-07-20T10:30:00Z",
  "status": "in_progress"
}
```

On completion: `"status": "complete"`.
On failure: file shows last successful batch.

### §3.3.3 Resume semantics

On restart with --resume:
1. Read checkpoint file for this domain.
2. If status = "complete": report already done, exit.
3. If status = "in_progress": resume from last_rowid + 1.
4. Idempotency (§3.2.6) ensures already-written decisions are skipped.
5. The last interrupted batch was rolled back by PostgreSQL — its
   decisions are not in AGE and will be re-attempted.

### §3.3.4 Rollback (domain-scoped, tagged only)

Deletes ONLY migration-created nodes. Does NOT delete shared context
nodes, non-migration decisions, or anything without migration_source tag.

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision {domain: 'trading', migration_source: 'sqlite'})
  OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o:Outcome {migration_source: 'sqlite'})
  OPTIONAL MATCH (d)-[:EMITTED_RECEIPT]->(r:EvidenceReceipt {migration_source: 'sqlite'})
  OPTIONAL MATCH (d)-[:HAS_CENTROID_CHECKPOINT]->(c:CentroidCheckpoint {migration_source: 'sqlite'})
  DETACH DELETE d, o, r, c
  RETURN count(*)
$$) as (deleted agtype);
```

Note: literal domain string, not $domain. migration_source tag on
every OPTIONAL MATCH prevents deleting non-migration nodes.

### §3.3.5 CLI interface

```powershell
python -m copilot_sdk.migrate sqlite_to_age --domain=trading --age-dsn="host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres" --graph-name=soc_graph --all-decisions --batch-size=1000 --resume
```

Flags:
- `--all-decisions`: include pending (default: verified only)
- `--batch-size=1000`: decisions per batch (default: 1000)
- `--resume`: resume from checkpoint file

### §3.3.6 Scale estimate

Trading (201): 1 batch, seconds.
Purchasing (520): 1 batch, seconds.
DataOps (620): 1 batch, seconds.
S2P (24,032): ~25 batches. **Estimated from benchmark gate (§3.3.7).**

### §3.3.7 Benchmark gate (pre-S2P)

Before S2P migration, run on a disposable test graph:
- 1,000-row batch: measure wall-clock duration
- 5,000-row migration: measure total, verify checkpoint, test resume
- Extrapolate 24,032-row estimate from measured per-batch time

**Gate:** Measured time documented. Acceptance limit set.
Replace "minutes" estimate with measured value.

### §3.3.8 Migration manifest (required before every flip)

After migration and before dual-write/flip, produce a manifest:

```json
{
  "domain": "trading",
  "source_db": "/home/baner/.ci-platform/trading/trading.db",
  "source_db_checksum": "<sha256>",
  "tool_version": "<package version from pyproject.toml or __version__>",
  "timestamp": "2026-07-20T10:30:00Z",
  "source_counts": {
    "decisions_total": 201,
    "decisions_verified": 150,
    "decisions_pending": 51,
    "outcomes": 150,
    "centroid_checkpoints": 5,
    "evidence_receipts": 0,
    "entity_edges": 0,
    "entity_edges_verdict": "N/A"
  },
  "age_counts_after": {
    "decisions_total": 201,
    "decisions_verified": 150,
    "decisions_pending": 51,
    "outcomes": 150,
    "has_outcome_edges": 150,
    "checkpoints": 5,
    "receipts": 0
  },
  "v_before": 150,
  "v_after": 150,
  "v_soc_before": 4899,
  "v_soc_after": 4899,
  "checkpoint_path": "trading_migration_checkpoint.json",
  "rollback_query": "§3.3.4",
  "outbox_count": 0,
  "cypher_acceptance_test": "PASS",
  "status": "migrated_awaiting_flip"
}
```

**Gate:** All source counts match AGE counts. V unchanged.

---

## §3.4 DualWriteStore

### §3.4.1 Identity problem and resolution

**Problem:** `write_decision()` generates DIFFERENT IDs in each store.
SQLite uses `metadata["decision_id"]`. AGE generates fresh `DEC-<uuid>`.
A naive dual-write creates divergent IDs, after which `write_outcome()`
cannot find the secondary Decision.

**Resolution:** DualWriteStore intercepts `write_decision()` and calls
`write_governed_decision()` on the secondary with the primary's returned ID.
The governed path accepts caller-provided IDs in both stores.

**Signature mismatch:** The two methods have materially different inputs:

```
# Raw path (6 positional args + metadata):
write_decision(domain, category, action, confidence, factors, metadata) -> str

# Governed path (14 positional args + metadata):
write_governed_decision(decision_id, domain, category, category_index,
  recommended_action, recommended_index, confidence, probabilities,
  factor_vector, factor_names, source, scorer_version, preset_version,
  factor_schema_version, metadata) -> None
```

### §3.4.2 Field source policy for write_decision → write_governed_decision

| Governed field | Source in DualWriteStore |
|---|---|
| decision_id | Primary's returned ID |
| domain | write_decision positional arg `domain` |
| category | write_decision positional arg `category` |
| recommended_action | write_decision positional arg `action` |
| confidence | write_decision positional arg `confidence` |
| factor_vector | `metadata["factor_vector"]`; raw `factors` arg is a named-value dict, not the ordered vector |
| category_index | `metadata["category_index"]` — scorer populates (scorer.py:260-268) |
| recommended_index | `metadata["recommended_index"]` — scorer populates (scorer.py:260-268) |
| probabilities | `metadata["probabilities"]` — scorer populates (scorer.py:260-268) |
| factor_names | **NOT in current scorer metadata. Scorer must add it before dual-write deployment.** |
| source | Default: `"score"`. Optional enrichment. |
| scorer_version | Default: `""`. Optional enrichment. |
| preset_version | Default: `""`. Optional enrichment. |
| factor_schema_version | Default: `""`. Optional enrichment. |

**Pre-conditions (must be completed before DualWriteStore deployment):**
1. Scorer must add `factor_names` to `decision_metadata` in `score()`.
2. Optionally add `source`, `scorer_version`, `preset_version`,
   `factor_schema_version` for richer governed records.

**Non-scorer callers:** S2P has a direct `write_decision()` caller
(s2p.py:1610-1638) outside the scorer path. Its metadata supplies
`category_index`, `recommended_index`, `probabilities`, and `factor_vector`,
but lacks `factor_names` and the optional source/version fields.
**This path must either:**
- (a) Be adapted to populate `factor_names` in metadata, OR
- (b) Be routed through `write_governed_decision()` directly, OR
- (c) Bypass dual-write and write only to the primary store (acceptable
  if S2P hasn't flipped to AGE yet).

Codex S3 Prompt 0 must discover ALL callers of `write_decision()` beyond
`scorer.py` and define handling for each.

### §3.4.3 Protocol delegation contract

DualWriteStore implements ProtocolV2GraphStore. It delegates EVERY method
from both GraphStore (protocol.py:19-128) and ProtocolV2GraphStore
(protocol.py:142-280).

**The complete method list must be read from protocol.py during Codex S3
Prompt 0.** Prior versions of this document missed methods between
protocol.py lines 53-85. The Codex prompt must enumerate every method
by introspecting the protocol classes and verify each is delegated.

**Delegation rules:**

| Category / methods | Rule |
|---|---|
| `write_decision()` | **The only method requiring transformation.** Call primary, capture returned ID. Call `write_governed_decision()` on secondary with transformed args (§3.4.2). |
| `write_outcome()` | Call both stores with same `decision_id`. OD-7 governs compound identity safety — single-key matching is NOT accepted until OD-7 resolves. |
| `save_centroids()`, `archive_old_decisions()` | State-mutating GraphStore writes. Delegate primary first and secondary with identical arguments; return the primary result. They are not eligible for asynchronous replay until §3.4.5 defines an operation-specific idempotency contract. |
| `write_entity_enrichment()` | Secondary AGE support currently raises `NotImplementedError`. Do not enable this operation under dual-write until the implementation/defer decision is recorded and tested. |
| All other ProtocolV2 write methods | Call both stores with identical arguments. Use the operation-specific replay rule in §3.4.5; not every method has a caller-provided ID. |
| `get_decision()`, `get_decisions()`, `get_all_decisions()`, `get_verified_decisions()`, `count_verified()`, `count_correct()`, `count_decisions()`, `load_latest_centroids()`, `get_centroid_checkpoints()`, `count_archived()`, `read_entity_enrichment()`, `list_entity_enrichments()` | Delegate to primary only. Secondary is never read during dual-write. |
| `close()` | Close both stores. |
| `domain_scoped_reset()` | Call both stores. |

**Completeness test (go/no-go gate §7.0):** Introspect all abstract
methods in GraphStore + ProtocolV2GraphStore. For each, verify
DualWriteStore delegates it. Any missing method fails the gate.

### §3.4.4 Failure semantics

- Primary write fails → raise (fail the request).
- Secondary write fails → log error, record in outbox, continue.
  Do NOT fail the request. Reset diff counter to 0. **Exception:** methods
  marked "No asynchronous replay" in §3.4.5 fail closed or require operator
  intervention; they must not be silently queued.
- Secondary never blocks primary.

### §3.4.5 Outbox format (replayable payloads)

Each outbox entry stores the exact method name, full serializable
arguments, and a method-specific idempotency key:

```json
{
  "method": "write_governed_decision",
  "args": { "decision_id": "TRD-abc123", "domain": "trading", "...": "..." },
  "idempotency_key": "write_governed_decision:trading:TRD-abc123",
  "timestamp": "2026-07-20T10:30:00Z",
  "error": "connection refused",
  "retries": 0
}
```

**Per-method idempotency keys:**

| Method | Key |
|---|---|
| write_governed_decision | `(method, domain, decision_id)` |
| write_outcome | `(method, decision_id)` — extends to (method, domain, decision_id) after OD-7 |
| write_observation | `(method, domain, observation_id)` |
| append_evidence_receipt | `(method, domain, receipt_intent_id)` |
| write_conservation_status | `(method, domain, status_id)` |
| write_fingerprint | `(method, domain, fingerprint_id)` |
| write_centroid_checkpoint | `(method, domain, checkpoint_id)` |
| write_evolution_event | `(method, domain, event_id)` |
| link_entity | `(method, domain, decision_id, entity_id, entity_type)` |
| archive_decisions | `(method, domain, before, status_filter, confirm_verified)` |
| write_entity_enrichment | `(method, idempotency_key)` when supplied; otherwise no asynchronous replay |
| save_centroids | No asynchronous replay until a stable operation-specific key is designed |
| archive_old_decisions | No asynchronous replay until a stable operation-specific key is designed |
| domain_scoped_reset | No asynchronous replay; a failed destructive reset requires operator intervention |

Persisted to `<domain>_dual_write_outbox.json` after each failure.

### §3.4.6 Outbox replay

`replay_outbox()`: for each entry, call `secondary.<method>(**entry.args)`.
Check idempotency key before calling — skip if target already exists.
Return list of still-failed entries. Clear succeeded entries.
**Before flip: outbox must be empty.** Flip is blocked if entries remain.

### §3.4.7 Factory integration

```
GRAPH_BACKEND=dual-write
GRAPH_WRITE_PRIMARY=sqlite
GRAPH_WRITE_SECONDARY=age
```

Factory constructs both stores, wraps in DualWriteStore.

## §3.5 ReadDiffRunner

### §3.5.1 Interface

```python
class ReadDiffRunner:
    def __init__(self, primary: GraphStore, secondary: GraphStore, domain: str): ...

    def compare_all(self) -> list[Discrepancy]:
        """Full comparison of all decisions in both stores."""

    def compare_sample(self, n: int = 1000) -> list[Discrepancy]:
        """Random sample of n decisions for scale."""
```

### §3.5.2 Semantic equality

Match decisions by compound key (domain, decision_id).

**Fields compared (all decisions):**
- status (string equality)
- category (string equality)
- category_index (integer equality)
- confidence (float, tolerance 1e-6)
- recommended_action (string equality)
- recommended_index (integer equality)
- factor_vector (element-wise float comparison, tolerance 1e-6; null-equal if both null)
- probabilities (element-wise float comparison, tolerance 1e-6)
- domain (string equality)

**Additional fields for verified decisions (status in confirmed/overridden):**
- is_correct (boolean equality)
- actual_action (string equality)

**Normalization contract:** `get_decisions()` and `get_all_decisions()`
already return normalized decision dictionaries in both stores. SQLite
deserializes JSON in `_decision_from_row()` (sqlite_store.py:2976); AGE
deserializes the same fields in `_node_to_dict()` (age_graph_store.py:2395).
ReadDiffRunner compares these return values, not storage columns.

| Semantic field | SQLite return key/type | AGE return key/type | Normalization |
|---|---|---|---|
| factor_vector | `factor_vector`: `list` | `factor_vector`: `list` | Validate numeric list; compare element-wise |
| probabilities | `probabilities`: `list` | `probabilities`: `list` | Validate numeric list; compare element-wise |
| recommended_action | `recommended_action`: `str` | `recommended_action`: `str` | Direct string comparison |
| status | `status`: `str` or null | `status`: `str` or absent/null for legacy SOC | Normalize absent to null; direct comparison |
| metadata | `metadata`: `dict` | `metadata`: `dict` | Ignored unless a later contract promotes a field |

`get_decisions()` returns Decision fields only. For the verified-only
comparison, ReadDiffRunner must additionally call `get_verified_decisions()`
on both stores and join by `(domain, decision_id)`; both implementations
return `actual_action` and `is_correct` there.

**Ignored:**
- List ordering (decisions may come back in different order)
- Timestamp precision (epoch float vs int — round to integer before comparing)
- Metadata fields not in the above list (implementation-specific)

### §3.5.3 Discrepancy

```python
@dataclass
class Discrepancy:
    decision_id: str
    domain: str
    field: str           # e.g. "status", "confidence", "MISSING_IN_SECONDARY"
    primary_value: Any
    secondary_value: Any
```

Types: field mismatch, MISSING_IN_PRIMARY, MISSING_IN_SECONDARY.

### §3.5.4 Diff cycle protocol

- **Cycle:** One call to compare_all() (Trading scale) or compare_sample(1000) (S2P scale).
- **Counter:** N = 40 zero-discrepancy cycles.
- **Any discrepancy resets counter to 0.**
- **Any AGE write failure (from DualWriteStore) also resets to 0.**
- **Frequency:** Every 10 minutes (automated) or on-demand.
- **Flip condition:** N = 40 AND outbox empty.

### §3.5.5 At-scale strategy

At Trading (201): compare_all() every cycle.
At S2P (24,032): compare_sample(1000) every cycle. Full compare_all()
once at N=40 before flip. Requires §3.7 pagination.

---

## §3.6 Cold-start specification

After flip, SDK copilot scorer starts with no L5 state in AGE
(stale records deleted in Phase 1).

**Production scorer behavior after flip:**
The production scorer calls `startup_restore.py` at startup, which queries
AGE for L5Centroid, L5DKWeight, and L5ConservationState by domain. With
stale records deleted, these queries return empty → scorer starts from
**bootstrap centroids** (scorer.py:192-199). This is not a replay of
historic decisions — the scorer initializes with default/bootstrap state
and refines centroids as new live decisions are verified.

**The deterministic gate below is a VALIDATION of migration fidelity,
not a production rehydration step.** It runs on an isolated scorer, not
the production scorer. The production scorer's cold-start behavior is
accepted and monitored.

### §3.6.1 Deterministic gate (Phase 3, Trading)

Immediately after migration, before any new scoring:

1. Create an **isolated scorer** against a **scratch store** (not the
   production AGE store). The replay must NOT write Outcome nodes, edges,
   or status updates into the live graph — those already exist from migration.
2. Replay the 150 migrated verified Trading decisions through the scorer's
   centroid-update path, **ordered by created_at** (or SQLite rowid).
   Order matters: centroid learning is online and order-dependent. SQLite's
   centroids came from chronological arrival. Replaying in a different order
   produces different centroids for algorithmic reasons, not migration fidelity.
3. Compare replay-derived centroids against SQLite scorer's centroids for
   the same 150 decisions (also in chronological order).

**This proves:** the migrated data is complete and ordered correctly —
a fresh scorer fed the same decisions in the same order produces the same
centroids. It does NOT prove the production scorer starts warm; the
production scorer starts from bootstrap and is expected to diverge until
sufficient verified decisions arrive.

**Tolerance:** Cosine similarity >= 0.95 per category centroid.
Below threshold → investigate migration fidelity (ordering, precision,
missing field), not centroid convergence.

### §3.6.2 Behavioral observation

After deterministic gate passes, monitor first 50 live-scored decisions.
The production scorer starts from bootstrap, NOT from the replay state.
Monitor how quickly centroids converge toward the SQLite baseline as
verified decisions accumulate. This is an observation, not a gate.

### §3.6.3 Verdict for remaining copilots (OD-2)

Deterministic gate passes → migration fidelity confirmed.
Production cold start acceptable for Trading (150 verified = fast convergence).

**For Phase 4 copilots:** Purchasing (20 verified) and DataOps (20 verified)
have fewer decisions for convergence. S2P (12 verified) has the least.
If Trading's production scorer converges within 50 decisions → L1 confirmed.
If not → evaluate L2 (migrate SQLite L5 snapshots to AGE to warm-start
the production scorer) before Phase 4.

This is open decision OD-2. Must resolve after Phase 3, before Phase 4.

---

## §3.7 Pagination (G5)

### §3.7.1 Changes

| Method | Current | Change |
|---|---|---|
| get_decisions(domain) | limit=400 default | Add limit and offset params. Default limit=None (return all). |
| get_all_decisions(domain) | Exists but delegates to get_decisions with 400-row cap — **broken** | Fix: paginate internally (1,000 per page) and return complete list. |

Note: `get_verified_decisions()` already returns all rows in SQLite and
has no limit parameter in the protocol. The AGE implementation must match
this — remove any internal cap. No signature change needed.

Existing callers that pass no arguments currently receive at most 400 rows.
Changing the default to limit=None means they receive ALL rows — which for
S2P is 24,032. This is correct for data completeness but may cause latency
and memory regression on UI/API paths that were silently paginated.

**Caller audit (before flipping the default):** Enumerate all callers of
get_decisions() and get_verified_decisions() across all repos. For each:
- If it displays to UI or serializes to API response → give it an explicit
  limit (e.g., 100, 400) to preserve current behavior.
- If it computes aggregates, comparisons, or exports → leave limit=None.
- Document each caller's decision.

get_all_decisions() is what ReadDiffRunner calls for full comparison.

### §3.7.2 Gate

get_all_decisions(domain='s2p') returns all 24,032 rows.
Must complete before S2P migration.

---

# §4 DO NOT DO

- Do not make V depend on HAS_OUTCOME edges. V is property-based (§3.1).
- Do not omit status from migrated Decision nodes. Branch 1 requires it.
- Do not create FactorVector nodes. Embed on Decision.
- Do not use scratch graph for migration. Batched direct-write (§3.3).
- Do not leave stale L5 records.
- Do not use d.category equality for cross-domain proofs (disjoint vocabularies).
- Do not use hard V = N gates. Use V >= N.
- Do not remove a write gate without a documented revert path.
- Do not use unbound $params in AGE Cypher.
- Do not match by decision_id alone. Use (domain, decision_id).
- Do not delete non-migration nodes in rollback. Tag + delete tagged only (§3.3.4).
- Do not claim "one traversal, one answer." Use "one graph, one query."
- Do not re-derive V in Cypher. Call count_verified().
- Do not trust V through the AGE adapter until §3.1 fix lands.

---

# §5 PHASE 1: Cleanup + Backfill + V Fix (weeks 1-2)

## §5.1 Backup

```powershell
wsl -u root sh -c "pg_dump -h localhost -p 5433 -U postgres -d soc_copilot -t 'soc_graph.\"Outcome\"' -t 'soc_graph.\"EvidenceReceipt\"' -t 'soc_graph.\"CentroidCheckpoint\"' -t 'soc_graph.\"DecisionDistanceLog\"' -t 'soc_graph.\"DecisionEntityLink\"' -t 'soc_graph.\"EvolutionEvent\"' -t 'soc_graph.\"L5Centroid\"' -t 'soc_graph.\"L5DKWeight\"' -t 'soc_graph.\"L5ConservationState\"' -t 'soc_graph.\"L5DKWeightArchive\"' > /tmp/age_stale_backup.sql"
```

**Gate:** `wsl -u root wc -l /tmp/age_stale_backup.sql` returns > 0 lines.

**Restore (if rollback needed):**
```powershell
wsl -u root sh -c "psql -h localhost -p 5433 -U postgres -d soc_copilot < /tmp/age_stale_backup.sql"
```

## §5.2 Delete stale orphans (4,743 nodes, 6 labels)

```sql
LOAD 'age'; SET search_path = ag_catalog, "$user", public;

SELECT * FROM cypher('soc_graph', $$ MATCH (n:Outcome) DETACH DELETE n RETURN count(*) $$) as (deleted agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:EvidenceReceipt) DETACH DELETE n RETURN count(*) $$) as (deleted agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:CentroidCheckpoint) DETACH DELETE n RETURN count(*) $$) as (deleted agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:DecisionDistanceLog) DETACH DELETE n RETURN count(*) $$) as (deleted agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:DecisionEntityLink) DETACH DELETE n RETURN count(*) $$) as (deleted agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:EvolutionEvent) DETACH DELETE n RETURN count(*) $$) as (deleted agtype);
```

**Post-delete verification (separate queries — DELETE returns deleted count, not remaining):**

```sql
SELECT * FROM cypher('soc_graph', $$ MATCH (n:Outcome) RETURN count(n) $$) as (remaining agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:EvidenceReceipt) RETURN count(n) $$) as (remaining agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:CentroidCheckpoint) RETURN count(n) $$) as (remaining agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:DecisionDistanceLog) RETURN count(n) $$) as (remaining agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:DecisionEntityLink) RETURN count(n) $$) as (remaining agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:EvolutionEvent) RETURN count(n) $$) as (remaining agtype);
```

**Gate:** All 6 verification queries return 0. **Rollback:** §5.1 backup.

## §5.3 Delete stale L5 (128 nodes, 4 labels)

```sql
SELECT * FROM cypher('soc_graph', $$ MATCH (n:L5Centroid) DETACH DELETE n RETURN count(*) $$) as (deleted agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:L5DKWeight) DETACH DELETE n RETURN count(*) $$) as (deleted agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:L5ConservationState) DETACH DELETE n RETURN count(*) $$) as (deleted agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:L5DKWeightArchive) DETACH DELETE n RETURN count(*) $$) as (deleted agtype);

SELECT * FROM cypher('soc_graph', $$ MATCH (n:L5Centroid) RETURN count(n) $$) as (remaining agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:L5DKWeight) RETURN count(n) $$) as (remaining agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:L5ConservationState) RETURN count(n) $$) as (remaining agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:L5DKWeightArchive) RETURN count(n) $$) as (remaining agtype);
```

**Gate:** All 4 return 0. **Rollback:** §5.1 backup.

## §5.4 SOC forward-write fix (BEFORE backfill — prevents race)

age_client.py L848 CREATE: add `domain: 'soc'`.
L827 SET: add `d.domain = COALESCE(d.domain, 'soc')`.

**Gate:** SOC BE tests pass. New decision has domain='soc'.
**Rollback:** Revert the two-line change.

## §5.5 Decision domain backfill (5,114 nodes — AFTER §5.4)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision) WHERE d.domain IS NULL
  SET d.domain = 'soc', d.domain_source = 'backfill'
  RETURN count(*) AS updated
$$) as (updated agtype);
```

**Verify:**
```sql
SELECT * FROM cypher('soc_graph', $$ MATCH (d:Decision) WHERE d.domain IS NULL RETURN count(*) $$) as (c agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (d:Decision {domain:'soc'}) RETURN count(*) $$) as (c agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (d:Decision {domain:'soc'}) WHERE d.outcome IS NOT NULL RETURN count(*) $$) as (c agtype);
```

**Gate:** remaining=0, total >= 6,253, V >= 4,899.
**Rollback:** `MATCH (d:Decision {domain_source:'backfill'}) REMOVE d.domain, d.domain_source`

## §5.6 DataOps domain backfill (29 nodes)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (n:DataQualityAlert) WHERE n.domain IS NULL
  SET n.domain = 'dataops', n.domain_source = 'backfill' RETURN count(*)
$$) as (c agtype);
SELECT * FROM cypher('soc_graph', $$
  MATCH (n:PipelineSystem) WHERE n.domain IS NULL
  SET n.domain = 'dataops', n.domain_source = 'backfill' RETURN count(*)
$$) as (c agtype);
```

**Gate:** Untagged = 0.
**Rollback (tagged only — preserves any pre-existing domain):**
```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (n) WHERE n.domain_source = 'backfill'
  AND (n:DataQualityAlert OR n:PipelineSystem)
  REMOVE n.domain, n.domain_source RETURN count(*)
$$) as (c agtype);
```

## §5.7 PW gate

**Baseline capture (run BEFORE any Phase 1 changes):**
```powershell
cd "$env:CLAUDE_SOC\frontend"
npx playwright test "tests/e2e" --reporter=json --timeout=60000 --workers=1 > $env:CLAUDE_SOC\pw_baseline.json
```

**Post-change verification:**
```powershell
cd "$env:CLAUDE_SOC\frontend"
npx playwright test "tests/e2e" --reporter=list --timeout=60000 --workers=1
```

**Gate:** Same spec names fail as in pw_baseline.json. No new failures.

## §5.8 Diagnostic graph cleanup

55 scratch/diagnostic graphs. Disposable artifacts from prior sessions.
No backup needed — they are test/debug byproducts with no production value.

**Gate:** Only soc_graph and protocol_v2_test remain.

## §5.9 D2 — count_verified fix

Implement §3.1 in full. All methods (§3.1.4), all fixtures (§3.1.7),
both adapters, V parity (§3.1.8).

**SQLite V regression (live blast radius):** The D2 fix changes
`count_verified_decisions` for the four copilots running on SQLite TODAY.
The current SQLite predicate may differ from the locked D2 predicate — the
change could increase or decrease V depending on how the existing SQLite
implementation handles status/outcome combinations. Record pre-fix V for
all four, apply fix, assert unchanged:

```python
# Pre-fix baseline (record before changing any code)
for domain in ["trading", "purchasing", "dataops", "s2p"]:
    v = sqlite_store.count_verified_decisions(domain)
    print(f"pre-fix {domain}: V={v}")
# Expect: trading=150, purchasing=20, dataops=20, s2p=12

# Post-fix assertion (after code change)
for domain in ["trading", "purchasing", "dataops", "s2p"]:
    v = sqlite_store.count_verified_decisions(domain)
    assert v == baseline[domain], f"{domain} V changed: {baseline[domain]} → {v}"
```

**AGE Cypher acceptance tests (disposable graph):**
Before deploying the D2 predicate to production, run on a disposable graph:

```sql
-- Setup: load AGE extension first, then create disposable graph
LOAD 'age';
SET search_path = ag_catalog, "$user", public;
SELECT create_graph('age_cypher_acceptance_test');

-- Insert test decisions
SELECT * FROM cypher('age_cypher_acceptance_test', $$
  CREATE (:Decision {decision_id: 'TEST-001', domain: 'test', status: 'confirmed', outcome: 'correct'}) RETURN 1
$$) as (v agtype);
SELECT * FROM cypher('age_cypher_acceptance_test', $$
  CREATE (:Decision {decision_id: 'TEST-002', domain: 'test', outcome: 'correct'}) RETURN 1
$$) as (v agtype);
SELECT * FROM cypher('age_cypher_acceptance_test', $$
  CREATE (:Decision {decision_id: 'TEST-003', domain: 'test', status: 'pending', outcome: 'correct'}) RETURN 1
$$) as (v agtype);

-- Test 1: IN [...] syntax
SELECT * FROM cypher('age_cypher_acceptance_test', $$
  MATCH (d:Decision) WHERE d.status IN ['confirmed','overridden'] RETURN count(d)
$$) as (c agtype);
-- Expect: 1 (TEST-001)

-- Test 2: IS NULL / IS NOT NULL in same WHERE
SELECT * FROM cypher('age_cypher_acceptance_test', $$
  MATCH (d:Decision)
  WHERE (d.status IS NOT NULL AND d.status IN ['confirmed','overridden'])
     OR (d.status IS NULL AND d.outcome IS NOT NULL)
  RETURN count(d)
$$) as (c agtype);
-- Expect: 2 (TEST-001 + TEST-002, not TEST-003)

-- Test 3: Multi-variable OPTIONAL MATCH ... DETACH DELETE (with linked topology)
-- Step 3a: Create Decision
SELECT * FROM cypher('age_cypher_acceptance_test', $$
  CREATE (:Decision {decision_id: 'DEL-001', domain: 'test', migration_source: 'sqlite'}) RETURN 1
$$) as (v agtype);
-- Step 3b: Create Outcome
SELECT * FROM cypher('age_cypher_acceptance_test', $$
  CREATE (:Outcome {decision_id: 'DEL-001', migration_source: 'sqlite'}) RETURN 1
$$) as (v agtype);
-- Step 3c: Link with MATCH-then-CREATE (proven AGE pattern, not multi-CREATE)
SELECT * FROM cypher('age_cypher_acceptance_test', $$
  MATCH (d:Decision {decision_id: 'DEL-001'}), (o:Outcome {decision_id: 'DEL-001'})
  CREATE (d)-[:HAS_OUTCOME]->(o) RETURN 1
$$) as (v agtype);
-- Step 3d: Test rollback with multi-variable OPTIONAL MATCH DETACH DELETE
SELECT * FROM cypher('age_cypher_acceptance_test', $$
  MATCH (d:Decision {domain: 'test', migration_source: 'sqlite'})
  OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o:Outcome {migration_source: 'sqlite'})
  DETACH DELETE d, o RETURN count(*)
$$) as (c agtype);
-- Step 3e: Verify both Decision and linked Outcome deleted
SELECT * FROM cypher('age_cypher_acceptance_test', $$
  MATCH (n) WHERE n.decision_id = 'DEL-001' RETURN count(n)
$$) as (remaining agtype);
-- Expect: 0

-- Cleanup
SELECT drop_graph('age_cypher_acceptance_test', true);
```

If Test 1 (`IN [...]`) fails, use `(d.status = 'confirmed' OR d.status = 'overridden')`.
If Test 3 (multi-variable DETACH DELETE) fails, use sequential single-variable deletes.

**d.correct type pre-flight (§3.1.6):**
```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision) WHERE d.correct IS NOT NULL
  RETURN d.correct, count(*) ORDER BY count(*) DESC
$$) as (val agtype, c agtype);
```
If boolean → `d.correct = true` works. If string/integer → adjust Branch 2.

**Gate:** 8 fixtures pass on both adapters. count_verified(store,'soc') >= 4,899.
SQLite V unchanged for all 4 copilots. AGE Cypher acceptance tests pass.
d.correct type verified.
**Rollback:** Revert function + caller changes.

---

# §6 PHASE 2: Migration Tool + Conformance (weeks 2-5)

## §6.1 Migration writer implementation

Implement §3.2. Outcome topology, all-decisions, status on Decision,
schema discovery, compound identity, migration_source tagging.

**Tests required:**
- Verified: Outcome node + HAS_OUTCOME + status on Decision
- Pending: no Outcome, status='pending'
- Checkpoint + edge when rows exist
- Receipt + edge when rows exist
- factor_vector embedded, not node
- Idempotency: run twice, count unchanged
- Schema: missing outcome columns handled gracefully
- Output-equivalence: migrate one verified, write one via live adapter, diff = 0

**Gate:** All tests pass. **Rollback:** Revert sqlite_to_age.py.

## §6.1b Live adapter: compound identity fix (OD-7)

The live AGEGraphStoreAdapter.write_outcome() matches by decision_id alone
(age_graph_store.py:779). In a shared graph this risks collision. Fix to
match by (domain, decision_id). Implementation path determined by OD-7:
option (a) adds domain to AGEGraphStore constructor; option (b) adds it
to the protocol signature. Option (c) is rejected.

**Gate:** write_outcome Cypher uses both domain and decision_id in MATCH.
**Rollback:** Revert age_graph_store.py.

## §6.2 Batched direct-write implementation

Implement §3.3. Replace scratch graph. Checkpoint/resume.

**Tests required:**
- 1,000-row batch completes with correct counts
- Checkpoint written AFTER commit (not before)
- Interrupt mid-batch: checkpoint shows last completed batch.
  Resume: final count correct, no duplicates.
- Rollback deletes only migration-tagged nodes; non-migration nodes preserved.
- Run on disposable test graph (NOT soc_graph).

**Gate:** All tests pass including interrupt/resume at 1,000 rows.

## §6.3 DualWriteStore + ReadDiffRunner implementation

Implement §3.4 and §3.5.

**DualWriteStore tests:**
- Both writes succeed → both stores have decision
- Secondary fails → primary has decision, outbox has entry, no exception
- replay_outbox succeeds → secondary has decision, outbox cleared
- Reads come from primary only
- Diff counter resets on secondary failure

**ReadDiffRunner tests:**
- Identical stores → zero discrepancies
- One field different → one discrepancy with field name + values
- Missing decision in secondary → MISSING_IN_SECONDARY
- Extra decision in secondary → MISSING_IN_PRIMARY
- Timestamp precision difference → NOT a discrepancy

**Gate:** All tests pass. **Rollback:** Revert modules.

## §6.4 Entity edge investigation (§3.2.7)

Run before S2P migration. Output: migrate, defer, or discard.

## §6.5 Rule #38 factory compliance

All 4 copilots route through create_graph_store().
Default GRAPH_BACKEND=sqlite. Behavior unchanged.

**Gate:** All BE + PW suites pass. **Rollback:** Revert each main.py.

## §6.6 AGE conformance

88 tests. Report exact pass/skip/fail counts.
**Zero migration-related skips.** If any are skipped, list and justify.

**Gate:** pass count + skip justification. **Rollback:** N/A.

## §6.7 Projection module

Closed PROJECTION_PATTERNS registry. Scanner. Equivalence tests.
DataOps graph_queries.py wrapped.

**Gate:** All tests pass. Scanner clean.

## §6.8 Benchmark (§3.3.7)

Run after §6.2 complete. Measured S2P estimate replaces "minutes."

---

# §7 PHASE 3: Trading AGE Migration (weeks 5-6)

## §7.0 Go/no-go gate (Phase 2 → Phase 3)

**All must pass before Phase 3 begins:**

| Gate | Requirement |
|---|---|
| Migration writer | Outcome topology + status + checkpoint/resume tests pass |
| Batched writer | 1K interrupt/resume test passes on disposable graph |
| Scorer metadata | scorer.py adds factor_names to decision_metadata (§3.4.2 pre-condition) |
| Non-scorer callers | All write_decision callers (incl. S2P) handled per §3.4.2 |
| DualWriteStore | Full protocol delegation verified by introspection test |
| Shape parity | write_decision→write_governed_decision produces identical AGE node |
| ReadDiffRunner | Compares all §3.5.2 fields with normalization (§3.5.2) |
| OD-7 resolved | write_outcome uses compound identity |
| OD-8 resolved | write_entity_enrichment: if (a) implement → AGE enrichment works under dual-write. If (b) defer → DualWriteStore explicitly skips secondary for this method, introspection test documents the exception, and the completeness gate passes with that documented exclusion. |
| Outbox replay | Replay of governed payload succeeds + per-method idempotency (§3.4.5) |
| Conformance | Exact pass/skip/fail counts; zero migration-related skips |
| Rule #38 | All 4 copilots via factory |

**If any gate fails: HOLD Phase 3. Fix in Phase 2.**

## §7.1 Pre-migration

SQLite backup + AGE pg_dump. Verify count_verified(store,'soc') >= 4,899.

## §7.2 Migration

```powershell
cd "$env:CLAUDE_SDK"
python -m copilot_sdk.migrate sqlite_to_age --domain=trading --all-decisions --batch-size=1000 --age-dsn="host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres" --graph-name=soc_graph
```

**Post-migration verification:**
```sql
-- Total
SELECT * FROM cypher('soc_graph', $$ MATCH (d:Decision {domain:'trading'}) RETURN count(d) $$) as (c agtype);
-- Gate: 201

-- Status distribution
SELECT * FROM cypher('soc_graph', $$ MATCH (d:Decision {domain:'trading'}) RETURN d.status, count(d) $$) as (s agtype, c agtype);
-- Gate: confirmed:75, overridden:75, pending:51

-- Audit chain (edge count — not V)
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision {domain:'trading'})-[:HAS_OUTCOME]->(o:Outcome)
  RETURN count(DISTINCT d), count(o) $$) as (d agtype, o agtype);
-- Gate: 150, 150

-- V through function (property-based)
count_verified(store, 'trading')  -- Gate: >= 150
count_verified(store, 'soc')      -- Gate: >= 4,899

-- Pending without outcomes
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision {domain:'trading', status:'pending'})
  OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o)
  WITH d, o WHERE o IS NULL RETURN count(d) $$) as (c agtype);
-- Gate: 51

-- Migration tag
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision {domain:'trading', migration_source:'sqlite'}) RETURN count(d) $$) as (c agtype);
-- Gate: 201
```

**Rollback:** §3.3.4 domain-scoped tagged delete.

## §7.3 Output-equivalence test

Migrate one verified Trading decision. Write one equivalent through
AGEGraphStoreAdapter live. Diff subgraphs (properties, edges, topology).

**Gate:** Zero diff.

## §7.4 Remove Trading write gate

Remove graph_status.py:243 test-only rejection. Set GRAPH_BACKEND=age.

**Gate:** Trading BE tests pass.
**Rollback:** Restore rejection + GRAPH_BACKEND=sqlite.

## §7.5 Dual-write → read-diff → flip

Activate DualWriteStore (§3.4). Run ReadDiffRunner (§3.5).
compare_all() for Trading (201 decisions — full diff every cycle).

**Flip condition:** N=40 AND outbox empty.
**Revert:** GRAPH_READ_SOURCE=sqlite + restore write gate.

## §7.6 Trading PW

246/0 with --workers=1. Measure AGE latency.

## §7.7 Cold-start evaluation (§3.6)

Deterministic gate: cosine >= 0.95 per category.
Behavioral observation: 50 decisions.

## §7.8 Cross-copilot proof (Trading ↔ SOC)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision) WHERE d.domain IN ['soc','trading']
  RETURN d.domain, count(d) $$) as (domain agtype, c agtype);
```

**Gate:** Both domains present. V_soc >= 4,899.

---

# §8 PHASE 4: Purchasing + DataOps + S2P (weeks 6-8)

## §8.0 Pre-tasks

### §8.0.1 DataOps Rule #29

Wrap graph_queries.py 15 AGEClient references through projection.
**Gate:** BE tests + scanner clean. Must complete before DataOps migration.

### §8.0.2 DataOps bundle restore

Update demo bundle for AGE backend. Route through factory.
**Gate:** demo.py --preseed completes with GRAPH_BACKEND=age.

### §8.0.3 Pagination (§3.7)

Implement before S2P migration.
**Gate:** get_all_decisions('s2p') returns 24,032.

## §8.1 Purchasing (520 total, 20 verified, 500 pending)

SQLite backup. Migration. Verification (total=520, status distribution, V >= 20).
Remove write gate. Dual-write (N=40, compare_all). Flip. PW: 235/0/1.

**V regression:** soc >= 4,899, trading >= 150, purchasing >= 20.
**Rollback:** Tagged delete + restore gate + un-flip.

## §8.2 DataOps (620 total, 20 verified, 600 pending)

Pre-req: §8.0.1 + §8.0.2.
Same pattern. PW: 133/0/1.

## §8.2b Go/no-go gate (before S2P)

S2P is 48× larger than any prior migration. Require explicit sign-off:

| Gate | Requirement |
|---|---|
| Purchasing + DataOps | Both flipped, read-diff clean, V unchanged |
| Pagination | get_all_decisions('s2p') returns 24,032 |
| Benchmark | Measured per-batch time, acceptance limit set |
| OD-1 | Entity edge verdict signed |
| OD-2 | Production convergence accepted or L2 implemented |

## §8.3 S2P (24,032 total, 12 verified, 24,020 pending)

Pre-req: §8.0.3 (pagination) + §6.8 (benchmark) + §6.4 (entity investigation).

SQLite backup + AGE pg_dump. Migration with --batch-size=1000.

**Read-diff at scale:** compare_sample(1000) per cycle (draws from ALL statuses).
Full compare_all() once at N=40 before flip (requires pagination).

S2P entity edges (353): migrate only if OD-1 = migrate.

PW: 194/0.
**V regression:** all 5 domains.

## §8.4 Demo.py integration

All 5 copilots on AGE. Full PW gate. V regression all domains.

---

# §9 PHASE 5: Skipped (projection permanent)

---

# §10 PHASE 6: Cross-Copilot Proof (weeks 8-9)

**Framing:** ~96% SOC by count. Claims are structural, not volumetric.
"All five copilots on one graph" = decision records + audit chains.
SOC scorer state is outside AGE (InMemoryGraphStore + files).

## §10.1 Multi-domain visibility

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision) RETURN d.domain, count(d) ORDER BY count(d) DESC
$$) as (domain agtype, c agtype);
```

**Gate:** 5 rows: soc, trading, purchasing, dataops, s2p.

## §10.2 Per-domain V through one function

```python
for domain in ["soc", "s2p", "trading", "purchasing", "dataops"]:
    v = count_verified(store, domain)
    print(f"{domain}: V={v}")
```

**Gate:** soc >= 4,899; trading >= 150; purchasing >= 20; dataops >= 20; s2p >= 12.

## §10.3 Multi-domain status distribution

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision) RETURN d.domain, d.status, count(d) ORDER BY d.domain
$$) as (domain agtype, status agtype, c agtype);
```

**Expected:**

| Domain | Statuses |
|---|---|
| soc | NULL only (legacy, no status property) |
| trading | confirmed, overridden, pending |
| purchasing | confirmed, overridden, pending |
| dataops | confirmed, overridden, pending |
| s2p | confirmed, overridden, pending |

**Gate:** All expected values present.

## §10.4 SDK audit chain (real edges)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision {domain:'trading'})-[:HAS_OUTCOME]->(o:Outcome)
  RETURN d.decision_id, d.status, o.actual_action, o.is_correct LIMIT 5
$$) as (did agtype, s agtype, action agtype, correct agtype);
```

S2P receipts (receipts always migrate — §3.2.1):
```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision {domain:'s2p'})-[:EMITTED_RECEIPT]->(r:EvidenceReceipt)
  RETURN d.decision_id, r.chain_index LIMIT 5
$$) as (did agtype, chain agtype);
```

**Gate:** Returns rows (S2P has 4 receipts). If count < 4, investigate. (OD-6 determines whether this gate is required for sign-off or informational.)

## §10.5 SOC audit via projection

```python
results = projection.query("outcome", domain="soc", limit=5)
```

## §10.6 Cross-domain shared entity

Zero DomainContext nodes. Disjoint vocabularies. No natural shared entity.
Cross-domain edge traversal requires TransferPattern — future work.
Stated explicitly, not claimed.

## §10.7 Claim wording

- "one graph, one query" (not "one traversal, one answer")
- Decision records + audit chains shared. Scorer state per-copilot.
- Structural proof: §10.1, §10.2, §10.4.

## §10.8 V parity

Per §3.1.8. SOC runtime V == adapter count_verified(store,'soc').
**Gate:** Parity holds.

---

# §11 DEFINITION OF DONE

| Item | Gate |
|---|---|
| Backup | pg_dump non-empty |
| Stale deletion | 10 labels: all verification queries return 0 |
| Forward-write | domain='soc' on CREATE; BE pass; ordered BEFORE backfill |
| Domain backfill | IS NULL = 0; total >= 6,253; V >= 4,899 |
| D2/V fix (§3.1) | 8 fixtures both adapters; parity; all callers wired |
| Migration writer (§3.2) | Outcome + HAS_OUTCOME + status; equiv test; schema discovery |
| Batched writer (§3.3) | Checkpoint/resume; 1K interrupt test; tagged rollback |
| DualWriteStore (§3.4) | Full protocol; outbox; replay |
| ReadDiffRunner (§3.5) | Semantic equality; compound key; sample mode |
| Pagination (§3.7) | get_all_decisions returns all S2P rows |
| Rule #38 | All 4 copilots via factory |
| Conformance | Exact pass/skip/fail; zero migration-related skips |
| Projection | Registry; scanner; equivalence; DataOps wrapped |
| Entity investigation (§3.2.7) | Written verdict before S2P |
| Benchmark (§3.3.7) | Measured S2P estimate |
| Trading | 201 migrated; V >= 150; 246 PW; cold-start cosine >= 0.95 |
| Purchasing | 520; V >= 20; 235 PW |
| DataOps | 620; V >= 20; 133 PW; Rule #29; bundle |
| S2P | 24,032; V >= 12; 194 PW; pagination; benchmark |
| Demo.py | All copilots; shared graph; reset |
| Phase 6 | All 8 subsections; V parity; claim wording |

---

# §12 EXECUTION SEQUENCE

| Week | Work | Gate |
|---|---|---|
| 1-2 | §5: backup, delete 4,871, forward-write fix, backfill, D2 fix, cleanup | Counts=0; V >= 4,899 direct+function; PW diff empty |
| 2-5 | §6: migration writer, batched writer, dual-write, conformance, projection, entity investigation, benchmark | All §6 tests; 88/88; benchmark measured |
| 5-6 | §7: Trading migration, equiv test, dual-write, flip, cold-start, PW | V >= 150; 246 PW; cosine >= 0.95; cross-copilot |
| 6-8 | §8: Purchasing, DataOps, S2P (ascending) | All V baselines; all PW; demo.py |
| 8-9 | §10: structural proofs, V parity, claim wording | All 8 subsections pass |

~9 weeks. Phase 5 (§9) skipped.
