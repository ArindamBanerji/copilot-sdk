# S2P FIX-B What-If — Phase B Results v1
**Date:** 2026-08-04  
**soc_graph touched:** NO

Phase B was run in disposable AGE graphs only. The temporary runtime patch was
S2P-scoped, then reverted and verified byte-for-byte by SHA-256 hash.

## Part 1: Density Query

### P1-Setup

Sandbox: `protocol_v2_test_s2p_active_61c1f7a27819`.

The corrected A′ wrapper seeded the active S2P entity shape and added 500
synthetic incoming `DECIDED_ON` Decision hubs for `S2P-INV-0003`.

| Label | Count |
|---|---:|
| Activity | 4 |
| Category | 5 |
| Commodity | 14 |
| CommodityIndex | 1 |
| ComplianceHistory | 1 |
| ComplianceRule | 5 |
| Contract | 33 |
| ContractClause | 1 |
| Decision | 550 |
| Factor | 7 |
| GoodsReceipt | 51 |
| Invoice | 50 |
| PurchaseOrder | 50 |
| Supplier | 10 |
| ProcessModel | 1 |

`DECIDED_ON` edges: 550. The invoice index was created successfully with:

```sql
CREATE INDEX phaseb_invoice_03fa03c4
ON "protocol_v2_test_s2p_active_61c1f7a27819"."Invoice"
USING btree
(agtype_access_operator(VARIADIC ARRAY[properties, '"invoice_id"'::agtype]));
```

### B1: Query Variants

AGE accepted directed relationships and rejected the label-expression form in
the third variant with a syntax error near `:`.

| Variant | Cold ms | W1 ms | W2 ms | W3 ms | Rows | Entities present? | Crowded? | Index? |
|---|---:|---:|---:|---:|---:|---|---|---|
| V1 undirected `-[]-` | 28.961 | 5.923 | 7.709 | 6.201 | 100 | No | Yes | Yes |
| V2 directed outgoing `-[]->` | 4.152 | 5.447 | 0.990 | 0.853 | 7 | Yes, all 5 | No | Yes |
| V3 label-filtered | syntax error | — | — | — | 0 | No | — | Yes |
| V2 directed outgoing `-[]->` | 1.436 | 2.962 | 0.792 | 0.618 | 7 | Yes, all 5 | No | No |
| V3 label-filtered | syntax error | — | — | — | 0 | No | — | No |

V1 returned 100 rows dominated by incoming Decision neighbors; the five factor
entities were pushed out by `LIMIT 100`. V2 returned the outgoing factor
neighbors and excluded incoming `DECIDED_ON` hubs. The winning query was:

```cypher
MATCH (e:Invoice {invoice_id: 'S2P-INV-0003'})-[]->(n)
WHERE n.domain = 's2p'
RETURN n
LIMIT 100
```

SQL column declaration: `AS (n agtype)`. The index was not required for this
small sandbox after the label anchor was present, although an
`Invoice.invoice_id` index remains appropriate at production scale.

### B2: Bounded Duplicate

`DuplicateScore` itself has no fixed percentage tolerance; it compares sibling
Invoice amounts using its similarity calculation. The experiment used a 5%
bounded candidate window:

```cypher
MATCH (:Supplier {supplier_id: 'SUP-003'})
  <-[:SUPPLIED_BY]-(sib:Invoice)
WHERE sib.invoice_id <> 'S2P-INV-0003'
  AND sib.amount > 3592.615
  AND sib.amount < 3970.785
RETURN sib
LIMIT 20
```

| Run | Latency ms | Rows |
|---:|---:|---:|
| 1 | 2.019 | 0 |
| 2 | 0.482 | 0 |
| 3 | 0.478 | 0 |
| 4 | 0.383 | 0 |
| 5 | 0.428 | 0 |

Bounded by `LIMIT`: YES. Targeted duplicate lookup is viable: YES. The zero
rows reflect the fixture distribution, not a query failure.

## Part 2: Runtime Patch + Perturbation

### P2-Step 1: Code Scan

The unmodified shared AGE store query in
`ci-platform/ci_platform/graph/age_graph_store.py:3143-3164` was:

```python
MATCH p = (e {entity_id: <entity_id>})-[*1..<hop_count>]-(n)
WHERE n.domain = <domain>
RETURN p
LIMIT 100
```

`_node_to_dict` at `age_graph_store.py:3190-3230` preserves a path result as a
dictionary containing `p`; it does not turn that path into a vertex dictionary.
The S2P reader originally delegated to this method at
`s2p-copilot/backend/app/graph/s2p_graph_reader.py:118-130`.

The original `_resolve_graph_context` in
`s2p-copilot/backend/app/routers/s2p.py:138-161` accepted a list only if a row
passed `_graph_context_row_is_domain_specific` at `:164-170`. That predicate
checks `row.get("node")`; a path row such as `{"p": "...::path"}` has no
`node`, so it was rejected and the endpoint passed `context=None` to
`compute_all_factors`.

The factor pipeline accepts a list of neighbor dictionaries or
`{"neighbors": [...]}`. Each entry can be a direct property dictionary or a
`{"node": property_dictionary}` wrapper; `_node` in
`s2p-copilot/backend/app/domains/s2p/factors.py:95-99` unwraps the latter.

The winning query returns direct vertex rows (`RETURN n`, `AS (n agtype)`),
which can be normalized to `{"node": {...properties...}}`. This bridges the
gap without changing the shared generic query used by other copilots.

### P2-Step 2: Patch Applied

The patch was temporary and was not retained.

| File | Temporary lines | Old | New |
|---|---:|---|---|
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py` | 132-214 | Only generic `query_context` | Added S2P-only `query_direct_context(invoice_id, limit=100)` using directed outgoing `RETURN n`, plus `query_duplicate_context(invoice_id, supplier_id, amount, limit=20)` |
| `s2p-copilot/backend/app/routers/s2p.py` | 141-150 | `_resolve_graph_context` called `reader.query_context(..., max_depth=2)` | Called the direct method and appended bounded duplicate candidates |

The temporary reader unwrapped the runtime chain
`S2PActiveAGEGraphStore → AGEGraphStoreAdapter → AGEGraphStore`.
The shared `AGEGraphStore.query_context` was not changed.

### P2-Step 4: Baseline Score

The backend ran on port 8099 with the sandbox graph and
`S2P_ACTIVE_AGE_TEST_MODE=1`. Request identity was
`event_id="S2P-INV-0003"`, so the runtime selected the target invoice.

| Field | Value |
|---|---|
| HTTP | 200 |
| Latency | 398 ms |
| Action | `refer_to_specialist` |
| Confidence | 0.7208302462 |
| Factor vector | `[0.1, 0.0, 0.0, 0.04, 0.515, 0.822, 0.15, 0.5]` |
| `commodity_index_correlation` | 0.822 |

The graph-derived values differ from the fixture baseline, independently
showing that the temporary patch stopped fixture coincidence before perturbing.

### P2-Step 5: Perturbed Score

The target Commodity was located through the Invoice's
`HAS_COMMODITY_INDEX` edge. Its volatility changed from `0.822` to `0.123`.

| Field | Value |
|---|---|
| HTTP | 200 |
| Latency | 252 ms |
| Action | `refer_to_specialist` |
| Confidence | 0.7503919254 |
| Factor vector | `[0.1, 0.0, 0.0, 0.04, 0.515, 0.123, 0.15, 0.5]` |
| `commodity_index_correlation` | 0.123 |

### PERTURBATION VERDICT

`commodity_index_correlation` changed: YES (`0.822 → 0.123`).

GRAPH-BACKED: YES. The endpoint genuinely read the perturbed Commodity
property from the disposable AGE graph. This is not fixture coincidence.

### P2-Step 6: Factor Verification

| Factor | Baseline | Perturbed | Changed? | Verdict |
|---|---:|---:|---|---|
| `match_status` | 0.100 | 0.100 | No | Stable, graph-derived |
| `amount_variance_ratio` | 0.000 | 0.000 | No | Stable, graph-derived |
| `duplicate_score` | 0.000 | 0.000 | No | Stable; no bounded sibling matched |
| `supplier_exception_history` | 0.040 | 0.040 | No | Stable, graph-derived |
| `payment_terms_impact` | 0.515 | 0.515 | No | Stable, graph-derived |
| `commodity_index_correlation` | 0.822 | 0.123 | Yes | Required perturbation passed |
| `tax_regulatory_compliance` | 0.150 | 0.150 | No | Stable, graph-derived |
| `environmental_risk` | 0.500 | 0.500 | No | Outside the seven-factor spike |

Only the perturbed factor moved. This rules out a malformed context vector that
would cause unrelated factors to change together.

## Phase B Synthesis

### Winning Query Shape

Direct context:

```cypher
MATCH (e:Invoice {invoice_id: 'S2P-INV-0003'})-[]->(n)
WHERE n.domain = 's2p'
RETURN n
LIMIT 100
```

SQL declaration: `AS (n agtype)`.

Duplicate lookup:

```cypher
MATCH (:Supplier {supplier_id: 'SUP-003'})
  <-[:SUPPLIED_BY]-(sib:Invoice)
WHERE sib.domain = 's2p'
  AND sib.invoice_id <> 'S2P-INV-0003'
  AND sib.amount > 3592.615
  AND sib.amount < 3970.785
RETURN sib
LIMIT 20
```

SQL declaration: `AS (sib agtype)`. An `Invoice.invoice_id` AGE property index
is recommended for production scale; the direct query remained fast without it
in this sandbox.

### Track-2 Code Change Shape

- Reader method: `S2PGraphReader.query_direct_context(invoice_id: str,
  limit: int = 100) -> list[dict[str, Any]]`.
- Duplicate method: `S2PGraphReader.query_duplicate_context(invoice_id: str,
  supplier_id: str, amount: float, limit: int = 20) -> list[dict[str, Any]]`.
- `_resolve_graph_context`: call the S2P direct method, then merge bounded
  sibling candidates.
- Normalization: generic path rows `{"p": "...::path"}` become direct
  normalized rows `{"node": {properties...}}`.
- Scope: the shared generic `AGEGraphStore.query_context` remains unchanged;
  permanent implementation should expose this S2P-specific capability without
  relying on an unbounded private-wrapper walk.

### GRAPH-BACKED PROOF

Perturbation moved the factor: YES.  
Endpoint is genuinely graph-backed: YES, under the temporary S2P-scoped patch.

## What Surprised Us

1. The initial temporary method failed not because AGE was unavailable, but
   because S2P runtime construction has two wrappers around `AGEGraphStore`.
   The runtime chain is `S2PActiveAGEGraphStore → AGEGraphStoreAdapter →
   AGEGraphStore`.
2. The generic undirected query was fast in the small sandbox but still
   semantically wrong: `LIMIT 100` hid all factor entities behind Decision
   hubs.
3. AGE rejected the natural `n:Supplier OR n:PurchaseOrder ...` predicate, so
   directed traversal is both simpler and portable for this AGE runtime.
4. The graph-backed baseline action and confidence differed materially from
   the fixture vector, exposing the prior fallback before perturbation.

## Remaining Gaps Before C/D

1. Implement the temporary reader method as a permanent, typed S2P-specific AGE
   read capability; do not make other copilots depend on S2P labels.
2. Decide and document the production duplicate tolerance/window policy. The
   factor itself has no fixed percentage tolerance; this experiment used 5%.
3. Add permanent tests for direct context normalization, density exclusion of
   Decision hubs, bounded duplicate lookup, and commodity perturbation in a
   disposable AGE graph.
4. The temporary endpoint trial used a scratch port and sandbox config; no
   production deployment behavior was changed by this experiment.

## Patches Reverted

| File | Reverted? | Verified? |
|---|---|---|
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py` | YES | YES — SHA-256 restored to `82A890F84D0097A8AB95F74039B807D07698E021D9D92F70DC7E6CFB718FEDFB` |
| `s2p-copilot/backend/app/routers/s2p.py` | YES | YES — SHA-256 restored to `5A041E12CFA6DE5A8B5440ECE23EC1BFE73A2FD14165EED22D3CB1E49B6B4A0F` |

All temporary source changes were reverted. No production or test file was left
modified.

## Cleanup

- Sandboxes dropped: YES. All nine `protocol_v2_test_s2p_active_*` graphs
  present in the database were dropped; zero remain.
- Scripts deleted: YES. `_phase_b.py` and `_phase_b_perturb.py` are absent.
- Backend stopped: YES. Port 8099 is no longer listening.
- Production files unmodified: YES.
- `soc_graph` untouched: YES. It was excluded from all create, write, and drop
  operations and remains present.

## READY FOR TRACK-2 IMPLEMENTATION: YES

The Phase B spike validates the FIX-B premise and identifies the production
query shape: label-anchored, directed-outgoing, domain-filtered direct context
with a bounded sibling lookup. The permanent Track-2 implementation can now be
made and tested without changing the shared generic AGE traversal.
