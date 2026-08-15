# RL-SAFETY Execution Plan — Remove Fail-Open GREEN Paths

Audit date: 2026-08-15  
Status: design-only, verified execution plan. No production or test source
files are to be changed as part of this plan.

The governing contract is explicit: GREEN must be positively established by
the live conservation source. Missing, unknown, stale, malformed,
CALIBRATING, AMBER, RED, and provider-error states must not be converted to
promotion-safe GREEN (copilot-sdk/docs/design/rl_architecture.md:39-53).
The SDK gate already fails closed for missing or unsafe state
(copilot-sdk/copilot_sdk/evolution/gate.py:73-89); this plan removes upstream
paths that manufacture or accept an unverified safe state.

## 1. Current-state verification

### B1 — SOC effective conservation status: confirmed

File: gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:371-395.

Current behavior:

- missing health["status"] defaults to "GREEN" at line 373;
- CALIBRATING is returned as GREEN at lines 377-378;
- AMBER or RED with fewer than the calibration threshold is returned as GREEN
  at lines 387-393;
- only auto_pause_active forces RED at lines 374-375.

This is a confirmed safety violation. Existing tests encode the old behavior:
gen-ai-roi-demo-v4-v50/backend/tests/test_soc_dk_l5.py:48-59 expects
under-calibrated RED to become GREEN. That expectation must change.

Blast radius:

- one direct caller at triage.py:2084;
- the result is persisted in L5 metadata at triage.py:2085-2089;
- the exception path initializes _eff_status to GREEN at triage.py:2062-2064;
- raw-health recording has a second missing-status GREEN fallback at
  triage.py:2086-2088.

### B2 — Purchasing status helper: confirmed

File: copilot-sdk/apps/purchasing/backend/app/main.py:570-581.

Current behavior:

- an override dictionary with no category/state/default becomes GREEN at line
  574;
- a computed payload with no status/state becomes GREEN at line 581;
- a thrown provider computation returns UNAVAILABLE at lines 577-580.

The first two paths are confirmed fail-open behavior. Missing or malformed
state must become UNKNOWN; present validated state must be returned unchanged
after normalization. Direct callers are main.py:615 and :627.

### B5 — Explicit promotion state bypass: confirmed

File: copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:158-168,297-308.

Current behavior:

- check_for_promotion accepts caller-supplied conservation_state;
- _resolve_conservation_state immediately returns explicit state at lines
  297-299;
- only absent explicit state causes the configured provider to be called;
- no provider/no explicit state is eventually blocked by the gate, but explicit
  GREEN can override the configured live provider.

The non-test source sweep found no current literal GREEN caller assignment,
but the public method permits one. This is confirmed as a capability-level
safety bypass. S2P passes explicit state from
s2p-copilot/backend/app/routers/s2p_evolution.py:56-59, and SDK unit tests
intentionally pass GREEN to exercise low-level gate mechanics.

## 2. Additional fail-open paths

The broad search found legitimate computed GREEN values and demo/report
fixtures. They must be classified, not mechanically replaced. These are the
additional safety-relevant candidates:

| Priority | Location | Current behavior | Required disposition |
|---|---|---|---|
| High | SOC triage.py:2062-2064 | Exception path initializes _eff_status = GREEN | Initialize UNKNOWN; retain the fail-closed block. |
| High | SOC triage.py:2086-2088 | Missing raw health status is recorded as GREEN | Record UNKNOWN; preserve present raw status. |
| High | Purchasing predictive_par.py:48-63,121-129 | Missing conservation status defaults to GREEN | Default UNKNOWN so the existing non-GREEN block runs. |
| High | Purchasing alert_engine.py:142-153 | Empty state suppresses the conservation warning | Treat missing state as UNKNOWN and warn. |
| Review | SOC soc.py:3506,4189-4205,4257; evidence_room.py:224 | Several report/enrichment surfaces default to GREEN | Trace each to action/promotion; leave display-only values only with provenance. |
| Review | Purchasing multi_unit.py:210 and fixture constants | Missing per-unit conservation falls back to GREEN | Change to UNKNOWN if it reaches auto-action; otherwise label as fixture/display. |

Not automatically bugs: GREEN computed from verified counts in Purchasing
evidence.py:224-227 and queue.py:331-344, and learning-health's actual
conservation calculation at learning_health.py:334. These still need positive
evidence tests, but are not manufactured defaults.

## 3. Blast-radius map

### Callers and tests

- B1: 1 direct helper caller, plus two adjacent defaults in the same monitor
  block.
- B2: 2 direct helper callers, plus predictive-par and alert-provider paths.
- B5: one SDK promotion resolver used by all PromptVariantEvolver instances;
  explicit state callers exist in S2P and SDK tests.
- Direct SOC coverage: 4 tests in test_soc_dk_l5.py, including the three
  conservation-function tests at lines 48-84.
- Direct Purchasing coverage: test_conservation_status_returns_live_counts
  at test_purchasing_backend.py:616-637, plus three predictive-par tests
  setting explicit GREEN at test_predictive_par.py:80,137,154.
- SDK explicit-state coverage: test_prompt_promotion_gate.py, test_gate.py,
  test_conservation_gate_coverage.py, test_evolver.py, and test_plateau.py.

A search found 21 PW spec files containing conservation/GREEN references,
including conservation.spec.ts, checklist.spec.ts,
cross_tab_consistency.spec.ts, governance/evidence-room specs, and S2P
preview/provenance specs. These are UI/API regression surfaces, not substitutes
for backend branch tests.

### Collection baselines

Read-only collection checks produced:

- SOC backend: 2,262 tests collected;
- Purchasing backend: 691 tests collected;
- SDK keyword selection conservation/green/evolution/gate: 278 selected out
  of 2,262 SDK tests.

These are collection counts, not pass counts.

## 4. Per-bug fix specification

### B1 — SOC status preserves reality

Files: triage.py:371-395 and triage.py:2062-2092; tests:
backend/tests/test_soc_dk_l5.py:48-84.

Before: missing becomes GREEN; CALIBRATING becomes GREEN; early AMBER/RED
becomes GREEN to avoid pausing during calibration; exception state starts as
GREEN.

After:

1. Normalize missing, empty, and unrecognized health status to UNKNOWN.
2. Return CALIBRATING unchanged.
3. Return actual AMBER/RED unchanged, including under-calibrated states.
4. Preserve auto_pause_active to RED.
5. Initialize effective and raw metadata to UNKNOWN before the health call;
   exception handling records UNKNOWN and continues to block learning.
6. If learning should proceed during calibration, represent that as a separate
   explicitly named learning-policy decision, never as conservation GREEN.

Tests: change the old under-calibrated expectation; add missing, empty,
CALIBRATING, AMBER, RED, unknown, provider-exception, and auto-pause cases.
Add an integration assertion that exception metadata is UNKNOWN and learning
is blocked. Add a static check rejecting unverified GREEN in this monitor path.

### B2 — Purchasing status is UNKNOWN unless proven

Files: apps/purchasing/backend/app/main.py:570-581; adjacent
services/predictive_par.py:48-63,121-129 and services/alert_engine.py:142-153.

Before: malformed override and missing computed status become GREEN.

After:

1. Normalize absent override and payload fields to UNKNOWN.
2. Preserve validated actual status, including CALIBRATING/AMBER/RED.
3. Normalize provider exceptions to UNKNOWN or a typed unavailable state that
   every gate treats exactly as UNKNOWN.
4. Use one normalized provider result for evolver and action helpers.
5. Change predictive-par's default argument and row fallback to UNKNOWN.
6. Make empty alert status conservative rather than silently suppressing the
   conservation warning.

Auto-ordering already blocks every status other than GREEN
(services/auto_order.py:117-127), so UNKNOWN is conservative. Tests should add
malformed override, empty dict, missing payload status, exception,
CALIBRATING/AMBER/RED, positive GREEN, predictive missing-status, and
alert-empty-status cases.

### B5 — Configured provider is authoritative

File: copilot_sdk/evolution/prompt_evolver.py:158-168,297-308.

Before: explicit state wins; provider is consulted only when explicit state is
absent.

After:

1. If explicit state is supplied, log a warning that production promotion
   state is ignored/deprecated.
2. If a configured provider exists, call it and use its result regardless of
   explicit state.
3. If provider invocation fails, return UNKNOWN and never fall back to
   explicit GREEN.
4. With no provider and no live state, use UNKNOWN for production promotion.
   Retain explicit state only in a documented low-level test/gate compatibility
   boundary, if required.
5. Production wrappers should not pass conservation_state at all.

Tests: provider versus explicit GREEN precedence; provider error versus
explicit GREEN; provider UNKNOWN; no-provider/no-explicit UNKNOWN; warning
logging; and no-promotion assertions. Add an AST check forbidding literal
GREEN promotion arguments in application code. Keep direct gate tests that
intentionally supply GREEN.

## 5. Test verification plan

This is the eventual implementation order, not a test run for this
design-only task.

### Level 0 — static inventory

Run AST/rg checks over all five copilot trees. Review every GREEN occurrence as
computed, fixture, display, action, or promotion. Acceptance: no unverified
GREEN in promotion, learning-pause, auto-action, or alert-suppression paths.

### Level 1 — focused tests

Run without increasing the repository's existing timeout policy:

    cd gen-ai-roi-demo-v4-v50/backend
    python -m pytest tests/test_soc_dk_l5.py -q --timeout=120
    cd ../../copilot-sdk
    python -m pytest apps/purchasing/backend/tests/test_purchasing_backend.py apps/purchasing/backend/tests/test_predictive_par.py -q --timeout=120
    python -m pytest tests/evolution/test_prompt_promotion_gate.py tests/test_conservation_gate_coverage.py tests/evolution/test_gate_fail_closed.py -q --timeout=120

Expected: all focused tests pass, including new UNKNOWN/CALIBRATING and
provider-precedence cases; no old test asserts implicit GREEN.

### Level 2 — backend blast radius

Run the full SOC backend suite, Purchasing backend suite, and SDK keyword
selection, then the full SDK suite because prompt_evolver.py is public
package behavior. Run mypy on every changed file before pytest once
implementation begins, as required by CLAUDE.md.

### Level 3 — real integration scenarios

Using real scorer/store paths and no forbidden mocks:

1. provider GREEN plus valid evidence may promote;
2. UNKNOWN, CALIBRATING, AMBER, RED block promotion;
3. malformed/provider exception becomes UNKNOWN and blocks;
4. explicit GREEN with provider AMBER/UNKNOWN still blocks;
5. SOC health exception records UNKNOWN and blocks learning;
6. Purchasing missing state disables auto-order, blocks predictive-par, and
   does not suppress conservation alerting.

### Level 4 — PW regression

Run the 21 identified conservation/GREEN-referencing specs, prioritizing
conservation, checklist, cross-tab, governance/evidence-room, and S2P
preview/provenance specs. PW verifies UI/API contracts; backend tests remain
authoritative for safety branches.

### Level 5 — exit criteria

- zero unclassified fail-open GREEN results;
- B1, B2, and B5 focused tests pass;
- missing/malformed/CALIBRATING/error states return UNKNOWN or actual
  non-GREEN state;
- explicit caller GREEN cannot override a configured provider;
- no promotion, learning-pause, auto-action, or alert-suppression path uses
  an unverified default;
- full regression and import/type checks pass.

## 6. Risk assessment

| Risk | Failure mode | Mitigation |
|---|---|---|
| Calibration is changed to UNKNOWN without separating learning policy | Legitimate calibration learning pauses | Separate learning policy from conservation status; test both. |
| Only named helpers are changed | Adjacent SOC/Purchasing defaults remain fail-open | Repeat static inventory and Level-3 scenarios. |
| Provider precedence breaks low-level tests | Gate fixtures fail | Keep direct gate tests explicit; add production-provider tests separately. |
| Provider exception falls back to explicit GREEN | Safety bypass remains | Provider error must return UNKNOWN and ignore explicit state. |
| Broad replacement changes demos/reports | UI/narrative regressions | Classify each occurrence before changing it. |
| UNKNOWN propagates poorly | 500s or truthiness-based enablement | Normalize typed payloads and add API/UI contracts. |
| SOC safety fix changes action semantics | G1 or outcome accounting regresses | Keep centroid action unchanged; test decision_method and fixed-input action/probability invariance. |

## Review / exit summary

- B1 confirmed: yes — triage.py:373,378,393; adjacent defaults at 2064,2087.
- B2 confirmed: yes — purchasing main.py:574,581.
- B5 confirmed: yes as a capability — prompt_evolver.py:297-306; no current
  non-test literal GREEN caller was found.
- Additional fail-open paths: 4 high-priority adjacent paths and 2 review
  candidates requiring action/display classification.
- Blast radius: 3 direct caller groups, 6 directly identified backend tests
  plus SDK explicit-state suites, and 21 PW spec files with references.
- Fix files: at least 6 files across 3 repos for named and adjacent paths;
  finalize count after classification.
- New tests needed: at least 17 focused cases.
- Estimated effort: 2–3 engineering days for named fixes/tests; 3–5 days if
  all adjacent action/reporting paths and PW contracts require changes.
