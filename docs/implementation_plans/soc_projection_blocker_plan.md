# SOC Projection Blocker Plan

Date: 2026-06-01

## Purpose

The AGE Protocol v2 adapter completion gate is closed, but the SOC projection gate remains partial. This plan resolves the two live SOC projection blockers without mutating `soc_graph`:

- SOC `Decision.factor_vector` has vector values but not canonical factor schema metadata on graph rows.
- `DataQualityAlert` and `PipelineSystem` exist in `soc_graph` without explicit enough domain/source partition metadata for safe cross-copilot projection.

The plan is design-only. It does not change production routes, SOC graph schema, GraphStore factory wiring, S2P migration, reset/delete/archive behavior, frontend code, or Playwright tests.

## Current SOC projection gate status

The guarded read-only SOC projection contract is active in `tests/graph/test_soc_age_projection_contract.py`.

Default run:

- `1 passed, 9 skipped`

Live SOC projection run with `SOC_PROJECTION_INTEGRATION=1`, `SOC_AGE_GRAPH=soc_graph`, and explicit `SOC_AGE_DSN`:

- `5 passed`
- `3 skipped`
- `2 xfailed`

The two xfails are valid blockers:

- FactorVector projection cannot prove canonical `factor_names`, `factor_schema_version`, `shape`, and `factor_names_hash` from the graph row alone.
- DataOps-like context cannot be treated as safe `DomainContext` because explicit partition metadata is absent or insufficient.

## Blocker 1: FactorVector schema projection

### Current evidence

SOC `Decision` rows contain embedded `factor_vector` values. The live projection test can parse and validate numeric vector values, but xfails because the rows do not carry `factor_names` or `factor_schema_version`.

The SOC source tree does contain a stable factor source of truth:

- `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/config.py`
- import target: `backend.app.domains.soc.config.SOC_FACTORS` when `gen-ai-roi-demo-v4-v50/backend` is on `sys.path`
- `N_FACTORS = len(SOC_FACTORS)`
- `SOC_PROFILE_CENTROIDS` shaped by `N_FACTORS`
- `SOCDomainConfig.factors`
- `SOCDomainConfig.get_factor_computers`

The ordered canonical SOC factor names are:

```text
privileged_identity_context
asset_criticality
threat_intel_enrichment
pattern_history
time_anomaly
device_trust
```

`gen-ai-roi-demo-v4-v50/backend/app/domains/soc/orchestrator.py` computes factor values by iterating ordered factor computers and then delegates vector assembly to `gae.factors.assemble_factor_vector`. That gives the projection a defensible read-time source for factor order without mutating SOC graph rows.

### Source of truth

For current projection, the authoritative source is `SOC_FACTORS` from SOC config, not the graph row. The next test fixer may use a checked-in compatibility constant derived from `SOC_FACTORS` if importing SOC config from the `copilot-sdk` test process is brittle, but that constant must be validated against the source file or documented as a pinned compatibility copy.

The projection should treat graph row metadata as optional override only if it is present and matches the source-of-truth order. The graph row must not be allowed to silently define a divergent order.

Initial schema version:

```text
soc_factor_schema_v1
```

This is a projection compatibility schema version for the current six-factor SOC vector. It should be introduced in the projection/test helper first. Forward writers can later persist the same value.

Factor names hash:

```python
payload = json.dumps(list(factor_names), separators=(",", ":"), ensure_ascii=True)
factor_names_hash = sha256(payload.encode("utf-8")).hexdigest()
```

The exact hash input for the current schema is:

```json
["privileged_identity_context","asset_criticality","threat_intel_enrichment","pattern_history","time_anomaly","device_trust"]
```

The list order must be preserved. Do not sort the factor name list. Do not hash labels, descriptions, or graph row values. The hash identifies the ordered schema, not the unordered set of names.

### Canonical projection rule

Input:

- SOC `Decision.factor_vector`
- ordered `SOC_FACTORS` loaded from SOC config or a checked-in compatibility constant derived from it

Output canonical projection:

- `factor_names`: ordered `SOC_FACTORS`
- `factor_schema_version`: `soc_factor_schema_v1`
- `shape`: `[len(SOC_FACTORS)]`
- `factor_names_hash`: SHA-256 hash of the ordered `factor_names` JSON list
- `values`: parsed numeric vector values from `Decision.factor_vector`

Validation:

- `factor_vector` must parse as a list.
- Every vector element must be numeric.
- `len(factor_vector) == len(SOC_FACTORS)`.
- If the row has `factor_names`, it must equal ordered `SOC_FACTORS`.
- If the row has `factor_schema_version`, it must equal the selected projection schema version or be explicitly mapped by a compatibility table.
- If SOC config import fails and no pinned compatibility constant exists, the projection must skip or xfail with a precise source-of-truth error. It must not invent factor names.
- If the pinned compatibility constant diverges from `SOC_FACTORS`, the projection must fail. That is schema drift.
- If lengths or names differ, the projection must block or xfail with a precise mismatch reason. It must not guess a partial mapping.

The projection must not create `FactorVector` nodes in `soc_graph` in this gate. It is read-only compatibility projection.

### Recommended remediation

Use projection-only metadata from source config as the first remediation.

Before GraphStore factory design:

- Add a small projection helper in the SOC projection contract that loads or defines the ordered six-factor `SOC_FACTORS`.
- Compute `factor_schema_version`, `shape`, and `factor_names_hash` at read time.
- Turn the FactorVector xfail into an active read-only test if vector length matches the source-of-truth factor list.

Before GraphStore factory implementation:

- Decide whether the factory uses this projection helper only for SOC compatibility reads or whether it requires a shared SOC projection adapter module.
- The FactorVector blocker test must pass live in read-only mode. Factory implementation should not depend on an xfailed FactorVector projection.
- Keep canonical Protocol v2 AGE writes unchanged.

Before S2P AGE shadow implementation:

- Forward writes should persist canonical factor metadata directly (`factor_names`, `factor_schema_version`, `shape`, and `factor_names_hash`) for any newly written canonical decisions or snapshots.
- Source-config projection alone is enough for read-only compatibility, but not enough for new canonical AGE writes. Forward writes must store the canonical metadata.

Historical metadata backfill:

- Optional and later. It is not required to close the read-only projection gate if the source-config projection passes.
- If backfill is later chosen, it must be a separate reviewed migration/backfill plan and must not run as part of projection tests.

### Tests to activate

Update `test_soc_factor_vector_projection_from_embedded_decision_property` so it:

- reads one SOC `Decision.factor_vector` row;
- loads ordered `SOC_FACTORS` from source config or a checked compatibility constant;
- asserts all vector values are numeric;
- asserts vector length equals factor count;
- computes `factor_schema_version = "soc_factor_schema_v1"`;
- computes ordered `factor_names_hash`;
- asserts `shape == [6]`;
- asserts no short alias such as `threat_intel` replaces `threat_intel_enrichment`.

Add or include helper-level assertions:

- source-of-truth factor names are exactly the six names above;
- hash is deterministic across repeated computation;
- graph row metadata, if present, cannot conflict with the source-of-truth order.

### Gate impact

If the active read-only FactorVector projection test passes with source-config metadata, the FactorVector blocker becomes resolved for projection compatibility.

This does not imply SOC graph canonicalization is complete. It means current SOC factor vectors can be interpreted safely for read-only canonical projection.

## Blocker 2: DataOps partition metadata

### Current evidence

The compatibility spec identifies `DataQualityAlert` and `PipelineSystem` as useful DataOps-like context already present in `soc_graph`.

The live SOC projection test found rows for these labels but xfailed because nodes lacked explicit domain/source partition metadata such as:

- `domain`
- `source_domain`
- `owner_domain`
- `source`

Searches of the local SOC setup/rebuild path did not find local forward-write creation for `DataQualityAlert` or `PipelineSystem`. That suggests the current rows are imported or pre-existing SOC graph inventory rather than graph state created by the current rebuild script with explicit partition fields.

### Source of truth

Until a DataOps metadata source is explicitly added, labels alone are not a sufficient source of truth for SOC projection.

`DataQualityAlert` and `PipelineSystem` should be treated as DataOps-like context only when explicit partition metadata exists. Without that metadata, they remain unpartitioned graph context and must not be traversed as SOC alert context.

Required metadata for canonical `DomainContext` projection:

- `domain` or `source_domain`: must be `dataops` for DataOps projection, or another explicitly documented non-SOC domain.
- `entity_type`: `data_quality_alert` for `DataQualityAlert`, `pipeline_system` for `PipelineSystem`.
- stable natural key: label-specific ID such as alert/system identifier.
- `source` or `owner_copilot`: provenance only unless it is part of an explicit allow-list that maps to a non-SOC domain. A generic `source` property by itself is not enough to establish domain ownership.

### Canonical projection rule

Use an explicit-domain-only rule.

Allowed projection:

- `DataQualityAlert` may project to `DomainContext` only if explicit metadata identifies it as DataOps context.
- `PipelineSystem` may project to `DomainContext` only if explicit metadata identifies it as DataOps context.
- Accepted explicit domain values for this gate are `dataops` or a future non-SOC domain listed in the compatibility spec. `soc`, blank, null, and missing values are not accepted for DataOps projection.
- A stable natural key must be present. Acceptable key candidates should be label-specific, for example `alert_id`, `data_quality_alert_id`, `pipeline_id`, `system_id`, `name`, `id`, or another documented key.
- Projected `DomainContext.domain` must not be inferred as `soc` from graph location.

Blocked projection:

- If explicit domain/source metadata is missing, classify the node as `blocked_unpartitioned_context`.
- If `source` exists but no explicit domain/source-domain/owner-domain allow-list maps it to `dataops`, classify the node as `blocked_unpartitioned_context`.
- If metadata says `domain=soc`, classify it as not eligible for DataOps `DomainContext` projection in this test. The node may still exist in `soc_graph`, but it must not become DataOps context.
- If no stable natural key exists, classify it as blocked even when domain metadata exists.
- Do not include it in SOC alert context.
- Do not use it to enrich SOC `Decision`, `Alert`, or `Outcome` semantics.
- Do not claim cross-copilot traversal through it.

This rule prevents DataOps nodes inside `soc_graph` from contaminating SOC alert semantics while preserving them as future shared graph opportunities.

`blocked_unpartitioned_context` is a safe-pass classification for the active safety test, not a successful canonical projection. It proves the projection layer refuses unsafe nodes; it does not prove DataOps DomainContext projection is complete.

### Recommended remediation

Use a deny-by-default projection rule now, plus forward-write metadata later.

Immediate read-only remediation:

- Replace the current DataOps xfail with a projection helper that classifies existing unpartitioned `DataQualityAlert` and `PipelineSystem` rows as blocked.
- Make the active test assert the safety invariant: unpartitioned nodes are not projected as SOC alert context or canonical `DomainContext`.
- Keep the helper pure/read-only. It should inspect node properties already returned by the query and return a classification object; it must not write metadata back to `soc_graph`.

Forward-write remediation:

- Any future DataOps-producing path must write explicit metadata:
  - `domain = "dataops"`
  - `source_domain = "dataops"` or equivalent
  - `entity_type`
  - stable natural key
  - optional `owner_copilot` / `created_by`

Backfill remediation:

- Optional separate plan. If historical `DataQualityAlert` / `PipelineSystem` rows must become traversable, add an explicit metadata backfill design with read-before-write inventory, rollback plan, and no SOC route changes.

Avoid:

- Do not infer `domain=dataops` from label alone for production projection claims.
- Do not hard-code existing rows as SOC-safe context.
- Do not mutate `soc_graph` in projection tests.

### Tests to activate

Update `test_soc_dataops_context_requires_explicit_domain_partition` so it can pass in either of two safe states:

- If explicit metadata exists, assert the node projects to `DomainContext` with non-SOC explicit domain, expected entity type, and stable natural key.
- If metadata is absent or insufficient, assert projection status is `blocked_unpartitioned_context` and assert it is not treated as SOC alert context. This is a pass for the safety invariant, but the test should report/record that DataOps canonical projection remains incomplete.

Additional assertions:

- `DataQualityAlert` without explicit metadata does not project as `domain="soc"`.
- `PipelineSystem` without explicit metadata does not project as `domain="soc"`.
- `source` alone does not satisfy the partition requirement unless explicitly allow-listed to a non-SOC domain.
- metadata with `domain="soc"` does not satisfy DataOps projection.
- missing stable key blocks DomainContext projection.
- The test remains read-only and does not create or backfill metadata.

Future tests after forward-write/backfill design:

- `DataQualityAlert` with `domain=dataops` projects to `DomainContext`.
- `PipelineSystem` with `domain=dataops` projects to `DomainContext`.
- Mixed SOC and DataOps traversals require explicit allowed edge vocabulary.

### Gate impact

If the active read-only test proves unpartitioned DataOps nodes are denied by projection, the contamination risk becomes controlled for projection compatibility.

This does not make DataOps canonicalization complete. It means the SOC projection layer will not accidentally absorb unpartitioned DataOps graph state into SOC alert memory.

## Test plan

Keep active:

- `test_soc_decision_projection_returns_canonical_decision`
- `test_soc_outcome_projection_from_embedded_fields`
- `test_soc_factor_vector_projection_from_embedded_decision_property`, after source-config projection helper is added
- `test_soc_dataops_context_requires_explicit_domain_partition`, after blocked/unpartitioned classification is added
- `test_soc_canonical_edge_vocabulary_matches_jm_v2_7`
- `test_soc_projection_compatibility_before_route_migration`
- `test_soc_profile_snapshot_projection_to_centroid_checkpoint`
- `test_soc_shadow_decision_not_automatically_observation`

Keep skipped until later gates:

- `test_soc_partial_outcome_backfill_does_not_double_count_V`: requires canonical SOC Outcome backfill design.
- `test_soc_triggered_evolution_forward_write_required`: read-only projection cannot prove forward writes.
- ShadowDecision-to-Observation promotion: must remain deferred until an explicit mapping exists.

The next test slice should be read-only and limited to `copilot-sdk/tests/graph/test_soc_age_projection_contract.py`. It should not touch SOC production code or `soc_graph`.

Additional helper-level tests/assertions for the next slice:

- SOC factor names hash is stable for repeated computation.
- Factor vector length equals `len(SOC_FACTORS)`.
- SOC factor source import failure is explicit and does not silently pass.
- DataOps metadata absent means blocked, not failed.
- DataOps metadata present with `domain=dataops` means non-SOC `DomainContext` projection.
- DataOps `source` without explicit domain mapping remains blocked.

## Implementation prompt outline

Next safe Codex task:

```text
TASK: SOC projection blocker test fixer - read-only FactorVector schema projection and DataOps partition denial.
TYPE: Test/projection-helper only. NO production code changes. NO soc_graph mutation.

Implement only:
- source-of-truth SOC factor metadata helper for projection tests;
- deterministic factor_names_hash helper;
- active FactorVector projection assertions;
- DataOps projection classifier with explicit-domain-only and blocked_unpartitioned_context behavior;
- active DataOps partition safety assertions;
- update soc_projection_gate_report.md with new live/default results.

Do not implement:
- GraphStore factory;
- S2P AGE shadow or migration;
- SOC route changes;
- schema writes/backfills;
- reset/delete/archive;
- frontend/Playwright;
- production DataOps writes.

Validation:
- default test_soc_age_projection_contract.py;
- full graph/scoring tests;
- live SOC projection run only when SOC_PROJECTION_INTEGRATION, SOC_AGE_DSN, and SOC_AGE_GRAPH are explicitly configured.
```

## Gate decision after remediation

If both blocker tests pass live in read-only mode:

- SOC projection gate: `PASS_WITH_P3`
- GraphStore factory design: `YES`
- GraphStore factory implementation: `PARTIAL`, only after factory design keeps SOC projection compatibility explicit and does not route production SOC writes through canonical adapters prematurely
- S2P AGE shadow design: `YES`
- S2P AGE shadow implementation: `NO`, until factory planning and service/outbox gates are explicitly reviewed
- S2P AGE migration: `NO`

Deferred gates remain deferred after this remediation:

- Outcome double-count prevention still waits for canonical SOC Outcome backfill design.
- `TRIGGERED_EVOLUTION` still waits for SOC write-path proof.
- ShadowDecision-to-Observation mapping remains intentionally deferred until explicit semantics are accepted.

If only the plan is accepted but tests are not yet updated/run:

- SOC projection gate remains `PARTIAL`
- GraphStore factory design is allowed as design-only, but implementation remains blocked
- S2P shadow design is allowed as design-only, but implementation remains blocked
- S2P migration remains blocked

## Open questions

- Should `soc_factor_schema_v1` be added as a production constant in SOC config later, or remain a projection compatibility constant until forward writes are redesigned?
- Should historical `Decision` rows ever be backfilled with factor metadata, or is source-config projection sufficient for all legacy reads?
- Which code path, if any, currently creates `DataQualityAlert` and `PipelineSystem` rows in live `soc_graph`?
- Should future DataOps metadata use `domain`, `source_domain`, both, or a richer `owner_copilot` convention?
- Should DataOps nodes become canonical `DomainContext` only after metadata backfill, or only for forward-written rows?
- What canonical edge vocabulary should connect explicit DataOps `DomainContext` to SOC `Decision` or `Alert` after cross-copilot traversal is allowed?
