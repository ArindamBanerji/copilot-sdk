# AGE Protocol v2 local conformance skip triage

Date: 2026-06-01

## Context

AGE Slice 8 passed GPT-5.5 review with no fixer required. The accepted scope included soft
`archive_decisions`, guarded transactional `domain_scoped_reset`, archived-aware
`count_decisions` and `count_verified_decisions`, AGE adapter wrappers, and guarded AGE
conformance tests.

Before this triage, `tests/graph/test_protocol_v2_conformance.py` appeared as an untracked
file in `copilot-sdk`. It is still untracked at the time of this report; this report does not
stage or commit it.

Future warning: if new Protocol v2 relationship types are added, AGE `domain_scoped_reset`
must be extended and tested for those relationships, or replaced with a verified
domain-scoped detach/delete strategy. Slice 8 reset currently covers the known Protocol v2
relationships: `EMITTED_RECEIPT`, `HAS_OUTCOME`, and `ABOUT`.

## Baseline commands

Repository hygiene:

- `git status --short` from `copilot-sdk`: dirty worktree with many unrelated modified and
  untracked files; `tests/graph/test_protocol_v2_conformance.py` is untracked.
- `git diff --stat` from `copilot-sdk`: large unrelated dirty diff across the repo.
- `git diff -- tests/graph/test_protocol_v2_conformance.py`: empty because the file is
  untracked.
- `git status --short` from `ci-platform`: `age_client.py`, `age_graph_store.py`, and
  `age_sdk_adapter.py` are modified; `graphify-out/assessment_a.txt` is untracked.
- `git diff --stat` from `ci-platform`: 3 graph files changed.

Skip and test baseline:

- `python -m pytest tests/graph/test_protocol_v2_conformance.py -q --timeout=120 -rs`
  - `34 passed, 53 skipped`
- `python -m pytest tests/graph/test_protocol_v2_conformance.py -q --timeout=120 -m age -rs`
  without AGE env:
  - `44 skipped, 43 deselected`
- `python -m pytest tests/graph -q --timeout=120 -rs`
  - `127 passed, 67 skipped`

No live AGE run was performed during this triage because `AGE_INTEGRATION`, `AGE_TEST_DSN`,
and `AGE_TEST_GRAPH` were not configured in the shell environment. This triage did not invent
or reuse a DSN.

## Skip classification

| Test name / pattern | Skip reason | Default local status | AGE-live status | Classification | Recommended action |
| --- | --- | --- | --- | --- | --- |
| `@pytest.mark.age` Protocol v2 AGE tests | `AGE_INTEGRATION=1 required for AGE Protocol v2 conformance` when env is absent | 44 skipped | Active only with explicit AGE env; otherwise skipped | EXPECTED_AGE_ONLY | Keep guarded. These are live AGE adapter/graph semantics and should not be converted to fake local fixtures. |
| `test_v1_decision_idempotent` | `Protocol v2 implementation pending` | 1 skipped | Not AGE-specific | FIXTURE_LIMITATION | Keep as a local cleanup candidate. v1 `write_decision` generates IDs, so this placeholder should be clarified or replaced with a concrete local idempotency scenario. |
| `test_concurrent_cross_domain` | `Protocol v2 AGE adapter implementation pending` | 1 skipped | Not currently active | SHOULD_REMAIN_LIVE_ONLY | Keep as a future AGE concurrency/domain-isolation test. It should be implemented against live AGE if needed, not as a local-only assertion. |
| `test_evidence_receipt_concurrent_append` placeholder | `Protocol v2 AGE adapter implementation pending` | 1 skipped | Duplicates already-active AGE receipt concurrency coverage from Slice 7 | ACCIDENTAL_SKIP | Cleanup candidate: remove, rename, or re-scope this stale placeholder in a tiny skipped-test cleanup. Do not weaken the active AGE receipt concurrency test. |
| `test_age_transaction_rollback` placeholder | `Protocol v2 AGE adapter implementation pending` | 1 skipped | Partly covered by active EvidenceReceipt rollback test; generic transaction rollback remains broader | FIXTURE_LIMITATION | Clarify as generic AGE transaction rollback or remove if redundant after confirming intended coverage. |
| `test_migration_replay` | `SQLite-to-AGE migration replay implementation pending` | 1 skipped | Future migration only | EXPECTED_AGE_ONLY | Keep skipped. S2P AGE migration remains blocked and out of scope. |
| `test_outbox_replay_ordering` | `Protocol v2 outbox/service-layer implementation pending` | 1 skipped | Future service-layer/outbox only | SHOULD_REMAIN_LIVE_ONLY | Keep skipped until outbox worker/service-layer replay exists. |
| `test_governed_decision_conflict_quarantines` | `Protocol v2 outbox/service-layer implementation pending` | 1 skipped | Future outbox/quarantine only | SHOULD_REMAIN_LIVE_ONLY | Keep skipped; direct local duplicate behavior is already covered separately. |
| `test_evolution_event_conflict_quarantines` | `Protocol v2 outbox/service-layer implementation pending` | 1 skipped | Future outbox/quarantine only | SHOULD_REMAIN_LIVE_ONLY | Keep skipped until quarantine semantics exist. |
| `test_outbox_quarantine_recorded` | `Protocol v2 outbox/service-layer implementation pending` | 1 skipped | Future outbox/quarantine only | SHOULD_REMAIN_LIVE_ONLY | Keep skipped until outbox quarantine storage exists. |
| `test_protocol_v2_service_layer.py` module | `Protocol v2 implementation pending` | 4 skipped in full graph run | Future service-layer only | SHOULD_REMAIN_LIVE_ONLY | Keep skipped until service-layer `accepted_pending_sync` work is explicitly scoped. |
| `test_soc_age_projection_contract.py` module | `SOC projection implementation pending` | 10 skipped in full graph run | Future SOC projection only | EXPECTED_AGE_ONLY | Keep skipped. Do not claim SOC canonical projection conformance yet. |

## Local fixture coverage audit

Archive local coverage:

- `test_archive_pending` covers pending archive against SQLite and Memory, cutoff behavior,
  other-domain isolation, and verified count preservation.
- `test_archive_verified` covers verified archive confirmation guard, active V decrease,
  cutoff behavior, and other-domain isolation against SQLite and Memory.
- Local stores archive by moving/removing active local rows, so relationship-preservation
  assertions are AGE-specific rather than local fixture coverage.
- Missing or non-numeric AGE `created_at` cutoff behavior is an AGE-specific graph
  compatibility case and is covered by AGE-live tests, not local SQLite/Memory fixtures.

Reset local coverage:

- `test_domain_scoped_reset` covers target-domain clearing, other-domain preservation,
  idempotency, and all implemented local Protocol v2 tables for SQLite and Memory.
- Unsafe AGE graph/domain guard behavior is intentionally AGE-live-only because it is tied to
  graph names and destructive test-graph safeguards.

Counts and V:

- Local tests cover status-based V, pending exclusion, outcome lifecycle, archived verified
  exclusion from active V, and active decision count behavior.
- AGE-live tests cover archived-aware `count_decisions` and `count_verified_decisions` against
  AGE graph nodes.
- Protocol v2 V remains status-based and does not use Outcome counts.

Adapter:

- Local conformance covers GraphStore method semantics for SQLite/Memory.
- AGE-live tests cover AGE adapter wrappers and guard propagation. These should remain live AGE
  tests because fixture-only substitution would reduce parity.

## AGE-live-only rationale

The AGE-marked conformance tests validate behavior that depends on PostgreSQL+AGE graph labels,
Cypher semantics, relationship preservation, transaction helper behavior, lock rows, guarded
test graph names, and destructive reset protections. Those tests are correctly skipped by
default unless all explicit AGE integration environment variables are set.

Archive relationship preservation, AGE reset guard behavior, reset delete ordering, AGE receipt
transaction rollback, and AGE receipt concurrency should remain live-only. They cannot be
validated honestly by SQLite or memory fixtures without hiding the AGE behavior under test.

## Coverage gaps and cleanup candidates

- `test_v1_decision_idempotent` is a vague local placeholder. Either clarify the v1 ID
  semantics or replace it with a concrete local test if a caller-supplied v1 ID path exists.
- `test_evidence_receipt_concurrent_append` is a stale skipped placeholder now that the live
  AGE receipt concurrency test exists. It should be removed or renamed in a narrow cleanup.
- `test_age_transaction_rollback` is broad and partly duplicated by the active EvidenceReceipt
  rollback/failure-injection test. Keep only if it is meant to become a generic transaction
  helper rollback test across more Protocol v2 write paths.
- No accidental broad skip is hiding local archive/reset behavior; local SQLite/Memory coverage
  is active.

## Recommended next slices

1. Tiny skipped-test cleanup: resolve the stale `test_evidence_receipt_concurrent_append`
   placeholder and clarify or rename `test_age_transaction_rollback`.
2. Local v1 compatibility cleanup: decide whether `test_v1_decision_idempotent` is still a real
   invariant; if so, implement a concrete local fixture test, otherwise re-scope the placeholder.
3. AGE graph reset future-proofing: when adding any new Protocol v2 relationship, add reset
   coverage for that relationship in the same slice.
4. Keep service-layer/outbox, SOC projection, GraphStore factory, and S2P migration skipped
   until explicitly scoped.

## Slice 10 cleanup

Slice 10 performed the tiny skipped-test cleanup recommended above. No production code was
changed.

- Stale placeholder removed/renamed: removed the skipped
  `test_evidence_receipt_concurrent_append` placeholder. Active live AGE coverage already exists
  in `test_age_evidence_receipt_concurrent_append`.
- Rollback placeholder clarified: renamed the broad `test_age_transaction_rollback` placeholder
  to `test_age_transaction_rollback_preserves_domain_on_mid_reset_failure` and gave it a precise
  skip reason. It remains live-only because safe reset mid-failure injection must exercise the
  real AGE transaction helper without corrupting the test graph.
- v1 idempotency resolved as: replaced the skipped `test_v1_decision_idempotent` placeholder
  with active local coverage, `test_v1_write_decision_generates_distinct_ids`. This reflects the
  current v1 behavior: `write_decision` generates IDs by default; idempotent replay belongs to
  caller-supplied v2 IDs, EvidenceReceipt intent IDs, or future outbox semantics.
- Before skip count: `34 passed, 53 skipped` for
  `tests/graph/test_protocol_v2_conformance.py`.
- After skip count: `35 passed, 51 skipped` for
  `tests/graph/test_protocol_v2_conformance.py`.
- Remaining skips: 44 AGE-marked tests guarded by explicit AGE env, one future AGE
  cross-domain concurrency placeholder, one generic AGE reset rollback placeholder, one migration
  replay placeholder, and four outbox/service-layer placeholders.
- `tests/graph/test_protocol_v2_conformance.py` still must be tracked before merge if it remains
  untracked in `git status`.

## Slice 11 rollback failure-injection

Slice 11 converted the generic AGE reset rollback placeholder into an active live AGE test. No
production code was changed.

- Decision: active test added in `test_age_transaction_rollback_preserves_domain_on_mid_reset_failure`.
- Reason: the reset implementation already has a narrow private helper seam,
  `_delete_domain_label`, that can be monkeypatched inside the test after the real
  `AGEClient.run_transaction` path has started. This avoids adding a production test hook.
- Files changed: `tests/graph/test_protocol_v2_conformance.py` and this triage report.
- Rollback invariant covered: a controlled exception after reset relationship deletes and the
  first target-domain node delete must roll back the transaction, preserving the target domain
  and an unrelated same-graph domain.
- Local fixture limitation: SQLite and Memory fixtures cannot exercise PostgreSQL+AGE
  transaction rollback or AGE relationship delete behavior, so this remains AGE-live-only.
- Live AGE requirement: the test still requires `AGE_INTEGRATION=1`, explicit `AGE_TEST_DSN`,
  explicit `AGE_TEST_GRAPH`, a guarded `protocol_v2_test*` graph, and a
  `pytest_protocol_v2_*` domain.
- Remaining risk: future Protocol v2 relationship types must extend reset coverage in the same
  implementation slice that introduces the new relationship.
