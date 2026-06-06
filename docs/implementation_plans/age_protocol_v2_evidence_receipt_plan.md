# AGE Protocol v2 EvidenceReceipt Transaction/Hash-Chain Plan

## Purpose

Design AGE Protocol v2 `append_evidence_receipt(...)` before implementation.
EvidenceReceipt is audit memory, not conservation input, and its hash-chain
append semantics are more transaction-sensitive than the previous AGE slices.

This plan keeps S2P AGE migration, GraphStore factory work, outbox processing,
archive/reset, production routes, and frontend work out of scope.

## Current AGE evidence/audit state

- `ci-platform/ci_platform/graph/age_graph_store.py` has no
  `append_evidence_receipt(...)` method today.
- `ci-platform/ci_platform/graph/age_sdk_adapter.py` has no SDK wrapper for
  `append_evidence_receipt(...)`.
- Current AGE Protocol v2 support covers governed decisions, outcomes,
  observations, conservation snapshots, fingerprints, centroid checkpoints,
  evolution events, and entity links.
- No first-class `EvidenceReceipt` AGE node is written by the AGE adapter today.
- `docs/soc_age_schema_compatibility_spec_v1.md` states that
  `EvidenceReceipt` is not currently first-class in AGE, that a ledger exists
  outside the graph, and that some audit fields may be embedded on `Decision`.
- `ci-platform/ci_platform/audit/evidence_ledger.py` implements an in-memory
  hash-chained audit ledger with `LedgerEntry` and `OutcomeEntry`. It is useful
  prior art for hash-chain concepts, but it is not the Protocol v2 AGE graph
  receipt store.
- Existing SOC/onboarding code references the evidence ledger and may embed
  fields such as `entry_hash` into decision metadata, but this is not equivalent
  to graph-native `EvidenceReceipt` nodes.
- `AGEClient` currently opens a new psycopg connection per query with
  `autocommit=True`. There is no explicit transaction helper, no advisory-lock
  helper, and no helper that executes SQL plus AGE Cypher on one connection.

## Canonical EvidenceReceipt target

`append_evidence_receipt(...)` should create a distinct AGE
`(:EvidenceReceipt)` node with at minimum:

- `receipt_intent_id`
- `receipt_id`, an alias equal to `receipt_intent_id`
- `domain`
- `decision_id`
- `chain_index`
- `previous_hash`
- `payload_hash`
- `actor`
- `source_route`
- `canonical_payload`, serialized deterministically
- `metadata`, serialized deterministically
- `created_at` as float epoch
- `schema_version: "protocol_v2"`

The canonical relationship is:

- `(Decision)-[:EMITTED_RECEIPT]->(EvidenceReceipt)`

AGE should require the referenced `Decision` to exist in the same `domain`.
This avoids orphan graph receipts and makes audit traversal start from the
decision node. Missing Decision should raise `KeyError`.

EvidenceReceipt writes must not create or mutate `Decision`, `Outcome`,
`Observation`, `ConservationStatus`, `Fingerprint`, `CentroidCheckpoint`,
`EvolutionEvent`, `DomainContext`, or lifecycle status except for adding the
`EMITTED_RECEIPT` relationship from an existing Decision.

## Payload hash definition

AGE must match the local SQLite/Memory payload-hash semantics.

The hash input is canonical JSON:

```python
receipt_payload = {
    "receipt_intent_id": str(receipt_intent_id),
    "domain": str(domain),
    "decision_id": str(decision_id),
    "canonical_payload": canonical_payload,
    "actor": actor,
    "source_route": source_route,
    "metadata": metadata or {},
}
encoded = json.dumps(
    receipt_payload,
    default=_json_default,
    sort_keys=True,
    separators=(",", ":"),
)
payload_hash = sha256(encoded.encode("utf-8")).hexdigest()
```

The hash includes caller-stable receipt content. It must exclude
store-generated fields:

- `created_at`
- `chain_index`
- `previous_hash`
- AGE vertex ids
- relationship ids

AGE should reuse or locally duplicate the SQLite-compatible `_json_default`
behavior for numpy values only if the AGE adapter can import it without
cross-package coupling. Otherwise add a small AGE-local helper with the same
semantics.

## Idempotency semantics

Identity is `(domain, receipt_intent_id)`.

- Same `receipt_intent_id` and same `payload_hash`:
  return existing `(chain_index, payload_hash)` and do not mutate the graph.
- Same `receipt_intent_id` and different `payload_hash`:
  raise `ValueError` and preserve the existing chain.
- Different `receipt_intent_id`:
  append a new receipt at the next per-domain `chain_index`.

Receipt replay must never silently overwrite a different existing receipt.

## Chain append options

### Option A - single Cypher best-effort append

One AGE Cypher statement would:

1. Match the existing Decision.
2. Check no `EvidenceReceipt` with the same `(domain, receipt_intent_id)`.
3. Find the latest receipt for the domain.
4. Create the new `EvidenceReceipt`.
5. Create `EMITTED_RECEIPT`.

This may be acceptable for a non-concurrent conformance slice, but it is not
race-safe. AGE/Cypher cannot compute the SHA-256 payload hash, and without a
transaction-level lock two writers can observe the same latest receipt and
create forked or duplicated `chain_index` values.

### Option B - SQL lock row plus AGE Cypher on one connection

Add a transaction-capable AGE helper that:

1. Opens one psycopg connection with `autocommit=False`.
2. Loads AGE and sets the AGE search path.
3. Ensures a relational lock table exists outside AGE:
   `protocol_v2_receipt_locks(domain TEXT PRIMARY KEY)`.
4. Inserts the lock row for the receipt domain if missing.
5. Executes `SELECT domain FROM protocol_v2_receipt_locks WHERE domain = %s FOR UPDATE`.
6. Executes duplicate-intent diagnostics.
7. Verifies the referenced Decision exists in the same domain.
8. Reads latest receipt for the domain.
9. Computes `chain_index` and `previous_hash` in Python.
10. Creates the `EvidenceReceipt` node and `EMITTED_RECEIPT` edge.
11. Verifies one receipt and one edge were created.
12. Commits, releasing the row lock.

This is the correct race-safe design for AGE EvidenceReceipt. It requires an
AGEClient helper that can execute SQL lock statements plus multiple AGE Cypher
statements on the same transaction-bound connection. It avoids advisory-lock
hash collision ambiguity because the lock identity is the exact domain string.

### Option C - domain chain state node

Create or maintain a per-domain `(:EvidenceChainState)` node with
`latest_index` and `latest_hash`, and update it in the same Cypher statement
that creates the receipt. This keeps state in graph form, but it still needs a
proven concurrency mechanism. Without compare-and-set or transaction isolation
guarantees over the state node, two writers can lose updates or fork the chain.

### Option D - defer implementation

Keep AGE EvidenceReceipt tests skipped until a transaction helper exists.
This is safest if the project is not ready to add transaction-capable AGE
client support.

## Recommended immediate strategy

Use Option B as the implementation target for the next AGE EvidenceReceipt
slice: add a narrow transaction/SQL-lock-row helper and implement
`append_evidence_receipt(...)` on top of it.

Do not implement a best-effort read-then-create receipt chain. EvidenceReceipt
is a chain-sensitive audit primitive, and Protocol v2 explicitly calls for a
per-domain lock for AGE. This plan chooses a relational lock row keyed by the
exact domain instead of advisory hash locks.

If the implementation needs to be split, the first code slice should be:

1. Add transaction/SQL-lock-row helper support in `AGEClient` or
   `AGEGraphStore`.
2. Add `append_evidence_receipt(...)`.
3. Activate non-concurrent chain/idempotency tests.

If the first implementation does not include a concurrent test, call it
"transactional non-concurrent conformance." Do not claim race-safe conformance
until a deterministic live AGE concurrent append test passes.

## Future race-safe strategy

After the immediate implementation passes non-concurrent conformance:

- Add deterministic concurrent append tests using two receipt intents in the
  same domain.
- Require no duplicate `chain_index`, no gaps, and correct `previous_hash`
  linkage.
- Add rollback/failure-injection tests if the helper exposes a test hook or
  can be verified without brittle database fault injection.
- Consider adding an AGE-side uniqueness backstop if PostgreSQL catalog access
  to AGE label tables is made reliable. Do not depend on this as the primary
  Protocol v2 guard in the first slice.

## Atomicity and concurrency policy

Non-concurrent AGE EvidenceReceipt is not enough for migration readiness.
However, it can be acceptable as a first implementation slice only if it uses
the same transaction/SQL-lock-row helper intended for concurrent correctness.

Before claiming race-safe EvidenceReceipt:

- The append path must run under one transaction.
- The append path must lock the exact per-domain row in
  `protocol_v2_receipt_locks`.
- The same psycopg connection must execute every SQL and AGE/Cypher statement
  in the append path.
- `autocommit` must be disabled for the transaction.
- Lock acquisition, duplicate intent classification, Decision existence check,
  latest-chain read, chain index allocation, previous-hash selection, receipt
  creation, edge creation, and post-create verification must all happen before
  commit.
- Any failure must roll back the receipt node and edge.
- Concurrent append tests must prove no chain fork/gap.

Until then, skip:

- `test_evidence_receipt_concurrent_append`
- AGE transaction rollback/failure injection
- outbox replay/quarantine table behavior
- migration replay

## Missing Decision / duplicate / corruption diagnostics

### Missing Decision

AGE should require an existing `Decision` with matching `decision_id` and
`domain`. Missing Decision raises `KeyError`. No receipt node should be created.

### Duplicate intent

Inside the transaction and lock:

1. Search for `(:EvidenceReceipt {domain, receipt_intent_id})`.
2. If found and `payload_hash` matches, return existing
   `(chain_index, payload_hash)`.
3. If found and `payload_hash` differs, raise `ValueError`.

### Chain corruption

Before appending, read the latest receipt:

- If none exists, next index is `0` and `previous_hash` is `"GENESIS"`.
- If one exists, next index is `last.chain_index + 1` and `previous_hash` is
  `last.payload_hash`.

If diagnostics find multiple receipts with the same `chain_index` for a domain,
or if the latest receipt lacks `chain_index` or `payload_hash`, raise
`RuntimeError` and do not append. This signals existing chain corruption rather
than extending it.

### Orphan receipt

The transaction should create the receipt and edge together. If the edge cannot
be created, the transaction must roll back. No orphan `EvidenceReceipt` should
be committed for the canonical append method.

## Transaction helper requirements

The implementation must not use the existing AGEClient per-query autocommit
path for `append_evidence_receipt(...)`.

The transaction helper must:

1. Open one psycopg connection with `autocommit=False`.
2. Execute `LOAD 'age'`.
3. Execute `SET search_path = ag_catalog, '$user', public`.
4. Ensure the lock table exists using:
   `CREATE TABLE IF NOT EXISTS protocol_v2_receipt_locks (domain TEXT PRIMARY KEY)`.
5. Insert the target domain lock row if missing:
   `INSERT INTO protocol_v2_receipt_locks(domain) VALUES (%s) ON CONFLICT DO NOTHING`.
6. Acquire the lock:
   `SELECT domain FROM protocol_v2_receipt_locks WHERE domain = %s FOR UPDATE`.
7. Execute all required AGE/Cypher statements through the same connection using
   the same Cypher SQL wrapping/parsing semantics as `AGEClient._sync_execute`.
8. Commit only after the receipt node and `EMITTED_RECEIPT` edge are verified.
9. Roll back on any exception.

The lock table is a small relational coordination table, not a product graph
table and not an outbox. It contains only domain keys. It avoids advisory
hash-collision risk and keeps lock ownership easy to inspect.

## Test activation plan

### Activate in first AGE implementation slice

- `test_age_evidence_receipt_chain`
  - Append three receipts in one unique AGE test domain.
  - Assert chain indexes `0, 1, 2`.
  - Assert first `previous_hash == "GENESIS"`.
  - Assert each later `previous_hash` equals prior `payload_hash`.
  - Assert receipt nodes and `EMITTED_RECEIPT` edges exist.
  - Does not require concurrency, but should use transaction helper.

- `test_age_evidence_replay_same_intent_skips`
  - Append one receipt.
  - Append same intent and same payload again.
  - Assert same `(chain_index, payload_hash)` returned.
  - Assert one receipt node and one edge.

- `test_age_evidence_replay_conflict_raises`
  - Append one receipt.
  - Append same intent with different canonical payload.
  - Assert `ValueError`.
  - Assert original chain unchanged.

- `test_age_evidence_missing_decision`
  - Call append for a missing Decision.
  - Assert `KeyError`.
  - Assert no receipt node for that intent.

- `test_age_evidence_no_decision_or_V_side_effect`
  - Create a governed pending Decision.
  - Append receipt.
  - Assert `count_decisions(domain)` unchanged.
  - Assert `count_verified_decisions(domain)` unchanged.
  - Assert Decision status unchanged.

- `test_age_evidence_chain_integrity_after_multiple_appends`
  - Can be combined with `test_age_evidence_receipt_chain` if test count needs
    to stay small.

All tests must use the existing guarded AGE fixture with a unique
`pytest_protocol_v2_*` domain and no destructive cleanup.

If concurrent append is not activated in the first implementation slice, the
test output and review notes must explicitly state that the slice provides
transactional non-concurrent conformance only.

### Keep skipped until later

- `test_evidence_receipt_concurrent_append`
- `test_age_transaction_rollback`
- outbox ordering/quarantine tests
- service-layer accepted-pending-sync tests
- SQLite-to-AGE migration replay tests
- SOC projection contract tests
- S2P AGE migration tests

## Safety guards

Preserve existing AGE test requirements:

- `AGE_INTEGRATION=1`
- explicit `AGE_TEST_DSN`
- explicit `AGE_TEST_GRAPH`
- reject missing graph name
- reject `soc_graph`
- require test graph name prefix such as `protocol_v2_test`
- unique per-test domains prefixed `pytest_protocol_v2_`
- no destructive cleanup/reset
- no production route wiring
- no product conformance claims from partial AGE support

## Implementation prompt outline

Next implementation prompt should be narrowly scoped to:

- `ci-platform/ci_platform/graph/age_client.py`
  - Add a minimal transaction helper capable of executing SQL lock-row
    operations and AGE Cypher on one transaction-bound connection.
  - Keep existing `run_query` behavior unchanged for non-transaction callers.
  - Reuse the existing Cypher SQL wrapping/parsing logic without opening a new
    connection per statement.

- `ci-platform/ci_platform/graph/age_graph_store.py`
  - Add canonical receipt payload hash helper matching local adapters.
  - Add `append_evidence_receipt(...) -> tuple[int, str]`.
  - Use the `protocol_v2_receipt_locks` per-domain row lock and one transaction.
  - Require existing Decision in same domain.
  - Store `receipt_id = receipt_intent_id` as a naming alias.
  - Create `EvidenceReceipt` and `EMITTED_RECEIPT` together.
  - Implement duplicate identical skip and duplicate conflict raise.

- `ci-platform/ci_platform/graph/age_sdk_adapter.py`
  - Add wrapper method.

- `copilot-sdk/tests/graph/test_protocol_v2_conformance.py`
  - Add guarded AGE tests listed above.

The next implementation prompt must keep untouched:

- S2P AGE migration
- GraphStore factory
- outbox worker/service-layer sync
- archive/reset
- production routes
- frontend/Playwright
- SOC projection implementation

## Implementation readiness

The plan is ready for a first implementation prompt after this repair.

The first implementation should include:

1. A narrow transaction helper that keeps SQL lock-row operations and AGE/Cypher
   statements on one psycopg connection with `autocommit=False`.
2. `append_evidence_receipt(...)` in AGEGraphStore using
   `protocol_v2_receipt_locks`.
3. SDK adapter wrapper.
4. Guarded AGE tests for chain append, same-intent replay, conflict, missing
   Decision, and no V/status side effects.

The first implementation may defer concurrent append and rollback/failure
injection tests, but if so it must label the result as transactional
non-concurrent conformance.

## Blockers / open questions

- Exact transaction helper shape: AGEClient-level generic helper vs
  AGEGraphStore-private psycopg helper. AGEClient-level is cleaner if kept
  minimal and non-invasive.
- AGE SQL wrapping: the helper must reuse the same Cypher wrapping/parsing
  logic as `_sync_execute` without opening a new connection per statement.
- `receipt_id` is decided: store it as an alias equal to
  `receipt_intent_id`. It is not a second identity.
- Whether historical SOC embedded audit fields will be backfilled into
  `EvidenceReceipt`. This must remain separate from forward-write
  implementation.
