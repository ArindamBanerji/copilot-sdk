# Skipped-Test Queue Design v1

**Status:** diagnostic/design only; no source or test changes made by this analysis  
**Scope:** six queue items listed in `docs/design/skipped_test_queue_executable_v1.md`  
**Repository state inspected:** 2026-08-12

## Executive conclusion

The queue metadata says “9 tests,” but the current skip inventory contains **10 distinct tests**:

| Queue item | Tests |
|---|---:|
| PROTO-V2 | 4 |
| AGE-STRESS | 1 |
| SOC-BACKFILL | 1 |
| SOC-WRITE-PATH | 1 |
| SHADOW-MAP | 1 |
| S2P-DOMAIN-PANEL | 2 |
| **Total found in source** | **10** |

This is a queue accounting defect. The implementation plan below keeps all ten source tests in scope; it does not silently omit either domain-panel test.

The reuse claims are mostly valid, but they are lower-level primitives rather than completed queue features. The largest dependency is the V contract: forward Protocol-v2 commits and historical SOC backfill must agree that V is the number of distinct, canonical, verified decisions, counted once. AGE-STRESS is not covered by the existing lifecycle fix: the client is now protected against concurrent initialization/disposal, but pool exhaustion still requires a bounded, fail-closed stress contract.

Recommended order:

1. Freeze the V/idempotency contract and confirm the seed timestamp contract.
2. Run AGE-STRESS against the current pool behavior; fix only if the bounded-failure assertion fails.
3. Implement PROTO-V2 over the existing outbox.
4. Implement SOC-BACKFILL against the agreed V contract.
5. Implement SOC-WRITE-PATH and SHADOW-MAP in parallel.
6. Implement S2P-DOMAIN-PANEL with the existing fail-closed fault-injection surface.

## 1. Exact test inventory

The following locations were obtained from the skip decorators and test bodies, not from the queue summary.

| Queue ID | Repository | Exact location | Test name | Current skip condition/reason |
|---|---|---|---|---|
| PROTO-V2 | `copilot-sdk` | `tests/graph/test_protocol_v2_service_layer.py:9` | `test_api_learn_committed` | Module-level `pytestmark`: `Protocol v2 implementation pending` |
| PROTO-V2 | `copilot-sdk` | `tests/graph/test_protocol_v2_service_layer.py:15` | `test_api_learn_pending_sync` | Same module-level skip |
| PROTO-V2 | `copilot-sdk` | `tests/graph/test_protocol_v2_service_layer.py:21` | `test_pending_sync_no_V_increment` | Same module-level skip |
| PROTO-V2 | `copilot-sdk` | `tests/graph/test_protocol_v2_service_layer.py:27` | `test_replay_then_V_increments` | Same module-level skip |
| AGE-STRESS | `copilot-sdk` | `tests/graph/test_protocol_v2_conformance.py:3002` | `test_concurrent_cross_domain` | `AGE_CROSS_DOMAIN_CONCURRENCY_PENDING`: cross-domain concurrency/isolation stress coverage pending |
| SOC-BACKFILL | `copilot-sdk` | `tests/graph/test_soc_age_projection_contract.py:206` | `test_soc_partial_outcome_backfill_does_not_double_count_V` | Requires canonical SOC Outcome backfill data; backfill design pending |
| SOC-WRITE-PATH | `copilot-sdk` | `tests/graph/test_soc_age_projection_contract.py:315` | `test_soc_triggered_evolution_forward_write_required` | Read-only projection cannot prove forward writes; write-path slice pending |
| SHADOW-MAP | `copilot-sdk` | `tests/graph/test_soc_age_projection_contract.py:333` | `test_soc_shadow_decision_not_automatically_observation` | ShadowDecision-to-Observation mapping intentionally deferred; no auto-promotion |
| S2P-DOMAIN-PANEL | `gen-ai-roi-demo-v4-v50` | `frontend/tests/e2e/s2p_polish.spec.ts:22` | `domain applicability panel is visible in Tab 6` | Explicit unconditional `test.skip` |
| S2P-DOMAIN-PANEL | `gen-ai-roi-demo-v4-v50` | `frontend/tests/e2e/s2p_polish.spec.ts:45` | `domain applicability remains visible when S2P backend is unavailable` | Requires SOC up and S2P down; intended for controlled stack |

The `test_protocol_v2_service_layer.py` module skip means removing an individual decorator is not sufficient; the module-level mark must be replaced by a queue-specific readiness gate or removed when the service is implemented.

## 2. Reuse verification

### 2.1 PROTO-V2

The claimed outbox foundation exists.

| Claimed component | Finding | Evidence |
|---|---|---|
| Durable persistence outbox | Exists | `copilot_sdk/scoring/persistence_outbox.py:36`, `PersistenceOutbox` |
| Failure persistence | Exists | `record_failure` at `persistence_outbox.py:138`; SQLite `failed_artifacts` table is created near lines 50–102 |
| Pending enqueue | Exists | `enqueue` at line 193; it accepts an idempotency key and creates pending rows |
| Replay/drain | Exists | `drain` at line 226; rows are ordered and replayed by artifact type |
| Retry/abandon policy | Exists | `MAX_RETRIES=10` at line 39; drain updates retry state and abandons terminal rows |
| Periodic worker primitive | Exists | `start_periodic_drain` at line 369 and `stop_periodic_drain` at line 398 |
| Scorer wiring | Exists | `copilot_sdk/scoring/scorer.py:30,165-166,1183-1186,2439`; `CompoundingScorer` owns `_outbox`, drains it, and records failed artifacts |
| Replay/learn test | Exists | `tests/scoring/test_outbox_decision_evolution.py:130`, `test_learn_finds_replayed_decision` |
| Existing outbox tests | Exists | `tests/scoring/test_persistence_outbox.py` contains 30+ tests covering failure, enqueue, retry, idempotency, drain, periodic drain, and fail-closed outcome behavior |

The gap is not persistence. The existing outbox is an artifact replay mechanism. It does not yet define a Protocol-v2 API-level result (`committed` versus `pending_sync`), a confirmed-commit token, or the exact point at which V is allowed to advance. It also contains both a `PersistenceOutbox` and other durable-outbox abstractions in the SDK/graph layer; the implementation must select the existing `PersistenceOutbox` path rather than introduce a third replay loop.

### 2.2 SOC-WRITE-PATH

The write primitive exists in the shared graph layer:

- `ci-platform/ci_platform/graph/age_graph_store.py:2032` defines `write_evolution_event`.
- `ci-platform/ci_platform/graph/age_sdk_adapter.py:272-287` forwards `write_evolution_event` to the graph store.
- The dual-write store also forwards evolution events (`copilot-sdk/copilot_sdk/graph/dual_write_store.py`, `write_evolution_event` wrapper).
- `age_client.py` contains the legacy `TRIGGERED_EVOLUTION` relationship write at approximately lines 976–1072, including `verified_correct`, `timestamp_epoch`, and `created_at` properties.

The missing piece is a projection/verifier that proves the write is observable through the canonical read path. A test that only queries pre-seeded edges would not cover this queue item.

### 2.3 SHADOW-MAP

Shadow infrastructure exists in the SOC backend:

- `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py:141`, `fill_shadow_outcome` fills a buffered shadow comparison.
- `backend/app/routers/triage.py:2680-2681` invokes it after a qualifying verified outcome.
- `backend/app/routers/soc.py:2129-2148` reads `ShadowDecision` nodes for analyst benchmarking, using source `v_shadow_synthetic_v3`.
- The existing F9 report describes a 1,500-decision synthetic benchmark, but the live AGE count query could not be executed in this session because WSL returned `E_ACCESSDENIED`. The source and endpoint contract establish that the dataset is expected; they do not prove the live row count.

The missing piece is intentionally the promotion policy. `fill_shadow_outcome` is an outcome-fill operation, not a ShadowDecision-to-Observation promotion rule. The new feature must preserve provenance and must not auto-promote merely because a shadow outcome exists.

### 2.4 S2P-DOMAIN-PANEL

The exact SOC test expectations exist, but a reusable panel was not found in the inspected frontend sources. The current `s2p_polish.spec.ts` expects:

- `Domain Applicability`;
- `Nine domains, one engine.`;
- domain status content including S2P and one or more of Trading, Purchasing, or DataOps;
- the same panel to remain visible while the S2P backend is unavailable.

The S2P preview/front-end and SOC platform already expose adjacent preview/config and health surfaces, but no existing component matching these panel semantics was found. Therefore the queue’s “reuse shared harness” claim is valid for fault injection, not for the panel itself. The panel is new UI work; it should reuse the existing same-origin API/proxy and the existing frontend test route.

## 3. Dependency confirmations

### 3.1 PROTO-V2 versus SOC-BACKFILL and V

The codebase has a canonical count query, but not a single shared V-increment function:

- `ci-platform/ci_platform/graph/age_client.py:741-749`, `count_verified_decisions`, counts `DISTINCT d.decision_id` for SOC decisions with status `confirmed` or `overridden`.
- The adapter exposes verified-count fields when writing conservation/checkpoint state (`age_sdk_adapter.py:159-179` and `225-250`).
- The outbox explicitly treats outcome persistence as fail-closed (`tests/scoring/test_persistence_outbox.py:448` and `persistence_outbox.py` enqueue validation), which is useful but does not define the Protocol-v2 API result.

**Answer:** PROTO-V2 and SOC-BACKFILL are operationally different, but semantically coupled. PROTO-V2 is forward commit/replay; SOC-BACKFILL is historical reconciliation. They do not currently share one implementation path that would automatically conflict, but both must implement the same invariant:

> `V = count(distinct canonical verified decision IDs)`; an embedded outcome and its later canonical Outcome representation count once.

The contract must be frozen before either queue item is marked complete. Backfill should deduplicate by a stable decision/outcome identity and recompute or compare against the distinct canonical count; it must not blindly increment V for every migrated row. PROTO-V2 should advance V only after the canonical commit is confirmed. This makes the items semantically dependent, though they can remain separate code modules.

### 3.2 AGE-STRESS versus the v0.7.11-ci lifecycle fix

The current AGE client already has:

- `_pool_lock` and double-checked pool creation at `ci-platform/ci_platform/graph/age_client.py:137,185-205`;
- `min_size=3`, `max_size=15`, and `connect_timeout=15` defaults at lines 133–134 and 196–198;
- serialized/idempotent close via `_sync_close` at lines 243–250;
- a defensive `PoolClosed` empty-read guard in `age_graph_store.py:582-589`.

These changes address pool initialization and disposal races for one process/shared store. They do **not** prove behavior when all 15 connections are busy. Each copilot process has its own client/pool, while multiple processes consume the same PostgreSQL server budget. Pool exhaustion should normally produce a bounded pool-acquisition failure; a hang, request-thread starvation, or `PoolClosed` cascade remains an AGE-STRESS failure.

**Answer:** v0.7.11-ci covers single-process pool lifecycle/disposal safety, not shared-instance exhaustion/capacity behavior. AGE-STRESS therefore needs a real concurrent harness. It may require no production change if the client already fails closed within the configured deadline; otherwise the smallest additional fix is a bounded pool-acquisition timeout/error mapping, not silent pool enlargement or serialization.

### 3.3 SOC-SEED-REDESIGN #9

The seed code does have timestamp generation in the current tree:

- `gen-ai-roi-demo-v4-v50/backend/app/seed/decisions.py:46-60` assigns deterministic `timestamp_epoch` values and an ISO timestamp to generated decisions.
- `backend/app/seed/validate.py:273-279` validates timestamp uniqueness.
- The support seed/repair scripts also operate on `timestamp_epoch` (`support/setup/seed_zero_day.py` and `repair_zero_day_timestamps.py`).

This means the narrow “seed writes no timestamps” claim is stale. However, the existence of timestamp fields is not proof that every AGE migration path has been run against the live graph, nor that all canonical backfill rows have the required timestamp shape.

**Answer:** SOC-SEED-REDESIGN #9 is partially present in code, but its live-data rollout status is unconfirmed; it should be treated as **in progress/needs rollout verification**, not fully shipped. SOC-BACKFILL can work around missing timestamps by using a deterministic source ordering and preserving `decision_id`, but temporal assertions and reproducible historical ordering should be gated on a seed/migration verification step. Do not make the backfill silently fabricate business timestamps.

## 4. Implementation specifications

### 4.1 PROTO-V2 — service layer over `PersistenceOutbox`

**WHAT**

Add a protocol service that exposes an API-level learn/commit operation with two explicit outcomes:

- `committed`: canonical decision/outcome/evolution writes succeeded; return a commit receipt and the post-commit V;
- `pending_sync`: the request is durably queued with an idempotency key; return a pending receipt and the pre-commit V.

The service must never report `committed` merely because an outbox row was inserted.

**REUSE**

Reuse `PersistenceOutbox` (`record_failure`, `enqueue`, `drain`, `pending_count`, periodic-drain lifecycle), `CompoundingScorer._outbox`, and the existing replay test at `tests/scoring/test_outbox_decision_evolution.py:130`. Reuse the existing graph-store canonical write methods and verified-count query instead of adding another persistence abstraction.

**NEW CODE**

Proposed modules:

- `copilot-sdk/copilot_sdk/scoring/protocol_v2_service.py`: service, receipt model, idempotency/commit state machine;
- the owning backend router (under `copilot-sdk/apps/<copilot>/backend/app/routers/`): thin API adapter;
- optional `copilot-sdk/copilot_sdk/scoring/protocol_v2_worker.py` only if the existing outbox periodic worker cannot expose pending-drain metrics cleanly.

Use a stable idempotency key derived from domain, decision ID, operation type, and client request key. Persist the request before returning pending. On replay, make the canonical write idempotent, then mark the outbox row replayed, then recompute/advance V exactly once.

**V-INCREMENT CONTRACT**

V advances only after the canonical verified outcome is committed and its identity is present in the distinct verified set. Pending rows do not advance V. A replay of an already committed idempotency key is a no-op for V. The service should assert `new_V == distinct_verified_count` in tests and expose a diagnostic mismatch rather than correcting silently.

**REPLAY WORKER**

Prefer the existing periodic drain as the background worker. The HTTP request may perform a bounded synchronous attempt, but must not wait indefinitely for replay. Worker failures remain pending/failed according to current retry policy and must be observable through pending count and abandoned count.

**API SURFACE**

Add a read-only pending-sync status endpoint in the owning backend, for example `GET /api/learn/pending-sync`, returning pending, failed, abandoned, last-drain time, and protocol version. Do not expose raw payloads or credentials.

**TEST PLAN**

- Unskip the four service-layer tests listed in §1.
- Extend `test_learn_finds_replayed_decision` to assert the committed receipt and V behavior.
- Add tests for duplicate idempotency replay, pending status visibility, worker replay after restart, and permanent failure/abandonment. These are four new tests, matching the queue proposal.
- Include a property-style assertion that a pending request leaves V unchanged and a replay increments it at most once.

**BLAST RADIUS**

Primary repo: `copilot-sdk`; shared graph/outbox interfaces may require a small `ci-platform` compatibility change only if an existing method cannot express the receipt semantics. Expected 4–7 files, 9 effective tests including the four unskipped tests, one extension, and four new tests. Risk is high because the scorer, learning path, and conservation counters are cross-cutting.

### 4.2 AGE-STRESS — cross-domain concurrency and exhaustion

**WHAT**

Create a bounded stress contract proving that concurrent AGE activity across domains is isolated and fails closed under genuine pool exhaustion.

**HARNESS**

Use `ThreadPoolExecutor` with worker count greater than the configured `max_size` (read the actual client setting; current default is 15). Use one shared AGE client/store for the shared-instance case and a disposable graph name for isolation scenarios. Set an explicit per-operation deadline shorter than the test runner timeout.

**SCENARIOS**

1. concurrent read-only queries across at least three domains;
2. concurrent writes to independent domain entities;
3. mixed reads/writes with one deliberately failing transaction;
4. pool-at-max with workers held long enough to force acquisition contention;
5. repeated run to catch state leakage and pool disposal races.

**FAIL-CLOSED ASSERTION**

Every request must complete within the harness deadline. Accepted outcomes are success or a typed/bounded pool/transaction error. A hang, unbounded retry, cross-domain result, `PoolClosed` cascade from an unrelated request, or leaked connection is a failure. Do not “fix” the test by serializing work or increasing the pool until exhaustion cannot occur.

**DISPOSABLE GRAPH**

Create the graph before the test and drop it in `finally`; close only the test-owned client/store. Verify cleanup in a second run. The current test suite has teardown patterns for disposable graph cleanup, but this new harness must make ownership explicit so it cannot close a process-shared store.

**NEW CODE / TESTS**

Prefer a focused `tests/graph/test_age_pool_stress.py` or the existing conformance file near line 3002. Production changes are conditional: first run against current lifecycle code; add only the smallest bounded acquisition/error mapping if the stress test demonstrates a hang or cascade.

**BLAST RADIUS**

The harness belongs primarily in `ci-platform` tests, with SDK conformance invocation if the shared adapter is the entry point. Expected 1–3 test/support files, one unskipped test, and medium risk to connection lifecycle code.

### 4.3 SOC-BACKFILL — canonical Outcome reconciliation

**WHAT**

Backfill canonical SOC `Outcome` records from legacy/embedded decision outcome fields without double-counting V.

**REUSE**

Reuse the existing AGE adapter/store write methods, the distinct verified count at `age_client.py:741-749`, and existing seed/validation conventions for decision IDs and timestamps. Do not route historical rows through the forward Protocol-v2 HTTP path.

**NEW CODE**

Proposed SOC-owned migration/service module: `gen-ai-roi-demo-v4-v50/backend/support/setup/backfill_soc_outcomes.py` with dry-run as the default and an explicit `--apply`. It should:

- identify eligible SOC decisions;
- derive a stable outcome identity from `(domain, decision_id, outcome_version)` or the existing canonical outcome ID;
- `MERGE`/upsert the Outcome and its decision relationship;
- preserve source/provenance and original verification timestamp;
- emit before/after counts and duplicate candidates;
- refuse to apply when the postcondition `V == distinct verified decision IDs` cannot be checked.

**V-DEDUP**

The embedded decision outcome is evidence for the canonical Outcome, not a second verified event. The migration must mark/record the source mapping and calculate V from distinct decision IDs after migration. Re-running the migration must produce zero new canonical outcomes and zero V delta.

**DEPENDENCY**

Define the shared V contract before implementation. Verify SOC seed/migration #9 in the target graph first. Backfill can operate with deterministic ID ordering when timestamps are absent, but production application should be blocked until timestamp/provenance validation passes.

**TEST PLAN**

Seed: embedded-only, canonical-only, embedded-plus-canonical duplicate, and malformed/missing outcome cases. Run backfill twice. Assert canonical count, distinct verified count, V delta, provenance, and dry-run/apply behavior.

**BLAST RADIUS**

Primary repo: `gen-ai-roi-demo-v4-v50` backend; shared AGE query helpers may be reused from `ci-platform`. Estimated 3–6 files and one unskipped contract test. Data risk is high; default dry-run and explicit postconditions are mandatory.

### 4.4 SOC-WRITE-PATH — TRIGGERED_EVOLUTION projection verifier

**WHAT**

Prove that a forward `write_evolution_event` produces the canonical `TRIGGERED_EVOLUTION` edge and that the read projection observes the same event, fields, and decision/entity linkage.

**REUSE**

Reuse `age_graph_store.write_evolution_event` at line 2032, the SDK/adapter forwarding method, and the existing legacy edge write in `age_client.py:1047-1072`. Reuse existing graph projection query helpers.

**NEW CODE**

Add a test-only projection/verifier helper under `copilot-sdk/tests/graph/` unless the queue’s intended public read API requires a production read method. The verifier should query by stable event ID and assert one edge, not merely “some edge exists.”

**TEST PLAN**

Write one event to a disposable graph, project it, assert event ID/type/decision/entity/timestamp/verification fields, repeat the write, and assert idempotent cardinality. Test a failed write does not create a projected edge.

**BLAST RADIUS**

Mostly `copilot-sdk` tests and shared adapter contract coverage; estimated 1–3 files and one unskipped test. Low-to-medium runtime risk, but high correctness value because it closes the read/write proof gap.

### 4.5 SHADOW-MAP — approved ShadowDecision promotion

**WHAT**

Define and implement an explicit, provenance-preserving mapping from a qualified `ShadowDecision` to an `Observation`. A filled shadow outcome is not itself a promotion.

**REUSE**

Reuse `ShadowDecision` graph records, `shadow_runner.fill_shadow_outcome` at `app/services/shadow_runner.py:141`, triage’s existing call at `triage.py:2680-2681`, and the F9 query/report that reads shadow nodes.

**NEW CODE / PROMOTION RULE**

Add a SOC service such as `app/services/shadow_promotion.py` with an explicit command/API and audit event. Conservative initial rule:

- shadow record has a filled outcome;
- required fields and source provenance validate;
- confidence meets a named configuration threshold;
- a minimum sample count is met per category or the promotion is explicitly manual;
- no active safety/learning pause applies;
- promotion carries `source_shadow_decision_id`, rule version, actor, and timestamp.

Do not auto-promote the synthetic F9 population. Prefer manual approval for the first release; if batch promotion is later enabled, require a dry-run preview and approval token. Promoted Observations must not be counted as verified Decisions unless they separately satisfy the canonical outcome contract.

**TEST PLAN**

Create eligible and ineligible shadows, fill outcomes, approve one, promote it, and assert exactly one Observation with provenance. Assert low confidence, missing outcome, duplicate promotion, and no-approval cases do not create Observations.

**BLAST RADIUS**

SOC backend plus tests, estimated 3–5 files and one unskipped test. High data-governance risk; no automatic production promotion should be enabled by merely removing the skip.

### 4.6 S2P-DOMAIN-PANEL — Tab 6 and fail-closed degradation

**WHAT**

Add the Domain Applicability panel expected by `s2p_polish.spec.ts` and make its static/known domain content render when S2P is unavailable.

**FRONTEND**

Add a focused component in the SOC frontend, for example `src/components/DomainApplicabilityPanel.tsx`, mounted in the existing S2P preview/Tab 6 surface. It should render the heading and domain status from a typed configuration. S2P live health may be an enrichment, not a prerequisite for the panel shell. The shell must not expose hardcoded `8002` text.

**BACKEND**

First reuse the existing platform domain-applicability endpoint (the SOC backend test suite already asserts `/api/platform/domain-applicability` exists in `test_rl_display.py:109-112`). Add a new endpoint only if the current response lacks the fields needed by the panel. The S2P service health should be optional and fail closed to `unavailable`, not erase the panel.

**FAULT INJECTION**

Use the existing Playwright route/request interception harness to block S2P calls for the second test while leaving SOC available. Do not stop or mutate a shared live backend in the test. Verify that the panel remains visible, shows a bounded unavailable state, and does not leak the S2P port.

**TEST PLAN**

Unskip both current tests. Add assertions for the typed domain list, status labels, no port leakage, and bounded S2P-down behavior. Run twice to detect state leakage.

**BLAST RADIUS**

SOC frontend and E2E tests; estimated 3–5 files, two unskipped tests, and low-to-medium risk. It should not require S2P backend changes if existing health/proxy routes are adequate.

## 5. Blast-radius matrix

Estimates are implementation estimates, not changes made by this document.

| Queue ID | Repositories | Estimated files | New tests | Skips removed | Downstream consumers | Regression risk across 12,415 tests |
|---|---|---:|---:|---:|---|---|
| PROTO-V2 | `copilot-sdk`; possibly `ci-platform` interface | 4–7 | 4 new + 1 extension | 4 | scorer, learn API, outbox worker, conservation/V reporting | High |
| AGE-STRESS | `ci-platform`; SDK conformance test invocation | 1–3 | 1 stress test | 1 | all AGE-backed copilots and shared PostgreSQL | Medium–high |
| SOC-BACKFILL | `gen-ai-roi-demo-v4-v50`; reuse `ci-platform` | 3–6 | 1 contract/migration test | 1 | SOC counts, conservation, trajectory, audit views | High data risk |
| SOC-WRITE-PATH | `copilot-sdk`, possibly `ci-platform` | 1–3 | 1 | 1 | evolution projections and W2/read paths | Medium |
| SHADOW-MAP | `gen-ai-roi-demo-v4-v50` | 3–5 | 1 | 1 | SOC observations, learning/audit, analyst benchmarking | High governance risk |
| S2P-DOMAIN-PANEL | `gen-ai-roi-demo-v4-v50` | 3–5 | 0 new; harden 2 | 2 | SOC frontend Tab 6 and S2P health display | Low–medium |
| **Total** | 3 repositories, shared AGE interfaces | **15–29** | **8 new + 1 extension** | **10 source tests** | cross-domain graph, SOC, SDK scoring | Medium overall; concentrated high-risk data paths |

The queue’s original “9 tests” total would understate this matrix by one. The two S2P panel tests are both real skip sites and should both be tracked.

## 6. Trap verification and guards

The queue document lists eight traps. All eight are relevant to the current tree, with the following concrete guards.

| Trap | Current-code assessment | Required guard and placement |
|---|---|---|
| Silent V corruption | Real. The distinct verified query exists, and the outbox has idempotency support, but no Protocol-v2 receipt contract currently binds replay to V. | In the Protocol-v2 commit/replay transaction and backfill postcondition: compare V with `count(DISTINCT decision_id)`; fail closed on mismatch. Add duplicate replay and duplicate backfill tests. |
| Green because skipped | Real. The four Protocol tests are module-skipped; AGE and three projection tests are explicitly skipped; two panel tests are unconditional skips. | Replace skips only after behavior assertions pass. Add queue IDs/reasons to any remaining intentional skip and a CI collection check. |
| Reuse drift | Real. Existing `PersistenceOutbox` and other durable-outbox code paths coexist. | Protocol-v2 implementation must import and use `PersistenceOutbox`; prohibit a second SQLite schema/replay worker. Add a test proving the existing learn replay path remains authoritative. |
| AGE stress masking | Real. Lifecycle locking is present, but max-size exhaustion has not been proven. | Force workers above max pool, hold connections, enforce operation deadlines, assert bounded pool error and no cross-domain contamination. Do not serialize or simply raise the pool limit. |
| Cross-adapter timestamp skew | Real risk. The tree uses both ISO timestamps and numeric `timestamp_epoch`/`created_at_epoch` fields (`age_client.py:1042-1072`, SOC seed/repair scripts). | Normalize ordering/comparison on numeric epoch at the adapter boundary; retain original ISO as metadata. Backfill tests must include different precision/time zones. |
| Fault-injection state leakage | Real risk for disposable graphs and backend interception. Existing SOC fixtures restore monkeypatched state in `backend/tests/conftest.py:78-92`, but the new AGE test owns a separate graph/client. | `try/finally` drop disposable graph, close only owned clients, restore env/monkeypatches, and run the stress/panel tests twice. |
| Skip-lint false confidence | Real. The queue document specifies a desired queue-ID lint, but no verified live checker was found during this read-only pass. | Add a collection-time/static checker in the implementation phase that reports every skip without queue ID/reason and checks that the named queue row exists. Do not count collection success as feature success. |
| Dependency assumed done | Real. Pool lifecycle code is present, while shared-instance exhaustion and live seed rollout are not proven; WSL database verification was unavailable. | Gate AGE-STRESS on bounded pool behavior and gate SOC-BACKFILL on seed/timestamp verification. Record evidence in test output before removing the skip. |

### Idempotency evidence

`persistence_outbox.py:73,100-102,193-222` stores `idempotency_key` and creates a pending-row unique index. Existing tests include `test_enqueue_idempotency_upsert` and `test_enqueue_different_keys_coexist` in `tests/scoring/test_persistence_outbox.py:238-250`. This is reusable, but the Protocol-v2 implementation must extend idempotency across the canonical commit and V transition; an outbox-only unique index is not sufficient to prove end-to-end exactly-once semantics.

## 7. Recommended implementation order and gates

| Order | Work | Gate |
|---:|---|---|
| 0 | Correct queue metadata from 9 to 10 tests and assign stable queue IDs to all skip sites | Collection report lists all ten sites |
| 1 | Freeze V contract and verify SOC seed/timestamp rollout | Distinct verified-ID invariant and timestamp provenance are documented and testable |
| 2 | Run AGE-STRESS against current lifecycle code | Every forced-exhaustion operation completes bounded; otherwise implement only bounded error handling |
| 3 | Implement PROTO-V2 | Four service tests plus replay/idempotency/pending tests pass; V unchanged while pending |
| 4 | Implement SOC-BACKFILL | Dry-run and two-pass apply show no duplicate canonical outcomes or V increment |
| 5a | Implement SOC-WRITE-PATH | Forward write is observable exactly once through projection |
| 5b | Implement SHADOW-MAP | Promotion requires explicit rule/approval and preserves provenance |
| 5c | Implement S2P-DOMAIN-PANEL | Both panel tests pass with S2P up and down; no port leakage |
| 6 | Run the full relevant suites twice | No new failures, no unaccounted skips, no resource leakage |

The dependency gates deliberately put the V contract before both forward protocol and historical backfill. SOC-WRITE-PATH, SHADOW-MAP, and S2P-DOMAIN-PANEL can proceed in parallel once their local fixtures are defined. AGE-STRESS should precede any claim that the pool fix is complete.

## 8. Revised effort estimate

The queue’s original 12–15 day estimate is plausible only if it is corrected for the ten-test inventory and assumes no new AGE production bug.

| Queue item | Revised estimate | Main uncertainty |
|---|---:|---|
| PROTO-V2 | 3–5 days | API ownership, V receipt semantics, worker lifecycle |
| AGE-STRESS | 1–2 days | Whether current pool behavior already fails bounded |
| SOC-BACKFILL | 2–3 days | Live graph schema/provenance and safe migration execution |
| SOC-WRITE-PATH | 0.5–1 day | Existing projection API versus test-only verifier |
| SHADOW-MAP | 2–3 days | Governance approval rules and audit surface |
| S2P-DOMAIN-PANEL | 1–2 days | Existing platform endpoint shape and test harness |
| **Total** | **9.5–16 days** | **15–20 days if pool or seed rollout needs production remediation** |

The most credible planning number is **12–15 engineering days with two engineers working in parallel**, or **15–20 days serially** if backfill and shadow governance require review. The queue should not advertise completion based solely on skip removal: PROTO-V2 and SOC-BACKFILL require invariant evidence, AGE-STRESS requires real exhaustion, and SHADOW-MAP requires an explicit promotion policy.

## Evidence limitations

No source or test files were changed. No git commands were used. The requested live AGE count query was attempted as a read-only operation, but the environment denied WSL instance creation with `E_ACCESSDENIED`; therefore the document does not assert a live `V-SHADOW-SYNTHETIC` row count. Source-level evidence confirms the shadow schema, loader/report contract, and `fill_shadow_outcome` path; live population must be rechecked in an environment with WSL/PostgreSQL access before SHADOW-MAP implementation is scheduled as a data migration.
