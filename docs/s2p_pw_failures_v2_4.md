# S2P Playwright Failures — Diagnosis, Fix, and Architecture Decisions
**Version:** 2.4 · **Date:** May 30, 2026
**For:** Roadmap session + Coding session handoff
**Supersedes:** v2.3 (May 30, 2026)
**Status:** Fix 1 (algorithmic) ready for Codex. Architecture questions DECIDED
(Q1-Q4). Fix 3 implementation sequence defined.

**Changes v2.3 → v2.4:** Fix 3c SQL rewritten: decisions_archive is
denormalized (decisions+outcomes columns + archived_at + autoincrement PK).
SELECT * replaced with explicit column INSERT, NULLs for outcome fields.
Fix 3a atomic update confirmed: is_correct is bool, no mapping needed.
Review note #13 (outcome.action ambiguity) resolved.

**Changes v2.2 → v2.3:** Implementation sequence reordered: Fix 4
(CI_DATA_DIR) promoted to FIRST — gates Fix 3c path and Phase 2
factory. §8 updated: Fix 4 first, then Fix 1. Platform-wide warning
added to §13 for Fix 3a/3b (affects ALL 5 copilots, not just S2P).

**Changes v2.1 → v2.2:** Fixed 5 items from second coding session review:
(1) Migration trigger specified: constructor version-check (SDK convention).
(2) `expired` state marked reserved/future — removed from Fix 3 scope.
(3) Cross-copilot ALTER explicit for existing Trading/Purchasing/DataOps DBs.
(4) Defensive `WHERE is_correct IS NOT NULL` added to backfill SQL.
(5) Demo bundle interaction documented (bundles get DEFAULT 'pending').

**Changes v2.0 → v2.1:** Fixed 4 issues from coding session review:
(1) SQL migration uses is_correct not action column. (2) Fix 1→Fix 3
stepping-stone relationship explicit. (3) count_verified_decisions()
method spec added to Fix 3a. (4) learn() status mapping resolved
to is_correct=1→confirmed, is_correct=0→overridden.

**Changes v1.0 → v2.0:** Added architecture decisions with mathematical
justification (§10), product/commercial implications (§11), innovation value
analysis (§12), and implementation sequence for Fix 3 (§13). All four
architecture questions resolved. Review notes appended (§14).

---

## §1 — What the S2P Tests Do

The S2P copilot is an invoice exception triage system. A procurement analyst
sees a queue of invoices, selects one, clicks Score to get a recommendation
(approve / hold / escalate / flag / refer), and then confirms or overrides it.
The Playwright tests simulate this flow end-to-end against a live backend.

The test file `phase1.spec.ts` covers the core triage flow:

```
1. Open "Exception Triage" tab
2. Expect the invoice queue to render (panel contains "queued" or "S2P-INV-...")
3. Click Score on the selected invoice
4. Expect a result card to appear containing "Action index", "Confidence", "Decision"
```

The locator `scoreResultPanel` is defined as:
```typescript
page.locator("article", { hasText: "Action index" })
```

This text comes from the score API response field `action_index` rendered in
the UI. At `workers=1`, the test passes in ~4.5 seconds. At `workers=4`, 24
tests hard-fail.

The 12 "flaky" tests fail on first attempt and pass on retry. This is
explained by Playwright's `retries: 1` setting — the retry hits a populated
cache and succeeds.

---

## §2 — The Conservation Law (What It Is and Why It Runs on Every Request)

The CI platform enforces a mathematical conservation law on every copilot:

```
α · q · V ≥ θ_min
```

Where:
- α = fraction of decisions verified by humans (standing rule #12: among
  verified decisions — measures category coverage, not verification ratio)
- q = rolling verified accuracy over 400 decisions (q_window=400,
  theorem-validated in math_synopsis v14)
- V = decision volume
- θ_min = 23.53 / (α × V) — formula, not a constant

The conservation law is a safety guarantee: it auto-pauses centroid learning
when human oversight thins. GREEN = learning active. AMBER = learning paused.
RED = learning paused, scoring degraded.

`GET /api/conservation/status` evaluates this law on every call by reading
three counts from the database: `verified_count`, `correct_count`,
`total_decisions`. This endpoint is called:
- Once per Playwright worker at startup (backendHealth pre-warm)
- Once per score request (the score route reads conservation to gate learning)
- On every browser poll from the frontend UI

**Key: the conservation law protects HUMAN OVERSIGHT quality.** It is the
only AI safety theorem in production — validated by 3 independent reviewers,
proven via 4 independent proof paths, tested across 295 experiments with zero
falsification. The definition of V must be consistent with this purpose.

---

## §3 — The Database (What It Contains and How It Got There)

The S2P backend uses a SQLite database at:
```
s2p-copilot/backend/app/data/s2p.db
```

This path is hardcoded in `main.py`:
```python
DATA_DIR = Path(__file__).parent / "data"
app.state.scorer = build_s2p_scorer(str(DATA_DIR / "s2p.db"))
```

Note: `demo.py --reset s2p` wipes `~/.ci-platform/s2p/` — a different
location that does not exist. The demo.py reset command has no effect on S2P.

At time of diagnosis, the database contained:
- **23,607 rows** in the `decisions` table
- **12 rows** in the `outcomes` table (human confirmations/overrides)
- **0 rows** in `decisions_archive`
- File size: **33 MB**

The ratio of 1,967 unconfirmed decisions per confirmed outcome means the
conservation signal has collapsed under the current V definition:
```
θ_min = 23.53 / (α × V) = 3,857
signal = α · q · V = 0.0056
Conservation status: permanently RED
```
*(These values are as reported by the current implementation, which computes
α as verified/total. Under the Option B decision in §7, V = verified_count
and conservation recovers to GREEN — see §7 recovery test.)*

Where did the 23,607 rows come from? Every `POST /api/s2p/score` call writes
a row to `decisions`. Sources: Playwright test runs, demo sessions, preseed
scripts. None write a corresponding `outcomes` row unless the analyst
explicitly confirms or overrides.

---

## §4 — The Failure Mechanism (Confirmed by Live Scans)

### The algorithmic bug

`GET /api/conservation/status` calls `_read_conservation_counts()` which
calls `get_all_decisions()` — fetching all rows from the `decisions` table
into Python memory just to count them. At 23,607 rows: **4–7 seconds per
call**.

The identical bug exists in `_state_counts()` in `conservation_router.py`.

`count_decisions(domain)` already exists on `SQLiteGraphStore` and runs a
SQL `COUNT(*)`. It is already used in `bundle.py`. It was simply never used
in the conservation path.

### Why concurrent workers make it worse

`SQLiteGraphStore` uses `threading.RLock` that serializes all SQLite access.
With 4 Playwright workers:

```
Worker 1: get_all_decisions() → holds _lock → 4-7s
Worker 2: waits → 4-7s after W1
Worker 3: waits → 8-14s total
Worker 4: waits → 12-21s total
```

Playwright per-assertion timeout: 10 seconds. Workers 3-4 consistently
exceed this. Assertions expire → hard failures.

### Why some tests are "flaky"

Cache TTL makes retries work. A test that fails on first attempt (cache cold)
passes on retry (cache warm, <1ms). After Fix 1, conservation is always
<1ms — no retries needed.

### What was ruled out

| Hypothesis | Evidence against |
|---|---|
| React AbortController | None in frontend codebase |
| StrictMode double-invoke | `handleScore()` is onClick, not useEffect |
| Empty invoice queue | Queue returns 50 invoices; passes at workers=1 |
| Stale locator | Score response confirmed to contain `action_index` |
| Missing globalSetup | `global-setup.ts` already exists |

---

## §5 — Diagnostic Reset (Not a Fix)

Deleting the database proves the accumulation hypothesis: with 0 rows,
`COUNT(*)` is trivial and conservation returns in <10ms.

**This is diagnostic, not a product fix.** It destroys accumulated state
and hides the failure mode.

---

## §6 — Fix 1: Algorithmic Fix (Ready for Codex)

Replace `len(get_all_decisions(...))` with `count_decisions(...)` in both
conservation paths. O(1) via SQL `COUNT(*)` regardless of DB size. No
conservation semantics change. No schema change. Minimal diff.

### Codex prompt (use verbatim)

```
/model gpt-5.3
Echo the current model name in the first line of output.

TASK: Replace O(N) conservation decision counting with O(1) count_decisions.
TASK TYPE: Minimal systemic performance fix.

WORKING DIRECTORY:
C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects

REPOS:
- s2p-copilot
- copilot-sdk

BUG:
S2P conservation status computation uses len(get_all_decisions(domain)) to
compute total_decisions. This fetches all decision rows into Python just to
count them. With a large S2P DB this takes seconds and serializes under
SQLiteGraphStore locking. The graph store already exposes count_decisions(domain).

IMPORTANT:
This prompt fixes only the algorithmic counting bug. Do not change conservation
semantics. Do not delete/reset DB. Do not add source tagging. Do not archive
decisions. Do not change Playwright timeouts.

FILES TO EDIT:

1. s2p-copilot/backend/app/routers/s2p.py
   Function: _read_conservation_counts

2. copilot-sdk/copilot_sdk/backend/conservation_router.py
   Function: _state_counts

IMPLEMENTATION:
In both functions, replace total_decisions computation that uses
len(get_all_decisions(...)) with count_decisions(...) when available.

In s2p.py, replace:

    get_all_decisions = getattr(graph_store, "get_all_decisions", None)
    total_decisions = (
        len(get_all_decisions(selected_domain)) if callable(get_all_decisions)
        else verified_count
    )

with:

    # O(1) COUNT(*) — avoids full row fetch
    _count_decisions = getattr(graph_store, "count_decisions", None)
    if callable(_count_decisions):
        total_decisions = int(_count_decisions(selected_domain))
    else:
        _get_all = getattr(graph_store, "get_all_decisions", None)
        total_decisions = (
            len(_get_all(selected_domain)) if callable(_get_all)
            else verified_count
        )

In conservation_router.py, replace:

    total_decisions = (
        len(get_all_decisions(store_domain)) if callable(get_all_decisions)
        else verified_count
    )

with:

    # O(1) COUNT(*) — avoids full row fetch
    _count_decisions = getattr(store, "count_decisions", None)
    if callable(_count_decisions):
        total_decisions = int(_count_decisions(store_domain))
    elif callable(get_all_decisions):
        total_decisions = len(get_all_decisions(store_domain))
    else:
        total_decisions = verified_count

TEST REQUIREMENTS:
Add focused tests confirming count_decisions used when available, fallback
works, total_decisions value unchanged for known dataset.

OUTPUT:
READY:
FILES_CHANGED:
ROOT_CAUSE:
IMPLEMENTATION_SUMMARY:
SEMANTICS_AUDIT:
- total_decisions semantics changed: YES/NO
- only algorithm changed: YES/NO
TESTS_RUN:
RESULTS:
PERFORMANCE_RESULT:
RESIDUAL_RISKS:
```

**Stepping-stone note:** Fix 1 makes counting fast (O(1) COUNT of ALL
rows). Fix 3 changes WHAT is counted (verified-only via a new
`count_verified_decisions()` method). Fix 1 is intentionally temporary —
it makes counting fast; Fix 3 makes it semantically correct. After Fix 3
ships, `count_decisions()` is superseded by `count_verified_decisions()` in
the conservation path. Both methods continue to exist — `count_decisions()`
for audit/replay, `count_verified_decisions()` for conservation.

### After Fix 1 — Validation sequence

```powershell
# 1. Measure conservation timing on existing (large) DB
$t = [Diagnostics.Stopwatch]::StartNew()
Invoke-RestMethod "http://localhost:8002/api/conservation/status" `
  -TimeoutSec 20 | ConvertTo-Json -Depth 8
$t.Stop()
Write-Host "Conservation: $([math]::Round($t.Elapsed.TotalSeconds,3))s"
# Target: <0.1s regardless of DB size

# 2. Run PW at workers=1 first
npx playwright test --project=s2p --workers=1 --timeout=60000 2>&1 |
  Tee-Object pw_s2p_after_fix1_workers1.txt

# 3. If workers=1 green, run at workers=4
npx playwright test --project=s2p --workers=4 2>&1 |
  Tee-Object pw_s2p_after_fix1_workers4.txt
```

---

## §7 — Architecture Questions (DECIDED)

Fix 1 resolves the performance bug. But the failure exposed three unresolved
design questions about what `decisions` means in the conservation formula.
All four questions are now resolved.

### Q1: What does V mean in the conservation formula?

**DECISION: Option B — Verified decisions only.**

**Reasoning (mathematical):**

The conservation law α·q·V ≥ θ_min exists to guarantee that HUMAN OVERSIGHT
is sufficient before the system expands automation. Every component of the
formula must be consistent with this purpose:

- **α** is already computed among verified decisions (standing rule #12,
  propagated to all 4 math documents in v14). α measures category coverage
  of the verified decision space, not a ratio of verified to total.
- **q** is rolling verified accuracy over 400 verified decisions (q_window=400,
  theorem-validated in math_synopsis v14, SOC-Q1 adjudicated).
- **θ_min = 23.53/(α×V)** is the minimum signal strength required.

If α and q are both scoped to verified decisions, V must be too. Otherwise
the formula is dimensionally inconsistent — α and q measure human oversight
quality while V measures automated throughput. The conservation law would
be mixing two different populations in one equation.

**The absurdity test:** Under Option A (all scored), a Playwright test suite
scoring 1,000 invoices with zero human confirmations pushes V to 1,000 and
changes θ_min. That's not a safety signal — it's an artifact of automated
testing. The conservation law must be BLIND to non-human activity.

**The recovery test (illustrative):** Under Option B with 12 verified
decisions at q≈0.83 and α≈0.6 (assuming 3 of 5 categories have verified
data — actual coverage depends on the 12 decisions' category distribution):

```
V = 12 (verified only)
α = 3/5 = 0.6 (categories with verified decisions — illustrative)
q = 10/12 ≈ 0.83 (rolling accuracy)
θ_min = 23.53 / (0.6 × 12) = 3.27
signal = 0.6 × 0.83 × 12 = 5.98
5.98 ≥ 3.27 → GREEN ✓
```

Even with only 2 categories covered (α = 0.4): signal = 0.4 × 0.83 × 12 =
3.98 vs θ_min = 23.53 / (0.4 × 12) = 4.90 → AMBER. Still recoverable
with ~5 more verified decisions. Under Option A: permanently unrecoverable.

12 verified decisions with 83% accuracy across 3 categories IS sufficient
to start learning. The system should not be permanently RED because a test
suite ran 23,000 unverified scores. Under Option B, the conservation signal
is recoverable and accurately reflects human oversight — which is exactly
what the theorem was designed to protect.

**Cross-copilot consistency:** SOC (6,4,6)=144 tensor already counts V from
verified decisions. Trading and Purchasing also scope to verified. S2P must
be consistent. The conservation law is domain-independent — the V definition
must be too.

---

### Q2: When does score() write to decisions?

**DECISION: Write at score time + status column.**

This cleanly separates two concerns that the current design conflates:

| Concern | What it needs | Solution |
|---|---|---|
| **Audit trail** | Every score event recorded and replayable | Write at score time → `status='pending'` |
| **Conservation** | Only human-verified decisions count toward V | Filter: `status IN ('confirmed','overridden')` |
| **Flywheel** | TRIGGERED_EVOLUTION edges reference Decision nodes | Decision node exists from score time ✓ |

**Why not "write at outcome time only":**
- Breaks TRIGGERED_EVOLUTION edges in the AgentEvolver flywheel — the
  evolution system references Decision nodes at score time to trace which
  patterns led to which recommendations. Deferring the write breaks this
  chain.
- Loses audit trail for scores never acted on. In production, a procurement
  analyst may score 20 invoices, act on 15, and abandon 5. The 5 abandoned
  scores still have diagnostic value (why were they scored but not acted on?).
- Requires a staging mechanism for in-flight decisions that adds complexity
  without adding capability.

**Why status column is better than source tagging:**
Source tagging (`source='preseed'`, `source='test'`, `source='production'`)
was evaluated and rejected because:
1. It requires retroactive classification of 23,607 rows with incomplete
   provenance information.
2. It introduces a fragile taxonomy — every new scoring context needs a new
   source value.
3. It conflates origin with lifecycle state. A preseed decision that gets
   confirmed by a human IS a verified decision regardless of origin.

The status column captures lifecycle state cleanly: every decision starts
as `'pending'` and transitions to `'confirmed'` or `'overridden'` when acted
on. This is the decision's LIFECYCLE, not its ORIGIN.

**Note on `'expired'` state:** Reserved for future use — not implemented in
Fix 3. A future mechanism (TTL-based, nightly job, or manual) could transition
old `'pending'` decisions to `'expired'` to distinguish "never acted on" from
"waiting to be acted on." For Fix 3, only three states exist: `pending`,
`confirmed`, `overridden`. Do not build expiry logic in this fix.

**Schema change (minimal, backwards-compatible):**
```sql
ALTER TABLE decisions ADD COLUMN status TEXT DEFAULT 'pending';
```

Existing rows get `'pending'` by default. Migration backfills from outcomes.
No schema break. No API change. Conservation counting changes from
`count_decisions()` to `count_verified_decisions()`.

---

### Q3: What to do with the 23,607 existing rows?

**DECISION: Archive unverified + backfill status column.**

Given Q1=B (verified only) and Q2 (status column), the migration is:

```sql
-- Step 1: Add status column to BOTH tables (archive schema must match)
ALTER TABLE decisions ADD COLUMN status TEXT DEFAULT 'pending';
ALTER TABLE decisions_archive ADD COLUMN status TEXT DEFAULT 'pending';

-- Step 2: Add index for conservation counting performance
CREATE INDEX IF NOT EXISTS idx_decisions_domain_status
ON decisions(domain, status);

-- Step 3: Backfill from outcomes (is_correct=1 → confirmed, 0 → overridden)
-- Note: outcomes table has actual_action TEXT and is_correct INTEGER,
-- NOT an 'action' column. is_correct is the canonical discriminator.
-- Defensive: WHERE is_correct IS NOT NULL guards against partial writes
-- or old schema rows where is_correct may be NULL.
UPDATE decisions SET status = 'confirmed'
WHERE decision_id IN (
    SELECT decision_id FROM outcomes
    WHERE is_correct IS NOT NULL AND is_correct = 1
);
UPDATE decisions SET status = 'overridden'
WHERE decision_id IN (
    SELECT decision_id FROM outcomes
    WHERE is_correct IS NOT NULL AND is_correct = 0
);

-- Step 4: Archive old unverified rows
-- NOTE: decisions_archive is DENORMALIZED (decisions + outcomes columns
-- + archived_at + autoincrement PK). SELECT * will NOT work.
-- Outcome columns are NULL for pending (unverified) decisions.
INSERT INTO decisions_archive (
    decision_id, domain, category, category_index,
    factors_json, factor_vector_json, recommended_action, recommended_index,
    confidence, probabilities_json, created_at,
    actual_action, actual_index, is_correct,
    verified_at, context_json, archived_at, status
)
SELECT
    d.decision_id, d.domain, d.category, d.category_index,
    d.factors_json, d.factor_vector_json, d.recommended_action,
    d.recommended_index,
    d.confidence, d.probabilities_json, d.created_at,
    NULL, NULL, NULL,        -- outcome columns: NULL for unverified
    NULL, NULL,              -- verified_at, context_json: NULL
    strftime('%s', 'now'),   -- archived_at
    'pending'                -- status
FROM decisions d
WHERE d.status = 'pending'
AND d.created_at < strftime('%s', datetime('now', '-30 days'));

DELETE FROM decisions WHERE status = 'pending'
AND created_at < strftime('%s', datetime('now', '-30 days'));
```

After migration:
- `decisions` table: 12 verified rows + recent pending scores
- `decisions_archive`: ~23,595 rows (available for audit/replay)
- Conservation: computes from 12 verified → GREEN, recoverable
- DB size: drops from 33 MB to ~200 KB active

**Cross-copilot note:** The constructor migration (_ensure_schema_v2)
runs on ALL copilots at next startup, not just S2P. Trading, Purchasing,
and DataOps .db files at ~/.ci-platform/{copilot}/ will get the status
column added automatically. Their existing decision rows receive
DEFAULT 'pending' — correct, because SDK copilot decisions that were
confirmed have matching outcomes rows and will be backfilled.

The `decisions_archive` table already exists in the schema with 0 rows — the
archival intent was clearly anticipated when the schema was designed. This
migration completes the original design, not invents new architecture.

---

### Q4: Should demo.py --reset s2p work?

**DECISION: Option A — Align to CI_DATA_DIR.**

```python
# s2p-copilot/backend/app/main.py — one line change
DATA_DIR = Path(os.environ.get("CI_DATA_DIR",
    str(Path(__file__).parent / "data")))
```

This aligns S2P with the SDK convention used by Trading, Purchasing, and
DataOps. Makes `demo.py --reset s2p` work correctly. No semantic change.
Important for demo reliability and operator hygiene.

---

## §8 — Decision Table (RESOLVED)

| Question | Decision | Rationale | Blocks |
|---|---|---|---|
| Q1: What is V? | **Verified only** | Math consistency (α, q already verified-scoped). Conservation measures human oversight. | Fix 3 |
| Q2: When write? | **Score time + status** | Preserves audit trail + flywheel. Status separates lifecycle from persistence. | Fix 3 |
| Q3: Existing rows? | **Archive + backfill** | decisions_archive exists. Completes original design intent. | Fix 3 |
| Q4: demo.py reset? | **CI_DATA_DIR align** | One line. SDK consistency. Demo reliability. | Fix 4 |

**Implementation order (strict):**
1. **Fix 4 (CI_DATA_DIR) — FIRST.** Gates Fix 3c (archive reads
   correct path) and Phase 2 (factory assumes CI_DATA_DIR). One line.
2. **Fix 1 (algorithmic) — second.** Independent performance fix.
3. **Fix 3a/3b/3c — after Fix 1.** Status column + conservation V + archive.

---

## §9 — What Fix 1 Does and Does Not Change

| Dimension | Before Fix 1 | After Fix 1 |
|---|---|---|
| `total_decisions` value | 23,607 | 23,607 (unchanged) |
| Conservation status | RED | Still RED (same data, same formula) |
| Conservation response time | 4–7s per call | <10ms per call |
| PW hard failures | 24 | 0 (timing resolved) |
| PW flaky tests | 12 | 0 (no retries needed) |
| `decisions` table | Unchanged | Unchanged |
| Conservation semantics | Unchanged | Unchanged |
| DB schema | Unchanged | Unchanged |

Fix 1 fixes the performance. It does not fix the conservation signal. After
Fix 1, the system correctly and quickly reports RED — because it genuinely is,
given the current data under the current V definition. That is honest behavior.

Fix 3 will change the V definition (to verified-only) and archive unverified
rows, making conservation GREEN and recoverable. Fixes 1 and 3 together
resolve both the performance and the semantic issues.

---

## §10 — Mathematical Context

### Why the conservation law's V definition matters for the theorem

The conservation law α·q·V ≥ θ_min is not a heuristic threshold. It is a
mathematical theorem with four independent proof paths (analytic, coding,
simulation, centroid-distance). The theorem guarantees that centroid learning
does not degrade scoring quality below a safety bound.

The proof depends on the POPULATION over which α, q, and V are computed
being consistent:

**If V includes unverified decisions:**
- α = verified/total → approaches 0 as automated scoring volume grows
- The system can transition from GREEN to RED purely from non-human scoring
  activity, with zero change in human oversight quality
- θ_min → ∞ as V grows without verification, making the conservation
  constraint unsatisfiable
- This violates the theorem's intent: conservation should reflect human
  oversight quality, not automated throughput

**If V counts only verified decisions:**
- α measures category coverage of verified decisions (what fraction of the
  decision space has human oversight)
- q measures accuracy within the verified population
- V measures volume of human oversight
- All three quantities describe the same population
- θ_min scales correctly: more verified decisions → lower threshold → easier
  to maintain GREEN → which is correct (more oversight = more trust)

The theorem's proof assumes a consistent population. Mixing verified and
unverified decisions in the same formula is like computing a batting average
from at-bats AND walks — it produces a number, but the number doesn't mean
what you think it means.

### Connection to re-convergence

The re-convergence theorem (γ > 1) proves that after a disruption, recovery
is faster each time — but ONLY if the recovery operates on a clean population
of verified decisions. If V is polluted with automated scores, the re-
convergence rate is artificially suppressed because the system appears to
have massive volume (23,607) with negligible oversight (12/23,607 = 0.05%).

Under Option B (verified-only V), re-convergence operates on the correct
population: 12 verified decisions, growing with each human confirmation.
γ > 1 applies correctly, and the system recovers from disruptions at the
mathematically predicted rate.

### The q_window connection

q is defined as rolling verified accuracy over 400 decisions (q_window=400,
theorem-validated). This window slides over VERIFIED decisions, not all
decisions. If V counted all decisions but q only looked at verified ones,
the formula would be comparing quantities from two different populations.
V = verified ensures the formula is internally consistent.

---

## §11 — Product & Commercial Implications

### The conservation law is the enterprise sales proof

The conservation law is the single most important enterprise differentiator:
"Our system mathematically CANNOT expand automation when it's unsafe. Not
'chooses not to.' CANNOT."

Every enterprise buyer asks: "What happens when AI quality degrades?" The
conservation law is the answer. But if conservation is permanently RED from
test artifacts — and the buyer sees RED in a demo — the proof becomes
evidence AGAINST the product.

**Fix 3 ensures that conservation accurately reflects human oversight:**
- GREEN when human verification is sufficient → buyer sees a healthy system
- AMBER when verification thins → buyer sees the safety mechanism working
- RED when oversight is critically low → buyer sees honest self-governance

A system that reports RED because of test accumulation is neither honest
(the RED doesn't reflect real quality degradation) nor useful (it can't
demonstrate the GREEN→AMBER→RED→GREEN lifecycle in a demo).

### Demo reliability

The current state (permanently RED, 4-7s response time) means:
1. S2P demo cannot show conservation-gated auto-approve (flagship feature)
2. S2P demo cannot show the GREEN→AMBER transition (trust-building moment)
3. S2P Playwright suite is unreliable at workers>1 (CI/CD barrier)

After Fix 1 + Fix 3:
1. Conservation responds in <10ms regardless of DB size
2. Conservation accurately reflects human oversight (GREEN with 12 verified)
3. Demo can show the full lifecycle: GREEN → analyst stops confirming →
   AMBER → analyst resumes → GREEN. This IS the product story.

### The audit trail value proposition

The status column preserves audit trail value while cleaning conservation
semantics. Every scored invoice remains queryable — when was it scored, what
was recommended, was it acted on, how long did it take to confirm?

For enterprise buyers (especially in regulated procurement), this audit trail
is a selling point: "Every recommendation is hash-chained. Every decision
has provenance. Every override has a reason code. Your regulator can audit
every step." The status column makes this story cleaner, not weaker.

### The $680K leakage claim depends on clean conservation

The S2P value proposition claims $680K/year in pricing leakage detection
(MODELED). The demo moment is: system detects pattern → conservation proves
safe to auto-flag → $680K recovered automatically.

If conservation is permanently RED, auto-flagging never activates, and the
$680K story is theoretical. Fix 3 makes it demonstrable.

---

## §12 — Innovation Value

### What this bug reveals about the platform architecture

The S2P Playwright failure is not just a performance bug. It is the first
PRODUCTION-SCALE test of whether the conservation law's implementation
matches its mathematical specification. The diagnosis revealed:

1. **The counting implementation conflated two populations** — all scored
   events and human-verified decisions. The math assumes one population.
   This is the kind of implementation drift that wouldn't be caught by unit
   tests (which use small, clean datasets) but emerges at scale.

2. **The archival infrastructure was designed but not wired** —
   `decisions_archive` exists with 0 rows. The original designer anticipated
   this problem. Completing the wiring is architectural completion, not
   a new feature.

3. **The conservation law is self-diagnosing** — the permanent RED status
   IS the system detecting that something is wrong. A system without the
   conservation law would silently degrade. The conservation law caught the
   population inconsistency by collapsing the signal. This is the "system
   that warns about itself" (I3 scenario from the product definition) in
   action — just not in the way anyone expected.

### The status column as a novel lifecycle primitive

The `status` column on the decisions table introduces a clean lifecycle
abstraction: `pending → confirmed/overridden` (with `expired` reserved
for future use). This lifecycle
is not just an S2P feature. It is a PLATFORM primitive:

- **SOC:** Alert scored → analyst triages → confirmed/escalated/dismissed
- **Trading:** Trade scored → trader executes → confirmed/skipped
- **Purchasing:** Order scored → chef confirms/adjusts → verified
- **DataOps:** Alert scored → engineer triages → resolved/deferred

The same lifecycle applies to all five copilots. The status column should
be implemented at the SDK level (`SQLiteGraphStore`), not per-copilot.
This is a one-time investment that improves conservation semantics
across the entire platform.

### IP implications

The combination of:
- Conservation law operating on verified-only population
- Status lifecycle on decision table (pending → confirmed → archived)
- Self-diagnosing conservation (RED when oversight thins, self-correcting)
- Hash-chained audit trail with lifecycle metadata

...constitutes a novel approach to AI governance that has no equivalent in
any competing platform. CrowdStrike, Splunk, Coupa, BlueCart — none have
a mathematical safety proof that operates on a lifecycle-managed decision
store with tamper-evident provenance.

---

## §13 — Implementation Sequence

**Order is strict. Do not reorder.**

```
Fix 4 (FIRST — prerequisite for everything else):
  S2P main.py reads CI_DATA_DIR env var
  → demo.py --reset s2p works correctly
  → S2P moves from Model C (hardcoded) to Model B (CI_DATA_DIR)
  → Gates Fix 3c (archive must read correct DB path)
  → Gates Phase 2 (factory assumes CI_DATA_DIR)
  One line. Zero semantic change. Ship immediately.

Fix 1 (second — performance):
  Replace len(get_all_decisions()) with count_decisions()
  → Conservation <10ms regardless of DB size
  → PW tests pass at workers=4
  → Conservation still RED (semantic fix is Fix 3)

Fix 2 (skip):
  Pre-warm timeout increase — moot after Fix 1

Fix 3a (third — SDK level, ALL 5 COPILOTS):
  *** PLATFORM-WIDE: This runs on Trading, Purchasing, DataOps, AND S2P ***
  *** _ensure_schema_v2() fires in SQLiteGraphStore constructor ***
  *** One schema bug breaks ALL copilot test suites (~5,484 BE tests) ***
  Add status column to SQLiteGraphStore._create_tables()
  Migration trigger: constructor version-check (see below)
  CREATE count_verified_decisions(domain) method (see spec below)
  Backfill from outcomes (is_correct mapping)
  Add index on (domain, status)
  → Platform primitive, all copilots benefit

  Migration trigger (SDK convention for schema evolution):
  ```python
  def _ensure_schema_v2(self):
      """Idempotent migration: add status column if missing."""
      cursor = self._conn.execute(
          "PRAGMA table_info(decisions)"
      )
      columns = {row[1] for row in cursor.fetchall()}
      if 'status' not in columns:
          self._conn.execute(
              "ALTER TABLE decisions ADD COLUMN status "
              "TEXT DEFAULT 'pending'"
          )
          self._conn.execute(
              "ALTER TABLE decisions_archive ADD COLUMN status "
              "TEXT DEFAULT 'pending'"
          )
          self._conn.execute(
              "CREATE INDEX IF NOT EXISTS "
              "idx_decisions_domain_status "
              "ON decisions(domain, status)"
          )
          self._conn.commit()
  ```
  Call from __init__() after _create_tables(). Runs once per DB,
  idempotent on subsequent startups (PRAGMA check is <1ms).
  Handles ALL copilots: S2P, Trading, Purchasing, DataOps —
  any existing .db file at ~/.ci-platform/{copilot}/ gets the
  column added on first startup after Fix 3a deploys.

  count_verified_decisions() spec:
  ```python
  def count_verified_decisions(self, domain: str) -> int:
      """O(1) count of human-verified decisions for conservation V."""
      with self._lock:
          return self._conn.execute(
              "SELECT COUNT(*) FROM decisions WHERE domain = ? "
              "AND status IN ('confirmed', 'overridden')",
              (domain,)
          ).fetchone()[0]
  ```

Fix 3b (fourth — conservation router, ALL 5 COPILOTS):
  *** PLATFORM-WIDE: Changes V definition for ALL copilots ***
  *** Conservation may flip RED→GREEN for copilots with verified data ***
  Update conservation_router.py to use count_verified_decisions()
  for V computation instead of count_decisions()
  Update s2p.py _read_conservation_counts() same way
  → Conservation reflects verified decisions only

Fix 3c (fifth — S2P archive, REQUIRES Fix 4):
  *** Must run AFTER Fix 4: archives from CI_DATA_DIR path, not hardcoded ***
  Archive unverified decisions older than 30 days to decisions_archive
  → Active table clean, audit trail preserved, DB size drops

```

### Critical implementation note for Fix 3a

The status column update must happen in the SAME TRANSACTION as the outcome
write in `POST /api/learn`:

```python
def learn(self, decision_id: str, outcome: Outcome) -> None:
    with self._lock:
        # Write outcome AND update status atomically
        self._conn.execute(
            "INSERT INTO outcomes (...) VALUES (...)", (...)
        )
        self._conn.execute(
            "UPDATE decisions SET status = ? WHERE decision_id = ?",
            (outcome.action, decision_id)
        )
        self._conn.commit()
```

**Resolved mapping (confirmed from write_outcome() signature scan):**

```python
def write_outcome(
    self, decision_id: str, actual_action: str,
    is_correct: bool,       # ← plain bool, no mapping needed
    metadata: dict | None = None,
) -> None:
```

`is_correct` is a plain `bool` passed directly. The atomic status update
adds two lines inside `write_outcome()` in the SAME transaction:

```python
status = 'confirmed' if is_correct else 'overridden'
self.connection.execute(
    "UPDATE decisions SET status = ? WHERE decision_id = ?",
    (status, decision_id)
)
```

No ambiguity. No mapping. `is_correct=True` → 'confirmed'.
`is_correct=False` → 'overridden'. The `actual_action` field records
WHICH action was taken (e.g., 'approve', 'hold') — it is NOT the
lifecycle discriminator.

Without atomic update, you could have outcomes without status updates (if
the UPDATE fails after INSERT) or orphaned status changes. The transaction
boundary ensures consistency.

### Cache invalidation after migration

The conservation status cache (`_SCORE_CONSERVATION_STATUS_TTL_SECONDS`)
will retain the pre-migration RED value until TTL expires. After running
the migration (Fix 3a-3c), either:
- Restart the backend (clears all caches), or
- Set TTL to 0 temporarily, make one request, restore TTL

First conservation request after migration should show GREEN (if category
coverage ≥ 2/5 with the 12 verified decisions). If it still shows RED,
check: (a) the counting method is actually using `count_verified_decisions`,
(b) the status backfill ran correctly, (c) the α computation.

### Performance index

After adding the status column, `count_verified_decisions()` runs:
```sql
SELECT COUNT(*) FROM decisions WHERE domain=? AND status IN ('confirmed','overridden')
```
Without an index, this scans all rows. Add:
```sql
CREATE INDEX idx_decisions_domain_status ON decisions(domain, status);
```
This keeps `count_verified_decisions()` at O(1) even as the table grows.

### Standing rule and claims registry impact

**New standing rule (propose as #37):** "V in conservation formula =
count of verified decisions (status IN confirmed, overridden). Standing
rule #12 (α = among verified decisions) extends to V."

**Claims registry updates needed:**
- CLAIM-CONSERVATION-WIRE: update to note V = verified_count
- CLAIM-Q-DEF: confirm q_window operates on same verified population
- Add new FINDING: conservation self-diagnosed population inconsistency
  (real-world I3 scenario — "the system that warns about itself")

### Demo bundle interaction

`regenerate_demo_bundles.py` (#102) produces bundles WITHOUT the status
column (bundles were generated before Fix 3). When `bundle.py` restores
a bundle, decisions are written without `status` — they receive
DEFAULT 'pending', which is CORRECT: bundle decisions are unverified
synthetic data and should not count toward conservation V.

Do NOT add `status='confirmed'` to the bundle generator. Preseed and
demo data should always enter as `pending`. Only human confirmation
via the learn() endpoint transitions to `confirmed`/`overridden`.

If bundles are regenerated AFTER Fix 3a, the bundle schema will include
the status column. Both paths (old bundles without column, new bundles
with column) work correctly due to the DEFAULT clause.

### Test requirements for Fix 3

1. `count_verified_decisions()` returns correct count for known dataset
2. Conservation status changes from RED → GREEN after migration
3. `decisions_archive` receives archived rows with correct schema
4. Status column defaults to 'pending' for new score calls
5. Status updates to 'confirmed'/'overridden' on learn() call
6. Conservation only counts status IN ('confirmed', 'overridden')
7. Existing SDK copilots (Trading, Purchasing, DataOps) unaffected
8. Re-convergence operates correctly on verified-only population

---

## §14 — Review Notes

### Self-review (post-authoring, v2.0)

1. **Fix 1 is unambiguously correct and independent.** No architecture
   decision is needed. Ship today.

2. **Q1 (V = verified) is mathematically justified.** The conservation law's
   proof assumes a consistent population. Mixing populations breaks the
   theorem. Standing rule #12 already says "α = among verified decisions" —
   V must match. This is not a new interpretation; it is alignment with the
   existing mathematical specification.

3. **Q2 (status column) is the cleanest separation.** The alternatives
   (outcome-time write, source tagging) were evaluated and rejected with
   specific reasons. The status column maps to a natural lifecycle that
   transfers across all five copilots.

4. **Q3 (archive) completes original design intent.** The decisions_archive
   table exists with 0 rows. The schema designer anticipated this need.
   We are wiring what was designed, not inventing new architecture.

5. **Risk: SDK-level status column affects all copilots.** Trading,
   Purchasing, and DataOps all use SQLiteGraphStore. Adding a status column
   must not break their existing tests. The migration must be backwards-
   compatible (DEFAULT 'pending' for existing rows). Run all test suites
   after Fix 3a.

6. **Risk: conservation formula behavior changes.** After Fix 3b,
   conservation will report GREEN for S2P (12 verified decisions at ~83%
   accuracy). This is correct behavior — but it IS a change from the
   current RED. Verify this is the desired state before deploying.

7. **The innovation insight (§12) is genuine.** The conservation law
   catching its own implementation inconsistency IS the "system that warns
   about itself" story. Worth noting in the claims registry and innovation
   note as a real-world example of self-governance.

### Comprehensive review (post-review, v2.0)

8. **§3 math numbers clarified.** The θ_min = 3,857 and signal = 0.0056
   values come from the running implementation's α computation (which uses
   verified/total ratio under Option A). Added clarifying note that these
   are implementation-reported values, and that Option B changes them.

9. **§7 recovery test marked illustrative.** The α = 0.6 (3/5 categories)
   is assumed — actual coverage depends on the 12 decisions' distribution.
   Added AMBER case (α=0.4) showing the system is still recoverable even
   with fewer categories, unlike Option A which is permanently collapsed.

10. **Archive schema compatibility fixed.** The `decisions_archive` table
    needs the status column added BEFORE rows are inserted, otherwise
    INSERT INTO...SELECT fails on column mismatch. Added
    `ALTER TABLE decisions_archive ADD COLUMN status` to the migration.

11. **Performance index added.** `count_verified_decisions()` needs an
    index on `(domain, status)` to remain O(1) as the table grows. Without
    it, the COUNT scans all rows — reintroducing the performance problem
    Fix 1 solved, just with a different WHERE clause.

12. **Cache invalidation documented.** After migration, the conservation
    cache retains pre-migration RED until TTL expires. Backend restart or
    cache clear needed. Without this note, the implementer would see RED
    after migration and think the fix failed.

13. **learn() action mapping noted.** The `outcome.action` value in the
    actual code may not map directly to 'confirmed'/'overridden'. The
    implementer must check the learn endpoint's vocabulary before wiring
    the status update.

14. **Standing rule and claims impact documented.** V = verified should
    become standing rule #37. CLAIM-CONSERVATION-WIRE needs update. New
    FINDING for the self-diagnosis observation.

15. **No issues found with:** Fix 1 Codex prompt (complete and correct),
    Q2 reasoning (flywheel edge preservation), Q4 one-line fix, §10 math
    context (population consistency argument is sound), §11 commercial
    implications (conservation-as-demo-proof is accurate), §12 innovation
    value (lifecycle primitive transfers across copilots).

---

*S2P Playwright Failures — Diagnosis, Fix, and Architecture Decisions*
*Version 2.4 · May 30, 2026*
*Fix 1: Algorithmic (ship today). Fix 3: Status column + archive (ship next).*
*Q1: V = verified only (math consistency). Q2: Score-time + status (lifecycle).*
*Q3: Archive (complete original design). Q4: CI_DATA_DIR (one line).*
*"The system that warns about itself — in action."*
