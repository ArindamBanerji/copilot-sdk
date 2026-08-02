# JM v2.7 Phase A-C Post-Implementation Review

## §1 EXECUTIVE SUMMARY

| Area | Verdict |
|---|---|
| Line-by-line verdict | **FAIL_NEEDS_FIXER** |
| Architecture verdict | **FAIL_NEEDS_FIXER** |
| Blast radius | **CONCERNS** |
| Design alignment | **GAP** |

The reviewed SDK/AGE changes are not ready for closure. The focused regression
set passed: `48 passed` for the strict-count, outbox, projection, and no-amend
tests. That evidence supports the local behavior covered by those tests, but it
does not close the active SOC path or the default AGE outbox path.

The blocking findings are:

1. The active SOC `AGEClient` still counts verified decisions with the removed
   outcome fallback and counts correct decisions without a status predicate
   (`ci-platform/ci_platform/graph/age_client.py:720-747`). SOC startup calls
   those methods through the client (`gen-ai-roi-demo-v4-v50/backend/app/main.py:343-344`),
   so the Phase A invariant is not universal.
2. The default scorer setting leaves governed writes disabled unless
   `SCORER_GOVERNED_WRITES=1` (`copilot-sdk/copilot_sdk/scoring/scorer.py:63-72`).
   In that default raw-write path the queued payload carries the original ID
   only inside metadata (`scorer.py:370-381`), while AGE `write_decision`
   generates a new ID and ignores that metadata identity (`ci-platform/ci_platform/graph/age_graph_store.py:558-575`).
   Replay therefore cannot preserve the ID returned to the caller.
3. The policy says historical SOC rows with `d.correct` but no Outcome node
   are counted (`copilot-sdk/docs/design/no_amend_outcome_policy_v1.md:57-67`),
   but the Phase A AGE count requires both status and correct
   (`ci-platform/ci_platform/graph/age_graph_store.py:2176-2185`). The
   documented mixed topology and the implemented counting model disagree.

The evolution-edge implementation itself is domain-checked and deduplicated,
and the projection injection, bundle status materialization for explicit
boolean outcomes, and backfill refusal logic are substantially correct. They
still need the residual issues in §6 resolved before the overall verdict can
be PASS_WITH_P3.

## §2 LINE-BY-LINE REVIEW

All files below were read to EOF. “Full” means the complete file was read, not
just the cited excerpt.

| File | Lines reviewed | Verdict | Findings |
|---|---:|---|---|
| `ci-platform/ci_platform/graph/age_graph_store.py` | Full, 3291 lines | PARTIAL | `count_verified_decisions` and `count_correct` are status-scoped and domain/archival scoped (`:2163-2188`); the separate `count_categories_with_n` retains an outcome fallback (`:2201-2219`). Evolution linking is domain-scoped and deduplicated (`:1750-1777`). |
| `copilot-sdk/copilot_sdk/graph/memory_store.py` | Full, 2061 lines | PARTIAL | `count_verified_decisions` is status-only and `count_correct` is status plus exact Python `True` (`:1146-1166`). `count_categories_with_n` still accepts an outcome-only decision (`:1171-1183`). The evolution edge checks domain and deduplicates (`:876-901`). Domain reset clears in-memory outbox state (`:1700-1783`). |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py` | Full, 3539 lines | PARTIAL | Count methods use status-only predicates; correct also requires `correct = 1` (`:2249-2277`). SQLite evolution persistence validates the decision domain and is retry-idempotent by `event_id` (`:1894-1974`, `:1976-1985`). Category coverage still uses `OR o.decision_id IS NOT NULL` (`:3161-3177`). |
| `copilot-sdk/copilot_sdk/graph/protocol.py` | Full, 432 lines | PASS | `write_evolution_event` adds only an optional `decision_id` (`:283-298`), preserving existing callers. |
| `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py` | Full, 219 lines | PARTIAL | Persistent failed-artifact storage and uniqueness are present (`:30-81`); decision/evolution replay dispatch exists (`:176-204`). Replay does not repair a raw AGE decision ID mismatch, and no store-reset hook clears this persistent DB. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py` | Full, 2176 lines | PARTIAL | Score returns normally after decision-write failure and records an outbox item (`:363-393`). Learn calls `write_outcome` without a catch (`:692-698`), preserving fail-closed behavior. The raw path does not put `decision_id` at the top-level payload (`:370-381`). Outbox drains during construction (`:164-171`). |
| `copilot-sdk/copilot_sdk/evolution/ledger.py` | Full, 100 lines | PARTIAL | Evolution failures are queued (`:52-69`), but the payload contains no `decision_id` (`:44-51`), so normal ledger-created events cannot use the new Decision→Evolution edge. |
| `copilot-sdk/tests/scoring/test_outbox_decision_evolution.py` | Full, 158 lines | PARTIAL | Tests prove normal return, queue/drain, evolution queue/drain, and fail-closed learn (`:88-158`). They use a stateful failing store, but do not exercise raw AGE replay identity or reset persistence. |
| `copilot-sdk/copilot_sdk/graph/projection.py` | Full, 333 lines | PASS_WITH_P3 | No direct `AGEClient` import/construction remains. Constructor requires an injected client and authorizes the graph (`:235-255`); mutation queries are rejected (`:257-266`). Count predicates include status, correct, domain, and archive guards (`:268-289`). The predicate is duplicated rather than imported from a shared source (`:90-99`, `:268-287`). |
| `copilot-sdk/tests/graph/test_projection_lifecycle.py` | Full, 103 lines | PASS | Injection, no direct client, unauthorized graph, read-only rejection, domain predicate, status/correct rendering, and token substitution are covered (`:22-103`). No real factory-owned client integration is exercised. |
| `copilot-sdk/tests/graph/test_soc_age_projection_contract.py` | Full | PASS_WITH_P3 | Projection contract coverage was read in full; it complements, but does not replace, a live factory/client integration test. |
| `copilot-sdk/copilot_sdk/demo/bundle.py` | Full, 304 lines | PARTIAL | Explicit boolean outcomes materialize `confirmed`/`overridden` (`:88-106`). `_verified_outcomes` admits any `verified is True` record (`:200-206`), and `_outcome_values` coerces missing or `None` correctness through `bool(..., True)` (`:242-258`); malformed verified rows can become confirmed/overridden instead of remaining pending. |
| `copilot-sdk/scripts/backfill_d_correct.py` | Full, 188 lines | PASS_WITH_P3 | Explicit true/false encodings are the only values written (`:55-74`); unclassifiable rows are counted and block apply unless `--force` (`:77-140`, `:149-162`). The timing note is present at `:6-13`. No test was found for malformed encodings against a live AGE connection. |
| `copilot-sdk/scripts/scan_forbidden_patterns.py` | Full, 734 lines | PARTIAL | The property-scoped rule and allowlisted writer are implemented (`:641-674`). Detection is limited to literal `d.correct`/`d.status` and `d["correct"]`/`d["status"]` forms (`:65-73`); aliases and other equivalent property-write forms are not structurally detected. |
| `copilot-sdk/docs/design/age_unification_forbidden_patterns_allowlist.toml` | Full, 67 lines | PASS_WITH_P3 | The sole allowlist file is the AGE `write_outcome` file entry (`:63-66`). It is file-scoped, with enforcement additionally checking the enclosing function in the scanner (`scan_forbidden_patterns.py:657-662`). |
| `copilot-sdk/tests/graph/test_verified_count_strict.py` | Full, 166 lines | PASS_WITH_P3 | Ten strict-count tests cover memory/SQLite and gated AGE cases. They prove status-only verified counting and status+correct counting locally; they do not cover the active SOC `AGEClient` counter. |
| `copilot-sdk/tests/graph/test_evolution_event_links.py` | Full, 77 lines | PASS_WITH_P3 | Three tests cover linked, unlinked, and cross-domain events for Memory/SQLite (`:65-77`). They do not exercise the AGE Cypher edge or a production ledger caller. |
| `copilot-sdk/tests/graph/test_no_amend_policy.py` | Full, 119 lines | PASS_WITH_P3 | Re-triage, non-pending rejection, and archive/count behavior are covered (`:84-119`). AGE cleanup uses unscoped `MATCH (n) DETACH DELETE n` (`:38-42`), which is unsafe if a shared test graph is reused concurrently. |
| `copilot-sdk/tests/test_rule72_sdk_enforcement.py` | Full, 200 lines | PASS | Evolution capability checks are allowlisted as intended; no source behavior change was found. |
| `copilot-sdk/tests/test_scanner_domain_scope.py` | Full, 99 lines | PASS_WITH_P3 | The projection line allowlist was updated, but this test checks allowlist line metadata rather than proving scanner behavior against an unauthorized property writer. |
| `copilot-sdk/tests/test_dual_write_store.py` | Full | PASS_WITH_P3 | Dual-write evolution signature propagation is present in the implementation (`copilot-sdk/copilot_sdk/graph/dual_write_store.py:391-392`); existing coverage calls the optional parameterless form (`:88-90`). |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py` | Full | PASS | Adapter signature and forwarding include optional `decision_id` (`:247-275`). |
| `gen-ai-roi-demo-v4-v50/backend/app/db/graph_client.py` | Full, 65 lines | PARTIAL | The renamed module resolves GraphConfig and constructs the AGE client (`:25-60`). The returned object is the legacy `AGEClient`, not the Phase A `AGEGraphStore`, so the active SOC path retains the legacy counter behavior. |
| `gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py` | Full, 8 lines | PASS_WITH_P3 | Backward-compatible wildcard re-export and alias are present (`:1-8`). Wildcard re-export is less explicit than a named compatibility surface. |
| `gen-ai-roi-demo-v4-v50/backend/tests/test_graph_client_conformance.py` | Full, 41 lines | PASS | Tests GraphConfig, `soc_graph`, no Neo4j package, and alias identity (`:10-41`). |
| SOC import-renamed files | Full read of all 52 files containing the renamed import | PASS_WITH_P3 | The source import set points to `app.db.graph_client`; the legacy module remains only as a compatibility wrapper. The full list is in §8. No stale production import to a separate implementation was found. |

The SOC import-renamed files read in full were: `app/connectors/crowdstrike_mock.py`,
`app/connectors/greynoise.py`, `app/connectors/pulsedive.py`, `app/data/alert_pool.py`,
`app/db/neo4j.py`, `app/framework/audit.py`, `app/routers/admin.py`,
`app/routers/cohort_status_router.py`, `app/routers/discoveries_router.py`,
`app/routers/evolution.py`, `app/routers/graph.py`, `app/routers/judgment.py`,
`app/routers/metrics.py`, `app/routers/simulation.py`, `app/routers/soc.py`,
`app/routers/time_machine_router.py`, `app/routers/triage.py`,
`app/services/evidence_room.py`, `app/services/executive_narrative.py`,
`app/services/governance_report.py`, `app/services/graph_explorer.py`,
`app/services/iks.py`, `app/services/learning_health.py`, `app/services/model_swap.py`,
`app/services/override_detector.py`, `app/services/rl_engine.py`,
`app/services/shadow_runner.py`, `app/services/simulation.py`,
`app/services/snapshots.py`, `app/services/state_manager.py`,
`app/services/timestamp_backfill.py`, `app/services/triage.py`,
`app/services/variant_generator.py`, `app/main.py`,
`scripts/ingest_synthetic_decisions.py`, `scripts/migrate_datetime_to_epoch.py`,
`scripts/run_sentinel_mock.py`, `scripts/seed_verified_decisions.py`,
`support/setup/repair_zero_day_timestamps.py`, `tests/test_cold_start_guards.py`,
`tests/test_data_integrity.py`, `tests/test_fix_05_06_07.py`,
`tests/test_graph_backend_switcher.py`, `tests/test_graph_client_conformance.py`,
`tests/test_graph_contract_stress.py`, `tests/test_shadow_runner.py`,
`tests/test_soc_domain_isolation.py`, `cleanup_decisions.py`, `conftest.py`,
`diagnose_decisions.py`, `ingest_shadow_decisions.py`, and `seed_neo4j.py`.

## §3 ARCHITECTURE AUDIT

### Abstraction consistency

Projection injection follows the factory/config boundary: the projection accepts
an authorized client and checks `require_shared_graph` (`projection.py:238-255`).
The evolution edge follows the store edge pattern and uses optional matching to
avoid duplicates (`age_graph_store.py:1761-1768`). Outbox dispatch follows the
existing artifact-type pattern (`persistence_outbox.py:183-204`). These portions
are conformant.

### State/reset integrity

The in-memory domain reset removes the domain's in-memory outbox
(`memory_store.py:1779-1783`), but the scorer creates a persistent outbox under
`~/.ci-platform/<domain>/outbox.db` (`persistence_outbox.py:30-46`) and only
drains it when the scorer is constructed (`scorer.py:164-171`). No canonical
domain-reset hook is present in `PersistenceOutbox`. A reset can therefore leave
queued artifacts to replay into a newly reset graph. **P2.**

### Graph/store integrity

The three principal stores now agree on status-scoped verified/correct counts:
AGE (`age_graph_store.py:2163-2188`), SQLite (`sqlite_store.py:2252-2277`), and
Memory (`memory_store.py:1149-1166`). The active SOC `AGEClient` is an exception:
its verified predicate retains the outcome fallback and its correct predicate
has no status guard (`age_client.py:720-747`). `graph_client.py:52-60` constructs
that client, and SOC startup calls its counters (`backend/app/main.py:343-344`).
This is a P1 integrity failure, not merely a stale helper.

### Formula/gate consistency

The intended formula requires α, q, and V to describe the same verified
population (`judgment_memory_v2_7.md:425-444`). The Phase A predicates make
`correct ⊆ verified` in the three principal stores. However, the active SOC
client can count correct rows without status, and all three store-level category
coverage methods retain outcome-only fallbacks (`age_graph_store.py:2201-2219`,
`memory_store.py:1171-1183`, `sqlite_store.py:3161-3177`). This leaves formula
population drift in live/secondary paths. **P1 for the active SOC path; P2 for
the category coverage methods.**

### Framework drift

The optional `decision_id` is consistently added to protocol, Memory, SQLite,
AGE adapter, AGE store, and DualWriteStore (`protocol.py:283-297`,
`age_sdk_adapter.py:247-275`, `dual_write_store.py:391-392`). Existing callers
remain source-compatible. No protocol drift was found in this change.

### Fixture/live-data integrity

Bundle restore writes the same status mapping for explicit boolean outcomes as
`write_outcome` (`bundle.py:88-106`; Memory outcome transition at
`memory_store.py:575-587`). The malformed-row case is not equivalent: a verified
record with missing/`None` `is_correct` is coerced through `bool` in
`bundle.py:242-258` rather than remaining pending as required by the lifecycle
mapping (`judgment_memory_v2_7.md:409-412`). **P2.**

The AGE conformance fixture uses a real AGE adapter when availability is enabled,
not a mock (`tests/graph/test_no_amend_policy.py:18-42`). The evolution link
tests themselves cover only Memory/SQLite (`test_evolution_event_links.py:18-34`).

### Duplication

`projection.py` defines its own status/domain/correct predicate
(`:90-99`) instead of importing a canonical predicate from the AGE store. The
rendered output currently matches the intended text and tests assert the status
and correct fragments (`test_projection_lifecycle.py:74-95`), but future changes
can drift. **P3.**

### Test architecture

The new tests use stateful stores and prove local behavior, including outbox
drain and no-amend transitions. They do not prove the default raw AGE replay
identity, active SOC legacy counters, persistent-outbox reset, or production
ledger-to-decision evolution linkage. Passing tests therefore under-cover the
highest-risk paths identified above.

**Architecture verdict: FAIL_NEEDS_FIXER.**

## §4 BLAST RADIUS

| Change | Downstream impact | Verdict |
|---|---|---|
| Count status guards | Principal Memory/SQLite/AGE stores satisfy `correct <= verified`; active SOC `AGEClient` and category coverage remain divergent. | CONCERN — P1/P2 |
| Decision outbox | Score response remains non-blocking (`scorer.py:367-393`), but default raw AGE replay can write a different decision ID than the returned ID (`scorer.py:63-72`, `:370-381`; `age_graph_store.py:567-575`). | CONCERN — P1 |
| Evolution outbox/edge | Edge creation is safe when `decision_id` is provided; normal `InMemoryEvolutionLedger` payloads omit it (`ledger.py:44-54`). | CONCERN — P2 |
| Projection injection | Direct AGE client construction is removed and read-only rejection remains. | CLEAN, with P3 duplication risk |
| SOC rename | Imports converge on `graph_client`; legacy module aliases the same object (`neo4j.py:7-8`, conformance test `:33-41`). | CLEAN |
| Bundle restore | Explicit true/false rows are materialized correctly; malformed verified rows are not lifecycle-safe. | CONCERN — P2 |
| Backfill and scanner | Backfill is explicit and guarded; scanner patterns are syntactic and narrower than a full property-write AST rule. | CONCERN — P2/P3 |

## §5 DESIGN ALIGNMENT

| Design decision | Implemented correctly? | Evidence |
|---|---|---|
| C1: `write_outcome` is sole writer of `d.correct`/`d.status` | **PARTIAL** | AGE contract writer is allowlisted (`scan_forbidden_patterns.py:657-662`, TOML `:63-66`), but the active SOC legacy API still reads/counts the same properties outside the principal store contract (`age_client.py:720-747`). The scanner’s mutation detector only recognizes literal `d` forms (`scan_forbidden_patterns.py:65-73`). |
| C2: no independent correctness writer | **PARTIAL** | Principal AGE/Memory/SQLite outcome writes are aligned (`age_graph_store.py:886-984`, `memory_store.py:549-598`, `sqlite_store.py:1175-1247`), but the review cannot claim universal closure because the scanner does not structurally detect aliases/equivalent writes. |
| C3: count predicates are property/status based | **PARTIAL** | Principal counts match the model, but active SOC `AGEClient.count_correct_decisions` lacks status (`age_client.py:737-747`), and category coverage retains outcome fallback in all stores (`age_graph_store.py:2201-2219`, `memory_store.py:1171-1183`, `sqlite_store.py:3161-3177`). |
| No-amend/write-once | **PASS_WITH_P3** | Store outcome methods reject non-pending rows; the no-amend tests assert rejection and preserved state (`test_no_amend_policy.py:99-109`). |
| Re-triage/archive mechanic | **PASS_WITH_P3** | The test creates two outcomes, archives the first, checks active counts, and checks archive visibility (`test_no_amend_policy.py:84-96`). The AGE cleanup is broad (`:38-42`). |
| E3 property-scoped ban | **PARTIAL** | The allowlisted writer and property scope are present (`scan_forbidden_patterns.py:641-674`, TOML `:63-66`), but pattern matching is not an AST/property-resolution guarantee. |
| §12b Score failure policy | **PARTIAL** | The score path returns normally and queues (`scorer.py:363-393`), but raw AGE replay does not preserve the returned decision ID. |
| §12b Learn failure policy | **PASS** | `write_outcome` is not caught in `learn` (`scorer.py:692-698`). |
| §12b Evidence/evolution queue | **PASS_WITH_P2** | Evidence records through outbox on failure (`scorer.py:1187-1201`); evolution ledger queues (`ledger.py:52-69`), but no decision ID is propagated for the new edge. |
| Rule #37 V=verified only | **FAIL** | Principal stores are corrected, but active SOC uses the legacy fallback (`age_client.py:720-731`; startup call `backend/app/main.py:343-344`). |
| Historical SOC mixed topology | **FAIL** | The policy says `d.correct`-only historical rows are counted (`no_amend_outcome_policy_v1.md:57-67`), while the new AGE principal count requires status (`age_graph_store.py:2176-2185`). |

## §6 P1/P2/P3 FINDINGS

### P1 BUGS

**P1-1 — Active SOC counters still violate Rule #37 and `correct ⊆ verified`.**

`AGEClient.count_verified_decisions` explicitly retains
`d.status IS NULL AND d.outcome IS NOT NULL` (`ci-platform/ci_platform/graph/age_client.py:720-731`),
and `count_correct_decisions` counts `d.correct = true` without status
(`age_client.py:737-747`). SOC startup uses those methods through the client
(`gen-ai-roi-demo-v4-v50/backend/app/main.py:343-344`), whose construction comes
from `get_graph_client` (`gen-ai-roi-demo-v4-v50/backend/app/db/graph_client.py:52-60`).
This can make the active SOC population differ from the Phase A store population
and can make the conservation ratio exceed the intended verified population.

**P1-2 — Default raw AGE decision replay loses the score’s decision identity.**

`_resolve_governed_writes(None)` is false unless an environment variable is set
(`copilot-sdk/copilot_sdk/scoring/scorer.py:63-72`). The raw score payload puts
the generated ID only in `metadata` (`scorer.py:370-381`), and the outbox replays
it through `write_decision` (`persistence_outbox.py:191-196`). AGE’s raw
`write_decision` always creates `DEC-<random>` (`ci-platform/ci_platform/graph/age_graph_store.py:558-575`),
so a failed write followed by replay creates a different node from the ID
returned by `score`. A subsequent `learn` for the returned ID cannot reliably
find the replayed decision. This directly violates the §12b idempotency intent
(`judgment_memory_v2_7.md:1043-1046`).

**P1-3 — Historical SOC policy contradicts the implemented count model.**

The policy records that historical SOC Decisions may have only `d.correct` and
that `count_correct` counts both historical and new topologies
(`copilot-sdk/docs/design/no_amend_outcome_policy_v1.md:57-67`). The principal
AGE count now requires status and correct (`ci-platform/ci_platform/graph/age_graph_store.py:2176-2185`),
so `d.correct`-only historical rows are excluded there. The legacy active SOC
counter does the opposite (`ci-platform/ci_platform/graph/age_client.py:737-747`).
There is no single authoritative result for the documented mixed topology.

### P2 ISSUES

**P2-1 — Persistent outbox is outside the canonical reset path.**

The persistent DB is created under the user profile (`persistence_outbox.py:30-46`)
and drained at scorer construction (`scorer.py:164-171`). Memory domain reset
clears only its own list (`memory_store.py:1779-1783`). No corresponding
`PersistenceOutbox` reset is present, so a domain reset can leave artifacts for
later replay.

**P2-2 — Bundle restore can turn an indeterminate verified record into a terminal status.**

`_verified_outcomes` accepts `verified=True` without requiring a boolean
`is_correct` (`bundle.py:200-206`), and `_outcome_values` uses `bool` with a
default of true (`bundle.py:242-258`). The lifecycle contract says
`is_correct IS NULL` remains pending (`judgment_memory_v2_7.md:409-412`).

**P2-3 — Evolution edge capability is not wired from the normal ledger path.**

The stores support `decision_id` and create a safe edge when present
(`age_graph_store.py:1750-1777`; `memory_store.py:876-901`), but the standard
ledger payload contains only event/domain/rule metadata (`copilot_sdk/evolution/ledger.py:44-54`).
The new edge is therefore optional in implementation but absent for normal
ledger-created evolution events. The tests cover only Memory/SQLite and do not
exercise the AGE edge (`tests/graph/test_evolution_event_links.py:18-34`, `:65-77`).

**P2-4 — Category coverage still has the removed outcome fallback.**

All three store-level category-count methods accept an outcome without status
(`age_graph_store.py:2201-2219`, `memory_store.py:1171-1183`,
`sqlite_store.py:3161-3177`). The locked formula defines α as category coverage
among verified decisions (`judgment_memory_v2_7.md:436-441`).

**P2-5 — Scanner enforcement is syntactic rather than property-scoped semantically.**

The E3 rule detects literal `d.correct`, `d.status`, and `d["correct"]` forms
(`scan_forbidden_patterns.py:65-73`) and checks the allowlist/enclosing function
(`:657-662`). It does not resolve aliases, f-string expressions, or equivalent
mapping/property writes. A forbidden write can therefore avoid the rule without
being a legitimate archival mutation.

### P3 ITEMS

**P3-1 — Projection predicates are duplicated.** `d2_predicate` is local to the
projection (`projection.py:90-99`) while AGE has its own domain clause
(`age_graph_store.py:553-556`). Current tests prove the rendered fragments, not
source-level identity (`test_projection_lifecycle.py:83-103`).

**P3-2 — AGE cleanup in no-amend tests is unscoped.** The fixture executes
`MATCH (n) DETACH DELETE n` (`test_no_amend_policy.py:38-42`) rather than a
domain-scoped disposable-graph cleanup.

**P3-3 — Full scanner execution was not independently completed in this review.**
The full repository scanner exceeded the available execution window and was
terminated; therefore this review makes no claim that its final process result
was PASS. Static evidence for the rule is cited above.

## §7 FIXER NEEDED: YES

Minimal fixer scope:

1. Route SOC conservation/count reads through the corrected AGE graph-store
   contract, or update the active legacy `AGEClient` methods to the same
   status-only predicates and explicitly reconcile historical SOC rows.
2. Make raw AGE decision writes accept/use the caller-supplied decision ID, or
   force the governed/idempotent path for production and test the failure →
   replay → learn sequence.
3. Resolve the historical SOC mixed-topology policy: either status-backfill the
   historical rows or define a separate explicit historical counting query; do
   not claim both topology types are handled by the same status-guarded property
   count without evidence.
4. Add tests for persistent-outbox reset, malformed bundle correctness, AGE
   evolution edge creation from the production path, and active SOC counter
   semantics. Then strengthen the E3 scanner for equivalent property writes.

## §8 READING LOG

Read to EOF:

- `copilot-sdk/docs/design/judgment_memory_v2_7.md`
- `copilot-sdk/docs/design/no_amend_outcome_policy_v1.md`
- `copilot-sdk/docs/design/jm_v27_post_fix_review_s1.md`
- `copilot-sdk/docs/design/jm_v27_post_fix_review_s2.md`
- `copilot-sdk/docs/design/jm_v27_post_fix_review_s3.md`
- `copilot-sdk/CLAUDE.md`
- `ci-platform/CLAUDE.md`
- All implementation and test files listed in §2, including the full SOC
  import-renamed file set listed there.

Verification performed without source changes:

- `python -m pytest tests/graph/test_verified_count_strict.py tests/scoring/test_outbox_decision_evolution.py tests/graph/test_projection_lifecycle.py tests/graph/test_no_amend_policy.py -q --timeout=120`
  → **48 passed**.
- The full forbidden-pattern scan was started but exceeded the execution window
  and was terminated; no scanner PASS claim is made.

READY: NO
