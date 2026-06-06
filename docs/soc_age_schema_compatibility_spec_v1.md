# SOC AGE Schema Compatibility Spec v1

## Purpose

This spec maps the current SOC AGE schema to the canonical Judgment Memory v2.7 and GraphStore Protocol v2 v1.8 vocabulary without modifying the live graph.

The goal is compatibility planning only. No labels, edges, properties, views, or migrations are created by this document. The spec exists so Protocol v2 conformance and later S2P/SDK AGE migration do not assume that SOC already uses canonical labels everywhere.

Authoritative inputs:

- `docs/judgment_memory_v2_7.md`
- `docs/protocol_v2_design_v1_8.md`
- Latest live SOC AGE inventory run against `soc_graph`

## Current SOC schema summary

Graph:

- AGE graph name: `soc_graph`
- Connection discovered from SOC `.env` and `ci-platform` AGE client wiring:
  - `GRAPH_BACKEND=age`
  - `DATABASE_URL=postgresql://postgres:***@localhost:5433/soc_copilot?connect_timeout=5`
  - `AGE_GRAPH_NAME` defaults to `soc_graph`

Live vertex labels with nonzero rows:

- `Alert`
- `Asset`
- `AttackPattern`
- `Campaign`
- `DataQualityAlert`
- `Decision`
- `DecisionDistanceLog`
- `DeploymentState`
- `EvolutionEvent`
- `PipelineSystem`
- `ProfileSnapshot`
- `ShadowDecision`
- `ThreatIndicator`
- `ThreatIntel`
- `User`

Live edge labels with nonzero rows:

- `AFFECTS`
- `CLASSIFIED_AS`
- `DECIDED_ON`
- `DETECTED_ON`
- `FEEDS`
- `HAS_INDICATOR`
- `INVOLVES`
- `MEMBER_OF`

Key live counts from the inventory:

| Item | Count |
|---|---:|
| `Decision` | 5053 |
| `DECIDED_ON` | 5053 |
| `DecisionDistanceLog` | 2136 |
| `ShadowDecision` | 1500 |
| `Alert` | 645 |
| `INVOLVES` | 645 |
| `DETECTED_ON` | 645 |
| `CLASSIFIED_AS` | 645 |
| `HAS_INDICATOR` | 633 |
| `MEMBER_OF` | 367 |
| `EvolutionEvent` | 122 |
| `TRIGGERED_EVOLUTION` | 0 |
| `ProfileSnapshot` | 4 |
| `DeploymentState` | 1 |
| `DataQualityAlert` | 20 |
| `AFFECTS` | 20 |
| `PipelineSystem` | 9 |
| `FEEDS` | 9 |

Topology highlights:

- `(Decision)-[:DECIDED_ON]->(Alert)`
- `(Alert)-[:INVOLVES]->(User)`
- `(Alert)-[:DETECTED_ON]->(Asset)`
- `(Alert)-[:CLASSIFIED_AS]->(AttackPattern)`
- `(Alert)-[:HAS_INDICATOR]->(ThreatIndicator)`
- `(Alert)-[:MEMBER_OF]->(Campaign)`
- `(DataQualityAlert)-[:AFFECTS]->(PipelineSystem)`
- `(PipelineSystem)-[:FEEDS]->(PipelineSystem)`

Important current representations:

- Outcome is not a first-class graph node. SOC uses `Decision.outcome` and `Decision.correct`.
- FactorVector is not a first-class graph node. SOC embeds `factor_vector` on `Decision`.
- EvidenceReceipt is not a first-class AGE node. The hash-chain ledger exists outside the graph and some audit fields may be embedded on `Decision`.
- `ProfileSnapshot` partially maps to canonical `CentroidCheckpoint` and judgment state.
- `DecisionDistanceLog` overlaps with fingerprint and judgment telemetry.
- `EvolutionEvent` nodes exist, but the live graph currently has no `TRIGGERED_EVOLUTION` edges.
- `DataQualityAlert` and `PipelineSystem` already exist inside `soc_graph`; they are useful for shared graph proof, but they need explicit domain partitioning before being used as cross-copilot evidence.

## Canonical vocabulary target

Canonical node labels from Judgment Memory v2.7 / Protocol v2:

- `Decision`
- `Outcome`
- `FactorVector`
- `Observation`
- `Domain`
- `DomainContext`
- `EvolutionEvent`
- `Rule`
- `TransferPattern`
- `EvidenceReceipt`
- `CentroidCheckpoint`
- `Fingerprint`
- `ConservationStatus`

Canonical edge concepts include:

- `Decision -[:IN_DOMAIN]-> Domain`
- `Decision -[:ABOUT]-> DomainContext`
- `Decision -[:HAS_FACTOR_VECTOR]-> FactorVector`
- `Decision -[:HAS_OUTCOME]-> Outcome`
- `Decision -[:EMITTED_RECEIPT]-> EvidenceReceipt`
- `Decision -[:SNAPSHOT_AFTER]-> CentroidCheckpoint`
- `Decision -[:USED_RULE]-> Rule`
- `Decision -[:TRIGGERED_EVOLUTION]-> EvolutionEvent`
- `Observation -[:IN_DOMAIN]-> Domain`
- `Observation -[:ABOUT]-> DomainContext`
- `Observation -[:HAS_FACTOR_VECTOR]-> FactorVector`
- `EvolutionEvent -[:PROMOTED_RULE|ROLLED_BACK_RULE]-> Rule`
- `Rule -[:APPLIES_TO]-> DomainContext`
- `CentroidCheckpoint -[:DERIVED_FROM]-> Decision`
- `Fingerprint -[:SUMMARIZES_DOMAIN]-> Domain`
- `ConservationStatus -[:SUMMARIZES_DOMAIN]-> Domain`
- `TransferPattern -[:FROM_DOMAIN]-> Domain`
- `TransferPattern -[:TO_DOMAIN]-> Domain`
- `TransferPattern -[:DERIVED_FROM]-> EvolutionEvent`

Canonical edge vocabulary is governed by `judgment_memory_v2_7.md` §4.2.
This compatibility spec may not widen canonical edge targets. Any future
proposal to derive `TransferPattern` from `Rule` or `Fingerprint`, or to
apply `Rule` directly to `Domain`, must be handled as a Judgment Memory /
Protocol revision before it becomes canonical vocabulary.

Locked semantic constraints:

- V = verified decisions only.
- Alpha is category coverage among verified decisions.
- Preview/read paths do not create `Decision` nodes.
- `Observation` nodes are excluded from V and AgentEvolver flywheel.
- Score-time `Decision` writes are preserved.
- SQLite remains local/test adapter only.
- AGE/PostgreSQL+AGE is canonical product graph.

## Mapping table

| Current SOC item | Type | Current representation | Canonical equivalent | Action | Migration risk | Notes |
|---|---|---|---|---|---|---|
| `Decision` | vertex | First-class node with `decision_id`, `category`, `action`, `confidence`, `factor_vector`, `outcome`, `correct`, timestamps | `Decision` | keep + add canonical properties/edges | Medium | Preserve existing routes. Add `domain`, `status`, `source`, and canonical edge writes forward. |
| `Decision.outcome` / `Decision.correct` | properties | Embedded verification fields on `Decision` | `Outcome` + `Decision -[:HAS_OUTCOME]-> Outcome` | migrate embedded property to node | High | Backfill must preserve verified-only V and avoid double-counting. |
| `Decision.factor_vector` | property | Serialized vector embedded on `Decision` | `FactorVector` + `Decision -[:HAS_FACTOR_VECTOR]-> FactorVector` | migrate embedded property to node | Medium | Need factor names, schema version, shape, hash. Existing values can seed backfill. |
| `Alert` | vertex | SOC alert context | `DomainContext` | add compatibility projection / dual-label later | Medium | Keep SOC label. Add `DomainContext` typing or view for canonical traversal. |
| `User` | vertex | SOC user context | `DomainContext` | add compatibility projection / dual-label later | Medium | Preserve SOC-specific fields. |
| `Asset` | vertex | SOC asset context | `DomainContext` | add compatibility projection / dual-label later | Medium | Preserve SOC-specific fields. |
| `AttackPattern` | vertex | MITRE-like pattern context | `DomainContext` and possibly `Rule` | investigate | Medium | May remain context; only promoted procedures should become `Rule`. |
| `ThreatIndicator` | vertex | IOC/threat context | `DomainContext` | add compatibility projection / dual-label later | Low | Straight context mapping. |
| `ThreatIntel` | vertex | Enrichment/intel context | `DomainContext` | add compatibility projection / dual-label later | Low | Straight context mapping. |
| `Campaign` | vertex | Alert grouping/campaign context | `DomainContext` | add compatibility projection / dual-label later | Medium | `MEMBER_OF` can remain compatibility edge. |
| `DataQualityAlert` | vertex | DataOps-like context already in SOC graph | `DomainContext` | add domain partition before cross-copilot use | High | Must not imply DataOps migration is complete. Requires explicit `domain=dataops` or source metadata. |
| `PipelineSystem` | vertex | Pipeline/system context | `DomainContext` | add domain partition before cross-copilot use | High | Useful for shared graph proof but needs ownership/domain metadata. |
| `EvolutionEvent` | vertex | Existing evolution event nodes with `event_type`, `triggered_by`, etc. | `EvolutionEvent` | keep + repair/link edges | High | Nodes exist but live `TRIGGERED_EVOLUTION` edge count is 0. |
| `TRIGGERED_EVOLUTION` | edge | Catalog label exists, live count 0 | `Decision -[:TRIGGERED_EVOLUTION]-> EvolutionEvent` | investigate + repair write path | High | Blocks clean procedural-memory traversal if not repaired. |
| `ProfileSnapshot` | vertex | Snapshot of `mu`, `counts`, `decision_count`, timestamp | `CentroidCheckpoint` / partial `Fingerprint` | add compatibility projection / dual-label later | Medium | Likely canonical source for centroid checkpoints. |
| `DecisionDistanceLog` | vertex | Distance and pattern telemetry per decision | `Fingerprint` or judgment telemetry | investigate | Medium | It is not a full fingerprint; avoid over-mapping without factor semantics. |
| `ShadowDecision` | vertex | Shadow/evaluation decision records | `Observation` or evaluation event | investigate | High | Do not count as `Decision`. Must exclude from V/flywheel unless intentionally promoted. |
| Evidence ledger / audit properties | ledger + embedded fields | `EvidenceLedger` outside graph; optional Decision hash/index fields | `EvidenceReceipt` | add canonical node for forward writes; optional backfill | High | Must preserve hash chain and append semantics. |
| `DeploymentState` | vertex | Bootstrap mu and runtime state | Operational judgment state | keep + investigate canonical links | Low | Not a direct canonical replacement; useful for bootstrap provenance. |

## Canonical gaps

### Domain

- Introduction: add one `Domain` node per copilot/domain, starting with `soc`.
- Derivable from current data: partially. SOC records imply `soc`, but many nodes lack explicit `domain`.
- Requires new writes: yes. Forward writes should link `Decision`, `Observation`, `Fingerprint`, `ConservationStatus`, `Rule`, and `TransferPattern` to `Domain`.
- Backfill needed: yes, at least for current SOC `Decision` and context nodes.
- Blocks Protocol v2 conformance: yes for canonical AGE conformance; no for projection-only planning.

### Outcome

- Introduction: create `Outcome` nodes and `HAS_OUTCOME` edges.
- Derivable from current data: yes, from `Decision.outcome`, `Decision.correct`, and verification fields where present.
- Requires new writes: yes. Protocol v2 `write_outcome` must create `Outcome` and atomically transition `Decision.status`.
- Backfill needed: yes, if historical SOC decisions must participate in canonical V.
- Blocks Protocol v2 conformance: yes.

### FactorVector

- Introduction: create `FactorVector` nodes with vector values, names, shape, schema version, and hash.
- Derivable from current data: partially. `Decision.factor_vector` exists, but factor names/schema version may need domain config.
- Requires new writes: yes. Protocol v2 `write_governed_decision` should write `Decision`, `FactorVector`, and `HAS_FACTOR_VECTOR` atomically.
- Backfill needed: yes for canonical traversal over existing SOC decisions.
- Blocks Protocol v2 conformance: yes.

### Observation

- Introduction: create `Observation` for preview/read or simulation records that should not be `Decision`.
- Derivable from current data: maybe from `ShadowDecision`, but semantics differ and must be reviewed before mapping.
- Requires new writes: yes for preview/read persistence.
- Backfill needed: no for initial conformance; optional later for shadow/evaluation history.
- Blocks Protocol v2 conformance: yes.

### EvidenceReceipt

- Introduction: create graph-backed hash-chain receipt nodes via `append_evidence_receipt`.
- Derivable from current data: partially. Some Decision audit fields may exist, and the in-memory ledger has a model, but full graph hash chain is missing.
- Requires new writes: yes.
- Backfill needed: optional but recommended for audit completeness; forward writes are the minimum.
- Blocks Protocol v2 conformance: yes.

### CentroidCheckpoint

- Introduction: canonical `CentroidCheckpoint` nodes.
- Derivable from current data: yes, partly from `ProfileSnapshot`.
- Requires new writes: yes when centroid state changes or at configured checkpoints.
- Backfill needed: optional for SOC history; required if old snapshots must be canonical.
- Blocks Protocol v2 conformance: yes for checkpoint methods.

### Fingerprint

- Introduction: canonical `Fingerprint` nodes summarizing domain judgment/factor quality.
- Derivable from current data: partially from `DecisionDistanceLog`, `ProfileSnapshot`, and current analytics.
- Requires new writes: yes.
- Backfill needed: optional; forward snapshots are enough for initial conformance.
- Blocks Protocol v2 conformance: yes for `write_fingerprint`.

### ConservationStatus

- Introduction: canonical `ConservationStatus` nodes with V, q, alpha, theta_min, status, and timestamp.
- Derivable from current data: yes, if verified decisions are mapped correctly.
- Requires new writes: yes on status transition or configured snapshot cadence.
- Backfill needed: optional; current status can be computed and then persisted forward.
- Blocks Protocol v2 conformance: yes.

### TransferPattern

- Introduction: first-class transfer lineage node for cross-copilot pattern reuse.
- Derivable from current data: mostly no. Current SOC does not encode cross-copilot transfer as canonical graph nodes.
- Requires new writes: yes when patterns transfer across domains.
- Backfill needed: only for validated historical transfer stories.
- Blocks Protocol v2 conformance: not for store basics, but blocks cross-copilot proof.

### Rule

- Introduction: canonical procedural rule nodes.
- Derivable from current data: partially from `AttackPattern`, `Playbook`, and AgentEvolver state, but those are not equivalent by default.
- Requires new writes: yes for AgentEvolver promoted/shadow/retired rules.
- Backfill needed: optional after rule taxonomy is settled.
- Blocks Protocol v2 conformance: partly, for evolution/rule traversal tests.

## Compatibility strategy

Recommended staged approach: combine A, B, and D in phases.

1. **Compatibility projection only.**
   - Define read-only projections from current SOC labels to canonical concepts.
   - No SOC route rewrites.
   - No AGE schema mutation.
   - Used to finish Protocol v2 conformance design.

2. **Add canonical labels/edges alongside existing SOC labels.**
   - Add forward-write support for canonical nodes without deleting or renaming SOC labels.
   - Existing SOC routes continue using `Alert`, `Decision`, `ProfileSnapshot`, etc.
   - Canonical queries use `Domain`, `DomainContext`, `Outcome`, `FactorVector`, and receipt/status nodes.

3. **Dual-write new data to both old and canonical shape.**
   - Forward writes preserve SOC behavior while generating canonical graph shape.
   - Dual-write must be operation-class aware and idempotent per Protocol v2.

4. **Optional historical backfill.**
   - Backfill only after forward writes pass conformance.
   - Backfill should be replayable, idempotent, and scoped by domain.

Do not destructively migrate existing SOC labels in the first implementation phase. Compatibility projections and dual-labeling are safer because current SOC Playwright and API routes are green and should remain green.

## Decision / Outcome compatibility

Current SOC:

- `Decision` nodes contain `outcome` and `correct` properties.
- Verified decisions are counted with `d.outcome IS NOT NULL`.
- Correct decisions are counted with `d.correct = true`.

Canonical target:

- `(Decision)-[:HAS_OUTCOME]->(Outcome)`
- `Decision.status` transitions from `pending` to `confirmed` or `overridden`.
- V counts verified decisions only: statuses `confirmed` and `overridden`, or a compatibility projection from current `outcome IS NOT NULL`.

Transition plan:

1. Projection phase:
   - Treat `Decision.outcome IS NOT NULL` as verified.
   - Treat `Decision.correct = true` as confirmed/correct.
   - Derive canonical status:
     - `outcome IS NULL` -> `pending`
     - `correct = true` -> `confirmed`
     - `correct = false` -> `overridden`
2. Forward-write phase:
   - `write_outcome` creates an `Outcome` node and `HAS_OUTCOME` edge.
   - It atomically updates `Decision.status`.
   - Direct duplicate outcome writes raise.
   - Outbox replay identical payload skips; conflicting replay quarantines.
3. Backfill phase:
   - Create `Outcome` nodes for historical decisions with verified fields.
   - Mark backfilled receipts/outcomes with `source='soc_backfill'` or equivalent metadata.

During transition, conservation V must not count both embedded properties and backfilled `Outcome` nodes as separate verified events. The counting contract must choose one population per query path.

## FactorVector compatibility

Current SOC:

- `Decision.factor_vector` is embedded, usually serialized.

Canonical target:

- `(Decision)-[:HAS_FACTOR_VECTOR]->(FactorVector)`

Transition plan:

1. Projection phase:
   - Parse `Decision.factor_vector` into canonical vector values at query time.
   - Derive `shape` and factor names from SOC domain config.
2. Forward-write phase:
   - `write_governed_decision` creates `FactorVector` atomically with `Decision`.
   - Include `factor_names`, `factor_names_hash`, `shape`, and `schema_version`.
3. Backfill phase:
   - Create `FactorVector` nodes for historical decisions that have valid factor vectors.
   - Quarantine or mark incompatible legacy vectors rather than failing the whole backfill.

Existing SOC tests should remain green because old routes can continue reading embedded `Decision.factor_vector` while canonical queries use the projection or new node.

## EvidenceReceipt compatibility

Current SOC:

- `EvidenceLedger` exists as a hash-chain implementation outside AGE.
- Some audit-chain fields may be embedded on `Decision`, such as `entry_hash`, `decision_chain_index`, `outcome_chain_index`, and `outcome_entry_hash`.

Canonical target:

- `EvidenceReceipt` graph node appended via `append_evidence_receipt`.
- Store-managed `chain_index` and `previous_hash` under a per-domain lock/advisory lock.
- `Decision -[:EMITTED_RECEIPT]-> EvidenceReceipt`.

Minimum forward-write requirement:

- New decisions and outcomes should emit receipts into AGE through `append_evidence_receipt`.
- Receipt append must use `receipt_intent_id` for idempotent replay.
- Identical replay returns existing receipt; conflicting replay quarantines/errors.

Backfill:

- Optional for historical SOC decisions.
- If performed, it must preserve historical chain semantics and should not pretend old embedded audit fields were graph-native receipts.

## Evolution / TRIGGERED_EVOLUTION repair

Current SOC:

- `EvolutionEvent` nodes exist.
- `TRIGGERED_EVOLUTION` edge label exists but live count is 0.
- Code paths intend `(Decision)-[:TRIGGERED_EVOLUTION]->(EvolutionEvent)` for event-style evolution writes, and SOC design docs depend on that traversal.

Interpretation:

- This is at least a data gap.
- It may also be a write-path gap, depending on whether current runtime evolution writes still fail to create the edge or whether only historical data lacks edges.

Compatibility requirements:

1. Projection phase:
   - Use `EvolutionEvent.triggered_by` to associate events with `Decision` when possible.
2. Forward-write phase:
   - Protocol v2 `write_evolution_event` must create the canonical `EvolutionEvent` node and `TRIGGERED_EVOLUTION` edge.
3. Repair/backfill phase:
   - For existing `EvolutionEvent` rows with a valid `triggered_by` decision id, add or project the missing edge.
   - Events with no resolvable `Decision` should remain unlinked and be reported.

Blocker status:

- This should block cross-copilot procedural-memory proof.
- It should not block initial Protocol v2 method design, but it should be a required AGE conformance/integration gate before S2P migration claims transfer traversal.

## ProfileSnapshot / CentroidCheckpoint / Fingerprint compatibility

Current SOC:

- `ProfileSnapshot` stores centroid tensor state (`mu`), `counts`, `decision_count`, and timestamp.
- `DecisionDistanceLog` stores distance and judgment telemetry per decision.
- `DeploymentState` stores bootstrap mu and shape.

Canonical target:

- `CentroidCheckpoint`
- `Fingerprint`

Mapping:

- `ProfileSnapshot` is the strongest current equivalent for `CentroidCheckpoint`.
- `DecisionDistanceLog` is telemetry that can contribute to `Fingerprint`, but it is not a full `Fingerprint` by itself.
- `DeploymentState` is bootstrap/provenance state, not a replacement for either canonical node.

Transition plan:

1. Keep `ProfileSnapshot` for existing SOC routes.
2. Add canonical `CentroidCheckpoint` writes forward.
3. Either dual-label `ProfileSnapshot` as `CentroidCheckpoint` later or project it in canonical queries.
4. Define `Fingerprint` explicitly from factor quality, skipped/incompatible decisions, noise state, IKS, and summary metrics. Do not over-map `DecisionDistanceLog` as a complete fingerprint.

## Domain and DomainContext strategy

Current SOC:

- Domain context is represented through rich domain-specific labels: `Alert`, `User`, `Asset`, `AttackPattern`, `ThreatIndicator`, `ThreatIntel`, `Campaign`, `DataQualityAlert`, and `PipelineSystem`.

Canonical target:

- `DomainContext` with `entity_type`, `domain`, `natural_key`, and attributes.
- Domain-specific labels may remain for query ergonomics and route compatibility.

Strategy:

- Preserve SOC-specific labels.
- Add canonical `DomainContext` typing or compatibility projection.
- Add explicit `domain` metadata before cross-copilot use.
- For SOC context:
  - `Alert` -> `DomainContext {domain:'soc', entity_type:'alert'}`
  - `User` -> `DomainContext {domain:'soc', entity_type:'user'}`
  - `Asset` -> `DomainContext {domain:'soc', entity_type:'asset'}`
  - `AttackPattern` -> `DomainContext {domain:'soc', entity_type:'attack_pattern'}`
  - `ThreatIndicator` / `ThreatIntel` -> `DomainContext {domain:'soc', entity_type:'threat_indicator'/'threat_intel'}`
  - `Campaign` -> `DomainContext {domain:'soc', entity_type:'campaign'}`
- For embedded DataOps context already in `soc_graph`:
  - `DataQualityAlert` -> `DomainContext {domain:'dataops', entity_type:'data_quality_alert'}`
  - `PipelineSystem` -> `DomainContext {domain:'dataops', entity_type:'pipeline_system'}`

This preserves SOC richness while giving canonical cross-domain queries a stable layer.

## Observation strategy

Current SOC:

- `ShadowDecision` exists.
- Canonical preview/read `Observation` does not exist.

Decision:

- Do not automatically map every `ShadowDecision` to `Observation`.
- Treat `ShadowDecision` as an evaluation/shadow-test concept until its semantics are explicitly audited.
- New preview/read endpoints should write `Observation` only when product behavior calls for persisted preview analytics.
- Pure reads may remain write-free.

Rules:

- `Observation` is not `Decision`.
- `Observation` never counts toward V.
- `Observation` must not create AgentEvolver flywheel edges.
- Promotion from `Observation` to `Decision`, if ever implemented, must be explicit and audited.

## ConservationStatus strategy

Current SOC:

- Conservation status can be computed from decision/outcome fields and learning state, but no canonical `ConservationStatus` graph node exists.

Canonical target:

- Persist `ConservationStatus` snapshots with V, q, alpha, theta_min, status, timestamp, and metadata.

Strategy:

- Projection phase: compute from current SOC verified-decision semantics.
- Forward-write phase: write `ConservationStatus` on status transitions or configured snapshot cadence.
- Backfill: optional. Historical status snapshots can be reconstructed only if inputs are trustworthy; otherwise start forward.

Counting rule during transition:

- V is the count of verified decisions.
- In current SOC projection, verified means `Decision.outcome IS NOT NULL`.
- After canonical outcome migration, verified means `Decision.status IN ('confirmed', 'overridden')` and/or existence of exactly one canonical `Outcome` linked to the decision.
- Do not count `ShadowDecision` or `Observation`.

## TransferPattern / Rule strategy

Current SOC:

- `AttackPattern` represents MITRE/security context, not necessarily an operational `Rule`.
- `Playbook` label exists in catalog but has no live rows in the inventory.
- `EvolutionEvent` exists but lacks live `TRIGGERED_EVOLUTION` edges.
- No canonical `TransferPattern` exists.

Canonical target:

- `Rule` for procedural memory.
- `TransferPattern` for cross-domain pattern transfer.

Strategy:

- Do not relabel `AttackPattern` wholesale as `Rule`.
- Introduce `Rule` from AgentEvolver/promoted procedures and playbook/policy records after rule taxonomy is fixed.
- Introduce `TransferPattern` only when there is explicit source and target domain evidence.
- Use `EvolutionEvent` as lineage input, but repair/link `TRIGGERED_EVOLUTION` first.

## Risk assessment

- Breaking SOC routes: high risk if labels are renamed or fields are removed. Mitigation: preserve current labels and add canonical shape alongside them.
- Duplicate labels: medium risk with dual-labeling. Mitigation: explicit `domain`, `entity_type`, and idempotency keys.
- Ambiguous `DomainContext` mapping: high risk for `DataQualityAlert` and `PipelineSystem` already in `soc_graph`. Mitigation: require explicit domain partition before cross-copilot claims.
- Conservation count drift: high risk during `Outcome` backfill. Mitigation: one counting source per transition phase, verified-only invariant tests.
- Evolution edge ambiguity: high risk because `EvolutionEvent` nodes exist but edges do not. Mitigation: repair/projection plan before transfer claims.
- Audit chain mismatch: high risk if embedded audit fields are treated as canonical receipts. Mitigation: forward-write `EvidenceReceipt` first; backfill separately and explicitly.
- Shadow/evaluation contamination: high risk if `ShadowDecision` is counted as Decision/Observation without review. Mitigation: exclude from V/flywheel by default.

## Recommended staged implementation

This section follows Protocol v2 v1.8 phase gates. Full Protocol v2
conformance gates SOC forward-write changes, historical backfill, route
migration, and S2P AGE migration. Projection compatibility tests must exist
before any SOC route migration.

### Phase 1: repair this spec

- Align canonical vocabulary with `judgment_memory_v2_7.md` §4.2.
- Keep this document as planning only: no live AGE schema mutation, no route
  rewrites, no labels, no views, no migrations.

### Phase 2: create Protocol v2 conformance skeletons/stubs

- Create store-level conformance skeletons for Protocol v2 methods from
  `protocol_v2_design_v1_8.md`.
- Include canonical edge vocabulary checks so implementation cannot widen
  JM v2.7 edge targets.
- Keep tests as design/stub work until implementation is explicitly scoped.

### Phase 3: add SOC projection/compatibility tests

- Define canonical read projections for:
  - Decision projection
  - Outcome projection from embedded properties
  - FactorVector projection from embedded property
  - DomainContext projection from SOC labels
  - CentroidCheckpoint projection from `ProfileSnapshot`
- Prove projections return expected canonical data before any route
  migration.
- Preserve all SOC routes unchanged.

### Phase 4: implement Protocol v2 methods

- Add Protocol v2 methods to the GraphStore protocol and adapters under the
  method contracts in `protocol_v2_design_v1_8.md`.
- Do not migrate S2P or SDK copilots to AGE in this phase.

### Phase 5: harden AGE adapter until conformance passes

- Run Protocol v2 conformance on AGE and SQLite adapters.
- Fix adapter gaps until all required store-level and service-layer
  conformance tests pass.

### Phase 6: implement SOC canonical forward-write/projection paths

- Add canonical writes for new events:
  - `Decision` + `FactorVector` + `HAS_FACTOR_VECTOR`
  - `Outcome` + `HAS_OUTCOME`
  - `EvidenceReceipt`
  - `Observation`
  - `ConservationStatus`
  - `CentroidCheckpoint`
  - `Fingerprint`
  - `EvolutionEvent` + `TRIGGERED_EVOLUTION`
- Keep old SOC labels and embedded fields for current route compatibility
  until route migration is separately planned.

### Phase 7: optional historical backfill

- Backfill historical `Outcome`, `FactorVector`, `EvidenceReceipt`, and
  checkpoint nodes only after Protocol v2 conformance and SOC projection
  compatibility tests pass.
- Backfills must be idempotent and domain-scoped.
- Backfills must not alter SOC route behavior.

### Phase 8: route migration

- Update SOC routes to prefer canonical nodes where available.
- Keep compatibility fallback to old fields until migration is complete.
- Run SOC backend/API and full Playwright gates after each route migration
  slice.

### Phase 9: S2P AGE migration gate

- S2P AGE migration remains blocked until SOC compatibility projection
  contract is accepted and Protocol v2 conformance passes on AGE and SQLite.
- S2P migration scripts must be replay-safe and domain-scoped before use.

## Tests required

- Existing SOC full Playwright remains green.
- Existing SOC API contracts remain green.
- Canonical projection query returns `Decision` rows from current SOC graph.
- Embedded `Decision.outcome` / `Decision.correct` projects to canonical `Outcome` semantics.
- Embedded `Decision.factor_vector` projects to canonical `FactorVector` semantics.
- New `append_evidence_receipt` emits graph receipts with valid chain ordering.
- New `write_outcome` creates exactly one `Outcome` and transitions `Decision.status`.
- `TRIGGERED_EVOLUTION` edges are created for new evolution events.
- Existing unlinked `EvolutionEvent` records are reported by an inventory/repair diagnostic.
- `ConservationStatus` snapshots are written and queryable.
- `Observation` writes are excluded from V and AgentEvolver flywheel.
- `ShadowDecision` is excluded from V.
- `ProfileSnapshot` projection to `CentroidCheckpoint` is deterministic.
- `DecisionDistanceLog` is not incorrectly treated as a full `Fingerprint`.
- `test_soc_partial_outcome_backfill_does_not_double_count_V`: future mixed
  mode with embedded `Decision.outcome` / `Decision.correct` and canonical
  `Outcome` nodes counts each verified decision once.
- `test_soc_dataops_context_requires_explicit_domain_partition`:
  `DataQualityAlert` and `PipelineSystem` nodes inside `soc_graph` require
  explicit domain/source metadata before cross-domain traversal can treat
  them as DataOps-owned context.
- `test_soc_canonical_edge_vocabulary_matches_jm_v2_7`: compatibility
  projections and implementation use exactly the canonical edge targets from
  Judgment Memory v2.7 §4.2.
- `test_soc_projection_compatibility_before_route_migration`: SOC
  compatibility projections return expected canonical Decision, Outcome,
  FactorVector, and DomainContext data before any SOC route migration.
- Cross-domain query proof remains deferred until S2P migrates.

## Blockers before S2P AGE migration

- Protocol v2 conformance tests must pass for AGE and SQLite adapters.
- SOC compatibility projections must be reviewed and accepted.
- `Domain` and `DomainContext` strategy must be implemented or available as reliable projections.
- `Outcome` compatibility must be defined so V is verified-only and not double-counted.
- `FactorVector` compatibility must preserve SOC/S2P factor schema integrity.
- `EvidenceReceipt` forward-write semantics must be implemented for AGE.
- `Observation` implementation must exist and be excluded from V/flywheel.
- `TRIGGERED_EVOLUTION` write path must be fixed for new events and historical gap strategy documented.
- `ConservationStatus` write/query behavior must be implemented or explicitly deferred with no product claim depending on it.
- S2P migration scripts must be replay-safe and domain-scoped.

## Open questions

1. Should SOC use dual labels such as `(:Alert:DomainContext)` or compatibility query projections without dual labels?
2. Should historical `Outcome` backfill create receipt records, or should receipts start forward-only?
3. Should `ShadowDecision` become `Observation`, a separate `EvaluationEvent`, or remain SOC-specific?
4. What exact factor names/schema version should be assigned when backfilling SOC `FactorVector` nodes?
5. Should `ProfileSnapshot` be dual-labeled as `CentroidCheckpoint`, or should new checkpoints be written separately?
6. What is the authoritative repair policy for existing `EvolutionEvent` nodes with missing `TRIGGERED_EVOLUTION` edges?
7. Should `DataQualityAlert`/`PipelineSystem` remain in `soc_graph` as early shared graph evidence, or be re-partitioned under a formal `dataops` domain before claims use them?
