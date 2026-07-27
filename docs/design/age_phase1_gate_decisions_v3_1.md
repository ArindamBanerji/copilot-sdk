# AGE Phase 1 Gate — v3.1 (Executable)

**Date:** July 19, 2026 · **Revision:** v3.1
**Authority:** judgment_memory_v2_7.md
**History:** v1 → review → v2 → close review → v3 → executability + correctness pass → v3.1
**Status:** Decisions are settled (v3). v3.1 adds what a coding session needs to run them,
plus three correctness fixes found while making them runnable.

## What changed v3 → v3.1

| # | Finding | v3 | v3.1 |
|---|---|---|---|
| C1 | `correct` field dropped from the V predicate | Predicate uses `outcome IS NOT NULL` only | v1 said `outcome IS NOT NULL or correct IS NOT NULL`. The `or correct` was lost between v1→v3. Pre-flight PF-2 decides it with data, then the predicate is locked |
| C2 | `outcome IS NOT NULL` is unvalidated as a verification signal | Assumed to mean "verified" | If outcome is written at score time (or can be `''`/`'pending'`), V overcounts — the direction that weakens the safety proof. PF-1 profiles the values before the predicate is locked |
| C3 | Queries are written in SQL, not AGE | `SELECT … FROM Outcome GROUP BY …`; two chained `MATCH … SET` in one block | Rewritten as runnable `cypher()` calls (§3, §4) |
| C4 | `WHERE NOT EXISTS { … }` subquery may be unsupported in AGE | Given as an option | Portable `OPTIONAL MATCH … WHERE r IS NULL` form given as the default |
| C5 | PW gate stated as a count | "SOC 408/0" | Compare failing-spec SETS, not counts — capture the baseline set first (the tab_data_provider lesson) |
| C6 | Missing verification + rollback commands | "verify counts", "delete by tag" | Exact queries for both, per edge type (§3.4, §3.5) |
| C7 | Fixture set missing the contradictory case | 3-shape + mixed-domain | Adds `status='pending'` with an embedded outcome (must NOT count) |

---

## 0. START HERE — coding session orientation (2 minutes)

**What this is.** Seven settled design decisions plus a runbook. Most of the work is
additive backfill and one new function — not a migration of live code paths.

**The three things that are true before you start:**

1. **GAE attention operates on protocol data, not graph labels** (`SchemaContract.node_type`
   is opaque). Projection is viable — you are not blocked on this.

2. **SOC has zero wildcard Cypher traversals** (`-[*` → 0 matches in `age_client.py`).
   Adding new edge types is invisible to SOC's existing reads.

3. **That invisibility does NOT extend to `TRIGGERED_EVOLUTION`** — SOC already queries it
   (`age_client.py:621`, `:972`, `:1012`) and those queries return zero rows today.
   **Furthermore, SOC uses a different topology:** `(Alert)-[:TRIGGERED_EVOLUTION]->(Entity)`,
   while §4 canonical says `(Decision)-[:TRIGGERED_EVOLUTION]->(EvolutionEvent)`. Same edge
   label, different source and target node types. This is a vocabulary collision, not just
   zero edges. It is excluded from the backfill and its separate analysis must address the
   node-type conflict, not merely the edge count. Do not add it back. (§6)

**Do-first order:**

| # | Task | Why first | Effort |
|---|---|---|---|
| 1 | PF-1..PF-5 pre-flight data checks (§1) | They can invalidate the V predicate. Nothing else should start until PF-2 is answered. | ~2h |
| 2 | Edge backfill, 3 types (§3) | ~1d, reversible, and it tests the load-bearing assumption of the whole plan (SOC's suite is insensitive to new edges). Fail here in week 1, not week 4. | ~1d |
| 3 | DataOps 29-node backfill (§4) | Trivial; removes a label special-case from a destructive op. | ~15m |
| 4 | D2 V function + fixtures (§2) | Must land before Rule #38 factory compliance. | 2-3d |

**Do NOT start Rule #38 factory compliance until item 4 is green.** Factory compliance can begin
writing `status`-bearing decisions into the SOC domain, creating the mixed-domain case that a
wrong V function mishandles silently.

---

## 1. Pre-flight data checks — these gate the V predicate (run FIRST)

**Set up once:**

```sql
LOAD 'age';
SET search_path = ag_catalog, "$user", public;
```

### PF-1 — What does an embedded outcome actually contain? (blocks D2)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)
  RETURN d.outcome AS outcome_value, count(*) AS n
  ORDER BY n DESC
$$) as (outcome_value agtype, n agtype);
```

**Why this gates everything:** the V predicate treats `outcome IS NOT NULL` as "verified."
If outcome is written at score time, or can be `''` / `'pending'` / `'unknown'`, then
V overcounts — inflating α·q·V and weakening the conservation proof. That is the one
failure direction that is not fail-safe.

**Decision rule:**
- Values are all terminal verification results (e.g. `confirmed`/`overridden`/`escalate`/`dismiss`)
  → predicate stands as `d.outcome IS NOT NULL`.
- Any non-verified sentinel appears (`''`, `pending`, null-string, score-time placeholder)
  → narrow the predicate to an explicit allow-list and record it in the docstring.

### PF-2 — Is `correct` a second verification signal? (blocks D2 — C1)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)
  WHERE d.outcome IS NULL AND d.correct IS NOT NULL
  RETURN count(*) AS orphaned_correct
$$) as (orphaned_correct agtype);
```

**Why:** v1 defined projection-mode V as `outcome IS NOT NULL or correct IS NOT NULL`.
The `or correct` clause was lost by v3. If this count is > 0, the v3 predicate
undercounts V for those decisions.

**Decision rule:** result 0 → predicate stands. Result > 0 → predicate becomes
`(d.outcome IS NOT NULL OR d.correct IS NOT NULL)`. Either way, write the answer into the
docstring so it is never silently re-dropped.

### PF-3 — Do any Decisions already carry `status`? (sizes the mixed-domain risk)

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)
  RETURN d.status AS status_value, count(*) AS n
$$) as (status_value agtype, n agtype);
```

Expect all-null today. Any non-null result means a mixed domain already exists — the
mixed-domain test (§2) becomes a regression test rather than a precaution, and D2's priority
rises above the backfill.

### PF-4 — Cardinality + orphan gates for the backfill (blocks §3)

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

-- (d) orphan Outcomes with no matching Decision — record the count
SELECT * FROM cypher('soc_graph', $$
  MATCH (o:Outcome)
  OPTIONAL MATCH (d:Decision) WHERE d.decision_id = o.decision_id
  WITH o, d WHERE d IS NULL
  RETURN count(*) AS orphans
$$) as (orphans agtype);

-- (e) CentroidCheckpoints with no decision_id — record the count
SELECT * FROM cypher('soc_graph', $$
  MATCH (c:CentroidCheckpoint) WHERE c.decision_id IS NULL
  RETURN count(*) AS no_did
$$) as (no_did agtype);
```

**Gate:** (a), (b), and (c) must return zero rows. A duplicate breaks D2's canonical-mode
requirement that exactly one Outcome links per decision. If non-empty: stop, understand
whether it is re-verification or correction, and decide disposition before backfilling.

**Orphan disposition (d):** Orphan Outcomes are excluded from the backfill. The OPTIONAL MATCH
form in §3.1 naturally handles this — if no Decision matches, no edge is created. Adjust the
dry-run expected count: `would_create ≈ Outcome count − orphan count`, not `≈ Outcome count`.

**CentroidCheckpoint nulls (e):** If many CentroidCheckpoints lack `decision_id`, the backfill
will create zero edges for those nodes and the expected count won't match. Record the count and
adjust the §3.2 dry-run gate accordingly.

### PF-5 — capture the PW baseline as a SET, not a count (C5)

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\frontend"
npx playwright test "tests/e2e" --reporter=list --timeout=60000 --workers=1 2>&1 | Select-String "^\s+\d+.*FAIL|failed" > C:\temp\soc_baseline_fails.txt
npx playwright test "tests/e2e" --reporter=list --timeout=60000 --workers=1 2>&1 | Select-String "^\s+-\s+" > C:\temp\soc_baseline_skips.txt
```

Record WHICH specs fail and skip, not how many. The post-backfill gate compares sets.

---

## 2. Decision 2 — the V function (corrected)

### The predicate

```
-- LOCKED after PF-1/PF-2 resolve the two bracketed choices.
V = count(DISTINCT d.decision_id) WHERE
      (d.status IS NOT NULL AND d.status IN ('confirmed','overridden'))
   OR (d.status IS NULL     AND <PF1_VERIFIED_PREDICATE>)

-- <PF1_VERIFIED_PREDICATE> is one of:
--   d.outcome IS NOT NULL                                  -- if PF-1 clean and PF-2 == 0
--   (d.outcome IS NOT NULL OR d.correct IS NOT NULL)       -- if PF-2 > 0
--   d.outcome IN (<allow-list from PF-1>) [OR d.correct …] -- if PF-1 found sentinels
```

`IS NOT NULL` and `IS NULL` are complementary, so "never both" holds by construction — it is
a property of the predicate, not a test someone can delete. Keep that structure through any
PF-driven edit.

### Implementation

```python
# copilot_sdk/graph/conservation.py — THE V FUNCTION. One implementation. No copilot reimplements.
def count_verified(store: GraphStore, domain: str) -> int:
    """V for conservation (rule #37). Per-decision predicate:
      status-bearing  -> status IN ('confirmed','overridden')
      status-less     -> <PF1_VERIFIED_PREDICATE>   # resolved by PF-1/PF-2 on <date>; see §1
    Complementary branches — cannot double-count by construction.
    
    Legacy branch (status IS NULL) exists for pre-migration SOC decisions.
    Remove after SOC schema migration (if ever — projection is permanent)."""
```

Both `SQLiteGraphStore` and `AGEGraphStoreAdapter` implement the same per-decision predicate
in `count_verified_decisions(domain)`.

### Fixtures (four cases — case 4 is new)

| # | Fixture | Assert |
|---|---|---|
| 1 | Three shapes: embedded-only, canonical-only, both | each counts exactly once |
| 2 | Mixed domain: one domain with a status-bearing and a status-less decision | `V == 2` — this is the test that catches the v2 domain-fallback bug |
| 3 | Overlap metric: runtime log of `V_embedded + V_canonical − V_actual` | nonzero in a single-domain query → alarm |
| 4 | Contradictory (C7): `status='pending'` with an embedded outcome | NOT counted — pending is not verified, and the status branch owns it |

### Sequencing

D2 lands before Rule #38 factory compliance. Non-negotiable — see §0.

---

## 3. Runbook A — canonical edge backfill (three types)

**Scope:** HAS_OUTCOME (~1,015), EMITTED_RECEIPT (~216), HAS_CENTROID_CHECKPOINT (~1,015).
**Excluded:** TRIGGERED_EVOLUTION — see §6.
**Precondition:** PF-4 (a)(b)(c) returned zero rows; PF-5 baseline captured.

### 3.1 Idempotency form (portable — C4)

AGE's support for MERGE on relationships and for `WHERE NOT EXISTS { … }` subqueries is
version-dependent. Use the `OPTIONAL MATCH … WHERE r IS NULL` form, which works on every
AGE version:

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

Replace `<CURRENT_EPOCH>` with the actual epoch at execution time (e.g., `1753045200` for
July 20, 2026). Do not leave as a placeholder.

Two properties this buys you:

- **Re-runnable.** Already-linked pairs are filtered out, so a second run creates 0 edges.
- **Resumable.** If the statement is killed halfway, re-running completes the remainder —
  which is why the guard matters more than the transaction size.

(If you prefer MERGE, first prove it on a 5-node sample and confirm it does not duplicate on
a second run before using it at scale.)

### 3.2 Dry-run — count what would be created, change nothing

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision), (o:Outcome)
  WHERE d.decision_id = o.decision_id
  OPTIONAL MATCH (d)-[r:HAS_OUTCOME]->(o)
  WITH d, o, r WHERE r IS NULL
  RETURN count(*) AS would_create
$$) as (would_create agtype);
```

**Gate:** `would_create ≈ Outcome node count − orphan count` (from PF-4d). A materially
different number means the join key is wrong — stop and investigate.

Also time this dry-run. It is the same plan as the write; if it is slow at ~6K × ~1K rows,
add a property index before writing rather than discovering it mid-transaction.

### 3.3 Apply (one label at a time, verifying between)

Run 3.1 for each of the three edge types, substituting:

| Edge | Target label | Expected |
|---|---|---|
| HAS_OUTCOME | Outcome | ~1,015 minus orphans |
| EMITTED_RECEIPT | EvidenceReceipt | ~216 |
| HAS_CENTROID_CHECKPOINT | CentroidCheckpoint | ~1,015 minus null-`decision_id` count (PF-4e) |

### 3.4 Verify (per edge type — C6)

```sql
-- (a) edge count equals the matched-pair count
SELECT * FROM cypher('soc_graph', $$
  MATCH ()-[r:HAS_OUTCOME]->() RETURN count(r) AS edges
$$) as (edges agtype);

-- (b) every backfilled edge is tagged (untagged => something else wrote it)
SELECT * FROM cypher('soc_graph', $$
  MATCH ()-[r:HAS_OUTCOME]->()
  WHERE r.source IS NULL
  RETURN count(r) AS untagged
$$) as (untagged agtype);

-- (c) no decision has more than one (protects D2's "exactly one" requirement)
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)-[:HAS_OUTCOME]->(o:Outcome)
  WITH d.decision_id AS did, count(*) AS c
  WHERE c > 1
  RETURN did, c
$$) as (did agtype, c agtype);

-- (d) the audit chain is now a traversal — the claim this unlocks
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)-[:HAS_OUTCOME]->(o:Outcome)
  RETURN d.decision_id, o.is_correct LIMIT 5
$$) as (decision_id agtype, is_correct agtype);
```

**Gates:** (a) matches the dry-run number · (b) `untagged == 0` at this stage ·
(c) zero rows · (d) returns rows.

### 3.5 Post-backfill PW gate (set comparison, not count — C5)

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\frontend"
npx playwright test "tests/e2e" --reporter=list --timeout=60000 --workers=1 2>&1 | Select-String "^\s+\d+.*FAIL|failed" > C:\temp\soc_after_fails.txt
Compare-Object (Get-Content C:\temp\soc_baseline_fails.txt) (Get-Content C:\temp\soc_after_fails.txt)
```

**Gate:** the diff is empty. A count match with a different failing spec is a regression
masked by a flake — the exact trap the 239/2 baseline taught. Any new title in the diff →
roll back (§3.6) and analyse before retrying.

### 3.6 Rollback (exact — C6)

```sql
-- Deletes ONLY backfilled edges. Forward-written SDK edges (no source tag) survive.
SELECT * FROM cypher('soc_graph', $$
  MATCH ()-[r:HAS_OUTCOME {source: 'backfill'}]->()
  DELETE r RETURN count(*) AS deleted
$$) as (deleted agtype);
```

Repeat per edge type. **Never** `MATCH ()-[r:HAS_OUTCOME]->() DELETE r` — that also removes
edges written forward by SDK copilots after the backfill.

---

## 4. Runbook B — DataOps domain backfill (29 nodes)

Two separate statements — AGE executes one Cypher statement per `cypher()` call (C3):

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (n:DataQualityAlert) SET n.domain = 'dataops' RETURN count(*) AS updated
$$) as (updated agtype);

SELECT * FROM cypher('soc_graph', $$
  MATCH (n:PipelineSystem) SET n.domain = 'dataops' RETURN count(*) AS updated
$$) as (updated agtype);
```

**Verify** (two queries — AGE may not support multi-label OR in WHERE):

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (n:DataQualityAlert) WHERE n.domain IS NULL RETURN count(*) AS untagged
$$) as (untagged agtype);

SELECT * FROM cypher('soc_graph', $$
  MATCH (n:PipelineSystem) WHERE n.domain IS NULL RETURN count(*) AS untagged
$$) as (untagged agtype);
```

Both must return 0.

Then: forward-tag all new DataOps context writes with `domain='dataops'`, and add the
label→domain registry test — for every label a copilot writes, assert it is registered with
the correct owner. That converts "assumed ownership" into a checkable constraint in front of
`domain_scoped_reset`.

**Rollback:** `MATCH (n:DataQualityAlert) REMOVE n.domain` (and PipelineSystem).

---

## 5. Definition of done

| Item | Done when |
|---|---|
| PF-1..PF-5 | Values profiled; `<PF1_VERIFIED_PREDICATE>` chosen and written into the docstring; cardinality gates zero-row; PW baseline set captured |
| Edge backfill | 3 types applied; §3.4 (a)-(d) gates pass; §3.5 diff empty; rollback rehearsed once on one edge type |
| DataOps backfill | 29 nodes tagged; untagged query returns 0; registry test in CI |
| D2 V function | One implementation; both adapters use the same predicate; all four fixtures pass; overlap metric emitting |
| Projection module | `PROJECTION_PATTERNS` closed registry; equivalence test per entry; scanner finds no raw cross-copilot Cypher outside the module |
| Rule #38 | Started only after D2 is green |
| TRIGGERED_EVOLUTION | A written analysis exists (consumers, PW assertions, join key, **node-type vocabulary collision**) — not a backfill |

---

## 6. Do NOT do (each of these has bitten a prior version)

**Do not backfill TRIGGERED_EVOLUTION with the other three.** SOC already queries it at
`age_client.py:621`, `:972`, `:1012`; those queries return zero rows today. Adding 142 edges
changes a live read path — UI, counts, and any PW assertion depending on emptiness.
**The conflict is deeper than zero edges:** SOC uses `(Alert)-[:TRIGGERED_EVOLUTION]->(Entity)`
while the canonical model says `(Decision)-[:TRIGGERED_EVOLUTION]->(EvolutionEvent)`. Same edge
label, different source and target node types. The separate analysis must decide: rename one,
use both with domain-scoped queries, or introduce a new canonical edge label for SDK copilots.

**Do not use `CREATE` without the `OPTIONAL MATCH … WHERE r IS NULL` guard.** `CREATE` is
not idempotent; a second run duplicates every edge.

**Do not roll back by edge type alone.** Delete by `{source: 'backfill'}`.

**Do not implement V per copilot.** One function; both adapters call the same predicate.

**Do not start Rule #38 before D2 is green.** It can create the mixed domain that a wrong
V function silently mishandles.

**Do not compare PW results by count.** Compare failing-spec sets.

**Do not claim "one traversal, one answer" externally.** The projection branches by domain.
Use "one graph, one query." This must reach `outreach_elevator_pitches_v5_0.md` —
a claim decided here and not propagated there is cosmetic.

---

## 7. Execution sequence

| Week | Work | Gate |
|---|---|---|
| **1** | PF-1..PF-5 pre-flight; lock the V predicate | PF-4 zero rows; predicate written into the docstring |
| **1** | Edge backfill (3 types, ~2,246 edges) + DataOps 29 nodes | §3.4 gates pass; §3.5 diff empty |
| **1-2** | D2 V function + four fixtures + overlap metric | all fixtures pass on both adapters |
| **2-3** | TRIGGERED_EVOLUTION analysis (not backfill) — must address node-type collision | written decision |
| **2-4** | Projection module: registry, equivalence tests, scanner | equivalence test per registered pattern |
| **2-4** | Rule #38 factory compliance — **after D2** | all suites pass with factory |
| **3-5** | AGE conformance: 44 skipped tests on the live test graph | 88/88 |
| **5-7** | Phase 3: S2P dual-write → read-diff (N=40, AGE write failure resets the counter) → flip | 194 S2P PW on AGE |
| **7-8** | Phase 4: Trading + Purchasing + DataOps, same pattern | all PW suites on AGE |
| **8-9** | Phase 6: cross-copilot traversal proof | every §2 claim demonstrated |

~9 weeks sequential. Phase 5 skipped (projection is permanent infrastructure).
Some overlap possible (projection module can start in week 2 alongside V work).

### Dual-write failure policy (Phase 3+)

When AGE write fails and SQLite succeeds:
- **Action:** Log the failure. Continue serving from SQLite.
- **Diff-cycle counter:** Reset to zero. AGE write failures mean the two stores may have
  diverged. The diff-cycle counter measures read equivalence; masking write drift produces
  false confidence.
- **Alarm:** If AGE write failure rate exceeds 1% over a 1-hour window, surface an
  operational alert.
- **N = 40** (same discipline as P29-D shadow scorer, proven).

---

*AGE Phase 1 Gate v3.1 · July 19, 2026 · Decisions from v3, unchanged.*
*Three correctness fixes: the `correct` clause restored as a data question (PF-2), the*
*outcome-means-verified assumption made a gate (PF-1), the contradictory pending+outcome*
*fixture added. Everything else is executability: AGE-syntax queries, dry-run gates,*
*verification and rollback commands, set-based PW comparison, and a do-not-do list.*
*TRIGGERED_EVOLUTION identified as a vocabulary collision (different node types), not just*
*zero edges — deferred to separate analysis.*
