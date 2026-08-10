# S2P FIX-B What-If — Phase A′ Results v1
**Date:** 2026-08-04  
**Follows:** Phase A (A1 FAIL)  
**soc_graph touched:** NO

> Repository note: the requested definitive reference file `docs/design/s2p_fix_b_whatif_phase_a_corrected_v1.md` was absent from this checkout. The A′ specification in the task message was used as the experiment protocol; this drift is recorded explicitly rather than silently treated as resolved.

## Step 0: Model Source Resolution

### Active builder

The active builder is `s2p-copilot/backend/app/seed_graph.py:141-367`, function:

```python
def seed_s2p_graph(seed: int = 42) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
```

`seed_graph(graph=..., seed=...)` validates the graph name and returns the tuple from `seed_s2p_graph`; it does not write AGE data [s2p-copilot/backend/app/seed_graph.py:116-138]. No third entity-subgraph builder was found in `s2p-copilot/backend/app/`; the other seed-like functions are the same module’s helpers and the separate S2P active graph/factory functions, not another entity writer.

### Edge labels produced by the active builder

The builder emits the active contract’s Decision/entity edges for each invoice:

`DECIDED_ON`, `SUPPLIED_BY`, `MATCHED_TO`, `IN_CATEGORY`, `VIOLATES`, and `EVALUATED_WITH` [s2p-copilot/backend/app/seed_graph.py:257-271]. It also emits `HAS_COMMODITY_INDEX`, `GOVERNED_BY`, and `RECEIVED_AS`, but only from the first invoice to one demo node each [s2p-copilot/backend/app/seed_graph.py:273-310]. It emits `COMPLIANCE_RECORD` only for the first supplier’s demo compliance-history node [s2p-copilot/backend/app/seed_graph.py:312-324], plus process edges `CONTAINS`, `FOLLOWS`, and conditional `BOTTLENECK_AT` [s2p-copilot/backend/app/seed_graph.py:326-365].

### Entity types linked to Invoice before wrapper additions

| Entity/relationship | Builder behavior |
|---|---|
| `Decision` via `DECIDED_ON` | Yes, every invoice |
| `Supplier` via `SUPPLIED_BY` | Yes, every invoice with a known supplier |
| `PurchaseOrder` via `MATCHED_TO` | Yes, every invoice |
| `GoodsReceipt` via `RECEIVED_AS` | Only one demo receipt, attached to the first invoice |
| `Commodity` | No `Commodity` node; only one `CommodityIndex` demo node |
| `Contract` | No `Contract` node; only one `ContractClause` demo node |

### Domain and identity before wrapper

The builder sets `domain='s2p'` and `provenance='seed'` on `Decision` nodes [s2p-copilot/backend/app/seed_graph.py:209-224], but not on the other nodes or edges. It does not set `entity_id` on any node. The entity natural-key properties are `invoice_id`, `supplier_id`, `po_id`, and the active builder’s demo keys for the other labels [s2p-copilot/backend/app/seed_graph.py:174-191,225-255,273-307].

### Wrapper additions required

The wrapper had to add:

1. `domain='s2p'` and `provenance='seed'` to every node and edge;
2. a `seed_node_id` write key so scratch edges could match deterministic nodes;
3. `entity_id` to Invoice, Supplier, PurchaseOrder, GoodsReceipt, Commodity, and Contract;
4. a per-invoice GoodsReceipt node and `RECEIVED_AS` edge;
5. a per-invoice Commodity node with `volatility` and `HAS_COMMODITY_INDEX` edge;
6. a per-invoice Contract node and `GOVERNED_BY` edge;
7. `amount` on each PurchaseOrder, because `AmountVarianceRatio` reads PO amount [s2p-copilot/backend/app/domains/s2p/factors.py:169-177].

## Step 1: Wrapper Details

### Builder used

The deleted scratch wrapper called `app.seed_graph.seed_s2p_graph(seed=42)`, then wrote the returned node/edge plan through raw AGE `CREATE` statements in the disposable graph. It did not alter the builder or any repository source.

### Entity ID mapping

| Label | Natural key | Wrapper `entity_id` |
|---|---|---|
| `Invoice` | `invoice_id` | `invoice_id` |
| `Supplier` | `supplier_id` | `supplier_id` |
| `PurchaseOrder` | `po_id` | `po_id` |
| `GoodsReceipt` | generated `GR-<po_number>` | same generated GR key |
| `Commodity` | fixture metadata `commodity` | commodity name, e.g. `resin` |
| `Contract` | fixture metadata `contract_ref` | contract reference, e.g. `CTR-003-PRI` |

### Additions made

All node and edge creates included `domain='s2p'` and `provenance='seed'`. The wrapper retained the builder’s active edge set and supplemented each invoice with `SUPPLIED_BY`, `MATCHED_TO`, `RECEIVED_AS`, `HAS_COMMODITY_INDEX`, and `GOVERNED_BY` connections. The wrapper used `AGEClient.serialize_for_age()` for scalar interpolation and raw `CREATE` Cypher only inside the sandbox.

## Step 2: Entity Verification

Sandbox: `protocol_v2_test_s2p_active_0aa5d6f2cf83`.

### Node counts

| Label | Count |
|---|---:|
| `Activity` | 4 |
| `Category` | 5 |
| `Commodity` | 14 |
| `CommodityIndex` | 1 |
| `ComplianceHistory` | 1 |
| `ComplianceRule` | 5 |
| `Contract` | 33 |
| `ContractClause` | 1 |
| `Decision` | 50 |
| `Factor` | 7 |
| `GoodsReceipt` | 51 |
| `Invoice` | 50 |
| `ProcessModel` | 1 |
| `PurchaseOrder` | 50 |
| `Supplier` | 10 |
| **Total** | **266** |

### Edge counts

| Type | Count |
|---|---:|
| `BOTTLENECK_AT` | 1 |
| `COMPLIANCE_RECORD` | 1 |
| `CONTAINS` | 4 |
| `DECIDED_ON` | 50 |
| `EVALUATED_WITH` | 350 |
| `FOLLOWS` | 3 |
| `GOVERNED_BY` | 51 |
| `HAS_COMMODITY_INDEX` | 51 |
| `IN_CATEGORY` | 50 |
| `MATCHED_TO` | 50 |
| `RECEIVED_AS` | 51 |
| `SUPPLIED_BY` | 50 |
| `VIOLATES` | 50 |
| **Total** | **856** |

The target checks were:

| Check | Result |
|---|---|
| `MATCH (e {entity_id: 'S2P-INV-0003'})` | found: YES |
| `MATCH (e:Invoice {invoice_id: 'S2P-INV-0003'})` | found: YES |
| linked Supplier | YES |
| linked PurchaseOrder | YES |
| linked GoodsReceipt | YES |
| linked Commodity | YES |
| linked Contract | YES |
| domain-filtered direct neighbors | 8 |
| direct neighbors without domain filter | 8 |

The eight normalized T2 neighbors were `Contract`, `Commodity`, `GoodsReceipt`, `PurchaseOrder`, `Decision`, `Supplier`, `ComplianceRule`, and `Category`. This proves the corrected sandbox contains all five factor-required entity labels for the target and that domain stamping does not eliminate them.

## T1: Generic Query (entity_id anchor)

The current runtime query was executed through `S2PGraphReader.query_context('S2P-INV-0003', 2)`, which delegates to the AGE store’s label-less variable-length query [ci-platform/ci_platform/graph/age_graph_store.py:3143-3164].

| Measurement | Result |
|---|---:|
| rows | 53 |
| latency | 113.251 ms |
| errors | none |
| OID/timeout | none |

The returned paths visibly included `Invoice`, `Decision`, `DECIDED_ON`, `EVALUATED_WITH`, `Factor`, and other two-hop records. However, the reader result shape was path-shaped: each row had a `p` string containing AGE vertex/edge/path serialization rather than a direct normalized neighbor dictionary. This matters because `_resolve_graph_context` checks for `row['node']` and otherwise rejects the rows as non-domain-specific [s2p-copilot/backend/app/routers/s2p.py:138-161].

## T2: Label-Anchored Query (invoice_id anchor)

The direct query was:

```cypher
MATCH (e:Invoice {invoice_id: 'S2P-INV-0003'})-[]-(n)
WHERE n.domain = 's2p'
RETURN n
LIMIT 100
```

| Measurement | Result |
|---|---:|
| rows with domain filter | 8 |
| rows without domain filter | 8 |
| latency with domain filter | 117.349 ms |
| latency without domain filter | 78.746 ms |
| normalized neighbor types | Contract, Commodity, GoodsReceipt, PurchaseOrder, Decision, Supplier, ComplianceRule, Category |

The same eight direct neighbors were returned with and without the domain predicate because the wrapper stamped domain on every node. T2 is therefore a usable direct-context shape for the six direct factor readers, but it intentionally does not reach sibling Invoices through a shared Supplier hub.

## T3: Factor Computation

The factor computation used T2’s normalized direct neighbors. The invoice input included `payment_days=30` to exercise the Supplier `Net 30` property; this was an explicit experimental input, not a production-source edit.

| Factor | SQLite | A′ | Real/Fallback | Match? |
|---|---:|---:|---|---|
| `match_status` | 0.953 | 0.100 | REAL graph value; PO + GR found | NO |
| `amount_variance_ratio` | 0.040 | 0.000 | REAL graph value; PO amount found | NO |
| `duplicate_score` | 0.007 | 0.000 | REAL graph-context result, but no sibling in direct T2 set | NO |
| `supplier_exception_history` | 0.033 | 0.040 | REAL graph value; Supplier found | NO |
| `payment_terms_impact` | 0.515 | 0.000 | REAL graph value; `Net 30` matched `payment_days=30` | NO |
| `commodity_index_correlation` | 0.822 | 0.822 | REAL graph value; Commodity volatility found | YES |
| `tax_regulatory_compliance` | 0.938 | 0.150 | REAL graph value; Contract found | NO |

The T2 path returned seven computed values from graph context rather than the fixture fallback values. The duplicate result is a graph-derived zero because T2 is deliberately one-hop and contains no sibling Invoice; a separate bounded duplicate-candidate read is still required to preserve a positive duplicate signal.

For comparison, applying the factor function to T1’s path-shaped rows produced `match_status=0.9`, `duplicate_score=0.0`, `supplier_exception_history=0.033`, `payment_terms_impact=0.515`, `commodity_index_correlation=0.822`, and `tax_regulatory_compliance=0.8`; this is not a valid real-context result because the factor code cannot see the serialized path’s node properties.

**All 7 graph-derived under T2:** structurally YES, baseline match NO.  
**All 7 usable through the current endpoint:** NO; see T4.

## T4: Endpoint Trial

### Startup

Startup succeeded with:

```text
S2P_ACTIVE_GRAPH_BACKEND=age
S2P_ACTIVE_AGE_GRAPH=protocol_v2_test_s2p_active_0aa5d6f2cf83
S2P_ACTIVE_AGE_DOMAIN=s2p
S2P_ACTIVE_AGE_TEST_MODE=1
```

The correct health route was `/health`, which returned 200. `/api/health` is not an S2P route and returned 404.

### Endpoint request and result

The first diagnostic request with `event_id=A-PRIME-SPIKE` returned 200 but queried the wrong entity ID. The decisive retry used `event_id=S2P-INV-0003` and the minimal valid score body:

```json
{
  "event_id": "S2P-INV-0003",
  "category": "price_variance",
  "amount": 3781.7,
  "supplier_id": "SUP-003",
  "supplier_name": "Northstar Packaging"
}
```

| Measurement | Result |
|---|---:|
| HTTP status | 200 |
| latency | 364.904 ms |
| action | `auto_approve` |
| confidence | `0.9470536485614564` |
| conservation status | `UNKNOWN` |
| backend startup error | none |

Returned factor vector:

```text
[0.953, 0.04, 0.007, 0.033, 0.515, 0.822, 0.938, 0.5]
```

The first seven values numerically equal the fixture/SQLite baseline. They are **not** evidence that the endpoint consumed the seeded graph: `_resolve_graph_context` receives T1 path rows, its domain-specific-row check rejects them, and `compute_all_factors` receives `context=None`, allowing the fixture invoice values to supply the vector [s2p-copilot/backend/app/routers/s2p.py:138-161,1922-1965]. Thus the endpoint action/confidence match is a fallback match, not a graph-backed correctness pass.

The direct import path also emitted a non-fatal environment warning:

```text
Persistence outbox unavailable for s2p: attempt to write a readonly database
```

It did not prevent startup or the HTTP 200 response, but it should be separated from the graph experiment in future endpoint runs.

## A′ VERDICT

### FIX-B premise validated: NO

The corrected sandbox proves that a runtime-shaped entity subgraph can make the target discoverable and can drive six direct factor readers through a label-anchored query. It does **not** prove the full FIX-B premise through the current S2P endpoint because the endpoint still uses the generic variable-length path query and rejects its path-shaped output, then falls back to fixture factors.

### Anchor choice

**Adopt (b), the label-anchored direct query, for direct context.**

- (a) Generic `entity_id` anchor: rows exist after stamping, but the query returns 53 path rows, has hub/fan-out semantics, and is rejected by the current endpoint normalization.
- (b) Label-anchored `Invoice.invoice_id` direct query: 8 normalized direct neighbors, all five required entity types, and usable graph-backed values for the direct factor readers.
- Both anchors technically find data, but they do not both produce a correct runtime factor context.

### Canonical builder

`s2p-copilot/backend/app/seed_graph.py:seed_s2p_graph()` is the canonical active builder. The standalone `scripts/seed_s2p_graph.py` writer remains unsuitable without a model rewrite because it writes a different legacy edge vocabulary [s2p-copilot/scripts/seed_s2p_graph.py:158-226].

### Canonical labels for the corrected factor spike

The factor-compatible migration set demonstrated by A′ is:

`Decision`, `Invoice`, `Supplier`, `PurchaseOrder`, `GoodsReceipt`, `Commodity`, and `Contract`.

The active builder’s `CommodityIndex`, `ContractClause`, and `ComplianceHistory` remain separate contract labels. A′ does not resolve the broader label competition because no A2 experiment was run.

### Canonical edge set demonstrated by A′

For the score target, the demonstrated edge set is:

`DECIDED_ON`, `SUPPLIED_BY`, `MATCHED_TO`, `RECEIVED_AS`, `HAS_COMMODITY_INDEX`, and `GOVERNED_BY`, with `domain='s2p'` and `provenance='seed'` on every edge. The active builder additionally emits `IN_CATEGORY`, `VIOLATES`, `EVALUATED_WITH`, and process/compliance edges.

### Wrapper additions for migration

The production migration would need an explicit, governed writer that:

1. stamps domain/provenance on every node and edge;
2. aligns the score lookup identity (`entity_id` versus `invoice_id`);
3. creates per-invoice GoodsReceipt, Commodity, and Contract nodes with factor-readable properties;
4. creates the corresponding direct edges;
5. replaces the generic path read with T2-style direct context;
6. adds a bounded sibling-invoice lookup for DuplicateScore;
7. makes endpoint sandbox testing legal without weakening production `soc_graph` protection.

## What Surprised Us

1. The active builder already creates Decisions and `DECIDED_ON`; the A1 failure was not a missing Decision in the active model, but the wrong standalone writer being used.
2. Correcting the anchor and domain made the generic query return 53 rows quickly, but the rows were path strings rather than factor-readable node dictionaries.
3. T2 returned all five required entity types in only 8 direct rows and was faster in the no-filter measurement, but it cannot produce a sibling duplicate signal by design.
4. The endpoint returned the exact SQLite factor vector and matching confidence, yet this was a fallback path because the runtime discarded the T1 context.
5. The health endpoint is `/health`, not `/api/health`; the first endpoint readiness probe falsely reported startup failure.

## Remaining Gaps Before A2/B/C/D

1. Implement and test the split-read runtime shape: label-anchored direct context plus bounded duplicate candidates.
2. Make the context normalization contract accept the direct `RETURN n` result, not AGE path strings.
3. Decide whether `Commodity`/`Contract` or the active-contract `CommodityIndex`/`ContractClause` labels are canonical; A2 remains intentionally unrun.
4. Define the production migration’s idempotency, provenance, rollback, and orphan policy.
5. Add an explicit disposable graph endpoint-test profile that accepts `protocol_v2_test_s2p_active_*` without broadening production graph authorization.
6. Investigate the non-fatal readonly PersistenceOutbox warning independently.

## Cleanup

| Item | Result |
|---|---|
| Sandbox dropped | YES — `protocol_v2_test_s2p_active_0aa5d6f2cf83` |
| Other pre-existing protocol test graphs | Preserved; not created by this experiment |
| Scratch scripts deleted | YES — `_a_prime.py` removed |
| Backend stopped | YES — port 18099 process stopped after each trial |
| Production files unmodified | YES |
| Test files unmodified | YES |
| `soc_graph` untouched | YES |

## Reading and Experiment Log

- Read fully: `copilot-sdk/CLAUDE.md`.
- Read fully: `copilot-sdk/docs/design/s2p_fix_b_whatif_experiments_v3.md`.
- Requested but absent: `copilot-sdk/docs/design/s2p_fix_b_whatif_phase_a_corrected_v1.md`.
- Read fully: `copilot-sdk/docs/design/s2p_fix_b_whatif_phase_a_results_v1.md`.
- Read fully: `copilot-sdk/docs/design/s2p_entity_model_scan_v1.md`.
- Read fully: `copilot-sdk/docs/design/s2p_score_context_rootcause_design_v1.md`.
- Read fully/traced: `s2p-copilot/backend/app/seed_graph.py`, S2P factors, S2P score router, S2P active graph validation, S2P graph reader, AGEGraphStore query context, and the score endpoint request model.
- AGE connection used `localhost:5433`; WSL IP discovery was unavailable in this environment.
- All writes were confined to the named disposable sandbox. The only persistent file created by this experiment is this result document.
