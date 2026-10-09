# P10 Factor Computers Design

Date: 2026-10-02 · Author: Codex · Status: DRAFT

This is a source-backed implementation design, not an implementation or evidence of live graph readiness. The latest session entry before this work is `PHASE1-AGE-TEST-FIX`, dated 2026-10-02: **4,217 SDK tests passed, 0 failures**. Its preceding experiment entries are also dated 2026-10-02; they do not record time-of-day timestamps. No tests were run for this design.

**Recommendation:** extend the existing S2P graph-context pipeline, retain the eight-factor scoring contract, and introduce `process_bottleneck_factor` as a separately reported process-evidence result first. Reuse ci-platform's process labels and transition directions. S2P-GR must reconcile the existing contracts and add invoice-specific process execution evidence before the factor can describe an invoice as currently delayed.

## 1. Current Factor Inventory

### Actual implementation and call path

The requested `backend/app/domains/s2p/scorer.py` does **not** exist. Factor computers are already separate from the scorer: all eight implementations live in [factors.py](../../s2p-copilot/backend/app/domains/s2p/factors.py), with the public structural contract in [factor_protocol.py](../../s2p-copilot/backend/app/domains/s2p/factor_protocol.py). There is no `factors/` directory. Extraction from an inline scorer is unnecessary; put the new process computation in a separate module and preserve existing imports.

[S2PDomainConfig](../../s2p-copilot/backend/app/domains/s2p/config.py) and the shared [S2PDomainConfigV2](../../ci-platform/domain_config.py) specify **five categories, five actions, eight ordered factors: `(5,5,8)`**. The four `canonical_factors` identity/context names in config are not four additional scoring computers.

The current path in [the S2P score router](../../s2p-copilot/backend/app/routers/s2p.py) is:

1. `POST /api/s2p/score` resolves the request and optional invoice fixture.
2. `_resolve_graph_context()` calls `S2PGraphReader.query_direct_context()` and `query_duplicate_context()`.
3. Direct context supplies PO, receipt, supplier, commodity and contract nodes; duplicate context supplies same-supplier invoice candidates.
4. `compute_all_factors(invoice, context)` computes the eight scalar values; the SDK scorer consumes them in config order.

Thus the premise that all factors are currently flat is outdated. The computers consume graph-derived dictionaries but do not themselves perform database I/O. The [reader](../../s2p-copilot/backend/app/graph/s2p_graph_reader.py) already has directed AGE queries. Its duplicate query is bounded to 20 same-supplier invoices within a strict ±5% amount band. [Existing integration tests](../../s2p-copilot/backend/tests/test_s2p_track2_graph_reader_and_factors.py) exercise real graph context and PO/contract perturbations; their presence does not establish that they passed during this design.

All current `compute()` methods return a **single `float`, intended to be in `[0,1]`**. They do not return explanation/metadata objects. `compute_all_factors()` returns `dict[str,float]`, or `(values, available, degraded_factor_names)` with `return_status=True`; `compute_factor_vector()` returns `list[float]` in configuration order. Existing availability tracking catches `RuntimeError` from a computer; it is not comprehensive evidence-quality validation.

| Factor / class | Data read today | Current computation and fallback | P10 classification | Return |
|---|---|---|---|---|
| `match_status` / `MatchStatus` | Invoice amount/quantity; graph PO and GoodsReceipt; invoice approvals/explicit factors | With comparable numeric properties, `1 - max(relative discrepancies)`, clamped. Presence-only branches return 0.1 or 0.6; otherwise invoice approval match or factor/default 0.5. | HYBRID | float |
| `amount_variance_ratio` / `AmountVarianceRatio` | Invoice amount; graph PO amount aliases; flat variance percentage or historical mean | Absolute invoice/PO difference divided by `max(abs(PO amount),1)`; otherwise variance percentage, historical-mean difference or factor/default 0.3. | HYBRID | float |
| `duplicate_score` / `DuplicateScore` | Graph-context Invoice siblings, invoice ID and amount; explicit factor fallback | Maximum amount similarity excluding the current invoice. It is **not string matching** and does not itself validate currency. Empty candidate set in nonempty context yields 0; absent context falls back to 0.05. | GRAPH-AWARE | float |
| `supplier_exception_history` / `SupplierExceptionHistory` | Graph Supplier.exception_rate; flat vendor counts, supplier rating or explicit factor | Uses supplier rate; else `1 - approvals/decisions`; else `1 - supplier_risk_rating`; default 0.5. It does not currently traverse verified history itself. | GRAPH-AWARE | float |
| `payment_terms_impact` / `PaymentTermsImpact` | Invoice/metadata payment_days; graph Supplier.payment_terms | Relative absolute difference in payment days; graph terms default to 30 if unparsable/absent; factor/default 0.5 when context insufficient. | HYBRID | float |
| `commodity_index_correlation` / `CommodityIndexCorrelation` | Graph Commodity.volatility or explicit factor | Clamped volatility, default 0.5. Despite its name, **no statistical correlation is calculated**. | HYBRID | float |
| `tax_regulatory_compliance` / `TaxRegulatoryCompliance` | Graph Contract max_amount, tax_compliant, regulatory_status; supplier presence; invoice tax metadata | Fraction of available checks passing. Presence-only/no-contract branches have separate legacy constants; default factor 0.5. | HYBRID | float |
| `environmental_risk` / `EnvironmentalRisk` | Neighbor environmental_risk/carbon_footprint; invoice metadata including route_weather_risk | Direct risk or footprint/1,000, clamped; then metadata or factor/default 0.5. Current neighbor selection is first matching value. | HYBRID | float |

**Counts:** current eight = **0 FLAT, 2 GRAPH-AWARE, 6 HYBRID**. Including the proposed process computer = **0 FLAT, 3 GRAPH-AWARE, 6 HYBRID**, nine design entries but still eight active scoring dimensions. Classification describes P10's data dependency, not whether the mathematical formula runs on a Python dictionary. None of the existing computers is exclusively flat today.

## 2. Factor Classification

Keep the arithmetic and existing scalar interfaces for the six HYBRID computers. They need bounded, identified entity context and explicit provenance, not additional multi-hop algorithms. Do not remove their existing graph branches or silently invert their scoring polarity. Match/compliance high values generally indicate a good match/compliance, while variance/risk high values indicate risk; legacy presence-only branches need a separate semantic review before any recalibration.

The two existing GRAPH-AWARE computers require relational evidence:

- **Duplicate score:** reuse and harden the existing sibling traversal; it already exists. Candidate completeness, currency and deterministic ordering matter more than introducing another similarity formula.
- **Supplier history:** wire the existing verified-history enrichment into factor context rather than trusting an unqualified supplier property. Reuse [S2PEnrichmentService.compute_supplier_metrics](../../s2p-copilot/backend/app/services/s2p_enrichment.py), its `ProvenancedValue` eligibility, and its existing exception-rate definition.

The new process computer requires case linkage, execution state, variant-scoped activity/transition metrics and explicit duration units. Supplier-level `INVOICE_PATTERN` correlation alone cannot establish which activity an individual invoice occupies.

### GraphStore capability boundary

[GraphStore](../copilot_sdk/graph/protocol.py) provides domain-scoped Decision reads (`get_decision`, `get_decisions`, all/archived/verified variants and counts), checkpoint APIs, and domain state for evolution, posteriors, promotions, ledgers and governance. Entity enrichment has read/write/list methods with provenance. These state buckets are **not** substitutes for process nodes.

The separate optional `GraphTraversalStore` declares `get_decision_links`, `query_context(entity_id,max_depth,domain=...)` and `query_similar`. It does not declare generic typed-node lookup, arbitrary edge traversal, pagination/completeness metadata, or a process-case query. Protocol V2 adds decision movement/contextual judgment; those are not process-mining readers either.

[InMemoryGraphStore](../copilot_sdk/graph/memory_store.py) has decision/entity-link traversal, not an arbitrary ProcessVariant/Transition graph. Passing an Invoice ID to `get_decision()` is not a valid invoice lookup. Existing `S2PGraphReader` also reaches private AGE query methods for its directed reads; that is an existing implementation seam, not a portable GraphStore guarantee.

**Implementation boundary:** add a read-only S2P process-context capability behind `S2PGraphReader`, with a typed result containing nodes, typed edges, observation time, provenance and completeness. The conceptual operation is `read_process_context(invoice_id, as_of)` on a reader bound to domain `s2p`. S2P-GR owns its AGE adapter/query and typed capability contract; factor code must not unwrap stores or execute Cypher. A bare GraphStore without that capability returns an explicit unavailable process result. Keep the base GraphStore protocol unchanged. Specify this extension in S2P-GR before implementing P10; it is not an API already present.

## 3. process_bottleneck_factor Design

### Inputs and integration

Public orchestration inputs: `invoice_id: str` and the application's canonical `GraphStore` instance. Bind a domain-scoped S2P reader to that store. Also inject an `as_of` UTC timestamp and a versioned process-factor policy for deterministic calculation; the request layer supplies these, not a second backend configuration.

Separate the read operation from a pure computation over a validated `ProcessContext` DTO. The policy controls maximum evidence age, minimum aggregate sample size, node/page budgets and a bounded read deadline. Proposed initial limits: 24-hour evidence age, 20 aggregate samples, 100 activities/transitions per selected variant, 100 executions per case and five backend pages; deployments must configure and record their actual values. A truncated result is `partial`, never evidence that omitted activities are healthy.

Initially expose the result beside existing score evidence, for example under `process_context.factor_results.process_bottleneck_factor`. Do not add it to `ALL_FACTORS`, overwrite an existing factor, or pass nine numbers to the eight-dimensional scorer. A future promotion to an actual scoring dimension requires a factor-schema version, nine-dimensional centroids/DK state, checkpoint compatibility and recalibration. Keep that as a separate rollout gate.

### Traversal and evidence

The following are **proposed S2P-GR paths**; only the process-model portion already has a connector representation:

```text
Invoice -IN_PROCESS_CASE-> ProcessCase -OF_VARIANT-> ProcessVariant
ProcessModel -HAS_VARIANT-> ProcessVariant -CONTAINS-> Activity
ProcessCase -HAS_EXECUTION-> ActivityExecution -INSTANCE_OF-> Activity
ProcessVariant -HAS_TRANSITION-> Transition
Activity -TRANSITION_FROM-> Transition -TRANSITION_TO-> Activity
```

1. Resolve the scoped Invoice and its process case at `as_of`. No supplier-name guess or first-variant fallback. A case can contain several invoices; an invoice may have multiple historical cases. This version requires one explicitly selected active case; ambiguous mappings produce `unavailable: ambiguous_case`.
2. Read its exact variant/model revision and executions. Repeated activity occurrences have distinct execution IDs and occurrence indices; parallel active executions are preserved.
3. Join each execution to its Activity and the selected variant's `CONTAINS` relationship. Read observed state/times from the execution and variant-specific historical duration, sample size and target duration from that relationship.
4. For a queued execution, follow its predecessor execution ID to identify the preceding Activity, then the selected variant's Transition into the queued Activity. Read mean wait and target wait there. Do not choose a transition merely because both activities occur somewhere in the model.
5. Require domain, source namespace, model revision, provenance and observation-window agreement across joins. Read consistent evidence as of the same snapshot; reject future timestamps or negative durations. Keep connector payloads/fixtures separate from live evidence.

### Computation

Use **seconds** internally, minutes only for display. Each producer must declare units. Convert legacy `avg_duration_hours * 3600`; do not infer units from magnitude. ci-platform's `avg_duration`/`wait_time` need an explicit ingestion unit contract; DataOps' enterprise adapter currently interprets `avg_duration` as seconds.

For each active execution:

- `in_progress`: observed elapsed `e = as_of - started_at`; target `b = CONTAINS.target_duration_seconds`.
- `queued`: observed wait `e = as_of - entered_at`; target `b = Transition.target_wait_seconds` for the identified predecessor transition.
- Require finite `e >= 0` and finite `b > 0`, with an identified target source/version. Missing targets are not zero and do not get a guessed global default.
- Severity `s = clamp((e - b) / max(e, b), 0, 1)`. At/below target the value is 0; at twice target it is 0.5. This is a proposed deterministic normalization of observed delay, **not a probability**, learned DK weight or causal estimate.
- Invoice score is the maximum severity among its active executions, with execution ID as a stable tie-breaker. Do not sum service time and transition wait: their clocks and budgets differ. Report the selected component and all evaluated components.
- A reliably completed case with no active executions returns 0 and `completed`. An open case with no current execution, missing timing/budget, conflicting evidence, or truncated context has `score=null` and an explicit unavailable/partial reason. Do not treat missing evidence as neutral 0.5 or healthy 0.

Historical `avg_duration_seconds`, transition `wait_time_seconds`, sample count and window enrich the explanation; they do not prove this invoice's current elapsed time. With only aggregate data, return contextual historical information and `score=null`. Only fresh case evidence makes the invoice-specific factor available. Simulation can produce a numeric result labeled `source=fixture`, `factor_eligible=false`; production scoring must not relabel it as measured live evidence.

### Explanation and output

Example with explicit execution evidence: “Invoice INV-123 is still at Match Invoice to GR after 42 minutes, against a 30-minute target. The selected variant's historical mean is 42 minutes across 100 observations.” The score is `12/42 ≈ 0.286`. If only a historical mean is known: “This variant's invoice-matching activity averages 42 minutes; the invoice's current execution state is unavailable.” Do not claim a root cause or say “stuck because” from aggregate correlation alone.

Proposed result envelope (new API; existing scalar computers remain unchanged):

```json
{
  "name": "process_bottleneck_factor",
  "score": 0.2857142857,
  "status": "available",
  "explanation": "Invoice INV-123 is still at Match Invoice to GR after 42 minutes, against a 30-minute target.",
  "metadata": {
    "domain": "s2p",
    "invoice_id": "INV-123",
    "case_id": "CASE-123",
    "variant_id": "PV-1",
    "model_version": "v1",
    "execution_id": "EX-123-3",
    "activity_id": "ACT-MATCH",
    "transition_id": null,
    "component": "service",
    "elapsed_seconds": 2520,
    "target_seconds": 1800,
    "historical_mean_seconds": 2520,
    "sample_count": 100,
    "as_of": "2026-10-02T12:42:00Z",
    "source": "live",
    "factor_eligible": true,
    "complete": true,
    "formula_version": "p10-delay-v1",
    "evidence_ids": ["CASE-123", "EX-123-3", "ACT-MATCH"],
    "warnings": []
  }
}
```

Also retain scoped edge identifiers, snapshot/window timestamps, target provenance and applied policy values in metadata. Explanation text and score must derive from the same DTO. No shared mutable `last_provenance` state for the new computer.

## 4. Other Graph-Aware Factors

### duplicate_score — extend existing candidate read

Path: `Invoice -SUPPLIED_BY-> Supplier <-SUPPLIED_BY- Invoice` (two hops). Use the existing `query_duplicate_context()` seam. Retain the current clamped amount-similarity formula. Add explicit domain/source/company scope, equal currency, exclusion of the target invoice and deterministic candidate ordering. Distinguish complete no-match from failed/truncated reads. Do not compare USD/EUR amounts or label missing candidates “no duplicates.”

The existing strict ±5% filter and 20-row cap must be documented as candidate-selection policy. A top-K query ordered by amount distance and invoice ID can preserve the highest similarity without an unbounded domain scan. Duplicate output stays float; candidate IDs, selection window, currency and completeness go in per-request evidence. If using an invoice-date window, make it an explicit versioned policy rather than silently changing recall.

Required nodes/edges already exist in the hardened S2P entity migration. Do not create a second duplicate graph or new `duplicate_detection` factor name.

### supplier_exception_history — reuse verified enrichment

Logical evidence path: `Invoice -SUPPLIED_BY-> Supplier <-SUPPLIED_BY- Invoice <-DECIDED_ON- Decision -HAS_OUTCOME-> Outcome`. Use canonical GraphStore verified readers/enrichment; do not introduce a separate outcome-count definition or alter conservation's history readers.

`S2PEnrichmentService.compute_supplier_metrics()` already calculates a provenanced exception rate from supplier-scoped verified decisions, using incorrect outcomes divided by verified decisions, rounded to four places. It uses `min_decisions=20` for eligibility. This measures **verified decision error history**, not necessarily business invoice exceptions; use truthful explanation text and defer any change in meaning to an explicit product decision.

Prefer a fresh, factor-eligible `exception_rate` enrichment (including source IDs/count/version); otherwise compute the same metric through the existing service in a read-only path. A previously written enrichment may be read with `GraphStore.read_entity_enrichment`; P10 scoring must not trigger a materializer write on every request. Missing/insufficient history is distinct from a genuine zero rate. Preserve the scalar interface, with provenance/eligibility beside it, and retain the existing explicit-input fallback policy without claiming such a fallback is verified graph evidence.

The six HYBRID factors keep their direct Invoice-to-entity reads. Reconcile their labels/properties in S2P-GR (section 5); do not implement six redundant graph queries per score.

## 5. S2P-GR Graph Schema Requirements

### Existing definitions and dependency gap

`docs/dcel_design.md` and `docs/process_nodes.md` are absent in copilot-sdk. However, **the process node definitions themselves are present** in [ci-platform/connectors/celonis.py](../../ci-platform/ci_platform/connectors/celonis.py): `ProcessModel`, `ProcessVariant`, `Activity`, `Transition`, with a validated `ProcessFixture` and `ProcessManifestBuilder`. Reuse these definitions. The [older G15 plan](../../ci-platform/docs/implementation_plans/g15_pycelonis_connector.md) is historical: its proposed direct `TRANSITIONS_TO` edge was superseded by explicit Transition nodes in the implementation.

The missing dependency is **integration**, including case/execution definitions and ingestion, variant-specific timing targets/windows, explicit metric units, and S2P invoice linkage. Connector/manifest existence does not prove those nodes are present in the active S2P graph. The [D-CEL diagnostic](design/forward_queue_diagnostic.md) also distinguishes sample/cache behavior from verified live connectivity.

Three representations must be reconciled:

- [Legacy S2P contract](../../s2p-copilot/backend/app/graph_contract.py): nine local node types, nine edges, plus external PipelineSystem; includes ProcessVariant/HAS_ACTIVITY.
- Typed `S2P_GRAPH_CONTRACT` in the same file: 13 node types and 13 edges; omits ProcessVariant/Transition and uses CommodityIndex/ContractClause instead of some legacy entities. Its dictionary compatibility accessor still exposes the legacy definition.
- [Hardened Track-1 migration](../../s2p-copilot/backend/app/migration/s2p_entity_migration.py): actual factor evidence uses Commodity and Contract; invoice edges are SUPPLIED_BY, MATCHED_TO to PO, RECEIVED_AS to receipt, HAS_COMMODITY_INDEX to Commodity, GOVERNED_BY to Contract. This is the recommended compatibility baseline for P10's current factor inputs.

`GraphContract.validate()` checks label/edge consistency and required Decision/DECIDED_ON declarations. It does not enforce property types, uniqueness, units, cardinality or evidence provenance; S2P-GR needs runtime ingestion and read-contract validation for those.

### Common identity and provenance contract

The following tables define the **P10-required subgraph**, not replacements for every existing S2P type. Keep unrelated existing labels/edges intact. Every node/edge is scoped to domain `s2p` and a source/company namespace. Define a stable `entity_id`, retain the natural key, and preserve source record ID, source system, provenance, observed/extracted time and schema version. Qualify process IDs with model revision; the connector's bare `id` is not assumed globally unique. P10 reads a scoped projection in the S2P graph, not an ungoverned join into another copilot's graph.

### Required node types: 14

| Node label | Identity and required P10 fields | Consumers | Existing vs required work |
|---|---|---|---|
| Invoice | invoice_id; supplier_id, amount, currency, quantity, category, invoice_date, payment_days | All factors; process root | Existing; ensure numeric/date types and scoped identity |
| Supplier | supplier_id; payment_terms; exception_rate with provenance if supplied | Supplier history, duplicate, terms | Existing; verified enrichment must not be confused with fixture properties |
| PurchaseOrder | po_id; amount, quantity, currency | Match, variance | Existing migration; typed contract omits some required metrics |
| GoodsReceipt | gr_id; qty_received, amount, invoice/PO identity, currency | Match | Existing; reconcile legacy vs typed receipt linkage |
| Contract | contract_id; max_amount, tax_compliant, regulatory_status, currency | Compliance | Existing migration/legacy; add to typed contract without deleting ContractClause |
| Commodity | commodity_id; volatility, observed_at; optional environmental_risk/carbon_footprint with units | Commodity, environmental | Existing migration/legacy; reconcile typed CommodityIndex rather than pretending labels are interchangeable |
| Decision | decision_id; invoice_id, supplier identity, category, created_at | Supplier verified-history evidence | Existing platform/typed contract; no new write semantics |
| Outcome | outcome_id; decision identity, actual_action, is_correct, verified time | Supplier verified-history evidence | Existing platform HAS_OUTCOME path; preserve canonical reader semantics |
| ProcessModel | model_id mapped from connector id; name, source, extracted_at, model_version | Bottleneck | Existing connector and S2P contracts; scoped projection required |
| ProcessVariant | variant_id mapped from id; process_model_id, model_version, frequency, conformance_rate | Bottleneck | Existing connector/legacy; add to typed contract and actual S2P ingestion |
| Activity | activity_id mapped from id; name; source avg_duration/unit, automation_rate, rework_rate | Bottleneck | Existing; keep identity distinct from execution; per-variant metrics on CONTAINS |
| Transition | transition_id mapped from id; from_activity, to_activity, frequency, conformance, wait_time_seconds, target_wait_seconds, sample_count, window_start/end, target_source/version | Bottleneck queue component | Existing connector type; new S2P projection/typed declaration and timing/variant scope |
| ProcessCase | case_id; source_case_id, state, selected variant/model revision, observed_at, started_at, completed_at nullable | Invoice-specific process state | **New definition and ingestion dependency**; cannot synthesize from supplier correlation |
| ActivityExecution | execution_id; case_id, activity_id, occurrence_index, status, entered_at, started_at nullable, completed_at nullable, predecessor_execution_id nullable, observed_at | Actual elapsed/wait | **New definition and ingestion dependency**; source events must establish timestamps |

For `ActivityExecution`, valid active states in this design are `queued` and `in_progress`; terminal states are `completed` and `cancelled`. Unknown producer states are unavailable until explicitly mapped. Invoice/PO amounts must share currency before comparison. Environmental units must be declared before using any footprint normalization.

### Required edge types: 16

Common provenance/scope fields above apply to every row. Cardinalities are within one scoped, versioned snapshot.

| Edge label | Exact source → target | Key properties/cardinality | Status / consumer |
|---|---|---|---|
| SUPPLIED_BY | Invoice → Supplier | One identified supplier per invoice in this design | Existing migration/typed; duplicate, history, terms |
| MATCHED_TO | Invoice → PurchaseOrder | Preserve linked PO IDs; legacy scalar factors currently select one | Existing canonical migration; match/variance |
| RECEIVED_AS | Invoice → GoodsReceipt | Preserve receipt IDs; do not reinterpret MATCHED_TO-to-receipt as canonical | Existing migration/typed; match |
| GOVERNED_BY | Invoice → Contract | Effective interval and contract ID | Existing migration endpoint label differs from typed ContractClause; compliance |
| HAS_COMMODITY_INDEX | Invoice → Commodity | Observation time/source; preserve current label despite its historical name | Existing migration endpoint label differs from typed CommodityIndex; commodity/environmental |
| DECIDED_ON | Decision → Invoice | Decision and invoice IDs; existing audit provenance | Existing platform/typed; supplier history |
| HAS_OUTCOME | Decision → Outcome | Canonical verification linkage; no P10 write changes | Existing platform; supplier history |
| HAS_VARIANT | ProcessModel → ProcessVariant | Model revision, source snapshot | Existing connector/legacy; bottleneck |
| CONTAINS | ProcessVariant → Activity | sequence_index if known; avg_duration_seconds, target_duration_seconds, target_source/version, sample_count, window_start/end | Existing connector triple, **new S2P triple/properties**; do not confuse ProcessModel→Activity CONTAINS |
| TRANSITION_FROM | Activity → Transition | Source snapshot; source Activity must match from_activity | Existing connector direction; new S2P projection |
| TRANSITION_TO | Transition → Activity | Source snapshot; target Activity must match to_activity | Existing connector direction; new S2P projection |
| IN_PROCESS_CASE | Invoice → ProcessCase | source mapping ID, effective interval; explicitly selected active mapping | **New**; case join |
| OF_VARIANT | ProcessCase → ProcessVariant | assignment_source, model_version, effective_at | **New**; exactly one selected revision for a case snapshot |
| HAS_EXECUTION | ProcessCase → ActivityExecution | Source event/occurrence IDs | **New**; all executions, including repeats/parallelism |
| INSTANCE_OF | ActivityExecution → Activity | Same model revision as the case | **New**; execution-to-definition join |
| HAS_TRANSITION | ProcessVariant → Transition | Scoped variant membership | **New**; prevents mixing transitions across variants |

Totals: **14 required node labels and 16 required edge labels/triples**. Of these, **2 node types and 5 edge types are new to the inspected entity/platform/process implementations**. The remaining 12 nodes/11 edges already have definitions somewhere, but may still need S2P contract declarations, reconciliation, ingestion or new properties. This is not a claim that only seven schema edits are required.

S2P-GR must provide a field-mapping manifest: connector `id` to model_id/variant_id/activity_id/transition_id; duration units to seconds; legacy HAS_ACTIVITY to the canonical variant CONTAINS triple; and revision-scoped transition membership. Preserve existing ProcessModel→Activity CONTAINS/FOLLOWS consumers during migration. Do not create duplicate facts by reading both aliases twice.

**Timing warning:** the DataOps fixture records `avg_duration_hours=0.7` for Match Invoice to GR (**42 minutes**); the S2P fixture records `avg_duration_hours=42.0` (**2,520 minutes**). The ci-platform process fixture records `avg_duration=2520`, interpreted as seconds by the DataOps enterprise adapter. These are distinct fixture datasets, not interchangeable evidence. None supplies the full proposed invoice execution/target contract.

No new Exception, PipelineSystem or ProcessKPI node is required by this minimal factor design. Keep existing nodes if other consumers need them. Root-cause claims about technical systems would require an additional, separately specified causal/evidence path.

## 6. Implementation Sequence

1. **S2P-GR contract reconciliation:** inventory the deployed graph without mutating it; choose the existing hardened entity migration as the factor-input baseline; add the process triples and typed property checks. Preserve legacy consumers with an explicit compatibility plan. Record schema/version/provenance rather than relying on the seed contract's fixed node counts.
2. **D-CEL/SAP producer prerequisites:** map invoice business keys to process cases; ingest case/execution state, explicit units, metric windows and targets. Import connector process manifests without labeling fixtures live. If producer evidence is unavailable, ship an unavailable process card/result, not invented cases.
3. **Read capability:** implement the scoped process DTO/query behind S2PGraphReader with bounded pagination, stable ordering, typed edges and completeness. Keep raw Cypher in the adapter. Add no GraphStore state-bucket workaround.
4. **Existing factors first:** retain the six hybrid formulas; add candidate policy/evidence tests for duplicate_score and wire eligible supplier enrichment. Do not duplicate the reader or enrichment service.
5. **New pure process computer:** add a separate module, deterministic clock/policy inputs and the result envelope. Register it as supplementary evidence in the score/process response and explanation path. The existing `invoice_process_context()` reads process_context saved on decisions; it is not a live process traversal and must not be relabeled as one.
6. **Optional scoring migration:** only after calibration/approval, introduce a new factor schema with nine dimensions, update centroids/DK/checkpoint readers and API contracts together, and verify old-model compatibility. Until then the active scoring tensor remains `(5,5,8)`.

Future implementation scope: S2P factor module, reader/capability adapter, score/process response models, graph contract/migration and tests; ci-platform connector/AGE adapter only where the new source/query capabilities require it. SDK documentation is the only current deliverable. There are no source/test changes in this prompt.

## 7. Test Strategy

Estimate **36 new cases**, separate from existing regression suites:

| Layer | Estimated cases | What they prove |
|---|---:|---|
| Schema/manifest contracts | 8 | Exact node/edge triples and directions; unit mappings; natural-key/revision uniqueness; missing case linkage; repeated activities; fixture provenance; invalid time/metric types; contract alias compatibility |
| Pure process computation | 12 | Below/at/twice budget; 42-minute example; zero/negative/nonfinite target handling; absent timing; completed vs missing active state; queue vs service clocks; parallel max; stale/truncated evidence; deterministic as_of; no causal overclaim |
| Existing factor integration/contracts | 6 | Eight-factor order unchanged; duplicate supplier/currency/ID filtering; bounded candidate completeness; supplier verified-rate/eligibility; missing vs zero history; hybrid graph perturbation/fallback provenance |
| AGE integration | 10 | Real fixture-manifest ingestion; exact process path; repeated/parallel execution joins; cross-domain and source isolation; variant/revision isolation; pagination completeness; missing capability/source; score envelope; zero decision/outcome writes on reads; compatibility with existing entity factor queries |

Use fresh `InMemoryGraphStore(profile="test")` for decision/outcome/enrichment contract tests. It cannot prove arbitrary process traversal: pair it with an explicit typed process-reader test double for pure/composition tests, and state that limitation in test names. Do not pretend `write_decision()` creates an Activity or ProcessCase. Tests must call the production computation and assert evidence IDs and values, not reproduce its formula in a fixture and test that fixture.

Use disposable, explicitly configured AGE graphs for traversal/integration tests, seeded through the S2P-GR ingestion path. Assert real edge directions, same business IDs in different scopes, duplicates/rework, and cardinality. Pure tests must make no graph/network connection even with an ambient AGE configuration. Existing factor integration tests and S2P/SDK suites remain regression gates during implementation; none was run here.

### Design-time type checks

The reader's use of traversal methods through a `GraphStore` annotation and config's optional shared import warranted checks. From `s2p-copilot`, the requested `python -m mypy <file> --config-file pyproject.toml` commands were run individually for:

- `backend/app/graph/s2p_graph_reader.py` — PASS, no issues in one source file.
- `backend/app/domains/s2p/config.py` — PASS, no issues in one source file.
- `backend/app/domains/s2p/factors.py` — PASS, no issues in one source file.

These results use the repository configuration (`follow_imports=skip`); they do not establish that the broader cross-repository traversal capability is statically guaranteed. No type errors were reported by these checks and no fixes were made.

## 8. Open Questions

There are **7 open decisions/dependency questions**. Recommended defaults are explicit; none should be silently guessed by the implementation.

1. **Invoice-to-case producer:** which SAP/Celonis business key and source events establish the real ProcessCase/ActivityExecution records? The process definitions exist, but these invoice-specific definitions/data are missing from the inspected path. S2P-GR/D-CEL must supply them before claiming current delay.
2. **Targets and units:** who owns target service/wait budgets, freshness windows and unit conversion for each model revision? Use producer-declared units and a versioned target source; never infer that 42 means minutes. Missing targets make the process score unavailable.
3. **Contract deployment:** which graph-contract/migration version is deployed? The legacy, typed and hardened migration representations disagree. Adopt the section 5 triples for P10, but validate deployed consumers before replacing any aliases.
4. **Reader ownership:** can S2P-GR add the typed, bounded process read capability to its canonical AGE adapter? Base GraphStore is insufficient. Do not implement arbitrary graph traversal in the factor or add backend-private unwrapping to new code.
5. **Scoring rollout:** when should the process result become a ninth scored dimension? Recommended initial release is evidence-only; model migration/calibration is a separate approved stage, not an implicit registry append.
6. **Supplier metric meaning:** is verified recommendation error rate the intended definition of supplier_exception_history, or should it measure actual business invoice exceptions? Reuse the current enrichment definition initially and label it accurately; a semantic change needs its own numerator/denominator contract.
7. **Multi-document/process ambiguity:** how should several POs/receipts, concurrent cases and cancellation/reopening be selected or aggregated? Preserve current scalar-factor behavior for compatibility; the new process factor must abstain on ambiguous case selection and retain distinct execution occurrences. Agree on explicit policies before broad production rollout.
