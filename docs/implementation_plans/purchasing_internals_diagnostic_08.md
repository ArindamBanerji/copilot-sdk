# Purchasing Internals Diagnostic 08

Date: 2026-06-05  
Model: gpt-5.3  
Task Type: Diagnostic document creation only. No source code changes.  
Repo: copilot-sdk  
Diagnostic Scope: Purchasing `context_router.py`, AgentEvolver config, TODO/stub/hash-chain context, and graph status layer.  
Prior Diagnostics Read: `purchasing_backend_true_state_diagnostic_05.md`, `sdk_backend_endpoint_map_diagnostic_02.md`, plus Purchasing-related implementation plan names discovered under `docs/implementation_plans`.

## Executive Summary

* Overall verdict: Purchasing internals are PARTIAL. Context and evidence APIs exist, but they are cached/static-data backed and do not complete spend dashboard, PAR learning, trust analysis, or verification/hash-chain workflows.
* P68 spend-dashboard update: SUPPLEMENT. `/api/context/analytics` returns spend-adjacent cost, category, waste, event, AE impact, and portfolio fields from `analytics_cache.json`, but no spend-dashboard-specific vendor/supplier totals, budget/savings-vs-budget, or live aggregation route was found.
* P71 verify/hash-chain update: widen to SUPPLEMENT 2d. Evidence audit explicitly returns `hash_chain_available: False`, `hash: None`, `previous_hash: None`, and `source: fixture`.
* P73 par-intelligence update: SUPPLEMENT. `/api/context/items` exposes `par_level` from `items.json`/fallback, but no learning/update logic or PAR recommendation endpoint was found.
* P75 trust-analysis update: FULL/SUPPLEMENT remains. Evidence and scoring primitives exist, but no Purchasing trust-analysis endpoint or DK/trust-trap logic was found.
* Purchasing AE verdict: SUPPLEMENT. Configured variants are real but narrow: waste threshold and lead-time buffer only.
* Biggest remaining ambiguity: whether MAP scope accepts cached demo analytics as sufficient API scaffolding or requires production data integration and frontend contract.
* Recommended next prompt: targeted SUPPLEMENT implementation for P71 hash-chain verification and P68 analytics/spend API contract, then P73/P75 supplements.

## Path Resolution

* CLAUDE_SDK value: `C:\Users\baner\CopyFolder\IOT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
* Repo path used: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
* context_router.py path: `apps/purchasing/backend/app/context_router.py`
* evolution **init**.py path: `apps/purchasing/backend/app/evolution/__init__.py`
* evolution evolver_config.py path: `apps/purchasing/backend/app/evolution/evolver_config.py`
* main.py path: `apps/purchasing/backend/app/main.py`
* evidence.py path: `apps/purchasing/backend/app/routers/evidence.py`
* data_helpers.py path: `apps/purchasing/backend/app/data_helpers.py`
* graph_status.py path: `apps/purchasing/backend/app/graph_status.py`
* Report path: `docs/implementation_plans/purchasing_internals_diagnostic_08.md`
* Prior Diag 05 found: YES
* Prior SDK Diag 02 found: YES

## CLAUDE.md Relevant Notes

* Do not use git directly.
* Docs are aspirational until proven in code.
* Cite file and line for behavioral claims.
* Code and tests beat docs; this task forbids tests and source edits, so evidence is source inspection only.

## Part 1 — context_router.py

### Endpoint inventory

| Method | Path | Function | Purpose | Evidence |
| ------ | ---- | -------- | ------- | -------- |
| GET | `/today-summary` | `today_summary` | Date, day of week, weather, events | `context_router.py:144-151` |
| GET | `/items` | `items` | Static item catalog with par/supplier lead time fields | `context_router.py:154-168` |
| GET | `/waste-history/{item}` | `waste_history` | Waste history by item | `context_router.py:171-176` |
| GET | `/weather` | `weather` | Cached/deterministic weather context | `context_router.py:179-181` |
| POST | `/order-metadata` | `save_order_metadata` | Persist order metadata JSON by decision_id | `context_router.py:184-195` |
| GET | `/order-metadata` | `get_order_metadata` | Return order metadata JSON | `context_router.py:198-200` |
| GET | `/analytics` | `analytics` | Cached analytics payload | `context_router.py:203-218` |
| GET | `/similar` | `similar_orders` | Cosine similarity over seven purchasing factors | `context_router.py:221-272` |
| GET | `/item/{name}/profile` | `item_profile` | Item profile, waste history, matched AE rules | `context_router.py:275-301` |

### /analytics response shape

`/analytics` loads `analytics_cache.json` through `_load_data_json` and otherwise returns a default object with:

* `source`
* `contrast_card`
* `counterfactual`
* `category_accuracy`
* `day_of_week`
* `event_impact`
* `waste_cost_analysis`
* `ae_impact`
* `portfolio_summary`

Evidence: `context_router.py:203-218`. The inspected cache is generated from `purchasing_seed_v2.json` and contains cost/savings-adjacent fields including `dollars_saved`, category `total_cost_dollars`, `waste_cost_analysis`, `ae_impact.estimated_savings_from_promoted_rules`, and `portfolio_summary.total_cost` at `analytics_cache.json:1-196`.

### Spend-dashboard-adjacent fields

| Field / Signal | Present? | Evidence | P68 Impact |
| -------------- | -------: | -------- | ---------- |
| spend_by_category | NO | No `spend_by_category` match in app scan; `/analytics` has `category_accuracy` instead at `context_router.py:211`. | Keeps P68 from DROP. |
| vendor_totals | NO | No `vendor_totals` match in app scan. | Gap. |
| exception_rate_by_vendor | NO | No `exception_rate_by_vendor` match in app scan. | Gap. |
| savings_vs_budget | NO | No `savings_vs_budget` match in app scan. | Gap. |
| category spend | PARTIAL | Cache category rows include `total_cost_dollars`, e.g. `analytics_cache.json:43`, `51`, `59`. | Spend-adjacent scaffold. |
| supplier/vendor totals | NO | `items.json` has suppliers, but `/analytics` does not aggregate supplier/vendor totals. | Gap. |
| budget or savings fields | PARTIAL | `counterfactual.dollars_saved` at `analytics_cache.json:33`; `estimated_savings_from_promoted_rules` at `analytics_cache.json:186`; no budget field. | Scaffold only. |
| other spend-adjacent signals | YES | `waste_cost_analysis` at `analytics_cache.json:154-167`; `portfolio_summary` at `analytics_cache.json:188-195`. | Supports SUPPLEMENT. |

### /similar response

* Response shape: `{"similar": [...], "count": len(results)}` with each row containing `order_id`, `item`, `category`, `day_of_week`, `is_event_day`, `quantity_lbs`, `waste_pct`, `stockout_occurred`, `is_correct`, `similarity`.
* Factor vectors exposed: NO. The query vector and order vector are computed internally at `context_router.py:237-253`, but the response rows at `context_router.py:257-268` do not include the factor vector.
* Evidence: `_FACTOR_NAMES` at `context_router.py:22-31`; `_order_vector` at `context_router.py:101-110`; response at `context_router.py:256-272`.

### /items response

* par_level exposed: YES. Fallback item has `par_level` at `context_router.py:164`; `items.json` entries also include `par_level`.
* price_memory_index exposed: NO. App-wide scan found `price_memory_index` in similarity/scoring contexts, not item response fields.
* price_trend exposed: NO. No `price_trend` match in app scan.
* Evidence: item route loads `items.json` or returns fallback at `context_router.py:154-168`.

### Fixture/data backing

| Data File / Source | Classification | Evidence |
| ------------------ | -------------- | -------- |
| `analytics_cache.json` | CACHED_STATIC / DEMO-FIXTURE | `/analytics` loads this file at `context_router.py:203-218`; cache says `source: purchasing_seed_v2.json`. |
| `purchasing_seed_v2.json` | DEMO/FIXTURE | `/similar` loads this file at `context_router.py:233`; main auto-seeds from it at `main.py:49`, `main.py:134-193`. |
| `items.json` | CACHED_STATIC / DEMO-FIXTURE | `/items` reads `apps/purchasing/backend/app/items.json` at `context_router.py:156-168`. |
| `waste_history.json` | CACHED_STATIC / DEMO-FIXTURE | `/waste-history` and item profile read it at `context_router.py:174`, `context_router.py:290-291`. |
| `weather_cache.json` / `get_weather_factor(use_live=False)` | CACHED_STATIC / deterministic | `_get_weather` reads cache or non-live weather at `context_router.py:137-141`. |

### P68 / P73 / P75 implications

* P68 verdict update: SUPPLEMENT. `/analytics` contains spend-adjacent cost/category/portfolio fields, but not the full spend dashboard API contract.
* P73 verdict update: SUPPLEMENT. `par_level` is exposed in item catalog data, but no PAR learning/update/recommendation workflow was found.
* P75 verdict update: FULL/SUPPLEMENT. No trust-analysis endpoint or DK/trust-trap logic was found; scoring/evidence primitives may support later implementation.

## Part 2 — Purchasing AgentEvolver

### Files inspected

* `apps/purchasing/backend/app/evolution/__init__.py`
* `apps/purchasing/backend/app/evolution/evolver_config.py`
* `apps/purchasing/backend/app/main.py` evolution wiring

### Variant dimensions

| Dimension | Baseline | Variant(s) | Purchasing PD relevance | Evidence |
| --------- | -------- | ---------- | ----------------------- | -------- |
| `waste_threshold` | `WASTE_THRESHOLD_v1`, active, `over_order_penalty: 0.30`, `under_order_penalty: 0.70` | `WASTE_THRESHOLD_v2`, shadow, `over_order_penalty: 0.40`, `under_order_penalty: 0.60` | Relevant to waste/stockout tradeoff, not price variance/trust/PAR. | `evolver_config.py:18-42` |
| `lead_time_buffer` | `LEAD_TIME_BUFFER_v1`, active, `buffer_days: 2`, `supplier_reliability_floor: 0.60` | `LEAD_TIME_BUFFER_v2`, shadow, `buffer_days: 3`, `supplier_reliability_floor: 0.70` | Relevant to supplier lead time/reliability; narrow relative to PD concepts. | `evolver_config.py:43-67` |

Missing PD/product dimensions from inspected config:

* price variance threshold: absent
* exception rate sensitivity: absent
* supplier trust score adjustment speed: absent
* supplier trust decay rate: absent
* relationship_legacy masking deterioration: absent
* auto-approve thresholds: absent
* price_memory_index behavior: absent

### Wiring

* get_purchasing_variants exists: YES. Exported in `evolution/__init__.py:3-15`; implemented in `evolver_config.py:114-117`.
* wired into main.py or SDK evolution router: YES. `main.py:30` imports `get_purchasing_variants`; `main.py:348-355` wires `create_evolution_router` with `variant_provider=lambda: _purchasing_variants_with_config(...)`.
* promoted/tested through verified outcomes: UNCLEAR/PARTIAL. SDK evolution router is wired, but inspected Purchasing config only defines static variants; no Purchasing-specific outcome evaluation logic appears in `evolver_config.py`.
* Evidence: `PURCHASING_EVOLVER_CONFIG` sets generic `promotion_improvement_threshold=0.05` and `promotion_min_samples=50` at `evolver_config.py:70-75`.

### Purchasing AE verdict

* Verdict: SUPPLEMENT
* Remaining effort: targeted supplement for domain-specific dimensions and outcome/promotion evidence.
* Rationale: Purchasing AE is not missing or placeholder-only; it is wired and has real variants. It is narrow and does not cover the listed Purchasing PD dimensions.

## Part 3 — TODO / Stub Context

### main.py

| Line / Context | Signal | Classification | Feature Impact |
| -------------- | ------ | -------------- | -------------- |
| `main.py:40` imports `_restore_demo_bundle` | demo bundle restore | DEMO INFRA | Startup can restore demo bundle if configured. |
| `main.py:49`, `main.py:134-193` use `SEED_FIXTURE_PATH` and `_seed_from_fixtures` | fixture seed path | DEMO INFRA | Existing data path is seeded/demo fixture based. |
| `main.py:137-142` returns zero on unavailable fixture | fixture unavailable fallback | DEMO INFRA / UNCLEAR | Not a product feature by itself, but confirms seed dependence. |
| `main.py:186-187` skips failed seed entries | skipped seed on exception | DEMO INFRA | Source data issues are printed and skipped. |
| `main.py:348-355` wires SDK evolution router | evolution wiring | Not a stub | Supports AE SUPPLEMENT, not FULL missing. |
| `main.py:359-370` wires conservation/self/context/evidence/graph routers | router registration | Not a stub | Confirms SDK/context/evidence API layers are registered. |

### evidence.py

| Line / Context | Signal | Hash-chain / Verify Impact | Classification |
| -------------- | ------ | -------------------------- | -------------- |
| `evidence.py:69-93` audit trail endpoint | audit-trail exists | Exposes evidence chain endpoint. | PARTIAL |
| `evidence.py:80-83` `hash: None`, `previous_hash: None`, `integrity: "fixture"` | hash-chain placeholders | Hash-chain validation is not implemented. | PRODUCTION STUB / FEATURE GAP |
| `evidence.py:89-92` `integrity_status: "fixture" if chain else "unavailable"`, `hash_chain_available: False`, `source: "fixture"` | explicit unavailable hash chain | P71 cannot be DROP. | FEATURE GAP |
| `evidence.py:95-121` conservation proof | proof endpoint exists | Returns status/q/trajectory from graph store, but `days_in_green: None` and `status_transitions: []`. | PARTIAL |
| `evidence.py:165-192` graph helper methods return empty lists on unavailable/error | empty fallback | Verification evidence can silently empty out if graph methods fail. | UNCLEAR / FEATURE GAP |

### data_helpers.py

| Line / Context | Missing Functionality | Feature Impact | Classification |
| -------------- | --------------------- | -------------- | -------------- |
| `data_helpers.py:1` says deterministic Purchasing demo fixtures | production data source absent | Helper is fixture-focused, not a production source. | DEMO INFRA |
| `data_helpers.py:10-12` fixed supplier/orders JSON paths | static data source | No connector/live purchasing data integration. | FEATURE GAP |
| `data_helpers.py:14-15`, `22-39` module caches and reset | fixture cache only | No verification/hash-chain logic. | DEMO INFRA |
| `data_helpers.py:42-66` supplier/category lookup helpers | no aggregation or trust/PAR logic | Useful helper only; not a spend/PAR/trust service. | FEATURE GAP |

### P71 verdict update

* Verdict: SUPPLEMENT widened to 2d.
* Remaining effort: build or wire a real verify workflow plus hash-chain validation, then update evidence endpoints and tests.
* Rationale: verification counts and evidence endpoints exist, but the audit chain explicitly returns fixture hashes and `hash_chain_available: False`; no complete hash-chain validation path was found.

## Part 4 — graph_status.py

### Endpoint inventory

| Method | Path | Function | Purpose | Evidence |
| ------ | ---- | -------- | ------- | -------- |
| GET | `/api/purchasing/graph/status` | `graph_status` | Active graph backend/cutover/guard status | `graph_status.py:30`, `graph_status.py:340-342` |

### Graph backend usage

* AGEClient used: NO direct `AGEClient` symbol found.
* SQLiteGraphStore used: YES indirectly as default authoritative store in `main.py:41`, `main.py:77-80`; graph status reports SQLite/AGE status.
* Other graph backend: `copilot_sdk.graph.factory.create_graph_store` for AGE test-mode active store creation.
* Evidence: `graph_status.py:240-269` creates active AGE graph store through factory; `graph_status.py:272-337` returns status/cutover metadata.

### Feature relevance

* Health/status only: YES.
* Graph traversal/query endpoints: NO. No decorators besides `@router.get("/status")` at `graph_status.py:340` were found.
* Future Purchasing graph work reduced: PARTIAL. The active AGE adapter preserves governed Decision write semantics at `graph_status.py:157-228` and cutover guard status at `graph_status.py:288-337`, but no traversal/query API exists.
* Evidence: `graph_status.py:302-315` explicitly marks migration/backfill/receipt mapping as not in scope/excluded/design required.

## Final Verdict Updates

| Prompt | Previous | Update | Remaining Effort | Evidence | Next Action |
| ------------------------ | --------------- | ------ | ---------------- | -------- | ----------- |
| P67 PUR-FACTORS-7 | DROP | confirm DROP | None for backend factor registration | Factor names include `price_memory_index` in `main.py:50-58` and `context_router.py:22-31`; Diag 05 confirmed preset-level coverage. | MAP queue update only. |
| P68 PUR-SPEND-DASH | FULL | SUPPLEMENT | 1-2d | `/analytics` exists at `context_router.py:203-218`; cache includes cost/savings/portfolio fields, but no vendor totals or budget fields. | Define spend dashboard API response and wire live/static aggregation. |
| P71 PUR-VERIFY | SUPPLEMENT 1-2d | widen SUPPLEMENT | 2d | `evidence.py:80-92` returns fixture chain with no hashes and `hash_chain_available: False`. | Implement/wire verification workflow and hash-chain validation. |
| P73 PUR-PAR-INTELLIGENCE | FULL | SUPPLEMENT | 1d | `/items` exposes `par_level` at `context_router.py:154-168`; no learning/update logic found. | Add PAR recommendation/update logic and endpoint contract. |
| P75 PUR-TRUST-ANALYSIS | FULL/SUPPLEMENT | FULL/SUPPLEMENT | 1-2d depending scope | No trust endpoint found; evidence exposes IKS/factors at `evidence.py:23-50`, not trust-trap analysis. | Implement named trust-analysis endpoint if MAP requires it. |
| Purchasing AE | unknown | SUPPLEMENT | 1-2d | Variants/wiring exist at `evolver_config.py:18-75`, `main.py:348-355`, but domain dimensions are narrow. | Add PD-specific AE dimensions and outcome/promotion evidence. |

## Diagnostic Limitations

* This diagnostic does not run tests.
* This diagnostic does not validate runtime API behavior.
* This diagnostic does not validate frontend/UI wiring.
* This diagnostic does not prove production data connectivity.
* DROP means source-level/API-layer evidence suggests no implementation prompt is needed, not that E2E validation passed.

## Recommended Next Step

Use a targeted SUPPLEMENT implementation prompt for P71 first, because `hash_chain_available: False` is an explicit product gap. Then run a P68/P73 supplement to formalize the spend/PAR API contract over the existing cached context scaffolding. P75 should get a focused trust-analysis design/implementation prompt if the MAP requires a named DK/trust-trap endpoint rather than generic evidence/scoring primitives.
