# Production outbox retirement design

Date: 2026-10-07T12:10:12-07:00

## Pre-check

The most recent session entry is DSTORE-CLEANUP: FAILED, stopped on exactly the three references below. SDK-STEP7-SQLITE-RETIREMENT records PASS and deletion of sqlite_store.py and dual_write_store.py; both files are absent. The last full SDK result is 4,407 passed / 1 xfailed / 0 failed / 0 errors. Steps 5-13 have PASS/COMPLETE records; Steps 1-4 cannot be confirmed from this SDK session record. Step 7 is the explicit prerequisite and is satisfied.

## Complete source reads and findings

Both affected modules were read end-to-end before edits. The old concrete queue exists; these are not dangling imports. Its SQLite connection, secondary_outbox table, append/read/ack/failure/quarantine/purge operations and file/schema locking support only legacy secondary-write replay. It is separate from the allowed scoring/persistence_outbox.py.

| Original location | Line content | Use | Proposed fix | Impact of deleting only the reference |
| --- | --- | --- | --- | --- |
| outcome_service.py:8 | Import of the retired concrete queue from copilot_sdk.graph.outbox | Names the queue dependency used by the constructor and retry methods | Remove the import together with its dependent pending-sync/replay code and unused lock/path imports | Import removal alone leaves an unresolved annotation and does not retire the dependency |
| outcome_service.py:34 | outbox parameter annotated with that concrete queue type | Constructor injection; learn() appends failures and replay() reads, commits, and acknowledges queued writes | Remove the required keyword parameter and stored queue attribute; learn() calls _commit directly; remove replay()/_replay_locked() | Removing only the parameter or annotation leaves self.outbox accesses broken or untyped; these methods must be removed coherently |
| outbox.py:15 | Concrete legacy queue class definition | Implements a second SQLite persistence buffer | Retire the entire implementation and leave an importable module documenting retirement and the supported scoring buffer location | Deleting only the class name or renaming it leaves prohibited SQLite persistence or invalid code; deleting the module would fail the required import smoke |

No instances of this queue or service are constructed in copilot_sdk/, apps/, or tests/. No remaining non-queue functions exist in outbox.py. Preserve ProtocolV2OutcomeStore, OutcomeWriter, ProtocolV2OutcomeService, set_canonical_writer(), canonical learn() success response, _commit(), _current_v(), _state(), and _payload() in outcome_service.py. Do not alter the accounting algorithm or graph protocol. Backend failures now propagate; never report pending sync without a supported queue.

## Proposed implementation

1. outcome_service.py: remove the obsolete concrete queue import and constructor parameter/attribute; remove pending-sync catch and replay methods; keep direct canonical commits and all existing conservation updates. Update stale SQLite/pending-sync documentation. No replacement protocol or None parameter is needed because the queue functionality is retired, not rebound.
2. outbox.py: remove the obsolete queue class, SQLite/JSON/threading/time/path/lock imports, and all queue-only operations. Keep an importable documentation-only module; do not alias another implementation under a retired name.
3. No test, export, graph backend, namespace, or scoring persistence-buffer changes. The design and session entry are the explicitly requested documentation exceptions to the two-source-file scope. Do not refresh generated graph files in this narrowly restricted task.

## Verification plan

- Mypy after each source change and both files at completion.
- Scan both targets for the retired symbol; rerun the cleanup patterns over SDK/tests to check the original blocker is removed.
- Run the exact requested targeted selection: python -m pytest tests/ -q --timeout=120 -k "outcome_service or outbox". Only use full SDK fallback if no tests match.
- Import both modules.
- Exercise retained canonical service behavior directly against a real InMemoryGraphStore with seeded conservation state, a real decision/outcome, idempotent repeat, and missing-decision failure. No test files or store mocks.
- The recorded full SDK baseline remains 4,407 / 1 xfailed; do not present targeted results as a new full run.

## Design review findings (resolved before implementation)

- The requested exact original source excerpts are historical evidence, not new code dependencies:
  - outcome_service.py:8: `from copilot_sdk.graph.outbox import DurableOutbox`
  - outcome_service.py:34: `outbox: DurableOutbox,`
  - outbox.py:15: `class DurableOutbox:`
- All specified caller searches plus a full service/protocol/class-name scan across SDK/apps/tests found only these modules. There are no in-repository callers to update. Unknown external callers using the retired queue constructor or replay API would need to migrate; no compatibility alias is added.
- Removing only the type or renaming the class would leave the second SQLite implementation intact. Remove its entire queue implementation and dependent service branch instead.
- No replacement parameter is necessary. Keep the injectable canonical_writer and its setter; persistence failures propagate. Canonical success and conservation logic remain intact.
- Keep both module paths importable as explicitly requested. outbox.py has no independent functionality to preserve beyond importability; outcome_service.py retains its canonical commit behavior.
- No export changes or test changes are necessary. The retained scoring persistence buffer is neither edited nor imported as an incompatible drop-in replacement.
- Verification limitation: the original service-specific tests were deleted in Step 7; the requested selection primarily covers the retained outbox subsystems. Add a direct real-store smoke execution without adding a test file.

## Verification results

- Targeted selection: 72 passed, 4,336 deselected; no failures/errors. Full SDK fallback was not needed because tests matched.
- Mypy: both files PASS individually after edits and together.
- Both required module imports: PASS.
- Real InMemoryGraphStore smoke: canonical commit, V increment, idempotent repeat, writer setter, and missing-decision error propagation PASS. The initial standalone smoke used an invalid COLD_START storage status; valid RED setup passed without code changes.
- All eight cleanup patterns are now empty across SDK/tests; no secondary SQLite import remains in either affected module.
- Tests, persistence buffer, exports, graph protocol, memory backend, and namespace hashes are unchanged (360 protected files checked).
