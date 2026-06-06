# AGE Protocol v2 write_outcome implementation plan

## Purpose

This plan defines the next narrow AGE Protocol v2 slice: `write_outcome` lifecycle and direct duplicate semantics for the guarded AGE conformance test graph.

The product architecture remains unchanged:

- AGE/PostgreSQL+AGE is the canonical product graph.
- SQLite remains the local/test adapter.
- `soc_graph` must not be touched by conformance tests.
- S2P AGE migration remains blocked.
- Outbox/service-layer pending sync, EvidenceReceipt, Observation, archive/reset, GraphStore factory, SOC projections, and frontend work are out of scope.

The goal is to make AGE match the local Protocol v2 lifecycle invariant for outcomes:

- a Decision starts as `status='pending'`;
- a successful outcome write creates exactly one Outcome and `HAS_OUTCOME` edge;
- the same write atomically changes Decision status to `confirmed` or `overridden`;
- `count_verified_decisions` is status-based and increments only after the canonical write succeeds.

## Current AGE adapter behavior

Current AGE files inspected:

- `ci-platform/ci_platform/graph/age_graph_store.py`
- `ci-platform/ci_platform/graph/age_sdk_adapter.py`
- `ci-platform/ci_platform/graph/age_client.py`
- `copilot-sdk/tests/graph/test_protocol_v2_conformance.py`

Current state:

- `AGEGraphStore.write_governed_decision(...)` exists from AGE Slice 1 and creates a `Decision` node with `status: 'pending'`.
- `AGEGraphStore.count_decisions(domain)` counts `Decision` nodes by `domain`.
- `AGEGraphStore.count_verified_decisions(domain)` is status-based: it counts `Decision` nodes with `status = 'confirmed' OR status = 'overridden'`.
- Legacy `AGEGraphStore.count_verified(domain)` remains outcome-edge based and should not be used as Protocol v2 conservation V.
- `AGEGraphStore.write_outcome(...)` currently:
  - matches a `Decision`;
  - creates an `Outcome` node;
  - creates a `Decision -[:HAS_OUTCOME]-> Outcome` edge;
  - does not set `Decision.status`;
  - does not enforce one outcome per decision;
  - does not raise explicitly when the decision is missing;
  - does not guard duplicate direct calls.
- `Outcome` nodes and `HAS_OUTCOME` edges already exist as labels/edges in current AGE write behavior.
- Current implementation is a single Cypher query for the create path, but it lacks Protocol v2 guards.
- `AGEClient.run_query(...)` opens a connection per query with `autocommit=True`. There is no current multi-statement transaction helper.
- `AGEClient` rejects `MERGE`, so idempotency must not depend on `MERGE`.

## Protocol v2 target behavior

Target signature follows `GraphStore.write_outcome`:

```python
def write_outcome(
    self,
    decision_id: str,
    actual_action: str,
    is_correct: bool,
    metadata: dict[str, Any] | None = None,
) -> None:
    ...
```

Target behavior:

- require an existing `Decision`;
- require that the `Decision` has no existing `HAS_OUTCOME` edge and no existing `Outcome` with the same `decision_id`;
- create one `Outcome` node;
- create one `HAS_OUTCOME` edge from the Decision to the Outcome;
- set `Decision.status`:
  - `is_correct=True` -> `confirmed`;
  - `is_correct=False` -> `overridden`;
- raise for missing decisions;
- raise for direct duplicate outcomes;
- do not overwrite existing outcomes;
- preserve existing outcome/status when duplicate direct write raises;
- no orphan Outcome if Decision status update cannot be applied;
- no status transition without Outcome creation;
- `count_verified_decisions(domain)` increments only after the canonical AGE write succeeds.

Future outbox replay behavior is separate:

- identical replay may skip;
- conflicting replay must quarantine/error;
- outbox tables/worker/service-layer response semantics are not part of this slice.

## Atomicity options

### Option A: single Cypher statement

Use one AGE Cypher statement that:

1. matches the target `Decision`;
2. verifies no existing outcome relationship or same-decision Outcome exists;
3. creates the `Outcome`;
4. creates the `HAS_OUTCOME` edge;
5. sets `Decision.status`;
6. returns the updated status/outcome.

This avoids AGEClient's per-query autocommit problem because all mutations happen in one submitted statement.

Candidate shape:

```cypher
MATCH (d:Decision {decision_id: '...'})
WHERE NOT EXISTS((d)-[:HAS_OUTCOME]->(:Outcome))
  AND NOT EXISTS((:Outcome {decision_id: '...'}))
  AND d.status = 'pending'
SET d.status = 'confirmed'
CREATE (o:Outcome {
  decision_id: '...',
  domain: d.domain,
  actual_action: '...',
  actual_index: 0,
  is_correct: true,
  reward: 0.0,
  verifier: 'analyst',
  override_reason: null,
  metadata: '{}',
  verified_at: 123.0
})
CREATE (d)-[:HAS_OUTCOME]->(o)
RETURN d.status AS status, o AS o
```

Before implementation, this exact `NOT EXISTS((pattern))` form must be verified against Apache AGE. If AGE rejects pattern predicates, use a single-statement alternative that remains atomic, such as `OPTIONAL MATCH` plus `WITH` filtering:

```cypher
MATCH (d:Decision {decision_id: '...'})
OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(linked:Outcome)
WITH d, count(linked) AS linked_outcome_count
OPTIONAL MATCH (same:Outcome {decision_id: '...'})
WITH d, linked_outcome_count, count(same) AS same_decision_outcome_count
WHERE linked_outcome_count = 0
  AND same_decision_outcome_count = 0
  AND d.status = 'pending'
SET d.status = 'confirmed'
CREATE (o:Outcome {...})
CREATE (d)-[:HAS_OUTCOME]->(o)
RETURN d.status AS status, o AS o
```

This still submits one Cypher statement.

### Option B: transaction-capable helper

Add an AGEClient helper that opens one PostgreSQL connection with autocommit disabled and runs multiple AGE Cypher statements in one transaction.

This is more general and will be needed for later complex operations, but it expands the scope and touches the central AGE client. It is not needed if Option A works.

### Option C: defer implementation

If AGE cannot express the missing-decision, duplicate guard, Outcome create, edge create, and status update in one safe statement, and no transaction helper is approved, defer the slice.

## Recommended atomicity strategy

Use **Option A: single Cypher statement** for AGE Slice 2.

Rationale:

- It avoids multi-step autocommit hazards.
- It keeps the slice narrow.
- It does not require AGEClient transaction-helper changes.
- It can preserve all-or-nothing behavior inside one submitted Cypher statement.

Implementation must treat "no rows returned" as a classified failure, not a silent no-op.

To produce a precise exception, the adapter must run read-only diagnostic queries after the single write statement returns no rows:

1. read whether `Decision` exists for the `decision_id` and expected domain if the caller/test has a domain context;
2. if not, raise `KeyError(decision_id)`;
3. read whether either a linked outcome or a standalone `Outcome` with the same `decision_id` exists;
4. if yes, raise `ValueError("outcome already exists for decision_id: ...")`;
5. read the current `Decision.status`;
6. if status is not `pending`, raise `ValueError("decision status is not pending for decision_id: ...")`;
7. otherwise raise `RuntimeError("AGE write_outcome returned no rows for an unexpected reason: ...")`.

These diagnostic reads are not part of the mutation path and must not mutate the graph.

## Outcome node/edge schema

Minimum `Outcome` node properties for AGE Slice 2:

- `decision_id`: string;
- `domain`: copied from `Decision.domain`;
- `actual_action`: string;
- `actual_index`: integer, from `metadata["actual_index"]` if provided, else `0`;
- `is_correct`: boolean;
- `reward`: float, from `metadata["reward"]` if provided, else `0.0`;
- `verifier`: string, from `metadata["verifier"]` if provided, else `"analyst"`;
- `override_reason`: nullable string, from `metadata["override_reason"]` if provided, else `null`;
- `metadata`: canonical JSON string;
- `verified_at`: float epoch seconds, from metadata if supplied, else current time;
- `created_at`: float epoch seconds.

The current `GraphStore.write_outcome` method signature accepts only `metadata` beyond `decision_id`, `actual_action`, and `is_correct`. For AGE Slice 2, `reward`, `verifier`, `override_reason`, `actual_index`, and `verified_at` should be read from `metadata` when present and defaulted otherwise. This preserves Protocol v2 fields without widening the public method signature in this slice.

Relationship:

- `(Decision)-[:HAS_OUTCOME]->(Outcome)`

The edge may include:

- `decision_id`;
- `created_at`.

Do not add EvidenceReceipt or audit-chain nodes in this slice.

## Direct duplicate semantics

Direct duplicate behavior:

- if the Decision already has a `HAS_OUTCOME` edge, raise `ValueError`;
- if an `Outcome` node with the same `decision_id` already exists, raise `ValueError`;
- do not create a second Outcome;
- do not create another edge;
- do not mutate the original Outcome;
- do not alter the existing `Decision.status`.

Duplicate detection should use both:

- `Decision -[:HAS_OUTCOME]-> Outcome`;
- `Outcome.decision_id`.

Reason:

- edge-based detection is canonical graph structure;
- `Outcome.decision_id` catches malformed or partially migrated Outcome nodes.

## Missing decision semantics

If no `Decision` exists for `decision_id`:

- raise `KeyError(decision_id)`;
- create no Outcome;
- create no edge;
- create no status transition.

This should be tested against the AGE test graph with a unique missing ID.

## Status transition semantics

Mapping:

- `is_correct=True` -> `Decision.status = 'confirmed'`;
- `is_correct=False` -> `Decision.status = 'overridden'`.

Only `pending -> confirmed/overridden` should be considered valid for the normal direct path in AGE Slice 2.

If the Decision status is already `confirmed` or `overridden`, treat that as duplicate/invalid direct outcome state and raise.

If old SOC Decisions lack `status`, do not infer status in this slice. The guarded conformance tests run against `protocol_v2_test` and use `write_governed_decision`, which writes `pending`. Legacy/missing-status SOC compatibility is deferred to the SOC projection/migration plan and must not be solved by weakening Slice 2 status rules.

## count_verified_decisions interaction

`count_verified_decisions(domain)` must remain status-based:

```cypher
MATCH (d:Decision)
WHERE d.domain = ...
  AND (d.status = 'confirmed' OR d.status = 'overridden')
RETURN count(d) AS cnt
```

It must not use Outcome counts.

Expected behavior:

- pending decisions are excluded;
- confirmed decisions are included;
- overridden decisions are included;
- after successful `write_outcome`, V increments by 1;
- after missing/duplicate failure, V remains unchanged.

Archive filtering remains deferred until AGE archive semantics exist.

## Test activation plan

All AGE tests use the existing guarded fixture:

- `AGE_INTEGRATION=1`;
- explicit `AGE_TEST_DSN`;
- explicit `AGE_TEST_GRAPH`;
- reject `soc_graph`;
- require `AGE_TEST_GRAPH` to start with `protocol_v2_test`;
- unique `pytest_protocol_v2_*` domain per test;
- no destructive cleanup.

Recommended AGE Slice 2 tests:

| Test | Fixture | Purpose | Needs single-Cypher write | Cleanup |
| --- | --- | --- | --- | --- |
| `test_age_write_outcome_confirmed` | `age_store` | `is_correct=True` creates Outcome and sets status `confirmed` | Yes | unique domain/IDs |
| `test_age_write_outcome_overridden` | `age_store` | `is_correct=False` creates Outcome and sets status `overridden` | Yes | unique domain/IDs |
| `test_age_outcome_missing_decision` | `age_store` | missing Decision raises and creates no Outcome | Yes | unique domain/IDs |
| `test_age_outcome_direct_duplicate_raises` | `age_store` | second direct outcome raises, original status/outcome preserved | Yes | unique domain/IDs |
| `test_age_count_verified_after_outcome` | `age_store` | V increments only after successful outcome write | Yes | unique domain/IDs |
| `test_age_outcome_no_orphan_on_duplicate` | `age_store` | duplicate does not create second Outcome or mutate status | Yes | unique domain/IDs |
| `test_age_outcome_duplicate_standalone_node_raises` | `age_store` | standalone `Outcome.decision_id` without `HAS_OUTCOME` still blocks write | Yes | unique domain/IDs |

Potentially defer:

- `test_age_outcome_atomic_failure_injection`
- `test_age_outcome_duplicate_standalone_node_raises` if creating a standalone malformed Outcome in the test graph proves too broad for Slice 2. If deferred, keep it as a follow-up integrity test before migration replay or SOC projection claims.

Reason: proving rollback on an injected mid-statement failure may require AGE-specific trigger/error mechanics or a transaction helper. For Slice 2, single-Cypher structure plus duplicate/missing negative tests are the practical atomicity proof. Keep the existing broad `test_age_transaction_rollback` skipped until an AGE transaction/failure-injection strategy exists.

Tests still skipped:

- AGE transaction rollback failure injection;
- EvidenceReceipt;
- Observation;
- archive/reset;
- migration replay;
- outbox replay/quarantine;
- SOC projection tests;
- service-layer pending sync.

## Safety guards

Preserve the current fixture guards:

- skip unless `AGE_INTEGRATION=1`;
- require explicit `AGE_TEST_DSN`;
- require explicit `AGE_TEST_GRAPH`;
- reject `soc_graph`;
- reject blank graph name;
- reject graph names that do not start with `protocol_v2_test`;
- use unique `pytest_protocol_v2_*` domains;
- use unique decision IDs in AGE tests;
- no destructive cleanup;
- no `domain_scoped_reset`;
- no S2P migration;
- no production route changes.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| AGE pattern predicates differ from Neo4j | Verify candidate single-Cypher form against AGE; if `NOT EXISTS((pattern))` fails, use `OPTIONAL MATCH ... WITH count(...)` form that checks both linked and standalone outcomes. |
| Per-query autocommit creates partial writes | Use one Cypher statement for all mutations. Do not split create/update across calls. |
| Missing, duplicate, and non-pending status all return no rows | Use read-only diagnostic queries after no-row write result to classify `KeyError`, duplicate `ValueError`, non-pending `ValueError`, or unexpected `RuntimeError`. |
| Duplicate Outcome node exists without edge | Check both `HAS_OUTCOME` and `Outcome.decision_id`. |
| Test graph accumulates data | Use unique domains and unique decision IDs; defer cleanup until safe AGE reset design. |
| Existing SOC schema lacks status | Do not run tests against `soc_graph`; do not infer status for old SOC nodes in this slice. |
| Race-safe duplicate idempotency not guaranteed | Defer concurrent/idempotent replay tests until transaction/advisory-lock strategy. |

## Implementation prompt outline

Suggested next Codex prompt scope:

1. Edit only:
   - `ci-platform/ci_platform/graph/age_graph_store.py`
   - `ci-platform/ci_platform/graph/age_sdk_adapter.py` only if wrapper changes are needed
   - `copilot-sdk/tests/graph/test_protocol_v2_conformance.py`
2. Implement AGE `write_outcome` Protocol v2 behavior:
   - one Cypher mutation statement;
   - missing Decision raises `KeyError`;
   - duplicate direct outcome raises `ValueError`;
   - create `Outcome` with `actual_index`, `reward`, `verifier`, `override_reason`, `metadata`, `verified_at`, and `created_at`;
   - create `HAS_OUTCOME`;
   - set `Decision.status` to `confirmed` or `overridden`;
   - preserve original outcome/status on duplicate.
3. Activate only AGE outcome lifecycle tests:
   - confirmed;
   - overridden;
   - missing decision;
   - direct duplicate;
   - verified count after outcome.
4. Keep skipped:
   - AGE transaction failure injection;
   - outbox/replay/quarantine;
   - EvidenceReceipt;
   - Observation;
   - archive/reset;
   - SOC projection;
   - service-layer pending sync.
5. Validation:
   - default no-AGE conformance;
   - full graph and scoring suites;
   - AGE marked subset only with explicit non-`soc_graph` env.

## Blockers / open questions

- Does Apache AGE support `NOT EXISTS((d)-[:HAS_OUTCOME]->(:Outcome))` in `WHERE`?
- If not, does the `OPTIONAL MATCH ... WITH linked_outcome_count and same_decision_outcome_count` form work reliably in AGE?
- Should status transition explicitly require `d.status = 'pending'`, or should missing status be allowed for transitional AGE Decisions? Recommendation for Slice 2: require pending in conformance-created Decisions and treat existing non-pending as duplicate/invalid.
- Should AGE Outcome store `verified_at` as float epoch or ISO string? Decision for Slice 2: use float epoch to mirror SQLite local adapter, unless live AGE tests prove serialization issues that require a follow-up revision.
- When should a transaction-capable AGE helper be introduced? Recommendation: not in Slice 2 unless single-Cypher cannot express the required mutation.
