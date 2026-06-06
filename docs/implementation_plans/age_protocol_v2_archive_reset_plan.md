# AGE Protocol v2 Archive/Reset Plan

## Purpose

This plan defines safe AGE Protocol v2 semantics for `archive_decisions(...)` and `domain_scoped_reset(...)` before implementation.

Archive/reset is high-risk because it can remove or hide graph state, alter active conservation counts, and damage shared canonical graph data if scoped incorrectly. The first AGE implementation must preserve the product architecture:

- AGE/PostgreSQL+AGE is the canonical product graph.
- SQLite remains local/test adapter only.
- Archive is lifecycle/retention management, not a reset shortcut.
- Domain-scoped reset is test/dev/admin isolation, not product data-loss behavior.
- No AGE archive/reset test may target `soc_graph`.
- No S2P AGE migration, GraphStore factory, outbox, service-layer sync, frontend, or production route work is implied by this plan.

## Current AGE archive/reset state

The current AGE adapter has only legacy placeholder archive behavior:

- `AGEGraphStore.archive_old_decisions(domain, keep_recent=800)` is a no-op and returns `0`.
- `AGEGraphStore.count_archived(domain)` is a no-op and returns `0`.
- There is no Protocol v2 `archive_decisions(...)` implementation in AGE.
- There is no Protocol v2 `domain_scoped_reset(...)` implementation in AGE.
- Current AGE `count_decisions(domain)` counts all `Decision` nodes in the domain and does not filter archived data.
- Current AGE `count_verified_decisions(domain)` counts `Decision.status IN ['confirmed', 'overridden']` and does not filter archived data.
- Existing AGE Protocol v2 slices do not set `archived`, `archived_at`, `archive_reason`, or related archive properties.
- Existing guarded AGE tests rely on unique `pytest_protocol_v2_*` domains and avoid destructive cleanup.

No current AGE behavior should be treated as production-ready archive/reset semantics.

## Canonical archive semantics

Protocol v2 archive shape:

```python
def archive_decisions(
    domain: str,
    before: float,
    status_filter: str = "pending",
    confirm_verified: bool = False,
) -> int:
    ...
```

Required semantics:

- `before` is Unix epoch seconds.
- Only active, non-archived `Decision` nodes with numeric `created_at < before` are eligible.
- Rows at or after `before` remain active.
- `created_at` is the archive cutoff field for Protocol v2 AGE decisions. Do not fall back to legacy `timestamp` in the first implementation.
- Decisions with missing or non-numeric `created_at` are non-archivable in the first implementation and should be left active; legacy timestamp normalization is a separate migration concern.
- Pending archive is allowed without `confirm_verified`.
- Archiving `confirmed` or `overridden` decisions requires `confirm_verified=True`; otherwise raise `ValueError`.
- Archived decisions remain in AGE for audit/replay.
- Archive must not physically delete `Decision` nodes in the first AGE implementation.
- Archive must preserve existing relationships such as `HAS_OUTCOME`, `EMITTED_RECEIPT`, and `ABOUT`.
- Archive must not mutate `Outcome`, `EvidenceReceipt`, `DomainContext`, or snapshot nodes.

Recommended archived properties on `Decision`:

- `archived = true`
- `archived_at = <float epoch seconds>`
- `archive_reason = "protocol_v2_archive:<status_filter>"`
- `archive_status = "archived"`
- `archived_from_status = <previous Decision.status>`

The first implementation should support explicit status filters `pending`, `confirmed`, and `overridden`. Broader filters such as `all` should remain out of scope unless separately reviewed.

## Active V after archive

Active Protocol v2 counts must exclude archived decisions:

- `count_decisions(domain)` counts active non-archived `Decision` nodes only.
- `count_verified_decisions(domain)` counts active non-archived `Decision` nodes whose status is `confirmed` or `overridden`.
- Archived verified decisions do not count in active V.
- Archived pending decisions never count in active V.
- Outcome counts must not define Protocol v2 V.
- The legacy `count_verified(domain)` method may remain outcome-edge based for compatibility, but Protocol v2 V must use `count_verified_decisions(domain)`.

The AGE implementation must update the count queries to add:

```cypher
AND (d.archived IS NULL OR d.archived = false)
```

Historical/replay queries may later include archived decisions explicitly. That is not part of the first implementation.

## Canonical domain reset semantics

Protocol v2 domain reset shape:

```python
def domain_scoped_reset(domain: str) -> None:
    ...
```

AGE domain reset is destructive and must be treated as test/dev/admin-only behavior.

Required semantics:

- Reset must affect only the requested domain.
- Reset must preserve all other domains.
- Reset must be idempotent.
- Reset must be hard-guarded against `soc_graph`.
- Reset must reject blank/default graph names.
- Reset must reject non-test graph names in the first implementation.
- Reset must reject domains that do not start with `pytest_protocol_v2_` in the first implementation.
- Reset must avoid deleting global/shared semantic nodes unless they are domain-scoped Protocol v2 test nodes.
- Reset must delete relationships before nodes when AGE does not reliably support `DETACH DELETE`.
- Reset must not delete `DomainContext` nodes that are shared across domains or lack the target test domain.

Target Protocol v2 data for a guarded test-domain reset:

- `Decision` nodes in the domain.
- Connected `Outcome` nodes and `HAS_OUTCOME` edges for target-domain decisions.
- `Observation` nodes in the domain.
- `EvidenceReceipt` nodes in the domain and `EMITTED_RECEIPT` edges.
- `ConservationStatus` nodes in the domain.
- `Fingerprint` nodes in the domain.
- Protocol v2 `CentroidCheckpoint` nodes in the domain.
- `EvolutionEvent` nodes in the domain.
- `DomainContext` nodes in the domain that were created for Protocol v2 test entity links, plus `ABOUT` edges. A `DomainContext` is eligible for deletion only when `ctx.domain = domain` and either its `entity_id` is linked only from target-domain decisions or it has explicit Protocol v2/test metadata such as `schema_version`/domain properties from the AGE entity-link slice.

The reset implementation must not attempt production/demo cleanup and must not be exposed as a product reset route in this slice.

## Archive implementation options

### Option A: Soft archive on Decision

Set archive properties directly on eligible `Decision` nodes and update active count queries to filter archived decisions.

Pros:

- Preserves audit/replay traversability.
- Avoids physical deletion.
- Can be implemented as one Cypher mutation for a single status filter.
- Aligns with Protocol v2 design guidance for AGE.

Cons:

- Requires all active-count/read paths to respect the archived filter.
- Historical query semantics must be explicit later.

### Option B: ArchiveEvent node

Create an `ArchiveEvent` node connected to archived decisions.

Pros:

- Adds richer audit metadata.
- Can represent operator/admin intent later.

Cons:

- More schema surface.
- Not needed for first conformance.
- Still requires archived filtering on active counts.

### Option C: Physical move/delete

Delete or move AGE decision nodes into archive labels/tables.

Pros:

- Active graph becomes smaller.

Cons:

- High risk to audit/replay.
- Can break relationships and canonical graph traversability.
- Too destructive for first AGE implementation.

### Option D: Hybrid

Soft archive plus an `ArchiveEvent`.

Pros:

- Strong future audit model.

Cons:

- Wider than needed for first AGE conformance.

## Recommended archive strategy

Use Option A: soft archive on `Decision`.

The first AGE implementation should:

1. Validate `status_filter`.
2. Raise `ValueError` if `status_filter in {'confirmed', 'overridden'}` and `confirm_verified is False`.
3. Run a single Cypher mutation for the requested status:

```cypher
MATCH (d:Decision)
WHERE d.domain = $domain
  AND d.status = $status_filter
  AND (d.archived IS NULL OR d.archived = false)
  AND d.created_at IS NOT NULL
  AND d.created_at < $before
SET d.archived = true,
    d.archived_at = $archived_at,
    d.archive_reason = $archive_reason,
    d.archive_status = 'archived',
    d.archived_from_status = d.status
RETURN count(d) AS archived_count
```

4. Return the archived count.
5. Test that archived pending decisions are excluded from `count_decisions`.
6. Test that archived verified decisions are excluded from `count_verified_decisions`.
7. Update `count_decisions` and `count_verified_decisions` to exclude archived decisions.
8. Keep legacy `archive_old_decisions(...)` unchanged unless a separate compatibility review decides otherwise.

Decisions missing numeric `created_at` should not be silently archived in the first implementation. Legacy AGE migration for missing timestamps is a separate migration-planning concern.

## Domain reset implementation options

### Option A: Single broad Cypher delete

Delete all domain-scoped labels and relationships in one large query.

Pros:

- Fewer round trips.

Cons:

- Harder to review.
- Higher risk of accidentally deleting shared/global nodes.
- AGE dialect limitations around complex deletes must be verified.

### Option B: Label-specific deletes inside one transaction

Run explicit label/type-scoped delete statements in a transaction after passing strict guards.

Pros:

- Reviewable and auditable.
- Lets each label use the safest domain predicate.
- Rollback can cover the whole reset.
- Avoids broad graph wipes.

Cons:

- Requires transaction helper use.
- Requires AGE delete syntax verification.

### Option C: Guarded test-graph-only reset

Permit reset only in explicit AGE integration test graph contexts and for `pytest_protocol_v2_*` domains.

Pros:

- Prevents production/demo graph damage.
- Matches current no-cleanup AGE test strategy.

Cons:

- Does not solve product/admin reset needs yet.

### Option D: Defer reset implementation

Keep reset skipped until a broader AGE admin safety model exists.

Pros:

- Lowest immediate destructive risk.

Cons:

- Leaves Protocol v2 AGE local/test conformance incomplete.

## Recommended reset strategy

Use Options B and C together: label-specific deletes inside one transaction, allowed only for guarded test graph/domain contexts.

Required method-level guards:

- Reject graph name if blank.
- Reject graph name `soc_graph`.
- Reject graph names that do not start with `protocol_v2_test`.
- Reject domains that do not start with `pytest_protocol_v2_`.

The implementation should use the existing transaction-capable AGE helper from EvidenceReceipt work or a narrow equivalent. All reset delete statements must execute on the same psycopg connection with `autocommit=False` and rollback on any exception.

Recommended reset order:

1. Select target-domain `Decision` ids inside the transaction when needed for edge-specific deletes.
2. Delete `EMITTED_RECEIPT` relationships from target-domain decisions to target-domain `EvidenceReceipt` nodes.
3. Delete target-domain `EvidenceReceipt` nodes after their incoming receipt edges are removed.
4. Delete `HAS_OUTCOME` relationships from target-domain decisions to target-domain or decision-linked `Outcome` nodes.
5. Delete `Outcome` nodes connected to target-domain decisions or with `o.domain = domain`.
6. Delete `ABOUT` relationships from target-domain decisions to target-domain `DomainContext` nodes.
7. Delete eligible `DomainContext` nodes only when `ctx.domain = domain` and no remaining non-target-domain relationships point at them.
8. Delete target-domain `Decision` nodes.
9. Delete target-domain `Observation` nodes.
10. Delete target-domain `ConservationStatus` nodes.
11. Delete target-domain `Fingerprint` nodes.
12. Delete target-domain Protocol v2 `CentroidCheckpoint` nodes.
13. Delete target-domain `EvolutionEvent` nodes.

The implementation must verify AGE delete syntax before enabling tests. Prefer explicit relationship deletes before node deletes. Use `DETACH DELETE` only if PostgreSQL+AGE behavior is verified in the guarded test graph and the query remains domain-scoped.

## Transaction/rollback strategy

Archive:

- A single-status archive can be one Cypher mutation and is atomically applied by the database for that statement.
- Archive does not need the transaction helper in the first implementation if it remains a single soft-property update statement.
- If future archive modes touch multiple statuses or create `ArchiveEvent` nodes, use the transaction helper.

Reset:

- Reset must use a transaction because it requires multiple label/edge-specific deletes.
- Reset must not be implemented until the transaction-capable AGE helper is available in the target branch.
- All Cypher SQL calls must execute on one psycopg connection with `autocommit=False`.
- Roll back on any exception.
- Do not use the AGEClient per-query autocommit path for reset.
- Do not run reset without passing graph-name and domain-prefix guards.

Rollback tests should be planned after the first reset implementation lands. The first reset test must at least prove idempotency and other-domain preservation.

## Safety guards

Existing AGE fixture guards remain mandatory:

- `AGE_INTEGRATION=1`
- explicit `AGE_TEST_DSN`
- explicit `AGE_TEST_GRAPH`
- reject blank/default graph names
- reject `soc_graph`
- use unique `pytest_protocol_v2_*` domains
- avoid destructive cleanup by default

Additional reset guards:

- `domain_scoped_reset` must itself reject unsafe graph names.
- `domain_scoped_reset` must itself reject non-`pytest_protocol_v2_*` domains.
- `domain_scoped_reset` must itself reject `soc_graph` even if fixture guards fail.
- `domain_scoped_reset` must itself reject graph names that do not start with `protocol_v2_test`.
- Tests must never simulate reset by pointing at `soc_graph`.
- No production/demo reset route is in scope.

Archive is a product lifecycle operation and should not have the same test-domain-only method guard, but all AGE archive tests must still run only through the guarded AGE test fixture.

## Test activation plan

### Archive tests

Activate guarded AGE tests:

- `test_age_archive_pending`
  - Create old pending and old confirmed decisions.
  - Archive pending before cutoff.
  - Assert pending decision is archived.
  - Assert confirmed decision remains active.
  - Assert active V is unchanged.
  - Assert `count_decisions` excludes archived pending decisions.
  - Assert other-domain pending decisions remain active.

- `test_age_archive_verified_requires_confirmation`
  - Create confirmed decision.
  - Archive `confirmed` without `confirm_verified=True`.
  - Assert `ValueError`.
  - Assert active V unchanged.

- `test_age_archive_verified_decreases_active_V`
  - Create confirmed decision.
  - Archive `confirmed` with `confirm_verified=True`.
  - Assert active verified count decreases.
  - Assert archived decision remains in graph with archive properties.
  - Assert existing `HAS_OUTCOME` and `EMITTED_RECEIPT` relationships remain for audit/replay if present.

- `test_age_archive_cutoff_respected`
  - Create decisions before and at/after cutoff.
  - Archive before cutoff.
  - Assert only older decisions are archived.
  - Assert a decision exactly at the cutoff remains active.

- `test_age_archive_missing_created_at_not_archived`
  - Create or inject a guarded test Decision without numeric `created_at` if feasible.
  - Archive before a future cutoff.
  - Assert the method does not silently archive that Decision.
  - If direct setup is too broad, keep this as a skipped integrity test with a precise reason.

### Reset tests

Activate guarded AGE tests:

- `test_age_domain_scoped_reset`
  - Create Protocol v2 data in one target `pytest_protocol_v2_*` domain.
  - Create comparable data in another unique domain.
  - Reset target domain.
  - Assert target-domain Protocol v2 nodes/edges are removed.
  - Assert other-domain data remains.
  - Call reset again and assert idempotency.
  - Assert target-domain `DomainContext` nodes are removed only when no non-target-domain relationships remain.

- `test_age_domain_scoped_reset_rejects_unsafe_domain`
  - In the guarded test graph, call reset for a non-`pytest_protocol_v2_*` domain.
  - Assert `ValueError` or a dedicated safety exception.
  - Do not target `soc_graph` in this test.

- `test_age_domain_scoped_reset_preserves_shared_context`
  - Create a target-domain context and another-domain context with the same `entity_id`.
  - Reset the target domain.
  - Assert the other-domain `DomainContext` and relationships remain.
  - If creating this topology is too broad, fold the assertion into `test_age_domain_scoped_reset`.

Keep skipped:

- reset against `soc_graph`
- production/demo cleanup
- migration replay
- outbox/service-layer tests
- SOC projection tests
- S2P AGE migration tests
- reset of shared legacy SOC semantic nodes

## Implementation prompt outline

First implementation scope:

- `ci-platform/ci_platform/graph/age_graph_store.py`
  - Add `archive_decisions(...)`.
  - Add guarded `domain_scoped_reset(...)`.
  - Update `count_decisions(...)` to exclude archived decisions.
  - Update `count_verified_decisions(...)` to exclude archived decisions.
  - Optionally update `count_archived(...)` to count `Decision.archived = true`.
  - Keep legacy `count_verified(...)` outcome-edge based unless a separate compatibility review changes it.
  - Keep `archive_old_decisions(...)` no-op unless a separate legacy retention review changes it.

- `ci-platform/ci_platform/graph/age_sdk_adapter.py`
  - Add wrapper methods if required by the SDK adapter surface.

- `copilot-sdk/tests/graph/test_protocol_v2_conformance.py`
  - Add guarded AGE archive tests.
  - Add guarded AGE reset tests.
  - Add coverage for relationship preservation during archive.
  - Add coverage for other-domain and shared-`DomainContext` preservation during reset.
  - Keep future/service/migration/SOC tests skipped.

Potential helper reuse:

- Reuse the transaction-capable AGE helper introduced for EvidenceReceipt for `domain_scoped_reset`.
- Do not broaden the helper for unrelated AGE operations.

Must remain untouched:

- S2P AGE migration.
- GraphStore factory.
- outbox/service-layer accepted pending sync.
- frontend/Playwright.
- production routes.
- SOC projection implementation.
- EvidenceReceipt chain semantics except incidental transaction helper reuse.

## Blockers / open questions

- Verify exact PostgreSQL+AGE delete syntax for relationship and node deletion before implementation.
- Decide whether AGE `get_decisions` and `get_all_decisions` should filter archived decisions by default or preserve legacy all-decision semantics. Active counts must filter archived decisions.
- Decide whether future archive should also create an `ArchiveEvent` node. Not needed for first implementation.
- Decide whether `status_filter="all"` should ever be supported. It should not be part of the first implementation.
- Older AGE decisions missing numeric `created_at` are non-archivable in the first implementation. Normalizing legacy timestamps is a separate migration task.
- If both `created_at` and legacy `timestamp` exist, archive uses `created_at` only in the first implementation.
- Reset is intentionally limited to guarded test graph/domain contexts. A product/admin reset design would require a separate safety review.
