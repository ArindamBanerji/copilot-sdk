# Opus Review Handoff - Governed Graph Migration MAP

Version/date: v1.0, 2026-06-01.

Source basis: governed graph migration session, S2P cutover plans, SDK apps governed graph adoption plan, Judgment Memory v2.7, Protocol v2 design v1.8, and reported GPT-5.5 milestone reviews.

Goal: Level 5 governed AGE architecture across SOC, S2P, Trading, Purchasing, and DataOps.

Status: NOT Level 5 complete.

Current accepted apps: S2P, Purchasing, and Trading for new Decision/Outcome AGE writes only, behind explicit app-specific env.

Current blockers: DataOps active AGE, EvidenceReceipt, migration/backfill, demo.py AGE operations, product graph smoke, product-mode Playwright/status validation, cross-copilot proof, and shared GraphStore/mypy failures.

External review ask: review the migration for correctness, architectural integrity, false claims, and missing Level 5 deliverables.

## 0. Review Purpose and Claim Boundary

This report is for Opus review of correctness, architectural integrity, false claims, and missing Level 5 deliverables. It is an external-review handoff, not a completion certificate.

Current safe claim:

- S2P, Purchasing, and Trading have accepted new Decision/Outcome AGE write paths under explicit app-specific env.
- Those accepted scopes preserve SQLite fallback/rollback and keep migration/backfill and EvidenceReceipt outside the first cutover.

Current unsafe claim:

- The whole platform is fully migrated.
- All copilots are on the final governed graph architecture.
- Historical SQLite data has been migrated.
- Full canonical audit memory is complete.
- Product/external claims are safe.

Level 5 is not complete.

## 1. Executive Summary

This is not a completion report. It is a handoff showing partial migration progress and remaining Level 5 blockers.

The Level 5 goal is a common governed AGE-backed judgment-memory architecture across SOC, S2P, Trading, Purchasing, and DataOps, with Protocol v2 Decision/Outcome semantics, SQLite retained only for local/test/rollback, and clear boundaries for EvidenceReceipt, migration/backfill, demo operations, Playwright smoke, and cross-copilot proof.

What has been implemented:

- S2P is implemented and accepted as new-write AGE active for Decision/Outcome records under explicit `S2P_ACTIVE_*` env.
- Purchasing is implemented and accepted as new-write AGE active for Decision/Outcome records under explicit `PURCHASING_ACTIVE_*` env.
- Trading is implemented and accepted as new-write AGE active for Decision/Outcome records under explicit `TRADING_ACTIVE_*` env, including broader route-surface coverage.
- GraphStore factory and Protocol v2 adapter work have been accepted as supporting foundations.
- SOC projection gate was accepted with P3 caveats.

What has only been designed:

- DataOps governed graph semantics and adoption are planned, but DataOps active AGE adoption has not been implemented.
- SDK-wide batch adoption strategy is documented.
- S2P product graph cutover design/status hardening is documented and partially implemented, but full product/external claim remains blocked.
- EvidenceReceipt mapping and historical migration/backfill remain design/future work.
- demo.py operational AGE flags/status remain future work.
- Cross-copilot proof is not implemented.

Accepted by GPT-5.5:

- S2P active AGE new Decision/Outcome milestone.
- Purchasing active AGE new Decision/Outcome milestone.
- Trading active AGE new Decision/Outcome milestone.
- S2P C1/C2 allow-list/status gates.
- S2P true parallel active AGE backend gate.
- S2P Playwright workers=1 and workers=4 command smoke, with the workers=4 limitation recorded as P3.
- AGE Protocol v2 adapter, SOC projection, and GraphStore factory gates.

What remains unfinished:

- DataOps active AGE implementation.
- EvidenceReceipt mapping across apps.
- Historical migration/backfill across apps.
- Product live `governed_copilot_graph` smoke.
- Product-mode Playwright status validation across apps.
- demo.py AGE operational flags/status.
- Cross-copilot proof and final product/external claim.

Safe to claim fully migrated: NO.

The current safe claim is narrower: S2P, Purchasing, and Trading can write new Decision/Outcome records to AGE under explicit app-specific env, with SQLite fallback/rollback retained and no migration/backfill or EvidenceReceipt claim.

## 1A. Goals, Sub-Targets, and Definitions of Done

Goal 0 - Final architecture:

- SOC, S2P, Trading, Purchasing, and DataOps all participate in one governed AGE-backed judgment-memory architecture.
- Done when all five domains have accepted write/read boundaries, domain separation, and cross-copilot proof against the reviewed common graph.

Goal 1 - Runtime storage:

- AGE is canonical runtime graph storage; SQLite is fallback/local/test only.
- Done when each app defaults safely, can run explicit AGE mode, and status/demo never describes SQLite as the product graph.

Goal 2 - Protocol v2:

- All new Decisions and Outcomes use the canonical Protocol v2 lifecycle.
- Done when score creates pending Decisions, outcome/learn creates Outcome/status transitions, one-outcome invariant is preserved, and conformance tests cover both adapters.

Goal 3 - Read/preview safety:

- Read/preview/research routes do not create Decisions unless explicitly intended and tested.
- Done when each app has tests proving read-like paths create no Decision side effects.

Goal 4 - Rollback:

- Every app has rollback to SQLite with no deletion, copy-back, or hidden reconciliation.
- Done when rollback proof shows AGE writes first, SQLite writes after restart/reconfiguration, status reports SQLite, and AGE-only history remains AGE-only.

Goal 5 - EvidenceReceipt:

- EvidenceReceipt/audit-chain mapping is implemented or the product claim is explicitly narrowed.
- Done when `append_evidence_receipt` behavior is mapped, tested, and included, or when status/docs explicitly say the claim is Decision/Outcome-only.

Goal 6 - Migration/backfill:

- Historical migration/backfill is implemented or status/UI/demo explicitly say new-writes-only.
- Done when replay/backfill is tested and run, or every operator/product surface states historical SQLite data is not migrated.

Goal 7 - Operator/demo:

- `demo.py` supports safe AGE test/product/shadow flags and status.
- Done when demo startup/status can distinguish SQLite, AGE shadow, AGE active test, and AGE active product for each accepted app without exposing secrets or using `soc_graph`.

Goal 8 - Verification:

- Backend, live AGE, Playwright, rollback, and cross-copilot proof pass.
- Done when targeted and broad suites are clean or dispositioned, guarded live AGE tests pass, product-mode Playwright/status checks pass, and cross-domain graph queries are documented and reproducible.

Goal 9 - Product claim:

- No full product/external claim until all Level 5 gates pass.
- Done only when DataOps, EvidenceReceipt, migration/backfill caveats, demo operations, product graph smoke, product-mode Playwright, and cross-copilot proof are accepted.

## 1B. Level 5 Sub-Target Matrix

| Domain | AGE runtime new Decision/Outcome | SQLite fallback | Read/preview safety | Rollback proof | EvidenceReceipt | Migration/backfill | demo.py support | Product graph smoke | Product-mode Playwright | Cross-copilot proof inclusion | Current level | Blocking gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SOC | Projection/AGE foundation accepted, final write proof not complete | Not primary focus | Projection caveats remain | Not complete for final architecture | Not complete | Not complete | Not complete | Not complete | Not complete | Required, not complete | Projection accepted with P3 | Final proof/audit caveats, EvidenceReceipt, cross-copilot proof |
| S2P | Accepted under explicit env | Preserved | Accepted, preview/read no Decision writes | Accepted for milestone | Missing/excluded | Missing/excluded | Missing | Product `governed_copilot_graph` smoke not run | Product-mode Playwright not rerun | Required, not complete | New-write AGE active | EvidenceReceipt, migration/backfill, demo.py, product graph smoke, cross-proof |
| Purchasing | Accepted under explicit env | Preserved | Accepted for milestone | Accepted with fake/live milestone scope | Missing/excluded | Missing/excluded | Missing | Not run | Existing flows passed, graph-status validation needs rerun | Required, not complete | New-write AGE active | Graph-status Playwright rerun, EvidenceReceipt, migration/backfill, demo.py, product graph smoke, cross-proof |
| Trading | Accepted under explicit env | Preserved | Accepted for prescore/read-like routes | Accepted with fake/live milestone scope | Missing/excluded | Missing/excluded | Missing | Not run | Existing flows passed, graph-status validation needs rerun | Required, not complete | New-write AGE active | Graph-status Playwright rerun, EvidenceReceipt, migration/backfill, demo.py, product graph smoke, cross-proof |
| DataOps | Not implemented | Baseline only | Baseline/plan only | Not implemented | Missing/excluded | Missing/excluded | Missing | Not run | Not run for active AGE | Required, not complete | Baseline/semantics plan only | Active AGE implementation, operational graph separation, live AGE, Playwright, milestone acceptance |

## 1C. Claims Explicitly Not Allowed Yet

- "All copilots are fully migrated."
- "Historical SQLite data is migrated."
- "Full canonical audit memory is implemented."
- "EvidenceReceipt/audit chain is complete across apps."
- "Product `governed_copilot_graph` live cutover is validated."
- "`demo.py` fully supports AGE operation."
- "Cross-copilot proof is complete."
- "The platform is safe for a full product/external Level 5 claim."

## 1D. Blocking Dependency Graph

- DataOps active AGE blocks Level 5.
- EvidenceReceipt blocks full audit-memory claim.
- Migration/backfill blocks historical continuity claim.
- demo.py blocks repeatable operator/demo claim.
- Product graph smoke blocks product graph readiness claim.
- Product-mode Playwright graph-status validation blocks operator-visible E2E readiness.
- Cross-copilot proof blocks final architecture claim.
- Broad GraphStore/mypy failures block clean SDK-wide acceptance.

## Platform State

| Copilot/Repo | Current Level | Tests Reported | AGE Runtime Status | Playwright | Status |
| --- | --- | --- | --- | --- | --- |
| SOC | Projection/AGE foundation with P3 | SOC projection contract tests reported | AGE/projection accepted, final proof/audit caveats remain | Not current app smoke | P3 accepted, not final Level 5 |
| S2P | New-write AGE active | Final backend 941 passed, 10 skipped; live/parallel gates accepted | Explicit `S2P_ACTIVE_*` new Decision/Outcome writes accepted; product live graph not run | workers=1 and command-level workers=4 accepted; product mode not rerun | Accepted partial migration |
| Purchasing | New-write AGE active | Backend 167 passed, 1 skipped; graph/status 20 passed; live AGE 1 passed | Explicit `PURCHASING_ACTIVE_*` new Decision/Outcome writes accepted | 14 passed; graph-status validation caveat | Accepted partial migration |
| Trading | New-write AGE active | Backend 726 passed, 1 skipped; graph/status 21 passed; live AGE 1 passed | Explicit `TRADING_ACTIVE_*` new Decision/Outcome writes accepted | 14 passed; graph-status validation caveat | Accepted partial migration |
| DataOps | Baseline/semantics plan only | Discovery baseline 130 passed | No active AGE implementation | Not run for active AGE | Blocker for Level 5 |
| copilot-sdk shared GraphStore | Foundation accepted with unresolved broad failures | Shared subsets 195/157 passed; broad 4 failures reported | Factory/protocol foundation exists | Not applicable | Needs cleanup/disposition |
| ci-platform AGE adapter | AGE adapter foundation accepted | Live AGE app gates passed through adapter | Canonical AGE direction | Not applicable | Accepted foundation, final proof pending |
| demo.py | Operational AGE support missing | Not tested for AGE ops | Does not yet provide full AGE test/product/shadow flags/status | Not applicable | Blocks repeatable operator/demo claim |

## Summary Metrics

| Metric | Value |
| --- | --- |
| Accepted app new-write AGE milestones | 3: S2P, Purchasing, Trading |
| Apps still missing active AGE | 1: DataOps |
| Full Level 5 blockers | 8: DataOps, EvidenceReceipt, migration/backfill, demo.py, product graph smoke, product Playwright/status, cross-copilot proof, shared failures |
| Known broad suite failures | 4 |
| Product/external claim safe | NO |
| Current safe claim | New Decision/Outcome AGE writes for S2P/Purchasing/Trading under explicit env only |

## Evidence Provenance and Verification Limits

| Evidence type | Source | Reliability | Opus should verify |
| --- | --- | --- | --- |
| Current worktree inventory | `git status`, `git diff`, and `git ls-files` scans | High for file presence, not semantic correctness | Rerun git commands |
| Test results | Codex-reported outputs from the migration session | Medium/high, but not all freshly rerun in this handoff | Rerun commands in Appendix |
| GPT-5.5 acceptances | Conversation review outputs | Useful gate signal, not independent proof | Inspect code/tests |
| Live AGE results | Codex/user-reported guarded runs | Medium/high, environment-dependent | Rerun with env |
| Playwright results | Reported commands | Medium; stale-stack caveats exist | Rerun after restart |

## Cumulative Accepted - Governed Graph Migration

| Area | Accepted Scope | Evidence | Exclusions |
| --- | --- | --- | --- |
| AGE Protocol v2 adapter | Protocol v2 adapter foundation | Reported accepted gate; live app AGE gates use adapter path | Full EvidenceReceipt/product claim |
| GraphStore factory | Factory construction pattern and guardrails | GraphStore factory accepted; shared subsets reported | Final SDK-wide broad suite still has unresolved failures |
| SOC projection gate | Projection compatibility | PASS_WITH_P3 | Final cross-copilot proof, forward-write/audit caveats |
| S2P preview/read no-write | Preview/read no Decision write | `test_s2p_preview.py` 37 passed; accepted fixer | Observation/EvidenceReceipt mapping |
| S2P new-write AGE active | New Decision/Outcome AGE writes under explicit env | Full backend 941 passed, 10 skipped; live and parallel gates accepted | EvidenceReceipt, migration/backfill, product/external claim |
| Purchasing new-write AGE active | New Decision/Outcome AGE writes under explicit env | Backend 167 passed, 1 skipped; live AGE 1 passed | EvidenceReceipt, migration/backfill, product graph smoke, graph-status Playwright rerun |
| Trading new-write AGE active | New Decision/Outcome AGE writes under explicit env, including route surface | Backend 726 passed, 1 skipped; live AGE 1 passed | EvidenceReceipt, migration/backfill, product graph smoke, graph-status Playwright rerun |
| S2P/Purchasing/Trading rollback proof scope | Rollback by env/restart, no copy-back/reconciliation | Fake-store and accepted milestone reviews | Historical continuity claim |
| S2P/Purchasing/Trading Playwright caveats | UI smoke/regression accepted where run | S2P active AGE workers=1/4 command; Purchasing/Trading 14 passed each | Product-mode graph-status validation and true multi-test UI parallel pressure |

## Active Level 5 Items

| # | ID | Domain | Deliverable | Status | Blocks Level 5? | Next action |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | SHARED-GRAPH-FAILURES | SDK graph | Fix/disposition protocol/mypy failures | Active blocker | YES | Run focused review/fix for structural GraphStore tests and mypy |
| 2 | DOPS-AGE-ACTIVE | DataOps | Implement scorer-only active AGE | Not implemented | YES | Execute DataOps adoption with operational separation tests |
| 3 | EVIDENCE-RECEIPT-ALL | All apps | Canonical EvidenceReceipt mapping or downgraded claim | Not implemented | YES for audit-memory claim | Design/implement receipt mapping and status flags |
| 4 | MIGRATION-BACKFILL | All apps | Historical backfill or enforced new-writes-only boundary | Not implemented | YES for historical continuity claim | Choose replay/backfill or strict claim boundary |
| 5 | DEMO-AGE-OPS | demo.py/all apps | AGE flags/status for operator repeatability | Not implemented | YES for demo/operator claim | Implement safe flags and redacted status after app gates |
| 6 | PRODUCT-GRAPH-SMOKE | Accepted apps | `governed_copilot_graph` product smoke | Not run | YES for product graph readiness | Run only with explicit approval and no `soc_graph` |
| 7 | PRODUCT-PW-STATUS | Accepted apps | Product-mode Playwright/status validation | Not complete | YES for UI/operator readiness | Restart matching stacks and verify status endpoints |
| 8 | CROSS-COPILOT-PROOF | All domains | Final graph proof/report | Not implemented | YES | Execute last after all domains accepted |
| 9 | SOC-CANONICAL-CAVEATS | SOC | SOC final projection/forward-write/audit caveat review | P3 open | YES for final architecture claim | Review SOC caveats before final proof |
| 10 | ARTIFACT-HYGIENE | All repos | Remove/exclude DBs, reports, generated artifacts | Open | YES for clean review/merge hygiene | Clean or explicitly ignore non-deliverables |

## Level 5 Acceptance Checklist

| Gate | Status | Blocking Level 5? | Evidence | Next action |
| --- | --- | --- | --- | --- |
| SOC final proof | PARTIAL | YES | SOC projection gate PASS_WITH_P3 | Resolve final projection/forward-write/audit caveats before cross-proof |
| S2P full Level 5 | PARTIAL | YES | New-write AGE active accepted | Add EvidenceReceipt/migration/demo/product graph/cross-proof gates |
| Purchasing full Level 5 | PARTIAL | YES | New-write AGE active accepted | Rerun product/status Playwright and add remaining Level 5 gates |
| Trading full Level 5 | PARTIAL | YES | New-write AGE active accepted | Rerun product/status Playwright and add remaining Level 5 gates |
| DataOps active AGE | NOT STARTED | YES | Baseline/semantics plan only | Implement scorer-only active AGE with operational separation tests |
| EvidenceReceipt | NOT STARTED | YES | Explicitly excluded so far | Implement mapping or downgrade claim to Decision/Outcome active AGE only |
| migration/backfill | NOT STARTED | YES for historical continuity | Explicitly excluded so far | Implement replay/backfill or enforce new-writes-only claim boundary |
| demo.py AGE ops | NOT STARTED | YES for repeatable operator/demo readiness | No AGE test/product/shadow flags/status implemented | Add safe flags/status with defaults unchanged |
| product graph smoke | NOT STARTED | YES for product graph readiness | Product `governed_copilot_graph` smoke not run | Run only after explicit product graph approval |
| product-mode Playwright/status | PARTIAL | YES for UI/operator readiness | S2P test-mode smoke accepted; Purchasing/Trading stale-status caveat | Rerun against restarted product/product-like stacks |
| cross-copilot proof | NOT STARTED | YES | No final graph proof report | Execute last after all app and audit/history gates |
| broad GraphStore/mypy cleanup | FAIL | YES for clean SDK-wide acceptance | 4 broad failures reported | Fix or formally disposition |

Strict Level 5 acceptance wording:

- EvidenceReceipt is REQUIRED for full canonical audit-memory Level 5. If EvidenceReceipt remains excluded, the claim must be downgraded to "Decision/Outcome active AGE only."
- Migration/backfill is REQUIRED for full historical migration/continuity. If migration/backfill is excluded, the claim must be "new-writes-only."
- demo.py AGE operation is REQUIRED for repeatable operator/demo readiness.
- Cross-copilot proof is REQUIRED for Level 5.

## Coding Plan - Remaining Level 5 Work

### Coding Bundle 1 - Shared GraphStore Cleanup

Scope:

- Fix/disposition structural protocol tests.
- Fix mypy failures in `copilot_sdk/graph/sqlite_store.py` and `copilot_sdk/graph/factory.py`.
- Preserve the GraphStore interface and app behavior.
- Do not weaken tests.

Deliverables:

- Broad graph/protocol tests pass, or failures are explicitly dispositioned by reviewer with a non-Level-5-blocking rationale.
- mypy tests pass, or type-checking scope is explicitly dispositioned by reviewer.
- No app milestone regressions.

Stop conditions:

- Protocol breakage.
- Unsafe narrowing of GraphStore interface.
- Test weakening or skipping to hide failures.

### Coding Bundle 2 - DataOps Scorer-Only AGE Adoption

Scope:

- Add `DATAOPS_ACTIVE_*` env parsing and guards.
- Add `/api/dataops/graph/status`.
- Implement scorer Decision/Outcome AGE active path only.
- Keep DataOpsGraphClient and operational graph concepts separate.
- Add operational graph separation tests.
- Add guarded live AGE tests.
- Run Playwright if stack is available and matching backend is running.

Deliverables:

- DataOps accepted for new Decision/Outcome AGE writes under explicit env.
- Pipeline, DataQualityAlert, PipelineSystem, Activity, Transformation, and operational graph routes are not silently mapped as scorer Decisions.
- Status endpoint truthfully reports migration/backfill and EvidenceReceipt exclusions.

Stop conditions:

- Scorer GraphStore and DataOpsGraphClient are inseparable.
- Generic `GRAPH_DSN` or `GRAPH_*` accidentally controls scorer backend.
- Operational routes create scorer Decisions without explicit design and tests.

### Coding Bundle 3 - EvidenceReceipt + Audit Mapping

Scope:

- Map app receipts/audit outputs to Protocol v2 EvidenceReceipt.
- Cover S2P, Purchasing, Trading, and DataOps where applicable.
- Ensure no V impact.
- Define replay/idempotency and hash-chain behavior.
- Update status endpoints to report receipt readiness.

Deliverables:

- Canonical audit-memory claim becomes possible, or claim is formally downgraded to Decision/Outcome-only.
- EvidenceReceipt tests pass across required adapters/apps.

Stop conditions:

- Receipt model ambiguous.
- Hash-chain semantics inconsistent across apps.
- Hidden audit loss or silent receipt omission.

### Coding Bundle 4 - Migration/Backfill Policy

Scope:

- Choose and implement either historical SQLite to AGE backfill/replay, or strict new-writes-only enforcement in status/UI/demo.
- Avoid hidden reconciliation.
- Preserve rollback clarity.

Deliverables:

- Historical continuity claim is either implemented and tested or explicitly forbidden.
- Status/UI/demo truthfully report whether history is migrated.

Stop conditions:

- Duplicate IDs.
- AGE/SQLite status mismatch.
- Split-brain behavior or hidden copy-back.

### Coding Bundle 5 - demo.py AGE Operations

Scope:

- Add flags for S2P, Purchasing, Trading, and DataOps AGE test/product modes.
- Add status output for SQLite, AGE shadow, AGE active test, and AGE active product.
- Keep defaults unchanged.
- Redact DSNs/secrets.
- Forbid `soc_graph` for non-SOC apps.

Deliverables:

- Repeatable operator startup/status for accepted AGE modes.
- Safe default local/SQLite behavior remains unchanged.

Stop conditions:

- Default behavior changes.
- Unsafe env/DSN leakage.
- `soc_graph` used for non-SOC apps.

### Coding Bundle 6 - Cross-Copilot Proof

Scope:

- Query/report the common graph.
- Prove all domains present.
- Verify canonical Decision/Outcome fields.
- Verify domain separation.
- Report caveats.
- Submit final Opus/GPT-5.5 review packet.

Deliverables:

- Level 5 proof report.
- Final claim boundary accepted or rejected explicitly.

Stop conditions:

- Any domain missing.
- Canonical fields absent.
- Claim boundary unclear.
- EvidenceReceipt/migration caveats hidden.

## Testing Plan - Level 5 Gates

## Minimum Level 5 Test Gate

- All targeted app backend tests pass.
- DataOps active AGE tests pass.
- Broad GraphStore/mypy failures are fixed or formally dispositioned.
- Guarded live AGE tests pass for all non-SOC apps.
- Product-mode status endpoint is verified per app.
- Playwright status smoke passes per app.
- Cross-copilot proof query/report passes.
- EvidenceReceipt and migration/backfill claim boundaries are verified.

### Unit/backend tests

- GraphStore factory tests.
- Protocol v2 conformance tests.
- App graph/status tests.
- Score/learn/outcome route tests.
- Preview/read no-write tests.
- Rollback tests.
- DataOps operational separation tests.
- Shared GraphStore protocol/mypy tests.

### Live AGE tests

- Guarded env per app.
- `protocol_v2_test*` domain per app.
- Product `governed_copilot_graph` smoke only after explicit approval.
- No broad deletion.
- Unique IDs for live tests.
- Row accumulation policy or retention note.

### Playwright tests

- S2P active AGE/status.
- Purchasing active AGE/status.
- Trading active AGE/status.
- DataOps active AGE/status after implementation.
- workers=1 for targeted smoke.
- workers=4 only when multiple independent tests exist.
- Avoid command-only false confidence.
- Restart matching backend/frontend stacks before status validation.

### Migration/backfill tests

- Replay idempotency.
- No duplicate Decision/Outcome.
- Historical visibility.
- Rollback after migration.
- Status/UI/demo wording matches the actual migration state.

### EvidenceReceipt tests

- Receipt node.
- `EMITTED_RECEIPT` edge.
- Chain index/hash.
- Replay/idempotency.
- Conflict quarantine or explicit failure behavior.
- No V impact.

### Cross-copilot proof tests

- All domains present.
- Canonical vocabulary.
- No `soc_graph` contamination.
- Status endpoint consistency.
- Cross-domain traversal/report.
- Claim boundary check.

## Next 10 Prompt Queue

| # | Prompt ID | Closes blocker | Purpose | Repos touched | Stop condition | Expected deliverable |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | SHARED-GRAPH-FAILURES-FIX | Broad GraphStore/mypy blocker | Fix/disposition GraphStore protocol and mypy failures | `copilot-sdk` | Interface narrowing or test weakening | Clean shared graph/type gate or reviewed disposition |
| 2 | DATAOPS-AGE-ACTIVE | DataOps active AGE blocker | Implement DataOps scorer-only AGE with operational separation tests | `copilot-sdk`, `ci-platform` if live adapter needed | DataOpsGraphClient/scorer inseparable or generic `GRAPH_*` cutover | DataOps active AGE backend milestone candidate |
| 3 | DATAOPS-MILESTONE-REVIEW | DataOps acceptance blocker | GPT-5.5 milestone review | No edits | P1/P2 correctness/data-safety issue | Accepted/rejected DataOps milestone |
| 4 | EVIDENCE-RECEIPT-ALL | Audit-memory blocker | Implement or formally scope EvidenceReceipt across apps | `copilot-sdk`, `s2p-copilot`, possibly `ci-platform` | Ambiguous receipt/hash semantics | Receipt mapping implementation or explicit downgraded audit claim |
| 5 | MIGRATION-BACKFILL-POLICY | Historical continuity blocker | Implement backfill or strict new-writes-only enforcement | `copilot-sdk`, `s2p-copilot` | Duplicate IDs, hidden reconciliation, split-brain | Historical continuity implemented or explicitly forbidden |
| 6 | DEMO-AGE-OPS | Operator repeatability blocker | Add demo.py flags/status for all AGE modes | `copilot-sdk`, possibly app startup env docs | Default behavior change or secret leakage | Repeatable operator AGE startup/status |
| 7 | PRODUCT-GRAPH-SMOKE | Product graph readiness blocker | Run governed_copilot_graph smoke for accepted apps | `copilot-sdk`, `s2p-copilot`, `ci-platform` | Product graph not approved or `soc_graph` risk | Product graph readiness evidence |
| 8 | PRODUCT-PW-STATUS | UI/operator readiness blocker | Product-mode Playwright/status validation | `copilot-sdk`, `s2p-copilot` | Stack mismatch or status endpoint unavailable | UI/operator readiness evidence |
| 9 | CROSS-COPILOT-PROOF | Final architecture proof blocker | Final graph proof/report | `copilot-sdk`, `s2p-copilot`, `ci-platform` | Missing domain or canonical field | Level 5 proof report |
| 10 | FINAL-LEVEL5-REVIEW | Final claim boundary blocker | Opus/GPT-5.5 final architecture review | Docs only unless fixes requested | Any P1/P2 or false claim | Final acceptance or precise blocker list |

## Sequencing Constraints

- Shared GraphStore failures must be fixed or dispositioned before final Level 5.
- DataOps must be accepted before cross-copilot proof.
- EvidenceReceipt must be implemented before a full audit-memory claim.
- Migration/backfill must be implemented before a historical continuity claim.
- demo.py AGE operations must exist before a repeatable operator/demo claim.
- Product graph smoke must pass before a product graph readiness claim.
- Product Playwright/status validation must pass before a UI/operator readiness claim.
- Cross-copilot proof runs last.
- P3s may move to backlog only if they do not affect correctness, data safety, rollback, or claim boundaries.

## Standing Rules

1. P1/P2 block; P3 backlog.
2. No partial milestone can be called fully migrated.
3. SQLite fallback remains unless explicitly replaced by a reviewed gate.
4. Generic `GRAPH_*` cannot cut over app backends.
5. `soc_graph` is forbidden for non-SOC writes.
6. Preview/read paths create no Decision writes unless explicitly intended and tested.
7. EvidenceReceipt is required for the full audit-memory claim.
8. Migration/backfill is required for the historical continuity claim.
9. `demo.py` default behavior remains unchanged.
10. Do not commit generated DB/report artifacts.

## Opus Acceptance Criteria

Opus should mark:

- handoff accurate: YES/NO
- Level 5 goal complete/testable: YES/NO
- false claims present: YES/NO
- next 10 prompts sufficient: YES/NO
- immediate blockers: list
- final claim boundary: accepted/rejected

## Detailed Level 5 Target

Level 5 means:

- SOC, S2P, Trading, Purchasing, and DataOps participate in one common governed AGE-backed judgment-memory architecture.
- SQLite is retained for local/test/rollback fallback, not as the canonical product memory.
- Protocol v2 Decision/Outcome semantics are used consistently.
- Preview/read/research-like paths do not create Decisions unless explicitly intended and tested.
- Rollback is proved per app and does not delete AGE data, copy AGE data back to SQLite, or run hidden reconciliation.
- EvidenceReceipt/audit behavior is explicitly mapped or explicitly excluded from a narrower claim.
- Migration/backfill status is explicit and not hidden in UI/status.
- demo.py supports operator-safe AGE test/product flags and mode status.
- Backend and Playwright smoke gates cover active AGE modes.
- Cross-copilot proof demonstrates domain separation, canonical vocabulary queries, no `soc_graph` contamination, and cross-domain graph integrity.

## Detailed Milestone Evidence Table

| Domain | Current Level | New-write AGE active? | Reviewed/accepted? | Backend tests | Live AGE tests | Playwright | Product graph smoke? | EvidenceReceipt? | Migration/backfill? | demo.py? | Cross-copilot proof? | Product claim safe? | Remaining blockers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SOC | Projection/AGE foundation with P3 | Partial/projection-side, not final domain proof | PASS_WITH_P3 | SOC projection contract tests reported | AGE adapter/projection gates accepted | Not a current app smoke gate | Not complete | Not complete | Not complete | Not complete | Not complete | NO | Final cross-copilot proof, canonical audit, migration caveats |
| S2P | New-write AGE active | YES, Decision/Outcome only under explicit env | ACCEPTED | Full backend reported 941 passed, 10 skipped at final candidate | Test-mode live and parallel live gates accepted | workers=1 and command-level workers=4 accepted; product-mode Playwright not rerun | Not run | Excluded | Excluded | Not implemented | Not complete | NO | EvidenceReceipt, migration/backfill, demo.py, product graph smoke, product-mode Playwright, cross-proof |
| Purchasing | New-write AGE active | YES, Decision/Outcome only under explicit env | ACCEPTED | 167 passed, 1 skipped; new graph/status 20 passed | Guarded live AGE 1 passed | 14 passed, but status endpoint was not validated against restarted backend | Not run | Excluded | Excluded | Not implemented | Not complete | NO | Graph-status Playwright rerun, EvidenceReceipt, migration/backfill, demo.py, product graph smoke, cross-proof |
| Trading | New-write AGE active | YES, Decision/Outcome only under explicit env | ACCEPTED | 726 passed, 1 skipped; graph/status 21 passed | Guarded live AGE 1 passed | 14 passed, but status endpoint was not validated against restarted backend | Not run | Excluded | Excluded | Not implemented | Not complete | NO | Graph-status Playwright rerun, EvidenceReceipt, migration/backfill, demo.py, product graph smoke, cross-proof |
| DataOps | Baseline/semantics plan only | NO | Not yet reviewed in this session | Baseline/discovery 130 passed | Not run | Not run | Not run | Excluded | Excluded | Not implemented | Not complete | NO | Scorer-vs-operational graph separation review, active AGE implementation, live AGE, Playwright, milestone acceptance |

## 4. Documents Created or Updated

Observed implementation-plan documents matching the governed graph migration themes:

| Path | Created/updated | Purpose | Current status | Reviewer acceptance | Type |
| --- | --- | --- | --- | --- | --- |
| `docs/implementation_plans/age_protocol_v2_archive_reset_plan.md` | Created/updated in dirty tree | Protocol v2 archive/reset planning | Needs Opus inventory review | Not confirmed in this handoff | Design |
| `docs/implementation_plans/age_protocol_v2_evidence_receipt_plan.md` | Created/updated in dirty tree | EvidenceReceipt mapping planning | Future work | Not implemented | Design |
| `docs/implementation_plans/age_protocol_v2_skip_triage.md` | Existing/updated candidate | AGE Protocol v2 triage context | Background | Not confirmed here | Design/triage |
| `docs/implementation_plans/age_protocol_v2_write_outcome_plan.md` | Created/updated in dirty tree | Protocol v2 Outcome write planning | Foundation accepted via later milestones | Accepted indirectly by adapter gates | Design |
| `docs/implementation_plans/dataops_governed_graph_semantics_plan.md` | Created | DataOps scorer-vs-operational graph semantics and adoption decision | Pending GPT-5.5/Opus review | Not accepted yet | Design |
| `docs/implementation_plans/graphstore_factory_design_plan.md` | Created | GraphStore factory plan | Accepted | ACCEPTED | Design/implementation plan |
| `docs/implementation_plans/s2p_age_cutover_design_plan.md` | Created/updated | S2P AGE active/cutover plan, product graph guardrails, status, rollback, exclusions | S2P milestone accepted for new writes | ACCEPTED with exclusions | Design plus milestone record |
| `docs/implementation_plans/s2p_age_shadow_design_plan.md` | Created/updated | S2P shadow AGE design | Accepted as part of S2P shadow gates | ACCEPTED | Design |
| `docs/implementation_plans/sdk_apps_governed_graph_adoption_plan.md` | Created/updated | Batch plan for Trading/Purchasing/DataOps adoption using S2P as reference | Reviewed/repaired | PASS/PASS_WITH_P3 style acceptance for planning | Design |
| `docs/implementation_plans/shared_judgment_memory_graph_plan.md` | Created/updated | Common governed graph architecture planning | Background/foundation | Not separately reviewed here | Design |
| `docs/implementation_plans/soc_projection_blocker_plan.md` | Created/updated | SOC projection blocker plan | SOC projection gate later passed with P3 | PASS_WITH_P3 downstream | Design |
| `docs/implementation_plans/soc_projection_gate_report.md` | Created/updated | SOC projection gate report | Accepted with P3 | PASS_WITH_P3 | Gate report |
| `docs/implementation_plans/gap_h1_s2p_agentevolver_design.md` | Observed matching `s2p_age` scan context | S2P/agent-evolver gap context | Background | Not part of final accepted scope | Design/background |
| `docs/implementation_plans/opus_review_handoff_governed_graph_migration.md` | Created by this audit | External Opus handoff inventory | Ready for Opus review | Pending | Audit/report |

Additional supporting docs observed in the dirty tree include:

- `docs/judgment_memory_v2_5.md`
- `docs/judgment_memory_v2_7.md`
- `docs/protocol_v2_design_v1_3.md`
- `docs/protocol_v2_design_v1_5.md`
- `docs/protocol_v2_design_v1_8.md`
- `docs/soc_age_schema_compatibility_spec_v1.md`

## 5. Source Files Changed

The worktree is broad and dirty. The inventory below separates migration-relevant files from additional dirty files observed by `git status`. Generated data, SQLite DB files, Playwright artifacts, and unrelated frontend/demo changes should not be treated as governed graph implementation unless explicitly reviewed.

### copilot-sdk migration-relevant source files

| Path | What changed | Why | Related milestone | Tests cover it | Risk |
| --- | --- | --- | --- | --- | --- |
| `copilot_sdk/graph/factory.py` | New/untracked factory module observed | Central GraphStore construction and AGE/SQLite selection | GraphStore factory, app adoption | `tests/graph/test_graphstore_factory.py`; app graph/status tests | Medium; mypy failure reported |
| `copilot_sdk/graph/protocol.py` | Modified | Protocol v2 Decision/Outcome interface support | Protocol v2, AGE adapter | Protocol v2 tests and live app tests | Medium |
| `copilot_sdk/graph/sqlite_store.py` | Modified | SQLite GraphStore behavior and Protocol v2 compatibility | SQLite fallback and tests | Broad graph/scoring tests | Medium; mypy failure reported |
| `copilot_sdk/graph/memory_store.py` | Modified | In-memory GraphStore compatibility | Unit/fake-store coverage | Graph tests | Low/medium |
| `copilot_sdk/scoring/scorer.py` | Modified | Scorer integration with governed graph behavior | S2P/Purchasing/Trading active AGE semantics | App score/learn tests | Medium |
| `copilot_sdk/scoring/fingerprint.py` | Modified | Scoring fingerprint behavior | Scoring support | Scoring subset | Low/medium |
| `copilot_sdk/scoring/presets/trading.py` | Modified | Trading scoring presets | Trading route surface | Trading backend tests | Medium |
| `copilot_sdk/scoring/presets/trading_bootstrap.json` | Modified | Trading bootstrap factors | Trading scoring | Trading backend tests | Low/medium |
| `copilot_sdk/backend/scoring_router.py` | Modified | Shared score/learn route behavior | Purchasing/Trading | Shared router and app tests | Medium |
| `copilot_sdk/backend/scorer_proxy.py` | Modified | Scorer proxy behavior | SDK apps | App tests | Medium |
| `copilot_sdk/backend/conservation_router.py` | Modified | Conservation/status support | Status/readiness | Backend tests | Low/medium |
| `copilot_sdk/backend/models.py` | Modified | Shared backend models | App response shapes | Backend tests | Medium |
| `apps/purchasing/backend/app/graph_status.py` | New | Purchasing active graph config/status endpoint | Purchasing milestone | `test_purchasing_graph_status.py` | Medium |
| `apps/purchasing/backend/app/main.py` | Modified | Purchasing active AGE wiring/status route | Purchasing milestone | Purchasing backend suite/live test | Medium |
| `apps/purchasing/backend/app/context_router.py` | Modified | App context routing | Purchasing context/status | Purchasing tests | Low/medium |
| `apps/trading/backend/app/graph_status.py` | New | Trading active graph config/status endpoint | Trading milestone | `test_trading_graph_status.py` | Medium |
| `apps/trading/backend/app/main.py` | Modified | Trading active AGE wiring/status route | Trading milestone | Trading backend suite/live test | Medium |
| `apps/trading/backend/app/context_router.py` | Modified | Trading context route behavior | Trading | Trading tests | Low/medium |
| `apps/trading/backend/app/routers/broker_router.py` | Modified | Trading broker/webhook route surface | Trading route-surface gate | Trading backend tests | Medium |
| `apps/trading/backend/app/models/trade.py` | Modified | Trading model support | Trading route surface | Trading tests | Medium |
| `apps/trading/backend/app/factors/registry.py` | Modified | Trading factor registry | Trading score flows | Trading tests | Low/medium |
| `apps/trading/backend/app/factors/signal_confidence.py` | Modified | Trading signal confidence factors | Trading score flows | Trading tests | Low/medium |
| `apps/dataops/backend/app/main.py` | Modified | DataOps app surface in dirty tree | DataOps discovery/planning only | DataOps baseline tests | Medium until reviewed |
| `apps/dataops/backend/app/ae_router.py` | Modified | DataOps operational/evolution route | DataOps semantics risk | DataOps tests | Medium/high until semantics plan accepted |
| `apps/dataops/backend/app/context_router.py` | Modified | DataOps context routing | DataOps semantics | DataOps tests | Medium |
| `apps/dataops/backend/app/routers/dataops_status.py` | Modified | DataOps status route | DataOps discovery | DataOps status tests | Low/medium |

### s2p-copilot migration-relevant source files

| Path | What changed | Why | Related milestone | Tests cover it | Risk |
| --- | --- | --- | --- | --- | --- |
| `backend/app/s2p_graph_status.py` | New | S2P active config, guards, graph status endpoint, product allow-list/status readiness | S2P Phase A-C and final milestone | S2P graph status/product-like tests | Medium |
| `backend/app/s2p_shadow.py` | New/untracked | S2P shadow AGE helper | S2P shadow Phase 1/2/live | Shadow tests | Medium |
| `backend/app/main.py` | Modified | S2P status route and active AGE wiring | S2P active AGE milestone | Full S2P backend tests | Medium |
| `backend/app/routers/s2p.py` | Modified | S2P score/outcome/learn routing | S2P active writes | S2P active/live/preview tests | Medium/high |
| `backend/app/routers/s2p_preview.py` | Modified | Preview/read no-Decision-write safety | S2P preview fixer | `test_s2p_preview.py` | Medium |
| `backend/app/models.py` | Modified | Response/model support | S2P route shapes | S2P backend tests | Medium |
| `backend/app/scoring/engine.py` | Modified | S2P scoring engine support | S2P score path | S2P tests | Medium |
| `backend/app/services/learning.py` | Modified | Outcome/learn behavior | S2P one-outcome invariant | S2P active/live tests | Medium |
| `backend/app/services/persistence.py` | Modified | SQLite persistence fallback | Rollback/default SQLite | S2P tests | Medium |
| `backend/app/services/projection.py` | Modified | Projection behavior | S2P/SOC context | S2P tests | Low/medium |
| `backend/app/services/soc_graph.py` | Modified | SOC graph service boundary | soc_graph protection | S2P tests | Medium |

### ci-platform migration-relevant source files

| Path | What changed | Why | Related milestone | Tests cover it | Risk |
| --- | --- | --- | --- | --- | --- |
| `ci_platform/graph/age_graph_store.py` | Modified, 97 insertions in diff stat | AGE GraphStore support | Protocol v2/AGE adapter/app live tests | AGE adapter/live app tests | Medium |
| `ci_platform/graph/age_sdk_adapter.py` | Referenced/read; no current diff shown by command | SDK adapter support | AGE adapter | Live tests | Medium if changed outside diff not present |
| `ci_platform/graph/age_client.py` | Included in required inventory if changed; no diff shown by command | AGE client support | AGE foundation | AGE tests | Unknown/no current diff |

### gen-ai-roi-demo-v4-v50 dirty source files observed

These were observed by `git status` but are not part of the accepted governed graph app migration scope in this handoff:

- `backend/app/routers/soc.py`
- `backend/app/services/evolver.py`
- `backend/app/services/variant_generator.py`
- `backend/tests/test_d06_unmapped.py`
- `backend/tests/test_evolver_sdk_migration.py`
- `frontend/src/components/tabs/CompoundingTab.tsx`
- centroid backup JSON files under `backend/app/data/centroid_backups/`

### Additional dirty files and artifacts to avoid confusing with migration implementation

- SQLite DB artifacts such as `s2p-copilot/backend/app/data/s2p.db`, `copilot-sdk/apps/purchasing/backend/app/data/purchasing.db`, and `copilot-sdk/apps/trading/backend/app/data/trading.db`.
- Playwright reports and `test-results` artifacts.
- Many frontend files in `copilot-sdk/apps/dataops/frontend`, `apps/purchasing/frontend`, and `apps/trading/frontend` are dirty in the broader worktree. The governed graph milestone reports say no frontend feature changes were part of the accepted S2P/Purchasing/Trading migration scopes.
- `graphify-out/` files and assessment artifacts.

## 6. Test Files Added or Updated

### Protocol v2 / graph foundation

| Path | Purpose | Milestone | Behavior proved | Type/guard |
| --- | --- | --- | --- | --- |
| `tests/graph/test_graphstore_factory.py` | GraphStore factory tests | Factory accepted | SQLite/AGE factory guard behavior | Unit/backend |
| `tests/graph/test_protocol_v2_service_layer.py` | Protocol v2 service tests | Protocol v2 adapter | Decision/Outcome service-layer behavior | Unit/backend |
| `tests/graph/test_protocol_v2_conformance.py` | Protocol v2 conformance | Protocol v2 adapter | Conformance expectations | Unit/backend |
| `tests/graph/test_soc_age_projection_contract.py` | SOC projection contract | SOC projection gate | AGE/SOC projection compatibility | Backend/contract |

### S2P

| Path | Purpose | Milestone | Behavior proved | Type/guard |
| --- | --- | --- | --- | --- |
| `s2p-copilot/backend/tests/test_s2p_shadow_phase1.py` | Shadow config/diagnostics | S2P Shadow Phase 1 | Default behavior, shadow status | Backend |
| `s2p-copilot/backend/tests/test_s2p_shadow_phase2.py` | Shadow dual-write score/outcome | S2P Shadow Phase 2 | Shadow score/outcome behavior | Backend |
| `s2p-copilot/backend/tests/test_s2p_shadow_live_age.py` | Guarded live shadow AGE | S2P live AGE shadow | Live AGE shadow when env enabled | Guarded live AGE |
| `s2p-copilot/backend/tests/test_s2p_graph_status_phase_a.py` | Active config/status, guards, product readiness | S2P Phase A/C1/C2 | Defaults, env guards, redaction, readiness flags | Backend |
| `s2p-copilot/backend/tests/test_s2p_active_age_phase_b.py` | Active AGE fake-store tests | S2P Phase B | Active AGE test-mode score/outcome/rollback semantics | Backend/fake-store |
| `s2p-copilot/backend/tests/test_s2p_active_age_live.py` | Guarded active AGE live tests | S2P Phase B/live | Score/outcome/preview/rollback live test mode | Guarded live AGE |
| `s2p-copilot/backend/tests/test_s2p_active_age_parallel.py` | True parallel active AGE backend gate | S2P parallel gate | 8 independent flows, at least 4 workers, duplicate invariant | Guarded live AGE |
| `s2p-copilot/backend/tests/test_s2p_product_like_phase_c2.py` | Product-like guard/status tests | S2P C2 | Product-like status/guards, construction boundary | Backend/fake-store |
| `s2p-copilot/backend/tests/test_s2p_preview.py` | Preview/read safety | Preview fixer | Preview does not create Decisions | Backend |
| `s2p-copilot/backend/tests/test_pydantic_responses.py` | Response smoke | S2P route response shapes | JSON response success | Backend |
| `copilot-sdk/e2e/s2p/shadow-smoke.spec.ts` | S2P shadow UI smoke | S2P shadow Playwright | UI flow with shadow status | Playwright |
| `copilot-sdk/e2e/s2p/active-age-smoke.spec.ts` | S2P active AGE UI smoke | S2P active AGE Playwright | Page, score, learn/outcome, preview/read, graph status | Playwright |

### Purchasing

| Path | Purpose | Milestone | Behavior proved | Type/guard |
| --- | --- | --- | --- | --- |
| `apps/purchasing/backend/tests/test_purchasing_graph_status.py` | Purchasing config/status and fake-store coverage | Purchasing milestone | Defaults, env guards, active AGE fake-store, rollback, redaction | Backend/fake-store |
| `apps/purchasing/backend/tests/test_purchasing_active_age_live.py` | Purchasing live active AGE test | Purchasing milestone | Guarded live Decision/Outcome write/readback | Guarded live AGE |
| `copilot-sdk/e2e/purchasing/flows.spec.ts` | Purchasing UI flow smoke | Purchasing milestone/regression | Existing Purchasing flows | Playwright |

### Trading

| Path | Purpose | Milestone | Behavior proved | Type/guard |
| --- | --- | --- | --- | --- |
| `apps/trading/backend/tests/test_trading_graph_status.py` | Trading config/status and route surface fake-store coverage | Trading milestone | Defaults, env guards, score/learn/social/webhook/read safety, rollback | Backend/fake-store |
| `apps/trading/backend/tests/test_trading_active_age_live.py` | Trading live active AGE test | Trading milestone | Guarded live Decision/Outcome write/readback | Guarded live AGE |
| `copilot-sdk/e2e/trading/flows.spec.ts` | Trading UI flow smoke | Trading milestone/regression | Existing Trading flows | Playwright |

### DataOps

| Path | Purpose | Milestone | Behavior proved | Type/guard |
| --- | --- | --- | --- | --- |
| `apps/dataops/backend/tests/test_dataops_backend.py` | DataOps backend baseline | DataOps discovery | Baseline app behavior | Backend |
| `apps/dataops/backend/tests/test_graph_queries.py` | DataOps graph query baseline | DataOps semantics discovery | Operational graph/query behavior | Backend |
| `apps/dataops/backend/tests/test_dataops_status.py` | DataOps status baseline | DataOps semantics discovery | Status behavior | Backend |
| `copilot-sdk/e2e/dataops/flows.spec.ts` | DataOps UI flows | Future DataOps adoption | Existing UI flows | Playwright, not rerun for active AGE |

## 7. Test Runs and Results

Dates/times were not available from persistent logs in this audit; results below are the reported results from the migration session and the command categories used.

### Protocol v2 / graph

- GraphStore factory: accepted; graph factory tests were part of shared subset runs.
- Purchasing shared graph/scoring subset: 195 passed.
- Trading graph factory + scoring subset: 157 passed.
- Known unresolved broad failures include two structural GraphStore protocol tests and two mypy tests.

### SOC projection

- SOC projection gate: PASS_WITH_P3.
- SOC projection contract tests were created/updated and accepted as a gate with P3 caveats.

### S2P backend

- Shadow Phase 1: 17 passed.
- Shadow Phase 2: 11 passed.
- Preview route: 37 passed.
- Pydantic response smoke: 1 passed.
- Phase A graph status: 10 passed initially, later 15 passed after guard expansion.
- Phase B fake-store active AGE: 5 passed initially, later 7 passed.
- C1 product graph allow-list/status: 20 passed.
- Parallel gate default: 1 skipped.
- C2 status/product-like tests: 33 passed.
- Completion candidate targeted product/status/active tests: 43 passed.
- Full backend results reported across milestones: 908 passed/4 skipped, 918 passed/8 skipped, 925 passed/9 skipped, 927 passed/10 skipped, 938 passed/10 skipped, and final 941 passed/10 skipped.

### S2P live AGE

- Shadow live AGE default: 4 skipped by default.
- Guarded active AGE live: 4 passed.
- Guarded true parallel active AGE live: 1 passed.
- Live product `governed_copilot_graph`: not run.

### S2P Playwright

- `npx playwright test s2p/active-age-smoke.spec.ts --project=s2p --workers=1 --reporter=list`: 1 passed.
- `npx playwright test s2p/active-age-smoke.spec.ts --project=s2p --workers=4 --reporter=list`: 1 passed.
- Caveat: workers=4 was command-level only because Playwright reported one matching test using one worker, so it did not create true parallel UI pressure.
- Product-mode Playwright was not rerun.

### Purchasing backend

- Baseline Purchasing backend tests: 147 passed.
- Baseline shared router tests: 38 passed.
- New graph/status tests: 20 passed.
- Purchasing backend suite: 167 passed, 1 skipped.
- Shared graph factory/backend/scoring subset: 195 passed.

### Purchasing live AGE

- Guarded live AGE: 1 passed.
- Live AGE was enabled only under explicit `PURCHASING_ACTIVE_LIVE_AGE_TEST=1` and app-specific `PURCHASING_ACTIVE_*` env.

### Purchasing Playwright

- Purchasing Playwright flows: 14 passed.
- Caveat: already-running backend did not expose graph status, so this was UI regression smoke, not active-status validation.

### Trading backend

- Baseline Trading route slice: 79 passed.
- New graph/status tests: 21 passed.
- Trading backend suite: 726 passed, 1 skipped.
- Graph factory + scoring subset: 157 passed.

### Trading live AGE

- Guarded live Trading AGE: 1 passed.
- Live AGE was enabled only under explicit `TRADING_ACTIVE_LIVE_AGE_TEST=1` and app-specific `TRADING_ACTIVE_*` env.

### Trading Playwright

- Trading Playwright flows: 14 passed.
- Caveat: already-running backend did not expose the new graph status endpoint, so this was UI regression smoke, not active-status validation.

### DataOps baseline

- Discovery-safe DataOps baseline: `python -m pytest apps/dataops/backend/tests/test_dataops_backend.py apps/dataops/backend/tests/test_graph_queries.py apps/dataops/backend/tests/test_dataops_status.py -q --timeout=120`: 130 passed.
- No DataOps active AGE implementation or live AGE test was run.

### Broad suite failures

- Broad suite after Purchasing: 1011 passed, 67 skipped, 4 failed.
- Reported failures:
  - `tests/test_graph_entity_links.py::test_minimal_structural_graphstore_still_satisfies_graphstore_protocol`
  - `tests/test_graphstore_consolidation.py::test_graphstore_protocol_remains_narrow_for_entity_link_helpers`
  - `tests/test_type_checking.py::test_mypy_passes_with_config`
  - `tests/test_type_checking.py::test_unsuppressed_mypy_targets_pass_individually`
- Reported mypy errors:
  - `copilot_sdk\graph\sqlite_store.py:904: error: Incompatible return value type (got "tuple[Any, ...]", expected "tuple[int, str]")`
  - `copilot_sdk\graph\factory.py:175: error: Returning Any from function declared to return "GraphStore"`
- These were treated as unrelated to the Purchasing milestone, but they remain unresolved and should be reviewed before a final Level 5 claim.

## 8. Accepted Milestones

| Milestone | Acceptance status | Accepted scope | Explicit exclusions |
| --- | --- | --- | --- |
| AGE Protocol v2 adapter | ACCEPTED | Protocol v2 adapter foundation | Final EvidenceReceipt/product claim not included |
| SOC projection gate | PASS_WITH_P3 | SOC projection compatibility | Remaining SOC P3/cross-copilot proof |
| GraphStore factory | ACCEPTED | Factory construction pattern | App cutovers not included |
| S2P Shadow Phase 1 | ACCEPTED | Config/diagnostics shadow setup | Active cutover |
| S2P Shadow Phase 2 | ACCEPTED | Score/outcome dual-write shadow | Product cutover |
| S2P live AGE shadow | ACCEPTED | Guarded live shadow testing | Product graph writes |
| S2P preview/read no-Decision-write fixer | ACCEPTED | Preview/read safety | Active cutover |
| S2P active AGE Phase B | ACCEPTED | Test-mode active AGE backend | Product graph cutover |
| S2P Playwright workers=1 | ACCEPTED | Active AGE test-mode UI smoke | Product mode |
| S2P Playwright workers=4 command | PASS_WITH_P3 | Command-level workers=4 smoke | True UI parallel pressure |
| S2P true parallel backend gate | ACCEPTED | Parallel active AGE backend pressure | Product graph live smoke |
| S2P C1/C2 | ACCEPTED | Product allow-list/status hardening and product-like guards | Live product graph writes until final explicit env implementation |
| S2P final milestone | ACCEPTED | New Decision/Outcome AGE active under explicit env | Migration/backfill, EvidenceReceipt, product/external claim |
| SDK apps adoption plan | Reviewed/repaired | Purchasing first, Trading second, DataOps last/blocker | Implementation itself |
| Purchasing milestone | ACCEPTED | New Decision/Outcome AGE active under explicit env | Product graph cutover, migration/backfill, EvidenceReceipt |
| Trading milestone | ACCEPTED | New Decision/Outcome AGE active under explicit env plus route surface | Product graph cutover, migration/backfill, EvidenceReceipt |
| DataOps semantics plan | Created | Discovery/design decision | Not reviewed/accepted; no implementation |

## 9. Known Unresolved Failures

| Issue | Evidence | Related to migration? | Blocker? | Recommended owner/fix |
| --- | --- | --- | --- | --- |
| Broad suite 4 failures after Purchasing | 1011 passed, 67 skipped, 4 failed | PARTIAL | Not milestone blocker, but Level 5 blocker until triaged | Shared SDK graph owner |
| Structural GraphStore protocol failures | `test_graph_entity_links.py`, `test_graphstore_consolidation.py` failures | YES/PARTIAL | Not Purchasing/Trading milestone blocker; may block clean SDK claim | GraphStore factory/protocol owner |
| mypy failure in `sqlite_store.py` | Return type `tuple[Any, ...]` vs `tuple[int, str]` at line 904 | YES/PARTIAL | Not app milestone blocker; blocks type-clean claim | Graph SQLite owner |
| mypy failure in `factory.py` | Returning `Any` from function declared `GraphStore` at line 175 | YES | Not app milestone blocker; should be fixed before final architecture claim | Graph factory owner |
| pytest cache permission warnings | Reported during validation | NO | NO | Local environment cleanup |
| Live row accumulation in `protocol_v2_test` | Guarded live tests avoid broad deletion and use unique IDs | YES/P3 | NO | Add retention/cleanup plan or test graph lifecycle |
| Stale live stacks causing 404 graph status during Playwright | Purchasing/Trading UI smoke ran against already-running backend without new status endpoint | PARTIAL | NO for backend milestone; YES for final E2E status proof | Rerun Playwright after restarting matching backend |
| Dirty SQLite DB files | `backend/app/data/s2p.db`, app DB files modified | PARTIAL | NO unless accidentally committed | Do not commit DB artifacts; add cleanup/ignore policy if needed |
| Product live `governed_copilot_graph` not run | S2P/Purchasing/Trading product live smoke deferred | YES | Blocks product/external claim | Operator-approved live product graph smoke |
| EvidenceReceipt not implemented | Explicitly excluded in S2P/Purchasing/Trading | YES | Blocks full audit-memory claim | EvidenceReceipt mapping implementation |
| Migration/backfill not implemented | Explicitly excluded | YES | Blocks historical continuity claim | Migration/backfill design and implementation |

## 10. Remaining Level 5 Gaps

- DataOps is not implemented beyond baseline/discovery and semantics/adoption planning.
- EvidenceReceipt mapping is not implemented across S2P, Purchasing, Trading, or DataOps.
- Historical migration/backfill is not implemented across apps.
- demo.py AGE flags/status are not implemented.
- Product `governed_copilot_graph` live smoke was not run.
- Product-mode Playwright validation is not complete across S2P, Purchasing, or Trading.
- Cross-copilot proof is not implemented.
- SOC forward-write/canonical audit caveats remain dependent on SOC projection P3s and final cross-copilot proof.
- Broad suite GraphStore/mypy failures remain unresolved.
- Full product/external claim is not safe.

## 11. Risk Assessment

### P1/P2 risks

- No current accepted app milestone was reported with P1/P2 blockers.
- The unresolved broad GraphStore/mypy failures are not app milestone blockers as reviewed, but they are correctness/type-safety risks for a final SDK-wide claim.
- DataOps remains a blocker for the full common architecture because active AGE adoption has not been implemented or accepted.

### P3/backlog risks

- Product-mode Playwright and live product graph smoke are deferred.
- Live test row accumulation in `protocol_v2_test` requires lifecycle policy.
- Existing Playwright results for Purchasing/Trading did not validate graph status against a restarted backend.
- Dirty generated data and DB files may obscure review unless excluded carefully.

### Product-claim blockers

- EvidenceReceipt mapping is excluded.
- Migration/backfill is excluded.
- DataOps is not adopted.
- Cross-copilot proof is missing.
- Product live graph smoke and product-mode Playwright are incomplete.
- demo.py operational status/flags are missing.

### Data-safety risks

- Rollback is explicitly no-copy-back/no-hidden-reconciliation, so AGE-only writes remain AGE-only after SQLite rollback.
- Historical SQLite records are not automatically visible in AGE-active mode unless migrated.
- Live test data accumulates unless retention is managed.
- `soc_graph` must remain forbidden for non-SOC write paths.

### Architecture risks

- DataOps operational graph semantics may be conflated with scorer Decision/Outcome semantics unless the blocker plan is reviewed and enforced.
- Cross-domain graph proof is still absent.
- EvidenceReceipt and migration boundaries must remain visible to avoid false “fully migrated” claims.

## Opus Review Checklist

1. Are any claims overstated?
2. Are Level 5 goals complete and testable?
3. Are S2P, Purchasing, and Trading correctly scoped as new Decision/Outcome only?
4. Are DataOps, EvidenceReceipt, migration/backfill, demo.py, and cross-copilot proof correctly marked blocking?
5. Are broad GraphStore/mypy failures serious enough to block final acceptance?
6. Are dirty/generated artifacts separated from implementation?
7. What is the shortest safe path to Level 5?

## Commit Readiness / Do Not Commit

| Category | Examples | Action |
| --- | --- | --- |
| Commit candidates | Reviewed source/test/doc files for accepted governed graph milestones | Include only after human review confirms they are intentional and related |
| Do not commit | SQLite DBs, Playwright reports, `test-results`, cache files, local PID/process files, local live-test data dumps | Exclude/remove before commit |
| Needs human decision | Generated centroid backups, `graphify-out`, unrelated frontend/SOC dirty files | Review separately; commit only if intentionally part of a reviewed SOC/demo deliverable |

## 13. Appendix: Commands to Reproduce

### Status inspection

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
git status --short
git diff --name-only
git diff --stat
git ls-files docs/implementation_plans
git ls-files e2e
git ls-files apps/trading apps/purchasing apps/dataops copilot_sdk/graph copilot_sdk/scoring tests
git diff -- docs/implementation_plans
git diff -- apps/trading apps/purchasing apps/dataops copilot_sdk/graph copilot_sdk/scoring tests e2e
```

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot"
git status --short
git diff --name-only
git diff --stat
git ls-files backend/app backend/tests
git diff -- backend/app backend/tests
```

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\ci-platform"
git status --short
git diff --name-only
git diff --stat
git diff -- ci_platform/graph
```

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50"
git status --short
git diff --name-only
git diff --stat
```

### Targeted S2P tests

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot\backend"
python -m py_compile app/s2p_shadow.py app/s2p_graph_status.py
python -m pytest tests/test_s2p_graph_status_phase_a.py -q --timeout=120
python -m pytest tests/test_s2p_product_like_phase_c2.py -q --timeout=120
python -m pytest tests/test_s2p_active_age_phase_b.py -q --timeout=120
python -m pytest tests/test_s2p_active_age_live.py -q --timeout=120 -rs
python -m pytest tests/test_s2p_active_age_parallel.py -q --timeout=120 -rs
python -m pytest tests/test_s2p_preview.py -q --timeout=120
python -m pytest tests/ -q --timeout=120
```

### Targeted Purchasing tests

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -m pytest apps/purchasing/backend/tests/test_purchasing_graph_status.py -q --timeout=120
python -m pytest apps/purchasing/backend/tests/test_purchasing_active_age_live.py -q --timeout=120 -rs
python -m pytest apps/purchasing/backend/tests -q --timeout=120
```

### Targeted Trading tests

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -m pytest apps/trading/backend/tests/test_trading_graph_status.py -q --timeout=120
python -m pytest apps/trading/backend/tests/test_trading_active_age_live.py -q --timeout=120 -rs
python -m pytest apps/trading/backend/tests -q --timeout=120
```

### DataOps baseline

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -m pytest apps/dataops/backend/tests/test_dataops_backend.py apps/dataops/backend/tests/test_graph_queries.py apps/dataops/backend/tests/test_dataops_status.py -q --timeout=120
```

### Guarded live AGE test envs

Windows PowerShell must use the Windows port proxy at `127.0.0.1:5433`; do not assume bare `psql` is available on Windows.

```powershell
$env:S2P_ACTIVE_LIVE_AGE_TEST="1"
$env:S2P_ACTIVE_GRAPH_BACKEND="age"
$env:S2P_ACTIVE_AGE_TEST_MODE="1"
$env:S2P_ACTIVE_AGE_GRAPH="protocol_v2_test"
$env:S2P_ACTIVE_AGE_DOMAIN="s2p"
$env:S2P_ACTIVE_AGE_DSN="postgresql://postgres:postgres@127.0.0.1:5433/soc_copilot?connect_timeout=5"
python -m pytest tests/test_s2p_active_age_live.py -q --timeout=180 -rs
```

```powershell
$env:S2P_ACTIVE_PARALLEL_AGE_TEST="1"
$env:S2P_ACTIVE_GRAPH_BACKEND="age"
$env:S2P_ACTIVE_AGE_TEST_MODE="1"
$env:S2P_ACTIVE_AGE_GRAPH="protocol_v2_test"
$env:S2P_ACTIVE_AGE_DOMAIN="s2p"
$env:S2P_ACTIVE_AGE_DSN="postgresql://postgres:postgres@127.0.0.1:5433/soc_copilot?connect_timeout=5"
python -m pytest tests/test_s2p_active_age_parallel.py -q --timeout=180 -rs
```

```powershell
$env:PURCHASING_ACTIVE_LIVE_AGE_TEST="1"
$env:PURCHASING_ACTIVE_GRAPH_BACKEND="age"
$env:PURCHASING_ACTIVE_AGE_TEST_MODE="1"
$env:PURCHASING_ACTIVE_AGE_GRAPH="protocol_v2_test"
$env:PURCHASING_ACTIVE_AGE_DOMAIN="purchasing"
$env:PURCHASING_ACTIVE_AGE_DSN="postgresql://postgres:postgres@127.0.0.1:5433/soc_copilot?connect_timeout=5"
python -m pytest apps/purchasing/backend/tests/test_purchasing_active_age_live.py -q --timeout=180 -rs
```

```powershell
$env:TRADING_ACTIVE_LIVE_AGE_TEST="1"
$env:TRADING_ACTIVE_GRAPH_BACKEND="age"
$env:TRADING_ACTIVE_AGE_TEST_MODE="1"
$env:TRADING_ACTIVE_AGE_GRAPH="protocol_v2_test"
$env:TRADING_ACTIVE_AGE_DOMAIN="trading"
$env:TRADING_ACTIVE_AGE_DSN="postgresql://postgres:postgres@127.0.0.1:5433/soc_copilot?connect_timeout=5"
python -m pytest apps/trading/backend/tests/test_trading_active_age_live.py -q --timeout=180 -rs
```

### Playwright smoke commands

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
npx playwright test s2p/active-age-smoke.spec.ts --project=s2p --workers=1 --reporter=list
npx playwright test s2p/active-age-smoke.spec.ts --project=s2p --workers=4 --reporter=list
npx playwright test purchasing/flows.spec.ts --project=purchasing --workers=1 --reporter=list
npx playwright test trading/flows.spec.ts --project=trading --workers=1 --reporter=list
npx playwright test dataops/flows.spec.ts --project=dataops --workers=1 --reporter=list
```

## Handoff Readiness

- Ready for Opus review: YES.
- Ready for Level 5 claim: NO.
- Ready for implementation resumption: YES, after Opus or the user approves the next task.
- Recommended next implementation: shared GraphStore/mypy failure cleanup, then DataOps active AGE.
- Remaining ambiguity: whether EvidenceReceipt and migration/backfill will be implemented or explicitly excluded from a narrowed product claim; whether product `governed_copilot_graph` smoke is approved for live writes; whether broad dirty artifacts are intended or must be cleaned before commit.
