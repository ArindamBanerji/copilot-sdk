# SOC Projection Gate Report

Date: 2026-06-01

## Purpose

This report turns the SOC AGE compatibility plan into a concrete read-only
projection gate. The gate is intentionally non-mutating: it does not create,
delete, archive, reset, migrate, dual-label, or rewrite `soc_graph`.

AGE Protocol v2 adapter completion is accepted. The SOC projection gate is now
PASS_WITH_P3 after the read-only blocker tests passed live against `soc_graph`.
GraphStore factory design and S2P AGE shadow design are allowed; factory
implementation, S2P AGE shadow implementation, and S2P AGE migration remain
blocked pending their own reviewed plans and parity gates.

## Fixture

`tests/graph/test_soc_age_projection_contract.py` now uses a distinct SOC
projection fixture:

- `SOC_PROJECTION_INTEGRATION=1` is required.
- `SOC_AGE_DSN` is required.
- `SOC_AGE_GRAPH=soc_graph` is required.
- The fixture allows `soc_graph` only for read-only projection tests.
- A read-only wrapper rejects Cypher/SQL mutation verbs including `CREATE`,
  `SET`, `DELETE`, `DETACH`, `MERGE`, `REMOVE`, `DROP`, `ALTER`, `INSERT`,
  `UPDATE`, and `TRUNCATE`.
- The Protocol v2 AGE conformance fixture still rejects `soc_graph`.

## Activated Tests

Default/no-SOC-env:

- `test_soc_canonical_edge_vocabulary_matches_jm_v2_7`
- `test_soc_factor_schema_source_of_truth_is_stable`

SOC read-only integration, when explicit env is present:

- `test_soc_decision_projection_returns_canonical_decision`
- `test_soc_outcome_projection_from_embedded_fields`
- `test_soc_factor_vector_projection_from_embedded_decision_property`
- `test_soc_dataops_context_requires_explicit_domain_partition`
- `test_soc_projection_compatibility_before_route_migration`
- `test_soc_profile_snapshot_projection_to_centroid_checkpoint`
- `test_soc_shadow_decision_not_automatically_observation`

## Skipped / Deferred Tests

- `test_soc_partial_outcome_backfill_does_not_double_count_V`: requires mixed
  embedded Outcome plus canonical Outcome backfill data.
- `test_soc_triggered_evolution_forward_write_required`: read-only projection
  cannot prove forward writes; this requires a SOC write-path slice.
- SOC integration tests skip cleanly unless explicit read-only SOC env is set.

## Projection Mapping Status

Decision projection:

- Active read-only test finds a current SOC `Decision` and projects stable ID,
  domain=`soc`, category, recommended action, status basis, and timestamp.

Outcome projection:

- Active read-only test derives canonical Outcome semantics from embedded
  `Decision.outcome` / `Decision.correct` where present.
- No `Outcome` node is created.

FactorVector projection:

- Active read-only test parses embedded `Decision.factor_vector`.
- The projection now derives canonical schema metadata from the ordered
  `SOC_FACTORS` source in `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/config.py`.
- The projected metadata is:
  - `factor_schema_version = "soc_factor_schema_v1"`
  - `shape = [len(SOC_FACTORS)]`
  - `factor_names_hash = sha256(compact ordered SOC_FACTORS JSON)`
- The test fails on import/source drift, vector length mismatch, non-numeric
  vector values, or graph metadata that conflicts with the accepted ordered
  factor schema.
- No `FactorVector` nodes are created.

DomainContext projection:

- Decision/context route migration is still deferred.
- Current SOC labels remain the projection source; no dual labels are created.

DataQualityAlert / PipelineSystem partition:

- Active read-only test now uses a deny-by-default classifier.
- `DataQualityAlert` / `PipelineSystem` project as canonical non-SOC
  `DomainContext` only with explicit allowed non-SOC domain metadata, explicit
  type, stable key, and ownership/provenance metadata.
- Labels alone are denied.
- `source` alone is denied.
- `domain="soc"` is denied for DataOps projection.
- Missing or insufficient metadata classifies as
  `blocked_unpartitioned_context`. This is a safety pass, not a successful
  DataOps canonical projection.

Canonical edge vocabulary:

- Default test locks the compatibility spec to Judgment Memory v2.7 edge
  targets, including:
  - `Decision -> TRIGGERED_EVOLUTION -> EvolutionEvent`
  - `Rule -> APPLIES_TO -> DomainContext`
  - `TransferPattern -> DERIVED_FROM -> EvolutionEvent`
  - `Decision -> HAS_OUTCOME -> Outcome`
  - `Decision -> EMITTED_RECEIPT -> EvidenceReceipt`

ProfileSnapshot / CentroidCheckpoint:

- Active read-only diagnostic checks that `ProfileSnapshot` has centroid-like
  state usable as a future `CentroidCheckpoint` projection source.

ShadowDecision / Observation:

- Active read-only diagnostic confirms `ShadowDecision` is not automatically
  promoted to canonical `Observation`.

TRIGGERED_EVOLUTION:

- Forward-write proof remains deferred. Existing read-only projection can only
  inspect current shape; it cannot prove new writes create canonical edges.

## Gate Status

SOC projection gate: PASS_WITH_P3.

Default/no-SOC-env after blocker-test fixer:

```text
python -m pytest tests/graph/test_soc_age_projection_contract.py -q --timeout=120 -rs
2 passed, 9 skipped, 22 warnings
```

Live SOC read-only tests after the blocker-test fixer were run against
`soc_graph` with explicit projection env:

```text
python -m pytest tests/graph/test_soc_age_projection_contract.py -q --timeout=180 -rs
8 passed, 3 skipped, 0 xfailed, 0 failed, 22 warnings
```

The prior xfails drove the blocker-test fixer:

- SOC `Decision.factor_vector` values exist, but factor names/schema metadata
  were not previously available as canonical projection fields. The live test
  now passes by projecting names/schema from the ordered `SOC_FACTORS` source.
- `DataQualityAlert` / `PipelineSystem` rows exist, but explicit domain/source
  partition metadata was not present enough to treat them as canonical
  DataOps-owned context. The live test now passes by denying labels alone and
  safely classifying insufficiently partitioned rows as
  `blocked_unpartitioned_context`.

Remaining deferred items:

- Outcome double-count backfill.
- `TRIGGERED_EVOLUTION` forward writes.
- ShadowDecision mapping.
- SOC route migration.

Ready for GraphStore factory design: YES.

Ready for GraphStore factory implementation: NO, pending factory design/review
and explicit decision on how SOC projection compatibility is consumed.

Ready for S2P AGE shadow design: YES.

Ready for S2P AGE shadow implementation: NO.

Ready for S2P AGE migration: NO.

## Next Recommended Slice

Create and review the GraphStore factory design plan. The next slice must remain
design-only: no factory implementation, no app runtime switch, no SOC route
change, no S2P AGE shadow implementation, and no S2P AGE migration.
