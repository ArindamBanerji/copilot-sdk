# P74/P75 Purchasing IKS + Trust Audit/Implementation Report

Date: 2026-06-07
Model: gpt-5.5
Task Type: Prerequisite-aware implementation cycle
Repo: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk
Design Doc: docs/design/purchasing_copilot_pd_v1_3.md

## Executive Summary
- P74 status: COMPLETE
- P75 status: COMPLETE
- Files created: copilot_sdk/scoring/iks_service.py; apps/purchasing/backend/app/routers/iks.py; apps/purchasing/backend/app/routers/trust.py; tests/test_iks_service.py; apps/purchasing/backend/tests/test_iks_trust.py
- Files modified: copilot_sdk/__init__.py; apps/purchasing/backend/app/main.py; docs/implementation_plans/purchasing_p74_p75_iks_trust_audit_impl.md
- IKSService import path used: copilot_sdk.IKSService, backed by copilot_sdk.scoring.iks_service.IKSService
- Tests run: SDK wrapper tests, P74/P75 endpoint tests, Purchasing regression selector with unrelated stale q_window test documented
- Remaining gaps: No P74/P75 implementation gaps found in the audited scope. Supplier scorecard falls back to labeled fixture context when graph-store supplier history is absent.
- Recommended next action: P74/P75 implementation cycle complete; separately fix stale `test_q_window_unchanged` if the full Purchasing selector must pass without exclusions.

## Path Resolution
- Repo path: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk
- Purchasing backend path: apps/purchasing/backend
- Design doc found: YES
- main.py found: YES
- Existing iks/trust/scorecard files found before implementation: None found under apps/purchasing/backend.
- IKSService path found: FOUND_CANONICAL_LOGIC initially; service wrapper added at copilot_sdk/scoring/iks_service.py.

## SDK IKS Prerequisite
- Classification: FOUND_CANONICAL_LOGIC
- Evidence: copilot_sdk/framework/iks_base.py defines canonical centroid IKS logic; copilot_sdk/scoring/trajectory.py defines canonical verified-decision trajectory IKS logic.
- Fix applied: Added `IKSService` in copilot_sdk/scoring/iks_service.py as a thin service over `compute_trajectory`.
- Export: copilot_sdk/__init__.py exports `IKSService`.
- Import validation: `from copilot_sdk import IKSService` resolves to `copilot_sdk.scoring.iks_service.IKSService`.
- SDK evidence: copilot_sdk/scoring/iks_service.py:7 imports `compute_trajectory`; line 10 defines `IKSService`; lines 28 and 42 call `compute_trajectory`.

## Spec Evidence
- P74 F9 IKS evidence: docs/design/purchasing_copilot_pd_v1_3.md:539 says `F9: IKS Tracker | IKS 0->62 trajectory. Per-category breakdown.`; docs/design/purchasing_copilot_pd_v1_3.md:842 lists `/api/purchasing/iks | GET | IKS score and trend`.
- P74 F10 scorecard evidence: docs/design/purchasing_copilot_pd_v1_3.md:540 says `F10: Supplier Scorecard | OTIF, pricing, exception rate, seasonal patterns. Price memory: last 5 rates.`; docs/design/purchasing_copilot_pd_v1_3.md:844 lists supplier scorecard plus price memory.
- P75 F11 trust analysis evidence: docs/design/purchasing_copilot_pd_v1_3.md:541 says `F11: Trust Analysis [HERO] | Radar chart: expected vs actual factor importance (DK weights). Trust trap.`; docs/design/purchasing_copilot_pd_v1_3.md:965 gives the hero line.

## Audit Findings Before Implementation
- Existing IKS implementation: ABSENT in Purchasing backend.
- Existing supplier scorecard implementation: ABSENT in Purchasing backend.
- Existing trust implementation: ABSENT in Purchasing backend.
- Existing IKSService: ABSENT as a service class, but canonical SDK IKS logic existed.
- Existing DK/scorer data access: `CompoundingScorer.get_dk_weights()` exists and `FreshScorerProxy` exposes `_scorer()` for the active scorer.
- Existing graph/outcome/supplier history access: Existing router patterns use scorer proxy graph store; Purchasing data helpers provide supplier/order fixture context.

## Implementation Summary

P74 IKS:
- Endpoint: GET /api/purchasing/iks
- IKSService import: `from copilot_sdk import IKSService`
- Response model: `iks`, `per_category`, `trajectory`, `verified_count`, `available`, `source`
- per_category behavior: Returns one IKS value for each of the five Purchasing categories.
- no verified decisions behavior: Returns `iks=0.0`, `available=false`, and a valid five-category breakdown.
- Evidence: apps/purchasing/backend/app/routers/iks.py:23 defines the router; line 26 registers `/iks`; line 29 instantiates `IKSService`.

P74 Supplier Scorecard:
- Endpoint: GET /api/purchasing/suppliers/{supplier_id}/scorecard
- Data source: Uses graph-store verified decisions when supplier rows exist; falls back to labeled fixture context otherwise.
- OTIF calculation: Graph rows calculate OTIF from row/metadata/context boolean values; fixture fallback uses supplier `otif_score`.
- exception_rate calculation: Graph rows calculate exception rate from row/metadata/context boolean values; fixture fallback uses supplier `exception_rate`.
- price_memory behavior: Graph rows return last invoice prices by category; fixture fallback returns last five verified fixture order values.
- unknown supplier behavior: Returns 404.
- Evidence: apps/purchasing/backend/app/routers/iks.py:37 registers the scorecard endpoint; line 85 returns graph price memory; line 87 labels graph source; line 110 labels fixture fallback.

P75 Trust Analysis:
- Endpoint: GET /api/purchasing/trust
- Display names: Required seven display names are defined in `DISPLAY_NAMES`.
- Expected weight: `1.0 / 7.0`.
- Actual weight source: Reads DK weights from scorer state via `get_dk_weights()` when available.
- DK unavailable behavior: Returns `available=false`, all seven display-name factors, and expected weights only.
- trust_trap rule: `actual_weight < expected_weight * 0.5`.
- hero narrative: `The factor you trust most is the one that lies to you.`
- Evidence: apps/purchasing/backend/app/routers/trust.py:10 defines display names; line 19 sets expected weight; line 20 sets the hero narrative; line 26 registers `/trust`; line 49 implements the trust trap rule; line 58 reads `get_dk_weights`.

Router Wiring:
- main.py imports `create_iks_router` and `create_trust_router`.
- main.py registers `/api/purchasing/iks`, `/api/purchasing/suppliers/{supplier_id}/scorecard`, and `/api/purchasing/trust` once.
- Evidence: apps/purchasing/backend/app/main.py:32 and line 35 import routers; line 409 registers IKS; line 412 registers trust.

## Tests and Validation
- Command: `python -m pytest tests/test_iks_service.py -v --tb=short`
  Result: PASS, 3 passed.
  Relevant coverage: SDK `IKSService` root import, no verified decisions, per-category trajectory breakdown.
- Command: `python -m pytest tests/test_iks_trust.py -v --tb=short`
  Result: PASS, 9 passed.
  Relevant coverage: `/iks`, no verified decisions, supplier scorecard, unknown supplier, `/trust` display names, trust trap, DK unavailable, no `price_memory_index` leak, main app registration.
- Command: `python -m pytest tests -q --tb=short -k "iks or trust or supplier or scorecard or evidence or health or purchasing"`
  Result: FAIL, 193 passed, 1 skipped, 1 failed.
  Notes: Failure is unrelated stale `tests/test_purchasing_config_migration.py::test_q_window_unchanged`, which expects `PurchasingPreset` not to have `q_window`; this contradicts the prior P65 q_window fix.
- Command: `python -m pytest tests -q --tb=short -k "(iks or trust or supplier or scorecard or evidence or health or purchasing) and not q_window_unchanged"`
  Result: PASS, 193 passed, 1 skipped, 1 deselected.
  Relevant coverage: Small Purchasing backend regression slice excluding the known stale unrelated test.

## Built-In Self-Review
- SDK prerequisite reviewed: YES; canonical SDK IKS logic existed and a service wrapper was added over it.
- SDK wrapper reviewed: YES; it delegates to `compute_trajectory` and does not copy formulas into Purchasing.
- Source changes reviewed: YES; changes are within allowed SDK, Purchasing router/main, tests, and report scope.
- Tests reviewed: YES; endpoint test file has 9 tests, exceeding the 8-test acceptance gate.
- Router registration reviewed: YES; P74/P75 routers are registered once.
- IKSService usage reviewed: YES; Purchasing imports SDK `IKSService`.
- Display-name-only response reviewed: YES; `/trust` response rows contain display names and do not expose factor code names.
- Document freshness reviewed: YES; previous BLOCKED/DEFERRED status is replaced with current COMPLETE status.
- Remaining contradictions: Only unrelated stale q_window test remains outside P74/P75 scope.
- Self-review verdict: PASS

## Final Decision Table
Prompt | Status | Evidence | Next Action
P74 PUR-IKS-SCORECARD | COMPLETE | SDK `IKSService` exposed; `/api/purchasing/iks` and `/api/purchasing/suppliers/{supplier_id}/scorecard` implemented and tested. | No P74 action needed in audited scope.
P75 PUR-TRUST-ANALYSIS | COMPLETE | `/api/purchasing/trust` implemented with display names, expected weight, DK weight handling, trust trap rule, and tests. | No P75 action needed in audited scope.

## Limitations
- Supplier scorecard uses graph-store verified decisions when available and explicitly labels fixture fallback as `fixture_context`.
- Scorecard graph-backed behavior is verified with mock graph-store rows; live graph-store supplier history was not E2E validated.
- DK weights are returned when active scorer state exposes them; otherwise `/trust` returns `available=false` without fake actual weights.
- No frontend behavior was validated.
