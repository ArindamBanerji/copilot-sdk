# S2P FIX-B What-If — Phase A Results v1
**Date:** 2026-08-04  
**Type:** Experimental correctness spike in a disposable AGE graph.  
**soc_graph touched:** NO

## Seed Writer Analysis

### CLI flags

The standalone writer is `s2p-copilot/scripts/seed_s2p_graph.py`. Its `main()` accepts:

| Flag | Required/default | Behavior | Evidence |
|---|---|---|---|
| `--graph` | required | target AGE graph name | [s2p-copilot/scripts/seed_s2p_graph.py:385-396] |
| `--dsn` | optional | AGE DSN; otherwise config/env fallback | [s2p-copilot/scripts/seed_s2p_graph.py:398-410] |
| `--force` | false | delete `domain='s2p'` vertices before seeding | [s2p-copilot/scripts/seed_s2p_graph.py:335-336,385-396] |
| `--dry-run` | false | print the plan without writing | [s2p-copilot/scripts/seed_s2p_graph.py:385-432] |
| `--limit` | optional | limit invoice fixtures | [s2p-copilot/scripts/seed_s2p_graph.py:385-432] |

The `--graph` flag exists. The guard rejects `soc_graph` unless `ALLOW_PRODUCTION_SEED=1`; a `whatif_*` graph is not rejected by this guard [s2p-copilot/scripts/seed_s2p_graph.py:385-396]. The command actually used was:

```text
python ..\s2p-copilot\scripts\seed_s2p_graph.py --graph whatif_s2p_4d07b4815066 --dsn "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres sslmode=disable"
```

It reported `214 nodes, 247 edges`.

### `write_seed_plan` Cypher

`write_seed_plan(plan, dsn, graph_name, force=False)` constructs `AGEClient(dsn=dsn, graph_name=graph_name)` and calls `ensure_graph()` [s2p-copilot/scripts/seed_s2p_graph.py:330-334]. With `force=True`, it executes this exact cleanup:

```cypher
MATCH (n) WHERE n.domain = 's2p' DETACH DELETE n
```

Evidence: [s2p-copilot/scripts/seed_s2p_graph.py:335-336]. This cleanup is not entity-specific and was not used in A1.

For each plan node, the writer first executes this natural-key lookup, where `<label>` and `<key>` are substituted from the plan:

```cypher
MATCH (n:<label> {<key>: <value>}) RETURN n LIMIT 1
```

If absent, it executes:

```cypher
CREATE (n:<label> {<serialized properties>}) RETURN n
```

Evidence: [s2p-copilot/scripts/seed_s2p_graph.py:338-350].

For each plan edge, it first matches the source and target vertices by their labels and key properties, then checks for an existing relationship. If absent, it executes the equivalent of:

```cypher
MATCH (a:<source_label> {<source_key>: <source_value>})
MATCH (b:<target_label> {<target_key>: <target_value>})
CREATE (a)-[r:<edge_type> {<serialized edge properties>}]->(b)
RETURN r
```

Evidence: [s2p-copilot/scripts/seed_s2p_graph.py:352-374].

The writer does not add `domain`, `provenance`, or `domain_source` automatically. `_add_node()` and `_add_edge()` only preserve the properties supplied by `build_seed_plan()` [s2p-copilot/scripts/seed_s2p_graph.py:69-111]. Therefore the A1 seed was not domain-stamped.

### Node labels created

The complete A1 node count was:

| Label | Count |
|---|---:|
| `Invoice` | 50 |
| `Supplier` | 10 |
| `PurchaseOrder` | 50 |
| `GoodsReceipt` | 50 |
| `Commodity` | 14 |
| `Contract` | 33 |
| `ProcessModel` | 1 |
| `ProcessVariant` | 1 |
| `Activity` | 4 |
| `PipelineSystem` | 1 |
| **Total** | **214** |

These labels are assembled by `build_seed_plan()` from suppliers, invoices, Celonis process fixtures, and optional invoice relationships [s2p-copilot/scripts/seed_s2p_graph.py:114-318].

### Edge types created

The complete A1 edge count was:

| Edge type | Count |
|---|---:|
| `INVOICED_BY` | 50 |
| `REFERENCES` | 50 |
| `MATCHED_TO` | 50 |
| `COVERS` | 45 |
| `SUPPLIES` | 45 |
| `HAS_ACTIVITY` | 4 |
| `HAS_VARIANT` | 1 |
| `BOTTLENECK_AT` | 1 |
| `INVOICE_PATTERN` | 1 |
| **Total** | **247** |

The seven active-contract edge types requested by the experiment were all absent: `DECIDED_ON`, `SUPPLIED_BY`, `HAS_COMMODITY_INDEX`, `GOVERNED_BY`, `RECEIVED_AS`, and `COMPLIANCE_RECORD` each counted 0; `DECIDED_ON` also counted 0. The standalone writer creates the legacy edge set shown above [s2p-copilot/scripts/seed_s2p_graph.py:218-226,228-307], not the active contract’s edge set [s2p-copilot/backend/app/graph_contract.py:127-141].

## A1: Seed-Fixes-Score

### Sandbox and safety

Sandbox: `whatif_s2p_4d07b4815066`. AGE was reached through `localhost:5433` because the requested WSL IP lookup was blocked by the environment with `Wsl/Service/CreateInstance/E_ACCESSDENIED`. The sandbox was created, seeded, queried, and dropped. No `create_graph`, `drop_graph`, or write was issued against `soc_graph`.

### Entity verification

The experiment queried each label with `MATCH (n:<Label>) RETURN count(n)` and each edge with `MATCH ()-[r:<EdgeType>]->() RETURN count(r)`. The results are the tables in the Seed Writer Analysis above.

The target lookup required by the score path was:

```cypher
MATCH (e {entity_id: 'S2P-INV-0003'}) RETURN e
```

Result: **no rows**.

The corresponding key-based lookup was:

```cypher
MATCH (i:Invoice {invoice_id: 'S2P-INV-0003'}) RETURN i
```

Result: one `Invoice` vertex with these properties:

```json
{
  "amount": 3781.7,
  "category": "price_variance",
  "currency": "USD",
  "po_number": "PO-20260003",
  "invoice_id": "S2P-INV-0003",
  "supplier_id": "SUP-003",
  "ground_truth_action": "auto_approve"
}
```

The seeded invoice had three direct neighbors:

| Relationship | Neighbor label | Key evidence |
|---|---|---|
| `INVOICED_BY` | `Supplier` | `supplier_id=SUP-003`, `payment_terms=Net 30`, `exception_rate=0.04` |
| `REFERENCES` | `PurchaseOrder` | `po_id=PO-20260003`, `po_number=PO-20260003` |
| `MATCHED_TO` | `GoodsReceipt` | `gr_id=GR-PO-20260003`, `invoice_id=S2P-INV-0003` |

No `DECIDED_ON` relationship or Decision was created by the standalone seed, so the target had no linked Decision. The direct neighbors also lacked a `domain` property because the standalone writer does not stamp one.

### Direct score observation

The scratch diagnostic constructed `AGEGraphStore(dsn=..., graph_name=...)`, wrapped it in `S2PGraphReader`, and called:

```python
reader.query_context("S2P-INV-0003", 2)
```

Observed result:

| Measurement | Result |
|---|---:|
| `query_context` rows | 0 |
| latency | 107.918 ms |
| target anchor used | `entity_id` |
| seed key present | `invoice_id` |

Because the context was empty, the diagnostic computed factors without graph context. The values numerically matched the embedded SQLite reference factors, but this was a fixture/fallback result, not evidence of real AGE factor computation:

| Factor | SQLite baseline | AGE sandbox | Classification |
|---|---:|---:|---|
| `match_status` | 0.953 | 0.953 | fallback; no graph context |
| `amount_variance_ratio` | 0.040 | 0.040 | fallback; no graph context |
| `duplicate_score` | 0.007 | 0.007 | fallback; no graph context |
| `supplier_exception_history` | 0.033 | 0.033 | fallback; no graph context |
| `payment_terms_impact` | 0.515 | 0.515 | fallback; no graph context |
| `commodity_index_correlation` | 0.822 | 0.822 | fallback; no graph context |
| `tax_regulatory_compliance` | 0.938 | 0.938 | fallback; no graph context |

No authoritative scorer action or confidence was claimed from this direct observation, because the required graph context was absent and the experiment’s A1 pass criterion requires all seven values to be real.

### Endpoint score observation

The endpoint trial used port `18002` to avoid touching any existing S2P process and set:

```text
S2P_ACTIVE_GRAPH_BACKEND=age
S2P_ACTIVE_AGE_DSN=host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres sslmode=disable
S2P_ACTIVE_AGE_GRAPH=whatif_s2p_4d07b4815066
S2P_ACTIVE_AGE_DOMAIN=s2p
S2P_ACTIVE_AGE_TEST_MODE=1
```

The backend did not become healthy. Import/startup failed before the endpoint was available with:

```text
app.s2p_graph_status.S2PActiveGraphConfigError:
S2P active AGE test mode is allowed only for protocol_v2_test* graphs
```

Therefore:

| Measurement | Result |
|---|---|
| HTTP status | not reached |
| endpoint latency | not applicable |
| endpoint factors | not produced |
| backend error | active AGE test-mode graph-name guard rejected `whatif_s2p_4d07b4815066` |

This is an independent A1 integration blocker: disposable `whatif_*` graphs cannot currently be used as S2P active AGE endpoint targets under test mode, while production/shared-graph validation does not permit replacing the shared production graph with the sandbox.

### A1 VERDICT: FAIL

The FIX-B premise was **not validated**. Seeding the standalone entity plan did not make the existing S2P score context work because:

1. The score anchor is `entity_id`, while the seeded `Invoice` uses `invoice_id`; `MATCH (e {entity_id: 'S2P-INV-0003'})` returned no rows.
2. The seed writer does not stamp `domain='s2p'`, while `AGEGraphStore.query_context()` filters neighbors with `WHERE n.domain = 's2p'` [ci-platform/ci_platform/graph/age_graph_store.py:3143-3164].
3. The seed creates no `Decision` and no `DECIDED_ON` edge, so there is no linked target Decision.
4. The seed creates legacy relationship labels (`INVOICED_BY`, `REFERENCES`, `MATCHED_TO`, etc.), not the active contract relationships required by the runtime design.
5. The endpoint could not be exercised against the disposable graph because S2P active AGE test mode only permits `protocol_v2_test*` graph names [s2p-copilot/backend/app/s2p_graph_status.py:178-212].

The ~108 ms empty query is not a successful correctness result. It only demonstrates that the absent `entity_id` anchor avoids the expected timeout in this small sandbox by returning nothing.

### Surprises / what failed and why

The biggest mismatch was not AGE performance: the seed’s natural key and provenance schema are incompatible with the runtime query contract. A second mismatch is that the standalone seed and active graph contract describe different label and edge vocabularies. Finally, the endpoint’s “disposable graph” path is blocked by an active-graph guard before scoring can begin.

## A2: Label Mapping

**SKIPPED.** The experiment plan requires stopping after an A1 failure. No `SB_A2_SEED` or `SB_A2_CONTRACT` graph was created, and no contract-label experiment was run.

This means Phase A does not establish a canonical migration label set. Any choice between `Commodity`/`Contract` and `CommodityIndex`/`ContractClause` remains unresolved and must be tested only after the A1 identity, provenance, edge, and endpoint-sandbox blockers are addressed in a new experiment.

## Phase A Synthesis

### FIX-B premise validated: NO

The experiment did not demonstrate that running the current seed tool against the graph read by S2P makes scoring work. It demonstrated that the current seed output is not a runtime-compatible S2P entity subgraph.

### Canonical labels for migration

**UNRESOLVED.** A2 was correctly skipped. The migration must first resolve:

- whether runtime reads should use `Invoice.invoice_id` or the score’s `entity_id` contract;
- which exact `domain`/provenance fields all seeded vertices and edges must carry;
- whether legacy seed labels/edges are retained or mapped to active contract labels/edges;
- how a Decision and `DECIDED_ON` relationship are supplied for the score target;
- how S2P active AGE endpoint tests may target a disposable graph without weakening the shared `soc_graph` guard.

### Canonical properties per label

The A1 seed’s observed invoice properties are compatible with the legacy contract (`invoice_id`, `supplier_id`, `po_number`, `amount`, `currency`, `category`, `ground_truth_action`) [s2p-copilot/backend/app/graph_contract.py:19-30]. The seed’s observed Supplier, PurchaseOrder, GoodsReceipt, Commodity, and Contract properties are likewise from the legacy seed plan [s2p-copilot/scripts/seed_s2p_graph.py:158-216]. However, A1 did not prove that these are the canonical runtime properties because the runtime query did not find the invoice.

### Blocking issues for Phase B

Phase B must not proceed as a production migration design until a follow-up spike resolves:

1. invoice identity mapping (`entity_id` versus `invoice_id`);
2. domain stamping in the standalone writer;
3. Decision/`DECIDED_ON` creation and association;
4. legacy-versus-active contract label and edge mapping;
5. safe endpoint execution against a disposable graph.

## Cleanup

| Cleanup item | Result | Evidence |
|---|---|---|
| A1 sandbox dropped | YES | `whatif_s2p_4d07b4815066` was dropped with `drop_graph(..., true)` |
| A2 sandboxes dropped | YES / NONE CREATED | A2 was skipped after A1 failure |
| Scratch scripts deleted | YES | `scripts/_tmp_s2p_fixb_a1.py` deleted after use |
| Production files unmodified | YES | no production or test file was edited |
| `soc_graph` untouched | YES | all AGE writes were scoped to `whatif_s2p_4d07b4815066` |

## Reading and Experiment Log

- Read fully: `copilot-sdk/CLAUDE.md`.
- Read fully: `copilot-sdk/docs/design/s2p_fix_b_whatif_experiments_v3.md`.
- Read fully: `copilot-sdk/docs/design/s2p_entity_model_scan_v1.md`.
- Read fully: `copilot-sdk/docs/design/s2p_score_context_rootcause_design_v1.md`.
- Read and traced: `s2p-copilot/scripts/seed_s2p_graph.py`, S2P graph contract, S2P reader, S2P active graph validation, factor pipeline, and AGE `query_context`.
- A1 AGE connection used `localhost:5433`; the requested WSL IP discovery was unavailable because WSL returned `E_ACCESSDENIED`.
- Persistent output: this document only. No production/test source was edited.
