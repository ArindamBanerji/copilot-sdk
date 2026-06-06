# Judgment-Memory Architecture
## Theory, End State, Implementation, and Migration
**Version:** 2.5 · **Date:** May 30, 2026
**Supersedes:** graph_architecture_v1.md + judgment_memory_v1.md
(this document integrates both: theory from judgment memory analysis
sessions + graph design from architecture v1)
**Integrates:** Judgment memory analysis (fourth cognitive type, April-May
2026 sessions) + Shared governed judgment-memory graph plan (coding session
scan, May 2026) + Graph architecture v1 (end state design, May 30, 2026).
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

**Separate SQLite files make these interactions impossible.** You can fake
them with API endpoints that query two stores and stitch results. But that
is not a graph traversal — it's a join across disconnected databases. It
cannot scale, cannot be audited, and cannot support the "one traversal, one
answer" claim.

---

## §2 — Claims the Current Implementation Cannot Support

| Claim (in outreach) | What it requires | Current reality | Gap type |
|---|---|---|---|
| "One engine, one graph" | Shared graph substrate | 5 separate stores (1 AGE + 4 SQLite) | **STRUCTURAL** |
| "Cross-graph attention" | Traversal across systems | Each copilot queries only its own store | **STRUCTURAL** |
| "$604K cross-graph finding" | SAP × Celonis × operations traversal | Fixture data, not live query | **DEMO** |
| "Pattern transfer SOC→S2P→DataOps" | Transfer edges in shared graph | Badge + API, no shared substrate | **STRUCTURAL** |
| "315 values that compound" | Values in shared graph geometry | Values in isolated SQLite files | **NARRATIVE** |
| "You can't fork judgment" | Judgment in unforkable graph | Judgment in local files, trivially forkable | **NARRATIVE** |
| "One traversal. One answer." | Cross-system query in one operation | Manual cross-store stitching | **STRUCTURAL** |
| Conservation across copilots | Shared decision population | Separate conservation per copilot | **ARCHITECTURAL** |

**Four of eight claims are STRUCTURAL gaps.** They cannot be resolved by
fixture data, API endpoints, or UI badges. They require one shared graph.

---

# PART II — END STATE DESIGN: WHAT WE'RE BUILDING

---

## §3 — Architecture Target (Non-Negotiable)

### 3.1 The End State

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
│  SQLite adapter (local/test ONLY)      │
│  Same protocol. Same lifecycle.        │
│  NOT the product graph. Ever.          │
└────────────────────────────────────────┘
```

### 3.2 Six Non-Negotiable Properties

1. **ONE physical graph** for all copilots in production and demo.
   Apache AGE on PostgreSQL. Domain-partitioned by `domain` property
   on every node.

2. **SQLite is a LOCAL ADAPTER ONLY.** For unit tests, deterministic
   fixtures, and offline development. Never described as "the product
   graph" in any material, demo, commit message, or docstring.

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
  confidence, source,  -- 'preview' | 'what-if' | 'simulation'
  scorer_version, created_at
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
  shape, factor_names_hash, created_at, metadata
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

### 4.2 Edge Labels (Canonical — No Aliases)

```
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

---

# PART III — CURRENT STATE: WHERE WE ARE

---

## §7 — Current Implementation Map

### Per-Copilot Store Architecture (as scanned)

| Copilot | Physical backend | Lifecycle model | demo.py contract | CI_DATA_DIR |
|---|---|---|---|---|
| **SOC** | Apache AGE/PostgreSQL | **Model A** (AGE-owned) | `persistent: False` — honest | N/A |
| **Trading** | Local SQLite | **Model B** (CI_DATA_DIR) | `persistent: True` — correct | ✅ Reads it |
| **Purchasing** | Local SQLite | **Model B** (CI_DATA_DIR) | `persistent: True` — correct | ✅ Reads it |
| **DataOps** | Local SQLite | **Model B** (CI_DATA_DIR) | `persistent: True` — correct | ✅ Reads it |
| **S2P** | Local SQLite | **Model C** (hardcoded) | `persistent: True` — **BROKEN** | ❌ Ignores it |

### The Three Lifecycle Models

The platform has THREE data lifecycle models, not two. The architecture
documents previously framed the world as "AGE vs SQLite." The actual
situation is more complex — and Model C is invisible until it breaks.

**Model A — AGE (SOC):** PostgreSQL/AGE owns the data. demo.py doesn't
manage it (`persistent: False`). Honest.

**Model B — CI_DATA_DIR SQLite (Trading, Purchasing, DataOps):** demo.py
sets `CI_DATA_DIR` → backend reads it → demo.py owns the path. Reset
works. Status works. Contract holds.

**Model C — Hardcoded SQLite (S2P):** S2P hardcodes its DB path in
`main.py` (`Path(__file__).parent / "data"`). Ignores `CI_DATA_DIR`.
demo.py sets `CI_DATA_DIR` → backend ignores it → demo.py owns nothing.
`demo.py --reset s2p` wipes a path that doesn't exist → silent no-op.
`demo.py --status` reads a path that doesn't exist → "no data."
The `persistent: True` flag is a lie.

**Fix 4 closes Model C.** After Fix 4, S2P reads `CI_DATA_DIR` and
becomes Model B. This is not a convenience fix — it is a prerequisite
for Phase 2 (GraphStore factory), which assumes all copilots respect
`CI_DATA_DIR`.

### Per-Copilot Store Detail

| Copilot | Decision store | Outcome store | Evidence/audit | Evolution | Centroid/judgment |
|---|---|---|---|---|---|
| **SOC** | AGE graph client | AGE sync | AGE bootstrapped | AGE nodes/edges | AGE snapshots |
| **Trading** | SQLiteGraphStore (domain='trading') | Same SQLite | SDK routers | SDK evolution | SQLite checkpoints |
| **Purchasing** | SQLiteGraphStore (domain='purchasing') | Same SQLite | SDK routers | SDK evolution | SQLite checkpoints |
| **DataOps** | SQLiteGraphStore (domain='dataops') | Same SQLite | SDK/DataOps routers | SDK evolution | SQLite checkpoints |
| **S2P** | SQLiteGraphStore (domain='s2p') | Same SQLite | S2P routers | S2PEvolutionService | SQLite checkpoints |

### Shared SDK and CI Platform Pieces (Already Built)

| Component | Location | Status |
|---|---|---|
| `GraphStore` protocol | copilot-sdk | ✅ Works — defines write_decision, write_outcome, count, centroid, evolution, entity_link, archive, close |
| `SQLiteGraphStore` | copilot-sdk | ✅ Works — tables for decisions, outcomes, checkpoints, evolution, RL, entity edges, archive |
| `AGEGraphStoreAdapter` | ci-platform | ✅ Started — decision/outcome writes, counts, checkpoints, evolution, entity links, archive no-ops, close |
| SOC on AGE | soc-copilot | ✅ Proven — SOC runs on AGE in demo (BE test count at time of scan) |
| DataOps AGE DSN | copilot-sdk demo.py | ✅ Exists — env vars present, backend not wired |

### What's Missing

1. **GraphStore factory** — copilots construct stores directly
2. **AGEGraphStoreAdapter conformance** — untested against SDK protocol
3. **Canonical vocabulary enforcement** — AGE labels are ad-hoc
4. **ConservationStatus as graph node** — computed transiently
5. **Observation nodes** — preview writes Decision, not Observation
6. **Cross-copilot traversal queries** — impossible with separate stores
7. **Decision lifecycle (status column)** — designed in S2P PW v2.4, not implemented

---

## §8 — Gap Analysis

### Memory type gaps

| Memory type | SOC (AGE) | S2P (SQLite) | Trading (SQLite) | Purchasing (SQLite) | DataOps (SQLite) |
|---|---|---|---|---|---|
| Episodic: decisions | ✅ In AGE | ⚠️ In SQLite | ⚠️ In SQLite | ⚠️ In SQLite | ⚠️ In SQLite |
| Episodic: outcomes | ✅ In AGE | ⚠️ In SQLite | ⚠️ In SQLite | ⚠️ In SQLite | ⚠️ In SQLite |
| Semantic: entities | ✅ In AGE | ❌ Fixtures only | ❌ Fixtures only | ❌ Fixtures only | ⚠️ Partial AGE |
| Procedural: evolution | ✅ In AGE | ⚠️ In SQLite | ⚠️ In SQLite | ⚠️ In SQLite | ⚠️ In SQLite |
| Judgment: centroids | ✅ In AGE | ⚠️ In SQLite | ⚠️ In SQLite | ⚠️ In SQLite | ⚠️ In SQLite |
| Cross-copilot transfer | ❌ Source exists, no shared target | ❌ API badge only | ❌ API badge only | ❌ Not implemented | ❌ API badge only |
| Conservation lifecycle | ⚠️ No status column | ❌ No status column (23K ghost rows) | ⚠️ No status column | ⚠️ No status column | ⚠️ No status column |

**Legend:** ✅ In canonical location. ⚠️ Works but in wrong substrate. ❌ Missing or broken.

---

# PART IV — MIGRATION: HOW WE GET THERE

---

## §9 — Architectural Blockers

### BLOCKER 1: AGEGraphStoreAdapter conformance

**Status:** UNKNOWN — no conformance tests exist.
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

**Status:** DECIDED — V = verified only (standing rule #37).
**Must do:** Implement in Fix 3. Both adapters.

### BLOCKER 4: Preview/read write contamination

**Status:** DECIDED (design) / PENDING (implementation).
**Design:** Observation nodes, not Decision nodes (§5).
**Implementation:** SQLite-level Observation table not yet built.
AGE-level (:Observation) label not yet created. S2P PW v2.4 §13
contains the design spec but it has not been reviewed by the coding
session for implementation feasibility.
**Must do:** Review Observation design with coding session. Implement
in Phase 1 alongside AGE adapter work. Do not mark as DECIDED until
both adapters can create Observation nodes.

### BLOCKER 5: demo.py reset for AGE

**Status:** OPEN.
**Decision:** Domain-scoped reset (preserve other copilots' state).

### BLOCKER 6: Demo bundle format

**Status:** OPEN.
**Decision:** Protocol-based JSON restore through GraphStore, not
SQLite file copy. Bundles enter as `status='pending'`.

---

## §10 — Migration Phases

### Phase 0: Foundation (CURRENT — S2P PW Fixes)

**Duration:** 1 week. **Prerequisite:** None.
**Implementation spec:** S2P Playwright Failures v2.4 (separate document).
This section defines WHAT Phase 0 does and WHY. The S2P PW v2.4 document
defines HOW (Codex prompts, SQL, validation scripts, defensive clauses).
Both documents are authoritative — JM for architecture, S2P PW for
implementation.

### Phase 0 Dependency Chain (Strict — No Reordering)

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
| Fix 4 | S2P reads CI_DATA_DIR env var | Closes Model C → all copilots on Model B → factory viable | §7 lifecycle models |
| Fix 1 | count_decisions() replaces len(get_all_decisions()) | O(1) audit count method — survives alongside count_verified_decisions() | §6 conservation |
| Fix 3a | Adds `status` column + `_ensure_schema_v2()` | **IS the Decision lifecycle** from §5 (pending→confirmed→overridden). Migration pattern reused for AGE in Phase 3. | §5 lifecycle |
| Fix 3b | conservation uses count_verified_decisions() | **IS standing rule #37** (V=verified). Same method on SQLite and AGE. | §6 conservation |
| Fix 3c | Archives unverified S2P rows to decisions_archive | Cleans decision table for Phase 3 S2P→AGE migration. Can't migrate 23,607 ghost rows. **Note:** decisions_archive is denormalized (decisions+outcomes). INSERT must list columns explicitly with NULLs for outcome fields. | §10 Phase 3 |

### Phase 0 Blast Radius

| Fix | Repos | Copilots affected | Tests at risk | Risk |
|---|---|---|---|---|
| Fix 4 | s2p only | S2P only | S2P BE only | **MINIMAL** — 1 line, no semantic change |
| Fix 1 | copilot-sdk + s2p | S2P directly, others inherit | Conservation tests | **LOW** — algorithm only, same value |
| Fix 3a | copilot-sdk | **ALL 5** — schema migration in constructor | All BE suites (~5,484 tests) | **MEDIUM** — one bug breaks 5 copilots |
| Fix 3b | copilot-sdk + s2p | **ALL 5** — V definition changes | Conservation tests | **MEDIUM** — may flip RED→GREEN |
| Fix 3c | s2p only | S2P only | S2P conservation | **LOW** — moves rows, no logic change |

**Fix 3a is the highest-risk item** because `_ensure_schema_v2()` runs in
the SQLiteGraphStore constructor, called by ALL copilots at startup. One
schema migration bug breaks 5 copilots simultaneously. This is why the
Phase 0 gate requires ALL test suites to pass — not just S2P's.

### Phase 0 Items (Ordered)

| Order | Item | Repo | What | Status |
|---|---|---|---|---|
| **1st** | Fix 4: CI_DATA_DIR | s2p | Close Model C → Model B. **Gates everything else.** | Ready |
| 2nd | Fix 1: count_decisions() | copilot-sdk + s2p | O(1) counting (performance) | Codex prompt ready |
| 3rd | Fix 3a: status column | copilot-sdk | _ensure_schema_v2(), count_verified_decisions() | Designed in v2.4 |
| 4th | Fix 3b: conservation V | copilot-sdk + s2p | Use verified-only counting | Designed |
| 5th | Fix 3c: S2P archive | s2p | Archive ghost decisions (explicit column INSERT — archive is denormalized) | Designed in v2.4 |
| 6th | Standing rule #37 | Docs | V = verified | Proposed |

**Why Fix 4 is first:** Fix 3c archives decisions from S2P's DB. If
S2P still hardcodes its path, Fix 3c archives from a DB that demo.py
has never managed, and the migration script in Phase 3 reads a 33MB
file at the wrong location. Fix 4 aligns S2P to Model B so every
subsequent fix operates on the correct, demo.py-managed path.

**Conservation V is platform-wide, not S2P-only:** The current code
counts ALL decisions as V for ALL five copilots (not just S2P).
Trading, Purchasing, and DataOps use `count_decisions()` which includes
pending rows. S2P hit the wall first (23,607 ghost decisions) but every
PW run, every demo session, every preseed adds rows to all copilots.
The collapse is a matter of WHEN, not WHETHER. Fix 3a/3b must ship
to copilot-sdk (affecting all SDK copilots), not just S2P.

**Gate:** All test suites pass with status column. Conservation correct
across all 5 copilots. S2P PW passes workers=4. `demo.py --reset s2p`
works correctly (verifies Fix 4).

**Why this is Phase 0 of graph migration:** The status column IS the
Decision lifecycle primitive. `_ensure_schema_v2()` IS the migration
pattern. `count_verified_decisions()` IS the conservation query. All
transfer directly to AGE in Phase 3.

### Phase 1: GraphStore Conformance

**Duration:** 1-2 weeks. **Prerequisite:** Phase 0.

| Item | Repo | What |
|---|---|---|
| Conformance test suite | copilot-sdk | Parametrized for SQLite + AGE |
| AGE adapter gaps | ci-platform | Fix failures in AGEGraphStoreAdapter |
| Status column on AGE | ci-platform | Decision.status property |
| Observation label on AGE | ci-platform | (:Observation) node type |
| Canonical vocabulary | ci-platform | Labels match §4 exactly |

**Conformance tests cover:**
```
write_decision, write_outcome, count_decisions,
count_verified_decisions, centroid_checkpoint,
evolution_event, entity_link, fingerprint, archive,
close, decision_lifecycle, observation_not_counted
```

**Gate:** Identical assertions pass on both backends. Zero exceptions.

### Phase 2: GraphStore Factory

**Duration:** 1 week. **Prerequisite:** Phase 1 conformance + Fix 4
shipped (S2P must be Model B before factory assumes CI_DATA_DIR).

```python
# copilot_sdk/graph/factory.py
def create_graph_store(
    domain: str,
    decision_id_prefix: str,
    backend: str = os.environ.get("GRAPH_BACKEND", "sqlite"),
    data_dir: str = os.environ.get("CI_DATA_DIR", "~/.ci-platform"),
    dsn: str = os.environ.get("GRAPH_DSN", ""),
    graph_name: str = os.environ.get("AGE_GRAPH_NAME", "ci_graph"),
) -> GraphStore:
    if backend == "age":
        return AGEGraphStoreAdapter(dsn, graph_name, domain, decision_id_prefix)
    else:
        path = Path(data_dir) / domain / f"{domain}.db"
        path.parent.mkdir(parents=True, exist_ok=True)
        return SQLiteGraphStore(str(path), domain, decision_id_prefix)
```

| Item | Repo | What |
|---|---|---|
| Factory function | copilot-sdk | create_graph_store() |
| Trading main.py | copilot-sdk | Replace direct construction |
| Purchasing main.py | copilot-sdk | Same |
| DataOps main.py | copilot-sdk | Same |
| S2P main.py | s2p | Same |

**Default:** `GRAPH_BACKEND=sqlite`. No behavior change until switched.

**Standing rule #38:** No copilot main.py may construct SQLiteGraphStore
directly. Must use create_graph_store().

**Gate:** All test suites pass. GRAPH_BACKEND=sqlite identical to before.

### Phase 3: S2P AGE Migration (First Non-SOC)

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

### Phase 5: SOC Schema Alignment

**Duration:** 1-2 weeks. **Prerequisite:** Phase 4.

| Item | Repo | What |
|---|---|---|
| SOC AGE label inventory | soc | Document all labels, edges, properties |
| Canonical mapping | soc + ci-platform | SOC → canonical labels |
| Compatibility views | ci-platform | Views for SOC routes |
| SOC test verification | soc | All BE + PW tests pass (counts at time of execution) |

**Gate:** SOC routes work via compatibility views. Cross-copilot queries
use one label vocabulary.

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
| Backend | Views only | Factory + migration | Factory | Factory | Factory |
| Frontend | None | None | None | None | None |
| PW tests | None | Re-run on AGE | Re-run on AGE | Re-run on AGE | Re-run on AGE |
| Seed data | Verify fixtures | Migration script | Migration script | Migration script | Migration script |
| Conservation | None (already AGE) | V=verified (Fix 3) | V=verified | V=verified | V=verified |
| Audit chain | Verify on views | Chain on AGE | Chain on AGE | Chain on AGE | Chain on AGE |
| AgentEvolver | Verify edges | TRIGGERED_EVOLUTION on AGE | Same | Same | Same |
| Transfer | Source | First cross-copilot target | Later | Later | Later |

**What does NOT change:** Scoring semantics, factor computation, frontend
components, API signatures, tensor shapes, conservation formula, math
framework, outreach claims, proof labels.

---

## §12 — SQLite Adapter Role (Permanent)

SQLite remains valuable with a clear boundary:

| Role | Acceptable | Not acceptable |
|---|---|---|
| Unit tests | ✅ Fast, deterministic | — |
| Integration tests | ✅ No AGE dependency | — |
| Fixture loading | ✅ Deterministic state | — |
| Offline development | ✅ Works without PostgreSQL | — |
| Demo fallback | ⚠️ Only if labeled [local adapter] | ❌ Claiming shared memory |
| Product deployment | — | ❌ Never |
| Outreach demos | — | ❌ Cannot demonstrate cross-copilot |

SQLite MUST implement the same GraphStore protocol and mirror canonical
state: decisions.status, outcomes, centroid_checkpoints, evolution_events,
decision_entity_edges. Archive tables are adapter-specific retention.

---

# PART V — GOVERNANCE

---

## §13 — Test Strategy

### Level 1: GraphStore Conformance (Phase 1)

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

## §14 — Standing Rules (Proposed Additions)

| # | Rule | Reference |
|---|---|---|
| **#37** | V in conservation = verified decisions only (status IN confirmed, overridden) | §6 |
| **#38** | Copilot main.py must use create_graph_store(), not construct SQLiteGraphStore directly | §10 Phase 2 |
| **#39** | Preview/read endpoints create Observation nodes, not Decision nodes | §5 |
| **#40** | SQLite is never described as "the product graph" in any material | §12 |
| **#41** | Cross-domain queries must include explicit domain filter unless intentionally cross-copilot | §4.3 |

---

## §15 — Open Questions

| # | Question | Status | Recommendation |
|---|---|---|---|
| 1 | AGEGraphStoreAdapter conformance gaps | UNKNOWN — needs testing | Phase 1 will reveal |
| 2 | SOC AGE label mapping | UNKNOWN — needs scan | Compatibility views |
| 3 | AGE reset: domain or full? | OPEN | Domain-scoped |
| 4 | Bundle format: SQLite or protocol? | OPEN | Protocol-based JSON |
| 5 | Transfer patterns: nodes or views? | OPEN | Nodes (queryable) |
| 6 | Minimum evidence per decision | OPEN | Hash of factors + decision + timestamp |
| 7 | AGE down: fail-open or fail-closed? | OPEN | Fail-closed (score continues, learn pauses) |
| 8 | Should ConservationStatus persist every computation or only changes? | OPEN | Only on status transitions (GREEN→AMBER etc.) |

---

## §16 — Coding Session Implementation Guide

### Which document to follow

**ONE document per phase. No dual-reading.**

| Phase | Follow THIS document | Why |
|---|---|---|
| **Phase 0** (now) | **S2P PW Failures v2.4** | Has everything: Codex prompts (§6), SQL (§13), validation scripts, defensive clauses, is_correct mapping. Self-contained. |
| **Phase 1+** (later) | **This document (JM v2.4)** | Conformance tests, factory, AGE migration. Implementation specs TBD after Phase 0 ships. |

**The coding session does NOT need to read the JM document for Phase 0.**
The S2P PW v2.4 document is the single implementation authority for
Phase 0. It contains the ordered fix list, the Codex prompts, the SQL
migrations, the validation sequences, and the test requirements. The JM
document provides architectural context (WHY the fixes matter) but the
coding session can ship all Phase 0 fixes from S2P PW v2.4 alone.

**Fix ordering is enforced in both documents.** S2P PW v2.4 §8 and §13
both specify strict ordering: Fix 4 → Fix 1 → Fix 3a → Fix 3b → Fix 3c.
This document's §10 Phase 0 dependency chain shows the same ordering
with rationale. The two documents agree.

### Phase 0 summary (for quick reference — details in S2P PW v2.4)

| Order | Fix | What | Where in S2P PW v2.4 |
|---|---|---|---|
| 1st | Fix 4: CI_DATA_DIR | One line — S2P reads CI_DATA_DIR | §7 Q4 |
| 2nd | Fix 1: count_decisions() | O(1) conservation counting | §6 (verbatim Codex prompt) |
| 3rd | Fix 3a: status column | _ensure_schema_v2() + count_verified_decisions() | §13 (spec + migration SQL) |
| 4th | Fix 3b: conservation V | Use count_verified_decisions() for V | §13 |
| 5th | Fix 3c: S2P archive | Archive 23,607 ghost rows | §13 (migration SQL) |

### Must NOT do (regardless of phase)

- Do NOT migrate any copilot to AGE before conformance passes
- Do NOT create custom AGE schemas per copilot
- Do NOT add cross-copilot queries before all copilots on AGE
- Do NOT change SOC AGE schema before compatibility views designed
- Do NOT build expiry logic
- Do NOT build Observation nodes before design reviewed
- Do NOT describe SQLite as product graph in any artifact

### Documents to create/update in repo

- `docs/judgment_memory.md` — this document
- `docs/graph_vocabulary.md` — canonical labels from §4
- `copilot_sdk/graph/factory.py` — Phase 2
- `tests/graph/test_conformance.py` — Phase 1
- Standing rules: add #37-#41

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

*Judgment-Memory Architecture v2.5 · May 30, 2026*
*Theory: 4 memory types. End state: ONE AGE graph, 5 copilots.*
*13 node labels (incl. EvidenceReceipt). 18 edge types. Domain-partitioned.*
*Decision lifecycle: pending → confirmed/overridden. Locked.*
*Conservation V = verified only (rule #37). Locked.*
*Preview = Observation nodes, not Decision nodes. Locked.*
*Migration: 7 phases. Phase 0 = current S2P fixes.*
*Phase 6 gate: every product claim resolved by graph traversal.*
*"This document governs. Code follows."*
