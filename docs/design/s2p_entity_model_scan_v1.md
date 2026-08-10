# S2P Entity Model Scan v1
**Date:** 2026-08-04  
**Type:** Read-only diagnosis. No files edited.

## 1. Entity Model (Task 1)

### Graph Contract

The requested implementation-ready design file `docs/design/s2p_score_context_and_timing_implementation_ready_v4.md` is absent from this checkout. The available root-cause design is `docs/design/s2p_score_context_rootcause_design_v1.md`; it records the score query as `MATCH p = (e {entity_id:$id})-[*1..2]-(n) WHERE n.domain='s2p' RETURN p LIMIT 100` and notes that label-anchoring plus an index would avoid scanning every label table [copilot-sdk/docs/design/s2p_score_context_rootcause_design_v1.md:11,44-54].

`LEGACY_GRAPH_CONTRACT` is a dictionary with `graph_name = "s2p_graph"`, one external node type, nine legacy node types, and nine legacy edge types [s2p-copilot/backend/app/graph_contract.py:10-96]. Its legacy external node is `PipelineSystem`, keyed by `system_id`, with `system_id`, `name`, and `source` [s2p-copilot/backend/app/graph_contract.py:12-17]. Its legacy node definitions are:

| Label | Key | Required/declared properties | Evidence |
|---|---|---|---|
| Invoice | `invoice_id` | `invoice_id`, `supplier_id`, `po_number`, `amount`, `currency`, `category`, `ground_truth_action` | [s2p-copilot/backend/app/graph_contract.py:19-30] |
| Supplier | `supplier_id` | `supplier_id`, `name`, `category`, `exception_rate`, `payment_terms`, `otif_score` | [s2p-copilot/backend/app/graph_contract.py:31-41] |
| PurchaseOrder | `po_id` | `po_id`, `po_number`, `supplier_id`, `currency` | [s2p-copilot/backend/app/graph_contract.py:42-45] |
| GoodsReceipt | `gr_id` | `gr_id`, `po_id`, `invoice_id`, `source` | [s2p-copilot/backend/app/graph_contract.py:46-49] |
| Contract | `contract_id` | `contract_id`, `supplier_id`, `commodity_id` | [s2p-copilot/backend/app/graph_contract.py:50-53] |
| Commodity | `commodity_id` | `commodity_id`, `name` | [s2p-copilot/backend/app/graph_contract.py:54-57] |
| ProcessModel | `model_id` | `model_id`, `name`, `source` | [s2p-copilot/backend/app/graph_contract.py:58-61] |
| ProcessVariant | `variant_id` | `variant_id`, `name`, `variant_frequency`, `total_cases` | [s2p-copilot/backend/app/graph_contract.py:62-70] |
| Activity | `activity_id` | `activity_id`, `name`, `avg_duration_hours`, `case_count`, `status`, `bottleneck`, `bottleneck_cause`, `system` | [s2p-copilot/backend/app/graph_contract.py:71-83] |

The active `S2P_GRAPH_CONTRACT` is not the legacy dictionary. It is constructed with `graph_name="s2p_graph"`, `expected_nodes=187`, and `expected_edges=662` [s2p-copilot/backend/app/graph_contract.py:108-112]. Its active `expected_nodes` labels and required fields are:

| Label | Required fields |
|---|---|
| Decision | `decision_id`, `invoice_id`, `category`, `recommended_action`, `confidence`, `created_at` |
| Invoice | `invoice_id`, `supplier_id`, `po_number`, `amount`, `currency`, `category`, `ground_truth_action` |
| Supplier | `supplier_id`, `name`, `category`, `exception_rate`, `payment_terms`, `otif_score` |
| PurchaseOrder | `po_id`, `po_number`, `supplier_id`, `currency` |
| ProcessModel | `model_id`, `name`, `source` |
| Activity | `activity_id`, `name`, `avg_duration_hours`, `case_count`, `status`, `bottleneck` |
| Category | `category_id`, `name` |
| Factor | `factor_id`, `name` |
| ComplianceRule | `rule_id`, `name`, `category` |
| CommodityIndex | `commodity`, `delta_pct`, `lookback_days`, `as_of` |
| ContractClause | `ref`, `threshold_pct`, `clause_type` |
| GoodsReceipt | `gr_id`, `qty_received`, `date` |
| ComplianceHistory | `rule_id`, `pass_rate`, `sample_count` |

These active node declarations are at [s2p-copilot/backend/app/graph_contract.py:113-126]. The active contract’s 13 edge declarations are:

`DECIDED_ON(Decision, Invoice)`, `SUPPLIED_BY(Invoice, Supplier)`, `MATCHED_TO(Invoice, PurchaseOrder)`, `CONTAINS(ProcessModel, Activity)`, `FOLLOWS(Activity, Activity)`, `IN_CATEGORY(Invoice, Category)`, `EVALUATED_WITH(Decision, Factor)`, `VIOLATES(Invoice, ComplianceRule)`, `BOTTLENECK_AT(Activity, Supplier)`, `HAS_COMMODITY_INDEX(Invoice, CommodityIndex)`, `GOVERNED_BY(Invoice, ContractClause)`, `RECEIVED_AS(Invoice, GoodsReceipt)`, and `COMPLIANCE_RECORD(Supplier, ComplianceHistory)` [s2p-copilot/backend/app/graph_contract.py:127-141]. This differs from both the nine-edge legacy dictionary [s2p-copilot/backend/app/graph_contract.py:85-95] and the seven-edge list in the task anchors.

### Per-Label Trace

#### Invoice

- **Created:** The backend app seed builder creates `Invoice` node records with the seven invoice properties at [s2p-copilot/backend/app/seed_graph.py:225-239]. The standalone seed plan creates `Invoice` records with the same seven properties at [s2p-copilot/scripts/seed_s2p_graph.py:158-172]. The standalone writer emits `CREATE (n:Invoice {...}) RETURN n` for every plan node not already found by its label/key lookup [s2p-copilot/scripts/seed_s2p_graph.py:338-350].
- **Read:** Factor logic consumes an `Invoice`-typed context node and expects `invoice_id` at [s2p-copilot/backend/app/domains/s2p/factors.py:208-214]. Situation output synthesizes an invoice traversal node with `invoice_id`, `amount`, `category`, and supplier-related fields at [s2p-copilot/backend/app/services/situation_traversals.py:582-591]. The score path does not issue a labeled `MATCH (i:Invoice ...)`; it calls the label-less `query_context` through `S2PGraphReader` [s2p-copilot/backend/app/routers/s2p.py:138-161] and [s2p-copilot/backend/app/graph/s2p_graph_reader.py:118-130].
- **Properties expected by readers:** `invoice_id`, plus factor-specific invoice fields and `po_id`/supplier/commodity/contract context when present [s2p-copilot/backend/app/domains/s2p/factors.py:149-214].
- **MATCH form:** No S2P runtime `MATCH (e:Invoice...)` was found in the backend application path. The actual score context uses `(e {entity_id: ...})-[*1..N]-(n)` without a label [ci-platform/ci_platform/graph/age_graph_store.py:3143-3164].

#### Supplier

- **Created:** The app seed builder creates `Supplier` records with `supplier_id`, `name`, `category`, `exception_rate`, `payment_terms`, and `otif_score` [s2p-copilot/backend/app/seed_graph.py:174-191]. The standalone seed plan creates the same label/properties from supplier fixtures [s2p-copilot/scripts/seed_s2p_graph.py:131-145].
- **Read:** Factor logic identifies a `Supplier` node by `supplier_id` and reads `exception_rate` [s2p-copilot/backend/app/domains/s2p/factors.py:221-266]. S2P enrichment uses `entity_type = "Supplier"`, but its AGE implementation is explicitly unavailable: AGE `write_entity_enrichment()` raises `NotImplementedError` and `read_entity_enrichment()` returns `{}` [s2p-copilot/backend/app/services/s2p_enrichment.py:19-24] and [ci-platform/ci_platform/graph/age_graph_store.py:3243-3268].
- **Properties expected:** `supplier_id` and `exception_rate` for the factor path; enrichment expects supplier identity and metric records, not a base `Supplier` vertex [s2p-copilot/backend/app/domains/s2p/factors.py:221-266] and [s2p-copilot/backend/app/services/s2p_enrichment.py:204-235].
- **MATCH form:** Supplier is reached through the label-less context traversal; no labeled S2P runtime supplier vertex query was found.

#### PurchaseOrder

- **Created:** The app seed builder creates `PurchaseOrder` with `po_id`, `po_number`, `supplier_id`, and `currency` [s2p-copilot/backend/app/seed_graph.py:244-255]. The standalone seed plan creates it with the same properties [s2p-copilot/scripts/seed_s2p_graph.py:173-184].
- **Read:** The quantity and contract factor paths inspect context nodes using `PurchaseOrder`/`po_id` tests [s2p-copilot/backend/app/domains/s2p/factors.py:149-181]. Situation traversals also construct/request `purchase_order` context nodes [s2p-copilot/backend/app/services/situation_traversals.py:183-205 and 260-287].
- **Properties expected:** `po_id`, with fixture/request values such as PO quantity and contract references supplied in the traversal variable map [s2p-copilot/backend/app/services/situation_traversals.py:189-205,271-287].
- **MATCH form:** No labeled runtime MATCH; all graph context comes from the label-less query [ci-platform/ci_platform/graph/age_graph_store.py:3155-3164].

#### GoodsReceipt

- **Created:** The app seed builder creates a demo `GoodsReceipt` with `gr_id`, `qty_received`, and `date` [s2p-copilot/backend/app/seed_graph.py:297-307]. The standalone seed plan creates per-invoice `GoodsReceipt` nodes with `gr_id`, `po_id`, `invoice_id`, and `source` [s2p-copilot/scripts/seed_s2p_graph.py:185-196].
- **Read:** Factor logic checks `GoodsReceipt`/`gr_id` presence for quantity reasoning [s2p-copilot/backend/app/domains/s2p/factors.py:149-181]. Situation traversal maps `goods_receipt` to `GoodsReceipt` and expects receipt quantity/date-like properties [s2p-copilot/backend/app/services/situation_traversals.py:195-205 and 486-535].
- **Properties expected:** `gr_id`; runtime traversal variables use `gr_qty`/received quantity, while the active contract requires `qty_received` and `date` [s2p-copilot/backend/app/graph_contract.py:124-125] and [s2p-copilot/backend/app/services/situation_traversals.py:195-205].
- **MATCH form:** No labeled runtime MATCH; it is discovered by context traversal and edge aliasing [s2p-copilot/backend/app/services/situation_traversals.py:507-523].

#### Contract

- **Created:** The standalone seed plan creates `Contract` nodes from invoice metadata, with `contract_id`, `supplier_id`, and `commodity_id` [s2p-copilot/scripts/seed_s2p_graph.py:149-156 and 205-216]. The active app seed does not create `Contract`; it creates `ContractClause` instead [s2p-copilot/backend/app/seed_graph.py:286-296].
- **Read:** Factor logic checks context for `Contract`/`contract_id` [s2p-copilot/backend/app/domains/s2p/factors.py:289-306]. Situation traversal maps the logical `contract` and `contract_clause` views to `ContractClause` [s2p-copilot/backend/app/services/situation_traversals.py:486-500].
- **Properties expected:** factor code expects contract identity; situation rendering expects `ref`, `scope`, `covered_pct`, and gap variables, while the graph contract’s `ContractClause` declares `ref`, `threshold_pct`, and `clause_type` [s2p-copilot/backend/app/services/situation_traversals.py:276-294] and [s2p-copilot/backend/app/graph_contract.py:122-123].
- **MATCH form:** No labeled runtime MATCH; the query is label-less and results are normalized by edge type or ID prefix [s2p-copilot/backend/app/services/situation_traversals.py:465-523].

#### Commodity

- **Created:** Only the standalone seed plan creates `Commodity` vertices, using `commodity_id` and `name` [s2p-copilot/scripts/seed_s2p_graph.py:197-204]. The app seed creates `CommodityIndex`, not `Commodity` [s2p-copilot/backend/app/seed_graph.py:273-285].
- **Read:** The commodity factor looks for a `Commodity` node with `commodity_id` and `volatility` [s2p-copilot/backend/app/domains/s2p/factors.py:270-300]. The production situation path instead maps `commodity_index` to `CommodityIndex` [s2p-copilot/backend/app/services/situation_traversals.py:486-523].
- **Properties expected:** `commodity_id`, `volatility` for the factor path; `commodity`, `delta_pct`, `lookback_days`, and `as_of` for the contract’s `CommodityIndex` [s2p-copilot/backend/app/graph_contract.py:122] and [s2p-copilot/backend/app/seed_graph.py:277-285].
- **MATCH form:** No labeled runtime MATCH; context traversal is label-less.

#### Other contract labels

`Category`, `Factor`, and `ComplianceRule` are constructed only by the app seed builder [s2p-copilot/backend/app/seed_graph.py:151-172]; their declared edges are `IN_CATEGORY`, `EVALUATED_WITH`, and `VIOLATES` [s2p-copilot/backend/app/graph_contract.py:119-121 and 133-135]. `ProcessModel`, `ProcessVariant`, and `Activity` are created by the standalone seed plan [s2p-copilot/scripts/seed_s2p_graph.py:228-288] and by the app seed builder [s2p-copilot/backend/app/seed_graph.py:326-359]. `ComplianceHistory` is created only by the app seed builder [s2p-copilot/backend/app/seed_graph.py:312-324]. `PipelineSystem` is an external contract node [s2p-copilot/backend/app/graph_contract.py:12-17] and is created by the standalone seed plan only when a bottleneck activity has a system [s2p-copilot/scripts/seed_s2p_graph.py:276-288]. Runtime S2P code uses fixture/synthesized traversal nodes for several of these concepts rather than issuing labeled graph reads [s2p-copilot/backend/app/services/situation_traversals.py:138-320].

### Runtime Entity Creation: NO for base S2P entity vertices

The score path can create a `Decision` and can create a `DECIDED_ON` edge only when an entity already matches; it does not create an `Invoice`, `Supplier`, PO, GR, Commodity, or Contract vertex. AGE `write_decision()` uses `MATCH (e {entity_id: ...}) ... CREATE (d:Decision ...) CREATE (d)-[:DECIDED_ON]->(e)` and falls back to `CREATE (d:Decision ...)` if the entity match is empty [ci-platform/ci_platform/graph/age_graph_store.py:558-596]. `link_decision_to_entity()` similarly matches a label-less entity and, on no match, creates an orphan `DecisionEntityLink` rather than an entity vertex [ci-platform/ci_platform/graph/age_graph_store.py:2702-2733].

There is a separate runtime enrichment API, but the S2P AGE implementation explicitly rejects enrichment writes [ci-platform/ci_platform/graph/age_graph_store.py:3243-3258]. Therefore the seed is the only current writer of the required base entity vertices in AGE. Preview writes `Observation`, not a Decision or base entity, through `write_observation()` [s2p-copilot/backend/app/routers/s2p_preview.py:209-240].

## 2. Seed Writer (Task 2)

### `scripts/seed_s2p_graph.py`

`build_seed_plan()` sets its plan `graph_name` from `S2P_GRAPH_CONTRACT["graph_name"]`, therefore `s2p_graph`, and starts empty `nodes`, `edges`, and `warnings` arrays [s2p-copilot/scripts/seed_s2p_graph.py:114-129]. It loads invoices and suppliers from the S2P data directory and process data from the DataOps Celonis fixture path or S2P data path [s2p-copilot/scripts/seed_s2p_graph.py:29-60 and 378-382].

The complete node construction is:

- `Supplier` from fixture fields `supplier_id`, `name`, `category`, `exception_rate`, `payment_terms`, `otif_score` [s2p-copilot/scripts/seed_s2p_graph.py:131-145].
- Per selected invoice: `Invoice` with `invoice_id`, `supplier_id`, `po_number`, `amount`, `currency`, `category`, `ground_truth_action` [s2p-copilot/scripts/seed_s2p_graph.py:148-172]; `PurchaseOrder` with `po_id`, `po_number`, `supplier_id`, `currency` [173-184]; `GoodsReceipt` with `gr_id`, `po_id`, `invoice_id`, `source="synthetic_invoices"` [185-196]; optional `Commodity` with `commodity_id` and `name` [197-204]; optional `Contract` with `contract_id`, `supplier_id`, `commodity_id` [205-216].
- If process data exists: `ProcessModel`, `ProcessVariant`, `Activity`, and conditional `PipelineSystem` [s2p-copilot/scripts/seed_s2p_graph.py:228-288].

The complete standalone plan edge construction is `INVOICED_BY`, `REFERENCES`, `MATCHED_TO`, optional `COVERS`, optional `SUPPLIES`, `HAS_VARIANT`, `HAS_ACTIVITY`, conditional `BOTTLENECK_AT`, and conditional `INVOICE_PATTERN` [s2p-copilot/scripts/seed_s2p_graph.py:218-226 and 255-307]. These are not identical to the active contract’s `DECIDED_ON`/`IN_CATEGORY`/`EVALUATED_WITH`/etc. edge set [s2p-copilot/backend/app/graph_contract.py:127-141].

`write_seed_plan()` constructs `AGEClient(dsn=dsn, graph_name=graph_name)` and calls `ensure_graph()` [s2p-copilot/scripts/seed_s2p_graph.py:330-334]. With `force=True`, it runs the exact Cypher `MATCH (n) WHERE n.domain = 's2p' DETACH DELETE n` [s2p-copilot/scripts/seed_s2p_graph.py:335-336]. For every node it checks `MATCH (n:<Label> {<key>: <value>}) RETURN n LIMIT 1` and, when absent, emits `CREATE (n:<Label> {<properties>}) RETURN n` [s2p-copilot/scripts/seed_s2p_graph.py:338-350]. For every edge it checks an exact labeled endpoint pattern and, when absent, emits:

```cypher
MATCH (a:<source_label> {<source_key>: <source_value>})
MATCH (b:<target_label> {<target_key>: <target_value>})
CREATE (a)-[r:<edge_type> {<props>}]->(b)
RETURN r
```

This is the exact writer shape at [s2p-copilot/scripts/seed_s2p_graph.py:352-374]. It is idempotent for the natural-key node lookup and exact edge lookup, but it does not delete/reconcile existing entity rows unless `--force` is used. The force delete is not entity-specific and deletes every node carrying `domain='s2p'` [s2p-copilot/scripts/seed_s2p_graph.py:335-336].

The CLI requires `--graph`; it accepts `--dsn`, `--force`, `--dry-run`, and `--limit` [s2p-copilot/scripts/seed_s2p_graph.py:385-392]. It refuses `--graph soc_graph` unless `ALLOW_PRODUCTION_SEED=1` [s2p-copilot/scripts/seed_s2p_graph.py:394-396]. Without `--dsn`, it loads `GraphConfig.load("s2p")` and uses that config’s DSN [s2p-copilot/scripts/seed_s2p_graph.py:398-410]. There is no separate `--target` flag. The `main()` default is therefore no graph default: the graph is mandatory, and the plan’s internal graph name does not override the CLI target [s2p-copilot/scripts/seed_s2p_graph.py:385-392 and 419-432].

The standalone writer does **not** stamp `domain`, `provenance`, or `domain_source` into any node or edge properties. Its `_add_node()` stores exactly the supplied fixture properties [s2p-copilot/scripts/seed_s2p_graph.py:69-84], `_add_edge()` stores only `type`, endpoints, and optional properties [86-111], and the node/edge property dictionaries shown above contain no domain/provenance fields. This is a rollback and isolation gap for a shared graph migration.

The full local plan, computed from the current fixtures without writing AGE, is 214 nodes and 247 edges: 50 invoices, 10 suppliers, 50 POs, 50 GRs, 14 commodities, 33 contracts, one process model, one process variant, four activities, and one pipeline system. Edge counts are: `INVOICED_BY=50`, `REFERENCES=50`, `MATCHED_TO=50`, `COVERS=45`, `SUPPLIES=45`, `HAS_VARIANT=1`, `HAS_ACTIVITY=4`, `BOTTLENECK_AT=1`, `INVOICE_PATTERN=1`. This count was obtained by calling the unchanged `build_seed_plan()` and counting its returned `summary`, node labels, and edge types; the plan’s summary fields are defined at [s2p-copilot/scripts/seed_s2p_graph.py:311-317].

### `app/seed_graph.py`

This file is a deterministic data builder, not an AGE writer. `seed_graph(graph=..., seed=...)` validates the target, loads `GraphConfig.load("s2p")`, and returns `seed_s2p_graph(seed=seed)`; it explicitly says that it performs no deletion or production write [s2p-copilot/backend/app/seed_graph.py:116-138]. `seed_s2p_graph()` returns in-memory node/edge dictionaries [s2p-copilot/backend/app/seed_graph.py:141-149]. It builds `Category`, `Factor`, `ComplianceRule`, `Supplier`, `Decision`, `Invoice`, `PurchaseOrder`, `CommodityIndex`, `ContractClause`, `GoodsReceipt`, `ComplianceHistory`, `ProcessModel`, and `Activity` records [s2p-copilot/backend/app/seed_graph.py:151-367]. Its Decision records are the only seed-builder records explicitly stamped with `domain="s2p"` and `provenance="seed"` [s2p-copilot/backend/app/seed_graph.py:209-224].

The exact app seed clean-delete constant is:

```text
MATCH (d:Decision) WHERE d.domain = 's2p' DETACH DELETE d
```

at [s2p-copilot/backend/app/seed_graph.py:26-28]. It deletes only domain-scoped `Decision` nodes, not entity labels. The app builder and standalone writer can coexist as in-memory planning mechanisms, but they are not schema-equivalent: they produce different node/edge sets and only the standalone writer performs AGE writes. Running a writer against one graph and using the other builder’s assumptions would therefore not be a safe substitute.

### Idempotency + Coexistence Assessment

The standalone writer’s non-force mode is natural-key/idempotent for the labels it creates, but its current properties are not domain-stamped. Its force mode is unsafe as a shared-graph cleanup primitive because it deletes all `domain='s2p'` nodes, including existing S2P Decisions and other domain-stamped artifacts, then creates un-stamped seed nodes [s2p-copilot/scripts/seed_s2p_graph.py:335-350]. The app clean-delete is safer for Decisions but does not remove or reconcile entity subgraphs [s2p-copilot/backend/app/seed_graph.py:26-28].

## 3. Live Graph State (Task 3)

The requested WSL command returned an access-denied error (`WSL/Service/CreateInstance/E_ACCESSDENIED`) in this environment. The same requested psycopg/AGE queries were therefore executed against `localhost:5433`, which connected successfully. The temporary query script was deleted after execution.

### Graphs

`SELECT name FROM ag_catalog.ag_graph ORDER BY name` returned 89 graph names. The relevant results are:

- `soc_graph` exists.
- `s2p_graph` does not exist.
- Disposable/test graph families include `protocol_v2_test`, many `protocol_v2_test_<suffix>` graphs, `protocol_v2_test_s2p_active_<suffix>`, `protocol_v2_test_s2p_shadow_<suffix>`, `ci_age_client`, `ci_auto_test_446cb566`, `ci_counter_compat`, `soc_graph_counter_p2c_live_1`, `soc_graph_counter_p2d_route_readiness_1`, and three `soc_stress_test_<suffix>` graphs.

The complete returned graph list was: `ci_age_client`, `ci_auto_test_446cb566`, `ci_counter_compat`, `protocol_v2_test`, `protocol_v2_test_1`, `protocol_v2_test_128f36bb`, `protocol_v2_test_2001225c`, `protocol_v2_test_2c73ac2b`, `protocol_v2_test_40555e50`, `protocol_v2_test_44d24132`, `protocol_v2_test_457c4b31`, `protocol_v2_test_488dd899`, `protocol_v2_test_4985d790`, `protocol_v2_test_4d00fb4a`, `protocol_v2_test_5a679f05`, `protocol_v2_test_6538af0d`, `protocol_v2_test_65c926bf`, `protocol_v2_test_677df976`, `protocol_v2_test_693ce0ba`, `protocol_v2_test_6caacfe2`, `protocol_v2_test_6fa31732`, `protocol_v2_test_71a95c55`, `protocol_v2_test_72cb0230`, `protocol_v2_test_74a612ef`, `protocol_v2_test_7877ea55`, `protocol_v2_test_7ba2fe50`, `protocol_v2_test_7bd5bc71`, `protocol_v2_test_8088f788`, `protocol_v2_test_82e03c63`, `protocol_v2_test_82f6c17e`, `protocol_v2_test_850f7c5d`, `protocol_v2_test_85e3f462`, `protocol_v2_test_898aa128`, `protocol_v2_test_8adb33f2`, `protocol_v2_test_8f4bef88`, `protocol_v2_test_a1bec537`, `protocol_v2_test_a40fedc8`, `protocol_v2_test_a44df5d6`, `protocol_v2_test_a451cfb7`, `protocol_v2_test_af35e4e4`, `protocol_v2_test_af917d4c`, `protocol_v2_test_b22be330`, `protocol_v2_test_b418c65c`, `protocol_v2_test_ba1dc25f`, `protocol_v2_test_bad412e4`, `protocol_v2_test_bcc25bef`, `protocol_v2_test_bd20c10f`, `protocol_v2_test_bd79a784`, `protocol_v2_test_bf7587ac`, `protocol_v2_test_c3981499`, `protocol_v2_test_c4a24fa8`, `protocol_v2_test_c61e8a8e`, `protocol_v2_test_c70e9ebe`, `protocol_v2_test_d07f0d48`, `protocol_v2_test_d2ebf149`, `protocol_v2_test_d344eeb7`, `protocol_v2_test_d48669f4`, `protocol_v2_test_d7933aa7e951`, `protocol_v2_test_de1a42d3`, `protocol_v2_test_e6d2a30d4b2a`, `protocol_v2_test_ee2649c9`, `protocol_v2_test_efb33750`, `protocol_v2_test_f905367d`, `protocol_v2_test_fadfcc1b`, `protocol_v2_test_feb18fe9`, `protocol_v2_test_s2p_active_00127688b474`, `protocol_v2_test_s2p_active_1a4a1dfe1e82`, `protocol_v2_test_s2p_active_5574847c2314`, `protocol_v2_test_s2p_active_58e5cefa2b2d`, `protocol_v2_test_s2p_active_6533a5a232fe`, `protocol_v2_test_s2p_active_7f69c699408e`, `protocol_v2_test_s2p_active_b62153025233`, `protocol_v2_test_s2p_active_c14a75617a67`, `protocol_v2_test_s2p_shadow_0866cf2789bc`, `protocol_v2_test_s2p_shadow_25cddd44ee0e`, `protocol_v2_test_s2p_shadow_6463549dbd01`, `protocol_v2_test_s2p_shadow_6aaea8397235`, `protocol_v2_test_s2p_shadow_838653595ca5`, `protocol_v2_test_s2p_shadow_fb5cd85bfc4b`, `soc_graph`, `soc_graph_counter_p2c_live_1`, `soc_graph_counter_p2d_route_readiness_1`, `soc_stress_test_1570c30de47a`, `soc_stress_test_86fd90c4f7c0`, and `soc_stress_test_bd1b28fd8fdb`.

### `soc_graph` Labels + Counts

`ag_label` returned the following complete non-internal labels. Edge labels are marked `(edge)` and vertex labels `(vertex)`:

| Label | Kind | Count |
|---|---|---:|
| ABOUT | edge | 164 |
| AFFECTS | edge | 20 |
| APPLIED_PLAYBOOK | edge | 0 |
| ASSIGNED_TO | edge | 0 |
| ASSOCIATED_WITH | edge | 0 |
| BY_ANALYST | edge | 0 |
| CLASSIFIED_AS | edge | 645 |
| CONTINUES | edge | 146 |
| DECIDED_ON | edge | 5,562 |
| DERIVED_FROM | edge | 474 |
| DETECTED_ON | edge | 855 |
| EMITTED_RECEIPT | edge | 760 |
| FEEDS | edge | 9 |
| FOR_ALERT | edge | 0 |
| FROM_DOMAIN | edge | 6 |
| HAD_CONTEXT | edge | 0 |
| HANDLED_BY | edge | 0 |
| HAS_CENTROID_CHECKPOINT | edge | 82 |
| HAS_FACTOR_VECTOR | edge | 0 |
| HAS_HISTORY | edge | 0 |
| HAS_INDICATOR | edge | 633 |
| HAS_OUTCOME | edge | 2,228 |
| HAS_TRAVEL | edge | 0 |
| INVOLVES | edge | 855 |
| IN_CATEGORY | edge | 0 |
| IN_DOMAIN | edge | 0 |
| MATCHES | edge | 0 |
| MEMBER_OF | edge | 824 |
| ORIGINATES_FROM | edge | 0 |
| PART_OF | edge | 0 |
| SEEN_CATEGORY | edge | 0 |
| SHAPED_BY | edge | 18 |
| SNAPSHOT_AFTER | edge | 474 |
| STORES | edge | 0 |
| SUBJECT_TO | edge | 0 |
| SUMMARIZES_DOMAIN | edge | 1,085 |
| SUPERSEDES | edge | 0 |
| TO_DOMAIN | edge | 6 |
| TRIGGERED_EVOLUTION | edge | 13 |
| Alert | vertex | 868 |
| AlertCategory | vertex | 0 |
| AlertType | vertex | 0 |
| AnalystArchetype | vertex | 0 |
| Asset | vertex | 226 |
| AttackPattern | vertex | 9 |
| BehaviorHistory | vertex | 0 |
| Campaign | vertex | 507 |
| CampaignSeed | vertex | 265 |
| Category | vertex | 0 |
| CentroidCheckpoint | vertex | 828 |
| Checkpoint | vertex | 0 |
| ConservationStatus | vertex | 620 |
| DataClass | vertex | 0 |
| DataQualityAlert | vertex | 20 |
| Decision | vertex | 34,668 |
| DecisionContext | vertex | 0 |
| DecisionDistanceLog | vertex | 1 |
| DecisionEntityLink | vertex | 88 |
| DeploymentState | vertex | 1 |
| Domain | vertex | 5 |
| DomainContext | vertex | 55 |
| Entity | vertex | 2 |
| EvidenceReceipt | vertex | 760 |
| EvolutionEvent | vertex | 61 |
| FactorVector | vertex | 34 |
| Fingerprint | vertex | 463 |
| L5Centroid | vertex | 26 |
| L5ConservationState | vertex | 5 |
| L5DKWeight | vertex | 4 |
| L5DKWeightArchive | vertex | 0 |
| Location | vertex | 0 |
| Observation | vertex | 385 |
| Outcome | vertex | 2,262 |
| PhishingCampaign | vertex | 0 |
| PipelineSystem | vertex | 9 |
| Playbook | vertex | 0 |
| ProfileSnapshot | vertex | 51 |
| SLA | vertex | 0 |
| ShadowDecision | vertex | 1,500 |
| TestAlert | vertex | 0 |
| TestDecision | vertex | 0 |
| TestIntegrity | vertex | 0 |
| TestNode | vertex | 0 |
| TestSetBehavior | vertex | 0 |
| ThreatIndicator | vertex | 10 |
| ThreatIntel | vertex | 5 |
| TransferPattern | vertex | 6 |
| TravelContext | vertex | 0 |
| TravelRecord | vertex | 0 |
| User | vertex | 231 |

The S2P contract entity labels `Invoice`, `Supplier`, `Commodity`, `PurchaseOrder`, `GoodsReceipt`, `Contract`, `ProcessModel`, `ProcessVariant`, `Activity`, `ComplianceRule`, `CommodityIndex`, `ContractClause`, and `ComplianceHistory` are absent from the live `soc_graph` label catalog. There is a generic `Entity` label with count 2, but it is not any of those typed S2P labels.

### `soc_graph` Indexes

The live graph has 135 indexes. AGE supplies primary-key indexes for vertex labels and start/end ID indexes for edge labels. The two application-specific Decision indexes are exactly:

```sql
CREATE INDEX decision_archived_idx ON soc_graph."Decision"
  USING btree (agtype_access_operator(VARIADIC ARRAY[properties, '"archived"'::agtype]));
CREATE INDEX decision_domain_idx ON soc_graph."Decision"
  USING btree (agtype_access_operator(VARIADIC ARRAY[properties, '"domain"'::agtype]));
```

There are no indexes for `entity_id`, `invoice_id`, `supplier_id`, `po_id`, `gr_id`, `commodity_id`, or `contract_id`, and no S2P entity label tables on which such indexes could currently exist. The full live index-name list is: `ABOUT_end_id_idx`, `ABOUT_start_id_idx`, `AFFECTS_end_id_idx`, `AFFECTS_start_id_idx`, `APPLIED_PLAYBOOK_end_id_idx`, `APPLIED_PLAYBOOK_start_id_idx`, `ASSIGNED_TO_end_id_idx`, `ASSIGNED_TO_start_id_idx`, `ASSOCIATED_WITH_end_id_idx`, `ASSOCIATED_WITH_start_id_idx`, `AlertCategory_pkey`, `AlertType_pkey`, `Alert_pkey`, `AnalystArchetype_pkey`, `Asset_pkey`, `AttackPattern_pkey`, `BY_ANALYST_end_id_idx`, `BY_ANALYST_start_id_idx`, `BehaviorHistory_pkey`, `CLASSIFIED_AS_end_id_idx`, `CLASSIFIED_AS_start_id_idx`, `CONTINUES_end_id_idx`, `CONTINUES_start_id_idx`, `CampaignSeed_pkey`, `Campaign_pkey`, `Category_pkey`, `CentroidCheckpoint_pkey`, `Checkpoint_pkey`, `ConservationStatus_pkey`, `DECIDED_ON_end_id_idx`, `DECIDED_ON_start_id_idx`, `DERIVED_FROM_end_id_idx`, `DERIVED_FROM_start_id_idx`, `DETECTED_ON_end_id_idx`, `DETECTED_ON_start_id_idx`, `DataClass_pkey`, `DataQualityAlert_pkey`, `DecisionContext_pkey`, `DecisionDistanceLog_pkey`, `DecisionEntityLink_pkey`, `Decision_pkey`, `DeploymentState_pkey`, `DomainContext_pkey`, `Domain_pkey`, `EMITTED_RECEIPT_end_id_idx`, `EMITTED_RECEIPT_start_id_idx`, `Entity_pkey`, `EvidenceReceipt_pkey`, `EvolutionEvent_pkey`, `FEEDS_end_id_idx`, `FEEDS_start_id_idx`, `FOR_ALERT_end_id_idx`, `FOR_ALERT_start_id_idx`, `FROM_DOMAIN_end_id_idx`, `FROM_DOMAIN_start_id_idx`, `FactorVector_pkey`, `Fingerprint_pkey`, `HAD_CONTEXT_end_id_idx`, `HAD_CONTEXT_start_id_idx`, `HANDLED_BY_end_id_idx`, `HANDLED_BY_start_id_idx`, `HAS_CENTROID_CHECKPOINT_end_id_idx`, `HAS_CENTROID_CHECKPOINT_start_id_idx`, `HAS_FACTOR_VECTOR_end_id_idx`, `HAS_FACTOR_VECTOR_start_id_idx`, `HAS_HISTORY_end_id_idx`, `HAS_HISTORY_start_id_idx`, `HAS_INDICATOR_end_id_idx`, `HAS_INDICATOR_start_id_idx`, `HAS_OUTCOME_end_id_idx`, `HAS_OUTCOME_start_id_idx`, `HAS_TRAVEL_end_id_idx`, `HAS_TRAVEL_start_id_idx`, `INVOLVES_end_id_idx`, `INVOLVES_start_id_idx`, `IN_CATEGORY_end_id_idx`, `IN_CATEGORY_start_id_idx`, `IN_DOMAIN_end_id_idx`, `IN_DOMAIN_start_id_idx`, `L5Centroid_pkey`, `L5ConservationState_pkey`, `L5DKWeightArchive_pkey`, `L5DKWeight_pkey`, `Location_pkey`, `MATCHES_end_id_idx`, `MATCHES_start_id_idx`, `MEMBER_OF_end_id_idx`, `MEMBER_OF_start_id_idx`, `ORIGINATES_FROM_end_id_idx`, `ORIGINATES_FROM_start_id_idx`, `Observation_pkey`, `Outcome_pkey`, `PART_OF_end_id_idx`, `PART_OF_start_id_idx`, `PhishingCampaign_pkey`, `PipelineSystem_pkey`, `Playbook_pkey`, `ProfileSnapshot_pkey`, `SEEN_CATEGORY_end_id_idx`, `SEEN_CATEGORY_start_id_idx`, `SHAPED_BY_end_id_idx`, `SHAPED_BY_start_id_idx`, `SLA_pkey`, `SNAPSHOT_AFTER_end_id_idx`, `SNAPSHOT_AFTER_start_id_idx`, `STORES_end_id_idx`, `STORES_start_id_idx`, `SUBJECT_TO_end_id_idx`, `SUBJECT_TO_start_id_idx`, `SUMMARIZES_DOMAIN_end_id_idx`, `SUMMARIZES_DOMAIN_start_id_idx`, `SUPERSEDES_end_id_idx`, `SUPERSEDES_start_id_idx`, `ShadowDecision_pkey`, `TO_DOMAIN_end_id_idx`, `TO_DOMAIN_start_id_idx`, `TRIGGERED_EVOLUTION_end_id_idx`, `TRIGGERED_EVOLUTION_start_id_idx`, `TestAlert_pkey`, `TestDecision_pkey`, `TestIntegrity_pkey`, `TestNode_pkey`, `TestSetBehavior_pkey`, `ThreatIndicator_pkey`, `ThreatIntel_pkey`, `TransferPattern_pkey`, `TravelContext_pkey`, `TravelRecord_pkey`, `User_pkey`, `_ag_label_edge_end_id_idx`, `_ag_label_edge_pkey`, `_ag_label_edge_start_id_idx`, `_ag_label_vertex_pkey`, `decision_archived_idx`, and `decision_domain_idx`.

### `s2p_graph` State

`s2p_graph` is not present in `ag_catalog.ag_graph`, so there is no live S2P-owned graph state to census. The contract’s `graph_name="s2p_graph"` is therefore declarative/legacy relative to the deployed database [s2p-copilot/backend/app/graph_contract.py:108-110].

### Orphan `DecisionEntityLink` Count

The exact AGE query `MATCH (l:DecisionEntityLink) WHERE l.domain = 's2p' RETURN count(l)` returned **84**. The total `DecisionEntityLink` label count is 88. This matches the fallback behavior in `link_decision_to_entity()` [ci-platform/ci_platform/graph/age_graph_store.py:2720-2733].

### S2P Decision Count

The exact AGE query `MATCH (d:Decision) WHERE d.domain = 's2p' RETURN count(d)` returned **25,892** S2P Decisions. The total live `Decision` vertex count is 34,668.

## 4. Graph-Name Reconciliation (Task 4)

### Contract vs Runtime

The S2P contract says `s2p_graph` [s2p-copilot/backend/app/graph_contract.py:108-110], but the active repository configuration says S2P uses AGE, expects AGE, and targets `soc_graph` [copilot-sdk/graph_config.toml:46-54]. The runtime cutover is explicit in `S2PActiveGraphConfig.validate()`: product AGE is allow-listed only for `soc_graph`, and `soc_graph` requires `shared_graph_authorization == "s2p:soc_graph"` [s2p-copilot/backend/app/s2p_graph_status.py:181-224].

`create_s2p_active_graph_store()` validates the active config and calls `require_shared_graph()` with profile `production` unless active test mode is enabled [s2p-copilot/backend/app/s2p_graph_status.py:331-348]. It then delegates to `copilot_sdk.graph.factory.create_graph_store` with `backend="age"`, `domain="s2p"`, `dsn=config.dsn`, `graph_name=config.graph`, `test_mode=config.test_mode`, and optional shared authorization [s2p-copilot/backend/app/s2p_graph_status.py:349-367]. The wrapper is installed into `app.state.scorer` at startup [s2p-copilot/backend/app/main.py:167-177].

### `require_shared_graph`

The SDK guard accepts `age`/`dual_write` only as governed backends, returns early for non-production or test mode, and in production requires the exact graph name `soc_graph`; otherwise it raises `GraphConfigError` [copilot-sdk/copilot_sdk/config/graph_config.py:26-50]. This prevents a production S2P startup using `s2p_graph`, but it does not rewrite the contract object.

### `create_s2p_active_graph_store` and the factory

The generic factory is fail-closed for configuration-driven production paths: it loads typed `GraphConfig`, rejects a production config that resolves SQLite while AGE is expected, and selects the configured backend [copilot-sdk/copilot_sdk/graph/factory.py:123-175]. SQLite construction is an explicit selected-backend branch [copilot-sdk/copilot_sdk/graph/factory.py:177-192]. AGE construction requires a non-blank DSN and explicit graph name, validates shared-graph authorization, and constructs the AGE adapter [copilot-sdk/copilot_sdk/graph/factory.py:257-285]. For `soc_graph`, the factory requires a matching `domain:soc_graph` authorization pair [copilot-sdk/copilot_sdk/graph/factory.py:225-243].

### Hybrid Feasibility

The runtime can technically construct separate stores, but the active S2P startup installs one `S2PActiveAGEGraphStore` around the factory-produced store and uses that same store for scorer, `app.state.graph_store`, and `S2PGraphReader` [s2p-copilot/backend/app/main.py:167-177]. A hybrid with entities in `s2p_graph` and Decisions in `soc_graph` would not work for the current score context because `S2PGraphReader.query_context()` delegates to the same active store [s2p-copilot/backend/app/graph/s2p_graph_reader.py:118-130]. The AGE query itself has no graph parameter; the adapter’s configured graph owns the entire read [ci-platform/ci_platform/graph/age_graph_store.py:3143-3164].

### Recommendation: `soc_graph`

FIX-B should seed the entity subgraph into **`soc_graph`**, not `s2p_graph`. Evidence: `graph_config.toml` maps S2P to `soc_graph` [copilot-sdk/graph_config.toml:46-54]; production guardrails require `soc_graph` [copilot-sdk/copilot_sdk/config/graph_config.py:40-50]; `create_s2p_active_graph_store()` passes the configured graph to the shared factory [s2p-copilot/backend/app/s2p_graph_status.py:349-367]; and the live database has `soc_graph` but no `s2p_graph`. Seeding `s2p_graph` would either create an unreferenced graph or require a new split-read architecture that the current runtime does not have. The tradeoff is that shared-graph seeding must add `domain='s2p'`, `provenance='seed'`/`domain_source`, precise cleanup scope, and entity-specific indexes so it cannot contaminate other copilot domains.

## 5. Full Graph-Op Surface (Task 5)

The canonical S2P graph-read facade exposes domain-bound `get_decision`, decision collections, verified/correct counts, decision links, and `query_context`; every call fixes `domain='s2p'` [s2p-copilot/backend/app/graph/s2p_graph_reader.py:18-130]. The runtime operation map is:

| # | Endpoint / path | Function | Graph method | Entity dependencies | Absent behavior |
|---:|---|---|---|---|---|
| 1 | `POST /api/s2p/score` | `score_procurement_event` | `S2PGraphReader.query_context` via `_resolve_graph_context` [s2p-copilot/backend/app/routers/s2p.py:1921-1965] | Invoice anchor plus optional Supplier/PO/GR/Commodity/Contract context | Label-less AGE traversal can scan all labels and time out when the invoice entity is absent; the exception is caught and context is set to `None`, so scoring continues with degraded/fixture factors [s2p-copilot/backend/app/routers/s2p.py:138-161]. |
| 2 | `POST /api/s2p/score` | score write | `scorer.score()` then `_link_decision_to_invoice` | Decision plus pre-existing invoice entity | Decision is written; entity absence causes `DECIDED_ON` linking to miss and the link path can create `DecisionEntityLink` fallback [s2p-copilot/backend/app/routers/s2p.py:1971-1987 and 2030-2035] and [ci-platform/ci_platform/graph/age_graph_store.py:2702-2733]. |
| 3 | `POST /api/learn` | `learn_decision` | `get_decision`, evidence append, scorer learn/outcome, L5 persistence | Existing Decision; optional invoice link/context | AGE read failure is converted to HTTP 503; missing Decision is not silently substituted and the subsequent learning path cannot authoritatively proceed [s2p-copilot/backend/app/routers/s2p.py:2117-2155]. |
| 4 | `POST /api/s2p/outcome` | `record_outcome` | `_ensure_outcome_decision`, `get_decision`, then scorer learn/outcome | Existing Decision; optional invoice entity for link | Decision lookup failure is HTTP 503; outcome path is fail-closed rather than a fixture entity substitute [s2p-copilot/backend/app/routers/s2p.py:2220-2278]. |
| 5 | `GET /api/s2p/situation/{decision_id}` | `get_situation` | `get_decision`, then `SituationAnalyzer` patterns → `query_context`, optional `query_similar`, enrichment reads | Decision anchor; Invoice/PO/GR/Commodity/ContractClause/ComplianceHistory context | Missing Decision is 404; graph failure during read/traversal is 503; traversal patterns may render fixture-shaped nodes when graph rows are absent [s2p-copilot/backend/app/routers/s2p_situation.py:27-79] and [s2p-copilot/backend/app/services/situation_traversals.py:440-462]. |
| 6 | `GET /api/s2p/preview/queue` | `preview_queue` | read-only scorer; optional `write_observation` | No required entity vertex for score; observation carries invoice ID | Preview is fixture-backed and writes an Observation only when store implements Protocol V2; it does not create Decision/entity vertices [s2p-copilot/backend/app/routers/s2p_preview.py:161-165 and 209-240]. |
| 7 | `GET /api/s2p/preview/conservation` | `preview_conservation` | No graph call; fixture scoring | None | Returns illustration/fixture values and computed fixture counts [s2p-copilot/backend/app/routers/s2p_preview.py:510-544]. |
| 8 | `GET /api/s2p/preview/compounding` | `preview_compounding` | No graph call; local simulation | None | Returns local preview simulation [s2p-copilot/backend/app/routers/s2p_preview.py:547-563]. |
| 9 | `GET /api/s2p/preview/suppliers` | `preview_suppliers` | No graph call; supplier JSON fixture | None | Returns fixture suppliers [s2p-copilot/backend/app/routers/s2p_preview.py:566-580]. |
| 10 | `GET /api/s2p/evidence/audit-trail/{invoice_id}` | evidence router | `get_decision_links`, `get_decision`, `get_all_decisions` | Decision/invoice link; base invoice entity is not directly required by the reader | Missing links/decision produce an empty/filtered audit result; AGE read errors are surfaced through the router’s graph reader handling [s2p-copilot/backend/app/routers/s2p_evidence.py:231-261]. |
| 11 | `GET /api/s2p/explorer/...` | explorer endpoints | `get_decision`, `get_all_decisions`, count methods; centroid writes in import path | Decision and optionally context/enrichment | Missing decision is handled as not found/empty by explorer response; read failures use `GraphUnavailableError` handling [s2p-copilot/backend/app/routers/s2p_explorer.py:184-213 and 339-343]. |
| 12 | `GET /api/s2p/performance/...` | performance endpoints | `count_verified`, `count_correct`, `count_decisions`, `count_recommended_action`, `get_verified_decisions` | Decisions only | Counts return zero/raise through reader depending on store availability; no entity vertex is needed [s2p-copilot/backend/app/routers/s2p_performance.py:77-100]. |
| 13 | `POST /api/s2p/enrich-context/{invoice_id}` | `enrich_context` | `read_entity_enrichment`, `write_entity_enrichment`, decision links | Enrichment entity types: `CommodityIndex`, `ContractClause`, `GoodsReceipt`, `ComplianceHistory` | AGE write is explicitly `NotImplementedError`; the route therefore cannot materialize durable AGE enrichment [s2p-copilot/backend/app/routers/s2p_enrichment_context.py:28-40] and [ci-platform/ci_platform/graph/age_graph_store.py:3243-3268]. |
| 14 | `POST /api/s2p/enrichment/run` and supplier enrichment reads | enrichment service | `read_entity_enrichment`, `list_entity_enrichments`, `write_entity_enrichment`, verified/all Decision reads | Supplier enrichment records and Decisions | AGE enrichment write/read is unsupported/empty; Decision history reads remain available through the S2P reader [s2p-copilot/backend/app/services/s2p_enrichment.py:204-235 and 291-355]. |
| 15 | centroid/factor/auto-approve services | service/router helpers | `get_centroid_checkpoints`, `read_entity_enrichment`, verified/all Decision reads and counts | Decisions and optional supplier/enrichment context | Missing optional context is represented as absent/fallback; graph failures are generally converted to service/router errors, not entity creation [s2p-copilot/backend/app/services/centroid_explorer.py:157-202], [s2p-copilot/backend/app/services/s2p_auto_approve_gate.py:406], and [s2p-copilot/backend/app/routers/s2p.py:858-917]. |

### Runtime Creates Entities: NO

Across the full backend scan, the only runtime graph writes that can create vertices are Decision writes, Observation writes, and framework/audit artifacts. No production S2P route emits `CREATE (i:Invoice)`, `CREATE (s:Supplier)`, or equivalent typed base-entity creation. `write_entity_enrichment` is called by runtime services, but AGE intentionally raises `NotImplementedError` rather than creating a vertex [ci-platform/ci_platform/graph/age_graph_store.py:3243-3258]. The missing base entity subgraph is therefore a seed/migration problem, not a missing score-time writer.

## 6. Factory + Launch (Task 6)

### `create_s2p_active_graph_store` source

The complete active-store route is [s2p-copilot/backend/app/s2p_graph_status.py:331-367]. It returns `None` for non-AGE config, validates S2P active config, calls `require_shared_graph`, invokes `create_graph_store(backend="age", domain="s2p", dsn=config.dsn, graph_name=config.graph, env={}, test_mode=config.test_mode, shared_graph_authorization=...)`, wraps the result in `S2PActiveAGEGraphStore`, and labels the phase `product_decision_outcome_cutover` for product graph or `phase_b_test_mode` for protocol test graph.

### `create_graph_store` factory

The full factory decision is:

1. If backend/DSN/graph are omitted, load typed `GraphConfig` for the supplied domain [copilot-sdk/copilot_sdk/graph/factory.py:145-170].
2. In production, reject a config whose expected backend is AGE but selected backend is SQLite [copilot-sdk/copilot_sdk/graph/factory.py:157-164].
3. Construct SQLite only when the selected backend is SQLite [copilot-sdk/copilot_sdk/graph/factory.py:177-192].
4. Construct dual-write with SQLite primary + AGE secondary when explicitly selected, requiring DSN and shared authorization for `soc_graph` [copilot-sdk/copilot_sdk/graph/factory.py:194-255].
5. For AGE, require non-blank domain, DSN, and graph, validate graph name/authorization, then instantiate the AGE adapter [copilot-sdk/copilot_sdk/graph/factory.py:257-285].

### S2P_ACTIVE_* environment variables

Typed config maps S2P fields to these variables [copilot-sdk/copilot_sdk/config/graph_config.py:116-125]:

| Variable | Control |
|---|---|
| `S2P_ACTIVE_GRAPH_BACKEND` | Active backend (`sqlite`, `age`, or supported typed value) |
| `S2P_ACTIVE_AGE_DSN` | AGE DSN |
| `S2P_ACTIVE_AGE_GRAPH` | Active AGE graph name |
| `S2P_ACTIVE_AGE_DOMAIN` | Active domain, validated as `s2p` |
| `S2P_ACTIVE_AGE_TEST_MODE` | Enables disposable `protocol_v2_test*` graph mode |
| `S2P_SHADOW_AGE` | Shadow AGE lifecycle flag, read by S2P status/config paths |
| `S2P_ACTIVE_LIVE_AGE_TEST` | Live AGE test status flag |
| `S2P_SHARED_GRAPH_AUTHORIZED` | S2P shared graph authorization/status input; `GraphConfig.authorized` supplies the canonical `s2p:soc_graph` pair |

The graph-status module’s environment audit list confirms the S2P active variables plus `S2P_SHADOW_AGE`, `S2P_SHARED_GRAPH_AUTHORIZED`, and generic graph variables [s2p-copilot/backend/app/s2p_graph_status.py:72-78].

### `demo.py` S2P launch

`demo.py` defines S2P on backend port 8002, frontend port 5177, S2P backend path, AGE requirement, the shared SOC DSN, and `_build_graph_env("s2p", AGE_DSN_SOC)` [copilot-sdk/demo.py:216-227]. `_build_graph_env()` sets generic `GRAPH_BACKEND=age`, `GRAPH_DSN`, `GRAPH_NAME=soc_graph`, `AGE_GRAPH_NAME=soc_graph`, `GRAPH_DOMAIN=s2p`, `DEMO_MODE=1`, and `DATAOPS_DEMO_MODE=1`; for non-SOC domains it additionally sets `<DOMAIN>_ACTIVE_GRAPH_BACKEND=age`, `<DOMAIN>_ACTIVE_AGE_DSN`, `<DOMAIN>_ACTIVE_AGE_GRAPH=soc_graph`, and `<DOMAIN>_ACTIVE_AGE_DOMAIN` [copilot-sdk/demo.py:106-127]. Thus S2P launch points at `soc_graph` with `S2P_ACTIVE_GRAPH_BACKEND=age`, `S2P_ACTIVE_AGE_DSN`, `S2P_ACTIVE_AGE_GRAPH=soc_graph`, and `S2P_ACTIVE_AGE_DOMAIN=s2p`.

### `demo.py` runs entity seed: NO

The launcher’s `setup_graph_mode()` invokes CI’s DataOps seed script only for DataOps graph mode [copilot-sdk/demo.py:1044-1064]. Its generic `run_preseed()` calls `DemoPreseed().preseed_all()` and `scripts/preseed_all_copilots.py` for the SDK copilots [copilot-sdk/demo.py:1069-1110 and 1139-1149]; there is no invocation of `s2p-copilot/scripts/seed_s2p_graph.py` or `s2p-copilot/backend/app/seed_graph.py`. S2P-specific preseed is an HTTP learning loop against `/api/alerts/queue`, `/api/s2p/score`, and `/api/learn`, not entity seeding [copilot-sdk/demo.py:1243-1285]. Therefore the demo starts S2P against `soc_graph` without running the entity seed tool, which directly explains the absent subgraph.

## 7. Migration Design Inputs (synthesis)

### Where entities must land: `soc_graph`

The migration target is `soc_graph`. This is required by the active TOML configuration [copilot-sdk/graph_config.toml:46-54], production shared-graph guard [copilot-sdk/copilot_sdk/config/graph_config.py:26-50], S2P active factory [s2p-copilot/backend/app/s2p_graph_status.py:331-367], and live graph availability (soc exists; s2p_graph does not).

### Which tool writes them: `seed_s2p_graph.py`

The standalone tool has the necessary AGE writer and accepts an arbitrary required `--graph` argument [s2p-copilot/scripts/seed_s2p_graph.py:330-375 and 385-432]. It can technically target `soc_graph`, but only with `ALLOW_PRODUCTION_SEED=1` [394-396]. It is not safe for the migration as-is because it does not stamp domain/provenance, its force cleanup is broad, and its edge/node schema differs from the active contract. A migration wrapper or a hardened version of this tool must be read-only/planned first, use explicit `soc_graph` authorization, stamp every vertex/edge, and clean only seed-owned S2P entity records.

### Coexistence with existing Decisions

Non-force seeding will not delete existing Decisions, because it only performs natural-key existence checks [s2p-copilot/scripts/seed_s2p_graph.py:338-350]. Force mode is unsafe: `MATCH (n) WHERE n.domain='s2p' DETACH DELETE n` can delete S2P Decisions and artifacts before writing un-stamped entity nodes [335-336]. The app constant is safer for Decision cleanup but does not clean entities [s2p-copilot/backend/app/seed_graph.py:26-28].

### Labels the split-read query needs

The score context/factor path needs at minimum `Invoice`, `Supplier`, `PurchaseOrder`, `GoodsReceipt`, `Commodity` (or a deliberate `CommodityIndex` mapping), and `Contract` (or a deliberate `ContractClause` mapping). The active contract additionally declares `Category`, `Factor`, `ComplianceRule`, `CommodityIndex`, `ContractClause`, and `ComplianceHistory`; process enrichment needs `ProcessModel`, `ProcessVariant`, `Activity`, and `PipelineSystem` [s2p-copilot/backend/app/graph_contract.py:113-140]. The standalone seed currently creates the six invoice-related labels plus process labels; it does not create the active app seed’s `Category`, `Factor`, `ComplianceRule`, `CommodityIndex`, `ContractClause`, or `ComplianceHistory` set.

### Indexes needed

AGE currently has no S2P entity labels or entity-key indexes. The root-cause design specifically recommends label-anchoring `(e:<InvoiceLabel> {entity_id: ...})` and an index instead of the label-less scan [copilot-sdk/docs/design/s2p_score_context_rootcause_design_v1.md:44-54]. The migration design therefore needs a verified index strategy for the actual property keys used by the final Cypher: at least invoice/entity anchor identity, and likely `supplier_id`, `po_id`, `gr_id`, `commodity_id`, and `contract_id` according to the selected query shapes. AGE index syntax and planner behavior must be validated against the live version before any schema write.

### Orphan cleanup needed

There are 84 S2P `DecisionEntityLink` vertices. Because `link_decision_to_entity()` creates them when either Decision/entity matching fails [ci-platform/ci_platform/graph/age_graph_store.py:2717-2733], migration planning must decide whether to retain them as audit evidence, reconcile them into real edges after entities are seeded, or delete only those that are provably orphaned. Any cleanup must be domain-scoped and idempotent; it must not use the broad seed force-delete query.

## 8. Open Questions

1. The requested `s2p_score_context_and_timing_implementation_ready_v4.md` is missing. The available root-cause design is sufficient to identify the pathological query, but the implementation-ready acceptance criteria could not be compared.
2. The active contract declares `ContractClause`, `CommodityIndex`, and `ComplianceHistory`, while the standalone seed creates `Contract`, `Commodity`, and `GoodsReceipt` with a different property schema. A migration must choose one canonical label/property mapping before writing AGE.
3. The standalone seed plan reports 214 nodes/247 edges for the current 50-invoice fixtures, while `S2P_GRAPH_CONTRACT` says 187 expected nodes/662 expected edges. The expected-count semantics and fixture version are unresolved.
4. The standalone seed writer does not stamp `domain`, `provenance`, or `domain_source`; the migration needs an explicit property contract for rollback and cross-domain isolation.
5. The live `soc_graph` contains 34,668 Decisions but only 25,892 S2P Decisions and 84 S2P orphan link vertices. The relationship between the 84 links and the 25,892 Decisions has not been reconciled; do not delete them without an identity-level audit.
6. AGE has no typed S2P entity labels in the live catalog and no entity-key indexes. The migration must validate AGE label creation and index support on this instance before changing the graph.
7. Runtime S2P enrichment calls exist, but AGE `write_entity_enrichment()` is intentionally unsupported. If enrichment is part of the demo acceptance criteria, it requires a separate governed implementation; seeding base vertices alone will not make those writes durable.

## Reading Log

- Read fully: `copilot-sdk/CLAUDE.md`.
- Read fully: `copilot-sdk/docs/design/s2p_score_context_rootcause_design_v1.md`.
- Requested file missing: `copilot-sdk/docs/design/s2p_score_context_and_timing_implementation_ready_v4.md`.
- Read fully: `s2p-copilot/backend/app/graph_contract.py`.
- Read fully: `s2p-copilot/scripts/seed_s2p_graph.py`.
- Read fully: `s2p-copilot/backend/app/seed_graph.py`.
- Read fully or traced in full: S2P graph reader, active graph status/factory path, S2P main startup, score/learn/outcome/situation/preview/evidence/explorer/enrichment paths, situation traversal and enrichment services, SDK GraphConfig/factory, and AGE store query/write/enrichment methods cited above.
- Read fully: `copilot-sdk/graph_config.toml`.
- Live AGE queries executed with psycopg using `LOAD 'age'` and `SET search_path = ag_catalog, '$user', public`; WSL IP resolution was blocked, so the same DSN was queried via `localhost:5433`.
- Temporary scratch script `scripts/_tmp_s2p_entity_scan.py` was created only for the live query and deleted.
- No production or test source file was edited. The only persistent file created by this scan is this report.

## Final Finding

The migration target is **`soc_graph`**; the seed tool **can** target it only behind `ALLOW_PRODUCTION_SEED=1`, but it cannot target it safely without domain/provenance stamping and a narrower cleanup policy. The live graph currently has **zero** S2P entity-label tables, the active contract defines **13** edge types, the standalone fixture plan produces **9** edge types and **214/247** nodes/edges, and `soc_graph` has **135** existing indexes but none for S2P entity keys. The immediate root cause is confirmed: S2P runtime reads and writes use shared `soc_graph`, while `demo.py` never runs the entity seed and entity absence causes the label-less context traversal to scan the shared graph.
