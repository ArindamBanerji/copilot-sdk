# AGE Shared Graph Migration — Complete Execution Plan

**Date:** July 19, 2026 · **Version:** v3.2
**Authority:** judgment_memory_v2_7.md
**History:** v1 → review → v2 → close review → v3 → executability pass → v3.1 → final review → v3.2
**Scope:** Current state to "every §2 claim demonstrated"

## Changes v3.1 → v3.2

| # | Finding | v3.1 | v3.2 |
|---|---|---|---|
| B1 | SOC Decisions have no `domain`; 5 of 6 proof queries filter on it | Not addressed | PF-6 + Decision domain backfill in week 1 (same D7 logic: additive, invisible, checkable) |
| B2 | Phase 6 conservation query re-derives V a third way | `count(d) AS V` via HAS_OUTCOME | Route through `count_verified()` — never re-derive V in Cypher |
| B3 | "Traversal proofs" are property joins, not traversals | Cartesian product filtered by category | Phase 6 retitled "Cross-Copilot Proof"; honest about joins vs edges; adds one genuine traversal via shared DomainContext |
| I1 | Trading PW under AGE with 4 workers | No `--workers` flag | `--workers=1` for Trading; measure AGE-backed cache miss first |
| I2 | "No inter-phase gate reviews" self-contradicted | Stated twice | Reworded: design decisions don't need re-litigation; phase transitions have execution gates |
| I3 | Projection registry: outcome_traversal assumes backfill complete; factor_vector returns different shapes | Two Cypher strings | Invariant test for outcome; normalize function per pattern for factor_vector |
| S1 | `--use-scratch-graph` unexplained | Appears without context | One sentence: what it does, how scratch promotes |
| S2 | Phase 6 query syntax unverified against AGE | CASE WHEN / is_correct integer assumption | Run proof queries against real data in PF phase, not week 9 |
| S3 | DataOps Rule #29 (graph_queries.py:43) left as TODO | "resolve or document" | Decision made: wrap in projection module |

---

## Current state

| Copilot | Store | Decisions | AGE infrastructure |
|---|---|---|---|
| SOC | AGE ✅ | ~6,253 | AGEClient direct, no GraphStore protocol |
| S2P | SQLite | 12 verified | Factory exists, AGE writes permitted in product mode |
| Trading | SQLite | 425 verified | Factory exists, test-only hard gate |
| Purchasing | SQLite | ? | Factory exists, test-only hard gate |
| DataOps | SQLite | ? | Factory exists, live-test gate + demo restore issue |

**Target:** All 5 copilots on one AGE graph. Every outreach claim provable by query.

---

## Three enabling facts

1. **GAE attention operates on protocol data, not graph labels.** `SchemaContract.node_type`
   is opaque. Projection is architecturally viable.

2. **SOC has zero wildcard Cypher traversals.** All edges fully typed. Adding new edge types
   is invisible to SOC's existing reads.

3. **TRIGGERED_EVOLUTION is the exception.** SOC queries it (`age_client.py:621, :972, :1012`)
   and uses a different topology: `(Alert)-[:TRIGGERED_EVOLUTION]->(Entity)` vs §4's
   `(Decision)-[:TRIGGERED_EVOLUTION]->(EvolutionEvent)`. Vocabulary collision. Excluded from
   all backfill. Separate analysis required.

---

## Seven design decisions (settled)

| # | Decision | Final form |
|---|---|---|
| 1 | DomainContext | Projection with owned module, closed `PROJECTION_PATTERNS` registry, equivalence tests, scanner |
| 2 | V-transition | Single per-decision predicate (`status IS NOT NULL` / `IS NULL` — complementary by construction). Mixed-domain fixture. Overlap metric. Lands before Rule #38 |
| 3 | ShadowDecision | SOC-specific, excluded from V (unchanged) |
| 4 | FactorVector | Forward canonical for SDK, projection for SOC. Named costs: similarity + attention parse |
| 5 | Canonical edges | Backfill 3 types (HAS_OUTCOME, EMITTED_RECEIPT, HAS_CENTROID_CHECKPOINT) tagged `source='backfill'`, MERGE/guard, cardinality-gated. TRIGGERED_EVOLUTION **DEFERRED** to separate analysis |
| 6 | SOC compatibility | Permanent projection infrastructure (Phase 5 will not happen) |
| 7 | DataOps context | Backfill `domain='dataops'` on 29 nodes + forward tag + registry test |
| NEW | Decision domain | Backfill `domain='soc'` on ~6,253 Decision nodes (week 1, before any migration) |
| NEW | Phase 3 rollback | Dual-write → read-diff (N=40, AGE failure resets counter) → flip |
| NEW | Sequencing | Edge backfill + domain backfill week 1. D2 before Rule #38. TRIGGERED_EVOLUTION separate |

---

## Do NOT do

- Do not backfill TRIGGERED_EVOLUTION with the other three. Vocabulary collision (different node types).
- Do not use `CREATE` without the `OPTIONAL MATCH … WHERE r IS NULL` guard. `CREATE` duplicates.
- Do not roll back by edge type alone. Delete by `{source: 'backfill'}` tag.
- Do not implement V per copilot. One function, one location.
- Do not re-derive V in Cypher for demos or proofs. Call `count_verified()`.
- Do not start Rule #38 before D2 is green. Factory can create the mixed domain.
- Do not compare PW results by count. Compare failing-spec sets.
- Do not claim "one traversal, one answer" externally. Use "one graph, one query."
- Do not run Trading PW against AGE with 4 workers without measuring cache-miss latency first.
- Do not backfill `domain='soc'` after any SDK copilot has migrated — that risks mislabeling.
- Do not assume `is_correct` is an integer in AGE. Verify the stored type before writing proof queries.

---

# PHASE 1: Pre-flight + Backfill + V Function (weeks 1-2)

## 1.1 Pre-flight data checks — run FIRST

```sql
LOAD 'age';
SET search_path = ag_catalog, "$user", public;
```

### PF-1 — What does embedded outcome contain? (blocks V predicate)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)
  RETURN d.outcome AS outcome_value, count(*) AS n
  ORDER BY n DESC
$$) as (outcome_value agtype, n agtype);
```

If all values are terminal verification results → predicate is `d.outcome IS NOT NULL`.
If any sentinel (`''`, `pending`, score-time placeholder) → narrow to explicit allow-list.

### PF-2 — Is `correct` a second verification signal? (blocks V predicate)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)
  WHERE d.outcome IS NULL AND d.correct IS NOT NULL
  RETURN count(*) AS orphaned_correct
$$) as (orphaned_correct agtype);
```

Result 0 → predicate stands. Result > 0 → predicate becomes
`(d.outcome IS NOT NULL OR d.correct IS NOT NULL)`.

### PF-3 — Do any Decisions carry `status`? (sizes mixed-domain risk)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)
  RETURN d.status AS status_value, count(*) AS n
$$) as (status_value agtype, n agtype);
```

Expect all-null. Non-null → mixed domain already exists → D2 priority rises.

### PF-4 — Cardinality + orphan gates (blocks edge backfill)

```sql
-- (a) duplicate Outcomes per decision — MUST return zero rows
SELECT * FROM cypher('soc_graph', $$
  MATCH (o:Outcome)
  WITH o.decision_id AS did, count(*) AS c
  WHERE c > 1
  RETURN did, c
$$) as (did agtype, c agtype);

-- (b) duplicate EvidenceReceipts per decision — MUST return zero rows
SELECT * FROM cypher('soc_graph', $$
  MATCH (r:EvidenceReceipt)
  WITH r.decision_id AS did, count(*) AS c
  WHERE c > 1
  RETURN did, c
$$) as (did agtype, c agtype);

-- (c) duplicate CentroidCheckpoints per decision — MUST return zero rows
SELECT * FROM cypher('soc_graph', $$
  MATCH (c:CentroidCheckpoint)
  WITH c.decision_id AS did, count(*) AS cnt
  WHERE cnt > 1
  RETURN did, cnt
$$) as (did agtype, cnt agtype);

-- (d) orphan Outcomes (no matching Decision) — record count
SELECT * FROM cypher('soc_graph', $$
  MATCH (o:Outcome)
  OPTIONAL MATCH (d:Decision) WHERE d.decision_id = o.decision_id
  WITH o, d WHERE d IS NULL
  RETURN count(*) AS orphans
$$) as (orphans agtype);

-- (e) CentroidCheckpoints with no decision_id — record count
SELECT * FROM cypher('soc_graph', $$
  MATCH (c:CentroidCheckpoint) WHERE c.decision_id IS NULL
  RETURN count(*) AS no_did
$$) as (no_did agtype);
```

**Gates:** (a), (b), (c) must return zero rows. (d) and (e) adjust dry-run expected counts.
Orphan Outcomes are excluded from backfill (the OPTIONAL MATCH form handles this naturally).

### PF-5 — PW baseline as a SET

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\frontend"
npx playwright test "tests/e2e" --reporter=list --timeout=60000 --workers=1 2>&1 | Select-String "^\s+\d+.*FAIL|failed" > C:\temp\soc_baseline_fails.txt
npx playwright test "tests/e2e" --reporter=list --timeout=60000 --workers=1 2>&1 | Select-String "^\s+-\s+" > C:\temp\soc_baseline_skips.txt
```

### PF-6 — Decisions without `domain` (blocks every cross-copilot query) — NEW

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision) WHERE d.domain IS NULL
  RETURN count(*) AS no_domain
$$) as (no_domain agtype);
```

Expected: ~6,253 (all SOC decisions). This is the gap that silently breaks every
Phase 3+ proof query. Fixed by the Decision domain backfill (§1.3).

### PF-7 — Verify `is_correct` stored type (blocks Phase 6 proof queries)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (o:Outcome)
  RETURN o.is_correct AS val, count(*) AS n
  ORDER BY n DESC
$$) as (val agtype, n agtype);
```

If values are `true`/`false` (boolean), Phase 6 queries filtering `{is_correct: 1}` will
match nothing. Know the type now, write the proofs correctly.

## 1.2 Edge backfill (3 types, ~2,246 edges)

**Precondition:** PF-4 (a)(b)(c) zero rows; PF-5 baseline captured.

### Idempotent write (portable AGE)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision), (o:Outcome)
  WHERE d.decision_id = o.decision_id
  OPTIONAL MATCH (d)-[r:HAS_OUTCOME]->(o)
  WITH d, o, r WHERE r IS NULL
  CREATE (d)-[:HAS_OUTCOME {source: 'backfill', backfilled_at: <CURRENT_EPOCH>}]->(o)
  RETURN count(*) AS created
$$) as (created agtype);
```

Replace `<CURRENT_EPOCH>` with actual epoch at execution time.

### Dry-run

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision), (o:Outcome)
  WHERE d.decision_id = o.decision_id
  OPTIONAL MATCH (d)-[r:HAS_OUTCOME]->(o)
  WITH d, o, r WHERE r IS NULL
  RETURN count(*) AS would_create
$$) as (would_create agtype);
```

**Gate:** `would_create ≈ Outcome count − orphan count` (from PF-4d).

### Apply (one type at a time)

| Edge | Target label | Expected |
|---|---|---|
| HAS_OUTCOME | Outcome | ~1,015 minus orphans |
| EMITTED_RECEIPT | EvidenceReceipt | ~216 |
| HAS_CENTROID_CHECKPOINT | CentroidCheckpoint | ~1,015 minus null-`decision_id` (PF-4e) |

### Verification (per edge type)

```sql
-- (a) edge count
SELECT * FROM cypher('soc_graph', $$
  MATCH ()-[r:HAS_OUTCOME]->() RETURN count(r) AS edges
$$) as (edges agtype);

-- (b) all tagged
SELECT * FROM cypher('soc_graph', $$
  MATCH ()-[r:HAS_OUTCOME]->() WHERE r.source IS NULL
  RETURN count(r) AS untagged
$$) as (untagged agtype);

-- (c) no duplicates per decision
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)-[:HAS_OUTCOME]->(o:Outcome)
  WITH d.decision_id AS did, count(*) AS c WHERE c > 1
  RETURN did, c
$$) as (did agtype, c agtype);

-- (d) traversal works
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)-[:HAS_OUTCOME]->(o:Outcome)
  RETURN d.decision_id, o.is_correct LIMIT 5
$$) as (decision_id agtype, is_correct agtype);

-- (e) INVARIANT: backfilled edges == matched pairs (detects partial backfill)
-- Compare (a) against the join count:
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision), (o:Outcome)
  WHERE d.decision_id = o.decision_id
  RETURN count(*) AS pairs
$$) as (pairs agtype);
-- edges (a) must equal pairs (e). If not, backfill is incomplete.
```

**Gates:** (a) matches dry-run · (b) untagged == 0 · (c) zero rows · (d) returns rows ·
(a) == (e).

### PW gate (set comparison)

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\frontend"
npx playwright test "tests/e2e" --reporter=list --timeout=60000 --workers=1 2>&1 | Select-String "^\s+\d+.*FAIL|failed" > C:\temp\soc_after_fails.txt
Compare-Object (Get-Content C:\temp\soc_baseline_fails.txt) (Get-Content C:\temp\soc_after_fails.txt)
```

**Gate:** diff is empty. New failure → rollback → analyze.

### Rollback (by tag only)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH ()-[r:HAS_OUTCOME {source: 'backfill'}]->()
  DELETE r RETURN count(*) AS deleted
$$) as (deleted agtype);
```

## 1.3 Decision domain backfill (~6,253 nodes) — NEW

**Why this is critical:** Every cross-copilot query in Phases 3-6 filters on
`d.domain`. SOC's Decisions have no `domain` property. Without this backfill,
the Phase 3 cross-copilot proof returns zero rows, and someone under deadline
pressure "fixes" it with an unplanned mutation.

**Why week 1:** At this point every Decision in the graph is SOC's.
`WHERE d.domain IS NULL SET d.domain = 'soc'` is provably correct. Run it
in week 7 after S2P has migrated and you risk mislabeling S2P decisions.

**Same safety argument as D7 (DataOps 29 nodes):** Additive property, no label
or edge change, invisible to SOC's typed reads (SOC never filters by `domain`).

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision) WHERE d.domain IS NULL
  SET d.domain = 'soc'
  RETURN count(*) AS updated
$$) as (updated agtype);
```

**Verify:**
```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision) WHERE d.domain IS NULL
  RETURN count(*) AS remaining
$$) as (remaining agtype);
```

Must return 0. **Rollback:** `MATCH (d:Decision {domain:'soc'}) REMOVE d.domain`.

## 1.4 DataOps domain backfill (29 nodes)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (n:DataQualityAlert) SET n.domain = 'dataops' RETURN count(*) AS updated
$$) as (updated agtype);

SELECT * FROM cypher('soc_graph', $$
  MATCH (n:PipelineSystem) SET n.domain = 'dataops' RETURN count(*) AS updated
$$) as (updated agtype);
```

**Verify:**
```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (n:DataQualityAlert) WHERE n.domain IS NULL RETURN count(*) AS untagged
$$) as (untagged agtype);

SELECT * FROM cypher('soc_graph', $$
  MATCH (n:PipelineSystem) WHERE n.domain IS NULL RETURN count(*) AS untagged
$$) as (untagged agtype);
```

## 1.5 D2 — V function

### Predicate (locked after PF-1/PF-2)

```
V = count(DISTINCT d.decision_id) WHERE
      (d.status IS NOT NULL AND d.status IN ('confirmed','overridden'))
   OR (d.status IS NULL     AND <PF1_VERIFIED_PREDICATE>)
```

Complementary predicates — "never both" by construction.

### Implementation

```python
# copilot_sdk/graph/conservation.py — THE V FUNCTION
# One implementation. No copilot reimplements. No Cypher re-derivation.
def count_verified(store: GraphStore, domain: str) -> int:
    """V for conservation (rule #37). Per-decision predicate.
    Legacy branch (status IS NULL) for pre-migration SOC decisions."""
```

**All demos, proofs, and Phase 6 queries call this function. Never re-derive V.**

### Fixtures

| # | Fixture | Assert |
|---|---|---|
| 1 | Three shapes: embedded-only, canonical-only, both | each counts exactly once |
| 2 | Mixed domain: status-bearing + status-less in one domain | V == 2 |
| 3 | Overlap metric: log V_embedded + V_canonical − V_actual | nonzero → alarm |
| 4 | Contradictory: `status='pending'` with embedded outcome | NOT counted |

---

# PHASE 2: Conformance + Factory + Projection (weeks 2-5)

**Precondition:** Phase 1 complete (backfills verified, D2 green).
**Design decisions settled. Phase transitions have execution gates.**

## 2.1 TRIGGERED_EVOLUTION analysis (weeks 2-3)

Must answer:

1. **What consumes it?** Trace `age_client.py:621, :972, :1012` through SOC router/service to frontend.
2. **What do PW tests assert?** Grep SOC PW specs for evolution/triggered/variant.
3. **The vocabulary collision:** SOC uses `(Alert)-[:TRIGGERED_EVOLUTION]->(Entity)`.
   Canonical says `(Decision)-[:TRIGGERED_EVOLUTION]->(EvolutionEvent)`.
   Same edge label, different source AND target node types.
4. **Resolution options:**
   - (a) SDK copilots use a different edge label (e.g., `EVOLVED_FROM`)
   - (b) Both topologies coexist; cross-copilot queries filter by source/target type
   - (c) Rename SOC's usage (risky — touches live reads)

**Output:** Written decision document. Not a backfill.

## 2.2 Rule #38 factory compliance (after D2)

All 4 SDK copilot `main.py` default paths route through `create_graph_store()`.
Factory returns SQLiteGraphStore when `GRAPH_BACKEND=sqlite` — identical behavior.

**Gate:** All backend + PW suites pass.

## 2.3 AGE conformance tests (weeks 3-5)

88 test functions in `tests/graph/test_protocol_v2_conformance.py`.

```powershell
$env:AGE_INTEGRATION = "1"
$env:AGE_TEST_DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
$env:AGE_TEST_GRAPH = "protocol_v2_test"

cd "$env:CLAUDE_SDK"
python -m pytest tests/graph/test_protocol_v2_conformance.py -v --timeout=120
```

**Gate:** 88/88 pass.

## 2.4 Projection module (weeks 2-4)

```
copilot_sdk/graph/projection.py
```

### Closed registry

```python
PROJECTION_PATTERNS: dict[str, ProjectionPattern] = {
    "domain_context": ProjectionPattern(
        canonical="MATCH (d:Decision)-[:ABOUT]->(ctx:DomainContext {entity_id: $eid})",
        soc="MATCH (d:Decision)-[:DECIDED_ON]->(ctx:Alert {alert_id: $eid})",
    ),
    "outcome_traversal": ProjectionPattern(
        canonical="MATCH (d:Decision)-[:HAS_OUTCOME]->(o:Outcome)",
        soc="MATCH (d:Decision)-[:HAS_OUTCOME]->(o:Outcome)",
        invariant="count(HAS_OUTCOME edges) == count(decision_id-matched pairs)",
        # Both forms use the same edge AFTER backfill. The invariant test detects
        # partial or rolled-back backfill — do not silently return incomplete results.
    ),
    "factor_vector": ProjectionPattern(
        canonical="MATCH (d:Decision)-[:HAS_FACTOR_VECTOR]->(fv:FactorVector)",
        soc="MATCH (d:Decision) WITH d, d.factor_vector AS fv_json",
        normalize=normalize_factor_vector,
        # Returns different shapes: canonical yields a FactorVector node,
        # SOC yields a JSON blob. Equivalence test compares through normalize().
    ),
}
```

### Requirements

1. **One function per pattern.** No raw cross-copilot Cypher outside this module.
2. **Scanner:** Test greps codebase for cross-copilot Cypher outside `projection.py`.
3. **Equivalence test per pattern:** Through `normalize()` where shapes differ.
4. **Invariant test for outcome_traversal:** Detects incomplete backfill.
5. **Overhead measurement:** Measure highest-frequency pattern on live graph. Report.
6. **DataOps graph_queries.py:43** (Rule #29 violation): Wrap the direct AGEClient
   import in the projection module. DataOps cross-graph queries route through
   `projection.py` like every other copilot. One-line change, not a TODO.

---

# PHASE 3: S2P AGE Migration (weeks 5-7)

**Precondition:** Phase 2 complete (88/88 conformance, Rule #38, projection module).

## 3.1 S2P migration

The migration CLI uses `--use-scratch-graph` to write to a temporary graph first,
verify against the source SQLite, then atomically promote to the live graph. This
prevents a failed migration from corrupting the production graph.

```powershell
# Dry-run
cd "$env:CLAUDE_SDK"
python -m copilot_sdk.migrate sqlite_to_age --domain=s2p --source=<S2P_SQLITE_PATH> --age-dsn="host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres" --graph-name=soc_graph --dry-run

# Apply (scratch graph → verify → promote)
python -m copilot_sdk.migrate sqlite_to_age --domain=s2p --source=<S2P_SQLITE_PATH> --age-dsn="host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres" --graph-name=soc_graph --use-scratch-graph
```

## 3.2 Dual-write → read-diff → flip

1. **Dual-write:** S2P writes to BOTH SQLite and AGE. Reads stay on SQLite.
2. **Read-diff:** Compare SQLite vs AGE reads. N=40 zero-discrepancy cycles → flip.
3. **Flip:** Reads move to AGE. SQLite retained as cold backup.

**Failure policy:**
- AGE write fails, SQLite succeeds → log, continue, **reset diff counter to zero**.
- AGE failure rate > 1% over 1 hour → operational alert.

## 3.3 S2P verification

```powershell
cd "$env:CLAUDE_S2P\backend"
python -m pytest tests/ -q --timeout=120  # expect 1627+

cd "$env:CLAUDE_SDK\e2e"
npx playwright test --config=s2p/playwright.config.ts s2p/ --reporter=list --retries=0 --workers=1
# expect 194/0
```

## 3.4 Cross-copilot query proof (S2P ↔ SOC)

This is the first real test of the shared graph. After the Decision domain backfill
(§1.3), SOC decisions have `domain='soc'` and S2P decisions have `domain='s2p'`.

```sql
-- Both domains visible in one query
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)
  WHERE d.domain IN ['soc', 's2p']
  RETURN d.domain, count(*) AS decisions
$$) as (domain agtype, decisions agtype);
```

**Gate:** Returns rows for both domains.

For a genuine edge traversal across domains (not a property join), write a shared
`DomainContext` node that both domains reference:

```sql
-- If a supplier entity appears in both domains' decision context:
SELECT * FROM cypher('soc_graph', $$
  MATCH (d1:Decision {domain:'s2p'})-[:ABOUT]->(ctx:DomainContext)<-[:DECIDED_ON]-(d2:Decision {domain:'soc'})
  RETURN d1.decision_id AS s2p, d2.decision_id AS soc, ctx.entity_id
  LIMIT 5
$$) as (s2p agtype, soc agtype, entity agtype);
```

If no shared entity exists yet (likely at 12 S2P decisions), this is deferred to
Phase 6 when more data exists. The domain visibility query is the Phase 3 gate.

---

# PHASE 4: Trading + Purchasing + DataOps (weeks 7-8)

**Precondition:** Phase 3 stable.
**Pattern:** Same as Phase 3 — migrate, dual-write (N=40), flip.

## 4.1 Remove product-write hard gates

```
apps/trading/backend/app/graph_status.py:241-244       # test-only rejection
apps/purchasing/backend/app/graph_status.py:295-299     # test-only rejection
apps/dataops/backend/app/graph_status.py:91-133         # live-test gate
```

Configuration-driven: `GRAPH_BACKEND=age` enables AGE writes.

## 4.2 Trading migration + verification

```powershell
python -m copilot_sdk.migrate sqlite_to_age --domain=trading --source=<TRADING_SQLITE_PATH> --age-dsn="host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres" --graph-name=soc_graph --use-scratch-graph
```

Dual-write → read-diff (N=40) → flip.

**AGE latency check (before PW):** Measure one AGE-backed cache miss for Trading's
highest-frequency endpoint. If latency increases materially under `GRAPH_BACKEND=age`,
apply `@cached_static` before running PW.

```powershell
cd "$env:CLAUDE_SDK"
python -m pytest apps/trading/backend/tests/ -q --timeout=120  # expect 1229+

cd e2e
npx playwright test trading/ --reporter=list --retries=0 --workers=1
# --workers=1 for Trading. AGE-over-TCP raises latency on cache misses;
# 4 workers against single-threaded uvicorn re-creates the tab_data_provider
# timeout pattern. Measure first, relax later.
```

## 4.3 Purchasing migration + verification

Same pattern.

```powershell
python -m pytest apps/purchasing/backend/tests/ -q --timeout=120  # expect 686+
npx playwright test purchasing/ --reporter=list --retries=0  # expect 235/0/1
```

## 4.4 DataOps migration + verification

Same pattern, plus:
- `apps/dataops/backend/app/graph_queries.py:43` — direct AGEClient import wrapped
  through the projection module (decided in Phase 2.4, not a TODO).
- Demo bundle restore path (`copilot_sdk/demo/bundle.py:55-60`) updated to use
  GraphStore protocol for AGE restore.

```powershell
python -m pytest apps/dataops/backend/tests/ -q --timeout=120  # expect 176+
npx playwright test dataops/ --reporter=list --retries=0 --workers=1  # expect 133/0/1
```

## 4.5 Demo.py integration

```powershell
cd "$env:CLAUDE_SDK"
python demo.py --stop
$env:GRAPH_BACKEND = "age"
python demo.py --preseed --no-browser
```

All 5 copilots on AGE. `demo.py --status` shows `[shared judgment graph]`.
`demo.py --reset <domain>` calls `domain_scoped_reset()`.

**Full PW gate:**

```powershell
cd e2e
npx playwright test trading/ --reporter=list --retries=0 --workers=1
npx playwright test purchasing/ --reporter=list --retries=0
npx playwright test --config=s2p/playwright.config.ts s2p/ --reporter=list --retries=0 --workers=1
npx playwright test dataops/ --reporter=list --retries=0 --workers=1

cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\frontend"
npx playwright test "tests/e2e" --reporter=list --timeout=60000 --workers=1
```

---

# PHASE 5: Skipped

Projection is permanent infrastructure. SOC schema stays as-is.

---

# PHASE 6: Cross-Copilot Proof (weeks 8-9)

**Precondition:** All 5 copilots on AGE. All PW suites pass.

**What this phase proves:** "Multiple domains coexist in one graph and one statement
can read across them." It proves both property-based cross-domain queries (joins) and,
where shared entities exist, genuine edge traversals. The honest claim is "one graph,
one query" — not "one traversal pattern."

## 6.1 Multi-domain visibility

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)
  RETURN d.domain, count(*) AS decisions
  ORDER BY decisions DESC
$$) as (domain agtype, decisions agtype);
```

**Gate:** Returns rows for soc, s2p, trading, purchasing, dataops.

## 6.2 Cross-domain category overlap

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d1:Decision {domain: 'soc'})
  WITH d1.category AS cat, count(d1) AS soc_count
  MATCH (d2:Decision {domain: 's2p', category: cat})
  RETURN cat, soc_count, count(d2) AS s2p_count
$$) as (category agtype, soc_count agtype, s2p_count agtype);
```

## 6.3 Conservation via `count_verified()` — NOT re-derived in Cypher

```python
# Python proof, not a Cypher query. V is never re-derived.
for domain in ["soc", "s2p", "trading", "purchasing", "dataops"]:
    store = create_graph_store(domain=domain, ...)
    v = count_verified(store, domain)
    print(f"{domain}: V={v}")
```

**Why not Cypher:** D2 defines V as a per-decision predicate with complementary branches.
Counting HAS_OUTCOME edges is a third definition that disagrees with the real V. A demo
that displays a V different from the conservation gate's V is the kind of thing a
technical reviewer catches live.

## 6.4 Audit chain traversal (within domain)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision {domain: 'soc'})-[:HAS_OUTCOME]->(o:Outcome)
  MATCH (d)-[:EMITTED_RECEIPT]->(r:EvidenceReceipt)
  MATCH (d)-[:HAS_CENTROID_CHECKPOINT]->(c:CentroidCheckpoint)
  RETURN d.decision_id, o.is_correct, r.chain_index, c.category
  LIMIT 5
$$) as (did agtype, correct agtype, chain agtype, cat agtype);
```

**Gate:** Returns rows. The full chain resolves in one query.

## 6.5 Genuine cross-domain edge traversal (if shared entities exist)

If any `DomainContext` node is referenced by decisions in two domains:

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d1:Decision {domain: 's2p'})-[:ABOUT]->(ctx:DomainContext)<-[:ABOUT]-(d2:Decision {domain: 'trading'})
  RETURN d1.decision_id, d2.decision_id, ctx.entity_id, ctx.entity_type
  LIMIT 5
$$) as (s2p_did agtype, trading_did agtype, entity_id agtype, entity_type agtype);
```

If no shared entities exist (depends on data), create one explicitly during preseed
to demonstrate the traversal pattern. Document whether the proof uses live or seeded data.

If no genuine cross-domain traversal is achievable with current data, state that
honestly. The claim "one graph, one query" is proven by §6.1-6.4. Cross-domain edge
traversal is the Phase 6+ aspiration once TransferPattern nodes exist.

## 6.6 Claim wording propagation

Update `outreach_elevator_pitches_v5_0.md`:
- "one traversal, one answer" → "one graph, one query"
- Each claim gets a footnote referencing the proof query

## 6.7 Demo.py display

```
$ python demo.py --status

  SOC        [shared judgment graph]  6,253 decisions  AGE
  S2P        [shared judgment graph]     12 decisions  AGE
  Trading    [shared judgment graph]    425 decisions  AGE
  Purchasing [shared judgment graph]      ? decisions  AGE
  DataOps    [shared judgment graph]      ? decisions  AGE
```

---

# Definition of done (all phases)

| Item | Done when |
|---|---|
| PF-1..PF-7 | Values profiled; V predicate locked; cardinality zero-row; `is_correct` type known; PW baseline captured |
| Edge backfill | 3 types applied; verification gates pass; PW diff empty; invariant test passing |
| Decision domain backfill | ~6,253 SOC Decisions tagged `domain='soc'`; zero remaining nulls |
| DataOps backfill | 29 nodes tagged; registry test in CI |
| D2 V function | One implementation; four fixtures pass; overlap metric emitting; used by all proofs |
| TRIGGERED_EVOLUTION | Written analysis with vocabulary collision resolution |
| Projection module | Closed registry; equivalence tests (with normalize); scanner; invariant test; DataOps Rule #29 resolved |
| Rule #38 | All 4 SDK mains use factory; all suites pass |
| AGE conformance | 88/88 on isolated test graph |
| S2P on AGE | Dual-write → 40 cycles → flip; 194 PW pass; cross-domain visibility proven |
| Trading on AGE | Same pattern; 246 PW pass (workers=1); AGE latency measured |
| Purchasing on AGE | Same pattern; 235 PW pass |
| DataOps on AGE | Same pattern; 133 PW pass; graph_queries.py wrapped; bundle restore fixed |
| Demo.py on AGE | All copilots start; status shows shared graph; reset works per domain |
| Phase 6 proof | Multi-domain visibility; audit chain traversal; conservation via count_verified(); claim wording updated |

---

# Execution sequence

| Week | Work | Gate |
|---|---|---|
| **1** | PF-1..PF-7; lock V predicate | Cardinality zero; predicate documented; `is_correct` type known |
| **1** | Edge backfill (3 types) + Decision domain (~6,253) + DataOps (29) | Verification gates pass; PW diff empty |
| **1-2** | D2 V function + four fixtures + overlap metric | All fixtures pass both adapters |
| **2-3** | TRIGGERED_EVOLUTION analysis | Written decision |
| **2-4** | Projection module: registry, normalize, equivalence, scanner, invariant | Tests pass |
| **2-4** | Rule #38 factory compliance (**after D2**) | All suites pass with factory |
| **3-5** | AGE conformance: 44→88 tests | 88/88 |
| **5-7** | Phase 3: S2P migrate → dual-write → read-diff (N=40) → flip | 194 PW on AGE; cross-domain visibility |
| **7-8** | Phase 4: Trading (workers=1, measure latency) + Purchasing + DataOps | All PW suites on AGE |
| **8-9** | Phase 6: proofs; claim wording; demo.py display | Every claim demonstrated |

**~9 weeks sequential.** Phase 5 skipped. Weeks 2-4 overlap after D2 lands.

---

*AGE Shared Graph Migration v3.2 · July 19, 2026*
*Three v3.1 blockers resolved: Decision domain backfill (B1), V never*
*re-derived (B2), Phase 6 retitled with honest claims (B3).*
*9 decisions. 6 phases. Executable runbooks.*
*Design decisions settled — phase transitions have execution gates.*
*Target: every §2 claim provable. Honest about joins vs traversals.*
