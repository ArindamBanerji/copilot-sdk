# Campaign Phase 3 — Async Seed Materialization

**Version:** 1.4
**Date:** June 15, 2026
**Status:** Roadmap-approved — ready for Codex prompt
**Trigger:** 1b-2 closeout M2 p95 = 215ms vs 5ms budget (43x over)
**Depends on:** 1b-2 (CLOSED_FOR_CORRECTNESS)

---

## §1 — Why Phase 3 Exists

### 1.1 The 1b-2 Closeout Data

Campaign 1b-2 shipped correct, race-safe seed materialization
with advisory-lock + MATCH-then-CREATE. The graph integrity is
clean:

| Metric | Result |
|---|---|
| Duplicate seed keys | **0** |
| CONTINUES edges | **0** |
| BELONGS_TO edges | **0** |
| Campaign nodes | 151 → 152 |
| MEMBER_OF edges | 506 → 508 |
| Backend tests | 1952 passed, 14 skipped |
| GPT-5.5 review | PASS (P3 orphan caveat only) |

**But the latency fails the hot-path budget:**

| Measurement | Fresh | Pooled | Budget |
|---|---|---|---|
| M2 campaign total p95 | 176ms | **215ms** | 5ms |
| M3 seed materialization p95 | 202ms | **229ms** | 3ms |

Pooling made it WORSE, not better — the bottleneck is the AGE
write operation itself, not connection setup. This is not
optimizable with query tuning. 215ms → 5ms requires an
architecture change.

### 1.2 The Architecture Split

The insight from the data: campaign work has two parts with
fundamentally different latency profiles:

```
CHECK (read-only):
  "Does this alert match an existing campaign?"
  → MATCH query against Campaign + MEMBER_OF
  → estimated ~2ms (pre-1b-2 baseline)
  → MUST stay on hot path

MATERIALIZE (write):
  "Persist the seed / promote to campaign / add MEMBER_OF"
  → advisory lock + MATCH-then-CREATE
  → measured 215ms at p95
  → MUST move off hot path
```

Phase 3 moves the WRITE off the hot path. The READ stays.

### 1.3 What Phase 3 Is NOT

| Not this | Why |
|---|---|
| A 1b-2 fixer | 1b-2 is correct. Phase 3 is an architecture change. |
| Query optimization | 215ms → 5ms isn't achievable through SQL/Cypher tuning |
| CONTINUES edges | Phase 4 scope |
| v6.0 scorer integration | Separate design (context injection) |
| v7.0 tensor expansion | Separate design (needs 90d override-rate data) |
| Queue infrastructure | v1 uses asyncio.create_task, not a queue |
| Frontend changes | No UI in Phase 3 |

---

## §2 — The Design

### 2.1 Before Phase 3 (Current — Synchronous)

```
analyze(alert)
  └→ check_alert(alert_id)        # ~215ms total (read + write)
       ├→ check membership         # ~2ms (read)
       └→ materialize_seed()       # ~213ms (write, advisory lock)
            └→ return campaign match
  └→ scorer.score(...)
  └→ return response               # blocked until write completes
```

The analyst waits for the AGE write to complete before seeing
the score. Every analyze call pays the 215ms tax.

### 2.2 After Phase 3 (Async — Fire-and-Forget)

```
analyze(alert)
  └→ check_alert(alert_id)        # ~2ms (read-only)
       ├→ check membership         # ~2ms (read)
       └→ if should_materialize AND seed_key not pending:
            task = create_task(    # fire-and-forget
              materialize_in_background(alert_id)
            )
            _bg_tasks.add(task)    # prevent GC
            task.add_done_callback(_bg_tasks.discard)
       └→ return campaign match    # immediate
  └→ scorer.score(...)
  └→ return response               # ~2ms campaign overhead

  [background, after response sent:]
  materialize_in_background(alert_id)
       └→ materialize_seed()       # 215ms (advisory lock)
       └→ finally: _pending_seeds.discard(seed_key)
```

The analyst sees the score immediately. The seed materializes in
the background after the response is sent.

### 2.3 Why `asyncio.create_task()` (Not a Queue)

| Option | Complexity | Multi-worker | Demo/pilot fit | Production fit |
|---|---|---|---|---|
| **E: create_task** | **3 lines** | No (single process) | **Perfect** | Insufficient |
| A: in-process async queue | Queue class + consumer | No | Over-engineered | Marginal |
| B: DB-backed outbox | Table + poller + consumer | Yes | Over-engineered | Good |
| C: AGE-backed job node | Graph writes for jobs | Yes | Circular (writes cause the problem) | Bad |
| D: Repo task mechanism | Framework dependency | Maybe | Unknown | Unknown |

**Recommendation:** Option E for v1. The platform is demo/pilot
stage. `asyncio.create_task()` is 3 lines of code, zero
infrastructure, and the materialization is IDEMPOTENT (1b-2's
advisory lock handles duplicates). Upgrade to outbox when
multi-worker production deployment requires it.

The production upgrade path is a separate roadmap item (P-CAMP-
OUTBOX or similar), not Phase 3 scope. Phase 3 proves the
architecture works. Production hardening follows.

---

## §3 — Implementation

### 3.1 The Core Change (~35 lines)

```python
# backend/app/domains/soc/campaigns.py
import asyncio
import logging

logger = logging.getLogger(__name__)

class CampaignEngine:  # or whatever the actual class name is
    def __init__(self, ..., background: bool = True):
        ...
        self._background = background  # False in tests
        # Task retention: prevent GC of fire-and-forget tasks.
        # asyncio.create_task() holds only a WEAK reference —
        # without this set, tasks can be garbage-collected before
        # completing, silently losing the materialization.
        self._bg_tasks: set[asyncio.Task] = set()
        # Storm dedup: prevent N tasks for the same seed key.
        # Without this, a 100-alert storm spawns 100 background
        # tasks all serializing on the same advisory lock.
        self._pending_seeds: set[str] = set()

    async def check_alert(self, alert_id: str) -> CampaignMatch | None:
        """HOT PATH: read-only campaign membership check.
        Materialization happens in background — never blocks the response."""
        
        # 1. READ-ONLY: does this alert match an existing campaign?
        match = await self._check_membership(alert_id)
        
        # 2. BACKGROUND: fire-and-forget seed materialization
        if self._should_materialize(alert_id, match):
            seed_key = self._compute_seed_key(alert_id, match)
            if self._background:
                if seed_key not in self._pending_seeds:
                    self._pending_seeds.add(seed_key)
                    task = asyncio.create_task(
                        self._materialize_in_background(
                            alert_id, match, seed_key)
                    )
                    # Prevent GC: strong reference until done
                    self._bg_tasks.add(task)
                    task.add_done_callback(self._bg_tasks.discard)
                # else: another task already pending for this seed — skip
            else:
                # Synchronous mode (tests): same logic, inline execution
                await self._materialize_in_background(
                    alert_id, match, seed_key)
        
        # 3. RETURN IMMEDIATELY (response not blocked by write)
        return match

    async def _materialize_in_background(self, alert_id: str,
                                          match: CampaignMatch | None,
                                          seed_key: str):
        """Runs AFTER the response is already sent (in background mode).
        No latency impact on the analyst. 215ms is fine here.
        Idempotent: advisory lock + MATCH-then-CREATE from 1b-2.
        
        Advisory lock is transaction-scoped (PostgreSQL releases on
        connection close) — a crashed task cannot strand a lock."""
        try:
            await self._materialize_seed(alert_id)
        except Exception as e:
            logger.warning(
                f"Background campaign materialization failed for "
                f"alert={alert_id} seed={seed_key}: {e}"
            )
        finally:
            self._pending_seeds.discard(seed_key)
```

### 3.2 The Rapid Second-Alert Question (Resolved by Idempotency)

```
Alert A arrives → check (no match) → enqueue materialize(seed-X)
Alert B arrives 50ms later → check (no match yet) → enqueue materialize(seed-X)

Background processes A → advisory lock → seed-X created → MEMBER_OF added
Background processes B → advisory lock → seed-X exists → no-op (idempotent)

Result: exactly 1 seed node. Both alerts eventually linked.
```

This is not a design decision — it's a consequence of 1b-2's
advisory lock. The MATCH-then-CREATE pattern handles concurrent
materialization correctly. Phase 3 doesn't need a separate
"rapid second-alert strategy."

**The only trade-off:** Alert B's `check_alert()` returns null
(no campaign match yet) because the seed isn't materialized.
The analyst sees alert B without campaign context for ~215ms.
This self-heals on the next check.

**DECISION: Include pending-seed in-memory check NOW.**

The in-memory pending-seed check is low-risk (~0ms, reads from
`self._pending_seeds` set, no AGE query) and protects the demo
campaign-forming beat. Include unless Codex proves it distorts
existing campaign match semantics.

```python
async def _check_membership(self, alert_id):
    # Check materialized campaigns first (fast, indexed)
    match = await self._check_materialized(alert_id)
    if match:
        return match
    # Check pending seeds (in-memory, ~0ms)
    return self._check_pending_seeds(alert_id)
```

The pending check returns a PROVISIONAL match — the campaign
isn't materialized yet, but the system knows a seed is in
progress. The analyst sees campaign context immediately instead
of a flicker.

### 3.3 Error Handling and Convergence Guarantee

| Failure | Consequence | Recovery |
|---|---|---|
| Background task exception | Seed not materialized | Next alert for same campaign retries (idempotent) |
| AGE connection failure | Same | Same |
| Advisory lock timeout | Same | Same — lock is transaction-scoped, released on connection close |
| Process crash during background task | Seed not materialized | **No startup reconciliation in v1** — see gaps below |
| Duplicate background tasks | Seed-key dedup prevents spawning; advisory lock deduplicates if spawned | Zero data inconsistency |

**Honest convergence guarantee:**

The system self-heals IF another alert for the same campaign seed
arrives after a failure. This covers the common case (campaigns
grow because alerts keep arriving).

**Two gaps in v1 (accepted for demo/pilot):**

1. **Singleton/terminal seeds:** A seed created by a single alert
   with no follow-up has no future retry. If its background task
   fails (GC'd, exception, crash), the seed is NEVER materialized.
   The task-set retention (#1 fix above) eliminates the GC case.
   Exception and crash remain as low-probability gaps.

2. **Crash recovery:** Nothing on startup proactively re-materializes
   pending seeds. Seeds orphaned by a crash sit unmaterialized until
   a new matching alert happens to arrive. There is no startup
   reconciliation pass in v1.

**Mitigation (production, not v1):** A startup sweep over
un-materialized seed keys — the same reconciliation-job pattern
used elsewhere in the platform. Add as a production hardening
item alongside the outbox upgrade.

The v1 guarantee is: "self-heals if another alert for the same
seed arrives; singleton/terminal seeds and crash-orphaned seeds
rely on the background task succeeding. No startup reconciliation."
This is acceptable for demo/pilot where crash recovery is manual.

### 3.4 Worker Lifecycle

```python
# No separate worker process needed for v1.
# create_task runs inside the existing FastAPI event loop.
# Background tasks complete after the response is sent.

# Shutdown: FastAPI's shutdown handler cancels pending tasks.
# Any in-flight materialization is abandoned — idempotent
# retry on next startup handles it.

# Tests: inject background=False to run materialization
# synchronously (same logic, synchronous execution path).
# This avoids asyncio.sleep() flakiness:
#
#   engine = CampaignEngine(..., background=False)
#   # materialize runs inline, same as pre-Phase-3
#   # but the production path uses create_task
```

---

## §4 — What to Measure (Phase 3 Closeout)

### M8 — check_alert READ-ONLY Latency (The Critical Measurement)

This is the measurement that proves Phase 3 worked. After
stripping the write from the hot path, what's the actual
read-only campaign check latency?

**Two assumptions that must hold for M8 ≤ 5ms:**

1. **The membership read must be O(1) keyed, not O(N) scan.**
   There are 152 campaigns and 508 MEMBER_OF edges, growing.
   If `_check_membership` scans all campaigns rather than doing
   an indexed lookup by seed key, it regresses at pilot scale
   (250+ campaigns). The Codex discovery step MUST verify:
   ```
   grep -n "_check_membership\|MATCH.*Campaign\|MATCH.*MEMBER_OF" \
     backend/app/domains/soc/campaigns.py
   ```
   If the query is a full scan, add an index or keyed lookup
   BEFORE measuring M8.

2. **The read must go through the pooled AGE adapter.**
   The 1b-2 data showed pooled point read ≈ 1.2ms vs unpooled
   ≈ 83ms. The "pooling made it worse" finding applies to the
   WRITE (advisory lock + WAL fsync, where pooling adds checkout
   overhead). The READ is the opposite: it NEEDS the pool to
   hit ≤ 5ms. Make "read goes through pooled adapter" an explicit
   requirement.

**Measure at current graph size. Report campaign count. Do NOT
block on synthetic pilot-scale seeding.**

```python
latencies = []
for _ in range(100):
    start = time.perf_counter_ns()
    result = await campaign_matcher.check_alert(test_alert_id)
    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
    latencies.append(elapsed_ms)

m8 = {
    "measurement": "M8_check_alert_read_only",
    "n": 100,
    "p50_ms": statistics.median(latencies),
    "p95_ms": sorted(latencies)[94],
    "p99_ms": sorted(latencies)[98],
    "campaign_count": current_campaign_count,  # report actual
    "connection_mode": "pooled",  # MUST be pooled
    "read_is_keyed": True_or_False,  # discovery step confirms
}
```

**Target: p95 ≤ 5ms on pooled connection.**
Report the actual campaign count at measurement time. If the
read is NOT O(1) keyed (discovery step reveals a scan), add an
index or keyed lookup BEFORE measuring. Do not fabricate a 250+
campaign graph — measure what exists and report honestly.

### M9 — Background Materialization Latency

Same as M3 from 1b-2, but now measured as a background operation.
No budget target — it runs after the response is sent. Measured
for observability only.

### M10 — End-to-End Convergence Time

How long from "alert arrives" to "seed is visible to the next
check_alert call"?

```python
# Fire alert A → check returns null
# Background materializes seed → ~215ms
# Fire alert B → check returns campaign match
# Convergence time = time between A's arrival and B's match

start = time.perf_counter_ns()
await campaign_matcher.check_alert(alert_a)  # no match
await asyncio.sleep(0.5)  # wait for background
match = await campaign_matcher.check_alert(alert_b)  # should match
convergence_ms = (time.perf_counter_ns() - start) / 1_000_000
```

**Target: < 500ms.** Not a hard gate — just confirms that the
background task completes in a reasonable window.

### Closeout Report Template

```
=== CAMPAIGN PHASE 3 CLOSEOUT REPORT ===

M8 check_alert READ-ONLY (hot path):
  p50: ___ms  p95: ___ms  p99: ___ms
  Connection mode: pooled / unpooled
  Campaign count at measurement: ___
  Budget: ≤ 5ms at p95
  VERDICT: PASS / FAIL

M9 Background materialization (off-path):
  p50: ___ms  p95: ___ms  p99: ___ms
  (no budget — observability only)

M10 Convergence time:
  Alert A → background → Alert B sees campaign: ___ms
  Target: < 500ms

Graph integrity:
  Duplicate seed keys: ___  (MUST be 0)
  CONTINUES edges: ___      (MUST be 0)
  BELONGS_TO edges: ___     (MUST be 0)

Async mechanism verification:
  Task retention (GC proof): PASS / FAIL
  Seed-key dedup (storm → 1 task): PASS / FAIL
  Done-callback cleanup (_bg_tasks empty after): PASS / FAIL
  Background failure isolation: PASS / FAIL

TEST RESULTS:
  Correctness tests (background=False): ___ passed, ___ failed
  Async mechanism tests (background=True): ___ passed, ___ failed
  Existing campaign tests: ___ passed, ___ failed
  Full SOC backend suite: ___ passed, ___ failed

=== END CLOSEOUT REPORT ===
```

---

## §5 — Files Changed

```
Modify:
  backend/app/domains/soc/campaigns.py
    - check_alert() → read-only hot path + create_task
    - Add background flag (True in prod, False in tests)
    - _materialize_in_background() → async wrapper with try/except
    - _check_membership() → extracted read-only path
      (may already exist, may need extraction from check_alert)
    - import asyncio, logging at top

  backend/app/routers/triage.py
    - ONLY IF discovery step 2 (§9, Stage 1) shows triage
      depends on materialization being complete before using
      the result. Check: does triage read campaign membership
      data AFTER check_alert returns? If it only uses the
      match/null return value, NO CHANGE needed.

Create:
  backend/tests/test_campaign_phase3_async.py
    - Test gates from §6
    - Materialization correctness tests: background=False
    - Async mechanism tests: background=True (task retention,
      seed-key dedup, storm convergence, failure isolation,
      done-callback cleanup)
    - Hot-path timing test: background=True (check_alert < 5ms
      while background task is still running)

Do NOT modify:
  - scorer / ProfileScorer
  - conservation / DK
  - GraphStore protocol
  - frontend
  - any other copilot
  - 1b-2's materialize_seed / write_campaign logic
    (Phase 3 changes WHEN, not HOW)
```

### Blast Radius

| Change | Files | Risk |
|---|---|---|
| check_alert split (read vs write) | 1 | LOW — same logic, split into sync read + async write |
| create_task wrapper | 1 | LOW — 3 lines |
| Tests | 1 new | ZERO — additive |
| Total | 2-3 files | LOW |

---

## §6 — Test Gates

**Materialization correctness tests (background=False):**

These test the LOGIC (unchanged from 1b-2). Use `background=False`
so materialization runs inline and assertions are deterministic:

- check_alert returns correct match when campaign exists
- check_alert returns null when no campaign exists
- Materialization creates seed node correctly
- Materialization is idempotent (duplicate calls → 1 seed node)
- MEMBER_OF edges correct after materialization

**Async mechanism tests (background=True — REQUIRED):**

These test the CONCURRENCY BEHAVIOR that IS Phase 3. They CANNOT
run with `background=False` because that path doesn't exercise
the task set, GC protection, or seed-key dedup:

- **Task retention:** Fire N alerts → all N tasks in `_bg_tasks`
  set → all complete (catches GC bug). Assert `_bg_tasks` is
  empty after all tasks finish (done_callback cleanup).
- **Seed-key dedup:** Fire 100 alerts for the same campaign seed
  → exactly 1 background task spawned (not 100). Assert
  `len(engine._bg_tasks) == 1` during the storm.
- **Storm convergence:** After the storm's single task completes,
  exactly 1 seed node exists, zero duplicates.
- **Background failure logged:** Inject a failing materialize_seed
  → `logger.warning` called → check_alert response unaffected.
- **Background exception isolation:** Inject a raising
  materialize_seed → event loop continues (no crash, no
  unhandled exception).
- **Done callback cleanup:** After task completes (success or
  failure), task is removed from `_bg_tasks` and seed_key is
  removed from `_pending_seeds`.

**Pending-seed in-memory check tests:**

- Alert B arrives while seed-X is pending → check_alert returns
  provisional campaign match (not null)
- Provisional match includes seed_key and "pending" status
- After background task completes, subsequent check returns
  materialized match (not provisional)
- Pending-seed check does NOT distort which campaign an alert
  matches (only supplements when no materialized match exists)
- Pending-seed set is empty after all background tasks complete

**Hot-path timing test (background=True):**

- check_alert returns in < 5ms (M8 target) while background
  task is still running. Assert elapsed < 5ms AND background
  task is in `_bg_tasks` (not yet complete).

**Graph integrity tests:**

- Zero duplicate seed keys after concurrent materialization
- Zero CONTINUES edges
- Zero BELONGS_TO edges
- MEMBER_OF edges correct after background completion

**Regression tests:**

- All existing campaign tests pass (zero regressions)
- Full SOC backend suite passes

---

## §7 — Relationship to v6.0 and v7.0

Phase 3 is the performance prerequisite for v6.0 context
injection. Without Phase 3, adding a campaign context read
to the situation builder adds latency to an already-overbudget
path. With Phase 3, the hot path is ≤ 5ms and the context
builder can safely add a campaign membership read (~2ms).

```
Phase 3 ships → hot path ≤ 5ms
  └→ v6.0 context injection → adds ~2ms campaign read
       → total hot path ≤ 7ms (acceptable)
       → analyst sees campaign context
       → override-rate data accumulates
         └→ v7.0 tensor expansion (if signal exists)
```

Phase 3 does NOT include v6.0 or v7.0. It only proves that the
hot path is fast enough to support them later.

### 1b-2 Compatibility Properties (Preserved)

Phase 3 reuses 1b-2's materialization logic unchanged. The
advisory lock, MATCH-then-CREATE, seed-to-campaign promotion,
and MEMBER_OF edge creation are all inherited. Phase 3 only
changes WHEN the materialization runs (synchronous → background),
not HOW it works.

The seed node properties required for v6.0/v7.0 compatibility
(campaign_id, size, first_seen, category from the scorer
integration design) are already present from 1b-2.

---

## §8 — Decisions for Roadmap

### Roadmap Decisions (Confirmed)

| # | Question | Decision | Status |
|---|---|---|---|
| 1 | Close 1b-2 for correctness? | **YES** — zero duplicates, zero forbidden edges, tests pass | CONFIRMED |
| 2 | Trigger Phase 3? | **YES** — 215ms p95 vs 5ms budget, 43x over | CONFIRMED |
| 3 | Queue mechanism? | **create_task with task-set retention + seed-key dedup.** Confirmed for demo/pilot. Outbox deferred to production hardening. | **CONFIRMED** |
| 4 | Rapid second-alert strategy? | **Seed-key dedup prevents spawning duplicates. Idempotent lock catches any that slip through.** | CONFIRMED |
| 5 | Pending-seed in-memory check? | **INCLUDE NOW.** In-memory, low-risk, protects the demo beat. Codex should include unless it proves the check distorts existing campaign match semantics. | **CONFIRMED** |
| 6 | M8 scale requirement? | **Measure at current graph size. Report campaign count. Verify read is pooled + O(1) keyed.** Do NOT block implementation on synthetic 250-campaign seeding. Do NOT fake pilot-scale data. | **CONFIRMED** |
| 7 | Another 1b-2 latency fixer? | **NO** — 215ms → 5ms needs architecture, not optimization | CONFIRMED |

---

## §9 — Codex Prompt

```
WORKING DIRECTORY: gen-ai-roi-demo-v4-v50
ACTIVATE:
  & "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\proj-envs\python_expts_venv\Scripts\Activate.ps1"
TASK: Campaign Phase 3 — move seed materialization off the
  synchronous analyze hot path into asyncio background.
TASK TYPE: Modify existing campaign code + add tests.

Stage 1 (discovery — do FIRST):
  1. Find the current check_alert implementation:
     grep -rn "check_alert\|check_membership\|materialize_seed" \
       backend/app/domains/soc/campaigns.py

  2. Find what triage.py does with the check_alert result:
     grep -rn "check_alert\|camp_matcher\|campaign" \
       backend/app/routers/triage.py
     QUESTION: does triage.py depend on materialization being
     COMPLETE before using the result? If yes, Phase 3 changes
     triage.py. If no (it only uses the match/null return),
     triage.py is unchanged.

  3. Find the materialize/seed write path:
     grep -rn "materialize\|write_campaign\|create_task" \
       backend/app/domains/soc/campaigns.py
     Identify which method does the AGE write (advisory lock +
     MATCH-then-CREATE). This is the method that moves to
     background.

  4. Check existing test structure:
     ls backend/tests/test_campaign_*.py
     Read test names. Phase 3 tests must not break existing ones.

Modify:
  backend/app/domains/soc/campaigns.py
    - Split check_alert into:
      (a) synchronous read-only membership check (HOT PATH)
      (b) asyncio.create_task fire-and-forget materialization
    - check_alert returns IMMEDIATELY after the read
    - _materialize_in_background wraps existing materialize
      logic in try/except with logger.warning on failure
    - import asyncio at top of file
    - Existing materialize_seed / write_campaign logic UNCHANGED
      (Phase 3 changes WHEN it runs, not HOW)

  backend/app/routers/triage.py
    - ONLY IF discovery step 2 shows triage depends on
      materialization being complete. Otherwise: NO CHANGE.

Create:
  backend/tests/test_campaign_phase3_async.py
    - Test gates from the design document §6

TEST APPROACH for background tasks:
  Do NOT use asyncio.sleep() to wait for background tasks in
  tests — that creates flakiness. Instead:

  Option A (preferred): inject a synchronous materialization
  path for CORRECTNESS tests:
    campaign_engine = CampaignEngine(..., background=False)
    # When background=False, materialize runs synchronously

  Option B: for ASYNC MECHANISM tests, use background=True
  and await all tasks in the _bg_tasks set:
    engine = CampaignEngine(..., background=True)
    await engine.check_alert(alert_id)
    # Wait for background tasks to complete:
    await asyncio.gather(*engine._bg_tasks)
    # Then assert materialization results + task set empty

  Use Option A for materialization correctness tests.
  Use Option B for async mechanism tests (task retention,
  seed-key dedup, storm, failure isolation).

NON-NEGOTIABLES:
  - check_alert must return in < 5ms (M8 target)
  - check_alert READ must go through POOLED AGE adapter
  - check_alert READ must be O(1) keyed lookup, not O(N) scan
    (verify in discovery step 1 — add index if scan)
  - INCLUDE pending-seed in-memory check: _check_membership
    tries materialized campaigns first, then _pending_seeds set.
    Do NOT distort existing campaign match semantics — if the
    pending check would change which campaign an alert matches,
    skip it and document why.
  - Materialization uses EXISTING 1b-2 advisory lock logic
    unchanged — do not rewrite the write path
  - Advisory lock is transaction-scoped (released on connection
    close — crashed tasks cannot strand a lock)
  - create_task with TASK-SET RETENTION (self._bg_tasks set +
    done_callback discard). Do NOT use bare create_task —
    the event loop holds only a weak reference and tasks
    can be garbage-collected before completing.
  - SEED-KEY DEDUP: do not spawn a second background task for
    a seed key that already has one pending. Use
    self._pending_seeds set. Discard in finally block.
  - Background failure → logger.warning, not exception to caller
  - Zero CONTINUES edges created
  - Zero BELONGS_TO edges created
  - Zero existing campaign test regressions
  - No scorer / conservation / DK / GraphStore protocol changes
  - Tests MUST include async-mechanism tests (background=True)
    for task retention, seed-key dedup, storm convergence, and
    failure isolation — NOT just background=False correctness tests
  - M8 closeout: report actual campaign count, connection mode,
    whether read is keyed. Do NOT fabricate pilot-scale data.

RUN (Codex scope — automated tests only):
  pytest backend/tests/test_campaign_phase3_async.py -v --timeout=60
  pytest backend/tests/test_campaign_*.py -v --timeout=60
  pytest backend/tests/ -q --timeout=300

EXIT: All tests pass. Async-mechanism tests prove task retention
(no GC), seed-key dedup (storm → 1 task), and failure isolation.
check_alert returns immediately. Zero regressions.
```

---

## §10 — Manual / Live Validation (NOT Codex)

**Run manually after Codex completes Phase 3:**

```powershell
# Activate
& "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\proj-envs\python_expts_venv\Scripts\Activate.ps1"

# Start SOC diagnostic backend (backend-only, no frontend)
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python .\demo.py --soc --diag-mode --diag-graph-name soc_graph --diag-backend-port 8001 --age-use-pool

# In a separate terminal:
# M8: check_alert read-only latency (must be ≤ 5ms at p95, pooled)
# M9: background materialization latency (observability only)
# M10: convergence time (< 500ms target)

# Graph integrity check:
# Verify duplicate seed keys = 0
# Verify CONTINUES edges = 0
# Verify BELONGS_TO edges = 0

# Fill in the closeout report template from §4.
```

**NOTE:** `demo.py` lives in `copilot-sdk`, not `gen-ai-roi-demo`.
Use `--diag-mode` for backend-only proof/perf validation.
`--age-use-pool` ensures M8 measures the pooled read path.

---

## §11 — Execution Summary

```
Scope:
  Move campaign seed materialization off the synchronous
  analyze hot path into asyncio.create_task background.
  Preserve 1b-2's advisory-lock idempotent writes unchanged.

Effort: 0.5d (implementation) + measurements

Files: 2-3 (campaigns.py modify + 1 test file create)

Measurements: M8 (hot-path read-only), M9 (background write),
  M10 (convergence time)

Exit: M8 p95 ≤ 5ms. Zero duplicates. Zero CONTINUES.
  All existing campaign tests pass.

What stays deferred:
  - Queue infrastructure (production upgrade)
  - Provisional pending-seed check (production refinement)
  - CONTINUES edges (Phase 4)
  - v6.0 context injection (separate scope, post-Phase-3)
  - v7.0 tensor expansion (separate scope, needs override data)
```

---

## §12 — MAP Status After Phase 3

```
Campaign Phase 1:     CLOSED
Campaign 1b-1:        CLOSED (test authority reconciled)
Campaign 1b-2:        CLOSED_FOR_CORRECTNESS / PERFORMANCE_TRIGGERED
                      (zero duplicates, 215ms p95 vs 5ms budget)
Campaign Phase 3:     IN_PROGRESS / DESIGN_APPROVED
                      (async materialization — create_task for v1)
Campaign Phase 4:     DEFERRED (CONTINUES)
Campaign v6.0:        DESIGN_APPROVED (context injection, post-Phase-3)
Campaign v7.0:        DESIGN_APPROVED / IMPLEMENTATION_DEFERRED
                      (tensor expansion, needs 90d override-rate data)
```

---

## Document Control

| Version | Date | Change |
|---|---|---|
| v1.0 | June 15, 2026 | Initial design. asyncio.create_task for v1. M8/M9/M10 measurements. Hot-path target: M8 p95 ≤ 5ms. |
| v1.1 | June 15, 2026 | Made executable: Codex prompt, discovery step, venv path, test approach (background flag), manual validation separated. |
| v1.2 | June 15, 2026 | P1 review: GC footgun (task-set retention), honest convergence (singleton/crash gaps), M8 assumptions (pooled + O(1) + scale), storm dedup (_pending_seeds), demo decision (pending-seed gap), async-mechanism tests. |
| v1.3 | June 15, 2026 | **Final review pass.** (1) Duplicate §1.2 → §1.1. (2) §2.2 diagram updated to show task-set + seed-key dedup + done_callback (matched §3.1 implementation). (3) §5 test file description updated to match §6 test categories (correctness=background=False, async mechanism=background=True). (4) Codex prompt: `_last_background_task` → `asyncio.gather(*engine._bg_tasks)` (matches task-set pattern, not old single-slot). (5) Closeout report template: added async mechanism verification section + connection_mode + campaign_count fields + split test results by category. (6) Version header fixed (was 1.0, now 1.3). (7) Duplicate changelog entries deduplicated. |
| v1.4 | June 15, 2026 | **Roadmap decisions confirmed + launcher correction.** (1) §10: launcher corrected — `copilot-sdk/demo.py --soc --diag-mode --diag-graph-name soc_graph --diag-backend-port 8001 --age-use-pool` (not gen-ai-roi-demo/demo.py --soc --no-browser). (2) §8: 3 roadmap decisions confirmed — create_task v1 mechanism APPROVED; pending-seed in-memory check INCLUDE NOW; M8 at current scale, report count, no synthetic data. (3) §3.2: pending-seed check upgraded from DEMO DECISION REQUIRED to CONFIRMED — include unless Codex proves semantic distortion. (4) §4 M8: measure at current graph size, report campaign count, verify O(1)+pooled, do not fake pilot-scale. (5) §6: pending-seed tests added (provisional match, semantic non-distortion, cleanup). (6) §9 Codex NON-NEGOTIABLES: pending-seed check + M8 reporting requirements added. Status: Roadmap-approved, ready for Codex prompt. |
