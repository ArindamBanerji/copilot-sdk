# Purchasing mutable-flow diagnosis

## Summary

Investigated on Windows on 2026-09-05, using the requested Python 3.11 environment and the live AGE demo graph. The failure is reproducible under a sequence of page loads: the unchanged two-worker order suite took **237.525s**, with **7 clean passes, 1 flaky pass, and 1 failure**. The failed reasoning test and its retry timed out awaiting score; the flaky learn test actually timed out awaiting **verify**, after score had returned in **8,539.622ms**. This is a more precise distinction than treating every failure as the same POST.

The main cause is a read path that writes: Purchasing dashboard readiness called `proof_ledger()`, which replayed every decision and outcome into new UUID-keyed AGE proof events. These synchronous GET handlers continued their work after browser cancellation. AGE contained **571,690 Purchasing proof events**, versus **14 variant-outcome events** and **12 registration/status events**. Score then repeatedly queried that growing EvolutionEvent table to choose a prompt variant, while blocking the ASGI event loop. In a real handler profile, variant selection took **2,756ms** of **2,796ms**; prediction plus decision persistence took **39ms**. Workers reduced some waiting but did not remove its source.

Four bounded fixes are implemented: remove proof replay from control GETs, use two fresh event reads per variant selection, execute blocking score work in a worker thread with its mutation lock, and honor SQLite evolution-event filters. No Playwright timeout, retry, assertion, production frontend code, scorer algorithm, or learning authorization was relaxed. The accumulated historical proof events were preserved. Multi-worker learning consistency remains a separate limitation documented in `../design/workers_safety_audit.md`.

After the fixes, isolated score medians were **416ms with one worker** and **287ms with two**. The unchanged order suite passed **9/9 without retries** in both configurations: **97.96s** and **75.52s**, respectively. Dashboard **10/10** and inventory **3/3** regressions passed with one worker. Full Purchasing backend tests passed **714**, with one skip. The full SDK/package gates retain existing failures described below, and the concurrent-read transport reset remains unresolved; this is not an unconditional all-green platform certification.

## POST /api/score Lifecycle

The requested legacy `scoring/compounding.py` and `scoring/storage.py` files do not exist here. The active implementation is `copilot_sdk/scoring/scorer.py`; Purchasing uses `PurchasingActiveAGEGraphStore` over AGE. SQLiteGraphStore is exercised by the real-store regression tests. Legacy DecisionStore is not on this HTTP path.

| Step | Code evidence | Measured cost / behavior |
|---|---|---|
| Build request | `apps/purchasing/frontend/src/screens/OrderScreen.tsx:398`; `src/api.ts:141`, `:696` | `category`, seven numerical factors, and item/quantity/day/events/cost context; camel-case context keys normalized to snake case. A top-level item/quantity-only request is invalid |
| HTTP/CORS/tenant/evidence middleware | Purchasing `app/main.py:455`, `:464`, `:882`; `services/purchasing_control.py:98`; `copilot_sdk/tenant_middleware.py:17` | Score receives evidence headers. It is outside the claim-body-rewrite routes. No external middleware I/O on this route; middleware-only duration was not independently isolated |
| Parse request, load stable context | `copilot_sdk/backend/scoring_router.py:62`, `:169`, `:204` | Stable context read-through only; measured **0.26–0.40ms** after fix. Current factors still reach the scorer |
| Acquire per-domain mutation lock | `scoring_router.py:216`; `scoring/mutation_lock.py:29` | Before: synchronous lock and database calls inside an async endpoint. After: all synchronous mutation work, including invalidation, executes inside `run_in_threadpool`; no threading lock held over the context await |
| Select prompt variant | Purchasing `main.py:541`; `evolution/prompt_evolver.py:86`; `evolution/graph_store.py:107` | Before: **10 EvolutionEvent queries / 2,756ms**, including eight reads for category stats and two registration reads. After: **2 event queries / 279–290ms** in the instrumented run. No retained TTL cache |
| Predict | `scoring/scorer.py:209`, `:377` | Category/factor validation, NumPy vector, GAE ProfileScorer prediction. Measured **0.51–0.54ms** after fix |
| Persist decision | Purchasing `app/graph_status.py:236`; `../ci-platform/ci_platform/graph/age_sdk_adapter.py:50` | Active governed write adapter; **2 graph calls**, **22–40ms** after fix. This is not the generic AGE legacy write path. Failures retain the existing outbox behavior |
| Build response | `scoring_router.py:233`, `_score_response_payload` | Dataclass/NumPy normalization and ScoreResponse validation; **0.35–0.92ms** for payload validation. Complete score body approximately **493–498 bytes**, including engine attribution |
| Invalidate affected read caches | `scoring_router.py:239`; `state/invalidation.py:80` | **0.008–0.021ms** in the Purchasing profile; no registered Purchasing TabStateCache recompute cascade. Trading can recompute its critical tab entries synchronously |
| Deliver response | HTTP probe and browser trace artifacts below | No internal HTTP calls, no conservation recalculation, and no learning in score itself. Before isolated HTTP **2,073.775 / 2,156.669 / 3,302.963ms**; after instrumented in-process HTTP **317.489 / 350.439ms** |

Profile totals include different process/sample conditions and are not additive across rows from different runs. cProfile's approximately 2.8s in lock acquisition/join is predominantly AGE's synchronous bridge waiting for query threads; it is not evidence that the numerical scorer itself uses 2.8s of CPU. Source: `../ci-platform/ci_platform/graph/age_graph_store.py:76`, `:709` and `age_client.py:573`.

The direct-before probe used the running two-worker server, verified from the Uvicorn supervisor/spawn process tree. Counting netstat listener PIDs is insufficient: Uvicorn workers share the parent's socket. The measured before score median was **2,156.669ms**; the concurrent POST alongside six GETs was **2,376.833ms**. Several GETs completed only at approximately 2.39s, after score released the event loop. These six GETs do not include dashboard readiness, so this small experiment understates the sustained browser workload.

### Verify and learn

`Confirm` calls **`POST /api/purchasing/verify`**, not a `/confirm` endpoint and not directly `/api/learn` (`OrderScreen.tsx:435`; `api.ts:713`). `routers/verify_router.py:74` validates the action/reason, reads the decision, checks verification history, calls the scorer's learning path, handles the existing conservation-pause outcome policy, and computes conservation for the response. In isolation it took **1,249.810ms**; a standalone browser run took about **1,002ms** from confirm click to response.

`CompoundingScorer.learn` (`scoring/scorer.py:923`) reads the decision, detects judgment conflicts, checks conservation, updates centroids when allowed, writes the outcome/evidence, refreshes DK and fingerprints, persists learning artifacts, and may perform evolution/archive work at their existing boundaries. The general SDK `/learn` route additionally records variant outcomes and persists L5 centroid/conservation/DK state (`scoring_router.py:244`). The direct general learn request took **1,113.665ms**. Neither path is equivalent to the cheap score prediction. The verify route's redundant full-history double-verification check remains a scaling concern, but was not the dominant isolated cost established here.

The reproduced flaky verify timeout followed an 8.54s score while two readiness and two queue GETs remained unfinished. Earlier tests can leave server work running even though Playwright creates a fresh page. Therefore “score passed in another test” does not establish that confirm encounters the same server load.

## Frontend Behavior During Score

`OrderScreen` initial load requests items, today-summary, weather, analytics and fingerprint, plus verification reason codes. After item selection it requests item profile and waste history. Child panels request `/api/purchasing/queue` and `/api/purchasing/match/queue`. Development StrictMode repeats mount effects. Global SelfComputationPanels and shell requests can still be running from the dashboard (`OrderScreen.tsx:269`, `:308`, `:337`; Purchasing `App.tsx:60`; `src/main.tsx:6`).

The click itself does this sequence (`OrderScreen.tsx:398–480`):

1. Send `POST http://127.0.0.1:8020/api/score`.
2. After its JSON returns, send `GET /api/context/similar?...&n=5`.
3. After similar returns, publish score, similar matches and the result card. Reasoning uses the supplied score/fingerprint/matches in React; this screen issues no reasoning HTTP request.
4. On a separate Confirm click, send `POST /api/purchasing/verify`.
5. After verify returns, publish its reward/IKS/conservation response, then send `POST /api/context/order-metadata`.

It does **not** initiate trajectory, conservation, or an SC refresh from the score callback. Competing dashboard/Order mount GETs explain the overlap. The complete request/timing/body logs are `logs/mutable_browser_before_workers2.json` and the after artifacts recorded below; the report's final measurement appendix lists the actual requests started within ten seconds of a click.

The unchanged `waitForResponse` filter matches the actual direct backend URL (`order.spec.ts:23`). The waiter is installed before clicking. `actionTimeout: 10_000` supplies its timeout; `test.setTimeout(60_000)` does not change that per-operation budget (`e2e/playwright.config.ts:25`). Verify's predicate also requires `response.ok()`, so a fast HTTP error can be reported as a timeout. No mismatched score URL was observed.

**Vite is not a proxy in this configuration.** `apps/purchasing/frontend/vite.config.ts:9` defines an absolute API URL and has no proxy entry. `GET :5175/api/health` returned **560 bytes of HTML**, a Vite fallback page, not backend health JSON; `POST :5175/api/score` returned **404** in 31ms. Direct health returned 1,929 bytes of JSON. Bypassing a nonexistent proxy would not fix this failure.

The 18–29s numbers in the user's passing-test output are **whole-test durations**, including backend fixture warming, dashboard navigation, Order loading and assertions. They cannot be used as isolated POST durations. A before standalone browser probe observed score returning approximately **2,540ms after click**, then the result card becoming visible about 141ms later.

## Contributing Factors Table

| Factor | Contribution | Evidence | Fix complexity / disposition |
|---|---|---|---|
| Readiness/proof GETs write history | Roughly active decisions + verified outcomes new writes per read; repeated loads generate sustained write traffic | Original `PurchasingControlService.proof_ledger`; `GraphProofLedger.record` generates UUIDs; failed traces retain readiness calls | Fixed within 50 production lines: use existing graph records for projection and count coverage directly |
| Accumulated EvolutionEvent volume | **571,690 proof events**, 14 variant outcomes; unrelated proof rows share the event label queried by selection | Read-only AGE count; `get_evolution_events` filters the label by domain/type | Further growth from reads stopped; existing historical data preserved. No EXPLAIN/index claim is asserted |
| Repeated per-variant event queries | **2,756ms**, 10 queries out of score's 12 graph calls | Actual cProfile and source loops | Fixed within 70 production lines across two SDK files; two fresh stream reads and local statistics |
| Blocking async score handler | Delays response delivery and other requests; can block the loop waiting for the proxy/domain lock | Real SQLite regression: a held domain lock delayed ping **0.603–0.605s** before the fix in Purchasing/Trading/DataOps | Fixed within 20 lines; threadpool execution with mutation serialization retained |
| Duplicate/front-loaded GETs | Dashboard + Order + globally mounted panels continue independently; repeats accumulate across retries | Full browser/trace request records and StrictMode | Removing their writes addresses the demonstrated amplification; request totals remain a UI performance concern |
| Proxy serialization | Reads and writes share one scorer RLock per process | `backend/scorer_proxy.py:30`, `:49`, `:116` | Retained for model safety; score no longer waits for it on the event loop |
| Optional similar result delays visible score | Result card is withheld until similar finishes; a failed similar request can hide a successful score | `OrderScreen.tsx:418–422` | Existing behavior documented; not the observed waitForResponse failure, because this occurs after the score response |
| Response timeout and retry amplification | Fixed 10s waiter; retries create fresh pages and more backend work | Config and unchanged order helper; baseline 237.525s | Timeout unchanged because the isolated required work does not inherently take 15–20s |
| Verify/learn persistence | About **1.11–1.25s** isolated before, with more graph/state work than score | Direct probes and scorer/verify/general learn handlers | Semantics preserved; observe after-load measurements below |
| SQLite event-filter mismatch | SQLite ignored `event_type` and `variant_id`; registrations could be interpreted as failed outcomes in GraphVariantStore | New real SQLite selection test caught a wrong cold-start choice | Fixed with four SQL-filter lines; filters run before LIMIT |

Small payloads, Vite, and evidence header generation are not established primary causes. The evidence middleware does not call the proof service on score: the **separate readiness GET** calls it. This distinction prevents optimizing the wrong layer.

## Fixes Implemented

1. **Keep synchronous mutations off the event loop.** Stable context is awaited before acquiring the threading lock; scorer access, variant selection, decision persistence, response shaping and invalidation run together in the threadpool. HTTP schemas and exception mapping remain intact. Regression tests use real scorers/SQLite and a held real mutation lock, without mocking scorer or storage methods.
2. **Read variant state once per selection.** GraphVariantStore builds a disposable InMemoryVariantStore from the two persisted event streams. PromptVariantEvolver reuses category/global statistics during that one decision. No instance-level history cache is retained. Real SQLite SQL tracing asserts exactly two queries, and another connection writes outcomes to verify that the next selection observes them. Existing tie-breaking, default selection and hooks are covered by the evolution tests.
3. **Make control reads read-only.** Readiness derives coverage/conservation from graph decisions/outcomes. Proof/handoff responses project those already persisted records and keep explicit proof receipts. Explicit outcome POSTs still persist receipts; GETs do not replay them. Proof history requests ask storage for the existing bounded response limit instead of fetching 10,000 events for a 100-entry display. A real HTTP regression checks repeated readiness/proof/handoff/discovery GETs leave the event stream unchanged while returning coverage and decision evidence.
4. **Respect SQLite event filters.** Apply event-type and variant-ID predicates before limiting returned rows. This fixes the real adapter discrepancy exposed during verification and keeps selection tests faithful to AGE semantics.

All four implementation groups are below 200 new production lines each. Five production files changed, with SDK changes affecting multiple copilots. No database data deletion or protocol-signature change was made.

## Fixes Deferred (>200 lines)

**Durable multi-worker model consistency (more than 400 lines, previously designed in the workers audit).** Persist a complete versioned model state, including centroids, Welford state, posterior and conservation/control state, under one transaction/compare-and-swap boundary. Score must observe a committed version; learn must reload/retry on version conflict. Invalidation and ownership must cross process boundaries. A request-local variant snapshot does not make the cached scorer fresh. Two-worker HTTP passes are not a correctness certification for concurrent learning.

**Historical proof cleanup and durable event-query capacity (estimated 250–400 lines including migration/verification).** Inventory proof-event `stable` payload identities, retain a deterministic canonical record, map any references before removal, and validate counts/receipts before and after a reversible migration. Separately assess AGE query plans and indexed/materialized event summaries with an explicit version/refresh contract. Include SQLite/AGE parity, historical status ordering, and the current 10,000-event evolution-history bound. The current task stops read-induced growth; it does not silently rewrite 571,690 existing evidence records. A raw delete statement is not a sufficient migration design.

## Broad Platform Findings

**Writes are not confined to POST routes.** The readiness GET was the strongest example. `fingerprint()` can also persist a fingerprint artifact (`scoring/scorer.py:1172`), and some preview/evidence flows perform graph reads or writes. Browser cancellation is not a transaction rollback and does not automatically stop a synchronous handler already executing.

The write-route inventory includes shared `/score`, `/learn`, `/self/regime-reinit`, `/self/rollback`, evolution record-outcome/promotion, transfer execute, and archetype apply. Purchasing adds verify, metadata, auto-order enable/disable/evaluate, match, events, proof-outcome, promotion, frozen-twin and demo reset/chain routes. Trading adds journal writes, broker orders/sync, webhook score, social score-as, imports, market refresh, and evolution lifecycle/promotion. DataOps adds apply-fix, alert metadata, perturb/revert, holdout registration/verification, promotion and frozen-twin. Not every POST is a write: conservation what-if and several query/preview endpoints compute responses. Source inventory: `copilot_sdk/backend/*_router.py`, `apps/*/backend/app/routers/`, and context routers.

Trading and DataOps mount the same SDK score router. Trading's score callback first fetches current regime, then scores, persists trade metadata and fetches similar trades (`LogTradeScreen.tsx:208–289`). DataOps scores, publishes its result, fetches abstention state and writes alert metadata (`TriageScreen.tsx:248–294`). Their non-shared synchronous mutation handlers already use FastAPI's threadpool; they can still queue behind locks/database capacity. Async DataOps connector routes need endpoint-specific profiling before attributing delay to synchronous blocking. No claim is made that every write handler has the same bottleneck.

The screen-request inventory is recorded in `logs/mutable_screen_counts_healthy.json`. Counts use seven-second observation windows, include attempted API requests and development mount duplicates, and depend on current selected entities. Dashboard counts include shell/global panels; subsequent rows count incremental navigation requests. SOC/S2P were sampled at initial page load, not exhaustively through every screen. These are workload observations, not fixed universal request budgets. Earlier trial files include a selector error and a backend restart and are not used for this table.

| Copilot | Screen: attempted requests / distinct method-paths |
|---|---|
| Purchasing | Dashboard **68/34**; Order **18/10**; Analysis **36/13**; Inventory **34/16**; Performance **56/24** |
| Trading | Dashboard **57/29**; Log Trade **8/4**; Analysis **61/27**; Performance **100/34**; Journal **6/2**; Trade Detail **0/0** with no trade selected |
| DataOps | Dashboard **60/25**; Triage **0/0** with no alert selected; Insight **47/20**; Evidence **40/17**; Curve **6/2** |
| SOC | Initial page **30/14** |
| S2P | Initial page **24/10** |

Purchasing Inventory's core summary request is still one API call per effect; the 34 count includes its evolution/SC/child panels and repeated mounts. Trading Performance requested regime and active-evolution state six times each. DataOps Dashboard requested enterprise-health eight times and trajectory six times. These bounded observations support shared-request coordination as follow-up work; they do not by themselves establish an infinite React loop. A populated DataOps Triage screen starts at least the six detail/dependency/factor/recurrence/recommendation/conservation calls in `TriageScreen.tsx:130`, followed by conditional system/history work; the zero-selection row is not its populated request budget.

Hidden limits and failure handling remain relevant: Purchasing/Trading/DataOps GET helpers typically abort at 5s; S2P contains 10s/15s request limits. Purchasing POST has no explicit AbortController timeout. `safeApiGet` and several DataOps optional loaders turn errors into null/empty state, while Purchasing App falls back to IKS 50 after trajectory failure (`api.ts:108–151`; DataOps `DashboardScreen.tsx:105–136`; Purchasing `App.tsx:35`). The backend fixture retries health with exponential backoff and skips on exhaustion; its fingerprint/conservation warm-up errors are swallowed (`e2e/fixtures/copilot-fixture.ts:17–71`). These patterns can obscure partial loading, but no skip was treated as a successful gate here.

The order tests do not require score from a preceding test: every mutable test scores its own decision and every test gets a fresh page. They do rely on a prepared catalog, server model state, and the demo route being enabled. Demo reset clears chain/events/outbox state, **not all scored/learned decisions or the graph proof-event history** (`main.py:923`). Test retries therefore do not restore a fresh backend.

## Cross-Copilot Impact

The threadpool change applies to all users of `create_scoring_router`, including Purchasing, Trading and DataOps. The regression exercises those three actual presets and confirms a decision is persisted while an unrelated ping remains responsive. Variant selection changes apply to GraphVariantStore consumers; in-memory and legacy durable stores retain their existing public protocol. SQLite filtering affects all domains and is included in the SDK-wide test gate. The control-service change is Purchasing-specific. The final gate section distinguishes startup, endpoint responsiveness, Playwright flow success and the unresolved cross-worker model-coherence guarantee.

## Files Changed

- `copilot_sdk/backend/scoring_router.py`
- `copilot_sdk/evolution/graph_store.py`
- `copilot_sdk/evolution/prompt_evolver.py`
- `copilot_sdk/graph/sqlite_store.py`
- `apps/purchasing/backend/app/services/purchasing_control.py`
- `tests/backend/test_score_responsiveness.py` (new)
- `tests/evolution/test_selection_snapshot.py` (new)
- `apps/purchasing/backend/tests/test_control_reads.py` (new)
- `scripts/mutable_flow_probe.py` (new, explicit real writes)
- `e2e/diagnostics/mutable-network-probe.mjs` (new)
- `e2e/diagnostics/screen-request-probe.mjs` (new)
- `docs/diagnostics/mutable_flow_diagnosis.md` (this report)
- `graphify-out/graph.json` (generated)
- `graphify-out/GRAPH_REPORT.md` (generated)
- `graphify-out/manifest.json` (generated)

Diagnostic scratch scripts under workspace `.codex_tmp/` profile the actual handlers, count AGE event types, and extract retained Playwright traces. Logs and copied baseline traces are under ignored `logs/`. No git command was used.

Scope for this task: **12 source/test/probe/report files plus 3 generated graph files**. The three additional workspace scratch scripts are `.codex_tmp/mutable_profile.py`, `.codex_tmp/mutable_graph_counts.py`, and `.codex_tmp/mutable_trace_read.py`; they are outside the SDK directory. The earlier workers/SC changes remain in place and are not counted as new changes in this task.

## Remaining Risks

Multi-worker cached centroids/control state remain unsafe for unrestricted concurrent learning; use one worker for authoritative demo mutations until the versioned-state design is implemented. Historical proof rows still cost storage/query work. Query snapshots use two separate event reads, not a database-wide transactional snapshot, and the existing 10,000-event stream bound remains. Control response lists remain bounded and preserve existing explicit ledger entries; they do not guarantee every historical or newest decision appears in a 100-entry view. Purchasing still delays result rendering behind the optional similar lookup. The latter is a separate UI resilience improvement, not evidence for a score-response timeout.

An incidental launcher restart race was also observed: `demo.py:987–990` kills the old listener and immediately checks the port; once, the closing socket still appeared open, so startup reported an existing backend and subsequently failed health. The diagnostic log correctly said no new backend had been launched (`logs/mutable_launcher_purchasing_refresh.log`). Explicit selected `--stop`, a three-second wait, then start succeeded. This existing launcher behavior was not the cause of the original running-server score timeout; no launcher source was changed in this task. The centroid-timeline connection resets described in the measurement appendix remain a separate unresolved transport observation.

## Recommended Next Steps

Keep the one-worker mode as the normal mutable-demo configuration. Review the retained before/after HTTP and Playwright traces when evaluating future timeout changes. Schedule the evidence-data migration and transactional model-state work separately. Add endpoint tracing for lock wait, database time and response completion if diagnosing another production workload; a whole Playwright test duration must not be labeled handler time.

## Measurement Appendix and Test Results

### Direct HTTP measurements

All score requests below returned HTTP 200 with the same schema and approximately 493–498 bytes. Probes perform real, separately identified score/verify/learn writes; they are not dry runs. Samples are consecutive requests without a browser. They are observations on this demo host, not percentile estimates.

| Operation | Before, 2 workers (ms) | After, 1 worker (ms) | After, 2 workers (ms) |
|---|---:|---:|---:|
| Isolated score, run 1 | 2,073.775 | 314.066 | 294.081 |
| Isolated score, run 2 | 2,156.669 | 415.786 | 285.156 |
| Isolated score, run 3 | 3,302.963 | 479.548 | 286.900 |
| **Isolated score median** | **2,156.669** | **415.786** | **286.900** |
| Score concurrent with six GETs | 2,376.833 | 893.359 | 347.023 |
| Verify in isolation | 1,249.810 | 1,061.287 | 554.518 |
| General learn in isolation | 1,113.665 | 1,237.117 | 715.187 |

Sources: `logs/mutable_before_workers2.json`, `logs/mutable_after_workers1_elevated.json`, and `logs/mutable_after_workers2.json`. The initial after one-worker probe also completed isolated score in 511–592ms; the elevated repeat above checked whether sandboxing explained a concurrent-read error. After the two-worker probe, the actual supervisor PID was **37684**, with spawn worker PIDs **41636** and **15760**; PID **23508** was the virtualenv launcher. One netstat listener does not establish one worker.

**The after concurrent batch is not all green.** Five GETs and score completed, but `/api/self/centroid-timeline` reset its connection at **19,560ms** with one worker and **19,040ms** with two. It also reset in the initial sandboxed after probe. Backend logs contain Windows Proactor socket-close `ConnectionResetError` callbacks; this does not establish the application or network cause. Similar resets occurred before these changes in the SC investigation (`sc_endpoint_slowness.md:64`, `:89`). No retry was added to hide the failure, and it cannot be attributed solely to sandboxing. The before concurrent batch completed; therefore the table reports POST improvements without claiming every concurrent GET improved.

The score body contains `decision_id`, `action`, `action_index`, `confidence`, four `probabilities`, `category`, seven `factors`, and `engine`. It is not a large graph dump. Verify and general learn responses were approximately 561 and 465–467 bytes. Full bodies are retained in the probe JSON.

### Browser requests within ten seconds of Score

The after one-worker probe observed the following requests starting within ten seconds of the Score click. It also clicked Confirm after the result appeared; the last two rows are caused by that separate action.

| Start after Score click (ms) | Method and path | Response |
|---:|---|---|
| 55.7 | `POST /api/score` | 200 |
| 798.4 | `GET /api/context/similar?...&n=5` | 200 |
| 969.7 | `POST /api/purchasing/verify` | 200 |
| 2,459.0 | `POST /api/context/order-metadata` | 201 |

Score response arrived **792.713ms after click** and its result appeared approximately **133ms later**. Verify took **1,521.587ms from Confirm click**. Before, the comparable standalone browser score took **2,539.811ms**, with similar/verify/metadata starting at approximately 2,549/2,765/3,695ms after Score. Source: `logs/mutable_browser_after_workers1.json` and `logs/mutable_browser_before_workers2.json`. The after probe's cold dashboard load also contained aborted optional GETs, and took 15.66s to reach its readiness marker. These timings are not presented as a perfect or fully loaded initial page.

### Verification gates

Focused verification completed: **266 SDK tests passed** and **25 Purchasing tests passed**. Full Purchasing tests finished with **714 passed, 1 skipped, 0 failed in 672.24s** (`logs/mutable_purchasing_tests.log`). The skip is not counted as a pass.

The full SDK run finished with **3,351 passed and 3 failed in 1,122.19s**. Two failures were stricter mypy checks exposing a missing protocol annotation and invariant dictionary typing in the new selection code. Both were corrected with `VariantStore` and read-only `Mapping` annotations; all three type-checking tests plus the selection regression then passed (**4 passed in 34.25s**). These were annotation-only corrections. The remaining failure is the existing `tests/test_ent03_models.py::test_no_incorrect_rl_naming`, which identifies unchanged text in `docs/design/product_integrity_execution_strategy_v3_0.md` at lines 38, 839, 1480 and 1506. It was already recorded by the previous audits. The complete SDK suite was not rerun after the annotation corrections; the recorded full run and targeted recovery are distinguished rather than reporting an invented fresh all-green result. Sources: `logs/mutable_sdk_tests.log`, `logs/mutable_type_recheck.log`.

| Playwright gate | Backend workers | Result | Duration |
|---|---:|---|---:|
| Unchanged order baseline | 2 | 7 clean passes, 1 flaky pass, 1 failure | 237.525s wall |
| Order after | 1 | **9 passed, 0 failed, no retries** | **97.962s wall** |
| Order after | 2 | **9 passed, 0 failed, no retries** | **75.522s wall** |
| Dashboard regression | 1 | **10 passed, 0 failed, no retries** | 1.3m as reported by Playwright |
| Inventory regression | 1 | **3 passed, 0 failed, no retries** | 49.271s wall; 46.2s runner |

Artifacts: `logs/mutable_pw_before_workers2.log`, `logs/mutable_pw_order_workers1.log`, `logs/mutable_pw_order_workers2.log`, `logs/mutable_pw_order_workers2_timing.log`, `logs/mutable_pw_dashboard_workers1.log`, and `logs/mutable_pw_inventory_workers1.log`. Wall times include command startup/global setup. The baseline failure traces were copied into `logs/mutable_baseline_traces/` before later runs replaced Playwright's output directory.

| Order test | After, 1 worker (s) | After, 2 workers (s) |
|---|---:|---:|
| Item dropdown | 11.3 | 5.8 |
| Cost analysis | 8.5 | 7.2 |
| Cost framing | 9.2 | 7.4 |
| Seven factors | 9.5 | 7.2 |
| Score result | 10.6 | 8.2 |
| Confirm reward | 11.5 | 9.5 |
| Learn response | 11.7 | 9.1 |
| Similar orders | 9.8 | 7.9 |
| Reasoning | 9.4 | 7.8 |

Final per-file mypy passed on all **nine changed repository Python files**, using `--follow-imports=skip --no-error-summary`. The three scratch Python files also passed with the same flags and the Purchasing backend added to MYPYPATH. Both diagnostic JavaScript files passed `node --check`. Production frontend and E2E TypeScript were not changed, so the user's conditional TypeScript gates were not invoked.

A final read-only AGE count found **571,690 proof records**, exactly the same as the initial count, after the HTTP probes, browser navigation inventory, and all regression suites. Variant outcomes increased from 14 to 18 through the intended general learn writes. This is live evidence that the dashboard/control reads no longer replay proof history; the real SQLite HTTP test also asserts event preservation across repeated control GETs. Sources: `logs/mutable_graph_counts.log`, `logs/mutable_graph_counts_after.log`.

Stopping the two-worker Purchasing instance left **zero** of its launcher/supervisor/worker PIDs and **zero listeners on 8020** (`logs/mutable_stop_verification.log`). Purchasing was then restored to **one worker**, with its frontend ready (`logs/mutable_launcher_restored_workers1.log`). All five backends returned HTTP 200 with JSON health responses on **8001, 8010, 8020, 8030 and 8002** (`logs/mutable_final_health.json`); the other four remained in the one-worker configuration started earlier. No Trading/DataOps mutable Playwright suite was run for this task; cross-copilot evidence here is startup plus the real-store shared-router regressions, not an unperformed end-to-end certification.

`graphify update .` completed successfully after the final source changes: **21,344 nodes and 40,499 edges** over **1,692 files** (`logs/mutable_graphify_final.log`). Its HTML visualization was skipped because the graph exceeds the tool's 5,000-node visualization limit; the code graph and report were updated. This does not block the requested Markdown report.

Completion scope: **10 contributing factors documented; 4 bounded fixes implemented; 2 larger designs deferred; 9/9 order tests passing with either worker count; 10/10 dashboard and 3/3 inventory regressions passing**. No newly introduced failing test remains in the executed checks after the typing corrections. The existing SDK naming/package failures, concurrent-read reset and multi-worker model-consistency risk are explicitly outstanding.

The repository's prescribed package gate remains blocked by existing configuration: `pyproject.toml:61` names an unavailable build backend, and `copilot_sdk/__init__.py` does not export `CopilotFramework`. The actual install/import failures are saved in `logs/mutable_package_gate.log` and `logs/mutable_import_gate.log`. These files were not changed to mask the gate.
