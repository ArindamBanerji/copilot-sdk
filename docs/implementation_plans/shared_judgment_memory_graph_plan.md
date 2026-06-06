# Shared governed judgment-memory graph plan

## Non-negotiable product architecture

All copilots must participate in one governed live judgment-memory graph. Local SQLite stores are acceptable as local development and test adapters, but they are not the canonical product memory.

Judgment memory includes:

- episodic memory: decisions, outcomes, overrides, and verification history
- semantic memory: domain entities and context relationships
- procedural memory: rules, AgentEvolver variants, promotions, rollbacks, and operational patterns
- judgment memory: centroid geometry, factor quality, fingerprints, IKS, conservation state, and transfer patterns

The product target is not "each copilot has a GraphStore-shaped database." The target is one physical governed graph substrate with domain partitioning, shared audit policy, shared traversal, and cross-copilot transfer queries.

## Current implementation map

### SOC

- Store for decisions: AGE-backed SOC graph through the SOC backend graph client. `demo.py` starts SOC with `GRAPH_BACKEND=age` and `GRAPH_DSN`.
- Store for outcomes: AGE-backed graph state and SOC decision/outcome synchronization during startup.
- Store for evidence/audit: SOC backend bootstraps audit chain state from AGE and exposes graph-backed evidence/governance behavior.
- Store for evolution: SOC backend uses graph-backed evolution/bootstrap behavior, including AGE nodes and edges for evolution events and variants.
- Store for centroid/judgment state: SOC queries graph state for snapshots, centroid evolution, IKS, and related judgment analytics.
- Physical backend: Apache AGE/PostgreSQL.
- Graph/domain: SOC graph configured by the SOC AGE DSN and graph name.

### Trading

- Store for decisions: `SQLiteGraphStore` constructed in `apps/trading/backend/app/main.py` with domain `trading` and decision prefix `TRD-`.
- Store for outcomes: same SQLite store through `write_outcome`.
- Store for evidence/audit: SDK evidence, journal, analytics, correlation, prescore, promotion, regime, social, broker, webhook, and self-computation routers are mounted against the Trading SQLite store or scorer proxy.
- Store for evolution: SDK evolution router is mounted with a Trading SQLite store factory.
- Store for centroid/judgment state: SQLite centroid checkpoints via the SDK `GraphStore` protocol.
- Physical backend: local persistent SQLite file, normally under `CI_DATA_DIR` or the app data path.
- Graph/domain: domain-scoped SQLite adapter, not the shared governed graph.

### Purchasing

- Store for decisions: `SQLiteGraphStore` constructed in `apps/purchasing/backend/app/main.py` with domain `purchasing` and decision prefix `PUR-`.
- Store for outcomes: same SQLite store through `write_outcome`.
- Store for evidence/audit: SDK routers mounted against the Purchasing SQLite store.
- Store for evolution: SDK evolution router reads/writes evolution events from the Purchasing SQLite store.
- Store for centroid/judgment state: SQLite centroid checkpoints via the SDK `GraphStore` protocol.
- Physical backend: local persistent SQLite file, normally under `CI_DATA_DIR` or the app data path.
- Graph/domain: domain-scoped SQLite adapter, not the shared governed graph.

### DataOps

- Store for decisions: `SQLiteGraphStore` constructed in `apps/dataops/backend/app/main.py` with domain `dataops` and decision prefix `DOPS-`.
- Store for outcomes: same SQLite store through `write_outcome`.
- Store for evidence/audit: SDK evidence and DataOps AE/evolution routers mounted against the DataOps SQLite store.
- Store for evolution: DataOps seeds and queries evolution events in the SQLite store.
- Store for centroid/judgment state: SQLite centroid checkpoints via the SDK `GraphStore` protocol.
- Physical backend: local persistent SQLite file, normally under `CI_DATA_DIR` or the app data path.
- Graph/domain: domain-scoped SQLite adapter. `demo.py` has a DataOps AGE DSN for graph-mode setup, but the current DataOps backend wiring still constructs `SQLiteGraphStore`.

### S2P

- Store for decisions: `s2p-copilot/backend/app/main.py` constructs `SQLiteGraphStore(..., domain="s2p", decision_id_prefix="S2P-")`.
- Store for outcomes: same SQLite store through real score/confirm/learn paths.
- Store for evidence/audit: S2P routers expose evidence, governance, audit export, preview, performance, evolution, and transfer behavior using `app.state.scorer` and `app.state.graph_store`.
- Store for evolution: `S2PEvolutionService(app.state.scorer)` and related routers use app-local scorer/store state.
- Store for centroid/judgment state: SQLite centroid checkpoints via the SDK `GraphStore` protocol.
- Physical backend: local persistent SQLite file at the S2P backend data path.
- Graph/domain: domain-scoped SQLite adapter, not the shared governed graph.

### Shared SDK and CI platform pieces already present

- `copilot_sdk.graph.GraphStore` defines the common decision, outcome, count, centroid, archive, and close surface.
- `SQLiteGraphStore` implements that protocol with tables for decisions, outcomes, centroid checkpoints, evolution events, RL state, decision-entity edges, and archive rows.
- `ci-platform` contains an `AGEGraphStore` and `AGEGraphStoreAdapter`. The adapter exposes SDK-compatible methods including decision/outcome writes, counts, centroid checkpoints, evolution events, entity links, archive no-ops, and close.
- This proves the bridge is started, but not that the product currently has one shared graph. The SDK apps and S2P still construct SQLite stores directly.

## Gap analysis

### Common GraphStore abstraction

The apps mostly share a common GraphStore-shaped interface. This is useful because score, outcome, evidence, conservation, and evolution code can be moved behind a common storage factory.

### Same graph technology

SOC uses AGE today. The SDK apps and S2P do not. DataOps has AGE DSN setup in `demo.py`, but its backend still constructs SQLite.

### Same physical governed judgment-memory graph

This is the missing product architecture. Current local demo wiring creates separate physical stores:

- SOC: AGE
- Trading: SQLite
- Purchasing: SQLite
- DataOps: SQLite
- S2P: SQLite

Separate stores cannot support governed cross-copilot judgment memory without export/import, dual-write, or a shared backend. Transfer/status endpoints can present a story, but they do not by themselves make decisions, outcomes, centroids, evidence, evolution events, and transfer patterns queryable as one governed graph.

## Canonical graph model

The shared graph should be append-first and domain-partitioned. Mutable convenience properties can exist for query speed, but durable lineage should be represented as nodes and edges.

### Core nodes

`Domain`

- Properties: `domain_id`, `name`, `copilot`, `version`, `environment`, `owner`, `created_at`
- Purpose: stable partition for all domain-scoped memory.

`Decision`

- Properties: `decision_id`, `domain`, `category`, `category_index`, `recommended_action`, `recommended_index`, `confidence`, `status`, `source_endpoint`, `scorer_version`, `preset_version`, `factor_schema_version`, `created_at`, `metadata`
- Purpose: episodic score-time record. Real scoring writes this node.

`Outcome`

- Properties: `outcome_id`, `decision_id`, `actual_action`, `actual_index`, `is_correct`, `reward`, `verified_at`, `verifier`, `override_reason`, `metadata`
- Purpose: verified result and learning signal.

`FactorVector`

- Properties: `vector_id`, `decision_id`, `dimension`, `factor_names`, `factor_values`, `factor_names_hash`, `shape`, `schema_version`, `created_at`
- Purpose: immutable score-time factor evidence.

`CentroidCheckpoint`

- Properties: `checkpoint_id`, `domain`, `category`, `action`, `centroids`, `decisions_count`, `verified_count`, `iks`, `shape`, `factor_names_hash`, `created_at`, `metadata`
- Purpose: judgment geometry history.

`Fingerprint`

- Properties: `fingerprint_id`, `domain`, `factor_names`, `factor_stats`, `skipped_incompatible`, `window`, `created_at`, `metadata`
- Purpose: factor quality and drift snapshot.

`ConservationStatus`

- Properties: `status_id`, `domain`, `V`, `q`, `alpha`, `theta_min`, `verified_count`, `correct_count`, `total_decisions`, `status`, `computed_at`, `counts_scope`, `policy_version`
- Purpose: auditable conservation calculation snapshot.

`EvolutionEvent`

- Properties: `event_id`, `domain`, `event_type`, `rule_name`, `variant_id`, `status`, `source_copilot`, `source_rule`, `metric`, `shadow_batch_size`, `min_shadow_batches`, `created_at`, `metadata`
- Purpose: procedural memory and AgentEvolver trace.

`EvidenceReceipt`

- Properties: `receipt_id`, `domain`, `payload_hash`, `previous_hash`, `chain_index`, `actor`, `source_route`, `created_at`, `metadata`
- Purpose: tamper-evident audit chain material.

`DomainContext`

- Properties: `entity_id`, `domain`, `entity_type`, `natural_key`, `attributes`, `created_at`, `updated_at`
- Purpose: semantic memory. Examples include SOC alerts, S2P invoices, suppliers, trades, purchase orders, datasets, incidents, controls, and process activities.

`TransferPattern`

- Properties: `pattern_id`, `source_domain`, `target_domain`, `source_rule`, `target_rule`, `factor_mapping`, `confidence`, `validation_status`, `conservation_status`, `created_at`, `metadata`
- Purpose: governed cross-copilot pattern transfer.

`Rule` / `Procedure`

- Properties: `rule_id`, `domain`, `rule_family`, `parameters`, `status`, `owner`, `policy_version`, `created_at`, `metadata`
- Purpose: governed operational procedure state.

### Core edges

- `(Decision)-[:IN_DOMAIN]->(Domain)`
- `(Decision)-[:ABOUT]->(DomainContext)`
- `(Decision)-[:HAS_FACTOR_VECTOR]->(FactorVector)`
- `(Decision)-[:HAS_OUTCOME]->(Outcome)`
- `(Decision)-[:EMITTED_RECEIPT]->(EvidenceReceipt)`
- `(Decision)-[:SNAPSHOT_AFTER]->(CentroidCheckpoint)`
- `(Decision)-[:USED_RULE]->(Rule)`
- `(Decision)-[:TRIGGERED_EVOLUTION]->(EvolutionEvent)`
- `(EvolutionEvent)-[:PROMOTED_RULE]->(Rule)`
- `(EvolutionEvent)-[:ROLLED_BACK_RULE]->(Rule)`
- `(CentroidCheckpoint)-[:DERIVED_FROM]->(Decision)`
- `(Fingerprint)-[:SUMMARIZES_DOMAIN]->(Domain)`
- `(ConservationStatus)-[:SUMMARIZES_DOMAIN]->(Domain)`
- `(TransferPattern)-[:FROM_DOMAIN]->(Domain)`
- `(TransferPattern)-[:TO_DOMAIN]->(Domain)`
- `(TransferPattern)-[:DERIVED_FROM]->(EvolutionEvent)`
- `(Rule)-[:APPLIES_TO]->(DomainContext)`

## Decision lifecycle in the shared graph

Decision lifecycle should be explicit and queryable.

`pending`

- Created by real scoring.
- Has a `Decision` and `FactorVector`.
- May have evidence receipt and context edges.
- Has no verified `Outcome`.
- Should not count as correct. Whether it contributes to V is an explicit conservation policy choice.

`confirmed`

- Created when an outcome is recorded and the recommended action is accepted or verified as correct.
- Adds an `Outcome` node and `HAS_OUTCOME` edge.
- Updates current `Decision.status` to `confirmed` for query speed.

`overridden`

- Created when a human or downstream system selects a different action.
- Adds an `Outcome` node with actual action, correctness, reward, and override reason.
- Updates current `Decision.status` to `overridden`.
- Must remain part of audit and learning history. It must not be erased or relabeled.

`expired`

- Reserved future state for unverified pending decisions that should no longer affect online policy metrics.
- Should be represented by a lifecycle event or status transition, not by deleting the original decision.
- Default migration should avoid introducing expiry until policy owners define the retention window.

## Conservation semantics

The current code paths use domain counts such as total decisions, verified decisions, and correct decisions. The shared graph model should make those counts explicit and cheap:

- `total_decisions`: count of `Decision` nodes for a domain and environment, filtered by the active conservation policy.
- `verified_count`: count of `Decision` nodes with a verified `Outcome`.
- `correct_count`: count of verified outcomes where `is_correct=true`.
- `q`: `correct_count / verified_count` when verified decisions exist, otherwise the existing insufficient-data behavior.
- `alpha`: domain policy penalty ratio or conservation coefficient.
- `V`: conservation volume. Current routes have used total decision count as V in places. A verified-only V is a strong architecture candidate because preview/read activity and unverified pending records should not inflate conservation exposure. This is an architecture decision pending review, not a silent implementation change.

Every conservation response should be backed by either a live aggregate query or a persisted `ConservationStatus` node that records the input counts, policy version, and timestamp.

## AGE implementation plan

### SOC

SOC already runs against AGE in the demo launcher. It should become the first reference consumer for the canonical node and edge vocabulary, not a separate schema island.

Steps:

1. Document the existing SOC AGE labels and edge names.
2. Map SOC-specific nodes into the canonical labels without breaking existing SOC routes.
3. Add compatibility views or adapter methods if SOC routes need old label names during transition.
4. Verify SOC audit chain, evolution, centroid, and IKS queries still resolve from AGE.

### S2P

S2P should be the first non-SOC migration candidate because recent failures exposed the cost of hidden read writes, graph growth, and fragmented persistent state.

Steps:

1. Introduce a storage factory in S2P backend startup: SQLite local adapter by default for unit tests, AGE adapter when `GRAPH_BACKEND=age`.
2. Keep `CompoundingScorer` using the `GraphStore` protocol.
3. Extend `AGEGraphStoreAdapter` if S2P needs fields not currently represented in AGE nodes, especially invoice context links, process context, audit receipts, performance aggregates, and evolution dimensions.
4. Add an S2P SQLite-to-AGE migration command that writes `Decision`, `Outcome`, `FactorVector`, `CentroidCheckpoint`, `EvidenceReceipt`, and `EvolutionEvent` nodes.
5. Run S2P in shadow compare mode: same route responses from SQLite and AGE counts/fingerprints/conservation before switching demo/product.
6. Switch demo S2P to AGE-backed graph once parity tests pass.

### Trading, Purchasing, and DataOps

These apps should move through the same SDK factory path rather than each app hand-constructing SQLite.

Steps:

1. Add a shared SDK graph-store factory that accepts `GRAPH_BACKEND`, `GRAPH_DSN`, `AGE_GRAPH_NAME`, `CI_DATA_DIR`, domain, and decision prefix.
2. Convert Trading/Purchasing/DataOps main files to use the factory without changing scoring semantics.
3. Preserve local SQLite as the default for fast unit tests.
4. Enable AGE in demo/product wiring.
5. Migrate existing demo bundles and seed fixtures to either load into AGE or restore through GraphStore protocol.

## SQLite local adapter role

SQLite remains valuable, but only with a clear boundary:

- local development adapter
- unit/integration test adapter
- deterministic fixture adapter
- offline fallback for demos that do not claim shared judgment memory

SQLite must continue to implement the same `GraphStore` protocol and should mirror canonical graph state:

- `decisions.status` may mirror `Decision.status`
- `outcomes` mirrors `Outcome`
- `centroid_checkpoints` mirrors `CentroidCheckpoint`
- `evolution_events` mirrors `EvolutionEvent`
- `decision_entity_edges` mirrors `Decision` to `DomainContext` edges
- archive tables remain adapter-specific retention implementation, not canonical deletion

SQLite should never be described as the product judgment-memory graph unless it is a temporary local adapter mode.

## Migration options

### Option A: S2P first to AGE, then SDK apps

Pros:

- Targets the current instability surface first.
- Keeps blast radius smaller than an all-app migration.
- Exercises score, learn, preview, conservation, audit export, performance, evolution, and transfer paths.

Cons:

- Leaves Trading/Purchasing/DataOps fragmented during the transition.
- Requires temporary demo messaging that distinguishes S2P migrated state from other SDK apps.

Blast radius:

- S2P backend startup, graph-store factory, S2P tests, AGE integration tests, demo launcher S2P env.

Tests:

- S2P GraphStore parity tests.
- SQLite-to-AGE migration tests.
- S2P score/confirm/learn with AGE.
- S2P conservation, fingerprint, audit export, performance, preview, and evolution tests.
- Cross-domain transfer query against SOC and S2P in the same AGE graph.

Migration sequence:

1. Harden AGE adapter conformance.
2. Add S2P storage factory.
3. Add migration and parity tests.
4. Run S2P AGE in shadow.
5. Switch S2P demo/product to AGE.
6. Repeat for SDK apps.

### Option B: all SDK apps via AGE-backed GraphStore

Pros:

- Aligns the product architecture quickly.
- Forces one common factory and one conformance suite.
- Reduces long-lived transition debt.

Cons:

- Larger blast radius.
- More parallel route-specific issues.
- Harder to attribute regressions.

Blast radius:

- SDK graph factory, Trading, Purchasing, DataOps, S2P, demo launcher, migration tools, test harnesses.

Tests:

- Full SDK app GraphStore parity.
- All app backend suites under SQLite and AGE.
- Full Playwright gates with shared AGE.

Migration sequence:

1. Build factory and AGE conformance.
2. Convert all apps behind env switch.
3. Run SQLite default tests.
4. Run AGE integration tests.
5. Switch demo/product.

### Option C: dual-write/write-through from SQLite to AGE during transition

Pros:

- Allows live comparison.
- Preserves current local app behavior while building shared graph confidence.
- Good for migration auditability.

Cons:

- Consistency complexity.
- Requires idempotent writes and replay handling.
- Can hide source-of-truth ambiguity if not time-boxed.

Blast radius:

- GraphStore wrapper, retry semantics, idempotency keys, migration/reconciliation tools.

Tests:

- Dual-write idempotency.
- SQLite/AGE count and payload parity.
- Failure behavior when AGE is unavailable.
- Replay and reconciliation tests.

Migration sequence:

1. Implement write-through wrapper.
2. Dual-write non-production demo.
3. Reconcile counts and fingerprints.
4. Promote AGE to read source.
5. Retire SQLite writes for product mode.

### Option D: local stores only for tests, shared AGE for demo/product

Pros:

- Cleanest product boundary.
- Keeps fast tests fast.
- Avoids presenting local SQLite as product memory.

Cons:

- Requires robust AGE CI/integration lane.
- Local-only bugs may differ from AGE behavior unless conformance tests are strong.

Blast radius:

- Demo launcher, environment configuration, integration test setup, documentation.

Tests:

- SQLite adapter unit tests.
- AGE adapter conformance tests.
- Demo/product smoke tests against shared AGE.
- Cross-copilot traversal tests.

Migration sequence:

1. Keep SQLite as default in unit tests.
2. Make demo/product require AGE.
3. Add AGE integration lane.
4. Update demo display and docs.

## Track B conservation lifecycle plan under shared graph

The prior status-column direction maps naturally to graph state:

- `Decision.status` is the fast current-state property.
- Lifecycle transitions are append-only `EvidenceReceipt` or `DecisionLifecycleEvent` records.
- `Outcome` nodes create the verified lifecycle.
- `overridden` decisions retain both recommended and actual action.
- `expired` is a future policy transition, not deletion.

For AGE:

- Current status is a property on `Decision`.
- Transitions are append-only event/receipt nodes.
- Conservation queries count `Decision` and `Outcome` nodes according to active policy.
- `ConservationStatus` snapshots record inputs and policy version.

For SQLite:

- Add or retain status columns only as adapter mirrors.
- Preserve `outcomes` as the source of verified/correct truth.
- Add lifecycle/event rows if needed for audit parity.

Open architecture decision:

- Whether V should be all scored decisions or verified-only decisions. Verified-only V better protects conservation from read-path or pending-decision growth, but it must be reviewed because it changes policy interpretation.

## Demo.py implications

Current display categories are implementation details:

- `[AGE]`: SOC only in current demo wiring.
- `[persistent]`: app has local persistent SQLite state.

Recommended display vocabulary:

- `[shared judgment graph]`: backed by the canonical AGE graph and participating in cross-copilot memory.
- `[local adapter]`: SQLite local development/test adapter.
- `[persistent local]`: durable local state, not shared product memory.
- `[AGE]`: reserve only for low-level backend detail if needed.

Recommended target display:

- SOC `[shared judgment graph]`
- Trading `[shared judgment graph]`
- Purchasing `[shared judgment graph]`
- DataOps `[shared judgment graph]`
- S2P `[shared judgment graph]`

During transition, the display should explicitly say which apps are still `[persistent local]` so the architecture gap is visible.

## Cross-copilot test strategy

### Local adapter tests

- GraphStore protocol conformance for SQLite and AGE adapters.
- Decision/outcome write/read/count parity.
- Centroid checkpoint save/load parity.
- Evolution event save/query parity.
- Entity link parity.
- Archive behavior documented as adapter-specific.

### AGE integration tests

- Shared graph startup and schema bootstrap.
- Domain partitioning in one graph.
- Concurrent writes across domains.
- Count and aggregate performance on large data.
- Failure behavior when AGE is unavailable.

### Shared memory traversal tests

- Query from S2P invoice decision to supplier, evidence receipt, outcome, centroid checkpoint, and conservation snapshot.
- Query from SOC-origin transfer pattern to S2P rule/evolution event.
- Query DataOps source lineage without misattributing DataOps-local rules as S2P.

### Conservation tests

- V/q/alpha calculation from graph counts.
- Pending vs verified vs overridden behavior.
- Conservation snapshot auditability.
- SQLite and AGE parity for identical fixture state.

### Transfer/evolution tests

- Evolution event shadow/promotion/rollback lineage.
- Transfer pattern source and target domain evidence.
- Cross-copilot governance approval trace.

## Risks and mitigations

- Risk: AGE adapter does not fully match SDK GraphStore semantics.
  - Mitigation: conformance tests become the first milestone.
- Risk: Graph label drift between SOC and SDK apps.
  - Mitigation: canonical vocabulary and compatibility views.
- Risk: dual-write consistency bugs.
  - Mitigation: use dual-write only as a bounded transition, with idempotency keys and reconciliation reports.
- Risk: shared graph test flakiness.
  - Mitigation: isolated graph names per test run and fixture teardown.
- Risk: conservation semantics change accidentally during migration.
  - Mitigation: preserve current semantics first, then review verified-only V as a separate policy change.
- Risk: read-looking endpoints continue to write.
  - Mitigation: classify routes as command/query. Query routes may read scorer state but must not write decisions unless they create explicit governed observation nodes.

## Open questions for GPT-5.5/O1/Opus review

- Should V be all decisions or verified decisions in the product conservation policy?
- Should preview/read endpoints be pure queries, or should they create explicit `Observation` nodes distinct from `Decision` nodes?
- Is `AGEGraphStoreAdapter` sufficient as the production adapter foundation, or should a new governed graph service own writes and expose GraphStore as a client?
- How should SOC's existing AGE schema be mapped to the canonical vocabulary without breaking current SOC routes?
- What is the minimum evidence receipt required for every score-time decision?
- Should transfer patterns be first-class graph nodes or derived views over evolution events?
- Should demo/product ever run with local SQLite stores while claiming shared memory?

## Recommended implementation sequence

1. Freeze this document as the architecture target and review it with GPT-5.5/O1/Opus.
2. Add GraphStore conformance tests covering SQLite and `AGEGraphStoreAdapter`.
3. Define canonical labels, edge names, property names, and versioning rules.
4. Harden `AGEGraphStoreAdapter` until it passes SDK protocol conformance.
5. Add a shared SDK graph-store factory with explicit backends: `sqlite`, `age`.
6. Migrate S2P first behind the factory and run SQLite/AGE parity tests.
7. Add SQLite-to-AGE migration tooling for S2P.
8. Run S2P AGE in shadow comparison against current SQLite state.
9. Switch S2P demo/product to shared AGE.
10. Convert Trading, Purchasing, and DataOps to the same factory.
11. Align SOC AGE schema with canonical vocabulary or compatibility views.
12. Switch demo display from implementation labels to memory-role labels.
13. Add cross-copilot shared traversal tests for SOC to S2P, DataOps lineage, Trading/Purchasing judgment history, and global conservation/evolution dashboards.

