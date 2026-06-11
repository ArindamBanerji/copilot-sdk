# Copilot Decision Hot-Path Architecture (Reconciled)

**Version:** v2.1 (reconciled — single primary architecture)
**Date:** June 9, 2026
**Supersedes:** copilot_analyze_route_architecture_v2_0.md
**Status:** For design-authority review → implementation
**Authority:** DK Runtime Execution Plan v6.9, MAP v5.44

**What changed from v2.0.** v2.0 carried two architectures at once:
an in-memory cache model (its §0B/0C) and a parallelize-AGE-reads
model (its §1–§7). They contradicted each other — §0B said "the
async-gather complexity goes away," §7 still specified
asyncio.gather over factor reads. This version resolves the
contradiction: the cache model is the single primary architecture.
The parallel-reads approach is retired.

Two correctness fixes folded in:
1. Counters are NOT cached in memory — they are materialized on AGE
   entity nodes, read O(1), and written inside the Phase-3
   transaction (persist-before-cache, Rule #48).
2. The cache holds only immutable / rarely-changing entity context,
   which fixes multi-worker coherence and removes the
   triple-representation hazard.

---

## §0 Synopsis

The copilot decision hot path (`/api/alert/analyze` in SOC;
`/api/score` in the SDK copilots; `/api/s2p/score` in S2P) wraps a
0.25ms scorer in 19+ sequential AGE round-trips, four of which are
O(N) scans. Measured on SOC/AGE, analyze averages 25.6s at 250
decisions and grows linearly with graph size. A system that gets
smarter and slower with use cannot credibly claim to compound.

**The fix is not to make AGE queries faster. It is to stop putting
AGE on the read hot path for data that has not changed since the
last read.** The scorer, centroid tensor, DK weights, and
conservation state are already in-memory; their inputs (entity
context, factor data) should be served from the same in-memory
layer. AGE remains the system of record for writes (decisions,
audit, counters — must persist) and for complex graph traversal
(campaign correlation, attack chains, L5 reads).

### The Single Architecture

1. Read entity context from an **in-memory cache** (populated from
   AGE on miss, invalidated on entity write).
2. Factors compute from cached context — **in-memory**.
3. Read mutable counters from their **materialized AGE entity nodes**
   as O(1) point lookups (**not cached** — see §5.3).
4. Score + gate **in memory** (composite gate decision is synchronous).
5. **Persist** Decision + audit + counter increment to AGE in one
   Phase-3 transaction before the response returns, then update the
   in-memory context cache (**persist-before-cache**, Rule #48).
6. **Defer** enrichment (campaign, RL, cluster, gate telemetry) to
   fire-and-forget.

### Headline Numbers

| | Hot path (cache hit) | Cold start (cache miss) | Growth |
|---|---|---|---|
| **Target** | ~111ms | ~260ms | **Zero** |
| **Today (SOC/AGE, 250)** | 25,600ms | — | Linear O(N) |

### Why This Is P1

1. **Cannot demo.** 20s at 250 decisions. Microsoft is sub-second.
2. **Cannot pilot.** 4 min/alert by month 2 of normal use.
3. **Contradicts core claim.** Compounding intelligence requires
   constant-time performance. Slower-with-more-data ≠ compounding.

### Why Framework, Not SOC

The sequential pipeline is the CopilotFramework pattern. The fix
belongs in ci-platform (framework-level). **But the measured 25s is
SOC/AGE-specific** — SDK copilots on SQLite may have no problem
today. The honest two-layer generalization:

- **Pattern** (cache + counters + phases + fire-and-forget): all
  copilots NOW — backend-agnostic.
- **Connection pool**: SOC NOW. Others AT THEIR AGE MIGRATION.

### Sharing

The HOW (pool, cache, counter store, task manager, four-phase
orchestration) lives once in `copilot_core` (ci-platform). Each
copilot injects the WHAT (factors, counters, enrichment) via a
`DomainProfile`. One fix, five copilots. (§4)

### Sequencing: A → C (Framework-First)

```
Phase A: C9B proof (~45 min)     → L5 COMPLETE (current code)
Phase C: copilot_core + SOC adopt → demo-viable + architecturally correct
         SDK copilots at AGE migration
```

### Open Questions

| # | Question | Status |
|---|---|---|
| Q1 | Counter integrity model | ANSWERED: AGE-authoritative + reconciliation (§5.3, §5.6) |
| Q2 | Phase-4 fire-and-forget safe? | ANSWERED: Yes for campaign/RL/cluster. No for composite gate decision. |
| Q3 | Factor independence | Confirm: none reads a counter another writes in-phase |
| Q7 | Sync vs async pool | ANSWERED: Sync suffices (no read fan-out). Async only if parallel Phase-3 writes. |
| Q9 | Framework scope | ANSWERED: copilot_core in ci-platform; boundary = hot path only (§4.4) |
| Q10 | Pool sizing | ANSWERED: 5 × 8 = 40, headroom preserved (§6) |

---

## §0.5 Codex Verification Pass (Pre-Build Gate)

This document asserts empirical claims about the codebase that the
architecture depends on. Before the Coding session builds §8, Codex
verifies those claims against the code. This is a **read-only
adversarial review**, not an execution pass. Output is a DRIFT
report that returns to the design session; Codex does not modify
code and does not touch the MAP.

### How to Run

```
rtk codex --wait
```

Paste the prompt below in CLI mode. It is read-only: does not run
the test runner, does not execute the spike, does not edit anything.

### The Verification Prompt

```
ROLE: Adversarial verification reviewer. READ-ONLY. Do NOT modify
code, do NOT run the configured test runner, do NOT execute the spike,
do NOT propose fixes or refactors. Report findings only.

CONTEXT: The architecture document copilot_analyze_route_architecture_v2_2.md
makes empirical claims about this codebase. The architecture stands
or falls on them. Verify each claim C1–C8 below against actual code.

RULES:
- No evidence, no claim. Every verdict cites file:line. If you cannot
  locate evidence, mark UNVERIFIED — do NOT infer or assume.
- Do NOT propose fixes. Report only what the code shows.
- Architectural adherence: flag any code that contradicts a stated
  Design Constraint (DC-1..DC-8 in §2).
- Quote the minimum necessary; cite file:line rather than pasting.

FILE SCOPE (read only within these):
- SOC analyze route + counter/scan helpers:
    backend/app/routers/triage.py
- Graph client / connection model:
    ci-platform/ci_platform/graph/age_client.py
- Composite gate (locate; likely CompositeDiscriminant or similar)
- Scorer + learned state (in-memory?):
    GAE library (ProfileScorer: centroids/μ, DK weights)
    ci-platform (conservation state, L5LearningStore)
- Per-copilot graph backend config (SQLite vs AGE):
    SOC main.py/settings
    copilot-sdk apps/{trading,purchasing,dataops}/backend main.py
    S2P main.py/settings

CLAIMS TO VERIFY:

C1 [P1] Hot path = "19+ sequential AGE round-trips, 4 of which are
    O(N) scans" (§0, §1.2). Enumerate the actual AGE queries issued
    by the SOC analyze handler. Identify which ones scan all Decision
    nodes (O(N)) vs point/keyed lookups. Report the real count and
    file:line of each O(N) scan.
    DRIFT-P1 if count is materially off OR the named scans are not
    full Decision scans where claimed.

C2 [P1] Composite gate is DECISION-CRITICAL — "can override action
    to refer_to_analyst" (§2 DC-5, §8 Step 4). Locate the gate
    evaluation. Confirm whether its output mutates the action returned
    to the caller, or is only recorded as telemetry/metadata. file:line.
    DRIFT-P1 if gate is telemetry-only (then DC-5 exception is wrong).

C3 [P1] Backend per copilot (§4.6): SOC on AGE; SDK copilots on
    SQLite today. For EACH copilot, cite the graph-store construction
    / GRAPH_BACKEND default. file:line per copilot.
    DRIFT-P1 if any SDK copilot is already on AGE, or SOC is not.

C4 [P1] Connection model (§8 Step 0): AGEClient opens a FRESH
    psycopg connection per run_query (cited as age_client.py:299-323),
    sync psycopg. Confirm: connect/close per call vs pool; sync vs
    async psycopg API. file:line.
    DRIFT-P1 if already pooled (connection-tax premise is wrong).
    DRIFT-P2 if async (changes pool choice only).

C5 [P2] Counters currently SCAN Decision nodes (§3, §8 Step 3):
    sequence_count and cross_category_count are computed today by
    scanning Decision nodes. Confirm the scan exists and state whether
    cross_category is DISTINCT or TOTAL. file:line.

C6 [P1] Scorer state is IN-MEMORY (§2 DC-3): centroid tensor μ, DK
    weights, conservation state. Confirm each is held in memory and
    NOT read from AGE on the analyze hot path. file:line.
    DRIFT-P1 if any is fetched from AGE per-request.

C7 [P2] "Already fixed, do not re-litigate" (§1.4): (a) campaign
    identity Phase 1 = stable identity tuple; (b) Rule #40 = localhost
    DSN; (c) L5-UPSERT = SET-based, not DELETE+CREATE. Cite file:line
    or commit evidence. DRIFT-P2 per item not present.

C8 [classification] §1.2 waterfall provenance. For each line item,
    classify as MEASURED (traceable to a named proof/trace artifact) or
    ESTIMATED. Flag any presented as measured that is apportioned.

OUTPUT FORMAT:
| ID | Doc claims | Code shows (file:line) | Verdict | Severity | Note |
Verdict ∈ {MATCH, DRIFT, UNVERIFIED}.
Summary: "<n> MATCH / <m> DRIFT / <k> UNVERIFIED; of DRIFT, <j> P1."
GATE:
  - j >= 3 P1 DRIFT → "STOP: revise document before build."
  - Else → "PROCEED to build; apply noted corrections."

STOP CONDITION: 3 P1 DRIFT findings → stop, report, recommend halt.
```

### After the Pass

The DRIFT report returns to the design (Roadmap) session, NOT to the
build. Apply corrections to this document, re-version, and only then
send the Step-1 execution prompt to the Coding session. Codex does
not update the MAP.

---

All numbers below are from live SOC/AGE proof runs, not synthetic
benchmarks.

### 1.1 The Scorer Is Fast; the Route Is Not

| Stage | Time | Note |
|---|---|---|
| ProfileScorer.score() | 0.25ms | The actual ML computation, in-memory |
| Full analyze route (pre-campaign fix) | 5,692ms at 25 decisions | Route is ~23,000× the work it wraps |
| Full analyze route (post-campaign fix) | 1,757ms at 25 decisions | Campaign Phase 1 halved baseline |
| Full analyze route (pre-campaign fix) | 25,602ms at 250 decisions | Grows ~85ms/outcome (O(N) scans) |

### 1.2 Where the Time Goes (Phase-C Waterfall, 25 Outcomes, Pre-Campaign Fix)

**These timings are from the Phase-C trace BEFORE Campaign Phase 1.**
Post-campaign, campaign correlation drops but the O(N) scans and
sequential pipeline remain unchanged.

```
READS (all from AGE today):
  alert / subject lookup           ~80 ms
  security / entity context        ~90 ms
  factor inputs (6 × AGE query)   ~336 ms
  sequence_count        O(N) scan ~500 ms   ← grows
  cross_category_count  O(N) scan ~500 ms   ← grows
  cluster_history       O(N) scan ~200 ms   ← grows

COMPUTE:
  scorer + gate                  ~0.35 ms

WRITES (must persist):
  Decision + DECIDED_ON          ~106 ms
  audit hash                      ~83 ms

ENRICHMENT (not decision-critical):
  campaign correlation           ~480 ms + O(N)
  RL metadata / composite-gate telemetry / event bus  ~160 ms
```

### 1.3 Why This Is Architectural, Not Optimization

Even with perfect indexes (O(N) → O(log N)) and a connection pool,
~19 sequential AGE round-trips at 20-50ms each floor the route well
above 1s and still grow. Indexes change the slope; they do not change
the fact that the scorer's inputs are being fetched from a graph
database on every request. The structural change is to serve unchanged
data from memory and reserve AGE for persistence and genuine graph
traversal.

### 1.4 What Has Already Been Fixed (Do Not Re-Litigate)

| Fix | Impact |
|---|---|
| Campaign identity Phase 1 (stable identity tuple) | O(N²) → O(N) campaign graph |
| Rule #40 (localhost vs 127.0.0.1) | Removed 2.1s IPv6 fallback per HTTP call |
| L5-UPSERT (DELETE → SET) | L5 persistence correctness (not a perf fix) |

---

## §2 Design Constraints (Read This First)

These encode why the architecture splits AGE and memory the way it
does, so a future reviewer does not re-open settled ground. Numbered
for reference in implementation decisions.

**DC-1 — AGE is a persistence layer, not a hot-path cache.** Every
AGE query is 30-100ms even with pooling (PostgreSQL → AGE extension →
Cypher parse → traversal → serialize). AGE belongs on the write path
and on complex graph traversal. It does NOT belong on the read hot
path for data unchanged since the last write.

**DC-2 — Entity data changes rarely, is read constantly.** A User's
properties, an Asset's criticality, a Vendor's risk profile change on
ingestion (rare) and are read on every analyze (frequent). Re-reading
the same node from AGE for every alert against that entity is waste.
Such data belongs in an in-memory cache with write-through
invalidation.

**DC-3 — The scorer is already in-memory; extend the pattern.** The
centroid tensor μ, DK weights, and conservation state are all
in-memory. The only reason the route is slow is that the scorer's
inputs come from AGE instead of from the same in-memory layer.

**DC-4 — Writes must persist before the response reports them.** A
Decision that exists only in memory is a suggestion that vanishes on
restart. Conservation counts persisted decisions; the audit chain is
tamper-evident because it is in the graph. All writes go to AGE
synchronously in Phase 3, before the response returns.

**DC-5 — Enrichment is not decision-critical.** Campaign correlation,
RL metadata, cluster history, and gate telemetry enrich a decision
after the fact; they do not change the action or confidence. They fire
after the response. **Exception:** the composite-gate decision (can
override action to refer_to_analyst) is decision-critical and stays
synchronous in Phase 2. Only gate telemetry is deferred.

**DC-6 — Cache invalidation must be correct, not fast.** The cache
serves stale data by design; the discipline is bounding how stale.
Immutable data (a created alert) is never invalidated; rarely-changing
context is invalidated on entity write; mutable counters are not
cached at all (DC-7, §5.3).

**DC-7 — Mutable counters are AGE-authoritative, never
memory-authoritative.** Counters have zero staleness tolerance (the
referral engine vetoes on them). An in-process counter cache is
incoherent across workers and violates persist-before-cache (Rule #48)
and DC-4. Therefore counters are materialized on AGE entity nodes,
read as O(1) point lookups on the hot path, and written inside the
Phase-3 transaction. They are NOT in the cache. (Full reasoning §5.3.)

**DC-8 — The design must apply to all 5 copilots with no SOC
assumptions.** Cache keying, invalidation, counter management, and
the four-phase orchestration are generic. Domain specifics (which
factors, which counters, the derived_entity_key fallback) live in
each copilot's DomainProfile, never in the shared layer.

### Summary: What Goes Where

**STAYS ON AGE (must persist, write path + complex traversal):**

| Operation | Home | When | Coherence |
|---|---|---|---|
| Decision + DECIDED_ON write | AGE | Phase 3 (sync, before response) | persisted |
| Audit hash write | AGE | Phase 3 (sync, same transaction) | persisted |
| Counter increment | AGE node | Phase 3 (sync, same transaction) | authoritative, O(1) read |
| Campaign correlation | AGE | Phase 4 (async) | graph traversal |
| L5 centroid / DK / conservation | AGE | outcome path (not analyze) | proof chain |

**MOVES TO IN-MEMORY (read path, cached, AGE-backed):**

| Operation | Home | When | Coherence |
|---|---|---|---|
| Subject lookup (alert/invoice/trade) | read once | Phase 1 | one-shot, not cached (§5.2) |
| Entity context (user/asset/vendor) | cache | Phase 1 | invalidate on entity write |
| Factor inputs from entity context | cache | Phase 2 | invalidate with context |
| Mutable counters | **AGE node (NOT cache)** | Phase 2 read / Phase 3 write | DC-7 |

---

## §3 The Target Architecture (Single Model)

### 3.1 The Four-Phase Hot Path

```python
# copilot_core/pipeline.py

class DecisionPipeline:
    """Owns the HOW. The domain supplies the WHAT via DomainProfile."""

    def __init__(self, profile: DomainProfile, cache: EntityCache,
                 counters: CounterStore, pool: PooledAGEClient,
                 tasks: BackgroundTaskManager):
        self.profile = profile
        self.cache = cache
        self.counters = counters
        self.pool = pool
        self.tasks = tasks

    async def run(self, subject_id: str) -> DecisionResponse:
        # ---- Phase 1: bootstrap reads ----
        subject = await self.profile.read_subject(subject_id, self.pool)
        entity_key = self.profile.entity_key(subject)
        context = await self.cache.get_or_load(
            entity_key,
            loader=self.profile.load_entity_context,
            pool=self.pool,
        )

        # ---- Phase 2: compute + counter read + score + GATE ----
        factors = self.profile.compute_factors(subject, context)
        counters = await self.counters.read(entity_key)  # AGE O(1), NOT cached
        category = self.profile.category(subject)
        action, confidence = self.profile.scorer().score(factors, category)
        final_action = self.profile.gate(action, confidence, counters)

        decision_id = new_decision_id()

        # ---- Phase 3: persist BEFORE response (one transaction) ----
        async with self.pool.transaction() as tx:  # DC-4
            await self.profile.write_decision(
                tx, decision_id, subject_id, final_action, confidence, factors)
            await self.profile.write_audit(tx, decision_id, factors)
            await self.counters.increment(tx, entity_key, category)

        # persist-before-cache (Rule #48)
        self.cache.note_decision(entity_key)

        # ---- Phase 4: fire-and-forget enrichment ----
        for coro in self.profile.enrichment_tasks(decision_id, subject, context):
            self.tasks.schedule(coro)

        return DecisionResponse(final_action, confidence, factors, decision_id)
```

**Key properties:**

- Reads are in-memory (context) or O(1) point lookups (counters).
  No O(N) scans. Growth with graph size is zero.
- Writes are synchronous and transactional (DC-4). Counter increment
  is in the same transaction as the Decision.
- Cache is touched only AFTER commit (persist-before-cache, Rule #48).
- Composite-gate decision is in Phase 2 (synchronous); only telemetry
  is deferred (DC-5).
- **asyncio.gather is not required.** Reads are in-memory — no slow
  fan-out to parallelize. Phase 3 is writes in one transaction. If a
  profile later shows Phase-3 writes are the bottleneck, parallel
  writes are a per-profile knob (§4.3), not a default.

### 3.2 Target Performance (Derived from §1.2)

```
Phase 1 reads:   ~5 ms    (subject: pooled AGE read ~5ms; context: cache hit ~0ms)
Phase 2 compute: ~6 ms    (cached factors ~1ms + counter O(1) ~5ms + scorer 0.25ms)
Phase 3 writes: ~100 ms   (Decision + audit + counter in one AGE transaction)
Phase 4 async:    0 ms    (off response path)
─────────────────────────────
Hot path total:  ~111 ms   at ANY graph size, growth ZERO
Cold start:      ~260 ms   (first request fills cache from AGE: subject ~5ms + context ~5ms + factors ~5ms)
```

**Note:** Phase 1 subject read IS an AGE query (the alert/invoice
is looked up by ID). It is NOT cached (§5.2 — one-shot, read once).
With pooling this is ~5ms. The ~80ms in §1.2 is unpooled. Step 0
spike validates the pooled cost.

Faster than the retired parallel-reads target (~260ms) and simpler
(no async-gather, no large read-side pool). Pool sized for writes
(3-5 connections/copilot), not parallel reads (15-20). See §6.

### 3.3 Why O(1), Not O(log N)

Materialized counters on entity nodes are point lookups: ~constant
regardless of graph size. Indexes give O(log N) (250 → ~200ms,
100k → ~420ms); counters give O(1) (~5ms at any size). The cache
makes context reads O(1) — keyed point access, not traversal.

---

## §4 The Sharing Architecture: copilot_core + DomainProfile

### 4.1 Governing Insight

Every copilot's hot path has the same shape. What varies is the
WHAT — which factors, counters, keys, enrichment. None of the
performance lives there. The performance lives in the HOW: pool,
cache, counter store, transaction boundary, task manager.

**Share the HOW. Inject the WHAT.** The dangerous code should exist
in exactly one tested place.

### 4.2 Shared Components (in copilot_core, ci-platform)

| Component | Responsibility | Why shared |
|---|---|---|
| `PooledAGEClient` | Connection pool + AGE session | Pool + write path, sized once (§6) |
| `EntityCache` | In-memory context cache; get-or-load; invalidate | Cache + invalidation logic, once |
| `CounterStore` | Materialized AGE counters: O(1) read, transactional increment, distinct via SEEN_* edges, reconciliation | Distinct-count + reconciliation bugs fixed once |
| `BackgroundTaskManager` | Fire-and-forget with retained task set + done-callback | GC footgun fixed once |
| `DecisionPipeline` | Four-phase orchestrator (§3.1) with per-profile knobs | Transaction boundary + ordering correct once |
| `DomainProfile` (Protocol) | The injected WHAT | The only per-copilot surface |

**Adapters shrink to thin shims:**
- copilot-sdk `scoring_router` → build DomainProfile, call pipeline
- SOC `triage.py` → build SOC's DomainProfile, call pipeline
  (SOC stops being a separate hot-path implementation)

### 4.3 Knobs, Not Forks

| Apparent difference | Knob on shared pipeline |
|---|---|
| Factor B depends on factor A | DomainProfile declares factor dependency order |
| Enrichment must be sync (v6.0 campaign-as-scorer-input) | Profile marks task Phase-2 instead of Phase-4 |
| Reads cheap, parallelism not worth it | Per-profile sequential vs parallel writes |
| Different cache size / recurrence | Per-profile cache size + TTL (§5.5) |

**Rule:** if you want a hack, you are missing a knob — add the knob.
A fork requires a measured extreme gain a knob cannot capture. No
measurement, no fork. No such case exists today.

### 4.4 Scope Discipline

copilot_core's boundary is exactly the decision hot path and its
performance machinery. It does NOT own domain enrichment logic, the
math engine (GAE, already shared), or the frontend shell (already
shared via CopilotShell). If something does not serve the hot path's
correctness or speed, it stays in the domain.

### 4.5 Per-Domain Counter Definitions

Each counter is a `CounterDef`, declared per copilot — not
implemented per copilot:

```python
CounterDef(
    node_label   = "User",
    key_prop     = "entity_key",
    counter_prop = "sequence_count",
    trigger      = Trigger.DECISION,   # DECISION (Phase 3) | OUTCOME
    mode         = Mode.CUMULATIVE,    # CUMULATIVE (+1) | DISTINCT (SEEN_* edges)
    population   = Pop.OBSERVED,       # OBSERVED | VERIFIED (#111)
)
```

| Copilot | Counter | Node / key | Trigger | Mode | Population |
|---|---|---|---|---|---|
| SOC | sequence_count | User / entity_key | DECISION | cumulative | observed |
| SOC | cross_category | User / entity_key | DECISION | distinct (SEEN_CATEGORY) | observed |
| SOC | analyst_accuracy | AnalystProfile / analyst_id | OUTCOME | ratio (correct/total) | verified |
| Trading | trade_by_instrument | Trader / trader_id | DECISION | distinct (SEEN_INSTRUMENT) | observed |
| Trading | position_history | Trader / trader_id | DECISION | cumulative | observed |
| Purchasing | supplier_decisions | Supplier / supplier_id | DECISION | cumulative | observed |
| Purchasing | category_spend | Category / category_id | DECISION | distinct | observed |
| DataOps | pipeline_decisions | Pipeline / pipeline_id | DECISION | cumulative | observed |
| DataOps | quality_scans | DataSource / source_id | DECISION | cumulative | observed |
| S2P | vendor_risk | Vendor / vendor_id | DECISION | cumulative | observed |
| S2P | compliance_checks | ComplianceRule / rule_id | DECISION | distinct | observed |

**Correctness notes:**
- Decision-count counters increment in Phase 3 (decision write),
  NOT on outcome. Only verified counters increment on outcome.
- Distinct counters use bounded SEEN_* edge sets (MERGE, idempotent).
  Count = bounded edge count (≤ |categories|). CounterStore
  implements this once.
- `population` ties to #111 (V = verified-only).
- `derived_entity_key` fallback is SOC-specific (messy SIEM IDs).
  Trading/Purchasing/DataOps/S2P key directly off clean IDs.

### 4.6 Per-Copilot Backend Reality

| Copilot | Backend today | Destination | When pool/cache lands |
|---|---|---|---|
| **SOC** | **AGE** | AGE | **Now** (problem measured here) |
| Trading | SQLite | AGE (#150) | At AGE migration |
| Purchasing | SQLite | AGE (#179) | At AGE migration |
| DataOps | SQLite | AGE (#117) | At AGE migration |
| S2P | SQLite | AGE (L5) | At AGE migration |

The pool fix is **pre-positioned**: pays off for SOC now, for each
SDK copilot at AGE cutover. Cache + counter + four-phase pattern is
backend-agnostic and benefits every copilot regardless of backend.

**Validate before generalizing:** measure one SDK copilot at 250+
decisions on SQLite. If sub-second: confirmed SOC-urgent / SDK-deferred.

---

## §5 Cache Coherence (The Hard Part, Made Explicit)

### 5.1 Single Source of Truth

AGE is authoritative for everything. The EntityCache is strictly
derived: read-through on miss, invalidate-on-write. If cache and AGE
disagree, AGE wins and the cache is dropped/refilled.

### 5.2 What Is Cached vs Read-Fresh

| Data | Cached? | Why |
|---|---|---|
| Entity context (User/Asset/Vendor + edges) | **Yes** | Recurring, rarely changes (DC-2) |
| Factor inputs from entity context | **Yes** | Function of cached context |
| Per-transaction subject (alert/invoice/trade) | **No** | One-shot — created and read once |
| Mutable counters | **No** | AGE-authoritative O(1) read (DC-7, §5.3) |

**Per-copilot cache scope:** The benefit comes from the recurring
entity, not the subject. SOC alerts recur against the same user →
cache the user. S2P analyzes each invoice once → cache the vendor
context, not the invoice. Each DomainProfile declares what is
cacheable-recurring vs read-once.

### 5.3 Why Counters Are NOT Cached (Multi-Worker Coherence)

The cache lives in FastAPI app state — in-process. If a copilot runs
more than one uvicorn worker (normal for multiple cores), each worker
has its own cache. A counter incremented in worker A's memory is
stale in worker B's; an analyze routed to B reads a stale counter →
the referral engine vetoes wrong — a wrong decision, violating DC-6.

Caching the counter also reverses persist-before-cache (Rule #48) and
DC-4. All three problems dissolve with one choice: the materialized
counter on the AGE entity node is the only counter. It is read O(1)
(~5ms pooled, always coherent across workers) and written in the
Phase-3 transaction. The in-memory cache holds only immutable /
rarely-changing context.

**Cost:** one ~5ms pooled point-lookup per analyze.
**Benefit:** multi-worker correctness, persist-before-cache
compliance, one fewer representation.

This cleanly separates the two ideas v2.0 conflated: materialize the
counter (AGE node — the fix for counters) vs cache the context
(memory — the fix for reads).

### 5.4 Invalidation Call Sites (Enumerate Every Writer)

The analyze/outcome routes are NOT where entities are mutated —
ingestion is. Cache invalidation must be wired into every writer:

- `/api/admin/ingest` and any BYOD/CSV importer
- Sentinel / connector pulls (SOC), broker/exchange sync (Trading),
  ERP/Celonis feeds (DataOps/Purchasing), supplier feeds (S2P)
- Admin/manual entity edits
- Any Phase-4 enrichment that mutates a cached entity property

Each calls `cache.invalidate(entity_key)`. A missing call site is
how this architecture breaks — the list is part of the spec.

### 5.5 Bounded Cache + Cold Miss + Per-Profile Size

"Hundreds of entities, in-process dict, never evict" is the demo
configuration. Production needs a bounded LRU with a size cap; a
cold/evicted miss falls back to a pooled AGE read (~5ms) — worst
case degrades to pooled-read latency, not catastrophe. Cache size is
a per-profile knob (§4.3).

### 5.6 Reconciliation Job (Required, Not Optional)

Materialized read models drift (partial failures, bugs, migrations).
`CounterStore.reconcile(entity_key | all)`:
1. Recount from raw Decision nodes in AGE
2. Compare to materialized counter
3. Log delta at WARNING, correct in one transaction
4. Stamp `last_reconciled`

Schedule: nightly and on process restart.
Acceptance: inject deliberate drift → reconcile → counter == recount.

---

## §6 Pool Sizing (Coordinated Against Shared PostgreSQL)

Under the cache model the pool is for writes + cache fill + Phase-4,
not parallel reads:

```
5 copilots × max_size 8 = 40 connections
Leaves headroom for: psql, migrations, L5 writers, reconciliation
PostgreSQL default max_connections = 100
```

Set `min_size=2`, `max_size=8` per copilot. Do NOT size at 20
(5 × 20 = 100 = ceiling, zero headroom). If write concurrency needs
more, raise `max_connections` or front with PgBouncer — a deployment
decision, not a per-copilot default.

**Phase-4 pool contention:** Fire-and-forget Phase-4 tasks (campaign,
RL, cluster) also draw from the pool. Under concurrent load, Phase-4
of request A competes with Phase 1-3 of request B. At K=10 concurrent
requests with lingering Phase-4 work: up to 20 pool checkouts. If
`max_size=8`, the pool queues Phase-4 work behind hot-path work —
this is acceptable (Phase-4 is enrichment, not decision-critical).
The pool's FIFO queue ensures hot-path writes are not starved by
Phase-4 only if Phase-4 tasks return connections promptly.

---

## §7 Performance Targets

| Milestone | Acceptable | Today (250, SOC) | Cache model |
|---|---|---|---|
| C9B proof | <120s/loop | ~20s ⚠️ | ~111ms ✅ |
| LOOM video | <5s | ~20s ❌ | ~111ms ✅ |
| CISO live demo | <3s at 250 | ~20s ❌ | ~111ms ✅ |
| Pilot week 1 | <3s at 500 | ~40s ❌ | ~111ms ✅ |
| Pilot month 1 | <2s at 3,000 | ~250s ❌ | ~111ms ✅ |
| Production | <1s any scale | — | ~111ms ✅ |
| Competitive (MS) | <500ms | — | ~111ms ✅ |

Load-bearing assumption: DC-2 (entity data recurs and changes rarely).
Step-0 spike and cold-start measurement validate it.

---

## §8 Implementation Plan

Sequencing follows MAP's AGE-everything plan: build shared core,
prototype on SOC (where the problem is measured), adopt at each SDK
copilot's AGE cutover.

### Step 0 — Connection-Model Spike (parallel with C9B)

**Why this replaces the prior spike.** The earlier version measured
the current (unpooled) AGEClient but compared against pooled targets,
so the connection tax it was supposed to expose was baked in. It also
used a scan-then-LIMIT (not a keyed point lookup) and wrote to
soc_graph_diag_f8 (the proof graph). This version measures fresh-
per-query vs pooled side by side (isolating connection tax from query
cost), uses a keyed point lookup, and rolls the write back so f8 is
untouched.

**Goal.** Decide whether the cache model is viable on AGE by measuring
the only two things the hot path still touches AGE for: a single keyed
entity read (cache-miss cost) and a Phase-3 write transaction. And
quantify how much of the read cost is connection establishment (which
pooling removes) vs query execution (which it does not).

```powershell
# Terminal 1: C9B proof (~45 min) — proves L5 correctness BEFORE change
python scripts/diagnostics/run_soc_diag_f.py `
    --graph-name soc_graph_c9b `
    --prefix C9B-SOC `
    --target-outcomes 250 `
    --max-attempts 400
```

```python
# Terminal 2: spike — connection-tax isolation + Phase-3 write cost
# Read-only against f8 (write is rolled back).
# Requires: psycopg, psycopg_pool. Sync pool sufficient (no read fan-out).
import time, json
import psycopg
import psycopg_pool

DSN   = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
GRAPH = "soc_graph_diag_f8"   # read-only; write below is rolled back
N     = 10

def _configure(conn):
    conn.execute("LOAD 'age'")
    conn.execute('SET search_path = ag_catalog, "$user", public')

def _point_read(key):
    return (f"SELECT * FROM cypher('{GRAPH}', $$ "
            f"MATCH (u:User {{id: '{key}'}}) RETURN u $$) AS (u agtype)")

def main():
    pool = psycopg_pool.ConnectionPool(
        DSN, min_size=2, max_size=4, configure=_configure, open=True)

    # 0. Grab a real User key from f8 for representative lookup
    with pool.connection() as c:
        row = c.execute(
            f"SELECT * FROM cypher('{GRAPH}', $$ "
            f"MATCH (u:User) RETURN u.id LIMIT 1 $$) AS (id agtype)"
        ).fetchone()
    assert row, "no User node in f8"
    key = str(row[0]).strip('"')

    # 1. BASELINE — fresh connection per query (current AGEClient)
    t0 = time.perf_counter()
    for _ in range(N):
        with psycopg.connect(DSN) as c:
            _configure(c)
            c.execute(_point_read(key)).fetchone()
    baseline_ms = (time.perf_counter() - t0) / N * 1000

    # 2. POOLED — warm connection reused (proposed fix)
    t0 = time.perf_counter()
    for _ in range(N):
        with pool.connection() as c:
            c.execute(_point_read(key)).fetchone()
    pooled_ms = (time.perf_counter() - t0) / N * 1000

    # 3. POOLED WRITE transaction, ROLLED BACK (Phase-3 cost, no residue)
    with pool.connection() as c:
        t0 = time.perf_counter()
        c.execute(f"SELECT * FROM cypher('{GRAPH}', $$ "
                  f"CREATE (d:SpikeDummy {{id:'spike'}}) RETURN d "
                  f"$$) AS (d agtype)")
        write_ms = (time.perf_counter() - t0) * 1000
        c.rollback()  # AGE writes are PG rows → rollback undoes them

    tax = round(baseline_ms - pooled_ms, 1)

    if pooled_ms < 10 and write_ms < 100:
        branch = "cache_model_viable"
    elif tax > pooled_ms:
        branch = ("reassess: dominant cost is CONNECTION TAX — "
                  "pooling helps; re-measure pooled path")
    else:
        branch = ("reassess: pooled reads still slow — AGE QUERY "
                  "cost, not connection tax; pooling won't save it")

    result = {
        "baseline_per_query_ms": round(baseline_ms, 1),
        "pooled_per_query_ms":   round(pooled_ms, 1),
        "connection_tax_ms":     tax,
        "pooled_write_ms":       round(write_ms, 1),
        "branch":                branch,
    }
    print(json.dumps(result, indent=2))
    with open("spike_decision.json", "w") as f:
        json.dump(result, f, indent=2)
    pool.close()

main()
```

**spike_decision.json:**
```json
{
  "baseline_per_query_ms": "...",
  "pooled_per_query_ms": "...",
  "connection_tax_ms": "...",
  "pooled_write_ms": "...",
  "branch": "cache_model_viable | reassess: ..."
}
```

**Gate (three outcomes):**

- `pooled_per_query_ms < 10` AND `pooled_write_ms < 100` →
  **cache_model_viable**, proceed to Step 1.
- `connection_tax_ms` large, `pooled_per_query_ms` small → pooling
  removes most cost; cache model is comfortable.
- `pooled_per_query_ms` still ~50ms → AGE point reads intrinsically
  slow; cache model still wins (reads each entity once, serves from
  memory), but raise per-profile cache TTL and re-examine §6 pool
  config before relying on f8-scale cold starts.

**Note:** C9B proof (Terminal 1) runs in parallel and is unaffected —
spike is read-only against f8, write is rolled back.

### Step 1 — copilot_core Skeleton (~1.5d)

`DomainProfile` protocol, `PooledAGEClient`, `DecisionPipeline`
shell (§3.1, §4.2).

**Gate:** SOC DomainProfile builds; pipeline runs end-to-end against
a fixture with reads still hitting AGE (cache not yet in front). All
SOC analyze tests pass.

### Step 2 — EntityCache + Invalidation Wiring (~1.5-2d)

Read-through cache; bounded LRU; the invalidation call-site list
(§5.4) wired into every entity writer.

**Gate:** analyze hot path serves context from cache (hit ~0ms); an
ingestion that mutates an entity invalidates the cache (test: write →
analyze sees new value, not stale).

### Step 3 — CounterStore (~1.5d)

Materialized AGE counters: O(1) read, transactional Phase-3
increment, distinct via SEEN_* edges, reconciliation job (§5.6).

**Gate (machine-checkable):**
```powershell
$a25  = (Get-Content perf_25.json  | ConvertFrom-Json).analyze_avg_ms
$a250 = (Get-Content perf_250.json | ConvertFrom-Json).analyze_avg_ms
if ($a250 -le $a25 * 1.2) { "PASS: O(N) eliminated" } else { "FAIL" }
```

### Step 4 — BackgroundTaskManager (~0.5d)

Fire-and-forget with retained task set (GC footgun) + done-callback
WARNING logging. Campaign / RL / cluster / gate-telemetry → Phase 4.
Composite-gate decision stays synchronous Phase 2.

**Gate:** response returns before Phase-4 writes land; no silent task
failures in logs.

### Step 5 — SOC Adopts copilot_core (Prototype Domain)

SOC `triage.py` → thin adapter building SOC's DomainProfile.

**Gate:** full SOC suite passes; 250-outcome proof on fresh graph
shows hot path ~111ms, flat across 1/250/1,000 decisions.
Concurrent: K=10 simultaneous analyzes → p95 < target AND zero
PoolTimeout.

### Step 6 — SDK Copilots Adopt at AGE Migration

Trading / Purchasing / DataOps / S2P build DomainProfile and route
through copilot_core at their AGE migration (#150 / #179 / #117).
Marginal cost ≈ DomainProfile + CounterDef list (declarative).

### Rollback

Each step is independently reversible and additive: cache is
bypassable (read from AGE), counter properties are additive, pipeline
can swap back to per-route path. No irreversible schema change.

### Effort (Honest)

| Item | Effort | Note |
|---|---|---|
| copilot_core skeleton | ~1.5d | Clear interfaces |
| EntityCache + invalidation | ~1.5-2d | The hard part — coherence, not wiring |
| CounterStore + reconciliation | ~1.5d | Distinct + transaction + recount, once |
| BackgroundTaskManager | ~0.5d | Once |
| SOC adopt | ~1d | Prototype domain |
| SDK adopt (×4) | ~0.5d each | Declarative profile, at AGE cutover |

Do not let "the design is done over many versions" hide that the
cache layer is net-new code with real test surface (§5).

---

## §9 Blast Radius

| Component | Change | Risk |
|---|---|---|
| copilot_core/* (new) | New shared module | MEDIUM — central, tested once |
| PooledAGEClient (age_client.py) | Per-query connect → pool | LOW (adapter only) |
| SOC triage.py | Route body → thin DomainProfile adapter | HIGH — central orchestration |
| copilot-sdk scoring_router | → DomainProfile adapter | MEDIUM (shared by 4) |
| Ingestion / admin / connector paths | Add cache.invalidate() | MEDIUM — must be complete (§5.4) |
| Outcome route | Verified-counter increment | LOW |
| Scorer math, centroid/DK, conservation, L5, graph schema, API contract | **Unchanged** | **NONE** |

---

## §10 Correctness Test List

| # | Test |
|---|---|
| 1 | test_sequence_count_increments_on_decision_write_not_on_analyze_read |
| 2 | test_cross_category_distinct_not_total (3 decisions, 2 categories → count=2) |
| 3 | test_counter_read_keyed_consistently_with_write |
| 4 | test_counter_persisted_in_phase3_transaction_with_decision |
| 5 | test_counter_not_in_cache (two workers → same counter value; DC-7) |
| 6 | test_cache_invalidated_on_entity_ingestion |
| 7 | test_cache_miss_falls_back_to_pooled_read |
| 8 | test_reconciliation_corrects_injected_drift |
| 9 | test_composite_gate_action_present_in_response |
| 10 | test_fireforget_task_retained_until_done |
| 11 | test_response_returns_before_phase4_writes_land |
| 12 | test_analyze_latency_flat_25_vs_250_vs_1000 |

---

## §11 Relationship to Other Decisions

**Campaign identity (v1.3):** Campaign correlation is Phase-4
enrichment at v5.x. This doc governs timing; the campaign doc governs
semantics. If v6.0 makes campaign a scorer input, DomainProfile
promotes the task to Phase 2 (a knob, §4.3).

**L5 proof chain / DK runtime:** Independent of hot-path latency.
Run C9B before this change (Step 0) so a later failure isn't
ambiguous. Counter persist-before-cache follows Rule #48.

**Conservation law (α·q·V ≥ θ_min):** Reads verified decisions from
L5/graph nodes, not from cache or hot-path counters.
`population=VERIFIED` counters align with conservation's V (#111).

**Compounding intelligence claim:** Constant hot-path latency with
growing knowledge is a precondition for the claim's credibility.
Constant latency is necessary, not itself the compounding mechanism.

---

## §12 Document Control

| Version | Date | Change |
|---|---|---|
| v1.0-v1.9 | June 9, 2026 | Sequential evolution: problem diagnosis → parallel-reads → cross-copilot → framework-first → cache model. See copilot_analyze_route_architecture_v2_0.md for full v1.x changelog. |
| v2.0 | June 9, 2026 | Introduced cache model alongside parallel-reads body — internally contradictory. |
| v2.1 | June 9, 2026 | **Reconciled to single architecture (cache model).** Counters AGE-authoritative, not memory-cached (DC-7, §5.3) — fixes multi-worker coherence + persist-before-cache + triple representation. Body rewritten around cache model; parallel-reads retired. copilot_core sharing integrated (§4). Cache-coherence §5: invalidation call sites, bounded LRU, per-copilot scope, reconciliation. Spike narrowed. Pool sizing 5×8. Effort honest. |
| v2.2 | June 9, 2026 | Comprehensive review. §1.1: pre/post Campaign Phase 1 clarity. §3.2: Phase 1 subject read ~5ms (not ~1ms). Target ~107→~111ms. Spike script added. Pool contention documented. |
| v2.3 | June 9, 2026 | **§0.5: Codex Verification Pass (pre-build gate).** 8 claims (C1-C8) verified against code before any build. Read-only adversarial review with DRIFT report. Stop condition: ≥3 P1 DRIFT → halt. **Step 0 spike corrected:** measures fresh-per-query vs pooled side-by-side (isolates connection tax from query cost). Keyed point lookup (not scan-then-LIMIT). Write rolled back (f8 untouched). Three-outcome gate with diagnostic branch messages. |

**Review notes (items to track, not blocking):**
- SOC `source_sequence_count` (by source_location) was in v1.x,
  dropped in v2.1. Confirm referral engine uses user-level counts
  only, or re-add as a SOC CounterDef.
- Multi-worker counter test (#5 in §10) requires multi-process test
  harness (2 uvicorn workers). Implementation is non-trivial.
- All pooled-read timings (~5ms) are contingent on Step 0 spike
  confirming connection-tax hypothesis. If pooled reads are still
  50ms, the ~111ms target becomes ~161ms (still acceptable).
- `cache.note_decision()` in pipeline code: clarify semantics. Does
  it update a "last decision time" on the cached entity, or is it a
  no-op? If entity context is truly unchanged by decisions, it's a
  no-op and can be removed for clarity.

**References:**
- soc_campaign_identity_architecture_v1_3.md
- dk_runtime_execution_plan_v6.9
- Master Action Plan v5.44 (#117 / #150 / #179, Rules #40 / #48)
- Phase-C trace + F8 proof reports
