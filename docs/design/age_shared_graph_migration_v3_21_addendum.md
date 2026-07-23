# AGE Shared Graph Migration — v3.21 Design Addendum

**Date:** July 23, 2026
**Authority:** v3.20 + o1 design review (July 23, 2026)
**Supersedes:** v3.20 §3.4.1–§3.4.3 (DualWriteStore identity/delegation),
  §7.1/§7.4 (Phase 3 flip env vars)
**Status:** APPROVED for implementation

---

## §3.4.1-REVISED: Identity — Scorer Governed Writes (replaces raw→governed bridge)

v3.20 specified a raw-to-governed transformation inside DualWriteStore.
This is replaced by a scorer-governed-write design:

**CompoundingScorer.score()** calls `write_governed_decision()` instead
of `write_decision()` when `governed_writes=True` (feature gate).

### ID generation: V2 generate_decision_id()

New method on ProtocolV2GraphStore:

```python
def generate_decision_id(self, domain: str) -> str:
    """Generate a prefixed, unique decision ID for this domain."""
```

Implementations:
- **SQLiteGraphStore**: applies configured `decision_id_prefix` + UUID.
  Formalizes the prefix logic currently embedded in `write_decision()`.
- **InMemoryGraphStore**: bare UUID (preserves test behavior).
- **AGEGraphStoreAdapter**: bare UUID (AGE DEC-* prefix is a separate scheme).
- **DualWriteStore**: delegates to `primary.generate_decision_id(domain)`.
  SQLite remains the identity authority during dual-write.

### Scorer governed-write flow

```
1. decision_id = store.generate_decision_id(domain)     # prefixed
2. store.write_governed_decision(
       decision_id=decision_id,
       domain=domain,
       category=category,
       category_index=category_index,
       recommended_action=action,
       recommended_index=recommended_index,
       confidence=confidence,
       probabilities=probabilities,
       factor_vector=factor_vector,
       factor_names=list(preset.shape.factor_names),
       source="compounding_scorer",
       scorer_version="copilot_sdk.compounding_scorer.v1",
       preset_version=f"{preset.name}.v1",
       factor_schema_version=f"{preset.name}.factor_schema.v1",
       metadata=decision_metadata,
   )
3. ScoreResult.decision_id = decision_id                 # already known
4. Later: store.write_outcome(decision_id, ..., domain=domain)  # OD-7
```

DualWriteStore sends identical `write_governed_decision()` args to both
SQLite and AGE. Both get the same prefixed ID. No bridge needed.

### Feature gate

- `SCORER_GOVERNED_WRITES=1` — process-level env var.
- Read once at scorer construction. Passed through FreshScorerProxy.
- Default: `False` (raw `write_decision()` path unchanged).
- Trading enables for Phase 3. Purchasing/DataOps enable at Phase 4.
- When enabled, scorer requires `isinstance(store, ProtocolV2GraphStore)`
  at construction. Fails with clear message if store is not V2.

### Canonical version fields

| Field | Value | Bump rule |
|---|---|---|
| source | `"compounding_scorer"` | Changed only if scorer algorithm changes |
| scorer_version | `"copilot_sdk.compounding_scorer.v1"` | Bump on scoring contract change |
| preset_version | `f"{preset.name}.v1"` | Bump on preset shape/weight change |
| factor_schema_version | `f"{preset.name}.factor_schema.v1"` | Bump on factor addition/removal |

---

## §3.4.2-REVISED: DualWriteStore delegation (replaces transformation table)

| Method | Behavior |
|---|---|
| `write_decision()` | **Primary only.** Logs SKIPPED for secondary. Legacy path. |
| `write_governed_decision()` | Both stores, identical args. Caller provides stable ID. |
| `write_outcome(domain=...)` | Both stores, identical args. OD-7 compound identity. |
| `generate_decision_id(domain)` | Delegates to primary. |
| All other V2 writes | Both stores, identical args. Secondary failure logged. |
| All reads | Primary only. |
| Lifecycle (archive, reset, close) | Both stores. Secondary failure logged. |

---

## §3.4.7-NEW: Shared-graph authorization

### Authorization grammar

Exact `(writer_domain, graph_name)` pairs. Format: comma-separated.

**Factory level:**
```
SHARED_GRAPH_AUTHORIZED=trading:soc_graph
```
- Factory permits `soc_graph` only when `f"{domain}:{graph}"` is listed.
- Without this var, `soc_graph` is rejected (existing behavior).
- Multiple pairs: `trading:soc_graph,purchasing:soc_graph`

**Per-copilot level (Trading example):**
```
TRADING_SHARED_GRAPH_AUTHORIZED=trading:soc_graph
```
- Required in combination with full TRADING_ACTIVE_* suite.
- Must match exactly. `soc:soc_graph` does NOT authorize Trading.

### Factory + graph_status interaction

1. Factory checks `SHARED_GRAPH_AUTHORIZED` for `dual_write` backend.
2. Trading graph_status checks `TRADING_SHARED_GRAPH_AUTHORIZED` for
   active AGE path.
3. Both must pass. Generic `GRAPH_BACKEND=age` downgrade is unchanged.
4. Domain isolation is structural: every Decision carries `domain`
   in AGE. Authorization is operational: prevents misconfiguration.

---

## §7.1-REVISED: Phase 3 Trading environment

### Dual-write phase (step 1):
```
GRAPH_BACKEND=dual_write
GRAPH_DSN=host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres
GRAPH_NAME=soc_graph
SHARED_GRAPH_AUTHORIZED=trading:soc_graph
SCORER_GOVERNED_WRITES=1
```

### Active-read/flip phase (step 2, after compare_all gate):
```
TRADING_ACTIVE_GRAPH_BACKEND=age
TRADING_ACTIVE_AGE_DSN=host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres
TRADING_ACTIVE_AGE_GRAPH=soc_graph
TRADING_ACTIVE_AGE_DOMAIN=trading
TRADING_SHARED_GRAPH_AUTHORIZED=trading:soc_graph
TRADING_ACTIVE_AGE_TEST_MODE=0
TRADING_SHADOW_AGE=0
SCORER_GOVERNED_WRITES=1
```

### Phase 4 equivalents:
```
SHARED_GRAPH_AUTHORIZED=purchasing:soc_graph
PURCHASING_SHARED_GRAPH_AUTHORIZED=purchasing:soc_graph
SCORER_GOVERNED_WRITES=1
```

---

## Implementation order

| Step | Scope | Depends on |
|---|---|---|
| 1 | This design addendum (v3.21) | — |
| 2 | V2 generate_decision_id() — 4 stores + protocol | — |
| 3 | Scorer governed branch + feature gate + versions | Step 2 |
| 4 | DualWrite ID generation delegation | Step 2 |
| 5 | Factory pair authorization | — |
| 6 | Trading active shared-graph authorization | Step 5 |
| 7 | Full compare_all() + outbox gate | Steps 2-6 |
| 8 | Active AGE flip | Step 7 passes |

---

*v3.21 Addendum · July 23, 2026*
*Replaces: §3.4.1-§3.4.3 (DualWrite bridge → scorer governed writes)*
*Replaces: §7.1/§7.4 (Phase 3 env vars)*
*Adds: §3.4.7 (shared-graph authorization grammar)*
