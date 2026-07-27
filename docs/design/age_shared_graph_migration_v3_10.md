# AGE Shared Graph Migration — Complete Execution Plan

**Date:** July 20, 2026 · **Version:** v3.10
**Authority:** judgment_memory_v2_7.md
**History:** v1→v3.9 (9 review cycles) → v3.10
**Scope:** Current state to "every §2 claim demonstrated"

---

## Changes v3.9 → v3.10

| # | Change |
|---|---|
| 1 | G5 restored: `get_decisions` pagination before S2P (defaults to 400 rows, S2P has 24,032) |
| 2 | Read-diff widened: samples ALL decisions (verified + pending), not just verified |
| 3 | Cold-start: deterministic centroid comparison as gate (cosine similarity ≥ 0.95), 50-decision monitoring as observation |
| 4 | Discrepancy rule explicit: any read discrepancy resets counter to 0 |

## Changes v3.8 → v3.9 (prior)

| # | Change |
|---|---|
| 1 | Phases 2-6 expanded to Phase 1's standard |
| 2 | §6.2 replaced — zero category overlap across domains (disjoint vocabularies confirmed). New proof: per-domain V through one function |
| 3 | Factor vectors: embedded on Decision (matching live writer). D4 updated. Zero FactorVector nodes in AGE. |
| 4 | write_outcome() confirmed: sets d.status. Fixture 8 added (migrated-pending→verified lifecycle) |
| 5 | Dual-write spec restored: cycle=one read comparison, discrepancy=semantic equality, failure policy, sampling at scale |
| 6 | V baselines: >= with delta reconciliation, not hard equality |
| 7 | Rollback per step in every phase |
| 8 | Misplaced Phase 2 gates moved to Phase 3 |
| 9 | DataOps Rule #29 and bundle restore as explicit Phase 4 pre-tasks |
| 10 | Cold-start evaluation has comparison baseline (AGE centroids vs SQLite) |
| 11 | Phase 6 queries restored and corrected for disjoint vocabularies |
| 12 | V parity test: SOC runtime V vs adapter V |

---

## Verified facts

### AGE graph (July 19-20, 2026)

**SOC:** 6,253 Decisions. V_soc = **4,899** (3,749 correct + 1,150 incorrect).
`"incorrect"` = overridden per JM §4.2. Forward-write: NO domain set. Must fix.
Scorer: InMemoryGraphStore + file checkpoint (does NOT read L5 from AGE).

**Stale nodes to delete (4,871):**

| Label | Count | Evidence |
|---|---|---|
| Outcome | 1,015 | 100% orphaned, SDK domains |
| EvidenceReceipt | 216 | 100% orphaned |
| CentroidCheckpoint | 1,015 | 100% orphaned |
| DecisionDistanceLog | 2,139 | 100% orphaned |
| DecisionEntityLink | 216 | 100% orphaned |
| EvolutionEvent | 142 | 0 edges, 0 Decision overlap |
| L5Centroid | 17 | Wrong: Trading=4 vs 0 in SQLite |
| L5DKWeight | 4 | Wrong: Trading claims 280 decisions |
| L5ConservationState | 5 | Wrong: Trading V=351 vs actual 150 |
| L5DKWeightArchive | 102 | Stale archive of wrong state |

**TRIGGERED_EVOLUTION:** 0 edges globally. Collision is theoretical.
**19 empty vertex labels:** catalog artifacts. No action.

**Live writer behavior (confirmed):**
- Factor vectors: embedded on Decision. Zero FactorVector nodes.
- `write_outcome()`: sets `d.status` to confirmed/overridden, creates Outcome + HAS_OUTCOME.
- `write_decision()`: no centroid update. Centroids from `learn()`/`write_outcome()` only.

**Category vocabularies (confirmed disjoint):**
SOC: cloud_infrastructure, credential_access, data_exfiltration, insider_threat, lateral_movement, malware_execution.
Trading: event_driven, income_strategy, scalp_intraday, trend_following.
Purchasing: beverages, dairy, dry_goods, produce, protein.
DataOps: freshness_violation, pipeline_failure, quality_anomaly, schema_change, transform_drift, volume_anomaly.
S2P: contract_gap, duplicate_risk, format_compliance, price_variance, quantity_mismatch.
**Zero overlap. Cross-domain proofs cannot use raw category equality.**

### SQLite copilots (July 20, 2026)

| Copilot | Total | Verified | Pending | V baseline |
|---|---|---|---|---|
| Trading | 201 | 150 | 51 | 150 |
| Purchasing | 520 | 20 | 500 | 20 |
| DataOps | 620 | 20 | 600 | 20 |
| S2P | 24,032 | 12 | 24,020 | 12 |

All 25,171 pending are real scored work. No ghosts.

### Live bug

`count_verified(store, 'soc')` returns **0**. AGE adapter is edge-based.
SOC has zero HAS_OUTCOME edges. Three V implementations, none correct for SOC.

---

## Design decisions

| # | Decision | Resolution |
|---|---|---|
| 1 | DomainContext | Projection, closed registry |
| 2 | V-transition | Locked predicate, **property-based both branches**, no edge dependency |
| 3 | ShadowDecision | SOC-specific, excluded from V |
| 4 | FactorVector | **Embedded on Decision** (matching live writer; zero nodes in AGE) |
| 5 | Canonical edges | Forward-only. HAS_OUTCOME for audit chain, not V. |
| 6 | SOC compatibility | Permanent projection |
| 7 | DataOps context | Backfill 29 nodes |
| 8 | Decision domain | Backfill 5,114 + fix age_client.py + domain_source tag |
| 9 | Stale cleanup | Delete 4,871 nodes (10 labels) |
| 10 | Phase rollback | Dual-write → read-diff → flip. Revert = un-flip + restore gate. |
| A | Pending policy | A2: migrate all. No behavioral cost. |
| B | Outcome topology | Migration writes Outcome + HAS_OUTCOME + **status on Decision**. count_verified() property-based. |
| C | Scratch promotion | C2: batched direct-write, per-batch transactions, domain-scoped rollback |
| L | L5 state | Delete stale. Cold start. SOC confirmed not affected. |

---

## Do NOT do

- Do not make V depend on HAS_OUTCOME edges. V is property-based (locked D2 predicate).
- Do not omit `status` from migrated Decision nodes. V Branch 1 requires it.
- Do not create FactorVector nodes. Embed on Decision (matching live writer).
- Do not use scratch graph for migration. Direct-write with batched transactions.
- Do not leave stale L5 records (startup_restore loads them uncritically for SDK copilots).
- Do not use `d.category` equality for cross-domain proofs (disjoint vocabularies).
- Do not use hard `V = N` gates. Use `V >= N` with delta reconciliation.
- Do not remove a copilot's write gate without a documented revert path.
- Do not claim "one traversal, one answer." Use "one graph, one query."
- Do not re-derive V in Cypher. Call count_verified().

---

# PHASE 1: Cleanup + Backfill + V Fix (weeks 1-2)

## 1.1 Backup

```powershell
wsl -u root pg_dump -h localhost -p 5433 -U postgres -d soc_copilot \
  -t 'soc_graph."Outcome"' -t 'soc_graph."EvidenceReceipt"' \
  -t 'soc_graph."CentroidCheckpoint"' -t 'soc_graph."DecisionDistanceLog"' \
  -t 'soc_graph."DecisionEntityLink"' -t 'soc_graph."EvolutionEvent"' \
  -t 'soc_graph."L5Centroid"' -t 'soc_graph."L5DKWeight"' \
  -t 'soc_graph."L5ConservationState"' -t 'soc_graph."L5DKWeightArchive"' \
  > /tmp/age_stale_backup.sql
```

**Gate:** Backup > 0 bytes. **Rollback:** Restore from backup.

## 1.2 Delete stale orphan nodes (4,743 nodes, 6 labels)

```sql
LOAD 'age'; SET search_path = ag_catalog, "$user", public;
SELECT * FROM cypher('soc_graph', $$ MATCH (n:Outcome) DETACH DELETE n RETURN count(*) $$) as (c agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:EvidenceReceipt) DETACH DELETE n RETURN count(*) $$) as (c agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:CentroidCheckpoint) DETACH DELETE n RETURN count(*) $$) as (c agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:DecisionDistanceLog) DETACH DELETE n RETURN count(*) $$) as (c agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:DecisionEntityLink) DETACH DELETE n RETURN count(*) $$) as (c agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:EvolutionEvent) DETACH DELETE n RETURN count(*) $$) as (c agtype);
```

**Gate:** All 6 return count=0. **Rollback:** Restore from §1.1 backup.

## 1.3 Delete stale L5 records (128 nodes, 4 labels)

SOC confirmed: does not read L5 at startup. Deletion is inert for SOC.

```sql
SELECT * FROM cypher('soc_graph', $$ MATCH (n:L5Centroid) DETACH DELETE n RETURN count(*) $$) as (c agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:L5DKWeight) DETACH DELETE n RETURN count(*) $$) as (c agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:L5ConservationState) DETACH DELETE n RETURN count(*) $$) as (c agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:L5DKWeightArchive) DETACH DELETE n RETURN count(*) $$) as (c agtype);
```

**Gate:** All 4 return count=0. **Rollback:** Restore from §1.1 backup.

## 1.4 Decision domain backfill (5,114 nodes)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision) WHERE d.domain IS NULL
  SET d.domain = 'soc', d.domain_source = 'backfill'
  RETURN count(*) AS updated
$$) as (updated agtype);
```

**Verify:**
```sql
-- remaining nulls = 0
SELECT * FROM cypher('soc_graph', $$ MATCH (d:Decision) WHERE d.domain IS NULL RETURN count(*) $$) as (c agtype);
-- total_soc = 6,253
SELECT * FROM cypher('soc_graph', $$ MATCH (d:Decision {domain:'soc'}) RETURN count(*) $$) as (c agtype);
-- V_soc = 4,899
SELECT * FROM cypher('soc_graph', $$ MATCH (d:Decision {domain:'soc'}) WHERE d.outcome IS NOT NULL RETURN count(*) $$) as (c agtype);
```

**Gate:** remaining=0, total=6,253, V=4,899.
**Rollback:** `MATCH (d:Decision {domain_source:'backfill'}) REMOVE d.domain, d.domain_source`

## 1.5 SOC forward-write fix

age_client.py L848 CREATE: add `domain: 'soc'`.
L827 SET: add `d.domain = COALESCE(d.domain, 'soc')`.

**Gate:** SOC BE tests pass. New decision has domain='soc'.
**Rollback:** Revert the two-line change.

## 1.6 DataOps domain backfill (29 nodes)

```sql
SELECT * FROM cypher('soc_graph', $$ MATCH (n:DataQualityAlert) SET n.domain = 'dataops' RETURN count(*) $$) as (c agtype);
SELECT * FROM cypher('soc_graph', $$ MATCH (n:PipelineSystem) SET n.domain = 'dataops' RETURN count(*) $$) as (c agtype);
```

**Gate:** Untagged counts = 0. **Rollback:** `REMOVE n.domain`.

## 1.7 PW gate

```powershell
cd "$env:CLAUDE_SOC\frontend"
npx playwright test "tests/e2e" --reporter=list --timeout=60000 --workers=1
```

**Gate:** Failing-spec set identical to baseline.

## 1.8 Diagnostic graph cleanup (55 → 2)

```sql
SELECT name FROM ag_graph WHERE name NOT IN ('soc_graph','protocol_v2_test') ORDER BY name;
-- Drop each after verifying name
SELECT drop_graph('<name>', true);
```

**Gate:** Only soc_graph and protocol_v2_test remain.

## 1.9 D2 — count_verified() (live bug fix)

**Property-based. Both branches. No edge dependency.**

```python
def count_verified(store: GraphStore, domain: str) -> int:
    """V for conservation. Locked predicate. Property-based. No traversal.
    Branch 1: d.status IN ('confirmed','overridden') WHERE d.domain = domain
    Branch 2: d.status IS NULL AND d.outcome IS NOT NULL WHERE d.domain = domain
    Complementary: status IS NOT NULL vs IS NULL. Never both.
    HAS_OUTCOME edges NOT used — they exist for audit chain only."""
```

**Fixtures:**

| # | Fixture | Assert |
|---|---|---|
| 1 | Embedded-only (status NULL, outcome set) | counted once via Branch 2 |
| 2 | Canonical-only (status='confirmed') | counted once via Branch 1 |
| 3 | Both present (status='confirmed', outcome set) | counted once via Branch 1 only |
| 4 | status='pending' with embedded outcome | NOT counted |
| 5 | Overlap metric: V_branch1 + V_branch2 - V | must = 0 |
| 6 | count_verified(store, 'soc') >= 4,899 | live bug fixed |
| 7 | count_verified(store, 'trading') >= 150 | Branch 1 (after Phase 3) |
| 8 | Migrate pending → verify via write_outcome() → V increments by 1 | migrated-then-verified lifecycle |

**Gate:** All 8 pass. count_verified('soc') >= 4,899.
**Rollback:** Revert function.

---

# PHASE 2: Migration Tool Fixes + Conformance (weeks 2-5)

## 2.1 Migration tool: Outcome topology fix

Modify `copilot_sdk/migrate/sqlite_to_age.py`:

**For verified decisions:** Write:
1. Decision node — all properties including `status` from SQLite ('confirmed'/'overridden'),
   `factor_vector` embedded, `migration_source='sqlite'`
2. Outcome node — from outcomes table (actual_action, actual_index, is_correct,
   reward, verified_at, verifier, metadata)
3. HAS_OUTCOME edge — Decision → Outcome

**Critical:** `status` MUST be written onto the Decision node. Without it,
V Branch 1 cannot find migrated decisions (`status IN ('confirmed','overridden')`).

**For pending decisions:** Write:
1. Decision node — all properties including `status='pending'`,
   `factor_vector` embedded, `migration_source='sqlite'`
2. No Outcome node, no HAS_OUTCOME edge

**Additional edges** where SQLite has related data:
- EMITTED_RECEIPT from evidence_receipts
- HAS_CENTROID_CHECKPOINT from centroid_checkpoints

**Tests:** Modify existing 86 migration tests + add:
- Verified decision: Outcome node exists, HAS_OUTCOME edge exists, `status` on Decision
- Pending decision: no Outcome, no edge, `status='pending'`
- `factor_vector` is embedded property, not a separate node
- Output-equivalence: migrate one, write one via live adapter, diff subgraphs

**Gate:** All tests pass. **Rollback:** Revert sqlite_to_age.py.

## 2.2 Migration tool: Batched direct-write (C2)

Replace scratch-graph promotion with direct-write to live graph.

- **Batch size:** 1,000 decisions
- **Transaction:** BEGIN; cypher calls; COMMIT per batch
- **Ordering:** SQLite `rowid` (monotonic — decision_id is not ordered)
- **Checkpoint:** persist `last_migrated_rowid` to file after each batch commit
- **Resume:** read checkpoint, skip rows <= last_migrated_rowid
- **Idempotent:** MATCH by decision_id first, skip if exists
- **Tag:** `migration_source='sqlite'` on all migrated nodes

**Rollback (domain-scoped):**
```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision {domain: $domain, migration_source: 'sqlite'})
  OPTIONAL MATCH (d)-[]->(related)
  DETACH DELETE d, related RETURN count(*)
$$) as (c agtype);
```

**Gate:** Test migration of 5 rows completes with correct counts.
**Rollback:** Revert writer changes.

## 2.3 TRIGGERED_EVOLUTION naming

0 edges globally. Write naming convention for future SDK evolution events.
Not blocking.

## 2.4 Rule #38 factory compliance (after D2)

| Copilot | File:Line | Fix |
|---|---|---|
| Trading | main.py:104 | Route through `create_graph_store(domain='trading')` |
| Purchasing | main.py:128 | Same |
| DataOps | main.py:91 | Same |
| S2P | main.py:89 | Same |

Default `GRAPH_BACKEND=sqlite`. Behavior unchanged.

**Gate:** All 4 copilot BE + PW suites pass.
**Rollback:** Revert each main.py.

## 2.5 AGE conformance (88/88)

```powershell
$env:AGE_INTEGRATION = "1"
$env:AGE_TEST_DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
$env:AGE_TEST_GRAPH = "protocol_v2_test"
cd "$env:CLAUDE_SDK"
python -m pytest tests/graph/test_protocol_v2_conformance.py -v --timeout=120
```

**Gate:** 88/88.

## 2.6 Projection module

```python
PROJECTION_PATTERNS = {
    "domain_context": ProjectionPattern(
        canonical="MATCH (d:Decision)-[:ABOUT]->(ctx:DomainContext {entity_id: $eid})",
        soc="MATCH (d:Decision)-[:DECIDED_ON]->(ctx:Alert {alert_id: $eid})",
    ),
    "outcome": ProjectionPattern(
        canonical="MATCH (d:Decision)-[:HAS_OUTCOME]->(o:Outcome)",
        soc="MATCH (d:Decision) WHERE d.outcome IS NOT NULL "
            "WITH d, d.outcome AS outcome_value, d.correct AS is_correct",
        normalize=normalize_outcome,
    ),
    "factor_vector": ProjectionPattern(
        canonical="MATCH (d:Decision) WITH d, d.factor_vector AS fv_json",
        soc="MATCH (d:Decision) WITH d, d.factor_vector AS fv_json",
        # Identical — factor vectors embedded everywhere.
    ),
    "evidence_receipt": ProjectionPattern(
        canonical="MATCH (d:Decision)-[:EMITTED_RECEIPT]->(r:EvidenceReceipt)",
        soc=None,
    ),
}
```

Requirements: closed registry, scanner (no cross-copilot Cypher outside module),
equivalence test per pattern, DataOps `graph_queries.py` wrapped (15 AGEClient refs).

**Gate:** All tests pass. Scanner clean.
**Rollback:** Revert projection.py + wrappers.

---

# PHASE 3: Trading AGE Migration (weeks 5-6)

## 3.1 Pre-migration

```powershell
Copy-Item "$env:CI_DATA_DIR\trading\trading.db" "$env:CI_DATA_DIR\trading\trading.db.pre-migration"
wsl -u root pg_dump -h localhost -p 5433 -U postgres -d soc_copilot > /tmp/age_pre_trading.sql
```

Verify: count_verified(store, 'soc') >= 4,899. SQLite Trading: total=201, verified=150.

## 3.2 Migration

```powershell
cd "$env:CLAUDE_SDK"
python -m copilot_sdk.migrate sqlite_to_age --domain=trading --all-decisions --batch-size=1000
```

**Verification:**
```sql
-- Total = 201
SELECT * FROM cypher('soc_graph', $$ MATCH (d:Decision {domain:'trading'}) RETURN count(d) $$) as (c agtype);

-- Status distribution matches SQLite
SELECT * FROM cypher('soc_graph', $$ MATCH (d:Decision {domain:'trading'}) RETURN d.status, count(d) $$) as (s agtype, c agtype);
-- confirmed: 75, overridden: 75, pending: 51

-- Verified with audit chain
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision {domain:'trading'})-[:HAS_OUTCOME]->(o:Outcome)
  RETURN count(DISTINCT d), count(o)
$$) as (d agtype, o agtype);
-- 150, 150

-- V through function
count_verified(store, 'trading')  # >= 150
count_verified(store, 'soc')      # >= 4,899

-- Pending have no outcome edges
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision {domain:'trading', status:'pending'})
  OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o)
  WITH d, o WHERE o IS NULL RETURN count(d)
$$) as (c agtype);
-- 51
```

**Gate:** All counts match. **Rollback:** Domain-scoped delete (§2.2).

## 3.3 Output-equivalence test

Migrate one verified decision. Write one equivalent through live adapter.
Diff subgraphs: properties, edges, topology.

**Gate:** Zero diff.

## 3.4 Remove Trading product-write gate

`graph_status.py:243` — remove test-only rejection. Set `GRAPH_BACKEND=age`.

**Gate:** Trading BE tests pass.
**Rollback:** Restore rejection + set `GRAPH_BACKEND=sqlite`.

## 3.5 Dual-write → read-diff → flip

**Dual-write:** Trading writes to both SQLite and AGE. Reads on SQLite.

**Read-diff:**
- **Cycle:** One comparison of ALL decisions (verified + pending) for the domain
  from both stores. At Trading's 201 rows, compare everything.
- **Semantic equality:** Match by decision_id. For each matched pair, compare:
  status, category, confidence, factor_vector presence. For verified decisions
  additionally compare: is_correct, actual_action. Ignore list ordering and
  timestamp precision differences.
- **Discrepancy:** Any field mismatch on any decision, or any decision present in
  one store but not the other. Log decision_id + field + both values.
- **Counter:** N=40 zero-discrepancy cycles. **Any discrepancy resets counter to 0.**
  AGE write failure also resets to 0.
- **Failure policy:** AGE write fails, SQLite succeeds → log, continue, reset counter.
  AGE failure rate > 1%/hour → alert, pause dual-write, investigate.
- **Frequency:** Every 10 minutes (automated) or on-demand.

**Flip:** After N=40, reads move to AGE. SQLite dual-write continues 1 week as backup.

**Gate:** 40 consecutive zero-discrepancy cycles.
**Revert:** Set `GRAPH_READ_SOURCE=sqlite`. Restore write gate from §3.4.

## 3.6 Trading PW

```powershell
cd "$env:CLAUDE_SDK\e2e"
npx playwright test trading/ --reporter=list --retries=0 --workers=1
```

**Gate:** 246/0. Measure AGE latency: if any endpoint > 2× SQLite baseline, investigate.

## 3.7 Cold-start evaluation

Trading scorer starts cold (no L5 state).

**Deterministic gate (before any new scoring):** Immediately after migration
and flip, re-derive centroids from the 150 migrated verified decisions using
the scorer's `learn()` path. Compare against SQLite scorer's centroids for
the same 150 decisions. Same inputs, same algorithm.

**Tolerance:** Cosine similarity >= 0.95 per category centroid. Any category
below threshold → investigate migration fidelity (ordering, precision, missing field).

**Behavioral observation (after gate passes):** Monitor first 50 live-scored
decisions. Compare AGE-derived centroids against the deterministic baseline
as they evolve. This is an observation, not a gate — centroids move as new
decisions arrive.

**Verdict:** Deterministic gate passes → L1 (cold start) confirmed for
remaining copilots. Gate fails → investigate before Phase 4.

## 3.8 Cross-copilot proof (Trading ↔ SOC)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision) WHERE d.domain IN ['soc','trading']
  RETURN d.domain, count(d)
$$) as (domain agtype, c agtype);

SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision {domain:'trading'})-[:HAS_OUTCOME]->(o:Outcome)
  RETURN d.decision_id, d.status, o.is_correct LIMIT 5
$$) as (did agtype, s agtype, c agtype);
```

**Gate:** Both queries return expected rows. V_soc >= 4,899.

---

# PHASE 4: Purchasing + DataOps + S2P (weeks 6-8)

## 4.0 Pre-tasks

### 4.0.1 DataOps Rule #29

Wrap `graph_queries.py` (15 AGEClient references) through projection module.
Must complete BEFORE DataOps migration.

**Gate:** DataOps BE tests pass. Scanner clean.
**Rollback:** Revert graph_queries.py.

### 4.0.2 DataOps demo bundle restore

Update `bundle.py` for AGE backend support.

**Gate:** `python demo.py --preseed` completes with `GRAPH_BACKEND=age`.
**Rollback:** Revert bundle.py.

## 4.1 Purchasing (520 total, 20 verified, 500 pending)

```powershell
Copy-Item "$env:CI_DATA_DIR\purchasing\purchasing.db" "$env:CI_DATA_DIR\purchasing\purchasing.db.pre-migration"
python -m copilot_sdk.migrate sqlite_to_age --domain=purchasing --all-decisions --batch-size=1000
```

**Verify:** total=520, status distribution matches SQLite, V_purchasing >= 20.
Remove `graph_status.py:298`. Dual-write (N=40). Flip. PW: 235/0/1.

**V regression:** soc >= 4,899, trading >= 150, purchasing >= 20.
**Rollback:** Domain-scoped delete + restore gate + un-flip.

## 4.2 DataOps (620 total, 20 verified, 600 pending)

**Pre-req:** §4.0.1 and §4.0.2 complete.

```powershell
Copy-Item "$env:CI_DATA_DIR\dataops\dataops.db" "$env:CI_DATA_DIR\dataops\dataops.db.pre-migration"
python -m copilot_sdk.migrate sqlite_to_age --domain=dataops --all-decisions --batch-size=1000
```

Remove `graph_status.py:243` (+ `live_age_test` gate). Dual-write. Flip.
PW: 133/0/1.

**V regression:** all prior domains unchanged.
**Rollback:** Same pattern.

## 4.3 S2P (24,032 total, 12 verified, 24,020 pending)

```powershell
Copy-Item "$env:CI_DATA_DIR\s2p\s2p.db" "$env:CI_DATA_DIR\s2p\s2p.db.pre-migration"
wsl -u root pg_dump -h localhost -p 5433 -U postgres -d soc_copilot > /tmp/age_pre_s2p.sql
python -m copilot_sdk.migrate sqlite_to_age --domain=s2p --all-decisions --batch-size=1000
```

**Scale:** ~24,032 Decision nodes (factor_vector embedded), 12 Outcome + edges,
12 checkpoints, 4 receipts, 353 entity edges. ~25 batches. Minutes.

**G5 prerequisite:** `get_decisions` defaults to 400 rows. S2P has 24,032.
Add pagination (cursor or offset) to `get_decisions` and any method that
enumerates decisions before S2P migration. Without this, read-diff silently
compares only the first 400 and the flip gate is meaningless.
**Gate:** `get_decisions(domain='s2p')` returns all 24,032 (paginated).

**Read-diff at scale:** Each cycle samples 1,000 random decisions from ALL
statuses (verified + pending), comparing status, category, confidence,
factor_vector presence. For verified in the sample, also compare is_correct,
actual_action. Full diff once at N=40 before flip.
**Critical:** S2P has 12 verified and 24,020 pending. A verified-only diff
covers 0.05% of the data. Sampling must draw from the full population.

**Verify:** total=24,032, V_s2p >= 12. PW: 194/0.
**V regression:** all 5 domains.
**Rollback:** Domain-scoped delete + pg_dump restore if needed.

## 4.4 Demo.py integration

```powershell
cd "$env:CLAUDE_SDK"
python demo.py --stop
$env:GRAPH_BACKEND = "age"
python demo.py --preseed --no-browser
```

**Full PW gate:**
```powershell
npx playwright test trading/ --reporter=list --retries=0 --workers=1
npx playwright test purchasing/ --reporter=list --retries=0
npx playwright test --config=s2p/playwright.config.ts s2p/ --reporter=list --retries=0 --workers=1
npx playwright test dataops/ --reporter=list --retries=0 --workers=1

cd "$env:CLAUDE_SOC\frontend"
npx playwright test "tests/e2e" --reporter=list --timeout=60000 --workers=1
```

**V regression:**
```python
for domain in ["soc", "trading", "purchasing", "dataops", "s2p"]:
    v = count_verified(store, domain)
    print(f"{domain}: V={v}")
# soc >= 4899, trading >= 150, purchasing >= 20, dataops >= 20, s2p >= 12
```

---

# PHASE 5: Skipped (projection is permanent)

---

# PHASE 6: Cross-Copilot Proof (weeks 8-9)

**Framing:** ~96% SOC by count. Claims are structural, not volumetric.
"All five copilots on one graph" means **decision records and audit chains**.
SOC scorer state lives in InMemoryGraphStore + file checkpoints, not AGE.
State this explicitly in claim wording.

## 6.1 Multi-domain visibility

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision) RETURN d.domain, count(d) ORDER BY count(d) DESC
$$) as (domain agtype, c agtype);
```

**Gate:** Returns rows for all 5 domains.

## 6.2 Per-domain V through one function

```python
for domain in ["soc", "s2p", "trading", "purchasing", "dataops"]:
    v = count_verified(store, domain)
    print(f"{domain}: V={v}")
# One function, one predicate, five domains, correct for each.
```

**Gate:** soc >= 4,899; trading >= 150; purchasing >= 20; dataops >= 20; s2p >= 12.

(Replaces former cross-domain category overlap — disjoint vocabularies make
raw category join return zero rows.)

## 6.3 Multi-domain status distribution

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)
  RETURN d.domain, d.status, count(d)
  ORDER BY d.domain, d.status
$$) as (domain agtype, status agtype, c agtype);
```

**Gate:** All 5 domains × all status values. One query, one graph.

## 6.4 SDK audit chain traversal (real edges)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision {domain:'trading'})-[:HAS_OUTCOME]->(o:Outcome)
  RETURN d.decision_id, d.status, o.actual_action, o.is_correct LIMIT 5
$$) as (did agtype, s agtype, action agtype, correct agtype);
```

S2P evidence receipts (if any):
```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision {domain:'s2p'})-[:EMITTED_RECEIPT]->(r:EvidenceReceipt)
  RETURN d.decision_id, r.chain_index LIMIT 5
$$) as (did agtype, chain agtype);
```

**Gate:** Both return rows.

## 6.5 SOC audit via projection

```python
results = projection.query("outcome", domain="soc", limit=5)
```

Same function, different domain — projection handles SOC's embedded outcomes.

## 6.6 Cross-domain shared entity

Zero DomainContext nodes. Disjoint category vocabularies. No natural shared entity.

**Honest claim:** "One graph, one query" proven by §6.1-6.4. Cross-domain edge
traversal requires TransferPattern nodes — explicitly stated as future work.

## 6.7 Claim wording

- "one traversal, one answer" → "one graph, one query"
- Decision records and audit chains are shared. Scorer runtime state is per-copilot.
- Structural proof: §6.1 (visibility), §6.2 (V through one function),
  §6.4 (audit traversal). All hold at any N.

```
$ python demo.py --status
  SOC        [shared judgment graph]  6,253+ decisions  AGE
  Trading    [shared judgment graph]    201  decisions  AGE
  Purchasing [shared judgment graph]    520  decisions  AGE
  DataOps    [shared judgment graph]    620  decisions  AGE
  S2P        [shared judgment graph] 24,032  decisions  AGE
```

## 6.8 V parity test

SOC computes V via direct queries. Adapter computes V via count_verified().

```python
soc_runtime_v = soc_learning_health.get_verified_count()
adapter_v = count_verified(store, 'soc')
assert soc_runtime_v == adapter_v
```

**Gate:** Parity holds.

---

# Definition of done

| Item | Gate |
|---|---|
| Backup | pg_dump non-empty |
| Stale deletion | 10 label counts = 0 |
| Domain backfill | domain IS NULL = 0; total_soc = 6,253; V_soc >= 4,899 |
| SOC forward-write | domain='soc' on CREATE; BE tests pass |
| D2/V fix | 8 fixtures; count_verified('soc') >= 4,899 |
| Migration tool: Outcome topology | Outcome + HAS_OUTCOME + status; equiv test |
| Migration tool: Batched writer | Per-batch txn; checkpoint/resume; idempotent |
| Rule #38 | All 4 copilots via factory; all suites pass |
| AGE conformance | 88/88 |
| Projection | Registry; scanner; equivalence; DataOps wrapped |
| Trading | 201 migrated; V >= 150; 246 PW; cold-start eval; cross-copilot |
| Purchasing | 520 migrated; V >= 20; 235 PW |
| DataOps | 620 migrated; V >= 20; 133 PW; Rule #29; bundle restore |
| S2P | 24,032 migrated; V >= 12; 194 PW |
| Demo.py | All copilots; shared graph; reset per domain |
| Phase 6 | All 8 subsections; V parity; claim wording |

---

# Execution sequence

| Week | Work | Gate |
|---|---|---|
| **1-2** | Phase 1 | Counts=0; V_soc >= 4,899 direct+function; PW diff empty |
| **2-5** | Phase 2 | 88/88; migration tests; projection scanner; equiv test |
| **5-6** | Phase 3: Trading | V >= 150; 246 PW; V_soc >= 4,899; cross-copilot; cold-start |
| **6-8** | Phase 4: Purchasing → DataOps → S2P | All V baselines; all PW; demo.py |
| **8-9** | Phase 6 | All 8 subsections; parity; claim wording |

**~9 weeks.** Phase 5 skipped.

---

*AGE Shared Graph Migration v3.10 · July 20, 2026*
*All phases at runbook standard. Read-diff covers all decisions, not just verified.*
*G5 pagination before S2P. Cold-start gate: cosine >= 0.95, deterministic.*
*V is property-based. Edges for audit chain only. Status written on Decision.*
*A2: all decisions. C2: batched direct-write. Factor vectors embedded.*
*V baselines: >= with delta reconciliation.*
