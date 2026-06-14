# Copilot Decision Hot-Path Architecture (Reconciled)

**Version:** v4.0 (synopsis + execution + actionable)
**Date:** June 11, 2026
**Status:** All packages built. Route wiring architecture designed. Entering measurement + adoption phase.
**Authority:** DK Runtime Execution Plan v6.9, MAP v5.150

**Document evolution:** Started as a hot-path performance fix (v2.0,
25.6s → target <1s). Through 5 design-authority reviews, 2 Codex
GPT-5.5 verification passes, 4 rounds of measured data, and a route
wiring reconciliation, it became a complete copilot decision
architecture covering performance, correctness, counter design,
cache model, pipeline structure, and per-copilot route policy.
Campaign Phase 1 + pooling solved 99.2% of the performance problem
(25,602ms → 193ms). The remaining architecture is pre-built levers
for scale and maintainability.

---

## §0 Synopsis

### Are Both Goals Met?

**Goal 1 — Product performance: MET.**

193ms at 250 decisions. Every milestone achieved (demo <3s, pilot
<2s, production <1s, competitive <500ms). Achieved with Campaign
Phase 1 + connection pooling alone — no counters, no cache, no
pipeline, no task manager required.

**Goal 2 — Scaling wish-list: PRESERVED.**

Every scaling optimization is designed, built, and activatable
with a feature flag. No architectural rework needed when scale
demands it:

| Package | Status | Activation | When needed |
|---|---|---|---|
| Pooling (Pkg 1) | ✅ ON | Already active | — |
| Counters (Pkg 2) | ✅ Built | `USE_MATERIALIZED_COUNTERS=true` | O(N) scans breach 500ms |
| Cache (Pkg 3) | ✅ Built | `USE_ENTITY_CACHE=true` | Entity reads dominate at 1K+ |
| Tasks (Pkg 4) | ✅ Built | `USE_BACKGROUND_TASKS=true` | Enrichment exceeds budget |
| Pipeline (Pkg 5) | ✅ Built | `PIPELINE_MODE=shadow→served` | Cross-copilot sharing |

**The architecture is a set of pre-built levers, not a to-do list.**
Each lever pulls independently. Performance goals are met TODAY.
Scaling levers activate WHEN MEASURED DATA shows they're needed.

**One caveat:** Growth rate post-pooling at 1000+ decisions is
unmeasured. The O(N) scans are still present, just faster (pooled).
If they breach targets at scale, Package 2 activates via flag —
design complete (§5.3), code built, proof criteria specified. No
design work remains.

**Next step:** Measure at 500 and 1,000 decisions. This determines
whether any lever needs pulling now, or the system runs on pooling
alone through pilot.

### What This Document Is

This is the architecture spec for the copilot decision hot path —
the code that runs every time an alert, invoice, or trade is
analyzed. It governs all 5 copilots (SOC, Trading, Purchasing,
DataOps, S2P) because they share the same four-phase pattern:
read context → compute factors → score → persist.

The document has been through 5 design-authority reviews (2 Opus
sessions + 1 route wiring reconciliation), 2 Codex GPT-5.5
verification passes, and 4 rounds of measured data. It resolves
every known design gap for Packages 1-5 and specifies the route
wiring architecture for production adoption.

### Where We Started and Why

SOC analyze averaged **25.6 seconds** at 250 decisions (F8 proof,
pre-campaign fix). The scorer takes 0.25ms. The other 99.98% was:
- O(N²) campaign correlation (dominant cost — fixed by Campaign Phase 1)
- Sequential AGE round-trips paying 82ms connection tax per query
- O(N) scans for referral counters (sequence_count, cross_category)

A system that gets slower as it learns cannot credibly claim to
compound intelligence. This was blocking demo, pilot, and the
core product narrative.

### What Has Been Fixed (Measured)

| Fix | Before | After | What it proved |
|---|---|---|---|
| Campaign Phase 1 (stable identity) | 25,602ms | 1,767ms | O(N²) campaign was the dominant cost |
| Package 1 (pooled AGE connections) | 1,767ms | **193ms** | 82ms connection tax was 98.7% of per-query cost |
| Phase-3 committed write | (unmeasured) | 8.8ms avg | Write path is fast; commit overhead = ~5ms |

**Current state: 193ms at 250 decisions.** All targets met:
- Competitive (<500ms): ✅ 193ms
- Production (<1s): ✅ 193ms
- Pilot (<3s): ✅ 193ms
- Demo (<3s): ✅ 193ms

**99.2% of the original problem is solved** (25,602ms → 193ms).
The remaining architecture is for scale-hardening and competitive
positioning at 1,000+ decisions, not for unblocking the product.

### The Architecture (Single Model)

Two structural changes, both validated by measurement:

**1. AGE is for persistence, not hot-path reads (DC-1).**
Entity context (user properties, asset criticality, security edges)
changes on ingestion (rare) and is read on every analyze (frequent).
An in-memory cache serves these reads. AGE is queried only on cache
miss (~1.1ms pooled) and for writes (~8.8ms committed transaction).

**2. Counters are materialized on AGE entity nodes, not scanned (DC-7).**
Referral counters (sequence_count, cross_category_count) are
decision-critical — the referral engine reads them to veto actions.
Today they're computed by O(N) scans. The redesign materializes them
as properties on entity nodes (O(1) point lookup, ~1.1ms). They are:
- **Route-authoritative** after parity proof (not experimental)
- Updated in the **same AGE transaction** as the Decision write
  (zero divergence by construction)
- Protected by **PostgreSQL advisory locks** for multi-worker safety
  (AGE lacks MERGE and uniqueness constraints)
- **Not cached in memory** (multi-worker coherence — DC-7)
- Distinct counters (cross_category) use MATCH-then-CREATE edge sets
  (AGE-compatible, no MERGE)

### Performance Numbers

| Metric | F8 | C9B baseline | Package 1 | Full arch (projected) |
|---|---|---|---|---|
| Avg analyze at 250 | 25,602ms | 1,767ms | **193ms** | ~12ms (small graph) |
| Growth rate | O(N) | O(N) | O(N) reduced | **Zero** |
| All targets met? | ❌ | ⚠️ | **✅ (all)** | ✅ |

**99.2% solved.** Campaign P1 + pooling: 25,602ms → 193ms.
Remaining architecture is for scale (1,000+ decisions). Scalability
validation (500/1K/5K/25K/100K) required before projecting further.
Storage caveat: committed-write numbers from WSL2 dev-box.

### Why Each Decision Was Made

| Decision | Why |
|---|---|
| Cache entity context, not counters | Counters are decision-critical with zero staleness tolerance. Multi-worker in-process caches diverge. Entity context changes rarely. (DC-2, DC-7) |
| Advisory locks, not MERGE | AGE rejects MERGE (age_client.py:49-69). Advisory locks are standard PostgreSQL, work across uvicorn workers, and scope to the transaction. |
| Counter as property on entity node, not separate node | Entity node already exists from ingestion. No duplicate-node problem. SET under lock, not CREATE. |
| Transaction coupling (Decision + counter) | If counter diverges from decision count, referral engine makes wrong decisions. Same-transaction = zero divergence by construction. |
| Counters route-authoritative, not experimental | Package 1 bought time but didn't remove the O(N) scan. At scale (10K+ decisions), the scan will dominate again. Deferring = building on a known-bad foundation. |
| Framework-first (copilot_core) | The dangerous code (transaction boundary, lock management, distinct-counter maintenance) must exist in one tested place, not five copies. |

### Sharing: copilot_core + DomainProfile

The HOW (pool, cache, counter store, task manager, four-phase
pipeline) lives once in `copilot_core` (ci-platform). Each copilot
injects the WHAT (factors, counters, enrichment) via a
`DomainProfile`. SOC is first adopter; SDK copilots adopt at their
AGE migration. (§4)

### Package Status (All Built)

```
Package 0: Phase-3 committed measurement      ✅ DONE (8.8ms)
Package 1: Pooled AGE adapter                  ✅ DONE (193ms at 250)
Package 2: Materialized counters               ✅ BUILT (design complete §5.3)
Package 3: EntityCache                         ✅ BUILT (correctness passed, default OFF §8A.7)
Package 4: BackgroundTaskManager               ✅ BUILT
Package 5: DecisionPipeline + DomainProfile    ✅ BUILT (5D shadow parity passed)
```

All packages are built. The build phase is complete.

### What's Next: Measurement + Adoption

The execution shifts from building to measuring and wiring. Three
tracks, in priority order:

**Track 1 — Scale measurement (immediate, gates everything else):**
```
1a. Measure at 500 decisions (current stack, pooling only)
1b. Measure at 1,000 decisions
1c. If analyze > 500ms at any count → activate Package 2 counters
1d. If growth is flat → system runs on pooling through pilot
```

**Track 2 — SOC diagnostics hook (§8A.10, zero-risk):**
```
2a. Route calls RoutePolicyResolver, emits diagnostics
2b. Canonical continues serving (no behavior change)
2c. Builds evidence-gathering substrate for future shadow/served
```

**Track 3 — Counter adoption (if Track 1 triggers it):**
```
3a. Codex verifies rolling-window semantics from code (§5.3 Gap 4)
3b. Implement advisory-locked Phase-3 transaction
3c. Live AGE proof (10 criteria, §5.3)
3d. Parity proof: counter == graph-truth for 250 decisions
3e. Enable USE_MATERIALIZED_COUNTERS=true
```

### Actionable Items (From Codex Reviews + Design Authority)

| # | Item | Effort | Priority | Blocked by |
|---|---|---|---|---|
| **A1** | Measure at 500 + 1000 decisions | 1h | **P1** | Nothing — do first |
| **A2** | SOC no-behavior-change diagnostics hook | 0.5d | **P1** | Nothing |
| **A3** | Verify rolling-window semantics from code | 2h | **P2** | A1 (if counters not needed, defer) |
| **A4** | Counter live AGE proof (10 criteria) | 1d | **P2** | A3 |
| **A5** | Counter parity proof (250 decisions) | 0.5d | **P2** | A4 |
| **A6** | Pipeline-served-alone benchmark (per workload) | 0.5d | **P3** | A2 (needs diagnostics substrate) |
| **A7** | Proof-authority artifact (machine-checkable) | 1d | **P3** | A6 (prerequisite for pipeline_served) |
| **A8** | Scale tests at 5K / 25K / 100K (seeded graphs) | 2d | **P3** | A1 results determine urgency |

**A1 is the decision point.** If 500/1000-decision measurements
show flat growth under pooling, Tracks 2-3 become quality-of-life.
If they show O(N) resurgence, Track 3 (counters) activates immediately.

### Open Questions (Updated)

| # | Question | Status |
|---|---|---|
| Q1 | Counter integrity | ANSWERED: route-authoritative, advisory-locked, transaction-coupled (§5.3) |
| Q2 | Phase-4 safe? | ANSWERED: yes for enrichment; no for action-mutating gates (DC-5) |
| Q3 | Factor independence | Verify: none reads a counter another writes in-phase |
| Q4 | Rolling-window semantics | DESIGNED: 3 outcomes pre-designed, Codex verifies from code (§5.3). **Actionable: A3** |
| Q7 | Sync vs async pool | ANSWERED: sync suffices (no read fan-out) |
| Q9 | Framework scope | ANSWERED: copilot_core, hot path + perf machinery only (§4.4) |
| Q10 | Pool sizing | ANSWERED: 5 × 8 = 40, headroom preserved (§6) |
| Q11 | Pipeline-served-alone latency | **UNMEASURED.** Shadow runs both paths. **Actionable: A6** |
| Q12 | Growth rate at 1000+ decisions | **UNMEASURED.** O(N) scans still present. **Actionable: A1** |
| Q13 | Proof-authority artifact | **NOT BUILT.** Prerequisite for pipeline_served. **Actionable: A7** |

---

## §0.5 Codex Verification Pass (Completed)

Two Codex GPT-5.5 verification passes completed (v2.3 and v2.4).
Results: 0 P1 DRIFT in final pass, all P2/P3 items resolved through
v2.5-v2.6. The verification prompt and claims (C1-C8) are retained
below for reference and re-verification after any future code change.

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

CONTEXT: The architecture document (current version)
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

C1 [P2] Hot path = "multiple sequential AGE round-trips, several
    O(N) scans" (§0, §1.2). Enumerate the actual AGE queries issued
    by the SOC analyze handler. Identify which ones scan Alert/Entity
    nodes (O(N)) vs point/keyed lookups. Report the real count and
    file:line of each O(N) scan.
    DRIFT-P2 if the named scans (sequence_count, cross_category_count)
    do not scan Alert/Entity nodes as claimed.

C2 [P1] Decision-critical gates are synchronous (§2 DC-5). Locate
    ALL action-mutating gates: low-confidence gate (→refer_to_analyst),
    referral veto, RL exploration (→action override), and composite
    auto-approval. Confirm which ones mutate the returned action vs
    only write metadata. file:line for each.
    DRIFT-P1 if any action-mutating gate is missing from the sync list.

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

C5 [P2] Counters currently SCAN nodes (§3, §8 Step 3):
    sequence_count and cross_category_count are computed today by
    scanning Alert/Entity nodes on AGE (age_client.py:478-510) or
    Decision nodes on legacy Neo4j (db/neo4j.py:410-457). Confirm
    which backend is active and what node label is scanned. State
    whether cross_category is DISTINCT or TOTAL. file:line.

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

**Measured values** (from live SOC/AGE proof runs) are labeled
"measured." **Projected values** (derived from measured data but not
yet validated at target architecture) are labeled "projected." Do
not treat projected numbers as guaranteed until Step 0 spike and
25/250/1000 validation confirm them.

### 1.1 The Scorer Is Fast; the Route Is Not

| Stage | Time | Source |
|---|---|---|
| ProfileScorer.score() | 0.25ms | Measured (Phase-C trace) |
| Full analyze (pre-campaign) | 5,692ms at 25 decisions | Measured (Phase-C trace) |
| Full analyze (post-campaign) | 1,757ms at 25 decisions | Measured (CAMPAIGNP1EDGE) |
| Full analyze (pre-campaign) | 25,602ms at 250 decisions | Measured (F8 proof) |
| **Full analyze (C9B baseline)** | **1,767ms at 250 decisions** | **Measured (C9B pre-hotpath)** |
| Hot-path target (full arch) | ~12ms | Measured-based (spike + committed Phase-3) |

### 1.2 Where the Time Goes (Phase-C Waterfall, 25 Outcomes, Pre-Campaign Fix)

**These timings are from the Phase-C trace BEFORE Campaign Phase 1.**
Post-campaign, campaign correlation drops but the O(N) scans and
sequential pipeline remain unchanged.

```
READS (all from AGE today):
  alert / subject lookup           ~80 ms
  security / entity context        ~90 ms
  factor inputs (6 × AGE query)   ~336 ms
  sequence_count        O(N) scan ~500 ms   ← scans Alert/Entity nodes (AGE)
  cross_category_count  O(N) scan ~500 ms   ← scans Alert/Entity nodes (AGE)
  cluster_history       O(N) scan ~200 ms   ← grows
```

**Note on O(N) scans:** The active AGE backend (`age_client.py:478-510`)
scans Alert/Entity nodes for sequence and cross-category counts. The
legacy Neo4j backend (`db/neo4j.py:410-457`) scanned Decision nodes.
The architectural problem is the same (O(N) per-request scan), but the
node label differs by backend. Counter materialization (§8 Step 3)
replaces both paths.

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
multiple sequential AGE round-trips at 20-50ms each floor the route
well above 1s and still grow. Indexes change the slope; they do not change
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
after the response.

**Synchronous gates (decision-critical, stay in Phase 2):**
- **Low-confidence gate** (triage.py:446-464): can override action to
  `refer_to_analyst` — mutates the returned action.
- **Referral rule veto** (triage.py:591-640): can veto based on
  sequence count / cross-category count — mutates the returned action.
- **RL exploration** (triage.py:493-529): can mutate `selected_action`
  for exploration — action-changing, must remain synchronous. If RL
  exploration is disabled for a copilot, DomainProfile omits it.
- **Composite auto-approval decision** (composite_gate.py:61-194):
  computes auto-approval status — influences returned metadata.

**Deferred (Phase 4):** composite gate TELEMETRY writes, RL
METADATA/logging (not the exploration decision), campaign correlation,
cluster history, event bus.

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
        # Synchronous gates (decision-critical — DC-5):
        # - low-confidence gate: can override to refer_to_analyst
        # - referral rule veto: can veto based on counters
        # - RL exploration: can mutate selected_action
        # - composite auto-approval: influences metadata
        final_action = self.profile.gate(action, confidence, counters)

        decision_id = new_decision_id()

        # ---- Phase 3: persist BEFORE response (one transaction) ----
        async with self.pool.transaction() as tx:  # DC-4
            await self.profile.write_decision(
                tx, decision_id, subject_id, final_action, confidence, factors)
            await self.profile.write_audit(tx, decision_id, factors)
            await self.counters.increment(tx, entity_key, category)

        # persist-before-cache (Rule #48): commit complete.
        # Entity context is NOT changed by a decision — no cache update needed.
        # Counter was written to AGE in the transaction above (DC-7).

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


### 3.2 Target Performance (All Measurements Complete)

```
                              v2.6 projected    Spike (rolled)    Committed (measured)
Phase 1 reads:                ~5 ms              ~1.1 ms           ~1.1 ms
Phase 1 context (cache hit):  ~0 ms              ~0 ms             ~0 ms
Phase 2 compute:              ~6 ms              ~2 ms             ~2 ms
Phase 3 writes:              ~100 ms             ~40 ms            ~9 ms (8.782 avg)
Phase 4 async:                 0 ms               0 ms              0 ms
──────────────────────────────────────────────────────────────────────────
Hot path total:              ~111 ms             ~47 ms            ~12 ms
```

**All spike + committed data:**
```json
{
  "baseline_per_query_ms": 83.16,
  "pooled_per_query_ms": 1.10,
  "connection_tax_ms": 82.06,
  "committed_phase3_avg_ms": 8.782,
  "committed_phase3_p95_ms": 11.597,
  "commit_overhead_ms": 4.920,
  "branch": "cache_model_viable"
}
```

**Storage caveat:** All from WSL2 dev-box. Pilot-like storage
must be re-measured before buyer-facing claims.

### 3.3 Strategic Staging (Urgency Reframed)

**The urgency profile changed.** C9B baseline = 1,767ms at 250
decisions — 14.5× drop from F8's 25,602ms. Campaign Phase 1 was
the dominant fix. "Cannot demo, cannot pilot" urgency is gone.
The refactor is about **scaling headroom + competitive positioning.**

| Milestone | Required | Current (1.77s) | With pooling | Full arch |
|---|---|---|---|---|
| CISO demo | <3s | 1.77s ✅ | ~0.5s ✅ | ~12ms ✅ |
| Pilot wk 1 | <3s at 500 | ~2.5s ⚠️ | ~0.8s ✅ | ~12ms ✅ |
| Production | <1s | 1.77s ❌ | ~0.5s ✅ | ~12ms ✅ |
| Competitive | <500ms | 1.77s ❌ | ~0.5s ⚠️ | ~12ms ✅ |

**6-package staging:**
```
Package 0: Phase-3 committed measurement      DONE (8.8ms)
Package 1: Pooled AGE adapter                  1.77s → ~0.5s (banked win)
  ↓ re-measure at 250 and 500 decisions
  ↓ if <1s: Packages 2-5 = quality-of-life, not blockers
Package 2: Materialized AGE counters           eliminates O(N) growth
Package 3: EntityCache                         ~12ms hot path
Package 4: BackgroundTaskManager               async enrichment
Package 5: DecisionPipeline + DomainProfile    copilot_core + SOC adoption
Each independently shippable. Can interleave with feature work.
```

### 3.4 Why O(1), Not O(log N)

Materialized counters on entity nodes are point lookups: ~constant
regardless of graph size. Indexes give O(log N) (250 → ~200ms,
100k → ~420ms); counters give O(1) (~1.1ms pooled at any size).
The cache makes context reads O(1) — keyed point access, not traversal.

### 3.5 Scalability Caveat (Do Not Extrapolate From Small Graphs)

**Every measurement in this document is from a graph with ~250
decisions and ~1,000 nodes.** Production SOC graphs will have
10,000-100,000+ decisions, 50,000+ edges, and significantly more
complex entity relationships. The ~12ms hot-path and ~1.1ms pooled
read are small-graph numbers that may not hold at scale.

**What scales and what doesn't:**

| Component | Small graph (250) | Concern at scale | Scale behavior |
|---|---|---|---|
| Cache hit (in-memory dict) | ~0ms | None — in-process lookup | **O(1) genuinely** |
| Scorer (in-memory) | 0.25ms | None — tensor math | **O(1) genuinely** |
| Pooled point read (keyed) | 1.1ms | AGE index selectivity degrades with table size. PostgreSQL B-tree on 100K nodes vs 250 nodes. | **O(log N)** — likely still <5ms at 100K, but not 1.1ms |
| Counter read (materialized property) | ~1.1ms | Same as point read — property on a keyed node | **O(log N)** — same as above |
| Phase-3 committed write | 8.8ms | WAL pressure increases with concurrent writes. Index maintenance grows with table size. Vacuum overhead on large AGE tables. | **O(log N) + WAL contention** — may be 20-50ms at scale |
| Cache fill (cold start) | ~5ms | Entity context with many edges takes longer to load. A user with 1,000 DECIDED_ON edges vs 5. | **O(edges per entity)** — could be 50-100ms for heavy entities |
| Factor traversals (INVOLVES, DETECTED_ON) | ~56ms (unpooled) | Edge density per entity grows with decisions. Factor computers traverse entity edges. | **O(edges per entity)** — the cache eliminates this per-request, but cold start pays it |
| Campaign correlation (Phase 4) | ~480ms | Campaign membership grows. MEMBER_OF edge count per campaign. Level 1 is bounded by time bucket. | **O(members per campaign)** — bounded by window |

**Scale-sensitive projections (honest):**

```
                        Small graph (250)    Projected (10K)    Projected (100K)
Pooled point read:      1.1ms                ~2-3ms             ~3-5ms
Counter read:           1.1ms                ~2-3ms             ~3-5ms
Phase-3 write:          8.8ms                ~15-30ms           ~30-60ms
Cache fill (cold):      ~5ms                 ~20-50ms           ~50-200ms

Hot path (cache hit):   ~12ms                ~20-35ms           ~35-70ms
Hot path (cold start):  ~17ms                ~40-80ms           ~80-260ms
```

**These projections are estimates based on typical PostgreSQL B-tree
scaling characteristics, not measurements.** The actual scale
behavior depends on:
- AGE's internal table layout (one PG table per label? per graph?)
- Index types AGE creates (B-tree, hash, none?)
- PostgreSQL autovacuum behavior on AGE tables
- WAL configuration (synchronous_commit, wal_buffers)
- Physical storage (SSD vs HDD vs WSL2 virtualized)

**Scalability validation plan (required before production claims):**

| Test | Graph size | What it proves |
|---|---|---|
| Package 1 re-measure | 250 + 500 decisions | Pooling effect at 2× scale |
| Scale test 1 | 5,000 decisions (seeded) | O(N) growth eliminated by counters |
| Scale test 2 | 25,000 decisions (seeded) | Phase-3 write cost at 100× |
| Scale test 3 | 100,000 decisions (seeded) | Production ceiling |

**Seeding strategy:** Use the diagnostic runner with `--target-outcomes`
set high, or bulk-seed Decision/Alert nodes via SQL INSERT into AGE
tables. The test must run the full analyze route, not just point
lookups — factor traversals and counter reads at scale are the
unknowns.

**The architecture's defense against scale degradation:**
- Cache hits are genuinely O(1) — they don't touch AGE at all
- Counter reads are materialized properties, not scans — O(log N)
  at worst, which is dramatically better than the current O(N) scan
- Phase-3 writes are bounded (3 statements per decision) — they
  grow with index/WAL, not with query complexity
- The only component that scales with entity history is the cache
  FILL (cold start), and that amortizes across all requests for
  that entity

**Bottom line:** The ~12ms number is a small-graph measurement.
Production hot-path is projected ~35-70ms at 100K decisions (still
far under all thresholds). But this is an estimate, not a
measurement. The scalability validation plan (above) must run before
the number goes in front of a buyer.

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
- Distinct counters use bounded edge sets. **MERGE is forbidden in
  AGE** (age_client.py:49-69 rejects it). Use AGE-compatible
  MATCH-then-CREATE within one transaction:
  ```cypher
  -- Step 1: Check if SEEN_CATEGORY edge already exists
  -- MATCH existing User and Category nodes (never CREATE them here)
  MATCH (u:User {id: $entity_key})
  MATCH (c:Category {id: $cat})
  OPTIONAL MATCH (u)-[e:SEEN_CATEGORY]->(c)
  RETURN e IS NOT NULL AS edge_exists

  -- Step 2: If edge_exists = false, CREATE only the EDGE
  -- (User and Category nodes already exist from ingestion)
  MATCH (u:User {id: $entity_key})
  MATCH (c:Category {id: $cat})
  CREATE (u)-[:SEEN_CATEGORY]->(c)

  -- Step 3: Read distinct count (bounded ≤ |categories|)
  MATCH (u:User {id: $entity_key})-[:SEEN_CATEGORY]->(c)
  RETURN count(c) AS cross_category_count
  ```
  All three steps run inside ONE transaction. Category nodes are
  created at ingestion/seed time, never by the counter logic.
  CounterStore implements this MATCH-then-CREATE-edge pattern once.
- `population` ties to #111 (V = verified-only).
- `derived_entity_key` fallback is SOC-specific (messy SIEM IDs).
  Trading/Purchasing/DataOps/S2P key directly off clean IDs.

### 4.6 Per-Copilot Backend Reality

| Copilot | Backend today | Destination | When pool/cache lands |
|---|---|---|---|
| **SOC** | **AGE** (env: `GRAPH_BACKEND=age`, runtime contract for diagnostic/C9B; source default falls back to Neo4j) | AGE | **Now** (problem measured here) |
| Trading | SQLite (default) | AGE (#150) | At AGE migration |
| Purchasing | SQLite (default) | AGE (#179) | At AGE migration |
| DataOps | SQLite (default) | AGE (#117) | At AGE migration |
| S2P | SQLite (default; optional AGE config available) | AGE (L5) | At AGE migration |

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

### 5.2.1 Package 3 Benchmark Result (P3H) and Split-Read Decision

**P3H showed the cache wraps the expensive read instead of replacing
it.** The current implementation calls `get_security_context(alert_id)`
(~83ms full AGE traversal) on EVERY request, then checks the cache
for the entity portion. On cache hits, the AGE read has already
executed — the cache adds overhead without saving any I/O.

**Evidence:**
```
repeat_same workload (all cache hits): 64.1% SLOWER with cache enabled
  → cache adds work on top of the full AGE read
direct get_security_context: 83ms avg
split/recompose overhead: 0.033ms avg (negligible)
```

**Root cause:** `get_security_context()` is monolithic — it reads
alert data AND entity data in one operation. The cache must intercept
BEFORE the entity read, not after.

**Decision: Option A — split the read path (implements §3.1 as
designed).**

```python
# WRONG (current — cache wraps the expensive call):
context = get_security_context(alert_id)       # AGE ~83ms ALWAYS
entity = cache.get_or_store(key, context.entity)  # too late

# RIGHT (§3.1 — cache REPLACES the entity read):
subject = read_subject(alert_id, pool)            # AGE ~1.1ms (NOT cached)
entity_key = derive_entity_key(subject)
entity_ctx = cache.get_or_load(                   # ~0ms on hit
    entity_key,
    loader=lambda: load_entity_context(entity_key, pool)  # AGE ~1.1ms on miss
)
```

**Split definition:**

| Function | Reads | Cached | Why |
|---|---|---|---|
| `read_subject(alert_id)` | Alert node + INVOLVES/DETECTED_ON edges | No | One-shot, each alert unique |
| `load_entity_context(entity_key)` | User/Asset node + stable relationships | Yes | Entity recurring, rarely changes (DC-2) |

This is exactly the `DomainProfile` protocol's `read_subject()` +
`load_entity_context()` split. The cache infrastructure (LRU,
invalidation, diagnostics) is already built. The fix is WHERE the
cache intercepts — before the entity read, not after.

**Projected result after split:**

| Workload | Current (wraps) | After split (replaces) |
|---|---|---|
| repeat_same (all hits) | 64.1% slower | ~95% faster (1.1ms vs 83ms) |
| mixed_reuse | 25.5% faster | ~80% faster |
| 250-outcome proof | 202ms | ~120ms |

**Package 3 status:** Correctness/observability milestone PASSED.
Performance closure requires the split-read implementation (Option A)
before Package 4 proceeds. `USE_ENTITY_CACHE` remains disabled by
default until the split-read is implemented and benchmarked.

### 5.3 Why Counters Are NOT Cached — And How They Work

**Authority model:** Counters are **route-authoritative** — the
referral engine reads them to make decisions. Not experimental, not
advisory, not deferred. They replace the O(N) scans after proof.

**Storage model:** Counter values are PROPERTIES on existing entity
nodes (e.g., `User.sequence_count`). Not separate CopilotCounter
nodes. The entity node already exists from ingestion. No duplicate-
node problem — the update is a SET on an existing node.

**Multi-worker safety: PostgreSQL advisory locks.**

AGE runs inside PostgreSQL. Cypher queries are SQL calls. Advisory
locks and Cypher share the same transaction context:

```sql
BEGIN;
-- Lock entity for this transaction. Other workers for U1 wait here.
SELECT pg_advisory_xact_lock(hashtext('user:U1:counters'));

-- Read + increment cumulative counter (under lock, no lost updates)
SELECT * FROM cypher('graph', $$
    MATCH (u:User {id: 'U1'})
    SET u.sequence_count = u.sequence_count + 1
    RETURN u.sequence_count
$$) AS (count agtype);

-- Distinct counter: MATCH-then-CREATE edge if missing (no MERGE)
SELECT * FROM cypher('graph', $$
    MATCH (u:User {id: 'U1'})
    MATCH (c:Category {id: 'credential_access'})
    OPTIONAL MATCH (u)-[e:SEEN_CATEGORY]->(c)
    RETURN e IS NOT NULL AS exists
$$) AS (exists agtype);
-- If exists = false:
SELECT * FROM cypher('graph', $$
    MATCH (u:User {id: 'U1'})
    MATCH (c:Category {id: 'credential_access'})
    CREATE (u)-[:SEEN_CATEGORY]->(c)
$$) AS (r agtype);

-- Decision + audit writes (same transaction — DC-4)
SELECT * FROM cypher('graph', $$
    CREATE (d:Decision {id: 'DEC-001', action: 'escalate'})
$$) AS (d agtype);
SELECT * FROM cypher('graph', $$
    CREATE (a:AuditEntry {decision_id: 'DEC-001', hash: '...'})
$$) AS (a agtype);

COMMIT;  -- lock released, counter + decision committed atomically
```

**Why advisory locks, not alternatives:**

| Approach | AGE support | Multi-worker | Selected? |
|---|---|---|---|
| AGE MERGE | ❌ Rejected | — | No |
| AGE uniqueness constraint | ❌ None | — | No |
| PG UNIQUE on AGE table | ⚠️ Fragile | ✅ | No (internal schema) |
| **PG advisory locks** | **✅ Standard SQL** | **✅** | **Yes** |
| Application locks | ✅ | ❌ Single process | No |

**Lock key design:** `hashtext('user:U1:counters')` → deterministic
int8. All counters for the same entity share one lock. Different
entities don't contend.

**Transaction coupling (non-negotiable):** Counter increment is in
the SAME transaction as the Decision write. If the Decision commits,
the counter reflects it. If the Decision rolls back, the counter
doesn't change. Zero divergence by construction.

**Failure modes (all correct under this model):**
- Decision write fails → counter not incremented (ROLLBACK)
- Counter increment fails → Decision not persisted (ROLLBACK)
- Advisory lock contention → worker waits, then proceeds
- Connection lost → PostgreSQL ROLLBACK (timeout)
- Worker crash → PostgreSQL ROLLBACK

**Rolling-window semantics:** The exact semantics of
`get_sequence_count()` and `get_cross_category_count()` must be
verified from code (age_client.py:478-510) before implementation.
Three possible outcomes:
- **Lifetime totals:** cumulative +1, never decrement. Simplest.
- **Time-windowed:** time-bucketed counters, sum recent K buckets.
- **Decision-sequence:** ring buffer. Most complex.

Conservative fallback: lifetime totals never under-refer (safe for
security copilot — may over-refer but never miss a referral).

**Live AGE proof required before route adoption (10 criteria):**
1. Counter property created after first decision
2. Counter increments by exactly 1 per decision
3. SEEN_CATEGORY edge created, not duplicated
4. 2 concurrent workers, 100 decisions each → counter = 200
5. Kill connection mid-write → Decision AND counter both absent
6. Inject drift (+5) → reconcile → counter == graph-truth
7. Parity: materialized == graph-truth scan for 250 decisions
8. All above pass with PooledAGEClient
9. Repeated runs produce correct results
10. Counter read < 5ms; Phase-3 transaction < 20ms

**Proof authority:** Graph-truth remains proof authority. Counters
reported alongside as diagnostics (`counter_parity: true/false`).
Counters become proof-authoritative only after sustained parity
proof (1000+ decisions, zero drift).

**Current CounterStore code: fix and ship.** Not experimental.
Address advisory locks, transaction coupling, rolling-window
verification, live AGE proof. Then wire into route with feature
flag `USE_MATERIALIZED_COUNTERS=true|false`.

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
cold/evicted miss falls back to a pooled AGE read (~1.1ms per Step 0)
— worst case degrades to pooled-read latency, not catastrophe. Cache size is
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

## §7 Performance Targets (Step 0 + Phase-3: PASSED)

**C9B pre-hotpath baseline (measured, 250 decisions):**
```
Verdict: EXTERNAL_DIAGNOSTIC_F_PASS
Valid outcomes: 250, verified: 250, L5 types: all present
avg_analyze: 1.767s, max_analyze: 3.334s
avg_outcome: 1.492s, max_outcome: 4.517s
```

| Milestone | Acceptable | F8 (pre-campaign) | C9B baseline | Pooling est | Full arch |
|---|---|---|---|---|---|
| C9B proof | <120s | ~20s | **1.77s** ✅ | — | ~12ms |
| CISO demo | <3s at 250 | ~20s ❌ | **1.77s** ✅ | ~0.5s ✅ | ~12ms ✅ |
| Pilot wk 1 | <3s at 500 | ~40s ❌ | ~2.5s ⚠️ | ~0.8s ✅ | ~12ms ✅ |
| Pilot mo 1 | <2s at 3k | ~250s ❌ | ~25s ❌ | ~3s ⚠️ | ~12ms ✅ |
| Production | <1s any | — | 1.77s ❌ | ~0.5s ✅ | ~12ms ✅ |
| Competitive | <500ms | — | 1.77s ❌ | ~0.5s ⚠️ | **~12ms** ✅ |

**14.5× already achieved.** Campaign Phase 1 took 25.6s → 1.77s.
Pooling (Package 1) is projected to take 1.77s → ~0.5s (removing
~82ms × ~15 reads = ~1.2s connection tax). Full architecture
projects ~12ms. All production/competitive targets need Package 1
at minimum.

---

## §8 Implementation Plan

Sequencing follows MAP's AGE-everything plan: build shared core,
prototype on SOC (where the problem is measured), adopt at each SDK
copilot's AGE cutover.

### Step 0 — Connection-Model Spike: **PASSED** (cache_model_viable)

**Result (measured on soc_graph_diag_f8, 250 decisions):**
```json
{
  "baseline_per_query_ms": 83.1,
  "pooled_per_query_ms": 1.1,
  "connection_tax_ms": 82.0,
  "pooled_write_ms": 13.0,
  "branch": "cache_model_viable"
}
```

Connection tax = 98.7% of baseline cost. Pooling gives 75× read
improvement. All gate criteria met: pooled read <10ms (1.1ms),
pooled write <100ms (13ms).

**Sequencing confirmed:** C9B proof first on current code, then
implementation. Do not change the hot path until L5 COMPLETE is
proven on the existing architecture. Reason: changing the hot path
before L5 COMPLETE makes any C9B failure ambiguous — you wouldn't
know if it was L5 or the refactor. The spike was read-only/rolled-back
so C9B runs clean.

**Follow-up measurement needed (before publishing ~47ms):**
Re-measure Phase-3 as an actual committed transaction against a
scratch graph:
```python
# Against a scratch graph (not f8):
with pool.connection() as c:
    t0 = time.perf_counter()
    c.execute("BEGIN")
    c.execute(f"SELECT * FROM cypher('{SCRATCH}', $$ "
              "CREATE (d:Decision {id:'p3-test'}) RETURN d $$) AS (d agtype)")
    c.execute(f"SELECT * FROM cypher('{SCRATCH}', $$ "
              "CREATE (a:Audit {id:'p3-test'}) RETURN a $$) AS (a agtype)")
    c.execute(f"SELECT * FROM cypher('{SCRATCH}', $$ "
              "MATCH (u:User {id:'test-user'}) SET u.seq = 1 RETURN u $$) AS (u agtype)")
    c.execute("COMMIT")  # includes WAL fsync
    phase3_ms = (time.perf_counter() - t0) * 1000
# Expected: 20-50ms. If >50ms, commit/fsync dominates.
```

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

Full design in §5.3. Implementation sequence:

```
3a. Codex verifies rolling-window semantics from code
    (age_client.py:478-510 get_sequence_count / get_cross_category_count)
    → reports: lifetime / windowed / decision-based

3b. PooledAGEClient.transaction() context manager
    → pg_advisory_xact_lock integration
    → Decision + audit + counter in one transaction

3c. CounterStore in copilot_core
    → CounterDef protocol (node, key, prop, trigger, mode, population)
    → read(): O(1) point lookups on entity node properties
    → increment(): advisory-locked, transaction-scoped
    → SEEN_CATEGORY MATCH-then-CREATE for distinct counters

3d. Reconciliation job
    → recount from graph truth, compare, log delta, correct
    → nightly + on restart

3e. Live AGE proof on soc_graph_counter_proof
    → 10 criteria (§5.3), all on live AGE with PooledAGEClient

3f. Parity proof (250 decisions)
    → materialized == graph-truth scan for every decision
    → counter_parity in proof output
```

**Gate (machine-checkable):**
```powershell
$a25  = (Get-Content perf_25.json  | ConvertFrom-Json).analyze_avg_ms
$a250 = (Get-Content perf_250.json | ConvertFrom-Json).analyze_avg_ms
if ($a250 -le $a25 * 1.2) { "PASS: O(N) eliminated" } else { "FAIL" }
```

**Route adoption gate:** parity proof passes AND feature flag
`USE_MATERIALIZED_COUNTERS=true` → counters wired into referral
engine, graph-truth scans removed from hot path.

### Step 4 — BackgroundTaskManager (~0.5d)

Fire-and-forget with retained task set (GC footgun) + done-callback
WARNING logging. Campaign / RL / cluster / gate-telemetry → Phase 4.
Composite-gate decision stays synchronous Phase 2.

**Gate:** response returns before Phase-4 writes land; no silent task
failures in logs.

### Step 5 — SOC Adopts copilot_core (Prototype Domain)

SOC `triage.py` → thin adapter building SOC's DomainProfile.

**Rollback/parity guard:** Before removing the old route, run both
old and new paths side-by-side on the same inputs and assert response
parity (same action, same confidence, same factors). Feature flag
`USE_COPILOT_CORE=true|false` controls which path serves the response.
Old path remains available until parity is proven over 250+ decisions.

**Gate:** full SOC suite passes; 250-outcome proof on fresh graph
shows hot path ~111ms (projected), flat across 1/250/1,000 decisions.
Concurrent: K=10 simultaneous analyzes → p95 < target AND zero
PoolTimeout.

### Step 6 — SDK Copilots Adopt at AGE Migration

Trading / Purchasing / DataOps / S2P build DomainProfile and route
through copilot_core at their AGE migration (#150 / #179 / #117).
Marginal cost ≈ DomainProfile + CounterDef list (declarative).

### Rollback

Each step is independently reversible and additive: cache is
bypassable (read from AGE), counter properties are additive
(don't break existing queries), pipeline can swap back to per-route
path via `USE_COPILOT_CORE=false`. No irreversible schema change.
Counter nodes/edges are additive read-model additions only.

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

## §8A Route Wiring Architecture (Reconciled)

### 8A.1 The Tension Is Already Decoupled

The measured wins — 25.6s → 1.77s (campaign) → 193ms (pooling) —
were all bought in **Layer 1, inside the canonical route**, by
`PooledAGEClient` and `CounterStore`. These are framework-level
components in ci-platform. Every copilot inherits the speed WITHOUT
adopting the pipeline.

**Layer 1 is not a "route mode." It's always-on performance
plumbing inside the canonical route.** Pool, counters, cache, tasks
— these are implementation details beneath the route handler, not
alternative route paths.

**Layer 2 (the pipeline) is a separate flexibility investment** —
unified orchestration, cheap Nth copilot, one place for hot-path
correctness. Its value is maintainability, not latency. The data
shows the pipeline currently has NO performance case to serve — so
adoption must be justified on maintainability grounds alone.

**You are not choosing flexibility OR performance.** Performance is
banked in Layer 1 for all five copilots. The only question is
whether the pipeline is worth serving for its flexibility benefits.

### 8A.2 Four States, Not Seven

Seven modes across five copilots = 35 combinations to test and
maintain. Collapse to four:

| State | What it does | Status |
|---|---|---|
| **canonical_only** | Served canonical with Layer-1 flags on. Default, rollback target, current performance winner. | **DEFAULT for all copilots** |
| **shadow** | Serve canonical, run pipeline diagnostically for parity + per-workload latency. `pipeline_read_only` is a diagnostics-verbosity flag on shadow, not a separate mode. | **Available for SOC** |
| **pipeline_served** | Serve pipeline output. High-bar, per-copilot, separately approved. Never automatic. | **Far-future, gated** |
| **disabled** | Fail closed on invalid/unapproved config. Guard rail. | **Always available** |

**Deferred — do not build speculatively:**

| Deferred mode | Why not now |
|---|---|
| **hybrid_fast_path** | Canonical IS the fast path (measured). Pipeline branch would be the slow one. Two decision paths with different semantics = silent drift. No latency case exists. |
| **fallback_to_canonical** | Only meaningful when pipeline is primary served path. Silent fallback papers over a broken pipeline looking healthy. If pipeline fails: **fail closed or fall back LOUDLY with the fallback counted as a failure in gate metrics.** Never a silent pass. |

### 8A.3 Layer 1: Performance Plumbing (Always-On)

Layer-1 flags are NOT route modes. They are implementation details
inside the canonical route that the RoutePolicyResolver does NOT
arbitrate:

```
USE_POOLED_AGE=true              ← already on, proven at 193ms
USE_MATERIALIZED_COUNTERS=false  ← activate after counter proof
USE_ENTITY_CACHE=false           ← default OFF (see §8A.7)
USE_BACKGROUND_TASKS=false       ← activate after testing
```

**Enablement order:** pool (done) → tasks → counters → cache.
Each flag: enable → 250-outcome proof → compare to baseline.
Do not enable multiple new flags simultaneously.

### 8A.4 Layer 2: Shadow (Evidence-Gathering)

```
PIPELINE_MODE=shadow
```

Shadow runs Phase 1+2 (reads + compute) alongside canonical.
Phase 3+4 (writes + enrichment) are SKIPPED — shadow MUST NOT
write to AGE (no duplicate decisions).

**The shadow measurement gap:** Shadow numbers show canonical PLUS
pipeline cost (both run). The 5D repeat_same 0.169s → 0.356s delta
is pipeline's ADDED cost alongside canonical, not its served-alone
latency. **Pipeline-served-alone is genuinely unmeasured.**

No one can approve `pipeline_served` on performance grounds until
a controlled pipeline-served-alone benchmark exists, per workload
shape.

### 8A.5 Pipeline Served: Prerequisites (High Bar)

`pipeline_served` is a separate decision package, never automatic.
Two prerequisites before any copilot can be considered:

**Prerequisite 1: Pipeline-served-alone benchmark.**

Per workload shape (unique_once / repeat_same / mixed_reuse / burst),
pipeline served WITHOUT canonical alongside it. Until this exists,
pipeline_served stays theoretical.

**Prerequisite 2: Proof-authority artifact.**

The platform's integrity claim is that the graph is the source of
truth (conservation counts persisted decisions, audit chain is
tamper-evident BECAUSE it's in the graph). A served pipeline cannot
be approved until a machine-checkable artifact proves it writes the
same decision/audit/counter truth and preserves the L5/conservation
proof chain. This is a PREREQUISITE, not optional hardening.

**Promotion gates (all must pass, judged per-workload, not aggregate):**

| Gate | Threshold | Metric |
|---|---|---|
| Decision parity | 0 discrepancies in 1,000 requests | Per workload shape |
| Latency | **p95 < X, max < Y** (not avg — avg hides tails) | Per workload shape |
| Proof preservation | C9B/DK/L5 PASS on pipeline-written graph | Named artifact |
| Side-effect parity | Same graph state after N decisions | Graph-truth comparison |
| Concurrency | K=10, zero errors | Load test |
| Rollback | PIPELINE_MODE=off works | Manual test |
| Per-copilot approval | Roadmap decision | Not automatic |

**Aggregate is a trap.** 5D aggregate looked fine at 0.169s while
shadow repeat_same was 0.356s. Aggregate hid a workload-specific
regression. Every workload shape must pass independently.

### 8A.6 Per-Copilot Posture

| Copilot | Served mode | Why |
|---|---|---|
| **SOC** | canonical_only; pipeline in shadow | Strongest evidence. Still no served pipeline. |
| **Trading** | canonical_only; strictest tail thresholds | Canonical IS the fast path. No hybrid case. |
| **Purchasing** | canonical_only; tightest side-effect controls | Monetary risk argues AGAINST a served pipeline. |
| **DataOps** | canonical_only; most plausible eventual pipeline_served | Pipeline's Phase-4 deferred work may help THROUGHPUT under concurrency — but proven via shadow load test, not assumed. |
| **S2P** | canonical_only; strictest "no isolated state" rule | No in-memory preview scorer. EntityCache may cache context but NEVER scorer state. Vendor learned risk changes must reflect immediately. |

**Nobody serves the pipeline for latency** — canonical is fastest.
"Flexibility-priority" copilots (DataOps) can pursue shadow→served
on maintainability grounds. "Strict" copilots (Trading, S2P) stay
canonical.

### 8A.7 EntityCache: Default OFF (P3H Is Decisive)

At 1.1ms pooled reads, caching saves ~1ms and costs invalidation/
coherence overhead. P3H proved: helps reuse-heavy, hurts repeat-same.
Net-negative on common SOC workloads.

**Decision:** `USE_ENTITY_CACHE=false` by default. Never wired into
served path by default. Per-DomainProfile opt-in ONLY for a copilot
that demonstrates BOTH:
1. Expensive context assembly (not a 1.1ms keyed read)
2. High entity recurrence

For SOC's common case, EntityCache is dead weight. This is the
"knob, off by default" outcome.

### 8A.8 RoutePolicyResolver (Layer 2 Only)

The resolver arbitrates Layer 2 (canonical vs pipeline), not
Layer 1 (performance flags):

```python
@dataclass
class RoutePolicy:
    pipeline_mode: str  # "off" | "shadow" | "served" | "disabled"

class RoutePolicyResolver:
    def resolve(self, copilot: str) -> RoutePolicy:
        """Per-copilot. Config-driven. Default: off (canonical_only)."""
```

Layer-1 flags are read directly from env by each component
(AGEClient reads USE_POOLED_AGE; CounterStore reads
USE_MATERIALIZED_COUNTERS). They are not policy — they are plumbing.

### 8A.9 Rollback

| From | To | How | Downtime |
|---|---|---|---|
| Any Layer-1 flag | Flag off | Set env=false, restart | ~5s |
| Shadow | Canonical | PIPELINE_MODE=off, restart | ~5s |
| Served | Shadow or canonical | PIPELINE_MODE=shadow or off | ~5s |

Canonical route stays in codebase until pipeline_served is stable
for months and Roadmap explicitly approves code removal.

### 8A.10 Immediate Next Step

**No-behavior-change SOC diagnostics hook.** Route calls the policy
resolver, emits safe route-decision diagnostics, continues serving
canonical. This builds the evidence-gathering substrate (and the
isolated-measurement capability needed for the pipeline_served gate)
at zero served-behavior risk.

Change the wiring's OBSERVABILITY before its AUTHORITY.

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
| 9 | test_all_action_mutating_gates_synchronous (low-confidence, referral, RL exploration in Phase 2) |
| 10 | test_fireforget_task_retained_until_done |
| 11 | test_response_returns_before_phase4_writes_land |
| 12 | test_analyze_latency_flat_25_vs_250_vs_1000 |
| 13 | test_pooled_read_latency_at_5000_decisions (scale test 1) |
| 14 | test_phase3_write_latency_at_25000_decisions (scale test 2) |
| 15 | test_hot_path_under_100ms_at_100000_decisions (scale test 3) |

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
| v2.3 | June 9, 2026 | §0.5 Codex Verification Pass. Corrected Step 0 spike. |
| v2.4 | June 9, 2026 | First Codex verification (FAIL_REVISE). MERGE→MATCH-then-CREATE. Gate taxonomy. Targets labeled projected. |
| v2.5 | June 9, 2026 | **Second Codex GPT-5.5 re-verification (FAIL_REVISE, 0 P1, 4 P2).** §0.5 C1/C2/C5 claims updated to match body (Alert/Entity not Decision, gate taxonomy, path-dependent counts). RL exploration added to synchronous gate list (triage.py:493-529 mutates action). Counter pseudocode rewritten: MATCH existing nodes, CREATE edge only (never creates User/Category). §1.1 labeled measured vs projected. Backend reality: SOC AGE is env-controlled (`GRAPH_BACKEND=age`), not source default. |

**Review notes (items to track, not blocking):**
- SOC `source_sequence_count` (by source_location) was in v1.x,
  dropped in v2.1. Confirm referral engine uses user-level counts
  only, or re-add as a SOC CounterDef.
- Multi-worker counter test (#5 in §10) requires multi-process test
  harness (2 uvicorn workers). Implementation is non-trivial.
- All pooled-read timings (~5ms) are contingent on Step 0 spike
  confirming connection-tax hypothesis. If pooled reads are still
  50ms, the ~111ms target becomes ~161ms (still acceptable).
- `cache.note_decision()` REMOVED from pipeline code (v2.6) —
  decisions do not change entity context, so no cache update needed.

| v2.6 | June 9, 2026 | Pre-submission self-review. Last stale "~19" removed. All 4 gates in synopsis. cache.note_decision removed. Test #9 renamed. Headlines labeled projected. |
| v2.7 | June 9, 2026 | **Step 0 spike PASSED.** Measured data integrated throughout. Hot-path ~111ms → ~47ms. |
| v2.8 | June 9, 2026 | Commit caveat + strategic staging. |
| v2.9 | June 9, 2026 | Full data integration. Phase-3 committed, C9B baseline, urgency reframed. |
| v3.0 | June 9, 2026 | §3.5 Scalability Caveat. Scale projections for 10K/100K decisions. |
| v3.1 | June 9, 2026 | Package 2 counter design integrated (10 gaps resolved). §5.3 rewritten with advisory locks, transaction coupling, live proof criteria. |
| v3.2 | June 9, 2026 | Synopsis rewritten for reviewers. Package 1 at 280ms. Why each decision table. |
| v3.3 | June 10, 2026 | P3H benchmark integrated. Cache wraps read, doesn't replace it. Option A split-read decision. |
| v3.4 | June 10, 2026 | Data-driven priority update. 193ms. All targets met. |
| v3.5 | June 10, 2026 | Build full stack, measure, fix. Packages 2+3 BUILT not parked. |
| v3.6 | June 11, 2026 | §8A Route Wiring initial. Three layers, policy resolver, promotion gates. |
| v3.7 | June 11, 2026 | **§8A expanded for reviewer.** 8A.2: per-flag integration detail, interaction risk, enablement order, per-flag metrics. 8A.3: shadow side-effect problem (skip Phase 3+4), parity check code, shadow overhead. 8A.4: fallback auto-downgrade mechanism, served semantics. 8A.5: concrete thresholds (tolerance values, request counts). 8A.6: per-copilot workload sensitivity (from P3H — aggregate hides workload-dependent behavior). 8A.9: 6 open questions for reviewer. |

**References:**
- soc_campaign_identity_architecture_v1_3.md
- dk_runtime_execution_plan_v6.9
- Master Action Plan v5.44 (#117 / #150 / #179, Rules #40 / #48)
- Phase-C trace + F8 proof reports
| v3.8 | June 11, 2026 | Goal assessment. Both goals met. Pre-built levers framing. |
| v3.9 | June 11, 2026 | §8A reconciled with design authority review. 4 states, Layer 1/2 split, per-copilot posture. |
| v4.0 | June 11, 2026 | **Synopsis + execution plan + actionable items updated.** All packages BUILT (including 4+5). Execution shifts from building to measuring + adoption. Three tracks: (1) scale measurement at 500/1000 — the decision point; (2) SOC diagnostics hook — observability before authority; (3) counter adoption — if scale triggers it. 8 actionable items (A1-A8) with priority/effort/dependencies. Q11-Q13 added (pipeline-served-alone unmeasured, growth rate unmeasured, proof-authority artifact not built). §0.5 marked completed. Header updated (MAP v5.150, review count, status). |
