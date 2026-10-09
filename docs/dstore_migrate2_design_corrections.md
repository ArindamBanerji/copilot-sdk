# DSTORE-MIGRATE-2 design corrections

Verified: 2026-10-02T23:41:14-07:00. Both repositories are on `main`. This is a design-verification pass, not a backend-removal implementation. Existing dirty source trees were preserved. Nine named files were verified; all exist. Source inventory covers 1924 Python/TOML/YAML/JSON files across both repositories.

**Result: corrections needed.** The delete-first order is unsafe; DurableOutbox has a second public-service consumer; the memory backend has no missing methods but one L5 signature defect; the reference estimates are stale. The implementation plan below supersedes the claims supplied in the prompt.

Session context: SDK's latest `DSTORE-MIGRATE-REVIEW-FIX` records the earlier migration, 105 file-level follow-ups, 3981 passed / 0 failed / 260 skipped / 3 xfailed under an AGE-outage configuration. Its earlier AGE-RUNTIME-FIX and AGE-RUNTIME-DIAGNOSTIC-2 entries are historical baselines, not new results. ci-platform's latest AGE pagination implementation/review records 661 ci-platform tests and 4200 SDK tests passing under that earlier environment. Those totals must not be combined or presented as this pass's results.

Current verification: **52 passed / 0 failed / 0 skipped** for the four focused test files listed in Section 8. Runtime method-presence and signature-binding probes also ran. A direct one-argument memory L5 count call reproduced a TypeError. No live AGE database, full-suite rerun, or production data cutover was performed.

## SECTION 1: FILE VERIFICATION RESULTS

Sizes below are bytes on disk, not rounded KB. Paths are workspace-relative.

| File | Exists | Bytes | Verification |
| --- | --- | --- | --- |
| copilot-sdk/copilot_sdk/graph/sqlite_store.py | EXISTS | 167948 | AMENDED: 167,948 bytes, about 164 KiB, not ~40 KB. Concrete SQLite backend; deletion must follow consumer migration. |
| copilot-sdk/copilot_sdk/graph/dual_write_store.py | EXISTS | 36248 | AMENDED: generic GraphStore primary/secondary wrapper, not intrinsically SQLite+AGE. Factory chooses that pairing. Also defines ReplayReport. |
| copilot-sdk/copilot_sdk/graph/outbox.py | EXISTS | 5906 | AMENDED: 5,906 bytes, not ~8 KB. DurableOutbox serves both DualWriteStore and ProtocolV2OutcomeService. |
| copilot-sdk/copilot_sdk/graph/factory.py | EXISTS | 11099 | AMENDED: four claimed backends confirmed. SQLite import is module-level; DualWriteStore import is lazy inside its branch. |
| copilot-sdk/copilot_sdk/graph/protocol.py | EXISTS | 17242 | AMENDED: five runtime-checkable protocols, not three; exact counts and overlap in Section 3. |
| copilot-sdk/copilot_sdk/graph/memory_store.py | EXISTS | 99463 | AMENDED: all named protocol methods exist; one L5 default-argument mismatch. Implements both omitted extension protocols too. |
| copilot-sdk/copilot_sdk/backend/health_builder.py | EXISTS | 5715 | CONFIRMED with import nuance: SQLite/memory module imports, dual/AGE lazy imports; wrapper unwrapping precedes classification. |
| copilot-sdk/copilot_sdk/scoring/persistence_outbox.py | EXISTS | 17425 | CONFIRMED: independent raw-SQLite failure buffer; keep. Outcome deferral is explicitly forbidden. |
| ci-platform/ci_platform/graph/age_sdk_adapter.py | EXISTS | 26007 | CONFIRMED for the three named protocols at method/signature level. Does not natively implement ScoringPersistenceStore. |

No named path is missing. Separately, `copilot-sdk/copilot_sdk/scoring/storage.py` is already absent; there is no DecisionStore implementation left to delete. AGEGraphStore's implementation is in `ci-platform/ci_platform/graph/age_graph_store.py`, while `age_client.py` is the lower-level client. AGEGraphStoreAdapter is a standalone adapter, not a SQLite subclass. No SQLiteGraphStore subclass was found in the searched source trees.

### Factory and health behavior

`copilot_sdk/graph/factory.py:20` contains `_VALID_BACKENDS = {"sqlite", "memory", "age", "dual_write"}`. Line 15 imports SQLiteGraphStore; line 241 imports DualWriteStore inside the dual-write branch. GraphConfig is loaded/validated before construction. Results are wrapped with LegacySignalFilteringGraphStore, then optionally TenantScopedGraphStore.

- Memory (`:173`): constructs `InMemoryGraphStore(domain=selected_domain)`; the current branch does not forward the selected decision-ID prefix.
- SQLite (`:178`): chooses explicit `db_path`, otherwise `CI_DATA_DIR/<domain>.db`, otherwise `:memory:`; constructs SQLiteGraphStore with domain/prefix.
- Dual write (`:198`): constructs a SQLite primary and AGE adapter secondary, validates AGE configuration, and creates `<domain>_dual_write_outbox.db` beside the resolved SQLite path.
- AGE (`:264` onward): requires explicit nonblank domain/DSN, validates graph authorization, constructs the AGE adapter, attaches configuration/domain, wraps it, and validates production capabilities. It closes the adapter on production-validation failure.

Only memory+AGE makes sense for the intended architecture, but factory-only editing is insufficient. `config/graph_config.py:19,303,305,314` contains the backend type, allowlists and dual-write DSN logic. Three app graph-status modules still default/validate against SQLite and can reject memory. Preserve AGE authorization, domain checks, wrappers and production capability validation. Forward the prefix when moving development creation to memory.

`backend/health_builder.py:18` unwraps declared GraphStoreWrapper ownership and `_graph_store`, with cycle detection. `_backend()` at line 34 checks SQLite, memory, then lazily imports/checks DualWriteStore and recursively classifies its primary. Finally it lazily imports AGEGraphStoreAdapter and AGEGraphStore; unsupported/import-unavailable cases are `unknown`. Remove the SQLite/dual branches and imports; retain memory/AGE/unknown and unwrapping. Existing readiness requires a connected AGE backend on `soc_graph` (`:80`); reducing backend options must not silently relax that rule.

### PersistenceOutbox carve-out and exact replay mapping

`scoring/persistence_outbox.py:8,132` imports/calls sqlite3 directly. Default path is `~/.ci-platform/{domain}/outbox.db`, overridable by constructor/CI_PERSISTENCE_OUTBOX_PATH, with a temporary-directory fallback on parent-directory PermissionError. It stores failed/deferred artifact payloads, retry/status/schema information and idempotency keys. Its methods include record_failure, enqueue, drain, _replay, periodic draining and abandoned-record export. No DecisionStore or SQLiteGraphStore reference exists in this file.

This is a sound bounded carve-out: its local durable buffer must remain usable when AGE is unavailable, and it is not a selectable GraphStore backend. Do not broaden the exception to every SQLite module. The existing strict-xfail raw-SQLite-in-scoring gate must become an enforced gate with exactly this documented file exception.

| Artifact type | Actual _replay action |
| --- | --- |
| conservation | write_conservation_status(**payload) |
| l5_conservation | update_conservation_state(**payload) |
| l5_centroid | update_centroid(**payload) |
| dk_weights | update_dk_weights(**payload), under optional _persistence_outbox_dk_lock |
| fingerprint | write_fingerprint(**payload) |
| evidence_receipt | append_evidence_receipt(**payload) |
| centroid_checkpoint | write_centroid_checkpoint(**payload) |
| decision | write_governed_decision when _governed is true; otherwise write_decision after preserving decision_id in metadata |
| evolution | write_evolution_event if available; otherwise remove event_id and call save_evolution_event |
| anything else | ValueError; enqueue separately rejects outcome as fail-closed |

`graph/outbox.py` is not this buffer. ProtocolV2OutcomeService currently queues `write_outcome` through DurableOutbox. PersistenceOutbox neither replays that artifact nor permits `enqueue("outcome", ...)`. A blind substitution loses outcome/replay semantics.

## SECTION 2: ACTUAL REFERENCE COUNTS

**Counting rule:** an inventory entry is one matching file; an occurrence is one unique `(repository, path, line)` across scans A–J. Overlapping scan matches are deduplicated. Every occurrence appears verbatim in Appendix B, with scan IDs and an assigned design category. These are review entries, not a claim that every file needs modification.

The old 105 was a prior SDK-only follow-up table with five additional cross-cutting issues; it was not a deduplicated two-repository grep count. The supplied eight category ranges do not define a unique partition. Therefore there is no defensible unqualified “105 vs N tasks” comparison. Use the reproducible inventory below for implementation triage; retain cross-cutting semantic work separately.

Actual inventory: **148 files / 637 unique lines** (43 more file-review entries than 105, with different scope). SDK: 146 files / 634 lines. ci-platform: 2 files / 3 lines.

| Category | Design claimed files | Actual files | Unique lines | Delta vs claimed range | Notable entries |
| --- | --- | --- | --- | --- | --- |
| A: Direct SQLiteGraphStore imports | 15–20 | 70 | 303 | +50 to +55 | test_age_graph_store_v.py, conftest.py, test_bundle_wiring.py, test_dataops_backend.py |
| B: DecisionStore test imports | 25–30 | 0 | 0 | -30 to -25 | none |
| C: DualWriteStore references | 5–10 | 13 | 124 | +3 to +8 | dual_write_store.py, legacy_signal_filter.py, read_diff_runner.py, phase3_dual_write_e2e_v4.py |
| D: Factory/config SQLite backend references | 10–15 | 18 | 71 | +3 to +8 | conftest.py, main.py, cli.py, conftest.py |
| E: Health/status | 5–10 | 10 | 58 | +0 to +5 | graph_status.py, test_dataops_graph_status.py, graph_status.py, test_health_outage_contract.py |
| F: Scoring/storage internals and tests | 10–15 | 4 | 13 | -11 to -6 | scorer.py, test_persistence_outbox.py, test_scorer_governed.py, test_storage.py |
| G: Preseed/seed | 5–10 | 2 | 7 | -8 to -3 | test_gate_preseed_initialization.py, test_preseed_gap_supersession.py |
| H: Evolution/learning | 5–10 | 4 | 9 | -6 to -1 | variant_store.py, test_evolution_store.py, test_selection_snapshot.py, test_summary_snapshot.py |
| I: Other / unmatched / historical evidence | not supplied | 27 | 52 | new category | prompt0_ci_structural_map.py, purchasing_control.py, cli_sdk.py, signal_store.py |

Categories are assigned once per file and all its matching lines inherit that category. Priority: historical logs → I; real DecisionStore test import → B; health/status → E; scoring paths → F; seed-named paths → G; evolution/learning → H; factory/config or backend-only hits → D; dual-write → C; an AST-confirmed SQLiteGraphStore import → A; remainder → I. Thus the table sums without overlap. This is an explicit operational partition, not evidence that the original design used the same rules. For example, health files with SQLite imports are counted under E, not twice under A.

Raw scan counts below are independent and overlap; do not sum their file or line columns.

| Scan | Pattern | Files | Lines |
| --- | --- | --- | --- |
| A | SQLiteGraphStore | 98 | 375 |
| B | DecisionStore | 1 | 2 |
| C | DualWriteStore | 18 | 68 |
| D | DurableOutbox | 5 | 15 |
| E | SQLite graph import patterns | 95 | 112 |
| F | dual_write_store imports | 15 | 17 |
| G | graph.outbox imports | 4 | 4 |
| H | backend.*sqlite in .py/.toml/.yaml/.json | 35 | 138 |
| I | scoring.storage import | 0 | 0 |
| J | import sqlite3 except scoring/persistence_outbox.py | 39 | 40 |

DecisionStore's two textual hits are architectural-gate strings in one test file, not imports or consumers. Real DecisionStore/scoring.storage imports: **zero**. Independently of the exclusive category assignment, AST-confirmed SQLiteGraphStore import occurrences total **112 across 96 files**; category A contains 70 of those files after assigning specialized consumers to their owning categories. This is the direct-import comparison to the claimed 15–20, rather than interpreting the category partition as a complete import count. There are **126 backend/config-related files** in the union of scans A/C/D/E/F/G/H/I; the other 22 files add raw-SQLite review scope. Both totals still include detection tests and historical evidence, not just required edits.

ci-platform has one SQLiteGraphStore parity-test import/instantiation (`tests/test_age_graph_store_v.py`) and one unrelated code-review database script (`prompt0_ci_structural_map.py`). No targeted backend reference was found in its `ci_platform/` production package.

Scan scope includes hidden/unignored source/config files, excluding dependency environments, node_modules, VCS internals, caches, build/dist, .codex_tmp, .codex, temporary directories and generated code-review/graphify databases. Two existing `logs/design_drift_*.json` reports were included because the requested JSON scan matches them; they are historical evidence, not runtime configuration. Scan J includes test code and literal scan-pattern strings as requested, not only live imports. Markdown, .env, shell scripts and .yml were not part of the requested A–J suffix set; configuration rollout must also check these surfaces. “No match” here is not a claim of zero SQLite usage in the entire workspace.

## SECTION 3: PROTOCOL GAP ANALYSIS

`protocol.py` defines **five** runtime-checkable protocols: GraphStore, GraphTraversalStore, ProtocolV2GraphStore, L5LearningStore and ScoringPersistenceStore. ProtocolV2GraphStore inherits GraphStore. L5LearningStore stays separate and explicitly documents that separation. GraphTraversalStore and ScoringPersistenceStore are separate extensions too.

GraphStore declares 45 methods. V2 declares 22 methods but redeclares `count_verified_decisions`, so it adds **21 unique methods**, for **66 effective methods**, not 67. L5 declares 7 methods. Appendix A lists every exact declared signature; all methods in the three named protocols are present on memory and AGE adapters.

| Protocol | Required methods | Memory missing names | Memory call-shape gaps | AGE adapter missing names | AGE call-shape gaps |
| --- | --- | --- | --- | --- | --- |
| GraphStore | 45 | 0 | 0 | 0 | 0 |
| ProtocolV2GraphStore | 66 | 0 | 0 | 0 | 0 |
| L5LearningStore | 7 | 0 | 1 | 0 | 0 |
| GraphTraversalStore | 3 | 0 | 0 | 0 | 0 |
| ScoringPersistenceStore | 4 | 0 | 0 | 4 | 0 |

Missing InMemoryGraphStore methods by requested protocol: GraphStore **none (0)**; ProtocolV2GraphStore **none (0)**; L5LearningStore **none (0)**. There is consequently no missing-method signature list to implement.

There is one real signature defect:

```python
# Required, protocol.py:597
def count_categories_with_n(self, domain: str, n: int = 1) -> int: ...
# Actual, memory_store.py:1324
def count_categories_with_n(self, domain: str, n: int) -> int: ...
```

`InMemoryGraphStore().count_categories_with_n("soc")` raises TypeError. Correct WS2 to add the default `n=1` and verify a protocol-typed caller can omit it. Runtime isinstance currently returns true despite this defect; method-name presence is not signature or behavioral conformance. The audit checked required-only, all-positional/keyword-only and all-named call binding, not exhaustive semantic equivalence or return-type variance.

AGEGraphStoreAdapter has no missing methods or observed call-binding gaps for GraphStore, V2, L5 or GraphTraversalStore. That supports leaving its source unchanged for backend elimination alone. It lacks the four **native ScoringPersistenceStore** methods listed below; consumers already use GraphScoringPersistence over save_governance/list_governance, so this is not a present missing-call failure:

```python
def save_k_utility(self, domain: str, episode_id: str, k: int, utility: float, metadata: dict[str, Any] | None=None) -> str: ...
def get_k_utilities(self, domain: str, episode_id: str | None=None, limit: int=100) -> list[dict[str, Any]]: ...
def save_holdout_decision(self, domain: str, decision_id: str, holdout_group: str, metadata: dict[str, Any] | None=None) -> str: ...
def get_holdout_decisions(self, domain: str, holdout_group: str | None=None) -> list[dict[str, Any]]: ...
```

DD-6 is therefore “staged extension plus bridge is integrated,” not “all backends natively implement the extension.” Do not add these four methods to required GraphStore until a coordinated AGE rollout has implemented them. The current AGE generic governance `_save_platform_state` (`ci_platform/graph/age_graph_store.py:138–155`) issues delete and create in separate calls; source inspection exposes a durability/concurrency concern, not a newly demonstrated live failure. Transactional native upserts and historical K/holdout data import remain separately scoped follow-ups.

Gap accounting: **0 missing methods in the three requested protocols; 1 memory signature defect; 4 intentionally staged native AGE scoring methods.** These are distinct counts, not five unimplemented memory methods.

## SECTION 4: SEQUENCING RECOMMENDATION

**Correct WS1 → WS2 → WS3 → WS5 to WS2 verification/fixes → WS3 consumer migration → WS1 deletion → WS5 enforcement.** WS4 outbox documentation can run alongside verification, but the outcome-buffer policy must be settled before outbox deletion. Coordinated consumer changes and deletions may land in one atomic change; do not leave a deletion-only intermediate state.

Concrete import failures prove delete-first is unsafe:

1. `graph/__init__.py:12` imports SQLiteGraphStore and exports it at line 27. Even importing a remaining graph submodule initializes this package and fails if sqlite_store.py is removed first.
2. `graph/__init__.py:14` imports ProtocolV2OutcomeService, whose module imports DurableOutbox at `outcome_service.py:8`. Removing graph/outbox.py breaks this public import chain.
3. `scoring/scorer.py:36,184` imports/checks DualWriteStore; `legacy_signal_filter.py:339,608` lazily imports it for reads. Removing dual_write_store.py breaks scoring/imports or wrapped reads unless those consumers are migrated.
4. Factory, health, migration tools, examples, scripts and test collection still import the deleted modules.

WS2 has no dependency on deletion: the probes in this pass ran with all legacy files present. No new circular dependency is required by the corrected sequence. Existing package initialization and lazy cross-package imports create ordering hazards; preserve deferred imports where used. This audit establishes the concrete edges above, not a proof that the full repository import graph has no cycles.

Before WS1, validate durable AGE replacements for reopen/process-safety tests, retain portable archive/domain/tenant invariants, resolve bundle/migration tooling, and handle queued dual-write/outcome records. Deleting backend files does not migrate their stored data. Do not replace persistent stores with memory where restart or cross-process state is part of the contract.

## SECTION 5: MISSED FILES

The table below accounts for every non-test file hit from the requested scans. Files already explicitly named in the design are labeled accordingly. Appendix B preserves every corresponding line. Additional consumers without literal class names include public package imports, config callers and migration/archive readers; direct SQL usage must be reviewed by role, not blanket-deleted.

| Non-test file | First hit | Design coverage / required action |
| --- | --- | --- |
| ci-platform/prompt0_ci_structural_map.py | 4 | Independent code-review graph.db reader; not a scoring/GraphStore migration target. |
| copilot-sdk/apps/dataops/backend/app/graph_status.py | 89 | Missed concrete module: SQLite defaults/allowlists/fallback labels and dual-write status branches. Add memory support for dev and preserve AGE readiness. |
| copilot-sdk/apps/purchasing/backend/app/graph_status.py | 91 | Missed concrete module: SQLite defaults/allowlists/fallback labels and dual-write status branches. Add memory support for dev and preserve AGE readiness. |
| copilot-sdk/apps/purchasing/backend/app/main.py | 262 | Factory/config caller or startup helper: remove SQLite assumptions, select memory only for disposable dev state and AGE for persistent state. |
| copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py | 8 | Local ProofLedger SQL and GraphOutcomeLedger/OutcomeLedger selection; broader offline-sidecar scope, not deleted-backend import. |
| copilot-sdk/apps/purchasing/backend/cli.py | 55 | Factory/config caller or startup helper: remove SQLite assumptions, select memory only for disposable dev state and AGE for persistent state. |
| copilot-sdk/apps/regime_experiment/experiment.py | 22 | Experiment/example constructs SQLite backend. Use memory only for disposable runs; use AGE or explicit export/import where persisted results matter. |
| copilot-sdk/apps/s2p_differentiation/engine.py | 20 | Experiment/example constructs SQLite backend. Use memory only for disposable runs; use AGE or explicit export/import where persisted results matter. |
| copilot-sdk/apps/trading/backend/app/cli_sdk.py | 17 | CLI factory defaults plus SQLite backup integrity check; redesign AGE/memory backup behavior, do not mechanically remove sqlite3. |
| copilot-sdk/apps/trading/backend/app/graph_status.py | 88 | Missed concrete module: SQLite defaults/allowlists/fallback labels and dual-write status branches. Add memory support for dev and preserve AGE readiness. |
| copilot-sdk/apps/trading/backend/app/main.py | 201 | Factory/config caller or startup helper: remove SQLite assumptions, select memory only for disposable dev state and AGE for persistent state. |
| copilot-sdk/copilot_sdk/backend/health_builder.py | 12 | Named in design; apply corrections in Sections 1–4. |
| copilot-sdk/copilot_sdk/backend/signal_store.py | 9 | Independent SQLiteSignalStore sidecar; no direct deleted-class import. Broader persistence policy/guard review, not automatic backend removal. |
| copilot-sdk/copilot_sdk/config/graph_config.py | 303 | Reduce Backend Literal, both allowlists, dual-write DSN branches and policy messages; preserve production AGE guards. |
| copilot-sdk/copilot_sdk/demo/bundle.py | 14 | SQL restore branch writes decisions/outcomes/checkpoints/RL/evolution state directly; replace through protocols with round-trip coverage or retire branch. Existing AGE branch is not proof of full parity. |
| copilot-sdk/copilot_sdk/evolution/variant_store.py | 10 | Separate SQLiteVariantStore implementation with in-memory alternative; not a missing GraphStore method. Audit callers if all scoring persistence is in scope. |
| copilot-sdk/copilot_sdk/graph/__init__.py | 12 | Remove SQLite re-export only after consumer migration; preserve or explicitly retire public outcome-service API. |
| copilot-sdk/copilot_sdk/graph/dual_write_store.py | 19 | Named in design; apply corrections in Sections 1–4. |
| copilot-sdk/copilot_sdk/graph/factory.py | 15 | Named in design; apply corrections in Sections 1–4. |
| copilot-sdk/copilot_sdk/graph/legacy_signal_filter.py | 339 | Remove lazy dual-write imports/primary selection while preserving tenant/domain filtering and AGE pagination behavior. |
| copilot-sdk/copilot_sdk/graph/outbox.py | 6 | Named in design; apply corrections in Sections 1–4. |
| copilot-sdk/copilot_sdk/graph/outcome_service.py | 8 | BLOCKER: independent DurableOutbox consumer. Resolve pending-outcome durability/fail-closed policy before deleting its dependency. |
| copilot-sdk/copilot_sdk/graph/read_diff_runner.py | 11 | Remove dual-write-specific rejection import; preserve useful memory/AGE comparison behavior or explicitly retire the tool. |
| copilot-sdk/copilot_sdk/graph/sqlite_store.py | 7 | Named in design; apply corrections in Sections 1–4. |
| copilot-sdk/copilot_sdk/migrate/__main__.py | 91 | Archive/reconcile command constructs SQLiteGraphStore; isolate legacy read-only import tooling or retire command after cutover. Memory substitution is invalid. |
| copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py | 17 | Raw SQLite source importer; legitimate legacy-data migration tool, not a selectable GraphStore. Define retained tooling scope. |
| copilot-sdk/copilot_sdk/migration/rehearsal.py | 6 | Raw SQLite migration rehearsal/source handling; decide tooling retention separately from backend deletion. |
| copilot-sdk/copilot_sdk/outbox/store.py | 6 | Third outbox abstraction, OutboxStore/event queue; neither DurableOutbox nor PersistenceOutbox. Separate retention/migration decision. |
| copilot-sdk/copilot_sdk/outcome/ledger.py | 7 | Independent SQLite OutcomeLedger; GraphOutcomeLedger exists elsewhere. Audit callers without conflating it with DecisionStore. |
| copilot-sdk/copilot_sdk/pilot/transfer.py | 12 | MeasuredTransferStore persists sessions/observations directly in SQLite; independent sidecar scope. |
| copilot-sdk/copilot_sdk/promotion/core.py | 6 | Separate SQLite promotion storage; audit persistence policy/callers, not a GraphStore class import. |
| copilot-sdk/copilot_sdk/scoring/scorer.py | 36 | Remove concrete DualWriteStore import and governed-write special case after remaining V2 stores are verified. |
| copilot-sdk/examples/build_your_own/engine.py | 3 | Experiment/example constructs SQLite backend. Use memory only for disposable runs; use AGE or explicit export/import where persisted results matter. |
| copilot-sdk/examples/jm_reference/run.py | 8 | Experiment/example constructs SQLite backend. Use memory only for disposable runs; use AGE or explicit export/import where persisted results matter. |
| copilot-sdk/integrity/architecture_scan.py | 73 | Backend audit rules contain intentional SQLite patterns; retain detection and update allowed-backend expectations. |
| copilot-sdk/logs/design_drift_db_sidecars.json | 3 | Historical JSON report; no runtime break. Do not rewrite evidence just to reduce grep counts. |
| copilot-sdk/logs/design_drift_inventory.json | 13483 | Historical JSON report; no runtime break. Do not rewrite evidence just to reduce grep counts. |
| copilot-sdk/scripts/age_migration_benchmark.py | 11 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/age_pf_blockers.py | 9 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/age_v35_review_checks.py | 6 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/phase3_cycle_gate_v3.py | 131 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/phase3_dual_parity_v2.py | 9 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/phase3_dual_write_e2e_v2.py | 46 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/phase3_dual_write_e2e_v4.py | 13 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/phase3_dual_write_e2e_v5.py | 3 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/phase3_read_diff_v2.py | 4 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/phase3_read_diff_v4.py | 9 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/phase3_read_diff_v5.py | 5 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/phase3_reset_v3.py | 6 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/phase3_verify_v3.py | 3 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/phase_dual_write_e2e.py | 6 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/phase_read_diff.py | 5 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py | 13 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/shadow_live_test.py | 18 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |
| copilot-sdk/scripts/sqlite_copilot_audit.py | 8 | Audit/benchmark/replay/seed script: migrate AGE-relevant behavior; explicitly retire legacy SQLite/dual-write diagnostics or retain isolated source-reader tooling. |

Specific missed tests also matter: `tests/graph/test_protocol_v2_service_layer.py` tests public outcome/pending-sync behavior, not only a backend implementation; `tests/test_worker_process_safety.py` requires process-persistent state; `tests/scoring/test_storage.py` mixes portable behavior with SQLite schema/reopen tests. Do not delete these files wholesale or rename all their fixtures to memory. ci-platform's `tests/test_age_graph_store_v.py` contains a SQLite parity fixture even though production code there has no legacy backend import.

An additional indirect consumer is `copilot_sdk/migrate/reconcile_archive.py:12`: it imports ReadDiffRunner, so removing the latter's DualWriteStore dependency is required to keep archive reconciliation importable. It also still needs a way to read historical source archives. This file has no literal A–J match in the current snapshot and is therefore additional semantic scope, not included in the 148-file grep inventory. Similarly, the bridge and historical-data follow-ups need not mention deleted class names to remain unfinished work.

There are no actual DecisionStore imports in the two-repository scan. There are no preseed script hits under the supplied symbol patterns; the seed category consists of tests. That does not establish that scripts using factory calls, raw SQL or environment configuration are already migrated.

## SECTION 6: DESIGN DECISION CORRECTIONS

| Decision | Verdict | Corrected instruction |
| --- | --- | --- |
| DD-1 L5 stays separate | CONFIRMED | Keep separate; fix memory default argument. Preserve optional runtime capability checks. |
| DD-2 PersistenceOutbox keeps SQLite | CONFIRMED | Explicit one-file resilience exception; enforce the scoring SQLite gate around it. Do not route queued outcomes into it. |
| DD-3 Delete DualWriteStore + DurableOutbox | AMENDED | Dual wrapper removal follows consumer/data cutover. DurableOutbox removal additionally requires a replacement or explicit retirement of ProtocolV2OutcomeService pending-sync behavior. |
| DD-4 Factory only memory+AGE | CONFIRMED, scope expanded | Update GraphConfig types/validation, app configs/status and callers together; preserve production guards/wrappers. |
| DD-5 Remove health concrete checks | CONFIRMED, scope expanded | Remove lazy and top-level imports/branches; retain memory/AGE/unknown and wrapper ownership. Three app status modules need coordinated cleanup. |
| DD-6 ScoringPersistenceStore integrated | AMENDED | Four-method separate extension plus governance bridge already integrated. Native AGE extension remains absent; adding it to GraphStore now would break runtime conformance. |
| DD-7 SQLite tests switch to memory | AMENDED | Portable tests → memory; backend-only implementation tests → remove; restart/process/AGE durability tests → real AGE; migration-source fixtures → isolated legacy SQL reader. Preserve mixed-file behavior coverage. |

Additional corrections: five protocols, not three; SQLite implementation is ~168 KB, not ~40 KB; V2 has 21 unique additions, not 22; outbox is ~5.9 KB and not exclusively dual-write-owned. Category B's estimated 25–30 imports is obsolete (actual zero). Keep AGE adapter unchanged for the three existing protocol surfaces, but do not describe it as implementing every extension. The persistence-outbox exception changes the earlier task's blanket raw-SQLite scoring gate requirement; document that deliberate policy amendment.

The raw-SQLite sidecars in Section 5 do not all break when the three graph modules disappear. They expose a separate ambiguity: “eliminate two GraphStore backends” is narrower than “remove every SQLite database.” The corrected plan does the former, retains the explicit resilience exception, and requires individual scope decisions for source migration tools and independent sidecars. It does not silently authorize a wider persistence rewrite.

## SECTION 7: CORRECTED EFFORT ESTIMATES

The 3–4 days / 4 prompts + review / 6–8 credits claim is **not verified by source inspection**. Counts are larger than the proposed import bands, but WS2 is much smaller than a many-method implementation. Durable outcome policy, bundle fidelity, retained legacy-data import and live AGE fixtures drive risk more than grep-line count.

Nonbinding planning estimate, assuming AGE test access and an agreed outcome-buffer policy:

- Protocol/default fix and executable conformance checks: 0.25–0.5 engineering day.
- Factory/config/status/wrapper/scorer and portable consumer/test migration: 1–2 days.
- Outcome durability, bundle/archive/import-tool disposition and restart/process tests: 1.5–3 days.
- Deletion, gates, both-repository regression/type checks and review: 1–1.5 days.

Allow approximately **4–7 engineering days**, with data-cutover execution and optional native AGE scoring upserts estimated separately. This is a planning range, not measured execution time. A narrower disposable-dev-only conversion may fit 3–4 days but would not satisfy the durable-consumer scope. Credits cannot be responsibly inferred from file counts; the 6–8-credit estimate has no verified basis here.

## SECTION 8: CORRECTED CODEX PROMPT STRATEGY

Use six bounded implementation prompts plus one integration review, ordered by dependencies:

1. **Contract and scope lock:** fix memory L5 default; add meaningful call-contract coverage; lock the one-file resilience exception and decide outcome-service/legacy-import retention. Preserve separate extensions and document native AGE follow-up.
2. **Runtime selection and wrappers:** migrate GraphConfig, factory, app status/defaults, health, scorer and wrapper branches. Keep legacy modules until consumers are ready; reject new legacy selection without weakening AGE production checks.
3. **Portable consumers:** migrate disposable fixtures, examples and experiments to memory; keep domain/tenant/ID assertions. Partition mixed test files by behavior rather than deleting entire files.
4. **Durable behavior:** implement the agreed outcome-service replacement/retirement; preserve restart/process correctness on AGE, bundle contents, archive/reconcile behavior and retained legacy-source migration. Address pending records and historical K/holdout import before data cutover.
5. **Removal:** remove legacy package exports/imports, classes/modules and obsolete backend-only tests/diagnostics in the same coherent change. Run both-repository import/collection scans before and after.
6. **Enforcement and acceptance:** enforce absence/import gates across SDK/apps and the external test consumer; add dual/outbox removal gates if their dependencies are resolved; narrow the raw-SQLite scoring gate to its explicit exception and remove strict xfails once satisfied. Run full SDK/app/ci-platform suites, live AGE durability tests and per-repository mypy on changed Python files.
7. **Independent review:** verify no lost outcome/bundle/archive semantics, no memory fallback in production, exact exception scope, both repositories' public imports, and evidence for cutover. Record measured results rather than carrying forward previous suite totals.

WS4 documentation is small and can accompany prompts 1–2. Native AGE ScoringPersistenceStore upserts and historical data import require explicit ownership; they are not prerequisites for retaining the current bridge, but must not disappear from follow-up tracking.

### Verification performed in this pass

```text
python -m pytest tests/test_l5_protocol_extension.py tests/graph/test_protocol.py tests/graph/test_protocol_v2_service_layer.py tests/scoring/test_persistence_outbox.py -q --timeout=120
52 passed, 0 failed, 0 skipped (104 dependency deprecation warnings)
```

AST and runtime inspection checked exact protocol declarations, implementation method presence and representative permitted call shapes. AGE adapter inspection used an uninitialized instance solely for structural checks; no live database was contacted. The L5 omitted-argument probe intentionally raised the documented TypeError even while all 52 existing tests passed, showing the coverage gap.

No product/test Python file was modified in this pass. Mypy applies to the local audit/report helpers under `.codex_tmp/dstore_verify2/`: `python -m mypy .codex_tmp/dstore_verify2/audit.py .codex_tmp/dstore_verify2/write_report.py --config-file pyproject.toml` passed with no issues in two files. A SHA-256 comparison of all 1,924 inventoried source/config files found zero changes during this audit. Markdown changes are this corrections report and both session-state appendices. No migration deletions or commits were performed.

Local machine-readable evidence: `.codex_tmp/dstore_verify2/{scan_manifest,references,files,protocols,summary}.json`. The report embeds the reference/signature inventory so review does not depend on keeping ignored scratch files.

## APPENDIX A: EXACT PROTOCOL SIGNATURE INVENTORY

All GraphStore, V2 and L5 methods below are implemented by both InMemoryGraphStore and AGEGraphStoreAdapter. V2 inherits the GraphStore list, replacing the duplicate count_verified_decisions declaration. Memory also implements the separate traversal and scoring lists; AGE implements traversal but lacks the four native scoring methods. Presence does not erase the L5 signature defect in Section 3.

### ScoringPersistenceStore — protocol.py:16

Bases: `Protocol`. Runtime-checkable: `True`. Declared methods: 4.

```python
# line 26
def save_k_utility(self, domain: str, episode_id: str, k: int, utility: float, metadata: dict[str, Any] | None=None) -> str: ...
# line 29
def get_k_utilities(self, domain: str, episode_id: str | None=None, limit: int=100) -> list[dict[str, Any]]: ...
# line 32
def save_holdout_decision(self, domain: str, decision_id: str, holdout_group: str, metadata: dict[str, Any] | None=None) -> str: ...
# line 35
def get_holdout_decisions(self, domain: str, holdout_group: str | None=None) -> list[dict[str, Any]]: ...
```

### GraphStore — protocol.py:40

Bases: `Protocol`. Runtime-checkable: `True`. Declared methods: 45.

```python
# line 43
def write_decision(self, domain: str, category: str, action: str, confidence: float, factors: dict[str, Any], metadata: dict[str, Any] | None=None) -> str: ...
# line 54
def write_outcome(self, decision_id: str, actual_action: str, is_correct: bool, metadata: dict[str, Any] | None=None, *, domain: str, outcome: str | None=None, verified_at_epoch: float | None=None, quality_signal: float | None=None, override_comment: str | None=None, verified_by: str | None=None, analyst_action: str | None=None, final_action: str | None=None, recommended_action: str | None=None, was_override: bool | None=None) -> None: ...
# line 74
def get_decision(self, decision_id: str, domain: str, *, include_outcome: bool=False) -> dict[str, Any] | None: ...
# line 91
def get_decisions(self, domain: str, category: str | None=None, limit: int=400) -> list[dict[str, Any]]: ...
# line 99
def get_all_decisions(self, domain: str) -> list[dict[str, Any]]: ...
# line 107
def get_archived_decisions(self, domain: str) -> list[dict[str, Any]]: ...
# line 111
def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]: ...
# line 114
def count_verified(self, domain: str) -> int: ...
# line 117
def count_verified_decisions(self, domain: str) -> int: ...
# line 123
def save_evolution(self, domain: str, variant_id: str, state: dict[str, Any]) -> None: ...
# line 126
def get_evolution(self, domain: str, variant_id: str) -> dict[str, Any] | None: ...
# line 129
def list_evolutions(self, domain: str) -> list[dict[str, Any]]: ...
# line 132
def delete_evolution(self, domain: str, variant_id: str) -> None: ...
# line 135
def save_evolution_state(self, domain: str, variant_id: str, state: dict[str, Any]) -> None: ...
# line 138
def get_evolution_state(self, domain: str, variant_id: str) -> dict[str, Any] | None: ...
# line 141
def save_posterior(self, domain: str, key: str, state: dict[str, Any]) -> None: ...
# line 144
def get_posterior(self, domain: str, key: str) -> dict[str, Any] | None: ...
# line 147
def list_posteriors(self, domain: str) -> list[dict[str, Any]]: ...
# line 150
def delete_posterior(self, domain: str, key: str) -> None: ...
# line 153
def save_promotion(self, domain: str, rule_id: str, state: dict[str, Any]) -> None: ...
# line 156
def get_promotion(self, domain: str, rule_id: str) -> dict[str, Any] | None: ...
# line 159
def list_promotions(self, domain: str) -> list[dict[str, Any]]: ...
# line 162
def delete_promotion(self, domain: str, rule_id: str) -> None: ...
# line 165
def save_ledger(self, domain: str, entry_id: str, state: dict[str, Any]) -> None: ...
# line 168
def get_ledger(self, domain: str, entry_id: str) -> dict[str, Any] | None: ...
# line 171
def list_ledgers(self, domain: str) -> list[dict[str, Any]]: ...
# line 174
def delete_ledger(self, domain: str, entry_id: str) -> None: ...
# line 177
def save_governance(self, domain: str, key: str, state: dict[str, Any]) -> None: ...
# line 180
def get_governance(self, domain: str, key: str) -> dict[str, Any] | None: ...
# line 183
def list_governance(self, domain: str) -> list[dict[str, Any]]: ...
# line 186
def delete_governance(self, domain: str, key: str) -> None: ...
# line 189
def count_correct(self, domain: str) -> int: ...
# line 192
def count_decisions(self, domain: str) -> int: ...
# line 195
def save_centroids(self, domain: str, category: str, centroids: Any, metadata: dict[str, Any] | None=None, **kwargs: Any) -> None: ...
# line 205
def load_latest_centroids(self, domain: str) -> Any | None: ...
# line 208
def get_centroid_checkpoints(self, domain: str, include_v2: bool=False, **kwargs: Any) -> list[dict[str, Any]]: ...
# line 216
def load_latest_checkpoint_for_regime(self, domain: str, regime_tag: str) -> dict[str, Any] | None: ...
# line 222
def get_checkpoint_lineage(self, domain: str, checkpoint_id: str) -> dict[str, Any] | None: ...
# line 228
def get_decision_checkpoints(self, domain: str, decision_id: str) -> list[dict[str, Any]]: ...
# line 234
def archive_old_decisions(self, domain: str, keep_recent: int=800) -> int: ...
# line 237
def count_archived(self, domain: str) -> int: ...
# line 240
def close(self) -> None: ...
# line 243
def write_entity_enrichment(self, *, domain: str, entity_type: str, entity_id: str, namespace: str, metrics: dict[str, ProvenancedValue], computed_from: EnrichmentSourceSet, dry_run: bool=False, idempotency_key: str | None=None) -> EntityEnrichmentReceipt: ...
# line 259
def read_entity_enrichment(self, *, domain: str, entity_type: str, entity_id: str, namespace: str | None=None) -> dict[str, ProvenancedValue]: ...
# line 269
def list_entity_enrichments(self, *, domain: str, entity_type: str | None=None, namespace: str | None=None, limit: int=500) -> list[EntityEnrichmentRecord]: ...
```

### GraphTraversalStore — protocol.py:281

Bases: `Protocol`. Runtime-checkable: `True`. Declared methods: 3.

```python
# line 284
def get_decision_links(self, decision_id: str | None=None, *, domain: str, limit: int | None=None) -> list[dict[str, Any]]: ...
# line 293
def query_context(self, entity_id: str, max_depth: int, *, domain: str) -> list[dict[str, Any]]: ...
# line 302
def query_similar(self, entity_id: str, limit: int, *, domain: str) -> list[dict[str, Any]]: ...
```

### ProtocolV2GraphStore — protocol.py:307

Bases: `GraphStore, Protocol`. Runtime-checkable: `True`. Declared methods: 22.

```python
# line 314
def generate_decision_id(self, domain: str) -> str: ...
# line 321
def write_governed_decision(self, decision_id: str, domain: str, category: str, category_index: int, recommended_action: str, recommended_index: int, confidence: float, probabilities: list[float], factor_vector: list[float], factor_names: list[str], source: str='score', scorer_version: str='', preset_version: str='', factor_schema_version: str='', metadata: dict[str, Any] | None=None) -> None: ...
# line 341
def write_observation(self, observation_id: str, domain: str, category: str, recommended_action: str, confidence: float, source_route: str, scorer_version: str, factor_schema_version: str, entity_id: str | None=None, factor_vector: list[float] | None=None, factor_names: list[str] | None=None, metadata: dict[str, Any] | None=None) -> None: ...
# line 358
def append_evidence_receipt(self, receipt_intent_id: str, domain: str, decision_id: str, canonical_payload: dict[str, Any], actor: str, source_route: str, metadata: dict[str, Any] | None=None) -> tuple[int, str]: ...
# line 370
def write_conservation_status(self, status_id: str, domain: str, V: int, q: float, alpha: float, theta_min: float, verified_count: int, correct_count: int, status: str, policy_version: str) -> None: ...
# line 385
def write_fingerprint(self, fingerprint_id: str, domain: str, factor_names: list[str], factor_stats: dict[str, Any], skipped_incompatible: int, window: int, metadata: dict[str, Any] | None=None) -> None: ...
# line 397
def write_centroid_checkpoint(self, checkpoint_id: str, domain: str, category: str, action: str, centroids: Any, decisions_count: int, verified_count: int, iks: float, shape: list[int], factor_names_hash: str, quality_window_size: int | None=None, quality_verified_count: int | None=None, quality_correct_count: int | None=None, rolling_accuracy: float | None=None, quality_window_end: str | None=None, quality_policy_version: str | None=None, metadata: dict[str, Any] | None=None, decision_id: str | None=None) -> None: ...
# line 420
def write_evolution_event(self, event_id: str, domain: str, event_type: str, rule_name: str, variant_id: str, source_copilot: str | None=None, source_rule: str | None=None, metric: float | None=None, shadow_batch_size: int | None=None, min_shadow_batches: int | None=None, metadata: dict[str, Any] | None=None, decision_id: str | None=None) -> None: ...
# line 437
def get_evolution_events(self, domain: str, **kwargs: Any) -> list[dict[str, Any]]: ...
# line 442
def write_transfer_pattern(self, pattern_id: str, source_domain: str, target_domain: str, pattern_type: str, factor_mapping: dict[str, Any], confidence: float, validation_status: str, conservation_status: str, source_rule: str | None=None, target_rule: str | None=None, source_fingerprint_id: str | None=None, evolution_event_id: str | None=None, metadata: dict[str, Any] | None=None) -> None: ...
# line 460
def get_transfer_patterns(self, source_domain: str | None=None, target_domain: str | None=None) -> list[dict[str, Any]]: ...
# line 467
def decision_movement(self, domain: str, decision_id: str) -> list[dict[str, Any]]: ...
# line 471
def contextual_judgment(self, domain: str, entity_group: str, category: str) -> list[dict[str, Any]]: ...
# line 477
def promotion_basis(self, domain: str, rule_id: str) -> list[dict[str, Any]]: ...
# line 481
def transfer_witness(self, source_domain: str, target_domain: str, pattern_id: str) -> list[dict[str, Any]]: ...
# line 487
def list_fingerprints(self, domain: str | None=None) -> list[dict[str, Any]]: ...
# line 491
def get_latest_conservation_statuses(self, domains: list[str] | None=None) -> list[dict[str, Any]]: ...
# line 497
def get_iks_trajectory(self, domains: list[str] | None=None, start: float | None=None, end: float | None=None) -> list[dict[str, Any]]: ...
# line 505
def link_entity(self, decision_id: str, entity_id: str, entity_type: str, domain: str) -> None: ...
# line 514
def archive_decisions(self, domain: str, before: float, status_filter: str='pending', confirm_verified: bool=False) -> int: ...
# line 523
def domain_scoped_reset(self, domain: str) -> None: ...
# line 526
def count_verified_decisions(self, domain: str) -> int: ...
```

### L5LearningStore — protocol.py:531

Bases: `Protocol`. Runtime-checkable: `True`. Declared methods: 7.

```python
# line 539
def update_centroid(self, domain: str, category: str, action: str, centroid_vector: list[float], delta_norm: float, caused_by_decision_id: str | None=None) -> None: ...
# line 550
def get_centroids(self, domain: str) -> list[dict[str, object]]: ...
# line 553
def update_dk_weights(self, domain: str, weight_tensor: list[list[float]], n_decisions_used: int, computed_at: float, *, welford_state: dict[str, object] | None=None, n_confirmed: int | None=None, n_overridden: int | None=None, entity_group: str | None=None) -> None: ...
# line 568
def get_dk_weights(self, domain: str) -> dict[str, object] | None: ...
# line 571
def update_conservation_state(self, domain: str, status: str, alpha: float, q: float, V: int, theta_min: float, product: float, categories_total: int, categories_with_data: int, baseline_product: float, relative_threshold: float, complacency_flag: str, caused_by_decision_id: str | None=None, old_status: str | None=None) -> str: ...
# line 591
def get_conservation_state(self, domain: str) -> dict | None: ...
# line 597
def count_categories_with_n(self, domain: str, n: int=1) -> int: ...
```

## APPENDIX B: COMPLETE DEDUPLICATED REFERENCE INVENTORY

Each header gives workspace-relative path, assigned design category, and occurrence count. Each source line is prefixed with original line number and scan IDs (A–J from Section 2); the remainder is the actual line content, including indentation. Test/assertion strings and historical-report hits are intentionally retained. One line matching several scans is listed once.

### ci-platform/prompt0_ci_structural_map.py

Category I; 1 matching lines; non-test.

```text
4 [J] import sqlite3
```

### ci-platform/tests/test_age_graph_store_v.py

Category A; 2 matching lines; test/helper.

```text
149 [A,E]     from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
151 [A]     sqlite_store = SQLiteGraphStore(":memory:", domain="soc")
```

### copilot-sdk/apps/dataops/backend/app/graph_status.py

Category E; 5 matching lines; non-test.

```text
89 [H]         overrides["backend"] = "sqlite"
101 [H]     requested_backend: str = "sqlite"
137 [H]         if self.requested_backend not in {"sqlite", "age"}:
141 [H]         if self.requested_backend == "sqlite":
363 [H]         "active_backend": "age" if age_active else "sqlite",
```

### copilot-sdk/apps/dataops/backend/conftest.py

Category D; 1 matching lines; test/helper.

```text
19 [H]         'backend = "sqlite"\nexpected_backend = "sqlite"\nprefix = "DOPS-"\n',
```

### copilot-sdk/apps/dataops/backend/tests/conftest.py

Category A; 3 matching lines; test/helper.

```text
11 [A,E] from copilot_sdk.graph import SQLiteGraphStore
79 [A]         store = SQLiteGraphStore(str(target / "test_dataops.db"), domain="dataops", decision_id_prefix="DOPS-")
94 [A] def _seed_ae_events(store: SQLiteGraphStore) -> None:
```

### copilot-sdk/apps/dataops/backend/tests/test_bundle_wiring.py

Category A; 3 matching lines; test/helper.

```text
10 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
27 [A]     store = SQLiteGraphStore(str(db_path), domain=DOMAIN, decision_id_prefix="DOPS-")
35 [A]     store = SQLiteGraphStore(str(tmp_path / "bundle.db"), domain=DOMAIN, decision_id_prefix="DOPS-")
```

### copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py

Category A; 10 matching lines; test/helper.

```text
161 [H]     assert payload["graph_backend"] == "sqlite"
189 [H]     assert payload["graph_backend"] == "sqlite"
228 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
231 [A]     store = SQLiteGraphStore(db_path, domain="dataops")
1529 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
1531 [A]     store = SQLiteGraphStore(db_path, domain=domain)
1539 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
1541 [A]     store = SQLiteGraphStore(db_path, domain=domain)
1549 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
1551 [A]     store = SQLiteGraphStore(db_path, domain=domain)
```

### copilot-sdk/apps/dataops/backend/tests/test_dataops_fixture_closure.py

Category A; 3 matching lines; test/helper.

```text
19 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
160 [A,E] from copilot_sdk.graph import SQLiteGraphStore
170 [A] store = SQLiteGraphStore(str(db_path), domain='dataops', decision_id_prefix='DOPS-')
```

### copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py

Category E; 10 matching lines; test/helper.

```text
41 [H]     assert payload["active_backend"] == "sqlite"
42 [H]     assert payload["requested_backend"] == "sqlite"
60 [H]     assert payload["active_backend"] == "sqlite"
283 [H]     assert status["active_backend"] == "sqlite"
390 [H] backend = \"sqlite\"
391 [H] expected_backend = \"sqlite\"
397 [H] backend = \"sqlite\"
398 [H] expected_backend = \"sqlite\"
438 [A,E]     from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
440 [A]     store = SQLiteGraphStore(db_path, domain="dataops")
```

### copilot-sdk/apps/purchasing/backend/app/graph_status.py

Category E; 5 matching lines; non-test.

```text
91 [H]         overrides["backend"] = "sqlite"
103 [H]     requested_backend: str = "sqlite"
139 [H]         if self.requested_backend not in {"sqlite", "age", "dual_write"}:
143 [H]         if self.requested_backend == "sqlite":
411 [H]         "sqlite_authoritative": active_backend == "sqlite",
```

### copilot-sdk/apps/purchasing/backend/app/main.py

Category D; 1 matching lines; non-test.

```text
262 [H]             backend = "sqlite"
```

### copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py

Category I; 1 matching lines; non-test.

```text
8 [J] import sqlite3
```

### copilot-sdk/apps/purchasing/backend/cli.py

Category D; 1 matching lines; non-test.

```text
55 [H]         backend="sqlite",
```

### copilot-sdk/apps/purchasing/backend/conftest.py

Category D; 1 matching lines; test/helper.

```text
19 [H]         'backend = "sqlite"\nexpected_backend = "sqlite"\nprefix = "PUR-"\n',
```

### copilot-sdk/apps/purchasing/backend/tests/conftest.py

Category A; 3 matching lines; test/helper.

```text
11 [A,E] from copilot_sdk.graph import SQLiteGraphStore
98 [A]     store = SQLiteGraphStore(str(db_path), domain="purchasing", decision_id_prefix="PUR-")
104 [A] def _seed_ae_events(store: SQLiteGraphStore) -> None:
```

### copilot-sdk/apps/purchasing/backend/tests/conftest_helpers.py

Category A; 2 matching lines; test/helper.

```text
7 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
21 [A]     store = SQLiteGraphStore(db, domain=domain)
```

### copilot-sdk/apps/purchasing/backend/tests/test_bundle_wiring.py

Category A; 3 matching lines; test/helper.

```text
10 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
27 [A]     store = SQLiteGraphStore(str(db_path), domain=DOMAIN, decision_id_prefix="PUR-")
35 [A]     store = SQLiteGraphStore(str(tmp_path / "bundle.db"), domain=DOMAIN, decision_id_prefix="PUR-")
```

### copilot-sdk/apps/purchasing/backend/tests/test_health_outage_contract.py

Category E; 1 matching lines; test/helper.

```text
14 [H]         assert payload["graph_backend"] == "sqlite"
```

### copilot-sdk/apps/purchasing/backend/tests/test_purchasing_backend.py

Category A; 16 matching lines; test/helper.

```text
99 [H] backend = "sqlite"
100 [H] expected_backend = "sqlite"
316 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
319 [A]     store = SQLiteGraphStore(db_path, domain="purchasing")
805 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
808 [A]     store = SQLiteGraphStore(db_path, domain="purchasing")
827 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
830 [A]     store = SQLiteGraphStore(db_path, domain="purchasing")
978 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
984 [A]     store = SQLiteGraphStore(db_path, domain="purchasing")
1007 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
1009 [A]     store = SQLiteGraphStore(db_path, domain=domain)
1017 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
1019 [A]     store = SQLiteGraphStore(db_path, domain=domain)
1027 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
1029 [A]     store = SQLiteGraphStore(db_path, domain=domain)
```

### copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py

Category E; 10 matching lines; test/helper.

```text
40 [H]     assert payload["active_backend"] == "sqlite"
41 [H]     assert payload["requested_backend"] == "sqlite"
60 [H]     assert payload["active_backend"] == "sqlite"
294 [H]     assert status["active_backend"] == "sqlite"
373 [H] backend = \"sqlite\"
374 [H] expected_backend = \"sqlite\"
380 [H] backend = \"sqlite\"
381 [H] expected_backend = \"sqlite\"
421 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
423 [A]     store = SQLiteGraphStore(db_path, domain="purchasing")
```

### copilot-sdk/apps/regime_experiment/experiment.py

Category A; 3 matching lines; non-test.

```text
22 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
120 [A] def _new_scorer(db_path: str) -> tuple[CompoundingScorer, SQLiteGraphStore]:
121 [A]     store = SQLiteGraphStore(db_path, domain="trading")
```

### copilot-sdk/apps/s2p_differentiation/engine.py

Category A; 2 matching lines; non-test.

```text
20 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
179 [A]     store = SQLiteGraphStore(path, domain="s2p")
```

### copilot-sdk/apps/trading/backend/app/cli_sdk.py

Category I; 2 matching lines; non-test.

```text
17 [J] import sqlite3
607 [H]     if _load_cli_graph_config(_cli_profile()).backend != "sqlite":
```

### copilot-sdk/apps/trading/backend/app/graph_status.py

Category E; 4 matching lines; non-test.

```text
88 [H]         overrides["backend"] = "sqlite"
100 [H]     requested_backend: str = "sqlite"
136 [H]         if self.requested_backend not in {"sqlite", "age", "dual_write"}:
141 [H]         if self.requested_backend == "sqlite":
```

### copilot-sdk/apps/trading/backend/app/main.py

Category D; 1 matching lines; non-test.

```text
201 [H]         backend = "sqlite"
```

### copilot-sdk/apps/trading/backend/conftest.py

Category D; 1 matching lines; test/helper.

```text
19 [H]         'backend = "sqlite"\nexpected_backend = "sqlite"\nprefix = "TRD-"\n',
```

### copilot-sdk/apps/trading/backend/tests/conftest_helpers.py

Category A; 3 matching lines; test/helper.

```text
10 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
35 [A]     store = SQLiteGraphStore(db, domain=domain)
114 [A]     store = SQLiteGraphStore(db, domain=domain)
```

### copilot-sdk/apps/trading/backend/tests/test_bundle_wiring.py

Category A; 3 matching lines; test/helper.

```text
10 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
27 [A]     store = SQLiteGraphStore(str(db_path), domain=DOMAIN, decision_id_prefix="TRD-")
35 [A]     store = SQLiteGraphStore(str(tmp_path / "bundle.db"), domain=DOMAIN, decision_id_prefix="TRD-")
```

### copilot-sdk/apps/trading/backend/tests/test_health_route_contract.py

Category E; 1 matching lines; test/helper.

```text
20 [H]     assert root["graph_backend"] == "sqlite"
```

### copilot-sdk/apps/trading/backend/tests/test_regime_replay.py

Category A; 3 matching lines; test/helper.

```text
9 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
13 [A]     store = SQLiteGraphStore(path, domain="trading")
27 [A]     store = SQLiteGraphStore(path, domain="trading")
```

### copilot-sdk/apps/trading/backend/tests/test_trading_backend.py

Category A; 17 matching lines; test/helper.

```text
140 [H] backend = "sqlite"
141 [H] expected_backend = "sqlite"
172 [H]     assert payload["graph_backend"] == "sqlite"
433 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
436 [A]     store = SQLiteGraphStore(db_path, domain="trading")
801 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
804 [A]     store = SQLiteGraphStore(db_path, domain="trading")
823 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
826 [A]     store = SQLiteGraphStore(db_path, domain="trading")
891 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
897 [A]     store = SQLiteGraphStore(db_path, domain="trading")
920 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
922 [A]     store = SQLiteGraphStore(db_path, domain=domain)
930 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
932 [A]     store = SQLiteGraphStore(db_path, domain=domain)
940 [A,E]     from copilot_sdk.graph import SQLiteGraphStore
942 [A]     store = SQLiteGraphStore(db_path, domain=domain)
```

### copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py

Category E; 13 matching lines; test/helper.

```text
17 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
44 [H]     assert payload["active_backend"] == "sqlite"
45 [H]     assert payload["requested_backend"] == "sqlite"
64 [H]     assert payload["active_backend"] == "sqlite"
222 [H] def test_generic_graph_backend_age_still_downgrades_to_sqlite(monkeypatch, tmp_path):
228 [A]         assert isinstance(store._store, SQLiteGraphStore)
362 [H]     assert status["active_backend"] == "sqlite"
460 [H] backend = \"sqlite\"
461 [H] expected_backend = \"sqlite\"
467 [H] backend = \"sqlite\"
468 [H] expected_backend = \"sqlite\"
507 [A,E]     from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
509 [A]     store = SQLiteGraphStore(db_path, domain="trading")
```

### copilot-sdk/copilot_sdk/backend/health_builder.py

Category E; 4 matching lines; non-test.

```text
12 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
35 [A]     if isinstance(store, SQLiteGraphStore):
39 [C,F]     from copilot_sdk.graph.dual_write_store import DualWriteStore
40 [C]     if isinstance(store, DualWriteStore):
```

### copilot-sdk/copilot_sdk/backend/signal_store.py

Category I; 1 matching lines; non-test.

```text
9 [J] import sqlite3
```

### copilot-sdk/copilot_sdk/config/graph_config.py

Category D; 4 matching lines; non-test.

```text
303 [H]         if self.backend not in {"sqlite", "memory", "age", "dual_write"}:
305 [H]         if self.expected_backend not in {"sqlite", "memory", "age", "dual_write"}:
309 [H]         if self.expected_backend == "age" and self.backend == "sqlite":
312 [H]                     f"expected backend age but resolved sqlite for domain '{self.domain}'"
```

### copilot-sdk/copilot_sdk/demo/bundle.py

Category A; 2 matching lines; non-test.

```text
14 [A,E]     from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
168 [A]         LOGGER.warning("Demo bundle restore requires a direct-write SQLiteGraphStore")
```

### copilot-sdk/copilot_sdk/evolution/variant_store.py

Category H; 1 matching lines; non-test.

```text
10 [J] import sqlite3
```

### copilot-sdk/copilot_sdk/graph/__init__.py

Category A; 2 matching lines; non-test.

```text
12 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
27 [A]     "SQLiteGraphStore",
```

### copilot-sdk/copilot_sdk/graph/dual_write_store.py

Category C; 5 matching lines; non-test.

```text
19 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
20 [D,G] from copilot_sdk.graph.outbox import DurableOutbox
36 [C] class DualWriteStore(GraphStore):
61 [A]         if isinstance(primary, SQLiteGraphStore) and isinstance(secondary, SQLiteGraphStore):
76 [D]         self._outbox = DurableOutbox(outbox_path) if outbox_path else None
```

### copilot-sdk/copilot_sdk/graph/factory.py

Category D; 6 matching lines; non-test.

```text
15 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
178 [H]     if selected_backend == "sqlite":
191 [A]             SQLiteGraphStore(
204 [A]         primary = SQLiteGraphStore(
241 [C,F]         from copilot_sdk.graph.dual_write_store import DualWriteStore
258 [C]             DualWriteStore(
```

### copilot-sdk/copilot_sdk/graph/legacy_signal_filter.py

Category C; 4 matching lines; non-test.

```text
339 [C,F]         from copilot_sdk.graph.dual_write_store import DualWriteStore
341 [C]         return self._store.primary if isinstance(self._store, DualWriteStore) else self._store
608 [C,F]         from copilot_sdk.graph.dual_write_store import DualWriteStore
610 [C]         reader = self._store.primary if isinstance(self._store, DualWriteStore) else self._store
```

### copilot-sdk/copilot_sdk/graph/outbox.py

Category I; 2 matching lines; non-test.

```text
6 [J] import sqlite3
15 [D] class DurableOutbox:
```

### copilot-sdk/copilot_sdk/graph/outcome_service.py

Category I; 2 matching lines; non-test.

```text
8 [D,G] from copilot_sdk.graph.outbox import DurableOutbox
34 [D]         outbox: DurableOutbox,
```

### copilot-sdk/copilot_sdk/graph/read_diff_runner.py

Category C; 3 matching lines; non-test.

```text
11 [C,F] from copilot_sdk.graph.dual_write_store import DualWriteStore
156 [C]         if isinstance(primary, DualWriteStore) or isinstance(secondary, DualWriteStore):
158 [C]                 "ReadDiffRunner requires two concrete stores, not DualWriteStore. "
```

### copilot-sdk/copilot_sdk/graph/sqlite_store.py

Category I; 3 matching lines; non-test.

```text
7 [J] import sqlite3
393 [A] class SQLiteGraphStore:
429 [A]             raise RuntimeError("SQLiteGraphStore is closed")
```

### copilot-sdk/copilot_sdk/migrate/__main__.py

Category A; 2 matching lines; non-test.

```text
91 [A,E]         from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
94 [A]         sqlite_store = SQLiteGraphStore(args.source, domain=args.domain)
```

### copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py

Category I; 1 matching lines; non-test.

```text
17 [J] import sqlite3
```

### copilot-sdk/copilot_sdk/migration/rehearsal.py

Category I; 1 matching lines; non-test.

```text
6 [J] import sqlite3
```

### copilot-sdk/copilot_sdk/outbox/store.py

Category I; 1 matching lines; non-test.

```text
6 [J] import sqlite3
```

### copilot-sdk/copilot_sdk/outcome/ledger.py

Category I; 1 matching lines; non-test.

```text
7 [J] import sqlite3
```

### copilot-sdk/copilot_sdk/pilot/transfer.py

Category I; 1 matching lines; non-test.

```text
12 [J] import sqlite3
```

### copilot-sdk/copilot_sdk/promotion/core.py

Category I; 1 matching lines; non-test.

```text
6 [J] import sqlite3
```

### copilot-sdk/copilot_sdk/scoring/scorer.py

Category F; 2 matching lines; non-test.

```text
36 [C,F] from copilot_sdk.graph.dual_write_store import DualWriteStore
184 [C]             isinstance(graph_store, DualWriteStore)
```

### copilot-sdk/examples/build_your_own/engine.py

Category A; 3 matching lines; non-test.

```text
3 [A] The governed arm uses the real CompoundingScorer and SQLiteGraphStore. The
19 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
89 [A]     store = SQLiteGraphStore(work_dir / "decisions.sqlite", domain=preset.name)
```

### copilot-sdk/examples/jm_reference/run.py

Category A; 4 matching lines; non-test.

```text
8 [A] ``SQLiteGraphStore``.  ``CompoundingScorer.learn`` performs the real outcome
24 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
70 [A] def _evolution_events(store: SQLiteGraphStore, domain: str) -> list[dict[str, Any]]:
89 [A]         store = SQLiteGraphStore(db_path, domain="trading")
```

### copilot-sdk/integration/age_jm/test_phase_01_contracts.py

Category D; 4 matching lines; test/helper.

```text
19 [H]         overrides={"backend": "sqlite", "expected_backend": "sqlite"},
57 [H]         backend="sqlite",
58 [H]         expected_backend="sqlite",
63 [H]     assert config.backend == "sqlite"
```

### copilot-sdk/integrity/architecture_scan.py

Category D; 12 matching lines; non-test.

```text
73 [H]     ("copilot-sdk/copilot_sdk/backend/signal_store.py", 'sqlite3.connect(":memory:", check_same_thread=False)'),
74 [H]     ("copilot-sdk/copilot_sdk/backend/signal_store.py", "db = self._memory if self._memory is not None else sqlite3.connect(self.db_path, timeout=30)"),
93 [H]     ("copilot-sdk/apps/dataops/backend/app/dataops_governance.py", "self._db = sqlite3.connect(str(db_path), check_same_thread=False)"),
94 [H]     ("copilot-sdk/apps/dataops/backend/app/main.py", "self.conn = sqlite3.connect(path, check_same_thread=False)"),
95 [H]     ("copilot-sdk/apps/purchasing/backend/app/main.py", "self.conn = sqlite3.connect(path, check_same_thread=False)"),
96 [H]     ("copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py", "self._db = sqlite3.connect(self.path, check_same_thread=False)"),
97 [H]     ("copilot-sdk/apps/trading/backend/app/cli_sdk.py", "conn = sqlite3.connect(backup_path)"),
98 [H]     ("copilot-sdk/apps/trading/backend/app/main.py", "self.conn = sqlite3.connect(path, check_same_thread=False)"),
99 [H]     ("s2p-copilot/backend/app/main.py", "self.conn = sqlite3.connect(path, check_same_thread=False)"),
100 [H]     ("s2p-copilot/backend/app/services/proposal_service.py", "self._connection = sqlite3.connect(db_path, check_same_thread=False)"),
101 [H]     ("gen-ai-roi-demo-v4-v50/backend/app/main.py", "self.conn = sqlite3.connect(path, check_same_thread=False)"),
102 [H]     ("gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py", "self._audit = sqlite3.connect(self.db_path, check_same_thread=False)"),
```

### copilot-sdk/logs/design_drift_db_sidecars.json

Category I; 6 matching lines; non-test.

```text
3 [H]     "path": "apps/dataops/backend/data/dataops_evolution.sqlite3-shm",
7 [H]     "path": "apps/dataops/backend/data/dataops_evolution.sqlite3-wal",
11 [H]     "path": "apps/purchasing/backend/data/purchasing_evolution.sqlite3-shm",
15 [H]     "path": "apps/purchasing/backend/data/purchasing_evolution.sqlite3-wal",
27 [H]     "path": "apps/trading/backend/data/trading_evolution.sqlite3-shm",
31 [H]     "path": "apps/trading/backend/data/trading_evolution.sqlite3-wal",
```

### copilot-sdk/logs/design_drift_inventory.json

Category I; 11 matching lines; non-test.

```text
13483 [H]       "path": "apps/dataops/backend/dataops_promotion.sqlite3",
13495 [H]       "path": "apps/dataops/backend/data/dataops_evolution.sqlite3",
13499 [H]       "path": "apps/dataops/backend/data/dataops_governance.sqlite3",
13503 [H]       "path": "apps/dataops/backend/data/dataops_outcomes.sqlite3",
13507 [H]       "path": "apps/dataops/backend/data/dataops_promotion.sqlite3",
13519 [H]       "path": "apps/purchasing/backend/data/purchasing_evolution.sqlite3",
13527 [H]       "path": "apps/purchasing/backend/data/purchasing_promotion.sqlite3",
13531 [H]       "path": "apps/purchasing/backend/data/purchasing_proof_ledger.sqlite3",
13535 [H]       "path": "apps/purchasing/backend/data/purchasing_verified_outcomes.sqlite3",
13547 [H]       "path": "apps/trading/backend/data/trading_evolution.sqlite3",
13551 [H]       "path": "apps/trading/backend/data/trading_promotion_engine.sqlite3",
```

### copilot-sdk/scripts/age_migration_benchmark.py

Category I; 1 matching lines; non-test.

```text
11 [J] import sqlite3
```

### copilot-sdk/scripts/age_pf_blockers.py

Category I; 1 matching lines; non-test.

```text
9 [J] import sqlite3
```

### copilot-sdk/scripts/age_v35_review_checks.py

Category I; 1 matching lines; non-test.

```text
6 [J] import sqlite3
```

### copilot-sdk/scripts/phase3_cycle_gate_v3.py

Category I; 1 matching lines; non-test.

```text
131 [J]     import sqlite3
```

### copilot-sdk/scripts/phase3_dual_parity_v2.py

Category A; 2 matching lines; non-test.

```text
9 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
27 [A] primary = SQLiteGraphStore(SQLITE_PATH, domain=DOMAIN, decision_id_prefix="TRD-")
```

### copilot-sdk/scripts/phase3_dual_write_e2e_v2.py

Category A; 3 matching lines; non-test.

```text
46 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
49 [A] sqlite = SQLiteGraphStore(sqlite_path, domain="trading", decision_id_prefix="TRD-")
102 [A] sqlite = SQLiteGraphStore(sqlite_path, domain="trading", decision_id_prefix="TRD-")
```

### copilot-sdk/scripts/phase3_dual_write_e2e_v4.py

Category C; 5 matching lines; non-test.

```text
13 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
52 [A] sqlite = SQLiteGraphStore(SQLITE_PATH, domain="trading", decision_id_prefix="TRD-")
102 [A] sqlite = SQLiteGraphStore(SQLITE_PATH, domain="trading", decision_id_prefix="TRD-")
138 [J] import sqlite3
162 [C]     print(f"  (This is OK if no DualWriteStore failures occurred)")
```

### copilot-sdk/scripts/phase3_dual_write_e2e_v5.py

Category A; 4 matching lines; non-test.

```text
3 [J] import sqlite3 as sqlite3_mod
10 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
49 [A] sqlite = SQLiteGraphStore(SQLITE_PATH, domain="trading", decision_id_prefix="TRD-")
96 [A] sqlite = SQLiteGraphStore(SQLITE_PATH, domain="trading", decision_id_prefix="TRD-")
```

### copilot-sdk/scripts/phase3_read_diff_v2.py

Category C; 3 matching lines; non-test.

```text
4 [C] Does NOT use DualWriteStore — the diff needs distinct store instances.
9 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
22 [A] primary = SQLiteGraphStore(SQLITE_PATH, domain=DOMAIN, decision_id_prefix="TRD-")
```

### copilot-sdk/scripts/phase3_read_diff_v4.py

Category A; 2 matching lines; non-test.

```text
9 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
22 [A] primary = SQLiteGraphStore(SQLITE_PATH, domain=DOMAIN, decision_id_prefix="TRD-")
```

### copilot-sdk/scripts/phase3_read_diff_v5.py

Category A; 2 matching lines; non-test.

```text
5 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
23 [A] primary = SQLiteGraphStore(SQLITE_PATH, domain=DOMAIN, decision_id_prefix="TRD-")
```

### copilot-sdk/scripts/phase3_reset_v3.py

Category I; 1 matching lines; non-test.

```text
6 [J] import sqlite3
```

### copilot-sdk/scripts/phase3_verify_v3.py

Category I; 1 matching lines; non-test.

```text
3 [J] import sqlite3
```

### copilot-sdk/scripts/phase_dual_write_e2e.py

Category A; 3 matching lines; non-test.

```text
6 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
13 [A]     store=SQLiteGraphStore(cfg["db_path"], domain=cfg["domain"], decision_id_prefix=cfg["prefix"]); baseline=store.count_decisions(cfg["domain"]); store.close()
23 [A]     store=SQLiteGraphStore(cfg["db_path"], domain=cfg["domain"], decision_id_prefix=cfg["prefix"]); delta=store.count_decisions(cfg["domain"])-baseline; store.close()
```

### copilot-sdk/scripts/phase_read_diff.py

Category A; 2 matching lines; non-test.

```text
5 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
12 [A]     primary = SQLiteGraphStore(cfg["db_path"], domain=cfg["domain"], decision_id_prefix=cfg["prefix"])
```

### copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py

Category I; 1 matching lines; non-test.

```text
13 [J] import sqlite3
```

### copilot-sdk/scripts/shadow_live_test.py

Category A; 6 matching lines; non-test.

```text
18 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
30 [A] def _open_readable_store(path: Path) -> SQLiteGraphStore | None:
32 [A]         return SQLiteGraphStore(path, domain="trading")
72 [A]     source_store = SQLiteGraphStore(source, domain="trading")
88 [A]         primary_store = SQLiteGraphStore(primary_db, domain="trading", decision_id_prefix="TRD-P-")
89 [A]         shadow_store = SQLiteGraphStore(shadow_db, domain="trading", decision_id_prefix="TRD-S-")
```

### copilot-sdk/scripts/sqlite_copilot_audit.py

Category I; 6 matching lines; non-test.

```text
8 [A] - Rule #38 compliance (direct SQLiteGraphStore construction)
16 [J] import sqlite3
190 [A]     """Check Rule #38: does main.py construct SQLiteGraphStore directly?"""
209 [A]             if "SQLiteGraphStore(" in stripped:
216 [A]             print(f"    VIOLATION: {len(direct_constructions)} direct SQLiteGraphStore() calls:")
220 [A]             print(f"    COMPLIANT: no direct SQLiteGraphStore() calls")
```

### copilot-sdk/tests/backend/test_coalesced_reads.py

Category A; 5 matching lines; test/helper.

```text
15 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
19 [A]     store = SQLiteGraphStore(tmp_path / "reads.db", domain="purchasing")
53 [A]     store = SQLiteGraphStore(tmp_path / "retry.db", domain="purchasing")
57 [A]     store = SQLiteGraphStore(tmp_path / "retry.db", domain="purchasing")
67 [A]     store = SQLiteGraphStore(tmp_path / "fresh.db", domain="purchasing")
```

### copilot-sdk/tests/backend/test_graph_access_health.py

Category E; 5 matching lines; test/helper.

```text
13 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
17 [H] @pytest.mark.parametrize("backend", ["memory", "sqlite"])
20 [A]     store = (SQLiteGraphStore(str(tmp_path / "health.db"), domain=domain)
21 [H]              if backend == "sqlite" else InMemoryGraphStore(domain=domain))
67 [H]         payload = build_graph_health(store, SimpleNamespace(backend="sqlite", graph="soc_graph"), domain)
```

### copilot-sdk/tests/backend/test_scorer_proxy.py

Category A; 2 matching lines; test/helper.

```text
11 [A,E] from copilot_sdk.graph import SQLiteGraphStore
37 [A]     store = SQLiteGraphStore(str(db_path), domain="trading")
```

### copilot-sdk/tests/backend/test_scoring_router.py

Category A; 2 matching lines; test/helper.

```text
21 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
320 [A]         self.graph_store = SQLiteGraphStore(db_path, domain="test")
```

### copilot-sdk/tests/demo/test_bundle.py

Category A; 3 matching lines; test/helper.

```text
5 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
85 [A]     return SQLiteGraphStore(tmp_path / "graph.sqlite", domain=DOMAIN)
184 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite", domain=DOMAIN)
```

### copilot-sdk/tests/evolution/test_evolution_store.py

Category H; 2 matching lines; test/helper.

```text
4 [A,E] from copilot_sdk.graph import GraphStore, InMemoryGraphStore, SQLiteGraphStore
35 [A]     assert isinstance(SQLiteGraphStore(tmp_path / "graph.sqlite"), EvolutionStore)
```

### copilot-sdk/tests/evolution/test_selection_snapshot.py

Category H; 3 matching lines; test/helper.

```text
8 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
12 [A]     graph = SQLiteGraphStore(tmp_path / "variants.db")
13 [A]     other_graph = SQLiteGraphStore(tmp_path / "variants.db")
```

### copilot-sdk/tests/evolution/test_summary_snapshot.py

Category H; 3 matching lines; test/helper.

```text
7 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
11 [A]     graph = SQLiteGraphStore(tmp_path / "summary.db")
12 [A]     writer_graph = SQLiteGraphStore(tmp_path / "summary.db")
```

### copilot-sdk/tests/graph/test_contract_cross.py

Category D; 1 matching lines; test/helper.

```text
193 [H]             '[defaults]\nbackend="sqlite"\nexpected_backend="sqlite"\ngraph="test_graph"\ndsn=""\n',
```

### copilot-sdk/tests/graph/test_correctness_conformance.py

Category A; 2 matching lines; test/helper.

```text
11 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
19 [A]         graph_store = SQLiteGraphStore(tmp_path / "correctness.sqlite", domain="test")
```

### copilot-sdk/tests/graph/test_decision_metadata.py

Category A; 5 matching lines; test/helper.

```text
3 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
48 [A]     store = SQLiteGraphStore(db_path)
61 [A]     store = SQLiteGraphStore(db_path)
72 [A]     store = SQLiteGraphStore(db_path)
78 [A]     reopened = SQLiteGraphStore(db_path)
```

### copilot-sdk/tests/graph/test_domain_required_conformance.py

Category A; 2 matching lines; test/helper.

```text
8 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
15 [A]     return SQLiteGraphStore(tmp_path / "domain-required.sqlite", domain="test")
```

### copilot-sdk/tests/graph/test_evolution_event_links.py

Category A; 4 matching lines; test/helper.

```text
9 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
11 [A] Store = InMemoryGraphStore | SQLiteGraphStore
20 [A]         graph_store = SQLiteGraphStore(tmp_path / "evolution-links.sqlite", domain="test")
63 [A]     if isinstance(store, SQLiteGraphStore):
```

### copilot-sdk/tests/graph/test_graph_store_evolution.py

Category A; 7 matching lines; test/helper.

```text
4 [J] import sqlite3
7 [A,E] from copilot_sdk.graph import GraphStore, InMemoryGraphStore, SQLiteGraphStore
68 [A]     store = SQLiteGraphStore(db_path)
89 [A]     store = SQLiteGraphStore(db_path)
104 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
114 [A]     store = SQLiteGraphStore(db_path)
123 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
```

### copilot-sdk/tests/graph/test_graphstore_factory.py

Category D; 9 matching lines; test/helper.

```text
11 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
21 [H]     store = create_graph_store(profile="test", backend="sqlite", domain="s2p", env={})
23 [A]         assert isinstance(store.graph_primary, SQLiteGraphStore)
31 [H]     store = create_graph_store(profile="test", backend="sqlite", domain="trading", db_path=db_path, env={})
33 [A]         assert isinstance(store.graph_primary, SQLiteGraphStore)
41 [H]         backend="sqlite",
46 [A]         assert isinstance(store.graph_primary, SQLiteGraphStore)
226 [H]     store = create_graph_store(profile="test", backend="sqlite", domain="test", db_path=":memory:")
227 [A]     assert isinstance(store.graph_primary, SQLiteGraphStore)
```

### copilot-sdk/tests/graph/test_link_domain_conformance.py

Category A; 3 matching lines; test/helper.

```text
8 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
16 [A]         graph_store = SQLiteGraphStore(tmp_path / "links.sqlite", domain="test")
43 [A]     if isinstance(store, SQLiteGraphStore):
```

### copilot-sdk/tests/graph/test_no_amend_policy.py

Category A; 2 matching lines; test/helper.

```text
14 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
24 [A]         graph_store = SQLiteGraphStore(tmp_path / "no-amend.sqlite", domain="test")
```

### copilot-sdk/tests/graph/test_protocol.py

Category A; 3 matching lines; test/helper.

```text
11 [A]     SQLiteGraphStore,
21 [A]     sqlite = SQLiteGraphStore(str(tmp_path / "protocol-v2.db"), domain="test")
173 [A]     assert isinstance(SQLiteGraphStore(tmp_path / "graph.sqlite"), EvolutionStore)
```

### copilot-sdk/tests/graph/test_protocol_v2_conformance.py

Category A; 9 matching lines; test/helper.

```text
8 [J] import sqlite3
16 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
35 [A]     store = SQLiteGraphStore(tmp_path / "protocol_v2.sqlite", domain="test")
67 [A]     store: SQLiteGraphStore,
399 [A]     store: SQLiteGraphStore,
421 [A]     store: SQLiteGraphStore,
1041 [A]     store = SQLiteGraphStore(db_path, domain="test")
1083 [A]     sqlite = SQLiteGraphStore(tmp_path / "receipt-parity.sqlite", domain="test")
2641 [A]     store = SQLiteGraphStore(db_path, domain="test")
```

### copilot-sdk/tests/graph/test_protocol_v2_service_layer.py

Category A; 6 matching lines; test/helper.

```text
5 [A,E] from copilot_sdk.graph import ProtocolV2OutcomeService, SQLiteGraphStore
6 [D,G] from copilot_sdk.graph.outbox import DurableOutbox
20 [A]     store = SQLiteGraphStore(tmp_path / "protocol-v2.sqlite", domain=DOMAIN)
48 [D]     outbox = DurableOutbox(str(tmp_path / "outbox.sqlite"))
58 [A,D] def _close(store: SQLiteGraphStore, outbox: DurableOutbox) -> None:
161 [J]             import sqlite3
```

### copilot-sdk/tests/graph/test_sqlite_store.py

Category A; 33 matching lines; test/helper.

```text
3 [J] import sqlite3
8 [A,E] from copilot_sdk.graph import SQLiteGraphStore
12 [A] def _write(store: SQLiteGraphStore, domain: str, index: int, category: str = "alpha") -> str:
41 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
65 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
82 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
88 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
100 [A]     store = SQLiteGraphStore(db_path)
114 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
124 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
142 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
163 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
174 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
185 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
198 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
226 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
239 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
247 [A]     store = SQLiteGraphStore(":memory:")
256 [A]     SQLiteGraphStore(db_path)
262 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
275 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
284 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
292 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
304 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite", domain="mock")
312 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite", domain="mock")
318 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite", domain="mock")
328 [A]     alpha = SQLiteGraphStore(db_path, domain="alpha")
329 [A]     beta = SQLiteGraphStore(db_path, domain="beta")
391 [A]     store = SQLiteGraphStore(db_path, domain="legacy")
406 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
424 [A]     stores = [SQLiteGraphStore(db_path) for _ in range(3)]
427 [A]     def write(store: SQLiteGraphStore, index: int) -> None:
448 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
```

### copilot-sdk/tests/graph/test_verified_count_strict.py

Category A; 4 matching lines; test/helper.

```text
13 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
23 [A]         graph_store = SQLiteGraphStore(tmp_path / "verified-count.sqlite", domain="test")
58 [A]     if isinstance(store, SQLiteGraphStore):
82 [A]     if isinstance(store, SQLiteGraphStore):
```

### copilot-sdk/tests/graph/test_write_outcome_extended.py

Category A; 2 matching lines; test/helper.

```text
10 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
19 [A]         graph_store = SQLiteGraphStore(tmp_path / "extended.sqlite", domain="test")
```

### copilot-sdk/tests/scoring/test_persistence_outbox.py

Category F; 1 matching lines; test/helper.

```text
3 [J] import sqlite3
```

### copilot-sdk/tests/scoring/test_scorer_governed.py

Category F; 4 matching lines; test/helper.

```text
14 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
16 [C,F] from copilot_sdk.graph.dual_write_store import DualWriteStore
83 [A]     store = SQLiteGraphStore(tmp_path / "raw.sqlite", domain="mock", decision_id_prefix="TRD-")
131 [C]     store = DualWriteStore(primary, secondary)
```

### copilot-sdk/tests/scoring/test_storage.py

Category F; 6 matching lines; test/helper.

```text
3 [J] import sqlite3
8 [A,E] from copilot_sdk.graph import SQLiteGraphStore
264 [A]     migrated = SQLiteGraphStore(db_path, domain="mock")
287 [A]     store = SQLiteGraphStore(db_path, domain="mock")
346 [A]     store = SQLiteGraphStore(temp_db, domain="mock")
350 [A]     reopened = SQLiteGraphStore(temp_db, domain="mock")
```

### copilot-sdk/tests/test_age_unification_invariants.py

Category C; 11 matching lines; test/helper.

```text
21 [C,F] from copilot_sdk.graph.dual_write_store import DualWriteStore
23 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
59 [B]     assert not path.exists() or "class DecisionStore" not in path.read_text(encoding="utf-8")
68 [B]     assert not _forbidden_store_imports("DecisionStore", "copilot_sdk.scoring.storage")
73 [A]     assert not _forbidden_store_imports("SQLiteGraphStore", "copilot_sdk.graph.sqlite_store")
79 [J]             if re.search(r"import sqlite3|sqlite3\.connect", path.read_text(encoding="utf-8"))]
135 [A]         store = SQLiteGraphStore(":memory:", domain="trading")
145 [A]         primary = SQLiteGraphStore(":memory:", domain="trading")
146 [A]         secondary = SQLiteGraphStore(":memory:", domain="trading")
149 [C]                 DualWriteStore(primary, secondary)
272 [J]             if path.exists() and ("import sqlite3" in _source(path) or "import aiosqlite" in _source(path))
```

### copilot-sdk/tests/test_archive_reader.py

Category C; 8 matching lines; test/helper.

```text
5 [C,F] from copilot_sdk.graph.dual_write_store import DualWriteStore
7 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
63 [A]     store = SQLiteGraphStore(str(tmp_path / "archive.db"), domain=DOMAIN)
76 [A]     store = SQLiteGraphStore(str(tmp_path / "empty.db"), domain=DOMAIN)
85 [A]     store = SQLiteGraphStore(str(tmp_path / "outcome.db"), domain=DOMAIN)
112 [A]     primary = SQLiteGraphStore(str(tmp_path / "primary.db"), domain=DOMAIN)
114 [C]     store = DualWriteStore(primary, secondary)
123 [A]     store = SQLiteGraphStore(str(tmp_path / "normalized.db"), domain=DOMAIN)
```

### copilot-sdk/tests/test_centroid_refresh.py

Category I; 1 matching lines; test/helper.

```text
2 [J] import sqlite3
```

### copilot-sdk/tests/test_cross_copilot_transfer.py

Category A; 3 matching lines; test/helper.

```text
9 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
13 [A] def _green(store: InMemoryGraphStore | SQLiteGraphStore, domain: str) -> None:
146 [A]         store = SQLiteGraphStore(tmp_path / "transfer.sqlite", domain="trading")
```

### copilot-sdk/tests/test_dual_write_outbox.py

Category C; 13 matching lines; test/helper.

```text
3 [J] import sqlite3
8 [C,F] from copilot_sdk.graph.dual_write_store import DualWriteStore
9 [D,G] from copilot_sdk.graph.outbox import DurableOutbox
29 [D] class FailingDurableOutbox:  # MOCK-OK: forces the durable-storage failure boundary.
37 [C] def _governed_write(store: DualWriteStore, decision_id: str = "DEC-1") -> None:
57 [C] def _store(tmp_path, secondary: RecordingEndpoint) -> tuple[DualWriteStore, RecordingEndpoint]:
59 [C]     return DualWriteStore(primary, secondary, outbox_path=str(tmp_path / "secondary_outbox.db")), primary
157 [D]     outbox = DurableOutbox(str(tmp_path / "outbox.db"))
195 [D]     outbox = DurableOutbox(str(tmp_path / "outbox.db"))
207 [D]     outbox = DurableOutbox(str(path))
211 [D]     restored = DurableOutbox(str(path))
220 [C]     store = DualWriteStore(RecordingEndpoint(), secondary)
232 [D]     store._durable_outbox = FailingDurableOutbox()  # type: ignore[assignment]
```

### copilot-sdk/tests/test_dual_write_store.py

Category C; 25 matching lines; test/helper.

```text
8 [C,F] from copilot_sdk.graph.dual_write_store import DualWriteStore
10 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
48 [C]     dual = DualWriteStore(primary, secondary)
59 [C]     assert DualWriteStore(primary, secondary).write_outcome("d1", "buy", True, domain="trading") is None
65 [C]     DualWriteStore(primary, secondary).write_governed_decision("d1", "trading", "cat", 0, "buy", 0, 0.8, [0.8], [1.0], ["x"])
71 [C]     result = DualWriteStore(primary, secondary).append_evidence_receipt("r1", "trading", "d1", {}, "actor", "route")
78 [C]     dual = DualWriteStore(primary, secondary)
99 [C]     dual = DualWriteStore(primary, secondary)
107 [C]     dual = DualWriteStore(primary, secondary)
116 [C]         DualWriteStore(primary, secondary).write_decision("trading", "cat", "buy", 0.8, {})
129 [C]     dual = DualWriteStore(primary, secondary)
144 [C]     dual = DualWriteStore(primary, secondary)
155 [A]     primary = SQLiteGraphStore(tmp_path / "trading.db", domain=domain)
157 [C]     dual = DualWriteStore(primary, secondary)
176 [C]     DualWriteStore(primary, secondary).domain_scoped_reset("trading")
183 [C]         DualWriteStore(primary, secondary).close()
189 [C]     dual = DualWriteStore(primary, secondary)
199 [C]     dual = DualWriteStore(primary, secondary)
208 [C]     dual = DualWriteStore(primary, secondary)
216 [C]     dual = DualWriteStore(primary, secondary)
230 [C]     dual = DualWriteStore(primary, secondary, max_failures=3)
241 [C]     dual = DualWriteStore(primary, secondary)
244 [C]     restored = DualWriteStore(*_pair(), failure_log_path=str(log_path))
255 [C]         DualWriteStore(primary, PlainGraphStore())
260 [C]     dual = DualWriteStore(primary, secondary)
```

### copilot-sdk/tests/test_entity_enrichment.py

Category A; 13 matching lines; test/helper.

```text
19 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
254 [A] @pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
270 [A] @pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
293 [A] @pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
315 [A] @pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
331 [A] @pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
344 [A]     store = SQLiteGraphStore(":memory:")
358 [A]     store = SQLiteGraphStore(":memory:")
366 [A] @pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
376 [A] @pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
400 [A] @pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
411 [A]     store = SQLiteGraphStore(":memory:")
497 [A] @pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
```

### copilot-sdk/tests/test_factory_dual_write.py

Category D; 11 matching lines; test/helper.

```text
7 [C,F] from copilot_sdk.graph.dual_write_store import DualWriteStore
9 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
35 [C]     assert isinstance(store.graph_primary, DualWriteStore)
49 [H]     store = create_graph_store(profile="test", backend="sqlite", domain="trading", db_path=tmp_path / "trading.db")
50 [A]     assert isinstance(store.graph_primary, SQLiteGraphStore)
70 [C]     assert isinstance(store.graph_primary, DualWriteStore)
71 [A]     assert isinstance(store.primary, SQLiteGraphStore)
84 [C]     assert isinstance(store.graph_primary, DualWriteStore)
99 [C]     assert isinstance(store.graph_primary, DualWriteStore)
130 [C]     assert isinstance(store.graph_primary, DualWriteStore)
170 [C]     assert isinstance(store.graph_primary, DualWriteStore)
```

### copilot-sdk/tests/test_five_domain_completeness.py

Category A; 2 matching lines; test/helper.

```text
14 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
32 [A]         graph_store = SQLiteGraphStore(str(tmp_path / "five_domains.db"), "test", "TEST-")
```

### copilot-sdk/tests/test_gate_preseed_initialization.py

Category G; 5 matching lines; test/helper.

```text
7 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
15 [A] def degraded_store(path: Path) -> SQLiteGraphStore:
16 [A]     store = SQLiteGraphStore(path, domain="trading")
28 [A] def real_scorer(store: SQLiteGraphStore, path: Path, via_proxy: bool) -> Any:
59 [A]     reopened = SQLiteGraphStore(path, domain="trading")
```

### copilot-sdk/tests/test_generate_decision_id.py

Category C; 10 matching lines; test/helper.

```text
5 [C,F] from copilot_sdk.graph.dual_write_store import DualWriteStore
7 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
14 [A]     store = SQLiteGraphStore(tmp_path / "trading.db", domain="trading", decision_id_prefix="TRD-")
24 [A]     store = SQLiteGraphStore(tmp_path / "purchasing.db", domain="purchasing", decision_id_prefix="PUR-")
34 [A]     store = SQLiteGraphStore(tmp_path / "plain.db", domain="test")
46 [A]     primary = SQLiteGraphStore(tmp_path / "trading.db", domain="trading", decision_id_prefix="TRD-")
48 [C]     dual = DualWriteStore(primary, secondary)
58 [A]     store = SQLiteGraphStore(tmp_path / "unique.db", domain="trading", decision_id_prefix="TRD-")
66 [A]     store = SQLiteGraphStore(tmp_path / "governed.db", domain="trading", decision_id_prefix="TRD-")
87 [A]     store = SQLiteGraphStore(tmp_path / "domain.db", domain="trading", decision_id_prefix="TRD-")
```

### copilot-sdk/tests/test_global_queries.py

Category A; 4 matching lines; test/helper.

```text
6 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
12 [A]         SQLiteGraphStore(tmp_path / "global.db", domain="soc"),
30 [A]         if isinstance(store, SQLiteGraphStore):
114 [A]     store = SQLiteGraphStore(tmp_path / f"checkpoint-{include_v2}.db", domain="soc")
```

### copilot-sdk/tests/test_graph_config.py

Category D; 7 matching lines; test/helper.

```text
34 [H] def write_config(path: Path, *, backend: str = "sqlite", expected: str = "sqlite") -> None:
122 [H]     write_config(config_path, backend="sqlite", expected="age")
131 [H]     write_config(config_path, backend="sqlite", expected="age")
135 [H]     assert config.backend == "sqlite"
164 [H]         '[defaults]\nbackend = "sqlite"\nexpected_backend = "sqlite"\n'
223 [H]     write_config(config_path, backend="sqlite", expected="sqlite")
226 [H]     assert config.backend == "sqlite"
```

### copilot-sdk/tests/test_graph_entity_links.py

Category A; 2 matching lines; test/helper.

```text
10 [A,E] from copilot_sdk.graph import GraphStore, InMemoryGraphStore, SQLiteGraphStore
179 [A]     store = SQLiteGraphStore(tmp_path / "graph.sqlite")
```

### copilot-sdk/tests/test_graph_factory.py

Category D; 4 matching lines; test/helper.

```text
7 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
20 [H]         backend="sqlite", domain="test", db_path=tmp_path / "test.db", profile="test"
23 [A]         assert isinstance(store.graph_primary, SQLiteGraphStore)
59 [A]         assert isinstance(store.graph_primary, SQLiteGraphStore)
```

### copilot-sdk/tests/test_graph_production_boundary.py

Category C; 9 matching lines; test/helper.

```text
16 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
35 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory", "dual_write"])
44 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
57 [H]         replace(config, backend="sqlite", expected_backend="sqlite").require_shared_graph()
78 [A]     local = SQLiteGraphStore(":memory:", domain="trading") if kind == "sqlite" else InMemoryGraphStore(domain="trading")
99 [C,F]         from copilot_sdk.graph.dual_write_store import DualWriteStore
103 [C]         dual = object.__new__(DualWriteStore)
118 [H]     for kwargs in ({"backend": "sqlite"}, {"profile": "test"}, {"domain": "s2p"}, {"dsn": "other"}, {"test_mode": True}):
139 [H]     assert loaded.backend == "sqlite"
```

### copilot-sdk/tests/test_graphstore_consolidation.py

Category A; 3 matching lines; test/helper.

```text
4 [J] import sqlite3
7 [A,E] from copilot_sdk.graph import GraphStore, InMemoryGraphStore, SQLiteGraphStore
268 [A]     store = SQLiteGraphStore(db_path)
```

### copilot-sdk/tests/test_historical_checkpoint_import.py

Category A; 2 matching lines; test/helper.

```text
10 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
14 [A]     store = SQLiteGraphStore(tmp_path / "history.db", domain="purchasing")
```

### copilot-sdk/tests/test_jm_conformance.py

Category A; 2 matching lines; test/helper.

```text
13 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
46 [A]         instance = SQLiteGraphStore(str(tmp_path / "conformance.sqlite"), domain=DOMAIN)
```

### copilot-sdk/tests/test_jm_rl_cross_copilot.py

Category A; 2 matching lines; test/helper.

```text
111 [A,E]     from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
113 [A]     store = SQLiteGraphStore(":memory:", domain="test")
```

### copilot-sdk/tests/test_jm_v27_validation.py

Category A; 5 matching lines; test/helper.

```text
15 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
101 [A]         else SQLiteGraphStore(tmp_path / "count.sqlite", domain="validation")
118 [A]         else SQLiteGraphStore(tmp_path / "outcome.sqlite", domain="validation")
148 [A]         else SQLiteGraphStore(tmp_path / "link.sqlite", domain="validation")
169 [A]         assert not isinstance(store, SQLiteGraphStore)
```

### copilot-sdk/tests/test_l5_centroid_storage.py

Category A; 6 matching lines; test/helper.

```text
9 [A,E] from copilot_sdk.graph import GraphStore, InMemoryGraphStore, ProtocolV2GraphStore, SQLiteGraphStore
17 [A]     return SQLiteGraphStore(tmp_path / "l5-centroids.sqlite")
26 [A]     if not isinstance(store, SQLiteGraphStore):
42 [A]     assert hasattr(SQLiteGraphStore, "update_centroid")
43 [A]     assert hasattr(SQLiteGraphStore, "get_centroids")
150 [A]     store = SQLiteGraphStore(tmp_path / "schema.sqlite")
```

### copilot-sdk/tests/test_l5_conservation_storage.py

Category A; 5 matching lines; test/helper.

```text
10 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
55 [A]         sqlite_store = SQLiteGraphStore(tmp_path / "graph.sqlite")
99 [A]     assert callable(SQLiteGraphStore.update_conservation_state)
100 [A]     assert callable(SQLiteGraphStore.get_conservation_state)
141 [A]     if isinstance(store, SQLiteGraphStore):
```

### copilot-sdk/tests/test_l5_dk_weight_storage.py

Category A; 7 matching lines; test/helper.

```text
9 [A,E] from copilot_sdk.graph import GraphStore, InMemoryGraphStore, ProtocolV2GraphStore, SQLiteGraphStore
27 [A]     return SQLiteGraphStore(tmp_path / "l5-dk.sqlite")
36 [A]     if not isinstance(store, SQLiteGraphStore):
60 [A]     assert hasattr(SQLiteGraphStore, "update_dk_weights")
61 [A]     assert hasattr(SQLiteGraphStore, "get_dk_weights")
184 [A]     store = SQLiteGraphStore(tmp_path / "corrupt.sqlite")
201 [A]     store = SQLiteGraphStore(tmp_path / "schema.sqlite")
```

### copilot-sdk/tests/test_l5_dk_welford_storage.py

Category A; 5 matching lines; test/helper.

```text
4 [J] import sqlite3
10 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
30 [A]     return SQLiteGraphStore(tmp_path / "l5-dk-welford.sqlite")
137 [A]     store = SQLiteGraphStore(db_path)
149 [A]     store = SQLiteGraphStore(tmp_path / "partial-welford.sqlite")
```

### copilot-sdk/tests/test_learn_context.py

Category A; 5 matching lines; test/helper.

```text
4 [J] import sqlite3
8 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
70 [A]     graph_store = SQLiteGraphStore(tmp_path / "default-sqlite.sqlite", domain="context-test")
108 [A]     store = SQLiteGraphStore(tmp_path / "store.sqlite", domain="mock")
195 [A]     store = SQLiteGraphStore(db_path, domain="mock")
```

### copilot-sdk/tests/test_legacy_signal_filter.py

Category C; 26 matching lines; test/helper.

```text
11 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
17 [A]         raw = SQLiteGraphStore(path, domain="trading")
35 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
50 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
61 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
75 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
88 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
119 [H] @pytest.mark.parametrize("backend", ["memory", "sqlite", "age", "dual_write"])
191 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
210 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
228 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
257 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
274 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
285 [H]         if backend == "sqlite":
297 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
335 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
364 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
383 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
404 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
429 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
453 [C,F]     from copilot_sdk.graph.dual_write_store import DualWriteStore
457 [C]     store = LegacySignalFilteringGraphStore(DualWriteStore(primary, secondary))
548 [H] @pytest.mark.parametrize("backend", ["sqlite", "memory"])
777 [C,F]     from copilot_sdk.graph.dual_write_store import DualWriteStore
801 [C]     dual = DualWriteStore(primary, secondary)
827 [C]     local_wrapper = LegacySignalFilteringGraphStore(DualWriteStore(local_primary, local_secondary))
```

### copilot-sdk/tests/test_migration_live_age.py

Category I; 1 matching lines; test/helper.

```text
11 [J] import sqlite3
```

### copilot-sdk/tests/test_migration_resilience.py

Category I; 1 matching lines; test/helper.

```text
5 [J] import sqlite3
```

### copilot-sdk/tests/test_outbox_sqlite.py

Category A; 2 matching lines; test/helper.

```text
9 [A,E] from copilot_sdk.graph import SQLiteGraphStore
24 [A]     store = SQLiteGraphStore(tmp_path / "outbox.sqlite", domain="test")
```

### copilot-sdk/tests/test_preseed_gap_supersession.py

Category G; 2 matching lines; test/helper.

```text
10 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
37 [A]     store = SQLiteGraphStore(tmp_path / "gap.db", domain="purchasing")
```

### copilot-sdk/tests/test_quality_axis.py

Category A; 2 matching lines; test/helper.

```text
10 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
142 [A]         SQLiteGraphStore(str(tmp_path / "quality.db")),
```

### copilot-sdk/tests/test_read_diff_runner.py

Category C; 2 matching lines; test/helper.

```text
7 [C,F] from copilot_sdk.graph.dual_write_store import DualWriteStore
89 [C]     dual = DualWriteStore(InMemoryGraphStore(), InMemoryGraphStore())
```

### copilot-sdk/tests/test_reconcile_archive.py

Category A; 2 matching lines; test/helper.

```text
14 [A,E]     from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
15 [A]     source = SQLiteGraphStore(tmp_path / "trading.db", domain="trading")
```

### copilot-sdk/tests/test_rule38_factory_compliance.py

Category D; 4 matching lines; test/helper.

```text
11 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
29 [H]         backend="sqlite",
34 [A]     assert isinstance(store.graph_primary, SQLiteGraphStore)
62 [A]         assert not any(node.func.id == "SQLiteGraphStore" for node in calls), path
```

### copilot-sdk/tests/test_session_regression.py

Category A; 2 matching lines; test/helper.

```text
63 [A,E]     from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
66 [A]     store = SQLiteGraphStore(str(tmp_path / "test.db"), domain="trading")
```

### copilot-sdk/tests/test_signal_store_isolation.py

Category D; 1 matching lines; test/helper.

```text
78 [H]         '[defaults]\nbackend="sqlite"\nexpected_backend="sqlite"\n'
```

### copilot-sdk/tests/test_situation_analyzer.py

Category A; 3 matching lines; test/helper.

```text
24 [A,E] from copilot_sdk.graph import GraphTraversalStore, SQLiteGraphStore
444 [A]     store = SQLiteGraphStore(tmp_path / "graph.db", domain="demo")
465 [A]     store = SQLiteGraphStore(tmp_path / "graph.db", domain="demo")
```

### copilot-sdk/tests/test_snapshot_after.py

Category A; 3 matching lines; test/helper.

```text
7 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
33 [A]     value = InMemoryGraphStore(domain="test") if request.param == "memory" else SQLiteGraphStore(Path(tmp_path) / "jm.db", domain="test")
75 [A]     stores = [InMemoryGraphStore(domain="test"), SQLiteGraphStore(Path(tmp_path) / "parity.db", domain="test")]
```

### copilot-sdk/tests/test_soc_graph_invariant.py

Category D; 2 matching lines; test/helper.

```text
65 [H]             backend="sqlite", graph="local_scratch_graph", domain="trading", profile="production"
71 [H]         backend="sqlite", graph="local_scratch_graph", domain="trading", profile="offline"
```

### copilot-sdk/tests/test_sqlite_to_age_migration.py

Category I; 1 matching lines; test/helper.

```text
3 [J] import sqlite3
```

### copilot-sdk/tests/test_store_parity.py

Category A; 2 matching lines; test/helper.

```text
13 [A,E] from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
24 [A]         SQLiteGraphStore(str(tmp_path / "parity.sqlite"), domain=DOMAIN),
```

### copilot-sdk/tests/test_transfer_pattern.py

Category A; 3 matching lines; test/helper.

```text
9 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
15 [A]         SQLiteGraphStore(tmp_path / "graph.db", domain="soc"),
116 [A]     store = SQLiteGraphStore(tmp_path / "transfer.db", domain="soc")
```

### copilot-sdk/tests/test_worker_process_safety.py

Category A; 7 matching lines; test/helper.

```text
12 [A,E] from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
46 [A]     store = SQLiteGraphStore(path, domain="purchasing")
61 [A]     store = SQLiteGraphStore(path, domain="purchasing")
73 [A]     store = SQLiteGraphStore(path + ".target", domain="purchasing")
97 [A]     store = SQLiteGraphStore(str(path) + ".target", domain="purchasing")
134 [A]     store = SQLiteGraphStore(path, domain="purchasing")
152 [A]     store = SQLiteGraphStore(path, domain="purchasing")
```

### copilot-sdk/tests/vld_validation_report.py

Category A; 4 matching lines; test/helper.

```text
7 [A] SQLiteGraphStore. SOC has no local checkpoint: its real CompoundingScorer uses
25 [J] import sqlite3
224 [A,E]     from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
238 [A]     store = SQLiteGraphStore(":memory:", domain=domain)
```
