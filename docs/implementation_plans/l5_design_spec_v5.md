# L5 Design Spec: Judgment Memory Graph Nodes
**Date:** June 1, 2026
**Authority:** JM v2.7 §4.1-4.3 + Protocol v2 v1.8
**Scope:** Centroid, DKWeight, ConservationState as AGE nodes
**Prerequisites:** L3 complete (all 5 apps write Decisions/Outcomes),
L4 complete (EvidenceReceipt, Observation, outbox, conformance tests)

---

## 0. Design Principles

1. **AGE is canonical persistence; in-memory is cache.** On startup,
   read from AGE to populate cache. On update, the accepted state
   transition is:
   (a) compute candidate update in-memory (do NOT expose to callers yet);
   (b) persist to AGE or durable outbox (MUST succeed before proceeding);
   (c) update in-memory cache and expose success to caller.
   If AGE is unavailable, write to durable outbox — do NOT silently
   advance only in memory. This ensures no state is "accepted" without
   a durable record.

2. **Decision identity is (domain, decision_id).** All Cypher that
   references a Decision uses `{domain: ..., decision_id: ...}` —
   never bare `{id: ...}`. This matches Protocol v2 conventions and
   app-specific ID formats (S2P-*, PUR-*, TRD-*, etc.).

3. **Every graph write has a causal Decision.** Centroid updates,
   DK weight changes, and conservation state transitions are CAUSED BY
   specific verified Decisions. The edge from the node to the causing
   Decision is mandatory — it is the audit chain.

4. **Flat properties only.** AGE stores properties as scalar key-value
   pairs. Vectors (centroid, DK weights) are stored as JSON strings
   and deserialized on read.

5. **Domain isolation.** Each domain (SOC, S2P, Trading, Purchasing,
   DataOps) has its own Centroid/DKWeight/ConservationState nodes.
   Cross-domain queries are explicit and guarded.

6. **Option C integrated.** ConservationState uses α = cumulative
   coverage (D1). Complacency is advisory, not gating.

---

## 1. Node Schemas

**AGE Cypher compatibility note:** Apache AGE prohibits MERGE, ON CREATE
SET, and ON MATCH SET. The `_check_safe_cypher()` guard in AGEClient
enforces this. All Cypher shown below is in **implementation pseudocode**
using MERGE for clarity. The implementer MUST translate every MERGE to
the two-step AGE-compatible pattern:

```python
# Step 1: Try to read existing
result = age_client.query(
    "MATCH (c:Centroid {domain: _S(domain), category: _S(cat), action: _S(act)}) "
    "RETURN c.id"
)
# Step 2a: If exists → SET
if result:
    age_client.query(
        "MATCH (c:Centroid {domain: _S(domain), ...}) "
        "SET c.vector_json = _S(vec), c.count = _S(cnt), c.updated_at = _S(now)"
    )
# Step 2b: If not exists → CREATE
else:
    age_client.query(
        "CREATE (c:Centroid {domain: _S(domain), ..., vector_json: _S(vec), ...})"
    )
```

All `$param` syntax below is pseudocode — use `_S()` inline serialization
per AGEClient conventions. All string literals in Cypher use single
quotes (AGE requirement). The read-then-write-or-create logic lives in
Python (GraphStore methods), not in Cypher.

### 1.1 Centroid

Represents the per-category, per-action learned centroid vector.
One Centroid node per (domain, category, action) triple.

```
Label: Centroid
Properties:
  id:            TEXT  (UUID, primary key)
  domain:        TEXT  (e.g., "soc", "s2p", "trading")
  category:      TEXT  (e.g., "account_takeover", "invoice_match")
  action:        TEXT  (e.g., "escalate", "approve", "flag")
  vector_json:   TEXT  (JSON array of d floats — the centroid vector)
  d:             INT   (dimensionality — number of factors)
  count:         INT   (number of verified decisions that shaped this centroid)
  eta_last:      REAL  (learning rate of most recent update — 0.05 or 0.01)
  created_at:    TEXT  (ISO 8601)
  updated_at:    TEXT  (ISO 8601)

Uniqueness: (domain, category, action) — exactly one Centroid per triple.

Example (SOC, canonical tensor (6,4,6) — 6 factors):
  domain = "soc"
  category = "account_takeover"
  action = "escalate"
  vector_json = "[0.483, 0.424, 0.451, 0.064, 0.010, 0.312]"
  d = 6
  count = 342
```

**Edges FROM Centroid:**

| Edge type | Target | Properties | Meaning |
|---|---|---|---|
| `SHAPED_BY` | Decision | eta (REAL), delta_norm (REAL), timestamp (TEXT) | "This Decision caused a centroid update" |

**Cardinality:** Each Centroid has 0..N SHAPED_BY edges (one per verified
decision in its category/action). Each Decision has 0..1 incoming
SHAPED_BY from a Centroid (one centroid per decision). However, a single
verified Decision may affect up to 3 node types: one SHAPED_BY edge
(from Centroid), contribution to one DKWeight (via aggregate counts),
and one TRIGGERED_BY edge (from ConservationState if status transitions).
The implementer must handle all three in the learn flow.

**Write operation — `update_centroid()`:**

```python
def update_centroid(
    self,
    domain: str,
    category: str,
    action: str,
    new_vector: list[float],
    count: int,
    eta: float,
    caused_by_decision_id: str,
    delta_norm: float,
) -> str:
    """
    MERGE centroid node. Update vector + count. Create SHAPED_BY edge.
    Returns centroid node id.
    Raises on AGE failure (caller retries or surfaces error).
    """
```

**Cypher:**

```cypher
-- MERGE centroid (create if not exists, update if exists)
MERGE (c:Centroid {domain: $domain, category: $category, action: $action})
ON CREATE SET
  c.id = $id,
  c.vector_json = $vector_json,
  c.d = $d,
  c.count = $count,
  c.eta_last = $eta,
  c.created_at = $now,
  c.updated_at = $now
ON MATCH SET
  c.vector_json = $vector_json,
  c.count = $count,
  c.eta_last = $eta,
  c.updated_at = $now

-- Link to causing Decision
MATCH (c:Centroid {domain: $domain, category: $category, action: $action})
MATCH (d:Decision {domain: $domain, decision_id: $decision_id})
CREATE (c)-[:SHAPED_BY {eta: $eta, delta_norm: $delta_norm, timestamp: $now}]->(d)
```

**Read operation — `get_centroid()`:**

```cypher
MATCH (c:Centroid {domain: $domain, category: $category, action: $action})
RETURN c.vector_json, c.count, c.updated_at
```

**Batch read — `get_all_centroids(domain)`:**

```cypher
MATCH (c:Centroid {domain: $domain})
RETURN c.category, c.action, c.vector_json, c.count
ORDER BY c.category, c.action
```

**Storage math:** SOC (C=6, A=4, d=6): 24 Centroid nodes, each with a
6-element vector. Total: 144 float values + 24 nodes. At 500 verified
decisions: ~500 SHAPED_BY edges. Negligible storage.

---

### 1.2 DKWeight

Represents the DiagonalKernel precision weights for a domain
(or per-entity, for L6 E-JM-7 style interactions).

```
Label: DKWeight
Properties:
  id:              TEXT  (UUID)
  domain:          TEXT
  entity_group:    TEXT  (NULL for global weights, entity name for per-entity)
  weight_json:     TEXT  (JSON array of d floats — precision weights, sum to 1.0)
  d:               INT
  n_confirmed:     INT   (total confirmed decisions used in estimation)
  n_overridden:    INT   (total overridden decisions used in estimation)
  mechanism:       TEXT  ("inverse_variance_discriminability")
  confirmed_mean_json:   TEXT  (JSON array — Welford running mean, confirmed)
  confirmed_m2_json:     TEXT  (JSON array — Welford M2, confirmed)
  overridden_mean_json:  TEXT  (JSON array — Welford running mean, overridden)
  overridden_m2_json:    TEXT  (JSON array — Welford M2, overridden)
  all_mean_json:         TEXT  (JSON array — Welford running mean, all verified)
  all_m2_json:           TEXT  (JSON array — Welford M2, all verified)
  created_at:      TEXT
  updated_at:      TEXT

Welford fields are REQUIRED for L5 conformance (audit chain).
Without them, the weight vector is opaque and unreproducible.

Uniqueness: (domain, entity_group) — one DKWeight per domain (global)
or per (domain, entity_group) pair (per-entity, L6).
entity_group = NULL or "" for global.
```

**Edges FROM DKWeight:**

| Edge type | Target | Properties | Meaning |
|---|---|---|---|
| `ESTIMATED_FROM` | Decision | contribution (REAL) | *DEFERRED (O(V)). Welford state serves as audit chain instead.* |
| `SUPERSEDES` | DKWeight | timestamp (TEXT) | *DEFERRED to L6. DKWeight versioning via snapshot properties for L5.* |

**Write operation — `update_dk_weights()`:**

```python
def update_dk_weights(
    self,
    domain: str,
    new_weights: list[float],
    n_confirmed: int,
    n_overridden: int,
    welford_state: dict,  # {confirmed_mean, confirmed_m2,
                          #  overridden_mean, overridden_m2,
                          #  all_mean, all_m2} — each list[float]
    entity_group: str | None = None,
) -> str:
    """
    Create or update DKWeight node. Stores weights + counts +
    Welford accumulators (required for audit chain).
    Does NOT create per-decision edges (deferred, O(V)).
    Returns DKWeight node id.
    """
```

**Cypher:**

```cypher
MERGE (w:DKWeight {domain: $domain, entity_group: COALESCE($entity_group, "")})
ON CREATE SET
  w.id = $id,
  w.weight_json = $weight_json,
  w.d = $d,
  w.n_confirmed = $n_confirmed,
  w.n_overridden = $n_overridden,
  w.mechanism = "inverse_variance_discriminability",
  w.created_at = $now,
  w.updated_at = $now
ON MATCH SET
  w.weight_json = $weight_json,
  w.n_confirmed = $n_confirmed,
  w.n_overridden = $n_overridden,
  w.updated_at = $now
```

**Note on ESTIMATED_FROM edges:** Creating an edge per Decision is O(V)
and impractical at scale. Instead, DKWeight stores aggregate counts
(n_confirmed, n_overridden) and the weight vector. The causal chain is
implicit: DKWeight was estimated from the Decisions in the domain. For
audit, the Welford accumulators (mean, M2) are stored as canonical
properties in the DKWeight schema above.

ESTIMATED_FROM edges (DKWeight → Decision) are **deferred** as O(V).
The Welford accumulators in the canonical schema above serve as the
audit chain instead. Per-decision edges are optional/future.

---

### 1.3 ConservationState

Represents the current conservation status for a domain.

```
Label: ConservationState
Properties:
  id:                TEXT  (UUID)
  domain:            TEXT
  status:            TEXT  ("GREEN", "AMBER", "RED")
  alpha:             REAL  (cumulative category coverage = c_d/C)
  q:                 REAL  (rolling verified accuracy over q_window)
  V:                 INT   (cumulative verified decision count)
  q_window:          INT   (window size, canonical = 400 — snapshot at write time)
  theta_min:         REAL  (computed: 23.53 / (alpha * V))
  product:           REAL  (computed: alpha * q * V)
  categories_total:  INT   (C — snapshot at write time, not live reference)
  categories_with_data: INT (c_d)
  baseline_product:  REAL  (rolling baseline for relative trigger)
  relative_threshold: REAL (0.7 × baseline — the steady-state protector)
  complacency_flag:  TEXT  ('true'/'false' — AGE boolean serialization varies by helper; use TEXT and normalize on read)
  last_checked:      TEXT
  last_status_change: TEXT
  created_at:        TEXT
  updated_at:        TEXT

Uniqueness: (domain) — exactly one ConservationState per domain.
```

**Edges FROM ConservationState:**

| Edge type | Target | Properties | Meaning |
|---|---|---|---|
| `TRIGGERED_BY` | Decision | old_status (TEXT), new_status (TEXT), timestamp (TEXT) | "This Decision caused a status transition" |
| `MONITORS` | *(deferred — DomainConfig node not in L5 scope)* | — | *Deferred to L6. categories_total stored as snapshot property on ConservationState instead.* |

**Write operation — `update_conservation_state()`:**

```python
def update_conservation_state(
    self,
    domain: str,
    status: str,       # GREEN/AMBER/RED
    alpha: float,      # cumulative coverage
    q: float,          # rolling accuracy
    V: int,            # verified count
    theta_min: float,  # computed threshold
    product: float,    # alpha * q * V
    baseline_product: float,
    complacency_flag: bool,
    triggered_by_decision_id: str | None = None,
    old_status: str | None = None,
) -> str:
    """
    MERGE ConservationState node. Update all metrics.
    If status changed, create TRIGGERED_BY edge to the causing Decision.
    """
```

**Cypher — update:**

```cypher
MERGE (cs:ConservationState {domain: $domain})
ON CREATE SET
  cs.id = $id,
  cs.status = $status,
  cs.alpha = $alpha,
  cs.q = $q,
  cs.V = $V,
  cs.q_window = $q_window,
  cs.theta_min = $theta_min,
  cs.product = $product,
  cs.categories_total = $C,
  cs.categories_with_data = $c_d,
  cs.baseline_product = $baseline,
  cs.relative_threshold = $rel_threshold,
  cs.complacency_flag = $complacency,
  cs.last_checked = $now,
  cs.last_status_change = $now,
  cs.created_at = $now,
  cs.updated_at = $now
ON MATCH SET
  cs.status = $status,
  cs.alpha = $alpha,
  cs.q = $q,
  cs.V = $V,
  cs.theta_min = $theta_min,
  cs.product = $product,
  cs.categories_with_data = $c_d,
  cs.baseline_product = $baseline,
  cs.relative_threshold = $rel_threshold,
  cs.complacency_flag = $complacency,
  cs.last_checked = $now,
  cs.updated_at = $now
```

**Cypher — status transition edge:**

```cypher
MATCH (cs:ConservationState {domain: $domain})
MATCH (d:Decision {domain: $domain, decision_id: $decision_id})
CREATE (cs)-[:TRIGGERED_BY {
  old_status: $old_status,
  new_status: $new_status,
  timestamp: $now
}]->(d)
SET cs.last_status_change = $now
```

---

## 2. Integration Points — Where Writes Happen

### 2.1 Score/Learn Flow (all copilots)

The current flow (simplified):

```
1. POST /score → create pending Decision → return score
2. POST /learn (or /outcome) → verify Decision (confirm/override)
   → update centroid (in-memory)
   → update DK weights (in-memory)
   → check conservation (in-memory)
   → return result
```

The L5 flow adds AGE writes after each in-memory update:

```
1. POST /score → create pending Decision → write Decision to AGE → return score
2. POST /learn (or /outcome):
   Step 1: verify Decision → write Outcome to AGE (status → confirmed/overridden)
   Step 2: recompute conservation in-memory (V, q, alpha, theta_min, product)
           — this MUST happen before centroid/DK/conservation AGE writes
           — determines whether conservation status transitions
   Step 3: compute centroid candidate → persist Centroid + SHAPED_BY to AGE/outbox → update cache
   Step 4: compute DK weight candidate → persist DKWeight to AGE/outbox → update cache
   Step 5: persist ConservationState + TRIGGERED_BY (if changed) to AGE/outbox → update cache
   Step 6: return result
```

### 2.2 AGE Write Ordering (within a single learn/outcome call)

```
Step 1: write_outcome()                    — Decision status → confirmed/overridden
Step 2: recompute_conservation_in_memory() — V, q, alpha, theta_min, product, status
                                            (determines whether Step 5 creates edge)
Step 3: persist_centroid()                 — compute candidate → AGE/outbox → cache
Step 4: persist_dk_weights()               — compute candidate → AGE/outbox → cache
Step 5: persist_conservation_state()       — compute candidate → AGE/outbox → cache + TRIGGERED_BY if changed
```

**Transaction strategy for L5 learn/outcome writes:**

The 5 steps (outcome, centroid, dk_weights, conservation_state,
edges) use a **durable outbox with idempotent replay**:

1. Compute all candidate updates in memory.
2. Write all 5 operations as outbox entries (status=pending) in a
   SINGLE local transaction (SQLite or PostgreSQL — the outbox is
   local, not in AGE).
3. Replay outbox entries to AGE. Each entry is idempotent:
   - Centroid/DKWeight/ConservationState: Class B (recomputable, upsert)
   - SHAPED_BY/TRIGGERED_BY edges: Class A (must-survive, payload-hash)
4. Mark outbox entries as replayed on success.
5. On partial AGE failure: remaining entries stay pending for retry.
   Graph may be temporarily incomplete but never inconsistent (each
   entry is independently idempotent).
6. Update in-memory cache only after outbox write succeeds (step 2).

**Minimal durable outbox schema:**

```
outbox_id:            INTEGER  (auto-increment primary key)
domain:               TEXT
operation_type:       TEXT     (centroid/dk_weight/conservation_state/shaped_by/triggered_by)
target_key:           TEXT     (e.g., "soc:account_takeover:escalate" for centroid)
payload_json:         TEXT     (full node properties as JSON)
payload_hash:         TEXT     (SHA-256 of payload_json — for idempotency)
causal_decision_id:   TEXT     (domain:decision_id of the causing decision)
status:               TEXT     (pending/replayed/failed/quarantined)
attempt_count:        INTEGER  (default 0)
last_error_redacted:  TEXT     (nullable — error message without secrets)
schema_version:       INTEGER  (outbox schema version for forward compat)
created_at:           TEXT     (ISO 8601)
updated_at:           TEXT
replayed_at:          TEXT     (nullable — set on successful replay)

UNIQUE(operation_type, target_key, payload_hash)
```

Replay idempotency: operation_type + target_key + payload_hash.
Conflicts (same operation+key, different hash) quarantine rather
than overwrite — supervisor must review.

This avoids requiring AGE multi-statement transactions (which AGE
does not reliably support) while ensuring no state is lost.

### 2.3 AGE Read on Startup

On copilot startup (or scorer initialization):

```
1. Read all Centroids for domain → populate ProfileScorer.centroids
2. Read DKWeight for domain → populate ProfileScorer.dk_weights
3. Read ConservationState for domain → populate LearningHealthMonitor
4. If AGE unavailable → fall back to SQLite (L3 rollback path)
```

### 2.4 File Locations (per copilot)

| Copilot | Score/learn flow | Centroid update | DK update | Conservation | Startup read |
|---|---|---|---|---|---|
| SOC | `soc-copilot/services/triage.py` | `gae/profile_scorer.py` | `gae/profile_scorer.py` | `soc-copilot/services/learning_health.py` | `soc-copilot/services/startup.py` |
| S2P | `s2p-copilot/backend/app/routers/s2p.py` | `copilot_sdk/scoring/scorer.py` | `copilot_sdk/scoring/scorer.py` | `copilot_sdk/backend/conservation_router.py` | `s2p-copilot/backend/app/main.py` |
| Trading | `copilot-sdk/apps/trading/.../main.py` | `copilot_sdk/scoring/scorer.py` | `copilot_sdk/scoring/scorer.py` | `copilot_sdk/backend/conservation_router.py` | same |
| Purchasing | `copilot-sdk/apps/purchasing/.../main.py` | `copilot_sdk/scoring/scorer.py` | `copilot_sdk/scoring/scorer.py` | `copilot_sdk/backend/conservation_router.py` | same |
| DataOps | `copilot-sdk/apps/dataops/.../main.py` | `copilot_sdk/scoring/scorer.py` | `copilot_sdk/scoring/scorer.py` | `copilot_sdk/backend/conservation_router.py` | same |

---

## 3. GraphStore Interface Extensions

Protocol v2 v1.8 defines the narrow GraphStore protocol. L5 operations
are defined as a **separate extension protocol** to avoid breaking
minimal GraphStore implementations:

```python
class L5LearningStore(Protocol):
    """Extension protocol for judgment memory persistence.
    Implementations: AGELearningStore, SQLiteLearningStore.
    Minimal GraphStore (InMemoryStore, test fakes) need NOT implement this.
    """


    # Centroid operations
    def update_centroid(
        self, domain: str, category: str, action: str,
        vector: list[float], count: int, eta: float,
        caused_by_decision_id: str, delta_norm: float,
    ) -> str: ...

    def get_centroids(self, domain: str) -> list[CentroidRecord]: ...

    # DKWeight operations
    def update_dk_weights(
        self, domain: str, weights: list[float],
        n_confirmed: int, n_overridden: int,
        welford_state: dict,  # required for audit chain
        entity_group: str | None = None,
    ) -> str: ...

    def get_dk_weights(self, domain: str,
                       entity_group: str | None = None) -> DKWeightRecord | None: ...

    # ConservationState operations
    def update_conservation_state(
        self, domain: str, status: str, alpha: float,
        q: float, V: int, theta_min: float, product: float,
        baseline_product: float, complacency_flag: bool,
        triggered_by_decision_id: str | None = None,
        old_status: str | None = None,
    ) -> str: ...

    def get_conservation_state(self, domain: str) -> ConservationStateRecord | None: ...
```

**Return types:**

```python
@dataclass
class CentroidRecord:
    domain: str
    category: str
    action: str
    vector: list[float]
    count: int
    updated_at: str

@dataclass
class DKWeightRecord:
    domain: str
    entity_group: str | None
    weights: list[float]
    n_confirmed: int
    n_overridden: int
    mechanism: str
    updated_at: str

@dataclass
class ConservationStateRecord:
    domain: str
    status: str  # GREEN/AMBER/RED
    alpha: float
    q: float
    V: int
    theta_min: float
    product: float
    baseline_product: float
    complacency_flag: bool
    updated_at: str
```

---

## 4. Conformance Tests (L5 additions)

Adding to the 37 store + 4 integration = 41 from Protocol v2 v1.8:

| # | Test | What it proves |
|---|---|---|
| 42 | `test_update_centroid_creates_node` | Creates Centroid node with correct properties |
| 43 | `test_update_centroid_idempotent` | Same (domain, category, action) → updates, not duplicates |
| 44 | `test_update_centroid_creates_shaped_by_edge` | SHAPED_BY edge links Centroid to causing Decision |
| 45 | `test_get_centroids_returns_all_for_domain` | Batch read returns C×A centroids |
| 46 | `test_get_centroids_domain_isolation` | Domain X centroids not returned for domain Y query |
| 47 | `test_update_dk_weights_creates_node` | Creates DKWeight node with correct properties + Welford state |
| 48 | `test_update_dk_weights_idempotent` | Same domain → updates, not duplicates |
| 49 | `test_dk_weights_entity_group_isolation` | Per-entity weights separate from global |
| 50 | `test_get_dk_weights_returns_correct` | Read-back matches write |
| 51 | `test_update_conservation_creates_node` | Creates ConservationState node with correct properties |
| 52 | `test_conservation_status_transition_edge` | GREEN→AMBER creates TRIGGERED_BY edge to Decision |
| 53 | `test_conservation_no_edge_on_same_status` | GREEN→GREEN does NOT create edge |
| 54 | `test_conservation_alpha_is_cumulative_coverage` | α = c_d/C, monotone |
| 55 | `test_conservation_complacency_is_advisory` | complacency_flag does NOT affect status |
| 56 | `test_get_conservation_state` | Read-back matches write |
| 57 | `test_centroid_survives_rollback` | Centroid in AGE persists after rollback. Rollback path reads AGE first; falls back to SQLite only if READ fails (not if write fails). |
| 58 | `test_dk_welford_enables_recomputation` | Given stored Welford state (means + M2), recompute weight vector and verify it matches weight_json |
| 59 | `test_full_learn_flow_writes_all_three` | Single learn/outcome call writes Centroid + DKWeight + ConservationState. MUST verify SHAPED_BY and TRIGGERED_BY edges exist, not just nodes. |

**Minimum L5 additions: 18 conformance tests.** Total depends on
current L4 count (verify against actual test files before asserting
a specific total).

---

## 5. Cross-Type Queries Enabled by L5

These are the queries that become possible ONLY with L5 nodes in the
graph (centroids, DK weights, conservation alongside decisions):

### Q1: "What shaped this centroid?"
```cypher
MATCH (c:Centroid {domain: "soc", category: "account_takeover", action: "escalate"})
      -[:SHAPED_BY]->(d:Decision)
RETURN d.decision_id, d.status, d.factor_vector_json, d.created_at
ORDER BY d.created_at DESC
LIMIT 20
```

### Q2: "Which factor's DK weight is highest?"
```cypher
MATCH (w:DKWeight {domain: "soc", entity_group: ""})
RETURN w.weight_json, w.n_confirmed, w.n_overridden, w.updated_at
```

### Q3: "When did conservation status last change, and why?"
```cypher
MATCH (cs:ConservationState {domain: "soc"})
      -[t:TRIGGERED_BY]->(d:Decision)
RETURN t.old_status, t.new_status, t.timestamp, d.decision_id, d.status
ORDER BY t.timestamp DESC
LIMIT 5
```

### Q4: "Transfer SOC's DK weights to S2P" (L6, but enabled by L5)
```cypher
MATCH (w:DKWeight {domain: "soc", entity_group: ""})
RETURN w.weight_json, w.mechanism
-- Then: create TransferPattern node + write to S2P domain
```

### Q5: "Cross-copilot conservation dashboard"
```cypher
MATCH (cs:ConservationState)
RETURN cs.domain, cs.status, cs.alpha, cs.q, cs.V, cs.product, cs.complacency_flag
ORDER BY cs.domain
```

---

## 6. Failure Policy (L5 nodes)

| Operation | On AGE failure | Fallback | Data loss? |
|---|---|---|---|
| update_centroid | AGE write fails | If outbox write succeeds: candidate accepted (status=outbox_pending), cache updated, replay queued. If BOTH AGE and outbox fail: RAISE, cache NOT updated, no state accepted. | No if outbox succeeds; yes if both fail |
| update_dk_weights | AGE write fails | Same as centroid: outbox captures → cache accepted. Both fail → raise. | Same |
| update_conservation_state | AGE write fails | Same pattern. TRIGGERED_BY edge queued in outbox for replay. | Same |
| get_centroids (startup) | AGE read fails | Fall back to SQLite centroids or cold-start zeros. Status must indicate source=degraded/stale. | Yes (stale data, flagged) |
| get_dk_weights (startup) | AGE read fails | Fall back to uniform weights (domain prior). Status=degraded. | Yes (stale, flagged) |
| get_conservation_state (startup) | AGE read fails | Start as GREEN with V=0. Status=degraded. | Yes (conservative default, flagged) |

**Consistency model:** Compute in memory, persist to AGE or durable
outbox, then update cache. If AGE is unavailable, the outbox captures
the write for replay. The system does NOT advance in-memory-only without
a durable record — this prevents silent state loss on restart. Scoring
continues using the last-known cached state until the outbox replays.

---

## 7. Option C Integration

ConservationState.alpha is computed as:

```python
alpha = len(categories_with_any_verified_decision) / total_categories
```

Where:
- `categories_with_any_verified_decision` = cumulative count of unique
  categories that have EVER had a verified Decision (confirmed or
  overridden). Monotone — can only grow.
- `total_categories` = C from app configuration (fixed per domain,
  e.g., `domain_config.n_categories` in Python). Not from an AGE node.

This is read from the graph on startup:

```cypher
MATCH (d:Decision {domain: $domain})
WHERE d.status IN ['confirmed', 'overridden']
RETURN COUNT(DISTINCT d.category) AS c_d
```

C (total categories) is read from app domain configuration at
computation time (e.g., `domain_config.n_categories` in Python).
No DomainConfig AGE node is required for L5. C is stored as
`ConservationState.categories_total` (snapshot at write time).

α = c_d / C. Stored in ConservationState.alpha on each update.

Complacency flag: computed in-memory from the rolling override rate.
Stored as ConservationState.complacency_flag (TEXT: 'true'/'false').
Does NOT affect
ConservationState.status (GREEN/AMBER/RED).

---

*L5 Design Spec v5.0 · June 1, 2026*
*3 node types · 6 new L5LearningStore operations · 18 new conformance tests*
*Minimum 18 new L5 conformance tests (total depends on current L4 count)*
*v2: AGE MERGE→two-step, Welford required, write ordering explicit, edge assertions added*
*v3: consistency model, outbox strategy, L5LearningStore, Welford canonical, Decision identity*
*v4: failure policy, DomainConfig removed, write ordering, outbox schema, d.decision_id, BOOL→TEXT*
*v5: Welford stale language fixed, DomainConfig ref in §7 fixed, complacency TEXT in §7,*
*update_dk_weights signature includes welford_state, ESTIMATED_FROM/SUPERSEDES deferred,*
*test descriptions MERGE-free, footer matches body on test count*
