# Judgment-Memory Architecture
## Theory, End State, Implementation, and Migration
**Version:** 2.9 · **Date:** August 8, 2026
**Supersedes:** graph_architecture_v1.md + judgment_memory_v1.md
(this document integrates both: theory from judgment memory analysis
sessions + graph design from architecture v1)
**Integrates:** Judgment memory analysis (fourth cognitive type, April-May
2026 sessions) + Shared governed judgment-memory graph plan (coding session
scan, May 2026) + Graph architecture v1 (end state design, May 30, 2026).
**Changes v2.6 → v2.7:** 4 self-consistency fixes from coding session
review. (1) §4.1 Observation node: source→source_route, added missing
fields. (2) §4.2: added 3 Observation edges. (3) §13: added 6 Protocol
v2 test stubs. (4) Q10 idempotency keys moved from open to Phase 1.

**Changes v2.7 → v2.8:** P0-P2 Judgment History Surface shipped. All five
copilots now use AGE as the canonical runtime graph; SQLite is test-only.
Checkpoint loading is unified across legacy and V2 records, warm-start is
guarded before mutation, checkpoint IKS uses canonical centroid drift, factor
hashes are validated at startup, outcomes are idempotent across AGE, SQLite,
and Memory, and the quality axis plus centroid ablation endpoint are shipped.
SNAPSHOT_AFTER remains specified and is deferred to Program B. SOC learning
is enabled by default, and Rule #86 adds a mypy gate for every changed file.

**Changes v2.8 → v2.9:** The seven non-negotiable judgment-memory design
goals are now explicit constraints. Every production Decision path is
GraphStore→AGE, every graph access resolves through GraphConfig, AGE failure
cannot silently substitute fixtures or another store, every query and write
is domain-scoped/stamped, and all five copilots share `soc_graph` in the
`soc_copilot` database. Stale pre-cutover migration instructions, SQLite
production/default language, outdated blocker statuses, and stale test/state
claims were corrected. Program B scope now reflects what is shipped versus
what remains.

**Changes v2.5 → v2.6:** GPT-5.5 review (PASS_WITH_P2). 7 findings fixed:
(1) V locked everywhere. (2) α definition verified clean. (3) Observation
node expanded from PENDING to LOCKED with full spec. (4) GraphStore Protocol
v2 section added. (5) SOC inventory moved from Phase 5 to Phase 1.
(6) AGE failure policy expanded to operation-specific. (7) Archive semantics
clarified (active vs historical V). Authority section added.

**Changes v2.4 → v2.5:** §16 simplified: ONE document per phase.
Phase 0 = follow S2P PW v2.4 only. Phase 1+ = follow this document.
No dual-reading. Quick-reference table maps each fix to its S2P PW
section.

**Changes v2.3 → v2.4:** §16 rewritten as Coding Session Implementation
Guide. Fix ordering aligned with Phase 0 (Fix 4 first, was listed third).
Added "which document to follow" table: JM for WHAT/WHY, S2P PW for HOW.
Conflict resolution rule added (JM governs if documents conflict).

**Changes v2.2 → v2.3:** Added Phase 0 dependency chain diagram,
per-fix blast radius table, and explicit mapping of each S2P PW fix
to the JM architecture component it creates. Cross-document relationship
with S2P PW v2.4 documented (JM = architecture, S2P PW = implementation).

**Changes v2.1 → v2.2:** Three lifecycle models (not two) — S2P Model C
acknowledged. Fix 4 promoted to first Phase 0 item (gates Phase 2).
Conservation V inconsistency flagged as platform-wide (all 5 copilots).
§7 implementation map adds lifecycle model column. BLOCKER 4 status
corrected from DECIDED to DECIDED-PENDING-IMPL.

**Authority:** This document governs all graph and judgment-memory
architecture decisions. Coding sessions implement what this document
specifies. Deviations require explicit approval HERE, not in code.

## §0 — Non-Negotiable Design Goals (Constraints)

These seven goals are product architecture constraints, not aspirations,
nice-to-haves, or deferrable scope. Every design document, implementation
decision, and Codex session MUST obey them. No design document or
LLM-generated scope limit may defer a goal without explicit founder approval.

1. **Every Decision read/write** across all five copilots goes through the
   GraphStore protocol backed by AGE. No direct Neo4j, direct psycopg, or
   direct SQLite path may handle production Decision data.
2. **Every graph access path uses GraphConfig for DSN** and graph resolution.
   No raw environment-variable reads, localhost fallbacks, or hardcoded graph
   defaults are permitted in graph access code.
3. **No silent substitution.** When AGE is the declared backend, failure
   raises or is surfaced; it never returns fixtures, SQLite, or in-memory
   Decision data as a substitute.
4. **Every query is domain-scoped.** No unscoped Decision read may return
   another copilot's data.
5. **Every write stamps domain.** No Decision enters the graph without an
   explicit domain property (`domain`).
6. **One shared graph:** `soc_graph` in the `soc_copilot` database. All five
   copilots read from and write to this graph, enabling cross-copilot
   traversal.
7. **Close all non-unified paths.** Direct stores, raw graph clients, raw
   configuration resolution, unscoped queries, and unstamped writes are
   defects to eliminate, not alternate implementations.

Rules #87 and #88 make these design goals binding: Rule #87 prohibits
deferral without founder approval, and Rule #88 prohibits new Neo4j naming.

### §0.1 — Constraint Status

Goals 1-6 are fully implemented as of this authority revision. Goal 7 is
partially complete: most runtime paths are unified, while the remaining
non-unified paths are tracked as explicit defects under Program B and must be
closed without weakening Goals 1-6.

AGE is the production Decision backend. SQLite is permitted only for the
non-graph `PersistenceOutbox`, labeled temporary demo bundle restore, and
explicitly marked unit-test fixtures (`GRAPH_BACKEND=sqlite`). InMemory is
for fast unit tests only. None may silently substitute for AGE graph data.

### §0.2 — P0-P2 Shipped Inventory

The following are shipped and must be treated as current state, not planned
work: all five copilots on AGE; factory production backend is AGE; removed production SQLite
fallbacks; `demo.py` AGE + GraphConfig wiring; `AGE_USE_POOL=true` with at most
five connections per copilot; epoch-based checkpoint loading; startup factor
hash validation; pre-mutation warm-start guard; canonical checkpoint IKS;
idempotent outcomes across AGE/SQLite/Memory; V2 quality fields with legacy
`quality=null`; centroid ablation; SOC learning enabled by default; SOC V2
checkpoint writer; `/api/self/centroid-history` on all five copilots; SOC
centroid-evolution empty response; 45 store-parity tests and six fixed
divergences; DataOps custom-route deprecation with Sunset header and migrated
frontend; removed Neo4j config fields and deleted `db/neo4j.py`; Rule #86 in
all five CLAUDE.md files; SOC outcome-route idempotency; and SOC PW 407/420.

Additionally shipped on August 8, 2026: SOC atomic outcome/checkpoint
transaction using AGE `run_transaction` (rollback-safe); DataOps custom
centroid-history route deleted after zero-caller gate (shared route is the
sole path); B5 `SNAPSHOT_AFTER` traversal API with backfill (808 checkpoints
scanned, 579 edges confirmed, lineage endpoint live on all 5 copilots);
cross-copilot semantic transfer (`TransferPattern` nodes in AGE, shape-safe
factor/category insight mapping, SOC→Trading demo beat, conservation-gated,
endpoints on Trading/Purchasing/DataOps); S2P evolver conservation fix
(literal `GREEN` replaced with live scorer-backed provider, fail-closed on
unknown); Purchasing and DataOps `PromptVariantEvolver` instantiation (6+6
and 2+2 variants registered, live conservation providers, evolution summary
endpoints); S2P score path instrumented with per-step `[S2P-PERF]` timing;
SOC ServiceNow 4 failures fixed (unclassified alerts skip learning); RL
diagnostic scan completed (consolidated results with path:line evidence
across all repos); SOC G1 boundary decision memo produced (Option A strict,
exploration becomes proposal/shadow only); SOC PW 407/420 confirmed stable.

### Locked Decisions (do not reopen)

| Decision | Status | Authority |
|---|---|---|
| V = verified decisions only | **LOCKED** | §6, standing rule #37 |
| α = category coverage among verified decisions | **LOCKED** | §6, standing rule #12 |
| Observation nodes for preview/read | **LOCKED** | §5, §9 BLOCKER 4 |
| SQLite = local/test adapter only | **LOCKED** | §3, §12 |
| AGE = canonical product graph | **LOCKED** | §3 |
| Decision lifecycle: pending→confirmed/overridden | **LOCKED** | §5 |
| expired = reserved future, not in scope | **LOCKED** | §5 |
| Fix ordering: Fix 4→Fix 1→Fix 3a→3b→3c | **LOCKED** | §10 Phase 0 |
| **L-8.1: All 5 copilots on AGE; SQLite is test-only; no silent fallback** | **SHIPPED** | §7, v2.8 store parity |
| **L-8.2: Select newest checkpoint by numeric `created_at_epoch` across legacy + V2** | **SHIPPED** | §4.1, §7 |
| **L-8.3: Warm-start guard covers the entire method before centroid mutation** | **SHIPPED** | §10, warm-start invariant |
| **L-8.4: Checkpoint IKS is canonical centroid drift; prior composite is metadata** | **SHIPPED** | §4.1, §6 |
| **L-8.5: Validate `factor_names_hash` at startup; legacy missing hash remains compatible** | **SHIPPED** | §4.1, §10 |
| **L-8.6: `write_outcome` is idempotent across AGE, SQLite, and Memory** | **SHIPPED** | §12a, store parity |
| **L-8.7: V2 checkpoints carry quality fields; legacy checkpoints expose `quality=null`** | **SHIPPED** | Quality axis |
| **L-8.8: Centroid ablation endpoint is contract-bound and holds DK weights/temperature fixed** | **SHIPPED** | Centroid ablation |
| **L-8.9: SOC learning is enabled by default; env false still overrides** | **SHIPPED** | Platform state |
| **L-8.10: `SNAPSHOT_AFTER` is deferred to Program B, not removed** | **DECIDED** | §1.3, §4.2, Program B |
| **L-8.11: Every Codex session runs mypy on all changed files before success** | **SHIPPED** | Standing rule #86 |

**Do NOT:**
- Redefine α as penalty ratio or conservation coefficient
- Treat V as an open question
- Mix penalty_ratio into α/q/V semantics
- Create Decision nodes from GET preview/read endpoints

---

# PART I — THEORY: WHY THE SHARED GRAPH

---

## §1 — Judgment Memory as the Fourth Cognitive Type

The Compounding Intelligence platform implements four types of memory.
This taxonomy was established through cross-session analysis and is the
theoretical foundation for every architectural decision in this document.

### 1.1 The Four Memory Types

| Type | What it stores | How it's created | How it compounds |
|---|---|---|---|
| **Episodic** | Specific events: decisions made, outcomes observed, overrides recorded, verifications logged | Score + learn cycle: each decision-outcome pair is one episode | Each episode refines centroid geometry. 10,000 episodes create unreproducible judgment. |
| **Semantic** | Domain entities and context relationships: alerts, invoices, suppliers, trades, pipelines, controls | Connected from source systems (SAP, Celonis, Toast POS, SIEM) + enriched from graph traversal | Entity relationships enable cross-system discovery. "Supplier Aster invoices 3.1× slower" requires supplier → invoice → process edges. |
| **Procedural** | Learned rules, AgentEvolver variants, operational procedures, promoted/rejected automations | AgentEvolver proposes → shadow tests → conservation gates → promotes or rejects | Rules transfer across copilots. SOC 68% → S2P 69% → DataOps 83%. Procedural memory compounds across domains. |
| **Judgment** | Centroid geometry, DiagonalKernel factor weights, noise fingerprints, IKS scores, conservation state, transfer patterns | Computed from episodic memory via CompoundingScorer. Updated on every verified decision. | The moat. 315 learned values per copilot. Centroid geometry IS accumulated organizational judgment. Cannot be synthesized, cannot be forked. |

### 1.2 Why These Are "Memory" and Not "Data"

Data is stored and queried. Memory COMPOUNDS — each new piece changes the
meaning and weight of everything that came before. The distinction matters:

- **Data:** "Invoice INV-4521 was $1,234.56." Static. Same value forever.
- **Memory:** "Invoice INV-4521's resolution CHANGED the centroid for
  'produce' category by +0.08 on supplier_lead_time, which CHANGED the
  scoring of all future produce invoices from this supplier, which CHANGED
  the conservation status from AMBER to GREEN." Dynamic. One episode
  cascades through the entire judgment system.

The cascade is the compound interest of intelligence. It cannot happen
in a flat database. It requires a GRAPH — where the cascade is a traversal.

### 1.3 Why All Four Types Must Be in ONE Substrate

Each memory type is valuable alone. The product differentiation comes from
their INTERACTION — which is only possible through graph traversal:

**Episodic × Judgment:** "This decision moved the centroid. Show me the
before and after." → Requires `(Decision)-[:SNAPSHOT_AFTER]->(CentroidCheckpoint)`.

**Procedural × Judgment:** "This rule was rejected because the centroid
it would have moved was already at ε_firm★." → Requires
`(Decision)-[:TRIGGERED_EVOLUTION]->(EvolutionEvent)` plus
`(Decision)-[:SNAPSHOT_AFTER]->(CentroidCheckpoint)` — traverse from the
Decision that triggered the evolution to the centroid it would affect.

**Episodic × Semantic:** "This decision was about Invoice INV-4521 from
Supplier Aster in the 'produce' category." → Requires
`(Decision)-[:ABOUT]->(DomainContext {entity_type: 'invoice'})`.

**Semantic × Semantic (cross-system):** "SAP schema change → Celonis process
slowdown → S2P invoice exceptions." → Requires edges between DomainContext
nodes across systems. The $604K finding.

**Judgment × Judgment (cross-copilot):** "SOC's pattern for 'recurrence'
transferred to DataOps with warm_start 0.757." → Requires
`(tp:TransferPattern)-[:FROM_DOMAIN]->(d1:Domain {name:'soc'}),
(tp)-[:TO_DOMAIN]->(d2:Domain {name:'dataops'})` — both edges originate
from TransferPattern, not a chain through Domain.

**Before the v2.8 AGE cutover, separate stores made these interactions
impossible.** That historical failure mode is retained as rationale. The
current architecture uses one shared AGE graph; API stitching remains
prohibited because it is not a governed graph traversal and cannot support
the "one traversal, one answer" claim.

---

## §2 — Claims the Current Implementation Cannot Support

| Claim (in outreach) | What it requires | Current reality | Gap type |
|---|---|---|---|
| "One engine, one graph" | Shared graph substrate | All 5 copilots on one AGE graph; SQLite is test-only | **RESOLVED P0-P2** |
| "Cross-graph attention" | Traversal across systems | AGE substrate is shared; governed traversal remains a Program B proof item | **IN PROGRESS** |
| "$604K cross-graph finding" | SAP × Celonis × operations traversal | Fixture data, not live query | **DEMO** |
| "Pattern transfer SOC→S2P→DataOps" | Transfer edges in shared graph | Shared AGE substrate is wired; traversal proof remains Program B | **IN PROGRESS** |
| "315 values that compound" | Values in shared graph geometry | Runtime judgment is on AGE; checkpoint quality/IKS semantics are shipped | **RESOLVED P0-P2** |
| "You can't fork judgment" | Judgment in unforkable graph | Runtime judgment is on canonical AGE; SQLite is test-only | **RESOLVED P0-P2** |
| "One traversal. One answer." | Cross-system query in one operation | Shared substrate is live; governed cross-copilot traversal remains Program B | **IN PROGRESS** |
| Conservation across copilots | Shared decision population | All five copilots share AGE; conservation remains domain-scoped and verified-only | **RESOLVED SUBSTRATE** |

The former store-divergence structural gap is resolved: all five copilots now
run on the canonical AGE graph. Remaining cross-copilot proof work is tracked
in Program B and cannot be substituted by fixture data, API endpoints, or UI
badges.

---

# PART II — END STATE DESIGN: WHAT WE'RE BUILDING

---

## §3 — Architecture Target (Non-Negotiable)

### 3.1 The End State

The production AGE graph is named `soc_graph` in the `soc_copilot` database.
All five copilot domains are partitions in that one graph; there are no
per-copilot production graphs.

```
┌─────────────────────────────────────────────────────────┐
│            Apache AGE / PostgreSQL                       │
│                                                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐         │
│  │  SOC   │ │  S2P   │ │Trading │ │Purchasing│         │
│  │ domain │ │ domain │ │ domain │ │  domain  │         │
│  └───┬────┘ └───┬────┘ └───┬────┘ └────┬─────┘         │
│      │          │          │            │                │
│  ┌───┴──────────┴──────────┴────────────┴────────────┐  │
│  │         Shared graph substrate                     │  │
│  │  TransferPattern · ConservationStatus ·            │  │
│  │  EvidenceReceipt · cross-domain traversal          │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────┐                                            │
│  │ DataOps  │                                            │
│  │ domain   │                                            │
│  └──────────┘                                            │
└─────────────────────────────────────────────────────────┘

        │ GraphStore protocol
        │ (identical semantics)
┌───────┴────────────────────────────────┐
│  SQLite adapter (unit-test ONLY)       │
│  Same protocol. Same lifecycle.        │
│  NOT the product graph. Ever.          │
└────────────────────────────────────────┘
```

### 3.2 Seven Non-Negotiable Properties

1. **ONE physical graph** for all copilots in production and demo.
   Apache AGE on PostgreSQL. Domain-partitioned by `domain` property
   on every node.

2. **SQLite is a UNIT-TEST ADAPTER ONLY.** Production Decision data never
   uses SQLite. PersistenceOutbox and labeled temporary bundle restore are
   non-graph exceptions; neither is a graph substitute.

3. **Both adapters implement the same GraphStore protocol.** Identical
   semantics, identical lifecycle, identical conservation counting,
   identical test assertions. Conformance tests enforce this.

4. **Cross-copilot queries are GRAPH TRAVERSALS, not API stitching.**
   "Show me all S2P decisions that used a rule transferred from SOC"
   resolves as one Cypher query on one graph.

5. **Conservation operates on the shared graph.** V, q, α are computed
   from graph aggregates. ConservationStatus is a persisted snapshot.

6. **The audit chain is a graph traversal.** Decision → Outcome →
   EvidenceReceipt → CentroidCheckpoint is traversable from any node.

7. **Graph access is configured and unified.** Every graph path resolves its
   DSN and graph name through GraphConfig. Production uses the shared
   `soc_graph` graph in the `soc_copilot` database.

### 3.3 GraphConfig Resolution Contract

`GraphConfig` is the sole authority for AGE DSN, database, graph name,
pooling, and backend selection. Copilot entrypoints receive or construct one
validated GraphConfig through the platform configuration layer; graph clients
do not read raw environment variables and do not invent localhost or empty
DSN defaults. The production configuration is AGE + `soc_graph` on the
`soc_copilot` database with `AGE_USE_POOL=true` and a maximum of five
connections per copilot.

---

## §4 — Canonical Graph Model

### 4.1 Node Labels and Required Properties

Every node MUST have: `domain` (partition key), `created_at` (ISO 8601).
Every node SHOULD have: `schema_version` (integer).

**Episodic memory:**

```
(:Decision {
  decision_id, domain, category, category_index,
  recommended_action, recommended_index, confidence,
  status,             -- 'pending' | 'confirmed' | 'overridden'
  source,             -- 'score' | 'preseed' | 'bundle'
  scorer_version, preset_version, factor_schema_version,
  created_at, metadata
})

(:Outcome {
  outcome_id, decision_id, actual_action, actual_index,
  is_correct,          -- INTEGER: 1=confirmed, 0=overridden
  reward, verified_at, verifier, override_reason, metadata
})

(:FactorVector {
  vector_id, decision_id, dimension, factor_names,
  factor_values, factor_names_hash, shape,
  schema_version, created_at
})

(:Observation {
  observation_id, domain, category, recommended_action,
  confidence,
  source_route,        -- 'preview' | 'what-if' | 'simulation' | 'batch-score'
  factor_schema_version, scorer_version,
  created_at, metadata
})
-- Observations are NOT Decisions. They do NOT count toward
-- conservation V. They exist for debugging and analytics only.
```

**Semantic memory:**

```
(:Domain {
  domain_id, name, copilot, tensor_shape, penalty_ratio,
  environment, owner, schema_version, created_at
})

(:DomainContext {
  entity_id, domain, entity_type, natural_key,
  attributes, created_at, updated_at
})
-- entity_type: 'alert', 'invoice', 'supplier', 'trade',
-- 'purchase_order', 'pipeline', 'dataset', 'incident',
-- 'control', 'process_activity'
```

**Procedural memory:**

```
(:EvolutionEvent {
  event_id, domain, event_type, rule_name, variant_id,
  status,             -- 'proposed' | 'shadow' | 'promoted' | 'rejected' | 'rolled_back'
  source_copilot, source_rule,
  metric, shadow_batch_size, min_shadow_batches,
  created_at, metadata
})

(:Rule {
  rule_id, domain, rule_family, parameters,
  status,             -- 'active' | 'shadow' | 'retired'
  owner, policy_version, created_at, metadata
})

(:TransferPattern {
  pattern_id, source_domain, target_domain,
  source_rule, target_rule, factor_mapping,
  confidence, validation_status, conservation_status,
  created_at, metadata
})
```

**Audit memory:**

```
(:EvidenceReceipt {
  receipt_id, domain, payload_hash, previous_hash,
  chain_index, actor, source_route, created_at, metadata
})
-- Hash chain: each receipt's previous_hash points to the prior
-- receipt's payload_hash. Chain integrity is verifiable by
-- traversing receipts in chain_index order and checking hashes.
-- This is the tamper-evident audit trail for regulators.
```

**Judgment memory:**

```
(:CentroidCheckpoint {
  checkpoint_id, domain, category, action,
  centroids,          -- serialized centroid state
  decisions_count, verified_count, iks,
  shape, factor_names_hash, created_at, created_at_epoch, metadata,
  quality_window_size, quality_verified_count, quality_correct_count,
  rolling_accuracy, quality_policy_version
})

(:Fingerprint {
  fingerprint_id, domain, factor_names, factor_stats,
  skipped_incompatible, window, created_at, metadata
})

(:ConservationStatus {
  status_id, domain,
  V,                  -- verified decision count (rule #37)
  q, alpha, theta_min,
  verified_count, correct_count,
  status,             -- 'GREEN' | 'AMBER' | 'RED'
  counts_scope,       -- 'verified_only' (locked)
  policy_version, computed_at
})
```

**Checkpoint compatibility and quality axis (v2.9):** Loaders select the
newest checkpoint by numeric `created_at_epoch` across legacy and V2 records;
ISO timestamps are normalized on read. A missing `factor_names_hash` is
legacy-compatible, while a mismatched hash causes bootstrap fallback. V2
checkpoints may carry rolling quality fields; legacy checkpoints expose
`quality = null`. Quality is never fabricated. The canonical checkpoint IKS is
`100 * min(mean_drift / 0.20, 1.0)`; any prior composite value is retained only
as `metadata["composite_iks"]`.

### 4.2 Edge Labels (Canonical — No Aliases)

```
-- Observation edges (preview/read — excluded from conservation)
(Observation)-[:IN_DOMAIN]->(Domain)
(Observation)-[:ABOUT]->(DomainContext)
(Observation)-[:HAS_FACTOR_VECTOR]->(FactorVector)

-- Episodic edges
(Decision)-[:IN_DOMAIN]->(Domain)
(Decision)-[:ABOUT]->(DomainContext)
(Decision)-[:HAS_FACTOR_VECTOR]->(FactorVector)
(Decision)-[:HAS_OUTCOME]->(Outcome)
(Decision)-[:EMITTED_RECEIPT]->(EvidenceReceipt)
(Decision)-[:SNAPSHOT_AFTER]->(CentroidCheckpoint)
(Decision)-[:USED_RULE]->(Rule)
(Decision)-[:TRIGGERED_EVOLUTION]->(EvolutionEvent)

-- Procedural edges
(EvolutionEvent)-[:PROMOTED_RULE]->(Rule)
(EvolutionEvent)-[:ROLLED_BACK_RULE]->(Rule)
(Rule)-[:APPLIES_TO]->(DomainContext)

-- Judgment edges
(CentroidCheckpoint)-[:DERIVED_FROM]->(Decision)
(Fingerprint)-[:SUMMARIZES_DOMAIN]->(Domain)
(ConservationStatus)-[:SUMMARIZES_DOMAIN]->(Domain)

-- Transfer edges (cross-copilot — the reason for shared graph)
(TransferPattern)-[:FROM_DOMAIN]->(Domain)
(TransferPattern)-[:TO_DOMAIN]->(Domain)
(TransferPattern)-[:DERIVED_FROM]->(EvolutionEvent)
```

### 4.3 Domain Partitioning Rule

Every node has a `domain` property. ALL queries MUST include
`WHERE domain = $d` unless explicitly performing cross-domain
traversal. This prevents accidental cross-domain contamination.

Cross-domain queries are legitimate graph operations — they are
the REASON for the shared graph. But they must be explicit, governed,
and audited.

**Write invariant:** Every GraphStore write requires an explicit non-empty
`domain` and stamps that value on the node before persistence. A Decision
write without `domain` is rejected. No copilot may bypass GraphStore to write
Decision data directly.

---

## §5 — Decision Lifecycle (Locked)

```
                    ┌──────────┐
  POST /api/score → │ pending  │ (+ FactorVector, EvidenceReceipt)
                    └────┬─────┘
                         │
              POST /api/learn
              (analyst confirms or overrides)
                         │
                    ┌────┴─────┐
                    │          │
              ┌─────┴───┐ ┌───┴──────┐
              │confirmed│ │overridden│
              └─────────┘ └──────────┘

  'expired' — reserved future state. NOT in current scope.
  Do not implement expiry until retention policy is defined.
```

**Mapping from outcomes table:**
- `is_correct = 1` → `status = 'confirmed'`
- `is_correct = 0` → `status = 'overridden'`
- `is_correct IS NULL` → remains `'pending'` (defensive)

**Score-time writes:** `POST /api/score` creates Decision(pending) +
FactorVector + EvidenceReceipt. This preserves audit trail and
AgentEvolver flywheel (TRIGGERED_EVOLUTION edges reference Decisions).

**Preview/read writes:** `GET` preview endpoints create Observation
nodes, NOT Decision nodes. Observations are excluded from conservation
V and from the AgentEvolver flywheel. This prevents the contamination
that caused S2P's 23,607 ghost decisions.

---

## §6 — Conservation on the Shared Graph (Locked)

### Standing Rule #37

**V in the conservation formula = count of verified decisions
(status IN 'confirmed', 'overridden'). Applies to ALL copilots,
both SQLite and AGE backends. Pending, preseed, bundle, preview,
and test scores do NOT count toward V.**

### Mathematical Justification

Conservation law: α·q·V ≥ θ_min. Protects human oversight quality.
All three variables must describe the SAME population:

- **α** = category coverage among verified decisions (rule #12)
- **q** = rolling accuracy over 400 verified decisions (q_window=400)
- **V** = volume of verified decisions (rule #37)

The theorem's proof (4 paths, 295 experiments, 3 reviewers) assumes
consistent population. Mixing verified and unverified breaks the proof.

### Conservation Query (AGE Cypher)

```cypher
-- Single-pass aggregation (AGE Cypher dialect)
-- Note: Apache AGE supports a subset of openCypher. Test CASE/sum
-- support against your AGE version. Fallback: multiple COUNT queries.
MATCH (d:Decision {domain: $domain})-[:HAS_OUTCOME]->(o:Outcome)
WHERE d.status IN ['confirmed', 'overridden']
RETURN
  count(d) AS V,
  count(CASE WHEN o.is_correct = 1 THEN 1 END) AS correct_count,
  count(DISTINCT d.category) AS categories_with_data
-- V = verified_count (by definition: all counted decisions have outcomes)
-- q = correct_count / V
-- α = categories_with_data / C (domain tensor C dimension)
-- θ_min = 23.53 / (α × V)
-- signal = α × q × V
```

Result persisted as `(:ConservationStatus)` with `counts_scope='verified_only'`.

### Conservation Query (SQLite — must produce identical results)

```python
def count_verified_decisions(self, domain: str) -> int:
    with self._lock:
        return self._conn.execute(
            "SELECT COUNT(*) FROM decisions WHERE domain = ? "
            "AND status IN ('confirmed', 'overridden')",
            (domain,)
        ).fetchone()[0]
```

Conformance tests verify both backends produce identical counts
for identical data.

### Archive Semantics (Locked)

- **Active verified decisions** count toward conservation V by default.
- **Archived verified decisions** (moved to decisions_archive) do NOT
  count toward active V unless explicitly included by time-window query
  for historical replay/analysis.
- **Archived pending decisions** are audit/replay material only. They
  never counted toward V (they were pending) and archiving doesn't
  change that.
- **Archive must not delete auditability.** Archived rows remain
  queryable for compliance, debugging, and forensic analysis. Archive
  is a lifecycle transition, not deletion.
- **Historical V windows:** A policy may allow querying "what was V at
  time T?" by including archived verified decisions within a time range.
  This is an analytics query, not a conservation input — active
  conservation always uses current active verified count.

### v2.9 Math Invariant Status

Nine invariant gaps were identified in the P0-P2 review; two are addressed
in v2.9:

| Invariant | Status |
|---|---|
| Rolling accuracy q from 400 verified decisions | **ADDRESSED** — quality fields are persisted on V2 checkpoints |
| Factor-version drift resets incompatible learned state | **ADDRESSED** — `factor_names_hash` is validated at startup |
| Convergence, DK shrinkage, novelty, composition, holdout, re-convergence, auto-pause | **DEFERRED** — GAE conformance track / Program B |

The Conservation-V store-divergence root is resolved: all five runtime
copilots use AGE, with domain-scoped verified-only predicates. The formula
`α·q·V ≥ θ_min` and its population semantics remain unchanged.

---

# PART III — CURRENT STATE: WHERE WE ARE

---

## §7 — Current Implementation Map

### Per-Copilot Store Architecture (as scanned)

| Copilot | Physical backend | Lifecycle model | demo.py contract | CI_DATA_DIR |
|---|---|---|---|---|
| **SOC** | Apache AGE/PostgreSQL | **Model A** (AGE-owned) | `persistent: False` — canonical | N/A |
| **Trading** | Apache AGE/PostgreSQL | **Model A** (AGE-owned) | `persistent: False` — canonical | N/A |
| **Purchasing** | Apache AGE/PostgreSQL | **Model A** (AGE-owned) | `persistent: False` — canonical | N/A |
| **DataOps** | Apache AGE/PostgreSQL | **Model A** (AGE-owned) | `persistent: False` — canonical | N/A |
| **S2P** | Apache AGE/PostgreSQL | **Model A** (AGE-owned) | `persistent: False` — canonical | N/A |

### The Three Lifecycle Models

The platform previously had THREE data lifecycle models, not two. v2.9
resolves that divergence: the runtime platform now uses Model A for all five
copilots, while Model B remains the explicitly local/test adapter and Model C
is retired.

**Model A — AGE (all five copilots):** PostgreSQL/AGE owns the data.
demo.py doesn't manage it (`persistent: False`). Canonical.

**Model B — local/test SQLite:** The adapter remains available for unit tests,
integration tests, deterministic fixtures, and offline development. It is not
the product graph and has no silent runtime fallback.

**Model C — hardcoded SQLite (retired):** The former S2P hardcoded SQLite
path is retired by the v2.8 factory/runtime cutover; no copilot silently falls
back to SQLite when AGE is unavailable.
<!-- Historical Model C details retained below for audit context. -->
<!-- **Model C — Hardcoded SQLite (S2P):** S2P hardcodes its DB path in
`main.py` (`Path(__file__).parent / "data"`). Ignores `CI_DATA_DIR`.
demo.py sets `CI_DATA_DIR` → backend ignores it → demo.py owns nothing.
`demo.py --reset s2p` wipes a path that doesn't exist → silent no-op.
`demo.py --status` reads a path that doesn't exist → "no data."
The `persistent: True` flag is a lie. -->

**v2.9 records the closed store divergence root.** All five copilots now use AGE and
the factory raises when AGE is missing. SQLite remains a test-only adapter.

### Per-Copilot Store Detail

| Copilot | Decision store | Outcome store | Evidence/audit | Evolution | Centroid/judgment |
|---|---|---|---|---|---|
| **SOC** | AGE graph client | AGE sync | AGE bootstrapped | AGE nodes/edges | AGE snapshots |
| **Trading** | AGE graph client | AGE | AGE receipts | AGE nodes/edges | AGE checkpoints |
| **Purchasing** | AGE graph client | AGE | AGE receipts | AGE nodes/edges | AGE checkpoints |
| **DataOps** | AGE graph client | AGE | AGE receipts | AGE nodes/edges | AGE checkpoints |
| **S2P** | AGE graph client | AGE | AGE receipts | AGE nodes/edges | AGE checkpoints |

### Shared SDK and CI Platform Pieces (Already Built)

| Component | Location | Status |
|---|---|---|
| `GraphStore` protocol | copilot-sdk | ✅ Works — defines write_decision, write_outcome, count, centroid, evolution, entity_link, archive, close |
| `SQLiteGraphStore` | copilot-sdk | ✅ Works — tables for decisions, outcomes, checkpoints, evolution, RL, entity edges, archive |
| `AGEGraphStoreAdapter` | ci-platform | ✅ Runtime adapter for all 5 copilots — decision/outcome writes, counts, checkpoints, evolution, entity links, archive, close |
| SOC on AGE | soc-copilot | ✅ Proven — SOC runs on AGE in demo (BE test count at time of scan) |
| DataOps AGE DSN | copilot-sdk demo.py | ✅ Runtime AGE wiring shipped |

### Platform State After v2.9

| Copilot | Backend | Learning | SOC PW | Centroid History | Quality | Ablation | Evolver | Transfer |
|---|---|---|---|---|---|---|---|---|
| SOC | AGE ✅ | Enabled ✅ | 407/420 | 200 ✅ | null (legacy) | no_id (legacy) | ✅ SDK wrapper | ✅ Source |
| S2P | AGE ✅ | Frozen | — | 200 ✅ | null (legacy) | no_id (legacy) | ✅ SDK (conservation live) | — |
| Trading | AGE ✅ | Enabled | — | 200 ✅ | null→present | ✅ centroid_ablation | ✅ Custom | ✅ Target |
| Purchasing | AGE ✅ | Enabled | — | 200 ✅ | null→present | ✅ centroid_ablation | ✅ SDK (6+6 variants) | ✅ Target |
| DataOps | AGE ✅ | Enabled | — | 200 ✅ | null→present | ✅ centroid_ablation | ✅ SDK (2+2 variants) | ✅ Target |

SOC PW verification: 407/420 passed, with 1 timing flake and 12 skipped.

The `null` quality values are valid legacy behavior, not fabricated defaults.
V2 checkpoints may expose quality fields when verified-window data exists.

### What's Missing / Deferred

1. **GraphStore factory** — shipped for the AGE runtime cutover; continued conformance hardening remains.
2. **AGEGraphStoreAdapter conformance** — 45 parity tests shipped; broader GAE conformance remains.
3. **Canonical vocabulary enforcement** — inventory and compatibility work remain for later migration proof.
4. **ConservationStatus as graph node** — persistence semantics remain governed by §12a.
5. **Observation nodes** — semantics are locked; full reader/writer traversal remains implementation work.
6. **Cross-copilot traversal queries** — shared AGE substrate is live; proof and traversal API are Program B.
7. **Decision lifecycle (status column)** — locked and implemented in the adapters; continue regression coverage.

---

## §8 — Gap Analysis

### Memory type gaps

| Memory type | SOC (AGE) | S2P (AGE) | Trading (AGE) | Purchasing (AGE) | DataOps (AGE) |
|---|---|---|---|---|---|
| Episodic: decisions | ✅ In AGE | ✅ In AGE | ✅ In AGE | ✅ In AGE | ✅ In AGE |
| Episodic: outcomes | ✅ In AGE | ✅ In AGE | ✅ In AGE | ✅ In AGE | ✅ In AGE |
| Semantic: entities | ✅ In AGE | ✅ In AGE substrate | ✅ In AGE substrate | ✅ In AGE substrate | ✅ In AGE substrate |
| Procedural: evolution | ✅ In AGE | ✅ In AGE | ✅ In AGE | ✅ In AGE | ✅ In AGE |
| Judgment: centroids | ✅ In AGE | ✅ In AGE | ✅ In AGE | ✅ In AGE | ✅ In AGE |
| Cross-copilot transfer | ⚠️ Shared AGE; Program B proof | ⚠️ Shared AGE; Program B proof | ⚠️ Shared AGE; Program B proof | ⚠️ Shared AGE; Program B proof | ⚠️ Shared AGE; Program B proof |
| Conservation lifecycle | ✅ AGE status predicates | ✅ AGE status predicates | ✅ AGE status predicates | ✅ AGE status predicates | ✅ AGE status predicates |

**Legend:** ✅ In canonical location. ⚠️ Works but in wrong substrate. ❌ Missing or broken.

---

# PART IV — MIGRATION: HOW WE GET THERE

---

## §9 — Architectural Blockers

### BLOCKER 1: AGEGraphStoreAdapter conformance

**Status:** SHIPPED for the runtime path; 45 AGE/SQLite/Memory parity tests
are passing. Remaining GAE-track hardening is Program B work.
**Must do:** Run same protocol tests against SQLite and AGE. Every
assertion must pass on both.
**Decision:** None needed — this is work, not a choice.
**Risk if skipped:** Every migration builds on unverified foundation.

### BLOCKER 2: SOC AGE schema vs canonical vocabulary

**Status:** UNKNOWN — SOC labels not inventoried against canonical.
**Must do:** Scan SOC AGE labels. Map to canonical.
**Decision:** Compatibility views (SOC keeps working, canonical labels
exist for cross-copilot queries).

### BLOCKER 3: Conservation V definition

**Status:** SHIPPED — V = verified only (standing rule #37) across all five
copilots and all adapters.

### BLOCKER 4: Preview/read write contamination

**Status:** LOCKED and implemented in the governed adapter paths; remaining
reader/traversal proof is tracked under Program B.

**Rule:** GET preview/read endpoints MUST NOT create Decision nodes.
If preview/read activity needs persistence (for audit or debugging),
it creates Observation nodes. If no persistence needed, read is
non-persistent (pure computation, no graph write).

**Observation semantics (locked):**
- Excluded from conservation V (not verified, no Outcome)
- Excluded from AgentEvolver / TRIGGERED_EVOLUTION flywheel
- Excluded from Decision lifecycle (no pending→confirmed transition)
- MAY link to DomainContext and FactorVector for debugging
- MAY be promoted to Decision through an explicit command endpoint
  (not automatic — requires human or system action)

**Observation node spec (canonical):**
```
(:Observation {
  observation_id, domain, category,
  recommended_action, confidence,
  factor_schema_version, scorer_version,
  source_route,        -- 'preview' | 'what-if' | 'simulation' | 'batch-score'
  created_at, metadata
})
```

**Observation edges:**
```
(Observation)-[:IN_DOMAIN]->(Domain)
(Observation)-[:ABOUT]->(DomainContext)
(Observation)-[:HAS_FACTOR_VECTOR]->(FactorVector)
```

**SQLite adapter:** `observations` table mirroring node properties.
**AGE adapter:** `(:Observation)` label with same properties.
**Both adapters must implement `write_observation()` in Protocol v2.**

### BLOCKER 5: demo.py reset for AGE

**Status:** OPEN.
**Decision:** Domain-scoped reset (preserve other copilots' state).

### BLOCKER 6: Demo bundle format

**Status:** OPEN.
**Decision:** Protocol-based JSON restore through GraphStore, not
SQLite file copy. Bundles enter as `status='pending'`.

---

## §10 — Migration Phases

### Phase 0: Foundation (SHIPPED — S2P PW Fixes)

**Duration:** 1 week. **Prerequisite:** None.
**Historical implementation spec:** S2P Playwright Failures v2.4 (separate
document). This section records what Phase 0 did and why. Phase 0 and the
P0-P2 AGE cutover are shipped; this document is the current implementation
authority for all subsequent work.

### Phase 0 Dependency Chain (historical execution order — complete)

```
Fix 4: CI_DATA_DIR ──→ Fix 1: count_decisions() ──→ Fix 3a: status column
  │                      │                            │
  │ S2P only.            │ copilot-sdk + s2p.         │ copilot-sdk.
  │ 1 line.              │ 2 files.                   │ ALL 5 copilots.
  │ Closes Model C.      │ O(1) performance.          │ _ensure_schema_v2()
  │                      │ Same V value.              │ Decision lifecycle.
  ▼                      ▼                            ▼
  Gates Fix 3c           Gates nothing               Fix 3b: conservation V
  (archive path)         (independent perf)            │
  Gates Phase 2                                        │ copilot-sdk + s2p.
  (factory needs                                       │ ALL 5 copilots.
   CI_DATA_DIR)                                        │ V = verified only.
                                                       ▼
                                                     Fix 3c: S2P archive
                                                       │
                                                       │ s2p only.
                                                       │ Archives 23,607 rows.
                                                       │ Needs correct path
                                                       │ (Fix 4) + status
                                                       │ column (Fix 3a).
                                                       ▼
                                                     Phase 0 COMPLETE
                                                       │
                                                     Phase 1 begins
```

### What Each Fix Creates for the Architecture

| Fix | What it does (implementation) | What it creates (architecture) | JM section |
|---|---|---|---|
| Fix 4 | S2P reads CI_DATA_DIR env var | Closed the historical Model C path; factory now resolves AGE through GraphConfig | §7 lifecycle models |
| Fix 1 | count_decisions() replaces len(get_all_decisions()) | O(1) audit count method — survives alongside count_verified_decisions() | §6 conservation |
| Fix 3a | Adds `status` column + `_ensure_schema_v2()` | **Is the Decision lifecycle** from §5; semantics now enforced through GraphStore and AGE | §5 lifecycle |
| Fix 3b | conservation uses count_verified_decisions() | **Is standing rule #37** (V=verified) across all five copilots | §6 conservation |
| Fix 3c | Archives unverified S2P rows to decisions_archive | Historical cleanup completed before AGE cutover; archive remains non-graph retention material | §10 Phase 3 |

### Phase 0 Blast Radius

| Fix | Repos | Copilots affected | Tests at risk | Risk |
|---|---|---|---|---|
| Fix 4 | s2p only | S2P only | S2P BE only | **MINIMAL** — 1 line, no semantic change |
| Fix 1 | copilot-sdk + s2p | S2P directly, others inherit | Conservation tests | **LOW** — algorithm only, same value |
| Fix 3a | copilot-sdk | **ALL 5** — schema migration in constructor | All BE suites (~5,484 tests) | **MEDIUM** — one bug breaks 5 copilots |
| Fix 3b | copilot-sdk + s2p | **ALL 5** — V definition changes | Conservation tests | **MEDIUM** — may flip RED→GREEN |
| Fix 3c | s2p only | S2P only | S2P conservation | **LOW** — moves rows, no logic change |

**Historical risk note:** Fix 3a was highest-risk because schema migration
ran in the SQLite adapter constructor used by all SDK copilots. That risk was
covered by the shipped parity suite; production Decision data is now AGE-only.

### Phase 0 Items (Ordered — all shipped)

| Order | Item | Repo | What | Status |
|---|---|---|---|---|
| **1st** | Fix 4: CI_DATA_DIR | s2p | Historical lifecycle alignment; production now uses AGE | **SHIPPED** |
| 2nd | Fix 1: count_decisions() | copilot-sdk + s2p | O(1) counting (performance) | **SHIPPED** |
| 3rd | Fix 3a: status column | copilot-sdk | `_ensure_schema_v2()`, `count_verified_decisions()` | **SHIPPED** |
| 4th | Fix 3b: conservation V | copilot-sdk + s2p | Verified-only counting | **SHIPPED** |
| 5th | Fix 3c: S2P archive | s2p | Archive ghost decisions | **SHIPPED** |
| 6th | Standing rule #37 | Docs | V = verified | **SHIPPED** |

**Historical rationale for Fix 4:** Fix 3c archived decisions from S2P's
then-managed database. Fix 4 removed the historical hardcoded path before the
AGE cutover. Production now resolves the shared graph through GraphConfig;
no copilot uses the old Model B production path.

**Conservation V is platform-wide, not S2P-only:** All five copilots now use
verified-only predicates through GraphStore on AGE. The former pending-row
and ghost-decision population was the trigger for the shipped Fix 3a/3b work.

**Gate result:** Status and conservation semantics are correct across all five
copilots; the S2P gate passed, and the AGE cutover is shipped.

**v2.9 status:** P0-P2 implementation work moved the runtime platform
past the SQLite migration plan: all five copilots are now AGE-backed, the
store divergence root is resolved, and the quality/ablation verification
surface is shipped. The remaining Phase 1-6 items below remain the governing
design for conformance, vocabulary, and cross-copilot proof work.

**Why this was Phase 0 of graph migration:** The status column became the
Decision lifecycle primitive, `_ensure_schema_v2()` the adapter migration
pattern, and `count_verified_decisions()` the conservation query. These
semantics now govern the shared AGE runtime.

### Phase 1: Protocol v2 Design + SOC Inventory + Conformance Design (SHIPPED)

**Duration:** 2-3 weeks. **Prerequisite:** Phase 0.
**Key change from earlier plans:** SOC schema inventory moves HERE
(before S2P migration), not after. SOC is already AGE-backed and
richer than S2P — the canonical vocabulary must be designed WITH
SOC's existing schema, not in isolation.

| Item | Repo | What |
|---|---|---|
| **GraphStore Protocol v2** | copilot-sdk | Define governed-memory extension (see §X below) |
| **SOC AGE label inventory** | soc-copilot | Document every label, edge, property in SOC's AGE |
| **Canonical vocabulary diff** | ci-platform | Diff §4 canonical model vs SOC's actual schema |
| **Conformance test DESIGN** | copilot-sdk | Test specs for Protocol v2 (SQLite + AGE) |
| **AGE adapter gap analysis** | ci-platform | What AGEGraphStoreAdapter is missing vs Protocol v2 |
| **Idempotency key scheme** | copilot-sdk | Define key format for outbox replay (decision_id, event_id sufficiency check) |

**Gate result:** Protocol v2 is defined, SOC inventory/configuration work is
recorded, canonical vocabulary work is governed, and conformance tests are
shipped. This phase is complete; remaining vocabulary proof is Program B.

**Why SOC inventory is here:** If we design the canonical vocabulary
without SOC, then migrate S2P to AGE in Phase 3, then discover SOC
uses different labels for the same concepts — we have two incompatible
vocabularies in one AGE instance. The whole point of the shared graph
is one vocabulary. Design it once, with SOC's reality in hand.

### Phase 2: Conformance Implementation + Factory (SHIPPED)

**Historical duration:** 2-3 weeks. Phase 1 and the AGE cutover are shipped.
The factory requires GraphConfig and never assumes a production SQLite path.

```python
# copilot_sdk/graph/factory.py
def create_graph_store(
    domain: str,
    decision_id_prefix: str,
    config: GraphConfig,
) -> GraphStore:
    if config.backend == "age":
        return AGEGraphStoreAdapter(
            config.dsn, config.graph_name, domain, decision_id_prefix
        )
    if config.backend == "sqlite" and config.test_only:
        return SQLiteGraphStore(config.test_path, domain, decision_id_prefix)
    raise RuntimeError("AGE is required for production graph access")
```

| Item | Repo | What |
|---|---|---|
| **Protocol v2 implementation** | copilot-sdk | Add write_observation, write_evidence_receipt, write_conservation_status, write_fingerprint to GraphStore |
| **Conformance test suite** | copilot-sdk | Parametrized for SQLite + AGE, testing all Protocol v2 methods |
| **AGE adapter hardening** | ci-platform | Fix all conformance failures in AGEGraphStoreAdapter |
| **SQLite adapter updates** | copilot-sdk | Add observations table, evidence_receipts table |
| Factory function | copilot-sdk | create_graph_store() |
| Trading main.py | copilot-sdk | Replace direct construction |
| Purchasing main.py | copilot-sdk | Same |
| DataOps main.py | copilot-sdk | Same |
| S2P main.py | s2p | Same |

**Production backend:** AGE through GraphConfig. SQLite is available only in
an explicitly marked unit-test configuration that sets `GRAPH_BACKEND=sqlite`.

**Conformance tests cover (Protocol v2 — all methods):**
```
write_decision, write_outcome, write_observation,
count_decisions, count_verified_decisions,
write_evidence_receipt, write_conservation_status,
write_fingerprint, write_centroid_checkpoint,
write_evolution_event, entity_link,
archive_decisions, domain_scoped_reset, close,
decision_lifecycle, observation_not_counted,
observation_excluded_from_V, observation_excluded_from_flywheel,
evidence_receipt_hash_chain_integrity,
domain_scoped_reset_only_clears_target,
archive_pending_does_not_affect_V
```

**Standing rule #38:** No copilot main.py may construct SQLiteGraphStore
directly. Must use create_graph_store().

**Gate result:** All shipped parity tests pass; production is AGE-backed and
explicit test adapters retain identical protocol semantics.

### Phase 3: S2P AGE Migration (First Non-SOC)

**v2.9 status:** SHIPPED for the runtime cutover. S2P is on AGE; the
cross-copilot traversal proof and remaining migration artifacts stay in the
forward Program B track.

**Duration:** 2-3 weeks. **Prerequisite:** Phase 2 factory.
**Why S2P first:** $604K cross-graph finding requires real traversal.
S2P PW failures exposed SQLite cost. S2P↔SOC in one AGE proves
cross-copilot.

| Item | Repo | What |
|---|---|---|
| S2P GRAPH_BACKEND=age | s2p | Factory switch + env |
| S2P AGE extensions | ci-platform | Invoice, supplier, process entities |
| SQLite→AGE migration | s2p | Script reads .db, writes AGE nodes |
| Shadow comparison | s2p | Diff SQLite vs AGE responses |
| S2P PW on AGE | copilot-sdk/e2e | Tests pass with GRAPH_BACKEND=age |
| Cross-copilot query | ci-platform | S2P↔SOC traversal works |
| demo.py S2P AGE | copilot-sdk | Start S2P on AGE |

**Gate:** S2P passes all tests on AGE. PW workers=4. Cross-copilot
query returns correct results. Conservation GREEN.

### Phase 4: SDK Copilots AGE Migration

**v2.9 status:** SHIPPED for the runtime cutover. Trading, Purchasing, and
DataOps run on AGE with no silent SQLite fallback; remaining proof gates stay
in the forward track.

**Duration:** 1-2 weeks. **Prerequisite:** Phase 3 stable.

| Item | Repo | What |
|---|---|---|
| Trading on AGE | copilot-sdk | Factory config |
| Purchasing on AGE | copilot-sdk | Factory config |
| DataOps on AGE | copilot-sdk | Factory config (DSN already exists) |
| Migration scripts | copilot-sdk | SQLite→AGE per copilot |
| Bundle restore via protocol | copilot-sdk | JSON bundles, GraphStore API |

**Gate:** All SDK tests pass on AGE. All PW tests pass. Demo runs 5
copilots on one AGE instance.

### Phase 5: SOC Compatibility Views (if inventory requires)

**Duration:** 1-2 weeks. **Prerequisite:** Phase 4.
**Note:** SOC inventory was completed in Phase 1. This phase implements
any compatibility views or schema changes identified in that inventory.
If Phase 1 found SOC labels already match canonical vocabulary, this
phase is minimal or skipped.

| Item | Repo | What |
|---|---|---|
| Compatibility views | ci-platform | Views/aliases for any SOC labels that differ from canonical |
| SOC route updates | soc | Update routes to use canonical labels (or views) |
| SOC test verification | soc | All BE + PW tests pass (counts at time of execution) |

**Gate:** SOC routes work with canonical vocabulary. Cross-copilot
queries use one label vocabulary across SOC + S2P + SDK copilots.

### Phase 6: Cross-Copilot Proof

**Duration:** 1 week. **Prerequisite:** Phase 5.

| Item | What |
|---|---|
| Transfer traversal | SOC pattern → DataOps rule → S2P variant |
| Cross-graph discovery | SAP change → S2P impact → DataOps alert |
| Global conservation | All domains in one query |
| Global IKS | IKS trajectories across domains |
| demo.py display | All: [shared judgment graph] |
| Outreach update | Every claim demonstrably true |

**Gate:** Every claim in §2 has a working query. No fixtures. No API
stitching. Pure graph traversal.

---

## §11 — Blast Radius

| Impact | SOC | S2P | Trading | Purchasing | DataOps |
|---|---|---|---|---|---|
| Backend | AGE runtime | AGE runtime | AGE runtime | AGE runtime | AGE runtime |
| Frontend | None | None | None | None | None |
| PW tests | None | Re-run on AGE | Re-run on AGE | Re-run on AGE | Re-run on AGE |
| Seed data | Verify fixtures | Migration script | Migration script | Migration script | Migration script |
| Conservation | V=verified | V=verified | V=verified | V=verified | V=verified |
| Audit chain | Verify on views | Chain on AGE | Chain on AGE | Chain on AGE | Chain on AGE |
| AgentEvolver | Verify edges | TRIGGERED_EVOLUTION on AGE | Same | Same | Same |
| Transfer | Source | First cross-copilot target | Later | Later | Later |

**What does NOT change:** Scoring semantics, factor computation, frontend
components, API signatures, tensor shapes, conservation formula, math
framework, outreach claims, proof labels.

---

## §12 — SQLite Adapter Role (Permanent)

SQLite is not a production graph backend. Its only permitted roles are
explicit unit-test fixtures; non-graph PersistenceOutbox and labeled,
temporary demo bundle restore are separate exceptions:

| Role | Acceptable | Not acceptable |
|---|---|---|
| Unit tests | ✅ Fast, deterministic | — |
| Unit-test fixtures | ✅ Explicit `GRAPH_BACKEND=sqlite` or InMemory | — |
| PersistenceOutbox | ✅ Non-graph queue only | ❌ Reading it as Decision state |
| Demo bundle restore | ✅ Labeled and temporary | ❌ Treating it as the product graph |
| PersistenceOutbox | ✅ Non-graph scoring/persistence queue | ❌ Reading it as graph state |
| Demo bundle restore | ✅ Labeled, temporary protocol restore | ❌ Treating it as the product graph |
| Product deployment | — | ❌ Never |
| Outreach demos | — | ❌ Cannot demonstrate cross-copilot |

SQLite and InMemory MUST implement the same GraphStore protocol for explicit
tests and mirror canonical state: decisions.status, outcomes,
centroid_checkpoints, evolution_events, and decision_entity_edges. They are
never production Decision stores. PersistenceOutbox is non-graph and may
queue the exact payload for later GraphStore→AGE persistence; it is not a
read source for Decision data.

---

## §12a — GraphStore Protocol v2 (Governed-Memory Extension)

Protocol v1 (current): write_decision, write_outcome, count_decisions,
centroid_checkpoint, evolution_event, entity_link, archive, close.

**Protocol v2 adds governed-memory primitives.** Conformance tests in
Phase 2 must test ALL Protocol v2 methods against BOTH adapters.

### Required Methods

| Method | What | Conservation impact |
|---|---|---|
| `write_decision(...)` | Create Decision(pending) | No — pending doesn't count toward V |
| `write_outcome(...)` | Create Outcome + update Decision status | YES — transitions to confirmed/overridden, counts toward V |
| `write_observation(...)` | Create Observation from preview/read | No — excluded from V, excluded from flywheel |
| `count_decisions(domain)` | Count ALL decisions (audit/total) | Used for audit, NOT conservation |
| `count_verified_decisions(domain)` | Count confirmed+overridden | THIS is V in conservation formula |
| `write_evidence_receipt(...)` | Hash-chained audit entry | No — audit, not conservation |
| `write_conservation_status(...)` | Persist conservation snapshot | No — records computation, not input |
| `write_fingerprint(...)` | Factor quality snapshot | No |
| `write_centroid_checkpoint(...)` | Judgment geometry snapshot | No |
| `write_evolution_event(...)` | AgentEvolver trace | No |
| `link_entity(decision_id, entity_id)` | Decision→DomainContext edge | No |
| `archive_decisions(domain, before, status)` | Move to archive table | Reduces active V if verified rows archived |
| `domain_scoped_reset(domain)` | Clear domain partition | Resets V to 0 for domain |
| `close()` | Release resources | — |

### Observation Write Spec

```python
def write_observation(
    self,
    observation_id: str,
    domain: str,
    category: str,
    recommended_action: str,
    confidence: float,
    source_route: str,      # 'preview' | 'what-if' | 'simulation' | 'batch-score'
    scorer_version: str,
    factor_schema_version: str,
    metadata: dict | None = None,
) -> None:
    """Write an Observation node. NOT a Decision.
    Observations are excluded from conservation V and AgentEvolver."""
```

### Conservation Status Write Spec

```python
def write_conservation_status(
    self,
    domain: str,
    V: int,
    q: float,
    alpha: float,          # category coverage, NOT penalty ratio
    theta_min: float,
    verified_count: int,
    correct_count: int,
    status: str,           # 'GREEN' | 'AMBER' | 'RED'
    policy_version: str,
) -> None:
    """Persist auditable conservation snapshot."""
```

---

## §12b — AGE Failure Policy (Operation-Specific)

"Fail-closed" is too generic. Different operations have different
failure behaviors when AGE is unavailable.

| Operation | On AGE failure | Rationale |
|---|---|---|
| **Read/preview** | **Surface AGE failure** — no fixture, SQLite, or in-memory Decision substitute | Goal 3 prohibits silent substitution; a non-graph UI cache must be explicitly labeled and is not graph state. |
| **Score (POST /api/score)** | **Queue exact Decision payload in PersistenceOutbox and surface persistence pending** — final Decision persistence still goes through GraphStore→AGE | Scoring may compute a request without claiming it is persisted; no alternate Decision store is read. |
| **Learn/outcome (POST /api/learn)** | **Fail-closed — block until AGE available** — do not lose verified outcomes | Outcomes are conservation inputs. Losing an outcome means V is wrong. Queue locally with retry, surface error if retry exhausts. |
| **Evidence/audit write** | **Queue with retry** — do not lose, do not block user | Audit must be durable but can tolerate seconds of delay. Local outbox with sync. |
| **Observation write** | **Best-effort through GraphStore** — drop only with explicit telemetry | Observations are optional analytics and are not Decision substitutes. |
| **Conservation snapshot** | **Queue with retry** — recompute when AGE recovers | Snapshots are derived from V/q/α. Recomputable. Don't block. |
| **Evolution event write** | **Queue with retry** — AgentEvolver events must not be lost | Evolution lineage is procedural memory. Losing events breaks promotion/rollback trace. |

**PersistenceOutbox pattern:** When AGE is unavailable, exact pending payloads
that must not be lost may go to the non-graph `PersistenceOutbox`. A sync
process replays them through GraphStore when AGE recovers. Outbox writes use
idempotency keys (decision_id, event_id) to prevent duplicates on replay; the
outbox is never queried as Decision graph state.

---

## §12c — Store Parity (v2.9)

AGE, SQLite, and Memory are conformance-equivalent adapters for the shipped
judgment-memory operations. AGE is the only runtime product backend; SQLite
and Memory are explicit unit-test adapters. The factory raises when AGE is
requested but unavailable; there is no silent fallback.

| Method | AGE | SQLite | Memory | Parity |
|---|---|---|---|---|
| `write_outcome` | Idempotent | Idempotent | Idempotent | ✅ |
| `write_centroid_checkpoint` | V2 + quality | V2 + quality | V2 + quality | ✅ |
| `load_latest_centroids` | Newest by epoch | Newest by epoch | Newest by epoch | ✅ |
| `get_centroid_checkpoints` | `include_v2` | `include_v2` | `include_v2` | ✅ |
| `update_centroid` (L5) | Domain upsert | Domain upsert | Domain upsert | ✅ |
| conservation | Domain-scoped | Domain-scoped | Domain-scoped | ✅ |
| count verified/correct | Status predicates | Status predicates | Status predicates | ✅ |

Forty-five conformance tests verify this parity. `write_outcome` with the
same action is a silent duplicate return; a conflicting action raises
`ValueError`; an unknown decision raises `KeyError`.

## §12d — Quality Axis (v2.9; `quality_axis`)

V2 centroid checkpoints may include:

```text
quality_window_size
quality_verified_count
quality_correct_count
rolling_accuracy
quality_policy_version
```

The quality object is derived only from verified decisions. Legacy checkpoints
return `quality = null`; consumers must render nothing for that case rather
than fabricate `0%`, `N/A`, or another default. The quality axis complements
the locked conservation variables: `q` remains rolling accuracy over the
verified window, α remains category coverage, and V remains verified volume.

## §12e — Centroid Ablation (v2.9)

The endpoint
`GET /api/self/centroid-history/{checkpoint_id}/counterfactual?window=N`
returns a centroid-ablation analysis with:

```json
{
  "analysis_type": "centroid_ablation",
  "held_fixed": ["dk_weights", "temperature"],
  "decisions_rescored": 0,
  "change_rate": 0.0
}
```

This is not a point-in-time replay. A checkpoint does not store DiagonalKernel
weights or temperature, so the endpoint holds the current `_dk_weights` and
`tau` fixed while rescoring the selected window with checkpoint centroids.
The contract includes a zero-identity gate. Full `SNAPSHOT_AFTER` traversal
and historical model-state replay are deferred to Program B.

## §12f — Cleanup (v2.9)

The v2.9 authority records these shipped cleanup removals and updates:

| Item | Status |
|---|---|
| `neo4j_uri` and `neo4j_password` removed from `GraphConfig` | **SHIPPED** |
| `db/neo4j.py` deleted from SOC and S2P | **SHIPPED** |
| Neo4j collision logs silenced | **SHIPPED** |
| `test_graph_client_conformance` updated for the deleted module | **SHIPPED** |

These changes do not weaken the AGE authority or the GraphStore abstraction.

## §12g — Forward Program B

| Item | What | Status |
|---|---|---|
| B1-B3 | Migration preparation | **DONE** |
| B4 | Per-copilot cutover verification | **DONE** |
| B5 | `SNAPSHOT_AFTER` backfill + traversal API | **DONE — 17 tests, 808 checkpoints scanned, lineage endpoints live** |
| B6 | InMemory conformance | **DONE** |
| B7 | Neo4j rename | **REMAINING — 700 refs** |
| B8 | PgBouncer deployment | **REMAINING** |
| B+ cross-copilot transfer | Semantic transfer with `TransferPattern` nodes | **DONE — 34 tests, SOC→Trading demo beat, conservation-gated** |
| B+ trust traps | Trust traps and decision rollback | **REMAINING — design needed** |

Program B also includes the shipped cross-copilot semantic transfer with
`TransferPattern` nodes. Trust traps and decision rollback remain, as does
the remaining Counterfactual Option B (persisted DK/τ for point-in-time
replay) and the seven deferred math invariant gaps #6, #7, #9, #10, #11, #15,
and #16. These are explicitly remaining; the shipped centroid ablation
contract is not point-in-time replay.

Program B extends the shipped v2.9 substrate. It does not reopen the locked
decisions, remove the `SNAPSHOT_AFTER` model, or restore SQLite as a runtime
fallback.

## §12h — Confirmed P1 Findings

| Item | Value | Source/implication |
|---|---|---|
| ProfileScorer temperature | `tau` | ProfileScorer implementation |
| ProfileScorer DK weights | `_dk_weights` | ProfileScorer implementation |
| Verified decisions method | `get_verified_decisions(domain)` | GraphStore protocol |
| `created_at` | Caller-supplied; AGE permits it | Normalize on read |
| IKS implementations | SDK composite differs from canonical drift | Canonical drift is used on checkpoints |
| DataOps custom route | Zero-caller gate passed | **Deleted** — shared route is sole path |

## §12i — What v2.9 Does Not Change

- The four memory types model — Episodic, Semantic, Procedural, Judgment — is unchanged.
- The conservation law `α·q·V ≥ θ_min` is unchanged.
- Canonical Purchasing tensor dimensions are `(5,4,7) = 140` centroid
  cells; factor 7 is `price_memory_index` (legacy `(5,4,6)` checkpoints
  remain readable through the explicit migration path).
- Learning rates `η_confirm=0.05` and `η_override=0.01` are unchanged.
- The `SNAPSHOT_AFTER` model in the specification is unchanged: deferred, not removed.
- GraphStore remains the storage abstraction, strengthened by all-five AGE runtime parity.

---

# PART V — GOVERNANCE

---

## §13 — Test Strategy

### Level 1: GraphStore Conformance (shipped; historical Phase 1)

```python
@pytest.fixture(params=["sqlite", "age"])
def graph_store(request):
    if request.param == "sqlite":
        return SQLiteGraphStore(":memory:", "test", "TEST-")
    else:
        return AGEGraphStoreAdapter(DSN, "test_graph", "test", "TEST-")

def test_write_decision(graph_store): ...
def test_write_outcome(graph_store): ...
def test_count_decisions(graph_store): ...
def test_count_verified_decisions(graph_store): ...
def test_centroid_checkpoint(graph_store): ...
def test_evolution_event(graph_store): ...
def test_entity_link(graph_store): ...
def test_conservation_counts_verified_only(graph_store): ...
def test_decision_lifecycle(graph_store): ...
def test_observation_not_counted(graph_store): ...
# Protocol v2 methods
def test_write_observation(graph_store): ...
def test_write_evidence_receipt(graph_store): ...
def test_write_conservation_status(graph_store): ...
def test_write_fingerprint(graph_store): ...
def test_domain_scoped_reset(graph_store): ...
def test_archive_decisions(graph_store): ...
```

### Level 2: Per-Copilot on AGE (Phases 3-4)

Run existing suites with `GRAPH_BACKEND=age`. Zero test modifications.
Any failure reveals adapter gap, not test problem.

### Level 3: Cross-Copilot Traversal (Phase 6)

```python
def test_transfer_traversal():
    """SOC pattern → DataOps rule → S2P variant."""
def test_cross_graph_discovery():
    """SAP change → S2P invoice → DataOps alert."""
def test_global_conservation():
    """Conservation across all domains."""
```

### Level 4: Regression Prevention

- Standing rule #38: Use factory, not direct construction.
- CI gate: GRAPH_BACKEND=age tests must pass before merge.
- No test may assume SQLite-specific behavior in protocol tests.

---

## §14 — Standing Rules

| # | Rule | Reference |
|---|---|---|
| **#37** | V in conservation = verified decisions only (status IN confirmed, overridden) | §6 |
| **#38** | Copilot main.py must use create_graph_store(), not construct SQLiteGraphStore directly | §10 Phase 2 |
| **#39** | Preview/read endpoints create Observation nodes, not Decision nodes | §5 |
| **#40** | SQLite is never described as "the product graph" in any material | §12 |
| **#41** | Cross-domain queries must include explicit domain filter unless intentionally cross-copilot | §4.3 |
| **#86** | Every Codex session must pass mypy on all changed files before declaring success | v2.8 authority update |
| **#87** | The seven JM design goals are constraints, not aspirations; no design document or LLM-generated scope limit may defer one without explicit founder approval | §0 |
| **#88** | No new Neo4j references; all new code uses AGE or graph naming | §0, cleanup |

---

## §15 — Open Questions

| # | Question | Status | Resolution |
|---|---|---|---|
| 1 | AGEGraphStoreAdapter conformance gaps | **PARTIALLY SHIPPED** | 45 parity tests pass; broader GAE conformance remains in Program B |
| 2 | SOC AGE label mapping | **SHIPPED inventory** | Remaining compatibility proof is governed by Program B |
| 3 | AGE reset: domain or full? | OPEN | Domain-scoped (recommended) |
| 4 | Bundle format: SQLite or protocol? | **SHIPPED** | Protocol-based JSON restore; temporary and labeled |
| 5 | Transfer patterns: nodes or views? | OPEN | Nodes — queryable (recommended) |
| 6 | Minimum evidence per decision | OPEN | Hash of factors + decision + timestamp |
| 7 | AGE failure policy | **SPECIFIED in §12b** | Operation-specific (7 operations defined) |
| 8 | ConservationStatus persistence | OPEN | On status transitions (recommended) |
| 9 | Observation promotion to Decision | OPEN | Explicit command, not automatic |
| 10 | Protocol v2 idempotency keys | **PARTIALLY SHIPPED** | `write_outcome` is idempotent across AGE, SQLite, and Memory; broader outbox replay policy remains governed by §12b |
| Q11 | SNAPSHOT_AFTER reader/traversal and point-in-time model state | **SHIPPED** — B5 traversal API live, backfill complete, lineage endpoints on all 5 copilots. Point-in-time model state (DK/τ on checkpoint) remains deferred. | Existing AGE V2 writer and lineage traversal are live; historical DK/τ replay remains deferred |
| Q12 | Cross-copilot transfer demo and traversal proof | **SHIPPED** — Semantic cross-copilot transfer with `TransferPattern` nodes in AGE, shape-safe factor/category insight mapping, conservation-gated. SOC→Trading demo beat verified. | Shared `soc_graph` transfer infrastructure and demo are live |
| 13 | Trust traps and lineage-driven decision rollback | **OPEN — Program B** | Requires SNAPSHOT_AFTER traversal and rollback lineage |
| 14 | Neo4j rename and PgBouncer deployment | **OPEN — tech debt / Program B** | 700 references and deployment work remain; no new references permitted |
| Q15 | SOC G1 boundary | **DECIDED, implementation pending** | Option A (strict) decided; `RL_EXPLORATION_ENABLED` prod flag + structural fix pending in RL Tier 1. Exploration becomes proposal/shadow only. |
| Q16 | RL evolution spine uniformity | **DESIGNED** | Design finalized in `rl_consolidated_verification_and_design.md`; Tier 1 (WP-0 + WP-1) and Tier 2 (WP-2-6) implementation pending. |

---

## §16 — Coding Session Implementation Guide

### Which document to follow

**ONE document per phase. No dual-reading.**

| Phase | Follow THIS document | Why |
|---|---|---|
| **P0-P2** (shipped) | **This document (JM v2.9)** | Governs the shipped AGE cutover, GraphStore paths, domain constraints, quality, and parity. |
| **Program B** (next) | **This document (JM v2.9)** | Governs SNAPSHOT_AFTER traversal, cross-copilot proof, rollback, trust traps, and deployment tech debt. |

**Every coding session must read this authority before changing graph or
judgment-memory behavior.** Historical S2P PW v2.4 prompts and migrations may
be consulted as implementation history, but they cannot override this
document or defer the seven design goals.

The historical fix ordering was Fix 4 → Fix 1 → Fix 3a → Fix 3b → Fix 3c.
That sequence is complete. New work follows Program B and must preserve the
GraphStore→AGE, GraphConfig, domain, and shared-graph constraints.

### P0-P2 summary (shipped; historical details in S2P PW v2.4)

| Order | Fix | What | Where in S2P PW v2.4 |
|---|---|---|---|
| 1st | Fix 4: CI_DATA_DIR | Historical S2P lifecycle alignment | **SHIPPED** |
| 2nd | Fix 1: count_decisions() | O(1) conservation counting | **SHIPPED** |
| 3rd | Fix 3a: status column | `_ensure_schema_v2()` + verified counting | **SHIPPED** |
| 4th | Fix 3b: conservation V | Verified-only counting | **SHIPPED** |
| 5th | Fix 3c: S2P archive | Archive ghost decisions | **SHIPPED** |
| P0-P2 | AGE switch and judgment surface | Five copilots, shared graph, quality, ablation, parity | **SHIPPED** |

### Must NOT do (regardless of phase)

- Do NOT revert any copilot from AGE to SQLite for production Decision data.
- Do NOT add `SQLiteGraphStore` instantiation in production code paths.
- Do NOT bypass GraphStore, GraphConfig, domain scoping, or domain stamping.
- Do NOT substitute fixtures, SQLite, or InMemory data when AGE is declared.
- Do NOT create custom AGE schemas per copilot — use canonical vocabulary from §4
- Do NOT change SOC AGE schema before compatibility views designed (Phase 1 inventory first)
- Do NOT build expiry logic (expired = future)
- Do NOT create Decision nodes from GET preview/read endpoints
- Do NOT describe SQLite as product graph in any artifact
- Do NOT redefine α as penalty ratio or conservation coefficient
- Do NOT treat V as an open question — it is LOCKED as verified-only
- Do NOT reopen shipped P0-P2 decisions to create a second production backend.

### Documents to create/update in repo

- `docs/design/judgment_memory_v2_9.md` — this document
- `docs/graph_vocabulary.md` — canonical labels from §4
- `copilot_sdk/graph/factory.py` — Phase 2
- `tests/graph/test_conformance.py` — Phase 1
- Standing rules: #37-#41 and #86-#88

---

---

## §17 — Review Notes (v2.0 → v2.1)

**Issues found and fixed in comprehensive review:**

1. **§1.3 wrong edge label.** Used `[:TRIGGERED_BY]` — not in canonical
   vocabulary. Fixed to `[:TRIGGERED_EVOLUTION]` with correct traversal
   direction (Decision → EvolutionEvent, not reverse).

2. **§1.3 TransferPattern traversal syntax.** Showed a chain through
   Domain nodes, but FROM_DOMAIN and TO_DOMAIN are both outgoing from
   TransferPattern. Fixed to two-arm MATCH pattern.

3. **§4.1 EvidenceReceipt missing.** Referenced in edges (EMITTED_RECEIPT)
   but had no node definition. Added with full property spec including
   hash chain description (previous_hash → payload_hash traversal).

4. **§6 Cypher query inefficient and potentially incompatible.** Three
   separate MATCH clauses scanning same nodes. Simplified to single-pass.
   Added AGE dialect warning (CASE/sum support varies by version).

5. **§6 V/verified_count redundancy.** V and verified_count were computed
   separately but are identical by definition (all counted decisions have
   outcomes). Clarified with comment.

6. **Test counts hardcoded.** SOC "1,714 BE" and "281 PW" will drift.
   Changed to "at time of scan" / "at time of execution."

7. **§16 document filename.** Referenced `docs/graph_architecture.md` but
   file is `judgment_memory.md`. Fixed.

8. **Supersedes incomplete.** Only referenced graph_architecture_v1. Now
   references both graph_architecture_v1 AND judgment_memory_v1.

**No issues found with:** Four memory type taxonomy (§1.1), claim-to-gap
mapping (§2), non-negotiable properties (§3.2), canonical node labels
(§4.1 — 12 correct, EvidenceReceipt added = 13), edge labels (§4.2 — all
18 consistent with node model), decision lifecycle (§5), conservation
math justification (§6), implementation map (§7), gap analysis matrix
(§8), all 6 blockers (§9), all 7 migration phases (§10), blast radius
(§11), SQLite role (§12), test strategy (§13), standing rules #37-41
(§14), open questions (§15), Codex must/must-not (§16).

---

## §18 — Document Control

| Version | Date | Key changes |
|---|---|---|
| v2.7 | Prior | AGE canonical, SQLite test-only. `SNAPSHOT_AFTER` model. Conservation V locked. Historical base authority. |
| **v2.8** | **August 6-7, 2026** | **All 5 on AGE. Loader unified. Warm-start guard. Canonical IKS. Quality axis. Centroid ablation. Idempotent outcomes. 45 conformance tests. SOC learning enabled. Factor hash validation. Mypy gate. Neo4j cleanup.** |
| **v2.9** | **August 8, 2026** | **Seven non-negotiable design goals. GraphStore→AGE and GraphConfig constraints. Shared `soc_graph`/`soc_copilot` state. No silent substitution. Domain query/write invariants. Corrected Phase 0-P2 and Program B status. Rules #87-#88.** |
| **v2.9 (update)** | **August 8, 2026** | **B5 `SNAPSHOT_AFTER` shipped. Cross-copilot transfer shipped. SOC atomic transaction. DataOps route deleted. S2P evolver conservation fix. Purchasing/DataOps evolvers wired. RL scan complete. G1 boundary decided. Program B status corrected.** |

v2.7 and v2.8 are historical after this merge. v2.9 is the single governing authority.

---

*Judgment-Memory Architecture v2.9 · August 8, 2026*
*Theory: 4 memory types. End state: ONE AGE graph, 5 copilots.*
*13 node labels (incl. EvidenceReceipt). 18 edge types. Domain-partitioned.*
*Decision lifecycle: pending → confirmed/overridden. Locked.*
*Conservation V = verified only (rule #37). Locked.*
*Preview = Observation nodes, not Decision nodes. Locked.*
*Migration: P0-P2 shipped; Program B carries only the explicitly remaining work.*
*Phase 6 gate: every product claim resolved by graph traversal.*
*"This document governs. Code follows."*
