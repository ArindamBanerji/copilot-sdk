# Purchasing Backend True State Diagnostic 05

Date: 2026-06-05
Model: gpt-5.3
Task Type: Diagnostic document creation only. No source code changes.
Repo: copilot-sdk
Diagnostic Scope: Purchasing backend app, tests, synthetic generator, and shared SDK backend router contribution.
Prior Diagnostics Read: `sdk_backend_endpoint_map_diagnostic_02.md` found and used. Purchasing-related planning docs found: `purchasing_backend_v2.md`, `purchasing_frontend_v2_rebuild.md`, `purchasing_preset_plan.md`, `trading_purchasing_backends.md`.

## Executive Summary

* Overall Purchasing backend state: PARTIAL / SDK-ROUTED.
* Highest-confidence findings: Purchasing has app-local context/evidence/graph/evolution endpoints and registers SDK scoring, transfer, evolution, conservation, and self-computation routers from `main.py`. No app-local routes were found for QuickBooks/QBO, spend dashboard, three-way match, order queue, verify workflow, PAR intelligence, supplier scorecard, or named trust-analysis APIs.
* P64 synthetic data verdict: SUPPLEMENT. The generator embeds supplier behavior and order patterns, but archetype names/counts do not match the required PD archetype list.
* P66-P75 implementation state summary: P67 is mostly present at scoring factor/preset level; P72 is partially covered by SDK conservation and evidence endpoints; P74/P75 have IKS/evidence primitives but no named scorecard/trust endpoint; P66/P68/P69/P70/P71/P73 are FULL unless later frontend/domain code outside inspected backend changes the scope.
* Biggest ambiguity: Whether Purchasing MAP items expect API layer only or complete product-specific workflows and UI wiring. This diagnostic only inspected backend code/tests/generator.
* Recommended next prompt: MAP queue update that drops or narrows P67, converts P72/P74/P75 to supplement prompts, and keeps P66/P68/P69/P70/P71/P73 as full implementation prompts.

## Path Resolution

* CLAUDE_SDK value: `C:\Users\baner\CopyFolder\IOT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
* Repo path used: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
* Purchasing backend path: `apps\purchasing\backend`
* Purchasing app path: `apps\purchasing\backend\app`
* Purchasing main.py path: `apps\purchasing\backend\app\main.py`
* test_purchasing_backend.py path: `apps\purchasing\backend\tests\test_purchasing_backend.py`
* purchasing_synthetic.py path: `apps\purchasing\backend\generators\purchasing_synthetic.py`
* SDK backend path: `copilot_sdk\backend`
* Prior SDK diagnostic found: YES

## CLAUDE.md Relevant Notes

* Do not use git unless explicitly requested.
* Treat docs as aspirational until validated against code.
* Prefer code/tests over planning docs and cite file/line evidence.
* This task explicitly forbids tests and source edits, so verification is source inspection only.

## Part 1 - Purchasing Backend File Tree and main.py

### File tree

```text
__init__.py (0.1KB)
context_router.py (9.3KB)
data_helpers.py (1.7KB) TODO_OR_STUB_SIGNAL_COUNT=2
evolution\__init__.py (0.3KB)
evolution\evolver_config.py (3.5KB)
graph_contract.py (1.2KB)
graph_status.py (13.1KB)
main.py (13.8KB) TODO_OR_STUB_SIGNAL_COUNT=7
routers\evidence.py (11.5KB) TODO_OR_STUB_SIGNAL_COUNT=4
seed_graph.py (6.1KB)
```

### main.py router registrations

| Router / Factory | Prefix | Tags | Source | Evidence |
| ---------------- | ------ | ---- | ------ | -------- |
| `create_scoring_router(...)` | `/api` | SDK scoring router tags | `copilot_sdk.backend` | `main.py` lines 33-37 import SDK factories; lines 339-346 include scoring router with `prefix="/api"`. |
| `create_transfer_router(scorer_proxy)` | factory-defined | SDK transfer router tags | `copilot_sdk.backend.transfer_router` | `main.py` line 32 imports; line 347 includes. |
| `create_evolution_router(...)` | factory-defined | SDK evolution router tags | `copilot_sdk.backend` | `main.py` lines 348-356 include with `domain=DOMAIN` and Purchasing variant provider. |
| `create_conservation_router(...)` | `/api` | SDK conservation router tags | `copilot_sdk.backend` | `main.py` lines 359-365 include conservation router with `prefix="/api"`. |
| `mount_self_computation_router(...)` | `/api/self` | SDK self-computation | `copilot_sdk.backend` | `main.py` line 366 mounts self-computation router. |
| `context_router_module.router` | `/api/context` | `["context"]` | `app/context_router.py` | `main.py` line 368 includes app-local context router. |
| `create_evidence_router(scorer_proxy)` | `/api/purchasing` | `["purchasing-evidence"]` | `app/routers/evidence.py` | `main.py` line 369 includes evidence router; evidence router line 21 defines prefix/tags. |
| `purchasing_graph_status_router` | `/api/purchasing/graph` | `["purchasing-graph"]` | `app/graph_status.py` | `main.py` line 370 includes; `graph_status.py` line 30 defines prefix/tags. |

### SDK router registration implications

* create_conservation_router registered: YES.
* create_scoring_router registered: YES.
* create_evolution_router registered: YES.
* create_transfer_router registered: YES.
* mount_self_computation_router registered: YES.
* Purchasing gets `/conservation` through SDK: YES, via `/api/conservation/status` and `/api/conservation/what-if` per prior SDK diagnostic and `main.py` prefix evidence.
* Purchasing gets `/iks` through SDK: PARTIAL. No standalone `/iks` or `/iks-trend` exists in prior SDK diagnostic; IKS appears embedded in scoring trajectory/evidence/self-computation.

## Part 2 - test_purchasing_backend.py Coverage

### Test function inventory

| Test Function | Apparent Coverage | Endpoint(s) | Mocked? | Evidence |
| ------------- | ----------------- | ----------- | ------- | -------- |
| `test_health`, `test_api_health_returns_phase_alpha_and_engine` | root health and SDK health | `/health`, `/api/health` | Real TestClient app | Test lines 70, 82. |
| `test_today_summary`, `test_items_list`, `test_items_enhanced_fields`, `test_waste_history_*`, `test_weather` | app-local purchasing context | `/api/context/*` | fixture data files | Test lines 93-156. |
| `test_order_metadata_*` | order metadata persistence in context router | `/api/context/order-metadata` | temp data in some tests | Test lines 164-215. |
| `test_seed_v2_exists`, startup path tests | seed DB initialization and path resolution | `/health` startup checks | temp dirs and monkeypatch env | Test lines 221-308. |
| `test_analytics`, `test_analytics_consistent_with_seed_v2`, `test_similar_orders`, `test_v2_endpoints_use_temp_data` | cached analytics and similarity | `/api/context/analytics`, `/api/context/similar` | temp fixture data in places | Test lines 314-479. |
| `test_item_profile*` | item profile and evolution rule matching | `/api/context/item/{name}/profile` | fresh DB variant case | Test lines 499-539. |
| `test_score_via_sdk_router`, `test_learn_returns_reward`, `test_fingerprint` | SDK scoring/learning/fingerprint | `/api/score`, `/api/learn`, `/api/fingerprint` | Real TestClient app | Helpers at lines 53 and 62; tests lines 547, 558, 764. |
| `test_conservation_status_returns_live_counts`, `test_in_memory_scoring_and_conservation_share_proxy_store` | SDK conservation status | `/api/conservation/status` | in-memory DB in one test | Test lines 569-599. |
| `test_self_computation_*` | SDK self-computation endpoints | `/api/self/centroid-history`, `/api/self/accuracy-by-category`, `/api/self/decisions`, `/api/self/audit-trail` | Real TestClient app | Test lines 607-644. |
| `test_graph_store_count_*` | graph store count helpers | no HTTP endpoint | temp SQLite graph store | Test lines 650-671. |
| `test_evolution_variants*` | SDK evolution variants with Purchasing config/events | `/api/evolution/variants` | fixture/fresh DB variants | Test lines 698-757. |

### Endpoint coverage summary

Tested endpoint paths observed:

* `/health`
* `/api/health`
* `/api/context/today-summary`
* `/api/context/items`
* `/api/context/waste-history/{item}`
* `/api/context/weather`
* `/api/context/order-metadata`
* `/api/context/analytics`
* `/api/context/similar`
* `/api/context/item/{name}/profile`
* `/api/score`
* `/api/learn`
* `/api/conservation/status`
* `/api/self/centroid-history`
* `/api/self/accuracy-by-category`
* `/api/self/decisions`
* `/api/self/audit-trail`
* `/api/evolution/variants`
* `/api/fingerprint`

### Fixture/mock setup

* Tests use `fastapi.testclient.TestClient` from line 7.
* Startup and isolation tests instantiate `create_app(...)` with temp DB paths and `demo_bundle_path=False` at lines 247, 267, 278, 294, 307, 538, 596, and 732.
* Monkeypatch usage is limited to environment/path behavior at lines 273, 287, and 302.
* No heavy service mocking was observed in the fixture/mocking scan.

### Coverage implications

* Does test suite prove only health/evidence endpoints? NO. It proves context, SDK scoring/learn/fingerprint, SDK conservation, SDK self-computation, SDK evolution variants, and graph-store helpers.
* Does it prove spend/match/queue/verify/par/supplier/IKS/trust endpoints? NO. No test calls were observed for `/purchasing/spend`, `/purchasing/match`, `/purchasing/queue`, `/purchasing/verify`, PAR, supplier scorecard, standalone `/iks`, `/trust`, or `/signal-trust`.
* What does 43 tests actually mean? The 43 tests cover existing context/SDK/evolution/graph behavior, not the full P66-P75 product surface.

## Part 3 - Router and Service Inventory for P66-P75

### Endpoint definitions found

| File | Method | Path | Function | Feature Area | Evidence |
| ---- | ------ | ---- | -------- | ------------ | -------- |
| `app/context_router.py` | GET | `/today-summary` | `today_summary` | context | line 144 |
| `app/context_router.py` | GET | `/items` | `items` | item catalog | line 154 |
| `app/context_router.py` | GET | `/waste-history/{item}` | `waste_history` | waste context | line 171 |
| `app/context_router.py` | GET | `/weather` | `weather` | weather context | line 179 |
| `app/context_router.py` | POST | `/order-metadata` | `save_order_metadata` | order metadata | line 184 |
| `app/context_router.py` | GET | `/order-metadata` | `get_order_metadata` | order metadata | line 198 |
| `app/context_router.py` | GET | `/analytics` | `analytics` | cached analytics/spend-adjacent | line 203 |
| `app/context_router.py` | GET | `/similar` | `similar_orders` | similarity / factor context | line 221 |
| `app/context_router.py` | GET | `/item/{name}/profile` | `item_profile` | item profile | line 275 |
| `app/graph_status.py` | GET | `/api/purchasing/graph/status` | graph status endpoint | graph health | line 340 |
| `app/routers/evidence.py` | GET | `/api/purchasing/evidence/summary` | `evidence_summary` | evidence / IKS summary | lines 21, 23 |
| `app/routers/evidence.py` | GET | `/api/purchasing/evidence/decisions` | `evidence_decisions` | verified decision evidence | line 52 |
| `app/routers/evidence.py` | GET | `/api/purchasing/evidence/audit-trail` | `audit_trail` | audit evidence | line 69 |
| `app/routers/evidence.py` | GET | `/api/purchasing/evidence/conservation-proof` | `conservation_proof` | conservation proof | line 95 |
| `app/routers/evidence.py` | GET | `/api/purchasing/health` | `purchasing_health` | purchasing evidence health | line 124 |
| `app/routers/evidence.py` | GET | `/api/purchasing/status` | `purchasing_status` | purchasing evidence status | line 140 |

### Feature signal inventory

| Feature Area | Files / Symbols Found | Routed? | Evidence |
| ------------ | --------------------- | ------: | -------- |
| QBO / QuickBooks connector | No `qbo` or `quickbooks` feature signals found in app scan. | NO | Feature scan returned no QBO/QuickBooks route or service. |
| 7th factor / price_memory_index | `main.py` factor list, `context_router.py` `_FACTOR_NAMES` and similarity params, `copilot_sdk/scoring/presets/purchasing.py`. | YES through SDK scoring/context | `main.py` lines 56-57; `context_router.py` lines 22-30, 229-230; preset lines 38-47. |
| spend dashboard | `context_router.py` `/analytics` has cached analytics sections but no spend-dashboard route. | PARTIAL | `context_router.py` lines 203-218 returns analytics cache/defaults. |
| three-way match | No route/service found. | NO | Feature scan found only `_rule_matches_item`; no invoice/three-way match. |
| order queue | No queue route/service found. | NO | Feature scan found no queue route. |
| verify / override / hash-chain | Evidence audit uses fixture integrity and `hash_chain_available: False`; SDK `/api/learn` verifies learning outcomes, not a Purchasing verify workflow. | PARTIAL / NO product route | `evidence.py` lines 69-93; tests helper posts `/api/learn` at lines 62-66. |
| conservation / auto-approve | SDK conservation registered and evidence conservation proof exists; no auto-approve route found. | PARTIAL | `main.py` lines 359-365; `evidence.py` lines 95-121. |
| par intelligence | `par_level` appears in item fallback/catalog fields only. | NO product route | `context_router.py` lines 158-166. |
| IKS scorecard | Evidence summary exposes `iks_score`, proof exposes checkpoint `iks`; no standalone IKS scorecard route. | PARTIAL | `evidence.py` lines 35-37, 104-115, 205-209. |
| trust analysis | No `/trust` or `/signal-trust` route found. | NO | App scan found no trust endpoint. |
| commodity decomposition | Synthetic generator has `commodity_bulk`; app routes do not expose commodity decomposition. | NO product route | `purchasing_synthetic.py` lines 34, 77, 186. |
| supplier scorecard | `data_helpers.py` loads suppliers; no supplier scorecard endpoint found. | NO | `data_helpers.py` lines 22-26, 42-57. |

## Part 4 - SDK Backend Contribution

* Prior SDK diagnostic used: YES.
* Minimal SDK scan run: NO, because prior SDK diagnostic 02 was present and `main.py` registration was inspected directly.
* SDK conservation endpoint exposed: YES, via registered SDK conservation router.
* SDK scoring/IKS endpoint exposed: PARTIAL. `/api/score`, `/api/learn`, `/api/fingerprint`, `/api/trajectory` primitives exist per prior diagnostic; no standalone `/iks`.
* SDK trust/signal-trust endpoint exposed: NO named trust endpoint in prior SDK diagnostic.
* Purchasing registers the required SDK routers: PARTIAL / YES for generic SDK routers. It registers scoring, transfer, evolution, conservation, and self-computation.
* P72 implication: SUPPLEMENT. API primitives exist, but Purchasing-specific full conservation/auto-approve product workflow is not proven.
* P74 implication: SUPPLEMENT. Evidence endpoints expose `iks_score` and checkpoint IKS; no scorecard route/product shape was found.
* P75 implication: FULL or SUPPLEMENT depending MAP scope. No named trust endpoint exists; scoring/evidence primitives may support a supplement but do not satisfy a trust-analysis API by themselves.

## Part 5 - P64 purchasing_synthetic.py Archetype Match

### Archetype definitions found

| Archetype | Count | Behavioral Meaning | Matches PD Requirement? | Evidence |
| --------- | ----: | ------------------ | ----------------------: | -------- |
| `reliable_premium` | 6 | High OTIF, premium price, stable | PARTIAL for `gold_reliable` | `ARCHETYPE_COUNTS` lines 29-40; profile line 72. |
| `budget_volatile` | 5 | Low price, volatile service | NO direct required match | lines 30, 73. |
| `seasonal_specialist` | 4 | Seasonal performance | PARTIAL for `seasonal_premium`, wrong count/name | lines 31, 74, 183. |
| `local_organic` | 4 | Weather-sensitive local sourcing | NO direct required match | lines 32, 75, 184. |
| `national_distributor` | 5 | Broad catalog/stable logistics | NO direct required match | lines 33, 76, 185. |
| `commodity_bulk` | 4 | Bulk/shelf-stable pricing | PARTIAL for `commodity_linked`, wrong count/name | lines 34, 77, 186. |
| `specialty_dairy` | 3 | Dairy/cold chain | NO direct required match | lines 35, 78, 187. |
| `quick_turn` | 4 | Fast replenishment | NO direct required match | lines 36, 79, 188. |
| `relationship_legacy` | 3 | Relationship can mask deteriorating economics | PARTIAL for `trust_trap`, wrong count/name | lines 37, 80, 189. |
| `new_vendor` | 4 | Limited history | PARTIAL for `new_unproven`, wrong count/name | lines 38, 81, 190. |
| `declining_quality` | 4 | Quality trend declines | PARTIAL for `declining`, wrong count/name | lines 39, 82, 191. |
| `inconsistent_star` | 4 | Upside but inconsistent execution | NO direct required match | lines 40, 83, 192. |

### Required PD archetype coverage

| Required Behavioral Archetype | Required Count | Present? | Actual Name(s) / Evidence | Gap |
| ----------------------------- | -------------: | -------: | ------------------------- | --- |
| `gold_reliable` | 5 | PARTIAL | `reliable_premium` count 6 | Name/count mismatch. |
| `seasonal_premium` | 2 | PARTIAL | `seasonal_specialist` count 4 | Name/count mismatch; seasonal behavior exists. |
| `trust_trap` | 2 | PARTIAL | `relationship_legacy` count 3 | Semantic partial; no explicit `trust_trap` flag. |
| `declining` | 2 | PARTIAL | `declining_quality` count 4 and longitudinal Greenleaf degradation | Name/count mismatch. |
| `behavioral_duplicates` | 6 | NO | No explicit duplicate archetype. | Missing. |
| `commodity_linked` | 3 | PARTIAL | `commodity_bulk` count 4 | No explicit commodity correlation/decomposition fields found. |
| `price_memory` | 3 | PARTIAL | `price_memory_index` factor and supplier PUR-SUP-007 low price memory | No explicit archetype/count. |
| `format_changer` | 1 | NO | No `format_changer` or format-change marker found. | Missing. |
| `new_unproven` | 3 | PARTIAL | `new_vendor` count 4 | Name/count mismatch. |
| `high_frequency_basic` | 3 | NO | High order counts exist in profiles, but no explicit archetype. | Missing. |

### Behavioral pattern embedding

* Seasonal premium behavior: PARTIAL. `seasonal_specialist` profile has trend `"seasonal"` and notes say best performance during seasonal demand windows.
* Trust trap behavior: PARTIAL. `relationship_legacy` notes say long relationship can mask deteriorating economics, but supplier records do not include explicit reputation/trust trap fields.
* Declining supplier behavior: YES/PARTIAL. `declining_quality` profile exists, PUR-SUP-009 is forced to declining, and `_apply_longitudinal_patterns` lowers Greenleaf outcomes in the second half of its history.
* Behavioral duplicate behavior: NOT FOUND.
* Commodity-linked behavior: PARTIAL. `commodity_bulk` exists, but no commodity index/correlation field was observed.
* Price memory behavior: YES/PARTIAL. `price_memory_index` is generated from supplier price index, and PUR-SUP-007 forces low price memory.
* Format changer behavior: NOT FOUND.
* Par/spend behavior: PARTIAL. Orders include total values/items and app catalog has `par_level`, but no PAR intelligence behavior was found.
* Evidence: `purchasing_synthetic.py` lines 29-40, 72-83, 143-172, 197-274, 318-348, 352-402, 420-429.

### Supplier record structure

Supplier records include `supplier_id`, `name`, `archetype`, `categories`, `primary_category`, `otif_score`, `avg_order_value`, `price_index`, `lead_time_days`, `waste_rate`, `order_count_90d`, `exception_rate`, `payment_terms`, `quality_score`, `recent_trend`, `years_active`, `min_order_value`, `delivery_window`, and `notes` at `purchasing_synthetic.py` lines 143-172.

### P64 Verdict

* Verdict: SUPPLEMENT.
* Remaining effort: 1-1.5d.
* Rationale: The generator is behavioral and useful, but it does not directly implement the required archetype names/counts or all required behavioral markers.

## Final MAP Verdict Table

| Prompt                    | Verdict | Remaining Effort | Likely Actual Files | Key Evidence | Next Action |
| ------------------------- | ------- | ---------------- | ------------------- | ------------ | ----------- |
| P64 PUR-SYNTH-DATA        | SUPPLEMENT | 1-1.5d | `apps/purchasing/backend/generators/purchasing_synthetic.py` | Behavioral generator exists, but required archetypes mismatch. | Supplement implementation. |
| P66 PUR-QBO-CONNECTOR     | FULL | 2-3d | No obvious file found | No QBO/QuickBooks routes/services in app feature scan. | Full implementation prompt. |
| P67 PUR-FACTORS-7         | DROP / SUPPLEMENT | 0-0.5d | `app/main.py`, `app/context_router.py`, `copilot_sdk/scoring/presets/purchasing.py` | Seven factors include `price_memory_index`; SDK score/fingerprint tests cover factor set. | Drop if factor presence is enough; supplement if factor derivation needs product logic. |
| P68 PUR-SPEND-DASH        | FULL | 1.5-2d | `app/context_router.py` only has `/analytics` | No `/spend` route; analytics cache is generic. | Full implementation prompt. |
| P69 PUR-MATCH-ENGINE      | FULL | 2d | No obvious file found | No invoice/three-way match routes/services. | Full implementation prompt. |
| P70 PUR-ORDER-QUEUE       | FULL | 1.5-2d | No obvious file found | No queue route/service found. | Full implementation prompt. |
| P71 PUR-VERIFY            | FULL / SUPPLEMENT | 1-2d | `routers/evidence.py`, SDK `/api/learn` | Evidence audit has fixture integrity and no hash chain; SDK learn exists but no Purchasing verify workflow. | Implementation prompt focused on verify/audit workflow. |
| P72 PUR-CONSERVATION-FULL | SUPPLEMENT | 0.5-1d | `app/main.py`, SDK conservation router, `routers/evidence.py` | SDK conservation registered; evidence conservation proof exists. | Supplement domain-specific conservation/auto-approve needs. |
| P73 PUR-PAR-INTELLIGENCE  | FULL | 1.5-2d | `app/context_router.py` item `par_level` only | No PAR route/service; `par_level` appears as catalog field. | Full implementation prompt. |
| P74 PUR-IKS-SCORECARD     | SUPPLEMENT | 1d | `routers/evidence.py`, SDK scoring/self-computation | `iks_score` embedded in evidence; no standalone IKS scorecard endpoint. | Supplement endpoint/product shape. |
| P75 PUR-TRUST-ANALYSIS    | FULL / SUPPLEMENT | 1-2d | SDK scoring/evidence primitives only | No `/trust` or `/signal-trust` route found. | Deeper prompt or implementation supplement for trust API. |

## Diagnostic Limitations

* This diagnostic does not validate runtime behavior.
* This diagnostic does not run tests.
* This diagnostic does not prove frontend/UI implementation.
* This diagnostic does not prove endpoint behavior beyond source/test inspection.
* DROP verdict means implementation/API layer appears covered enough to remove or reduce a MAP item, not that E2E validation passed.

## Recommended Next Step

Run a MAP queue update: mark P66, P68, P69, P70, and P73 as FULL; convert P64, P71, P72, P74, and P75 into narrower supplement prompts; drop or shrink P67 depending whether the MAP requires only the seventh factor to exist or also requires richer price-memory derivation.
