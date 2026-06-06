# S2P AGE Shadow Design Plan

Date: 2026-06-01

## Purpose

This plan defines S2P AGE shadow mode before any runtime implementation. Shadow
mode must let the S2P backend keep SQLite as the authoritative product store
while comparing selected Protocol v2 writes and reads against PostgreSQL+AGE.

The goal is parity evidence, not cutover. AGE is the canonical product graph
direction, but S2P must not switch to AGE until shadow tests, live parity, and
rollback gates pass.

## Current gate status

- AGE Protocol v2 adapter completion gate: closed.
- SOC projection gate: PASS_WITH_P3.
- GraphStore factory design: PASS.
- GraphStore factory implementation: accepted.
- S2P AGE shadow design: allowed.
- S2P AGE shadow implementation: blocked until this plan is reviewed.
- S2P AGE cutover/migration: blocked.

## Current S2P construction inventory

### `s2p-copilot/backend/app/main.py`

- `DATA_DIR = Path(os.environ.get("CI_DATA_DIR", Path(__file__).parent /
  "data"))`.
- `build_s2p_scorer(db_path=None)` builds `CompoundingScorer.from_preset("s2p",
  graph_store=SQLiteGraphStore(effective, domain="s2p",
  decision_id_prefix="S2P-"), reward_function=S2PRewardFunction())`.
- At module import, `app.state.scorer` is set to
  `build_s2p_scorer(str(DATA_DIR / "s2p.db"))`.
- `app.state.graph_store` points to the scorer's SQLite store.
- Risk: high. Store/scorer construction happens at import time and is shared by
  many routers. Shadow implementation must avoid implicit import-time AGE writes
  and must preserve default SQLite behavior.

### `/api/s2p/score` in `backend/app/routers/s2p.py`

- Uses `request.app.state.scorer`.
- `CompoundingScorer.score()` writes a SQLite Decision through
  `scorer.graph_store.write_decision`.
- The route also tries a legacy graph write through `app.db.neo4j` /
  `write_s2p_decision`, swallowing failures.
- Links the Decision to invoice via `link_decision_to_entity` where available.
- Risk: high. This is the primary live Decision write path and the first useful
  shadow target.

### `/learn` and `/api/s2p/outcome` in `backend/app/routers/s2p.py`

- `/learn` calls `_learn_with_scorer`, which calls `scorer.learn(...)`.
- `/api/s2p/outcome` ensures a missing Decision with `write_decision`, then calls
  `_learn_with_scorer`.
- `scorer.learn()` writes Outcome/status semantics through the current
  `graph_store`.
- Outcome receipt logic records product audit receipts outside the AGE
  EvidenceReceipt path.
- Risk: high. Outcome/status parity is essential, but shadowing must preserve
  SQLite response semantics and receipt behavior.

### Conservation reads

- `create_conservation_router("s2p", state_provider=lambda:
  cached_conservation_state_provider(app.state))` is mounted under `/api`.
- `cached_conservation_state_provider` reads counts from `app.state.graph_store`
  or the scorer's store.
- Score-time conservation status uses cached graph counts from the same SQLite
  store.
- Risk: high. V/q/alpha parity must be checked without changing product
  conservation responses.

### `/api/s2p/performance/*`

- `backend/app/routers/s2p_performance.py` reads `app.state.graph_store`.
- Summary, trajectory, and what-if endpoints read counts, verified decisions,
  centroid checkpoints, and recommendation counts.
- It has SQLite-specific fallback logic using `graph_store.connection` for
  recommended action counts.
- Risk: medium-high. Read parity matters, but this route should not be first
  write-shadow scope.

### `/api/s2p/preview/*`

- `backend/app/routers/s2p_preview.py` uses the live app scorer for preview queue
  scoring, and uses `build_s2p_scorer(":memory:")` for simulation trajectories.
- `CompoundingScorer.score()` writes Decisions, so any preview use of the live
  scorer must be treated as potentially mutating unless separately fixed.
- Hard constraint for future implementation: preview/read endpoints must not
  create live Decision rows. If a preview trace must be persisted, it must be an
  Observation, not a Decision.
- Risk: high. Shadow implementation must not add AGE Decision writes for preview
  paths until preview write semantics are corrected and tested.

### Read-only / mostly-read routers

- `s2p_evidence`, `s2p_explorer`, `s2p_governance`, `s2p_audit_export`, and
  `s2p_performance` read from `app.state.graph_store` or scorer graph store.
- These should consume SQLite authoritative state in first shadow mode.
- Risk: medium. Later parity diagnostics can compare read outputs from SQLite
  and AGE, but product responses must stay SQLite-backed.

### Demo and tests

- `copilot-sdk/demo.py` passes `CI_DATA_DIR` to S2P; the backend owns the
  `s2p.db` filename.
- `s2p-copilot/backend/demo/s2p_demo.py` uses in-memory SQLite.
- Many backend tests reset `app.state.scorer = build_s2p_scorer()` and
  `app.state.graph_store = app.state.scorer.graph_store`.
- Risk: high for test isolation. Shadow env must be off by default, and tests
  must prove no behavior change when shadow env is absent.

## Shadow architecture options

### Option A: dual-write shadow

- SQLite remains authoritative.
- For selected live operations, a shadow layer writes equivalent Protocol v2
  events to an AGE store.
- Diagnostics compare counts/statuses after the operation.
- Pros: closest to eventual runtime behavior and catches write-path parity
  issues.
- Cons: adds request-path overhead and needs careful failure isolation.

### Option B: sidecar shadow replay

- SQLite remains authoritative.
- A background or explicit sidecar replays selected SQLite decisions/outcomes to
  AGE outside the request path.
- Pros: safer for product latency and easier rollback.
- Cons: does not prove inline request write behavior and introduces ordering /
  replay bookkeeping.

### Option C: read-only shadow comparison

- No AGE writes from S2P runtime.
- Compare SQLite against AGE only after a separately seeded/replayed AGE graph.
- Pros: lowest runtime risk.
- Cons: cannot prove S2P shadow writes, EvidenceReceipt chains, or live parity.

## Recommended first shadow strategy

Select Option A, dual-write shadow, but stage it so the first implementation is
configuration and diagnostics only:

- SQLite remains the only product response source.
- AGE writes are diagnostic shadow writes.
- AGE failures are isolated from product responses unless strict mode is enabled.
- Shadow diagnostics are logged and exposed only through a later explicit
  diagnostics endpoint or test helper.

Implementation sequence:

- Phase 1: add S2P shadow config parsing, guard validation, and an in-memory
  diagnostics coordinator. Do not wire shadow calls into routes and do not write
  to AGE.
- Phase 2: add narrow score/outcome dual-write shadow behind
  `S2P_SHADOW_AGE=1`, after Phase 1 is reviewed.
- Phase 3: design and test preview read-only prediction / Observation behavior
  before any preview shadowing.
- Phase 4: produce a live parity report.
- Phase 5: cutover design only after parity evidence.

First route-shadow scope after Phase 1:

- `/api/s2p/score`: mirror the canonical governed Decision payload to AGE after
  the SQLite score succeeds.
- `/learn` and `/api/s2p/outcome`: mirror Outcome/status transition to AGE after
  the SQLite learn/outcome succeeds.
- Count parity: compare SQLite and AGE `count_decisions("s2p")` and
  `count_verified_decisions("s2p")`.
- Basic status parity: pending/confirmed/overridden for the affected Decision.
- Conservation parity: V/q/alpha derived from active verified Decisions.

Score shadow must use Protocol v2 `write_governed_decision`, not legacy
`write_decision`. The AGE shadow `decision_id` must equal the SQLite
authoritative Decision ID. If implementation cannot build the canonical governed
payload from the S2P score request/result path, it must stop and add a mapper
design/test rather than silently falling back to legacy writes.

Excluded from first shadow:

- Preview/read endpoint AGE writes.
- EvidenceReceipt shadowing, unless a later slice maps current S2P receipt store
  events to canonical `append_evidence_receipt`.
- Observation shadowing for preview traces.
- Archive/reset.
- Migration replay.
- SOC graph.
- Frontend/Playwright behavior changes.

## Shadow write/read scope

The first implementation should introduce S2P-local shadow configuration and
diagnostics only, not change `CompoundingScorer.from_preset`, generic GraphStore
semantics, or route behavior.

Suggested shape for Phase 1:

- `S2PShadowConfig.from_env(env=os.environ)`.
- `S2PShadowDiagnostics` with an in-memory ring buffer and structured status
  records.
- Guard validation for AGE DSN, graph, domain, test graph usage, and
  `soc_graph` rejection.

Suggested shape for Phase 2 route shadowing:

- `S2PShadowStorePair(primary_sqlite_store, age_shadow_store, config)`.
- `S2PShadowRecorder` methods:
  - `record_score_shadow(score_request, score_result, factor_vector, metadata)`.
  - `record_outcome_shadow(decision_id, actual_action, outcome_payload,
    context)`.
  - `collect_parity_snapshot(decision_id=None)`.

The route layer should call the coordinator only after the SQLite operation
succeeds. The coordinator should not replace `app.state.graph_store` in first
shadow mode.

Score shadow must pass the SQLite authoritative `decision_id` into AGE. Each
shadowed request should also have a `shadow_run_id` and per-request
`operation_id` recorded in diagnostics and, where useful, AGE metadata. Replays
must rely on Protocol v2 Class A idempotency: same `decision_id` and identical
canonical payload is a no-op; same `decision_id` and conflicting payload is a
shadow parity failure.

## Preview/read semantics

Preview Decision writes avoided:

- `/api/s2p/preview/*` must not write shadow AGE Decisions.
- Preview/read shadowing is fully excluded until a read-only prediction API or
  facade exists over the live learned scorer state.
- Before any preview shadowing, add a regression test proving preview/read
  endpoints do not increase live Decision count.
- If current preview queue scoring uses the live scorer and therefore writes
  SQLite Decisions, fix that as a separate preview-read semantics slice before
  enabling AGE shadow for preview.

Observation usage:

- If a preview trace must be persisted, write it as Protocol v2 Observation.
- Observation must not affect V, alpha, Decision count, or Outcome status.
- Do not promote `ShadowDecision` or preview recommendations to canonical
  Decision automatically.

Live learned scorer state preserved:

- Preview recommendations should reflect the learned/persistent scorer state.
- Do not use a disconnected in-memory scorer for product preview recommendations
  if that would hide learned state.
- A safe future pattern is a read-only scoring/simulation method that uses live
  centroids but does not call `write_decision`.
- That facade must not instantiate an isolated scorer with empty memory. It must
  read the same live centroids/preset state used by product scoring while
  avoiding all Decision write paths.

Endpoint semantics:

- `/api/s2p/score`: product Decision write, first shadow target.
- `/learn`: product Outcome/status write, first shadow target.
- `/api/s2p/outcome`: product Outcome/status write, first shadow target.
- `/api/conservation/status`: SQLite authoritative response; shadow computes
  parity diagnostics only.
- `/api/s2p/performance/summary`: SQLite authoritative response; shadow may add
  diagnostics later but must not alter response shape in first implementation.
- `/api/s2p/preview/*`: no AGE shadow Decision writes in first implementation.

## Parity metrics

Required parity checks:

- Decision count parity by domain `s2p`.
- Verified count parity by active confirmed/overridden Decisions.
- Pending/confirmed/overridden status parity for affected decisions.
- Outcome parity: actual action, correctness, status, metadata essentials.
- Response-shape parity for score and outcome responses.
- Conservation parity:
  - V = active verified Decisions.
  - q = correct / verified.
  - alpha / override rate from active verified Decisions.
  - theta/status if available.
- Observation no-V parity when Observation shadowing is added later.
- Receipt chain parity when EvidenceReceipt shadowing is added later.
- Latency overhead per shadowed request.
- Shadow error count and last error.

Decision identity and correlation:

- Score shadow must use the SQLite authoritative `decision_id` as the AGE
  `decision_id`.
- Generate a `shadow_run_id` per process/test run and an `operation_id` per
  shadowed request.
- Diagnostics should include `shadow_run_id`, `operation_id`,
  `sqlite_decision_id`, `age_decision_id`, operation name, status, and latency.
- The expected score invariant is `sqlite_decision_id == age_decision_id`.
- Any AGE idempotency conflict for the same `decision_id` is a parity failure,
  not a reason to create a replacement Decision.

Diagnostics:

- Log one structured shadow diagnostic event per shadowed request.
- Redact DSN credentials.
- Include backend, domain, graph name, operation, decision_id, parity status,
  latency, and error class.
- Do not change product response shape in first implementation.

## Failure handling

Default non-strict mode:

- SQLite request remains authoritative.
- If AGE shadow construction or write fails, the product request still succeeds.
- Failure is logged and counted in diagnostics.
- The response body is not modified.

Strict mode:

- Intended for tests and controlled staging only.
- If AGE shadow write/parity fails, fail the request clearly after SQLite has
  already succeeded.
- Strict mode must warn that it can create operator-visible failures and should
  not be default.

No fake success:

- Shadow diagnostics must distinguish skipped, disabled, succeeded, failed, and
  parity_mismatch states.
- Swallowed AGE errors without diagnostic records are not acceptable.
- Phase 1 diagnostics should use an in-memory ring buffer plus normal
  application logging. Do not persist diagnostics into AGE in Phase 1.
- Do not add a SQLite diagnostics table in Phase 1 unless a later design
  explicitly approves it.
- Diagnostic records should include timestamp, `shadow_run_id`, `operation_id`,
  operation, SQLite Decision ID when available, AGE graph, AGE domain, status,
  latency in milliseconds, strict flag, sanitized error type, and sanitized error
  message.
- Track repeated shadow failures with counters and last-error summaries so
  repeated failures remain visible.

## Environment variables

Defaults:

- `S2P_SHADOW_AGE=0`: shadow disabled.
- `S2P_SHADOW_STRICT=0`: AGE failures do not fail product requests.
- `CI_DATA_DIR`: existing SQLite data directory behavior.

Shadow AGE inputs:

- `S2P_SHADOW_AGE=1`.
- `S2P_AGE_DSN`: required when shadow is enabled.
- `S2P_AGE_GRAPH`: required when shadow is enabled.
- `S2P_AGE_DOMAIN=s2p`; if set to anything else, reject.
- `S2P_AGE_TEST_MODE=0|1`; required for `protocol_v2_test*` graphs.
- Optional `S2P_SQLITE_DB_PATH` only if a later implementation decides to
  override the current `DATA_DIR / "s2p.db"` behavior.

Rules:

- Default behavior is unchanged.
- There is no active-backend switch in shadow mode. SQLite remains authoritative
  by construction.
- `S2P_GRAPH_BACKEND` and generic `GRAPH_*` cutover variables are out of scope
  for shadow implementation and must not switch S2P runtime behavior.
- Shadow must require explicit AGE DSN and graph.
- `S2P_AGE_GRAPH=soc_graph` is forbidden.
- Test AGE graphs must start with `protocol_v2_test` and require test-mode
  construction with `S2P_AGE_TEST_MODE=1`.
- Product AGE graph names must be explicit and reviewed before use.
- Generic `GRAPH_*` variables should not drive S2P shadow in the first
  implementation; use S2P-specific env to avoid accidental app-wide switches.

Rollback:

- Set `S2P_SHADOW_AGE=0` or remove the variable.
- Keep SQLite authoritative data untouched.
- Do not delete AGE shadow data during rollback.
- Reset/replay of AGE shadow data requires a separate guarded test/admin plan.

## Test plan

Phase 1 unit/config tests:

- `S2PShadowConfig` defaults to disabled.
- Shadow config requires DSN and graph when enabled.
- Shadow config rejects `soc_graph`.
- Shadow config rejects non-`s2p` domain.
- Shadow config rejects `protocol_v2_test*` unless `S2P_AGE_TEST_MODE=1`.
- Strict/non-strict behavior is parsed correctly.
- Shadow recorder records disabled/skipped/succeeded/failed states.
- Diagnostics redact DSN secrets.
- No shadow env: S2P backend construction and responses remain unchanged.
- Phase 1 does not call AGE from score/outcome/preview routes.

Phase 2 backend tests:

- Shadow env constructs SQLite primary plus AGE shadow store, without replacing
  `app.state.graph_store`.
- `/api/s2p/score` succeeds when AGE shadow succeeds.
- `/api/s2p/score` succeeds in non-strict mode when AGE shadow fails and records
  diagnostics.
- `/api/s2p/score` fails clearly in strict mode when AGE shadow fails.
- `/learn` and `/api/s2p/outcome` mirror Outcome/status after SQLite success.
- Score shadow uses Protocol v2 `write_governed_decision`, not legacy
  `write_decision`.
- AGE shadow Decision ID equals SQLite authoritative Decision ID.
- Preview endpoints do not write AGE Decisions.
- Preview endpoints do not increase live Decision count; if this currently
  fails for SQLite, fix preview-read semantics before enabling preview shadow.
- `/api/conservation/status` response remains SQLite-authoritative.
- `/api/s2p/performance/summary` response shape remains unchanged.

Preview/read tests:

- Preview/read endpoints must not create AGE Decisions.
- Preview/read endpoints must not increase SQLite Decision count once a
  read-only facade exists.
- If Observation preview traces are introduced, they must not affect active V.
- These tests are mandatory before any preview shadowing; they do not block
  score/outcome shadow.

Live AGE tests:

- Guarded by explicit S2P shadow env and AGE test graph.
- Use `protocol_v2_test*` graph, never `soc_graph`.
- Score/outcome parity after a small scenario.
- V/q/alpha parity after confirmed and overridden outcomes.
- Shadow failure isolation with invalid AGE config in non-strict mode.

Playwright/manual tests:

- S2P workers=1 smoke flow with shadow disabled.
- S2P workers=4 smoke flow with shadow disabled.
- Later, workers=1 and workers=4 with shadow enabled against test graph.
- No frontend copy should claim cutover.

Blocked tests:

- S2P AGE cutover tests.
- Migration replay tests.
- SOC graph mutation tests.
- Archive/reset in S2P product runtime.

## Demo/operational behavior

Do not change `demo.py` in first shadow implementation.

Future demo/status output may show:

- Active backend: SQLite authoritative.
- Shadow: enabled/disabled.
- AGE graph name: safe name only, DSN redacted.
- Last parity status and mismatch count.
- Last shadow error class.

It must not claim AGE cutover or canonical S2P runtime until cutover gates pass.

## Cutover gates

Required before S2P AGE cutover:

- Shadow implementation tests pass.
- Live AGE shadow parity report passes for score/outcome/conservation scenarios.
- S2P backend tests pass with shadow disabled and enabled.
- S2P Playwright workers=1 pass with shadow disabled and enabled.
- S2P Playwright workers=4 pass with shadow disabled and enabled.
- Rollback plan tested by disabling shadow env without data loss.
- SOC projection gate remains at least PASS_WITH_P3.
- No critical drift in V, q, alpha, Decision status, or Outcome semantics.
- EvidenceReceipt strategy for S2P audit receipts is designed if receipts are in
  cutover scope.
- Receipt/audit mapping is designed and tested, or explicitly accepted as out of
  cutover scope by a separate reviewed decision.
- Operational runbook reviewed.

S2P AGE migration remains blocked until cutover gates pass and a separate
migration/replay design is reviewed.

Required before S2P AGE migration:

- S2P AGE cutover gates have passed.
- Migration/replay design is reviewed.
- Historical SQLite-to-AGE replay is tested in a non-production graph.
- Rollback and data reconciliation are documented.

## Implementation prompt outline

First implementation prompt after this plan is reviewed:

- Add S2P shadow config parser and in-memory diagnostics coordinator only.
- Validate AGE env, graph, domain, `soc_graph`, and test graph guardrails.
- Keep SQLite as authoritative runtime store.
- Do not replace `app.state.graph_store`.
- Do not change `CompoundingScorer.from_preset`.
- Do not wire score/outcome/preview routes to AGE.
- Do not write to AGE.
- Do not change frontend or Playwright.
- Do not mutate `soc_graph`.
- Add unit/backend tests for disabled defaults, env guards, diagnostics
  redaction, and no route behavior change.

Second implementation prompt after Phase 1 review:

- Add route integration for `/api/s2p/score`, `/learn`, and
  `/api/s2p/outcome`.
- Use `create_graph_store` only for AGE shadow store creation.
- Keep active SQLite store construction unchanged.
- Use Protocol v2 `write_governed_decision` for score shadow.
- Use SQLite authoritative `decision_id` as AGE `decision_id`.
- Do not shadow preview.
- Add backend and live AGE tests for score/outcome parity, non-strict failure
  isolation, strict mode, and diagnostics.

## Open questions

- How should current S2P receipt-store events map to Protocol v2
  `append_evidence_receipt`? Recommendation: separate receipt mapping design
  before cutover.
- Where should long-lived shadow diagnostics be stored if the Phase 1 in-memory
  ring buffer and logs are insufficient?
- What product AGE graph name should be used after test graph parity?
- What canonical mapper is needed if S2P score request/result paths do not
  expose every `write_governed_decision` field required by Protocol v2?
