# SDK Backend Endpoint Map Diagnostic 02

Date: 2026-06-05
Model: gpt-5.3
Task Type: Diagnostic document creation only; no source code changes.
Repo: copilot-sdk
Diagnostic Scope: Comprehensive code-inspection map of `copilot_sdk/backend` endpoints, public backend exports, and Trading/Purchasing SDK router registrations.
Prior Diagnostics Read: `docs/implementation_plans/trading_backend_filetree_diagnostic.md`; `docs/implementation_plans/trading_deep_chase_diagnostic_01b.md`

## Executive Summary

* Overall verdict: SDK backend provides shared scoring, conservation, evolution, transfer, self-computation, and discovery routers, but it does not expose standalone `/iks`, `/iks-trend`, `/trust`, or `/signal-trust` endpoints.
* High-leverage endpoint findings:
  * SDK scoring exposes `/score`, `/learn`, `/fingerprint`, `/trajectory`, `/health`, and `/history`.
  * SDK conservation exposes `/conservation/status` and `/conservation/what-if`.
  * SDK evolution exposes `/api/evolution/variants`, `/api/evolution/history`, and `/api/evolution/promoted`.
  * SDK transfer exposes `/api/transfer/status` and `/api/transfer/opportunities`.
  * SDK self-computation exposes `/api/self/centroid-history`, `/api/self/accuracy-by-category`, `/api/self/decisions`, `/api/self/audit-trail`, and `/api/self/decision-flow`.
* Trading MAP impacts:
  * P56 needs SUPPLEMENT, not FULL, because generic conservation exists but no per-strategy endpoint was observed.
  * P58 remains FULL for a standalone IKS endpoint/API layer.
  * P53 remains SUPPLEMENT/FULL depending on whether `/fingerprint`/`/trajectory` are acceptable; no `/trust` endpoint exists.
  * P84 is SUPPLEMENT because SDK evolution routes are registered by Trading, but domain-specific variant/evolver semantics still need review.
* Purchasing MAP impacts:
  * P72 needs SUPPLEMENT, not FULL, because generic conservation exists and is registered.
  * P74 remains FULL for standalone `/iks` or `/iks-trend`; IKS appears embedded in learn/trajectory models, not exposed as a named scorecard endpoint.
  * P75 remains FULL/SUPPLEMENT depending on whether scoring fingerprint is accepted as trust analysis; no `/trust` endpoint exists.
* Biggest remaining ambiguity: runtime behavior and domain-specific semantic completeness were not validated; this is endpoint/API code inspection only.
* Recommended next prompt: update the MAP queue to drop no SDK endpoint items outright, mark P56/P72/P84 as supplements, and create a focused implementation supplement for IKS/trust endpoint gaps affecting Trading P58/P53 and Purchasing P74/P75.

## Path Resolution

* CLAUDE_SDK value: `C:\Users\baner\CopyFolder\IOT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
* Repo path used: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
* SDK backend path: `copilot_sdk/backend`
* Trading main.py path: `apps/trading/backend/app/main.py`
* Purchasing main.py path: `apps/purchasing/backend/app/main.py`
* Prior Diag 01 found: YES
* Prior Diag 01b found: YES

## CLAUDE.md Relevant Notes

* Do not use git directly.
* Docs are aspirational until proven in code; inspect actual source files.
* Cite file and line for behavioral claims.
* Code and tests beat docs; report drift when source and docs disagree.
* The SDK is public interface code and should avoid leaking domain internals.
* Repo guidance says to verify after changes, but this task explicitly prohibited tests and allowed only this Markdown write.

## SDK Backend File Tree

```text
__init__.py (0.5KB)
conservation_router.py (6.4KB)
discovery_router.py (1.5KB)
evolution_router.py (3.3KB)
models.py (5.3KB)
scorer_proxy.py (2.8KB)
scoring_router.py (10.8KB)
self_computation_router.py (16KB)
transfer_router.py (5.2KB)
transfer.py (6.6KB)
```

## SDK Backend **init**.py Exports

`copilot_sdk/backend/__init__.py` exports:

* `create_scoring_router`
* `create_conservation_router`
* `create_evolution_router`
* `mount_self_computation_router`

`create_transfer_router` exists in `copilot_sdk/backend/transfer_router.py` and is imported directly by Trading and Purchasing main files, but it is not listed in `copilot_sdk/backend/__init__.py` `__all__`.

`create_discovery_router` exists in `copilot_sdk/backend/discovery_router.py`, but it is not exported from `copilot_sdk/backend/__init__.py` and was not observed in Trading/Purchasing main registrations.

## Complete SDK Router Endpoint Inventory

| Router File | Method | Path | Function | Line | Capability Area | Notes |
| ----------- | ------ | ---- | -------- | ---: | --------------- | ----- |
| `conservation_router.py` | GET | `/conservation/status` | `status` | 50 | Conservation | Returns domain-level conservation counts/status. |
| `conservation_router.py` | POST | `/conservation/what-if` | `what_if` | 67 | Conservation | Runs what-if conservation check from supplied alpha/q/V/theta_min. |
| `discovery_router.py` | POST | `/api/discovery/sweep` | `sweep` | 22 | Discovery | Router prefix is `/api/discovery`; returns new alerts from engine sweep. |
| `discovery_router.py` | GET | `/api/discovery/digest` | `digest` | 30 | Discovery | Router prefix is `/api/discovery`; supports `min_confidence`. |
| `discovery_router.py` | GET | `/api/discovery/alerts` | `alerts` | 39 | Discovery | Router prefix is `/api/discovery`; returns stored alerts. |
| `evolution_router.py` | GET | `/api/evolution/variants` | `variants` | 50 | Evolution | Router prefix is `/api/evolution`; returns variants, active rules, promoted rules. |
| `evolution_router.py` | GET | `/api/evolution/history` | `history` | 65 | Evolution | Router prefix is `/api/evolution`; accepts `rule_name` and `limit`. |
| `evolution_router.py` | GET | `/api/evolution/promoted` | `promoted` | 78 | Evolution | Router prefix is `/api/evolution`; returns promoted rules. |
| `scoring_router.py` | POST | `/score` | `score` | 71 | Scoring | Mounted with `/api` prefix by Trading/Purchasing, so app path is `/api/score`. |
| `scoring_router.py` | POST | `/learn` | `learn` | 84 | Learning/IKS embedded | Mounted with `/api`; response model includes `iks_before` and `iks_after`. |
| `scoring_router.py` | GET | `/fingerprint` | `fingerprint` | 123 | Fingerprint/trust-adjacent | Mounted with `/api`; response factors include sigma/weight/interpretation. |
| `scoring_router.py` | GET | `/trajectory` | `trajectory` | 130 | IKS trajectory embedded | Mounted with `/api`; response model includes `current_iks`. |
| `scoring_router.py` | GET | `/health` | `health` | 137 | Scoring health | Mounted with `/api`; returns phase and alpha. |
| `scoring_router.py` | GET | `/history` | `history` | 146 | Decision history | Mounted with `/api`; returns graph-store decisions. |
| `self_computation_router.py` | GET | `/api/self/centroid-history` | `centroid_history` | 29 | Self-computation | Returns centroid checkpoints and total. |
| `self_computation_router.py` | GET | `/api/self/accuracy-by-category` | `accuracy_by_category` | 50 | Self-computation/trust-adjacent | Returns per-category accuracy and alerts. |
| `self_computation_router.py` | GET | `/api/self/decisions` | `decisions` | 84 | Self-computation | Returns filtered decisions. |
| `self_computation_router.py` | GET | `/api/self/audit-trail` | `audit_trail` | 107 | Self-computation/audit | Returns decision/outcome chain info or recent verified trails. |
| `self_computation_router.py` | GET | `/api/self/decision-flow` | `decision_flow` | 134 | Self-computation/IKS embedded | Returns decision flow, centroid evolution, category stats, flow statistics. |
| `transfer_router.py` | GET | `/api/transfer/status` | `transfer_status` | 24 | Transfer | Returns warm-start status. |
| `transfer_router.py` | GET | `/api/transfer/opportunities` | `transfer_opportunities` | 29 | Transfer | Detects transfer opportunities from fingerprint files. |

## Conservation Router Deep Dive

### File inspected

* `copilot_sdk/backend/conservation_router.py`

### Endpoint table

| Method | Path | Function | Response Shape / Key Fields | Evidence |
| ------ | ---- | -------- | --------------------------- | -------- |
| GET | `/conservation/status` | `status` | `engine`, `domain`, `verified_count`, `correct_count`, `total_decisions`, `penalty_ratio`, `signal`, `theta_min`, `headroom`, `status`, `passed` | Decorator at `conservation_router.py` L50; return payload assembled at L58-L64; model fields in `models.py` `ConservationStatusResponse`. |
| POST | `/conservation/what-if` | `what_if` | `engine`, `domain`, `inputs`, `signal`, `theta_min`, `headroom`, `status`, `passed` | Decorator at `conservation_router.py` L67; return payload assembled at L81-L91; model fields in `models.py` `ConservationWhatIfResponse`. |

### Per-strategy / per-category status analysis

* Exposes GREEN/AMBER/RED: PARTIAL
* Per-strategy or per-category: NO
* Evidence:
  * The router status endpoint computes one aggregate `conservation_status(...)` from `verified_count`, `correct_count`, `total_decisions`, and `penalty_ratio` at `conservation_router.py` L53-L59.
  * The response includes one `status` field through `_check_payload` at `conservation_router.py` L143-L151.
  * No route parameter or query parameter for category/strategy was observed inside `create_conservation_router`.
* Trading P56 verdict: SUPPLEMENT. Generic conservation exists and Trading registers it, but per-strategy Trading conservation needs app/domain supplement if required.
* Purchasing P72 verdict: SUPPLEMENT. Generic conservation exists and Purchasing registers it, but per-category/per-strategy purchasing conservation needs app/domain supplement if required.

## Scoring Router Deep Dive

### File inspected

* `copilot_sdk/backend/scoring_router.py`

### Endpoint table

| Method | Path | Function | Response Shape / Key Fields | Evidence |
| ------ | ---- | -------- | --------------------------- | -------- |
| POST | `/score` | `score` | `decision_id`, `action`, `action_index`, `confidence`, `probabilities`, `category`, `factors`, `engine` | Decorator at `scoring_router.py` L71; `ScoreResponse` fields in `models.py`. |
| POST | `/learn` | `learn` | `decision_id`, `iks_before`, `iks_after`, `centroid_delta`, `decisions_total`, `outcome`, `reward`, `previous_reward`, `reward_multiplier`, `engine`, pause fields | Decorator at `scoring_router.py` L84; `LearnResponse` fields in `models.py`; payload shaped at `scoring_router.py` L224-L249. |
| GET | `/fingerprint` | `fingerprint` | `factors`, `overall_win_rate`, `per_category_precision`, `decisions_analyzed`, `engine` | Decorator at `scoring_router.py` L123; `FingerprintResponse` fields in `models.py`. |
| GET | `/trajectory` | `trajectory` | `points`, `current_iks`, `current_win_rate`, `decisions_total`, `days_active`, `engine` | Decorator at `scoring_router.py` L130; `TrajectoryResponse` fields in `models.py`. |
| GET | `/health` | `health` | `phase`, `alpha`, `engine` | Decorator at `scoring_router.py` L137; return at L139-L144. |
| GET | `/history` | `history` | `engine`, `decisions` | Decorator at `scoring_router.py` L146; return at L157. |

### IKS coverage

* /iks exposed: NO
* /iks-trend exposed: NO
* IKS embedded elsewhere: YES
* Evidence:
  * No `/iks` or `/iks-trend` route was found in SDK backend endpoint inventory.
  * `LearnResponse` includes `iks_before` and `iks_after` in `models.py`.
  * `TrajectoryResponse` includes `current_iks` in `models.py`.
  * `self_computation_router.py` normalizes checkpoint `iks` into centroid evolution at L282-L292 in the inspected output.
* Trading P58 verdict: FULL for a named `/iks` or `/iks-trend` endpoint; SUPPLEMENT if embedded `/api/trajectory` is accepted as sufficient.
* Purchasing P74 verdict: FULL for a named IKS scorecard endpoint; SUPPLEMENT if `/api/trajectory` plus `/api/learn` embedded IKS fields are accepted.

### Trust / signal-trust coverage

* /trust exposed: NO
* /signal-trust exposed: NO
* Signal confidence / DK weights exposed: PARTIAL
* Evidence:
  * No `/trust` or `/signal-trust` route was found in SDK backend endpoint inventory.
  * `FingerprintFactorResponse` includes `name`, `sigma`, `weight`, and `interpretation` in `models.py`, and `/fingerprint` exposes factors through `scoring_router.py` L123-L127.
  * `self_computation_router.py` exposes `/accuracy-by-category` at L50 and `/decision-flow` at L134, which can support analysis but are not named trust endpoints.
* Trading P53 verdict: SUPPLEMENT/FULL. SDK has fingerprint and self-computation primitives, but no explicit trust/radar endpoint.
* Purchasing P75 verdict: SUPPLEMENT/FULL. SDK has fingerprint and accuracy primitives, but no explicit purchasing trust-analysis endpoint.

## Evolution / Transfer / Self-Computation Endpoint Relevance

### Evolution

* Endpoints:
  * GET `/api/evolution/variants`
  * GET `/api/evolution/history`
  * GET `/api/evolution/promoted`
* Trading P84 verdict: SUPPLEMENT. Trading registers `create_evolution_router` and supplies `variant_provider=get_trading_variants`, but this diagnostic did not validate full agent evolver behavior.
* Evidence:
  * `evolution_router.py` creates `APIRouter(prefix="/api/evolution", tags=["evolution"])`.
  * Endpoint decorators are at L50, L65, and L78.
  * Trading registers `create_evolution_router(... variant_provider=get_trading_variants)` at `apps/trading/backend/app/main.py` L274-L280.

### Transfer

* Endpoints:
  * GET `/api/transfer/status`
  * GET `/api/transfer/opportunities`
* Trading relevance: relevant.
* Purchasing relevance: relevant.
* Evidence:
  * `transfer_router.py` creates `APIRouter(prefix="/api/transfer", tags=["Transfer"])`.
  * Endpoint decorators are at L24 and L29.
  * Trading registers `create_transfer_router(scorer_proxy)` at `apps/trading/backend/app/main.py` L273.
  * Purchasing registers `create_transfer_router(scorer_proxy)` at `apps/purchasing/backend/app/main.py` L347.

### Self-Computation

* Endpoints:
  * GET `/api/self/centroid-history`
  * GET `/api/self/accuracy-by-category`
  * GET `/api/self/decisions`
  * GET `/api/self/audit-trail`
  * GET `/api/self/decision-flow`
* IKS/trust/contribution relevance:
  * Relevant but indirect. `/api/self/decision-flow` includes centroid evolution with checkpoint `iks` where present, category accuracy, recent decisions, decision chain, and flow statistics.
  * `/api/self/accuracy-by-category` is trust-adjacent because it returns per-category accuracy and alert flags.
* Evidence:
  * `self_computation_router.py` creates `APIRouter(prefix="/api/self", tags=["self-computation"])`.
  * Endpoint decorators are at L29, L50, L84, L107, and L134.
  * `mount_self_computation_router` includes the router on the app at `self_computation_router.py` L174-L176.
  * Trading calls `mount_self_computation_router(app, selected_graph_store_factory(scoring_db))` at `apps/trading/backend/app/main.py` L290.
  * Purchasing calls `mount_self_computation_router(app, selected_graph_store_factory(scoring_db))` at `apps/purchasing/backend/app/main.py` L366.

## App Router Registration Comparison

### Trading

Trading registers these SDK routers:

* `create_scoring_router`, imported from `copilot_sdk.backend` at `apps/trading/backend/app/main.py` L44-L48 and included with prefix `/api` at L265-L272.
* `create_transfer_router`, imported directly from `copilot_sdk.backend.transfer_router` at L43 and included at L273.
* `create_evolution_router`, imported from `copilot_sdk.backend` at L44-L48 and included at L274-L280.
* `create_conservation_router`, imported from `copilot_sdk.backend` at L44-L48 and included with prefix `/api` at L283-L289.
* `mount_self_computation_router`, imported from `copilot_sdk.backend` at L44-L48 and mounted at L290.

### Purchasing

Purchasing registers these SDK routers:

* `create_scoring_router`, imported from `copilot_sdk.backend` at `apps/purchasing/backend/app/main.py` L33-L37 and included with prefix `/api` at L339-L346.
* `create_transfer_router`, imported directly from `copilot_sdk.backend.transfer_router` at L32 and included at L347.
* `create_evolution_router`, imported from `copilot_sdk.backend` at L33-L37 and included at L348-L356.
* `create_conservation_router`, imported from `copilot_sdk.backend` at L33-L37 and included with prefix `/api` at L359-L365.
* `mount_self_computation_router`, imported from `copilot_sdk.backend` at L33-L37 and mounted at L366.

### Comparison

* Same SDK router set: YES
* Purchasing gets conservation through SDK router: YES
* Purchasing gets IKS through SDK router: PARTIAL
* Important registration differences:
  * Trading passes `variant_provider=get_trading_variants` to the evolution router.
  * Purchasing passes `variant_provider=lambda: _purchasing_variants_with_config(...)` to the evolution router.
  * Both register scoring, transfer, evolution, conservation, and self-computation SDK routers.
  * Neither observed app registration includes `create_discovery_router`.

## Endpoint Decision Table

| SDK endpoint                              | Exposed? | Registered by Trading? | Registered by Purchasing? | Trading prompt impact | Purchasing prompt impact | Evidence |
| ----------------------------------------- | -------- | ---------------------- | ------------------------- | --------------------- | ------------------------ | -------- |
| /conservation or /conservation/{category} | YES for `/api/conservation/status` and `/api/conservation/what-if`; NO for category route | YES | YES | P56 SUPPLEMENT | P72 SUPPLEMENT | `conservation_router.py` L50/L67; Trading main L283-L289; Purchasing main L359-L365. |
| per-strategy GREEN/AMBER/RED conservation | PARTIAL aggregate status only | YES, aggregate only | YES, aggregate only | P56 SUPPLEMENT | P72 SUPPLEMENT | `conservation_router.py` status uses aggregate counts at L53-L64; no strategy/category route observed. |
| /iks or /iks-trend                        | NO named route; YES embedded IKS fields | PARTIAL via scoring/self routes | PARTIAL via scoring/self routes | P58 FULL | P74 FULL | No `/iks` route in inventory; `LearnResponse`/`TrajectoryResponse` include IKS fields in `models.py`; scoring registered by both apps. |
| /trust or /signal-trust                   | NO named route; PARTIAL fingerprint/accuracy primitives | PARTIAL | PARTIAL | P53 SUPPLEMENT/FULL | P75 SUPPLEMENT/FULL | No `/trust` route in inventory; `/fingerprint` at `scoring_router.py` L123; `/api/self/accuracy-by-category` at `self_computation_router.py` L50. |
| /evolution/*                              | YES | YES | YES | P84 SUPPLEMENT | N/A | `evolution_router.py` L50/L65/L78; Trading main L274-L280; Purchasing main L348-L356. |
| /transfer/*                               | YES | YES | YES | relevant | relevant | `transfer_router.py` L24/L29; Trading main L273; Purchasing main L347. |
| self-computation endpoints                | YES | YES | YES | relevant | relevant | `self_computation_router.py` L29/L50/L84/L107/L134; Trading main L290; Purchasing main L366. |

## Diagnostic Limitations

* This diagnostic does not validate runtime behavior.
* This diagnostic does not run tests.
* This diagnostic does not prove frontend/UI wiring.
* This diagnostic does not prove domain-specific semantic completeness unless the implementation was read.
* DROP verdict means endpoint/API layer appears covered, not necessarily UI/product completion.
* No DROP verdicts were assigned for the key Trading/Purchasing MAP endpoint items because each still has either domain-specific gaps or named endpoint gaps.

## Recommended Next Step

Run a MAP queue update: mark SDK generic conservation and evolution as existing shared primitives, but keep Trading P56/P84 and Purchasing P72 as supplement/review items. Create a focused implementation supplement for named IKS/trust endpoints or adapters covering Trading P58/P53 and Purchasing P74/P75.
