# Sweep 8 — Monkeypatch, test-double, and production-fixture audit

Date: September 19, 2026.
Method: static source/AST analysis and targeted call-chain inspection. No application imports, test execution, endpoint calls, seeding, or database mutations were performed.
Workspace-relative paths below start at the parent of copilot-sdk.

## Summary

The main risk is not widespread production imports of unittest.mock. It is **different behavior under pytest, fabricated operational evidence, and tests that replace the safety/persistence operations they appear to cover**.

Confirmed findings: **2 P1 and 7 P2**, plus **6 REVIEW items** requiring stronger integration coverage or isolation. One P2 groups occurrences in older repo versions; their current deployment status was not established.

- **S8-01, P1:** S2P graph-backed audit verification returns a hardcoded success. Its pytest-only in-memory branch actually verifies hashes, so the tamper tests exercise different behavior.
- **S8-02, P1:** SOC still mounts a destructive demo reset-all route. It bypasses the confirmation required by the admin reset route and is absent from the shared admin-only mutation-path list.
- **S8-03, P2:** DataOps, S2P, and SOC select configuration/storage behavior by detecting pytest rather than exclusively through explicit application configuration.
- **S8-04–08, P2:** Mounted SOC benchmark/metrics/ServiceNow paths and Trading webhook diagnostics retain fabricated or demo behavior; SOC threat-intelligence refresh can overwrite existing observations with static fallback data.
- **S8-09, P2:** Six older SOC repo trees still serve entirely generated compounding metrics.
- **R1–R6:** Specific test substitutions bypass graph construction, conservation, receipt persistence, AGE escaping, or the deployed router branch.

### Scope and counting

| Scope | Production-path Python files | Test Python files | conftest.py |
|---|---:|---:|---:|
| copilot-sdk shared package and app backends | 524 | 485 | 9 |
| s2p-copilot | 130 | 154 | 1 |
| gen-ai-roi-demo-v4-v50 | 204 | 262 | 2 |
| ci-platform | 37 | 46 | 1 |
| Additional libraries, older repo versions, and workspace source remnants | 269 | 104 | 1 |
| **Total** | **1,164** | **1,051** | **14** |

The four active repos account for 895 production-path files. The additional 269 include compounding-scorer, three graph-attention-engine trees, six older SOC trees, gen_ai_roi_demo_temp/gae, and the root backend/copilot_sdk source remnants. These are not assumed to be mounted by the current applications.

An additional 1,012 auxiliary Python files (scripts, experiments, setup/doc exports) were inventoried and included in import analysis, not treated as deployed application modules. Twelve notebook-export files had Python syntax errors; these are auxiliary files, not application modules. Their failed AST parsing is disclosed in the appendix.

Production-path counts include the two explicitly named copilot_sdk/testing helper modules; they are classified separately below. Dependencies, virtual environments, node_modules, caches, generated graph indexes, and agent working directories were excluded. This is a Python audit; it does not establish absence of fakes in TypeScript, JSON fixture contents, packaged dependencies, or generated template text.

All scoped Python files received automated scanning. Function-level manual tracing was risk-selected; it was not a manual reading of every test. Keyword candidates are not automatically findings.

## P1: Test imports/mocks in production code (file:line list)

**No confirmed runtime import of pytest, unittest.mock, Mock, MagicMock, or AsyncMock was found in the scanned application paths.** There were two import candidates:

| Location | What it is | Verdict |
|---|---|---|
| copilot-sdk/copilot_sdk/testing/fixtures.py:12 | Imports pytest and defines shared test fixtures. Its __init__.py:3 re-exports availability helpers. | Explicit test-support package shipped beside production code, not a demonstrated runtime leak. Scanned application consumers do not import it; tests do. Importing this helper evaluates AGE availability, so keep it outside runtime imports. |
| copilot-sdk/apps/trading/backend/app/brokers/__init__.py:8 | Relative import from .mock of MockBroker. | Not an import of the Python mock package. get_broker defaults to alpaca; mock is an explicitly selected broker adapter. |

Actual custom mock services in production are discussed under S8-06 and the adapter inventory. Their presence is real even though they do not import unittest.mock.

Other false positives: HTTP client.patch calls in ci-platform/ci_platform/connectors/sap.py:444, sentinel.py:80, and SOC connectors/sentinel_real.py:316 are HTTP PATCH, not monkeypatching. The “monkeypatch hooks” text in SOC services/triage_providers.py:5 describes replacing old hooks with dependency providers; it is not an executed patch.

## P1: Testing guards in production code (file:line list)

### S8-01 — P1 — S2P verifies the test ledger but rubber-stamps the production graph

**Locate/read:** s2p-copilot/backend/app/framework/audit.py:62 (_graph_store), :166 (async_record_decision), :251 (async_record_outcome), and :572 (verify_chain); s2p-copilot/backend/app/main.py:486 configures the audit store during startup.

**Trace:** If _GRAPH_STORE is missing, _graph_store returns None only when "pytest" is present in sys.modules (:66); outside pytest it raises. The None branch writes to _LEDGER (:208). The configured branch writes graph decisions/outcomes (:187, :270). In verify_chain, the graph branch returns verified=True and tamper_evidence=[] at :580 without recomputing hashes or checking links. Only the in-memory branch iterates over entries, recomputes compute_hash, and checks prev_hash (:602–627).

**Test evidence:** backend/tests/test_audit.py:13 clears _LEDGER, and tamper tests at :98, :121, and :148 modify that ledger's entries directly. They do not corrupt graph-backed rows and run the same graph verifier. The graph branch is exposed through routers/s2p_audit_export.py:218.

**Why wrong:** Successful tests of the in-memory hash chain cannot substantiate the deployed graph-backed audit's tamper-evidence claim. A graph with edited evidence still receives successful verification if retrieval succeeds. This is a confirmed static contract defect, not an inference from mock density.

**Recommendation:** Use one verifier over persisted canonical entries; fail closed or report verification unsupported when hashes are unavailable. Test tampering through the configured store. Remove the implicit pytest-only alternate implementation; inject an explicit test store.

### S8-03 — P2 — Ambient pytest detection changes application semantics

Listed here because the requested category concerns testing guards; **not all such guards merit P1**.

| Location | Runtime branch | Why it weakens test fidelity |
|---|---|---|
| copilot-sdk/apps/dataops/backend/app/main.py:134 | _resolve_profile returns test when pytest is imported or PYTEST_CURRENT_TEST exists. | _graph_store tolerates GraphConfigError by choosing SQLite at :189; production raises. |
| Same file :143 and :782 | _is_demo_or_test_mode treats pytest as demo mode. | Startup may restore demo bundles and seed decisions/evolution events without DATAOPS_DEMO_MODE. Tests do not exercise the ordinary unseeded production startup. |
| s2p-copilot/backend/app/main.py:168 | Implicit test profile passed into build_s2p_scorer. | Configuration and shared-graph checks differ from production. |
| gen-ai-roi-demo-v4-v50/backend/app/main.py:118 | Health constructs GraphConfig with test profile under PYTEST_CURRENT_TEST. | The health path can inspect a different configuration from deployment. |
| Same repo services/rl_engine.py:629 | Posterior initialization selects test profile. | Tests can validate an alternate persistence setup. |
| Same repo services/posterior_store.py:41, :58, :76, :85 | Implicit test profile and test-only POSTERIOR_DSN override. | Storage endpoint selection depends on the runner environment. |

The shared distinction matters: copilot-sdk/copilot_sdk/config/graph_config.py:43 skips the production shared-graph restriction for non-production profiles or explicit test_mode. An explicit injected test profile is legitimate; merely importing pytest should not silently choose it.

**Verdict:** Confirmed test/production divergence. This is not evidence of a remotely exploitable pytest toggle. Replace runner detection with explicit app-factory configuration and test the production branch separately.

Normal if __name__ == "__main__" guards in CLI, migration, scaffold, graph-schema, and policy modules are entry points, not demonstrated bypasses. Explicit guarded disposable-graph test modes are also not automatically bugs.

## P2: Test-only markers in production code (file:line list)

### S8-04 — P2 — Mounted SOC benchmark fabricates experimental outcomes

**Locate/read:** gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1756, entire benchmarking_level2 function; services/benchmarking_level2.py:17 and :82.

**Trace:** GET /api/soc/benchmarking-level2 is mounted through main.py:175. The handler always supplies literal groups of 382 and 387 decisions, accuracy 0.695 and 0.790, variant_promoted=True, conservation_breached=False, p_value=0.0001, and cohens_d=3.746 (:1765). The section generator turns these into significance and promotion/conservation claims. Its return object has no synthetic/sample provenance flag; gate_2_correctness and gate_4_variance are hardcoded PASS (:90, :92).

**Why wrong:** A mounted API presents invented benchmark evidence independently of stored decisions. A source-code comment saying “mock data” or “not called by frontend” does not qualify the response contract.

**Recommendation:** Disable the unfinished route outside explicit demos or return versioned, unmistakably synthetic content; measured reports must consume experiment artifacts.

### S8-05 — P2 — SOC compounding metrics substitute old synthetic data into a current-week bucket

**Locate/read:** gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:182 (get_compounding_metrics); fallback starts :243, with synthetic Decision query :248 and latest-bucket assignment :265.

**Trace:** The endpoint starts from generate_compounding_data (:62), retaining fixed projected headline/business-impact values. It then queries real rolling time buckets. If all buckets contain zero decisions, it queries all zero_day_synthetic decisions without the time bounds and inserts their count/accuracy into weekly_trend[-1]. historical_fallback=True is provided, but the bucket is still in the requested present-day period and is not individually marked synthetic. The normal serialized response does not separately label its fixed headline as projected.

**Why wrong:** Empty recent activity becomes apparent activity in the newest bucket, with a different origin and time population. This is not equivalent to a historical series. A flag mitigates but does not correct the mis-bucketing. The separate /metrics/compounding/headline route correctly reports source="projected"; do not confuse that improvement with this mixed response.

**Recommendation:** Preserve zero current-week counts, return historical synthetic material separately, and label each metric's origin/time interval.

### S8-06 — P2 — ServiceNow mock is the only implementation behind production-shaped routes

**Locate/read:** SOC services/servicenow_mock.py:28, :36, :68; routers/servicenow_router.py:8, :29, :55; routers/triage.py:2941; main.py:192.

**Trace:** Create/list/get/update endpoints always call get_servicenow_mock. It allocates INC numbers in a process-local dict, makes no network calls, and returns a demo.servicenow.local URL. Correct escalation outcomes also call it directly, with no demo-mode check at that call site. IncidentResponse has no simulation/provenance field.

**Why wrong:** The generic ServiceNow API and automatic escalation path cannot create a real external incident. Restarts lose the records. The fake URL and module name offer clues but are not an explicit transport-mode contract. This is not a claim that a configured real ServiceNow connector was overridden; these routes have no real connector selection at all.

**Recommendation:** Make demo mode explicit and machine-readable; inject a real incident provider or return unavailable outside demo mode.

### S8-07 — P2 — Trading test webhook enters ordinary intake without synthetic provenance

**Locate/read:** copilot-sdk/apps/trading/backend/app/routers/webhook.py:156, :88, :228; mount main.py:689.

**Trace:** POST /api/trading/webhook/test builds a default AAPL/$150.25/2026-05-27 alert and calls tradingview_webhook. The common history receives it like other intake (:132). If auto_score is requested, the real scorer is called and metadata says source="tradingview_webhook" (:243), not test/synthetic. No local demo-mode restriction is present.

**Why wrong:** Diagnostic sample traffic is mixed into operational intake and, when scoring succeeds, into decision evidence under a live-source name. observation_only=True limits execution claims, but does not identify synthetic origin or prevent decision writes.

**Recommendation:** Use an isolated diagnostic adapter or carry test provenance through history and decisions; disable the diagnostic write route outside explicit demos.

### S8-08 — P2 — Static threat-intelligence fallback can replace existing live observations

**Locate/read:** SOC connectors/greynoise.py:192 and connectors/pulsedive.py:261; graph router :171.

**Trace:** Each refresh attempts external calls, then uses HARDCODED_FALLBACK per failed item or for the whole batch when no key/data exists. It updates existing graph nodes keyed by IP/IOC (:256 GreyNoise, :339 Pulsedive), including classification/severity/source and a fresh refreshed_at. There is no demo-mode gate or stale-live-data preservation condition. graph.py:218 additionally attempts to forward stored threat intel into the persistent indicator service.

**Why wrong:** Missing credentials or a provider outage is converted into new static observations rather than unavailability/stale data. Existing values can be overwritten. The entries do retain source="hardcoded_fallback", which is good and means this is **not** an unlabelled-source finding; provenance alone does not isolate fallback writes from the live graph.

**Recommendation:** Preserve last-known live observations and mark staleness; place synthetic fallback in a separate demo namespace and never replace live observations with it.

### S8-09 — P2 — Older repo variants still serve wholly fabricated compounding series

| Repo | Handler | Generator |
|---|---|---|
| gen-ai-roi-demo | backend/app/routers/metrics.py:158 | same file :48 |
| gen-ai-roi-demo-v2 | backend/app/routers/metrics.py:177 | same file :57 |
| gen-ai-roi-demo-v3 | backend/app/routers/metrics.py:177 | same file :57 |
| gen-ai-roi-demo-v3.2 | backend/app/routers/metrics.py:177 | same file :57 |
| gen-ai-roi-demo-v4 | backend/app/routers/metrics.py:191 | same file :71 |
| gen-ai-roi-demo-v4-v45 | backend/app/routers/metrics.py:191 | same file :71 |

These handlers serialize generate_compounding_data directly instead of querying a data store. Their values and apparent evolution-event timestamps are generated independently of observations. This is a grouped finding, not six additional active-production incidents. Deployment status of these older directories is unknown. Quarantine them as historical/demo artifacts and prevent packaging them as current backends.

### Markers reviewed without a confirmed defect

| Location | Disposition |
|---|---|
| copilot-sdk/apps/purchasing/backend/app/routers/spend_router.py:124 | Detects mock/fixture origin and gates sample values; this is a protection, not a mock insertion. |
| copilot-sdk/apps/purchasing/backend/app/data_helpers.py:66 | Temporary file for atomic replacement; “temporary” is not test-only logic. |
| copilot-sdk/copilot_sdk/scaffold/generator.py:237 | Generates a test template intentionally; no runtime pytest import established. |
| copilot-sdk/copilot_sdk/graph/read_diff_runner.py:248 | Statistical sampling, not fabricated metrics. |
| SDK connectors/mock_airflow.py, mock_dbt.py, mock_snowflake.py, mock_weather.py:1 | Explicit demo adapters. Presence is inventoried, not automatically a defect; inspect selection/provenance separately. |
| SOC connectors/crowdstrike_mock.py:90, :230 | Explicitly advertises mock EDR inventory and mock health. Do not call this a hidden unittest.mock import. It still belongs in a segregated demo deployment. |
| compounding-scorer/tests/conftest.py:13 and SDK tests/scoring/conftest.py:13 | MockPreset is deterministic test configuration used with real stores/scorers, not a replacement scorer implementation. |
| ci-platform/ci_platform/graph/age_graph_store.py:3668 | Restricts domain_scoped_reset to pytest_protocol_v2_* domains; a safety guard, not an unrestricted reset-all. |

## P2: Planted fixture references in production routers (file:line list)

These occurrences are real, but no additional confirmed P2 is assigned merely for referencing an explicitly labeled planted scenario.

| Location | Behavior | Audit verdict |
|---|---|---|
| SOC routers/triage.py:526 | Known fixture alert IDs use run_stage1_investigation(..., force_correct=False); other alerts use InvestigationLoop. | Fixture-specific branch in a production router. Tests using only those IDs do not cover ordinary graph investigation. Response mode identifies the shadow path. |
| SOC routers/triage.py:602 | /soc/investigate/oracle uses force_correct=True. | Deliberate positive-control endpoint, not hidden: response explicitly says READ_ONLY, decision_use=forbidden, k_updates=forbidden (:640). Move to an opt-in demo/test router; do not present it as real investigation evidence. |
| SOC services/multihop_scenarios.py:391, :402 | Oracle mode may choose ground-truth action; fixture_source="planted", conservation_emit_gate="not_evaluated_read_only". | Labels are present; cannot substantiate production gate or K-update claims. |
| SOC services/investigation_patterns.py:304 | Planted multi-hop pattern. | Keep test/demo-only contract explicit. |
| SOC services/investigation_loop.py:182 and SDK apps/dataops/backend/app/services/investigation_loop.py:170 | Classify synthetic origins as planted. | Correct provenance handling, not fixture injection. |
| SOC routers/discoveries_router.py:62 | Looks for planted/sample/origin/source/provenance fields. | Provenance extraction, not by itself a hardcoded outcome. |
| s2p-copilot/backend/app/vld_preseed.py:129 | Describes designed K weights as PLANTED FIXTURE. | Explicit fixture narrative. No finding of concealed measurement from this marker alone. |

## P2: Debug/reset endpoints in production (file:line list)

### S8-02 — P1 — SOC demo reset bypasses admin-reset controls and can erase real session evidence

**Locate/read:** SOC routers/metrics.py:358 (reset_all_demo_data), services/state_manager.py:119 and :205, and copilot-sdk/copilot_sdk/auth/dependencies.py:11–12. Mounted by SOC main.py:176.

**Trace:** POST /api/demo/reset-all calls hard_reset(preserve_learning=True) without a confirmation body or demo-mode check. hard_reset deletes session Decision/DecisionContext nodes and resets the audit ledger (:244, :248). The selection predicate in state_manager.py:54 excludes only zero_day_synthetic origin, so “session” does not mean “proven demo fixture”: ordinary decisions with null or any other origin qualify. Preserving learning does not preserve these decisions.

SOC does have global AuthMiddleware. It is therefore **not accurate to call this universally unauthenticated**. However /api/demo/reset-all is absent from ADMIN_PREFIXES and MUTATION_PATHS, whereas /api/admin/reset is protected. With authentication enabled, the shared middleware does not require an admin role for this path; explicit SOC demo mode bypasses authentication generally. The admin route separately requires confirm=true (admin.py:104); the demo route does not.

**Why wrong:** A legacy demo path bypasses the stronger reset contract and preserves synthetic training data preferentially over ordinary decision evidence. It violates the stated no-reset-all policy.

**Recommendation:** Remove/disable the legacy destructive route, or restrict an explicit demo-only reset to positively identified disposable fixture records. Do not use “anything except training” as a safe deletion predicate.

### Other routes inspected

| Route / source | What it does | Verdict |
|---|---|---|
| SOC /api/demo/seed — metrics.py:337 | Returns status=disabled; does not invoke destructive seed. | False positive, already blocked. |
| SOC /api/admin/reset — admin.py:82 | Confirmed soft/hard reset; admin path covered by shared auth. | Privileged destructive operation; distinct from S8-02. |
| SOC /api/eval/simulate-failure — evolution.py:620 | Temporarily modifies scorer, snapshots/restores in finally, returns simulated/provenance labels. | Explicit simulation, not a lasting pause proof. This audit does not establish completeness of every snapshot field. |
| SOC /api/alerts/reset — routers/triage.py:1870 | Legacy reset route candidate. | Retain in reset-surface review; no separate destructive verdict assigned without a full downstream trace. |
| DataOps /api/dataops/trust/reset — apps/dataops/backend/app/routers/trust_perturbation_router.py:115 | Removes reversible per-source overlay; returns simulation=true. | Not bulk graph deletion. |
| Purchasing /api/purchasing/demo/reset — main.py:988 | 404 outside explicit demo mode; resets demo chain/events/outbox. | Guarded demo mutation; shared outbox isolation should remain an integration-test invariant. |
| Trading /api/trading/webhook/test — routers/webhook.py:156 | Routes sample input to common intake. | S8-07. |
| S2P evolution /reset — routers/s2p_evolution.py:82 | Serializes mutation, rejects RED and holds AMBER, resets evolver. | Guarded state mutation, not evidence of an unguarded database wipe. |
| S2P simulation routes — routers/s2p_simulation.py:281, :287 | Advisory simulation endpoints. | Diagnostic names alone do not establish a production bypass. |

Older reset-all candidates also remain at gen-ai-roi-demo/.../metrics.py:231, v2/v3/v3.2 :250, and v4/v4-v45 :264. Base SOC reseeds the database; v45 calls hard_reset and legacy reset_all. These are not assumed reachable from SOC v50. Historical deployments require their own retirement decision.

## REVIEW: Test fakes that don't match production interface (file:line list)

REVIEW means a demonstrated coverage/isolation mismatch, not an assertion that the current full test suite passes or that the substituted implementation is necessarily broken in production. Tests were not run.

### R1 — S2P conftest globally replaces the factories it should sometimes verify

**Locations:** s2p-copilot/backend/tests/conftest.py:71, :80, :87, :99, :183.

The conftest replaces create_s2p_active_graph_store at module import; non-AGE requests receive S2PTestGraphStore rather than the production backend construction. It also replaces build_s2p_scorer and injects a memory store under missing GRAPH_CONFIG_PATH. The autouse fixture directly overwrites app.state scorer/store/reader/reward fields and ends after yield, without restoring prior objects.

**Real contract:** backend/app/main.py:177 constructs the configured scorer/store; backend/app/s2p_graph_status.py owns backend validation. The wrapper preserves explicit AGE calls, so this is not a claim that all AGE tests are mocked.

**Risk:** SQLite construction, persistence and configuration errors can be bypassed by ordinary app tests. Module-import assignments are not automatically undone by pytest.MonkeyPatch. Use explicit injected stores for unit tests and a separate unmodified factory/startup contract test.

### R2 — SOC “full pipeline” replaces conservation and the guarded learning update

**Locations:** SOC backend/tests/test_rl_full_pipeline.py:61, :67, :79, :90–92.

The test replaces LearningHealthMonitor.evaluate with an AsyncMock returning GREEN, acquires a SimpleNamespace scorer whose set_conservation_status is a no-op, replaces guarded_update with a spy returning centroid_update=None, and replaces the chain credit assigner.

**Real contract:** backend/app/services/gae_state.py:984 checks spike/freeze/pause/cap guards and finally calls scorer.update (:1037).

**Risk:** This tests orchestration/eta bookkeeping, not end-to-end gated learning or persisted centroid changes. A broken RED/AMBER guard or scorer update could coexist with this test's assertions. Keep the focused unit test, label it honestly, and add a real-scorer pipeline test. Randomness injection itself is not the problem.

### R3 — S2P “full learn flow” removes mandatory receipt behavior

**Locations:** s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:82–87.

The test uses a real scorer and InMemoryGraphStore subclass, but replaces conservation receipt snapshots with {}, and replaces pre-outcome evidence receipts, outcome receipts, supplier profiles, evolver notifications, and shadow writes with no-ops.

**Real contract:** backend/app/routers/s2p.py:1595 returns a receipt dict after durable append or queued outbox. If both persistence paths fail, it raises HTTP 503 at :1666. The fake instead returns None. The outcome receipt writer at :1459 also has real downstream metadata/persistence responsibilities.

**Risk:** The test can prove L5 state calculations in isolation but cannot prove full learn-flow evidence-before-outcome ordering or fail-closed receipt persistence. Add an unpatched full-flow test with a disposable real store and assert receipt/outcome ordering.

### R4 — AGE fake duplicates the old, incorrect string serializer

**Locations:** ci-platform/tests/test_age_graph_store.py:35–43 and :64; production ci_platform/graph/age_client.py:364–371.

FakeAGEClient._S escapes quotes only, whereas the real helper now escapes backslashes before quotes. Fake run_query merely records queries and consumes queued responses; it does not parse Cypher.

**Risk:** Store tests can accept malformed or differently escaped queries and miss interface changes. This is concrete test-double drift; it is **not** evidence that the repaired production helper is still vulnerable. tests/test_age_escaping.py:63 onward directly exercises real escaping and reduces that specific gap.

**Recommendation:** Reuse the canonical serializer in any narrow transport fake, and verify representative store calls against a disposable AGE graph.

### R5 — SDK backend conftests leave process-global configuration behind

**Locations:** copilot-sdk/apps/trading/backend/conftest.py:11, :24; purchasing/backend/conftest.py:7, :20; dataops/backend/conftest.py:7, :20.

Each creates a delete=False temporary configuration and writes GRAPH_CONFIG_PATH/GRAPH_BACKEND at import time, with no teardown. Nested Trading/Purchasing conftests additionally set PROFILE and SAMPLE_DATA globals at :18.

**Risk:** Collection/import order can determine the active graph configuration when suites share a process, and temporary files accumulate. Separate-process app tests reduce the impact but do not make the fixtures locally scoped. Use controlled session fixtures/subprocess isolation and restore environment/remove temporary configuration.

### R6 — Switching-cost unit fake never exercises the deployed graph-store branch

**Locations:** copilot-sdk/tests/test_switching_cost_router.py:10, :26; production copilot_sdk/backend/switching_cost_router.py:30, :41.

FakeScorer supplies a decisions list and count_decisions(), but the router's fallback actually looks for get_decision_count() then uses len(records). The test client omits domain and graph_store, so the deployed store.get_all_decisions(domain)/count_decisions(domain) path is never exercised by these router tests. The API's explicit fallback makes the tests pass without validating the fake method.

**Risk:** Domain scoping, store-record timestamp shape, and proxy binding can break while this module remains green. The epoch tests cover _timestamp directly, not this integration. Add a FreshScorerProxy plus disposable SQLite/AGE store and the mounted domain argument. Do not claim a current zero-count production bug solely from this gap.

### Positive counterexample

copilot-sdk/tests/test_platform_router.py:69 now uses a real FreshScorerProxy and SQLiteGraphStore, scores and verifies a decision, then calls the router. Its smaller _Scorer fixture also uses get_verified_count and trajectory, matching the current read contract. Do not recycle the earlier stale-method finding as a current defect.

## INFO: Monkeypatch density per test file (ranked table)

Metric: lexical occurrences of monkeypatch, @patch, @mock.patch, MagicMock, or AsyncMock divided by AST-counted test_* functions. This counts repeated fixture names/comments and misses direct assignment patches; it is a triage heuristic, not an operation count or quality score. High means strictly greater than 3.

There are **18 high-density test files**. Including conftests with an artificial denominator of one would add DataOps' fixture module (14 occurrences, zero tests); it is not included in the 18.

| Test file | Tokens | Test functions | Ratio | Flag |
|---|---:|---:|---:|---|
| gen-ai-roi-demo-v4-v50/backend/tests/test_rl_full_pipeline.py | 17 | 1 | 17.00 | HIGH |
| s2p-copilot/backend/tests/test_l5_full_flow_s2p.py | 11 | 1 | 11.00 | HIGH |
| gen-ai-roi-demo-v4-v50/backend/tests/test_ae_integration.py | 67 | 10 | 6.70 | HIGH |
| gen-ai-roi-demo-v4-v50/backend/tests/test_fix_05_06_07.py | 23 | 4 | 5.75 | HIGH |
| gen-ai-roi-demo-v4-v50/backend/tests/test_rl_triage_integration.py | 145 | 29 | 5.00 | HIGH |
| s2p-copilot/backend/tests/test_s2p_preseed_integration.py | 5 | 1 | 5.00 | HIGH |
| copilot-sdk/tests/test_preseed_demo_data.py | 24 | 5 | 4.80 | HIGH |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_learning_live.py | 14 | 3 | 4.67 | HIGH |
| gen-ai-roi-demo-v4-v50/backend/tests/test_l5_learning_store_init.py | 27 | 6 | 4.50 | HIGH |
| gen-ai-roi-demo-v4-v50/backend/tests/test_evidence_room_conservation_fallback.py | 26 | 6 | 4.33 | HIGH |
| gen-ai-roi-demo-v4-v50/backend/tests/test_sentinel_integration.py | 65 | 15 | 4.33 | HIGH |
| copilot-sdk/tests/test_graph_config.py | 64 | 16 | 4.00 | HIGH |
| gen-ai-roi-demo-v4-v50/backend/tests/test_governance_report.py | 24 | 6 | 4.00 | HIGH |
| gen-ai-roi-demo-v4-v50/backend/tests/test_quickfix_sweep.py | 22 | 6 | 3.67 | HIGH |
| gen-ai-roi-demo-v4-v50/backend/tests/test_promotion_gate.py | 187 | 52 | 3.60 | HIGH |
| gen-ai-roi-demo-v4-v50/backend/tests/test_simulation_eventloop.py | 17 | 5 | 3.40 | HIGH |
| s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py | 49 | 16 | 3.06 | HIGH |
| copilot-sdk/tests/test_demo_age_ops.py | 55 | 18 | 3.06 | HIGH |
| copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py | 33 | 11 | 3.00 | MEDIUM |
| copilot-sdk/tests/scripts/test_preseed_all_copilots.py | 3 | 1 | 3.00 | MEDIUM |
| gen-ai-roi-demo-v4-v50/backend/tests/test_rejection_summary.py | 12 | 4 | 3.00 | MEDIUM |
| copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py | 40 | 14 | 2.86 | MEDIUM |
| gen-ai-roi-demo-v4-v50/backend/tests/test_dual_update_fix.py | 29 | 11 | 2.64 | MEDIUM |
| gen-ai-roi-demo-v4-v50/backend/tests/test_metrics_learning_health_failures.py | 21 | 8 | 2.63 | MEDIUM |
| gen-ai-roi-demo-v4-v50/backend/tests/test_balance_sheet.py | 31 | 12 | 2.58 | MEDIUM |
| gen-ai-roi-demo-v4-v50/backend/tests/test_startup_sync.py | 5 | 2 | 2.50 | MEDIUM |
| copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py | 34 | 14 | 2.43 | MEDIUM |
| s2p-copilot/backend/tests/test_learn_conservation_guard.py | 12 | 5 | 2.40 | MEDIUM |
| gen-ai-roi-demo-v4-v50/backend/tests/test_l5_conservation_soc_hook.py | 26 | 11 | 2.36 | MEDIUM |
| copilot-sdk/apps/trading/backend/tests/test_market_refresh.py | 7 | 3 | 2.33 | MEDIUM |

High density is not itself a ranked defect: environment/path isolation and external HTTP stubs may be appropriate. For example, DataOps conftest patches filesystem paths and uses a real SQLiteGraphStore; its high lexical count does not mean it replaces the scorer.

## INFO: Conftest locations and global mutations

No conftest.py was found inside the scanned runtime package/app directories. Backend-root conftests are test collection configuration, not imported runtime code by default.

| Conftest location | Global effects and cleanup |
|---|---|
| ci-platform/tests/conftest.py:15 | AGE reachability probe and disposable UUID graph fixture; finally drops only its graph. No runtime module replacement. |
| compounding-scorer/tests/conftest.py:13 | Small MockPreset with real DecisionStore; store closed in finally. |
| copilot-sdk/tests/conftest.py:1 | Re-exports real shared fixtures. |
| copilot-sdk/tests/graph/conftest.py:34 | Temporarily sets AGE_TEST_GRAPH; restores environment in finally and drops disposable graph. |
| copilot-sdk/tests/scoring/conftest.py:13 | MockPreset data plus real SQLiteGraphStore; not a fake scorer. |
| copilot-sdk/apps/trading/backend/conftest.py:24 | Import-time GRAPH_CONFIG_PATH/BACKEND writes, no restoration; R5. |
| copilot-sdk/apps/purchasing/backend/conftest.py:20 | Same process-global configuration pattern; R5. |
| copilot-sdk/apps/dataops/backend/conftest.py:20 | Same process-global configuration pattern; R5. |
| copilot-sdk/apps/trading/backend/tests/conftest.py:18 | Import-time PROFILE/SAMPLE_DATA and sys.path changes. Scoped live-AGE environment at :51 is restored in finally. |
| copilot-sdk/apps/purchasing/backend/tests/conftest.py:18 | Same import-time profile/sample selection. Scoped live-AGE environment at :50 is restored in finally. |
| copilot-sdk/apps/dataops/backend/tests/conftest.py:18 | sys.path setup; pytest monkeypatch restores environment and data-directory replacements. Seeds a disposable SQLite store. |
| gen-ai-roi-demo-v4-v50/backend/conftest.py | Loads dotenv, changes cwd at import, installs persistent-data and graph-health session guards. Guards can yield when AGE is unavailable; this is not proof that live data was verified. Run this suite in its own process. |
| gen-ai-roi-demo-v4-v50/backend/tests/conftest.py:79 | soc_triage_harness temporarily replaces scorer getter/graph client and SOC_RL_OUTBOX_SQLITE; restores prior values in finally. Explicit live-backend test opt-in exists. |
| s2p-copilot/backend/tests/conftest.py:37 | Environment replacement, fixed temp config filename, direct factory assignments (:80/:99), and app.state replacement (:183). No corresponding restoration for those import-level changes; R1. |

The production code also contains explicit import-cache manipulation unrelated to pytest: copilot-sdk/copilot_sdk/generators/archetype.py:329 tracks and removes newly imported sklearn modules in finally; demo/connector_freeze.py:91 registers a dynamically loaded module. These are not mock imports. Their concurrent-import behavior was not established by this static audit.

## Ranked Findings (P1 → P2 → REVIEW)

| ID | Priority | Finding | Primary location |
|---|---|---|---|
| S8-01 | P1 | Test-only ledger verifies hashes while graph-backed audit returns unconditional success | s2p-copilot/backend/app/framework/audit.py:580 |
| S8-02 | P1 | Mounted demo reset-all bypasses confirmation/admin-only path controls and deletes non-training evidence | gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:358 |
| S8-03 | P2 | Ambient pytest detection selects different startup, persistence and fixture behavior | copilot-sdk/apps/dataops/backend/app/main.py:136 |
| S8-04 | P2 | Fabricated benchmark promotion, conservation, and statistical evidence | gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1765 |
| S8-05 | P2 | Old synthetic decisions substituted into newest rolling-week metric bucket | gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:265 |
| S8-06 | P2 | ServiceNow-shaped routes and escalation hook always use process-local mock | gen-ai-roi-demo-v4-v50/backend/app/routers/servicenow_router.py:57 |
| S8-07 | P2 | Test webhook samples share normal intake and live-source metadata | copilot-sdk/apps/trading/backend/app/routers/webhook.py:156 |
| S8-08 | P2 | Static provider fallbacks overwrite existing graph observations | gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py:339 |
| S8-09 | P2, older trees | Six older SOC variants expose entirely generated compounding metrics | gen-ai-roi-demo/backend/app/routers/metrics.py:158 |
| R1 | REVIEW | S2P factory replacement and un-restored app/global state | s2p-copilot/backend/tests/conftest.py:80 |
| R2 | REVIEW | SOC full-pipeline test replaces health, scorer acquisition and guarded update | gen-ai-roi-demo-v4-v50/backend/tests/test_rl_full_pipeline.py:61 |
| R3 | REVIEW | S2P full-flow test replaces receipt persistence and related side effects | s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:83 |
| R4 | REVIEW | Fake AGE serializer diverges from repaired real serializer | ci-platform/tests/test_age_graph_store.py:35 |
| R5 | REVIEW | SDK app conftests leak process-global configuration and temporary files | copilot-sdk/apps/trading/backend/conftest.py:24 |
| R6 | REVIEW | Switching-cost fake tests omit mounted domain/store integration | copilot-sdk/tests/test_switching_cost_router.py:26 |

P1 total = 2, of which 1 is a test/production implementation split and 1 is a destructive demo route.
P2 total = 7, of which 6 concern synthetic/demo data or endpoints (including older versions) and 1 concerns implicit test-runner configuration.
REVIEW total = 6. Raw candidates and high-density files are not added to finding counts.

## Recommended actions

1. Fix S2P graph-backed verification and add tamper cases through the configured persistent store. A verification endpoint must not report success without verification.
2. Disable SOC's legacy reset-all surface; preserve operational evidence by default and enforce role/confirmation checks on every remaining destructive path.
3. Make startup profiles and demo provider selection explicit. Production functions should not inspect pytest membership or PYTEST_CURRENT_TEST to choose an implementation.
4. Separate synthetic benchmark/metric/connector data from real observations. Label source and time bounds in API responses and persisted records; never refresh live records from static fixture fallback.
5. Keep focused orchestration tests, but stop treating them as full-stack evidence. Add unpatched scorer + gate + receipt + store integration cases using disposable real stores.
6. Remove duplicate fake serializers and ensure every proxy/router test uses the mounted domain/store contract at least once.
7. Scope and restore test environment/state changes; use separate backend test processes where packages share the name app.
8. Introduce a static gate for forbidden runtime test imports and implicit pytest guards, with narrow documented exceptions for copilot_sdk/testing. Do not ban legitimate HTTP PATCH, explicit test-data configuration, or external-service test doubles by substring.
9. Quarantine or retire historical demo backends so static fabricated behavior is not accidentally redeployed.

No remediation was performed in this audit.

## Appendix A — Additional repo coverage

| Tree | Production-path files | Test files | Conftests |
|---|---:|---:|---:|
| backend | 1 | 0 | 0 |
| compounding-scorer | 17 | 7 | 1 |
| copilot_sdk | 1 | 0 | 0 |
| gen-ai-roi-demo | 15 | 0 | 0 |
| gen-ai-roi-demo-v2 | 20 | 2 | 0 |
| gen-ai-roi-demo-v3 | 25 | 2 | 0 |
| gen-ai-roi-demo-v3.2 | 37 | 2 | 0 |
| gen-ai-roi-demo-v4 | 47 | 5 | 0 |
| gen-ai-roi-demo-v4-v45 | 55 | 5 | 0 |
| gen_ai_roi_demo_temp | 3 | 0 | 0 |
| graph-attention-engine | 9 | 10 | 0 |
| graph-attention-engine-v45 | 10 | 11 | 0 |
| graph-attention-engine-v50 | 29 | 57 | 0 |

Tests outside these production trees are included in the test denominator (for example cross-graph-experiments and a nested workspace test). Scanning all repo versions does not mean their running-service status was verified.

## Appendix B — Automated candidate index (not confirmed findings)

This index records files flagged by fake-class/dynamic-fake, patch-operation, or global-mutation patterns. Numbers are source lines. “Global” here is a lexical candidate, including legitimate environment setup. Some matches are comments or intentional test fixtures. The six manually traced REVIEW findings above are the actionable assessment; do not convert this entire index into defects.

| Test/support file | Fake candidates | Patch candidates | Global candidates |
|---|---|---|---|
| ci-platform/tests/test_age_archive.py | 11 | — | — |
| ci-platform/tests/test_age_client.py | 87 | 69, 108, 353, 372, 380, 399, 415, 417, 432, 444, 474, 497 | 107 |
| ci-platform/tests/test_age_graph_store.py | 12, 21 | 64, 486, 951, 1371, 1390, 1661, 1678 | — |
| ci-platform/tests/test_age_graph_store_v.py | — | 142, 220 | — |
| ci-platform/tests/test_age_sdk_adapter.py | 11 | — | — |
| ci-platform/tests/test_celonis_connector.py | — | 312, 331, 351, 373 | 173, 175, 289, 294 |
| ci-platform/tests/test_counter_store.py | 18, 30 | — | — |
| ci-platform/tests/test_dataops_schema.py | 199 | 197, 198, 199, 205 | — |
| ci-platform/tests/test_decision_pipeline.py | 17 | — | — |
| ci-platform/tests/test_graph_backend_switcher.py | — | 44, 66, 96, 117 | — |
| ci-platform/tests/test_sap_connector.py | — | 264, 291, 307, 405, 406, 430, 482, 517, 558, 631 | — |
| ci-platform/tests/test_sentinel.py | — | 105, 129, 157 | — |
| ci-platform/tests/test_splunk.py | — | 77, 96, 117 | — |
| ci-platform/tests/test_two_phase_strategy.py | 8 | — | — |
| compounding-scorer/tests/conftest.py | 13 | — | — |
| copilot-sdk/test_pat.py | — | — | 2 |
| copilot-sdk/_ant_test.py | — | — | 3 |
| copilot-sdk/apps/dataops/backend/conftest.py | — | — | 20, 21, 22 |
| copilot-sdk/apps/dataops/backend/tests/conftest.py | — | 70, 71, 72, 73, 74 | 28 |
| copilot-sdk/apps/dataops/backend/tests/test_bundle_wiring.py | — | — | 46, 55 |
| copilot-sdk/apps/dataops/backend/tests/test_connector_smoke.py | — | 43 | — |
| copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py | — | 202, 203, 204 | — |
| copilot-sdk/apps/dataops/backend/tests/test_dataops_fixture_closure.py | — | — | 25, 29, 31, 36, 38, 173 |
| copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py | 436 | 244 | 52, 53, 54, 393, 394, 399, 400, 401 |
| copilot-sdk/apps/dataops/backend/tests/test_dataops_regime_policy.py | 11 | — | — |
| copilot-sdk/apps/dataops/backend/tests/test_dcel_connectors.py | — | 41, 71, 98, 183, 184, 189, 204 | — |
| copilot-sdk/apps/dataops/backend/tests/test_dq_benchmark.py | 16 | — | — |
| copilot-sdk/apps/dataops/backend/tests/test_enterprise_connectors.py | — | 294, 295 | — |
| copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py | 9 | — | 112, 113, 114, 139, 140, 141, 160, 161, 162, 181, 182, 183 |
| copilot-sdk/apps/dataops/backend/tests/test_multihop_evaluation.py | — | — | 14 |
| copilot-sdk/apps/purchasing/backend/conftest.py | — | — | 20, 21, 22 |
| copilot-sdk/apps/purchasing/backend/tests/conftest.py | — | 90, 93 | 18, 19, 50, 56, 61, 63 |
| copilot-sdk/apps/purchasing/backend/tests/test_cross_discovery.py | 19, 23 | — | — |
| copilot-sdk/apps/purchasing/backend/tests/test_dashboard_projection.py | — | 28 | — |
| copilot-sdk/apps/purchasing/backend/tests/test_inventory_summary.py | — | 50 | — |
| copilot-sdk/apps/purchasing/backend/tests/test_investigation_integration.py | — | 74, 89, 90, 108 | — |
| copilot-sdk/apps/purchasing/backend/tests/test_match_queue.py | 200 | 200 | — |
| copilot-sdk/apps/purchasing/backend/tests/test_multihop_evaluation.py | — | — | 19 |
| copilot-sdk/apps/purchasing/backend/tests/test_purchasing_active_age_live.py | — | — | 86, 87, 88 |
| copilot-sdk/apps/purchasing/backend/tests/test_purchasing_backend.py | — | 404, 405 | 111 |
| copilot-sdk/apps/purchasing/backend/tests/test_purchasing_factors.py | — | 286 | — |
| copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py | 419 | — | 52, 53, 54, 376, 377, 382, 383, 384 |
| copilot-sdk/apps/purchasing/backend/tests/test_purchasing_path_config.py | — | — | 14, 16, 18, 23, 25 |
| copilot-sdk/apps/purchasing/backend/tests/test_purchasing_regime_policy.py | 11 | — | — |
| copilot-sdk/apps/trading/backend/conftest.py | — | — | 24, 25, 26 |
| copilot-sdk/apps/trading/backend/tests/conftest.py | — | 94 | 18, 19, 51, 57, 62, 64 |
| copilot-sdk/apps/trading/backend/tests/test_broker.py | 143, 190, 219, 234, 263 | 146, 147, 204, 223, 248, 286 | — |
| copilot-sdk/apps/trading/backend/tests/test_broker_cli.py | — | 62, 74, 95, 113, 126, 151 | — |
| copilot-sdk/apps/trading/backend/tests/test_broker_router.py | — | 104, 120, 136, 232 | — |
| copilot-sdk/apps/trading/backend/tests/test_cli_complete.py | 85, 101, 393, 426, 464, 497, 530 | 92, 93, 128, 129, 419, 420, 452, 453, 490, 491, 523, 524, 556, 557 | — |
| copilot-sdk/apps/trading/backend/tests/test_correlation.py | 216 | 29, 30, 145, 154, 155, 195, 216, 227, 261 | — |
| copilot-sdk/apps/trading/backend/tests/test_csv_connector.py | — | 285 | 285 |
| copilot-sdk/apps/trading/backend/tests/test_entrant_comparison.py | 8 | — | — |
| copilot-sdk/apps/trading/backend/tests/test_investigation_integration.py | — | 74, 89, 90, 108 | — |
| copilot-sdk/apps/trading/backend/tests/test_journal.py | — | 485 | — |
| copilot-sdk/apps/trading/backend/tests/test_market_refresh.py | — | 41, 56, 57, 73 | — |
| copilot-sdk/apps/trading/backend/tests/test_market_source.py | — | — | 80 |
| copilot-sdk/apps/trading/backend/tests/test_multihop_evaluation.py | — | — | 13 |
| copilot-sdk/apps/trading/backend/tests/test_options_factors.py | 51 | 27, 40, 51, 114, 115, 215, 226, 237 | — |
| copilot-sdk/apps/trading/backend/tests/test_p50_smoke.py | — | 45, 58, 71, 83, 95, 108, 122, 135, 148, 161 | — |
| copilot-sdk/apps/trading/backend/tests/test_prescore.py | 32, 95, 105, 124, 235, 244, 277, 328 | 21, 32, 79, 95, 104, 105, 114, 123, 124, 133, 141, 149, 158, 166, 175, 194, 235, 243, 244, 252, 261, 269, 274, 304, 320, 325 | — |
| copilot-sdk/apps/trading/backend/tests/test_real_providers.py | — | 81 | — |
| copilot-sdk/apps/trading/backend/tests/test_regime.py | 155, 164, 174, 187, 209 | 86, 141, 155, 164, 174, 187, 209, 220, 236, 248, 258 | 55 |
| copilot-sdk/apps/trading/backend/tests/test_regime_beats.py | — | 58 | — |
| copilot-sdk/apps/trading/backend/tests/test_regime_recommender.py | 189 | 167, 177, 178, 188, 189, 199, 210, 220, 232 | — |
| copilot-sdk/apps/trading/backend/tests/test_regime_recommender_p49.py | 110 | 75, 95, 96, 110, 245, 246 | — |
| copilot-sdk/apps/trading/backend/tests/test_signal_confidence.py | — | 122 | 114, 122, 132 |
| copilot-sdk/apps/trading/backend/tests/test_subcategory.py | 193, 207 | 192, 193, 194, 206, 207, 208 | — |
| copilot-sdk/apps/trading/backend/tests/test_trading_active_age_live.py | — | — | 115, 116, 117 |
| copilot-sdk/apps/trading/backend/tests/test_trading_backend.py | — | 208, 236, 237, 238, 252, 277, 289, 348, 349, 521, 522, 600 | 152 |
| copilot-sdk/apps/trading/backend/tests/test_trading_evidence.py | 19, 27 | 169 | — |
| copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py | 503 | — | 56, 57, 58, 223, 461, 462, 467, 468, 469 |
| copilot-sdk/apps/trading/backend/tests/test_trust_analysis.py | 42, 50 | — | — |
| copilot-sdk/apps/trading/backend/tests/test_vix_timing.py | — | 228, 250 | — |
| copilot-sdk/experiments/vld/test_external_baseline.py | — | 84 | — |
| copilot-sdk/tests/test_archetype_generator.py | — | 135 | 135, 224, 230 |
| copilot-sdk/tests/test_bitemporal_scorer.py | 66 | — | — |
| copilot-sdk/tests/test_budget_policy.py | 34 | — | — |
| copilot-sdk/tests/test_bug_fixes.py | 89 | — | — |
| copilot-sdk/tests/test_cached_static.py | — | 181 | — |
| copilot-sdk/tests/test_cc7_app2.py | — | — | 27, 48 |
| copilot-sdk/tests/test_centroid_ablation.py | 116 | — | — |
| copilot-sdk/tests/test_chain_transfer.py | — | 140 | 295, 297 |
| copilot-sdk/tests/test_conservation_contract.py | 62 | — | — |
| copilot-sdk/tests/test_consolidation.py | 57 | — | — |
| copilot-sdk/tests/test_cross_copilot_integration.py | 158, 159, 160 | 155, 156, 157, 158, 159, 160 | 30, 32, 36, 38, 55, 57 |
| copilot-sdk/tests/test_demo_age_ops.py | — | 38, 39, 75, 76, 77, 78, 79, 85, 163, 164, 184, 185, 198, 199, 212, 225, 241, 242, 243, 246, 252, 253, 254, 255, 293, 321, 322, 327, 328, 356, 357 | 113, 114 |
| copilot-sdk/tests/test_demo_truth_preflight.py | — | — | 16 |
| copilot-sdk/tests/test_discipline.py | — | — | 40, 42, 46, 48, 152 |
| copilot-sdk/tests/test_di_claude_parser.py | 30, 43 | — | — |
| copilot-sdk/tests/test_di_combinations.py | 9, 36 | — | — |
| copilot-sdk/tests/test_di_perturbation.py | 11 | — | — |
| copilot-sdk/tests/test_di_profiler.py | 11 | — | — |
| copilot-sdk/tests/test_di_query.py | 15, 24 | — | — |
| copilot-sdk/tests/test_di_router.py | 13, 19 | — | — |
| copilot-sdk/tests/test_entity_enrichment.py | 455 | — | 448, 450 |
| copilot-sdk/tests/test_evolution_telemetry.py | — | — | 103, 105 |
| copilot-sdk/tests/test_evolver_wiring.py | — | — | 19, 21 |
| copilot-sdk/tests/test_factory_dual_write.py | 19 | 23 | — |
| copilot-sdk/tests/test_gate_enforced_scorer.py | 14, 22 | — | — |
| copilot-sdk/tests/test_graph_config.py | — | — | 51, 52, 66, 67, 68, 80, 81, 82, 95, 114, 123, 132, 140, 141, 148, 149, 167, 168, 178, 179, 188, 189, 198, 207, 214, 215, 224 |
| copilot-sdk/tests/test_graph_factory.py | 70 | 75 | 45, 51 |
| copilot-sdk/tests/test_integrator.py | 13 | — | — |
| copilot-sdk/tests/test_investigation.py | 28, 54, 59, 205 | — | — |
| copilot-sdk/tests/test_jm_conformance.py | — | — | 17, 21 |
| copilot-sdk/tests/test_jm_v27_validation.py | — | — | 35, 37, 38, 39, 40, 41, 46, 48 |
| copilot-sdk/tests/test_judgment_conflict.py | — | 246 | — |
| copilot-sdk/tests/test_l5_proof.py | 18, 29, 234, 235, 262, 263 | 222, 234, 235, 236, 262, 263, 264, 286 | — |
| copilot-sdk/tests/test_migration_live_age.py | — | 236, 239 | 29 |
| copilot-sdk/tests/test_migration_resilience.py | — | 141 | — |
| copilot-sdk/tests/test_mutation_lock.py | — | 161 | — |
| copilot-sdk/tests/test_nl_query_extended.py | 23 | — | — |
| copilot-sdk/tests/test_outbox_worker.py | 306 | — | — |
| copilot-sdk/tests/test_phase6_batch_b.py | — | 154, 165 | — |
| copilot-sdk/tests/test_preseed.py | — | 25, 36 | 37, 38, 45, 47, 114, 127, 128, 132, 148 |
| copilot-sdk/tests/test_preseed_demo_data.py | 78, 79, 110, 142, 174, 175 | 76, 77, 78, 79, 80, 107, 108, 109, 110, 111, 139, 140, 141, 142, 143, 172, 173, 174, 175, 176 | — |
| copilot-sdk/tests/test_qualification.py | 55 | — | — |
| copilot-sdk/tests/test_quant.py | — | — | 289 |
| copilot-sdk/tests/test_response_models.py | 43, 54, 64, 72, 80, 88, 96, 122, 194, 205, 217 | — | — |
| copilot-sdk/tests/test_rl_evolution_matrix.py | — | — | 58, 60 |
| copilot-sdk/tests/test_rl_framework.py | 126 | 126, 127 | — |
| copilot-sdk/tests/test_s2p_preset.py | — | — | 15, 16 |
| copilot-sdk/tests/test_scratch_graph.py | 15, 27 | 69, 70, 105, 200 | — |
| copilot-sdk/tests/test_shadow_scorer.py | 28, 44 | 24 | — |
| copilot-sdk/tests/test_situation_analyzer.py | 28, 44, 525 | — | — |
| copilot-sdk/tests/test_soc_graph_invariant.py | — | — | 15, 17, 18, 19, 20, 25, 27 |
| copilot-sdk/tests/test_soc_preset.py | 70 | — | — |
| copilot-sdk/tests/test_sqlite_to_age_migration.py | 159, 167, 346, 379, 470, 478, 508, 512, 516, 520, 524, 558, 616, 620, 624, 628, 659, 663, 667, 671, 675, 702, 706, 710, 714, 718, 759 | 320, 343, 344, 358, 367, 376, 377, 381, 389, 410, 441, 453, 467, 468, 472, 476, 480, 497, 498, 502, 506, 510, 514, 518, 522, 526, 550, 551, 555, 556, 560, 564, 568, 583, 584, 588, 589, 593, 608, 609, 613, 614, 618, 622, 626, 630, 634, 651, 652, 656, 657, 661, 665, 669, 673, 677, 694, 695, 699, 700, 704, 708, 712, 716, 720, 756, 783, 931, 1187, 1199, 1223, 1224, 1245, 1257 | — |
| copilot-sdk/tests/test_store_parity.py | — | — | 28, 30 |
| copilot-sdk/tests/test_substantiation_e2e.py | — | — | 19 |
| copilot-sdk/tests/test_supplier_signal.py | — | — | 21, 23, 27, 29 |
| copilot-sdk/tests/test_switching_cost_router.py | 10 | — | — |
| copilot-sdk/tests/test_tab_state_cache.py | — | 276 | — |
| copilot-sdk/tests/test_trading_evolver_wiring.py | — | — | 24, 26 |
| copilot-sdk/tests/test_transfer.py | 162 | — | — |
| copilot-sdk/tests/test_transfer_router.py | 7, 15 | — | — |
| copilot-sdk/tests/test_verify_state.py | 22, 495, 496, 526, 527, 528, 529 | 347, 348, 349, 353, 365, 366, 480, 481, 494, 495, 496, 497, 523, 524, 525, 526, 527, 528, 529, 535 | — |
| copilot-sdk/tests/test_warm_start_demo.py | — | 53 | — |
| copilot-sdk/tests/vld_validation_report.py | — | — | 407, 408, 415, 417, 427 |
| copilot-sdk/tests/backend/test_conservation_router.py | — | — | 211, 212, 213 |
| copilot-sdk/tests/backend/test_cors.py | — | — | 32 |
| copilot-sdk/tests/backend/test_evolution_router.py | — | — | 157, 158, 159 |
| copilot-sdk/tests/backend/test_evolution_router_extended.py | 9 | — | — |
| copilot-sdk/tests/backend/test_l5_full_flow.py | 95 | — | — |
| copilot-sdk/tests/backend/test_scorer_proxy.py | 42 | 33, 168, 193, 226, 246 | — |
| copilot-sdk/tests/backend/test_scoring_router.py | 25, 36, 48, 56, 64, 72, 80, 141 | — | 1724, 1725, 1726 |
| copilot-sdk/tests/discovery/test_demo.py | — | 14 | — |
| copilot-sdk/tests/discovery/test_engine.py | 14 | — | — |
| copilot-sdk/tests/discovery/test_patterns.py | 14 | — | — |
| copilot-sdk/tests/discovery/test_router.py | 11 | — | — |
| copilot-sdk/tests/evolution/test_evolve_integration.py | 68, 78 | — | — |
| copilot-sdk/tests/graph/conftest.py | — | — | 34, 39, 43, 45 |
| copilot-sdk/tests/graph/test_age_pool_stress.py | — | — | 26, 49 |
| copilot-sdk/tests/graph/test_contract_cross.py | — | — | 66, 73 |
| copilot-sdk/tests/graph/test_graphstore_factory.py | 241 | 220 | 252, 253, 254 |
| copilot-sdk/tests/graph/test_protocol_v2_conformance.py | — | 3155 | 3568 |
| copilot-sdk/tests/graph/test_soc_age_projection_contract.py | — | — | 51, 55, 61, 63, 64 |
| copilot-sdk/tests/rl/test_exploration.py | 10, 23, 31 | 10, 11, 23, 31, 80 | — |
| copilot-sdk/tests/rl/test_rl_wiring.py | — | 135, 186, 213 | — |
| copilot-sdk/tests/scoring/conftest.py | 13 | — | — |
| copilot-sdk/tests/scoring/test_checkpoint_legacy.py | — | — | 18, 19, 24, 26 |
| copilot-sdk/tests/scoring/test_dk_persistence.py | 154, 169 | — | — |
| copilot-sdk/tests/scoring/test_dk_runtime_learning.py | 24 | — | — |
| copilot-sdk/tests/scoring/test_j6_persistence.py | — | — | 26, 27, 32, 34 |
| copilot-sdk/tests/scoring/test_scorer.py | 540 | 540, 567, 572, 614, 684, 706, 707, 722, 723, 724, 725, 726, 727, 728, 822, 938, 939, 1005 | — |
| copilot-sdk/tests/scoring/test_weather_cache.py | — | 40 | — |
| copilot-sdk/tests/scripts/test_c9_live_age_smoke.py | 221 | 312 | 20 |
| copilot-sdk/tests/scripts/test_preseed_all_copilots.py | 12 | 46, 47 | — |
| copilot-sdk/tests/transfer/test_transfer_demo.py | — | 18 | — |
| gen-ai-roi-demo-v4/backend/tests/test_gae_persistence.py | — | 63, 64, 91, 133, 153, 154, 162 | — |
| gen-ai-roi-demo-v4-v45/backend/tests/test_gae_persistence.py | — | 63, 64, 91, 133, 153, 154, 162 | — |
| gen-ai-roi-demo-v4-v50/test_age_precheck.py | — | — | 15 |
| gen-ai-roi-demo-v4-v50/backend/tests/conftest.py | — | — | 46, 79, 80, 90, 92 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_accuracy_trajectory.py | — | 34 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_ae_integration.py | 147, 414 | 47, 75, 117, 122, 127, 128, 146, 147, 148, 149, 155, 163, 179, 208, 239, 240, 253, 286, 301, 326, 346, 347, 354, 402, 403, 414, 415, 420, 430 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_ae_sd_rl_seed.py | — | 99, 100 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_ae_seed_enrichment.py | 117, 143 | 126, 127, 185, 186 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_analyst_eta.py | — | 140 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_audit_chain_wiring.py | — | 203, 205 | 136 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_audit_chain_wiring_extended.py | — | 149, 305 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_audit_seed_timestamps.py | 12 | — | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_auth_health.py | — | — | 20, 26 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_balance_sheet.py | 256 | 62, 93, 94, 99, 100, 101, 102, 236, 255, 256, 270, 271, 272, 273 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_benchmarking_report.py | 4 | — | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_bootstrap_centroids.py | 69 | 86, 87, 103, 114 | 27 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_campaign_matcher.py | 94, 157, 169, 210 | — | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_campaign_measurement_instrumentation.py | 6 | — | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_campaign_seed_materialization.py | 58, 193 | — | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_campaign_timeline.py | 67 | 108 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_campaign_v6_context.py | — | 206, 224, 246, 273, 299, 344 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_campaign_vld_topology.py | 39 | — | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_category_freeze.py | — | 175 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_centroid_export.py | — | 157 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_centroid_pitr.py | 12 | 50, 75, 93, 94 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_cluster_history.py | 13 | — | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_cold_start_guards.py | — | 41, 42, 62, 63, 68, 73, 88, 99, 113, 124, 139, 153, 182, 186 | 23 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_composite_gate.py | 48, 72, 300 | 225, 274, 275, 276 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_conservation_bugs.py | — | 34 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_conservation_extended.py | — | 68, 79, 90, 106, 265, 325 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_conservation_formula.py | — | 105, 106, 122, 123, 138, 139 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_credit_assigner.py | 13 | — | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_cross_graph_discovery.py | 539 | — | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_cross_signals.py | — | 69 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_d06_unmapped.py | 60, 92, 113, 117 | 70, 71, 72, 141, 142, 143 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_decision_distance_log.py | — | 93, 94 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_discoveries_router.py | 14 | 58 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_domain_table.py | — | 147 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_dual_update_fix.py | 142, 146, 156 | 139, 140, 141, 142, 143, 144, 145, 146, 147, 151, 152, 153, 154, 155, 156, 157 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_econ1.py | — | 65, 97, 131, 157, 183, 207 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_eta_contract.py | — | 163, 194 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_eval_upload.py | 343 | 153, 154, 187, 188, 217, 218, 285, 286, 302, 303, 331, 332, 343, 355, 356, 489, 490, 511, 512, 528, 529, 546, 547, 570, 571, 588, 589, 609, 610, 629, 630, 650, 651, 664, 665, 686, 687, 709, 710, 731, 732, 746, 747 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_evidence_room_conservation_fallback.py | — | 24, 33, 41, 54, 62, 73, 81, 93, 101, 113, 121, 133, 148 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_evolution_ledger.py | — | 600, 613, 626, 642, 654, 674, 687, 698 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py | — | 184, 208 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_executive_narrative.py | 9, 285, 312 | 144, 145, 146, 352, 353, 354 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_exploration_policy.py | 84, 94, 101, 131, 139, 178, 221 | 84, 85, 94, 101, 131, 139, 178, 188, 199, 208, 221, 229 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_f2_design.py | — | 46, 47, 77, 78, 105, 106, 133, 134, 164, 165, 201, 202 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_f4_overlay.py | — | 54, 81, 108, 134, 157 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_factor_analysis.py | 93 | 45, 46, 93, 102 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_factor_contribution.py | 69, 80, 91, 102, 114, 125, 139 | 67, 78, 89, 100, 112, 123, 137, 154 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_factor_provenance.py | 11 | — | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_factor_provider_protocol.py | 12 | — | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_factor_validation.py | — | 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_fix_05_06_07.py | — | 102, 103, 104, 105, 106, 108, 110, 111, 163, 164, 188 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_fw10_learning_display.py | — | 32, 33, 37, 45, 57, 65, 77, 88 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_g1_boundary.py | — | 34, 53 | 12 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_gae_persistence.py | — | 63, 64, 133, 151, 152, 163 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_governance_report.py | — | 148, 149, 150, 151, 152, 153, 154, 155, 232 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_graph_backend_switcher.py | — | — | 14, 15, 19, 22, 24, 31, 32, 33, 37, 43, 45, 47 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_graph_explorer.py | — | 119, 150, 172, 206 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_h7_fix2.py | — | 34, 54, 73, 89 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_h7_fix3.py | — | 75, 78, 98, 127 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_h7_fix4.py | — | 60, 89, 115 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_iks_consistency.py | — | 87, 88, 89, 103, 104, 118, 119, 120, 131, 132, 133 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_iks_stability.py | — | 50, 72, 148, 177, 202 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_iks_v2.py | 40 | 149, 186 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_ingest_endpoint.py | — | 37, 78, 105, 184 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_j6_state_capture.py | — | — | 18, 19, 24, 26 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_kill_chain.py | 36 | 42 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_l5_conservation_soc_hook.py | 88, 197, 231 | 82, 88, 101, 132, 144, 156, 167, 179, 195, 197, 199, 220, 221, 231, 235 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_l5_learning_store_init.py | 21, 30, 39, 76, 108, 135 | 18, 54, 64, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 115, 143, 160 | 59, 60, 61, 113, 140, 141, 158 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_learning_health.py | — | 92, 112, 113, 136, 137, 155, 170, 199, 218, 245, 246, 269 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_learning_toggle.py | — | 46, 76, 121, 163, 166 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_lifespan.py | — | 28, 29 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_metrics_learning_health_failures.py | — | 10, 25, 40, 55 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_model_swap.py | 95 | 95 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_nl_templates.py | 224, 282 | — | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_outcome_route_idempotency.py | — | 29, 50 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_p77_migration.py | 332 | 27, 92, 121, 122, 134, 135, 148, 149, 159, 160, 171, 172, 183, 184, 305, 306, 307, 308, 309, 310, 312, 322, 327, 332 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_pii_middleware.py | — | 145 | 52, 56, 63, 119, 131, 144, 156, 167, 176 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_policy_alert_type.py | — | 47, 48, 82, 83 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_posterior_health.py | 48 | 21, 33, 48, 62, 74 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_posterior_store.py | — | — | 95, 96 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_promotion_gate.py | 79, 113, 127, 142, 169, 197, 329, 337, 373, 387, 474, 553, 597, 617, 624, 646, 653, 686, 710, 722, 829, 830, 831 | 78, 79, 89, 90, 100, 101, 111, 112, 113, 125, 126, 127, 128, 129, 140, 141, 142, 143, 148, 167, 168, 169, 170, 175, 195, 196, 197, 198, 203, 229, 249, 250, 251, 263, 264, 265, 289, 290, 291, 303, 304, 305, 318, 319, 320, 329, 337, 346, 348, 364, 365, 373, 387, 397, 408, 421, 439, 456, 467, 474, 484, 485, 486, 498, 499, 500, 518, 519, 531, 532, 553, 559, 570, 571, 572, 586, 587, 588, 606, 636, 637, 671, 672, 679, 699, 700, 710, 716, 731, 761, 762, 763, 783, 784, 785, 804, 805, 806, 829, 830, 831, 832 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_provenance.py | — | 113 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_quickfix_sweep.py | — | 59, 60, 61, 62, 63, 64, 85, 86, 87, 88, 89, 90, 109, 110, 111, 123, 124, 125 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_rejection_summary.py | — | 19, 20, 32, 33, 49, 50, 65, 66 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_reward_ledger.py | — | 62, 72, 105, 109 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_rl_api.py | — | 94, 95, 96, 97 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_rl_display.py | — | 89, 90 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_rl_feature_flags.py | 79, 96, 120 | 56, 83, 84, 93, 94, 130, 131, 132, 142, 143, 144, 145 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_rl_full_pipeline.py | 65, 71 | 32, 33, 34, 35, 40, 41, 61, 65, 90, 91, 92 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_rl_triage_integration.py | 17, 84, 166, 172, 178, 419, 455, 518, 538, 543, 547, 551 | 145, 163, 164, 166, 167, 168, 177, 178, 204, 283, 302, 304, 323, 325, 335, 343, 358, 366, 377, 379, 393, 399, 409, 420, 427, 428, 445, 446, 447, 457, 466, 467, 491, 492, 493, 498, 499, 500, 504, 517, 518, 519, 537, 538, 563, 567, 571, 575, 688, 691, 692, 705, 716, 717, 820, 823, 824, 830, 860, 863, 864, 870, 899, 902, 903, 925, 931 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_saml_auth.py | — | — | 94 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_saml_auth_extended.py | — | — | 147, 148, 154, 155, 280 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_scorer_adapter.py | 232 | 22, 201, 202, 203, 204, 205, 206, 208, 218, 223, 232 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_seed_graph_gate.py | 13 | — | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_seed_verified_decisions.py | 85 | — | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_sentinel_integration.py | 107, 212 | 55, 67, 71, 86, 90, 103, 107, 144, 186, 191, 196, 197, 211, 212, 213, 214, 220, 253, 257, 297, 306, 307, 353, 388, 418 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_servicenow_triage_integration.py | — | 73, 74, 75, 76, 77, 78, 80, 81, 82 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_shadow_checkpoint.py | — | 51, 71, 111, 112, 152, 153, 174, 175, 195, 236, 237, 268 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_shadow_runner.py | 161, 194, 554, 570 | 91, 107, 131, 147, 159, 173, 192, 380, 381, 396, 401, 423, 424, 445, 459, 460, 495, 496, 534, 535, 553, 554, 569, 570, 595, 596, 600, 601, 619, 620, 642, 643 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_simulate_failure.py | — | 46 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_simulate_failure_state.py | — | 48 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_simulation_eventloop.py | 75 | 19, 20, 110, 111, 112, 117 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_c9b_l5_proof.py | 200, 206, 212, 274 | 198, 199, 200, 201, 202, 211, 212, 213, 214, 215, 216, 217, 232, 236, 237, 273, 274, 431, 473 | 30, 44, 472 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_c9b_seed_contract.py | 59, 90 | — | 17 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_conservation_132.py | 256, 305, 322 | 255, 256, 275, 276, 292, 293, 304, 305, 321, 322 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_conservation_fixes.py | — | 42, 53, 72, 73, 74, 105 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_contract_fixes.py | — | 46, 57, 72, 88, 89, 98, 102, 112, 122, 132, 141, 153 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_dk_l5.py | 425, 431, 437, 445 | 40, 230, 256, 276, 296, 316, 423, 424, 425, 426, 427, 436, 437, 438, 442, 443, 444, 445, 458, 459, 460 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_domain_profile_pipeline.py | — | 192, 234, 293, 340 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_entity_cache_route_readiness.py | — | 113, 141, 176, 198, 223, 245 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_evidence.py | 14, 37 | 191 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_grate.py | — | 74, 79 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_learning_live.py | — | 21, 38 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_route_validation_runner.py | 329, 423, 426, 482, 485, 599, 637, 653, 667, 899, 987, 1003, 1015 | 311, 312, 329, 426, 427, 428, 429, 438, 439, 440, 445, 485, 486, 487, 488, 493, 505, 506, 530, 531, 532, 555, 556, 557, 578, 579, 580, 597, 598, 599, 600, 640, 641, 642, 643, 652, 653, 654, 666, 667, 702, 703, 749, 750, 919, 920, 925, 926, 935, 941, 1003, 1004, 1005, 1006, 1015, 1021, 1260, 1261 | 19, 445, 493, 919, 935 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_situation_pattern.py | 20 | — | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_spike_detector.py | — | 59, 87, 109, 164 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_state_locking.py | — | 49, 56, 66, 77, 124, 135 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_switching_cost.py | — | 160, 168 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_tab_content.py | — | 31, 46, 56, 100, 169, 173, 218, 222, 269, 270, 308, 359, 417, 421, 439, 443, 478, 482, 523, 527, 562, 595, 599, 631, 647, 673, 708, 712, 755, 774, 811, 815, 845, 878, 882, 913, 917, 949, 953, 986, 987, 1387, 1426, 1427, 1428, 1429 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_threat_indicator.py | — | 174, 202 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_threat_intel_cascade.py | — | 101 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_threat_intel_provider.py | 42, 66 | 202 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_time_machine.py | — | 42, 53, 54, 55, 63, 64, 75 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_triage_c2_compliance.py | — | — | 60, 61, 89, 91 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_triage_routing_actions.py | — | 67, 68, 69, 70, 71, 72, 74, 75, 76, 133, 136, 139, 142 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_triggered_evolution.py | — | 63, 64, 65, 66, 67, 68, 70, 71 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_variant_generator.py | — | 70, 82, 182, 241, 263, 276, 286, 338, 363, 375, 389, 417, 433, 620, 740, 749, 799, 991 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_verification_health.py | — | 51 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_whatif_simulator.py | — | 243 | — |
| gen-ai-roi-demo-v4-v50/backend/tests/test_zero_day_timestamp_spread.py | 114, 137 | — | 16 |
| gen-ai-roi-demo-v4-v50/scratch/temp/runner_debug_20260610_154609/backend/tests/test_soc_route_validation_runner.py | 329, 423, 426, 482, 485 | 311, 312, 329, 426, 427, 428, 429, 438, 439, 440, 445, 485, 486, 487, 488, 493, 510, 511, 547, 548, 589, 590, 785, 786 | 19, 445, 493 |
| graph-attention-engine-v50/tests/test_api_contract.py | 436 | — | — |
| graph-attention-engine-v50/tests/test_referral.py | 24 | — | — |
| s2p-copilot/backend/tests/conftest.py | — | — | 37, 38, 39, 40, 41, 43, 62, 94, 113 |
| s2p-copilot/backend/tests/test_centroid_explorer.py | 33, 62, 75 | — | — |
| s2p-copilot/backend/tests/test_centroid_import.py | — | 103, 124, 136, 145, 179, 192, 197 | — |
| s2p-copilot/backend/tests/test_compounding_ledger.py | — | 414, 434, 469 | — |
| s2p-copilot/backend/tests/test_cors.py | — | — | 30 |
| s2p-copilot/backend/tests/test_cross_copilot_signals.py | — | 43, 55, 67, 79, 85, 94, 103 | — |
| s2p-copilot/backend/tests/test_domain_isolation.py | — | — | 32, 41, 43 |
| s2p-copilot/backend/tests/test_e2_e3_validation.py | 15, 32 | — | 70 |
| s2p-copilot/backend/tests/test_evidence_receipt_wiring.py | — | 111, 112, 159, 160, 196, 197, 198, 313, 314, 348, 349 | — |
| s2p-copilot/backend/tests/test_evolver_conservation.py | — | 86 | — |
| s2p-copilot/backend/tests/test_factors.py | — | 179 | — |
| s2p-copilot/backend/tests/test_factor_proposer.py | — | 124 | — |
| s2p-copilot/backend/tests/test_financial_router.py | 28, 62 | 80, 298 | — |
| s2p-copilot/backend/tests/test_graphstore_consolidation.py | — | 127, 145 | — |
| s2p-copilot/backend/tests/test_graph_contract.py | 185 | — | — |
| s2p-copilot/backend/tests/test_graph_links.py | — | 126, 141 | — |
| s2p-copilot/backend/tests/test_intervention_controls.py | 12, 21, 32 | — | — |
| s2p-copilot/backend/tests/test_jm_rl_verification.py | — | — | 270, 279 |
| s2p-copilot/backend/tests/test_l5_conservation_s2p_hook.py | 16 | — | — |
| s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py | 40, 72, 90, 156, 160, 163, 164, 165, 166 | 139, 149, 150, 155, 156, 157, 163, 164, 165, 166, 179 | — |
| s2p-copilot/backend/tests/test_l5_full_flow_s2p.py | 82, 83, 84, 85, 86, 87 | 78, 79, 80, 81, 82, 83, 84, 85, 86, 87 | — |
| s2p-copilot/backend/tests/test_lead_time.py | — | 345, 346 | — |
| s2p-copilot/backend/tests/test_learn_conservation_guard.py | — | 71, 82, 95, 109, 114, 131, 136 | — |
| s2p-copilot/backend/tests/test_novelty.py | — | 300 | — |
| s2p-copilot/backend/tests/test_optimizer_service.py | 137 | — | — |
| s2p-copilot/backend/tests/test_outcome_receipt.py | — | 398, 399, 413, 467, 490, 522, 523, 538, 539, 559, 578 | — |
| s2p-copilot/backend/tests/test_preview.py | — | 40 | — |
| s2p-copilot/backend/tests/test_s2p_active_age_phase_b.py | 39 | — | — |
| s2p-copilot/backend/tests/test_s2p_audit_export.py | 176 | — | — |
| s2p-copilot/backend/tests/test_s2p_auto_approve.py | — | 171, 172, 184, 185, 195, 196, 206, 207, 218, 219 | — |
| s2p-copilot/backend/tests/test_s2p_auto_approve_gate.py | 33 | 85, 90, 275, 293, 310 | — |
| s2p-copilot/backend/tests/test_s2p_conservation_coverage.py | — | 100 | — |
| s2p-copilot/backend/tests/test_s2p_context_builder.py | 13, 23 | — | — |
| s2p-copilot/backend/tests/test_s2p_contract_fixes.py | — | 28, 34, 60, 61, 95, 102 | — |
| s2p-copilot/backend/tests/test_s2p_control_tower.py | — | 155 | — |
| s2p-copilot/backend/tests/test_s2p_data_helpers.py | — | 41, 47 | — |
| s2p-copilot/backend/tests/test_s2p_enrichment.py | — | 471, 490, 504, 514, 526, 539, 550 | — |
| s2p-copilot/backend/tests/test_s2p_entity_migration.py | — | — | 236 |
| s2p-copilot/backend/tests/test_s2p_evolution_shadow_runner.py | 50, 67, 100 | — | — |
| s2p-copilot/backend/tests/test_s2p_iks.py | — | 119 | — |
| s2p-copilot/backend/tests/test_s2p_insight.py | 116, 117 | 116, 117 | — |
| s2p-copilot/backend/tests/test_s2p_performance.py | 22 | 310 | — |
| s2p-copilot/backend/tests/test_s2p_preseed_integration.py | 37 | 35, 36, 37, 38 | — |
| s2p-copilot/backend/tests/test_s2p_preview.py | 442 | 303, 336, 376 | — |
| s2p-copilot/backend/tests/test_s2p_pvg.py | — | 60 | — |
| s2p-copilot/backend/tests/test_s2p_score_endpoint.py | 159, 160, 162, 163, 165, 166, 1134 | 157, 158, 159, 160, 161, 162, 163, 165, 166, 177, 198, 239, 263, 280, 281, 307, 340, 373, 501, 502, 533, 534, 557, 558, 582, 583, 596, 620, 649, 664, 709, 738, 767, 802, 929, 954, 1019, 1052, 1075, 1105, 1106, 1133, 1134, 1169 | — |
| s2p-copilot/backend/tests/test_s2p_shadow_live_age.py | — | — | 35, 37, 42, 44 |
| s2p-copilot/backend/tests/test_s2p_shadow_phase1.py | — | — | 48, 61, 62 |
| s2p-copilot/backend/tests/test_s2p_shadow_phase2.py | 37 | — | — |
| s2p-copilot/backend/tests/test_s2p_situation_pattern.py | 10, 108 | — | — |
| s2p-copilot/backend/tests/test_s2p_supplier_cutoff.py | 6 | — | — |
| s2p-copilot/backend/tests/test_seed_quarantine.py | — | — | 12, 18 |
| s2p-copilot/backend/tests/test_supplier_intel.py | 42, 57 | — | — |
| s2p-copilot/backend/tests/test_supplier_intelligence.py | 24 | — | — |
| s2p-copilot/backend/tests/test_supplier_intel_cascade.py | 121 | 136 | — |

## Appendix C — Parse limitations and verification

Twelve auxiliary notebook exports could not be parsed as ordinary Python. None is in the primary runtime trees:

- gen-ai-roi-demo/support/setup/setup_notebook_v4.py: invalid syntax (gen-ai-roi-demo/support/setup/setup_notebook_v4.py, line 51)
- gen-ai-roi-demo-v2/support/setup/setup_notebook_v4.py: invalid syntax (gen-ai-roi-demo-v2/support/setup/setup_notebook_v4.py, line 51)
- gen-ai-roi-demo-v3/support/setup/setup_notebook_v4.py: invalid syntax (gen-ai-roi-demo-v3/support/setup/setup_notebook_v4.py, line 51)
- gen-ai-roi-demo-v3.2/support/setup/setup_notebook_v4.py: invalid syntax (gen-ai-roi-demo-v3.2/support/setup/setup_notebook_v4.py, line 51)
- gen-ai-roi-demo-v4/support/setup/setup_notebook_v4.py: invalid syntax (gen-ai-roi-demo-v4/support/setup/setup_notebook_v4.py, line 51)
- gen-ai-roi-demo-v4-v45/support/setup/setup_notebook_v4.py: invalid syntax (gen-ai-roi-demo-v4-v45/support/setup/setup_notebook_v4.py, line 51)
- gen-ai-roi-demo-v4-v50/support/setup/setup_notebook_v4.py: invalid syntax (gen-ai-roi-demo-v4-v50/support/setup/setup_notebook_v4.py, line 51)
- gen_ai_roi_demo_temp/docs/ciso_setup_notebook_v1.py: invalid syntax (gen_ai_roi_demo_temp/docs/ciso_setup_notebook_v1.py, line 40)
- gen_ai_roi_demo_temp/docs_v2/soc_copilot_demo_v5/notebooks/setup_notebook_v4.py: invalid syntax (gen_ai_roi_demo_temp/docs_v2/soc_copilot_demo_v5/notebooks/setup_notebook_v4.py, line 51)
- gen_ai_roi_demo_temp/sources/setup_notebook_v4.py: invalid syntax (gen_ai_roi_demo_temp/sources/setup_notebook_v4.py, line 51)
- gen_ai_roi_demo_temp/sources/usable/setup_notebook_v4.py: invalid syntax (gen_ai_roi_demo_temp/sources/usable/setup_notebook_v4.py, line 51)
- gen_ai_roi_demo_temp/v2.3/project_source/setup_notebook_v4.py: invalid syntax (gen_ai_roi_demo_temp/v2.3/project_source/setup_notebook_v4.py, line 51)

The frozen SDK files were read only and their SHA-256 prefixes remain:

| File | Prefix |
|---|---|
| copilot-sdk/copilot_sdk/scoring/investigation.py | 3441dcbd |
| copilot-sdk/copilot_sdk/backend/investigation_router.py | 08f4df7a |
| copilot-sdk/copilot_sdk/scoring/scorer.py | 24ac9e49 |

Only this report was created. No existing source, tests, fixture data, configuration, or session-state file was modified by this audit. No git commands were used.

## Exit summary

Monkey patch audit complete.
Production-path files scanned: 1,164.
Test files scanned: 1,051, plus 14 conftests.
P1 (test/production behavior split): 1; additional P1 destructive demo route: 1.
P2 (test-only/demo data and surfaces): 6; additional P2 implicit pytest configuration: 1.
REVIEW (mocks/fixtures shadowing behavior or isolation): 6.
High-density mock test files: 18.
0 existing files modified; 1 report created.

