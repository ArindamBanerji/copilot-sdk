# Demo Feature Design — v2: Verified Contracts and Story Evidence
**Reviewed:** Sep 18, 2026 (America/Los_Angeles).
**Baseline:** 56 catalog rows; saved run reports 30 passed, 26 skipped, 0 failed.
**Purpose:** Correct v1 against source, mounts, actual spec bodies, and read-only live probes.
**Decision:** Do not commission 14 greenfield features or promise 56 demonstrated stories from endpoint availability.

Only this document and the SDK session-state append are deliverables of this review.
No source/spec changes, server restarts, fixture injection, scoring, checkpoint creation, rollback, or suite reruns were performed.
All implementation changes below are recommendations for a subsequent authorized task.

## Part 0: Verification Results

### 0.1 Evidence scope and limitations

Repository abbreviations used in source references:

- **SDK:** `copilot-sdk`.
- **SOC:** `gen-ai-roi-demo-v4-v50`.
- **S2P:** `s2p-copilot`.
- All spec paths are relative to `SDK/e2e/demo/`.
- All API paths below are either exact existing spec probes or explicitly identified source-discovered native routes. A proposed compatibility contract is not an existing spec requirement.

Read the first 80 lines of SDK and SOC `docs/session_state.md` and S2P `backend/docs/session_state.md`.
Read v1, `pw_selfdiag_report.md`, `pw_selfdiag_results.txt`, SOC `docs/soc_endpoint_map.md`, the demo specs, relevant routers/services/models/mounts, and fixture files.
The requested `docs/map_addendum_v26.md` was not found at that location.
The actual shipping evidence is `SDK/docs/design/master_action_plan_v5.228 (1).md:274–278`: DI prompt integration, valuation, intelligence map, and acquisition advice are CLOSED/PASS at v0.7.62.
Those historical test counts were read, not rerun.

Live verification used the 23 requested GET probes, plus 19 native/contract-disambiguation GET probes.
OpenAPI discovery was also attempted on all five ports: Trading responded; SOC, S2P, Purchasing, and DataOps exceeded the 10-second request timeout.
A discovery timeout is not evidence that a route is absent.
POST operations were not exercised because this review is read-only.
Consequently a GET 405 confirms a method mismatch, not a failed POST feature.
Source presence, current process behavior, and saved-run results are separate evidence layers; deployment/version differences remain possible.

**Historical HTTP-status limitation:** the saved list reporter prints skipped test names, not their skip annotations.
The report says “SKIP (HTTP status)” but supplies no number.
For every historical runtime skip below, the exact original HTTP status is **not recorded**.
Current GET results and source-inferred POST validation/resource failures must not be substituted for historical measurements.

### 0.2 Corrected current-state table

The v1 pass list matches the report exactly. SOC-04 and SOC-08 were already counted as passing in v1.
The correction is the interpretation of those passes and skips, not a fabricated change in counts.

| Saved-run category | Count | Catalog IDs |
|---|---:|---|
| PASS, assertions executed | 30 | SOC-01/03/04/07/08; S2P-04/05/06/08; PUR-01/02/03/04; TRD-01/03/06; DO-01/02/03/06; PLAT-02/04/06/07; MACH-04; PILOT-01/02/03/04; FORK-01 |
| Runtime HTTP skip; exact code unavailable | 16 | SOC-02/06/09/10; S2P-01/02/03/09; PUR-05; TRD-02; DO-04/05; PLAT-03; MACH-01/02/03 |
| Permanent ROADMAP skip; no HTTP call | 7 | SOC-05; S2P-07; PUR-06; TRD-04/05; DO-07/08 |
| Permanent CONCEPTUAL skip; no HTTP call | 3 | PLAT-01/05; MACH-05 |
| Failed | 0 | Saved run only; no new run in this review |

The directory counts are SOC 10, S2P 9, Purchasing 6, Trading 6, DataOps 8, Platform 7, Machine 5, Pilot 4, Fork 1: **56**, not 47.
The 10 permanent specs contain `test.skip(true, ...)`; shipping an endpoint cannot activate them.
The 16 runtime skips do not all mean “endpoint down”: bad bodies, absent fixture resources, and wrong URLs are distinct causes.

### 0.3 What the passing tests actually establish

Most passing specs assert only that JSON is defined and is not the string `{}`.
These are API smoke checks, not browser rendering checks or proof of the catalog story.

| Spec(s) | Actual test limitation | Required later acceptance evidence |
|---|---|---|
| SOC-01 | Reads evolution trust scores, not the catalog's learning-state/verified-count contract | Retained domain knowledge with nonzero verified support |
| SOC-03 | Nonempty recent-events JSON | Both promoted and rejected counts/events; exact 12/35 only if supported |
| SOC-04 | POST simulate-failure then nonempty JSON; no AMBER assertion or restoration | Controlled before/after gate transition and cleanup |
| SOC-07 | Nonempty audit-verification JSON | Verification boolean and actual CSV export; no invented CSV capability |
| SOC-08 | Nonempty frozen-twin JSON | Defined comparison provenance and appropriate paired evidence, not merely drift fields |
| S2P-04/05/06/08 | Nonempty conservation/compliance/threshold JSON | GREEN with support; extinction N→0; kept-manual failed bar; four bands and noise metadata respectively |
| PUR-01/02/03/04 | Fingerprint or conservation smoke checks | Inherited nonzero weights; high-noise trust trap; actual pause; actual proof and competence curves |
| TRD-01/03/06, FORK-01 | Fingerprint/category smoke checks | Ten learned factors or the certificate-specific supported assertion |
| DO-01/02/03/06 | Nonempty perturbation/trust/fingerprint/decisions response | Before/after change, differentiated trust, six factors plus checkpoints, historical differentiation |
| PLAT-02 | Publish/list checks for a fixed entity string | Returned signal ID, isolation, and receipt/re-scoring if claiming SOC→S2P influence |
| PLAT-04 | Five conservation HTTP successes and list length five | Actual time-series data for five curves; status objects are not curves |
| PLAT-06/07 | Nonempty platform JSON | Five domain rows with EXPLORATORY provenance; accumulated decisions >0 |
| MACH-04 | Nonempty learning-state | Actual tensor dimensions and separate plateau evidence |
| PILOT-01/02/03/04 | Health, centroid-history, or conservation smoke checks | Readiness fields; >7-day verified gap; timestamped μ/σ/K evidence; proof export |

SOC-09 is especially unsafe as written: it compares top-level `action` and `confidence`, but SOC returns these under `recommendation`.
Two successful responses with both top-level fields absent would compare `undefined === undefined` and pass.
MACH-03 currently issues only one POST; it cannot establish a two-decision K change.
SOC-10 currently creates a checkpoint at the wrong path; it never scores, rolls back, or compares state.
These assertion repairs are prerequisites for a credible “56 stories” claim.

### 0.4 Requested live GET probe ledger

Observed during this review; no POST result is implied.

| Port | Requested path | GET status | Meaning |
|---|---|---:|---|
| 8001 | /api/alert/analyze | 405 | POST handler exists |
| 8001 | /api/learning/checkpoint | 404 | Not the mounted checkpoint path |
| 8001 | /api/learning/checkpoints | 404 | Not the mounted list path |
| 8001 | /api/learning/frozen-twin | 200 | SOC-08 route already available |
| 8001 | /api/alert/cross-correlate | 404 | No dedicated route at this path |
| 8002 | /api/fingerprint | 404 | Generic compatibility route absent |
| 8002 | /api/s2p/insight/fingerprint | 422 | Required invoice_id omitted |
| 8002 | /api/s2p/score | 405 | POST handler exists |
| 8002 | /api/learning/frozen-twin | 404 | Wrong native twin path |
| 8002 | /api/self/investigation-budget | 404 | No statistics endpoint here; permanent spec does not probe it |
| 8010 | /api/self/regime-analytics | 404 | Native Trading prefix differs |
| 8010 | /api/self/investigation-trace | 404 | Existing investigation is POST with an input contract |
| 8010 | /api/self/entrant-comparison | 404 | No dedicated endpoint found |
| 8010 | /api/platform/concepts/four-clocks | 404 | Not called by permanent conceptual spec |
| 8020 | /api/learning/frozen-twin | 404 | Purchasing-specific prefix differs |
| 8020 | /api/self/investigation-trace | 404 | Existing investigation is POST |
| 8030 | /api/self/rule-lifecycle | 404 | Existing route requires rule_id |
| 8030 | /api/self/k14-comparison | 404 | Not the URL DO-05 actually calls |
| 8030 | /api/di/acquisition-advisor | 404 | Actual suffix is acquisition-advice |
| 8030 | /api/di/prompt-integrator | 404 | NL query uses POST /api/di/query |
| 8030 | /api/dataops/intelligence-map | 404 | Mounted native map uses /api/di/intelligence-map |
| 8030 | /api/dataops/acquisition | 404 | Wrong route |
| 8030 | /api/dataops/acquisition-advisor | 404 | Wrong route |

### 0.5 Source-discovered live contracts and data

| Port | Additional GET probe | Status / actual observation |
|---|---|---|
| 8001 | /api/fingerprint | 200; six factors, reported weights zero, decisions_analyzed=0, shape 6×4×6 |
| 8001 | /api/soc/checkpoint/list | 200; one checkpoint, decision_count=0 |
| 8001 | /api/soc/centroid-backups | 200; backups available |
| 8001 | /api/conservation/status | 200; status RED, theta_min=1e9, verified_count=0 in observed response |
| 8001 | /api/alerts/queue | 200; queue array available |
| 8002 | /api/s2p/learning/twin | 404; exact S2P-09 probe is wrong |
| 8002 | /api/s2p/learning/frozen-twin | 200; frozen_available=true, current_decisions=812, compared_decisions=0, delta_accuracy=null, visual_diff=[] |
| 8002 | /api/s2p/insight/fingerprint?invoice_id=S2P-INV-0001 | 200; invoice-level factor mapping, not learned domain weights |
| 8010 | /api/trading/regime-analytics | 200; 800 decisions, three regimes; trending 24, volatile 4, ranging 772 |
| 8010 | /api/trading/regime/throttle | 200; regime_break_active=false, current regime unknown, observation_only=true |
| 8020 | /api/purchasing/frozen-twin | 200; available=false, status NOT_INITIALIZED |
| 8020 | /api/purchasing/frozen-twin/comparison | 404; route exists, but twin resource is uninitialized |
| 8030 | /api/di/acquisition-advice | 200; recommendations present |
| 8030 | /api/di/query | 405; registered POST, not a missing NL feature |
| 8030 | /api/dataops/di/acquisition-advice | 200; second mounted DI prefix also works |
| 8030 | /api/di/intelligence-map | 200; populated map |
| 8030 | /api/self/rule-genealogy | 200; rules=[], total=0 |
| 8030 | /api/score | 405; POST exists |
| 8030 | /api/investigation/health | 200; investigation available, K store available, classifier_loaded=false, default_budget=2 |

Do not erase or “repair” the live RED state during a review.
Its cause was not established; it makes earlier GREEN assumptions unsafe.
An empty comparison, uninitialized resource, or zero weights is a data/state finding, not a reason to generate fabricated gains.
SOC's live twin JSON exposes drift/IKS fields; inspect versioned native schemas before assuming uniform live/frozen series across repos.

### 0.6 Verified Claims: v1 assumption audit

Classification is of the **build premise**, not whether the catalog story has been demonstrated.
Eight premises are substantially contradicted/already implemented, five are partial or overstated, and one missing production integration is confirmed.
All 14 were assessed; none of these counts represents completed story acceptance.

| v1 item | Classification | Verified correction and evidence |
|---|---|---|
| F-DEMO-01 analyze | Partial | Handler, nested score, referral and novelty already exist; trace/K-causal story needs separate work. SOC triage.py:619,874,987,1490; schemas.py:33 |
| F-DEMO-02 checkpoint | Contradicted | Mounted AGE-backed create/list/rollback already exist. SOC framework_router.py:483,507,515; framework/checkpoint.py |
| F-DEMO-03 S2P score | Contradicted as backend-missing premise | Existing POST; spec missing amount/supplier_id and uses invalid category. S2P s2p.py:2109,2155,2163 |
| F-DEMO-04 twins | Contradicted | Native twins already exist in both domains; availability/paired evidence are the gaps. S2P s2p_demo_beats.py:175; SDK purchasing_control router:39–55 |
| F-DEMO-05 regime | Contradicted | Mounted regime analytics, monitor and throttle exist. SDK Trading main.py:663; routers/regime_analytics.py:21,27; regime_beats.py:90 |
| F-DEMO-06 lifecycle | Partial | Per-rule and genealogy APIs already mounted; collection URL and actual promotion→demotion evidence absent. SDK self_computation_router.py:508,514 |
| F-DEMO-07 K14 | Partial | DO-05 actually calls /api/score, not proposed comparison URL; shared investigator already compares surface/final actions. SDK investigation_router.py:56 |
| F-DEMO-08 alias | Contradicted scope estimate | Missing generic alias confirmed, but native requires invoice_id and returns a different semantic shape; not a three-line domain-fingerprint delegation. S2P s2p_insight.py:129 |
| F-DEMO-09 trace | Contradicted | Existing POST investigator and response steps/contrast; remaining story fixtures, adapters and display differ from new engine work. SDK investigation_router.py:18–39,56 |
| F-DEMO-10 entrant | Partial | Dedicated surface absent; one historical accuracy point is not a controlled paired entrant study |
| F-DEMO-11 kill chain | Partial | Dedicated pair contract absent, but cross-graph discoveries and campaign correlation already exist. SOC discoveries_router.py:77; cross_graph_discovery.py; triage.py:1132 |
| F-DEMO-12 RL | Confirmed missing production integration | Experiment is not the production budget policy. Fixed/optional classifier budget support exists. Experiment summary contradicts “safe at λ=0” for SOC |
| F-DEMO-13 concepts | Contradicted necessity | Specs have no requests; narrative panels/content tests need no mandatory backend concepts endpoint |
| F-DEMO-14 DI | Contradicted | Routers mounted, services supplied, frontend panels wired, native acquisition GET live; no mount-only feature needed. SDK DataOps main.py:886,903; api.ts:369,403; MAP R27–R30 |

Additional corrections:

- v1 says “12 features” but enumerates 14.
- Its individual estimates sum to 15 person-days, not the stated approximately 12 days.
- Its batch spec gains sum to 27 although only 26 are skipped; some batch headings disagree with their own rows.
- The SOC-04/SOC-08 pass-list discrepancy suggested in the review brief is not present in the actual v1.
- Historical session summaries claiming SOC fingerprint is absent are superseded by the current 200 and compatibility route; do not use them as current route truth.
- A “fixture exists” claim is not “fixture executes.” SOC preseed creates graph alerts/context; file placement alone does not do that.
- `SDK/data/demo_fixtures/soc_recursion_k_delta.json` merely states first factors and k_entry_changed; no observed K snapshots or executable verification.
- `SDK/data/demo_fixtures/dataops_k14_divergence.json` states APPROVE/REJECT and prose; no scored input/evidence trace.
- The cited CTRL-2C summary gives S2P λ=0 gain +6.818pp, but SOC's selected safe λ is **1**, gain +6.469pp. SOC λ=0 clean pause is **80%**, not safe.
- Those CTRL-2C results are geometry-derived/simulated, in-distribution. They are not production accuracy uplift measurements.
- A 200 is not sufficient for promotion; 404 can mean a missing entity, and 422 normally means an invalid request, not absent implementation.

## Part 1: Corrected Feature Inventory and Per-Spec Contracts

### 1.1 Contract conventions

Every row below refers to its named existing `.spec.ts` file.
“Historical: unrecorded” means it was skipped in the saved run, but no numeric status survives in the provided text artifacts.
“None” means the permanent test never sent a request.
All writes mentioned are future implementation/test setup, not actions taken in this review.

For SOC's analyze handler the supported body is `{alert_id, deployment_version?, simulate_failure?}`.
The current generic specs invent `PW-SELFDIAG-...` alert IDs and do not load their claimed fixtures.
Source explicitly returns 404 for an absent alert or context and 503 for unavailable scorer.
Current GET=405 does not tell us which POST error occurred historically.

For S2P the minimum score body includes `event_id, category, amount, supplier_id`.
The score response has `action, confidence, factor_vector, factor_names, probabilities, decision_id`, not the proposed generic `factors` array.
A typed example derived from an existing invoice is `{event_id:"S2P-INV-0001", category:"contract_gap", amount:22426.73, supplier_id:"SUP-001"}`.
This is a shape example, not a replay-safe instruction or an ACCEPT/HOLD guarantee.
The gate may hold/reject scoring; valid schema alone does not guarantee normal scoring output.

### 1.2 SOC skipped specs (five)

#### SOC-02 — no-precedent
- **Spec:** `soc/soc-02-no-precedent.spec.ts`.
- **Exact probe:** POST `http://127.0.0.1:8001/api/alert/analyze`; generic invented alert ID. Historical status: unrecorded. Current GET to that path: 405.
- **Exists/mounted:** Yes, SOC `backend/app/routers/triage.py:619`, mounted in `backend/app/main.py:169`. Already returns `no_precedent`; `services/soc_explainability.py:18` defines `is_novel, similar_count, min_distance, threshold`.
- **200 repair:** No new scoring endpoint. Future change this spec to use a graph-loaded alert such as `PL-SOC-1-NO-PRECEDENT-001`; verify context via existing `scripts/preseed_demo_scenarios.py`.
- **Story work:** Assert nested recommendation and actual novelty results. `similar_count` counts nearby action centroids, not retrieved historical cases; do not relabel it `similar_cases=[]`. If historical-case emptiness is essential, extend triage's retrieval evidence with a defined query rather than inventing an array.

#### SOC-05 — two-alerts
- **Spec:** `soc/soc-05-two-alerts.spec.ts`. Exact probe: **none**, permanent ROADMAP skip; historical status: none.
- **Exists/mounted:** No dedicated v1 `/api/alert/cross-correlate` route (GET 404). Existing `/api/discoveries` router is mounted in SOC main.py; campaign correlation already feeds analyze.
- **Product work/files:** Extend `backend/app/services/cross_graph_discovery.py` and `backend/app/routers/discoveries_router.py` only for missing pair-specific evidence; reuse campaign matching in triage rather than inventing a second correlation engine.
- **Acceptance:** Fixture two alerts with independently benign outcomes and evidence-linked coordinated risk; negative pair control, provenance, reproducible shared entities. Rewrite this permanent spec against the agreed native contract. A dedicated new pair API is optional and would require a separate contract decision.

#### SOC-06 — policy-wins
- **Spec:** `soc/soc-06-policy-wins.spec.ts`.
- **Exact probe:** POST `http://127.0.0.1:8001/api/alert/analyze`; invented alert ID. Historical: unrecorded; current GET: 405.
- **Exists/mounted:** Same mounted handler. `referral.should_refer/reasons/audit_summary`, `decision_method="referral_override"` and `recommendation.action="refer_to_analyst"` already implement a veto (triage.py:987–1005).
- **200 repair/files:** Fix this spec's alert ID/setup using `PL-SOC-3-POLICY-CONFLICT-001`; ensure graph fixture fields activate the intended rule through SOC preseed. No duplicate policy_override backend is required.
- **Story work:** Assert the actual rule reason and final veto; expose/verify pre-veto model action if not already available in the chosen response. Fixture metadata “AI suppresses” is not scored proof. Use domain action names, not an invented universal ESCALATE enum.

#### SOC-09 — same-alert
- **Spec:** `soc/soc-09-same-alert.spec.ts`.
- **Exact probe:** Two POSTs to `http://127.0.0.1:8001/api/alert/analyze`, body `{alert_id:"PW-SELFDIAG-SOC-09"}`. Historical: unrecorded; current GET: 405.
- **Exists/mounted:** Yes. No backend required merely to accept a real alert.
- **Files/work:** Fix this spec to assert existence/type and equality of `recommendation.action/confidence` and `gae_scoring.factor_vector/action_probabilities`; arrange identical scorer AND contextual state.
- **Dependency:** Analyze writes decisions and referral uses live sequence/cross-category counts (triage.py:930 onward). Two mutating requests are not an invariant-state experiment. Use isolated state reset or an explicitly scoped deterministic scoring comparison; do not assert full pipeline determinism while context changes.

#### SOC-10 — rollback
- **Spec:** `soc/soc-10-rollback.spec.ts`.
- **Exact probe:** One POST `http://127.0.0.1:8001/api/learning/checkpoint` with the generic demo payload. Historical: unrecorded; current GET: 404.
- **Exists/mounted:** That alias is absent; native POST `/api/soc/checkpoint/create`, GET `/api/soc/checkpoint/list`, POST `/api/soc/checkpoint/rollback` are mounted through framework_router.py:483–515. List GET=200.
- **200 repair:** Change this spec to native create `{reason}` and rollback `{checkpoint_id}`; do not build another in-memory checkpoint store.
- **Story work/files:** Existing `backend/app/framework/checkpoint.py` persists μ/counts and restores them then freezes; returned restored_decision_count is metadata, not proof that all live counters/K/gates were restored. Verify an actual permitted learning update between snapshots and μ/count equality afterwards, plus intentional freeze. Full-state rollback would be a separate extension to this service with a defined state manifest.

### 1.3 S2P skipped specs (five)

#### S2P-01 — rule-said-no
- **Spec:** `s2p/s2p-01-rule-said-no.spec.ts`.
- **Exact probe:** POST `http://127.0.0.1:8002/api/s2p/score`; generic body omits amount/supplier_id and uses category demo. Historical: unrecorded; current GET: 405.
- **Exists/mounted:** `S2P/backend/app/routers/s2p.py:2109,2155`, main.py:352. Missing required fields imply schema 422; not POST-tested here.
- **200 repair/files:** Correct this spec's payload using valid invoice/category/supplier data; no new score endpoint. If the copper scenario is missing, extend S2P's existing preseed fixture loader, not production score validation.
- **Story work:** Assert ACCEPT and evidence for the actual contract exception. The typed score response is not itself a contract-clause narrative; connect the existing invoice insight/context evidence or add a traceable explanation projection in s2p.py only if necessary. Never hardcode a clause string to satisfy the test.

#### S2P-02 — day-zero
- **Spec:** `s2p/s2p-02-day-zero.spec.ts`.
- **Exact probe:** POST `http://127.0.0.1:8002/api/s2p/score`; same invalid generic body. Historical: unrecorded; current GET: 405.
- **Exists/mounted:** Same working POST contract; no missing scorer.
- **200 repair/files:** Fix the payload in this spec and assert `confidence > 0`, correct factor-vector length/names on a valid scoring result.
- **Story work:** Use an isolated fresh store or explicit day-zero snapshot; assert zero prior verified decisions before scoring. The shared live S2P stream observed 812 current decisions and cannot substantiate “first ever” without isolation. Do not clear the user's live preseed.

#### S2P-03 — paying-more
- **Spec:** `s2p/s2p-03-paying-more.spec.ts`.
- **Exact probe:** POST `http://127.0.0.1:8002/api/s2p/score`; same invalid generic body. Historical: unrecorded; current GET: 405.
- **Exists/mounted:** Existing score router, no new scoring endpoint needed for a valid request.
- **Files/work:** Fix this spec and S2P `scripts/preseed_demo_scenarios.py` fixture mapping as needed. `data/demo_fixtures/demo_container_context.json` is context (demurrage, working capital, asserted HOLD), not a ScoreRequest.
- **Story work:** Follow real context→factor derivation and explanation; assert HOLD plus the supported working-capital tradeoff. If score/insight does not consume that context, extend the existing s2p.py/insight integration rather than treating the fixture's expected action as an outcome.

#### S2P-07 — budget-strip
- **Spec:** `s2p/s2p-07-budget-strip.spec.ts`. Exact probe: **none**; permanent ROADMAP; historical status: none.
- **Exists/mounted:** V1's proposed GET `/api/self/investigation-budget` is absent (404). Shared POST `/api/investigation/investigate` is already mounted in S2P main.py:340 with default_budget=2.
- **Product work/files:** Production policy selection and telemetry must be integrated at S2P's investigation mount/evidence-provider boundary and a separately reviewed controller module, with safety constraints and rollback. Do not edit frozen SDK scorer/investigator merely for a demo.
- **Acceptance:** Allocated versus actually used reads, fixed-budget comparator, latency/quality/conservation measurements and provenance. Optional classifier-based budget support is not the experimental learned controller. Keep deferred until this is approved and measured.

#### S2P-09 — frozen-twin
- **Spec:** `s2p/s2p-09-frozen-twin.spec.ts`.
- **Exact probe:** GET `http://127.0.0.1:8002/api/s2p/learning/twin`. Historical: unrecorded; current: 404.
- **Exists/mounted:** Native GET `/api/s2p/learning/frozen-twin` is mounted via `backend/app/routers/s2p_demo_beats.py:175`, main.py:365; current 200.
- **200 repair/files:** Change the spec's URL; no new shared twin backend. Existing init operation is POST `/api/s2p/learning/twin/freeze` (documented by S2P preseed), subject to state/approval checks.
- **Story work:** Obtain verified paired decisions, not just `frozen_available`. Current `compared_decisions=0`, `delta_accuracy=null`; fallback can set frozen_available=true while using configuration geometry. Inspect evidence_tier/source, initialize real twin where required, and extend existing comparison projection only if time series are needed.

### 1.4 Purchasing and Trading skipped specs (five)

#### PUR-05 — two-stores
- **Spec:** `purchasing/pur-05-two-stores.spec.ts`.
- **Exact probe:** GET `http://127.0.0.1:8020/api/learning/frozen-twin`. Historical: unrecorded; current 404.
- **Exists/mounted:** Native GET `/api/purchasing/frozen-twin` and `/comparison`, POST `/freeze` already exist in SDK `apps/purchasing/backend/app/routers/purchasing_control.py:39–55`, mounted main.py:916.
- **200 repair/files:** Change this spec to native contract; initialize via existing freeze operation in authorized isolated setup. Status GET=200/uninitialized; comparison GET=404 is missing resource, not missing router.
- **Story work:** Service `services/purchasing_control.py` reports geometry drift/IKS, not two observed waste curves. Add measured paired outcome projection there only if supported by a same-context waste dataset; do not rename centroid drift as waste reduction.

#### PUR-06 — demand-limit
- **Spec:** `purchasing/pur-06-demand-limit.spec.ts`. Exact probe: **none**; permanent ROADMAP; historical status: none.
- **Exists/mounted:** Shared POST `/api/investigation/investigate` already mounted at Purchasing main.py:853; proposed GET `/api/self/investigation-trace` is 404.
- **Product work/files:** Reuse SDK `copilot_sdk/backend/investigation_router.py` contract without modifying that frozen file. Wire a concrete capacity/bottleneck evidence fixture through Purchasing main.py's existing provider and the order/detail UI.
- **Acceptance:** A real ordered `steps` trace identifies non-demand constraint with source evidence and final action. Rewrite permanent spec against the native POST plus display; endpoint presence alone does not prove the scenario.

#### TRD-02 — throttle
- **Spec:** `trading/trd-02-throttle.spec.ts`.
- **Exact probe:** GET `http://127.0.0.1:8010/api/self/regime-analytics`. Historical: unrecorded; current 404.
- **Exists/mounted:** Native GET `/api/trading/regime-analytics` returns 200; GET `/api/trading/regime/throttle` returns monitor state. Main.py:663 mounts analytics; regime_beats.py:90 exposes throttle.
- **200 repair/files:** Fix this spec to native routes; no greenfield regime engine. Use existing `services/regime_monitor.py`, `regime_scoring.py` and `routers/regime_beats.py` for fixture-driven transitions.
- **Story work:** Current break=false. Require a controlled break and before/after autonomy evidence; label observation_only honestly. Do not synthesize Hurst/tail-dependence statistics from correctness volatility as v1 proposes; use the actual market-data calculation and its availability flags.

#### TRD-04 — position-alone
- **Spec:** `trading/trd-04-position-alone.spec.ts`. Exact probe: **none**; permanent ROADMAP; historical status: none.
- **Exists/mounted:** Shared POST investigation mounted at Trading main.py:572; proposed GET `/api/self/investigation-trace` is 404.
- **Product work/files:** Reuse the investigator response; connect position-exposure evidence in Trading main.py's provider and its decision-detail UI. No replacement investigation engine.
- **Acceptance:** Ordered reads, changed factor evidence, action/margin and provenance from the same decision; authorize explicit replay semantics if the UI recomputes rather than retrieves a persisted trace. Rewrite permanent spec accordingly.

#### TRD-05 — cold-warm
- **Spec:** `trading/trd-05-cold-warm.spec.ts`. Exact probe: **none**; permanent ROADMAP; historical status: none.
- **Exists/mounted:** No dedicated comparison route found; v1's GET `/api/self/entrant-comparison` returned 404. Existing frozen geometry utilities are reusable, not a full entrant experiment.
- **Product work/files:** A new read-only comparison adapter under SDK `apps/trading/backend/app/routers/` and a paired evaluator service would be needed only after approving the study contract; mount in Trading main.py. Do not invent a route that the current spec supposedly calls.
- **Acceptance:** Same inputs/outcomes for a frozen initial scorer and learned scorer, explicit split/state isolation, coverage and uncertainty. Historical initial accuracy alone cannot estimate competitor catch-up time or causal moat.

### 1.5 DataOps skipped specs (four)

#### DO-04 — rule-wrong
- **Spec:** `dataops/do-04-rule-wrong.spec.ts`.
- **Exact probe:** GET `http://127.0.0.1:8030/api/self/rule-lifecycle`. Historical: unrecorded; current 404.
- **Exists/mounted:** Shared self-computation router is mounted; `/api/self/rule-genealogy` lists IDs, `/api/self/rule-lifecycle/{rule_id}` returns evolution/promotion (self_computation_router.py:508,514). Not an unmounted feature.
- **200 repair/files:** Fix spec to discover an ID then request its native lifecycle, or add a deliberate collection projection to that router if product UI needs it. Current genealogy is empty: rules=[], total=0.
- **Story work:** Seed genuine lifecycle records through the existing evolution state workflow. If persisted transition reasons/history are insufficient, extend their projection in `copilot_sdk/backend/self_computation_router.py`; do not fabricate promote→demote events from one promotion record.

#### DO-05 — llm-wrong
- **Spec:** `dataops/do-05-llm-wrong.spec.ts`.
- **Exact probe:** POST `http://127.0.0.1:8030/api/score` with category demo and no factors. Historical: unrecorded; current GET to score=405.
- **Exists/mounted:** Generic score exists. V1's proposed GET `/api/self/k14-comparison` is not called by the spec and returned 404.
- **200 repair/files:** Fix this spec's category/factors using the real domain contract. For the story, use the already mounted shared POST investigation response: `surface_action, final_action, action_changed, steps, contrast`.
- **Product work:** Supply real evidence through DataOps main.py's investigator provider; extend its UI projection if needed. File-placement fixture merely says APPROVE/REJECT. Compare real domain action indices mapped to names; a geometry surface prediction must not be labeled an actual LLM judgment without a recorded independent LLM label.

#### DO-07 — what-to-buy
- **Spec:** `dataops/do-07-what-to-buy.spec.ts`. Exact probe: **none**; permanent ROADMAP; historical status: none.
- **Exists/mounted:** Acquisition advice already shipped and mounted twice: native GET `/api/di/acquisition-advice`, plus `/api/dataops/di/acquisition-advice`; both live 200.
- **200 repair/files:** No product backend work required for availability. Rewrite this permanent spec to call the verified native path and assert populated recommendation/schema/provenance.
- **UI/evidence:** `apps/dataops/frontend/src/api.ts:369` and `components/AcquisitionAdvisorPanel.tsx`, rendered by `screens/InsightScreen.tsx:117`, already wire it. Test that existing UI; prospective ROI is an estimate, not realized causal gain.

#### DO-08 — ask-person
- **Spec:** `dataops/do-08-ask-person.spec.ts`. Exact probe: **none**; permanent ROADMAP; historical status: none.
- **Exists/mounted:** POST `/api/di/query` with `{question, context?}` already exists in di_router.py:272 and receives query_service in DataOps main.py:893,908. GET=405, not missing.
- **200 repair/files:** No remount needed; rewrite permanent spec with a supported question. POST success not tested in this read-only review; runtime dependency/data errors remain possible.
- **UI/evidence:** `api.ts:403`, `components/NLQueryPanel.tsx`, and DashboardScreen.tsx:286 already render answers, evidence and source attribution. Assert supported/insufficient cases honestly, not an invented prompt-integrator URL.

### 1.6 Platform and Machine skipped specs (seven)

#### PLAT-01 — clocks
- **Spec:** `platform/plat-01-clocks.spec.ts`. Exact probe: **none**; permanent CONCEPTUAL; historical status: none.
- **Exists/mounted:** No concepts API found; proposed GET `/api/platform/concepts/four-clocks` is 404, but no spec depends on it.
- **Product work/files:** None required for an API smoke test because there is no API story. If promoted to UI acceptance, create approved versioned editorial content in the chosen frontend and rewrite this spec against visible clocks/labels.
- **Decision:** Do not introduce a server just to convert a conceptual skip into a meaningless 200.

#### PLAT-03 — five-corrections
- **Spec:** `platform/plat-03-five-corrections.spec.ts`.
- **Exact probes:** GET `http://127.0.0.1:{8001,8002,8010,8020,8030}/api/fingerprint`; skip if any non-OK. Historical individual codes: unrecorded. Current SOC generic=200; S2P generic=404.
- **Exists/mounted:** SDK/SOC generic surfaces exist. S2P native `/api/s2p/insight/fingerprint` is mounted, but requires invoice_id (422 without, 200 with).
- **Files/work:** Fix this spec to explicit per-domain contracts if an invoice-level explanation is acceptable, with semantic labels. If the catalog needs earned domain weights across all five, extend `S2P/backend/app/routers/s2p_insight.py` and mount through main.py a consciously designed domain projection/compatibility route.
- **Acceptance:** The native S2P factor mapping is not equivalent to sigma/learned weight arrays. Do not add a no-argument alias to a required-argument handler. Current SOC weights are zero, so “five learned corrections” still needs data evidence after HTTP availability is fixed.

#### PLAT-05 — two-questions
- **Spec:** `platform/plat-05-two-questions.spec.ts`. Exact probe: **none**; permanent CONCEPTUAL; historical status: none.
- **Exists/mounted:** No current endpoint requirement. V1's concepts API is a proposed design choice, not a discovered contract.
- **Product work/files:** Approved K14 caption content and a UI/content test in the chosen frontend/spec if this is to become executable. No backend build required.
- **Acceptance:** Cite the specific copilot/sample/tier for each K14 number; do not generalize SOC's 86% or DataOps' 12% into a universal surface accuracy.

#### MACH-01 — through-machine
- **Spec:** `machine/mach-01-through-machine.spec.ts`.
- **Exact probe:** POST `http://127.0.0.1:8001/api/alert/analyze` with invented alert ID. Historical: unrecorded; current GET: 405.
- **Exists/mounted:** Analyze exists; ordered investigation is a different native POST `/api/soc/investigate` (triage.py:453) returning `single_pass, vld, investigation_trace`.
- **Files/work:** Correct fixture ID/body in this spec and use native investigation for the trace. If a production decision needs the trace attached, extend SOC triage/explanation projection with explicit mode/provenance; do not retrofit fake reads onto a single-pass response.
- **Acceptance:** Assert ordered trace and confidence from an actually executed investigation. Native SOC investigation is explicitly a read-only shadow; label it as such rather than claiming it produced the authoritative decision.

#### MACH-02 — reshape
- **Spec:** `machine/mach-02-reshape.spec.ts`.
- **Exact probe:** POST `http://127.0.0.1:8001/api/alert/analyze` with invented alert ID. Historical: unrecorded; current GET: 405.
- **Exists/mounted:** Same source and mount as SOC-02; no separate reshape/no-precedent backend.
- **Files/work:** Share a valid graph-backed no-precedent fixture/setup and typed response adapter with SOC-02; change this spec accordingly.
- **Acceptance:** Distinguish centroid novelty from historical similarity and use actual referral/escalation semantics. No reshape or parameter mutation may be inferred from a novel flag alone.

#### MACH-03 — parameter-moved
- **Spec:** `machine/mach-03-parameter-moved.spec.ts`.
- **Exact probe:** One POST `http://127.0.0.1:8001/api/alert/analyze` with invented alert ID; no second call or verified outcome. Historical: unrecorded; current GET: 405.
- **Exists/mounted:** Analyze and shadow investigation exist, but this does not establish a verified-outcome→K-only causal chain. Shared investigator reads K weights; it does not perform the learning update.
- **Product work/files:** Replace declarative `SDK/data/demo_fixtures/soc_recursion_k_delta.json` with reproducible input/outcome evidence. Instrument/wire the actual SOC verified-outcome and investigation integration in triage.py and its provider; inspect ownership of K before changing anything.
- **Acceptance:** Record K before/after, μ/σ and other routing inputs unchanged, same counterfactual input, different ordered reads and claimed action. Different alert profiles with preselected first factors are not evidence that K caused the difference. Keep blocked if production K-only update isolation is unavailable.

#### MACH-05 — retraction
- **Spec:** `machine/mach-05-retraction.spec.ts`. Exact probe: **none**; permanent CONCEPTUAL; historical status: none.
- **Exists/mounted:** No required API; absence of a concepts route is immaterial.
- **Product work/files:** Approved, versioned retraction content and a UI/content assertion if the catalog is to count this as an executable surface. Do not fabricate a dynamic measurement endpoint.
- **Acceptance:** Entries link to the actual withdrawn claim, reason, scope and replacement evidence. This is editorial governance, not a computed learning metric.

### 1.7 Consolidated delivery packages (merge by implementation, not scenario count)

These replace v1's 14 independent build orders. IDs in this table are the 26 currently skipped IDs only.
Restoring truthful assertions in the 30 existing passes is a separate cross-cutting dependency.

| Package | Unique skipped IDs | Reuse / remaining work | Estimated engineer-days |
|---|---|---|---:|
| A: SOC contracts + shared novelty/referral fixture | SOC-02, SOC-06, SOC-09, MACH-02 | Fix IDs/nesting, isolate deterministic state, validate existing novelty/referral | 1–2 |
| B: Existing checkpoint acceptance | SOC-10 | Native route adapter, verified mutation→restore test, scoped snapshot assertion | 0.5–1.5 |
| C: S2P score fixtures | S2P-01, S2P-02, S2P-03 | Valid schema, isolated cold state, genuine clause/container evidence | 1–3 |
| D: Native twins | S2P-09, PUR-05 | Correct paths/init/paired evidence; optional real series projection | 1–3 |
| E: Existing Trading regime | TRD-02 | Native route, controlled break and monitor/gate evidence | 0.5–1.5 |
| F: Existing DataOps DI | DO-07, DO-08 | Activate correct specs and test already-wired UI/service contracts | 0.5–1 |
| G: Fingerprint semantics | PLAT-03 | Domain adapter or new honest domain-level S2P projection | 0.5–1.5 |
| H: Investigation stories | MACH-01, MACH-03, DO-05, TRD-04, PUR-06 | Reuse native traces, evidence providers, provenance/UI and K-causality isolation | 3–6 |
| I: Rule lifecycle evidence | DO-04 | Genealogy→ID flow, state fixtures, missing history projection if needed | 0.5–2 |
| J: Paired entrant + pair correlation | TRD-05, SOC-05 | Reuse geometry/campaign services; design real paired evidence and negatives | 3–6 |
| K: Editorial surfaces | PLAT-01, PLAT-05, MACH-05 | Product/content decision, UI/content assertions; no mandatory backend API | 0.5–1.5 |
| L: Production adaptive budgets | S2P-07 | Safety-reviewed policy integration and telemetry; separate approval gate | 3–6+ |

Total planning range: **15.5–35.0+ engineer-days**, not a delivery commitment.
Contract/path-only edits may be quick; ranges include the missing story evidence and safe setup/cleanup.
The estimate does not include repair of every weak assertion in the 30 existing passes (allow another 2–4 engineer-days), broad regression investigation, external data acquisition, or research proving an effect that may not occur.
Some stories may legitimately remain unproven; do not tune fixtures/metrics or manufacture a positive effect to hit the pass target.
No product code is required merely to make DO-07's native GET available, mount DI again, expose Trading regime analytics, or recreate checkpoint/twin engines.

## Part 2: Revised Batch Plan and Dependencies

### 2.1 Batch sequence with non-duplicated accounting

| Batch | Scope and unique formerly skipped IDs | Count | Dependency / exit |
|---|---|---:|---|
| 0 | Baseline/contract test repairs; no claimed unskips | 0 | Preserve machine-readable skip annotations, isolate mutations, define evidence tiers |
| 1 | SOC-02/06/09/10; S2P-01/02/03/09; PUR-05; TRD-02; PLAT-03; DO-07/08 | 13 | Native paths, valid resources, controlled cold/twin/regime state; no “all pass” guarantee |
| 2 | MACH-01/02/03; DO-04/05; TRD-04; PUR-06 | 7 | Reuse Batch 1 no-precedent setup; real trace/K/lifecycle evidence and UI |
| 3 | SOC-05; TRD-05 | 2 | Paired experiments and campaign evidence; product contract approval |
| 4 | PLAT-01/05; MACH-05 | 3 | Decide editorial surface testing versus continued conceptual deferral |
| 5 | S2P-07 | 1 | Production policy/safety review, then telemetry; independent go/no-go |
| Total | Exactly the 26 historical skipped IDs, each once | 26 | 30 saved passes + 26 candidates = 56 catalog rows, not 56 verified stories |

MACH-02 shares Package A implementation but is counted only in Batch 2 execution; no double count.
Batch 1 “potentially executable” is not “13 stories demonstrated.”
If the ten permanent deferrals remain policy, a 56-pass target is impossible: at most 46 tests can execute.
Changing that policy requires explicit spec/content acceptance, not adding arbitrary JSON endpoints.

### 2.2 Required ordering and state isolation

1. Fix assertions and request schemas before diagnosing absent implementation from test results.
2. Load fixture entities plus required relationships via existing supported setup; check each ID resolves.
3. Capture real typed response fields before exposing optional compatibility aliases.
4. Freeze/initialize twins before generating paired verified outcomes; initialization after learning cannot retrospectively prove the intended baseline.
5. Isolate SOC simulate-failure, Purchasing pause, rollback, cold start and normal GREEN demonstrations from each other.
6. Prevent parallel demo tests from changing shared conservation/K/μ/referral history under deterministic tests.
7. Verify a controlled learning outcome changes the intended state; scoring alone need not update μ or K.
8. Restore only the explicitly snapshotted state and honor freeze side effects; checkpoint is not a transactional rollback of all graphs/audits.
9. Establish fixture provenance and expected negative controls before adding a trace UI.
10. Treat production adaptive control and entrant/correlation efficacy as measured acceptance, not inevitable outputs.

### 2.3 Test failure taxonomy

A future test run should retain JSON/JUnit annotations with method, URL, status, and safe error detail.
Use distinct statuses for route missing, method mismatch, invalid request, missing fixture resource, unavailable dependency, empty evidence, genuine assertion failure, and planned deferral.
Do not let a blanket `skip(!response.ok())` permanently mask invalid bodies or server regressions.
The current “auto-unskip when a feature ships” promise applies only to the correct method/path with a valid fixture and request.
Timeouts and transport errors may throw before a response exists; they are not HTTP 404.
No future report should label API-only smoke tests as verified UI renders.

## Part 3: Verification, Acceptance and Handoff

### 3.1 Source contract index

| Area | Primary read evidence | Correction established |
|---|---|---|
| SOC analyze | SOC backend/app/routers/triage.py:619,666,874,987,1490; models/schemas.py:33 | Required existing alert; nested recommendation, gae_scoring, referral and novelty |
| SOC novelty | SOC backend/app/services/soc_explainability.py:18 | Centroid novelty has similar_count; not historical case retrieval |
| SOC trace | SOC backend/app/routers/triage.py:453,559 | Read-only shadow investigation; oracle route explicitly not production/K-update truth |
| SOC checkpoints | SOC backend/app/routers/framework_router.py:483,507,515; framework/checkpoint.py | AGE snapshot/restore, optional counts, freeze; not new in-memory store |
| SOC twins | SOC backend/app/routers/soc_demo_beats.py:107 | Existing comparison surface; live drift contract must be respected |
| SOC correlation | SOC backend/app/routers/discoveries_router.py:77; services/cross_graph_discovery.py; triage.py:1132 | Existing discovery/campaign infrastructure |
| S2P score | S2P backend/app/routers/s2p.py:2109,2132,2155; models/responses.py:20 | amount/supplier_id required; typed factor_vector/names; held response possible |
| S2P fingerprint | S2P backend/app/routers/s2p_insight.py:129 | Invoice-specific query argument and factor mapping |
| S2P twin | S2P backend/app/routers/s2p_demo_beats.py:153,175; main.py:365 | Existing comparison; fallback/config geometry is not measured frozen accuracy |
| Purchasing twin | SDK apps/purchasing/backend/app/routers/purchasing_control.py:39; services/purchasing_control.py:161 | Existing persistent twin and explicit uninitialized state |
| Trading regime | SDK apps/trading/backend/app/routers/regime_analytics.py:21; regime_beats.py:90; services/regime_monitor.py | Real native analytics and monitor, not a new correctness-volatility proxy |
| DI | SDK copilot_sdk/backend/di_router.py:184,272; di/query_models.py:33; DataOps main.py:886,903 | Shipped mounted acquisition/query; native paths |
| DI UI | SDK apps/dataops/frontend/src/api.ts:369,403; components/AcquisitionAdvisorPanel.tsx; NLQueryPanel.tsx | Existing UI consumers; not browser-verified in this review |
| Lifecycle | SDK copilot_sdk/backend/self_computation_router.py:508,514 | List genealogy and per-rule lifecycle differ from collection path |
| Investigation | SDK copilot_sdk/backend/investigation_router.py:18,56; SDK app main.py mounts; S2P main.py:340 | Existing typed steps/contrast, K input, optional classifier budget |
| RL evidence | SDK experiments/vld/results/rl_ctrl2c_constrained_enrichment_summary.md | S2P safe λ=0, SOC selected λ=1; no production uplift claim |

### 3.2 Review checklist and unresolved verification

| Check | Outcome |
|---|---|
| Three repo session prechecks | Read |
| v1 and saved report/list output | Read; 30/26/0 verified as historical totals |
| SOC endpoint map | Read; aliases corroborated by live/source evidence |
| MAP DI shipping status | Actual v5.228 file located; R27–R30 corroborate implementation |
| All 26 historical skipped specs | Contract and status-source audit in Part 1 |
| All 14 v1 feature premises | Classified with source evidence in Part 0 |
| Requested 23 live probes | Completed as GET; status ledger above |
| Additional 19 native probes | Completed; partial/empty evidence preserved |
| Five OpenAPI probes | Trading succeeded; four timed out, not missing-route evidence |
| POST feature execution | Not performed; read-only scope |
| Browser render validation | Not performed; source inspection only |
| Playwright rerun | Not performed; suite contains mutations |
| Source/spec edits | None |
| Corrected design | This document; only future implementation recommendations |
| Exact historical skip HTTP codes | Unavailable from supplied text artifacts; not fabricated |
| Live “all 56 stories” claim | Not established |

### 3.3 Acceptance gates for the next implementation task

- Approve whether catalog assertions may adapt to native domain semantics or require new compatibility contracts.
- Keep passing smoke tests distinct from scenario acceptance; strengthen both skipped and passing stories.
- For every scenario, require the actual input fixture, called method/path, real typed fields, evidence provenance, and at least one negative control where a causal claim is made.
- For every mutable test, specify setup, isolation, cleanup, and which state remains append-only.
- Use observed null/empty/insufficient states without forcing fake results.
- For S2P fingerprint, decide invoice explanation versus earned domain fingerprint before coding.
- For twin/waste, compare against verified shared outcomes; a drift number is not an accuracy or dollar gain.
- For K14, distinguish an LLM label from a geometry-derived surface prediction and mark planted simulation.
- For K-routing, verify only K changed; do not substitute different input scenarios for a causal test.
- For ROADMAP/CONCEPTUAL rows, explicitly revise the deferral decision before counting an unskip.
- For adaptive budgets, preserve safety gates and frozen SDK files unless separately authorized; experimental deployability does not establish production integration.
- Rerun isolated tests and UI checks only in a subsequent authorized implementation/validation task.

### 3.4 Preservation evidence

Frozen file SHA-256 prefixes read during this review:

| SDK file | Prefix |
|---|---|
| copilot_sdk/scoring/investigation.py | 3441dcbd |
| copilot_sdk/backend/investigation_router.py | 08f4df7a |
| copilot_sdk/scoring/scorer.py | 24ac9e49 |

V1 SHA-256: `70872d25e4296a4f664fa2e4ce1bf2b3d3a605778028297c51a3b0d8f3231ef3`.
V1 is preserved.
This review does not authorize any of the future source/spec changes listed above.

### Changelog v1 → v2

Added verification evidence and a complete 26-spec contract ledger; retained the correct historical 30-pass list.
Removed greenfield build orders for already-mounted DI, checkpoint, twin, regime and investigation capabilities.
Separated request/path bugs, missing resources, empty evidence and genuine product gaps.
Corrected S2P fingerprint semantics, SOC nested scoring fields, fixture execution claims and SOC's RL λ=0 safety claim.
Replaced the inconsistent batch arithmetic with a 26-ID, non-duplicated plan and explicitly uncertain effort ranges.
No new pass count or UI readiness is claimed.
