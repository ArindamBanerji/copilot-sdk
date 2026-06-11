# DK Runtime Execution Plan v5.4 — 5 Prompts to Full Intelligence Loop
**Date:** June 6, 2026
**Priority:** P1 — execute BEFORE all other roadmap items
**Goal:** All SDK copilots compute, persist, and score with learned DK weights
**Timeline:** ~5-6 working days
**Authority:** dk_runtime_fix_architecture_v3.md + p_welford_architecture_decision.md
**Scan status:** Prompt 0 discovery scan COMPLETE. All GAE parameters confirmed.

---

## Why This Runs First

DK runtime is the P1 gap that makes or breaks the product's core claims.
Without it, "compounding intelligence" is aspirational for 5 of 5
copilots. Every other roadmap item (migration, SOC Option C, demo build,
blog publish, arxiv submission) is LESS urgent than making the
intelligence loop actually run. Those items improve a working product;
this item makes the product work.

**Everything else waits until these 5 prompts are done.**

---

## Prerequisites (verify BEFORE Prompt 0)

DK estimation reads verified decisions. If ghost decisions contaminate
the verified pool, DK learns from garbage.

| Prerequisite | MAP# | Status | Verify |
|---|---|---|---|
| **CONS-V-FIX** (V = verified only) | #111 | Must be SHIPPED | `curl http://localhost:8010/api/conservation/status` — total_decisions should match verified count, not inflated by ghosts |
| **OBSERVATION-WIRING** (preview → write_observation) | #115 | Must be SHIPPED | `grep -rn "write_observation" copilot-sdk/` shows preview using observation path |
| **BUNDLE-REGEN** (Trading d=10 bundle) | #102 | Must be SHIPPED | Trading cold-start produces d=10 centroids |
| **GAE editable install** | — | ✅ DONE | `pip install -e ../graph-attention-engine-v50` verified — GAE imports from copilot-sdk |

**If ANY prerequisite is not shipped, fix it BEFORE starting Prompt 0.**
DK estimation on ghost-polluted data produces wrong weights — the
intelligence loop would "learn" from noise, which is worse than static priors.

---

## Architectural Review Synopsis

Six review passes shaped this plan. This synopsis captures the key
decisions and their rationale so the coding session understands WHY,
not just WHAT.

### Review 1 — GPT feedback (6 points, all accepted)

**1. Split Prompt 2 into 2a/2b/2c with behavioral gate.** The original
plan had a 3-4d monolith. If Part A (construction change) is subtly
wrong, Parts B-E build persistence and routing on a broken foundation.
Fix: 2a ships the construction + behavioral gate (G1+G2). Only after
G1+G2 pass does 2b (persistence) and 2c (routing) proceed.

**2. Behavioral acceptance test is THE gate, not item 12 in a list.**
All storage tests can pass and the system still not learn — e.g.,
`reestimate_dk()` runs but returns near-prior weights, or weights
compute but `score()` never consumes them. G1 proves the intelligence
loop WORKS: feed a noisy factor, verify its weight drops, verify
scoring shifts. G2 proves shrinkage: at low N weights stay near prior,
at high N they diverge. These are the "pipeline runs" vs "intelligence
works" distinction.

**3. Ghost-fix prerequisite.** DK estimation reads verified decisions.
If #111 CONS-V-FIX and #115 OBSERVATION-WIRING haven't shipped,
ghost decisions contaminate the verified pool and DK learns from
garbage. These prerequisites must be verified BEFORE Prompt 0.

**4. Low-N shrinkage is built into GAE.** `FixedAlpha(0.5)` = 50%
prior + 50% data. This IS the "graduating from domain prior to
firm-specific" mechanism the blog claims. No James-Stein needed —
GAE already has it. The graduation is continuous, not a threshold.

**5. GAE as editable install, not sys.path.insert.** `pip install -e`
makes GAE a proper importable package. Brittle path hacks break test
suites and don't align with the open-source plan.

**6. C9 gates everything, not just the roadmap.** The blog publish
gate was "Option C only." Wrong — C9 (L5 COMPLETE) is what makes the
288-moat and Mirror TRUE. A buyer who deploys before C9 and inspects
DK weights sees the domain prior. Gate: C9 + #132 for blog/arxiv.
C9 + #132 + demo build for LOOM-V1.

### Review 2 — No-hack architectural audit (3 findings)

**Finding 1 (SIGNIFICANT): Option B (external DK bridge) was a hack.**
The original plan created a `dk_bridge.py` that ran
`CoordinateDescentEstimator` independently, injected `_dk_weights`
via private attribute assignment, and read from GraphStore instead of
the scorer's decision buffer. Three red flags: parallel computation
path, monkey-patching, different data source. Fix: Option A — change
`from_preset()` to construct ProfileScorer with full LearningStrategy.
The scorer calls its own `reestimate_dk()` through its designed API.
Persistence layer READS from the scorer, doesn't compute.

**Finding 2 (resolved): Why not split persist-only (Phase 1.5) and
activate (Phase 2)?** Three reasons the split was wrong:
- "Don't change scoring" is circular — the conservation gate exists
  precisely to catch accuracy degradation from DK activation
- "Observe before trusting" is waste — DK weights in L5 that nobody
  reads have zero commercial value
- "Conservation should be GREEN first" is backwards — conservation
  should monitor DK-weighted accuracy from day one, not switch later
  with no baseline

Combined: compute + persist + activate in one step. Conservation
monitors DK-weighted accuracy as the safety net.

**Finding 3 (resolved): No "minimal" LearningStrategy.** Use the FULL
strategy from `for_soc_twophase()`: `DecisionCountPolicy(n=200)`,
`CoordinateDescentEstimator()`, `FixedAlpha(0.5)`, `eta_override=0.01`,
`auto_pause_on_amber=True`. These are the designed parameters. The
product is a compounding intelligence system — the learning strategy
should be full, not minimal.

### Review 3 — Phase-aware centroid writes (1 significant finding)

**Centroid L5 writes must be conditional on MEAN_CONVERGENCE phase.**
When a category enters VARIANCE_LEARNING (after 200 decisions),
`ProfileScorer.update()` freezes the centroid and buffers decisions
for DK estimation instead. Writing an L5 centroid node with a
SHAPED_BY edge for a frozen centroid is false provenance — it claims
"this decision shaped this centroid" when the centroid didn't move.

Fix: `_persist_centroid_l5()` checks `get_category_phase(category)`.
If VARIANCE_LEARNING: skip centroid write (DK write fires instead).
If MEAN_CONVERGENCE: write centroid with SHAPED_BY edge (truthful).

This aligns with GAE's designed two-phase architecture:
- Phase 1 (MEAN_CONVERGENCE): centroid learning active, L5 centroid writes active
- Phase 2 (VARIANCE_LEARNING): DK learning active, L5 DK writes active
- Both phases: conservation L5 writes always active

### Review 4 — P27 centroid sequencing conflict (1 finding)

**P-CENTROID-L5-WIRE was listed after C9 but required before P27.**
The original plan said "centroids work via checkpoints — L5 adds
auditability, lower priority." But P27's gate is "all three L5 node
types." Without centroid L5 writes, P27 verifies 2 of 3 — which fails
the gate dishonestly. Codex correctly stopped P27 and escalated.

Fix: P-CENTROID-L5-WIRE moved to Prompt 3b (before P27). The wiring
is in `scoring_router.py` (consistent with DK and conservation L5
writes — all three in the router layer). `save_centroids()` checkpoint
behavior is unchanged — L5 centroid write is ADDITIVE. S2P covered by
the same pattern in its outcome handler.

**Key distinction:** `save_centroids()` = full tensor checkpoint for
scorer restore. `update_centroid()` = per-(category, action) L5 node
with SHAPED_BY edge for audit. Both serve different purposes. Both
coexist.

### Review 5 — C9 live AGE blockers (8 issues, 3 code fixes)

**C9 live AGE proof attempted after P27 passed. Five code/config
issues and three accepted gaps found.**

**Issue A — Conservation domain bug (CODE FIX).** Live AGE seeding
produced 200+ verified decisions per copilot, but `compute_conservation_metrics()`
returned V=0, q=0, alpha=0 → theta_min=inf. Root cause: count
functions used implicit `graph_store.domain` (None for AGE stores that
serve all domains) instead of the explicit domain the route passes.
Fix: pass explicit domain through ALL count paths.

**Issue B — AGE cannot serialize infinity (CODE FIX).** When
theta_min=inf (legitimate for zero-data), AGE Cypher interprets `inf`
as a variable name, not a numeric. Fix: sentinel string `"Infinity"`
stored as TEXT, decoded to `float("inf")` on read. NaN always rejected
(computation error upstream, not a valid state).

**Issue C — DKWeight JSON/list read compatibility (CODE FIX).** AGEClient
normalizes JSON string properties into Python lists on read. The
`get_dk_weights()` read path expected JSON strings only. Fix: accept
both `str` (parse with `json.loads`) and `list` (use directly). Same
for Welford vector fields. Keep validation strict. Don't change write
format.

**Issue D — Old status-null Decision nodes.** Not migrated. New
writes include status + domain. Historical cleanup is a separate
later item.

**Issue E — GRAPH_DSN vs DATABASE_URL auth mismatch.** Config issue.
Standardize on DATABASE_URL for live AGE proof. Not a product bug.

**Issue F — SOC remains #132 gap.** SOC L5 persistence is conditional
on categories_with_data (P25c accepted behavior). SOC DK runtime
requires P-DK-RUNTIME-SOC (separate prompt). C9 passes for 4 non-SOC
domains. SOC adds 3 cells after #132 ships.

**Issue G — TRIGGERED_BY edge requires status transition.** If live
seeding keeps conservation at the same status throughout (e.g., GREEN
from start), no TRIGGERED_BY edge is created — correct behavior, not
a bug. Fix: seed starting from zero decisions (RED) through 200+
(GREEN transition). That RED→GREEN produces a TRIGGERED_BY edge.

**Issue H — Multi-process tracker coordination.** Future hardening.
Not C9 blocker.

**C9 revised proof standard:** 4 non-SOC domains × 3 node types =
12 cells (not 15). SOC = #132 gap. TRIGGERED_BY = present if
transition exercised, "not exercised" if not.

### Review 6 — L5 upsert as core reusable capability (1 pattern, 3 callers)

**L5Centroid used DKWeight's delete-create pattern, but L5Centroid has
SHAPED_BY edges and DKWeight does not.** AGE refuses to DELETE a vertex
with edges. This caused all repeated centroid writes to fail once the
first SHAPED_BY edge existed.

**The deeper fix:** updating an L5 current-state node is a BASIC
REPEATABLE OPERATION — not three separate implementations with different
mutation patterns. All three node types (Centroid, DKWeight,
ConservationState) need the same capability: upsert a current-state node,
handle duplicates from garbled state, manage optional provenance edges.

Fix: `_l5_upsert_current()` — one method on AGEGraphStore that ALL
three node types call. Handles 0 nodes (CREATE), 1 node (SET), N
duplicates (cleanup → CREATE), edge replacement, missing edge target,
and edge_condition gating. 8 parametrized tests cover every starting
state × every node type.

**All three L5 node types now use the SAME core method:**

| Node | identity keys | edge_type | edge_condition |
|---|---|---|---|
| L5Centroid | (domain, category, action) | SHAPED_BY | Always (when in MEAN_CONVERGENCE) |
| L5ConservationState | (domain) | TRIGGERED_BY | Only on status transitions |
| L5DKWeight | (domain) | None | N/A (Welford is the audit chain) |

**Seven design questions answered permanently:**

1. L5Centroid model = **current-state** (one node per identity, SET-updated)
2. SHAPED_BY = **latest decision only** (not accumulated history)
3. Delete old SHAPED_BY edge = **YES** (delete EDGE, not NODE)
4. C9 = **current-state proof** (exists + has SHAPED_BY = pass)
5. P26 startup read = **one node per identity** (no latest-selection needed)
6. update_centroid = **upsert via SET** (not delete-create)
7. DETACH DELETE = **NEVER for L5 nodes** (delete edges explicitly)

**Core design: L5 current-state upsert as a reusable capability.**

Updating a current-state L5 node in AGE (centroid, DK weight, or
conservation state) is a BASIC REPEATABLE OPERATION that every L5
write path uses. It must be a single well-tested method — not three
separate implementations with different mutation patterns.

**The pattern (implemented once, used by all three node types):**

```python
def _l5_upsert_current(
    self,
    label: str,                    # "L5Centroid", "L5DKWeight", "L5ConservationState"
    identity: dict[str, str],      # fields that define "same node" (domain + node-specific keys)
    properties: dict[str, Any],    # all properties to SET/CREATE with
    edge_type: str | None = None,  # "SHAPED_BY", "TRIGGERED_BY", or None
    edge_target_label: str = "Decision",
    edge_target_id: dict[str, str] | None = None,  # {domain: ..., decision_id: ...}
    edge_condition: bool = True,   # False = skip edge ops (e.g., same-status conservation)
) -> str | None:
    """
    Core L5 current-state upsert. Guarantees convergence to exactly
    1 node + 0 or 1 edge regardless of starting state.
    Returns node id if available, None otherwise.

    Handles:
    - 0 nodes → CREATE
    - 1 node → SET properties
    - N nodes → cleanup duplicates → CREATE fresh
    - 0 edges → CREATE if edge_condition
    - 1 edge → DELETE old + CREATE new if edge_condition
    - N edges → DELETE ALL + CREATE 1 if edge_condition
    - edge_condition=False → leave existing edges untouched
    - Missing edge target → log warning, skip edge (non-fatal)

    NOT atomic: makes 3-5 separate AGE queries. If a query fails
    mid-sequence, state may be inconsistent — but the self-healing
    property recovers on the NEXT call (garbled → cleanup → correct).
    """
    where_clause = " AND ".join(
        f"n.{k} = {_S(v)}" for k, v in identity.items()
    )

    # Step 1: Count existing nodes for this identity
    existing = self._client.query(
        f"MATCH (n:{label}) WHERE {where_clause} RETURN n"
    )

    if len(existing) > 1:
        # GARBLED STATE: duplicates from failed prior writes.
        # Delete ALL edges in BOTH directions (outgoing AND incoming)
        # to ensure nodes become edge-free and deletable.
        # Uses -[r]-() not -[r]->() to catch any edge direction.
        logger.warning(
            f"{label} garbled state: {len(existing)} nodes for "
            f"{identity}. Cleaning up."
        )
        self._client.query(
            f"MATCH (n:{label})-[r]-() "
            f"WHERE {where_clause} DELETE r"
        )
        self._client.query(
            f"MATCH (n:{label}) WHERE {where_clause} DELETE n"
        )
        existing = []  # Force CREATE path

    all_props = {**identity, **properties}
    prop_str = ", ".join(f"{k}: {_S(v)}" for k, v in all_props.items())

    if existing:
        # EXACTLY ONE NODE: SET properties in place (never delete node)
        set_clause = ", ".join(
            f"n.{k} = {_S(v)}" for k, v in properties.items()
        )
        self._client.query(
            f"MATCH (n:{label}) WHERE {where_clause} SET {set_clause}"
        )
        # Delete + replace edge ONLY when edge_condition is True.
        # When edge_condition=False (e.g., conservation same-status),
        # leave existing edges untouched — don't delete provenance
        # from the last real transition.
        if edge_type and edge_condition:
            self._client.query(
                f"MATCH (n:{label})-[r:{edge_type}]->() "
                f"WHERE {where_clause} DELETE r"
            )
    else:
        # NO NODE: CREATE fresh
        self._client.query(f"CREATE (n:{label} {{{prop_str}}})")

    # Step 3: CREATE new edge if conditions met
    if edge_type and edge_condition and edge_target_id:
        target_where = " AND ".join(
            f"t.{k} = {_S(v)}" for k, v in edge_target_id.items()
        )
        target_exists = self._client.query(
            f"MATCH (t:{edge_target_label}) WHERE {target_where} "
            f"RETURN t"
        )
        if target_exists:
            now = _S(str(time.time()))
            self._client.query(
                f"MATCH (n:{label}), (t:{edge_target_label}) "
                f"WHERE {where_clause} AND {target_where} "
                f"CREATE (n)-[:{edge_type} {{timestamp: {now}}}]->(t)"
            )
        else:
            logger.warning(
                f"{edge_type} edge target not found: {edge_target_id}"
            )

    return None  # AGE CREATE doesn't return id reliably; callers
                 # generate their own ids if needed
```

**Each L5 node type calls the core method:**

```python
# L5Centroid — called from scoring_router after learn (MEAN_CONVERGENCE only)
def update_centroid(self, domain, category, action, centroid_vector,
                    count=None, eta_last=None, caused_by_decision_id=None):
    self._l5_upsert_current(
        label="L5Centroid",
        identity={"domain": domain, "category": category, "action": action},
        properties={
            "centroid_vector_json": json.dumps(centroid_vector),
            "count": count or 0,
            "eta_last": eta_last or 0.0,
            "updated_at_epoch": time.time(),
        },
        edge_type="SHAPED_BY",
        edge_target_id={"domain": domain, "decision_id": caused_by_decision_id}
            if caused_by_decision_id else None,
    )

# L5ConservationState — called from scoring_router after learn
def update_conservation_state(self, domain, status, alpha, q, V, ...
                              caused_by_decision_id=None, old_status=None):
    is_transition = old_status is not None and old_status != status
    self._l5_upsert_current(
        label="L5ConservationState",
        identity={"domain": domain},
        properties={
            "status": status, "alpha": alpha, "q": q, "V": V,
            "theta_min": "Infinity" if math.isinf(theta_min) else theta_min,
            # ... all other properties
            "updated_at_epoch": time.time(),
        },
        edge_type="TRIGGERED_BY",
        edge_target_id={"domain": domain, "decision_id": caused_by_decision_id}
            if caused_by_decision_id else None,
        edge_condition=is_transition,  # Only on status transitions
    )

# L5DKWeight — called from dk_persistence after reestimate_dk
def update_dk_weights(self, domain, weight_tensor, n_decisions_used,
                      computed_at, *, welford_state=None, ...):
    # DECISION: DKWeight migrates to _l5_upsert_current (SET pattern).
    # L5DKWeightArchive / supersedes chain from P24 is DROPPED.
    # Rationale: Welford state IS the audit chain for DK weights —
    # archive nodes were a pre-Welford mechanism, now redundant.
    self._l5_upsert_current(
        label="L5DKWeight",
        identity={"domain": domain},
        properties={
            "weight_json": json.dumps(weight_tensor),
            "n_decisions_used": n_decisions_used,
            "computed_at": computed_at,
            # Welford fields (nullable — absent for old rows):
            **({"confirmed_mean_json": json.dumps(welford_state["confirmed_mean"]),
                "confirmed_m2_json": json.dumps(welford_state["confirmed_m2"]),
                "overridden_mean_json": json.dumps(welford_state["overridden_mean"]),
                "overridden_m2_json": json.dumps(welford_state["overridden_m2"]),
                "all_mean_json": json.dumps(welford_state["all_mean"]),
                "all_m2_json": json.dumps(welford_state["all_m2"]),
               } if welford_state else {}),
            "updated_at_epoch": time.time(),
        },
        edge_type=None,  # No provenance edges — Welford IS the audit chain
    )
```

**What this achieves:**

| Before (three separate implementations) | After (one core method) |
|---|---|
| Centroid: delete-create (crashes on edges) | `_l5_upsert_current(edge_type="SHAPED_BY")` |
| Conservation: SET (works but edge handling is separate code) | `_l5_upsert_current(edge_type="TRIGGERED_BY", edge_condition=is_transition)` |
| DKWeight: delete-create + archive (separate pattern) | `_l5_upsert_current(edge_type=None)` |
| Three mutation patterns, three edge-handling paths, three sets of tests | **One pattern, one test suite, three callers** |

**Test suite for `_l5_upsert_current` (10 tests — covers ALL node types):**

| # | Test | Starting state | Proves |
|---|---|---|---|
| 1 | `test_l5_upsert_create_fresh` | 0 nodes | CREATE works for any label |
| 2 | `test_l5_upsert_set_existing` | 1 node, 0 edges | SET updates properties, node preserved |
| 3 | `test_l5_upsert_replace_edge` | 1 node, 1 edge | Old edge deleted, new edge created |
| 4 | `test_l5_upsert_cleanup_duplicates` | 3 nodes, mixed edges | Recovery → 1 node, 1 edge |
| 5 | `test_l5_upsert_multiple_stale_edges` | 1 node, 4 edges | All old edges deleted, 1 new edge |
| 6 | `test_l5_upsert_missing_edge_target` | 1 node, decision doesn't exist | Edge skipped, node updated, warning logged |
| 7 | `test_l5_upsert_edge_condition_false` | 1 node, 1 old edge | edge_condition=False: old edge LEFT IN PLACE (no delete, no create). Conservation same-status update preserves last transition's TRIGGERED_BY. |
| 8 | `test_l5_upsert_no_edge_type` | 1 node | edge_type=None: no edge operations (DKWeight pattern) |
| 9 | `test_l5_upsert_edge_wanted_no_target_id` | 1 node, 1 old edge | edge_type set, edge_condition=True, but edge_target_id=None: old edge deleted, no new edge. Centroid without caused_by_decision_id. |
| 10 | `test_l5_upsert_garbled_with_incoming_edges` | 2 nodes, 1 has incoming edge | Cleanup deletes both-direction edges, then deletes nodes, creates fresh. Verifies `-[r]-()` pattern. |

**This test suite runs against ALL three label types** via parametrization:

```python
@pytest.fixture(params=["L5Centroid", "L5DKWeight", "L5ConservationState"])
def label(request):
    return request.param
```

Every label gets every test. One suite covers all three node types.

### Review findings applied to `_l5_upsert_current` (7 issues found, all fixed)

| # | Issue | Severity | Fix applied |
|---|---|---|---|
| 1 | `edge_condition=False` deleted old edge but skipped new → 0 edges. Conservation same-status lost its TRIGGERED_BY. | **BUG** | Edge deletion now gated on `edge_condition`. When False: edges untouched. |
| 2 | DKWeight archive pattern conflict. P24 used L5DKWeightArchive + supersedes chain. `_l5_upsert_current` uses SET (no archive). | **DESIGN** | DKWeight archive DROPPED. Welford IS the audit chain — archive was pre-Welford, now redundant. |
| 3 | Garbled cleanup only deleted `edge_type` edges. Nodes with unexpected edge types still had edges → DELETE failed. | **BUG** | Cleanup deletes ALL edges: `[r]-()` not `[r:{edge_type}]->()`. |
| 4 | Return value mismatch. Protocol says `-> str`, method returned None. | **MINOR** | Returns `None` with note: AGE CREATE doesn't return id reliably. Callers generate ids if needed. |
| 5 | Bare `time.time()` float in edge Cypher. AGE may interpret incorrectly. | **MINOR** | Wrapped in `_S(str(time.time()))` for serialization consistency. |
| 6 | No atomicity documentation. 3-5 separate queries per upsert. | **MINOR** | Docstring added: "NOT atomic. Self-healing on next call." |
| 7 | Garbled cleanup only deleted OUTGOING edges `(n)-[r]->()`. Incoming edges would cause DELETE node to fail. | **BUG** | Changed to both-direction pattern `(n)-[r]-()` in garbled cleanup. |

### 8-Criteria Architectural Review of `_l5_upsert_current`

**1. CORRECTNESS — State machine convergence:** ✅ PASS

Every starting state in the table converges to (1 node, 0 or 1 edge).
Traced all 9 paths:
- 0 nodes + no target → (1, 0) ✅
- 0 nodes + target → (1, 1) ✅
- 1 node, 0 edges, condition=True → (1, 1) ✅
- 1 node, 0 edges, condition=False → (1, 0) ✅
- 1 node, 1 edge, condition=True → (1, 1) ✅
- 1 node, 1 edge, condition=False → (1, 1 preserved) ✅
- 1 node, N edges, condition=True → (1, 1) ✅
- N nodes, mixed → cleanup → (1, 0 or 1) ✅
- N nodes, condition=False → cleanup → (1, 0) ✅ (provenance lost but garbled state was already broken)

**2. EDGE CASES — 3 additional starting states found:**

| State | Handled? | Notes |
|---|---|---|
| 1 node with INCOMING edges `()-[r]->(n)` | ⚠️ **PARTIALLY** | The garbled cleanup deletes `(n)-[r]->()` (outgoing only). If an L5 node has incoming edges, the subsequent `DELETE n` crashes. No current code creates incoming edges to L5 nodes, but for robustness the cleanup should use `(n)-[r]-()` (both directions). |
| edge_condition=True but edge_target_id=None | ✅ Handled | Line 331: `edge_type and edge_condition and edge_target_id` — all three must be truthy. With edge_target_id=None, edge creation is skipped. Old edge is deleted (line 321). Result: (1 node, 0 edges). Correct for centroid with no caused_by_decision_id. |
| Duplicate Decision targets (violating Standing Rule #52) | ⚠️ **LOW RISK** | If two Decision nodes share (domain, decision_id), edge CREATE at line 341-344 produces 1×2=2 edges. Unlikely given Standing Rule #52 but worth a defensive LIMIT 1 on the target MATCH. |

**Fix for incoming edges (apply to garbled cleanup):**
```python
# BEFORE (outgoing only):
f"MATCH (n:{label})-[r]->() WHERE {where_clause} DELETE r"

# AFTER (both directions):
f"MATCH (n:{label})-[r]-() WHERE {where_clause} DELETE r"
```

**3. AGE COMPATIBILITY:** ✅ PASS

All Cypher patterns are valid AGE syntax. No MERGE (Standing Rule #50).
No ON CREATE SET. No partial constraints. SET on existing nodes is
supported. DELETE on edge-free nodes is supported. CREATE with
properties is supported. MATCH with WHERE clause is supported.

One note: AGE's `MATCH (n), (t) WHERE ... CREATE (n)-[]->(t)` is a
Cartesian product. With 1 L5 node and 1 Decision target, this produces
exactly 1 edge. Safe given the cleanup ensures 1 L5 node.

**4. CONCURRENCY:** ⚠️ DOCUMENTED RISK (acceptable)

Two concurrent writers for the same identity:
```
Writer A: reads 0 nodes → CREATE → 1 node
Writer B: reads 0 nodes → CREATE → 2 nodes (race)
Next call: detects 2 → cleanup → 1 node
```
The self-healing property recovers on the next call. Between the race
and the next call, reads may return either node — the ORDER BY LIMIT 1
from P25-HARDENING mitigates this for readers. Documented as "NOT
atomic. Self-healing on next call." Acceptable for single-process
deployment per domain (current architecture).

**5. PERFORMANCE:** ✅ PASS (minor optimization possible)

| Path | Queries | Could optimize? |
|---|---|---|
| 1 node, edge_condition=True | 4 (MATCH, SET, DELETE edge, MATCH+CREATE edge) | Could combine SET + DELETE edge into one query. Minor. |
| 1 node, edge_condition=False | 2 (MATCH, SET) | Optimal. |
| 0 nodes, with edge | 3 (MATCH, CREATE, MATCH+CREATE edge) | Optimal. |
| N nodes garbled | 5 (MATCH, DELETE edges, DELETE nodes, CREATE, CREATE edge) | Acceptable — rare path. |

No unnecessary queries. The target_exists check before edge creation
(lines 335-338) adds 1 query but provides clean logging when the
Decision is missing — better than try/except on a failed CREATE.

**6. API DESIGN:** ✅ PASS

- `identity` vs `properties` separation is clean and correct
- `edge_condition` gating works for all three callers
- `edge_type=None` cleanly disables all edge operations (DKWeight)
- Callers are thin (5-15 lines each) — all complexity is in the core method
- The `edge_target_id` as optional dict handles "no provenance available" correctly

**7. TEST COVERAGE:** ⚠️ 2 MISSING TESTS

| # | Missing test | What it would prove |
|---|---|---|
| 9 | `test_l5_upsert_edge_wanted_no_target_id` | edge_type="SHAPED_BY", edge_condition=True, edge_target_id=None. Old edge deleted, no new edge created. Centroid without caused_by_decision_id. |
| 10 | `test_l5_upsert_garbled_with_incoming_edges` | 2 nodes where one has an incoming edge. Cleanup deletes both-direction edges, then deletes nodes. Verifies the `-[r]-()` fix. |

**8. BUGS:** 1 remaining after prior 6 fixes

**Garbled cleanup only deletes OUTGOING edges.** Line 297-299 uses
`(n)-[r]->()` which is direction-specific. If an L5 node has incoming
edges (from any source), `DELETE n` at line 301-303 will fail.

Fix: change `(n)-[r]->()` to `(n)-[r]-()` in the garbled cleanup.
This matches edges in both directions. The normal single-node path
(line 322-325) can stay direction-specific because it only manages
known edge types which are always outgoing.

### Discovery scan resolution (Prompt 0 — COMPLETE)

The scan confirmed every GAE parameter with zero unknowns:
- `DecisionCountPolicy(n=200)`: categories transition after 200 decisions
- `FixedAlpha(0.5)`: 50% prior + 50% data = shrinkage/graduation
- `CoordinateDescentEstimator.estimate()`: takes (decisions, centroids, n_categories, n_dims), returns (C, d) ndarray
- `VARIANCE_LEARNING` is a phase string on `CategoryState`, not a category-index set
- `get_verified_decisions()` returns all needed fields (factor_vector, category_index, is_correct)
- GAE editable install works from copilot-sdk
- No custom cadence counter needed — call `reestimate_dk()` every learn, it returns early when not in VARIANCE_LEARNING

### What this plan produces when complete

After C9, every SDK copilot (Trading, Purchasing, DataOps, S2P):
1. **Constructs** ProfileScorer with full LearningStrategy + estimator
2. **Learns centroids** for the first 200 decisions per category (MEAN_CONVERGENCE)
3. **Transitions** to DK estimation after 200 decisions (VARIANCE_LEARNING)
4. **Estimates** DK precision weights via CoordinateDescentEstimator
5. **Shrinks** estimated weights: 50% prior + 50% data (FixedAlpha)
6. **Scores** with learned DK weights (factor precision affects recommendations)
7. **Persists** centroids (MEAN_CONVERGENCE only), DK weights + Welford, and conservation state to L5
8. **Monitors** DK-weighted accuracy via conservation gate (auto-pause on AMBER)
9. **Survives restart** via P26 startup read from L5 store

SOC follows with P-DK-RUNTIME-SOC (separate prompt) + #132 SOC-OPTION-C.

This is the full compounding intelligence loop for SDK copilots. Trust
traps are discovered. The 288-moat is firm-specific. The Mirror shows
learned insight. The product's three core claims become true for 4 of
5 copilots; SOC follows as a documented next step.

### Execution Plan Synopsis

**What this plan is:** A 5-prompt sequence (+ C9 gate) that takes the
platform from "scores with static DK priors" to "computes, persists,
and scores with learned DK precision weights." This is the P1 gap that
makes or breaks the product's three core claims (trust-trap discovery,
288-moat, compounding intelligence).

**Complete prompt sequence:**

```
Prompt 0:  Discovery scan           (30 min) ✅ COMPLETE
Prompt 1:  P-WELFORD-A storage      (0.5d)   ✅ Nullable Welford columns in L5 stores
Prompt 2a: Construction change      (1d)     ✅ from_preset() → LearningStrategy + estimator
           ── GATE: G1 (noisy factor down-weighted) + G2 (shrinkage at low N) ──
Prompt 2b: DK persistence + Welford (1d)     ✅ dk_persistence.py, WelfordTracker
Prompt 2c: Router wiring + startup  (1d)     ✅ scoring_router.py, S2P, app init
Prompt 3:  P26 startup read         (0.5d)   ✅ Warm-start from L5
Prompt 3b: Centroid L5 write        (0.5d)   ✅ Phase-aware (MEAN_CONVERGENCE only)
Prompt 4:  P27 full flow test       (0.5d)   ✅ All 3 node types + Welford + edges
C9-FIX:    Combined fixer           (0.5d)   ← CURRENT
           Fix A: explicit-domain conservation metrics
           Fix B: theta_min=inf sentinel serialization
           Fix C: DKWeight JSON/list read compatibility
           Fix D: L5Centroid upsert → _l5_upsert_current (SET, not delete-create)
C9:        L5 proof rerun           (1h)     ← NEXT
           4 non-SOC domains × 3 node types = 12 cells + edges
```

**Total effort:** ~6.5 working days. All prompts through P27 complete.
C9-FIX + C9 rerun remaining.

**What changed across versions (v1 → v5.4):**

| Version | Key change | Why |
|---|---|---|
| v1 | Original 5-prompt plan: Prompt 0-4 + C9 | Initial plan, linear sequence |
| v2 | +GPT 6-point feedback: split Prompt 2 (2a/2b/2c), behavioral gate G1+G2, ghost prerequisite, built-in shrinkage, editable install, C9 gates blog | Monolith was too risky. Behavioral test became THE gate. |
| v2.1 | +Scan results: DecisionCountPolicy(n=200), FixedAlpha(0.5), no custom cadence | All GAE params confirmed. Custom cadence eliminated. |
| v3 | Clean rebuild integrating scan results throughout | Removed all stale cadence=10 references. 200-decision phase gate in behavioral tests. |
| v4 | +Prompt 3b (centroid L5 wire moved before P27). Sequencing conflict resolved. | P27 = "all 3 types" but centroid wire was listed after C9. |
| v4.1 | +C9-FIX section: domain bug + inf sentinel + JSON compat | Live AGE proof found 3 code issues blocking ConservationState. |
| v5 | Integrated C9-FIX. Synopsis expanded to 6 reviews. C9 = 12 cells (SOC = #132 gap). | Removed "addendum" label. All reviews in synopsis. |
| v5.1 | +Review 6: L5Centroid upsert used wrong AGE pattern (delete-create → SET) | Centroid with SHAPED_BY edge couldn't be deleted. |
| v5.2 | +Core `_l5_upsert_current()` method. 1 pattern, 3 callers, 8 tests. | Objectified the upsert as reusable capability, not 3 separate implementations. |
| v5.3 | +Self-review: 6 bugs fixed (edge_condition gating, garbled cleanup, archive drop, timestamp, return type, atomicity doc) | Line-by-line code review of the core method. |
| **v5.4** | +8-criteria review: 1 more bug (incoming edges), 2 more tests, DKWeight archive formally dropped | Comprehensive correctness/AGE/concurrency/performance/test audit. 10 tests × 3 labels = 30 cases. |

**Key architectural decisions locked across all versions:**

| Decision | Resolution | Version locked |
|---|---|---|
| DK affects live scoring? | YES — compute + persist + activate in one step | v2 (Phase 2 eliminated) |
| Runtime strategy | Option A — scorer's own `reestimate_dk()`, not external bridge | v3 (hack rejected) |
| LearningStrategy | FULL (not minimal): DecisionCountPolicy(200) + CoordinateDescentEstimator + FixedAlpha(0.5) | v3 |
| Custom cadence | NONE — use GAE phase transitions | v2.1 (scan confirmed) |
| Centroid L5 writes | MEAN_CONVERGENCE only (frozen in VARIANCE_LEARNING = skip) | v4 |
| L5 upsert pattern | `_l5_upsert_current()`: SET for existing, CREATE for new, edge replacement | v5.2 |
| DKWeight archive | DROPPED — Welford IS the audit chain | v5.3 |
| C9 scope | 4 non-SOC domains × 3 types = 12 cells. SOC = #132 gap. | v5 |
| DETACH DELETE | NEVER for L5 nodes | v5.1 |
| theta_min = inf | Sentinel string `"Infinity"` decoded to `float("inf")` | v5 (C9-FIX) |

**Standing rules added by this plan:**

- All L5 node types use `_l5_upsert_current()` core method
- L5 centroid writes are phase-aware (MEAN_CONVERGENCE only)
- SHAPED_BY = latest decision only (not accumulated history)
- DKWeight audit chain = Welford accumulators (not archive nodes)
- Conservation same-status: properties updated, edges untouched
- Garbled state: self-healing cleanup on next write
- AGE serialization: infinity as sentinel, NaN always rejected

```python
from gae.profile_scorer import LearningStrategy, ProfileScorer
from gae.dk_estimator import CoordinateDescentEstimator

# EXACT parameters for_soc_twophase() uses — use these in from_preset():
strategy = LearningStrategy(
    phase_policy=DecisionCountPolicy(n=200),   # 200 decisions before VARIANCE_LEARNING
    dk_estimator=CoordinateDescentEstimator(),  # coordinate descent on buffered decisions
    shrinkage_schedule=FixedAlpha(0.5),         # 50% prior + 50% data = graduation
)
# Additional ProfileScorer params:
# eta_override=0.01           (v14 canonical)
# auto_pause_on_amber=True    (conservation integration)
```

**Phase behavior (GAE's designed architecture, NOT custom code):**
- Category starts in `MEAN_CONVERGENCE`: `update()` does centroid learning only
- After 200 verified decisions: `CategoryState.freeze()` → `VARIANCE_LEARNING`
- In `VARIANCE_LEARNING`: `update()` buffers decisions for DK estimation
- `reestimate_dk()` runs `CoordinateDescentEstimator.estimate()` on buffered decisions
- `FixedAlpha(0.5)` shrinks results: `applied = 0.5 * prior + 0.5 * estimated`
- `score()` uses `_dk_weights` when category is in `VARIANCE_LEARNING`

**No custom cadence counter needed.** Call `reestimate_dk()` after every
learn. It returns early when no category is in VARIANCE_LEARNING
(negligible cost). `DecisionCountPolicy(n=200)` controls the phase
transition — not our code.

**CoordinateDescentEstimator.estimate() API (from scan):**
```python
estimate(
    decisions,     # sequence of (factor_vector, category_index, correct_action_index)
    centroids,     # (C, A, D) or (A, D) numpy array
    n_categories,  # int
    n_dims,        # int
) -> np.ndarray   # shape (n_categories, n_dims)
```

---

## Prompt Sequence

```
Prompt 0: DISCOVERY SCAN           (30 min, no code changes) ✅ COMPLETE
Prompt 1: P-WELFORD-A              (0.5d, storage/protocol)
Prompt 2: P-DK-RUNTIME-FULL        (3-4d, split into 3 sub-prompts)
  Prompt 2a: CONSTRUCTION CHANGE   (1d, construction + behavioral gate)
  ──── GATE: behavioral test proves DK weights change with data ────
  Prompt 2b: PERSISTENCE + WELFORD (1d, dk_persistence.py + L5 writes)
  Prompt 2c: ROUTER + STARTUP      (1d, scoring_router wiring + app init)
Prompt 3: P26 STARTUP-READ         (0.5d, warm-start from L5)
Prompt 3b: P-CENTROID-L5-WIRE      (0.5d, L5 centroid runtime write)
Prompt 4: P27 FULL-FLOW-TEST       (0.5d, L5 completion gate)
          C9: L5 PROOF             (manual, 1h)
```

---
## Prompt 0 — Discovery Scan (30 min, no code changes)

**Purpose:** Determine exact constructor parameters for ProfileScorer
with full LearningStrategy. This is information gathering — Codex
reads code and reports, does not modify anything.

**Prompt:**

```
/model gpt-5.3
Echo the current model name in the first line of output.

TASK: Discovery scan only. Read code and report findings. NO code changes.
TASK TYPE: Code analysis.

WORKING DIRECTORY:
C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects

RUN THESE SCANS AND REPORT OUTPUT:

SCAN 1 — ProfileScorer constructor and for_soc_twophase:

Set-Location "$env:CLAUDE_PROJECTS\graph-attention-engine-v50"
python -c @"
import inspect
from gae.profile_scorer import ProfileScorer

print('=== for_soc_twophase FULL SOURCE ===')
print(inspect.getsource(ProfileScorer.for_soc_twophase))

print('=== __init__ FULL SOURCE ===')
print(inspect.getsource(ProfileScorer.__init__))

print('=== reestimate_dk FULL SOURCE ===')
print(inspect.getsource(ProfileScorer.reestimate_dk))

print('=== score DK-RELEVANT LINES ===')
src = inspect.getsource(ProfileScorer.score)
for i, line in enumerate(src.split(chr(10))):
    if any(k in line for k in ['_dk_weights', 'VARIANCE', '_learning_strategy', 'learning']):
        print(f'  L{i}: {line.strip()}')
"@

SCAN 2 — LearningStrategy class:

python -c @"
import inspect, sys
sys.path.insert(0, '.')
# Find LearningStrategy - may be in profile_scorer or separate module:
try:
    from gae.profile_scorer import LearningStrategy
    print('=== LearningStrategy SOURCE ===')
    print(inspect.getsource(LearningStrategy))
except ImportError:
    print('LearningStrategy not in profile_scorer')
    # Search other modules:
    import os
    for f in os.listdir('gae'):
        if f.endswith('.py'):
            src = open(f'gae/{f}').read()
            if 'class LearningStrategy' in src or 'VARIANCE_LEARNING' in src:
                print(f'FOUND in gae/{f}')
                for i, line in enumerate(src.split(chr(10))):
                    if 'LearningStrategy' in line or 'VARIANCE' in line:
                        print(f'  L{i}: {line}')
"@

SCAN 3 — CoordinateDescentEstimator.estimate() signature:

python -c @"
import inspect
from gae.dk_estimator import CoordinateDescentEstimator
print('=== estimate FULL SOURCE ===')
print(inspect.getsource(CoordinateDescentEstimator.estimate))
print('=== __init__ ===')
print(inspect.getsource(CoordinateDescentEstimator.__init__))
"@

SCAN 4 — Can GAE be imported from copilot-sdk?

Set-Location "$env:CLAUDE_PROJECTS\copilot-sdk"

# First: install GAE as an editable package (correct dependency management):
pip install -e ../graph-attention-engine-v50 --break-system-packages 2>&1 | Select-Object -Last 3

# Then verify import:
python -c @"
try:
    from gae.dk_estimator import CoordinateDescentEstimator
    from gae.profile_scorer import ProfileScorer
    print('GAE IMPORT: OK')
    print(f'ProfileScorer methods: {[m for m in dir(ProfileScorer) if not m.startswith("_")]}')
except ImportError as e:
    print(f'GAE IMPORT FAILED: {e}')
    print('RESOLUTION: GAE may need a setup.py/pyproject.toml for editable install')
    print('Create a minimal pyproject.toml in graph-attention-engine-v50/ if missing')
"@

SCAN 5 — Current from_preset() and CompoundingScorer.learn():

python -c @"
import inspect
from copilot_sdk.scoring.scorer import CompoundingScorer
print('=== from_preset FULL SOURCE ===')
print(inspect.getsource(CompoundingScorer.from_preset))
print('=== learn FULL SOURCE ===')
print(inspect.getsource(CompoundingScorer.learn))
print('=== __init__ ===')
print(inspect.getsource(CompoundingScorer.__init__))
"@

SCAN 6 — What get_verified_decisions returns:

python -c @"
import inspect
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
print('=== get_verified_decisions ===')
print(inspect.getsource(SQLiteGraphStore.get_verified_decisions))
"@

OUTPUT REQUIRED:
Report ALL scan output. Then answer these 5 questions:

Q1: What parameters does for_soc_twophase() pass to ProfileScorer.__init__
    that from_preset() does NOT? List each with its default value.

Q2: What is the LearningStrategy constructor signature? What does
    VARIANCE_LEARNING contain (set of category indices)?

Q3: What does CoordinateDescentEstimator.estimate() expect as input?
    (exact parameter names + types)

Q4: Does GAE import from copilot-sdk? If not, what path fix is needed?

Q5: What fields does get_verified_decisions() return per decision?
    (exact dict keys)

DO NOT MODIFY ANY CODE. Report only.
```

**Gate:** If Scan 4 fails (GAE import), resolve before proceeding:
1. Check if `graph-attention-engine-v50/` has a `setup.py` or `pyproject.toml`
2. If not, create a minimal `pyproject.toml` with `[project] name="gae"`
3. Run `pip install -e ../graph-attention-engine-v50`
4. Verify `from gae.dk_estimator import CoordinateDescentEstimator` works

Do NOT use `sys.path.insert` — that's brittle, CWD-dependent, and
breaks test suites. GAE must be a proper importable package, which
also aligns with the open-source (Track A) plan.


---

## Prompt 1 — P-WELFORD-A: Storage Extension (0.5d)

**Full spec:** p_welford_architecture_decision.md §P-WELFORD-A

**Summary:** Extend L5LearningStore.update_dk_weights() with optional
keyword-only `welford_state`, `n_confirmed`, `n_overridden`,
`entity_group`. Add nullable columns to SQLite, InMemory, AGE stores.
6 tests. Backward-compatible (old rows return welford_state=None).

**Prerequisite:** Prompt 0 scan complete. ✅

**Acceptance:** All existing tests pass + 6 new Welford storage tests.

---

## Prompt 2 — P-DK-RUNTIME-FULL (3-4d, split into 3 sub-prompts)

**Full spec:** dk_runtime_fix_architecture_v3.md
**This is the prompt sequence that makes the product's claims true.**

### Prompt 2a — Construction Change + Behavioral Gate (1d)

**The crux.** If this is wrong, everything built on it is wrong.

**Scope:**
1. Modify `CompoundingScorer.from_preset()` to construct `ProfileScorer`
   with full `LearningStrategy` + `CoordinateDescentEstimator`.
   Categories start in `MEAN_CONVERGENCE` and transition to
   `VARIANCE_LEARNING` via `DecisionCountPolicy(n=200)` — this is
   GAE's designed phase gate, not custom code.
2. Add `reestimate_dk_if_due()` method that calls
   `self._scorer.reestimate_dk()` after every learn. Returns early
   if no category is in `VARIANCE_LEARNING` yet (negligible cost).
   No custom cadence counter — GAE's phase policy controls timing.
3. Add accessors: `get_dk_weights()`, `get_verified_count()`.

**Exact construction change in `from_preset()`:**
```python
# BEFORE (current — no DK learning):
self._scorer = ProfileScorer(mu=centroids, actions=actions, categories=categories)

# AFTER (full intelligence loop):
from gae.dk_estimator import CoordinateDescentEstimator
strategy = LearningStrategy(
    phase_policy=DecisionCountPolicy(n=200),
    dk_estimator=CoordinateDescentEstimator(),
    shrinkage_schedule=FixedAlpha(0.5),
)
self._scorer = ProfileScorer(
    mu=centroids, actions=actions, categories=categories,
    learning_strategy=strategy,
    eta_override=0.01,
    auto_pause_on_amber=True,
)
# If for_soc_twophase() hardcodes SOC-specific constants, use direct
# constructor with these params instead. Either way: full strategy.
```

**File:** `copilot_sdk/scoring/scorer.py` ONLY.

**CoordinateDescentEstimator.estimate() API (from scan):**
```python
estimate(
    decisions,     # sequence of (factor_vector, category_index, correct_action_index)
    centroids,     # (C, A, D) or (A, D) numpy array
    n_categories,  # int
    n_dims,        # int
) -> np.ndarray   # shape (n_categories, n_dims)
```

**Verified-decision data (from scan — `get_verified_decisions()` keys):**
```
decision_id, domain, entity_id, category, category_index,
factors, factor_vector, recommended_action, recommended_index,
confidence, probabilities, status, metadata, created_at,
actual_action, actual_index, is_correct, verified_at,
context, outcome_metadata
```

**THE BEHAVIORAL GATE (must pass before Prompt 2b):**

```python
def test_dk_learning_actually_works():
    """THE gate test. Proves the intelligence loop works, not just the pipeline.

    Feed a dataset where factor 0 is pure noise (random uniform)
    and factor 1 is highly predictive (correlates with correct action).
    Must run 200+ decisions to pass DecisionCountPolicy phase gate,
    then verify DK weights change.

    (a) factor 0's DK weight drops measurably below the prior
    (b) factor 1's DK weight rises measurably above the prior
    (c) scoring output shifts with the updated weights
    """
    scorer = CompoundingScorer.from_preset("trading", graph_store=store)

    # Phase 1: 200 decisions in MEAN_CONVERGENCE (centroid-only learning)
    for i in range(200):
        correct = (i % 2 == 0)
        factors = {
            "signal_alignment": random.random(),              # NOISE — random
            "market_regime": 0.8 if correct else 0.2,         # SIGNAL — predictive
            # ... other factors with moderate signal
        }
        result = scorer.score(category="momentum", factors=factors)
        scorer.learn(decision_id=result.decision_id,
                     actual_action="buy" if correct else "hold",
                     outcome="correct" if correct else "incorrect")

    # Category should now be in VARIANCE_LEARNING
    scorer.reestimate_dk_if_due()

    # Phase 2: 50 more decisions in VARIANCE_LEARNING (DK estimation active)
    for i in range(50):
        # ... same pattern
        result = scorer.score(category="momentum", factors=factors)
        scorer.learn(...)

    scorer.reestimate_dk_if_due()
    learned_weights = scorer.get_dk_weights()
    assert learned_weights is not None, "DK weights should exist after VARIANCE_LEARNING"

    # (a) Noisy factor weight should be lower
    # (b) Signal factor weight should be higher
    # (c) Scoring output should differ from prior-only scoring
    # Exact assertions depend on weight matrix structure — see (C, d) shape
```

**Additional test: FixedAlpha(0.5) shrinkage verification:**

```python
def test_dk_shrinkage_via_fixed_alpha():
    """FixedAlpha(0.5) means DK weights = 50% prior + 50% data-driven.
    This IS the 'graduating from domain prior to firm-specific' mechanism.

    At N=210 (just entered VARIANCE_LEARNING + 10 decisions): weights
    are 50% prior + 50% of a small dataset (close to prior).
    At N=410 (200 more decisions in VARIANCE_LEARNING): weights are
    50% prior + 50% of a larger dataset (more data-driven, but still
    bounded by alpha=0.5).

    The FixedAlpha(0.5) blend ensures DK never fully abandons the prior.
    """
    scorer = CompoundingScorer.from_preset("trading", graph_store=store)

    # Phase 1: 200 decisions → MEAN_CONVERGENCE → VARIANCE_LEARNING
    for i in range(200):
        # ... score + learn
        pass

    # 10 decisions in VARIANCE_LEARNING
    for i in range(10):
        # ... score + learn with noisy factor 0, signal factor 1
        pass
    scorer.reestimate_dk_if_due()
    weights_210 = scorer.get_dk_weights()

    # 200 more decisions in VARIANCE_LEARNING
    for i in range(200):
        # ... score + learn with same pattern
        pass
    scorer.reestimate_dk_if_due()
    weights_410 = scorer.get_dk_weights()

    # More data = more divergence from prior (within 50% alpha constraint)
    # Both should exist and differ
    assert weights_210 is not None
    assert weights_410 is not None
    # weights_410 should show more separation between noisy/signal factors
```

**Gate: If G1 + G2 do not pass, DO NOT proceed to Prompt 2b.**
The GAE machinery (DecisionCountPolicy + FixedAlpha + CoordinateDescentEstimator)
must produce the expected behavior. If it does not, investigate the GAE
estimator — do not work around it.

**Prompt 2a tests (4):**

| # | Test | What it proves |
|---|---|---|
| G1 | `test_dk_learning_actually_works` | **THE gate.** Noisy factor down-weighted, signal factor up-weighted, scoring shifts. |
| G2 | `test_dk_shrinkage_via_fixed_alpha` | FixedAlpha(0.5) graduation: 50% prior + 50% data. More data = more divergence. |
| 3 | `test_dk_phase_transition` | After 200 decisions, category enters VARIANCE_LEARNING. Before 200: centroid-only. |
| 4 | `test_dk_reestimate_early_return` | `reestimate_dk_if_due()` returns early when no category in VARIANCE_LEARNING (fast, no-op). |

### ──── GATE: Prompt 2a behavioral tests G1+G2 must pass ────

### Prompt 2b — Persistence + Welford (1d)

**Scope:**
1. Create `copilot_sdk/scoring/dk_persistence.py`:
   - `WelfordAccumulator` class (online mean + M2)
   - `DKWelfordTracker` class (confirmed + overridden + all)
   - `persist_dk_after_reestimate()`: reads weights FROM scorer,
     writes to L5 with Welford state. Non-fatal.
2. Follows **persist-before-cache ordering** (Standing Rule #48):
   persist to L5 store FIRST, then update cache/state. If both fail,
   raise. If L5 fails but scorer has weights, log error and continue
   (scorer is authoritative for scoring; L5 is for audit/restart).

**File:** `copilot_sdk/scoring/dk_persistence.py` (NEW)

**Prompt 2b tests (5):**

| # | Test | What it proves |
|---|---|---|
| 5 | `test_welford_accumulator_math` | Mean + M2 match batch numpy |
| 6 | `test_welford_confirmed_overridden_split` | is_correct routes correctly |
| 7 | `test_welford_roundtrip_via_state` | Serialize/deserialize matches |
| 8 | `test_persist_dk_reads_from_scorer` | Persistence reads scorer's weights, doesn't compute independently |
| 9 | `test_persist_dk_nonfatal` | L5 failure → scoring continues |

### Prompt 2c — Router Wiring + App Startup (1d)

**Scope:**
1. Wire inline DK persistence in `scoring_router.py` after conservation
   L5 write. After every learn: call `scorer.reestimate_dk_if_due()`,
   then if weights updated, call `persist_dk_after_reestimate()`.
   Same non-fatal pattern as P25b.
2. Wire same in S2P `s2p.py`.
3. App startup: Welford tracker initialization + warm-start from L5.

**Files:** `scoring_router.py`, `s2p.py`, Trading/Purchasing/DataOps/S2P `main.py`

**Prompt 2c tests (5):**

| # | Test | What it proves |
|---|---|---|
| 10 | `test_learn_persists_dk_weights_to_l5` | After 200+ learns (phase transition), L5 has DK weights |
| 11 | `test_learn_dk_includes_welford_state` | L5 DK entry has Welford (6 vectors) |
| 12 | `test_learn_dk_no_store_silent` | learning_store=None → no error |
| 13 | `test_dk_welford_warm_start` | Tracker restored from L5 on startup |
| 14 | `test_dk_weights_activated_in_scorer` | Scorer's own `_dk_weights` updated by `reestimate_dk()`, not external injection |

### Full suite runs

```powershell
Set-Location "$env:CLAUDE_PROJECTS\copilot-sdk"
python -m pytest tests/ -q --timeout=120
python -m pytest apps/trading/backend/tests/ -q --timeout=120
python -m pytest apps/purchasing/backend/tests/ -q --timeout=120
python -m pytest apps/dataops/backend/tests/ -q --timeout=120

Set-Location "$env:CLAUDE_PROJECTS\s2p-copilot\backend"
python -m pytest tests/ -q --timeout=120
```

### Stop conditions

- Do NOT modify GAE library code
- Do NOT create a parallel DK computation path (no external bridge estimator)
- Do NOT inject _dk_weights via private attribute assignment
- Do NOT broaden GraphStore
- Do NOT change conservation formulas
- If GAE import fails → STOP, resolve path, report

---

## Prompt 3 — P26: Startup Read (0.5d)

**Scope:** On copilot startup, read from L5 store:
- Centroids → populate scorer centroids (if available)
- DK weights + Welford → populate scorer DK weights + tracker
- Conservation state → populate conservation monitor

If AGE/L5 unavailable → fall back to SQLite checkpoint or cold-start
defaults. Status must indicate source (AGE vs SQLite vs cold-start).

**Tests:**
- `test_startup_loads_dk_from_l5` — DK weights survive restart
- `test_startup_loads_welford_from_l5` — Welford state survives restart
- `test_startup_loads_conservation_from_l5` — conservation survives restart
- `test_startup_fallback_on_l5_failure` — cold-start if L5 unavailable
- `test_startup_status_indicates_source` — status reports AGE/SQLite/cold

---

## Prompt 4 — P27: Full Flow Integration Test (0.5d)

**Scope:** End-to-end test that verifies the COMPLETE L5 schema:

```
score() → learn() → centroid updated (MEAN_CONVERGENCE phase)
                   → after 200 decisions: phase transition to VARIANCE_LEARNING
                   → DK re-estimated via reestimate_dk()
                   → conservation state persisted
                   → Welford accumulators updated
                   → ALL nodes readable from L5 store
                   → SHAPED_BY edge (centroid → decision)
                   → TRIGGERED_BY edge (conservation → decision, on transition)
```

**Key tests:**
- Test 58: `test_dk_welford_storage_roundtrip` — write + read Welford
- Test 59: `test_full_learn_flow_writes_all_three` — 200+ learn calls
  produce Centroid + DKWeight + ConservationState in L5, with edge
  assertions

**After P27 passes → C9 manual gate.**

---

## C9 — L5 Cross-Copilot Proof (manual, 1h)

Query the AGE graph:

```powershell
# All 5 domains present with L5 nodes:
# (run via psql or AGEClient)

MATCH (c:L5Centroid) RETURN c.domain, count(c) ORDER BY c.domain
MATCH (w:L5DKWeight) RETURN w.domain, count(w) ORDER BY w.domain
MATCH (cs:L5ConservationState) RETURN cs.domain, cs.status ORDER BY cs.domain
```

**Pass criteria:** 4 non-SOC domains × 3 node types = 12 cells populated.
SOC = #132 gap (3 cells added after #132 ships).
DKWeight nodes have welford_state (not null). ConservationState has
valid status. Centroids have count > 0.

**Deliverable:** L5 proof report. L5 COMPLETE.

---

## What Runs AFTER These 5 Prompts

| Item | Effort | Why it can wait |
|---|---|---|
| P-DK-RUNTIME-SOC | 1-2d | SOC has different construction path. SDK first. |
| ~~P-CENTROID-L5-WIRE~~ | — | **MOVED to Prompt 3b (before P27).** Required for all-three-node gate. |
| #131 SQLITE-TO-AGE-MIGRATION | 2-3d | Historical data → AGE. Requires L5 complete. |
| #132 SOC-OPTION-C | 2-3d | SOC α = coverage. Requires L5 complete. |
| #133 L5+ PROOF | 0.5d | Full common data platform proof. |
| Demo build (#120-#127) | 11-16d | Requires L5+ complete. |
| Blog/arxiv publish | Founder action | Gated on **C9 + #132** (see below). |

**None of these run until Prompts 0-4 are done and C9 passes.**

### Updated gate language — C9 is upstream of EVERYTHING

The blog's publish gate was previously "Option C (#132) only." This
is wrong. C9 is what makes the 288-moat and the Mirror TRUE:

| Gate | What it unblocks | Why |
|---|---|---|
| **C9 (L5 COMPLETE)** | 288-moat claim, Mirror demo beat, trust-trap discovery claim, "compounding intelligence" across SDK copilots | Until C9, DK weights are static priors. The 288 is actually 144. The Mirror shows domain design, not learned insight. |
| **C9 + #132** | Blog publish, arxiv submission | Blog claims 288 + SOC conservation. Both must be true. |
| **C9 + #132 + demo build** | LOOM-V1 (#88) | Demo shows learned trust traps + correct SOC conservation numbers. |

A buyer who deploys today and inspects DK weights sees the domain
prior — exactly the over-claim we hedged against in the 288-guardrails.
C9 is what makes the hedge unnecessary.

---

## Discovery Scan Results — Decision Summary (11 questions)

| Q | Question | Answer | Source |
|---|---|---|---|
| 1 | DK affect live scoring? | **YES** | Architecture v3 decision |
| 2 | Which option? | **A — for_soc_twophase() params** | Architecture v3 + scan confirms |
| 3 | Change from_preset()? | **YES** | Architecture v3 decision |
| 4 | S2P same path? | **YES — same from_preset()** | Scan: S2P uses CompoundingScorer.from_preset("s2p") |
| 5 | Cadence? | **GAE DecisionCountPolicy(n=200) + reestimate_dk() every learn** | Scan: for_soc_twophase uses n=200 |
| 6 | Use n=200 as-is? | **YES** | 200 decisions in MEAN_CONVERGENCE before VARIANCE_LEARNING |
| 7 | Use FixedAlpha(0.5)? | **YES — this IS the shrinkage/graduation** | 50% prior + 50% data. The blog's "graduating" mechanism. |
| 8 | eta_override=0.01 + auto_pause? | **YES — canonical values** | eta_override=0.01 = v14 math synopsis. auto_pause = conservation. |
| 9 | P-WELFORD-A now? | **YES** | Already approved, storage only |
| 10 | Test 58? | **Storage roundtrip (P-WELFORD-A). Behavioral gate (2a).** | Welford can't recompute coordinate descent alone |
| 11 | P27 blocked on DK scoring? | **YES** | C9 requires DK weights USED in scoring, not just stored |

---

## Summary

| Prompt | What | Effort | Outcome |
|---|---|---|---|
| **0** | Discovery scan (6 scans, no code) | 30 min | ✅ COMPLETE — all params confirmed |
| **1** | P-WELFORD-A storage | 0.5d | ✅ L5 accepts Welford state |
| **2a** | Construction change (for_soc_twophase params) + behavioral gate | 1d | ✅ **Scorer learns DK weights (PROVEN by G1+G2)** |
| **2b** | Persistence + Welford tracking | 1d | ✅ DK weights + Welford in L5 store |
| **2c** | Router wiring + app startup | 1d | ✅ Learn flow writes DK to L5 per copilot |
| **3** | P26 startup read | 0.5d | ✅ Judgment memory survives restart |
| **3b** | P-CENTROID-L5-WIRE | 0.5d | ✅ **L5 centroid writes from learn flow (MEAN_CONVERGENCE only)** |
| **4** | P27 full flow test | 0.5d | ✅ L5 completion gate (ALL THREE node types) |
| **C9-FIX** | Combined fixer: domain bug + inf sentinel + JSON compat | 0.5d | **Unblocks live AGE proof** |
| | C9 proof rerun | 1h | **L5 COMPLETE (4 non-SOC domains, SOC = #132 gap)** |
| | **Total** | **~6.5d** | **Product claims become true for SDK copilots** |

---

*DK Runtime Execution Plan v5.4 · June 7, 2026*
*5 prompts (2 split into 2a/2b/2c) + Prompt 3b (centroid) + C9-FIX.*
*GAE params: LearningStrategy(DecisionCountPolicy(200), CoordinateDescentEstimator(), FixedAlpha(0.5)).*
*eta_override=0.01. auto_pause_on_amber=True. No custom cadence — use GAE phase transitions.*
*Prerequisites: #111 + #115 + #102 + GAE editable install (all done).*
*C9 = 4 non-SOC domains × 3 types = 12 cells. SOC = #132 gap.*
*After C9: 288-moat is real, Mirror shows learned insight, compounding runs.*

---

## Prompt 3b — P-CENTROID-L5-WIRE: L5 Centroid Runtime Write (0.5d)

**Why this moved:** The original plan listed P-CENTROID-L5-WIRE after
C9, reasoning "centroids work via checkpoints." But P27's gate is
"all three L5 node types." Without centroid L5 writes, P27 can only
verify 2 of 3 — and C9's 12-cell proof (4 non-SOC domains × 3 types) has
empty cells. The sequencing conflict is resolved by moving this BEFORE
P27.

**Important distinction:** `save_centroids()` (existing checkpoint
persistence) is NOT equivalent to `update_centroid()` (L5 graph node).
Checkpoints serialize the full centroid tensor for scorer restore.
L5 centroid nodes store per-(category, action) centroid vectors with
SHAPED_BY edges linking them to the causing Decision node. Both serve
different purposes. Both continue to exist.

### Answers to all 8 questions

**Q1:** YES — required before P27. See above.

**Q2: Insertion point — Option B (scoring_router.py)**

Consistent with DK and conservation L5 writes. All three L5 write
types are in the router layer, after learn:

```python
# scoring_router.py learn handler, AFTER learn_result:

# 1. Conservation L5 write (P25b — already wired)
_persist_conservation_state_l5(...)

# 2. DK re-estimation + L5 write (P-DK-RUNTIME-FULL — Prompt 2)
scorer.reestimate_dk_if_due()
persist_dk_after_reestimate(...)

# 3. Centroid L5 write (P-CENTROID-L5-WIRE — THIS PROMPT)
_persist_centroid_l5(
    scorer=scorer,
    learning_store=learning_store,
    domain=domain,
    category=learn_result.category,
    actual_action=learn_result.actual_action,
    caused_by_decision_id=learn_result.decision_id,
)
```

**Q3: Field mapping for update_centroid()**

| Field | Source | Notes |
|---|---|---|
| `domain` | `domain_config.domain` | Same as conservation/DK writes |
| `category` | `learn_result.category` | The decision's category |
| `action` | `learn_result.actual_action` | The action whose centroid was updated by `ProfileScorer.update()`. This is the ACTUAL action (the analyst's choice), because `update()` moves the centroid toward the observed factor vector for the action that was taken. |
| `centroid_vector` | Read from scorer AFTER learn | `scorer.get_centroid(category, action)` or equivalent accessor. This is the POST-update centroid. |
| `count` | From scorer | Number of decisions that have shaped this centroid |
| `eta_last` | From scorer if available | Last learning rate used. None if not exposed. |
| `caused_by_decision_id` | `learn_result.decision_id` | The decision that triggered this centroid update |

**On delta_norm:** If the P21/P22 `update_centroid()` signature includes
`delta_norm`, compute as `norm(post_centroid - pre_centroid)`. This
requires capturing the centroid BEFORE `scorer.learn()`:

```python
# BEFORE learn:
pre_centroid = scorer.get_centroid(category, action)

# learn() updates centroid in-memory
learn_result = scorer.learn(...)

# AFTER learn:
post_centroid = scorer.get_centroid(category, action)
delta_norm = sum((a - b)**2 for a, b in zip(post_centroid, pre_centroid)) ** 0.5
```

If capturing pre-centroid is impractical (requires an extra read), set
`delta_norm=None`. The centroid vector itself is the critical field.
Delta is monitoring metadata, not structural.

**Discovery required:** Read the actual `update_centroid()` signature
from `copilot_sdk/graph/protocol.py` (P21 implementation) to confirm
exact parameter names and which are required vs optional.

**Q4: Non-fatal?** YES. Same try/except/log/continue pattern:

```python
def _persist_centroid_l5(scorer, learning_store, domain, category,
                          actual_action, caused_by_decision_id):
    if learning_store is None:
        return

    # CRITICAL: Only write L5 centroid when the category is in
    # MEAN_CONVERGENCE (centroid actually updated by update()).
    # In VARIANCE_LEARNING, centroids are FROZEN — update() buffers
    # decisions for DK estimation instead. Writing an L5 centroid node
    # with SHAPED_BY edge for a frozen centroid is false provenance.
    category_phase = scorer.get_category_phase(category)
    if category_phase == "VARIANCE_LEARNING":
        return  # Centroid frozen — DK estimation active, not centroid learning

    try:
        centroid_vector = scorer.get_centroid(category, actual_action)
        if centroid_vector is None:
            return  # No centroid for this (category, action) yet
        learning_store.update_centroid(
            domain=domain,
            category=category,
            action=actual_action,
            centroid_vector=centroid_vector,
            # count, eta_last, delta_norm: discover from P21 signature
            caused_by_decision_id=caused_by_decision_id,
        )
    except Exception as e:
        logger.error(f"L5 centroid write failed for {domain}: {e}")
```

**Why the phase check matters:** Without it, a category that has been
in VARIANCE_LEARNING for 1,000 decisions would have 1,000 L5 centroid
nodes all pointing to the SAME frozen centroid vector, each falsely
claiming to be "shaped by" a different decision. This is incorrect
provenance that would mislead an auditor. The centroid stopped changing
at decision 200 — only the first 200 L5 centroid nodes are real.

**Q5: save_centroids() unchanged?** YES. L5 centroid write is ADDITIVE.
The existing checkpoint mechanism continues to work exactly as before.
Both coexist:
- `save_centroids()`: full tensor checkpoint for scorer restore
- `update_centroid()`: per-(category, action) L5 node for audit + graph

**Q6: S2P in scope?** YES. S2P uses `CompoundingScorer.from_preset("s2p")`
which shares the SDK learn path. The wiring in `scoring_router.py`
covers Trading/Purchasing/DataOps. S2P's `/api/s2p/outcome` handler
needs the same inline write (same pattern as P25b and P-DK-RUNTIME).

**Q7: SHAPED_BY edge — P27 or C9?**

- **P27 (automated):** Assert L5 centroid ROW/STATE exists after learn.
  Verify `learning_store.get_centroid(domain, category, action)` returns
  a populated dict with the expected centroid_vector.
- **C9 (manual):** Assert SHAPED_BY edge exists in AGE. Requires live
  AGE graph. `MATCH (c:L5Centroid)-[:SHAPED_BY]->(d:Decision) RETURN count(*)`

P27 tests storage correctness. C9 tests graph topology. Both are needed;
they test different things.

**Q8: Updated sequencing — P-CENTROID-L5-WIRE is now Prompt 3b.**

### Prompt 3b scope

**Files to modify:**
- `copilot_sdk/backend/scoring_router.py` — add `_persist_centroid_l5()` after DK write
- `s2p-copilot/backend/app/routers/s2p.py` — same pattern for S2P outcome
- `copilot_sdk/scoring/scorer.py` — add `get_centroid(category, action)` accessor if not already exposed

**Files NOT to modify:**
- `save_centroids()` checkpoint path — untouched
- `update_centroid()` store implementations — already exist from P21/P22
- Conservation or DK paths — already wired

### Prompt 3b tests (5)

| # | Test | What it proves |
|---|---|---|
| 1 | `test_learn_persists_centroid_to_l5` | After learn (MEAN_CONVERGENCE), L5 store has centroid for (domain, category, action) |
| 2 | `test_centroid_l5_has_caused_by_decision_id` | SHAPED_BY provenance: which decision caused this centroid update |
| 3 | `test_centroid_l5_nonfatal` | L5 failure → learn continues, checkpoint still works |
| 4 | `test_centroid_l5_coexists_with_checkpoint` | Both save_centroids() and update_centroid() fire on same learn — no interference |
| 5 | `test_centroid_l5_skipped_in_variance_learning` | After 200 decisions (VARIANCE_LEARNING), centroid L5 write is SKIPPED — no false provenance. DK L5 write fires instead. |

### Required accessor additions

```python
# In CompoundingScorer (scorer.py):

def get_centroid(self, category: str, action: str) -> list[float] | None:
    """Read post-update centroid for (category, action). Read-only."""
    # Thin wrapper over ProfileScorer centroid access
    ...

def get_category_phase(self, category: str) -> str:
    """Return 'MEAN_CONVERGENCE' or 'VARIANCE_LEARNING' for a category.
    Used by centroid L5 write to determine if centroid is frozen."""
    # Read from ProfileScorer._category_states[category_index].phase
    ...
```

**Discovery required:** Verify how `CategoryState.phase` is accessed
in ProfileScorer. The phase field may be a string or an enum.

### L5 write ordering note

The L5 write order in the router is conservation (P25b) → DK (Prompt 2c)
→ centroid (Prompt 3b). The spec's intended order is centroid → DK →
conservation (matching the data flow: centroid update first, DK estimation
second, conservation check last). The writes are independent — all
reference a Decision node that already exists — so order doesn't affect
correctness. However, if the team wants semantic clarity, the three
inline calls can be reordered in `scoring_router.py` during Prompt 3b
to match the spec.

### P27 test runtime note

P27's full-flow test requires 200+ decisions to trigger the VARIANCE_LEARNING
phase transition. Running 200 score+learn cycles takes 1-3 minutes in
automated tests. This is acceptable for an integration test that runs
once per suite. If faster testing is needed, the test fixture can
construct a scorer with a reduced phase threshold (e.g., `DecisionCountPolicy(n=10)`
for test-only) — but this should be clearly marked as test-only and not
affect production construction.

### Stop conditions

- Do NOT modify save_centroids() checkpoint behavior
- Do NOT change centroid computation (that's ProfileScorer.update())
- Do NOT change DK or conservation paths
- Do NOT broaden GraphStore
- Do NOT write L5 centroid nodes when category is in VARIANCE_LEARNING
  (centroid is frozen — false SHAPED_BY provenance)
- If `get_centroid(category, action)` accessor doesn't exist, add it
  as a thin wrapper (read-only, no computation) — do NOT restructure scorer
- If `get_category_phase(category)` accessor doesn't exist, add it
  as a thin wrapper reading CategoryState.phase — do NOT restructure scorer

---

## Updated Prompt Sequence (v5)

```
Prompt 0: DISCOVERY SCAN           (30 min) ✅ COMPLETE
Prompt 1: P-WELFORD-A              (0.5d)   ✅ storage/protocol
Prompt 2a: CONSTRUCTION CHANGE     (1d)     ✅ construction + behavioral gate
──── GATE: G1+G2 must pass ────
Prompt 2b: PERSISTENCE + WELFORD   (1d)     ✅ dk_persistence.py + L5 writes
Prompt 2c: ROUTER + STARTUP        (1d)     ✅ DK wiring + app init
Prompt 3: P26 STARTUP-READ          (0.5d)   ✅ warm-start from L5
Prompt 3b: P-CENTROID-L5-WIRE       (0.5d)   ✅ L5 centroid runtime write
Prompt 4: P27 FULL-FLOW-TEST        (0.5d)   ✅ ALL THREE node types + Welford
C9-FIX: COMBINED FIXER              (0.5d)   ← CURRENT: domain bug + inf + compat
C9: L5 PROOF RERUN                   (1h)    ← NEXT: 4 domains × 3 types = 12 cells
```

**Total: ~6.5d** (Prompts 0–4 complete. C9-FIX + C9 rerun remaining.)

---

## C9-FIX — Combined Live AGE Fixer (0.5d)

**Date:** June 7, 2026
**Context:** Prompts 0–4 complete. P27 passed. C9 live AGE proof
attempted and found 3 code issues blocking ConservationState persistence.
All L5Centroid, L5DKWeight, and Welford fields are confirmed present
in live AGE for 4 non-SOC domains.

### Answers to All 10 Questions

**Q1: Combined fixer.** Option A — fix Issues A+B+C together. All
three are small (domain passthrough, infinity sentinel, list/string
compat). Combined saves one review cycle. ~0.5d total.

**Q2: theta_min = inf representation: Option A — sentinel string.**

`"Infinity"` stored as TEXT, decoded to `float("inf")` on read.

Rationale:
- Preserves semantic value (infinity IS the correct theta_min when α=0 or V=0)
- No information loss (unlike cap or null)
- `json.dumps(float("inf"))` fails in standard JSON — so store as TEXT, not as a JSON numeric
- Readback: `float(value) if value != "Infinity" else float("inf")`
- Same pattern for negative infinity if ever needed: `"-Infinity"`

Implementation in AGE serialization:
```python
# Write:
theta_min_str = "Infinity" if math.isinf(theta_min) else str(theta_min)
# In Cypher: theta_min: _S(theta_min_str)  (stored as string)

# Read:
theta_min_raw = row.get("theta_min", "0")
theta_min = float("inf") if str(theta_min_raw) == "Infinity" else float(theta_min_raw)
```

**Q3: NaN always rejected.** YES. Add validation:
```python
if math.isnan(theta_min):
    raise ValueError("theta_min cannot be NaN")
```
NaN in conservation metrics means a computation error upstream.
Log error and skip L5 write rather than persisting garbage.

**Q4: C9 with infinite theta_min?** After Issue A is fixed, seeded
domains with 200+ decisions should have finite theta_min. Infinite
theta_min is legitimate ONLY for zero-data state (no verified
decisions yet). C9 proof domains all have 200+ seeded decisions, so
theta_min MUST be finite for them. If still infinite after the fixer,
that's a bug.

**Q5: Explicit domain passthrough.** YES. The route knows the domain.
Pass it through all conservation count paths. Do not rely on
`graph_store.domain` or implicit state.

**Q6: JSON/list read compat.** YES. `get_dk_weights()` and
`get_conservation_state()` read paths should accept both JSON strings
and AGEClient-decoded Python lists/dicts. Keep validation strict
(correct types, correct dimensions). Do not change write format.

**Q7: C9 without SOC?** YES. C9 passes for **4 non-SOC domains**
(Trading, Purchasing, DataOps, S2P). SOC is documented as #132 gap.

C9 proof matrix becomes:

| Domain | L5Centroid | L5DKWeight | L5ConservationState | SHAPED_BY |
|---|---|---|---|---|
| Trading | ✅ 2 | ✅ 1 | **after fixer** | ✅ 2 |
| Purchasing | ✅ 2 | ✅ 1 | **after fixer** | ✅ 2 |
| DataOps | ✅ 2 | ✅ 1 | **after fixer** | ✅ 2 |
| S2P | ✅ 2 | ✅ 1 | **after fixer** | ✅ 2 |
| SOC | — | — | — | — | **#132 gap** |

4 domains × 3 node types = **12 cells** (not 15). SOC adds 3 after #132.

**Q8: TRIGGERED_BY edge?** The C9 seeding should exercise a status
TRANSITION (e.g., RED→GREEN as decisions accumulate). If the seeding
run produces a transition, TRIGGERED_BY edge MUST be present. If no
transition occurred (conservation stayed GREEN throughout all 200+
decisions), classify as "transition not exercised" — do not fake it.

**Recommended seeding strategy for TRIGGERED_BY:**
1. Start copilot with zero decisions → conservation = RED (V=0)
2. Seed 10 decisions → still RED (insufficient data)
3. Seed 200+ decisions → conservation transitions to GREEN
4. That RED→GREEN transition produces a TRIGGERED_BY edge
5. Verify edge exists in AGE

**Q9: Old status-null Decision nodes?** NO. Not in this fixer.
Later migration item. New decisions have correct status + domain.

**Q10: Proof standard to unblock next roadmap item?**

**4 non-SOC domains × 3 node types + SHAPED_BY edges.**

| Requirement | Status |
|---|---|
| 4 domains × L5Centroid | ✅ Present |
| 4 domains × L5DKWeight + Welford | ✅ Present |
| 4 domains × L5ConservationState | **After fixer** |
| SHAPED_BY edges (centroid→decision) | ✅ Present |
| TRIGGERED_BY edge (conservation→decision) | After seeding exercises transition |
| SOC (all 3 types) | #132 gap — documented, not blocking |
| DKWeight readback | After Issue C compat fix |

### Combined Fixer Spec

**Effort:** 0.5d · **Risk:** Low · **Repos:** copilot-sdk, ci-platform

**Fix A — Explicit-domain conservation metrics:**

File: `copilot-sdk/copilot_sdk/backend/conservation_utils.py`

`compute_conservation_metrics()` and its internal count helpers must
use the explicit `domain` parameter for ALL count queries. The bug:
some count paths fall through to `graph_store.domain` (which may be
None or wrong for AGE-backed stores where the store serves all domains).

```python
# BEFORE (broken — implicit domain):
verified = graph_store.count_verified_decisions()  # uses store.domain

# AFTER (fixed — explicit domain):
verified = graph_store.count_verified_decisions(domain)  # route's domain
```

Discovery required: read `compute_conservation_metrics()` to identify
every count call. Ensure EACH one receives the explicit `domain` arg.
The fix is: grep for every `count_` call in the function, verify each
passes `domain`.

Tests:
- `test_conservation_metrics_explicit_domain` — construct store WITHOUT
  `.domain` attribute, pass explicit domain, verify nonzero counts
- `test_conservation_metrics_live_age_compat` — if feasible, test
  against AGE adapter with multi-domain data

**Fix B — Non-finite theta_min AGE serialization:**

File: `ci-platform/ci_platform/graph/age_graph_store.py`

In `update_conservation_state()`:
```python
import math

# Validate: reject NaN
if math.isnan(theta_min):
    raise ValueError(f"theta_min cannot be NaN for domain {domain}")

# Serialize: infinity as sentinel string
theta_min_serialized = "Infinity" if math.isinf(theta_min) else theta_min
# Use _S(theta_min_serialized) in Cypher for string sentinel
# OR use numeric for finite values and string for infinite
```

In `get_conservation_state()`:
```python
# Deserialize: sentinel back to float
raw = row.get("theta_min", "0")
if str(raw) == "Infinity":
    theta_min = float("inf")
else:
    theta_min = float(raw)
```

Tests:
- `test_conservation_state_infinite_theta_min_roundtrip` — write inf,
  read inf, verify `math.isinf(result["theta_min"])`
- `test_conservation_state_nan_rejected` — write NaN, verify ValueError
- `test_conservation_state_finite_unchanged` — write 0.467, read 0.467

**Fix C — DKWeight JSON/list read compatibility:**

File: `ci-platform/ci_platform/graph/age_graph_store.py`

In `get_dk_weights()`:
```python
# Accept both JSON string and already-decoded list
weight_raw = row.get("weight_json")
if isinstance(weight_raw, str):
    weight_tensor = json.loads(weight_raw)
elif isinstance(weight_raw, list):
    weight_tensor = weight_raw  # AGEClient already decoded
else:
    raise ValueError(f"Unexpected weight_json type: {type(weight_raw)}")

# Same pattern for Welford vector fields:
for field in ["confirmed_mean_json", "confirmed_m2_json",
              "overridden_mean_json", "overridden_m2_json",
              "all_mean_json", "all_m2_json"]:
    raw = row.get(field)
    if raw is None:
        continue
    if isinstance(raw, str):
        decoded = json.loads(raw)
    elif isinstance(raw, list):
        decoded = raw
    else:
        raise ValueError(f"Unexpected {field} type: {type(raw)}")
```

Tests:
- `test_dk_weight_read_json_string` — write as JSON, read succeeds
- `test_dk_weight_read_decoded_list` — simulate AGEClient decoding, read succeeds
- `test_welford_read_both_formats` — same for Welford fields

### Regression

```powershell
Set-Location "$env:CLAUDE_PROJECTS\copilot-sdk"
python -m pytest tests/ -q --timeout=120

Set-Location "$env:CLAUDE_PROJECTS\ci-platform"
python -m pytest tests/ -q --timeout=120
python -m mypy ci_platform/graph --ignore-missing-imports --no-incremental
```

### After Fixer: C9 Proof Rerun

```powershell
# 1. Restart all 4 SDK copilots via demo.py
# 2. Exercise score→learn loops (200+ per copilot for DK phase transition)
# 3. Query AGE:
#    MATCH (c:L5Centroid) RETURN c.domain, count(c) ORDER BY c.domain
#    MATCH (w:L5DKWeight) RETURN w.domain, count(w) ORDER BY w.domain
#    MATCH (cs:L5ConservationState) RETURN cs.domain, cs.status ORDER BY cs.domain
#    MATCH (c:L5Centroid)-[:SHAPED_BY]->(d:Decision) RETURN c.domain, count(*)
#    MATCH (cs:L5ConservationState)-[:TRIGGERED_BY]->(d:Decision) RETURN cs.domain, count(*)
# 4. Verify: 4 domains × 3 types = 12 cells populated
# 5. Verify: SHAPED_BY edges exist
# 6. Verify: TRIGGERED_BY edge exists if transition was exercised
# 7. Mark SOC as #132 gap
```

**C9 PASSES when:** 12 cells populated + SHAPED_BY edges present +
DKWeight has Welford fields + ConservationState has finite theta_min.
SOC is documented gap. TRIGGERED_BY is "present if exercised."

### Stop conditions

- Do NOT change conservation formulas
- Do NOT cap infinity to a finite value
- Do NOT accept NaN anywhere
- Do NOT migrate old status-null Decision nodes
- Do NOT modify write format for DKWeight (only read compatibility)
- Do NOT touch SOC code (that's #132)
- Do NOT modify DK estimation or centroid update paths

### Updated C9 Definition

**Original:** 5 domains × 3 node types = 15 cells.
**Revised:** 4 non-SOC domains × 3 node types = 12 cells + SOC
documented as #132 gap. SOC adds 3 cells after #132 ships.

L5 COMPLETE (revised): all SDK/S2P copilots have judgment memory
in the graph. SOC judgment memory gates on #132 SOC-OPTION-C.
