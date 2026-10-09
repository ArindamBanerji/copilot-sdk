# DecisionStore Migration Design v5

Task: DSTORE-MIGRATE-2-DESIGN-V5. Verification date: 2026-10-03, America/Los_Angeles. Model/reasoning: sol/high. Repository: copilot-sdk, branch main.

This is a verified design and execution plan, not an implementation. No production code, tests or infrastructure files were changed or deleted. The only deliverables are this document and the explicitly requested final append to `docs/session_state.md`. The latest session entry at start was `DSTORE-MIGRATE-2-DESIGN-VERIFY`, dated 2026-10-02T23:41:14-07:00. Earlier working-tree edits were preserved.

Evidence labels: **VERIFIED** means inspected or executed in this session; **DECISION** means the chosen future implementation policy; **UNVERIFIED** identifies a remaining operational fact, not an unresolved design choice. Source inspection and signature checks do not establish live database behavior.

## Executive Summary

Retire SQLiteGraphStore, DualWriteStore and DurableOutbox. Retain InMemoryGraphStore for disposable test/development state and AGEGraphStoreAdapter over AGEGraphStore for persistent/production state. Preserve the raw-SQLite PersistenceOutbox as the explicit scoring resilience exception. DecisionStore is already absent; do not recreate it.

**DD-8 is resolved: Option C, retire ProtocolV2OutcomeService.** The two-repository Python scan found its definition, package export and one dedicated test module, but no production invocation. Canonical outcome writes continue through the current scorer/GraphStore path and fail closed. Retire the service module/export and its pending-sync API with an explicit compatibility notice; do not teach PersistenceOutbox to queue outcomes. External installed consumers and deployed queue contents remain UNVERIFIED release prerequisites, not evidence of a production caller in this checkout.

Corrections and confirmations from v4:

1. All nine sizes and all five protocol declaration locations/counts are unchanged and freshly verified.
2. The broad inventory remains **148 files / 637 unique lines**. The new prompt's narrower SDK/package-only scans measure different scopes; their smaller counts are not code removal.
3. **70 is the exclusive category-A allocation, not the total number of importing files.** AST-confirmed SQLiteGraphStore imports occur on 112 lines across **96 files**. There are zero actual DecisionStore imports; its two textual matches are gate strings.
4. InMemoryGraphStore still has every named protocol method and still lacks the L5 `n=1` default. Runtime method presence does not establish full conformance. SQLiteGraphStore has the same obsolete L5 default defect; it need not be repaired before retirement.
5. DD-8 removes an architectural question and adds `graph/outcome_service.py` to the eventual deletion set. Its four dedicated tests must be reviewed individually; retain canonical commit/conservation invariants in active-path tests.
6. **Bundle fidelity is larger than a constructor change.** The existing AGE branch restores only decisions; the SQL branch also writes outcomes, checkpoints, RL state and evolution events. The report can mark the decision-only branch fully restored without accounting for other sections.
7. Two additional fidelity dependencies were verified: `rl/exploration.py:84,112` uses legacy RL methods absent from AGE, and AGE `save_centroids` stamps current time while its checkpoint reader does not implement the legacy temporal-filter kwargs. Include these in the durable-consumer work package. No new required GraphStore methods are needed for the selected design.
8. The consumer-first sequence remains mandatory. Keep six implementation prompts plus one review; allow approximately **5–8 engineering days** after including the newly identified fidelity work. This is a planning estimate, not measured runtime or a credit quotation.

All eight DDs are resolved below. Code deletion remains gated on implementation of bundle/restart preservation and explicit operational cutover evidence. “Design ready” does not mean those gates already passed.

## Source File Analysis

E1: `Path.stat().st_size` measured the following bytes on disk in this session. Every claimed path exists; all nine deltas from v4 are zero. Paths are SDK-relative except the final row.

| File | v4 bytes | Actual bytes | Verified characterization | Post-migration action |
| --- | ---: | ---: | --- | --- |
| `copilot_sdk/graph/sqlite_store.py` | 167948 | 167948 | GraphStore and V2 methods; all L5 names but the same missing-default defect; also traversal methods | DELETE after consumer/data gates |
| `copilot_sdk/graph/dual_write_store.py` | 36248 | 36248 | Declares GraphStore inheritance; wraps generic primary/secondary; factory chooses SQLite+AGE; also defines ReplayReport | DELETE after consumers |
| `copilot_sdk/graph/outbox.py` | 5906 | 5906 | DurableOutbox; used by dual write and independently by outcome service | DELETE after DD-8 execution |
| `copilot_sdk/graph/factory.py` | 11099 | 11099 | Four current backends; SQLite import at module scope, DualWriteStore import inside branch | MODIFY |
| `copilot_sdk/graph/protocol.py` | 17242 | 17242 | Five runtime-checkable protocols | UNCHANGED required membership/signatures |
| `copilot_sdk/graph/memory_store.py` | 99463 | 99463 | All five protocol method sets; one L5 call-shape defect | FIX default; consumer fidelity changes only where tests require |
| `copilot_sdk/backend/health_builder.py` | 5715 | 5715 | SQLite/memory/dual/AGE classification and wrapper unwrapping | MODIFY legacy branches |
| `copilot_sdk/scoring/persistence_outbox.py` | 17425 | 17425 | Direct sqlite3; independent artifact retry queue | KEEP unchanged for this migration |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py` | 26007 | 26007 | GraphStore, V2, L5 and Traversal methods; four native scoring-extension methods absent | KEEP; existing kwargs forwarding supports the planned checkpoint backend work |

E2: `python -c "import ci_platform; import os; print(os.path.dirname(ci_platform.__file__))"` succeeded and returned:

```text
C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\ci-platform\ci_platform
```

The installed package resolves to the sibling checkout. The adapter and supporting AGE backend were therefore accessible and verified, not marked inaccessible. AGEGraphStore itself lives in `ci_platform/graph/age_graph_store.py`; `age_client.py` is the lower-level client.

Additional disposition, beyond the nine-file table:

- `graph/outcome_service.py` exists and is **6,199 bytes**: DELETE under DD-8, with its export and dedicated retired-behavior tests handled first.
- `graph/__init__.py`: remove SQLite and outcome-service exports in coordination with consumers.
- `scoring/storage.py`: already absent; no deletion work remains.
- `config/graph_config.py`: update `Backend` Literal at line 19, both allowlists at 303/305, and dual-write DSN logic at 314.
- `apps/{trading,purchasing,dataops}/backend/app/graph_status.py`: remove SQLite defaults/fallback labels and retired-backend validation; explicitly support development memory and production AGE. Trading has dual-write branches; DataOps currently permits only SQLite/AGE.
- `scoring/scorer.py`, `graph/legacy_signal_filter.py`, `graph/read_diff_runner.py`: remove concrete dual-write handling while preserving governed writes, filtering, archive comparisons and pagination.
- `demo/bundle.py`, `rl/exploration.py`, `rl/presets.py` and relevant RL readers/tests: migrate actual persisted state semantics, not only class names.
- `ci_platform/graph/age_graph_store.py`: add preservation/readback of imported checkpoint fields through existing kwargs; this is additional cross-repository implementation scope discovered by E8. The adapter's existing forwarding does not require a new required protocol method.
- `migrate/__main__.py`, `migrate/reconcile_archive.py`, `migrate/sqlite_to_age.py`: retain explicitly offline legacy-source import/reconciliation tooling through a narrow read-only source reader, not SQLiteGraphStore. No factory registration, live scoring writes, generic backend replacement or new GraphStore implementation is permitted for that reader.

E7: current factory `_VALID_BACKENDS` at line 20 is `{"sqlite", "memory", "age", "dual_write"}`. Memory constructs `InMemoryGraphStore(domain=selected_domain)` at line 176 without forwarding the selected prefix. SQLite resolves explicit db_path, `CI_DATA_DIR/<domain>.db`, or `:memory:`. Dual write constructs SQLite primary, AGE secondary and a sibling `<domain>_dual_write_outbox.db`. AGE validates explicit domain/DSN/authorization and production capabilities. Preserve the LegacySignalFilteringGraphStore and optional TenantScopedGraphStore wrappers. Forward `decision_id_prefix` for memory when removing SQLite selection.

E7: health `_backend()` at line 34 checks SQLite, memory, dual primary and AGE adapter/backend, otherwise unknown. `_primary_store()` unwraps declared ownership and detects cycles. Readiness at line 80 requires connected AGE on `soc_graph`. Remove only retired branches/imports; do not equate a connected development memory store with production readiness.

## Five Protocols

E3: AST inspection counted direct declarations and inherited unique method names; callable lookup and representative protocol-permitted argument binding checked both retained implementations. No inherited protocol stub was mistaken for an implementation in these checks.

| Protocol | Declaration line | Declared | Effective | InMemoryGraphStore | AGEGraphStoreAdapter |
| --- | ---: | ---: | ---: | --- | --- |
| ScoringPersistenceStore | 16 | 4 | 4 | All methods/call shapes | Missing all four native methods; bridge used |
| GraphStore | 40 | 45 | 45 | All methods/call shapes | All methods/call shapes |
| GraphTraversalStore | 281 | 3 | 3 | All methods/call shapes | All methods/call shapes |
| ProtocolV2GraphStore | 307 | 22 | 66 | All methods/call shapes | All methods/call shapes |
| L5LearningStore | 531 | 7 | 7 | All names; one default defect | All methods/call shapes |

All five have `@runtime_checkable`. Only V2 inherits GraphStore. It redeclares `count_verified_decisions`, so its 22 declarations add 21 unique methods: 45 + 21 = 66. L5 remains separate. Required membership of GraphStore and V2 will not be enlarged during this migration.

The four staged scoring methods are `save_k_utility`, `get_k_utilities`, `save_holdout_decision`, `get_holdout_decisions`. E7 verified that KUtilityStore (`scoring/investigation.py:489`) and DataOpsGovernance (`apps/dataops/backend/app/dataops_governance.py:30`) construct GraphScoringPersistence, which calls existing `save_governance`/`list_governance`. Memory delegates its native extension methods to this same bridge. AGE does not need native extension methods for current callers to function.

Scope of the conformance claim: missing-name and representative positional/keyword/default binding checks passed as listed. Full static type variance, concurrency behavior and live AGE conformance are **UNVERIFIED in this pass** and are acceptance work. Additional methods outside these protocols can still expose migration gaps, as the legacy RL methods demonstrate.

For completeness, E3 found that DualWriteStore has all V2 method names but its `write_centroid_checkpoint` omits the six quality parameters in the protocol; it lacks L5/Traversal members. Do not treat its runtime shape as full conformance or expand work to repair a backend being retired.

## Signature Defect

E3/E4: the signatures and line numbers still match v4:

```python
# copilot_sdk/graph/protocol.py:597
def count_categories_with_n(self, domain: str, n: int = 1) -> int: ...

# copilot_sdk/graph/memory_store.py:1324
def count_categories_with_n(self, domain: str, n: int) -> int: ...
```

InMemoryGraphStore can be constructed with no arguments. The direct call executed this session produced:

```text
InMemoryGraphStore.count_categories_with_n() missing 1 required positional argument: 'n'
```

DECISION: prompt P1 adds `= 1` and an omitted-argument call test through the L5 contract, with populated category data and an explicit threshold comparison. Do not count an isinstance-only assertion as proof. This design pass leaves the defect unchanged.

## Design Decisions

| Decision | Final resolution | Evidence and execution consequence |
| --- | --- | --- |
| DD-1 | L5LearningStore stays separate | E3 confirms intentional independent declaration. Fix memory default; do not merge protocols. |
| DD-2 | Keep PersistenceOutbox and its raw sqlite3 | E7/E9 confirm independent local artifact queue and explicit outcome rejection. One-file exception for the scoring SQLite gate. Preserve retry, restart, ordering and locking behavior. |
| DD-3 | Delete DualWriteStore and DurableOutbox after their consumers | E5/E6 confirm dependencies. DD-8 retires the independent outcome service; pending records require reconciliation before deployment. No replacement dual-write wrapper. |
| DD-4 | Factory/config support only memory and AGE | E7 confirms scope includes GraphConfig, three app status modules, callers and tests. Invalid retired values fail explicitly; never silently map SQLite to memory. |
| DD-5 | Remove health's SQLite/dual branches | E7 confirms imports/checks. Keep AGE/memory/unknown, owner unwrapping, domain connection checks and AGE-only production readiness. |
| DD-6 | Keep separate scoring extension and current governance bridge | E3/E7 confirm four native AGE methods absent. No required GraphStore additions. Native transactional scoring upserts are a separately owned future change, not hidden migration scope. |
| DD-7 | Partition tests by behavior | E6/E8/E9: disposable portable cases use memory; durable restart/worker behavior uses real AGE; SQLite implementation-only tests retire; legacy input fixtures use the isolated source reader. Preserve portable assertions in mixed files. |
| DD-8 | **Option C: retire ProtocolV2OutcomeService** | E5/E6 show no production invocation in the inspected repos; only definition/export and four dedicated tests. Retain existing direct canonical outcome writes and fail-closed behavior. Publish removal notice and reconcile any deployed pending rows before release. |

DD-8 rejects Option A because it reverses the explicit outcome fail-closed contract and broadens the surviving outbox's purpose. Option B would add a second outcome orchestration/retry path without an observed production caller; the current scorer already owns direct writes. Retries after an ambiguous commit require canonical readback/conflict handling, not blind local retry or a successful pending acknowledgement. Appendix B records the complete consumer inventory and lost behavior.

Additional scope decisions, now closed:

- **Legacy data import:** keep offline source import/reconciliation available; replace SQLiteGraphStore dependence with a minimal read-only SQL source reader. Preserve source DB files and backups. Database selection and contents are deployment inputs, not guessed by a factory.
- **Bundle fidelity:** preserve every populated section and its reader-visible meaning. Replace SQLite-specific restore with protocol writes plus per-section completion reporting; unsupported or invalid state fails explicitly. Existing AGE decision-only behavior is not accepted as equivalent. Use deterministic import identities, resumable/idempotent writes and a durable completion marker written only after successful readback; a decision-count threshold alone must not hide a partial restore.
- **Checkpoint import:** preserve original creation/checkpoint/decision-window times, counts, metadata, category and lineage. Update AGE persistence/read filters through the existing `save_centroids(..., **kwargs)` / `get_centroid_checkpoints(..., **kwargs)` contract; keep public protocol and adapter signatures stable. Validate reader-visible temporal behavior, not merely archival metadata retention.
- **RL bundle state:** migrate ConservationBoundedThompson to domain-scoped `save_posterior`/`get_posterior`; pass domain explicitly from `get_rl_components`, and use the same stable key (`thompson_posteriors`) in importer and consumer. Map each other legacy RL key through a documented shared key/schema table; unsupported keys prevent full-restore success. Do not invent unused governance blobs and claim the policy was restored. Preserve deliberate no-store behavior for disposable callers; configured production persistence failures must be visible.
- **Independent sidecars:** keep existing non-GraphStore sidecars in separate scope; no new scoring writes may be routed to them. This is backend retirement, not a claim that all SQLite throughout the repository disappears.

## Reference Inventory

E10 reran both the prompt's exact root/suffix scans and the broad A–J inventory used by v4. A unique occurrence is `(repo, path, line)`; a file is counted once in each relevant scan. Scan totals overlap. Inventory entries are review surfaces, not equal-sized required edits.

### Prompt-requested scan scope

| Search | Scope | Files | Matching lines |
| --- | --- | ---: | ---: |
| SQLiteGraphStore | SDK copilot_sdk/apps/tests/scripts/examples/integrity, Python | 97 | 373 |
| DecisionStore | SDK copilot_sdk/apps/tests/scripts/examples, excluding persistence_outbox matches | 1 | 2 |
| DualWriteStore | SDK copilot_sdk/apps/tests/scripts/examples, Python | 18 | 68 |
| DurableOutbox | Same SDK scope | 5 | 15 |
| import sqlite3 | Same SDK scope, excluding any persistence_outbox path/content | 37 | 38 |
| SQLiteGraphStore | Discovered installed ci_platform package only | 0 | 0 |
| DualWriteStore | Discovered installed ci_platform package only | 0 | 0 |

The two DecisionStore lines are `tests/test_age_unification_invariants.py:59,68`, which check absence/import violations. Actual DecisionStore/scoring.storage imports are **zero**. Do not delete positive enforcement strings to manufacture zero textual hits.

The package-only ci-platform scan excludes its repository-level tests and developer script. The broader repository scan still finds `tests/test_age_graph_store_v.py` (SQLite import plus instantiation) and `prompt0_ci_structural_map.py:4` (unrelated code-review SQLite DB). Thus v4's ci-platform **2 files / 3 lines** remains correct for its original scope.

### Like-for-like v4 inventory

The broad scan covered **1,924** `.py`, `.toml`, `.yaml`, `.json` files across both repositories. Result: **148 files / 637 unique lines**, SDK **146/634**, ci-platform **2/3**. No added, removed or modified source/config files were found against the previous audit's saved per-file SHA-256 manifest. Counts and sizes have not changed; differences above are scope differences.

| Exclusive category | v4 files/lines | Fresh files/lines | Delta |
| --- | ---: | ---: | --- |
| A: direct SQLite imports after specialized ownership assignment | 70 / 303 | 70 / 303 | 0 |
| B: DecisionStore test imports | 0 / 0 | 0 / 0 | 0 |
| C: dual-write | 13 / 124 | 13 / 124 | 0 |
| D: factory/config | 18 / 71 | 18 / 71 | 0 |
| E: health/status | 10 / 58 | 10 / 58 | 0 |
| F: scoring/storage | 4 / 13 | 4 / 13 | 0 |
| G: seed | 2 / 7 | 2 / 7 | 0 |
| H: evolution/learning | 4 / 9 | 4 / 9 | 0 |
| I: other/historical/unmatched | 27 / 52 | 27 / 52 | 0 |
| Total | 148 / 637 | 148 / 637 | 0 |

Assignment priority was reproduced exactly: historical logs → I; DecisionStore test import → B; health/status path → E; scoring path → F; seed path → G; evolution/learning → H; factory/config/backend-only → D; dual-write → C; AST-confirmed SQLite import → A; remainder → I. Every file's matching lines inherit its category. This prevents double counting but makes A smaller than the total import surface. **AST-confirmed SQLite imports: 112 matching source lines in 96 files**, including specialized categories. Broad textual SQLiteGraphStore references: 375 lines in 98 files.

Two `logs/design_drift_*.json` snapshots remain historical evidence. The seed category contains tests, not proof that all factory-using seed scripts are already migrated. Newly inspected indirect RL/AGE checkpoint consumers do not need a literal legacy class name to be migration work; they are additional semantic scope outside the fixed 148-file grep inventory.

The broad scan prunes `.git`, dependency environments, node_modules, caches, build/dist, .codex_tmp, .codex, temporary directories and code-review/graphify-generated trees. The inventory is not a workspace-wide count including dependencies. Markdown, `.env`, shell and `.yml` configuration were not included in the A–J suffix scope; implementation prechecks must audit these deployment surfaces too.

## Work Stream Sequencing

**WS2 protocol verification/fix → WS3 consumer migration → WS1 deletion → WS5 enforcement.** WS4 documentation accompanies the early work. Consumer cleanup and deletion can land atomically, but a deletion-only intermediate state is invalid.

E5 verified the exact import edges claimed by v4:

| Edge | Current location | Consequence |
| --- | --- | --- |
| graph package → SQLiteGraphStore | `graph/__init__.py:12`, export `:27` | Importing surviving graph submodules initializes this package and fails after premature SQLite deletion. |
| graph package → outcome service → DurableOutbox | `graph/__init__.py:14`, service export `:26`, `graph/outcome_service.py:8` | Deleting graph/outbox.py first breaks public package initialization. |
| scorer → DualWriteStore | `scoring/scorer.py:36,184` | Direct import and governed-store special case require coordinated cleanup. |
| filtering wrapper → DualWriteStore | `graph/legacy_signal_filter.py:339,608` | Lazy reader imports fail at use time even if initial imports succeed. |

`migrate/reconcile_archive.py:12` also imports ReadDiffRunner, which imports DualWriteStore. Preserve or retire this dependency deliberately. Protocol verification ran successfully while all legacy modules were present, proving no WS1 prerequisite for WS2. Existing lazy imports and package initialization order must remain safe; this is not a proof that the entire import graph is acyclic.

During P1–P4 keep legacy implementation modules available for remaining consumers, prohibit new dependencies, and migrate each changed factory/config test with its caller. Retire behavior before deleting its implementation. P5 removes modules only after targeted consumer scans and collection gates pass. Promote a strict-xfail gate to an ordinary assertion as soon as its invariant becomes true; do not leave a passing strict-xfail to break an intermediate suite.

## Execution Plan

All prompts use **sol / high**, as requested. These are sequential work packages, not instructions to spawn agents. P2/P3 investigations may overlap, but their changes must respect shared-file ownership. Future implementation is authorized by separate execution prompts, not by this verification pass.

### Common prechecks and completion rules

Before each prompt: read AGENTS.md, this v5, the latest SDK session entry and any affected external repo instructions/session; inspect branch/status and preserve unrelated edits. Re-scan relevant consumers, record source versions and identify required configuration. Discover ci-platform through its import path again. Do not reset dirty trees. Capture target tests before changes and map any deleted case to a retired behavior or a surviving equivalent assertion.

After each prompt: run targeted tests and import/collection checks for touched surfaces; run `python -m mypy <changed_python_file> --config-file pyproject.toml` from the owning repo for every changed Python file, including helpers. Resolve app-local namespaces using their established test setup. Pre-existing external type failures require a recorded baseline and separate disposition; they cannot be advertised as a clean type check. Document actual passes/failures/skips and data limitations in session state. An unavailable live-AGE prerequisite may block a gate but must not become fabricated passing evidence.

| Prompt | Model/reasoning | Engineering-day estimate | Dependencies |
| --- | --- | ---: | --- |
| P1 Contract correction and policy lock | sol/high | 0.25–0.5 | v5 accepted as execution design |
| P2 Runtime backend selection and consumers | sol/high | 0.75–1.25 | P1 |
| P3 Portable fixtures, examples and experiments | sol/high | 0.75–1.25 | P1; integrate after P2 |
| P4 Durable fidelity and outcome-service retirement | sol/high | 2–3.25 | P2/P3 and disposable AGE access |
| P5 Coordinated infrastructure deletion | sol/high | 0.25–0.5 | P4 plus consumer/compatibility gates |
| P6 Enforcement and full acceptance | sol/high | 0.5–0.75 | P5 |
| R1 Integration review | sol/high | 0.25–0.5 | P6 evidence |

### P1 — Contract correction and policy lock

**Read:** `graph/protocol.py`, `memory_store.py`, `scoring_persistence.py`, `scoring/investigation.py`, app-local DataOpsGovernance, AGE adapter, `tests/test_l5_protocol_extension.py`, `tests/graph/test_scoring_persistence.py`, and existing architectural gates.

**Change:** add memory's `n=1`; test omitted and explicit thresholds with actual verified categories. Record DD-8 and rules below in implementation-facing instructions. Keep required protocol membership and AGE adapter unchanged. Change the raw-SQLite scoring gate to an exact `scoring/persistence_outbox.py` exception and enforce it when it passes; do not suppress other raw SQL.

**Prechecks:** rerun the four-file baseline in Appendix A and signature probe; confirm no native AGE scoring methods have appeared since this snapshot.

**Postchecks:** L5 omitted/default/explicit calls agree; scoring bridge state remains domain/tenant isolated; the exception names one file; all affected mypy checks pass.

**Gate:** zero missing methods/call-shape defects on retained required contracts; no broadened runtime protocol; unchanged fail-closed outcome rule. Legacy backend absence gates may remain strict-xfailed until their conditions become true.

### P2 — Runtime backend selection and consumers

**Read/change:** `graph/factory.py`, `config/graph_config.py`, `backend/health_builder.py`, `scoring/scorer.py`, `graph/legacy_signal_filter.py`, `graph/read_diff_runner.py`, three app `graph_status.py` modules, startup/main/CLI callers and their factory/config/health fixtures. Scan `graph_config.toml`, environment templates and launch scripts as well as Python; correct any retired backend configuration found. Remove SQLite/dual selection and obsolete path parameters only with every affected caller updated. Forward memory decision-ID prefixes.

Keep production AGE validation, domain/tenant isolation, authorization, read filtering, pagination and connection error propagation. Preserve unknown-backend reporting. Remove dual-specific imports/dispatch in surviving runtime paths; keep the implementation modules until P5. Convert tests that specifically assert retired selection to explicit rejection tests rather than leaving them to fail later.

**Prechecks:** inventory all factory/config call sites and per-app profile resolution; establish current health/factory test results. Confirm P1 conformance before replacing governed-store dispatch.

**Postchecks:** memory/AGE creation and invalid SQLite/dual rejection; production rejects memory and unavailable/misconfigured AGE; ID prefix propagation; three app health/status suites; wrapper archive/legacy-signal/pagination regression tests; root and isolated app test collection.

**Gate:** only memory/AGE are selectable; no silent persistence substitution; all changed caller/config tests pass. Existing direct legacy constructors scheduled for P3/P4 can remain temporarily, but are individually tracked.

### P3 — Portable fixtures, examples and experiments

**Read/change:** all direct imports in the fresh inventory, including `tests/graph`, scoring/backend/evolution tests, app fixtures, `examples/build_your_own/engine.py`, `examples/jm_reference/run.py`, `apps/regime_experiment/experiment.py`, `apps/s2p_differentiation/engine.py`, and relevant scripts. Inspect each test's assertions before replacing constructors. Include ci-platform's `tests/test_age_graph_store_v.py` parity fixture in its owning repo.

Use memory for disposable state, retaining explicit domain/prefix and independent fixture state. Persistent experiments use AGE or an explicit supported snapshot/import interface. Retire legacy-only diagnostic scripts deliberately; do not leave runnable scripts with dead imports. Split mixed test files by semantics. A filename such as `tests/scoring/test_storage.py` is not evidence that every case is obsolete.

**Prechecks:** assign every remaining reference a portable, durable, retired-backend-only, source-import or historical-evidence disposition. Inventory test node IDs and outcomes before migration.

**Postchecks:** migrated contract/fixture tests, example smoke runs using disposable state, explicit run-isolation checks, app fixture collection and changed-file mypy. Do not regenerate historical reports to make grep empty.

**Gate:** all portable consumers are migrated and green; remaining references belong to a named P4/P5 disposition. No durability assertion has been weakened to a same-process memory round trip.

### P4 — Durable fidelity and outcome-service retirement

**Read:** complete `demo/bundle.py`, `demo/startup.py`, bundle tests and app bundle wiring; `tests/test_worker_process_safety.py`; archive/reconciliation/import modules/tests; `rl/exploration.py`, `rl/presets.py`, `tests/rl/test_rl_persistence.py`; AGE checkpoint write/read methods; complete outcome service and its dedicated four-test module; active scorer outcome flow, scoring router and PersistenceOutbox tests.

**Change, bundle/import:** implement the resolved section-by-section restore contract. Decisions retain IDs/category/action/vector/provenance; outcomes retain correctness/action/time and canonical duplicate/conflict behavior. Checkpoints retain tensor, counts, metadata, timestamps/windows and lineage with readback through normal readers. RL state uses the same domain-scoped posterior keys as the migrated policy. Evolution events retain IDs or deterministic import identities, metadata and historical ordering. Importer and consumers must agree on schemas. Unsupported input fails visibly before claiming completion. Verify all populated sections, partial failure/resume and repeated/concurrent import; do not use a decision-count shortcut as a completion signal.

**Change, AGE/RL:** implement checkpoint historical-field persistence and filters in `ci_platform/graph/age_graph_store.py` through existing kwargs; retain SDK protocol/adapter forwarding unless a demonstrated compatible bug requires a documented change. Migrate Thompson persistence to existing GraphStore posterior methods with explicit domain. Add actual reopen/readback tests. Do not add optional methods to required GraphStore simply to make isinstance pass.

**Change, DD-8:** remove all callers/exports of the retired service; transfer useful commit/V/failure/conflict assertions to scorer/router/GraphStore tests, and retire its queued-outcome tests explicitly. The module can remain unexported until the coordinated P5 deletion. No replacement queue or automatic outcome retry loop. Publish the public API removal notice and migration path to CompoundingScorer/GraphStore.

**Change, durable tests/tools:** move shared graph target state in worker tests to disposable AGE; keep PersistenceOutbox's local SQLite file and multiprocessing/file-lock tests. Retire SQLite WAL/integrity assertions with the backend but preserve the two-worker write, single-drain and single-restore invariants. Keep atomic JSON/file-lock tests unchanged unless a real failure requires repair. Retain offline source reading and archive reconciliation through the minimal read-only reader. Do not treat the existing sqlite_to_age importer as a full learned-state importer: its module explicitly says L5/DK/conservation state is re-derived.

**Prechecks:** require a disposable, authorized AGE graph and a clear test domain; never use a production graph for write tests. Capture source bundle/DB schemas and expected semantic readbacks. Identify deployed pending/failed secondary_outbox records without deleting them. External consumers, database locations and data volume are UNVERIFIED until deployment inventory supplies them.

**Postchecks:** live AGE restart/multiprocess tests; per-section bundle round trip and temporal filtering; posterior reload through the real policy; resume/idempotency and domain/tenant isolation; canonical-write failure returns an error with no queued outcome/no premature V advance; caller retry after ambiguous success reconciles the canonical record; duplicate/conflict behavior remains explicit. Run SDK and external changed-file mypy and targeted suites.

**Gate:** B-1 is removed as a consumer dependency; B-3/B-4 behavioral equivalents pass on retained stores. For code retirement, publish the compatibility/runbook evidence. For deployment, reconcile all pending/failed rows or keep the previous release serving them until resolved; do not purge queues or equate quarantine with successful delivery. Historical K/holdout imports must have identified sources and reconciliation if that data is deployed. Native AGE scoring upserts remain a separately tracked follow-up.

### P5 — Coordinated infrastructure deletion

**Read:** the remaining reference inventory, package exports, collection results and P4 gate evidence. Re-scan both SDK and external repo, including dynamic imports/module strings and alias imports.

**Change:** delete `graph/sqlite_store.py`, `graph/dual_write_store.py`, `graph/outbox.py`, and `graph/outcome_service.py`; remove remaining exports/imports and obsolete backend-only tests/scripts. Remove ReplayReport consumers if any are found. Delete the service-only test module only after its retained invariants have active-path coverage. Do not delete PersistenceOutbox, process locks, independent sidecars, legacy source data or source-import fixtures.

**Prechecks:** every executable reference outside files being deleted is resolved; no retained script/test needs a deleted symbol; portable and durable gates passed. External API removal is documented. No new DecisionStore shim or SQLite-backed GraphStore substitute is introduced.

**Postchecks:** import SDK graph/scorer/factory/health and the AGE adapter in clean processes; collect root, each app and external tests; run surviving focused contract suites; promote newly satisfied absence/import gates immediately.

**Gate:** the four modules are absent, imports/exports are gone from executable consumers, and collection succeeds. Historical documentation and enforcement-pattern strings are not false-positive failures.

### P6 — Enforcement and full acceptance

**Read/change:** `tests/test_age_unification_invariants.py`, configuration tests, contract tests and CI invocations. Enforce DecisionStore/SQLiteGraphStore absence and import gates; add equivalent dual/outcome-service/DurableOutbox removal checks. Use AST-based import detection covering aliases and imported modules, plus explicit dynamic-import checks for the deleted paths. Restrict the raw-SQLite scoring exception to PersistenceOutbox. Cover only-memory/AGE factory values, production readiness, both retained protocol surfaces and L5 default-call behavior.

**Prechecks:** P5 imports/collection pass and live AGE is available for required acceptance lanes. Record retained/retired test mapping so changing test totals are explainable.

**Postchecks:** full SDK `python -m pytest tests/ -q --timeout=120`; isolated Trading/Purchasing/DataOps backend suites; full ci-platform tests from its repo; disposable live-AGE durability/consumer suites; mypy for every changed Python file in its owning repo. Record passed/failed/skipped/xfail counts and the reason for every unavailable prerequisite. Run outage-mode resilience separately from live-AGE acceptance.

**Gate:** zero failures, no strict-xfail left masking a completed migration invariant, and no skipped required durability/cutover test counted as passed. Remaining unrelated baseline issues must be explicitly resolved or prevent an unconditional completion claim. Review actual diffs for unintended sidecar/data deletion.

### R1 — Integration review

**Read:** final source diff in both repos, test deletion/retention ledger, cutover runbook, semantic bundle/readback results, enforcement code and actual acceptance logs. Re-run focused protocol/import/gate tests against the reviewed revision.

**Verify:** only two selectable GraphStore backends; no production memory fallback; canonical outcomes remain fail-closed; no new queued-outcome path; exact one-file scoring exception; independently durable artifact recovery; preserved bundle/temporal/RL semantics; public API removal and offline source import scope; no inflated counts or inherited historical test results.

**Gate:** no unresolved correctness/coverage issue affecting retirement, source revision matches evidence, and deployment prerequisites are explicitly satisfied before declaring the data cutover complete. Append final results and next steps; do not claim deployed-data migration from a source-only review.

## Blockers

| Blocker | Verified current state | Resolution status and owner |
| --- | --- | --- |
| B-1 outcome-service dependency | DurableOutbox import still exists at outcome_service.py:8; service is publicly exported | **Design resolved by DD-8 Option C.** Still a current import dependency; P4 retires consumer behavior/export, P5 deletes modules. External API usage/queued data are release gates. |
| B-2 package import ordering | All four v4 chains still exist at the claimed lines | **Resolved by sequencing.** Migrate imports/exports before or atomically with deletion; P5 import/collection checks enforce it. |
| B-3 bundle fidelity | SQL branch exists; AGE branch only restores decisions; legacy RL and checkpoint historical behavior differ | **Implementation blocker with a fixed mitigation.** P4 must implement per-section protocol restore, posterior reader migration, AGE historical checkpoint preservation/filtering, truthful reports and live readback. No silent omission accepted. |
| B-4 worker durability | Six tests in worker file; three graph-related cases share persistent state between spawned processes | **Implementation blocker with a fixed mitigation.** P4 uses live AGE for graph targets, keeps local outbox/locking/atomic-JSON tests, retires only SQLite-specific assertions. |

No DD remains open. Operational facts still UNVERIFIED: external package users, deployed secondary-outbox contents, historical data locations/volume, live AGE accessibility and performance. These facts have explicit release/acceptance gates above; they do not change the selected architecture.

Independent SQLite sidecars were rechecked and remain separate scope:

| File | Verified role | Decision |
| --- | --- | --- |
| `backend/signal_store.py:24` | SQLiteSignalStore | Retain existing sidecar scope; do not convert it into scoring persistence. |
| `evolution/variant_store.py:191` | SQLiteVariantStore alongside memory variant store | Separate lifecycle from GraphStore removal; production scoring/evolution changes must use graph-backed interfaces. |
| `outcome/ledger.py:14` | OutcomeLedger | Not DurableOutbox or DecisionStore; graph-backed alternative exists in evolution/graph_store.py. |
| `promotion/core.py:111` | PromotionStore | Independent promotion persistence; not a selectable GraphStore. |
| `pilot/transfer.py:46` | MeasuredTransferStore | Pilot sessions/observations, separate from backend deletion. |
| `outbox/store.py:15` | OutboxStore event queue | Third distinct outbox abstraction; not the graph DurableOutbox being removed. |

These are source-role findings, not proof that every deployment disables every sidecar. Preserve existing data and apply the no-new-scoring-SQL rule; a repository-wide SQLite elimination would require a different design.

## Effort Estimate

The work-package estimates sum to **4.75–8 engineering days**, rounded to **5–8 days**, assuming disposable AGE access and responsive cross-repository coordination. DD-8 retirement reduces the need for a new outcome queue, but verified bundle/RL/checkpoint work adds scope beyond v4's constructor/import migration.

This is a judgment-based planning range; no engineering-day or credit consumption was measured by the scan. Six implementation prompts plus one review is a decomposition, not a promise of seven uninterrupted model turns. Deployed-data migration duration, external release scheduling and separately deferred native AGE transactional scoring upserts are excluded and depend on operational inputs. There is no verified credit estimate.

## Verification Ladder (post-migration)

1. **Structure:** required files absent; DecisionStore absent; no executable imports/module loading/re-exports of retired APIs; factory/config allow only memory and AGE. Preserve deliberate gate strings and historical reports.
2. **Contracts:** all five protocol inventories remain explicit; memory omitted/default threshold works; AGE covers its four supported protocols; scoring bridge performs domain/tenant-safe round trips. Static signatures and runtime isinstance are supplementary, not behavioral proof.
3. **Portable behavior:** memory-based scorer, filtering, domain/tenant, centroid, evolution, IDs, examples and disposable fixtures pass. No same-process replacement masquerades as restart coverage.
4. **Fail-closed outcomes:** canonical failure surfaces through scorer/HTTP error handling; no queued outcome or pending-success response; no speculative centroid/V success; duplicates/conflicts and ambiguous commit retries reconcile against canonical state. Derived artifacts may use PersistenceOutbox under its existing contract.
5. **Fidelity:** every populated bundle section is read back by its real consumer; identities, outcomes, original times/windows, checkpoints, RL priors and event order are preserved; incomplete imports are reported incomplete and resumable; repeat/concurrent restore does not duplicate state.
6. **Durability:** disposable live AGE across spawned workers and reopened connections; local PersistenceOutbox survives restart and concurrent drains; startup coordination and atomic JSON still work. Outage and live lanes are recorded separately.
7. **Integration:** full SDK, isolated app and external suites; changed-file mypy; no migration invariant hidden behind xfail and no required live test skipped as success. Explain test removals by retired behavior, not merely reduced totals.
8. **Release/data:** public API removal communicated, known external users checked, pending/failed legacy queues reconciled, historical deployed K/holdout data reconciled, backups retained, source revision matched to validation. Source acceptance alone does not pass this rung.

## Post-Migration Architecture

- CompoundingScorer and application consumers use GraphStore and explicit optional capability protocols.
- The factory selects InMemoryGraphStore for disposable test/dev state or AGEGraphStoreAdapter for persistent/production state. Filtering and tenant wrappers remain; AGEGraphStore implements the underlying AGE persistence.
- L5, traversal and scoring extensions retain their current separation. GraphScoringPersistence continues to support current AGE through governance methods; native AGE scoring upserts remain separate work.
- Canonical outcomes go directly through the scorer/graph path. ProtocolV2OutcomeService, accepted-pending-sync outcomes, DualWriteStore and graph DurableOutbox no longer exist.
- PersistenceOutbox remains a local SQLite artifact recovery buffer and replays supported artifacts to the selected graph. It never becomes an outcome acceptance queue or selectable graph backend.
- Bundle/source import maps historical records into retained protocol state with verifiable completion. An offline read-only SQLite source reader is tooling, not a third GraphStore backend.
- Existing independent sidecars are explicitly outside this backend-removal change; new scoring persistence must not use them.

## Standing Rules

E11 scanned numbered rule references throughout `docs/session_state.md`; the highest existing number at task start was **Rule #85** (including lines 4005, 4026 and 4287). There was no higher numbered Rule reference. Allocate the next numbers **86–92** here; record this allocation in the final session append so subsequent work does not reuse them. These are policy decisions for the migration, not claims that the current code already satisfies all of them.

- **Rule #86 — No DecisionStore revival.** DecisionStore is deprecated and absent. No new dependency, compatibility shim or replacement `scoring/storage.py` may revive it. All new scoring persistence uses GraphStore methods or explicit graph-backed extensions.
- **Rule #87 — Two GraphStore backends.** Target supported selection is memory and AGE only; memory is disposable test/dev, AGE is persistent/production. Never silently downgrade an AGE or retired-backend request to memory.
- **Rule #88 — Retire dual-write infrastructure coherently.** No new DualWriteStore/DurableOutbox consumers. Remove consumer imports/exports before or atomically with deleting the graph modules; never drop unresolved queue data as a code-cleanup step.
- **Rule #89 — Bounded scoring SQLite exception.** Only `copilot_sdk/scoring/persistence_outbox.py` is excepted from the no-raw-SQLite-in-scoring gate. Keep its durable artifact recovery and its prohibition on queued outcomes. This is not a repository-wide sidecar exemption for new scoring code.
- **Rule #90 — DD-8 outcome ownership.** Retire ProtocolV2OutcomeService and its public pending-sync behavior. Canonical outcome failures remain visible; no successful pending acknowledgement or automatic blind retry. Reconcile ambiguous commits and existing queued records before retry/cutover.
- **Rule #91 — Preserve contracts and durable semantics.** Keep optional protocols separate and stage required membership with AGE. Tests must verify valid call shapes and real consumer readback; memory cannot substitute for a restart/process durability contract. Bundle completion requires all populated sections, not decision count alone.
- **Rule #92 — Separate source retirement from data cutover.** Offline legacy readers may read existing SQLite sources but may not become GraphStore backends. Retain backups, reconcile historical state and pending records, document external API retirement, and report unverified deployment facts explicitly.

## Appendix A: Verification Evidence

All evidence below was gathered during this v5 session; earlier reports supplied comparison data only.

| ID | Verification run | Actual result |
| --- | --- | --- |
| E1 | Byte-size/existence inspection of all nine paths; extra service/storage checks | Nine files present, all byte counts match v4; outcome_service.py 6199 bytes; storage.py absent. |
| E2 | ci_platform import-path discovery and source access | Resolves to sibling ci-platform/ci_platform; adapter/backend accessible. |
| E3 | AST protocol declarations plus callable/signature binding inspection | Five protocols at 16/40/281/307/531; counts 4/45/3/22/7; V2 effective 66; one memory L5 binding gap; four native scoring methods absent from AGE. |
| E4 | Source signature comparison and actual no-argument construction/omitted-n call | TypeError reproduced; mismatch still exists. |
| E5 | Fresh symbol scans and claimed import-chain reads | All four claimed chains and line numbers confirmed; complete DD-8 matches listed in Appendix B. |
| E6 | Full outcome-service, dedicated test and worker-process file reads | Service queues write_outcome on specified availability exceptions; four dedicated tests; six worker tests, including three graph-durability cases. |
| E7 | Factory/GraphConfig/health/scorer/router/bridge/outbox/sidecar source reads | Current backend choices, fail-closed write path, exact SQLite exception and independent sidecar roles confirmed. |
| E8 | Full bundle restore branches; RL persistence/wiring; AGE checkpoint saver/reader; in-memory control-flow probe | AGE branch restores one decision, leaves checkpoint count zero and RL state absent; both AGE classes lack legacy RL methods but have posterior methods; checkpoint saver uses current time and reader only consumes limit/include_v2 of the examined kwargs. |
| E9 | Existing four-file pytest baseline | **52 passed, 0 failed, 0 skipped**, 104 dependency deprecation warnings, **3.93s** reported test time. |
| E10 | Fresh requested scans and broad A–J scan; SHA-256 comparison with prior saved manifest | Requested counts and broad/category counts above; 1924 files; no source/config additions/removals/modifications versus previous manifest. |
| E11 | Numbered Rule scan of full SDK session state | Highest reference 85; allocate 86–92. |

### Executed test baseline

All four files existed at the requested paths; no fallback file search was necessary:

```text
tests/test_l5_protocol_extension.py                 5809 bytes
tests/graph/test_protocol.py                       5345 bytes
tests/graph/test_protocol_v2_service_layer.py       5584 bytes
tests/scoring/test_persistence_outbox.py           18493 bytes

python -m pytest tests/test_l5_protocol_extension.py tests/graph/test_protocol.py tests/graph/test_protocol_v2_service_layer.py tests/scoring/test_persistence_outbox.py -q --timeout=120

52 passed, 104 warnings in 3.93s
```

Warnings are pytest_freezegun/distutils deprecations. This test run is new evidence even though its pass count matches the previous pass. The L5 negative probe still failed as expected, demonstrating that these existing tests do not exercise the omitted implementation default.

No full suite or live AGE test was run in this design-only pass. No helper script files were created: inspection code ran via `python -c` / Python stdin. Consequently changed-helper-file mypy is **not applicable**, not a claimed mypy success. Future saved helpers and modified Python files must be type-checked under their owning pyproject.

### Broad A–J scan counts

| Scan | Pattern/scope | Files | Lines |
| --- | --- | ---: | ---: |
| A | SQLiteGraphStore, Python | 98 | 375 |
| B | DecisionStore, Python | 1 | 2 |
| C | DualWriteStore, Python | 18 | 68 |
| D | DurableOutbox, Python | 5 | 15 |
| E | SQLite graph from-import patterns | 95 | 112 |
| F | dual_write_store from-import | 15 | 17 |
| G | graph.outbox from-import | 4 | 4 |
| H | backend.*sqlite, Python/TOML/YAML/JSON | 35 | 138 |
| I | scoring.storage from-import | 0 | 0 |
| J | import sqlite3, excluding only scoring/persistence_outbox.py | 39 | 40 |

Broad J differs from the prompt's 38-line SDK scan because the latter also excludes the test filename containing persistence_outbox and does not include the external structural-map script. Broad SQLite counts include the external test; package-only external scans do not. AST import detection additionally catches a multiline import missed by the textual from-import file pattern. These are counting-method differences, not newly migrated consumers.

The broad manifest SHA-256, computed from the sorted path-to-file-hash mapping in this session, is:

```text
4c2307c3c70e8ecbd0109e68ef5193417628beb3cbc8653fbf0546c6767548ec
```

This digest covers the 1,924 source/config inventory files, not Markdown or databases. The detailed previous line inventory in `docs/dstore_migrate2_design_corrections.md` remains valid because every inventoried file hash was freshly compared and unchanged. The new requested-scope counts, decisions and semantic findings are recorded here rather than copying 637 lines again.

A second hash pass after writing v5, at 2026-10-03T00:34:23-07:00, reproduced the same file count and digest. Document validation confirmed all 15 requested sections, six implementation packages plus review, rules 86–92, balanced code fences and no trailing whitespace. No saved Python helper was introduced.

### Bundle and protocol verification limits

The bundle probe used InMemoryGraphStore with `backend='age'` solely to exercise the existing AGE-selection branch in `_restore`; it did not impersonate a real database validation. A bundle with a valid decision, checkpoint, RL state and evolution section returned `{'restored_count': 1, 'skipped_count': 0}`, with zero checkpoint records and no legacy RL state. Source inspection of `restore_bundle_if_empty:62–83` shows how that result can set fully_restored without checking the omitted sections. This establishes a control-flow/reporting gap; live AGE restore behavior remains an implementation acceptance requirement.

AGE `age_graph_store.py:3336` save_centroids uses current `time.time()` for created_at, and `:3557` get_centroid_checkpoints consumes limit/include_v2 without applying the other historical filter kwargs inspected. The v5 checkpoint plan therefore requires actual backend read/write work, not merely passing arguments that are currently ignored.

## Appendix B: DD-8 Analysis

### Complete current consumer inventory

The fresh search for `ProtocolV2OutcomeService|outcome_service` across SDK Python and the accessible ci-platform repository produced exactly five matching lines in three files:

| File/line | Actual use | Classification |
| --- | --- | --- |
| `copilot_sdk/graph/outcome_service.py:20` | class ProtocolV2OutcomeService | Definition |
| `copilot_sdk/graph/__init__.py:14` | from copilot_sdk.graph.outcome_service import ProtocolV2OutcomeService | Public re-export |
| `copilot_sdk/graph/__init__.py:26` | __all__ entry | Public export declaration |
| `tests/graph/test_protocol_v2_service_layer.py:5` | imports service and SQLiteGraphStore from graph package | Dedicated test import |
| `tests/graph/test_protocol_v2_service_layer.py:49` | constructs service in _service fixture | Only observed instantiation |

No invocation was found in apps, production scorer/router paths, scripts, examples or ci-platform source/tests. Symbol scanning cannot establish absence of unknown external users or arbitrary dynamic imports; those are explicitly UNVERIFIED. Public export makes retirement an API change even without an in-repo production caller.

### Current behavior and what retirement removes

The service accepts a canonical writer (default store.write_outcome), computes verified counts before/after, and updates conservation snapshot and L5 state after a newly verified outcome. `learn()` catches ConnectionError/OSError/RuntimeError, appends a `write_outcome` payload to DurableOutbox and returns `accepted_pending_sync`, `canonical_committed=False`, decision_id, current V and outbox_id. `set_canonical_writer()` switches the recovered writer; `replay()` uses an interprocess lock, retries pending rows, and reports replayed/failed/remaining/V. Replay failures remain inspectable and can be explicitly quarantined through the outbox.

Retirement removes that constructor, public import, pending-success response shape, local durable outcome admission, service replay/writer-switch API, replay counters and this service's conservation orchestration. It does not remove the active scorer's canonical outcome writes or PersistenceOutbox's derived-artifact recovery. Existing records in secondary_outbox do not disappear merely because the Python class is removed and must not be silently discarded.

The dedicated module contains four tests:

1. `test_api_learn_committed`: successful canonical commit and V increment; move equivalent assertions to the active outcome path before removing the service-only case.
2. `test_api_learn_pending_sync`: retired acceptance behavior; replace with active-path failure visibility/no queued outcome assertions.
3. `test_pending_sync_no_V_increment`: pending response itself retires; preserve no premature learning/V advance on canonical failure in active-path tests.
4. `test_replay_then_V_increments`: retired queue replay and quarantine APIs; retain canonical duplicate/conflict and correct V invariants where those behaviors remain relevant.

### Why Option C is selected

E7 inspected `CompoundingScorer.learn/_learn_impl` (`scorer.py:996,1133–1170`): it calls the atomic outcome/centroid writer when available, otherwise write_outcome and production centroid persistence. If that durable write path fails it restores speculative centroids and re-raises. This is source evidence of the canonical failure path, not a proof that all multi-write transactions are atomic.

The shared `/learn` route calls scorer.learn at `backend/scoring_router.py:291`; graph connection errors at `:303` become `graph_unavailable`, which returns HTTP 503 (`backend/graph_access.py:35`). Successful conservation-gate handling remains separate. `PersistenceOutbox.enqueue` at `scoring/persistence_outbox.py:214–215` rejects `outcome`, and its existing tests verify that rule. The selected retirement preserves this ownership and failure policy.

Option A would change that policy to accept deferred canonical outcomes and requires more than adding a replay branch. Option B would add an unneeded service/retry layer and raises duplicate/ambiguous-commit questions already belonging at the canonical boundary. Option C removes unused orchestration while retaining the observed production route. No claim is made that a published API can be removed without communicating the change.

### Compatibility and deployed-data disposition

P4 documents the removed API and directs callers to the canonical scorer/GraphStore outcome API. Before deploying P5, inventory known external imports and pending/failed secondary_outbox rows. Complete or reconcile writes with the previous release, compare canonical outcomes by identity, and preserve conflict evidence/backups. If any consumer or unresolved row is found, pause that deployment until migration/reconciliation finishes; do not change DD-8 to a new hidden queue or silently delete data. Actual external dependency and queue inventories are UNVERIFIED in this source-only session.

Design disposition: **all DDs resolved; implementation ready in the gated sequence above.** Code and data migration remain future work, with B-3/B-4 and release prerequisites explicitly tracked.
