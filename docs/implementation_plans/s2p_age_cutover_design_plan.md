# S2P AGE Cutover Design Plan

Date: 2026-06-01

## Purpose

This plan defines how S2P can switch its active graph store from SQLite to
PostgreSQL+AGE after the accepted shadow gates, without implementing the switch
in this task.

AGE/PostgreSQL+AGE is the canonical product graph. SQLite remains the default
S2P runtime store, local/test adapter, and rollback option until explicit
cutover implementation, validation, and rollback gates pass.

The plan separates three concerns:

- Shadow mode: SQLite authoritative, AGE non-authoritative parity writes.
- Cutover: AGE active for new S2P graph writes/reads under explicit config.
- Migration/backfill: historical SQLite replay into AGE, designed separately.

## Current gate status

- AGE Protocol v2 adapter completion: accepted.
- SOC projection gate: PASS_WITH_P3.
- GraphStore factory implementation: accepted.
- S2P Shadow Phase 1 config/guards/diagnostics: accepted.
- S2P Shadow Phase 2 score/outcome dual-write: accepted.
- S2P live AGE shadow backend tests: accepted.
- S2P parity/reporting hardening: accepted.
- S2P preview/read no-Decision-write fixer: accepted.
- S2P shadow-enabled Playwright smoke workers=1: accepted.
- S2P shadow-enabled Playwright smoke workers=4: accepted.
- S2P active AGE Phase B test-mode backend: accepted.
- S2P active AGE Playwright workers=1: accepted.
- S2P active AGE Playwright workers=4 command-level smoke: accepted.
- S2P product graph cutover design hardening: allowed.
- S2P product graph cutover implementation: blocked pending product graph
  allow-list, rollback proof, true parallel active AGE proof, and review.
- S2P AGE migration/backfill: blocked pending a separate migration plan.

## Definition of cutover

S2P AGE cutover means:

- The active S2P graph store is AGE, not SQLite, only when explicit S2P cutover
  config is set.
- `/api/s2p/score` writes active Protocol v2 governed Decisions to AGE.
- `/api/s2p/outcome` and `/learn` write active Protocol v2 Outcome/status
  transitions to AGE.
- `count_decisions`, `count_verified_decisions`, conservation status, V/q/alpha,
  performance summaries, and read-side graph consumers use AGE as the active S2P
  graph source.
- Preview/read endpoints continue to use the read-only live scorer path and must
  not create Decisions.
- SQLite remains available as the default and rollback/local mode.

The first cutover is a Decision/Outcome active-AGE cutover for new writes. It is
not a full audit-memory cutover until EvidenceReceipt mapping, historical
continuity, rollback reconciliation, and cross-copilot proof are separately
accepted.

Cutover does not mean:

- Historical SQLite-to-AGE migration or backfill.
- SOC graph mutation or SOC route migration.
- Cross-copilot proof.
- Trading, Purchasing, or DataOps AGE migration.
- EvidenceReceipt/audit receipt completion unless explicitly included by a
  reviewed receipt scope decision.
- Removal of SQLite support.
- A claim that historical SQLite state has been migrated or reconciled.

## Non-goals and blocked work

Blocked from the first cutover implementation:

- Historical replay/backfill from SQLite to AGE.
- Writes to or resets of `soc_graph`.
- Generic `GRAPH_*` active backend switching for S2P runtime.
- Preview AGE Decision writes.
- EvidenceReceipt shadowing or activation unless a separate receipt design
  approves it.
- Observation shadowing for preview traces.
- Archive/reset shadowing.
- Frontend feature changes.
- Migration claims or product claims that historical SQLite data has moved.

## Architecture options

### Option A: factory-based active store switch

S2P active graph store is constructed through
`copilot_sdk.graph.factory.create_graph_store(...)`, and generic `GRAPH_*`
configuration selects SQLite or AGE.

Pros:

- Reuses accepted factory guardrails.
- Aligns with the broader SDK product direction.

Cons:

- Generic `GRAPH_*` env creates accidental cutover risk.
- S2P already uses S2P-specific shadow env, and mixing generic app-wide env with
  cutover would blur shadow, test, and product runtime boundaries.

### Option B: S2P-specific active backend switch

S2P owns explicit cutover env such as
`S2P_ACTIVE_GRAPH_BACKEND=sqlite|age`, then calls `create_graph_store(...)`
internally with explicit arguments.

Pros:

- Makes cutover impossible unless S2P-specific env is set.
- Keeps default S2P SQLite behavior unchanged.
- Avoids generic `GRAPH_*` accidental runtime switches.
- Keeps S2P shadow env distinct from active AGE cutover env.
- Still reuses the accepted GraphStore factory for AGE construction guardrails.

Cons:

- Adds S2P-local configuration code.
- Requires careful test coverage for interaction with `S2P_SHADOW_AGE`.

### Option C: staged wrapper promotion

Keep the existing SQLite composition path and introduce a wrapper that can route
active writes to AGE only at one S2P composition boundary.

Pros:

- Can localize risk while preserving app-state shape.

Cons:

- Wrapper semantics can hide which backend is authoritative.
- Risk of split-brain if some readers use the wrapper and others use the
  original `app.state.graph_store`.

## Recommended cutover strategy

Select Option B: S2P-specific active backend switch, implemented at the S2P app
composition boundary, using the GraphStore factory internally.

Accepted implementation status:

- Phase A config/status endpoint is accepted.
- Phase B active AGE test-mode backend is accepted only for
  `protocol_v2_test*` with `S2P_ACTIVE_AGE_TEST_MODE=1`.
- Active AGE Playwright workers=1 is accepted.
- Active AGE Playwright workers=4 is accepted as a command-level smoke only; it
  did not prove true parallel pressure because only one test matched.

Next implementation scope after this hardened product graph design review:

- Add product graph allow-list/guard constants and status endpoint updates
  without enabling product writes if possible.
- Keep default S2P SQLite behavior unchanged.
- Keep active AGE product graph behind explicit `S2P_ACTIVE_*` env.
- Continue using `create_graph_store(backend="age", domain="s2p", ...)` only
  after S2P-specific guards pass.
- Ensure `app.state.scorer.graph_store` and `app.state.graph_store` reference
  the same active store.
- Keep `CompoundingScorer.from_preset` unchanged.
- Disable/disallow S2P shadow when active backend is AGE.

Excluded from first cutover:

- Historical migration/backfill.
- Receipt/audit EvidenceReceipt activation.
- Preview Observation persistence.
- Archive/reset.
- Cross-copilot proof.
- Frontend changes beyond later optional status display.

## Environment variables and guardrails

Cutover env:

- `S2P_ACTIVE_GRAPH_BACKEND=sqlite|age`
- `S2P_ACTIVE_AGE_DSN`
- `S2P_ACTIVE_AGE_GRAPH`
- `S2P_ACTIVE_AGE_DOMAIN=s2p`
- `S2P_ACTIVE_AGE_TEST_MODE=0|1`
- `S2P_SHADOW_AGE=0` when active backend is AGE
- `CI_DATA_DIR` for SQLite default path and rollback mode

Final product cutover env:

- `S2P_ACTIVE_GRAPH_BACKEND=age`
- `S2P_ACTIVE_AGE_DSN=<reviewed product AGE DSN>`
- `S2P_ACTIVE_AGE_GRAPH=<reviewed product graph>`
- `S2P_ACTIVE_AGE_DOMAIN=s2p`
- `S2P_ACTIVE_AGE_TEST_MODE=0`
- `S2P_SHADOW_AGE=0`

Defaults:

- If `S2P_ACTIVE_GRAPH_BACKEND` is unset, S2P uses the existing SQLite behavior.
- `S2P_ACTIVE_GRAPH_BACKEND=sqlite` uses SQLite and must not require AGE DSN or
  graph.
- `S2P_ACTIVE_AGE_DOMAIN` defaults to `s2p` and rejects any non-`s2p` value.
- Generic `GRAPH_*`, `AGE_*`, and `S2P_GRAPH_BACKEND` variables are ignored for
  active S2P cutover selection. S2P cutover must be driven only by the
  `S2P_ACTIVE_*` namespace in the first implementation.

AGE active guards:

- Active AGE requires explicit DSN and graph.
- Blank graph is rejected.
- `soc_graph` is rejected.
- `protocol_v2_test*` graphs require `S2P_ACTIVE_AGE_TEST_MODE=1`.
- Product cutover must not use `protocol_v2_test*`.
- Product AGE graph name must be explicit, non-test, non-SOC, and reviewed
  before use.
- Product AGE graph names must come from a small S2P allow-list owned by this
  plan or an immediately adjacent reviewed operations note.
- The implementation should represent this as a code-level constant such as
  `S2P_ALLOWED_PRODUCT_AGE_GRAPHS`. Product graph use must be denied unless
  `S2P_ACTIVE_AGE_GRAPH` is a member of that allow-list.
- Preferred product candidate: `governed_copilot_graph`, because the product
  architecture points toward one governed live judgment-memory graph across
  copilots. Alternative candidate: `s2p_graph`, only if a reviewed operations
  decision deliberately chooses an S2P-only product graph as an interim step.
  The first product implementation must not accept arbitrary non-test graph
  names.
- Product graph names are forbidden when blank, equal to `soc_graph`, or
  starting with `protocol_v2_test`.
- No default product graph guessing is allowed. If a product graph name is not
  reviewed and allow-listed, startup/config validation must fail.
- `S2P_ACTIVE_AGE_TEST_MODE=0` is required for product graph use.
- Product allow-list behavior must be test-covered before any active product
  graph write is enabled:
  - allowed product graph accepted only with `S2P_ACTIVE_AGE_TEST_MODE=0`;
  - allowed product graph rejected when test mode is on;
  - non-allow-listed graph rejected;
  - `protocol_v2_test*` rejected in product mode;
  - `soc_graph` rejected in every S2P mode.
- DSN credentials must be redacted in logs, status responses, and diagnostics.
- Generic `GRAPH_*` and `S2P_GRAPH_BACKEND` must not switch S2P active runtime in
  the first cutover implementation.

Shadow interaction:

- If `S2P_ACTIVE_GRAPH_BACKEND=age`, `S2P_SHADOW_AGE=1` is rejected.
- Active AGE must not self-shadow to the same graph.
- Shadow mode remains valid only when the active backend is SQLite.
- If future AGE-to-AGE shadow is needed, it requires a separate design with
  distinct source/target graphs and correlation rules.

## Diagnostics/reporting endpoint

A guarded status endpoint/report is required before cutover implementation is
accepted.

Recommended path:

- `GET /api/s2p/graph/status`

Purpose:

- Make active backend, shadow status, and readiness visible without exposing
  secrets.
- Provide an operator/debug contract for Playwright and backend cutover tests.

Fields:

- `active_backend`: `sqlite` or `age`.
- `requested_backend`: `sqlite` or `age`.
- `active_domain`: `s2p`.
- `sqlite_authoritative`: boolean.
- `age_active`: boolean.
- `active_graph_name`: safe graph name or null.
- `age_graph_kind`: `test`, `product`, or `none`.
- `active_test_mode`: boolean.
- `shadow_enabled`: boolean.
- `shadow_allowed`: boolean.
- `shadow_run_id`: safe ID when shadow is enabled.
- `recent_shadow_status_counts`: diagnostic counts if available.
- `diagnostics_summary`: bounded counts only, not raw DSN, raw env, SQL, or full
  exception payloads.
- `last_shadow_error`: redacted error class/message if available.
- `migration_backfill_status`: `not_in_scope`, `not_migrated`, or a later
  reviewed migration state.
- `receipt_mapping_status`: `excluded`, `planned`, or a later reviewed active
  state.
- `rollback_instructions`: short non-secret operator instruction, e.g. unset
  `S2P_ACTIVE_GRAPH_BACKEND` and restart.
- `cutover_ready_flags`: backend guard, graph guard, preview read-only guard,
  receipt scope decision, rollback plan present, true parallel gate status,
  product graph allow-list status, and migration/backfill boundary.
- `historical_visibility`: a concise status such as
  `new_writes_only_history_not_migrated`.
- `historical_sqlite_count_warning`: present when SQLite has historical S2P
  Decisions and the active AGE graph has fewer or zero product Decisions.
- `warnings`: non-secret operator warnings, including historical migration not
  performed.

The status endpoint must distinguish these operator states:

- `S2P [SQLite authoritative]`: `active_backend=sqlite`, `age_active=false`.
- `S2P [AGE shadow]`: SQLite active with `shadow_enabled=true`.
- `S2P [AGE active test]`: `active_backend=age`, `age_graph_kind=test`,
  `active_test_mode=true`.
- `S2P [AGE active product]`: `active_backend=age`, `age_graph_kind=product`,
  `active_test_mode=false`, and product graph allow-list validation passed.

For product graph hardening, `cutover_ready_flags` must include:

- `product_graph_reviewed`: true only when `S2P_ACTIVE_AGE_GRAPH` is in the
  reviewed S2P product allow-list.
- `true_parallel_active_age_gate_passed`: true only after the separate
  concurrency/parallel gate passes.
- `rollback_proof_passed`: true only after active AGE then SQLite rollback proof
  passes.
- `evidence_receipts_active`: false for first cutover.
- `migration_backfill_in_scope`: false for first cutover.
- `product_claim_allowed`: false until product graph cutover, rollback,
  EvidenceReceipt scope, migration/backfill boundary, and cross-copilot proof
  are all resolved by reviewed gates.

Security assumptions:

- Demo/dev endpoint only for this phase.
- Do not include DSN, username/password, tokens, raw env, SQL, or AGE driver
  errors containing credentials.
- If product exposure is needed, add auth before enabling it outside local/demo
  contexts.

Required before cutover implementation: YES.

Playwright and backend cutover tests should use this endpoint/report to prove
the runtime is in the expected mode. The endpoint must remain read-only and
safe for demo/dev use.

## Rollback plan

Rollback mechanism:

- Set `S2P_ACTIVE_GRAPH_BACKEND=sqlite` or unset it.
- Remove active AGE env.
- Restart S2P.
- Keep `CI_DATA_DIR` and existing SQLite path unchanged.
- Treat rollback as a new-writes routing change. It is not data reconciliation.

Split-brain prevention:

- Exactly one active write backend is allowed.
- Shadow is disallowed when active AGE is enabled.
- All S2P graph consumers must read from the same `app.state.graph_store` as the
  scorer.
- Cutover implementation must not switch score/outcome while conservation,
  performance, evidence, or governance routes continue reading SQLite.

AGE data written during cutover:

- Rollback does not delete AGE data.
- Rollback does not copy AGE data back to SQLite.
- Reconciliation of AGE cutover writes back to SQLite is a separate incident or
  migration plan.
- Status output must say when AGE contains new cutover data that SQLite does not
  contain.
- Operators must not infer that rollback restored AGE-only cutover Decisions
  into SQLite. If that continuity is required, run a separately reviewed
  reconciliation/backfill plan.

Rollback test:

- Start with SQLite default and prove score/outcome writes to SQLite.
- Start with active AGE test graph and prove score/outcome writes to AGE.
- Start with active AGE product or product-like allow-listed graph and prove
  score/outcome writes to AGE before product cutover implementation is accepted.
- Restart with SQLite default and prove score/outcome writes to SQLite again.
- Verify `/api/s2p/graph/status` reports `active_backend=sqlite`,
  `sqlite_authoritative=true`, and `age_active=false` after rollback.
- Verify no AGE deletion is required.
- Verify no hidden AGE-to-SQLite reconciliation runs.
- Document that rollback does not migrate AGE-only cutover Decisions or Outcomes
  back into SQLite.
- Verify at least one AGE-only cutover Decision remains readable in AGE after
  rollback.
- Verify the SQLite store used after rollback does not see that AGE-only
  Decision unless a separately reviewed reconciliation/backfill has run.
- Verify status/operator output warns that historical visibility is split:
  rollback routes new writes to SQLite, but AGE cutover history remains in AGE.
- Verify no code path attempts to use `soc_graph`.

## Receipt/audit scope decision

First cutover scope: exclude active EvidenceReceipt mapping. This makes the
first implementation a Decision/Outcome active-AGE cutover, not a complete
audit-memory cutover.

Rationale:

- Current S2P receipt/audit behavior is product-specific and not yet mapped to
  Protocol v2 `append_evidence_receipt`.
- Score/outcome Protocol v2 parity is accepted; EvidenceReceipt chain parity is
  a separate audit contract.
- Including receipts in first cutover would expand the blast radius.

Audit gap if excluded:

- AGE active Decisions and Outcomes will be canonical, but the existing S2P
  receipt store remains outside canonical EvidenceReceipt nodes.
- Cutover status/reporting must explicitly state `evidence_receipts_active:
  false`.
- Product claims must not say S2P audit receipts are fully canonical until the
  receipt mapping is designed and tested.
- External/product claims that S2P has fully canonical audit memory remain
  blocked until EvidenceReceipt mapping is accepted or explicitly scoped out by
  a reviewed product decision.

Later plan:

- Create
  `copilot-sdk/docs/implementation_plans/s2p_evidence_receipt_mapping_plan.md`.
- Map current receipt payloads to Protocol v2 `append_evidence_receipt`.
- Define hash payload, previous-hash behavior, idempotency, and replay rules.
- Add backend/live AGE tests before including receipts in product claims.

Gate decision:

- Internal demo cutover: EvidenceReceipt mapping is not required if the demo
  explicitly says first cutover is Decision/Outcome only and status reports
  `receipt_mapping_status=excluded_first_cutover`.
- External product claim: EvidenceReceipt mapping is required before claiming
  full canonical audit memory.
- Cross-copilot proof: EvidenceReceipt mapping is required before claiming
  governed audit continuity across copilots unless a reviewed product decision
  explicitly scopes receipts out.

## Migration/backfill boundary

Historical backfill included: NO.

First cutover may be new-writes-only:

- New score/outcome writes after cutover go to AGE.
- Existing SQLite history remains in SQLite unless a separate migration plan is
  approved.
- UI/status/reporting must distinguish active AGE from migrated history.
- UI/demo/status wording must not say "migration complete", "historical data
  migrated", or equivalent unless a separate migration plan has passed and run.
- Operator status must state that historical SQLite records are not visible in
  AGE-active mode unless migration/backfill has run.
- Cutover implementation should include a non-blocking count warning when the
  selected SQLite fallback store contains historical S2P Decisions and the
  active AGE product graph starts empty or materially lower. This warning is for
  operator clarity only; it must not synthesize parity or hide the mismatch.
- Conservation and performance views after cutover reflect the active AGE graph
  unless a separate continuity bridge is explicitly designed.
- Test-mode cutover should use a fresh or uniquely named `protocol_v2_test*`
  graph/domain run where possible. If residual test rows are retained, tests
  must use unique IDs and status must not imply historical parity.

Separate migration plan required:

- Historical Decision replay.
- Historical Outcome/status replay.
- EvidenceReceipt replay, if receipts are included.
- Idempotency conflict handling.
- Cutover data reconciliation.
- Rollback after partial replay.

## Test and validation gates

Backend config/guard tests:

- Default with no env remains SQLite.
- `S2P_ACTIVE_GRAPH_BACKEND=sqlite` does not require DSN/graph.
- Invalid backend is rejected.
- Active AGE requires DSN.
- Active AGE requires graph.
- Blank graph is rejected.
- `soc_graph` is rejected.
- `protocol_v2_test*` requires `S2P_ACTIVE_AGE_TEST_MODE=1`.
- Product mode rejects `protocol_v2_test*`.
- Non-`s2p` domain is rejected.
- Active AGE rejects `S2P_SHADOW_AGE=1`.
- Generic `GRAPH_*` does not switch active S2P backend.
- Status endpoint redacts secrets.
- Status endpoint reports `migration_backfill_status` and
  `receipt_mapping_status`.
- Status endpoint includes rollback instructions and active/shadow conflict
  state.

Backend behavior tests:

- Active SQLite score still writes SQLite Decision.
- Active SQLite outcome still updates SQLite Outcome/status.
- Active AGE score writes AGE governed Decision and does not write SQLite
  Decision.
- Active AGE outcome writes AGE Outcome/status after successful active AGE
  Decision.
- One-outcome invariant is preserved in active AGE.
- Preview does not write AGE Decision.
- Preview still reflects live learned scorer state.
- Conservation/status counts use active AGE V in AGE mode.
- Performance/read routes use active AGE store in AGE mode.
- Rollback env returns to SQLite behavior.

Live AGE tests:

- Guarded by explicit live env.
- Use `protocol_v2_test*` with `S2P_ACTIVE_AGE_TEST_MODE=1` for test cutover.
- Verify score/outcome/learn parity.
- Verify conservation V/q/alpha after confirmed and overridden outcomes.
- Verify rollback to SQLite after AGE run.
- Verify status endpoint reports active backend and redacts DSN.
- Verify live rollback proof: active AGE score/outcome succeeds, process is
  restarted or app state is reconstructed with SQLite config, and subsequent
  score/outcome writes go to SQLite.

Playwright gates:

- Shadow-enabled workers=1: already accepted.
- Shadow-enabled workers=4: required before implementation cutover acceptance.
- Active AGE test graph workers=1: required before product cutover.
- Active AGE test graph workers=4 command-level smoke: accepted before product
  graph design hardening.
- True parallel active AGE proof: required before product cutover implementation
  and before any product claim. The accepted workers=4 Playwright command ran one
  matching test and therefore did not exercise concurrent AGE writes.
- Default SQLite workers=1 and workers=4 must remain green.

True parallel active AGE gate options:

- Backend concurrency gate: run multiple parallel independent score/outcome and
  `/learn` flows against active AGE test mode or a product-like allow-listed
  graph, with unique event IDs and decision IDs, then verify AGE status/Outcome
  parity and one-outcome invariant.
- Playwright parallel gate: split the active AGE smoke into multiple independent
  tests with unique data so `--workers=4` runs real parallel flows.
- The backend concurrency gate is preferred for first product implementation
  readiness because it directly stresses write semantics without UI selector
  noise.

Minimum true parallel gate:

- Run at least 8 independent score flows with at least 4 concurrent workers.
- Include at least 4 `/api/s2p/outcome` confirmations/overrides and at least 4
  `/learn` confirmations/overrides, each against a distinct Decision.
- Use unique event IDs and unique returned Decision IDs; no shared canonical
  smoke IDs.
- Do not broad-delete the `s2p` domain. Use unique IDs and targeted readback.
- Success criteria:
  - every score returns a unique Decision ID;
  - each AGE Decision exists with domain `s2p` and expected status;
  - each outcome/learn creates exactly one Outcome and transitions status to
    confirmed or overridden;
  - duplicate outcome/learn remains rejected;
  - no orphan Outcomes;
  - verified count increases by the expected number for the affected IDs;
  - preview/read run during or after the gate creates no Decisions;
  - status endpoint remains in the expected mode and exposes no secrets.

Blocked tests:

- Product graph cutover tests until product graph name is reviewed.
- Historical migration/replay tests until migration plan exists.
- SOC graph mutation tests.
- EvidenceReceipt active tests until receipt mapping design exists.
- Product-claim tests for full audit memory until EvidenceReceipt and migration
  boundaries are resolved.

## demo.py operational TODO

Design only; do not implement in this task.

Future flags:

- `--s2p-shadow-age`: starts S2P with SQLite authoritative and AGE shadow.
- `--s2p-age-test`: starts S2P with active AGE test-mode env against
  `protocol_v2_test*`.
- `--s2p-age-product`: starts S2P with active AGE product env only after product
  graph name, DSN, and runbook are reviewed.

Status output:

- `S2P [SQLite authoritative]`
- `S2P [AGE shadow: protocol_v2_test]`
- `S2P [AGE active test: protocol_v2_test]`
- `S2P [AGE active product: <reviewed_graph_name>]`

Rules:

- Default demo behavior stays SQLite.
- `--s2p-age-test` requires explicit test DSN and `protocol_v2_test*` graph.
- `--s2p-age-product` requires explicit reviewed product DSN and allow-listed
  graph.
- `soc_graph` is never allowed for S2P.
- DSN is redacted.
- Demo must not claim historical SQLite migration unless migration has run.
- demo.py status wiring is not required for the first config/status endpoint
  implementation or product-like mocked backend tests.
- demo.py flag/status support is required before any repeatable operator-facing
  product graph runbook, live product graph cutover rehearsal, or external demo
  claim.
- `--s2p-age-product` must refuse to start unless the requested graph is in the
  reviewed S2P product allow-list and is not `soc_graph` or `protocol_v2_test*`.

## Implementation prompt outline

Phase A implementation prompt after this plan is reviewed:

- Add S2P active graph config parser and tests.
- Add `/api/s2p/graph/status` or equivalent guarded operator report.
- Do not change active backend default.
- Do not activate AGE writes.
- Do not refactor app graph-store construction yet unless required for reporting
  current SQLite mode.
- Prove no-env S2P behavior remains SQLite.
- Prove generic `GRAPH_*` does not switch S2P active runtime.

Phase B implementation prompt:

- Refactor S2P app composition so active store construction can select SQLite or
  AGE through S2P-specific config.
- Use `create_graph_store` for AGE only.
- Keep `CompoundingScorer.from_preset` unchanged.
- Reject shadow when active AGE is enabled.
- Add backend config/guard/default behavior tests.
- Restrict active AGE to test graph mode first.

Phase C1 implementation prompt:

- Add S2P product graph allow-list/guard constants.
- Update `/api/s2p/graph/status` with product graph kind, product allow-list
  status, true parallel gate status placeholder, and rollback proof status.
- Do not enable product graph writes if avoidable.
- Add tests for product graph allow-list acceptance/rejection with product-like
  names.
- Keep `protocol_v2_test*` restricted to test mode.
- Do not require demo.py changes in C1.

Phase C2 implementation prompt:

- Exercise product-like graph config behind explicit product env, preferably
  with mocked/fake store construction first:
  `S2P_ACTIVE_GRAPH_BACKEND=age`,
  `S2P_ACTIVE_AGE_DSN=<reviewed product DSN>`,
  `S2P_ACTIVE_AGE_GRAPH=<allow-listed product graph>`,
  `S2P_ACTIVE_AGE_DOMAIN=s2p`,
  `S2P_ACTIVE_AGE_TEST_MODE=0`, and `S2P_SHADOW_AGE=0`.
- Add backend tests with mocked/product-like graph name.
- Prove route response shape unchanged.
- Keep migration/backfill excluded.
- Do not run against the real product graph in C2 unless a separate review
  explicitly approves it.

Phase C3 implementation prompt:

- Add the true parallel active AGE gate before any real product graph write path
  is accepted.
- Prefer backend concurrency with at least 8 independent score flows and at
  least 4 concurrent workers.
- Include both `/api/s2p/outcome` and `/learn` against distinct Decisions.
- Keep the gate on active AGE test mode or product-like allow-listed graph until
  product graph use is separately approved.

Phase C4 implementation prompt:

- Run guarded live reviewed product graph or product-like graph smoke only after
  C1-C3 pass.
- Prove rollback: active AGE score/outcome, restart or reconstruct with SQLite,
  subsequent score/outcome writes to SQLite, and status reports SQLite.
- Verify AGE-only cutover data remains in AGE and is not silently copied back to
  SQLite.
- Do not delete AGE data.
- Do not run hidden reconciliation.
- Run Playwright workers=1 and workers=4 with product-like graph or approved
  product graph.
- Run default SQLite workers=1 and workers=4.
- Verify preview/read no-Decision-write behavior.
- Verify conservation/performance read paths use active AGE.

Phase C5/future design prompts:

- Create S2P EvidenceReceipt mapping design.
- Create S2P historical migration/backfill design.
- Create cross-copilot proof design.
- EvidenceReceipt mapping design may proceed in parallel with C1-C4, but
  EvidenceReceipt implementation remains blocked until that design is reviewed.
- Keep full audit-memory product claims blocked until EvidenceReceipt scope is
  resolved.
- Keep historical continuity claims blocked until migration/backfill is designed,
  tested, and run.

## Open questions

- What reviewed product AGE graph name should S2P use after
  `protocol_v2_test*` parity?
- Should the first product cutover be new-writes-only, or is historical
  continuity required before product demonstration?
- Where should long-lived cutover diagnostics live if the in-memory shadow
  diagnostics are insufficient?
- What auth model should protect `/api/s2p/graph/status` outside local/demo?
- When should S2P EvidenceReceipt mapping become mandatory for product claims?
- Should rollback include an AGE-to-SQLite reconciliation utility, or only a
  config switch plus incident runbook?
