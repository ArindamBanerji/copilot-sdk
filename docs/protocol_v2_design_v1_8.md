# GraphStore Protocol v2 — Implementation Design
## Bridge from Architecture (JM v2.7) to Implementation (Codex)
**Version:** 1.8 · **Date:** May 31, 2026
**Reads:** judgment_memory_v2_7.md (architecture authority),
s2p_pw_failures_v2_4.md (Phase 0 implementation spec)
**Purpose:** Fill the gap between locked architecture decisions and
implementation-grade method signatures, return types, idempotency
keys, transaction semantics, and conformance tests.
**Rule:** This document does NOT reopen locked decisions. It specifies
HOW to implement WHAT is already decided.

---

## §1 — Implementation-Readiness Gap List

| # | Gap | Why it blocks AGE migration | Phase | Addressed by |
|---|---|---|---|---|
| 1 | Protocol v2 exact method signatures | Can't write conformance tests without exact params/returns | Phase 1 | This document §2 |
| 2 | Return shapes | Adapters can't be tested for equivalence without defined outputs | Phase 1 | This document §2 |
| 3 | Idempotency key scheme | Outbox replay produces duplicates without keys | Phase 1 | This document §3 |
| 4 | Transaction semantics | write_outcome must atomically update Decision.status | Phase 1 | This document §2 |
| 5 | AGE failure/outbox behavior | Operation-specific failure policy defined but outbox replay order unspecified | Phase 1 | This document §3 |
| 6 | SOC schema inventory | Canonical vocabulary may conflict with SOC's existing labels | Phase 1 | This document §4 |
| 7 | Canonical vocabulary diff | Must verify §4 labels against SOC reality before migration | Phase 1 | This document §5 |
| 8 | Conformance test matrix | No test suite exists for Protocol v2 on either adapter | Phase 2 | This document §6 |
| 9 | domain_scoped_reset implementation | AGE reset must clear domain partition without affecting others | Phase 2 | This document §2 |
| 10 | Observation write semantics | Persisted preview vs pure-read (no write) distinction | Phase 2 | This document §2 |
| 11 | EvidenceReceipt hash-chain payload | What goes into payload_hash is unspecified | Phase 1 | This document §2 |
| 12 | ConservationStatus persistence trigger | Every computation vs only on transitions | Phase 1 | This document §2 |
| 13 | Archive verified-row semantics | Archiving verified rows reduces active V — implications unspecified | Phase 2 | This document §2 |
| 14 | Migration replay safety | SQLite→AGE migration must be replayable without duplicates | Phase 3 | This document §3 |

---

## §2 — Governed GraphStore Protocol v2: Exact Method Signatures

### Convention

All methods use these types:
```python
from typing import Any
Json = dict[str, Any]       # serializable dict
IdKey = str                 # globally unique, format: "{prefix}-{uuid4}"
DomainStr = str             # e.g. "soc", "s2p", "trading"
StatusStr = str             # 'pending' | 'confirmed' | 'overridden'
ConservationStr = str       # 'GREEN' | 'AMBER' | 'RED'
```

---

### 2.0 Compatibility with GraphStore v1 / CompoundingScorer

**Decision: Option A — Protocol v2 is ADDITIVE, not breaking.**

Current `GraphStore.write_decision()` returns a generated `decision_id`
string. `CompoundingScorer.score()` depends on this return value. Protocol
v2 must NOT break this contract.

**Approach:**
- **Keep v1 method:** `write_decision(...) -> str` — unchanged, used by
  current CompoundingScorer. Generates and returns decision_id internally.
- **Add v2 method:** `write_governed_decision(decision_id, ...) -> None` —
  caller supplies ID, Protocol v2 semantics (source, probabilities, status).
- **Migration:** Phase 2 adds `write_governed_decision`. Phase 3+ migrates
  scorer call sites one copilot at a time. v1 method deprecated after all
  copilots migrate. No hard removal until conformance confirms zero v1 usage.

**Tests proving compatibility:**
- `test_v1_write_decision_returns_id` — v1 method still returns generated ID
- `test_v1_scorer_round_trip` — CompoundingScorer.score() works unchanged
- `test_v2_governed_decision_caller_id` — v2 method uses caller-supplied ID
- `test_v1_v2_interop` — v1 decision readable by v2 methods and vice versa

**Deprecation timeline:**
- Phase 2: v2 method added alongside v1
- Phase 3-4: copilot main.py files migrate to v2
- Phase 5+: v1 method marked @deprecated
- Removal: only after all conformance tests confirm zero v1 usage

---

### 2.1 write_decision (v1 — PRESERVED for CompoundingScorer)

**Existing signature (do not change):**
```python
def write_decision(self, ...) -> str:
    # Returns generated decision_id
    # Used by CompoundingScorer.score()
    # Signature matches current GraphStore protocol
```
This method is NOT modified by Protocol v2. It continues to work.

---

### 2.1b write_governed_decision (v2 — NEW)

**Purpose:** Protocol v2 governed decision write. Caller supplies ID.
Status = 'pending'.

```python
def write_governed_decision(
    self,
    decision_id: IdKey,          # "S2P-{uuid4}" or "TRD-{uuid4}"
    domain: DomainStr,
    category: str,
    category_index: int,
    recommended_action: str,
    recommended_index: int,
    confidence: float,
    probabilities: list[float],  # per-action probability distribution
    factor_vector: list[float],
    factor_names: list[str],
    source: str = 'score',       # 'score' | 'preseed' | 'bundle'
    scorer_version: str = '',
    preset_version: str = '',
    factor_schema_version: str = '',
    metadata: Json | None = None,
) -> None:
```

| Property | Value |
|---|---|
| **Return** | None. Raises on failure. |
| **Idempotency key** | `decision_id` — Class A (must-survive): identical payload_hash → skip. Conflicting payload_hash → quarantine/raise. NOT generic INSERT OR IGNORE. |
| **Transaction** | Single atomic write. FactorVector created in same transaction. |
| **Status on creation** | Always `'pending'`. Never confirmed at write time. |
| **SQLite** | INSERT into `decisions` + `factor_vectors` tables. |
| **AGE** | CREATE (:Decision) + (:FactorVector) + [:HAS_FACTOR_VECTOR] + [:IN_DOMAIN]. |
| **Failure** | Raise. Caller handles retry or outbox. |

**Conformance tests:**
- write_governed_decision creates node with status='pending'
- identical payload replay → skip (Class A idempotent)
- conflicting payload with same decision_id → quarantine/raise (Class A conflict)
- factor_vector is persisted and retrievable
- decision is counted by count_decisions but NOT count_verified_decisions

---

### 2.2 write_outcome

**Purpose:** Record human verification. Atomically transitions Decision
status to 'confirmed' or 'overridden'.

```python
def write_outcome(
    self,
    decision_id: IdKey,          # must reference existing Decision
    actual_action: str,
    actual_index: int,
    is_correct: bool,            # True='confirmed', False='overridden'
    reward: float = 0.0,
    verifier: str = "analyst",
    override_reason: str | None = None,
    metadata: Json | None = None,
) -> None:
```

| Property | Value |
|---|---|
| **Return** | None. Raises on failure. |
| **Idempotency key** | `decision_id` — one outcome per decision. See dual-mode idempotency below. |
| **Direct call** | Duplicate outcome for same decision_id **RAISES**. One outcome per decision is a hard invariant. Silent ignore risks masking learn() bugs. |
| **Outbox replay** | Before replaying: check if outcome exists. If exists with identical `(actual_action, actual_index, is_correct)` → **SKIP** (already applied). If exists with different values → **QUARANTINE** outbox record + alert (conflicting outcome). If decision doesn't exist in AGE yet → **RETRY** (outbox ordering ensures decision replays first, but network partition may delay). |
| **Transaction** | ATOMIC: INSERT outcome + UPDATE decisions SET status. Both or neither. |
| **Status mapping** | `is_correct=True` → 'confirmed'. `is_correct=False` → 'overridden'. |
| **SQLite** | INSERT into `outcomes` + UPDATE `decisions` SET status in one transaction. |
| **Schema migration** | Protocol v2 adds `reward`, `verifier`, `override_reason` columns not in current outcomes table. Requires two migration functions (do NOT conflate):
- `_ensure_schema_v3_columns()`: ALTER TABLE outcomes ADD COLUMN reward/verifier/override_reason. Uses PRAGMA table_info check before ALTER (same pattern as _ensure_schema_v2). Idempotent on re-run.
- `_ensure_schema_v3_tables()`: CREATE TABLE IF NOT EXISTS for observations, observation_entity_edges, observation_factor_vectors, evidence_receipts, conservation_snapshots, fingerprints, outbox, outbox_quarantine. Idempotent by definition (IF NOT EXISTS).
Schema versions: v2 = status column (Phase 0), v3 = Protocol v2 (Phase 2). |
| **AGE** | CREATE (:Outcome) + [:HAS_OUTCOME] + SET Decision.status in one transaction. |
| **Failure** | **Raises.** GraphStore.write_outcome() is a synchronous canonical write. It succeeds only after the canonical store (SQLite or AGE) commits. If the store is unavailable, it raises. Outbox fallback is handled by the SERVICE LAYER, not GraphStore. See §2.15 "GraphStore vs Service Layer Boundary." |

**Conformance tests:**
- write_outcome transitions Decision.status from 'pending' to 'confirmed'/'overridden'
- write_outcome for non-existent decision_id raises
- duplicate outcome for same decision_id RAISES (one outcome per decision is a hard invariant)
- after write_outcome, count_verified_decisions increments by 1
- atomic: if UPDATE fails, INSERT is rolled back (no orphaned outcome)

---

### 2.3 write_observation

**Purpose:** Record preview/read scoring. NOT a Decision. Excluded
from conservation V and AgentEvolver flywheel.

```python
def write_observation(
    self,
    observation_id: IdKey,       # "OBS-{uuid4}"
    domain: DomainStr,
    category: str,
    recommended_action: str,
    confidence: float,
    source_route: str,           # 'preview' | 'what-if' | 'simulation' | 'batch-score'
    scorer_version: str,
    factor_schema_version: str,
    entity_id: str | None = None,       # optional: creates ABOUT edge to DomainContext
    factor_vector: list[float] | None = None,  # optional: creates HAS_FACTOR_VECTOR edge
    factor_names: list[str] | None = None,
    metadata: Json | None = None,
) -> None:
```

| Property | Value |
|---|---|
| **Return** | None. |
| **Idempotency key** | `observation_id` — INSERT OR IGNORE. |
| **Transaction** | Single write. No Decision status change. |
| **When to call** | Only when preview/read persistence is desired. Pure reads may skip. |
| **SQLite** | INSERT into `observations` table. If entity_id provided, INSERT into `observation_entity_edges`. If factor_vector provided, INSERT into `observation_factor_vectors` (schema below). |

**observation_factor_vectors schema (created by _ensure_schema_v3_tables):**
```sql
CREATE TABLE IF NOT EXISTS observation_factor_vectors (
    observation_id TEXT NOT NULL,
    domain TEXT NOT NULL,
    dimension INTEGER NOT NULL,
    factor_names TEXT NOT NULL,     -- JSON array
    factor_values TEXT NOT NULL,    -- JSON array
    factor_names_hash TEXT NOT NULL,
    created_at REAL NOT NULL,
    PRIMARY KEY (observation_id)
);
```
Note: This is a SEPARATE table from `factor_vectors` (which has `decision_id NOT NULL`). Observations and Decisions have distinct factor vector stores to preserve the invariant that factor_vectors.decision_id is always a real Decision.

|
| **AGE** | CREATE (:Observation) + [:IN_DOMAIN]. If entity_id provided: + [:ABOUT]->(DomainContext). If factor_vector provided: + (:FactorVector) + [:HAS_FACTOR_VECTOR]. |
| **Failure** | Best-effort. Drop if AGE unavailable. Do not outbox. |

**Conformance tests:**
- write_observation does NOT increment count_decisions
- write_observation does NOT increment count_verified_decisions
- observations are queryable for debugging but excluded from conservation
- duplicate observation_id is silently ignored

---

### 2.4 count_decisions

**Purpose:** Count ALL decisions for audit/total. NOT for conservation.

```python
def count_decisions(self, domain: DomainStr) -> int:
```

| Property | Value |
|---|---|
| **Return** | Integer count of all Decision nodes/rows for domain (any status). |
| **SQLite** | `SELECT COUNT(*) FROM decisions WHERE domain = ?` |
| **AGE** | `MATCH (d:Decision {domain: $d}) RETURN count(d)` |

---

### 2.5 count_verified_decisions

**Purpose:** Count verified decisions for conservation V.

```python
def count_verified_decisions(self, domain: DomainStr) -> int:
```

| Property | Value |
|---|---|
| **Return** | Integer count where status IN ('confirmed', 'overridden'). |
| **This IS V** in the conservation formula. Standing rule #37. |
| **SQLite** | `SELECT COUNT(*) FROM decisions WHERE domain = ? AND status IN ('confirmed','overridden')` |
| **AGE** | `MATCH (d:Decision {domain: $d}) WHERE d.status IN ['confirmed','overridden'] AND (d.archived IS NULL OR d.archived = false) RETURN count(d)` — archived filter required after Phase 2 archive implementation. |

**Conformance tests:**
- returns 0 on empty store
- pending decisions not counted
- confirmed decisions counted
- overridden decisions counted
- observations not counted
- count matches between SQLite and AGE for identical data

---

### 2.6 append_evidence_receipt (renamed from write_evidence_receipt)

**Purpose:** Append to tamper-evident hash chain.

```python
def append_evidence_receipt(
    self,
    receipt_intent_id: IdKey,    # stable idempotency key, e.g. "RCP-{uuid4}"
    domain: DomainStr,
    decision_id: IdKey,          # Decision this receipt is for
    canonical_payload: Json,     # {decision_id, action, confidence, factor_hash, timestamp}
    actor: str,                  # "scorer", "analyst", "agent_evolver"
    source_route: str,           # API route that triggered this receipt
    metadata: Json | None = None,
) -> tuple[int, str]:            # returns (chain_index, payload_hash) — caller already has intent_id
```

**Decision: Option A — STORE-MANAGED APPEND.** The store allocates
chain_index, reads last hash under lock, computes payload_hash, and
writes atomically. Caller provides the canonical payload; store handles
chain integrity. This is safe under concurrency and outbox replay.

**Hash chain payload spec:** compute the hash from the full canonical
receipt content, not only the business payload:
`receipt_payload = {receipt_intent_id, domain, decision_id,
canonical_payload, actor, source_route, metadata or {}}`;
`payload_hash = SHA256(json.dumps(receipt_payload, sort_keys=True))`.
Canonical JSON, sorted keys. Chain fields allocated by the store
(`chain_index`, `previous_hash`) are excluded from this hash because they
are derived during append.

| Property | Value |
|---|---|
| **Return** | `(chain_index, payload_hash)` — caller already has receipt_intent_id. Store returns only computed values. |
| **Idempotency** | `receipt_intent_id` is stable across outbox replay. UNIQUE(domain, receipt_intent_id) + UNIQUE(domain, chain_index). If same receipt_intent_id exists with identical payload_hash → return existing tuple (skip). If same receipt_intent_id with different payload_hash → quarantine/raise conflict. Replay is safe. |
| **Transaction** | Read last receipt + compute hash + INSERT — all under per-domain lock. |
| **Chain integrity** | STORE enforces. Reads `previous_hash` from last receipt (or "GENESIS" for first). Verifies monotonic chain_index. Atomic. |
| **SQLite** | Under `self._lock`: read last receipt, compute, INSERT into `evidence_receipts`. |
| **AGE** | Under advisory lock or `SELECT FOR UPDATE` on domain receipt counter: same logic. |
| **Failure** | Queue the full append intent to outbox (`receipt_intent_id`, domain, decision_id, canonical_payload, actor, source_route, metadata). Replay calls `append_evidence_receipt` again with the same `receipt_intent_id` — identical payload returns existing chain tuple, conflicting payload quarantines/raises, and new payload allocates the next chain_index from the current last hash. Safe. |
| **Concurrent safety** | Per-domain lock serializes appends. Two concurrent writers: one succeeds, one retries. No chain fork. |

**Conformance tests:**
- chain_index is monotonically increasing
- previous_hash matches prior receipt's payload_hash
- "GENESIS" accepted as previous_hash for chain_index=0
- receipt is linked to Decision via EMITTED_RECEIPT edge

---

### 2.7 write_conservation_status

**Purpose:** Persist auditable conservation computation snapshot.

```python
def write_conservation_status(
    self,
    status_id: IdKey,            # "CSV-{uuid4}"
    domain: DomainStr,
    V: int,
    q: float,
    alpha: float,                # category coverage, NOT penalty ratio
    theta_min: float,
    verified_count: int,
    correct_count: int,
    status: ConservationStr,     # 'GREEN' | 'AMBER' | 'RED'
    policy_version: str,         # e.g. "v1"
) -> None:
```

| Property | Value |
|---|---|
| **Return** | None. |
| **Idempotency key** | `status_id`. |
| **When to persist** | On status TRANSITIONS (GREEN→AMBER, AMBER→RED, etc.) and at system startup. NOT every computation. |
| **SQLite** | INSERT into `conservation_snapshots` table (created by _ensure_schema_v3_tables). |
| **AGE** | CREATE (:ConservationStatus) + [:SUMMARIZES_DOMAIN]. |

**SQLite schema for conservation_snapshots (created by _ensure_schema_v3_tables):**
```sql
CREATE TABLE IF NOT EXISTS conservation_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    V INTEGER NOT NULL,
    q REAL NOT NULL,
    alpha REAL NOT NULL,
    theta_min REAL NOT NULL,
    verified_count INTEGER NOT NULL,
    correct_count INTEGER NOT NULL,
    status TEXT NOT NULL,       -- 'GREEN' | 'AMBER' | 'RED'
    policy_version TEXT NOT NULL,
    computed_at REAL NOT NULL   -- Unix epoch
);
CREATE INDEX IF NOT EXISTS idx_conservation_domain
ON conservation_snapshots(domain, computed_at);
```
| **Failure** | Queue with retry. Recomputable from V/q/α if lost. |

---

### 2.8 write_fingerprint

```python
def write_fingerprint(
    self,
    fingerprint_id: IdKey,       # "FPR-{uuid4}"
    domain: DomainStr,
    factor_names: list[str],
    factor_stats: Json,          # per-factor σ, mean, weight
    skipped_incompatible: int,
    window: int,
    metadata: Json | None = None,
) -> None:
```

| Property | Value |
|---|---|
| **Idempotency key** | `fingerprint_id`. |
| **Idempotency** | `fingerprint_id` is the Protocol v2 write idempotency key. Duplicate same `fingerprint_id` with identical payload skips; duplicate same `fingerprint_id` with conflicting payload raises/quarantines. Domain/window replacement is a future query or rollup policy, not current `write_fingerprint` write semantics. |
| **SQLite** | INSERT into `fingerprints` table. |
| **AGE** | CREATE (:Fingerprint) + [:SUMMARIZES_DOMAIN]. |

---

### 2.9 write_centroid_checkpoint

```python
def write_centroid_checkpoint(
    self,
    checkpoint_id: IdKey,        # "CKP-{uuid4}"
    domain: DomainStr,
    category: str,
    action: str,
    centroids: Json,             # serialized centroid state
    decisions_count: int,
    verified_count: int,
    iks: float,
    shape: list[int],
    factor_names_hash: str,
    metadata: Json | None = None,
) -> None:
```

| Property | Value |
|---|---|
| **Idempotency key** | `checkpoint_id`. |
| **SQLite** | INSERT into `centroid_checkpoints` table. |
| **AGE** | CREATE (:CentroidCheckpoint) + [:DERIVED_FROM] linking to recent Decisions. |

---

### 2.10 write_evolution_event

```python
def write_evolution_event(
    self,
    event_id: IdKey,             # "EVO-{uuid4}"
    domain: DomainStr,
    event_type: str,             # 'proposed' | 'shadow' | 'promoted' | 'rejected' | 'rolled_back'
    rule_name: str,
    variant_id: str,
    source_copilot: str | None = None,
    source_rule: str | None = None,
    metric: float | None = None,
    shadow_batch_size: int | None = None,
    min_shadow_batches: int | None = None,
    metadata: Json | None = None,
) -> None:
```

| Property | Value |
|---|---|
| **Idempotency key** | `event_id`. |
| **Transaction** | Single write. |
| **SQLite** | INSERT into `evolution_events` table. |
| **AGE** | CREATE (:EvolutionEvent) + edges to Rule if promoted/rolled_back. |
| **Failure** | Queue with retry. Must not be lost (procedural memory). |

---

### 2.11 link_entity

```python
def link_entity(
    self,
    decision_id: IdKey,
    entity_id: str,              # DomainContext natural_key
    entity_type: str,            # 'alert', 'invoice', 'supplier', etc.
    domain: DomainStr,
) -> None:
```

| Property | Value |
|---|---|
| **Idempotency key** | `(decision_id, entity_id)` pair. |
| **SQLite** | INSERT OR IGNORE into `decision_entity_edges`. |
| **AGE** | MERGE (d:Decision)-[:ABOUT]->(e:DomainContext). |

---

### 2.12 archive_decisions

```python
def archive_decisions(
    self,
    domain: DomainStr,
    before: float,               # Unix epoch (seconds). Adapters convert internally.
    status_filter: str = 'pending',  # which status to archive
    confirm_verified: bool = False,  # MUST be True to archive verified rows
) -> int:                        # returns count of archived rows
```

| Property | Value |
|---|---|
| **Return** | Integer count of rows archived. |
| **Safety guard** | If `status_filter` is 'confirmed' or 'overridden' AND `confirm_verified` is False, raise `ValueError("Archiving verified decisions reduces active V. Pass confirm_verified=True to proceed.")`. This prevents accidental conservation base destruction. |
| **SQLite** | Explicit column INSERT into `decisions_archive` (denormalized — see S2P PW v2.4). DELETE from `decisions`. |
| **AGE** | SET `Decision.archived = true` property. Active V queries add `WHERE (d.archived IS NULL OR d.archived = false)`. No label change — property flag is simplest and preserves traversability. |
| **Cross-doc note** | JM v2.7 §6 conservation Cypher currently lacks the archived filter. MUST be updated to add `AND (d.archived IS NULL OR d.archived = false)` before AGE archiving is tested. Without this, test #20 passes on SQLite (row deleted) but fails on AGE (node still present, counted by conservation). |
| **V impact** | Archiving pending rows: V unchanged. Archiving verified rows: active V decreases. |

---

### 2.13 domain_scoped_reset

```python
def domain_scoped_reset(self, domain: DomainStr) -> None:
```

| Property | Value |
|---|---|
| **Effect** | Deletes ALL nodes and edges for the specified domain. Other domains unaffected. |
| **SQLite** | DELETE FROM decisions/outcomes/observations/etc WHERE domain = ?. |
| **AGE** | MATCH (n {domain: $d}) DETACH DELETE n. |
| **Safety** | MUST NOT affect other domains. Conformance test verifies isolation. |

---

### 2.14 close

```python
def close(self) -> None:
```

| Property | Value |
|---|---|
| **Effect** | Release local database connections. Flush pending LOCAL writes only. Does NOT attempt AGE outbox sync (that's a separate background process). Does NOT block on network. |
| **SQLite** | `self._conn.commit()` then `self._conn.close()`. |
| **AGE** | Close PostgreSQL connection pool. Outbox remains for background sync. |

---

### 2.15 GraphStore vs Service Layer Boundary

**Decision: Option A — GraphStore methods are synchronous canonical writes.**

GraphStore methods (write_outcome, write_governed_decision, etc.) are
STORAGE operations. They succeed after the canonical store commits, or
they raise. They do NOT contain outbox logic, API response formatting,
or retry behavior.

The SERVICE LAYER (copilot backend routers) handles:
- Catching store failures
- Writing to local outbox on AGE unavailability
- Formatting API responses ({status: 'committed'} vs {status: 'accepted_pending_sync'})
- V/conservation impact tracking

```
┌─────────────────────────────────────────────┐
│  API Layer (FastAPI router)                  │
│  POST /api/learn → LearnService.learn()     │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  Service Layer (LearnService)               │
│  try:                                        │
│    graph_store.write_outcome(...)  # → None  │
│    return {status: "committed"}              │
│  except StoreUnavailableError:               │
│    outbox.queue("write_outcome", payload)    │
│    return {status: "accepted_pending_sync"}  │
│  V updates ONLY after canonical commit.      │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  GraphStore (SQLite or AGE adapter)         │
│  write_outcome() → None | raises            │
│  Pure storage. No outbox. No API logic.     │
└─────────────────────────────────────────────┘
```

**API response contract (service layer, NOT GraphStore):**
- AGE available + committed: `{status: "committed", decision_id}`
- AGE unavailable + outbox: `{status: "accepted_pending_sync", decision_id, outbox_id}`
- V updates ONLY on canonical commit (direct or outbox replay)
- UI must show "pending sync" indicator if outbox is non-empty

**Conformance tests (store level):**
- write_outcome succeeds → returns None
- write_outcome on unavailable store → raises StoreUnavailableError
- NO outbox logic in GraphStore tests — that's service layer tests

**Integration tests (service layer):**
- AGE available → API returns "committed", V increments
- AGE unavailable → API returns "accepted_pending_sync", V unchanged
- Outbox replay → V increments after replay commit

---

## §3 — Idempotency and Outbox Design

### 3.1 Idempotency Key Format

```
{PREFIX}-{uuid4}

Prefixes:
  Decision:           S2P-, TRD-, PUR-, DOPS-, SOC-
  Outcome:            keyed by decision_id (one outcome per decision)
  Observation:        OBS-{uuid4}
  EvidenceReceipt:    RCP-{uuid4}
  ConservationStatus: CSV-{uuid4}
  Fingerprint:        FPR-{uuid4}
  CentroidCheckpoint: CKP-{uuid4}
  EvolutionEvent:     EVO-{uuid4}
```

### Idempotency Conflict Policy by Operation Class

**DO NOT use generic INSERT OR IGNORE for all writes.** Different
operation classes require different conflict handling:

**Class A — Must-survive governed writes (payload-hash comparison):**
- `write_governed_decision`: identical replay → skip. Conflicting payload → quarantine/raise.
- `write_outcome`: direct duplicate → RAISE. Outbox replay identical → skip. Conflicting → quarantine.
- `append_evidence_receipt`: same intent_id + same payload → skip. Different payload → quarantine.
- `write_centroid_checkpoint`: identical replay → skip. Conflicting → quarantine.
- `write_evolution_event`: identical replay → skip. Conflicting → quarantine.
- `write_conservation_status`: identical status_id → skip. Conflicting → quarantine. Conservation snapshots are AUDIT TRAIL — never upsert/replace.

**Class B — Recomputable writes (upsert/replace):**
- `write_fingerprint`: recomputable, but Protocol v2 writes are idempotent by `fingerprint_id`. Future domain/window query policy may choose the latest fingerprint; current writes do not replace existing rows.

**Class C — Disposable/best-effort writes (INSERT OR IGNORE acceptable):**
- `write_observation`: INSERT OR IGNORE. Silent drop on duplicate or AGE failure.
- `link_entity`: INSERT OR IGNORE. Duplicate link is harmless.
- v1 `write_decision`: INSERT OR IGNORE for backwards compatibility.

**Canonical payload hash:** For Class A writes, compute
`SHA256(json.dumps(payload, sort_keys=True))` and store alongside
the idempotency key. Replay compares hashes before applying.

### 3.2 Outbox Design

When AGE is unavailable, writes that must not be lost go to a local
SQLite outbox table:

```sql
CREATE TABLE IF NOT EXISTS outbox (
    outbox_id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,         -- 'write_governed_decision', 'write_outcome', etc.
    idempotency_key TEXT NOT NULL,
    payload_json TEXT NOT NULL,      -- serialized method arguments
    payload_hash TEXT NOT NULL,      -- SHA256 of canonical payload for conflict detection
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'synced' | 'quarantined' | 'failed'
    synced_at TEXT DEFAULT NULL,     -- NULL until replayed
    quarantine_reason TEXT DEFAULT NULL,  -- reason if quarantined
    UNIQUE(operation, idempotency_key)
);

CREATE TABLE IF NOT EXISTS outbox_quarantine (
    quarantine_id INTEGER PRIMARY KEY AUTOINCREMENT,
    outbox_id INTEGER DEFAULT NULL,  -- NULL for direct-call conflicts (no outbox record)
    source TEXT NOT NULL DEFAULT 'replay',  -- 'replay' | 'direct' — how conflict was detected
    operation TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    existing_payload_hash TEXT NOT NULL,
    new_payload_hash TEXT NOT NULL,
    new_payload_json TEXT NOT NULL,
    quarantined_at TEXT NOT NULL,
    resolved_at TEXT DEFAULT NULL,
    resolution TEXT DEFAULT NULL     -- 'accepted_new' | 'kept_existing' | 'manual'
);
```

### 3.3 Outbox Replay Order

**Critical:** Replay must respect dependency order:
1. `write_decision` / `write_governed_decision` — Decisions must exist before Outcomes reference them
2. `write_outcome` — Outcomes reference Decisions
3. `append_evidence_receipt` — Receipts reference Decisions
4. `write_evolution_event` — Events may reference Decisions
5. All others — no ordering constraint

Replay sorted by `outbox_id` (insertion order) respects this naturally
IF score() always runs before learn() — which it does by design.

**Outbox worker ownership:** Not yet decided (pull/cron vs push/retry
loop — see Open Questions). Do NOT implement the outbox worker until
this is decided. The outbox data model and replay semantics are defined;
the scheduler/worker is not.

### 3.4 Operation Classification

| Operation | Must survive AGE failure | Outbox? | Idempotent? |
|---|---|---|---|
| write_decision / write_governed_decision | Yes (audit trail) | ✅ Queue | ✅ decision_id |
| write_outcome | **Yes (conservation V)** | ✅ Queue + retry | ✅ decision_id |
| write_observation | No (analytics) | ❌ Drop | ✅ observation_id |
| append_evidence_receipt | Yes (compliance) | ✅ Queue | ✅ receipt_intent_id |
| write_conservation_status | Yes (audit trail — Class A) | ✅ Queue | ✅ status_id |
| write_fingerprint | Recomputable | ❌ Recompute | ✅ fingerprint_id |
| write_centroid_checkpoint | Yes (judgment history) | ✅ Queue | ✅ checkpoint_id |
| write_evolution_event | Yes (procedural memory) | ✅ Queue | ✅ event_id |

---

## §4 — SOC AGE Schema Inventory Plan

### 4.1 Discovery Queries (run against live SOC AGE instance)

```sql
-- Step 0: Discover graph name (do NOT assume 'soc_graph')
SELECT name FROM ag_catalog.ag_graph;
-- Use the returned name in all subsequent queries as $GRAPH_NAME

-- Step 1: List all vertex labels
SELECT * FROM ag_catalog.ag_label
WHERE graph = (SELECT graphid FROM ag_catalog.ag_graph WHERE name = '$GRAPH_NAME')
AND kind = 'v';

-- Step 2: List all edge labels
SELECT * FROM ag_catalog.ag_label
WHERE graph = (SELECT graphid FROM ag_catalog.ag_graph WHERE name = '$GRAPH_NAME')
AND kind = 'e';

-- Step 3: Sample node properties for each label (5 rows each)
-- Replace LabelName with each discovered vertex label
SELECT * FROM cypher('$GRAPH_NAME', $$
  MATCH (n:LabelName) RETURN properties(n) LIMIT 5
$$) AS (props agtype);

-- Step 4: Sample edge properties
SELECT * FROM cypher('$GRAPH_NAME', $$
  MATCH ()-[e:EdgeName]->() RETURN properties(e) LIMIT 5
$$) AS (props agtype);

-- Step 5: Count nodes per label
SELECT * FROM cypher('$GRAPH_NAME', $$
  MATCH (n:LabelName) RETURN count(n)
$$) AS (cnt agtype);
```

### 4.2 Inventory Output Table

| SOC current label | Node/Edge | Properties found | Canonical equivalent | Action |
|---|---|---|---|---|
| (discovered) | vertex | (discovered) | Decision / Outcome / ... | Rename / View / Keep / Add |
| (discovered) | edge | (discovered) | HAS_OUTCOME / IN_DOMAIN / ... | Rename / View / Keep / Add |

**Actions:**
- **Keep** — SOC label matches canonical exactly
- **Rename** — SOC label maps to canonical but name differs (create compatibility view)
- **View** — SOC needs both old and new label (AGE view or dual-label)
- **Add** — Canonical label not present in SOC (create new)
- **Investigate** — SOC has label with no canonical equivalent (document purpose)

### 4.3 Relationship Topology Query

```sql
-- Step 6: Discover relationship topology (start→edge→end triples)
SELECT * FROM cypher('$GRAPH_NAME', $$
  MATCH (a)-[r]->(b)
  RETURN labels(a) AS start_label, type(r) AS edge_type,
         labels(b) AS end_label, count(*) AS cnt
  ORDER BY cnt DESC
$$) AS (start_label agtype, edge_type agtype, end_label agtype, cnt agtype);
```

**Output table:**

| Start label | Edge type | End label | Count | Sample properties | Canonical equivalent |
|---|---|---|---|---|---|
| (discovered) | (discovered) | (discovered) | (discovered) | (sampled) | (mapped) |

This topology map is REQUIRED before canonical vocabulary signoff.
Without it, we may define edges that conflict with SOC's existing
relationship structure.

### 4.4 What Blocks Migration If Not Done

If SOC uses label `Alert` where canonical uses `DomainContext {entity_type: 'alert'}`,
and S2P migrates to AGE with `DomainContext`, then cross-copilot queries like
"find all S2P decisions about entities similar to SOC alerts" fail because
the labels don't match. The entire point of the shared graph is one vocabulary.

---

## §5 — Canonical Vocabulary Finalization Checklist

Before S2P migration (Phase 3), verify every item:

| # | Check | Source | Verified? |
|---|---|---|---|
| 1 | All 13 canonical node labels exist in AGE schema | JM v2.7 §4.1 | |
| 2 | All canonical edge labels from JM v2.7 §4.2 exist in AGE schema | JM v2.7 §4.2 | |
| 3 | `domain` property on every node | JM v2.7 §4.1 | |
| 4 | `created_at` property on every node | JM v2.7 §4.1 | |
| 5 | `schema_version` on nodes that need it | JM v2.7 §4.1 | |
| 6 | Decision.status supports pending/confirmed/overridden | JM v2.7 §5 | |
| 7 | Observation label exists and is distinct from Decision | JM v2.7 §4.1 | |
| 8 | EvidenceReceipt has previous_hash + chain_index | JM v2.7 §4.1 | |
| 9 | ConservationStatus has counts_scope='verified_only' | JM v2.7 §4.1 | |
| 10 | TransferPattern has FROM_DOMAIN + TO_DOMAIN edges | JM v2.7 §4.2 | |
| 11 | SOC inventory complete (no unknown labels) | This doc §4 | |
| 12 | Compatibility views created where needed | This doc §4 | |
| 13 | Conformance tests pass on both adapters | This doc §6 | |

---

## §6 — Conformance Test Matrix

Every test runs parametrized against BOTH SQLite and AGE adapters.
Identical assertions. Any failure = adapter gap, not test problem.

| # | Test name | Behavior asserted | Adapters | Required fixture | Expected failure if broken |
|---|---|---|---|---|---|
| 1 | test_write_decision | Creates Decision(pending), counted by count_decisions | Both | Empty store | Missing decision |
| 2 | test_v1_decision_idempotent | v1 write_decision: duplicate decision_id silently ignored (INSERT OR IGNORE) | Both | 1 v1 decision | Count > 1 |
| 3 | test_write_outcome_confirmed | is_correct=True → status='confirmed' | Both | 1 pending decision | Status != 'confirmed' |
| 4 | test_write_outcome_overridden | is_correct=False → status='overridden' | Both | 1 pending decision | Status != 'overridden' |
| 5 | test_outcome_atomic | If UPDATE fails, outcome INSERT rolled back | Both | 1 pending decision | Orphaned outcome |
| 6 | test_outcome_missing_decision | write_outcome for non-existent decision raises | Both | Empty store | Silent no-op |
| 7 | test_write_observation | Created, queryable, not counted in V | Both | Empty store | Counted in V |
| 8 | test_observation_not_in_V | count_verified_decisions excludes observations | Both | 1 observation | V > 0 |
| 9 | test_observation_not_in_flywheel | No TRIGGERED_EVOLUTION edge from Observation | AGE | 1 observation | Edge exists |
| 10 | test_count_verified_empty | Returns 0 on empty store | Both | Empty store | Non-zero |
| 11 | test_count_verified_pending | Pending decisions not counted | Both | 3 pending decisions | V > 0 |
| 12 | test_count_verified_mixed | Counts only confirmed+overridden | Both | 2 confirmed + 1 pending | V != 2 |
| 13 | test_evidence_receipt_chain | chain_index monotonic, previous_hash links | Both | 3 receipts | Chain broken |
| 14 | test_conservation_status_write | Snapshot persisted with correct fields | Both | 1 status | Missing fields |
| 15 | test_fingerprint_write_read | Write and retrieve fingerprint | Both | 1 fingerprint | Missing |
| 16 | test_centroid_checkpoint | Write and retrieve checkpoint | Both | 1 checkpoint | Missing |
| 17 | test_evolution_event | Write and retrieve evolution event | Both | 1 event | Missing |
| 18 | test_entity_link | Decision linked to DomainContext | Both | 1 decision + 1 entity | No link |
| 19 | test_archive_pending | Pending rows archived, V unchanged | Both | 3 pending + 2 confirmed | V != 2 |
| 20 | test_archive_verified | Archived verified reduces active V | Both | 3 confirmed | V != 0 after archive all. **AGE note:** requires count_verified_decisions Cypher to include `AND (d.archived IS NULL OR d.archived = false)`. |
| 21 | test_domain_scoped_reset | Only target domain cleared | Both | 2 domains, 3 decisions each | Other domain affected |
| 22 | test_idempotent_replay | Replaying all writes produces same state | Both | Full fixture | Count mismatch |
| 23 | test_concurrent_cross_domain | Writes to domain A and B don't interfere | AGE | 2 domains concurrent | Cross-contamination |
| 24 | test_migration_replay | SQLite→AGE migration produces identical counts | AGE | SQLite fixture | Count mismatch |
| 25 | test_v1_scorer_compatibility | CompoundingScorer.score() works with v1 write_decision | Both | Scorer + empty store | Score fails or no decision_id returned |
| 26 | test_outcome_direct_duplicate_raises | Direct write_outcome for same decision raises | Both | 1 confirmed decision | Silent ignore |
| 27 | test_outcome_replay_identical_skips | Outbox replay with matching payload skips | Both | 1 confirmed decision + outbox entry | Duplicate outcome created |
| 28 | test_outcome_replay_conflicting_errors | Outbox replay with different payload quarantines | Both | 1 confirmed decision + conflicting outbox | Silent overwrite |
| 29 | test_evidence_receipt_concurrent_append | Two concurrent appends don't fork chain | AGE | Empty chain + 2 threads | Chain fork or gap |
| 30 | test_age_transaction_rollback | Failed AGE transaction leaves no partial writes | AGE | 1 pending decision | Orphaned nodes |
| 31 | test_preview_no_decision_write | GET preview endpoint creates no Decision nodes | Both | Scored observation | count_decisions > 0 |
| 32 | test_outbox_replay_ordering | Decisions replay before outcomes | Both | Outbox with decision + outcome | Outcome references missing decision |
| 33 | test_evidence_replay_same_intent_skips | Same receipt_intent_id + same payload → skip | Both | 1 existing receipt | Duplicate receipt appended |
| 34 | test_evidence_replay_conflict_quarantines | Same receipt_intent_id + different payload → quarantine | Both | 1 existing receipt | Silent overwrite |
| 35 | test_governed_decision_conflict_quarantines | Same decision_id + different payload → quarantine | Both | 1 existing decision | Silent overwrite |
| 36 | test_evolution_event_conflict_quarantines | Same event_id + different payload → quarantine | Both | 1 existing event | Silent overwrite |
| 37 | test_outbox_quarantine_recorded | Conflicting replay creates quarantine record | Both | Outbox + existing data | No quarantine trail |

### §6b — Integration Test Matrix (Service Layer)

These tests require a running service layer (FastAPI test client + mock/live AGE), NOT the parametrized `graph_store` fixture.

| # | Test name | Behavior asserted | Fixture | Expected failure if broken |
|---|---|---|---|---|
| I1 | test_api_learn_committed | Service layer returns "committed" when AGE available | Live AGE + FastAPI client | Wrong status |
| I2 | test_api_learn_pending_sync | Service layer returns "accepted_pending_sync" when AGE down | Mock AGE failure + FastAPI client | No outbox write |
| I3 | test_pending_sync_no_V_increment | accepted_pending_sync does not increment V before replay | Outbox entry + conservation check | V increments prematurely |
| I4 | test_replay_then_V_increments | Outbox replay commits outcome, then V increments | Outbox replay + conservation | V stays at pre-replay |

**Total: 37 store-level conformance tests + 4 integration tests = 41 tests.**

---

## §7 — Refined Phase Sequence

### Phase 0: Tactical Fixes + Local-Adapter Lifecycle Precursor

**Prerequisites:** None.
**Duration:** 1-2 weeks.
**Implementation authority:** S2P PW Failures v2.4.

| Task | Details | Authority |
|---|---|---|
| Fix stale doc refs | "JM v2.4" → v2.7, "§X" → §12a | This doc |
| Fix 4: CI_DATA_DIR | One line in S2P main.py. FIRST — gates Fix 3c. | S2P PW v2.4 §7 Q4 |
| Fix 1: count_decisions() | O(1) conservation counting | S2P PW v2.4 §6 |
| Fix 3a: status column | _ensure_schema_v2() on SQLite. ALL 5 copilots. | S2P PW v2.4 §13 |
| Fix 3b: conservation V | count_verified_decisions() for V. ALL 5 copilots. | S2P PW v2.4 §13 |
| Fix 3c: S2P archive | Archive 23,607 ghost rows (explicit column INSERT). | S2P PW v2.4 §13 |
| Verify S2P PW green | workers=1 clean, workers=4 acceptable | — |

**Note:** Fix 3a/3b/3c are explicitly scoped as LOCAL-ADAPTER PRECURSORS
per GPT-5.5 guidance. They implement the Decision lifecycle on SQLite
now. Phase 2 re-validates them through Protocol v2 conformance on both
adapters. This is not redundant — Phase 0 ships the primitive, Phase 2
proves it works identically on AGE.

**Gate:** S2P reads CI_DATA_DIR. Conservation correct across all 5
copilots. S2P PW passes workers=4.
**Rollback:** Revert Fix 4 (one line). Revert Fix 3a (_ensure_schema_v2
is idempotent — column already exists, no harm).

### Phase 1: Protocol v2 Design + SOC Inventory

**Prerequisites:** Phase 0 complete.
**Duration:** 2-3 weeks. Design only — no code.

| Task | Details |
|---|---|
| Protocol v2 exact signatures | Finalize from this document §2 |
| SOC AGE schema inventory | Run §4 discovery queries, populate §4.2 table |
| Canonical vocabulary diff | Compare §5 checklist against SOC reality |
| Conformance test design | Finalize §6 matrix, write test specs |
| AGE adapter gap analysis | List which Protocol v2 methods AGEGraphStoreAdapter is missing |
| Idempotency key scheme | Confirm §3.1 format, verify no collisions |

**Gate:** Protocol v2 signed off. SOC inventory complete. Conformance
test specs written. Vocabulary reconciled. No code yet.
**Rollback:** N/A (design documents only).

### Phase 2: Conformance Implementation + Factory

**Prerequisites:** Phase 1 design complete + Fix 4 shipped.
**Duration:** 2-3 weeks.

| Task | Details |
|---|---|
| Protocol v2 implementation | Add new methods to GraphStore protocol |
| SQLite adapter updates | Add observations, evidence_receipts, conservation_snapshots tables |
| AGE adapter hardening | Fix all conformance failures |
| Conformance test suite | All 37 store-level conformance tests (§6) pass on both adapters. 4 integration tests (§6b) pass against live service layer |
| GraphStore factory | create_graph_store() function |
| Convert copilot main.py | All 4 SDK copilots use factory |
| Validate Fix 1 + Fix 3 on AGE | Lifecycle primitives shipped in Phase 0 (SQLite). Phase 2 verifies they work identically on AGE via conformance tests. |

**Gate:** All 37 store-level conformance tests pass on both adapters. All 4
service-layer integration tests pass. All copilot test suites pass. Factory
is default construction path.
**Rollback:** Revert factory to direct SQLiteGraphStore construction.
All copilots fall back to pre-factory behavior.

### Phase 3: S2P AGE Migration

**Prerequisites:** Phase 2 conformance passing. All tests green on SQLite.
**Duration:** 2-3 weeks.

| Task | Details |
|---|---|
| S2P GRAPH_BACKEND=age | Factory config + env |
| SQLite→AGE migration script | Reads S2P .db, writes canonical AGE nodes |
| Shadow comparison | Same requests, diff responses (SQLite vs AGE) |
| S2P PW on AGE | Playwright passes with GRAPH_BACKEND=age |
| Cross-copilot query | S2P↔SOC traversal works |

**Gate:** S2P tests pass on AGE. PW workers=4. Cross-copilot query correct.
**Rollback:** Set GRAPH_BACKEND=sqlite. Factory falls back. No data loss.

### Phase 4: SDK Copilots AGE Migration

**Prerequisites:** Phase 3 stable for 1 week.
**Duration:** 1-2 weeks.

| Task | Details |
|---|---|
| Trading/Purchasing/DataOps on AGE | Factory config per copilot |
| Migration scripts | SQLite→AGE per copilot |
| Demo bundles via protocol | JSON bundles restored through GraphStore |

**Gate:** All SDK tests pass on AGE. All PW tests pass.
**Rollback:** Per-copilot GRAPH_BACKEND=sqlite fallback.

### Phase 5: SOC Compatibility (if needed)

**Prerequisites:** Phase 4 complete.
**Duration:** 1-2 weeks (may be minimal if inventory found no conflicts).

| Task | Details |
|---|---|
| Compatibility views | Create views for SOC labels that differ from canonical |
| SOC route updates | Update routes or add view-based queries |
| SOC test verification | All tests pass |

**Gate:** Cross-copilot queries use one vocabulary.
**Rollback:** Remove views, SOC continues on its existing labels.

### Phase 6: Cross-Copilot Proof

**Prerequisites:** Phase 5 complete.
**Duration:** 1 week.

| Task | Details |
|---|---|
| Transfer traversal | SOC → DataOps → S2P in one Cypher |
| Global conservation | All domains in one query |
| demo.py display | All: [shared judgment graph] |

**Gate:** Every claim in JM v2.7 §2 has a working query. Pure traversal.
**Rollback:** N/A — this phase only adds queries and display, doesn't change data paths.

---

## §8 — Next Codex Tasks (High-Level Only)

### A. Doc Cleanup + Fix 4 CI_DATA_DIR

**Type:** Minimal fix + doc update.
**Repo:** s2p-copilot.
**Files:** `backend/app/main.py` (one line), repo docs (stale refs).
**Why next:** Gates everything. Zero risk.
**Must NOT:** Change conservation semantics, scoring logic, or tests.

### B. SOC AGE Schema Inventory

**Type:** Diagnostic scan (read-only).
**Repo:** soc-copilot + ci-platform (AGE instance).
**Output:** Populated table from §4.2 — SOC labels → canonical mapping.
**Why next:** Blocks canonical vocabulary finalization, which blocks
conformance tests, which blocks migration.
**Must NOT:** Change any SOC labels, create new labels, or modify AGE schema.

### C. Protocol v2 Conformance Test Design

**Type:** Test specification (no implementation yet).
**Repo:** copilot-sdk.
**Output:** Test file skeleton with all store-level test stubs from §6 (37 tests), each with
docstring describing exact assertion. Parametrized for SQLite + AGE.
**Why next:** Conformance tests are the gate for Phase 2. Design before code.
**Must NOT:** Implement Protocol v2 methods yet. Tests should initially
SKIP for methods that don't exist, marking them as Phase 2 work.

---

## §9 — What Must NOT Happen Yet

- **No AGE migration** until Phase 2 conformance passes
- **No Fix 3 lifecycle implementation** until Protocol v2 design is
  complete, unless explicitly scoped as local-adapter precursor for
  Phase 0 (the S2P PW v2.4 scope)
- **No Observation implementation** before Protocol v2 signatures final
- **No SOC schema changes** before inventory
- **No direct SQLiteGraphStore construction** after factory ships (Phase 2)
- **No product claims** based on SQLite local adapter
- **No AgentEvolver flywheel edges** from Observation nodes
- **No Decision nodes** from GET preview/read endpoints

---

## §10 — Open Questions (Require Human/Product Decision)

| # | Question | Why it matters | When to decide |
|---|---|---|---|
| 1 | ~~write_outcome duplicate behavior~~ | **DECIDED: Raise on duplicate.** One outcome per decision is a hard invariant. Conformance test #26 (test_outcome_direct_duplicate_raises) asserts this. | Resolved |
| 2 | ~~AGE archive format~~ | **DECIDED: property flag** (`Decision.archived = true`). See §2.12. | Resolved |
| 3 | Should conformance tests use shared AGE or per-test graph names? | Test isolation vs setup cost | Phase 1 |
| 4 | Outbox sync: pull (cron) or push (retry loop)? | Affects latency and resource usage. Phase 2 scope cannot be confirmed without this. | **End of Phase 1** |
| 5 | Should conservation snapshot include category-level breakdown? | Richer audit but more storage | Phase 1 |
| 6 | Observation → Decision promotion: API endpoint or manual? | Affects preview→action workflow | Phase 3+ |

---

**READY_FOR_5_5_REVIEW:** YES

**SUMMARY:**
- Protocol v2: 15 method surfaces (14 governed methods + v1 write_decision compatibility) with exact signatures, return types, idempotency keys, transaction semantics, and per-adapter behavior
- Idempotency: three operation classes (must-survive with payload-hash, recomputable with upsert, disposable with INSERT OR IGNORE); outbox with quarantine for conflicts
- SOC inventory: discovery queries provided; output table templated; blocks canonical vocabulary
- Conformance: 37 store + 4 integration = 41 tests, parametrized SQLite+AGE, every test has expected failure mode
- Phases: 7 phases with prerequisites, gates, and rollback strategies
- Next Codex: (A) Fix 4 + doc cleanup, (B) SOC inventory, (C) conformance test design
- 6 open questions identified for Phase 1/2 decisions

**REMAINING_AGE_MIGRATION_GAPS:**
- SOC schema inventory not done (Phase 1)
- Protocol v2 methods not implemented (Phase 2)
- AGE adapter conformance untested (Phase 2)
- GraphStore factory not built (Phase 2)
- Outbox sync mechanism not implemented (Phase 2)
- Migration scripts not written (Phase 3)

**DOCUMENTS_TO_UPDATE:**
- `docs/judgment_memory_v2_7.md` — minor: fix stale "§X" refs, add link to this Protocol v2 doc
- `docs/protocol_v2_design_v1_8.md` — THIS document (new, commit to repo)
- `docs/s2p_pw_failures_v2_4.md` — no changes needed

---

*GraphStore Protocol v2 — Implementation Design v1.8*
*May 31, 2026*
*15 methods (14 + v1 compat). 37 store + 4 integration = 41 tests. 7 phases with gates.*
*"This document specifies HOW. JM v2.7 specifies WHAT and WHY."*
