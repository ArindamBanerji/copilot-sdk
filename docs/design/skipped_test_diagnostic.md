# Skipped-test diagnostic

Date: 2026-08-12

Scope: diagnostic only. No source or test files were changed. The requested
total of 37 is the number of skip sites/guards in the named groups, not 37
distinct test functions. In the current checkout, the evidence-receipt file
contains one test under two describe-level guards; both guards are listed
because they are separate skip causes.

## Executive summary

The skips fall into five categories:

- Environment gates: live SOC backend, isolated AGE DSN, or an intentionally
  selected fixture/source. These are real preconditions, not code defects.
- Seed/data gates: legacy Trading checkpoints, missing SOC timestamps, or too
  few SOC alerts. These need deterministic seed data or a controlled fixture.
- Safety gates: S2P write tests refuse the shared demo database. This is an
  intentional protection; unskipping requires a disposable S2P target or an
  explicit write opt-in.
- Deferred implementation gates: Protocol v2 service semantics, canonical
  backfills, forward-write proof, and ShadowDecision mapping are not delivered
  by the current code.
- Stale/topology assumptions: several SOC frontend skips target port 8001,
  while the live S2P preview is on 8002; the tensor expectation is also stale
  (`(5, 5, 8)` is live, not `(5, 5, 7)`).

Observed environment evidence:

- `AGE_TEST_DSN` is unset, but the normal `GRAPH_DSN`/copilot AGE DSN is
  configured and reachable. Tests that require an isolated test graph still
  need an explicit test DSN or a documented fallback policy.
- `http://127.0.0.1:8002/api/s2p/preview/config` returned 200 and
  `tensor_shape: "(5, 5, 8)"`.
- The same preview URL on SOC port 8001 returned 404. Thus “S2P is live” does
  not make an SOC frontend test that hardcodes the SOC backend URL live.
- Purchasing commodity indices returned `source: "scraped_external"`, so the
  fixture-only provenance assertion correctly skipped.
- Trading checkpoint history returned checkpoints without a top-level
  `regime_tag`; the Trading skip condition was true.
- A targeted unskipped SOC projection run demonstrated a real data/schema
  problem: a row matched `factor_vector IS NOT NULL`, but projection raised
  `ValueError: Decision.factor_vector must be a non-empty numeric list`.

## Inventory

| # | Repo | Test / skip site | Exact condition or reason | Actually blocked? | Effort | What would unskip it |
|---:|---|---|---|---|---|---|
| 1 | SDK root | `test_api_learn_committed` | Module marker: `Protocol v2 implementation pending` (`tests/graph/test_protocol_v2_service_layer.py:6`) | YES | high | Implement the Protocol v2 service layer and assert canonical commit semantics. |
| 2 | SDK root | `test_api_learn_pending_sync` | Same module marker | YES | high | Implement outbox/pending-sync behavior and its API status. |
| 3 | SDK root | `test_pending_sync_no_V_increment` | Same module marker | YES | high | Implement delayed conservation-V update until replay commit. |
| 4 | SDK root | `test_replay_then_V_increments` | Same module marker | YES | high | Implement replay worker/transaction and then remove the pending marker. |
| 5 | SDK root | `test_concurrent_cross_domain` | `AGE_CROSS_DOMAIN_CONCURRENCY_PENDING` (`tests/graph/test_protocol_v2_conformance.py:23-25,3001`) | YES | high | Deliver cross-domain AGE isolation/concurrency stress coverage and prove cleanup/serialization on a disposable graph. |
| 6 | SDK root | `test_soc_partial_outcome_backfill_does_not_double_count_V` | Explicit: `requires canonical SOC Outcome backfill data; keep skipped until backfill design` (`tests/graph/test_soc_age_projection_contract.py:206`) | YES | high | Complete the canonical SOC Outcome backfill design and seed mixed embedded/canonical outcomes. |
| 7 | SDK root | `test_soc_triggered_evolution_forward_write_required` | Explicit: read-only projection cannot prove forward writes; requires SOC write-path slice (`...test_soc_age_projection_contract.py:315`) | YES | high | Add the SOC forward-write implementation/test slice; a read-only projection cannot satisfy this test. |
| 8 | SDK root | `test_soc_shadow_decision_not_automatically_observation` | Explicit mapping deferred; do not auto-promote (`...test_soc_age_projection_contract.py:334`) | YES | high | Define and implement an approved ShadowDecision→Observation mapping, then replace the guard. |
| 9 | Purchasing BE | `test_live_active_age_score_learn_status_and_read_safety` | Module skip if `not age_available()` (`apps/purchasing/backend/tests/test_purchasing_active_age_live.py:25`); fixture additionally skips if Purchasing AGE DSN is absent (`tests/conftest.py:38`) | YES only without AGE | low/medium | Supply reachable AGE and let the fixture create its disposable `protocol_v2_test_*` graph. SQLite/InMemory cannot satisfy the test’s AGE status, graph-kind, and real score/learn assertions. |
| 10 | SOC BE | `test_both_tabs_have_status` | Collection marker `live_backend`; default requires `--run-live-backend` and port 8001 (`backend/tests/conftest.py:21-25,95-106`) | YES in default run | low | Start SOC on 8001 and run with `--run-live-backend`; TestClient conversion would require rebuilding the live seeded app state. |
| 11 | SOC BE | `test_statuses_match` | Same live-backend gate | YES in default run | low | Same as row 10; requires seeded SOC endpoint state. |
| 12 | SOC BE | `test_tab1_verified_positive` | Same live-backend gate | YES in default run | low | Same as row 10; needs verified SOC decisions. |
| 13 | SOC BE | `test_tab1_le_tab2` | Same live-backend gate | YES in default run | low | Same as row 10; needs coherent seeded Tab 1/Tab 2 totals. |
| 14 | SOC BE | `test_no_unknown` | Same live-backend gate | YES in default run | low | Same as row 10; needs nonempty seeded audit entries. |
| 15 | SOC BE | `test_all_canonical` | Same live-backend gate | YES in default run | low | Same as row 10; needs canonical categories in the live audit trail. |
| 16 | SOC BE | `test_total_gt_50` | Same live-backend gate | YES in default run | low | Same as row 10; seed at least 51 audit entries. |
| 17 | SOC BE | `test_tab3_rationale_not_contradicts_tab1` | Same live-backend gate | YES in default run | low | Same as row 10; needs coherent live narrative data. |
| 18 | SOC BE | `test_evolution_label_not_misleading` | Same live-backend gate | YES in default run | low | Same as row 10; needs live evolution summary and Tab 4 data. |
| 19 | SOC BE | `test_five_articles` | Same live-backend gate | YES in default run | low | Same as row 10; endpoint must expose five governance sections. |
| 20 | SOC BE | `test_evidence_room_sections` | Same live-backend gate | YES in default run | low | Same as row 10; endpoint must be reachable and seeded. |
| 21 | SOC BE | `test_hash_chain_verified` | Same live-backend gate | YES in default run | low | Same as row 10; needs a verified live hash chain. |
| 22 | SOC BE | `test_conservation_verified_positive` | Same live-backend gate | YES in default run | low | Same as row 10; needs positive verified-decision state. |
| 23 | SOC BE | `test_unique_timestamps` | Explicit `SOC-SEED-REDESIGN #9`: seed_graph does not write `Decision.timestamp` to AGE (`backend/tests/test_cross_tab_consistency.py:120-121`) | YES | medium | Write a real timestamp/timestamp_epoch during SOC seed/migration, expose it in the evidence-room projection, and seed at least five distinct values. |
| 24 | Trading PW | `trading checkpoint history exposes regime tags` | If checkpoints exist and none has `regime_tag`, skip (`copilot-sdk/e2e/trading/centroid-regime.spec.ts:12-16`) | YES for current data | low/medium | Run the Trading preseed that writes regime-tagged checkpoints; current live response contains legacy checkpoints without that field. |
| 25 | Purchasing PW | `badge shows sample for fixture data when fixture source is active` | Skip unless commodity API `source` is `sample` or `fixture` (`copilot-sdk/e2e/purchasing/provenance-badge.spec.ts:32-38`) | YES for current source, intentionally | low | Run against an explicitly fixture-backed Purchasing source; do not relabel the observed `scraped_external` source as sample. |
| 26 | SOC PW | `POST /api/s2p/score x10` | Permanently skipped because S2P runs on a separate port (`gen-ai-roi-demo-v4-v50/frontend/tests/e2e/checklist.spec.ts:204-205`) | NO, but topology-gated | low | Point the test at 8002 (or the configured S2P URL) and use the S2P request schema; current body uses the SOC-style scenario fields and posts to `BACKEND` 8001. |
| 27 | SOC PW | `NL explanation changes when a different alert is clicked` | `if (count < 2) test.skip()` (`.../checklist.spec.ts:301-303`) | YES if fewer than two alerts | low | Seed two visible SOC alert cards; the condition is valid, not a stale feature flag. |
| 28 | SOC PW | `D2: audit timestamps are not identical` | `if (entries.length < 2) test.skip()` (`.../cross_tab_consistency.spec.ts:90-96`) | YES if fewer than two entries; otherwise test is active | low | Seed at least two audit entries; distinct timestamp semantics still need the backend seed fix in row 23 for the related backend test. |
| 29 | SOC PW | `S2P preview has (5,5,7) tensor` | Skip if `GET ${API}/api/s2p/preview/config` is non-2xx (`.../cross_tab_consistency.spec.ts:177-180`) | NO for S2P itself; wrong endpoint/topology in SOC run | low | Configure API to 8002 or proxy the route through 8001. After that, update the expected shape: live S2P currently reports `(5, 5, 8)`, so the assertion is stale too. |
| 30 | SOC PW | `test_eval_result_displays_accuracy` | Unconditional `test.skip` (`.../feature01_eval.spec.ts:50`) | YES for a clean run | medium | Upload a valid evaluation file and wait for `/api/soc/eval/demo`/frontend state; replace the unconditional skip with a test that creates its own eval result. |
| 31 | SOC PW | `scored invoice exposes seven numeric contribution rows` — guard 1 | Skip if `S2P_API_URL` is absent (`.../s2p_contribution_chart.spec.ts:3-5,41-42`) | NO, configuration-only | low | Set `S2P_API_URL` to an isolated S2P backend. |
| 32 | SOC PW | Same contribution test — guard 2 | Skip for live `127.0.0.1:8002` unless `ALLOW_LIVE_S2P_CONTRIB_WRITES=1` (`.../s2p_contribution_chart.spec.ts:7-18,43-46`) | YES by design on shared demo | low | Use a disposable isolated S2P URL, or explicitly opt into live writes after accepting persistent test data. |
| 33 | SOC PW | `verified outcome increments conservation once` — guard 1 | Skip if `S2P_API_URL` is absent (`.../s2p_evidence_receipt.spec.ts:3-5,64-65`) | NO, configuration-only | low | Set isolated `S2P_API_URL`. |
| 34 | SOC PW | Same evidence test — guard 2 | Skip for live 8002 unless `ALLOW_LIVE_S2P_EVIDENCE_WRITES=1` (`.../s2p_evidence_receipt.spec.ts:7-15,66-69`) | YES by design on shared demo | low | Use isolated S2P or intentionally opt into writes. The current checkout has one evidence test under these two guards; lines 95/112 mentioned in the task are not skip sites in this checkout. |
| 35 | SOC PW | `supplier lead-time renders contractual and actual Q4 values` | Skip when Supplier Intelligence is not visible (`.../s2p_polish.spec.ts:9-16`) | Conditional; currently likely topology/data dependent | medium | Make the SOC frontend’s S2P preview route reachable and seed supplier data with contractual and actual-Q4 lead-time fields. |
| 36 | SOC PW | `domain applicability panel is visible in Tab 6` | Unconditional `test.skip` (`.../s2p_polish.spec.ts:26`) | YES: feature/test contract is deferred | medium/high | Implement/render the Domain Applicability panel and expected counts/text, then remove the unconditional skip. |
| 37 | SOC PW | `domain applicability remains visible when S2P backend is unavailable` | Unconditional skip; comment requires SOC up and S2P down (`.../s2p_polish.spec.ts:49-51`) | YES for ordinary suite; deliberately fault-injection | medium | Add a controlled test fixture that starts SOC, stops/blocks only S2P, and verifies the fallback panel; do not run it against the normal all-backends-up demo. |

## Group-specific findings

### SDK root

The four service-layer tests are placeholders whose bodies are `pass`; removing
the marker would produce passing-but-vacuous tests, not evidence of a feature.
They should remain blocked until the service contract exists. The AGE
cross-domain test is a real deferred stress test, not an environment mistake.

The three SOC projection skips are intentionally narrower than the generic AGE
availability gates. The live graph is reachable, but the required canonical
data/write semantics are not present. In the targeted run, the factor-vector
test did not skip because a row existed; it failed on malformed stored data.
That is evidence that “property exists” is insufficient as a readiness check.

### Purchasing backend

The live test genuinely needs AGE. It asserts `active_backend=age`, test graph
kind, isolated graph name, score persistence, learn persistence, and duplicate
learn rejection. SQLiteGraphStore or InMemoryGraphStore cannot replace AGE for
this test. The fixture already creates a disposable graph when AGE is
available; the missing piece is environment reachability/configuration, not a
new implementation.

### SOC backend

The 13 live tests use `requests.get("http://127.0.0.1:8001/...")` through
helpers in `test_cross_tab_consistency.py`; they do not use TestClient or direct
calls. They are black-box checks of a running, seeded SOC service. They could
be converted to TestClient, but that would change the test’s purpose and would
still require constructing the app with the same AGE-backed state. The
appropriate unskip is `--run-live-backend` plus a reachable, seeded 8001
process, not silently converting them.

The timestamp test is a genuine seed/schema gap. Adding only a test-side
timestamp would defeat the cross-tab data-integrity purpose; seed/migration
must write and project it.

### Playwright topology and safety

The SOC frontend’s S2P checks are stale or intentionally isolated:

- S2P is a separate service on 8002, while SOC frontend tests use the SOC
  backend base URL on 8001.
- The live S2P preview shape is `(5, 5, 8)`, so `(5, 5, 7)` is a stale contract.
- Contribution and evidence tests write scores/outcomes. Their guards prevent
  accidental mutation of the shared demo backend; an isolated URL is the
  correct prerequisite.
- The Domain Applicability tests are unconditional skips, not availability
  checks. They represent deferred UI/fault-injection coverage.

## Unskip plan and classification totals

Counting the 37 skip sites in the table:

- Low-effort configuration/topology or controlled-run changes: 22. This
  includes live-backend command/configuration, isolated S2P URLs, the
  wrong-port tensor/score checks, and the Trading preseed invocation. These
  still require the stated environment or write-safety controls.
- Medium fixture/seed changes: 6. These are alert counts, audit timestamps,
  Purchasing fixture provenance, supplier lead-time data, and evaluation
  records.
- High protocol/data-model implementation: 9. These are Protocol v2 service
  semantics, AGE concurrency isolation, canonical SOC backfill/forward-write
  semantics, ShadowDecision mapping, and the deferred Domain Applicability
  surface.
- Delete immediately: 0. No row is proven obsolete. The service-layer tests
  are vacuous placeholders and the unconditional UI tests may be stale, but
  they still describe identifiable deferred work; deletion should follow an
  explicit product decision, not be inferred from the skip.

These totals classify skip sites, so the two guards on each S2P write test are
counted separately. They are not counts of unique test functions.

## Queue references and orphan status

Explicit queue references found in code:

- `SOC-SEED-REDESIGN #9` owns the missing Decision timestamp behavior.
- Protocol v2 tests explicitly say “implementation pending”; no completed
  implementation was found in the SDK service-layer test file.
- The projection tests name “backfill design,” “SOC write-path slice,” and
  “ShadowDecision-to-Observation mapping,” but no concrete queue identifier is
  attached to those three items in the inspected test/source context.
- Trading’s skip names the required “Trading preseed”; the preseed path exists
  in the E2E suite, but the current live history confirms it has not produced
  regime-tagged checkpoints.
- S2P write guards document the required isolated URL/environment variables;
  those are operational prerequisites, not orphaned product work.

The canonical backfill, forward-write, ShadowDecision mapping, and Domain
Applicability items have no explicit queue ID in the inspected files. Until a
queue item is assigned, they are orphaned deferred coverage: either assign
implementation work or explicitly retire the tests.

## Verification performed

- Read all named skip conditions and relevant test bodies.
- Ran targeted SDK AGE/projection tests. Result: 108 passed, 3 explicit
  projection skips, and one non-skipped malformed-factor-vector failure.
- Queried live Trading checkpoint history, live Purchasing commodity source,
  SOC port 8001 preview routes, and S2P port 8002 preview routes.
- No source or test files were modified. This document is the only filesystem
  write made by this investigation.
